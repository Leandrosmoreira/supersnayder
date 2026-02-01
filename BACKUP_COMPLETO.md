# 💾 Backup Completo Criado

## ✅ Backup Realizado

**Data:** $(date +%Y-%m-%d)
**Tipo:** Código completo (sem arquivos sensíveis)
**Local:** `/root/backups/polymarket-codigo-*.tar.gz`

## 📦 O que está incluído no backup:

✅ Todo o código Python
✅ Scripts de configuração
✅ Documentação (.md)
✅ Configurações (exceto .env)
✅ Estrutura de pastas
✅ Scripts de teste

## ❌ O que NÃO está incluído (por segurança):

❌ `.env` (chaves privadas)
❌ `secrets/` (credenciais Google)
❌ `*.log` (logs)
❌ `venv/` (ambiente virtual)
❌ `__pycache__/` (cache Python)

## 🔄 Como restaurar:

```bash
# 1. Extrair o backup
cd /root
tar -xzf backups/polymarket-codigo-YYYYMMDD_HHMMSS.tar.gz

# 2. Recriar ambiente virtual
cd polymarket-automated-mm
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Recriar arquivos sensíveis:
# - Criar .env com suas chaves
# - Adicionar secrets/credentials.json
```

## 📋 Checklist de Restauração:

- [ ] Extrair backup
- [ ] Recriar venv
- [ ] Instalar dependências
- [ ] Criar `.env` com PK e BROWSER_ADDRESS
- [ ] Adicionar `secrets/credentials.json`
- [ ] Configurar `SPREADSHEET_URL` no `.env`
- [ ] Testar conexão: `python testar_google_sheets.py`
- [ ] Testar bot: `python iniciar_bot.py`

