#!/usr/bin/env python3
"""
Polymarket Auto-Claimer

Automatically claims winning positions on Polymarket prediction markets.

Security Notes:
- Use a dedicated private key (not your main key)
- Never commit .env files
- Run in isolated environment (VM/WSL/container)
- Always test with DRY_RUN=true first

Usage:
    python auto_claim.py [--dry-run] [--safe-address ADDRESS]
"""

import os
import sys
import argparse
from typing import Optional, List, Dict
from dotenv import load_dotenv
from web3 import Web3
from eth_utils import to_checksum_address

# Import claimer modules
from claimer_core.position_fetcher import fetchPositions, create_session
from claimer_core.claim_filter import filterClaimables
from claimer_core.tx_builder import buildRedeemTx
from claimer_core.tx_sender import submitToSafe, submitDirect
from claimer_core.tx_sender_magic import submitViaPolymarketClient
from poly_data.polymarket_client import PolymarketClient
from claimer_core.logger_config import setup_logger

# Load environment variables
load_dotenv()

# Initialize logger
logger = setup_logger("auto_claimer", "auto_claimer.log")

def validate_config() -> Dict[str, str]:
    """
    Validate required environment variables.
    
    Returns:
        Dictionary with validated config values
    
    Raises:
        ValueError: If required config is missing
    """
    config = {}
    
    # Required
    config['PRIVATE_KEY'] = os.getenv('CLAIMER_PRIVATE_KEY') or os.getenv('PK')
    if not config['PRIVATE_KEY']:
        raise ValueError("CLAIMER_PRIVATE_KEY or PK must be set in .env")
    
    config['WALLET_ADDRESS'] = os.getenv('CLAIMER_WALLET_ADDRESS') or os.getenv('BROWSER_ADDRESS')
    if not config['WALLET_ADDRESS']:
        raise ValueError("CLAIMER_WALLET_ADDRESS or BROWSER_ADDRESS must be set in .env")
    
    # Optional
    config['RPC_URL'] = os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com')
    config['SAFE_ADDRESS'] = os.getenv('PROXY_ADDRESS')  # Gnosis Safe address
    config['DRY_RUN'] = os.getenv('DRY_RUN', 'false').lower() == 'true'
    
    # Ensure wallet address is checksummed
    config['WALLET_ADDRESS'] = to_checksum_address(config['WALLET_ADDRESS'])
    
    return config

def main(
    dry_run: bool = False,
    safe_address: Optional[str] = None,
    rpc_url: Optional[str] = None
):
    """
    Main execution function for auto-claiming.
    
    Args:
        dry_run: If True, only simulate without sending transactions
        safe_address: Optional Gnosis Safe address (if None, uses direct execution)
        rpc_url: Optional Polygon RPC URL
    """
    try:
        logger.info("=" * 80)
        logger.info("POLYMARKET AUTO-CLAIMER")
        logger.info("=" * 80)
        
        # Validate configuration
        config = validate_config()
        
        # Override with CLI args if provided
        if dry_run:
            config['DRY_RUN'] = True
        if safe_address:
            config['SAFE_ADDRESS'] = safe_address
        if rpc_url:
            config['RPC_URL'] = rpc_url
        
        logger.info(f"Wallet: {config['WALLET_ADDRESS']}")
        logger.info(f"RPC: {config['RPC_URL']}")
        logger.info(f"Dry Run: {config['DRY_RUN']}")
        if config['SAFE_ADDRESS']:
            logger.info(f"Safe Address: {config['SAFE_ADDRESS']}")
        else:
            logger.info("Mode: Direct execution (not using Safe)")
        
        if config['DRY_RUN']:
            logger.warning("⚠️  DRY RUN MODE - No transactions will be sent")
        
        # Initialize Web3 and check if using Magic Link
        logger.info("Connecting to Polygon...")
        web3 = Web3(Web3.HTTPProvider(config['RPC_URL']))
        if not web3.is_connected():
            raise ConnectionError(f"Failed to connect to RPC: {config['RPC_URL']}")
        logger.info("✓ Connected to Polygon")
        
        # Check if using Magic Link (funder address matches wallet address)
        # If so, use PolymarketClient instead of direct signing
        use_magic_link = False
        try:
            pm_client = PolymarketClient()
            if pm_client.browser_wallet.lower() == config['WALLET_ADDRESS'].lower():
                use_magic_link = True
                logger.info("✓ Detected Magic Link wallet - using PolymarketClient")
        except Exception as e:
            logger.warning(f"Could not initialize PolymarketClient: {e}")
            logger.info("Will attempt direct transaction signing")
        
        # Step 1: Fetch positions
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: Fetching positions from Polymarket API")
        logger.info("=" * 80)
        
        session = create_session()
        positions = fetchPositions(config['WALLET_ADDRESS'], session)
        
        logger.info(f"Total positions fetched: {len(positions)}")
        
        if len(positions) == 0:
            logger.info("No positions found. Exiting.")
            return
        
        # Step 2: Filter claimables
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: Filtering claimable positions")
        logger.info("=" * 80)
        
        claimables = filterClaimables(positions)
        
        logger.info(f"Claimable positions: {len(claimables)}")
        
        if len(claimables) == 0:
            logger.info("No claimable positions found. Exiting.")
            return
        
        # Log claimable positions summary
        total_redeemable = 0
        for claimable in claimables:
            redeemable = float(claimable.get('redeemable', 0))
            total_redeemable += redeemable
            logger.info(
                f"  - {claimable.get('market', 'Unknown')} | "
                f"Outcome: {claimable.get('outcome', 'Unknown')} | "
                f"Redeemable: ${redeemable:.2f} | "
                f"Asset: {claimable.get('asset', 'Unknown')[:20]}..."
            )
        
        logger.info(f"\nTotal redeemable amount: ${total_redeemable:.2f}")
        
        # Step 3: Build transactions
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: Building redeem transactions")
        logger.info("=" * 80)
        
        tx_list = []
        for claimable in claimables:
            try:
                tx_data = buildRedeemTx(claimable, web3)
                tx_list.append({
                    'claimable': claimable,
                    'tx_data': tx_data
                })
                logger.info(f"✓ Built tx for {claimable.get('asset', 'unknown')[:20]}...")
            except Exception as e:
                logger.error(f"❌ Failed to build tx for {claimable.get('asset', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully built {len(tx_list)} transactions")
        
        # Step 4: Execute or simulate
        logger.info("\n" + "=" * 80)
        if config['DRY_RUN']:
            logger.info("STEP 4: DRY RUN - Transaction Summary (not executing)")
        else:
            logger.info("STEP 4: Executing transactions")
        logger.info("=" * 80)
        
        results = []
        for idx, item in enumerate(tx_list, 1):
            claimable = item['claimable']
            tx_data = item['tx_data']
            position_info = tx_data.get('position_info', {})
            
            logger.info(f"\n[{idx}/{len(tx_list)}] Processing: {position_info.get('market', 'Unknown')}")
            logger.info(f"  Asset: {position_info.get('asset', 'Unknown')}")
            logger.info(f"  Redeemable: ${float(position_info.get('redeemable', 0)):.2f}")
            logger.info(f"  To: {tx_data['to']}")
            
            # Handle data as bytes or string
            data = tx_data.get('data')
            if data:
                if isinstance(data, bytes):
                    data_str = data.hex()[:20] + "..."
                elif isinstance(data, str):
                    if data.startswith('0x'):
                        data_str = data[2:22] + "..."
                    else:
                        data_str = data[:20] + "..."
                else:
                    data_str = str(data)[:20] + "..."
                logger.info(f"  Data: {data_str}")
            else:
                logger.info(f"  Data: (not encoded - will be encoded on execution)")
            
            if config['DRY_RUN']:
                logger.info("  [DRY RUN] Would execute transaction")
                results.append({
                    'status': 'dry_run',
                    'position_info': position_info,
                    'tx_data': tx_data
                })
            else:
                try:
                    if use_magic_link:
                        # Use PolymarketClient for Magic Link
                        logger.info("  Using PolymarketClient (Magic Link)")
                        result = submitViaPolymarketClient(
                            claimable,
                            pm_client
                        )
                        if result.get('status') == 'requires_manual_action':
                            logger.warning("  ⚠️  Magic Link requires manual claim via Polymarket UI")
                            logger.info("  You can claim at: https://polymarket.com/portfolio")
                    elif config['SAFE_ADDRESS']:
                        # Submit to Safe
                        result = submitToSafe(
                            tx_data,
                            config['SAFE_ADDRESS'],
                            web3,
                            config['PRIVATE_KEY']
                        )
                    else:
                        # Execute directly
                        result = submitDirect(
                            tx_data,
                            web3,
                            config['PRIVATE_KEY']
                        )
                    
                    results.append(result)
                    logger.info(f"  ✓ Transaction {result.get('status', 'unknown')}: {result.get('tx_hash', 'N/A')}")
                
                except Exception as e:
                    logger.error(f"  ❌ Transaction failed: {e}")
                    results.append({
                        'status': 'error',
                        'error': str(e),
                        'position_info': position_info
                    })
        
        # Final summary
        logger.info("\n" + "=" * 80)
        logger.info("FINAL SUMMARY")
        logger.info("=" * 80)
        
        if config['DRY_RUN']:
            logger.info(f"DRY RUN: Would have executed {len(tx_list)} transactions")
            logger.info(f"Total redeemable: ${total_redeemable:.2f}")
        else:
            successful = sum(1 for r in results if r.get('status') == 'success')
            failed = sum(1 for r in results if r.get('status') in ['error', 'failed'])
            pending = sum(1 for r in results if r.get('status') == 'pending')
            
            logger.info(f"Successful: {successful}")
            logger.info(f"Failed: {failed}")
            logger.info(f"Pending: {pending}")
            logger.info(f"Total redeemable: ${total_redeemable:.2f}")
        
        logger.info("=" * 80)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Polymarket Auto-Claimer - Automatically claim winning positions"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (simulate without sending transactions)'
    )
    parser.add_argument(
        '--safe-address',
        type=str,
        help='Gnosis Safe address (overrides PROXY_ADDRESS from .env)'
    )
    parser.add_argument(
        '--rpc-url',
        type=str,
        help='Polygon RPC URL (overrides POLYGON_RPC_URL from .env)'
    )
    
    args = parser.parse_args()
    
    main(
        dry_run=args.dry_run,
        safe_address=args.safe_address,
        rpc_url=args.rpc_url
    )


