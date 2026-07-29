#!/usr/bin/env python3
"""Validate zhihui-knowledge-capture-decision JSON output."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_FIELDS = [
    "capture_decision",
    "knowledge_type",
    "target_reference",
    "dedupe_result",
    "sensitivity_check",
    "quality_check",
    "draft",
    "review_required",
    "review_reason",
]

DECISIONS = {"入库", "暂存", "不入库", "转人工复核"}
TYPES = {"FAQ", "真实问法", "排障规则", "风险边界", "销售话术", "产品反馈"}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def require_object(value, name: str) -> dict:
    if not isinstance(value, dict):
        fail(f"{name} must be an object")
    return value


def require_str(obj: dict, field: str, context: str, allow_empty: bool = False) -> None:
    if field not in obj:
        fail(f"{context}.{field} is required")
    if not isinstance(obj[field], str):
        fail(f"{context}.{field} must be a string")
    if not allow_empty and not obj[field].strip():
        fail(f"{context}.{field} must not be empty")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: validate_knowledge_capture_output.py <output.json>")
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

    if obj["capture_decision"] not in DECISIONS:
        fail("capture_decision must be 入库/暂存/不入库/转人工复核")
    if obj["knowledge_type"] not in TYPES:
        fail("knowledge_type must be one of " + ", ".join(sorted(TYPES)))

    require_str(obj, "target_reference", "root", allow_empty=obj["capture_decision"] == "不入库")
    require_str(obj, "draft", "root", allow_empty=obj["capture_decision"] != "入库")
    require_str(obj, "review_reason", "root", allow_empty=True)

    dedupe = require_object(obj["dedupe_result"], "dedupe_result")
    if not isinstance(dedupe.get("is_duplicate"), bool):
        fail("dedupe_result.is_duplicate must be boolean")
    if not isinstance(dedupe.get("similar_items"), list):
        fail("dedupe_result.similar_items must be an array")

    sensitivity = require_object(obj["sensitivity_check"], "sensitivity_check")
    if not isinstance(sensitivity.get("has_sensitive_content"), bool):
        fail("sensitivity_check.has_sensitive_content must be boolean")
    if not isinstance(sensitivity.get("risk_types"), list):
        fail("sensitivity_check.risk_types must be an array")

    quality = require_object(obj["quality_check"], "quality_check")
    if not isinstance(quality.get("is_reusable"), bool):
        fail("quality_check.is_reusable must be boolean")
    require_str(quality, "reason", "quality_check")

    if not isinstance(obj["review_required"], bool):
        fail("review_required must be boolean")
    if obj["review_required"] and not obj["review_reason"].strip():
        fail("review_reason is required when review_required is true")

    print("OK: knowledge capture output is valid")


if __name__ == "__main__":
    main()
