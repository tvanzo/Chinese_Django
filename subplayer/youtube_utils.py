from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
import re
import os
import json
from django.conf import settings
import logging
from isodate import parse_duration
from google.auth.exceptions import DefaultCredentialsError
from datetime import datetime
from datetime import datetime, timezone  # Add timezone import


logger = logging.getLogger(__name__)

# Initialize YouTube API
google_api_key = os.getenv('GOOGLE_API_KEY')
if not google_api_key:
    raise RuntimeError("GOOGLE_API_KEY environment variable is not set")

try:
    youtube = build('youtube', 'v3', developerKey=google_api_key)
except DefaultCredentialsError as e:
    logger.error("Failed to authenticate with Google API: %s", e)
    raise RuntimeError("Failed to authenticate with Google API") from e

def fetch_subtitles(video_id, language='zh'):
    try:
        proxy_username = os.getenv('SMARTPROXY_USERNAME', 'spkvdhj6aq')
        proxy_password = os.getenv('SMARTPROXY_PASSWORD', 'BmbkI+85nRf1Idopi2')
        proxy_host = 'gate.visitxiangtan.com'
        proxy_port = '10003'  # Updated to working port

        proxies = {
            "http": f"http://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}",
            "https": f"http://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"
        }

        # Use timeout if library supports it; otherwise omit
        try:
            # For version >= 0.6.0
            return YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=['zh-CN', 'zh-Hans', 'zh-Hant', 'zh', 'zh-TW'],
                proxies=proxies,
                timeout=15  # Increased for stability
            )
        except TypeError:
            # Fallback for older versions
            return YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=['zh-CN', 'zh-Hans', 'zh-Hant', 'zh', 'zh-TW'],
                proxies=proxies
            )
    except Exception as e:
        logger.error(f"Failed to fetch subtitles for video ID {video_id}: {e}")
        return None

#d
def fetch_video_details(url):
    logger.debug(f"Fetching video details for URL: {url}")
    if "youtube.com" not in url and "youtu.be" not in url:
        url = f"https://www.youtube.com/watch?v={url}"
        logger.debug(f"Adjusted URL to: {url}")

    video_id_match = re.search(r'(?<=v=)[^&#]+', url) or re.search(r'(?<=be/)[^&#]+', url)
    video_id = video_id_match.group(0) if video_id_match else None

    if not video_id:
        logger.error("Invalid YouTube URL provided: " + url)
        return {'status': 'invalid', 'message': "Invalid YouTube URL."}

    logger.debug(f"Using video ID: {video_id} to fetch details.")

    try:
        video_response = youtube.videos().list(id=video_id, part='snippet,contentDetails,status').execute()
        if not video_response.get('items'):
            logger.warning(f"No YouTube video exists for the provided ID: {video_id}")
            return {'status': 'invalid', 'message': "YouTube video does not exist."}

        video_item = video_response['items'][0]

        # Check if the video is embeddable
        if video_item['status'].get('embeddable') is False:
            logger.warning(f"Video ID {video_id} is not embeddable.")
            return {'status': 'invalid', 'message': "Video not supported: Sorry, this is the rare case a YouTuber has disabled embedding on this video."}

        video_title = video_item['snippet']['title']
        thumbnail_url = video_item['snippet']['thumbnails']['high']['url']
        channel_id = video_item['snippet']['channelId']
        category_id = video_item['snippet']['categoryId']
        duration = parse_duration(video_item['contentDetails']['duration'])
        video_length_seconds = int(duration.total_seconds())

        # Capture the upload time
        published_at = video_item['snippet']['publishedAt']
        from django.utils.timezone import make_aware

        upload_time = make_aware(datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ"))

        subtitles = fetch_subtitles(video_id)
        subtitles_path = None
        word_count = 0
        if subtitles:
            subtitles_path, word_count = process_and_save_subtitles(subtitles, video_id)

        logger.info(f"Successfully fetched details for video ID: {video_id}")
        return {
            'status': 'valid',
            'message': "Video details fetched successfully.",
            'title': video_title,
            'video_id': video_id,
            'thumbnail_url': thumbnail_url,
            'video_length': video_length_seconds,
            'subtitles_file_path': subtitles_path,
            'word_count': word_count,
            'channel_id': channel_id,
            'category_id': category_id,
            'upload_time': upload_time  # Added this line for upload time
        }
    except HttpError as e:
        logger.error(f"HTTP Error while fetching video details: {e}")
        return {'status': 'invalid', 'message': f"An API error occurred: {e}"}

def process_and_save_subtitles(subtitles, video_id):
    if not subtitles:
        logger.error(f"No subtitles data provided for video ID: {video_id}")
        return None, 0

    transcript = " ".join([sub.get('text', '') for sub in subtitles])
    if not transcript:
        logger.error(f"Transcript could not be constructed for video ID: {video_id}")
        return None, 0

    word_count = len(transcript.split())
    subtitles_data = {
        'transcript': transcript,
        'words': [{
            'startTime': sub['start'],
            'endTime': sub['start'] + sub['duration'],
            'word': word
        } for sub in subtitles for word in sub.get('text', '').split()]
    }

    subtitles_dir = os.path.join(settings.MEDIA_ROOT, 'subtitles')
    os.makedirs(subtitles_dir, exist_ok=True)
    file_path = os.path.join(subtitles_dir, f"{video_id}_subtitles.json")

    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(subtitles_data, file, ensure_ascii=False, indent=4)

        if os.path.exists(file_path):
            relative_path = os.path.relpath(file_path, start=settings.MEDIA_ROOT)
            logger.info(
                f"Successfully saved subtitles for video ID {video_id} at {relative_path} with word count of {word_count}")
            return relative_path, word_count
        else:
            logger.error(f"Subtitle file was not created at the expected path: {file_path}")
            return None, 0
    except Exception as e:
        logger.error(f"Failed to save subtitles for video ID {video_id}: {e}")
        return None, 0

def fetch_channel_details(url):
    try:
        channel_id = None
        username = None
        # Try extracting channel ID from URL
        match = re.search(r'youtube\.com/channel/([^/?]+)', url)
        if match:
            channel_id = match.group(1)
            logger.debug(f"Extracted channel ID: {channel_id}")
        else:
            # Try extracting username from URL
            match = re.search(r'youtube\.com/@([^/?]+)', url)
            if match:
                username = match.group(1)
                logger.debug(f"Extracted username: {username}")
                # Fetch channel ID using the username
                response = youtube.channels().list(part='snippet', forUsername=username).execute()
                logger.debug(f"Response for username {username}: {response}")
                if response.get('items'):
                    channel_id = response['items'][0]['id']
                else:
                    # Handle the case where username lookup fails
                    search_response = youtube.search().list(part='snippet', q=username, type='channel').execute()
                    logger.debug(f"Search response for username {username}: {search_response}")
                    if search_response.get('items'):
                        channel_id = search_response.get('items')[0]['snippet']['channelId']
        if not channel_id:
            logger.error("Channel ID could not be found or extracted from the URL.")
            return None
        # Fetch details using the channel ID
        response = youtube.channels().list(id=channel_id, part='snippet').execute()
        logger.debug(f"Response for channel ID {channel_id}: {response}")
        if response.get('items'):
            item = response['items'][0]
            profile_pic_url = item['snippet']['thumbnails']['default']['url']
            # Replace 's88' with 's176'
            profile_pic_url = re.sub(r's88', 's176', profile_pic_url)
            return {
                'channel_id': item['id'],
                'channel_name': item['snippet']['title'],
                'profile_pic_url': profile_pic_url
            }
        else:
            logger.error("No channel found for the given ID or username.")
            return None
    except Exception as e:
        logger.error(f"An error occurred while fetching channel details: {e}")
        return None

#teste
def fetch_videos_from_channel_with_chinese_subtitles(channel_id):
    videos = []
    nextPageToken = None
    try:
        logger.info(f"Starting video fetch for channel ID: {channel_id}")
        while len(videos) < 5:
            response = youtube.search().list(
                channelId=channel_id, part='id,snippet', maxResults=5, order='date', type='video',
                pageToken=nextPageToken
            ).execute()
            if 'items' not in response:
                logger.warning("No items found in response from YouTube API.")
                break
            for item in response.get('items', []):
                video_id = item['id']['videoId']
                logger.info(f"Processing video ID: {video_id}")
                details = fetch_video_details(video_id)
                if details['status'] == 'valid':
                    if details.get('subtitles_file_path'):
                        videos.append(details)
                        logger.info(f"Video {video_id} added with subtitles.")
                    else:
                        logger.info(f"Video {video_id} skipped, no subtitles.")
                    if len(videos) == 5:
                        break
            nextPageToken = response.get('nextPageToken')
            if not nextPageToken:
                logger.info("No more pages to fetch.")
                break
    except Exception as e:
        logger.error(f"Failed to fetch videos: {e}")
    if not videos:
        logger.warning("No suitable videos were found or added.")
    else:
        logger.info(f"Total videos fetched and added: {len(videos)}")
    return videos


def get_channel_profile_pic(youtube_url):
    try:
        # Extract video ID from the URL
        video_id_match = re.search(r'(?<=v=)[^&#]+', youtube_url) or re.search(r'(?<=be/)[^&#]+', youtube_url)
        video_id = video_id_match.group(0) if video_id_match else None

        if not video_id:
            logger.error(f"Invalid YouTube URL provided: {youtube_url}")
            return None

        # Fetch channel ID
        video_response = youtube.videos().list(
            part="snippet",
            id=video_id
        ).execute()

        if not video_response['items']:
            logger.error(f"No video found with ID: {video_id}")
            return None

        channel_id = video_response["items"][0]["snippet"]["channelId"]

        # Fetch profile picture
        channel_response = youtube.channels().list(
            part="snippet",
            id=channel_id
        ).execute()

        if not channel_response['items']:
            logger.error(f"No channel found with ID: {channel_id}")
            return None

        profile_pic_url = channel_response["items"][0]["snippet"]["thumbnails"]["default"]["url"]
        logger.info(f"Profile picture URL fetched successfully for channel ID: {channel_id}")

        return profile_pic_url
    except Exception as e:
        logger.error(f"An error occurred while fetching the channel profile picture: {e}")
        return None
