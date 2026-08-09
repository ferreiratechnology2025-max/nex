@echo off
echo ========================================
echo   Configurando OpenRouter para Nex Chat
echo ========================================
echo.

echo [1/3] Instalando dependencias...
pip install httpx python-dotenv

echo.
echo [2/3] Criando arquivo .env...
if not exist ".env" (
    copy ".env.example" ".env"
    echo . Arquivo .env criado
) else (
    echo . .env ja existe, nao foi sobrescrito
)

echo.
echo [3/3] Configuracao finalizada!
echo.
echo ========================================
echo   PROXIMOS PASSOS:
echo ========================================
echo 1. Edite o arquivo .env
echo 2. Adicione sua API key: OPENROUTER_API_KEY=sua-chave
echo 3. Obtenha a chave em: https://openrouter.ai/keys
echo.
echo NOTA: Modelos free funcionam SEM API key
echo.
echo 4. Teste com:
echo    python -c "from src.config import get_settings; from src.core.openrouter_client import OpenRouterClient; s=get_settings(); c=OpenRouterClient(s.OPENROUTER_API_KEY, s.OPENROUTER_MODEL, s.OPENROUTER_FALLBACK_MODEL); import asyncio; print('Disponivel:', asyncio.run(c.is_available()))"
echo.
pause
