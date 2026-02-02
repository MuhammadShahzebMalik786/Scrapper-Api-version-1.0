-- Mobile.de Scraper Database Schema
-- This schema supports both PostgreSQL and SQLite

-- Cars table (main listing data)
CREATE TABLE IF NOT EXISTS cars (
    id INTEGER PRIMARY KEY,
    source VARCHAR(50) DEFAULT 'mobile.de',
    listing_id VARCHAR(100),
    url VARCHAR(500) UNIQUE NOT NULL,
    url_title VARCHAR(500),
    additional_info TEXT,
    price VARCHAR(100),
    dealer_rating VARCHAR(50),
    dealer VARCHAR(200),
    seller_type VARCHAR(100),
    location VARCHAR(200),
    phone VARCHAR(50),
    rating VARCHAR(50),
    negotiable VARCHAR(50),
    monthly_rate VARCHAR(100),
    monthly_rate_link VARCHAR(500),
    financing_link VARCHAR(500),
    mileage VARCHAR(100),
    power VARCHAR(100),
    fuel_type VARCHAR(100),
    transmission VARCHAR(100),
    first_registration VARCHAR(100),
    vehicle_condition VARCHAR(100),
    category VARCHAR(100),
    model_range VARCHAR(200),
    trim_line VARCHAR(200),
    vehicle_number VARCHAR(100),
    origin VARCHAR(100),
    cubic_capacity VARCHAR(100),
    drive_type VARCHAR(100),
    energy_consumption VARCHAR(100),
    co2_emissions VARCHAR(100),
    co2_class VARCHAR(50),
    fuel_consumption VARCHAR(100),
    image_urls TEXT, -- JSON array stored as text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Features table (normalized feature names)
CREATE TABLE IF NOT EXISTS features (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL
);

-- Feature sections table (categories like "Comfort", "Safety", etc.)
CREATE TABLE IF NOT EXISTS feature_sections (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL
);

-- Car features junction table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS car_features (
    car_id INTEGER NOT NULL,
    feature_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    PRIMARY KEY (car_id, feature_id, section_id),
    FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE,
    FOREIGN KEY (feature_id) REFERENCES features(id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES feature_sections(id) ON DELETE CASCADE
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_cars_url ON cars(url);
CREATE INDEX IF NOT EXISTS idx_cars_listing_id ON cars(listing_id);
CREATE INDEX IF NOT EXISTS idx_cars_created_at ON cars(created_at);
CREATE INDEX IF NOT EXISTS idx_features_name ON features(name);
CREATE INDEX IF NOT EXISTS idx_feature_sections_name ON feature_sections(name);
CREATE INDEX IF NOT EXISTS idx_car_features_car_id ON car_features(car_id);

-- PostgreSQL specific: Update trigger for updated_at
-- (SQLite doesn't support this, but the application handles it)
-- CREATE OR REPLACE FUNCTION update_updated_at_column()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     NEW.updated_at = CURRENT_TIMESTAMP;
--     RETURN NEW;
-- END;
-- $$ language 'plpgsql';

-- CREATE TRIGGER update_cars_updated_at BEFORE UPDATE ON cars
--     FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
