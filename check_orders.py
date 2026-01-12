#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binance Futures Orders Checker
Tüm açık emirleri, TP/SL'leri ve trailing stop'ları gösterir
"""

import sys
import os
from datetime import datetime
from binance.client import Client
from binance.exceptions import BinanceAPIException
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Config

def load_config():
    """Load configuration from JSON file"""
    config_file = 'data/config.json'
    backup_file = 'data/config_backup.json'
    
    try:
        if not os.path.exists(config_file):
            if os.path.exists(backup_file):
                print(f"⚠️  Config file not found, using backup: {backup_file}")
                config_file = backup_file
            else:
                print(f"❌ Config file not found: {config_file}")
                return None
        
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return Config.from_dict(data)
    except Exception as e:
        print(f"❌ Error loading config: {str(e)}")
        return None

def format_datetime(timestamp_ms):
    """Convert timestamp to readable datetime"""
    if timestamp_ms:
        return datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
    return "N/A"

def format_price(price, symbol):
    """Format price based on symbol precision"""
    if not price or float(price) == 0:
        return "N/A"
    
    # Price precision based on symbol
    price_precision = {
        'BTCUSDT': 1, 'BTCUSDC': 1,
        'ETHUSDT': 2, 'ETHUSDC': 2,
        'SOLUSDT': 2, 'SOLUSDC': 2,
        'BNBUSDT': 2, 'BNBUSDC': 2,
        'XRPUSDT': 4, 'XRPUSDC': 4,
        'ADAUSDT': 4, 'ADAUSDC': 4,
        'DOTUSDT': 3, 'XLMUSDT': 5,
        'IMXUSDT': 4, 'DOGEUSDT': 6,
        'INJUSDT': 3, 'LDOUSDT': 4,
        'ARBUSDT': 4, 'ARBUSDC': 4,
        'UNIUSDT': 3, 'UNIUSDC': 3,
        'FETUSDT': 4,
    }
    
    precision = price_precision.get(symbol.upper(), 2)
    return f"${float(price):.{precision}f}"

def get_order_type_display(order_type):
    """Get display name for order type"""
    type_map = {
        'MARKET': 'MARKET',
        'LIMIT': 'LIMIT',
        'STOP_MARKET': '🛑 STOP_MARKET',
        'TAKE_PROFIT_MARKET': '🎯 TAKE_PROFIT',
        'TRAILING_STOP_MARKET': '🔥 TRAILING_STOP',
        'STOP': 'STOP',
        'TAKE_PROFIT': 'TAKE_PROFIT',
    }
    return type_map.get(order_type, order_type)

def get_order_status_display(status):
    """Get display name for order status"""
    status_map = {
        'NEW': '✅ NEW (Aktif)',
        'PARTIALLY_FILLED': '⚠️ PARTIALLY_FILLED',
        'FILLED': '✅ FILLED',
        'CANCELED': '❌ CANCELED',
        'EXPIRED': '⏰ EXPIRED',
        'REJECTED': '❌ REJECTED',
    }
    return status_map.get(status, status)

def check_orders():
    """Check all orders from Binance Futures"""
    
    print("=" * 100)
    print("🔍 BINANCE FUTURES ORDERS CHECKER")
    print("=" * 100)
    print()
    
    # Load config
    try:
        config = load_config()
        if not config.binance_api_key or not config.binance_secret_key:
            print("❌ HATA: Binance API anahtarları bulunamadı!")
            print("   Lütfen settings sayfasından API anahtarlarınızı girin.")
            return
        
        # Initialize Binance client
        client = Client(config.binance_api_key, config.binance_secret_key)
        
        print("✅ Binance API bağlantısı başarılı")
        print()
        
    except Exception as e:
        print(f"❌ HATA: Config yüklenemedi: {str(e)}")
        return
    
    try:
        # Get all open orders (regular orders)
        print("📥 Açık emirler çekiliyor...")
        open_orders = client.futures_get_open_orders()
        
        # Get algo orders (trailing stop orders are algo orders)
        print("Algo emirler (Trailing Stop) cekiliyor...")
        try:
            # Try to get algo orders - method might not exist in older python-binance versions
            if hasattr(client, 'futures_get_open_algo_orders'):
                algo_orders = client.futures_get_open_algo_orders()
            else:
                # Fallback: Use futures_get_all_algo_orders with symbol filter
                # Get algo orders for common symbols
                algo_orders = []
                symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'LDOUSDT', 'XLMUSDT', 'ADAUSDT', 'DOTUSDT', 'UNIUSDT', 'DOGEUSDT', 'FETUSDT', 'INJUSDT', 'IMXUSDT', 'ARBUSDT']
                for symbol in symbols:
                    try:
                        if hasattr(client, 'futures_get_all_algo_orders'):
                            symbol_algos = client.futures_get_all_algo_orders(symbol=symbol)
                            # Filter for open algo orders (status NEW)
                            algo_orders.extend([a for a in symbol_algos if a.get('algoStatus') == 'NEW'])
                    except:
                        continue
            
            # Convert algo orders to same format for processing
            for algo_order in algo_orders:
                if algo_order.get('orderType') == 'TRAILING_STOP_MARKET':
                    # Convert algo order to order-like format
                    order_like = {
                        'symbol': algo_order.get('symbol'),
                        'side': algo_order.get('side'),
                        'type': algo_order.get('orderType'),
                        'status': algo_order.get('algoStatus'),
                        'orderId': algo_order.get('algoId'),  # Use algoId as orderId
                        'callbackRate': algo_order.get('callbackRate'),
                        'activationPrice': algo_order.get('activatePrice'),
                        'workingType': algo_order.get('workingType'),
                        'positionSide': algo_order.get('positionSide', 'BOTH'),
                        'closePosition': algo_order.get('closePosition', False),
                        'time': algo_order.get('createTime', 0),
                        'origQty': algo_order.get('quantity', '0')
                    }
                    open_orders.append(order_like)
        except Exception as e:
            print(f"[WARNING] Algo orders alinamadi: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print(f"✅ {len(open_orders)} açık emir bulundu (normal + algo)")
        print()
        
        if not open_orders:
            print("ℹ️  Açık emir bulunmuyor.")
            return
        
        # Group orders by type
        market_orders = []
        stop_orders = []
        take_profit_orders = []
        trailing_stop_orders = []
        other_orders = []
        
        for order in open_orders:
            order_type = order.get('type', '')
            if order_type == 'MARKET' or order_type == 'LIMIT':
                market_orders.append(order)
            elif order_type == 'STOP_MARKET' or order_type == 'STOP':
                stop_orders.append(order)
            elif order_type == 'TAKE_PROFIT_MARKET' or order_type == 'TAKE_PROFIT':
                take_profit_orders.append(order)
            elif order_type == 'TRAILING_STOP_MARKET':
                trailing_stop_orders.append(order)
            else:
                other_orders.append(order)
        
        # Display Market/Limit Orders
        if market_orders:
            print("=" * 100)
            print("📊 MARKET/LIMIT ORDERS (Entry Orders)")
            print("=" * 100)
            for order in market_orders:
                symbol = order.get('symbol', 'N/A')
                side = order.get('side', 'N/A')
                order_type = order.get('type', 'N/A')
                status = order.get('status', 'N/A')
                quantity = order.get('origQty', '0')
                price = order.get('price', '0')
                time = format_datetime(order.get('time', 0))
                
                print(f"  📌 {symbol} | {side} | {get_order_type_display(order_type)}")
                print(f"     Status: {get_order_status_display(status)}")
                print(f"     Quantity: {quantity} | Price: {format_price(price, symbol)}")
                print(f"     Time: {time}")
                print(f"     Order ID: {order.get('orderId', 'N/A')}")
                print()
        
        # Display Stop Loss Orders
        if stop_orders:
            print("=" * 100)
            print("🛑 STOP LOSS ORDERS")
            print("=" * 100)
            for order in stop_orders:
                symbol = order.get('symbol', 'N/A')
                side = order.get('side', 'N/A')
                status = order.get('status', 'N/A')
                stop_price = order.get('stopPrice', '0')
                activation_price = order.get('activationPrice', stop_price)
                position_side = order.get('positionSide', 'BOTH')
                close_position = order.get('closePosition', False)
                time = format_datetime(order.get('time', 0))
                
                print(f"  🛑 {symbol} | {side} | Position: {position_side}")
                print(f"     Status: {get_order_status_display(status)}")
                print(f"     Stop Price: {format_price(stop_price, symbol)}")
                if activation_price != stop_price:
                    print(f"     Activation Price: {format_price(activation_price, symbol)}")
                print(f"     Close Position: {'✅ Yes' if close_position else '❌ No'}")
                print(f"     Time: {time}")
                print(f"     Order ID: {order.get('orderId', 'N/A')}")
                print()
        
        # Display Take Profit Orders
        if take_profit_orders:
            print("=" * 100)
            print("🎯 TAKE PROFIT ORDERS")
            print("=" * 100)
            for order in take_profit_orders:
                symbol = order.get('symbol', 'N/A')
                side = order.get('side', 'N/A')
                status = order.get('status', 'N/A')
                stop_price = order.get('stopPrice', '0')
                position_side = order.get('positionSide', 'BOTH')
                close_position = order.get('closePosition', False)
                time = format_datetime(order.get('time', 0))
                
                print(f"  🎯 {symbol} | {side} | Position: {position_side}")
                print(f"     Status: {get_order_status_display(status)}")
                print(f"     Take Profit Price: {format_price(stop_price, symbol)}")
                print(f"     Close Position: {'✅ Yes' if close_position else '❌ No'}")
                print(f"     Time: {time}")
                print(f"     Order ID: {order.get('orderId', 'N/A')}")
                print()
        
        # Display Trailing Stop Orders
        if trailing_stop_orders:
            print("=" * 100)
            print("🔥 TRAILING STOP ORDERS")
            print("=" * 100)
            for order in trailing_stop_orders:
                symbol = order.get('symbol', 'N/A')
                side = order.get('side', 'N/A')
                status = order.get('status', 'N/A')
                callback_rate = order.get('callbackRate', '0')
                activation_price = order.get('activationPrice', '0')
                working_type = order.get('workingType', 'N/A')
                position_side = order.get('positionSide', 'BOTH')
                close_position = order.get('closePosition', False)
                time = format_datetime(order.get('time', 0))
                
                print(f"  🔥 {symbol} | {side} | Position: {position_side}")
                print(f"     Status: {get_order_status_display(status)}")
                print(f"     Callback Rate: {callback_rate}%")
                print(f"     Activation Price: {format_price(activation_price, symbol)}")
                print(f"     Working Type: {working_type}")
                print(f"     Close Position: {'✅ Yes' if close_position else '❌ No'}")
                print(f"     Time: {time}")
                print(f"     Order ID: {order.get('orderId', 'N/A')}")
                print()
        
        # Display Other Orders
        if other_orders:
            print("=" * 100)
            print("📋 OTHER ORDERS")
            print("=" * 100)
            for order in other_orders:
                symbol = order.get('symbol', 'N/A')
                side = order.get('side', 'N/A')
                order_type = order.get('type', 'N/A')
                status = order.get('status', 'N/A')
                time = format_datetime(order.get('time', 0))
                
                print(f"  📋 {symbol} | {side} | Type: {order_type}")
                print(f"     Status: {get_order_status_display(status)}")
                print(f"     Time: {time}")
                print(f"     Order ID: {order.get('orderId', 'N/A')}")
                print(f"     Full Data: {json.dumps(order, indent=2)}")
                print()
        
        # Summary
        print("=" * 100)
        print("📊 ÖZET")
        print("=" * 100)
        print(f"  📊 Market/Limit Orders: {len(market_orders)}")
        print(f"  🛑 Stop Loss Orders: {len(stop_orders)}")
        print(f"  🎯 Take Profit Orders: {len(take_profit_orders)}")
        print(f"  🔥 Trailing Stop Orders: {len(trailing_stop_orders)}")
        print(f"  📋 Other Orders: {len(other_orders)}")
        print(f"  📈 Toplam Açık Emir: {len(open_orders)}")
        print()
        
        # Check active positions
        print("=" * 100)
        print("💼 AÇIK POZİSYONLAR")
        print("=" * 100)
        try:
            positions = client.futures_position_information()
            active_positions = []
            
            for pos in positions:
                position_amt = abs(float(pos.get('positionAmt', '0')))
                if position_amt > 0:
                    active_positions.append(pos)
            
            if active_positions:
                print(f"✅ {len(active_positions)} aktif pozisyon bulundu:")
                print()
                for pos in active_positions:
                    symbol = pos.get('symbol', 'N/A')
                    side = pos.get('positionSide', 'BOTH')
                    size = abs(float(pos.get('positionAmt', '0')))
                    entry_price = float(pos.get('entryPrice', '0'))
                    mark_price = float(pos.get('markPrice', '0'))
                    unrealized_pnl = float(pos.get('unrealizedProfit', '0'))
                    leverage = pos.get('leverage', '1')
                    
                    print(f"  💼 {symbol} | {side} | Size: {size}")
                    print(f"     Entry: {format_price(entry_price, symbol)} | Mark: {format_price(mark_price, symbol)}")
                    print(f"     Unrealized PnL: ${unrealized_pnl:.2f} | Leverage: {leverage}x")
                    print()
            else:
                print("ℹ️  Aktif pozisyon bulunmuyor.")
        except Exception as e:
            print(f"⚠️  Pozisyon bilgileri alınamadı: {str(e)}")
        
        print("=" * 100)
        print("✅ Kontrol tamamlandı!")
        print("=" * 100)
        
    except BinanceAPIException as e:
        print(f"❌ Binance API Hatası: {e.message} (Code: {e.code})")
    except Exception as e:
        print(f"❌ HATA: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        check_orders()
    except KeyboardInterrupt:
        print("\n⚠️  İşlem kullanıcı tarafından iptal edildi.")
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()

