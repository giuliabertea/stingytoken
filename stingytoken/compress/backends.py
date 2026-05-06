from __future__ import annotations

import os
from abc import ABC, abstractmethod

import requests


class Backend(ABC):
    @abstractmethod
    def complete(self, system: str, user: str) -> str: ...


class OllamaBackend(Backend):
    def __init__(self, model: str = "mistral", base_url: str = "http://localhost:11434") -> None:
        self.model = model
        self.base_url = base_url

    def complete(self, system: str, user: str) -> str:
        payload = {
            "model": self.model,
            "prompt": f"System: {system}\n\nUser: {user}",
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 120},
        }
        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            return response.json()["response"].strip()
        except requests.exceptions.ConnectionError:
            raise RuntimeError("Ollama is not running. Start it with: ollama serve")
        except requests.exceptions.RequestException as exc:
            resp = getattr(exc, "response", None)
            if resp is not None:
                raise RuntimeError(f"{resp.status_code} {resp.text}")
            raise RuntimeError(str(exc))


class OpenAIBackend(Backend):
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    def complete(self, system: str, user: str) -> str:
        import openai

        client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=120,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()


def get_backend(config) -> Backend:
    name = config.compress.backend
    if name == "ollama":
        return OllamaBackend(model=config.compress.model)
    if name == "openai":
        key = os.environ.get("OPENAI_API_KEY", "")
        return OpenAIBackend(model=config.compress.model, api_key=key)
    raise ValueError(f"Unknown backend: {name!r}")
