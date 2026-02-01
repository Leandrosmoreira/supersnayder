#!/usr/bin/env python3
"""
Script para ciclo completo: criar ordens BUY UP e BUY DOWN, aguardar 30s e cancelar
"""
import os
import sys
import time
import asyncio
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from poly_data.polymarket_client import PolymarketClient
from poly_data.utils import get_sheet_df

load_dotenv()

def ciclo_completo_ordens():
    """Ciclo completo: criar ordens BUY UP e BUY DOWN, aguardar 30s e cancelar."""
    print("=" * 80)
    print("  🔄 CICLO COMPLETO: CRIAR ORDENS → AGUARDAR 30s → CANCELAR")
    print("=" * 80)
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
        return False
    
    # Buscar mercados
    print("\n2️⃣  Buscando mercados disponíveis...")
    try:
        df_selected, params = get_sheet_df()
        
        if df_selected.empty:
            print("   ❌ Nenhum mercado selecionado na planilha!")
            return False
        
        mercado = df_selected.iloc[0]
        question = str(mercado.get('question', 'Unknown Market'))
        token1 = str(mercado.get('token1', ''))
        token2 = str(mercado.get('token2', ''))
        condition_id = str(mercado.get('condition_id', ''))
        
        if not token1 or token1 == 'nan' or token1 == '':
            print("   ❌ Token1 não encontrado!")
            return False
        
        print(f"   ✅ Mercado selecionado: {question[:70]}...")
        print(f"   ✅ Token1 (UP): {token1[:30]}...")
        print(f"   ✅ Token2 (DOWN): {token2[:30]}...")
        print(f"   ✅ Condition ID: {condition_id[:30]}...")
        
    except Exception as e:
        print(f"   ❌ Erro ao buscar mercados: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verificar saldo
    print("\n3️⃣  Verificando saldo...")
    try:
        saldo = client.get_usdc_balance()
        print(f"   ✅ Saldo USDC: ${saldo:.2f}")
        
        if saldo < 0.10:
            print("   ⚠️  Saldo insuficiente para teste")
            return False
        
    except Exception as e:
        print(f"   ❌ Erro ao verificar saldo: {e}")
        return False
    
    # Preparar ordens
    print("\n4️⃣  Preparando ordens...")
    try:
        # Obter order book para calcular preço maker
        order_book_up = client.get_order_book(token1)
        order_book_down = client.get_order_book(token2)
        
        if order_book_up and len(order_book_up) == 2:
            bids_up, asks_up = order_book_up
            best_bid_up = float(bids_up.iloc[0]['price']) if not bids_up.empty else 0.01
        else:
            best_bid_up = 0.01
        
        if order_book_down and len(order_book_down) == 2:
            bids_down, asks_down = order_book_down
            best_bid_down = float(bids_down.iloc[0]['price']) if not bids_down.empty else 0.01
        else:
            best_bid_down = 0.01
        
        # Preço maker (abaixo do best bid)
        preco_up = max(0.01, best_bid_up - 0.001) if best_bid_up > 0.01 else 0.01
        preco_down = max(0.01, best_bid_down - 0.001) if best_bid_down > 0.01 else 0.01
        
        # Tamanho mínimo
        tamanho = 5.0
        
        # Lados
        lado_up = 'BUY'
        lado_down = 'BUY'
        
        print(f"   📊 ORDEM 1 - BUY UP:")
        print(f"      Token: {token1[:30]}...")
        print(f"      Lado: {lado_up}")
        print(f"      Preço: ${preco_up:.6f}")
        print(f"      Tamanho: {tamanho:.2f} shares")
        print(f"      Valor: ${preco_up * tamanho:.6f}")
        
        print(f"\n   📊 ORDEM 2 - BUY DOWN:")
        print(f"      Token: {token2[:30]}...")
        print(f"      Lado: {lado_down}")
        print(f"      Preço: ${preco_down:.6f}")
        print(f"      Tamanho: {tamanho:.2f} shares")
        print(f"      Valor: ${preco_down * tamanho:.6f}")
        
        print(f"\n   💰 Valor total: ${(preco_up + preco_down) * tamanho:.6f}")
        
    except Exception as e:
        print(f"   ❌ Erro ao preparar ordens: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Criar ordens
    print("\n5️⃣  Criando ordens BUY UP e BUY DOWN...")
    orders_criadas = []
    inicio_criacao = time.time()
    
    try:
        # Criar ordem BUY UP
        print("   📤 Criando ordem BUY UP...")
        resultado_up = client.create_order(token1, lado_up, preco_up, tamanho, neg_risk=False)
        
        if resultado_up and 'orderID' in resultado_up:
            order_id_up = resultado_up['orderID']
            print(f"      ✅ Ordem BUY UP criada! Order ID: {order_id_up[:20]}...")
            orders_criadas.append({
                'order_id': order_id_up,
                'token': token1,
                'asset_id': token1,
                'tipo': 'BUY UP'
            })
        else:
            print(f"      ❌ Falha ao criar ordem BUY UP")
            return False
        
        # Criar ordem BUY DOWN
        print("   📤 Criando ordem BUY DOWN...")
        resultado_down = client.create_order(token2, lado_down, preco_down, tamanho, neg_risk=False)
        
        if resultado_down and 'orderID' in resultado_down:
            order_id_down = resultado_down['orderID']
            print(f"      ✅ Ordem BUY DOWN criada! Order ID: {order_id_down[:20]}...")
            orders_criadas.append({
                'order_id': order_id_down,
                'token': token2,
                'asset_id': token2,
                'tipo': 'BUY DOWN'
            })
        else:
            print(f"      ❌ Falha ao criar ordem BUY DOWN")
            # Cancelar a primeira se a segunda falhou
            try:
                client.cancel_all_asset(token1)
            except:
                pass
            return False
        
        tempo_criacao = time.time() - inicio_criacao
        print(f"\n   ⚡ Tempo de criação: {tempo_criacao*1000:.2f}ms")
        print(f"   ✅ {len(orders_criadas)} ordens criadas com sucesso!")
        
    except Exception as e:
        print(f"   ❌ Erro ao criar ordens: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Aguardar 30 segundos
    print("\n6️⃣  Aguardando 30 segundos...")
    print("   ⏳ Aguardando... (30s)")
    
    for i in range(30, 0, -1):
        print(f"   ⏱️  {i} segundos restantes...", end='\r')
        time.sleep(1)
    
    print("\n   ✅ 30 segundos decorridos!")
    
    # Cancelar ordens
    print("\n7️⃣  Cancelando ordens...")
    inicio_cancelamento = time.time()
    
    try:
        canceladas = 0
        erros = 0
        
        # Cancelar por asset_id
        for order in orders_criadas:
            try:
                print(f"   🗑️  Cancelando {order['tipo']} (Order ID: {order['order_id'][:20]}...)...")
                client.cancel_all_asset(order['asset_id'])
                canceladas += 1
                print(f"      ✅ Comando de cancelamento enviado para {order['tipo']}")
            except Exception as e:
                erros += 1
                print(f"      ❌ Erro ao cancelar {order['tipo']}: {e}")
        
        # Também cancelar por market (condition_id)
        try:
            print(f"   🗑️  Cancelando todas as ordens do market...")
            client.cancel_all_market(condition_id)
            print(f"      ✅ Comando de cancelamento por market enviado")
        except Exception as e:
            print(f"      ⚠️  Erro ao cancelar por market: {e}")
        
        tempo_cancelamento = time.time() - inicio_cancelamento
        print(f"\n   ⚡ Tempo de cancelamento: {tempo_cancelamento*1000:.2f}ms")
        print(f"   ✅ Cancelamento concluído: {canceladas} ordens, {erros} erros")
        
    except Exception as e:
        print(f"   ❌ Erro ao cancelar ordens: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verificar ordens restantes
    print("\n8️⃣  Verificando ordens restantes...")
    try:
        orders_restantes = client.get_all_orders()
        print(f"   📊 Ordens restantes: {len(orders_restantes)}")
        
        if len(orders_restantes) == 0:
            print("   ✅ Todas as ordens foram canceladas com sucesso!")
        else:
            print("   ⚠️  Ainda existem ordens ativas:")
            for idx, (_, order) in enumerate(orders_restantes.head(5).iterrows(), 1):
                order_id = str(order.get('id', 'N/A'))
                asset_id = str(order.get('asset_id', 'N/A'))
                status = str(order.get('status', 'N/A'))
                print(f"      {idx}. Order ID: {order_id[:20]}... | Asset: {asset_id[:20]}... | Status: {status}")
        
    except Exception as e:
        print(f"   ⚠️  Erro ao verificar ordens restantes: {e}")
    
    # Resumo final
    print("\n" + "=" * 80)
    print("  📊 RESUMO DO CICLO")
    print("=" * 80)
    print(f"   ✅ Ordens criadas: {len(orders_criadas)}")
    print(f"   ⏱️  Tempo de criação: {tempo_criacao*1000:.2f}ms")
    print(f"   ⏱️  Tempo de espera: 30.00s")
    print(f"   ⏱️  Tempo de cancelamento: {tempo_cancelamento*1000:.2f}ms")
    print(f"   ✅ Ordens canceladas: {canceladas}")
    print(f"   📊 Ordens restantes: {len(orders_restantes) if 'orders_restantes' in locals() else 'N/A'}")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    success = ciclo_completo_ordens()
    if success:
        print("\n✅ CICLO COMPLETO CONCLUÍDO COM SUCESSO!")
    else:
        print("\n❌ CICLO COMPLETO FALHOU")
        sys.exit(1)

