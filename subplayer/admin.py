from django.contrib import admin
from django import forms
from django.contrib import messages
from .models import Media, Channel, Category
from .youtube_utils import fetch_video_details, fetch_channel_details, fetch_videos_from_channel_with_chinese_subtitles
import logging

logger = logging.getLogger(__name__)

# Static mapping of YouTube category IDs to names
YOUTUBE_CATEGORIES = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "18": "Short Movies",
    "19": "Travel & Events",
    "20": "Gaming",
    "21": "Videoblogging",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
    "29": "Nonprofits & Activism",
    "30": "Movies",
    "31": "Anime/Animation",
    "32": "Action/Adventure",
    "33": "Classics",
    "34": "Comedy",
    "35": "Documentary",
    "36": "Drama",
    "37": "Family",
    "38": "Foreign",
    "39": "Horror",
    "40": "Sci-Fi/Fantasy",
    "41": "Thriller",
    "42": "Shorts",
    "43": "Shows",
    "44": "Trailers",
}


# MediaAdminForm to handle the URL field
class MediaAdminForm(forms.ModelForm):
    class Meta:
        model = Media
        fields = ['url']


# Custom filter to allow filtering by category in the admin interface
class CategoryFilter(admin.SimpleListFilter):
    title = 'Category'
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        categories = Category.objects.all()
        return [(category.id, category.name) for category in categories]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(categories__id=self.value())
        return queryset


# Admin for Media model
class MediaAdmin(admin.ModelAdmin):
    form = MediaAdminForm
    list_display = ('title', 'url', 'media_type', 'channel', 'media_id', 'category_display')
    search_fields = ['title', 'url', 'channel__name']
    list_filter = [CategoryFilter]

    # Custom method to display categories
    def category_display(self, obj):
        return ", ".join([category.name for category in obj.categories.all()])

    category_display.short_description = 'Categories'

    def save_model(self, request, obj, form, change):
        video_details = fetch_video_details(obj.url)
        if video_details['status'] == 'valid':
            channel_url = f"https://www.youtube.com/channel/{video_details['channel_id']}"
            channel_details = fetch_channel_details(channel_url)
            obj.youtube_upload_time = video_details['youtube_upload_time']

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
            super().save_model(request, obj, form, change)

            # Handle categories
            if 'category_id' in video_details:
                category_name = YOUTUBE_CATEGORIES.get(video_details['category_id'],
                                                       f"Category {video_details['category_id']}")
                category, _ = Category.objects.get_or_create(
                    id=video_details['category_id'],
                    defaults={'name': category_name}
                )
                obj.categories.add(category)
        else:
            messages.error(request, video_details.get('message', 'Failed to fetch video details.'))


admin.site.register(Media, MediaAdmin)


# ChannelAdminForm for Channel model with added categories
class ChannelAdminForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(queryset=Category.objects.all(), required=False)

    class Meta:
        model = Channel
        fields = ['url', 'categories']

    def clean(self):
        cleaned_data = super().clean()
        url = cleaned_data.get('url')
        if not url:
            raise forms.ValidationError({'url': "URL cannot be blank."})
        logger.info(f"Fetching channel details for URL: {url}")
        channel_details = fetch_channel_details(url)
        if not channel_details or 'channel_id' not in channel_details or not channel_details['channel_id']:
            logger.error(f"Failed to fetch channel details for URL: {url}")
            raise forms.ValidationError(
                "Failed to fetch channel details or channel ID not found. Please check the URL and try again.")

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
            # Assign selected categories to the channel
            if self.cleaned_data['categories']:
                instance.categories.set(self.cleaned_data['categories'])
        return instance


# Admin for Channel model
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
                    if video['status'] == 'valid':
                        result, created = Media.objects.update_or_create(
                            youtube_video_id=video['video_id'],
                            defaults={
                                'title': video['title'],
                                'url': f"https://www.youtube.com/watch?v={video['video_id']}",
                                'media_type': 'video',
                                'subtitle_file': video.get('subtitles_file_path'),
                                'word_count': video.get('word_count', 0),
                                'video_length': video.get('video_length'),
                                'channel': channel,
                                'thumbnail_url': video.get('thumbnail_url'),
                                'media_id': video['video_id'],
                                'youtube_upload_time': video['youtube_upload_time']
                            }
                        )
                        # Handle YouTube category
                        if 'category_id' in video:
                            category_name = YOUTUBE_CATEGORIES.get(video['category_id'],
                                                                   f"Category {video['category_id']}")
                            category, _ = Category.objects.get_or_create(
                                id=video['category_id'],
                                defaults={'name': category_name}
                            )
                            result.categories.add(category)
                        if created:
                            logger.info(f"Created new media object for video: {video['title']}")
                        else:
                            logger.info(f"Updated existing media object for video: {video['title']}")
                messages.success(request, f"Successfully fetched {len(videos)} videos for channel: {channel.name}")
            else:
                logger.warning(f"No videos found or failed to fetch videos for channel: {channel.name}")
                messages.warning(request, f"No videos found or failed to fetch videos for channel: {channel.name}")

    fetch_videos.short_description = "Fetch latest videos with Chinese subtitles"


# Registering ChannelAdmin
admin.site.register(Channel, ChannelAdmin)


# Registering Category model to be editable in the Django admin
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')
    search_fields = ['name']


admin.site.register(Category, CategoryAdmin)