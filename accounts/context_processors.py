# accounts/context_processors.py
from accounts.models import Profile

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
    if request.user.is_authenticated:
        try:
            profile = Profile.objects.get(user=request.user)
            total_points = profile.calculate_total_points()  # Calculate total points using method
            print(f"Total points calculated: {total_points}")  # Debug print
        except Profile.DoesNotExist:
            total_points = 0
    else:
        total_points = 0
    print(f"Total points in context: {total_points}")  # Debug print
    return {'total_points': total_points}