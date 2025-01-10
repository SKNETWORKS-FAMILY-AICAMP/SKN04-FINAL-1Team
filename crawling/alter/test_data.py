from db_config import SessionLocal, engine
import models as models
import uuid
import json

def create_test_data():
    db = SessionLocal()
    try:
        # 테이블 생성
        models.Base.metadata.create_all(bind=engine)
        
        # 1. Users 테스트 데이터
        users = [
            models.User(
                uuid=str(uuid.uuid4()),
                gender=models.Gender.M,
                age=28,
                age_group="20대",
                desired_location="서울시 강남구"
            ),
            models.User(
                uuid=str(uuid.uuid4()),
                gender=models.Gender.F,
                age=35,
                age_group="30대",
                desired_location="서울시 서초구"
            ),
            models.User(
                uuid=str(uuid.uuid4()),
                gender=models.Gender.O,
                age=42,
                age_group="40대",
                desired_location="서울시 마포구"
            )
        ]
        db.add_all(users)
        db.flush()
        
        # 2. Feedback 테스트 데이터
        feedbacks = [
            models.Feedback(
                user_uuid=users[0].uuid,
                homepage_rating=9,
                q1_accuracy=5,
                q2_naturalness=4,
                q3_resolution=5,
                feedback_text="매우 만족스러운 서비스입니다."
            ),
            models.Feedback(
                user_uuid=users[1].uuid,
                homepage_rating=8,
                q1_accuracy=4,
                q2_naturalness=5,
                q3_resolution=4,
                feedback_text="UI가 직관적이에요."
            ),
            models.Feedback(
                user_uuid=users[2].uuid,
                homepage_rating=7,
                q1_accuracy=3,
                q2_naturalness=4,
                q3_resolution=4,
                feedback_text="추천 기능이 좋습니다."
            )
        ]
        db.add_all(feedbacks)
        
        # 3. Notice 테스트 데이터
        notices = [
            models.Notice(
                title="서비스 오픈 안내",
                content="부동산 추천 서비스가 오픈했습니다.",
                author_id=users[0].uuid,
                status=models.NoticeStatus.ACTIVE
            ),
            models.Notice(
                title="시스템 점검 안내",
                content="2024년 1월 1일 시스템 점검이 있을 예정입니다.",
                author_id=users[1].uuid,
                status=models.NoticeStatus.ACTIVE
            ),
            models.Notice(
                title="이용 가이드",
                content="서비스 이용 방법을 안내드립니다.",
                author_id=users[2].uuid,
                status=models.NoticeStatus.ACTIVE
            )
        ]
        db.add_all(notices)
        
        # 4. ChatLog 테스트 데이터
        chat_logs = [
            models.ChatLog(
                user_uuid=users[0].uuid,
                session_id=str(uuid.uuid4()),
                message_type=models.MessageType.USER,
                message="강남역 근처 원룸 추천해주세요."
            ),
            models.ChatLog(
                user_uuid=users[1].uuid,
                session_id=str(uuid.uuid4()),
                message_type=models.MessageType.BOT,
                message="신논현역 인근에 추천할 만한 매물이 있습니다."
            ),
            models.ChatLog(
                user_uuid=users[2].uuid,
                session_id=str(uuid.uuid4()),
                message_type=models.MessageType.USER,
                message="홍대입구역 근처 투룸 찾아주세요."
            )
        ]
        db.add_all(chat_logs)
        
        # 5. UserAction 테스트 데이터
        user_actions = [
            models.UserAction(
                user_uuid=users[0].uuid,
                session_id=str(uuid.uuid4()),
                action_type="page_view",
                page_url="/main",
                device_info="Chrome/Windows",
                event_details=json.dumps({"page": "main", "section": "recommendations"})
            ),
            models.UserAction(
                user_uuid=users[1].uuid,
                session_id=str(uuid.uuid4()),
                action_type="search",
                page_url="/search",
                device_info="Safari/iOS",
                event_details=json.dumps({"keyword": "강남 원룸", "filters": {"price_max": 5000000}})
            ),
            models.UserAction(
                user_uuid=users[2].uuid,
                session_id=str(uuid.uuid4()),
                action_type="click",
                page_url="/property/123",
                device_info="Firefox/MacOS",
                event_details=json.dumps({"property_id": 123, "action": "contact"})
            )
        ]
        db.add_all(user_actions)
        
        # 6. Favorite 테스트 데이터 - Property 테이블 데이터 확인 후 추가
        try:
            # 먼저 property_info 테이블에서 실제 존재하는 property_id 확인
            existing_properties = db.query(models.Property).limit(3).all()
            
            if existing_properties:
                favorites = [
                    models.Favorite(
                        user_uuid=users[0].uuid,
                        item_id=existing_properties[0].property_id,
                        item_type="property",
                        name=existing_properties[0].building_name or "강남 역세권 원룸",
                        latitude=float(existing_properties[0].location.latitude) if existing_properties[0].location else 37.4969,
                        longitude=float(existing_properties[0].location.longitude) if existing_properties[0].location else 127.0278
                    ),
                    models.Favorite(
                        user_uuid=users[1].uuid,
                        item_id=existing_properties[1].property_id,
                        item_type="property",
                        name=existing_properties[1].building_name or "신논현 신축 투룸",
                        latitude=float(existing_properties[1].location.latitude) if existing_properties[1].location else 37.5044,
                        longitude=float(existing_properties[1].location.longitude) if existing_properties[1].location else 127.0246
                    ),
                    models.Favorite(
                        user_uuid=users[2].uuid,
                        item_id=existing_properties[2].property_id,
                        item_type="property",
                        name=existing_properties[2].building_name or "홍대입구 복층 원룸",
                        latitude=float(existing_properties[2].location.latitude) if existing_properties[2].location else 37.5571,
                        longitude=float(existing_properties[2].location.longitude) if existing_properties[2].location else 126.9245
                    )
                ]
                db.add_all(favorites)
            else:
                print("Warning: property_info 테이블에 데이터가 없어 favorites 테스트 데이터를 생성하지 않습니다.")
        
        except Exception as e:
            print(f"Favorites 데이터 생성 중 오류: {str(e)}")
        
        # 변경사항 저장
        db.commit()
        print("테스트 데이터 생성 완료!")
        
    except Exception as e:
        print(f"테스트 데이터 생성 중 오류 발생: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data() 