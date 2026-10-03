# 11.4 — Alternativas

ALTERNATIVAS (o que o usuário faz hoje sem o Nex):
1. ChatGPT/Claude/Gemini via web ou app — memória entre sessões nativa
   (ChatGPT tem "memory" desde 2024), sem instalação, sem manutenção de
   infraestrutura própria.
2. Ferramentas de IA local prontas (LM Studio, GPT4All, Jan.ai,
   Ollama + interface de terceiros) — já resolvem "rodar modelo local"
   sem precisar construir/manter um backend próprio.
3. Não fazer nada / usar busca tradicional (Google) + edição manual de
   documentos, sem assistente de IA.

CUSTO DA ALTERNATIVA:
- Alternativa 1 (cloud pago/free): tempo de setup ≈ 0. Custo monetário:
  US$0-20/mês dependendo do plano. Custo de privacidade: dados enviados
  a terceiros.
- Alternativa 2 (IA local pronta): tempo de setup ≈ minutos a poucas
  horas. Custo monetário: zero. Sem controle sobre orquestração
  multi-agente ou memória customizada, mas resolve a necessidade central
  ("IA local, sem custo") com muito menos esforço de manutenção do que
  construir e manter um sistema próprio (que esta auditoria mostrou
  exigir correções de segurança, testes, arquitetura — dezenas de horas
  de trabalho já investidas).
- Alternativa 3 (nada): custo de oportunidade de não ter assistência de
  IA — alto para tarefas como a observada (exame de documento jurídico),
  baixo para saudações/testes.

STATUS: EVIDÊNCIA (para a existência das alternativas 1 e 2 — são fatos
de mercado público, não específicos deste projeto) / HIPÓTESE (para
"o usuário efetivamente comparou o Nex a essas alternativas antes de
construir")

FONTE: conhecimento geral de mercado (ChatGPT memory, Ollama, LM Studio,
GPT4All são produtos públicos e amplamente documentados). Nenhum
artefato do repositório Nex registra uma comparação explícita com essas
alternativas antes da decisão de construir o sistema do zero.

## Critério de falsificação
Se a alternativa "usar uma ferramenta de IA local já pronta" (ex.:
Ollama + qualquer UI existente) fosse "suficientemente boa" para as
necessidades reais observadas (saudação, pergunta simples, exame
ocasional de documento), a dor não seria forte o suficiente para
justificar construir e manter um sistema multi-componente do zero
(FastAPI + FAISS + SQLite + multi-backend fallback + orquestração
multi-agente). Achado relevante: o próprio uso real observado em
data/memoria.db é majoritariamente composto de interações simples
(saudações, perguntas de identidade, testes de memória) que QUALQUER
ferramenta de IA com memória (incluindo o ChatGPT gratuito) já resolve
hoje. O único caso de uso diferenciado observado (exame de documento
jurídico com pedido de "defesa") também é hoje suportado nativamente por
ChatGPT/Claude com upload de arquivo. Isso sugere que o critério de
falsificação está satisfeito na direção negativa: a alternativa mais
simples parece suficiente para os casos de uso reais observados até
agora.
