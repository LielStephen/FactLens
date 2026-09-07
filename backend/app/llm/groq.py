import json
import time
import random
import httpx
from typing import List, Dict, Any, Optional
from app.config import settings
from app.llm.base import LLMProvider


class GroqProvider(LLMProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.primary_model = model or "openai/gpt-oss-20b"
        # High-quota, fast models on the current tier
        self.fallback_models = ["openai/gpt-oss-20b", "qwen/qwen3.6-27b", "openai/gpt-oss-120b"]
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "FactLens/1.0"
        }

    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False
    ) -> str:
        tokens = max_tokens or settings.GROQ_MAX_TOKENS
        temp = temperature if temperature is not None else settings.GROQ_TEMPERATURE

        # Deep copy messages to avoid mutating caller's data
        formatted_messages = [dict(m) for m in messages]

        if json_mode and formatted_messages:
            formatted_messages[-1]["content"] += "\nReturn strictly valid JSON only."

        models_to_try = [self.primary_model] + [m for m in self.fallback_models if m != self.primary_model]
        last_exception = None

        for model in models_to_try:
            payload: Dict[str, Any] = {
                "model": model,
                "messages": formatted_messages,
                "max_tokens": tokens,
                "temperature": temp,
            }

            for attempt in range(2):
                try:
                    with httpx.Client(timeout=25.0) as client:
                        response = client.post(
                            self.base_url,
                            headers=self.headers,
                            json=payload
                        )

                    if response.status_code == 200:
                        data = response.json()
                        return data["choices"][0]["message"]["content"]
                    elif response.status_code == 429:
                        # Rate limit or quota exhausted for this model: immediately fall through to next model!
                        last_exception = RuntimeError(f"Rate limit 429 on model {model}: {response.text[:120]}")
                        break
                    elif response.status_code == 400:
                        last_exception = RuntimeError(f"Bad Request 400 on model {model}: {response.text[:120]}")
                        break
                    else:
                        response.raise_for_status()

                except Exception as e:
                    last_exception = e
                    time.sleep(0.3)

        raise RuntimeError(f"Groq API call failed across models: {last_exception}")


_global_llm_provider: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    global _global_llm_provider
    if _global_llm_provider is None:
        _global_llm_provider = GroqProvider()
    return _global_llm_provider
