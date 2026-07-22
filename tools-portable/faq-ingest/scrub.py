#!/usr/bin/env python
"""Local redaction and sensitive-content scanning for FAQ screenshot ingest."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


RULES: list[tuple[str, re.Pattern[str], str]] = [
    ("手机号", re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"), "[手机号]"),
    ("邮箱", re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"), "[邮箱]"),
    ("微信", re.compile(r"(?i)(?:微信|vx|wx|wechat)\s*[:：]?\s*[A-Za-z][A-Za-z0-9_-]{4,19}"), "[微信]"),
    ("QQ", re.compile(r"(?i)\bqq\s*[:：]?\s*[1-9]\d{4,10}\b"), "[QQ]"),
    ("身份证", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "[身份证]"),
    ("链接", re.compile(r"(?i)https?://[^\s，。；;、）)]+"), "[链接]"),
    ("编号", re.compile(r"(?<!\d)\d{8,}(?!\d)"), "[编号]"),
]


def load_terms(paths: list[Path]) -> list[tuple[str, str]]:
    terms: list[tuple[str, str]] = []
    for path in paths:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            value = raw.strip()
            if not value or value.startswith("#"):
                continue
            label = "公司" if any(x in value for x in ("公司", "科技", "服饰", "集团")) else "群名"
            terms.append((value, f"[{label}]"))
    terms.sort(key=lambda item: len(item[0]), reverse=True)
    return terms


def scrub_text(text: str, terms: list[tuple[str, str]]) -> str:
    result = text
    for _name, pattern, replacement in RULES:
        result = pattern.sub(replacement, result)
    for term, replacement in terms:
        result = result.replace(term, replacement)
    return result


def scan_text(text: str, terms: list[tuple[str, str]], source: str = "") -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for name, pattern, _replacement in RULES:
            for match in pattern.finditer(line):
                hits.append(
                    {
                        "type": name,
                        "line": line_no,
                        "start": match.start() + 1,
                        "end": match.end(),
                        "source": source,
                    }
                )
        for term, replacement in terms:
            col = line.find(term)
            if col >= 0:
                hits.append(
                    {
                        "type": replacement.strip("[]"),
                        "line": line_no,
                        "start": col + 1,
                        "end": col + len(term),
                        "source": source,
                    }
                )
    return hits


def scrub_json(value: Any, terms: list[tuple[str, str]]) -> Any:
    if isinstance(value, str):
        return scrub_text(value, terms)
    if isinstance(value, list):
        return [scrub_json(item, terms) for item in value]
    if isinstance(value, dict):
        return {key: scrub_json(item, terms) for key, item in value.items()}
    return value


def read_input(path: Path | None) -> str:
    if path is None or str(path) == "-":
        return sys.stdin.read()
    return path.read_text(encoding="utf-8-sig")


def run_pre(args: argparse.Namespace, terms: list[tuple[str, str]]) -> int:
    raw = read_input(args.input)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        sys.stdout.write(scrub_text(raw, terms))
        return 0
    json.dump(scrub_json(data, terms), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def run_scan(args: argparse.Namespace, terms: list[tuple[str, str]]) -> int:
    raw = read_input(args.input)
    hits = scan_text(raw, terms, source=str(args.input or "stdin"))
    json.dump({"ok": not hits, "hits": hits}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 1 if hits and args.fail_on_hit else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Redact or scan screenshot FAQ ingest text.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--pre", action="store_true", help="replace sensitive content")
    mode.add_argument("--scan", action="store_true", help="scan only and emit JSON")
    parser.add_argument("input", nargs="?", type=Path, help="input file, or stdin when omitted")
    parser.add_argument("--terms", action="append", type=Path, default=[], help="known group/company names file")
    parser.add_argument("--fail-on-hit", action="store_true", help="return non-zero when scan finds hits")
    args = parser.parse_args()

    terms = load_terms(args.terms)
    if args.pre:
        return run_pre(args, terms)
    return run_scan(args, terms)


if __name__ == "__main__":
    raise SystemExit(main())
