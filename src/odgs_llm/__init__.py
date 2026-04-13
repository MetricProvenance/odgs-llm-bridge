"""
ODGS LLM Bridge — AI-powered governance capabilities for the
Open Data Governance Standard (Sovereign Validation Engine v6.0).

This is a headless, standalone package that uses LLM providers
to augment the deterministic ODGS core with five AI capabilities:

1. Regulatory Compiler   — regulation text → ODGS rule JSON
2. Drift Watchdog        — semantic hash staleness detection
3. Conflict Detector     — cross-bridge rule conflict analysis
4. Audit Narrator        — S-Cert → human-readable narrative
5. Binding Discoverer    — catalog metadata → physical_data_map.json
"""

__version__ = "0.1.0"

from odgs_llm.bridge import OdgsLlmBridge

__all__ = ["OdgsLlmBridge", "__version__"]
