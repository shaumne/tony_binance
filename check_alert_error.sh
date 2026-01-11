#!/bin/bash
# JP saatlerinde oluşan alert'leri, webhook'ları ve pozisyon sonuçlarını bulma komutu
# NOT: Sistem UTC formatında çalışıyor. JST = UTC + 9 saat

LOG_FILE="logs/app.log"

# JP saatleri ve UTC karşılıkları
# JST 08:10 = UTC 23:10 (önceki gün)
# JST 07:07 = UTC 22:07 (önceki gün)
# JST 06:06 = UTC 21:06 (önceki gün)
# JST 02:52 = UTC 17:52 (önceki gün)
# JST 00:29 = UTC 15:29 (önceki gün)

# Timezone bilgisi
echo "=========================================="
echo "JP SAATLERİ ALERT & WEBHOOK ANALİZİ"
echo "=========================================="
echo ""
echo "⚠️  NOT: Sistem UTC formatında çalışıyor"
echo "    JST (Japonya Saati) = UTC + 9 saat"
echo ""
echo "📋 Analiz edilecek saatler:"
echo "   JST 08:10 → UTC 23:10 (önceki gün)"
echo "   JST 07:07 → UTC 22:07 (önceki gün)"
echo "   JST 06:06 → UTC 21:06 (önceki gün)"
echo "   JST 02:52 → UTC 17:52 (önceki gün)"
echo "   JST 00:29 → UTC 15:29 (önceki gün)"
echo ""
echo "=========================================="
echo ""

# Fonksiyon: Belirli bir UTC saati için webhook, pozisyon ve hata analizi
analyze_time() {
    local jst_time=$1
    local utc_time=$2
    local time_label=$3
    
    echo ""
    echo "=========================================="
    echo "🕐 $time_label (JST $jst_time → UTC $utc_time)"
    echo "=========================================="
    echo ""
    
    # UTC saat formatı (örn: 15:29)
    utc_hour=$(echo $utc_time | cut -d: -f1)
    utc_min=$(echo $utc_time | cut -d: -f2)
    
    # 1. Webhook alındı mesajları
    echo "📥 1. WEBHOOK ALINDI MESAJLARI:"
    echo "---------------------------------------------------"
    webhook_count=$(grep -E "202[0-9]-[0-9]{2}-[0-9]{2}.*${utc_hour}:${utc_min}:[0-9]{2}" "$LOG_FILE" | \
      grep -c "Webhook received" 2>/dev/null || echo "0")
    
    if [ "$webhook_count" -gt 0 ]; then
        echo "📊 Toplam webhook sayısı: $webhook_count"
        echo ""
        grep -E "202[0-9]-[0-9]{2}-[0-9]{2}.*${utc_hour}:${utc_min}:[0-9]{2}" "$LOG_FILE" | \
          grep -E "Webhook received|webhook received" | \
          tail -10 | while read line; do
            # Tarih ve zamanı göster
            timestamp=$(echo "$line" | grep -oE "202[0-9]-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}" | head -1)
            # Webhook içeriğini parse et
            if echo "$line" | grep -q "trailType.*TRAILING_STOP_MARKET"; then
                # Trailing stop webhook
                symbol=$(echo "$line" | grep -oE "'symbol': '[^']*'" | cut -d"'" -f4 || echo "N/A")
                side=$(echo "$line" | grep -oE "'side': '[^']*'" | cut -d"'" -f4 || echo "N/A")
                callback=$(echo "$line" | grep -oE "'callbackRate': [0-9.]+" | cut -d" " -f2 || echo "N/A")
                echo "  🕐 $timestamp | 🔥 TRAILING STOP | Symbol: $symbol | Side: $side | Callback: ${callback}%"
            else
                # Standard webhook
                signal=$(echo "$line" | grep -oE "'signal': '[^']*'" | cut -d"'" -f4 || echo "N/A")
                echo "  🕐 $timestamp | 📨 Standard | Signal: $signal"
            fi
          done
    else
        echo "⚠️  Bu saatte webhook bulunamadı"
    fi
    
    echo ""
    
    # 2. Entry order sonuçları
    echo "📤 2. ENTRY ORDER SONUÇLARI:"
    echo "---------------------------------------------------"
    entry_results=$(grep -E "202[0-9]-[0-9]{2}-[0-9]{2}.*${utc_hour}:${utc_min}:[0-9]{2}" "$LOG_FILE" -A 100 | \
      grep -E "ENTRY ORDER PLACED SUCCESSFULLY|ENTRY ORDER FILLED SUCCESSFULLY|ENTRY ORDER FAILED|Order ID.*[0-9]|entry_order_id|APIError.*code=-4164|Notional.*below minimum" | \
      head -20)
    
    if [ ! -z "$entry_results" ]; then
        echo "$entry_results" | while read line; do
            # Başarılı entry order
            if echo "$line" | grep -qE "ENTRY ORDER.*SUCCESSFULLY|ENTRY ORDER FILLED"; then
                order_id=$(echo "$line" | grep -oE "Order ID: [0-9]+|orderId.*[0-9]+" | head -1 | grep -oE "[0-9]+" | head -1)
                echo "  ✅ Entry Order Başarılı | Order ID: $order_id"
            # Başarısız entry order
            elif echo "$line" | grep -qE "ENTRY ORDER FAILED|APIError.*code=-4164|Notional.*below minimum"; then
                error_msg=$(echo "$line" | grep -oE "APIError.*code=-[0-9]+|Notional.*below minimum|Entry order.*failed" | head -1)
                echo "  ❌ Entry Order Başarısız | $error_msg"
            # Order ID
            elif echo "$line" | grep -qE "Order ID|entry_order_id"; then
                order_id=$(echo "$line" | grep -oE "[0-9]+" | head -1)
                echo "    └─ Order ID: $order_id"
            fi
        done
    else
        echo "⚠️  Entry order sonucu bulunamadı"
    fi
    
    echo ""
    
    # 3. Trailing stop sonuçları
    echo "🎯 3. TRAILING STOP SONUÇLARI:"
    echo "---------------------------------------------------"
    trailing_results=$(grep -E "202[0-9]-[0-9]{2}-[0-9]{2}.*${utc_hour}:${utc_min}:[0-9]{2}" "$LOG_FILE" -A 150 | \
      grep -E "TRAILING STOP ORDER PLACED SUCCESSFULLY|TRAILING STOP.*FAILED|FALLBACK.*STOP_MARKET|FALLBACK.*PLACED|callbackRate.*validated|trailing_stop_id.*[0-9]+" | \
      grep -v "Webhook received" | \
      head -25)
    
    if [ ! -z "$trailing_results" ]; then
        echo "$trailing_results" | while read line; do
            # Başarılı trailing stop
            if echo "$line" | grep -qE "TRAILING STOP ORDER PLACED SUCCESSFULLY"; then
                order_id=$(echo "$line" | grep -oE "Order ID.*[0-9]+|orderId.*[0-9]+" | grep -oE "[0-9]+" | head -1)
                echo "  ✅ Trailing Stop Başarılı | Order ID: $order_id"
            # Fallback stop
            elif echo "$line" | grep -qE "FALLBACK.*STOP_MARKET|FALLBACK.*PLACED"; then
                order_id=$(echo "$line" | grep -oE "Order ID.*[0-9]+|orderId.*[0-9]+" | grep -oE "[0-9]+" | head -1)
                echo "  ⚠️  Fallback Stop (Hard Stop) | Order ID: $order_id"
            # Başarısız trailing stop
            elif echo "$line" | grep -qE "TRAILING STOP.*FAILED"; then
                error_msg=$(echo "$line" | grep -oE "code=-[0-9]+|Invalid.*callback|Error.*trailing" | head -1)
                echo "  ❌ Trailing Stop Başarısız | $error_msg"
            # Callback rate validated
            elif echo "$line" | grep -qE "callbackRate.*validated"; then
                callback=$(echo "$line" | grep -oE "[0-9.]+%" | head -1)
                echo "    └─ Callback Rate: $callback (validated)"
            fi
        done
    else
        echo "⚠️  Trailing stop sonucu bulunamadı (standart strateji veya trailing stop yok)"
    fi
    
    echo ""
    
    # 4. Hata mesajları (sadece gerçek hatalar)
    echo "❌ 4. HATA MESAJLARI:"
    echo "---------------------------------------------------"
    error_results=$(grep -E "202[0-9]-[0-9]{2}-[0-9]{2}.*${utc_hour}:${utc_min}:[0-9]{2}" "$LOG_FILE" -A 100 | \
      grep -E "__main__.*ERROR|binance_handler.*ERROR|❌.*ORDER.*FAILED|❌.*ERROR|APIError.*code=-|Exception.*:" | \
      grep -vE "INFO.*OK|INFO.*READY|INFO.*Coin Config Manager" | \
      head -20)
    
    if [ ! -z "$error_results" ]; then
        echo "$error_results" | while read line; do
            # ERROR seviyesi loglar
            if echo "$line" | grep -qE "__main__.*ERROR|binance_handler.*ERROR"; then
                error_msg=$(echo "$line" | sed 's/.*ERROR - //' | sed 's/.*❌ //')
                timestamp=$(echo "$line" | grep -oE "202[0-9]-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}" | head -1)
                echo "  🕐 $timestamp | ❌ $error_msg"
            # API Error
            elif echo "$line" | grep -qE "APIError.*code=-"; then
                error_code=$(echo "$line" | grep -oE "code=-[0-9]+" | head -1)
                error_msg=$(echo "$line" | sed 's/.*APIError(//' | sed 's/).*//')
                echo "  ❌ API Error $error_code | $error_msg"
            fi
        done
    else
        echo "✅ Bu saatte hata bulunamadı"
    fi
    
    echo ""
    
    # 5. Pozisyon bilgileri
    echo "📍 5. POZİSYON BİLGİLERİ:"
    echo "---------------------------------------------------"
    position_results=$(grep -E "202[0-9]-[0-9]{2}-[0-9]{2}.*${utc_hour}:${utc_min}:[0-9]{2}" "$LOG_FILE" -A 100 | \
      grep -E "Position verified.*LONG|Position verified.*SHORT|Position Size: [0-9.]+|Entry Price:.*[0-9]|Found [0-9]+ active positions" | \
      head -15)
    
    if [ ! -z "$position_results" ]; then
        echo "$position_results" | while read line; do
            # Position verified
            if echo "$line" | grep -qE "Position verified"; then
                direction=$(echo "$line" | grep -oE "LONG|SHORT" | head -1)
                size=$(echo "$line" | grep -oE "Position Size: [0-9.]+" | grep -oE "[0-9.]+" | head -1)
                price=$(echo "$line" | grep -oE "Entry Price:.*[0-9.]+" | grep -oE "[0-9.]+" | head -1)
                echo "  ✅ Position Verified | Direction: $direction | Size: $size | Entry: $price"
            # Active positions count
            elif echo "$line" | grep -qE "Found.*active positions"; then
                count=$(echo "$line" | grep -oE "Found [0-9]+" | grep -oE "[0-9]+")
                echo "  📊 Active Positions: $count"
            fi
        done
    else
        echo "⚠️  Pozisyon bilgisi bulunamadı"
    fi
    
    echo ""
    
    # 6. Detaylı timeline (en son webhook'tan sonraki 200 satır)
    echo ""
    echo "📊 6. DETAYLI TIMELINE (En son webhook'tan sonraki önemli olaylar):"
    echo "---------------------------------------------------"
    # En son webhook satır numarasını bul
    last_webhook_line=$(grep -n "Webhook received.*${utc_hour}:${utc_min}" "$LOG_FILE" | tail -1 | cut -d: -f1)
    
    if [ ! -z "$last_webhook_line" ]; then
        sed -n "${last_webhook_line},$((last_webhook_line + 200))p" "$LOG_FILE" | \
          grep -E "(🔥 TRAILING STOP STRATEGY|📤 STEP 2|ENTRY ORDER.*SUCCESSFULLY|ENTRY ORDER.*FAILED|ENTRY ORDER FILLED|🎯 STEP 3|TRAILING STOP ORDER.*PLACED|TRAILING STOP.*FAILED|FALLBACK|✅✅✅|❌❌❌|Position verified|Order ID.*[0-9]+)" --color=always | \
          head -50
    else
        echo "⚠️  Webhook satırı bulunamadı"
    fi
    
    echo ""
    echo "---"
}

# Her saat için analiz yap
analyze_time "00:29" "15:29" "JP SAATİ 00:29"
analyze_time "02:52" "17:52" "JP SAATİ 02:52"
analyze_time "06:06" "21:06" "JP SAATİ 06:06"
analyze_time "07:07" "22:07" "JP SAATİ 07:07"
analyze_time "08:10" "23:10" "JP SAATİ 08:10"

echo ""
echo ""

echo ""
echo "=========================================="
echo "ÖZET VE ÖNERİLEN KOMUTLAR"
echo "=========================================="
echo ""
echo "📋 Analiz edilen saatler:"
echo "   JST 00:29 → UTC 15:29"
echo "   JST 02:52 → UTC 17:52"
echo "   JST 06:06 → UTC 21:06"
echo "   JST 07:07 → UTC 22:07"
echo "   JST 08:10 → UTC 23:10"
echo ""
echo "💡 Manuel arama komutları:"
echo ""
echo "1. JST 00:29 (UTC 15:29) için:"
echo "   grep -E '15:29:[0-9]{2}' logs/app.log -B 30 -A 200 | grep -E '(Webhook|TRAILING|ENTRY|ERROR|Position)' --color=always | less"
echo ""
echo "2. JST 02:52 (UTC 17:52) için:"
echo "   grep -E '17:52:[0-9]{2}' logs/app.log -B 30 -A 200 | grep -E '(Webhook|TRAILING|ENTRY|ERROR|Position)' --color=always | less"
echo ""
echo "3. JST 06:06 (UTC 21:06) için:"
echo "   grep -E '21:06:[0-9]{2}' logs/app.log -B 30 -A 200 | grep -E '(Webhook|TRAILING|ENTRY|ERROR|Position)' --color=always | less"
echo ""
echo "4. JST 07:07 (UTC 22:07) için:"
echo "   grep -E '22:07:[0-9]{2}' logs/app.log -B 30 -A 200 | grep -E '(Webhook|TRAILING|ENTRY|ERROR|Position)' --color=always | less"
echo ""
echo "5. JST 08:10 (UTC 23:10) için:"
echo "   grep -E '23:10:[0-9]{2}' logs/app.log -B 30 -A 200 | grep -E '(Webhook|TRAILING|ENTRY|ERROR|Position)' --color=always | less"
echo ""
echo "6. Tüm saatler için webhook mesajları:"
echo "   grep -E '(15:29|17:52|21:06|22:07|23:10):[0-9]{2}' logs/app.log | grep -E 'Webhook received' --color=always"
echo ""
echo "7. Tüm saatler için hata mesajları:"
echo "   grep -E '(15:29|17:52|21:06|22:07|23:10):[0-9]{2}' logs/app.log -A 100 | grep -E '(ERROR|error|FAILED|failed|Exception|❌)' --color=always"
echo ""
echo "=========================================="
echo "ANALİZ TAMAMLANDI"
echo "=========================================="

