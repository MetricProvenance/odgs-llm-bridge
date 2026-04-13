"""
Output validators — ensure LLM-generated JSON conforms to ODGS schemas
before it enters the deterministic engine.

This is the critical safety gate: LLMs are probabilistic, but the ODGS
engine is deterministic. This module ensures the boundary is clean.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import jsonschema

logger = logging.getLogger(__name__)

# ── Minimal rule schema for validation ────────────────────────────
# This is a subset of the full ODGS rule schema, sufficient to validate
# LLM-generated rules before they enter the engine.

RULE_SCHEMA = {
    "type": "object",
    "required": ["rule_id", "name", "severity", "logic_expression"],
    "properties": {
        "rule_id": {"type": "string", "pattern": "^RULE_"},
        "rule_urn": {"type": "string", "pattern": "^urn:odgs:rule:"},
        "name": {"type": "string", "minLength": 1},
        "description": {"type": "string"},
        "source_authority": {"type": "string"},
        "severity": {
            "type": "string",
            "enum": ["HARD_STOP", "SOFT_STOP", "WARNING", "INFO"],
        },
        "logic_expression": {"type": "string", "minLength": 1},
        "failure_response": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["BLOCK", "WARN", "LOG"]},
                "message": {"type": "string"},
            },
        },
        "tags": {"type": "array", "items": {"type": "string"}},
        "version": {"type": "string"},
        "depends_on": {"type": "array", "items": {"type": "string"}},
    },
}

DRIFT_WARNING_SCHEMA = {
    "type": "object",
    "required": ["file", "status"],
    "properties": {
        "file": {"type": "string"},
        "metric_id": {"type": "string"},
        "status": {
            "type": "string",
            "enum": ["STALE", "EXPIRED", "ORPHANED", "CURRENT"],
        },
        "reason": {"type": "string"},
        "recommendation": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
}

CONFLICT_SCHEMA = {
    "type": "object",
    "required": ["rule_a", "rule_b", "conflict_type"],
    "properties": {
        "rule_a": {"type": "string"},
        "rule_b": {"type": "string"},
        "conflict_type": {
            "type": "string",
            "enum": ["CONTRADICTION", "OVERLAP", "SHADOW", "DEADLOCK"],
        },
        "severity": {
            "type": "string",
            "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        },
        "description": {"type": "string"},
        "recommendation": {"type": "string"},
    },
}

BINDING_SCHEMA = {
    "type": "object",
    "required": ["bindings"],
    "properties": {
        "bindings": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["metric_urn", "physical_source"],
                "properties": {
                    "metric_urn": {"type": "string", "pattern": "^urn:odgs:metric:"},
                    "physical_source": {"type": "object"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "reasoning": {"type": "string"},
                },
            },
        },
        "unmatched_columns": {"type": "array", "items": {"type": "string"}},
        "suggested_metrics": {"type": "array"},
    },
}


def validate_rules(rules: list[dict]) -> list[dict]:
    """Validate a list of LLM-generated rule dicts against the ODGS rule schema."""
    validated = []
    for i, rule in enumerate(rules):
        try:
            jsonschema.validate(instance=rule, schema=RULE_SCHEMA)
            validated.append(rule)
        except jsonschema.ValidationError as e:
            logger.warning(f"Rule {i} failed validation: {e.message}. Skipping.")
    return validated


def validate_drift_warnings(warnings: list[dict]) -> list[dict]:
    """Validate drift warning dicts."""
    validated = []
    for w in warnings:
        try:
            jsonschema.validate(instance=w, schema=DRIFT_WARNING_SCHEMA)
            validated.append(w)
        except jsonschema.ValidationError as e:
            logger.warning(f"Drift warning failed validation: {e.message}. Skipping.")
    return validated


def validate_conflicts(conflicts: list[dict]) -> list[dict]:
    """Validate conflict dicts."""
    validated = []
    for c in conflicts:
        try:
            jsonschema.validate(instance=c, schema=CONFLICT_SCHEMA)
            validated.append(c)
        except jsonschema.ValidationError as e:
            logger.warning(f"Conflict failed validation: {e.message}. Skipping.")
    return validated


def validate_bindings(bindings: dict) -> dict:
    """Validate a physical_data_map dict."""
    jsonschema.validate(instance=bindings, schema=BINDING_SCHEMA)
    return bindings
