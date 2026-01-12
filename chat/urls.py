# chat/urls.py
from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    # Page
    path("", views.chat, name="chat"),

    # Chat API
    path("api/", views.chat_api, name="chat_api"),

    # Highlights API
    path("api/highlights/", views.chat_highlights, name="chat_highlights"),
    path("api/highlights/<int:highlight_id>/", views.chat_highlight_detail, name="chat_highlight_detail"),

    # Categories
    path("api/categories/", views.create_chat_category, name="create_chat_category"),
    path("api/set-category/", views.set_chat_category, name="set_chat_category"),
]
