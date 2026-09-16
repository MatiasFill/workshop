import httpx
from app.core.config import settings
from .base import LLMProvider

class OpenAIProvider(LLMProvider):
    name = "openai"
    async def generate(self, prompt: str) -> str:
        headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": "Você é um assistente de gestão de oficina. Responda com base no contexto fornecido e não invente dados."},
                {"role": "user", "content": prompt},
            ],
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

class AnthropicProvider(LLMProvider):
    name = "anthropic"
    async def generate(self, prompt: str) -> str:
        headers = {
            "x-api-key": settings.ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": settings.ANTHROPIC_MODEL,
            "max_tokens": 1200,
            "messages": [{"role": "user", "content": prompt}],
        }
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers)
            r.raise_for_status()
            return r.json()["content"][0]["text"]

class GeminiProvider(LLMProvider):
    name = "gemini"
    async def generate(self, prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(url, params={"key": settings.GEMINI_API_KEY}, json=payload)
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]

class OllamaProvider(LLMProvider):
    name = "ollama"
    async def generate(self, prompt: str) -> str:
        payload = {"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False}
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(f"{settings.OLLAMA_BASE_URL}/api/generate", json=payload)
            r.raise_for_status()
            return r.json()["response"]

def get_provider():
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "gemini": GeminiProvider,
        "ollama": OllamaProvider,
    }
    cls = providers.get(settings.LLM_PROVIDER)
    if not cls:
        raise ValueError(f"LLM_PROVIDER inválido: {settings.LLM_PROVIDER}")
    return cls()
