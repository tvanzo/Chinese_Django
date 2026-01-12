# chat/views.py
import json
import os
import logging
import requests

from django.conf import settings
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

from accounts.models import Subscription, ChatSession, ChatMessage, ChatCategory
from subplayer.models import Highlight  # unified highlight model

logger = logging.getLogger(__name__)


# =========================
# CHAT PAGE
# =========================
@login_required
def chat(request: HttpRequest) -> HttpResponse:
    user = request.user
    category_id = request.GET.get("category")

    # Resolve active session
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
@require_http_methods(["POST"])
def chat_api(request: HttpRequest) -> JsonResponse:
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
    ChatMessage.objects.create(session=session, role="user", content=user_msg)

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
        temperature = 0.3
    elif mode == "review":
        system_prompt = (
            "You are a patient, upbeat Chinese language tutor reviewing previously "
            "highlighted Chinese snippets. Use simple explanations, give 1-2 natural "
            "examples. Include pinyin when useful. Keep answers clear and encouraging."
        )
        temperature = 0.7
    else:
        system_prompt = (
            "You are a patient, upbeat, encouraging Chinese language tutor. "
            "Use simple, clear explanations and give 1-2 good example sentences. "
            "Include pinyin (with tone marks) and brief English glosses when helpful. "
            "Be friendly and supportive. Keep most answers in Chinese when appropriate."
        )
        temperature = 0.7

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
                "temperature": temperature,
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

    # Save assistant reply (and return its id)
    assistant_msg = ChatMessage.objects.create(session=session, role="assistant", content=reply)

    # Update session
    update_fields = ["updated_at"]
    session.updated_at = timezone.now()
    if not session.title or session.title == "New Chat":
        session.title = user_msg[:60].strip() + "..." if len(user_msg) > 60 else user_msg
        update_fields.append("title")
    session.save(update_fields=update_fields)

    return JsonResponse({
        "reply": reply,
        "mode_used": mode,
        "message_id": assistant_msg.id,
    })


# =========================
# CHAT HIGHLIGHTS API
# =========================
@login_required
@require_http_methods(["GET", "POST"])
def chat_highlights(request: HttpRequest) -> JsonResponse:
    user = request.user

    # ---------- GET ----------
    if request.method == "GET":
        session_id = request.GET.get("session")
        qs = Highlight.objects.filter(user=user, source="chat")

        if session_id:
            qs = qs.filter(chat_session_id=session_id)

        data = [
            {
                "id": h.id,
                "text": h.highlighted_text,
                "message_id": h.chat_message_id,
            }
            for h in qs.order_by("created_at")
        ]
        return JsonResponse(data, safe=False)

    # ---------- POST ----------
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    text = (payload.get("text") or "").strip()
    session_id = payload.get("session_id")
    message_id = payload.get("message_id")

    # Require text for selection highlights
    # For message highlights, allow empty text (we can pull from ChatMessage)
    if not text and not message_id:
        return JsonResponse({"error": "Text is required"}, status=400)

    # Daily limit: ONLY enforce for FREE and ONLY for "chat" source
    subscription = Subscription.objects.filter(user=user).first()
    if subscription and subscription.tier == "FREE":
        today = timezone.now().date()
        if Highlight.objects.filter(user=user, source="chat", created_at__date=today).count() >= 3:
            return JsonResponse(
                {"error": "Daily highlight limit reached", "limit_reached": True},
                status=403,
            )

    chat_message = None
    session = None

    # ----- Message highlight (star) -----
    if message_id:
        chat_message = (
            ChatMessage.objects
            .filter(id=message_id, session__user=user)
            .select_related("session")
            .first()
        )
        if not chat_message:
            return JsonResponse({"error": "Message not found"}, status=404)

        session = chat_message.session

        if not text:
            text = (chat_message.content or "").strip()

        # one highlight per message
        existing = Highlight.objects.filter(
            user=user,
            source="chat",
            chat_message=chat_message
        ).first()

        if existing:
            # return existing (front-end can treat as already highlighted)
            return JsonResponse(
                {
                    "id": existing.id,
                    "text": existing.highlighted_text,
                    "message_id": existing.chat_message_id,
                    "already_exists": True,
                },
                status=200,
            )

    # ----- Selection highlight -----
    else:
        if not session_id:
            return JsonResponse({"error": "session_id is required"}, status=400)

        session = ChatSession.objects.filter(user=user, pk=session_id).first()
        if not session:
            return JsonResponse({"error": "Session not found"}, status=404)

    new_highlight = Highlight.objects.create(
        user=user,
        source="chat",
        chat_session=session,
        chat_message=chat_message,
        highlighted_text=text,
    )

    # Keep profile count sane (if Profile exists)
    try:
        profile = user.profile
        profile.total_highlights = max(0, (profile.total_highlights or 0) + 1)
        profile.save(update_fields=["total_highlights"])
    except Exception:
        pass

    return JsonResponse(
        {
            "id": new_highlight.id,
            "text": new_highlight.highlighted_text,
            "message_id": new_highlight.chat_message_id,
        },
        status=201,
    )


@login_required
@require_http_methods(["DELETE"])
def chat_highlight_detail(request: HttpRequest, highlight_id: int) -> JsonResponse:
    h = Highlight.objects.filter(id=highlight_id, user=request.user, source="chat").first()
    if not h:
        return JsonResponse({"error": "Not found"}, status=404)

    h.delete()

    try:
        profile = request.user.profile
        profile.total_highlights = max(0, (profile.total_highlights or 0) - 1)
        profile.save(update_fields=["total_highlights"])
    except Exception:
        pass

    return JsonResponse({"ok": True})


# =========================
# CATEGORIES
# =========================
@login_required
@require_http_methods(["POST"])
def set_chat_category(request: HttpRequest) -> JsonResponse:
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    session_id = payload.get("session_id")
    category_id = payload.get("category_id")

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

    session.updated_at = timezone.now()
    session.save(update_fields=["category", "updated_at"])
    return JsonResponse({"ok": True})


@login_required
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
