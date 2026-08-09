@echo off
REM Nex Local AI Assistant - Start Script (Windows)
REM Starts the server with optimizations from Nex.spec.md

REM Apply optimizations (Nex.spec.md Seção 3.3)
set OMP_NUM_THREADS=2
set MKL_NUM_THREADS=2
set TOKENIZERS_PARALLELISM=false

REM Create .env from example if not exists
if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
)

REM Change to project root (parent of scripts folder)
cd /d "%~dp0.."

REM Ensure data directory exists
if not exist data mkdir data
if not exist logs mkdir logs

REM Start the server
echo Starting Nex Local AI Assistant...
python -m src.main

pause