# Manual Trading Commands

This document contains all available commands for the manual trading bot with examples.

## Quick Command Reference

### 1. Market Buy Commands
```bash
# Basic market buy
python3 manual_trade.py buy --token YOUR_TOKEN_ADDRESS --amount 100

# Market buy with Take Profit and Stop Loss
python3 manual_trade.py buy --token YOUR_TOKEN_ADDRESS --amount 100 --tp 1.5 --sl 0.85
```

### 2. Market Sell Commands
```bash
# Sell entire position
python3 manual_trade.py sell --token YOUR_TOKEN_ADDRESS

# Sell specific amount
python3 manual_trade.py sell --token YOUR_TOKEN_ADDRESS --amount 50
```

### 3. Limit Order Commands
```bash
# Place limit buy
python3 manual_trade.py limit --token YOUR_TOKEN_ADDRESS --amount 100 --price 1.0

# Limit buy with TP/SL
python3 manual_trade.py limit --token YOUR_TOKEN_ADDRESS --amount 100 --price 1.0 --tp 1.2 --sl 0.95
```

### 4. Update TP/SL Commands
```bash
# Update both TP and SL
python3 manual_trade.py update --token YOUR_TOKEN_ADDRESS --tp 1.4 --sl 0.9

# Update only TP
python3 manual_trade.py update --token YOUR_TOKEN_ADDRESS --tp 1.4

# Update only SL
python3 manual_trade.py update --token YOUR_TOKEN_ADDRESS --sl 0.9
```

### 5. Cancel Order Commands
```bash
# Cancel limit order
python3 manual_trade.py cancel --token YOUR_TOKEN_ADDRESS
```

### 6. Status Check Commands
```bash
# Check position status
python3 manual_trade.py status --token YOUR_TOKEN_ADDRESS
```

## Parameter Explanations

- `--token`: Your token's address (required for all commands)
- `--amount`: Amount to trade (required for buy/sell)
- `--price`: Price for limit orders
- `--tp`: Take profit price multiplier (e.g., 1.5 = +50%)
- `--sl`: Stop loss price multiplier (e.g., 0.85 = -15%)

## Usage Instructions

1. Copy any command above
2. Replace `YOUR_TOKEN_ADDRESS` with your actual token address
3. Adjust the numbers for your trade:
   - `amount`: How much to trade
   - `price`: For limit orders
   - `tp`: Take profit level
   - `sl`: Stop loss level

## Built-in MEV Protection

The bot automatically includes these protections:
- Sandwich attack detection and prevention
- Transaction timing optimization
- Flashbots integration when available
- Large trade splitting
- Random timing delays

## Examples with Real Values

Here are some examples with realistic values:

```bash
# Buy 1000 tokens with 50% take profit and 15% stop loss
python3 manual_trade.py buy --token So1aNaT0keN123456789 --amount 1000 --tp 1.5 --sl 0.85

# Place limit buy for 500 tokens at 1.2 SOL with 20% TP and 10% SL
python3 manual_trade.py limit --token So1aNaT0keN123456789 --amount 500 --price 1.2 --tp 1.2 --sl 0.9

# Sell 300 tokens from your position
python3 manual_trade.py sell --token So1aNaT0keN123456789 --amount 300
```

## Common Use Cases

1. **Quick Market Entry**
   ```bash
   python3 manual_trade.py buy --token YOUR_TOKEN_ADDRESS --amount 100
   ```

2. **Protected Entry with TP/SL**
   ```bash
   python3 manual_trade.py buy --token YOUR_TOKEN_ADDRESS --amount 100 --tp 1.3 --sl 0.9
   ```

3. **Buy the Dip with Limit Order**
   ```bash
   python3 manual_trade.py limit --token YOUR_TOKEN_ADDRESS --amount 100 --price 0.9 --tp 1.2 --sl 0.85
   ```

4. **Quick Exit**
   ```bash
   python3 manual_trade.py sell --token YOUR_TOKEN_ADDRESS
   ```

5. **Adjust Risk Management**
   ```bash
   python3 manual_trade.py update --token YOUR_TOKEN_ADDRESS --tp 1.5 --sl 0.8
   ```
