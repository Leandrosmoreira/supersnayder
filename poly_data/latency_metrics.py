"""
FASE 0: Sistema de métricas de latência
FASE 7: Otimizado com menos locks (lock-free quando possível)
Mede t_decision, t_send, t_ack para análise de performance
"""
import time
import threading
from collections import deque
from typing import Dict, List, Optional
import json

class LatencyMetrics:
    """Coleta métricas de latência com percentis.
    
    FASE 7: Otimizado com lock mais granular (menos contenção).
    """
    
    def __init__(self, buffer_size=1000):
        self.buffer_size = buffer_size
        self.t_decision: Dict[str, deque] = {}  # market -> deque de nanosegundos
        self.t_send: Dict[str, deque] = {}
        self.t_ack: Dict[str, deque] = {}
        # FASE 7: Lock mais granular (um por métrica seria ideal, mas deque já é thread-safe para append)
        # Para simplicidade, mantemos um lock, mas reduzimos tempo de lock
        self._lock = threading.Lock()
        self.enabled = True
    
    def record_decision(self, market: str, duration_ns: int):
        """Registra t_decision para um mercado.
        
        FASE 7: Lock apenas para criar deque (se necessário), append é thread-safe.
        """
        if not self.enabled:
            return
        # FASE 7: Lock apenas para verificar/criar deque, não para append
        if market not in self.t_decision:
            with self._lock:
                if market not in self.t_decision:  # Double-check
                    self.t_decision[market] = deque(maxlen=self.buffer_size)
        # deque.append() é thread-safe (atomic)
        self.t_decision[market].append(duration_ns)
    
    def record_send(self, market: str, duration_ns: int):
        """Registra t_send para um mercado.
        
        FASE 7: Lock apenas para criar deque (se necessário), append é thread-safe.
        """
        if not self.enabled:
            return
        if market not in self.t_send:
            with self._lock:
                if market not in self.t_send:  # Double-check
                    self.t_send[market] = deque(maxlen=self.buffer_size)
        self.t_send[market].append(duration_ns)
    
    def record_ack(self, market: str, duration_ns: int):
        """Registra t_ack para um mercado.
        
        FASE 7: Lock apenas para criar deque (se necessário), append é thread-safe.
        """
        if not self.enabled:
            return
        if market not in self.t_ack:
            with self._lock:
                if market not in self.t_ack:  # Double-check
                    self.t_ack[market] = deque(maxlen=self.buffer_size)
        self.t_ack[market].append(duration_ns)
    
    def get_percentiles(self, values: deque, percentiles=[50, 90, 99]):
        """Calcula percentis de uma série de valores (ns -> ms)."""
        if not values:
            return {}
        sorted_vals = sorted(values)
        result = {}
        for p in percentiles:
            idx = min(int(len(sorted_vals) * p / 100), len(sorted_vals) - 1)
            result[f'p{p}'] = sorted_vals[idx] / 1_000_000  # ns -> ms
        return result
    
    def get_all_metrics(self, market: Optional[str] = None):
        """Retorna todas as métricas (por market ou total)."""
        with self._lock:
            if market:
                return {
                    't_decision': self.get_percentiles(self.t_decision.get(market, deque())),
                    't_send': self.get_percentiles(self.t_send.get(market, deque())),
                    't_ack': self.get_percentiles(self.t_ack.get(market, deque()))
                }
            else:
                # Total (todos os markets)
                all_decision = deque()
                all_send = deque()
                all_ack = deque()
                
                for market_deque in self.t_decision.values():
                    all_decision.extend(market_deque)
                for market_deque in self.t_send.values():
                    all_send.extend(market_deque)
                for market_deque in self.t_ack.values():
                    all_ack.extend(market_deque)
                
                return {
                    't_decision': self.get_percentiles(all_decision),
                    't_send': self.get_percentiles(all_send),
                    't_ack': self.get_percentiles(all_ack)
                }
    
    def report(self, market: Optional[str] = None):
        """Gera relatório de métricas."""
        metrics = self.get_all_metrics(market)
        report = []
        report.append("=" * 80)
        report.append(f"📊 RELATÓRIO DE LATÊNCIA {'(' + market + ')' if market else '(TOTAL)'}")
        report.append("=" * 80)
        
        for metric_name, percentiles in metrics.items():
            if percentiles:
                report.append(f"\n{metric_name.upper()}:")
                for p_name, p_value in percentiles.items():
                    report.append(f"  {p_name}: {p_value:.2f}ms")
            else:
                report.append(f"\n{metric_name.upper()}: Sem dados")
        
        report.append("=" * 80)
        return "\n".join(report)
    
    def reset(self):
        """Limpa todas as métricas."""
        with self._lock:
            self.t_decision.clear()
            self.t_send.clear()
            self.t_ack.clear()

# Instância global
metrics = LatencyMetrics()

