from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


FAQ_DIR = Path(__file__).resolve().parent
WEB_DIR = FAQ_DIR / "web"
sys.path.insert(0, str(WEB_DIR))

from drafts import read_cards, write_cards  # noqa: E402
from idspace import next_free, parse_formal_id  # noqa: E402
from ledger import Ledger, now_text  # noqa: E402


KB_HEADING_PATTERN = re.compile(r"(?m)^###\s+(FAQ|UQ)-(F\d{2})-(\d+)[A-Z]?\s*$")


@dataclass
class Unit:
    kind: str
    formal_id: str
    draft_path: Path | None
    draft_date: str
    title: str
    draft_seq: int
    ledger_id: str
    card: dict[str, Any] | None
    record: dict[str, str] | None
    committed: bool

    @property
    def label(self) -> str:
        if self.kind == "draft":
            return f"{self.draft_date} {self.title}"
        return f"ledger-only {self.ledger_id}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Repair duplicated FAQ/UQ formal IDs in drafts and ledger.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--dry-run", action="store_true", help="Only print planned changes.")
    args = parser.parse_args(argv)

    root = Path(os.getenv("ZHIHUI_PORTABLE_ROOT", args.root)).resolve()
    plan = build_plan(root)
    print_plan(plan, dry_run=args.dry_run)
    if args.dry_run:
        return 0
    apply_plan(root, plan)
    verify_no_duplicates(root)
    print("修复完成：草稿和台账有效记录正式ID重复数均为 0。")
    return 0


def build_plan(root: Path) -> dict[str, Any]:
    inbox = _inbox_dir(root)
    draft_dir = inbox / "faq-drafts"
    ledger = Ledger(inbox / "faq-ledger.jsonl")
    ledger_rows = {row.get("台账ID", ""): row for row in ledger.load(include_withdrawn=True)}
    draft_files: dict[Path, list[dict[str, Any]]] = {}
    draft_ledger_ids: set[str] = set()
    units_by_id: dict[str, list[Unit]] = defaultdict(list)

    for path in sorted(draft_dir.glob("*.md")):
        cards = read_cards(path)
        draft_files[path] = cards
        for card in cards:
            formal_id = str(card.get("建议ID") or "").strip()
            if not parse_formal_id(formal_id):
                continue
            ledger_id = str(card.get("台账ID") or "").strip()
            if ledger_id:
                draft_ledger_ids.add(ledger_id)
            record = ledger_rows.get(ledger_id)
            units_by_id[formal_id].append(
                Unit(
                    kind="draft",
                    formal_id=formal_id,
                    draft_path=path,
                    draft_date=path.stem,
                    title=str(card.get("id_title") or ""),
                    draft_seq=_draft_seq(str(card.get("id_title") or "")),
                    ledger_id=ledger_id,
                    card=card,
                    record=record,
                    committed=_is_committed(card, record),
                )
            )

    for ledger_id, row in ledger_rows.items():
        if not ledger_id or ledger_id in draft_ledger_ids or row.get("状态") == "已撤回":
            continue
        formal_id = str(row.get("建议ID") or "").strip()
        if not parse_formal_id(formal_id):
            continue
        units_by_id[formal_id].append(
            Unit(
                kind="ledger",
                formal_id=formal_id,
                draft_path=None,
                draft_date=str(row.get("草稿日期") or "9999-99-99"),
                title="",
                draft_seq=999999,
                ledger_id=ledger_id,
                card=None,
                record=row,
                committed=_is_committed(None, row),
            )
        )

    used = collect_used_numbers(root, draft_files, ledger_rows.values())
    changes: list[dict[str, Any]] = []
    locked_conflicts: list[str] = []

    for formal_id, units in sorted(units_by_id.items()):
        if len(units) < 2:
            continue
        committed_count = sum(1 for unit in units if unit.committed)
        if committed_count > 1:
            locked_conflicts.append(formal_id)
            continue
        keep = sorted(units, key=_keep_key)[0]
        parsed = parse_formal_id(formal_id)
        if not parsed:
            continue
        namespace = (parsed.prefix, parsed.feature)
        for unit in sorted(units, key=_keep_key):
            if unit is keep:
                continue
            new_id = next_free(parsed.prefix, parsed.feature, used[namespace])
            new_parsed = parse_formal_id(new_id)
            if not new_parsed:
                raise RuntimeError(f"invalid generated id: {new_id}")
            used[namespace].add(new_parsed.number)
            changes.append({"old_id": formal_id, "new_id": new_id, "keep": keep, "unit": unit})

    return {
        "root": root,
        "ledger": ledger,
        "ledger_rows": ledger_rows,
        "draft_files": draft_files,
        "changes": changes,
        "locked_conflicts": locked_conflicts,
    }


def collect_used_numbers(
    root: Path,
    draft_files: dict[Path, list[dict[str, Any]]],
    ledger_rows: Any,
) -> dict[tuple[str, str], set[int]]:
    used: dict[tuple[str, str], set[int]] = defaultdict(set)
    kb_dir = _kb_dir(root)
    for path in kb_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8-sig")
        for match in KB_HEADING_PATTERN.finditer(text):
            used[(match.group(1), match.group(2))].add(int(match.group(3)))
    for cards in draft_files.values():
        for card in cards:
            parsed = parse_formal_id(str(card.get("建议ID") or ""))
            if parsed:
                used[(parsed.prefix, parsed.feature)].add(parsed.number)
    for row in ledger_rows:
        if row.get("状态") == "已撤回":
            continue
        parsed = parse_formal_id(str(row.get("建议ID") or ""))
        if parsed:
            used[(parsed.prefix, parsed.feature)].add(parsed.number)
    return used


def print_plan(plan: dict[str, Any], dry_run: bool) -> None:
    changes = plan["changes"]
    locked_conflicts = plan["locked_conflicts"]
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"[{mode}] duplicated formal ID repair plan")
    if locked_conflicts:
        print("以下重复组存在多条已入库记录，无法自动改号：")
        for item in locked_conflicts:
            print(f"  - {item}")
    if not changes:
        print("未发现需要修复的重复正式ID。")
        return

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for change in changes:
        grouped[change["old_id"]].append(change)
    for old_id, items in grouped.items():
        keep = items[0]["keep"]
        print(f"{old_id} duplicate:")
        print(f"  keep   {keep.label} ({_commit_state_text(keep)})")
        for item in items:
            unit = item["unit"]
            targets = ["draft"] if unit.kind == "draft" else []
            if unit.ledger_id:
                targets.append(f"ledger {unit.ledger_id}")
            print(f"  change {unit.label} -> {item['new_id']} [{', '.join(targets) or 'no ledger'}]")

    draft_changes = sum(1 for item in changes if item["unit"].kind == "draft")
    ledger_changes = sum(1 for item in changes if item["unit"].ledger_id)
    print(f"合计：将修改 {draft_changes} 条草稿、追加 {ledger_changes} 条台账记录")


def apply_plan(root: Path, plan: dict[str, Any]) -> None:
    if plan["locked_conflicts"]:
        raise RuntimeError("存在多条已入库重复ID，已停止自动修复。")
    changes = plan["changes"]
    if not changes:
        return

    backup_dir = backup_files(root, plan)
    print(f"已备份到：{backup_dir}")

    ledger: Ledger = plan["ledger"]
    draft_files: dict[Path, list[dict[str, Any]]] = plan["draft_files"]
    ledger_rows: dict[str, dict[str, str]] = plan["ledger_rows"]
    touched_paths: set[Path] = set()

    for change in changes:
        unit: Unit = change["unit"]
        new_id = change["new_id"]
        if unit.card is not None:
            unit.card["建议ID"] = new_id
            if unit.draft_path:
                touched_paths.add(unit.draft_path)
        if unit.ledger_id and unit.ledger_id in ledger_rows:
            row = dict(ledger_rows[unit.ledger_id])
            if row.get("状态") != "已撤回":
                row["建议ID"] = new_id
                row["更新时间"] = now_text()
                ledger.append(row)

    for path in sorted(touched_paths):
        write_cards(path, draft_files[path])


def backup_files(root: Path, plan: dict[str, Any]) -> Path:
    inbox = _inbox_dir(root)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = inbox / "faq-drafts" / "_trash" / f"repair-{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    ledger_path = inbox / "faq-ledger.jsonl"
    if ledger_path.exists():
        shutil.copy2(ledger_path, backup_dir / ledger_path.name)

    changed_paths = {
        change["unit"].draft_path
        for change in plan["changes"]
        if change["unit"].draft_path is not None
    }
    for path in changed_paths:
        shutil.copy2(path, backup_dir / path.name)
    return backup_dir


def verify_no_duplicates(root: Path) -> None:
    report = duplicate_report(root)
    if report["draft_duplicates"] or report["ledger_duplicates"]:
        raise RuntimeError(f"修复后仍有重复：{report}")


def duplicate_report(root: Path) -> dict[str, dict[str, int]]:
    inbox = _inbox_dir(root)
    draft_dir = inbox / "faq-drafts"
    ledger = Ledger(inbox / "faq-ledger.jsonl")
    draft_counts: dict[str, int] = defaultdict(int)
    ledger_counts: dict[str, int] = defaultdict(int)
    for path in draft_dir.glob("*.md"):
        for card in read_cards(path):
            item_id = str(card.get("建议ID") or "")
            if parse_formal_id(item_id):
                draft_counts[item_id] += 1
    for row in ledger.load(include_withdrawn=True):
        if row.get("状态") == "已撤回":
            continue
        item_id = str(row.get("建议ID") or "")
        if parse_formal_id(item_id):
            ledger_counts[item_id] += 1
    return {
        "draft_duplicates": {key: value for key, value in draft_counts.items() if value > 1},
        "ledger_duplicates": {key: value for key, value in ledger_counts.items() if value > 1},
    }


def _is_committed(card: dict[str, Any] | None, record: dict[str, str] | None) -> bool:
    values = []
    if card:
        values.append(str(card.get("入库状态") or ""))
    if record:
        values.append(str(record.get("入库状态") or ""))
    return any(value.startswith("已入库") for value in values)


def _keep_key(unit: Unit) -> tuple[int, str, int, str]:
    return (0 if unit.committed else 1, unit.draft_date, unit.draft_seq, unit.ledger_id or unit.title)


def _draft_seq(title: str) -> int:
    match = re.search(r"-(\d+)$", title)
    return int(match.group(1)) if match else 999999


def _commit_state_text(unit: Unit) -> str:
    if unit.committed:
        return "已入库"
    value = ""
    if unit.card:
        value = str(unit.card.get("入库状态") or "")
    if not value and unit.record:
        value = str(unit.record.get("入库状态") or "")
    return value or "待入库"


def _runtime_dir(root: Path) -> Path:
    portable_root = Path(os.getenv("ZHIHUI_PORTABLE_ROOT", str(root))).resolve()
    export_root = Path(os.getenv("ZHIHUI_EXPORT_ROOT", str(portable_root.parent))).resolve()
    return Path(os.getenv("ZHIHUI_RUNTIME_DIR", str(export_root / "runtime"))).resolve()


def _inbox_dir(root: Path) -> Path:
    return Path(os.getenv("ZHIHUI_INBOX_DIR", str(_runtime_dir(root) / "workspace" / "inbox"))).resolve()


def _kb_dir(root: Path) -> Path:
    return Path(os.getenv("ZHIHUI_KB_DIR", str(_runtime_dir(root) / "workspace" / "v1_0_3"))).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
