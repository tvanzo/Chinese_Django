# subplayer/admin.py

from django.contrib import admin
from django import forms
from django.contrib import messages
from .models import Media
from .youtube_utils import fetch_video_details, process_and_save_subtitles  # Ensure these functions provide the necessary data

class MediaAdminForm(forms.ModelForm):
    class Meta:
        model = Media
        fields = ['url']  # Only show the URL field

class MediaAdmin(admin.ModelAdmin):
    form = MediaAdminForm
    list_display = ('title', 'url', 'media_type', 'media_id')
    search_fields = ['title', 'url']

    # In save_model method of MediaAdmin class

    def save_model(self, request, obj, form, change):
        video_details = fetch_video_details(obj.url)
        if video_details['status'] == 'valid':
            # Use the path to the subtitles file
            obj.subtitle_file = video_details['subtitles_file_path']
            obj.title = video_details['title']
            obj.media_type = 'video'
            obj.media_id = video_details['video_id']
            super().save_model(request, obj, form, change)
        else:
            # Handle invalid video or other errors
            messages.error(request, video_details['message'])



admin.site.register(Media, MediaAdmin)