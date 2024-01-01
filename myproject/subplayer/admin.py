# subplayer/admin.py

from django.contrib import admin
from .models import Media

class MediaAdmin(admin.ModelAdmin):
    list_display = ('title', 'url')
    search_fields = ['title', 'url']

admin.site.register(Media, MediaAdmin)
