from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from .views import (
    AddressViewSet, CulturalFacilityViewSet, PropertyLocationViewSet,
    PropertyInfoViewSet, RentalViewSet, SaleViewSet, UserViewSet,
    ChatViewSet, FeedbackViewSet, NoticeViewSet, UserLogViewSet,
    FavoriteViewSet, CrimeStatsViewSet, SubwayViewSet,
    LocationDistanceViewSet, UserRegistrationView
)
from rest_framework_simplejwt.views import TokenRefreshView
from .auth_views import LoginView, RegisterView

# Swagger 문서 설정 수정
schema_view = get_schema_view(
    openapi.Info(
        title="부동산 정보 API",
        default_version='v1.0',
        description="""
# API 사용 방법

## 인증
1. 회원가입: POST /api/auth/register/
2. 로그인: POST /api/auth/login/
3. 토큰 갱신: POST /api/auth/refresh/

## 인증 헤더
모든 API 요청에 다음 헤더를 포함해야 합니다:

## 주요 기능

### 1. 사용자 관리
- 회원가입
- 로그인/로그아웃
- 사용자 프로필 관리

### 2. 부동산 정보
- 매물 정보 조회
- 위치 기반 검색
- 상세 정보 확인

### 3. 즐겨찾기
- 관심 매물 등록
- 즐겨찾기 목록 조회
- 즐겨찾기 삭제

### 4. 채팅
- 실시간 채팅
- 채팅 내역 조회
- AI 응답 기능

### 5. 알림
- 새로운 매물 알림
- 가격 변동 알림
- 관심 지역 알림

## 에러 처리
- 400: 잘못된 요청
- 401: 인증 실패
- 403: 권한 없음
- 404: 리소스 없음
- 500: 서버 오류
        """,
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
router.register(r'addresses', AddressViewSet)
router.register(r'cultural-facilities', CulturalFacilityViewSet)
router.register(r'property-locations', PropertyLocationViewSet)
router.register(r'property-info', PropertyInfoViewSet)
router.register(r'rentals', RentalViewSet)
router.register(r'sales', SaleViewSet)
router.register(r'users', UserViewSet)
router.register(r'chats', ChatViewSet)
router.register(r'feedbacks', FeedbackViewSet)
router.register(r'notices', NoticeViewSet)
router.register(r'user-logs', UserLogViewSet)
router.register(r'favorites', FavoriteViewSet)
router.register(r'crime-stats', CrimeStatsViewSet)
router.register(r'subway-stations', SubwayViewSet)
router.register(r'location-distances', LocationDistanceViewSet)

urlpatterns = [
    path('', include(router.urls)),

    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('auth/', include('rest_framework.urls')),

    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('chats/sessions/', ChatViewSet.as_view({'get': 'sessions'}), name='chat-sessions'),
    path('chats/session-messages/', ChatViewSet.as_view({'get': 'session_messages'}), name='chat-session-messages'),
    path('favorites/my-favorites/', FavoriteViewSet.as_view({'get': 'my_favorites'}), name='my-favorites'),
    path('notices/<int:pk>/toggle-active/', NoticeViewSet.as_view({'patch': 'toggle_active'}), name='notice-toggle-active'),
] 