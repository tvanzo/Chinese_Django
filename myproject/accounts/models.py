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


class MediaProgress(models.Model):
    media = models.ForeignKey(Media, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)  # Linking to Profile
    time_stopped = models.IntegerField(default=0)
    date = models.DateField(default=timezone.now)  # Track the day of the progress
    words_learned = models.IntegerField(default=0, help_text="Number of words learned during this session.")
    minutes_watched = models.IntegerField(default=0, help_text="Number of minutes watched during this session.")

    class Meta:
        unique_together = ('media', 'profile', 'date')  # Ensuring one entry per media, profile, and date

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)