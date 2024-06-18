from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from subplayer.models import Media
from django.utils import timezone
# models.py

# models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from subplayer.models import Media
from django.utils import timezone

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    finished_media = models.ManyToManyField(Media, related_name='finished_users', blank=True)
    viewed_media = models.ManyToManyField(Media, through='MediaProgress', related_name='viewing_users', blank=True)
    total_word_count = models.IntegerField(default=0, help_text="Total word count from completed videos.")
    total_minutes = models.IntegerField(default=0, help_text="Total minutes of video completed")
    total_highlights = models.IntegerField(default=0, help_text="Total highlights")
    total_points = models.IntegerField(default=0, help_text="Total points accumulated")

    def calculate_total_points(self):
        total_highlights_points = self.total_highlights // 2
        total_minutes_points = round(self.total_minutes / 60)  # Divide minutes by 60 and round
        total_videos_points = self.finished_media.count()
        total_points = total_highlights_points + total_minutes_points + total_videos_points
        print(
            f"Highlights Points: {total_highlights_points}, Minutes Points: {total_minutes_points}, Videos Points: {total_videos_points}, Total Points: {total_points}")
        return total_points
    def calculate_total_minutes_watched(self):
        # Assuming `MediaProgress` model has a field `minutes_watched`
        total_minutes_watched = MediaProgress.objects.filter(profile=self).aggregate(total_minutes=Sum('minutes_watched'))['total_minutes']
        return total_minutes_watched or 0


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)



class MediaProgress(models.Model):
    media = models.ForeignKey(Media, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)  # Linking to Profile
    time_stopped = models.IntegerField(default=0)
    date = models.DateField(default=timezone.now)  # Track the day of the progress
    words_learned = models.IntegerField(default=0, help_text="Number of words learned during this session.")
    minutes_watched = models.IntegerField(default=0, help_text="Number of minutes watched during this session.")

    class Meta:
        unique_together = ('media', 'profile', 'date')  # Ensuring one entry per media, profile, and date

