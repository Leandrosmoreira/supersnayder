# 📊 Tipos de Mercados que o Bot Opera

## 🎯 Resposta Direta

**NÃO**, o bot **não** opera especificamente em "crypto 15min". 

O bot opera em **qualquer mercado de previsão do Polymarket** que atenda aos critérios de seleção, independente do tema ou timeframe.

## 🔍 Como o Bot Seleciona Mercados

### Critérios de Seleção (Modo Padrão - Profitability):

```python
✅ Recompensa >= 1.0% (gm_reward_per_100)
✅ Volatilidade < 20 (volatility_sum)
✅ Spread < 0.1 (spread)
✅ Preço entre 0.1 e 0.9 (best_bid)
✅ Mercado ativo e não fechado
```

### Critérios de Seleção (Modo High Reward):

```python
✅ Recompensa diária >= $X (rewards_daily_rate)
✅ Preço entre 0.1 e 0.9
✅ Spread < 0.15
✅ Volatilidade < 50
```

## 📈 Tipos de Mercados que o Bot Pode Operar

### 1. **Mercados Políticos**
```
Exemplo: "Will Trump win the 2024 election?"
- Preço: $0.45 (45% de chance)
- Spread: $0.02
- Recompensas: Boas
```

### 2. **Mercados de Ações/Stocks**
```
Exemplo: "Will Tesla close above $250 on Feb 2?"
- Preço: $0.60
- Spread: $0.03
- Recompensas: Variáveis
```

### 3. **Mercados de Crypto** (se atenderem critérios)
```
Exemplo: "Will Bitcoin hit $100k by end of 2024?"
- Preço: $0.30
- Spread: $0.05
- Recompensas: Depende do mercado
```

### 4. **Mercados de Esportes**
```
Exemplo: "Will Team X win the championship?"
- Preço: $0.70
- Spread: $0.02
- Recompensas: Boas
```

### 5. **Mercados de Eventos**
```
Exemplo: "Will event X happen by date Y?"
- Preço: Variável
- Spread: Variável
- Recompensas: Depende
```

## ⚠️ O que o Bot NÃO Opera

### ❌ Mercados com Preços Extremos
```
- Preço < 0.1 (muito baixo)
- Preço > 0.9 (muito alto)
→ Difíceis de gerenciar, maior risco
```

### ❌ Mercados com Spread Muito Largo
```
- Spread >= 0.15 (15%)
→ Pouca liquidez, difícil de fazer market making
```

### ❌ Mercados com Alta Volatilidade
```
- Volatilidade >= 20 (modo padrão)
- Volatilidade >= 50 (modo high reward)
→ Muito arriscado para market making
```

### ❌ Mercados Fechados ou Expirados
```
- Mercados inativos
- Mercados que já terminaram
→ Não há liquidez
```

## 🎲 Sobre "Crypto 15min"

Se você está se referindo a mercados de crypto com resolução de 15 minutos:

1. **O bot pode operar neles** - Se atenderem os critérios
2. **Mas não é específico** - O bot não filtra por tipo de mercado
3. **Depende da liquidez** - Precisa ter spread adequado e recompensas

### Exemplo de Mercado Crypto que o Bot Operaria:

```
✅ "Will Bitcoin close above $50k in the next 15 minutes?"
   - Preço: $0.55
   - Spread: $0.02
   - Recompensa: 2.5%
   - Volatilidade: 12
   → Bot OPERARIA ✅

❌ "Will Bitcoin close above $50k in the next 15 minutes?"
   - Preço: $0.05 (muito baixo)
   - Spread: $0.20 (muito largo)
   - Recompensa: 0.5%
   - Volatilidade: 35
   → Bot NÃO operaria ❌
```

## 🔧 Como Ver Quais Mercados o Bot Está Operando

### 1. **Google Sheets - Aba "Selected Markets"**
```
Lista todos os mercados que o bot está trading atualmente
```

### 2. **Google Sheets - Aba "All Markets"**
```
Lista TODOS os mercados disponíveis no Polymarket
```

### 3. **Google Sheets - Aba "Volatility Markets"**
```
Mercados filtrados por volatilidade < 20
```

### 4. **Logs do Bot**
```bash
tail -f main.log
# Mostra quais mercados estão sendo processados
```

## 📊 Estatísticas Típicas

### Mercados que o Bot Prefere:

| Característica | Valor Ideal |
|---------------|-------------|
| Recompensa | >= 1.0% |
| Volatilidade | < 20 |
| Spread | < 0.1 (10%) |
| Preço | 0.1 - 0.9 |
| Liquidez | Alta |

### Distribuição Típica de Mercados:

- **Política**: ~30%
- **Ações/Stocks**: ~25%
- **Crypto**: ~15%
- **Esportes**: ~20%
- **Outros**: ~10%

## 🎯 Resumo

1. **O bot não é específico para crypto ou timeframes**
2. **Opera em QUALQUER mercado do Polymarket que atenda critérios**
3. **Foca em recompensas, volatilidade e spread**
4. **Pode operar em crypto 15min se o mercado for bom**
5. **Mas não filtra especificamente por isso**

---

**Em resumo:** O bot é um market maker genérico que seleciona mercados baseado em **características técnicas** (recompensas, volatilidade, spread), não em **tipo de mercado** ou **timeframe**.

