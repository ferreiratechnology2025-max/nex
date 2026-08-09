# Classificação — Diretórios e artefatos untracked (5 diretórios)

## data/
- **Conteúdo:** `config.json`, `memoria.db`, `memoria.index`, `sessions/`
  (com subpastas por sessão contendo `long_term_memories.json`,
  `profile.json`).
- **Finalidade:** persistência real do sistema em produção.
- **Evidência:** `data/memoria.db` e `data/memoria.index` são, desde a
  Fase 2-3 desta auditoria, a fonte de verdade confirmada por três ângulos
  independentes (schema SQLite, contagem FAISS, `/health` em runtime real —
  `memory_count: 71` em toda validação desta fase).
- **Valor:** CRÍTICO como dado, mas é ESTADO, não CÓDIGO — versionar um
  banco SQLite binário e sessões de usuário em texto (potencialmente com
  dados pessoais, ex.: "Meu nome é João...") no git é anti-padrão e risco
  de privacidade.
- **Classificação: KEEP-UNTRACKED**
- Justificativa: dado de runtime, não artefato de build. Deve permanecer
  fora do controle de versão, mas ativamente presente no `.gitignore`
  (hoje ausente — ver recomendações).

## monitor/
- **Conteúdo:** `index.html` — dashboard estático de monitoramento.
- **Finalidade:** interface de monitoramento servida via container Nginx
  separado.
- **Dependências:** referenciado explicitamente em `docker-compose.yml:54-60`
  (serviço `nex-monitor`, monta `./monitor:/usr/share/nginx/html:ro`). NÃO
  é montado pelo FastAPI (`src/api_gateway.py` só expõe `/static`, sem rota
  para `/monitor`) — é servido por um container Nginx dedicado, não pelo
  backend Python.
- **Duplicação:** nenhuma.
- **Valor:** ALTO — parte de uma stack de deploy real e documentada
  (docker-compose já classificado PROMOTE).
- **Classificação: PROMOTE**

## .streamlit/
- **Conteúdo:** `config.toml` (tema, porta 8501, configurações de servidor).
- **Finalidade:** configuração do Streamlit.
- **Dependências:** `streamlit>=1.39.0` está em `requirements.txt`;
  `streamlit_app.py` (na raiz) importa `streamlit` e **já está tracked no
  git** (confirmado: `git status --porcelain` não lista `streamlit_app.py`,
  ou seja, já está commitado e sem modificações). `.streamlit/config.toml`
  é a configuração oficial desse app já versionado.
- **Duplicação:** nenhuma.
- **Valor:** ALTO — configuração de uma aplicação que já faz parte do
  repositório oficial; sem ela, `streamlit_app.py` roda com defaults não
  documentados (tema, porta).
- **Classificação: PROMOTE**

## test_memory/
- **Conteúdo:** `long_term/long_term_memories.json`.
- **Finalidade:** NENHUMA finalidade de produção — é resíduo de execução.
- **Origem:** `test_system.py` (DELETADO na Etapa 3 desta Fase 7) chamava
  `MemoryManager(storage_path=Path("./test_memory"))`. Embora esse
  parâmetro (`storage_path`) nem sequer existisse na assinatura real da
  classe (a classe usa `db_path`/`index_path`, não `storage_path` — já
  documentado na Etapa 3), ALGUM processo, nesta mesma família de scripts
  obsoletos ou de execuções manuais anteriores, gravou este diretório.
  É exatamente a mesma classe de problema do órfão `D:\Nex\memoria.db`
  resolvida nas Etapas 4-5: resíduo de execução de script já removido.
- **Duplicação:** nenhuma finalidade a duplicar.
- **Valor:** NENHUM — não é referenciado por nenhum código atual, não é
  usado por nenhum teste ativo (os testes reais de memória usam
  `tempfile.mkdtemp()`, não este diretório fixo).
- **Classificação: DELETE**
- Justificativa: resíduo órfão da mesma natureza do `memoria.db` da raiz,
  já resolvido nas Etapas 4-5. Sua causa-raiz (o script que o criava) já
  foi removida; o diretório em si é lixo remanescente.

## venv/
- **Conteúdo:** ambiente virtual Python completo (milhares de arquivos de
  pacotes instalados).
- **Finalidade:** ambiente de execução local, não código-fonte.
- **Valor:** NENHUM para controle de versão — reproduzível a partir de
  `requirements.txt` (já tracked) via `pip install -r requirements.txt`.
- **Classificação: KEEP-UNTRACKED**
- Justificativa: padrão universal — ambientes virtuais nunca são
  versionados. Ausência confirmada de qualquer entrada de `.gitignore`
  cobrindo isso é o achado real (ver recomendações).

---

## Resumo do grupo

| Diretório | Classificação |
|---|---|
| data/ | KEEP-UNTRACKED |
| monitor/ | PROMOTE |
| .streamlit/ | PROMOTE |
| test_memory/ | DELETE |
| venv/ | KEEP-UNTRACKED |
