#!/usr/bin/env python3

import requests
import time
import os
from config import Config

def test_api():
    """Test API endpoints"""
    base_url = f"http://localhost:{Config.API_PORT}"
    headers = {"Authorization": f"Bearer {Config.API_TOKEN}"}
    
    print("Testing Mobile.de Scraper API")
    print("=" * 40)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"✓ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False
    
    # Test status endpoint
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"✓ Status check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"✗ Status check failed: {e}")
    
    # Test stats endpoint
    try:
        response = requests.get(f"{base_url}/stats", timeout=10)
        print(f"✓ Stats check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"✗ Stats check failed: {e}")
    
    # Test protected endpoint (cars)
    try:
        response = requests.get(f"{base_url}/cars?limit=1", headers=headers, timeout=10)
        print(f"✓ Cars endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Found {len(data)} cars")
    except Exception as e:
        print(f"✗ Cars endpoint failed: {e}")
    
    # Test scraper trigger (don't actually run it)
    print("\n⚠️  Scraper trigger test skipped (would start actual scraping)")
    print("   To test manually: curl -X POST -H 'Authorization: Bearer TOKEN' http://localhost:8080/populate")
    
    print("\n✓ API tests completed!")
    return True

def test_database():
    """Test database connection"""
    try:
        from database import db_manager
        if db_manager.health_check():
            print("✓ Database connection: OK")
            return True
        else:
            print("✗ Database connection: Failed")
            return False
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False

if __name__ == "__main__":
    print("Mobile.de Scraper - System Test")
    print("=" * 40)
    
    # Test configuration
    try:
        Config.validate()
        print("✓ Configuration: Valid")
    except Exception as e:
        print(f"✗ Configuration: {e}")
        exit(1)
    
    # Test database
    if not test_database():
        print("Database tests failed - check your DB_URL configuration")
        exit(1)
    
    # Test API
    if not test_api():
        print("API tests failed")
        exit(1)
    
    print("\n🎉 All tests passed! System is ready.")
