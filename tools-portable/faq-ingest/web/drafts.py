from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FIELD_ORDER = [
    "台账ID",
    "批次",
    "状态",
    "入库状态",
    "来源",
    "归属文件",
    "建议ID",
    "疑似重复",
    "脱敏复扫",
    "证据片段",
    "问题",
    "回答",
    "适用功能",
    "关键词",
    "是否需要转人工",
]

MULTILINE_FIELDS = {"回答", "证据片段"}
FIELD_PATTERN = re.compile(rf"^({'|'.join(re.escape(name) for name in FIELD_ORDER)})[：:](.*)$")
BLOCK_SPLIT_PATTERN = re.compile(r"(?m)(?=^###\s+DRAFT-)")
TITLE_PATTERN = re.compile(r"^###\s+(.+?)\s*$")


@dataclass
class DraftParseError(ValueError):
    message: str

    def __str__(self) -> str:
        return self.message


def empty_card(seq: str = "DRAFT-YYYY-MM-DD-001") -> dict[str, str]:
    card = {"id_title": seq}
    for field in FIELD_ORDER:
        card[field] = ""
    return card


def parse_markdown(markdown: str) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []
    for raw_block in BLOCK_SPLIT_PATTERN.split(markdown.replace("\r\n", "\n")):
        block = raw_block.strip("\n")
        if not block.strip():
            continue
        if not block.lstrip().startswith("### DRAFT-"):
            continue
        cards.append(parse_block(block))
    return cards


def parse_block(block: str) -> dict[str, str]:
    lines = block.split("\n")
    if not lines:
        raise DraftParseError("empty draft block")

    title_match = TITLE_PATTERN.match(lines[0])
    if not title_match:
        raise DraftParseError("draft block must start with ### DRAFT-...")

    card = empty_card(title_match.group(1))
    current_field: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_field, current_lines
        if current_field is not None:
            card[current_field] = "\n".join(current_lines).strip()
        current_field = None
        current_lines = []

    for line in lines[1:]:
        match = FIELD_PATTERN.match(line)
        if match:
            flush()
            current_field = match.group(1)
            current_lines = [match.group(2).strip()]
            continue
        if current_field in MULTILINE_FIELDS:
            current_lines.append(line)
    flush()
    return card


def serialize_cards(cards: list[dict[str, Any]]) -> str:
    blocks = [serialize_card(card) for card in cards]
    return "\n\n".join(blocks).rstrip() + ("\n" if blocks else "")


def serialize_card(card: dict[str, Any]) -> str:
    title = str(card.get("id_title") or "").strip()
    if not title.startswith("DRAFT-"):
        raise DraftParseError(f"invalid draft title: {title!r}")

    lines = [f"### {title}"]
    for field in FIELD_ORDER:
        value = str(card.get(field, "") or "").strip()
        if "\n" in value:
            first, rest = value.split("\n", 1)
            lines.append(f"{field}：{first}")
            lines.append(rest.rstrip())
        else:
            lines.append(f"{field}：{value}")
        if field == "证据片段":
            lines.append("")
    return "\n".join(lines).rstrip()


def validate_round_trip(cards: list[dict[str, Any]]) -> None:
    reparsed = parse_markdown(serialize_cards(cards))
    normalized = parse_markdown(serialize_cards(reparsed))
    if reparsed != normalized:
        raise DraftParseError("draft parse/serialize round trip is not stable")


def read_cards(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return parse_markdown(path.read_text(encoding="utf-8-sig"))


def write_cards(path: Path, cards: list[dict[str, Any]]) -> None:
    validate_round_trip(cards)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialize_cards(cards), encoding="utf-8")


def _sample_cards() -> list[dict[str, str]]:
    return [
        {
            "id_title": "DRAFT-2026-06-05-001",
            "台账ID": "",
            "批次": "RUN-20260605-143207",
            "状态": "待审",
            "入库状态": "",
            "来源": "截图 fake.png",
            "归属文件": "09_高频_FAQ.md",
            "建议ID": "TODO-ID",
            "疑似重复": "无",
            "脱敏复扫": "通过",
            "证据片段": "用户问“能不能换衣服”\n客服答“可以，先上传图片”",
            "问题": "AI改款能不能换衣服？",
            "回答": "可以。\n先上传模特图和服装图，再写清保留项。",
            "适用功能": "AI改款",
            "关键词": "AI改款，换衣服",
            "是否需要转人工": "否",
        }
    ]


def self_test() -> None:
    cards = _sample_cards()
    validate_round_trip(cards)
    text = serialize_cards(cards)
    reparsed = parse_markdown(text)
    assert reparsed[0]["回答"].startswith("可以。")
    assert reparsed[0]["证据片段"].startswith("用户问")

    with_separator = text.rstrip() + "\n---\n\n"
    reparsed_with_separator = parse_markdown(with_separator)
    assert reparsed_with_separator[0]["回答"].startswith("可以。")
    assert reparsed_with_separator[0]["回答"] != "---"


if __name__ == "__main__":
    self_test()
    print("drafts.py self-test passed")
