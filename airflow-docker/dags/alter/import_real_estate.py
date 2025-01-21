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
from .enums import (
    SeoulDistrictCode, NaverSubCategory, HeatingType, CoolingType,
    MoveInType, LivingFacilityType, FacilityType, SecurityType,
    DirectionType, BuildingUseType, PropertyType, LoanAvailability,
    TransactionType
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
            property_id = property_data.get('seq')
            if not property_id:
                logger.error(f"Invalid property data - missing seq: {property_data}")
                return False

            # 거래 정보 처리 추가
            trade_info = property_data.get('tradeTypeCode')
            if not trade_info:
                logger.error(f"Missing trade type for property {property_id}")
                return False

            # 기존 데이터 삭제
            self.session.query(PropertyLocation).filter_by(property_id=property_id).delete()
            self.session.query(PropertyInfo).filter_by(property_id=property_id).delete()
            self.session.query(Sale).filter_by(property_id=property_id).delete()
            self.session.query(Rental).filter_by(property_id=property_id).delete()

            # 안전하게 데이터 추출
            legal_dong = property_data.get('legalDong', {}) or {}
            center = property_data.get('center', {}).get('coordinates', []) if property_data.get('center') else []
            
            # 1. Location 정보 저장
            location = PropertyLocation(
                property_id=property_id,
                sido=legal_dong.get('sidoName', ''),
                sigungu=legal_dong.get('gugunName', ''),
                dong=legal_dong.get('dongName', ''),
                jibun_main=property_data.get('jibunMainNumber', ''),
                jibun_sub=property_data.get('jibunSubNumber', ''),
                latitude=center[1] if len(center) > 1 else None,
                longitude=center[0] if len(center) > 0 else None
            )
            self.session.add(location)

            # 2. Property 정보 저장 - Enum 처리 개선
            try:
                property_type = PropertyType(property_data.get('categoryCode')).name if property_data.get('categoryCode') else "UNKNOWN"
            except ValueError:
                property_type = "UNKNOWN"

            try:
                property_subtype = NaverSubCategory(property_data.get('subCategoryCode')).name if property_data.get('subCategoryCode') else "UNKNOWN"
            except ValueError:
                property_subtype = "UNKNOWN"

            try:
                heating_type = HeatingType(property_data.get('heatTypeCode')).name if property_data.get('heatTypeCode') else "UNKNOWN"
            except ValueError:
                heating_type = "UNKNOWN"

            try:
                direction = DirectionType(property_data.get('directionCode')).name if property_data.get('directionCode') else "UNKNOWN"
            except ValueError:
                direction = "UNKNOWN"

            try:
                purpose_type = BuildingUseType(property_data.get('lawUsageCode')).name if property_data.get('lawUsageCode') else "UNKNOWN"
            except ValueError:
                purpose_type = "UNKNOWN"

            try:
                move_in_type = MoveInType(property_data.get('moveInTypeCode')).name if property_data.get('moveInTypeCode') else "UNKNOWN"
            except ValueError:
                move_in_type = "UNKNOWN"

            try:
                loan_availability = LoanAvailability(property_data.get('loanCode')).name if property_data.get('loanCode') else "UNKNOWN"
            except ValueError:
                loan_availability = "UNKNOWN"

            # 숫자 필드 안전하게 처리
            def safe_float(value, default=0.0):
                try:
                    return float(value) if value is not None else default
                except (ValueError, TypeError):
                    return default

            def safe_int(value, default=0):
                try:
                    return int(value) if value is not None else default
                except (ValueError, TypeError):
                    return default

            property_info = PropertyInfo(
                property_id=property_id,
                property_type=property_type,
                property_subtype=property_subtype,
                building_name=property_data.get('buildingName', ''),
                detail_address=property_data.get('detailAddress', ''),
                construction_date=property_data.get('useApproveDay', ''),
                total_area=safe_float(property_data.get('space1')),
                exclusive_area=safe_float(property_data.get('space2')),
                land_area=safe_float(property_data.get('space3')),
                on_floor=safe_int(property_data.get('onFloorCount')),
                under_floor=safe_int(property_data.get('underFloorCount')),
                room_count=safe_int(property_data.get('room')),
                bathroom_count=safe_int(property_data.get('restroom')),
                parking_count=safe_int(property_data.get('parkingCount')),
                heating_type=heating_type,
                direction=direction,
                purpose_type=purpose_type,
                current_usage=property_data.get('currentUsage', ''),
                recommended_usage=property_data.get('recommendUsage', ''),
                facilities={
                    'cooling': self.process_facilities(property_data.get('facilitiesAircon', ''), CoolingType),
                    'living': self.process_facilities(property_data.get('facilitiesLife', ''), LivingFacilityType), 
                    'security': self.process_facilities(property_data.get('facilitiesSecurity', ''), SecurityType),
                    'etc': self.process_facilities(property_data.get('facilitiesEtc', ''), FacilityType)
                },
                description=property_data.get('description', ''),
                photos=process_photos(property_data.get('photoList')),
                move_in_type=move_in_type,
                move_in_date=property_data.get('moveInDate', ''),
                loan_availability=loan_availability,
                negotiable=property_data.get('negotiationFlagCode', 'N')[-1],
                is_active=True,
                last_seen=datetime.now()  # updated_at을 last_seen로 변경
            )
            self.session.add(property_info)

            # 3. 거래 정보 저장 - BigInteger 타입에 맞게 수정
            trade_type = property_data.get('tradeTypeCode')
            if trade_type == '30051A1':  # 매매
                price = int(property_data.get('price1', 0) or 0) * 10000
                if price >= 1000000000000:  # 1조원 이상
                    logger.warning(f"매물 {property_id}의 가격이 너무 높습니다: {price}")
                    price = 999999999999  # BigInteger 최대값 설정
                
                sale = Sale(
                    property_id=property_id,
                    price=price,
                    end_date=property_data.get('endDate'),
                    transaction_date=property_data.get('transactionDate')
                )
                self.session.add(sale)
            else:  # 임대
                deposit = int(property_data.get('price1', 0) or 0) * 10000
                monthly_rent = int(property_data.get('price2', 0) or 0) * 10000
                
                if deposit >= 1000000000000:  # 1조원 이상
                    logger.warning(f"매물 {property_id}의 보증금이 너무 높습니다: {deposit}")
                    deposit = 999999999999
                if monthly_rent >= 1000000000000:
                    logger.warning(f"매물 {property_id}의 월세가 너무 높습니다: {monthly_rent}")
                    monthly_rent = 999999999999
                
                rental = Rental(
                    property_id=property_id,
                    rental_type=TransactionType(trade_type).name,
                    deposit=deposit,
                    monthly_rent=monthly_rent
                )
                self.session.add(rental)

            return True

        except Exception as e:
            logger.error(f"매물 처리 중 오류 발생 (ID: {property_id}): {str(e)}")
            self.session.rollback()
            return False

    def process_batch(self, batch: List[dict]):
        """배치 처리 메서드"""
        processed_count = 0
        
        # 배치의 모든 property_id 수집
        property_ids = []
        for property_data in batch:
            item = property_data.get('result', {}).get('item', {})
            if item and item.get('seq'):
                property_ids.append(item.get('seq'))
        
        try:
            # 한 번에 모든 기존 데이터 삭제 (순서 중요)
            if property_ids:
                with self.session.begin_nested():
                    # 1. 먼저 rentals와 sales 삭제 (자식 테이블)
                    self.session.query(Rental).filter(
                        Rental.property_id.in_(property_ids)
                    ).delete(synchronize_session=False)
                    
                    self.session.query(Sale).filter(
                        Sale.property_id.in_(property_ids)
                    ).delete(synchronize_session=False)
                    
                    # 2. property_info 삭제 (중간 테이블)
                    self.session.query(PropertyInfo).filter(
                        PropertyInfo.property_id.in_(property_ids)
                    ).delete(synchronize_session=False)
                    
                    # 3. 마지막으로 property_locations 삭제 (부모 테이블)
                    self.session.query(PropertyLocation).filter(
                        PropertyLocation.property_id.in_(property_ids)
                    ).delete(synchronize_session=False)
                    
                self.session.commit()
        except Exception as e:
            logger.error(f"데이터 삭제 중 오류 발생: {str(e)}")
            self.session.rollback()
            return 0

        # 새로운 데이터 처리
        for property_data in batch:
            try:
                item = property_data.get('result', {}).get('item', {})
                if not item:
                    continue
                
                if self.process_single_property(item):
                    processed_count += 1
                    
                if processed_count % 100 == 0:
                    try:
                        self.session.commit()
                    except Exception as commit_error:
                        logger.error(f"Failed to commit batch: {str(commit_error)}")
                        self.session.rollback()
                    
            except Exception as e:
                logger.error(f"Failed to process property: {str(e)}")
                continue
        
        try:
            self.session.commit()
        except Exception as final_commit_error:
            logger.error(f"Failed to commit final batch: {str(final_commit_error)}")
            self.session.rollback()
        
        return processed_count

    def process_facilities(self, facilities_data, facility_type_enum):
        """시설 정보를 처리하는 함수"""
        if not facilities_data:
            return []
        
        try:
            facilities = []
            # 문자열로 된 리스트를 파싱
            if isinstance(facilities_data, str):
                try:
                    facilities_data = json.loads(facilities_data)
                except json.JSONDecodeError:
                    return []
            
            # 리스트가 아닌 경우 처리
            if not isinstance(facilities_data, list):
                facilities_data = [facilities_data]
            
            for facility_code in facilities_data:
                try:
                    if facility_code:
                        facility_type = facility_type_enum(facility_code).name
                        facilities.append(facility_type)
                except (ValueError, AttributeError) as e:
                    logger.warning(f"시설 코드 처리 중 오류: {str(e)}, 코드: {facility_code}")
                    continue
            
            return facilities
            
        except Exception as e:
            logger.error(f"시설 정보 처리 중 오류 발생: {str(e)}")
            return []

async def get_property_detail(session, article_id, headers):
    """개별 매물 상세 정보를 가져오는 함수"""
    try:
        url = f"https://www.rter2.com/hompyArticle/{article_id}"
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if data and isinstance(data, dict):
                    data['seq'] = article_id
                return data
            else:
                logger.error(f"매물 상세 정보 가져오기 실패 (ID: {article_id}): {response.status}")
                return None
    except Exception as e:
        logger.error(f"매물 상세 정보 요청 중 오류 발생 (ID: {article_id}): {str(e)}")
        return None

async def get_property_details_batch(session, items, processor, batch_size=100):
    """매물 상세 정보를 배치로 비동기 수집"""
    tasks = []
    all_details = []
    total_processed = 0
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_tasks = []
        
        for idx, item in enumerate(batch):
            article_id = item.get('seq')
            if not article_id:
                logger.warning(f"매물 ID 없음: {item}")
                continue
                
            detail_headers = {
                'accept': '*/*',
                'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'content-type': 'application/json;charset=UTF-8',
                'user-agent': processor.user_agent.random,
                'referer': f'https://www.rter2.com/hompyArticle/detail/{article_id}',
                'origin': 'https://www.rter2.com'
            }
            
            task = get_property_detail(session, article_id, detail_headers)
            batch_tasks.append(task)
        
        if batch_tasks:
            logger.info(f"배치 처리 시작: {i+1}~{min(i+batch_size, len(items))}/{len(items)}")
            results = await asyncio.gather(*batch_tasks)
            successful_details = [r for r in results if r is not None and r.get('seq')]
            
            if successful_details:
                logger.info(f"성공적으로 가져온 매물 수: {len(successful_details)}")
                try:
                    processor.process_batch(successful_details)
                    total_processed += len(successful_details)
                    logger.info(f"현재까지 처리된 총 매물 수: {total_processed}")
                except Exception as e:
                    logger.error(f"배치 처리 중 오류 발생: {str(e)}")
            
            # IP 차단 방지를 위한 대기
            await asyncio.sleep(random.uniform(2, 4))
            
            # 매 10000개 데이터마다 IP 변경
            if total_processed >= 10000:
                logger.info("10000개 데이터 처리 완료, IP 변경")
                await processor.tor_controller.renew_tor_ip()
                await asyncio.sleep(random.uniform(3, 5))
                total_processed = 0
    
    return total_processed

async def get_property_data(processor, district_code):
    """특정 구역의 부동산 데이터를 가져오는 함수"""
    # 구역 코드로부터 구역 이름 가져오기
    district_name = SeoulDistrictCode(district_code).name
    logger.info(f"구역 {district_name}에 대한 데이터 수집 시작")
    
    try:
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

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(import_real_estate()) 