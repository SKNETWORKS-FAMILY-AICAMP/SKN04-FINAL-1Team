-- PostGIS 확장 설치
CREATE EXTENSION IF NOT EXISTS postgis;

-- realestate 스키마 생성
CREATE SCHEMA IF NOT EXISTS realestate;

-- addresses 테이블 생성
CREATE TABLE IF NOT EXISTS realestate.addresses (
    id SERIAL PRIMARY KEY,
    area_name VARCHAR(100) NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_area_name ON realestate.addresses(area_name);

-- property_locations 테이블 생성
CREATE TABLE IF NOT EXISTS realestate.property_locations (
    id SERIAL PRIMARY KEY,
    property_id INTEGER UNIQUE NOT NULL,
    sido VARCHAR(20) NOT NULL,
    sigungu VARCHAR(20) NOT NULL,
    dong VARCHAR(20),
    jibun_main VARCHAR(20),
    jibun_sub VARCHAR(20),
    latitude FLOAT,
    longitude FLOAT
);

-- property_info 테이블 생성
CREATE TABLE IF NOT EXISTS realestate.property_info (
    id SERIAL PRIMARY KEY,
    property_id INTEGER REFERENCES realestate.property_locations(property_id) UNIQUE NOT NULL,
    property_type VARCHAR(50) NOT NULL,
    property_subtype VARCHAR(50) NOT NULL,
    building_name VARCHAR(100),
    detail_address VARCHAR(200),
    construction_date VARCHAR(10),
    total_area DECIMAL(10,2),
    exclusive_area DECIMAL(10,2),
    land_area DECIMAL(10,2),
    on_floor INTEGER,
    under_floor INTEGER,
    room_count INTEGER,
    bathroom_count INTEGER,
    parking_count INTEGER,
    heating_type VARCHAR(50),
    direction VARCHAR(50),
    purpose_type VARCHAR(50),
    current_usage VARCHAR(100),
    recommended_usage VARCHAR(100),
    facilities JSONB DEFAULT '{}',
    description TEXT,
    move_in_type VARCHAR(50),
    move_in_date VARCHAR(10),
    loan_availability VARCHAR(50),
    negotiable VARCHAR(2) DEFAULT 'N',
    photos JSONB DEFAULT '{}',
    update_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    inactive_reason VARCHAR(200),
    first_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- rentals 테이블 생성
CREATE TABLE IF NOT EXISTS realestate.rentals (
    id SERIAL PRIMARY KEY,
    property_id INTEGER REFERENCES realestate.property_info(property_id) UNIQUE NOT NULL,
    rental_type VARCHAR(50) NOT NULL,
    deposit BIGINT DEFAULT 0,
    monthly_rent BIGINT DEFAULT 0
);

-- sales 테이블 생성
CREATE TABLE IF NOT EXISTS realestate.sales (
    id SERIAL PRIMARY KEY,
    property_id INTEGER REFERENCES realestate.property_info(property_id) UNIQUE NOT NULL,
    price BIGINT DEFAULT 0,
    end_date VARCHAR(10),
    transaction_date VARCHAR(10)
);

-- 문화시설 테이블 생성
CREATE TABLE IF NOT EXISTS realestate.cultural_facilities (
    id SERIAL PRIMARY KEY,
    address_id INTEGER REFERENCES realestate.addresses(id),
    facility_name VARCHAR(255),
    facility_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 문화축제 테이블 생성
CREATE TABLE IF NOT EXISTS realestate.cultural_festivals (
    id SERIAL PRIMARY KEY,
    address_id INTEGER REFERENCES realestate.addresses(id),
    festival_name VARCHAR(255),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 지하철역 테이블 생성
CREATE TABLE IF NOT EXISTS realestate.subway_stations (
    id SERIAL PRIMARY KEY,
    address_id INTEGER REFERENCES realestate.addresses(id),
    line_info VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- 범죄 통계 테이블 생성
CREATE TABLE IF NOT EXISTS realestate.crime_stats (
    id BIGSERIAL PRIMARY KEY,
    address_id BIGINT REFERENCES realestate.addresses(id) NOT NULL,
    reference_date DATE NOT NULL,
    total_crime_count INTEGER NOT NULL,
    violent_crime_count INTEGER NOT NULL,
    theft_crime_count INTEGER NOT NULL,
    intellectual_crime_count INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- location_distances 테이블 생성
CREATE TABLE IF NOT EXISTS realestate.location_distances (
    id SERIAL PRIMARY KEY,
    property_id INTEGER REFERENCES realestate.property_locations(property_id) NOT NULL,
    address_id INTEGER REFERENCES realestate.addresses(id) NOT NULL,
    distance FLOAT NOT NULL,  -- 미터 단위
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_property_address UNIQUE (property_id, address_id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_location_distances_property ON realestate.location_distances(property_id);
CREATE INDEX IF NOT EXISTS idx_location_distances_address ON realestate.location_distances(address_id);

-- 권한 설정
GRANT ALL PRIVILEGES ON DATABASE realestate TO realestate;
GRANT ALL PRIVILEGES ON SCHEMA realestate TO realestate;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA realestate TO realestate;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA realestate TO realestate;

-- 기본 검색 경로 설정
ALTER DATABASE realestate SET search_path TO realestate, public; 