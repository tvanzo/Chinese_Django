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

@login_required
@csrf_exempt
def create_highlight(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        new_highlight = Highlight.objects.create(
            user=request.user,
            media_id=data['media'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            highlighted_text=data['highlighted_text']
        )
        new_highlight.save()

        return JsonResponse({'message': 'Highlight created!'}, status=201)