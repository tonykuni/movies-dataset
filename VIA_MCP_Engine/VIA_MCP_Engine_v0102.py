#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA_MCP_Engine v0102 — 泛用型多 AI 平台 MCP 設定引擎(Python 後端 + 滑鼠操作 HTML 前端)

v0102(2026-11-05;v0101 = PR #591 併入 main 的無 probe 版,已發布不就地改,升版為 v0102;操作員令「UPGRADE AGAIN AND ADD VERSION NO. ON THE NAME · OPTIMIZE TEST DEBUG USER-TEST DEBUG TILL IT WORKS · ADD IT TO VCGC」):
  • 檔名帶版號(VIA_MCP_Engine_v0102.py / .html;前端檔照本檔 stem 找,舊名不再用)。
  • 新增 probe(▶ 測試啟動):真的用渲染出的指令把 MCP server 跑起來,走 stdio JSON-RPC initialize → tools/list,
    回報 server 名稱 / 版本 / 工具數;秘密只從憑證庫或環境變數注入子行程,stderr 回報前把秘密遮掉。
  • VCGC 入口:via-vcgc mcp <子指令>(CGC_MDL149 v0192 薄尾轉接到本檔 main);--selftest 與 selftest 同義。
  • GitHub API 位址可用 VIA_MCP_GITHUB_API 指到本機假伺服器(使用者測試用;預設 https://api.github.com)。
  • 自測收尾印機讀判決行「[計] VIA_MCP_Engine v0102 自測 N/N · PASS」。

一句話:把「哪個 AI 平台 → 接哪幾個 MCP Server → 用什麼跑 → 秘密放哪 → 設定檔寫到哪」
這五件事收成一個只靠滑鼠點選就能完成的本機平台;每個平台最多掛 5 個 MCP。

設計原則
  • 泛用:平台(Claude Desktop / Code / Design · ChatGPT Chat / Projects / Codex · Copilot · Gemini · Manus
    · Perplexity · Cursor · Windsurf)與 MCP 目錄(Filesystem · Git · GitHub · Fetch · Memory · SQLite · DuckDB
    · PostgreSQL · OneDrive · Google Drive · Dropbox · Obsidian · Notion …)都是資料,不是程式分支。
  • 自適應:偵測 OS / node / npx / uvx / docker / 憑證庫 / 既有設定檔,自動選執行器與秘密保護方式;
    Windows 自動用 cmd /c 包 npx,Claude Desktop 設定檔不存在就建立。
  • 安全:秘密(Token)永不寫進任何設定檔與 state;走 Windows 憑證管理員 / macOS Keychain /
    secret-tool 的包裝器,或 VS Code 的 inputs(password)。GitHub Token 可一鍵做
    「真讀成功、寫被拒」驗證,寫入意外成功時自動清掉測試 Issue 與分支。
  • 只讀他系統:不碰 VRN-1 / VRN-2 / VDF / VCGC 的任何正本(本引擎是 VIA 根下獨立工具)。
  • 零第三方依賴:只用 Python 標準庫(3.11+;tomllib 用於 Codex TOML 回讀驗證)。

用法
  python3 VIA_MCP_Engine_v0102.py serve [--port 8765] [--no-browser]     開前端(預設只綁 127.0.0.1)
  python3 VIA_MCP_Engine_v0102.py doctor                                  環境偵測
  python3 VIA_MCP_Engine_v0102.py platforms | catalog                     列平台 / MCP 目錄
  python3 VIA_MCP_Engine_v0102.py add <platform> <server> [k=v ...]       加一個 MCP(上限 5)
  python3 VIA_MCP_Engine_v0102.py remove <platform> <server>
  python3 VIA_MCP_Engine_v0102.py apply <platform> [--dry-run]            寫設定檔(先備份)
  python3 VIA_MCP_Engine_v0102.py probe <platform> [name] [--timeout S]   真啟動 MCP 做 initialize / tools/list
  python3 VIA_MCP_Engine_v0102.py token check                             Token 類型 / 範圍 / 到期
  python3 VIA_MCP_Engine_v0102.py token readonly-test --repo o/r [--temp] 讀成功寫被拒驗證(+自動清理)
  python3 VIA_MCP_Engine_v0102.py selftest | --selftest                   離線自測(不連網、不碰真設定)
  經 VCGC:VIA_FROM_VCGC=YES via-vcgc mcp <以上任一子指令>

環境變數
  VIA_MCP_HOME                   state / 備份 / 包裝器存放夾(預設 ~/.via_mcp_engine)
  GITHUB_PERSONAL_ACCESS_TOKEN   受測 Token(唯讀);GITHUB_ADMIN_TOKEN 只在 --temp 建刪臨時倉用
"""
from __future__ import annotations

import argparse
import base64
import copy
import datetime as _dt
import hashlib
import http.server
import json
import os
import platform as _platform
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

VERSION = "v0102"
ENGINE_NAME = "VIA_MCP_Engine"
MAX_SERVERS_PER_PLATFORM = 5
HERE = Path(__file__).resolve().parent
HTML_FILE = HERE / (Path(__file__).stem + ".html")        # 前端與後端同 stem 同版號
GITHUB_API = os.environ.get("VIA_MCP_GITHUB_API", "https://api.github.com").rstrip("/")  # 使用者測試可指本機假伺服器
USER_AGENT = f"{ENGINE_NAME}/{VERSION}"
PROBE_PROTOCOL = "2025-06-18"


# ────────────────────────────────────────────────────────────────────────────
# 小工具
# ────────────────────────────────────────────────────────────────────────────
def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d%H%M%S")


def os_name() -> str:
    s = _platform.system()
    return s if s in ("Windows", "Darwin", "Linux") else "Linux"


def home() -> Path:
    return Path(os.environ.get("VIA_MCP_FAKE_HOME") or Path.home())


def engine_home() -> Path:
    p = Path(os.environ.get("VIA_MCP_HOME") or (home() / ".via_mcp_engine"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def mask(secret: str) -> str:
    if not secret:
        return ""
    if len(secret) <= 8:
        return "*" * len(secret)
    return secret[:4] + "…" + secret[-4:]


def which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def run_quiet(args: List[str], timeout: float = 8.0) -> Tuple[int, str]:
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or p.stderr or "").strip()
    except Exception as e:  # noqa: BLE001 — 偵測用途,失敗只回報不中斷
        return 1, f"{type(e).__name__}: {e}"


def expand_path(template: str, project: Optional[str] = None) -> Path:
    s = template
    if "{project}" in s:
        s = s.replace("{project}", project or str(home()))
    s = s.replace("%APPDATA%", os.environ.get("APPDATA", str(home() / "AppData" / "Roaming")))
    s = s.replace("~", str(home()), 1) if s.startswith("~") else s
    return Path(s)


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as e:
        raise ValueError(f"{path} 不是合法 JSON:{e}") from e


def write_text_with_backup(path: Path, text: str, backup_dir: Path) -> Optional[Path]:
    """寫檔前先備份舊檔到 backup_dir;回傳備份路徑(沒有舊檔則 None)。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    backup: Optional[Path] = None
    if path.exists():
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / f"{path.name}.bak-{stamp()}"
        shutil.copy2(path, backup)
    path.write_text(text, encoding="utf-8")
    return backup


# ────────────────────────────────────────────────────────────────────────────
# 資料:MCP 目錄(免費 · 開源 · 主流維護 · 安全評分 1~5)
#   runner: npx | uvx | docker | binary;params 由前端滑鼠選(paths/path/file 走資料夾瀏覽器;secret 不入設定)
# ────────────────────────────────────────────────────────────────────────────
CATALOG: List[Dict[str, Any]] = [
    # ── 核心 ──
    {"id": "filesystem", "name": "Filesystem", "group": "核心", "safety": 5, "free": True, "open_source": True,
     "maintainer": "官方(modelcontextprotocol)", "local_only": True, "recommended": True,
     "desc": "本機檔案讀寫,只開放你點選的資料夾",
     "runner": "npx", "package": "@modelcontextprotocol/server-filesystem",
     "args": ["{paths}"],
     "params": [{"key": "paths", "type": "paths", "label": "允許的資料夾", "required": True}]},
    {"id": "memory", "name": "Memory", "group": "核心", "safety": 5, "free": True, "open_source": True,
     "maintainer": "官方(modelcontextprotocol)", "local_only": True, "recommended": True,
     "desc": "知識圖譜長期記憶(本機 JSONL)",
     "runner": "npx", "package": "@modelcontextprotocol/server-memory", "args": [],
     "params": [{"key": "memory_file", "type": "file", "label": "記憶檔(可空)", "required": False,
                 "env": "MEMORY_FILE_PATH"}]},
    {"id": "git", "name": "Git", "group": "核心", "safety": 5, "free": True, "open_source": True,
     "maintainer": "官方(modelcontextprotocol)", "local_only": True, "recommended": True,
     "desc": "本機 Git 倉:log / diff / status / commit",
     "runner": "uvx", "package": "mcp-server-git", "args": ["--repository", "{repository}"],
     "params": [{"key": "repository", "type": "path", "label": "Git 倉資料夾", "required": True}]},
    {"id": "github", "name": "GitHub", "group": "核心", "safety": 5, "free": True, "open_source": True,
     "maintainer": "官方(GitHub)", "local_only": False, "recommended": True,
     "desc": "Repo / Issues / PR / Actions;建議搭配唯讀 Fine-grained PAT",
     "runner": "docker", "image": "ghcr.io/github/github-mcp-server",
     "alt_runner": {"binary": "github-mcp-server", "args": ["stdio"]},
     "args": [], "secrets": [{"env": "GITHUB_PERSONAL_ACCESS_TOKEN", "store_key": "GITHUB_PAT_READONLY",
                              "label": "GitHub Token(唯讀)"}],
     "params": [{"key": "toolsets", "type": "choice", "label": "工具集", "required": False,
                 "choices": ["repos,issues,pull_requests", "repos", "all"], "env": "GITHUB_TOOLSETS"},
                {"key": "read_only", "type": "bool", "label": "唯讀模式", "default": True,
                 "env": "GITHUB_READ_ONLY", "true_value": "1"}]},
    {"id": "fetch", "name": "Fetch", "group": "核心", "safety": 4, "free": True, "open_source": True,
     "maintainer": "官方(modelcontextprotocol)", "local_only": False, "recommended": True,
     "desc": "安全讀取網頁並轉 Markdown",
     "runner": "uvx", "package": "mcp-server-fetch", "args": [], "params": []},
    {"id": "sequential-thinking", "name": "Sequential Thinking", "group": "核心", "safety": 5, "free": True,
     "open_source": True, "maintainer": "官方(modelcontextprotocol)", "local_only": True, "recommended": False,
     "desc": "逐步推理輔助(無外連、無檔案存取)",
     "runner": "npx", "package": "@modelcontextprotocol/server-sequential-thinking", "args": [], "params": []},
    # ── 資料庫 ──
    {"id": "sqlite", "name": "SQLite", "group": "資料庫", "safety": 5, "free": True, "open_source": True,
     "maintainer": "社群(mcp-sqlite)", "local_only": True, "recommended": True,
     "desc": "本機單檔資料庫,最簡單",
     "runner": "npx", "package": "mcp-sqlite", "args": ["{db}"],
     "params": [{"key": "db", "type": "file", "label": "SQLite 檔(.db)", "required": True, "ext": [".db", ".sqlite", ".sqlite3"]}]},
    {"id": "duckdb", "name": "DuckDB", "group": "資料庫", "safety": 4, "free": True, "open_source": True,
     "maintainer": "MotherDuck(官方)", "local_only": True, "recommended": True,
     "desc": "量化研究首選:parquet / 大表分析",
     "runner": "uvx", "package": "mcp-server-motherduck", "args": ["--db-path", "{db}"],
     "params": [{"key": "db", "type": "file", "label": "DuckDB 檔(.duckdb)", "required": True, "ext": [".duckdb", ".db"]},
                {"key": "read_only", "type": "bool", "label": "唯讀", "default": True, "flag": "--read-only"}]},
    {"id": "postgres", "name": "PostgreSQL", "group": "資料庫", "safety": 4, "free": True, "open_source": True,
     "maintainer": "官方(封存版)", "local_only": True, "recommended": False,
     "desc": "大型專案;連線字串視為秘密",
     "runner": "npx", "package": "@modelcontextprotocol/server-postgres", "args": [],
     "secrets": [{"env": "POSTGRES_URL", "store_key": "VIA_POSTGRES_URL", "label": "連線字串", "as_arg": True}],
     "params": []},
    # ── 雲端硬碟 ──
    {"id": "onedrive", "name": "OneDrive / M365", "group": "雲端硬碟", "safety": 4, "free": True, "open_source": True,
     "maintainer": "社群(Softeria ms-365-mcp-server)", "local_only": False, "recommended": True,
     "desc": "OneDrive · SharePoint · Outlook · Teams(Microsoft Graph,裝置碼登入)",
     "runner": "npx", "package": "@softeria/ms-365-mcp-server", "args": [],
     "params": [{"key": "read_only", "type": "bool", "label": "唯讀", "default": True, "flag": "--read-only"},
                {"key": "org_mode", "type": "bool", "label": "組織帳號(工作/學校)", "default": False, "flag": "--org-mode"}]},
    {"id": "gdrive", "name": "Google Drive", "group": "雲端硬碟", "safety": 4, "free": True, "open_source": True,
     "maintainer": "官方(封存版)", "local_only": False, "recommended": True,
     "desc": "Drive 搜尋與讀取(OAuth 憑證檔放本機)",
     "runner": "npx", "package": "@modelcontextprotocol/server-gdrive", "args": [],
     "params": [{"key": "credentials", "type": "file", "label": "OAuth 憑證 JSON", "required": False,
                 "env": "GDRIVE_CREDENTIALS_PATH", "ext": [".json"]}]},
    {"id": "dropbox", "name": "Dropbox", "group": "雲端硬碟", "safety": 3, "free": True, "open_source": True,
     "maintainer": "社群", "local_only": False, "recommended": False,
     "desc": "備份與跨平台同步;社群維護,先驗再用",
     "runner": "npx", "package": "dropbox-mcp-server", "args": [],
     "secrets": [{"env": "DROPBOX_ACCESS_TOKEN", "store_key": "VIA_DROPBOX_TOKEN", "label": "Dropbox Token"}],
     "params": []},
    # ── 知識庫 ──
    {"id": "obsidian", "name": "Obsidian", "group": "知識庫", "safety": 5, "free": True, "open_source": True,
     "maintainer": "社群(mcp-obsidian)", "local_only": True, "recommended": True,
     "desc": "資料完全本機(需 Obsidian Local REST API 外掛)",
     "runner": "uvx", "package": "mcp-obsidian", "args": [],
     "secrets": [{"env": "OBSIDIAN_API_KEY", "store_key": "VIA_OBSIDIAN_KEY", "label": "Local REST API Key"}],
     "params": []},
    {"id": "notion", "name": "Notion", "group": "知識庫", "safety": 4, "free": True, "open_source": True,
     "maintainer": "官方(Notion)", "local_only": False, "recommended": False,
     "desc": "Notion 頁面與資料庫",
     "runner": "npx", "package": "@notionhq/notion-mcp-server", "args": [],
     "secrets": [{"env": "NOTION_TOKEN", "store_key": "VIA_NOTION_TOKEN", "label": "Notion Integration Token"}],
     "params": []},
    # ── 搜尋 / 瀏覽 ──
    {"id": "brave-search", "name": "Brave Search", "group": "搜尋", "safety": 4, "free": True, "open_source": True,
     "maintainer": "官方(封存版)", "local_only": False, "recommended": False,
     "desc": "網頁搜尋(免費額度)",
     "runner": "npx", "package": "@modelcontextprotocol/server-brave-search", "args": [],
     "secrets": [{"env": "BRAVE_API_KEY", "store_key": "VIA_BRAVE_KEY", "label": "Brave API Key"}], "params": []},
    {"id": "playwright", "name": "Playwright", "group": "搜尋", "safety": 4, "free": True, "open_source": True,
     "maintainer": "官方(Microsoft)", "local_only": False, "recommended": False,
     "desc": "瀏覽器自動化(網頁截圖、表單)",
     "runner": "npx", "package": "@playwright/mcp", "args": ["--headless"], "params": []},
    # ── 不建議(權限過大 / API 常變 / 第三方維護) ──
    {"id": "discord", "name": "Discord", "group": "不建議", "safety": 3, "free": True, "open_source": True,
     "maintainer": "社群", "local_only": False, "recommended": False, "desc": "權限過大;只在隔離帳號使用",
     "runner": "npx", "package": "mcp-discord", "args": [],
     "secrets": [{"env": "DISCORD_TOKEN", "store_key": "VIA_DISCORD_TOKEN", "label": "Bot Token"}], "params": []},
    {"id": "telegram", "name": "Telegram", "group": "不建議", "safety": 3, "free": True, "open_source": True,
     "maintainer": "社群", "local_only": False, "recommended": False, "desc": "API 常變;第三方維護",
     "runner": "npx", "package": "mcp-telegram", "args": [],
     "secrets": [{"env": "TELEGRAM_BOT_TOKEN", "store_key": "VIA_TELEGRAM_TOKEN", "label": "Bot Token"}], "params": []},
]
CATALOG_BY_ID = {c["id"]: c for c in CATALOG}
GROUP_ORDER = ["核心", "資料庫", "雲端硬碟", "知識庫", "搜尋", "不建議"]


# ────────────────────────────────────────────────────────────────────────────
# 資料:AI 平台(mode = local 寫設定檔 · paste 產 JSON 貼上 · remote 只收遠端 URL 需橋接 · none 無 MCP 入口)
# ────────────────────────────────────────────────────────────────────────────
PLATFORMS: List[Dict[str, Any]] = [
    {"id": "claude-desktop", "name": "Claude Desktop / Cowork", "vendor": "Anthropic", "mode": "local",
     "format": "mcp_json", "root_key": "mcpServers", "scope": "user",
     "config_path": {"Windows": "%APPDATA%/Claude/claude_desktop_config.json",
                     "Darwin": "~/Library/Application Support/Claude/claude_desktop_config.json",
                     "Linux": "~/.config/Claude/claude_desktop_config.json"},
     "note": "Cowork 與 Desktop 共用同一份設定;改完重啟 Claude Desktop"},
    {"id": "claude-code", "name": "Claude Code", "vendor": "Anthropic", "mode": "local",
     "format": "mcp_json", "root_key": "mcpServers", "scope": "project",
     "config_path": "{project}/.mcp.json", "note": "專案層 .mcp.json(可進 git,因此秘密一律走包裝器)"},
    {"id": "claude-design", "name": "Claude Design(claude.ai)", "vendor": "Anthropic", "mode": "remote",
     "note": "只收遠端 MCP(HTTPS URL):在 claude.ai → 設定 → 連接器 貼上橋接 URL"},
    {"id": "chatgpt-codex", "name": "ChatGPT Codex(CLI / IDE)", "vendor": "OpenAI", "mode": "local",
     "format": "codex_toml", "root_key": "mcp_servers", "scope": "user",
     "config_path": "~/.codex/config.toml", "note": "TOML [mcp_servers.<名>];Codex 雲端版另需遠端 URL"},
    {"id": "chatgpt-chat", "name": "ChatGPT Chat / Projects", "vendor": "OpenAI", "mode": "remote",
     "note": "連接器需遠端 MCP(開發者模式):用橋接把本機 MCP 變成 HTTPS URL"},
    {"id": "copilot-vscode", "name": "Copilot Chat / Notebook(VS Code)", "vendor": "Microsoft", "mode": "local",
     "format": "vscode_json", "root_key": "servers", "scope": "project",
     "config_path": "{project}/.vscode/mcp.json", "note": "秘密走 inputs(password:true),VS Code 會加密保存"},
    {"id": "copilot-web", "name": "Copilot Chat(github.com)", "vendor": "Microsoft", "mode": "remote",
     "note": "只收遠端 MCP;本機 MCP 需橋接"},
    {"id": "gemini-cli", "name": "Gemini CLI / Code Assist", "vendor": "Google", "mode": "local",
     "format": "mcp_json", "root_key": "mcpServers", "scope": "user",
     "config_path": "~/.gemini/settings.json", "note": "settings.json 內的 mcpServers 區段"},
    {"id": "gemini-chat", "name": "Gemini Chat / NotebookLM", "vendor": "Google", "mode": "none",
     "note": "目前無 MCP 入口;以 Google Drive 共用資料夾作為替代"},
    {"id": "manus", "name": "Manus", "vendor": "其他", "mode": "remote",
     "note": "在 Manus 設定加入遠端 MCP URL;本機 MCP 需橋接"},
    {"id": "perplexity", "name": "Perplexity(桌面版)", "vendor": "其他", "mode": "paste",
     "format": "mcp_json", "root_key": "mcpServers",
     "note": "設定 → 連接器 → 進階,貼上產生的 JSON(mcpServers 格式)"},
    {"id": "cursor", "name": "Cursor", "vendor": "其他", "mode": "local",
     "format": "mcp_json", "root_key": "mcpServers", "scope": "user", "config_path": "~/.cursor/mcp.json"},
    {"id": "windsurf", "name": "Windsurf", "vendor": "其他", "mode": "local",
     "format": "mcp_json", "root_key": "mcpServers", "scope": "user",
     "config_path": "~/.codeium/windsurf/mcp_config.json"},
]
PLATFORM_BY_ID = {p["id"]: p for p in PLATFORMS}
VENDOR_ORDER = ["Anthropic", "OpenAI", "Microsoft", "Google", "其他"]


# ────────────────────────────────────────────────────────────────────────────
# 環境偵測(自適應的根)
# ────────────────────────────────────────────────────────────────────────────
def detect_tools() -> Dict[str, Any]:
    tools: Dict[str, Any] = {}
    for name, args in (("node", ["node", "-v"]), ("npx", ["npx", "-v"]), ("uvx", ["uvx", "--version"]),
                       ("uv", ["uv", "--version"]), ("docker", ["docker", "--version"]),
                       ("git", ["git", "--version"]), ("python", [sys.executable, "--version"]),
                       ("pwsh", ["pwsh", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"]),
                       ("powershell", ["powershell", "-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"]),
                       ("github-mcp-server", ["github-mcp-server", "--version"])):
        path = which(args[0]) if args[0] != sys.executable else sys.executable
        entry: Dict[str, Any] = {"found": bool(path), "path": path, "version": None}
        if path and os.environ.get("VIA_MCP_SKIP_VERSIONS") != "1":
            rc, out = run_quiet(args)
            if rc == 0:
                entry["version"] = out.splitlines()[0][:60] if out else ""
        tools[name] = entry
    return tools


def detect_secret_store() -> Dict[str, Any]:
    o = os_name()
    if o == "Windows":
        return {"kind": "credman", "label": "Windows 憑證管理員(cmdkey / CredentialManager 模組)",
                "available": bool(which("cmdkey")) or bool(which("powershell")) or bool(which("pwsh"))}
    if o == "Darwin":
        return {"kind": "keychain", "label": "macOS Keychain(security)", "available": bool(which("security"))}
    return {"kind": "secret-tool", "label": "libsecret(secret-tool)", "available": bool(which("secret-tool"))}


def platform_config_path(p: Dict[str, Any], project: Optional[str]) -> Optional[Path]:
    cp = p.get("config_path")
    if not cp:
        return None
    if isinstance(cp, dict):
        cp = cp.get(os_name()) or cp.get("Linux")
    return expand_path(cp, project)


def doctor(project: Optional[str] = None) -> Dict[str, Any]:
    tools = detect_tools()
    plats = []
    for p in PLATFORMS:
        path = platform_config_path(p, project)
        plats.append({"id": p["id"], "config_path": str(path) if path else None,
                      "exists": bool(path and path.exists())})
    runners = {"npx": tools["npx"]["found"], "uvx": tools["uvx"]["found"], "docker": tools["docker"]["found"],
               "binary": tools["github-mcp-server"]["found"]}
    return {"engine": ENGINE_NAME, "version": VERSION, "at": now_iso(), "os": os_name(),
            "os_release": _platform.release(), "python": sys.version.split()[0], "home": str(home()),
            "engine_home": str(engine_home()), "tools": tools, "runners": runners,
            "secret_store": detect_secret_store(), "platform_configs": plats,
            "suggested_folders": suggested_folders()}


def suggested_folders() -> List[str]:
    h = home()
    cands = [h / "Documents", h / "Projects", h / "Research", Path("D:/Research"), Path("D:/Projects"), h / "OneDrive",
             h / "Dropbox", h / "Google Drive", h / "Desktop", h]
    out: List[str] = []
    unreadable: List[str] = []
    for c in cands:
        try:
            if c.exists() and c.is_dir() and str(c) not in out:
                out.append(str(c))
        except OSError as e:  # 例:斷線的網路磁碟 — 記下來,不中斷偵測
            unreadable.append(f"{c}:{e.__class__.__name__}")
    if unreadable and os.environ.get("VIA_MCP_VERBOSE") == "1":
        print("[doctor] 跳過無法讀取的候選夾:" + " · ".join(unreadable), file=sys.stderr)
    return out


# ────────────────────────────────────────────────────────────────────────────
# 狀態(state.json):專案夾 · 每平台的指派(≤5)· 秘密模式
# ────────────────────────────────────────────────────────────────────────────
def state_path() -> Path:
    return engine_home() / "state.json"


def load_state() -> Dict[str, Any]:
    st = read_json(state_path(), None) or {}
    st.setdefault("schema", "VIA.MCP.ENGINE.STATE/1")
    st.setdefault("project_dir", str(home()))
    st.setdefault("assignments", {})
    st.setdefault("secret_mode", "auto")  # auto | wrapper | env | plain(拒絕)
    st.setdefault("history", [])
    return st


def save_state(st: Dict[str, Any]) -> None:
    st["updated_at"] = now_iso()
    state_path().write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def server_instance_name(server_id: str, params: Dict[str, Any], existing: List[str]) -> str:
    base = server_id
    name = base
    i = 2
    while name in existing:
        name = f"{base}-{i}"
        i += 1
    return name


def assign(st: Dict[str, Any], platform_id: str, server_id: str, params: Optional[Dict[str, Any]] = None,
           name: Optional[str] = None) -> Dict[str, Any]:
    if platform_id not in PLATFORM_BY_ID:
        raise ValueError(f"未知平台:{platform_id}")
    if server_id not in CATALOG_BY_ID:
        raise ValueError(f"未知 MCP:{server_id}")
    p = PLATFORM_BY_ID[platform_id]
    if p["mode"] == "none":
        raise ValueError(f"{p['name']} 目前沒有 MCP 入口,無法加入")
    lst: List[Dict[str, Any]] = st["assignments"].setdefault(platform_id, [])
    if len(lst) >= MAX_SERVERS_PER_PLATFORM:
        raise ValueError(f"{p['name']} 已達上限 {MAX_SERVERS_PER_PLATFORM} 個 MCP,請先移除一個")
    params = dict(params or {})
    cat = CATALOG_BY_ID[server_id]
    for prm in cat.get("params", []):
        if prm.get("type") == "bool" and prm["key"] not in params and "default" in prm:
            params[prm["key"]] = prm["default"]
    names = [a["name"] for a in lst]
    inst = {"server_id": server_id, "name": name or server_instance_name(server_id, params, names),
            "params": params, "added_at": now_iso()}
    if inst["name"] in names:
        raise ValueError(f"名稱重複:{inst['name']}")
    lst.append(inst)
    st["history"].append({"at": inst["added_at"], "op": "add", "platform": platform_id, "name": inst["name"]})
    return inst


def unassign(st: Dict[str, Any], platform_id: str, name: str) -> bool:
    lst = st["assignments"].get(platform_id, [])
    before = len(lst)
    st["assignments"][platform_id] = [a for a in lst if a["name"] != name and a["server_id"] != name]
    removed = before != len(st["assignments"][platform_id])
    if removed:
        st["history"].append({"at": now_iso(), "op": "remove", "platform": platform_id, "name": name})
    return removed


def validate_params(cat: Dict[str, Any], params: Dict[str, Any]) -> List[str]:
    problems: List[str] = []
    for prm in cat.get("params", []):
        v = params.get(prm["key"])
        if prm.get("required") and (v is None or v == "" or v == []):
            problems.append(f"{cat['name']}:缺「{prm['label']}」")
        if prm.get("type") == "paths" and isinstance(v, str):
            params[prm["key"]] = [v]
    return problems


# ────────────────────────────────────────────────────────────────────────────
# 渲染:指派 → 各平台設定(含執行器自適應與秘密保護)
# ────────────────────────────────────────────────────────────────────────────
def pick_runner(cat: Dict[str, Any], runners: Dict[str, bool]) -> Tuple[str, Optional[str]]:
    """回傳 (runner, 警告)。有偏好但缺工具時自動退到可用的替代。"""
    want = cat["runner"]
    if runners.get(want):
        return want, None
    alt = cat.get("alt_runner")
    if alt and runners.get("binary") and alt.get("binary") and which(alt["binary"]):
        return "binary", f"{cat['name']}:缺 {want},改用本機二進位 {alt['binary']}"
    if want == "docker" and runners.get("npx") and cat.get("npm_fallback"):
        return "npx", f"{cat['name']}:缺 docker,改用 npx {cat['npm_fallback']}"
    return want, f"{cat['name']}:偏好執行器 {want} 未安裝 — 設定仍會寫出,請安裝 {want} 後再啟動"


def fill_args(cat: Dict[str, Any], params: Dict[str, Any]) -> Tuple[List[str], Dict[str, str]]:
    """把 {占位} 填入實際值;bool 參數轉成 flag 或 env。回傳 (args, env_from_params)。"""
    args: List[str] = []
    env: Dict[str, str] = {}
    for a in cat.get("args", []):
        m = re.fullmatch(r"\{(\w+)\}", a)
        if not m:
            args.append(a)
            continue
        key = m.group(1)
        v = params.get(key)
        if isinstance(v, list):
            args.extend(str(x) for x in v)
        elif v not in (None, ""):
            args.append(str(v))
    for prm in cat.get("params", []):
        v = params.get(prm["key"])
        if prm.get("type") == "bool":
            if v and prm.get("flag"):
                args.append(prm["flag"])
            if prm.get("env"):
                env[prm["env"]] = prm.get("true_value", "1") if v else prm.get("false_value", "0")
        elif prm.get("env") and v not in (None, "", []):
            env[prm["env"]] = str(v)
    return args, env


def base_command(cat: Dict[str, Any], runner: str, args: List[str], env_passthrough: List[str]) -> Tuple[str, List[str]]:
    if runner == "npx":
        return "npx", ["-y", cat["package"], *args]
    if runner == "uvx":
        return "uvx", [cat["package"], *args]
    if runner == "docker":
        dargs = ["run", "-i", "--rm"]
        for e in env_passthrough:
            dargs += ["-e", e]
        return "docker", [*dargs, cat["image"], *args]
    if runner == "binary":
        alt = cat.get("alt_runner", {})
        return alt.get("binary", cat["id"]), [*alt.get("args", []), *args]
    raise ValueError(f"未知執行器 {runner}")


def windows_wrap(command: str, args: List[str]) -> Tuple[str, List[str]]:
    """Windows 上 Claude Desktop 等直接 spawn npx/uvx 常失敗(.cmd shim),用 cmd /c 包起來。"""
    if command in ("npx", "uvx", "uv", "node"):
        return "cmd", ["/c", command, *args]
    return command, args


def wrapper_dir() -> Path:
    d = engine_home() / "wrappers"
    d.mkdir(parents=True, exist_ok=True)
    return d


def render_wrapper(name: str, command: str, args: List[str], secrets: List[Dict[str, str]], env: Dict[str, str],
                   target_os: Optional[str] = None) -> Tuple[Path, str]:
    """產生「從作業系統憑證庫取秘密 → 設 env → 啟動 MCP」的包裝器;秘密永不寫入檔案。"""
    o = target_os or os_name()
    if o == "Windows":
        path = wrapper_dir() / f"start-{name}.ps1"
        lines = ["# 由 VIA_MCP_Engine 產生 — 秘密只存在 Windows 憑證管理員,不在此檔、不在設定檔",
                 "$ErrorActionPreference = 'Stop'",
                 "Import-Module CredentialManager -ErrorAction Stop"]
        for s in secrets:
            lines += [f"$c = Get-StoredCredential -Target '{s['store_key']}'",
                      f"if (-not $c) {{ Write-Error '憑證管理員沒有 {s['store_key']}:先執行 cmdkey /generic:{s['store_key']} /user:via /pass:<秘密>' }}",
                      f"$env:{s['env']} = $c.GetNetworkCredential().Password"]
        for k, v in env.items():
            lines.append(f"$env:{k} = '{v}'")
        q = " ".join(_ps_quote(a) for a in args)
        lines.append(f"& {_ps_quote(command)} {q}".rstrip())
        lines.append("exit $LASTEXITCODE")
        text = "\r\n".join(lines) + "\r\n"
    else:
        path = wrapper_dir() / f"start-{name}.sh"
        lines = ["#!/usr/bin/env bash", "# 由 VIA_MCP_Engine 產生 — 秘密只存在系統憑證庫,不在此檔、不在設定檔",
                 "set -euo pipefail"]
        for s in secrets:
            if o == "Darwin":
                lines.append(f"export {s['env']}=\"$(security find-generic-password -s '{s['store_key']}' -w)\"")
            else:
                lines.append(f"export {s['env']}=\"${{{s['env']}:-$(secret-tool lookup service '{s['store_key']}')}}\"")
        for k, v in env.items():
            lines.append(f"export {k}={_sh_quote(v)}")
        lines.append("exec " + " ".join(_sh_quote(x) for x in [command, *args]))
        text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")
    if o != "Windows":
        try:
            path.chmod(0o700)
        except OSError as e:  # 某些掛載點不給 chmod — 包裝器仍可用,只是權限沒收緊
            print(f"[wrapper] 無法把 {path} 權限收緊為 700:{e}", file=sys.stderr)
    return path, text


def _ps_quote(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def _sh_quote(s: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_./:=@%+-]+", s or ""):
        return s
    return "'" + s.replace("'", "'\\''") + "'"


def render_server(cat: Dict[str, Any], inst: Dict[str, Any], platform: Dict[str, Any], env_info: Dict[str, Any],
                  secret_mode: str) -> Tuple[Dict[str, Any], List[str], Optional[Dict[str, Any]]]:
    """回傳 (通用 server 結構 {command,args,env,secrets}, 警告, 包裝器資訊)。"""
    warnings: List[str] = []
    runners = env_info["runners"]
    runner, warn = pick_runner(cat, runners)
    if warn:
        warnings.append(warn)
    params = dict(inst.get("params") or {})
    warnings.extend(validate_params(cat, params))
    args, env = fill_args(cat, params)
    secrets = list(cat.get("secrets", []))
    env_pass = [s["env"] for s in secrets] + list(env.keys())
    command, full_args = base_command(cat, runner, args, env_pass)
    target_os = env_info["os"]
    mode = secret_mode
    if mode == "auto":
        if platform["format"] == "vscode_json":
            mode = "inputs"
        elif secrets:
            mode = "wrapper" if env_info["secret_store"]["available"] else "env"
        else:
            mode = "none"
    wrapper_info = None
    if secrets and mode == "wrapper":
        wpath, _ = render_wrapper(inst["name"], command, full_args, secrets, env, target_os)
        if target_os == "Windows":
            command, full_args = "powershell", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(wpath)]
        else:
            command, full_args = str(wpath), []
        env = {}
        wrapper_info = {"path": str(wpath), "store_keys": [s["store_key"] for s in secrets],
                        "store": env_info["secret_store"]["kind"]}
    elif secrets and mode == "env":
        warnings.append(f"{cat['name']}:秘密 {', '.join(s['env'] for s in secrets)} 由作業系統環境變數提供,未寫入設定檔")
    elif secrets and mode == "plain":
        raise ValueError("拒絕:本引擎不把秘密明文寫進設定檔(secret_mode=plain)")
    if target_os == "Windows" and mode != "wrapper":
        command, full_args = windows_wrap(command, full_args)
    srv = {"command": command, "args": full_args, "env": env, "secrets": secrets, "runner": runner,
           "mode": mode, "server_id": cat["id"]}
    return srv, warnings, wrapper_info


def to_mcp_json(name: str, srv: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {"command": srv["command"], "args": srv["args"]}
    if srv["env"]:
        out["env"] = dict(srv["env"])
    return out


def to_vscode(name: str, srv: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    out: Dict[str, Any] = {"type": "stdio", "command": srv["command"], "args": list(srv["args"])}
    env = dict(srv["env"])
    inputs: List[Dict[str, Any]] = []
    if srv["mode"] == "inputs":
        for s in srv["secrets"]:
            iid = f"{name}-{s['env'].lower().replace('_', '-')}"
            inputs.append({"type": "promptString", "id": iid, "description": s.get("label", s["env"]), "password": True})
            env[s["env"]] = "${input:" + iid + "}"
    if env:
        out["env"] = env
    return out, inputs


def toml_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)  # TOML 基本字串與 JSON 字串逸出相容


def to_codex_toml_block(name: str, srv: Dict[str, Any]) -> str:
    lines = [f"[mcp_servers.{name}]", f"command = {toml_str(srv['command'])}",
             "args = [" + ", ".join(toml_str(a) for a in srv["args"]) + "]"]
    if srv["env"]:
        lines.append("env = { " + ", ".join(f"{k} = {toml_str(v)}" for k, v in srv["env"].items()) + " }")
    return "\n".join(lines) + "\n"


def bridge_command(name: str, srv: Dict[str, Any], port: int) -> str:
    """遠端平台(ChatGPT / Claude Design / Copilot web / Manus)用:把 stdio MCP 橋成 HTTP/SSE。"""
    inner = " ".join(_sh_quote(x) for x in [srv["command"], *srv["args"]])
    return (f"npx -y supergateway --stdio {_sh_quote(inner)} --port {port} --outputTransport streamableHttp"
            f"   # → http://127.0.0.1:{port}/mcp;雲端平台需再以 HTTPS 隧道(例:cloudflared tunnel)對外")


def render_platform(st: Dict[str, Any], platform_id: str, env_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    p = PLATFORM_BY_ID[platform_id]
    env_info = env_info or doctor(st.get("project_dir"))
    insts = st["assignments"].get(platform_id, [])
    warnings: List[str] = []
    wrappers: List[Dict[str, Any]] = []
    servers: Dict[str, Dict[str, Any]] = {}
    if len(insts) > MAX_SERVERS_PER_PLATFORM:
        warnings.append(f"超過上限 {MAX_SERVERS_PER_PLATFORM},只渲染前 {MAX_SERVERS_PER_PLATFORM} 個")
    for inst in insts[:MAX_SERVERS_PER_PLATFORM]:
        cat = CATALOG_BY_ID[inst["server_id"]]
        fmt = p.get("format", "mcp_json")
        srv, w, wi = render_server(cat, inst, {**p, "format": fmt}, env_info, st.get("secret_mode", "auto"))
        warnings.extend(w)
        if wi:
            wrappers.append({"name": inst["name"], **wi})
        servers[inst["name"]] = srv
    result: Dict[str, Any] = {"platform": p, "count": len(insts), "max": MAX_SERVERS_PER_PLATFORM,
                              "warnings": warnings, "wrappers": wrappers,
                              "config_path": None, "text": None, "paste_json": None, "bridge": None}
    if p["mode"] == "none":
        result["warnings"].append(p.get("note", "此平台無 MCP 入口"))
        return result
    if p["mode"] == "remote":
        port = 8900
        lines = []
        for name, srv in servers.items():
            lines.append(f"# {name}\n{bridge_command(name, srv, port)}")
            port += 1
        result["bridge"] = "\n\n".join(lines) if lines else "# 尚未加入任何 MCP"
        result["warnings"].append(p.get("note", ""))
        return result
    fmt = p.get("format", "mcp_json")
    if fmt == "codex_toml":
        result["text"] = "".join(to_codex_toml_block(n, s) + "\n" for n, s in servers.items())
    elif fmt == "vscode_json":
        body: Dict[str, Any] = {"servers": {}, "inputs": []}
        for n, s in servers.items():
            srv_json, inputs = to_vscode(n, s)
            body["servers"][n] = srv_json
            body["inputs"].extend(inputs)
        if not body["inputs"]:
            body.pop("inputs")
        result["text"] = json.dumps(body, ensure_ascii=False, indent=2) + "\n"
    else:
        body = {"mcpServers": {n: to_mcp_json(n, s) for n, s in servers.items()}}
        result["text"] = json.dumps(body, ensure_ascii=False, indent=2) + "\n"
        result["paste_json"] = result["text"]
    cp = platform_config_path(p, st.get("project_dir"))
    result["config_path"] = str(cp) if cp else None
    result["servers"] = {n: {k: v for k, v in s.items() if k != "secrets"} for n, s in servers.items()}
    return result


# ────────────────────────────────────────────────────────────────────────────
# 套用:合併進既有設定(保留別人的 server,只覆寫本引擎管理的名稱),先備份
# ────────────────────────────────────────────────────────────────────────────
def managed_names(st: Dict[str, Any], platform_id: str) -> List[str]:
    return list(st.setdefault("managed", {}).get(platform_id, []))


def apply_platform(st: Dict[str, Any], platform_id: str, dry_run: bool = False,
                   env_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    p = PLATFORM_BY_ID[platform_id]
    rendered = render_platform(st, platform_id, env_info)
    if p["mode"] != "local":
        rendered["applied"] = False
        rendered["reason"] = {"paste": "此平台以貼上 JSON 方式設定,不寫檔", "remote": "此平台只收遠端 URL,請用橋接指令",
                              "none": "此平台無 MCP 入口"}[p["mode"]]
        return rendered
    cp = Path(rendered["config_path"])
    fmt = p.get("format", "mcp_json")
    new_names = list((rendered.get("servers") or {}).keys())
    old_managed = managed_names(st, platform_id)
    backup_dir = engine_home() / "backups" / platform_id
    if fmt == "codex_toml":
        old_text = cp.read_text(encoding="utf-8") if cp.exists() else ""
        merged = merge_codex_toml(old_text, rendered["text"], set(old_managed) | set(new_names))
        total = len(re.findall(r"^\[mcp_servers\.", merged, flags=re.M))
    else:
        root_key = p["root_key"]
        existing = read_json(cp, {}) if cp.exists() else {}
        if not isinstance(existing, dict):
            raise ValueError(f"{cp} 頂層不是物件,拒絕合併")
        new_body = json.loads(rendered["text"])
        servers = dict(existing.get(root_key) or {})
        for n in old_managed:
            servers.pop(n, None)
        servers.update(new_body.get(root_key, {}))
        existing[root_key] = servers
        if fmt == "vscode_json":
            inputs = [i for i in (existing.get("inputs") or []) if not any(i.get("id", "").startswith(f"{n}-") for n in set(old_managed) | set(new_names))]
            inputs.extend(new_body.get("inputs", []))
            if inputs:
                existing["inputs"] = inputs
            else:
                existing.pop("inputs", None)
        merged = json.dumps(existing, ensure_ascii=False, indent=2) + "\n"
        total = len(servers)
    if total > MAX_SERVERS_PER_PLATFORM:
        rendered["warnings"].append(f"合併後此平台共 {total} 個 MCP(含非本引擎管理者),超過建議上限 {MAX_SERVERS_PER_PLATFORM}")
    rendered["merged_preview"] = merged
    rendered["dry_run"] = dry_run
    if dry_run:
        rendered["applied"] = False
        return rendered
    backup = write_text_with_backup(cp, merged, backup_dir)
    st.setdefault("managed", {})[platform_id] = new_names
    st["history"].append({"at": now_iso(), "op": "apply", "platform": platform_id, "path": str(cp),
                          "backup": str(backup) if backup else None, "names": new_names})
    rendered["applied"] = True
    rendered["backup"] = str(backup) if backup else None
    return rendered


def merge_codex_toml(old_text: str, new_blocks: str, replace_names: set) -> str:
    """移除舊檔中本引擎管理的 [mcp_servers.<名>] 區塊,把新區塊接在尾端。其餘內容原樣保留。"""
    out_lines: List[str] = []
    skipping = False
    for line in old_text.splitlines():
        m = re.match(r"^\s*\[(mcp_servers\.([A-Za-z0-9_\-\"']+))(\.[^\]]*)?\]\s*$", line)
        if m:
            name = m.group(2).strip("\"'")
            skipping = name in replace_names
            if skipping:
                continue
        elif re.match(r"^\s*\[", line):
            skipping = False
        if not skipping:
            out_lines.append(line)
    base = "\n".join(out_lines).rstrip("\n")
    if base:
        base += "\n\n"
    return base + f"# ── {ENGINE_NAME} 管理區段(自動產生,{now_iso()}) ──\n" + new_blocks


# ────────────────────────────────────────────────────────────────────────────
# GitHub Token:範圍檢查 + 唯讀驗證(讀成功、寫被拒;寫入意外成功就自動清理)
#   transport 可注入(selftest 用假傳輸,不連網)
# ────────────────────────────────────────────────────────────────────────────
Transport = Callable[[str, str, Optional[Dict[str, Any]], Dict[str, str]], Tuple[int, Dict[str, str], Any]]


def http_transport(method: str, url: str, body: Optional[Dict[str, Any]], headers: Dict[str, str]) -> Tuple[int, Dict[str, str], Any]:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read().decode("utf-8", "replace")
            hdrs = {k.lower(): v for k, v in resp.headers.items()}
            return resp.status, hdrs, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        hdrs = {k.lower(): v for k, v in (e.headers.items() if e.headers else [])}
        try:
            parsed = json.loads(raw) if raw.strip() else None
        except json.JSONDecodeError:
            parsed = {"message": raw[:200]}
        return e.code, hdrs, parsed
    except urllib.error.URLError as e:
        return 0, {}, {"message": f"網路錯誤:{e.reason}"}


def gh_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": USER_AGENT, "Content-Type": "application/json"}


def token_kind(token: str) -> str:
    if token.startswith("github_pat_"):
        return "fine-grained PAT"
    if token.startswith("ghp_"):
        return "classic PAT"
    if token.startswith("gho_"):
        return "OAuth token"
    if token.startswith("ghs_"):
        return "App installation token"
    if token.startswith("ghu_"):
        return "App user token"
    return "未知格式"


def resolve_token(source: str = "env", store_key: str = "GITHUB_PAT_READONLY", env_name: str = "GITHUB_PERSONAL_ACCESS_TOKEN",
                  pasted: Optional[str] = None) -> Tuple[Optional[str], str]:
    """從 env / 憑證庫 / 一次性貼上 取 Token。回傳 (token, 來源說明);Token 不落地。"""
    if source == "paste":
        return (pasted or "").strip() or None, "一次性貼上(不儲存)"
    if source == "store":
        o = os_name()
        if o == "Windows":
            ps = which("pwsh") or which("powershell")
            if not ps:
                return None, "找不到 PowerShell"
            rc, out = run_quiet([ps, "-NoProfile", "-Command",
                                 f"Import-Module CredentialManager; (Get-StoredCredential -Target '{store_key}').GetNetworkCredential().Password"], 20)
            return (out.strip() or None) if rc == 0 else None, f"Windows 憑證管理員 {store_key}"
        if o == "Darwin":
            rc, out = run_quiet(["security", "find-generic-password", "-s", store_key, "-w"], 20)
            return (out.strip() or None) if rc == 0 else None, f"macOS Keychain {store_key}"
        rc, out = run_quiet(["secret-tool", "lookup", "service", store_key], 20)
        return (out.strip() or None) if rc == 0 else None, f"secret-tool {store_key}"
    return (os.environ.get(env_name) or "").strip() or None, f"環境變數 {env_name}"


def token_check(token: str, transport: Transport = http_transport) -> Dict[str, Any]:
    h = gh_headers(token)
    status, hdrs, body = transport("GET", f"{GITHUB_API}/user", None, h)
    res: Dict[str, Any] = {"at": now_iso(), "token_masked": mask(token), "kind": token_kind(token), "ok": status == 200,
                           "status": status}
    if status != 200:
        res["error"] = (body or {}).get("message") if isinstance(body, dict) else str(body)
        return res
    res["login"] = (body or {}).get("login")
    scopes = hdrs.get("x-oauth-scopes", "")
    res["classic_scopes"] = [s.strip() for s in scopes.split(",") if s.strip()] if scopes else []
    res["expires"] = hdrs.get("github-authentication-token-expiration")
    res["rate_limit_remaining"] = hdrs.get("x-ratelimit-remaining")
    if res["kind"] == "classic PAT":
        write_scopes = {"repo", "public_repo", "write:packages", "delete_repo", "workflow", "admin:org", "write:org"}
        res["looks_readonly"] = not (set(res["classic_scopes"]) & write_scopes)
        res["advice"] = ("classic PAT 的 repo scope 一定含寫入;要唯讀請改用 Fine-grained PAT"
                         if not res["looks_readonly"] else "沒有寫入類 scope")
    elif res["kind"] == "fine-grained PAT":
        res["looks_readonly"] = None
        res["advice"] = "fine-grained PAT 不會在標頭揭露權限,請用「唯讀驗證」實測讀成功 / 寫被拒"
    else:
        res["looks_readonly"] = None
        res["advice"] = "非 PAT;用「唯讀驗證」實測"
    # 可見倉數(確認讀取)
    s2, _, b2 = transport("GET", f"{GITHUB_API}/user/repos?per_page=1&affiliation=owner", None, h)
    res["can_list_repos"] = s2 == 200
    return res


def list_repos(token: str, transport: Transport = http_transport, limit: int = 100) -> List[Dict[str, Any]]:
    s, _, b = transport("GET", f"{GITHUB_API}/user/repos?per_page={limit}&sort=updated&affiliation=owner,collaborator", None, gh_headers(token))
    if s != 200 or not isinstance(b, list):
        raise ValueError(f"列倉失敗 HTTP {s}:{(b or {}).get('message') if isinstance(b, dict) else b}")
    return [{"full_name": r.get("full_name"), "private": r.get("private"), "default_branch": r.get("default_branch", "main")} for r in b]


def readonly_test(token: str, repo: str, transport: Transport = http_transport, cleanup: bool = True) -> Dict[str, Any]:
    """對 repo 做讀 ✓ / 寫 ✗ 矩陣。寫入若意外成功(= Token 不是唯讀),自動關閉測試 Issue、刪除測試分支。"""
    h = gh_headers(token)
    base = f"{GITHUB_API}/repos/{repo}"
    tag = f"via-mcp-readonly-test-{stamp()}"
    rows: List[Dict[str, Any]] = []
    cleanup_log: List[str] = []

    def row(name: str, kind: str, status: int, body: Any, expect_ok: bool) -> bool:
        ok = (200 <= status < 300)
        passed = ok if expect_ok else (status in (401, 403, 404))
        msg = (body or {}).get("message") if isinstance(body, dict) else ""
        rows.append({"test": name, "kind": kind, "status": status, "expected": "成功" if expect_ok else "被拒",
                     "actual": "成功" if ok else "被拒", "pass": passed, "message": (msg or "")[:120]})
        return ok

    # ── 讀(應成功) ──
    s, _, b = transport("GET", base, None, h)
    row("讀取 Repository 資訊", "read", s, b, True)
    default_branch = (b or {}).get("default_branch", "main") if isinstance(b, dict) else "main"
    s, _, b = transport("GET", f"{base}/contents/README.md", None, h)
    rows.append({"test": "讀取 README.md", "kind": "read", "status": s, "expected": "成功", "actual": "成功" if s == 200 else "被拒/不存在",
                 "pass": s in (200, 404), "message": "404 = 倉內沒有 README,不算失敗" if s == 404 else ""})
    s, _, b = transport("GET", f"{base}/issues?per_page=5&state=all", None, h)
    row("列出 Issues", "read", s, b, True)
    s, _, b = transport("GET", f"{base}/pulls?per_page=5&state=all", None, h)
    row("列出 Pull Requests", "read", s, b, True)
    s, _, b = transport("GET", f"{base}/git/ref/heads/{urllib.parse.quote(default_branch)}", None, h)
    row(f"讀取分支 {default_branch} 的 SHA", "read", s, b, True)
    head_sha = ((b or {}).get("object") or {}).get("sha") if isinstance(b, dict) else None

    # ── 寫(應被拒) ──
    s, _, b = transport("POST", f"{base}/issues", {"title": f"[{tag}] 唯讀驗證用,可關閉", "body": "由 VIA_MCP_Engine 自動建立;若看到此 Issue 代表 Token 具寫入權。"}, h)
    issue_created = row("建立 Issue", "write", s, b, False)
    issue_number = (b or {}).get("number") if issue_created and isinstance(b, dict) else None
    branch_created = False
    if head_sha:
        s, _, b = transport("POST", f"{base}/git/refs", {"ref": f"refs/heads/{tag}", "sha": head_sha}, h)
        branch_created = row("建立分支", "write", s, b, False)
    else:
        rows.append({"test": "建立分支", "kind": "write", "status": 0, "expected": "被拒", "actual": "略過",
                     "pass": True, "message": "讀不到預設分支 SHA,無法嘗試"})
    s, _, b = transport("PUT", f"{base}/contents/{tag}.txt",
                        {"message": f"{tag}", "content": base64.b64encode(b"readonly test").decode(), "branch": tag if branch_created else default_branch}, h)
    file_created = row("新增檔案(Contents PUT)", "write", s, b, False)
    file_sha = (((b or {}).get("content") or {}).get("sha")) if file_created and isinstance(b, dict) else None

    # ── 清理(只在寫入意外成功時) ──
    if cleanup:
        if issue_number:
            s2, _, _ = transport("PATCH", f"{base}/issues/{issue_number}", {"state": "closed", "state_reason": "not_planned"}, h)
            cleanup_log.append(f"關閉測試 Issue #{issue_number}:{'完成' if 200 <= s2 < 300 else '失敗 ' + str(s2)}")
        if file_created and file_sha and not branch_created:
            s2, _, _ = transport("DELETE", f"{base}/contents/{tag}.txt", {"message": f"remove {tag}", "sha": file_sha, "branch": default_branch}, h)
            cleanup_log.append(f"刪除測試檔 {tag}.txt:{'完成' if 200 <= s2 < 300 else '失敗 ' + str(s2)}")
        if branch_created:
            s2, _, _ = transport("DELETE", f"{base}/git/refs/heads/{tag}", None, h)
            cleanup_log.append(f"刪除測試分支 {tag}:{'完成' if 200 <= s2 < 300 else '失敗 ' + str(s2)}")

    reads_ok = all(r["pass"] for r in rows if r["kind"] == "read")
    writes_rejected = all(r["pass"] for r in rows if r["kind"] == "write")
    verdict = "READONLY_OK" if reads_ok and writes_rejected else ("NOT_READONLY" if reads_ok else "READ_FAILED")
    return {"at": now_iso(), "repo": repo, "token_masked": mask(token), "kind": token_kind(token), "tag": tag,
            "rows": rows, "reads_ok": reads_ok, "writes_rejected": writes_rejected, "verdict": verdict,
            "cleanup": cleanup_log,
            "advice": {"READONLY_OK": "通過:AI 只能讀、不能改。",
                       "NOT_READONLY": "此 Token 具寫入權,不應交給 AI;測試痕跡已清理。請改發 Fine-grained PAT 只給 Contents/Metadata/Issues/PR 的 Read。",
                       "READ_FAILED": "連讀都失敗:Token 無效、過期,或未授權此倉。"}[verdict]}


def readonly_test_with_temp_repo(readonly_token: str, admin_token: str, owner: Optional[str] = None,
                                 transport: Transport = http_transport) -> Dict[str, Any]:
    """用 admin Token 建私有臨時倉 → 用唯讀 Token 跑矯陣 → 用 admin Token 刪臨時倉。"""
    ah = gh_headers(admin_token)
    s, _, me = transport("GET", f"{GITHUB_API}/user", None, ah)
    if s != 200:
        return {"error": "admin Token 無效", "status": s}
    owner = owner or me.get("login")
    name = f"via-mcp-readonly-test-{stamp()}"
    s, _, b = transport("POST", f"{GITHUB_API}/user/repos", {"name": name, "private": True, "auto_init": True,
                                                            "description": "VIA_MCP_Engine 唯讀驗證臨時倉,測後自刪"}, ah)
    if s not in (200, 201):
        return {"error": f"建臨時倉失敗 {s}:{(b or {}).get('message')}", "status": s}
    full = (b or {}).get("full_name") or f"{owner}/{name}"
    result: Dict[str, Any] = {}
    try:
        result = readonly_test(readonly_token, full, transport)
        result["temp_repo"] = full
        result["note"] = ("fine-grained PAT 若只授權「選定倉」,對新建臨時倉本來就是 404,"
                          "請把臨時倉加入 Token 的倉清單,或改對既有倉測")
    finally:
        s2, _, _ = transport("DELETE", f"{GITHUB_API}/repos/{full}", None, ah)
        result.setdefault("cleanup", []).append(
            f"刪除臨時倉 {full}:{'完成' if s2 == 204 else '失敗 ' + str(s2) + '(admin Token 需 delete_repo / Administration 權限)'}")
    return result


# ────────────────────────────────────────────────────────────────────────────
# probe:用渲染出的指令真的把 MCP server 跑起來(stdio JSON-RPC:initialize → initialized → tools/list)
# ────────────────────────────────────────────────────────────────────────────
def _redact(text: str, secrets: List[str]) -> str:
    for sv in secrets:
        if sv and len(sv) >= 6:
            text = text.replace(sv, mask(sv))
    return text


def probe_command(command: str, args: List[str], env: Dict[str, str], timeout: float = 90.0,
                  secret_values: Optional[List[str]] = None, cwd: Optional[str] = None) -> Dict[str, Any]:
    """啟動子行程,做 MCP 握手並列工具。回傳 ok / server / protocol / tools / stderr_tail / elapsed;不丟例外。"""
    import time
    import queue
    t0 = time.time()
    res: Dict[str, Any] = {"command": command, "args": args, "ok": False, "stage": "spawn", "tools": [], "tool_count": 0,
                           "server": None, "protocol": None, "stderr_tail": "", "elapsed": 0.0, "rc": None}
    full_env = dict(os.environ)
    full_env.update(env or {})
    secret_values = list(secret_values or [])
    try:
        proc = subprocess.Popen([command, *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=full_env, cwd=cwd or None, text=False)
    except (OSError, ValueError) as e:
        res["error"] = f"{type(e).__name__}: {e}"
        res["elapsed"] = round(time.time() - t0, 2)
        return res
    out_q: "queue.Queue[Optional[bytes]]" = queue.Queue()
    err_buf: List[bytes] = []

    def pump_out() -> None:
        assert proc.stdout is not None
        for line in iter(proc.stdout.readline, b""):
            out_q.put(line)
        out_q.put(None)

    def pump_err() -> None:
        assert proc.stderr is not None
        for line in iter(proc.stderr.readline, b""):
            err_buf.append(line)
            if sum(len(x) for x in err_buf) > 65536:
                del err_buf[0]

    threading.Thread(target=pump_out, daemon=True).start()
    threading.Thread(target=pump_err, daemon=True).start()

    def send(obj: Dict[str, Any]) -> bool:
        try:
            assert proc.stdin is not None
            proc.stdin.write((json.dumps(obj) + "\n").encode("utf-8"))
            proc.stdin.flush()
            return True
        except (OSError, ValueError):
            return False

    def recv(want_id: int) -> Optional[Dict[str, Any]]:
        deadline = t0 + timeout
        while time.time() < deadline:
            try:
                line = out_q.get(timeout=min(1.0, max(0.05, deadline - time.time())))
            except queue.Empty:
                if proc.poll() is not None and out_q.empty():
                    return None
                continue
            if line is None:
                return None
            try:
                msg = json.loads(line.decode("utf-8", "replace"))
            except json.JSONDecodeError:
                continue  # 有些 server 會往 stdout 印雜訊;只認 JSON 行
            if isinstance(msg, dict) and msg.get("id") == want_id:
                return msg
        return None

    try:
        res["stage"] = "initialize"
        if send({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                 "params": {"protocolVersion": PROBE_PROTOCOL, "capabilities": {},
                            "clientInfo": {"name": ENGINE_NAME, "version": VERSION}}}):
            init = recv(1)
            if init and "result" in init:
                r = init["result"]
                res["server"] = r.get("serverInfo")
                res["protocol"] = r.get("protocolVersion")
                send({"jsonrpc": "2.0", "method": "notifications/initialized"})
                res["stage"] = "tools/list"
                send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
                tl = recv(2)
                if tl and "result" in tl:
                    tools = tl["result"].get("tools") or []
                    res["tools"] = [t.get("name") for t in tools][:50]
                    res["tool_count"] = len(tools)
                    res["ok"] = True
                    res["stage"] = "done"
                elif tl and "error" in tl:
                    res["error"] = f"tools/list 錯誤:{tl['error']}"
                else:
                    res["error"] = "tools/list 逾時或無回應"
            elif init and "error" in init:
                res["error"] = f"initialize 錯誤:{init['error']}"
            else:
                res["error"] = "initialize 逾時或無回應(第一次 npx / uvx 會先下載套件,可拉長 --timeout)"
        else:
            res["error"] = "無法寫入子行程 stdin(可能立刻退出)"
    finally:
        try:
            if proc.stdin:
                proc.stdin.close()
        except OSError:
            res.setdefault("notes", []).append("stdin 關閉時子行程已結束")
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                res.setdefault("notes", []).append("子行程 kill 後仍未收尾")
        res["rc"] = proc.returncode
        tail = b"".join(err_buf[-30:]).decode("utf-8", "replace")
        res["stderr_tail"] = _redact(tail[-2000:], secret_values)
        res["elapsed"] = round(time.time() - t0, 2)
    return res


def probe_instance(st: Dict[str, Any], platform_id: str, name: str, timeout: float = 90.0,
                   env_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """對某平台已加入的一個 MCP 做 probe。秘密:先憑證庫、再環境變數;都沒有就照實回報缺秘密(仍嘗試啟動)。"""
    env_info = env_info or doctor(st.get("project_dir"))
    insts = [a for a in st["assignments"].get(platform_id, []) if a["name"] == name]
    if not insts:
        return {"ok": False, "error": f"{platform_id} 沒有 {name}"}
    inst = insts[0]
    cat = CATALOG_BY_ID[inst["server_id"]]
    p = PLATFORM_BY_ID[platform_id]
    fmt = p.get("format", "mcp_json")
    srv, warnings, _ = render_server(cat, inst, {**p, "format": fmt}, env_info, "env")  # probe 一律本行程注入,不經包裝器
    env = dict(srv["env"])
    secret_values: List[str] = []
    missing: List[str] = []
    for sec in cat.get("secrets", []):
        tok, _src = resolve_token("store", sec["store_key"], sec["env"])
        if not tok:
            tok, _src = resolve_token("env", sec["store_key"], sec["env"])
        if tok:
            env[sec["env"]] = tok
            secret_values.append(tok)
        else:
            missing.append(sec["env"])
    res = probe_command(srv["command"], srv["args"], env, timeout, secret_values)
    res.update({"platform": platform_id, "name": name, "server_id": cat["id"], "runner": srv["runner"],
                "warnings": warnings, "missing_secrets": missing, "at": now_iso()})
    res["args"] = [_redact(a, secret_values) for a in res["args"]]
    return res


# ────────────────────────────────────────────────────────────────────────────
# 資料夾瀏覽(滑鼠點選路徑用)
# ────────────────────────────────────────────────────────────────────────────
def browse(path: Optional[str], want_files: bool = False, exts: Optional[List[str]] = None) -> Dict[str, Any]:
    if not path:
        roots: List[str] = []
        if os_name() == "Windows":
            for d in "CDEFGH":
                if Path(f"{d}:/").exists():
                    roots.append(f"{d}:/")
        else:
            roots = ["/"]
        return {"path": None, "parent": None, "dirs": [{"name": r, "path": r} for r in roots],
                "files": [], "suggested": suggested_folders()}
    p = Path(path)
    if not p.exists() or not p.is_dir():
        raise ValueError(f"不是資料夾:{path}")
    dirs, files = [], []
    skipped = 0
    denied: Optional[str] = None
    try:
        for child in sorted(p.iterdir(), key=lambda c: c.name.lower()):
            if child.name.startswith(".") or child.name.startswith("$"):
                continue
            try:
                if child.is_dir():
                    dirs.append({"name": child.name, "path": str(child)})
                elif want_files and child.is_file():
                    if not exts or child.suffix.lower() in [e.lower() for e in exts]:
                        files.append({"name": child.name, "path": str(child)})
            except OSError:
                skipped += 1  # 壞捷徑 / 無權限的單一項目:算進 skipped 讓前端知道
    except PermissionError as e:
        denied = f"沒有權限列出此資料夾:{e.strerror or e}"
    parent = str(p.parent) if p.parent != p else None
    return {"path": str(p), "parent": parent, "dirs": dirs[:500], "files": files[:500], "skipped": skipped,
            "denied": denied, "suggested": suggested_folders()}


# ────────────────────────────────────────────────────────────────────────────
# HTTP API(只綁本機;前端 fetch 用)
# ────────────────────────────────────────────────────────────────────────────
class Api:
    """把狀態與鎖集中,Handler 只做路由。"""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self._env: Optional[Dict[str, Any]] = None

    def env(self, refresh: bool = False) -> Dict[str, Any]:
        if refresh or self._env is None:
            self._env = doctor(load_state().get("project_dir"))
        return self._env

    def state_payload(self) -> Dict[str, Any]:
        st = load_state()
        env = self.env()
        plats = []
        for p in PLATFORMS:
            cp = platform_config_path(p, st.get("project_dir"))
            plats.append({**p, "config_path_resolved": str(cp) if cp else None,
                          "config_exists": bool(cp and cp.exists()),
                          "assigned": st["assignments"].get(p["id"], []), "max": MAX_SERVERS_PER_PLATFORM})
        return {"engine": ENGINE_NAME, "version": VERSION, "max_per_platform": MAX_SERVERS_PER_PLATFORM,
                "state": {k: v for k, v in st.items() if k != "history"}, "env": env,
                "platforms": plats, "vendors": VENDOR_ORDER, "catalog": CATALOG, "groups": GROUP_ORDER}

    def handle(self, method: str, route: str, query: Dict[str, List[str]], body: Dict[str, Any]) -> Tuple[int, Any]:
        q = {k: v[0] for k, v in query.items()}
        with self.lock:
            if route == "/api/state" and method == "GET":
                return 200, self.state_payload()
            if route == "/api/doctor" and method == "GET":
                return 200, self.env(refresh=True)
            if route == "/api/browse" and method == "GET":
                exts = [e for e in (q.get("ext") or "").split(",") if e]
                return 200, browse(q.get("path") or None, q.get("files") == "1", exts or None)
            if route == "/api/project" and method == "POST":
                st = load_state()
                pd = body.get("project_dir")
                if not pd or not Path(pd).is_dir():
                    return 400, {"error": "專案資料夾不存在"}
                st["project_dir"] = pd
                save_state(st)
                self._env = None
                return 200, {"ok": True, "project_dir": pd}
            if route == "/api/secret-mode" and method == "POST":
                st = load_state()
                mode = body.get("mode", "auto")
                if mode not in ("auto", "wrapper", "env"):
                    return 400, {"error": "secret_mode 只接受 auto / wrapper / env(不接受明文)"}
                st["secret_mode"] = mode
                save_state(st)
                return 200, {"ok": True, "secret_mode": mode}
            if route == "/api/assign" and method == "POST":
                st = load_state()
                inst = assign(st, body["platform"], body["server"], body.get("params") or {}, body.get("name"))
                save_state(st)
                return 200, {"ok": True, "instance": inst, "count": len(st["assignments"][body["platform"]])}
            if route == "/api/update-params" and method == "POST":
                st = load_state()
                for a in st["assignments"].get(body["platform"], []):
                    if a["name"] == body["name"]:
                        a["params"] = body.get("params") or {}
                        save_state(st)
                        return 200, {"ok": True, "instance": a}
                return 404, {"error": "找不到該 MCP"}
            if route == "/api/remove" and method == "POST":
                st = load_state()
                ok = unassign(st, body["platform"], body["name"])
                save_state(st)
                return (200 if ok else 404), {"ok": ok}
            if route == "/api/clone" and method == "POST":
                st = load_state()
                src, dst = body["from"], body["to"]
                st["assignments"][dst] = []
                for a in st["assignments"].get(src, [])[:MAX_SERVERS_PER_PLATFORM]:
                    assign(st, dst, a["server_id"], copy.deepcopy(a["params"]), a["name"])
                save_state(st)
                return 200, {"ok": True, "count": len(st["assignments"][dst])}
            if route == "/api/render" and method == "GET":
                st = load_state()
                return 200, render_platform(st, q["platform"], self.env())
            if route == "/api/apply" and method == "POST":
                st = load_state()
                res = apply_platform(st, body["platform"], bool(body.get("dry_run")), self.env())
                save_state(st)
                return 200, res
            if route == "/api/token/check" and method == "POST":
                token, src = resolve_token(body.get("source", "env"), body.get("store_key", "GITHUB_PAT_READONLY"),
                                           body.get("env_name", "GITHUB_PERSONAL_ACCESS_TOKEN"), body.get("token"))
                if not token:
                    return 400, {"error": f"取不到 Token({src})"}
                res = token_check(token)
                res["source"] = src
                return 200, res
            if route == "/api/token/repos" and method == "POST":
                token, src = resolve_token(body.get("source", "env"), body.get("store_key", "GITHUB_PAT_READONLY"),
                                           body.get("env_name", "GITHUB_PERSONAL_ACCESS_TOKEN"), body.get("token"))
                if not token:
                    return 400, {"error": f"取不到 Token({src})"}
                return 200, {"repos": list_repos(token)}
            if route == "/api/token/readonly-test" and method == "POST":
                token, src = resolve_token(body.get("source", "env"), body.get("store_key", "GITHUB_PAT_READONLY"),
                                           body.get("env_name", "GITHUB_PERSONAL_ACCESS_TOKEN"), body.get("token"))
                if not token:
                    return 400, {"error": f"取不到 Token({src})"}
                if body.get("temp"):
                    admin = (os.environ.get("GITHUB_ADMIN_TOKEN") or body.get("admin_token") or "").strip()
                    if not admin:
                        return 400, {"error": "臨時倉模式需要 GITHUB_ADMIN_TOKEN(只用於建 / 刪臨時倉)"}
                    res = readonly_test_with_temp_repo(token, admin)
                else:
                    if not body.get("repo"):
                        return 400, {"error": "請選擇測試倉"}
                    res = readonly_test(token, body["repo"])
                res["source"] = src
                self._append_evidence("readonly_test", res)
                return 200, res
            if route == "/api/probe" and method == "POST":
                st = load_state()
                res = probe_instance(st, body["platform"], body["name"], float(body.get("timeout") or 90), self.env())
                self._append_evidence("probe", res)
                return 200, res
            if route == "/api/store-hint" and method == "GET":
                return 200, {"hints": store_hints(q.get("key", "GITHUB_PAT_READONLY"))}
            return 404, {"error": f"無此路徑 {method} {route}"}

    def _append_evidence(self, kind: str, payload: Dict[str, Any]) -> None:
        d = engine_home() / "evidence"
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{kind}_{stamp()}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def store_hints(key: str) -> Dict[str, str]:
    return {"Windows": f"cmdkey /generic:{key} /user:via /pass:<貼上 Token>    (PowerShell 需先 Install-Module CredentialManager -Scope CurrentUser)",
            "Darwin": f"security add-generic-password -s {key} -a via -w    (會提示輸入,不留在歷史)",
            "Linux": f"secret-tool store --label='{key}' service {key}    (會提示輸入)"}


API = Api()


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = USER_AGENT

    def log_message(self, fmt: str, *args: Any) -> None:  # 安靜;不把 query(可能含路徑)印到終端
        if os.environ.get("VIA_MCP_VERBOSE") == "1":
            super().log_message(fmt, *args)

    def _send(self, code: int, payload: Any, ctype: str = "application/json; charset=utf-8") -> None:
        data = payload if isinstance(payload, (bytes, bytearray)) else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(data)

    def _route(self, method: str) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        route = parsed.path
        if method == "GET" and route in ("/", "/index.html"):
            if not HTML_FILE.exists():
                self._send(500, {"error": f"找不到前端 {HTML_FILE.name}"})
                return
            self._send(200, HTML_FILE.read_bytes(), "text/html; charset=utf-8")
            return
        if not route.startswith("/api/"):
            self._send(404, {"error": "not found"})
            return
        # 同源保護:只接受本機來源(擋瀏覽器內其他網站打本 API)
        origin = self.headers.get("Origin")
        if origin and not re.match(r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$", origin):
            self._send(403, {"error": "forbidden origin"})
            return
        body: Dict[str, Any] = {}
        if method == "POST":
            n = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(n) if n else b""
            try:
                body = json.loads(raw.decode("utf-8")) if raw else {}
            except json.JSONDecodeError:
                self._send(400, {"error": "body 不是 JSON"})
                return
        try:
            code, payload = API.handle(method, route, urllib.parse.parse_qs(parsed.query), body)
        except (ValueError, KeyError) as e:
            code, payload = 400, {"error": str(e)}
        except Exception as e:  # noqa: BLE001 — 回給前端看,不讓伺服器死掉
            code, payload = 500, {"error": f"{type(e).__name__}: {e}"}
        self._send(code, payload)

    def do_GET(self) -> None:  # noqa: N802
        self._route("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._route("POST")


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve(port: int = 8765, open_browser: bool = True, host: str = "127.0.0.1") -> None:
    httpd = ThreadingServer((host, port), Handler)
    url = f"http://{host}:{httpd.server_address[1]}/"
    print(f"[{ENGINE_NAME} v{VERSION}] 前端:{url}  state:{state_path()}  (Ctrl+C 結束)")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已結束")
    finally:
        httpd.server_close()


# ────────────────────────────────────────────────────────────────────────────
# 自測(離線;用假 HOME 與假 GitHub 傳輸)
# ────────────────────────────────────────────────────────────────────────────
def _fake_github(readonly: bool) -> Transport:
    """模擬 GitHub:讀全 200;寫在 readonly 時 403、否則 201。記錄清理呼叫。"""
    calls: List[Tuple[str, str]] = []

    def t(method: str, url: str, body: Optional[Dict[str, Any]], headers: Dict[str, str]) -> Tuple[int, Dict[str, str], Any]:
        calls.append((method, url))
        path = url.replace(GITHUB_API, "")
        if method == "GET":
            if path == "/user":
                return 200, {"x-oauth-scopes": "" if readonly else "repo, read:org",
                             "github-authentication-token-expiration": "2027-01-01 00:00:00 UTC"}, {"login": "tony"}
            if path.startswith("/user/repos"):
                return 200, {}, [{"full_name": "tony/demo", "private": True, "default_branch": "main"}]
            if path.endswith("/git/ref/heads/main"):
                return 200, {}, {"object": {"sha": "a" * 40}}
            if path.endswith("/contents/README.md"):
                return 200, {}, {"name": "README.md"}
            if re.search(r"/repos/[^/]+/[^/]+$", path):
                return 200, {}, {"default_branch": "main", "full_name": path.split("/repos/")[1]}
            return 200, {}, []
        if readonly:
            return 403, {}, {"message": "Resource not accessible by personal access token"}
        if method == "POST" and path.endswith("/issues"):
            return 201, {}, {"number": 42}
        if method == "POST" and path.endswith("/git/refs"):
            return 201, {}, {"ref": body["ref"]}
        if method == "POST" and path == "/user/repos":
            return 201, {}, {"full_name": "tony/" + body["name"]}
        if method == "PUT":
            return 201, {}, {"content": {"sha": "b" * 40}}
        if method == "PATCH":
            return 200, {}, {"state": "closed"}
        if method == "DELETE":
            return 204, {}, None
        return 500, {}, {"message": "unexpected"}

    t.calls = calls  # type: ignore[attr-defined]
    return t


FAKE_MCP_SERVER = r'''
import json, sys, os
sys.stderr.write("fake-mcp booting with token " + os.environ.get("FAKE_TOKEN", "") + "\n"); sys.stderr.flush()
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    msg = json.loads(line)
    m, i = msg.get("method"), msg.get("id")
    if m == "initialize":
        out = {"jsonrpc": "2.0", "id": i, "result": {"protocolVersion": msg["params"]["protocolVersion"], "capabilities": {"tools": {}},
                                                     "serverInfo": {"name": "fake-mcp", "version": "9.9"}}}
    elif m == "tools/list":
        out = {"jsonrpc": "2.0", "id": i, "result": {"tools": [{"name": "read_file"}, {"name": "list_directory"}]}}
    elif i is None:
        continue
    else:
        out = {"jsonrpc": "2.0", "id": i, "error": {"code": -32601, "message": "no such method"}}
    sys.stdout.write(json.dumps(out) + "\n"); sys.stdout.flush()
'''
TOTAL_CHECKS = [0]


def selftest() -> int:
    fails: List[str] = []
    TOTAL_CHECKS[0] = 0

    def check(cond: bool, msg: str) -> None:
        TOTAL_CHECKS[0] += 1
        print(("  ✓ " if cond else "  ✗ ") + msg)
        if not cond:
            fails.append(msg)

    with tempfile.TemporaryDirectory() as td:
        fake_home = Path(td) / "home"
        (fake_home / "Documents").mkdir(parents=True)
        (fake_home / "Research").mkdir()
        (fake_home / "Research" / "factor.db").write_bytes(b"")
        os.environ["VIA_MCP_FAKE_HOME"] = str(fake_home)
        os.environ["VIA_MCP_HOME"] = str(Path(td) / "engine")
        os.environ["VIA_MCP_SKIP_VERSIONS"] = "1"
        print(f"[selftest] {ENGINE_NAME} {VERSION} · 假 HOME {fake_home}")

        print("[1] 目錄 / 平台資料完整性")
        check(len(CATALOG) >= 15 and len(set(c["id"] for c in CATALOG)) == len(CATALOG), f"目錄 {len(CATALOG)} 筆、id 不重複")
        check(all(c["group"] in GROUP_ORDER for c in CATALOG), "每筆目錄都有分組")
        check(all(p["vendor"] in VENDOR_ORDER for p in PLATFORMS), "每個平台都有廠商分類")
        check(all(p["mode"] in ("local", "paste", "remote", "none") for p in PLATFORMS), "平台 mode 合法")
        check(all((p["mode"] != "local") or p.get("config_path") for p in PLATFORMS), "local 平台都有設定檔路徑")

        print("[2] 環境偵測")
        env = doctor(str(fake_home))
        check(env["os"] in ("Windows", "Darwin", "Linux"), f"OS={env['os']}")
        check(str(fake_home / "Documents") in env["suggested_folders"], "建議資料夾含 Documents")
        check(all(pc["config_path"] for pc in env["platform_configs"] if PLATFORM_BY_ID[pc["id"]]["mode"] == "local"), "local 平台路徑已展開")

        print("[3] 指派 + 上限 5")
        st = load_state()
        st["project_dir"] = str(fake_home / "Research")
        assign(st, "claude-desktop", "filesystem", {"paths": [str(fake_home / "Research")]})
        assign(st, "claude-desktop", "memory")
        assign(st, "claude-desktop", "sqlite", {"db": str(fake_home / "Research" / "factor.db")})
        assign(st, "claude-desktop", "github")
        assign(st, "claude-desktop", "fetch")
        check(len(st["assignments"]["claude-desktop"]) == 5, "加滿 5 個")
        try:
            assign(st, "claude-desktop", "duckdb", {"db": "x.duckdb"})
            check(False, "第 6 個應被拒")
        except ValueError as e:
            check("上限" in str(e), f"第 6 個被拒:{e}")
        try:
            assign(st, "gemini-chat", "fetch")
            check(False, "無入口平台應被拒")
        except ValueError as e:
            check("入口" in str(e), f"gemini-chat 被拒:{e}")
        check(unassign(st, "claude-desktop", "fetch") and len(st["assignments"]["claude-desktop"]) == 4, "移除 fetch → 4")
        inst2 = assign(st, "claude-desktop", "filesystem", {"paths": [str(fake_home / "Documents")]})
        check(inst2["name"] == "filesystem-2", f"同種第二個自動命名 {inst2['name']}")
        save_state(st)

        print("[4] 渲染:mcp_json(Linux / Windows)")
        env_linux = {**env, "os": "Linux", "runners": {"npx": True, "uvx": True, "docker": True, "binary": False},
                     "secret_store": {"kind": "secret-tool", "available": True}}
        r = render_platform(st, "claude-desktop", env_linux)
        body = json.loads(r["text"])
        check(set(body["mcpServers"]) == {"filesystem", "memory", "sqlite", "github", "filesystem-2"}, "五個 server 都渲染")
        check(body["mcpServers"]["filesystem"]["args"][:2] == ["-y", "@modelcontextprotocol/server-filesystem"], "npx -y 套件 路徑")
        gh = body["mcpServers"]["github"]
        check(gh["command"].endswith("start-github.sh") and not gh.get("env"), "GitHub 走包裝器,設定檔無秘密")
        wtext = Path(gh["command"]).read_text(encoding="utf-8")
        check("secret-tool lookup" in wtext and "ghp_" not in wtext, "包裝器從 secret-tool 取 Token,無明文")
        check("GITHUB_READ_ONLY=1" in wtext, "唯讀旗標進包裝器")
        env_win = {**env_linux, "os": "Windows", "secret_store": {"kind": "credman", "available": True}}
        rw = render_platform(st, "claude-desktop", env_win)
        bw = json.loads(rw["text"])
        check(bw["mcpServers"]["memory"]["command"] == "cmd" and bw["mcpServers"]["memory"]["args"][:2] == ["/c", "npx"], "Windows 用 cmd /c npx 包")
        check(bw["mcpServers"]["github"]["command"] == "powershell" and bw["mcpServers"]["github"]["args"][-1].endswith(".ps1"), "Windows GitHub 走 .ps1 包裝器")
        ps = Path(bw["mcpServers"]["github"]["args"][-1]).read_text(encoding="utf-8")
        check("Get-StoredCredential -Target 'GITHUB_PAT_READONLY'" in ps, "ps1 從憑證管理員取 GITHUB_PAT_READONLY")
        env_no_docker = {**env_linux, "runners": {"npx": True, "uvx": True, "docker": False, "binary": False}}
        r2 = render_platform(st, "claude-desktop", env_no_docker)
        check(any("docker" in w for w in r2["warnings"]), "缺 docker 有警告但仍渲染")

        print("[5] 渲染:VS Code inputs · Codex TOML · 遠端橋接 · 貼上")
        for pid in ("copilot-vscode", "chatgpt-codex", "chatgpt-chat", "perplexity"):
            st["assignments"][pid] = []
            assign(st, pid, "github")
            assign(st, pid, "filesystem", {"paths": [str(fake_home / "Research")]})
        rv = render_platform(st, "copilot-vscode", env_linux)
        bv = json.loads(rv["text"])
        check(bv["servers"]["github"]["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"].startswith("${input:") and bv["inputs"][0]["password"] is True, "VS Code 秘密走 inputs password")
        check(bv["servers"]["filesystem"]["type"] == "stdio", "VS Code 格式 type=stdio")
        rc_ = render_platform(st, "chatgpt-codex", env_linux)
        import tomllib
        parsed = tomllib.loads(rc_["text"])
        check(set(parsed["mcp_servers"]) == {"github", "filesystem"}, "Codex TOML 可被 tomllib 解析")
        rr = render_platform(st, "chatgpt-chat", env_linux)
        check(rr["bridge"] and "supergateway" in rr["bridge"] and rr["text"] is None, "遠端平台給橋接指令不寫檔")
        rp = render_platform(st, "perplexity", env_linux)
        check(rp["paste_json"] and json.loads(rp["paste_json"])["mcpServers"], "貼上型平台給 mcpServers JSON")
        rn = render_platform(st, "gemini-chat", env_linux)
        check(rn["text"] is None and rn["warnings"], "無入口平台只給說明")

        print("[6] 套用:合併保留他人 server · 備份 · dry-run")
        cfg = platform_config_path(PLATFORM_BY_ID["claude-desktop"], None)
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(json.dumps({"mcpServers": {"someone-else": {"command": "x", "args": []}}, "other": 1}), encoding="utf-8")
        dry = apply_platform(st, "claude-desktop", dry_run=True, env_info=env_linux)
        check(dry["applied"] is False and "someone-else" in dry["merged_preview"], "dry-run 不寫、預覽含他人 server")
        check(json.loads(cfg.read_text(encoding="utf-8"))["mcpServers"].keys() == {"someone-else"}, "dry-run 後檔案未變")
        real = apply_platform(st, "claude-desktop", dry_run=False, env_info=env_linux)
        after = json.loads(cfg.read_text(encoding="utf-8"))
        check(real["applied"] and set(after["mcpServers"]) == {"someone-else", "filesystem", "memory", "sqlite", "github", "filesystem-2"} and after["other"] == 1, "真套用:合併且保留其他鍵")
        check(real["backup"] and Path(real["backup"]).exists(), "有備份檔")
        check(any("超過建議上限" in w for w in real["warnings"]), "合併後 6 個有超上限警告")
        unassign(st, "claude-desktop", "filesystem-2")
        real2 = apply_platform(st, "claude-desktop", dry_run=False, env_info=env_linux)
        after2 = json.loads(cfg.read_text(encoding="utf-8"))
        check("filesystem-2" not in after2["mcpServers"] and "someone-else" in after2["mcpServers"], "再套用移除本引擎已拿掉的,仍保留他人")
        tcfg = platform_config_path(PLATFORM_BY_ID["chatgpt-codex"], None)
        tcfg.parent.mkdir(parents=True, exist_ok=True)
        tcfg.write_text('model = "o4-mini"\n\n[mcp_servers.keep]\ncommand = "k"\nargs = []\n', encoding="utf-8")
        apply_platform(st, "chatgpt-codex", dry_run=False, env_info=env_linux)
        t2 = tomllib.loads(tcfg.read_text(encoding="utf-8"))
        check(t2["model"] == "o4-mini" and set(t2["mcp_servers"]) == {"keep", "github", "filesystem"}, "Codex TOML 合併保留 model 與 keep")
        apply_platform(st, "chatgpt-codex", dry_run=False, env_info=env_linux)
        t3 = tomllib.loads(tcfg.read_text(encoding="utf-8"))
        check(set(t3["mcp_servers"]) == {"keep", "github", "filesystem"}, "Codex TOML 重複套用不重複區塊")
        vcfg = platform_config_path(PLATFORM_BY_ID["copilot-vscode"], st["project_dir"])
        apply_platform(st, "copilot-vscode", dry_run=False, env_info=env_linux)
        apply_platform(st, "copilot-vscode", dry_run=False, env_info=env_linux)
        v2 = json.loads(vcfg.read_text(encoding="utf-8"))
        check(len(v2["inputs"]) == 1 and set(v2["servers"]) == {"github", "filesystem"}, "VS Code inputs 重複套用不累積")
        rp2 = apply_platform(st, "perplexity", dry_run=False, env_info=env_linux)
        check(rp2["applied"] is False and "貼上" in rp2["reason"], "貼上型平台 apply 不寫檔")
        save_state(st)

        print("[7] 秘密保護:拒絕明文")
        st["secret_mode"] = "plain"
        try:
            render_platform(st, "claude-desktop", env_linux)
            check(False, "plain 應被拒")
        except ValueError as e:
            check("拒絕" in str(e), "secret_mode=plain 被拒")
        st["secret_mode"] = "auto"

        print("[8] Token 檢查 / 唯讀驗證(假 GitHub)")
        ro = _fake_github(readonly=True)
        tc = token_check("github_pat_" + "x" * 30, ro)
        check(tc["ok"] and tc["kind"] == "fine-grained PAT" and tc["login"] == "tony" and tc["token_masked"].count("x") <= 8, "fine-grained 檢查 + 遮罩")
        tc2 = token_check("ghp_" + "y" * 36, _fake_github(readonly=False))
        check(tc2["kind"] == "classic PAT" and tc2["looks_readonly"] is False and "repo" in tc2["classic_scopes"], "classic repo scope 判為可寫")
        rt = readonly_test("github_pat_" + "x" * 30, "tony/demo", ro)
        check(rt["verdict"] == "READONLY_OK" and rt["reads_ok"] and rt["writes_rejected"] and not rt["cleanup"], f"唯讀 Token → {rt['verdict']},無需清理")
        rw_t = _fake_github(readonly=False)
        rt2 = readonly_test("ghp_" + "y" * 36, "tony/demo", rw_t)
        check(rt2["verdict"] == "NOT_READONLY", f"可寫 Token → {rt2['verdict']}")
        dels = [u for m, u in rw_t.calls if m == "DELETE"]
        patches = [u for m, u in rw_t.calls if m == "PATCH"]
        check(any("/git/refs/heads/via-mcp-readonly-test-" in u for u in dels) and any("/issues/42" in u for u in patches), "寫入成功後自動刪分支、關 Issue")
        check(len(rt2["cleanup"]) >= 2, f"清理紀錄 {len(rt2['cleanup'])} 筆")
        tmp = readonly_test_with_temp_repo("github_pat_" + "x" * 30, "ghp_admin" + "z" * 30, transport=rw_t)
        check(tmp.get("temp_repo", "").startswith("tony/via-mcp-readonly-test-") and any("刪除臨時倉" in c for c in tmp["cleanup"]), "臨時倉建→測→刪")
        check(not any(("x" * 30) in json.dumps(x) for x in (tc, rt, tmp)), "回報 JSON 不含完整 Token")

        print("[9] 資料夾瀏覽 / API 路由")
        b = browse(str(fake_home))
        check(any(d["name"] == "Research" for d in b["dirs"]), "browse 列出子資料夾")
        bf = browse(str(fake_home / "Research"), want_files=True, exts=[".db"])
        check(any(f["name"] == "factor.db" for f in bf["files"]), "browse 依副檔名列檔")
        api = Api()
        code, payload = api.handle("GET", "/api/state", {}, {})
        check(code == 200 and payload["max_per_platform"] == 5 and len(payload["platforms"]) == len(PLATFORMS), "/api/state")
        code, payload = api.handle("POST", "/api/secret-mode", {}, {"mode": "plain"})
        check(code == 400, "/api/secret-mode 拒絕 plain")
        code, payload = api.handle("POST", "/api/assign", {}, {"platform": "cursor", "server": "fetch"})
        check(code == 200 and payload["count"] == 1, "/api/assign")
        code, payload = api.handle("POST", "/api/clone", {}, {"from": "claude-desktop", "to": "windsurf"})
        check(code == 200 and payload["count"] == 4, "/api/clone 複製指派")
        code, payload = api.handle("GET", "/api/render", {"platform": ["windsurf"]}, {})
        check(code == 200 and payload["count"] == 4, "/api/render")
        code, payload = api.handle("GET", "/api/nope", {}, {})
        check(code == 404, "未知路徑 404")
        check(HTML_FILE.exists() and "VIA MCP Engine" in HTML_FILE.read_text(encoding="utf-8"), f"前端檔存在 {HTML_FILE.name}")
        check(HTML_FILE.stem == Path(__file__).stem and VERSION in Path(__file__).stem, f"前後端同 stem 同版號 {VERSION}")

        print("[10] probe:假 MCP server(stdio JSON-RPC)")
        fake = Path(td) / "fake_mcp.py"
        fake.write_text(FAKE_MCP_SERVER, encoding="utf-8")
        pr = probe_command(sys.executable, ["-I", str(fake)], {"FAKE_TOKEN": "sekrit-token-123456"}, timeout=20,
                           secret_values=["sekrit-token-123456"])
        check(pr["ok"] and pr["tool_count"] == 2 and pr["server"]["name"] == "fake-mcp" and pr["protocol"] == PROBE_PROTOCOL,
              f"握手 + tools/list:{pr.get('server')} 工具 {pr['tool_count']} · {pr['elapsed']}s")
        check("sekrit-token-123456" not in json.dumps(pr) and "sekr…3456" in pr["stderr_tail"], "stderr 回報把秘密遮掉")
        bad = probe_command(sys.executable, ["-I", "-c", "import sys; sys.exit(3)"], {}, timeout=5)
        check(not bad["ok"] and bad["rc"] == 3 and bad.get("error"), f"立刻退出的 server 照實回報:{bad.get('error')}")
        nf = probe_command("definitely-not-a-command-xyz", [], {}, timeout=5)
        check(not nf["ok"] and "FileNotFoundError" in (nf.get("error") or ""), "找不到指令照實回報")
        st = load_state()
        st["assignments"]["cursor"] = []
        assign(st, "cursor", "fetch")
        save_state(st)
        st["assignments"]["cursor"].append({"server_id": "github", "name": "github", "params": {"read_only": True}, "added_at": now_iso()})
        save_state(st)
        seen: Dict[str, Any] = {}

        def stub_probe(command, args, env, timeout=90.0, secret_values=None, cwd=None):
            seen.update(command=command, args=list(args), env=dict(env), secrets=list(secret_values or []))
            return {"command": command, "args": list(args), "ok": True, "tool_count": 1, "tools": ["x"], "server": {"name": "stub"},
                    "protocol": PROBE_PROTOCOL, "stderr_tail": "", "elapsed": 0.01, "rc": 0, "stage": "done"}

        real_probe = globals()["probe_command"]
        os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"] = "ghp_" + "q" * 36
        try:
            globals()["probe_command"] = stub_probe
            pi = probe_instance(st, "cursor", "fetch", 5, {**env_linux, "runners": {"npx": False, "uvx": False, "docker": False, "binary": False}})
            check(pi["name"] == "fetch" and pi["ok"] is True and any("uvx" in w for w in pi["warnings"]) and seen["command"] == "uvx",
                  "probe_instance 缺執行器:仍組出 uvx 指令、帶警告、不丟例外")
            pg = probe_instance(st, "cursor", "github", 5, env_linux)
            check(seen["env"].get("GITHUB_PERSONAL_ACCESS_TOKEN", "").startswith("ghp_") and seen["env"].get("GITHUB_READ_ONLY") == "1"
                  and pg["missing_secrets"] == [] and ("q" * 36) not in json.dumps(pg), "probe_instance 秘密由環境注入子行程、唯讀旗標在、回報不含秘密")
        finally:
            globals()["probe_command"] = real_probe
            os.environ.pop("GITHUB_PERSONAL_ACCESS_TOKEN", None)
        code, payload = api.handle("POST", "/api/probe", {}, {"platform": "cursor", "name": "nope"})
        check(code == 200 and payload["ok"] is False and "沒有" in payload["error"], "/api/probe 找不到項目照實回")

    for k in ("VIA_MCP_FAKE_HOME", "VIA_MCP_HOME", "VIA_MCP_SKIP_VERSIONS"):
        os.environ.pop(k, None)
    print(f"[selftest] {'PASS' if not fails else 'FAIL'} · 失敗 {len(fails)}")
    for f in fails:
        print("   -", f)
    print(f"[計] {ENGINE_NAME} {VERSION} 自測 {TOTAL_CHECKS[0] - len(fails)}/{TOTAL_CHECKS[0]} · {'PASS' if not fails else 'FAIL'}")
    return 0 if not fails else 1


# ────────────────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────────────────
def _kv(items: List[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for it in items:
        if "=" not in it:
            raise SystemExit(f"參數要 k=v:{it}")
        k, v = it.split("=", 1)
        if "," in v and k in ("paths",):
            out[k] = v.split(",")
        elif v.lower() in ("true", "false"):
            out[k] = v.lower() == "true"
        else:
            out[k] = v
    return out


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog=ENGINE_NAME, description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("serve", help="開前端(本機)")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--no-browser", action="store_true")
    sub.add_parser("doctor", help="環境偵測")
    sub.add_parser("platforms", help="列平台")
    sub.add_parser("catalog", help="列 MCP 目錄")
    a = sub.add_parser("add", help="加 MCP 到平台(上限 5)")
    a.add_argument("platform"); a.add_argument("server"); a.add_argument("kv", nargs="*")
    rm = sub.add_parser("remove", help="移除")
    rm.add_argument("platform"); rm.add_argument("name")
    ls = sub.add_parser("list", help="列目前指派")
    ap_ = sub.add_parser("apply", help="寫設定檔(先備份)")
    ap_.add_argument("platform"); ap_.add_argument("--dry-run", action="store_true")
    rd = sub.add_parser("render", help="只渲染不寫")
    rd.add_argument("platform")
    pj = sub.add_parser("project", help="設定專案資料夾(Claude Code / VS Code 用)")
    pj.add_argument("path")
    tk = sub.add_parser("token", help="GitHub Token 檢查 / 唯讀驗證")
    tk.add_argument("action", choices=["check", "readonly-test", "repos"])
    tk.add_argument("--repo"); tk.add_argument("--temp", action="store_true")
    tk.add_argument("--source", choices=["env", "store"], default="env")
    tk.add_argument("--store-key", default="GITHUB_PAT_READONLY")
    tk.add_argument("--no-cleanup", action="store_true")
    pb = sub.add_parser("probe", help="真啟動 MCP:initialize / tools/list")
    pb.add_argument("platform"); pb.add_argument("name", nargs="?"); pb.add_argument("--timeout", type=float, default=90)
    sub.add_parser("selftest", help="離線自測")
    sub.add_parser("version")
    raw = list(sys.argv[1:] if argv is None else argv)
    if raw == ["--selftest"]:                      # VCGC 慣例:run X --selftest 照路由給 X
        return selftest()
    ns = ap.parse_args(raw)

    if ns.cmd in (None, "serve"):
        serve(getattr(ns, "port", 8765), not getattr(ns, "no_browser", False), getattr(ns, "host", "127.0.0.1"))
        return 0
    if ns.cmd == "version":
        print(f"{ENGINE_NAME} {VERSION}"); return 0
    if ns.cmd == "selftest":
        return selftest()
    if ns.cmd == "doctor":
        print(json.dumps(doctor(load_state().get("project_dir")), ensure_ascii=False, indent=2)); return 0
    if ns.cmd == "platforms":
        for p in PLATFORMS:
            cp = platform_config_path(p, load_state().get("project_dir"))
            print(f"{p['id']:16} {p['mode']:6} {p['name']:34} {cp or p.get('note', '')}")
        return 0
    if ns.cmd == "catalog":
        for g in GROUP_ORDER:
            print(f"── {g}")
            for c in CATALOG:
                if c["group"] == g:
                    print(f"  {c['id']:20} {'★' * c['safety']:5} {c['runner']:6} {c.get('package') or c.get('image')}  {c['desc']}")
        return 0
    st = load_state()
    if ns.cmd == "project":
        if not Path(ns.path).is_dir():
            raise SystemExit("資料夾不存在")
        st["project_dir"] = str(Path(ns.path).resolve()); save_state(st); print("ok"); return 0
    if ns.cmd == "add":
        inst = assign(st, ns.platform, ns.server, _kv(ns.kv)); save_state(st)
        print(f"已加入 {inst['name']} → {ns.platform}({len(st['assignments'][ns.platform])}/{MAX_SERVERS_PER_PLATFORM})"); return 0
    if ns.cmd == "remove":
        ok = unassign(st, ns.platform, ns.name); save_state(st); print("已移除" if ok else "找不到"); return 0 if ok else 1
    if ns.cmd == "list":
        for pid, lst in st["assignments"].items():
            print(f"{pid}({len(lst)}/{MAX_SERVERS_PER_PLATFORM}):" + ", ".join(a["name"] for a in lst))
        return 0
    if ns.cmd == "render":
        print(json.dumps(render_platform(st, ns.platform), ensure_ascii=False, indent=2)); return 0
    if ns.cmd == "probe":
        names = [ns.name] if ns.name else [a["name"] for a in st["assignments"].get(ns.platform, [])]
        if not names:
            print("此平台沒有已加入的 MCP", file=sys.stderr); return 2
        worst = 0
        for n in names:
            r = probe_instance(st, ns.platform, n, ns.timeout)
            lamp = "GREEN" if r["ok"] else "RED"
            print(f"[probe] {ns.platform}/{n} {lamp} · {r.get('runner')} · 工具 {r['tool_count']} · {r['elapsed']}s"
                  + (f" · {r.get('error')}" if r.get("error") else "") + (f" · 缺秘密 {r['missing_secrets']}" if r.get("missing_secrets") else ""))
            if r["tools"]:
                print("        " + ", ".join(r["tools"][:12]) + (" …" if r["tool_count"] > 12 else ""))
            if r.get("stderr_tail") and not r["ok"]:
                print("        stderr: " + r["stderr_tail"].strip().splitlines()[-1][:160] if r["stderr_tail"].strip() else "")
            worst = max(worst, 0 if r["ok"] else 1)
        return worst
    if ns.cmd == "apply":
        res = apply_platform(st, ns.platform, ns.dry_run); save_state(st)
        print(json.dumps({k: v for k, v in res.items() if k in ("applied", "dry_run", "config_path", "backup", "warnings", "reason", "bridge", "paste_json")}, ensure_ascii=False, indent=2))
        if ns.dry_run:
            print(res.get("merged_preview") or res.get("text") or "")
        return 0
    if ns.cmd == "token":
        token, src = resolve_token(ns.source, ns.store_key)
        if not token:
            print(f"取不到 Token({src})", file=sys.stderr); return 2
        if ns.action == "check":
            print(json.dumps(token_check(token), ensure_ascii=False, indent=2)); return 0
        if ns.action == "repos":
            for r in list_repos(token):
                print(r["full_name"]); return 0
        if ns.temp:
            admin = os.environ.get("GITHUB_ADMIN_TOKEN", "").strip()
            if not admin:
                print("--temp 需要 GITHUB_ADMIN_TOKEN", file=sys.stderr); return 2
            res = readonly_test_with_temp_repo(token, admin)
        else:
            if not ns.repo:
                print("需要 --repo owner/name 或 --temp", file=sys.stderr); return 2
            res = readonly_test(token, ns.repo, cleanup=not ns.no_cleanup)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("verdict") == "READONLY_OK" else 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
