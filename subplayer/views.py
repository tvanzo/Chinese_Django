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