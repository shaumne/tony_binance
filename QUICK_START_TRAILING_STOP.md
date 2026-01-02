# ⚡ Trailing Stop - Hızlı Başlangıç

## 🎯 3 Adımda Kullanım

### 1️⃣ Webhook Payload Hazırla

**LONG Pozisyon için:**
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

**SHORT Pozisyon için:**
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

### 2️⃣ TradingView Alert Oluştur

```pinescript
//@version=5
strategy("My Trailing Stop", overlay=true)

// Giriş koşulunuzda:
if (longCondition)
    entryPrice = close
    activationPrice = entryPrice * 1.02  // %2 yukarıda aktif ol
    stopLossPrice = entryPrice * 0.97    // %3 aşağıda hard stop
    
    alert_message = '{"symbol": "BTCUSDT", "side": "BUY", "action": "open", "quantity": "50%", "trailType": "TRAILING_STOP_MARKET", "callbackRate": 1.5, "activationPrice": ' + str.tostring(activationPrice) + ', "workingType": "MARK_PRICE", "stopLoss": ' + str.tostring(stopLossPrice) + '}'
    
    alert(alert_message, alert.freq_once_per_bar_close)
```

---

### 3️⃣ Test Et

```bash
# Terminal'den test et
curl -X POST http://localhost:5001/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "BUY",
    "action": "open",
    "quantity": "10%",
    "trailType": "TRAILING_STOP_MARKET",
    "callbackRate": 1.5,
    "activationPrice": 98500,
    "workingType": "MARK_PRICE",
    "stopLoss": 95000
  }'
```

**veya Python script ile:**
```bash
python test_trailing_stop.py
```

---

## 🔑 Önemli Parametreler

| Parametre | LONG için | SHORT için | Açıklama |
|-----------|-----------|------------|----------|
| `side` | **BUY** | **SELL** | Giriş yönü |
| `callbackRate` | 1.5 | 2.0 | Trailing stop % (fiyat ne kadar geri dönerse tetiklenir) |
| `activationPrice` | Entry'nin **üstünde** | Entry'nin **altında** | Trailing stop bu fiyatta aktif olur |
| `stopLoss` | Entry'nin **altında** | Entry'nin **üstünde** | Fallback hard stop |

---

## ⚙️ Parametre Hesaplama

### LONG Pozisyon
```python
entry_price = 97000      # Giriş fiyatı
activation = entry_price * 1.02   # %2 yukarıda = 98940
stop_loss = entry_price * 0.97    # %3 aşağıda = 94090
callback = 1.5                     # %1.5 geri dönüşte tetikle
```

### SHORT Pozisyon
```python
entry_price = 99000      # Giriş fiyatı
activation = entry_price * 0.98   # %2 aşağıda = 97020
stop_loss = entry_price * 1.03    # %3 yukarıda = 101970
callback = 2.0                     # %2.0 geri dönüşte tetikle
```

---

## 🎯 Trailing Stop Nasıl Çalışır?

### LONG Örnek
```
Entry: $97,000
Activation: $98,500 (%1.55 yukarıda)
Callback: 1.5%

Senaryo:
1️⃣ Fiyat $98,500'e çıkıyor → Trailing stop aktif oluyor
2️⃣ Fiyat $100,000'e çıkıyor → Trailing stop takip ediyor
3️⃣ Fiyat $98,500'e düşüyor ($100k - 1.5% = $98,500)
4️⃣ → STOP TETİKLENİYOR ✅
5️⃣ Pozisyon $98,500 civarında kapanıyor
```

### SHORT Örnek
```
Entry: $99,000
Activation: $97,500 (%1.52 aşağıda)
Callback: 2.0%

Senaryo:
1️⃣ Fiyat $97,500'e düşüyor → Trailing stop aktif oluyor
2️⃣ Fiyat $95,000'e düşüyor → Trailing stop takip ediyor
3️⃣ Fiyat $96,900'e çıkıyor ($95k + 2% = $96,900)
4️⃣ → STOP TETİKLENİYOR ✅
5️⃣ Pozisyon $96,900 civarında kapanıyor
```

---

## 🛡️ Fallback (Güvenlik Ağı)

Eğer trailing stop Binance tarafından reddedilirse:

```
❌ TRAILING_STOP_MARKET reddedildi
    ↓
⚠️ FALLBACK aktif oldu
    ↓
✅ Normal STOP_MARKET yerleştirildi (stopLoss fiyatında)
```

**Örnek:**
- `activationPrice: 98500` rejected ❌
- `stopLoss: 95000` kullanılıyor ✅
- Pozisyon $95,000'de korunuyor 🛡️

---

## ⚡ Hızlı Test Senaryoları

### Test 1: Başarılı Trailing Stop
```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "action": "open",
  "quantity": "10%",
  "trailType": "TRAILING_STOP_MARKET",
  "callbackRate": 1.0,
  "activationPrice": 96000,
  "workingType": "MARK_PRICE",
  "stopLoss": 93000
}
```
**Beklenen:** Entry + Trailing stop başarılı ✅

---

### Test 2: Invalid Callback (Fallback Test)
```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "action": "open",
  "quantity": "10%",
  "trailType": "TRAILING_STOP_MARKET",
  "callbackRate": 10.0,
  "activationPrice": 96000,
  "workingType": "MARK_PRICE",
  "stopLoss": 93000
}
```
**Beklenen:** Trailing stop fail → Fallback STOP_MARKET ✅

---

### Test 3: Eksik Parametre
```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "trailType": "TRAILING_STOP_MARKET"
}
```
**Beklenen:** Error: "Missing required fields" ❌

---

## 📊 Log Kontrol

### Başarılı İşlem
```
✅ ENTRY ORDER PLACED SUCCESSFULLY
   Order ID: 12345678
✅✅✅ TRAILING STOP ORDER PLACED SUCCESSFULLY! ✅✅✅
   Order ID: 12345679
```

### Fallback Senaryosu
```
❌❌❌ TRAILING STOP FAILED AFTER 3 ATTEMPTS ❌❌❌
🛡️ FALLBACK ACTIVATED: PLACING STOP_MARKET ORDER
✅ FALLBACK STOP_MARKET ORDER PLACED
   Order ID: 12345680
```

---

## 🔍 Sorun Giderme (1 Dakikada)

| Sorun | Çözüm |
|-------|-------|
| "Missing required fields" | Tüm parametreleri kontrol et |
| "Invalid callback rate" | callbackRate'i düşür (1-2 arası dene) |
| "Trading disabled" | Dashboard'dan trading'i aktif et |
| "No stop protection placed" | Manuel pozisyon kapat, log kontrol et |

---

## 📞 Hızlı Yardım

**Log dosyası:**
```bash
tail -f logs/app.log
```

**Test script:**
```bash
python test_trailing_stop.py
```

**Detaylı guide:**
```bash
# TRAILING_STOP_GUIDE.md dosyasını oku
```

---

## 🎯 Önemli Notlar

1. **callbackRate**: %0.1 - %5 arası önerilir
2. **activationPrice**: Her zaman mantıklı değer gir
3. **stopLoss**: Her zaman geçerli fallback değeri gönder
4. **workingType**: "MARK_PRICE" önerilir (likidasyonları önler)
5. **quantity**: "50%" veya "0.01" formatında gönderilebilir

---

## ✅ Checklist

Trailing stop kullanmadan önce:

- [ ] `trailType: "TRAILING_STOP_MARKET"` ekledim
- [ ] `callbackRate` 0.1-5 arasında
- [ ] `activationPrice` mantıklı (LONG için üstte, SHORT için altta)
- [ ] `stopLoss` mantıklı (LONG için altta, SHORT için üstte)
- [ ] `workingType: "MARK_PRICE"` kullandım
- [ ] Test script ile test ettim
- [ ] Küçük pozisyonla prod test yaptım

**Tamamsa → Fire and Forget!** 🚀🔥


