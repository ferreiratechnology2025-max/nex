# 11.2 — Usuário

USUÁRIO COM DOR: Desenvolvedor(a) individual (aparentemente o próprio
autor) que quer um assistente de IA com memória, rodando localmente,
como projeto pessoal/portfólio e/ou ferramenta de uso próprio.

USUÁRIO QUE USA: A mesma pessoa — CORREÇÃO APÓS INSPEÇÃO DIRETA DO
CONTEÚDO DAS MEMÓRIAS (não apenas dos metadados): as 71 linhas de
`data/memoria.db` foram lidas diretamente. O usuário real se identifica
consistentemente como "Romel" em múltiplas conversas ao longo de 7 datas
distintas (20/04, 21/04, 22/04, 01/06, 02/06, 29/06, 14/07/2026 — ~3
meses de uso espaçado, não uma rajada de teste). "Romel" também é o nome
associado à conta autenticada do Hugging Face nesta própria sessão
("Romel1001"), reforçando que se trata do desenvolvedor/autor do
projeto usando sua própria ferramenta.
`data/sessions/*/profile.json` mostra o nome "João" em 2 das 7 sessões —
esse SIM é dado de teste (coincide com a fixture usada em vários arquivos
de teste: "Meu nome é João e sou programador Python"). As duas fontes
não se sobrepõem: "João" = sessões de teste automatizado; "Romel" = uso
real do próprio desenvolvedor, incluindo pelo menos um caso de uso
genuíno fora de teste — exame de documentos jurídicos pessoais ("examine
'MEMORIAS MINISTERIO PUBLICO.pdf'... e faça a defesa", em
`C:\Users\becat\Documents\processo\`).

USUÁRIO QUE PAGA: Ninguém identificado. Não há modelo de cobrança,
plano, checkout, ou qualquer artefato de monetização em todo o
repositório (README, Nex.spec.md, docker-compose.yml, config.py — nenhum
menciona billing, planos, ou usuários pagantes). O backend padrão
(OpenRouter free tier) é desenhado explicitamente para não exigir
pagamento.

STATUS: EVIDÊNCIA (para "não há usuário externo comprovado") /
HIPÓTESE (para "quem seria o usuário-alvo se o projeto fosse distribuído")

FONTE: `git log`, `data/sessions/*/profile.json`, ausência de qualquer
artefato de billing/planos no repositório completo (confirmado durante
toda a Fase 8/9 desta auditoria, que inventariou 100% dos arquivos do
projeto).

## Critério de falsificação
Saberíamos que EXISTE usuário para o Nex se houvesse: múltiplos
`git log --format="%ae"` (emails de autor) distintos, múltiplas sessões
com nomes de perfil distintos e coerentes com pessoas reais (não "João"
repetido como fixture de teste), ou qualquer telemetria/analytics
mostrando acessos de origens/IPs diferentes ao longo do tempo. Nenhum
desses sinais foi encontrado nesta auditoria.

## Conclusão honesta (revisada após inspeção do conteúdo real)
Toda a evidência disponível aponta para um projeto de UM único usuário
real (o desenvolvedor "Romel"), sem instância de "usuário com dor"
distinta de "usuário que constrói a ferramenta" — mas, diferente da
hipótese inicial, há EVIDÊNCIA (não apenas suposição) de uso genuíno e
repetido ao longo de ~3 meses, incluindo pelo menos um caso de uso real
não-trivial (análise de documento jurídico pessoal). Isso é "dogfooding"
válido — o criador usa a própria ferramenta para uma tarefa real —, mas
continua sendo N=1: não há nenhum segundo usuário identificado em nenhum
artefato do repositório. Não invalida o valor do projeto como ferramenta
pessoal — mas invalida qualquer afirmação de que existe um mercado, um
usuário externo validado, ou um "product-market fit" nos moldes deste
framework.
