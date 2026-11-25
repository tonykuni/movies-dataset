#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL279_MCPServer v0107 — 薄尾(v0106 一字不動):加 `vcgc_read_card`(只回結構卡)

操作員 2026-11-25 20:32 裁定(架構規劃 v0101 待裁 14):「yes」。
VCGC MCP 原有 17 個工具全是治理類,外部 AI 經 MCP 讀不到任何檔。本版加第 18 個工具:
  vcgc_read_card {path, depth?}
    · 回 VCGC 省 Token 工具(鎖冊 token 那一支)`read` 的**骨架卡**:匯入 · 定義樹(行號 · 簽章 · 首行說明)· AST 問題;
      .json 兩層卡(depth 1~4)· .jsonl 欄位次數 · .md 標題樹 · .ps1 函式表。**不回全文、不給 slice**(slice 會回整段原始碼)。
    · 只收倉內(VIA 根之下)的程式檔與冊:.py .ps1 .psm1 .json .jsonl .md;單檔 ≤ 20 MB。
    · 一律拒絕:VIA 根以外 · VIA_Reports · 資料家 / 庫 / 湖 / 研報 / 收件 / 上傳夾 · .parquet .duckdb .db .sqlite .csv .xlsx .pdf 等資料檔
      → 符合「能離開本機的只有程式碼結構與 schema」。
    · 輸出上限 300 行;子行程 120 秒逾時;零寫入 · 零網路 · 不 import 他系統 · 不讀寫同意閘。
其餘 17 個工具與資源照 v0106。用法同前:--serve [--root] · --client-config [--root] · --selftest。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import io
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

NAME = "CGC_MDL279_MCPServer"
VERSION = "v0107"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_FILE = max((p for p in HERE.glob(NAME + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if _PRIOR_FILE.stem in sys.modules:
    PRIOR = sys.modules[_PRIOR_FILE.stem]
else:
    _spec = importlib.util.spec_from_file_location(_PRIOR_FILE.stem, _PRIOR_FILE)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[_PRIOR_FILE.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)
P0 = PRIOR.P0

TOOL = "vcgc_read_card"
ALLOW_EXT = {".py", ".ps1", ".psm1", ".json", ".jsonl", ".md"}
DENY_PARTS = {"via_reports", "data", "datahome", "data_home", "database", "via_database", "db", "lake", "datalake",
              "research", "reports", "研報", "inbox", "intake", "uploads", "raw", "cache", ".git", "node_modules"}
MAX_BYTES = 20 * 1024 * 1024
MAX_LINES = 300
_ORIG_CALL = P0.Server.call
_ORIG_SPECS = P0.tool_specs


def token_tool(via: Path):
    """鎖冊 token 那一支(倉根相對路徑);找不到回 None。"""
    try:
        lk = json.loads((via / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))
        rel = (lk.get("token") or {}).get("path", "")
    except (OSError, ValueError):
        return None
    p = via.parent / rel
    return p if rel and p.is_file() else None


def check_path(via: Path, rel: str):
    """回 (Path, None) 或 (None, 拒絕原因)。"""
    if not rel or not isinstance(rel, str):
        return None, "path 必填(VIA 根之下的相對路徑)"
    root = Path(via).resolve()
    try:
        p = (root / rel).resolve()
        p.relative_to(root)
    except (ValueError, OSError):
        return None, "拒絕:在 VIA 根以外"
    parts = {x.lower() for x in p.relative_to(root).parts[:-1]}
    hit = sorted(parts & DENY_PARTS)
    if hit:
        return None, "拒絕:資料 / 報告類資料夾(%s)— 只有程式碼結構與 schema 能離開本機" % "、".join(hit)
    if p.suffix.lower() not in ALLOW_EXT:
        return None, "拒絕:只收 %s(%s 不收)" % (" ".join(sorted(ALLOW_EXT)), p.suffix or "無副檔名")
    if not p.is_file():
        return None, "找不到檔案"
    if p.stat().st_size > MAX_BYTES:
        return None, "拒絕:檔案超過 20 MB"
    return p, None


def read_card(via: Path, rel: str, depth=None) -> dict:
    p, why = check_path(via, rel)
    if p is None:
        return {"content": [{"type": "text", "text": why}], "isError": True}
    tool = token_tool(Path(via))
    if tool is None:
        return {"content": [{"type": "text", "text": "找不到鎖冊 token 工具"}], "isError": True}
    argv = [sys.executable, "-B", str(tool), "read", str(p)]
    if depth is not None:
        if type(depth) is not int or not 1 <= depth <= 4:
            return {"content": [{"type": "text", "text": "depth 要 1~4 的整數"}], "isError": True}
        argv += ["--depth", str(depth)]
    try:
        r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
                           cwd=str(Path(via).parent), env={"PYTHONUTF8": "1", "PATH": "", "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")})
    except subprocess.TimeoutExpired:
        return {"content": [{"type": "text", "text": "骨架卡逾時(120 秒)"}], "isError": True}
    lines = (r.stdout or "").splitlines()
    cut = len(lines) > MAX_LINES
    text = "\n".join(lines[:MAX_LINES]) + ("\n…(超過 %d 行,其餘略;用本機 read 看完整卡)" % MAX_LINES if cut else "")
    return {"content": [{"type": "text", "text": text}], "isError": r.returncode not in (0, 2),
            "structuredContent": {"path": str(p.relative_to(Path(via).resolve())), "lines": len(lines), "truncated": cut, "rc": r.returncode,
                                  "kind": "skeleton_card_only", "full_text_returned": False}}


def call(self, name: str, args: dict) -> dict:
    if name == TOOL:
        return read_card(self.via, (args or {}).get("path"), (args or {}).get("depth"))
    return _ORIG_CALL(self, name, args)


def tool_specs() -> list:
    specs = _ORIG_SPECS()
    if not any(t.get("name") == TOOL for t in specs):
        specs.append({"name": TOOL,
                      "description": "讀一個倉內程式檔 / 冊的骨架卡(VCGC 省 Token read:匯入 · 定義樹 · 行號 · 首行說明;JSON 兩層 · MD 標題樹)。"
                                     "只回結構、不回全文;資料 / 報告類夾與資料檔一律拒絕(v0107)",
                      "inputSchema": {"type": "object", "required": ["path"], "additionalProperties": False, "properties": {
                          "path": {"type": "string", "description": "VIA 根之下的相對路徑,例 supportive modules/registry/CGC_SystemManager_v0120.py"},
                          "depth": {"type": "integer", "minimum": 1, "maximum": 4, "description": ".json 看幾層(預設 2)"}}}})
    return specs


P0.Server.call = call
P0.tool_specs = tool_specs
P0.VERSION = VERSION


def client_config(via: Path) -> dict:
    cfg = PRIOR.client_config(via)
    text = json.dumps(cfg, ensure_ascii=False).replace(str(_PRIOR_FILE), str(Path(__file__).resolve())).replace(_PRIOR_FILE.name, Path(__file__).name)
    return json.loads(text)


def selftest() -> int:
    ok = []

    def chk(n, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + n + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print("[計] %s %s 自測開始(本版 8 項 · 前版 %s)" % (NAME, VERSION, _PRIOR_FILE.name), flush=True)
    via = P0.VIA_DEFAULT
    names = [t["name"] for t in P0.tool_specs()]
    chk("T1 工具表多一個 vcgc_read_card,其餘照舊(共 %d)" % len(names), TOOL in names and len(names) == len(_ORIG_SPECS()) + 1)
    card = read_card(via, "supportive modules/registry/" + Path(__file__).name)
    txt = card["content"][0]["text"]
    chk("T2 倉內 .py → 骨架卡(有定義樹、不是全文)", not card["isError"] and "def read_card" in txt and "MAX_BYTES = 20" not in txt, txt[:200])
    chk("T3 VIA 根以外 → 拒絕", read_card(via, "../../etc/passwd")["isError"])
    with tempfile.TemporaryDirectory(prefix="mcp107_") as td:
        fake = Path(td) / "VIA"
        for rel in ("VIA_Reports/x.py", "functional modules/VDF/data/y.json", "z.parquet", "docs/a.csv"):
            f = fake / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text("x = 1\n", encoding="utf-8")
        deny = [check_path(fake, r)[1] for r in ("VIA_Reports/x.py", "functional modules/VDF/data/y.json", "z.parquet", "docs/a.csv")]
        chk("T4 報告夾 · 資料夾 · .parquet · .csv 一律拒絕", all(d and d.startswith("拒絕") for d in deny), deny)
    md = read_card(via, "docs/handoff/VCGC_ToolManual_v0102.md")
    chk("T5 .md → 標題樹", not md["isError"] and "h2" in md["content"][0]["text"], md["content"][0]["text"][:160])
    chk("T6 depth 只收 1~4 的整數", read_card(via, "supportive modules/registry/VIA_ToolVersion_Lock_v0100.json", depth=9)["isError"])
    inp = io.StringIO("\n".join(json.dumps(m) for m in (
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": TOOL, "arguments": {"path": "supportive modules/registry/" + Path(__file__).name}}})) + "\n")
    out = io.StringIO()
    P0.serve(via, P0.find_console(via), inp, out)
    resp = [json.loads(x) for x in out.getvalue().splitlines() if x.strip()]
    listed = [t["name"] for t in (resp[1].get("result") or {}).get("tools", [])] if len(resp) > 1 else []
    called = (resp[2].get("result") or {}) if len(resp) > 2 else {}
    chk("T7 stdio 握手:tools/list 有它 · tools/call 回骨架卡", TOOL in listed and not called.get("isError") and "def read_card" in json.dumps(called, ensure_ascii=False), resp[-1:])
    src = Path(__file__).read_text(encoding="utf-8")
    prc = subprocess.run([sys.executable, "-B", str(_PRIOR_FILE), "--selftest"], capture_output=True, text=True,
                         encoding="utf-8", errors="replace", timeout=600).returncode   # 子行程:前版看不到本版加的工具
    chk("T8 第 3 行加速器標記且載入生效(VIA_ACCEL 非空)· 零 TA-Lib · 不 import 他系統 · 前版 %s 自測照過" % _PRIOR_FILE.name,
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*(import|from)\s+(VDF|VRN|VQG|VAP)", src, re.M) and prc == 0 and VIA_ACCEL is not None,
        "前版 rc %s · VIA_ACCEL %s" % (prc, VIA_ACCEL is not None))
    n = sum(ok)
    print("[計] %s %s 自測 %d/%d · %s" % (NAME, VERSION, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args or (args and args[0] in ("selftest", "test")):
        return selftest()
    if "--client-config" in args:
        root = args[args.index("--root") + 1] if "--root" in args else None
        via = Path(root).resolve() if root else P0.VIA_DEFAULT
        if (via / "VeritasIntelligenceAnalytics").is_dir():
            via = via / "VeritasIntelligenceAnalytics"
        print(json.dumps(client_config(via), ensure_ascii=False, indent=2))
        return 0
    return P0.main(args)


def __getattr__(name):
    return getattr(PRIOR, name)


if __name__ == "__main__":
    raise SystemExit(main())
