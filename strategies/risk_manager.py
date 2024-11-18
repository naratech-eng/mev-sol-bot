import os
import time
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TokenPosition:
    token_address: str
    entry_price: float
    current_price: float
    quantity: float
    highest_price: float
    entry_time: float

class RiskManager:
    def __init__(self):
        # Stop loss parameters
        self.stop_loss_threshold = float(os.getenv("STOP_LOSS_THRESHOLD", "0.15"))  # 15% drop
        self.trailing_stop_loss = float(os.getenv("TRAILING_STOP_LOSS", "0.10"))    # 10% from highest
        self.max_holding_time = int(os.getenv("MAX_HOLDING_TIME", "3600"))          # 1 hour max hold
        self.quick_loss_threshold = float(os.getenv("QUICK_LOSS_THRESHOLD", "0.05")) # 5% drop in 1 min
        
        # Position tracking
        self.positions: Dict[str, TokenPosition] = {}
        self.price_alerts: Dict[str, float] = {}
        
    async def start_monitoring(self):
        """Start monitoring positions for risk management"""
        while True:
            try:
                await self._check_positions()
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in risk monitoring: {str(e)}")
                await asyncio.sleep(5)
                
    async def _check_positions(self):
        """Check all positions for stop loss conditions"""
        current_time = time.time()
        
        for token_address, position in list(self.positions.items()):
            try:
                # Update current price
                new_price = await self._get_current_price(token_address)
                if new_price is None:
                    continue
                    
                position.current_price = new_price
                
                # Update highest price if new high
                if new_price > position.highest_price:
                    position.highest_price = new_price
                
                # Check stop loss conditions
                await self._check_stop_loss_conditions(token_address, position, current_time)
                
            except Exception as e:
                logger.error(f"Error checking position {token_address}: {str(e)}")
                
    async def _check_stop_loss_conditions(self, token_address: str, position: TokenPosition, current_time: float):
        """Check various stop loss conditions"""
        try:
            # Calculate price drops
            price_drop = (position.entry_price - position.current_price) / position.entry_price
            drop_from_high = (position.highest_price - position.current_price) / position.highest_price
            time_held = current_time - position.entry_time
            
            # Quick loss check (significant drop in short time)
            if time_held <= 60 and price_drop >= self.quick_loss_threshold:
                await self._execute_emergency_sell(token_address, position, "Quick Loss Triggered")
                return
                
            # Regular stop loss
            if price_drop >= self.stop_loss_threshold:
                await self._execute_emergency_sell(token_address, position, "Stop Loss Triggered")
                return
                
            # Trailing stop loss
            if drop_from_high >= self.trailing_stop_loss:
                await self._execute_emergency_sell(token_address, position, "Trailing Stop Loss Triggered")
                return
                
            # Maximum holding time
            if time_held >= self.max_holding_time:
                await self._execute_emergency_sell(token_address, position, "Max Holding Time Reached")
                return
                
        except Exception as e:
            logger.error(f"Error checking stop loss for {token_address}: {str(e)}")
            
    async def _execute_emergency_sell(self, token_address: str, position: TokenPosition, reason: str):
        """Execute emergency sell order"""
        try:
            logger.warning(f"Emergency sell for {token_address}: {reason}")
            logger.info(f"Position details: Entry: ${position.entry_price:.4f}, "
                       f"Current: ${position.current_price:.4f}, "
                       f"Highest: ${position.highest_price:.4f}")
            
            # Implement your sell execution logic here
            # This should integrate with your main trading strategy
            
            # Remove position after successful sell
            del self.positions[token_address]
            
        except Exception as e:
            logger.error(f"Error executing emergency sell for {token_address}: {str(e)}")
            
    async def add_position(self, token_address: str, entry_price: float, quantity: float):
        """Add new position to monitor"""
        self.positions[token_address] = TokenPosition(
            token_address=token_address,
            entry_price=entry_price,
            current_price=entry_price,
            quantity=quantity,
            highest_price=entry_price,
            entry_time=time.time()
        )
        
    async def _get_current_price(self, token_address: str) -> Optional[float]:
        """Get current token price"""
        try:
            # Implement your price fetching logic here
            # This should use your existing price feed
            return 0.0  # Placeholder
            
        except Exception as e:
            logger.error(f"Error getting price for {token_address}: {str(e)}")
            return None
            
    def get_position_status(self, token_address: str) -> Optional[Dict]:
        """Get current position status"""
        if token_address not in self.positions:
            return None
            
        position = self.positions[token_address]
        return {
            "entry_price": position.entry_price,
            "current_price": position.current_price,
            "quantity": position.quantity,
            "highest_price": position.highest_price,
            "time_held": time.time() - position.entry_time,
            "pnl_percent": (position.current_price - position.entry_price) / position.entry_price * 100
        }
