# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False

"""
FASE 8: Cython payload builder para criação eficiente de JSON.
"""

cimport cython
from libc.string cimport memcpy

@cython.boundscheck(False)
@cython.wraparound(False)
def build_order_payload_fast(str market_id, str action, double price, double size, int price_scale=1000):
    """Constrói payload de ordem de forma otimizada (Cython).
    
    Args:
        market_id: ID do mercado
        action: 'BUY' ou 'SELL'
        price: Preço (float)
        size: Tamanho (float)
        price_scale: Escala para conversão (default 1000 = mils)
    
    Returns:
        dict pronto para serialização JSON
    """
    # Converter preço para int (fixed-point)
    cdef int price_int = <int>(price * price_scale)
    cdef int size_int = <int>(size)
    
    # Construir payload
    cdef dict payload = {
        'token_id': market_id,
        'price': price_int,
        'size': size_int,
        'side': action
    }
    
    return payload

