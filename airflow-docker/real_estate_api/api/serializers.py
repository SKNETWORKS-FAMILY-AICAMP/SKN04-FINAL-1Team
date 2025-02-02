from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    Address, CulturalFacility, CulturalFestival, PropertyLocation, PropertyInfo, 
    Rental, Sale, User, Chat, Feedback, Notice, UserLog, Favorite,
    CrimeStats, Subway, LocationDistance
)

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
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Incorrect Credentials")

class ChatSerializer(serializers.ModelSerializer):
    ai_response = serializers.CharField(read_only=True)
    
    class Meta:
        model = Chat
        fields = ['id', 'user', 'session_id', 'message_type', 'message', 'ai_response', 'created_at']
        read_only_fields = ('user', 'ai_response', 'created_at')

    def create(self, validated_data):
        # 사용자 메시지 저장
        chat = Chat.objects.create(**validated_data)
        
        # 메시지 타입이 'user'인 경우에만 AI 응답 생성
        if chat.message_type == 'user':
            # 부동산 관련 기본 응답 템플릿
            ai_responses = {
                '가격': '해당 매물의 가격은 시세와 비교했을 때 적절한 수준입니다. 주변 시세 정보를 함께 확인해보시겠습니까?',
                '위치': '해당 지역은 교통이 편리하며, 주변에 편의시설이 잘 갖추어져 있습니다. 더 자세한 정보를 원하시나요?',
                '학군': '이 지역은 우수한 학군이 형성되어 있으며, 도보 거리에 여러 학교가 있습니다.',
                '교통': '지하철역과 버스정류장이 가깝고, 주요 도로와의 접근성이 좋습니다.',
                '환경': '주변에 공원과 녹지가 있어 주거 환경이 쾌적합니다.',
                '시설': '단지 내 주차장, 헬스장, 놀이터 등 편의시설이 잘 갖추어져 있습니다.',
                '안전': '24시간 경비 시스템과 CCTV가 설치되어 있어 안전한 주거환경을 제공합니다.'
            }

            # 사용자 메시지에서 키워드 매칭
            message = chat.message.lower()
            matched_response = None

            for keyword, response in ai_responses.items():
                if keyword in message:
                    matched_response = response
                    break

            # 기본 응답
            if not matched_response:
                matched_response = "죄송합니다. 좀 더 구체적인 질문을 해주시면 자세히 답변 드리겠습니다. 매물의 가격, 위치, 학군, 교통, 환경, 시설, 안전 등에 대해 문의해 주세요."

            chat.ai_response = matched_response
            chat.save()

        return chat

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ('created_at',)

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
    class Meta:
        model = PropertyLocation
        fields = '__all__'

class PropertyInfoSerializer(serializers.ModelSerializer):
    location_info = serializers.SerializerMethodField()
    
    class Meta:
        model = PropertyInfo
        exclude = ('property_id',)

    def get_location_info(self, obj):
        if hasattr(obj, 'property_id'):
            return PropertyLocationSerializer(obj.property_id).data
        return None

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