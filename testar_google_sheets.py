#!/usr/bin/env python3
"""
Script de teste para verificar a configuração do Google Sheets
"""
import os
from dotenv import load_dotenv

load_dotenv()

def testar_configuracao():
    print("🔍 Verificando configuração do Google Sheets...\n")
    
    # 1. Verificar SPREADSHEET_URL
    spreadsheet_url = os.getenv("SPREADSHEET_URL")
    if not spreadsheet_url:
        print("❌ ERRO: SPREADSHEET_URL não está configurado no .env")
        print("   Edite o arquivo .env e adicione: SPREADSHEET_URL=sua_url_aqui")
        return False
    elif "your_spreadsheet_url_here" in spreadsheet_url:
        print("❌ ERRO: SPREADSHEET_URL ainda está com valor padrão")
        print("   Edite o arquivo .env e substitua pelo URL real da sua planilha")
        return False
    else:
        print(f"✅ SPREADSHEET_URL configurado: {spreadsheet_url[:50]}...")
    
    # 2. Verificar credentials.json (procurar em múltiplos locais)
    creds_file = None
    for path in ['secrets/credentials.json', 'credentials.json', '../secrets/credentials.json', '../credentials.json']:
        if os.path.exists(path):
            creds_file = path
            break
    
    if not creds_file:
        print("❌ ERRO: Arquivo credentials.json não encontrado")
        print("   Procurando em: secrets/credentials.json, credentials.json")
        print("   Baixe o arquivo do Google Cloud Console e coloque em secrets/credentials.json")
        return False
    else:
        print(f"✅ Arquivo encontrado: {creds_file}")
    
    # 3. Tentar conectar
    try:
        from poly_utils.google_utils import get_spreadsheet
        print("\n🔄 Tentando conectar ao Google Sheets...")
        spreadsheet = get_spreadsheet()
        print("✅ Conexão estabelecida com sucesso!")
        
        # 4. Listar abas disponíveis
        try:
            worksheets = spreadsheet.worksheets()
            print(f"\n📊 Abas encontradas na planilha ({len(worksheets)}):")
            for ws in worksheets:
                print(f"   - {ws.title}")
        except Exception as e:
            print(f"⚠️  Não foi possível listar abas: {e}")
        
        return True
        
    except FileNotFoundError as e:
        print(f"❌ ERRO: {e}")
        print("   Verifique se o arquivo credentials.json está em secrets/credentials.json ou no diretório raiz")
        return False
    except ValueError as e:
        print(f"❌ ERRO: {e}")
        return False
    except Exception as e:
        print(f"❌ ERRO ao conectar: {e}")
        print("\nPossíveis causas:")
        print("   1. A planilha não foi compartilhada com o service account")
        print("   2. O service account não tem permissão de Editor")
        print("   3. As APIs do Google Sheets/Drive não estão ativadas")
        return False

if __name__ == "__main__":
    sucesso = testar_configuracao()
    if sucesso:
        print("\n🎉 Tudo configurado corretamente!")
    else:
        print("\n⚠️  Corrija os erros acima antes de continuar")
        exit(1)

