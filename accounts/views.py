import requests
import os
import time
import uuid
import json
from django.shortcuts import redirect
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .models import *
from django.http import JsonResponse
from urllib.parse import urlencode
from django.conf import settings
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')    
    
    return render(request, 'home.html')

def generate_state():
    return str(uuid.uuid4())

# Login to Spotify, Spotify redirects to callback URI automatically
def spotify_login(request):
    state = generate_state()
    request.session.flush()
    request.session['spotify_auth_state'] = state
    spotify_auth_url = "https://accounts.spotify.com/authorize"
    
    params = {
        'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
        'response_type': 'code',
        'redirect_uri': os.getenv('SPOTIFY_REDIRECT_URI'),
        'scope': 'user-top-read user-read-email streaming user-read-private user-modify-playback-state',
        'state': state,
    }
    
    return redirect(f"{spotify_auth_url}?{urlencode(params)}")

# Spotify will redirect here after user login
def spotify_callback(request):
    #print("Entered spotify_callback")
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
    #print("Token Data:", token_data)

    if 'scope' in token_data:
        print("Token scopes:", token_data['scope'])
    else:
        print("Scope field missing in token response")

    if 'access_token' in token_data:
        access_token = token_data['access_token']
        request.session['spotify_access_token'] = access_token

        user_info_url = "https://api.spotify.com/v1/me"
        headers = {
            'Authorization': f'Bearer {access_token}',
        }
        user_info_response = requests.get(user_info_url, headers=headers)
        user_info = user_info_response.json()
        #print("User Info:", user_info)

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

def get_access_token(request):
    access_token = request.session.get('spotify_access_token')
    if not access_token:
        return JsonResponse({'error': 'Spotify access token missing'}, status=401)
    return access_token

@login_required
def dashboard(request):
    access_token = request.session.get('spotify_access_token')
    if not access_token:
        return JsonResponse({'error': 'Spotify access token missing'}, status=401)

    top_artists = get_top_artists(access_token)
    top_genres = get_top_genres(access_token)
    top_tracks = get_user_top_tracks(access_token)
    user_wraps = Wrap.objects.all().filter(user=request.user)
    wraps = []
    for i in range(len(user_wraps)):
        wraps.append({"overview": user_wraps[i], "top_tracks": user_wraps[i].top_tracks.all(), "top_artists": user_wraps[i].top_artists.all()})

    context = {
        'top_artists': top_artists,
        'top_genres': top_genres,
        'top_tracks': top_tracks,
        'access_token': access_token,
        'wraps': wraps,
    }

    if request.method == "POST":
        #print("TIMEFRAME SELECT", request.POST.get("timeframe_select"))
        create_wrap(access_token, request.POST.get("timeframe_select"), request.user)
        return redirect("/dashboard/")

    return render(request, 'dashboard.html', context)

def create_wrap(access_token, time_frame, user):
    top_artists = get_top_artists(access_token, time_frame=time_frame)
    #print("TOP ARTISTS WRAP\n", top_artists, "\n")
    top_genres = get_top_genres(access_token, time_frame=time_frame)
    #print("TOP GENRES WRAP\n", top_genres, "\n")
    top_tracks = get_user_top_tracks(access_token, time_range=time_frame)
    #print("TOP TRACKS WRAP\n", top_tracks, "\n")

    tempWrap = Wrap(user=user, title="My Wrap", top_genres=str(top_genres))
    tempWrap.save()

    for i in top_artists:
        tempArtist, created = Artist.objects.get_or_create(name=i['name'])
        tempArtist.image_url = i['image_url']
        tempArtist.save()
        tempWrap.top_artists.add(tempArtist)
    for i in top_tracks:
        print(i['name'])
        artist, created = Artist.objects.get_or_create(name=i['artist'])
        tempSong, created = Song.objects.get_or_create(name=i['name'], artist=artist, album=i['album'], preview_url=i['preview_url'], album_cover_url=i['album_cover_url'])
        tempWrap.top_tracks.add(tempSong)

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

def get_top_artists(access_token, time_frame="medium_term"):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    params = {
        'limit': 10,
        'time_range': time_frame,
    }

    response = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        top_artists = [{
            'name': artist['name'],
            'image_url': artist['images'][0]['url'] if artist['images'] else None
        } for artist in data.get('items', [])]
        return top_artists
    else:
        print("Error fetching top artists:", response.json())
        return []

def get_top_genres(access_token, time_frame="medium_term"):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    params = {
        'limit': 50,
        'time_range': time_frame,
    }

    response = requests.get('https://api.spotify.com/v1/me/top/artists', headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        top_genres = list({genre for artist in data.get('items', []) for genre in artist.get('genres', [])})
        return top_genres
    else:
        print("Error fetching top genres:", response.json())
        return []

@require_GET
@login_required
def fetch_top_tracks(request):
    access_token = request.session.get('spotify_access_token')
    if not access_token:
        return JsonResponse({'error': 'Spotify access token missing'}, status=401)

    time_frame = request.GET.get('time_frame', 'medium_term')
    top_tracks = get_user_top_tracks(access_token, limit=15, time_range=time_frame)

    return JsonResponse({'top_tracks': top_tracks})

def about(request):
    context = {"access_token": request.session.get('spotify_access_token')}
    return render(request, 'about.html', context)

def get_user_top_tracks(access_token, limit=15, time_range='medium_term'):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    params = {
        'limit': limit,
        'time_range': time_range,
    }

    response = requests.get('https://api.spotify.com/v1/me/top/tracks', headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        top_tracks = [{
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'preview_url': track.get('preview_url'),
            'album_cover_url': track['album']['images'][0]['url'] if track['album']['images'] else None
        } for track in data.get('items', [])]
        return top_tracks
    else:
        print("Error fetching top tracks:", response.json())
        return []
