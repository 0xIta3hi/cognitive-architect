"""
Debug script to diagnose MemGraph API issues.
"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(method, endpoint, params=None, json_data=None):
    """Test an endpoint and show detailed response."""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"{method.upper()} {endpoint}")
    print(f"{'='*60}")
    
    try:
        if method.lower() == "get":
            response = requests.get(url, params=params, timeout=5)
        elif method.lower() == "post":
            response = requests.post(url, params=params, json=json_data, timeout=5)
        else:
            print(f"❌ Unknown method: {method}")
            return
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            print(f"Body: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Body (raw): {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🔍 MemGraph API Debug Tool")
    print(f"Testing: {BASE_URL}\n")
    
    # Wait for server
    print("⏳ Waiting for server...")
    for i in range(10):
        try:
            requests.get(f"{BASE_URL}/health", timeout=2)
            print("✅ Server is ready!\n")
            break
        except:
            if i < 9:
                time.sleep(1)
            else:
                print("❌ Server is not responding!")
                exit(1)
    
    # Test endpoints
    test_endpoint("GET", "/")
    test_endpoint("GET", "/health")
    test_endpoint("POST", "/agents", params={
        "agent_id": "debug_test",
        "name": "Debug Test Agent"
    })
    test_endpoint("GET", "/agents/debug_test")
    
    print("\n" + "="*60)
    print("✅ Debug test complete")
    print("="*60)
