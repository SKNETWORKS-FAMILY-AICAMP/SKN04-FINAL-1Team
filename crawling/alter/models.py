from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column, Integer, String, Float, DateTime, Boolean, ForeignKey, 
                       Text, JSON, DECIMAL, CHAR, Enum as SQLEnum, Index, func, TypeDecorator)
from sqlalchemy.orm import relationship, remote
from datetime import datetime, timezone
import uuid
import json
from enums import (HeatingType, TransactionType, 
                  LoanAvailability, MoveInType, Gender, MessageType, NoticeStatus, DirectionType, BuildingUseType, PropertyType, NaverSubCategory)

class JSONEncodedDict(TypeDecorator):
    """JSON 데이터를 안전하게 처리하는 커스텀 타입"""
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return '{}'

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                return json.loads(value)
            except (ValueError, TypeError):
                return {}
        return {}

def default_json():
    return {}

Base = declarative_base()

class Address(Base):
    __tablename__ = 'addresses'
    __table_args__ = (
        Index('idx_area_name', 'area_name'),
    )
    
    address_id = Column(Integer, primary_key=True)
    area_name = Column(String(100), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    cultural_facilities = relationship("CulturalFacility", back_populates="address")
    cultural_festivals = relationship("CulturalFestival", back_populates="address")
    subway_stations = relationship("SubwayStation", back_populates="address")
    crime_stats = relationship("CrimeStats", back_populates="address")
    population_stats = relationship("PopulationStats", back_populates="address")
    distances = relationship("LocationDistance", back_populates="address")

class CulturalFacility(Base):
    __tablename__ = 'cultural_facilities'
    
    facility_id = Column(Integer, primary_key=True)
    address_id = Column(Integer, ForeignKey('addresses.address_id'))
    facility_name = Column(String(100), nullable=False)
    facility_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    address = relationship("Address", back_populates="cultural_facilities")

class CulturalFestival(Base):
    __tablename__ = 'cultural_festivals'
    
    festival_id = Column(Integer, primary_key=True)
    address_id = Column(Integer, ForeignKey('addresses.address_id'))
    festival_name = Column(String(100), nullable=False)
    begin_date = Column(String(10))
    end_date = Column(String(10))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    address = relationship("Address", back_populates="cultural_festivals")

class SubwayStation(Base):
    __tablename__ = 'subway_stations'
    
    station_id = Column(Integer, primary_key=True)
    address_id = Column(Integer, ForeignKey('addresses.address_id'))
    line_info = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    address = relationship("Address", back_populates="subway_stations")

class CrimeStats(Base):
    __tablename__ = 'crime_stats'
    
    stat_id = Column(Integer, primary_key=True)
    address_id = Column(Integer, ForeignKey('addresses.address_id'))
    reference_date = Column(String(8))
    total_population = Column(Float)
    crime_category = Column(String(50), nullable=False)
    crime_subcategory = Column(String(50), nullable=False)
    incident_count = Column(Integer, nullable=False)
    crime_rate = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    address = relationship("Address", back_populates="crime_stats")

class PopulationStats(Base):
    __tablename__ = 'population_stats'
    
    stat_id = Column(Integer, primary_key=True)
    address_id = Column(Integer, ForeignKey('addresses.address_id'))
    collection_time = Column(DateTime, nullable=False)
    population_level = Column(String(50))
    population_message = Column(Text)
    min_population = Column(Integer)
    max_population = Column(Integer)
    male_ratio = Column(Float)
    female_ratio = Column(Float)
    age_0_9_ratio = Column(Float)
    age_10s_ratio = Column(Float)
    age_20s_ratio = Column(Float)
    age_30s_ratio = Column(Float)
    age_40s_ratio = Column(Float)
    age_50s_ratio = Column(Float)
    age_60s_ratio = Column(Float)
    age_70s_ratio = Column(Float)
    resident_ratio = Column(Float)
    non_resident_ratio = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    address = relationship("Address", back_populates="population_stats")

class Location(Base):
    __tablename__ = "property_locations"
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, unique=True, nullable=False)
    sido = Column(String(20), nullable=False)
    sigungu = Column(String(20), nullable=False)
    dong = Column(String(20), nullable=True)
    jibun_main = Column(String(20), nullable=True)
    jibun_sub = Column(String(20), nullable=True)
    latitude = Column(Float)
    longitude = Column(Float)
    
    property = relationship("Property", back_populates="location", uselist=False)
    distances = relationship("LocationDistance", back_populates="property_location")

class LocationDistance(Base):
    __tablename__ = 'location_distances'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('property_locations.property_id'), nullable=False)
    address_id = Column(Integer, ForeignKey('addresses.address_id'), nullable=False)
    distance = Column(Float, nullable=False)
    
    property_location = relationship("Location", back_populates="distances")
    address = relationship("Address", back_populates="distances")

class User(Base):
    __tablename__ = "users"
    
    uuid = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    gender = Column(SQLEnum(Gender), nullable=False)
    age = Column(Integer, nullable=False)
    age_group = Column(String(10), nullable=False)
    desired_location = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    feedbacks = relationship("Feedback", back_populates="user")
    chat_logs = relationship("ChatLog", back_populates="user")
    favorites = relationship("Favorite", back_populates="user")
    user_actions = relationship("UserAction", back_populates="user")

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True)
    user_uuid = Column(CHAR(36), ForeignKey('users.uuid'), nullable=False)
    homepage_rating = Column(Integer, nullable=False)
    q1_accuracy = Column(Integer, nullable=False)
    q2_naturalness = Column(Integer, nullable=False)
    q3_resolution = Column(Integer, nullable=False)
    feedback_text = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    user = relationship("User", back_populates="feedbacks")

class Notice(Base):
    __tablename__ = "notices"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(CHAR(36), ForeignKey('users.uuid'), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime)
    status = Column(SQLEnum(NoticeStatus), nullable=False, default=NoticeStatus.ACTIVE)

class ChatLog(Base):
    __tablename__ = "chat_logs"
    
    id = Column(Integer, primary_key=True)
    user_uuid = Column(CHAR(36), ForeignKey('users.uuid'), nullable=False)
    session_id = Column(CHAR(36), nullable=False)
    message_type = Column(SQLEnum(MessageType), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    user = relationship("User", back_populates="chat_logs")

class UserAction(Base):
    __tablename__ = "user_actions"
    
    id = Column(Integer, primary_key=True)
    user_uuid = Column(CHAR(36), ForeignKey('users.uuid'))
    session_id = Column(CHAR(36), nullable=False)
    action_type = Column(String(50), nullable=False)
    action_time = Column(DateTime, nullable=False, server_default=func.now())
    page_url = Column(String(255), nullable=False)
    referrer_url = Column(String(255))
    device_info = Column(String(255), nullable=False)
    location = Column(String(255))
    event_details = Column(JSON)
    
    user = relationship("User", back_populates="user_actions")

class Property(Base):
    __tablename__ = "property_info"
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('property_locations.property_id'), unique=True, nullable=False)
    property_type = Column(SQLEnum(PropertyType), nullable=False)
    property_subtype = Column(SQLEnum(NaverSubCategory), nullable=False)
    building_name = Column(String(100), nullable=True)
    detail_address = Column(String(200), nullable=True)
    construction_date = Column(String(10))
    total_area = Column(DECIMAL(10,2), nullable=True)
    exclusive_area = Column(DECIMAL(10,2), nullable=True)
    land_area = Column(DECIMAL(10,2), nullable=True)
    on_Floor = Column(Integer, nullable=True)
    under_floor = Column(Integer, nullable=True)
    room_count = Column(Integer, nullable=True)
    bathroom_count = Column(Integer, nullable=True)
    parking_count = Column(Integer, nullable=True)
    heating_type = Column(SQLEnum(HeatingType), nullable=True, default=None)
    direction = Column(SQLEnum(DirectionType), nullable=True, default=None)
    purpose_type = Column(SQLEnum(BuildingUseType), nullable=True, default=None)
    current_usage = Column(String(100), nullable=True)
    recommended_usage = Column(String(100), nullable=True)
    facilities = Column(JSONEncodedDict, nullable=True, default=default_json)
    description = Column(Text, nullable=True)
    move_in_type = Column(SQLEnum(MoveInType), nullable=True)
    move_in_date = Column(String(10), nullable=True)
    loan_availability = Column(SQLEnum(LoanAvailability), nullable=True, default=None)
    negotiable = Column(String(2), default='N')
    photos = Column(JSONEncodedDict, nullable=True, default=default_json)
    update_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    inactive_reason = Column(String(200), nullable=True)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    location = relationship("Location", back_populates="property")
    rentals = relationship("Rental", back_populates="property")
    sales = relationship("Sale", back_populates="property")
    favorites = relationship("Favorite", back_populates="property")

    @property
    def facilities_dict(self):
        """facilities JSON 필드를 안전하게 가져오기"""
        return self.facilities if isinstance(self.facilities, dict) else {}

    @property
    def photos_list(self):
        """photos JSON 필드를 안전하게 가져오기"""
        return self.photos if isinstance(self.photos, dict) else {}

class Favorite(Base):
    __tablename__ = "favorites"
    
    id = Column(Integer, primary_key=True)
    user_uuid = Column(CHAR(36), ForeignKey('users.uuid'), nullable=False)
    item_id = Column(Integer, ForeignKey('property_info.property_id'), nullable=False)
    item_type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    user = relationship("User", back_populates="favorites")
    property = relationship("Property", back_populates="favorites")

class Rental(Base):
    __tablename__ = "rentals"
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('property_info.property_id'), unique=True, nullable=False)
    rental_type = Column(SQLEnum(TransactionType), nullable=False)
    deposit = Column(DECIMAL(10,2), nullable=False)
    monthly_rent = Column(DECIMAL(10,2), nullable=False)
    
    property = relationship("Property", back_populates="rentals")

class Sale(Base):
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('property_info.property_id'), unique=True, nullable=False)
    price = Column(DECIMAL(10,2), nullable=False)
    end_date = Column(DateTime)
    transaction_date = Column(DateTime)
    
    property = relationship("Property", back_populates="sales")

class APISearchData(Base):
    __tablename__ = 'api_search_data'
    
    id = Column(Integer, primary_key=True)
    api_name = Column(String(100), nullable=False)
    parameter = Column(String(500))
    response = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))