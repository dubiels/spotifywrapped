from rest_framework import serializers
from .models import SpotifyListeningData, SpotifyWrapHistory

class SpotifyListeningDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpotifyListeningData
        fields = '__all__'

class SpotifyWrapHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SpotifyWrapHistory
        fields = '__all__'