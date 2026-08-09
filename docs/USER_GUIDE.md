# Guia do Usuário - Nex Chat

## Índice
1. [Instalação](#instalação)
2. [Primeiros Passos](#primeiros-passos)
3. [Usando a Interface](#usando-a-interface)
4. [Busca na Web](#busca-na-web)
5. [Memória do Sistema](#memória-do-sistema)
6. [Dicas e Truques](#dicas-e-truques)
7. [FAQ](#faq)

---

## Instalacao

### Requisitos Minimos
- **CPU**: 4 cores (qualquer arquitetura)
- **RAM**: 8GB (recomendado) / 4GB (minimo)
- **Disco**: 10GB livres
- **Sistema**: Windows 10+, Linux (Ubuntu 20.04+), macOS 11+

### Passo a Passo

#### Windows
```powershell
# 1. Clone ou navegue até o projeto
cd D:\Nex

# 2. Crie ambiente virtual
python -m venv venv

# 3. Ative o ambiente virtual
venv\Scripts\activate

# 4. Instale dependências
pip install -r requirements.txt

# 5. Configure API key (opcional)
copy .env.example .env
# Edite .env com sua OPENROUTER_API_KEY (opcional, modelos free funcionam sem)

# 6. Execute o Nex Chat
python -m src.main
```

#### Linux/Mac
```bash
# 1. Clone ou navegue até o projeto
cd ~/nex-chat

# 2. Crie ambiente virtual
python -m venv venv

# 3. Ative o ambiente virtual
source venv/bin/activate

# 4. Instale dependências
pip install -r requirements.txt

# 5. Configure API key (opcional)
cp .env.example .env
# Edite .env com sua OPENROUTER_API_KEY (opcional, modelos free funcionam sem)

# 6. Execute o Nex Chat
python -m src.main
```

---

## Primeiros Passos

### 1. Inicie o Servidor
```bash
python -m src.main
```

Voce vera:
```
==================================================
            Nex Chat - IA Local
  Interface Web: http://localhost:8000
  API Docs:      http://localhost:8000/docs
==================================================
```

### 2. Acesse a Interface
Abra seu navegador em: **http://localhost:8000**

### 3. Comece a Conversar
Digite sua mensagem no campo inferior e pressione **Enter**.

---

## Usando a Interface

### Layout

```
+-----------------------------------------------------+
| Sidebar            |       Chat Principal            |
| ------------------ | ------------------------------- |
| Nex Chat           | Conversa                        |
| IA Local           |                                 |
| ------------------ | Bot: Ola! Como posso ajudar?    |
| Sessoes            |                                 |
| [+ Nova Conversa]  | Voce: Meu nome e Joao           |
|                    |                                 |
| * Sessao abc123    | Bot: Prazer, Joao!              |
| * Sessao def456    |                                 |
|                    | [Digite sua mensagem...     >]  |
+-----------------------------------------------------+
```

### Componentes

| Elemento | Funcao |
| :--- | :--- |
| **Sidebar** | Lista de sessoes e estatisticas |
| **+ Nova Conversa** | Inicia uma nova sessao |
| **Area de Mensagens** | Exibe o historico da conversa |
| **Campo de Texto** | Digite suas mensagens |
| **Botao Enviar** | Envia a mensagem |

### Atalhos de Teclado
- `Enter` - Envia mensagem
- `Shift + Enter` - Nova linha no campo de texto

---

## Busca na Web

### Ativando a Busca na Web
Adicione `"use_web_search": true` na sua requisição:

```bash
# Via cURL
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"text": "Últimas notícias sobre IA", "use_web_search": true}'
```

### O que acontece:
1. O sistema busca informações atualizadas na internet
2. Os resultados são salvos na memória (busca semântica)
3. Você recebe a resposta com base nas informações mais recentes

### Exemplos:
- "Qual a capital da Argentina?"
- "Últimas notícias de tecnologia"
- "Quem ganhou o jogo ontem?"

---

## Gerenciando Sessões

### Criar Nova Sessao
Clique em **"+ Nova Conversa"** no sidebar.

### Alternar Entre Sessoes
Clique em qualquer sessao listada no sidebar.

### Deletar Sessao
1. Passe o mouse sobre a sessao no sidebar
2. Clique no X para excluir
3. Ou use a API: `DELETE /api/sessions/{session_id}`

---

## Memoria do Sistema

### Como a Memoria Funciona

#### Curto Prazo
- Mantem as ultimas **20 mensagens** da conversa atual
- Limite de **2048 tokens** (~1500 palavras)
- Mensagens antigas sao automaticamente removidas

#### Longo Prazo
- Informacoes importantes sao salvas automaticamente
- O sistema detecta frases como:
  - "Meu nome e..."
  - "Eu trabalho com..."
  - "Gosto de..."
  - "Lembre-se que..."
- Busca semantica recupera informacoes relevantes

### Exemplo de Memoria

```
# O sistema lembra informacoes importantes
Usuario: "Meu nome e Joao e sou programador Python"
Assistente: "Prazer, Joao!"

# Em outra conversa, dias depois...
Usuario: "Qual e minha profissao?"
Assistente: "Voce e programador Python!"  # Lembrou!
```

---

## Fallback Local (HuggingFace)

Quando o OpenRouter estiver indisponivel (timeout, rate limit, erro de rede), o sistema usa automaticamente um modelo local via HuggingFace.

### Baixar o modelo TinyLlama

```bash
# Execute o script de download
scripts\windows\download_tinyllama.bat
```

### Configurar no `.env`

```bash
# Modelo local GGUF
LOCAL_MODEL_PATH=models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
LOCAL_MODEL_THREADS=4
LOCAL_MODEL_TIMEOUT=120
```

### Modelos GGUF Recomendados

| Modelo | Tamanho | RAM Mínima | Qualidade |
|--------|---------|-----------|-----------|
| `tinyllama-1.1b-chat-v1.0.Q3_K_S.gguf` | ~500MB | 1GB | ⭐⭐⭐ |
| `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf` | ~700MB | 1.5GB | ⭐⭐⭐⭐ |
| `tinyllama-1.1b-chat-v1.0.Q5_K_M.gguf` | ~900MB | 2GB | ⭐⭐⭐⭐⭐ |

### Troubleshooting

| Erro | Causa Provável | Solução |
|------|---------------|---------|
| `Model file not found` | Arquivo GGUF ausente | Execute `download_tinyllama.bat` |
| `GGUF magic mismatch` | Arquivo corrompido | Baixe novamente |
| `Timeout na inferência` | CPU lenta ou prompt longo | Aumente `LOCAL_MODEL_TIMEOUT` ou reduza o prompt |
| `MemoryError` | RAM insuficiente | Use Q3_K_S ou feche outros apps |

### Monitorando Fallbacks

```bash
# Ver qual backend está sendo usado
curl -s -i -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"text":"teste"}' | grep X-Backend

# Ver contador de fallbacks
curl -s http://localhost:8000/metrics | grep llm_fallback
```

---

## Dicas e Truques

### 1. Use Frases Explicitas para Memoria
```
BOM:  "Meu nome e Joao"
BOM:  "Eu trabalho com analise de dados"
BOM:  "Lembre-se que prefiro respostas curtas"

RUIM: "Joao" (muito vago)
```

### 2. Contexto Importante
Quanto mais contexto voce der, melhor:
```
BOM: "Sou desenvolvedor backend com 5 anos de experiencia em Python"
BOM: "Estou aprendendo machine learning, especialmente redes neurais"
```

### 3. Use Perguntas Diretas
```
BOM:  "O que voce lembra sobre meu trabalho?"
BOM:  "Qual foi o ultimo assunto que discutimos?"

RUIM: "Lembra?" (muito vago)
```

### 4. Resetar Contexto
Se a conversa ficar confusa, inicie uma nova sessao.

---

## FAQ

### Q: Quanto tempo leva para responder?
**A:** 2-5 segundos na primeira vez, 50-100ms em cache.

### Q: Posso usar outros modelos?
**A:** Sim! Mude a variavel `MODEL_NAME` ou use:
```bash
ollama pull llama3.2:1b
# Depois inicie o Nex Chat
```

### Q: Onde ficam salvos os dados?
**A:** Em `./data/sessions/`. As conversas sao persistentes.

### Q: Como limpar todas as memorias?
**A:** Delete a pasta `./data/sessions/` e reinicie.

### Q: O sistema funciona offline?
**A:** Sim! 100% local, sem necessidade de internet.

### Q: Posso acessar de outros dispositivos?
**A:** Sim! Na mesma rede, use o IP do computador: `http://192.168.x.x:8000`

### Q: Como parar o servidor?
**A:** Pressione `Ctrl+C` no terminal.

### Q: Da para integrar com outros sistemas?
**A:** Sim! Use a API REST em `http://localhost:8000/docs`

### Q: O que fazer se travar?
**A:** Reinicie o servidor. As conversas sao salvas automaticamente.

---

## Suporte

- Issues: GitHub Issues
- Documentacao: docs/API_REFERENCE.md
- Guia Dev: docs/DEVELOPER_GUIDE.md

---

**Aproveite o Nex Chat!**
