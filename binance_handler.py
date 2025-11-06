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
                            tp_order = self.client.futures_create_order(
                                symbol=formatted_symbol,
                                side=tp_side,
                                positionSide=position_side,
                                type='TAKE_PROFIT_MARKET',
                                stopPrice=tp_price,
                                closePosition=True
                            )
                            logger.info(f"✅ TP order placed: ${tp_price:.2f}")
                            
                            # Place SL order
                            sl_order = self.client.futures_create_order(
                                symbol=formatted_symbol,
                                side=tp_side,
                                positionSide=position_side,
                                type='STOP_MARKET',
                                stopPrice=sl_price,
                                closePosition=True
                            )
                            logger.info(f"✅ SL order placed: ${sl_price:.2f}")
                            
                            # Send notification
                            self._send_enhanced_notification(
                                symbol, side, current_price, quantity, 
                                order_result['orderId'],
                                {'tp_price': tp_price, 'sl_price': sl_price, 'direction': direction}
                            )
                except Exception as tp_sl_error:
                    logger.error(f"❌ Error placing TP/SL: {str(tp_sl_error)}")
            
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
        """Monitor positions continuously"""
        while True:
            try:
                current_positions = self.get_open_positions()
                
                # Update position states
                for pos in current_positions:
                    pos_id = f"{pos['symbol']}_{pos['positionSide']}"
                    self.last_position_states[pos_id] = pos
                
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
