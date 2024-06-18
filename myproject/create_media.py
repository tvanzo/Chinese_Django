import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django.setup()

from django.contrib.auth.models import User
from subplayer.models import Media

def create_media_objects():
    # Create audio media objects
    audio_media_data = [
        {
            'media_id': '1',
            'title': 'Audio Media 1',
            'media_type': 'audio',
            'url': 'https://example.com/audio1.mp3',
            'sentences': [],
            'words': [],
        },
        {
            'media_id': '2',
            'title': 'Audio Media 2',
            'media_type': 'audio',
            'url': 'https://example.com/audio2.mp3',
            'sentences': [],
            'words': [],
        },
        {
            'media_id': '3',
            'title': 'Audio Media 3',
            'media_type': 'audio',
            'url': 'https://example.com/audio3.mp3',
            'sentences': [],
            'words': [],
        },
    ]

    # Create video media objects
    video_media_data = [
        {
            'media_id': '4',
            'title': 'Video Media 1',
            'media_type': 'video',
            'url': 'https://example.com/video1.mp4',
            'sentences': [],
            'words': [],
        },
        {
            'media_id': '5',
            'title': 'Video Media 2',
            'media_type': 'video',
            'url': 'https://example.com/video2.mp4',
            'sentences': [],
            'words': [],
        },
    ]

    # Create media objects
    for media_data in audio_media_data + video_media_data:
        media = Media(**media_data)
        media.save()

create_media_objects()
