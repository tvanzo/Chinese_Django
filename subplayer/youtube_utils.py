import os
import re
import json
import logging
import requests
from datetime import datetime
from django.conf import settings
from isodate import parse_duration
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import DefaultCredentialsError
from django.utils.timezone import make_aware

logger = logging.getLogger(__name__)

# Use a single API key (like your original setup)
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY environment variable is not set")

# Initialize YouTube API client
try:
    youtube = build('youtube', 'v3', developerKey=GOOGLE_API_KEY)
except DefaultCredentialsError as e:
    logger.error("Failed to authenticate with Google API: %s", e)
    raise RuntimeError("Failed to authenticate with Google API") from e

### Fetch Subtitles from YouTube API ###
def fetch_subtitles(video_id, language="zh"):
    """Fetch subtitles using YouTube Data API"""
    try:
        url = f"https://www.googleapis.com/youtube/v3/captions?part=snippet&videoId={video_id}&key={GOOGLE_API_KEY}"
        response = requests.get(url).json()

        if "items" not in response:
            logger.warning(f"No subtitles found for video {video_id}")
            return None

        # Find subtitles in the preferred language
        for caption in response["items"]:
            if caption["snippet"]["language"] in [language, "zh-CN", "zh-Hans", "zh-Hant", "zh-TW"]:
                caption_id = caption["id"]
                return download_caption(caption_id)

        logger.info(f"No {language} subtitles available for {video_id}")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed while fetching subtitles: {e}")
        return None

def download_caption(caption_id):
    """Download the subtitle file"""
    try:
        url = f"https://www.googleapis.com/youtube/v3/captions/{caption_id}?tfmt=srv3&key={GOOGLE_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.text  # YouTube provides subtitles in XML format
        else:
            logger.error(f"Failed to download subtitles for caption ID: {caption_id}")
            return None
    except Exception as e:
        logger.error(f"Error downloading captions: {e}")
        return None

### Fetch Video Details ###
def fetch_video_details(url):
    """Fetch video metadata using YouTube API"""
    logger.debug(f"Fetching video details for URL: {url}")

    # Extract video ID from URL
    video_id_match = re.search(r'(?<=v=)[^&#]+', url) or re.search(r'(?<=be/)[^&#]+', url)
    video_id = video_id_match.group(0) if video_id_match else None

    if not video_id:
        logger.error(f"Invalid YouTube URL provided: {url}")
        return {'status': 'invalid', 'message': "Invalid YouTube URL."}

    try:
        video_response = youtube.videos().list(
            id=video_id, part='snippet,contentDetails,status'
        ).execute()

        if not video_response.get('items'):
            return {'status': 'invalid', 'message': "YouTube video does not exist."}

        video_item = video_response['items'][0]

        # Check if video is embeddable
        if not video_item['status'].get('embeddable', True):
            return {'status': 'invalid', 'message': "Video is not embeddable."}

        # Extract video details
        video_title = video_item['snippet']['title']
        thumbnail_url = video_item['snippet']['thumbnails']['high']['url']
        channel_id = video_item['snippet']['channelId']
        category_id = video_item['snippet']['categoryId']
        duration = parse_duration(video_item['contentDetails']['duration'])
        video_length_seconds = int(duration.total_seconds())

        # Get upload time
        published_at = video_item['snippet']['publishedAt']
        upload_time = make_aware(datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ"))

        # Fetch subtitles
        subtitles = fetch_subtitles(video_id)
        subtitles_path = None
        word_count = 0
        if subtitles:
            subtitles_path, word_count = process_and_save_subtitles(subtitles, video_id)

        return {
            'status': 'valid',
            'title': video_title,
            'video_id': video_id,
            'thumbnail_url': thumbnail_url,
            'video_length': video_length_seconds,
            'subtitles_file_path': subtitles_path,
            'word_count': word_count,
            'channel_id': channel_id,
            'category_id': category_id,
            'upload_time': upload_time
        }

    except HttpError as e:
        logger.error(f"HTTP Error: {e}")
        return {'status': 'invalid', 'message': f"An API error occurred: {e}"}

### Save Subtitles ###
def process_and_save_subtitles(subtitles, video_id):
    """Save subtitles to file"""
    if not subtitles:
        return None, 0

    word_count = len(subtitles.split())
    subtitles_data = {
        'transcript': subtitles,
        'word_count': word_count
    }

    subtitles_dir = os.path.join(settings.MEDIA_ROOT, 'subtitles')
    os.makedirs(subtitles_dir, exist_ok=True)
    file_path = os.path.join(subtitles_dir, f"{video_id}_subtitles.json")

    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(subtitles_data, file, ensure_ascii=False, indent=4)
        return os.path.relpath(file_path, start=settings.MEDIA_ROOT), word_count
    except Exception as e:
        logger.error(f"Failed to save subtitles: {e}")
        return None, 0

### Fetch Latest Videos from a Channel ###
def fetch_videos_from_channel(channel_id):
    """Fetch latest videos from a YouTube channel"""
    videos = []
    try:
        response = youtube.search().list(
            channelId=channel_id, part='id,snippet', maxResults=5, order='date', type='video'
        ).execute()

        if 'items' not in response:
            logger.warning("No videos found.")
            return []

        for item in response.get('items', []):
            video_id = item['id']['videoId']
            details = fetch_video_details(f"https://www.youtube.com/watch?v={video_id}")

            if details['status'] == 'valid' and details.get('subtitles_file_path'):
                videos.append(details)

            if len(videos) >= 5:
                break

    except HttpError as e:
        logger.error(f"Failed to fetch videos: {e}")

    return videos

### Fetch Channel Details ###
def fetch_channel_details(url):
    """Fetch YouTube channel details"""
    try:
        match = re.search(r'youtube\.com/channel/([^/?]+)', url)
        channel_id = match.group(1) if match else None

        if not channel_id:
            return None

        response = youtube.channels().list(id=channel_id, part='snippet').execute()
        if response.get('items'):
            item = response['items'][0]
            return {
                'channel_id': item['id'],
                'channel_name': item['snippet']['title'],
                'profile_pic_url': item['snippet']['thumbnails']['high']['url']
            }
        return None

    except Exception as e:
        logger.error(f"Error fetching channel details: {e}")
        return None
