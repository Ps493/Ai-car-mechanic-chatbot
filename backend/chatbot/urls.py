from django.urls import path
from .views import (
    ChatView, UploadView, DiagnosisView, BookingCreateView, BookingDetailView,
    ConversationDetailView,
)

urlpatterns = [
    path("chat/", ChatView.as_view(), name="chat"),
    path("upload/", UploadView.as_view(), name="upload"),
    path("diagnosis/", DiagnosisView.as_view(), name="diagnosis"),
    path("booking/", BookingCreateView.as_view(), name="booking-create"),
    path("booking/<int:booking_id>/", BookingDetailView.as_view(), name="booking-detail"),
    path("conversation/<uuid:conversation_id>/", ConversationDetailView.as_view(), name="conversation-detail"),
]
