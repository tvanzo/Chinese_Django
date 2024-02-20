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

import logging
from django.db import models
from django.contrib.auth.models import User



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import MediaForm
from .models import Media
from .youtube_utils import fetch_video_details
from googleapiclient.discovery import build


@login_required
def add_media(request):
    if request.method == 'POST':
        youtube_url = request.POST.get('youtube_url')

        # Use fetch_video_details from youtube_utils.py
        video_details = fetch_video_details(youtube_url)

        if video_details['status'] == 'valid':
            # Process and save the video details
            new_media = Media.objects.create(
                title=video_details['title'],
                media_type='video',  # Assuming all added media are videos
                media_id=video_details['video_id'],
                youtube_video_id=video_details['video_id'],
                url=youtube_url,
                # Assuming process_and_save_subtitles returns a relative path
                subtitle_file=video_details.get('subtitles_file_path', ''),
                thumbnail_url=video_details.get('thumbnail_url', '')  # Assuming you add thumbnail_url to fetch_video_details return
            )
            messages.success(request, 'Media added successfully!')
            return redirect('home')  # Adjust the redirect as necessary
        else:
            messages.error(request, video_details['message'])

    # Adjust the template name as necessary
    return render(request, 'add_media.html')

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

    # Fetch highlights for this media without ordering
    highlights = Highlight.objects.filter(media=media, user=request.user)

    media_serialized = serialize('json', [media])
    media_dict = json.loads(media_serialized)[0]['fields']
    media_dict['media_id'] = media.media_id
    media_dict['media_type'] = media.media_type
    media_dict['model'] = str(media._meta)
    media_dict['url'] = media.subtitle_file.url

    media_json = json.dumps(media_dict)

    # Pass both media and highlights to the context
    context = {
        'media': media, 
        'media_json': media_json,
        'highlights': highlights  # Add highlights to the context
    }
    return render(request, 'subplayer.html', context)


def media_list(request):
    media_objects = Media.objects.all()
    return render(request, 'media_list.html', {'media': media_objects})



# Set up logging
logger = logging.getLogger(__name__)
