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
from django.contrib.auth.views import LoginView
from django.views.generic import TemplateView
from subplayer import views as subplayer_views
from subplayer.views import podcast_detail, video_detail
from django.contrib.auth import views as auth_views
from accounts import views as accounts_views




urlpatterns = [
    path('admin/', admin.site.urls),
    path('subplayer/', TemplateView.as_view(template_name='subplayer.html'), name='subplayer'),
    path('podcast/', subplayer_views.podcast_view, name='podcast_view'),
    path('video/', subplayer_views.video_view, name='video_view'),
    path('podcast/<str:media_id>/', podcast_detail, name='podcast_detail'),
    path('video/<str:media_id>/', video_detail, name='video_detail'),
    path('register/', accounts_views.register, name='register'),
    path('login/', accounts_views.user_login, name='login'),
    path('logout/', accounts_views.user_logout, name='logout'),





    # Add other URL patterns for your project
]