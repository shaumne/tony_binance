#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Trailing Stop Strategy
Tests both standard and trailing stop webhook payloads

Updated to include validation tests for:
- callbackRate limits (0.1% - 5.0%)
- Type safety (string to float conversion)
- Entry fill verification
- Position verification
- Error handling improvements
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

# Test 2: Trailing Stop Strategy (New Logic) - BUY (LONG) - Valid
# activationPrice ve stopLoss OPSIYONEL - otomatik hesaplanacak!
# activationPrice = entry * 1.02 (LONG için %2 üstte)
# stopLoss = entry * 0.97 (LONG için %3 altta)
trailing_stop_long_payload = {
    "symbol": "LDOUSDT",
    "side": "BUY",
    "action": "open",
    "quantity": "10%",            # Küçük pozisyon test için
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": 1.5,          # %1.5 trailing (valid: within 0.1-5.0%)
    "workingType": "MARK_PRICE"
    # activationPrice: Otomatik (entry'nin %2 üstünde)
    # stopLoss: Otomatik (entry'nin %3 altında)
}

# Test 3: Trailing Stop Strategy - BUY (LONG) - With Explicit Prices
# Tam payload ile activationPrice ve stopLoss belirtilmiş (0.0 = auto-calculate)
# Note: 0.0 veya null değerler otomatik hesaplanacak
trailing_stop_full_payload = {
    "symbol": "ADAUSDT",
    "side": "BUY",
    "action": "open",
    "quantity": "10%",
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": 2.0,          # %2.0 trailing (valid)
    "activationPrice": None,      # Will be calculated from entry (auto: entry * 1.02)
    "workingType": "MARK_PRICE",
    "stopLoss": None              # Will be calculated from entry (auto: entry * 0.97)
}

# Test 4: Trailing Stop Strategy - SELL (SHORT) - Valid
trailing_stop_short_payload = {
    "symbol": "XLMUSDT",
    "side": "SELL",
    "action": "open",
    "quantity": "10%",
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": 1.5,          # %1.5 trailing (valid)
    "workingType": "MARK_PRICE"
}

# Test 5: callbackRate String Format (Should Work - Auto Convert)
trailing_stop_callback_string_payload = {
    "symbol": "DOTUSDT",
    "side": "BUY",
    "action": "open",
    "quantity": "10%",
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": "1.5",        # String format (should convert to float)
    "workingType": "MARK_PRICE"
}

# Test 6: callbackRate with Percentage Sign (Should Work - Auto Strip)
trailing_stop_callback_percent_payload = {
    "symbol": "UNIUSDT",
    "side": "BUY",
    "action": "open",
    "quantity": "10%",
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": "1.5%",       # String with % (should strip and convert)
    "workingType": "MARK_PRICE"
}

# Test 7: callbackRate Too Low (< 0.1%) - Should Fail
trailing_stop_callback_too_low = {
    "symbol": "IMXUSDT",
    "side": "BUY",
    "action": "open",
    "quantity": "10%",
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": 0.05,         # Too low (< 0.1%) - should fail validation
    "workingType": "MARK_PRICE"
}

# Test 8: callbackRate Too High (> 5.0%) - Should Fail
trailing_stop_callback_too_high = {
    "symbol": "ARBUSDT",
    "side": "BUY",
    "action": "open",
    "quantity": "10%",
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": 6.0,          # Too high (> 5.0%) - should fail validation
    "workingType": "MARK_PRICE"
}

# Test 9: callbackRate at Lower Limit (0.1%) - Should Pass
trailing_stop_callback_min = {
    "symbol": "INJUSDT",
    "side": "BUY",
    "action": "open",
    "quantity": "10%",
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": 0.1,          # Minimum valid (0.1%) - should pass
    "workingType": "MARK_PRICE"
}

# Test 10: callbackRate at Upper Limit (5.0%) - Should Pass
trailing_stop_callback_max = {
    "symbol": "SOLUSDT",
    "side": "BUY",
    "action": "open",
    "quantity": "10%",
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": 5.0,          # Maximum valid (5.0%) - should pass
    "workingType": "MARK_PRICE"
}

# Test 11: Missing callbackRate (Should Fail)
invalid_missing_callbackrate = {
    "symbol": "ETHUSDT",
    "side": "BUY",
    "action": "open",
    "quantity": "10%",
    "trailType": "TRAILING_STOP_MARKET",
    "workingType": "MARK_PRICE"
    # Missing: callbackRate (required)
}

# Test 12: Missing Fields (Should Fail)
invalid_missing_fields = {
    "symbol": "BNBUSDT",
    "side": "BUY",
    "trailType": "TRAILING_STOP_MARKET"
    # Missing: callbackRate, action, workingType
}

# Test 13: Invalid workingType (Should Default to MARK_PRICE)
trailing_stop_invalid_workingtype = {
    "symbol": "FETUSDT",
    "side": "BUY",
    "action": "open",
    "quantity": "10%",
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": 1.5,
    "workingType": "INVALID_TYPE"  # Invalid - should default to MARK_PRICE
}

# Test 14: Invalid activationPrice Format (Should Auto-Calculate)
trailing_stop_invalid_activation = {
    "symbol": "DOGEUSDT",
    "side": "BUY",
    "action": "open",
    "quantity": "10%",
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": 1.5,
    "activationPrice": "invalid",  # Invalid format - should auto-calculate
    "workingType": "MARK_PRICE"
}

# Test 15: Invalid stopLoss Format (Should Auto-Calculate)
trailing_stop_invalid_stoploss = {
    "symbol": "BTCUSDT",
    "side": "BUY",
    "action": "open",
    "quantity": "5%",              # Very small position for BTC
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": 1.5,
    "stopLoss": "invalid",         # Invalid format - should auto-calculate
    "workingType": "MARK_PRICE"
}

# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def send_webhook(payload, test_name, expected_status='success'):
    """
    Send webhook to bot and print response
    
    Args:
        payload (dict): Payload to send
        test_name (str): Test identifier
        expected_status (str): Expected status ('success', 'error', or 'filtered')
        
    Returns:
        dict: Response data with test result info
    """
    try:
        logger.info("=" * 80)
        logger.info(f"🧪 TEST: {test_name}")
        logger.info("=" * 80)
        logger.info(f"📤 Sending payload:")
        logger.info(json.dumps(payload, indent=2))
        logger.info(f"   Expected Status: {expected_status}")
        
        start_time = time.time()
        response = requests.post(
            WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        elapsed_time = time.time() - start_time
        
        logger.info(f"📥 Response Status: {response.status_code} (Time: {elapsed_time:.2f}s)")
        
        try:
            response_data = response.json()
            logger.info(f"📥 Response Body:")
            logger.info(json.dumps(response_data, indent=2))
        except json.JSONDecodeError:
            logger.error(f"❌ Invalid JSON response: {response.text}")
            return {
                "test_name": test_name,
                "status": "error",
                "expected_status": expected_status,
                "test_passed": False,
                "error": "Invalid JSON response",
                "response_text": response.text[:200],
                "elapsed_time": elapsed_time
            }
        
        # Check if test passed based on expected status
        actual_status = response_data.get('status', 'unknown')
        test_passed = False
        test_result = "UNKNOWN"
        
        if expected_status == 'success':
            test_passed = actual_status == 'success'
            test_result = "✅ PASS" if test_passed else "❌ FAIL"
        elif expected_status == 'error':
            test_passed = actual_status == 'error'
            test_result = "✅ PASS" if test_passed else "❌ FAIL (Expected error)"
        elif expected_status == 'filtered':
            test_passed = actual_status in ['filtered', 'error']
            test_result = "✅ PASS" if test_passed else "❌ FAIL"
        
        if test_passed:
            logger.info(f"{test_result} - Test passed as expected")
        else:
            logger.warning(f"{test_result} - Test did not behave as expected")
            logger.warning(f"   Expected: {expected_status}, Got: {actual_status}")
        
        return {
            "test_name": test_name,
            "status": actual_status,
            "expected_status": expected_status,
            "test_passed": test_passed,
            "test_result": test_result,
            "response_data": response_data,
            "elapsed_time": elapsed_time
        }
        
    except requests.exceptions.Timeout:
        logger.error(f"❌ Request timeout for {test_name}")
        return {
            "test_name": test_name,
            "status": "timeout",
            "test_passed": False,
            "error": "Request timeout"
        }
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Connection error - is the bot running at {WEBHOOK_URL}?")
        return {
            "test_name": test_name,
            "status": "connection_error",
            "test_passed": False,
            "error": "Connection error"
        }
    except Exception as e:
        logger.error(f"❌ Error in {test_name}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "test_name": test_name,
            "status": "error",
            "test_passed": False,
            "error": str(e)
        }

def run_all_tests():
    """Run all test cases organized by category"""
    
    logger.info("🚀 STARTING TRAILING STOP STRATEGY TESTS")
    logger.info("=" * 80)
    logger.info("📋 Test Categories:")
    logger.info("   1. Valid Payload Tests (Should Pass)")
    logger.info("   2. Type Safety Tests (String to Float Conversion)")
    logger.info("   3. Validation Tests (callbackRate Limits)")
    logger.info("   4. Error Handling Tests (Invalid Inputs)")
    logger.info("   5. Edge Case Tests (Boundary Values)")
    logger.info("=" * 80)
    
    # ========================================================================
    # TEST CATEGORIES
    # ========================================================================
    tests = [
        # Category 1: Valid Payload Tests (Should Pass)
        {
            "category": "Valid Payloads",
            "name": "1.1 Trailing Stop - LDO (LONG, Auto Calculate)",
            "payload": trailing_stop_long_payload,
            "expected_status": "success",
            "enabled": True
        },
        {
            "category": "Valid Payloads",
            "name": "1.2 Trailing Stop - SHORT Position",
            "payload": trailing_stop_short_payload,
            "expected_status": "success",
            "enabled": True
        },
        {
            "category": "Valid Payloads",
            "name": "1.3 Trailing Stop - Full Payload (All Fields)",
            "payload": trailing_stop_full_payload,
            "expected_status": "success",
            "enabled": True
        },
        
        # Category 2: Type Safety Tests (String to Float Conversion)
        {
            "category": "Type Safety",
            "name": "2.1 callbackRate String Format (\"1.5\")",
            "payload": trailing_stop_callback_string_payload,
            "expected_status": "success",
            "enabled": True
        },
        {
            "category": "Type Safety",
            "name": "2.2 callbackRate with % Sign (\"1.5%\")",
            "payload": trailing_stop_callback_percent_payload,
            "expected_status": "success",
            "enabled": True
        },
        {
            "category": "Type Safety",
            "name": "2.3 Invalid activationPrice Format (Auto-Calculate)",
            "payload": trailing_stop_invalid_activation,
            "expected_status": "success",
            "enabled": True
        },
        {
            "category": "Type Safety",
            "name": "2.4 Invalid stopLoss Format (Auto-Calculate)",
            "payload": trailing_stop_invalid_stoploss,
            "expected_status": "success",
            "enabled": True
        },
        {
            "category": "Type Safety",
            "name": "2.5 Invalid workingType (Should Default)",
            "payload": trailing_stop_invalid_workingtype,
            "expected_status": "success",
            "enabled": True
        },
        
        # Category 3: Validation Tests (callbackRate Limits)
        {
            "category": "Validation",
            "name": "3.1 callbackRate Too Low (< 0.1%)",
            "payload": trailing_stop_callback_too_low,
            "expected_status": "error",
            "enabled": True
        },
        {
            "category": "Validation",
            "name": "3.2 callbackRate Too High (> 5.0%)",
            "payload": trailing_stop_callback_too_high,
            "expected_status": "error",
            "enabled": True
        },
        {
            "category": "Validation",
            "name": "3.3 callbackRate at Minimum (0.1%)",
            "payload": trailing_stop_callback_min,
            "expected_status": "success",
            "enabled": True
        },
        {
            "category": "Validation",
            "name": "3.4 callbackRate at Maximum (5.0%)",
            "payload": trailing_stop_callback_max,
            "expected_status": "success",
            "enabled": True
        },
        
        # Category 4: Error Handling Tests (Invalid Inputs)
        {
            "category": "Error Handling",
            "name": "4.1 Missing callbackRate (Required Field)",
            "payload": invalid_missing_callbackrate,
            "expected_status": "error",
            "enabled": True
        },
        {
            "category": "Error Handling",
            "name": "4.2 Missing Multiple Fields",
            "payload": invalid_missing_fields,
            "expected_status": "error",
            "enabled": True
        },
        
        # Category 5: Standard Strategy (Old Logic)
        {
            "category": "Legacy",
            "name": "5.1 Standard Strategy (Old Logic)",
            "payload": standard_payload,
            "expected_status": "success",
            "enabled": False  # Set to True to test standard strategy
        }
    ]
    
    # Organize tests by category
    categories = {}
    for test in tests:
        category = test["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(test)
    
    results = []
    
    # Run tests by category
    for category_name, category_tests in categories.items():
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"📂 CATEGORY: {category_name}")
        logger.info("=" * 80)
        
        for test in category_tests:
            if test["enabled"]:
                result = send_webhook(
                    test["payload"], 
                    test["name"],
                    test["expected_status"]
                )
                if result:
                    results.append({
                        "category": category_name,
                        "test": test["name"],
                        "expected": test["expected_status"],
                        "actual": result.get("status", "unknown"),
                        "passed": result.get("test_passed", False),
                        "result": result
                    })
                
                time.sleep(1)  # Wait between tests to avoid rate limiting
            else:
                logger.info(f"⏭️ SKIPPING: {test['name']}")
    
    # ========================================================================
    # TEST SUMMARY
    # ========================================================================
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 DETAILED TEST SUMMARY")
    logger.info("=" * 80)
    
    # Group by category
    for category_name in categories.keys():
        category_results = [r for r in results if r["category"] == category_name]
        if category_results:
            logger.info("")
            logger.info(f"📂 {category_name}:")
            
            for result in category_results:
                status_icon = "✅" if result["passed"] else "❌"
                logger.info(f"   {status_icon} {result['test']}")
                logger.info(f"      Expected: {result['expected']}, Got: {result['actual']}")
    
    # Overall statistics
    logger.info("")
    logger.info("=" * 80)
    logger.info("📈 OVERALL STATISTICS")
    logger.info("=" * 80)
    
    total_tests = len(results)
    passed_tests = len([r for r in results if r["passed"]])
    failed_tests = total_tests - passed_tests
    
    logger.info(f"   Total Tests: {total_tests}")
    logger.info(f"   ✅ Passed: {passed_tests}")
    logger.info(f"   ❌ Failed: {failed_tests}")
    
    if total_tests > 0:
        pass_rate = (passed_tests / total_tests) * 100
        logger.info(f"   Pass Rate: {pass_rate:.1f}%")
    
    logger.info("=" * 80)
    logger.info("🏁 ALL TESTS COMPLETED")
    logger.info("=" * 80)
    
    return results

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

