import json
import asyncio
import aiohttp
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect, text
import logging
from typing import List
from tqdm import tqdm
from utils import setup_logger, batch_process, retry_on_failure
from models import LoanAvailability, Base 
from enums import (SeoulDistrictCode, NaverSubCategory, HeatingType, CoolingType, 
                  MoveInType, LivingFacilityType, FacilityType, SecurityType, 
                  DirectionType, BuildingUseType, PropertyType)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import re
from sqlalchemy import inspect
from pathlib import Path
from sqlalchemy import event

# SQLAlchemy 로그 레벨 조정
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

# 로거 설정
main_logger = setup_logger('alter_main', 'logs/alter_main.log')
error_logger = setup_logger('alter_error', 'logs/alter_error.log', level=logging.ERROR)
db_logger = setup_logger('alter_db', 'logs/alter_db.log')

# 디버그 로그 추가
debug_logger = setup_logger('alter_debug', 'logs/alter_debug.log', level=logging.DEBUG)

# 프로젝트 루트 디렉토리 설정
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'real_estate.db'

debug_logger.info(f"BASE_DIR: {BASE_DIR}")
debug_logger.info(f"DB_PATH: {DB_PATH}")

# 비동기 엔진 설정
async_engine = create_async_engine(
    f'sqlite+aiosqlite:///{DB_PATH}',
    echo=False,
    connect_args={
        'timeout': 30,
        'check_same_thread': False,
        'isolation_level': 'IMMEDIATE'
    }
)

@event.listens_for(async_engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=-2000000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.execute("PRAGMA mmap_size=30000000000")
    cursor.execute("PRAGMA busy_timeout=60000")
    cursor.close()

# 비동기 세션 팩토리
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class PropertyProcessor:
    def __init__(self, session):
        self.session = session
        self.batch_size = 100
        
    @retry_on_failure(max_retries=3)
    def process_single_property(self, property_data: dict) -> bool:
        """단일 매물 처리 함수"""
        try:
            # 매물 처리 로직
            property_id = property_data.get('id')
            main_logger.info(f"Processing property {property_id}")
            return True
            
        except Exception as e:
            error_logger.error(
                f"Failed to process property {property_data.get('id')}: {str(e)}",
                exc_info=True
            )
            return False
    
    def process_batch(self, batch: List[dict]):
        """배치 처리 함수"""
        for property_data in batch:
            try:
                self.process_single_property(property_data)
            except Exception as e:
                error_logger.error(
                    f"Batch processing error for property {property_data.get('id')}: {str(e)}",
                    exc_info=True
                )
        
        # 배치 완료 후 커밋
        try:
            self.session.commit()
            db_logger.info(f"Successfully committed batch of {len(batch)} items")
        except Exception as e:
            self.session.rollback()
            db_logger.error(f"Failed to commit batch: {str(e)}", exc_info=True)
            raise
    
    def process_all(self, properties: List[dict]):
        """전체 매물 처리"""
        main_logger.info(f"Starting to process {len(properties)} properties")
        start_time = datetime.now()
        
        failed_items = batch_process(
            items=properties,
            batch_size=self.batch_size,
            process_func=self.process_batch,
            logger=main_logger
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        main_logger.info(
            f"Completed processing. Duration: {duration:.2f} seconds. "
            f"Failed items: {len(failed_items)}"
        )
        
        return failed_items

async def process_district(district_name, district_code, session, semaphore):
    """구별 매물 처리"""
    district_data = []
    total_items = 0
    page_no = 1
    
    headers = {
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.rter2.com',
        'referer': 'https://www.rter2.com/mapview',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }

    debug_logger.info(f"[{district_name}] 크롤링 시작")
    
    try:
        async with aiohttp.ClientSession(headers=headers) as client:
            async with AsyncSessionLocal() as db_session:
                while True:
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
                    
                    debug_logger.info(f"[{district_name}] 페이지 {page_no} 요청")
                    debug_logger.debug(f"Payload: {payload}")
                    
                    try:
                        async with client.post('https://www.rter2.com/hompyArticle/list', 
                                            data=payload) as response:
                            debug_logger.info(f"[{district_name}] 응답 상태 코드: {response.status}")
                            
                            if response.status == 200:
                                text = await response.text(encoding='utf-8')
                                debug_logger.debug(f"[{district_name}] 응답 데이터: {text[:200]}...")  # 처음 200자만 로깅
                                
                                try:
                                    data = json.loads(text)
                                    if 'result' in data and 'list' in data['result']:
                                        items = data['result']['list']
                                        if not items:
                                            debug_logger.info(f"[{district_name}] 더 이상 데이터가 없음")
                                            break
                                            
                                        debug_logger.info(f"[{district_name}] {len(items)}개 매물 발견")
                                        
                                        async with db_session.begin():
                                            chunk_results = await process_district_chunk(
                                                client, district_name, items, semaphore, db_session
                                            )
                                            if chunk_results:
                                                district_data.extend(items)
                                        
                                        total_items += len(items)
                                        if page_no % 5 == 0:
                                            main_logger.info(
                                                f"[{district_name}] {total_items}개 매물 수집 중... (페이지 {page_no})"
                                            )
                                        page_no += 1
                                        await asyncio.sleep(0.5)
                                    else:
                                        debug_logger.warning(f"[{district_name}] 응답 데이터 형식이 올바르지 않음")
                                        break
                                        
                                except json.JSONDecodeError as e:
                                    error_logger.error(f"[{district_name}] JSON 파싱 오류: {str(e)}")
                                    debug_logger.error(f"[{district_name}] 원본 텍스트: {text[:500]}...")  # 처음 500자만 로깅
                                    continue
                                    
                            else:
                                error_logger.error(f"[{district_name}] HTTP 오류: {response.status}")
                                debug_logger.error(f"[{district_name}] 응답 헤더: {response.headers}")
                                await asyncio.sleep(1)
                                continue
                                    
                    except Exception as e:
                        error_logger.error(f"[{district_name}] 요청 처리 오류: {str(e)}")
                        debug_logger.exception(f"[{district_name}] 상세 오류:")
                        await asyncio.sleep(1)
                        continue
                        
    except Exception as e:
        error_logger.error(f"[{district_name}] 세션 오류: {str(e)}")
        debug_logger.exception(f"[{district_name}] 상세 세션 오류:")
            
    main_logger.info(f"[{district_name}] 수집 완료: 총 {total_items}개 매물")
    return district_name, district_data

async def process_all_districts():
    """모든 구 처리"""
    connector = aiohttp.TCPConnector(
        ssl=False,
        ttl_dns_cache=300,
        limit=30,
        force_close=True,
        enable_cleanup_closed=True,
        limit_per_host=5
    )
    
    timeout = aiohttp.ClientTimeout(
        total=1800,
        connect=60,
        sock_read=120
    )
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(
            ssl=False,
            ttl_dns_cache=300,
            limit=30,
            force_close=True,
            enable_cleanup_closed=True,
            limit_per_host=5,
            # proxy="http://172.31.7.25:8080"
        ),
        timeout=timeout,
        headers={
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Connection': 'keep-alive',
            'Referer': 'https://www.rter2.com',
            'Origin': 'https://www.rter2.com',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        }
    ) as session:
        semaphore = asyncio.Semaphore(3)
        
        total_progress = tqdm(
            total=len(SeoulDistrictCode),
            desc="전체 진행률",
            unit="구",
            ncols=100
        )
        
        async def process_with_progress(district_name, SeoulDistrictCode, idx):
            result = await process_district(district_name, SeoulDistrictCode, session, semaphore)
            total_progress.update(1)
            total_progress.set_description(f"현재: {district_name}")
            return result
        
        tasks = [
            process_with_progress(district.name, district.value, idx)
            for idx, district in enumerate(SeoulDistrictCode)
        ]
        
        results = await asyncio.gather(*tasks)
        total_progress.close()
        return results

async def get_article_detail(client, article_id):
    """매물 상세 정보 가져오기"""
    url = f"https://www.rter2.com/hompyArticle/{article_id}"
    
    headers = {
        'accept': '*/*',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/json;charset=UTF-8',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'referer': f'https://www.rter2.com/hompyArticle/detail/{article_id}',
        'origin': 'https://www.rter2.com'
    }
    
    max_retries = 5  # 재시도 횟수 증가
    base_timeout = 2  # 기본 대기 시간

    for attempt in range(max_retries):
        try:
            timeout = aiohttp.ClientTimeout(total=30)  # 요청 전체 타임아웃 30초로 설정
            async with client.post(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    text = await response.text(encoding='utf-8')
                    try:
                        data = json.loads(text)
                        if data and isinstance(data, dict):
                            return data
                            
                    except json.JSONDecodeError as e:
                        error_logger.error(f"JSON 파싱 오류 (ID: {article_id}): {str(e)}")
                        
                elif response.status == 429:  # Rate limit
                    wait_time = base_timeout * (2 ** attempt)  # 지수 백오프
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    error_logger.error(f"API 오류 (ID: {article_id}): Status {response.status}")
                    
        except asyncio.TimeoutError:
            wait_time = base_timeout * (2 ** attempt)
            error_logger.error(f"타임아웃 발생 (ID: {article_id}), {attempt+1}번째 시도, {wait_time}초 대기")
            await asyncio.sleep(wait_time)
            continue
            
        except Exception as e:
            wait_time = base_timeout * (2 ** attempt)
            error_logger.error(f"요청 실패 (ID: {article_id}): {str(e)}")
            await asyncio.sleep(wait_time)
            continue
            
    return None

def process_trade_type(detail_item):
    """매매/임대 구분 처리"""
    trade_type = detail_item.get('tradeTypeCode')
    
    # 매매인 경우
    if trade_type == '30051A1':
        return {
            'type': 'sale',
            'data': {
                'price': detail_item.get('price1', 0) * 10000 if detail_item.get('price1') else 0,  # 매매가
            }
        }
    # 임대인 경우 (전세/월세/단기임대)
    else:
        return {
            'type': 'rental',
            'data': {
                'deposit': detail_item.get('price1') * 10000  if detail_item.get('price1') else 0,  # 보증금
                'monthly_rent': detail_item.get('price2') * 10000 if detail_item.get('price2') else 0,  # 월세
                'right_price': detail_item.get('rightPrice') * 10000 if detail_item.get('rightPrice') else 0,  # 권리금
                'rental_type': trade_type,  # 30051B1: 전세, 30051B2: 월세, 30051B3: 단기임대
            }
        }

async def process_district_chunk(client, district_name, items, semaphore, db_session):
    """구별 청크 처리"""
    if not items:
        return True
        
    async with semaphore:
        try:
            # SQLite 최적화 설정
            await db_session.execute(text('PRAGMA journal_mode=WAL'))  # Write-Ahead Logging 모드
            await db_session.execute(text('PRAGMA synchronous=NORMAL'))  # 동기화 수준 조정
            await db_session.execute(text('PRAGMA cache_size=-2000000'))  # 캐시 크기 약 2GB로 설정
            await db_session.execute(text('PRAGMA temp_store=MEMORY'))  # 임시 저장소를 메모리로 설정
            await db_session.execute(text('PRAGMA mmap_size=30000000000'))  # 메모리 매핑 크기 증가
            await db_session.execute(text('PRAGMA busy_timeout=60000'))  # 타임아웃 설정
            
            # 상세 정보 요청을 병렬로 처리
            async def get_detail_with_retry(item):
                """매물 상세 정보 가져오기 (재시도 로직 포함)"""
                max_retries = 7
                base_timeout = 3
                
                for attempt in range(max_retries):
                    try:
                        timeout = aiohttp.ClientTimeout(total=60)
                        detail = await get_article_detail(client, item['seq'])
                        
                        # 단계별로 안전하게 데이터 추출
                        result = detail.get('result', {}) if detail else {}
                        detail_item = result.get('item', {})
                        construction_info_list = result.get('constructionInfoList', [])
                        
                        # 준공일 정보 추출
                        use_approve_day = None
                        if construction_info_list and isinstance(construction_info_list, list):
                            first_construction = construction_info_list[0] if construction_info_list else {}
                            use_approve_day = first_construction.get('useApproveDay')
                        
                        # 상세 정보가 있는 경우에만 처리
                        if detail_item and isinstance(detail_item, dict):
                            detail_item['useApproveDay'] = use_approve_day
                            return item.get('seq'), detail_item
                            
                    except Exception as e:
                        wait_time = base_timeout * (2 ** attempt)
                        error_logger.error(f"상세 정보 요청 실패 (ID: {item.get('seq', 'unknown')}, 시도: {attempt+1}/{max_retries}): {str(e)}")
                        await asyncio.sleep(wait_time)
                        continue
                        
                return item.get('seq'), None
            
            # 배치 크기 감소 및 대기 시간 증가
            batch_size = 50  # 100에서 50으로 감소
            
            # 데이터 준비
            all_details = {}
            location_data_list = []
            property_data_list = []
            sale_data_list = []
            rental_data_list = []

            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                details = await asyncio.gather(*[
                    get_detail_with_retry(item) for item in batch
                ])
                all_details.update(dict(details))
                await asyncio.sleep(0.5)  # 0.1에서 0.5초로 증가

            # 기존 매물 ID 확인
            property_ids = [item['seq'] for item in items]
            placeholders = ','.join(f':id{i}' for i in range(len(property_ids)))
            params = {f'id{i}': id_ for i, id_ in enumerate(property_ids)}
            
            existing_properties = await db_session.execute(
                text(f"""
                    SELECT property_id, is_active 
                    FROM property_info 
                    WHERE property_id IN ({placeholders})
                """),
                params
            )
            existing_ids = {row[0]: row[1] for row in existing_properties}

            # 데이터 처리
            for item in items:
                try:
                    detail_item = all_details.get(item['seq'])
                    
                    # 기존 매물이고 활성 상태이면서 detail_item이 없는 경우만 비활성화
                    if item['seq'] in existing_ids:
                        if existing_ids[item['seq']] and not detail_item:  # 활성 상태이면서 detail_item이 없는 경우만 비활성화
                            await db_session.execute(
                                text("""
                                    UPDATE property_info 
                                    SET is_active = FALSE,
                                        inactive_reason = :reason,
                                        last_seen = :last_seen
                                    WHERE property_id = :property_id
                                """),
                                {
                                    'property_id': item['seq'],
                                    'reason': 'detail_item is None',
                                    'last_seen': datetime.now(timezone.utc)
                                }
                            )
                        continue  # 기존 매물은 건너뛰기

                    # 새로운 매물인 경우만 처리
                    if not detail_item:
                        property_data_list.append({
                            'property_id': item['seq'],
                            'property_type': '',
                            'property_subtype': '',
                            'building_name': '',
                            'detail_address': '',
                            'construction_date': '',
                            'total_area': 0,
                            'exclusive_area': 0,
                            'land_area': 0,
                            'on_Floor': 0,
                            'under_floor': 0,
                            'room_count': 0,
                            'bathroom_count': 0,
                            'parking_count': 0,
                            'heating_type': '',
                            'direction': '',
                            'purpose_type': '',
                            'current_usage': '',
                            'recommended_usage': '',
                            'facilities': None,
                            'description': '',
                            'photos': None,
                            'move_in_type': '',
                            'move_in_date': '',
                            'loan_availability': '',
                            'negotiable': 'N',
                            'update_count': 0,
                            'is_active': False,
                            'inactive_reason': 'detail_item is None',
                            'first_seen': datetime.now(timezone.utc),
                            'last_seen': datetime.now(timezone.utc)
                        })
                        
                        # 기본 위치 정보만 저장
                        legal_dong = item.get('legalDong', {})
                        location_data_list.append({
                            'property_id': item['seq'],
                            'sido': legal_dong.get('sidoName', ''),
                            'sigungu': legal_dong.get('gugunName', district_name),
                            'dong': legal_dong.get('dongName', ''),
                            'jibun_main': '',
                            'jibun_sub': '',
                            'latitude': 0,
                            'longitude': 0
                        })
                        continue
                        
                    legal_dong = item.get('legalDong', {})
                    
                    # 좌표 정보 추출
                    coordinates = [0, 0]
                    if 'center' in detail_item:
                        center = detail_item['center']
                        coordinates = center.get('coordinates', [0, 0])
                    elif 'danji' in detail_item:
                        danji = detail_item['danji']
                        if 'boundCenter' in danji:
                            coordinates = danji['boundCenter'].get('coordinates', [0, 0])
                        elif 'manualCenter' in danji:
                            coordinates = danji['manualCenter'].get('coordinates', [0, 0])

                    # 좌표값 변환
                    try:
                        longitude = float(coordinates[0]) if coordinates and len(coordinates) > 0 else 0.0
                        latitude = float(coordinates[1]) if coordinates and len(coordinates) > 1 else 0.0
                    except (TypeError, ValueError):
                        longitude, latitude = 0.0, 0.0

                    # Location 데이터 준비
                    location_data_list.append({
                        'property_id': item['seq'],
                        'sido': legal_dong.get('sidoName', ''),
                        'sigungu': legal_dong.get('gugunName', district_name),
                        'dong': legal_dong.get('dongName', ''),
                        'jibun_main': detail_item.get('jibunMainNumber', ''),
                        'jibun_sub': detail_item.get('jibunSubNumber', ''),
                        'latitude': latitude,
                        'longitude': longitude
                    })

                    # Property 데이터 준비
                    property_data = {
                        'property_id': item['seq'],
                        'property_type': PropertyType(item.get('categoryCode')).name if item.get('categoryCode') else "NULL",
                        'property_subtype': NaverSubCategory(detail_item.get('subCategoryCode')).name if detail_item.get('subCategoryCode') else "NULL",
                        'building_name': detail_item.get('buildingName', ''),
                        'detail_address': detail_item.get('detailAddress', ''),
                        'construction_date': detail_item.get('useApproveDay', ''),
                        'total_area': detail_item.get('space1', 0),
                        'exclusive_area': detail_item.get('space2', 0),
                        'land_area': detail_item.get('space3', 0),
                        'on_Floor': detail_item.get('onFloorCount', 0),
                        'under_floor': detail_item.get('underFloorCount', 0),
                        'room_count': detail_item.get('room', 0),
                        'bathroom_count': detail_item.get('restroom', 0),
                        'parking_count': detail_item.get('parkingCount', 0),
                        'heating_type': HeatingType(detail_item.get('heatTypeCode')).name if detail_item.get('heatTypeCode') else "NULL",
                        'direction': DirectionType(detail_item.get('directionCode')).name if detail_item.get('directionCode') else "NULL",
                        'purpose_type': BuildingUseType(detail_item.get('lawUsageCode')).name if detail_item.get('lawUsageCode') else "NULL",
                        'current_usage': detail_item.get('currentUsage', ''),
                        'recommended_usage': detail_item.get('recommendUsage', ''),
                        'facilities': json.dumps({
                            'cooling': process_facilities(detail_item.get('facilitiesAircon', ''), CoolingType),
                            'living': process_facilities(detail_item.get('facilitiesLife', ''), LivingFacilityType),
                            'security': process_facilities(detail_item.get('facilitiesSecurity', ''), SecurityType),
                            'etc': process_facilities(detail_item.get('facilitiesEtc', ''), FacilityType)
                        }),
                        'description': detail_item.get('description', ''),
                        'photos': process_photos(detail_item.get('photoList', [])),
                        'move_in_type': MoveInType(detail_item.get('moveInTypeCode')).name if detail_item.get('moveInTypeCode') else "NULL",
                        'move_in_date': detail_item.get('moveInDate', ''),
                        'loan_availability': LoanAvailability(detail_item.get('loanCode', '')).name if detail_item.get('loanCode') else "NULL",
                        'negotiable': detail_item.get('negotiationFlagCode', 'N')[-1],
                        'update_count': 0,
                        'is_active': True,
                        'inactive_reason': None,
                        'first_seen': datetime.now(timezone.utc),
                        'last_seen': datetime.now(timezone.utc)
                    }
                    property_data_list.append(property_data)

                    # Sale/Rental 데이터 준비
                    trade_info = process_trade_type(detail_item)
                    if trade_info['type'] == 'sale':
                        sale_data_list.append({
                            'property_id': item['seq'],
                            'price': trade_info['data']['price'],
                            'end_date': None,
                            'transaction_date': None
                        })
                    else:
                        rental_data_list.append({
                            'property_id': item['seq'],
                            'rental_type': trade_info['data']['rental_type'],
                            'deposit': trade_info['data']['deposit'],
                            'monthly_rent': trade_info['data']['monthly_rent']
                        })

                except Exception as e:
                    error_logger.error(f"[{district_name}] Error processing item {item.get('seq', 'unknown')}: {str(e)}")
                    continue

            # DB 작업
            try:
                # Location 데이터 삽입
                if location_data_list:
                    await db_session.execute(
                        text("""
                            INSERT INTO property_locations 
                            (property_id, sido, sigungu, dong, jibun_main, jibun_sub, 
                             latitude, longitude)
                            VALUES (:property_id, :sido, :sigungu, :dong, :jibun_main, :jibun_sub, 
                                    :latitude, :longitude)
                            ON CONFLICT(property_id) DO UPDATE SET
                                sido = excluded.sido,
                                sigungu = excluded.sigungu, 
                                dong = excluded.dong,
                                jibun_main = excluded.jibun_main,
                                jibun_sub = excluded.jibun_sub,
                                latitude = excluded.latitude,
                                longitude = excluded.longitude
                        """),
                        location_data_list
                    )
                # Property 데이터 삽입
                if property_data_list:
                    await db_session.execute(
                        text("""
                            INSERT INTO property_info 
                            (property_id, property_type, property_subtype, 
                             building_name, detail_address, construction_date, total_area, exclusive_area,
                             land_area, on_Floor, under_floor, room_count, bathroom_count, parking_count,
                             heating_type, direction, purpose_type, current_usage, recommended_usage,
                             facilities, description, photos, move_in_type, move_in_date, loan_availability,
                             negotiable, update_count, is_active, inactive_reason, first_seen, last_seen)
                            VALUES (:property_id, :property_type, :property_subtype,
                                    :building_name, :detail_address, :construction_date, :total_area, :exclusive_area,
                                    :land_area, :on_Floor, :under_floor, :room_count, :bathroom_count, :parking_count,
                                    :heating_type, :direction, :purpose_type, :current_usage, :recommended_usage,
                                    :facilities, :description, :photos, :move_in_type, :move_in_date, :loan_availability,
                                    :negotiable, :update_count, :is_active, :inactive_reason, :first_seen, :last_seen)
                            ON CONFLICT(property_id) DO UPDATE SET
                                property_type = excluded.property_type,
                                property_subtype = excluded.property_subtype,
                                building_name = excluded.building_name,
                                detail_address = excluded.detail_address,
                                construction_date = excluded.construction_date,
                                total_area = excluded.total_area,
                                exclusive_area = excluded.exclusive_area,
                                land_area = excluded.land_area,
                                on_Floor = excluded.on_Floor,
                                under_floor = excluded.under_floor,
                                room_count = excluded.room_count,
                                bathroom_count = excluded.bathroom_count,
                                parking_count = excluded.parking_count,
                                heating_type = excluded.heating_type,
                                direction = excluded.direction,
                                purpose_type = excluded.purpose_type,
                                current_usage = excluded.current_usage,
                                recommended_usage = excluded.recommended_usage,
                                facilities = excluded.facilities,
                                description = excluded.description,
                                photos = excluded.photos,
                                move_in_type = excluded.move_in_type,
                                move_in_date = excluded.move_in_date,
                                loan_availability = excluded.loan_availability,
                                negotiable = excluded.negotiable,
                                update_count = COALESCE((SELECT update_count FROM property_info 
                                                       WHERE property_id = :property_id), 0) + 1,
                                is_active = excluded.is_active,
                                inactive_reason = excluded.inactive_reason,
                                last_seen = excluded.last_seen
                        """),
                        property_data_list
                    )
                # Sale 데이터 삽입
                if sale_data_list:
                    await db_session.execute(
                        text("""
                            INSERT INTO sales 
                            (property_id, price, end_date, transaction_date)
                            VALUES (:property_id, :price, :end_date, :transaction_date)
                            ON CONFLICT(property_id) DO UPDATE SET
                                price = excluded.price,
                                end_date = excluded.end_date,
                                transaction_date = excluded.transaction_date
                        """),
                        sale_data_list
                    )
                # Rental 데이터 삽입
                if rental_data_list:
                    await db_session.execute(
                        text("""
                            INSERT INTO rentals 
                            (property_id, rental_type, deposit, monthly_rent)
                            VALUES (:property_id, :rental_type, :deposit, :monthly_rent)
                            ON CONFLICT(property_id) DO UPDATE SET
                                rental_type = excluded.rental_type,
                                deposit = excluded.deposit,
                                monthly_rent = excluded.monthly_rent
                        """),
                        rental_data_list
                    )

                return True

            except Exception as e:
                error_logger.error(f"[{district_name}] Database Error: {str(e)}")
                return False

        except Exception as e:
            error_logger.error(f"[{district_name}] Chunk Error: {str(e)}")
            return False

async def check_tables(conn):
    """테이블 존재 여부 확인"""
    def _check_tables(connection):
        inspector = inspect(connection)
        return inspector.get_table_names()
    
    return await conn.run_sync(_check_tables)

async def create_tables():
    """테이블 생성"""
    try:
        async with async_engine.begin() as conn:
            # 테이블 존재 여부 확인
            existing_tables = await check_tables(conn)
            
            # 필요한 테이블 목록
            required_tables = ['property_info', 'property_locations', 'sales', 'rentals']
            
            # 누락된 테이블 확인
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:  # 누락된 테이블이 있으면 생성
                main_logger.info(f"누락된 테이블 생성: {missing_tables}")
                await conn.run_sync(Base.metadata.create_all)
                main_logger.info("테이블 생성 완료")
            else:
                main_logger.info(f"모든 테이블이 이미 존재합니다: {existing_tables}")
                
    except Exception as e:
        error_logger.error(f"테이블 생성/확인 중 오류: {str(e)}")
        raise

async def initialize_database():
    """데이터베이스 초기화"""
    try:
        # DB 파일이 없으면 생성
        if not DB_PATH.exists():
            main_logger.info(f"새로운 데이터베이스 생성: {DB_PATH}")
            DB_PATH.touch()

        # 테이블 생성
        await create_tables()

    except Exception as e:
        error_logger.error(f"데이터베이스 초기화 중 오류: {str(e)}")
        raise

def process_facilities(facilities_data, enum_type):
    """시설 정보를 문자열로 변환"""
    if not facilities_data:
        return None
    try:
        # 각 값을 enum name으로 변환하고 쉼표로 구분
        facility_names = []
        # JSON 문자열로 들어올 경우 처리
        if isinstance(facilities_data, str):
            try:
                facilities_data = json.loads(facilities_data.replace('\\', ''))
            except json.JSONDecodeError:
                pass
                
        # 리스트로 변환
        if isinstance(facilities_data, str):
            facilities_data = [facilities_data]
        elif not isinstance(facilities_data, list):
            facilities_data = []
            
        for value in facilities_data:
            try:
                facility_names.append(enum_type(value).name)
            except (ValueError, TypeError):
                continue
                
        return ','.join(facility_names) if facility_names else None
    except Exception:
        return None

def process_photos(photo_list):
    """사진 URL 리스트 처리"""
    if not photo_list:
        return None
    try:
        # URL만 추출하여 리스트로 만들기
        photo_urls = [photo['url'] for photo in photo_list]
        # 쉼표로 구분된 문자열로 변환
        return ','.join(photo_urls)
    except Exception:
        return None

def main():
    try:
        # 데이터베이스 초기화
        asyncio.run(initialize_database())
        
        # 크롤링 실행
        asyncio.run(process_all_districts())
            
    except Exception as e:
        error_logger.error(f"실행 중 오류: {str(e)}")
        return

if __name__ == "__main__":
    main()