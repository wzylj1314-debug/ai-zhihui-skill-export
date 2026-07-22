from __future__ import annotations

import socket
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


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
_preload_env_file(WEB_DIR.parents[1] / ".env")
_preload_env_file(WEB_DIR.parent / ".env")
TOOL_HOST = os.getenv("ZHIHUI_TOOL_HOST", "127.0.0.1")
HUB_PORT = int(os.getenv("ZHIHUI_TOOL_HUB_PORT", "8900"))
FAQ_PORT = int(os.getenv("ZHIHUI_FAQ_PORT", "8899"))
CONVERSATION_PORT = int(os.getenv("ZHIHUI_CONVERSATION_PORT", "8910"))

app = FastAPI(title="AI\u667a\u7ed8\u5de5\u5177\u5e73\u53f0")
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")


@dataclass(frozen=True)
class ToolEntry:
    key: str
    title: str
    subtitle: str
    description: str
    primary_url: str
    primary_label: str
    secondary_url: str
    secondary_label: str
    port: int
    owner: str


TOOLS = [
    ToolEntry(
        key="faq",
        title="FAQ \u5de5\u4f5c\u53f0",
        subtitle="\u622a\u56fe\u5165\u5e93\u3001\u8349\u7a3f\u5ba1\u6838\u3001FAQ \u53f0\u8d26",
        description="\u7528\u4e8e\u5904\u7406\u9489\u9489\u622a\u56fe\u3001\u751f\u6210 FAQ \u8349\u7a3f\u3001\u5ba1\u6838\u654f\u611f\u5185\u5bb9\uff0c\u5e76\u8fdb\u5165\u8fd0\u8425\u770b\u677f\u67e5\u770b\u5165\u5e93\u72b6\u6001\u3002",
        primary_url=f"http://{TOOL_HOST}:{FAQ_PORT}/",
        primary_label="\u8fdb\u5165\u622a\u56fe\u5de5\u4f5c\u53f0",
        secondary_url=f"http://{TOOL_HOST}:{FAQ_PORT}/board",
        secondary_label="\u8fd0\u8425\u770b\u677f",
        port=FAQ_PORT,
        owner="\u8fd0\u8425 / \u77e5\u8bc6\u5e93",
    ),
    ToolEntry(
        key="conversation",
        title="\u5ba2\u6237\u5bf9\u8bdd\u5206\u6790",
        subtitle="\u5f55\u97f3\u6587\u672c\u5206\u6790\u3001\u4eca\u65e5\u6c47\u603b\u3001\u9489\u9489\u5206\u7fa4",
        description="\u4e0a\u4f20\u9500\u552e\u4e0e\u5ba2\u6237\u901a\u8bdd\u8f6c\u5199\u6587\u672c\uff0c\u751f\u6210\u4e1a\u52a1\u7248\u3001\u4ea7\u54c1\u7248\u548c\u6bcf\u65e5\u6c47\u603b\uff0c\u5e76\u63a8\u9001\u5230\u5bf9\u5e94\u9489\u9489\u7fa4\u3002",
        primary_url=f"http://{TOOL_HOST}:{CONVERSATION_PORT}/",
        primary_label="\u8fdb\u5165\u5206\u6790\u5e73\u53f0",
        secondary_url=f"http://{TOOL_HOST}:{CONVERSATION_PORT}/",
        secondary_label="\u65b0\u5efa\u5206\u6790",
        port=CONVERSATION_PORT,
        owner="\u9500\u552e / \u4ea7\u54c1",
    ),
]


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    html = (WEB_DIR / "templates" / "index.html").read_text(encoding="utf-8")
    return (
        html.replace("http://127.0.0.1:8899", f"http://{TOOL_HOST}:{FAQ_PORT}")
        .replace("http://127.0.0.1:8910", f"http://{TOOL_HOST}:{CONVERSATION_PORT}")
        .replace("http://127.0.0.1:8900", f"http://{TOOL_HOST}:{HUB_PORT}")
    )


@app.get("/api/tools")
def list_tools() -> dict[str, object]:
    tools = []
    for tool in TOOLS:
        item = asdict(tool)
        item["online"] = is_port_open("127.0.0.1", tool.port)
        tools.append(item)
    return {"tools": tools}


def is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.4):
            return True
    except OSError:
        return False
