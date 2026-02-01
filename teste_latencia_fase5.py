#!/usr/bin/env python3
"""
Script para medir latência da Fase 5 - WS-first
Compara: HTTP get_order_book vs BookState.get_snapshot()
"""
import os
import sys
import time
import asyncio
import statistics
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from poly_data.polymarket_client import PolymarketClient
from poly_data.utils import get_sheet_df
from poly_data.book_state import book_state_manager

load_dotenv()

async def teste_latencia_fase5():
    """Testa latência de leitura do book: HTTP vs BookState."""
    print("=" * 80)
    print("  📊 TESTE DE LATÊNCIA - FASE 5 (WS-first)")
    print("=" * 80)
    
    # Inicializar cliente
    print("\n1️⃣  Inicializando cliente...")
    client = PolymarketClient()
    print("   ✅ Cliente inicializado")
    
    # Buscar mercado
    print("\n2️⃣  Buscando mercado...")
    df_selected, _ = get_sheet_df()
    if df_selected.empty:
        print("   ❌ Nenhum mercado encontrado")
        return
    
    mercado = df_selected.iloc[0]
    token1 = str(mercado.get('token1', ''))
    print(f"   ✅ Token: {token1[:30]}...")
    
    # Inicializar BookState
    print("\n3️⃣  Inicializando BookState...")
    order_book_result = client.get_order_book(token1)
    if order_book_result and len(order_book_result) == 2:
        bids_df, asks_df = order_book_result
        bids = [(float(row['price']), float(row['size'])) for _, row in bids_df.iterrows()]
        asks = [(float(row['price']), float(row['size'])) for _, row in asks_df.iterrows()]
        
        book_state = book_state_manager.get_book(token1)
        book_state.initialize_from_snapshot(bids, asks)
        print("   ✅ BookState inicializado")
    
    # Teste 1: Latência de leitura HTTP (baseline)
    print("\n4️⃣  Testando latência de leitura HTTP (baseline)...")
    latencias_http = []
    num_testes = 20
    
    for i in range(num_testes):
        inicio = time.monotonic_ns()
        try:
            order_book_result = client.get_order_book(token1)
            if order_book_result:
                best_bid = float(order_book_result[0].iloc[0]['price']) if not order_book_result[0].empty else 0.0
        except:
            best_bid = 0.0
        fim = time.monotonic_ns()
        latencia_ns = fim - inicio
        latencias_http.append(latencia_ns / 1_000_000)  # ns -> ms
        if (i + 1) % 5 == 0:
            print(f"   ⏱️  {i+1}/{num_testes} testes...")
    
    # Teste 2: Latência de leitura BookState (Fase 5)
    print("\n5️⃣  Testando latência de leitura BookState (Fase 5)...")
    latencias_bookstate = []
    
    for i in range(num_testes):
        inicio = time.monotonic_ns()
        snapshot = book_state.get_snapshot()
        if snapshot:
            best_bid = snapshot.get_best_bid()
        fim = time.monotonic_ns()
        latencia_ns = fim - inicio
        latencias_bookstate.append(latencia_ns / 1_000_000)  # ns -> ms
        if (i + 1) % 5 == 0:
            print(f"   ⏱️  {i+1}/{num_testes} testes...")
    
    # Análise estatística
    print("\n" + "=" * 80)
    print("  📊 RESULTADOS")
    print("=" * 80)
    
    # HTTP
    print("\n📡 HTTP get_order_book() (Baseline):")
    print(f"   Média: {statistics.mean(latencias_http):.2f}ms")
    print(f"   Mediana (p50): {statistics.median(latencias_http):.2f}ms")
    print(f"   Min: {min(latencias_http):.2f}ms")
    print(f"   Max: {max(latencias_http):.2f}ms")
    print(f"   Desvio padrão: {statistics.stdev(latencias_http):.2f}ms")
    
    # Calcular p90 e p99
    sorted_http = sorted(latencias_http)
    p90_http = sorted_http[int(len(sorted_http) * 0.90)]
    p99_http = sorted_http[int(len(sorted_http) * 0.99)]
    print(f"   p90: {p90_http:.2f}ms")
    print(f"   p99: {p99_http:.2f}ms")
    
    # BookState
    print("\n📡 BookState.get_snapshot() (Fase 5):")
    print(f"   Média: {statistics.mean(latencias_bookstate):.2f}ms")
    print(f"   Mediana (p50): {statistics.median(latencias_bookstate):.2f}ms")
    print(f"   Min: {min(latencias_bookstate):.2f}ms")
    print(f"   Max: {max(latencias_bookstate):.2f}ms")
    print(f"   Desvio padrão: {statistics.stdev(latencias_bookstate):.2f}ms")
    
    sorted_bookstate = sorted(latencias_bookstate)
    p90_bookstate = sorted_bookstate[int(len(sorted_bookstate) * 0.90)]
    p99_bookstate = sorted_bookstate[int(len(sorted_bookstate) * 0.99)]
    print(f"   p90: {p90_bookstate:.2f}ms")
    print(f"   p99: {p99_bookstate:.2f}ms")
    
    # Comparação
    print("\n" + "=" * 80)
    print("  📈 COMPARAÇÃO")
    print("=" * 80)
    
    reducao_media = statistics.mean(latencias_http) - statistics.mean(latencias_bookstate)
    reducao_p50 = statistics.median(latencias_http) - statistics.median(latencias_bookstate)
    reducao_p90 = p90_http - p90_bookstate
    reducao_p99 = p99_http - p99_bookstate
    
    reducao_jitter = statistics.stdev(latencias_http) - statistics.stdev(latencias_bookstate)
    
    print(f"\n⏱️  REDUÇÃO DE LATÊNCIA:")
    print(f"   Média: {reducao_media:.2f}ms ({reducao_media/statistics.mean(latencias_http)*100:.1f}%)")
    print(f"   p50: {reducao_p50:.2f}ms ({reducao_p50/statistics.median(latencias_http)*100:.1f}%)")
    print(f"   p90: {reducao_p90:.2f}ms ({reducao_p90/p90_http*100:.1f}%)")
    print(f"   p99: {reducao_p99:.2f}ms ({reducao_p99/p99_http*100:.1f}%)")
    
    print(f"\n📊 REDUÇÃO DE JITTER (Desvio Padrão):")
    print(f"   {reducao_jitter:.2f}ms ({reducao_jitter/statistics.stdev(latencias_http)*100:.1f}%)")
    
    print(f"\n✅ GANHOS DA FASE 5:")
    print(f"   - Latência de leitura: {reducao_p50:.2f}ms mais rápido (p50)")
    print(f"   - Jitter reduzido: {reducao_jitter:.2f}ms menos variação")
    print(f"   - Zero HTTP no hot path: ✅")
    print(f"   - Responsividade: {reducao_p99/p99_http*100:.1f}% melhor no p99")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(teste_latencia_fase5())

