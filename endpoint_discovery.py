#!/usr/bin/env python3
"""
Quick endpoint discovery script
"""

import requests

def test_endpoints():
    base_url = "http://localhost:8000"
    endpoints_to_try = [
        "/",
        "/health",
        "/docs",
        "/credit/evaluate/123",
        "/credit/calculate/123", 
        "/credit/demo/123",
        "/credit/status",
        "/api/v1/credit/offers",
        "/api/v1/credit/users/123/summary",
        "/api/v1/credit/users/123/offers"
    ]
    
    print("🔍 Testing Available Endpoints:")
    print("=" * 50)
    
    for endpoint in endpoints_to_try:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            status = response.status_code
            symbol = "✅" if status == 200 else "❓" if status == 404 else "⚠️"
            print(f"{symbol} {endpoint:<30} Status: {status}")
        except Exception as e:
            print(f"❌ {endpoint:<30} Error: {e}")

if __name__ == "__main__":
    test_endpoints()
