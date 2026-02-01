#!/usr/bin/env python3
"""
Script para testar o envio de uma ordem maker, aguardar 30 segundos e cancelá-la.
Cria uma ordem com características únicas para facilitar a identificação.
"""
import os
import sys
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import requests

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from poly_data.polymarket_client import PolymarketClient
from poly_data.utils import get_sheet_df

# Carregar variáveis de ambiente
load_dotenv()

def verificar_ordem_no_orderbook(client, token, preco, lado, tamanho, order_id=None, timeout=30):
    """
    Verifica se uma ordem apareceu no order book do Polymarket.
    Retorna o tempo decorrido desde o início até a ordem aparecer.
    
    Args:
        client: PolymarketClient
        token: Token ID da ordem
        preco: Preço da ordem
        lado: 'BUY' ou 'SELL'
        tamanho: Tamanho da ordem
        order_id: Order ID para verificação mais precisa (opcional)
        timeout: Tempo máximo para aguardar (segundos)
    
    Returns:
        dict: {'encontrada': bool, 'tempo_decorrido': float, 'tentativas': int}
    """
    inicio = time.time()
    tentativas = 0
    max_tentativas = timeout * 4  # Verificar a cada 0.25 segundos para maior precisão
    
    print(f"   🔍 Verificando se a ordem apareceu no order book...")
    print(f"      Procurando: {lado} @ ${preco:.6f} com {tamanho:.2f} shares")
    
    # Primeiro, verificar se a ordem está nas ordens ativas (mais confiável)
    if order_id:
        print(f"      Usando Order ID para verificação: {order_id[:20]}...")
        for _ in range(10):  # Verificar por até 2.5 segundos
            try:
                orders_ativas = client.get_all_orders()
                if not orders_ativas.empty:
                    # Procurar pelo order ID
                    for idx, row in orders_ativas.iterrows():
                        order_id_ativo = str(row.get('id', ''))
                        if order_id.lower() in order_id_ativo.lower() or order_id_ativo.lower() in order_id.lower():
                            tempo_decorrido = time.time() - inicio
                            print(f"      ✅ ORDEM ENCONTRADA NAS ORDENS ATIVAS!")
                            print(f"         Tempo: {tempo_decorrido*1000:.2f}ms")
                            return {
                                'encontrada': True,
                                'tempo_decorrido': tempo_decorrido,
                                'tentativas': tentativas + 1,
                                'metodo': 'ordens_ativas'
                            }
                time.sleep(0.25)
            except:
                time.sleep(0.25)
    
    # Se não encontrou nas ordens ativas, verificar no order book
    print(f"      Verificando no order book...")
    tamanho_anterior = 0
    
    while tentativas < max_tentativas:
        tentativas += 1
        tempo_decorrido = time.time() - inicio
        
        try:
            # Obter order book atual
            order_book_result = client.get_order_book(token)
            
            if order_book_result and len(order_book_result) == 2:
                bids_df, asks_df = order_book_result
                
                # Verificar no lado correto (BID para BUY, ASK para SELL)
                if lado == 'BUY':
                    df_to_check = bids_df
                else:
                    df_to_check = asks_df
                
                if not df_to_check.empty:
                    # Procurar por uma ordem com preço exato
                    # Verificar se o tamanho total no nível de preço aumentou
                    for idx, row in df_to_check.iterrows():
                        preco_orderbook = float(row['price'])
                        tamanho_orderbook = float(row.get('size', row.get('amount', 0)))
                        
                        # Verificar se o preço está exato (tolerância muito pequena)
                        if abs(preco_orderbook - preco) < 0.00001:
                            # Verificar se o tamanho aumentou (nossa ordem foi adicionada)
                            # Ou se o tamanho está próximo do esperado
                            if tamanho_orderbook >= tamanho * 0.8 or tamanho_orderbook > tamanho_anterior + tamanho * 0.5:
                                print(f"      ✅ ORDEM ENCONTRADA NO ORDER BOOK!")
                                print(f"         Preço encontrado: ${preco_orderbook:.6f}")
                                print(f"         Tamanho encontrado: {tamanho_orderbook:.2f} shares")
                                return {
                                    'encontrada': True,
                                    'tempo_decorrido': tempo_decorrido,
                                    'tentativas': tentativas,
                                    'preco_encontrado': preco_orderbook,
                                    'tamanho_encontrado': tamanho_orderbook,
                                    'metodo': 'order_book'
                                }
                            
                            # Guardar tamanho anterior para comparação
                            tamanho_anterior = max(tamanho_anterior, tamanho_orderbook)
                
                # Mostrar progresso a cada segundo
                if tentativas % 4 == 0:
                    print(f"      ⏳ Aguardando... {tempo_decorrido:.2f}s decorridos (tentativa {tentativas})")
            
            # Aguardar 0.25 segundos antes da próxima verificação (mais frequente)
            time.sleep(0.25)
            
        except Exception as e:
            # Em caso de erro, continuar tentando
            if tentativas % 4 == 0:
                print(f"      ⚠️  Erro ao verificar order book: {e}")
            time.sleep(0.25)
    
    # Timeout atingido
    tempo_total = time.time() - inicio
    print(f"      ⏱️  Timeout atingido após {tempo_total:.2f} segundos")
    return {
        'encontrada': False,
        'tempo_decorrido': tempo_total,
        'tentativas': tentativas
    }

def teste_ordem_maker_verificacao():
    """Testa o envio de uma ordem maker e fornece informações para verificação no site."""
    
    print("=" * 80)
    print("🧪 TESTE DE ORDEM MAKER - CRIAÇÃO E CANCELAMENTO APÓS 30s")
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
    
    # Buscar mercados disponíveis
    print("\n2️⃣  Buscando mercados disponíveis...")
    try:
        df_selected, params = get_sheet_df()
        
        if df_selected.empty:
            print("   ❌ Nenhum mercado selecionado na planilha!")
            print("   💡 Adicione mercados na aba 'Selected Markets' da planilha.")
            return False
        
        # Usar o primeiro mercado selecionado
        mercado = df_selected.iloc[0]
        
        # Extrair informações do mercado
        question = str(mercado.get('question', 'Unknown Market'))
        token1 = str(mercado.get('token1', ''))
        token2 = str(mercado.get('token2', ''))
        condition_id = str(mercado.get('condition_id', ''))
        
        # Verificar se os tokens estão presentes
        if not token1 or token1 == 'nan' or token1 == '':
            print("   ❌ Token1 não encontrado no mercado!")
            print("   💡 Execute 'python data_updater/data_updater.py' para atualizar os dados.")
            return False
        
        print(f"   ✅ Mercado selecionado: {question[:70]}...")
        print(f"   ✅ Token1: {token1[:30]}...")
        print(f"   ✅ Token2: {token2[:30]}...")
        print(f"   ✅ Condition ID: {condition_id[:30]}...")
        
    except Exception as e:
        print(f"   ❌ Erro ao buscar mercados: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verificar saldo disponível
    print("\n3️⃣  Verificando saldo disponível...")
    try:
        saldo_usdc = client.get_usdc_balance()
        print(f"   ✅ Saldo USDC: ${saldo_usdc:.2f}")
        
        if saldo_usdc < 1.0:
            print("   ⚠️  Saldo muito baixo! A ordem pode falhar.")
    except Exception as e:
        print(f"   ⚠️  Não foi possível verificar saldo: {e}")
        saldo_usdc = 10.0  # Fallback
    
    # Obter order book atual
    print("\n4️⃣  Verificando order book atual...")
    try:
        order_book_result = client.get_order_book(token1)
        if order_book_result and len(order_book_result) == 2:
            bids_df, asks_df = order_book_result
            
            if not bids_df.empty:
                best_bid = float(bids_df.iloc[0]['price'])
                print(f"   ✅ Best Bid atual: ${best_bid:.4f}")
            else:
                best_bid = 0.50
                print("   ⚠️  Sem bids no order book, usando preço padrão: $0.50")
            
            if not asks_df.empty:
                best_ask = float(asks_df.iloc[0]['price'])
                print(f"   ✅ Best Ask atual: ${best_ask:.4f}")
            else:
                best_ask = 0.51
                print("   ⚠️  Sem asks no order book, usando preço padrão: $0.51")
        else:
            best_bid = 0.50
            best_ask = 0.51
            print("   ⚠️  Order book vazio, usando preços padrão")
    except Exception as e:
        print(f"   ⚠️  Erro ao obter order book: {e}")
        best_bid = 0.50
        best_ask = 0.51
    
    # Preparar duas ordens maker: BUY UP (token1) e BUY DOWN (token2)
    print("\n5️⃣  Preparando duas ordens maker (BUY UP e BUY DOWN)...")
    
    # Ordem 1: BUY UP (comprar token1 - "Yes")
    token_up = token1
    lado_up = 'BUY'
    
    # Preço para BUY UP: 1 centavo abaixo do best_bid para garantir que seja maker
    preco_up = max(0.01, best_bid - 0.0001)
    if preco_up < 0.01:
        preco_up = 0.45
        print(f"   ⚠️  Preço BUY UP ajustado para $0.45 (valor de teste)")
    
    # Ordem 2: BUY DOWN (comprar token2 - "No")
    token_down = token2
    lado_down = 'BUY'
    
    # Para BUY DOWN, precisamos obter o order book do token2
    try:
        order_book_result_down = client.get_order_book(token2)
        if order_book_result_down and len(order_book_result_down) == 2:
            bids_df_down, asks_df_down = order_book_result_down
            if not bids_df_down.empty:
                best_bid_down = float(bids_df_down.iloc[0]['price'])
            else:
                best_bid_down = 0.50
        else:
            best_bid_down = 0.50
    except Exception as e:
        print(f"   ⚠️  Erro ao obter order book do token2: {e}")
        best_bid_down = 0.50
    
    # Preço para BUY DOWN: 1 centavo abaixo do best_bid do token2
    preco_down = max(0.01, best_bid_down - 0.0001)
    if preco_down < 0.01:
        preco_down = 0.45
        print(f"   ⚠️  Preço BUY DOWN ajustado para $0.45 (valor de teste)")
    
    # Tamanho: usar um valor pequeno mas visível (5 shares para cada)
    tamanho = 5.0
    
    # Calcular valor total para ambas as ordens
    valor_total_up = preco_up * tamanho
    valor_total_down = preco_down * tamanho
    valor_total_ambas = valor_total_up + valor_total_down
    
    # Verificar se cabe no saldo (usar 70% do saldo para ter margem)
    if valor_total_ambas > saldo_usdc * 0.7:
        # Ajustar tamanho proporcionalmente
        tamanho = (saldo_usdc * 0.7) / (preco_up + preco_down)
        tamanho = max(1.0, tamanho)
        valor_total_up = preco_up * tamanho
        valor_total_down = preco_down * tamanho
        valor_total_ambas = valor_total_up + valor_total_down
        print(f"   ⚠️  Tamanho ajustado para caber no saldo: {tamanho:.2f} shares cada")
    
    print(f"\n   📊 ORDEM 1 - BUY UP (Token 'Yes'):")
    print(f"      ✅ Token: {token_up[:30]}...")
    print(f"      ✅ Lado: {lado_up}")
    print(f"      ✅ Preço: ${preco_up:.6f} (maker - abaixo do best bid)")
    print(f"      ✅ Tamanho: {tamanho:.2f} shares")
    print(f"      ✅ Valor total: ${valor_total_up:.6f}")
    
    print(f"\n   📊 ORDEM 2 - BUY DOWN (Token 'No'):")
    print(f"      ✅ Token: {token_down[:30]}...")
    print(f"      ✅ Lado: {lado_down}")
    print(f"      ✅ Preço: ${preco_down:.6f} (maker - abaixo do best bid)")
    print(f"      ✅ Tamanho: {tamanho:.2f} shares")
    print(f"      ✅ Valor total: ${valor_total_down:.6f}")
    
    print(f"\n   💰 Valor total das duas ordens: ${valor_total_ambas:.6f}")
    
    # Mostrar resumo
    print("\n" + "=" * 80)
    print("📋 RESUMO DAS ORDENS QUE SERÃO CRIADAS:")
    print("=" * 80)
    print(f"   📊 Mercado: {question[:70]}...")
    print(f"   📍 Condition ID: {condition_id[:50]}...")
    print(f"\n   🔼 ORDEM 1 - BUY UP:")
    print(f"      🪙 Token: {token_up[:30]}...")
    print(f"      🔄 Ação: {lado_up} (comprar token 'Yes')")
    print(f"      💰 Preço: ${preco_up:.6f}")
    print(f"      📦 Tamanho: {tamanho:.2f} shares")
    print(f"      💵 Valor: ${valor_total_up:.6f}")
    print(f"\n   🔽 ORDEM 2 - BUY DOWN:")
    print(f"      🪙 Token: {token_down[:30]}...")
    print(f"      🔄 Ação: {lado_down} (comprar token 'No')")
    print(f"      💰 Preço: ${preco_down:.6f}")
    print(f"      📦 Tamanho: {tamanho:.2f} shares")
    print(f"      💵 Valor: ${valor_total_down:.6f}")
    print(f"\n   💰 Valor total: ${valor_total_ambas:.6f}")
    print(f"   ⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Confirmar
    print("\n⚠️  ATENÇÃO: Duas ordens serão enviadas ao Polymarket!")
    print("   As ordens serão canceladas automaticamente após 30 segundos.")
    print("   Será executado um 'cancel all orders' no order book.\n")
    
    try:
        resposta = input("❓ Deseja enviar esta ordem? (s/n): ").strip().lower()
        if resposta != 's':
            print("❌ Operação cancelada pelo usuário.")
            return False
    except EOFError:
        print("⚠️  Ambiente não-interativo. Enviando automaticamente...")
    
    # FASE 1: Paralelização - Enviar duas ordens em paralelo
    print("\n6️⃣  Enviando duas ordens maker (PARALELO - Fase 1)...")
    timestamp_criacao = datetime.now()
    orders_criadas = []
    
    try:
        # FASE 1: Função para enviar ordem (para usar em paralelo)
        def enviar_ordem(token, lado, preco, tamanho, tipo):
            """Envia uma ordem e retorna resultado com timestamp."""
            timestamp_envio = time.time()
            timestamp_envio_str = datetime.fromtimestamp(timestamp_envio).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            print(f"   📤 Enviando {tipo}...")
            result = client.create_order(token, lado, preco, tamanho, neg_risk=False)
            
            if result:
                order_id = result.get('orderID', 'N/A')
                print(f"      ✅ {tipo} criada! Order ID: {order_id[:20]}...")
                print(f"      ⏰ Timestamp de envio: {timestamp_envio_str}")
                return {
                    'order_id': order_id,
                    'token': token,
                    'lado': lado,
                    'preco': preco,
                    'tamanho': tamanho,
                    'tipo': tipo,
                    'timestamp_envio': timestamp_envio,
                    'timestamp_envio_str': timestamp_envio_str,
                    'success': True
                }
            else:
                print(f"      ❌ Falha ao criar {tipo}")
                return {'success': False, 'tipo': tipo}
        
        # FASE 1: Enviar ordens em paralelo usando ThreadPoolExecutor
        print("   🚀 Enviando ordens em PARALELO (otimização Fase 1)...")
        inicio_paralelo = time.time()
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_up = executor.submit(
                enviar_ordem, token_up, lado_up, preco_up, tamanho, 'ORDEM 1 - BUY UP'
            )
            future_down = executor.submit(
                enviar_ordem, token_down, lado_down, preco_down, tamanho, 'ORDEM 2 - BUY DOWN'
            )
            
            # Aguardar ambas as ordens
            resultado_up = future_up.result()
            resultado_down = future_down.result()
        
        tempo_paralelo = time.time() - inicio_paralelo
        print(f"\n   ⚡ Tempo total (paralelo): {tempo_paralelo*1000:.2f}ms")
        
        # Verificar resultados
        if not resultado_up.get('success'):
            print(f"   ❌ Falha ao criar ordem 1")
            return False
        
        if not resultado_down.get('success'):
            print(f"   ❌ Falha ao criar ordem 2")
            # Cancelar a primeira ordem se a segunda falhou
            try:
                client.cancel_all_asset(token_up)
            except:
                pass
            return False
        
        # Adicionar ordens criadas
        orders_criadas.append(resultado_up)
        orders_criadas.append(resultado_down)
        
        # FASE 1: Remover polling desnecessário - Verificação opcional
        # Comentado para reduzir latência. Descomente se precisar verificar latência.
        verificar_latencia = os.getenv('VERIFICAR_LATENCIA', 'false').lower() == 'true'
        
        if verificar_latencia:
            print(f"\n   🔍 Medindo latência (opcional)...")
            # Verificar quando as ordens aparecem no order book
            for order in orders_criadas:
                print(f"\n   🔍 Verificando {order['tipo']}...")
                resultado_verificacao = verificar_ordem_no_orderbook(
                    client, order['token'], order['preco'], order['lado'], 
                    order['tamanho'], order_id=order['order_id'], timeout=10
                )
                order['verificacao'] = resultado_verificacao
                
                if resultado_verificacao['encontrada']:
                    latencia_ms = resultado_verificacao['tempo_decorrido'] * 1000
                    print(f"      ✅ Latência: {latencia_ms:.2f}ms ({resultado_verificacao['tempo_decorrido']:.3f}s)")
                else:
                    print(f"      ⚠️  Ordem não encontrada no order book dentro do timeout")
        else:
            print(f"\n   ⚡ Polling desabilitado (otimização Fase 1 - reduz latência)")
            print(f"   💡 Para habilitar verificação de latência, defina VERIFICAR_LATENCIA=true no .env")
        
        # Resumo das ordens criadas com latência
        print("\n" + "=" * 80)
        print("✅ AMBAS AS ORDENS CRIADAS COM SUCESSO!")
        print("=" * 80)
        for idx, order in enumerate(orders_criadas, 1):
            print(f"\n   📋 ORDEM {idx} - {order['tipo']}:")
            print(f"      Order ID: {order['order_id']}")
            print(f"      Token: {order['token'][:30]}...")
            print(f"      Lado: {order['lado']}")
            print(f"      Preço: ${order['preco']:.6f}")
            print(f"      Tamanho: {order['tamanho']:.2f} shares")
            print(f"      ⏰ Enviada em: {order['timestamp_envio_str']}")
            
            # Mostrar latência se disponível
            if 'verificacao' in order:
                verificacao = order['verificacao']
                if verificacao['encontrada']:
                    latencia_ms = verificacao['tempo_decorrido'] * 1000
                    print(f"      ⚡ Latência: {latencia_ms:.2f}ms ({verificacao['tempo_decorrido']:.3f}s)")
                    print(f"      📊 Tentativas: {verificacao['tentativas']}")
                else:
                    print(f"      ⚠️  Não encontrada no order book (timeout: {verificacao['tempo_decorrido']:.2f}s)")
        
        # Calcular latência média (se verificação foi habilitada)
        latencias = []
        for order in orders_criadas:
            if 'verificacao' in order and order['verificacao'].get('encontrada', False):
                latencias.append(order['verificacao']['tempo_decorrido'] * 1000)
        
        if latencias:
            latencia_media = sum(latencias) / len(latencias)
            latencia_min = min(latencias)
            latencia_max = max(latencias)
            print(f"\n   📊 ESTATÍSTICAS DE LATÊNCIA:")
            print(f"      Média: {latencia_media:.2f}ms")
            print(f"      Mínima: {latencia_min:.2f}ms")
            print(f"      Máxima: {latencia_max:.2f}ms")
        else:
            print(f"\n   ⚡ Latência não medida (polling desabilitado para otimização)")
        
        print(f"\n   ⏰ Criadas em: {timestamp_criacao.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Salvar informações em arquivo
        info_file = "ultima_ordem_teste.txt"
        with open(info_file, 'w') as f:
            f.write(f"TESTE DE ORDENS MAKER (BUY UP + BUY DOWN) - {timestamp_criacao.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Mercado: {question}\n")
            f.write(f"Condition ID: {condition_id}\n\n")
            for idx, order in enumerate(orders_criadas, 1):
                f.write(f"ORDEM {idx} - {order['tipo']}:\n")
                f.write(f"  Order ID: {order['order_id']}\n")
                f.write(f"  Token: {order['token']}\n")
                f.write(f"  Lado: {order['lado']}\n")
                f.write(f"  Preço: ${order['preco']:.6f}\n")
                f.write(f"  Tamanho: {order['tamanho']:.2f} shares\n\n")
        
        print(f"\n💾 Informações salvas em: {info_file}")
        
        # Aguardar 30 segundos antes de cancelar
        print("\n" + "=" * 80)
        print("⏳ AGUARDANDO 30 SEGUNDOS ANTES DE CANCELAR TODAS AS ORDENS...")
        print("=" * 80)
        print("   💡 Você pode verificar as ordens no site durante este tempo:")
        print(f"      1. Acesse: https://polymarket.com")
        print(f"      2. Procure pelo mercado: {question[:50]}...")
        print(f"      3. No order book, procure por duas ordens BUY:")
        print(f"         - BUY UP: Preço ${preco_up:.6f}, Tamanho {tamanho:.2f} shares")
        print(f"         - BUY DOWN: Preço ${preco_down:.6f}, Tamanho {tamanho:.2f} shares")
        print("=" * 80)
        print()
        
        # Contador regressivo de 30 segundos
        for i in range(30, 0, -1):
            print(f"   ⏰ Cancelamento em {i:2d} segundos...", end='\r')
            time.sleep(1)
        print()  # Nova linha após o contador
        
        # Cancelar TODAS as ordens após 30 segundos
        print("\n7️⃣  Cancelando TODAS as ordens do order book...")
        timestamp_cancelamento = datetime.now()
        tempo_decorrido = (timestamp_cancelamento - timestamp_criacao).total_seconds()
        
        try:
            # Verificar ordens ativas antes de cancelar
            print("   📊 Verificando ordens ativas...")
            orders_ativas = client.get_all_orders()
            print(f"   ✅ Encontradas {len(orders_ativas)} ordem(ns) ativa(s)")
            
            # Cancelar TODAS as ordens usando cancel_all_orders
            print("   🛑 Executando 'cancel all orders'...")
            
            # Cancelar ordens de ambos os tokens
            client.cancel_all_asset(token_up)
            print(f"   ✅ Ordens do token UP canceladas")
            
            client.cancel_all_asset(token_down)
            print(f"   ✅ Ordens do token DOWN canceladas")
            
            # Verificar se ainda há ordens ativas
            orders_restantes = client.get_all_orders()
            
            print("\n" + "=" * 80)
            print("✅ CANCELAMENTO CONCLUÍDO!")
            print("=" * 80)
            print(f"   📋 Ordens canceladas: {len(orders_criadas)}")
            for idx, order in enumerate(orders_criadas, 1):
                print(f"      {idx}. {order['tipo']} - Order ID: {order['order_id'][:20]}...")
            print(f"\n   ⏰ Criadas em: {timestamp_criacao.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   ⏰ Canceladas em: {timestamp_cancelamento.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   ⏱️  Tempo decorrido: {tempo_decorrido:.1f} segundos")
            print(f"   📊 Ordens restantes no order book: {len(orders_restantes)}")
            print("=" * 80)
            
            # Atualizar arquivo com informações de cancelamento e latência
            with open(info_file, 'a') as f:
                f.write(f"\nCANCELADAS EM: {timestamp_cancelamento.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Tempo decorrido: {tempo_decorrido:.1f} segundos\n")
                f.write(f"Ordens restantes no order book: {len(orders_restantes)}\n\n")
                f.write("LATÊNCIA (VPS -> Polymarket):\n")
                f.write("=" * 80 + "\n")
                for idx, order in enumerate(orders_criadas, 1):
                    f.write(f"\nORDEM {idx} - {order['tipo']}:\n")
                    f.write(f"  Enviada em: {order['timestamp_envio_str']}\n")
                    if 'verificacao' in order:
                        verificacao = order['verificacao']
                        if verificacao['encontrada']:
                            latencia_ms = verificacao['tempo_decorrido'] * 1000
                            f.write(f"  Latência: {latencia_ms:.2f}ms ({verificacao['tempo_decorrido']:.3f}s)\n")
                            f.write(f"  Tentativas: {verificacao['tentativas']}\n")
                        else:
                            f.write(f"  Status: Não encontrada (timeout: {verificacao['tempo_decorrido']:.2f}s)\n")
                
                # Estatísticas
                latencias = []
                for order in orders_criadas:
                    if 'verificacao' in order and order['verificacao']['encontrada']:
                        latencias.append(order['verificacao']['tempo_decorrido'] * 1000)
                
                if latencias:
                    latencia_media = sum(latencias) / len(latencias)
                    latencia_min = min(latencias)
                    latencia_max = max(latencias)
                    f.write(f"\nESTATÍSTICAS:\n")
                    f.write(f"  Média: {latencia_media:.2f}ms\n")
                    f.write(f"  Mínima: {latencia_min:.2f}ms\n")
                    f.write(f"  Máxima: {latencia_max:.2f}ms\n")
            
            print(f"\n💾 Informações atualizadas em: {info_file}")
            print("\n✅ Teste concluído com sucesso!")
            print("   As duas ordens foram criadas, permaneceram ativas por ~30 segundos")
            print("   e foram canceladas. Todas as ordens do order book foram canceladas.")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Erro ao cancelar ordens: {e}")
            import traceback
            traceback.print_exc()
            print(f"\n⚠️  Algumas ordens podem ainda estar ativas.")
            print("   Você pode cancelá-las manualmente usando:")
            print(f"   python cancel_all_orders.py")
            return False
            
    except Exception as e:
        print(f"\n❌ Erro ao criar ordens: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = teste_ordem_maker_verificacao()
    sys.exit(0 if sucesso else 1)

