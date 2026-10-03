# 11.8 — Kill Condition

MATAR O NEX (como candidato a produto/ferramenta distribuída — não como
código do repositório, que continua tendo valor de aprendizado
independente desta decisão) SE:

1. CONDIÇÃO DE ADOÇÃO
   Menos de 1 sessão de uso espontâneo (fora de contexto de
   desenvolvimento/teste/auditoria) por semana, medida ao longo de 4
   semanas consecutivas, a partir da data em que essa métrica passar a
   ser rastreada.
   Status hoje: NÃO MEDIDO PROSPECTIVAMENTE (só há dado retrospectivo
   não rotulado — ver 11.6).

2. CONDIÇÃO DE VALOR
   Nas próximas 10 tarefas reais (não-teste) em que o usuário considerar
   usar o Nex, ele optar pela alternativa mais simples (ChatGPT/Claude/
   outra ferramenta pronta) em mais de 70% dos casos.
   Status hoje: NÃO MEDIDO — não há registro comparativo de escolha
   entre Nex e alternativas.

3. CONDIÇÃO ECONÔMICA
   Custo de manutenção (tempo de engenharia) por mês exceder o tempo que
   o próprio uso do Nex economiza no mesmo período. Proxy observável: se
   o tempo gasto corrigindo/mantendo o sistema (como as ~10 fases desta
   auditoria) continuar superando, mês a mês, o tempo de uso real
   registrado em `data/memoria.db`.
   Status hoje: DESEQUILÍBRIO JÁ OBSERVÁVEL NESTA PRÓPRIA SESSÃO — uma
   única sessão de auditoria/correção consumiu esforço de engenharia
   muito maior do que as 71 interações de uso acumuladas em 3 meses.
   Isso não decide a questão sozinho (auditoria de dívida técnica é
   investimento único, não recorrente), mas é um sinal de alerta.

4. CONDIÇÃO TECNOLÓGICA
   Se um concorrente (ex.: ChatGPT memory, ferramentas de IA local
   prontas) passar a oferecer o diferencial central do Nex (privacidade
   local + zero custo + memória persistente) com esforço de setup igual
   ou menor.
   Status hoje: PARCIALMENTE JÁ VERDADEIRO — ChatGPT já tem memória
   nativa; Ollama+UIs prontas já oferecem "IA local sem custo". O
   diferencial exclusivo remanescente do Nex é a orquestração
   multi-agente (Researcher/Analyst/Writer) e o controle total de
   arquitetura — nenhum dos dois foi validado como algo que o usuário
   real valoriza (ver 11.5).

STATUS: DEFINIDA (as 4 condições têm critério mensurável), mas NENHUMA
FOI INSTRUMENTADA PARA MEDIÇÃO CONTÍNUA até o momento desta fase.
