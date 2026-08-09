# Recomendações para .gitignore

**Estado atual (verificado):** `.gitignore` existe no disco (290 bytes) mas
está **untracked** (`git status --porcelain -- .gitignore` → `?? .gitignore`).
Nunca foi commitado. Suas regras (abaixo) nunca estiveram em vigor do ponto
de vista do git para um clone fresco do repositório — só protegeram quem já
tinha esse arquivo localmente. Conteúdo atual:

```gitignore
# Environment variables
.env
.env.local
.env.*.local

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/

# Data
data/memoria.db
data/memoria.db-*
data/*.index

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Test
.pytest_cache/
.coverage
htmlcov/
```

**Ação recomendada prioritária:** `git add .gitignore` deve ser o primeiro
comando da Fase 8.2, antes de qualquer outro `git add`, para que as regras
abaixo (adicionais às já existentes) tenham efeito real a partir desse
commit.

## Entradas recomendadas, com base na classificação KEEP-UNTRACKED

```gitignore
# Ambiente virtual
venv/

# Dados de runtime (persistência real, não código)
data/

# Scripts de debug/smoke-test manuais (sem asserts, não fazem parte da suíte oficial)
tests/debug_test.py
tests/quick_test.py

# Bytecode Python (já deve existir, mas confirmar)
__pycache__/
*.pyc

# Bancos SQLite/WAL soltos na raiz (defesa contra recorrência do bug
# corrigido nas Etapas 4-5 da Fase 7 — caso algum script futuro volte a
# criar um órfão por engano, ele não entra no controle de versão)
/memoria.db
/memoria.db-shm
/memoria.db-wal
/memoria.index
```

## Itens a remover do disco (não do .gitignore — DELETE, Fase 8.2)

```
test_orch.py       # credencial hardcoded — ver classificacao_root.md
test_memory/       # resíduo órfão — ver classificacao_artifacts.md
```

## Item a mover, não a deletar (ARCHIVE)

```
CLAUDE.md   # mover para archive/ ou reescrever do zero para descrever o
            # projeto Nex real, antes de qualquer promoção futura
```

## Itens a promover via `git add` (PROMOTE — Fase 8.2, após aprovação)

Ver lista completa em `03_resumo/SUMMARY.md`. Resumo por grupo:
- Todo `src/agents/*.py` (5 arquivos) e `src/core/*.py` restantes (7
  arquivos) + `src/metrics.py` + `src/ws_handler.py`
- 8 de 10 arquivos de `tests/*.py`
- `docker-compose.yml`, `pytest.ini`
- `monitor/index.html`, `.streamlit/config.toml`
- `requirements.txt`, `README.md`, `SYSTEM_MAP.md`, `Nex.spec.md`

## Nota de precaução para a Fase 8.2

Antes de qualquer `git add`, recomenda-se rodar novamente
`grep -rn "api_key\|secret\|token\|password"` (mesmo padrão da Fase 7,
Etapa 1) sobre o conjunto de arquivos PROMOTE, para garantir que nenhum
outro segredo hardcoded (como o encontrado em `test_orch.py`) escape para
o histórico do git no momento do commit. O achado de `test_orch.py` prova
que a auditoria original (Fase 7) não cobriu 100% dos arquivos untracked —
só cobriu os dois que já haviam sido identificados por outro motivo
(erro de importação do GenerationConfig).
