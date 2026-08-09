@echo off
echo ========================================
echo   Executando Testes (venv)
echo ========================================
echo.

cd /d D:/Nex

call venv\Scripts\activate.bat

echo Instalando dependencias de teste...
python -m pip install pytest pytest-asyncio pytest-cov

echo.
echo Executando testes...
pytest tests/ -v --tb=short

echo.
echo ========================================
echo   Testes Concluidos!
echo ========================================
pause