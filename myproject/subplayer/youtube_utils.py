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
        # Try fetching Chinese subtitles first
        try:
            subtitles = YouTubeTranscriptApi.get_transcript(video_id, languages=['zh-CN', 'zh-Hans', 'zh-Hant', 'zh-CN', 'zh', 'zh-TW'])
            logger.info(f"Chinese subtitles fetched successfully for video ID: {video_id}")
        except:
            # If fetching Chinese subtitles fails, fall back to the default language
            subtitles = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
            logger.info(f"Subtitles fetched successfully for video ID: {video_id} in default language")
        
        return subtitles
    except Exception as e:
        logger.error(f"An error occurred while fetching subtitles for video ID {video_id}: {e}")
        return None


def fetch_video_details(url):
    video_id_match = re.search(r'(?<=v=)[^&#]+', url) or re.search(r'(?<=be/)[^&#]+', url)
    video_id = video_id_match.group(0) if video_id_match else None

    if not video_id:
        return {'status': 'invalid', 'message': "Invalid YouTube URL."}

    try:
        video_response = youtube.videos().list(id=video_id, part='snippet,contentDetails').execute()

        if not video_response['items']:
            return {'status': 'invalid', 'message': "YouTube video does not exist."}

        video_item = video_response['items'][0]
        video_title = video_item['snippet']['title']
        thumbnail_url = video_item['snippet']['thumbnails']['high']['url']
        duration = parse_duration(video_item['contentDetails']['duration'])
        duration_iso8601 = video_item['contentDetails']['duration']
        duration_timedelta = parse_duration(duration_iso8601)
        video_length_seconds = int(duration_timedelta.total_seconds())  # Convert to total seconds as integer

        subtitles = fetch_subtitles(video_id)
        subtitles_path = None
        if subtitles:
            subtitles_path, word_count= process_and_save_subtitles(subtitles, video_id)

        return {
            'status': 'valid',
            'message': "Video details fetched successfully.",
            'title': video_title,
            'video_id': video_id,
            'thumbnail_url': thumbnail_url,
            'video_length': video_length_seconds,
            'subtitles_file_path': subtitles_path,
            'word_count': word_count  

        }
    except HttpError as e:
        return {'status': 'invalid', 'message': f"An API error occurred: {e}"}


# Initialize logger
logger = logging.getLogger(__name__)

def process_and_save_subtitles(subtitles, video_id):
    if not subtitles:
        logger.error(f"No subtitles data provided for video ID: {video_id}")
        return None, 0

    # Construct transcript and count words
    transcript = " ".join([sub.get('text', '') for sub in subtitles])
    if not transcript:
        logger.error(f"Transcript could not be constructed for video ID: {video_id}")
        return None, 0
    logger.error(f"Transcript: {transcript.split()}")
    logger.error(f"Transcript2: {transcript}")
    logger.error(f"Transcriptlen: {len(transcript.split())}")
    logger.error(f"Transcriptlen2: {len(transcript)}")




    word_count = len(transcript)

    # Prepare subtitles data for saving
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
        
        # Check if the subtitles file was created successfully
        if os.path.exists(file_path):
            relative_path = os.path.relpath(file_path, start=settings.MEDIA_ROOT)
            logger.info(f"Successfully saved subtitles for video ID {video_id} at {relative_path} with wordcount of {word_count}")
            return relative_path, word_count
        else:
            logger.error(f"Subtitle file was not created at the expected path: {file_path}")
            return None, 0
    except Exception as e:
        logger.error(f"Failed to save subtitles for video ID {video_id}: {e}")
        return None, 0
