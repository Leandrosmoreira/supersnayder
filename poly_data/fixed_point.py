"""
FASE 6: Fixed-point para preço/tamanho (ints em vez de floats)
Reduz overhead de conversão e melhora performance
"""
import os

# FASE 6: Configuração de escala (mils = 0.001 = 1 mil)
PRICE_SCALE = int(os.getenv('PRICE_SCALE', '1000'))  # Default: 1000 (mils)
USE_FIXED_POINT = os.getenv('USE_FIXED_POINT', 'true').lower() == 'true'

class FixedPointPrice:
    """Preço em fixed-point (int) para reduzir overhead de floats."""
    
    @staticmethod
    def to_int(price: float) -> int:
        """Converte float para int (mils).
        
        Args:
            price: Preço em float (ex: 0.534)
        
        Returns:
            Preço em int (ex: 534 para 0.534 com escala 1000)
        """
        if not USE_FIXED_POINT:
            return price
        return int(price * PRICE_SCALE)
    
    @staticmethod
    def to_float(price_int: int) -> float:
        """Converte int para float.
        
        Args:
            price_int: Preço em int (ex: 534)
        
        Returns:
            Preço em float (ex: 0.534)
        """
        if not USE_FIXED_POINT:
            return price_int
        return price_int / PRICE_SCALE
    
    @staticmethod
    def to_int_safe(price) -> int:
        """Converte para int de forma segura (aceita int ou float)."""
        if isinstance(price, int):
            return price if USE_FIXED_POINT else int(price * PRICE_SCALE)
        return FixedPointPrice.to_int(float(price))
    
    @staticmethod
    def to_float_safe(price) -> float:
        """Converte para float de forma segura (aceita int ou float)."""
        if isinstance(price, float):
            return price if not USE_FIXED_POINT else FixedPointPrice.to_float(int(price * PRICE_SCALE))
        return FixedPointPrice.to_float(int(price))

class FixedPointSize:
    """Tamanho em fixed-point (int) para reduzir overhead."""
    
    @staticmethod
    def to_int(size: float) -> int:
        """Converte float para int (shares sempre int).
        
        Args:
            size: Tamanho em float (ex: 5.0)
        
        Returns:
            Tamanho em int (ex: 5)
        """
        return int(size)
    
    @staticmethod
    def to_float(size_int: int) -> float:
        """Converte int para float.
        
        Args:
            size_int: Tamanho em int (ex: 5)
        
        Returns:
            Tamanho em float (ex: 5.0)
        """
        return float(size_int)
    
    @staticmethod
    def to_int_safe(size) -> int:
        """Converte para int de forma segura."""
        if isinstance(size, int):
            return size
        return int(float(size))
    
    @staticmethod
    def to_float_safe(size) -> float:
        """Converte para float de forma segura."""
        if isinstance(size, float):
            return size
        return float(int(size))

