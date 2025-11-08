from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from subplayer.models import Media, Channel  # Import Channel
from django.utils import timezone
from django.db.models import Sum
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    finished_media = models.ManyToManyField(Media, related_name='finished_users', blank=True)
    viewed_media = models.ManyToManyField(Media, through='MediaProgress', related_name='viewing_users', blank=True)
    total_word_count = models.IntegerField(default=0, help_text="Total word count from completed videos.")
    total_minutes = models.IntegerField(default=0, help_text="Total minutes of video completed")
    total_highlights = models.IntegerField(default=0, help_text="Total highlights")
    total_points = models.IntegerField(default=0, help_text="Total points accumulated")
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=50, blank=True, null=True)
    subscribed_channels = models.ManyToManyField(Channel, related_name='subscribers', blank=True)  # New field

    def calculate_total_points(self):
        total_highlights_points = self.total_highlights // 2
        total_minutes_points = round(self.total_minutes / 60)
        total_videos_points = self.finished_media.count()
        total_points = total_highlights_points + total_minutes_points + total_videos_points
        return total_points

    def calculate_total_minutes_watched(self):
        total_minutes_watched = MediaProgress.objects.filter(profile=self).aggregate(total_minutes=Sum('minutes_watched'))['total_minutes']
        return total_minutes_watched or 0

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

class MediaProgress(models.Model):
    media = models.ForeignKey(Media, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    time_stopped = models.IntegerField(default=0)
    date = models.DateField(default=timezone.now)
    words_learned = models.IntegerField(default=0, help_text="Number of words learned during this session.")
    minutes_watched = models.IntegerField(default=0, help_text="Number of minutes watched during this session.")

    class Meta:
        unique_together = ('media', 'profile', 'date')

class Subscription(models.Model):
    TIER_CHOICES = [
        ('FREE', 'Free'),
        ('BASIC', 'Basic'),
        ('PREMIUM', 'Premium'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='FREE')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True, help_text="Set for non-recurring subscriptions.")
    is_active = models.BooleanField(default=True)
    stripe_subscription_id = models.CharField(max_length=50, blank=True, null=True)
    next_billing_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.tier}"

    def is_valid(self):
        return self.is_active and (self.end_date is None or self.end_date > timezone.now())

@receiver(post_save, sender=User)
def create_default_subscription(sender, instance, created, **kwargs):
    if created:
        Subscription.objects.create(user=instance, tier='FREE')

class ChatSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )
    title = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or f"Chat #{self.pk}"


class ChatMessage(models.Model):
    ROLE_CHOICES = (
        ("user", "User"),
        ("assistant", "Assistant"),
    )

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:40]}"