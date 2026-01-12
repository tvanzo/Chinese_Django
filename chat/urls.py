from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    # Main chat page
    path("", views.chat, name="chat"),

    # Chat API: send messages
    path("api/", views.chat_api, name="chat_api"),

    # Highlights API (GET list, POST create, DELETE remove)
    path("api/highlights/", views.chat_highlights, name="chat_highlights"),

    # Optional: single highlight detail (GET/PUT/DELETE by ID)
    # Only add this if you have or plan a chat_highlight_detail view
    path("api/highlights/<int:id>/", views.chat_highlight_detail, name="chat_highlight_detail"),

    # Chat categories
    path("api/categories/", views.create_chat_category, name="create_chat_category"),
    path("api/set-category/", views.set_chat_category, name="set_chat_category"),
]