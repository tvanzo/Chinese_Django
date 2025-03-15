from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db.models import Sum
from django.core.serializers import serialize
from django.conf import settings
from django.db.models import Count, Exists, OuterRef, Q
from subplayer.models import Category

from django.http import HttpResponse
from reportlab.pdfgen import canvas

import logging
import json
import os
import re
from math import ceil

from .models import Media, Highlight, UserMediaStatus, Channel
from accounts.models import Profile, MediaProgress
from .forms import MediaForm, SearchForm
from .youtube_utils import fetch_video_details, process_and_save_subtitles, parse_duration,  get_channel_profile_pic, fetch_channel_details
from googleapiclient.discovery import build
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q

from django.shortcuts import get_object_or_404, render
from django.core.serializers import serialize
from django.db.models import Sum, Count, Q, Subquery, OuterRef
from django.db.models.functions import TruncDay
from django.utils import timezone
import json
from django.shortcuts import get_object_or_404, render
from django.core.serializers import serialize
from django.db.models import Count
import json
def format_duration(seconds):
    """Helper function to convert seconds to 'minutes:seconds' format."""
    minutes = seconds // 60
    remainder_seconds = seconds % 60
    return f"{minutes}m {remainder_seconds}s"

# Set up logging
logger = logging.getLogger(__name__)
from django.contrib import messages

@login_required
def add_media(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            youtube_url = data.get('youtube_url')
            if not youtube_url:
                return JsonResponse({'status': 'error', 'message': 'No YouTube URL provided.'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'})

        logger.info(f"Fetching video details for URL: {youtube_url}")
        video_details = fetch_video_details(youtube_url)
        if video_details['status'] == 'valid':
            # Check if the video has Chinese subtitles
            if not video_details.get('subtitles_file_path'):
                return JsonResponse({'status': 'error', 'message': 'Video does not have Chinese subtitles.'})

            video_id = video_details['video_id']

            # Check if the video already exists in the database
            existing_media = Media.objects.filter(media_id=video_id).first()
            if existing_media:
                # Check if the video is already in the user's added_media
                if request.user.added_media.filter(id=existing_media.id).exists():
                    return JsonResponse({'status': 'success', 'message': 'Video already in your library.'})
                else:
                    request.user.added_media.add(existing_media)
                    return JsonResponse({'status': 'success', 'message': 'Video successfully added to your library.'})

            # Fetch and save channel details
            channel_details = fetch_channel_details(f"https://www.youtube.com/channel/{video_details['channel_id']}")
            if channel_details:
                channel, created = Channel.objects.update_or_create(
                    channel_id=channel_details['channel_id'],
                    defaults={
                        'name': channel_details['channel_name'],
                        'url': f"https://www.youtube.com/channel/{channel_details['channel_id']}",
                        'profile_pic_url': channel_details['profile_pic_url']
                    }
                )
                if created:
                    logger.info(f"New channel created: {channel.name} with ID {channel.channel_id}")
                else:
                    logger.info(f"Channel updated: {channel.name} with ID {channel.channel_id}")
            else:
                logger.error("Failed to fetch or update channel details.")
                return JsonResponse({'status': 'error', 'message': 'Failed to fetch or update channel details.'})

            # Save new media details
            try:
                new_media = Media(
                    title=video_details['title'],
                    media_type='video',
                    media_id=video_id,
                    youtube_video_id=video_id,
                    url=youtube_url,
                    thumbnail_url=video_details['thumbnail_url'],
                    video_length=video_details['video_length'],
                    word_count=int(video_details.get('word_count', 0)),
                    channel=channel,
                    category=video_details.get('category_id', 'Unknown')
                )

                subtitles_path = video_details.get('subtitles_file_path')
                if subtitles_path:
                    full_path = os.path.join(settings.MEDIA_ROOT, subtitles_path)
                    with open(full_path, 'rb') as f:
                        new_media.subtitle_file.save(os.path.basename(subtitles_path), ContentFile(f.read()))
                    logger.info(f"Subtitles file saved for {youtube_url} at {full_path}")

                new_media.save()
                logger.info(f"Media added successfully: {new_media.title}")

                # Add the media to the user's added_media
                request.user.added_media.add(new_media)

                return JsonResponse({'status': 'success', 'message': 'Video successfully added to your library.'})
            except Exception as e:
                logger.error(f"Failed to add new media for {youtube_url}: {e}")
                return JsonResponse({'status': 'error', 'message': 'Failed to add new media.'})
        else:
            logger.error(f"Failed to fetch video details for {youtube_url}: {video_details['message']}")
            return JsonResponse({'status': 'error', 'message': video_details.get('message', 'Failed to fetch video details.')})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

@login_required
def myapp_view(request):
    return render(request, 'subplayer.html')

def podcast_view(request):
    media_id = request.GET.get('media_id')  # Get the media_id parameter from the URL
    context = {'media_id': media_id}
    return render(request, 'podcast.html', context)

def video_view(request):
    media_id = request.GET.get('media_id')  # Get the media_id parameter from the URL
    context = {'media_id': media_id}
    return render(request, 'video.html', context)

@login_required
def podcast_detail(request, media_id):
    media = get_object_or_404(Media, media_id=media_id, media_type='audio')

    media_serialized = serialize('json', [media])
    media_dict = json.loads(media_serialized)[0]['fields']
    media_dict['media_id'] = media.media_id
    media_dict['media_type'] = media.media_type
    media_dict['model'] = str(media._meta)
    media_dict['url'] = media.subtitle_file.url

    media_json = json.dumps(media_dict)

    context = {'media': media, 'media_json': media_json}
    return render(request, 'subplayer.html', context)

@login_required
@login_required

@login_required


@login_required
@login_required
@login_required
def video_detail(request, media_id):
    media = get_object_or_404(Media, media_id=media_id, media_type='video')
    highlights = Highlight.objects.filter(media=media, user=request.user)

    # Function to sort highlights based on frame index, sentence index, and start index
    def sort_highlights(highlight):
        return (highlight.frame_index, highlight.start_sentence_index, highlight.start_index)

    sorted_highlights = sorted(highlights, key=sort_highlights)

    user_media_status = UserMediaStatus.objects.filter(user=request.user, media=media).first()
    media_status = user_media_status.status if user_media_status else 'none'

    media_serialized = serialize('json', [media])
    media_dict = json.loads(media_serialized)[0]['fields']
    media_dict['media_id'] = media.media_id
    media_dict['media_type'] = media.media_type
    media_dict['model'] = str(media._meta)
    media_dict['url'] = media.subtitle_file.url
    media_dict['video_length'] = media.video_length
    media_dict['word_count'] = media.word_count

    media_json = json.dumps(media_dict)

    profile = request.user.profile

    # Get the user's last media progress for the current media
    last_media_progress = MediaProgress.objects.filter(profile=profile, media=media).last()

    context = {
        'media': media,
        'media_json': media_json,
        'highlights': sorted_highlights,
        'has_status': user_media_status is not None,
        'media_status': media_status,
        'hide_nav': True,
        'total_minutes': profile.total_minutes / 60,  # Keep this if used elsewhere
        'last_media_progress': last_media_progress,
    }

    return render(request, 'subplayer.html', context)
import os



from django.db.models import Exists, OuterRef

from django.db.models import OuterRef, Exists

from django.db.models import OuterRef, Exists

from django.db.models import Exists, OuterRef


@login_required
def media_list(request):
    user = request.user
    today = timezone.now().date()

    # Time span filtering
    time_span = request.GET.get('span', 'all')
    if time_span == 'day':
        start_date = today
    elif time_span == 'month':
        start_date = today.replace(day=1)
    else:
        start_date = None

    # Category filtering
    category_filter = request.GET.get('category', '').lower()

    # Fetch all media with annotations and optimizations
    all_media = Media.objects.select_related('channel').prefetch_related('categories', 'channel__categories').annotate(
        user_highlights_count=Count('highlights', filter=Q(highlights__user=user)),
        is_in_log=Exists(UserMediaStatus.objects.filter(media=OuterRef('pk'), user=user)) |
                  Exists(user.added_media.filter(id=OuterRef('pk')))
    )

    # Apply category filter if specified
    if category_filter and category_filter != 'all':
        all_media = all_media.filter(
            Q(categories__name__iexact=category_filter) |
            Q(channel__categories__name__iexact=category_filter)
        ).distinct()

    # Fetch user media statuses
    user_media_statuses = UserMediaStatus.objects.filter(user=user).select_related('media')
    media_statuses = {entry.media_id: entry.status for entry in user_media_statuses}

    # Attach additional attributes to each media object
    for media in all_media:
        media.status = media_statuses.get(media.id, "Not Available")
        media.formatted_video_length = format_duration(media.video_length)
        media.time_ago = time_ago(media.youtube_upload_time)

    # Progress stats
    progress_filters = {'profile': user.profile}
    if start_date:
        progress_filters['date__gte'] = start_date
    progress_entries = MediaProgress.objects.filter(**progress_filters)

    total_minutes = progress_entries.aggregate(sum_minutes=Sum('minutes_watched'))['sum_minutes'] or 0
    total_words = progress_entries.aggregate(sum_words=Sum('words_learned'))['sum_words'] or 0
    total_highlights = Highlight.objects.filter(user=user).count()

    # Get all categories relevant to the media
    categories = Category.objects.filter(
        Q(media__in=all_media) | Q(channels__media__in=all_media)
    ).distinct()

    # Get channels with media count
    channels = Channel.objects.annotate(media_count=Count('media'))

    context = {
        'media': all_media,
        'total_minutes': round(total_minutes, 2),
        'total_words': total_words,
        'total_highlights': total_highlights,
        'channels': channels,
        'categories': categories,
        'selected_category': category_filter or 'all',
    }

    return render(request, 'watch.html', context)


def dictionary_lookup(request):
    word = request.GET.get('word', '')
    try:
        entry = DictionaryEntry.objects.get(word=word)
        return JsonResponse({'word': word, 'definition': entry.definition})
    except DictionaryEntry.DoesNotExist:
        return JsonResponse({'error': 'Word not found'}, status=404)



def search(request):
    search_results = []
    form = SearchForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        query = form.cleaned_data['query']

        # Initialize the Filmot client
        filmot = Filmot()

        # Set your RapidAPI key
        filmot.set_rapidapi_key("f463dda2e4mshb4bb8c3e659f680p110c46jsne3b83c22aa8b")

        try:
            # Perform the search
            response = filmot.search(query, limit=2, language=Language.ENGLISH)
            
            # Process the response
            if response:  # Ensure response is not None
                for video in response[:1]:
                    hits = video.hits_data() if video.hits_data() else []
                    for hit in hits:  # Ensure hits_data is not None
                        search_results.append({
                            'link': hit['link'],
                            'text': hit['text']
                        })
        except Exception as e:
            print(f"An error occurred: {e}")
            # Optionally, add a message to display to the user that an error occurred

    return render(request, 'search.html', {'form': form, 'search_results': search_results})


def video_completion_stats(request):
    if not request.user.is_authenticated:
        return {}

    completed_media_ids = UserMediaStatus.objects.filter(
        user=request.user,
        status='completed'
    ).values_list('media_id', flat=True)

    total_minutes = Media.objects.filter(
        id__in=completed_media_ids
    ).annotate(total_duration=Sum('video_length')).aggregate(Sum('total_duration'))['total_duration__sum'] or 0

    total_words = Media.objects.filter(
        id__in=completed_media_ids
    ).aggregate(total_word_count=Sum('word_count'))['total_word_count'] or 0

    # Convert total_minutes to the desired format if necessary

    return {
        'total_minutes': total_minutes,
        'total_words': total_words,
    }
@login_required
def channel_view(request, channel_name):
    channel = get_object_or_404(Channel, channel_id=channel_name)
    user = request.user

    media_list = Media.objects.filter(channel=channel).annotate(
        user_highlights_count=Count('highlights', filter=Q(highlights__user=user))
    )

    media_statuses = {entry.media_id: entry.status for entry in UserMediaStatus.objects.filter(media__in=media_list, user=user)}

    for media in media_list:
        media.status = media_statuses.get(media.id, "Not Available")
        media.formatted_video_length = format_duration(media.video_length)

    context = {
        'channel': channel,
        'media_list': media_list,
    }
    return render(request, 'channel.html', context)
def channels_list(request):
    channels = Channel.objects.annotate(media_count=Count('media'))
    context = {
        'channels': channels
    }
    return render(request, 'channels.html', context)
def intro_view(request):
    return render(request, 'intro.html')

# Set up logging
logger = logging.getLogger(__name__)

from django.utils import timezone

from django.utils import timezone
from datetime import datetime

def time_ago(datetime_str):
    # First, convert the string to a datetime object if it's not already one
    if isinstance(datetime_str, str):
        # Assuming the string is in ISO 8601 format with 'Z' at the end
        datetime_obj = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ")
        # Ensure the datetime is timezone-aware, converting from UTC
        datetime_obj = timezone.make_aware(datetime_obj, timezone=timezone.utc)
    else:
        # If it's already a datetime object, use it directly
        datetime_obj = datetime_str

    now = timezone.now()
    diff = now - datetime_obj

    if diff.days == 0 and diff.seconds < 60:
        return "just now"
    elif diff.days == 0:
        if diff.seconds < 3600:
            return f"{diff.seconds // 60} minutes ago"
        else:
            return f"{diff.seconds // 3600} hours ago"
    elif diff.days < 30:
        return f"{diff.days} days ago"
    elif diff.days < 365:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    else:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
import os
import json
import logging
from io import BytesIO
import requests
from django.conf import settings  # For static file paths
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect  # Use this instead of csrf_exempt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Configure logging
logger = logging.getLogger(__name__)

# Retrieve API key from environment
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    logger.error("DEEPSEEK_API_KEY is not set in environment variables.")

# Define font paths using STATIC_ROOT
font_path_regular = os.path.join(settings.STATIC_ROOT, "fonts", "NotoSerifSC-Regular.ttf")
font_path_bold = os.path.join(settings.STATIC_ROOT, "fonts", "NotoSerifSC-Bold.ttf")

# Register the fonts in ReportLab
try:
    pdfmetrics.registerFont(TTFont('NotoSerif', font_path_regular))
    pdfmetrics.registerFont(TTFont('NotoSerifBold', font_path_bold))
except Exception as e:
    logger.warning(f"Font registration failed: {e}. Ensure font files are in {font_path_regular} and {font_path_bold}.")

@csrf_protect  # Replace csrf_exempt with proper CSRF protection
def generate_pdf(request):
    """Generate a PDF study guide from a YouTube script for Chinese learners."""
    if request.method != "POST":
        return HttpResponse("Invalid request method", status=405)

    try:
        # Extract data from request
        data = json.loads(request.body)
        script_text = data.get("script_text")
        highlights = data.get("highlights", [])

        if not script_text:
            logger.error("No script text provided in request.")
            return HttpResponse("No script text provided", status=400)

        # Log received data
        logger.info("Received script_text: %s...", script_text[:100] if len(script_text) > 100 else script_text)
        logger.info("Received highlights: %s", highlights)

        # Chunk the script to ensure full coverage (max 2500 characters per chunk)
        CHUNK_SIZE = 2500
        script_chunks = [script_text[i:i + CHUNK_SIZE] for i in range(0, len(script_text), CHUNK_SIZE)]
        highlight_text = "\n".join(highlights) if highlights else "无亮点提供。"

        # Process the first chunk to generate title and summary
        first_chunk_prompt = f"""Using the provided Chinese script chunk and highlights, generate a title and summary for the entire video, and contribute to a comprehensive Chinese language study guide in JSON format for a 30-minute video, designed for intermediate-to-advanced learners (HSK 5-6 level). The title should be a descriptive, general title for the entire video content, without referencing specific parts or chunks.

Structure the JSON as follows:
{{
  "title": "A descriptive title in simplified Chinese based on the overall content (15-20 characters)",
  "summary": "A concise summary of the script in simplified Chinese (100-150 characters)",
  "vocabulary": [
    {{
      "chinese": "难词 (difficult word/phrase from this chunk)",
      "pinyin": "Accurate pinyin with tones",
      "english": "Precise English definition",
      "context": "The phrase/sentence from this chunk where this word appears",
      "difficulty": "HSK level (5-6) or '高级' if beyond HSK",
      "examples": [
        {{
          "chinese": "Example sentence using the word",
          "pinyin": "Full pinyin with tones",
          "english": "Natural English translation"
        }},
        ...2-3 unique examples per word, including at least one from this chunk if possible
      ]
    }},
    ...5-7 vocabulary items from this chunk
  ],
  "phrases": [
    {{
      "chinese": "Complete useful phrase from this chunk",
      "pinyin": "Full pinyin with tones",
      "english": "Natural English translation",
      "notes": "Brief usage notes or cultural context (optional)"
    }},
    ...2-4 phrases from this chunk
  ],
  "grammar_points": [
    {{
      "pattern": "Grammar pattern in Chinese from this chunk",
      "explanation": "Explanation in Chinese with English",
      "example": "Example from this chunk"
    }},
    ...1-2 grammar points from this chunk
  ],
  "cultural_notes": [
    "Brief cultural explanation related to specific content in this chunk (50-100 characters each)",
    ...1-2 notes from this chunk
  ]
}}

Selection criteria:
1. Analyze the ENTIRE chunk and select difficult words/phrases evenly from beginning, middle, and end.
2. Prioritize words/phrases from highlighted sections if they appear in this chunk.
3. Choose 5-7 difficult vocabulary words (HSK 5-6 or beyond, not basic level) unique to this chunk.
4. Provide 2-3 unique example sentences per word, including at least one from this chunk if possible.
5. Include Taiwan-specific or travel-related terms if relevant to this chunk.
6. Ensure a mix of nouns, verbs, adjectives, and idiomatic expressions.
7. Select practical phrases for real-world use.

All Chinese text must be in simplified characters. Pinyin must include tone marks and proper spacing. Ensure pinyin accuracy and contextually appropriate English definitions.

Highlights (prioritize these if present in this chunk):
{highlight_text}

Script Chunk 1 of {len(script_chunks)}:
{script_chunks[0]}
"""

        # Call DeepSeek API for the first chunk
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"  # Use variable directly
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You are a Chinese language expert creating comprehensive study guides for intermediate-to-advanced learners from 30-minute video transcripts."},
                {"role": "user", "content": first_chunk_prompt}
            ],
            "stream": False,
            "response_format": {"type": "json_object"}
        }
        response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload)
        if response.status_code != 200:
            logger.error("DeepSeek API Error for first chunk: %s", response.text)
            return HttpResponse(f"DeepSeek API Error for first chunk: {response.text}", status=500)

        # Parse first chunk response
        try:
            first_data = json.loads(response.json()["choices"][0]["message"]["content"])
            title = first_data["title"]
            summary = first_data["summary"]
            all_vocabulary = first_data.get("vocabulary", [])
            all_phrases = first_data.get("phrases", [])
            all_grammar_points = first_data.get("grammar_points", [])
            all_cultural_notes = first_data.get("cultural_notes", [])
        except (KeyError, json.JSONDecodeError) as e:
            logger.error("Invalid JSON response for first chunk: %s", str(e))
            return HttpResponse(f"Invalid JSON response for first chunk: {str(e)}", status=500)

        # Process remaining chunks
        for i in range(1, len(script_chunks)):
            chunk_prompt = f"""Using the provided Chinese script chunk and highlights, contribute to a comprehensive Chinese language study guide in JSON format for a 30-minute video, designed for intermediate-to-advanced learners (HSK 5-6 level).

Structure the JSON as follows:
{{
  "vocabulary": [
    {{
      "chinese": "难词 (difficult word/phrase from this chunk)",
      "pinyin": "Accurate pinyin with tones",
      "english": "Precise English definition",
      "context": "The phrase/sentence from this chunk where this word appears",
      "difficulty": "HSK level (5-6) or '高级' if beyond HSK",
      "examples": [
        {{
          "chinese": "Example sentence using the word",
          "pinyin": "Full pinyin with tones",
          "english": "Natural English translation"
        }},
        ...2-3 unique examples per word, including at least one from this chunk if possible
      ]
    }},
    ...5-7 vocabulary items from this chunk
  ],
  "phrases": [
    {{
      "chinese": "Complete useful phrase from this chunk",
      "pinyin": "Full pinyin with tones",
      "english": "Natural English translation",
      "notes": "Brief usage notes or cultural context (optional)"
    }},
    ...2-4 phrases from this chunk
  ],
  "grammar_points": [
    {{
      "pattern": "Grammar pattern in Chinese from this chunk",
      "explanation": "Explanation in Chinese with English",
      "example": "Example from this chunk"
    }},
    ...1-2 grammar points from this chunk
  ],
  "cultural_notes": [
    "Brief cultural explanation related to specific content in this chunk (50-100 characters each)",
    ...1-2 notes from this chunk
  ]
}}

Selection criteria:
1. Analyze the ENTIRE chunk and select difficult words/phrases evenly from beginning, middle, and end.
2. Prioritize words/phrases from highlighted sections if they appear in this chunk.
3. Choose 5-7 difficult vocabulary words (HSK 5-6 or beyond, not basic level) unique to this chunk.
4. Provide 2-3 unique example sentences per word, including at least one from this chunk if possible.
5. Include Taiwan-specific or travel-related terms if relevant to this chunk.
6. Ensure a mix of nouns, verbs, adjectives, and idiomatic expressions.
7. Select practical phrases for real-world use.

All Chinese text must be in simplified characters. Pinyin must include tone marks and proper spacing. Ensure pinyin accuracy and contextually appropriate English definitions.

Highlights (prioritize these if present in this chunk):
{highlight_text}

Script Chunk {i + 1} of {len(script_chunks)}:
{script_chunks[i]}
"""

            # Call DeepSeek API for this chunk
            response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are a Chinese language expert creating comprehensive study guides for intermediate-to-advanced learners from 30-minute video transcripts."},
                    {"role": "user", "content": chunk_prompt}
                ],
                "stream": False,
                "response_format": {"type": "json_object"}
            })
            if response.status_code != 200:
                logger.error("DeepSeek API Error for chunk %d: %s", i + 1, response.text)
                return HttpResponse(f"DeepSeek API Error for chunk {i + 1}: {response.text}", status=500)

            # Parse chunk response
            try:
                chunk_data = json.loads(response.json()["choices"][0]["message"]["content"])
                all_vocabulary.extend(chunk_data.get("vocabulary", []))
                all_phrases.extend(chunk_data.get("phrases", []))
                all_grammar_points.extend(chunk_data.get("grammar_points", []))
                all_cultural_notes.extend(chunk_data.get("cultural_notes", []))
            except (KeyError, json.JSONDecodeError) as e:
                logger.error("Invalid JSON response for chunk %d: %s", i + 1, str(e))
                return HttpResponse(f"Invalid JSON response for chunk {i + 1}: {str(e)}", status=500)

        # Deduplicate and limit items
        def deduplicate(items, key, max_items):
            seen = set()
            result = []
            for item in items:
                identifier = item.get(key)
                if identifier not in seen:
                    seen.add(identifier)
                    result.append(item)
                    if len(result) >= max_items:
                        break
            return result

        study_guide = {
            "title": title,
            "summary": summary,
            "vocabulary": deduplicate(all_vocabulary, "chinese", 20),
            "phrases": deduplicate(all_phrases, "chinese", 10),
            "grammar_points": deduplicate(all_grammar_points, "pattern", 5),
            "cultural_notes": all_cultural_notes[:5]  # No deduplication for notes
        }

        # Set up PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=60, rightMargin=60, topMargin=72, bottomMargin=72)

        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontName='NotoSerifBold', fontSize=20, leading=24, alignment=1, textColor=colors.HexColor('#2C3E50'), spaceAfter=16)
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading1'], fontName='NotoSerifBold', fontSize=16, leading=20, textColor=colors.HexColor('#3498DB'), spaceBefore=24, spaceAfter=12)
        normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontName='NotoSerif', fontSize=11, leading=16, spaceBefore=4, spaceAfter=4)
        vocab_style = ParagraphStyle('VocabStyle', parent=normal_style, leftIndent=20, firstLineIndent=-20)
        example_style = ParagraphStyle('ExampleStyle', parent=normal_style, leftIndent=30, spaceBefore=6, spaceAfter=6, borderWidth=1, borderColor=colors.HexColor('#E0E0E0'), borderPadding=8, borderRadius=5)
        note_style = ParagraphStyle('NoteStyle', parent=normal_style, fontName='NotoSerif', fontSize=10, leading=14, textColor=colors.HexColor('#7F8C8D'), leftIndent=20)

        # Add page numbers and header
        def add_page_number(canvas, doc):
            canvas.saveState()
            canvas.setFont('NotoSerifBold', 10)
            canvas.setFillColor(colors.HexColor('#3498DB'))
            canvas.drawString(72, 720, study_guide["title"])
            canvas.setFont('NotoSerif', 10)
            canvas.setFillColor(colors.gray)
            page_num = canvas.getPageNumber()
            text = f"第 {page_num} 页"
            canvas.drawRightString(540, 36, text)
            canvas.setStrokeColor(colors.HexColor('#E0E0E0'))
            canvas.line(72, 710, 540, 710)
            canvas.line(72, 50, 540, 50)
            canvas.restoreState()

        # Build flowables
        flowables = [Paragraph(study_guide["title"], title_style)]
        flowables.append(Paragraph("内容摘要", heading_style))
        flowables.append(Paragraph(study_guide["summary"], normal_style))
        flowables.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E0E0E0'), spaceBefore=12, spaceAfter=12))

        # Vocabulary
        if study_guide["vocabulary"]:
            flowables.append(Paragraph("重点词汇", heading_style))
            for i, word in enumerate(study_guide["vocabulary"]):
                word_text = f'<b>{i + 1}. <font color="#E74C3C">{word.get("chinese", "未知")}</font></b> <font color="#7F8C8D">[{word.get("pinyin", "无拼音")}]</font><br/><b>释义：</b>{word.get("english", "无定义")}'
                flowables.append(Paragraph(word_text, vocab_style))
                if word.get("context"):
                    flowables.append(Paragraph(f'<b>语境：</b><i>"{word["context"]}"</i>', example_style))
                for ex in word.get("examples", []):
                    ex_text = f'<font color="black">{ex.get("chinese", "无例句")}</font><br/><font color="gray">{ex.get("pinyin", "无拼音")}</font><br/><font color="gray">{ex.get("english", "无翻译")}</font>'
                    flowables.append(Paragraph(ex_text, example_style))
                if word.get("difficulty"):
                    flowables.append(Paragraph(f'<b>难度：</b>{word["difficulty"]}', note_style))
                flowables.append(Spacer(1, 10))
        else:
            flowables.append(Paragraph("未提供重点词汇。", normal_style))
        flowables.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E0E0E0'), spaceBefore=12, spaceAfter=12))

        # Phrases
        if study_guide["phrases"]:
            flowables.append(Paragraph("实用短语", heading_style))
            for i, phrase in enumerate(study_guide["phrases"]):
                phrase_text = f'<b>{i + 1}. <font color="#E74C3C">{phrase.get("chinese", "未知")}</font></b> <font color="#7F8C8D">[{phrase.get("pinyin", "无拼音")}]</font><br/><b>翻译：</b>{phrase.get("english", "无翻译")}'
                flowables.append(Paragraph(phrase_text, vocab_style))
                if phrase.get("notes"):
                    flowables.append(Paragraph(f'<b>笔记：</b>{phrase["notes"]}', note_style))
                flowables.append(Spacer(1, 8))
        else:
            flowables.append(Paragraph("未提供实用短语。", normal_style))
        flowables.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E0E0E0'), spaceBefore=12, spaceAfter=12))

        # Grammar Points
        if study_guide["grammar_points"]:
            flowables.append(Paragraph("语法要点", heading_style))
            for i, gp in enumerate(study_guide["grammar_points"]):
                gp_text = f'<b>{i + 1}. <font color="#2980B9">{gp.get("pattern", "未知")}</font></b><br/><b>解释：</b>{gp.get("explanation", "无解释")}'
                flowables.append(Paragraph(gp_text, normal_style))
                if gp.get("example"):
                    flowables.append(Paragraph(f'<b>例句：</b><i>"{gp["example"]}"</i>', example_style))
                flowables.append(Spacer(1, 8))
        else:
            flowables.append(Paragraph("未提供语法要点。", normal_style))
        flowables.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E0E0E0'), spaceBefore=12, spaceAfter=12))

        # Cultural Notes
        if study_guide["cultural_notes"]:
            flowables.append(Paragraph("文化笔记", heading_style))
            for i, note in enumerate(study_guide["cultural_notes"]):
                flowables.append(Paragraph(f'<b>{i + 1}.</b> {note}', normal_style))
                flowables.append(Spacer(1, 6))
        else:
            flowables.append(Paragraph("未提供文化笔记。", normal_style))

        # Build PDF
        doc.build(flowables, onFirstPage=add_page_number, onLaterPages=add_page_number)

        # Prepare response
        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{title}_study_guide.pdf"'
        response.write(pdf)
        logger.info("PDF generated and sent successfully.")
        return response

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body.")
        return HttpResponse("Invalid JSON in request body", status=400)
    except requests.RequestException as e:
        logger.error("API request failed: %s", str(e))
        return HttpResponse(f"API request failed: {str(e)}", status=500)
    except Exception as e:
        logger.exception("Unexpected error generating PDF: %s", str(e))
        return HttpResponse(f"Internal error: {str(e)}", status=500)