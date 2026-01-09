#!/bin/bash
# Log Analiz Komutları - Ubuntu Server için
# Binance Bot Log Analizi

LOG_FILE="logs/app.log"
CURRENT_DATE=$(date +"%Y-%m-%d")

echo "=========================================="
echo "BINANCE BOT LOG ANALİZİ"
echo "Tarih: $CURRENT_DATE"
echo "=========================================="
echo ""

# 1. TRAILING STOP STRATEGY LOGLARI
echo "1. TRAILING STOP STRATEGY LOGLARI (Son 100 satır):"
echo "---------------------------------------------------"
tail -n 100 "$LOG_FILE" | grep -i "trailing stop" | tail -20
echo ""

# 2. TRAILING STOP ORDER BAŞARISIZLIKLARI
echo "2. TRAILING STOP ORDER BAŞARISIZLIKLARI:"
echo "---------------------------------------------------"
grep -i "trailing.*failed\|trailing.*error\|trailing stop.*rejected" "$LOG_FILE" | tail -20
echo ""

# 3. ORDER PLACEMENT LOGLARI (Son 1 saat)
echo "3. ORDER PLACEMENT LOGLARI (Son 1 saat):"
echo "---------------------------------------------------"
grep -i "order.*placed\|order.*success\|order.*failed" "$LOG_FILE" | tail -30
echo ""

# 4. TP/SL ORDER PLACEMENT LOGLARI
echo "4. TP/SL ORDER PLACEMENT LOGLARI:"
echo "---------------------------------------------------"
grep -i "tp/sl\|take profit\|stop loss\|TP ORDER\|SL ORDER" "$LOG_FILE" | tail -30
echo ""

# 5. POSITION VALIDATION LOGLARI (Auto Position Switch)
echo "5. POSITION VALIDATION LOGLARI (Auto Position Switch):"
echo "---------------------------------------------------"
grep -i "position.*validation\|auto position\|duplicate.*position\|already have.*position" "$LOG_FILE" | tail -30
echo ""

# 6. WEBHOOK RECEIVED LOGLARI
echo "6. WEBHOOK RECEIVED LOGLARI (Son 50):"
echo "---------------------------------------------------"
grep -i "webhook received\|trailType\|TRAILING_STOP" "$LOG_FILE" | tail -50
echo ""

# 7. ERROR LOGLARI (Son 2 saat)
echo "7. ERROR LOGLARI (Son 2 saat):"
echo "---------------------------------------------------"
grep -i "error\|failed\|exception\|traceback" "$LOG_FILE" | tail -40
echo ""

# 8. ENTRY ORDER BAŞARILI AMA TRAILING STOP BAŞARISIZ OLANLAR
echo "8. ENTRY ORDER BAŞARILI AMA TRAILING STOP BAŞARISIZ:"
echo "---------------------------------------------------"
grep -A 10 "ENTRY ORDER PLACED SUCCESSFULLY" "$LOG_FILE" | grep -B 5 -A 10 "TRAILING STOP.*FAILED\|FALLBACK" | tail -30
echo ""

# 9. AYNı COİN İÇİN HEM LONG HEM SHORT POZİSYONLAR
echo "9. AYNI COİN İÇİN HEM LONG HEM SHORT POZİSYONLAR:"
echo "---------------------------------------------------"
grep -i "both.*long.*short\|conflict\|duplicate position" "$LOG_FILE" | tail -20
echo ""

# 10. SON 1 SAAT İÇİNDEKİ TÜM ÖNEMLİ OLAYLAR (Zaman Damgalı)
echo "10. SON 1 SAAT İÇİNDEKİ TÜM ÖNEMLİ OLAYLAR:"
echo "---------------------------------------------------"
tail -n 2000 "$LOG_FILE" | grep -E "(TRAILING STOP|ORDER PLACED|TP/SL|POSITION|WEBHOOK|ERROR)" | tail -50
echo ""

# 11. TRAILING STOP PARAMETRELERİ
echo "11. TRAILING STOP PARAMETRELERİ:"
echo "---------------------------------------------------"
grep -i "TRAILING STOP PARAMETERS\|callbackRate\|activationPrice" "$LOG_FILE" | tail -20
echo ""

# 12. FALLBACK STOP ORDER LOGLARI
echo "12. FALLBACK STOP ORDER LOGLARI:"
echo "---------------------------------------------------"
grep -i "FALLBACK\|fallback.*stop\|STOP_MARKET" "$LOG_FILE" | tail -20
echo ""

echo "=========================================="
echo "ANALİZ TAMAMLANDI"
echo "=========================================="

