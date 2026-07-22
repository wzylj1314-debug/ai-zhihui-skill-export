from __future__ import annotations

import re
import shutil
import subprocess
from collections import Counter
from datetime import date, datetime, timedelta
from functools import lru_cache
import json
import os
from pathlib import Path
from shutil import which
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from commit import FAQ_TARGET_FILES, commit_many
from drafts import DraftParseError, read_cards, validate_round_trip, write_cards
from idspace import ledger_conflicts, next_free, occupied_numbers, parse_formal_id
from ledger import Ledger
from pipeline import JobRunner


def _preload_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


WEB_DIR = Path(__file__).resolve().parent
FAQ_DIR = WEB_DIR.parent
_preload_env_file(FAQ_DIR.parent / ".env")
_preload_env_file(FAQ_DIR / ".env")
PORTABLE_ROOT = Path(os.getenv("ZHIHUI_PORTABLE_ROOT", str(FAQ_DIR.parent))).resolve()
EXPORT_ROOT = Path(os.getenv("ZHIHUI_EXPORT_ROOT", str(PORTABLE_ROOT.parent))).resolve()
RUNTIME_DIR = Path(os.getenv("ZHIHUI_RUNTIME_DIR", str(EXPORT_ROOT / "runtime"))).resolve()
ROOT = PORTABLE_ROOT
INBOX_DIR = Path(os.getenv("ZHIHUI_INBOX_DIR", str(RUNTIME_DIR / "workspace" / "inbox"))).resolve()
SCREENSHOT_DIR = INBOX_DIR / "screenshots"
DRAFT_DIR = INBOX_DIR / "faq-drafts"
LEDGER_FILE = INBOX_DIR / "faq-ledger.jsonl"
KB_DIR = Path(os.getenv("ZHIHUI_KB_DIR", str(RUNTIME_DIR / "workspace" / "v1_0_3"))).resolve()
SCRUB = FAQ_DIR / "scrub.py"
TERMS = FAQ_DIR / "known-sensitive-terms.txt"
ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
FUNCTION_MAP = FAQ_DIR / "function-map.json"


app = FastAPI(title="FAQ Screenshot Workbench")
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
runner = JobRunner(ROOT, script=FAQ_DIR / "faq-ingest.ps1")
ledger = Ledger(LEDGER_FILE)


class DraftPayload(BaseModel):
    cards: list[dict[str, Any]]


class ScanPayload(BaseModel):
    text: str


class CommitPayload(BaseModel):
    ids: list[str]


class DeletePayload(BaseModel):
    ids: list[str]


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _with_portable_links((WEB_DIR / "templates" / "index.html").read_text(encoding="utf-8"))


@app.get("/board", response_class=HTMLResponse)
def board() -> str:
    return _with_portable_links((WEB_DIR / "templates" / "board.html").read_text(encoding="utf-8"))


@app.post("/api/upload")
async def upload(files: list[UploadFile] = File(...)) -> dict[str, Any]:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for item in files:
        suffix = Path(item.filename or "").suffix.lower()
        if suffix not in ALLOWED_EXTS:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {item.filename}")
        safe_name = _safe_filename(Path(item.filename or f"upload{suffix}").name)
        target = _dedupe_path(SCREENSHOT_DIR / safe_name)
        target.write_bytes(await item.read())
        saved.append(target.name)
    return {"files": saved}


@app.post("/api/process")
def process(force_ocr: bool = False) -> dict[str, str]:
    job = runner.start(force_ocr=force_ocr)
    return {"job_id": job.id}


@app.get("/api/process/{job_id}")
def process_status(job_id: str) -> dict[str, Any]:
    job = runner.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job.to_dict()


@app.get("/api/drafts")
def drafts(
    date_query: str | None = Query(default=None, alias="date"),
    date_value: str | None = None,
    batch: str | None = None,
) -> dict[str, Any]:
    draft_date = date_query or date_value or date.today().isoformat()
    path = _draft_path(draft_date)
    try:
        all_cards = read_cards(path)
    except DraftParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    batches = sorted({card.get("批次", "") for card in all_cards if card.get("批次")}, reverse=True)
    cards = [card for card in all_cards if card.get("批次") == batch] if batch else all_cards
    return {"date": draft_date, "cards": cards, "batches": batches, "exists": path.exists(), "batch": batch or ""}


@app.put("/api/drafts/{date_value}")
def save_drafts(date_value: str, payload: DraftPayload) -> dict[str, Any]:
    try:
        validate_round_trip(payload.cards)
        _validate_formal_id_uniqueness(payload.cards)
        cards = ledger.sync_cards(date_value, payload.cards)
        write_cards(_draft_path(date_value), cards)
    except DraftParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "date": date_value, "cards": cards}


@app.post("/api/drafts/{date_value}/clear")
def clear_drafts(date_value: str) -> dict[str, Any]:
    path = _draft_path(date_value)
    if path.exists() and path.stat().st_size > 0:
        trash = DRAFT_DIR / "_trash"
        trash.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path.replace(trash / f"{date_value}-{stamp}.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    return {"ok": True, "date": date_value}


@app.get("/api/drafts/{date_value}/download")
def download_draft(date_value: str) -> FileResponse:
    path = _draft_path(date_value)
    if not path.exists():
        raise HTTPException(status_code=404, detail="draft not found")
    return FileResponse(path, filename=path.name, media_type="text/markdown")


@app.post("/api/scan")
def scan(payload: ScanPayload) -> dict[str, Any]:
    py = _python()
    cmd = [py, str(SCRUB), "--scan", "-"]
    if TERMS.exists():
        cmd += ["--terms", str(TERMS)]
    proc = subprocess.run(
        cmd,
        input=payload.text,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode not in (0, 1):
        raise HTTPException(status_code=500, detail=(proc.stderr or proc.stdout))
    import json

    return json.loads(proc.stdout)


@app.get("/api/allowed-files")
def allowed_files() -> dict[str, list[str]]:
    existing = {path.name for path in KB_DIR.glob("*.md")}
    return {"files": [name for name in FAQ_TARGET_FILES if name in existing]}


@app.get("/api/board")
def board_data(
    from_date: str | None = Query(default=None, alias="from"),
    to_date: str | None = Query(default=None, alias="to"),
    function: str | None = None,
    file: str | None = None,
    commit_state: str | None = None,
    q: str | None = None,
) -> dict[str, Any]:
    rows = ledger.load(include_withdrawn=(commit_state == "全部"))
    rows = _filter_board_rows(rows, from_date, to_date, function, file, commit_state, q)
    return {"rows": rows, "stats": _board_stats(rows), "allowed_files": allowed_files()["files"]}


@app.post("/api/board/commit")
def board_commit(payload: CommitPayload) -> dict[str, Any]:
    if not payload.ids:
        raise HTTPException(status_code=400, detail="ids is required")
    return {"results": commit_many(ROOT, payload.ids)}


@app.post("/api/board/delete")
def board_delete(payload: DeletePayload) -> dict[str, Any]:
    if not payload.ids:
        raise HTTPException(status_code=400, detail="ids is required")

    results: list[dict[str, Any]] = []
    delete_ids: list[str] = []
    for ledger_id in payload.ids:
        row = ledger.get(ledger_id)
        if row is None:
            results.append({"id": ledger_id, "ok": False, "reason": "台账记录不存在"})
            continue
        if row.get("入库状态") == "已入库":
            results.append({"id": ledger_id, "ok": False, "reason": "已入库记录不能永久删除"})
            continue
        delete_ids.append(ledger_id)

    backup_dir = ""
    if delete_ids:
        backup_dir = str(_backup_delete_targets(delete_ids))
        _delete_ledger_history(delete_ids)
        removed_cards = _delete_draft_cards(delete_ids)
        for ledger_id in delete_ids:
            results.append(
                {
                    "id": ledger_id,
                    "ok": True,
                    "reason": "已永久删除",
                    "removed_cards": removed_cards.get(ledger_id, 0),
                }
            )
    return {"results": results, "backup": backup_dir}


@app.get("/api/next-id")
def next_id(file: str, prefix: str = "FAQ", feature: str = "") -> dict[str, str]:
    allowed = allowed_files()["files"]
    if file not in allowed:
        raise HTTPException(status_code=400, detail="file is not in allowed list")
    prefix = prefix.upper()
    if prefix not in {"FAQ", "UQ"}:
        raise HTTPException(status_code=400, detail="prefix must be FAQ or UQ")
    feature_code, reason = _resolve_feature_code(feature)
    if not feature_code:
        return {"suggestion": "TODO-ID", "reason": reason or "无法从适用功能映射到功能号"}
    if not re.match(r"^F\d{2}$", feature_code):
        return {"suggestion": "TODO-ID", "reason": f"unsupported feature code: {feature_code}"}
    numbers = occupied_numbers(KB_DIR / file, ledger, prefix, feature_code)
    numbers |= _draft_numbers(prefix, feature_code)
    return {
        "suggestion": next_free(prefix, feature_code, numbers),
        "feature_code": feature_code,
        "reason": reason,
    }


def _validate_formal_id_uniqueness(cards: list[dict[str, Any]]) -> None:
    seen: dict[str, str] = {}
    for card in cards:
        item_id = str(card.get("建议ID") or "").strip()
        if not parse_formal_id(item_id):
            continue
        title = str(card.get("id_title") or "")
        if item_id in seen:
            raise DraftParseError(f"正式ID重复：{item_id}（{seen[item_id]} / {title}）")
        seen[item_id] = title

    for card in cards:
        item_id = str(card.get("建议ID") or "").strip()
        if not parse_formal_id(item_id):
            continue
        ledger_id = str(card.get("台账ID") or "").strip()
        conflicts = ledger_conflicts(ledger, item_id, exclude_ledger_id=ledger_id)
        if conflicts:
            conflict = conflicts[0]
            raise DraftParseError(
                f"正式ID已被台账其他记录占用：{item_id}（台账ID {conflict.get('台账ID', '')}）"
            )


def _draft_numbers(prefix: str, feature_code: str) -> set[int]:
    numbers: set[int] = set()
    for path in DRAFT_DIR.glob("*.md"):
        try:
            cards = read_cards(path)
        except DraftParseError:
            continue
        for card in cards:
            parsed = parse_formal_id(str(card.get("建议ID") or ""))
            if parsed and parsed.prefix == prefix and parsed.feature == feature_code:
                numbers.add(parsed.number)
    return numbers


def _backup_delete_targets(delete_ids: list[str]) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = DRAFT_DIR / "_trash" / f"delete-{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    if LEDGER_FILE.exists():
        shutil.copy2(LEDGER_FILE, backup_dir / LEDGER_FILE.name)
    for path in _draft_paths_with_ledger_ids(set(delete_ids)):
        shutil.copy2(path, backup_dir / path.name)
    return backup_dir


def _delete_ledger_history(delete_ids: list[str]) -> None:
    delete_set = set(delete_ids)
    if not LEDGER_FILE.exists():
        return
    kept: list[str] = []
    for line in LEDGER_FILE.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            kept.append(line)
            continue
        if str(raw.get("台账ID") or "") in delete_set:
            continue
        kept.append(line)
    LEDGER_FILE.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")


def _delete_draft_cards(delete_ids: list[str]) -> dict[str, int]:
    delete_set = set(delete_ids)
    removed: dict[str, int] = {ledger_id: 0 for ledger_id in delete_ids}
    for path in sorted(DRAFT_DIR.glob("*.md")):
        try:
            cards = read_cards(path)
        except DraftParseError:
            continue
        next_cards: list[dict[str, Any]] = []
        changed = False
        for card in cards:
            ledger_id = str(card.get("台账ID") or "")
            if ledger_id in delete_set:
                removed[ledger_id] = removed.get(ledger_id, 0) + 1
                changed = True
                continue
            next_cards.append(card)
        if changed:
            write_cards(path, next_cards)
    return removed


def _with_portable_links(html: str) -> str:
    host = os.getenv("ZHIHUI_TOOL_HOST", "127.0.0.1")
    hub_port = os.getenv("ZHIHUI_TOOL_HUB_PORT", "8900")
    faq_port = os.getenv("ZHIHUI_FAQ_PORT", "8899")
    conversation_port = os.getenv("ZHIHUI_CONVERSATION_PORT", "8910")
    return (
        html.replace("http://127.0.0.1:8900", f"http://{host}:{hub_port}")
        .replace("http://127.0.0.1:8899", f"http://{host}:{faq_port}")
        .replace("http://127.0.0.1:8910", f"http://{host}:{conversation_port}")
    )


def _draft_paths_with_ledger_ids(ledger_ids: set[str]) -> list[Path]:
    paths: list[Path] = []
    for path in sorted(DRAFT_DIR.glob("*.md")):
        try:
            cards = read_cards(path)
        except DraftParseError:
            continue
        if any(str(card.get("台账ID") or "") in ledger_ids for card in cards):
            paths.append(path)
    return paths


@lru_cache(maxsize=1)
def _feature_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for path in KB_DIR.glob("03_*.md"):
        text = path.read_text(encoding="utf-8-sig")
        for match in re.finditer(r"编号：((?:F|T)\d+)\s*[\r\n]+\s*-\s*(?:功能名称|能力名称)：([^\r\n]+)", text):
            code = match.group(1).strip()
            name = match.group(2).strip()
            mapping[name] = code
    if FUNCTION_MAP.exists():
        mapping.update(json.loads(FUNCTION_MAP.read_text(encoding="utf-8-sig")))
    return mapping


@lru_cache(maxsize=1)
def _canonical_features() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for path in KB_DIR.glob("03_*.md"):
        text = path.read_text(encoding="utf-8-sig")
        for match in re.finditer(r"编号：((?:F|T)\d+)\s*[\r\n]+\s*-\s*(?:功能名称|能力名称)：([^\r\n]+)", text):
            mapping[match.group(1).strip()] = match.group(2).strip()
    return mapping


def _resolve_feature_code(feature: str) -> tuple[str, str]:
    value = (feature or "").strip()
    if not value:
        return "", "适用功能为空，无法建议 ID"
    explicit = re.search(r"\b(F\d{2}|T\d{2})\b", value, re.IGNORECASE)
    if explicit:
        return explicit.group(1).upper(), "matched explicit feature code"

    mapping = _feature_map()
    parts = [part.strip() for part in re.split(r"[、，,;；\s]+", value) if part.strip()]
    for part in parts:
        cleaned = re.sub(r"^(?:F|T)\d{2}\s*", "", part, flags=re.IGNORECASE).strip()
        if cleaned in mapping:
            return mapping[cleaned], f"matched {cleaned}"
    for name, code in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
        if name and name in value:
            return code, f"matched {name}"
    return "", f"无法从适用功能“{value}”映射到功能号"


def _board_stats(rows: list[dict[str, str]]) -> dict[str, Any]:
    active = [row for row in rows if row.get("状态") != "已撤回"]
    week_start = datetime.now() - timedelta(days=7)
    recent = [
        row
        for row in active
        if _parse_time(row.get("更新时间") or row.get("草稿日期")) >= week_start
    ]
    by_function: Counter[str] = Counter()
    for row in active:
        features = _extract_real_features(row.get("适用功能", ""))
        if features:
            by_function.update(features)
        else:
            by_function.update(["未归类"])
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


def _extract_real_features(value: str) -> list[str]:
    text = (value or "").strip()
    if not text:
        return []
    canonical = _canonical_features()
    alias_to_code = _feature_map()
    found: list[str] = []

    for code in re.findall(r"\b(?:F|T)\d{2}\b", text, flags=re.IGNORECASE):
        name = canonical.get(code.upper())
        if name and name not in found:
            found.append(name)

    parts = [part.strip() for part in re.split(r"[、，,;；/\s]+", text) if part.strip()]
    for part in parts:
        cleaned = re.sub(r"^(?:F|T)\d{2}\s*", "", part, flags=re.IGNORECASE).strip()
        code = alias_to_code.get(cleaned)
        name = canonical.get(code or "")
        if name and name not in found:
            found.append(name)

    for code, name in sorted(canonical.items(), key=lambda item: len(item[1]), reverse=True):
        if name and name in text and name not in found:
            found.append(name)
    return found


def _parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.min
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        candidate = value[:16] if fmt.endswith("%M") else value[:10]
        try:
            return datetime.strptime(candidate, fmt)
        except ValueError:
            continue
    return datetime.min


def _filter_board_rows(
    rows: list[dict[str, str]],
    from_date: str | None,
    to_date: str | None,
    function: str | None,
    file: str | None,
    commit_state: str | None,
    q: str | None,
) -> list[dict[str, str]]:
    result = rows
    if from_date:
        result = [row for row in result if row.get("草稿日期", "") >= from_date]
    if to_date:
        result = [row for row in result if row.get("草稿日期", "") <= to_date]
    if function:
        result = [row for row in result if function in row.get("适用功能", "")]
    if file:
        result = [row for row in result if row.get("归属文件") == file]
    if commit_state and commit_state != "全部":
        if commit_state == "待入库":
            result = [row for row in result if row.get("入库状态") != "已入库"]
        elif commit_state == "已入库":
            result = [row for row in result if row.get("入库状态") == "已入库"]
    if q:
        needle = q.strip().lower()
        result = [
            row
            for row in result
            if needle in "\n".join(
                [
                    row.get("问题", ""),
                    row.get("回答", ""),
                    row.get("关键词", ""),
                    row.get("适用功能", ""),
                    row.get("建议ID", ""),
                ]
            ).lower()
        ]
    return result


def _draft_path(value: str) -> Path:
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", value) and value != "test-run":
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    return DRAFT_DIR / f"{value}.md"


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._\-\u4e00-\u9fff]+", "_", value).strip("._") or "upload.png"


def _dedupe_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    for index in range(1, 10000):
        candidate = path.with_name(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise HTTPException(status_code=500, detail="could not allocate upload filename")


def _python() -> str:
    venv = FAQ_DIR / "venv" / "Scripts" / "python.exe"
    if venv.exists():
        return str(venv)
    return which("python") or "python"
