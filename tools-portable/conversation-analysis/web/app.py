from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import sqlite3
import time
import urllib.parse
import urllib.request
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Literal
from xml.etree import ElementTree

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


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
APP_DIR = WEB_DIR.parent
_preload_env_file(APP_DIR.parent / ".env")
_preload_env_file(APP_DIR / ".env")
PORTABLE_ROOT = Path(os.getenv("ZHIHUI_PORTABLE_ROOT", str(APP_DIR.parent))).resolve()
EXPORT_ROOT = Path(os.getenv("ZHIHUI_EXPORT_ROOT", str(PORTABLE_ROOT.parent))).resolve()
RUNTIME_DIR = Path(os.getenv("ZHIHUI_RUNTIME_DIR", str(EXPORT_ROOT / "runtime"))).resolve()
ROOT = PORTABLE_ROOT
DATA_DIR = Path(os.getenv("ZHIHUI_CONVERSATION_DATA_DIR", str(RUNTIME_DIR / "data" / "conversation-analysis"))).resolve()
DB_PATH = DATA_DIR / "analysis.db"
PROMPT_PATH = DATA_DIR / "prompt.txt"
SUMMARY_PROMPT_PATH = DATA_DIR / "summary_prompt.txt"

DEFAULT_BASE_URL = "https://api.apiyi.com/v1"
DEFAULT_ENDPOINT_MODE = "chat"
DEFAULT_MODEL = "gpt-5-chat-latest"


app = FastAPI(title="Conversation Analysis Platform")
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")


class CreateAnalysisPayload(BaseModel):
    title: str = Field(default="")
    call_type: str = Field(default="")
    customer_name: str = Field(default="")
    sales_name: str = Field(default="")
    source_filename: str = Field(default="")
    raw_text: str


class UpdateAnalysisPayload(BaseModel):
    title: str = Field(default="")
    call_type: str = Field(default="")
    customer_name: str = Field(default="")
    sales_name: str = Field(default="")
    business_message: str = Field(default="")
    product_message: str = Field(default="")
    business_result: dict[str, Any]
    product_result: dict[str, Any]


class SendResult(BaseModel):
    ok: bool
    message: str


class PromptPayload(BaseModel):
    prompt: str


class SummaryRequestPayload(BaseModel):
    summary_date: str = Field(default="")


class UpdateSummaryPayload(BaseModel):
    business_summary: str = Field(default="")
    product_summary: str = Field(default="")


class BatchDeletePayload(BaseModel):
    ids: list[str] = Field(default_factory=list)


TEXT_EXTS = {".txt", ".text", ".md"}


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _with_portable_links((WEB_DIR / "templates" / "index.html").read_text(encoding="utf-8"))


@app.get("/api/config")
def config() -> dict[str, Any]:
    return {
        "has_openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "base_url": openai_base_url(),
        "endpoint_mode": os.getenv("OPENAI_ENDPOINT_MODE", DEFAULT_ENDPOINT_MODE),
        "model": os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        "has_business_channel": bool(os.getenv("DINGTALK_BUSINESS_WEBHOOK")),
        "has_product_channel": bool(os.getenv("DINGTALK_PRODUCT_WEBHOOK")),
    }


@app.get("/api/prompt")
def get_prompt() -> dict[str, str]:
    return {"prompt": build_prompt(), "default_prompt": default_prompt()}


@app.put("/api/prompt")
def update_prompt(payload: PromptPayload) -> dict[str, str]:
    prompt = payload.prompt.strip()
    if len(prompt) < 200:
        raise HTTPException(status_code=400, detail="提示词太短，可能会导致分析规则缺失。")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_PATH.write_text(prompt, encoding="utf-8")
    return {"prompt": prompt}


@app.get("/api/summary-prompt")
def get_summary_prompt() -> dict[str, str]:
    return {"prompt": build_summary_prompt(), "default_prompt": default_summary_prompt()}


@app.put("/api/summary-prompt")
def update_summary_prompt(payload: PromptPayload) -> dict[str, str]:
    prompt = payload.prompt.strip()
    if len(prompt) < 100:
        raise HTTPException(status_code=400, detail="汇总提示词太短，可能会导致汇总规则缺失。")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_PROMPT_PATH.write_text(prompt, encoding="utf-8")
    return {"prompt": prompt}


@app.post("/api/summary-prompt/reset")
def reset_summary_prompt() -> dict[str, str]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    prompt = default_summary_prompt()
    SUMMARY_PROMPT_PATH.write_text(prompt, encoding="utf-8")
    return {"prompt": prompt}


@app.post("/api/prompt/reset")
def reset_prompt() -> dict[str, str]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    prompt = default_prompt()
    PROMPT_PATH.write_text(prompt, encoding="utf-8")
    return {"prompt": prompt}


@app.post("/api/extract-files")
async def extract_files(files: list[UploadFile] = File(...)) -> dict[str, Any]:
    if not files:
        raise HTTPException(status_code=400, detail="请先选择文件。")
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="一次最多处理 20 个文件。")

    rows: list[dict[str, Any]] = []
    for item in files:
        filename = Path(item.filename or "未命名文件").name
        suffix = Path(filename).suffix.lower()
        try:
            content = await item.read()
            text = extract_file_text(filename, suffix, content)
            rows.append({"name": filename, "text": text, "error": ""})
        except Exception as exc:
            rows.append({"name": filename, "text": "", "error": str(exc)})
    return {"files": rows}


@app.get("/api/analyses")
def list_analyses(analysis_date: str = "") -> dict[str, Any]:
    target_date = analysis_date.strip()
    params: tuple[Any, ...] = ()
    where = ""
    if target_date:
        target_date = normalize_summary_date(target_date)
        where = "WHERE substr(created_at, 1, 10) = ?"
        params = (target_date,)
    with db() as conn:
        rows = conn.execute(
            f"""
            SELECT id, title, call_type, customer_name, sales_name,
                   business_opportunity, lead_level, sales_stage, product_fit,
                   confidence, business_sent_status, product_sent_status,
                   created_at, updated_at
              FROM analysis_records
             {where}
             ORDER BY created_at DESC
             LIMIT 100
            """,
            params,
        ).fetchall()
    return {"rows": [dict(row) for row in rows], "analysis_date": target_date}


@app.post("/api/analyses/batch-delete")
def batch_delete_analyses(payload: BatchDeletePayload) -> dict[str, int]:
    ids = [item.strip() for item in payload.ids if item.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="请先选择要删除的分析记录。")
    if len(ids) > 100:
        raise HTTPException(status_code=400, detail="一次最多删除 100 条记录。")
    placeholders = ",".join("?" for _ in ids)
    with db() as conn:
        cursor = conn.execute(f"DELETE FROM analysis_records WHERE id IN ({placeholders})", ids)
    return {"deleted": cursor.rowcount}


@app.get("/api/summaries")
def get_daily_summary(summary_date: str = "") -> dict[str, Any]:
    target_date = normalize_summary_date(summary_date)
    with db() as conn:
        summary = conn.execute(
            """
            SELECT * FROM daily_summaries
             WHERE summary_date = ?
             ORDER BY updated_at DESC
             LIMIT 1
            """,
            (target_date,),
        ).fetchone()
        records = fetch_analysis_rows_for_date(conn, target_date)
    return {
        "summary_date": target_date,
        "record_count": len(records),
        "summary": summary_to_payload(summary) if summary else None,
        "records": [summary_record_preview(row) for row in records],
    }


@app.post("/api/summaries/generate")
def generate_daily_summary(payload: SummaryRequestPayload) -> dict[str, Any]:
    target_date = normalize_summary_date(payload.summary_date)
    model_name = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    with db() as conn:
        records = fetch_analysis_rows_for_date(conn, target_date)
    if not records:
        raise HTTPException(status_code=400, detail="这一天没有可汇总的分析记录。")

    result, token_usage = summarize_with_gpt(target_date, records, model_name)
    summary_id = str(uuid.uuid4())
    now = now_text()
    source_ids = [row["id"] for row in records]
    with db() as conn:
        conn.execute(
            """
            INSERT INTO daily_summaries (
                id, summary_date, record_count, source_record_ids,
                business_summary, product_summary, model_name, token_usage,
                business_sent_status, product_sent_status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                summary_id,
                target_date,
                len(records),
                json.dumps(source_ids, ensure_ascii=False),
                result["business_summary"],
                result["product_summary"],
                model_name,
                json.dumps(token_usage, ensure_ascii=False),
                "未发送",
                "未发送",
                now,
                now,
            ),
        )
    return get_summary_record(summary_id)


@app.put("/api/summaries/{summary_id}")
def update_daily_summary(summary_id: str, payload: UpdateSummaryPayload) -> dict[str, Any]:
    get_summary_row(summary_id)
    now = now_text()
    with db() as conn:
        conn.execute(
            """
            UPDATE daily_summaries
               SET business_summary = ?,
                   product_summary = ?,
                   updated_at = ?
             WHERE id = ?
            """,
            (
                payload.business_summary.strip(),
                payload.product_summary.strip(),
                now,
                summary_id,
            ),
        )
    return get_summary_record(summary_id)


@app.get("/api/analyses/{analysis_id}")
def get_analysis(analysis_id: str) -> dict[str, Any]:
    row = get_record(analysis_id)
    return row_to_payload(row)


@app.post("/api/analyses")
def create_analysis(payload: CreateAnalysisPayload) -> dict[str, Any]:
    raw_text = payload.raw_text.strip()
    if len(raw_text) < 30:
        raise HTTPException(status_code=400, detail="请粘贴完整的销售与客户对话文本。")

    analysis_id = str(uuid.uuid4())
    now = now_text()
    title = payload.title.strip() or f"客户对话分析 {now[:16]}"
    prompt_version = "mvp-2026-07-20"
    model_name = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

    try:
        result, token_usage = analyze_with_gpt(payload, model_name)
        meta = normalize_meta(result.get("meta") or {}, payload, now)
        business = result["business"]
        product = result["product"]
    except Exception as exc:
        with db() as conn:
            conn.execute(
                """
                INSERT INTO analysis_records (
                    id, title, call_type, customer_name, sales_name, raw_text,
                    prompt_version, model_name, business_result_json,
                    product_result_json, business_message, product_message,
                    business_sent_status, product_sent_status, error_message,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    title,
                    payload.call_type.strip(),
                    payload.customer_name.strip(),
                    payload.sales_name.strip(),
                    raw_text,
                    prompt_version,
                    model_name,
                    "{}",
                    "{}",
                    "",
                    "",
                    "未发送",
                    "未发送",
                    str(exc),
                    now,
                    now,
                ),
            )
        raise HTTPException(status_code=502, detail=f"GPT 分析失败：{exc}") from exc

    title = meta["title"]
    final_payload = CreateAnalysisPayload(
        title=meta["title"],
        call_type=meta["call_type"],
        customer_name=meta["customer_name"],
        sales_name=meta["sales_name"],
        raw_text=raw_text,
    )
    business_message = render_business_message(title, final_payload, business)
    product_message = render_product_message(title, final_payload, product)
    summary = extract_summary_fields(business)

    with db() as conn:
        conn.execute(
            """
            INSERT INTO analysis_records (
                id, title, call_type, customer_name, sales_name, raw_text,
                prompt_version, model_name, business_result_json,
                product_result_json, business_message, product_message,
                business_opportunity, lead_level, sales_stage, product_fit,
                confidence, business_sent_status, product_sent_status,
                token_usage, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                analysis_id,
                title,
                final_payload.call_type,
                final_payload.customer_name,
                final_payload.sales_name,
                raw_text,
                prompt_version,
                model_name,
                json.dumps(business, ensure_ascii=False),
                json.dumps(product, ensure_ascii=False),
                business_message,
                product_message,
                summary["business_opportunity"],
                summary["lead_level"],
                summary["sales_stage"],
                summary["product_fit"],
                summary["confidence"],
                "未发送",
                "未发送",
                json.dumps(token_usage, ensure_ascii=False),
                now,
                now,
            ),
        )

    return get_analysis(analysis_id)


@app.put("/api/analyses/{analysis_id}")
def update_analysis(analysis_id: str, payload: UpdateAnalysisPayload) -> dict[str, Any]:
    row = get_record(analysis_id)
    meta = row_to_payload(row)
    title = payload.title.strip() or meta["title"]
    raw_update_meta = CreateAnalysisPayload(
        title=title,
        call_type=payload.call_type.strip() or meta["call_type"],
        customer_name=payload.customer_name.strip() or meta["customer_name"],
        sales_name=payload.sales_name.strip() or meta["sales_name"],
        raw_text=meta["raw_text"],
    )
    corrected_meta = normalize_meta(
        {
            "title": raw_update_meta.title,
            "call_type": raw_update_meta.call_type,
            "customer_name": raw_update_meta.customer_name,
            "sales_name": raw_update_meta.sales_name,
        },
        raw_update_meta,
        now_text(),
    )
    title = corrected_meta["title"]
    create_meta = CreateAnalysisPayload(
        title=corrected_meta["title"],
        call_type=corrected_meta["call_type"],
        customer_name=corrected_meta["customer_name"],
        sales_name=corrected_meta["sales_name"],
        raw_text=meta["raw_text"],
    )
    meta_changed = any(
        [
            raw_update_meta.call_type != create_meta.call_type,
            raw_update_meta.customer_name != create_meta.customer_name,
            raw_update_meta.sales_name != create_meta.sales_name,
        ]
    )
    business_message = (
        payload.business_message.strip()
        if payload.business_message.strip() and not meta_changed
        else render_business_message(title, create_meta, payload.business_result)
    )
    product_message = (
        payload.product_message.strip()
        if payload.product_message.strip() and not meta_changed
        else render_product_message(title, create_meta, payload.product_result)
    )
    summary = extract_summary_fields(payload.business_result)
    now = now_text()

    with db() as conn:
        conn.execute(
            """
            UPDATE analysis_records
               SET title = ?,
                   call_type = ?,
                   customer_name = ?,
                   sales_name = ?,
                   business_result_json = ?,
                   product_result_json = ?,
                   business_message = ?,
                   product_message = ?,
                   business_opportunity = ?,
                   lead_level = ?,
                   sales_stage = ?,
                   product_fit = ?,
                   confidence = ?,
                   updated_at = ?
             WHERE id = ?
            """,
            (
                title,
                create_meta.call_type,
                create_meta.customer_name,
                create_meta.sales_name,
                json.dumps(payload.business_result, ensure_ascii=False),
                json.dumps(payload.product_result, ensure_ascii=False),
                business_message,
                product_message,
                summary["business_opportunity"],
                summary["lead_level"],
                summary["sales_stage"],
                summary["product_fit"],
                summary["confidence"],
                now,
                analysis_id,
            ),
        )
    return get_analysis(analysis_id)


@app.delete("/api/analyses/{analysis_id}")
def delete_analysis(analysis_id: str) -> dict[str, bool]:
    get_record(analysis_id)
    with db() as conn:
        conn.execute("DELETE FROM analysis_records WHERE id = ?", (analysis_id,))
    return {"ok": True}


@app.post("/api/analyses/{analysis_id}/refresh-meta")
def refresh_meta(analysis_id: str) -> dict[str, Any]:
    row = get_record(analysis_id)
    meta = normalize_meta(
        {
            "title": row["title"],
            "call_type": row["call_type"],
            "customer_name": row["customer_name"],
            "sales_name": row["sales_name"],
        },
        CreateAnalysisPayload(title="", call_type="", customer_name="", sales_name="", raw_text=row["raw_text"]),
        now_text(),
    )
    create_meta = CreateAnalysisPayload(
        title=meta["title"],
        call_type=meta["call_type"],
        customer_name=meta["customer_name"],
        sales_name=meta["sales_name"],
        raw_text=row["raw_text"],
    )
    business = parse_json(row["business_result_json"], {})
    product = parse_json(row["product_result_json"], {})
    business_message = render_business_message(meta["title"], create_meta, business)
    product_message = render_product_message(meta["title"], create_meta, product)
    with db() as conn:
        conn.execute(
            """
            UPDATE analysis_records
               SET title = ?,
                   call_type = ?,
                   customer_name = ?,
                   sales_name = ?,
                   business_message = ?,
                   product_message = ?,
                   updated_at = ?
             WHERE id = ?
            """,
            (
                meta["title"],
                meta["call_type"],
                meta["customer_name"],
                meta["sales_name"],
                business_message,
                product_message,
                now_text(),
                analysis_id,
            ),
        )
    return get_analysis(analysis_id)


@app.post("/api/analyses/{analysis_id}/send/{channel}")
def send_analysis(analysis_id: str, channel: Literal["business", "product"]) -> SendResult:
    row = get_record(analysis_id)
    message = row["business_message"] if channel == "business" else row["product_message"]
    if not message.strip():
        raise HTTPException(status_code=400, detail="当前版本内容为空，不能发送。")

    webhook_key = "DINGTALK_BUSINESS_WEBHOOK" if channel == "business" else "DINGTALK_PRODUCT_WEBHOOK"
    secret_key = "DINGTALK_BUSINESS_SECRET" if channel == "business" else "DINGTALK_PRODUCT_SECRET"
    webhook = os.getenv(webhook_key, "").strip()
    secret = os.getenv(secret_key, "").strip()
    if not webhook:
        raise HTTPException(status_code=400, detail=f"未配置 {webhook_key}。")

    title = build_analysis_push_title(row, channel)
    push_message = build_analysis_push_message(row, channel, message)
    try:
        send_dingtalk_markdown(webhook, secret, title, push_message)
        status = "已发送"
        sent_at = now_text()
        error = ""
    except Exception as exc:
        status = "发送失败"
        sent_at = None
        error = str(exc)

    status_column = "business_sent_status" if channel == "business" else "product_sent_status"
    time_column = "business_sent_at" if channel == "business" else "product_sent_at"
    with db() as conn:
        conn.execute(
            f"""
            UPDATE analysis_records
               SET {status_column} = ?,
                   {time_column} = ?,
                   error_message = ?,
                   updated_at = ?
             WHERE id = ?
            """,
            (status, sent_at, error, now_text(), analysis_id),
        )

    if error:
        raise HTTPException(status_code=502, detail=f"钉钉发送失败：{error}")
    return SendResult(ok=True, message=status)


def build_analysis_push_title(row: sqlite3.Row, channel: str) -> str:
    version = "业务版" if channel == "business" else "产品版"
    title = clean_display_value(row["title"], "未命名对话")
    return f"客户对话分析｜{version}｜{title}"


def build_analysis_push_message(row: sqlite3.Row, channel: str, body: str) -> str:
    version = "业务版" if channel == "business" else "产品版"
    title = clean_display_value(row["title"], "未命名对话")
    call_type = clean_display_value(row["call_type"], "未填写")
    sales_name = clean_display_value(row["sales_name"], "未识别")
    customer_name = clean_display_value(row["customer_name"], "无")
    created_at = clean_display_value(row["created_at"], "未记录")
    confidence = clean_display_value(row["confidence"], "未识别")

    if channel == "business":
        status_lines = [
            f"**业务机会**：{clean_display_value(row['business_opportunity'], '未识别')}",
            f"**线索等级**：{clean_display_value(row['lead_level'], '未识别')}",
            f"**销售阶段**：{clean_display_value(row['sales_stage'], '未识别')}",
        ]
    else:
        status_lines = [
            f"**产品适配**：{clean_display_value(row['product_fit'], '未识别')}",
            f"**分析可信度**：{confidence}",
        ]

    header_lines = [
        f"# 客户对话分析｜{version}",
        "",
        f"**对话标题**：{title}",
        f"**通话类型**：{call_type}",
        f"**销售**：{sales_name}",
        f"**客户**：{customer_name}",
        f"**创建时间**：{created_at}",
        "",
        *status_lines,
        "",
        "---",
        "",
    ]
    return "\n".join(header_lines) + body.strip()


def clean_display_value(value: object, fallback: str) -> str:
    text = str(value or "").strip()
    return text if text else fallback


@app.post("/api/summaries/{summary_id}/send/{channel}")
def send_daily_summary(summary_id: str, channel: Literal["business", "product"]) -> SendResult:
    row = get_summary_row(summary_id)
    message = row["business_summary"] if channel == "business" else row["product_summary"]
    if not message.strip():
        raise HTTPException(status_code=400, detail="当前汇总内容为空，不能发送。")

    webhook_key = "DINGTALK_BUSINESS_WEBHOOK" if channel == "business" else "DINGTALK_PRODUCT_WEBHOOK"
    secret_key = "DINGTALK_BUSINESS_SECRET" if channel == "business" else "DINGTALK_PRODUCT_SECRET"
    webhook = os.getenv(webhook_key, "").strip()
    secret = os.getenv(secret_key, "").strip()
    if not webhook:
        raise HTTPException(status_code=400, detail=f"未配置 {webhook_key}。")

    title = f"{row['summary_date']} 客户对话汇总｜业务版" if channel == "business" else f"{row['summary_date']} 客户对话汇总｜产品版"
    try:
        send_dingtalk_markdown(webhook, secret, title, message)
        status = "已发送"
        sent_at = now_text()
        error = ""
    except Exception as exc:
        status = "发送失败"
        sent_at = None
        error = str(exc)

    status_column = "business_sent_status" if channel == "business" else "product_sent_status"
    time_column = "business_sent_at" if channel == "business" else "product_sent_at"
    with db() as conn:
        conn.execute(
            f"""
            UPDATE daily_summaries
               SET {status_column} = ?,
                   {time_column} = ?,
                   error_message = ?,
                   updated_at = ?
             WHERE id = ?
            """,
            (status, sent_at, error, now_text(), summary_id),
        )

    if error:
        raise HTTPException(status_code=502, detail=f"钉钉发送失败：{error}")
    return SendResult(ok=True, message=status)


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_records (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                call_type TEXT NOT NULL DEFAULT '',
                customer_name TEXT NOT NULL DEFAULT '',
                sales_name TEXT NOT NULL DEFAULT '',
                raw_text TEXT NOT NULL,
                prompt_version TEXT NOT NULL DEFAULT '',
                model_name TEXT NOT NULL DEFAULT '',
                business_result_json TEXT NOT NULL DEFAULT '{}',
                product_result_json TEXT NOT NULL DEFAULT '{}',
                business_message TEXT NOT NULL DEFAULT '',
                product_message TEXT NOT NULL DEFAULT '',
                business_opportunity TEXT NOT NULL DEFAULT '',
                lead_level TEXT NOT NULL DEFAULT '',
                sales_stage TEXT NOT NULL DEFAULT '',
                product_fit TEXT NOT NULL DEFAULT '',
                confidence TEXT NOT NULL DEFAULT '',
                business_sent_status TEXT NOT NULL DEFAULT '未发送',
                product_sent_status TEXT NOT NULL DEFAULT '未发送',
                business_sent_at TEXT,
                product_sent_at TEXT,
                token_usage TEXT NOT NULL DEFAULT '{}',
                error_message TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_summaries (
                id TEXT PRIMARY KEY,
                summary_date TEXT NOT NULL,
                record_count INTEGER NOT NULL DEFAULT 0,
                source_record_ids TEXT NOT NULL DEFAULT '[]',
                business_summary TEXT NOT NULL DEFAULT '',
                product_summary TEXT NOT NULL DEFAULT '',
                model_name TEXT NOT NULL DEFAULT '',
                token_usage TEXT NOT NULL DEFAULT '{}',
                business_sent_status TEXT NOT NULL DEFAULT '未发送',
                product_sent_status TEXT NOT NULL DEFAULT '未发送',
                business_sent_at TEXT,
                product_sent_at TEXT,
                error_message TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def load_env_file(path: Path) -> None:
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


load_env_file(PORTABLE_ROOT / ".env")
load_env_file(APP_DIR / ".env")


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


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_record(analysis_id: str) -> sqlite3.Row:
    with db() as conn:
        row = conn.execute("SELECT * FROM analysis_records WHERE id = ?", (analysis_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="分析记录不存在。")
    return row


def get_summary_row(summary_id: str) -> sqlite3.Row:
    with db() as conn:
        row = conn.execute("SELECT * FROM daily_summaries WHERE id = ?", (summary_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="汇总记录不存在。")
    return row


def get_summary_record(summary_id: str) -> dict[str, Any]:
    return summary_to_payload(get_summary_row(summary_id))


def summary_to_payload(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    payload = dict(row)
    payload["source_record_ids"] = parse_json(row["source_record_ids"], [])
    payload["token_usage"] = parse_json(row["token_usage"], {})
    return payload


def normalize_summary_date(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return datetime.now().strftime("%Y-%m-%d")
    try:
        return datetime.strptime(text, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="日期格式必须是 YYYY-MM-DD。") from exc


def fetch_analysis_rows_for_date(conn: sqlite3.Connection, summary_date: str) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT *
          FROM analysis_records
         WHERE substr(created_at, 1, 10) = ?
         ORDER BY created_at ASC
        """,
        (summary_date,),
    ).fetchall()


def summary_record_preview(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "customer_name": row["customer_name"],
        "sales_name": row["sales_name"],
        "business_opportunity": row["business_opportunity"],
        "lead_level": row["lead_level"],
        "sales_stage": row["sales_stage"],
        "product_fit": row["product_fit"],
        "created_at": row["created_at"],
    }


def row_to_payload(row: sqlite3.Row) -> dict[str, Any]:
    payload = dict(row)
    payload["business_result"] = parse_json(row["business_result_json"], {})
    payload["product_result"] = parse_json(row["product_result_json"], {})
    payload["token_usage"] = parse_json(row["token_usage"], {})
    payload.pop("business_result_json", None)
    payload.pop("product_result_json", None)
    return payload


def extract_file_text(filename: str, suffix: str, content: bytes) -> str:
    if suffix in TEXT_EXTS:
        return decode_text_bytes(content)
    if suffix == ".docx":
        return extract_docx_text(content)
    if suffix == ".doc":
        raise RuntimeError(f"{filename} 是旧版 .doc 格式，请先另存为 .docx。")
    raise RuntimeError(f"{filename} 不支持，当前支持 .txt、.text、.md、.docx。")


def decode_text_bytes(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def extract_docx_text(content: bytes) -> str:
    try:
        from io import BytesIO

        with zipfile.ZipFile(BytesIO(content)) as archive:
            xml = archive.read("word/document.xml")
    except KeyError as exc:
        raise RuntimeError("docx 文件缺少正文内容。") from exc
    except zipfile.BadZipFile as exc:
        raise RuntimeError("docx 文件无法解析，请确认文件未损坏。") from exc

    root = ElementTree.fromstring(xml)
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        parts = [node.text or "" for node in paragraph.findall(".//w:t", namespace)]
        text = "".join(parts).strip()
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def analyze_with_gpt(payload: CreateAnalysisPayload, model_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("未配置 OPENAI_API_KEY，无法调用 GPT。")

    mode = os.getenv("OPENAI_ENDPOINT_MODE", DEFAULT_ENDPOINT_MODE).strip().lower()
    if mode == "responses":
        return analyze_with_responses_api(payload, model_name, api_key)
    if mode == "chat":
        return analyze_with_chat_completions(payload, model_name, api_key)
    raise RuntimeError("OPENAI_ENDPOINT_MODE 只支持 chat 或 responses。")


def analyze_with_chat_completions(
    payload: CreateAnalysisPayload, model_name: str, api_key: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    body = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": build_prompt()},
            {
                "role": "user",
                "content": (
                    f"【文件名】：{payload.source_filename.strip() or '未提供'}\n"
                    f"【通话类型】：{payload.call_type.strip() or '未填写'}\n"
                    f"【客户名称】：{payload.customer_name.strip() or '未填写'}\n"
                    f"【销售姓名】：{payload.sales_name.strip() or '未填写'}\n"
                    f"【销售与客户电话录音转写文本】：\n{payload.raw_text.strip()}"
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 6000,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "conversation_analysis_mvp",
                "strict": True,
                "schema": analysis_schema(),
            },
        },
    }
    data = post_openai_json(f"{openai_base_url()}/chat/completions", api_key, body)
    content = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
    )
    result = json.loads(strip_json_fence(content))
    if "business" not in result or "product" not in result:
        raise RuntimeError("GPT 返回结果缺少 business 或 product。")
    return result, data.get("usage", {})


def analyze_with_responses_api(
    payload: CreateAnalysisPayload, model_name: str, api_key: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    body = {
        "model": model_name,
        "input": [
            {"role": "developer", "content": build_prompt()},
            {
                "role": "user",
                "content": (
                    f"【文件名】：{payload.source_filename.strip() or '未提供'}\n"
                    f"【通话类型】：{payload.call_type.strip() or '未填写'}\n"
                    f"【客户名称】：{payload.customer_name.strip() or '未填写'}\n"
                    f"【销售姓名】：{payload.sales_name.strip() or '未填写'}\n"
                    f"【销售与客户电话录音转写文本】：\n{payload.raw_text.strip()}"
                ),
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "conversation_analysis_mvp",
                "strict": True,
                "schema": analysis_schema(),
            }
        },
    }
    data = post_openai_json(f"{openai_base_url()}/responses", api_key, body)

    output_text = data.get("output_text") or extract_output_text(data)
    if not output_text:
        raise RuntimeError("GPT 未返回可解析的分析结果。")
    result = json.loads(output_text)
    if "business" not in result or "product" not in result:
        raise RuntimeError("GPT 返回结果缺少 business 或 product。")
    return result, data.get("usage", {})


def summarize_with_gpt(summary_date: str, records: list[sqlite3.Row], model_name: str) -> tuple[dict[str, str], dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("未配置 OPENAI_API_KEY，无法调用 GPT。")
    payload = {
        "summary_date": summary_date,
        "record_count": len(records),
        "records": [summary_source_record(row, index + 1) for index, row in enumerate(records)],
    }
    mode = os.getenv("OPENAI_ENDPOINT_MODE", DEFAULT_ENDPOINT_MODE).strip().lower()
    if mode == "responses":
        body = {
            "model": model_name,
            "input": [
                {"role": "developer", "content": build_summary_prompt()},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "daily_conversation_summary",
                    "strict": True,
                    "schema": summary_schema(),
                }
            },
        }
        data = post_openai_json(f"{openai_base_url()}/responses", api_key, body)
        output_text = data.get("output_text") or extract_output_text(data)
        result = json.loads(output_text)
        return validate_summary_result(result), data.get("usage", {})

    body = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": build_summary_prompt()},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        "temperature": 0.2,
        "max_tokens": 6000,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "daily_conversation_summary",
                "strict": True,
                "schema": summary_schema(),
            },
        },
    }
    data = post_openai_json(f"{openai_base_url()}/chat/completions", api_key, body)
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    result = json.loads(strip_json_fence(content))
    return validate_summary_result(result), data.get("usage", {})


def summary_source_record(row: sqlite3.Row, index: int) -> dict[str, Any]:
    return {
        "index": index,
        "title": row["title"],
        "customer_name": row["customer_name"],
        "sales_name": row["sales_name"],
        "call_type": row["call_type"],
        "created_at": row["created_at"],
        "business_opportunity": row["business_opportunity"],
        "lead_level": row["lead_level"],
        "sales_stage": row["sales_stage"],
        "product_fit": row["product_fit"],
        "confidence": row["confidence"],
        "business_result": parse_json(row["business_result_json"], {}),
        "product_result": parse_json(row["product_result_json"], {}),
        "business_message": row["business_message"][:4000],
        "product_message": row["product_message"][:4000],
    }


def validate_summary_result(result: dict[str, Any]) -> dict[str, str]:
    business_summary = str(result.get("business_summary") or "").strip()
    product_summary = str(result.get("product_summary") or "").strip()
    business_summary, product_summary = split_combined_summary(business_summary, product_summary)
    if not business_summary or not product_summary:
        raise RuntimeError("GPT 返回结果缺少业务汇总或产品汇总。")
    return {"business_summary": business_summary, "product_summary": product_summary}


def split_combined_summary(business_summary: str, product_summary: str) -> tuple[str, str]:
    product_markers = ["二、产品汇总版", "二. 产品汇总版", "产品汇总版"]
    for marker in product_markers:
        if marker in business_summary:
            before, after = business_summary.split(marker, 1)
            business_summary = before.strip()
            if not product_summary.strip():
                product_summary = f"{marker}{after}".strip()
            break

    business_markers = ["一、业务汇总版", "一. 业务汇总版", "业务汇总版"]
    for marker in business_markers:
        if marker in product_summary and not product_summary.strip().startswith(marker):
            _, after = product_summary.split(marker, 1)
            product_summary = after.strip()
            break
    return business_summary.strip(), product_summary.strip()


def post_openai_json(url: str, api_key: str, body: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(detail) from exc


def openai_base_url() -> str:
    return os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")


def strip_json_fence(value: str) -> str:
    text = value.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def extract_output_text(data: dict[str, Any]) -> str:
    chunks: list[str] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(content["text"])
    return "".join(chunks)


def build_prompt() -> str:
    if PROMPT_PATH.exists():
        value = PROMPT_PATH.read_text(encoding="utf-8-sig").strip()
        if value:
            return value
    return default_prompt()


def build_summary_prompt() -> str:
    if SUMMARY_PROMPT_PATH.exists():
        value = SUMMARY_PROMPT_PATH.read_text(encoding="utf-8-sig").strip()
        if value:
            return value
    return default_summary_prompt()


def default_prompt() -> str:
    return """
你是 AI智绘 的客户与销售对话分析助手。请严格基于销售与客户电话录音转写文本，输出业务版和产品版分析。

公共判断规则：
1. 所有重要判断必须有客户或销售原话支撑。
2. 不得将推测写入事实栏。
3. 信息不足时直接写“未提及”“不明确”“未了解”或“证据不足”。
4. 不重复同一个结论。
5. 下一步动作必须明确到做什么、找谁、什么时候、如何验证。
6. 产品版只关注产品适配、真实使用流程和反馈价值，不重复业务版中的意向、线索等级和销售过程。
7. 如销售存在功能错配、错误表达或过度承诺，只列最关键的 1-3 项。
8. 单个客户提出的新功能，原则上不直接进入产品规划。除非涉及核心功能无法使用、严重效果问题、普遍成交阻断或版权、合规等商业风险。
9. 如客户明确承诺提供素材、安排测试、约定下一次沟通或给出具体时间，通常不得判为“明显不成立”或 D，除非原话同时显示明确拒绝、无需求或产品明显无法满足。
10. 如对话已约定素材测试，应优先判断当前销售阶段为“演示测试”或“需求确认”，并在“客户明确承诺”和“下一步动作”中写出动作、对象、时间和验证方式。
11. 先从录音文本中自动提取 meta：标题、通话类型、客户名称、销售姓名、核心话题。用户提供的标题/客户/销售/类型只是参考；如用户未填写，必须尽量从文本中识别。
12. meta.title 用一句短标题概括本次对话，不超过 24 个中文字符；meta.call_type 可根据内容归纳为首次沟通、需求确认、演示测试、试用跟进、报价沟通、采购评估、售后回访或其他合适类型。
13. 如果无法确认客户名称或销售姓名，客户名称写“无”，销售姓名写“销售不明确”，不要编造真实姓名。
14. 识别姓名时严格区分称呼和自我介绍：如原文出现“孙总，我是蛋蛋”“王总您好，我是小李”，则“孙总/王总”是客户称呼，“蛋蛋/小李”是销售姓名。
15. “我是X”“我叫X”“这边是X”“我是XX的销售X”优先作为说话人的真实姓名；“X总/老师/老板/经理”通常是对对方的称呼，不能直接当作销售姓名。
16. 如果文件名里出现类似“家饰新签组员工”，不得把“新签组员工”当客户或销售姓名，姓名必须优先来自正文原话。
17. 销售在开场中直接称呼对方时，可以把该称呼作为客户名称，例如“严先生你好”“孙总您好”“付姐你好”“徐小姐，我是...”；但“老板”“老师”等没有姓氏或具体指向的泛称不能当客户名称。
18. 客户名称可以是有原文依据的客户称呼、客户公司或对方身份信息，例如“徐总”“付姐”“某某公司负责人”；只要不是凭空编造即可。文件名中的部门、组别、员工信息不能作为客户名称。
19. 客户名称不能包含销售姓名，不能写成“销售姓名+客户”“销售的客户”“某某客户”这类没有客户真实称呼或公司依据的泛称；这种情况统一写“无”。

输出要求：
只输出符合 JSON Schema 的 JSON，不要输出 Markdown，不要输出解释性文字。
""".strip()


def default_summary_prompt() -> str:
    return """
你是 AI智绘 的销售对话日汇总分析助手。你会收到某一天多条“单条对话分析”的结构化结果和已生成文案。请基于这些材料生成两份可直接发钉钉群的汇总文案：
1. 业务汇总版：发业务群，供销售、销售负责人快速判断今日线索质量、优先级、跟进动作和销售风险。
2. 产品汇总版：发产品群，供产品团队判断高频场景、产品适配、反馈分类、共性需求，以及 AI智绘 与客户真实业务场景的匹配度验证方式。

汇总原则：
1. 汇总不是逐条复制单条分析，要合并同类项、排序、去重。
2. 业务版只关注线索价值、销售推进、优先跟进和管理动作。
3. 产品版只关注客户场景、工作流、产品适配、能力缺口、效果/体验/案例/话术问题，不重复业务版中的线索等级和销售过程。
4. 重要判断必须能从输入记录中找到支撑；证据不足就写“证据不足”。
5. 客户名称为“无”时不要编造客户名，可用标题或第X条记录指代。
6. 不要把单个客户的新需求直接定为产品规划，除非输入中显示核心功能不可用、严重效果问题、普遍成交阻断或版权/合规风险。
7. 输出要适合钉钉群阅读，控制长度，优先给结论和动作。

业务汇总版建议结构：
一、业务汇总版
日期：
分析对话数：

0. 30秒管理摘要
用不超过5行给负责人先看结论：
- 今日是否值得重点投入：
- 最值得推进的线索：
- 暂缓或不建议继续投入的线索：
- 今日最大阻断：
- 需要管理者拍板或介入的事项：

1. 今日总体判断
按 A/B/C/D 和业务机会分布概括，并给出整体结论。必须明确今天整体线索质量是偏强、一般、偏弱，原因是什么。

2. 重点线索排序
列最值得跟进的 3-10 条。不要用横向长表格，不要输出“客户/标题｜销售｜客户意向｜机会成熟度...”这种挤在一行的格式。必须使用下面的卡片式格式，每条最多4行：
1）客户/标题｜销售｜综合判断
   意向/成熟度：客户意向；机会成熟度
   价值/推进：商业价值；销售可推进性
   下一步：做什么、找谁、什么时候、如何验证
维度定义：
- 客户意向：主动推进 / 愿意继续但未承诺 / 礼貌配合 / 明确拒绝
- 机会成熟度：已明确场景和下一步 / 有需求但缺关键决策信息 / 仅了解 / 已流失
- 商业价值：高 / 中 / 低 / 不明确
- 销售可推进性：可立即推进 / 需补信息 / 暂缓 / 不建议继续
不要只写线索等级，必须说明为什么值得跟或不值得跟。

3. 需要销售立即跟进
写清楚做什么、找谁、什么时候、如何验证。

4. 销售风险和管理提醒
只列最关键 3-5 项，不要泛泛评价。不要用横向长表格，使用下面的短卡片格式：
1）对话/销售：
   客户关键节点：
   销售实际问题：
   影响：
   更合理动作：
重点识别：未确认决策人、无明确下一步、未验证预算、未锁定素材测试、过度承诺、功能错配、客户拒绝后仍强推、客户有兴趣但销售未推进到具体动作等。

5. 今日管理建议
给销售负责人可执行建议。

产品汇总版建议结构：
二、产品汇总版
日期：
分析对话数：

1. 今日客户场景分布
概括行业/品类、业务任务、高频使用环节。

2. 产品适配总体判断
按直接适配、需要测试、部分覆盖、明显不适配归纳。

3. 高频需求与反馈
合并相似反馈，写出现次数、典型记录/原话、产品判断、建议处理方式。

4. 产品风险
明确区分产品能力缺口、效果或稳定性问题、使用体验问题、案例或教程不足、销售表达问题、客户认知偏差。

5. 建议进入产品反馈池
只列证据初步或充分的事项，说明是否共性。

6. 产品建议
不要写成泛泛的功能测试建议，而是围绕“验证产品与客户真实业务场景是否匹配”输出：
- 需要验证的业务场景：
- 需要客户提供的真实素材或业务样例：
- AI智绘进入客户流程的具体环节：
- 判断匹配的成功标准：
- 如果验证通过，产品/销售下一步应怎么推进：
- 如果验证不通过，说明是产品能力问题、效果问题、流程不匹配、客户认知偏差，还是案例/教程不足：

输出要求：
只输出符合 JSON Schema 的 JSON，不要输出 Markdown 代码块，不要输出解释性文字。
business_summary 字段放完整业务汇总版文案。
product_summary 字段放完整产品汇总版文案。
""".strip()


def summary_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["business_summary", "product_summary"],
        "properties": {
            "business_summary": {"type": "string"},
            "product_summary": {"type": "string"},
        },
    }


def analysis_schema() -> dict[str, Any]:
    string = {"type": "string"}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["meta", "business", "product"],
        "properties": {
            "meta": {
                "type": "object",
                "additionalProperties": False,
                "required": ["title", "call_type", "customer_name", "sales_name", "topics"],
                "properties": {
                    "title": string,
                    "call_type": string,
                    "customer_name": string,
                    "sales_name": string,
                    "topics": {"type": "array", "maxItems": 5, "items": string},
                },
            },
            "business": {
                "type": "object",
                "additionalProperties": False,
                "required": ["project_conclusion", "key_evidence", "sales_judgement", "must_verify_next"],
                "properties": {
                    "project_conclusion": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "business_opportunity",
                            "customer_core_scene",
                            "customer_real_need",
                            "current_workflow",
                            "customer_role",
                            "personal_intent",
                            "product_fit",
                            "clear_commitment",
                            "key_blockers",
                            "sales_stage",
                            "lead_level",
                            "next_action",
                            "confidence",
                        ],
                        "properties": {
                            "business_opportunity": {"type": "string", "enum": ["成立", "初步成立", "尚未成立", "明显不成立"]},
                            "customer_core_scene": string,
                            "customer_real_need": string,
                            "current_workflow": string,
                            "customer_role": {"type": "string", "enum": ["决策者", "关键影响者", "使用者", "接口转发者", "角色不明"]},
                            "personal_intent": {"type": "string", "enum": ["主动推进", "愿意继续但未承诺", "礼貌或被动配合", "明确拒绝"]},
                            "product_fit": {"type": "string", "enum": ["直接适配", "需要测试", "部分覆盖", "明显不适配"]},
                            "clear_commitment": string,
                            "key_blockers": {"type": "array", "maxItems": 3, "items": string},
                            "sales_stage": {"type": "string", "enum": ["联系", "场景确认", "需求确认", "演示测试", "试用", "报价", "采购评估", "谈判", "暂停", "流失"]},
                            "lead_level": {"type": "string", "enum": ["A", "B", "C", "D"]},
                            "next_action": string,
                            "confidence": {"type": "string", "enum": ["高", "中", "低"]},
                        },
                    },
                    "key_evidence": {
                        "type": "array",
                        "minItems": 0,
                        "maxItems": 6,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["quote", "confirmed_fact"],
                            "properties": {"quote": string, "confirmed_fact": string},
                        },
                    },
                    "sales_judgement": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["effectiveness", "right_actions", "biggest_loss", "stage_changed", "stage_change_evidence", "risk_responses"],
                        "properties": {
                            "effectiveness": {"type": "string", "enum": ["有效推动", "部分推动", "未有效推动", "造成推进风险"]},
                            "right_actions": {"type": "array", "items": string},
                            "biggest_loss": string,
                            "stage_changed": {"type": "string", "enum": ["是", "否", "无法判断"]},
                            "stage_change_evidence": string,
                            "risk_responses": {
                                "type": "array",
                                "maxItems": 3,
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ["customer_question_or_node", "sales_response", "problem", "better_response"],
                                    "properties": {
                                        "customer_question_or_node": string,
                                        "sales_response": string,
                                        "problem": string,
                                        "better_response": string,
                                    },
                                },
                            },
                        },
                    },
                    "must_verify_next": {
                        "type": "array",
                        "maxItems": 3,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["question", "need_to_confirm", "why_important", "suggested_question"],
                            "properties": {
                                "question": string,
                                "need_to_confirm": string,
                                "why_important": string,
                                "suggested_question": string,
                            },
                        },
                    },
                },
            },
            "product": {
                "type": "object",
                "additionalProperties": False,
                "required": ["user_scene_workflow", "fit_judgement", "feedback_judgement", "test_suggestion"],
                "properties": {
                    "user_scene_workflow": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "industry",
                            "business_task",
                            "operator",
                            "current_tools",
                            "current_time_cost",
                            "current_money_cost",
                            "current_problem",
                            "ai_entry_point",
                        ],
                        "properties": {
                            "industry": string,
                            "business_task": string,
                            "operator": string,
                            "current_tools": string,
                            "current_time_cost": string,
                            "current_money_cost": string,
                            "current_problem": string,
                            "ai_entry_point": string,
                        },
                    },
                    "fit_judgement": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "function_fit",
                            "function_fit_basis",
                            "effect_fit",
                            "effect_fit_basis",
                            "workflow_fit",
                            "workflow_fit_basis",
                            "commercial_fit",
                            "commercial_fit_basis",
                            "overall_fit",
                            "main_risks",
                            "verification_method",
                        ],
                        "properties": {
                            "function_fit": {"type": "string", "enum": ["直接具备", "部分具备", "不具备", "需求不明确"]},
                            "function_fit_basis": string,
                            "effect_fit": {"type": "string", "enum": ["已有证据可满足", "需要素材测试", "存在明显风险", "无法判断"]},
                            "effect_fit_basis": string,
                            "workflow_fit": {"type": "string", "enum": ["可直接进入", "调整后可进入", "只能解决部分环节", "难以进入", "工作流未了解"]},
                            "workflow_fit_basis": string,
                            "commercial_fit": {"type": "string", "enum": ["价值明确", "有潜在价值但需验证", "使用价值有限", "未提及"]},
                            "commercial_fit_basis": string,
                            "overall_fit": {"type": "string", "enum": ["直接适配", "需要测试", "部分覆盖", "明显不适配"]},
                            "main_risks": {"type": "array", "items": string},
                            "verification_method": string,
                        },
                    },
                    "feedback_judgement": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "category",
                            "customer_quote",
                            "affects_purchase_or_usage",
                            "common_need",
                            "evidence_level",
                            "suggested_handling",
                            "reason",
                        ],
                        "properties": {
                            "category": {"type": "string", "enum": ["产品能力缺口", "效果或稳定性问题", "使用体验问题", "案例或教程不足", "销售表达问题", "客户认知偏差", "个性化需求", "无明显反馈"]},
                            "customer_quote": string,
                            "affects_purchase_or_usage": {"type": "string", "enum": ["是", "否", "不明确"]},
                            "common_need": {"type": "string", "enum": ["是", "可能", "暂无证据"]},
                            "evidence_level": {"type": "string", "enum": ["充分", "初步", "不足"]},
                            "suggested_handling": {"type": "string", "enum": ["进入缺陷处理", "进入产品反馈池，等待更多客户佐证", "通过案例解决", "通过教程解决", "通过销售话术解决", "暂不进入产品规划"]},
                            "reason": string,
                        },
                    },
                    "test_suggestion": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "needed",
                            "test_goal",
                            "required_materials",
                            "test_features",
                            "success_criteria",
                            "focus_points",
                            "impact_on_next_judgement",
                        ],
                        "properties": {
                            "needed": {"type": "boolean"},
                            "test_goal": string,
                            "required_materials": string,
                            "test_features": string,
                            "success_criteria": {"type": "array", "items": string},
                            "focus_points": {"type": "array", "items": string},
                            "impact_on_next_judgement": string,
                        },
                    },
                },
            },
        },
    }


def extract_summary_fields(business: dict[str, Any]) -> dict[str, str]:
    conclusion = business.get("project_conclusion") or {}
    return {
        "business_opportunity": str(conclusion.get("business_opportunity") or ""),
        "lead_level": str(conclusion.get("lead_level") or ""),
        "sales_stage": str(conclusion.get("sales_stage") or ""),
        "product_fit": str(conclusion.get("product_fit") or ""),
        "confidence": str(conclusion.get("confidence") or ""),
    }


def normalize_meta(meta: dict[str, Any], payload: CreateAnalysisPayload, now: str) -> dict[str, str]:
    fallback_title = f"客户对话分析 {now[:16]}"
    filename_meta = extract_meta_from_filename(payload.source_filename or payload.raw_text)
    title = payload.title.strip() or str(meta.get("title") or "").strip() or fallback_title
    call_type = first_meaningful_meta_value(
        payload.call_type,
        filename_meta.get("call_type") or "",
        str(meta.get("call_type") or ""),
        fallback="不明确",
    )
    extracted = extract_names_from_text(payload.raw_text)
    excluded_sales_names = collect_sales_exclusion_names(payload, meta, filename_meta, extracted)
    sales_name = first_valid_sales_name(
        payload.sales_name,
        filename_meta.get("sales_name") or "",
        extracted.get("sales_name") or "",
        str(meta.get("sales_name") or ""),
    ) or "销售不明确"
    customer_name = first_valid_customer_name(
        sales_name,
        payload.customer_name,
        extract_explicit_customer_name(payload.raw_text),
        str(meta.get("customer_name") or ""),
        excluded_names=excluded_sales_names,
    ) or "无"
    return {
        "title": title[:80],
        "call_type": call_type[:80],
        "customer_name": customer_name[:80],
        "sales_name": sales_name[:80],
    }


def first_meaningful_meta_value(*values: str, fallback: str) -> str:
    for value in values:
        text = str(value or "").strip()
        if text and not is_blank_meta_value(text):
            return text
    return fallback


def is_blank_meta_value(value: str) -> bool:
    return value.strip() in {"无", "未填写", "不明确", "未识别", "客户不明确", "销售不明确", "角色不明"}


def extract_meta_from_filename(value: str) -> dict[str, str]:
    first_line = (value or "").strip().splitlines()[0] if (value or "").strip() else ""
    name = Path(first_line).name
    stem = Path(name).stem
    parts = [part.strip() for part in re.split(r"[-_－—]+", stem) if part.strip()]
    result: dict[str, str] = {}
    if parts:
        sales_name = clean_person_name(parts[0])
        if is_valid_person_name(sales_name):
            result["sales_name"] = sales_name
    if len(parts) >= 2 and is_valid_call_type_from_filename(parts[1]):
        result["call_type"] = parts[1]
    return result


def is_valid_call_type_from_filename(value: str) -> bool:
    text = str(value or "").strip()
    if not text or len(text) > 30:
        return False
    if re.search(r"(组|员工|客户|原文|通话|录音)$", text):
        return False
    return bool(re.search(r"(电销|销售|直销|客服|运营|VIP|SH\d+|\d{5,})", text, re.IGNORECASE))


def collect_sales_exclusion_names(
    payload: CreateAnalysisPayload,
    meta: dict[str, Any],
    filename_meta: dict[str, str],
    extracted: dict[str, str],
) -> set[str]:
    names = {
        payload.sales_name,
        filename_meta.get("sales_name") or "",
        extracted.get("sales_name") or "",
        str(meta.get("sales_name") or ""),
    }
    first_line = (payload.source_filename or payload.raw_text or "").strip().splitlines()[0] if (payload.source_filename or payload.raw_text or "").strip() else ""
    stem = Path(Path(first_line).name).stem
    first_part = re.split(r"[-_－—]+", stem)[0].strip() if stem else ""
    names.add(first_part)
    return {name for raw in names if (name := clean_person_name(raw)) and is_valid_person_name(name)}


def extract_names_from_text(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    compact = re.sub(r"\s+", " ", text)
    speaker_intro = re.search(
        r"(?:^|[。！？\n\r\s，,：:])[\u4e00-\u9fa5]{1,6}(?:总|姐|哥|老板|老师|经理|主任|院长|店长)"
        r"[，,、\s]*(?:您好|你好|早上好|下午好)?[，,、\s]*"
        r"(?:我(?:是|叫)|这边是|我是这边的)(?P<sales>[\u4e00-\u9fa5A-Za-z0-9]{1,12})",
        compact,
    )
    if speaker_intro:
        result["sales_name"] = clean_person_name(speaker_intro.group("sales"))
        return result

    sales_match = re.search(
        r"(?:我(?:是|叫)|这边是|我是这边的)(?P<sales>[\u4e00-\u9fa5A-Za-z0-9]{1,12})",
        compact,
    )
    if sales_match:
        result["sales_name"] = clean_person_name(sales_match.group("sales"))

    return result


def extract_explicit_customer_name(text: str) -> str:
    compact = re.sub(r"\s+", " ", text)
    addressed = extract_addressed_customer_name(compact)
    if addressed:
        return addressed
    mentioned = extract_mentioned_customer_name(text)
    if mentioned:
        return mentioned
    patterns = [
        r"(?:客户名称|客户姓名|客户名|客户公司|公司名称|公司名|客户)[:：]\s*(?P<name>[\u4e00-\u9fa5A-Za-z0-9（）()·\-]{2,30})",
        r"(?:对方|客户)(?:叫|是)\s*(?P<name>[\u4e00-\u9fa5A-Za-z0-9（）()·\-]{2,20})",
    ]
    for pattern in patterns:
        match = re.search(pattern, compact)
        if not match:
            continue
        name = clean_customer_name(match.group("name"))
        if name:
            return name
    return ""


def extract_mentioned_customer_name(text: str) -> str:
    body_lines = []
    for line in text.splitlines()[:40]:
        cleaned = line.strip()
        if not cleaned or re.search(r"\.(txt|text|md|docx)$", cleaned, re.IGNORECASE):
            continue
        cleaned = re.sub(r"^发言人\d+\s*\d{1,2}:\d{2}\s*", "", cleaned)
        body_lines.append(cleaned)
    compact = " ".join(body_lines)
    honorific = r"(?P<name>[\u4e00-\u9fa5]{1,4}(?:先生|女士|小姐|总|姐|哥|经理|主任|院长|店长))"
    patterns = [
        rf"(?:你好|您好|早上好|上午好|中午好|下午好|晚上好)[，,。；;、\s]*{honorific}",
        rf"{honorific}[，,。；;、\s]*(?:你好|您好|请问|哪里|在吗|方便|有空)",
        rf"(?:联系|对接|跟|给|问一下|找一下)[\u4e00-\u9fa5]{{0,6}}{honorific}",
        rf"(?:客户|对方|负责人|老板|采购|设计师|老板娘)[^\n。；;，,]{{0,8}}{honorific}",
    ]
    for pattern in patterns:
        match = re.search(pattern, compact)
        if not match:
            continue
        name = clean_customer_name(match.group("name"), allow_honorific=True)
        if name:
            return name
    return ""


def extract_addressed_customer_name(compact_text: str) -> str:
    honorific = r"(?P<name>[\u4e00-\u9fa5]{1,4}(?:先生|女士|小姐|总|姐|哥|老师|经理|主任|院长|店长))"
    patterns = [
        rf"(?:你好|您好|早上好|上午好|中午好|下午好|晚上好)[，,、\s]*{honorific}(?:你?好)?[，,、\s]*(?:我(?:是|叫)|我们是|这边是|我是这边的)",
        rf"{honorific}[，,、\s]*(?:你好|您好|早上好|上午好|中午好|下午好|晚上好)?[，,、\s]*(?:我(?:是|叫)|我们是|这边是|我是这边的)",
    ]
    for pattern in patterns:
        match = re.search(pattern, compact_text)
        if not match:
            continue
        name = clean_customer_name(match.group("name"), allow_honorific=True)
        if name:
            return name
    return ""


def first_valid_customer_name(sales_name: str, *values: str, excluded_names: set[str] | None = None) -> str:
    excluded = excluded_names or set()
    for value in values:
        name = clean_customer_name(value, allow_honorific=True)
        if name and is_valid_customer_against_sales(name, sales_name, excluded):
            return name
    return ""


def clean_customer_name(value: str, allow_honorific: bool = False) -> str:
    text = re.split(r"[，,。；;、\s]", value.strip())[0]
    if allow_honorific:
        text = re.sub(r"^(?:打扰您|打扰你|麻烦您|麻烦你)(?=[\u4e00-\u9fa5]{1,4}(?:先生|女士|小姐|总|姐|哥|老师|经理|主任|院长|店长)$)", "", text)
        text = re.sub(r"^(?:喂|喂喂|你好|您好)+(?=[\u4e00-\u9fa5]{1,4}(?:先生|女士|小姐|总|姐|哥|老师|经理|主任|院长|店长)$)", "", text)
        text = re.sub(r"^(?:我|你|您|这个|那个)(?=[\u4e00-\u9fa5]{1,4}(?:先生|女士|小姐|总|姐|哥|老师|经理|主任|院长|店长)$)", "", text)
    invalid_parts = [
        "未提及",
        "不明确",
        "客户不明确",
        "角色不明",
        "客户",
        "老板",
        "员工",
        "销售",
        "组",
        "团队",
        "这个",
        "那个",
        "我们",
        "你们",
        "这边",
        "哪里",
        "可以",
        "不是",
        "没有",
        "不用",
        "暂时",
        "打扰",
        "麻烦",
    ]
    if not text or any(part in text for part in invalid_parts):
        return ""
    if not allow_honorific and re.fullmatch(r"[\u4e00-\u9fa5]{1,3}(总|姐|哥|老师|经理|小姐|女士|先生|主任|店长)", text):
        return ""
    if allow_honorific and re.fullmatch(r"(老板|老师|先生|女士|小姐|姐|哥|经理|主任|店长)", text):
        return ""
    return text[:30]


def is_valid_customer_against_sales(customer_name: str, sales_name: str, excluded_names: set[str] | None = None) -> bool:
    customer = re.sub(r"[（(].*?[）)]", "", customer_name or "").strip()
    sales = re.sub(r"[（(].*?[）)]", "", sales_name or "").strip()
    excluded = {re.sub(r"[（(].*?[）)]", "", name or "").strip() for name in (excluded_names or set())}
    if not customer:
        return False
    if sales and sales != "销售不明确" and (customer == sales or sales in customer):
        return False
    if any(name and (customer == name or name in customer) for name in excluded):
        return False
    return True


def clean_person_name(value: str) -> str:
    text = re.sub(r"[（(].*?[）)]", "", value).strip()
    text = re.sub(r"(您好|你好|有段时间|想问问|这边|销售|顾问|客服|员工|团队|组).*$", "", text).strip()
    return text[:12]


def first_valid_sales_name(*values: str) -> str:
    for value in values:
        name = clean_person_name(value)
        if is_valid_person_name(name):
            return name
    return ""


def is_valid_person_name(value: str) -> bool:
    if not re.fullmatch(r"[\u4e00-\u9fa5]{2,4}", value or ""):
        return False
    invalid_parts = [
        "自己",
        "账号",
        "那个",
        "这个",
        "我们",
        "你们",
        "老板",
        "客户",
        "可以",
        "联系",
        "未填写",
        "不明确",
        "未识别",
        "无",
        "先生",
        "女士",
        "小姐",
        "老师",
        "经理",
        "主任",
        "店长",
        "总",
        "姐",
        "哥",
    ]
    return not any(part in value for part in invalid_parts)


def render_business_message(title: str, meta: CreateAnalysisPayload, business: dict[str, Any]) -> str:
    pc = business.get("project_conclusion") or {}
    evidence = business.get("key_evidence") or []
    judgement = business.get("sales_judgement") or {}
    verify = business.get("must_verify_next") or []
    date_label = extract_date_label(meta.raw_text)
    lines = [
        "一、业务版",
        f"第1段｜{meta.customer_name or '客户不明确'}｜{date_label}通话",
        "",
        "管理摘要",
        "",
        f"业务机会：{pc.get('business_opportunity', '不明确')}",
        f"核心场景：{pc.get('customer_core_scene', '未了解')}",
        f"真实需求：{pc.get('customer_real_need', '不明确')}",
        f"客户当前工作方式：{pc.get('current_workflow', '未了解')}",
        f"客户角色：{pc.get('customer_role', '角色不明')}",
        f"个人意向：{pc.get('personal_intent', '不明确')}",
        f"产品适配：{pc.get('product_fit', '不明确')}",
        f"明确承诺：{pc.get('clear_commitment', '无')}",
        f"关键阻断：{join_items(pc.get('key_blockers') or ['无'])}",
        f"销售阶段：{pc.get('sales_stage', '不明确')}",
        f"线索等级：{pc.get('lead_level', '不明确')}",
        f"下一步：{pc.get('next_action', '不明确')}",
        f"分析可信度：{pc.get('confidence', '低')}",
        "",
        "关键证据",
        "",
        *[f"“{item.get('quote', '')}”\n确认事实：{item.get('confirmed_fact', '')}" for item in evidence],
        "",
        "销售推进判断",
        "",
        f"是否有效推动：{judgement.get('effectiveness', '无法判断')}",
        f"阶段跃迁：{judgement.get('stage_changed', '无法判断')}。{judgement.get('stage_change_evidence', '证据不足')}",
        f"做对的关键动作：{join_items(judgement.get('right_actions') or ['未提及'])}",
        f"最关键缺失：{judgement.get('biggest_loss', '未提及')}",
        "",
        "必须验证",
        "",
        *[f"{index}. {item.get('need_to_confirm') or item.get('question', '')}\n建议问法：{item.get('suggested_question', '')}" for index, item in enumerate(verify, 1)],
    ]
    return "\n".join(lines).strip()


def render_product_message(title: str, meta: CreateAnalysisPayload, product: dict[str, Any]) -> str:
    scene = product.get("user_scene_workflow") or {}
    fit = product.get("fit_judgement") or {}
    feedback = product.get("feedback_judgement") or {}
    test = product.get("test_suggestion") or {}
    lines = [
        "二、产品版",
        f"第1段｜{meta.customer_name or '客户不明确'}｜{scene.get('industry', '场景未了解')}",
        "",
        "用户场景与工作流",
        "",
        f"行业/品类：{scene.get('industry', '未了解')}",
        f"业务任务：{scene.get('business_task', '未了解')}",
        f"当前由谁完成：{scene.get('operator', '未了解')}",
        f"当前工作流、耗时、成本：{scene.get('current_tools', '未了解')}；{scene.get('current_time_cost', '未了解')}；{scene.get('current_money_cost', '未了解')}",
        f"当前结果存在的问题：{scene.get('current_problem', '未了解')}",
        f"AI智绘进入环节：{scene.get('ai_entry_point', '未了解')}",
        "",
        "产品适配",
        "",
        f"功能适配：{fit.get('function_fit', '需求不明确')}。{fit.get('function_fit_basis', '')}",
        f"效果适配：{fit.get('effect_fit', '无法判断')}。{fit.get('effect_fit_basis', '')}",
        f"流程适配：{fit.get('workflow_fit', '工作流未了解')}。{fit.get('workflow_fit_basis', '')}",
        f"商业适配：{fit.get('commercial_fit', '未提及')}。{fit.get('commercial_fit_basis', '')}",
        f"综合适配：{fit.get('overall_fit', '不明确')}",
        f"主要风险：{join_items(fit.get('main_risks') or ['无'])}",
        f"建议验证方式：{fit.get('verification_method', '不明确')}",
        "",
        "产品反馈",
        "",
        f"分类：{feedback.get('category', '无明显反馈')}",
        f"客户原话：{feedback.get('customer_quote', '未提及')}",
        f"是否影响购买或使用：{feedback.get('affects_purchase_or_usage', '不明确')}",
        f"共性判断：{feedback.get('common_need', '暂无证据')}；证据充分度：{feedback.get('evidence_level', '不足')}",
        f"建议：{feedback.get('suggested_handling', '暂不进入产品规划')}",
        f"判断理由：{feedback.get('reason', '证据不足')}",
    ]
    if test.get("needed"):
        lines.extend(
            [
                "",
                "产品建议",
                "",
                f"需要验证的业务场景：{test.get('test_goal', '不明确')}",
                f"客户需提供的真实素材或业务样例：{test.get('required_materials', '未提及')}",
                f"AI智绘进入客户流程的具体环节：{test.get('test_features', '不明确')}",
                f"判断匹配的成功标准：{join_items(test.get('success_criteria') or ['不明确'])}",
                f"需要重点观察的问题：{join_items(test.get('focus_points') or ['不明确'])}",
                f"验证结果如何影响后续判断：{test.get('impact_on_next_judgement', '不明确')}",
            ]
        )
    return "\n".join(lines).strip()


def numbered(items: list[Any]) -> list[str]:
    return [f"{index}. {item}" for index, item in enumerate(items, 1)]


def join_items(items: list[Any]) -> str:
    return "；".join(str(item).strip() for item in items if str(item).strip()) or "无"


def extract_date_label(text: str) -> str:
    first_line = (text or "").strip().splitlines()[0] if (text or "").strip() else ""
    match = re.search(r"(20\d{2})[-_/\.](\d{1,2})[-_/\.](\d{1,2})", first_line)
    if match:
        return f"{int(match.group(2))}月{int(match.group(3))}日"
    return f"{datetime.now().month}月{datetime.now().day}日"


def send_dingtalk_markdown(webhook: str, secret: str, title: str, text: str) -> None:
    url = signed_dingtalk_url(webhook, secret)
    body = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": text,
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    if data.get("errcode") != 0:
        raise RuntimeError(data.get("errmsg") or json.dumps(data, ensure_ascii=False))


def signed_dingtalk_url(webhook: str, secret: str) -> str:
    if not secret:
        return webhook
    timestamp = str(round(time.time() * 1000))
    sign_source = f"{timestamp}\n{secret}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), sign_source, hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(digest).decode("utf-8"))
    separator = "&" if "?" in webhook else "?"
    return f"{webhook}{separator}timestamp={timestamp}&sign={sign}"


def parse_json(value: str, fallback: Any) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
