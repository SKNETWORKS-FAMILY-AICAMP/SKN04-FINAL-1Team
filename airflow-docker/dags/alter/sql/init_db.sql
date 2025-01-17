-- addresses 테이블
CREATE TABLE IF NOT EXISTS addresses (
    address_id SERIAL PRIMARY KEY,
    area_name VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_area_name ON addresses(area_name);

-- cultural_facilities 테이블
CREATE TABLE IF NOT EXISTS cultural_facilities (
    facility_id SERIAL PRIMARY KEY,
    address_id INTEGER REFERENCES addresses(address_id),
    facility_name VARCHAR(100) NOT NULL,
    facility_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- cultural_festivals 테이블
CREATE TABLE IF NOT EXISTS cultural_festivals (
    festival_id SERIAL PRIMARY KEY,
    address_id INTEGER REFERENCES addresses(address_id),
    festival_name VARCHAR(100) NOT NULL,
    begin_date VARCHAR(10),
    end_date VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- subway_stations 테이블
CREATE TABLE IF NOT EXISTS subway_stations (
    station_id SERIAL PRIMARY KEY,
    address_id INTEGER REFERENCES addresses(address_id),
    line_info VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- crime_stats 테이블
CREATE TABLE IF NOT EXISTS crime_stats (
    stat_id SERIAL PRIMARY KEY,
    address_id INTEGER REFERENCES addresses(address_id),
    reference_date VARCHAR(8),
    total_population DOUBLE PRECISION,
    crime_category VARCHAR(50) NOT NULL,
    crime_subcategory VARCHAR(50) NOT NULL,
    incident_count INTEGER NOT NULL,
    crime_rate DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- property_locations 테이블
CREATE TABLE IF NOT EXISTS property_locations (
    id SERIAL PRIMARY KEY,
    property_id INTEGER UNIQUE NOT NULL,
    sido VARCHAR(20) NOT NULL,
    sigungu VARCHAR(20) NOT NULL,
    dong VARCHAR(20),
    jibun_main VARCHAR(20),
    jibun_sub VARCHAR(20),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

-- location_distances 테이블
CREATE TABLE IF NOT EXISTS location_distances (
    id SERIAL PRIMARY KEY,
    property_id INTEGER REFERENCES property_locations(property_id) NOT NULL,
    address_id INTEGER REFERENCES addresses(address_id) NOT NULL,
    distance DOUBLE PRECISION NOT NULL
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_property_locations_property_id ON property_locations(property_id);
CREATE INDEX IF NOT EXISTS idx_property_locations_coords ON property_locations(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_location_distances_property ON location_distances(property_id);
CREATE INDEX IF NOT EXISTS idx_location_distances_address ON location_distances(address_id); 