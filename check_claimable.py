#!/usr/bin/env python3
"""
Script para verificar saldo claimable no Polymarket

Verifica posições vencedoras que podem ser resgatadas sem executar transações.
"""

import os
import sys
from dotenv import load_dotenv
from eth_utils import to_checksum_address
from claimer_core.position_fetcher import fetchPositions, create_session
from claimer_core.claim_filter import filterClaimables
from claimer_core.logger_config import setup_logger

# Load environment variables
load_dotenv()

# Initialize logger
logger = setup_logger("check_claimable", "check_claimable.log")

def main():
    """Verifica posições claimables."""
    try:
        logger.info("=" * 80)
        logger.info("VERIFICANDO SALDO CLAIMABLE NO POLYMARKET")
        logger.info("=" * 80)
        
        # Get wallet address
        wallet_address = os.getenv('CLAIMER_WALLET_ADDRESS') or os.getenv('BROWSER_ADDRESS')
        if not wallet_address:
            logger.error("❌ CLAIMER_WALLET_ADDRESS ou BROWSER_ADDRESS deve estar configurado no .env")
            sys.exit(1)
        
        wallet_address = to_checksum_address(wallet_address)
        logger.info(f"Wallet: {wallet_address}")
        
        # Fetch positions
        logger.info("\nBuscando posições na API do Polymarket...")
        session = create_session()
        positions = fetchPositions(wallet_address, session)
        
        logger.info(f"\n✓ Total de posições encontradas: {len(positions)}")
        
        if len(positions) == 0:
            logger.info("\n❌ Nenhuma posição encontrada.")
            return
        
        # Show raw data for debugging (first position only)
        if len(positions) > 0:
            logger.info("\n" + "-" * 80)
            logger.info("DEBUG: Exemplo de dados da API (primeira posição):")
            logger.info("-" * 80)
            first_pos = positions[0]
            for key, value in first_pos.items():
                # Truncate long values
                if isinstance(value, str) and len(str(value)) > 100:
                    value = str(value)[:100] + "..."
                logger.info(f"  {key}: {value}")
            logger.info("-" * 80)
        
        # Filter claimables with debug mode
        logger.info("\nFiltrando posições claimables...")
        claimables = filterClaimables(positions, debug=True)
        
        logger.info(f"\n{'=' * 80}")
        logger.info("RESULTADO")
        logger.info("=" * 80)
        
        if len(claimables) == 0:
            logger.info("\n❌ Nenhuma posição claimable encontrada.")
            logger.info("\nIsso pode significar:")
            logger.info("  - Mercados ainda não foram resolvidos")
            logger.info("  - Posições já foram resgatadas")
            logger.info("  - Você não tem posições vencedoras")
            return
        
        # Calculate totals
        total_redeemable = 0
        total_positions = len(claimables)
        
        logger.info(f"\n✓ Encontradas {total_positions} posição(ões) claimable(is):\n")
        
        # Display claimables
        for idx, claimable in enumerate(claimables, 1):
            market = claimable.get('market') or claimable.get('title', 'Unknown')
            outcome = claimable.get('outcome', 'Unknown')
            
            # Get redeemable amount from currentValue or calculate from size * price
            redeemable = claimable.get('currentValue') or 0
            if not redeemable or float(redeemable) == 0:
                size = claimable.get('size', 0)
                cur_price = claimable.get('curPrice', 0)
                if size and cur_price:
                    redeemable = float(size) * float(cur_price)
            
            redeemable = float(redeemable) if redeemable else 0
            asset = claimable.get('asset') or claimable.get('tokenId', 'Unknown')
            
            total_redeemable += redeemable
            
            logger.info(f"[{idx}] {market}")
            logger.info(f"     Outcome: {outcome}")
            logger.info(f"     Redeemable: ${redeemable:.2f}")
            logger.info(f"     Size: {claimable.get('size', 0)}")
            logger.info(f"     Current Price: {claimable.get('curPrice', 0)}")
            logger.info(f"     Asset: {str(asset)[:50]}...")
            logger.info("")
        
        # Summary
        logger.info("=" * 80)
        logger.info("RESUMO")
        logger.info("=" * 80)
        logger.info(f"Total de posições claimables: {total_positions}")
        logger.info(f"Total a resgatar: ${total_redeemable:.2f}")
        logger.info("")
        
        if total_redeemable > 0:
            logger.info("💡 Para resgatar, execute:")
            logger.info("   python auto_claim.py --dry-run  # Simular primeiro")
            logger.info("   python auto_claim.py            # Executar")
        
        logger.info("=" * 80)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Erro: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

