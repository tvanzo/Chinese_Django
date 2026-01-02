# chat/views.py
import json
import os
import logging

import requests
from django.conf import settings
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

from accounts.models import (
    Subscription,
    Profile,
    ChatSession,
    ChatMessage,
)
from subplayer.models import Highlight  # unified highlight model

logger = logging.getLogger(__name__)


# =========================
# CHAT PAGE
# =========================
from accounts.models import ChatCategory  # add import

@login_required
def chat(request: HttpRequest) -> HttpResponse:
    user = request.user

    # ---- category filter ----
    category_id = request.GET.get("category")  # optional

    # ---- resolve active session ----
    if request.GET.get("new") == "1":
        session = ChatSession.objects.create(user=user, title="")
    else:
        session_id = request.GET.get("session")
        session = None

        if session_id:
            session = ChatSession.objects.filter(user=user, pk=session_id).first()

        if session is None:
            session = ChatSession.objects.filter(user=user).order_by("-updated_at").first()

        if session is None:
            session = ChatSession.objects.create(user=user, title="")

    # categories for UI
    categories = ChatCategory.objects.filter(user=user).order_by("name")

    sessions_qs = (
        ChatSession.objects.filter(user=user)
        .annotate(
            highlight_count=Count(
                "chat_highlights",
                filter=Q(chat_highlights__source="chat")
            )
        )
    )

    # apply filter
    if category_id == "none":
        sessions_qs = sessions_qs.filter(category__isnull=True)
    elif category_id:
        sessions_qs = sessions_qs.filter(category_id=category_id)

    sessions = sessions_qs.order_by("-updated_at")

    messages = session.messages.all().order_by("created_at")

    current_highlight_count = Highlight.objects.filter(
        user=user,
        source="chat",
        chat_session=session,
    ).count()

    context = {
        "categories": categories,
        "selected_category": category_id or "",
        "sessions": sessions,
        "current_session": session,
        "messages": messages,
        "current_highlight_count": current_highlight_count,
    }
    return render(request, "chat.html", context)

# =========================
# CHAT API (messages)
# =========================
@login_required
@csrf_exempt
def chat_api(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed."}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    user_msg = (payload.get("message") or "").strip()
    mode = (payload.get("mode") or "normal").lower()

    if not user_msg:
        return JsonResponse({"error": "Empty message."}, status=400)

    user = request.user

    # ✅ IMPORTANT: use the session_id coming from the frontend
    session_id = payload.get("session_id")
    if session_id:
        session = ChatSession.objects.filter(user=user, pk=session_id).first()
        if session is None:
            return JsonResponse({"error": "Session not found."}, status=404)
    else:
        session = (
            ChatSession.objects.filter(user=user)
            .order_by("-updated_at")
            .first()
        )
        if session is None:
            session = ChatSession.objects.create(user=user, title="")

    # save user message
    ChatMessage.objects.create(
        session=session,
        role="user",
        content=user_msg,
    )

    api_key = getattr(settings, "DEEPSEEK_API_KEY", None) or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return JsonResponse({"error": "Server not configured."}, status=500)

    base_prompt = (
        "You are a patient, upbeat Chinese language tutor. "
        "Use simple explanations with examples. "
        "Include pinyin and brief English glosses for key words."
    )

    if mode == "review":
        system_prompt = base_prompt + (
            " The user is reviewing previously highlighted Chinese snippets. "
            "Use ONLY the provided highlight texts."
        )
    else:
        system_prompt = base_prompt

    body = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    r = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers=headers,
        json=body,
        timeout=30,
    )

    if r.status_code != 200:
        return JsonResponse({"error": "LLM error"}, status=502)

    reply = r.json()["choices"][0]["message"]["content"]

    # save assistant message
    ChatMessage.objects.create(
        session=session,
        role="assistant",
        content=reply,
    )

    # update title + timestamp
    if not session.title:
        session.title = user_msg[:80]
    session.updated_at = timezone.now()
    session.save(update_fields=["title", "updated_at"])

    return JsonResponse({"reply": reply})

# =========================
# CHAT HIGHLIGHTS API
# =========================
@login_required
@require_http_methods(["GET", "POST"])
def chat_highlights(request: HttpRequest) -> JsonResponse:
    """
    /chat/api/highlights/

    GET  -> list chat highlights (optionally by ?session=<id>)
    POST -> create a chat highlight
    """
    user = request.user

    # ---- resolve session safely ----
    session_id = request.GET.get("session")
    session = None
    if session_id:
        session = ChatSession.objects.filter(user=user, pk=session_id).first()

    if session is None:
        session = (
            ChatSession.objects.filter(user=user)
            .order_by("-updated_at")
            .first()
        )

    # ---- GET ----
    if request.method == "GET":
        qs = Highlight.objects.filter(
            user=user,
            source="chat",
        )
        if session:
            qs = qs.filter(chat_session=session)

        data = [{"id": h.id, "text": h.highlighted_text} for h in qs.order_by("created_at")]
        return JsonResponse(data, safe=False)

    # ---- POST ----
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    text = (payload.get("text") or "").strip()
    if not text:
        return JsonResponse({"error": "Text is required"}, status=400)

    # ---- daily limit (ALL highlights count, same as before) ----
    subscription = Subscription.objects.filter(user=user).first()
    if subscription and subscription.tier == "FREE":
        today = timezone.now().date()
        if Highlight.objects.filter(user=user, created_at__date=today).count() >= 3:
            return JsonResponse(
                {"error": "Daily highlight limit reached", "limit_reached": True},
                status=403,
            )

    # ✅ IMPORTANT: chat highlights DO NOT set media timing fields
    new_highlight = Highlight.objects.create(
        user=user,
        source="chat",
        chat_session=session,
        highlighted_text=text,
    )

    profile = user.profile
    profile.total_highlights += 1
    profile.save(update_fields=["total_highlights"])

    return JsonResponse(
        {
            "id": new_highlight.id,
            "text": new_highlight.highlighted_text,
        },
        status=201,
    )
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def set_chat_category(request: HttpRequest) -> JsonResponse:
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    session_id = payload.get("session_id")
    category_id = payload.get("category_id")  # can be null/None to clear

    if not session_id:
        return JsonResponse({"error": "session_id is required"}, status=400)

    session = ChatSession.objects.filter(user=request.user, pk=session_id).first()
    if not session:
        return JsonResponse({"error": "Session not found"}, status=404)

    if category_id in (None, "", "none"):
        session.category = None
    else:
        category = ChatCategory.objects.filter(user=request.user, pk=category_id).first()
        if not category:
            return JsonResponse({"error": "Category not found"}, status=404)
        session.category = category

    session.save(update_fields=["category", "updated_at"])
    return JsonResponse({"ok": True})

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def create_chat_category(request: HttpRequest) -> JsonResponse:
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = (payload.get("name") or "").strip()
    if not name:
        return JsonResponse({"error": "name is required"}, status=400)

    obj, created = ChatCategory.objects.get_or_create(user=request.user, name=name)
    return JsonResponse({"id": obj.id, "name": obj.name, "created": created})