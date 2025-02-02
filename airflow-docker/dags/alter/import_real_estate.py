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
            property_id = item.get('seq')
            if not property_id:
                logger.error(f"Invalid property data - missing seq: {item}")
                return False

            # 단일 트랜잭션으로 모든 작업 수행
            with self.session.begin():
                try:
                    # 1. 기존 데이터 삭제 (자식 테이블부터 삭제)
                    try:
                        # LocationDistance 테이블이 존재하는지 확인
                        self.session.execute(text("SELECT 1 FROM information_schema.tables WHERE table_name = 'location_distances'"))
                        self.session.query(LocationDistance).filter_by(property_id=property_id).delete(synchronize_session=False)
                    except Exception as e:
                        logger.warning(f"LocationDistance 삭제 중 오류 (무시됨): {str(e)}")

                    try:
                        self.session.query(Rental).filter_by(property_id=property_id).delete(synchronize_session=False)
                    except Exception as e:
                        logger.warning(f"Rental 삭제 중 오류 (무시됨): {str(e)}")

                    try:
                        self.session.query(Sale).filter_by(property_id=property_id).delete(synchronize_session=False)
                    except Exception as e:
                        logger.warning(f"Sale 삭제 중 오류 (무시됨): {str(e)}")

                    try:
                        self.session.query(PropertyInfo).filter_by(property_id=property_id).delete(synchronize_session=False)
                    except Exception as e:
                        logger.warning(f"PropertyInfo 삭제 중 오류 (무시됨): {str(e)}")

                    try:
                        self.session.query(PropertyLocation).filter_by(property_id=property_id).delete(synchronize_session=False)
                    except Exception as e:
                        logger.warning(f"PropertyLocation 삭제 중 오류 (무시됨): {str(e)}")

                    self.session.flush()

                    # 2. Location 정보 저장 (부모 테이블)
                    legal_dong = item.get('legalDong', {}) or {}
                    center = item.get('center', {}).get('coordinates', []) if item.get('center') else []
                    
                    location = PropertyLocation(
                        property_id=property_id,
                        sido=legal_dong.get('sidoName', ''),
                        sigungu=legal_dong.get('gugunName', ''),
                        dong=legal_dong.get('dongName', ''),
                        jibun_main=item.get('jibunMainNumber', ''),
                        jibun_sub=item.get('jibunSubNumber', ''),
                        latitude=center[1] if len(center) > 1 else None,
                        longitude=center[0] if len(center) > 0 else None
                    )
                    try:
                        self.session.add(location)
                        self.session.flush()

                        # Location이 실제로 저장되었는지 확인
                        saved_location = self.session.query(PropertyLocation).filter_by(property_id=property_id).first()
                        if not saved_location:
                            raise Exception(f"PropertyLocation {property_id}가 저장되지 않았습니다.")
                    except Exception as e:
                        logger.error(f"Location 저장 중 오류 발생: {str(e)}")
                        raise

                    # 3. Property 정보 저장 (중간 테이블)
                    property_info = PropertyInfo(
                        property_id=saved_location.property_id,  # PropertyLocation의 ID 값을 사용
                        property_type=PropertyType(item.get('categoryCode')).name if item.get('categoryCode') else "UNKNOWN",
                        property_subtype=NaverSubCategory(item.get('subCategoryCode')).name if item.get('subCategoryCode') else "UNKNOWN",
                        building_name=item.get('buildingName', ''),
                        detail_address=item.get('detailAddress', ''),
                        construction_date=item.get('useApproveDay', ''),
                        total_area=item.get('space1'),
                        exclusive_area=item.get('space2'),
                        land_area=item.get('space3'),
                        on_floor=item.get('onFloorCount'),
                        under_floor=item.get('underFloorCount'),
                        room_count=item.get('room'),
                        bathroom_count=item.get('restroom'),
                        parking_count=item.get('parkingCount'),
                        heating_type=HeatingType(item.get('heatTypeCode')).name if item.get('heatTypeCode') else "UNKNOWN",
                        direction=DirectionType(item.get('directionCode')).name if item.get('directionCode') else "UNKNOWN",
                        purpose_type=BuildingUseType(item.get('lawUsageCode')).name if item.get('lawUsageCode') else "UNKNOWN",
                        current_usage=item.get('currentUsage', ''),
                        recommended_usage=item.get('recommendUsage', ''),
                        facilities={
                            'cooling': self.process_facilities(item.get('facilitiesAircon', ''), CoolingType),
                            'living': self.process_facilities(item.get('facilitiesLife', ''), LivingFacilityType),
                            'security': self.process_facilities(item.get('facilitiesSecurity', ''), SecurityType),
                            'etc': self.process_facilities(item.get('facilitiesEtc', ''), FacilityType)
                        },
                        description=item.get('description', ''),
                        photos=process_photos(item.get('photoList')),
                        move_in_type=MoveInType(item.get('moveInTypeCode')).name if item.get('moveInTypeCode') else "UNKNOWN",
                        move_in_date=item.get('moveInDate', ''),
                        loan_availability=LoanAvailability(item.get('loanCode')).name if item.get('loanCode') else "UNKNOWN",
                        negotiable=item.get('negotiationFlagCode', 'N')[-1],
                        is_active=True,
                        last_seen=datetime.now()
                    )
                    self.session.add(property_info)
                    self.session.flush()

                    # PropertyInfo가 실제로 저장되었는지 확인
                    saved_property = self.session.query(PropertyInfo).filter_by(property_id=property_id).first()
                    if not saved_property:
                        raise Exception(f"PropertyInfo {property_id}가 저장되지 않았습니다.")

                    # 4. 거래 정보 저장 (자식 테이블)
                    trade_type = item.get('tradeTypeCode')
                    if trade_type == '30051A1':  # 매매
                        price = int(item.get('price1', 0) or 0) * 10000
                        if price >= 1000000000000:
                            logger.warning(f"매물 {property_id}의 가격이 너무 높습니다: {price}")
                            price = 999999999999
                        
                        sale = Sale(
                            property_id=property_id,  # property_id를 직접 사용
                            price=price,
                            end_date=item.get('endDate'),
                            transaction_date=item.get('transactionDate')
                        )
                        self.session.add(sale)
                    else:  # 임대
                        deposit = int(item.get('price1', 0) or 0) * 10000
                        monthly_rent = int(item.get('price2', 0) or 0) * 10000
                        
                        if deposit >= 1000000000000:
                            logger.warning(f"매물 {property_id}의 보증금이 너무 높습니다: {deposit}")
                            deposit = 999999999999
                        if monthly_rent >= 1000000000000:
                            logger.warning(f"매물 {property_id}의 월세가 너무 높습니다: {monthly_rent}")
                            monthly_rent = 999999999999
                        
                        rental = Rental(
                            property_id=property_id,  # property_id를 직접 사용
                            rental_type=TransactionType(trade_type).name,
                            deposit=deposit,
                            monthly_rent=monthly_rent
                        )
                        self.session.add(rental)
                    self.session.flush()

                    return True

                except Exception as inner_e:
                    logger.error(f"매물 {property_id} 처리 중 내부 오류 발생: {str(inner_e)}")
                    raise  # 외부 트랜잭션에서 롤백하도록 예외를 다시 발생시킴

        except Exception as e:
            logger.error(f"매물 {property_id} 처리 중 오류 발생: {str(e)}")
            return False

    def process_batch(self, batch: List[dict]):
        """배치 처리 메서드"""
        processed_count = 0
        
        # 배치의 모든 property_id 수집
        property_ids = []
        items_by_id = {}
        for property_data in batch:
            item = property_data.get('result', {}).get('item', {})
            if item and item.get('seq'):
                property_id = item.get('seq')
                property_ids.append(property_id)
                items_by_id[property_id] = item

        if not property_ids:
            return 0

        # 각 매물을 개별 트랜잭션으로 처리
        for property_id, item in items_by_id.items():
            try:
                with self.session.begin_nested():
                    # 1. 기존 데이터 삭제
                    try:
                        # LocationDistance 테이블이 존재하는지 확인
                        self.session.execute(text("SELECT 1 FROM information_schema.tables WHERE table_name = 'location_distances'"))
                        self.session.query(LocationDistance).filter_by(property_id=property_id).delete(synchronize_session=False)
                    except Exception as e:
                        logger.warning(f"LocationDistance 삭제 중 오류 (무시됨): {str(e)}")

                    try:
                        self.session.query(Rental).filter_by(property_id=property_id).delete(synchronize_session=False)
                    except Exception as e:
                        logger.warning(f"Rental 삭제 중 오류 (무시됨): {str(e)}")

                    try:
                        self.session.query(Sale).filter_by(property_id=property_id).delete(synchronize_session=False)
                    except Exception as e:
                        logger.warning(f"Sale 삭제 중 오류 (무시됨): {str(e)}")

                    try:
                        self.session.query(PropertyInfo).filter_by(property_id=property_id).delete(synchronize_session=False)
                    except Exception as e:
                        logger.warning(f"PropertyInfo 삭제 중 오류 (무시됨): {str(e)}")

                    try:
                        self.session.query(PropertyLocation).filter_by(property_id=property_id).delete(synchronize_session=False)
                    except Exception as e:
                        logger.warning(f"PropertyLocation 삭제 중 오류 (무시됨): {str(e)}")

                    self.session.flush()

                    # 2.1 Location 정보 저장
                    legal_dong = item.get('legalDong', {}) or {}
                    center = item.get('center', {}).get('coordinates', []) if item.get('center') else []
                    
                    location = PropertyLocation(
                        property_id=property_id,
                        sido=legal_dong.get('sidoName', ''),
                        sigungu=legal_dong.get('gugunName', ''),
                        dong=legal_dong.get('dongName', ''),
                        jibun_main=item.get('jibunMainNumber', ''),
                        jibun_sub=item.get('jibunSubNumber', ''),
                        latitude=center[1] if len(center) > 1 else None,
                        longitude=center[0] if len(center) > 0 else None
                    )
                    try:
                        self.session.add(location)
                        self.session.flush()

                        # Location이 실제로 저장되었는지 확인
                        saved_location = self.session.query(PropertyLocation).filter_by(property_id=property_id).first()
                        if not saved_location:
                            raise Exception(f"PropertyLocation {property_id}가 저장되지 않았습니다.")
                    except Exception as e:
                        logger.error(f"Location 저장 중 오류 발생: {str(e)}")
                        raise

                    # 2.2 Property 정보 저장
                    property_info = PropertyInfo(
                        property_id=saved_location.property_id,  # PropertyLocation의 ID 값을 사용
                        property_type=PropertyType(item.get('categoryCode')).name if item.get('categoryCode') else "UNKNOWN",
                        property_subtype=NaverSubCategory(item.get('subCategoryCode')).name if item.get('subCategoryCode') else "UNKNOWN",
                        building_name=item.get('buildingName', ''),
                        detail_address=item.get('detailAddress', ''),
                        construction_date=item.get('useApproveDay', ''),
                        total_area=item.get('space1'),
                        exclusive_area=item.get('space2'),
                        land_area=item.get('space3'),
                        on_floor=item.get('onFloorCount'),
                        under_floor=item.get('underFloorCount'),
                        room_count=item.get('room'),
                        bathroom_count=item.get('restroom'),
                        parking_count=item.get('parkingCount'),
                        heating_type=HeatingType(item.get('heatTypeCode')).name if item.get('heatTypeCode') else "UNKNOWN",
                        direction=DirectionType(item.get('directionCode')).name if item.get('directionCode') else "UNKNOWN",
                        purpose_type=BuildingUseType(item.get('lawUsageCode')).name if item.get('lawUsageCode') else "UNKNOWN",
                        current_usage=item.get('currentUsage', ''),
                        recommended_usage=item.get('recommendUsage', ''),
                        facilities={
                            'cooling': self.process_facilities(item.get('facilitiesAircon', ''), CoolingType),
                            'living': self.process_facilities(item.get('facilitiesLife', ''), LivingFacilityType),
                            'security': self.process_facilities(item.get('facilitiesSecurity', ''), SecurityType),
                            'etc': self.process_facilities(item.get('facilitiesEtc', ''), FacilityType)
                        },
                        description=item.get('description', ''),
                        photos=process_photos(item.get('photoList')),
                        move_in_type=MoveInType(item.get('moveInTypeCode')).name if item.get('moveInTypeCode') else "UNKNOWN",
                        move_in_date=item.get('moveInDate', ''),
                        loan_availability=LoanAvailability(item.get('loanCode')).name if item.get('loanCode') else "UNKNOWN",
                        negotiable=item.get('negotiationFlagCode', 'N')[-1],
                        is_active=True,
                        last_seen=datetime.now()
                    )
                    self.session.add(property_info)
                    self.session.flush()

                    # PropertyInfo가 실제로 저장되었는지 확인
                    saved_property = self.session.query(PropertyInfo).filter_by(property_id=property_id).first()
                    if not saved_property:
                        raise Exception(f"PropertyInfo {property_id}가 저장되지 않았습니다.")

                    # 2.3 거래 정보 저장
                    trade_type = item.get('tradeTypeCode')
                    if trade_type == '30051A1':  # 매매
                        price = int(item.get('price1', 0) or 0) * 10000
                        if price >= 1000000000000:
                            logger.warning(f"매물 {property_id}의 가격이 너무 높습니다: {price}")
                            price = 999999999999
                        
                        sale = Sale(
                            property_id=property_id,  # property_id를 직접 사용
                            price=price,
                            end_date=item.get('endDate'),
                            transaction_date=item.get('transactionDate')
                        )
                        self.session.add(sale)
                    else:  # 임대
                        deposit = int(item.get('price1', 0) or 0) * 10000
                        monthly_rent = int(item.get('price2', 0) or 0) * 10000
                        
                        if deposit >= 1000000000000:
                            logger.warning(f"매물 {property_id}의 보증금이 너무 높습니다: {deposit}")
                            deposit = 999999999999
                        if monthly_rent >= 1000000000000:
                            logger.warning(f"매물 {property_id}의 월세가 너무 높습니다: {monthly_rent}")
                            monthly_rent = 999999999999
                        
                        rental = Rental(
                            property_id=property_id,  # property_id를 직접 사용
                            rental_type=TransactionType(trade_type).name,
                            deposit=deposit,
                            monthly_rent=monthly_rent
                        )
                        self.session.add(rental)
                    self.session.flush()

                    processed_count += 1
                self.session.commit()  # 각 매물의 트랜잭션 커밋
                    
            except Exception as e:
                logger.error(f"매물 {property_id} 처리 중 오류 발생: {str(e)}")
                self.session.rollback()
                continue
        
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