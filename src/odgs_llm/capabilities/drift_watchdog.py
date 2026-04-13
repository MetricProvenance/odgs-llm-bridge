"""
Capability B.2: Drift Watchdog

Scans legislative definition files for semantic staleness — detects
rules whose source regulations may have been updated, hashes that
haven't been refreshed, or effective dates that have expired.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from odgs_llm.bridge import OdgsLlmBridge


def _load_prompt() -> str:
    path = Path(__file__).parent.parent / "prompts" / "drift_watchdog.md"
    return path.read_text(encoding="utf-8")


def check_drift(
    bridge: OdgsLlmBridge,
    definitions_dir: str,
    *,
    threshold_days: int = 90,
) -> list[dict]:
    """
    Scan a directory of ODGS definition files for drift.

    Args:
        bridge: The OdgsLlmBridge instance.
        definitions_dir: Path to directory containing definition JSONs.
        threshold_days: Number of days after which a definition is considered stale.

    Returns:
        List of drift warning dicts with fields:
        - file, metric_id, status, reason, recommendation
    """
    definitions_path = Path(definitions_dir)
    if not definitions_path.is_dir():
        raise FileNotFoundError(f"Definitions directory not found: {definitions_dir}")

    # Collect all definition files
    definition_files = list(definitions_path.glob("*.json"))
    if not definition_files:
        return []

    # Build summary for LLM analysis
    summaries = []
    for f in definition_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            summaries.append({
                "file": f.name,
                "content_preview": json.dumps(data, indent=2)[:2000],
            })
        except (json.JSONDecodeError, OSError):
            summaries.append({"file": f.name, "error": "Could not parse"})

    system_prompt = _load_prompt()
    user_message = (
        f"## Drift Analysis Request\n\n"
        f"Threshold: {threshold_days} days\n\n"
        f"## Definition Files\n\n"
        f"```json\n{json.dumps(summaries, indent=2)}\n```"
    )

    response = bridge._call(
        system_prompt=system_prompt,
        user_message=user_message,
        response_format="json",
    )

    parsed = json.loads(response.text)
    return parsed if isinstance(parsed, list) else parsed.get("warnings", [])
