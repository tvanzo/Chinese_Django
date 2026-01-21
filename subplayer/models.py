# subplayer/models.py (or wherever these live)

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import os


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Channel(models.Model):
    channel_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField()
    profile_pic_url = models.URLField(blank=True, null=True)
    categories = models.ManyToManyField(Category, related_name="channels", blank=True)

    def __str__(self):
        return self.name if self.name else "Unnamed Channel"


class Media(models.Model):
    MEDIA_TYPES = (("video", "Video"), ("audio", "Audio"))
    title = models.CharField(max_length=200)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, blank=True, null=True)
    url = models.URLField()
    sentences = models.JSONField(blank=True, null=True)
    words = models.JSONField(blank=True, null=True)
    media_id = models.CharField(max_length=200)
    subtitle_file = models.FileField(upload_to="subtitles/", blank=True, null=True)
    youtube_video_id = models.CharField(max_length=200, blank=True, null=True)
    thumbnail_url = models.URLField(blank=True, null=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="added_media")
    video_length = models.PositiveIntegerField(blank=True, null=True)
    word_count = models.IntegerField(default=0, blank=True, null=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="media")
    categories = models.ManyToManyField(Category, related_name="media", blank=True)
    profile_image_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    youtube_upload_time = models.DateTimeField()

    def delete(self, *args, **kwargs):
        if self.subtitle_file and os.path.isfile(self.subtitle_file.path):
            os.remove(self.subtitle_file.path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.media_type})"


class UserMediaStatus(models.Model):
    STATUS_CHOICES = (("in_progress", "In Progress"), ("completed", "Completed"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="media_statuses")
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name="user_statuses")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    completion_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "media")


class Article(models.Model):
    """
    Read feature source content.
    - curated articles: created_by is NULL, source_url usually NULL
    - web-saved articles: created_by=user, source_url=page URL
    """

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)

    # legacy columns (keep)
    level = models.CharField(max_length=50, blank=True, null=True, default="")
    description = models.TextField(blank=True, null=True, default="")

    # extracted content
    content = models.TextField(blank=True, null=True, default="")       # plain text snapshot
    content_html = models.TextField(blank=True, null=True, default="")  # optional cleaned html snapshot

    created_at = models.DateTimeField(auto_now_add=True)

    # IMPORTANT: NOT globally unique (so different users can save same URL)
    source_url = models.URLField(blank=True, null=True)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="articles"
    )

    class Meta:
        constraints = [
            # a given user can only have one saved record for the same URL
            models.UniqueConstraint(fields=["created_by", "source_url"], name="uniq_user_source_url"),
        ]
        indexes = [
            models.Index(fields=["created_by", "created_at"]),
            models.Index(fields=["created_by", "source_url"]),
        ]

    def __str__(self):
        return self.title


class Highlight(models.Model):
    SOURCE_CHOICES = (
        ("media", "Media"),
        ("chat", "Chat"),
        ("web", "Web"),
        ("read", "Read"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="highlights")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)

    # Link targets (only one is typically used depending on source)
    media = models.ForeignKey(
        "subplayer.Media",
        on_delete=models.CASCADE,
        related_name="highlights",
        null=True,
        blank=True,
    )

    chat_session = models.ForeignKey(
        "accounts.ChatSession",
        on_delete=models.CASCADE,
        related_name="chat_highlights",
        null=True,
        blank=True,
    )
    chat_message = models.ForeignKey(
        "accounts.ChatMessage",
        on_delete=models.CASCADE,
        related_name="highlights",
        null=True,
        blank=True,
    )

    # New: link highlights directly to an Article (preferred over URL matching)
    article = models.ForeignKey(
        "subplayer.Article",
        on_delete=models.CASCADE,
        related_name="highlights",
        null=True,
        blank=True,
    )

    # ===== MEDIA-SPECIFIC FIELDS =====
    start_time = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    end_time = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    start_index = models.IntegerField(null=True, blank=True)
    end_index = models.IntegerField(null=True, blank=True)
    start_sentence_index = models.IntegerField(null=True, blank=True)
    end_sentence_index = models.IntegerField(null=True, blank=True)
    frame_index = models.IntegerField(null=True, blank=True)

    # ===== SHARED =====
    highlighted_text = models.TextField()
    page_url = models.URLField(blank=True, null=True)
    page_title = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["user", "source", "created_at"]),
            models.Index(fields=["user", "page_url"]),
            models.Index(fields=["user", "article"]),
        ]

    def clean(self):
        # Basic consistency checks (optional but strongly recommended)
        if self.source == "media" and not self.media_id:
            raise ValidationError("media highlight must have media set")

        if self.source == "chat" and not (self.chat_session_id or self.chat_message_id):
            # if you only use chat_message, remove chat_session from this rule
            raise ValidationError("chat highlight must have chat_session or chat_message set")

        if self.source in ("web", "read") and not (self.article_id or self.page_url):
            raise ValidationError("web/read highlight must have article or page_url set")

    def __str__(self):
        if self.source == "media" and self.media:
            return f"[{self.source}] {self.media.title}: {self.highlighted_text[:50]}"
        return f"[{self.source}] {self.highlighted_text[:50]}"
