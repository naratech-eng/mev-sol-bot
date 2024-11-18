#!/usr/bin/env python3

import asyncio
import json
import os
from typing import Dict
import logging
from dotenv import load_dotenv
from solders.pubkey import Pubkey

from mev_bot import MEVBot
from strategies.advanced_strategies import TokenWhitelist

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='mev_bot.log'
)
logger = logging.getLogger(__name__)

async def validate_contract_address(address: str) -> bool:
    """Validate if the provided address is a valid Solana contract"""
    try:
        # Convert to Pubkey to validate format
        pubkey = Pubkey.from_string(address)
        return True
    except Exception as e:
        logger.error(f"Invalid contract address: {str(e)}")
        return False

async def get_token_info() -> Dict:
    """Get token information from user"""
    print("\n=== Token Configuration ===")
    
    while True:
        symbol = input("Enter token symbol (e.g., SOL): ").upper()
        address = input("Enter token contract address: ")
        
        if not await validate_contract_address(address):
            print("Invalid contract address. Please try again.")
            continue
            
        name = input("Enter token name: ")
        while True:
            try:
                decimals = int(input("Enter token decimals: "))
                break
            except ValueError:
                print("Please enter a valid number for decimals.")
        
        while True:
            try:
                min_liquidity = float(input("Enter minimum liquidity (default 1000.0): ") or "1000.0")
                break
            except ValueError:
                print("Please enter a valid number for minimum liquidity.")
        
        return {
            'symbol': symbol,
            'address': address,
            'name': name,
            'decimals': decimals,
            'min_liquidity': min_liquidity
        }

async def get_dex_config() -> Dict:
    """Get DEX configuration from user"""
    print("\n=== DEX Configuration ===")
    dex_configs = {}
    
    while True:
        dex_name = input("Enter DEX name (e.g., raydium, orca) or press Enter to finish: ").lower()
        if not dex_name:
            break
            
        while True:
            pool_address = input(f"Enter pool address for {dex_name}: ")
            if await validate_contract_address(pool_address):
                break
            print("Invalid pool address. Please try again.")
        
        dex_configs[dex_name] = {
            'pool_address': pool_address,
            'enabled': True
        }
    
    return dex_configs

async def setup_trading_pair(whitelist: TokenWhitelist):
    """Setup trading pair configuration"""
    print("\n=== Trading Pair Configuration ===")
    
    # Show available tokens
    print("\nAvailable tokens:")
    for symbol in whitelist.tokens.keys():
        print(f"- {symbol}")
    
    while True:
        base = input("\nEnter base token symbol: ").upper()
        quote = input("Enter quote token symbol: ").upper()
        
        if base not in whitelist.tokens or quote not in whitelist.tokens:
            print("One or both tokens not in whitelist. Please try again.")
            continue
        
        dex_configs = await get_dex_config()
        if dex_configs:
            whitelist.add_pair(base, quote, dex_configs)
            break
        else:
            print("At least one DEX configuration is required.")

async def main():
    try:
        # Load configuration
        load_dotenv()
        config_path = "config/token_whitelist.json"
        
        # Initialize whitelist
        whitelist = TokenWhitelist(config_path)
        
        while True:
            print("\n=== Solana MEV Bot Configuration ===")
            print("1. Add new token")
            print("2. Setup trading pair")
            print("3. Start bot")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ")
            
            if choice == "1":
                token_info = await get_token_info()
                whitelist.add_token(**token_info)
                whitelist.save_config(config_path)
                print(f"\nToken {token_info['symbol']} added successfully!")
                
            elif choice == "2":
                await setup_trading_pair(whitelist)
                whitelist.save_config(config_path)
                print("\nTrading pair added successfully!")
                
            elif choice == "3":
                if not whitelist.pairs:
                    print("\nNo trading pairs configured. Please set up at least one pair first.")
                    continue
                    
                print("\nStarting MEV bot...")
                bot = MEVBot()
                await bot.start()
                
            elif choice == "4":
                print("\nExiting...")
                break
                
            else:
                print("\nInvalid choice. Please try again.")
    
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
