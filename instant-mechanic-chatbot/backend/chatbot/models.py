import uuid
from django.db import models


class Conversation(models.Model):
    """One diagnosis session with a car owner."""

    STATUS_CHOICES = [
        ("collecting_info", "Collecting Info"),   # traditional-logic follow-up questions
        ("ready_for_diagnosis", "Ready for Diagnosis"),
        ("diagnosed", "Diagnosed"),
        ("booked", "Booked"),
        ("closed", "Closed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="collecting_info")

    # Slot-filling state used by the traditional (non-AI) question flow engine.
    # Stored as JSON so no AI call is needed to track what we already know.
    collected_slots = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Conversation {self.id} ({self.status})"


class Message(models.Model):
    SENDER_CHOICES = [("user", "User"), ("bot", "Bot")]
    TYPE_CHOICES = [("text", "Text"), ("image", "Image"), ("audio", "Audio"), ("video", "Video"), ("system", "System")]

    conversation = models.ForeignKey(Conversation, related_name="messages", on_delete=models.CASCADE)
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="text")
    text = models.TextField(blank=True)
    media = models.ForeignKey("MediaUpload", null=True, blank=True, on_delete=models.SET_NULL, related_name="messages")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.sender}] {self.text[:40]}"


class MediaUpload(models.Model):
    MEDIA_TYPE_CHOICES = [("image", "Image"), ("audio", "Audio"), ("video", "Video")]

    conversation = models.ForeignKey(Conversation, related_name="uploads", on_delete=models.CASCADE)
    file = models.FileField(upload_to="uploads/%Y/%m/%d/")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    # Populated by Gemini vision (images only) — AI used only where it adds real value.
    analysis_result = models.TextField(blank=True)
    analyzed = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.media_type} upload ({self.id})"


class Diagnosis(models.Model):
    conversation = models.OneToOneField(Conversation, related_name="diagnosis", on_delete=models.CASCADE)
    summary = models.TextField()
    likely_causes = models.JSONField(default=list, blank=True)
    recommended_service = models.CharField(max_length=255, blank=True)
    urgency = models.CharField(
        max_length=20,
        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent - stop driving")],
        default="medium",
    )
    confidence = models.FloatField(default=0.0)
    raw_ai_response = models.TextField(blank=True)  # audit trail of the single AI call used
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Diagnosis for {self.conversation_id}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    conversation = models.ForeignKey(Conversation, related_name="bookings", on_delete=models.CASCADE)
    diagnosis = models.ForeignKey(Diagnosis, null=True, blank=True, on_delete=models.SET_NULL, related_name="bookings")
    customer_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    vehicle_info = models.CharField(max_length=255, blank=True)
    preferred_date = models.DateField()
    preferred_time_slot = models.CharField(max_length=50, blank=True)
    address = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.id} - {self.customer_name} ({self.status})"
