# Guia do Desenvolvedor - Nex Chat

## Indice
1. [Arquitetura do Sistema](#arquitetura-do-sistema)
2. [Configuracao do Ambiente](#configuracao-do-ambiente)
3. [Estrutura do Codigo](#estrutura-do-codigo)
4. [Como Estender](#como-estender)
5. [Testes](#testes)
6. [Performance](#performance)
7. [Contribuindo](#contribuindo)

---

## Arquitetura do Sistema

### Visao Geral

```
+-------------------------------------------------------------+
|                    Camada de Apresentacao                     |
|  +--------------+  +--------------+  +--------------+        |
|  |  Web UI      |  |  REST API    |  |  WebSocket   |        |
|  +--------------+  +--------------+  +--------------+        |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
|                     Camada de Aplicacao                       |
|  +--------------------------------------------------------+ |
|  |                    FastAPI App                          | |
|  |  - Rotas (REST + WebSocket)                            | |
|  |  - Session Manager                                     | |
|  |  - Lifespan (startup/shutdown)                         | |
|  +--------------------------------------------------------+ |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
|                      Camada de Servicos                      |
|  +--------------+  +--------------+  +--------------+        |
|  | LLM Manager  |  |   Memory     |  |    Cache     |        |
|  | (multi-back) |  |   Manager    |  |   (LRU)      |        |
|  +--------------+  +--------------+  +--------------+        |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
|                      Camada de Infraestrutura                |
|  +--------------+  +--------------+  +--------------+        |
|  |   Ollama     |  |  File System |  |   Docker     |        |
|  |   Backend    |  |  (JSON)      |  |   Container  |        |
|  +--------------+  +--------------+  +--------------+        |
+-------------------------------------------------------------+
```

### Fluxo de Dados

1. **Usuario envia mensagem** -> Web UI ou API
2. **Session Manager** -> Identifica/recupera sessao
3. **Memory Manager** -> Recupera contexto relevante
4. **LLM Manager** -> Gera resposta (com cache)
5. **Memory Manager** -> Salva nova interacao
6. **Resposta** -> Retorna ao usuario

---

## Configuracao do Ambiente

### Desenvolvimento Local

```bash
# Clone o repositorio
git clone https://github.com/seu-user/nex-chat.git
cd nex-chat

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instale dependencias
pip install -r requirements.txt

# Execute em modo desenvolvimento (com hot-reload)
uvicorn src.main:app --reload --port 8000
```

### Dependencias de Desenvolvimento

```txt
# Testes
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Linting
black==23.11.0
flake8==6.1.0
mypy==1.7.0

# Debug
ipython==8.17.2
httpx==0.25.1
```

---

## Estrutura do Codigo

### Core Modules

#### Memory Manager (`src/core/memory_manager.py`)

```python
class MemoryManager:
    """Gerencia memoria curta e longa"""

    def add_user_message(self, content: str):
        """Adiciona mensagem do usuario"""

    def add_assistant_message(self, content: str):
        """Adiciona resposta do assistente"""

    def get_context(self, query: str) -> Tuple[List, str]:
        """Retorna contexto relevante (curto prazo, longo prazo)"""

    def recall(self, query: str) -> List[str]:
        """Recupera memorias por busca semantica"""

    def get_stats(self) -> Dict:
        """Retorna estatisticas da memoria"""

    def clear_session(self):
        """Limpa o contexto de curto prazo"""
```

**Componentes internos:**
- `ShortTermMemory` - Buffer circular de mensagens com limite de tokens
- `LongTermMemory` - Armazenamento persistente com embeddings (sentence-transformers)
- `EmbeddingEngine` - Gera vetores de 384 dimensoes para busca semantica

#### LLM Manager (`src/core/llm_manager.py`)

```python
class LLMManager:
    """Gerencia modelos LLM com fallback automatico"""

    def generate(self, prompt: str, config: GenerationConfig) -> str:
        """Gera resposta (com cache)"""

    def generate_stream(self, prompt: str) -> Generator:
        """Gera resposta em streaming (token por token)"""

    def batch_generate(self, prompts: List[str]) -> List[str]:
        """Gera respostas em lote"""

    def get_stats(self) -> Dict:
        """Retorna estatisticas (requests, cache hits, latencia)"""

    def clear_cache(self):
        """Limpa o cache de respostas"""
```

**Backends suportados (em ordem de prioridade):**
1. `ollama` - Recomendado para CPU (mais leve)
2. `ctransformers` - GGUF files
3. `llama_cpp` - llama-cpp-python
4. `transformers` - HuggingFace (mais pesado)

#### Session Manager (`src/main.py`)

```python
class SessionManager:
    """Gerencia multiplas sessoes de chat"""

    def get_or_create_session(self, session_id) -> Tuple[str, MemoryManager]:
        """Obtem ou cria sessao"""

    def update_activity(self, session_id: str):
        """Atualiza timestamp de atividade"""

    def delete_session(self, session_id: str) -> bool:
        """Remove sessao e seus dados"""

    def get_all_sessions(self) -> List[SessionInfo]:
        """Lista todas as sessoes"""
```

---

## Como Estender

### 1. Adicionar Novo Backend LLM

No arquivo `llm_manager.py`:

```python
# 1. Adicione a verificacao de disponibilidade no topo
try:
    import meu_backend
    BACKENDS_AVAILABLE['meu_backend'] = True
except ImportError:
    BACKENDS_AVAILABLE['meu_backend'] = False

# 2. Adicione o loader na classe LLMManager
def _load_meu_backend(self) -> bool:
    """Carrega meu backend personalizado"""
    if not BACKENDS_AVAILABLE['meu_backend']:
        return False
    try:
        self.model = meu_backend.Model(
            model_path=str(self.model_path),
            device="cpu"
        )
        return True
    except Exception as e:
        print(f"Erro: {e}")
        return False

# 3. Adicione o caller
def _call_meu_backend(self, prompt: str, config: GenerationConfig) -> str:
    """Chama meu backend"""
    response = self.model.generate(
        prompt,
        max_tokens=config.max_tokens,
        temperature=config.temperature
    )
    return response

# 4. Registre na ordem de backends em _load_model()
backends_order = [
    ('ollama', self._load_ollama),
    ('meu_backend', self._load_meu_backend),  # <-- Aqui
    ('ctransformers', self._load_ctransformers),
    ...
]

# 5. Adicione no dispatcher em generate()
elif self.backend == 'meu_backend':
    response = self._call_meu_backend(prompt, config)
```

### 2. Adicionar Novo Modelo de Embedding

Em `memory_manager.py`, altere a classe `LongTermMemory`:

```python
class LongTermMemory:
    def __init__(self, storage_path, model_name="seu-modelo-aqui"):
        # O modelo precisa ser compativel com sentence-transformers
        # Modelos menores: all-MiniLM-L6-v2 (padrao, 80MB)
        # Modelos maiores: all-mpnet-base-v2 (420MB, mais preciso)
        self.embedding_model = self._load_embedding_model(model_name)
```

### 3. Adicionar Nova Rota API

Em `main.py`:

```python
@app.get("/api/minha-rota")
async def minha_rota():
    """Descricao da rota"""
    return {"message": "Hello World"}

# Com parametros
@app.post("/api/minha-rota/{id}")
async def minha_rota_com_id(id: str, request: MeuRequest):
    return {"id": id, "data": request.dict()}
```

### 4. Customizar o Prompt do Sistema

Em `main.py`, modifique `build_prompt()`:

```python
def build_prompt(user_message, short_context, long_context):
    return f"""Voce e o Nex, um assistente de IA especializado em tecnologia.
Responda sempre em portugues, de forma clara e objetiva.

Memorias relevantes:
{long_context}

Historico recente:
{format_context(short_context)}

Usuario: {user_message}
Assistente:"""
```

---

## Testes

### Executando Testes

```bash
# Teste basico do sistema
python test_system.py

# Teste de integracao com Ollama
python test_ollama_integration.py

# Com pytest (se instalado)
pytest tests/ -v

# Com cobertura
pytest --cov=src tests/
```

### Escrevendo Testes

```python
# tests/test_memory_manager.py
import pytest
from pathlib import Path
from src.core.memory_manager import MemoryManager

def test_add_and_retrieve():
    mm = MemoryManager(storage_path=Path("./test_tmp"))
    mm.add_user_message("Meu nome e Joao")

    context, long_ctx = mm.get_context("Qual meu nome?")
    assert len(context) == 1
    assert "Joao" in context[0]['content']

def test_recall():
    mm = MemoryManager(storage_path=Path("./test_tmp"))
    mm.add_user_message("Trabalho com Python e dados")

    results = mm.recall("Python")
    assert len(results) > 0

# Teste de API com TestClient
from fastapi.testclient import TestClient
from src.main import app

def test_api_chat():
    client = TestClient(app)
    response = client.post("/api/chat", json={
        "message": "Ola, teste!"
    })
    assert response.status_code == 200
    assert "response" in response.json()

def test_api_stats():
    client = TestClient(app)
    response = client.get("/api/stats")
    assert response.status_code == 200
    assert "uptime_seconds" in response.json()
```

---

## Performance

### Otimizacoes Implementadas

1. **Cache LRU** - Respostas identicas servidas do cache (<1ms)
2. **Streaming** - Primeira resposta visivel em <500ms
3. **Lazy Loading** - Embeddings carregados sob demanda
4. **Thread Pool** - Batch requests paralelos (Ollama)
5. **Token Counting** - Estimativa rapida via split() em vez de tokenizer

### Metricas de Performance

```python
from src.core.llm_manager import LLMManager

llm = LLMManager()

# Apos algumas requests...
stats = llm.get_stats()
print(f"Latencia media: {stats['avg_latency_ms']}ms")
print(f"Cache hit rate: {stats['cache_hits']}/{stats['requests']}")
print(f"Total tokens: {stats['total_tokens']}")
```

### Benchmarks de Referencia

| Operacao | Tempo Esperado | Notas |
| :--- | :--- | :--- |
| Cache hit | <1ms | Hash lookup |
| Embedding (query) | 5-15ms | MiniLM-L6-v2 |
| Ollama generate | 2000-5000ms | gemma2:2b, CPU |
| Memory recall | 10-50ms | Cosine similarity |
| API overhead | <5ms | FastAPI routing |

---

## Contribuindo

### Padroes de Codigo

```python
# Use type hints
def minha_funcao(param: str) -> int:
    return len(param)

# Docstrings no estilo Google
def minha_funcao(param: str) -> int:
    """
    Descricao curta.

    Args:
        param: Descricao do parametro

    Returns:
        Descricao do retorno

    Raises:
        ValueError: Quando algo da errado
    """
    pass

# Constantes em UPPER_CASE
MAX_TOKENS = 2048
DEFAULT_MODEL = "gemma2:2b"
```

### Fluxo de Contribuicao

1. **Fork** o repositorio
2. **Branch** `feature/minha-feature`
3. **Commit** com mensagem descritiva
4. **Push** para seu fork
5. **Pull Request** para main

### Checklist PR

- [ ] Codigo segue estilo PEP 8
- [ ] Testes passam localmente
- [ ] Documentacao atualizada se necessario
- [ ] Sem breaking changes (ou documentados)
- [ ] Testado em hardware modesto (4-8GB RAM)

---

## Troubleshooting para Devs

### Problema: Modulo nao encontrado
```bash
# Solucao: adicione src ao PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%CD%          # Windows
```

### Problema: Porta em uso
```bash
# Encontre processo
lsof -i :8000          # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Mate processo
kill -9 <PID>          # Linux/Mac
taskkill /PID <PID> /F # Windows
```

### Problema: Memoria insuficiente
```bash
# Use modelo menor
ollama pull llama3.2:1b

# Ou reduza o contexto no GenerationConfig
config = GenerationConfig(max_tokens=256)
```

### Problema: Encoding no Windows
```bash
# Use -X utf8 flag
python -X utf8 script.py

# Ou set env var
set PYTHONUTF8=1
```

---

## Recursos Uteis

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Sentence Transformers](https://www.sbert.net)
- [Docker Documentation](https://docs.docker.com)

---

**Happy Coding!**
