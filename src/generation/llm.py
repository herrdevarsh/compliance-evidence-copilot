import requests
from src.config import settings

_session = requests.Session()

def call_ollama(system: str, user: str) -> str:
    url = f"{settings.ollama_url.rstrip('/')}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 220,   # HARD CAP response length (big speedup)
            "top_p": 1.0,
        },
    }

    # (connect timeout, read timeout)
    r = _session.post(url, json=payload, timeout=(10, 180))
    r.raise_for_status()
    data = r.json()
    return data["message"]["content"]

def generate_text(system: str, user: str) -> str:
    return call_ollama(system, user)
