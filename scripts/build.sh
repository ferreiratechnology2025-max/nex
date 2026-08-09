#!/bin/bash
# Script de build para Linux/Mac

set -e

echo "🔨 Build do Nex Chat"
echo "===================="

# Cria diretórios necessários
mkdir -p data models templates static monitor

# Verifica dependências
command -v docker >/dev/null 2>&1 || { echo "❌ Docker não encontrado. Instale Docker primeiro."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ docker-compose não encontrado."; exit 1; }

# Build da imagem
echo "📦 Build da imagem Docker..."
docker-compose build

# Download de modelos (opcional)
if [ -n "$DOWNLOAD_MODEL" ]; then
    echo "📥 Baixando modelo Gemma 2 2B..."
    docker run --rm -v ollama-models:/root/.ollama ollama/ollama pull gemma2:2b
fi

echo "✅ Build concluído!"
echo ""
echo "Para iniciar: ./scripts/start.sh"
echo "Para parar:   ./scripts/stop.sh"
