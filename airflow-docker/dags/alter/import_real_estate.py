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
from alter.models import PropertyLocation, PropertyInfo, Sale, Rental
from alter.db_config import provide_session
from alter.utils import main_logger as logger
from alter.enums import (
    SeoulDistrictCode, NaverSubCategory, HeatingType, CoolingType,
    MoveInType, LivingFacilityType, FacilityType, SecurityType,
    DirectionType, BuildingUseType, PropertyType, LoanAvailability
)
import os

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

    def process_single_property(self, property_data: dict) -> bool:
        """단일 매물 처리 함수"""
        try:
            property_id = int(property_data.get('seq'))
            if not property_id:
                logger.error(f"Invalid property data - missing seq: {property_data}")
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
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        ) as session:
            # IP 변경 확인
            await processor.check_ip_rotation()
            
            # 랜덤 User-Agent 사용
            headers = {
                'accept': '*/*',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://www.rter2.com',
                'referer': 'https://www.rter2.com/mapview',
                'user-agent': processor.user_agent.random,  # 랜덤 User-Agent
                'x-requested-with': 'XMLHttpRequest'
            }
            
            page_no = 1
            all_items = []
            
            while True:
                try:
                    # IP 차단 우회를 위한 대기
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
                    
                    async with session.post(
                        'https://www.rter2.com/hompyArticle/list',
                        data=payload,
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            text = await response.text()
                            logger.info(f"Response text: {text[:200]}...")
                            
                            try:
                                data = await response.json()
                                items = data.get('result', {}).get('list', [])
                                if not items:
                                    break
                                    
                                all_items.extend(items)
                                
                            except Exception as e:
                                logger.error(f"JSON 파싱 오류: {str(e)}")
                                # IP 차단 시 새로운 IP로 변경
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
                            
                except Exception as e:
                    logger.error(f"요청 중 오류 발생: {str(e)}")
                    await processor.tor_controller.renew_tor_ip()
                    await asyncio.sleep(random.uniform(5, 10))
                    continue
                
                page_no += 1
                
            return all_items
                    
    except Exception as e:
        logger.error(f"Error fetching property data: {str(e)}")
        return []

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
                property_data = await get_property_data(processor, district.name, district.value)
                if property_data:
                    processor.process_batch(property_data)
                    success_count += len(property_data)
                await asyncio.sleep(random.uniform(1, 5))
            except Exception as e:
                logger.error(f"Error processing district {district.name}: {str(e)}")
                continue
        
        return {"success": True, "processed_count": success_count}
            
    except Exception as e:
        logger.error(f"Error in import_real_estate: {str(e)}")
        return {"success": False, "error": str(e)}

def process_facilities(facilities_data):
    """시설 정보 처리"""
    if not facilities_data:
        return None
    try:
        facility_info = {
            'cooling': process_facility_type(facilities_data.get('cooling', []), CoolingType),
            'living': process_facility_type(facilities_data.get('living', []), LivingFacilityType),
            'security': process_facility_type(facilities_data.get('security', []), SecurityType),
            'etc': process_facility_type(facilities_data.get('etc', []), FacilityType)
        }
        return json.dumps(facility_info)
    except Exception:
        return None

def process_facility_type(facility_list, enum_type):
    """개별 시설 타입 처리"""
    if not facility_list:
        return []
    try:
        return [enum_type(item).name for item in facility_list if item]
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(import_real_estate()) 