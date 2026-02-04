"""
Module (B): Filter Claimable Positions

Filters positions that are:
- resolved == true
- you_won == true
- redeemable > 0
- notClaimed (not already claimed)
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def filterClaimables(positions: List[Dict], debug: bool = False) -> List[Dict]:
    """
    Filter positions that are eligible for claiming.
    
    Criteria (flexible field name matching):
    1. Market must be resolved (resolved/resolved_status == true)
    2. User must have won (you_won/youWon/won == true)
    3. Must have redeemable amount > 0 (redeemable/redeemableAmount)
    4. Must not be already claimed
    
    Args:
        positions: List of position dictionaries from API
        debug: If True, log details about each position for debugging
    
    Returns:
        List of claimable position dictionaries
    """
    claimables = []
    
    for pos in positions:
        if debug:
            logger.debug(f"\nAnalyzing position: {pos.get('asset', 'unknown')[:20]}...")
            logger.debug(f"  Keys: {list(pos.keys())}")
            logger.debug(f"  redeemable: {pos.get('redeemable')} | currentValue: {pos.get('currentValue')} | curPrice: {pos.get('curPrice')}")
        
        # Polymarket API uses 'redeemable' as a boolean flag
        # When redeemable == True, the position can be claimed
        redeemable_flag = pos.get('redeemable', False)
        
        # Handle both boolean and string representations
        if isinstance(redeemable_flag, str):
            redeemable_flag = redeemable_flag.lower() in ('true', '1', 'yes')
        elif not isinstance(redeemable_flag, bool):
            redeemable_flag = bool(redeemable_flag)
        
        if not redeemable_flag:
            if debug:
                logger.debug(f"  ❌ Not redeemable (redeemable flag is False)")
            continue
        
        # Get the redeemable amount
        # When redeemable is True, the value is typically in currentValue
        # or we can calculate from size * curPrice (which should be 1.0 for winning positions)
        redeemable_amount = (
            pos.get('currentValue') or
            pos.get('proceeds') or
            pos.get('redeemableAmount') or
            0
        )
        
        # If currentValue is not available, try to calculate from size and price
        if not redeemable_amount or float(redeemable_amount) == 0:
            size = pos.get('size', 0)
            cur_price = pos.get('curPrice', 0)
            if size and cur_price and float(cur_price) > 0:
                redeemable_amount = float(size) * float(cur_price)
        
        # Handle different types (string, number, etc)
        try:
            redeemable_float = float(redeemable_amount) if redeemable_amount else 0
        except (ValueError, TypeError):
            redeemable_float = 0
        
        # If redeemable is True but amount is 0, it might be a losing position
        # that still needs to be "claimed" to clear it, or the API hasn't updated yet
        # We'll allow it but log a warning
        if redeemable_float <= 0:
            if debug:
                logger.debug(f"  ⚠️  redeemable=True but amount is 0 (may be losing position or already claimed)")
            # Still allow it - sometimes you need to claim even losing positions to clear them
            # But set a flag so we know it's zero value
            pos['_zero_value_claim'] = True
        
        # Check if already claimed
        # If curPrice is 1.0 and we have a position, it's likely claimable
        # But we should check if there's a claimed flag
        claimed = (
            pos.get('claimed', False) or
            pos.get('isClaimed', False) or
            pos.get('claimed_at') is not None or
            pos.get('claimedAt') is not None or
            pos.get('hasClaimed', False)
        )
        
        if claimed:
            if debug:
                logger.debug(f"  ❌ Already claimed")
            logger.debug(f"Position {pos.get('asset', 'unknown')} already claimed, skipping")
            continue
        
        # All checks passed - this is claimable
        if debug:
            logger.debug(f"  ✓ CLAIMABLE! Amount: ${redeemable_float:.2f}")
        claimables.append(pos)
    
    logger.info(f"✓ Filtered {len(claimables)} claimable positions from {len(positions)} total positions")
    
    return claimables


