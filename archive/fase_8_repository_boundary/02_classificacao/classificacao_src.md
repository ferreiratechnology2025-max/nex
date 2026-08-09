# Classificação — src/ untracked (13 arquivos)

Método: para cada arquivo, verificado se é importado (direta ou
transitivamente) pela cadeia de execução real que já foi testada e validada
nas Fases 6-7 (`src/main.py` → sobe o servidor → `/health` retorna 200 com
`memory_count: 71`). Se o servidor sobe e serve requisições usando esses
módulos, eles são produção viva, não experimento.

## src/agents/__init__.py, base_agent.py, analyst_agent.py, researcher_agent.py, writer_agent.py
- **Origem:** parte da árvore `src/agents/`, também contém `coordinator.py`
  (esse SIM está tracked no git — só os 5 arquivos acima estão untracked).
- **Finalidade:** implementação do sistema multi-agente (LangGraph) — Analyst,
  Researcher, Writer, orquestrados por Coordinator.
- **Dependências:** `src/main.py:117` importa `from src.agents import
  Coordinator`; `src/agents/__init__.py` reexporta `BaseAgent`,
  `ResearcherAgent`, `AnalystAgent`, `WriterAgent`, `Coordinator`.
  `coordinator.py` (tracked) instancia `ResearcherAgent` diretamente
  (`src/agents/coordinator.py:71`).
- **Duplicação:** nenhuma — é a única implementação do sistema de agentes.
- **Valor:** ALTO. Log de startup do servidor (Fase 6) confirma:
  "Agent coordinator ready (LangGraph)" — esses módulos rodam em produção
  a cada boot do servidor.
- **Classificação: PROMOTE**
- Justificativa: dependência direta e confirmada em runtime do entrypoint
  oficial (`src/main.py`). `coordinator.py` já está tracked; estes 5 arquivos
  são o restante do mesmo subsistema e ficaram de fora do commit por
  inconsistência de versionamento, não por serem experimentais.

## src/core/__init__.py
- **Finalidade:** reexporta `OpenRouterClient` (`from .openrouter_client
  import OpenRouterClient`).
- **Dependências:** trivial, só re-export.
- **Valor:** ALTO — sem ele, `from src.core import ...` do pacote quebra.
- **Classificação: PROMOTE**

## src/core/document_manager.py, document_reader.py
- **Finalidade:** leitura/gestão de documentos enviados pelo usuário.
- **Dependências:** `src/api_gateway.py:32` importa `DocumentReader`
  diretamente; `src/main.py:49-50` importa ambos e os inicializa
  ("Document system ready" no log de startup da Fase 6).
- **Valor:** ALTO — feature de upload de documentos, confirmada ativa em
  runtime.
- **Classificação: PROMOTE**

## src/core/openrouter_client.py
- **Finalidade:** cliente HTTP para o backend OpenRouter (o backend
  efetivamente ativo, confirmado por `/health` → `"backend ativo:
  openrouter"` em todos os testes de servidor desta auditoria).
- **Dependências:** importado por `src/core/llm_manager.py:185`, usado em
  `chat_completion`, `chat_completion_stream`, `parse_response_content`.
- **Valor:** CRÍTICO — é o backend que respondeu a todo `/health` desta
  auditoria (`"model":"openrouter/owl-alpha"`).
- **Classificação: PROMOTE**

## src/core/web_search.py, web_search_engine.py
- **Finalidade:** busca web (DuckDuckGo) integrada ao LLM.
- **Dependências:** `src/core/llm_manager.py:294` importa
  `WebSearchProcessor` de `.web_search`; `web_search.py:55` importa
  `WebSearchEngine` de `.web_search_engine`. Cadeia completa: `llm_manager`
  → `web_search.WebSearchProcessor` → `web_search_engine.WebSearchEngine`.
  Também usado por `src/agents/researcher_agent.py:33`.
- **Valor:** ALTO — feature de busca web, exposta em `/health`
  implicitamente e usada pelos agentes.
- **Classificação: PROMOTE**

## src/metrics.py
- **Finalidade:** middleware de métricas (Prometheus-like).
- **Dependências:** `src/api_gateway.py:31` importa `MetricsMiddleware,
  get_metrics`; `src/ws_handler.py:12` importa `metrics`.
- **Valor:** ALTO — é literalmente o que respondeu ao `GET /metrics` em
  todas as validações desta auditoria (`requests_total`, `avg_latency_ms`,
  `peak_memory_mb`).
- **Classificação: PROMOTE**

## src/ws_handler.py
- **Finalidade:** handler de WebSocket para chat em tempo real.
- **Dependências:** `src/api_gateway.py:624` importa `router as ws_router`
  de `src.ws_handler`.
- **Valor:** ALTO — rota WebSocket ativa do gateway.
- **Classificação: PROMOTE**

---

## Resumo do grupo

Todos os 13 arquivos de `src/` classificados: **PROMOTE**, sem exceção.
Evidência uniforme: cada um é importado, direta ou transitivamente, pelo
entrypoint `src/main.py`, que foi executado com sucesso 3 vezes nesta
auditoria (Fases 6-7) com `/health` e `/metrics` respondendo 200. Não há
ambiguidade neste grupo — são código de produção que nunca foi commitado,
não experimentos.
