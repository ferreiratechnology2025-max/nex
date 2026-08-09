# Dockerfile para Nex Chat - IA Local com Memória
# Build: docker build -t nex-chat .
# Run: docker run -p 8000:8000 -v nex-data:/app/data nex-chat

FROM python:3.10-slim

# Define argumentos de build
ARG MODEL_NAME=gemma2:2b
ARG OLLAMA_HOST=http://host.docker.internal:11434

# Define variáveis de ambiente
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODEL_NAME=${MODEL_NAME} \
    OLLAMA_HOST=${OLLAMA_HOST} \
    DEBIAN_FRONTEND=noninteractive

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements primeiro (melhor cache)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Instala Ollama (opcional - para uso standalone)
RUN curl -fsSL https://ollama.com/install.sh | sh || true

# Copia o código fonte
COPY src/ ./src/
COPY templates/ ./templates/
COPY static/ ./static/

# Cria diretórios necessários
RUN mkdir -p /app/data /app/models

# Expõe a porta da aplicação
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/stats || exit 1

# Script de entrada
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]

# Comando padrão
CMD ["python", "-m", "src.main"]
