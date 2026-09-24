from rest_framework import serializers
from .models import Conversation, Message, MediaUpload, Diagnosis, Booking


class MediaUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaUpload
        fields = ["id", "file", "media_type", "analysis_result", "analyzed", "uploaded_at"]
        read_only_fields = ["analysis_result", "analyzed", "uploaded_at"]


class MessageSerializer(serializers.ModelSerializer):
    media = MediaUploadSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "sender", "message_type", "text", "media", "created_at"]


class DiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = [
            "id", "summary", "likely_causes", "recommended_service",
            "urgency", "confidence", "created_at",
        ]


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    diagnosis = DiagnosisSerializer(read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "status", "collected_slots", "messages", "diagnosis", "created_at", "updated_at"]


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "id", "conversation", "diagnosis", "customer_name", "phone_number",
            "vehicle_info", "preferred_date", "preferred_time_slot", "address",
            "notes", "status", "created_at",
        ]
        read_only_fields = ["status", "created_at"]
