#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleanup orphaned trailing stop orders (no matching position)
Pozisyon olmayan trailing stop order'ları otomatik iptal eder
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

def cleanup_orphaned_trailing_stops():
    """Cleanup trailing stop orders that have no matching position"""
    
    print("=" * 100)
    print("ORPHANED TRAILING STOP TEMIZLIGI")
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
                pos_side = pos.get('positionSide', 'BOTH')
                # Handle both One-way (BOTH) and Hedge mode
                key = f"{symbol}_{pos_side}"
                active_positions[key] = pos
                
                # Also add BOTH key for One-way mode compatibility
                if pos_side == 'BOTH':
                    actual_amt = float(pos.get('positionAmt', '0'))
                    if actual_amt > 0:
                        active_positions[f"{symbol}_LONG"] = pos
                    elif actual_amt < 0:
                        active_positions[f"{symbol}_SHORT"] = pos
        
        print(f"✅ {len(active_positions)} aktif pozisyon bulundu")
        print()
        
        # Get algo orders (trailing stops)
        algo_orders = []
        try:
            if hasattr(client, 'futures_get_open_algo_orders'):
                algo_orders = client.futures_get_open_algo_orders()
            else:
                # Fallback: Get algo orders per symbol
                symbols = set()
                for pos in positions:
                    if abs(float(pos.get('positionAmt', '0'))) > 0:
                        symbols.add(pos.get('symbol'))
                
                # Also check common symbols
                common_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'LDOUSDT', 'XLMUSDT', 'ADAUSDT', 
                                 'DOTUSDT', 'UNIUSDT', 'DOGEUSDT', 'FETUSDT', 'INJUSDT', 'IMXUSDT', 'ARBUSDT']
                symbols.update(common_symbols)
                
                for symbol in symbols:
                    try:
                        if hasattr(client, 'futures_get_all_algo_orders'):
                            symbol_algos = client.futures_get_all_algo_orders(symbol=symbol)
                            algo_orders.extend([a for a in symbol_algos if a.get('algoStatus') == 'NEW' and a.get('orderType') == 'TRAILING_STOP_MARKET'])
                    except:
                        continue
        except Exception as e:
            print(f"[WARNING] Algo orders alinamadi: {str(e)}")
            return
        
        print(f"✅ {len(algo_orders)} algo emir (trailing stop) bulundu")
        print()
        
        # Find orphaned trailing stops
        orphaned_trailing = []
        
        for algo in algo_orders:
            symbol = algo.get('symbol')
            algo_pos_side = algo.get('positionSide', 'BOTH')
            key = f"{symbol}_{algo_pos_side}"
            
            # Check if position exists
            position_exists = False
            
            # Check exact match
            if key in active_positions:
                position_exists = True
            else:
                # Check for BOTH (One-way mode)
                if algo_pos_side == 'BOTH':
                    # Check both LONG and SHORT
                    if f"{symbol}_LONG" in active_positions or f"{symbol}_SHORT" in active_positions:
                        position_exists = True
                else:
                    # Check BOTH position
                    if f"{symbol}_BOTH" in active_positions:
                        both_pos = active_positions[f"{symbol}_BOTH"]
                        actual_amt = float(both_pos.get('positionAmt', '0'))
                        if (algo_pos_side == 'LONG' and actual_amt > 0) or (algo_pos_side == 'SHORT' and actual_amt < 0):
                            position_exists = True
            
            if not position_exists:
                orphaned_trailing.append(algo)
                print(f"🔍 Orphaned Trailing Stop: {symbol} {algo_pos_side}")
                print(f"   Algo ID: {algo.get('algoId')}")
                print(f"   Activation Price: {algo.get('activatePrice')}")
                print(f"   Create Time: {algo.get('createTime')}")
                print()
        
        if not orphaned_trailing:
            print("✅ Orphaned trailing stop bulunamadi!")
            return
        
        print("=" * 100)
        print(f"TOPLAM {len(orphaned_trailing)} ORPHANED TRAILING STOP BULUNDU")
        print("=" * 100)
        print()
        
        # Ask for confirmation
        import sys
        auto_mode = '--auto' in sys.argv or '-y' in sys.argv
        
        if not auto_mode:
            try:
                response = input("Iptal etmek istiyor musunuz? (evet/hayir): ").strip().lower()
                if response not in ['evet', 'yes', 'y', 'e']:
                    print("❌ Iptal edildi.")
                    return
            except (EOFError, KeyboardInterrupt):
                print("❌ Interaktif mod desteklenmiyor. Script'i --auto flag ile çalıştırın.")
                return
        else:
            print("Auto mode: Orphaned trailing stop'lar iptal edilecek...")
        
        # Cancel orphaned trailing stops
        cancelled = 0
        failed = 0
        
        for algo in orphaned_trailing:
            try:
                symbol = algo.get('symbol')
                algo_id = algo.get('algoId')
                
                if hasattr(client, 'futures_cancel_algo_order'):
                    result = client.futures_cancel_algo_order(symbol=symbol, algoId=algo_id)
                    print(f"✅ Orphaned trailing stop iptal edildi: {symbol} (Algo ID: {algo_id})")
                    cancelled += 1
                else:
                    print(f"❌ futures_cancel_algo_order method bulunamadi!")
                    break
            except BinanceAPIException as e:
                print(f"❌ Orphaned trailing stop iptal edilemedi: {symbol} (Algo ID: {algo_id}) - {e.message} (Code: {e.code})")
                failed += 1
            except Exception as e:
                print(f"❌ Orphaned trailing stop iptal edilemedi: {symbol} (Algo ID: {algo_id}) - {str(e)}")
                failed += 1
        
        print()
        print("=" * 100)
        print("OZET")
        print("=" * 100)
        print(f"✅ Iptal edilen: {cancelled}")
        print(f"❌ Basarisiz: {failed}")
        print(f"📊 Toplam: {len(orphaned_trailing)}")
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
    cleanup_orphaned_trailing_stops()

