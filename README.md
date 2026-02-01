# SuperSnayder - Polymarket Automated Market Making Bot

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Cython](https://img.shields.io/badge/Cython-Optimized-green.svg)](https://cython.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Disclaimer:** This project was forked and recreated from the original creator [@defiance_cr](https://github.com/defiance_cr) and continued with additional features and optimizations.

A high-performance, automated market making bot for Polymarket prediction markets. This bot provides liquidity to markets by maintaining orders on both sides of the book with configurable parameters, optimized for low latency and high efficiency.

## 🚀 Key Features

### Core Trading Features
- **Real-time Order Book Monitoring** - WebSocket-based order book updates with sub-second latency
- **Two-Sided Market Making** - Places buy and sell orders simultaneously, even without existing positions
- **Reward-Optimized Pricing** - Calculates optimal order placement based on Polymarket's maker reward formula
- **Automated Market Selection** - Data-driven market selection by profitability or daily rewards
- **Position Management** - Risk controls with automated position merging and stop-loss/take-profit
- **Customizable Trade Parameters** - Fetched from Google Sheets for easy configuration
- **Maker Reward Tracking** - Real-time visibility into estimated rewards with automatic logging

### Performance Optimizations (8 Phases)
- **Fase 1-4**: Order intent system, payload templates, fixed-point arithmetic, sender task optimization
- **Fase 5**: Book state management with snapshot initialization and reconciliation
- **Fase 6**: Order intent batching and optimization
- **Fase 7**: uvloop integration for faster async I/O (Linux)
- **Fase 8**: **Cython hot path optimization** - 73.5% reduction in spread computation latency

### Advanced Features
- **Reduced Order Churn** - 95% reduction in unnecessary cancellations (30s cooldown + wider thresholds)
- **Position Merging** - Automatically merges opposing YES/NO positions to free capital
- **WebSocket Reconnection** - Automatic reconnection with exponential backoff
- **Comprehensive Logging** - Trade logs, position snapshots, and reward tracking in Google Sheets
- **Risk Management** - Stop-loss, take-profit, volatility filters, and position limits

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Architecture](#architecture)
- [Cython Optimization](#cython-optimization)
- [Performance Metrics](#performance-metrics)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## 🛠️ Installation

### Prerequisites

- **Python 3.9+** with latest setuptools
- **Node.js** (for `poly_merger` position merging)
- **Google Sheets API credentials** (Service Account)
- **Polymarket account** with API credentials
- **Cython** and **numpy** (for performance optimizations)

### Step-by-Step Setup

1. **Clone the repository:**
```bash
git clone https://github.com/Leandrosmoreira/supersnayder.git
cd supersnayder
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Compile Cython modules (Fase 8 optimization):**
```bash
python setup_cython.py build_ext --inplace
```

This compiles the optimized Cython modules:
- `poly_data/book_cython` - Fast order book operations
- `poly_data/payload_builder_cython` - Fast payload construction

**Note:** If Cython compilation fails, the bot will automatically fall back to pure Python implementations.

4. **Install Node.js dependencies for position merger:**
```bash
cd poly_merger
npm install
cd ..
```

5. **Set up environment variables:**
```bash
cp .env.example .env
```

6. **Configure your credentials in `.env`:**
```bash
# Required
PK=your_private_key_here
BROWSER_ADDRESS=your_wallet_address_here
SPREADSHEET_URL=https://docs.google.com/spreadsheets/d/...

# Optional
POLYGON_RPC_URL=https://polygon-rpc.com
TWO_SIDED_MARKET_MAKING=true
AGGRESSIVE_MODE=false
```

⚠️ **Important:** Your wallet must have made at least one trade through the Polymarket UI before using the bot (for proper permissions setup).

7. **Set up Google Sheets integration:**
   - Create a Google Service Account and download credentials as `credentials.json` to the main directory
   - Add your Google service account email to the spreadsheet with edit permissions
   - The spreadsheet should have these tabs (auto-created if missing):
     - **Selected Markets** - Markets you want to trade
     - **All Markets** - Database of all markets (auto-updated)
     - **Volatility Markets** - Filtered markets with volatility_sum < 20
     - **Hyperparameters** - Trading configuration parameters
     - **Trade Log** - Automatic trade logging (auto-created)
     - **Maker Rewards** - Reward tracking (auto-created)

8. **Update market data:**
```bash
# Run the data updater to fetch all available markets
python data_updater/data_updater.py
```

This fetches all available markets and calculates rewards/volatility metrics. Should run continuously in the background (preferably on a different IP than your trading bot).

9. **Select markets to trade:**
```bash
# Option 1: Automated selection by profitability (default)
python update_selected_markets.py

# Option 2: High reward mode (markets with >= $100/day)
python update_selected_markets.py --min-reward 100 --max-markets 10

# Option 3: Manual selection - Add markets to "Selected Markets" sheet
```

10. **Start the market making bot:**
```bash
python main.py
```

## ⚙️ Configuration

### Google Sheets Structure

The bot is configured via a Google Spreadsheet with several worksheets:

#### Selected Markets Tab
Markets you want to trade (can be auto-populated):
| question | max_size | trade_size | param_type | comments |
|----------|----------|------------|------------|----------|
| Market question | 100 | 50 | aggressive | ... |

#### Hyperparameters Tab
Configuration parameters for trading logic:
| type | param | value |
|------|-------|-------|
| aggressive | stop_loss_threshold | -15 |
| aggressive | take_profit_threshold | 10 |
| conservative | stop_loss_threshold | -5 |

### Environment Variables

**Required:**
- `PK` - Your private key for Polymarket
- `BROWSER_ADDRESS` - Your wallet address
- `SPREADSHEET_URL` - Google Sheets URL

**Optional:**
- `POLYGON_RPC_URL` - Polygon RPC endpoint (default: https://polygon-rpc.com)
- `TWO_SIDED_MARKET_MAKING` - Enable two-sided market making (default: false)
- `AGGRESSIVE_MODE` - Skip safety checks (use with caution, default: false)

## 📖 Usage

### Basic Workflow

```bash
# Terminal 1: Data updater (run continuously in background)
python data_updater/data_updater.py

# Terminal 2: Trading bot
python main.py
```

### Automated Market Selection

**Profitability Mode** (default):
```bash
python update_selected_markets.py
```
- Selects markets by `profitability_score = gm_reward_per_100 / (volatility_sum + 1)`
- Filters: reward >= 1.0%, volatility < 20, spread < 0.1, price 0.1-0.9
- Targets 5-6 markets for optimal diversification

**High Reward Mode:**
```bash
python update_selected_markets.py --min-reward 150 --max-markets 15 --replace
```
- Filters markets by minimum daily reward (e.g., >= $150/day)
- Automatically assigns trade sizes based on reward level

### Utility Scripts

```bash
# Cancel all orders
python cancel_all_orders.py

# Check current positions
python check_positions.py

# Update hyperparameters in Google Sheets
python update_hyperparameters.py

# Validate bot configuration
python validate_polymarket_bot.py
```

## 🏗️ Architecture

### Project Structure

```
supersnayder/
├── main.py                      # Entry point, orchestrates WebSocket connections
├── trading.py                   # Core trading logic and order placement
├── setup_cython.py              # Cython compilation script
│
├── poly_data/                   # Core data management and trading logic
│   ├── polymarket_client.py     # Polymarket API wrapper
│   ├── websocket_handlers.py    # WebSocket connection management
│   ├── data_processing.py       # Order book processing
│   ├── data_utils.py            # Market/position/order data utilities
│   ├── trading_utils.py         # Trading utility functions
│   ├── global_state.py          # Shared state management
│   ├── book_state.py            # Order book state management (Fase 5)
│   ├── reconcile_task.py        # Book reconciliation (Fase 5)
│   ├── order_intent.py          # Order intent system (Fase 1)
│   ├── payload_template.py      # Payload templates (Fase 2)
│   ├── fixed_point.py           # Fixed-point arithmetic (Fase 3)
│   ├── sender_task.py           # Sender task optimization (Fase 4)
│   ├── reward_tracker.py        # Maker reward tracking
│   ├── trade_logger.py          # Trade logging to Google Sheets
│   ├── position_snapshot.py     # Position snapshot logging
│   │
│   ├── book_cython.pyx           # Cython: Fast order book operations (Fase 8)
│   ├── payload_builder_cython.pyx # Cython: Fast payload builder (Fase 8)
│   └── cython_wrapper.py        # Cython wrapper with fallback
│
├── poly_merger/                 # Position merging utility (Node.js)
│   └── merge.js                 # Merges opposing YES/NO positions
│
├── poly_stats/                  # Account statistics tracking
│   └── account_stats.py
│
├── poly_utils/                  # Shared utility functions
│   └── google_utils.py
│
└── data_updater/                # Market data collection module
    ├── data_updater.py          # Fetches all Polymarket markets
    ├── find_markets.py          # Calculates rewards and volatility
    └── google_utils.py
```

### System Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     POLY-MAKER BOT                          │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐         ┌──────▼──────┐      ┌──────▼──────┐
   │ main.py │         │  trading.py │      │ websockets  │
   └────┬────┘         └──────┬──────┘      └──────┬──────┘
        │                     │                     │
        │              ┌──────▼──────┐              │
        │              │ data utils  │◄─────────────┘
        │              └──────┬──────┘
        │                     │
        └─────────────┬───────┴───────┬─────────────┘
                      │               │
           ┌──────────▼──────┐  ┌─────▼─────────┐
           │ Google Sheets   │  │  Polymarket   │
           │ (Config/Data)   │  │   (Trading)   │
           └─────────────────┘  └───────────────┘
```

## ⚡ Cython Optimization (Fase 8)

The bot includes Cython-optimized hot paths for critical operations:

### Compiled Modules

1. **`book_cython.pyx`** - Order book operations
   - `compute_spread_fast()` - Calculates spread with 73.5% latency reduction
   - `compute_quote_fast()` - Fast quote calculation

2. **`payload_builder_cython.pyx`** - Payload construction
   - `build_order_payload_fast()` - Optimized order payload creation

### Performance Gains

| Operation | Python Pure | Cython | Improvement |
|-----------|-------------|--------|-------------|
| Compute Spread (p50) | 0.0034ms | 0.0008ms | **73.5%** |
| Compute Spread (p99) | 0.0037ms | 0.0010ms | **73.0%** |
| Build Payload (p99) | 0.0004ms | 0.0003ms | **25%** |

### Compilation

```bash
# Compile Cython modules
python setup_cython.py build_ext --inplace

# The compiled .so files will be in poly_data/
# - book_cython.cpython-*.so
# - payload_builder_cython.cpython-*.so
```

### Fallback Behavior

If Cython modules are not available, the bot automatically falls back to pure Python implementations via `cython_wrapper.py`. The bot will work without Cython, but with slightly higher latency.

## 📊 Performance Metrics

### Order Cycle Performance

| Metric | Value |
|--------|-------|
| **p50 Latency** | 186ms |
| **p99 Latency** | 794ms* |
| **Average** | 310ms |

*First order includes connection/authentication overhead. Subsequent orders: ~186ms.

### Optimizations Summary

| Feature | Improvement |
|---------|-------------|
| Order Cancellations | ~95% reduction (30s cooldown + wider thresholds) |
| Spread Computation | 73.5% faster (Cython) |
| Reward Optimization | Orders placed at optimal distance for max rewards |
| Market Selection | Automated data-driven selection |
| Capital Efficiency | Automatic position merging frees locked capital |
| Gas Fees | Significantly reduced through smarter cancellation logic |

## 📈 Monitoring

### Log Files

- `main.log` - Main bot activity and trading decisions
- `data_updater.log` - Market data update logs
- `websocket_handlers.log` - WebSocket connection events
- `data_processing.log` - Order book processing

### Google Sheets

- **Trade Log** - Every order placed/filled/cancelled with timestamps
- **Maker Rewards** - Estimated rewards updated every 5 minutes
- **Position Snapshots** - Periodic position snapshots (every 5 minutes)

### Real-time Monitoring

```bash
# Watch main log
tail -f main.log

# Watch data processing
tail -f data_processing.log

# Check positions
python check_positions.py
```

## 🔧 Key Features Explained

### 1. Reward-Optimized Pricing

The bot calculates optimal order placement based on Polymarket's maker reward formula:
- Formula: `S = ((v - s) / v)^2` where `v` is max_spread and `s` is distance from mid-price
- Places orders at ~15% of max_spread distance for optimal reward/fill balance
- Maximizes maker rewards while maintaining fill probability

### 2. Reduced Order Churn

- **30-second cooldown** between trading actions on price changes
- **Wider cancellation thresholds**: 1.5% price diff, 25% size diff
- **Result**: ~95% reduction in unnecessary order cancellations, saving gas fees

### 3. Two-Sided Market Making

- Places buy and sell orders simultaneously, even without existing positions
- Enabled via `TWO_SIDED_MARKET_MAKING=true` in `.env`
- Earns from both maker rewards and spread capture

### 4. Position Merging

The `poly_merger` module automatically merges opposing YES/NO positions:
- Frees up locked capital when you have both sides of a market
- Triggers when mergeable amount > $20 (configurable)
- Built on open-source Polymarket code
- Reduces gas fees and improves capital efficiency

### 5. Risk Management

- **Stop Loss**: Automatic position exit when loss exceeds threshold
- **Take Profit**: Automatic sell orders at profit targets
- **Volatility Filter**: Skips trading in highly volatile markets
- **Position Limits**: Per-market and global position caps
- **Reverse Position Check**: Prevents hedging against yourself

## 🐛 Troubleshooting

### Orders Cancelling Too Often

- Increase cooldown in `data_processing.py` (default: 30s)
- Increase thresholds in `trading.py` (price: 1.5%, size: 25%)

### No Rewards Showing

- Ensure bot has been running for at least 5 minutes
- Check "Maker Rewards" tab exists in Google Sheets
- Verify orders are being placed (check "Trade Log" tab)

### Market Selection Not Working

- Run `python data_updater/data_updater.py` first to populate data
- Check "Volatility Markets" tab has data
- Try lowering `--min-reward` threshold

### Cython Compilation Issues

- Ensure `cython` and `numpy` are installed: `pip install cython numpy`
- Check Python version compatibility (3.9+)
- If compilation fails, the bot will use pure Python fallback

### WebSocket Disconnections

- Normal behavior: Auto-reconnects with exponential backoff
- Max backoff: 60 seconds
- Check network connection if frequent disconnections

## ⚠️ Important Notes

- ⚠️ **This code interacts with real markets and can potentially lose real money**
- 🧪 **Test thoroughly with small amounts before deploying with significant capital**
- 📊 **Monitor logs and Google Sheets regularly to ensure proper operation**
- 🔒 **Never commit `.env` or `credentials.json` to version control**
- 💡 **The `data_updater` should ideally run on a different IP than the trading bot**
- 🚀 **Cython optimizations are optional but recommended for best performance**

## 📚 Additional Documentation

- [BOT_OVERVIEW.md](BOT_OVERVIEW.md) - Complete system overview
- [GUIA_USO.md](GUIA_USO.md) - Usage guide (Portuguese)
- [COMO_FUNCIONA.md](COMO_FUNCIONA.md) - How it works (Portuguese)
- [FASE8_IMPLEMENTADA.md](FASE8_IMPLEMENTADA.md) - Cython optimization details

## 🤝 Contributing

This project was forked from [@defiance_cr](https://github.com/defiance_cr)'s original work and extended with additional features. Contributions are welcome!

## 📄 License

MIT

## 🙏 Acknowledgments

- Original creator: [@defiance_cr](https://github.com/defiance_cr)
- Built on open-source Polymarket code for position merging
- Uses `py-clob-client` for Polymarket API interactions

---

**Remember:** Market making requires patience. Profits come from many small trades over time, not immediate gains!
