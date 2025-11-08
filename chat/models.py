from django.db import models

# Create your models here.
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import ChatSession, ChatMessage

# however you generate the AI reply now:
from .openai_utils import get_ai_reply  # <- adapt to your code

@login_required
@require_POST
def chat_api(request):
    data = json.loads(request.body.decode("utf-8"))
    message = (data.get("message") or "").strip()
    session_id = data.get("session_id")

    if not message:
        return JsonResponse({"error": "Empty message"}, status=400)

    # Find or create a session
    if session_id:
        session = ChatSession.objects.filter(
            id=session_id, user=request.user
        ).first()
        if session is None:
            session = ChatSession.objects.create(
                user=request.user,
                title=message[:60],
            )
    else:
        session = (
            ChatSession.objects.filter(user=request.user)
            .order_by("-created_at")
            .first()
        )
        if session is None:
            session = ChatSession.objects.create(
                user=request.user,
                title=message[:60],
            )

    # Save user message
    ChatMessage.objects.create(
        session=session,
        role="user",
        content=message,
    )

    # Get AI reply (plug in your real logic)
    reply_text = get_ai_reply(message, session=session)

    # Save assistant message
    ChatMessage.objects.create(
        session=session,
        role="assistant",
        content=reply_text,
    )

    return JsonResponse(
        {
            "reply": reply_text,
            "session_id": session.id,
        }
    )
