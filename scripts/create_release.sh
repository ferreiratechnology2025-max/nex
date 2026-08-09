#!/bin/bash
# Script de criacao de release

set -e

VERSION="${1:-1.0.0}"
RELEASE_DIR="nex-chat-${VERSION}"
RELEASE_ZIP="${RELEASE_DIR}.zip"

echo "=========================================="
echo "Criando Release ${VERSION}"
echo "=========================================="

# Limpa releases anteriores
rm -rf ${RELEASE_DIR} ${RELEASE_ZIP}

# Cria diretorio de release
mkdir -p ${RELEASE_DIR}
mkdir -p ${RELEASE_DIR}/src/core
mkdir -p ${RELEASE_DIR}/templates
mkdir -p ${RELEASE_DIR}/static
mkdir -p ${RELEASE_DIR}/scripts
mkdir -p ${RELEASE_DIR}/scripts/windows
mkdir -p ${RELEASE_DIR}/docs
mkdir -p ${RELEASE_DIR}/monitor
mkdir -p ${RELEASE_DIR}/examples

# Copia arquivos principais
cp -r src/* ${RELEASE_DIR}/src/
cp -r templates/* ${RELEASE_DIR}/templates/
cp -r static/* ${RELEASE_DIR}/static/
cp -r scripts/*.sh ${RELEASE_DIR}/scripts/ 2>/dev/null || true
cp -r scripts/*.bat ${RELEASE_DIR}/scripts/ 2>/dev/null || true
cp -r scripts/windows/*.bat ${RELEASE_DIR}/scripts/windows/ 2>/dev/null || true
cp -r docs/* ${RELEASE_DIR}/docs/ 2>/dev/null || true
cp -r monitor/* ${RELEASE_DIR}/monitor/ 2>/dev/null || true
cp -r examples/* ${RELEASE_DIR}/examples/ 2>/dev/null || true

# Copia arquivos de configuracao
cp Dockerfile ${RELEASE_DIR}/
cp docker-compose.yml ${RELEASE_DIR}/
cp .dockerignore ${RELEASE_DIR}/
cp requirements.txt ${RELEASE_DIR}/
cp README.md ${RELEASE_DIR}/
cp Makefile ${RELEASE_DIR}/ 2>/dev/null || true

# Cria arquivo de versao
echo "{\"version\": \"${VERSION}\", \"release_date\": \"$(date -Iseconds)\"}" > ${RELEASE_DIR}/version.json

# Remove arquivos desnecessarios
find ${RELEASE_DIR} -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find ${RELEASE_DIR} -name "*.pyc" -delete 2>/dev/null || true
find ${RELEASE_DIR} -name ".DS_Store" -delete 2>/dev/null || true

# Cria zip
zip -r ${RELEASE_ZIP} ${RELEASE_DIR}

# Limpa diretorio temporario
rm -rf ${RELEASE_DIR}

echo ""
echo "Release criada: ${RELEASE_ZIP}"
echo "Tamanho: $(du -h ${RELEASE_ZIP} | cut -f1)"
echo ""
echo "Para usar:"
echo "  unzip ${RELEASE_ZIP}"
echo "  cd ${RELEASE_DIR}"
echo "  python -m src.main"
