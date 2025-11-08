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

from accounts.models import (
    Subscription,
    Profile,
    ChatSession,
    ChatMessage,
)
from subplayer.models import Highlight  # Highlight lives in subplayer

logger = logging.getLogger(__name__)


@login_required
def chat(request: HttpRequest) -> HttpResponse:
    """
    Render the main chat page with:
    - list of this user's ChatSession objects (history)
    - the currently selected session
    - that session's messages
    """
    user = request.user

    # If ?new=1, create a fresh session
    if request.GET.get("new") == "1":
        session = ChatSession.objects.create(user=user, title="")
    else:
        # If ?session=<id>, try to load that
        session_id = request.GET.get("session")
        session = None
        if session_id:
            session = ChatSession.objects.filter(user=user, pk=session_id).first()

        # Fallback: last updated session
        if session is None:
            session = (
                ChatSession.objects.filter(user=user)
                .order_by("-updated_at")
                .first()
            )

        # If still none, create a new one
        if session is None:
            session = ChatSession.objects.create(user=user, title="")

    # All sessions for left-side history list
    sessions = (
        ChatSession.objects.filter(user=user)
        .order_by("-updated_at")
    )

    # Messages for the current session
    messages = session.messages.all()

    context = {
        "sessions": sessions,
        "current_session": session,
        "messages": messages,
    }
    # Your template is currently in subplayer/templates/chat.html, but
    # since it's named "chat.html" this render will still find it.
    return render(request, "chat.html", context)


@login_required
@csrf_exempt  # you *are* sending CSRF, but keeping this avoids issues if token ever missing
def chat_api(request: HttpRequest) -> JsonResponse:
    """
    POST /chat/api/
    JSON body: { "message": "...", "mode": "normal|explain|roleplay|quiz|review" }

    Uses the most recently updated ChatSession for this user,
    saves user+assistant messages, and returns: { "reply": "..." } or { "error": "..." }
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed."}, status=405)

    # 1) Parse input safely
    try:
        payload_in = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    user_msg = (payload_in.get("message") or "").strip()
    mode = (payload_in.get("mode") or "normal").lower()
    if not user_msg:
        return JsonResponse({"error": "Empty message."}, status=400)

    user = request.user

    # 2) Get or create the active ChatSession for this user
    session = (
        ChatSession.objects.filter(user=user)
        .order_by("-updated_at")
        .first()
    )
    if session is None:
        session = ChatSession.objects.create(user=user, title="")

    # Save the user message
    ChatMessage.objects.create(
        session=session,
        role="user",
        content=user_msg,
    )

    # 3) Resolve API key
    api_key = getattr(settings, "DEEPSEEK_API_KEY", None) or os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        logger.error("DEEPSEEK_API_KEY missing")
        return JsonResponse({"error": "Server not configured for DeepSeek."}, status=500)

    # 4) Build system prompt based on mode
    base_prompt = (
        "You are a patient, upbeat Chinese language tutor. "
        "Use simple, clear explanations and give 1–2 examples. "
        "When you use Chinese characters, also provide pinyin and brief English glosses "
        "for key words. Keep answers focused and practical."
    )

    if mode == "explain":
        system_prompt = (
            base_prompt
            + " The user wants detailed breakdowns of Chinese sentences: "
              "explain grammar, give pinyin, tone hints, and key vocabulary."
        )
    elif mode == "roleplay":
        system_prompt = (
            base_prompt
            + " The user wants a role-play conversation: stay mostly in Chinese, "
              "keep responses short and interactive, correct mistakes gently, "
              "and occasionally explain in English when needed."
        )
    elif mode == "quiz":
        system_prompt = (
            base_prompt
            + " The user wants to be quizzed on Chinese. Ask short questions "
              "(sometimes multiple-choice or fill-in-the-blank), wait for answers, "
              "and then correct and explain."
        )
    elif mode == "review":
        system_prompt = (
            base_prompt
            + " The user is reviewing previously highlighted Chinese snippets. "
              "Use ONLY the provided highlight texts to create quizzes, example sentences, "
              "or reading comprehension activities that help them recall and internalize "
              "the phrases."
        )
    else:
        system_prompt = base_prompt

    body = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            # Simple context: just system + latest user message
            {"role": "user", "content": user_msg},
        ],
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # 5) Call DeepSeek with robust error handling
    try:
        r = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=body,
            timeout=30,
        )
    except requests.Timeout:
        logger.exception("DeepSeek timeout")
        return JsonResponse({"error": "Upstream timeout. Please try again."}, status=504)
    except Exception as e:
        logger.exception("DeepSeek request failed")
        return JsonResponse({"error": f"Upstream error: {e}"}, status=502)

    # 6) Handle non-200 responses
    if r.status_code != 200:
        logger.error("DeepSeek non-200: %s %s", r.status_code, r.text[:500])
        return JsonResponse(
            {"error": f"DeepSeek error {r.status_code}", "details": r.text[:500]},
            status=502,
        )

    # 7) Extract reply safely
    try:
        data = r.json()
        reply = data["choices"][0]["message"]["content"]
    except Exception:
        logger.exception("Unexpected DeepSeek payload: %s", r.text[:1000])
        return JsonResponse({"error": "Unexpected response shape from DeepSeek."}, status=502)

    # Save assistant message
    ChatMessage.objects.create(
        session=session,
        role="assistant",
        content=reply,
    )

    # Update session timestamps and title (first user message snippet as title)
    if not session.title:
        session.title = (user_msg[:80] + "…") if len(user_msg) > 80 else user_msg
    session.updated_at = timezone.now()
    session.save(update_fields=["title", "updated_at"])

    return JsonResponse({"reply": reply})


@login_required
@require_http_methods(["GET", "POST"])
def chat_highlights(request: HttpRequest) -> JsonResponse:
    """
    /chat/api/highlights/

    GET  -> list all chat highlights for this user:  [{id, text}, ...]
    POST -> create a new chat highlight from selected text: {text: "..."}

    Reuses same daily limit logic as video highlights for FREE users.
    """
    user = request.user

    # ------ GET: list highlights ------
    if request.method == "GET":
        highlights = Highlight.objects.filter(
            user=user,
            source="chat",
        ).order_by("created_at")

        data = [{"id": h.id, "text": h.highlighted_text} for h in highlights]
        return JsonResponse(data, safe=False)

    # ------ POST: create highlight ------
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    text = (payload.get("text") or "").strip()
    if not text:
        return JsonResponse({"error": "Text is required"}, status=400)

    # Daily limit: reuse same rule as create_highlight (3 / day for FREE)
    try:
        subscription = Subscription.objects.get(user=user)
    except Subscription.DoesNotExist:
        subscription = None

    if subscription and subscription.tier == "FREE":
        today = timezone.now().date()
        highlights_today = Highlight.objects.filter(
            user=user,
            created_at__date=today,
        ).count()

        if highlights_today >= 3:
            return JsonResponse(
                {
                    "error": "You have reached the daily limit of 3 highlights. Upgrade to create more.",
                    "limit_reached": True,
                },
                status=403,
            )

    # Create chat highlight (no media/timing)
    new_highlight = Highlight.objects.create(
        user=user,
        source="chat",
        media=None,
        highlighted_text=text,
        start_time=0,
        end_time=0,
        start_index=0,
        end_index=len(text),
        start_sentence_index=0,
        end_sentence_index=0,
        frame_index=0,
    )

    # Update profile highlight count
    profile: Profile = user.profile
    profile.total_highlights += 1
    profile.save()

    return JsonResponse(
        {
            "id": new_highlight.id,
            "text": new_highlight.highlighted_text,
            "total_points": profile.total_points,
        },
        status=201,
    )
