#!/usr/bin/env python3
"""
Script para comparar latência BASELINE vs FASE 4
Mede t_decision, t_send, t_ack antes e depois da implementação
"""
import os
import sys
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from poly_data.polymarket_client import PolymarketClient
from poly_data.utils import get_sheet_df
from poly_data.latency_metrics import metrics
from poly_data.order_intent import OrderIntent
from poly_data.sender_task import SenderTask

load_dotenv()

def print_section(title):
    """Imprime seção formatada."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

async def teste_baseline(client, token_up, token_down, lado_up, lado_down, preco_up, preco_down, tamanho):
    """Teste BASELINE (bloqueante) - Fase 1-3."""
    print_section("📊 TESTE BASELINE (Bloqueante)")
    
    # Resetar métricas
    metrics.reset()
    
    inicio_total = time.time()
    
    # Medir t_decision (simulado - em produção seria book_update → intents)
    t_decision_start = time.monotonic_ns()
    # Simular decisão de estratégia
    await asyncio.sleep(0.001)  # 1ms de processamento
    t_decision_end = time.monotonic_ns()
    metrics.record_decision("test_market", t_decision_end - t_decision_start)
    
    # Enviar ordens (bloqueante)
    print("   📤 Enviando ordens (BLOQUEANTE)...")
    
    def enviar_ordem_bloqueante(token, lado, preco, tamanho, tipo):
        """Envia ordem de forma bloqueante."""
        t_send_start = time.monotonic_ns()
        result = client.create_order(token, lado, preco, tamanho, neg_risk=False)
        t_send_end = time.monotonic_ns()
        
        if result:
            t_ack_start = t_send_end
            t_ack_end = time.monotonic_ns()
            metrics.record_send("test_market", t_send_end - t_send_start)
            metrics.record_ack("test_market", t_ack_end - t_ack_start)
            return {'success': True, 'order_id': result.get('orderID'), 'tipo': tipo}
        return {'success': False, 'tipo': tipo}
    
    # Enviar em paralelo (Fase 1)
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_up = executor.submit(enviar_ordem_bloqueante, token_up, lado_up, preco_up, tamanho, 'BUY UP')
        future_down = executor.submit(enviar_ordem_bloqueante, token_down, lado_down, preco_down, tamanho, 'BUY DOWN')
        
        resultado_up = future_up.result()
        resultado_down = future_down.result()
    
    tempo_total = time.time() - inicio_total
    
    print(f"   ⚡ Tempo total (baseline): {tempo_total*1000:.2f}ms")
    
    return {
        'tempo_total': tempo_total,
        'resultado_up': resultado_up,
        'resultado_down': resultado_down
    }

async def teste_fase4(client, token_up, token_down, lado_up, lado_down, preco_up, preco_down, tamanho):
    """Teste FASE 4 (pipeline assíncrono)."""
    print_section("🚀 TESTE FASE 4 (Pipeline Assíncrono)")
    
    # Resetar métricas
    metrics.reset()
    
    # Inicializar SenderTask
    sender_task = SenderTask(
        client,
        max_inflight_per_market=2,
        flush_window_ms=20
    )
    await sender_task.start()
    
    try:
        inicio_total = time.time()
        
        # Medir t_decision (simulado)
        t_decision_start = time.monotonic_ns()
        # Simular decisão de estratégia
        await asyncio.sleep(0.001)  # 1ms de processamento
        t_decision_end = time.monotonic_ns()
        metrics.record_decision("test_market", t_decision_end - t_decision_start)
        
        # Criar intents (não bloqueia)
        print("   📤 Criando intents (NÃO BLOQUEANTE)...")
        
        intent_up = OrderIntent(
            market=token_up,
            side=lado_up,
            price=preco_up,
            size=tamanho,
            priority=0
        )
        
        intent_down = OrderIntent(
            market=token_down,
            side=lado_down,
            price=preco_down,
            size=tamanho,
            priority=0
        )
        
        # Submeter intents (não bloqueia)
        await sender_task.submit(intent_up)
        await sender_task.submit(intent_down)
        
        tempo_submissao = time.time() - inicio_total
        print(f"   ⚡ Tempo até submissão (Fase 4): {tempo_submissao*1000:.2f}ms")
        print(f"   📊 Queue size: {sender_task.get_queue_size()}")
        
        # Aguardar conclusão das ordens (com timeout)
        print("   ⏳ Aguardando conclusão das ordens...")
        inicio_espera = time.time()
        max_wait = 5.0  # 5 segundos máximo
        
        while (time.time() - inicio_espera) < max_wait:
            await asyncio.sleep(0.1)
            if sender_task.get_queue_size() == 0 and \
               sender_task.get_in_flight_count(token_up) == 0 and \
               sender_task.get_in_flight_count(token_down) == 0:
                break
        
        tempo_total = time.time() - inicio_total
        
        print(f"   ⚡ Tempo total (Fase 4): {tempo_total*1000:.2f}ms")
        print(f"   📊 In-flight UP: {sender_task.get_in_flight_count(token_up)}")
        print(f"   📊 In-flight DOWN: {sender_task.get_in_flight_count(token_down)}")
        
        return {
            'tempo_total': tempo_total,
            'intent_up': intent_up,
            'intent_down': intent_down
        }
    finally:
        await sender_task.stop()

async def main():
    """Função principal de teste."""
    print_section("🧪 COMPARAÇÃO BASELINE vs FASE 4")
    print(f"⏰ Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Inicializar cliente
    print("1️⃣  Inicializando cliente Polymarket...")
    try:
        client = PolymarketClient()
        print("   ✅ Cliente inicializado com sucesso")
    except Exception as e:
        print(f"   ❌ Erro ao inicializar cliente: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Buscar mercados
    print("\n2️⃣  Buscando mercados disponíveis...")
    try:
        df_selected, params = get_sheet_df()
        
        if df_selected.empty:
            print("   ❌ Nenhum mercado selecionado na planilha!")
            return
        
        mercado = df_selected.iloc[0]
        token1 = str(mercado.get('token1', ''))
        token2 = str(mercado.get('token2', ''))
        
        if not token1 or token1 == 'nan' or token1 == '':
            print("   ❌ Token1 não encontrado!")
            return
        
        print(f"   ✅ Mercado selecionado")
        print(f"   ✅ Token1: {token1[:30]}...")
        print(f"   ✅ Token2: {token2[:30]}...")
        
    except Exception as e:
        print(f"   ❌ Erro ao buscar mercados: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Verificar saldo
    print("\n3️⃣  Verificando saldo...")
    try:
        saldo = client.get_usdc_balance()
        print(f"   ✅ Saldo USDC: ${saldo:.2f}")
        
        if saldo < 0.10:
            print("   ⚠️  Saldo insuficiente para teste")
            return
        
        # Tamanho mínimo
        tamanho = 5.0
        preco_up = 0.01
        preco_down = 0.01
        lado_up = 'BUY'
        lado_down = 'BUY'
        
        token_up = token1
        token_down = token2
        
    except Exception as e:
        print(f"   ❌ Erro ao verificar saldo: {e}")
        return
    
    # Executar testes
    print("\n" + "=" * 80)
    print("  EXECUTANDO TESTES")
    print("=" * 80)
    
    # Teste 1: BASELINE
    print("\n📊 Executando teste BASELINE...")
    resultado_baseline = await teste_baseline(
        client, token_up, token_down, lado_up, lado_down, 
        preco_up, preco_down, tamanho
    )
    
    # Relatório baseline
    print_section("📊 RELATÓRIO BASELINE")
    print(metrics.report())
    
    # Aguardar um pouco entre testes
    await asyncio.sleep(2)
    
    # Teste 2: FASE 4
    print("\n🚀 Executando teste FASE 4...")
    resultado_fase4 = await teste_fase4(
        client, token_up, token_down, lado_up, lado_down,
        preco_up, preco_down, tamanho
    )
    
    # Relatório Fase 4
    print_section("🚀 RELATÓRIO FASE 4")
    print(metrics.report())
    
    # Comparação final
    print_section("📈 COMPARAÇÃO FINAL")
    
    tempo_baseline = resultado_baseline['tempo_total'] * 1000
    tempo_fase4 = resultado_fase4['tempo_total'] * 1000
    
    print(f"\n⏱️  TEMPO TOTAL:")
    print(f"   Baseline: {tempo_baseline:.2f}ms")
    print(f"   Fase 4:   {tempo_fase4:.2f}ms")
    print(f"   Diferença: {tempo_fase4 - tempo_baseline:.2f}ms")
    
    if tempo_fase4 < tempo_baseline:
        melhoria = ((tempo_baseline - tempo_fase4) / tempo_baseline) * 100
        print(f"   ✅ Melhoria: {melhoria:.1f}% mais rápido")
    else:
        piora = ((tempo_fase4 - tempo_baseline) / tempo_baseline) * 100
        print(f"   ⚠️  Piora: {piora:.1f}% mais lento")
    
    # Métricas detalhadas
    baseline_metrics = metrics.get_all_metrics()
    print(f"\n📊 MÉTRICAS DETALHADAS:")
    print(f"   t_send p50: {baseline_metrics.get('t_send', {}).get('p50', 'N/A')}ms")
    print(f"   t_send p99: {baseline_metrics.get('t_send', {}).get('p99', 'N/A')}ms")
    print(f"   t_ack p50: {baseline_metrics.get('t_ack', {}).get('p50', 'N/A')}ms")
    print(f"   t_ack p99: {baseline_metrics.get('t_ack', {}).get('p99', 'N/A')}ms")
    
    print("\n✅ Testes concluídos!")

if __name__ == "__main__":
    asyncio.run(main())

