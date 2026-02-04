# Auto-Claimer Core Module

This module provides functionality to automatically claim winning positions on Polymarket prediction markets.

## Security First ⚠️

**CRITICAL SECURITY NOTES:**

1. **Use a dedicated private key** - Never use your main wallet's private key
2. **Never commit .env files** - Keep credentials secure
3. **Run in isolated environment** - Use VM/WSL/container
4. **Test with DRY_RUN first** - Always validate before real execution

## Architecture

The auto-claimer is split into 4 modular components:

### (A) `position_fetcher.py` - Fetch Positions
- Fetches all positions from Polymarket API
- Handles retries and error handling
- Returns list of position dictionaries

### (B) `claim_filter.py` - Filter Claimables
- Filters positions that are:
  - `resolved == true`
  - `you_won == true`
  - `redeemable > 0`
  - `notClaimed` (not already claimed)

### (C) `tx_builder.py` - Build Redeem Transaction
- Constructs transaction data for redeeming positions
- Encodes function calls to ConditionalTokens contract
- Returns transaction structure ready for execution

### (D) `tx_sender.py` - Submit Transaction
- `submitToSafe()` - Submit to Gnosis Safe (requires Safe SDK)
- `submitDirect()` - Execute directly from wallet

## Usage

See `../auto_claim.py` for the main script.

## Environment Variables

Required:
- `CLAIMER_PRIVATE_KEY` or `PK` - Private key for signing transactions
- `CLAIMER_WALLET_ADDRESS` or `BROWSER_ADDRESS` - Wallet address

Optional:
- `POLYGON_RPC_URL` - Polygon RPC endpoint (default: https://polygon-rpc.com)
- `PROXY_ADDRESS` - Gnosis Safe address (if using Safe)
- `DRY_RUN` - Set to `true` for dry-run mode

## Example

```python
from claimer_core import fetchPositions, filterClaimables, buildRedeemTx, submitDirect
from web3 import Web3

# Fetch positions
positions = fetchPositions("0xYourWalletAddress")

# Filter claimables
claimables = filterClaimables(positions)

# Build and execute transactions
web3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
for claimable in claimables:
    tx_data = buildRedeemTx(claimable, web3)
    result = submitDirect(tx_data, web3, "your_private_key")
    print(f"Transaction: {result['tx_hash']}")
```


