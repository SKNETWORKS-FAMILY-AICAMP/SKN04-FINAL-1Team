from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    Address, CulturalFacility, CulturalFestival, PropertyLocation, PropertyInfo, 
    Rental, Sale, User, Chat, Feedback, Notice, UserLog, Favorite,
    CrimeStats, Subway, LocationDistance
)
from .ai.llm_app import stream_response
import os
from dotenv import load_dotenv

# ✅ .env 파일 로드
load_dotenv()

# ✅ OpenAI API 설정
OPENAI_CONFIG = {
    "openai_api_key": os.getenv("OPENAI_API_KEY"),
    "model_name": "gpt-4-turbo-preview",
    "temperature": 0.7,
    "max_tokens": 2000,
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
}

# ✅ 데이터베이스 스키마 정보
DB_SCHEMA = """
CREATE TABLE addresses (
    address_id SERIAL PRIMARY KEY,
    area_name VARCHAR(255),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

CREATE TABLE location_distances (
    id SERIAL PRIMARY KEY,
    property_id INTEGER,
    address_id INTEGER,
    distance DOUBLE PRECISION
);

CREATE TABLE rentals (
    id SERIAL PRIMARY KEY,
    property_id INTEGER,
    rental_type VARCHAR(10),
    deposit BIGINT,
    monthly_rent BIGINT
);

CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    property_id INTEGER,
    price BIGINT
);

CREATE TABLE property_info (
    id SERIAL PRIMARY KEY,
    property_id INTEGER,
    property_type VARCHAR(50),
    room_count INTEGER,
    bathroom_count INTEGER,
    parking_count INTEGER,
    total_area DOUBLE PRECISION,
    exclusive_area DOUBLE PRECISION,
    land_area DOUBLE PRECISION,
    direction VARCHAR(50),
    floor INTEGER,
    total_floor INTEGER,
    construction_date DATE,
    facilities JSONB,
    description TEXT
);

CREATE TABLE property_locations (
    id SERIAL PRIMARY KEY,
    property_id INTEGER,
    sido VARCHAR(50),
    sigungu VARCHAR(50),
    dong VARCHAR(50),
    jibun VARCHAR(50),
    road_name VARCHAR(50),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);
"""

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'nickname', 'gender', 'age', 'profile_image')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'nickname': {'required': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            nickname=validated_data['nickname'],
            gender=validated_data.get('gender', None),
            age=validated_data.get('age', None),
            profile_image=validated_data.get('profile_image', None)
        )
        return user

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        return super().update(instance, validated_data)

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        label='사용자명',
        help_text='로그인에 사용할 사용자명을 입력하세요.'
    )
    password = serializers.CharField(
        label='비밀번호',
        style={'input_type': 'password'},
        write_only=True
    )

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise serializers.ValidationError('사용자명과 비밀번호를 모두 입력해주세요.')

        user = authenticate(username=username, password=password)
        
        if not user:
            raise serializers.ValidationError('잘못된 사용자명이나 비밀번호입니다.')

        data['user'] = user
        return data

class UserRegistrationSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        # UserSerializer.Meta에 정의된 필드, extra_kwargs를 그대로 쓰되
        # 혹은 수정/추가가 필요하면 작성
        fields = ('id', 'username', 'password', 'email', 'nickname', 'gender', 'age', 'profile_image')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'nickname': {'required': True}
        }

class ChatSerializer(serializers.ModelSerializer):
    ai_response = serializers.CharField(read_only=True)
    
    class Meta:
        model = Chat
        fields = ['id', 'user', 'session_id', 'message_type', 'message', 'ai_response', 'created_at']
        read_only_fields = ('user', 'ai_response', 'created_at')

    def create(self, validated_data):
        # 만약 message_type이 'bot'이면 AI 응답 생성 로직 없이 저장
        if validated_data.get('message_type') == 'bot':
            return Chat.objects.create(**validated_data)
        # 그렇지 않으면, 사용자 메시지일 때만 AI 응답 생성
        chat = Chat.objects.create(**validated_data)
        if chat.message_type == 'user':
            try:
                response_text = ""
                for chunk in stream_response({"message": chat.message, "table": DB_SCHEMA}, config=OPENAI_CONFIG):
                    if chunk[1]['langgraph_node'] in ["Re_Questions", "No_Result_Answer", "Generate_Response"]:
                        response_text += chunk[0].content
                chat.ai_response = response_text
                chat.save()
            except Exception as e:
                chat.ai_response = f"AI 응답 생성 중 오류: {str(e)}"
                chat.save()
        return chat
    
class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ('created_at', 'user')

class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notice
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class UserLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLog
        fields = '__all__'
        read_only_fields = ('created_at',)

class FavoriteSerializer(serializers.ModelSerializer):
    property_details = serializers.SerializerMethodField()

    class Meta:
        model = Favorite
        fields = ('id', 'user', 'property', 'created_at', 'property_details')
        read_only_fields = ('created_at',)

    def get_property_details(self, obj):
        try:
            property_info = obj.property
            if property_info:
                property_location = PropertyLocation.objects.filter(property_id=property_info.property_id).first()
                return {
                    'property_info': PropertyInfoSerializer(property_info).data,
                    'location': PropertyLocationSerializer(property_location).data if property_location else None
                }
        except Exception as e:
            return None
        return None

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'area_name', 'latitude', 'longitude']

class CulturalFacilitySerializer(serializers.ModelSerializer):
    address_detail = AddressSerializer(source='address', read_only=True)
    
    class Meta:
        model = CulturalFacility
        fields = '__all__'

class PropertyLocationSerializer(serializers.ModelSerializer):
    property_id = serializers.IntegerField(source="property.id", read_only=True)  # ✅ ForeignKey를 올바르게 매핑

    class Meta:
        model = PropertyLocation
        fields = '__all__'

class PropertyInfoSerializer(serializers.ModelSerializer):
    location_info = serializers.SerializerMethodField() 

    class Meta:
        model = PropertyInfo
        exclude = ('property_id',)

    def get_location_info(self, obj):  # ✅ 이 함수가 없으면 오류 발생함!
        try:
            property_location = PropertyLocation.objects.filter(property_id=obj.id).first()
            return PropertyLocationSerializer(property_location).data if property_location else None
        except Exception as e:
            return {"error": f"위치 정보를 가져오는 중 오류 발생: {str(e)}"}

class RentalSerializer(serializers.ModelSerializer):
    property_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Rental
        exclude = ('property_id',)

    def get_property_details(self, obj):
        if hasattr(obj, 'property_id'):
            property_info = PropertyInfoSerializer(obj.property_id).data
            location_info = PropertyLocationSerializer(obj.property_id.property_id).data if obj.property_id and obj.property_id.property_id else None
            return {
                'property_info': property_info,
                'location': location_info
            }
        return None

class SaleSerializer(serializers.ModelSerializer):
    property_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Sale
        exclude = ('property_id',)

    def get_property_details(self, obj):
        if hasattr(obj, 'property_id'):
            property_info = PropertyInfoSerializer(obj.property_id).data
            location_info = PropertyLocationSerializer(obj.property_id.property_id).data if obj.property_id and obj.property_id.property_id else None
            return {
                'property_info': property_info,
                'location': location_info
            }
        return None

class CrimeStatsSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)
    
    class Meta:
        model = CrimeStats
        fields = [
            'id', 'address', 'reference_date', 'total_crime_count',
            'violent_crime_count', 'theft_crime_count', 'intellectual_crime_count',
            'created_at'
        ]
        read_only_fields = ['created_at']

class SubwaySerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)
    
    class Meta:
        model = Subway
        fields = ['id', 'address', 'line_info', 'created_at']
        read_only_fields = ['created_at']

class LocationDistanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationDistance
        fields = '__all__'

class AddressDetailSerializer(serializers.ModelSerializer):
    crime_stats = CrimeStatsSerializer(many=True, read_only=True)
    subway_stations = SubwaySerializer(many=True, read_only=True)
    location_distances = LocationDistanceSerializer(many=True, read_only=True)

    class Meta:
        model = Address
        fields = '__all__' 