from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import UserLoginSerializer, UserRegistrationSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='사용자명'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='비밀번호'),
            },
        ),
        responses={
            200: openapi.Response(
                description="로그인 성공",
                examples={
                    "application/json": {
                        "message": "로그인 성공",
                        "token": {
                            "access": "access_token_example",
                            "refresh": "refresh_token_example"
                        },
                        "user": {
                            "id": 1,
                            "username": "example_user",
                            "email": "user@example.com",
                            "nickname": "닉네임"
                        }
                    }
                }
            ),
            400: "잘못된 요청"
        }
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': '로그인 성공',
                'token': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                },
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'nickname': user.nickname
                }
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password', 'email', 'nickname'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='사용자명'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='비밀번호'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='이메일'),
                'nickname': openapi.Schema(type=openapi.TYPE_STRING, description='닉네임'),
                'gender': openapi.Schema(type=openapi.TYPE_STRING, description='성별 (M/F/O)', enum=['M', 'F', 'O']),
                'age': openapi.Schema(type=openapi.TYPE_INTEGER, description='나이'),
                'profile_image': openapi.Schema(type=openapi.TYPE_STRING, description='프로필 이미지 URL'),
            },
        ),
        responses={
            201: openapi.Response(
                description="회원가입 성공",
                examples={
                    "application/json": {
                        "message": "회원가입 성공",
                        "token": {
                            "access": "access_token_example",
                            "refresh": "refresh_token_example"
                        },
                        "user": {
                            "id": 1,
                            "username": "example_user",
                            "email": "user@example.com",
                            "nickname": "닉네임"
                        }
                    }
                }
            ),
            400: "잘못된 요청"
        }
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': '회원가입 성공',
                'token': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                },
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'nickname': user.nickname
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 