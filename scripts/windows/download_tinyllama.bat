@echo off
setlocal enabledelayedexpansion

echo [Nex Chat] Baixando TinyLlama-1.1B-Chat GGUF...
echo.

REM Criar pasta models se nao existir
mkdir models 2>nul

set MODEL_NAME=tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
set DOWNLOAD_URL=https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/%MODEL_NAME%

echoBaixando: %MODEL_NAME%
echoDe: %DOWNLOAD_URL%
echo.

powershell -Command "Invoke-WebRequest -Uri '%DOWNLOAD_URL%' -OutFile 'models\%MODEL_NAME%' -UseBasicParsing"

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Falha no download.
    echo.
    echo Tente baixar manualmente em:
    echo https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF
    echo.
    echo Depois mova o arquivo para: models\%MODEL_NAME%
    exit /b 1
)

echo.
echo [OK] Modelo baixado: models\%MODEL_NAME%
echo.
echo [INFO] Configure no .env:
echo    LOCAL_MODEL_PATH=models\%MODEL_NAME%
echo.
echo Reinicie o servidor para usar o modelo local.
echo.

endlocal
pause