"""
FASE 8: Wrapper para módulos Cython (fallback para Python puro se Cython não disponível).
"""

try:
    from poly_data import book_cython
    from poly_data import payload_builder_cython
    CYTHON_AVAILABLE = True
except ImportError:
    CYTHON_AVAILABLE = False
    book_cython = None
    payload_builder_cython = None

def compute_spread_fast(bids_list, asks_list):
    """Calcula spread usando Cython se disponível, senão usa Python puro."""
    if CYTHON_AVAILABLE:
        return book_cython.compute_spread_fast(bids_list, asks_list)
    else:
        # Fallback Python puro
        if not bids_list or not asks_list:
            return (0.0, 0.0, 0.0)
        
        best_bid = max(bids_list, key=lambda x: x[0])[0] if bids_list else 0.0
        best_ask = min(asks_list, key=lambda x: x[0])[0] if asks_list else 0.0
        spread = best_ask - best_bid if best_ask > 0 and best_bid > 0 else 0.0
        return (best_bid, best_ask, spread)

def compute_quote_fast(price, size, best_bid, best_ask, side):
    """Calcula quote usando Cython se disponível, senão usa Python puro."""
    if CYTHON_AVAILABLE:
        return book_cython.compute_quote_fast(price, size, best_bid, best_ask, side)
    else:
        # Fallback Python puro
        is_maker = 0
        if side == 1:  # BUY
            if price < best_bid:
                is_maker = 1
            elif price >= best_ask:
                is_maker = 0
            else:
                is_maker = 1
        else:  # SELL
            if price > best_ask:
                is_maker = 1
            elif price <= best_bid:
                is_maker = 0
            else:
                is_maker = 1
        
        return (price, size, is_maker)

def build_order_payload_fast(market_id, action, price, size, price_scale=1000):
    """Constrói payload usando Cython se disponível, senão usa Python puro."""
    if CYTHON_AVAILABLE:
        return payload_builder_cython.build_order_payload_fast(market_id, action, price, size, price_scale)
    else:
        # Fallback Python puro
        price_int = int(price * price_scale)
        size_int = int(size)
        return {
            'token_id': market_id,
            'price': price_int,
            'size': size_int,
            'side': action
        }

