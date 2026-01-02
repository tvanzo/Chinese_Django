from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Sum
from django.conf import settings

import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY


# =========================
# Profile & Progress
# =========================

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    finished_media = models.ManyToManyField(
        "subplayer.Media",
        related_name="finished_users",
        blank=True,
    )

    viewed_media = models.ManyToManyField(
        "subplayer.Media",
        through="MediaProgress",
        related_name="viewing_users",
        blank=True,
    )

    total_word_count = models.IntegerField(default=0)
    total_minutes = models.IntegerField(default=0)
    total_highlights = models.IntegerField(default=0)
    total_points = models.IntegerField(default=0)

    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=50, blank=True, null=True)

    subscribed_channels = models.ManyToManyField(
        "subplayer.Channel",
        related_name="subscribers",
        blank=True,
    )

    def calculate_total_points(self):
        highlights_points = self.total_highlights // 2
        minutes_points = round(self.total_minutes / 60)
        videos_points = self.finished_media.count()
        return highlights_points + minutes_points + videos_points

    def calculate_total_minutes_watched(self):
        return (
            MediaProgress.objects
            .filter(profile=self)
            .aggregate(total=Sum("minutes_watched"))["total"]
            or 0
        )

    def __str__(self):
        return f"Profile: {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class MediaProgress(models.Model):
    media = models.ForeignKey(
        "subplayer.Media",
        on_delete=models.CASCADE,
    )
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    time_stopped = models.IntegerField(default=0)
    date = models.DateField(default=timezone.now)
    words_learned = models.IntegerField(default=0)
    minutes_watched = models.IntegerField(default=0)

    class Meta:
        unique_together = ("media", "profile", "date")


# =========================
# Subscription
# =========================

class Subscription(models.Model):
    TIER_CHOICES = [
        ("FREE", "Free"),
        ("BASIC", "Basic"),
        ("PREMIUM", "Premium"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default="FREE")
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    stripe_subscription_id = models.CharField(max_length=50, blank=True, null=True)
    next_billing_date = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        return self.is_active and (
            self.end_date is None or self.end_date > timezone.now()
        )

    def __str__(self):
        return f"{self.user.username} - {self.tier}"


@receiver(post_save, sender=User)
def create_default_subscription(sender, instance, created, **kwargs):
    if created:
        Subscription.objects.create(user=instance, tier="FREE")


# =========================
# Chat Models
# =========================

class ChatCategory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_categories",
    )
    name = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name


class ChatSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )
    title = models.CharField(max_length=255, blank=True)

    # ✅ NEW: one category per chat (optional)
    category = models.ForeignKey(
        ChatCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
    )

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
