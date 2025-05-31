from django.urls import path
from .views import chatbot_view,clear_chat

urlpatterns = [
    path("", chatbot_view, name="chatbot"),
    path('clear/', clear_chat, name='clear_chat'),
]
