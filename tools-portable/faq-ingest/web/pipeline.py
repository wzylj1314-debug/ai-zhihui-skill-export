from __future__ import annotations

import re
import os
import subprocess
import threading
import uuid
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from shutil import which
from typing import Any


STAGE_PATTERN = re.compile(r"^\[stage\]\s+(\w+)\s*$")
BATCH_PATTERN = re.compile(r"^\[batch\]\s+(\S+)\s*$")
OCR_TILE_PATTERN = re.compile(r"^OCR tile\s+(\d+)/(\d+):")
OCR_IMAGE_PATTERN = re.compile(r"^OCR image\s+(.+?):\s+(.+)$")
OCR_CACHE_PATTERN = re.compile(r"^OCR cache hit:\s+(.+)$")


@dataclass
class Job:
    id: str
    stage: str = "upload"
    status: str = "running"
    message: str = ""
    draft_date: str = field(default_factory=lambda: date.today().isoformat())
    batch: str = ""
    ocr_tile: int = 0
    ocr_tiles: int = 0
    ocr_detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.id,
            "stage": self.stage,
            "status": self.status,
            "message": self.message,
            "draft_date": self.draft_date,
            "batch": self.batch,
            "ocr_tile": self.ocr_tile,
            "ocr_tiles": self.ocr_tiles,
            "ocr_detail": self.ocr_detail,
        }


class JobRunner:
    def __init__(self, root: Path, script: Path | None = None):
        self.root = root
        self.script = script or (root / "scripts" / "faq-ingest" / "faq-ingest.ps1")
        self.jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def start(self, force_ocr: bool = False) -> Job:
        # Single-flight: if a run is already in progress, attach to it instead of
        # starting a second concurrent pipeline over the same screenshots folder
        # (double-click / double web server would otherwise duplicate drafts).
        with self._lock:
            for existing in self.jobs.values():
                if existing.status == "running":
                    return existing
            job = Job(id=uuid.uuid4().hex)
            self.jobs[job.id] = job
        thread = threading.Thread(target=self._run, args=(job.id, force_ocr), daemon=True)
        thread.start()
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self.jobs.get(job_id)

    def _update(self, job_id: str, **changes: Any) -> None:
        with self._lock:
            job = self.jobs[job_id]
            for key, value in changes.items():
                setattr(job, key, value)

    def _run(self, job_id: str, force_ocr: bool) -> None:
        job = self.get(job_id)
        if job is None:
            return

        ps = which("pwsh") or which("powershell") or "powershell"
        script = self.script
        cmd = [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-Date", job.draft_date]
        if force_ocr:
            cmd.append("-ForceOcr")
        cmd += ["-Root", str(self.root)]

        env = os.environ.copy()
        env.setdefault("ZHIHUI_PORTABLE_ROOT", str(self.root))
        env.setdefault("ZHIHUI_FAQ_TOOL_DIR", str(script.parent))

        output: list[str] = []
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=self.root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            assert proc.stdout is not None
            for line in proc.stdout:
                text = line.rstrip()
                output.append(text)
                match = STAGE_PATTERN.match(text)
                if match:
                    stage = match.group(1)
                    changes: dict[str, Any] = {"stage": stage, "message": "\n".join(output[-8:])}
                    if stage != "ocr":
                        changes.update({"ocr_tile": 0, "ocr_tiles": 0, "ocr_detail": ""})
                    self._update(job_id, **changes)
                    continue
                tile_match = OCR_TILE_PATTERN.match(text)
                if tile_match:
                    tile = int(tile_match.group(1))
                    tiles = int(tile_match.group(2))
                    self._update(
                        job_id,
                        stage="ocr",
                        ocr_tile=tile,
                        ocr_tiles=tiles,
                        ocr_detail=f"第 {tile}/{tiles} 段",
                        message="\n".join(output[-12:]),
                    )
                    continue
                image_match = OCR_IMAGE_PATTERN.match(text)
                if image_match:
                    self._update(
                        job_id,
                        stage="ocr",
                        ocr_tile=0,
                        ocr_tiles=0,
                        ocr_detail=image_match.group(2),
                        message="\n".join(output[-12:]),
                    )
                    continue
                cache_match = OCR_CACHE_PATTERN.match(text)
                if cache_match:
                    self._update(
                        job_id,
                        stage="ocr",
                        ocr_detail=f"命中缓存：{cache_match.group(1)}",
                        message="\n".join(output[-12:]),
                    )
                    continue
                batch_match = BATCH_PATTERN.match(text)
                if batch_match:
                    self._update(job_id, batch=batch_match.group(1), message="\n".join(output[-8:]))
                else:
                    self._update(job_id, message="\n".join(output[-12:]))
            code = proc.wait()
            if code == 0:
                if any("No screenshots found" in item for item in output):
                    self._update(
                        job_id,
                        status="failed",
                        message="没有找到待处理截图。请先上传截图，或确认截图没有已经被移动到 _done。",
                    )
                    return
                self._update(job_id, stage="done", status="done", message="\n".join(output[-20:]))
            else:
                self._update(job_id, status="failed", message=_friendly_error("\n".join(output), code))
        except Exception as exc:
            self._update(job_id, status="failed", message=str(exc))


def _friendly_error(output: str, code: int) -> str:
    lowered = output.lower()
    if "invoke-restmethod" in lowered or "connection" in lowered or "127.0.0.1" in lowered:
        return f"整理 FAQ 失败：无法连接 gateway（请先启动 openclaw gateway）。\n\n{output}"
    if "sensitive scan failed" in lowered:
        return f"脱敏复扫失败：发现敏感信息，需要先人工处理。\n\n{output}"
    return f"流水线失败，退出码 {code}。\n\n{output}"
