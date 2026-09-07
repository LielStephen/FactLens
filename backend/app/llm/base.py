import abc
from typing import List, Dict, Any, Optional


class LLMProvider(abc.ABC):
    @abc.abstractmethod
    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False
    ) -> str:
        """Generates a text completion given message conversation history."""
        pass
