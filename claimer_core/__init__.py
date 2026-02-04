"""
Polymarket Auto-Claimer Core Module

This module provides functionality to automatically claim winning positions
on Polymarket prediction markets.

Security Note:
- Always use a dedicated private key for automation (not your main key)
- Never commit .env files
- Run in isolated environment (VM/WSL/container)
"""

from .position_fetcher import fetchPositions
from .claim_filter import filterClaimables
from .tx_builder import buildRedeemTx
from .tx_sender import submitToSafe, submitDirect

__all__ = [
    'fetchPositions',
    'filterClaimables',
    'buildRedeemTx',
    'submitToSafe',
    'submitDirect',
]


