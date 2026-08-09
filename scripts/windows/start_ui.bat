@echo off
title Nex Chat - Inicializando
chcp 65001 >nul

set PROJECT_DIR=D:\Nex
set VENV_DIR=%PROJECT_DIR%\venv

REM === Verificar se venv existe ===
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [AVISO] Ambiente virtual nao encontrado.
    echo Executando correcao automatica...
    call "%PROJECT_DIR%\scripts\windows\fix_env.bat"
    if errorlevel 1 (
        echo [ERRO] Falha ao configurar ambiente. Execute fix_env.bat manualmente.
        pause
        exit /b 1
    )
)

echo ====================================
echo   Nex Chat - IA Local
echo ====================================
echo.

echo Iniciando API FastAPI...
start cmd /k "title Nex Chat - API && cd /d %PROJECT_DIR% && %VENV_DIR%\Scripts\activate && call :clean_env && python -m src.main"
echo Aguardando API iniciar...
timeout /t 5 /nobreak >nul
echo.
echo Iniciando Interface Streamlit...
echo Acesse: http://localhost:8501
echo.
start cmd /k "title Nex Chat - UI && cd /d %PROJECT_DIR% && %VENV_DIR%\Scripts\activate && call :clean_env && streamlit run streamlit_app.py --server.port 8501"
echo.
echo ====================================
echo   API: http://localhost:8000
echo   UI:  http://localhost:8501
echo ====================================
echo.
goto :eof

:clean_env
REM Remove variaveis que causam conflito com pacotes globais
set PYTHONPATH=
set PYTHONHOME=
goto :eof
