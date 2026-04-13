"""
Abstract base class for all LLM providers.

Every provider must implement `generate()` which accepts a system prompt
and user message, returning the model's text response.  The bridge is
model-agnostic — swap providers without changing capability code.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelResponse:
    """Standardised wrapper around any LLM provider response."""

    text: str
    model: str
    provider: str
    usage: dict[str, int] = field(default_factory=dict)
    raw: Any = None


class ModelProvider(abc.ABC):
    """Contract every LLM provider must satisfy."""

    name: str = "base"

    @abc.abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        response_format: str | None = None,
    ) -> ModelResponse:
        """Send a prompt pair to the model and return a structured response."""
        ...

    def health_check(self) -> bool:
        """Return True if the provider is reachable / configured."""
        try:
            resp = self.generate(
                system_prompt="Reply with the single word OK.",
                user_message="health",
                max_tokens=8,
            )
            return bool(resp.text)
        except Exception:
            return False
