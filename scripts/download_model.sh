#!/bin/bash
# Script para baixar o modelo Gemma 2 2B

set -e

MODEL_NAME="${1:-gemma2:2b}"

echo "=========================================="
echo "📥 Baixando modelo: ${MODEL_NAME}"
echo "=========================================="

# Verifica se Ollama está rodando
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️ Ollama não está rodando. Iniciando..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# Verifica se modelo já existe
if ollama list | grep -q "${MODEL_NAME}"; then
    echo "✅ Modelo ${MODEL_NAME} já está disponível"
    ollama list | grep "${MODEL_NAME}"
    exit 0
fi

# Download do modelo
echo "⏳ Baixando ${MODEL_NAME} (isso pode levar alguns minutos)..."
ollama pull ${MODEL_NAME}

echo "✅ Modelo baixado com sucesso!"
ollama list | grep "${MODEL_NAME}"

# Informações do modelo
echo ""
echo "📊 Informações do modelo:"
ollama show ${MODEL_NAME}
