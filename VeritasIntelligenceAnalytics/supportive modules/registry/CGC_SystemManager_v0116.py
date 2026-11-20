#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_SystemManager v0116 — 薄尾:VCGC 自己的 omniroute 動詞(與 VDF / VRN 管理器的 omniroute 對等,各寫各的)

操作員 2026-11-20 17:13:「VCGC 也要導入 OMNIROUTE」。
VDF / VRN 的管理器各有 omniroute:把自己的 MCP 伺服器寫成給各家 AI 用戶端的設定片段。VCGC 沒有 → 本版補上 VCGC 自己的一份
(不 import VDF / VRN;能力對等 L132):
  python CGC_SystemManager_v0116.py omniroute
    ① 找 VCGC 的 MCP 伺服器尾版(CGC_MDL279_MCPServer)→ 本機 stdio 實跑 initialize + tools/list(逾時 60 秒)→ 取得真的工具清單
    ② 寫 VIA_Reports/vcgc/omniroute/VCGC_OmniRoute_latest.json:claude · chatgpt · gemini · copilot · manus 五家的設定片段
       (形狀同倉根 .mcp.json 的 vcgc 那一段:相對倉根的路徑,不寫本機絕對路徑)
    ③ 另記外部閘道 OmniRoute(埠 20128)現在有沒有在聽 · 安裝夾在不在(只讀,不裝不啟動;裝與啟動在 VIA_VCGC_ApplyRun 的 G 道)
  燈:握手成功而且有工具 = GREEN(rc 0);伺服器找不到或握手失敗 = YELLOW(rc 2,寫原因)。只寫報告夾;零網路(只連本機 127.0.0.1 看埠)。
其餘動詞全部照前版 v0115(engine-matrix · 獨立 MAIN · 自動登記 …)。不寫編號冊、不碰 TA-Lib、不讀寫同意閘。
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
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA_ROOT = HERE.parents[1]
_STEM = "CGC_SystemManager"
FAMILY = _STEM
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
CLIENTS = ("claude", "chatgpt", "gemini", "copilot", "manus")
MCP_STEM = "CGC_MDL279_MCPServer"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _load(PRIOR_PATH, "cgc_prior_for_v0116")


def __getattr__(name):
    """PEP 562:公開名稱照前版鏈轉接,薄尾不漏 API(TAILAPI 律)。"""
    return getattr(PRIOR, name)


def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def mcp_tail(via: Path) -> Path | None:
    hits = [p for p in (via / "supportive modules" / "registry").glob(MCP_STEM + "_v*.py") if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def mcp_config(via: Path, tail: Path) -> dict:
    rel = tail.relative_to(via.parent).as_posix() if via.parent in tail.parents else tail.as_posix()
    return {"mcpServers": {"vcgc": {"command": "python", "args": [rel, "--serve", "--root", via.name],
                                     "env": {"PYTHONUTF8": "1", "VIA_FROM_VCGC": "YES"}}}}


def handshake(tail: Path, via: Path, timeout: int = 60) -> tuple[list, str]:
    msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                                                            "clientInfo": {"name": "vcgc-omniroute", "version": TAG}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}]
    env = dict(os.environ, PYTHONUTF8="1", VIA_FROM_VCGC="YES", VIA_NO_OPEN="1")
    try:
        p = subprocess.run([sys.executable, "-B", str(tail), "--serve", "--root", str(via)], input="".join(json.dumps(m) + "\n" for m in msgs),
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, cwd=str(via.parent), env=env)
    except (OSError, subprocess.TimeoutExpired) as e:
        return [], "握手失敗:%s" % type(e).__name__
    replies = {}
    for line in (p.stdout or "").splitlines():
        try:
            pkt = json.loads(line)
        except ValueError:
            continue
        if isinstance(pkt, dict) and "id" in pkt:
            replies[pkt["id"]] = pkt
    tools = [t.get("name") for t in ((replies.get(2) or {}).get("result") or {}).get("tools", []) if isinstance(t, dict)]
    if 1 not in replies or "result" not in replies[1]:
        return [], "initialize 沒有回應(結束碼 %s)" % p.returncode
    if not tools:
        return [], "tools/list 沒有工具"
    return tools, "握手成功"


def gateway() -> dict:
    up = False
    try:
        with socket.create_connection(("127.0.0.1", 20128), timeout=0.7):
            up = True
    except OSError:
        up = False
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "VIA" / "tools"
    inst = [n for n in ("OmniRoute3", "OmniRoute") if (base / n).is_dir()]
    return {"listening_20128": up, "installed": inst, "note": "只讀;裝與啟動在 VIA_VCGC_ApplyRun 的 G 道(要你開同意閘)"}


def omniroute(via: Path = VIA_ROOT, out_dir: Path | None = None) -> dict:
    tail = mcp_tail(via)
    out = out_dir or (via / "VIA_Reports" / "vcgc" / "omniroute")
    out.mkdir(parents=True, exist_ok=True)
    if tail is None:
        tools, why, cfg = [], "找不到 VCGC 的 MCP 伺服器(%s 尾版)" % MCP_STEM, {}
    else:
        cfg = mcp_config(via, tail)
        tools, why = handshake(tail, via)
    routes = {c: cfg for c in CLIENTS} if cfg else {}
    lamp = "GREEN" if tools and routes else "YELLOW"
    body = {"system": "VCGC", "manager": TAG, "at": utc(), "lamp": lamp, "why": why, "server": tail.name if tail else None,
            "tools": tools, "routes": routes, "gateway": gateway()}
    p = out / "VCGC_OmniRoute_latest.json"
    p.write_text(json.dumps(body, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    try:
        rel = p.relative_to(via).as_posix()
    except ValueError:
        rel = str(p)
    return {"lamp": lamp, "why": why, "clients": sorted(routes), "tools": len(tools), "file": rel, "gateway": body["gateway"]}


def main() -> int:
    argv = sys.argv[1:]
    if argv[:1] == ["omniroute"]:
        r = omniroute()
        g = r["gateway"]
        print("[%s] omniroute %s · tools %d · clients %s · %s · file %s · 外部閘道 %s" % (
            TAG, r["lamp"], r["tools"], ",".join(r["clients"]) or "—", r["why"], r["file"],
            "在聽 20128" if g["listening_20128"] else ("已裝沒在跑" if g["installed"] else "沒裝")), flush=True)
        return 0 if r["lamp"] == "GREEN" else 2
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)
    print(f"[計] {TAG} 自測開始(本版 7 項 · 再前版 {PRIOR_PATH.name})", flush=True)
    fake = ("import json,sys\n"
            "for line in sys.stdin:\n"
            "    m=json.loads(line)\n"
            "    if 'id' not in m: continue\n"
            "    r={'protocolVersion':'2025-06-18','serverInfo':{'name':'fake'}} if m['method']=='initialize' else {'tools':[{'name':'vcgc_status'},{'name':'vcgc_token'}]}\n"
            "    print(json.dumps({'jsonrpc':'2.0','id':m['id'],'result':r}),flush=True)\n")
    with tempfile.TemporaryDirectory(prefix="cgc_sm116_") as td:
        repo = Path(td) / "repo"
        via = repo / "VeritasIntelligenceAnalytics"
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (reg / (MCP_STEM + "_v0100.py")).write_text("raise SystemExit(1)\n", encoding="utf-8")
        (reg / (MCP_STEM + "_v0101.py")).write_text(fake, encoding="utf-8")
        r = omniroute(via)
        body = json.loads((via / "VIA_Reports/vcgc/omniroute/VCGC_OmniRoute_latest.json").read_text(encoding="utf-8"))
        chk("O1 取 MCP 伺服器尾版 · 實跑握手拿到真的工具清單 · GREEN", r["lamp"] == "GREEN" and body["tools"] == ["vcgc_status", "vcgc_token"]
            and body["server"] == MCP_STEM + "_v0101.py", r)
        args = body["routes"]["claude"]["mcpServers"]["vcgc"]["args"]
        chk("O2 五家用戶端都有設定 · 路徑相對倉根(同 .mcp.json 的 vcgc 段)· 不寫本機絕對路徑", sorted(body["routes"]) == sorted(CLIENTS)
            and args[0] == "VeritasIntelligenceAnalytics/supportive modules/registry/%s_v0101.py" % MCP_STEM and td not in json.dumps(body["routes"]), args)
        (reg / (MCP_STEM + "_v0102.py")).write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
        r2 = omniroute(via)
        chk("O3 伺服器握手失敗 → YELLOW 並寫原因(不丟例外)", r2["lamp"] == "YELLOW" and "沒有回應" in r2["why"], r2)
        empty = Path(td) / "empty" / "VeritasIntelligenceAnalytics"
        (empty / "supportive modules" / "registry").mkdir(parents=True)
        r3 = omniroute(empty)
        chk("O4 找不到伺服器 → YELLOW · 照實說", r3["lamp"] == "YELLOW" and "找不到" in r3["why"], r3)
        chk("O5 只寫報告夾(暫存倉裡除了報告夾沒有新檔)", sorted(p.relative_to(via).as_posix() for p in via.rglob("*") if p.is_file() and "VIA_Reports" not in p.parts)
            == sorted("supportive modules/registry/%s_v%s.py" % (MCP_STEM, v) for v in ("0100", "0101", "0102")))
    text = Path(__file__).read_text(encoding="utf-8")
    chk("O6 檔面:第 3 行加速器標記 · 零 TA-Lib · 不寫同意閘 · 不 import VDF / VRN",
        text.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and "import " + "talib" not in text
        and "environ[\"VIA_NET" + "_CONSENT\"] =" not in text and not re.search(r"^\s*(import|from)\s+(VDF|VRN)", text, re.M))
    prior_rc = PRIOR.selftest()
    chk(f"O7 前版 {PRIOR_PATH.name} 自測照過", prior_rc == 0, prior_rc)
    n = sum(ok)
    print(f"[計] {TAG} 自測 {n}/{len(ok)} · {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
