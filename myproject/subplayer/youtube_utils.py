from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
import re
import os
import json
from django.conf import settings
import logging
from isodate import parse_duration

logger = logging.getLogger(__name__)

# Initialize YouTube API
youtube = build('youtube', 'v3', developerKey='AIzaSyBbuGRULqUYyCxDBZyoHFgzHwseF-fnrwg')


def fetch_subtitles(video_id, language='zh'):
    try:
        return YouTubeTranscriptApi.get_transcript(video_id, languages=['zh-CN', 'zh-Hans', 'zh-Hant', 'zh', 'zh-TW'])
    except Exception as e:
        logger.error(f"Failed to fetch subtitles for video ID {video_id}: {e}")
        return None


def fetch_video_details(url):
    logger.debug(f"Fetching video details for URL: {url}")
    # Check if the URL already contains a proper YouTube base URL
    if "youtube.com" not in url and "youtu.be" not in url:
        url = f"https://www.youtube.com/watch?v={url}"
        logger.debug(f"Adjusted URL to: {url}")

    video_id_match = re.search(r'(?<=v=)[^&#]+', url) or re.search(r'(?<=be/)[^&#]+', url)
    video_id = video_id_match.group(0) if video_id_match else None
    logger.error("URL provided: " + url)

    if not video_id:
        logger.error("Invalid YouTube URL provided: " + url)
        return {'status': 'invalid', 'message': "Invalid YouTube URL."}

    logger.debug(f"Using video ID: {video_id} to fetch details.")

    try:
        video_response = youtube.videos().list(id=video_id, part='snippet,contentDetails').execute()
        if not video_response.get('items'):
            logger.warning(f"No YouTube video exists for the provided ID: {video_id}")
            return {'status': 'invalid', 'message': "YouTube video does not exist."}

        video_item = video_response['items'][0]
        video_title = video_item['snippet']['title']
        thumbnail_url = video_item['snippet']['thumbnails']['high']['url']
        channel_id = video_item['snippet']['channelId']
        category_id = video_item['snippet']['categoryId']
        duration = parse_duration(video_item['contentDetails']['duration'])
        video_length_seconds = int(duration.total_seconds())

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
            'category_id': category_id
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

    logger.info(f"Saving subtitles to: {file_path}")
    logger.info(f"Subtitles directory exists: {os.path.isdir(subtitles_dir)}")
    logger.info(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")

    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(subtitles_data, file, ensure_ascii=False, indent=4)

        if os.path.exists(file_path):
            relative_path = os.path.relpath(file_path, start=settings.MEDIA_ROOT)
            logger.info(f"Successfully saved subtitles for video ID {video_id} at {relative_path} with word count of {word_count}")
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
                        channel_id = search_response['items'][0]['snippet']['channelId']
        if not channel_id:
            logger.error("Channel ID could not be found or extracted from the URL.")
            return None
        # Fetch details using the channel ID
        response = youtube.channels().list(id=channel_id, part='snippet').execute()
        logger.debug(f"Response for channel ID {channel_id}: {response}")
        if response.get('items'):
            item = response['items'][0]
            return {
                'channel_id': item['id'],
                'channel_name': item['snippet']['title'],
                'profile_pic_url': item['snippet']['thumbnails']['default']['url']
            }
        else:
            logger.error("No channel found for the given ID or username.")
            return None
    except Exception as e:
        logger.error(f"An error occurred while fetching channel details: {e}")
        return None



def fetch_videos_from_channel_with_chinese_subtitles(channel_id):
    videos = []
    nextPageToken = None
    try:
        logger.info(f"Starting video fetch for channel ID: {channel_id}")
        while len(videos) < 25:
            response = youtube.search().list(
                channelId=channel_id, part='id,snippet', maxResults=25, order='date', type='video',
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
                    if len(videos) == 25:
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
