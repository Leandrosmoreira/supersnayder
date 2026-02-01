#!/bin/bash
# Script de Backup do Polymarket Bot
# Uso: ./backup.sh [tipo]
# Tipos: full (completo), code (apenas código), git (git commit)

BACKUP_DIR="/root/backups"
PROJECT_DIR="/root/polymarket-automated-mm"
DATE=$(date +%Y%m%d_%H%M%S)
TIPO=${1:-full}  # Default: full

mkdir -p $BACKUP_DIR

echo "═══════════════════════════════════════════════════════════"
echo "💾 BACKUP DO POLYMARKET BOT"
echo "═══════════════════════════════════════════════════════════"
echo "Tipo: $TIPO"
echo "Data: $(date)"
echo ""

case $TIPO in
    full)
        echo "📦 Criando backup COMPLETO (inclui .env e secrets)..."
        echo "⚠️  ATENÇÃO: Este backup contém informações sensíveis!"
        tar -czf $BACKUP_DIR/polymarket-full-$DATE.tar.gz \
            --exclude='venv' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.git' \
            -C /root polymarket-automated-mm/ 2>/dev/null
        echo "✅ Backup completo criado: $BACKUP_DIR/polymarket-full-$DATE.tar.gz"
        ;;
    
    code)
        echo "📦 Criando backup APENAS DO CÓDIGO (sem arquivos sensíveis)..."
        tar -czf $BACKUP_DIR/polymarket-codigo-$DATE.tar.gz \
            --exclude='.env' \
            --exclude='secrets' \
            --exclude='*.log' \
            --exclude='venv' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.git' \
            -C /root polymarket-automated-mm/ 2>/dev/null
        echo "✅ Backup de código criado: $BACKUP_DIR/polymarket-codigo-$DATE.tar.gz"
        ;;
    
    git)
        echo "📦 Fazendo commit no Git..."
        cd $PROJECT_DIR
        git add . 2>/dev/null
        git commit -m "Backup automático - $(date +%Y-%m-%d\ %H:%M:%S)" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✅ Commit criado com sucesso!"
            echo "💡 Para enviar ao GitHub: git push"
        else
            echo "⚠️  Nenhuma mudança para commitar"
        fi
        ;;
    
    zip)
        echo "📦 Criando ZIP do código..."
        cd /root
        zip -r $BACKUP_DIR/polymarket-codigo-$DATE.zip \
            polymarket-automated-mm/ \
            -x "polymarket-automated-mm/venv/*" \
            -x "polymarket-automated-mm/__pycache__/*" \
            -x "polymarket-automated-mm/*.log" \
            -x "polymarket-automated-mm/.env" \
            -x "polymarket-automated-mm/secrets/*" \
            -x "polymarket-automated-mm/.git/*" 2>/dev/null
        echo "✅ ZIP criado: $BACKUP_DIR/polymarket-codigo-$DATE.zip"
        ;;
    
    *)
        echo "❌ Tipo inválido: $TIPO"
        echo ""
        echo "Uso: ./backup.sh [tipo]"
        echo ""
        echo "Tipos disponíveis:"
        echo "  full  - Backup completo (inclui .env e secrets) ⚠️"
        echo "  code  - Apenas código (sem arquivos sensíveis) ✅"
        echo "  git   - Commit no Git"
        echo "  zip   - Criar arquivo ZIP do código"
        exit 1
        ;;
esac

echo ""
echo "📊 Tamanho dos backups:"
ls -lh $BACKUP_DIR/polymarket-*-$DATE.* 2>/dev/null | awk '{print "  " $5 " - " $9}'

echo ""
echo "✅ Backup concluído!"
echo "📁 Local: $BACKUP_DIR"

