# Webhook Test Rehberi

## ⚠️ ÖNEMLİ: Doğru Webhook Formatı

Webhook endpoint **zorunlu olarak** şu formatı bekler:

```json
{
  "signal": "SYMBOL/DIRECTION/ACTION"
}
```

**Örnekler:**
- `{"signal": "BTCUSDT/long/open"}` ✅
- `{"signal": "ETHUSDC/short/open"}` ✅
- `{"signal": "SOLUSDT/long/close"}` ✅

**Yanlış formatlar (ÇALIŞMAZ):**
- `{"symbol": "BTC", "action": "long"}` ❌
- `{"ticker": "BTCUSDT", "side": "BUY"}` ❌

---

## 🚀 Hızlı Başlangıç

### 1. Flask Uygulamasını Başlat
```bash
# Local test için
python app.py
```

### 2. Yeni Bir Terminal Aç ve Test Et

---

## 📋 Test Script'leri

### Option 1: Manuel Coin Seçimi (ÖNERİLEN)
Interaktif menü ile coin, pair, direction ve action seçin:

```bash
python test_webhook.py
```

**Menü seçenekleri:**
1. 🎯 **Manuel Coin Seçimi** - Kendi coininizi seçin
   - Pair: USDT veya USDC
   - Coin: BTC, ETH, SOL, vb.
   - Direction: Long veya Short
   - Action: Open veya Close

2. ⚡ **Hızlı Test** - 3 önceden tanımlı sinyal
3. 🔄 **Karşıt Sinyal Testi** - Position switch kontrolü
4. ⚡ **Duplicate Sinyal Testi** - Duplicate önleme kontrolü
5. 🌍 **Ortam Değiştir** - Local/EC2 seçimi

### Option 2: Hızlı Test
En basit test yöntemi:

```bash
python quick_test.py
```

Bu otomatik olarak 3 test sinyali gönderir:
- BTCUSDT/long/open
- ETHUSDT/short/open
- SOLUSDC/long/open

## 📊 Test Senaryoları

### Senaryo 1: Manuel Coin Seçimi
```bash
python test_webhook.py
# Menüden 1'i seçin (Manuel Coin Seçimi)
# Adım adım coininizi, pair'inizi ve yönünüzü seçin
```

### Senaryo 2: Hızlı Test
```bash
python quick_test.py
# Otomatik olarak 3 test sinyali gönderir
```

### Senaryo 3: Duplicate Kontrolü
```bash
python test_webhook.py
# Menüden 4'ü seçin (Duplicate Sinyal Testi)
# Aynı sinyal 3 kez gönderilir, sadece ilki işlenmeli
```

### Senaryo 4: Position Switch
```bash
python test_webhook.py
# Menüden 3'ü seçin (Karşıt Sinyal Testi)
# Önce LONG, sonra SHORT açılır (auto switch kontrolü)
```

### Senaryo 5: EC2 (Production) Test
```bash
python test_webhook.py
# Menüden 5'i seçin (Ortam Değiştir)
# EC2'yi seçin
# Sonra manuel coin seçimi ile test edin
```

## 🔍 Kontrol Edilmesi Gerekenler

### Dashboard'da:
- [ ] Pozisyon açıldı mı?
- [ ] PnL gösteriliyor mu?
- [ ] Doğru sembol ve side görünüyor mu?
- [ ] Leverage doğru mu?

### Terminal Loglarında:
- [ ] "Order placed successfully" mesajı
- [ ] Position validation mesajları
- [ ] TP/SL ayarlandı mı?

### Settings'te:
- [ ] İlgili coin'in `enable_trading` açık mı?
- [ ] Binance API key'leri girilmiş mi?

## ⚠️ Dikkat Edilmesi Gerekenler

### 1. Test Öncesi
```bash
# Settings'ten kontrol et:
- Binance API Key ve Secret doğru mu?
- Test yapacağın coin enable_trading = ON mu?
- Enable Trading genel ayarı açık mı?
```

### 2. Güvenlik
```bash
# ⚠️ TESTNET KULLAN!
Binance API Key'lerini Testnet'ten al:
https://testnet.binancefuture.com/

Asla gerçek API key'leri test için kullanma!
```

### 3. Hata Durumları

**"Connection refused"**
- Flask uygulaması çalışmıyor
- `python app.py` ile başlat

**"Invalid symbol"**
- Coin adı yanlış yazılmış
- Binance'de böyle bir çift yok
- Settings'te enable_trading kapalı

**"Duplicate position"**
- Aynı pozisyon zaten açık
- Cooldown süresi dolmamış (30 saniye)

**"API error"**
- API key hatalı
- Yeterli bakiye yok
- Binance API limitleri

## 📝 Webhook Format

Test script'leri bu formatı kullanır:

```json
{
  "symbol": "BTCUSDT",
  "action": "long"
}
```

**Desteklenen action'lar:**
- `long` - Long pozisyon aç
- `short` - Short pozisyon aç

**Desteklenen symbol formatları:**
- USDT çiftleri: `BTCUSDT`, `ETHUSDT`, `SOLUSDT` vs.
- USDC çiftleri: `BTCUSDC`, `ETHUSDC`, `SOLUSDC` vs.

## 🎯 Başarılı Test Örneği

```bash
$ python quick_test.py BTCUSDT long

==================================================
TEST: BTC Long (USDT)
Payload: {
  "symbol": "BTCUSDT",
  "action": "long"
}
==================================================

Status Code: 200
✅ BAŞARILI!
Sonuç:
{
  "status": "success",
  "message": "Signal processed: BTCUSDT LONG",
  "order_id": "123456789"
}
```

## 📞 Telegram Bildirimleri

Testler sırasında Telegram'a bildirim gitmesini istiyorsan:

1. Settings'te Telegram Bot Token ve Chat ID'yi gir
2. Test sinyali gönder
3. Telegram'dan bildirim geldiğini kontrol et

## 🐛 Sorun Giderme

### Hiçbir pozisyon açılmıyor
```bash
# Kontrol listesi:
1. Flask uygulaması çalışıyor mu? → python app.py
2. API key'ler doğru mu? → Settings sayfasından kontrol et
3. enable_trading açık mı? → Settings > General
4. Coin enable_trading açık mı? → Settings > USDT/USDC Coins
5. Yeterli bakiye var mı? → Dashboard'da balance kontrol et
```

### Test başarılı ama Dashboard'da görünmüyor
```bash
# Dashboard'ı yenile:
- F5 tuşuna bas
- Veya 10 saniye bekle (otomatik yenileme)
```

### API hatası alıyorum
```bash
# Log'ları kontrol et:
Terminal'de app.py çıktılarına bak
Binance API error mesajını oku
```

## 💡 İpuçları

1. **İlk testi küçük miktarla yap**
   - Order size'ı %1-2 gibi düşük tut
   - Test coin'i için leverage'ı 1-2x yap

2. **Testnet kullan**
   - Gerçek para risk etme
   - https://testnet.binancefuture.com/

3. **Log'ları takip et**
   - Terminal'deki app.py çıktılarını oku
   - Hata mesajları önemli ipuçları verir

4. **Adım adım ilerle**
   - İlk önce bir coin test et
   - Çalışıyorsa diğerlerine geç

5. **Dashboard'ı sürekli aç tut**
   - Pozisyonları real-time izle
   - PnL değişimlerini gör

