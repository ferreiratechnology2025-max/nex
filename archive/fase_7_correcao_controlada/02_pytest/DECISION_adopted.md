# Decisão adotada — asyncio_mode

**Configuração aplicada:** `asyncio_mode = auto` (não `strict`)

## Por quê

A proposta original do Arquiteto era `strict`, justificada por "os testes usam
`@pytest.mark.asyncio` explicitamente". Essa premissa foi testada contra o código
real antes de qualquer alteração:

- 23 funções `async def test_*` existem em `tests/`.
- Apenas 6 têm `@pytest.mark.asyncio`.
- 17 (`test_ollama_client.py`: 14, `test_fallback_activation.py`: 1,
  `test_memory_integration.py`: 2) não têm nenhum marcador.

Com `strict`, essas 17 continuariam falhando exatamente como no baseline da Fase 6
— a configuração não teria corrigido o problema que a motivou, apenas trocado a
mensagem de erro.

Com `auto`, o pytest-asyncio roda automaticamente qualquer `async def test_*`
independente de marcador. Isso reflete o padrão majoritário já presente no
código (74% dos testes async sem marcador explícito) sem exigir edição de
nenhum arquivo de teste.

## Resultado observado

Passed subiu de 70 para 87 (+17), failed caiu de 43 para 26 (-17) — a contagem
bate exatamente com o número de testes sem marcador, confirmando causalidade
direta, não coincidência.

## Reavaliação futura

Se o projeto adotar como convenção o uso explícito de `@pytest.mark.asyncio`
em todo novo teste, `strict` pode ser reconsiderado nesse momento — mas isso
exigiria primeiro adicionar marcadores aos 17 testes existentes, o que está
fora do escopo desta etapa (regra de engajamento: não editar os testes).
