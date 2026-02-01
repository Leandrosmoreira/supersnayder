# 🚀 Guia Rápido para Iniciar o Bot

## ✅ Status Atual

- ✅ Configuração básica OK
- ✅ Google Sheets conectado
- ✅ Abas criadas
- ⚠️  Mercados de exemplo adicionados (substitua por mercados reais)

## 🎯 Opção 1: Iniciar Agora (Teste)

```bash
cd /root/polymarket-automated-mm
source venv/bin/activate
python main.py
```

**Nota:** Os mercados de exemplo podem não existir. O bot vai tentar operar e mostrar erros se os mercados não forem válidos.

## 🎯 Opção 2: Adicionar Mercados Reais Primeiro

### Método A: Manualmente no Google Sheets

1. Acesse sua planilha
2. Vá na aba "All Markets" (se tiver dados) ou procure mercados no Polymarket
3. Copie dados de mercados reais
4. Cole na aba "Selected Markets" com esta estrutura:

| question | max_size | trade_size | param_type | comments |
|----------|----------|------------|------------|----------|
| Will [mercado real]? | 100 | 50 | default | Descrição |

### Método B: Atualizar Dados Completos (Recomendado)

```bash
# Terminal 1: Atualizar dados (pode demorar 5-10 minutos)
python data_updater/data_updater.py

# Depois, em outro terminal:
python update_selected_markets.py --max-markets 5
```

## 🎯 Opção 3: Iniciar em Background

```bash
# Iniciar bot em background
nohup python main.py > bot.log 2>&1 &

# Ver logs
tail -f bot.log

# Parar bot
pkill -f "python.*main.py"
```

## 📊 Monitoramento

### Ver logs em tempo real:
```bash
tail -f main.log
```

### Verificar se está rodando:
```bash
ps aux | grep "python.*main.py"
```

### Ver posições:
```bash
python check_positions.py
```

## ⚠️ Importante

1. **Mercados devem existir no Polymarket**
   - Os exemplos podem não existir
   - Adicione mercados reais da aba "All Markets"

2. **Primeira vez:**
   - Teste com valores pequenos
   - Monitore os logs
   - Verifique as posições

3. **Google Sheets:**
   - Aba "Trade Log" será criada automaticamente
   - Aba "Maker Rewards" será criada automaticamente

## 🆘 Troubleshooting

### Bot não inicia:
- Verifique logs: `tail -f main.log`
- Verifique .env: `cat .env`

### Nenhum mercado encontrado:
- Verifique aba "Selected Markets" no Google Sheets
- Adicione mercados reais

### Erros de autenticação:
- Verifique PK e BROWSER_ADDRESS no .env
- Execute: `python validate_polymarket_bot.py`

