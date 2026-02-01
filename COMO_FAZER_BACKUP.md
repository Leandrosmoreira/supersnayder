# 💾 Como Fazer Backup do Projeto

## 📦 Opções de Backup

### 1️⃣ **Git (Recomendado para Código)**
**Vantagens:**
- ✅ Controle de versão completo
- ✅ Histórico de mudanças
- ✅ Fácil de compartilhar
- ✅ Gratuito (GitHub, GitLab, etc.)

**Desvantagens:**
- ❌ Não salva arquivos sensíveis (`.env`, `credentials.json`)
- ❌ Precisa de conta Git

**Como fazer:**
```bash
cd /root/polymarket-automated-mm

# 1. Inicializar repositório (se ainda não tiver)
git init

# 2. Adicionar arquivos (exceto os ignorados pelo .gitignore)
git add .

# 3. Fazer commit
git commit -m "Backup do projeto - $(date +%Y-%m-%d)"

# 4. Criar repositório no GitHub/GitLab e conectar
git remote add origin https://github.com/SEU_USUARIO/polymarket-bot.git
git push -u origin main
```

**⚠️ IMPORTANTE:** O `.gitignore` já está configurado para NÃO salvar:
- `.env` (chaves privadas)
- `secrets/` (credenciais)
- `*.log` (logs)
- `venv/` (ambiente virtual)

---

### 2️⃣ **ZIP/TAR (Backup Completo)**
**Vantagens:**
- ✅ Backup completo de tudo
- ✅ Fácil de restaurar
- ✅ Não precisa de internet
- ✅ Inclui arquivos sensíveis (cuidado!)

**Desvantagens:**
- ❌ Arquivos grandes
- ❌ Sem controle de versão
- ❌ Precisa gerenciar manualmente

**Como fazer:**
```bash
cd /root

# Criar backup completo (incluindo arquivos sensíveis)
tar -czf polymarket-bot-backup-$(date +%Y%m%d).tar.gz \
    --exclude='polymarket-automated-mm/venv' \
    --exclude='polymarket-automated-mm/__pycache__' \
    --exclude='polymarket-automated-mm/*.pyc' \
    polymarket-automated-mm/

# Ou criar ZIP
zip -r polymarket-bot-backup-$(date +%Y%m%d).zip \
    polymarket-automated-mm/ \
    -x "polymarket-automated-mm/venv/*" \
    -x "polymarket-automated-mm/__pycache__/*" \
    -x "polymarket-automated-mm/*.pyc"
```

**Para restaurar:**
```bash
# Descompactar TAR
tar -xzf polymarket-bot-backup-20260201.tar.gz

# Descompactar ZIP
unzip polymarket-bot-backup-20260201.zip
```

---

### 3️⃣ **Backup Seletivo (Apenas Código)**
**Vantagens:**
- ✅ Sem arquivos sensíveis
- ✅ Pode compartilhar com segurança
- ✅ Arquivo menor

**Como fazer:**
```bash
cd /root

# Backup apenas do código (sem .env, secrets, logs)
tar -czf polymarket-bot-codigo-$(date +%Y%m%d).tar.gz \
    --exclude='polymarket-automated-mm/.env' \
    --exclude='polymarket-automated-mm/secrets' \
    --exclude='polymarket-automated-mm/*.log' \
    --exclude='polymarket-automated-mm/venv' \
    --exclude='polymarket-automated-mm/__pycache__' \
    polymarket-automated-mm/
```

---

### 4️⃣ **rsync (Sincronização)**
**Vantagens:**
- ✅ Sincroniza com servidor remoto
- ✅ Backup incremental (só muda o que mudou)
- ✅ Eficiente para backups regulares

**Como fazer:**
```bash
# Sincronizar com servidor remoto
rsync -avz --exclude='venv' --exclude='__pycache__' \
    /root/polymarket-automated-mm/ \
    usuario@servidor:/backup/polymarket-bot/

# Ou para pasta local
rsync -avz --exclude='venv' --exclude='__pycache__' \
    /root/polymarket-automated-mm/ \
    /backup/polymarket-bot/
```

---

### 5️⃣ **Google Drive / Dropbox (Cloud)**
**Vantagens:**
- ✅ Backup na nuvem
- ✅ Acesso de qualquer lugar
- ✅ Versionamento automático (alguns)

**Como fazer:**
```bash
# 1. Instalar rclone (se não tiver)
# apt-get install rclone

# 2. Configurar Google Drive
rclone config

# 3. Fazer backup
rclone copy /root/polymarket-automated-mm/ \
    gdrive:backups/polymarket-bot/ \
    --exclude "venv/**" \
    --exclude "__pycache__/**"
```

---

## 🎯 Recomendação por Situação

### **Para Desenvolvimento:**
✅ **Git + GitHub/GitLab**
- Código versionado
- Fácil colaboração
- Histórico completo

### **Para Backup Completo:**
✅ **ZIP/TAR + Armazenamento Seguro**
- Inclui tudo (cuidado com arquivos sensíveis!)
- Fácil de restaurar
- Guarde em local seguro (pen drive, HD externo, nuvem criptografada)

### **Para Backup Automático:**
✅ **rsync + Cron Job**
- Backup automático diário/semanal
- Eficiente e confiável

### **Para Compartilhar:**
✅ **Git (sem arquivos sensíveis)**
- Seguro para compartilhar
- Código aberto ou privado

---

## 🔒 Segurança dos Backups

### ⚠️ **ATENÇÃO COM ARQUIVOS SENSÍVEIS:**

**NUNCA faça backup público de:**
- `.env` (contém chave privada!)
- `secrets/credentials.json` (credenciais Google)
- `*.log` (pode conter informações sensíveis)

**SEMPRE:**
- ✅ Criptografe backups que contêm arquivos sensíveis
- ✅ Armazene em local seguro
- ✅ Use senha forte para arquivos ZIP
- ✅ Não compartilhe backups com arquivos sensíveis

**Como criptografar ZIP:**
```bash
# ZIP com senha (precisa instalar zip com suporte a criptografia)
zip -r -e polymarket-bot-seguro-$(date +%Y%m%d).zip \
    polymarket-automated-mm/ \
    -x "polymarket-automated-mm/venv/*"
```

---

## 📋 Script de Backup Automático

Crie um script para facilitar:

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/root/backups"
PROJECT_DIR="/root/polymarket-automated-mm"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup completo (com arquivos sensíveis - CUIDADO!)
tar -czf $BACKUP_DIR/polymarket-full-$DATE.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    -C /root polymarket-automated-mm/

# Backup apenas código (sem arquivos sensíveis)
tar -czf $BACKUP_DIR/polymarket-codigo-$DATE.tar.gz \
    --exclude='.env' \
    --exclude='secrets' \
    --exclude='*.log' \
    --exclude='venv' \
    --exclude='__pycache__' \
    -C /root polymarket-automated-mm/

echo "✅ Backups criados em $BACKUP_DIR"
ls -lh $BACKUP_DIR/polymarket-*-$DATE.tar.gz
```

**Tornar executável:**
```bash
chmod +x backup.sh
./backup.sh
```

---

## 🚀 Backup Rápido Agora

**Opção 1 - ZIP Simples:**
```bash
cd /root
zip -r polymarket-backup-$(date +%Y%m%d).zip polymarket-automated-mm/ -x "*/venv/*" "*/__pycache__/*"
```

**Opção 2 - TAR Comprimido:**
```bash
cd /root
tar -czf polymarket-backup-$(date +%Y%m%d).tar.gz --exclude='polymarket-automated-mm/venv' --exclude='polymarket-automated-mm/__pycache__' polymarket-automated-mm/
```

**Opção 3 - Git (se já tiver repositório):**
```bash
cd /root/polymarket-automated-mm
git add .
git commit -m "Backup $(date +%Y-%m-%d)"
git push
```

---

## 📝 Checklist de Backup

- [ ] Código Python (`.py`)
- [ ] Configurações (`.env` - **CUIDADO!**)
- [ ] Credenciais (`secrets/` - **CUIDADO!**)
- [ ] Planilha Google Sheets (URL no `.env`)
- [ ] Documentação (`.md`)
- [ ] Scripts de teste
- [ ] **NÃO** incluir: `venv/`, `__pycache__/`, `*.pyc`

---

## 💡 Dica Final

**Estratégia Recomendada:**
1. **Git** para código (GitHub privado)
2. **ZIP criptografado** para backup completo (guardar em local seguro)
3. **Backup automático** semanal via cron job

**Exemplo de Cron Job (backup semanal):**
```bash
# Editar crontab
crontab -e

# Adicionar linha (toda segunda-feira às 2h da manhã)
0 2 * * 1 /root/polymarket-automated-mm/backup.sh
```

