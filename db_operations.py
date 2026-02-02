#!/usr/bin/env python3

from database import get_session, Car, Feature, FeatureSection, CarFeature
from sqlalchemy.exc import IntegrityError
from datetime import datetime

def save_car_to_database(car_data):
    """Save car data to database with upsert functionality"""
    session = get_session()
    try:
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
                if key != 'created_at':  # Don't update created_at
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
            if isinstance(features_data, list):
                # Convert list to dict with default section
                features_dict = {'General': features_data}
            elif isinstance(features_data, dict):
                features_dict = features_data
            else:
                features_dict = {}
            
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
        
        session.commit()
        print(f"Saved car to database: {car.listing_id}")
        return True
        
    except Exception as e:
        session.rollback()
        print(f"Error saving to database: {e}")
        return False
    finally:
        session.close()

def extract_listing_id_from_url(url):
    """Extract listing ID from mobile.de URL"""
    if not url:
        return ""
    try:
        from urllib.parse import urlsplit, parse_qs
        qs = parse_qs(urlsplit(url.strip()).query)
        return (qs.get("id") or [""])[0].strip()
    except Exception:
        return ""
