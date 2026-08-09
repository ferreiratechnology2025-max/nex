@echo off
REM Script de instalacao do Ollama para Windows

echo ==========================================
echo Instalando Ollama
echo ==========================================

REM Verifica se ja esta instalado
where ollama >nul 2>nul
if %errorlevel% equ 0 (
    echo Ollama ja esta instalado
    ollama --version
    exit /b 0
)

echo Baixando Ollama...
curl -L https://ollama.com/download/OllamaSetup.exe -o %TEMP%\OllamaSetup.exe

echo Instalando...
start /wait %TEMP%\OllamaSetup.exe /S

echo Ollama instalado!
ollama --version

echo Iniciando Ollama...
start "" ollama serve

echo Aguardando inicializacao...
timeout /t 5 /nobreak >nul

echo Pronto!
