from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
import os

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Channel(models.Model):
    channel_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField()
    profile_pic_url = models.URLField(blank=True, null=True)  # Adding this field to store the channel's profile picture URL
    categories = models.ManyToManyField(Category, related_name='channels', blank=True)

    def __str__(self):
        return self.name if self.name else "Unnamed Channel"


class Media(models.Model):
    MEDIA_TYPES = (
        ('video', 'Video'),
        ('audio', 'Audio'),
    )
    title = models.CharField(max_length=200)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES, blank=True, null=True)
    url = models.URLField()
    sentences = models.JSONField(blank=True, null=True)
    words = models.JSONField(blank=True, null=True)
    media_id = models.CharField(max_length=200)
    subtitle_file = models.FileField(upload_to='subtitles/', blank=True, null=True)
    youtube_video_id = models.CharField(max_length=200, blank=True, null=True)
    thumbnail_url = models.URLField(blank=True, null=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='added_media')
    video_length = models.PositiveIntegerField(blank=True, null=True, help_text="Length of the video in seconds.")
    word_count = models.IntegerField(default=0, blank=True, null=True, help_text="Estimated word count from video subtitles.")
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='media')
    categories = models.ManyToManyField(Category, related_name='media', blank=True)
    profile_image_url = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Add this field
    youtube_upload_time = models.DateTimeField()

    def delete(self, *args, **kwargs):
        if self.subtitle_file:
            file_path = os.path.join(settings.MEDIA_ROOT, self.subtitle_file.name)
            if os.path.isfile(file_path):
                os.remove(file_path)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.media_type})"


class UserMediaStatus(models.Model):
    STATUS_CHOICES = (
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_statuses')
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='user_statuses')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    completion_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'media')


class Highlight(models.Model):
    SOURCE_CHOICES = (
        ('media', 'Media'),   # subtitles / video page
        ('chat', 'Chat'),     # chat page
        ('web', 'Web'),       # from Chrome extension / external pages
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='highlights')
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='media')

    media = models.ForeignKey(
        Media,
        on_delete=models.CASCADE,
        related_name='highlights',
        null=True,
        blank=True
    )

    start_time = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    end_time = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    highlighted_text = models.TextField()

    start_index = models.IntegerField(null=True, blank=True)
    end_index = models.IntegerField(null=True, blank=True)
    start_sentence_index = models.IntegerField(null=True, blank=True)
    end_sentence_index = models.IntegerField(null=True, blank=True)
    frame_index = models.IntegerField(null=True, blank=True)

    # NEW: where the highlight came from (for web highlights)
    page_url = models.URLField(blank=True, null=True)
    page_title = models.CharField(max_length=500, blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [
            'user',
            'source',
            'media',
            'start_time',
            'end_time',
            'highlighted_text',
        ]

    def __str__(self):
        if self.source == 'media' and self.media:
            return f'[{self.source}] {self.media.title}: {self.highlighted_text[:50]}'
        return f'[{self.source}] {self.highlighted_text[:50]}'

# subplayer/models.py
class Article(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    level = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    content = models.TextField(blank=True)  # ← this will store the cleaned text
    created_at = models.DateTimeField(auto_now_add=True)

    source_url = models.URLField(blank=True, null=True, unique=True)  # ← add unique!
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="articles"
    )


class ArticleHighlight(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="article_highlights"
    )

    # NEW: link directly to Article (can be null for old rows)
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="highlights",
        null=True,
        blank=True,
    )

    # keep these so the extension can send raw info, and they still work
    page_url = models.URLField(max_length=500)
    page_title = models.CharField(max_length=255, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        label = self.page_title or self.page_url
        return f"{self.user} – {label} – {self.text[:40]}"