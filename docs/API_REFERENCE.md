# API Reference - Nex Chat

## Base URL
```
http://localhost:8000
```

## Autenticação
A API não requer autenticação (ambiente local). Para produção, recomenda-se adicionar um proxy reverso com autenticação.

---

## Endpoints

### 1. POST /ask
Envia uma mensagem e aguarda a resposta completa. Suporta memória e busca na web.

**Request Body:**
```json
{
  "text": "string (obrigatório)",
  "use_web_search": false,
  "max_tokens": 2048,
  "temperature": 0.7,
  "stream": false,
  "use_memory": true
}
```

**Response:**
```json
{
  "response": "string",
  "context_used": 3,
  "backend": "openrouter|huggingface"
}
```

**Exemplo cURL:**
```bash
# Chat simples
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"text": "Olá! Como você funciona?"}'

# Com busca na web
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"text": "Últimas notícias sobre IA", "use_web_search": true}'
```

---

### 2. POST /remember
Salva memória explicitamente no sistema.

**Request Body:**
```json
{
  "text": "string (obrigatório)",
  "importancia": 1.0
}
```

**Response:**
```json
{
  "status": "saved",
  "id": 42,
  "text": "Primeiros 100 caracteres..."
}
```

---

### 3. GET /health
Health check do sistema.

**Response:**
```json
{
  "status": "healthy",
  "model": "openrouter/owl-alpha",
  "device": "cloud",
  "memory_count": 89
}
```

---

### 4. GET /metrics
Métricas em tempo real do sistema.

**Response:**
```json
{
  "requests_total": 1234,
  "active_connections": 5,
  "avg_latency_ms": 245.6,
  "peak_memory_mb": 512.3,
  "cache_hit_rate": 0.78,
  "memories_stored": 89
}
```

---

### 5. GET /
Endpoint raiz com informações básicas.

**Response:**
```json
{
  "message": "Nex Local AI Assistant API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

### 6. WebSocket /ws/chat
Chat em tempo real via WebSocket.

**Conexão:**
```
ws://localhost:8000/ws/chat
```

**Mensagem de entrada:**
```json
{"text": "Olá!", "use_web_search": false}
```

**Mensagens de saída:**
```json
{"type": "chunk", "content": "Olá"}
{"type": "end", "full_response": "Olá! Como posso ajudar?"}
```

---

## Códigos de Erro

| Código | Descrição |
|--------|-----------|
| 200 | Sucesso |
| 400 | Requisição inválida |
| 429 | Rate limit excedido (100 req/min) |
| 500 | Erro interno do servidor |

---

## Rate Limiting
Limit: 100 requisições por minuto por IP.

---

## Exemplos

### Python Client
```python
import requests

class NexChatClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def ask(self, text, use_web_search=False):
        response = requests.post(
            f"{self.base_url}/ask",
            json={
                "text": text,
                "use_web_search": use_web_search
            }
        )
        return response.json()

    def remember(self, text, importancia=1.0):
        response = requests.post(
            f"{self.base_url}/remember",
            json={"text": text, "importancia": importancia}
        )
        return response.json()

    def health(self):
        return requests.get(f"{self.base_url}/health").json()

# Uso
client = NexChatClient()
print(client.ask("Olá!"))
print(client.health())
```

---

## Versionamento
API Version: **v1.0.0**

---

## Suporte
Para dúvidas ou problemas, consulte a documentação ou abra uma issue no GitHub.