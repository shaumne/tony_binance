#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PositionValidator:
    """
    Position Duplication Prevention System for Binance
    Prevents multiple positions in same direction
    Handles timing-based conflicts
    Validates position logic before execution
    """
    
    def __init__(self):
        self.recent_orders = {}  # Track recent orders to prevent duplicates
        self.order_cooldown = 5  # Seconds between same orders
        self.position_locks = {}  # Symbol-based locks for concurrent protection
        
    def validate_position_request(self, symbol: str, direction: str, action: str,
                                 current_positions: List[Dict], auto_position_switch: bool = True) -> Dict[str, any]:
        """
        Validate if a position request should be allowed
        
        Args:
            symbol (str): Trading symbol (e.g., 'BTCUSDT', 'ETHUSDC')
            direction (str): Position direction ('LONG' or 'SHORT')
            action (str): Action type ('open' or 'close')
            current_positions (List[Dict]): List of current open positions
            auto_position_switch (bool): Whether auto position switch is enabled
            
        Returns:
            Dict[str, any]: Validation result with status and reason
        """
        try:
            validation_result = {
                'allowed': False,
                'reason': '',
                'action_required': None,
                'existing_positions': [],
                'conflicts': []
            }
            
            logger.info(f"🔍 Validating position request: {symbol}/{direction}/{action}")
            
            # Check for recent duplicate orders
            duplicate_check = self._check_duplicate_order(symbol, direction, action)
            if not duplicate_check['allowed']:
                validation_result.update(duplicate_check)
                return validation_result
            
            # Analyze current positions for this symbol
            symbol_positions = self._analyze_symbol_positions(symbol, current_positions)
            validation_result['existing_positions'] = symbol_positions
            
            if action == 'open':
                result = self._validate_open_position(symbol, direction, symbol_positions, auto_position_switch)
            elif action == 'close':
                result = self._validate_close_position(symbol, direction, symbol_positions)
            else:
                result = {
                    'allowed': False,
                    'reason': f"Invalid action: {action}",
                    'action_required': None
                }
            
            validation_result.update(result)
            
            # Log validation result
            if validation_result['allowed']:
                logger.info(f"✅ Position request APPROVED: {symbol}/{direction}/{action}")
                if validation_result.get('action_required'):
                    logger.info(f"   Required action: {validation_result['action_required']}")
            else:
                logger.warning(f"❌ Position request REJECTED: {symbol}/{direction}/{action}")
                logger.warning(f"   Reason: {validation_result['reason']}")
            
            # Record this request to prevent duplicates
            if validation_result['allowed']:
                self._record_order_request(symbol, direction, action)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"❌ Error validating position request: {str(e)}")
            return {
                'allowed': False,
                'reason': f"Validation error: {str(e)}",
                'action_required': None
            }
    
    def _check_duplicate_order(self, symbol: str, direction: str, action: str) -> Dict[str, any]:
        """
        Check for recent duplicate orders
        
        Args:
            symbol (str): Trading symbol
            direction (str): Position direction
            action (str): Action type
            
        Returns:
            Dict[str, any]: Duplicate check result
        """
        order_key = f"{symbol}_{direction}_{action}"
        current_time = time.time()
        
        if order_key in self.recent_orders:
            last_order_time = self.recent_orders[order_key]
            time_diff = current_time - last_order_time
            
            if time_diff < self.order_cooldown:
                return {
                    'allowed': False,
                    'reason': f"Duplicate order blocked. Last order was {time_diff:.1f}s ago (cooldown: {self.order_cooldown}s)",
                    'action_required': None
                }
        
        return {'allowed': True, 'reason': '', 'action_required': None}
    
    def _analyze_symbol_positions(self, symbol: str, current_positions: List[Dict]) -> List[Dict]:
        """
        Analyze current positions for a specific symbol
        
        Args:
            symbol (str): Trading symbol
            current_positions (List[Dict]): All current positions
            
        Returns:
            List[Dict]: Positions for this symbol with analysis
        """
        symbol_positions = []
        
        for pos in current_positions:
            # Binance position format
            pos_symbol = pos.get('symbol', '')
            pos_side = pos.get('positionSide', '').upper()
            pos_size = abs(float(pos.get('positionAmt', '0')))
            
            if pos_symbol == symbol and pos_size > 0:
                analyzed_pos = {
                    'symbol': pos_symbol,
                    'side': pos_side.lower(),
                    'size': pos_size,
                    'entry_price': float(pos.get('entryPrice', '0')),
                    'unrealized_pnl': float(pos.get('unrealizedProfit', '0')),
                    'leverage': int(pos.get('leverage', '1')),
                    'margin_type': pos.get('marginType', 'cross')
                }
                symbol_positions.append(analyzed_pos)
        
        if symbol_positions:
            logger.info(f"📊 Found {len(symbol_positions)} existing positions for {symbol}:")
            for pos in symbol_positions:
                logger.info(f"   {pos['side'].upper()}: {pos['size']} @ ${pos['entry_price']:.2f} (PnL: ${pos['unrealized_pnl']:.2f})")
        else:
            logger.info(f"📊 No existing positions found for {symbol}")
        
        return symbol_positions
    
    def _validate_open_position(self, symbol: str, direction: str, 
                               existing_positions: List[Dict], auto_position_switch: bool = True) -> Dict[str, any]:
        """
        Validate opening a new position
        
        Args:
            symbol (str): Trading symbol
            direction (str): Position direction
            existing_positions (List[Dict]): Existing positions for this symbol
            auto_position_switch (bool): Whether auto position switch is enabled
            
        Returns:
            Dict[str, any]: Validation result
        """
        # Check for existing positions in same direction
        same_direction_positions = [p for p in existing_positions if p['side'] == direction.lower()]
        opposite_direction_positions = [p for p in existing_positions if p['side'] != direction.lower()]
        
        if same_direction_positions:
            # Already have position in same direction - block it
            return {
                'allowed': False,
                'reason': f"Already have {direction.upper()} position for {symbol}",
                'action_required': None,
                'conflicts': same_direction_positions
            }
        
        if opposite_direction_positions:
            # CRITICAL FIX: Check auto_position_switch setting
            if not auto_position_switch:
                return {
                    'allowed': False,
                    'reason': f"Auto position switch disabled - cannot open {direction.upper()} position while {opposite_direction_positions[0]['side'].upper()} position exists for {symbol}",
                    'action_required': None,
                    'conflicts': opposite_direction_positions
                }
            
            # Auto position switch enabled - allow closing opposite position
            return {
                'allowed': True,
                'reason': f"Auto position switch enabled - will close existing {opposite_direction_positions[0]['side'].upper()} position before opening {direction.upper()}",
                'action_required': {
                    'type': 'close_opposite',
                    'positions_to_close': opposite_direction_positions,
                    'new_direction': direction
                }
            }
        
        # No existing positions - safe to open
        return {
            'allowed': True,
            'reason': f"No existing positions for {symbol}, safe to open {direction.upper()}",
            'action_required': None
        }
    
    def _validate_close_position(self, symbol: str, direction: str,
                                existing_positions: List[Dict]) -> Dict[str, any]:
        """
        Validate closing a position
        
        Args:
            symbol (str): Trading symbol
            direction (str): Position direction to close
            existing_positions (List[Dict]): Existing positions for this symbol
            
        Returns:
            Dict[str, any]: Validation result
        """
        # Check for positions in the direction we want to close
        matching_positions = [p for p in existing_positions if p['side'] == direction.lower()]
        
        if not matching_positions:
            return {
                'allowed': False,
                'reason': f"No {direction.upper()} position found for {symbol} to close",
                'action_required': None
            }
        
        return {
            'allowed': True,
            'reason': f"Found {len(matching_positions)} {direction.upper()} position(s) to close",
            'action_required': {
                'type': 'close_positions',
                'positions_to_close': matching_positions
            }
        }
    
    def _record_order_request(self, symbol: str, direction: str, action: str) -> None:
        """
        Record order request to prevent duplicates
        
        Args:
            symbol (str): Trading symbol
            direction (str): Position direction
            action (str): Action type
        """
        order_key = f"{symbol}_{direction}_{action}"
        self.recent_orders[order_key] = time.time()
        
        # Clean old entries (older than 1 minute)
        current_time = time.time()
        keys_to_remove = []
        for key, timestamp in self.recent_orders.items():
            if current_time - timestamp > 60:  # 1 minute
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.recent_orders[key]
    
    def detect_position_conflicts(self, current_positions: List[Dict]) -> List[Dict]:
        """
        Detect conflicting positions (e.g., both long and short for same symbol)
        
        Args:
            current_positions (List[Dict]): All current positions
            
        Returns:
            List[Dict]: List of conflicts detected
        """
        conflicts = []
        
        # Group positions by symbol
        symbol_groups = {}
        for pos in current_positions:
            symbol = pos.get('symbol', '')
            size = abs(float(pos.get('positionAmt', '0')))
            
            if size > 0:
                if symbol not in symbol_groups:
                    symbol_groups[symbol] = []
                symbol_groups[symbol].append(pos)
        
        # Check for conflicts in each symbol group
        for symbol, positions in symbol_groups.items():
            if len(positions) > 1:
                # Multiple positions for same symbol
                sides = [pos.get('positionSide', '').upper() for pos in positions]
                unique_sides = set(sides)
                
                if len(unique_sides) > 1:
                    # Both long and short positions exist
                    conflict = {
                        'type': 'opposite_positions',
                        'symbol': symbol,
                        'positions': positions,
                        'sides': list(unique_sides),
                        'severity': 'high',
                        'description': f"Both LONG and SHORT positions exist for {symbol}"
                    }
                    conflicts.append(conflict)
                    logger.warning(f"⚠️ CONFLICT DETECTED: Both LONG and SHORT positions for {symbol}")
                    
                elif len(positions) > 1 and len(unique_sides) == 1:
                    # Multiple positions in same direction
                    conflict = {
                        'type': 'duplicate_positions',
                        'symbol': symbol,
                        'positions': positions,
                        'sides': list(unique_sides),
                        'severity': 'medium',
                        'description': f"Multiple {unique_sides.pop().upper()} positions for {symbol}"
                    }
                    conflicts.append(conflict)
                    logger.warning(f"⚠️ DUPLICATE POSITIONS: Multiple {sides[0].upper()} positions for {symbol}")
        
        if conflicts:
            logger.warning(f"🚨 DETECTED {len(conflicts)} POSITION CONFLICTS:")
            for conflict in conflicts:
                logger.warning(f"   {conflict['description']}")
        else:
            logger.info(f"✅ No position conflicts detected")
        
        return conflicts
    
    def get_position_summary(self, current_positions: List[Dict]) -> Dict[str, any]:
        """
        Get a summary of current positions with conflict analysis
        
        Args:
            current_positions (List[Dict]): All current positions
            
        Returns:
            Dict[str, any]: Position summary
        """
        summary = {
            'total_positions': 0,
            'symbols': {},
            'conflicts': [],
            'warnings': []
        }
        
        for pos in current_positions:
            symbol = pos.get('symbol', '')
            side = pos.get('positionSide', '').upper()
            size = abs(float(pos.get('positionAmt', '0')))
            
            if size > 0:
                summary['total_positions'] += 1
                
                if symbol not in summary['symbols']:
                    summary['symbols'][symbol] = {'LONG': [], 'SHORT': []}
                
                summary['symbols'][symbol][side].append({
                    'size': size,
                    'entry_price': float(pos.get('entryPrice', '0')),
                    'unrealized_pnl': float(pos.get('unrealizedProfit', '0'))
                })
        
        # Detect conflicts
        summary['conflicts'] = self.detect_position_conflicts(current_positions)
        
        # Generate warnings
        for symbol, positions in summary['symbols'].items():
            if positions['LONG'] and positions['SHORT']:
                summary['warnings'].append(f"Both LONG and SHORT positions for {symbol}")
            elif len(positions['LONG']) > 1:
                summary['warnings'].append(f"Multiple LONG positions for {symbol}")
            elif len(positions['SHORT']) > 1:
                summary['warnings'].append(f"Multiple SHORT positions for {symbol}")
        
        return summary

