#!/bin/bash
# Exemplos de uso da API com cURL

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "Nex Chat - Exemplos cURL"
echo "=========================================="

# 1. Enviar mensagem
echo ""
echo "1. Enviando mensagem..."
RESPONSE=$(curl -s -X POST ${BASE_URL}/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Ola, meu nome e Joao"}')

SESSION_ID=$(echo $RESPONSE | jq -r '.session_id')
echo "Session ID: ${SESSION_ID}"
echo "Resposta: $(echo $RESPONSE | jq -r '.response')"
echo ""

# 2. Continuar conversa
echo "2. Continuando conversa..."
curl -s -X POST ${BASE_URL}/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Qual e meu nome?\", \"session_id\": \"${SESSION_ID}\"}" \
  | jq '.response'

# 3. Streaming
echo ""
echo "3. Streaming (resposta em tempo real)..."
curl -s -X POST ${BASE_URL}/api/chat/stream \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Conte uma piada\", \"session_id\": \"${SESSION_ID}\"}" \
  | while read line; do
      if [[ $line == data:* ]]; then
        TOKEN=$(echo $line | cut -d' ' -f2- | jq -r '.token // empty')
        if [[ -n "$TOKEN" ]]; then
          echo -n "$TOKEN"
        fi
      fi
    done
echo ""

# 4. Estatisticas
echo ""
echo "4. Estatisticas do sistema..."
curl -s ${BASE_URL}/api/stats | jq '{
  uptime: .uptime_seconds,
  sessions: .sessions_count,
  requests: .llm_stats.requests,
  cache_hits: .llm_stats.cache_hits
}'

# 5. Listar sessoes
echo ""
echo "5. Sessoes ativas..."
curl -s ${BASE_URL}/api/sessions | jq '.sessions[] | {id: .session_id, messages: .message_count}'

echo ""
echo "=========================================="
echo "Exemplos concluidos"
echo "=========================================="
