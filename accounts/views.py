from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core import serializers
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.timezone import localtime, now
from django.urls import reverse
from django.conf import settings
from django.db.models import Count, Q, Sum, F
from django.db.models.functions import TruncDay
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers import serialize
from datetime import datetime, timedelta, date
import json
import logging
from django.contrib.auth import authenticate, login
from subplayer.forms import CustomUserCreationForm
from accounts.models import Profile, MediaProgress
from subplayer.models import Media, Highlight, UserMediaStatus
from subplayer.views import format_duration  # Import the function from subplayer.views

logger = logging.getLogger(__name__)

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib import messages

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from django.contrib import messages

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm

from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomUserCreationForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(request)  # Save the user and pass the request
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(email=user.email, password=raw_password)  # Use email for authentication
            if user is not None:
                login(request, user)
                messages.success(request, f'Account created for {user.email}!')
                return redirect('/')
            else:
                messages.error(request, 'Authentication failed. Please try again.')
        else:
            messages.error(request, 'Invalid form submission. Please correct the errors and try again.')
            print(form.errors)  # Print form errors to debug
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})
@login_required
def media_list(request):
    media_data = serializers.serialize('json', Media.objects.all())
    finished_media_count = request.user.profile.finished_media.count()  # Get the count of finished media for the user

    context = {
        'media': media_data,
        'finished_media_count': finished_media_count,  # Add this to the context
    }

    return render(request, 'media/list.html', context)

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
            print(media_id)
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
    print("update_media_progress called")  # Debugging statement

    if request.method == 'POST':
        data = json.loads(request.body)
        media_id = data.get('mediaId')
        progress = data.get('progress')

        try:
            media = get_object_or_404(Media, media_id=media_id)
            profile = request.user.profile

            # Get today's date
            today = localtime(now()).date()

            # Try to get the MediaProgress for today, or none if it doesn't exist
            media_progress, created = MediaProgress.objects.get_or_create(
                media=media,
                profile=profile,
                date=today,
                defaults={'time_stopped': progress}  # Set defaults for a new record
            )

            if not created:
                # If the record was not created, it means it already exists, and we just need to update it
                media_progress.time_stopped = progress
                media_progress.save()

            print("Progress updated to:", progress)  # Debugging statement

            return JsonResponse({'status': 'ok'})

        except Media.DoesNotExist:
            return JsonResponse({'error': 'Media not found'}, status=404)
        except Exception as e:
            print(str(e))  # Print the error for debugging
            return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def create_highlight(request):
    try:
        data = json.loads(request.body)
        media_obj = Media.objects.get(media_id=data['media'])

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

        # Return the highlight details and updated points as JSON
        return JsonResponse({
            'id': new_highlight.id,
            'highlighted_text': new_highlight.highlighted_text,
            'media_id': new_highlight.media.media_id,
            'total_points': user_profile.total_points  # Return updated total points
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
    user = request.user
    profile = Profile.objects.get(user=user)
    all_highlights = Highlight.objects.filter(user=user).order_by('created_at')

    print(f"Total highlights: {all_highlights.count()}")  # Debugging line to check the total number of highlights

    return render(request, 'accounts/highlights.html', {'highlights': all_highlights})

@login_required
def download_highlights(request):
    user = request.user
    highlights = Highlight.objects.filter(user=user).order_by('created_at')

    # Create the text content
    highlights_text = "\n".join([highlight.highlighted_text for highlight in highlights])

    # Create the HttpResponse object with the appropriate headers for a text file
    response = HttpResponse(highlights_text, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=highlights.txt'

    return response

@login_required
def download_subtitles(request):
    user = request.user
    profile = Profile.objects.get(user=user)
    media_statuses = UserMediaStatus.objects.filter(user=user, status__in=['in_progress', 'completed'])

    combined_text = ""
    for media_status in media_statuses:
        media = media_status.media
        subtitle_path = media.subtitle_file.path
        if os.path.exists(subtitle_path):
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                subtitles = json.load(f)
                transcript = "\n".join([word['word'] for word in subtitles.get('words', [])])
                combined_text += f"{media.title}:\n{transcript}\n\n"

    response = HttpResponse(combined_text, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="combined_subtitles.txt"'
    return response

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
    current_time = data.get('current_time', 0)  # Assuming current_time is provided in seconds

    media = get_object_or_404(Media, media_id=media_id)
    profile = get_object_or_404(Profile, user=request.user)
    existing_status = UserMediaStatus.objects.filter(user=request.user, media=media).first()

    words_per_second = media.word_count / media.video_length
    current_words = int(words_per_second * current_time)
    current_minutes = current_time / 60  # Convert seconds to minutes

    today = timezone.now().date()

    if status == 'completed':
        # Adjust for total video completion
        total_words = media.word_count
        total_minutes = media.video_length / 60  # Convert to minutes

        previous_progress = MediaProgress.objects.filter(profile=profile, media=media).last()
        all_previous_progress = MediaProgress.objects.filter(profile=profile, media=media)

        previously_added_words = sum(progress.words_learned for progress in all_previous_progress)
        previously_added_minutes = previous_progress.minutes_watched if previous_progress else 0

        adjusted_words_to_add = total_words - previously_added_words
        adjusted_minutes_to_add = total_minutes - previously_added_minutes

        profile.total_word_count += adjusted_words_to_add
        profile.total_minutes += adjusted_minutes_to_add

        profile.save()

        # Check if there is an existing MediaProgress for today
        today_progress = MediaProgress.objects.filter(profile=profile, media=media, date=today).first()
        if today_progress:
            # Update the existing progress for today
            today_progress.words_learned += adjusted_words_to_add
            today_progress.minutes_watched += adjusted_minutes_to_add  # Convert minutes back to seconds for storage
            today_progress.save()
        else:
            # Create a new progress entry for today
            last_progress = MediaProgress.objects.filter(profile=profile, media=media).order_by('-date').first()
            if last_progress:
                # Accumulate values from the last entry
                MediaProgress.objects.create(
                    profile=profile,
                    media=media,
                    date=today,
                    time_stopped=media.video_length,
                    words_learned=total_words,
                    minutes_watched=total_minutes  # Convert to seconds for storage
                )
            else:
                MediaProgress.objects.create(
                    profile=profile,
                    media=media,
                    date=today,
                    time_stopped=media.video_length,
                    words_learned=total_words,
                    minutes_watched=total_minutes  # Convert to seconds for storage
                )

        # Add media to added_media list
        request.user.added_media.add(media)

    elif status == 'in_progress':
        profile.total_word_count += current_words
        profile.total_minutes += current_minutes
        profile.save()

        # Update or create the progress entry with current data
        MediaProgress.objects.update_or_create(
            profile=profile, media=media,
            date=today,
            defaults={'time_stopped': current_time, 'words_learned': current_words, 'minutes_watched': current_minutes}  # Convert minutes back to seconds for storage
        )

        # Add media to added_media list
        request.user.added_media.add(media)

    elif status == 'remove':
        if existing_status and existing_status.status == 'completed':
            profile.total_word_count -= media.word_count
            profile.total_minutes -= media.video_length / 60  # Convert to minutes
            profile.save()
        UserMediaStatus.objects.filter(user=request.user, media=media).delete()
        profile.total_points = profile.calculate_total_points()
        profile.save()

        # Remove media from added_media list
        request.user.added_media.remove(media)
        return JsonResponse({'status': 'success', 'message': 'Media status removed successfully', 'total_points': profile.total_points})

    elif existing_status and existing_status.status == 'completed' and status != 'completed':
        # If the existing status is 'completed' and the new status is not 'completed', adjust totals
        UserMediaStatus.objects.update_or_create(
            user=request.user,
            media=media,
            defaults={'status': status, 'completion_date': None}
        )
        profile.total_word_count -= media.word_count
        profile.total_minutes -= media.video_length / 60  # Convert to minutes
        profile.save()
        profile.total_points = profile.calculate_total_points()
        profile.save()

        # Add media to added_media list
        request.user.added_media.add(media)
        return JsonResponse({'status': 'success', 'message': 'Media status changed from completed', 'total_points': profile.total_points})

    if status in ['completed', 'in_progress']:
        UserMediaStatus.objects.update_or_create(
            user=profile.user, media=media,
            defaults={'status': status, 'completion_date': timezone.now().date() if status == 'completed' else None}
        )

    profile.total_points = profile.calculate_total_points()
    profile.save()

    response_data = {'status': 'success', 'message': 'Media status updated successfully', 'total_points': profile.total_points}
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

import json
from datetime import timedelta
from django.utils.timezone import now
from django.shortcuts import render
from django.db.models import Count, Sum
from django.db.models.functions import TruncDay
from django.contrib.auth.decorators import login_required

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncMonth
from itertools import accumulate
import json

from django.shortcuts import render
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Count, F, ExpressionWrapper, fields
from django.db.models.functions import TruncDay
from django.contrib.auth.decorators import login_required
import json

from django.shortcuts import render
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Count, Max, Subquery, OuterRef, F, ExpressionWrapper, fields
from django.db.models.functions import TruncDay
from django.contrib.auth.decorators import login_required
import json
from django.conf.urls.static import static
import os



@login_required
def stats_view(request):
    user = request.user
    profile = user.profile
    end_date = date.today()
    registration_date = user.date_joined.date()
    total_days_registered = (end_date - registration_date).days

    # Determine the interval for "all time"
    if total_days_registered <= 10:
        interval_days = 1
    else:
        interval_days = total_days_registered // 10

    data = {
        'week': timedelta(days=7),
        'month': timedelta(days=30),
        'all_time': timedelta(days=total_days_registered)
    }

    results = {}
    totals = {}
    media_info = []

    highlight_dates = Highlight.objects.filter(user=user).dates('created_at', 'day')
    media_dates = MediaProgress.objects.filter(profile=profile).dates('date', 'day')
    active_dates = sorted(set(highlight_dates) | set(media_dates))

    streak = 0
    today = date.today()
    for i in range(len(active_dates) - 1, -1, -1):
        if active_dates[i] == today:
            streak += 1
            today -= timedelta(days=1)
        else:
            break

    for key, delta in data.items():
        if key == 'all_time':
            start_date = registration_date
        else:
            start_date = end_date - delta

        num_days = (end_date - start_date).days
        interval_count = num_days // interval_days if key == 'all_time' else num_days
        all_dates = [start_date + timedelta(days=i * interval_days) for i in range(interval_count + 1)]
        dates_str = [d.strftime('%Y-%m-%d') for d in all_dates]

        highlights_data = {date: 0 for date in dates_str}
        minutes_data = {date: 0 for date in dates_str}
        words_data = {date: 0 for date in dates_str}
        points_data = {date: 0 for date in dates_str}  # Adding points data

        daily_highlights = Highlight.objects.filter(
            user=user,
            created_at__date__range=[start_date, end_date]
        ).annotate(day=TruncDay('created_at')).values('day').annotate(total=Count('id'))

        for highlight in daily_highlights:
            day_str = highlight['day'].strftime('%Y-%m-%d')
            highlights_data[day_str] = highlight['total']

        daily_minutes = MediaProgress.objects.filter(
            profile=profile,
            date__range=[start_date, end_date]
        ).annotate(day=TruncDay('date')).values('day').annotate(total_minutes=Sum('minutes_watched'), total_words=Sum('words_learned'))

        for minute in daily_minutes:
            day_str = minute['day'].strftime('%Y-%m-%d')
            minutes_data[day_str] = round(minute['total_minutes'] / 60, 2)
            words_data[day_str] = minute['total_words'] if minute['total_words'] else 0

            # Assuming points are derived from minutes and words. Adjust the calculation as needed.
            points_data[day_str] = round(minute['total_minutes']) + minute['total_words'] if minute['total_words'] else 0

        results[key] = {
            'dates': dates_str,
            'highlights': list(highlights_data.values()),
            'minutes': list(minutes_data.values()),
            'words': list(words_data.values()),
            'points': list(points_data.values())  # Adding points to results
        }

        totals[key] = {
            'total_highlights': sum(highlights_data.values()),
            'total_minutes': round(sum(minutes_data.values())),  # Round to nearest whole number
            'total_words': sum(words_data.values()),
            'total_videos': MediaProgress.objects.filter(profile=profile, date__range=[start_date, end_date]).values('media_id').distinct().count(),
            'total_points': sum(points_data.values())  # Adding total points to totals
        }

    media_statuses = UserMediaStatus.objects.filter(user=user, status__in=['in_progress', 'completed']).select_related('media__channel').annotate(
        total_highlights=Count('media__highlights', filter=Q(media__highlights__user=user)),
        latest_time_stopped=Subquery(
            MediaProgress.objects.filter(profile=profile, media=OuterRef('media')).order_by('-date').values('time_stopped')[:1]
        )
    )

    for status in media_statuses:
        video_length = status.media.video_length
        latest_time_stopped = status.latest_time_stopped or 0
        if status.status == 'completed':
            progress_percent = 100
        else:
            progress_percent = round((latest_time_stopped / video_length * 100), 0) if video_length > 0 else 0

        media_info.append({
            'media_id': status.media.media_id,
            'title': status.media.title,
            'total_highlights': status.total_highlights,
            'length': f"{video_length // 60}:{video_length % 60:02d}",
            'status': status.status,
            'progress_percent': progress_percent,
            'profile_image_url': status.media.channel.profile_pic_url  # Access the profile_pic_url of the Channel
        })

    context = {
        'highlight_data_json': json.dumps(results),
        'totals_json': json.dumps(totals),
        'media_info': media_info,
        'streak': streak,
        'default_image_url': static('accounts/img/small-logos/logo-xd.svg'),
        'total_minutes': totals['all_time']['total_minutes'],  # Adding total_minutes to context
    }

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
    today = localtime(now()).date()  # Get today's date in the local timezone

    # Check if there is an existing MediaProgress for today
    today_progress = MediaProgress.objects.filter(profile=profile, media=media, date=today).first()
    if today_progress:
        # Update the existing progress for today
        today_progress.time_stopped = progress_time
        today_progress.words_learned += additional_words
        today_progress.minutes_watched += additional_minutes
        today_progress.save()
    else:
        # Create a new progress entry for today
        last_progress = MediaProgress.objects.filter(profile=profile, media=media).order_by('-date').first()
        if last_progress:
            # Accumulate values from the last entry
            MediaProgress.objects.create(
                profile=profile,
                media=media,
                date=today,
                time_stopped=progress_time,
                words_learned=additional_words,
                minutes_watched=additional_minutes
            )
        else:
            MediaProgress.objects.create(
                profile=profile,
                media=media,
                date=today,
                time_stopped=progress_time,
                words_learned=additional_words,
                minutes_watched=additional_minutes
            )

    profile.total_word_count += additional_words
    profile.total_minutes += additional_minutes
    profile.save()

    profile.total_points = profile.calculate_total_points()
    profile.save()

    return JsonResponse({'status': 'success', 'message': 'Progress updated successfully', 'total_points': profile.total_points})


def highlights_detail(request, media_id):
    media = get_object_or_404(Media, media_id=media_id, media_type='video')
    highlights = Highlight.objects.filter(media=media, user=request.user)

    # Assuming UserMediaStatus has a 'status' field that contains the media status
    user_media_status = UserMediaStatus.objects.filter(user=request.user, media=media).first()
    media_status = user_media_status.status if user_media_status else 'none'

    # Serialize the media object to include in the JavaScript
    media_serialized = serialize('json', [media])
    media_dict = json.loads(media_serialized)[0]['fields']
    media_dict['media_id'] = media.media_id
    media_dict['media_type'] = media.media_type
    media_dict['model'] = str(media._meta)
    media_dict['url'] = media.subtitle_file.url
    # Add video_length and word_count directly to media_dict
    media_dict['video_length'] = media.video_length
    media_dict['word_count'] = media.word_count

    media_json = json.dumps(media_dict)

    context = {
        'media': media,
        'media_json': media_json,
        'highlights': highlights,
        'has_status': user_media_status is not None,
        'media_status': media_status,
        'hide_nav': True,
    }
    return render(request, 'accounts/highlights_detail.html', context)



@login_required
def user_videos(request):
    user = request.user

    # Fetch the media associated with the logged-in user's added_media
    user_media = user.added_media.all()

    # Attach the formatted video length and user highlights count directly to each media object
    for media in user_media:
        media.formatted_video_length = format_duration(media.video_length)
        media.user_highlights_count = media.highlights.filter(user=user).count()

    context = {
        'media': user_media,
    }

    return render(request, 'accounts/user_videos.html', context)


@login_required
def add_to_log(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    request.user.added_media.add(media)
    return JsonResponse({'success': True})

@login_required
def remove_from_log(request, media_id):
    media = get_object_or_404(Media, id=media_id)
    request.user.added_media.remove(media)
    return JsonResponse({'success': True})

def join(request):
    return render(request, 'accounts/join.html')

# In your views.py file

from django.contrib.auth import logout
from django.contrib import messages

def custom_logout_view(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return redirect('login')  # Redirect to the login page after logging ou


def home_redirect_view(request):
    if request.user.is_authenticated:
        return redirect('stats_view')  # or any other name you have for the dashboard view
    else:
        return redirect('intro')  # or any other name you have for the intro view