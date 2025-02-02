import json
import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
from datetime import datetime, timezone
import logging
from typing import List
from tqdm import tqdm
from stem import Signal
from stem.control import Controller
from fake_useragent import UserAgent
import random
import time
from alter.models import PropertyLocation, PropertyInfo, Sale, Rental, LocationDistance
from alter.db_config import provide_session
from alter.utils import main_logger as logger
from .enums import (
    SeoulDistrictCode, NaverSubCategory, HeatingType, CoolingType,
    MoveInType, LivingFacilityType, FacilityType, SecurityType,
    DirectionType, BuildingUseType, PropertyType, LoanAvailability,
    TransactionType
)
import os
import requests
import socket
from sqlalchemy import text

class TorController:
    def __init__(self, password='your_password', host='tor', port=9051):
        self.password = os.getenv('TOR_PASSWORD', password)
        self.host = host
        self.port = port
        
    async def renew_tor_ip(self):
        try:
            with Controller.from_port(address=self.host, port=self.port) as controller:
                controller.authenticate(password=self.password)
                controller.signal(Signal.NEWNYM)
                await asyncio.sleep(5)
                logger.info("Successfully renewed Tor IP")
        except Exception as e:
            logger.error(f"Failed to renew Tor IP: {str(e)}")

class PropertyProcessor:
    def __init__(self, session):
        self.session = session
        self.batch_size = 100
        self.tor_controller = TorController()
        self.user_agent = UserAgent()
        self.request_count = 0
        self.max_requests_per_ip = 30

    async def check_ip_rotation(self):
        self.request_count += 1
        if self.request_count >= self.max_requests_per_ip:
            await self.tor_controller.renew_tor_ip()
            self.request_count = 0
            await asyncio.sleep(random.uniform(1, 3))

    def process_property(self, item: dict) -> bool:
        """개별 매물 데이터 처리"""
        property_id = None
        try:
            property_id = int(property_data.get('seq'))
            if not property_id:
                logger.error(f"Invalid property data - missing seq: {item}")
                return False

            # 1. Location 정보 저장
            location = PropertyLocation(
                property_id=property_id,
                sido=property_data.get('sido', ''),
                sigungu=property_data.get('sigungu', ''),
                dong=property_data.get('dong', ''),
                jibun_main=property_data.get('jibunMain', ''),
                jibun_sub=property_data.get('jibunSub', ''),
                latitude=float(property_data.get('latitude', 0.0)),
                longitude=float(property_data.get('longitude', 0.0))
            )
            self.session.add(location)

            # 2. Property 정보 저장
            property_info = PropertyInfo(
                property_id=property_id,
                property_type=PropertyType(property_data.get('categoryCode', 'UNKNOWN')).name,
                property_subtype=NaverSubCategory(property_data.get('subCategoryCode', 'UNKNOWN')).name,
                building_name=property_data.get('buildingName', ''),
                detail_address=property_data.get('detailAddress', ''),
                construction_date=property_data.get('constructionDate', ''),
                total_area=property_data.get('totalArea', 0.0),
                exclusive_area=property_data.get('exclusiveArea', 0.0),
                land_area=property_data.get('landArea', 0.0),
                on_floor=property_data.get('floor', 0),
                under_floor=property_data.get('underFloor', 0),
                room_count=property_data.get('roomCount', 0),
                bathroom_count=property_data.get('bathroomCount', 0),
                parking_count=property_data.get('parkingCount', 0),
                heating_type=HeatingType(property_data.get('heatTypeCode', 'UNKNOWN')).name,
                direction=DirectionType(property_data.get('directionCode', 'UNKNOWN')).name,
                purpose_type=BuildingUseType(property_data.get('lawUsageCode', 'UNKNOWN')).name,
                current_usage=property_data.get('currentUsage', ''),
                recommended_usage=property_data.get('recommendedUsage', ''),
                facilities=process_facilities(property_data.get('facilities', [])),
                description=property_data.get('description', ''),
                photos=process_photos(property_data.get('photos', [])),
                move_in_type=MoveInType(property_data.get('moveInTypeCode', 'UNKNOWN')).name,
                move_in_date=property_data.get('moveInDate', ''),
                loan_availability=LoanAvailability(property_data.get('loanCode', 'UNKNOWN')).name,
                is_active=True
            )
            self.session.add(property_info)

            # 3. 거래 정보 저장
            trade_type = property_data.get('tradeType', '')
            if trade_type == 'sale':
                sale = Sale(
                    property_id=property_id,
                    price=property_data.get('price', 0) * 10000  # 만원 단위를 원 단위로 변환
                )
                self.session.add(sale)
            else:
                rental = Rental(
                    property_id=property_id,
                    rental_type=trade_type,
                    deposit=property_data.get('deposit', 0) * 10000,
                    monthly_rent=property_data.get('monthlyRent', 0) * 10000
                )
                self.session.add(rental)

                    return True

                except Exception as inner_e:
                    logger.error(f"매물 {property_id} 처리 중 내부 오류 발생: {str(inner_e)}")
                    raise  # 외부 트랜잭션에서 롤백하도록 예외를 다시 발생시킴

        except Exception as e:
            logger.error(f"Failed to process property {property_data.get('seq')}: {str(e)}")
            return False

    def process_batch(self, batch: List[dict]):
        """배치 처리 메서드"""
        processed_count = 0
        for property_data in batch:
            try:
                # 이미 존재하는지 확인
                property_id = property_data.get('seq')
                existing = self.session.query(PropertyLocation).filter_by(
                    property_id=property_id
                ).first()
                
                if existing:
                    # 이미 존재하면 스킵
                    logger.info(f"Property {property_id} already exists, skipping...")
                    continue
                    
                if self.process_single_property(property_data):
                    processed_count += 1
                
                # 100개마다 커밋
                if processed_count % 100 == 0:
                    try:
                        self.session.commit()
                        logger.info(f"Committed {processed_count} items")
                    except Exception as e:
                        self.session.rollback()
                        logger.error(f"Failed to commit batch at {processed_count} items: {str(e)}")
                        
            except Exception as e:
                # 개별 처리 실패 시 해당 항목만 롤백
                self.session.rollback()
                logger.error(f"Failed to process property {property_data.get('seq')}: {str(e)}")
                continue
        
        # 남은 항목들 커밋
        try:
            if processed_count % 100 != 0:
                self.session.commit()
                logger.info(f"Successfully committed final batch of {processed_count % 100} items")
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to commit final batch: {str(e)}")
            raise

        return processed_count

async def get_property_data(processor, district_name, district_code):
    """부동산 데이터 가져오기"""
    try:
        # Tor 프록시 설정
        connector = ProxyConnector.from_url('socks5://tor:9050')
        timeout = aiohttp.ClientTimeout(total=1800)
        
        total_processed = 0
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        ) as session:
            await processor.check_ip_rotation()
            logger.info("세션 생성 및 IP 로테이션 확인 완료")
            
            list_headers = {
                'user-agent': processor.user_agent.random,
                'Connection': 'keep-alive',
                'Referer': 'https://www.rter2.com',
                'Origin': 'https://www.rter2.com',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            logger.info(f"요청 헤더 설정: {list_headers}")

            page_no = 1
            
            while True:
                try:
                    logger.info(f"페이지 {page_no} 데이터 요청 시작")
                    await asyncio.sleep(random.uniform(1, 3))
                    
                    payload = {
                        'pageNo': str(page_no),
                        'pageSize': '10000',
                        'northLatitude': '37.6909188',
                        'eastLongitude': '127.266862',
                        'southLatitude': '37.3707375',
                        'westLongitude': '126.662614',
                        'centerLatitude': '37.531',
                        'centerLongitude': '126.964738',
                        'zoomLevel': '11',
                        'searchType': '',
                        'searchValue': '',
                        'startDate': '',
                        'endDate': '',
                        'searchMore': json.dumps({"order":"show_start_date,desc"}),
                        'temporary': json.dumps({
                            "legalDongCode": district_code,
                            "typeCode": "18000GUGUN"
                        })
                    }
                    logger.info(f"요청 페이로드: {payload}")
                    
                    async with session.post(
                        'https://www.rter2.com/hompyArticle/list',
                        data=payload,
                        headers=list_headers
                    ) as response:
                        logger.info(f"응답 상태 코드: {response.status}")
                        if response.status == 200:
                            try:
                                response_text = await response.text()
                                
                                data = await response.json()
                                items = data.get('result', {}).get('list', [])
                                total_count = data.get('result', {}).get('paging', {}).get('totalCount', 0)
                                
                                logger.info(f"페이지 {page_no}에서 {len(items)}개의 매물 발견 (전체: {total_count}개)")
                                
                                if not items or total_processed >= 10000:
                                    logger.info("매물 수집 완료 또는 최대 개수 도달. 페이지 순회 종료")
                                    break
                                    
                                # 배치로 상세 정보 수집
                                processed_count = await get_property_details_batch(session, items, processor)
                                total_processed += processed_count
                                
                                page_no += 1
                                logger.info(f"다음 페이지로 이동: {page_no}")
                                
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON 파싱 오류: {str(e)}, 응답 데이터: {response_text[:500]}")
                                await processor.tor_controller.renew_tor_ip()
                                await asyncio.sleep(random.uniform(5, 10))
                                continue
                            except Exception as e:
                                logger.error(f"데이터 처리 중 예외 발생: {str(e)}")
                                await processor.tor_controller.renew_tor_ip()
                                await asyncio.sleep(random.uniform(5, 10))
                                continue
                                
                        elif response.status == 403:
                            logger.error("접근이 차단됨. IP 변경 시도")
                            await processor.tor_controller.renew_tor_ip()
                            await asyncio.sleep(random.uniform(5, 10))
                            continue
                        else:
                            logger.error(f"API 오류 응답: {response.status}")
                            await processor.tor_controller.renew_tor_ip()
                            await asyncio.sleep(random.uniform(5, 10))
                            continue
                            
                    page_no += 1
                    logger.info(f"다음 페이지로 이동: {page_no}")
                    
                except Exception as e:
                    logger.error(f"페이지 처리 중 예외 발생: {str(e)}")
                    await processor.tor_controller.renew_tor_ip()
                    await asyncio.sleep(random.uniform(5, 10))
                    continue

            logger.info(f"구역 코드 {district_code} 데이터 수집 완료. 총 {total_processed}개의 매물 수집")
            return total_processed
                    
    except Exception as e:
        logger.error(f"전체 프로세스 실패: {str(e)}")
        return 0

def run_import_real_estate():
    """Airflow task에서 호출할 래퍼 함수"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(import_real_estate())
        loop.close()
        return result
    except Exception as e:
        logger.error(f"부동산 데이터 가져오기 실패: {str(e)}")
        raise

@provide_session
async def import_real_estate(session=None):
    """부동산 데이터를 가져와서 DB에 저장하는 함수"""
    success_count = 0
    try:
        processor = PropertyProcessor(session)
        
        for district in SeoulDistrictCode:
            try:
                # SIGTERM 시그널을 받았는지 확인
                if asyncio.current_task().cancelled():
                    logger.info("작업이 취소되었습니다. 정상적으로 종료합니다.")
                    break
                    
                property_data = await get_property_data(processor, district.value)
                if property_data:
                    success_count += property_data
                await asyncio.sleep(random.uniform(1, 5))
            except Exception as e:
                logger.error(f"Error processing district {district.name}: {str(e)}")
                continue
        
        return {"success": True, "processed_count": success_count}
            
    except asyncio.CancelledError:
        logger.info("작업이 취소되었습니다. 정상적으로 종료합니다.")
        return {"success": True, "processed_count": success_count}
    except Exception as e:
        logger.error(f"Error in import_real_estate: {str(e)}")
        return {"success": False, "error": str(e)}

def process_facility_type(facility_list, enum_type):
    """개별 시설 타입 처리"""
    print(facility_list)
    if not facility_list:
        return []
    try:
        # 역슬래시 제거
        cleaned_list = [item.replace('\\', '') for item in facility_list if item]
        return [enum_type(item).name for item in cleaned_list]
    except ValueError:
        return []

def process_photos(photos_data):
    if not photos_data:
        return {}
    try:
        if isinstance(photos_data, str):
            return json.loads(photos_data)
        return photos_data
    except:
        return {}

def get_tor_session():
    """Tor 프록시를 사용하는 requests 세션 생성"""
    session = requests.session()
    session.proxies = {
        'http': 'socks5h://tor:9050',
        'https': 'socks5h://tor:9050'
    }
    return session

def renew_tor_ip():
    """Tor IP 갱신"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('tor', 9051))
            s.send(b'AUTHENTICATE ""\r\n')
            response = s.recv(128)
            if response.startswith(b'250'):
                s.send(b'SIGNAL NEWNYM\r\n')
                response = s.recv(128)
                if response.startswith(b'250'):
                    logger.info('Successfully renewed Tor IP')
                    return True
        logger.error('Failed to renew Tor IP')
        return False
    except Exception as e:
        logger.error(f'Failed to renew Tor IP: {str(e)}')
        return False

def create_property_info(session, property_location, property_data):
    """매물 정보 생성"""
    try:
        property_info = PropertyInfo(
            property_id=property_data.get('property_id'),  # property_id를 직접 사용
            property_type=property_data.get('property_type'),
            property_subtype=property_data.get('property_subtype'),
            building_name=property_data.get('building_name'),
            detail_address=property_data.get('detail_address'),
            construction_date=property_data.get('construction_date', ''),
            total_area=property_data.get('total_area'),
            exclusive_area=property_data.get('exclusive_area'),
            land_area=property_data.get('land_area'),
            on_floor=property_data.get('on_floor'),
            under_floor=property_data.get('under_floor'),
            room_count=property_data.get('room_count'),
            bathroom_count=property_data.get('bathroom_count'),
            parking_count=property_data.get('parking_count'),
            heating_type=property_data.get('heating_type'),
            direction=property_data.get('direction'),
            purpose_type=property_data.get('purpose_type'),
            current_usage=property_data.get('current_usage'),
            recommended_usage=property_data.get('recommended_usage'),
            facilities=property_data.get('facilities'),
            description=property_data.get('description'),
            move_in_type=property_data.get('move_in_type'),
            move_in_date=property_data.get('move_in_date'),
            loan_availability=property_data.get('loan_availability'),
            negotiable=property_data.get('negotiable', 'N'),
            photos=property_data.get('photos', '{}'),
            update_count=property_data.get('update_count', 0),
            is_active=property_data.get('is_active', True),
            inactive_reason=property_data.get('inactive_reason'),
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc)
        )
        session.add(property_info)
        session.flush()
        return property_info
    except Exception as e:
        logger.error(f"매물 정보 생성 중 오류 발생: {str(e)}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(import_real_estate()) 