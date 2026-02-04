"""
Module (D): Submit Transaction to Safe or Execute Directly

Sends the transaction to Gnosis Safe for execution, or executes directly.
"""

import logging
import time
from typing import Dict, Optional
from web3 import Web3
from eth_account import Account
from eth_utils import to_checksum_address

logger = logging.getLogger(__name__)

def submitToSafe(
    tx_data: Dict,
    safe_address: str,
    web3: Optional[Web3] = None,
    private_key: Optional[str] = None
) -> Dict:
    """
    Submit transaction to Gnosis Safe for execution.
    
    Note: This is a placeholder implementation. Full Safe integration requires
    the Safe SDK or direct interaction with the Safe contract.
    
    Args:
        tx_data: Transaction data from buildRedeemTx()
        safe_address: Gnosis Safe address
        web3: Web3 instance
        private_key: Private key for signing (if needed for Safe API)
    
    Returns:
        Dictionary with transaction hash or Safe transaction hash
    """
    logger.warning("⚠️  Safe submission not fully implemented - requires Safe SDK")
    logger.info(f"Would submit transaction to Safe: {safe_address}")
    logger.info(f"Transaction data: {tx_data.get('position_info', {})}")
    
    # TODO: Implement full Safe integration using:
    # - Safe SDK (https://github.com/safe-global/safe-core-sdk)
    # - Or direct Safe contract interaction
    # - Or Safe Transaction Service API
    
    return {
        'status': 'pending',
        'safe_address': safe_address,
        'message': 'Safe submission requires Safe SDK implementation'
    }

def submitDirect(
    tx_data: Dict,
    web3: Web3,
    private_key: str,
    gas_price: Optional[int] = None,
    gas_limit: Optional[int] = None
) -> Dict:
    """
    Execute transaction directly (not through Safe).
    
    ⚠️  WARNING: Only use this if you're comfortable executing transactions
    directly from your wallet. For production, prefer Safe.
    
    Args:
        tx_data: Transaction data from buildRedeemTx()
        web3: Web3 instance connected to Polygon
        private_key: Private key for signing
        gas_price: Optional gas price (will use web3.eth.gas_price if not provided)
        gas_limit: Optional gas limit (will estimate if not provided)
    
    Returns:
        Dictionary with transaction hash and status
    """
    try:
        # Get account from private key
        account = Account.from_key(private_key)
        sender_address = to_checksum_address(account.address)
        
        logger.info(f"Executing transaction from {sender_address}")
        
        # Check MATIC balance for gas
        try:
            matic_balance = web3.eth.get_balance(sender_address)
            matic_balance_eth = web3.from_wei(matic_balance, 'ether')
            logger.info(f"MATIC balance: {matic_balance_eth:.6f} MATIC")
            
            if matic_balance == 0:
                logger.error("=" * 80)
                logger.error("❌ ERRO: Sem saldo MATIC!")
                logger.error("=" * 80)
                logger.error("Você precisa de MATIC na carteira para pagar as taxas de gas.")
                logger.error("O claim em si é gratuito, mas a transação precisa de MATIC.")
                logger.error("")
                logger.error("Solução:")
                logger.error("1. Envie MATIC para sua carteira: " + sender_address)
                logger.error("2. Você precisa de pelo menos 0.01 MATIC (~$0.01)")
                logger.error("3. Pode comprar MATIC em exchanges ou usar uma bridge")
                logger.error("=" * 80)
                raise ValueError("Insufficient MATIC balance for gas")
            elif matic_balance < web3.to_wei(0.001, 'ether'):
                logger.warning(f"⚠️  Saldo MATIC baixo ({matic_balance_eth:.6f} MATIC). Pode falhar.")
        except ValueError:
            # Re-raise ValueError (insufficient balance)
            raise
        except Exception as e:
            logger.warning(f"Could not check MATIC balance: {e}")
        
        # Build transaction
        tx = {
            'to': tx_data['to'],
            'data': tx_data['data'],
            'value': tx_data.get('value', 0),
            'from': sender_address,
            'nonce': web3.eth.get_transaction_count(sender_address),
            'chainId': web3.eth.chain_id,
        }
        
        # Set gas price
        if gas_price:
            tx['gasPrice'] = gas_price
        else:
            tx['gasPrice'] = web3.eth.gas_price
        
        # Estimate or set gas limit (with retry for rate limits)
        if gas_limit:
            tx['gas'] = gas_limit
        else:
            max_retries = 3
            retry_delay = 10  # seconds
            for attempt in range(max_retries):
                try:
                    estimated_gas = web3.eth.estimate_gas(tx)
                    tx['gas'] = int(estimated_gas * 1.2)  # Add 20% buffer
                    logger.info(f"Estimated gas: {estimated_gas}, using {tx['gas']}")
                    break
                except Exception as e:
                    error_msg = str(e)
                    if 'rate limit' in error_msg.lower() or 'too many requests' in error_msg.lower():
                        if attempt < max_retries - 1:
                            wait_time = retry_delay * (attempt + 1)
                            logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.error("❌ Rate limit exceeded after retries. Try again later or use a different RPC.")
                            raise
                    else:
                        logger.warning(f"Gas estimation failed: {e}, using default 500000")
                        tx['gas'] = 500000
                        break
        
        # Sign transaction
        signed_tx = account.sign_transaction(tx)
        
        # Get raw transaction (web3.py v6+ uses .raw_transaction)
        # Try both naming conventions for compatibility
        if hasattr(signed_tx, 'raw_transaction'):
            raw_tx = signed_tx.raw_transaction
        elif hasattr(signed_tx, 'rawTransaction'):
            raw_tx = signed_tx.rawTransaction
        else:
            # Fallback: try to get from dict or access directly
            raw_tx = getattr(signed_tx, 'raw_transaction', None) or getattr(signed_tx, 'rawTransaction', None)
            if raw_tx is None:
                raise ValueError(f"Could not extract raw transaction. Signed tx type: {type(signed_tx)}, attributes: {dir(signed_tx)}")
        
        # Send transaction (with retry for rate limits)
        max_retries = 3
        retry_delay = 10
        tx_hash = None
        
        for attempt in range(max_retries):
            try:
                tx_hash = web3.eth.send_raw_transaction(raw_tx)
                break
            except Exception as e:
                error_msg = str(e)
                if 'rate limit' in error_msg.lower() or 'too many requests' in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("❌ Rate limit exceeded after retries. Try again later or use a different RPC.")
                        raise
                else:
                    raise
        
        tx_hash_hex = tx_hash.hex()
        logger.info(f"✓ Transaction sent: {tx_hash_hex}")
        
        # Wait for receipt (optional - can be done separately)
        try:
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            status = 'success' if receipt.status == 1 else 'failed'
            logger.info(f"✓ Transaction {status}: {tx_hash_hex}")
            
            return {
                'status': status,
                'tx_hash': tx_hash_hex,
                'receipt': dict(receipt),
                'position_info': tx_data.get('position_info', {})
            }
        except Exception as e:
            logger.warning(f"Transaction sent but receipt wait failed: {e}")
            return {
                'status': 'pending',
                'tx_hash': tx_hash_hex,
                'position_info': tx_data.get('position_info', {})
            }
    
    except Exception as e:
        logger.error(f"❌ Failed to execute transaction: {e}")
        raise


