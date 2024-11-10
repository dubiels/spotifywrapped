from django.contrib import admin
from .models import Account, SpotifyListeningData, SpotifyWrapHistory, PublicWrapPost, UserSettings, Feedback

admin.site.register(Account)
admin.site.register(SpotifyListeningData)
admin.site.register(SpotifyWrapHistory)
admin.site.register(PublicWrapPost)
admin.site.register(UserSettings)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'rating', 'created_at')