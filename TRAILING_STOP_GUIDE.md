# 🔥 Trailing Stop Strategy Guide

## Genel Bakış

Bu yükseltme, Binance Futures trading bot'unuza **"Fire and Forget" Trailing Stop Strategy** özelliği ekler. TradingView'dan önceden hesaplanmış trailing stop parametrelerini alır ve otomatik olarak pozisyon açar + trailing stop order yerleştirir.

---

## 📊 Strateji Türleri

### 1️⃣ Standard Strategy (Eski Mantık)
Webhook payload'ında **`trailType` anahtarı YOKSA**, standart strateji çalışır:

**Örnek Payload:**
```json
{
  "signal": "BTCUSDT/long/open"
}
```

**Davranış:**
- Market order ile pozisyon açar
- ATR bazlı TP/SL order'ları yerleştirir (mevcut sistem)
- Ayrı bir "close" sinyali bekler

---

### 2️⃣ Trailing Stop Strategy (Yeni Mantık) 🔥
Webhook payload'ında **`trailType: "TRAILING_STOP_MARKET"`** varsa, yeni strateji çalışır:

**Örnek Payload (LONG):**
```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "action": "open",
  "quantity": "50%",
  "trailType": "TRAILING_STOP_MARKET",
  "callbackRate": 1.5,
  "activationPrice": 98500,
  "workingType": "MARK_PRICE",
  "stopLoss": 95000
}
```

**Örnek Payload (SHORT):**
```json
{
  "symbol": "ETHUSDT",
  "side": "SELL",
  "action": "open",
  "quantity": "50%",
  "trailType": "TRAILING_STOP_MARKET",
  "callbackRate": 2.0,
  "activationPrice": 3200,
  "workingType": "MARK_PRICE",
  "stopLoss": 3350
}
```

---

## 🔧 Parametre Açıklamaları

| Parametre | Tip | Zorunlu | Açıklama |
|-----------|-----|---------|----------|
| `symbol` | string | ✅ | Trading çifti (örn: "BTCUSDT", "ETHUSDC") |
| `side` | string | ✅ | Giriş yönü: **"BUY"** (LONG) veya **"SELL"** (SHORT) |
| `action` | string | ✅ | Her zaman **"open"** olmalı |
| `quantity` | string/float | ✅ | Pozisyon büyüklüğü (örn: "50%" veya "0.1") |
| `trailType` | string | ✅ | **"TRAILING_STOP_MARKET"** - Tetikleyici anahtar |
| `callbackRate` | float | ✅ | Trailing stop yüzdesi (örn: 1.5 = %1.5) |
| `activationPrice` | float | ✅ | Trailing stop aktivasyon fiyatı |
| `workingType` | string | ✅ | **"MARK_PRICE"** veya **"CONTRACT_PRICE"** |
| `stopLoss` | float | ✅ | Fallback hard stop fiyatı (trailing stop başarısız olursa) |

---

## 🚀 Çalışma Mantığı

### Adım 1: Entry Order Yerleştirme
```
📤 MARKET order ile pozisyon aç
   - LONG için: BUY order
   - SHORT için: SELL order
```

### Adım 2: Trailing Stop Order Yerleştirme
```
🎯 TRAILING_STOP_MARKET order yerleştir
   - Ters yönde (LONG için SELL, SHORT için BUY)
   - reduceOnly: true (yeni pozisyon açmayı engeller)
   - callbackRate ve activationPrice kullan
   - 3 deneme yapar (retry mechanism)
```

### Adım 3: Hata Yönetimi (Fallback)
```
🛡️ Trailing stop reddedilirse:
   ❌ TRAILING_STOP_MARKET başarısız
   ⚠️ FALLBACK aktif et
   ✅ Normal STOP_MARKET order yerleştir (stopLoss fiyatında)
```

---

## ⚙️ Trailing Stop Parametreleri

### callbackRate (Callback Percentage)
- **Tip:** Float (örn: 1.5)
- **Anlamı:** Fiyat ne kadar geri dönerse stop tetiklenir
- **LONG Örnek:** 
  - Pozisyon $100'dan açıldı
  - callbackRate = 1.5%
  - Fiyat $105'e çıktı
  - Fiyat $103.425'e düşerse ($105 - %1.5) stop tetiklenir
- **SHORT Örnek:**
  - Pozisyon $100'dan açıldı
  - callbackRate = 2.0%
  - Fiyat $95'e düştü
  - Fiyat $96.90'a çıkarsa ($95 + %2.0) stop tetiklenir

### activationPrice
- **Tip:** Float (örn: 98500)
- **Anlamı:** Trailing stop bu fiyata ulaşıldığında aktif olur
- **LONG Örnek:**
  - Entry: $97000
  - activationPrice: $98500
  - Trailing stop sadece fiyat $98500'e çıktığında aktif olur
- **SHORT Örnek:**
  - Entry: $99000
  - activationPrice: $97500
  - Trailing stop sadece fiyat $97500'e düştüğünde aktif olur

### workingType
- **MARK_PRICE:** Mark fiyatı kullan (önerilen - likidasyonları önler)
- **CONTRACT_PRICE:** Son işlem fiyatını kullan

### stopLoss (Fallback)
- Trailing stop başarısız olursa kullanılır
- Normal STOP_MARKET order olarak yerleştirilir
- **LONG için:** Entry'nin altında olmalı
- **SHORT için:** Entry'nin üstünde olmalı

---

## 📝 TradingView Pine Script Örneği

```pinescript
//@version=5
strategy("Trailing Stop Strategy", overlay=true)

// Parametreler
callbackPct = input.float(1.5, title="Callback Rate (%)", minval=0.1, maxval=10)
activationPct = input.float(2.0, title="Activation Distance (%)", minval=0.1, maxval=10)
stopLossPct = input.float(3.0, title="Hard Stop Loss (%)", minval=0.5, maxval=10)

// Giriş sinyali (örnek)
longCondition = ta.crossover(ta.sma(close, 20), ta.sma(close, 50))
shortCondition = ta.crossunder(ta.sma(close, 20), ta.sma(close, 50))

// LONG pozisyon
if (longCondition and strategy.position_size == 0)
    entryPrice = close
    activationPrice = entryPrice * (1 + activationPct/100)
    stopLossPrice = entryPrice * (1 - stopLossPct/100)
    
    // Webhook JSON oluştur
    alert_message = '{"symbol": "BTCUSDT", "side": "BUY", "action": "open", "quantity": "50%", "trailType": "TRAILING_STOP_MARKET", "callbackRate": ' + str.tostring(callbackPct) + ', "activationPrice": ' + str.tostring(activationPrice) + ', "workingType": "MARK_PRICE", "stopLoss": ' + str.tostring(stopLossPrice) + '}'
    
    strategy.entry("Long", strategy.long)
    alert(alert_message, alert.freq_once_per_bar_close)

// SHORT pozisyon
if (shortCondition and strategy.position_size == 0)
    entryPrice = close
    activationPrice = entryPrice * (1 - activationPct/100)
    stopLossPrice = entryPrice * (1 + stopLossPct/100)
    
    // Webhook JSON oluştur
    alert_message = '{"symbol": "BTCUSDT", "side": "SELL", "action": "open", "quantity": "50%", "trailType": "TRAILING_STOP_MARKET", "callbackRate": ' + str.tostring(callbackPct) + ', "activationPrice": ' + str.tostring(activationPrice) + ', "workingType": "MARK_PRICE", "stopLoss": ' + str.tostring(stopLossPrice) + '}'
    
    strategy.entry("Short", strategy.short)
    alert(alert_message, alert.freq_once_per_bar_close)
```

---

## 🧪 Test Etme

### Manuel Test (cURL)

**LONG Pozisyon:**
```bash
curl -X POST http://localhost:5001/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "BUY",
    "action": "open",
    "quantity": "50%",
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": 1.5,
    "activationPrice": 98500,
    "workingType": "MARK_PRICE",
    "stopLoss": 95000
  }'
```

**SHORT Pozisyon:**
```bash
curl -X POST http://localhost:5001/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "ETHUSDT",
    "side": "SELL",
    "action": "open",
    "quantity": "50%",
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": 2.0,
    "activationPrice": 3200,
    "workingType": "MARK_PRICE",
    "stopLoss": 3350
  }'
```

### Python Test Script Kullanımı

```bash
python test_trailing_stop.py
```

Test script'i şunları test eder:
- ✅ Standard strategy (eski mantık)
- ✅ Trailing stop LONG pozisyon
- ✅ Trailing stop SHORT pozisyon
- ✅ Geçersiz payload (eksik alanlar)

---

## 🔍 Log Örnekleri

### Başarılı Trailing Stop
```
================================================================================
🔥 TRAILING STOP STRATEGY - FIRE AND FORGET MODE ACTIVATED
================================================================================
📊 STRATEGY PARAMETERS:
   Symbol: BTCUSDT
   Entry Side: BUY
   Callback Rate: 1.5%
   Activation Price: $98500.00
   Working Type: MARK_PRICE
   Fallback Stop Loss: $95000.00
================================================================================
📤 STEP 2: PLACING PRIMARY ENTRY ORDER
================================================================================
✅ ENTRY ORDER PLACED SUCCESSFULLY
   Order ID: 12345678
   Status: FILLED
   Position Size: 0.01
⏳ Waiting 1 second for position to settle...
================================================================================
🎯 STEP 3: PLACING TRAILING STOP MARKET ORDER
================================================================================
🔒 TRAILING STOP PARAMETERS:
   Type: TRAILING_STOP_MARKET
   Side: SELL
   Quantity: 0.01
   Callback Rate: 1.5%
   Activation Price: $98500.00
   Working Type: MARK_PRICE
   Reduce Only: True
   Position Side: LONG
🔄 Trailing Stop Attempt 1/3
✅✅✅ TRAILING STOP ORDER PLACED SUCCESSFULLY! ✅✅✅
   Order ID: 12345679
   Status: NEW
   Type: TRAILING_STOP_MARKET
```

### Fallback Senaryosu
```
🔄 Trailing Stop Attempt 1/3
⚠️ Trailing stop attempt 1 failed: APIError(code=-2010): Invalid callback rate
🔄 Trailing Stop Attempt 2/3
⚠️ Trailing stop attempt 2 failed: APIError(code=-2010): Invalid callback rate
🔄 Trailing Stop Attempt 3/3
⚠️ Trailing stop attempt 3 failed: APIError(code=-2010): Invalid callback rate
❌❌❌ TRAILING STOP FAILED AFTER 3 ATTEMPTS ❌❌❌
   Last Error: APIError(code=-2010): Invalid callback rate
   ACTIVATING FALLBACK: Placing STOP_MARKET order
================================================================================
🛡️ FALLBACK ACTIVATED: PLACING STOP_MARKET ORDER
================================================================================
🔒 FALLBACK STOP PARAMETERS:
   Type: STOP_MARKET
   Side: SELL
   Quantity: 0.01
   Stop Price: $95000.00
   Reduce Only: True
✅ FALLBACK STOP_MARKET ORDER PLACED
   Order ID: 12345680
   Stop Price: $95000.00
```

---

## ⚠️ Önemli Notlar

### 1. Trailing Stop Sınırlamaları
- Binance her coin için **farklı callback rate limitleri** vardır
- Genelde %0.1 - %5 arasında kabul edilir
- Test yaparken önce küçük değerler deneyin

### 2. ActivationPrice Mantığı
- LONG için: activationPrice > entryPrice olmalı
- SHORT için: activationPrice < entryPrice olmalı
- Yanlış değer girerseniz trailing stop hiç aktif olmaz

### 3. Fallback Önemlidir
- Trailing stop %100 garantili değildir
- Her zaman geçerli bir `stopLoss` değeri gönderin
- Bu, pozisyonunuzun korunmasını garanti eder

### 4. Position Mode
- Bot otomatik olarak **Hedge Mode** kullanır
- Aynı anda LONG ve SHORT pozisyon açabilir
- Mevcut pozisyonlar varsa mod değiştirilemez

### 5. ClosePosition
- Trailing stop her zaman `closePosition: 'true'` ile yerleştirilir
- Bu, yanlışlıkla ters pozisyon açılmasını engeller
- Tüm pozisyonu otomatik kapatır (quantity belirtmeye gerek kalmaz)

---

## 🐛 Sorun Giderme

### Hata: "Missing required fields"
**Çözüm:** Tüm zorunlu alanların gönderildiğinden emin olun:
- symbol, side, action, callbackRate, activationPrice, workingType, stopLoss

### Hata: "Invalid callback rate"
**Çözüm:** 
- callbackRate değerini düşürün (örn: 5.0 → 1.5)
- Binance'in o coin için callback rate limitlerini kontrol edin

### Hata: "Trailing stop failed and no fallback"
**Çözüm:** Her zaman geçerli bir `stopLoss` değeri gönderin

### Hata: "Position opened but no stop protection placed"
**Çözüm:** 
- Bu kritik bir durumdur
- Manuel olarak Binance'den pozisyonu kapatın
- Log'larda hata nedenini kontrol edin

---

## 📞 Destek

Sorun yaşarsanız:
1. `logs/app.log` dosyasını kontrol edin
2. Test script'i ile manuel test yapın
3. Binance API dökümantasyonunu kontrol edin: https://binance-docs.github.io/apidocs/futures/en/

---

## 🎯 Özet

✅ **Yeni Özellik:** Trailing Stop Strategy  
✅ **Tetikleyici:** `trailType: "TRAILING_STOP_MARKET"`  
✅ **Fallback:** Otomatik STOP_MARKET order  
✅ **Uyumluluk:** Standart strategy ile birlikte çalışır  
✅ **Test:** `test_trailing_stop.py` ile test edilebilir  

**Fire and Forget!** 🚀

