# 🚀 PLANO NOVO — Redução de Latência (Fase 4–8)
## Incorporando Melhorias Avançadas

**Data:** 2026-02-01  
**Status Atual:** Fase 3 completa (440ms, 37.5% de melhoria)  
**Meta Realista:** ~320-380ms p50, reduzir p99/p999 (menos jitter)

**Regra:** Apenas mudanças de programação/software (sem trocar servidor/ISP)

---

## 📊 FASE 0: MEDIÇÃO OBRIGATÓRIA (Antes de Mexer)

### Objetivo
Separar o que é "tempo local" vs "rede/servidor" para identificar gargalos reais.

### 0.1 Definição de 3 Métricas de Latência

#### **t_decision** = book_update → intents gerados
- **O que mede:** Tempo de processamento da estratégia
- **Onde:** Entre recebimento de book update e criação de OrderIntent
- **Timestamp:** `time.monotonic_ns()` no início e fim

#### **t_send** = intents gerados → request bytes pronto + enviado ao socket
- **O que mede:** Tempo de preparação e envio da requisição
- **Onde:** Entre criação de OrderIntent e envio ao socket
- **Timestamp:** `time.monotonic_ns()` no início e fim

#### **t_ack** = enviado → resposta/ack recebida
- **O que mede:** Tempo de rede + processamento servidor
- **Onde:** Entre envio ao socket e recebimento da resposta
- **Timestamp:** `time.monotonic_ns()` no envio e recebimento

### 0.2 Instrumentação Leve

**Implementação:**
```python
import time
from collections import deque
from typing import Dict, List

class LatencyMetrics:
    def __init__(self, buffer_size=1000):
        self.buffer_size = buffer_size
        self.t_decision: Dict[str, deque] = {}  # market -> deque
        self.t_send: Dict[str, deque] = {}
        self.t_ack: Dict[str, deque] = {}
        self._lock = threading.Lock()
    
    def record_decision(self, market: str, duration_ns: int):
        """Registra t_decision para um mercado."""
        with self._lock:
            if market not in self.t_decision:
                self.t_decision[market] = deque(maxlen=self.buffer_size)
            self.t_decision[market].append(duration_ns)
    
    def record_send(self, market: str, duration_ns: int):
        """Registra t_send para um mercado."""
        with self._lock:
            if market not in self.t_send:
                self.t_send[market] = deque(maxlen=self.buffer_size)
            self.t_send[market].append(duration_ns)
    
    def record_ack(self, market: str, duration_ns: int):
        """Registra t_ack para um mercado."""
        with self._lock:
            if market not in self.t_ack:
                self.t_ack[market] = deque(maxlen=self.buffer_size)
            self.t_ack[market].append(duration_ns)
    
    def get_percentiles(self, values: deque, percentiles=[50, 90, 99]):
        """Calcula percentis de uma série de valores."""
        if not values:
            return {}
        sorted_vals = sorted(values)
        result = {}
        for p in percentiles:
            idx = int(len(sorted_vals) * p / 100)
            result[f'p{p}'] = sorted_vals[idx] / 1_000_000  # ns -> ms
        return result
    
    def report(self, interval_s=5):
        """Gera relatório de métricas a cada N segundos."""
        # Coletar por 5-10 minutos
        # Comparar p50/p90/p99 para cada métrica (por market e total)
        pass
```

**Saída Esperada:**
- p50/p90/p99 para cada métrica (por market e total)
- Identificação de gargalos (qual métrica tem maior p99)

### 0.3 Coleta e Análise

**Duração:** 5-10 minutos de coleta  
**Frequência:** A cada evento de trading  
**Output:** Relatório com percentis por métrica

**Arquivos a Criar:**
- `poly_data/latency_metrics.py` - Classe de métricas
- `instrumentar_latencia.py` - Script de instrumentação
- `analisar_metricas.py` - Script de análise

---

## 🔥 FASE 4 — "Hot Path" sem Bloqueio + Pipeline de Ordens

**Objetivo:** Tirar "head-of-line blocking" do loop e acelerar "time-to-send".  
**Ganhos Esperados:** Queda relevante em p50 e principalmente p99 (menos travadas quando API demora).

### 4.1 Arquitetura: Strategy → Queue → Sender Task

**Princípio:** Loop da estratégia NUNCA espera resposta HTTP.

```
┌─────────────┐      ┌──────────┐      ┌─────────────┐
│  Strategy   │─────▶│  Queue   │─────▶│ Sender Task │
│   Loop      │      │ (async)  │      │  (async)    │
└─────────────┘      └──────────┘      └─────────────┘
     │                    │                    │
     │                    │                    │
     │                    │                    ▼
     │                    │              ┌──────────┐
     │                    │              │  HTTP    │
     │                    │              │  API     │
     │                    │              └──────────┘
     │                    │                    │
     │                    │                    │
     └────────────────────┴────────────────────┘
              (não bloqueia)
```

**Implementação:**

```python
import asyncio
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class OrderIntent:
    """Intenção de ordem (não bloqueia estratégia)."""
    market: str
    side: str  # 'BUY' or 'SELL'
    price: float
    size: float
    priority: int  # 0=normal, 1=high, 2=critical
    timestamp: float

class SenderTask:
    """Task assíncrona que envia ordens em pipeline."""
    
    def __init__(self, client, max_inflight_per_market=2, flush_window_ms=20):
        self.client = client
        self.queue = asyncio.Queue()
        self.max_inflight_per_market = max_inflight_per_market
        self.flush_window_ms = flush_window_ms
        self.in_flight: Dict[str, int] = {}  # market -> count
        self.pending_intents: Dict[str, List[OrderIntent]] = {}  # market -> list
    
    async def run(self):
        """Loop principal do sender (nunca bloqueia estratégia)."""
        while True:
            try:
                # Coletar intents do queue (com timeout para flush window)
                intents = []
                deadline = time.monotonic() + (self.flush_window_ms / 1000)
                
                while time.monotonic() < deadline:
                    try:
                        intent = await asyncio.wait_for(
                            self.queue.get(), 
                            timeout=(deadline - time.monotonic())
                        )
                        intents.append(intent)
                    except asyncio.TimeoutError:
                        break
                
                # Processar intents coletados
                await self._process_intents(intents)
                
            except Exception as e:
                logger.error(f"Error in SenderTask: {e}")
                await asyncio.sleep(0.1)
    
    async def _process_intents(self, intents: List[OrderIntent]):
        """Processa intents respeitando in-flight limits."""
        # Agrupar por market
        by_market = {}
        for intent in intents:
            if intent.market not in by_market:
                by_market[intent.market] = []
            by_market[intent.market].append(intent)
        
        # Enviar respeitando in-flight limits
        tasks = []
        for market, market_intents in by_market.items():
            # Verificar in-flight
            in_flight_count = self.in_flight.get(market, 0)
            if in_flight_count >= self.max_inflight_per_market:
                # Segurar intents ou só mandar cancel crítico
                if any(i.priority >= 2 for i in market_intents):
                    # Permitir cancel crítico
                    critical = [i for i in market_intents if i.priority >= 2]
                    tasks.extend([self._send_intent(c) for c in critical])
                else:
                    # Re-queue intents normais
                    for intent in market_intents:
                        await self.queue.put(intent)
            else:
                # Enviar todos
                tasks.extend([self._send_intent(i) for i in market_intents])
        
        # Executar em paralelo
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_intent(self, intent: OrderIntent):
        """Envia uma intent (não bloqueia)."""
        market = intent.market
        self.in_flight[market] = self.in_flight.get(market, 0) + 1
        
        try:
            # Medir t_send
            t_send_start = time.monotonic_ns()
            
            # Preparar e enviar
            result = await asyncio.to_thread(
                self.client.create_order,
                intent.market,
                intent.side,
                intent.price,
                intent.size
            )
            
            t_send_end = time.monotonic_ns()
            metrics.record_send(market, t_send_end - t_send_start)
            
            return result
        finally:
            self.in_flight[market] = max(0, self.in_flight[market] - 1)
```

**Modificação no Loop Principal:**
```python
# ANTES (bloqueante):
result = client.create_order(...)  # Bloqueia até resposta

# DEPOIS (não bloqueante):
intent = OrderIntent(market=..., side=..., price=..., size=...)
await sender_task.queue.put(intent)  # Não bloqueia
```

### 4.2 "In-flight Control" por Mercado

**Configuração:**
```python
MAX_INFLIGHT_PER_MARKET = 2  # Máximo de requisições em voo por mercado
```

**Lógica:**
- Se já tem 2 em voo → segurar intents ou só mandar cancel crítico
- Evita sobrecarga da API e reduz timeouts

### 4.3 Batch Lógico (mesmo sem batch real)

**Flush Window:**
```python
SENDER_FLUSH_WINDOW_MS = 20  # Agrupar intents por 20ms
```

**Benefício:**
- Reduz overhead por loop
- Agrupa múltiplas intents do mesmo mercado
- Reduz número de requisições HTTP

### Entrega da Fase 4

**Arquivos a Criar/Modificar:**
- `poly_data/sender_task.py` - SenderTask com fila
- `poly_data/order_intent.py` - OrderIntent dataclass
- `main.py` - Modificar loop principal (não espera resposta)

**Checklist:**
- [ ] SenderTask implementado
- [ ] Queue assíncrona funcionando
- [ ] In-flight control por mercado
- [ ] Flush window implementado
- [ ] Loop principal não bloqueia
- [ ] Testes realizados

---

## 📡 FASE 5 — WS-first no Caminho Crítico

**Objetivo:** Remover HTTP do caminho crítico de decisão.  
**Ganhos Esperados:** Cortar esperas e reduzir jitter (principalmente se ainda existia fetch/poll).

### 5.1 Book 100% via WebSocket

**Estratégia:**
1. **Snapshot inicial (1x):** Via HTTP na inicialização
2. **Depois só deltas:** Via WebSocket em tempo real
3. **Manter estado local:** Book state em memória

**Implementação:**
```python
class BookState:
    """Estado local do order book (atualizado via WebSocket)."""
    
    def __init__(self, market: str):
        self.market = market
        self.bids: List[Tuple[float, float]] = []  # (price, size)
        self.asks: List[Tuple[float, float]] = []
        self.last_update_ns: int = 0
        self._lock = asyncio.Lock()
    
    async def apply_delta(self, delta: dict):
        """Aplica delta do WebSocket ao book."""
        async with self._lock:
            # Processar delta (add/update/remove)
            # Atualizar bids/asks
            self.last_update_ns = time.monotonic_ns()
    
    def get_best_bid(self) -> float:
        """Retorna best bid (sem lock, snapshot imutável)."""
        return self.bids[0][0] if self.bids else 0.0
    
    def get_best_ask(self) -> float:
        """Retorna best ask (sem lock, snapshot imutável)."""
        return self.asks[0][0] if self.asks else 0.0
```

### 5.2 Reconcile Fora do Hot Path

**Estratégia:**
- **reconcile_task** a cada 10-30s (ou em erro)
- **Nunca "poll" book** no loop de estratégia

**Implementação:**
```python
async def reconcile_task(book_states: Dict[str, BookState], client):
    """Task de reconciliação (fora do hot path)."""
    while True:
        await asyncio.sleep(RECONCILE_INTERVAL_S)  # 15s
        
        for market, book_state in book_states.items():
            try:
                # Buscar snapshot via HTTP (fora do hot path)
                snapshot = await asyncio.to_thread(
                    client.get_order_book, market
                )
                
                # Reconciliar com estado local
                await book_state.reconcile(snapshot)
            except Exception as e:
                logger.error(f"Reconcile error for {market}: {e}")
```

### Entrega da Fase 5

**Arquivos a Criar/Modificar:**
- `poly_data/book_state.py` - Estado local do book
- `poly_data/ws_book_handler.py` - Handler de deltas WebSocket
- `poly_data/reconcile_task.py` - Task de reconciliação
- `poly_data/websocket_handlers.py` - Integrar book updates

**Checklist:**
- [ ] Book state local implementado
- [ ] WebSocket atualiza book em tempo real
- [ ] Reconcile task fora do hot path
- [ ] Zero HTTP no loop de estratégia
- [ ] Testes realizados

---

## ⚡ FASE 6 — Redução de Overhead Python

**Objetivo:** Reduzir CPU/alloc e estabilizar p99.  
**Ganhos Esperados:** Pequenos no p50, bons no p99 (menos GC/alloc).

### 6.1 Fixed-point (inteiros) para Preço/Tamanho

**Conversão:**
- Preço 0–1 → int em "mils" (0.534 → 534) ou "bps" (0.534 → 53400)
- Size shares → sempre int

**Implementação:**
```python
PRICE_SCALE = 1000  # mils (0.001 = 1 mil)

class FixedPointPrice:
    """Preço em fixed-point (int)."""
    
    @staticmethod
    def to_int(price: float) -> int:
        """Converte float para int (mils)."""
        return int(price * PRICE_SCALE)
    
    @staticmethod
    def to_float(price_int: int) -> float:
        """Converte int para float."""
        return price_int / PRICE_SCALE

# No hot path:
price_int = FixedPointPrice.to_int(0.534)  # 534
# Operações com int (mais rápido)
# Converter para float só na borda (se API exigir)
```

**Trocar:**
- `float/Decimal` no hot path → `int ticks`
- Converter para float só na borda (se API exigir)

### 6.2 Prealloc e Reuse de Estruturas

**__slots__ em MarketState/OrderIntent:**
```python
@dataclass
class OrderIntent:
    __slots__ = ['market', 'side', 'price_int', 'size_int', 'priority', 'timestamp']
    market: str
    side: str
    price_int: int  # Fixed-point
    size_int: int
    priority: int
    timestamp: int
```

**Templates de Payload:**
```python
class PayloadTemplate:
    """Template de payload pré-definido (só trocar price/size)."""
    
    def __init__(self, market: str, side: str):
        self.template = {
            'token_id': market,
            'side': side,
            'price': 0,  # Será substituído
            'size': 0    # Será substituído
        }
    
    def build(self, price_int: int, size_int: int) -> dict:
        """Constrói payload (reutiliza template)."""
        payload = self.template.copy()
        payload['price'] = FixedPointPrice.to_float(price_int)
        payload['size'] = size_int
        return payload
```

### 6.3 JSON Mais Rápido "de Verdade"

**orjson.dumps retorna bytes:**
```python
import orjson

# ANTES:
payload_dict = {...}
json_str = json.dumps(payload_dict)  # String
request_body = json_str.encode()     # Bytes

# DEPOIS:
payload_dict = {...}
request_body = orjson.dumps(payload_dict)  # Bytes direto
```

**Headers Estáticos Cacheados:**
```python
# Cachear headers (não recriar a cada request)
_STATIC_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    # ... outros headers fixos
}
```

### Entrega da Fase 6

**Arquivos a Criar/Modificar:**
- `poly_data/fixed_point.py` - Conversão fixed-point
- `poly_data/payload_template.py` - Templates de payload
- `poly_data/polymarket_client.py` - Usar fixed-point e orjson bytes
- Refatorar OrderIntent para usar ints

**Checklist:**
- [ ] Fixed-point implementado
- [ ] __slots__ em estruturas críticas
- [ ] Payload templates
- [ ] orjson bytes direto
- [ ] Headers cacheados
- [ ] Testes realizados

---

## 🔄 FASE 7 — Event Loop + Sockets

**Objetivo:** Reduzir overhead de asyncio e sockets.  
**Ganhos Esperados:** Redução em p99 (menos overhead de event loop).

### 7.1 uvloop (Linux)

**Implementação:**
```python
import sys
import platform

if platform.system() == 'Linux':
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        logger.info("✓ uvloop enabled (Linux)")
    except ImportError:
        logger.warning("uvloop not available, using default event loop")
```

**Medir Impacto:** Comparar p99 antes/depois

### 7.2 Menos Locks / Single-Writer Book

**Arquitetura:**
- Uma task "writer" atualiza book
- Estratégia lê snapshot imutável por tick
- Evitar locks frequentes

**Implementação:**
```python
class ImmutableBookSnapshot:
    """Snapshot imutável do book (sem locks)."""
    
    def __init__(self, bids: List[Tuple[float, float]], asks: List[Tuple[float, float]]):
        self.bids = tuple(bids)  # Imutável
        self.asks = tuple(asks)   # Imutável
        self.timestamp_ns = time.monotonic_ns()

class BookWriter:
    """Task única que escreve no book (com lock)."""
    
    async def update(self, delta: dict):
        """Atualiza book (com lock)."""
        async with self._lock:
            # Aplicar delta
            # Criar novo snapshot imutável
            self.current_snapshot = ImmutableBookSnapshot(...)

# Estratégia lê snapshot (sem lock):
snapshot = book_writer.current_snapshot  # Sem lock, imutável
best_bid = snapshot.bids[0][0]
```

### Entrega da Fase 7

**Arquivos a Criar/Modificar:**
- `main.py` - Habilitar uvloop
- `poly_data/book_state.py` - Single-writer + snapshots imutáveis

**Checklist:**
- [ ] uvloop habilitado (Linux)
- [ ] Single-writer book
- [ ] Snapshots imutáveis
- [ ] Testes realizados

---

## 🦀 FASE 8 — "CPython/Rust Hot Path" (Opcional)

**Objetivo:** Se depois das fases acima ainda existir CPU significativo.  
**Nota:** Isso não reduz rede/servidor — melhora o "tempo local" e o jitter.

### 8.1 Alvos que Valem Mover para C/Rust

**Candidatos:**
1. **update do orderbook** (apply deltas + best bid/ask)
2. **compute_quotes + simulação pair_cost**
3. **payload builder** (bytes)

**Implementação (Rust via PyO3):**
```rust
// book_updater.rs
use pyo3::prelude::*;

#[pyfunction]
fn apply_delta(bids: Vec<(f64, f64)>, asks: Vec<(f64, f64)>, delta: PyDict) -> PyResult<(Vec<(f64, f64)>, Vec<(f64, f64)>)> {
    // Aplicar delta e retornar novo book
    // Muito mais rápido que Python
}
```

**Python Binding:**
```python
import book_updater_rust

# No hot path:
new_bids, new_asks = book_updater_rust.apply_delta(bids, asks, delta)
```

### Entrega da Fase 8

**Arquivos a Criar:**
- `poly_data/rust_ext/` - Módulo Rust
- `setup.py` - Build do módulo
- Bindings Python

**Checklist:**
- [ ] Identificar gargalos de CPU (após Fase 7)
- [ ] Implementar em Rust/Cython
- [ ] Benchmarks comparativos
- [ ] Integração com código Python

---

## ⚙️ CHECKLIST DE CONFIGURAÇÃO

### Valores Iniciais

```python
# Fase 4
MAX_INFLIGHT_PER_MARKET = 2
SENDER_FLUSH_WINDOW_MS = 20

# Fase 5
RECONCILE_INTERVAL_S = 15
BOOK_SNAPSHOT_TTL_S = 0  # Snapshot só na conexão

# Fase 6
USE_FIXED_POINT = True
PRICE_SCALE = 1000  # mils

# Fase 7
ENABLE_UVLOOP = True  # Linux

# Fase 0
METRICS_INTERVAL_S = 5
```

---

## 📊 CRITÉRIOS DE SUCESSO

### O que tem que melhorar:

1. **t_send p99 cai bastante**
   - Pipeline + prealloc
   - Menos bloqueios

2. **t_decision p99 cai**
   - Fixed-point + menos alloc
   - Menos GC pauses

3. **t_ack pode não cair muito** (rede/servidor)
   - Mas o bot fica mais responsivo e consistente
   - Menos jitter

### Métricas Esperadas:

| Métrica | Baseline | Meta Fase 4-8 |
|---------|----------|---------------|
| **t_decision p50** | ? | < 5ms |
| **t_decision p99** | ? | < 20ms |
| **t_send p50** | ? | < 10ms |
| **t_send p99** | ? | < 50ms |
| **t_ack p50** | ~176ms | ~176ms (rede) |
| **t_ack p99** | ? | < 300ms (menos jitter) |

---

## 📋 TAREFAS PARA IMPLEMENTAÇÃO

### Fase 0 (Obrigatória)
- [ ] Add latency spans: decision/send/ack
- [ ] p50/p99 report
- [ ] Instrumentação leve (buffer, flush periódico)
- [ ] Coleta por 5-10 min

### Fase 4
- [ ] Implement SenderTask com queue + inflight per market
- [ ] Modificar loop principal (não bloqueia)
- [ ] Flush window implementado
- [ ] Testes realizados

### Fase 5
- [ ] Remove any read-HTTP from hot path (WS-first)
- [ ] Book state local (WebSocket only)
- [ ] Reconcile task fora do hot path
- [ ] Testes realizados

### Fase 6
- [ ] Fixed-point refactor (price/size ints no core)
- [ ] Payload templates + orjson bytes
- [ ] __slots__ em estruturas críticas
- [ ] Testes realizados

### Fase 7
- [ ] Enable uvloop (se Linux)
- [ ] Single-writer book + snapshots imutáveis
- [ ] Menos locks
- [ ] Testes realizados

### Fase 8 (Opcional)
- [ ] Identificar gargalos de CPU
- [ ] Rust/Cython module para book + compute_quotes
- [ ] Benchmarks comparativos
- [ ] Integração

---

## 🎯 ORDEM DE IMPLEMENTAÇÃO RECOMENDADA

1. **Fase 0** (obrigatória) - Medir antes de mexer
2. **Fase 4** - Maior ROI (pipeline + não bloqueia)
3. **Fase 5** - Remove HTTP do hot path
4. **Fase 6** - Reduz overhead Python
5. **Fase 7** - Otimiza event loop
6. **Fase 8** - Opcional (só se necessário)

---

## 📈 EXPECTATIVAS REALISTAS

### Após Fase 4-7:
- **p50:** ~320-380ms (vs 440ms atual)
- **p99:** Redução significativa (menos jitter)
- **Jitter:** Muito menor (pipeline + não bloqueia)

### Limites:
- **Rede:** ~110ms (não redutível via código)
- **Servidor:** ~40ms (não controlável)
- **Tempo local:** Pode ser reduzido para < 50ms

---

**Última atualização:** 2026-02-01  
**Próximo passo:** Implementar Fase 0 (medição obrigatória)

