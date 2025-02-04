from django.shortcuts import render
from rest_framework import viewsets, status, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.contrib.auth import login
from rest_framework.views import APIView
from .models import (
    Address, CulturalFacility, CulturalFestival, PropertyLocation, PropertyInfo, 
    Rental, Sale, User, Chat, Feedback, Notice, UserLog, Favorite,
    CrimeStats, Subway, LocationDistance
)
from .serializers import (
    AddressSerializer, CulturalFacilitySerializer, PropertyLocationSerializer,
    PropertyInfoSerializer, RentalSerializer, SaleSerializer,
    UserSerializer, UserLoginSerializer, ChatSerializer, FeedbackSerializer,
    NoticeSerializer, UserLogSerializer, FavoriteSerializer,
    CrimeStatsSerializer, SubwaySerializer, LocationDistanceSerializer,
    AddressDetailSerializer, UserRegistrationSerializer
)
from django.db import models

# Create your views here.

class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['area_name']
    search_fields = ['area_name']

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        address = self.get_object()
        serializer = AddressDetailSerializer(address)
        return Response(serializer.data)

class CulturalFacilityViewSet(viewsets.ModelViewSet):
    queryset = CulturalFacility.objects.all()
    serializer_class = CulturalFacilitySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['facility_type']

class PropertyLocationViewSet(viewsets.ModelViewSet):
    queryset = PropertyLocation.objects.all()
    serializer_class = PropertyLocationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['sido', 'sigungu', 'dong', 'property_id']

    @action(detail=False, methods=['get'])
    def by_property_id(self, request):
        property_id = request.query_params.get('property_id')
        if not property_id:
            return Response({"error": "property_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            property_location = self.queryset.get(property_id=property_id)
            serializer = self.get_serializer(property_location)
            return Response(serializer.data)
        except PropertyLocation.DoesNotExist:
            return Response({"error": "Property not found"}, status=status.HTTP_404_NOT_FOUND)

class PropertyInfoViewSet(viewsets.ModelViewSet):
    queryset = PropertyInfo.objects.all()
    serializer_class = PropertyInfoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['property_type', 'property_subtype', 'is_active', 'property_id']

    @action(detail=False, methods=['get'])
    def active_properties(self, request):
        active_properties = self.queryset.filter(is_active=True)
        serializer = self.get_serializer(active_properties, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_property_id(self, request):
        property_id = request.query_params.get('property_id')
        if not property_id:
            return Response({"error": "property_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            property_info = self.queryset.get(property_id=property_id)
            serializer = self.get_serializer(property_info)
            return Response(serializer.data)
        except PropertyInfo.DoesNotExist:
            return Response({"error": "Property not found"}, status=status.HTTP_404_NOT_FOUND)

class RentalViewSet(viewsets.ModelViewSet):
    queryset = Rental.objects.all()
    serializer_class = RentalSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['rental_type', 'property_id']

    @action(detail=False, methods=['get'])
    def price_range(self, request):
        min_deposit = request.query_params.get('min_deposit', 0)
        max_deposit = request.query_params.get('max_deposit')
        min_rent = request.query_params.get('min_rent', 0)
        max_rent = request.query_params.get('max_rent')

        queryset = self.queryset.filter(deposit__gte=min_deposit)
        if max_deposit:
            queryset = queryset.filter(deposit__lte=max_deposit)
        if min_rent:
            queryset = queryset.filter(monthly_rent__gte=min_rent)
        if max_rent:
            queryset = queryset.filter(monthly_rent__lte=max_rent)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_property_id(self, request):
        property_id = request.query_params.get('property_id')
        if not property_id:
            return Response({"error": "property_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            rental = self.queryset.get(property_id=property_id)
            serializer = self.get_serializer(rental)
            return Response(serializer.data)
        except Rental.DoesNotExist:
            return Response({"error": "Rental property not found"}, status=status.HTTP_404_NOT_FOUND)

class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['price', 'property_id']

    @action(detail=False, methods=['get'])
    def price_range(self, request):
        min_price = request.query_params.get('min_price', 0)
        max_price = request.query_params.get('max_price')

        queryset = self.queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_property_id(self, request):
        property_id = request.query_params.get('property_id')
        if not property_id:
            return Response({"error": "property_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            sale = self.queryset.get(property_id=property_id)
            serializer = self.get_serializer(sale)
            return Response(serializer.data)
        except Sale.DoesNotExist:
            return Response({"error": "Sale property not found"}, status=status.HTTP_404_NOT_FOUND)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username', 'nickname', 'gender']

    def get_queryset(self):
        # 일반 사용자는 자신의 정보만 볼 수 있음
        if not self.request.user.is_staff:
            return User.objects.filter(id=self.request.user.id)
        return User.objects.all()

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['session_id']

    def get_queryset(self):
        # 사용자는 자신의 채팅만 볼 수 있음
        return Chat.objects.filter(user=self.request.user).order_by('created_at')

    def perform_create(self, serializer):
        # 세션 ID가 없으면 새로 생성
        session_id = self.request.data.get('session_id', f'session_{timezone.now().timestamp()}')
        serializer.save(user=self.request.user, session_id=session_id)

    @action(detail=False, methods=['get'])
    def sessions(self, request):
        # 사용자의 채팅 세션 목록 조회
        sessions = Chat.objects.filter(user=request.user)\
            .values('session_id')\
            .annotate(
                message_count=models.Count('id'),
                last_message=models.Max('created_at')
            )\
            .order_by('-last_message')
        
        return Response(sessions)

    @action(detail=False, methods=['get'])
    def session_messages(self, request):
        # 특정 세션의 메시지 목록 조회
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({"error": "session_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        messages = self.get_queryset().filter(session_id=session_id)
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.all()  # 모든 공지사항을 가져오도록 수정
    serializer_class = NoticeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['title', 'content']

    def get_queryset(self):
        # 관리자는 모든 공지사항을 볼 수 있고, 일반 사용자는 활성화된 공지사항만 볼 수 있습니다
        if self.request.user.is_staff:
            return Notice.objects.all()
        return Notice.objects.filter(is_active=True)

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def toggle_active(self, request, pk=None):
        notice = self.get_object()
        notice.is_active = not notice.is_active
        notice.save()
        
        status_text = "활성화" if notice.is_active else "비활성화"
        return Response({
            "message": f"공지사항이 {status_text} 되었습니다.",
            "is_active": notice.is_active
        })

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # 관리자만 is_active를 수정할 수 있습니다
        if 'is_active' in request.data and not request.user.is_staff:
            return Response(
                {"error": "관리자만 공지사항의 활성화 상태를 변경할 수 있습니다."}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        self.perform_update(serializer)
        return Response(serializer.data)

class UserLogViewSet(viewsets.ModelViewSet):
    queryset = UserLog.objects.all()
    serializer_class = UserLogSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user', 'property']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_favorites(self, request):
        favorites = self.queryset.filter(user=request.user)
        serializer = self.get_serializer(favorites, many=True)
        return Response(serializer.data)

class CrimeStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CrimeStats.objects.select_related('address').all()
    serializer_class = CrimeStatsSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'reference_date': ['exact', 'gte', 'lte'],
        'address__area_name': ['exact', 'contains'],
        'total_crime_count': ['gte', 'lte'],
    }

class SubwayViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subway.objects.select_related('address').all()
    serializer_class = SubwaySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        'line_info': ['exact', 'contains'],
        'address__area_name': ['exact', 'contains'],
    }

class LocationDistanceViewSet(viewsets.ModelViewSet):
    queryset = LocationDistance.objects.all()
    serializer_class = LocationDistanceSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['property', 'address']
    ordering_fields = ['distance']

    @action(detail=False, methods=['get'])
    def by_property(self, request):
        property_id = request.query_params.get('property_id')
        if not property_id:
            return Response({'error': 'property_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        distances = self.queryset.filter(property_id=property_id).order_by('distance')
        serializer = self.get_serializer(distances, many=True)
        return Response(serializer.data)

class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "회원가입이 성공적으로 완료되었습니다.",
                    "user": serializer.data
                }, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
