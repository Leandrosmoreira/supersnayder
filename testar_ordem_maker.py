#!/usr/bin/env python3
"""
Script para testar o envio de uma ordem maker com lote mínimo.
Isso verifica se o motor de envio de ordens está funcionando corretamente.
"""
import os
import sys
from dotenv import load_dotenv
import pandas as pd

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from poly_data.polymarket_client import PolymarketClient
from poly_data.utils import get_sheet_df

# Carregar variáveis de ambiente
load_dotenv()

def testar_ordem_maker():
    """Testa o envio de uma ordem maker com lote mínimo."""
    
    print("=" * 70)
    print("🧪 TESTE DE ORDEM MAKER - LOTE MÍNIMO")
    print("=" * 70)
    
    # Inicializar cliente
    print("\n1️⃣  Inicializando cliente Polymarket...")
    try:
        client = PolymarketClient()
        print("   ✓ Cliente inicializado com sucesso")
    except Exception as e:
        print(f"   ❌ Erro ao inicializar cliente: {e}")
        return False
    
    # Buscar mercados disponíveis
    print("\n2️⃣  Buscando mercados disponíveis...")
    try:
        df_selected, params = get_sheet_df()
        
        # Se não houver mercados selecionados, buscar da aba "All Markets"
        if df_selected.empty:
            print("   ⚠️  Nenhum mercado selecionado. Buscando da aba 'All Markets'...")
            # Tentar buscar da aba All Markets diretamente
            import gspread
            from google.oauth2.service_account import Credentials
            
            scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds_file = 'secrets/credentials.json' if os.path.exists('secrets/credentials.json') else 'credentials.json'
            creds = Credentials.from_service_account_file(creds_file, scopes=scope)
            gs_client = gspread.authorize(creds)
            sheet = gs_client.open_by_url(os.getenv("SPREADSHEET_URL"))
            worksheet = sheet.worksheet("All Markets")
            df_all = pd.DataFrame(worksheet.get_all_records())
            
            if df_all.empty:
                print("   ❌ Nenhum mercado encontrado na planilha!")
                return False
            
            # Pegar o primeiro mercado com min_size válido
            df_all = df_all[df_all['min_size'].notna() & (df_all['min_size'] > 0)]
            if df_all.empty:
                print("   ❌ Nenhum mercado com min_size válido encontrado!")
                return False
            
            mercado = df_all.iloc[0]
            token1 = mercado.get('token1', '')
            token2 = mercado.get('token2', '')
            min_size = float(mercado.get('min_size', 50))
            best_bid = float(mercado.get('best_bid', 0.5))
            best_ask = float(mercado.get('best_ask', 0.5))
            question = mercado.get('question', 'Unknown Market')
        else:
            # Usar o primeiro mercado selecionado
            mercado = df_selected.iloc[0]
            
            # Buscar dados completos da aba All Markets
            import gspread
            from google.oauth2.service_account import Credentials
            
            scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds_file = 'secrets/credentials.json' if os.path.exists('secrets/credentials.json') else 'credentials.json'
            creds = Credentials.from_service_account_file(creds_file, scopes=scope)
            gs_client = gspread.authorize(creds)
            sheet = gs_client.open_by_url(os.getenv("SPREADSHEET_URL"))
            worksheet = sheet.worksheet("All Markets")
            df_all = pd.DataFrame(worksheet.get_all_records())
            
            # Encontrar o mercado correspondente
            mercado_all = df_all[df_all['question'] == mercado.get('question', '')]
            if not mercado_all.empty:
                mercado_data = mercado_all.iloc[0]
                token1 = str(mercado_data.get('token1', ''))
                token2 = str(mercado_data.get('token2', ''))
                min_size = float(mercado_data.get('min_size', 50))
                best_bid = float(mercado_data.get('best_bid', 0.5))
                best_ask = float(mercado_data.get('best_ask', 0.5))
            else:
                # Se não encontrou, usar valores do mercado selecionado
                token1 = str(mercado.get('token1', ''))
                token2 = str(mercado.get('token2', ''))
                min_size = 50  # Default
                best_bid = 0.5
                best_ask = 0.5
            
            question = mercado.get('question', 'Unknown Market')
            
            # Se ainda não tem token, tentar buscar da planilha diretamente
            if not token1 or token1 == 'nan' or token1 == '':
                print("   ⚠️  Token1 vazio, tentando buscar da planilha...")
                # Tentar usar o primeiro mercado da All Markets que tenha token
                df_all_with_tokens = df_all[df_all['token1'].notna() & (df_all['token1'] != '')]
                if not df_all_with_tokens.empty:
                    mercado_data = df_all_with_tokens.iloc[0]
                    token1 = str(mercado_data.get('token1', ''))
                    token2 = str(mercado_data.get('token2', ''))
                    min_size = float(mercado_data.get('min_size', 50))
                    best_bid = float(mercado_data.get('best_bid', 0.5))
                    best_ask = float(mercado_data.get('best_ask', 0.5))
                    question = mercado_data.get('question', 'Unknown Market')
                    print(f"   ✓ Usando mercado alternativo: {question[:60]}...")
        
        print(f"   ✓ Mercado selecionado: {question[:60]}...")
        print(f"   ✓ Token1: {token1}")
        print(f"   ✓ Token2: {token2}")
        print(f"   ✓ Min Size: {min_size}")
        print(f"   ✓ Best Bid: {best_bid:.4f}")
        print(f"   ✓ Best Ask: {best_ask:.4f}")
        
    except Exception as e:
        print(f"   ❌ Erro ao buscar mercados: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verificar saldo disponível
    print("\n3️⃣  Verificando saldo disponível...")
    try:
        saldo_usdc = client.get_usdc_balance()
        print(f"   ✓ Saldo USDC: ${saldo_usdc:.2f}")
        
        # Limite máximo: usar 80% do saldo para ter margem de segurança
        limite_maximo = saldo_usdc * 0.8
        print(f"   ✓ Limite máximo para ordem: ${limite_maximo:.2f} (80% do saldo)")
    except Exception as e:
        print(f"   ⚠️  Não foi possível verificar saldo: {e}")
        saldo_usdc = 9.0  # Fallback
        limite_maximo = 7.0
    
    # Escolher token e lado da ordem
    print("\n4️⃣  Preparando ordem maker...")
    
    # Usar token1 para BUY (comprar o token "Yes")
    token = token1
    lado = 'BUY'
    
    # Converter preços de centavos para escala 0-1 (best_bid e best_ask estão em centavos)
    best_bid_normalized = best_bid / 100.0 if best_bid > 1.0 else best_bid
    best_ask_normalized = best_ask / 100.0 if best_ask > 1.0 else best_ask
    
    # Preço: 1 centavo abaixo do best_bid para garantir que seja maker
    # Se best_bid está em centavos, subtrair 0.01 centavos = 0.0001 na escala normalizada
    preco = max(0.01, best_bid_normalized - 0.0001)
    
    # Se o preço ficar muito baixo, usar um preço mais razoável (meio do spread)
    if preco < 0.01:
        preco = (best_bid_normalized + best_ask_normalized) / 2.0
        preco = max(0.01, min(0.99, preco))
    
    # Calcular tamanho baseado no saldo disponível
    # Tamanho máximo = limite_maximo / preco
    tamanho_maximo_por_saldo = limite_maximo / preco if preco > 0 else min_size
    
    # Usar o menor entre: min_size, tamanho_maximo_por_saldo, ou um valor seguro
    tamanho = min(min_size, tamanho_maximo_por_saldo, 50)  # Máximo de 50 shares para teste
    
    # Garantir que o tamanho seja pelo menos 1 share
    tamanho = max(1.0, tamanho)
    
    # Calcular valor total da ordem
    valor_total = preco * tamanho
    
    print(f"   ✓ Tamanho calculado: {tamanho:.2f} shares")
    print(f"   ✓ Valor total da ordem: ${valor_total:.2f}")
    
    # Verificar se o valor está dentro do limite
    if valor_total > limite_maximo:
        print(f"   ⚠️  Ajustando tamanho para caber no saldo...")
        tamanho = limite_maximo / preco
        tamanho = max(1.0, min(tamanho, 50))  # Entre 1 e 50 shares
        valor_total = preco * tamanho
        print(f"   ✓ Tamanho ajustado: {tamanho:.2f} shares")
        print(f"   ✓ Novo valor total: ${valor_total:.2f}")
    
    print(f"   ✓ Token: {token}")
    print(f"   ✓ Lado: {lado}")
    print(f"   ✓ Best Bid (normalizado): {best_bid_normalized:.4f}")
    print(f"   ✓ Best Ask (normalizado): {best_ask_normalized:.4f}")
    print(f"   ✓ Preço: {preco:.4f} (maker - abaixo do best_bid)")
    print(f"   ✓ Tamanho: {tamanho:.2f} shares (ajustado ao saldo)")
    print(f"   ✓ Valor total: ${valor_total:.2f}")
    
    # Obter order book atual para verificar
    print("\n5️⃣  Verificando order book atual...")
    try:
        order_book = client.get_order_book(token)
        if order_book and isinstance(order_book, dict) and 'bids' in order_book and len(order_book['bids']) > 0:
            best_bid_atual = float(order_book['bids'][0]['price'])
            print(f"   ✓ Best Bid atual: {best_bid_atual:.4f}")
            # Ajustar preço se necessário (garantir que seja maker - abaixo do best bid)
            if preco >= best_bid_atual:
                preco = max(0.01, best_bid_atual - 0.0001)
                print(f"   ✓ Preço ajustado para: {preco:.4f} (garantir que seja maker)")
        else:
            print("   ⚠️  Order book vazio ou sem bids")
    except Exception as e:
        print(f"   ⚠️  Não foi possível obter order book: {e}")
    
    # Verificar se token é válido
    if not token or token == '' or token == 'nan':
        print("\n❌ ERRO: Token inválido ou vazio!")
        print(f"   Token1: {token1}")
        print(f"   Token2: {token2}")
        return False
    
    # Confirmar antes de enviar (ou usar auto se passado como argumento)
    print("\n" + "=" * 70)
    print("📋 RESUMO DA ORDEM:")
    print(f"   Mercado: {question[:60]}...")
    print(f"   Token: {token}")
    print(f"   Ação: {lado}")
    print(f"   Preço: ${preco:.4f}")
    print(f"   Tamanho: {tamanho} shares")
    print(f"   Total: ${preco * tamanho:.2f}")
    print("=" * 70)
    
    # Se passou --auto como argumento, enviar automaticamente
    auto_mode = '--auto' in sys.argv or '-y' in sys.argv
    
    if not auto_mode:
        try:
            resposta = input("\n❓ Deseja enviar esta ordem? (s/n): ").strip().lower()
            if resposta != 's':
                print("❌ Operação cancelada pelo usuário.")
                return False
        except EOFError:
            # Se não há input disponível (ambiente não-interativo), usar modo auto
            print("\n⚠️  Ambiente não-interativo detectado. Usando modo automático...")
            auto_mode = True
    
    if auto_mode:
        print("\n🚀 Modo automático: enviando ordem...")
    
    # Enviar ordem
    print("\n6️⃣  Enviando ordem maker...")
    try:
        result = client.create_order(
            token,
            lado,
            preco,
            tamanho,
            neg_risk=False
        )
        
        if result:
            order_id = result.get('orderID', 'N/A')
            print(f"\n✅ ORDEM CRIADA COM SUCESSO!")
            print(f"   Order ID: {order_id}")
            print(f"   Token: {token}")
            print(f"   Lado: {lado}")
            print(f"   Preço: ${preco:.4f}")
            print(f"   Tamanho: {tamanho} shares")
            print(f"\n💡 Verifique a ordem no site do Polymarket!")
            return True
        else:
            print("\n❌ Falha ao criar ordem. Resultado vazio.")
            return False
            
    except Exception as e:
        print(f"\n❌ Erro ao criar ordem: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    sucesso = testar_ordem_maker()
    sys.exit(0 if sucesso else 1)

