#!/usr/bin/env python3

from database import db_manager, Car, Feature, FeatureSection, CarFeature
from datetime import datetime
import logging
from urllib.parse import urlsplit, parse_qs

logger = logging.getLogger(__name__)

def save_car_to_database(car_data: dict) -> bool:
    """Save car data to database with improved error handling"""
    try:
        with db_manager.get_session() as session:
            # Extract features data
            features_data = car_data.pop('features', {})
            
            # Prepare car data
            car_dict = {
                'source': 'mobile.de',
                'listing_id': extract_listing_id_from_url(car_data.get('url', '')),
                'url': car_data.get('url', ''),
                'url_title': car_data.get('title', ''),
                'additional_info': car_data.get('additional_info'),
                'price': car_data.get('price'),
                'dealer_rating': car_data.get('dealer_rating'),
                'dealer': car_data.get('dealer'),
                'seller_type': car_data.get('seller_type'),
                'location': car_data.get('location'),
                'phone': car_data.get('phone'),
                'rating': car_data.get('rating'),
                'negotiable': car_data.get('negotiable'),
                'monthly_rate': car_data.get('monthly_rate'),
                'monthly_rate_link': car_data.get('monthly_rate_href'),
                'financing_link': car_data.get('financing_link'),
                'mileage': car_data.get('mileage'),
                'power': car_data.get('power'),
                'fuel_type': car_data.get('fuel_type'),
                'transmission': car_data.get('transmission'),
                'first_registration': car_data.get('first_registration'),
                'vehicle_condition': car_data.get('vehicle_condition'),
                'category': car_data.get('category'),
                'model_range': car_data.get('model_range'),
                'trim_line': car_data.get('trim_line'),
                'vehicle_number': car_data.get('vehicle_number'),
                'origin': car_data.get('origin'),
                'cubic_capacity': car_data.get('cubic_capacity'),
                'drive_type': car_data.get('drive_type'),
                'energy_consumption': car_data.get('energy_consumption'),
                'co2_emissions': car_data.get('co2_emissions'),
                'co2_class': car_data.get('co2_class'),
                'fuel_consumption': car_data.get('fuel_consumption'),
                'image_urls': car_data.get('img_urls', [])
            }
            
            # Upsert car record
            existing_car = session.query(Car).filter_by(url=car_dict['url']).first()
            if existing_car:
                # Update existing record
                for key, value in car_dict.items():
                    if key != 'created_at':
                        setattr(existing_car, key, value)
                existing_car.updated_at = datetime.utcnow()
                car = existing_car
                
                # Remove existing car_features for this car
                session.query(CarFeature).filter_by(car_id=car.id).delete()
            else:
                # Create new record
                car = Car(**car_dict)
                session.add(car)
                session.flush()  # Get the ID
            
            # Handle features if they exist
            if features_data:
                _save_car_features(session, car, features_data)
            
            logger.info(f"Saved car to database: {car.listing_id}")
            return True
            
    except Exception as e:
        logger.error(f"Error saving car to database: {e}")
        return False

def _save_car_features(session, car, features_data):
    """Save car features to database"""
    if isinstance(features_data, list):
        features_dict = {'General': features_data}
    elif isinstance(features_data, dict):
        features_dict = features_data
    else:
        return
    
    for section_name, feature_list in features_dict.items():
        if not feature_list:
            continue
            
        # Upsert section
        section = session.query(FeatureSection).filter_by(name=section_name).first()
        if not section:
            section = FeatureSection(name=section_name)
            session.add(section)
            session.flush()
        
        for feature_name in feature_list:
            if not feature_name or not feature_name.strip():
                continue
                
            # Upsert feature
            feature = session.query(Feature).filter_by(name=feature_name).first()
            if not feature:
                feature = Feature(name=feature_name)
                session.add(feature)
                session.flush()
            
            # Create car_feature link
            car_feature = CarFeature(
                car_id=car.id,
                feature_id=feature.id,
                section_id=section.id
            )
            session.add(car_feature)

def extract_listing_id_from_url(url: str) -> str:
    """Extract listing ID from mobile.de URL"""
    if not url:
        return ""
    try:
        qs = parse_qs(urlsplit(url.strip()).query)
        return (qs.get("id") or [""])[0].strip()
    except Exception:
        return ""

def get_database_stats() -> dict:
    """Get database statistics"""
    try:
        with db_manager.get_session() as session:
            total_cars = session.query(Car).count()
            total_features = session.query(Feature).count()
            total_sections = session.query(FeatureSection).count()
            
            return {
                "total_cars": total_cars,
                "total_features": total_features,
                "total_sections": total_sections,
                "database_connected": True
            }
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {"database_connected": False, "error": str(e)}
