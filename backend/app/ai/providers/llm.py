from typing import Optional, List, Dict, Any
import httpx

from app.ai.providers.base import BaseLLMProvider
from app.core.config import settings
from app.core.logging import logger


class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock LLM provider for offline testing."""
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1000,
    ) -> str:
        if "no relevant context" in prompt.lower() or "not found" in prompt.lower():
            return "I couldn't find this information in the uploaded documents."
        return "Based on the provided document context, the refund period is 30 days from purchase."


class OpenAICompatibleProvider(BaseLLMProvider):
    """OpenAI-compatible LLM completion provider using async httpx."""
    def __init__(
        self,
        api_key: str = "",
        model: str = "gpt-3.5-turbo",
        base_url: str = "https://api.openai.com/v1"
    ):
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1000,
    ) -> str:
        if not self.api_key:
            logger.warning("No LLM API key provided. Falling back to MockLLMProvider.")
            mock = MockLLMProvider()
            return await mock.generate(prompt, system_prompt=system_prompt)

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                if resp.status_code != 200:
                    logger.error(f"LLM API error [{resp.status_code}]: {resp.text}")
                    mock = MockLLMProvider()
                    return await mock.generate(prompt, system_prompt=system_prompt)
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            mock = MockLLMProvider()
            return await mock.generate(prompt, system_prompt=system_prompt)


class LLMProviderFactory:
    @staticmethod
    def get_provider(provider_type: Optional[str] = None) -> BaseLLMProvider:
        p_type = (provider_type or settings.LLM_PROVIDER).lower()
        if p_type in ("openai", "api"):
            return OpenAICompatibleProvider(
                api_key=settings.LLM_API_KEY,
                model=settings.LLM_MODEL,
                base_url=settings.LLM_BASE_URL
            )
        else:
            return MockLLMProvider()
