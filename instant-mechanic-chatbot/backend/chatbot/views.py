from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Conversation, Message, MediaUpload, Diagnosis, Booking
from .serializers import (
    ConversationSerializer, MessageSerializer, MediaUploadSerializer,
    DiagnosisSerializer, BookingSerializer,
)
from .services import intent_classifier, question_flow, gemini_service

REJECTION_REPLY = (
    "I'm your virtual car mechanic, so I can only help with vehicle-related issues — "
    "engine, brakes, noises, warning lights, and similar. Could you tell me about a "
    "problem you're having with your car?"
)

GREETING_REPLY = (
    "Hello! I'm your virtual mechanic. Tell me what's going on with your vehicle and "
    "I'll help you figure out what's wrong."
)


class ChatView(APIView):
    """POST /api/chat/
    Body: { "conversation_id": "<uuid, optional>", "message": "<text>" }

    Drives the entire conversation using traditional logic (intent check +
    slot-filling state machine). No AI call happens here — this endpoint only
    decides *what to ask next* or flags that we're ready for /api/diagnosis/.
    """

    def post(self, request):
        message_text = (request.data.get("message") or "").strip()
        conversation_id = request.data.get("conversation_id")

        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id)
        else:
            conversation = Conversation.objects.create()

        if not message_text:
            return Response({"error": "message is required"}, status=status.HTTP_400_BAD_REQUEST)

        Message.objects.create(conversation=conversation, sender="user", message_type="text", text=message_text)

        # --- Traditional logic: intent filtering ---
        if intent_classifier.is_greeting(message_text) and not conversation.collected_slots:
            bot_text = GREETING_REPLY
            Message.objects.create(conversation=conversation, sender="bot", message_type="text", text=bot_text)
            return self._response(conversation, bot_text)

        # Only bypass the topic filter once slot-filling has actually begun
        # (i.e. at least one slot is already recorded). The very first
        # substantive message in a conversation must still pass the filter.
        has_active_slot_session = bool(conversation.collected_slots)
        if not has_active_slot_session and not intent_classifier.is_car_related(message_text):
            bot_text = REJECTION_REPLY
            Message.objects.create(conversation=conversation, sender="bot", message_type="text", text=bot_text)
            return self._response(conversation, bot_text)

        if conversation.status in ("diagnosed", "booked"):
            bot_text = (
                "You already have a diagnosis for this conversation. Start a new chat "
                "if you have a different issue, or use the Book Mechanic option below."
            )
            Message.objects.create(conversation=conversation, sender="bot", message_type="text", text=bot_text)
            return self._response(conversation, bot_text)

        # --- Traditional logic: slot-filling state machine ---
        pending_slot, _ = question_flow.next_missing_slot(conversation.collected_slots)
        if pending_slot:
            conversation.collected_slots = question_flow.record_answer(
                conversation.collected_slots, pending_slot, message_text
            )

        next_slot, next_question = question_flow.next_missing_slot(conversation.collected_slots)

        if next_slot:
            bot_text = next_question
            conversation.status = "collecting_info"
        else:
            bot_text = (
                "Thanks, that's everything I need for now.\n\n"
                f"{question_flow.build_progress_summary(conversation.collected_slots)}\n\n"
                f"{question_flow.OPTIONAL_MEDIA_PROMPT}\n\n"
                "Or just say 'diagnose' / 'no' and I'll give you my assessment now."
            )
            conversation.status = "ready_for_diagnosis"

        conversation.save()
        Message.objects.create(conversation=conversation, sender="bot", message_type="text", text=bot_text)
        return self._response(conversation, bot_text)

    def _response(self, conversation, bot_text):
        return Response(
            {
                "conversation_id": str(conversation.id),
                "reply": bot_text,
                "status": conversation.status,
                "ready_for_diagnosis": conversation.status == "ready_for_diagnosis",
                "collected_slots": conversation.collected_slots,
            },
            status=status.HTTP_200_OK,
        )


class UploadView(APIView):
    """POST /api/upload/  (multipart/form-data)
    Fields: conversation_id, file, media_type (image|audio|video)

    Traditional storage for all media. AI (Gemini vision) is invoked ONLY for
    images, because that's the one case where automated analysis genuinely
    adds diagnostic value; audio/video are stored and left for the technician
    to review (transcription/analysis would be a nice-to-have, not required
    for this deadline, and keeps AI usage minimal per the brief).
    """

    def post(self, request):
        conversation_id = request.data.get("conversation_id")
        media_type = request.data.get("media_type")
        file_obj = request.FILES.get("file")

        if not conversation_id or not file_obj or media_type not in ("image", "audio", "video"):
            return Response(
                {"error": "conversation_id, file, and media_type (image|audio|video) are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversation = get_object_or_404(Conversation, id=conversation_id)
        upload = MediaUpload.objects.create(conversation=conversation, file=file_obj, media_type=media_type)

        Message.objects.create(
            conversation=conversation, sender="user", message_type=media_type,
            text=f"[{media_type} uploaded]", media=upload,
        )

        bot_text = f"Got your {media_type}. "
        if media_type == "image":
            upload.file.open("rb")
            image_bytes = upload.file.read()
            upload.file.close()
            analysis = gemini_service.analyze_image(image_bytes, file_obj.content_type or "image/jpeg")
            upload.analysis_result = analysis
            upload.analyzed = True
            upload.save()
            bot_text += f"Here's what I can see: {analysis}"
        else:
            bot_text += "I've attached it to your case for the technician to review."

        Message.objects.create(conversation=conversation, sender="bot", message_type="text", text=bot_text)

        return Response(
            {
                "upload": MediaUploadSerializer(upload).data,
                "reply": bot_text,
                "conversation_id": str(conversation.id),
            },
            status=status.HTTP_201_CREATED,
        )


class DiagnosisView(APIView):
    """POST /api/diagnosis/  Body: { "conversation_id": "<uuid>" }
    Triggers the single Gemini call that synthesizes a diagnosis from the
    slots collected via traditional logic, plus any image analysis notes.

    GET /api/diagnosis/?conversation_id=<uuid>  Retrieves an existing diagnosis.
    """

    def post(self, request):
        conversation_id = request.data.get("conversation_id")
        conversation = get_object_or_404(Conversation, id=conversation_id)

        if hasattr(conversation, "diagnosis"):
            return Response(DiagnosisSerializer(conversation.diagnosis).data, status=status.HTTP_200_OK)

        image_notes = list(
            conversation.uploads.filter(media_type="image", analyzed=True).values_list("analysis_result", flat=True)
        )

        result = gemini_service.analyze_symptoms(conversation.collected_slots, image_notes)

        diagnosis = Diagnosis.objects.create(
            conversation=conversation,
            summary=result.get("summary", ""),
            likely_causes=result.get("likely_causes", []),
            recommended_service=result.get("recommended_service", ""),
            urgency=result.get("urgency", "medium"),
            confidence=result.get("confidence", 0.0),
            raw_ai_response=result.get("raw_ai_response", ""),
        )
        conversation.status = "diagnosed"
        conversation.save()

        bot_text = (
            f"Here's my assessment:\n\n{diagnosis.summary}\n\n"
            f"Likely cause(s): {', '.join(diagnosis.likely_causes) if diagnosis.likely_causes else 'N/A'}\n"
            f"Recommended service: {diagnosis.recommended_service}\n"
            f"Urgency: {diagnosis.urgency}\n\n"
            "Would you like to book a mechanic for this? Tap 'Book Mechanic' below."
        )
        Message.objects.create(conversation=conversation, sender="bot", message_type="text", text=bot_text)

        return Response(
            {"diagnosis": DiagnosisSerializer(diagnosis).data, "reply": bot_text},
            status=status.HTTP_201_CREATED,
        )

    def get(self, request):
        conversation_id = request.query_params.get("conversation_id")
        conversation = get_object_or_404(Conversation, id=conversation_id)
        if not hasattr(conversation, "diagnosis"):
            return Response({"error": "No diagnosis yet for this conversation"}, status=status.HTTP_404_NOT_FOUND)
        return Response(DiagnosisSerializer(conversation.diagnosis).data)


class BookingCreateView(APIView):
    """POST /api/booking/
    Body: { conversation_id, customer_name, phone_number, preferred_date, ... }
    Pure traditional CRUD — no AI involved.
    """

    def post(self, request):
        conversation_id = request.data.get("conversation_id")
        conversation = get_object_or_404(Conversation, id=conversation_id)

        data = request.data.copy()
        data["conversation"] = str(conversation.id)
        if hasattr(conversation, "diagnosis") and not data.get("diagnosis"):
            data["diagnosis"] = conversation.diagnosis.id
        if not data.get("vehicle_info"):
            data["vehicle_info"] = conversation.collected_slots.get("vehicle_info", "")

        serializer = BookingSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save(status="pending")

        conversation.status = "booked"
        conversation.save()

        Message.objects.create(
            conversation=conversation, sender="bot", message_type="text",
            text=f"Your booking is confirmed for {booking.preferred_date}. Booking ID: {booking.id}. "
                 "A mechanic will contact you shortly.",
        )

        return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)


class BookingDetailView(APIView):
    """GET /api/booking/{id}/"""

    def get(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)
        return Response(BookingSerializer(booking).data)


class ConversationDetailView(APIView):
    """GET /api/conversation/{id}/ — full chat + diagnosis history for the frontend."""

    def get(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        return Response(ConversationSerializer(conversation).data)
