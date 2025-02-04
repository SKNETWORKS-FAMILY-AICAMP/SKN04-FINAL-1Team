from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Address, CulturalFacility, PropertyLocation, PropertyInfo,
    Rental, Sale, Chat, Feedback, Notice, UserLog, Favorite,
    CrimeStats, Subway, LocationDistance
)
from .forms import CustomUserCreationForm

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    model = User
    list_display = ('username', 'email', 'nickname', 'is_staff', 'is_active',)
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('nickname',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('nickname',)}),
    )

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('area_name', 'latitude', 'longitude', 'created_at')
    search_fields = ('area_name',)
    ordering = ('-created_at',)

@admin.register(CulturalFacility)
class CulturalFacilityAdmin(admin.ModelAdmin):
    list_display = ('facility_name', 'facility_type', 'created_at')
    search_fields = ('facility_name', 'facility_type')
    list_filter = ('facility_type',)
    ordering = ('-created_at',)

@admin.register(PropertyLocation)
class PropertyLocationAdmin(admin.ModelAdmin):
    list_display = ('property_id', 'sido', 'sigungu', 'dong', 'jibun_main', 'jibun_sub', 'latitude', 'longitude')
    search_fields = ('property_id', 'sido', 'sigungu', 'dong', 'jibun_main', 'jibun_sub')
    list_filter = ('sido', 'sigungu', 'dong')
    ordering = ('sido', 'sigungu', 'dong', 'property_id')
    list_per_page = 50  # 페이지당 표시할 항목 수

@admin.register(PropertyInfo)
class PropertyInfoAdmin(admin.ModelAdmin):
    list_display = ('property_id', 'property_type', 'property_subtype', 'building_name', 'total_area', 'exclusive_area', 'is_active')
    list_filter = ('property_type', 'property_subtype', 'is_active')
    search_fields = ('property_id__property_id', 'building_name', 'detail_address')
    ordering = ('-last_seen',)
    list_per_page = 50

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('property_id', 'rental_type', 'deposit', 'monthly_rent')
    search_fields = ('property_id__property_id__property_id',)
    list_filter = ('rental_type',)

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('property_id', 'price', 'transaction_date')
    search_fields = ('property_id__property_id__property_id',)

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_id', 'message_type', 'message', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'session_id', 'message')
    readonly_fields = ('created_at',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'feedback_text', 'homepage_rating', 'q1_accuracy', 'q2_naturalness', 'q3_resolution', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'feedback_text')
    readonly_fields = ('created_at',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at', 'updated_at')
    search_fields = ('title', 'content')
    list_filter = ('is_active',)
    ordering = ('-created_at',)

@admin.register(UserLog)
class UserLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'created_at')
    search_fields = ('user__username', 'action_type')
    list_filter = ('action_type',)
    ordering = ('-created_at',)

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'property', 'created_at')
    search_fields = ('user__username', 'property__property_id__property_id')
    ordering = ('-created_at',)

@admin.register(CrimeStats)
class CrimeStatsAdmin(admin.ModelAdmin):
    list_display = ('address', 'reference_date', 'total_crime_count', 'violent_crime_count', 'theft_crime_count', 'intellectual_crime_count')
    list_filter = ('reference_date',)
    search_fields = ('address__area_name',)
    ordering = ('-reference_date',)

@admin.register(Subway)
class SubwayAdmin(admin.ModelAdmin):
    list_display = ('line_info', 'address', 'created_at')
    search_fields = ('line_info', 'address__area_name')
    list_filter = ('line_info',)
    ordering = ('line_info', 'created_at')

@admin.register(LocationDistance)
class LocationDistanceAdmin(admin.ModelAdmin):
    list_display = ('property', 'address', 'distance')
    search_fields = ('property__id', 'address__area_name')
    ordering = ('distance',)

# Register User model with custom admin class
admin.site.register(User, CustomUserAdmin)
