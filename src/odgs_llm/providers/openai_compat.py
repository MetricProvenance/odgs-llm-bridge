"""
OpenAI-compatible provider — covers GPT-NL (TNO), Mistral, Anthropic,
and any endpoint exposing the OpenAI chat completions API.
"""

from __future__ import annotations

import os

from odgs_llm.providers import ModelProvider, ModelResponse


class OpenAICompatProvider(ModelProvider):
    """Any OpenAI-compatible chat completions endpoint."""

    name = "openai-compat"

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL")
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not set for OpenAICompatProvider.")
            try:
                import openai

                kwargs = {"api_key": self.api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                self._client = openai.OpenAI(**kwargs)
            except ImportError:
                raise ImportError(
                    "openai package not installed. Run: pip install odgs-llm-bridge[openai]"
                )
        return self._client

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        response_format: str | None = None,
    ) -> ModelResponse:
        client = self._get_client()
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

        resp = client.chat.completions.create(**kwargs)
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
