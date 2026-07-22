from __future__ import annotations

import json
import re
import secrets
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


LEDGER_FIELDS = [
    "台账ID",
    "建议ID",
    "草稿日期",
    "批次",
    "问题",
    "回答",
    "适用功能",
    "归属文件",
    "状态",
    "入库状态",
    "入库时间",
    "来源",
    "疑似重复",
    "关键词",
    "是否需要转人工",
    "更新时间",
]


def gen_id() -> str:
    return f"LED-{secrets.token_hex(4)}"


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


class Ledger:
    def __init__(self, path: Path):
        self.path = path

    def append(self, record: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        normalized = {field: str(record.get(field, "") or "") for field in LEDGER_FIELDS}
        if not normalized["台账ID"]:
            normalized["台账ID"] = gen_id()
        if not normalized["更新时间"]:
            normalized["更新时间"] = now_text()
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(normalized, ensure_ascii=False, separators=(",", ":")) + "\n")

    def upsert(self, records: list[dict[str, Any]]) -> None:
        for record in records:
            self.append(record)

    def load(self, include_withdrawn: bool = True) -> list[dict[str, str]]:
        latest: dict[str, dict[str, str]] = {}
        for record in self._iter_records():
            ledger_id = record.get("台账ID", "")
            if not ledger_id:
                continue
            latest[ledger_id] = record
        rows = list(latest.values())
        if not include_withdrawn:
            rows = [row for row in rows if row.get("状态") != "已撤回"]
        return sorted(rows, key=lambda row: row.get("更新时间", ""), reverse=True)

    def get(self, ledger_id: str) -> dict[str, str] | None:
        for row in self.load(include_withdrawn=True):
            if row.get("台账ID") == ledger_id:
                return row
        return None

    def sync_cards(self, draft_date: str, cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
        updates: list[dict[str, str]] = []
        current_ids = {
            str(card.get("台账ID") or "").strip()
            for card in cards
            if str(card.get("台账ID") or "").strip()
        }
        for row in self.load(include_withdrawn=True):
            ledger_id = row.get("台账ID", "")
            if row.get("草稿日期") != draft_date:
                continue
            if not ledger_id or ledger_id in current_ids:
                continue
            if row.get("状态") == "已撤回" or row.get("入库状态") == "已入库":
                continue
            row["状态"] = "已撤回"
            row["更新时间"] = now_text()
            updates.append(row)

        for card in cards:
            ledger_id = str(card.get("台账ID") or "").strip()
            status = str(card.get("状态") or "").strip()
            if status == "通过":
                if not ledger_id:
                    ledger_id = gen_id()
                    card["台账ID"] = ledger_id
                if not str(card.get("入库状态") or "").strip():
                    card["入库状态"] = "待入库"
                updates.append(card_to_record(draft_date, card))
            elif ledger_id:
                record = card_to_record(draft_date, card)
                record["状态"] = "已撤回"
                updates.append(record)
        self.upsert(updates)
        return cards

    def mark_committed(self, ledger_id: str, commit_time: str | None = None) -> dict[str, str]:
        row = self.get(ledger_id)
        if row is None:
            raise KeyError(f"台账记录不存在：{ledger_id}")
        stamp = commit_time or now_text()
        row["入库状态"] = "已入库"
        row["入库时间"] = stamp
        row["更新时间"] = stamp
        self.append(row)
        return row

    def stats(self, rows: list[dict[str, str]]) -> dict[str, Any]:
        active = [row for row in rows if row.get("状态") != "已撤回"]
        week_start = datetime.now() - timedelta(days=7)
        recent = [
            row
            for row in active
            if _parse_time(row.get("更新时间") or row.get("草稿日期")) >= week_start
        ]
        by_function = Counter(row.get("适用功能") or "未填写" for row in active)
        duplicate_top = Counter(
            row.get("疑似重复")
            for row in active
            if row.get("疑似重复") and row.get("疑似重复") != "无"
        )
        handoff_count = sum(1 for row in active if row.get("是否需要转人工") == "是")
        return {
            "近7天通过数": len(recent),
            "待入库数": sum(1 for row in active if row.get("入库状态") != "已入库"),
            "按功能分布": by_function.most_common(10),
            "转人工占比": round(handoff_count / len(active), 4) if active else 0,
            "疑似重复top": duplicate_top.most_common(10),
        }

    def _iter_records(self) -> list[dict[str, str]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, str]] = []
        for line in self.path.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            rows.append({field: str(raw.get(field, "") or "") for field in LEDGER_FIELDS})
        return rows


def card_to_record(draft_date: str, card: dict[str, Any]) -> dict[str, str]:
    commit_state = str(card.get("入库状态") or "待入库")
    commit_time = str(card.get("入库时间") or "")
    committed_match = commit_state.strip().startswith("已入库")
    if committed_match:
        match = re.search(r"\(([^)]+)\)", commit_state)
        commit_time = commit_time or (match.group(1) if match else "")
        commit_state = "已入库"
    return {
        "台账ID": str(card.get("台账ID") or ""),
        "建议ID": str(card.get("建议ID") or ""),
        "草稿日期": draft_date,
        "批次": str(card.get("批次") or ""),
        "问题": str(card.get("问题") or ""),
        "回答": str(card.get("回答") or ""),
        "适用功能": str(card.get("适用功能") or ""),
        "归属文件": str(card.get("归属文件") or ""),
        "状态": str(card.get("状态") or ""),
        "入库状态": commit_state,
        "入库时间": commit_time,
        "来源": str(card.get("来源") or ""),
        "疑似重复": str(card.get("疑似重复") or ""),
        "关键词": str(card.get("关键词") or ""),
        "是否需要转人工": str(card.get("是否需要转人工") or ""),
        "更新时间": now_text(),
    }


def _parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.min
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value[:16] if fmt.endswith("%M") else value[:10], fmt)
        except ValueError:
            continue
    return datetime.min
