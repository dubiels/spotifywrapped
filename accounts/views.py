import requests
import os
import uuid
from django.shortcuts import redirect
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .models import *
from django.http import JsonResponse
from urllib.parse import urlencode

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')    
    
    return render(request, 'home.html')

def generate_state():
    return str(uuid.uuid4())

def spotify_login(request):
    state = generate_state()
    request.session['spotify_auth_state'] = state
    spotify_auth_url = "https://accounts.spotify.com/authorize"
    
    params = {
        'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
        'response_type': 'code',
        'redirect_uri': os.getenv('SPOTIFY_REDIRECT_URI'),
        'scope': 'user-read-email',
        'state': state,
    }
    
    return redirect(f"{spotify_auth_url}?{urlencode(params)}")

def spotify_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')

    if state != request.session.get('spotify_auth_state'):
        return JsonResponse({'error': 'State mismatch'}, status=400)

    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': os.getenv('SPOTIFY_REDIRECT_URI'),
        'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
        'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET'),
    }

    response = requests.post(token_url, data=payload)
    token_data = response.json()

    if 'access_token' in token_data:
        access_token = token_data['access_token']

        request.session['spotify_access_token'] = access_token

        user_info_url = "https://api.spotify.com/v1/me"
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info = user_info_response.json()

        spotify_email = user_info.get('email')
        spotify_username = user_info.get('id')
        spotify_first_name = user_info.get('display_name', '').split(' ')[0] or 'SpotifyUser'
        spotify_last_name = user_info.get('display_name', '').split(' ')[-1] or 'User'

        user, created = Account.objects.get_or_create(
            email=spotify_email,
            defaults={
                'username': spotify_username,
                'first_name': spotify_first_name,
                'last_name': spotify_last_name,
                'is_active': True,
            }
        )

        login(request, user)

        return redirect('dashboard')
    else:
        return JsonResponse({'error': 'Failed to authenticate with Spotify', 'details': token_data}, status=400)

def get_user_top_tracks(request):
    access_token = request.session.get('spotify_access_token')
    if not access_token:
        return JsonResponse({'error': 'No access token available'}, status=400)
    
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get('https://api.spotify.com/v1/me/top/tracks', headers=headers)
    
    if response.status_code == 200:
        top_tracks = response.json()
        return JsonResponse(top_tracks)
    else:
        return JsonResponse({'error': 'Failed to fetch top tracks'}, status=400)

@login_required
def dashboard(request):
    spotify_data = SpotifyListeningData.objects.filter(user=request.user)
    full_name = request.user.full_name()
    return render(request, 'dashboard.html', {'spotify_data': spotify_data, 'full_name': full_name})

@login_required
def past_wraps(request):
    past_wraps = SpotifyWrapHistory.objects.filter(user=request.user)
    return render(request, 'past_wraps.html', {'past_wraps': past_wraps})

@login_required
def wrap_detail(request, wrap_id):
    wrap = SpotifyWrapHistory.objects.get(id=wrap_id, user=request.user)
    return render(request, 'wrap_detail.html', {'wrap': wrap})

def logout_view(request):
    logout(request)
    request.session.flush()
    return render(request, 'logout.html')

@login_required
def delete_account(request):
    if request.method == 'POST':
        request.user.delete()
        return redirect('signup')
    return render(request, 'delete_account.html')

@login_required
def play_song_preview(request, track_id):
    spotify_data = SpotifyListeningData.objects.filter(user=request.user, spotify_id=track_id).first()
    if not spotify_data or not spotify_data.preview_url:
        return JsonResponse({'error': 'Preview unavailable'}, status=400)

    return JsonResponse({'preview_url': spotify_data.preview_url})

@login_required
def like_post(request, post_id):
    post = get_object_or_404(PublicWrapPost, id=post_id)
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return JsonResponse({'likes_count': post.total_likes()})

@login_required
def follow_user(request, user_id):
    user_to_follow = get_object_or_404(Account, id=user_id)
    if request.user != user_to_follow:
        if request.user.following_posts.filter(id=user_to_follow.id).exists():
            request.user.following_posts.remove(user_to_follow)
        else:
            request.user.following_posts.add(user_to_follow)
    return redirect('some_view')

@login_required
def followed_posts(request):
    followed_users = request.user.following_posts.all()
    posts = PublicWrapPost.objects.filter(user__in=followed_users)
    
    posts_with_names = []
    for post in posts:
        posts_with_names.append({
            'post': post,
            'full_name': post.user.full_name()
        })
        
    return render(request, 'followed_posts.html', {'followed_posts': posts_with_names})

@login_required
def toggle_dark_mode(request):
    settings, created = UserSettings.objects.get_or_create(user=request.user)
    settings.toggle_dark_mode()
    
    return JsonResponse({'dark_mode': settings.dark_mode})
