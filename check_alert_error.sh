#!/bin/bash
# JP saati 00:28'de oluşan alert hatalarını bulma komutu
# NOT: Sistem UTC formatında çalışıyor. JST 00:28 = UTC 15:28 (önceki gün)

LOG_FILE="logs/app.log"

# Timezone bilgisi
echo "=========================================="
echo "JP SAATİ 00:28 ALERT HATA ANALİZİ"
echo "=========================================="
echo ""
echo "⚠️  NOT: Sistem UTC formatında çalışıyor"
echo "    JST (Japonya Saati) = UTC + 9 saat"
echo "    JST 00:28 = UTC 15:28 (önceki gün)"
echo ""
echo "    Örnek: 10 Ocak 2026 JST 00:28 = 9 Ocak 2026 UTC 15:28"
echo ""
echo "=========================================="
echo ""

# Ana arama: UTC 15:28 formatında (JST 00:28'e karşılık gelir)
echo "1. UTC 15:28:xx zamanındaki alert ve hata mesajları (JST 00:28 karşılığı):"
echo "---------------------------------------------------"
echo "Arama kriteri: 15:28:xx (UTC zamanı)"
echo ""

# UTC formatında 15:28:xx'i ara (JST 00:28'e karşılık gelir)
grep -E "202[0-9]-[0-9]{2}-[0-9]{2}.*15:28:[0-9]{2}" "$LOG_FILE" -B 30 -A 100 | \
  grep -E "(Webhook received|webhook|alert|TRAILING|ERROR|error|FAILED|failed|Exception|exception|Traceback|❌|⚠️|15:28)" --color=always | \
  head -80

echo ""
echo ""

# Tarih bazlı arama (önceki gün UTC 15:28)
echo "2. Önceki günün UTC 15:28:xx zamanındaki detaylı loglar:"
echo "---------------------------------------------------"
# Önceki günün tarihini hesapla (UTC bazlı)
PREV_DATE=$(date -u -d "yesterday" +"%Y-%m-%d" 2>/dev/null || date -u -v-1d +"%Y-%m-%d" 2>/dev/null || date -u --date="yesterday" +"%Y-%m-%d" 2>/dev/null || echo "")

if [ ! -z "$PREV_DATE" ]; then
    echo "Aranan tarih: $PREV_DATE (önceki gün UTC)"
    echo ""
    grep -E "$PREV_DATE.*15:28:[0-9]{2}" "$LOG_FILE" -B 20 -A 150 | \
      grep -E "(Webhook received|webhook|TRAILING_STOP|callbackRate|activationPrice|ERROR|error|FAILED|failed|Exception|exception|Traceback|❌|⚠️|15:28)" --color=always
else
    echo "⚠️  Tarih hesaplanamadı, manuel tarih ile arayın:"
    echo "    grep -E '2026-01-09.*15:28' logs/app.log -B 30 -A 100"
fi

echo ""
echo ""

# JST 00:28 için alternatif arama (doğrudan 00:28 string'i içeren satırlar)
echo "3. '00:28' string'ini içeren satırlar (eğer log JST formatındaysa):"
echo "---------------------------------------------------"
grep -n "00:28:[0-9]{2}" "$LOG_FILE" 2>/dev/null | head -5 | while IFS=: read line_num rest; do
    start_line=$((line_num - 20))
    end_line=$((line_num + 100))
    if [ $start_line -lt 1 ]; then start_line=1; fi
    echo ""
    echo ">>> Satır $line_num civarında (00:28 içeren):"
    sed -n "${start_line},${end_line}p" "$LOG_FILE" | grep -E "(ERROR|error|FAILED|failed|Exception|exception|Traceback|webhook|alert|TRAILING|00:28)" --color=always
    echo "---"
done

echo ""
echo ""

# En kapsamlı arama: UTC 15:28:xx formatı
echo "4. UTC 15:28:xx formatındaki TÜM satırlar ve hatalar (En kapsamlı):"
echo "---------------------------------------------------"
grep -n "15:28:[0-9]{2}" "$LOG_FILE" | tail -5 | while IFS=: read line_num rest; do
    if [ ! -z "$line_num" ]; then
        echo ""
        echo ">>> Satır $line_num (UTC 15:28:xx):"
        sed -n "${line_num},$((line_num + 200))p" "$LOG_FILE" | \
          grep -E "(Webhook received|webhook received|TRAILING_STOP|TRAILING STOP|callbackRate|activationPrice|ERROR|error|FAILED|failed|Exception|exception|Traceback|❌|⚠️|FALLBACK|Entry order|Trailing stop)" --color=always | \
          head -100
        echo "---"
    fi
done

echo ""
echo ""

# Özel tarih ile arama (10 Ocak 2026 JST 00:28 = 9 Ocak 2026 UTC 15:28)
echo "5. 9 Ocak 2026 UTC 15:28:xx (10 Ocak 2026 JST 00:28) için spesifik arama:"
echo "---------------------------------------------------"
grep -E "2026-01-09.*15:28:[0-9]{2}" "$LOG_FILE" -B 50 -A 200 | \
  grep -E "(2026-01-09 15:28|Webhook received|webhook|TRAILING|ERROR|error|FAILED|failed|Exception|exception|Traceback|❌|⚠️|FALLBACK|callbackRate|activationPrice|Entry order)" --color=always | \
  head -150

echo ""
echo ""
echo "=========================================="
echo "ÖNERİLEN KOMUTLAR:"
echo "=========================================="
echo ""
echo "1. En detaylı analiz (UTC 15:28 formatı):"
echo "   grep -E '15:28:[0-9]{2}' logs/app.log -B 50 -A 200 | less"
echo ""
echo "2. Spesifik tarih ile (9 Ocak 2026 UTC 15:28):"
echo "   grep -E '2026-01-09.*15:28' logs/app.log -B 50 -A 200 | less"
echo ""
echo "3. Sadece hata mesajları:"
echo "   grep -E '15:28:[0-9]{2}' logs/app.log -A 200 | grep -E '(ERROR|error|FAILED|failed|Exception|❌|⚠️)' --color=always"
echo ""
echo "4. Webhook ve alert mesajları:"
echo "   grep -E '15:28:[0-9]{2}' logs/app.log -B 30 -A 100 | grep -E '(Webhook received|webhook|alert|TRAILING)' --color=always"
echo ""
echo "=========================================="

