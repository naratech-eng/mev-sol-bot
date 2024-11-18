# Solana Trading Bot with MEV Protection

An advanced trading bot for the Solana blockchain with built-in MEV (Maximal Extractable Value) protection, supporting both automated and manual trading strategies.

## Features

### MEV Protection
- Sandwich attack detection and prevention
- Transaction timing optimization
- Flashbots integration
- Large trade splitting
- Random timing delays

### Trading Capabilities
- Market orders (buy/sell)
- Limit orders
- Take-profit and stop-loss management
- Position tracking
- Order status monitoring

### Risk Management
- Multiple stop-loss types:
  - Regular stop-loss (15% drop)
  - Trailing stop-loss (10% from highest)
  - Quick loss protection (5% drop in 1 minute)
- Maximum holding time limits
- Configurable risk parameters

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/solana-trading-bot.git
cd solana-trading-bot
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Generate a new wallet (if needed):
```bash
python3 generate_wallet.py
```

## Configuration

Edit `.env` file with your settings:
```env
# RPC Configuration
ALCHEMY_RPC_URL=your_alchemy_rpc_url
ALCHEMY_WS_URL=your_alchemy_ws_url

# Risk Management
STOP_LOSS_THRESHOLD=0.15     # 15% drop
TRAILING_STOP_LOSS=0.10      # 10% from highest
MAX_HOLDING_TIME=3600        # 1 hour max hold
QUICK_LOSS_THRESHOLD=0.05    # 5% drop in 1 min
```

## Usage

### Manual Trading
See [MANUAL_TRADING_COMMANDS.md](MANUAL_TRADING_COMMANDS.md) for detailed command reference.

Quick examples:
```bash
# Market buy with TP/SL
python3 manual_trade.py buy --token TOKEN_ADDRESS --amount 100 --tp 1.5 --sl 0.85

# Limit buy
python3 manual_trade.py limit --token TOKEN_ADDRESS --amount 100 --price 1.0

# Check position
python3 manual_trade.py status --token TOKEN_ADDRESS
```

### Automated Trading
```bash
# Start the automated trading bot
python3 mev_bot.py
```

## Architecture

### Core Components
1. Manual Trading Module (`manual_trader.py`)
   - Direct market operations
   - Order management
   - Position tracking

2. MEV Protection (`strategies/advanced_strategies.py`)
   - Sandwich detection
   - Transaction optimization
   - Flashbots integration

3. Risk Management (`strategies/risk_manager.py`)
   - Stop-loss management
   - Position sizing
   - Risk calculations

4. Price Monitoring (`strategies/price_monitor.py`)
   - Real-time price tracking
   - Technical analysis
   - Trend detection

## Security

- Private keys are stored securely
- Environment variables for sensitive data
- Rate limiting for API calls
- Transaction signing validation
- MEV protection mechanisms

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Disclaimer

This bot is for educational purposes only. Use at your own risk. The authors take no responsibility for financial losses incurred through the use of this software.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
