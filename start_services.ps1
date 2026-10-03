# Script para iniciar serviços e baixar modelo
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 Iniciando Ambiente Nex Chat" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Verificar e iniciar Ollama
Write-Host "`n🤖 Ollama:" -ForegroundColor Yellow
$ollamaPath = "C:\Users\becat\AppData\Local\Programs\Ollama\ollama.exe"

if (Test-Path $ollamaPath) {
    Write-Host "  ✅ Ollama encontrado em: $ollamaPath" -ForegroundColor Green
    
    # Tentar listar modelos
    try {
        $models = & $ollamaPath list 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ Ollama está rodando" -ForegroundColor Green
            Write-Host "  📌 Modelos disponíveis:" -ForegroundColor Gray
            $models | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }
        } else {
            Write-Host "  ⚠️ Ollama não está rodando" -ForegroundColor Yellow
            Write-Host "  💡 Inicie o Ollama manualmente:" -ForegroundColor Gray
            Write-Host "     1. Abra o menu Iniciar" -ForegroundColor Gray
            Write-Host "     2. Procure por 'Ollama'" -ForegroundColor Gray
            Write-Host "     3. Clique para abrir" -ForegroundColor Gray
            Write-Host "     4. Ou execute: Start-Process '$ollamaPath'" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  ⚠️ Erro ao verificar Ollama" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ Ollama não encontrado" -ForegroundColor Red
}

# 2. Verificar Docker
Write-Host "`n🐳 Docker:" -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "  ✅ $dockerVersion" -ForegroundColor Green
    
    $dockerStatus = docker ps 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Docker está rodando" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ Docker Desktop não está rodando" -ForegroundColor Yellow
        Write-Host "  💡 Inicie o Docker Desktop manualmente:" -ForegroundColor Gray
        Write-Host "     1. Abra o menu Iniciar" -ForegroundColor Gray
        Write-Host "     2. Procure por 'Docker Desktop'" -ForegroundColor Gray
        Write-Host "     3. Clique para abrir" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ❌ Docker não encontrado" -ForegroundColor Red
}

# 3. Verificar Python
Write-Host "`n📦 Python:" -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Python não encontrado" -ForegroundColor Red
}

# 4. Verificar dependências
Write-Host "`n📚 Dependências Python:" -ForegroundColor Yellow
$required = @("fastapi", "uvicorn", "requests", "sentence-transformers")
$allInstalled = $true
foreach ($pkg in $required) {
    $check = python -c "import $pkg" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $pkg" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $pkg" -ForegroundColor Red
        $allInstalled = $false
    }
}

if (-not $allInstalled) {
    Write-Host "`n  💡 Para instalar dependências:" -ForegroundColor Gray
    Write-Host "     python -m pip install -r D:\Nex\requirements.txt" -ForegroundColor Gray
}

# 5. Instruções para baixar modelo
Write-Host "`n📥 Baixar Modelo:" -ForegroundColor Yellow
Write-Host "  💡 Escolha um modelo aberto e leve:" -ForegroundColor Gray
Write-Host "     ollama pull llama3.2:1b" -ForegroundColor Cyan
Write-Host "     ollama pull phi3:mini" -ForegroundColor Cyan
Write-Host "     ollama pull tinyllama:1.1b" -ForegroundColor Cyan

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "✅ Verificação concluída!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

Write-Host "`n🎯 Próximos passos:" -ForegroundColor Yellow
Write-Host "  1. Inicie o Docker Desktop (menu Iniciar)" -ForegroundColor Gray
Write-Host "  2. Inicie o Ollama (menu Iniciar)" -ForegroundColor Gray
Write-Host "  3. Baixe um modelo: ollama pull llama3.2:1b" -ForegroundColor Gray
Write-Host "  4. Execute: cd D:\Nex && python -m src.main" -ForegroundColor Gray