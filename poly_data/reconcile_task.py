"""
FASE 5: Reconcile Task - Reconciliação fora do hot path
Roda a cada 15s para garantir consistência do book state
"""
import asyncio
import logging
from typing import Dict
from poly_data.book_state import book_state_manager
from poly_data.polymarket_client import PolymarketClient

logger = logging.getLogger(__name__)

RECONCILE_INTERVAL_S = 15  # Reconciliar a cada 15 segundos

async def reconcile_task(client: PolymarketClient):
    """Task de reconciliação (fora do hot path - FASE 5).
    
    Reconcilia o estado local do book com snapshot da API (HTTP).
    Roda periodicamente para garantir consistência.
    """
    logger.info(f"🔄 Reconcile task iniciada (intervalo: {RECONCILE_INTERVAL_S}s)")
    
    while True:
        try:
            await asyncio.sleep(RECONCILE_INTERVAL_S)
            
            books = book_state_manager.get_all_books()
            
            if not books:
                continue
            
            logger.debug(f"🔄 Reconciliando {len(books)} books...")
            
            reconciled = 0
            errors = 0
            
            for market, book_state in books.items():
                try:
                    # Buscar snapshot via HTTP (fora do hot path)
                    # FASE 5: Isso não bloqueia o hot path, roda em background
                    order_book_result = await asyncio.to_thread(
                        client.get_order_book, market
                    )
                    
                    if order_book_result and len(order_book_result) == 2:
                        bids_df, asks_df = order_book_result
                        
                        # Converter para lista de tuplas
                        bids = [(float(row['price']), float(row['size'])) 
                               for _, row in bids_df.iterrows()]
                        asks = [(float(row['price']), float(row['size'])) 
                               for _, row in asks_df.iterrows()]
                        
                        # Reconciliar com estado local
                        book_state.reconcile(bids, asks)
                        reconciled += 1
                        
                except Exception as e:
                    errors += 1
                    logger.error(f"❌ Erro ao reconciliar book {market[:20]}...: {e}")
            
            if reconciled > 0:
                logger.info(f"✅ Reconciliados {reconciled} books ({errors} erros)")
            
        except Exception as e:
            logger.error(f"❌ Erro na reconcile task: {e}", exc_info=True)
            await asyncio.sleep(5)  # Aguardar um pouco antes de tentar novamente

