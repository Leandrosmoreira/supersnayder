# 🎯 Como Restringir os Mercados que o Bot Opera

## 📋 Resumo Rápido

O bot **só opera nos mercados listados na aba "Selected Markets"** do Google Sheets. Para restringir, você precisa editar essa aba.

## 🔧 Método 1: Edição Manual no Google Sheets (Mais Simples)

### Passo a Passo:

1. **Abra sua planilha do Google Sheets**
   - Acesse a URL configurada no `.env` (`SPREADSHEET_URL`)

2. **Vá para a aba "Selected Markets"**

3. **Remova os mercados que você NÃO quer**
   - Selecione a linha inteira
   - Delete (ou deixe vazia)

4. **Adicione apenas os mercados que você QUER**
   - Copie dados da aba "All Markets" ou "Volatility Markets"
   - Cole na aba "Selected Markets"

5. **Estrutura necessária da aba "Selected Markets":**

| question | max_size | trade_size | param_type | comments |
|----------|----------|------------|------------|----------|
| Will Bitcoin hit $100k? | 100 | 50 | default | Crypto market |
| Will Tesla close above $250? | 80 | 40 | conservative | Stock market |

### Campos Obrigatórios:

- **question**: A pergunta do mercado (deve existir em "All Markets")
- **max_size**: Tamanho máximo de posição (em USDC)
- **trade_size**: Tamanho de cada trade (em USDC)
- **param_type**: Tipo de parâmetros (default, conservative, aggressive)
- **comments**: Comentários opcionais

## 🔧 Método 2: Usando Script Python (Mais Automático)

### Opção A: Selecionar apenas mercados de Crypto

Crie um script personalizado:

```python
#!/usr/bin/env python3
import pandas as pd
from data_updater.data_updater import get_spreadsheet
from gspread_dataframe import set_with_dataframe

# Conectar ao Google Sheets
spreadsheet = get_spreadsheet(read_only=False)

# Carregar todos os mercados
all_markets_sheet = spreadsheet.worksheet("All Markets")
all_df = pd.DataFrame(all_markets_sheet.get_all_records())

# Filtrar apenas mercados de crypto
crypto_keywords = ['Bitcoin', 'BTC', 'Ethereum', 'ETH', 'crypto', 'cryptocurrency']
crypto_df = all_df[
    all_df['question'].str.contains('|'.join(crypto_keywords), case=False, na=False)
]

# Aplicar filtros de qualidade
crypto_df = crypto_df[
    (crypto_df['gm_reward_per_100'] >= 1.0) &
    (crypto_df['volatility_sum'] < 20) &
    (crypto_df['spread'] < 0.1) &
    (crypto_df['best_bid'] >= 0.1) &
    (crypto_df['best_bid'] <= 0.9)
]

# Preparar dados para "Selected Markets"
selected_markets = []
for _, row in crypto_df.head(10).iterrows():  # Top 10
    selected_markets.append({
        'question': row['question'],
        'max_size': 100,
        'trade_size': 50,
        'param_type': 'default',
        'comments': f"Crypto - Reward: {row.get('gm_reward_per_100', 0):.2f}%"
    })

# Atualizar aba "Selected Markets"
selected_sheet = spreadsheet.worksheet("Selected Markets")
new_df = pd.DataFrame(selected_markets)
set_with_dataframe(selected_sheet, new_df, include_index=False, resize=True)

print(f"✅ Atualizado! {len(selected_markets)} mercados de crypto selecionados")
```

### Opção B: Filtrar por palavras-chave específicas

```python
# Exemplo: Apenas mercados sobre "Tesla"
keywords = ['Tesla', 'TSLA']
filtered_df = all_df[
    all_df['question'].str.contains('|'.join(keywords), case=False, na=False)
]
```

### Opção C: Filtrar por recompensas mínimas

```python
# Exemplo: Apenas mercados com recompensa >= $100/dia
high_reward_df = all_df[
    (all_df['rewards_daily_rate'] >= 100) &
    (all_df['best_bid'] >= 0.1) &
    (all_df['best_bid'] <= 0.9)
]
```

## 🔧 Método 3: Modificar o Script de Seleção Automática

Edite o arquivo `update_selected_markets.py` para adicionar filtros personalizados:

```python
# Adicione filtros antes da seleção
filtered = source_df[
    (source_df['gm_reward_per_100'] >= 1.0) &
    (source_df['volatility_sum'] < 20) &
    (source_df['spread'] < 0.1) &
    (source_df['best_bid'] >= 0.1) &
    (source_df['best_bid'] <= 0.9) &
    # ADICIONE SEU FILTRO AQUI:
    (source_df['question'].str.contains('Bitcoin|BTC', case=False, na=False))  # Apenas Bitcoin
].copy()
```

## 📝 Exemplos Práticos

### Exemplo 1: Apenas Mercados de Crypto

**No Google Sheets:**
1. Aba "All Markets" → Filtrar por "Bitcoin" ou "crypto"
2. Copiar os melhores mercados
3. Colar na aba "Selected Markets"
4. Ajustar `max_size` e `trade_size`

### Exemplo 2: Apenas Mercados de Ações

**Filtros:**
- Palavras-chave: "Tesla", "Apple", "Microsoft", "stock", "close"
- Recompensa >= 1.5%
- Volatilidade < 15

### Exemplo 3: Apenas Mercados Políticos

**Filtros:**
- Palavras-chave: "election", "president", "vote", "Trump", "Biden"
- Recompensa >= 1.0%
- Spread < 0.08

### Exemplo 4: Mercados com Alta Recompensa

**Comando:**
```bash
python update_selected_markets.py --min-reward 150 --max-markets 5
```

Isso seleciona apenas mercados com recompensa >= $150/dia.

## ⚙️ Configuração Avançada

### Filtrar por Múltiplos Critérios

Crie um script personalizado:

```python
def filter_markets(all_df, filters):
    """
    Filtra mercados baseado em critérios personalizados
    
    filters = {
        'keywords': ['Bitcoin', 'BTC'],  # Palavras-chave na pergunta
        'min_reward': 1.5,               # Recompensa mínima (%)
        'max_volatility': 20,            # Volatilidade máxima
        'max_spread': 0.1,               # Spread máximo
        'price_range': (0.1, 0.9),       # Faixa de preço
        'min_daily_reward': 50           # Recompensa diária mínima ($)
    }
    """
    filtered = all_df.copy()
    
    # Filtro de palavras-chave
    if 'keywords' in filters:
        keywords = '|'.join(filters['keywords'])
        filtered = filtered[
            filtered['question'].str.contains(keywords, case=False, na=False)
        ]
    
    # Filtro de recompensa
    if 'min_reward' in filters:
        filtered = filtered[
            filtered['gm_reward_per_100'] >= filters['min_reward']
        ]
    
    # Filtro de volatilidade
    if 'max_volatility' in filters:
        filtered = filtered[
            filtered['volatility_sum'] < filters['max_volatility']
        ]
    
    # Filtro de spread
    if 'max_spread' in filters:
        filtered = filtered[
            filtered['spread'] < filters['max_spread']
        ]
    
    # Filtro de preço
    if 'price_range' in filters:
        min_price, max_price = filters['price_range']
        filtered = filtered[
            (filtered['best_bid'] >= min_price) &
            (filtered['best_bid'] <= max_price)
        ]
    
    # Filtro de recompensa diária
    if 'min_daily_reward' in filters:
        filtered = filtered[
            filtered['rewards_daily_rate'] >= filters['min_daily_reward']
        ]
    
    return filtered

# Uso:
filters = {
    'keywords': ['Bitcoin', 'BTC'],
    'min_reward': 2.0,
    'max_volatility': 15,
    'max_spread': 0.08,
    'price_range': (0.2, 0.8)
}

crypto_markets = filter_markets(all_df, filters)
```

## 🔄 Atualização Automática

O bot atualiza a lista de mercados a cada 60 segundos. Então:

1. **Edite a aba "Selected Markets"**
2. **Aguarde até 60 segundos**
3. **O bot automaticamente carregará os novos mercados**

Ou force atualização reiniciando o bot:
```bash
pkill -f "python.*main.py"
python main.py
```

## ⚠️ Importante

### Campos Obrigatórios:

A aba "Selected Markets" DEVE ter estas colunas:
- `question` (obrigatório) - Nome do mercado
- `max_size` (obrigatório) - Tamanho máximo
- `trade_size` (obrigatório) - Tamanho do trade
- `param_type` (obrigatório) - Tipo de parâmetros
- `comments` (opcional) - Comentários

### Validação:

O bot valida se o mercado existe em "All Markets". Se não existir, será ignorado.

### Erros Comuns:

1. **Mercado não encontrado**
   - Verifique se o `question` está exatamente igual em "All Markets"
   - Case-sensitive (maiúsculas/minúsculas importam)

2. **Bot não está operando**
   - Verifique se a aba "Selected Markets" tem dados
   - Verifique os logs: `tail -f main.log`

3. **Mercados não atualizam**
   - Aguarde 60 segundos (atualização automática)
   - Ou reinicie o bot

## 📊 Verificar Mercados Ativos

### Via Google Sheets:
1. Aba "Selected Markets" → Lista todos os mercados ativos

### Via Logs:
```bash
tail -f main.log | grep "question"
```

### Via Script:
```python
from poly_data.data_utils import update_markets
import poly_data.global_state as global_state

update_markets()
print(f"Mercados ativos: {len(global_state.df)}")
for _, row in global_state.df.iterrows():
    print(f"  - {row['question']}")
```

## 🎯 Resumo

1. **Edite a aba "Selected Markets"** no Google Sheets
2. **Adicione apenas os mercados que você quer**
3. **Remova os que você não quer**
4. **O bot atualiza automaticamente a cada 60 segundos**

**Simples assim!** 🚀

