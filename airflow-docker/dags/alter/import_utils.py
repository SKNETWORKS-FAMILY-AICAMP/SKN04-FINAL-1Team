from sqlalchemy.orm import Session
import pandas as pd
from datetime import datetime
import logging
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError
from alter.models import (
    Address, 
    CulturalFacility, 
    CulturalFestival, 
    CrimeStats,
    SubwayStation
)
from alter.db_config import get_session, provide_session

logger = logging.getLogger(__name__)

def get_or_create_address(session, area_name, latitude=None, longitude=None):
    """주소 가져오기 또는 생성"""
    try:
        address = session.query(Address).filter_by(area_name=area_name).first()
        if address:
            if latitude and longitude and (not address.latitude or not address.longitude):
                address.latitude = latitude
                address.longitude = longitude
                session.flush()
        else:
            address = Address(
                area_name=area_name,
                latitude=latitude,
                longitude=longitude
            )
            session.add(address)
            session.flush()
        return address
    except Exception as e:
        logger.error(f"주소 처리 중 오류: {str(e)}")
        raise

def import_with_address(process_func):
    """주소 정보와 함께 데이터를 가져오는 데코레이터"""
    @wraps(process_func)
    def wrapper(*args, **kwargs):
        try:
            session = get_session()
            try:
                data_list = process_func(*args, **kwargs)
                
                for data in data_list:
                    try:
                        # 주소 처리
                        address = get_or_create_address(
                            session,
                            area_name=data['area_name'],
                            latitude=data.get('FCLTY_LA'),
                            longitude=data.get('FCLTY_LO')
                        )
                        
                        # 데이터 처리 함수 호출
                        process_func(data, address.address_id, session)
                        
                    except Exception as e:
                        logger.error(f"데이터 처리 중 오류: {str(e)}")
                        session.rollback()
                        continue
                        
                session.commit()
                return True
                
            except SQLAlchemyError as e:
                logger.error(f"데이터베이스 오류: {str(e)}")
                session.rollback()
                return False
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"전체 처리 중 오류: {str(e)}")
            return False
            
    return wrapper

def get_data_by_address(address_id, model_class):
    """주소 ID로 데이터 조회"""
    session = get_session()
    try:
        return session.query(model_class).filter_by(address_id=address_id).all()
    finally:
        session.close()

def process_cultural_festival_data(festival_data, address_id, session):
    """문화축제 데이터 처리"""
    try:
        festival = CulturalFestival(
            address_id=address_id,
            festival_name=festival_data['festival_name'],
            begin_date=festival_data.get('begin_date'),
            end_date=festival_data.get('end_date')
        )
        session.add(festival)
        return True
        
    except Exception as e:
        logger.error(f"문화축제 데이터 처리 중 오류: {str(e)}")
        raise

def process_subway_data(subway_data, address_id, session):
    """지하철역 데이터 처리"""
    try:
        station = SubwayStation(
            address_id=address_id,
            line_info=subway_data.get('line_info')
        )
        session.add(station)
        return True
        
    except Exception as e:
        logger.error(f"지하철역 처리 오류: {str(e)}")
        raise

def process_cultural_facility_data(facility_data, address_id, session):
    """문화시설 데이터 처리"""
    try:
        facility = CulturalFacility(
            address_id=address_id,
            facility_name=facility_data['facility_name'],
            facility_type=facility_data.get('facility_type', '영화관')
        )
        session.add(facility)
        return True
        
    except Exception as e:
        logger.error(f"문화시설 처리 오류: {str(e)}")
        raise

def process_crime_stats_data(crime_data, address_id, session):
    """범죄 통계 데이터 처리"""
    try:
        stats = CrimeStats(
            address_id=address_id,
            crime_category=crime_data['crime_category'],
            crime_subcategory=crime_data['crime_subcategory'],
            incident_count=crime_data['incident_count'],
            reference_date=crime_data.get('reference_date'),
            total_population=crime_data.get('total_population'),
            crime_rate=crime_data.get('crime_rate')
        )
        session.add(stats)
        return True
        
    except Exception as e:
        logger.error(f"범죄 통계 처리 오류: {str(e)}")
        raise
