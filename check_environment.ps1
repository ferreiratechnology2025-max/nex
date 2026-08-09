# Script de verificação do ambiente Nex Chat
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🔍 Verificando Ambiente Nex Chat" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Python
Write-Host "`n📦 Python:" -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Python não encontrado no PATH" -ForegroundColor Red
}

# 2. Ollama
Write-Host "`n🤖 Ollama:" -ForegroundColor Yellow
$ollamaPaths = @(
    "C:\Program Files\Ollama\ollama.exe",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Ollama\ollama.exe"
)

$ollamaFound = $false
foreach ($path in $ollamaPaths) {
    if (Test-Path $path) {
        Write-Host "  ✅ Encontrado em: $path" -ForegroundColor Green
        $ollamaFound = $true
        break
    }
}

if (-not $ollamaFound) {
    Write-Host "  ❌ Ollama não encontrado" -ForegroundColor Red
} else {
    # Tentar executar
    try {
        $ollamaVersion = & "C:\Program Files\Ollama\ollama.exe" --version 2>&1
        Write-Host "  📌 Versão: $ollamaVersion" -ForegroundColor Gray
        
        # Listar modelos
        $models = & "C:\Program Files\Ollama\ollama.exe" list 2>&1
        Write-Host "  📌 Modelos disponíveis:" -ForegroundColor Gray
        $models | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }
    } catch {
        Write-Host "  ⚠️ Ollama não está rodando" -ForegroundColor Yellow
    }
}

# 3. Docker
Write-Host "`n🐳 Docker:" -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "  ✅ $dockerVersion" -ForegroundColor Green
    
    $dockerStatus = docker ps 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Docker está rodando" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ Docker Desktop não está rodando" -ForegroundColor Yellow
        Write-Host "     Inicie manualmente pelo menu Iniciar" -ForegroundColor Gray
    }
} catch {
    Write-Host "  ❌ Docker não encontrado" -ForegroundColor Red
}

# 4. Dependências Python
Write-Host "`n📚 Dependências Python:" -ForegroundColor Yellow
$required = @("fastapi", "uvicorn", "requests", "sentence-transformers")
foreach ($pkg in $required) {
    $check = python -c "import $pkg" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ $pkg" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $pkg (instale com: pip install $pkg)" -ForegroundColor Red
    }
}

# 5. Arquivos do Projeto
Write-Host "`n📁 Arquivos do Projeto:" -ForegroundColor Yellow
$files = @(
    "src\main.py",
    "src\core\memory_manager.py",
    "src\core\llm_manager.py",
    "templates\index.html",
    "requirements.txt"
)

foreach ($file in $files) {
    if (Test-Path "D:\Nex\$file") {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file" -ForegroundColor Red
    }
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "✅ Verificação concluída!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan