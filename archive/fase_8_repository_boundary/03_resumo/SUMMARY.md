# Fase 8.1 — Repository Boundary / Ownership Audit — Resumo

## Inventário total classificado: 29 itens untracked
(24 `.py` + docker-compose.yml + pytest.ini + 5 diretórios − 2 já contados
dentro dos `.py`... nota: contagem por grupo abaixo é exaustiva e não soma
trivialmente porque diretórios contêm múltiplos arquivos não listados
individualmente)

## Tabela consolidada

| Grupo | Item | Classificação | Motivo (1 linha) |
|---|---|---|---|
| src/ | 13 arquivos (agents/*, core/document_*, core/openrouter_client, core/web_search*, metrics.py, ws_handler.py, core/__init__) | **PROMOTE** (todos) | Importados e executados pelo entrypoint real, confirmado em runtime |
| tests/ | test_api_gateway.py | PROMOTE | 8/4, testa componente crítico |
| tests/ | test_config.py | PROMOTE | 19/0 |
| tests/ | test_fallback.py | PROMOTE | 2/2, API real |
| tests/ | test_fallback_activation.py | PROMOTE (ressalva) | 0/2, investigar causa antes de confiar |
| tests/ | test_llm_manager.py | PROMOTE (ressalva) | 1/7, investigar causa antes de confiar |
| tests/ | test_memory_opt.py | PROMOTE (ressalva) | 2/5, testa o módulo corrigido na Fase 7 |
| tests/ | test_web_search.py | PROMOTE | 11/5 |
| tests/ | test_ws_metrics.py | PROMOTE | 13/1 |
| tests/ | quick_test.py | KEEP-UNTRACKED | passa mas sem asserts, falso sinal de qualidade |
| tests/ | debug_test.py | KEEP-UNTRACKED | não coletado pelo pytest, ferramenta manual |
| raiz | test_orch.py | **DELETE** | credencial hardcoded em texto puro (P0 segurança) |
| config | docker-compose.yml | PROMOTE | infra real, sem segredos |
| config | pytest.ini | PROMOTE | correção da própria Fase 7, Etapa 2 |
| dirs | data/ | KEEP-UNTRACKED | estado de runtime, não código |
| dirs | monitor/ | PROMOTE | referenciado em docker-compose.yml |
| dirs | .streamlit/ | PROMOTE | config de streamlit_app.py (já tracked) |
| dirs | test_memory/ | **DELETE** | resíduo órfão do script já deletado na Etapa 3 |
| dirs | venv/ | KEEP-UNTRACKED | ambiente virtual, nunca versionado |
| docs | .gitignore | **PROMOTE (prioridade máxima)** | o próprio arquivo de exclusão nunca foi commitado — achado fora do grep original — corrigido na 8.2B.1 para ignorar `data/` por completo |
| docs | .dockerignore | PROMOTE | Dockerfile + docker-compose.yml confirmados; conteúdo correto, já ignorava `data/` por completo — achado da 8.2B.2 |
| docs | requirements.txt | PROMOTE | manifesto validado contra pip freeze |
| docs | README.md | PROMOTE | descreve corretamente o projeto real |
| docs | SYSTEM_MAP.md | PROMOTE | descreve corretamente o projeto real |
| docs | Nex.spec.md | PROMOTE | referenciado por teste já promovido |
| docs | CLAUDE.md | ~~ARCHIVE~~ → **PROMOTE (revisado na 8.2C.0)** | descreve corretamente agents/+rules/, consumido por 7 arquivos de agents/, README já promovido documenta o toolkit como feature deliberada |
| toolkit | agents/ (64 arquivos) | **PROMOTE (8.2C.0)** | nunca inventariado na 8.1; documentado como feature no README; zero acoplamento de código com src/ |
| toolkit | rules/ (104 arquivos) | **PROMOTE (8.2C.0)** | idem |

## Contagem por classificação

- **PROMOTE:** 13 (src/) + 8 (tests/) + 2 (config) + 2 (monitor, .streamlit) + 4 (docs) = **29 itens**
- **KEEP-UNTRACKED:** 2 (tests/) + 2 (data/, venv/) = **4 itens**
- **ARCHIVE:** 1 (CLAUDE.md)
- **DELETE:** 2 (test_orch.py, test_memory/)

## Achados críticos desta etapa

### 🔴 P0 — Nova exposição de credencial (test_orch.py)
`test_orch.py`, na raiz, contém a `OPENROUTER_API_KEY` hardcoded em texto
puro. É a mesma chave já rotacionada na Fase 7/Etapa 1, mas o arquivo em si
nunca havia sido examinado até agora. Classificado DELETE. Valor não
reimpresso nesta auditoria além da leitura de conteúdo inicial.

### 🟡 Resíduo órfão adicional (test_memory/)
Mesma classe de bug já corrigida nas Etapas 4-5 da Fase 7 (default
implícito de path relativo criando estado fragmentado), desta vez
manifestado como diretório em vez de arquivo único. Causa-raiz (o script
que o criava) já foi removida; o diretório é lixo remanescente.

### 🟡 Documentação desalinhada (CLAUDE.md)
O `CLAUDE.md` na raiz do repositório descreve um projeto inteiramente
diferente do Nex Chat (um "Claude Code plugin" com agents/skills/commands).
Isso já causou confusão de contexto nesta própria sessão de auditoria — o
arquivo foi injetado como contexto de sistema descrevendo um projeto que
não corresponde ao que estava sendo auditado.

### 🔴 P0 — .gitignore nunca foi commitado (achado fora do grep original desta etapa)
O grep inicial desta etapa (`\.(md|txt|pdf|docx)$`) não captura `.gitignore`,
então o arquivo ficou fora do inventário até uma verificação factual
adicional. `git status --porcelain -- .gitignore` confirma `?? .gitignore`
— nunca foi commitado. Suas regras (que já cobrem `.env`, `data/memoria.db`,
`__pycache__/` etc.) nunca estiveram em vigor do ponto de vista do git para
um clone fresco do repositório. Classificado PROMOTE com prioridade máxima
— deve ser o primeiro `git add` da Fase 8.2.

### 🟢 Confirmação positiva — a maioria do código é produção viva, não experimento
Ao contrário da suposição inicial de que "untracked = suspeito", 29 dos 35
itens classificados (83%) são **PROMOTE** — código e configuração que já
roda em produção real (confirmado por execução do servidor e da suíte de
testes nesta e nas fases anteriores), simplesmente nunca commitados. O
problema real não é "código experimental infiltrado", é **higiene de
controle de versão** — o projeto cresceu sem que grande parte do trabalho
fosse commitado.

## Estado após esta etapa
Nenhum arquivo foi modificado, movido, adicionado ao git ou removido nesta
etapa (regra de engajamento: apenas classificar). As ações (`git add`,
`rm`, mover para `archive/`) ficam para a Fase 8.2, mediante aprovação do
Arquiteto.
