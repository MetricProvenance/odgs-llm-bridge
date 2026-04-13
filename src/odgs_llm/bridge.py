"""
OdgsLlmBridge — main orchestrator that wires providers to capabilities.

Usage:
    from odgs_llm import OdgsLlmBridge

    bridge = OdgsLlmBridge()                          # auto-detects provider
    bridge = OdgsLlmBridge(provider="ollama")          # explicit local
    bridge = OdgsLlmBridge(provider="google-genai")    # explicit cloud

    # Compile a regulation into ODGS rules
    rules = bridge.compile_regulation("EU AI Act Article 10...")

    # Narrate an S-Cert for stakeholders
    narrative = bridge.narrate_audit(scert_json)
"""

from __future__ import annotations

import json
import logging
from typing import Any

from odgs_llm.config import BridgeConfig
from odgs_llm.providers import ModelProvider, ModelResponse

logger = logging.getLogger(__name__)


def auto_detect_provider(
    model: str | None = None, config: BridgeConfig | None = None
) -> ModelProvider:
    """
    Auto-detect the best available provider.

    Model names are resolved from config (file/env), not hardcoded.

    Priority:
      1. Ollama running locally → OllamaProvider
      2. GOOGLE_API_KEY set → GoogleGenAIProvider
      3. OPENAI_API_KEY set → OpenAICompatProvider
      4. Raise RuntimeError
    """
    import os

    cfg = config or BridgeConfig.load()

    # 1. Try Ollama
    try:
        from odgs_llm.providers.gemma import OllamaProvider

        resolved_model = model or cfg.default_model("ollama")
        provider = OllamaProvider(model=resolved_model)
        if provider.health_check():
            logger.info("Auto-detected: Ollama (local), model=%s", resolved_model)
            return provider
    except ImportError:
        pass

    # 2. Try Google GenAI
    if os.environ.get("GOOGLE_API_KEY") or cfg.google_genai.api_key:
        try:
            from odgs_llm.providers.gemma import GoogleGenAIProvider

            resolved_model = model or cfg.default_model("google-genai")
            api_key = cfg.google_genai.api_key or None  # let provider read env
            provider = GoogleGenAIProvider(model=resolved_model, api_key=api_key)
            logger.info("Auto-detected: Google GenAI (cloud), model=%s", resolved_model)
            return provider
        except ImportError:
            pass

    # 3. Try OpenAI-compatible
    if os.environ.get("OPENAI_API_KEY") or cfg.openai_compat.api_key:
        try:
            from odgs_llm.providers.openai_compat import OpenAICompatProvider

            resolved_model = model or cfg.default_model("openai-compat")
            provider = OpenAICompatProvider(
                model=resolved_model,
                api_key=cfg.openai_compat.api_key or None,
                base_url=cfg.openai_compat.base_url or None,
            )
            logger.info("Auto-detected: OpenAI-compatible (cloud), model=%s", resolved_model)
            return provider
        except ImportError:
            pass

    raise RuntimeError(
        "No LLM provider available. Install one of:\n"
        "  pip install odgs-llm-bridge[ollama]   # local (recommended)\n"
        "  pip install odgs-llm-bridge[google]   # Google GenAI\n"
        "  pip install odgs-llm-bridge[openai]   # OpenAI-compatible\n"
        "  pip install odgs-llm-bridge[litellm]  # LiteLLM universal\n"
        "And ensure the provider is running / API key is set."
    )


def _load_provider(
    provider_name: str, model: str | None = None, config: BridgeConfig | None = None
) -> ModelProvider:
    """Resolve a provider by short name. Model resolved from config if not explicit."""
    cfg = config or BridgeConfig.load()

    if provider_name == "ollama":
        from odgs_llm.providers.gemma import OllamaProvider

        return OllamaProvider(model=model or cfg.default_model("ollama"))
    elif provider_name == "google-genai":
        from odgs_llm.providers.gemma import GoogleGenAIProvider

        return GoogleGenAIProvider(
            model=model or cfg.default_model("google-genai"),
            api_key=cfg.google_genai.api_key or None,
        )
    elif provider_name == "openai-compat":
        from odgs_llm.providers.openai_compat import OpenAICompatProvider

        return OpenAICompatProvider(
            model=model or cfg.default_model("openai-compat"),
            api_key=cfg.openai_compat.api_key or None,
            base_url=cfg.openai_compat.base_url or None,
        )
    elif provider_name == "litellm":
        from odgs_llm.providers.litellm_router import LiteLLMProvider

        return LiteLLMProvider(model=model or cfg.default_model("litellm"))
    else:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            "Supported: ollama, google-genai, openai-compat, litellm"
        )


class OdgsLlmBridge:
    """
    Main entry point for all LLM-powered ODGS capabilities.

    The bridge is headless — it reads ODGS artifacts, sends structured
    prompts to an LLM, validates the output against ODGS JSON schemas,
    and returns deterministic-ready governance artifacts.
    """

    def __init__(
        self,
        provider: str | ModelProvider | None = None,
        model: str | None = None,
        config: BridgeConfig | None = None,
    ):
        self._config = config or BridgeConfig.load()
        if provider is None:
            self._provider = auto_detect_provider(model, config=self._config)
        elif isinstance(provider, str):
            self._provider = _load_provider(provider, model, config=self._config)
        else:
            self._provider = provider

    @property
    def provider(self) -> ModelProvider:
        return self._provider

    def _call(
        self,
        system_prompt: str,
        user_message: str,
        *,
        response_format: str | None = "json",
        temperature: float = 0.1,
    ) -> ModelResponse:
        """Internal: call the provider with standard defaults."""
        return self._provider.generate(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=temperature,
            response_format=response_format,
        )

    # ── Capability 1: Regulatory Compiler ──────────────────────────

    def compile_regulation(
        self, regulation_text: str, *, context: dict[str, Any] | None = None
    ) -> list[dict]:
        """
        Convert regulation text (statute, article, SLA clause)
        into one or more ODGS rule JSON objects.
        """
        from odgs_llm.capabilities.regulatory_compiler import compile_regulation

        return compile_regulation(self, regulation_text, context=context)

    # ── Capability 2: Drift Watchdog ───────────────────────────────

    def check_drift(
        self, definitions_dir: str, *, threshold_days: int = 90
    ) -> list[dict]:
        """
        Scan legislative definitions for staleness.
        Returns a list of drift warnings with recommendations.
        """
        from odgs_llm.capabilities.drift_watchdog import check_drift

        return check_drift(self, definitions_dir, threshold_days=threshold_days)

    # ── Capability 3: Conflict Detector ────────────────────────────

    def detect_conflicts(self, rules: list[dict]) -> list[dict]:
        """
        Analyze a set of rules for semantic conflicts, overlaps,
        or contradictions across different regulatory sources.
        """
        from odgs_llm.capabilities.conflict_detector import detect_conflicts

        return detect_conflicts(self, rules)

    # ── Capability 4: Audit Narrator ───────────────────────────────

    def narrate_audit(
        self, scert: dict, *, audience: str = "executive"
    ) -> str:
        """
        Convert an S-Cert (Semantic Certificate) JSON into a
        human-readable narrative suitable for the target audience.
        """
        from odgs_llm.capabilities.audit_narrator import narrate_audit

        return narrate_audit(self, scert, audience=audience)

    # ── Capability 5: Binding Discoverer ───────────────────────────

    def discover_bindings(
        self,
        catalog_metadata: dict,
        *,
        metrics: list[dict] | None = None,
    ) -> dict:
        """
        Given data catalog metadata (column names, types, descriptions),
        generate a physical_data_map.json binding to ODGS metrics.
        """
        from odgs_llm.capabilities.binding_discoverer import discover_bindings

        return discover_bindings(self, catalog_metadata, metrics=metrics)
