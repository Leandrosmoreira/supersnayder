"""
Module (D): Submit Transaction using PolymarketClient (Magic Link compatible)

For Magic Link users, we use the existing PolymarketClient which handles
the proxy wallet authentication.
"""

import logging
from typing import Dict, Optional
from poly_data.polymarket_client import PolymarketClient

logger = logging.getLogger(__name__)

def submitViaPolymarketClient(
    claimable: Dict,
    client: Optional[PolymarketClient] = None
) -> Dict:
    """
    Execute claim using PolymarketClient (works with Magic Link).
    
    This uses the existing client infrastructure which handles
    Magic Link proxy wallet authentication.
    
    Args:
        claimable: Claimable position dictionary from filterClaimables()
        client: Optional PolymarketClient instance (will create one if not provided)
    
    Returns:
        Dictionary with transaction hash and status
    """
    try:
        if client is None:
            logger.info("Initializing PolymarketClient...")
            client = PolymarketClient()
        
        # Extract position data
        asset = claimable.get('asset') or claimable.get('tokenId')
        condition_id = claimable.get('conditionId') or claimable.get('condition_id')
        
        logger.info(f"Attempting to redeem position {asset[:20]}...")
        logger.info(f"Condition ID: {condition_id}")
        
        # Note: The PolymarketClient doesn't have a direct redeem method
        # We need to call the contract directly through web3
        # But we can use the client's web3 instance and addresses
        
        from web3 import Web3
        from poly_data.abis import ConditionalTokenABI
        from eth_utils import to_checksum_address
        
        # Get contract addresses from client
        conditional_tokens_address = client.addresses['conditional_tokens']
        usdc_address = client.addresses['collateral']
        
        # Get the conditional tokens contract
        conditional_tokens = client.web3.eth.contract(
            address=to_checksum_address(conditional_tokens_address),
            abi=ConditionalTokenABI
        )
        
        # Extract parameters
        parent_collection_id = claimable.get('parentCollectionId') or '0x0000000000000000000000000000000000000000000000000000000000000000'
        index_sets = claimable.get('indexSets') or claimable.get('index_sets', [])
        
        # Determine indexSets from outcomeIndex if not provided
        if not index_sets:
            outcome_index = claimable.get('outcomeIndex')
            if outcome_index is not None:
                if outcome_index == 0:
                    index_sets = [1]  # YES
                elif outcome_index == 1:
                    index_sets = [2]  # NO
                else:
                    index_sets = [outcome_index + 1]
            else:
                outcome = claimable.get('outcome', '').upper()
                if 'YES' in outcome or 'UP' in outcome:
                    index_sets = [1]
                elif 'NO' in outcome or 'DOWN' in outcome:
                    index_sets = [2]
                else:
                    index_sets = [1]
        
        # Convert condition_id and parent_collection_id to bytes32
        if isinstance(condition_id, str):
            if condition_id.startswith('0x'):
                condition_id_bytes = bytes.fromhex(condition_id[2:])
            else:
                condition_id_bytes = bytes.fromhex(condition_id)
        else:
            condition_id_bytes = condition_id
        
        if len(condition_id_bytes) != 32:
            condition_id_bytes = condition_id_bytes[:32].ljust(32, b'\x00')
        
        if isinstance(parent_collection_id, str):
            if parent_collection_id.startswith('0x'):
                parent_collection_id_bytes = bytes.fromhex(parent_collection_id[2:])
            else:
                parent_collection_id_bytes = bytes.fromhex(parent_collection_id)
        else:
            parent_collection_id_bytes = parent_collection_id
        
        if len(parent_collection_id_bytes) != 32:
            parent_collection_id_bytes = parent_collection_id_bytes[:32].ljust(32, b'\x00')
        
        # Build transaction
        function_call = conditional_tokens.functions.redeemPositions(
            to_checksum_address(usdc_address),
            parent_collection_id_bytes,
            condition_id_bytes,
            index_sets
        )
        
        # Build transaction for execution
        # Note: For Magic Link, this will only work if the proxy wallet
        # has been authorized to interact with the ConditionalTokens contract
        logger.info("Building transaction for claim...")
        
        # Get wallet address
        wallet_address = client.browser_wallet
        
        # Build transaction
        tx = function_call.build_transaction({
            'from': wallet_address,
            'nonce': client.web3.eth.get_transaction_count(wallet_address),
            'gas': 500000,  # Default gas limit
            'gasPrice': client.web3.eth.gas_price,
            'chainId': 137,  # Polygon
        })
        
        # Try to estimate gas
        try:
            estimated_gas = client.web3.eth.estimate_gas(tx)
            tx['gas'] = int(estimated_gas * 1.2)
            logger.info(f"Estimated gas: {estimated_gas}, using {tx['gas']}")
        except Exception as e:
            logger.warning(f"Gas estimation failed: {e}, using default 500000")
        
        # For Magic Link, we need to use the ClobClient's signing mechanism
        # or try to send via the client's web3 instance
        # The issue is that Magic Link proxy wallets need special handling
        
        # Try to send transaction - this may work if the proxy wallet is set up correctly
        try:
            logger.info("Attempting to send transaction via web3...")
            logger.warning("⚠️  Note: This may fail if Magic Link proxy wallet is not authorized")
            
            # Check if we have a private key (even if it's for the proxy)
            # If not, we can't sign, so return the transaction data for manual execution
            from dotenv import load_dotenv
            import os
            load_dotenv()
            
            private_key = os.getenv('PK') or os.getenv('CLAIMER_PRIVATE_KEY')
            
            if private_key:
                from eth_account import Account
                account = Account.from_key(private_key)
                
                # For Magic Link, the private key might be for a different address
                # We need to use the wallet_address (funder) as the 'from' address
                # But sign with the private key we have
                if account.address.lower() != wallet_address.lower():
                    logger.warning(f"Private key address ({account.address}) doesn't match wallet ({wallet_address})")
                    logger.warning("Using wallet address as 'from' - this may work for Magic Link proxy wallets")
                    # Update tx to use the correct from address
                    tx['from'] = wallet_address
                    # But we still sign with the private key we have
                    # This might work if the proxy wallet is set up to relay transactions
                
                # Sign and send
                signed_tx = account.sign_transaction(tx)
                raw_tx = signed_tx.raw_transaction if hasattr(signed_tx, 'raw_transaction') else signed_tx.rawTransaction
                
                # For Magic Link proxy wallets, we might need to send via a relayer
                # Try direct send first
                try:
                    tx_hash = client.web3.eth.send_raw_transaction(raw_tx)
                    tx_hash_hex = tx_hash.hex() if hasattr(tx_hash, 'hex') else tx_hash.hex()
                except Exception as e:
                    error_msg = str(e)
                    if 'from field must match' in error_msg.lower():
                        logger.error("❌ Cannot sign transaction: private key doesn't match wallet address")
                        logger.error("For Magic Link, you need the private key of the proxy wallet")
                        logger.error("Or use the Polymarket UI to claim manually")
                        raise ValueError("Private key address mismatch - cannot sign for Magic Link proxy wallet")
                    else:
                        raise
                
                logger.info(f"✓ Transaction sent: {tx_hash_hex}")
                
                # Wait for receipt
                try:
                    receipt = client.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
                    status = 'success' if receipt.status == 1 else 'failed'
                    logger.info(f"✓ Transaction {status}: {tx_hash_hex}")
                    
                    return {
                        'status': status,
                        'tx_hash': tx_hash_hex,
                        'receipt': dict(receipt),
                        'position_info': {
                            'asset': asset,
                            'conditionId': condition_id,
                            'redeemable': claimable.get('redeemable', 0),
                            'market': claimable.get('market') or claimable.get('title', 'Unknown'),
                        }
                    }
                except Exception as e:
                    logger.warning(f"Transaction sent but receipt wait failed: {e}")
                    return {
                        'status': 'pending',
                        'tx_hash': tx_hash_hex,
                        'position_info': {
                            'asset': asset,
                            'conditionId': condition_id,
                            'redeemable': claimable.get('redeemable', 0),
                            'market': claimable.get('market') or claimable.get('title', 'Unknown'),
                        }
                    }
            else:
                raise ValueError("No private key found - cannot sign transaction")
                
        except Exception as e:
            logger.error(f"❌ Failed to execute transaction: {e}")
            logger.info("Transaction data prepared for manual execution:")
            logger.info(f"  To: {conditional_tokens_address}")
            logger.info(f"  Data: {function_call._encode_transaction_data().hex()}")
            raise
    
    except Exception as e:
        logger.error(f"❌ Failed to prepare claim transaction: {e}")
        raise

