# Open Data Governance Standard (ODGS) — LLM Bridge

> **AI-generated governance artefacts, deterministically enforced.**

[![Protocol](https://img.shields.io/badge/Protocol-v6.0.3_(Sovereign_Engine)-0055AA)](https://metricprovenance.com/brief)
[![LLM Bridge](https://img.shields.io/badge/LLM_Bridge-v0.2.0-blueviolet)](https://pypi.org/project/odgs-llm-bridge/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/odgs-llm-bridge?label=PyPI%20Downloads&color=blue)](https://pypistats.org/packages/odgs-llm-bridge)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache_2.0-lightgrey)](LICENSE)

---

> **For engineers:** See [Quick Start](#quick-start) below.  
> **For compliance and risk officers:** The bridge produces governance artefacts — compiled rules, drift reports, S-Cert narratives — that enter the Sovereign Validation Engine as structured, schema-validated JSON.  
> **For architectural assessment and certified packs:** [metricprovenance.com/brief](https://metricprovenance.com/brief)

---

> [!IMPORTANT]
> **ODGS LLM Bridge v0.2.0 — Offline Licence Verification + Enterprise Tier Gate**
> Licence JWTs are now verified **cryptographically** (Ed25519, offline — no network call).
> Regulatory compilation, drift detection, and catalog synchronisation require a certified pack licence.
> The community tier — schema validation, conformance checking — remains open with no registration.

---

### What's New in v0.2.0

| Change | Detail |
|---|---|
| **Ed25519 offline verification** | Licence JWTs signed by Metric Provenance; verified against embedded public key. Forged tokens are cryptographically rejected. |
| **Tier gate** | Community / Professional / Enterprise access from `odgs-workspace.yaml`. Air-gapped environments fully supported. |
| **`odgs-maturity` integration** | Governance maturity scoring delegates to the 8-pillar DAMA DMBOK engine when installed. |

> The European Data Governance Maturity Benchmark 2026 recorded an average maturity of **37.6%** across 99 enterprises — a **62.4% gap** against current regulatory expectation. The ODGS engine applies the same assessment methodology at the pipeline level.

---

## What This Is

The **ODGS LLM Bridge** is a headless Python package that converts probabilistic LLM output into deterministic governance artefacts. Every LLM-generated artifact passes a JSON Schema Validation Gate before it enters the ODGS Sovereign Validation Engine — the engine never sees malformed data.

```
┌──────────────────────────────────────────────────────────────┐
│                      ODGS LLM Bridge                         │
│                                                              │
│  Regulation Text ──→ [Regulatory Compiler] ──→ ODGS Rules   │
│  Definition Files ──→ [Drift Watchdog]     ──→ Alerts       │
│  Rule Sets        ──→ [Conflict Detector]  ──→ Conflicts     │
│  S-Cert JSON      ──→ [Audit Narrator]     ──→ Narrative     │
│  Catalog Metadata ──→ [Binding Discoverer] ──→ Data Map      │
│                                                              │
│              ↓  All outputs pass through  ↓                  │
│           [JSON Schema Validation Gate]                      │
│              ↓  before entering          ↓                   │
│       [ODGS Sovereign Validation Engine v6.0]                │
└──────────────────────────────────────────────────────────────┘
```

### EU AI Act & High-Risk AI Systems

Organisations operating High-Risk AI Systems under **EU AI Act Articles 10 and 12** require demonstrable, auditable data governance at the pipeline level. The bridge compiles regulatory text into machine-verifiable ODGS rules; each evaluation produces an S-Cert suitable for regulatory submission.

Certified Sovereign Packs and the S-Cert Registry are available through Metric Provenance certified implementation partners. For architectural assessment: [metricprovenance.com/brief](https://metricprovenance.com/brief).

---

## Quick Start

```bash
# Core bridge — no LLM provider bundled (bring your own)
pip install odgs-llm-bridge

# With Ollama (recommended for air-gapped / sovereign deployments)
pip install odgs-llm-bridge[ollama]

# With all providers
pip install odgs-llm-bridge[all]
```

### Python API

```python
from odgs_llm import OdgsLlmBridge

# Auto-detects best available provider (Ollama → Google GenAI → OpenAI)
bridge = OdgsLlmBridge()

# 1. Compile regulation text → validated ODGS rules
rules = bridge.compile_regulation("""
    Article 10(3): The provider shall ensure that training,
    validation and testing data sets are relevant, sufficiently
    representative, and to the best extent possible, free of errors
    and complete in view of the intended purpose.
""")

# 2. Narrate an S-Cert for non-technical stakeholders
narrative = bridge.narrate_audit(scert_json, audience="executive")

# 3. Detect contradictions between regulatory rule sets
conflicts = bridge.detect_conflicts(all_rules)

# 4. Identify definitional drift across governance artefact versions
warnings = bridge.check_drift("./definitions/", threshold_days=90)

# 5. Auto-generate physical data map from catalog metadata
bindings = bridge.discover_bindings(snowflake_catalog)
```

### CLI

```bash
odgs-llm compile regulation.txt -o rules.json
odgs-llm drift ./definitions/ --threshold 90
odgs-llm conflicts rules.json
odgs-llm narrate scert.json --audience legal -o report.md
odgs-llm discover catalog.json --metrics metrics.json -o bindings.json
odgs-llm health --provider ollama
```

---

## Capabilities

### Community (Free — no account required)

| Capability | Description |
|:---|:---|
| Schema validation | Validate LLM-generated artefacts against ODGS JSON schemas |
| Governance scoring | 8-pillar DAMA DMBOK maturity score (0–100) with gap analysis |
| Conformance check | Run ODGS conformance self-check against workspace definitions |

### Professional (Certified Pack Licence)

| Capability | Description |
|:---|:---|
| `compile_regulation` | Convert legislative text (EU AI Act, DORA, GDPR) → ODGS rule JSON |
| `check_drift` | Detect semantic drift in governance definitions across versions |
| `detect_conflicts` | Identify contradictions and shadows between regulatory rule sets |
| `narrate_audit` | Convert S-Cert JSON → narrative for executive, legal, or technical audiences |
| `discover_bindings` | Auto-generate `physical_data_map.json` from Snowflake, Databricks, dbt catalogs |

### Enterprise (Certified Pack Licence + Partner Agreement)

| Capability | Description |
|:---|:---|
| `sync_catalog` | Pull and ingest metadata from Databricks / Snowflake / Collibra |
| `harvest_sovereign_rules` | Extract and mint sovereign rules directly from data stores (Flint Bridge) |

*Certified Pack licensing is handled through Metric Provenance partners: [metricprovenance.com/brief](https://metricprovenance.com/brief).*

---

## Workspace Licence Configuration

For air-gapped and offline deployments, licences are issued as Ed25519-signed JWTs and placed in `odgs-workspace.yaml`:

```yaml
license:
  key: "eyJ..."   # Ed25519-signed JWT issued by Metric Provenance
  tier: enterprise
```

The bridge verifies the JWT signature offline against the embedded public key — no network call required. Licence issuance is handled through [metricprovenance.com/brief](https://metricprovenance.com/brief).

---

## Model Providers

| Provider | Extra | Recommended for |
|:---|:---|:---|
| **Ollama** (local) | `pip install odgs-llm-bridge[ollama]` | Full sovereignty — zero egress, air-gapped environments |
| **Google GenAI** | `pip install odgs-llm-bridge[google]` | Gemini cloud API |
| **OpenAI-compatible** | `pip install odgs-llm-bridge[openai]` | GPT-NL (TNO), Mistral, GPT-4o |
| **LiteLLM** | `pip install odgs-llm-bridge[litellm]` | Universal router (100+ providers) |

Auto-detection priority: Ollama → Google GenAI → OpenAI → error.

### Custom Provider

```python
from odgs_llm.providers import ModelProvider, ModelResponse

class MyProvider(ModelProvider):
    name = "my-provider"

    def generate(self, system_prompt, user_message, **kwargs) -> ModelResponse:
        return ModelResponse(text="...", model="my-model", provider=self.name)

bridge = OdgsLlmBridge(provider=MyProvider())
```

---

## Normative References

- **ODGS v6.0.3** — Sovereign Validation Engine specification
- **EU AI Act (2024/1689)** — Articles 10, 12 (data governance obligations for high-risk AI)
- **ISO/IEC 42001:2023** — AI Management System
- **DAMA DMBOK v2** — 8-pillar data management maturity framework
- **GPT4NL (TNO)** — Dutch sovereign LLM initiative

---

## About ODGS

The Open Data Governance Standard (ODGS) is an open protocol for deterministic data governance enforcement. It is a candidate standard under CEN/CENELEC JTC 25 and has been submitted to NEN ballot N42 (closes May 2026).

- [Protocol specification](https://github.com/MetricProvenance/odgs) — `pip install odgs`
- [MCP Server](https://pypi.org/project/odgs-mcp-server/) — `pip install odgs-mcp-server`
- [Maturity engine](https://pypi.org/project/odgs-maturity/) — `pip install odgs-maturity`
- [Research paper (SSRN 6205478)](https://papers.ssrn.com/abstract=6205478)
- [Metric Provenance](https://metricprovenance.com/brief)

## Licence

Apache 2.0 — see [LICENSE](LICENSE).

The protocol engine and LLM bridge are open source. Certified Regulation Packs are issued under a commercial licence through Metric Provenance certified partners.
