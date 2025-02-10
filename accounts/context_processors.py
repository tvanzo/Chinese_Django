# accounts/context_processors.py
from accounts.models import Profile
from subplayer.models import Highlight

def total_minutes_watched(request):
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
            total_minutes = round(profile.total_minutes / 60)  # Convert seconds to minutes and round
        except Profile.DoesNotExist:
            total_minutes = 0
    else:
        total_minutes = 0
    return {'total_minutes_watched': total_minutes}

def total_points(request):
    total_points = 0
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
            total_minutes = round(profile.total_minutes / 60)  # Convert seconds to minutes and round
            total_highlights = Highlight.objects.filter(user=request.user).count()
            total_points = total_minutes + total_highlights
            print(f"Total points calculated: {total_points}")  # Debug print
        except Profile.DoesNotExist:
            print("Profile does not exist for user.")
    else:
        print("User not authenticated.")
    print(f"Total points in context: {total_points}")  # Debug print
    return {'total_points': total_points}