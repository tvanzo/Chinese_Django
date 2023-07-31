from django.http import JsonResponse
from django.core.serializers import serialize
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Highlight
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

import json
from .models import Media
import logging
from django.db import models
from django.contrib.auth.models import User

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
    media_json = json.dumps(media_dict)

    context = {'media': media, 'media_json': media_json}
    return render(request, 'subplayer.html', context)

@login_required
def video_detail(request, media_id):
    media = get_object_or_404(Media, media_id=media_id, media_type='video')

    media_serialized = serialize('json', [media])
    media_dict = json.loads(media_serialized)[0]['fields']
    media_dict['media_id'] = media.media_id
    media_dict['media_type'] = media.media_type
    media_dict['model'] = str(media._meta)
    media_json = json.dumps(media_dict)

    context = {'media': media, 'media_json': media_json}
    return render(request, 'subplayer.html', context)

# Set up logging
logger = logging.getLogger(__name__)

@login_required
@csrf_exempt
def create_highlight(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        logger.info(f"Received data: {data}")  # Log the received data
        try:
            media_obj = Media.objects.get(pk=data['media'])
            new_highlight = Highlight.objects.create(
                user=request.user,
                media=media_obj,
                start_time=data['start_time'],
                end_time=data['end_time'],
                highlighted_text=data['highlighted_text'],
                frame_index=data['frame_index']
            )
        except ObjectDoesNotExist:
            return JsonResponse({'error': 'Media not found.'}, status=404)
        except Exception as e:
            logger.error(f"Error while creating highlight: {str(e)}")  # Log the error
            return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'message': 'Highlight created!'}, status=201)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)