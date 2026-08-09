.PHONY: help build start stop logs clean shell test

# Cores para output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Mostra ajuda
	@echo "$(GREEN)Nex Chat - Comandos Disponíveis$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

build: ## Build da imagem Docker
	@echo "$(GREEN)🔨 Buildando imagem Docker...$(NC)"
	docker-compose build
	@echo "$(GREEN)✅ Build concluído!$(NC)"

start: ## Inicia os serviços
	@echo "$(GREEN)🚀 Iniciando Nex Chat...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ Serviços iniciados!$(NC)"
	@echo "$(GREEN)🌐 Interface: http://localhost:8000$(NC)"

stop: ## Para os serviços
	@echo "$(YELLOW)🛑 Parando Nex Chat...$(NC)"
	docker-compose down
	@echo "$(GREEN)✅ Serviços parados!$(NC)"

restart: stop start ## Reinicia os serviços

logs: ## Mostra logs
	docker-compose logs -f

status: ## Status dos serviços
	docker-compose ps

clean: ## Remove containers, volumes e dados
	@echo "$(RED)⚠️ Isso irá remover TODOS os dados!$(NC)"
	@read -p "Tem certeza? (y/N) " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		rm -rf data/*; \
		echo "$(GREEN)✅ Limpeza concluída!$(NC)"; \
	fi

shell: ## Abre shell no container
	docker-compose exec nex-chat /bin/bash

test: ## Executa testes (requer pytest)
	docker-compose exec nex-chat python -m pytest tests/ -v

pull-model: ## Baixa modelo Gemma 2 2B
	@echo "$(GREEN)📥 Baixando modelo Gemma 2 2B...$(NC)"
	docker run --rm -v ollama-models:/root/.ollama ollama/ollama pull gemma2:2b
	@echo "$(GREEN)✅ Modelo baixado!$(NC)"

monitor: ## Inicia monitoramento (requer profile monitoring)
	docker-compose --profile monitoring up -d
	@echo "$(GREEN)📊 Monitor: http://localhost:8080$(NC)"
