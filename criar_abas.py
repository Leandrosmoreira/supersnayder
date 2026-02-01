#!/usr/bin/env python3
"""
Cria as abas necessárias no Google Sheets
"""
from poly_utils.google_utils import get_spreadsheet

try:
    print("🔄 Conectando ao Google Sheets...")
    spreadsheet = get_spreadsheet()
    print(f"✅ Conectado: {spreadsheet.title}\n")
    
    # Lista de abas necessárias com headers
    abas_necessarias = {
        "Selected Markets": ["question", "max_size", "trade_size", "param_type", "comments"],
        "Hyperparameters": ["type", "param", "value"],
        "All Markets": [],  # Será preenchida pelo data_updater
        "Volatility Markets": []  # Será preenchida pelo data_updater
    }
    
    # Verificar abas existentes
    abas_existentes = [ws.title for ws in spreadsheet.worksheets()]
    print(f"Abas existentes: {', '.join(abas_existentes)}\n")
    
    # Criar abas que não existem
    for aba_nome, headers in abas_necessarias.items():
        if aba_nome in abas_existentes:
            print(f"✅ Aba '{aba_nome}' já existe")
        else:
            try:
                worksheet = spreadsheet.add_worksheet(title=aba_nome, rows=1000, cols=20)
                print(f"✅ Aba '{aba_nome}' criada")
                
                # Adicionar headers se especificados
                if headers:
                    worksheet.update('A1', [headers])
                    print(f"   Headers adicionados: {', '.join(headers)}")
            except Exception as e:
                print(f"⚠️  Erro ao criar aba '{aba_nome}': {e}")
    
    print("\n" + "="*60)
    print("✅ Abas criadas com sucesso!")
    print("="*60)
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

