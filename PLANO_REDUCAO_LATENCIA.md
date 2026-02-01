# 📊 PLANO DE REDUÇÃO DE LATÊNCIA
## VPS → Polymarket

**Data:** 2026-02-01  
**Latência Atual:** ~176ms (média)  
**Objetivo:** Reduzir para ~80-120ms (redução de 30-55%)

---

## 📈 ANÁLISE ATUAL

### Distribuição da Latência (~176ms)

```
┌─────────────────────────────────────────────┐
│ Processamento Local (código):      ~20ms    │ ← Redutível via código
│ Rede VPS → Polymarket:             ~80ms   │ ← Não redutível via código
│ Processamento Polymarket (API):     ~40ms   │ ← Não controlável
│ Rede Polymarket → VPS:              ~30ms   │ ← Não redutível via código
│ Verificação/Polling:                ~6ms    │ ← Redutível via código
└─────────────────────────────────────────────┘
```

### Componentes Redutíveis via Código
- **Processamento local:** ~20ms
- **Verificação/polling:** ~6ms
- **Total redutível:** ~26ms (15% da latência total)

### Componentes NÃO Redutíveis via Código
- **Rede física:** ~110ms (62% da latência total)
- **Processamento servidor:** ~40ms (23% da latência total)

---

## 🎯 FASES DE IMPLEMENTAÇÃO

### **FASE 1: Otimizações de Alto Impacto** (Prioridade Máxima)
**Redução Estimada: 50-90ms**  
**Nova Latência Esperada: ~86-126ms**

#### 1.1 Connection Pooling / HTTP Keep-Alive
- **Problema:** Nova conexão TCP/TLS a cada requisição
- **Solução:** Reutilizar sessões HTTP com `requests.Session()` ou `httpx.Client()`
- **Impacto:** -30-50ms
- **Complexidade:** Baixa
- **Arquivos a modificar:**
  - `poly_data/polymarket_client.py`
  - Verificar se `py-clob-client` já usa connection pooling

#### 1.2 Remover Polling Desnecessário
- **Problema:** Verificação imediata após envio adiciona overhead
- **Solução:** Confiar na resposta da API, verificar apenas se necessário
- **Impacto:** -20-40ms
- **Complexidade:** Baixa
- **Arquivos a modificar:**
  - `teste_ordem_maker_verificacao.py`
  - Remover ou tornar opcional a verificação imediata

#### 1.3 Paralelização de Requisições
- **Problema:** Ordens enviadas sequencialmente
- **Solução:** Usar `asyncio` ou `threading` para envio paralelo
- **Impacto:** -0-30ms (depende do número de ordens)
- **Complexidade:** Média
- **Arquivos a modificar:**
  - `teste_ordem_maker_verificacao.py`
  - `poly_data/polymarket_client.py` (se necessário)

---

### **FASE 2: Otimizações de Médio Impacto** (Prioridade Alta)
**Redução Estimada: 15-30ms**  
**Nova Latência Esperada: ~56-111ms**

#### 2.1 Otimizar Verificação de Ordem
- **Problema:** Verificação atual pode ser mais eficiente
- **Solução:** 
  - Usar WebSocket para updates em tempo real
  - Reduzir frequência de polling
  - Cachear resultados de order book
- **Impacto:** -10-20ms
- **Complexidade:** Média
- **Arquivos a modificar:**
  - `teste_ordem_maker_verificacao.py`
  - `poly_data/websocket_handlers.py` (se usar WebSocket)

#### 2.2 Cache de Autenticação
- **Problema:** Recalcular assinaturas/credenciais a cada requisição
- **Solução:** Cachear tokens e credenciais quando possível
- **Impacto:** -5-10ms
- **Complexidade:** Baixa
- **Arquivos a modificar:**
  - `poly_data/polymarket_client.py`

#### 2.3 Reduzir Overhead de Serialização
- **Problema:** JSON parsing/encoding pode ser otimizado
- **Solução:** 
  - Usar `orjson` ou `ujson` em vez de `json` padrão
  - Reduzir tamanho de payloads
- **Impacto:** -5-15ms
- **Complexidade:** Baixa
- **Arquivos a modificar:**
  - `poly_data/polymarket_client.py`
  - Verificar dependências do `py-clob-client`

---

### **FASE 3: Otimizações de Baixo Impacto** (Prioridade Média)
**Redução Estimada: 5-10ms**  
**Nova Latência Esperada: ~46-106ms**

#### 3.1 Otimizar Imports e Inicialização
- **Problema:** Imports pesados e inicialização lenta
- **Solução:** Lazy loading de módulos pesados
- **Impacto:** -2-5ms
- **Complexidade:** Baixa
- **Arquivos a modificar:**
  - Múltiplos arquivos (verificar imports)

#### 3.2 Reduzir Logging Excessivo
- **Problema:** I/O de logs adiciona overhead
- **Solução:** 
  - Logging assíncrono
  - Reduzir nível de log em produção
  - Buffer de logs
- **Impacto:** -1-3ms
- **Complexidade:** Baixa
- **Arquivos a modificar:**
  - Múltiplos arquivos (ajustar logging)

#### 3.3 Otimizar Estruturas de Dados
- **Problema:** Uso ineficiente de estruturas de dados
- **Solução:** 
  - Usar `collections.deque` para filas
  - Otimizar conversões de tipos
- **Impacto:** -2-5ms
- **Complexidade:** Baixa
- **Arquivos a modificar:**
  - Múltiplos arquivos (verificar estruturas)

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### Fase 1 (Alto Impacto)
- [ ] 1.1 Implementar Connection Pooling
  - [ ] Verificar se `py-clob-client` já usa pooling
  - [ ] Implementar `requests.Session()` se necessário
  - [ ] Testar e medir latência
- [ ] 1.2 Remover Polling Desnecessário
  - [ ] Tornar verificação opcional
  - [ ] Confiar na resposta da API
  - [ ] Testar e medir latência
- [ ] 1.3 Paralelização de Requisições
  - [ ] Implementar envio paralelo de ordens
  - [ ] Testar e medir latência

### Fase 2 (Médio Impacto)
- [ ] 2.1 Otimizar Verificação de Ordem
  - [ ] Implementar WebSocket para updates
  - [ ] Reduzir frequência de polling
  - [ ] Testar e medir latência
- [ ] 2.2 Cache de Autenticação
  - [ ] Implementar cache de tokens
  - [ ] Testar e medir latência
- [ ] 2.3 Reduzir Overhead de Serialização
  - [ ] Avaliar uso de `orjson` ou `ujson`
  - [ ] Implementar se viável
  - [ ] Testar e medir latência

### Fase 3 (Baixo Impacto)
- [ ] 3.1 Otimizar Imports
  - [ ] Implementar lazy loading
  - [ ] Testar e medir latência
- [ ] 3.2 Reduzir Logging
  - [ ] Implementar logging assíncrono
  - [ ] Testar e medir latência
- [ ] 3.3 Otimizar Estruturas de Dados
  - [ ] Revisar e otimizar estruturas
  - [ ] Testar e medir latência

---

## 🧪 PLANO DE TESTES

### Teste de Baseline
1. Executar `teste_ordem_maker_verificacao.py` 10 vezes
2. Registrar latência média, mínima e máxima
3. Salvar resultados em `baseline_latencia.txt`

### Teste Após Cada Fase
1. Executar mesmo teste 10 vezes
2. Comparar com baseline
3. Registrar melhorias
4. Decidir se continua para próxima fase

### Critérios de Sucesso
- **Fase 1:** Redução de 50-90ms (latência < 126ms)
- **Fase 2:** Redução adicional de 15-30ms (latência < 111ms)
- **Fase 3:** Redução adicional de 5-10ms (latência < 106ms)

---

## 📊 MÉTRICAS E MONITORAMENTO

### Métricas a Coletar
- Latência média (ms)
- Latência mínima (ms)
- Latência máxima (ms)
- Desvio padrão (ms)
- Taxa de sucesso (%)
- Número de tentativas

### Ferramentas
- `teste_ordem_maker_verificacao.py` (já implementado)
- Script de análise de resultados
- Gráficos de evolução da latência

---

## ⚠️ RISCOS E CONSIDERAÇÕES

### Riscos
1. **Breaking Changes:** Otimizações podem quebrar funcionalidades existentes
2. **Complexidade:** Algumas otimizações podem aumentar complexidade do código
3. **Manutenibilidade:** Código otimizado pode ser mais difícil de manter

### Mitigações
1. **Testes Extensivos:** Testar cada mudança isoladamente
2. **Versionamento:** Manter versões anteriores funcionais
3. **Documentação:** Documentar todas as mudanças
4. **Rollback:** Ter plano de rollback para cada fase

---

## 🎯 OBJETIVOS FINAIS

### Objetivo Realista
- **Latência alvo:** 80-120ms
- **Redução:** 30-55% da latência atual
- **Prazo:** 2-3 semanas (implementação gradual)

### Objetivo Otimista
- **Latência alvo:** 60-100ms
- **Redução:** 43-66% da latência atual
- **Prazo:** 3-4 semanas (com todas as fases)

### Limite Teórico
- **Latência mínima possível:** ~50-80ms (limitado por rede física)
- **Redução máxima:** 55-72% da latência atual
- **Requer:** Otimizações de código + melhor infraestrutura

---

## 📝 NOTAS IMPORTANTES

1. **Latência de Rede:** A maior parte da latência (~110ms) é física e não pode ser reduzida via código
2. **Trade-offs:** Algumas otimizações podem aumentar complexidade ou reduzir confiabilidade
3. **Testes Contínuos:** Medir latência após cada mudança para validar melhorias
4. **Documentação:** Manter este documento atualizado com resultados reais

---

## 🔄 PRÓXIMOS PASSOS

1. ✅ Commit das alterações atuais (feito)
2. ✅ Criar plano de melhoria (feito)
3. ⏭️ Implementar Fase 1 (Connection Pooling)
4. ⏭️ Testar e medir resultados
5. ⏭️ Decidir se continua para Fase 2

---

**Última atualização:** 2026-02-01  
**Status:** Planejamento completo, pronto para implementação

