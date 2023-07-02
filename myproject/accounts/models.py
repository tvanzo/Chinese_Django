from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    highlighted_words = models.TextField(blank=True)
