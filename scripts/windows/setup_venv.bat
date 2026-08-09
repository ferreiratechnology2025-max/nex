@echo off
title Nex Chat - Setup Ambiente Virtual

echo ========================================
echo   Nex Chat - Setup Ambiente Virtual
echo ========================================
echo.

cd /d D:/Nex

echo [1/6] Verificando Python...
python --version
if errorlevel 1 (
    echo [ERRO] Python nao encontrado
    pause
    exit /b 1
)
echo [OK] Python OK
echo.

echo [2/6] Removendo venv antigo (se existir)...
if exist "venv" (
    echo Removendo pasta venv...
    rmdir /s /q venv
)
echo [OK]
echo.

echo [3/6] Criando novo ambiente virtual...
python -m venv venv
if not exist "venv" (
    echo [ERRO] Falha ao criar venv
    pause
    exit /b 1
)
echo [OK] venv criado em D:/Nex/venv
echo.

echo [4/6] Ativando ambiente virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERRO] Falha ao ativar venv
    pause
    exit /b 1
)
echo [OK] Ambiente ativado
echo.

echo [5/6] Atualizando pip dentro do venv...
python -m pip install --upgrade pip
echo [OK] Pip atualizado
echo.

echo [6/6] Instalando dependencias do projeto...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas
echo.

echo ========================================
echo   Setup Concluido com Sucesso!
echo ========================================
echo.
echo Para ATIVAR o ambiente virtual:
echo   venv\Scripts\activate
echo.
echo Para INICIAR o servidor:
echo   python -m src.main
echo.
echo OU use o script:
echo   scripts/windows/start_venv.bat
echo.
pause