@echo off
REM Script completo de validacao do sistema (Windows)

echo ==========================================
echo VALIDACAO COMPLETA DO NEX CHAT
echo ==========================================

REM 1. Verifica Python
echo.
echo Verificando Python...
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo Python nao encontrado
    exit /b 1
)
echo Python encontrado

REM 2. Verifica Ollama
echo.
echo Verificando Ollama...
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo Ollama nao encontrado. Instalando...
    call scripts\install_ollama.bat
)

REM 3. Verifica modelo
echo.
echo Verificando modelo Gemma 2 2B...
ollama list | findstr "gemma2:2b" >nul
if %errorlevel% neq 0 (
    echo Modelo nao encontrado. Baixando...
    call scripts\download_model.bat
)

REM 4. Instala dependencias
echo.
echo Instalando dependencias Python...
pip install -r requirements.txt

REM 5. Executa testes
echo.
echo Executando testes de integracao...
python test_ollama_integration.py

echo.
echo ==========================================
echo VALIDACAO CONCLUIDA
echo ==========================================
echo.
echo Para iniciar o servidor:
echo   python -m src.main
echo.
echo Acesse: http://localhost:8000
