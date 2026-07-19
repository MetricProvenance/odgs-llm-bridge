# Changelog

## v0.2.2 — 2026-07-18

### Fixed

- `__version__` in `odgs_llm/__init__.py` was stuck at `0.1.0` while the published package was 0.2.x. It now matches the package version (`0.2.2`).

### Changed

- `licensing.upgrade_prompt()` now points `upgrade_url` at the self-serve pricing page (`metricprovenance.com/pricing`) instead of the partner brief (`/brief`).

No functional changes to the bridge, providers, or capabilities.

---

## v0.2.1 — 2026-05-03

*(retroactive entry)*

- Packaging and metadata fixes on top of 0.2.0; no API changes.

## v0.2.0 — 2026-05-03

*(retroactive entry)*

- Added the offline zero-knowledge licensing module (`odgs_llm.licensing`): JWT-based tier verification (`check_tier`, `Tier`) used by downstream tooling (including odgs-mcp-server) to validate Professional/Enterprise workspaces without a network call.
- Structured `upgrade_prompt()` for tier-gated capabilities.

## v0.1.0 — 2026-04-13

Initial public release: `OdgsLlmBridge` with five AI capabilities (Regulatory Compiler, Drift Watchdog, Conflict Detector, Audit Narrator, Binding Discoverer), provider abstraction (Ollama/Gemma, OpenAI-compatible, LiteLLM), CLI, and schema-validated outputs.
