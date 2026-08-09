@echo off
echo ========================================
echo   Validacao do Sistema Nex Chat (venv)
echo ========================================
echo.

cd /d D:/Nex

echo [1/5] Verificando Python...
python --version
echo [OK] Python OK
echo.

echo [2/5] Verificando ambiente virtual...
if not exist "venv" (
    echo [ERRO] venv nao encontrado
    echo Execute: scripts/windows/setup_venv.bat
    pause
    exit /b 1
)
echo [OK] venv encontrado
echo.

echo [3/5] Ativando ambiente virtual...
call venv\Scripts\activate.bat
echo [OK] Ambiente ativado
echo.

echo [4/5] Verificando dependencias...
python -c "import fastapi, uvicorn, pydantic, transformers, sentence_transformers, faiss" 2>nul
if errorlevel 1 (
    echo [ERRO] Dependencias nao instaladas
    echo Execute: scripts/windows/setup_venv.bat
    pause
    exit /b 1
)
echo [OK] Dependencias OK
echo.

echo [5/5] Testando conexao com OpenRouter...
python -c "from src.config import get_settings; from src.core.openrouter_client import OpenRouterClient; s=get_settings(); c=OpenRouterClient(s.OPENROUTER_API_KEY, s.OPENROUTER_MODEL, s.OPENROUTER_FALLBACK_MODEL); import asyncio; print('[OK] OpenRouter disponivel' if asyncio.run(c.is_available()) else '[AVISO] OpenRouter nao disponivel')"
echo.

echo ========================================
echo   Validacao Concluida!
echo ========================================
echo.
echo Para iniciar o servidor:
echo   scripts/windows/start_venv.bat
echo.
pause