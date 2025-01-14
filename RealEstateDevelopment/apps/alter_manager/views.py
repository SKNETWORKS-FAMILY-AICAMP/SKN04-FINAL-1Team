from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import CulturalEvent, CulturalFacility, CrimeRate
from .serializers import (
    CulturalEventSerializer,
    CulturalFacilitySerializer,
    CrimeRateSerializer
)

class CulturalEventViewSet(viewsets.ModelViewSet):
    queryset = CulturalEvent.objects.all()
    serializer_class = CulturalEventSerializer

    @action(detail=False, methods=['get'])
    def by_district(self, request):
        district = request.query_params.get('district', None)
        if district:
            events = self.queryset.filter(district=district)
            serializer = self.get_serializer(events, many=True)
            return Response(serializer.data)
        return Response({'error': 'district parameter is required'}, status=400)

class CulturalFacilityViewSet(viewsets.ModelViewSet):
    queryset = CulturalFacility.objects.all()
    serializer_class = CulturalFacilitySerializer

    @action(detail=False, methods=['get'])
    def by_district(self, request):
        district = request.query_params.get('district', None)
        if district:
            facilities = self.queryset.filter(district=district)
            serializer = self.get_serializer(facilities, many=True)
            return Response(serializer.data)
        return Response({'error': 'district parameter is required'}, status=400)

class CrimeRateViewSet(viewsets.ModelViewSet):
    queryset = CrimeRate.objects.all()
    serializer_class = CrimeRateSerializer

    @action(detail=False, methods=['get'])
    def by_district(self, request):
        district = request.query_params.get('district', None)
        if district:
            crime_rates = self.queryset.filter(district=district)
            serializer = self.get_serializer(crime_rates, many=True)
            return Response(serializer.data)
        return Response({'error': 'district parameter is required'}, status=400)