# ODGS LLM Bridge

> AI-powered governance capabilities for the Open Data Governance Standard (v6.0 Sovereign Validation Engine)

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![ODGS](https://img.shields.io/badge/ODGS-v6.0.0-green.svg)](https://github.com/MetricProvenance/odgs-protocol)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)

---

## What Is This?

The **ODGS LLM Bridge** is a **headless, standalone package** that augments the deterministic ODGS core engine with five AI-powered capabilities. It bridges the gap between probabilistic LLM output and the zero-tolerance deterministic ODGS validation engine.

```
┌─────────────────────────────────────────────────────────────┐
│                    ODGS LLM Bridge                          │
│                                                             │
│  Regulation Text ──→ [Regulatory Compiler] ──→ ODGS Rules  │
│  Definition Files ──→ [Drift Watchdog]     ──→ Warnings    │
│  Rule Sets       ──→ [Conflict Detector]   ──→ Conflicts   │
│  S-Cert JSON     ──→ [Audit Narrator]      ──→ Narrative   │
│  Catalog Meta    ──→ [Binding Discoverer]   ──→ Data Map    │
│                                                             │
│              ↓ All outputs validated ↓                      │
│         [JSON Schema Validation Gate]                       │
│              ↓ Before entering ↓                            │
│     [ODGS Sovereign Validation Engine v6.0]                 │
└─────────────────────────────────────────────────────────────┘
```

**Key principle:** LLMs are probabilistic. ODGS is deterministic. The bridge ensures every LLM-generated artifact passes JSON schema validation before entering the engine.

---

## Architecture: Model-Agnostic Providers

The bridge supports **any LLM** through a pluggable provider abstraction:

| Provider | Package Extra | Use Case |
|---|---|---|
| **Ollama** (local) | `pip install odgs-llm-bridge[ollama]` | Full sovereignty — zero egress |
| **Google GenAI** | `pip install odgs-llm-bridge[google]` | Gemini cloud API |
| **OpenAI-compatible** | `pip install odgs-llm-bridge[openai]` | GPT-NL, Mistral, GPT-4o, etc. |
| **LiteLLM** | `pip install odgs-llm-bridge[litellm]` | Universal router (100+ providers) |

**Auto-detection priority:** Ollama (local) → Google GenAI → OpenAI → Error

---

## Installation

```bash
# Core bridge (no LLM provider — bring your own)
pip install odgs-llm-bridge

# With Ollama (recommended for sovereignty)
pip install odgs-llm-bridge[ollama]

# With all providers
pip install odgs-llm-bridge[all]
```

---

## Quick Start

### Python API

```python
from odgs_llm import OdgsLlmBridge

# Auto-detects best available provider
bridge = OdgsLlmBridge()

# Or specify explicitly
bridge = OdgsLlmBridge(provider="ollama", model="gemma4:26b")

# 1. Compile regulation text → ODGS rules
rules = bridge.compile_regulation("""
    Article 10(3): The provider shall ensure that training,
    validation and testing data sets are relevant, sufficiently
    representative, and to the best extent possible, free of errors
    and complete in view of the intended purpose.
""")

# 2. Narrate an S-Cert for executives
narrative = bridge.narrate_audit(scert_json, audience="executive")

# 3. Detect rule conflicts
conflicts = bridge.detect_conflicts(all_rules)

# 4. Check for semantic drift
warnings = bridge.check_drift("./definitions/", threshold_days=90)

# 5. Discover bindings from catalog
bindings = bridge.discover_bindings(snowflake_catalog)
```

### CLI

```bash
# Compile a regulation file
odgs-llm compile regulation.txt -o rules.json

# Check definitions for drift
odgs-llm drift ./definitions/ --threshold 90

# Detect conflicts
odgs-llm conflicts rules.json

# Narrate an S-Cert
odgs-llm narrate scert.json --audience legal -o report.md

# Discover bindings
odgs-llm discover catalog.json --metrics metrics.json -o bindings.json

# Health check
odgs-llm health --provider ollama
```

---

## The Five Capabilities

### B.1: Regulatory Compiler
Converts raw regulation text (statutes, SLA clauses, policy documents) into ODGS-compliant rule JSON objects ready for the Sovereign Validation Engine.

### B.2: Drift Watchdog
Scans legislative definition files for semantic staleness — detects rules whose source regulations may have been updated, hashes that haven't been refreshed, or effective dates that have expired.

### B.3: Conflict Detector
Analyzes rule sets for semantic conflicts (contradictions, overlaps, shadows, deadlocks) across different regulatory sources or jurisdictions.

### B.4: Audit Narrator
Converts S-Cert (Semantic Certificate) JSON into human-readable narratives for three audiences: executive, legal, and technical.

### B.5: Binding Discoverer
Given data catalog metadata (Snowflake, Databricks, dbt, BigQuery), auto-generates `physical_data_map.json` binding physical columns to ODGS metrics.

---

## Output Validation

Every LLM-generated artifact passes through a **JSON Schema Validation Gate** before it can enter the ODGS engine:

```python
# This happens automatically inside the bridge
from odgs_llm.schemas.output_validators import validate_rules

validated = validate_rules(llm_output)  # invalid rules silently dropped
```

Invalid outputs are logged and filtered — the deterministic engine never sees malformed data.

---

## Custom Providers

Implement the `ModelProvider` interface to bring any LLM:

```python
from odgs_llm.providers import ModelProvider, ModelResponse

class MyProvider(ModelProvider):
    name = "my-provider"

    def generate(self, system_prompt, user_message, **kwargs) -> ModelResponse:
        # Your LLM call here
        return ModelResponse(text="...", model="my-model", provider=self.name)

bridge = OdgsLlmBridge(provider=MyProvider())
```

---

## Normative References

- **ODGS v6.0.0** — Sovereign Validation Engine
- **EU AI Act (2024/1689)** — Articles 10, 12
- **ISO/IEC 42001:2023** — AI Management System
- **GPT4NL (TNO)** — Dutch sovereign LLM initiative

---

> **For architectural clearance and certified regulatory packs:** [Consult the Sovereign S-Cert Registry](https://metricprovenance.com/brief)

---

*Apache 2.0 Licensed — Part of the ODGS Ecosystem*
