@echo off
REM Script para baixar o modelo Gemma 2 2B (Windows)

set MODEL_NAME=%1
if "%MODEL_NAME%"=="" set MODEL_NAME=gemma2:2b

echo ==========================================
echo Baixando modelo: %MODEL_NAME%
echo ==========================================

REM Verifica se Ollama esta rodando
curl -s http://localhost:11434/api/tags >nul 2>nul
if %errorlevel% neq 0 (
    echo Ollama nao esta rodando. Iniciando...
    start "" ollama serve
    timeout /t 5 /nobreak >nul
)

REM Verifica se modelo ja existe
ollama list | findstr "%MODEL_NAME%" >nul
if %errorlevel% equ 0 (
    echo Modelo %MODEL_NAME% ja esta disponivel
    ollama list | findstr "%MODEL_NAME%"
    exit /b 0
)

echo Baixando %MODEL_NAME% (isso pode levar alguns minutos)...
ollama pull %MODEL_NAME%

echo Modelo baixado com sucesso!
ollama list | findstr "%MODEL_NAME%"
