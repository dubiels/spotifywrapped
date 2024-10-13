from django.contrib import admin
from .models import Account, SpotifyListeningData, SpotifyWrapHistory, PublicWrapPost, UserSettings

admin.site.register(Account)
admin.site.register(SpotifyListeningData)
admin.site.register(SpotifyWrapHistory)
admin.site.register(PublicWrapPost)
admin.site.register(UserSettings)
