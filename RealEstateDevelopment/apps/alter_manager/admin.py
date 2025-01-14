from django.contrib import admin
from .models import CulturalEvent, CulturalFacility, CrimeRate

@admin.register(CulturalEvent)
class CulturalEventAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'start_date', 'end_date')
    list_filter = ('district', 'start_date', 'end_date')
    search_fields = ('name', 'district', 'description')
    ordering = ('-start_date', 'district')

@admin.register(CulturalFacility)
class CulturalFacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'facility_type', 'district', 'address')
    list_filter = ('district', 'facility_type')
    search_fields = ('name', 'district', 'address')
    ordering = ('district', 'facility_type')

@admin.register(CrimeRate)
class CrimeRateAdmin(admin.ModelAdmin):
    list_display = ('district', 'year', 'crime_count', 'population', 'rate')
    list_filter = ('district', 'year')
    search_fields = ('district',)
    ordering = ('-year', 'district')