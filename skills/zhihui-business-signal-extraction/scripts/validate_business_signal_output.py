#!/usr/bin/env python3
"""Validate zhihui-business-signal-extraction JSON output.

This script intentionally uses only Python standard library so it can run on a
new machine without installing dependencies.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_FIELDS = [
    "opportunity_level",
    "opportunity_reason",
    "pain_points",
    "budget_signal",
    "timeline_signal",
    "decision_chain",
    "product_feedback",
    "risk_flags",
    "next_actions",
    "summary_for_sales",
    "summary_for_product",
]

LEVELS = {"A", "B", "C", "None"}
OWNERS = {"销售", "产品", "技术", "客服", "暂不处理"}
PRIORITIES = {"high", "medium", "low"}
BUDGET_STATUSES = {"明确", "隐含", "无"}
TIMELINE_STATUSES = {"紧急", "近期", "长期", "不明确"}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def require_object(value, name: str) -> dict:
    if not isinstance(value, dict):
        fail(f"{name} must be an object")
    return value


def require_array(value, name: str) -> list:
    if not isinstance(value, list):
        fail(f"{name} must be an array")
    return value


def require_str_field(obj: dict, field: str, context: str, allow_empty: bool = False) -> None:
    if field not in obj:
        fail(f"{context}.{field} is required")
    if not isinstance(obj[field], str):
        fail(f"{context}.{field} must be a string")
    if not allow_empty and not obj[field].strip():
        fail(f"{context}.{field} must not be empty")


def validate_evidence_items(items: list, context: str, fields: list[str]) -> None:
    for idx, item in enumerate(items):
        obj = require_object(item, f"{context}[{idx}]")
        for field in fields:
            require_str_field(obj, field, f"{context}[{idx}]")
        require_str_field(obj, "evidence", f"{context}[{idx}]")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: validate_business_signal_output.py <output.json>")
        raise SystemExit(2)

    path = Path(sys.argv[1])
    if not path.exists():
        fail(f"file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON: {exc}")

    obj = require_object(data, "root")

    missing = [field for field in REQUIRED_FIELDS if field not in obj]
    if missing:
        fail("missing required fields: " + ", ".join(missing))

    if obj["opportunity_level"] not in LEVELS:
        fail("opportunity_level must be one of A, B, C, None")

    require_str_field(obj, "opportunity_reason", "root")
    require_str_field(obj, "summary_for_sales", "root")
    require_str_field(obj, "summary_for_product", "root")

    validate_evidence_items(require_array(obj["pain_points"], "pain_points"), "pain_points", ["type"])
    validate_evidence_items(require_array(obj["decision_chain"], "decision_chain"), "decision_chain", ["role"])
    validate_evidence_items(
        require_array(obj["product_feedback"], "product_feedback"),
        "product_feedback",
        ["feature", "feedback_type"],
    )
    validate_evidence_items(require_array(obj["risk_flags"], "risk_flags"), "risk_flags", ["type"])

    budget = require_object(obj["budget_signal"], "budget_signal")
    require_str_field(budget, "status", "budget_signal")
    require_str_field(budget, "evidence", "budget_signal", allow_empty=True)
    if budget["status"] not in BUDGET_STATUSES:
        fail("budget_signal.status must be 明确/隐含/无")

    timeline = require_object(obj["timeline_signal"], "timeline_signal")
    require_str_field(timeline, "status", "timeline_signal")
    require_str_field(timeline, "evidence", "timeline_signal", allow_empty=True)
    if timeline["status"] not in TIMELINE_STATUSES:
        fail("timeline_signal.status must be 紧急/近期/长期/不明确")

    for idx, item in enumerate(require_array(obj["next_actions"], "next_actions")):
        action = require_object(item, f"next_actions[{idx}]")
        require_str_field(action, "owner", f"next_actions[{idx}]")
        require_str_field(action, "action", f"next_actions[{idx}]")
        require_str_field(action, "priority", f"next_actions[{idx}]")
        if action["owner"] not in OWNERS:
            fail(f"next_actions[{idx}].owner must be one of {', '.join(sorted(OWNERS))}")
        if action["priority"] not in PRIORITIES:
            fail(f"next_actions[{idx}].priority must be high/medium/low")

    print("OK: business signal output is valid")


if __name__ == "__main__":
    main()
