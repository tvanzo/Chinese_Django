import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from subplayer.models import Media
from accounts.models import Profile, MediaProgress

# Get the latest user
latest_user = User.objects.latest('date_joined')

# Get the profile of the latest user
profile = Profile.objects.get(user=latest_user)

# Get all media
media_list = Media.objects.all()

# Define the range for the past 7 days
end_date = timezone.now().date()
start_date = end_date - timedelta(days=6)

# Generate fake data for the past 7 days
for single_date in (start_date + timedelta(n) for n in range(7)):
    for media in media_list:
        minutes_watched = random.randint(1, 10)  # Random minutes watched between 1 and 10
        words_learned = random.randint(10, 50)  # Random words learned between 10 and 50
        time_stopped = random.randint(1, 120)  # Random time stopped between 1 and 120 seconds

        # Check if MediaProgress entry exists
        media_progress, created = MediaProgress.objects.get_or_create(
            media=media,
            profile=profile,
            date=single_date,
            defaults={'time_stopped': time_stopped, 'words_learned': words_learned, 'minutes_watched': minutes_watched}
        )

        # If the entry already exists, update it
        if not created:
            media_progress.time_stopped = time_stopped
            media_progress.words_learned = words_learned
            media_progress.minutes_watched = minutes_watched
            media_progress.save()

print("Fake media progress data created successfully.")
