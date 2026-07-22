from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, NamedTuple

from ledger import Ledger


FORMAL_ID_PATTERN = re.compile(r"^(FAQ|UQ)-(F\d{2})-(\d{3})$")


class FormalId(NamedTuple):
    prefix: str
    feature: str
    number: int


def parse_formal_id(value: str | None) -> FormalId | None:
    match = FORMAL_ID_PATTERN.match(str(value or "").strip())
    if not match:
        return None
    return FormalId(match.group(1), match.group(2), int(match.group(3)))


def kb_numbers(kb_file: Path, prefix: str, feature: str) -> set[int]:
    if not kb_file.exists():
        return set()
    text = kb_file.read_text(encoding="utf-8-sig")
    pattern = re.compile(rf"(?m)^###\s+{re.escape(prefix)}-{re.escape(feature)}-(\d+)[A-Z]?\s*$")
    return {int(match.group(1)) for match in pattern.finditer(text)}


def ledger_numbers(
    ledger: Ledger,
    prefix: str,
    feature: str,
    exclude_ledger_id: str = "",
) -> set[int]:
    return {
        parsed.number
        for row in active_ledger_rows(ledger)
        if row.get("台账ID") != exclude_ledger_id
        for parsed in [parse_formal_id(row.get("建议ID"))]
        if parsed and parsed.prefix == prefix and parsed.feature == feature
    }


def active_ledger_rows(ledger: Ledger) -> list[dict[str, str]]:
    return [row for row in ledger.load(include_withdrawn=True) if row.get("状态") != "已撤回"]


def ledger_conflicts(
    ledger: Ledger,
    formal_id: str,
    exclude_ledger_id: str = "",
) -> list[dict[str, str]]:
    if not parse_formal_id(formal_id):
        return []
    return [
        row
        for row in active_ledger_rows(ledger)
        if row.get("台账ID") != exclude_ledger_id and row.get("建议ID") == formal_id
    ]


def next_free(prefix: str, feature: str, used: Iterable[int]) -> str:
    occupied = set(used)
    number = 1
    while number in occupied:
        number += 1
    return f"{prefix}-{feature}-{number:03d}"


def occupied_numbers(kb_file: Path, ledger: Ledger, prefix: str, feature: str) -> set[int]:
    return kb_numbers(kb_file, prefix, feature) | ledger_numbers(ledger, prefix, feature)
