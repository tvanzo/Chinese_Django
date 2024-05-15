from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User

class Channel(models.Model):
    channel_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField()
    profile_pic_url = models.URLField(blank=True, null=True)  # Adding this field to store the channel's profile picture URL

    def __str__(self):
        return str(self.name) if self.name else "Unnamed Channel"



    def __str__(self):
        return self.name

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
    category = models.CharField(max_length=255,  default='Unknown')
    profile_image_url = models.URLField(null=True, blank=True)

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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='highlights')
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='highlights')
    start_time = models.DecimalField(max_digits=6, decimal_places=2)
    end_time = models.DecimalField(max_digits=6, decimal_places=2)
    highlighted_text = models.TextField()
    start_index = models.IntegerField()
    end_index = models.IntegerField()
    start_sentence_index = models.IntegerField()
    end_sentence_index = models.IntegerField()
    frame_index = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['user', 'media', 'start_time', 'end_time', 'highlighted_text']

    def __str__(self):
        return f'Highlight from {self.start_time} to {self.end_time} by {self.user.username}'
