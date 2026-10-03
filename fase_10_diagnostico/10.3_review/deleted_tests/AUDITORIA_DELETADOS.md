# Auditoria dos 2 arquivos de teste deletados

## tests/test_fallback_activation.py (2 testes: test_llm_manager_fallback_to_llama_cpp, test_api_ask_sets_fallback_headers)

**Motivo:** ambos os testes eram inteiramente construídos em torno do
cenário "Z.ai falha em runtime → sistema cai para llama_cpp" — patcheavam
`LLMManager._init_zai`, `BackendType.ZAI`, `manager._generate_zai`,
`manager._zai_client`. Nenhum desses símbolos existe na base atual
(confirmado: `grep -rn "zai" src/` → vazio).

**Evidência de obsolescência:** `docs/TEST_REPORT_FASE4.md` (já
tracked), item 3 dos "Problemas Encontrados": *"Web Search não usa tool
calling do Z.ai... Z.ai removido na Fase 2"*, e item 3 das
"Recomendações": *"Testes automatizados: Os testes existentes em `tests/`
precisam de atualização para refletir a nova arquitetura sem Z.ai."* —
essa recomendação, registrada pelo próprio projeto, nunca foi executada
até esta auditoria.

**Cobertura substituta: NÃO EXISTE — DÍVIDA EXPLÍCITA.**
O que esses testes verificavam de fato (além do wrapper Z.ai) era um
mecanismo real e ainda existente: quando o backend ativo falha ao gerar
uma resposta, o sistema deve cair para `llama_cpp`, marcar
`last_backend_used`/`last_fallback_triggered`, incrementar
`llm_fallback_total` nas métricas, e (no caso do endpoint HTTP) setar os
headers `X-Backend-Used`, `X-Fallback-Triggered`, `X-Fallback-Chain`. Essa
lógica (a própria `LLMManager.generate()`, cadeia
`ollama->openrouter->llama_cpp->huggingface`) continua existindo em
`src/core/llm_manager.py`, mas SEM TESTE que a exercite fim a fim.
`tests/test_fallback_chain.py` (já tracked) testa a ORDEM da cadeia e
alguns cenários de falha, mas não foi auditado linha a linha nesta etapa
para confirmar se cobre exatamente o caso "geração falha em runtime →
fallback ativado → headers corretos" — presumo que NÃO cobre até prova em
contrário, então trato como dívida real, não como "coberto em outro
lugar" (ao contrário do que verifiquei rigorosamente para CR1).

**Ação registrada:** item de backlog — escrever um teste equivalente
substituindo o mock de Z.ai por um mock do backend ativo real
(openrouter), simulando falha de geração e verificando o mesmo conjunto
de asserções (backend usado, fallback disparado, métricas, headers).

## tests/test_llm_manager.py (7 testes: test_cleanup, test_initialization, test_model_loaded, test_batch_processing, test_single_request, test_cpu_fallback_on_no_cuda, test_memory_cleanup)

**Motivo:** todos os 7 métodos instanciavam `LLMManager(model_name=
"HuggingFaceTB/SmolLM-135M")` — uma API de versão única-modelo-HuggingFace
que não corresponde à assinatura atual (`LLMManager(config: dict,
memory_manager=None)`). O arquivo também usava `from core.llm_manager
import LLMManager` (sem prefixo `src.`), consistente com uma versão bem
anterior da estrutura do projeto.

**Evidência de obsolescência:** `TypeError: LLMManager.__init__() got an
unexpected keyword argument 'model_name'` em todos os 7 testes — não é
uma questão de interpretação, é incompatibilidade de assinatura objetiva
e verificável lendo `src/core/llm_manager.py:41`.

**Cobertura substituta — verificada, não presumida:**
- `manager.cleanup()`: coberto por `tests/test_ollama_client.py`
  (já tracked, passando) — confirmado via `grep -n "\.cleanup()"
  tests/*.py` antes da remoção.
- `llm.is_loaded()`: coberto por
  `tests/test_web_search.py::test_generate_without_web_search`.
- Inicialização/detecção de backend: coberto por
  `tests/test_fallback.py` e `tests/test_fallback_chain.py` (ambos já
  tracked, testam `LLMManager` contra a API real).
- "batch_processing"/"single_request": verificado com
  `grep -in "batch" src/core/llm_manager.py` — única ocorrência é
  `OLLAMA_NUM_BATCH` (parâmetro de tuning de inferência do Ollama, não
  um mecanismo de "processar múltiplas requisições em lote"). Não existe
  `batch_generate`, `process_batch` ou equivalente no `LLMManager` atual.
  CONFIRMADO (não apenas presumido): a feature "batching" testada pelos
  métodos antigos não existe na arquitetura atual — não é dívida de
  cobertura, é remoção de teste de uma capacidade que já não está no
  produto.

**Ação registrada:** nenhuma dívida de cobertura para cleanup/is_loaded/
inicialização/batching — todos verificados (cobertos em outro lugar, ou
a capacidade testada não existe mais no produto).
