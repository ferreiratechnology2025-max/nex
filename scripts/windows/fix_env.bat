@echo off
title Nex Chat - Corrigir Ambiente
chcp 65001 >nul

set PROJECT_DIR=D:\Nex
set VENV_DIR=%PROJECT_DIR%\venv

echo ============================================
echo   Nex Chat - Correcao Automatica de Ambiente
echo ============================================
echo.

REM === 1. Verificar Python ===
echo [1/7] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH
    pause
    exit /b 1
)
for /f %%I in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set PY_VER=%%I
echo [OK] Python %PY_VER% encontrado
echo.

REM === 2. Remover venv antigo ===
echo [2/7] Removendo ambiente virtual anterior...
if exist "%VENV_DIR%" (
    rmdir /s /q "%VENV_DIR%"
    echo [OK] Antigo venv removido
) else (
    echo [OK] Nenhum venv anterior encontrado
)
echo.

REM === 3. Criar novo venv ===
echo [3/7] Criando novo ambiente virtual...
python -m venv "%VENV_DIR%"
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [ERRO] Falha ao criar venv
    pause
    exit /b 1
)
echo [OK] Venv criado em %VENV_DIR%
echo.

REM === 4. Ativar venv e atualizar pip ===
echo [4/7] Atualizando pip, setuptools e wheel...
call "%VENV_DIR%\Scripts\activate.bat"
python -m pip install --upgrade pip setuptools wheel --quiet
if errorlevel 1 (
    echo [AVISO] Falha ao atualizar pip (continuando)
) else (
    echo [OK] Pip atualizado
)
echo.

REM === 5. Remover pacotes conflitantes GLOBAIS ===
echo [5/7] Removendo pacotes conflitantes...
pip uninstall multipart python-multipart pydantic -y >nul 2>&1
echo [OK] Conflitos globais removidos
echo.

REM === 6. Instalar dependencias do projeto ===
echo [6/7] Instalando dependencias corrigidas...
cd /d "%PROJECT_DIR%"
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas com sucesso
echo.

REM === 7. Verificacao final ===
echo [7/7] Verificando imports criticos...
set IMPORTS_OK=1

python -c "from pydantic import BaseModel, Field, field_validator; print('  [OK] pydantic v2')" 2>nul || (echo '  [FALHA] pydantic v2' && set IMPORTS_OK=0)
python -c "from fastapi import FastAPI, UploadFile; print('  [OK] fastapi')" 2>nul || (echo '  [FALHA] fastapi' && set IMPORTS_OK=0)
python -c "import streamlit; print('  [OK] streamlit')" 2>nul || (echo '  [FALHA] streamlit' && set IMPORTS_OK=0)
python -c "from src.config import Settings; print('  [OK] src.config (pydantic-settings)')" 2>nul || (echo '  [FALHA] src.config' && set IMPORTS_OK=0)

echo.
if "%IMPORTS_OK%"=="1" (
    echo ============================================
    echo   CORRECAO CONCLUIDA COM SUCESSO!
    echo ============================================
    echo.
    echo Para iniciar:
    echo   scripts\windows\start_ui.bat
    echo.
    echo Ou manualmente:
    echo   venv\Scripts\activate ^&^& python -m src.main
) else (
    echo [ERRO] Alguns imports falharam. Verifique os logs acima.
)
echo.
pause
