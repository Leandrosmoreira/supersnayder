"""
FASE 6: Payload templates para reduzir overhead de criação de dicts
Prealloc e reuse de estruturas
"""
from typing import Dict, Any
from poly_data.fixed_point import FixedPointPrice, FixedPointSize

class PayloadTemplate:
    """Template de payload pré-definido (só trocar price/size).
    
    FASE 6: Reduz overhead de criação de dicts e conversões.
    """
    
    def __init__(self, market: str, side: str, order_type: str = 'GTC'):
        """Inicializa template com campos fixos."""
        self.market = market
        self.side = side
        self.order_type = order_type
        
        # Template base (campos fixos pré-definidos)
        self._base_template = {
            'token_id': market,
            'side': side,
            'order_type': order_type,
            'price': 0,  # Será substituído
            'size': 0    # Será substituído
        }
    
    def build(self, price_int: int, size_int: int) -> Dict[str, Any]:
        """Constrói payload (reutiliza template).
        
        Args:
            price_int: Preço em fixed-point (int)
            size_int: Tamanho em int
        
        Returns:
            Payload pronto para envio
        """
        # FASE 6: Reutilizar template (evitar criar dict novo)
        payload = self._base_template.copy()
        
        # Converter apenas price/size (campos variáveis)
        if USE_FIXED_POINT:
            payload['price'] = FixedPointPrice.to_float(price_int)
        else:
            payload['price'] = price_int
        
        payload['size'] = FixedPointSize.to_float(size_int)
        
        return payload
    
    def build_from_float(self, price: float, size: float) -> Dict[str, Any]:
        """Constrói payload a partir de floats (compatibilidade).
        
        Args:
            price: Preço em float
            size: Tamanho em float
        
        Returns:
            Payload pronto para envio
        """
        price_int = FixedPointPrice.to_int(price)
        size_int = FixedPointSize.to_int(size)
        return self.build(price_int, size_int)

# FASE 6: Cache de templates (reutilizar templates por market/side)
_template_cache: Dict[str, PayloadTemplate] = {}

def get_payload_template(market: str, side: str, order_type: str = 'GTC') -> PayloadTemplate:
    """Retorna ou cria template (com cache para reutilização).
    
    FASE 6: Reutilizar templates para reduzir overhead.
    """
    cache_key = f"{market}:{side}:{order_type}"
    
    if cache_key not in _template_cache:
        _template_cache[cache_key] = PayloadTemplate(market, side, order_type)
    
    return _template_cache[cache_key]

# Importar USE_FIXED_POINT
from poly_data.fixed_point import USE_FIXED_POINT

