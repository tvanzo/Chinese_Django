from django.db import models
from django.contrib.auth.models import User

class Media(models.Model):
    MEDIA_TYPES = (
        ('video', 'Video'),
        ('audio', 'Audio'),
    )
    title = models.CharField(max_length=200)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    url = models.URLField()
    sentences = models.JSONField()  # use django.db.models.JSONField
    words = models.JSONField()      # use django.db.models.JSONField
    media_id=models.CharField(max_length=200)

class Highlight(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='highlights')
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='highlights')
    start_time = models.DecimalField(max_digits=5, decimal_places=2)
    end_time = models.DecimalField(max_digits=5, decimal_places=2)
    highlighted_text = models.TextField()

    class Meta:
        unique_together = ['user', 'media', 'start_time', 'end_time']

    def __str__(self):
        return f'Highlight from {self.start_time} to {self.end_time} by {self.user.username}'

