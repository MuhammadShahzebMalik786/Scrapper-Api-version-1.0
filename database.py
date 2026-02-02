#!/usr/bin/env python3

import os
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.types import TypeDecorator

Base = declarative_base()

class JSONType(TypeDecorator):
    impl = Text
    
    def process_bind_param(self, value, dialect):
        return json.dumps(value) if value else value
    
    def process_result_value(self, value, dialect):
        return json.loads(value) if value else value

class Car(Base):
    __tablename__ = 'cars'
    
    id = Column(Integer, primary_key=True)
    source = Column(String(50), default='mobile.de')
    listing_id = Column(String(100))
    url = Column(String(500), unique=True, nullable=False)
    url_title = Column(String(500))
    additional_info = Column(Text)
    price = Column(String(100))
    dealer_rating = Column(String(50))
    dealer = Column(String(200))
    seller_type = Column(String(100))
    location = Column(String(200))
    phone = Column(String(50))
    rating = Column(String(50))
    negotiable = Column(String(50))
    monthly_rate = Column(String(100))
    monthly_rate_link = Column(String(500))
    financing_link = Column(String(500))
    mileage = Column(String(100))
    power = Column(String(100))
    fuel_type = Column(String(100))
    transmission = Column(String(100))
    first_registration = Column(String(100))
    vehicle_condition = Column(String(100))
    category = Column(String(100))
    model_range = Column(String(200))
    trim_line = Column(String(200))
    vehicle_number = Column(String(100))
    origin = Column(String(100))
    cubic_capacity = Column(String(100))
    drive_type = Column(String(100))
    energy_consumption = Column(String(100))
    co2_emissions = Column(String(100))
    co2_class = Column(String(50))
    fuel_consumption = Column(String(100))
    image_urls = Column(JSONType)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    car_features = relationship("CarFeature", back_populates="car", cascade="all, delete-orphan")

class Feature(Base):
    __tablename__ = 'features'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)

class FeatureSection(Base):
    __tablename__ = 'feature_sections'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)

class CarFeature(Base):
    __tablename__ = 'car_features'
    car_id = Column(Integer, ForeignKey('cars.id'), primary_key=True)
    feature_id = Column(Integer, ForeignKey('features.id'), primary_key=True)
    section_id = Column(Integer, ForeignKey('feature_sections.id'), primary_key=True)
    
    car = relationship("Car", back_populates="car_features")
    feature = relationship("Feature")
    section = relationship("FeatureSection")

def get_database_url():
    return os.getenv('DB_URL', 'sqlite:///mobile_scraper.db')

def create_database_engine():
    db_url = get_database_url()
    return create_engine(db_url, echo=False, poolclass=pool.QueuePool, pool_size=5, max_overflow=10)

def init_database():
    engine = create_database_engine()
    Base.metadata.create_all(engine)
    return engine

def get_session():
    engine = init_database()
    Session = sessionmaker(bind=engine)
    return Session()

engine = create_database_engine()
