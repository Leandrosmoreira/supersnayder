# 🚀 Guia de Uso do Bot Polymarket

## O que este bot faz?

Este é um **bot de market making automatizado** para o Polymarket. Ele:

1. **Faz market making** - Coloca ordens de compra e venda automaticamente
2. **Otimiza recompensas** - Calcula o melhor preço para maximizar as recompensas de maker
3. **Monitora mercados** - Acompanha o order book em tempo real via WebSocket
4. **Seleciona mercados** - Escolhe automaticamente os mercados mais lucrativos
5. **Gerencia posições** - Controla riscos e mescla posições automaticamente
6. **Registra tudo** - Salva todos os trades e estatísticas no Google Sheets

## 📋 O que você precisa configurar ANTES de começar:

### 1. Credenciais do Polymarket (OBRIGATÓRIO)

Edite o arquivo `.env` e adicione:

```bash
nano /root/polymarket-automated-mm/.env
```

Configure:
- `PK` - Sua chave privada da carteira (NUNCA compartilhe!)
- `BROWSER_ADDRESS` - Endereço da sua carteira
- `SPREADSHEET_URL` - ✅ Já configurado!

⚠️ **IMPORTANTE**: Sua carteira precisa ter feito pelo menos 1 trade manualmente no Polymarket antes de usar o bot (para configurar permissões).

### 2. Google Sheets (✅ JÁ CONFIGURADO!)

- ✅ Planilha criada
- ✅ Service Account configurado
- ✅ Permissões de escrita funcionando

## 🎯 Próximos Passos - Como Usar o Bot

### Opção 1: Modo Automático Completo (Recomendado)

**Terminal 1 - Atualizador de Dados:**
```bash
cd /root/polymarket-automated-mm
source venv/bin/activate
python data_updater/data_updater.py
```
Este script:
- Busca todos os mercados do Polymarket
- Calcula métricas de recompensa e volatilidade
- Atualiza a planilha do Google Sheets
- Deve rodar continuamente em background

**Terminal 2 - Bot de Trading:**
```bash
cd /root/polymarket-automated-mm
source venv/bin/activate
python main.py
```

### Opção 2: Passo a Passo Manual

**1. Atualizar dados de mercado (uma vez):**
```bash
python data_updater/data_updater.py
```
Isso pode levar 5-10 minutos na primeira vez.

**2. Selecionar mercados para trading:**
```bash
# Opção A: Seleção automática por lucratividade
python update_selected_markets.py

# Opção B: Focar em mercados com alta recompensa (>= $100/dia)
python update_selected_markets.py --min-reward 100 --max-markets 10

# Opção C: Seleção manual - Edite a aba "Selected Markets" no Google Sheets
```

**3. Configurar parâmetros de trading:**
- Abra sua planilha do Google Sheets
- Vá na aba "Hyperparameters"
- Ajuste os parâmetros conforme necessário
- Ou use os valores recomendados do arquivo `recommended_hyperparameters.csv`

**4. Iniciar o bot:**
```bash
python main.py
```

## 📊 Monitoramento

### Ver logs em tempo real:
```bash
# Logs do bot principal
tail -f main.log

# Logs do atualizador de dados
tail -f data_updater.log
```

### Verificar status:
```bash
# Ver se o bot está rodando
ps aux | grep "python.*main.py"

# Verificar posições atuais
python check_positions.py

# Cancelar todas as ordens (se necessário)
python cancel_all_orders.py
```

### Google Sheets - Abas importantes:

- **"Trade Log"** - Todos os trades executados (criado automaticamente)
- **"Maker Rewards"** - Estimativa de recompensas (criado automaticamente)
- **"Selected Markets"** - Mercados que você está trading
- **"Hyperparameters"** - Configurações do bot
- **"All Markets"** - Todos os mercados disponíveis
- **"Volatility Markets"** - Mercados filtrados por volatilidade

## ⚙️ Configurações Avançadas

### Variáveis opcionais no `.env`:

```bash
# Habilitar market making de dois lados (compra e venda simultânea)
TWO_SIDED_MARKET_MAKING=true

# Modo agressivo (pula verificações de segurança - use com cuidado!)
AGGRESSIVE_MODE=false

# URL do RPC do Polygon (padrão já funciona)
POLYGON_RPC_URL=https://polygon-rpc.com
```

## 🛑 Parar o Bot

```bash
# Parar o bot principal
pkill -f "python.*main.py"

# Parar o atualizador de dados
pkill -f "python.*data_updater"

# Ou use Ctrl+C no terminal onde está rodando
```

## ⚠️ Avisos Importantes

1. **Este bot opera com dinheiro real!**
   - Teste com valores pequenos primeiro
   - Monitore regularmente
   - Entenda os riscos antes de usar

2. **Gas fees:**
   - Cada ordem custa gas na rede Polygon
   - O bot tenta minimizar cancelamentos desnecessários
   - Monitore os custos de gas

3. **Riscos:**
   - Você pode perder dinheiro
   - Os mercados podem se mover contra você
   - Sempre monitore suas posições

## 🆘 Troubleshooting

### Bot não inicia:
- Verifique se `PK` e `BROWSER_ADDRESS` estão no `.env`
- Verifique se sua carteira tem fundos
- Verifique se fez pelo menos 1 trade manual no Polymarket

### Erro de conexão com Google Sheets:
- Execute: `python testar_google_sheets.py`
- Verifique se o service account tem permissão de Editor

### Nenhum mercado selecionado:
- Execute: `python update_selected_markets.py`
- Ou adicione mercados manualmente na aba "Selected Markets"

### Ordens sendo canceladas muito frequentemente:
- Isso é normal, o bot ajusta ordens quando o preço muda
- Verifique os logs para entender o comportamento

## 📚 Scripts Úteis

```bash
# Validar configuração completa
python validate_polymarket_bot.py

# Verificar posições atuais
python check_positions.py

# Cancelar todas as ordens
python cancel_all_orders.py

# Atualizar hiperparâmetros na planilha
python update_hyperparameters.py

# Exportar histórico de trades
python export_trades_to_sheets.py
```

## 🎓 Próximos Passos de Aprendizado

1. Leia `README.md` para entender todas as funcionalidades
2. Leia `BOT_OVERVIEW.md` para entender a arquitetura
3. Experimente com valores pequenos primeiro
4. Monitore os logs e a planilha para entender o comportamento
5. Ajuste os hiperparâmetros conforme sua estratégia

## 💡 Dicas

- Comece com 1-2 mercados para entender o comportamento
- Monitore por alguns dias antes de aumentar o capital
- Use a aba "Maker Rewards" para ver quanto está ganhando
- Ajuste os parâmetros gradualmente, não faça mudanças drásticas
- O bot funciona melhor em mercados com boa liquidez

---

**Boa sorte com seu bot de market making! 🚀**

