from django.db import models
from django.conf import settings

from django.contrib.auth.models import User

from django.db import models

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
    thumbnail_url = models.URLField(blank=True, null=True)  # New field for thumbnail URL
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='added_media')
    video_length = models.CharField(max_length=10, blank=True, null=True)  # For storing as "4:13"



    from django.db import models

    def delete(self, *args, **kwargs):
        # If there's a subtitle file associated with this instance, delete the file
        if self.subtitle_file:
            file_path = os.path.join(settings.MEDIA_ROOT, self.subtitle_file.name)
            if os.path.isfile(file_path):
                os.remove(file_path)
        super(Media, self).delete(*args, **kwargs)  # Call the "real" delete() method

class UserMediaStatus(models.Model):
    STATUS_CHOICES = (
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='media_statuses')
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='user_statuses')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('user', 'media')  # Ensure one status per user-media pair



class Highlight(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='highlights')
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='highlights')
    start_time = models.DecimalField(max_digits=6, decimal_places=2)
    end_time = models.DecimalField(max_digits=6, decimal_places=2)
    highlighted_text = models.TextField()
    start_index = models.IntegerField() # index where the highlight starts within the sentence
    end_index = models.IntegerField() # index where the highlight ends within the sentence
    start_sentence_index = models.IntegerField() # sentence where the highlight starts
    end_sentence_index = models.IntegerField() # sentence where the highlight ends
    frame_index = models.IntegerField()

    class Meta:
        unique_together = ['user', 'media', 'start_time', 'end_time', 'highlighted_text']

    def __str__(self):
        return f'Highlight from {self.start_time} to {self.end_time} by {self.user.username}'
