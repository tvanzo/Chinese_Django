from django.http import JsonResponse
from django.core.serializers import serialize
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Highlight
from django.contrib.auth.decorators import login_required
import json

import json
from .models import Media
from .models import Media, Highlight, UserMediaStatus  # Assuming UserMediaStatus is the model name

import logging
from django.db import models
from django.contrib.auth.models import User



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import MediaForm
from .models import Media, Highlight, UserMediaStatus
from .youtube_utils import fetch_video_details
from googleapiclient.discovery import build
import re
from .forms import SearchForm
from filmot import Filmot
from filmot import Categories, Countries, Language




@login_required
def add_media(request):
    if request.method == 'POST':
        youtube_url = request.POST.get('youtube_url')
        video_details = fetch_video_details(youtube_url)

        if video_details['status'] == 'valid':
            # Parse ISO 8601 duration format to "minutes:seconds"
            video_length = parse_duration(video_details.get('video_duration_iso', ''))

            new_media = Media.objects.create(
            title=video_details['title'],
            media_type='video',
            media_id=video_details['video_id'],
            youtube_video_id=video_details['video_id'],
            url=youtube_url,
            subtitle_file=video_details.get('subtitles_file_path', ''),
            thumbnail_url=video_details.get('thumbnail_url', ''),
            video_length=video_details.get('video_length', '')  # Save the video length
            )

            messages.success(request, 'Media added successfully!')
            return redirect('home')
        else:
            messages.error(request, video_details['message'])
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


# Set up logging
logger = logging.getLogger(__name__)
