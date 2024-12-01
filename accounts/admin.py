from django.contrib import admin
from .models import Account, SpotifyListeningData, SpotifyWrapHistory, PublicWrapPost, UserSettings, Feedback, Artist, Song, Wrap, Post, Genre

admin.site.register(Account)
admin.site.register(SpotifyListeningData)
admin.site.register(SpotifyWrapHistory)
admin.site.register(PublicWrapPost)
admin.site.register(UserSettings)
admin.site.register(Artist)
admin.site.register(Song)
admin.site.register(Wrap)
admin.site.register(Post)
admin.site.register(Genre)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'rating', 'created_at')