from rest_framework import serializers
from .models import CulturalEvent, CulturalFacility, CrimeRate

class CulturalEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CulturalEvent
        fields = ['id', 'name', 'district', 'start_date', 'end_date', 'description']

class CulturalFacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = CulturalFacility
        fields = ['id', 'name', 'facility_type', 'district', 'address', 'latitude', 'longitude']

class CrimeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrimeRate
        fields = ['id', 'district', 'year', 'crime_count', 'rate']