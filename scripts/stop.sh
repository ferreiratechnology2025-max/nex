#!/bin/bash
# Script de stop para Linux/Mac

echo "🛑 Parando Nex Chat..."
echo "======================"

docker-compose down

echo "✅ Nex Chat parado!"
echo ""
echo "Para remover volumes (dados): docker-compose down -v"
