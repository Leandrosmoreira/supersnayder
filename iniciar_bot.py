#!/usr/bin/env python3
"""
Script para verificar configuração e iniciar o bot
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def verificar_configuracao():
    """Verifica se tudo está configurado corretamente"""
    print("🔍 Verificando configuração...\n")
    
    erros = []
    avisos = []
    
    # 1. Verificar .env
    pk = os.getenv("PK")
    browser_address = os.getenv("BROWSER_ADDRESS")
    spreadsheet_url = os.getenv("SPREADSHEET_URL")
    
    if not pk or pk == "your_private_key_here":
        erros.append("❌ PK não configurado no .env")
    else:
        print(f"✅ PK configurado: {pk[:10]}...")
    
    if not browser_address or browser_address == "your_wallet_address_here":
        erros.append("❌ BROWSER_ADDRESS não configurado no .env")
    else:
        print(f"✅ BROWSER_ADDRESS configurado: {browser_address[:10]}...")
    
    if not spreadsheet_url or spreadsheet_url == "your_spreadsheet_url_here":
        erros.append("❌ SPREADSHEET_URL não configurado no .env")
    else:
        print(f"✅ SPREADSHEET_URL configurado")
    
    # 2. Verificar credentials.json
    if not os.path.exists("secrets/credentials.json") and not os.path.exists("credentials.json"):
        erros.append("❌ credentials.json não encontrado")
    else:
        print("✅ credentials.json encontrado")
    
    # 3. Verificar Google Sheets
    try:
        from poly_utils.google_utils import get_spreadsheet
        spreadsheet = get_spreadsheet()
        print(f"✅ Conectado ao Google Sheets: {spreadsheet.title}")
        
        # Verificar abas necessárias
        worksheets = [ws.title for ws in spreadsheet.worksheets()]
        abas_necessarias = ["Selected Markets", "Hyperparameters"]
        
        for aba in abas_necessarias:
            if aba in worksheets:
                print(f"✅ Aba '{aba}' encontrada")
            else:
                avisos.append(f"⚠️  Aba '{aba}' não encontrada (será criada automaticamente)")
        
        # Verificar se há mercados selecionados
        try:
            selected_sheet = spreadsheet.worksheet("Selected Markets")
            selected_data = selected_sheet.get_all_records()
            if len(selected_data) > 0:
                print(f"✅ {len(selected_data)} mercado(s) selecionado(s)")
            else:
                avisos.append("⚠️  Nenhum mercado selecionado. Execute: python update_selected_markets.py")
        except:
            avisos.append("⚠️  Aba 'Selected Markets' vazia. Execute: python update_selected_markets.py")
            
    except Exception as e:
        avisos.append(f"⚠️  Erro ao conectar Google Sheets: {e}")
    
    # 4. Resumo
    print("\n" + "="*60)
    if erros:
        print("❌ ERROS ENCONTRADOS:")
        for erro in erros:
            print(f"   {erro}")
        print("\n⚠️  Corrija os erros antes de iniciar o bot!")
        return False
    else:
        print("✅ Configuração básica OK!")
        if avisos:
            print("\n⚠️  AVISOS:")
            for aviso in avisos:
                print(f"   {aviso}")
        return True

if __name__ == "__main__":
    print("="*60)
    print("🚀 VERIFICAÇÃO DE CONFIGURAÇÃO DO BOT")
    print("="*60)
    print()
    
    ok = verificar_configuracao()
    
    if ok:
        print("\n" + "="*60)
        print("✅ Tudo pronto! Você pode iniciar o bot com:")
        print("   python main.py")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ Corrija os erros acima antes de iniciar")
        print("="*60)
        sys.exit(1)

