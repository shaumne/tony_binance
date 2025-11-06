#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CoinConfigManager:
    """
    Central Coin Configuration Management System for Binance
    Handles standardized config for ANY coin
    Prevents order size calculation errors
    Scalable for new coins without code changes
    """
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Default values for ANY coin
        self.defaults = {
            'order_size_percentage': 10.0,
            'leverage': 10,
            'atr_period': 14,
            'atr_tp_multiplier': 2.5,
            'atr_sl_multiplier': 3.0,
            'enable_trading': True
        }
        
    def extract_coin_type(self, symbol: str) -> str:
        """
        Extract coin type from Binance symbol
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT', 'ETHUSDC', 'SOLUSDT')
            
        Returns:
            str: Clean coin type (e.g., 'btc', 'ethusdc', 'sol')
        """
        # Remove any whitespace
        clean_symbol = symbol.upper().strip()
        
        # For USDC pairs, keep the USDC suffix to distinguish from USDT pairs
        # e.g., ETHUSDC -> ethusdc (different from ETH/ETHUSDT -> eth)
        if 'USDC' in clean_symbol and not clean_symbol.endswith('USDC'):
            # Handle cases like BTCUSDCPERP by removing PERP
            clean_symbol = clean_symbol.replace('PERP', '')
        
        if clean_symbol.endswith('USDC'):
            # Keep full symbol as coin type for USDC pairs
            coin_type = clean_symbol.lower()
        else:
            # For USDT pairs, remove USDT suffix
            clean_symbol = clean_symbol.replace('USDT', '').replace('PERP', '')
            coin_type = clean_symbol.lower()
        
        logger.debug(f"Extracted coin type '{coin_type}' from symbol '{symbol}'")
        return coin_type
    
    def get_product_type(self, symbol: str) -> str:
        """
        Determine product type based on symbol
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            str: Product type ('USDT-FUTURES' or 'USDC-FUTURES')
        """
        symbol_upper = symbol.upper().strip()
        
        if symbol_upper.endswith('USDC') or 'USDC' in symbol_upper:
            product_type = 'USDC-FUTURES'
        else:
            product_type = 'USDT-FUTURES'
        
        logger.debug(f"Product type for '{symbol}': {product_type}")
        return product_type
    
    def get_coin_config(self, symbol: str) -> Dict[str, Any]:
        """
        Get complete configuration for any coin with fallbacks
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            Dict[str, Any]: Complete coin configuration
        """
        coin_type = self.extract_coin_type(symbol)
        
        # Build coin config with fallbacks
        coin_config = {}
        
        for key, default_value in self.defaults.items():
            # Try coin-specific config first
            config_key = f'{coin_type}_{key}'
            coin_value = self.config.get(config_key)
            
            if coin_value is not None:
                # Validate and convert the value
                try:
                    if key in ['order_size_percentage', 'atr_tp_multiplier', 'atr_sl_multiplier']:
                        coin_config[key] = float(coin_value)
                    elif key in ['leverage', 'atr_period']:
                        coin_config[key] = int(float(coin_value))
                    elif key == 'enable_trading':
                        coin_config[key] = bool(coin_value)
                    else:
                        coin_config[key] = coin_value
                        
                    logger.debug(f"Using {coin_type} specific {key}: {coin_config[key]}")
                except (TypeError, ValueError) as e:
                    logger.warning(f"Invalid {config_key} value: {coin_value}, using default: {default_value}")
                    coin_config[key] = default_value
            else:
                # Use default value
                coin_config[key] = default_value
                logger.debug(f"Using default {key} for {coin_type}: {default_value}")
        
        # Add coin type and product type for reference
        coin_config['coin_type'] = coin_type
        coin_config['symbol'] = symbol
        coin_config['productType'] = self.get_product_type(symbol)
        
        logger.info(f"📊 Final Config for {symbol} ({coin_type}):")
        logger.info(f"   💰 Order Size: {coin_config['order_size_percentage']}%")
        logger.info(f"   🔥 Leverage: {coin_config['leverage']}x")
        logger.info(f"   🎯 TP Multiplier: {coin_config['atr_tp_multiplier']}x")
        logger.info(f"   🛡️ SL Multiplier: {coin_config['atr_sl_multiplier']}x")
        logger.info(f"   📈 Trading Enabled: {coin_config['enable_trading']}")
        logger.info(f"   📦 Product Type: {coin_config['productType']}")
        
        return coin_config
    
    def validate_order_size_calculation(self, symbol: str, balance: float, 
                                       expected_percentage: float) -> Dict[str, Any]:
        """
        Validate and calculate order size with detailed logging
        
        Args:
            symbol (str): Trading symbol
            balance (float): Account balance
            expected_percentage (float): Expected order size percentage
            
        Returns:
            Dict[str, Any]: Order calculation results
        """
        try:
            coin_config = self.get_coin_config(symbol)
            
            # Get the actual percentage from config
            actual_percentage = coin_config['order_size_percentage']
            leverage = coin_config['leverage']
            
            # Calculate order amounts
            base_order_amount = balance * (actual_percentage / 100)
            leveraged_amount = base_order_amount * leverage
            
            # Check if there's a mismatch
            percentage_mismatch = abs(actual_percentage - expected_percentage) > 0.01
            
            result = {
                'symbol': symbol,
                'coin_type': coin_config['coin_type'],
                'balance': balance,
                'expected_percentage': expected_percentage,
                'actual_percentage': actual_percentage,
                'percentage_mismatch': percentage_mismatch,
                'base_order_amount': base_order_amount,
                'leverage': leverage,
                'leveraged_amount': leveraged_amount,
                'config_source': 'coin_specific' if f"{coin_config['coin_type']}_order_size_percentage" in self.config else 'default'
            }
            
            # Log detailed information
            logger.info(f"💰 Order Size Validation for {symbol}:")
            logger.info(f"   Account Balance: ${balance:.2f}")
            logger.info(f"   Expected %: {expected_percentage}%")
            logger.info(f"   Actual %: {actual_percentage}%")
            logger.info(f"   Config Source: {result['config_source']}")
            logger.info(f"   Base Order: ${base_order_amount:.2f}")
            logger.info(f"   Leverage: {leverage}x")
            logger.info(f"   Final Amount: ${leveraged_amount:.2f}")
            
            if percentage_mismatch:
                logger.warning(f"⚠️ ORDER SIZE MISMATCH DETECTED:")
                logger.warning(f"   Expected: {expected_percentage}% -> Got: {actual_percentage}%")
                logger.warning(f"   This explains why {symbol} is using wrong order size!")
            else:
                logger.info(f"✅ Order size percentage matches expectation")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error validating order size for {symbol}: {str(e)}")
            return {'error': str(e)}
    
    def is_trading_enabled(self, symbol: str) -> bool:
        """
        Check if trading is enabled for a specific coin
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            bool: True if trading is enabled
        """
        coin_config = self.get_coin_config(symbol)
        enabled = coin_config['enable_trading']
        
        logger.info(f"Trading status for {symbol}: {'ENABLED' if enabled else 'DISABLED'}")
        return enabled

