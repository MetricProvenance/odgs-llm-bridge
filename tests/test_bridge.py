"""
Test suite for ODGS LLM Bridge — provider abstraction and output validation.

These tests use a mock provider to test the bridge logic without
requiring actual LLM access. This ensures deterministic CI testing.
"""

from __future__ import annotations

import json
import pytest

from odgs_llm.providers import ModelProvider, ModelResponse
from odgs_llm.schemas.output_validators import (
    validate_rules,
    validate_drift_warnings,
    validate_conflicts,
    validate_bindings,
)


# ── Mock Provider ──────────────────────────────────────────────────


class MockProvider(ModelProvider):
    """Deterministic mock provider for testing."""

    name = "mock"

    def __init__(self, response_text: str = ""):
        self._response_text = response_text

    def set_response(self, text: str):
        self._response_text = text

    def generate(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        response_format: str | None = None,
    ) -> ModelResponse:
        return ModelResponse(
            text=self._response_text,
            model="mock-model",
            provider="mock",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
        )

    def health_check(self) -> bool:
        return True


# ── Provider Tests ─────────────────────────────────────────────────


class TestProviderContract:
    def test_mock_provider_generates(self):
        p = MockProvider("hello")
        resp = p.generate("sys", "user")
        assert resp.text == "hello"
        assert resp.provider == "mock"

    def test_mock_health_check(self):
        p = MockProvider()
        assert p.health_check() is True

    def test_model_response_defaults(self):
        r = ModelResponse(text="ok", model="m", provider="p")
        assert r.usage == {}
        assert r.raw is None


# ── Bridge Tests ───────────────────────────────────────────────────


class TestBridge:
    def test_bridge_accepts_provider_instance(self):
        from odgs_llm.bridge import OdgsLlmBridge

        mock = MockProvider("test")
        bridge = OdgsLlmBridge(provider=mock)
        assert bridge.provider.name == "mock"

    def test_bridge_call(self):
        from odgs_llm.bridge import OdgsLlmBridge

        mock = MockProvider('{"rules": []}')
        bridge = OdgsLlmBridge(provider=mock)
        resp = bridge._call("sys", "user")
        assert resp.text == '{"rules": []}'


# ── Output Validator Tests ─────────────────────────────────────────


class TestRuleValidation:
    def test_valid_rule_passes(self):
        rule = {
            "rule_id": "RULE_TEST_001",
            "name": "Test Rule",
            "severity": "HARD_STOP",
            "logic_expression": "input.value > 0",
        }
        result = validate_rules([rule])
        assert len(result) == 1
        assert result[0]["rule_id"] == "RULE_TEST_001"

    def test_invalid_rule_id_rejected(self):
        rule = {
            "rule_id": "bad_id",  # doesn't start with RULE_
            "name": "Bad",
            "severity": "HARD_STOP",
            "logic_expression": "x > 0",
        }
        result = validate_rules([rule])
        assert len(result) == 0

    def test_invalid_severity_rejected(self):
        rule = {
            "rule_id": "RULE_X",
            "name": "X",
            "severity": "INVALID",
            "logic_expression": "x > 0",
        }
        result = validate_rules([rule])
        assert len(result) == 0

    def test_soft_stop_accepted(self):
        rule = {
            "rule_id": "RULE_SOFT",
            "name": "Soft Rule",
            "severity": "SOFT_STOP",
            "logic_expression": "input.x == True",
        }
        result = validate_rules([rule])
        assert len(result) == 1

    def test_missing_required_field_rejected(self):
        rule = {"rule_id": "RULE_MISSING", "name": "Missing"}
        result = validate_rules([rule])
        assert len(result) == 0

    def test_optional_fields_accepted(self):
        rule = {
            "rule_id": "RULE_FULL",
            "rule_urn": "urn:odgs:rule:eu:gdpr:art10",
            "name": "Full Rule",
            "description": "Comprehensive rule",
            "source_authority": "EU GDPR Art. 10",
            "severity": "HARD_STOP",
            "logic_expression": "input.has_consent == True",
            "failure_response": {"action": "BLOCK", "message": "Consent missing"},
            "tags": ["gdpr", "consent"],
            "version": "1.0.0",
            "depends_on": ["urn:odgs:rule:eu:gdpr:art5"],
        }
        result = validate_rules([rule])
        assert len(result) == 1

    def test_batch_validation(self):
        rules = [
            {"rule_id": "RULE_A", "name": "A", "severity": "HARD_STOP", "logic_expression": "a"},
            {"rule_id": "bad", "name": "B", "severity": "HARD_STOP", "logic_expression": "b"},
            {"rule_id": "RULE_C", "name": "C", "severity": "WARNING", "logic_expression": "c"},
        ]
        result = validate_rules(rules)
        assert len(result) == 2  # bad ID filtered out


class TestDriftValidation:
    def test_valid_drift_warning(self):
        warning = {
            "file": "metrics.json",
            "metric_id": "NET_REVENUE",
            "status": "STALE",
            "reason": "Last updated 180 days ago",
            "recommendation": "Review with source authority",
            "confidence": 0.85,
        }
        result = validate_drift_warnings([warning])
        assert len(result) == 1

    def test_invalid_status_rejected(self):
        warning = {"file": "x.json", "status": "UNKNOWN"}
        result = validate_drift_warnings([warning])
        assert len(result) == 0


class TestConflictValidation:
    def test_valid_conflict(self):
        conflict = {
            "rule_a": "RULE_EU_001",
            "rule_b": "RULE_NL_001",
            "conflict_type": "CONTRADICTION",
            "severity": "CRITICAL",
            "description": "Opposite outcomes on same condition",
            "recommendation": "Resolve with legal team",
        }
        result = validate_conflicts([conflict])
        assert len(result) == 1

    def test_invalid_conflict_type_rejected(self):
        conflict = {
            "rule_a": "A",
            "rule_b": "B",
            "conflict_type": "INVALID_TYPE",
        }
        result = validate_conflicts([conflict])
        assert len(result) == 0


class TestBindingValidation:
    def test_valid_bindings(self):
        bindings = {
            "bindings": [
                {
                    "metric_urn": "urn:odgs:metric:finance:net_revenue",
                    "physical_source": {
                        "platform": "snowflake",
                        "database": "PROD",
                        "schema": "FINANCE",
                        "table": "REVENUE",
                        "column": "net_revenue",
                    },
                    "confidence": 0.95,
                    "reasoning": "Exact column name match",
                }
            ],
            "unmatched_columns": ["temp_col"],
            "suggested_metrics": [],
        }
        result = validate_bindings(bindings)
        assert len(result["bindings"]) == 1

    def test_missing_bindings_key_raises(self):
        with pytest.raises(Exception):
            validate_bindings({"no_bindings": []})


# ── Regulatory Compiler Integration ───────────────────────────────


class TestRegulatoryCompilerIntegration:
    def test_compile_returns_validated_rules(self):
        from odgs_llm.bridge import OdgsLlmBridge

        mock_rules = json.dumps({
            "rules": [
                {
                    "rule_id": "RULE_GDPR_001",
                    "name": "Data accuracy requirement",
                    "severity": "HARD_STOP",
                    "logic_expression": "input.accuracy_score >= 0.95",
                    "source_authority": "EU GDPR Article 5(1)(d)",
                }
            ]
        })
        mock = MockProvider(mock_rules)
        bridge = OdgsLlmBridge(provider=mock)
        rules = bridge.compile_regulation("Personal data shall be accurate...")
        assert len(rules) == 1
        assert rules[0]["rule_id"] == "RULE_GDPR_001"

    def test_compile_filters_invalid_rules(self):
        from odgs_llm.bridge import OdgsLlmBridge

        mock_output = json.dumps({
            "rules": [
                {"rule_id": "RULE_OK", "name": "OK", "severity": "WARNING", "logic_expression": "x"},
                {"rule_id": "invalid", "name": "Bad", "severity": "HARD_STOP", "logic_expression": "y"},
            ]
        })
        mock = MockProvider(mock_output)
        bridge = OdgsLlmBridge(provider=mock)
        rules = bridge.compile_regulation("Some regulation text...")
        assert len(rules) == 1  # only valid rule passes


# ── Audit Narrator Integration ────────────────────────────────────


class TestAuditNarratorIntegration:
    def test_narrate_returns_text(self):
        from odgs_llm.bridge import OdgsLlmBridge

        mock = MockProvider("## Audit Summary\n\nThe process was GRANTED access.")
        bridge = OdgsLlmBridge(provider=mock)
        narrative = bridge.narrate_audit({"status": "GRANTED"}, audience="executive")
        assert "GRANTED" in narrative


# ── Conflict Detector Integration ─────────────────────────────────


class TestConflictDetectorIntegration:
    def test_detect_returns_conflicts(self):
        from odgs_llm.bridge import OdgsLlmBridge

        mock_output = json.dumps([{
            "rule_a": "RULE_A",
            "rule_b": "RULE_B",
            "conflict_type": "OVERLAP",
            "severity": "LOW",
            "description": "Both check same condition",
            "recommendation": "Deduplicate",
        }])
        mock = MockProvider(mock_output)
        bridge = OdgsLlmBridge(provider=mock)
        conflicts = bridge.detect_conflicts([{"rule_id": "A"}, {"rule_id": "B"}])
        assert len(conflicts) == 1

    def test_single_rule_returns_empty(self):
        from odgs_llm.bridge import OdgsLlmBridge

        mock = MockProvider("[]")
        bridge = OdgsLlmBridge(provider=mock)
        conflicts = bridge.detect_conflicts([{"rule_id": "A"}])
        assert conflicts == []
