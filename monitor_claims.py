#!/usr/bin/env python3
"""
Monitor de Claims - Polymarket

Monitora posições claimables e envia notificações quando há claims disponíveis.
Pode rodar em background ou via cron.

Usage:
    python monitor_claims.py [--interval SECONDS] [--once] [--discord-webhook URL]
"""

import os
import sys
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv
from eth_utils import to_checksum_address
from claimer_core.position_fetcher import fetchPositions, create_session
from claimer_core.claim_filter import filterClaimables
from claimer_core.logger_config import setup_logger

# Load environment variables
load_dotenv()

# Initialize logger
logger = setup_logger("monitor_claims", "monitor_claims.log")

def send_discord_notification(webhook_url: str, message: str):
    """Envia notificação para Discord webhook."""
    try:
        import requests
        payload = {
            "content": message,
            "username": "Polymarket Claim Monitor"
        }
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("✓ Notificação enviada para Discord")
    except Exception as e:
        logger.warning(f"Falha ao enviar notificação Discord: {e}")

def check_claims(webhook_url: str = None, previous_count: int = 0, previous_total: float = 0.0):
    """
    Verifica claims disponíveis e envia notificações se houver mudanças.
    
    Returns:
        (count, total_amount) - Número de claims e valor total
    """
    try:
        wallet_address = os.getenv('CLAIMER_WALLET_ADDRESS') or os.getenv('BROWSER_ADDRESS')
        if not wallet_address:
            logger.error("❌ CLAIMER_WALLET_ADDRESS ou BROWSER_ADDRESS deve estar configurado")
            return (0, 0.0)
        
        wallet_address = to_checksum_address(wallet_address)
        
        # Fetch positions
        session = create_session()
        positions = fetchPositions(wallet_address, session)
        
        # Filter claimables
        claimables = filterClaimables(positions, debug=False)
        
        # Calculate total
        total_amount = 0.0
        for claimable in claimables:
            redeemable = claimable.get('currentValue') or 0
            if not redeemable or float(redeemable) == 0:
                size = claimable.get('size', 0)
                cur_price = claimable.get('curPrice', 0)
                if size and cur_price and float(cur_price) > 0:
                    redeemable = float(size) * float(cur_price)
            total_amount += float(redeemable) if redeemable else 0
        
        count = len(claimables)
        
        # Check if there are new claims or amount changed
        if count > previous_count or (count > 0 and abs(total_amount - previous_total) > 0.01):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            message = f"🎯 **NOVOS CLAIMS DISPONÍVEIS!**\n\n"
            message += f"💰 **Total a resgatar: ${total_amount:.2f}**\n"
            message += f"📊 **Posições claimables: {count}**\n\n"
            
            if count > 0:
                message += "**Detalhes:**\n"
                for idx, claimable in enumerate(claimables[:5], 1):  # Limitar a 5 para não ficar muito longo
                    market = claimable.get('title') or claimable.get('market', 'Unknown')
                    outcome = claimable.get('outcome', 'Unknown')
                    redeemable = claimable.get('currentValue') or 0
                    if not redeemable or float(redeemable) == 0:
                        size = claimable.get('size', 0)
                        cur_price = claimable.get('curPrice', 0)
                        if size and cur_price and float(cur_price) > 0:
                            redeemable = float(size) * float(cur_price)
                    redeemable = float(redeemable) if redeemable else 0
                    message += f"{idx}. {market[:50]}\n"
                    message += f"   Outcome: {outcome} | ${redeemable:.2f}\n"
                
                if count > 5:
                    message += f"\n... e mais {count - 5} posição(ões)\n"
            
            message += f"\n⏰ {timestamp}\n"
            message += f"🔗 Resgatar: https://polymarket.com/portfolio"
            
            # Log to console
            logger.info("=" * 80)
            logger.info("🎯 NOVOS CLAIMS DISPONÍVEIS!")
            logger.info("=" * 80)
            logger.info(f"💰 Total a resgatar: ${total_amount:.2f}")
            logger.info(f"📊 Posições claimables: {count}")
            logger.info("")
            for idx, claimable in enumerate(claimables, 1):
                market = claimable.get('title') or claimable.get('market', 'Unknown')
                outcome = claimable.get('outcome', 'Unknown')
                redeemable = claimable.get('currentValue') or 0
                if not redeemable or float(redeemable) == 0:
                    size = claimable.get('size', 0)
                    cur_price = claimable.get('curPrice', 0)
                    if size and cur_price and float(cur_price) > 0:
                        redeemable = float(size) * float(cur_price)
                redeemable = float(redeemable) if redeemable else 0
                logger.info(f"  [{idx}] {market}")
                logger.info(f"       Outcome: {outcome} | ${redeemable:.2f}")
            logger.info("")
            logger.info(f"🔗 Resgatar em: https://polymarket.com/portfolio")
            logger.info("=" * 80)
            
            # Send Discord notification if webhook provided
            if webhook_url:
                send_discord_notification(webhook_url, message)
        
        elif count > 0:
            # Claims still available but no change
            logger.debug(f"Claims ainda disponíveis: {count} posições, ${total_amount:.2f} total")
        else:
            logger.debug("Nenhum claim disponível no momento")
        
        return (count, total_amount)
    
    except Exception as e:
        logger.error(f"❌ Erro ao verificar claims: {e}", exc_info=True)
        return (0, 0.0)

def main():
    parser = argparse.ArgumentParser(
        description="Monitora claims disponíveis no Polymarket"
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Intervalo entre verificações em segundos (padrão: 300 = 5 minutos)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Executa apenas uma vez e sai (útil para cron)'
    )
    parser.add_argument(
        '--discord-webhook',
        type=str,
        help='URL do webhook do Discord para notificações'
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("POLYMARKET CLAIM MONITOR")
    logger.info("=" * 80)
    logger.info(f"Intervalo: {args.interval} segundos")
    logger.info(f"Modo: {'Uma execução' if args.once else 'Contínuo'}")
    if args.discord_webhook:
        logger.info("✓ Notificações Discord habilitadas")
    logger.info("=" * 80)
    logger.info("")
    
    previous_count = 0
    previous_total = 0.0
    
    try:
        while True:
            count, total = check_claims(
                webhook_url=args.discord_webhook,
                previous_count=previous_count,
                previous_total=previous_total
            )
            
            previous_count = count
            previous_total = total
            
            if args.once:
                break
            
            # Wait before next check
            logger.info(f"⏳ Próxima verificação em {args.interval} segundos...")
            time.sleep(args.interval)
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  Monitor interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

