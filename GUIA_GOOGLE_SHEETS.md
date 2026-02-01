# Guia: Como Configurar Google Sheets (SPREADSHEET_URL)

## O que é o SPREADSHEET_URL?

O bot usa Google Sheets para:
- 📊 Armazenar dados de todos os mercados do Polymarket
- ⚙️ Configurar hiperparâmetros de trading
- 📝 Registrar todos os trades em tempo real
- 💰 Rastrear recompensas de maker
- 📈 Monitorar posições e estatísticas

## Passo a Passo Completo

### 1. Criar uma Planilha do Google Sheets

1. Acesse [Google Sheets](https://sheets.google.com)
2. Clique em **"Blank"** (Planilha em branco) para criar uma nova
3. Dê um nome à planilha (ex: "Polymarket Bot")
4. **Copie a URL da planilha** da barra de endereços do navegador
   - A URL será algo como: `https://docs.google.com/spreadsheets/d/1ABC123xyz.../edit#gid=0`
   - Você precisará dessa URL depois
https://docs.google.com/spreadsheets/d/1GJyM3B_txLcWvbUVHjAKyy8xzgqka6E3a-Yrxu7d1tw/edit?gid=0#gid=0

### 2. Criar um Google Service Account

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Se não tiver um projeto, crie um:
   - Clique em **"Select a project"** → **"New Project"**
   - Dê um nome (ex: "polymarket-bot")
   - Clique em **"Create"**

3. Ative a API do Google Sheets:
   - No menu lateral, vá em **"APIs & Services"** → **"Library"**
   - Procure por **"Google Sheets API"**
   - Clique e depois em **"Enable"**
   - Procure também por **"Google Drive API"** e ative também

4. Criar Service Account:
   - Vá em **"APIs & Services"** → **"Credentials"**
   - Clique em **"Create Credentials"** → **"Service Account"**
   - Dê um nome (ex: "polymarket-bot-service")
   - Clique em **"Create and Continue"**
   - Pule a etapa de permissões (opcional)
   - Clique em **"Done"**

5. Criar chave JSON:
   - Na lista de Service Accounts, clique no que você acabou de criar
   - Vá na aba **"Keys"**
   - Clique em **"Add Key"** → **"Create new key"**
   - Selecione **"JSON"**
   - Clique em **"Create"**
   - O arquivo `credentials.json` será baixado automaticamente

### 3. Compartilhar a Planilha com o Service Account

1. Abra o arquivo `credentials.json` que você baixou
2. Procure pelo campo **"client_email"** (algo como: `polymarket-bot-service@seu-projeto.iam.gserviceaccount.com`)
3. Copie esse email

4. Volte para sua planilha do Google Sheets
5. Clique no botão **"Share"** (Compartilhar) no canto superior direito
6. Cole o email do service account no campo
7. **IMPORTANTE**: Dê permissão de **"Editor"** (não apenas "Viewer")
8. Clique em **"Send"** (ou desmarque "Notify people" se preferir)

### 4. Configurar no Bot

1. **Mover o arquivo credentials.json:**
   ```bash
   # Se você baixou o arquivo, mova-o para o diretório do bot
   mv ~/Downloads/credentials.json /root/polymarket-automated-mm/
   ```

2. **Atualizar o arquivo .env:**
   ```bash
   cd /root/polymarket-automated-mm
   nano .env
   ```
   
   Edite a linha `SPREADSHEET_URL` com a URL da sua planilha:
   ```
   SPREADSHEET_URL=https://docs.google.com/spreadsheets/d/SUA_URL_AQUI/edit
   ```

3. **Verificar se está funcionando:**
   ```bash
   # Ative o ambiente virtual
   source venv/bin/activate
   
   # Teste a conexão (se houver um script de validação)
   python validate_polymarket_bot.py
   ```

## Estrutura da Planilha

O bot criará automaticamente as seguintes abas (sheets) na planilha:

- **"All Markets"** - Todos os mercados disponíveis
- **"Volatility Markets"** - Mercados filtrados por volatilidade
- **"Selected Markets"** - Mercados selecionados para trading
- **"Hyperparameters"** - Parâmetros de configuração do bot
- **"Trade Log"** - Log de todos os trades (criado automaticamente)
- **"Maker Rewards"** - Rastreamento de recompensas (criado automaticamente)

## Verificação Rápida

Para verificar se está tudo configurado:

```bash
cd /root/polymarket-automated-mm
source venv/bin/activate
python -c "from poly_utils.google_utils import get_spreadsheet; s = get_spreadsheet(); print('✅ Conexão OK!')"
```

Se aparecer "✅ Conexão OK!", está funcionando!

## Troubleshooting

### Erro: "Credentials file not found"
- Verifique se o arquivo `credentials.json` está no diretório `/root/polymarket-automated-mm/`
- Verifique se o arquivo tem permissões de leitura: `chmod 644 credentials.json`

### Erro: "SPREADSHEET_URL environment variable is not set"
- Verifique se você editou o arquivo `.env` e adicionou a URL correta
- A URL deve começar com `https://docs.google.com/spreadsheets/d/`

### Erro: "Permission denied" ou "Access denied"
- Verifique se você compartilhou a planilha com o email do service account
- Verifique se deu permissão de **"Editor"** (não apenas "Viewer")
- O email do service account está no arquivo `credentials.json` no campo `client_email`

### Erro: "API not enabled"
- Volte ao Google Cloud Console
- Ative as APIs: **Google Sheets API** e **Google Drive API**

## Segurança

⚠️ **IMPORTANTE**: 
- **NUNCA** compartilhe o arquivo `credentials.json`
- **NUNCA** faça commit do `credentials.json` no Git
- O arquivo já está no `.gitignore` para sua segurança

