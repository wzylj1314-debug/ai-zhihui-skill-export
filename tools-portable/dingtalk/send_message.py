from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def main() -> int:
    load_env(Path(__file__).resolve().parents[1] / ".env")
    load_env(Path(__file__).resolve().parent / ".env")

    parser = argparse.ArgumentParser(description="Portable DingTalk markdown sender.")
    parser.add_argument("--title", default="AI智绘通知")
    parser.add_argument("--text", required=True)
    parser.add_argument("--webhook-env", default="DINGTALK_WEBHOOK")
    parser.add_argument("--secret-env", default="DINGTALK_SECRET")
    parser.add_argument("--send", action="store_true", help="Actually send the message. Default is dry-run.")
    args = parser.parse_args()

    webhook = os.getenv(args.webhook_env, "").strip()
    secret = os.getenv(args.secret_env, "").strip()
    payload = {"msgtype": "markdown", "markdown": {"title": args.title, "text": args.text}}

    if not args.send:
        print(json.dumps({"ok": True, "dry_run": True, "payload": payload}, ensure_ascii=False, indent=2))
        return 0

    if not webhook:
        print(json.dumps({"ok": False, "error": f"missing env {args.webhook_env}"}, ensure_ascii=False), file=sys.stderr)
        return 2

    request = urllib.request.Request(
        signed_url(webhook, secret),
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    result: dict[str, Any]
    try:
        result = json.loads(body)
    except json.JSONDecodeError:
        result = {"raw": body}
    ok = result.get("errcode") in (None, 0)
    print(json.dumps({"ok": ok, "response": result}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


def signed_url(webhook: str, secret: str) -> str:
    if not secret:
        return webhook
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), string_to_sign, hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(digest).decode("utf-8"))
    separator = "&" if "?" in webhook else "?"
    return f"{webhook}{separator}timestamp={timestamp}&sign={sign}"


def load_env(path: Path) -> None:
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


if __name__ == "__main__":
    raise SystemExit(main())
