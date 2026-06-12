"""
Test script for SKU Matching API
Run this after starting the Flask API to verify it works correctly
"""

import requests
import json

API_URL = "http://localhost:8080"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def test_health_check():
    print_section("Testing Health Check")
    try:
        response = requests.get(f"{API_URL}/api/health")
        data = response.json()
        print("✓ Health check successful!")
        print(f"  Status: {data['status']}")
        print(f"  SKU Records: {data['sku_records']}")
        print(f"  Pricing Records: {data['pricing_records']}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_match_sku():
    print_section("Testing SKU Matching")
    
    payload = {
        "requirements": [
            "Exterior paint for outer walls",
            "Interior primer for living room",
            "Wood varnish"
        ],
        "top_k": 3,
        "include_pricing": True
    }
    
    print("Request payload:")
    print(json.dumps(payload, indent=2))
    print()
    
    try:
        response = requests.post(f"{API_URL}/api/match-sku", json=payload)
        data = response.json()
        
        print("✓ SKU matching successful!")
        print()
        
        for result in data['matches']:
            print(f"Requirement: '{result['requirement']}'")
            print(f"Found {len(result['matches'])} matches:")
            
            for idx, match in enumerate(result['matches'], 1):
                print(f"\n  {idx}. {match['product_name']} ({match['sku']})")
                print(f"     Score: {match['score']*100:.1f}%")
                print(f"     Description: {match['description']}")
                if 'price' in match:
                    print(f"     Price: ₹{match['price']}")
                if 'gst' in match:
                    print(f"     GST: {match['gst']}%")
            print()
        
        return True
    except Exception as e:
        print(f"✗ SKU matching failed: {e}")
        return False

def test_validate_sku():
    print_section("Testing SKU Validation")
    
    test_cases = [
        ("SKU001", True),
        ("SKU999", False)
    ]
    
    for sku_code, should_exist in test_cases:
        print(f"Testing SKU: {sku_code}")
        try:
            response = requests.post(f"{API_URL}/api/validate-sku", json={"sku_code": sku_code})
            
            if should_exist:
                data = response.json()
                print(f"  ✓ Found: {data['sku']['product_name']}")
            else:
                if response.status_code == 404:
                    print(f"  ✓ Correctly not found")
                else:
                    print(f"  ✗ Expected 404, got {response.status_code}")
        except Exception as e:
            print(f"  ✗ Validation failed: {e}")
        print()

def main():
    print("\n" + "▓"*60)
    print("  SKU MATCHING API TEST SUITE")
    print("▓"*60)
    
    print("\nMake sure the Flask API is running on http://localhost:8080")
    input("Press Enter to start tests...")
    
    tests_passed = 0
    tests_total = 3
    
    if test_health_check():
        tests_passed += 1
    
    if test_match_sku():
        tests_passed += 1
    
    if test_validate_sku():
        tests_passed += 1
    
    print_section("Test Results")
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\n✅ All tests passed! The SKU Matching API is working correctly.")
    else:
        print(f"\n⚠ {tests_total - tests_passed} test(s) failed. Please check the errors above.")

if __name__ == "__main__":
    main()
