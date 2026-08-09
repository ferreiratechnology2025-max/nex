# Classificação — .py untracked na raiz (1 arquivo)

## test_orch.py
- **Origem:** script procedural (`async def main(): ...` sob
  `if __name__ == "__main__"`), não é suíte pytest (nome bate com `test*`
  do pytest mas a função top-level chama-se `main`, não `test_*` — não
  seria coletado como teste; a coleta em si nunca foi tentada porque o
  arquivo está na raiz, fora do escopo de `pytest tests/`).
- **Finalidade:** smoke-test manual de ponta a ponta — instancia
  `LLMManager`, `Coordinator` e `MemoriaPersistente` reais e roda uma
  geração + orquestração completa.
- **Dependências:** `LLMManager(cfg)`, `Request(...)`, `Coordinator(
  llm_manager=lm, memory_manager=m)`, `MemoriaPersistente(":memory:", "",
  10)` — todos os símbolos e assinaturas conferem com a API atual
  (`Coordinator` e `MemoriaPersistente` confirmados existentes e com essa
  assinatura posicional em auditorias anteriores desta fase). Ao contrário
  dos dois scripts deletados na Etapa 3, este NÃO usa nenhuma API
  inexistente.
- **Duplicação:** nenhuma — é o único teste manual de orquestração completa
  ponta a ponta (LLM + Coordinator + memória).

## ⚠️ ACHADO DE SEGURANÇA (P0)
Linha 12 do arquivo contém a `OPENROUTER_API_KEY` **hardcoded em texto
puro** dentro de um dicionário de configuração:
```
cfg = {
    "OPENROUTER_API_KEY": "sk-or-v1-...<REDACTED>...",
    "USE_HUGGINGFACE": "false",
}
```
- É a MESMA chave que motivou o P0 da Fase 7, já rotacionada conforme
  confirmação do usuário na Etapa 1.
- O valor não foi reimpresso neste relatório (nem no terminal desta sessão)
  além da leitura inicial do arquivo — tratado como sensível daqui em
  diante.
- Mesmo com a chave já revogada, hardcoding de credenciais em arquivo-fonte
  é prática de risco por si só (reaparece em qualquer futuro `git add .`
  acidental, em backups, em buscas de texto).

- **Valor:** MÉDIO como ferramenta de smoke-test (única cobertura de
  orquestração ponta-a-ponta), mas **DESQUALIFICADO para PROMOTE** pelo
  hardcoding de credencial.

- **Classificação: DELETE**
- Justificativa: não pode ser versionado como está (credencial hardcoded).
  Se o smoke-test de orquestração ponta-a-ponta for considerado valioso,
  deve ser reescrito lendo a chave de variável de ambiente (`os.environ`)
  antes de qualquer promoção — mas isso é uma reescrita, não uma
  classificação, e está fora do escopo desta etapa (não modificar
  arquivos). Recomendo remoção imediata do arquivo como está.
