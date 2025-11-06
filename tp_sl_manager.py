#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)

class TPSLManager:
    """
    Unified TP/SL Management System for Binance
    Ensures consistent TP/SL behavior for ALL coins
    Uses 1h ATR data for calculations
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.default_tp_multiplier = 2.5
        self.default_sl_multiplier = 3.0
        self.default_atr_period = 14
        
    def calculate_tp_sl_prices(self, 
                              coin_symbol: str, 
                              current_price: float, 
                              atr_value: float, 
                              position_side: str) -> Tuple[float, float]:
        """
        Calculate TP and SL prices for any coin using standardized logic
        
        Args:
            coin_symbol (str): Trading symbol (e.g., 'BTCUSDT', 'ETHUSDC')
            current_price (float): Current market price
            atr_value (float): ATR value for the coin (calculated from 1h data)
            position_side (str): 'long' or 'short'
            
        Returns:
            Tuple[float, float]: (tp_price, sl_price)
        """
        try:
            # Get coin-specific multipliers with fallback to defaults
            coin_type = self._extract_coin_type(coin_symbol)
            
            tp_multiplier = self.config.get(f'{coin_type}_atr_tp_multiplier', self.default_tp_multiplier)
            sl_multiplier = self.config.get(f'{coin_type}_atr_sl_multiplier', self.default_sl_multiplier)
            
            # Validate multipliers
            tp_multiplier = float(tp_multiplier) if tp_multiplier else self.default_tp_multiplier
            sl_multiplier = float(sl_multiplier) if sl_multiplier else self.default_sl_multiplier
            
            logger.info(f"🎯 TP/SL Calculation for {coin_symbol} (1h ATR):")
            logger.info(f"   💰 Current Price: ${current_price:.2f}")
            logger.info(f"   📊 ATR Value (1h): {atr_value:.4f}")
            logger.info(f"   🎯 TP Multiplier: {tp_multiplier}x")
            logger.info(f"   🛡️ SL Multiplier: {sl_multiplier}x")
            logger.info(f"   📈 Position Side: {position_side}")
            
            # Calculate TP/SL based on position side
            position_side_lower = position_side.lower()
            
            if position_side_lower == 'long':
                tp_price = current_price + (atr_value * tp_multiplier)
                sl_price = current_price - (atr_value * sl_multiplier)
            elif position_side_lower == 'short':
                tp_price = current_price - (atr_value * tp_multiplier)
                sl_price = current_price + (atr_value * sl_multiplier)
            else:
                raise ValueError(f"Invalid position side: {position_side}")
            
            # Round prices to appropriate precision
            tp_price = self._round_to_price_step(coin_symbol, tp_price)
            sl_price = self._round_to_price_step(coin_symbol, sl_price)
            
            # Validate prices are positive
            if tp_price <= 0 or sl_price <= 0:
                raise ValueError(f"Invalid calculated prices: TP={tp_price}, SL={sl_price}")
            
            logger.info(f"✅ Calculated TP/SL Prices:")
            logger.info(f"   🎯 Take Profit: ${tp_price:.2f}")
            logger.info(f"   🛡️ Stop Loss: ${sl_price:.2f}")
            
            return tp_price, sl_price
            
        except Exception as e:
            logger.error(f"❌ Error calculating TP/SL for {coin_symbol}: {str(e)}")
            raise
    
    def _round_to_price_step(self, symbol: str, price: float) -> float:
        """
        Round price according to Binance's price step rules
        
        Args:
            symbol (str): Trading symbol
            price (float): Price to round
            
        Returns:
            float: Rounded price
        """
        try:
            # Define price step rules for different coins
            price_steps = {
                'BTCUSDT': 0.1,
                'BTCUSDC': 0.1,
                'ETHUSDT': 0.01,
                'ETHUSDC': 0.01,
                'SOLUSDT': 0.01,
                'SOLUSDC': 0.01,
                'BNBUSDT': 0.01,
                'BNBUSDC': 0.01,
                'XRPUSDT': 0.0001,
                'XRPUSDC': 0.0001,
                'ADAUSDT': 0.0001,
                'ADAUSDC': 0.0001,
                'DOTUSDT': 0.001,
                'XLMUSDT': 0.00001,
                'IMXUSDT': 0.0001,
                'DOGEUSDT': 0.000001,
                'INJUSDT': 0.001,
                'LDOUSDT': 0.0001,
                'ARBUSDT': 0.0001,
                'ARBUSDC': 0.0001,
                'UNIUSDT': 0.001,
                'UNIUSDC': 0.001,
                'FETUSDT': 0.0001,
                'AAVEUSDC': 0.01,
                'BCHUSDC': 0.01,
                'AVAXUSDC': 0.001,
                'LINKUSDC': 0.001,
                'CRVUSDC': 0.0001,
                'TIAUSDC': 0.0001,
                'FILUSDC': 0.001,
            }
            
            # Get price step for the symbol, default to 0.01
            price_step = price_steps.get(symbol.upper(), 0.01)
            
            # Round to the nearest price step
            rounded_price = round(price / price_step) * price_step
            
            # Fix floating point precision issues
            if price_step >= 1:
                rounded_price = round(rounded_price, 1)
            elif price_step >= 0.01:
                rounded_price = round(rounded_price, 2)
            elif price_step >= 0.001:
                rounded_price = round(rounded_price, 3)
            elif price_step >= 0.0001:
                rounded_price = round(rounded_price, 4)
            elif price_step >= 0.00001:
                rounded_price = round(rounded_price, 5)
            else:
                rounded_price = round(rounded_price, 6)
            
            # Ensure we don't round to 0
            if rounded_price <= 0:
                rounded_price = price_step
            
            logger.debug(f"Price rounding for {symbol}: {price:.6f} -> {rounded_price:.6f} (step: {price_step})")
            
            return rounded_price
            
        except Exception as e:
            logger.error(f"Error rounding price for {symbol}: {str(e)}")
            # Fallback to 2 decimal places
            return round(price, 2)
    
    def _extract_coin_type(self, symbol: str) -> str:
        """
        Extract coin type from symbol for config lookup
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT', 'ETHUSDC')
            
        Returns:
            str: Coin type (e.g., 'btc', 'ethusdc', 'sol')
        """
        # Remove whitespace
        clean_symbol = symbol.upper().strip()
        
        # For USDC pairs, keep the USDC suffix
        if clean_symbol.endswith('USDC'):
            coin_type = clean_symbol.lower()
        else:
            # For USDT pairs, remove USDT suffix
            clean_symbol = clean_symbol.replace('USDT', '')
            coin_type = clean_symbol.lower()
        
        logger.debug(f"Extracted coin type '{coin_type}' from symbol '{symbol}'")
        return coin_type
    
    def get_atr_period(self, coin_symbol: str) -> int:
        """
        Get ATR period for a specific coin
        
        Args:
            coin_symbol (str): Trading symbol
            
        Returns:
            int: ATR period
        """
        coin_type = self._extract_coin_type(coin_symbol)
        atr_period = self.config.get(f'{coin_type}_atr_period', self.default_atr_period)
        
        try:
            atr_period = int(atr_period)
        except (TypeError, ValueError):
            logger.warning(f"Invalid ATR period for {coin_type}: {atr_period}, using default {self.default_atr_period}")
            atr_period = self.default_atr_period
            
        return atr_period
    
    def create_tp_sl_params(self, 
                           coin_symbol: str, 
                           current_price: float, 
                           atr_value: float, 
                           position_side: str) -> Dict[str, float]:
        """
        Create TP/SL parameters for Binance API
        
        Args:
            coin_symbol (str): Trading symbol
            current_price (float): Current market price
            atr_value (float): ATR value (from 1h data)
            position_side (str): 'long' or 'short'
            
        Returns:
            Dict[str, float]: TP/SL prices
        """
        try:
            tp_price, sl_price = self.calculate_tp_sl_prices(
                coin_symbol, current_price, atr_value, position_side
            )
            
            params = {
                "tp_price": tp_price,
                "sl_price": sl_price
            }
            
            logger.info(f"🔒 TP/SL Parameters Created (1h ATR):")
            logger.info(f"   TP Price: ${tp_price:.2f}")
            logger.info(f"   SL Price: ${sl_price:.2f}")
            
            return params
            
        except Exception as e:
            logger.error(f"❌ Error creating TP/SL parameters for {coin_symbol}: {str(e)}")
            return {}
    
    def validate_tp_sl_logic(self, coin_symbol: str, position_side: str, 
                           entry_price: float, tp_price: float, sl_price: float) -> bool:
        """
        Validate TP/SL logic makes sense
        
        Args:
            coin_symbol (str): Trading symbol
            position_side (str): 'long' or 'short'
            entry_price (float): Entry price
            tp_price (float): Take profit price
            sl_price (float): Stop loss price
            
        Returns:
            bool: True if logic is valid
        """
        try:
            position_side_lower = position_side.lower()
            
            if position_side_lower == 'long':
                # For long positions: TP > entry > SL
                if tp_price <= entry_price:
                    logger.error(f"❌ Invalid LONG TP/SL: TP ({tp_price}) should be > entry ({entry_price})")
                    return False
                if sl_price >= entry_price:
                    logger.error(f"❌ Invalid LONG TP/SL: SL ({sl_price}) should be < entry ({entry_price})")
                    return False
                    
            elif position_side_lower == 'short':
                # For short positions: SL > entry > TP
                if tp_price >= entry_price:
                    logger.error(f"❌ Invalid SHORT TP/SL: TP ({tp_price}) should be < entry ({entry_price})")
                    return False
                if sl_price <= entry_price:
                    logger.error(f"❌ Invalid SHORT TP/SL: SL ({sl_price}) should be > entry ({entry_price})")
                    return False
            
            logger.info(f"✅ TP/SL Logic Validation PASSED for {coin_symbol} {position_side}")
            return True
            
        except Exception as e:
            logger.error(f"❌ TP/SL validation error for {coin_symbol}: {str(e)}")
            return False

