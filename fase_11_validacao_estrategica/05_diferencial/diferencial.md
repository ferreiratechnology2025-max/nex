# 11.5 — Diferencial

DIFERENCIAL (conforme a arquitetura sugere, não conforme validado por
uso comparativo real):
Controle total sobre dados e execução — memória e documentos nunca saem
da máquina do usuário por padrão (SQLite/FAISS locais), com opção de
zero custo monetário (fallback OpenRouter free-tier, modelos locais via
Ollama), mais um sistema de orquestração multi-agente (Researcher →
Analyst → Writer) que ferramentas de chat genéricas não oferecem
nativamente.

COMPARAÇÃO COM ALTERNATIVA:
- Alternativa (ChatGPT com memory / Claude / IA local pronta): setup
  quase nulo, memória e upload de documento já nativos, sem manutenção
  de infraestrutura.
- Nex: exige clonar repositório, configurar ambiente, entender
  arquitetura multi-backend, manter banco de dados e índice FAISS
  próprios. Em troca, oferece dados 100% locais por padrão e
  customização total (agentes, regras, backend).
- Vantagem mensurável: NENHUMA MEDIDA. Não há benchmark comparando
  qualidade de resposta, latência, ou taxa de sucesso do Nex contra
  ChatGPT/Claude/outra ferramenta local em tarefas equivalentes.

STATUS: HIPÓTESE

FONTE: nenhuma medição comparativa existe no repositório. O diferencial
técnico (privacidade + orquestração multi-agente + zero custo) é real
como CAPACIDADE do sistema (confirmado por esta auditoria: memória
persistente funciona, `/health` reporta múltiplos backends, agentes
Researcher/Analyst/Writer existem em `src/agents/`), mas não há evidência
de que esse diferencial é PERCEBIDO ou VALORIZADO pelo único usuário
observado — o uso real registrado não distingue entre "usei o Nex porque
ele é melhor" e "usei o Nex porque eu o construí e queria testá-lo".

## Critério de falsificação
Se a alternativa mais simples (ChatGPT/Claude com memória nativa, ou
Ollama+UI pronta) for "suficientemente boa" para as tarefas reais do
usuário, o diferencial não se sustenta na prática, mesmo que exista no
papel. Como já registrado em 11.4: os casos de uso reais observados
(saudações, testes de memória, um exame de documento jurídico) são,
todos, atendíveis por alternativas prontas com esforço de setup muito
menor. Isso não invalida o diferencial TÉCNICO (privacidade, controle,
zero custo, orquestração), mas indica que, até o momento, ele não foi
testado contra a pergunta "isso muda a decisão de qual ferramenta usar
no dia a dia?" — porque o único usuário é também quem construiu a
ferramenta, o que contamina qualquer leitura de preferência revelada.
