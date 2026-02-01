#!/usr/bin/env python3
"""
Adiciona alguns mercados de exemplo para começar rapidamente
Você pode editar manualmente depois no Google Sheets
"""
from poly_utils.google_utils import get_spreadsheet
import pandas as pd

try:
    print("🔄 Conectando ao Google Sheets...")
    spreadsheet = get_spreadsheet()
    
    # Adicionar mercados de exemplo na aba "Selected Markets"
    selected_sheet = spreadsheet.worksheet("Selected Markets")
    
    # Mercados de exemplo (você pode editar depois)
    mercados_exemplo = [
        {
            'question': 'Will Bitcoin close above $50,000 on February 15, 2026?',
            'max_size': 100,
            'trade_size': 50,
            'param_type': 'default',
            'comments': 'Exemplo - Crypto market'
        },
        {
            'question': 'Will Tesla stock close above $250 on February 10, 2026?',
            'max_size': 80,
            'trade_size': 40,
            'param_type': 'default',
            'comments': 'Exemplo - Stock market'
        }
    ]
    
    # Converter para DataFrame
    df = pd.DataFrame(mercados_exemplo)
    
    # Adicionar à planilha
    from gspread_dataframe import set_with_dataframe
    set_with_dataframe(selected_sheet, df, include_index=False, resize=True)
    
    print(f"✅ {len(mercados_exemplo)} mercado(s) de exemplo adicionado(s)")
    print("\n⚠️  ATENÇÃO: Estes são mercados de EXEMPLO!")
    print("   Para usar mercados reais:")
    print("   1. Execute: python data_updater/data_updater.py (pode demorar)")
    print("   2. Depois: python update_selected_markets.py")
    print("   3. Ou edite manualmente a aba 'Selected Markets' no Google Sheets")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

