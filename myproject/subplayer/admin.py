from django.contrib import admin
from django import forms
from django.contrib import messages
from django.core.files.base import ContentFile
from django.conf import settings
import os
import logging

from .models import Media, Channel
from .youtube_utils import fetch_video_details, fetch_channel_details, fetch_videos_from_channel_with_chinese_subtitles

logger = logging.getLogger(__name__)


class MediaAdminForm(forms.ModelForm):
    class Meta:
        model = Media
        fields = ['url']

class MediaAdmin(admin.ModelAdmin):
    form = MediaAdminForm
    list_display = ('title', 'url', 'media_type', 'channel', 'media_id', 'category')  # Added 'category'
    search_fields = ['title', 'url', 'channel__name']
    list_filter = ['category']  # Optional, for filtering by category

    def save_model(self, request, obj, form, change):
        video_details = fetch_video_details(obj.url)
        if video_details['status'] == 'valid':
            # Fetch or create the associated channel
            channel_url = f"https://www.youtube.com/channel/{video_details['channel_id']}"
            channel_details = fetch_channel_details(channel_url)
            if channel_details:
                channel, created = Channel.objects.update_or_create(
                    channel_id=channel_details['channel_id'],
                    defaults={
                        'name': channel_details.get('channel_name', 'Unnamed Channel'),
                        'url': channel_url,
                        'profile_pic_url': channel_details.get('profile_pic_url', '')
                    }
                )
                obj.channel = channel
            else:
                messages.error(request, "Failed to fetch or update channel details.")
                return

            obj.subtitle_file = video_details.get('subtitles_file_path')
            obj.word_count = int(video_details.get('word_count', 0))
            obj.title = video_details['title']
            obj.media_type = 'video'
            obj.media_id = video_details['video_id']
            obj.youtube_video_id = video_details['video_id']
            obj.video_length = video_details['video_length']
            obj.category = video_details.get('category_id', 'Unknown')  # Ensure the category is assigned
            super().save_model(request, obj, form, change)
        else:
            messages.error(request, video_details.get('message', 'Failed to fetch video details.'))



admin.site.register(Media, MediaAdmin)

class ChannelAdminForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['url']

    def clean(self):
        cleaned_data = super().clean()
        url = cleaned_data.get('url')
        if not url:
            raise forms.ValidationError({'url': "URL cannot be blank."})
        logger.info(f"Fetching channel details for URL: {url}")
        channel_details = fetch_channel_details(url)
        if not channel_details or 'channel_id' not in channel_details or not channel_details['channel_id']:
            logger.error(f"Failed to fetch channel details for URL: {url}")
            raise forms.ValidationError("Failed to fetch channel details or channel ID not found. Please check the URL and try again.")

        cleaned_data['channel_id'] = channel_details['channel_id']
        cleaned_data['name'] = channel_details.get('channel_name', 'Unnamed Channel')
        cleaned_data['profile_pic_url'] = channel_details.get('profile_pic_url', '')
        logger.info(f"Channel details fetched and validated for: {cleaned_data['name']}")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.channel_id = self.cleaned_data['channel_id']
        instance.name = self.cleaned_data['name']
        instance.profile_pic_url = self.cleaned_data.get('profile_pic_url', '')
        if commit:
            instance.save()
            logger.info(f"Channel '{instance.name}' saved successfully with ID: {instance.channel_id}")
        return instance

class ChannelAdmin(admin.ModelAdmin):
    form = ChannelAdminForm
    list_display = ('name', 'channel_id', 'url')
    actions = ['fetch_videos']

    def fetch_videos(self, request, queryset):
        logger.info("Starting fetch_videos action in admin.")
        for channel in queryset:
            logger.info(f"Attempting to fetch videos for channel: {channel.name} (ID: {channel.channel_id})")
            videos = fetch_videos_from_channel_with_chinese_subtitles(channel.channel_id)
            if videos:
                logger.info(f"Found {len(videos)} videos for channel: {channel.name}")
                for video in videos:
                    result, created = Media.objects.update_or_create(
                        youtube_video_id=video['video_id'],
                        defaults={
                            'title': video['title'],
                            'url': f"https://www.youtube.com/watch?v={video['video_id']}",
                            'media_type': 'video',
                            'subtitle_file': video.get('subtitles_file_path'),
                            'word_count': video.get('word_count', 0),
                            'video_length': video['video_length'],
                            'channel': channel,
                            'category': video['category_id'],
                            'thumbnail_url': video.get('thumbnail_url'),
                            'media_id': video['video_id']  # Ensure media_id is also set correctly
                        }
                    )
                    if created:
                        logger.info(f"Created new media object for video: {video['title']}")
                    else:
                        logger.info(f"Updated existing media object for video: {video['title']}")
            else:
                logger.warning(f"No videos found or failed to fetch videos for channel: {channel.name}")
                messages.warning(request, f"No videos found or failed to fetch videos for channel: {channel.name}")

    fetch_videos.short_description = "Fetch latest videos with Chinese subtitles"


admin.site.register(Channel, ChannelAdmin)
