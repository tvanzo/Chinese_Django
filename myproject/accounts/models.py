from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from subplayer.models import Media

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    finished_media = models.ManyToManyField(Media, related_name='finished_users', blank=True)
    viewed_media = models.ManyToManyField(Media, through='MediaProgress', related_name='viewing_users', blank=True)

class MediaProgress(models.Model):
    media = models.ForeignKey(Media, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)  # Linking to Profile
    time_stopped = models.IntegerField(default=0)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)