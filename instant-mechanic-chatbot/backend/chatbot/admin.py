from django.contrib import admin
from .models import Conversation, Message, MediaUpload, Diagnosis, Booking


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "created_at", "updated_at")
    list_filter = ("status",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "message_type", "created_at")
    list_filter = ("sender", "message_type")


@admin.register(MediaUpload)
class MediaUploadAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "media_type", "analyzed", "uploaded_at")


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "recommended_service", "urgency", "confidence", "created_at")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "phone_number", "preferred_date", "status", "created_at")
    list_filter = ("status",)
