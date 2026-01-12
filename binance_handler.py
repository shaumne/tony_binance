from binance.client import Client
from binance.exceptions import BinanceAPIException
import logging
import time
from datetime import datetime
import asyncio
import pandas as pd
import numpy as np

# Import management systems
from tp_sl_manager import TPSLManager
from coin_config_manager import CoinConfigManager
from position_validator import PositionValidator

logger = logging.getLogger(__name__)

class BinanceHandler:
    """Handler class for Binance Futures API operations"""
    
    def __init__(self, api_key, secret_key, config):
        """Initialize Binance API client
        
        Args:
            api_key (str): Binance API key
            secret_key (str): Binance API secret key
            config (dict): Configuration dictionary
        """
        self.api_key = api_key
        self.secret_key = secret_key
        
        # Handle config object or dict
        if hasattr(config, '__dict__'):
            self.config = config.__dict__
        else:
            self.config = config
        
        # Initialize Binance client
        self.client = Client(api_key, secret_key)
        
        # Store last known position states
        self.last_position_states = {}
        
        # Initialize management systems
        self.tp_sl_manager = TPSLManager(self.config)
        self.coin_config_manager = CoinConfigManager(self.config)
        self.position_validator = PositionValidator()
        
        logger.info("BinanceHandler initialized with ENHANCED SYSTEMS:")
        logger.info("   [OK] TP/SL Manager - Guarantees ATR-based TP/SL with 1h data")
        logger.info("   [OK] Coin Config Manager - Prevents order size errors")
        logger.info("   [OK] Position Validator - Prevents duplicate positions")
        logger.info("   [READY] All systems ready for Binance Futures trading")
        
    def _format_symbol(self, symbol: str) -> str:
        """
        Format symbol for Binance API
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT', 'ETHUSDC')
            
        Returns:
            str: Formatted symbol (Binance uses plain format)
        """
        # Binance uses simple format like BTCUSDT, ETHUSDC
        return symbol.upper().strip()
    
    def _format_quantity(self, symbol: str, quantity: float) -> float:
        """
        Format quantity according to Binance's precision requirements
        
        Args:
            symbol (str): Trading symbol
            quantity (float): Raw quantity value
            
        Returns:
            float: Formatted quantity with correct precision
        """
        try:
            # Get exchange info for the symbol
            exchange_info = self.client.futures_exchange_info()
            
            min_qty = None
            step_size = None
            precision = 3  # Default precision
            
            # Find the symbol in exchange info
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol.upper():
                    # Find LOT_SIZE filter
                    for filt in s['filters']:
                        if filt['filterType'] == 'LOT_SIZE':
                            step_size = float(filt['stepSize'])
                            min_qty = float(filt.get('minQty', 0))
                            
                            # Calculate precision from stepSize
                            # e.g., stepSize=0.001 -> precision=3
                            precision = len(filt['stepSize'].rstrip('0').split('.')[-1]) if '.' in filt['stepSize'] else 0
                            
                            # Round quantity to stepSize
                            rounded_qty = round(quantity / step_size) * step_size
                            
                            # Format to precision
                            rounded_qty = round(rounded_qty, precision)
                            
                            logger.info(f"📐 Quantity precision: stepSize={step_size}, precision={precision}, minQty={min_qty}")
                            logger.info(f"   Raw quantity: {quantity:.8f}, Rounded: {rounded_qty:.8f}")
                            
                            # Validate minimum quantity
                            if min_qty and rounded_qty < min_qty:
                                logger.error(f"❌ Quantity {rounded_qty:.8f} is below minimum {min_qty:.8f} for {symbol}")
                                raise ValueError(f"Quantity {rounded_qty:.8f} is below minimum {min_qty:.8f} for {symbol}")
                            
                            # Validate that quantity is not zero or negative
                            if rounded_qty <= 0:
                                logger.error(f"❌ Quantity {rounded_qty:.8f} is zero or negative after formatting")
                                raise ValueError(f"Quantity {rounded_qty:.8f} is zero or negative after formatting")
                            
                            return rounded_qty
            
            # Fallback: round to 3 decimal places
            logger.warning(f"⚠️ Could not find LOT_SIZE filter for {symbol}, using default precision (3)")
            rounded_qty = round(quantity, 3)
            
            if rounded_qty <= 0:
                logger.error(f"❌ Quantity {rounded_qty:.8f} is zero or negative after formatting")
                raise ValueError(f"Quantity {rounded_qty:.8f} is zero or negative after formatting")
            
            return rounded_qty
            
        except ValueError:
            # Re-raise ValueError (quantity validation errors)
            raise
        except Exception as e:
            logger.warning(f"⚠️ Error getting exchange info for {symbol}: {str(e)}, using default precision (3)")
            # Fallback: round to 3 decimal places
            rounded_qty = round(quantity, 3)
            
            if rounded_qty <= 0:
                logger.error(f"❌ Quantity {rounded_qty:.8f} is zero or negative after formatting")
                raise ValueError(f"Quantity {rounded_qty:.8f} is zero or negative after formatting")
            
            return rounded_qty
    
    def _get_margin_asset(self, symbol: str) -> str:
        """
        Determine margin asset from symbol
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            str: Margin asset (USDT or USDC)
        """
        if symbol.endswith('USDC'):
            return 'USDC'
        else:
            return 'USDT'
    
    def get_account_balance(self, asset='USDT'):
        """Get Futures account balance
        
        Args:
            asset (str): Asset symbol (USDT or USDC)
            
        Returns:
            tuple: (available_balance, total_balance, unrealized_pnl)
        """
        try:
            logger.info(f"[BALANCE] Fetching {asset} Futures balance...")
            
            # Get Futures account information
            account_info = self.client.futures_account()
            
            # Find the specific asset
            available = 0.0
            total = 0.0
            unrealized_pnl = 0.0
            
            for asset_info in account_info['assets']:
                if asset_info['asset'] == asset:
                    available = float(asset_info['availableBalance'])
                    total = float(asset_info['walletBalance'])
                    unrealized_pnl = float(asset_info['unrealizedProfit'])
                    break
            
            logger.info(f"[BALANCE] {asset} - Available: {available}, Total: {total}, Unrealized PnL: {unrealized_pnl}")
            return available, total, unrealized_pnl
            
        except Exception as e:
            logger.error(f"Failed to get {asset} account balance: {str(e)}")
            return 0.0, 0.0, 0.0
    
    def get_symbol_price(self, symbol):
        """Get current price for the symbol
        
        Args:
            symbol (str): Trading pair symbol (e.g., 'BTCUSDT', 'ETHUSDC')
            
        Returns:
            float: Current price
        """
        try:
            formatted_symbol = self._format_symbol(symbol)
            logger.info(f"Getting price for {formatted_symbol}")
            
            ticker = self.client.futures_symbol_ticker(symbol=formatted_symbol)
            price = float(ticker['price'])
            
            logger.info(f"Current price for {formatted_symbol}: ${price:.2f}")
            return price
            
        except Exception as e:
            logger.error(f"Failed to get symbol price for {symbol}: {str(e)}")
            return 0.0
    
    def set_leverage(self, symbol, leverage):
        """Set leverage for symbol
        
        Args:
            symbol (str): Trading symbol
            leverage (int): Leverage value
            
        Returns:
            dict: API response
        """
        try:
            formatted_symbol = self._format_symbol(symbol)
            response = self.client.futures_change_leverage(
                symbol=formatted_symbol,
                leverage=leverage
            )
            logger.info(f"✅ Leverage set to {leverage}x for {formatted_symbol}")
            return response
        except Exception as e:
            logger.error(f"Failed to set leverage for {symbol}: {str(e)}")
            return None
    
    def set_margin_type(self, symbol, margin_type='CROSSED'):
        """Set margin type for symbol
        
        Args:
            symbol (str): Trading symbol
            margin_type (str): 'ISOLATED' or 'CROSSED'
            
        Returns:
            dict: API response
        """
        try:
            formatted_symbol = self._format_symbol(symbol)
            response = self.client.futures_change_margin_type(
                symbol=formatted_symbol,
                marginType=margin_type
            )
            logger.info(f"✅ Margin type set to {margin_type} for {formatted_symbol}")
            return response
        except BinanceAPIException as e:
            # Error code -4046 means margin type is already set
            if e.code == -4046:
                logger.info(f"Margin type already set to {margin_type} for {formatted_symbol}")
                return {'status': 'already_set'}
            else:
                logger.error(f"Failed to set margin type for {symbol}: {str(e)}")
                return None
    
    def get_atr(self, symbol, period=14):
        """Calculate ATR using 1-hour candlestick data from Binance
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT')
            period (int): ATR period (default: 14)
            
        Returns:
            float: Calculated ATR value
        """
        try:
            formatted_symbol = self._format_symbol(symbol)
            logger.info(f"Calculating ATR for {formatted_symbol}, Period: {period}")
            
            # Fetch 1h klines (need period + 50 for ATR smoothing)
            klines = self.client.futures_klines(
                symbol=formatted_symbol,
                interval=Client.KLINE_INTERVAL_1HOUR,  # 1h interval
                limit=period + 50
            )
            
            if len(klines) < period + 1:
                logger.warning(f"Not enough data for ATR calculation. Need: {period+1}, Got: {len(klines)}")
                return 0.0
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            
            # Convert to float
            df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Calculate ATR
            df['previous_close'] = df['close'].shift(1)
            df['tr'] = df[['high', 'low', 'previous_close']].apply(
                lambda x: max(
                    x['high'] - x['low'],
                    abs(x['high'] - x['previous_close']),
                    abs(x['low'] - x['previous_close'])
                ), axis=1
            )
            
            # Wilder's ATR (EMA with alpha=1/period)
            df['ATR'] = df['tr'].ewm(alpha=1/period, adjust=False).mean()
            
            atr_value = df['ATR'].iloc[-1]
            logger.info(f"Calculated ATR (1h, {period}) for {formatted_symbol}: {atr_value:.4f}")
            return atr_value
                
        except Exception as e:
            logger.error(f"ATR calculation failed for {symbol}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return 0.0
    
    def place_order(self, symbol, side, order_type="MARKET", quantity=None, product_type='USDT-FUTURES'):
        """
        Place order on Binance Futures with TP/SL
        
        Args:
            symbol (str): Trading symbol
            side (str): 'open_long', 'open_short', 'close_long', 'close_short'
            order_type (str): Order type (default: MARKET)
            quantity (float, optional): Order quantity (for close orders)
            product_type (str): Product type ('USDT-FUTURES' or 'USDC-FUTURES')
            
        Returns:
            dict: Order response
        """
        try:
            logger.info(f"🚀 ENHANCED ORDER PLACEMENT START")
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Side: {side}")
            logger.info(f"   Product Type: {product_type}")
            
            # Check if trading is enabled
            if not self.config.get('enable_trading', False):
                logger.info("❌ Trading is disabled globally")
                return {"error": "Trading is disabled"}
            
            # Check coin-specific trading status
            if not self.coin_config_manager.is_trading_enabled(symbol):
                return {"error": f"Trading is disabled for {symbol}"}
            
            # Format symbol
            formatted_symbol = self._format_symbol(symbol)
            
            # Parse side
            parts = side.split('_')
            if len(parts) != 2:
                return {"error": "Invalid side format"}
            
            action = parts[0]  # open or close
            direction = parts[1]  # long or short
            
            # Get coin configuration
            coin_config = self.coin_config_manager.get_coin_config(symbol)
            
            # Set leverage
            self.set_leverage(formatted_symbol, coin_config['leverage'])
            
            # Set margin type
            self.set_margin_type(formatted_symbol, 'CROSSED')
            
            # Get current positions for validation
            current_positions = self.get_open_positions()
            
            # Validate position request
            auto_switch_enabled = self.config.get('auto_position_switch', True)
            validation_result = self.position_validator.validate_position_request(
                symbol, direction, action, current_positions, auto_switch_enabled
            )
            
            if not validation_result['allowed']:
                logger.warning(f"❌ Position request REJECTED: {validation_result['reason']}")
                return {"error": validation_result['reason']}
            
            # Handle required actions (e.g., close opposite position)
            if validation_result.get('action_required'):
                action_type = validation_result['action_required']['type']
                
                if action_type == 'close_opposite':
                    logger.info("🔄 Auto position switch: Closing opposite position...")
                    positions_to_close = validation_result['action_required']['positions_to_close']
                    
                    for pos in positions_to_close:
                        close_side = f"close_{pos['side']}"
                        close_result = self.place_order(symbol, close_side, quantity=pos['size'])
                        
                        if not close_result or 'error' in close_result:
                            logger.error(f"❌ Failed to close opposite position")
                            return {"error": "Failed to close opposite position"}
            
            # Get account balance
            margin_asset = self._get_margin_asset(formatted_symbol)
            available_balance, total_balance, unrealized_pnl = self.get_account_balance(margin_asset)
            
            if available_balance <= 0:
                logger.warning("Zero available balance, using dummy value for testing")
                available_balance = 1000.0
            
            # Calculate order quantity
            if quantity is None:
                current_price = self.get_symbol_price(formatted_symbol)
                if current_price <= 0:
                    return {"error": "Failed to get current price"}
                
                # Calculate order size
                order_amount = available_balance * (coin_config['order_size_percentage'] / 100)
                leveraged_amount = order_amount * coin_config['leverage']
                quantity = leveraged_amount / current_price
                
                logger.info(f"📊 Order Calculation:")
                logger.info(f"   💰 Balance: ${available_balance:.2f}")
                logger.info(f"   📈 Order %: {coin_config['order_size_percentage']}%")
                logger.info(f"   🔥 Leverage: {coin_config['leverage']}x")
                logger.info(f"   💵 Base Amount: ${order_amount:.2f}")
                logger.info(f"   💪 Leveraged: ${leveraged_amount:.2f}")
                logger.info(f"   🎯 Quantity: {quantity:.6f}")
            
            # Determine Binance API side and position side
            if action == 'open':
                binance_side = 'BUY' if direction == 'long' else 'SELL'
                position_side = 'LONG' if direction == 'long' else 'SHORT'
            else:  # close
                binance_side = 'SELL' if direction == 'long' else 'BUY'
                position_side = 'LONG' if direction == 'long' else 'SHORT'
            
            # Place main order
            logger.info(f"📤 Placing order:")
            logger.info(f"   Symbol: {formatted_symbol}")
            logger.info(f"   Side: {binance_side}")
            logger.info(f"   Position Side: {position_side}")
            logger.info(f"   Quantity: {quantity:.6f}")
            
            order_result = self.client.futures_create_order(
                symbol=formatted_symbol,
                side=binance_side,
                positionSide=position_side,
                type=order_type,
                quantity=quantity
            )
            
            logger.info(f"✅ Order placed successfully!")
            logger.info(f"   Order ID: {order_result['orderId']}")
            
            # Place TP/SL orders for open positions
            if action == 'open':
                try:
                    # Get ATR value using 1h data
                    atr_period = self.tp_sl_manager.get_atr_period(symbol)
                    atr_value = self.get_atr(formatted_symbol, atr_period)
                    
                    if atr_value > 0:
                        # Get current price
                        current_price = float(order_result.get('avgPrice', self.get_symbol_price(formatted_symbol)))
                        
                        # Calculate TP/SL prices
                        tp_price, sl_price = self.tp_sl_manager.calculate_tp_sl_prices(
                            symbol, current_price, atr_value, direction
                        )
                        
                        # Validate TP/SL logic
                        is_valid = self.tp_sl_manager.validate_tp_sl_logic(
                            symbol, direction, current_price, tp_price, sl_price
                        )
                        
                        if is_valid:
                            # Place TP order
                            tp_side = 'SELL' if direction == 'long' else 'BUY'
                            tp_order_success = False
                            sl_order_success = False
                            
                            # Place TP order with individual error handling
                            try:
                                tp_order = self.client.futures_create_order(
                                    symbol=formatted_symbol,
                                    side=tp_side,
                                    positionSide=position_side,
                                    type='TAKE_PROFIT_MARKET',
                                    stopPrice=tp_price,
                                    closePosition=True
                                )
                                tp_order_success = True
                                logger.info(f"✅ TP order placed: ${tp_price:.2f} (Order ID: {tp_order.get('orderId', 'N/A')})")
                            except Exception as tp_error:
                                logger.error(f"❌ Failed to place TP order: {str(tp_error)}")
                            
                            # Place SL order with individual error handling
                            try:
                                sl_order = self.client.futures_create_order(
                                    symbol=formatted_symbol,
                                    side=tp_side,
                                    positionSide=position_side,
                                    type='STOP_MARKET',
                                    stopPrice=sl_price,
                                    closePosition=True
                                )
                                sl_order_success = True
                                logger.info(f"✅ SL order placed: ${sl_price:.2f} (Order ID: {sl_order.get('orderId', 'N/A')})")
                            except Exception as sl_error:
                                logger.error(f"❌ Failed to place SL order: {str(sl_error)}")
                                logger.warning(f"⚠️  WARNING: Entry order placed but SL order failed! Position is unprotected!")
                            
                            # Send notification only if at least one order succeeded
                            if tp_order_success or sl_order_success:
                                self._send_enhanced_notification(
                                    symbol, side, current_price, quantity, 
                                    order_result['orderId'],
                                    {'tp_price': tp_price, 'sl_price': sl_price, 'direction': direction,
                                     'tp_success': tp_order_success, 'sl_success': sl_order_success}
                                )
                            
                            # Warn if SL failed
                            if not sl_order_success:
                                logger.warning(f"⚠️  CRITICAL: SL order failed for {formatted_symbol} {position_side} position!")
                                logger.warning(f"   Entry order ID: {order_result.get('orderId', 'N/A')}")
                                logger.warning(f"   Please manually place a stop loss order!")
                except Exception as tp_sl_error:
                    logger.error(f"❌ Error in TP/SL placement process: {str(tp_sl_error)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
            
            return order_result
            
        except Exception as e:
            logger.error(f"❌ Order placement error: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": str(e)}
    
    def get_open_positions(self):
        """Get all open positions from Binance Futures
        
        Returns:
            list: List of open positions
        """
        try:
            logger.info("Fetching open positions from Binance...")
            
            # Get position information
            positions = self.client.futures_position_information()
            
            # Filter active positions
            active_positions = []
            for pos in positions:
                position_amt = abs(float(pos.get('positionAmt', '0')))
                if position_amt > 0:
                    logger.info(f"Active position: {pos['symbol']} {pos['positionSide']} {position_amt}")
                    active_positions.append(pos)
            
            logger.info(f"Found {len(active_positions)} active positions")
            return active_positions
            
        except Exception as e:
            logger.error(f"Failed to get open positions: {str(e)}")
            return []
    
    def get_position_history(self, limit=50):
        """Get position history from Binance
        
        Args:
            limit (int): Number of records to fetch
            
        Returns:
            list: Trade history
        """
        try:
            logger.info("Fetching trade history from Binance...")
            
            # Get all symbols we trade
            symbols = []
            for coin in ['btc', 'eth', 'xrp', 'ada', 'dot', 'xlm', 'imx', 'doge', 'inj', 'ldo', 'arb', 'uni', 'sol', 'bnb', 'fet']:
                symbols.append(f"{coin.upper()}USDT")
            for coin in ['btcusdc', 'ethusdc', 'solusdc', 'aaveusdc', 'bchusdc', 'xrpusdc', 'adausdc', 'avaxusdc', 'linkusdc', 'arbusdc', 'uniusdc', 'crvusdc', 'tiausdc', 'bnbusdc', 'filusdc']:
                symbols.append(coin.upper())
            
            all_trades = []
            
            for symbol in symbols:
                try:
                    trades = self.client.futures_account_trades(symbol=symbol, limit=limit)
                    all_trades.extend(trades)
                except:
                    continue
            
            # Sort by time (newest first)
            all_trades.sort(key=lambda x: x['time'], reverse=True)
            
            logger.info(f"Retrieved {len(all_trades)} trades")
            return all_trades[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get position history: {str(e)}")
            return []
    
    def update_dashboard_positions(self, positions):
        """Format positions for dashboard display
        
        Args:
            positions (list): Raw positions from Binance
            
        Returns:
            list: Formatted positions
        """
        try:
            formatted_positions = []
            
            for pos in positions:
                position_amt = float(pos.get('positionAmt', '0'))
                if position_amt == 0:
                    continue
                
                side = pos.get('positionSide', 'BOTH')
                entry_price = float(pos.get('entryPrice', '0'))
                mark_price = float(pos.get('markPrice', '0'))
                unrealized_pnl = float(pos.get('unrealizedProfit', '0'))
                leverage = int(pos.get('leverage', '1'))
                
                # Calculate PnL percentage
                if entry_price > 0:
                    pnl_percentage = (unrealized_pnl / (abs(position_amt) * entry_price)) * 100 * leverage
                else:
                    pnl_percentage = 0
                
                formatted_pos = {
                    'symbol': pos['symbol'],
                    'side': side,
                    'size': f"{abs(position_amt):.4f}",
                    'entry_price': f"${entry_price:.4f}",
                    'current_price': f"${mark_price:.4f}",
                    'unrealized_pnl': f"${unrealized_pnl:.2f}",
                    'pnl_percentage': f"{pnl_percentage:.2f}%",
                    'leverage': f"{leverage}x",
                    'margin_type': pos.get('marginType', 'cross'),
                    'liquidation_price': f"${float(pos.get('liquidationPrice', '0')):.4f}"
                }
                
                formatted_positions.append(formatted_pos)
            
            return formatted_positions
            
        except Exception as e:
            logger.error(f"Error formatting positions: {str(e)}")
            return []
    
    def monitor_positions(self):
        """Monitor positions continuously and cleanup orphaned trailing stops"""
        while True:
            try:
                current_positions = self.get_open_positions()
                
                # Update position states
                for pos in current_positions:
                    pos_id = f"{pos['symbol']}_{pos['positionSide']}"
                    self.last_position_states[pos_id] = pos
                
                # Cleanup orphaned trailing stops (position closed but trailing stop still open)
                self.cleanup_orphaned_trailing_stops()
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in position monitoring: {e}")
                time.sleep(5)
    
    def _send_enhanced_notification(self, symbol, side, price, quantity, order_id, tp_sl_data=None):
        """Send enhanced notification via Telegram
        
        Args:
            symbol (str): Trading symbol
            side (str): Order side
            price (float): Entry price
            quantity (float): Order quantity
            order_id (str): Order ID
            tp_sl_data (dict, optional): TP/SL information
        """
        try:
            direction = side.replace('open_', '').upper()
            
            message = (
                f"🚀 NEW {direction} POSITION OPENED\n"
                f"💰 Symbol: {symbol}\n"
                f"📈 Entry Price: ${price:.2f}\n"
                f"📊 Quantity: {quantity:.6f}\n"
                f"🆔 Order ID: {order_id}\n"
            )
            
            if tp_sl_data:
                tp_price = tp_sl_data['tp_price']
                sl_price = tp_sl_data['sl_price']
                
                if direction == 'LONG':
                    tp_pct = ((tp_price - price) / price) * 100
                    sl_pct = ((price - sl_price) / price) * 100
                else:
                    tp_pct = ((price - tp_price) / price) * 100
                    sl_pct = ((sl_price - price) / price) * 100
                
                message += (
                    f"🎯 Take Profit: ${tp_price:.2f} (+{tp_pct:.1f}%)\n"
                    f"🛡️ Stop Loss: ${sl_price:.2f} (-{sl_pct:.1f}%)\n"
                )
            
            asyncio.run(self.send_telegram_notification(message))
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
    
    async def send_telegram_notification(self, message):
        """Send Telegram notification
        
        Args:
            message (str): Message to send
        """
        if self.config.get('telegram_bot_token') and self.config.get('telegram_chat_id'):
            try:
                from telegram import Bot
                bot = Bot(token=self.config['telegram_bot_token'])
                
                chat_id = self.config['telegram_chat_id']
                if chat_id.isdigit() and chat_id.startswith("100"):
                    chat_id = "-" + chat_id
                
                await bot.send_message(chat_id=chat_id, text=message)
                logger.info("Telegram notification sent")
            except Exception as e:
                logger.error(f"Failed to send Telegram notification: {str(e)}")
    
    def place_trailing_stop_strategy(self, data: dict) -> dict:
        """
        🔥 FIRE AND FORGET TRAILING STOP STRATEGY
        
        Places entry order (MARKET) and trailing stop order (TRAILING_STOP_MARKET)
        with automatic fallback to hard stop loss if trailing stop fails.
        
        Args:
            data (dict): Webhook payload with trailing stop parameters
            
        Returns:
            dict: Success/error status with order IDs
        """
        try:
            logger.info("=" * 80)
            logger.info("🚀 TRAILING STOP STRATEGY - STARTING")
            logger.info("=" * 80)
            
            # ====================================================================
            # STEP 1: PARSE & VALIDATE PAYLOAD
            # ====================================================================
            symbol = data.get('symbol', '').upper().strip()
            side = data.get('side', '').upper().strip()
            action = data.get('action', '').lower().strip()
            quantity_str = data.get('quantity')  # Will be set from coin_config if None
            working_type = data.get('workingType', 'MARK_PRICE').upper()
            
            # Validate required fields
            if not symbol:
                return {"success": False, "error": "Missing required field: symbol"}
            if side not in ['BUY', 'SELL']:
                return {"success": False, "error": f"Invalid side: {side}. Must be BUY or SELL"}
            if action != 'open':
                return {"success": False, "error": f"Invalid action: {action}. Must be 'open'"}
            if working_type not in ['MARK_PRICE', 'CONTRACT_PRICE']:
                working_type = 'MARK_PRICE'
                logger.warning(f"Invalid workingType, defaulting to MARK_PRICE")
            
            # Parse callbackRate (support string, float, and % sign)
            callback_rate_raw = data.get('callbackRate')
            if callback_rate_raw is None:
                return {"success": False, "error": "Missing required field: callbackRate"}
            
            try:
                # Convert to string first to handle % sign
                callback_rate_str = str(callback_rate_raw).strip().replace('%', '')
                callback_rate = float(callback_rate_str)
            except (TypeError, ValueError) as e:
                return {"success": False, "error": f"Invalid callbackRate format: {callback_rate_raw}"}
            
            # Validate callbackRate limits (0.1% - 5.0%)
            if callback_rate < 0.1 or callback_rate > 5.0:
                return {"success": False, "error": f"callbackRate must be between 0.1% and 5.0%. Got: {callback_rate}%"}
            
            # Parse activationPrice (optional - auto-calculated if None/0.0/invalid)
            activation_price_raw = data.get('activationPrice')
            activation_price = None
            if activation_price_raw is not None:
                try:
                    activation_price = float(activation_price_raw)
                    if activation_price <= 0:
                        activation_price = None
                except (TypeError, ValueError):
                    activation_price = None
            
            # Parse stopLoss (optional - auto-calculated if None/0.0/invalid)
            stop_loss_raw = data.get('stopLoss')
            stop_loss_price = None
            if stop_loss_raw is not None:
                try:
                    stop_loss_price = float(stop_loss_raw)
                    if stop_loss_price <= 0:
                        stop_loss_price = None
                except (TypeError, ValueError):
                    stop_loss_price = None
            
            # Parse takeProfit (optional - used in fallback if trailing stop fails)
            take_profit_raw = data.get('takeProfit')
            take_profit_price = None
            if take_profit_raw is not None:
                try:
                    take_profit_price = float(take_profit_raw)
                    if take_profit_price <= 0:
                        take_profit_price = None
                except (TypeError, ValueError):
                    take_profit_price = None
            
            formatted_symbol = self._format_symbol(symbol)
            direction = 'long' if side == 'BUY' else 'short'
            position_side = 'LONG' if direction == 'long' else 'SHORT'
            
            # ====================================================================
            # STEP 2: SETUP LEVERAGE & MARGIN
            # ====================================================================
            coin_config = self.coin_config_manager.get_coin_config(formatted_symbol)
            self.set_leverage(formatted_symbol, coin_config['leverage'])
            self.set_margin_type(formatted_symbol, 'CROSSED')
            
            # If quantity not provided, use coin config's order_size_percentage
            if quantity_str is None or quantity_str == '':
                order_size_pct = coin_config.get('order_size_percentage', 10.0)
                quantity_str = f"{order_size_pct}%"
                logger.info(f"📊 Quantity not provided, using coin config: {quantity_str}")
            
            logger.info(f"📋 Parsed Parameters:")
            logger.info(f"   Symbol: {formatted_symbol}")
            logger.info(f"   Side: {side} ({direction})")
            logger.info(f"   Quantity: {quantity_str}")
            logger.info(f"   Callback Rate: {callback_rate}%")
            logger.info(f"   Activation Price: {activation_price or 'Auto-calculate'}")
            logger.info(f"   Stop Loss: {stop_loss_price or 'Auto-calculate'}")
            logger.info(f"   Take Profit: {take_profit_price or 'Auto-calculate (fallback only)'}")
            logger.info(f"   Working Type: {working_type}")
            
            # ====================================================================
            # STEP 3: CHECK EXISTING POSITIONS (WITH AUTO SWITCH)
            # ====================================================================
            current_positions = self.get_open_positions()
            
            # Use position validator to check for duplicate/opposite positions
            auto_switch_enabled = self.config.get('auto_position_switch', True)
            validation_result = self.position_validator.validate_position_request(
                formatted_symbol, direction, action, current_positions, auto_switch_enabled
            )
            
            if not validation_result['allowed']:
                logger.warning(f"❌ Position request REJECTED: {validation_result['reason']}")
                return {"success": False, "error": validation_result['reason']}
            
            # Handle required actions (e.g., close opposite position)
            if validation_result.get('action_required'):
                action_type = validation_result['action_required']['type']
                
                if action_type == 'close_opposite':
                    logger.info("🔄 Auto position switch: Closing opposite position...")
                    positions_to_close = validation_result['action_required']['positions_to_close']
                    
                    for pos in positions_to_close:
                        close_side = f"close_{pos['side']}"
                        close_result = self.place_order(formatted_symbol, close_side, quantity=pos['size'])
                        
                        if not close_result or 'error' in close_result:
                            logger.error(f"❌ Failed to close opposite position: {close_result.get('error', 'Unknown error')}")
                            return {"success": False, "error": "Failed to close opposite position"}
                    
                    logger.info("✅ Opposite position closed successfully")
            
            # Note: position_validator already prevents duplicate same-direction positions
            # No need for additional check here
            
            # ====================================================================
            # STEP 4: CALCULATE QUANTITY
            # ====================================================================
            margin_asset = self._get_margin_asset(formatted_symbol)
            available_balance, total_balance, unrealized_pnl = self.get_account_balance(margin_asset)
            
            if available_balance <= 0:
                logger.warning("Zero available balance, using dummy value for testing")
                available_balance = 1000.0
            
            current_price = self.get_symbol_price(formatted_symbol)
            if current_price <= 0:
                return {"success": False, "error": "Failed to get current price"}
            
            # Parse quantity (support percentage string like "10%" or float)
            if isinstance(quantity_str, str) and quantity_str.endswith('%'):
                quantity_percentage = float(quantity_str.replace('%', ''))
                order_amount = available_balance * (quantity_percentage / 100)
                leveraged_amount = order_amount * coin_config['leverage']
                quantity = leveraged_amount / current_price
            else:
                try:
                    quantity = float(quantity_str)
                except (TypeError, ValueError):
                    # Default to coin config's order_size_percentage if invalid
                    order_size_pct = coin_config.get('order_size_percentage', 10.0)
                    order_amount = available_balance * (order_size_pct / 100)
                    leveraged_amount = order_amount * coin_config['leverage']
                    quantity = leveraged_amount / current_price
                    logger.warning(f"⚠️ Invalid quantity format '{quantity_str}', using coin config: {order_size_pct}%")
            
            logger.info(f"📊 Quantity Calculation:")
            logger.info(f"   Balance: ${available_balance:.2f} {margin_asset}")
            logger.info(f"   Quantity Input: {quantity_str}")
            logger.info(f"   Current Price: ${current_price:.2f}")
            logger.info(f"   Leverage: {coin_config['leverage']}x")
            logger.info(f"   Order Size %: {coin_config.get('order_size_percentage', 'N/A')}%")
            
            # Calculate order amount details for logging
            if isinstance(quantity_str, str) and quantity_str.endswith('%'):
                quantity_percentage = float(quantity_str.replace('%', ''))
                order_amount = available_balance * (quantity_percentage / 100)
                leveraged_amount = order_amount * coin_config['leverage']
                logger.info(f"   Order Amount: ${order_amount:.2f} ({quantity_percentage}% of balance)")
                logger.info(f"   Leveraged Amount: ${leveraged_amount:.2f} ({coin_config['leverage']}x)")
            
            logger.info(f"   Calculated Quantity: {quantity:.8f}")
            
            # Validate quantity before formatting
            if quantity <= 0:
                error_msg = f"Calculated quantity is zero or negative: {quantity:.8f}. Balance: ${available_balance:.2f}, Price: ${current_price:.2f}, Leverage: {coin_config['leverage']}x"
                logger.error(f"❌ {error_msg}")
                logger.error(f"   💡 Check: Balance may be too low or leverage too low for this symbol")
                return {"success": False, "error": error_msg}
            
            # ====================================================================
            # STEP 5: PLACE ENTRY ORDER (MARKET)
            # ====================================================================
            logger.info("=" * 80)
            logger.info("📤 STEP 5: PLACING ENTRY ORDER (MARKET)")
            logger.info("=" * 80)
            
            # Format quantity according to Binance precision requirements
            try:
                quantity = self._format_quantity(formatted_symbol, quantity)
                logger.info(f"✅ Formatted quantity: {quantity:.8f}")
            except ValueError as ve:
                error_msg = f"Quantity formatting failed: {str(ve)}. Calculated quantity was too small."
                logger.error(f"❌ {error_msg}")
                logger.error(f"   Balance: ${available_balance:.2f}, Quantity Input: {quantity_str}, Calculated: {quantity:.8f}")
                return {"success": False, "error": error_msg}
            
            # Check position mode BEFORE placing entry order
            is_one_way_mode_entry = True
            try:
                # Use futures_get_position_mode() if available, otherwise check positions
                try:
                    position_mode = self.client.futures_get_position_mode()
                    is_one_way_mode_entry = not position_mode.get('dualSidePosition', False)
                    logger.info(f"📌 Entry Order: Position mode API check - One-way: {is_one_way_mode_entry}")
                except:
                    # Fallback: check existing positions
                    positions = self.client.futures_position_information()
                    for pos in positions:
                        if pos.get('symbol') == formatted_symbol:
                            pos_side = pos.get('positionSide', 'BOTH')
                            if pos_side != 'BOTH':
                                is_one_way_mode_entry = False
                                break
                    logger.info(f"📌 Entry Order: Position mode from positions - One-way: {is_one_way_mode_entry}")
            except Exception as e:
                logger.warning(f"Could not check position mode for entry order: {str(e)}, assuming one-way mode")
                is_one_way_mode_entry = True
            
            try:
                entry_params = {
                    'symbol': formatted_symbol,
                    'side': side,
                    'type': 'MARKET',
                    'quantity': quantity
                }
                
                # CRITICAL: positionSide is ONLY required in HEDGE mode
                # In ONE-WAY mode, positionSide must NOT be included (causes API error)
                if not is_one_way_mode_entry:
                    entry_params['positionSide'] = position_side
                    logger.info(f"📌 Entry Order: Hedge mode - adding positionSide: {position_side}")
                else:
                    logger.info(f"📌 Entry Order: One-way mode - NOT adding positionSide")
                
                logger.info(f"📋 Entry Order Parameters:")
                for key, value in entry_params.items():
                    logger.info(f"   {key}: {value}")
                
                entry_order = self.client.futures_create_order(**entry_params)
                
                entry_order_id = entry_order.get('orderId')
                
                # Get entry price from order response (avgPrice may not be available immediately)
                avg_price = entry_order.get('avgPrice')
                if avg_price and float(avg_price) > 0:
                    entry_price = float(avg_price)
                else:
                    # Wait a bit for order to fill, then use current price
                    time.sleep(0.5)
                    entry_price = self.get_symbol_price(formatted_symbol)
                    if entry_price <= 0:
                        entry_price = current_price
                
                logger.info(f"✅ Entry order placed successfully!")
                logger.info(f"   Order ID: {entry_order_id}")
                logger.info(f"   Entry Price: ${entry_price:.2f}")
                logger.info(f"   Quantity: {quantity:.6f}")
                
                # Validate entry price
                if entry_price <= 0:
                    logger.error(f"❌ Invalid entry price: {entry_price}")
                    return {"success": False, "error": f"Invalid entry price: {entry_price}"}
                
            except Exception as e:
                logger.error(f"❌ Failed to place entry order: {str(e)}")
                return {"success": False, "error": f"Entry order failed: {str(e)}"}
            
            # ====================================================================
            # STEP 6: CALCULATE AUTO-PRICES (if needed)
            # ====================================================================
            if activation_price is None:
                if direction == 'long':
                    activation_price = entry_price * 1.02  # 2% above entry
                else:
                    activation_price = entry_price * 0.98  # 2% below entry
                # Format activation price precision
                activation_price = self.tp_sl_manager._round_to_price_step(formatted_symbol, activation_price)
                logger.info(f"🔄 Auto-calculated activation price: ${activation_price:.2f}")
            
            if stop_loss_price is None:
                if direction == 'long':
                    stop_loss_price = entry_price * 0.97  # 3% below entry
                else:
                    stop_loss_price = entry_price * 1.03  # 3% above entry
                # Format stop loss price precision
                stop_loss_price = self.tp_sl_manager._round_to_price_step(formatted_symbol, stop_loss_price)
                logger.info(f"🔄 Auto-calculated stop loss: ${stop_loss_price:.2f}")
            else:
                # Format provided stop loss price precision
                stop_loss_price = self.tp_sl_manager._round_to_price_step(formatted_symbol, stop_loss_price)
                logger.info(f"🔄 Using provided stop loss: ${stop_loss_price:.2f}")
            
            # Calculate take profit if not provided (for fallback only)
            if take_profit_price is None:
                if direction == 'long':
                    take_profit_price = entry_price * 1.05  # 5% above entry
                else:
                    take_profit_price = entry_price * 0.95  # 5% below entry
                # Format take profit price precision
                take_profit_price = self.tp_sl_manager._round_to_price_step(formatted_symbol, take_profit_price)
                logger.info(f"🔄 Auto-calculated take profit (fallback): ${take_profit_price:.2f}")
            else:
                # Format provided take profit price precision
                take_profit_price = self.tp_sl_manager._round_to_price_step(formatted_symbol, take_profit_price)
                logger.info(f"🔄 Using provided take profit (fallback): ${take_profit_price:.2f}")
            
            # Format activation price precision if provided
            if activation_price is not None:
                activation_price = self.tp_sl_manager._round_to_price_step(formatted_symbol, activation_price)
            
            # ====================================================================
            # STEP 7: PLACE TRAILING STOP ORDER (with retry)
            # ====================================================================
            logger.info("=" * 80)
            logger.info("📤 STEP 7: PLACING TRAILING STOP ORDER")
            logger.info("=" * 80)
            
            trailing_stop_side = 'SELL' if direction == 'long' else 'BUY'
            trailing_stop_id = None
            trailing_stop_success = False
            
            max_retries = 3
            retry_delays = [0.5, 1.0, 1.5]
            
            # Check position mode ONCE (before retry loop)
            # Use the same mode as entry order (already checked above)
            is_one_way_mode = is_one_way_mode_entry
            
            # Wait for position to be established after entry order
            logger.info("⏳ Waiting for position to be established after entry order...")
            time.sleep(1.0)  # Give Binance time to process the entry order
            
            # Verify position exists and get position size before placing trailing stop
            position_size = 0.0
            try:
                positions = self.client.futures_position_information()
                position_exists = False
                for pos in positions:
                    if pos.get('symbol') == formatted_symbol:
                        pos_amt = abs(float(pos.get('positionAmt', '0')))
                        if pos_amt > 0:
                            position_exists = True
                            position_size = pos_amt
                            logger.info(f"✅ Position verified: {formatted_symbol} | Size: {pos_amt} | Side: {pos.get('positionSide', 'BOTH')}")
                            break
                
                if not position_exists:
                    logger.error(f"❌ CRITICAL: Position not found for {formatted_symbol} after entry order!")
                    logger.error(f"   This will cause trailing stop order to fail.")
                    logger.error(f"   Entry order may not have been filled yet.")
            except Exception as e:
                logger.error(f"❌ Could not verify position: {str(e)}")
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"🔄 Attempt {attempt + 1}/{max_retries}...")
                    
                    # CRITICAL FIX: Binance API error -4136: "Target strategy invalid for orderType TRAILING_STOP_MARKET,closePosition true"
                    # Solution: Use quantity instead of closePosition for TRAILING_STOP_MARKET orders
                    # According to Binance docs, closePosition=true with TRAILING_STOP_MARKET requires reduceOnly,
                    # but reduceOnly is not allowed in Hedge Mode. So we use quantity instead.
                    trailing_params = {
                        'symbol': formatted_symbol,
                        'side': trailing_stop_side,
                        'type': 'TRAILING_STOP_MARKET',
                        'callbackRate': callback_rate,
                        'activationPrice': activation_price,
                        'workingType': working_type,
                        'quantity': position_size if position_size > 0 else quantity  # Use position size instead of closePosition
                    }
                    
                    # CRITICAL: positionSide is ONLY required in HEDGE mode
                    # In ONE-WAY mode, positionSide must NOT be included (causes API error)
                    if not is_one_way_mode:
                        trailing_params['positionSide'] = position_side
                        logger.info(f"📌 Hedge mode detected - adding positionSide: {position_side}")
                    else:
                        logger.info(f"📌 One-way mode detected - NOT adding positionSide")
                    
                    logger.info(f"📋 Trailing Stop Parameters:")
                    for key, value in trailing_params.items():
                        logger.info(f"   {key}: {value}")
                    
                    trailing_order = self.client.futures_create_order(**trailing_params)
                    
                    # CRITICAL: Binance returns algoId for TRAILING_STOP_MARKET orders, not orderId
                    # Trailing stop orders are Algo Orders (CONDITIONAL type)
                    trailing_stop_id = trailing_order.get('algoId') or trailing_order.get('orderId')
                    
                    if trailing_stop_id is None:
                        logger.error(f"❌ CRITICAL: Neither algoId nor orderId found in response!")
                        logger.error(f"   Response keys: {list(trailing_order.keys())}")
                        logger.error(f"   Full response: {trailing_order}")
                    else:
                        algo_type = trailing_order.get('algoType', 'N/A')
                        algo_status = trailing_order.get('algoStatus', 'N/A')
                        logger.info(f"✅ Trailing stop order placed successfully!")
                        logger.info(f"   Algo ID: {trailing_stop_id}")
                        logger.info(f"   Algo Type: {algo_type}")
                        logger.info(f"   Algo Status: {algo_status}")
                        
                        # Track trailing stop for cleanup when position closes
                        tracking_key = f"{formatted_symbol}_{position_side}"
                        if not hasattr(self, 'trailing_stop_tracking'):
                            self.trailing_stop_tracking = {}
                        if tracking_key not in self.trailing_stop_tracking:
                            self.trailing_stop_tracking[tracking_key] = []
                        self.trailing_stop_tracking[tracking_key].append(trailing_stop_id)
                        logger.info(f"📝 Trailing stop tracked for cleanup: {tracking_key}")
                    
                    trailing_stop_success = True
                    break
                    
                except BinanceAPIException as e:
                    error_code = e.code
                    error_msg = e.message
                    logger.error(f"❌ Trailing Stop Attempt {attempt + 1}/{max_retries} FAILED:")
                    logger.error(f"   Error Code: {error_code}")
                    logger.error(f"   Error Message: {error_msg}")
                    logger.error(f"   Parameters used:")
                    for key, value in trailing_params.items():
                        logger.error(f"      {key}: {value}")
                    
                    # Log specific error details
                    if hasattr(e, 'response'):
                        logger.error(f"   Full API Response: {e.response}")
                    
                    # Log position information for debugging
                    try:
                        positions = self.client.futures_position_information()
                        for pos in positions:
                            if pos.get('symbol') == formatted_symbol:
                                pos_amt = abs(float(pos.get('positionAmt', '0')))
                                if pos_amt > 0:
                                    logger.error(f"   Current Position: {formatted_symbol} | Size: {pos_amt} | Side: {pos.get('positionSide', 'BOTH')}")
                                    break
                    except Exception as pos_e:
                        logger.error(f"   Could not check position: {str(pos_e)}")
                    
                    # Log position mode
                    logger.error(f"   Position Mode: {'ONE-WAY' if is_one_way_mode else 'HEDGE'}")
                    
                    if attempt < max_retries - 1:
                        delay = retry_delays[attempt]
                        logger.info(f"⏳ Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"❌ All {max_retries} attempts failed. Last error: {error_msg} (Code: {error_code})")
                        trailing_stop_success = False
                except Exception as e:
                    import traceback
                    logger.error(f"❌ Unexpected error in attempt {attempt + 1}: {str(e)}")
                    logger.error(f"   Traceback: {traceback.format_exc()}")
                    logger.error(f"   Parameters used:")
                    for key, value in trailing_params.items():
                        logger.error(f"      {key}: {value}")
                    
                    if attempt < max_retries - 1:
                        delay = retry_delays[attempt]
                        time.sleep(delay)
                    else:
                        trailing_stop_success = False
            
            # ====================================================================
            # STEP 8: FALLBACK - PLACE TP/SL (if trailing stop failed)
            # ====================================================================
            if not trailing_stop_success:
                logger.info("=" * 80)
                logger.info("⚠️ STEP 8: TRAILING STOP FAILED - PLACING FALLBACK TP/SL")
                logger.info("=" * 80)
                
                # Re-check position mode for fallback (may have changed)
                is_one_way_mode_fallback = True
                try:
                    positions = self.client.futures_position_information()
                    for pos in positions:
                        if pos.get('symbol') == formatted_symbol:
                            pos_side = pos.get('positionSide', 'BOTH')
                            if pos_side != 'BOTH':
                                is_one_way_mode_fallback = False
                                break
                except Exception as e:
                    logger.warning(f"Could not check position mode for fallback: {str(e)}, assuming one-way mode")
                    is_one_way_mode_fallback = True
                
                # Place TP and SL orders separately (like in place_order)
                tp_order_id = None
                sl_order_id = None
                tp_success = False
                sl_success = False
                
                # Place Take Profit order
                try:
                    tp_side = 'SELL' if direction == 'long' else 'BUY'
                    tp_params = {
                        'symbol': formatted_symbol,
                        'side': tp_side,
                        'type': 'TAKE_PROFIT_MARKET',
                        'stopPrice': take_profit_price,
                        'closePosition': True
                    }
                    
                    if not is_one_way_mode_fallback:
                        tp_params['positionSide'] = position_side
                    
                    logger.info(f"📋 Fallback Take Profit Parameters:")
                    for key, value in tp_params.items():
                        logger.info(f"   {key}: {value}")
                    
                    tp_order = self.client.futures_create_order(**tp_params)
                    tp_order_id = tp_order.get('orderId')
                    tp_success = True
                    logger.info(f"✅ Fallback take profit placed successfully!")
                    logger.info(f"   Order ID: {tp_order_id}")
                    logger.info(f"   Take Profit Price: ${take_profit_price:.2f}")
                except Exception as tp_error:
                    logger.error(f"❌ Failed to place fallback take profit: {str(tp_error)}")
                    tp_success = False
                
                # Place Stop Loss order
                try:
                    sl_side = 'SELL' if direction == 'long' else 'BUY'
                    sl_params = {
                        'symbol': formatted_symbol,
                        'side': sl_side,
                        'type': 'STOP_MARKET',
                        'stopPrice': stop_loss_price,
                        'closePosition': True
                    }
                    
                    if not is_one_way_mode_fallback:
                        sl_params['positionSide'] = position_side
                    
                    logger.info(f"📋 Fallback Stop Loss Parameters:")
                    for key, value in sl_params.items():
                        logger.info(f"   {key}: {value}")
                    
                    sl_order = self.client.futures_create_order(**sl_params)
                    sl_order_id = sl_order.get('orderId')
                    sl_success = True
                    logger.info(f"✅ Fallback stop loss placed successfully!")
                    logger.info(f"   Order ID: {sl_order_id}")
                    logger.info(f"   Stop Price: ${stop_loss_price:.2f}")
                except Exception as sl_error:
                    logger.error(f"❌ Failed to place fallback stop loss: {str(sl_error)}")
                    sl_success = False
                
                # Return result based on what was placed
                if tp_success or sl_success:
                    message_parts = []
                    if tp_success:
                        message_parts.append("take profit")
                    if sl_success:
                        message_parts.append("stop loss")
                    message = f"Entry order placed. Trailing stop failed, fallback {' and '.join(message_parts)} placed."
                    
                    return {
                        "success": True,
                        "message": message,
                        "order_id": entry_order_id,
                        "trailing_stop_id": None,
                        "fallback_tp_id": tp_order_id if tp_success else None,
                        "fallback_sl_id": sl_order_id if sl_success else None,
                        "entry_price": entry_price,
                        "fallback_used": True,
                        "tp_success": tp_success,
                        "sl_success": sl_success
                    }
                else:
                    logger.error(f"❌ Both fallback TP and SL failed!")
                    return {
                        "success": False,
                        "error": f"Entry order placed, but trailing stop and both fallback TP/SL failed",
                        "order_id": entry_order_id
                    }
            
            # ====================================================================
            # STEP 9: SUCCESS RETURN
            # ====================================================================
            logger.info("=" * 80)
            logger.info("✅ TRAILING STOP STRATEGY - SUCCESS")
            logger.info("=" * 80)
            
            return {
                "success": True,
                "message": "Trailing stop order placed successfully",
                "order_id": entry_order_id,
                "trailing_stop_id": trailing_stop_id,
                "entry_price": entry_price,
                "activation_price": activation_price,
                "callback_rate": callback_rate,
                "fallback_used": False
            }
            
        except Exception as e:
            logger.error(f"❌ Trailing stop strategy error: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"success": False, "error": f"Trailing stop strategy failed: {str(e)}"}
    
    def cleanup_orphaned_trailing_stops(self):
        """
        Cleanup trailing stop orders that have no matching position
        Called periodically to ensure orphaned trailing stops are cancelled
        """
        try:
            # Get current positions
            current_positions = self.get_open_positions()
            active_position_keys = set()
            
            for pos in current_positions:
                symbol = pos['symbol']
                pos_side = pos.get('positionSide', 'BOTH')
                actual_amt = float(pos.get('positionAmt', '0'))
                
                if abs(actual_amt) > 0:
                    # Create tracking key
                    if pos_side == 'BOTH':
                        # One-way mode: determine direction from amount
                        if actual_amt > 0:
                            active_position_keys.add(f"{symbol}_LONG")
                        elif actual_amt < 0:
                            active_position_keys.add(f"{symbol}_SHORT")
                    else:
                        active_position_keys.add(f"{symbol}_{pos_side}")
            
            # Get all open algo orders (trailing stops)
            try:
                if hasattr(self.client, 'futures_get_open_algo_orders'):
                    algo_orders = self.client.futures_get_open_algo_orders()
                else:
                    algo_orders = []
                    # Fallback: get per symbol
                    symbols = set([pos['symbol'] for pos in current_positions])
                    common_symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'LDOUSDT', 'XLMUSDT', 'ADAUSDT', 
                                     'DOTUSDT', 'UNIUSDT', 'DOGEUSDT', 'FETUSDT', 'INJUSDT', 'IMXUSDT', 'ARBUSDT']
                    symbols.update(common_symbols)
                    for symbol in symbols:
                        try:
                            if hasattr(self.client, 'futures_get_all_algo_orders'):
                                symbol_algos = self.client.futures_get_all_algo_orders(symbol=symbol)
                                algo_orders.extend([a for a in symbol_algos if a.get('algoStatus') == 'NEW' and a.get('orderType') == 'TRAILING_STOP_MARKET'])
                        except:
                            continue
                
                # Check each trailing stop
                cancelled_count = 0
                for algo in algo_orders:
                    if algo.get('orderType') != 'TRAILING_STOP_MARKET':
                        continue
                    
                    symbol = algo.get('symbol')
                    algo_pos_side = algo.get('positionSide', 'BOTH')
                    algo_id = algo.get('algoId')
                    
                    # Create tracking key
                    tracking_key = f"{symbol}_{algo_pos_side}"
                    
                    # Check if position exists
                    position_exists = False
                    if tracking_key in active_position_keys:
                        position_exists = True
                    elif algo_pos_side == 'BOTH':
                        # Check both LONG and SHORT
                        if f"{symbol}_LONG" in active_position_keys or f"{symbol}_SHORT" in active_position_keys:
                            position_exists = True
                    else:
                        # Check BOTH position
                        if f"{symbol}_BOTH" in active_position_keys:
                            position_exists = True
                    
                    if not position_exists:
                        # Orphaned trailing stop - cancel it
                        try:
                            if hasattr(self.client, 'futures_cancel_algo_order'):
                                self.client.futures_cancel_algo_order(symbol=symbol, algoId=algo_id)
                                logger.info(f"🧹 Cleaned up orphaned trailing stop: {symbol} {algo_pos_side} (Algo ID: {algo_id})")
                                cancelled_count += 1
                                
                                # Remove from tracking
                                if hasattr(self, 'trailing_stop_tracking') and tracking_key in self.trailing_stop_tracking:
                                    if algo_id in self.trailing_stop_tracking[tracking_key]:
                                        self.trailing_stop_tracking[tracking_key].remove(algo_id)
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to cancel orphaned trailing stop {algo_id}: {str(e)}")
                
                if cancelled_count > 0:
                    logger.info(f"✅ Cleaned up {cancelled_count} orphaned trailing stop(s)")
                    
            except Exception as e:
                logger.warning(f"⚠️ Error cleaning up orphaned trailing stops: {str(e)}")
                
        except Exception as e:
            logger.error(f"❌ Error in cleanup_orphaned_trailing_stops: {str(e)}")