#!/usr/bin/env python3
"""Validate zhihui-customer-intent-resolution JSON output."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_FIELDS = [
    "intent_type",
    "answer",
    "recommended_feature",
    "troubleshooting_steps",
    "handoff_required",
    "handoff_reason",
    "confidence",
    "evidence",
]

INTENT_TYPES = {"功能推荐", "操作咨询", "FAQ", "效果排障", "风险转人工", "投诉升级"}
CONFIDENCE = {"high", "medium", "low"}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: validate_customer_intent_output.py <output.json>")
        raise SystemExit(2)

    path = Path(sys.argv[1])
    if not path.exists():
        fail(f"file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON: {exc}")

    if not isinstance(data, dict):
        fail("root must be an object")

    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        fail("missing required fields: " + ", ".join(missing))

    if data["intent_type"] not in INTENT_TYPES:
        fail("intent_type must be one of " + ", ".join(sorted(INTENT_TYPES)))

    if not isinstance(data["answer"], str) or not data["answer"].strip():
        fail("answer must be a non-empty string")

    if not isinstance(data["recommended_feature"], str):
        fail("recommended_feature must be a string")

    if not isinstance(data["troubleshooting_steps"], list):
        fail("troubleshooting_steps must be an array")
    if not all(isinstance(item, str) for item in data["troubleshooting_steps"]):
        fail("troubleshooting_steps items must be strings")

    if not isinstance(data["handoff_required"], bool):
        fail("handoff_required must be boolean")

    if not isinstance(data["handoff_reason"], str):
        fail("handoff_reason must be a string")
    if data["handoff_required"] and not data["handoff_reason"].strip():
        fail("handoff_reason is required when handoff_required is true")

    if data["confidence"] not in CONFIDENCE:
        fail("confidence must be high/medium/low")

    if not isinstance(data["evidence"], list):
        fail("evidence must be an array")
    if not data["evidence"]:
        fail("evidence must not be empty")
    if not all(isinstance(item, str) and item.strip() for item in data["evidence"]):
        fail("evidence items must be non-empty strings")

    print("OK: customer intent output is valid")


if __name__ == "__main__":
    main()
