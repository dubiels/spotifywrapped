from django.db import models
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db.models.signals import post_save
from django.dispatch import receiver

class AccountManager(BaseUserManager):
    def create_user(self, email, username, first_name, last_name, password=None):
        if not email:
            raise ValueError('The Email field is required')
        if not username:
            raise ValueError('The Username field is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, first_name=first_name, last_name=last_name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, first_name, last_name, password=None):
        user = self.create_user(email, username, first_name, last_name, password)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class Account(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    friends = models.ManyToManyField("self", blank=True, symmetrical=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = AccountManager()

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.email

@receiver(post_save, sender=Account)
def create_user_settings(sender, instance, created, **kwargs):
    if created:
        UserSettings.objects.create(user=instance)

class SpotifyListeningData(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    track_name = models.CharField(max_length=255)
    artist_name = models.CharField(max_length=255)
    album_name = models.CharField(max_length=255)
    played_at = models.DateTimeField()
    duration_ms = models.IntegerField()
    spotify_id = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.track_name} by {self.artist_name}"

class SpotifyWrapHistory(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    wrap_title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField()
    
    def __str__(self):
        return f"{self.wrap_title} for {self.user.email} on {self.created_at}"

class PublicWrapPost(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    wrap_history = models.ForeignKey(SpotifyWrapHistory, on_delete=models.CASCADE)
    is_public = models.BooleanField(default=True)
    likes = models.ManyToManyField(Account, related_name='liked_posts', blank=True)
    followers = models.ManyToManyField(Account, related_name='following_posts', blank=True)

    def total_likes(self):
        return self.likes.count()

    def __str__(self):
        return f"{self.user.email}'s wrap - {'Public' if self.is_public else 'Private'}"

class UserSettings(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    dark_mode = models.BooleanField(default=False)
    selected_theme = models.CharField(max_length=50, default="default")

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.save()

    def change_theme(self, theme_name):
        self.selected_theme = theme_name
        self.save()

    def __str__(self):
        return f"{self.user.email} settings"
    
class Artist(models.Model):
    name = models.CharField(max_length=200)
    image_url = models.CharField(max_length=400)

    def __str__(self):
        return f"{self.name}"

class Song(models.Model):
    name = models.CharField(max_length=200)
    artist = models.ForeignKey(Artist, default="None", on_delete=models.SET_DEFAULT)
    album = models.CharField(max_length=200)
    preview_url = models.CharField(max_length=400)
    album_cover_url = models.CharField(max_length=400)

    def __str__(self):
        return f"NAME: {self.name} ARTIST: {self.artist.name} ALBUM: {self.album}"

class Wrap(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    top_tracks = models.ManyToManyField(Song)
    top_artists = models.ManyToManyField(Artist)

    # Comma separated values
    top_genres = models.CharField(max_length=2000)

    def __str__(self):
        return f"{self.user.email}'s Wrap {self.title} created at: {self.created_at}"

class Feedback(models.Model):
    text = models.TextField()
    rating = models.PositiveSmallIntegerField(default=0) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback {self.id} - Rating: {self.rating}"
    
