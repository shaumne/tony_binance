# Webhook Test Rehberi

## 🚀 Hızlı Başlangıç

### 1. Flask Uygulamasını Başlat
```bash
python app.py
```

### 2. Yeni Bir Terminal Aç ve Test Et

## 📋 Test Script'leri

### Option 1: Hızlı Test (Önerilen)
En basit ve hızlı test yöntemi:

```bash
python quick_test.py
```

Bu otomatik olarak 3 test sinyali gönderir:
- BTC Long (USDT)
- ETH Short (USDT)  
- SOL Long (USDC)

**Özel sinyal göndermek için:**
```bash
python quick_test.py BTCUSDT long
python quick_test.py ETHUSDC short
```

### Option 2: Detaylı Test Menüsü
Kapsamlı test menüsü ile:

```bash
python test_webhook.py
```

**Menü seçenekleri:**
1. USDT Coins Test - USDT çiftlerini test et
2. USDC Coins Test - USDC çiftlerini test et
3. Geçersiz Sinyal Test - Hata kontrolü
4. Hızlı Duplicate Sinyal Test - Duplicate önleme kontrolü
5. Karşıt Sinyal Test - Auto position switch kontrolü
6. İnteraktif Test - Manuel sinyal gönder
7. TÜM TESTLER - Her şeyi test et

## 📊 Test Senaryoları

### Senaryo 1: Basit Long/Short Test
```bash
python quick_test.py BTCUSDT long
# Dashboard'da pozisyon açıldığını kontrol et

python quick_test.py BTCUSDT short
# Auto switch özelliği çalışıyorsa pozisyon kapanıp SHORT açılmalı
```

### Senaryo 2: Farklı Coinler
```bash
python quick_test.py ETHUSDT long
python quick_test.py SOLUSDC short
python quick_test.py BNBUSDT long
```

### Senaryo 3: Duplicate Kontrolü
```bash
# Aynı sinyali 3 kez hızlıca gönder
python quick_test.py BTCUSDT long
python quick_test.py BTCUSDT long
python quick_test.py BTCUSDT long
# Sadece ilki işlenmeli (cooldown sistemi)
```

### Senaryo 4: Position Switch
```bash
# İlk pozisyonu aç
python quick_test.py ETHUSDT long

# Bekle ve karşıt sinyal gönder
python quick_test.py ETHUSDT short
# Auto position switch ON ise LONG kapanıp SHORT açılmalı
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

