"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from accounts import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView
from subplayer import views as subplayer_views
from subplayer.views import podcast_detail, video_detail, media_list, add_media, dictionary_lookup, search
from django.contrib.auth import views as auth_views
from accounts.views import register
from accounts.views import add_viewed_media, viewed_media_list, get_media_progress, update_media_progress, get_highlights, get_all_highlights, create_highlight, delete_highlight, modify_highlight, my_media, remove_media_status





urlpatterns = [
    path('', media_list, name='home'),
    path('admin/', admin.site.urls),
    path('subplayer/', TemplateView.as_view(template_name='subplayer.html'), name='subplayer'),
    path('podcast/', subplayer_views.podcast_view, name='podcast_view'),
    path('video/', subplayer_views.video_view, name='video_view'),
    path('podcast/<str:media_id>/', podcast_detail, name='podcast_detail'),
    path('video/<str:media_id>/', video_detail, name='video_detail'),
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('api/user/viewed-media/add', add_viewed_media, name='add_viewed_media'),
    path('api/user/viewed_media_list/read', views.viewed_media_list, name='viewed_media_list'),
    path('api/user/media_progress/<int:media_id>/', views.get_media_progress, name='get_media_progress'),
    path('api/user/save-progress', update_media_progress, name='update_media_progress'),
    path('api/user/create_highlight', create_highlight, name='create_highlight'),
    path('api/user/delete_highlight/<int:highlight_id>/', delete_highlight, name='delete_highlight'),
    path('api/user/modify_highlight/<int:highlight_id>/', modify_highlight, name='modify_highlight'),

 path('api/user/get_highlights/', get_all_highlights, name='get_all_highlights'),
    path('api/user/get_highlights/<str:media_id>/', get_highlights, name='get_highlights'),

path('highlights/', views.highlights, name='highlights'),
    path('admin/', admin.site.urls),
        path('add_media/', add_media, name='add_media'),
    path('media_list/', views.media_list, name='media_list'),

path('media/update_status/<str:media_id>/<str:status>/', views.update_media_status, name='update_media_status'),
    path('media/list_by_status/<str:status>/', views.list_media_by_status, name='list_media_by_status'),

    path('my_media/', views.my_media, name='my_media'),

    

path('media/remove_status/<int:media_id>/', views.remove_media_status, name='remove_media_status'),
    path('api/dictionary-lookup/', dictionary_lookup, name='dictionary_lookup'),






path('search/', search, name='search'),


    # Add other URL patterns for your project
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)