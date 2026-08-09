#!/bin/bash
# Script completo de validação do sistema

set -e

echo "=========================================="
echo "🔍 VALIDAÇÃO COMPLETA DO NEX CHAT"
echo "=========================================="

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Função para verificar status
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1 falhou${NC}"
        exit 1
    fi
}

# 1. Verifica dependências
echo ""
echo "📦 Verificando dependências..."

command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Python3 não encontrado${NC}"; exit 1; }
command -v ollama >/dev/null 2>&1 || { echo -e "${YELLOW}Ollama não encontrado. Instalando...${NC}"; ./scripts/install_ollama.sh; }

# 2. Verifica modelo
echo ""
echo "📥 Verificando modelo Gemma 2 2B..."

if ! ollama list | grep -q "gemma2:2b"; then
    echo -e "${YELLOW}Modelo não encontrado. Baixando...${NC}"
    ./scripts/download_model.sh
fi

# 3. Instala dependências Python
echo ""
echo "📦 Instalando dependências Python..."
pip install -r requirements.txt

# 4. Executa testes de integração
echo ""
echo "🧪 Executando testes de integração..."
python test_ollama_integration.py

# 5. Inicia servidor para teste rápido
echo ""
echo "🚀 Testando inicialização do servidor (5 segundos)..."
timeout 5 python -m src.main &
SERVER_PID=$!
sleep 3

if curl -s http://localhost:8000/api/stats > /dev/null; then
    echo -e "${GREEN}✅ Servidor respondendo${NC}"
else
    echo -e "${RED}❌ Servidor não respondeu${NC}"
fi

kill $SERVER_PID 2>/dev/null

# 6. Relatório final
echo ""
echo "=========================================="
echo -e "${GREEN}✅ VALIDAÇÃO CONCLUÍDA COM SUCESSO${NC}"
echo "=========================================="
echo ""
echo "Para iniciar o servidor:"
echo "  python -m src.main"
echo ""
echo "Ou com Docker:"
echo "  docker-compose up -d"
echo ""
echo "Acesse: http://localhost:8000"
