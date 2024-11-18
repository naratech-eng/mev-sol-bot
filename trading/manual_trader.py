import os
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass
import logging
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from decimal import Decimal

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
        
    async def get_token_info(self, token_address: str) -> Optional[Dict]:
        """Get token information from the blockchain"""
        try:
            # First check if the address exists
            account_info = await self.client.get_account_info(
                Pubkey.from_string(token_address)
            )
            
            if not account_info or not account_info.value:
                return None
                
            # Get SOL balance
            sol_balance = account_info.value.lamports / 10**9  # Convert lamports to SOL
            
            # Get all SPL token accounts owned by this address
            token_accounts = []
            try:
                # Get token accounts using SPL token program
                response = await self.client.get_token_accounts_by_owner(
                    Pubkey.from_string(token_address),
                    {"programId": Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")}
                )
                
                if response and hasattr(response, 'value'):
                    for account in response.value:
                        # Get balance for each token account
                        balance = await self.client.get_token_account_balance(
                            Pubkey.from_string(account.pubkey)
                        )
                        if balance and hasattr(balance, 'value'):
                            token_accounts.append({
                                "account": account.pubkey,
                                "amount": balance.value.amount,
                                "decimals": balance.value.decimals,
                                "ui_amount": balance.value.ui_amount
                            })
            except Exception as e:
                logger.error(f"Error getting token accounts: {str(e)}")

            return {
                "address": token_address,
                "exists": True,
                "sol_balance": sol_balance,
                "token_accounts": token_accounts
            }
                
        except Exception as e:
            logger.error(f"Error getting token info: {str(e)}")
            return None

    def get_position_info(self, token_address: str) -> Optional[Position]:
        """Get information about an active position"""
        return self.active_positions.get(token_address)

    def get_pending_orders(self) -> Dict[str, TradeConfig]:
        """Get all pending orders"""
        return self.pending_orders.copy()

    async def market_buy(self, token_address: str, amount: float, 
                        take_profit: Optional[float] = None, 
                        stop_loss: Optional[float] = None) -> bool:
        """Execute immediate market buy"""
        try:
            # Get current price
            current_price = await self._get_token_price(token_address)
            if not current_price:
                logger.error("Could not get current price")
                return False
            
            # Create transaction data
            tx_data = await self._prepare_transaction(token_address, amount, current_price)
            
            # Execute the buy transaction
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
            
    async def _prepare_transaction(self, token_address: str, amount: float, price: float) -> Dict:
        """Prepare transaction with basic parameters"""
        return {
            'token': token_address,
            'amount': amount,
            'price': price,
            'deadline': int(time.time() + 60),  # 1 minute deadline
            'nonce': await self._get_next_nonce(),
            'gas_price': await self._get_optimal_gas_price()
        }

    async def _get_next_nonce(self) -> int:
        # Implement your nonce fetching logic here
        return 0  # Placeholder

    async def _get_optimal_gas_price(self) -> int:
        # Implement your gas price fetching logic here
        return 0  # Placeholder
