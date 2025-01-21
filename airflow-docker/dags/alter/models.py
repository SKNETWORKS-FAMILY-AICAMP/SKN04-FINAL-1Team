from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column, Integer, String, Float, DateTime, ForeignKey, 
                       Text, DECIMAL, Boolean, JSON, BigInteger, Numeric, Index, UniqueConstraint)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from sqlalchemy.types import TypeDecorator, String
import json

Base = declarative_base()

class Address(Base):
    __tablename__ = 'addresses'
    __table_args__ = {'schema': 'realestate'}
    
    id = Column(Integer, primary_key=True)
    area_name = Column(String(100), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    cultural_facilities = relationship("CulturalFacility", back_populates="address")
    cultural_festivals = relationship("CulturalFestival", back_populates="address")
    subway_stations = relationship("SubwayStation", back_populates="address")
    crime_stats = relationship("CrimeStats", back_populates="address")
    distances = relationship("LocationDistance", back_populates="address")

class CulturalFacility(Base):
    __tablename__ = 'cultural_facilities'
    __table_args__ = {'schema': 'realestate'}
    
    id = Column(Integer, primary_key=True)
    address_id = Column(Integer, ForeignKey('realestate.addresses.id'))
    facility_name = Column(String(255))
    facility_type = Column(String(100))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    address = relationship("Address", back_populates="cultural_facilities")

class CulturalFestival(Base):
    __tablename__ = 'cultural_festivals'
    __table_args__ = {'schema': 'realestate'}
    
    id = Column(Integer, primary_key=True)
    address_id = Column(Integer, ForeignKey('realestate.addresses.id'))
    festival_name = Column(String(255))
    start_date = Column(String(10))
    end_date = Column(String(10))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    address = relationship("Address", back_populates="cultural_festivals")

class SubwayStation(Base):
    __tablename__ = 'subway_stations'
    __table_args__ = {'schema': 'realestate'}
    
    id = Column(Integer, primary_key=True)
    address_id = Column(Integer, ForeignKey('realestate.addresses.id'))
    line_info = Column(String(50))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    address = relationship("Address", back_populates="subway_stations")

class CrimeStats(Base):
    __tablename__ = 'crime_stats'
    __table_args__ = {'schema': 'realestate'}
    
    id = Column(Integer, primary_key=True)
    address_id = Column(Integer, ForeignKey('realestate.addresses.id'))
    reference_date = Column(String(8))
    total_population = Column(Float)
    crime_category = Column(String(50), nullable=False)
    crime_subcategory = Column(String(50), nullable=False)
    incident_count = Column(Integer, nullable=False)
    crime_rate = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    address = relationship("Address", back_populates="crime_stats")

class PropertyLocation(Base):
    __tablename__ = 'property_locations'
    __table_args__ = {'schema': 'realestate'}
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, unique=True, nullable=False)
    sido = Column(String(20), nullable=False)
    sigungu = Column(String(20), nullable=False)
    dong = Column(String(20))
    jibun_main = Column(String(20))
    jibun_sub = Column(String(20))
    latitude = Column(Float)
    longitude = Column(Float)
    
    property = relationship("PropertyInfo", back_populates="location", uselist=False)
    distances = relationship("LocationDistance", back_populates="property_location")

class JSONType(TypeDecorator):
    """JSON 타입을 처리하는 커스텀 타입"""
    impl = String
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value, ensure_ascii=False)
        return None
        
    def process_result_value(self, value, dialect):
        if value is not None:
            # JSON 문자열로 들어올 경우 처리
            if isinstance(value, str):
                try:
                    value = value.replace('\\', '')
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return value
        return None

class PropertyInfo(Base):
    __tablename__ = 'property_info'
    __table_args__ = {'schema': 'realestate'}
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('realestate.property_locations.property_id'), unique=True, nullable=False)
    property_type = Column(String(50), nullable=False)
    property_subtype = Column(String(50), nullable=False)
    building_name = Column(String(100))
    detail_address = Column(String(200))
    construction_date = Column(String(10))
    total_area = Column(DECIMAL(10,2))
    exclusive_area = Column(DECIMAL(10,2))
    land_area = Column(DECIMAL(10,2))
    on_floor = Column(Integer)
    under_floor = Column(Integer)
    room_count = Column(Integer)
    bathroom_count = Column(Integer)
    parking_count = Column(Integer)
    heating_type = Column(String(50))
    direction = Column(String(50))
    purpose_type = Column(String(50))
    current_usage = Column(String(100))
    recommended_usage = Column(String(100))
    facilities = Column(JSONType)
    description = Column(Text)
    move_in_type = Column(String(50))
    move_in_date = Column(String(10))
    loan_availability = Column(String(50))
    negotiable = Column(String(2), default='N')
    photos = Column(JSON, default={})
    update_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    inactive_reason = Column(String(200))
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    location = relationship("PropertyLocation", back_populates="property")
    rentals = relationship("Rental", back_populates="property")
    sales = relationship("Sale", back_populates="property")

class Rental(Base):
    __tablename__ = 'rentals'
    __table_args__ = {'schema': 'realestate'}
    
    id = Column(Integer, primary_key=True)
    property_id = Column(BigInteger, ForeignKey('realestate.property_info.property_id'), unique=True, nullable=False)
    rental_type = Column(String)
    deposit = Column(BigInteger, default=0)
    monthly_rent = Column(BigInteger, default=0)
    
    property = relationship("PropertyInfo", back_populates="rentals")

class Sale(Base):
    __tablename__ = 'sales'
    __table_args__ = {'schema': 'realestate'}
    
    id = Column(Integer, primary_key=True)
    property_id = Column(BigInteger, ForeignKey('realestate.property_info.property_id'), unique=True, nullable=False)
    price = Column(BigInteger, default=0)
    end_date = Column(String)
    transaction_date = Column(String)
    
    property = relationship("PropertyInfo", back_populates="sales")

class LocationDistance(Base):
    __tablename__ = 'location_distances'
    __table_args__ = (
        Index('idx_location_distances_property', 'property_id'),
        Index('idx_location_distances_address', 'address_id'),
        UniqueConstraint('property_id', 'address_id', name='uq_property_address'),
        {'schema': 'realestate'}
    )
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('realestate.property_locations.property_id'), nullable=False)
    address_id = Column(Integer, ForeignKey('realestate.addresses.id'), nullable=False)
    distance = Column(Float, nullable=False)  # 미터 단위
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    property_location = relationship("PropertyLocation", back_populates="distances")
    address = relationship("Address", back_populates="distances")