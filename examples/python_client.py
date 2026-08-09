#!/usr/bin/env python3
"""
Cliente Python para Nex Chat API
Exemplo completo de integracao
"""

import requests
import json
import time
from typing import Optional, Generator


class NexChatClient:
    """Cliente para Nex Chat API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id: Optional[str] = None

    def chat(self, message: str) -> str:
        """Envia mensagem e retorna resposta"""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "message": message,
                "session_id": self.session_id
            }
        )

        if response.status_code == 200:
            data = response.json()
            self.session_id = data["session_id"]
            return data["response"]
        else:
            raise Exception(f"Erro: {response.status_code}")

    def chat_stream(self, message: str) -> Generator[str, None, None]:
        """Envia mensagem e retorna resposta em streaming"""
        response = requests.post(
            f"{self.base_url}/api/chat/stream",
            json={
                "message": message,
                "session_id": self.session_id
            },
            stream=True
        )

        for line in response.iter_lines():
            if line:
                text = line.decode('utf-8')
                if text.startswith('data: '):
                    data = json.loads(text[6:])
                    if data.get("done"):
                        if "session_id" in data:
                            self.session_id = data["session_id"]
                        break
                    else:
                        yield data.get("token", "")

    def get_stats(self) -> dict:
        """Retorna estatisticas do sistema"""
        response = requests.get(f"{self.base_url}/api/stats")
        return response.json()

    def list_sessions(self) -> list:
        """Lista todas as sessoes"""
        response = requests.get(f"{self.base_url}/api/sessions")
        return response.json()["sessions"]

    def delete_session(self, session_id: str) -> bool:
        """Deleta uma sessao"""
        response = requests.delete(f"{self.base_url}/api/sessions/{session_id}")
        return response.json()["success"]

    def clear_cache(self) -> bool:
        """Limpa o cache"""
        response = requests.post(f"{self.base_url}/api/clear-cache")
        return response.json()["success"]


def main():
    """Exemplo de uso do cliente"""
    print("=" * 50)
    print("Nex Chat - Cliente Python")
    print("=" * 50)

    client = NexChatClient()

    # Verifica status
    try:
        stats = client.get_stats()
        print(f"\n[OK] Conectado ao servidor")
        print(f"     Uptime: {stats['uptime_seconds']:.0f}s")
        print(f"     Sessoes ativas: {stats['sessions_count']}")
    except Exception:
        print("\n[ERRO] Nao foi possivel conectar ao servidor")
        print("       Certifique-se que o Nex Chat esta rodando:")
        print("       python -m src.main")
        return

    # Conversa simples
    print("\n--- Exemplo 1: Chat simples ---")
    response = client.chat("Ola! Meu nome e Joao.")
    print(f"Assistente: {response}")

    # Com memoria
    print("\n--- Exemplo 2: Testando memoria ---")
    response = client.chat("Qual e meu nome?")
    print(f"Assistente: {response}")

    # Streaming
    print("\n--- Exemplo 3: Streaming ---")
    print("Assistente: ", end="", flush=True)
    for token in client.chat_stream("Conte uma historia curta de 3 frases."):
        print(token, end="", flush=True)
        time.sleep(0.02)
    print()

    # Estatisticas finais
    stats = client.get_stats()
    llm = stats.get('llm_stats', {})
    print(f"\n--- Estatisticas ---")
    print(f"Requests: {llm.get('requests', 0)}, Cache hits: {llm.get('cache_hits', 0)}")


if __name__ == "__main__":
    main()
