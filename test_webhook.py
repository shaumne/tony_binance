"""
Binance Bot Webhook Test Script
Bu script webhook'a test sinyalleri gönderir
"""

import requests
import json
import time

# Webhook URL seçenekleri
WEBHOOK_URL_LOCAL = "http://127.0.0.1:5001/webhook"
WEBHOOK_URL_EC2 = "https://cryptosynapse.net/webhook"

# Aktif URL (varsayılan: local)
ACTIVE_URL = WEBHOOK_URL_LOCAL

# Desteklenen coinler
USDT_COINS = ["BTC", "ETH", "XRP", "ADA", "DOT", "XLM", "IMX", "DOGE", "INJ", "LDO", "ARB", "UNI", "SOL", "BNB", "FET"]
USDC_COINS = ["BTC", "ETH", "SOL", "AAVE", "BCH", "XRP", "ADA", "AVAX", "LINK", "ARB", "UNI", "CRV", "TIA", "BNB", "FIL"]

def send_signal(symbol, direction, action="open"):
    """
    Webhook'a sinyal gönder
    
    Args:
        symbol: Coin sembolü (örn: "BTCUSDT", "ETHUSDC")
        direction: İşlem yönü ("long" veya "short")
        action: İşlem türü ("open" veya "close")
    """
    # Doğru webhook formatı: "SYMBOL/DIRECTION/ACTION"
    signal = f"{symbol}/{direction}/{action}"
    
    payload = {
        "signal": signal
    }
    
    try:
        print(f"\n{'='*70}")
        print(f"📤 SİNYAL GÖNDERİLİYOR...")
        print(f"{'='*70}")
        print(f"   URL:       {ACTIVE_URL}")
        print(f"   Symbol:    {symbol}")
        print(f"   Direction: {direction.upper()}")
        print(f"   Action:    {action.upper()}")
        print(f"   Signal:    {signal}")
        print(f"{'='*70}")
        
        response = requests.post(ACTIVE_URL, json=payload, timeout=10)
        
        print(f"\n📊 SONUÇ:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   Durum: ✅ BAŞARILI")
            try:
                result = response.json()
                print(f"\n   Cevap:")
                print(f"   {json.dumps(result, indent=6, ensure_ascii=False)}")
            except:
                print(f"   {response.text}")
        else:
            print(f"   Durum: ❌ HATA")
            print(f"   Cevap: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ BAĞLANTI HATASI!")
        print(f"   Flask uygulaması çalışıyor mu?")
        print(f"   URL: {ACTIVE_URL}")
    except requests.exceptions.Timeout:
        print(f"\n❌ TIMEOUT!")
        print(f"   İstek zaman aşımına uğradı")
    except Exception as e:
        print(f"\n❌ HATA: {str(e)}")

def manual_coin_selection():
    """Manuel coin seçimi"""
    print("\n" + "🎯 MANUEL COİN SEÇİMİ ".center(70, "="))
    
    # Pair seçimi
    print("\n📌 1. PAIR SEÇİMİ:")
    print("   1. USDT-M")
    print("   2. USDC-M")
    
    pair_choice = input("\n➡️  Seçim (1-2): ").strip()
    
    if pair_choice == "1":
        pair = "USDT"
        available_coins = USDT_COINS
    elif pair_choice == "2":
        pair = "USDC"
        available_coins = USDC_COINS
    else:
        print("❌ Geçersiz seçim!")
        return
    
    # Coin listesini göster
    print(f"\n📌 2. COİN SEÇİMİ ({pair}):")
    for i, coin in enumerate(available_coins, 1):
        print(f"   {i:2d}. {coin}")
    
    coin_choice = input(f"\n➡️  Seçim (1-{len(available_coins)}): ").strip()
    
    try:
        coin_index = int(coin_choice) - 1
        if 0 <= coin_index < len(available_coins):
            coin = available_coins[coin_index]
        else:
            print("❌ Geçersiz seçim!")
            return
    except ValueError:
        print("❌ Geçersiz seçim!")
        return
    
    # Symbol oluştur
    if pair == "USDT":
        symbol = f"{coin}USDT"
    else:
        symbol = f"{coin}USDC"
    
    # Direction seçimi
    print("\n📌 3. YÖN SEÇİMİ:")
    print("   1. LONG")
    print("   2. SHORT")
    
    direction_choice = input("\n➡️  Seçim (1-2): ").strip()
    
    if direction_choice == "1":
        direction = "long"
    elif direction_choice == "2":
        direction = "short"
    else:
        print("❌ Geçersiz seçim!")
        return
    
    # Action seçimi
    print("\n📌 4. İŞLEM SEÇİMİ:")
    print("   1. OPEN  (Pozisyon Aç)")
    print("   2. CLOSE (Pozisyon Kapat)")
    
    action_choice = input("\n➡️  Seçim (1-2): ").strip()
    
    if action_choice == "1":
        action = "open"
    elif action_choice == "2":
        action = "close"
    else:
        print("❌ Geçersiz seçim!")
        return
    
    # Özet göster ve onay al
    print("\n" + "📋 SİNYAL ÖZETİ ".center(70, "="))
    print(f"   Symbol:    {symbol}")
    print(f"   Direction: {direction.upper()}")
    print(f"   Action:    {action.upper()}")
    print(f"   Signal:    {symbol}/{direction}/{action}")
    print("="*70)
    
    confirm = input("\n✅ Gönderilsin mi? (y/n): ").strip().lower()
    
    if confirm == 'y':
        send_signal(symbol, direction, action)
    else:
        print("❌ İptal edildi")

def quick_test():
    """Hızlı test - önceden tanımlı sinyaller"""
    print("\n" + "⚡ HIZLI TEST ".center(70, "="))
    
    test_signals = [
        ("BTCUSDT", "long", "open"),
        ("ETHUSDT", "short", "open"),
        ("SOLUSDC", "long", "open"),
    ]
    
    print(f"\n📌 {len(test_signals)} test sinyali gönderilecek:\n")
    for i, (symbol, direction, action) in enumerate(test_signals, 1):
        print(f"   {i}. {symbol}/{direction}/{action}")
    
    confirm = input(f"\n✅ Devam? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("❌ İptal edildi")
        return
    
    for symbol, direction, action in test_signals:
        send_signal(symbol, direction, action)
        time.sleep(2)
    
    print("\n✅ Tüm test sinyalleri gönderildi!")

def opposite_signal_test():
    """Karşıt sinyal testi (position switch)"""
    print("\n" + "🔄 KARŞIT SİNYAL TESTİ ".center(70, "="))
    print("\nBu test auto position switch özelliğini kontrol eder.")
    print("Önce LONG, sonra SHORT sinyali gönderilir.\n")
    
    symbol = "ETHUSDT"
    
    print(f"1️⃣  {symbol}/long/open sinyali gönderiliyor...")
    send_signal(symbol, "long", "open")
    
    print("\n⏳ 5 saniye bekleniyor...")
    time.sleep(5)
    
    print(f"\n2️⃣  {symbol}/short/open sinyali gönderiliyor...")
    send_signal(symbol, "short", "open")
    
    print("\n✅ Karşıt sinyal testi tamamlandı!")
    print("💡 Logları kontrol edin: LONG pozisyonu kapatılıp SHORT açılmalı")

def duplicate_test():
    """Duplicate sinyal testi"""
    print("\n" + "⚡ DUPLICATE SİNYAL TESTİ ".center(70, "="))
    print("\nAynı sinyal 3 kez hızlıca gönderilir.")
    print("Sadece ilki işlenmeli, diğerleri duplicate olarak reddedilmeli.\n")
    
    symbol = "BTCUSDT"
    direction = "long"
    action = "open"
    
    for i in range(3):
        print(f"\n{'='*70}")
        print(f"SİNYAL {i+1}/3")
        print(f"{'='*70}")
        send_signal(symbol, direction, action)
        time.sleep(1)
    
    print("\n✅ Duplicate test tamamlandı!")
    print("💡 İlk sinyal işlenmeli, diğer 2 sinyal duplicate olarak reddedilmeli")

def switch_environment():
    """Ortam değiştir (Local/EC2)"""
    global ACTIVE_URL
    
    print("\n" + "🌍 ORTAM SEÇİMİ ".center(70, "="))
    print(f"\n📍 Aktif Ortam: {'LOCAL' if ACTIVE_URL == WEBHOOK_URL_LOCAL else 'EC2 (Production)'}")
    print(f"   URL: {ACTIVE_URL}")
    
    print("\n📌 Ortam Seçenekleri:")
    print("   1. LOCAL  (http://127.0.0.1:5001/webhook)")
    print("   2. EC2    (https://cryptosynapse.net/webhook)")
    
    choice = input("\n➡️  Seçim (1-2): ").strip()
    
    if choice == "1":
        ACTIVE_URL = WEBHOOK_URL_LOCAL
        print("✅ LOCAL ortamı seçildi")
    elif choice == "2":
        ACTIVE_URL = WEBHOOK_URL_EC2
        print("✅ EC2 ortamı seçildi")
    else:
        print("❌ Geçersiz seçim!")

def main():
    """Ana test menüsü"""
    print("\n" + "="*70)
    print(" BINANCE BOT WEBHOOK TEST ".center(70))
    print("="*70)
    
    while True:
        print(f"\n📍 Aktif Ortam: {'LOCAL' if ACTIVE_URL == WEBHOOK_URL_LOCAL else 'EC2'}")
        print(f"   URL: {ACTIVE_URL}")
        
        print("\n📋 TEST MENÜSÜ:")
        print("  1. 🎯 Manuel Coin Seçimi")
        print("  2. ⚡ Hızlı Test (3 sinyal)")
        print("  3. 🔄 Karşıt Sinyal Testi")
        print("  4. ⚡ Duplicate Sinyal Testi")
        print("  5. 🌍 Ortam Değiştir (Local/EC2)")
        print("  0. ❌ Çıkış")
        
        choice = input("\n➡️  Seçim: ").strip()
        
        if choice == "1":
            manual_coin_selection()
        elif choice == "2":
            quick_test()
        elif choice == "3":
            opposite_signal_test()
        elif choice == "4":
            duplicate_test()
        elif choice == "5":
            switch_environment()
        elif choice == "0":
            print("\n👋 Çıkılıyor...")
            break
        else:
            print("\n❌ Geçersiz seçim!")
        
        input("\n⏸️  Devam etmek için Enter'a basın...")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║          BINANCE BOT WEBHOOK TEST SCRIPTI                        ║
║                                                                  ║
║  Bu script webhook'unuza test sinyalleri gönderir               ║
║  Flask uygulamanızın çalıştığından emin olun!                  ║
║                                                                  ║
║  🔹 LOCAL:  http://127.0.0.1:5001/webhook                       ║
║  🔹 EC2:    https://cryptosynapse.net/webhook                   ║
║                                                                  ║
║  ⚠️  DOĞRU FORMAT: {"signal": "BTCUSDT/long/open"}              ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test scripti sonlandırıldı (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {str(e)}")
