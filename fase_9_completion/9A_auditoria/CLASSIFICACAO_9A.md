# 9A — Classificação dos Diretórios de Auditoria

Critério aplicado: mesmo padrão das fases anteriores — origem, consumidores,
valor, evidência antes de decisão.

## Fato comum aos 5 diretórios
`grep` por referência cruzada em `*.py`/`*.md`/`*.sh`/`*.bat` fora dos
próprios diretórios de auditoria: **zero ocorrências**. Nenhum script,
nenhuma documentação, nenhum código do Nex Chat referencia qualquer um
destes 5 diretórios. São produto desta sessão de auditoria conversacional,
não parte do sistema Nex Chat.

## auditoria_nex/ (161K)
- **Origem:** Fase 0 desta conversa — coleta de baseline factual do
  ambiente (estrutura, configs, dependências, Ollama, dados, logs, health).
- **Conteúdo:** 10 subpastas numeradas com outputs brutos de comandos.
- **Consumidores:** nenhum (confirmado acima).
- **Valor:** histórico da sessão de auditoria — útil como log de auditoria
  passada, sem valor operacional para o funcionamento do Nex Chat.
- **Classificação: ARCHIVE**
- Justificativa: tem valor como registro de proveniência (o que foi
  encontrado e quando), mas não pertence ao controle de versão do
  produto — nenhum outro artefato depende dele.

## auditoria_profunda/ (7.3M — majoritariamente bloat)
- **Origem:** Fases 2-5 desta conversa (investigação de DB duplicado,
  FAISS, rastreamento de código, erro de coleta de testes).
- **Achado de qualidade:** `01_seguranca/outras_credenciais.txt` sozinho
  responde por ~7.6MB dos ~7.3M totais reportados (nota: `du -sh` e o
  tamanho real do arquivo divergem porque o sistema de arquivos comprime/
  aloca em blocos; o arquivo tem 25.560 linhas, quando o comando original
  reportou 152 linhas ao ser gerado). Causa-raiz identificada agora: o
  comando original de grep recursivo em "." não excluía o próprio
  `auditoria_profunda/`, então em algum momento leu seu próprio arquivo de
  saída em progresso (auto-referência clássica de `grep ... > arquivo`
  quando o padrão de busca varre o diretório de destino), duplicando
  conteúdo já redigido. Confirmado: nenhum segredo em texto puro
  sobrevive no arquivo (`grep -c "sk-or-v1-..." → 0`).
- **Consumidores:** nenhum.
- **Valor:** mesmo raciocínio de auditoria_nex/, mas com o adicional de
  ser um artefato tecnicamente corrompido/inflado (bug do próprio processo
  de auditoria, não do produto).
- **Classificação: DELETE**
- Justificativa: diferente de auditoria_nex/ (que é limpo e serve como
  registro), este diretório carrega um artefato de 7.6MB que é lixo
  técnico (self-referential grep bug), não um registro útil. Seu valor
  histórico (schema do DB, dimensão do FAISS, rastreamento de código) já
  está integralmente resumido em `00_SINTESE.txt` (4KB) e replicado nas
  fases posteriores desta conversa — a preservação do detalhe bruto não
  compensa carregar um arquivo corrompido de 7.6MB no repositório.

## baseline_saude/ (128K)
- **Origem:** Fase 6 (baseline de saúde: pytest, GenerationConfig,
  servidor).
- **Consumidores:** nenhum.
- **Valor:** registro de um baseline específico, já superado pelos
  baselines subsequentes gerados dentro de `fase_7_correcao_controlada/`.
- **Classificação: ARCHIVE**
- Justificativa: conteúdo limpo (sem o problema de bloat de
  auditoria_profunda/), documenta uma decisão técnica real (causa-raiz do
  GenerationConfig) que teve consequência prática (DELETE de dois
  arquivos na Fase 7) — vale preservar como evidência, mas fora do
  controle de versão do produto.

## fase_7_correcao_controlada/ (424K)
- **Origem:** Fase 7 desta conversa (correções controladas: segurança,
  pytest-asyncio, testes obsoletos, db_path/index_path).
- **Consumidores:** nenhum.
- **Valor:** contém a evidência e os diffs que justificam o Commit B
  (728e7c5) já aplicado ao repositório. Tem valor de rastreabilidade —
  "por que essas duas linhas mudaram" tem resposta completa aqui.
- **Classificação: ARCHIVE**
- Justificativa: mesmo raciocínio de baseline_saude/, com peso adicional
  de rastreabilidade de um commit já mesclado no histórico do projeto.

## fase_8_repository_boundary/ (485K)
- **Origem:** Fase 8 desta conversa (classificação de untracked, staging,
  commits).
- **Consumidores:** nenhum.
- **Valor:** contém a evidência e a matriz de classificação completa que
  justificam o Commit A (67763fc) já aplicado — inclusive a lista dos 24
  itens ainda não classificados que esta própria Fase 9 está resolvendo.
- **Classificação: ARCHIVE**
- Justificativa: mesmo raciocínio — rastreabilidade de um commit já
  mesclado, incluindo o próprio `NAO_CLASSIFICADOS.txt` referenciado pela
  Fase 9 que está em andamento (auto-referência legítima, ao contrário da
  auto-referência acidental de auditoria_profunda/).

---

## Resumo 9A

| Diretório | Classificação | Ação |
|---|---|---|
| auditoria_nex/ | ARCHIVE | mover para archive/ |
| auditoria_profunda/ | **DELETE** | remover (artefato corrompido) |
| baseline_saude/ | ARCHIVE | mover para archive/ |
| fase_7_correcao_controlada/ | ARCHIVE | mover para archive/ |
| fase_8_repository_boundary/ | ARCHIVE | mover para archive/ (com ressalva: este próprio diretório está sendo escrito enquanto é classificado — mover só deve acontecer depois que toda a Fase 9 terminar) |

Nota de ordem de execução (não é ação desta etapa, só observação para a
etapa de execução): `fase_9_completion/` (esta pasta, ainda não criada
quando este diretório foi listado no prompt do Arquiteto) deveria seguir
o mesmo destino de `fase_8_repository_boundary/` uma vez concluída — não
foi incluída na lista de 5 porque ainda não existia no momento em que o
prompt da Fase 9 foi escrito.
