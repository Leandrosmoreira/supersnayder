"""
FASE 4: OrderIntent - Representa uma intenção de ordem (não bloqueia estratégia)
FASE 6: Otimizado com fixed-point
"""
from typing import Optional
import time
from poly_data.fixed_point import FixedPointPrice, FixedPointSize, USE_FIXED_POINT

class OrderIntent:
    """Intenção de ordem (não bloqueia estratégia).
    
    FASE 6: Usa fixed-point para price/size (ints) quando habilitado.
    FASE 6: Sem dataclass para permitir __slots__ (reduz overhead de alloc).
    """
    __slots__ = ['market', 'side', 'price', 'size', 'priority', 'timestamp', 'order_id']
    
    def __init__(self, market: str, side: str, price, size, priority: int = 0, timestamp: Optional[int] = None, order_id: Optional[str] = None):
        """Inicializa OrderIntent.
        
        Args:
            market: ID do mercado
            side: 'BUY' ou 'SELL'
            price: Preço (float ou int se fixed-point)
            size: Tamanho (float ou int)
            priority: Prioridade (0=normal, 1=high, 2=critical)
            timestamp: Timestamp em nanosegundos (opcional)
            order_id: ID da ordem (opcional)
        """
        self.market = market
        self.side = side
        
        # FASE 6: Converter para fixed-point se habilitado
        if USE_FIXED_POINT:
            if not isinstance(price, int):
                self.price = FixedPointPrice.to_int(price)
            else:
                self.price = price
            if not isinstance(size, int):
                self.size = FixedPointSize.to_int(size)
            else:
                self.size = size
        else:
            self.price = float(price)
            self.size = float(size)
        
        self.priority = priority
        self.timestamp = timestamp if timestamp is not None else time.monotonic_ns()
        self.order_id = order_id
    
    def get_price_float(self) -> float:
        """Retorna preço como float (para API)."""
        if USE_FIXED_POINT and isinstance(self.price, int):
            return FixedPointPrice.to_float(self.price)
        return float(self.price)
    
    def get_size_float(self) -> float:
        """Retorna tamanho como float (para API)."""
        if USE_FIXED_POINT and isinstance(self.size, int):
            return FixedPointSize.to_float(self.size)
        return float(self.size)

