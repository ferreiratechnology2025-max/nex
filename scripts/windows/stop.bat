@echo off
REM Script de stop para Windows

echo 🛑 Parando Nex Chat...
echo ======================

docker-compose down

echo ✅ Nex Chat parado!
echo.
echo Para remover volumes (dados): docker-compose down -v
