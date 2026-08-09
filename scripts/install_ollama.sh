#!/bin/bash
# Script de instalação do Ollama para Linux/Mac

set -e

echo "=========================================="
echo "📦 Instalando Ollama"
echo "=========================================="

# Detecta sistema operacional
OS="$(uname -s)"
ARCH="$(uname -m)"

case "${OS}" in
    Linux*)
        echo "🟢 Detected Linux"
        curl -fsSL https://ollama.com/install.sh | sh
        ;;
    Darwin*)
        echo "🍎 Detected macOS"
        if [[ "${ARCH}" == "arm64" ]]; then
            curl -L https://ollama.com/download/Ollama-darwin-arm64.zip -o /tmp/ollama.zip
            unzip /tmp/ollama.zip -d /Applications/
        else
            curl -L https://ollama.com/download/Ollama-darwin-x86_64.zip -o /tmp/ollama.zip
            unzip /tmp/ollama.zip -d /Applications/
        fi
        ;;
    *)
        echo "❌ Sistema não suportado: ${OS}"
        exit 1
        ;;
esac

# Inicia serviço
echo "🚀 Iniciando Ollama..."
ollama serve > /dev/null 2>&1 &

# Aguarda inicialização
sleep 3

echo "✅ Ollama instalado e rodando!"
ollama --version
