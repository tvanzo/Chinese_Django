from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("", views.chat, name="chat"),
    path("api/", views.chat_api, name="chat_api"),
    path("api/highlights/", views.chat_highlights, name="chat_highlights"),
]
