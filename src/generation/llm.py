import json
import requests
from src.config import settings

def call_ollama(system: str, user: str) -> str:
    url = f"{settings.ollama_url.rstrip('/')}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": 0.0},
    }
    r = requests.post(url, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["message"]["content"]

def generate_text(system: str, user: str) -> str:
    # If you want OpenAI, implement it here using an SDK or HTTP.
    # Keep evaluation identical regardless of provider.
    return call_ollama(system, user)
