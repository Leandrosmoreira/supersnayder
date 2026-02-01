#!/usr/bin/env python3
"""
Script para cancelar todas as ordens maker ativas
"""
import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from poly_data.polymarket_client import PolymarketClient

load_dotenv()

def cancelar_todas_ordens():
    """Cancela todas as ordens maker ativas."""
    print("=" * 80)
    print("  🗑️  CANCELAR TODAS AS ORDENS MAKER")
    print("=" * 80)
    
    # Inicializar cliente
    print("\n1️⃣  Inicializando cliente Polymarket...")
    try:
        client = PolymarketClient()
        print("   ✅ Cliente inicializado com sucesso")
    except Exception as e:
        print(f"   ❌ Erro ao inicializar cliente: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Buscar ordens ativas
    print("\n2️⃣  Buscando ordens ativas...")
    try:
        orders = client.get_all_orders()
        print(f"   ✅ Encontradas {len(orders)} ordens ativas")
        
        if len(orders) == 0:
            print("   ℹ️  Nenhuma ordem ativa encontrada")
            return True
        
        # Mostrar ordens
        print("\n   📋 Ordens encontradas:")
        for idx, (_, order) in enumerate(orders.head(10).iterrows(), 1):  # Mostrar até 10
            order_id = str(order.get('id', 'N/A'))
            asset_id = str(order.get('asset_id', 'N/A'))
            side = str(order.get('side', 'N/A'))
            price = order.get('price', 'N/A')
            size = order.get('original_size', 'N/A')
            status = str(order.get('status', 'N/A'))
            print(f"      {idx}. Order ID: {order_id[:20]}... | Asset: {asset_id[:20]}... | {side} @ ${price} x {size} ({status})")
        
        if len(orders) > 10:
            print(f"      ... e mais {len(orders) - 10} ordens")
        
    except Exception as e:
        print(f"   ❌ Erro ao buscar ordens: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Cancelar todas as ordens
    print("\n3️⃣  Cancelando todas as ordens...")
    try:
        # Obter todos os asset_ids únicos
        asset_ids_unicos = orders['asset_id'].unique()
        print(f"   📊 Cancelando ordens de {len(asset_ids_unicos)} assets diferentes...")
        
        canceladas = 0
        erros = 0
        
        for asset_id in asset_ids_unicos:
            try:
                print(f"   🗑️  Cancelando ordens do asset: {str(asset_id)[:30]}...")
                # Tentar cancel_all_asset primeiro
                result = client.cancel_all_asset(str(asset_id))
                # Mesmo que retorne None/False, pode ter cancelado
                canceladas += 1
                print(f"      ✅ Comando de cancelamento enviado para asset {str(asset_id)[:20]}...")
            except Exception as e:
                erros += 1
                print(f"      ❌ Erro ao cancelar asset {str(asset_id)[:20]}...: {e}")
        
        # Também tentar cancel_all_market para cada market único
        markets_unicos = orders['market'].unique()
        print(f"\n   📊 Cancelando ordens por market ({len(markets_unicos)} markets)...")
        for market in markets_unicos:
            try:
                print(f"   🗑️  Cancelando ordens do market: {str(market)[:30]}...")
                result = client.cancel_all_market(str(market))
                print(f"      ✅ Comando de cancelamento enviado para market {str(market)[:20]}...")
            except Exception as e:
                print(f"      ⚠️  Erro ao cancelar market {str(market)[:20]}...: {e}")
        
        print(f"\n   ✅ Cancelamento concluído:")
        print(f"      Canceladas: {canceladas} tokens")
        print(f"      Erros: {erros} tokens")
        
        # Verificar se ainda há ordens
        print("\n4️⃣  Verificando ordens restantes...")
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
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao cancelar ordens: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = cancelar_todas_ordens()
    if success:
        print("\n" + "=" * 80)
        print("  ✅ PROCESSO CONCLUÍDO")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("  ❌ PROCESSO FALHOU")
        print("=" * 80)
        sys.exit(1)

