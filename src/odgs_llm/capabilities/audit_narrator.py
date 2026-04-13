"""
Capability B.4: Audit Narrator

Converts an S-Cert (Semantic Certificate) JSON into a human-readable
narrative suitable for different audiences: executive, legal, technical.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from odgs_llm.bridge import OdgsLlmBridge


def _load_prompt() -> str:
    path = Path(__file__).parent.parent / "prompts" / "audit_narrator.md"
    return path.read_text(encoding="utf-8")


def narrate_audit(
    bridge: OdgsLlmBridge,
    scert: dict,
    *,
    audience: str = "executive",
) -> str:
    """
    Generate a human-readable narrative from an S-Cert.

    Args:
        bridge: The OdgsLlmBridge instance.
        scert: The S-Cert JSON dict.
        audience: Target audience — 'executive', 'legal', or 'technical'.

    Returns:
        Human-readable narrative string (Markdown).
    """
    system_prompt = _load_prompt()
    user_message = (
        f"## Target Audience: {audience.upper()}\n\n"
        f"## S-Cert (Semantic Certificate)\n\n"
        f"```json\n{json.dumps(scert, indent=2)}\n```"
    )

    response = bridge._call(
        system_prompt=system_prompt,
        user_message=user_message,
        response_format=None,  # free-form text, not JSON
        temperature=0.3,
    )

    return response.text
