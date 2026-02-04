#!/usr/bin/env python3
"""
Helper script para Magic Link users - mostra como fazer claim manualmente
ou prepara dados da transação para execução via MetaMask/outra carteira
"""

import os
from dotenv import load_dotenv
from claimer_core.position_fetcher import fetchPositions, create_session
from claimer_core.claim_filter import filterClaimables
from claimer_core.tx_builder import buildRedeemTx
from web3 import Web3
from eth_utils import to_checksum_address

load_dotenv()

def main():
    print("=" * 80)
    print("MAGIC LINK CLAIM HELPER")
    print("=" * 80)
    print()
    
    wallet_address = os.getenv('CLAIMER_WALLET_ADDRESS') or os.getenv('BROWSER_ADDRESS')
    if not wallet_address:
        print("❌ CLAIMER_WALLET_ADDRESS ou BROWSER_ADDRESS deve estar configurado")
        return
    
    wallet_address = to_checksum_address(wallet_address)
    print(f"Wallet: {wallet_address}")
    print()
    
    # Fetch positions
    print("Buscando posições...")
    session = create_session()
    positions = fetchPositions(wallet_address, session)
    print(f"✓ Encontradas {len(positions)} posições")
    print()
    
    # Filter claimables
    claimables = filterClaimables(positions)
    print(f"✓ {len(claimables)} posições claimables")
    print()
    
    if len(claimables) == 0:
        print("❌ Nenhuma posição claimable encontrada")
        return
    
    # Build transactions
    web3 = Web3(Web3.HTTPProvider(os.getenv('POLYGON_RPC_URL', 'https://polygon-rpc.com')))
    
    print("=" * 80)
    print("OPÇÕES PARA FAZER CLAIM:")
    print("=" * 80)
    print()
    print("OPÇÃO 1: Fazer claim manualmente na UI do Polymarket")
    print("  1. Acesse: https://polymarket.com/portfolio")
    print("  2. Clique no botão 'Claim' quando aparecer")
    print("  3. Confirme a transação")
    print()
    print("OPÇÃO 2: Usar MetaMask ou outra carteira")
    print("  Se você tiver a chave privada do proxy wallet Magic Link,")
    print("  pode usar os dados abaixo para executar via web3:")
    print()
    
    for idx, claimable in enumerate(claimables, 1):
        print(f"[{idx}] {claimable.get('title', 'Unknown Market')}")
        print(f"     Outcome: {claimable.get('outcome', 'Unknown')}")
        print(f"     Redeemable: ${float(claimable.get('currentValue', 0)):.2f}")
        print()
        
        try:
            tx_data = buildRedeemTx(claimable, web3)
            print("  Dados da transação:")
            print(f"    To: {tx_data['to']}")
            print(f"    Data: {tx_data['data'].hex() if hasattr(tx_data['data'], 'hex') else tx_data['data']}")
            print()
        except Exception as e:
            print(f"  ❌ Erro ao construir transação: {e}")
            print()
    
    print("=" * 80)
    print("NOTA: Com Magic Link, o proxy wallet é controlado pela Magic.")
    print("Para automatizar, você precisa:")
    print("  1. Exportar a chave privada do proxy wallet (se possível)")
    print("  2. Ou usar a API da Magic para assinar transações")
    print("  3. Ou fazer manualmente na UI")
    print("=" * 80)

if __name__ == "__main__":
    main()

