#!/bin/bash
# Docker Entrypoint para Nex Chat

set -e

echo "=========================================="
echo "🧠 Nex Chat - Inicializando..."
echo "=========================================="

# Verifica se Ollama está rodando (se não estiver, inicia)
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "📦 Iniciando Ollama em background..."
    ollama serve &
    
    # Aguarda Ollama iniciar
    echo "⏳ Aguardando Ollama inicializar..."
    sleep 5
    
    # Verifica se o modelo existe, se não, baixa
    if ! ollama list | grep -q "$MODEL_NAME"; then
        echo "📥 Baixando modelo $MODEL_NAME..."
        ollama pull $MODEL_NAME
    fi
else
    echo "✅ Ollama já está rodando"
fi

# Verifica se o modelo está disponível
if ollama list | grep -q "$MODEL_NAME"; then
    echo "✅ Modelo $MODEL_NAME disponível"
else
    echo "⚠️ Modelo $MODEL_NAME não encontrado. Continuando sem ele..."
fi

echo "=========================================="
echo "🚀 Iniciando Nex Chat..."
echo "🌐 Interface: http://localhost:8000"
echo "📡 API Docs: http://localhost:8000/docs"
echo "=========================================="

# Executa o comando principal
exec "$@"
