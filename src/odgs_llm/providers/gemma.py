"""
Ollama / Google GenAI provider — local-first with cloud fallback.

Priority:
  1. If Ollama is running locally → use it (zero egress, full sovereignty).
  2. Else if GOOGLE_API_KEY is set → use google-genai cloud.
  3. Else → raise ConfigurationError.
"""

from __future__ import annotations

import os

from odgs_llm.providers import ModelProvider, ModelResponse


class OllamaProvider(ModelProvider):
    """Local Ollama backend (Gemma, Llama, Mistral, etc.)."""

    name = "ollama"

    def __init__(self, model: str = "gemma4:26b", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import ollama  # noqa: F811

                self._client = ollama.Client(host=self.base_url)
            except ImportError:
                raise ImportError(
                    "ollama package not installed. Run: pip install odgs-llm-bridge[ollama]"
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
        opts = {"temperature": temperature, "num_predict": max_tokens}
        if response_format == "json":
            opts["format"] = "json"

        resp = client.chat(model=self.model, messages=messages, options=opts)
        return ModelResponse(
            text=resp["message"]["content"],
            model=self.model,
            provider=self.name,
            usage={
                "prompt_tokens": resp.get("prompt_eval_count", 0),
                "completion_tokens": resp.get("eval_count", 0),
            },
            raw=resp,
        )

    def health_check(self) -> bool:
        try:
            client = self._get_client()
            client.list()
            return True
        except Exception:
            return False


class GoogleGenAIProvider(ModelProvider):
    """Google GenAI cloud backend (Gemini)."""

    name = "google-genai"

    def __init__(self, model: str = "gemini-3.1-pro", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self.api_key:
                raise ValueError("GOOGLE_API_KEY not set for GoogleGenAIProvider.")
            try:
                from google import genai

                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "google-genai package not installed. Run: pip install odgs-llm-bridge[google]"
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
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if response_format == "json":
            config.response_mime_type = "application/json"

        resp = client.models.generate_content(
            model=self.model,
            contents=user_message,
            config=config,
        )
        usage = {}
        if resp.usage_metadata:
            usage = {
                "prompt_tokens": resp.usage_metadata.prompt_token_count or 0,
                "completion_tokens": resp.usage_metadata.candidates_token_count or 0,
            }
        return ModelResponse(
            text=resp.text or "",
            model=self.model,
            provider=self.name,
            usage=usage,
            raw=resp,
        )
