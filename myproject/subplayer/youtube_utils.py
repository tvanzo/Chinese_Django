from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
import re
import os
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Initialize YouTube API
youtube = build('youtube', 'v3', developerKey='AIzaSyBbuGRULqUYyCxDBZyoHFgzHwseF-fnrwg')

def fetch_subtitles(video_id):
    try:
        # Fetch the subtitles using the youtube_transcript_api
        subtitles = YouTubeTranscriptApi.get_transcript(video_id)
        logger.info(f"Subtitles fetched successfully for video ID: {video_id}")
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
            'video_id': None
        }

    try:
        # Check if video exists and get details
        video_response = youtube.videos().list(id=video_id, part='snippet').execute()
        if not video_response['items']:
            logger.error(f"YouTube video does not exist for video ID: {video_id}")
            return {
                'status': 'invalid',
                'message': "This YouTube video does not exist.",
                'title': None,
                'video_id': None
            }

        # Extract title from video details
        video_title = video_response['items'][0]['snippet']['title']

        # Fetch and process subtitles
        subtitles = fetch_subtitles(video_id)
        if subtitles is None:
            logger.error(f"Failed to fetch subtitles for video ID: {video_id}")
            return {
                'status': 'invalid',
                'message': "Failed to fetch subtitles for this video.",
                'title': video_title,
                'video_id': video_id
            }

        # Process and save subtitles
        subtitles_file_path = process_and_save_subtitles(subtitles, video_id)
        if subtitles_file_path is None:
            logger.error(f"Failed to process and save subtitles for video ID: {video_id}")
            return {
                'status': 'invalid',
                'message': "Failed to process and save subtitles for this video.",
                'title': video_title,
                'video_id': video_id
            }

        logger.info(f"Video details fetched successfully for video ID: {video_id}")
        return {
            'status': 'valid',
            'message': "This YouTube video is valid and has subtitles.",
            'title': video_title,
            'video_id': video_id,
            'subtitles_file_path': subtitles_file_path
        }

    except HttpError as e:
        logger.error(f"An API error occurred for video ID {video_id}: {e}")
        return {
            'status': 'invalid',
            'message': f"An API error occurred: {e.resp.status} {e.content}",
            'title': None,
            'video_id': None
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
    try:
        os.makedirs(full_subtitles_dir, exist_ok=True)  # Ensure directory exists
    except OSError as e:
        print(f"An error occurred while creating the directory: {e}")
        # Handle the error or propagate it as needed

    # Specify the file path where you want to save the JSON data
    file_name = f"{video_id}_subtitles.json"
    file_path = os.path.join(full_subtitles_dir, file_name)
    relative_file_path = os.path.join(subtitles_dir, file_name)  # Relative path for the FileField

    # Convert to JSON and write to a file
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(output_data, file, ensure_ascii=False, indent=4)
        print(f"Subtitles saved to {file_path}")
        return relative_file_path  # Return the relative path for storing in the model
    except IOError as e:
        print(f"An error occurred while writing the file: {e}")
        # Handle the error or propagate it as needed
        return None



