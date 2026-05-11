"""
Capability B.5: Binding Discoverer

Given data catalog metadata (column names, types, descriptions from
Snowflake, Databricks, dbt, etc.), automatically generates a
physical_data_map.json that binds catalog columns to ODGS metrics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from odgs_llm.bridge import OdgsLlmBridge


def _load_prompt() -> str:
    path = Path(__file__).parent.parent / "prompts" / "binding_discoverer.md"
    return path.read_text(encoding="utf-8")


def discover_bindings(
    bridge: OdgsLlmBridge,
    catalog_metadata: dict,
    *,
    metrics: list[dict] | None = None,
    workspace_yaml: dict | None = None,
) -> dict:
    """
    Generate a physical_data_map.json from catalog metadata.

    Args:
        bridge: The OdgsLlmBridge instance.
        catalog_metadata: Dict describing the data catalog (tables, columns, types).
        metrics: Optional list of existing ODGS metric definitions to match against.
        workspace_yaml: Optional workspace configuration for license checks.

    Returns:
        physical_data_map dict ready for use with the ODGS Interceptor, or upgrade prompt.
    """
    if workspace_yaml is not None:
        from odgs_llm.licensing import check_tier, Tier, upgrade_prompt
        if not check_tier(workspace_yaml, Tier.PROFESSIONAL):
            return upgrade_prompt(
                "discover_bindings",
                Tier.PROFESSIONAL,
                "Auto-populate GOV-01 (Context Bindings) — typically +25-30% maturity score"
            )

    system_prompt = _load_prompt()

    user_message = f"## Data Catalog Metadata\n\n```json\n{json.dumps(catalog_metadata, indent=2)}\n```"

    if metrics:
        user_message += f"\n\n## Existing ODGS Metrics\n\n```json\n{json.dumps(metrics, indent=2)}\n```"

    response = bridge._call(
        system_prompt=system_prompt,
        user_message=user_message,
        response_format="json",
    )

    return json.loads(response.text)
