"""
Binance Bot Quick Webhook Test
Hızlı webhook testi için basitleştirilmiş script
"""

import requests
import json

# Webhook URL
WEBHOOK_URL = "http://127.0.0.1:5001/webhook"  # Local test için
# WEBHOOK_URL = "https://cryptosynapse.net/webhook"  # EC2 test için

def send_test_signal(symbol, direction, action="open"):
    """
    Webhook'a test sinyali gönder
    
    Args:
        symbol: Coin sembolü (örn: "BTCUSDT", "ETHUSDC")
        direction: "long" veya "short"
        action: "open" veya "close" (varsayılan: open)
    """
    # Doğru format: "SYMBOL/DIRECTION/ACTION"
    signal = f"{symbol}/{direction}/{action}"
    
    payload = {
        "signal": signal
    }
    
    print(f"\n{'='*60}")
    print(f"📤 Test Sinyali Gönderiliyor...")
    print(f"{'='*60}")
    print(f"URL:    {WEBHOOK_URL}")
    print(f"Signal: {signal}")
    print(f"{'='*60}\n")
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ BAŞARILI\n")
            try:
                result = response.json()
                print("Cevap:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            except:
                print(response.text)
        else:
            print("❌ HATA\n")
            print(f"Cevap: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ BAĞLANTI HATASI!")
        print("Flask uygulaması çalışıyor mu?")
        print(f"URL: {WEBHOOK_URL}")
    except Exception as e:
        print(f"❌ HATA: {str(e)}")

def main():
    """Ana fonksiyon - önceden tanımlı test sinyalleri"""
    print("""
╔══════════════════════════════════════════════════════════╗
║       BINANCE BOT - QUICK WEBHOOK TEST                   ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Test sinyalleri
    test_signals = [
        ("BTCUSDT", "long", "open"),
        ("ETHUSDT", "short", "open"),
        ("SOLUSDC", "long", "open"),
    ]
    
    print("Test Sinyalleri:")
    for i, (symbol, direction, action) in enumerate(test_signals, 1):
        print(f"  {i}. {symbol}/{direction}/{action}")
    
    print("\n" + "="*60)
    choice = input("\nTüm sinyalleri gönder? (y/n): ").strip().lower()
    
    if choice == 'y':
        for symbol, direction, action in test_signals:
            send_test_signal(symbol, direction, action)
            print()
        print("✅ Tüm test sinyalleri gönderildi!")
    else:
        # Manuel sinyal
        print("\n📌 Manuel Test:")
        symbol = input("Symbol (örn: BTCUSDT): ").strip().upper()
        direction = input("Direction (long/short): ").strip().lower()
        action = input("Action (open/close) [open]: ").strip().lower() or "open"
        
        if direction in ['long', 'short'] and action in ['open', 'close']:
            send_test_signal(symbol, direction, action)
        else:
            print("❌ Geçersiz giriş!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 İptal edildi")
    except Exception as e:
        print(f"\n❌ Hata: {str(e)}")
