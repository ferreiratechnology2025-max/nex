@echo off
echo ========================================
echo   Validacao do Sistema Nex Chat
echo ========================================
echo.

cd /d D:\Nex

echo [1/5] Verificando Python...
python --version
if errorlevel 1 (
    echo [ERRO] Python nao encontrado
    pause
    exit /b 1
)
echo [OK] Python OK
echo.

echo [2/5] Verificando dependencias...
pip list | findstr "fastapi" > nul
if errorlevel 1 (
    echo [ERRO] Dependencias nao instaladas
    echo Execute: pip install -r requirements.txt
    pause
    exit /b 1
)
echo [OK] Dependencias OK
echo.

echo [3/5] Verificando arquivo .env...
if not exist ".env" (
    echo [AVISO] Arquivo .env nao encontrado
    echo Copiando .env.example...
    copy .env.example .env
    echo [AVISO] Edite o arquivo .env com sua API key
)
echo [OK] .env OK
echo.

echo [4/5] Verificando diretorios...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
echo [OK] Diretorios OK
echo.

echo [5/5] Testando conexao OpenRouter...
python -c "from src.config import get_settings; from src.core.openrouter_client import OpenRouterClient; s=get_settings(); c=OpenRouterClient(s.OPENROUTER_API_KEY, s.OPENROUTER_MODEL, s.OPENROUTER_FALLBACK_MODEL); import asyncio; print('[OK] OpenRouter disponivel' if asyncio.run(c.is_available()) else '[AVISO] OpenRouter nao configurado')"
echo.

echo ========================================
echo   Validacao Concluida!
echo ========================================
echo.
echo Para iniciar o servidor:
echo   scripts\windows\start.bat
echo.
pause