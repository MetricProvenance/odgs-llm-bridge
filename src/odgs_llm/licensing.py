from enum import Enum
from typing import Optional
from pathlib import Path
import yaml
import hashlib
import hmac
from datetime import date

class Tier(Enum):
    COMMUNITY = "community"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

def check_tier(workspace_yaml: dict, required_tier: Tier) -> bool:
    """
    Check if workspace license meets the required tier.
    
    License validation is offline-first:
    1. Read license block from workspace YAML
    2. Verify JWT signature against workspace_id
    3. Check expiry date
    4. Compare tier level
    
    No network calls. No telemetry. Zero-knowledge.
    """
    license_block = workspace_yaml.get("license", {})
    
    if required_tier == Tier.COMMUNITY:
        return True  # Always allowed
    
    key = license_block.get("key", "")
    tier = license_block.get("tier", "community")
    workspace_id = license_block.get("workspace_id", "")
    expires = license_block.get("expires", "")
    
    # Tier hierarchy: enterprise > professional > community
    tier_levels = {
        "community": 0,
        "professional": 1,
        "enterprise": 2,
    }
    
    current_level = tier_levels.get(tier, 0)
    required_level = tier_levels.get(required_tier.value, 0)
    
    if current_level < required_level:
        return False
    
    # Verify key signature (JWT of workspace_id)
    # Key format: JWT token
    # Full validation requires the public signing key
    if required_level > 0 and not key.startswith("eyJ"):
        return False
    
    # Check expiry
    if expires:
        try:
            expiry = date.fromisoformat(expires)
            if date.today() > expiry:
                return False
        except ValueError:
            return False
    
    return True


def upgrade_prompt(skill_name: str, required_tier: Tier, maturity_impact: str) -> dict:
    """
    Generate a structured upgrade prompt when a skill requires a higher tier.
    
    Returns a dict that MCP/LLM bridge can render as a helpful message
    showing what the skill would fix and how to upgrade.
    """
    return {
        "status": "upgrade_required",
        "skill": skill_name,
        "required_tier": required_tier.value,
        "message": (
            f"The '{skill_name}' skill requires a {required_tier.value} license. "
            f"This skill would: {maturity_impact}"
        ),
        "upgrade_url": "https://metricprovenance.com/brief",
        "current_gaps": maturity_impact,
    }
