import base58
from typing import List, Dict, Optional, Tuple
from solders.pubkey import Pubkey
from solana.transaction import Transaction
from solana.rpc.async_api import AsyncClient

async def get_token_balance(
    client: AsyncClient,
    token_account: Pubkey
) -> Optional[float]:
    """Get the balance of a token account"""
    try:
        response = await client.get_token_account_balance(token_account)
        if response.value:
            return float(response.value.amount) / (10 ** response.value.decimals)
        return None
    except Exception as e:
        return None

async def get_multiple_accounts(
    client: AsyncClient,
    pubkeys: List[Pubkey]
) -> List[Optional[Dict]]:
    """Get multiple account infos in a single RPC call"""
    try:
        response = await client.get_multiple_accounts(pubkeys)
        return response.value
    except Exception as e:
        return [None] * len(pubkeys)

def estimate_price_impact(
    input_amount: float,
    input_reserve: float,
    output_reserve: float
) -> float:
    """
    Estimate price impact of a swap
    Returns the price impact as a percentage
    """
    if input_amount <= 0 or input_reserve <= 0 or output_reserve <= 0:
        return 0
    
    # Using constant product formula (x * y = k)
    k = input_reserve * output_reserve
    new_input_reserve = input_reserve + input_amount
    new_output_reserve = k / new_input_reserve
    
    # Calculate price impact
    price_impact = (output_reserve - new_output_reserve) / output_reserve * 100
    return price_impact

async def simulate_transaction(
    client: AsyncClient,
    transaction: Transaction,
    signers: List[bytes]
) -> Tuple[bool, Optional[str]]:
    """
    Simulate a transaction before sending
    Returns (success, error_message)
    """
    try:
        resp = await client.simulate_transaction(transaction, signers=signers)
        if resp.value.err:
            return False, str(resp.value.err)
        return True, None
    except Exception as e:
        return False, str(e)

def calculate_profit(
    input_amount: float,
    output_amount: float,
    gas_cost: float
) -> float:
    """
    Calculate the profit of a trade
    Returns the profit percentage
    """
    if input_amount <= 0:
        return 0
    
    net_output = output_amount - gas_cost
    profit_percentage = ((net_output - input_amount) / input_amount) * 100
    return profit_percentage

def encode_instruction_data(instruction_data: bytes) -> str:
    """Encode instruction data to base58 format"""
    return base58.b58encode(instruction_data).decode('ascii')

def decode_instruction_data(encoded_data: str) -> bytes:
    """Decode base58 instruction data"""
    return base58.b58decode(encoded_data)
