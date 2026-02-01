"""
FASE 4: OrderIntent - Representa uma intenção de ordem (não bloqueia estratégia)
"""
from dataclasses import dataclass
from typing import Optional
import time

@dataclass
class OrderIntent:
    """Intenção de ordem (não bloqueia estratégia)."""
    market: str
    side: str  # 'BUY' or 'SELL'
    price: float
    size: float
    priority: int = 0  # 0=normal, 1=high, 2=critical
    timestamp: float = None
    order_id: Optional[str] = None  # Preenchido após envio
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.monotonic_ns()

