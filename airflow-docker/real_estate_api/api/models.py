from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# Create your models here.

class Address(models.Model):
    id = models.AutoField(primary_key=True)
    area_name = models.CharField(max_length=100)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'addresses'
        managed = True

class CulturalFacility(models.Model):
    id = models.AutoField(primary_key=True)
    address = models.ForeignKey(Address, on_delete=models.CASCADE, db_column='address_id')
    facility_name = models.CharField(max_length=255)
    facility_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'cultural_facilities'
        managed = True

class CulturalFestival(models.Model):
    id = models.AutoField(primary_key=True)
    address = models.ForeignKey(Address, on_delete=models.CASCADE, db_column='address_id')
    festival_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'cultural_festivals'
        managed = True

class PropertyLocation(models.Model):
    property_id = models.BigIntegerField(primary_key=True)
    sido = models.CharField(max_length=50)
    sigungu = models.CharField(max_length=50)
    dong = models.CharField(max_length=50, null=True)
    jibun_main = models.CharField(max_length=20)
    jibun_sub = models.CharField(max_length=20, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True)

    class Meta:
        db_table = 'property_locations'
        managed = True

class PropertyInfo(models.Model):
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    property_id = models.BigIntegerField(unique=True)
    property_type = models.CharField(max_length=50)
    property_subtype = models.CharField(max_length=50)
    building_name = models.CharField(max_length=100, null=True, blank=True)
    detail_address = models.CharField(max_length=200, null=True, blank=True)
    construction_date = models.CharField(max_length=10, null=True, blank=True)
    total_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    exclusive_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    land_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    on_floor = models.IntegerField(null=True, blank=True)
    under_floor = models.IntegerField(null=True, blank=True)
    room_count = models.IntegerField(null=True, blank=True)
    bathroom_count = models.IntegerField(null=True, blank=True)
    parking_count = models.IntegerField(null=True, blank=True)
    heating_type = models.CharField(max_length=50, null=True, blank=True)
    direction = models.CharField(max_length=50, null=True, blank=True)
    purpose_type = models.CharField(max_length=50, null=True, blank=True)
    current_usage = models.CharField(max_length=100, null=True, blank=True)
    recommended_usage = models.CharField(max_length=100, null=True, blank=True)
    facilities = models.JSONField(default=dict, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    move_in_type = models.CharField(max_length=50, null=True, blank=True)
    move_in_date = models.CharField(max_length=10, null=True, blank=True)
    loan_availability = models.CharField(max_length=50, null=True, blank=True)
    negotiable = models.CharField(max_length=2, default='N')
    photos = models.JSONField(default=dict)
    update_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    inactive_reason = models.CharField(max_length=200, null=True, blank=True)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'property_info'
        managed = True

class Rental(models.Model):
    property_id = models.BigIntegerField(primary_key=True)
    rental_type = models.CharField(max_length=50)
    deposit = models.BigIntegerField(default=0)
    monthly_rent = models.BigIntegerField(default=0)

    class Meta:
        db_table = 'rentals'
        managed = True

class Sale(models.Model):
    property_id = models.BigIntegerField(primary_key=True)
    price = models.BigIntegerField(default=0)
    end_date = models.CharField(max_length=10, null=True)
    transaction_date = models.CharField(max_length=10, null=True)

    class Meta:
        db_table = 'sales'
        managed = True

class User(AbstractUser):
    nickname = models.CharField(max_length=50, unique=True)
    profile_image = models.CharField(max_length=200, null=True)
    gender = models.CharField(max_length=1, choices=[('M', '남성'), ('F', '여성'), ('O', '기타')], null=True)
    age = models.IntegerField(null=True)
    last_login_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Add related_name to avoid clash with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta:
        db_table = 'users'
        managed = True

class Chat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100, default='default_session')
    message_type = models.CharField(max_length=10, choices=[('user', '사용자'), ('bot', '봇')], default='user')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chats'
        managed = True

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback_text = models.TextField()
    homepage_rating = models.IntegerField(default=3)
    q1_accuracy = models.IntegerField(default=3)
    q2_naturalness = models.IntegerField(default=3)
    q3_resolution = models.IntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'feedbacks'
        managed = True

class Notice(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notices'
        managed = True

class UserLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=50)
    action_detail = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_logs'
        managed = True

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey('PropertyInfo', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'favorites'
        unique_together = ('user', 'property')
        managed = True

class CrimeStats(models.Model):
    id = models.AutoField(primary_key=True)
    address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name='crime_stats', db_column='address_id')
    reference_date = models.DateField()
    total_crime_count = models.IntegerField()
    violent_crime_count = models.IntegerField()
    theft_crime_count = models.IntegerField()
    intellectual_crime_count = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'crime_stats'
        managed = True

class Subway(models.Model):
    id = models.AutoField(primary_key=True)
    address = models.ForeignKey(Address, on_delete=models.CASCADE, db_column='address_id')
    line_info = models.CharField(max_length=50)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'subway_stations'
        managed = True

class LocationDistance(models.Model):
    id = models.AutoField(primary_key=True)
    property = models.ForeignKey(PropertyLocation, on_delete=models.CASCADE, db_column='property_id')
    address = models.ForeignKey(Address, on_delete=models.CASCADE, db_column='address_id')
    distance = models.FloatField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'location_distances'
        managed = True
        indexes = [
            models.Index(fields=['property']),
            models.Index(fields=['address'])
        ]
