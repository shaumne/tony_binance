"""
Binance Bot Webhook Test Script
Bu script webhook'a test sinyalleri gönderir
"""

import requests
import json
import time

# Webhook URL
WEBHOOK_URL = "http://127.0.0.1:5000/webhook"

def send_signal(symbol, action):
    """
    Webhook'a sinyal gönder
    
    Args:
        symbol: Coin sembolü (örn: "BTCUSDT", "ETHUSDC")
        action: İşlem türü ("long" veya "short")
    """
    payload = {
        "symbol": symbol,
        "action": action
    }
    
    try:
        print(f"\n{'='*60}")
        print(f"📤 Sinyal Gönderiliyor...")
        print(f"   Symbol: {symbol}")
        print(f"   Action: {action.upper()}")
        print(f"{'='*60}")
        
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ BAŞARILI - {response.status_code}")
            try:
                result = response.json()
                print(f"📊 Sonuç: {json.dumps(result, indent=2, ensure_ascii=False)}")
            except:
                print(f"📊 Sonuç: {response.text}")
        else:
            print(f"❌ HATA - Status: {response.status_code}")
            print(f"📊 Cevap: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ BAĞLANTI HATASI - Flask uygulaması çalışıyor mu?")
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT - İstek zaman aşımına uğradı")
    except Exception as e:
        print(f"❌ HATA - {str(e)}")

def test_usdt_coins():
    """USDT coin'lerini test et"""
    print("\n" + "🟢 USDT-M COINS TEST ".center(60, "="))
    
    usdt_coins = [
        ("BTCUSDT", "long"),
        ("ETHUSDT", "short"),
        ("SOLUSDT", "long"),
        ("BNBUSDT", "short"),
    ]
    
    for symbol, action in usdt_coins:
        send_signal(symbol, action)
        time.sleep(2)  # Her sinyal arasında 2 saniye bekle

def test_usdc_coins():
    """USDC coin'lerini test et"""
    print("\n" + "🔵 USDC-M COINS TEST ".center(60, "="))
    
    usdc_coins = [
        ("BTCUSDC", "long"),
        ("ETHUSDC", "short"),
        ("SOLUSDC", "long"),
    ]
    
    for symbol, action in usdc_coins:
        send_signal(symbol, action)
        time.sleep(2)

def test_invalid_signals():
    """Geçersiz sinyalleri test et"""
    print("\n" + "⚠️ INVALID SIGNALS TEST ".center(60, "="))
    
    # Geçersiz sembol
    send_signal("INVALID", "long")
    time.sleep(2)
    
    # Geçersiz action
    send_signal("BTCUSDT", "invalid_action")
    time.sleep(2)

def test_quick_signals():
    """Hızlı ardışık sinyaller (duplicate kontrolü için)"""
    print("\n" + "⚡ QUICK DUPLICATE SIGNALS TEST ".center(60, "="))
    
    print("\n📌 Aynı sinyali 3 kez hızlıca gönder (duplicate kontrolü)")
    for i in range(3):
        print(f"\n--- Sinyal {i+1}/3 ---")
        send_signal("BTCUSDT", "long")
        time.sleep(0.5)  # 0.5 saniye

def test_opposite_signals():
    """Karşıt sinyaller (position switch kontrolü için)"""
    print("\n" + "🔄 OPPOSITE SIGNALS TEST ".center(60, "="))
    
    print("\n📌 LONG sinyali gönder")
    send_signal("ETHUSDT", "long")
    
    time.sleep(3)
    
    print("\n📌 Aynı coin için SHORT sinyali gönder (auto switch kontrolü)")
    send_signal("ETHUSDT", "short")

def interactive_test():
    """İnteraktif test modu"""
    print("\n" + "🎮 INTERACTIVE TEST MODE ".center(60, "="))
    print("\nManuel olarak sinyal gönderin (çıkmak için 'q')")
    
    while True:
        print("\n" + "-"*60)
        symbol = input("Symbol (örn: BTCUSDT, ETHUSDC): ").strip().upper()
        
        if symbol.lower() == 'q':
            break
            
        action = input("Action (long/short): ").strip().lower()
        
        if action not in ['long', 'short']:
            print("❌ Geçersiz action! Sadece 'long' veya 'short'")
            continue
            
        send_signal(symbol, action)

def main():
    """Ana test menüsü"""
    print("\n" + "="*60)
    print(" BINANCE BOT WEBHOOK TEST ".center(60))
    print("="*60)
    
    while True:
        print("\n📋 TEST MENÜSÜ:")
        print("  1. USDT Coins Test")
        print("  2. USDC Coins Test")
        print("  3. Geçersiz Sinyal Test")
        print("  4. Hızlı Duplicate Sinyal Test")
        print("  5. Karşıt Sinyal Test (Position Switch)")
        print("  6. İnteraktif Test (Manuel)")
        print("  7. TÜM TESTLER")
        print("  0. Çıkış")
        
        choice = input("\n➡️  Seçim: ").strip()
        
        if choice == "1":
            test_usdt_coins()
        elif choice == "2":
            test_usdc_coins()
        elif choice == "3":
            test_invalid_signals()
        elif choice == "4":
            test_quick_signals()
        elif choice == "5":
            test_opposite_signals()
        elif choice == "6":
            interactive_test()
        elif choice == "7":
            print("\n🚀 TÜM TESTLER BAŞLATILIYOR...")
            test_usdt_coins()
            time.sleep(3)
            test_usdc_coins()
            time.sleep(3)
            test_invalid_signals()
            time.sleep(3)
            test_quick_signals()
            time.sleep(3)
            test_opposite_signals()
            print("\n✅ TÜM TESTLER TAMAMLANDI!")
        elif choice == "0":
            print("\n👋 Çıkılıyor...")
            break
        else:
            print("\n❌ Geçersiz seçim!")

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║        BINANCE BOT WEBHOOK TEST SCRIPTI                  ║
    ║                                                           ║
    ║  Bu script webhook'unuza test sinyalleri gönderir       ║
    ║  Flask uygulamanızın çalıştığından emin olun!          ║
    ║                                                           ║
    ║  URL: http://127.0.0.1:5000/webhook                      ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test scripti sonlandırıldı (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {str(e)}")

