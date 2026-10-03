# 11.7 — Riscos

RISCO 1: Ausência de validação de mercado além do próprio criador
- Probabilidade: ALTA (já confirmado — ver 11.2, N=1 usuário)
- Impacto: ALTO (todo o investimento de engenharia — 10 fases de
  auditoria/correção nesta sessão isolada, mais o desenvolvimento
  original — pode estar otimizando algo que não generaliza para
  nenhuma outra pessoa)
- Mitigação: definir e medir a métrica de 11.6 antes de investir mais
  engenharia; ou aceitar explicitamente que o projeto é uma ferramenta
  pessoal/de aprendizado, não um produto candidato a distribuição, e
  parar de avaliá-lo com critérios de produto

RISCO 2: Alternativas prontas (ChatGPT memory, Ollama+UI) resolvem a
maior parte dos casos de uso reais observados com menos esforço de
manutenção
- Probabilidade: MÉDIA-ALTA (evidência em 11.4 — casos de uso reais
  observados são majoritariamente simples)
- Impacto: MÉDIO (não invalida o valor de aprendizado técnico do
  projeto, mas invalida a tese de "isso deveria ser usado no lugar de X")
- Mitigação: nenhuma ação de código — decisão estratégica de escopo:
  o projeto compete em "controle e customização", não em "conveniência",
  e essa é a métrica que deveria ser vendida/medida, não velocidade de
  setup

RISCO 3: Dependência de fato do backend cloud (OpenRouter), apesar do
propósito declarado de independência
- Probabilidade: ALTA (confirmado nesta e em fases anteriores — backend
  ativo em toda a auditoria foi `openrouter`, não um modelo local)
- Impacto: MÉDIO — se o objetivo central é "IA 100% local", o sistema
  hoje não entrega isso na prática, embora a arquitetura pretenda
  priorizar Ollama. Mecanismo real, verificado em
  `_execute_with_fallback` (src/core/llm_manager.py:422): Ollama É
  tentado PRIMEIRO na cascata de geração quando `ollama_client` está
  configurado — a suposição inicial deste risco (de que
  `_detect_backend()` ignora Ollama por design) estava INCORRETA e foi
  corrigida após ler o código da cascata real, não apenas da função de
  detecção de rótulo. O que de fato acontece: `/health` reporta
  consistentemente `"ollama": {"ready": false}` em toda esta auditoria —
  o cliente Ollama existe mas o modelo não é confirmado disponível
  (`_model_available` falha), então a cascata cai automaticamente para
  OpenRouter a cada requisição. O sintoma observado (sempre openrouter)
  é real, mas a causa é uma falha de prontidão do Ollama neste ambiente,
  não uma falha de design da cascata de fallback.
- Mitigação: nenhuma ação de código nesta fase — investigar por que
  `ollama_client._model_available`/`_ensure_connection()` falha neste
  ambiente (o Ollama app está instalado e `ollama list` funciona, mas a
  verificação de prontidão do LLMManager falha) seria o próximo passo
  técnico, se o propósito de "IA local por padrão" for mantido como meta

RISCO 4: Complexidade de manutenção desproporcional ao valor validado
- Probabilidade: MÉDIA (a base de código já exigiu, só nesta sessão de
  auditoria: correção de segurança P0, remoção de dívida técnica,
  reescrita de 13 asserções de teste, remoção de 2 arquivos de teste
  obsoletos, reorganização completa do boundary do repositório)
- Impacto: MÉDIO-ALTO — esforço de engenharia real e não-trivial sendo
  investido sem métrica de valor correspondente (ver 11.6)
- Mitigação: pausar novo desenvolvimento de features até que a Fase 11
  produza uma decisão; se PROSSEGUIR, atrelar todo trabalho futuro a uma
  métrica de uso real, não a "mais uma funcionalidade"

RISCO 5: Segredo já vazado (achado da Fase 7/8, mitigado mas registrado
aqui como risco residual)
- Probabilidade: BAIXA (chave já rotacionada, conforme confirmado pelo
  usuário na Fase 7)
- Impacto: BAIXO agora, mas ALTO se recorrer — o padrão observado
  (chave hardcoded em `test_orch.py`, além do `.env`) sugere hábito de
  colar credenciais em arquivos de script ad-hoc
- Mitigação: já parcialmente endereçada (`.gitignore` corrigido,
  `test_orch.py` deletado); recomendação preventiva: nunca colar chaves
  reais em scripts de teste manuais, usar variável de ambiente sempre
