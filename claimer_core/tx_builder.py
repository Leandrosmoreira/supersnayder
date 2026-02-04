"""
Module (C): Build Redeem Transaction

Constructs the transaction data (to + calldata) for redeeming winning positions.
"""

import logging
from typing import Dict, Optional, List
from web3 import Web3
from eth_utils import to_checksum_address

logger = logging.getLogger(__name__)

# Polymarket contract addresses (Polygon)
CONDITIONAL_TOKENS_ADDRESS = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # Polygon USDC

# Minimal ABI for redeemPositions
REDEEM_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "collateralToken", "type": "address"},
            {"name": "parentCollectionId", "type": "bytes32"},
            {"name": "conditionId", "type": "bytes32"},
            {"name": "indexSets", "type": "uint256[]"}
        ],
        "name": "redeemPositions",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def buildRedeemTx(
    claimable: Dict,
    web3: Optional[Web3] = None,
    conditional_tokens_address: str = CONDITIONAL_TOKENS_ADDRESS
) -> Dict:
    """
    Build transaction data for redeeming a winning position.
    
    Args:
        claimable: Claimable position dictionary from filterClaimables()
        web3: Optional Web3 instance (for encoding)
        conditional_tokens_address: Address of ConditionalTokens contract
    
    Returns:
        Dictionary with:
        - 'to': Contract address
        - 'data': Encoded function call data
        - 'value': 0 (no ETH sent)
        - 'position_info': Original position info for logging
    """
    try:
        # Extract position data
        asset = claimable.get('asset') or claimable.get('tokenId')  # Token ID
        condition_id = claimable.get('conditionId') or claimable.get('condition_id')
        collateral_token = claimable.get('collateralToken') or claimable.get('collateral_token', USDC_ADDRESS)
        parent_collection_id = claimable.get('parentCollectionId') or claimable.get('parent_collection_id', '0x0000000000000000000000000000000000000000000000000000000000000000')
        index_sets = claimable.get('indexSets') or claimable.get('index_sets', [])
        
        # If indexSets is not provided, we need to determine it from the position
        # For binary markets, it's typically [1] for YES or [2] for NO
        if not index_sets:
            # Try to infer from outcome field
            outcome = claimable.get('outcome', '').upper()
            outcome_index = claimable.get('outcomeIndex')
            
            # Use outcomeIndex if available (1 = YES, 2 = NO typically)
            if outcome_index is not None:
                # outcomeIndex is 0-based or 1-based? Check common patterns
                # Polymarket typically uses: 0 = YES, 1 = NO
                # But indexSets uses: 1 = YES, 2 = NO
                if outcome_index == 0:
                    index_sets = [1]  # YES
                elif outcome_index == 1:
                    index_sets = [2]  # NO
                else:
                    # Try to map directly
                    index_sets = [outcome_index + 1] if outcome_index < 2 else [outcome_index]
                logger.info(f"Using outcomeIndex {outcome_index} -> indexSets {index_sets}")
            elif outcome:
                # Map outcome name to indexSets
                if 'YES' in outcome or 'UP' in outcome:
                    index_sets = [1]
                elif 'NO' in outcome or 'DOWN' in outcome:
                    index_sets = [2]
                else:
                    # Default based on common patterns
                    index_sets = [1]
                    logger.warning(f"Could not determine indexSets from outcome '{outcome}', defaulting to [1]")
            else:
                # Try to infer from token ID or use default
                try:
                    if asset:
                        # For binary markets, we might need to check the opposite asset
                        # But without more info, default to [1]
                        index_sets = [1]
                        logger.warning(f"Could not determine indexSets from API, defaulting to [1] for {asset}")
                except:
                    index_sets = [1]
                    logger.warning(f"Could not parse token ID, defaulting to [1]")
        
        # Ensure addresses are checksummed
        collateral_token = to_checksum_address(collateral_token)
        conditional_tokens_address = to_checksum_address(conditional_tokens_address)
        
        # Convert condition_id to bytes32 if it's a string
        if condition_id is None:
            raise ValueError("conditionId is required but not found in position data")
        
        if isinstance(condition_id, str):
            # Remove 0x prefix if present
            if condition_id.startswith('0x'):
                condition_id_hex = condition_id[2:]
            else:
                condition_id_hex = condition_id
            
            # Convert to bytes
            try:
                condition_id = bytes.fromhex(condition_id_hex)
            except ValueError:
                raise ValueError(f"Invalid conditionId format: {condition_id}")
        
        # Ensure condition_id is exactly 32 bytes
        if len(condition_id) != 32:
            if len(condition_id) < 32:
                # Pad with zeros
                condition_id = condition_id.ljust(32, b'\x00')
            else:
                # Truncate
                condition_id = condition_id[:32]
        
        # Convert parent_collection_id to bytes32
        if isinstance(parent_collection_id, str):
            if parent_collection_id.startswith('0x'):
                parent_collection_id_hex = parent_collection_id[2:]
            else:
                parent_collection_id_hex = parent_collection_id
            
            try:
                parent_collection_id = bytes.fromhex(parent_collection_id_hex)
            except ValueError:
                # Default to zero bytes32
                parent_collection_id = bytes(32)
                logger.warning(f"Invalid parentCollectionId format, using zero bytes32")
        
        if len(parent_collection_id) != 32:
            if len(parent_collection_id) < 32:
                parent_collection_id = parent_collection_id.ljust(32, b'\x00')
            else:
                parent_collection_id = parent_collection_id[:32]
        
        # Build transaction
        tx_data = {
            'to': conditional_tokens_address,
            'value': 0,
            'data': None,  # Will be set below
            'position_info': {
                'asset': asset,
                'conditionId': condition_id.hex() if isinstance(condition_id, bytes) else condition_id,
                'redeemable': claimable.get('redeemable', 0),
                'market': claimable.get('market', 'Unknown'),
                'outcome': claimable.get('outcome', 'Unknown'),
            }
        }
        
        # Encode function call if web3 is provided
        if web3:
            try:
                contract = web3.eth.contract(
                    address=conditional_tokens_address,
                    abi=REDEEM_ABI
                )
                
                # Encode the function call
                function_call = contract.functions.redeemPositions(
                    collateral_token,
                    parent_collection_id,
                    condition_id,
                    index_sets
                )
                
                tx_data['data'] = function_call._encode_transaction_data()
                
            except Exception as e:
                logger.error(f"Failed to encode transaction: {e}")
                raise
        else:
            # If no web3, return structure without encoded data
            # Caller can encode it themselves
            logger.warning("No Web3 instance provided, returning transaction structure without encoded data")
            tx_data['params'] = {
                'collateralToken': collateral_token,
                'parentCollectionId': parent_collection_id.hex() if isinstance(parent_collection_id, bytes) else parent_collection_id,
                'conditionId': condition_id.hex() if isinstance(condition_id, bytes) else condition_id,
                'indexSets': index_sets
            }
        
        logger.info(f"✓ Built redeem transaction for position {asset}")
        return tx_data
    
    except Exception as e:
        logger.error(f"❌ Failed to build redeem transaction: {e}")
        raise

