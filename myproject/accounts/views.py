from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core import serializers
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from accounts.models import Profile, MediaProgress
from subplayer.models import Media, Highlight
import json, math  # <- Add this import at the top






def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')  # or wherever you want to redirect after successful registration
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def media_list(request):
    media_data = serializers.serialize('json', Media.objects.all())
    return render(request, 'media/list.html', {'media': media_data})

@login_required
def viewed_media_list(request):
    profile = Profile.objects.get(user_id=request.user.id)
    viewed_media = list(profile.viewed_media.values_list('media_id', flat=True))
    return JsonResponse({'viewed_media': viewed_media}, safe=False)

@login_required
def add_viewed_media(request):
    if request.method == 'POST':
        data = json.loads(request.body)  # Load the JSON from the request body
        media_id = data.get('mediaId')  # Get the mediaId from the data
        profile = Profile.objects.get(user_id=request.user.id)
        print(media_id)
        try:
            media = Media.objects.get(media_id=media_id)
            profile.viewed_media.add(media)
            print(media_id )
        except Media.DoesNotExist:
            print("Media not found")
            print(media_id)

        return JsonResponse({'status': 'ok'})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def get_media_progress(request, media_id):
    user_id = request.user.id
    try:
        progress = MediaProgress.objects.get(profile__user_id=user_id, media_id=media_id)
        return JsonResponse({'time_stopped': progress.time_stopped})
    except MediaProgress.DoesNotExist:
        return JsonResponse({'error': 'MediaProgress not found'}, status=404)

@login_required
def update_media_progress(request):
    print("update_media_progress called")  # <-- Add this

    if request.method == 'POST':
        data = json.loads(request.body)  # Load the JSON from the request body
        media_id = data.get('mediaId')  # Get the mediaId from the data
        progress = data.get('progress')  # Get the progress from the data

        try:
            # Get the current user's profile
            profile = Profile.objects.get(user_id=request.user.id)
            # Get the MediaProgress object for this media and profile
            media_progress = MediaProgress.objects.get(media_id=media_id, profile=profile)
            # Update the time_stopped attribute
            media_progress.time_stopped = progress
            # Save the changes
            print("progooo" + str(progress))
            print(media_progress.time_stopped)
            media_progress.save()

            return JsonResponse({'status': 'ok'})

        except (Profile.DoesNotExist, MediaProgress.DoesNotExist):
            return JsonResponse({'error': 'Profile or MediaProgress not found'}, status=404)

    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def create_highlight(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        media_obj = Media.objects.get(pk=data['media'])

        new_highlight = Highlight.objects.create(
            user=request.user,
            media=media_obj,
            start_time=data['start_time'],
            end_time=data['end_time'],
            highlighted_text=data['highlighted_text'],
            start_index=data['start_index'],
            end_index=data['end_index'],
            start_sentence_index=data['start_sentence_index'],
            end_sentence_index=data['end_sentence_index'],
            frame_index=data['frame_index']

        )
        new_highlight.save()

        return JsonResponse({'message': 'Highlight created!'}, status=201)

def get_highlights(request, media_id):
    highlights = Highlight.objects.filter(user_id=request.user.id, media_id=media_id)
    data = serializers.serialize('json', highlights)
    print(data)
    return JsonResponse(data, safe=False)
