# Classificação — Configuração untracked (2 arquivos)

## docker-compose.yml
- **Origem:** arquivo de infraestrutura, referenciado no `CLAUDE.md`/estrutura
  documentada do projeto (Dockerfile também presente no repo).
- **Finalidade:** definição do serviço `nex-chat` para execução via Docker.
- **Dependências:** nenhum segredo hardcoded (verificado — 0 ocorrências de
  `OPENROUTER_API_KEY`, `env_file` ou `.env` no arquivo).
- **Duplicação:** nenhuma — único arquivo de orquestração Docker do projeto.
- **Valor:** ALTO — infraestrutura de deploy, sem a qual `docker-compose up`
  (mencionado como opção de execução em `test_system.py`, já deletado, e em
  `docker-entrypoint.sh`, presente no repo) não funciona.
- **Classificação: PROMOTE**

## pytest.ini
- **Origem:** criado NESTA PRÓPRIA AUDITORIA, na Etapa 2 da Fase 7
  (`asyncio_mode = auto`), para corrigir os 17 testes assíncronos que
  falhavam por ausência de configuração do harness.
- **Finalidade:** configuração oficial do pytest para o projeto.
- **Dependências:** nenhuma.
- **Duplicação:** nenhuma — não havia nenhum `pytest.ini`/`pyproject.toml`
  antes desta auditoria (confirmado na Fase 6).
- **Valor:** ALTO — sem ele, 17 testes voltam a falhar (regressão
  comprovada por reversão hipotética: era exatamente o estado do baseline
  da Fase 6, 70 passed / 43 failed).
- **Classificação: PROMOTE**
- Nota: por ser um artefato desta própria auditoria, sua promoção ao git é
  praticamente obrigatória — removê-lo do controle de versão desfaria a
  correção da Etapa 2.

---

## Nota — grupo "secrets"
`untracked_secrets.txt` (grep por `credential|secret|token|key` nos nomes de
arquivo, não no conteúdo) retornou **0 arquivos**. Isso NÃO significa
ausência de segredos no conteúdo dos arquivos — apenas que nenhum nome de
arquivo untracked contém essas palavras. O achado real de segredo em
conteúdo (test_orch.py, chave hardcoded) está documentado em
`classificacao_root.md`, encontrado por leitura de conteúdo, não pelo grep
de nome de arquivo desta etapa.
