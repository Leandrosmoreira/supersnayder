# 🧠 Como Funciona a Lógica do Bot

## 📖 Conceito Básico: Market Making

O bot funciona como um **"fazedor de mercado"** (market maker). É como se você fosse um **lojista** que:

1. **Compra barato** (coloca ordens de compra abaixo do preço atual)
2. **Vende caro** (coloca ordens de venda acima do preço atual)
3. **Lucra com a diferença** (o "spread")

### Exemplo Simples:

```
Preço atual do mercado: $0.75

Você coloca:
- Ordem de COMPRA em $0.74  ← "Quero comprar barato"
- Ordem de VENDA em $0.76   ← "Quero vender caro"

Se ambas preencherem:
- Comprou a $0.74
- Vendeu a $0.76
- Lucro: $0.02 por ação! 💰
```

## 🔄 Fluxo Completo do Bot

### 1. **Inicialização** (Quando o bot liga)

```
┌─────────────────────────────────────┐
│  1. Conecta ao Polymarket API      │
│  2. Carrega mercados do Google      │
│  3. Verifica posições atuais        │
│  4. Verifica ordens ativas          │
│  5. Conecta WebSockets (tempo real)│
└─────────────────────────────────────┘
```

### 2. **Loop Principal** (Roda continuamente)

```
┌─────────────────────────────────────────────────────────┐
│  A cada 10 segundos:                                    │
│  ├─ Limpa trades pendentes antigos                      │
│  ├─ Atualiza posições                                   │
│  ├─ Atualiza ordens                                     │
│  └─ A cada 60 segundos: atualiza dados de mercado       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Quando recebe atualização do order book (WebSocket):   │
│  ├─ Atualiza o order book local                        │
│  ├─ Calcula preços ideais                               │
│  ├─ Decide quanto comprar/vender                        │
│  ├─ Coloca/cancela/atualiza ordens                      │
│  └─ Gerencia posições                                   │
└─────────────────────────────────────────────────────────┘
```

## 🎯 Lógica de Decisão de Trading

### Passo 1: Analisar o Mercado

```python
# O bot olha o order book (livro de ordens)
best_bid = $0.74    # Melhor preço de compra disponível
best_ask = $0.76    # Melhor preço de venda disponível
mid_price = $0.75   # Preço médio

# Calcula o spread
spread = best_ask - best_bid = $0.02
```

### Passo 2: Calcular Preços Ideais

O bot calcula onde colocar suas ordens para:
- ✅ Maximizar recompensas de maker
- ✅ Ter boa chance de preencher
- ✅ Manter spread adequado

```python
# Fórmula de recompensa do Polymarket:
# S = ((v - s) / v)²
# onde:
#   v = max_spread (spread máximo)
#   s = distância do preço médio

# O bot coloca ordens a ~15% do max_spread para otimizar
buy_price = mid_price - (max_spread * 0.15)
sell_price = mid_price + (max_spread * 0.15)
```

### Passo 3: Decidir Quanto Comprar/Vender

```python
# Lógica baseada na posição atual:

if posição < max_size:
    # Ainda construindo posição
    buy_amount = trade_size  # Ex: $20
    sell_amount = 0          # Não vende ainda
    
elif posição >= max_size:
    # Já tem posição máxima
    buy_amount = 0            # Para de comprar
    sell_amount = trade_size  # Começa a vender
    
else:
    # Tem posição, mas não máxima
    buy_amount = trade_size
    sell_amount = trade_size  # Market making de dois lados
```

### Passo 4: Gerenciar Risco

```python
# O bot verifica:
- Preço está entre 0.1 e 0.9? (evita extremos)
- Spread é aceitável?
- Há liquidez suficiente?
- Posição não excede max_size?
- Não está em cooldown? (evita cancelamentos excessivos)
```

## 🔀 Tipos de Estratégia

### 1. **Market Making Tradicional** (Padrão)

```
Posição: $0
├─ Coloca ordem de COMPRA em $0.74
└─ Coloca ordem de VENDA em $0.76

Quando compra preenche:
├─ Agora tem posição de $20
└─ Continua colocando ordem de VENDA em $0.76

Quando venda preenche:
├─ Lucra $0.02 por ação
└─ Volta a colocar ordem de COMPRA
```

### 2. **Two-Sided Market Making** (Opcional)

```
Mesmo sem posição, coloca:
├─ Ordem de COMPRA
└─ Ordem de VENDA

Lucra de:
├─ Recompensas de maker (quando ordens preenchem)
└─ Spread (diferença entre compra e venda)
```

### 3. **Position Building** (Construção de Posição)

```
Objetivo: Construir posição até max_size

Estado 1: Posição = $0
├─ Compra $20
└─ Posição = $20

Estado 2: Posição = $20
├─ Compra mais $20
└─ Posição = $40

Estado 3: Posição = $40
├─ Compra mais $20
└─ Posição = $60 (max_size atingido)

Estado 4: Posição = $60
├─ Para de comprar
└─ Começa a vender para lucrar
```

## 🧩 Componentes Principais

### 1. **WebSocket Handlers** (Tempo Real)

```python
# Recebe atualizações do order book
market_websocket → order_book_update → process_data()

# Recebe seus próprios trades
user_websocket → trade_fill → update_position()
```

### 2. **Trading Logic** (`trading.py`)

```python
def perform_trade(market):
    # 1. Mescla posições opostas (YES + NO)
    # 2. Analisa o mercado
    # 3. Calcula preços ideais
    # 4. Decide quanto comprar/vender
    # 5. Coloca/cancela ordens
    # 6. Gerencia risco
```

### 3. **Price Calculator**

```python
def get_order_prices(...):
    # Considera:
    - Melhor bid/ask atual
    - Profundidade do order book
    - Tick size (incremento mínimo)
    - Recompensas de maker
    - Spread máximo
```

### 4. **Position Manager**

```python
def get_buy_sell_amount(...):
    # Decide baseado em:
    - Posição atual
    - Max size configurado
    - Trade size configurado
    - Preço médio de entrada
```

## 🎛️ Parâmetros Configuráveis

### No Google Sheets - Aba "Hyperparameters":

```python
trade_size = $20        # Quanto comprar/vender por vez
max_size = $60          # Posição máxima antes de vender
tick_size = 0.01       # Incremento mínimo de preço
max_spread = 0.10       # Spread máximo aceitável (10%)
```

### No `.env`:

```bash
TWO_SIDED_MARKET_MAKING=true   # Market making de dois lados
AGGRESSIVE_MODE=false          # Modo agressivo (pula verificações)
```

## 🔄 Ciclo de Vida de uma Ordem

```
1. Bot calcula preço ideal: $0.74
   ↓
2. Coloca ordem de COMPRA em $0.74
   ↓
3. Ordem fica no order book
   ↓
4. Alguém vende a $0.74 → Ordem preenche!
   ↓
5. Bot recebe notificação via WebSocket
   ↓
6. Atualiza posição: +$20 a $0.74
   ↓
7. Calcula nova ordem de VENDA em $0.76
   ↓
8. Repete o ciclo...
```

## 🛡️ Proteções e Segurança

### 1. **Cooldown** (30 segundos)
```
Evita cancelar ordens muito frequentemente
- Economiza gas fees
- Reduz churn (rotatividade) de ordens
```

### 2. **Thresholds de Cancelamento**
```
Só cancela ordem se:
- Diferença de preço > 1.5%
- Diferença de tamanho > 25%
```

### 3. **Validações**
```
Antes de colocar ordem:
- Preço entre 0.1 e 0.9? ✅
- Spread aceitável? ✅
- Há liquidez? ✅
- Não excede max_size? ✅
```

### 4. **Position Merging**
```
Se você tem:
- 100 ações YES
- 80 ações NO

O bot mescla 80 de cada:
- Libera $80 de capital
- Deixa 20 ações YES
```

## 📊 Exemplo Prático Completo

### Cenário: Mercado "Will Bitcoin hit $100k?"

```
Estado Inicial:
- Preço atual: $0.50 (50% de chance)
- Best bid: $0.49
- Best ask: $0.51
- Sua posição: $0

Bot calcula:
- Buy price: $0.49
- Sell price: $0.51
- Buy amount: $20
- Sell amount: $0 (sem posição ainda)

Ações:
1. Coloca ordem COMPRA $20 @ $0.49
   ↓
2. Ordem preenche! (alguém vendeu)
   ↓
3. Nova posição: $20 @ $0.49
   ↓
4. Bot calcula nova ordem VENDA $20 @ $0.51
   ↓
5. Coloca ordem VENDA $20 @ $0.51
   ↓
6. Ordem preenche! (alguém comprou)
   ↓
7. Lucro: $0.02 × 20 = $0.40 💰
   + Recompensas de maker
```

## 🆚 Diferenças de Outros Bots

### Este Bot vs. Bots de Arbitragem:

**Este bot (Market Making):**
- ✅ Fornece liquidez
- ✅ Lucra com spread + recompensas
- ✅ Riscos controlados
- ✅ Funciona em qualquer mercado

**Bots de Arbitragem:**
- Buscam diferenças de preço entre exchanges
- Requerem capital maior
- Mais complexos

### Este Bot vs. Trading Manual:

**Este bot:**
- ✅ 24/7 operando
- ✅ Reações instantâneas
- ✅ Sem emoções
- ✅ Otimizado para recompensas

**Trading Manual:**
- Precisa estar online
- Reações mais lentas
- Pode ter viés emocional

## 🎓 Resumo em 3 Pontos

1. **O bot coloca ordens de compra e venda simultaneamente**
   - Compra barato, vende caro
   - Lucra com a diferença (spread)

2. **Otimiza para recompensas de maker**
   - Calcula melhor posição para maximizar recompensas
   - Usa fórmula do Polymarket

3. **Gerencia risco automaticamente**
   - Limita tamanho de posição
   - Evita cancelamentos desnecessários
   - Mescla posições quando possível

---

**Em resumo:** É como ter um lojista 24/7 que compra barato e vende caro, otimizado para maximizar lucros e recompensas! 🚀

