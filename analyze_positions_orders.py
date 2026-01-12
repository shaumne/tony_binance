#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze positions and their orders (TP/SL/Trailing Stop)
"""

import sys
import os
import json
from binance.client import Client
from binance.exceptions import BinanceAPIException

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

def analyze_positions_orders():
    """Analyze positions and their associated orders"""
    
    print("=" * 100)
    print("POSITION VE EMIR ANALIZI")
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
        active_positions = []
        for pos in positions:
            pos_amt = abs(float(pos.get('positionAmt', '0')))
            if pos_amt > 0:
                active_positions.append(pos)
        
        # Get open orders
        open_orders = client.futures_get_open_orders()
        
        # Get algo orders (trailing stops)
        algo_orders = []
        try:
            if hasattr(client, 'futures_get_open_algo_orders'):
                algo_orders = client.futures_get_open_algo_orders()
            else:
                # Fallback: Get algo orders per symbol
                symbols = set([p.get('symbol') for p in active_positions])
                for symbol in symbols:
                    try:
                        if hasattr(client, 'futures_get_all_algo_orders'):
                            symbol_algos = client.futures_get_all_algo_orders(symbol=symbol)
                            algo_orders.extend([a for a in symbol_algos if a.get('algoStatus') == 'NEW' and a.get('orderType') == 'TRAILING_STOP_MARKET'])
                    except:
                        continue
        except Exception as e:
            print(f"[WARNING] Algo orders alinamadi: {str(e)}")
        
        print(f"Toplam Aktif Pozisyon: {len(active_positions)}")
        print(f"Toplam Acik Emir (Normal): {len(open_orders)}")
        print(f"Toplam Algo Emir (Trailing Stop): {len(algo_orders)}")
        print()
        
        # Analyze each position
        print("=" * 100)
        print("POZISYON ANALIZI")
        print("=" * 100)
        print()
        
        for pos in active_positions:
            symbol = pos.get('symbol', 'N/A')
            side = pos.get('positionSide', 'BOTH')
            size = abs(float(pos.get('positionAmt', '0')))
            
            # Find related orders
            trailing_stops = [a for a in algo_orders if a.get('symbol') == symbol and a.get('positionSide') == side]
            stop_losses = [o for o in open_orders if o.get('symbol') == symbol and 
                          o.get('type') in ['STOP_MARKET', 'STOP'] and
                          ((side == 'BOTH' and o.get('positionSide', 'BOTH') == 'BOTH') or 
                           (side != 'BOTH' and o.get('positionSide') == side))]
            take_profits = [o for o in open_orders if o.get('symbol') == symbol and 
                           o.get('type') in ['TAKE_PROFIT_MARKET', 'TAKE_PROFIT'] and
                           ((side == 'BOTH' and o.get('positionSide', 'BOTH') == 'BOTH') or 
                            (side != 'BOTH' and o.get('positionSide') == side))]
            
            print(f"Pozisyon: {symbol} | {side} | Size: {size}")
            print(f"  Trailing Stop: {'VAR (' + str(len(trailing_stops)) + ')' if trailing_stops else 'YOK'}")
            if trailing_stops:
                for ts in trailing_stops:
                    print(f"    - Algo ID: {ts.get('algoId')} | Callback: {ts.get('callbackRate')}% | Activation: {ts.get('activatePrice')}")
            print(f"  Stop Loss: {'VAR (' + str(len(stop_losses)) + ')' if stop_losses else 'YOK'}")
            if stop_losses:
                for sl in stop_losses:
                    print(f"    - Order ID: {sl.get('orderId')} | Stop Price: {sl.get('stopPrice')}")
            print(f"  Take Profit: {'VAR (' + str(len(take_profits)) + ')' if take_profits else 'YOK'}")
            if take_profits:
                for tp in take_profits:
                    print(f"    - Order ID: {tp.get('orderId')} | TP Price: {tp.get('stopPrice')}")
            
            # Analysis
            if not trailing_stops and not stop_losses and not take_profits:
                print(f"  [UYARI] Bu pozisyon icin HICBIR koruma emri yok!")
            elif trailing_stops:
                print(f"  [OK] Trailing stop aktif")
            elif stop_losses or take_profits:
                print(f"  [INFO] Standart TP/SL kullaniliyor (trailing stop yok)")
            
            print()
        
        # Summary
        print("=" * 100)
        print("OZET")
        print("=" * 100)
        
        positions_with_trailing = sum(1 for pos in active_positions 
                                     if any(a.get('symbol') == pos.get('symbol') and 
                                           a.get('positionSide') == pos.get('positionSide', 'BOTH')
                                           for a in algo_orders))
        positions_with_sl = sum(1 for pos in active_positions 
                               if any(o.get('symbol') == pos.get('symbol') and 
                                     o.get('type') in ['STOP_MARKET', 'STOP']
                                     for o in open_orders))
        positions_with_tp = sum(1 for pos in active_positions 
                               if any(o.get('symbol') == pos.get('symbol') and 
                                     o.get('type') in ['TAKE_PROFIT_MARKET', 'TAKE_PROFIT']
                                     for o in open_orders))
        positions_with_nothing = len(active_positions) - positions_with_trailing - positions_with_sl - positions_with_tp
        
        print(f"Trailing Stop olan pozisyonlar: {positions_with_trailing}/{len(active_positions)}")
        print(f"Stop Loss olan pozisyonlar: {positions_with_sl}/{len(active_positions)}")
        print(f"Take Profit olan pozisyonlar: {positions_with_tp}/{len(active_positions)}")
        print(f"Koruma emri olmayan pozisyonlar: {positions_with_nothing}/{len(active_positions)}")
        
    except BinanceAPIException as e:
        print(f"[ERROR] Binance API Error: {e.message} (Code: {e.code})")
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_positions_orders()

