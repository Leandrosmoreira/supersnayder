import gc  # Garbage collection
import time  # Time functions
import asyncio  # Asynchronous I/O
import traceback  # Exception handling
import logging  # Logging for debugging
import pandas as pd  # For reading Google Sheets
from poly_data.polymarket_client import PolymarketClient
from poly_data.data_utils import update_markets, update_positions, update_orders
from poly_data.websocket_handlers import connect_market_websocket, connect_user_websocket
import poly_data.global_state as global_state
from poly_data.data_processing import remove_from_performing
from poly_data.position_snapshot import log_position_snapshot
from poly_data.book_state import book_state_manager  # FASE 5
from poly_data.reconcile_task import reconcile_task  # FASE 5
from dotenv import load_dotenv
from data_updater.google_utils import get_spreadsheet  # Import to access Google Sheet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('main.log'),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

def update_once():
    """
    Initialize the application state by fetching market data, positions, and orders.
    """
    update_markets()  # Get market information from Google Sheets
    update_positions()  # Get current positions from Polymarket
    update_orders()  # Get current orders from Polymarket
    logger.info(f"Loaded {len(global_state.df)} markets from All Markets sheet")

def remove_from_pending():
    """
    Clean up stale trades that have been pending for too long (>15 seconds).
    """
    try:
        current_time = time.time()
        for col in list(global_state.performing.keys()):
            for trade_id in list(global_state.performing[col]):
                try:
                    if current_time - global_state.performing_timestamps[col].get(trade_id, current_time) > 15:
                        logger.info(f"Removing stale entry {trade_id} from {col} after 15 seconds")
                        remove_from_performing(col, trade_id)
                except:
                    logger.error(f"Error removing trade {trade_id} from {col}: {traceback.format_exc()}")
    except:
        logger.error(f"Error in remove_from_pending: {traceback.format_exc()}")

async def update_periodically():
    """
    Asynchronous function that periodically updates market data, positions, and orders.
    - Positions and orders every 10 seconds
    - Market data every 60 seconds (every 6 cycles)
    - Position snapshots every 5 minutes (every 30 cycles)
    - Stale pending trades removed each cycle
    """
    i = 1
    while True:
        await asyncio.sleep(10)  # Update every 10 seconds
        try:
            remove_from_pending()
            update_positions(avgOnly=True)
            update_orders()
            if i % 6 == 0:  # Every 60 seconds
                update_markets()
            if i % 30 == 0:  # Every 5 minutes (300 seconds)
                log_position_snapshot()
            i += 1
            if i > 30:
                i = 1
        except Exception as e:
            logger.error(f"Error in update_periodically: {e}")

async def main():
    """
    Main application entry point. Initializes client, data, and manages websocket connections.
    """
    # Initialize client with error handling
    try:
        logger.info("=" * 80)
        logger.info("STARTING POLYMARKET TRADING BOT")
        logger.info("=" * 80)
        global_state.client = PolymarketClient()
        logger.info("✓ Polymarket client initialized successfully")
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        logger.error("Please check your .env file and ensure PK and BROWSER_ADDRESS are set correctly.")
        return
    except RuntimeError as e:
        logger.error(f"❌ Authentication error: {e}")
        logger.error("Please verify your private key and API credentials are valid.")
        return
    except Exception as e:
        logger.error(f"❌ Unexpected error during client initialization: {e}")
        logger.error(traceback.format_exc())
        return

    # Initialize state and fetch initial data
    try:
        global_state.all_tokens = []
        update_once()
        logger.info(f"After initial updates: orders={global_state.orders}, positions={global_state.positions}")
    except Exception as e:
        logger.error(f"❌ Failed to load initial market data: {e}")
        logger.error("Please check your Google Sheets configuration and network connection.")
        return

    # Subscribe to WebSocket using subscribed_assets (token IDs), not condition_ids
    # subscribed_assets is populated by update_markets() in data_utils.py
    logger.info(f"Subscribing to WebSocket for {len(global_state.subscribed_assets)} token IDs: {global_state.subscribed_assets}")

    logger.info(
        f"There are {len(global_state.df)} markets, {len(global_state.positions)} positions, and {len(global_state.orders)} orders. Starting positions: {global_state.positions}")

    # Start periodic updates as an async task
    asyncio.create_task(update_periodically())
    
    # FASE 5: Inicializar BookStates com snapshot inicial (HTTP - apenas 1x)
    logger.info("FASE 5: Inicializando BookStates com snapshot inicial...")
    try:
        subscribed_list = list(global_state.subscribed_assets)
        logger.info(f"Inicializando BookStates para {len(subscribed_list)} mercados...")
        for idx, market_token in enumerate(subscribed_list[:10]):  # Limitar a 10 para não sobrecarregar
            try:
                order_book_result = global_state.client.get_order_book(market_token)
                if order_book_result and len(order_book_result) == 2:
                    bids_df, asks_df = order_book_result
                    bids = [(float(row['price']), float(row['size'])) for _, row in bids_df.iterrows()]
                    asks = [(float(row['price']), float(row['size'])) for _, row in asks_df.iterrows()]
                    
                    book_state = book_state_manager.get_book(market_token)
                    book_state.initialize_from_snapshot(bids, asks)
                    if (idx + 1) % 5 == 0:
                        logger.info(f"✓ {idx + 1}/{min(10, len(subscribed_list))} BookStates inicializados...")
            except Exception as e:
                logger.warning(f"Erro ao inicializar BookState para {market_token[:20]}...: {e}")
        logger.info("✓ BookStates inicializados com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar BookStates: {e}")
    
    # FASE 5: Iniciar reconcile task (fora do hot path - a cada 15s)
    logger.info("FASE 5: Iniciando reconcile task (intervalo: 15s)...")
    asyncio.create_task(reconcile_task(global_state.client))

    # Main loop - maintain websocket connections with backoff
    backoff_time = 5
    while True:
        try:
            # Connect to market and user websockets simultaneously
            # Subscribe using token IDs from subscribed_assets, not condition_ids
            await asyncio.gather(
                connect_market_websocket(list(global_state.subscribed_assets)),
                connect_user_websocket()
            )
            logger.info("Reconnecting to the websocket")
            backoff_time = 5  # Reset backoff on success
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(backoff_time)
            backoff_time = min(backoff_time * 2, 60)  # Exponential backoff up to 60 seconds

if __name__ == "__main__":
    asyncio.run(main())