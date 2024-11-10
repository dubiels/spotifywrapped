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
    path('logout/', views.logout_view, name='logout'),
    path('delete-account/', views.delete_account, name='delete_account'),
    path('top-artists/', views.get_top_artists, name='top_artists'),
    path('top-genres/', views.get_top_genres, name='top_genres'),
    path('fetch_top_tracks/', views.fetch_top_tracks, name='fetch_top_tracks'),
    path('about/', views.feedback_view, name='about'),
]
