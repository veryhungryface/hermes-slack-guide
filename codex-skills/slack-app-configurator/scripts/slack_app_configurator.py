#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


BOT_SCOPES = [
    ("app_mentions:read", "앱이 있는 대화에서 @ISM-helper 멘션 보기"),
    ("chat:write", "@ISM-helper로 메시지 보내기"),
    ("files:read", "앱이 추가된 채널과 대화에서 공유한 파일 보기"),
    ("files:write", "앱으로 파일 업로드, 편집 및 삭제"),
    ("im:history", "앱이 추가된 DM에서 메시지와 콘텐츠 보기"),
    ("im:read", "앱이 추가된 DM 기본 정보 보기"),
    ("im:write", "사람들과 DM 시작"),
    ("reactions:write", "이모티콘 반응 추가 및 편집"),
    ("users:read", "워크스페이스의 사람 보기"),
]

USER_SCOPES = [
    ("channels:history", "사용자의 공개 채널 메시지와 콘텐츠 보기"),
    ("channels:read", "워크스페이스 공개 채널 기본 정보 보기"),
    ("chat:write", "사용자를 대신하여 메시지 보내기"),
    ("files:read", "사용자가 접근 가능한 대화의 파일 보기"),
    ("files:write", "사용자를 대신하여 파일 업로드, 편집 및 삭제"),
    ("groups:history", "사용자의 비공개 채널 메시지와 콘텐츠 보기"),
    ("groups:read", "사용자의 비공개 채널 기본 정보 보기"),
    ("im:history", "사용자의 DM 메시지와 콘텐츠 보기"),
    ("im:read", "사용자의 DM 기본 정보 보기"),
    ("mpim:history", "사용자의 그룹 DM 메시지와 콘텐츠 보기"),
    ("mpim:read", "사용자의 그룹 DM 기본 정보 보기"),
    ("search:read", "워크스페이스의 콘텐츠 검색"),
    ("users:read", "워크스페이스의 사람 보기"),
]

DEFAULTS = {
    "appName": "",
    "botDisplayName": "",
    "description": "",
    "backgroundColor": "#0C6B4E",
    "botScopes": [{"id": scope, "label": label} for scope, label in BOT_SCOPES],
    "userScopes": [{"id": scope, "label": label} for scope, label in USER_SCOPES],
}

SKILL_DIR = Path(__file__).resolve().parent.parent
HTML_TEMPLATE = SKILL_DIR / "assets" / "slack_app_configurator.html"


def allowed_scopes() -> dict[str, set[str]]:
    return {
        "bot": {scope for scope, _ in BOT_SCOPES},
        "user": {scope for scope, _ in USER_SCOPES},
    }


def read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("content-length", "0") or "0")
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8") or "{}")


def write_json(handler: BaseHTTPRequestHandler, status: int, body: dict[str, Any]) -> None:
    data = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("content-type", "application/json; charset=utf-8")
    handler.send_header("cache-control", "no-store")
    handler.send_header("content-length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def render_html() -> bytes:
    template = HTML_TEMPLATE.read_text(encoding="utf-8")
    html = template.replace("__DEFAULTS__", json.dumps(DEFAULTS, ensure_ascii=False))
    return html.encode("utf-8")


def manifest_from_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, list[str]]]:
    app_name = str(payload.get("appName") or "").strip()
    description = str(payload.get("description") or "").strip()
    bot_display_name = str(payload.get("botDisplayName") or "").strip()
    background_color = str(payload.get("backgroundColor") or DEFAULTS["backgroundColor"]).strip()

    if not app_name:
        raise ValueError("App name is required.")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,78}[a-z0-9]", bot_display_name):
        raise ValueError("Bot display_name must use lowercase letters, numbers, dots, underscores, or hyphens.")
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", background_color):
        raise ValueError("Background color must be a hex color like #0C6B4E.")

    scopes = payload.get("scopes") if isinstance(payload.get("scopes"), dict) else {}
    allowed = allowed_scopes()
    selected = {
        "bot": [scope for scope in scopes.get("bot", []) if scope in allowed["bot"]],
        "user": [scope for scope in scopes.get("user", []) if scope in allowed["user"]],
    }
    if not selected["bot"]:
        raise ValueError("Select at least one bot scope.")
    if not selected["user"]:
        raise ValueError("Select at least one user scope.")

    display_information = {
        "name": app_name,
        "background_color": background_color.upper(),
    }
    if description:
        display_information["description"] = description

    manifest = {
        "display_information": display_information,
        "features": {
            "bot_user": {
                "display_name": bot_display_name,
                "always_online": False,
            }
        },
        "oauth_config": {
            "scopes": selected,
        },
        "settings": {
            "org_deploy_enabled": False,
            "socket_mode_enabled": False,
            "token_rotation_enabled": False,
        },
    }
    return manifest, selected


def compact_manifest(payload: dict[str, Any]) -> str:
    manifest = payload.get("manifest")
    if not isinstance(manifest, dict) or not manifest:
        manifest, _ = manifest_from_payload(payload)
    return json.dumps(manifest, ensure_ascii=False, separators=(",", ":"))


def redact(value: str, token: str | None) -> str:
    if token:
        value = value.replace(token, "[REDACTED]")
    return value


def run_slack(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    token = str(payload.get("configToken") or "").strip()
    env = os.environ.copy()
    env["SLACK_SKIP_UPDATE"] = "1"
    env["NO_COLOR"] = "1"

    if action in {"validate", "create"}:
        if not token:
            raise ValueError("App Configuration Token is required.")
    else:
        raise ValueError(f"Unsupported action: {action}")

    slack = shutil.which("slack")
    if not slack:
        raise RuntimeError("Slack CLI was not found in PATH.")

    if action in {"validate", "create"}:
        method = "apps.manifest.validate" if action == "validate" else "apps.manifest.create"
        command = [slack, "api", method, "--token", token, f"manifest={compact_manifest(payload)}"]

    completed = subprocess.run(
        command,
        env=env,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    stdout = redact(completed.stdout, token)
    stderr = redact(completed.stderr, token)
    preview = redact(" ".join(command), token)
    parsed = None
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        parsed = None

    return {
        "action": action,
        "exit_code": completed.returncode,
        "command": preview,
        "stdout": stdout,
        "stderr": stderr,
        "parsed": parsed,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            data = render_html()
            self.send_response(200)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("cache-control", "no-store")
            self.send_header("content-length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/api/defaults":
            write_json(self, 200, {"defaults": DEFAULTS})
            return
        write_json(self, 404, {"error": "not_found"})

    def do_POST(self) -> None:
        try:
            payload = read_json(self)
            path = urlparse(self.path).path
            if path == "/api/manifest":
                manifest, selected = manifest_from_payload(payload)
                write_json(self, 200, {"manifest": manifest, "selected": selected})
                return
            if path == "/api/run":
                result = run_slack(str(payload.get("action") or ""), payload)
                status = 200 if result["exit_code"] == 0 else 400
                write_json(self, status, result)
                return
            write_json(self, 404, {"error": "not_found"})
        except Exception as exc:
            write_json(self, 400, {"error": type(exc).__name__, "message": str(exc)})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a local Slack app configurator GUI.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind. Default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=4197, help="Port to bind. Default: 4197")
    parser.add_argument("--open", action="store_true", help="Open the GUI in the default browser.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{server.server_port}/"
    print(f"Slack App Configurator running at {url}", flush=True)
    if args.open:
        threading.Thread(target=lambda: (time.sleep(0.3), webbrowser.open(url)), daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Slack App Configurator.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
