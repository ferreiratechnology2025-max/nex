# Nex — Assistente de IA Local com Memória Persistente e Orquestração Multi-Agente

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**STATUS: PROJETO CONGELADO — TESE DE MERCADO NÃO VALIDADA**

> Este projeto está preservado como referência arquitetural e código-fonte.
> Nenhum desenvolvimento ativo está ocorrendo.
> Reativação somente mediante evidência externa de demanda.

---

## 📌 Estado Atual do Projeto

**Data do congelamento:** Agosto de 2026

**Decisão estratégica:** MATAR como produto / PRESERVAR como código

**Evidência da decisão:**
- Uso real identificado: N=1 usuário (criador)
- Nenhum usuário externo identificado em nenhum artefato do repositório
- Caso de uso mais substancial (análise de documentos jurídicos) já é resolvido adequadamente por ferramentas prontas
- Não há evidência de que outras pessoas valorizem uma solução própria para o problema

**Condição para reativação:**
- ≥ 5 usuários externos
- Uso repetido para uma tarefa específica
- Declaração explícita de que a alternativa atual é insuficiente
- Nex resolve uma deficiência concreta identificada

**Status do repositório:**
- ✅ Código preservado
- ✅ Auditoria completa realizada
- ✅ 469 arquivos versionados
- ✅ 98/98 testes passando
- ✅ Runtime validado (memory_count: 71)
- ✅ Backlog documentado (FB-001: cobertura do fallback)

---

## 📋 Funcionalidades Implementadas (estado na época do congelamento)

Assistente de IA local com memória persistente (embeddings via Ollama + FAISS HNSW), busca na web (DuckDuckGo), fallchain multi-backend (Ollama → OpenRouter → Llama.cpp → HuggingFace) e **orquestração multi-agente** com DAG de agentes especializados (Researcher → Analyst → Writer). Também inclui 90+ **agentes Claude Code** para revisão de código, build resolution, análise de segurança, etc.

## Funcionalidades

- **Multi-backend inteligente**: Ollama (local), OpenRouter (cloud, funciona sem API key em modelos free), Llama.cpp (GGUF local), HuggingFace (fallback local)
- **Memória Persistente**: Lembra de conversas anteriores via busca semântica (SQLite WAL + FAISS HNSW + embeddings Ollama 4096d)
- **Web Search**: Busca informações atualizadas na internet via DuckDuckGo (gratuito, sem API key) + leitura de páginas completas
- **Leitor de Documentos**: Upload e extração de texto de PDF, DOCX, TXT, MD, JSON, CSV com validação de segurança (MIME, content bomb, tamanho)
- **Sumarização Inteligente**: Resumo automático de documentos via LLM
- **Q&A sobre Documentos**: Pergunte sobre o conteúdo de documentos enviados
- **Orquestração Multi-Agente**: Pipeline DAG com triagem heurística (custo zero), circuit breaker, paralelismo via `asyncio.gather`
- **Agentes Claude Code**: 90+ agentes especializados (revisão Python/React/Rust/Dart/Go, build resolver, análise de segurança, etc.) em `agents/`
- **Streaming SSE**: Respostas token a token via REST, SSE (`/orchestrate`) e WebSocket (`/ws/chat`)
- **Cache Inteligente**: LRU cache com TTL para embeddings e respostas frequentes
- **Rate Limiter**: 100 requisições/minuto com janela deslizante
- **Monitoramento**: Métricas em tempo real via `/metrics` (requisições, latência, memória)
- **Interface Web**: UI moderna com upload, web search toggle, memory toggle, sidebar com status do backend
- **Interface Streamlit**: Dashboard com 4 abas (Chat, Documentos, Web Search, Métricas)
- **Docker**: Ambiente completo com Ollama + Nex + Monitor via docker-compose

## Backends Suportados

| Backend | Tipo | Prioridade | Modelo Padrão |
|---------|------|-----------|---------------|
| Ollama | Local | 1º (se disponível) | `ornith:latest` (auto-download) |
| OpenRouter | Cloud (free) | 2º (detecção automática) | `openrouter/owl-alpha` |
| Llama.cpp | Local (GGUF) | 3º (se LOCAL_MODEL_PATH configurado) | Configurável |
| HuggingFace | Local | 4º (fallback final) | `microsoft/phi-2` |

> A detecção automática prioriza: (1) Llama.cpp se `LOCAL_MODEL_PATH` existir, (2) OpenRouter como padrão. Ollama é carregado em paralelo se `OLLAMA_ENABLED=true`.

## Detecção Automática de Backend

```python
def _detect_backend(self) -> BackendType:
    if LOCAL_MODEL_PATH exists          → Llama.cpp (GGUF local)
    else                                → OpenRouter (cloud)
```

O **Ollama** é ativado separadamente via `OLLAMA_ENABLED=true` e entra na cadeia de fallback como primeira tentativa. A ordem real de tentativas é: **Ollama → OpenRouter → Llama.cpp → HuggingFace → mensagem de erro amigável**.

## Início Rápido

### Pré-requisitos

- Python 3.11+
- Pip
- [Ollama](https://ollama.ai) (opcional para modo 100% local)

### Instalação

```bash
# 1. Navegue até o projeto
cd D:/Nex

# 2. Crie ambiente virtual
python -m venv venv

# 3. Ative o ambiente virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 4. Instale dependências
pip install -r requirements.txt

# 5. Configure (opcional — modelos OpenRouter free funcionam sem API key)
# Edite o arquivo .env com suas preferências
```

### Executar com Ollama

```bash
scripts\windows\start_local.bat
```

Isso inicia o Ollama (se não estiver rodando), baixa o modelo `ornith:latest` automaticamente e sobe o servidor Nex.

Acesse no navegador: **http://localhost:8000**

### Executar (API Apenas)

```bash
python -m src.main
```

### Executar (API + Streamlit)

```bash
scripts\windows\start_ui.bat
```

### Executar com Docker

```bash
docker-compose up -d
```

Isso sobe três containers:
- **nex-chat**: Servidor Nex (FastAPI) na porta 8000
- **ollama**: Servidor Ollama dedicado na porta 11434
- **nex-monitor**: Painel de monitoramento (nginx) na porta 8080 (perfil `monitoring`)

## Interface Web

A interface web moderna (`http://localhost:8000`) oferece:

- **Upload de arquivos** (+): anexe PDF, DOCX, TXT, MD, JSON, CSV
- **Web Search** (🌐): ative/desative busca na web por mensagem
- **Memória** (🧠): ative/desative memória de longo prazo
- **Sidebar**: status do backend, modelo ativo, contagem de memórias, sessões recentes
- **Notificações toast**: feedback visual para ações
- **Streaming token a token**: respostas em tempo real

### Interface Streamlit

Uma interface alternativa com Streamlit (`http://localhost:8501`) oferece 4 abas:

- **Chat**: conversa com histórico e controles de temperatura/web search/memória
- **Documentos**: upload com preview e sumarização
- **Web Search**: resultados de busca na web
- **Métricas**: gráficos de desempenho do sistema

Inicie com: `scripts\windows\start_ui.bat`

### WebSocket Chat

Endpoint: `ws://localhost:8000/ws/chat`

Para chat em tempo real com conexão persistente. Exemplo:

```python
import asyncio, websockets
async def chat():
    async with websockets.connect("ws://localhost:8000/ws/chat") as ws:
        await ws.send(json.dumps({"text": "Olá!"}))
        async for msg in ws:
            print(msg)
asyncio.run(chat())
```

### Monitoramento

Painel de monitoramento via docker-compose em `http://localhost:8080` (perfil `monitoring`), servindo o conteúdo de `monitor/index.html` via nginx.

## API Endpoints

| Método | Endpoint | Descrição |
|:-------|:---------|:----------|
| GET | `/` | Interface web principal (HTML) |
| POST | `/ask` | Chat com memória e web search |
| POST | `/orchestrate` | Tarefa complexa multi-agente (SSE streaming) |
| POST | `/remember` | Salvar memória explicitamente |
| POST | `/upload` | Upload de documento (PDF/DOCX/TXT/MD/JSON/CSV) |
| POST | `/ask_about_document` | Perguntar sobre documento |
| POST | `/summarize_document` | Resumir documento |
| GET | `/documents` | Listar documentos carregados |
| DELETE | `/documents/{id}` | Remover documento |
| GET | `/health` | Health check com status de backends |
| GET | `/metrics` | Métricas do sistema (req/s, latência, memória) |
| WS | `/ws/chat` | WebSocket chat em tempo real |

```bash
# Upload de documento TXT/MD/PDF/DOCX
curl -X POST http://localhost:8000/upload \
  -F "file=@contrato.pdf" \
  -F "summarize=true"

# Perguntar sobre um documento
curl -X POST http://localhost:8000/ask_about_document \
  -H "Content-Type: application/json" \
  -d '{"document_id": "abc12345", "question": "Qual o valor total?"}'

# Resumir documento
curl -X POST http://localhost:8000/summarize_document \
  -H "Content-Type: application/json" \
  -d '{"document_id": "abc12345"}'

# Listar documentos carregados
curl http://localhost:8000/documents
```

## Configuração

Variáveis de ambiente (arquivo `.env` na raiz do projeto):

### Ollama

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OLLAMA_ENABLED` | true | Ativar backend Ollama |
| `OLLAMA_URL` | http://localhost:11434 | URL do servidor Ollama |
| `OLLAMA_MODEL` | ornith:latest | Modelo Ollama para geração |
| `OLLAMA_TIMEOUT` | 120 | Timeout em segundos |
| `OLLAMA_TEMPERATURE` | 0.7 | Temperatura de geração |
| `OLLAMA_TOP_K` | 40 | Top-K sampling |
| `OLLAMA_TOP_P` | 0.9 | Top-P sampling |
| `OLLAMA_REPEAT_PENALTY` | 1.1 | Penalidade de repetição |
| `OLLAMA_NUM_CTX` | 4096 | Tamanho do contexto |
| `OLLAMA_NUM_BATCH` | 512 | Batch size |
| `OLLAMA_USE_GPU` | true | Aceleração GPU |
| `USE_OLLAMA_EMBEDDINGS` | true | Usar Ollama para embeddings |
| `EMBEDDING_DIMENSION` | 4096 | Dimensão dos embeddings |

### OpenRouter

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OPENROUTER_API_KEY` | (vazio) | API key (opcional para modelos free) |
| `OPENROUTER_BASE_URL` | https://openrouter.ai/api/v1 | URL da API |
| `OPENROUTER_MODEL` | openrouter/owl-alpha | Modelo primário |
| `OPENROUTER_FALLBACK_MODEL` | nvidia/nemotron-3-nano-30b-a3b:free | Modelo fallback |

### Web Search

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `WEB_SEARCH_ENABLED` | true | Ativar busca na web (DuckDuckGo) |
| `WEB_SEARCH_MAX_RESULTS` | 5 | Máximo de resultados |
| `WEB_SEARCH_SAVE_TO_MEMORY` | true | Salvar resultados na memória |

### HuggingFace / Llama.cpp (Fallbacks Locais)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `USE_HUGGINGFACE` | true | Ativar fallback HuggingFace |
| `HF_MODEL_NAME` | microsoft/phi-2 | Modelo HuggingFace primário |
| `HF_FALLBACK_MODEL` | TinyLlama/TinyLlama-1.1B-Chat-v1.0 | Fallback HuggingFace |
| `HF_USE_GPU` | false | Usar GPU para HuggingFace |
| `HF_MAX_LENGTH` | 512 | Máximo de tokens HF |
| `LOCAL_MODEL_PATH` | (vazio) | Path para modelo GGUF (Llama.cpp) |
| `LOCAL_MODEL_THREADS` | 4 | Threads para inferência local |
| `LLAMA_N_CTX` | 2048 | Contexto Llama.cpp |
| `LLAMA_N_GPU_LAYERS` | 0 | Camadas GPU (0 = CPU) |
| `LOCAL_MODEL_TIMEOUT` | 120 | Timeout em segundos |

### Servidor e Geração

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `HOST` | 0.0.0.0 | Host do servidor |
| `PORT` | 8000 | Porta do servidor |
| `WORKERS` | 1 | Número de workers uvicorn |
| `MAX_TOKENS` | 2048 | Limite de tokens |
| `TEMPERATURE` | 0.7 | Temperatura global de geração |
| `TOP_P` | 0.95 | Top-P global |
| `DB_PATH` | data/memoria.db | Banco SQLite |
| `INDEX_PATH` | data/memoria.index | Índice FAISS |
| `MEMORY_MAX_ITEMS` | 500 | Máximo de memórias |
| `CACHE_MAX_SIZE` | 200 | Máximo do cache LRU |
| `MAX_UPLOAD_SIZE_MB` | 10 | Tamanho máximo de upload (MB) |
| `MAX_CONTENT_CHARS` | 50000 | Máximo de caracteres por documento |

## Estrutura do Projeto

```
D:/Nex/
+-- streamlit_app.py           # Interface Streamlit (dashboard 4 abas)
+-- .streamlit/
|   +-- config.toml            # Tema e config Streamlit
+-- src/                       # Código fonte principal (Python)
|   +-- core/
|   |   +-- ollama_client.py       # Cliente Ollama com auto-download de modelos
|   |   +-- llm_manager.py         # Multi-backend LLM com fallchain (776 linhas)
|   |   +-- openrouter_client.py   # Cliente OpenRouter (chat + streaming)
|   |   +-- memory_manager.py      # Memória persistente (FAISS HNSW + SQLite WAL)
|   |   +-- web_search.py          # Busca na web (DuckDuckGo) + leitura de páginas
|   |   +-- web_search_engine.py   # Engine de busca DuckDuckGo
|   |   +-- document_reader.py     # Leitor PDF/DOCX/TXT/MD/JSON/CSV
|   |   +-- document_manager.py    # Gerenciador e sumarização de documentos
|   +-- agents/
|   |   +-- coordinator.py         # Orquestrador DAG com SSE e circuit breaker
|   |   +-- base_agent.py          # Agente base abstrato (ABC)
|   |   +-- researcher_agent.py    # Agente de pesquisa (web + docs + GitHub API)
|   |   +-- analyst_agent.py       # Agente de análise (insights, padrões)
|   |   +-- writer_agent.py        # Agente de escrita (relatórios, e-mails, resumos)
|   +-- api_gateway.py             # API FastAPI (12 endpoints + rate limiter)
|   +-- config.py                  # Configurações centralizadas (Pydantic Settings)
|   +-- main.py                    # Ponto de entrada (servidor uvicorn)
|   +-- metrics.py                 # Métricas e monitoramento (middleware FastAPI)
|   +-- ws_handler.py              # Handlers WebSocket para chat real-time
+-- agents/                      # 90+ agentes Claude Code especializados (markdown)
+-- rules/                       # Regras de coding style por linguagem (16 linguagens)
|   +-- common/                  # Regras gerais (git, security, testing, patterns)
|   +-- python/                  # Python + FastAPI rules
|   +-- react/ typescript/ java/ go/ rust/ cpp/ csharp/ ...  (16 stacks)
+-- templates/                   # Interface web (HTML + Jinja2)
+-- static/                      # CSS/JS da interface web moderna
+-- data/                        # Banco SQLite + índice FAISS
+-- tests/                       # 14 testes Python (pytest)
+-- scripts/                     # Scripts de inicialização e setup
+-- docs/                        # Documentação (guia do usuário, API, dev)
+-- monitor/                     # Painel de monitoramento (index.html)
+-- examples/                    # Exemplos curl e Python client
+-- Nex.spec.md                  # Especificação técnica detalhada
+-- SYSTEM_MAP.md                # Mapa do sistema (visão arquitetural)
```

### Claude Code Agents (`agents/`)

90+ agentes especializados em markdown com frontmatter YAML para uso com Claude Code. Cada agente tem papel, ferramentas, modelo e instruções específicas:

- **Code Review**: python-reviewer, react-reviewer, rust-reviewer, go-reviewer, java-reviewer, cpp-reviewer, csharp-reviewer, typescript-reviewer, flutter-reviewer, django-reviewer, fastapi-reviewer, kotlin-reviewer, swift-reviewer, php-reviewer, fsharp-reviewer, database-reviewer, security-reviewer, mle-reviewer
- **Build Resolver**: python/resolvers para cada stack (django, react, rust, go, java, cpp, csharp, pytorch, swift, dart, kotlin, harmonyos)
- **Especialistas**: architect, code-architect, network-architect, homelab-architect, a11y-architect, seo-specialist, performance-optimizer, silent-failure-hunter, tdd-guide, code-explorer, code-simplifier, refactor-cleaner, type-design-analyzer, gan-planner/generator/evaluator
- **DevOps**: planner, chief-of-staff, loop-operator, e2e-runner, pr-test-analyzer, opensource-forker/packager/sanitizer, doc-updater, docs-lookup, marketing-agent

### Regras de Coding Style (`rules/`)

16 stacks com regras consistentes (coding-style, hooks, patterns, security, testing):

- **Linguagens**: Python (com FastAPI), TypeScript, React, Angular, Java, Kotlin, Golang, Rust, C++, C#, Swift, Dart, F#, PHP, Ruby, Perl, ArkTS
- **Web**: Design quality + performance além do padrão
- **Common**: Regras base para todos os projetos (agents, code-review, git-workflow, development-workflow)

## Fallback Chain

```
Ollama (se disponível)
  -> OpenRouter (detecção automática padrão)
    -> Llama.cpp (se LOCAL_MODEL_PATH configurado)
      -> HuggingFace (fallback local)
        -> Mensagem de erro amigável
```

## Scripts Disponíveis

### Windows

| Script | Função |
|--------|--------|
| `scripts/windows/start_local.bat` | Inicia Ollama + servidor (modo 100% local) |
| `scripts/windows/setup_ollama.bat` | Instala/configura Ollama |
| `scripts/windows/start.bat` | Inicia apenas o servidor API |
| `scripts/windows/start_ui.bat` | Inicia API + Streamlit UI |
| `scripts/windows/start_venv.bat` | Inicia servidor com venv |
| `scripts/windows/setup_venv.bat` | Cria venv e instala dependências |
| `scripts/windows/validate.bat` | Valida o sistema |
| `scripts/windows/validate_venv.bat` | Valida instalação com venv |
| `scripts/windows/test.bat` | Executa testes |
| `scripts/windows/test_venv.bat` | Executa testes com venv |
| `scripts/windows/fix_env.bat` | Corrige ambiente (recreate venv, resolve conflitos) |
| `scripts/windows/setup_openrouter.bat` | Configura OpenRouter |
| `scripts/windows/backup.bat` | Backup dos dados |
| `scripts/windows/build.bat` | Build do projeto |
| `scripts/windows/download_tinyllama.bat` | Download do modelo TinyLlama |
| `scripts/windows/stop.bat` | Para o servidor |

### Linux/Unix

| Script | Função |
|--------|--------|
| `scripts/start.sh` | Inicia o servidor |
| `scripts/stop.sh` | Para o servidor |
| `scripts/build.sh` | Build do projeto |
| `scripts/download_model.sh` | Download de modelos |
| `scripts/install_ollama.sh` | Instala Ollama |
| `scripts/validate_system.sh` | Valida o sistema |
| `scripts/create_release.sh` | Cria release |

## Testes

```bash
# Ative o venv primeiro
venv\Scripts\activate

# Executar todos os testes
python -m pytest tests/ -v

# Testes individuais
python -m pytest tests/test_api_gateway.py -v
python -m pytest tests/test_llm_manager.py -v
python -m pytest tests/test_memory_integration.py -v
python -m pytest tests/test_coordinator_triage.py -v
python -m pytest tests/test_fallback_chain.py -v
python -m pytest tests/test_web_search.py -v
```

14 testes cobrindo: API Gateway, Config, Coordenador/Triage, Fallback Chain, LLM Manager, Memória, Ollama Client, Web Search, WebSocket/Metrics.

## Sistema de Memória

- **Curto prazo**: Contexto da conversa atual (limitado por tokens, busca dos 3 itens mais relevantes)
- **Longo prazo**: Embeddings via Ollama (4096d) ou sentence-transformers (384d fallback) + FAISS HNSW + SQLite WAL
- **Cache**: LRU (100 itens, TTL 1800s) para embeddings em RAM
- **Busca semântica**: FAISS IVF com busca por similaridade de cosseno
- **Web Search**: Resultados de buscas são salvos automaticamente na memória
- **Documentos**: Upload de arquivos salvos na memória com prefixo `[DOC:uuid]`
- **Decaimento**: Pontuação baseada em `log(importância) * acessos`

## Orquestração Multi-Agente

Tarefas complexas são decompostas e executadas por um **DAG (Directed Acyclic Graph)** de agentes especializados com triagem, paralelismo interno e circuit breaker.

```
                          ┌──────────────┐
                          │   Triage     │  (classifica: simple ou complex)
                          └──────┬───────┘
                                 │
                     ┌───────────┴───────────┐
                     │                       │
                (simple)               (complex)
                     │                       │
                     ▼                       ▼
            ┌────────────────┐     ┌──────────────────┐
            │ Resposta Direta │     │     Planner      │
            └────────────────┘     └────────┬─────────┘
                                            │
                                 ┌──────────┴──────────┐
                                 │    Researcher        │
                                 │  ┌────────────────┐  │
                                 │  │ Web Search     │──│── asyncio.gather
                                 │  │ Document Search│  │
                                 │  └────────────────┘  │
                                 └──────────┬───────────┘
                                            │
                                            ▼
                                 ┌──────────────────┐
                                 │     Analyst      │
                                 └────────┬─────────┘
                                            │
                                            ▼
                                 ┌──────────────────┐
                                 │     Writer       │
                                 └──────────────────┘
```

### Triage Heurística

Antes de qualquer chamada de API, o **Triage** classifica a requisição por palavras-chave:

- **Simple** (< 2 keywords, ≤ 15 palavras): resposta direta, pipeline de agentes é ignorado
- **Complex** (≥ 2 keywords ou > 15 palavras): plano completo de 4 etapas é disparado

Custo: **zero** — nenhuma chamada LLM é feita para classificar.

### Agentes

| Agente | Função |
|--------|--------|
| **Planner** | Decompõe o objetivo em um plano de execução |
| **Researcher** | Busca na web e documentos em **paralelo** via `asyncio.gather` |
| **Analyst** | Analisa dados, extrai padrões e insights |
| **Writer** | Gera resposta final coesa a partir das análises |

### Circuit Breaker

Se o **Researcher** retornar vazio (0 resultados de web e documentos), o pipeline é abortado imediatamente:

1. **Analyst e Writer são pulados** — impedindo alucinação sobre dados inexistentes
2. **Fallback local** é acionado com uma resposta honesta: "Incapaz de acessar fontes externas no momento"
3. O resultado final carrega a flag `"circuit_breaker": true` para a UI exibir o aviso

### Streaming SSE

O endpoint `/orchestrate` retorna eventos em tempo real via `text/event-stream`:

```
data: {"stage": "triage", "status": "complete", "detail": "Classificado como: complex"}
data: {"stage": "research", "status": "running", "detail": "Pesquisando web e documentos..."}
data: {"stage": "research", "status": "complete", "detail": "Pesquisa concluída"}
data: {"stage": "analysis", "status": "running", "detail": "Analisando dados obtidos..."}
data: {"stage": "complete", "status": "done", "detail": "", "result": {...}}
```

## 📊 Auditoria Realizada

O projeto passou por uma auditoria completa em agosto de 2026:

| Fase | Escopo | Resultado |
|------|--------|-----------|
| 0-6 | Auditoria de estado | Baseline estabelecido |
| 7 | Correção controlada | Segurança, persistência, testes |
| 8-9 | Repository Boundary | 469 arquivos versionados |
| 10 | Diagnóstico das 26 falhas | 98/98 testes passando |
| 11 | Validação estratégica | Decisão: MATAR como produto |

**Evidência completa disponível em:** `fase_11_validacao_estrategica/DECISAO.md`

## Licença

MIT

## Agradecimentos

- [Ollama](https://ollama.ai) pela execução local de modelos LLM + embeddings
- [OpenRouter](https://openrouter.ai) pelos modelos free (owl-alpha, nemotron)
- [HuggingFace](https://huggingface.co) pelos modelos locais (phi-2, TinyLlama)
- [FAISS](https://github.com/facebookresearch/faiss) para busca vetorial eficiente (HNSW)
- [LangGraph](https://langchain-ai.github.io/langgraph/) para orquestração do pipeline multi-agente
- [FastAPI](https://fastapi.tiangolo.com) pelo framework web
- [Streamlit](https://streamlit.io) pela UI de dashboard
- [pypdf](https://github.com/py-pdf/pypdf) e [python-docx](https://github.com/python-openxml/python-docx) para leitura de documentos
- [DuckDuckGo](https://duckduckgo.com) pela busca gratuita sem API key
- [Anthropic](https://anthropic.com) pelo Claude Code e inspiração para os agentes

---

**Desenvolvido para rodar localmente com fallback inteligente para cloud, combinando o melhor dos dois mundos**

---

## ⚠️ Nota Final

Este projeto está preservado como demonstração de engenharia e arquitetura de sistemas de IA locais. Não há suporte ativo, desenvolvimento ou roadmap. Pull requests não serão revisados ou mesclados a menos que a condição de reativação seja atendida.
