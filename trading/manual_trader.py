import os
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass
import logging
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from decimal import Decimal
from strategies.advanced_strategies import (
    SandwichDetector, 
    BackrunOptimizer, 
    FlashbotsIntegration,
    initialize_advanced_strategies
)
import random
import time

logger = logging.getLogger(__name__)

@dataclass
class TradeConfig:
    token_address: str
    amount: float
    price: float
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None

@dataclass
class Position:
    token_address: str
    entry_price: float
    amount: float
    take_profit: Optional[float]
    stop_loss: Optional[float]
    order_type: str  # 'market' or 'limit'

class ManualTrader:
    def __init__(self, rpc_client: AsyncClient):
        self.client = rpc_client
        self.active_positions: Dict[str, Position] = {}
        self.pending_orders: Dict[str, TradeConfig] = {}
        
        # Initialize advanced protection strategies
        strategies = initialize_advanced_strategies(
            config_path=os.getenv("CONFIG_PATH", "config.json"),
            rpc_endpoints=[os.getenv("ALCHEMY_RPC_URL")]
        )
        self.sandwich_detector = strategies['sandwich_detector']
        self.backrun_optimizer = strategies['backrun_optimizer']
        self.flashbots = strategies['flashbots']
        
    async def market_buy(self, token_address: str, amount: float, 
                        take_profit: Optional[float] = None, 
                        stop_loss: Optional[float] = None) -> bool:
        """Execute immediate market buy with MEV protection"""
        try:
            # Get current price
            current_price = await self._get_token_price(token_address)
            if not current_price:
                logger.error("Could not get current price")
                return False
            
            # Create transaction data
            tx_data = await self._prepare_transaction(token_address, amount, current_price)
            
            # Check for sandwich attacks
            if await self.sandwich_detector.detect_sandwich_attempt(tx_data):
                logger.warning("Potential sandwich attack detected! Adjusting transaction...")
                tx_data = await self._adjust_for_sandwich(tx_data)
            
            # Optimize transaction timing
            optimal_params = await self.backrun_optimizer.optimize_backrun(tx_data)
            if optimal_params:
                logger.info("Using optimized transaction parameters")
                tx_data.update(optimal_params)
            
            # Submit via Flashbots if available
            if self.flashbots.endpoint:
                success = await self._execute_via_flashbots(tx_data)
            else:
                success = await self._execute_buy(token_address, amount, current_price)
                
            if success:
                self.active_positions[token_address] = Position(
                    token_address=token_address,
                    entry_price=current_price,
                    amount=amount,
                    take_profit=take_profit,
                    stop_loss=stop_loss,
                    order_type='market'
                )
                logger.info(f"Market buy executed successfully at {current_price}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error in market buy: {str(e)}")
            return False

    async def _execute_via_flashbots(self, tx_data: Dict) -> bool:
        """Execute transaction through Flashbots bundle"""
        try:
            bundle = await self._prepare_bundle(tx_data)
            return await self.flashbots.submit_bundle(bundle)
        except Exception as e:
            logger.error(f"Flashbots execution failed: {str(e)}")
            return False
            
    async def _adjust_for_sandwich(self, tx_data: Dict) -> Dict:
        """Adjust transaction parameters to prevent sandwich attack"""
        # Increase slippage tolerance
        tx_data['slippage'] = min(tx_data.get('slippage', 0.01) * 1.5, 0.05)
        
        # Add random delay
        tx_data['delay'] = asyncio.sleep(random.uniform(0.1, 2.0))
        
        # Split into smaller transactions if amount is large
        if tx_data['amount'] > float(os.getenv("LARGE_TX_THRESHOLD", "1000")):
            tx_data['split'] = True
            tx_data['split_count'] = 3
            
        return tx_data
            
    async def _prepare_transaction(self, token_address: str, amount: float, price: float) -> Dict:
        """Prepare transaction with MEV-resistant parameters"""
        return {
            'token': token_address,
            'amount': amount,
            'price': price,
            'slippage': float(os.getenv("DEFAULT_SLIPPAGE", "0.01")),
            'deadline': int(time.time() + 60),  # 1 minute deadline
            'nonce': await self._get_next_nonce(),
            'gas_price': await self._get_optimal_gas_price()
        }

    async def limit_buy(self, token_address: str, amount: float, price: float,
                       take_profit: Optional[float] = None,
                       stop_loss: Optional[float] = None) -> bool:
        """Place limit buy order at support level"""
        try:
            logger.info(f"Setting limit buy for {amount} tokens at {price}")
            
            # Add to pending orders
            self.pending_orders[token_address] = TradeConfig(
                token_address=token_address,
                amount=amount,
                price=price,
                take_profit=take_profit,
                stop_loss=stop_loss
            )
            
            # Start monitoring for limit price
            asyncio.create_task(self._monitor_limit_order(token_address))
            return True
            
        except Exception as e:
            logger.error(f"Error setting limit buy: {str(e)}")
            return False
            
    async def market_sell(self, token_address: str, amount: Optional[float] = None) -> bool:
        """Execute immediate market sell"""
        try:
            position = self.active_positions.get(token_address)
            if not position:
                logger.error("No active position found")
                return False
                
            sell_amount = amount if amount else position.amount
            current_price = await self._get_token_price(token_address)
            
            if not current_price:
                logger.error("Could not get current price")
                return False
                
            logger.info(f"Executing market sell for {sell_amount} tokens at {current_price}")
            
            # Execute the sell transaction
            success = await self._execute_sell(token_address, sell_amount, current_price)
            if success:
                if amount is None or amount >= position.amount:
                    del self.active_positions[token_address]
                else:
                    position.amount -= amount
                logger.info(f"Market sell executed successfully at {current_price}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error in market sell: {str(e)}")
            return False
            
    async def update_tp_sl(self, token_address: str, 
                          take_profit: Optional[float] = None,
                          stop_loss: Optional[float] = None) -> bool:
        """Update take-profit and stop-loss levels"""
        try:
            position = self.active_positions.get(token_address)
            if not position:
                logger.error("No active position found")
                return False
                
            if take_profit is not None:
                position.take_profit = take_profit
                logger.info(f"Updated take-profit to {take_profit}")
                
            if stop_loss is not None:
                position.stop_loss = stop_loss
                logger.info(f"Updated stop-loss to {stop_loss}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error updating TP/SL: {str(e)}")
            return False
            
    async def cancel_limit_order(self, token_address: str) -> bool:
        """Cancel pending limit order"""
        try:
            if token_address in self.pending_orders:
                del self.pending_orders[token_address]
                logger.info(f"Cancelled limit order for {token_address}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling limit order: {str(e)}")
            return False
            
    async def _monitor_limit_order(self, token_address: str):
        """Monitor price for limit order execution"""
        try:
            while token_address in self.pending_orders:
                current_price = await self._get_token_price(token_address)
                order = self.pending_orders[token_address]
                
                if current_price and current_price <= order.price:
                    # Execute the limit order
                    success = await self._execute_buy(
                        token_address, 
                        order.amount,
                        order.price
                    )
                    
                    if success:
                        self.active_positions[token_address] = Position(
                            token_address=token_address,
                            entry_price=order.price,
                            amount=order.amount,
                            take_profit=order.take_profit,
                            stop_loss=order.stop_loss,
                            order_type='limit'
                        )
                        del self.pending_orders[token_address]
                        logger.info(f"Limit order executed at {order.price}")
                        break
                        
                await asyncio.sleep(1)  # Check every second
                
        except Exception as e:
            logger.error(f"Error monitoring limit order: {str(e)}")
            
    async def _execute_buy(self, token_address: str, amount: float, price: float) -> bool:
        """Execute buy transaction"""
        try:
            # Implement your buy transaction logic here
            # This should integrate with your existing DEX interaction code
            return True
            
        except Exception as e:
            logger.error(f"Error executing buy: {str(e)}")
            return False
            
    async def _execute_sell(self, token_address: str, amount: float, price: float) -> bool:
        """Execute sell transaction"""
        try:
            # Implement your sell transaction logic here
            # This should integrate with your existing DEX interaction code
            return True
            
        except Exception as e:
            logger.error(f"Error executing sell: {str(e)}")
            return False
            
    async def _get_token_price(self, token_address: str) -> Optional[float]:
        """Get current token price"""
        try:
            # Implement your price fetching logic here
            # This should use your existing price feed
            return 0.0  # Placeholder
            
        except Exception as e:
            logger.error(f"Error getting token price: {str(e)}")
            return None
            
    def get_position_info(self, token_address: str) -> Optional[Dict]:
        """Get information about current position"""
        position = self.active_positions.get(token_address)
        if not position:
            return None
            
        return {
            "token_address": position.token_address,
            "entry_price": position.entry_price,
            "current_amount": position.amount,
            "take_profit": position.take_profit,
            "stop_loss": position.stop_loss,
            "order_type": position.order_type
        }
        
    def get_pending_orders(self) -> Dict[str, Dict]:
        """Get all pending limit orders"""
        return {
            addr: {
                "amount": order.amount,
                "price": order.price,
                "take_profit": order.take_profit,
                "stop_loss": order.stop_loss
            }
            for addr, order in self.pending_orders.items()
        }

    async def _get_next_nonce(self) -> int:
        # Implement your nonce fetching logic here
        return 0  # Placeholder

    async def _get_optimal_gas_price(self) -> int:
        # Implement your gas price fetching logic here
        return 0  # Placeholder

    async def _prepare_bundle(self, tx_data: Dict) -> Dict:
        # Implement your bundle preparation logic here
        return {}  # Placeholder
