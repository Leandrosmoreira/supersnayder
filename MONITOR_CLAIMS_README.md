# Monitor de Claims - Polymarket

Script que monitora posições claimables e envia notificações quando há claims disponíveis.

## Uso Básico

### Executar uma vez (útil para cron)

```bash
python monitor_claims.py --once
```

### Executar continuamente (monitoramento em tempo real)

```bash
python monitor_claims.py --interval 300
```

Isso verifica a cada 5 minutos (300 segundos).

### Com notificações Discord

```bash
python monitor_claims.py --interval 300 --discord-webhook https://discord.com/api/webhooks/...
```

## Configuração

### Variáveis de Ambiente

No seu `.env`:

```bash
CLAIMER_WALLET_ADDRESS=0xYourWalletAddress
# ou
BROWSER_ADDRESS=0xYourWalletAddress

# Opcional: Discord webhook para notificações
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

## Automação com Cron

### Verificar a cada hora

```bash
# Editar crontab
crontab -e

# Adicionar linha (verifica às :00 de cada hora)
0 * * * * cd /root/polymarket-automated-mm && /root/polymarket-automated-mm/venv/bin/python monitor_claims.py --once >> monitor_claims_cron.log 2>&1
```

### Verificar a cada 30 minutos

```bash
*/30 * * * * cd /root/polymarket-automated-mm && /root/polymarket-automated-mm/venv/bin/python monitor_claims.py --once >> monitor_claims_cron.log 2>&1
```

### Verificar a cada 15 minutos

```bash
*/15 * * * * cd /root/polymarket-automated-mm && /root/polymarket-automated-mm/venv/bin/python monitor_claims.py --once >> monitor_claims_cron.log 2>&1
```

## Rodar em Background

```bash
# Rodar em background
nohup python monitor_claims.py --interval 300 > monitor_claims.log 2>&1 &

# Ver logs
tail -f monitor_claims.log

# Parar
pkill -f monitor_claims.py
```

## Exemplo de Saída

```
================================================================================
🎯 NOVOS CLAIMS DISPONÍVEIS!
================================================================================
💰 Total a resgatar: $9.96
📊 Posições claimables: 1

  [1] Bitcoin Up or Down - February 1, 2:15PM-2:30PM ET
       Outcome: Down | $9.96

🔗 Resgatar em: https://polymarket.com/portfolio
================================================================================
```

## Notificações Discord

Para receber notificações no Discord:

1. Crie um webhook no seu servidor Discord:
   - Server Settings → Integrations → Webhooks → New Webhook
   - Copie a URL do webhook

2. Use o parâmetro `--discord-webhook`:

```bash
python monitor_claims.py --interval 300 --discord-webhook https://discord.com/api/webhooks/SEU_WEBHOOK_AQUI
```

Ou adicione no `.env`:

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/SEU_WEBHOOK_AQUI
```

E use:

```bash
python monitor_claims.py --interval 300 --discord-webhook $DISCORD_WEBHOOK_URL
```

## Logs

Os logs são salvos em:
- `monitor_claims.log` - Log principal
- Console (stdout) - Notificações importantes

## Troubleshooting

### "Nenhum claim disponível"
- Mercados podem ainda não estar resolvidos
- Claims podem já ter sido resgatados
- Verifique manualmente em https://polymarket.com/portfolio

### Notificações Discord não funcionam
- Verifique se a URL do webhook está correta
- Verifique se o webhook ainda está ativo no Discord
- Veja os logs para erros

### Script para de funcionar
- Verifique os logs: `tail -f monitor_claims.log`
- Verifique se o processo está rodando: `ps aux | grep monitor_claims`
- Reinicie se necessário

## Integração com Auto-Claim

Se você tiver uma carteira tradicional (não Magic Link), pode combinar:

```bash
# Terminal 1: Monitor (avisa quando há claims)
python monitor_claims.py --interval 300

# Terminal 2: Auto-claim (executa quando há claims)
# Você pode criar um script que roda auto_claim.py quando monitor detecta claims
```

