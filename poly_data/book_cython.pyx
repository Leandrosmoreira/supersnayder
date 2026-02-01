# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

"""
FASE 8: Cython hot path para operações críticas do orderbook.
- Update do orderbook (apply deltas)
- Compute quotes (cálculo de cotações)
- Operações de busca (best bid/ask)
"""

from libc.stdlib cimport malloc, free
from libc.string cimport memcpy
cimport cython

cdef struct PriceLevel:
    double price
    double size

cdef struct BookDelta:
    double price
    double size
    int is_bid  # 1 para bid, 0 para ask
    int is_remove  # 1 para remover, 0 para adicionar/atualizar

@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline double get_best_bid_price(PriceLevel* bids, int num_bids) nogil:
    """Retorna o melhor preço de bid (maior preço)."""
    if num_bids == 0:
        return 0.0
    
    cdef double best = bids[0].price
    cdef int i
    for i in range(1, num_bids):
        if bids[i].price > best:
            best = bids[i].price
    return best

@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline double get_best_ask_price(PriceLevel* asks, int num_asks) nogil:
    """Retorna o melhor preço de ask (menor preço)."""
    if num_asks == 0:
        return 0.0
    
    cdef double best = asks[0].price
    cdef int i
    for i in range(1, num_asks):
        if asks[i].price < best:
            best = asks[i].price
    return best

@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline double get_best_bid_size(PriceLevel* bids, int num_bids, double best_price) nogil:
    """Retorna o tamanho do melhor bid."""
    cdef int i
    for i in range(num_bids):
        if bids[i].price == best_price:
            return bids[i].size
    return 0.0

@cython.boundscheck(False)
@cython.wraparound(False)
cdef inline double get_best_ask_size(PriceLevel* asks, int num_asks, double best_price) nogil:
    """Retorna o tamanho do melhor ask."""
    cdef int i
    for i in range(num_asks):
        if asks[i].price == best_price:
            return asks[i].size
    return 0.0

def compute_spread_fast(list bids_list, list asks_list):
    """Calcula spread de forma otimizada (Cython).
    
    Args:
        bids_list: Lista de tuplas (price, size) para bids
        asks_list: Lista de tuplas (price, size) para asks
    
    Returns:
        (best_bid, best_ask, spread)
    """
    cdef int num_bids = len(bids_list)
    cdef int num_asks = len(asks_list)
    
    if num_bids == 0 or num_asks == 0:
        return (0.0, 0.0, 0.0)
    
    # Converter para arrays C
    cdef PriceLevel* bids = <PriceLevel*>malloc(num_bids * sizeof(PriceLevel))
    cdef PriceLevel* asks = <PriceLevel*>malloc(num_asks * sizeof(PriceLevel))
    
    cdef int i
    cdef double price, size
    cdef double best_bid_price, best_ask_price, best_bid_size, best_ask_size, spread
    
    try:
        # Preencher bids
        for i in range(num_bids):
            price, size = bids_list[i]
            bids[i].price = price
            bids[i].size = size
        
        # Preencher asks
        for i in range(num_asks):
            price, size = asks_list[i]
            asks[i].price = price
            asks[i].size = size
        
        # Calcular best bid/ask
        best_bid_price = get_best_bid_price(bids, num_bids)
        best_ask_price = get_best_ask_price(asks, num_asks)
        best_bid_size = get_best_bid_size(bids, num_bids, best_bid_price)
        best_ask_size = get_best_ask_size(asks, num_asks, best_ask_price)
        
        spread = best_ask_price - best_bid_price if best_ask_price > 0 and best_bid_price > 0 else 0.0
        
        return (best_bid_price, best_ask_price, spread)
    
    finally:
        free(bids)
        free(asks)

def compute_quote_fast(double price, double size, double best_bid, double best_ask, int side):
    """Calcula quote de forma otimizada (Cython).
    
    Args:
        price: Preço da ordem
        size: Tamanho da ordem
        best_bid: Melhor bid atual
        best_ask: Melhor ask atual
        side: 1 para BUY, 0 para SELL
    
    Returns:
        (quote_price, quote_size, is_maker)
    """
    cdef double quote_price = price
    cdef double quote_size = size
    cdef int is_maker = 0
    
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
    
    return (quote_price, quote_size, is_maker)

