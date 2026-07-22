from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from shutil import which
from typing import Any

from drafts import read_cards, write_cards
from idspace import ledger_conflicts
from ledger import Ledger, now_text


FAQ_TARGET_FILES = ["09_高频_FAQ.md", "10_用户真实问法库.md"]
COMMIT_ID_PATTERN = re.compile(r"^(FAQ|UQ)-F\d{2}-\d{3}$")


def commit_many(root: Path, ids: list[str]) -> list[dict[str, Any]]:
    return [commit_one(root, ledger_id) for ledger_id in ids]


def commit_all_drafts(root: Path) -> list[dict[str, Any]]:
    inbox = _inbox_dir(root)
    draft_dir = inbox / "faq-drafts"
    ledger = Ledger(inbox / "faq-ledger.jsonl")
    results: list[dict[str, Any]] = []
    for path in sorted(draft_dir.glob("*.md")):
        draft_date = path.stem
        cards = read_cards(path)
        cards = ledger.sync_cards(draft_date, cards)
        write_cards(path, cards)
        for card in cards:
            if card.get("状态") != "通过":
                continue
            ledger_id = card.get("台账ID", "")
            if not ledger_id:
                continue
            if str(card.get("入库状态", "")).startswith("已入库"):
                results.append({"id": ledger_id, "ok": False, "reason": "该条已经入库"})
                continue
            results.append(commit_one(root, ledger_id))
    return results


def commit_one(root: Path, ledger_id: str) -> dict[str, Any]:
    inbox = _inbox_dir(root)
    kb_dir = _kb_dir(root)
    faq_dir = _faq_dir(root)
    ledger = Ledger(inbox / "faq-ledger.jsonl")
    record = ledger.get(ledger_id)
    if record is None:
        return _fail(ledger_id, "台账记录不存在")

    ok, reason = _check_gate(record, kb_dir, ledger)
    if not ok:
        return _fail(ledger_id, reason)

    target_path = kb_dir / record["归属文件"]
    if _id_exists(target_path, record["建议ID"]):
        return _fail(ledger_id, f"正式ID已存在：{record['建议ID']}")

    ok, reason = _scan_record(root, faq_dir, record)
    if not ok:
        return _fail(ledger_id, reason)

    block = _formal_block(record)
    with target_path.open("a", encoding="utf-8") as handle:
        handle.write("\n" + block + "\n")

    stamp = now_text()
    ledger.mark_committed(ledger_id, stamp)
    _mark_draft_committed(root, record, stamp)
    return {"id": ledger_id, "ok": True, "reason": "已入库", "target": record["归属文件"]}


def _check_gate(record: dict[str, str], kb_dir: Path, ledger: Ledger) -> tuple[bool, str]:
    if record.get("状态") != "通过":
        return False, "状态不是通过"
    if record.get("归属文件") not in FAQ_TARGET_FILES:
        return False, "不可一键入库：归属文件不在 FAQ 入库白名单，请先改为 09 或 10，或人工整理到专题文档。"
    if not (kb_dir / record["归属文件"]).exists():
        return False, "归属文件不存在"
    item_id = record.get("建议ID", "")
    if item_id == "TODO-ID" or not COMMIT_ID_PATTERN.match(item_id):
        return False, "正式ID未填写或格式不正确"
    if record["归属文件"].startswith("09_") and not item_id.startswith("FAQ-"):
        return False, "09_高频_FAQ.md 只能使用 FAQ- ID"
    if record["归属文件"].startswith("10_") and not item_id.startswith("UQ-"):
        return False, "10_用户真实问法库.md 只能使用 UQ- ID"
    if record.get("是否需要转人工") == "是":
        return False, "该条需要转人工"
    if record.get("入库状态") == "已入库":
        return False, "该条已经入库"
    conflicts = ledger_conflicts(ledger, item_id, exclude_ledger_id=record.get("台账ID", ""))
    if conflicts:
        return False, f"正式ID 已被台账其他记录占用：{item_id}（台账ID {conflicts[0].get('台账ID', '')}）"
    return True, ""


def _scan_record(root: Path, faq_dir: Path, record: dict[str, str]) -> tuple[bool, str]:
    text = "\n".join([record.get("问题", ""), record.get("回答", "")])
    cmd = [_python(faq_dir), str(faq_dir / "scrub.py"), "--scan", "-"]
    terms = faq_dir / "known-sensitive-terms.txt"
    if terms.exists():
        cmd += ["--terms", str(terms)]
    proc = subprocess.run(
        cmd,
        input=text,
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode not in (0, 1):
        return False, proc.stderr or proc.stdout or "脱敏复扫失败"
    data = json.loads(proc.stdout)
    if not data.get("ok"):
        return False, f"脱敏复扫命中 {len(data.get('hits', []))} 项"
    return True, ""


def _formal_block(record: dict[str, str]) -> str:
    item_id = record["建议ID"]
    if item_id.startswith("UQ-"):
        return "\n".join(
            [
                f"### {item_id}",
                f"标准意图：{record.get('问题', '')}",
                "用户真实问法：",
                f"- {record.get('问题', '')}",
                f"推荐功能：{record.get('适用功能', '')}",
                f"推荐回答方向：{record.get('回答', '')}",
                f"关键词：{record.get('关键词', '')}",
                f"是否需要转人工：{record.get('是否需要转人工', '')}",
            ]
        ).rstrip()
    return "\n".join(
        [
            f"### {item_id}",
            f"问题：{record.get('问题', '')}",
            f"回答：{record.get('回答', '')}",
            f"适用功能：{record.get('适用功能', '')}",
            f"关键词：{record.get('关键词', '')}",
            f"是否需要转人工：{record.get('是否需要转人工', '')}",
        ]
    ).rstrip()


def _id_exists(path: Path, item_id: str) -> bool:
    text = path.read_text(encoding="utf-8-sig")
    return re.search(rf"(?m)^###\s+{re.escape(item_id)}\s*$", text) is not None


def _mark_draft_committed(root: Path, record: dict[str, str], stamp: str) -> None:
    draft_date = record.get("草稿日期", "")
    ledger_id = record.get("台账ID", "")
    if not draft_date or not ledger_id:
        return
    path = _inbox_dir(root) / "faq-drafts" / f"{draft_date}.md"
    cards = read_cards(path)
    changed = False
    for card in cards:
        if card.get("台账ID") == ledger_id:
            card["入库状态"] = f"已入库 ({stamp})"
            changed = True
    if changed:
        write_cards(path, cards)


def _python(faq_dir: Path) -> str:
    venv = faq_dir / "venv" / "Scripts" / "python.exe"
    if venv.exists():
        return str(venv)
    return which("python") or "python"


def _runtime_dir(root: Path) -> Path:
    portable_root = Path(os.getenv("ZHIHUI_PORTABLE_ROOT", str(root))).resolve()
    export_root = Path(os.getenv("ZHIHUI_EXPORT_ROOT", str(portable_root.parent))).resolve()
    return Path(os.getenv("ZHIHUI_RUNTIME_DIR", str(export_root / "runtime"))).resolve()


def _inbox_dir(root: Path) -> Path:
    return Path(os.getenv("ZHIHUI_INBOX_DIR", str(_runtime_dir(root) / "workspace" / "inbox"))).resolve()


def _kb_dir(root: Path) -> Path:
    return Path(os.getenv("ZHIHUI_KB_DIR", str(_runtime_dir(root) / "workspace" / "v1_0_3"))).resolve()


def _faq_dir(root: Path) -> Path:
    portable_root = Path(os.getenv("ZHIHUI_PORTABLE_ROOT", str(root))).resolve()
    return Path(os.getenv("ZHIHUI_FAQ_TOOL_DIR", str(portable_root / "faq-ingest"))).resolve()


def _fail(ledger_id: str, reason: str) -> dict[str, Any]:
    return {"id": ledger_id, "ok": False, "reason": reason}


def main(argv: list[str]) -> int:
    root = Path(".").resolve()
    if "--root" in argv:
        index = argv.index("--root")
        if index + 1 >= len(argv):
            print("--root requires a value", file=sys.stderr)
            return 2
        root = Path(argv[index + 1]).resolve()
    results = commit_all_drafts(root)
    for item in results:
        status = "Committed" if item.get("ok") else "Skip"
        print(f"{status} {item.get('id')}: {item.get('reason')}")
    print("Commit finished. Run qmd embed/status manually if needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
