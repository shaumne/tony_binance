"""
Quick Webhook Test - Hızlı Sinyal Testi
Kullanım: python quick_test.py
"""

import requests
import json
import sys

WEBHOOK_URL = "http://127.0.0.1:5000/webhook"

# Hızlı test sinyalleri
test_signals = [
    {"symbol": "BTCUSDT", "action": "long", "desc": "BTC Long (USDT)"},
    {"symbol": "ETHUSDT", "action": "short", "desc": "ETH Short (USDT)"},
    {"symbol": "SOLUSDC", "action": "long", "desc": "SOL Long (USDC)"},
]

def send_test_signal(symbol, action, description):
    """Test sinyali gönder"""
    payload = {"symbol": symbol, "action": action}
    
    print(f"\n{'='*50}")
    print(f"TEST: {description}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'='*50}")
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ BAŞARILI!")
            try:
                result = response.json()
                print(f"Sonuç:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
            except:
                print(f"Sonuç: {response.text}")
        else:
            print(f"❌ HATA!")
            print(f"Cevap: {response.text}")
            
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print("❌ BAĞLANTI HATASI - Flask uygulaması çalışmıyor!")
        print("Önce 'python app.py' ile uygulamayı başlatın.")
        return False
    except Exception as e:
        print(f"❌ HATA: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "="*50)
    print(" QUICK WEBHOOK TEST ".center(50))
    print("="*50)
    
    # Komut satırından argüman varsa özel test
    if len(sys.argv) == 3:
        symbol = sys.argv[1].upper()
        action = sys.argv[2].lower()
        
        if action not in ['long', 'short']:
            print(f"❌ Geçersiz action: {action}")
            print("Kullanım: python quick_test.py BTCUSDT long")
            sys.exit(1)
            
        send_test_signal(symbol, action, f"{symbol} {action.upper()}")
    else:
        # Varsayılan testler
        print("\n🚀 3 Test Sinyali Gönderiliyor...\n")
        
        success_count = 0
        for test in test_signals:
            if send_test_signal(test["symbol"], test["action"], test["desc"]):
                success_count += 1
            
            if test != test_signals[-1]:  # Son sinyal değilse bekle
                print("\n⏳ 2 saniye bekleniyor...")
                import time
                time.sleep(2)
        
        print(f"\n{'='*50}")
        print(f"SONUÇ: {success_count}/{len(test_signals)} test başarılı")
        print(f"{'='*50}\n")
        
        if success_count == 0:
            print("💡 İPUCU: Flask uygulamanızın çalıştığından emin olun:")
            print("   python app.py")

