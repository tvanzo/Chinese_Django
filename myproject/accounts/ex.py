# myapp/context_processors.py
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

def total_minutes_watched(request):
    if request.user.is_authenticated:
        # Replace with your actual logic to calculate total minutes watched
        total_minutes = User.objects.get(pk=request.user.pk).profile.total_minutes_watched
    else:
        total_minutes = 0
    return {'total_minutes_watched': total_minutes}
