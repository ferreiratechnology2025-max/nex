# System Map - Nex Chat

## Visao Geral

```
+-----------------------------------------------------------+
|                                                          |
|                   Nex Chat - IA Local                       |
|            Memoria Persistente + OpenRouter + HuggingFace    |
|                                                          |
+-----------------------------------------------------------+
```

## Arquitetura de Alto Nivel

```
+------------------------------------------------------------------+
|                                                                    |
|  +------------+    +------------+    +-------------------------+        |
|  |  Interface |    |    API     |    |      Core Modules       |        |
|  |  (Web/WS)  |    | (FastAPI)  |    | (LLM + Memory + Docs)  |        |
|  +-----+------+    +-----+------+    +----------+------------+        |
|        |                 |                      |                         |
|        v                 v                      v                         |
|  +------------+  +----------------+  +-----------+-----------+         |
|  | templates/ |  | api_gateway.py |  | llm_manager.py         |         |
|  | static/    |  | ws_handler.py  |  | memory_manager.py     |         |
|  |             |  |               |  | openrouter_client.py    |         |
|  |             |  |               |  | web_search.py         |         |
|  |               |  |               |  | document_reader.py    |         |
|  |             |  |               |  | document_manager.py   |         |
|  +------------+  +----------------+  +-----------------------+         |
|                                                                    |
|  +------------+                                                          |
|  | Interface  | (Streamlit)                                              |
|  | streamlit  |                                                          |
|  | _app.py    |                                                          |
|  +------------+                                                          |
|                                                                    |
+------------------------------------------------------------------+
```

## Estrutura de Arquivos

```
D:/Nex/
|
+-- streamlit_app.py              # Interface Streamlit
+-- .streamlit/
|   +-- config.toml              # Tema Streamlit
|
+-- src/                           # Codigo fonte principal
|   +-- __pycache__/
|   +-- core/
|   |   +-- __init__.py
|   |   +-- llm_manager.py        # Gerenciador de LLM
|   |   +-- memory_manager.py    # Sistema de memoria
|   |   +-- openrouter_client.py # Cliente OpenRouter
|   |   +-- web_search.py        # Busca na web (DuckDuckGo)
|   |   +-- web_search_engine.py # Engine de busca DuckDuckGo
|   |   +-- document_reader.py   # Leitor de documentos (PDF/DOCX/TXT)
|   |   +-- document_manager.py  # Gerenciador e sumarizacao de documentos
|   +-- __pycache__/
|   +-- api_gateway.py           # API FastAPI (rotas REST + WS)
|   +-- config.py                # Configuracoes centralizadas
|   +-- main.py                 # Ponto de entrada
|   +-- metrics.py              # Metricas e monitoramento
|   +-- ws_handler.py          # Handlers WebSocket
|
+-- templates/                   # Templates HTML
|   +-- index.html             # Interface web principal
|
+-- static/                      # Arquivos estaticos
|   +-- script.js              # Cliente JavaScript
|   +-- style.css             # Estilos CSS
|
+-- scripts/                    # Scripts de ambiente virtual
|   +-- windows/
|       +-- setup_venv.bat     # Cria ambiente virtual
|       +-- start_venv.bat    # Inicia servidor com venv
|       +-- validate_venv.bat # Valida instalacao
|       +-- test_venv.bat    # Testes automatizados
|
+-- data/                       # Dados do sistema
|   +-- memoria.db            # Banco SQLite
|   +-- memoria.db-shm
|   +-- memoria.db-wal
|   +-- memoria.index        # Indice FAISS
|
+-- docs/                      # Documentacao
|   +-- USER_GUIDE.md
|   +-- API_REFERENCE.md
|   +-- DEVELOPER_GUIDE.md
|
+-- docker-compose.yml        # Orquestracao Docker
+-- Dockerfile               # Imagem Docker
+-- requirements.txt       # Dependencias Python
+-- .env                    # Variaveis de ambiente
+-- README.md              # Documentacao principal
+-- Nex.spec.md           # Especificacao do sistema
+-- SYSTEM_MAP.md          # Este arquivo
```

## Módulos Principais

### 1. main.py
**Responsabilidade**: Ponto de entrada unificado
- Inicializa sistema de memoria
- Inicializa gerenciador LLM
- Configura servidor uvicorn
- Gerencia sinais de shutdown

```python
# Fluxo de inicializacao
main()
  -> load_settings()           # Carrega configuracoes
  -> MemoriaPersistente()    # Inicializa sistema de memoria
  -> LLMManager()           # Inicializa gerenciador LLM
  -> DocumentReader()       # Inicializa leitor de documentos
  -> DocumentManager()      # Inicializa gerenciador de documentos
  -> uvicorn.Server()        # Inicia servidor
```

### 2. api_gateway.py (FastAPI)
**Responsabilidade**: API REST + WebSocket
- Rate limiting (100 req/min, janela 60s)
- Rotas /ask, /remember, /upload, /ask_about_document, /summarize_document, /documents, /health, /metrics
- Middleware CORS
- Build de prompt com contexto
- Upload de documentos (PDF, DOCX, TXT, MD, JSON, CSV)

```
Endpoints:
  POST /ask               -> Chat com uso de memoria
  POST /remember          -> Salvar memoria explicita
  POST /upload            -> Upload de documento
  POST /ask_about_document -> Perguntar sobre documento
  POST /summarize_document -> Resumir documento
  GET  /documents        -> Listar documentos
  DELETE /documents/{id} -> Remover documento
  GET  /health           -> Health check
  GET  /metrics          -> Metricas do sistema
  WS  /ws/chat          -> Chat real-time
```

### 3. core/memory_manager.py
**Responsabilidade**: Sistema de memoria persistente
- Cache LRU (200 itens, TTL 3600s)
- SQLite WAL mode
- FAISS IVF para busca vetorial
- Sentence-transformers (all-MiniLM-L6-v2)

```
Componentes:
  CacheLRU              -> Cache com LRU + TTL
  MemoriaPersistente   -> Sistema principal
  MemoriaItem         -> Dataclass para itens

Tabela memorias (SQLite):
  id, texto, embedding_blob, timestamp,
  importancia, acessos, sumario, tags
```

### 4. core/llm_manager.py
**Responsabilidade**: Gerenciador de LLM
- Multi-backend (OpenRouter / HuggingFace)
- Detecção automática de backend
- Streaming token a token
- Web search integrado

```
Backends suportados:
  OpenRouter (default, prioritario)
  HuggingFace (fallback local)

Fluxo:
  generate()
    -> OpenRouter: _generate_openrouter() -> chat_completion()
    -> HF:  _generate_huggingface() -> model.generate()
```

### 5. core/openrouter_client.py
**Responsabilidade**: Cliente para API OpenRouter
- Suporte a modelos free (sem API key)
- Chat completion com fallback entre modelos
- Streaming SSE (Server-Sent Events)
- Metodos sync e async

```
Metodos:
  is_available()              -> Verifica acesso a API
  health_check()             -> Testa conectividade
  chat_completion()          -> Chat completion (dict)
  chat_completion_stream()   -> Streaming SSE (async generator)
  parse_response_content()  -> Extrai texto da resposta

Configuracoes:
  OPENROUTER_API_KEY          -> Chave da API (opcional)
  OPENROUTER_MODEL            -> openrouter/owl-alpha
  OPENROUTER_FALLBACK_MODEL   -> nvidia/nemotron-3-nano-30b-a3b:free
```

### 6. core/web_search.py
**Responsabilidade**: Busca na web e leitura de paǵinas
- Busca independente via DuckDuckGo (gratuito, sem API key)
- Leitura de paǵinas completas via HTTP (aiohttp + BeautifulSoup)
- Salvamento automatico de resultados na memoŕia
- Formatacão de resultados para contexto do LLM
- Fallback para leitura de páginas mesmo sem BeautifulSoup

```
Fluxo:
  1. Recebe query de busca
  2. WebSearchEngine busca no DuckDuckGo (POST html.duckduckgo.com)
  3. Parser extrai resultados (BeautifulSoup ou regex)
  4. Resultados injetados no prompt do LLM
  5. Conteudo das paginas lido via aiohttp
  6. Salvo na memoŕia para contexto futuro
```

### 7. core/document_reader.py
**Responsabilidade**: Leitura de documentos em multiplos formatos
- Extração de texto de TXT, MD, PDF, DOCX, JSON, CSV
- Suporte a bytes (upload) e file path (local)
- Fallback entre pypdf e PyPDF2 para PDFs
- Tratamento gracioso para formatos nao suportados

```
Formatos suportados:
  .txt .md  -> Leitura direta UTF-8
  .pdf      -> pypdf (fallback PyPDF2)
  .docx     -> python-docx
  .json     -> json.loads + pretty-print
  .csv      -> csv.reader + pipe separator
```

### 8. core/document_manager.py
**Responsabilidade**: Gerenciamento de documentos na memoria persistente
- Armazenamento de documentos no cache em memória
- Salvamento automatico na memoria persistente (prefixo [DOC:uuid])
- Sumarizacao via LLM configurado (OpenRouter ou HuggingFace)
- Listagem, consulta e remocao de documentos
- Integracao com memory_manager para persistencia

### 12. streamlit_app.py
**Responsabilidade**: Interface grafica moderna
- Dashboard com 4 abas: Chat, Documentos, Web Search, Metricas
- Sidebar com status do sistema (health check)
- Upload de documentos com preview e sumarizacao
- Chat com historico e controle de temperatura/web search/memoria
- Integracao com API FastAPI via HTTP (requests)
- Design responsivo inspirado em Bubble Dashboard

### 9. config.py
**Responsabilidade**: Configuracoes centralizadas
- Pydantic Settings com validacao
- Variaveis de ambiente
- Validadores de path

```
Configuracoes:
  OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_FALLBACK_MODEL
  HF_MODEL_NAME, HF_FALLBACK_MODEL
  MODEL_NAME
  MAX_TOKENS, TEMPERATURE
  DB_PATH, INDEX_PATH
  HOST, PORT
  WEB_SEARCH_ENABLED
```

### 10. metrics.py
**Responsabilidade**: Monitoramento
- Thread-safe Metrics collector
- Exponential moving average
- Middleware FastAPI
- CPU/Memory tracking

```
Metricas coletadas:
  requests_total
  active_connections
  avg_latency_ms
  peak_memory_mb
```

### 11. ws_handler.py
**Responsabilidade**: WebSocket handlers
- Chat em tempo real
- Conexoes persistentes
- Timeout de inatividade (30s)

## Fluxo de Dados

```
Usuario
   |
   v
Interface Web (templates/index.html)
   |
   v
Cliente JS (static/script.js)
   |
   v
HTTP/WebSocket Request
   |
   v
API FastAPI (api_gateway.py)
   |
   +--> Rate Limiter
   |
   +--> /ask endpoint
   |       |
   |       v
   |    Memory System (memory_manager.py)
   |       |
   |       +-> Cache LRU (hit -> retorna)
   |       |
   |       +-> SQLite + FAISS -> Embedding -> Busca semantica
   |       |
   |       v
   |    LLM Manager (llm_manager.py)
   |       |
   |       +-> OpenRouter (primario) + Web Search (DuckDuckGo)
   |       |
   |       +-> HuggingFace local (fallback)
   |       |
   |       v
   |    Resposta ao cliente
   |
   +--> /upload endpoint
   |       |
   |       v
   |    DocumentReader (document_reader.py)
   |       |
   |       +-> Detecta formato (.txt/.pdf/.docx/.json/.csv)
   |       |
   |       +-> Extrai texto (pypdf / python-docx / nativo)
   |       |
   |       v
   |    DocumentManager (document_manager.py)
   |       |
   |       +-> Salva no cache em memoria
   |       +-> Persiste na memoria (prefixo [DOC:uuid])
   |       +-> Opcional: sumariza via LLM
   |
   +--> /ask_about_document endpoint
   |       |
   |       v
   |    DocumentManager.get_document()
   |       +-> LLM.generate(conteudo + pergunta) -> resposta
   |
   +--> /summarize_document endpoint
           |
           v
        DocumentManager.summarize_document()
           +-> LLM.generate("Resuma o documento...") -> resumo
```

## Sistema de Memoria

### Curto Prazo
- Contexto da conversa atual
- Limitado por max_tokens
- Busca dos 3 itens mais relevantes

### Longo Prazo
- Embeddings (384 dim, all-MiniLM-L6-v2)
- Busca semantica via FAISS IVF
- Importancia (0.0-2.0)
- Acessos (contador)
- Decaimento (LOG importacia * acessos)
- Persistencia (SQLite WAL)

## Fluxo Atualizado - Operacoes de Memoria

### salvar_memoria()
```
1. Gerar embedding (via queue assincrona)
2. FAISS.add() em memoria           <- ANTES do commit
3. SQLite INSERT
4. conn.commit()                 <- Apenas se FAISS OK
5. FAISS.save()                  <- Best-effort (nao quebra atomicidade)
6. Logging + rollback em caso de erro
```

### buscar_contexto()
```
1. Verificar cache LRU (async)
2. Gerar query embedding
3. FAISS search
4. Atualizar contador de acessos
5. Cache resultado (async)
6. Retornar top-k
```

## Concorrencia

- CacheLRU: asyncio.Lock() + metodos async
- MemoriaPersistente: _db_lock protege DB+FAISS
- Worker de embeddings: threading.Thread + asyncio.run() (CPU-bound)
- RateLimiter: asyncio.Lock() (janela deslizante 60s)

## Configuracoes de Ambiente

| Variavel | Padrao | Descricao |
|---------|--------|----------|
| OPENROUTER_API_KEY | (vazio) | Chave API OpenRouter (opcional p/ free) |
| OPENROUTER_MODEL | openrouter/owl-alpha | Modelo primario |
| OPENROUTER_FALLBACK_MODEL | nvidia/nemotron-3-nano-30b-a3b:free | Fallback OpenRouter |
| HF_MODEL_NAME | microsoft/phi-2 | Modelo HuggingFace primario |
| HF_FALLBACK_MODEL | TinyLlama/TinyLlama-1.1B-Chat-v1.0 | Fallback local |
| MODEL_NAME | HuggingFaceTB/SmolLM-135M | Modelo HF |
| MAX_TOKENS | 2048 | Limite de tokens |
| DB_PATH | data/memoria.db | SQLite path |
| INDEX_PATH | data/memoria.index | FAISS index |
| WEB_SEARCH_ENABLED | true | Habilita busca na web |

## Dependencias

```
fastapi
uvicorn
pydantic
pydantic-settings
torch
transformers
sentence-transformers
faiss-cpu
numpy
psutil
requests
aiohttp
aiohttp
beautifulsoup4
html2text
pypdf
python-docx
python-magic
streamlit
pandas
```

## Scripts Disponiveis

| Script | Funcao |
|--------|--------|
| `setup_venv.bat` | Cria ambiente virtual e instala dependências |
| `start_venv.bat` | Inicia apenas o servidor API |
| `start_ui.bat` | Inicia API + Streamlit UI |
| `validate_venv.bat` | Valida instalação e conectividade |
| `test_venv.bat` | Executa testes automatizados |

## API Endpoints

| Metodo | Endpoint | Descricao |
|:------|:---------|:----------|
| POST | /ask | Chat com memoria |
| POST | /remember | Salvar memoria |
| POST | /upload | Upload de documento (PDF/DOCX/TXT) |
| POST | /ask_about_document | Perguntar sobre documento |
| POST | /summarize_document | Resumir documento |
| GET | /documents | Listar documentos carregados |
| DELETE | /documents/{id} | Remover documento |
| GET | /health | Health check |
| GET | /metrics | Metricas |
| WS | /ws/chat | WebSocket chat |
| GET | / | Root |

## Executando

```bash
# Via ambiente virtual (Windows) - apenas API
scripts\windows\setup_venv.bat
scripts\windows\start_venv.bat

# Com interface grafica Streamlit
scripts\windows\start_ui.bat

# Via scripts
./scripts/start.sh

# Docker
docker-compose up -d
```

## Status do Projeto

✅ **COMPLETO** - Sistema 100% funcional

### Funcionalidades Verificadas:
- [x] Chat via REST e WebSocket
- [x] Interface grafica Streamlit (Chat, Documentos, Web Search, Metricas)
- [x] Memoria persistente (SQLite + FAISS)
- [x] Busca semantica com embeddings
- [x] OpenRouter + HuggingFace integrados
- [x] Web search integrado (DuckDuckGo)
- [x] Leitura de paginas completas
- [x] Leitura de documentos (PDF, DOCX, TXT, MD, JSON, CSV)
- [x] Sumarizacao automatica de documentos
- [x] Q&A sobre documentos enviados
- [x] Fallback para HuggingFace local
- [x] Rate limiting
- [x] Metricas e monitoramento
- [x] Seguranca no upload (MIME, tamanho, bomba de repeticao)