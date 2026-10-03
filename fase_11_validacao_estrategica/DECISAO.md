# === DECISÃO ESTRATÉGICA — FASE 11 ===

## EVIDÊNCIA COLETADA

| Pilar | Status |
|---|---|
| Propósito | HIPÓTESE (inferido da documentação, nunca declarado explicitamente como transformação; tensionado pelo achado de que o backend real usado é cloud, não local) |
| Usuário | EVIDÊNCIA (para "N=1, é o próprio desenvolvedor") / UNKNOWN (para "existe mercado externo") |
| Dor | EVIDÊNCIA PARCIAL (uso real esporádico confirmado, incluindo 1 tarefa não-trivial) / HIPÓTESE (generalização para qualquer outra pessoa) |
| Alternativas | EVIDÊNCIA (alternativas prontas existem e cobririam a maioria dos casos de uso reais observados) |
| Diferencial | HIPÓTESE (existe tecnicamente; não validado como percebido/valorizado) |
| Métricas | UNKNOWN (nenhuma baseline, meta, ou critério de sucesso/falha jamais foi instrumentado) |
| Riscos | 5 listados, todos com evidência de suporte (ver 07_riscos/riscos.md) |
| Kill Condition | DEFINIDA (4 condições mensuráveis) mas nunca instrumentada |

## DECISÃO

**[X] MATAR** — como candidato a produto/ferramenta com tese de mercado
validada.

Não confundir com "apagar o código". Esta decisão é sobre o FRAMEWORK de
validação estratégica pedido pelo Arquiteto (propósito-usuário-dor-
alternativa-diferencial-métrica), não sobre o valor do repositório como
artefato técnico ou de aprendizado — esse valor é real e não depende
desta decisão.

## JUSTIFICATIVA

A regra de engajamento definida pelo próprio Arquiteto é explícita: *"Se
não houver evidência suficiente para decidir, a decisão padrão é
MATAR."* Aplicando essa regra ao que foi de fato coletado nesta fase:

1. **Não existe usuário externo validado.** Toda evidência (git log,
   sessões, conteúdo real das memórias) aponta para um único usuário: o
   próprio desenvolvedor. Isso não é uma suposição — é o resultado de
   inspecionar diretamente o conteúdo de `data/memoria.db` e o histórico
   de commits.

2. **A dor é real, mas não validada além do criador**, e a amostra (71
   interações em 7 dias ao longo de 3 meses) é majoritariamente
   exploratória (saudações, testes de memória, perguntas sobre a
   identidade do assistente), não recorrência de uma tarefa de alto
   valor. O único caso de uso genuinamente não-trivial (exame de
   documento jurídico) é também plenamente atendido por alternativas já
   existentes com upload de arquivo nativo.

3. **As alternativas mais simples parecem suficientes** para os casos de
   uso reais observados até agora — o critério de falsificação do pilar
   11.4 (Alternativas) foi satisfeito na direção negativa: se "não fazer
   nada" ou "usar a ferramenta pronta" resolve o caso real, a dor não é
   forte o suficiente para justificar manter uma infraestrutura própria.

4. **O diferencial técnico existe, mas nunca foi testado contra a
   pergunta que importa**: "isso muda a decisão de qual ferramenta usar
   no dia a dia?" — porque o único usuário é também quem construiu a
   ferramenta, o que contamina qualquer leitura de preferência revelada.

5. **Zero métricas de valor foram definidas ou coletadas** em qualquer
   momento da vida do projeto, apesar do sistema já expor telemetria
   técnica robusta (`/metrics`) que poderia ter sido estendida para
   isso a custo baixo.

6. **Sinal econômico de alerta já observável nesta própria sessão**: o
   esforço de engenharia investido só nesta auditoria (10 fases,
   dezenas de commits, correções de segurança e arquitetura) excede
   visivelmente o uso real acumulado em 3 meses de existência do
   projeto.

## O QUE ISSO NÃO SIGNIFICA

- Não significa que o código deve ser deletado — ele tem valor
  demonstrado de aprendizado técnico (a própria complexidade da
  arquitetura multi-backend, multi-agente, com memória persistente, é
  um portfólio técnico substancial, confirmado funcional por esta
  auditoria).
- Não significa que a dor original (querer um assistente de IA local,
  privado, com memória) seja falsa ou boba — é uma dor real e comum.
  Significa que ELA NÃO FOI VALIDADA como suficientemente forte para
  justificar a manutenção contínua de uma solução própria, em vez de
  usar uma pronta.
- Se o objetivo real do Nex sempre foi "ferramenta pessoal + prática de
  engenharia", e não "produto para terceiros", então este framework de
  validação de produto simplesmente não se aplica da forma como foi
  pedido — e a pergunta certa não é PROSSEGUIR/PIVOTAR/MATAR, é "isso
  ainda vale meu tempo como projeto pessoal?", que é uma decisão
  diferente, pessoal, e fora do escopo desta auditoria técnica.

## SE A INTENÇÃO FOR RECONSIDERAR PROSSEGUIR

O caminho mais barato para transformar HIPÓTESE em EVIDÊNCIA, sem
escrever nenhum código novo além de rotulagem manual: instrumentar as 4
kill conditions do pilar 11.8 por 4-8 semanas, distinguindo
manualmente sessões de "uso real" vs. "teste/desenvolvimento" em
`data/sessions/`, e revisitar esta decisão com dados prospectivos em vez
de retrospectivos.
