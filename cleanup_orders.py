#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup duplicate trailing stop orders and orphaned orders
- Removes duplicate trailing stops (keeps only the most recent)
- Removes orphaned TP/SL orders (no matching position)
"""

import sys
import os
import json
from binance.client import Client
from binance.exceptions import BinanceAPIException

# Fix Unicode encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models import Config

def load_config():
    """Load configuration from JSON file"""
    config_file = 'data/config.json'
    backup_file = 'data/config_backup.json'
    
    try:
        if not os.path.exists(config_file):
            if os.path.exists(backup_file):
                config_file = backup_file
            else:
                return None
        
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return Config.from_dict(data)
    except Exception as e:
        print(f"[ERROR] Error loading config: {str(e)}")
        return None

def cleanup_orders():
    """Cleanup duplicate and orphaned orders"""
    
    print("=" * 100)
    print("EMIR TEMIZLIGI - DUPLICATE VE ORPHANED ORDERS")
    print("=" * 100)
    print()
    
    config = load_config()
    if not config or not config.binance_api_key or not config.binance_secret_key:
        print("[ERROR] Binance API keys not found!")
        return
    
    client = Client(config.binance_api_key, config.binance_secret_key)
    
    try:
        # Get positions
        positions = client.futures_position_information()
        active_positions = {}
        for pos in positions:
            pos_amt = abs(float(pos.get('positionAmt', '0')))
            if pos_amt > 0:
                symbol = pos.get('symbol')
                side = pos.get('positionSide', 'BOTH')
                key = f"{symbol}_{side}"
                active_positions[key] = pos
        
        print(f"✅ {len(active_positions)} aktif pozisyon bulundu")
        print()
        
        # Get open orders (regular orders)
        open_orders = client.futures_get_open_orders()
        
        # Get algo orders (trailing stops)
        algo_orders = []
        try:
            if hasattr(client, 'futures_get_open_algo_orders'):
                algo_orders = client.futures_get_open_algo_orders()
            else:
                symbols = set([p.get('symbol') for p in positions if abs(float(p.get('positionAmt', '0'))) > 0])
                for symbol in symbols:
                    try:
                        if hasattr(client, 'futures_get_all_algo_orders'):
                            symbol_algos = client.futures_get_all_algo_orders(symbol=symbol)
                            algo_orders.extend([a for a in symbol_algos if a.get('algoStatus') == 'NEW' and a.get('orderType') == 'TRAILING_STOP_MARKET'])
                    except:
                        continue
        except Exception as e:
            print(f"[WARNING] Algo orders alinamadi: {str(e)}")
        
        print(f"✅ {len(open_orders)} normal emir bulundu")
        print(f"✅ {len(algo_orders)} algo emir (trailing stop) bulundu")
        print()
        
        # ========================================================================
        # 1. FIND DUPLICATE TRAILING STOPS
        # ========================================================================
        print("=" * 100)
        print("1. DUPLICATE TRAILING STOP ANALIZI")
        print("=" * 100)
        print()
        
        trailing_by_position = {}
        for algo in algo_orders:
            symbol = algo.get('symbol')
            side = algo.get('positionSide', 'BOTH')
            key = f"{symbol}_{side}"
            
            if key not in trailing_by_position:
                trailing_by_position[key] = []
            trailing_by_position[key].append(algo)
        
        duplicate_trailing = []
        to_keep_trailing = []
        
        for key, algos in trailing_by_position.items():
            if len(algos) > 1:
                # Sort by createTime (newest first)
                algos.sort(key=lambda x: x.get('createTime', 0), reverse=True)
                
                # Keep the most recent one
                to_keep_trailing.append(algos[0])
                
                # Cancel the rest
                for algo in algos[1:]:
                    duplicate_trailing.append(algo)
                
                print(f"🔍 {key}: {len(algos)} trailing stop bulundu")
                print(f"   ✅ Tutulacak: Algo ID {algos[0].get('algoId')} (Time: {algos[0].get('createTime')})")
                print(f"   ❌ Iptal edilecek: {len(algos) - 1} adet")
                for algo in algos[1:]:
                    print(f"      - Algo ID {algo.get('algoId')} (Time: {algo.get('createTime')})")
                print()
        
        if not duplicate_trailing:
            print("✅ Duplicate trailing stop bulunamadi!")
        else:
            print(f"⚠️  Toplam {len(duplicate_trailing)} duplicate trailing stop bulundu")
        print()
        
        # ========================================================================
        # 2. FIND ORPHANED ORDERS (TP/SL without matching position)
        # ========================================================================
        print("=" * 100)
        print("2. ORPHANED ORDERS ANALIZI (Pozisyon Olmayan Emirler)")
        print("=" * 100)
        print()
        
        orphaned_orders = []
        
        for order in open_orders:
            symbol = order.get('symbol')
            order_type = order.get('type', '')
            position_side = order.get('positionSide', 'BOTH')
            
            # Check if this order has a matching position
            key = f"{symbol}_{position_side}"
            if key not in active_positions:
                # Check if it's a TP or SL order
                if order_type in ['TAKE_PROFIT_MARKET', 'TAKE_PROFIT', 'STOP_MARKET', 'STOP']:
                    orphaned_orders.append(order)
                    print(f"🔍 Orphaned {order_type}: {symbol} {position_side}")
                    print(f"   Order ID: {order.get('orderId')}")
                    print(f"   Price: {order.get('stopPrice', 'N/A')}")
                    print()
        
        if not orphaned_orders:
            print("✅ Orphaned order bulunamadi!")
        else:
            print(f"⚠️  Toplam {len(orphaned_orders)} orphaned order bulundu")
        print()
        
        # ========================================================================
        # 3. SUMMARY AND CONFIRMATION
        # ========================================================================
        print("=" * 100)
        print("3. OZET")
        print("=" * 100)
        print()
        print(f"📊 Duplicate Trailing Stop: {len(duplicate_trailing)}")
        print(f"📊 Orphaned Orders: {len(orphaned_orders)}")
        print(f"📊 Toplam Iptal Edilecek: {len(duplicate_trailing) + len(orphaned_orders)}")
        print()
        
        if len(duplicate_trailing) == 0 and len(orphaned_orders) == 0:
            print("✅ Temizlenecek emir yok!")
            return
        
        # Ask for confirmation (skip if non-interactive)
        print("=" * 100)
        try:
            response = input("Devam etmek istiyor musunuz? (evet/hayir): ").strip().lower()
            if response not in ['evet', 'yes', 'y', 'e']:
                print("❌ Iptal edildi.")
                return
        except (EOFError, KeyboardInterrupt):
            print("❌ Interaktif mod desteklenmiyor. Script'i --auto flag ile çalıştırın.")
            print("   Örnek: python cleanup_orders.py --auto")
            return
        
        # ========================================================================
        # 4. CANCEL ORDERS
        # ========================================================================
        print()
        print("=" * 100)
        print("4. EMIRLER IPTAL EDILIYOR")
        print("=" * 100)
        print()
        
        cancelled_trailing = 0
        failed_trailing = 0
        cancelled_orphaned = 0
        failed_orphaned = 0
        
        # Cancel duplicate trailing stops
        for algo in duplicate_trailing:
            try:
                symbol = algo.get('symbol')
                algo_id = algo.get('algoId')
                
                if hasattr(client, 'futures_cancel_algo_order'):
                    result = client.futures_cancel_algo_order(symbol=symbol, algoId=algo_id)
                    print(f"✅ Trailing Stop iptal edildi: {symbol} (Algo ID: {algo_id})")
                    cancelled_trailing += 1
                else:
                    print(f"❌ futures_cancel_algo_order method bulunamadi!")
                    break
            except BinanceAPIException as e:
                print(f"❌ Trailing Stop iptal edilemedi: {symbol} (Algo ID: {algo_id}) - {e.message} (Code: {e.code})")
                failed_trailing += 1
            except Exception as e:
                print(f"❌ Trailing Stop iptal edilemedi: {symbol} (Algo ID: {algo_id}) - {str(e)}")
                failed_trailing += 1
        
        # Cancel orphaned orders
        for order in orphaned_orders:
            try:
                symbol = order.get('symbol')
                order_id = order.get('orderId')
                
                result = client.futures_cancel_order(symbol=symbol, orderId=order_id)
                print(f"✅ Orphaned order iptal edildi: {symbol} (Order ID: {order_id})")
                cancelled_orphaned += 1
            except BinanceAPIException as e:
                print(f"❌ Orphaned order iptal edilemedi: {symbol} (Order ID: {order_id}) - {e.message} (Code: {e.code})")
                failed_orphaned += 1
            except Exception as e:
                print(f"❌ Orphaned order iptal edilemedi: {symbol} (Order ID: {order_id}) - {str(e)}")
                failed_orphaned += 1
        
        # ========================================================================
        # 5. FINAL SUMMARY
        # ========================================================================
        print()
        print("=" * 100)
        print("5. FINAL OZET")
        print("=" * 100)
        print()
        print(f"✅ Iptal edilen Trailing Stop: {cancelled_trailing}")
        print(f"❌ Basarisiz Trailing Stop: {failed_trailing}")
        print(f"✅ Iptal edilen Orphaned Order: {cancelled_orphaned}")
        print(f"❌ Basarisiz Orphaned Order: {failed_orphaned}")
        print()
        print(f"📊 Toplam Basarili: {cancelled_trailing + cancelled_orphaned}")
        print(f"📊 Toplam Basarisiz: {failed_trailing + failed_orphaned}")
        print()
        print("=" * 100)
        print("✅ Temizlik tamamlandi!")
        print("=" * 100)
        
    except BinanceAPIException as e:
        print(f"[ERROR] Binance API Error: {e.message} (Code: {e.code})")
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    auto_mode = '--auto' in sys.argv or '-y' in sys.argv
    
    if auto_mode:
        # Non-interactive mode - auto confirm
        import builtins
        original_input = builtins.input
        def mock_input(prompt):
            print(f"{prompt} evet (auto mode)")
            return "evet"
        builtins.input = mock_input
    
    cleanup_orders()

