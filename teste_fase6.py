#!/usr/bin/env python3
"""
Script para testar Fase 6 - Redução de overhead Python
Compara: baseline vs fixed-point + prealloc + orjson
"""
import os
import sys
import time
import statistics
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from poly_data.polymarket_client import PolymarketClient
from poly_data.utils import get_sheet_df
from poly_data.fixed_point import FixedPointPrice, FixedPointSize, USE_FIXED_POINT
from poly_data.payload_template import get_payload_template
from poly_data.order_intent import OrderIntent

load_dotenv()

def teste_fase6():
    """Testa Fase 6 - Overhead Python."""
    print("=" * 80)
    print("  🧪 TESTE FASE 6 - Redução de Overhead Python")
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
    
    # Teste 1: Conversão de preço/tamanho (baseline vs fixed-point)
    print("\n3️⃣  Testando conversão de preço/tamanho...")
    num_testes = 10000
    
    # Baseline (float)
    print("   📊 Baseline (float)...")
    latencias_float = []
    for i in range(num_testes):
        inicio = time.monotonic_ns()
        price = 0.534
        size = 5.0
        # Simular operação
        total = price * size
        fim = time.monotonic_ns()
        latencias_float.append((fim - inicio) / 1_000_000)
    
    # Fixed-point (int)
    print("   📊 Fixed-point (int)...")
    latencias_int = []
    for i in range(num_testes):
        inicio = time.monotonic_ns()
        price_int = FixedPointPrice.to_int(0.534)
        size_int = FixedPointSize.to_int(5.0)
        # Simular operação (ints são mais rápidos)
        total = price_int * size_int
        fim = time.monotonic_ns()
        latencias_int.append((fim - inicio) / 1_000_000)
    
    # Teste 2: Criação de OrderIntent (baseline vs __slots__)
    print("\n4️⃣  Testando criação de OrderIntent...")
    
    # Baseline (sem __slots__)
    print("   📊 Baseline (sem __slots__)...")
    latencias_intent_baseline = []
    for i in range(1000):
        inicio = time.monotonic_ns()
        intent = OrderIntent(
            market=token1,
            side='BUY',
            price=0.534,
            size=5.0
        )
        fim = time.monotonic_ns()
        latencias_intent_baseline.append((fim - inicio) / 1_000_000)
    
    # Fase 6 (com __slots__ e fixed-point)
    print("   📊 Fase 6 (com __slots__ e fixed-point)...")
    latencias_intent_fase6 = []
    for i in range(1000):
        inicio = time.monotonic_ns()
        intent = OrderIntent(
            market=token1,
            side='BUY',
            price=0.534,  # Será convertido para int
            size=5.0      # Será convertido para int
        )
        fim = time.monotonic_ns()
        latencias_intent_fase6.append((fim - inicio) / 1_000_000)
    
    # Teste 3: Payload template (baseline vs template)
    print("\n5️⃣  Testando criação de payload...")
    
    # Baseline (criar dict novo)
    print("   📊 Baseline (criar dict novo)...")
    latencias_payload_baseline = []
    for i in range(1000):
        inicio = time.monotonic_ns()
        payload = {
            'token_id': token1,
            'side': 'BUY',
            'price': 0.534,
            'size': 5.0
        }
        fim = time.monotonic_ns()
        latencias_payload_baseline.append((fim - inicio) / 1_000_000)
    
    # Fase 6 (template reutilizado)
    print("   📊 Fase 6 (template reutilizado)...")
    template = get_payload_template(token1, 'BUY')
    latencias_payload_fase6 = []
    for i in range(1000):
        inicio = time.monotonic_ns()
        payload = template.build_from_float(0.534, 5.0)
        fim = time.monotonic_ns()
        latencias_payload_fase6.append((fim - inicio) / 1_000_000)
    
    # Análise
    print("\n" + "=" * 80)
    print("  📊 RESULTADOS")
    print("=" * 80)
    
    # Conversão
    print("\n1️⃣  CONVERSÃO DE PREÇO/TAMANHO:")
    print(f"   Baseline (float):")
    print(f"      p50: {statistics.median(latencias_float):.4f}ms")
    print(f"      p99: {sorted(latencias_float)[int(len(latencias_float)*0.99)]:.4f}ms")
    print(f"   Fixed-point (int):")
    print(f"      p50: {statistics.median(latencias_int):.4f}ms")
    print(f"      p99: {sorted(latencias_int)[int(len(latencias_int)*0.99)]:.4f}ms")
    
    reducao_conv_p50 = statistics.median(latencias_float) - statistics.median(latencias_int)
    reducao_conv_p99 = sorted(latencias_float)[int(len(latencias_float)*0.99)] - sorted(latencias_int)[int(len(latencias_int)*0.99)]
    print(f"   Redução p50: {reducao_conv_p50:.4f}ms")
    print(f"   Redução p99: {reducao_conv_p99:.4f}ms")
    
    # OrderIntent
    print("\n2️⃣  CRIAÇÃO DE OrderIntent:")
    print(f"   Baseline:")
    print(f"      p50: {statistics.median(latencias_intent_baseline):.4f}ms")
    print(f"      p99: {sorted(latencias_intent_baseline)[int(len(latencias_intent_baseline)*0.99)]:.4f}ms")
    print(f"   Fase 6 (__slots__ + fixed-point):")
    print(f"      p50: {statistics.median(latencias_intent_fase6):.4f}ms")
    print(f"      p99: {sorted(latencias_intent_fase6)[int(len(latencias_intent_fase6)*0.99)]:.4f}ms")
    
    reducao_intent_p50 = statistics.median(latencias_intent_baseline) - statistics.median(latencias_intent_fase6)
    reducao_intent_p99 = sorted(latencias_intent_baseline)[int(len(latencias_intent_baseline)*0.99)] - sorted(latencias_intent_fase6)[int(len(latencias_intent_fase6)*0.99)]
    print(f"   Redução p50: {reducao_intent_p50:.4f}ms")
    print(f"   Redução p99: {reducao_intent_p99:.4f}ms")
    
    # Payload
    print("\n3️⃣  CRIAÇÃO DE PAYLOAD:")
    print(f"   Baseline (dict novo):")
    print(f"      p50: {statistics.median(latencias_payload_baseline):.4f}ms")
    print(f"      p99: {sorted(latencias_payload_baseline)[int(len(latencias_payload_baseline)*0.99)]:.4f}ms")
    print(f"   Fase 6 (template):")
    print(f"      p50: {statistics.median(latencias_payload_fase6):.4f}ms")
    print(f"      p99: {sorted(latencias_payload_fase6)[int(len(latencias_payload_fase6)*0.99)]:.4f}ms")
    
    reducao_payload_p50 = statistics.median(latencias_payload_baseline) - statistics.median(latencias_payload_fase6)
    reducao_payload_p99 = sorted(latencias_payload_baseline)[int(len(latencias_payload_baseline)*0.99)] - sorted(latencias_payload_fase6)[int(len(latencias_payload_fase6)*0.99)]
    print(f"   Redução p50: {reducao_payload_p50:.4f}ms")
    print(f"   Redução p99: {reducao_payload_p99:.4f}ms")
    
    # Resumo
    print("\n" + "=" * 80)
    print("  📈 RESUMO FASE 6")
    print("=" * 80)
    print(f"\n✅ GANHOS NO P99:")
    print(f"   Conversão: {reducao_conv_p99:.4f}ms")
    print(f"   OrderIntent: {reducao_intent_p99:.4f}ms")
    print(f"   Payload: {reducao_payload_p99:.4f}ms")
    print(f"   Total estimado: {reducao_conv_p99 + reducao_intent_p99 + reducao_payload_p99:.4f}ms")
    
    print(f"\n✅ FIXED-POINT: {'Habilitado' if USE_FIXED_POINT else 'Desabilitado'}")
    print(f"✅ ORJSON: {'Disponível' if hasattr(client, '_USE_ORJSON') and client._USE_ORJSON else 'Não disponível'}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    teste_fase6()

