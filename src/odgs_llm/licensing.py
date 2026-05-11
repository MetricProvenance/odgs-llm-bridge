"""
Offline-first licence verification for ODGS workspaces.

Licence JWTs are issued by Metric Provenance and signed with an Ed25519
asymmetric key. The public key is embedded here; the private key is held
exclusively by Metric Provenance and never distributed.

Verification is fully offline — no network calls, no telemetry.
"""

from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Embedded public keys
# ---------------------------------------------------------------------------

# Production public key — replace with production key before first real
# customer licence is issued. Generate via:
#   python3 -c "
#   from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
#   from cryptography.hazmat.primitives import serialization
#   k = Ed25519PrivateKey.generate()
#   print(k.public_key().public_bytes(serialization.Encoding.PEM,
#         serialization.PublicFormat.SubjectPublicKeyInfo).decode())"
#
# Store the private key in GCP Secret Manager as:
#   projects/metricprovenance/secrets/odgs-licence-signing-key/versions/latest
#
# Then update LICENCE_PUBLIC_KEY_PEM below and rebuild / republish the package.

# TEST public key — used in CI, E2E tests, and local development.
# The corresponding private key is at /tmp/odgs_licence_test_private.pem
# (generated during development setup, never committed).
_LICENCE_PUBLIC_KEY_TEST = """-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAmVcxflkCJree6sw+/duSP2YO2XGhCv6rSA86/1XUr3Y=
-----END PUBLIC KEY-----"""

# PRODUCTION public key — Ed25519 public key for verifying customer licence JWTs.
# Corresponding private key stored in GCP Secret Manager:
#   projects/metric-provenance-prod/secrets/odgs-licence-signing-key/versions/1
# Generated 2026-05-11 via: openssl genpkey -algorithm ed25519
_LICENCE_PUBLIC_KEY_PRODUCTION = """-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAmkNRKcgAj2v2OD7RksOF+Fiuh09pKes971Zo9ODwg18=
-----END PUBLIC KEY-----"""

import os
_ENV = os.environ.get("ODGS_LICENCE_ENV", "production")
LICENCE_PUBLIC_KEY_PEM = (
    _LICENCE_PUBLIC_KEY_TEST if _ENV == "test" else _LICENCE_PUBLIC_KEY_PRODUCTION
)


# ---------------------------------------------------------------------------
# Tier definitions
# ---------------------------------------------------------------------------

class Tier(Enum):
    COMMUNITY = "community"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


_TIER_LEVELS = {
    "community": 0,
    "professional": 1,
    "enterprise": 2,
}


# ---------------------------------------------------------------------------
# Core verification
# ---------------------------------------------------------------------------

def check_tier(workspace_yaml: dict, required_tier: Tier) -> bool:
    """
    Check whether the workspace licence meets the required tier.

    Validation is offline-first and fully cryptographic:
    1. Extract the licence block from workspace YAML.
    2. Verify the JWT signature using the embedded Ed25519 public key.
    3. Check the token has not expired (PyJWT handles this via 'exp' claim).
    4. Compare the tier claim against the required level.

    No network calls. No telemetry. Zero-knowledge from the client side.

    Args:
        workspace_yaml: Parsed contents of odgs-workspace.yaml.
        required_tier:  The minimum Tier the calling feature requires.

    Returns:
        True if the licence is valid and meets the required tier.
        False for any validation failure (forged token, expired, wrong tier).
    """
    if required_tier == Tier.COMMUNITY:
        return True  # Community is always allowed

    license_block = workspace_yaml.get("license", {})
    key = license_block.get("key", "")

    if not key or not key.startswith("eyJ"):
        logger.debug("No valid licence key found in workspace YAML")
        return False

    try:
        import jwt as pyjwt
        from cryptography.hazmat.primitives.serialization import load_pem_public_key

        public_key = load_pem_public_key(LICENCE_PUBLIC_KEY_PEM.encode())

        # PyJWT verifies: signature (Ed25519), expiry ('exp'), issuer if options set.
        # options: verify_exp=True is the default — expired tokens raise ExpiredSignatureError.
        payload = pyjwt.decode(
            key,
            public_key,
            algorithms=["EdDSA"],
            options={"verify_exp": True},
        )

        token_tier = payload.get("tier", "community")
        current_level = _TIER_LEVELS.get(token_tier, 0)
        required_level = _TIER_LEVELS.get(required_tier.value, 0)

        if current_level < required_level:
            logger.debug(
                "Licence tier '%s' does not meet required '%s'",
                token_tier, required_tier.value,
            )
            return False

        logger.info(
            "Licence verified offline: org=%s tier=%s",
            payload.get("org", "unknown"), token_tier,
        )
        return True

    except ImportError:
        logger.warning(
            "PyJWT or cryptography not installed — cannot verify licence JWT. "
            "Install with: pip install 'PyJWT[crypto]' cryptography"
        )
        return False

    except Exception as e:
        # Log at debug level only — don't leak JWT internals in normal logs.
        logger.debug("Licence JWT verification failed: %s", e)
        return False


# ---------------------------------------------------------------------------
# Upgrade prompt
# ---------------------------------------------------------------------------

def upgrade_prompt(skill_name: str, required_tier: Tier, maturity_impact: str) -> dict:
    """
    Return a structured upgrade prompt when a feature requires a higher tier.

    The returned dict is rendered by the MCP/LLM bridge as a user-facing message
    explaining what the feature would address and where to request access.
    """
    return {
        "status": "upgrade_required",
        "skill": skill_name,
        "required_tier": required_tier.value,
        "message": (
            f"The '{skill_name}' capability requires a {required_tier.value} licence. "
            f"This would address: {maturity_impact}"
        ),
        "upgrade_url": "https://metricprovenance.com/brief",
        "current_gaps": maturity_impact,
    }
