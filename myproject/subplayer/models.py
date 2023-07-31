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
