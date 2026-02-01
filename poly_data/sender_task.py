"""
FASE 4: SenderTask - Task assíncrona que envia ordens em pipeline
Loop da estratégia NUNCA espera resposta HTTP
"""
import asyncio
import time
import logging
from typing import Dict, List, Optional
from collections import defaultdict

from poly_data.order_intent import OrderIntent
from poly_data.latency_metrics import metrics

logger = logging.getLogger(__name__)

class SenderTask:
    """Task assíncrona que envia ordens em pipeline (não bloqueia estratégia)."""
    
    def __init__(self, client, max_inflight_per_market=2, flush_window_ms=20):
        self.client = client
        self.queue = asyncio.Queue()
        self.max_inflight_per_market = max_inflight_per_market
        self.flush_window_ms = flush_window_ms
        self.in_flight: Dict[str, int] = defaultdict(int)  # market -> count
        self.running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Inicia a task de envio."""
        if self.running:
            return
        self.running = True
        self._task = asyncio.create_task(self._run())
        logger.info("✅ SenderTask started (Fase 4)")
    
    async def stop(self):
        """Para a task de envio."""
        self.running = False
        if self._task:
            await self._task
        logger.info("✅ SenderTask stopped")
    
    async def submit(self, intent: OrderIntent):
        """Submete uma intent para envio (não bloqueia)."""
        await self.queue.put(intent)
    
    async def _run(self):
        """Loop principal do sender (nunca bloqueia estratégia)."""
        logger.info(f"🚀 SenderTask running (flush_window={self.flush_window_ms}ms, max_inflight={self.max_inflight_per_market})")
        
        while self.running:
            try:
                # Coletar intents do queue (com timeout para flush window)
                intents = []
                deadline = time.monotonic() + (self.flush_window_ms / 1000)
                
                # Primeira intent (sem timeout)
                try:
                    intent = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=1.0  # Timeout máximo de 1s
                    )
                    intents.append(intent)
                except asyncio.TimeoutError:
                    continue
                
                # Coletar mais intents até deadline
                while time.monotonic() < deadline:
                    try:
                        intent = await asyncio.wait_for(
                            self.queue.get(),
                            timeout=max(0.001, deadline - time.monotonic())
                        )
                        intents.append(intent)
                    except asyncio.TimeoutError:
                        break
                
                # Processar intents coletados
                if intents:
                    await self._process_intents(intents)
                
            except Exception as e:
                logger.error(f"❌ Error in SenderTask: {e}", exc_info=True)
                await asyncio.sleep(0.1)
    
    async def _process_intents(self, intents: List[OrderIntent]):
        """Processa intents respeitando in-flight limits."""
        # Agrupar por market
        by_market = defaultdict(list)
        for intent in intents:
            by_market[intent.market].append(intent)
        
        # Enviar respeitando in-flight limits
        tasks = []
        for market, market_intents in by_market.items():
            # Verificar in-flight
            in_flight_count = self.in_flight[market]
            
            if in_flight_count >= self.max_inflight_per_market:
                # Segurar intents ou só mandar cancel crítico
                critical_intents = [i for i in market_intents if i.priority >= 2]
                normal_intents = [i for i in market_intents if i.priority < 2]
                
                # Permitir cancel crítico
                if critical_intents:
                    tasks.extend([self._send_intent(c) for c in critical_intents])
                
                # Re-queue intents normais
                for intent in normal_intents:
                    await self.queue.put(intent)
            else:
                # Enviar todos (dentro do limite)
                tasks.extend([self._send_intent(i) for i in market_intents])
        
        # Executar em paralelo (não bloqueia)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_intent(self, intent: OrderIntent):
        """Envia uma intent (não bloqueia estratégia)."""
        market = intent.market
        self.in_flight[market] += 1
        
        try:
            # Medir t_send (intent gerado → request enviado)
            t_send_start = time.monotonic_ns()
            
            # Preparar e enviar (em thread para não bloquear event loop)
            result = await asyncio.to_thread(
                self.client.create_order,
                intent.market,
                intent.side,
                intent.price,
                intent.size
            )
            
            t_send_end = time.monotonic_ns()
            metrics.record_send(market, t_send_end - t_send_start)
            
            # Medir t_ack (enviado → resposta recebida)
            if result:
                t_ack_start = t_send_end
                t_ack_end = time.monotonic_ns()
                metrics.record_ack(market, t_ack_end - t_ack_start)
                
                # Preencher order_id se disponível
                if 'orderID' in result:
                    intent.order_id = result['orderID']
            
            return result
        except Exception as e:
            logger.error(f"❌ Error sending intent for {market}: {e}")
            return None
        finally:
            self.in_flight[market] = max(0, self.in_flight[market] - 1)
    
    def get_in_flight_count(self, market: str) -> int:
        """Retorna número de requisições em voo para um mercado."""
        return self.in_flight.get(market, 0)
    
    def get_queue_size(self) -> int:
        """Retorna tamanho da fila."""
        return self.queue.qsize()

