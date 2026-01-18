#!/bin/bash
# Trailing Stop Monitoring Script
# Bu script düzeltmeden sonra trailing stop siparişlerini izler

echo "=========================================="
echo "TRAILING STOP MONITORING"
echo "=========================================="
echo ""

# Renkli çıktı için
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

LOG_FILE="logs/app.log"

# Menü
echo "Select monitoring option:"
echo ""
echo "1. Real-time log monitoring (trailing stops only)"
echo "2. Check recent successful trailing stops"
echo "3. Check recent errors"
echo "4. Check API endpoint usage (old vs new)"
echo "5. Full analysis (all checks)"
echo "6. Exit"
echo ""
read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        echo -e "${BLUE}[MONITORING]${NC} Real-time trailing stop logs..."
        echo "Press CTRL+C to stop"
        echo ""
        tail -f "$LOG_FILE" | grep --line-buffered -E "(TRAILING STOP|Algo Order API|futures_create_algo_order|✅.*Trailing stop|❌.*Trailing Stop)"
        ;;
    2)
        echo -e "${BLUE}[CHECK]${NC} Recent successful trailing stops..."
        echo ""
        grep -E "(🔧 Using Algo Order API|✅ Trailing stop order placed|Algo ID:)" "$LOG_FILE" | tail -n 50
        
        count=$(grep -c "✅ Trailing stop order placed" "$LOG_FILE")
        echo ""
        echo -e "${GREEN}Total successful trailing stops: $count${NC}"
        ;;
    3)
        echo -e "${BLUE}[CHECK]${NC} Recent errors..."
        echo ""
        grep -E "(❌ Trailing Stop Attempt.*FAILED|Error Code:|Error Message:)" "$LOG_FILE" | tail -n 100
        
        error_count=$(grep -c "❌ Trailing Stop Attempt.*FAILED" "$LOG_FILE")
        echo ""
        echo -e "${RED}Total failed attempts: $error_count${NC}"
        
        # Hata kodlarını say
        echo ""
        echo "Error breakdown:"
        grep -A 1 "❌ Trailing Stop Attempt" "$LOG_FILE" | grep "Error Code:" | sort | uniq -c
        ;;
    4)
        echo -e "${BLUE}[CHECK]${NC} API endpoint usage..."
        echo ""
        
        new_api_count=$(grep -c "Using Algo Order API (futures_create_algo_order)" "$LOG_FILE")
        old_api_count=$(grep -c "TRAILING_STOP_MARKET" "$LOG_FILE" | grep -v "Using Algo Order API")
        error_4120_count=$(grep -c "Error Code: -4120" "$LOG_FILE")
        
        echo "📊 Statistics:"
        echo ""
        echo -e "  ${GREEN}New API (futures_create_algo_order):${NC} $new_api_count times"
        echo -e "  ${YELLOW}Error -4120 (wrong endpoint):${NC} $error_4120_count times"
        echo ""
        
        if [ "$new_api_count" -gt 0 ]; then
            echo -e "${GREEN}✓ New API is being used!${NC}"
        else
            echo -e "${RED}✗ New API not detected in logs${NC}"
        fi
        
        if [ "$error_4120_count" -eq 0 ]; then
            echo -e "${GREEN}✓ No more -4120 errors!${NC}"
        else
            echo -e "${YELLOW}⚠ Still seeing -4120 errors (may be old logs)${NC}"
        fi
        ;;
    5)
        echo -e "${BLUE}[ANALYSIS]${NC} Running full analysis..."
        echo ""
        
        # 1. Toplam webhook
        webhook_count=$(grep -c "Webhook received.*trailType.*TRAILING_STOP" "$LOG_FILE")
        echo -e "${BLUE}1. Total trailing stop webhooks received:${NC} $webhook_count"
        
        # 2. Başarılı trailing stops
        success_count=$(grep -c "✅ Trailing stop order placed" "$LOG_FILE")
        echo -e "${BLUE}2. Successful trailing stops:${NC} ${GREEN}$success_count${NC}"
        
        # 3. Başarısız trailing stops
        fail_count=$(grep -c "❌ Trailing Stop Attempt.*FAILED" "$LOG_FILE")
        echo -e "${BLUE}3. Failed trailing stop attempts:${NC} ${RED}$fail_count${NC}"
        
        # 4. Fallback TP/SL kullanımı
        fallback_count=$(grep -c "TRAILING STOP FAILED - PLACING FALLBACK" "$LOG_FILE")
        echo -e "${BLUE}4. Fallback TP/SL used:${NC} ${YELLOW}$fallback_count${NC}"
        
        # 5. API endpoint kullanımı
        new_api_count=$(grep -c "Using Algo Order API" "$LOG_FILE")
        echo -e "${BLUE}5. New API usage (futures_create_algo_order):${NC} ${GREEN}$new_api_count${NC}"
        
        # 6. Hata kodları
        echo ""
        echo -e "${BLUE}6. Error breakdown:${NC}"
        error_4120=$(grep -c "Error Code: -4120" "$LOG_FILE")
        error_2007=$(grep -c "Error Code: -2007" "$LOG_FILE")
        echo "   Error -4120 (wrong endpoint): $error_4120"
        echo "   Error -2007 (invalid callback): $error_2007"
        
        # 7. Başarı oranı
        if [ "$webhook_count" -gt 0 ]; then
            success_rate=$(awk "BEGIN {printf \"%.1f\", ($success_count / $webhook_count) * 100}")
            echo ""
            echo -e "${BLUE}7. Success rate:${NC} ${GREEN}$success_rate%${NC}"
        fi
        
        # 8. Son 5 trailing stop denemesi
        echo ""
        echo -e "${BLUE}8. Last 5 trailing stop attempts:${NC}"
        grep -E "(🚀 TRAILING STOP STRATEGY - STARTING|✅ Trailing stop order placed|❌ Trailing Stop Attempt.*FAILED)" "$LOG_FILE" | tail -n 15
        
        # 9. CallbackRate düzeltmeleri
        echo ""
        echo -e "${BLUE}9. CallbackRate adjustments:${NC}"
        callback_adjusted=$(grep -c "callbackRate.*is below minimum\|callbackRate.*is above maximum" "$LOG_FILE")
        echo "   Auto-adjusted callbackRate: $callback_adjusted times"
        
        if [ "$callback_adjusted" -gt 0 ]; then
            grep "callbackRate.*is below minimum\|callbackRate.*is above maximum" "$LOG_FILE" | tail -n 5
        fi
        
        echo ""
        echo "=========================================="
        echo -e "${GREEN}✓ ANALYSIS COMPLETE${NC}"
        echo "=========================================="
        ;;
    6)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac
