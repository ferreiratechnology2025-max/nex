#!/bin/bash
# Script de start para Linux/Mac

set -e

echo "🚀 Iniciando Nex Chat..."
echo "========================"

# Verifica se o container já está rodando
if docker-compose ps | grep -q "Up"; then
    echo "⚠️ Nex Chat já está rodando!"
    docker-compose ps
    exit 0
fi

# Inicia os serviços
docker-compose up -d

# Aguarda o serviço ficar saudável
echo "⏳ Aguardando inicialização..."
sleep 5

# Verifica status
echo ""
echo "✅ Nex Chat rodando!"
echo ""
echo "📊 Status dos serviços:"
docker-compose ps
echo ""
echo "🌐 Interface Web: http://localhost:8000"
echo "📡 API Docs:      http://localhost:8000/docs"
echo "📊 Monitor:       http://localhost:8080 (se habilitado)"
echo ""
echo "📋 Logs: docker-compose logs -f"
echo "🛑 Parar: ./scripts/stop.sh"
