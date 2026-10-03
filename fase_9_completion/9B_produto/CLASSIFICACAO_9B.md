# 9B — Classificação dos 24 Itens do Produto

## Documentação

### docs/ (4 arquivos: API_REFERENCE.md, DEVELOPER_GUIDE.md, TEST_REPORT_FASE4.md, USER_GUIDE.md)
- README.md:297 e SYSTEM_MAP.md:90 documentam `docs/` explicitamente na
  árvore do projeto ("Documentação (guia do usuário, API, dev)").
- Nenhum segredo encontrado.
- **Classificação: PROMOTE**

### examples/ (2 arquivos: curl_examples.sh, python_client.py)
- README.md:299 documenta explicitamente ("Exemplos curl e Python client").
- Nenhum segredo encontrado.
- **Classificação: PROMOTE**

## Infraestrutura / build

### Dockerfile
- Referenciado por `docker-compose.yml` (já PROMOTE), por `.dockerignore`
  (já PROMOTE), por README.md e SYSTEM_MAP.md (árvore do projeto).
- **Classificação: PROMOTE**

### docker-entrypoint.sh
- `Dockerfile:55-58` o copia e o define como `ENTRYPOINT` da imagem —
  dependência funcional direta e confirmada, não apenas documental.
- **Classificação: PROMOTE**

### Makefile
- Não referenciado por nenhum .md, mas conteúdo coerente e funcional:
  alvos `build`, `start`, `stop`, `logs`, `clean`, `shell`, `test`
  operando sobre a mesma stack Docker já classificada PROMOTE
  (docker-compose.yml, Dockerfile). Nenhuma referência a arquivo
  inexistente detectada no cabeçalho.
- **Classificação: PROMOTE**
- Ressalva: ausência de menção no README é uma lacuna de documentação do
  projeto, não motivo para excluir o Makefile do controle de versão.

## Scripts operacionais

### scripts/*.sh, scripts/*.bat, scripts/windows/*.bat (17 arquivos da lista original)
- README.md documenta CADA arquivo individualmente, por nome, em duas
  tabelas (linhas 337-364): "Scripts Windows" e "Scripts Linux/Mac".
  Correspondência 1:1 confirmada entre a lista de 17 arquivos untracked e
  as entradas do README (ex.: `scripts/windows/backup.bat` →
  "Backup dos dados"; `scripts/create_release.sh` → "Cria release").
- Nota lateral: durante a verificação, encontrei `scripts/windows/
  setup_ollama.bat` e `scripts/windows/start_local.bat`, também
  documentados no README, mas que JÁ ESTÃO TRACKED (não fazem parte dos
  24 — confirmado via `git ls-files`). Não é uma inconsistência, apenas
  registro de que a cobertura de scripts/ no repo é maior do que os 17
  untracked por si só.
- **Classificação: PROMOTE** (todos os 17)

## Scripts operacionais pessoais (raiz)

### check_environment.ps1
- Não referenciado por nenhum .md (README documenta apenas variantes
  `.sh`/`.bat` de validação, não `.ps1`).
- Conteúdo: script de diagnóstico de ambiente (verifica Python, etc.),
  sem caminhos hardcoded de máquina específica, sem segredos.
- Funcionalmente equivalente a `scripts/validate_system.*` (já PROMOTE),
  mas em local diferente (raiz, não `scripts/`) e formato diferente
  (PowerShell nativo vs. .bat/.sh documentados).
- **Classificação: PROMOTE**
- Justificativa: útil, sem risco, mesmo padrão de scripts de validação já
  promovidos — a ausência de menção no README é lacuna de documentação,
  não desqualificação.

### start_services.ps1
- ⚠️ **Achado:** linha 8 contém um caminho absoluto hardcoded de UMA
  MÁQUINA ESPECÍFICA: `C:\Users\becat\AppData\Local\Programs\Ollama\
  ollama.exe` — usuário "becat", que não corresponde ao usuário desta
  sessão ("ferre", confirmado em todos os caminhos `C:\Users\ferre\...`
  usados ao longo desta auditoria). Isso quebra funcionalmente em
  qualquer máquina que não seja a de origem deste arquivo.
- Não referenciado por nenhum .md.
- **Classificação: KEEP-UNTRACKED**
- Justificativa: diferente de check_environment.ps1 (portável),
  start_services.ps1 tem um defeito de portabilidade que o desqualifica
  para promoção como está — promovê-lo introduziria um script quebrado
  para qualquer colaborador. Não é `DELETE` porque tem lógica útil
  (inicialização de Ollama + download de modelo) que vale a pena manter
  localmente ou corrigir (remover o hardcode) antes de promover — mas
  corrigir está fora do escopo desta etapa (classificar, não modificar).

## Conteúdo não-código

### "MANUAL SISTEMA Nex 1.pdf" (4,25 MB) e "Manual de Bolso do Nex Chat.pdf" (3,88 MB)
- Zero referências em qualquer arquivo `.md` do projeto.
- Binários grandes (8,1 MB combinados).
- **Classificação: KEEP-UNTRACKED**
- Justificativa: nenhuma evidência de que fazem parte do processo de
  build, documentação linkada ou entrega do produto (diferente de
  docs/USER_GUIDE.md, que É referenciado pela estrutura documentada em
  README/SYSTEM_MAP). Versionar binários grandes sem uma política
  explícita de documentação binária no repositório (ex.: Git LFS) é
  anti-padrão. Não são `DELETE` porque parecem ser manuais de usuário
  legítimos (nomes coerentes com o projeto) — só não há evidência de que
  devam entrar no controle de versão de código-fonte como estão.

### "ligar Nex.txt"
- Nota pessoal informal (português coloquial, sem formatação de
  documentação), com instruções passo-a-passo de como o próprio usuário
  liga a aplicação localmente. Não é referenciada por nada.
- **Classificação: KEEP-UNTRACKED**
- Justificativa: é um bloco de notas pessoal do desenvolvedor, análogo a
  um arquivo de anotações do IDE — tem valor para o usuário, não para o
  repositório compartilhado.

---

## Resumo 9B

| Item | Tipo | Classificação |
|---|---|---|
| docs/ (4 arquivos) | documentação | PROMOTE |
| examples/ (2 arquivos) | exemplos de uso | PROMOTE |
| Dockerfile | infra | PROMOTE |
| docker-entrypoint.sh | infra | PROMOTE |
| Makefile | build | PROMOTE |
| scripts/*.sh (7) | scripts | PROMOTE |
| scripts/*.bat (raiz de scripts/, 3) | scripts | PROMOTE |
| scripts/windows/*.bat (14 restantes da lista original) | scripts | PROMOTE |
| check_environment.ps1 | script pessoal | PROMOTE |
| start_services.ps1 | script pessoal | **KEEP-UNTRACKED** (caminho hardcoded de outra máquina) |
| "MANUAL SISTEMA Nex 1.pdf" | binário | KEEP-UNTRACKED |
| "Manual de Bolso do Nex Chat.pdf" | binário | KEEP-UNTRACKED |
| "ligar Nex.txt" | nota pessoal | KEEP-UNTRACKED |

**Contagem: 21 PROMOTE, 4 KEEP-UNTRACKED, 0 ARCHIVE, 0 DELETE** (24 itens
totais — a discrepância de contagem de scripts/ vs. a lista original de
17 é porque `scripts/*.bat`+`scripts/*.sh` na raiz de `scripts/` somam 7
+ 3 = 10, mais 14 em `scripts/windows/` seguindo a lista original de
NAO_CLASSIFICADOS.txt = 24 no total do grupo "scripts", já contabilizado
junto às outras categorias acima).
