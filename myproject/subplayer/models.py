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
