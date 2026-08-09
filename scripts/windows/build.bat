@echo off
REM Script de build para Windows

echo 🔨 Build do Nex Chat
echo ====================

REM Cria diretórios necessários
if not exist data mkdir data
if not exist models mkdir models
if not exist templates mkdir templates
if not exist static mkdir static
if not exist monitor mkdir monitor

REM Verifica Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker não encontrado. Instale Docker Desktop primeiro.
    exit /b 1
)

REM Build da imagem
echo 📦 Build da imagem Docker...
docker-compose build

echo ✅ Build concluído!
echo.
echo Para iniciar: scripts\windows\start.bat
echo Para parar:   scripts\windows\stop.bat
