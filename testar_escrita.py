#!/usr/bin/env python3
"""
Script para testar escrita na planilha do Google Sheets
"""
from poly_utils.google_utils import get_spreadsheet

try:
    print("🔄 Conectando à planilha...")
    spreadsheet = get_spreadsheet()
    print(f"✅ Conectado à planilha: {spreadsheet.title}\n")
    
    # Pegar a primeira aba (ou criar uma nova se necessário)
    try:
        worksheet = spreadsheet.worksheet("Página1")
    except:
        # Se não existir, pega a primeira aba disponível
        worksheets = spreadsheet.worksheets()
        if worksheets:
            worksheet = worksheets[0]
        else:
            worksheet = spreadsheet.add_worksheet(title="Página1", rows=100, cols=20)
    
    print(f"📝 Usando aba: {worksheet.title}")
    
    # Escrever o nome na célula A1
    print("✍️  Escrevendo 'Leandro' na célula A1...")
    worksheet.update(range_name='A1', values=[['Leandro']])
    print("✅ Nome escrito com sucesso!\n")
    
    # Ler de volta para confirmar
    valor = worksheet.acell('A1').value
    print(f"📖 Valor lido da célula A1: {valor}")
    
    if valor == "Leandro":
        print("\n🎉 Teste de escrita bem-sucedido! A planilha está funcionando corretamente.")
    else:
        print(f"\n⚠️  Atenção: Esperado 'Leandro', mas leu '{valor}'")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

