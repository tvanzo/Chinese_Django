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
