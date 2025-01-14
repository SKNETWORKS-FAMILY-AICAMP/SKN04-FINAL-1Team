from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SubwayStationViewSet

router = DefaultRouter()
router.register(r'subway-stations', SubwayStationViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 