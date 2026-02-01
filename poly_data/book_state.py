"""
FASE 5: BookState - Estado local do order book (atualizado via WebSocket)
Zero HTTP no hot path - apenas WebSocket para updates em tempo real
"""
import time
import threading
from typing import List, Tuple, Optional, Dict
from collections import OrderedDict
from sortedcontainers import SortedDict
import logging

logger = logging.getLogger(__name__)

class ImmutableBookSnapshot:
    """Snapshot imutável do book (sem locks, thread-safe para leitura)."""
    
    def __init__(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]], timestamp_ns: int):
        self.bids = tuple(bids)  # Imutável
        self.asks = tuple(asks)  # Imutável
        self.timestamp_ns = timestamp_ns
    
    def get_best_bid(self) -> float:
        """Retorna best bid (sem lock, snapshot imutável)."""
        return self.bids[0][0] if self.bids else 0.0
    
    def get_best_ask(self) -> float:
        """Retorna best ask (sem lock, snapshot imutável)."""
        return self.asks[0][0] if self.asks else 0.0
    
    def get_bid_size(self, price: float) -> float:
        """Retorna tamanho do bid no preço especificado."""
        for p, s in self.bids:
            if abs(p - price) < 0.00001:
                return s
        return 0.0
    
    def get_ask_size(self, price: float) -> float:
        """Retorna tamanho do ask no preço especificado."""
        for p, s in self.asks:
            if abs(p - price) < 0.00001:
                return s
        return 0.0

class BookState:
    """Estado local do order book (atualizado via WebSocket).
    
    FASE 5: Book 100% via WebSocket (zero HTTP no hot path)
    - Snapshot inicial (1x) via HTTP na inicialização
    - Depois só deltas via WebSocket
    - Manter estado local em memória
    """
    
    def __init__(self, market: str):
        self.market = market
        self.bids: SortedDict = SortedDict()  # price -> size (ordenado decrescente)
        self.asks: SortedDict = SortedDict()  # price -> size (ordenado crescente)
        self.last_update_ns: int = 0
        self.last_snapshot_ns: int = 0
        self._lock = threading.Lock()
        self._current_snapshot: Optional[ImmutableBookSnapshot] = None
        self._snapshot_lock = threading.Lock()
        self.initialized = False
    
    def initialize_from_snapshot(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]]):
        """Inicializa o book a partir de um snapshot (HTTP - apenas 1x na inicialização)."""
        with self._lock:
            self.bids.clear()
            self.asks.clear()
            
            # Adicionar bids (ordenado decrescente)
            for price, size in sorted(bids, key=lambda x: -x[0]):  # Ordenar decrescente
                if size > 0:
                    self.bids[price] = size
            
            # Adicionar asks (ordenado crescente)
            for price, size in sorted(asks, key=lambda x: x[0]):  # Ordenar crescente
                if size > 0:
                    self.asks[price] = size
            
            self.last_update_ns = time.monotonic_ns()
            self.last_snapshot_ns = self.last_update_ns
            self.initialized = True
            
            # Criar snapshot imutável
            self._update_snapshot()
            
            logger.info(f"✅ BookState inicializado para {self.market[:20]}... ({len(self.bids)} bids, {len(self.asks)} asks)")
    
    async def apply_delta(self, delta: dict):
        """Aplica delta do WebSocket ao book (FASE 5: hot path - sem HTTP).
        
        Args:
            delta: Dicionário com 'bids' e/ou 'asks' contendo updates
        """
        with self._lock:
            # Processar bids
            if 'bids' in delta:
                for entry in delta['bids']:
                    price = float(entry['price'])
                    size = float(entry.get('size', entry.get('amount', 0)))
                    
                    if size == 0:
                        # Remover nível de preço
                        if price in self.bids:
                            del self.bids[price]
                    else:
                        # Adicionar ou atualizar nível de preço
                        self.bids[price] = size
            
            # Processar asks
            if 'asks' in delta:
                for entry in delta['asks']:
                    price = float(entry['price'])
                    size = float(entry.get('size', entry.get('amount', 0)))
                    
                    if size == 0:
                        # Remover nível de preço
                        if price in self.asks:
                            del self.asks[price]
                    else:
                        # Adicionar ou atualizar nível de preço
                        self.asks[price] = size
            
            self.last_update_ns = time.monotonic_ns()
            
            # Atualizar snapshot imutável
            self._update_snapshot()
    
    def _update_snapshot(self):
        """Atualiza snapshot imutável (chamado dentro do lock)."""
        # Converter para lista de tuplas
        bids_list = [(price, size) for price, size in self.bids.items()]
        asks_list = [(price, size) for price, size in self.asks.items()]
        
        # Criar snapshot imutável
        with self._snapshot_lock:
            self._current_snapshot = ImmutableBookSnapshot(
                bids_list,
                asks_list,
                self.last_update_ns
            )
    
    def get_snapshot(self) -> Optional[ImmutableBookSnapshot]:
        """Retorna snapshot imutável atual (sem lock, thread-safe para leitura)."""
        with self._snapshot_lock:
            return self._current_snapshot
    
    def get_best_bid(self) -> float:
        """Retorna best bid (sem lock, snapshot imutável)."""
        snapshot = self.get_snapshot()
        if snapshot:
            return snapshot.get_best_bid()
        return 0.0
    
    def get_best_ask(self) -> float:
        """Retorna best ask (sem lock, snapshot imutável)."""
        snapshot = self.get_snapshot()
        if snapshot:
            return snapshot.get_best_ask()
        return 0.0
    
    def reconcile(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]]):
        """Reconcilia com snapshot externo (fora do hot path - FASE 5).
        
        Args:
            bids: Lista de (price, size) para bids
            asks: Lista de (price, size) para asks
        """
        with self._lock:
            # Comparar e atualizar se necessário
            # Por simplicidade, vamos re-inicializar com o snapshot
            self.initialize_from_snapshot(bids, asks)
            self.last_snapshot_ns = time.monotonic_ns()
            logger.debug(f"BookState reconciliado para {self.market[:20]}...")
    
    def get_age_ms(self) -> float:
        """Retorna idade do último update em milissegundos."""
        if self.last_update_ns == 0:
            return float('inf')
        return (time.monotonic_ns() - self.last_update_ns) / 1_000_000
    
    def is_stale(self, max_age_ms: float = 5000) -> bool:
        """Verifica se o book está desatualizado."""
        return self.get_age_ms() > max_age_ms

# Gerenciador global de BookStates
class BookStateManager:
    """Gerenciador global de BookStates (FASE 5)."""
    
    def __init__(self):
        self._books: Dict[str, BookState] = {}
        self._lock = threading.Lock()
    
    def get_book(self, market: str) -> BookState:
        """Retorna ou cria BookState para um mercado."""
        with self._lock:
            if market not in self._books:
                self._books[market] = BookState(market)
            return self._books[market]
    
    def get_all_books(self) -> Dict[str, BookState]:
        """Retorna todos os BookStates."""
        with self._lock:
            return self._books.copy()
    
    def remove_book(self, market: str):
        """Remove BookState de um mercado."""
        with self._lock:
            if market in self._books:
                del self._books[market]

# Instância global
book_state_manager = BookStateManager()

