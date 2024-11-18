import os
import json
import time
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solders.pubkey import Pubkey
import logging

logger = logging.getLogger(__name__)

@dataclass
class NewTokenInfo:
    address: str
    pool_address: str
    initial_liquidity: float
    creation_time: float
    dex_program: str
    initial_price: float
    total_supply: int

class NewTokenMonitor:
    def __init__(self, rpc_clients: List[AsyncClient]):
        self.clients = rpc_clients
        self.primary_client = rpc_clients[0]  # Alchemy client
        self.new_pairs = {}
        self.monitored_programs = json.loads(os.getenv("FACTORY_PROGRAMS", "[]"))
        self.min_liquidity = float(os.getenv("NEW_PAIR_MIN_LIQUIDITY", "1000"))
        self.max_age = int(os.getenv("NEW_PAIR_MAX_AGE", "300"))
        self.max_supply = int(os.getenv("NEW_TOKEN_MAX_SUPPLY", "1000000000"))
        self.max_price = float(os.getenv("MAX_NEW_TOKEN_PRICE", "0.001"))
        
    async def start_monitoring(self):
        """Start monitoring for new token pairs"""
        while True:
            try:
                await self._monitor_new_pairs()
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in new token monitoring: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
                
    async def _monitor_new_pairs(self):
        """Monitor DEX factory programs for new pair creation"""
        for program_id in self.monitored_programs:
            try:
                # Get recent program transactions
                recent_txs = await self.primary_client.get_signatures_for_address(
                    Pubkey.from_string(program_id),
                    commitment=Commitment("confirmed")
                )
                
                for tx in recent_txs.value:
                    if await self._is_pair_creation(tx.signature):
                        pair_info = await self._analyze_new_pair(tx.signature)
                        if pair_info and self._is_valid_new_pair(pair_info):
                            await self._handle_new_pair(pair_info)
                            
            except Exception as e:
                logger.error(f"Error monitoring program {program_id}: {str(e)}")
                
    async def _is_pair_creation(self, tx_sig: str) -> bool:
        """Check if transaction is a pair creation"""
        try:
            tx_info = await self.primary_client.get_transaction(
                tx_sig,
                commitment=Commitment("confirmed")
            )
            
            # Add your logic to detect pair creation
            # This will depend on the specific DEX program
            return False  # Placeholder
            
        except Exception as e:
            logger.error(f"Error checking pair creation: {str(e)}")
            return False
            
    async def _analyze_new_pair(self, tx_sig: str) -> Optional[NewTokenInfo]:
        """Analyze new trading pair details"""
        try:
            tx_info = await self.primary_client.get_transaction(
                tx_sig,
                commitment=Commitment("confirmed")
            )
            
            # Extract token and pool information
            # This is a placeholder - implement actual extraction logic
            token_info = NewTokenInfo(
                address="",
                pool_address="",
                initial_liquidity=0.0,
                creation_time=time.time(),
                dex_program="",
                initial_price=0.0,
                total_supply=0
            )
            
            return token_info
            
        except Exception as e:
            logger.error(f"Error analyzing new pair: {str(e)}")
            return None
            
    def _is_valid_new_pair(self, pair_info: NewTokenInfo) -> bool:
        """Validate if the new pair meets our criteria"""
        current_time = time.time()
        
        return (
            pair_info.initial_liquidity >= self.min_liquidity and
            (current_time - pair_info.creation_time) <= self.max_age and
            pair_info.total_supply <= self.max_supply and
            pair_info.initial_price <= self.max_price
        )
        
    async def _handle_new_pair(self, pair_info: NewTokenInfo):
        """Handle detection of valid new trading pair"""
        try:
            # Log the new pair
            logger.info(f"New valid trading pair detected: {pair_info}")
            
            # Store pair information
            self.new_pairs[pair_info.address] = pair_info
            
            # Trigger buy signal
            await self._execute_initial_buy(pair_info)
            
        except Exception as e:
            logger.error(f"Error handling new pair: {str(e)}")
            
    async def _execute_initial_buy(self, pair_info: NewTokenInfo):
        """Execute initial buy for new token"""
        try:
            initial_amount = float(os.getenv("INITIAL_BUY_AMOUNT", "0.1"))
            
            # Implement your buy execution logic here
            # This should integrate with your main trading strategy
            
            logger.info(f"Executed initial buy for {pair_info.address}")
            
        except Exception as e:
            logger.error(f"Error executing initial buy: {str(e)}")
            
    async def get_recent_pairs(self, max_age: int = 300) -> List[NewTokenInfo]:
        """Get recently detected pairs within specified age"""
        current_time = time.time()
        return [
            pair for pair in self.new_pairs.values()
            if (current_time - pair.creation_time) <= max_age
        ]
