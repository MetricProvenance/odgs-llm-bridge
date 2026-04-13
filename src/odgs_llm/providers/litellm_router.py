"""
LiteLLM multi-model router — unified interface to 100+ providers.

LiteLLM handles routing, retries, and cost-tracking across
OpenAI, Anthropic, Google, Ollama, Azure, Bedrock, etc.
"""

from __future__ import annotations

from odgs_llm.providers import ModelProvider, ModelResponse


class LiteLLMProvider(ModelProvider):
    """LiteLLM unified provider — supports all LiteLLM model strings."""

    name = "litellm"

    def __init__(self, model: str = "ollama/gemma4:26b"):
        self.model = model
        self._litellm = None

    def _get_litellm(self):
        if self._litellm is None:
            try:
                import litellm

                self._litellm = litellm
            except ImportError:
                raise ImportError(
                    "litellm package not installed. Run: pip install odgs-llm-bridge[litellm]"
                )
        return self._litellm

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        response_format: str | None = None,
    ) -> ModelResponse:
        litellm = self._get_litellm()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        resp = litellm.completion(**kwargs)
        choice = resp.choices[0]
        usage = {}
        if resp.usage:
            usage = {
                "prompt_tokens": resp.usage.prompt_tokens or 0,
                "completion_tokens": resp.usage.completion_tokens or 0,
            }
        return ModelResponse(
            text=choice.message.content or "",
            model=self.model,
            provider=self.name,
            usage=usage,
            raw=resp,
        )
