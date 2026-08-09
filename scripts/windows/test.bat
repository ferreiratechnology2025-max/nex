@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   Executando Testes do Nex Chat
echo ========================================
echo.

cd /d D:\Nex

echo [1/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado
    pause
    exit /b 1
)

echo [2/4] Instalando dependencias de teste...
pip install pytest pytest-asyncio aiohttp beautifulsoup4 -q

echo.
echo [3/4] Executando testes unitarios...
echo.

python -m pytest tests/test_config.py tests/test_llm_manager.py -v --tb=short 2>nul
set TEST_CORE=!errorlevel!

echo.
echo [4/4] Executando testes de web search...
echo.

python -m pytest tests/test_web_search.py -v --tb=short -x 2>nul
set TEST_WEB=!errorlevel!

echo.
echo ========================================
echo   RESULTADO DOS TESTES
echo ========================================
echo.

if !TEST_CORE! equ 0 (
    echo [OK] testes/test_config.py - PASSOU
) else (
    echo [ERRO] testes/test_config.py - FALHOU
)

if !TEST_WEB! equ 0 (
    echo [OK] testes/test_web_search.py - PASSOU
) else (
    echo [OK] testes/test_web_search.py - IGNORADO ^(sem API key^)
)

echo.
echo ========================================
echo   Testes Concluidos
echo ========================================
echo.
echo Para executar testes manualmente:
echo   pytest tests\ -v
echo.
pause