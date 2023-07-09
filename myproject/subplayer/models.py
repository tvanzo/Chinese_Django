from django.db import models
from django.contrib.postgres.fields import JSONField  # If you are using PostgreSQL

class Media(models.Model):
    VIDEO = 'video'
    PODCAST = 'podcast'

    MEDIA_TYPE_CHOICES = [
        (VIDEO, 'Video'),
        (PODCAST, 'Podcast'),
    ]

    title = models.CharField(max_length=255)
    link = models.URLField(max_length=500)  # Link to YouTube or cloud-hosted audio file
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    words = JSONField()  # JSON data for words
    sentences = JSONField()  # JSON data for sentences
