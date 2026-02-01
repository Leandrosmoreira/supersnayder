#!/usr/bin/env python3
"""
Script para verificar se os mercados inscritos têm atividade (order book, trades, etc.)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from poly_data.polymarket_client import PolymarketClient
from poly_data.utils import get_sheet_df
import pandas as pd

def verificar_atividade_mercados():
    """Verifica a atividade dos mercados inscritos."""
    
    print("=" * 70)
    print("🔍 VERIFICAÇÃO DE ATIVIDADE DOS MERCADOS")
    print("=" * 70)
    
    # Inicializar cliente
    print("\n1️⃣  Inicializando cliente...")
    client = PolymarketClient()
    
    # Carregar mercados
    print("\n2️⃣  Carregando mercados da planilha...")
    df_selected, params = get_sheet_df()
    
    if df_selected.empty:
        print("❌ Nenhum mercado selecionado!")
        return
    
    print(f"✅ {len(df_selected)} mercados selecionados\n")
    
    # Verificar cada mercado
    mercados_com_atividade = 0
    mercados_sem_atividade = 0
    
    for idx, row in df_selected.iterrows():
        question = row.get('question', 'Unknown')
        token1 = row.get('token1', '')
        token2 = row.get('token2', '')
        condition_id = row.get('condition_id', '')
        
        print(f"\n📊 Mercado: {question[:60]}...")
        print(f"   Token1: {str(token1)[:20]}...")
        print(f"   Token2: {str(token2)[:20]}...")
        print(f"   Condition ID: {str(condition_id)[:20]}...")
        
        # Verificar order book do token1
        try:
            order_book_result = client.get_order_book(token1)
            # get_order_book retorna uma tupla (bids_df, asks_df)
            if order_book_result and len(order_book_result) == 2:
                bids_df, asks_df = order_book_result
                bids = bids_df.to_dict('records') if not bids_df.empty else []
                asks = asks_df.to_dict('records') if not asks_df.empty else []
                best_bid = float(bids[0]['price']) if bids and len(bids) > 0 else 0
                best_ask = float(asks[0]['price']) if asks and len(asks) > 0 else 0
                
                print(f"   ✅ Order Book Token1:")
                print(f"      Bids: {len(bids)}, Asks: {len(asks)}")
                print(f"      Best Bid: ${best_bid:.4f}, Best Ask: ${best_ask:.4f}")
                print(f"      Spread: ${best_ask - best_bid:.4f}")
                
                if len(bids) > 0 and len(asks) > 0:
                    mercados_com_atividade += 1
                    print(f"   ✅ MERCADO ATIVO")
                else:
                    mercados_sem_atividade += 1
                    print(f"   ⚠️  MERCADO SEM LIQUIDEZ (sem bids ou asks)")
            else:
                mercados_sem_atividade += 1
                print(f"   ❌ Não foi possível obter order book")
        except Exception as e:
            mercados_sem_atividade += 1
            print(f"   ❌ Erro ao verificar order book: {e}")
    
    # Resumo
    print("\n" + "=" * 70)
    print("📊 RESUMO")
    print("=" * 70)
    print(f"✅ Mercados com atividade: {mercados_com_atividade}")
    print(f"⚠️  Mercados sem atividade: {mercados_sem_atividade}")
    print(f"📈 Total: {len(df_selected)}")
    
    if mercados_sem_atividade > 0:
        print(f"\n⚠️  ATENÇÃO: {mercados_sem_atividade} mercado(s) sem atividade.")
        print("   Esses mercados não receberão dados do WebSocket.")
        print("   Considere substituí-los por mercados mais ativos.")

if __name__ == "__main__":
    verificar_atividade_mercados()

