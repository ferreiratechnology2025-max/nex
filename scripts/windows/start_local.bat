@echo off
echo ========================================
echo Nex Chat - Modo 100%% Local (Ollama)
echo ========================================
echo.

echo [1/4] Verificando Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo Iniciando Ollama...
    start /B ollama serve
    timeout /t 5 /nobreak >nul
)

echo [2/4] Verificando modelo...
ollama list | findstr orbith:1.0 >nul
if errorlevel 1 (
    echo Baixando modelo Orbyth 1.0...
    ollama pull orbith:1.0
)

echo [3/4] Iniciando servidor Nex Chat...
cd /d "%~dp0../.."
set OLLAMA_ENABLED=true
set OLLAMA_MODEL=orbith:1.0
set OPENROUTER_ENABLED=false
set USE_OLLAMA_EMBEDDINGS=true

echo [4/4] Servidor pronto!
echo.
echo Acesse:
echo   API: http://localhost:8000
echo   UI:  http://localhost:8501
echo.
echo Pressione Ctrl+C para parar
echo.

python -m src.main
pause
