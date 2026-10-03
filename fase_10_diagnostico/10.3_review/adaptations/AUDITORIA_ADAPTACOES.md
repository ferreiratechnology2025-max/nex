# Auditoria das asserções adaptadas — critério de rejeição aplicado

**Critério de rejeição do Arquiteto:** qualquer asserção substituída por
`is not None` ou equivalente vacuamente fraco, sem preservar a
propriedade testada. Aplicado a cada item abaixo, individualmente.

| # | Arquivo | Teste | Antes | Depois | Enfraquecida? | Intenção preservada? |
|---|---|---|---|---|---|---|
| 1 | test_api_gateway.py | test_query_defaults | `assert query.max_tokens == 256` | `assert query.max_tokens == 2048` | NÃO — igualdade exata mantida, valor corrigido | SIM |
| 2 | test_api_gateway.py | test_app_with_test_client | `assert "message" in response.json()` | `assert "text/html" in response.headers["content-type"]` | NÃO — troca de JSON-body-check para header-check é específica e falsificável, não vacuidade | SIM (comportamento real do endpoint mudou de JSON→HTML; teste passou a checar a coisa certa) |
| 3 | test_api_gateway.py | test_ask_without_memory_uses_test_client | `assert response.status_code in [200, 500]` | idêntico (só setup de fixture mudou) | NÃO — asserção final intocada | SIM |
| 4 | test_fallback.py | test_backend_detection | `assert manager.backend == BackendType.HUGGINGFACE` | `assert manager.backend == BackendType.OPENROUTER` | NÃO — igualdade exata mantida, valor corrigido | SIM |
| 5 | test_fallback.py | test_health_structure | `assert "zai" in backends` (+ 2 outras) | linha removida, as outras 2 (`llama_cpp`, `huggingface`) mantidas intactas | NÃO — remoção de checagem de chave inexistente, não substituição por vacuidade | SIM |
| 6-9 | test_memory_opt.py | TestCacheLRU (4 testes) | `assertIsNotNone`/`assertIsNone`/`assertTrue(np.array_equal(...))` síncronos | MESMAS asserções, agora com `await` | NÃO — zero mudança nas asserções em si, apenas correção de que operam sobre o valor real em vez de um objeto coroutine | SIM (100% preservada — é o caso mais limpo desta lista) |
| 10 | test_memory_opt.py | test_cache_lru_interno | `assertIsNotNone` + `assertTrue(np.array_equal(...))` síncronos | MESMAS asserções, chamadas envolvidas em `asyncio.run()` | NÃO | SIM (idêntico ao grupo acima) |
| 11 | test_web_search.py | test_detect_huggingface_backend → **renomeado** test_detect_backend_ignores_use_huggingface_flag | `assert llm.backend == BackendType.HUGGINGFACE` | `assert llm.backend == BackendType.OPENROUTER` | NÃO — igualdade exata mantida | PARCIAL — teste renomeado porque a intenção original ("USE_HUGGINGFACE ativa esse backend") não existe mais; o novo nome documenta honestamente o que passou a ser verificado (o flag é ignorado) em vez de fingir que a intenção original sobrevive |
| 12 | test_web_search.py | test_detect_huggingface_placeholder_key → **renomeado** test_detect_backend_without_local_model | `assert llm.backend == BackendType.HUGGINGFACE` | `assert llm.backend == BackendType.OPENROUTER` (config trocado de `ZAI_API_KEY` placeholder para `LOCAL_MODEL_PATH` vazio) | NÃO — igualdade exata mantida | NÃO — já registrado na 10.2C como não sendo uma adaptação 1:1: a intenção original (rejeitar chave-placeholder) não tem equivalente na lógica atual; o teste foi reescrito para exercitar o outro ramo real existente. Documentado explicitamente, não disfarçado. |
| 13 | test_ws_metrics.py | test_ws_handler_has_correct_signature | `assert "websocket" in params` + `assert "request" in params` | apenas a primeira mantida | NÃO — remoção de expectativa sobre parâmetro que nunca existiu, a asserção real (sobre "websocket") permanece intocada | SIM |

## Veredito por item do critério de rejeição

**Nenhuma das 13 adaptações foi substituída por `is not None` ou
equivalente vacuamente fraco.** Todas mantêm verificação de igualdade
exata, verificação de header/conteúdo específico, ou removeram uma
expectativa sobre algo comprovadamente inexistente — sem inserir uma
checagem frouxa no lugar.

## Transparência sobre os 2 itens não-triviais (#11 e #12)

Diferente dos demais, #11 e #12 envolveram RENOMEAR o teste, não apenas
ajustar o valor esperado. Isso foi uma decisão editorial (documentada já
na 10.2C) porque manter o nome antigo (`test_detect_huggingface_backend`)
enquanto a asserção verifica `BackendType.OPENROUTER` seria enganoso — o
nome do teste é parte do contrato de legibilidade tanto quanto a
asserção. #12 em particular NÃO é uma adaptação 1:1: a propriedade
originalmente testada (rejeição de chave-placeholder) não tem
equivalente no código atual, e isso está registrado como tal desde a
10.2C, não apresentado como "adaptação limpa".
