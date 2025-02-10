from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import TemplateView
from accounts import views as account_views
from subplayer import views as subplayer_views
from allauth.account.views import LoginView, LogoutView, SignupView
from allauth.account.views import PasswordResetView
from django.views.static import serve
from accounts.views import stripe_webhook, create_checkout_session
from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', account_views.home_redirect_view, name='home_redirect'),
    path('subplayer/', TemplateView.as_view(template_name='subplayer.html'), name='subplayer'),
    path('podcast/', subplayer_views.podcast_detail, name='podcast_view'),
    path('video/', subplayer_views.video_detail, name='video_view'),
    path('podcast/<str:media_id>/', subplayer_views.podcast_detail, name='podcast_detail'),
    path('video/<str:media_id>/', subplayer_views.video_detail, name='video_detail'),
    path('watch/', subplayer_views.media_list, name='media_list'),
    path('add_media/', subplayer_views.add_media, name='add_media'),
    path('search/', subplayer_views.search, name='search'),
    path('channel/<str:channel_name>/', subplayer_views.channel_view, name='channel_view'),
    path('channels/', subplayer_views.channels_list, name='channels_list'),
    path('intro/', subplayer_views.intro_view, name='intro'),
path('dashboard/', account_views.stats_view, name='stats_view'),
    path('download_subtitles/', account_views.download_subtitles, name='download_subtitles'),

    # API paths
    path('api/user/viewed-media/add', account_views.add_viewed_media, name='add_viewed_media'),
    path('api/user/viewed_media_list/read', account_views.viewed_media_list, name='viewed_media_list'),
    path('api/user/media_progress/<str:media_id>/', account_views.get_media_progress, name='get_media_progress'),
    path('api/user/save-progress', account_views.update_media_progress, name='update_media_progress'),
    path('api/user/create_highlight', account_views.create_highlight, name='create_highlight'),
    path('api/user/delete_highlight/<int:highlight_id>/', account_views.delete_highlight, name='delete_highlight'),
    path('api/user/modify_highlight/<int:highlight_id>/', account_views.modify_highlight, name='modify_highlight'),
    path('api/user/get_highlights/', account_views.get_all_highlights, name='get_all_highlights'),
    path('api/user/get_highlights/<str:media_id>/', account_views.get_highlights, name='get_highlights'),
    path('api/dictionary-lookup/', subplayer_views.dictionary_lookup, name='dictionary_lookup'),
    path('api/user/update-progress', account_views.update_progress, name='update_progress'),

    # Highlights and media management
    path('highlights/', account_views.highlights, name='highlights'),
    path('highlights/download/', account_views.download_highlights, name='download_highlights'),
    path('highlights/<str:media_id>/', account_views.highlights_detail, name='highlights_detail'),
    path('media/update_status/<str:media_id>/<str:status>/', account_views.update_media_status, name='update_media_status'),
    path('media/list_by_status/<str:status>/', account_views.list_media_by_status, name='list_media_by_status'),
    path('my_media/', account_views.my_media, name='my_media'),
    path('media/remove_status/<int:media_id>/', account_views.remove_media_status, name='remove_media_status'),

    # User management
    path('library/', account_views.user_videos, name='user_videos'),
    path('remove_from_log/<int:media_id>/', account_views.remove_from_log, name='remove_from_log'),
    path('add_to_log/<int:media_id>/', account_views.add_to_log, name='add_to_log'),
    path('join/', account_views.join, name='join'),

    # Authentication and accounts
    path('accounts/', include('allauth.urls')),
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('register/', account_views.register, name='register'),
    path('logout/', account_views.custom_logout_view, name='logout'),
    path('password/reset/', PasswordResetView.as_view(template_name='accounts/password_reset.html'),
         name='account_reset_password'),
    path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    path('create-checkout-session/', create_checkout_session, name='create_checkout_session'),
    path('stripe-webhook/', stripe_webhook, name='stripe_webhook'),
    path('checkout/', TemplateView.as_view(template_name='accounts/checkout.html'), name='checkout'),
    path('success/', TemplateView.as_view(template_name='accounts/success.html'), name='success'),
    path('cancel/', TemplateView.as_view(template_name='accounts/cancel.html'), name='cancel'),
    path('payment_success/', account_views.handle_payment_success, name='payment_success'),
    path('account/', account_views.account_view, name='account'),
    path('update-payment/', account_views.update_payment_view, name='update_payment'),
    path('cancel-subscription/', account_views.cancel_subscription, name='cancel_subscription'),
    path('reactivate-subscription/', account_views.reactivate_subscription, name='reactivate_subscription'),
    path('upgrade/', account_views.upgrade_plan, name='upgrade_plan'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
