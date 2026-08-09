@echo off
title Nex Chat Server
setlocal enabledelayedexpansion

echo ========================================
echo   Nex Chat - IA Local com Memoria
echo ========================================
echo.

cd /d D:\Nex

echo [1/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado
    pause
    exit /b 1
)

echo [2/4] Verificando ambiente virtual...
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
)

echo [3/4] Ativando ambiente virtual e install dependencias...
call venv\Scripts\activate.bat >nul 2>&1
pip install -r requirements.txt >nul 2>&1

echo [4/4] Iniciando servidor...
echo.
echo ========================================
echo   Servidor disponivel em:
echo ========================================
echo   - Web:       http://localhost:8000
echo   - API:       http://localhost:8000/ask
echo   - Health:    http://localhost:8000/health
echo   - Metrics:   http://localhost:8000/metrics
echo   - WebSocket: ws://localhost:8000/ws/chat
echo.
echo   Pressione CTRL+C para parar
echo ========================================
echo.

python -m src.main

pause