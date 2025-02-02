from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import User, UserLog
import random
from datetime import timedelta

class Command(BaseCommand):
    help = '테스트용 유저 로그 데이터를 생성합니다.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=100, help='생성할 로그 수')

    def handle(self, *args, **options):
        count = options['count']
        users = User.objects.all()
        
        if not users.exists():
            self.stdout.write(self.style.ERROR('유저가 없습니다. 먼저 유저를 생성해주세요.'))
            return

        # 가능한 액션 타입들
        action_types = [
            'PROPERTY_VIEW',
            'PROPERTY_SEARCH',
            'FAVORITE_ADD',
            'FAVORITE_REMOVE',
            'PROFILE_UPDATE',
            'LOGIN',
            'LOGOUT',
            'FEEDBACK_SUBMIT',
            'CHAT_SEND',
            'FILTER_APPLY'
        ]

        # 각 액션 타입별 상세 정보 생성 함수
        def generate_action_detail(action_type):
            if action_type == 'PROPERTY_VIEW':
                return {
                    'property_id': random.randint(1000, 9999),
                    'view_duration': random.randint(10, 300),
                    'source': random.choice(['search', 'recommendation', 'favorite', 'direct'])
                }
            elif action_type == 'PROPERTY_SEARCH':
                return {
                    'search_params': {
                        'location': random.choice(['서울시 강남구', '서울시 서초구', '서울시 송파구']),
                        'min_price': random.choice([0, 50000000, 100000000]),
                        'max_price': random.choice([500000000, 1000000000, 1500000000]),
                        'property_type': random.choice(['아파트', '오피스텔', '단독주택'])
                    },
                    'results_count': random.randint(0, 50)
                }
            elif action_type in ['FAVORITE_ADD', 'FAVORITE_REMOVE']:
                return {
                    'property_id': random.randint(1000, 9999),
                    'property_type': random.choice(['아파트', '오피스텔', '단독주택'])
                }
            elif action_type == 'PROFILE_UPDATE':
                return {
                    'updated_fields': random.sample(['nickname', 'email', 'profile_image', 'age'], random.randint(1, 4))
                }
            elif action_type in ['LOGIN', 'LOGOUT']:
                return {
                    'device': random.choice(['web', 'mobile', 'tablet']),
                    'ip_address': f'192.168.{random.randint(1, 255)}.{random.randint(1, 255)}'
                }
            elif action_type == 'FEEDBACK_SUBMIT':
                return {
                    'rating': random.randint(1, 5),
                    'category': random.choice(['UI', 'search', 'recommendation', 'general'])
                }
            elif action_type == 'CHAT_SEND':
                return {
                    'message_length': random.randint(10, 200),
                    'chat_type': random.choice(['inquiry', 'support', 'complaint'])
                }
            elif action_type == 'FILTER_APPLY':
                return {
                    'filters': {
                        'price_range': random.choice(['0-5000', '5000-10000', '10000-20000']),
                        'area': random.choice(['10-30', '30-60', '60-85']),
                        'room_count': random.choice(['1', '2', '3+'])
                    }
                }
            return {}

        # 로그 생성
        created_count = 0
        base_time = timezone.now() - timedelta(days=30)

        for _ in range(count):
            user = random.choice(users)
            action_type = random.choice(action_types)
            action_detail = generate_action_detail(action_type)
            
            # 랜덤한 시간 설정 (최근 30일 이내)
            random_minutes = random.randint(0, 43200)  # 30일 = 43200분
            created_at = base_time + timedelta(minutes=random_minutes)

            UserLog.objects.create(
                user=user,
                action_type=action_type,
                action_detail=action_detail,
                created_at=created_at
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'성공적으로 {created_count}개의 테스트 로그를 생성했습니다.')
        ) 