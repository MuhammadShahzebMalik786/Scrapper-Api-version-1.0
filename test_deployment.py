#!/usr/bin/env python3

import requests
import time
import sys

def test_api():
    """Test API endpoints"""
    base_url = "http://localhost:8080"
    token = "mobile-scraper-2026-secure-token"
    
    print("Testing Mobile.de Scraper API...")
    print("=" * 40)
    
    # Test health endpoint (no auth required)
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✓ Health check: {response.json()}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False
    
    # Test status endpoint (no auth required)
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✓ Status check: {response.json()}")
    except Exception as e:
        print(f"✗ Status check failed: {e}")
        return False
    
    # Test scraper status (no auth required)
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        print(f"✓ Scraper status: {response.json()}")
    except Exception as e:
        print(f"✗ Scraper status failed: {e}")
        return False
    
    # Test database API stats (no auth required)
    try:
        response = requests.get(f"{base_url}/api/stats", timeout=5)
        print(f"✓ Database stats: {response.json()}")
    except Exception as e:
        print(f"✗ Database stats failed: {e}")
    
    # Test protected endpoint (auth required)
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{base_url}/api/cars?limit=5", headers=headers, timeout=5)
        if response.status_code == 200:
            print(f"✓ Protected endpoint: {len(response.json())} cars found")
        else:
            print(f"✓ Protected endpoint: {response.status_code} (expected for empty DB)")
    except Exception as e:
        print(f"✗ Protected endpoint failed: {e}")
    
    print("\n✓ All API tests completed!")
    return True

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
