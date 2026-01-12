#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Trailing Stop Strategy - Real TradingView Signal Simulation
Her test gerçek bir TradingView alert'i gibi davranır.

Gerçek TradingView sinyal formatı:
{
    "symbol": "BTCUSDT.P",           # .P extension otomatik temizlenir
    "side": "SELL",                   # BUY (LONG) veya SELL (SHORT)
    "action": "open",
    "takeProfit": 89747.31,          # Opsiyonel - TP fiyatı
    "stopLoss": 91320.29,             # Opsiyonel - SL fiyatı (fallback hard stop)
    "trailType": "TRAILING_STOP_MARKET",
    "activationPrice": 90462.30,      # Opsiyonel - otomatik hesaplanabilir
    "callbackRate": 0.6303060804,     # Zorunlu - trailing yüzdesi (0.1-5.0%)
    "workingType": "MARK_PRICE"       # Opsiyonel - default: MARK_PRICE
}

NOT: quantity alanı YOK - settings'den order_size_percentage kullanılır
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
# GERÇEK TRADINGVIEW SİNYAL FORMATI - TEST PAYLOADS
# ============================================================================

# Referans: Gerçek TradingView sinyali (kullanıcıdan alınan)
# {
#     "symbol": "BTCUSDT.P",
#     "side": "SELL",
#     "action": "open",
#     "takeProfit": 89747.3139075959,
#     "stopLoss": 91320.2920528024,
#     "trailType": "TRAILING_STOP_MARKET",
#     "activationPrice": 90462.3039735988,
#     "callbackRate": 0.6303060804,
#     "workingType": "MARK_PRICE"
# }

# Test 1: Standard Strategy (Old Logic) - Legacy
standard_payload = {
    "signal": "BTCUSDT/long/open",
    "message": "BTCUSDT/long/open"
}

# Test 2: Gerçek TradingView Sinyali - LONG (LDOUSDT)
# Gerçek sinyal formatında, quantity YOK - settings'den alınacak
trailing_stop_long_payload = {
    "symbol": "LDOUSDT.P",           # .P extension var (temizlenecek)
    "side": "BUY",                    # LONG pozisyon
    "action": "open",
    "takeProfit": 0.65,               # TP fiyatı (opsiyonel)
    "stopLoss": 0.60,                 # SL fiyatı (fallback hard stop)
    "trailType": "TRAILING_STOP_MARKET",
    "activationPrice": 0.63,          # Activation price (opsiyonel)
    "callbackRate": 1.5,              # %1.5 trailing (valid: 0.1-5.0%)
    "workingType": "MARK_PRICE"
}

# Test 3: Gerçek TradingView Sinyali - LONG (ADAUSDT) - Full Payload
trailing_stop_full_payload = {
    "symbol": "ADAUSDT.P",
    "side": "BUY",
    "action": "open",
    "takeProfit": 0.40,
    "stopLoss": 0.37,
    "trailType": "TRAILING_STOP_MARKET",
    "activationPrice": 0.39,
    "callbackRate": 2.0,              # %2.0 trailing
    "workingType": "MARK_PRICE"
}

# Test 4: Gerçek TradingView Sinyali - SHORT (XLMUSDT)
trailing_stop_short_payload = {
    "symbol": "XLMUSDT.P",
    "side": "SELL",                   # SHORT pozisyon
    "action": "open",
    "takeProfit": 0.215,
    "stopLoss": 0.222,
    "trailType": "TRAILING_STOP_MARKET",
    "activationPrice": 0.218,
    "callbackRate": 1.5,
    "workingType": "MARK_PRICE"
}

# Test 5: callbackRate String Format (Gerçek sinyal - String olarak gelebilir)
trailing_stop_callback_string_payload = {
    "symbol": "DOTUSDT.P",
    "side": "BUY",
    "action": "open",
    "takeProfit": 2.10,
    "stopLoss": 1.98,
    "trailType": "TRAILING_STOP_MARKET",
    "activationPrice": 2.05,
    "callbackRate": "1.5",            # String format (should convert to float)
    "workingType": "MARK_PRICE"
}

# Test 6: callbackRate with Percentage Sign (Gerçek sinyal - % işareti ile gelebilir)
trailing_stop_callback_percent_payload = {
    "symbol": "UNIUSDT.P",
    "side": "BUY",
    "action": "open",
    "takeProfit": 5.50,
    "stopLoss": 5.20,
    "trailType": "TRAILING_STOP_MARKET",
    "activationPrice": 5.40,
    "callbackRate": "1.5%",           # String with % (should strip and convert)
    "workingType": "MARK_PRICE"
}

# Test 7: callbackRate Too Low (< 0.1%) - Should Fail Validation
trailing_stop_callback_too_low = {
    "symbol": "IMXUSDT.P",
    "side": "BUY",
    "action": "open",
    "takeProfit": 0.28,
    "stopLoss": 0.26,
    "trailType": "TRAILING_STOP_MARKET",
    "activationPrice": 0.27,
    "callbackRate": 0.05,             # Too low (< 0.1%) - should fail validation
    "workingType": "MARK_PRICE"
}

# Test 8: callbackRate Too High (> 5.0%) - Should Fail Validation
trailing_stop_callback_too_high = {
    "symbol": "ARBUSDT.P",
    "side": "BUY",
    "action": "open",
    "takeProfit": 1.20,
    "stopLoss": 1.10,
    "trailType": "TRAILING_STOP_MARKET",
    "activationPrice": 1.15,
    "callbackRate": 6.0,              # Too high (> 5.0%) - should fail validation
    "workingType": "MARK_PRICE"
}

# Test 9: callbackRate at Lower Limit (0.1%) - Should Pass
trailing_stop_callback_min = {
    "symbol": "INJUSDT.P",
    "side": "BUY",
    "action": "open",
    "takeProfit": 5.50,
    "stopLoss": 5.00,
    "trailType": "TRAILING_STOP_MARKET",
    "activationPrice": 5.25,
    "callbackRate": 0.1,              # Minimum valid (0.1%) - should pass
    "workingType": "MARK_PRICE"
}

# Test 10: callbackRate at Upper Limit (5.0%) - Should Pass
trailing_stop_callback_max = {
    "symbol": "SOLUSDT.P",
    "side": "BUY",
    "action": "open",
    "takeProfit": 145.0,
    "stopLoss": 135.0,
    "trailType": "TRAILING_STOP_MARKET",
    "activationPrice": 140.0,
    "callbackRate": 5.0,              # Maximum valid (5.0%) - should pass
    "workingType": "MARK_PRICE"
}

# Test 11: Missing callbackRate (Should Fail - Required Field)
invalid_missing_callbackrate = {
    "symbol": "ETHUSDT.P",
    "side": "BUY",
    "action": "open",
    "takeProfit": 3500.0,
    "stopLoss": 3400.0,
    "trailType": "TRAILING_STOP_MARKET",
    "activationPrice": 3450.0,
    "workingType": "MARK_PRICE"
    # Missing: callbackRate (required)
}

# Test 12: Missing Multiple Fields (Should Fail)
invalid_missing_fields = {
    "symbol": "BNBUSDT.P",
    "side": "BUY",
    "trailType": "TRAILING_STOP_MARKET"
    # Missing: callbackRate, action, workingType
}

# Test 13: Invalid workingType (Should Default to MARK_PRICE)
trailing_stop_invalid_workingtype = {
    "symbol": "FETUSDT.P",
    "side": "BUY",
    "action": "open",
    "takeProfit": 0.30,
    "stopLoss": 0.28,
    "trailType": "TRAILING_STOP_MARKET",
    "activationPrice": 0.29,
    "callbackRate": 1.5,
    "workingType": "INVALID_TYPE"     # Invalid - should default to MARK_PRICE
}

# Test 14: Invalid activationPrice Format (Should Auto-Calculate)
trailing_stop_invalid_activation = {
    "symbol": "DOGEUSDT.P",
    "side": "BUY",
    "action": "open",
    "takeProfit": 0.15,
    "stopLoss": 0.13,
    "trailType": "TRAILING_STOP_MARKET",
    "activationPrice": "invalid",     # Invalid format - should auto-calculate
    "callbackRate": 1.5,
    "workingType": "MARK_PRICE"
}

# Test 15: Invalid stopLoss Format (Should Auto-Calculate)
trailing_stop_invalid_stoploss = {
    "symbol": "BTCUSDT.P",
    "side": "BUY",
    "action": "open",
    "takeProfit": 92000.0,
    "stopLoss": "invalid",            # Invalid format - should auto-calculate
    "trailType": "TRAILING_STOP_MARKET",
    "activationPrice": 91000.0,
    "callbackRate": 1.5,
    "workingType": "MARK_PRICE"
}

# Test 16: Gerçek TradingView Payload - BTCUSDT.P SHORT (Kullanıcıdan alınan)
# "BTC Short High-PF Streamlined (Binance Futures TRAILING_STOP payload)"
trailing_stop_real_btc_short_payload = {
    "symbol": "BTCUSDT.P",            # .P extension var (temizlenecek)
    "side": "SELL",                    # SHORT pozisyon
    "action": "open",
    "takeProfit": 89747.3139075959,
    "stopLoss": 91320.2920528024,
    "trailType": "TRAILING_STOP_MARKET",
    "activationPrice": 90462.3039735988,
    "callbackRate": 0.6303060804,     # %0.63 trailing (geçerli: 0.1-5.0 arası)
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
    """
    Run all test cases organized by category
    
    Her test gerçek bir TradingView alert'i gibi davranır:
    - .P extension'ları otomatik temizlenir
    - quantity yok - settings'den order_size_percentage kullanılır
    - takeProfit ve stopLoss değerleri gerçek sinyallerde olduğu gibi
    - Her test gerçek bir emir simülasyonu yapar
    """
    
    logger.info("🚀 STARTING TRAILING STOP STRATEGY TESTS")
    logger.info("=" * 80)
    logger.info("📋 Test Categories:")
    logger.info("   1. Valid Payload Tests (Should Pass) - Gerçek TradingView Sinyalleri")
    logger.info("   2. Type Safety Tests (String to Float Conversion)")
    logger.info("   3. Validation Tests (callbackRate Limits)")
    logger.info("   4. Error Handling Tests (Invalid Inputs)")
    logger.info("   5. Real TradingView Payloads (From Actual Alerts)")
    logger.info("   6. Standard Strategy (Old Logic) - Legacy")
    logger.info("")
    logger.info("⚠️  UYARI: Her test gerçek bir emir simülasyonu yapar!")
    logger.info("    - Pozisyon açılır")
    logger.info("    - Trailing stop yerleştirilir")
    logger.info("    - Auto switch aktif: Duplicate pozisyonlar oluşmaz")
    logger.info("      (Aynı sembol için zıt pozisyon varsa otomatik kapatılır)")
    logger.info("=" * 80)
    
    # ========================================================================
    # TEST CATEGORIES
    # ========================================================================
    tests = [
        # Category 1: Valid Payload Tests (Should Pass) - Gerçek TradingView Sinyalleri
        {
            "category": "Valid Payloads",
            "name": "1.1 Gerçek Sinyal - LDOUSDT.P LONG (TradingView Format)",
            "payload": trailing_stop_long_payload,
            "expected_status": "success",
            "enabled": True
        },
        {
            "category": "Valid Payloads",
            "name": "1.2 Gerçek Sinyal - XLMUSDT.P SHORT (TradingView Format)",
            "payload": trailing_stop_short_payload,
            "expected_status": "success",
            "enabled": True
        },
        {
            "category": "Valid Payloads",
            "name": "1.3 Gerçek Sinyal - ADAUSDT.P LONG (Full Payload)",
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
        
        # Category 5: Real TradingView Payloads (Kullanıcıdan Alınan Gerçek Sinyaller)
        {
            "category": "Real TradingView Payloads",
            "name": "5.1 Gerçek BTCUSDT.P SHORT (Kullanıcıdan Alınan TradingView Alert)",
            "payload": trailing_stop_real_btc_short_payload,
            "expected_status": "success",
            "enabled": True  # Gerçek payload testi - kullanıcıdan alınan sinyal
        },
        
        # Category 6: Standard Strategy (Old Logic)
        {
            "category": "Legacy",
            "name": "6.1 Standard Strategy (Old Logic)",
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

