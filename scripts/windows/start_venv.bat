@echo off
title Nex Chat Server (venv)

echo ========================================
echo   Nex Chat - IA Local com Memoria
echo   (Ambiente Virtual)
echo ========================================
echo.

cd /d D:/Nex

echo [1/4] Verificando ambiente virtual...
if not exist "venv" (
    echo [ERRO] venv nao encontrado!
    echo Execute primeiro: scripts/windows/setup_venv.bat
    pause
    exit /b 1
)
echo [OK] venv encontrado
echo.

echo [2/4] Ativando ambiente virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERRO] Falha ao ativar venv
    pause
    exit /b 1
)
echo [OK] Ambiente ativado
echo.

echo [3/4] Verificando dependencias...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo [ERRO] Dependencias nao instaladas!
    echo Execute: scripts/windows/setup_venv.bat
    pause
    exit /b 1
)
echo [OK] Dependencias OK
echo.

echo [4/4] Iniciando servidor...
echo.
echo Servidor disponivel em:
echo   - Web: http://localhost:8000
echo   - API: http://localhost:8000/ask
echo   - Metrics: http://localhost:8000/metrics
echo   - WebSocket: ws://localhost:8000/ws/chat
echo.
echo Pressione CTRL+C para parar
echo ========================================
echo.

python -m src.main