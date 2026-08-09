# Classificação — tests/ untracked (10 arquivos)

Base factual: contagem de PASS/FAIL por arquivo extraída do baseline final
da Fase 7 (`fase_7_correcao_controlada/06_baseline_final/pytest_full.txt`).

## test_api_gateway.py — 8 PASS / 4 FAIL
- **Finalidade:** testa `src/api_gateway.py` (rotas FastAPI, modelos Pydantic).
- **Dependências:** roda contra o app real via `TestClient`/`AsyncMock`.
- **Duplicação:** nenhuma — único arquivo que testa o gateway.
- **Valor:** ALTO — maioria passa contra o código atual, cobre componente
  crítico (a própria API HTTP do sistema).
- **Classificação: PROMOTE**

## test_config.py — 19 PASS / 0 FAIL
- **Finalidade:** testa `src/config.py` (Settings/Pydantic).
- **Valor:** ALTO — 100% de aprovação contra o código atual.
- **Classificação: PROMOTE**

## test_fallback.py — 2 PASS / 2 FAIL
- **Finalidade:** testa detecção de backend e estrutura de `/health` via
  `from src.core.llm_manager import LLMManager, BackendType` — import direto
  e válido contra a API real (`BackendType` existe, confirmado na Fase 6).
- **Valor:** MÉDIO-ALTO — testa lógica de fallback, componente crítico
  citado no próprio `/health` (`"fallback_order"`).
- **Classificação: PROMOTE** (as 2 falhas ficam para investigação de causa-raiz,
  não descartam o arquivo)

## test_fallback_activation.py — 0 PASS / 2 FAIL
- **Finalidade:** testa ativação de fallback via headers de API.
- **Valor:** MÉDIO — 0% de aprovação atual, mas não foi possível determinar
  nesta etapa se a falha é de teste desatualizado ou defeito real (fora do
  escopo — será tratado na investigação das 26 falhas residuais).
- **Classificação: PROMOTE COM RESSALVA** — recomendo versionar, mas marcar
  como candidato prioritário da próxima fase de investigação de falhas
  (0/2 é o pior índice do grupo).

## test_llm_manager.py — 1 PASS / 7 FAIL
- **Finalidade:** testa `LLMManager` (inicialização, batching, cleanup,
  fallback CPU).
- **Valor:** MÉDIO — testa componente crítico, mas 7/8 falham
  (TypeError, não investigado nesta fase).
- **Classificação: PROMOTE COM RESSALVA** — mesmo raciocínio acima; taxa de
  falha alta merece investigação antes de confiar no arquivo como regressão
  de referência, mas não há evidência de que seja "teste inválido" — é
  código de teste que importa e chama a API real, só que grande parte falha.

## test_memory_opt.py — 2 PASS / 5 FAIL
- **Finalidade:** testa `CacheLRU` e `MemoriaPersistente` (o mesmo módulo
  corrigido nas Etapas 4-5 desta auditoria).
- **Dependências:** `from core.memory_manager import MemoriaPersistente,
  CacheLRU` — nota: import relativo a `core` (sem prefixo `src.`), requer
  `sys.path.insert` (presente no arquivo) para funcionar. Já validado
  compatível com a assinatura atual (usa `db_path=self.db_path,
  index_path=self.index_path` explicitamente — call sites já auditados
  na Etapa 5).
- **Valor:** ALTO — testa exatamente o componente que foi objeto de correção
  nesta Fase 7 (MemoriaPersistente).
- **Classificação: PROMOTE COM RESSALVA** — 5 falhas em TestCacheLRU
  (AssertionError) merecem investigação, mas o arquivo é estruturalmente
  válido e relevante.

## test_web_search.py — 11 PASS / 5 FAIL
- **Finalidade:** testa `src/core/web_search.py` (também untracked, já
  classificado PROMOTE no grupo src/).
- **Valor:** ALTO — maioria passa; testa uma feature confirmada ativa em
  produção.
- **Classificação: PROMOTE**

## test_ws_metrics.py — 13 PASS / 1 FAIL
- **Finalidade:** testa `src/ws_handler.py` e `src/metrics.py` (ambos
  untracked, já classificados PROMOTE no grupo src/).
- **Valor:** ALTO — 93% de aprovação.
- **Classificação: PROMOTE**

## quick_test.py — 1 PASS / 0 FAIL (mas sem asserts)
- **Origem:** script procedural (`async def test(): ...` sob
  `if __name__ == "__main__"`), não estruturado como suíte pytest.
- **Finalidade:** verificação manual rápida de `MemoriaPersistente`
  (`salvar_memoria`, `buscar_contexto`, `get_stats` — todos métodos reais,
  confirmados existentes no código atual).
- **Dependências:** `from core.memory_manager import MemoriaPersistente`
  via `sys.path.insert` — funciona, e é coletado pelo pytest porque a
  função se chama `test()` (bate com o padrão `test*` do pytest), efeito
  colateral não-intencional, não desenho de teste.
- **Duplicação:** a mesma classe já é testada com asserts reais em
  `test_memory_opt.py` e `tests/test_memory_integration.py` (tracked).
- **Valor:** BAIXO como teste automatizado (não tem nenhum `assert` — só
  `print()`; "passa" mesmo que os resultados estejam semanticamente
  errados, contanto que não lance exceção). Tem valor como ferramenta de
  smoke-test manual para um dev rodar localmente.
- **Classificação: KEEP-UNTRACKED** — não deve ser versionado como parte da
  suíte oficial (dá falso sinal de "passou" sem validar nada de fato), mas
  tem utilidade como script de verificação rápida para desenvolvimento local.

## debug_test.py — 0 itens coletados pelo pytest
- **Origem:** script procedural (`async def debug_test(): ...`), função não
  bate com o padrão `test*` do pytest (chama-se `debug_test`, não
  `test_debug`) — por isso não aparece em nenhuma linha do
  `pytest_full.txt` (nem PASS nem FAIL: zero itens coletados deste arquivo).
- **Finalidade:** depuração de dimensões de embedding (FAISS vs
  SentenceTransformer) — imprime `memoria.dimension`, `index.ntotal`,
  `index.is_trained`, embeddings armazenados.
- **Dependências:** `from sentence_transformers import SentenceTransformer`
  — biblioteca não usada em nenhum outro lugar do código de produção
  auditado até agora (não aparece em `requirements.txt` como dependência
  direta verificada nesta etapa — a verificar). `memoria.dimension`
  confirmado como atributo real (`src/core/memory_manager.py:136`).
- **Duplicação:** nenhuma — é o único arquivo que inspeciona dimensões de
  embedding manualmente.
- **Valor:** BAIXO como teste automatizado (zero asserts, não é coletado
  pelo pytest, então não contribui para o baseline de forma alguma — nem
  positiva nem negativa). Tem valor como ferramenta de diagnóstico manual.
- **Classificação: KEEP-UNTRACKED** — útil para debug pontual de
  incompatibilidade de dimensão de embedding, mas não pertence à suíte
  oficial nem ao controle de versão do "conjunto de testes".

---

## Resumo do grupo tests/

| Arquivo | PASS/FAIL | Classificação |
|---|---|---|
| test_api_gateway.py | 8/4 | PROMOTE |
| test_config.py | 19/0 | PROMOTE |
| test_fallback.py | 2/2 | PROMOTE |
| test_fallback_activation.py | 0/2 | PROMOTE (com ressalva) |
| test_llm_manager.py | 1/7 | PROMOTE (com ressalva) |
| test_memory_opt.py | 2/5 | PROMOTE (com ressalva) |
| test_web_search.py | 11/5 | PROMOTE |
| test_ws_metrics.py | 13/1 | PROMOTE |
| quick_test.py | 1/0 (sem asserts) | KEEP-UNTRACKED |
| debug_test.py | não coletado | KEEP-UNTRACKED |
