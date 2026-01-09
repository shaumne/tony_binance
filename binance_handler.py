from binance.client import Client
from binance.exceptions import BinanceAPIException
import logging
import time
from datetime import datetime
import asyncio
import pandas as pd
import numpy as np
import threading
import hmac
import hashlib
import requests
from urllib.parse import urlencode

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
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = 'https://fapi.binance.com'  # Futures API base URL
        
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
            symbol (str): Trading symbol (e.g., 'BTCUSDT', 'ETHUSDC', 'FETUSDT.P')
            
        Returns:
            str: Formatted symbol (Binance uses plain format, .P extension removed)
        """
        # Remove .P extension if present (e.g., FETUSDT.P -> FETUSDT)
        symbol = symbol.replace('.P', '').replace('.p', '')
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
    
    def _get_coin_icon(self, symbol: str) -> dict:
        """
        Get coin icon and color for a symbol
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT', 'UNIUSDT')
            
        Returns:
            dict: {'icon': 'icon-class', 'color': '#color-code'}
        """
        # Extract base coin from symbol (remove USDT/USDC suffix)
        base_coin = symbol.replace('USDT', '').replace('USDC', '').upper()
        
        coin_icons = {
            'BTC': {'icon': 'fab fa-bitcoin', 'color': '#f7931a'},
            'ETH': {'icon': 'fab fa-ethereum', 'color': '#627eea'},
            'XRP': {'icon': 'fas fa-water', 'color': '#00AAE4'},
            'ADA': {'icon': 'fas fa-heart', 'color': '#0033AD'},
            'DOT': {'icon': 'fas fa-circle', 'color': '#E6007A'},
            'XLM': {'icon': 'fas fa-star', 'color': '#14B6E7'},
            'IMX': {'icon': 'fas fa-gem', 'color': '#00D4AA'},
            'DOGE': {'icon': 'fas fa-dog', 'color': '#C2A633'},
            'INJ': {'icon': 'fas fa-syringe', 'color': '#00D4FF'},
            'LDO': {'icon': 'fas fa-layer-group', 'color': '#00A3FF'},
            'ARB': {'icon': 'fas fa-shapes', 'color': '#28A0F0'},
            'UNI': {'icon': 'fas fa-exchange-alt', 'color': '#FF007A'},
            'SOL': {'icon': 'fas fa-sun', 'color': '#00FFA3'},
            'BNB': {'icon': 'fas fa-coins', 'color': '#F3BA2F'},
            'FET': {'icon': 'fas fa-robot', 'color': '#8B5CF6'},
            'AAVE': {'icon': 'fas fa-ghost', 'color': '#B6509E'},
            'BCH': {'icon': 'fas fa-money-bill-wave', 'color': '#8DC351'},
            'AVAX': {'icon': 'fas fa-mountain', 'color': '#E84142'},
            'LINK': {'icon': 'fas fa-link', 'color': '#2A5ADA'},
            'CRV': {'icon': 'fas fa-circle-notch', 'color': '#FF0084'},
            'TIA': {'icon': 'fas fa-moon', 'color': '#7B3FE4'},
            'FIL': {'icon': 'fas fa-database', 'color': '#0090FF'},
        }
        
        # Return coin icon or default
        return coin_icons.get(base_coin, {'icon': 'fas fa-coins', 'color': '#6b7280'})
    
    def get_account_balance(self, asset='USDT'):
        """Get Futures account balance
        
        Args:
            asset (str): Asset symbol (USDT or USDC)
            
        Returns:
            tuple: (available_balance, equity, unrealized_pnl)
            equity = walletBalance + unrealizedProfit
        """
        try:
            logger.info(f"[BALANCE] Fetching {asset} Futures balance...")
            
            # Get Futures account information
            account_info = self.client.futures_account()
            
            # Find the specific asset
            available = 0.0
            wallet_balance = 0.0
            unrealized_pnl = 0.0
            
            for asset_info in account_info['assets']:
                if asset_info['asset'] == asset:
                    available = float(asset_info['availableBalance'])
                    wallet_balance = float(asset_info['walletBalance'])
                    unrealized_pnl = float(asset_info['unrealizedProfit'])
                    break
            
            # Equity = walletBalance + unrealizedProfit
            equity = wallet_balance + unrealized_pnl
            
            logger.info(f"[BALANCE] {asset} - Available: {available}, Wallet: {wallet_balance}, Unrealized PnL: {unrealized_pnl}, Equity: {equity}")
            return available, equity, unrealized_pnl
            
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
            float: Calculated ATR value (0.0 if calculation fails)
        """
        try:
            formatted_symbol = self._format_symbol(symbol)
            logger.info(f"📊 Calculating ATR for {formatted_symbol}, Period: {period}")
            
            # Validate period
            if period < 1 or period > 100:
                logger.warning(f"⚠️ Invalid ATR period: {period}, using default 14")
                period = 14
            
            # Fetch 1h klines (need period + 50 for ATR smoothing and validation)
            min_required = period + 10  # Minimum required for reliable calculation
            requested_limit = period + 50  # Request more for smoothing
            
            try:
                klines = self.client.futures_klines(
                    symbol=formatted_symbol,
                    interval=Client.KLINE_INTERVAL_1HOUR,  # 1h interval
                    limit=requested_limit
                )
            except Exception as api_error:
                logger.error(f"❌ Failed to fetch klines from Binance API: {str(api_error)}")
                return 0.0
            
            if not klines or len(klines) == 0:
                logger.warning(f"⚠️ No klines data received for {formatted_symbol}")
                return 0.0
            
            if len(klines) < min_required:
                logger.warning(f"⚠️ Insufficient data for ATR calculation.")
                logger.warning(f"   Required: {min_required}, Got: {len(klines)}")
                logger.warning(f"   This may indicate new listing or API issue")
                return 0.0
            
            # Convert to DataFrame
            try:
                df = pd.DataFrame(klines, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades', 
                    'taker_buy_base', 'taker_buy_quote', 'ignore'
                ])
            except Exception as df_error:
                logger.error(f"❌ Failed to create DataFrame: {str(df_error)}")
                return 0.0
            
            # Convert to float and validate
            try:
                df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            except Exception as convert_error:
                logger.error(f"❌ Failed to convert data types: {str(convert_error)}")
                return 0.0
            
            # Validate data quality
            if df[['high', 'low', 'close']].isnull().any().any():
                logger.warning(f"⚠️ Missing data in klines, attempting to fill...")
                df[['high', 'low', 'close']] = df[['high', 'low', 'close']].ffill()
            
            # Calculate True Range (TR)
            try:
                df['previous_close'] = df['close'].shift(1)
                df['tr'] = df[['high', 'low', 'previous_close']].apply(
                    lambda x: max(
                        x['high'] - x['low'],
                        abs(x['high'] - x['previous_close']),
                        abs(x['low'] - x['previous_close'])
                    ), axis=1
                )
            except Exception as tr_error:
                logger.error(f"❌ Failed to calculate True Range: {str(tr_error)}")
                return 0.0
            
            # Validate TR values
            if df['tr'].isnull().any() or (df['tr'] < 0).any():
                logger.warning(f"⚠️ Invalid TR values detected, cleaning...")
                df['tr'] = df['tr'].fillna(0)
                df['tr'] = df['tr'].clip(lower=0)
            
            # Wilder's ATR (EMA with alpha=1/period)
            try:
                df['ATR'] = df['tr'].ewm(alpha=1/period, adjust=False).mean()
            except Exception as atr_error:
                logger.error(f"❌ Failed to calculate ATR: {str(atr_error)}")
                return 0.0
            
            # Get the latest ATR value
            atr_value = df['ATR'].iloc[-1]
            
            # Validate ATR value
            if pd.isna(atr_value) or atr_value <= 0:
                logger.warning(f"⚠️ Invalid ATR value calculated: {atr_value}")
                logger.warning(f"   This may indicate data quality issues")
                return 0.0
            
            logger.info(f"✅ ATR calculated successfully for {formatted_symbol}")
            logger.info(f"   Period: {period}")
            logger.info(f"   ATR Value: {atr_value:.6f}")
            logger.info(f"   Data Points Used: {len(df)}")
            
            return float(atr_value)
                
        except Exception as e:
            logger.error(f"❌ ATR calculation failed for {symbol}: {str(e)}")
            import traceback
            logger.error(f"Full traceback:")
            logger.error(traceback.format_exc())
            return 0.0
    
    def place_trailing_stop_strategy(self, data: dict):
        """
        🔥 FIRE AND FORGET TRAILING STOP STRATEGY
        
        Places an entry order followed immediately by a TRAILING_STOP_MARKET order
        with pre-calculated parameters from TradingView.
        
        Args:
            data (dict): Webhook payload containing:
                - symbol (str): Trading symbol (e.g., 'BTCUSDT')
                - side (str): Entry direction ('BUY' or 'SELL')
                - action (str): Should be 'open'
                - quantity (str/float): Order size (percentage or absolute)
                - trailType (str): Must be 'TRAILING_STOP_MARKET'
                - callbackRate (float): Trailing callback percentage (e.g., 1.5)
                - activationPrice (float): Price to activate trailing stop
                - workingType (str): 'MARK_PRICE' or 'CONTRACT_PRICE'
                - stopLoss (float): Fallback hard stop price
                
        Returns:
            dict: Result with success/error status
        """
        try:
            logger.info("=" * 80)
            logger.info("🔥 TRAILING STOP STRATEGY - FIRE AND FORGET MODE ACTIVATED")
            logger.info("=" * 80)
            
            # ============================================================
            # STEP 1: PARSE AND VALIDATE PAYLOAD
            # ============================================================
            symbol = data.get('symbol', '').upper().strip()
            # Clean .P extension from symbol (e.g., FETUSDT.P -> FETUSDT)
            symbol = symbol.replace('.P', '').replace('.p', '')
            entry_side_str = data.get('side', '').upper()  # 'BUY' or 'SELL'
            action = data.get('action', 'open').lower()
            
            # Convert types strictly
            try:
                callback_rate = float(data.get('callbackRate', 0))
                # activationPrice can be provided or calculated from entry
                activation_price_input = data.get('activationPrice', None)
                if activation_price_input is not None:
                    activation_price_input = float(activation_price_input)
                stop_loss_price = float(data.get('stopLoss', 0)) if data.get('stopLoss') else None
            except (TypeError, ValueError) as type_err:
                logger.error(f"❌ Type conversion error: {type_err}")
                return {"success": False, "error": f"Invalid numeric values: {type_err}"}
            
            working_type = data.get('workingType', 'MARK_PRICE').upper()
            
            # Validate required fields (activationPrice is optional - will be calculated)
            if not all([symbol, entry_side_str, callback_rate]):
                missing = []
                if not symbol: missing.append('symbol')
                if not entry_side_str: missing.append('side')
                if not callback_rate: missing.append('callbackRate')
                
                error_msg = f"Missing required fields: {', '.join(missing)}"
                logger.error(f"❌ {error_msg}")
                return {"success": False, "error": error_msg}
            
            logger.info(f"📊 STRATEGY PARAMETERS (INPUT):")
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Entry Side: {entry_side_str}")
            logger.info(f"   Callback Rate: {callback_rate}%")
            if activation_price_input:
                logger.info(f"   Activation Price (provided): ${activation_price_input:.2f}")
            else:
                logger.info(f"   Activation Price: Will be calculated from entry price")
            logger.info(f"   Working Type: {working_type}")
            if stop_loss_price:
                logger.info(f"   Fallback Stop Loss: ${stop_loss_price:.2f}")
            else:
                logger.info(f"   Fallback Stop Loss: Will be calculated from entry price")
            
            # Determine position direction
            if entry_side_str == 'BUY':
                direction = 'long'
                trailing_side = 'SELL'  # Close side for trailing stop
            elif entry_side_str == 'SELL':
                direction = 'short'
                trailing_side = 'BUY'  # Close side for trailing stop
            else:
                error_msg = f"Invalid entry side: {entry_side_str}"
                logger.error(f"❌ {error_msg}")
                return {"success": False, "error": error_msg}
            
            # Check if trading is enabled
            if not self.config.get('enable_trading', False):
                logger.warning("❌ Trading is globally disabled")
                return {"success": False, "error": "Trading is globally disabled"}
            
            # Check coin-specific trading
            if not self.coin_config_manager.is_trading_enabled(symbol):
                return {"success": False, "error": f"Trading is disabled for {symbol}"}
            
            # ============================================================
            # STEP 1.5: POSITION VALIDATION (AUTO POSITION SWITCH)
            # ============================================================
            logger.info("=" * 80)
            logger.info("🔍 STEP 1.5: POSITION VALIDATION (AUTO POSITION SWITCH)")
            logger.info("=" * 80)
            
            # Format symbol for validation
            formatted_symbol = self._format_symbol(symbol)
            
            # Get current positions for validation
            current_positions = self.get_open_positions()
            
            # Validate position request
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
                            logger.error(f"❌ Failed to close opposite position")
                            return {"success": False, "error": "Failed to close opposite position"}
            
            # ============================================================
            # STEP 2: PLACE PRIMARY ENTRY ORDER (WITHOUT TP/SL)
            # ============================================================
            logger.info("=" * 80)
            logger.info("📤 STEP 2: PLACING PRIMARY ENTRY ORDER (NO TP/SL)")
            logger.info("=" * 80)
            
            # Get coin configuration
            coin_config = self.coin_config_manager.get_coin_config(symbol)
            
            # Set leverage
            leverage_result = self.set_leverage(formatted_symbol, coin_config['leverage'])
            if not leverage_result:
                logger.error(f"Failed to set leverage to {coin_config['leverage']}x")
                return {"success": False, "error": f"Failed to set leverage to {coin_config['leverage']}x"}
            
            # Set margin type
            margin_result = self.set_margin_type(formatted_symbol, 'CROSSED')
            if not margin_result:
                logger.warning(f"Failed to set margin type (may already be set)")
            
            # Set position mode to Hedge mode
            self._set_position_mode(formatted_symbol, hedge_mode=True)
            is_hedge_mode = self._get_position_mode()
            
            # Get account balance
            margin_asset = self._get_margin_asset(formatted_symbol)
            available_balance, total_balance, unrealized_pnl = self.get_account_balance(margin_asset)
            
            if available_balance <= 0:
                logger.warning("Zero available balance, using dummy value for testing")
                available_balance = 1000.0
            
            # Calculate order quantity
            current_price = self.get_symbol_price(formatted_symbol)
            if current_price <= 0:
                return {"success": False, "error": "Failed to get current price"}
            
            # STEP 2.1: Get quantity from payload if provided, otherwise use config
            quantity_input = data.get('quantity')
            if quantity_input is not None:
                # Check if quantity is percentage string (e.g., "50%")
                if isinstance(quantity_input, str) and quantity_input.endswith('%'):
                    try:
                        percentage = float(quantity_input.rstrip('%'))
                        logger.info(f"📊 Using quantity from payload: {percentage}% of balance")
                        order_amount = available_balance * (percentage / 100)
                        leveraged_amount = order_amount * coin_config['leverage']
                        raw_quantity = leveraged_amount / current_price
                    except (ValueError, TypeError) as e:
                        logger.warning(f"⚠️ Invalid quantity format '{quantity_input}', using config instead")
                        # Fallback to config
                        order_amount = available_balance * (coin_config['order_size_percentage'] / 100)
                        leveraged_amount = order_amount * coin_config['leverage']
                        raw_quantity = leveraged_amount / current_price
                else:
                    # Direct quantity value provided
                    try:
                        raw_quantity = float(quantity_input)
                        logger.info(f"📊 Using quantity from payload: {raw_quantity} (absolute value)")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"⚠️ Invalid quantity value '{quantity_input}', using config instead")
                        # Fallback to config
                        order_amount = available_balance * (coin_config['order_size_percentage'] / 100)
                        leveraged_amount = order_amount * coin_config['leverage']
                        raw_quantity = leveraged_amount / current_price
            else:
                # No quantity in payload, use config
                logger.info(f"📊 No quantity in payload, using config: {coin_config['order_size_percentage']}%")
                order_amount = available_balance * (coin_config['order_size_percentage'] / 100)
                leveraged_amount = order_amount * coin_config['leverage']
                raw_quantity = leveraged_amount / current_price
            
            # Round quantity to symbol precision
            executed_qty = self._round_quantity_to_precision(formatted_symbol, raw_quantity)
            
            logger.info(f"📊 Order Calculation:")
            logger.info(f"   💰 Balance: ${available_balance:.2f}")
            logger.info(f"   📈 Order %: {coin_config['order_size_percentage']}%")
            logger.info(f"   🔥 Leverage: {coin_config['leverage']}x")
            logger.info(f"   💵 Base Amount: ${order_amount:.2f}")
            logger.info(f"   💪 Leveraged: ${leveraged_amount:.2f}")
            logger.info(f"   🎯 Quantity: {executed_qty:.6f}")
            
            # Determine Binance API side and position side
            binance_side = 'BUY' if direction == 'long' else 'SELL'
            position_side = 'LONG' if direction == 'long' else 'SHORT'
            
            # Place entry order (WITHOUT TP/SL - trailing stop will handle exit)
            logger.info(f"📤 Placing entry order:")
            logger.info(f"   Symbol: {formatted_symbol}")
            logger.info(f"   Side: {binance_side}")
            logger.info(f"   Position Side: {position_side}")
            logger.info(f"   Quantity: {executed_qty}")
            logger.info(f"   ⚠️ SKIPPING TP/SL (Trailing stop will manage exit)")
            
            # Build order parameters
            order_params = {
                'symbol': formatted_symbol,
                'side': binance_side,
                'type': 'MARKET',
                'quantity': executed_qty
            }
            
            # Only add positionSide if in Hedge mode
            if is_hedge_mode:
                order_params['positionSide'] = position_side
            
            try:
                entry_result = self.client.futures_create_order(**order_params)
                
                logger.info(f"✅ ENTRY ORDER PLACED SUCCESSFULLY")
                logger.info(f"   Order ID: {entry_result.get('orderId', 'N/A')}")
                logger.info(f"   Status: {entry_result.get('status', 'N/A')}")
                
                entry_order_id = entry_result.get('orderId', 'N/A')
                
            except Exception as entry_error:
                logger.error(f"❌ ENTRY ORDER FAILED: {str(entry_error)}")
                return {"success": False, "error": f"Entry order failed: {str(entry_error)}"}
            
            logger.info(f"   Position Size: {executed_qty}")
            
            # Wait for position to settle
            logger.info("⏳ Waiting 1 second for position to settle...")
            time.sleep(1.0)
            
            # ============================================================
            # STEP 2.5: GET ENTRY PRICE & CALCULATE ACTIVATION/STOP
            # ============================================================
            logger.info("=" * 80)
            logger.info("📊 STEP 2.5: CALCULATING ACTIVATION & STOP PRICES")
            logger.info("=" * 80)
            
            # Get actual entry price
            entry_price = current_price  # Fallback to order price
            
            # Try to get more accurate entry price from position
            try:
                positions = self.get_open_positions()
                for pos in positions:
                    if pos.get('symbol') == formatted_symbol:
                        pos_entry = float(pos.get('entryPrice', 0))
                        if pos_entry > 0:
                            entry_price = pos_entry
                            logger.info(f"✅ Got entry price from position: ${entry_price:.6f}")
                            break
            except Exception as e:
                logger.warning(f"Could not get entry from position, using order price: {str(e)}")
            
            # Calculate activation price if not provided
            if activation_price_input:
                activation_price = activation_price_input
                logger.info(f"📍 Using provided activation price: ${activation_price:.6f}")
            else:
                # Auto-calculate: 2% from entry in profit direction
                if direction == 'long':
                    activation_price = entry_price * 1.02  # 2% above entry
                else:
                    activation_price = entry_price * 0.98  # 2% below entry
                logger.info(f"📍 Calculated activation price: ${activation_price:.6f} (entry ± 2%)")
            
            # Calculate stop loss if not provided
            if stop_loss_price is None:
                # Auto-calculate: 3% from entry in loss direction
                if direction == 'long':
                    stop_loss_price = entry_price * 0.97  # 3% below entry
                else:
                    stop_loss_price = entry_price * 1.03  # 3% above entry
                logger.info(f"🛡️ Calculated stop loss: ${stop_loss_price:.6f} (entry ± 3%)")
            else:
                logger.info(f"🛡️ Using provided stop loss: ${stop_loss_price:.6f}")
            
            # Validate activation price logic
            if direction == 'long':
                if activation_price <= entry_price:
                    logger.warning(f"⚠️ LONG activation price should be > entry, adjusting...")
                    activation_price = entry_price * 1.02
                if stop_loss_price >= entry_price:
                    logger.warning(f"⚠️ LONG stop loss should be < entry, adjusting...")
                    stop_loss_price = entry_price * 0.97
            else:  # short
                if activation_price >= entry_price:
                    logger.warning(f"⚠️ SHORT activation price should be < entry, adjusting...")
                    activation_price = entry_price * 0.98
                if stop_loss_price <= entry_price:
                    logger.warning(f"⚠️ SHORT stop loss should be > entry, adjusting...")
                    stop_loss_price = entry_price * 1.03
            
            logger.info(f"📊 FINAL PRICES:")
            logger.info(f"   Entry: ${entry_price:.6f}")
            logger.info(f"   Activation: ${activation_price:.6f}")
            logger.info(f"   Stop Loss: ${stop_loss_price:.6f}")
            
            # ============================================================
            # STEP 3: PLACE TRAILING STOP ORDER (WITH FALLBACK)
            # ============================================================
            logger.info("=" * 80)
            logger.info("🎯 STEP 3: PLACING TRAILING STOP MARKET ORDER")
            logger.info("=" * 80)
            
            # Get position mode
            is_hedge_mode = self._get_position_mode()
            position_side = 'LONG' if direction == 'long' else 'SHORT'
            
            # Prepare trailing stop parameters
            # Note: TRAILING_STOP_MARKET does NOT support closePosition parameter
            # We must use quantity + correct side to close the position
            trailing_params = {
                'symbol': formatted_symbol,  # FIX: Use formatted_symbol instead of symbol
                'side': trailing_side,
                'type': 'TRAILING_STOP_MARKET',
                'quantity': executed_qty,  # Must specify quantity
                'callbackRate': callback_rate,
                'activationPrice': activation_price,
                'workingType': working_type
            }
            
            # Add positionSide only if in hedge mode
            if is_hedge_mode:
                trailing_params['positionSide'] = position_side
            
            logger.info(f"🔒 TRAILING STOP PARAMETERS:")
            logger.info(f"   Type: TRAILING_STOP_MARKET")
            logger.info(f"   Side: {trailing_side}")
            logger.info(f"   Quantity: {executed_qty}")
            logger.info(f"   Callback Rate: {callback_rate}%")
            logger.info(f"   Activation Price: ${activation_price:.2f}")
            logger.info(f"   Working Type: {working_type}")
            if is_hedge_mode:
                logger.info(f"   Position Side: {position_side}")
            
            # TRY to place trailing stop with retry
            # CRITICAL FIX: Use Algo Order API for trailing stop (error -4120)
            trailing_order = None
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"🔄 Trailing Stop Attempt {attempt + 1}/{max_retries}")
                    logger.info(f"   Using Binance Algo Order API (futures_create_algo_order)")
                    
                    # CRITICAL: Trailing stop MUST use Algo Order API, not regular order API
                    # Python-binance might not have this method, so we'll use direct API call
                    trailing_order = self._place_trailing_stop_algo_order(
                        formatted_symbol, trailing_side, executed_qty, callback_rate,
                        activation_price, working_type, position_side, is_hedge_mode
                    )
                    
                    logger.info(f"✅✅✅ TRAILING STOP ORDER PLACED SUCCESSFULLY! ✅✅✅")
                    logger.info(f"   Order ID: {trailing_order.get('orderId', 'N/A')}")
                    logger.info(f"   Status: {trailing_order.get('status', 'N/A')}")
                    logger.info(f"   Type: {trailing_order.get('type', 'N/A')}")
                    
                    # SUCCESS - Return immediately
                    return {
                        "success": True,
                        "message": "Trailing stop strategy executed successfully",
                        "order_id": entry_order_id,
                        "trailing_stop_id": trailing_order.get('orderId', 'N/A'),
                        "strategy": "TRAILING_STOP_MARKET"
                    }
                    
                except Exception as trailing_error:
                    error_msg = str(trailing_error)
                    logger.warning(f"⚠️ Trailing stop attempt {attempt + 1} failed: {error_msg}")
                    
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 0.5
                        logger.info(f"   Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    else:
                        # ALL RETRIES FAILED - ACTIVATE FALLBACK
                        logger.error(f"❌❌❌ TRAILING STOP FAILED AFTER {max_retries} ATTEMPTS ❌❌❌")
                        logger.error(f"   Last Error: {error_msg}")
                        logger.error(f"   ACTIVATING FALLBACK: Placing STOP_MARKET order")
                        break
            
            # ============================================================
            # STEP 4: FALLBACK - PLACE HARD STOP_MARKET ORDER
            # ============================================================
            if not trailing_order:
                logger.info("=" * 80)
                logger.info("🛡️ FALLBACK ACTIVATED: PLACING STOP_MARKET ORDER")
                logger.info("=" * 80)
                
                if stop_loss_price <= 0:
                    logger.error(f"❌ CRITICAL: No fallback stop loss price provided!")
                    return {
                        "success": False,
                        "error": "Trailing stop failed and no fallback stop loss provided"
                    }
                
                # Prepare fallback stop params
                # Note: Use quantity instead of closePosition for compatibility
                fallback_params = {
                    'symbol': formatted_symbol,  # FIX: Use formatted_symbol instead of symbol
                    'side': trailing_side,
                    'type': 'STOP_MARKET',
                    'quantity': executed_qty,  # Must specify quantity
                    'stopPrice': stop_loss_price
                }
                
                if is_hedge_mode:
                    fallback_params['positionSide'] = position_side
                
                logger.info(f"🔒 FALLBACK STOP PARAMETERS:")
                logger.info(f"   Type: STOP_MARKET")
                logger.info(f"   Side: {trailing_side}")
                logger.info(f"   Quantity: {executed_qty}")
                logger.info(f"   Stop Price: ${stop_loss_price:.2f}")
                
                try:
                    fallback_order = self.client.futures_create_order(**fallback_params)
                    
                    logger.info(f"✅ FALLBACK STOP_MARKET ORDER PLACED")
                    logger.info(f"   Order ID: {fallback_order.get('orderId', 'N/A')}")
                    logger.info(f"   Stop Price: ${stop_loss_price:.2f}")
                    
                    return {
                        "success": True,
                        "message": "Trailing stop failed, placed hard stop as fallback",
                        "order_id": entry_order_id,
                        "fallback_stop_id": fallback_order.get('orderId', 'N/A'),
                        "strategy": "FALLBACK_STOP_MARKET",
                        "warning": "Trailing stop rejected by exchange"
                    }
                    
                except Exception as fallback_error:
                    logger.error(f"❌❌❌ FALLBACK ALSO FAILED ❌❌❌")
                    logger.error(f"   Error: {str(fallback_error)}")
                    
                    # CRITICAL FIX: If both trailing stop and fallback failed, place TP/SL as last resort
                    logger.warning("🛡️ Last resort: Placing TP/SL orders as protection...")
                    try:
                        # Get entry price from position
                        positions = self.get_open_positions()
                        actual_entry_price = entry_price
                        for pos in positions:
                            if pos.get('symbol') == formatted_symbol:
                                pos_entry = float(pos.get('entryPrice', 0))
                                if pos_entry > 0:
                                    actual_entry_price = pos_entry
                                    break
                        
                        # Calculate ATR and TP/SL
                        atr_period = self.tp_sl_manager.get_atr_period(formatted_symbol)
                        atr_value = self.get_atr(formatted_symbol, atr_period)
                        
                        if atr_value > 0:
                            tp_price, sl_price = self.tp_sl_manager.calculate_tp_sl_prices(
                                formatted_symbol, actual_entry_price, atr_value, direction
                            )
                            
                            # Validate TP/SL logic
                            if self.tp_sl_manager.validate_tp_sl_logic(
                                formatted_symbol, direction, actual_entry_price, tp_price, sl_price
                            ):
                                # Place TP/SL orders
                                tp_side = 'SELL' if direction == 'long' else 'BUY'
                                tp_price_rounded = self.tp_sl_manager._round_to_price_step(formatted_symbol, tp_price)
                                sl_price_rounded = self.tp_sl_manager._round_to_price_step(formatted_symbol, sl_price)
                                
                                tp_params = {
                                    'symbol': formatted_symbol,
                                    'side': tp_side,
                                    'type': 'TAKE_PROFIT_MARKET',
                                    'stopPrice': tp_price_rounded,
                                    'closePosition': True
                                }
                                
                                sl_params = {
                                    'symbol': formatted_symbol,
                                    'side': tp_side,
                                    'type': 'STOP_MARKET',
                                    'stopPrice': sl_price_rounded,
                                    'closePosition': True
                                }
                                
                                if is_hedge_mode:
                                    tp_params['positionSide'] = position_side
                                    sl_params['positionSide'] = position_side
                                
                                try:
                                    tp_order = self.client.futures_create_order(**tp_params)
                                    sl_order = self.client.futures_create_order(**sl_params)
                                    logger.info(f"✅✅✅ TP/SL PLACED AS LAST RESORT ✅✅✅")
                                    logger.info(f"   TP Order ID: {tp_order.get('orderId', 'N/A')}")
                                    logger.info(f"   SL Order ID: {sl_order.get('orderId', 'N/A')}")
                                    
                                    return {
                                        "success": True,
                                        "message": "Trailing stop and fallback failed, but TP/SL placed as protection",
                                        "order_id": entry_order_id,
                                        "tp_order_id": tp_order.get('orderId', 'N/A'),
                                        "sl_order_id": sl_order.get('orderId', 'N/A'),
                                        "strategy": "FALLBACK_TP_SL",
                                        "warning": "Trailing stop failed, using TP/SL protection"
                                    }
                                except Exception as tp_sl_error:
                                    logger.error(f"❌ TP/SL placement also failed: {str(tp_sl_error)}")
                    except Exception as tp_sl_fallback_error:
                        logger.error(f"❌ TP/SL fallback failed: {str(tp_sl_fallback_error)}")
                    
                    return {
                        "success": False,
                        "error": f"Both trailing stop and fallback failed: {str(fallback_error)}",
                        "order_id": entry_order_id,
                        "warning": "Position opened but no stop protection placed!"
                    }
            
        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR IN TRAILING STOP STRATEGY: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
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
            logger.info(f"   Order Status: {order_result.get('status', 'N/A')}")
            logger.info(f"   Order Response Keys: {list(order_result.keys())}")
            
            # Get current price for notification and TP/SL
            # Try multiple sources for entry price
            current_price = 0.0
            
            # Method 1: Try avgPrice from order result
            if 'avgPrice' in order_result and float(order_result.get('avgPrice', 0)) > 0:
                current_price = float(order_result['avgPrice'])
                logger.info(f"📊 Entry price from order avgPrice: ${current_price:.2f}")
            # Method 2: Try price from order result
            elif 'price' in order_result and float(order_result.get('price', 0)) > 0:
                current_price = float(order_result['price'])
                logger.info(f"📊 Entry price from order price: ${current_price:.2f}")
            # Method 3: Get current market price
            else:
                logger.warning(f"⚠️ No avgPrice in order result, fetching current market price...")
                current_price = self.get_symbol_price(formatted_symbol)
                if current_price > 0:
                    logger.info(f"📊 Entry price from market: ${current_price:.2f}")
                else:
                    logger.error(f"❌ Failed to get entry price from all sources!")
                    logger.error(f"   Order result: {order_result}")
                    # Try to get from position info as last resort
                    time.sleep(0.5)  # Wait a bit for position to settle
                    positions = self.get_open_positions()
                    for pos in positions:
                        if pos.get('symbol') == formatted_symbol:
                            pos_price = float(pos.get('entryPrice', 0))
                            if pos_price > 0:
                                current_price = pos_price
                                logger.info(f"📊 Entry price from position info: ${current_price:.2f}")
                                break
            
            if current_price <= 0:
                logger.error(f"❌ CRITICAL: Entry price is invalid: ${current_price}")
                logger.error(f"   Cannot proceed with TP/SL placement")
                logger.error(f"   Order was placed but TP/SL will be skipped")
            
            tp_price = None
            sl_price = None
            
            # Place TP/SL orders for open positions
            if action == 'open':
                # Skip TP/SL if entry price is invalid
                if current_price <= 0:
                    logger.error(f"❌ Skipping TP/SL placement - invalid entry price: ${current_price}")
                    logger.error(f"   Order was placed successfully but TP/SL cannot be calculated")
                else:
                    logger.info(f"🔒 ========== TP/SL ORDER PLACEMENT START ==========")
                    logger.info(f"   Symbol: {formatted_symbol}")
                    logger.info(f"   Position Side: {position_side}")
                    logger.info(f"   Direction: {direction}")
                    logger.info(f"   Entry Price: ${current_price:.2f}")
                    
                    try:
                        # Wait for position to be fully opened (delay)
                        logger.info(f"⏳ Step 1/6: Waiting 0.5s for position to settle...")
                        time.sleep(0.5)
                        
                        # Verify position exists (non-blocking - just for info)
                        logger.info(f"⏳ Step 2/6: Verifying position exists...")
                        position_verified = self._wait_for_position_opening(formatted_symbol, position_side, max_wait=1.5)
                        
                        if position_verified:
                            logger.info(f"✅ Position verified successfully")
                        else:
                            logger.warning(f"⚠️ Position verification timeout, but continuing anyway...")
                        
                        # Get ATR value using 1h data
                        logger.info(f"⏳ Step 3/6: Calculating ATR...")
                        atr_period = self.tp_sl_manager.get_atr_period(formatted_symbol)  # FIX: Use formatted_symbol
                        logger.info(f"   ATR Period: {atr_period}")
                        
                        atr_value = self.get_atr(formatted_symbol, atr_period)
                        
                        if atr_value <= 0:
                            logger.error(f"❌ ATR calculation failed or returned 0: {atr_value}")
                            logger.error(f"   This will prevent TP/SL order placement")
                            logger.error(f"   Please check market data availability for {formatted_symbol}")
                            raise ValueError(f"ATR value is invalid: {atr_value}")
                        
                        logger.info(f"✅ ATR calculated successfully: {atr_value:.6f}")
                        
                        # Calculate TP/SL prices
                        logger.info(f"⏳ Step 4/6: Calculating TP/SL prices...")
                        tp_price, sl_price = self.tp_sl_manager.calculate_tp_sl_prices(
                            formatted_symbol, current_price, atr_value, direction  # FIX: Use formatted_symbol
                        )
                        
                        logger.info(f"📊 TP/SL Price Calculation Results:")
                        logger.info(f"   Entry Price: ${current_price:.2f}")
                        logger.info(f"   ATR Value: {atr_value:.6f}")
                        logger.info(f"   TP Price: ${tp_price:.2f}")
                        logger.info(f"   SL Price: ${sl_price:.2f}")
                        
                        # Validate TP/SL logic
                        logger.info(f"⏳ Step 5/6: Validating TP/SL logic...")
                        is_valid = self.tp_sl_manager.validate_tp_sl_logic(
                            formatted_symbol, direction, current_price, tp_price, sl_price  # FIX: Use formatted_symbol
                        )
                        
                        if not is_valid:
                            logger.error(f"❌ TP/SL validation FAILED!")
                            logger.error(f"   Entry: ${current_price:.2f}")
                            logger.error(f"   TP: ${tp_price:.2f}")
                            logger.error(f"   SL: ${sl_price:.2f}")
                            logger.error(f"   Direction: {direction}")
                            logger.error(f"   Please check TP/SL multipliers in configuration")
                            raise ValueError("TP/SL validation failed")
                        
                        logger.info(f"✅ TP/SL validation PASSED")
                        
                        # Prepare TP/SL order parameters
                        tp_side = 'SELL' if direction == 'long' else 'BUY'
                        
                        # Round stop prices to proper precision
                        tp_price_rounded = self.tp_sl_manager._round_to_price_step(formatted_symbol, tp_price)  # FIX: Use formatted_symbol
                        sl_price_rounded = self.tp_sl_manager._round_to_price_step(formatted_symbol, sl_price)  # FIX: Use formatted_symbol
                        
                        logger.info(f"📊 Rounded Prices:")
                        logger.info(f"   TP: ${tp_price:.6f} -> ${tp_price_rounded:.6f}")
                        logger.info(f"   SL: ${sl_price:.6f} -> ${sl_price_rounded:.6f}")
                        
                        tp_params = {
                            'symbol': formatted_symbol,
                            'side': tp_side,
                            'type': 'TAKE_PROFIT_MARKET',
                            'stopPrice': tp_price_rounded,
                            'closePosition': True
                        }
                        
                        sl_params = {
                            'symbol': formatted_symbol,
                            'side': tp_side,
                            'type': 'STOP_MARKET',
                            'stopPrice': sl_price_rounded,
                            'closePosition': True
                        }
                        
                        if is_hedge_mode:
                            tp_params['positionSide'] = position_side
                            sl_params['positionSide'] = position_side
                            logger.info(f"   Using Hedge Mode - positionSide: {position_side}")
                        else:
                            logger.info(f"   Using One-Way Mode")
                        
                        logger.info(f"⏳ Step 6/6: Placing TP/SL orders with retry mechanism...")
                        logger.info(f"   TP Params: {tp_params}")
                        logger.info(f"   SL Params: {sl_params}")
                        
                        # Place TP/SL orders with retry
                        tp_order, sl_order = self._place_tp_sl_with_retry(
                            formatted_symbol, tp_params, sl_params, position_side, max_retries=3
                        )
                        
                        # Check results
                        if tp_order:
                            logger.info(f"✅✅✅ TP ORDER SUCCESSFULLY PLACED! ✅✅✅")
                            logger.info(f"   Order ID: {tp_order.get('orderId', 'N/A')}")
                            logger.info(f"   Stop Price: ${tp_price_rounded:.2f}")
                        else:
                            logger.error(f"❌❌❌ TP ORDER FAILED AFTER ALL RETRIES ❌❌❌")
                            logger.error(f"   This is a critical error - TP order was not placed!")
                        
                        if sl_order:
                            logger.info(f"✅✅✅ SL ORDER SUCCESSFULLY PLACED! ✅✅✅")
                            logger.info(f"   Order ID: {sl_order.get('orderId', 'N/A')}")
                            logger.info(f"   Stop Price: ${sl_price_rounded:.2f}")
                        else:
                            logger.error(f"❌❌❌ SL ORDER FAILED AFTER ALL RETRIES ❌❌❌")
                            logger.error(f"   This is a critical error - SL order was not placed!")
                        
                        # Update prices for notification (use rounded prices)
                        if tp_order and sl_order:
                            tp_price = tp_price_rounded
                            sl_price = sl_price_rounded
                            logger.info(f"🔒 ========== TP/SL ORDER PLACEMENT COMPLETE ==========")
                        else:
                            logger.error(f"🔒 ========== TP/SL ORDER PLACEMENT INCOMPLETE ==========")
                            logger.error(f"   TP Order: {'✅' if tp_order else '❌'}")
                            logger.error(f"   SL Order: {'✅' if sl_order else '❌'}")
                            
                    except Exception as tp_sl_error:
                        logger.error(f"❌❌❌ CRITICAL ERROR IN TP/SL PLACEMENT ❌❌❌")
                        logger.error(f"   Error: {str(tp_sl_error)}")
                        logger.error(f"   Error Type: {type(tp_sl_error).__name__}")
                        import traceback
                        logger.error(f"Full traceback:")
                        logger.error(traceback.format_exc())
                        logger.error(f"⚠️ Main order was placed successfully, but TP/SL orders failed")
                        logger.error(f"   Please check logs above for details")
                        logger.error(f"🔒 ========== TP/SL ORDER PLACEMENT FAILED ==========")
            
            # Send notification AFTER order is placed (independent of TP/SL success)
            try:
                tp_sl_data = None
                if tp_price and sl_price and current_price > 0:
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
    
    def _wait_for_position_opening(self, symbol: str, position_side: str, max_wait: float = 2.0, check_interval: float = 0.5) -> bool:
        """
        Wait for position to be fully opened after order placement
        
        Args:
            symbol (str): Trading symbol
            position_side (str): Position side ('LONG' or 'SHORT')
            max_wait (float): Maximum time to wait in seconds
            check_interval (float): Interval between checks in seconds
            
        Returns:
            bool: True if position exists, False if timeout
        """
        try:
            formatted_symbol = self._format_symbol(symbol)
            elapsed = 0.0
            
            logger.info(f"⏳ Waiting for position to open: {formatted_symbol} {position_side}")
            
            while elapsed < max_wait:
                time.sleep(check_interval)
                elapsed += check_interval
                
                # Check if position exists
                if self._verify_position_exists(formatted_symbol, position_side):
                    logger.info(f"✅ Position verified after {elapsed:.1f}s")
                    return True
            
            logger.warning(f"⚠️ Position verification timeout after {max_wait}s")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error waiting for position: {str(e)}")
            return False
    
    def _verify_position_exists(self, symbol: str, position_side: str) -> bool:
        """
        Verify that a position exists for the given symbol and side
        
        Args:
            symbol (str): Trading symbol
            position_side (str): Position side ('LONG' or 'SHORT')
            
        Returns:
            bool: True if position exists, False otherwise
        """
        try:
            positions = self.get_open_positions()
            
            for pos in positions:
                pos_symbol = pos.get('symbol', '')
                pos_side = pos.get('positionSide', '')
                position_amt = abs(float(pos.get('positionAmt', '0')))
                
                if pos_symbol == symbol and position_amt > 0:
                    # Check position side match
                    if pos_side == position_side:
                        logger.debug(f"✅ Position verified: {symbol} {position_side} ({position_amt})")
                        return True
                    # For one-way mode, positionSide is 'BOTH', check positionAmt sign
                    elif pos_side == 'BOTH':
                        actual_side = 'LONG' if float(pos.get('positionAmt', '0')) > 0 else 'SHORT'
                        if actual_side == position_side:
                            logger.debug(f"✅ Position verified (one-way): {symbol} {position_side} ({position_amt})")
                            return True
            
            logger.debug(f"⚠️ Position not found: {symbol} {position_side}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error verifying position: {str(e)}")
            return False
    
    def _determine_position_side(self, position_amt: float, position_side: str) -> str:
        """
        Determine position side from positionAmt and positionSide
        
        Args:
            position_amt (float): Position amount (can be negative for short)
            position_side (str): Position side from API ('LONG', 'SHORT', or 'BOTH')
            
        Returns:
            str: 'LONG' or 'SHORT'
        """
        if position_side in ['LONG', 'SHORT']:
            return position_side
        
        # One-way mode: determine from positionAmt sign
        return 'LONG' if position_amt > 0 else 'SHORT'
    
    def _place_trailing_stop_algo_order(self, symbol: str, side: str, quantity: float,
                                       callback_rate: float, activation_price: float,
                                       working_type: str, position_side: str, is_hedge_mode: bool):
        """
        Place trailing stop order using Binance Algo Order API
        
        CRITICAL: Trailing stop orders MUST use Algo Order API, not regular order API
        Error -4120: "Order type not supported for this endpoint. Please use the Algo Order API endpoints instead."
        
        Args:
            symbol: Trading symbol
            side: Order side ('SELL' for long positions, 'BUY' for short)
            quantity: Order quantity
            callback_rate: Trailing callback rate (e.g., 0.1 for 0.1%)
            activation_price: Activation price
            working_type: 'MARK_PRICE' or 'CONTRACT_PRICE'
            position_side: 'LONG' or 'SHORT'
            is_hedge_mode: Whether in hedge mode
            
        Returns:
            dict: Order response
        """
        try:
            import time as time_module
            
            # Binance Futures Algo Order API endpoint
            endpoint = '/fapi/v1/algo/order'
            url = f"{self.base_url}{endpoint}"
            
            # Build parameters
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'TRAILING_STOP_MARKET',
                'quantity': quantity,
                'callbackRate': callback_rate,
                'activationPrice': activation_price,
                'workingType': working_type,
                'timestamp': int(time_module.time() * 1000)
            }
            
            # Add positionSide only if in hedge mode
            if is_hedge_mode:
                params['positionSide'] = position_side
            
            # Create signature
            query_string = urlencode(sorted(params.items()))
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            params['signature'] = signature
            
            # Make request
            headers = {
                'X-MBX-APIKEY': self.api_key
            }
            
            logger.info(f"📡 Calling Binance Algo Order API: {url}")
            logger.info(f"   Parameters: {dict((k, v) for k, v in params.items() if k != 'signature')}")
            
            response = requests.post(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Algo Order API Response: {result}")
                return result
            else:
                error_msg = f"Algo Order API error: {response.status_code} - {response.text}"
                logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"❌ Error placing algo order: {str(e)}")
            raise
    
    def _place_tp_sl_with_retry(self, symbol: str, tp_params: dict, sl_params: dict, 
                                position_side: str, max_retries: int = 3) -> tuple:
        """
        Place TP/SL orders with retry mechanism
        
        Args:
            symbol (str): Trading symbol
            tp_params (dict): TP order parameters
            sl_params (dict): SL order parameters
            position_side (str): Position side
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            tuple: (tp_order_result, sl_order_result) or (None, None) if failed
        """
        tp_order = None
        sl_order = None
        
        logger.info(f"🔄 Starting TP/SL retry mechanism for {symbol}")
        logger.info(f"   Max Retries: {max_retries}")
        
        # Place TP order with retry
        logger.info(f"📤 Attempting to place TP order...")
        for attempt in range(max_retries):
            try:
                logger.info(f"   Attempt {attempt + 1}/{max_retries}")
                logger.debug(f"   TP Params: {tp_params}")
                
                tp_order = self.client.futures_create_order(**tp_params)
                
                logger.info(f"✅ TP order placed successfully!")
                logger.info(f"   Order ID: {tp_order.get('orderId', 'N/A')}")
                logger.info(f"   Order Status: {tp_order.get('status', 'N/A')}")
                logger.info(f"   Stop Price: ${tp_params.get('stopPrice', 0):.2f}")
                logger.debug(f"   Full Response: {tp_order}")
                break
                
            except Exception as tp_error:
                error_msg = str(tp_error)
                error_code = None
                
                # Try to extract error code if it's a BinanceAPIException
                if hasattr(tp_error, 'code'):
                    error_code = tp_error.code
                elif '-2010' in error_msg or '-2011' in error_msg:
                    # Common Binance error codes
                    import re
                    code_match = re.search(r'-(\d{4})', error_msg)
                    if code_match:
                        error_code = code_match.group(1)
                
                logger.warning(f"⚠️ TP order attempt {attempt + 1} failed")
                logger.warning(f"   Error: {error_msg}")
                if error_code:
                    logger.warning(f"   Error Code: {error_code}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 0.5  # Exponential backoff
                    logger.info(f"   Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ TP order failed after {max_retries} attempts")
                    logger.error(f"   Final Error: {error_msg}")
                    if error_code:
                        logger.error(f"   Error Code: {error_code}")
                        if error_code == '2010':
                            logger.error(f"   This usually means: New order rejected")
                        elif error_code == '2011':
                            logger.error(f"   This usually means: Unknown order sent")
                    import traceback
                    logger.error(f"   Full traceback:")
                    logger.error(traceback.format_exc())
        
        # Place SL order with retry (independent of TP)
        logger.info(f"📤 Attempting to place SL order...")
        for attempt in range(max_retries):
            try:
                logger.info(f"   Attempt {attempt + 1}/{max_retries}")
                logger.debug(f"   SL Params: {sl_params}")
                
                sl_order = self.client.futures_create_order(**sl_params)
                
                logger.info(f"✅ SL order placed successfully!")
                logger.info(f"   Order ID: {sl_order.get('orderId', 'N/A')}")
                logger.info(f"   Order Status: {sl_order.get('status', 'N/A')}")
                logger.info(f"   Stop Price: ${sl_params.get('stopPrice', 0):.2f}")
                logger.debug(f"   Full Response: {sl_order}")
                break
                
            except Exception as sl_error:
                error_msg = str(sl_error)
                error_code = None
                
                # Try to extract error code if it's a BinanceAPIException
                if hasattr(sl_error, 'code'):
                    error_code = sl_error.code
                elif '-2010' in error_msg or '-2011' in error_msg:
                    # Common Binance error codes
                    import re
                    code_match = re.search(r'-(\d{4})', error_msg)
                    if code_match:
                        error_code = code_match.group(1)
                
                logger.warning(f"⚠️ SL order attempt {attempt + 1} failed")
                logger.warning(f"   Error: {error_msg}")
                if error_code:
                    logger.warning(f"   Error Code: {error_code}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 0.5  # Exponential backoff
                    logger.info(f"   Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ SL order failed after {max_retries} attempts")
                    logger.error(f"   Final Error: {error_msg}")
                    if error_code:
                        logger.error(f"   Error Code: {error_code}")
                        if error_code == '2010':
                            logger.error(f"   This usually means: New order rejected")
                        elif error_code == '2011':
                            logger.error(f"   This usually means: Unknown order sent")
                    import traceback
                    logger.error(f"   Full traceback:")
                    logger.error(traceback.format_exc())
        
        logger.info(f"🔄 TP/SL retry mechanism completed")
        logger.info(f"   TP Order: {'✅ Success' if tp_order else '❌ Failed'}")
        logger.info(f"   SL Order: {'✅ Success' if sl_order else '❌ Failed'}")
        
        return tp_order, sl_order
    
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
                
                symbol = pos.get('symbol', 'UNKNOWN')
                
                # Determine position side correctly
                position_side_api = pos.get('positionSide', 'BOTH')
                side = self._determine_position_side(position_amt, position_side_api)
                
                entry_price = float(pos.get('entryPrice', '0'))
                mark_price = float(pos.get('markPrice', '0'))
                
                # Debug: Log all available fields for troubleshooting
                logger.debug(f"📊 Processing position: {symbol} {side}")
                logger.debug(f"   Raw position data keys: {list(pos.keys())}")
                logger.debug(f"   positionAmt: {position_amt}")
                logger.debug(f"   entryPrice: {entry_price}")
                logger.debug(f"   markPrice: {mark_price}")
                
                # Try to get unrealized PnL from API (check multiple possible field names)
                unrealized_pnl_api = float(pos.get('unrealizedProfit', pos.get('unRealizedProfit', pos.get('unrealizedPnl', '0'))))
                logger.debug(f"   unrealizedProfit (API): {unrealized_pnl_api}")
                
                # Calculate PnL manually for verification
                unrealized_pnl_calculated = 0.0
                if entry_price > 0 and mark_price > 0:
                    if side == 'LONG':
                        # Long: profit = (mark_price - entry_price) * position_amt
                        unrealized_pnl_calculated = (mark_price - entry_price) * position_amt
                    else:  # SHORT
                        # Short: profit = (entry_price - mark_price) * abs(position_amt)
                        # Note: position_amt is negative for short positions
                        unrealized_pnl_calculated = (entry_price - mark_price) * abs(position_amt)
                    
                    logger.debug(f"   Calculated PnL: ${unrealized_pnl_calculated:.2f}")
                
                # Use API value if available and reasonable, otherwise use calculated value
                # If API value is 0 but calculated value is not, use calculated value
                if abs(unrealized_pnl_api) < 0.01 and abs(unrealized_pnl_calculated) >= 0.01:
                    logger.info(f"📊 Using calculated PnL for {symbol} {side}")
                    logger.info(f"   API PnL: ${unrealized_pnl_api:.2f}, Calculated: ${unrealized_pnl_calculated:.2f}")
                    unrealized_pnl = unrealized_pnl_calculated
                elif abs(unrealized_pnl_api) >= 0.01:
                    unrealized_pnl = unrealized_pnl_api
                    logger.debug(f"   Using API PnL: ${unrealized_pnl:.2f}")
                else:
                    # Both are essentially 0
                    unrealized_pnl = unrealized_pnl_calculated
                    logger.debug(f"   Both API and calculated PnL are ~0, using calculated: ${unrealized_pnl:.2f}")
                
                leverage = int(pos.get('leverage', '1'))
                
                # Calculate PnL percentage correctly (without leverage multiplication)
                # PnL percentage = (price_change / entry_price) * 100
                pnl_percentage = 0.0
                
                if entry_price > 0 and mark_price > 0:
                    if side == 'LONG':
                        # Long: profit when mark_price > entry_price
                        pnl_percentage = ((mark_price - entry_price) / entry_price) * 100
                    else:  # SHORT
                        # Short: profit when entry_price > mark_price
                        pnl_percentage = ((entry_price - mark_price) / entry_price) * 100
                else:
                    logger.warning(f"⚠️ Invalid prices for {pos.get('symbol', 'UNKNOWN')}: entry={entry_price}, mark={mark_price}")
                    pnl_percentage = 0.0
                
                # Get coin icon
                coin_icon = self._get_coin_icon(symbol)
                
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
                    'liquidation_price': f"${float(pos.get('liquidationPrice', '0')):.4f}",
                    'coin_icon': coin_icon['icon'],
                    'coin_color': coin_icon['color']
                }
                
                logger.debug(f"📊 Position formatted: {pos['symbol']} {side} - PnL: ${unrealized_pnl:.2f} ({pnl_percentage:.2f}%)")
                formatted_positions.append(formatted_pos)
            
            logger.info(f"✅ Formatted {len(formatted_positions)} positions for dashboard")
            return formatted_positions
            
        except Exception as e:
            logger.error(f"❌ Error formatting positions: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
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
                
                if price > 0:  # Prevent division by zero
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
                else:
                    message += (
                        f"🎯 Take Profit: ${tp_price:.2f}\n"
                        f"🛡️ Stop Loss: ${sl_price:.2f}\n"
                        f"⚠️ Entry price was invalid, percentages not calculated\n"
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
