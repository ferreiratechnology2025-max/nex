# 11.6 — Métricas

HIPÓTESE: Nex reduz o tempo (ou custo, ou esforço) de obter uma resposta
de IA contextualizada em relação à alternativa mais simples (ChatGPT/
Claude com memória nativa), em uma margem que justifique o custo de
manter a infraestrutura própria.

BASELINE: DESCONHECIDO. Não existe medição de quanto tempo/esforço o
usuário gastava antes do Nex, nem de quanto gasta hoje usando-o (fora do
próprio ato de desenvolvê-lo).

META: NÃO DEFINIDA em nenhum artefato do projeto.

AMOSTRA: N=1 usuário, 71 interações registradas ao longo de ~3 meses (7
dias distintos de uso real, conforme 02_usuario/usuario.md).

PERÍODO: dados disponíveis cobrem 13/04/2026 a 14/07/2026 (desde a
criação dos primeiros registros de sessão até a memória mais recente).

CRITÉRIO DE SUCESSO: NÃO DEFINIDO.
CRITÉRIO DE FALHA: NÃO DEFINIDO.

STATUS: UNKNOWN

## O que a infraestrutura de métricas do próprio sistema mede hoje
`/metrics` (validado nesta e em fases anteriores da auditoria) expõe:
`requests_total`, `active_connections`, `avg_latency_ms`,
`peak_memory_mb`, `fallback_counts`, `llm_fallback_total`. Essas são
métricas de SAÚDE TÉCNICA (o sistema está no ar e respondendo), não
métricas de VALOR (o sistema está resolvendo o problema do usuário
melhor que a alternativa). Nenhuma métrica de negócio/produto (retenção,
frequência de uso espontâneo vs. teste, satisfação, tempo economizado)
é coletada em lugar nenhum do sistema.

## Recomendação para tornar esta hipótese testável (não executada nesta
fase — zero código)
Se o Arquiteto decidir PROSSEGUIR, a métrica mínima viável seria: taxa de
uso espontâneo (sessões iniciadas fora de contexto de desenvolvimento/
teste do próprio autor) por semana, com meta explícita (ex.: "≥ 3
sessões espontâneas por semana ao longo de 4 semanas") e critério de
falha simétrico (ex.: "< 1 sessão espontânea por semana por 4 semanas
consecutivas → sinal de que a dor não é forte o suficiente"). Essa
métrica não requer novo código além do que já existe (`data/sessions/`
já registra sessões) — requer apenas rotular manualmente "teste" vs.
"uso real" e observar por um período definido.
