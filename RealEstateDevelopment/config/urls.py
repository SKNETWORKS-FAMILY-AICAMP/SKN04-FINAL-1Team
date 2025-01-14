from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.alter_manager.views import (
    CulturalEventViewSet,
    CulturalFacilityViewSet,
    CrimeRateViewSet
)

router = DefaultRouter()
router.register(r'cultural-events', CulturalEventViewSet)
router.register(r'cultural-facilities', CulturalFacilityViewSet)
router.register(r'crime-rates', CrimeRateViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
] 