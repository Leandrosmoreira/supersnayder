"""
Module (A): Fetch Positions from Polymarket API

Responsible for fetching all positions from the Polymarket API.
"""

import requests
import logging
from typing import List, Dict, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Polymarket API endpoints
POLYMARKET_DATA_API = "https://data-api.polymarket.com"
POSITIONS_ENDPOINT = f"{POLYMARKET_DATA_API}/positions"

def create_session() -> requests.Session:
    """Create a requests session with retry strategy."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetchPositions(wallet_address: str, session: Optional[requests.Session] = None) -> List[Dict]:
    """
    Fetch all positions for a given wallet address from Polymarket API.
    
    Args:
        wallet_address: Ethereum wallet address (checksummed)
        session: Optional requests session (will create one if not provided)
    
    Returns:
        List of position dictionaries from the API
    
    Raises:
        requests.RequestException: If API request fails
    """
    if session is None:
        session = create_session()
    
    try:
        logger.info(f"Fetching positions for wallet: {wallet_address}")
        response = session.get(
            POSITIONS_ENDPOINT,
            params={"user": wallet_address},
            timeout=30
        )
        response.raise_for_status()
        
        positions = response.json()
        logger.info(f"✓ Fetched {len(positions)} positions from API")
        
        return positions
    
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to fetch positions: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error fetching positions: {e}")
        raise


