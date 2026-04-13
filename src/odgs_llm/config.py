"""
Bridge configuration — centralises all model defaults and provider settings.

Resolution order (highest priority first):
  1. Explicit constructor args  (OdgsLlmBridge(model="..."))
  2. Environment variables       (ODGS_LLM_MODEL, ODGS_LLM_PROVIDER, etc.)
  3. Config file                 (.odgs-llm.toml or ~/.config/odgs-llm/config.toml)
  4. Hardcoded fallbacks below   (only used as absolute last resort)

This ensures model names are never baked into provider code and can be
rotated by ops without code changes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

# ── Fallback defaults (last resort only) ──────────────────────────
# These exist so the package can boot without any config file.
# They should be overridden via config or env vars in production.

_FALLBACK_MODELS = {
    "ollama": "gemma4:26b",
    "google-genai": "gemini-3.1-flash-lite-preview",
    "openai-compat": "gpt-4o",
    "litellm": "ollama/gemma4:26b",
}

_CONFIG_FILENAMES = [
    ".odgs-llm.toml",
    "odgs-llm.toml",
]

_GLOBAL_CONFIG_PATHS = [
    Path.home() / ".config" / "odgs-llm" / "config.toml",
]


@dataclass
class ProviderConfig:
    """Configuration for a single LLM provider."""

    model: str = ""
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.1
    max_tokens: int = 4096


@dataclass
class BridgeConfig:
    """Central configuration for the ODGS LLM Bridge."""

    # Active provider name
    provider: str = ""

    # Per-provider settings
    ollama: ProviderConfig = field(default_factory=ProviderConfig)
    google_genai: ProviderConfig = field(default_factory=ProviderConfig)
    openai_compat: ProviderConfig = field(default_factory=ProviderConfig)
    litellm: ProviderConfig = field(default_factory=ProviderConfig)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "BridgeConfig":
        """
        Load config from file, then overlay environment variables.

        Args:
            config_path: Explicit path to a TOML config file.
                          If None, searches cwd and global paths.
        """
        config = cls()

        # 1. Try loading from file
        file_data = _find_and_load_config(config_path)
        if file_data:
            config = _apply_file_config(config, file_data)

        # 2. Overlay environment variables (always wins over file)
        config = _apply_env_vars(config)

        return config

    def default_model(self, provider_name: str) -> str:
        """
        Resolve the model for a provider.

        Priority: provider config → env var → fallback.
        """
        provider_cfg = self._provider_config(provider_name)
        if provider_cfg and provider_cfg.model:
            return provider_cfg.model
        return _FALLBACK_MODELS.get(provider_name, "")

    def _provider_config(self, provider_name: str) -> Optional[ProviderConfig]:
        mapping = {
            "ollama": self.ollama,
            "google-genai": self.google_genai,
            "openai-compat": self.openai_compat,
            "litellm": self.litellm,
        }
        return mapping.get(provider_name)


def _find_and_load_config(explicit_path: Optional[str] = None) -> Dict[str, Any]:
    """Find and parse a TOML config file."""
    paths_to_try = []

    if explicit_path:
        paths_to_try.append(Path(explicit_path))
    else:
        # Check cwd
        for name in _CONFIG_FILENAMES:
            paths_to_try.append(Path.cwd() / name)
        # Check global
        paths_to_try.extend(_GLOBAL_CONFIG_PATHS)

    for p in paths_to_try:
        if p.is_file():
            try:
                # Python 3.11+ has tomllib; fallback to toml string parsing
                try:
                    import tomllib
                except ImportError:
                    import tomli as tomllib  # type: ignore[no-redef]

                return tomllib.loads(p.read_text(encoding="utf-8"))
            except (ImportError, Exception):
                # If no TOML parser available, try simple key=value parsing
                return _parse_simple_config(p)

    return {}


def _parse_simple_config(path: Path) -> Dict[str, Any]:
    """Fallback: parse a simple key=value config if no TOML parser is available."""
    result: Dict[str, Any] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("["):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                result[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        pass
    return result


def _apply_file_config(config: BridgeConfig, data: Dict[str, Any]) -> BridgeConfig:
    """Apply parsed TOML data to the config."""
    if "provider" in data:
        config.provider = str(data["provider"])

    provider_sections = {
        "ollama": config.ollama,
        "google-genai": config.google_genai,
        "openai-compat": config.openai_compat,
        "litellm": config.litellm,
    }

    for name, cfg in provider_sections.items():
        section = data.get(name, {})
        if isinstance(section, dict):
            if "model" in section:
                cfg.model = str(section["model"])
            if "api_key" in section:
                cfg.api_key = str(section["api_key"])
            if "base_url" in section:
                cfg.base_url = str(section["base_url"])
            if "temperature" in section:
                cfg.temperature = float(section["temperature"])
            if "max_tokens" in section:
                cfg.max_tokens = int(section["max_tokens"])

    return config


def _apply_env_vars(config: BridgeConfig) -> BridgeConfig:
    """Overlay environment variables onto config (highest priority)."""
    if os.environ.get("ODGS_LLM_PROVIDER"):
        config.provider = os.environ["ODGS_LLM_PROVIDER"]

    if os.environ.get("ODGS_LLM_MODEL"):
        # Apply to the active provider
        provider_name = config.provider or "ollama"
        cfg = config._provider_config(provider_name)
        if cfg:
            cfg.model = os.environ["ODGS_LLM_MODEL"]

    # Provider-specific env vars
    env_map = {
        "ODGS_LLM_OLLAMA_MODEL": config.ollama,
        "ODGS_LLM_GOOGLE_MODEL": config.google_genai,
        "ODGS_LLM_OPENAI_MODEL": config.openai_compat,
        "ODGS_LLM_LITELLM_MODEL": config.litellm,
    }
    for env_key, cfg in env_map.items():
        if os.environ.get(env_key):
            cfg.model = os.environ[env_key]

    # API keys from env (standard practice)
    if os.environ.get("GOOGLE_API_KEY"):
        config.google_genai.api_key = os.environ["GOOGLE_API_KEY"]
    if os.environ.get("OPENAI_API_KEY"):
        config.openai_compat.api_key = os.environ["OPENAI_API_KEY"]

    return config
