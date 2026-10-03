# 11.1 — Propósito

PROPÓSITO:
Fornecer um assistente de IA conversacional que roda inteiramente em
hardware local/modesto (i7 + GPU fraca + RAM reduzida — declarado no
próprio título de `Nex.spec.md`), com memória persistente entre sessões,
busca na web e capacidade de ler documentos, sem depender
obrigatoriamente de uma API paga (fallback OpenRouter free-tier / modelos
locais via Ollama/HuggingFace/Llama.cpp).

A transformação operacional pretendida (não a implementação): permitir
que alguém tenha uma experiência de "assistente que lembra de você" —
comparável a produtos cloud (ChatGPT com memória, por exemplo) — sem
enviar dados a terceiros por padrão e sem depender de assinatura paga.

STATUS: HIPÓTESE

FONTE: Inferido de README.md (linha 7: "Assistente de IA local com
memória persistente... funciona sem API key em modelos free") e
Nex.spec.md (título: "Para Hardware Limitado"). Nenhum documento do
projeto declara explicitamente um "porquê" em termos de transformação de
vida/trabalho do usuário — a documentação descreve FUNCIONALIDADES
(o quê e como), não o PROBLEMA que motiva sua existência (o porquê). A
inferência acima é a leitura mais razoável dos artefatos, mas não é uma
declaração de propósito no sentido estrito pedido pelo Arquiteto.

## Critério de falsificação
Saberíamos que o propósito NÃO está sendo alcançado se: (a) o sistema
exigir consistentemente conexão com serviços pagos para funcionar
minimamente (contradizendo "funciona sem API key"), ou (b) a memória
persistente não produzir, na prática, continuidade percebida entre
sessões (o que não foi medido — ver 11.6).

## Achado factual relevante
`.env` (não versionado) contém uma `OPENROUTER_API_KEY` REAL configurada,
e o backend ativo em toda esta auditoria foi `openrouter` (cloud), não um
backend 100% local — apesar de 9 modelos Ollama locais estarem instalados
e disponíveis (`ollama list` confirmou `ornith:latest` etc.). Ou seja: na
prática observada, o sistema roda primariamente contra um serviço cloud,
não local — o que tensiona (sem necessariamente invalidar) o propósito
declarado de independência de terceiros.
