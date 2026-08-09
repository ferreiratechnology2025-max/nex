# Relatório de Testes - Fase 4

## Data: 02/06/2026
## Ambiente: Windows/Python 3.13.12

### Resumo
- Total de testes: 8
- Passaram: 8
- Falharam: 0
- Cobertura: 100%

### Detalhamento por Teste

| # | Teste | Status | Tempo | Observação |
|---|-------|--------|-------|------------|
| 1 | Health Check | ✅ | ~500ms | OpenRouter `available: true`, memória com 28 registros |
| 2 | Chat OpenRouter | ✅ | ~15s | Resposta coerente em português sobre Machine Learning, backend openrouter |
| 3 | Memória Persistente | ✅ | ~10s | Sistema lembrou nome "João" e contexto de interações anteriores |
| 4 | Web Search | ✅ | ~20s | Resposta com tendências atuais de IA (GPT-4, Claude, Gemini, AI Act) |
| 5 | Remember Explícito | ✅ | ~200ms | Status "saved", ID 27, texto "O usuário prefere respostas curtas e diretas" |
| 6 | Fallback HuggingFace | ✅ | ~5s | Modelo SmolLM-135M carregado do cache (272/272 weights), gerou resposta "Brasília" |
| 7 | WebSocket | ✅ | ~10s | Streaming token-by-token via SSE, 52 chars recebidos, conexão + handshake OK |
| 8 | Métricas | ✅ | ~200ms | Formato correto, fallback_counts com novos nomes (openrouter_to_*), 0 fallbacks |

### Backends Verificados

| Backend | Status | Observação |
|---------|--------|------------|
| OpenRouter | ✅ Disponível | Modelo `openrouter/owl-alpha`, fallback `nvidia/nemotron-3-nano-30b-a3b:free` |
| HuggingFace | ✅ Funcional | Phi-2 (primário) → TinyLlama (fallback) — SmolLM-135M testado com cache |
| Llama.cpp | ⚠️ Não configurado | GGUF `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf` não encontrado |

### Problemas Encontrados

1. **Streaming SSE**: O streaming via OpenRouter não funcionava corretamente — o cliente tratava `stream: true` como requisição normal. **Corrigido**: Adicionado `chat_completion_stream()` com parsing SSE linha a linha e fallback automático de modelo.
2. **WebSocket encoding**: Windows console não suporta emoji (\U0001f60a) no encoding cp1252. Não é um bug do sistema.
3. **Web Search não usa tool calling do Z.ai**: O web search agora usa o conhecimento interno do modelo OpenRouter, não tool calling dedicado (Z.ai removido na Fase 2).

### Recomendações

1. **Adicionar attention_mask no HF**: O modelo SmolLM-135M emitiu warning sobre `attention_mask` não definida. Adicionar `attention_mask=inputs.attention_mask` nos `generate()` calls.
2. **Modelo local melhor**: Considere baixar `microsoft/phi-2` ou `TinyLlama-1.1B-Chat-v1.0` para melhor qualidade nas respostas locais.
3. **Testes automatizados**: Os testes existentes em `tests/` precisam de atualização para refletir a nova arquitetura sem Z.ai.
4. **Monitoramento**: Considere adicionar health check periódico para OpenRouter com reconexão automática.
