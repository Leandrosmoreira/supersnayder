# 💰 Erro: "not enough balance / allowance"

## 📖 O que significa esse erro?

Esse erro aparece quando você tenta criar uma ordem no Polymarket, mas há um dos seguintes problemas:

### 1. **Saldo Insuficiente (Balance)**
Você não tem USDC suficiente na sua carteira para criar a ordem.

**Exemplo:**
- Você quer comprar 200 shares a $0.19 = **$38.00**
- Mas você só tem **$13.61** na carteira
- ❌ **Erro: Saldo insuficiente!**

### 2. **Permissão Insuficiente (Allowance)**
Você tem USDC na carteira, mas não deu permissão para o contrato do Polymarket usar esse dinheiro.

**É como ter dinheiro no banco, mas não ter autorizado o débito automático!**

## 🔍 Como verificar?

### Verificar Saldo:
```bash
cd /root/polymarket-automated-mm
source venv/bin/activate
python check_positions.py
```

Isso mostrará:
- 💰 USDC Balance: $X.XX
- 📊 Position Value: $X.XX
- 💵 Total Balance: $X.XX

### Verificar Allowance:
O allowance é a permissão que você dá ao contrato do Polymarket para usar seu USDC.

## ✅ Como resolver?

### Opção 1: Depositar mais USDC
1. Acesse o site do Polymarket
2. Vá em "Deposit"
3. Adicione mais USDC à sua carteira
4. Certifique-se de ter pelo menos o valor necessário para a ordem + taxas

### Opção 2: Aprovar Allowance (Dar Permissão)
Se você tem saldo mas não tem allowance:

1. **Via Site do Polymarket:**
   - Acesse qualquer mercado
   - Tente fazer uma ordem manual
   - O site pedirá para você "Approve" (Aprovar) o uso do USDC
   - Clique em "Approve" e confirme na carteira

2. **Via Script (se disponível):**
   ```bash
   python approve_and_trade.py
   ```

### Opção 3: Reduzir o Tamanho da Ordem
Se você não quer depositar mais, pode reduzir o tamanho da ordem:

- Em vez de 200 shares, use 50 shares
- Em vez de $38, gastará apenas $9.50

## 📊 Exemplo Prático

**Situação Atual:**
- Saldo: $13.61
- Ordem tentada: 200 shares × $0.19 = **$38.00**
- ❌ **Falta: $24.39**

**Soluções:**
1. ✅ Depositar pelo menos $25 (para ter margem)
2. ✅ Reduzir ordem para 70 shares (70 × $0.19 = $13.30)
3. ✅ Verificar se precisa aprovar allowance

## 🎯 Resumo para Iniciantes

**Em palavras simples:**
- **Balance = Dinheiro na conta**
- **Allowance = Permissão para usar o dinheiro**

O erro significa que você precisa de:
1. Mais dinheiro na conta, OU
2. Dar permissão para o Polymarket usar seu dinheiro

**É como tentar comprar algo no cartão sem ter limite ou sem ter autorizado o débito!**

## 🔧 Verificação Rápida

Execute este comando para ver seu saldo atual:
```bash
cd /root/polymarket-automated-mm
source venv/bin/activate
python -c "from poly_data.polymarket_client import PolymarketClient; c = PolymarketClient(); print('Saldo USDC:', c.get_usdc_balance())"
```

Se o saldo for suficiente mas ainda der erro, o problema é o **allowance** - você precisa aprovar no site do Polymarket.

