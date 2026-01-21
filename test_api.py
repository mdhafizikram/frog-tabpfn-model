#!/usr/bin/env python3
"""
Test script for TabPFN Fraud Detection API
"""
import requests
import json
import time
from datetime import datetime

API_URL = "https://comzc4a9w2.execute-api.us-west-2.amazonaws.com/predict"

def test_api(name, payload):
    """Run a single test case"""
    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print(f"{'='*60}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    
    start = time.time()
    response = requests.post(API_URL, json=payload, headers={"Content-Type": "application/json"})
    elapsed = time.time() - start
    
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
    print(f"Duration: {elapsed:.2f}s")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        return result
    else:
        print(f"Error: {response.text}")
        return None

# Test 1: Medium Risk Case
test1_payload = {
    "data": [{
        "nameRiskLevel": "medium",
        "phoneLevel": "medium",
        "addressRiskLevel": "medium",
        "phoneEmailMatch": "nomatch",
        "phoneDobMatch": "nomatch",
        "phoneCityMatch": "nomatch",
        "phoneZipcodeMatch": "nomatch",
        "phoneStateMatch": "nomatch",
        "phoneNameMatch": "nomatch",
        "phoneAddressMatch": "nomatch",
        "overallLevel": "high",
        "persona_email_reputation": "high",
        "persona_email_is_suspicious": "false",
        "persona_email_is_spam": "false",
        "persona_email_is_disposable": "false",
        "persona_phone_risk_level": "medium-low",
        "persona_phone_risk_recommendation": "allow",
        "persona_address_has_match": "true",
        "persona_database_identity_comparison_status": "failed",
        "cheq_riskLabel": "low_risk",
        "cheq_is_vpn_confirmed": "false",
        "cheq_is_vpn_suspect": "false",
        "cheq_is_tor": "false",
        "cheq_is_hosting": "false",
        "cheq_is_corporate": "false",
        "cheq_is_mobile": "false",
        "cheq_geo_country": "",
        "cheq_risk_network_non_us": "false",
        "cheq_risk_distance": "false",
        "cheq_risk_unknown_email": "true",
        "applicant_geo_type": "domestic",
        "campus": "onground"
    }]
}

# Test 2: High Risk International Case
test2_payload = {
    "data": [{
        "nameRiskLevel": "",
        "phoneLevel": "",
        "addressRiskLevel": "",
        "phoneEmailMatch": "",
        "phoneDobMatch": "",
        "phoneCityMatch": "",
        "phoneZipcodeMatch": "",
        "phoneStateMatch": "",
        "phoneNameMatch": "",
        "phoneAddressMatch": "",
        "overallLevel": "",
        "persona_email_reputation": "high",
        "persona_email_is_suspicious": "false",
        "persona_email_is_spam": "false",
        "persona_email_is_disposable": "false",
        "persona_phone_risk_level": "medium-low",
        "persona_phone_risk_recommendation": "allow",
        "persona_address_has_match": "",
        "persona_database_identity_comparison_status": "",
        "cheq_riskLabel": "low_risk",
        "cheq_is_vpn_confirmed": "false",
        "cheq_is_vpn_suspect": "false",
        "cheq_is_tor": "false",
        "cheq_is_hosting": "false",
        "cheq_is_corporate": "true",
        "cheq_is_mobile": "true",
        "cheq_geo_country": "za",
        "cheq_risk_network_non_us": "true",
        "cheq_risk_distance": "true",
        "cheq_risk_unknown_email": "true",
        "applicant_geo_type": "international",
        "campus": "online"
    }]
}

# Test 3: Batch Prediction (Low + High Risk)
test3_payload = {
    "data": [
        {
            "nameRiskLevel": "low",
            "phoneLevel": "low",
            "addressRiskLevel": "low",
            "phoneEmailMatch": "match",
            "phoneDobMatch": "match",
            "phoneCityMatch": "match",
            "phoneZipcodeMatch": "match",
            "phoneStateMatch": "match",
            "phoneNameMatch": "match",
            "phoneAddressMatch": "match",
            "overallLevel": "low",
            "persona_email_reputation": "low",
            "persona_email_is_suspicious": "false",
            "persona_email_is_spam": "false",
            "persona_email_is_disposable": "false",
            "persona_phone_risk_level": "low",
            "persona_phone_risk_recommendation": "allow",
            "persona_address_has_match": "true",
            "persona_database_identity_comparison_status": "match",
            "cheq_riskLabel": "low_risk",
            "cheq_is_vpn_confirmed": "false",
            "cheq_is_vpn_suspect": "false",
            "cheq_is_tor": "false",
            "cheq_is_hosting": "false",
            "cheq_is_corporate": "false",
            "cheq_is_mobile": "false",
            "cheq_geo_country": "us",
            "cheq_risk_network_non_us": "false",
            "cheq_risk_distance": "false",
            "cheq_risk_unknown_email": "false",
            "applicant_geo_type": "domestic",
            "campus": "onground"
        },
        {
            "nameRiskLevel": "high",
            "phoneLevel": "high",
            "addressRiskLevel": "high",
            "phoneEmailMatch": "nomatch",
            "phoneDobMatch": "nomatch",
            "phoneCityMatch": "nomatch",
            "phoneZipcodeMatch": "nomatch",
            "phoneStateMatch": "nomatch",
            "phoneNameMatch": "nomatch",
            "phoneAddressMatch": "nomatch",
            "overallLevel": "high",
            "persona_email_reputation": "high",
            "persona_email_is_suspicious": "true",
            "persona_email_is_spam": "true",
            "persona_email_is_disposable": "true",
            "persona_phone_risk_level": "high",
            "persona_phone_risk_recommendation": "block",
            "persona_address_has_match": "false",
            "persona_database_identity_comparison_status": "failed",
            "cheq_riskLabel": "high_risk",
            "cheq_is_vpn_confirmed": "true",
            "cheq_is_vpn_suspect": "true",
            "cheq_is_tor": "true",
            "cheq_is_hosting": "true",
            "cheq_is_corporate": "false",
            "cheq_is_mobile": "false",
            "cheq_geo_country": "",
            "cheq_risk_network_non_us": "true",
            "cheq_risk_distance": "true",
            "cheq_risk_unknown_email": "true",
            "applicant_geo_type": "international",
            "campus": "online"
        }
    ]
}

if __name__ == "__main__":
    print("TabPFN Fraud Detection API - Test Suite")
    print(f"API URL: {API_URL}")
    
    # Run tests
    test_api("Medium Risk Case", test1_payload)
    test_api("High Risk International Case", test2_payload)
    test_api("Batch Prediction (Low + High Risk)", test3_payload)
    
    print(f"\n{'='*60}")
    print("All tests completed")
    print(f"{'='*60}\n")

# TabPFN Fraud Detection API - Test Suite
# API URL: https://comzc4a9w2.execute-api.us-west-2.amazonaws.com/predict

# ============================================================
# Test: Medium Risk Case
# ============================================================
# Started: 2026-01-21 13:38:32.592
# Completed: 2026-01-21 13:38:45.776
# Duration: 13.18s
# Status: 200
# Response: {
#   "predictions": [
#     0
#   ],
#   "probabilities": [
#     0.34814453125
#   ]
# }

# ============================================================
# Test: High Risk International Case
# ============================================================
# Started: 2026-01-21 13:38:45.778
# Completed: 2026-01-21 13:38:50.929
# Duration: 5.15s
# Status: 200
# Response: {
#   "predictions": [
#     1
#   ],
#   "probabilities": [
#     0.9420095086097717
#   ]
# }

# ============================================================
# Test: Batch Prediction (Low + High Risk)
# ============================================================
# Started: 2026-01-21 13:38:50.931
# Completed: 2026-01-21 13:38:56.013
# Duration: 5.08s
# Status: 200
# Response: {
#   "predictions": [
#     0,
#     1
#   ],
#   "probabilities": [
#     0.3369140625,
#     0.9734694361686707
#   ]
# }

# ============================================================
# All tests completed
# ============================================================

# hafiz@lenovo-ThinkPad-P14s-Gen-4:~/Documents/frog-tabpfn-model$ python3 test_api.py
# TabPFN Fraud Detection API - Test Suite
# API URL: https://comzc4a9w2.execute-api.us-west-2.amazonaws.com/predict

# ============================================================
# Test: Medium Risk Case
# ============================================================
# Started: 2026-01-21 13:39:25.265
# Completed: 2026-01-21 13:39:30.316
# Duration: 5.05s
# Status: 200
# Response: {
#   "predictions": [
#     0
#   ],
#   "probabilities": [
#     0.34814453125
#   ]
# }

# ============================================================
# Test: High Risk International Case
# ============================================================
# Started: 2026-01-21 13:39:30.318
# Completed: 2026-01-21 13:39:35.331
# Duration: 5.01s
# Status: 200
# Response: {
#   "predictions": [
#     1
#   ],
#   "probabilities": [
#     0.9420095086097717
#   ]
# }

# ============================================================
# Test: Batch Prediction (Low + High Risk)
# ============================================================
# Started: 2026-01-21 13:39:35.332
# Completed: 2026-01-21 13:39:40.451
# Duration: 5.12s
# Status: 200
# Response: {
#   "predictions": [
#     0,
#     1
#   ],
#   "probabilities": [
#     0.3369140625,
#     0.9734694361686707
#   ]
# }

# ============================================================
# All tests completed
# ============================================================

# hafiz@lenovo-ThinkPad-P14s-Gen-4:~/Documents/frog-tabpfn-model$ python3 test_api.py
# TabPFN Fraud Detection API - Test Suite
# API URL: https://comzc4a9w2.execute-api.us-west-2.amazonaws.com/predict

# ============================================================
# Test: Medium Risk Case
# ============================================================
# Started: 2026-01-21 13:44:00.241
# Completed: 2026-01-21 13:44:05.479
# Duration: 5.24s
# Status: 200
# Response: {
#   "predictions": [
#     0
#   ],
#   "probabilities": [
#     0.34814453125
#   ]
# }

# ============================================================
# Test: High Risk International Case
# ============================================================
# Started: 2026-01-21 13:44:05.481
# Completed: 2026-01-21 13:44:10.465
# Duration: 4.98s
# Status: 200
# Response: {
#   "predictions": [
#     1
#   ],
#   "probabilities": [
#     0.9420095086097717
#   ]
# }

# ============================================================
# Test: Batch Prediction (Low + High Risk)
# ============================================================
# Started: 2026-01-21 13:44:10.466
# Completed: 2026-01-21 13:44:15.544
# Duration: 5.08s
# Status: 200
# Response: {
#   "predictions": [
#     0,
#     1
#   ],
#   "probabilities": [
#     0.3369140625,
#     0.9734694361686707
#   ]
# }

# ============================================================
# All tests completed
# ============================================================
