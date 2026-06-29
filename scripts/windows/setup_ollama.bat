@echo off
echo ========================================
echo Setup Ollama + Orbyth 1.0 para Nex Chat
echo ========================================
echo.

echo [1/6] Verificando Ollama...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo Ollama nao encontrado. Baixando...
    powershell -Command "Invoke-WebRequest -Uri https://ollama.com/install.ps1 -OutFile ollama_install.ps1"
    powershell -ExecutionPolicy Bypass -File ollama_install.ps1
    del ollama_install.ps1 2>nul
) else (
    echo Ollama ja instalado!
)

echo.
echo [2/6] Baixando modelo Orbyth 1.0...
ollama pull orbith:1.0

echo.
echo [3/6] Verificando modelo...
ollama list | findstr orbith

echo.
echo [4/6] Configurando ambiente Nex Chat...
if not exist .env (
    if exist .env.example (
        copy .env.example .env
    )
)

echo.
echo [5/6] Atualizando dependencias...
pip install aiohttp

echo.
echo [6/6] Testando conexao...
python -c "import aiohttp; print('aiohttp OK: ' + aiohttp.__version__)"

echo.
echo ========================================
echo Setup concluido com sucesso!
echo.
echo Para iniciar modo local: scripts\windows\start_local.bat
echo ========================================
pause
