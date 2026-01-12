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
def chat_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception as e:
        logger.error(f"Invalid JSON body: {e}")
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    user_msg = (payload.get("message") or "").strip()
    mode = (payload.get("mode") or "normal").lower().strip()
    session_id = payload.get("session_id")

    if not user_msg:
        return JsonResponse({"error": "Message is required."}, status=400)

    user = request.user

    logger.info(
        "chat_api called | user=%s | mode=%s | session_id=%s | msg_preview=%s...",
        user.username,
        mode,
        session_id,
        user_msg[:80]
    )

    # Resolve session
    if session_id:
        session = ChatSession.objects.filter(user=user, pk=session_id).first()
        if not session:
            return JsonResponse({"error": "Session not found."}, status=404)
    else:
        session = ChatSession.objects.filter(user=user).order_by("-updated_at").first()
        if not session:
            session = ChatSession.objects.create(user=user, title="New Chat")

    # Save user message
    ChatMessage.objects.create(
        session=session,
        role="user",
        content=user_msg,
    )

    # Select system prompt
    if mode == "translate":
        system_prompt = (
            "You are a professional, precise translator. "
            "Your ONLY task is to provide the translation. "
            "Rules you MUST follow strictly:\n"
            "- Output ONLY the translation — nothing else\n"
            "- NO explanations, NO greetings, NO notes, NO pinyin, NO chit-chat\n"
            "- If input contains Chinese characters → translate to natural English\n"
            "- If input is English or other → translate to natural simplified Chinese\n"
            "- Preserve tone, swearing, names, numbers, punctuation exactly\n"
            "- Keep formatting (line breaks, quotes) if present"
        )
    elif mode == "review":
        system_prompt = (
            "You are a patient, upbeat Chinese language tutor reviewing previously "
            "highlighted Chinese snippets. Use simple explanations, give 1-2 natural "
            "examples. Include pinyin when useful. Keep answers clear and encouraging."
        )
    else:
        system_prompt = (
            "You are a patient, upbeat, encouraging Chinese language tutor. "
            "Use simple, clear explanations and give 1-2 good example sentences. "
            "Include pinyin (with tone marks) and brief English glosses when helpful. "
            "Be friendly and supportive. Keep most answers in Chinese when appropriate."
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]

    api_key = getattr(settings, "DEEPSEEK_API_KEY", None) or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        logger.error("DEEPSEEK_API_KEY not configured")
        return JsonResponse({"error": "Server configuration error"}, status=500)

    try:
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "stream": False,
                "temperature": 0.7 if mode != "translate" else 0.3,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        reply = data["choices"][0]["message"]["content"].strip()

    except requests.Timeout:
        logger.error("DeepSeek API timeout")
        return JsonResponse({"error": "Request timeout. Please try again."}, status=504)
    except Exception:
        logger.exception("DeepSeek API error")
        return JsonResponse({"error": "Failed to get response from AI"}, status=502)

    # Save assistant's reply (IMPORTANT: assign it)
    assistant_msg = ChatMessage.objects.create(
        session=session,
        role="assistant",
        content=reply,
    )

    # Update title + updated_at once
    update_fields = ["updated_at"]
    session.updated_at = timezone.now()

    if not session.title or session.title == "New Chat":
        session.title = user_msg[:60].strip() + "..." if len(user_msg) > 60 else user_msg
        update_fields.append("title")

    session.save(update_fields=update_fields)

    return JsonResponse({
        "reply": reply,
        "mode_used": mode,
        "message_id": assistant_msg.id,  # <-- now valid
    })


# =========================
# CHAT HIGHLIGHTS API
# =========================
@login_required
@require_http_methods(["GET", "POST", "DELETE"])
def chat_highlights(request: HttpRequest) -> JsonResponse:
    user = request.user

    # ── Resolve session from GET param (used mostly for GET) ──
    session_id_from_get = request.GET.get("session")

    # ── GET: List highlights for a session ──
    if request.method == "GET":
        qs = Highlight.objects.filter(user=user, source="chat")
        if session_id_from_get:
            qs = qs.filter(chat_session_id=session_id_from_get)

        data = [
            {
                "id": h.id,
                "text": h.highlighted_text,
                "message_id": h.chat_message_id if hasattr(h, 'chat_message') and h.chat_message else None,
            }
            for h in qs.order_by("created_at")
        ]
        return JsonResponse(data, safe=False)

    # ── POST: Create highlight ──
    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        text = (payload.get("text") or "").strip()
        message_id = payload.get("message_id")
        session_id = payload.get("session_id")  # optional, fallback if no message_id

        if not text:
            return JsonResponse({"error": "Text is required"}, status=400)

        # Daily limit
        subscription = Subscription.objects.filter(user=user).first()
        if subscription and subscription.tier == "FREE":
            today = timezone.now().date()
            if Highlight.objects.filter(user=user, created_at__date=today).count() >= 3:
                return JsonResponse(
                    {"error": "Daily highlight limit reached", "limit_reached": True},
                    status=403,
                )

        chat_message = None
        session = None

        # If message_id provided → use it to get session and enforce one per message
        if message_id:
            chat_message = get_object_or_404(
                ChatMessage, id=message_id, session__user=user
            )
            session = chat_message.session

            # Check if already highlighted (toggle behavior)
            existing = Highlight.objects.filter(
                user=user,
                source="chat",
                chat_message=chat_message
            ).first()
            if existing:
                return JsonResponse(
                    {
                        "id": existing.id,
                        "text": existing.highlighted_text,
                        "message_id": existing.chat_message_id,
                        "already_exists": True,
                    },
                    status=200,
                )

        # Fallback for text-only highlights (Shift + select)
        else:
            if not session_id:
                return JsonResponse({"error": "session_id required for text-only highlight"}, status=400)
            session = get_object_or_404(ChatSession, id=session_id, user=user)

        # Create
        new_highlight = Highlight.objects.create(
            user=user,
            source="chat",
            chat_session=session,
            chat_message=chat_message,  # safe even if None
            highlighted_text=text,
        )

        profile = user.profile
        profile.total_highlights += 1
        profile.save(update_fields=["total_highlights"])

        return JsonResponse(
            {
                "id": new_highlight.id,
                "text": new_highlight.highlighted_text,
                "message_id": new_highlight.chat_message_id if new_highlight.chat_message else None,
            },
            status=201,
        )

    # ── DELETE: Remove highlight ──
    if request.method == "DELETE":
        try:
            payload = json.loads(request.body.decode("utf-8")) if request.body else {}
        except Exception:
            payload = {}

        message_id = payload.get("message_id")
        text = payload.get("text", "").strip()

        qs = Highlight.objects.filter(user=user, source="chat")

        if message_id:
            qs = qs.filter(chat_message_id=message_id)
        elif text:
            qs = qs.filter(highlighted_text__exact=text)
        else:
            return JsonResponse({"error": "message_id or text required for delete"}, status=400)

        deleted_count, _ = qs.delete()

        if deleted_count == 0:
            return JsonResponse({"error": "No matching highlight found"}, status=404)

        return JsonResponse({"success": True, "deleted_count": deleted_count})
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

@login_required
@require_http_methods(["DELETE"])
def chat_highlight_detail(request: HttpRequest, highlight_id: int) -> JsonResponse:
    h = Highlight.objects.filter(id=highlight_id, user=request.user, source="chat").first()
    if not h:
        return JsonResponse({"error": "Not found"}, status=404)

    h.delete()

    # keep profile count sane
    profile = request.user.profile
    if profile.total_highlights > 0:
        profile.total_highlights -= 1
        profile.save(update_fields=["total_highlights"])

    return JsonResponse({"ok": True})

