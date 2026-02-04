# Polymarket Auto-Claimer

Automatically claims winning positions on Polymarket prediction markets.

## ⚠️ Security First

**CRITICAL:**
- Use a **dedicated private key** (not your main wallet key)
- Never commit `.env` files
- Run in isolated environment (VM/WSL/container)
- Always test with `DRY_RUN=true` first

## Quick Start

### 1. Configuration

Add to your `.env` file:

```bash
# Required
CLAIMER_PRIVATE_KEY=your_dedicated_private_key_here
CLAIMER_WALLET_ADDRESS=0xYourWalletAddress

# Optional
POLYGON_RPC_URL=https://polygon-rpc.com
PROXY_ADDRESS=0xYourSafeAddress  # If using Gnosis Safe
DRY_RUN=true  # Set to false for real execution
```

**Note:** You can also use `PK` and `BROWSER_ADDRESS` if they're already set, but it's recommended to use dedicated keys for the claimer.

### 2. Test with Dry Run

```bash
# Test without executing transactions
python auto_claim.py --dry-run
```

This will:
- Fetch all positions
- Filter claimable positions
- Build transactions
- Show what would be executed (without sending)

### 3. Execute Claims

```bash
# Execute directly (not recommended for production)
python auto_claim.py

# Or submit to Gnosis Safe (recommended)
python auto_claim.py --safe-address 0xYourSafeAddress
```

## Architecture

The auto-claimer follows a modular design:

```
auto_claim.py (Main Script)
    │
    ├── (A) fetchPositions() - Get positions from API
    │
    ├── (B) filterClaimables() - Filter winning positions
    │
    ├── (C) buildRedeemTx() - Build transaction data
    │
    └── (D) submitToSafe() / submitDirect() - Execute
```

## Modules

### `claimer_core/position_fetcher.py`
Fetches positions from Polymarket Data API.

### `claimer_core/claim_filter.py`
Filters positions that are:
- Resolved markets
- Winning positions
- Have redeemable amount > 0
- Not already claimed

### `claimer_core/tx_builder.py`
Builds transaction data for redeeming positions using the ConditionalTokens contract.

### `claimer_core/tx_sender.py`
- `submitToSafe()` - Submit to Gnosis Safe (requires Safe SDK)
- `submitDirect()` - Execute directly from wallet

## Usage Examples

### Check Claimable Balance

```bash
# Verificar se há saldo para resgatar (sem executar transações)
python check_claimable.py
```

This will show:
- Total positions found
- Claimable positions
- Total redeemable amount
- Details for each claimable position

### Basic Usage

```bash
# Dry run first
python auto_claim.py --dry-run

# Execute if dry run looks good
python auto_claim.py
```

### With Custom RPC

```bash
python auto_claim.py --rpc-url https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY
```

### With Safe

```bash
python auto_claim.py --safe-address 0xYourSafeAddress
```

## Automation

### Cron (Hourly)

```bash
# Edit crontab
crontab -e

# Add this line (runs every hour)
0 * * * * cd /path/to/polymarket-automated-mm && /path/to/venv/bin/python auto_claim.py >> auto_claimer_cron.log 2>&1
```

### Cron (Daily)

```bash
# Run once per day at 9 AM
0 9 * * * cd /path/to/polymarket-automated-mm && /path/to/venv/bin/python auto_claim.py >> auto_claimer_cron.log 2>&1
```

### Docker (Optional)

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "auto_claim.py"]
```

## Logging

Logs are written to:
- Console (stdout)
- `auto_claimer.log` file

Log format:
```
2024-01-01 12:00:00 - auto_claimer - INFO - Fetching positions for wallet: 0x...
2024-01-01 12:00:01 - auto_claimer - INFO - ✓ Fetched 10 positions from API
2024-01-01 12:00:02 - auto_claimer - INFO - ✓ Filtered 3 claimable positions
```

## Troubleshooting

### "No positions found"
- Check wallet address is correct
- Verify you have positions on Polymarket
- Check API is accessible

### "No claimable positions"
- Markets may not be resolved yet
- Positions may already be claimed
- Check `redeemable` field in API response

### "Transaction failed"
- Check gas price/limit
- Verify private key has MATIC for gas
- Check RPC connection

### "Failed to encode transaction"
- Verify position data structure matches API
- Check `conditionId`, `indexSets` are correct
- May need to adjust `tx_builder.py` for API changes

## Integration with Main Bot

The auto-claimer can run alongside the main trading bot:

```bash
# Terminal 1: Main trading bot
python main.py

# Terminal 2: Auto-claimer (hourly)
python auto_claim.py
```

Or use cron to schedule the claimer independently.

## Safe Integration

For production use, it's recommended to use Gnosis Safe:

1. Set up a Gnosis Safe wallet
2. Add your claimer address as a signer
3. Use `--safe-address` or `PROXY_ADDRESS` in `.env`

**Note:** Full Safe integration requires the Safe SDK. The current implementation is a placeholder - you'll need to implement the Safe transaction submission using the Safe SDK or Safe Transaction Service API.

## API Reference

### `fetchPositions(wallet_address: str) -> List[Dict]`
Fetches all positions for a wallet.

### `filterClaimables(positions: List[Dict]) -> List[Dict]`
Filters positions eligible for claiming.

### `buildRedeemTx(claimable: Dict, web3: Web3) -> Dict`
Builds transaction data for redeeming a position.

### `submitDirect(tx_data: Dict, web3: Web3, private_key: str) -> Dict`
Executes transaction directly.

### `submitToSafe(tx_data: Dict, safe_address: str, web3: Web3) -> Dict`
Submits transaction to Gnosis Safe (placeholder).

## License

MIT


