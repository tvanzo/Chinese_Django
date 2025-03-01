# your_project/tasks.py
from celery import shared_task
from .youtube_utils import fetch_videos_from_channel_with_chinese_subtitles

@shared_task
def fetch_videos_task(channel_id):
    """
    Celery task to fetch videos from a YouTube channel.
    """
    return fetch_videos_from_channel_with_chinese_subtitles(channel_id)