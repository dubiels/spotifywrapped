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
from django.http import JsonResponse, HttpResponseRedirect
from urllib.parse import urlencode
from django.conf import settings
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from .forms import FeedbackForm
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from datetime import timedelta
from django.http import Http404


def home(request):
    access_token = request.session.get('spotify_access_token')

    if request.user.is_authenticated and access_token:
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
    
    force_show_dialog = request.user.is_authenticated

    params = {
        'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
        'response_type': 'code',
        'redirect_uri': os.getenv('SPOTIFY_REDIRECT_URI'),
        'scope': 'user-top-read user-read-email streaming user-read-private user-modify-playback-state',
        'state': state,
    }

    if not request.user.is_authenticated:  # User is not authenticated, show dialog
        params['show_dialog'] = 'true'
    else:  # User is already authenticated, no need to show dialog
        params['show_dialog'] = 'false'
    
    return redirect(f"{spotify_auth_url}?{urlencode(params)}")

# Spotify will redirect here after user login
def spotify_callback(request):
    code = request.GET.get('code')
    state = request.GET.get('state')

    # Debug State
    print("Session State (stored):", request.session.get('spotify_auth_state'))
    print("Callback State (received):", state)

    if state != request.session.get('spotify_auth_state'):
        return JsonResponse({'error': 'State mismatch'}, status=400)
    
    if not code:
        print("User cancelled the login. Redirecting to home.")
        return redirect('home')
    
    # Token Exchange
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': os.getenv('SPOTIFY_REDIRECT_URI'),
        'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
        'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET'),
    }
    response = requests.post(token_url, data=payload)

    # Log Token Response
    print("Token Response Status Code:", response.status_code)
    print("Token Response Content:", response.text)

    try:
        token_data = response.json()
    except ValueError:
        return JsonResponse({'error': 'Invalid token response from Spotify'}, status=500)

    access_token = token_data.get('access_token')
    if not access_token:
        return JsonResponse({'error': 'Failed to fetch access token', 'details': token_data}, status=400)

    # Fetch User Info
    user_info_url = "https://api.spotify.com/v1/me"
    headers = {'Authorization': f'Bearer {access_token}'}
    user_info_response = requests.get(user_info_url, headers=headers)

    print("User Info Response Status Code:", user_info_response.status_code)
    print("User Info Response Content:", user_info_response.text)

    try:
        user_info = user_info_response.json()
    except ValueError:
        print("User Info Response (raw):", user_info_response.text)
        return JsonResponse({'error': 'Invalid user info response from Spotify'}, status=500)

    # Extract User Data
    spotify_email = user_info.get('email') or f"user_{uuid.uuid4().hex[:8]}@example.com"
    spotify_username = user_info.get('id') or f"user_{uuid.uuid4().hex[:8]}"
    spotify_first_name = user_info.get('display_name', '').split(' ')[0] or 'SpotifyUser'
    spotify_last_name = user_info.get('display_name', '').split(' ')[-1] or 'User'

    # Create or Fetch User
    user, created = Account.objects.get_or_create(
        email=spotify_email,
        defaults={
            'username': spotify_username,
            'first_name': spotify_first_name,
            'last_name': spotify_last_name,
            'is_active': True,
        }
    )

    # Handle Username Conflicts
    if not created and user.username != spotify_username:
        print("Username conflict detected. Generating a new unique username.")
        username = spotify_username
        while Account.objects.filter(username=username).exists():
            username = f"{spotify_username}_{uuid.uuid4().hex[:8]}"
        user.username = username
        user.save()

    # Login the User
    login(request, user)
    request.session['spotify_access_token'] = access_token
    return redirect('dashboard')

def get_access_token(request):
    access_token = request.session.get('spotify_access_token')
    if not access_token:
        return JsonResponse({'error': 'Spotify access token missing'}, status=401)
    return access_token

@login_required
def dashboard(request):
    access_token = request.session.get('spotify_access_token')
    
    if not access_token:
        print("Access token missing. Redirecting to Spotify login.")
        return spotify_login(request)

    if request.method == "POST" and "delete_friend_id" in request.POST:
        friend_id = request.POST.get("delete_friend_id")
        friend = Account.objects.filter(id=friend_id).first()
        if friend and friend in request.user.friends.all():
            request.user.friends.remove(friend)
            print(f"Friend {friend.username} removed successfully.")

    top_artists = get_top_artists(access_token)
    top_genres = get_top_genres(access_token)
    top_tracks = get_user_top_tracks(access_token)
    user_wraps = Wrap.objects.all().filter(user=request.user)
    wraps = []

    for wrap in user_wraps:
        wraps.append({
            "overview": wrap,
            "top_tracks": wrap.top_tracks.all(),
            "top_artists": wrap.top_artists.all(),
            "top_genres": wrap.top_genres.all(),  # This is now a queryset of Genre objects
        })

    # print("Wraps:", wraps)

    if request.method == "POST":
        if "delete_wrap" in request.POST:
            wrap_id = request.POST.get("wrap_id")
            Wrap.objects.filter(id=wrap_id, user=request.user).delete()
            return redirect("dashboard")

    friends = request.user.friends.all()

    context = {
        'top_artists': top_artists,
        'top_genres': top_genres,
        'top_tracks': top_tracks,
        'access_token': access_token,
        'wraps': wraps,
        'friends': friends,
        'invalid_username': False,
    }

    if request.method == "POST":
        if "timeframe_select" in request.POST.keys():
            create_wrap(access_token, request.POST.get("timeframe_select"), request.user, request.POST.get("new_wrap_name"))
            return redirect("/dashboard/")
        if "friend_name" in request.POST.keys() and request.POST.get("friend_name") != "":
            valid_friend = add_friend(request.POST.get("friend_name"), request.user)
            if valid_friend:
                return redirect("/dashboard/")
            else:
                return redirect("/dashboard/")
                context["invalid_username"] = True

    return render(request, 'dashboard.html', context)

def create_wrap(access_token, time_frame, user, title="My Wrap"):
    top_artists = get_top_artists(access_token, time_frame=time_frame)
    top_genres = get_top_genres(access_token, time_frame=time_frame)
    top_tracks = get_user_top_tracks(access_token, time_range=time_frame)

    if not top_artists or not top_genres or not top_tracks:
        raise ValueError("You don't have enough data to create a wrap.")
    
    # Create the wrap instance
    tempWrap = Wrap(user=user, title=title)
    tempWrap.save()

    # Add genres to the wrap
    for genre in top_genres:
        tempGenre, created = Genre.objects.get_or_create(name=genre)
        tempWrap.top_genres.add(tempGenre)
        print(f"Added Genre: {tempGenre.name} to Wrap: {tempWrap.title}")  # Debugging log

    # Add artists to the wrap
    for artist_data in top_artists:
        tempArtist, created = Artist.objects.get_or_create(name=artist_data['name'])
        tempArtist.image_url = artist_data.get('image_url', '')
        tempArtist.save()
        tempWrap.top_artists.add(tempArtist)

    # Add tracks to the wrap
    for track_data in top_tracks:
        artist, created = Artist.objects.get_or_create(name=track_data['artist'])
        tempSong, created = Song.objects.get_or_create(
            name=track_data['name'],
            artist=artist,
            album=track_data['album'],
            preview_url=track_data.get('preview_url', 'No URL'),
            album_cover_url=track_data.get('album_cover_url', '')
        )
        tempWrap.top_tracks.add(tempSong)

    # Save the wrap with all associated data
    tempWrap.save()

    return tempWrap

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

    spotify_logout_url = "https://accounts.spotify.com/logout"

    return render(request, 'logout.html', {
        'spotify_logout_url': spotify_logout_url,
        'redirect_url': 'home',
    })

@login_required
def delete_account(request):
    if request.method == 'POST':
        username = request.user.username

        logout(request)
        request.user.delete()

        messages.success(request, f"Your account '{username}' has been deleted successfully.")

        return redirect(spotify_login)

    return render(request, 'delete_account.html')

@login_required
def like_post(request, post_id):
    post = get_object_or_404(PublicWrapPost, id=post_id)
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return JsonResponse({'likes_count': post.total_likes()})

# @login_required
# def follow_user(request, user_id):
#     user_to_follow = get_object_or_404(Account, id=user_id)
#     if request.user != user_to_follow:
#         if request.user.following_posts.filter(id=user_to_follow.id).exists():
#             request.user.following_posts.remove(user_to_follow)
#         else:
#             request.user.following_posts.add(user_to_follow)
#     return redirect('some_view')

# @login_required
# def followed_posts(request):
#     followed_users = request.user.following_posts.all()
#     posts = PublicWrapPost.objects.filter(user__in=followed_users)
    
#     posts_with_names = []
#     for post in posts:
#         posts_with_names.append({
#             'post': post,
#             'full_name': post.user.full_name()
#         })
        
#     return render(request, 'followed_posts.html', {'followed_posts': posts_with_names})

@login_required
def toggle_dark_mode(request):
    print("Toggle Dark Mode view called!")  # Debug
    settings, created = UserSettings.objects.get_or_create(user=request.user)
    settings.toggle_dark_mode()
    print(f"Dark mode toggled: {settings.dark_mode}")  # Debug
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
        print("Fetched Genres:", top_genres)
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
    access_token = request.session.get('spotify_access_token')
    
    if not access_token:
        print("Access token missing. Redirecting to Spotify login.")
        return spotify_login(request, force_show_dialog=False)
    
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

def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()

            # Check if the user is logged in before sending the email
            if request.user.is_authenticated:
                send_mail(
                    subject="Feedback Form Submission",
                    message="Feedback form sent to your Spotify Email Address! Thank you so much.",
                    from_email="esther514514@gmail.com",
                    recipient_list=[request.user.email],
                    fail_silently=False,
                )
                print(f"Email sent to {request.user.email}")
            
            # Redirect to the 'about' page with a submission success flag
            return HttpResponseRedirect('/about/?submitted=true')
        else:
            print("Form is invalid:", form.errors)
    else:
        form = FeedbackForm()
    
    return render(request, 'about.html', {'form': form})

def add_friend(friend_name, user):
    new_friend = Account.objects.filter(username=friend_name)
    if not new_friend:
        return False

    user.friends.add(new_friend[0])
    return

def single_post(request, id):
    #post_id = request.GET.get("id")
    posts = Post.objects.filter(id=id)
    if not posts.exists():
        raise Http404("Post not found")
    
    post = posts[0]
    wrap = post.wrap
    
    print(wrap)
    print(type(wrap))
    print("SINGLE WRAP TOP TRACKS", wrap.top_tracks, wrap.top_artists, wrap.top_genres)

    if request.method == "POST":
        # Handle the delete request
        if "delete_wrap" in request.POST:
            wrap_id = request.POST.get("wrap_id")
            print(f"Request to delete Wrap ID: {wrap_id}")

            # Verify that the wrap to be deleted matches the wrap associated with the post
            if str(wrap.id) == wrap_id:
                wrap.delete()
                print(f"Wrap ID {wrap_id} deleted successfully.")
                return redirect("friends")  # Redirect to the dashboard or another appropriate page
            else:
                print(f"Wrap ID mismatch: {wrap_id} does not match Wrap ID {wrap.id}")

    context = {
        "wrap": wrap,
        "post": post,
    }
    return render(request, "single_post.html", context)

@login_required
def friends(request):
    access_token = request.session.get('spotify_access_token')
    if not access_token:
        print("Access token missing. Redirecting to Spotify login.")
        return spotify_login(request)
    # Retrieve all posts
    all_posts = Post.objects.all().order_by('-created_at')
    # Handle filters
    filter_value = request.GET.get("filter", "all")
    if filter_value == "liked":
        posts = all_posts.filter(liked_by=request.user)
    elif filter_value == "recent":
        one_week_ago = now() - timedelta(days=7)
        posts = all_posts.filter(created_at__gte=one_week_ago)
    elif filter_value == "follow":
        # Only posts from friends
        friends = request.user.friends.all()
        posts = all_posts.filter(user__in=friends)
    else:
        # Default: show all posts
        posts = all_posts

    context = {
        "posts": posts,
        "user": request.user,
        "filter_val": filter_value,
    }

    if request.method == "POST":
        # Redirect to new post page for creating a new post
        if "experience" in request.POST.keys():
            post_id = request.POST.get("post_id")
            return redirect('single_post', id=post_id)
        elif "create_post" in request.POST.keys():
            return redirect("/new_post/")
        # Add the user to the liked by field of the post
        elif "favorite" in request.POST.keys():
            post_id = request.POST.get("post_id")
            print("POST ID:", post_id)
            liked_post = Post.objects.get(id=post_id)
            if liked_post.liked_by.filter(id=request.user.id).exists():
                liked_post.liked_by.remove(request.user)
                #print("removed", liked_post.liked_by.all())
            else:
                liked_post.liked_by.add(request.user)
                #print("added", liked_post.liked_by.all())
            return redirect("/friends/")

    return render(request, 'friends.html', context)


def new_post(request):
    user_wraps = request.user.wraps.all()
    print(user_wraps)
    context = {
        "wraps": user_wraps,
    }

    # If the user wants to create a new wrap
    if request.method == "POST":
        # Get the wrap by its name
        wrap_name = request.POST.get("wrap_name")
        wrap = Wrap.objects.all().filter(user=request.user, title=wrap_name)[0]
        
        # Check if a post already exists with this wrap
        for i in Post.objects.all():
            if wrap == i.wrap:
                return redirect("/friends/")

        # Create the post if it hasn't been created already
        tempPost = Post(user=request.user, wrap=wrap)
        tempPost.save()

        return redirect("/friends/")

    return render(request, 'new_post.html', context)

@login_required
def profile(request):
    access_token = request.session.get('spotify_access_token')
    if not access_token:
        print("Access token missing. Redirecting to Spotify login.")
        return spotify_login(request)
    
    if request.method == "POST" and "delete_account" in request.POST:
        user = request.user
        user.delete()
        return redirect("home")
    
    if request.method == "POST" and "logout" in request.POST:
        return logout_view(request)

    context = {
        "user": request.user,
    }
    return render(request, "profile.html", context)