"""
Capability B.1: Regulatory Compiler

Converts regulation text (statute articles, SLA clauses, policy documents)
into ODGS-compliant rule JSON objects that can be loaded directly into
the Sovereign Validation Engine.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TYPE_CHECKING

from odgs_llm.schemas.output_validators import validate_rules

if TYPE_CHECKING:
    from odgs_llm.bridge import OdgsLlmBridge

_SYSTEM_PROMPT = (Path(__file__).parent.parent / "prompts" / "regulatory_compiler.md").read_text


def _load_prompt() -> str:
    path = Path(__file__).parent.parent / "prompts" / "regulatory_compiler.md"
    return path.read_text(encoding="utf-8")


def compile_regulation(
    bridge: OdgsLlmBridge,
    regulation_text: str,
    *,
    context: dict[str, Any] | None = None,
    workspace_yaml: dict | None = None,
) -> list[dict] | dict:
    """
    Parse regulation text into ODGS rule JSON objects.

    Args:
        bridge: The OdgsLlmBridge instance (provides the LLM provider).
        regulation_text: Raw regulation text to compile.
        context: Optional context dict (jurisdiction, domain, etc.).
        workspace_yaml: Optional workspace configuration for license checks.

    Returns:
        List of ODGS-compliant rule dicts, or upgrade prompt dict if unlicensed.
    """
    if workspace_yaml is not None:
        from odgs_llm.licensing import check_tier, Tier, upgrade_prompt
        if not check_tier(workspace_yaml, Tier.PROFESSIONAL):
            return upgrade_prompt(
                "compile_regulation",
                Tier.PROFESSIONAL,
                "Auto-generates rules from natural language (QE-01) — typically +40% maturity score"
            )

    system_prompt = _load_prompt()

    user_message = f"## Regulation Text\n\n{regulation_text}"
    if context:
        user_message += f"\n\n## Context\n\n```json\n{json.dumps(context, indent=2)}\n```"

    response = bridge._call(
        system_prompt=system_prompt,
        user_message=user_message,
        response_format="json",
    )

    # Parse and validate
    parsed = json.loads(response.text)
    rules = parsed if isinstance(parsed, list) else parsed.get("rules", [parsed])

    # Validate each rule against ODGS schema
    validated = validate_rules(rules)
    return validated
