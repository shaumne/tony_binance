#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Trailing Stop Strategy
Tests both standard and trailing stop webhook payloads
"""

import requests
import json
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
WEBHOOK_URL = "http://localhost:5001/webhook"

# ============================================================================
# TEST PAYLOADS
# ============================================================================

# Test 1: Standard Strategy (Old Logic)
standard_payload = {
    "signal": "BTCUSDT/long/open",
    "message": "BTCUSDT/long/open"
}

# Test 2: Trailing Stop Strategy (New Logic) - BUY (LONG) - LDO
# activationPrice ve stopLoss OPSIYONEL - otomatik hesaplanacak!
# activationPrice = entry * 1.02 (LONG için %2 üstte)
# stopLoss = entry * 0.97 (LONG için %3 altta)
trailing_stop_long_payload = {
    "symbol": "LDOUSDT",
    "side": "BUY",
    "action": "open",
    "quantity": "10%",            # Küçük pozisyon test için
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": 1.5,          # %1.5 trailing
    "workingType": "MARK_PRICE"
    # activationPrice: Otomatik (entry'nin %2 üstünde)
    # stopLoss: Otomatik (entry'nin %3 altında)
}

# Test 3: Trailing Stop Strategy - BUY (LONG) - ADA (Farklı Coin!)
# activationPrice ve stopLoss OPSIYONEL - otomatik hesaplanacak!
trailing_stop_ada_payload = {
    "symbol": "ADAUSDT",
    "side": "BUY",
    "action": "open",
    "quantity": "10%",            # Küçük pozisyon test için
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": 2.0,          # %2.0 trailing (farklı callback test için)
    "workingType": "MARK_PRICE"
    # activationPrice: Otomatik (entry'nin %2 üstünde)
    # stopLoss: Otomatik (entry'nin %3 altında)
}

# Test 4: Missing Fields (Should Fail)
invalid_payload = {
    "symbol": "XLMUSDT",          # Başka bir coin (test için)
    "side": "BUY",
    "trailType": "TRAILING_STOP_MARKET"
    # Missing: callbackRate, activationPrice, workingType
}

# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def send_webhook(payload, test_name):
    """
    Send webhook to bot and print response
    
    Args:
        payload (dict): Payload to send
        test_name (str): Test identifier
    """
    try:
        logger.info("=" * 80)
        logger.info(f"🧪 TEST: {test_name}")
        logger.info("=" * 80)
        logger.info(f"📤 Sending payload:")
        logger.info(json.dumps(payload, indent=2))
        
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        logger.info(f"📥 Response Status: {response.status_code}")
        logger.info(f"📥 Response Body:")
        logger.info(json.dumps(response.json(), indent=2))
        
        # Check success
        response_data = response.json()
        if response_data.get('status') == 'success':
            logger.info("✅ TEST PASSED")
        else:
            logger.warning("⚠️ TEST FAILED OR FILTERED")
        
        return response_data
        
    except requests.exceptions.Timeout:
        logger.error(f"❌ Request timeout for {test_name}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Connection error - is the bot running at {WEBHOOK_URL}?")
        return None
    except Exception as e:
        logger.error(f"❌ Error in {test_name}: {str(e)}")
        return None

def run_all_tests():
    """Run all test cases"""
    
    logger.info("🚀 STARTING TRAILING STOP STRATEGY TESTS")
    logger.info("=" * 80)
    
    tests = [
        {
            "name": "Standard Strategy (Old Logic)",
            "payload": standard_payload,
            "enabled": False  # Set to True to test
        },
        {
            "name": "Trailing Stop - LDO (LONG Position)",
            "payload": trailing_stop_long_payload,
            "enabled": True
        },
        {
            "name": "Trailing Stop - ADA (LONG Position)",
            "payload": trailing_stop_ada_payload,
            "enabled": True
        },
        {
            "name": "Invalid Payload (Missing Fields)",
            "payload": invalid_payload,
            "enabled": True
        }
    ]
    
    results = []
    
    for test in tests:
        if test["enabled"]:
            result = send_webhook(test["payload"], test["name"])
            results.append({
                "test": test["name"],
                "result": result
            })
            time.sleep(2)  # Wait between tests
        else:
            logger.info(f"⏭️ SKIPPING: {test['name']}")
    
    # Summary
    logger.info("=" * 80)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 80)
    
    for result in results:
        status = "✅ PASS" if result["result"] and result["result"].get("status") == "success" else "❌ FAIL"
        logger.info(f"{status} - {result['test']}")
    
    logger.info("=" * 80)
    logger.info("🏁 TESTS COMPLETED")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Tests interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()

