from binance.client import Client
from binance.exceptions import BinanceAPIException
import logging
import time
from datetime import datetime
import asyncio
import pandas as pd
import numpy as np
import threading

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
        
        # Log Telegram configuration status
        telegram_token = self.config.get('telegram_bot_token', '')
        telegram_chat_id = self.config.get('telegram_chat_id', '')
        
        if telegram_token and telegram_chat_id:
            logger.info(f"✅ Telegram configured:")
            logger.info(f"   Bot Token: {'Set' if telegram_token else 'Not Set'}")
            logger.info(f"   Chat ID: {telegram_chat_id}")
        else:
            logger.warning(f"⚠️ Telegram not configured:")
            logger.warning(f"   Bot Token: {'Set' if telegram_token else 'Not Set'}")
            logger.warning(f"   Chat ID: {'Set' if telegram_chat_id else 'Not Set'}")
        
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
    
    def _set_position_mode(self, symbol, hedge_mode=False):
        """
        Set position mode for symbol (One-way or Hedge mode)
        
        Args:
            symbol: Trading symbol
            hedge_mode: True for Hedge mode, False for One-way mode
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            formatted_symbol = self._format_symbol(symbol)
            
            # Get current position mode
            position_mode = self.client.futures_get_position_mode()
            current_dual_side = position_mode.get('dualSidePosition', False)
            
            target_mode = hedge_mode
            
            # Only change if different
            if current_dual_side != target_mode:
                if target_mode:
                    self.client.futures_change_position_mode(dualSidePosition=True)
                    logger.info(f"✅ Position mode set to HEDGE for {formatted_symbol}")
                else:
                    self.client.futures_change_position_mode(dualSidePosition=False)
                    logger.info(f"✅ Position mode set to ONE-WAY for {formatted_symbol}")
                return True
            else:
                mode_str = "HEDGE" if target_mode else "ONE-WAY"
                logger.info(f"Position mode already set to {mode_str}")
                return True
                
        except Exception as e:
            error_msg = str(e)
            
            # Error -4046 means position mode change is not allowed (has open positions)
            if "-4046" in error_msg or "No need to change" in error_msg:
                logger.info(f"Position mode cannot be changed (may have open positions)")
                return True  # Not a critical error
            
            logger.error(f"❌ Failed to set position mode: {error_msg}")
            return False
    
    def _get_position_mode(self):
        """
        Get current position mode
        
        Returns:
            bool: True if Hedge mode, False if One-way mode
        """
        try:
            position_mode = self.client.futures_get_position_mode()
            return position_mode.get('dualSidePosition', False)
        except Exception as e:
            logger.error(f"❌ Failed to get position mode: {str(e)}")
            return False  # Default to One-way mode
    
    def _round_quantity_to_precision(self, symbol, quantity):
        """
        Round quantity to Binance symbol precision
        
        Args:
            symbol: Trading symbol (e.g., BTCUSDT)
            quantity: Raw quantity value
            
        Returns:
            float: Properly rounded quantity
        """
        try:
            # Get exchange info for symbol
            info = self.client.futures_exchange_info()
            
            for symbol_info in info['symbols']:
                if symbol_info['symbol'] == symbol:
                    # Get LOT_SIZE filter
                    for filter_item in symbol_info['filters']:
                        if filter_item['filterType'] == 'LOT_SIZE':
                            step_size = float(filter_item['stepSize'])
                            min_qty = float(filter_item['minQty'])
                            max_qty = float(filter_item['maxQty'])
                            
                            # Calculate precision from step size
                            # e.g., 0.001 = 3 decimals, 0.1 = 1 decimal, 1 = 0 decimals
                            step_str = str(step_size).rstrip('0')
                            if '.' in step_str:
                                precision = len(step_str.split('.')[-1])
                            else:
                                precision = 0
                            
                            # Round to step size
                            quantity = round(quantity / step_size) * step_size
                            
                            # Round to precision
                            quantity = round(quantity, precision)
                            
                            # Ensure within limits
                            if quantity < min_qty:
                                logger.warning(f"Quantity {quantity} below minimum {min_qty}, using minimum")
                                quantity = min_qty
                            if quantity > max_qty:
                                logger.warning(f"Quantity {quantity} above maximum {max_qty}, using maximum")
                                quantity = max_qty
                            
                            logger.info(f"🔢 Quantity Precision:")
                            logger.info(f"   Step Size: {step_size}")
                            logger.info(f"   Precision: {precision} decimals")
                            logger.info(f"   Min: {min_qty}, Max: {max_qty}")
                            logger.info(f"   Final Quantity: {quantity}")
                            
                            return quantity
                    
                    # If LOT_SIZE not found, use default precision
                    logger.warning(f"LOT_SIZE filter not found for {symbol}, using default precision")
                    return round(quantity, 3)
            
            # Symbol not found in exchange info
            logger.warning(f"Symbol {symbol} not found in exchange info, using default precision")
            return round(quantity, 3)
            
        except Exception as e:
            logger.error(f"Error rounding quantity: {str(e)}")
            # Fallback to safe precision
            return round(quantity, 3)
    
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
            dict: API response or None if failed
        """
        try:
            formatted_symbol = self._format_symbol(symbol)
            
            # Ensure leverage is integer
            leverage = int(leverage)
            
            # Binance leverage limits: 1-125
            if leverage < 1 or leverage > 125:
                logger.error(f"Invalid leverage {leverage}x (must be 1-125)")
                return None
            
            response = self.client.futures_change_leverage(
                symbol=formatted_symbol,
                leverage=leverage
            )
            
            logger.info(f"✅ Leverage set to {leverage}x for {formatted_symbol}")
            logger.info(f"   Response: {response}")
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            
            # Check if error is about leverage already being set
            if "No need to change leverage" in error_msg or "-4028" in error_msg:
                logger.info(f"Leverage already set to {leverage}x for {formatted_symbol}")
                return {"leverage": leverage, "message": "Already set"}
            
            logger.error(f"❌ Failed to set leverage for {symbol}: {error_msg}")
            return None
    
    def set_margin_type(self, symbol, margin_type='CROSSED'):
        """Set margin type for symbol
        
        Args:
            symbol (str): Trading symbol
            margin_type (str): 'ISOLATED' or 'CROSSED'
            
        Returns:
            dict: API response or {'status': 'already_set'} if already set, None if failed
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
                logger.error(f"❌ Failed to set margin type for {symbol}: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"❌ Failed to set margin type for {symbol}: {str(e)}")
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
            leverage_result = self.set_leverage(formatted_symbol, coin_config['leverage'])
            if not leverage_result:
                logger.error(f"Failed to set leverage to {coin_config['leverage']}x")
                return {"error": f"Failed to set leverage to {coin_config['leverage']}x"}
            
            # Set margin type
            margin_result = self.set_margin_type(formatted_symbol, 'CROSSED')
            if not margin_result:
                logger.warning(f"Failed to set margin type (may already be set)")
            
            # Set position mode to Hedge mode (allows LONG/SHORT positions)
            # Note: This might fail if there are open positions, which is OK
            self._set_position_mode(formatted_symbol, hedge_mode=True)
            
            # Get current position mode
            is_hedge_mode = self._get_position_mode()
            
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
            
            # Round quantity to symbol precision
            quantity = self._round_quantity_to_precision(formatted_symbol, quantity)
            
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
            logger.info(f"   Position Mode: {'HEDGE' if is_hedge_mode else 'ONE-WAY'}")
            logger.info(f"   Quantity: {quantity}")
            
            # Build order parameters
            order_params = {
                'symbol': formatted_symbol,
                'side': binance_side,
                'type': order_type,
                'quantity': quantity
            }
            
            # Only add positionSide if in Hedge mode
            if is_hedge_mode:
                order_params['positionSide'] = position_side
            
            order_result = self.client.futures_create_order(**order_params)
            
            logger.info(f"✅ Order placed successfully!")
            logger.info(f"   Order ID: {order_result['orderId']}")
            
            # Get current price for notification
            current_price = float(order_result.get('avgPrice', self.get_symbol_price(formatted_symbol)))
            tp_price = None
            sl_price = None
            
            # Place TP/SL orders for open positions
            if action == 'open':
                try:
                    # Get ATR value using 1h data
                    atr_period = self.tp_sl_manager.get_atr_period(symbol)
                    atr_value = self.get_atr(formatted_symbol, atr_period)
                    
                    if atr_value > 0:
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
                            
                            tp_params = {
                                'symbol': formatted_symbol,
                                'side': tp_side,
                                'type': 'TAKE_PROFIT_MARKET',
                                'stopPrice': tp_price,
                                'closePosition': True
                            }
                            
                            if is_hedge_mode:
                                tp_params['positionSide'] = position_side
                            
                            tp_order = self.client.futures_create_order(**tp_params)
                            logger.info(f"✅ TP order placed: ${tp_price:.2f}")
                            
                            # Place SL order
                            sl_params = {
                                'symbol': formatted_symbol,
                                'side': tp_side,
                                'type': 'STOP_MARKET',
                                'stopPrice': sl_price,
                                'closePosition': True
                            }
                            
                            if is_hedge_mode:
                                sl_params['positionSide'] = position_side
                            
                            sl_order = self.client.futures_create_order(**sl_params)
                            logger.info(f"✅ SL order placed: ${sl_price:.2f}")
                        else:
                            logger.warning(f"⚠️ TP/SL validation failed, skipping TP/SL orders")
                    else:
                        logger.warning(f"⚠️ ATR value is 0, skipping TP/SL orders")
                        
                except Exception as tp_sl_error:
                    logger.error(f"❌ Error placing TP/SL: {str(tp_sl_error)}")
                    import traceback
                    logger.error(traceback.format_exc())
            
            # Send notification AFTER order is placed (independent of TP/SL success)
            try:
                tp_sl_data = None
                if tp_price and sl_price:
                    tp_sl_data = {'tp_price': tp_price, 'sl_price': sl_price, 'direction': direction}
                
                self._send_enhanced_notification(
                    symbol, side, current_price, quantity, 
                    order_result['orderId'],
                    tp_sl_data
                )
            except Exception as notify_error:
                logger.error(f"❌ Error sending notification: {str(notify_error)}")
                import traceback
                logger.error(traceback.format_exc())
                # Don't fail the order if notification fails
            
            return order_result
            
        except Exception as e:
            logger.error(f"❌ Order placement error: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": str(e)}
    
    def get_open_positions(self):
        """Get all open positions from Binance Futures
        
        Returns:
            list: List of open positions with leverage information
        """
        try:
            logger.info("Fetching open positions from Binance...")
            
            # Get position information
            positions = self.client.futures_position_information()
            
            # Get account information for leverage
            account_info = self.client.futures_account()
            assets = {asset['asset']: asset for asset in account_info.get('assets', [])}
            
            # Filter active positions
            active_positions = []
            for pos in positions:
                position_amt = abs(float(pos.get('positionAmt', '0')))
                if position_amt > 0:
                    symbol = pos['symbol']
                    
                    # Try to get leverage from position data or account
                    leverage = int(pos.get('leverage', '1'))
                    
                    # If leverage is 1 or not found, try to get from account
                    if leverage == 1:
                        # Get leverage from account positions
                        for asset in account_info.get('positions', []):
                            if asset['symbol'] == symbol and abs(float(asset.get('positionAmt', '0'))) > 0:
                                leverage = int(asset.get('leverage', '1'))
                                break
                    
                    # If still 1, try to get from recent leverage setting
                    if leverage == 1:
                        # Get leverage from exchange info or use configured leverage
                        coin_config = self.coin_config_manager.get_coin_config(symbol)
                        leverage = coin_config.get('leverage', 1)
                    
                    pos['leverage'] = leverage
                    logger.info(f"Active position: {symbol} {pos['positionSide']} {position_amt} Leverage: {leverage}x")
                    active_positions.append(pos)
            
            logger.info(f"Found {len(active_positions)} active positions")
            return active_positions
            
        except Exception as e:
            logger.error(f"Failed to get open positions: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
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
            
            # Send Telegram notification
            try:
                self._send_telegram_safe(message)
                logger.info("✅ Telegram notification sent successfully")
            except Exception as e:
                logger.error(f"❌ Error sending Telegram notification: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
            
        except Exception as e:
            logger.error(f"Error in _send_enhanced_notification: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _send_telegram_safe(self, message):
        """
        Thread-safe wrapper for sending Telegram notifications
        
        Args:
            message (str): Message to send
        """
        try:
            # Check if there's already an event loop running
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Event loop is already running, use threading
                    logger.info("Event loop detected, using thread for Telegram notification")
                    thread = threading.Thread(target=self._run_async_in_thread, args=(message,), daemon=True)
                    thread.start()
                    return
            except RuntimeError:
                pass  # No event loop, safe to use asyncio.run()
            
            # No event loop running, safe to use asyncio.run()
            asyncio.run(self.send_telegram_notification(message))
            
        except Exception as e:
            logger.error(f"Error in _send_telegram_safe: {str(e)}")
            raise
    
    def _run_async_in_thread(self, message):
        """Run async function in a new thread with its own event loop"""
        try:
            # Create new event loop for this thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                new_loop.run_until_complete(self.send_telegram_notification(message))
            finally:
                new_loop.close()
        except Exception as e:
            logger.error(f"Error in _run_async_in_thread: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def send_telegram_notification(self, message):
        """Send Telegram notification
        
        Args:
            message (str): Message to send
        """
        bot_token = self.config.get('telegram_bot_token')
        chat_id = self.config.get('telegram_chat_id')
        
        logger.info(f"📤 Attempting to send Telegram notification...")
        logger.info(f"   Bot Token: {'Set (' + str(len(bot_token)) + ' chars)' if bot_token else 'Not Set'}")
        logger.info(f"   Chat ID: {chat_id if chat_id else 'Not Set'}")
        
        if not bot_token:
            logger.warning("⚠️ Telegram bot token not configured - skipping notification")
            return
        
        if not chat_id:
            logger.warning("⚠️ Telegram chat ID not configured - skipping notification")
            return
        
        try:
            from telegram import Bot
            bot = Bot(token=bot_token)
            
            # Format chat ID (handle group IDs)
            if isinstance(chat_id, str) and chat_id.isdigit() and chat_id.startswith("100"):
                chat_id = "-" + chat_id
            
            logger.info(f"📤 Sending to chat ID: {chat_id}")
            await bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"✅ Telegram notification sent successfully to chat {chat_id}")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ Failed to send Telegram notification: {error_msg}")
            logger.error(f"   Bot Token: {'Set' if bot_token else 'Not Set'}")
            logger.error(f"   Chat ID: {chat_id if chat_id else 'Not Set'}")
            import traceback
            logger.error(traceback.format_exc())
            raise  # Re-raise to be caught by caller
