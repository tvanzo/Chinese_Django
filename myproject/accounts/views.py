from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core import serializers
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from accounts.models import Profile, MediaProgress
from subplayer.models import Media, Highlight, UserMediaStatus
import json, math  # <- Add this import at the top
from youtube_transcript_api import YouTubeTranscriptApi 
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.db.models.functions import TruncDay
from django.db.models import Count, Sum
from datetime import datetime, timedelta
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
import json
import logging
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

from django.db.models import F





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
        media = get_object_or_404(Media, media_id=media_id)
        progress = MediaProgress.objects.filter(profile__user_id=user_id, media=media).last()
        if progress:
            return JsonResponse({'time_stopped': progress.time_stopped, 'lastUpdateTime': progress.minutes_watched})
        else:
            return JsonResponse({'error': 'MediaProgress not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




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
            media_progress = MediaProgress.objects.get(media__media_id=media_id, profile=profile)

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
    try:
        data = json.loads(request.body)
        media_obj = Media.objects.get(media_id=data['media'])  # Assuming 'media_id' is the field name

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
        user_profile = request.user.profile
        user_profile.total_highlights += 1
        user_profile.save()

        # Return the highlight details as JSON
        return JsonResponse({
            'id': new_highlight.id,
            'highlighted_text': new_highlight.highlighted_text,
            'media_id': new_highlight.media.media_id,  # Include media_id if needed for linking
            # Add any other details you might need on the frontend
        }, status=201)
    except Media.DoesNotExist:
        return JsonResponse({'error': 'Media not found'}, status=404)
    except KeyError as e:
        return JsonResponse({'error': f'Missing key in request data: {e}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
def delete_highlight(request, highlight_id):
    try:
        data = json.loads(request.body.decode('utf-8'))  # Parse JSON from the request body
        highlight_id = data['highlight_id']
        highlight = Highlight.objects.get(pk=highlight_id)

        # Check if the user has the right to delete this highlight
        if request.user == highlight.user:
            highlight.delete()
            user_profile = request.user.profile
            user_profile.total_highlights -= 1
            user_profile.save()
            return JsonResponse({'status': 'success'})

        else:
            return JsonResponse({'status': 'error', 'message': 'Permission denied'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})



def modify_highlight(request, highlight_id):
    if request.method == 'PUT':
        try:
            highlight = Highlight.objects.get(pk=highlight_id)
            data = json.loads(request.body.decode('utf-8'))

            # Update fields as needed
            highlight.start_time = data.get('start_time', highlight.start_time)
            highlight.end_time = data.get('end_time', highlight.end_time)
            highlight.highlighted_text = data.get('highlighted_text', highlight.highlighted_text)
            # ... update other fields as needed ...

            highlight.save()
            return JsonResponse({'status': 'success'}, status=200)
        except Highlight.DoesNotExist:
            return HttpResponse('Highlight not found', status=404)
        except Exception as e:
            return HttpResponse(str(e), status=500)
    else:
        return HttpResponse('Method not allowed', status=405)

@login_required
def get_highlights(request, media_id):
    highlights = Highlight.objects.filter(user=request.user, media__media_id=media_id)
    highlights_data = serializers.serialize('json', highlights)
    return JsonResponse(highlights_data, safe=False)

@login_required
def get_all_highlights(request):
    highlights = Highlight.objects.filter(user_id=request.user.id)
    highlights_data = serializers.serialize('json', highlights)
    return JsonResponse(highlights_data, safe=False)


@login_required
def highlights(request):
    profile = Profile.objects.get(user=request.user)
    media_highlights = {}
    for media in profile.viewed_media.all():
        highlights = Highlight.objects.filter(user=request.user, media=media)
        media_highlights[media] = highlights

    return render(request, 'accounts/highlights.html', {'media_highlights': media_highlights})




@login_required
def list_media_by_status(request, status):
    media_statuses = UserMediaStatus.objects.filter(user=request.user, status=status)
    return render(request, 'media/list_by_status.html', {'media_statuses': media_statuses})
  
# assigning srt variable with the list 
# of dictionaries obtained by the get_transcript() function
#srt = YouTubeTranscriptApi.get_transcript("Ku507_9m2s8", languages=['zh'])
  
# prints the result
#print(srt)



@login_required
def my_media(request):
    status_filter = request.GET.getlist('status')  # Allows multiple status filters

    if status_filter:
        user_media_statuses = UserMediaStatus.objects.filter(
            user=request.user, 
            status__in=status_filter
        )
    else:
        user_media_statuses = UserMediaStatus.objects.filter(
            user=request.user, 
            status__in=['in_progress', 'completed']
        )

    # Annotate each UserMediaStatus object with the count of related highlights
    user_media_statuses = user_media_statuses.annotate(
        highlights_count=Count('media__highlights', filter=Q(media__highlights__user=request.user))
    )

    return render(request, 'accounts/my_media.html', {'user_media_statuses': user_media_statuses})



@login_required
def remove_media_status(request, media_id):
    if request.method == 'POST':
        # Assuming 'media_id' is the primary key of the Media model
        UserMediaStatus.objects.filter(user=request.user, media_id=media_id).delete()
        return JsonResponse({'status': 'success', 'message': 'Media status removed successfully'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)



@login_required
def update_media_status(request, media_id, status=None):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    data = json.loads(request.body)
    status = data.get('status')
    current_time = data.get('current_time', 0)  # Assuming current_time is provided in seconds

    media = get_object_or_404(Media, media_id=media_id)
    profile = get_object_or_404(Profile, user=request.user)
    existing_status = UserMediaStatus.objects.filter(user=request.user, media=media).first()

    words_per_second = media.word_count / media.video_length
    current_words = int(words_per_second * current_time)
    current_minutes = current_time 

    if status == 'completed':
        # Adjust for total video completion
        total_words = media.word_count
        print("fuckkkk")
        total_minutes = round(media.video_length, 2)  # Round to 2 decimal places

        previous_progress = MediaProgress.objects.filter(profile=profile, media=media)
        previously_added_words = sum(progress.words_learned for progress in previous_progress)
        previously_added_minutes = sum(progress.minutes_watched for progress in previous_progress)
        print(previously_added_minutes)


        adjusted_words_to_add = total_words - previously_added_words
        adjusted_minutes_to_add = total_minutes - previously_added_minutes
        print(adjusted_minutes_to_add)
        profile.total_word_count += adjusted_words_to_add
        profile.total_minutes += adjusted_minutes_to_add
        
        profile.save()

        MediaProgress.objects.update_or_create(
            profile=profile, media=media,
            defaults={'time_stopped': media.video_length, 'words_learned': total_words, 'minutes_watched': total_minutes, 'date': timezone.now().date()}
        )

    elif status == 'in_progress':
    # Since we start fresh each time it's set to 'in_progress', directly use the current counts
        profile.total_word_count += current_words
        profile.total_minutes += current_minutes
        profile.save()

        # Update or create the progress entry with current data
        MediaProgress.objects.update_or_create(
            profile=profile, media=media,
            defaults={'time_stopped': current_time, 'words_learned': current_words, 'minutes_watched': current_minutes, 'date': timezone.now().date()}
        )

    elif status == 'completed' or status == 'set-status':
        # When changing status, delete any 'in_progress' records if they exist
        MediaProgress.objects.filter(profile=profile, media=media).delete()
        if status == 'completed':
            # Adjust for total video completion
            profile.total_word_count += media.word_count
            profile.total_minutes += media.video_length
            profile.save()
        elif status == 'set-status':
            # If status is removed and it was previously 'completed', adjust profile totals back
            if existing_status and existing_status.status == 'completed':
                profile.total_word_count -= media.word_count
                profile.total_minutes -= media.video_length
                profile.save()
            UserMediaStatus.objects.filter(user=request.user, media=media).delete()
            return JsonResponse({'status': 'success', 'message': 'Media status removed successfully'})

    if status in ['completed', 'in_progress']:
        UserMediaStatus.objects.update_or_create(
            user=profile.user, media=media,
            defaults={'status': status, 'completion_date': timezone.now().date() if status == 'completed' else None}
        )

    response_data = {'status': 'success', 'message': 'Media status updated successfully'}
    print("Sending response:", response_data)  # Debug print
    return JsonResponse(response_data)



def get_words_read_data(user):
    one_month_ago = datetime.now() - timedelta(days=30)
    words_read_per_day = (
        UserMediaStatus.objects
        .filter(user=user, status='completed', completion_date__gte=one_month_ago)
        .annotate(day=TruncDay('completion_date'))
        .values('day')
        .annotate(total_words=Sum('media__word_count'))
        .order_by('day')
    )
    return words_read_per_day

@login_required
def stats_view(request):
    end_date = timezone.now()
    time_span = request.GET.get('span', 'month')  # Default to last month
    start_date = end_date - timedelta(days=7 if time_span == 'week' else 30)
    
    num_days = (end_date - start_date).days
    all_dates = [(start_date + timedelta(days=x)).date() for x in range(num_days + 1)]
    dates_str = [date.strftime('%Y-%m-%d') for date in all_dates]

    highlights_data = {date: 0 for date in dates_str}
    words_data = {date: 0 for date in dates_str}
    minutes_data = {date: 0 for date in dates_str}

    # Aggregate daily highlights
    daily_highlights = Highlight.objects.filter(
        user=request.user,
        created_at__date__range=[start_date, end_date]
    ).annotate(day=TruncDay('created_at')).values('day').annotate(total=Count('id'))    
    for highlight in daily_highlights:
        day_str = highlight['day'].strftime('%Y-%m-%d')
        highlights_data[day_str] = highlight['total']

    # Aggregate daily words and minutes
    daily_progress = MediaProgress.objects.filter(profile__user=request.user, date__range=[start_date, end_date]).annotate(day=TruncDay('date')).values('day').annotate(total_words=Sum('words_learned'), total_minutes=Sum('minutes_watched'))
    print(daily_progress)
    for progress in daily_progress:
        day_str = progress['day'].strftime('%Y-%m-%d')
        words_data[day_str] = progress['total_words']
        minutes_data[day_str] = progress['total_minutes']

    context = {
        'dates_json': json.dumps(dates_str),
        'highlight_counts_json': json.dumps(list(highlights_data.values())),
        'word_counts_json': json.dumps(list(words_data.values())),
        'minute_counts_json': json.dumps(list(minutes_data.values())),
        'total_highlights_json': json.dumps(Highlight.objects.filter(user=request.user).count()),
        'time_span': time_span,
    }
    print(context)
    return render(request, 'accounts/stats.html', context)


@login_required
def update_progress(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    data = json.loads(request.body)
    media_id = data.get('mediaId')
    additional_words = data.get('additionalWords')
    additional_minutes = data.get('additionalMinutes')
    progress_time = data.get('progressTime')

    media = get_object_or_404(Media, media_id=media_id)
    profile = get_object_or_404(Profile, user=request.user)

    # Retrieve the sum of all previously logged words and minutes for this media
    existing_progress = MediaProgress.objects.filter(profile=profile, media=media)
    total_words_so_far = existing_progress.aggregate(Sum('words_learned'))['words_learned__sum'] or 0
    total_minutes_so_far = existing_progress.aggregate(Sum('minutes_watched'))['minutes_watched__sum'] or 0

    # Calculate the new totals
    new_total_words = total_words_so_far + additional_words
    new_total_minutes = total_minutes_so_far + additional_minutes

    # Update or create the media progress with the new total time
    media_progress, created = MediaProgress.objects.update_or_create(
        profile=profile,
        media=media,
        defaults={'time_stopped': progress_time, 'words_learned': new_total_words, 'minutes_watched': new_total_minutes, 'date': timezone.now().date()}
    )

    # Update the profile with the new totals
    profile.total_word_count = new_total_words
    profile.total_minutes = new_total_minutes
    profile.save()

    return JsonResponse({'status': 'success', 'message': 'Progress updated successfully'})