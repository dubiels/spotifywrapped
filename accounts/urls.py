from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.spotify_login, name='login'),
    path('callback/', views.spotify_callback, name='callback'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('wraps/', views.past_wraps, name='past_wraps'),
    path('wraps/<int:wrap_id>/', views.wrap_detail, name='wrap_detail'),
    path('like-post/<int:post_id>/', views.like_post, name='like_post'),
    path('follow-user/<int:user_id>/', views.follow_user, name='follow_user'),
    path('followed-posts/', views.followed_posts, name='followed_posts'),
    path('toggle-dark-mode/', views.toggle_dark_mode, name='toggle_dark_mode'),
    path('play-song-preview/<str:track_id>/', views.play_song_preview, name='play_song_preview'),
    path('logout/', views.logout_view, name='logout'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path("create-wrap/<str:term>", views.create_wrap, name="create_wrap"),
]
