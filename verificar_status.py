#!/usr/bin/env python3
"""
Verifica o status completo do bot
"""
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("📊 STATUS DO BOT POLYMARKET")
print("="*60)
print()

# 1. Verificar se está rodando
print("1. Processo do Bot:")
result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
if 'python.*main.py' in result.stdout or 'main.py' in result.stdout:
    lines = [l for l in result.stdout.split('\n') if 'main.py' in l and 'grep' not in l]
    if lines:
        print("   ✅ Bot está RODANDO")
        for line in lines:
            print(f"   {line[:80]}")
    else:
        print("   ❌ Bot NÃO está rodando")
else:
    print("   ❌ Bot NÃO está rodando")

print()

# 2. Verificar configuração
print("2. Configuração:")
pk = os.getenv("PK")
browser = os.getenv("BROWSER_ADDRESS")
spreadsheet = os.getenv("SPREADSHEET_URL")

if pk and pk != "your_private_key_here":
    print("   ✅ PK configurado")
else:
    print("   ❌ PK não configurado")

if browser and browser != "your_wallet_address_here":
    print("   ✅ BROWSER_ADDRESS configurado")
else:
    print("   ❌ BROWSER_ADDRESS não configurado")

if spreadsheet and spreadsheet != "your_spreadsheet_url_here":
    print("   ✅ SPREADSHEET_URL configurado")
else:
    print("   ❌ SPREADSHEET_URL não configurado")

print()

# 3. Verificar Google Sheets
print("3. Google Sheets:")
try:
    from poly_utils.google_utils import get_spreadsheet
    s = get_spreadsheet()
    print(f"   ✅ Conectado: {s.title}")
    
    # Verificar mercados selecionados
    try:
        ws = s.worksheet("Selected Markets")
        data = ws.get_all_records()
        print(f"   ✅ {len(data)} mercado(s) selecionado(s)")
        if len(data) > 0:
            print("   Mercados:")
            for i, r in enumerate(data[:5], 1):
                q = r.get('question', 'N/A')
                print(f"      {i}. {q[:60]}...")
    except Exception as e:
        print(f"   ⚠️  Erro ao ler mercados: {e}")
        
except Exception as e:
    print(f"   ❌ Erro ao conectar: {e}")

print()

# 4. Verificar logs
print("4. Logs:")
if os.path.exists("main.log"):
    size = os.path.getsize("main.log")
    if size > 0:
        print(f"   ✅ main.log existe ({size} bytes)")
        # Ler últimas linhas
        with open("main.log", "r") as f:
            lines = f.readlines()
            if lines:
                print("   Últimas linhas:")
                for line in lines[-3:]:
                    print(f"      {line.strip()[:70]}")
    else:
        print("   ⚠️  main.log existe mas está vazio")
else:
    print("   ⚠️  main.log não encontrado (bot nunca foi iniciado)")

print()
print("="*60)
print("💡 Para iniciar o bot: python main.py")
print("="*60)

