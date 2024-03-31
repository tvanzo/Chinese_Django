from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db.models import Sum
from django.core.serializers import serialize
from django.conf import settings

import logging
import json
import os
import re

from .models import Media, Highlight, UserMediaStatus
from accounts.models import Profile
from .forms import MediaForm, SearchForm
from .youtube_utils import fetch_video_details, process_and_save_subtitles, parse_duration
from googleapiclient.discovery import build





# Set up logging
logger = logging.getLogger(__name__)
@login_required
def add_media(request):
    if request.method == 'POST':
        youtube_url = request.POST.get('youtube_url')
        logger.debug(f"Fetching video details for URL: {youtube_url}")

        video_details = fetch_video_details(youtube_url)
        if video_details['status'] == 'valid':
            try:
                new_media = Media(
                    title=video_details['title'],
                    media_type='video',
                    media_id=video_details['video_id'],
                    youtube_video_id=video_details['video_id'],
                    url=youtube_url,
                    thumbnail_url=video_details['thumbnail_url'],
                    video_length=video_details['video_length'],
                    word_count=video_details.get('word_count', 0)  # Ensure the model has a word_count field
                )

                if video_details.get('subtitles_file_path'):
                    subtitles_path = video_details['subtitles_file_path']
                    full_path = os.path.join(settings.MEDIA_ROOT, subtitles_path)
                    with open(full_path, 'rb') as f:
                        new_media.subtitle_file.save(os.path.basename(subtitles_path), ContentFile(f.read()))
                    logger.info(f"Subtitles file saved for {youtube_url} at {full_path}")

                new_media.save()
                messages.success(request, 'Media added successfully!')
                return redirect('home')
            except Exception as e:
                logger.error(f"Failed to add new media for {youtube_url}: {e}")
                messages.error(request, 'Failed to add new media.')
        else:
            logger.error(f"Failed to fetch video details for {youtube_url}: {video_details.get('message')}")
            messages.error(request, video_details.get('message', 'Failed to fetch video details.'))
    
    return render(request, 'media_list.html')




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
def video_detail(request, media_id):
    media = get_object_or_404(Media, media_id=media_id, media_type='video')
    highlights = Highlight.objects.filter(media=media, user=request.user)

    # Assuming UserMediaStatus has a 'status' field that contains the media status
    user_media_status = UserMediaStatus.objects.filter(user=request.user, media=media).first()

    media_status = user_media_status.status if user_media_status else 'none'

    media_serialized = serialize('json', [media])
    media_dict = json.loads(media_serialized)[0]['fields']
    media_dict['media_id'] = media.media_id
    media_dict['media_type'] = media.media_type
    media_dict['model'] = str(media._meta)
    media_dict['url'] = media.subtitle_file.url

    media_json = json.dumps(media_dict)

    context = {
        'media': media,
        'media_json': media_json,
        'highlights': highlights,
        'has_status': user_media_status is not None,
        'media_status': media_status,  # Include the media status in the context
        'hide_nav': True,
    }
    return render(request, 'subplayer.html', context)



def media_list(request):
    media_objects = Media.objects.all()
    return render(request, 'media_list.html', {'media': media_objects})





def parse_duration(duration):
    # Regular expression to match the duration format
    pattern = re.compile(r'PT(\d+H)?(\d+M)?(\d+S)?')
    match = pattern.match(duration)
    
    if match:  # Check if the pattern matched
        hours, minutes, seconds = match.groups()
        hours = int(hours[:-1]) if hours else 0
        minutes = int(minutes[:-1]) if minutes else 0
        seconds = int(seconds[:-1]) if seconds else 0

        # Convert hours to minutes
        total_minutes = hours * 60 + minutes
        return f'{total_minutes}:{seconds:02}'  # Format minutes:seconds with leading zeros for seconds
    else:
        return "0:00"  # Return a default value or handle the error as appropriate


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

# Set up logging
logger = logging.getLogger(__name__)
