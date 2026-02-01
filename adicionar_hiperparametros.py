#!/usr/bin/env python3
"""
Script para adicionar hiperparâmetros à planilha do Google Sheets.
"""
import os
import pandas as pd
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

# Carregar variáveis de ambiente
load_dotenv()

# Configurar credenciais do Google Sheets
creds_file = 'secrets/credentials.json' if os.path.exists('secrets/credentials.json') else 'credentials.json'
if not os.path.exists(creds_file):
    print(f"❌ Arquivo {creds_file} não encontrado!")
    exit(1)

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(creds_file, scopes=scope)
client = gspread.authorize(creds)

# Obter URL da planilha
spreadsheet_url = os.getenv('SPREADSHEET_URL')
if not spreadsheet_url:
    print("❌ SPREADSHEET_URL não configurado no .env!")
    exit(1)

print(f"📊 Conectando à planilha: {spreadsheet_url}")
spreadsheet = client.open_by_url(spreadsheet_url)

# Ler hiperparâmetros recomendados
print("📖 Lendo hiperparâmetros recomendados...")
df_recommended = pd.read_csv('recommended_hyperparameters.csv')
print(f"   Encontrados {len(df_recommended)} hiperparâmetros")

# Verificar se a aba "Hyperparameters" existe
try:
    worksheet = spreadsheet.worksheet("Hyperparameters")
    print("✓ Aba 'Hyperparameters' encontrada")
except gspread.exceptions.WorksheetNotFound:
    print("⚠️  Aba 'Hyperparameters' não encontrada. Criando...")
    worksheet = spreadsheet.add_worksheet(title="Hyperparameters", rows=100, cols=10)

# Limpar aba existente (opcional - comentar se quiser manter dados existentes)
print("🧹 Limpando aba existente...")
worksheet.clear()

# Adicionar cabeçalhos
print("📝 Adicionando cabeçalhos...")
worksheet.append_row(['type', 'param', 'value'])

# Adicionar dados
print("📝 Adicionando hiperparâmetros...")
for _, row in df_recommended.iterrows():
    worksheet.append_row([row['type'], row['param'], row['value']])
    print(f"   ✓ {row['type']}.{row['param']} = {row['value']}")

print("\n✅ Hiperparâmetros adicionados com sucesso!")
print("\n💡 Tipos disponíveis:")
print("   - default: Configuração padrão")
print("   - conservative: Mais conservador (menos risco)")
print("   - aggressive: Mais agressivo (mais risco)")
print("   - very_aggressive: Muito agressivo (muito risco)")
print("\n⚠️  IMPORTANTE: Configure o campo 'param_type' na aba 'Selected Markets'")
print("   para usar um dos tipos acima (ex: 'default', 'conservative', etc.)")

