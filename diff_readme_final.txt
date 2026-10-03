warning: in the working copy of 'README.md', LF will be replaced by CRLF the next time Git touches it
diff --git a/README.md b/README.md
index 59395db..18b476b 100644
--- a/README.md
+++ b/README.md
@@ -4,6 +4,44 @@
 [![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
 [![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
 
+**STATUS: PROJETO CONGELADO — TESE DE MERCADO NÃO VALIDADA**
+
+> Este projeto está preservado como referência arquitetural e código-fonte.
+> Nenhum desenvolvimento ativo está ocorrendo.
+> Reativação somente mediante evidência externa de demanda.
+
+---
+
+## 📌 Estado Atual do Projeto
+
+**Data do congelamento:** Agosto de 2026
+
+**Decisão estratégica:** MATAR como produto / PRESERVAR como código
+
+**Evidência da decisão:**
+- Uso real identificado: N=1 usuário (criador)
+- Nenhum usuário externo identificado em nenhum artefato do repositório
+- Caso de uso mais substancial (análise de documentos jurídicos) já é resolvido adequadamente por ferramentas prontas
+- Não há evidência de que outras pessoas valorizem uma solução própria para o problema
+
+**Condição para reativação:**
+- ≥ 5 usuários externos
+- Uso repetido para uma tarefa específica
+- Declaração explícita de que a alternativa atual é insuficiente
+- Nex resolve uma deficiência concreta identificada
+
+**Status do repositório:**
+- ✅ Código preservado
+- ✅ Auditoria completa realizada
+- ✅ 469 arquivos versionados
+- ✅ 98/98 testes passando
+- ✅ Runtime validado (memory_count: 71)
+- ✅ Backlog documentado (FB-001: cobertura do fallback)
+
+---
+
+## 📋 Funcionalidades Implementadas (estado na época do congelamento)
+
 Assistente de IA local com memória persistente (embeddings via Ollama + FAISS HNSW), busca na web (DuckDuckGo), fallchain multi-backend (Ollama → OpenRouter → Llama.cpp → HuggingFace) e **orquestração multi-agente** com DAG de agentes especializados (Researcher → Analyst → Writer). Também inclui 90+ **agentes Claude Code** para revisão de código, build resolution, análise de segurança, etc.
 
 ## Funcionalidades
@@ -468,6 +506,20 @@ data: {"stage": "analysis", "status": "running", "detail": "Analisando dados obt
 data: {"stage": "complete", "status": "done", "detail": "", "result": {...}}
 ```
 
+## 📊 Auditoria Realizada
+
+O projeto passou por uma auditoria completa em agosto de 2026:
+
+| Fase | Escopo | Resultado |
+|------|--------|-----------|
+| 0-6 | Auditoria de estado | Baseline estabelecido |
+| 7 | Correção controlada | Segurança, persistência, testes |
+| 8-9 | Repository Boundary | 469 arquivos versionados |
+| 10 | Diagnóstico das 26 falhas | 98/98 testes passando |
+| 11 | Validação estratégica | Decisão: MATAR como produto |
+
+**Evidência completa disponível em:** `fase_11_validacao_estrategica/DECISAO.md`
+
 ## Licença
 
 MIT
@@ -488,3 +540,9 @@ MIT
 ---
 
 **Desenvolvido para rodar localmente com fallback inteligente para cloud, combinando o melhor dos dois mundos**
+
+---
+
+## ⚠️ Nota Final
+
+Este projeto está preservado como demonstração de engenharia e arquitetura de sistemas de IA locais. Não há suporte ativo, desenvolvimento ou roadmap. Pull requests não serão revisados ou mesclados a menos que a condição de reativação seja atendida.
