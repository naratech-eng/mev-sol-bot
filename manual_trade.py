#!/usr/bin/env python3
import os
import asyncio
import argparse
from dotenv import load_dotenv
from solana.rpc.async_api import AsyncClient
from trading.manual_trader import ManualTrader

async def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize RPC client
    rpc_url = os.getenv("ALCHEMY_RPC_URL")
    client = AsyncClient(rpc_url)
    
    # Initialize manual trader
    trader = ManualTrader(client)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Manual Solana Trading Bot')
    parser.add_argument('action', choices=['buy', 'sell', 'limit', 'update', 'cancel', 'status'])
    parser.add_argument('--token', required=True, help='Token address')
    parser.add_argument('--amount', type=float, help='Amount to trade')
    parser.add_argument('--price', type=float, help='Price for limit order')
    parser.add_argument('--tp', type=float, help='Take profit price')
    parser.add_argument('--sl', type=float, help='Stop loss price')
    
    args = parser.parse_args()
    
    try:
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
                
        elif args.action == 'status':
            position = trader.get_position_info(args.token)
            if position:
                print(f"Active position: {position}")
            else:
                orders = trader.get_pending_orders()
                if args.token in orders:
                    print(f"Pending order: {orders[args.token]}")
                else:
                    print("No active position or pending orders found")
                    
    except Exception as e:
        print(f"Error: {str(e)}")
        
if __name__ == "__main__":
    asyncio.run(main())
