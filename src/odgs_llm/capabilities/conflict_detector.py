"""
Capability B.3: Conflict Detector

Analyzes a set of ODGS rules from potentially different regulatory
sources for semantic conflicts, overlapping jurisdictions,
contradictory severity levels, or logical impossibilities.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from odgs_llm.bridge import OdgsLlmBridge


def _load_prompt() -> str:
    path = Path(__file__).parent.parent / "prompts" / "conflict_detector.md"
    return path.read_text(encoding="utf-8")


def detect_conflicts(
    bridge: OdgsLlmBridge,
    rules: list[dict],
) -> list[dict]:
    """
    Detect conflicts across a set of ODGS rules.

    Args:
        bridge: The OdgsLlmBridge instance.
        rules: List of ODGS rule dicts to analyze.

    Returns:
        List of conflict dicts with fields:
        - rule_a, rule_b, conflict_type, severity, description, recommendation
    """
    if len(rules) < 2:
        return []

    system_prompt = _load_prompt()
    user_message = (
        f"## Rules to Analyze ({len(rules)} rules)\n\n"
        f"```json\n{json.dumps(rules, indent=2)}\n```"
    )

    response = bridge._call(
        system_prompt=system_prompt,
        user_message=user_message,
        response_format="json",
    )

    parsed = json.loads(response.text)
    return parsed if isinstance(parsed, list) else parsed.get("conflicts", [])
