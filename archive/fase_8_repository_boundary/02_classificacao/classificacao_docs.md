# Classificação — Documentação/manifesto untracked (6 arquivos)

## .gitignore — ACHADO CRÍTICO DE PROCESSO
- **Status:** `git status --porcelain -- .gitignore` → `?? .gitignore`.
  O próprio arquivo de exclusão do git **nunca foi commitado**.
- **Consequência factual:** nenhuma das regras nele definidas jamais foi
  aplicada a um clone fresco deste repositório. `.env` está listado nele
  (`# Environment variables\n.env`), mas isso só protege quem já tem esse
  `.gitignore` no working copy local — nunca esteve em vigor do ponto de
  vista do git em si.
- **Conteúdo já presente (avaliado):** cobre `.env`, `__pycache__/`,
  `*.pyc`, `data/memoria.db`, `data/memoria.db-*`, `data/*.index`,
  `logs/`, `*.log`, `.pytest_cache/`. NÃO cobre `venv/`, `.streamlit/`
  (que classificamos PROMOTE, então não precisaria mesmo), `test_memory/`,
  nem os padrões de órfão na raiz (`/memoria.db`, `/memoria.index`)
  recomendados em `recomendacoes_gitignore.md`.
- **Nota de grep:** este arquivo escapou do grep original desta etapa
  (`\.(md|txt|pdf|docx)$` não captura `.gitignore`) — corrigido aqui.
- **Valor:** CRÍTICO — sem ele versionado, o próximo `git add -A` de
  qualquer colaborador arrisca commitar `venv/`, `data/memoria.db`
  (binário com dados de usuário) ou `.env` (que já vazou uma vez nesta
  auditoria).
- **Classificação: PROMOTE** (prioridade máxima dentro do grupo — deveria
  ser o primeiro `git add` de toda a Fase 8.2, antes de qualquer outro)

## requirements.txt
- **Finalidade:** manifesto de dependências Python.
- **Dependências/consistência:** já validado nesta auditoria — `pip freeze`
  (Fase 2) confirmou fastapi 0.136.1, faiss-cpu 1.13.2, ollama 0.6.2,
  pytest-asyncio 1.3.0, streamlit>=1.39.0, todos consistentes com o que o
  arquivo declara e com o que o sistema de fato usa em runtime.
- **Valor:** CRÍTICO — sem ele, `pip install -r requirements.txt` (citado
  em `docker-entrypoint.sh`/`Dockerfile`, ambos já tracked) não funciona.
- **Classificação: PROMOTE**

## README.md
- **Finalidade:** documentação de entrada do projeto Nex Chat.
- **Consistência com o código real:** conteúdo descreve corretamente esta
  aplicação — "Assistente de IA local... memória persistente (embeddings
  via Ollama + FAISS)... fallchain multi-backend (Ollama → OpenRouter →
  Llama.cpp → HuggingFace)... orquestração multi-agente (Researcher →
  Analyst → Writer)" — bate exatamente com o `fallback_order` observado em
  todo `/health` desta auditoria e com os agentes classificados PROMOTE em
  `classificacao_src.md`.
- **Valor:** ALTO — documentação de entrada precisa.
- **Classificação: PROMOTE**

## SYSTEM_MAP.md
- **Finalidade:** mapa de arquitetura do sistema ("Nex Chat - IA Local,
  Memória Persistente + OpenRouter + HuggingFace").
- **Consistência:** título e escopo batem com o sistema real auditado.
- **Valor:** ALTO — documentação arquitetural.
- **Classificação: PROMOTE**

## Nex.spec.md
- **Finalidade:** especificação técnica original do sistema ("Sistema de
  IA Local com Memória Persistente", datado 2026-04-13 no próprio arquivo).
- **Consistência:** escopo bate com o sistema real; é citado inclusive por
  `tests/test_config.py` como referência ("Testes para Configuração -
  Nex.spec.md Seção 3" — visto no cabeçalho desse arquivo, já classificado
  PROMOTE).
- **Valor:** ALTO — é a spec original referenciada por pelo menos um teste
  já promovido.
- **Classificação: PROMOTE**

## ⚠️ CLAUDE.md — achado de inconsistência
- **Finalidade declarada no próprio arquivo:** "This is a **Claude Code
  plugin** - a collection of production-ready agents, skills, hooks,
  commands, rules, and MCP configurations."
- **Consistência com o repositório real:** **NENHUMA.** Este repositório é
  o Nex Chat — uma aplicação Python/FastAPI de assistente de IA local com
  memória persistente, conforme confirmado exaustivamente por todas as
  fases desta auditoria (Fases 1-7). O conteúdo de `CLAUDE.md` descreve um
  projeto completamente diferente (um plugin de ferramentas para o Claude
  Code CLI, com estrutura `agents/`, `skills/`, `commands/`, `hooks/`,
  `rules/`) que não corresponde à arquitetura real deste repositório
  (`src/`, `tests/`, `data/`, `docker-compose.yml`, etc.).
- **Origem provável:** parece ter sido copiado de um template genérico ou
  de outro repositório sem adaptação ao projeto Nex. Nota lateral: este
  MESMO arquivo já causou confusão nesta própria sessão de auditoria — ele
  foi injetado como contexto de sistema no início da conversa, descrevendo
  um projeto que não é o que estava sendo auditado.
- **Valor:** NEGATIVO no estado atual — um `CLAUDE.md` desalinhado com o
  repositório real é pior que nenhum, porque induz qualquer assistente de
  IA (incluindo este) a aplicar suposições erradas sobre a natureza do
  projeto.
- **Classificação: ARCHIVE** ~~(SUPERADA — ver revisão abaixo)~~

## ⚠️ REVISÃO (Fase 8.2C.0)
A classificação ARCHIVE acima foi feita sem inventariar `agents/` (66
arquivos) e `rules/` (104 arquivos) — ambos também untracked e nunca
cobertos por esta Fase 8.1. A Fase 8.2C.0 investigou os três como
conjunto e encontrou que `README.md` (já PROMOTE) documenta `agents/` e
`rules/` como feature deliberada e entregável do projeto Nex Chat
("90+ agentes Claude Code... em `agents/`", seções dedicadas). `CLAUDE.md`
é consumido ativamente por 7 arquivos de `agents/*.md` como fonte de
convenções — não é órfão.

**Nova classificação: PROMOTE**, junto com `agents/` e `rules/`. Ver
`fase_8_repository_boundary/8.2C0_toolkit/CLASSIFICACAO_TOOLKIT.txt` para
evidência completa. Justificativa: mover ou arquivar contradiria a própria
documentação pública do projeto (README) já promovida.

---

## Resumo do grupo

| Arquivo | Classificação |
|---|---|
| requirements.txt | PROMOTE |
| README.md | PROMOTE |
| SYSTEM_MAP.md | PROMOTE |
| Nex.spec.md | PROMOTE |
| CLAUDE.md | ARCHIVE (desalinhado com o projeto real) |
