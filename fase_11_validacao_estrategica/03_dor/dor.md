# 11.3 — Dor

DOR (conforme documentada, não conforme validada):
- Tarefa: obter respostas de IA conversacional com continuidade de
  contexto entre sessões, sem depender de um provedor cloud pago nem
  enviar dados a terceiros por padrão.
- Custo atual (alegado pela motivação implícita do projeto): custo
  monetário de assinaturas de IA cloud (ChatGPT Plus, Claude Pro, etc.)
  e/ou risco de privacidade de enviar conversas a serviços de terceiros.
- Frequência: parcialmente observável. `data/memoria.db` mostra
  interações reais em 7 datas ao longo de ~3 meses — uso esporádico e
  recorrente, não diário, e majoritariamente misturado com teste de
  funcionalidades (verificar memória, perguntar identidade do assistente,
  discutir a própria arquitetura do projeto). Pelo menos 1 sessão
  (14/07) tem um propósito de tarefa real fora de teste: exame de
  documentos jurídicos pessoais.

BEFORE: usar um serviço de IA cloud pago ou gratuito com limites,
sem controle sobre onde os dados residem.
AFTER: usar o Nex localmente/via OpenRouter free tier, com memória
persistente local (SQLite + FAISS).

STATUS: EVIDÊNCIA PARCIAL (para "o autor usa a ferramenta de vez em
quando, inclusive para uma tarefa real") / HIPÓTESE (para "essa dor é
generalizável a outras pessoas")

FONTE: inspeção direta do conteúdo de `data/memoria.db` (não apenas
metadados) — ver 02_usuario/usuario.md. Não há entrevista de usuário,
pesquisa de mercado, ticket de suporte, ou qualquer validação da dor
para além do próprio autor.

## Critério de falsificação
Saberíamos que a dor NÃO existe ou NÃO é relevante se o uso registrado
fosse EXCLUSIVAMENTE teste técnico. Isso foi parcialmente refutado: há
pelo menos um uso genuíno e não-trivial (exame de documento jurídico
real com pedido de "faça a defesa"). Porém a MAIORIA das 71 interações
observadas (saudações, perguntas sobre a identidade do assistente,
verificação de memória, discussão da própria arquitetura do sistema) é
consistente com uso exploratório/de desenvolvimento, não com uma dor
recorrente sendo resolvida em produção. Resumo honesto: a dor existe
para o autor, esporadicamente, mas a amostra é pequena demais (N=1
usuário, uso não-diário) para generalizar se ela é forte ou frequente o
suficiente para sustentar um produto.
