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

def fetch_subtitles(video_id, language='en'):
    try:
        # Try fetching Chinese subtitles first
        try:
            subtitles = YouTubeTranscriptApi.get_transcript(video_id, languages=['zh-Hans', 'zh-Hant', 'zh-CN'])
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
    # Extract video ID from URL
    video_id_match = re.search(r'(?<=v=)[^&#]+', url) or re.search(r'(?<=be/)[^&#]+', url)
    video_id = video_id_match.group(0) if video_id_match else None

    if not video_id:
        logger.error("Invalid YouTube URL.")
        return {
            'status': 'invalid',
            'message': "This is not a valid YouTube URL.",
            'title': None,
            'video_id': None,
            'thumbnail_url': None,
            'video_length': None  # Add video_length here
        }

    try:
        # Fetch video details including contentDetails for duration
        video_response = youtube.videos().list(
            id=video_id,
            part='snippet,contentDetails'
        ).execute()

        if not video_response['items']:
            logger.error(f"YouTube video does not exist for video ID: {video_id}")
            return {
                'status': 'invalid',
                'message': "This YouTube video does not exist.",
                'title': None,
                'video_id': None,
                'thumbnail_url': None,
                'video_length': None
            }

        video_item = video_response['items'][0]
        video_title = video_item['snippet']['title']
        thumbnail_url = video_item['snippet']['thumbnails']['high']['url']

        # Parse ISO 8601 duration format
        duration_iso8601 = video_item['contentDetails']['duration']
        duration = parse_duration(duration_iso8601)

        # Convert duration to a string format, e.g., "4:13"
        # Note: You might need to adjust this based on your requirements
        video_length = str(duration).split('.')[0]  # This will have format like '0:04:13'

        # Further process if needed (fetching subtitles, etc.)
        # ...
         # Fetch and process subtitles
        subtitles = fetch_subtitles(video_id)
        if subtitles is None:
            logger.error(f"Failed to fetch subtitles for video ID: {video_id}")
            return {
                'status': 'invalid',
                'message': "Failed to fetch subtitles for this video.",
                'title': video_title,
                'video_id': video_id,
                'thumbnail_url': thumbnail_url  # Include thumbnail_url in the return dictionary
            }

        # Process and save subtitles
        subtitles_file_path = process_and_save_subtitles(subtitles, video_id)
        if subtitles_file_path is None:
            logger.error(f"Failed to process and save subtitles for video ID: {video_id}")
            return {
                'status': 'invalid',
                'message': "Failed to process and save subtitles for this video.",
                'title': video_title,
                'video_id': video_id,
                'thumbnail_url': thumbnail_url  # Include thumbnail_url in the return dictionary
            }

        logger.info(f"Video details fetched successfully for video ID: {video_id}")
        return {
            'status': 'valid',
            'message': "This YouTube video is valid and has subtitles.",
            'title': video_title,
            'video_id': video_id,
            'thumbnail_url': thumbnail_url,
            'video_length': video_length,  # Include video_length in the return dictionary
            'subtitles_file_path': subtitles_file_path
        }
    except HttpError as e:
        logger.error(f"An API error occurred for video ID {video_id}: {e}")
        return {
            'status': 'invalid',
            'message': f"An API error occurred: {e.resp.status} {e.content}",
            'title': None,
            'video_id': None,
            'thumbnail_url': None,
            'video_length': None
        }


def process_and_save_subtitles(subtitles, video_id):
    # Initialize variables for transcript and words
    transcript = ""
    words = []

    # Loop through each subtitle entry to create words and transcript
    for subtitle in subtitles:
        text = subtitle['text']
        start_time = subtitle['start']
        duration = subtitle['duration']
        
        # Calculate end time by adding duration to start time
        end_time = start_time + duration
        
        # Append the text to the transcript
        transcript += text + " "  # Add space between sentences

        # Split the text into words
        words_list = text.split()

        # Create word entries with start and end times
        for word in words_list:
            words.append({
                'startTime': f"{start_time:.3f}s",
                'endTime': f"{end_time:.3f}s",
                'word': word
            })

    # Create the final JSON structure
    output_data = {
        'transcript': transcript.strip(),  # Remove trailing space
        'words': words
    }
 # Define the directory to save subtitle files within MEDIA_ROOT
    subtitles_dir = 'subtitles'  # Relative path from MEDIA_ROOT
    full_subtitles_dir = os.path.join(settings.MEDIA_ROOT, subtitles_dir)
    os.makedirs(full_subtitles_dir, exist_ok=True)  # Ensure directory exists

    # Specify the file path where you want to save the JSON data
    file_name = f"{video_id}_subtitles.json"
    file_path = os.path.join(full_subtitles_dir, file_name)

    # Convert to JSON and write to a file
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(output_data, file, ensure_ascii=False, indent=4)
        print(f"Subtitles saved to {file_path}")
        return os.path.join(subtitles_dir, file_name)  # Return the relative path for storing in the model
    except IOError as e:
        print(f"An error occurred while writing the file: {e}")
        return None

