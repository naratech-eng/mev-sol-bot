#!/usr/bin/env python3
import os
import asyncio
import argparse
from dotenv import load_dotenv
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from trading.manual_trader import ManualTrader

def is_valid_solana_address(address: str) -> bool:
    try:
        # Try to create a Pubkey object from the address
        Pubkey.from_string(address)
        return True
    except ValueError:
        return False

async def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize RPC client
    rpc_url = os.getenv("ALCHEMY_RPC_URL")
    client = AsyncClient(rpc_url)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Manual Solana Trading Bot')
    parser.add_argument('action', choices=['buy', 'sell', 'limit', 'update', 'cancel', 'status'])
    parser.add_argument('--token', required=True, help='Solana token address (must be a valid Solana public key)')
    parser.add_argument('--amount', type=float, help='Amount to trade')
    parser.add_argument('--price', type=float, help='Price for limit order')
    parser.add_argument('--tp', type=float, help='Take profit price')
    parser.add_argument('--sl', type=float, help='Stop loss price')
    
    args = parser.parse_args()
    
    # Validate Solana address
    if not is_valid_solana_address(args.token):
        print("Error: Invalid Solana address. Please provide a valid Solana token address.")
        print("Example of a valid Solana address: 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU")
        return
    
    try:
        # Initialize manual trader
        trader = ManualTrader(client)
        
        if args.action == 'status':
            # Get token information
            token_info = await trader.get_token_info(args.token)
            if token_info:
                print("\nWallet Information:")
                print(f"Address: {token_info['address']}")
                print(f"SOL Balance: {token_info['sol_balance']:.9f} SOL")
                
                if token_info['token_accounts']:
                    print("\nSPL Token Balances:")
                    for idx, token in enumerate(token_info['token_accounts'], 1):
                        print(f"\n{idx}. Token Account: {token['account']}")
                        print(f"   Amount: {token['ui_amount']} (Raw: {token['amount']})")
                        print(f"   Decimals: {token['decimals']}")
                else:
                    print("\nNo SPL tokens found in this wallet")
                
                # Check for active positions
                position = trader.get_position_info(args.token)
                if position:
                    print("\nActive Position:")
                    print(f"Entry Price: {position.entry_price}")
                    print(f"Amount: {position.amount}")
                    if position.take_profit:
                        print(f"Take Profit: {position.take_profit}")
                    if position.stop_loss:
                        print(f"Stop Loss: {position.stop_loss}")
                    print(f"Order Type: {position.order_type}")
                
                # Check for pending orders
                orders = trader.get_pending_orders()
                if args.token in orders:
                    order = orders[args.token]
                    print("\nPending Order:")
                    print(f"Amount: {order.amount}")
                    print(f"Price: {order.price}")
                    if order.take_profit:
                        print(f"Take Profit: {order.take_profit}")
                    if order.stop_loss:
                        print(f"Stop Loss: {order.stop_loss}")
            else:
                print("No token information available. The token account may not exist or may have no balance.")
            return
            
        # For other actions that require advanced features
        trader = ManualTrader(client)
        
        if args.action == 'buy':
            if not args.amount:
                print("Error: --amount required for buy order")
                return
            success = await trader.market_buy(
                args.token,
                args.amount,
                take_profit=args.tp,
                stop_loss=args.sl
            )
            if success:
                print(f"Market buy executed successfully")
                position = trader.get_position_info(args.token)
                print(f"Position: {position}")
            else:
                print("Market buy failed")
                
        elif args.action == 'sell':
            success = await trader.market_sell(
                args.token,
                amount=args.amount  # Optional, sells entire position if None
            )
            if success:
                print(f"Market sell executed successfully")
            else:
                print("Market sell failed")
                
        elif args.action == 'limit':
            if not all([args.amount, args.price]):
                print("Error: --amount and --price required for limit order")
                return
            success = await trader.limit_buy(
                args.token,
                args.amount,
                args.price,
                take_profit=args.tp,
                stop_loss=args.sl
            )
            if success:
                print(f"Limit order placed successfully")
                orders = trader.get_pending_orders()
                print(f"Pending orders: {orders}")
            else:
                print("Failed to place limit order")
                
        elif args.action == 'update':
            if not (args.tp or args.sl):
                print("Error: --tp or --sl required for update")
                return
            success = await trader.update_tp_sl(
                args.token,
                take_profit=args.tp,
                stop_loss=args.sl
            )
            if success:
                print(f"TP/SL updated successfully")
                position = trader.get_position_info(args.token)
                print(f"Updated position: {position}")
            else:
                print("Failed to update TP/SL")
                
        elif args.action == 'cancel':
            success = await trader.cancel_limit_order(args.token)
            if success:
                print(f"Limit order cancelled successfully")
            else:
                print("No limit order found to cancel")
                
    except Exception as e:
        print(f"Error: {str(e)}")
        
if __name__ == "__main__":
    asyncio.run(main())
