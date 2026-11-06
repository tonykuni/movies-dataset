#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""CGC_MDL279_MCPServer v0100 — VCGC 的 MCP 伺服器薄殼(stdio · JSON-RPC 2.0 · 只讀)。

操作員 2026-11-06:「透過 MCP 連結 … 用矩陣顯示整合工具 … 接續他(Manus)收尾 VCGC」。VCGC 之前對外只有三種介面:主控台動詞 ·
PowerShell 操作台 · 收據 JSON;本模組把**只讀**的那一部分照 MCP(Model Context Protocol)露出去,讓 Claude Desktop / Manus /
任何 MCP 用戶端能問 VCGC:省 Token 卡 · 必用卡 · 狀態 · 交接閘 · 盤點冊 · 矩陣 · SDD · SSOT 全景 · 事件 · 薄尾鏈,並讀各系統自報的收據。

邊界(四 / 五系統對等 · L120 · 本卡「禁」):
  · 只露唯讀動詞(白名單 READ_VERBS);會寫冊 / 鎖 / 快照 / 推送 / 開同意閘的動詞一律不露(tools/call 回 isError)。
  · 每個工具 = 子行程跑 VCGC 自己的主控台(`VIA_FROM_VCGC=YES python <console> <動詞>`),不 import 主控台、不繞過它的閘與事件紀錄。
  · 資源 = 收據 JSON / 矩陣 md(VIA_Reports/** · docs/handoff/**),只讀。
  · 零網路:stdio 傳輸(stdin / stdout),不 import socket / http;不改任何檔(本模組自己也只寫 stderr)。
用法:
  python CGC_MDL279_MCPServer_v0100.py --serve [--root <倉根>]        # MCP 用戶端設定 command 指向這一行(見 client_config)
  python CGC_MDL279_MCPServer_v0100.py --client-config [--root <倉根>] # 印給 Claude Desktop / Manus 貼的 mcpServers JSON
  python CGC_MDL279_MCPServer_v0100.py --selftest                       # 假主控台 · 不碰 VCGC
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None   # 本模組零網路(stdio);橋只為治理規則留名,不載入
# ===== [VIA:NET-BRIDGE:END] =====

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

NAME = "CGC_MDL279_MCPServer"
VERSION = "v0100"
PROTOCOL = "2025-06-18"
HERE = Path(__file__).resolve().parent                       # supportive modules/registry
VIA_DEFAULT = HERE.parent.parent                             # VeritasIntelligenceAnalytics
# 只讀動詞白名單:工具名 → (主控台 argv, 說明)。會寫冊 / 鎖 / 快照 / 推送 / 同意閘的動詞不在表上。
READ_VERBS = {
    "vcgc_token": (["token"], "省 Token 第一步:啟用狀態 + 政策卡(每次進場先看)"),
    "vcgc_functions": (["functions"], "AI 必用功能卡:順序 · 指令 · 禁止"),
    "vcgc_status": (["status"], "閘:政策整冊 · 子系統座位 · 加速器 / 網路已接"),
    "vcgc_sync_check": (["sync-check"], "座位 + 註冊冊乾跑 + SDD 檢"),
    "vcgc_handoff_check": (["handoff", "check"], "交接防遺漏:摘要 · 待辦 · 相依變更 · 發現(只讀 · 不 checkpoint)"),
    "vcgc_test_inventory": (["test", "inventory"], "盤點冊逐站列表(不跑)"),
    "vcgc_matrix": (["matrix"], "冊 × 啟動矩陣 × 引擎四態(預設 PLAN · 乾跑)"),
    "vcgc_sdd": (["sdd"], "SDD 驗證(X-REQ / X-NUM / X-LOCK …)"),
    "vcgc_ssot_panorama": (["ssot", "panorama"], "SSOT 六族四層全景"),
    "vcgc_events": (["events"], "最近的 VCGC 真實事件"),
    "vcgc_workflow": (["workflow"], "流程符合性"),
    "vcgc_systems": (["systems"], "五系統對等:各 SYSTEM MANAGER 自報的燈(只讀互看)"),
    "vcgc_tools": (["tools"], "鎖版工具席位清單(不 activate)"),
    "vcgc_chain": (["chain"], "薄尾版本鏈圖:參數 family(家族名)"),
    "vcgc_help": (["help"], "動詞清單"),
}
WRITE_VERBS_DENIED = ("checkpoint", "activate", "registry-sync", "--apply", "push", "go", "enter", "register", "sync", "install", "backup", "lock", "snapshot")
RECEIPTS = {   # 資源 URI 尾段 → 相對 VIA 根的檔(只讀)
    "vcgc/test": "VIA_Reports/vcgc/TEST_latest.json",
    "vcgc/handoff": "docs/handoff/HANDOFF_latest.json",
    "vcgc/token-activation": "VIA_Reports/vcgc/token_activation_latest.json",
    "settle/latest": "VIA_Reports/settle/SETTLE_latest.json",
    "vqg/closeout": "VIA_Reports/vqg/VQG_Closeout_latest.json",
    "graphify/latest": "VIA_Reports/graphify/VIA_Graphify_latest.json",
    "agent-os/selftest": "VIA_Reports/agent_os/VIA_AgentOS_v0102_selftest.json",
    "vrn2/closeout": "VIA_Reports/vrn2/VRN2_CloseoutUI_latest.json",
    "vdf/ui-manifest": "VIA_Reports/vdf/VDF_UI_MANIFEST.json",
    "matrix/vcgc-tools": "docs/handoff/ai/VCGC_ToolMatrix_20261106.md",
    "matrix/closeout-panorama": "docs/handoff/ai/VIA_Closeout_Panorama_20261105.md",
}
MAX_OUT = 60000


def find_console(via: Path) -> Path | None:
    hits = sorted((via / "supportive modules" / "registry").glob("CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"))
    return hits[-1] if hits else None


def run_console(console: Path, via: Path, argv: list, timeout: int = 900) -> dict:
    """子行程跑 VCGC 主控台(它自己的閘與事件紀錄照走);→ {rc, out}。"""
    env = dict(os.environ)
    env.update({"VIA_FROM_VCGC": "YES", "PYTHONUTF8": "1", "VIA_NO_OPEN": "1"})
    try:
        p = subprocess.run([sys.executable, str(console), *argv], cwd=str(via.parent), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout, env=env)
        out = (p.stdout or "") + (p.stderr or "")
        return {"rc": p.returncode, "out": out[-MAX_OUT:]}
    except subprocess.TimeoutExpired:
        return {"rc": 124, "out": "[逾時 %d 秒]" % timeout}
    except OSError as exc:
        return {"rc": 127, "out": "%s: %s" % (type(exc).__name__, exc)}


def tool_specs() -> list:
    specs = []
    for name, (argv, desc) in READ_VERBS.items():
        schema = {"type": "object", "properties": {}, "additionalProperties": False}
        if name == "vcgc_chain":
            schema["properties"] = {"family": {"type": "string", "description": "家族名,例 CGC_MDL149_VeritasCentralGovernanceConsole"}}
            schema["required"] = ["family"]
        if name == "vcgc_events":
            schema["properties"] = {"n": {"type": "integer", "minimum": 1, "maximum": 200, "description": "筆數(預設 20)"}}
        specs.append({"name": name, "description": "%s(只讀 · 子行程跑 VCGC 主控台 `%s`)" % (desc, " ".join(argv)), "inputSchema": schema})
    specs.append({"name": "via_receipt", "description": "讀一份系統自報收據(只讀):key 之一 " + " · ".join(RECEIPTS),
                  "inputSchema": {"type": "object", "properties": {"key": {"type": "string", "enum": list(RECEIPTS)}}, "required": ["key"], "additionalProperties": False}})
    return specs


def resource_specs(via: Path) -> list:
    out = []
    for key, rel in RECEIPTS.items():
        p = via / rel
        out.append({"uri": "via://" + key, "name": key, "description": rel + ("" if p.is_file() else "(這台機器還沒有)"),
                    "mimeType": "text/markdown" if rel.endswith(".md") else "application/json"})
    return out


class Server:
    def __init__(self, via: Path, console: Path | None):
        self.via, self.console = via, console

    def handle(self, msg: dict) -> dict | None:
        mid, method, params = msg.get("id"), msg.get("method") or "", msg.get("params") or {}
        if method.startswith("notifications/"):
            return None
        try:
            if method == "initialize":
                result = {"protocolVersion": PROTOCOL, "capabilities": {"tools": {"listChanged": False}, "resources": {"listChanged": False, "subscribe": False}},
                          "serverInfo": {"name": "vcgc", "title": "VIA VCGC(只讀)", "version": VERSION},
                          "instructions": "VCGC 只讀介面:先 vcgc_token → vcgc_functions → vcgc_handoff_check;收據用 via_receipt / resources。不會寫冊、不會開同意閘、不會推送。"}
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": tool_specs()}
            elif method == "tools/call":
                result = self.call(params.get("name") or "", params.get("arguments") or {})
            elif method == "resources/list":
                result = {"resources": resource_specs(self.via)}
            elif method == "resources/read":
                result = self.read_resource(str(params.get("uri") or ""))
            else:
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": "Method not found: %s" % method}}
            return {"jsonrpc": "2.0", "id": mid, "result": result}
        except (ValueError, KeyError, TypeError, OSError) as exc:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32602, "message": "%s: %s" % (type(exc).__name__, exc)}}

    def call(self, name: str, args: dict) -> dict:
        if name == "via_receipt":
            key = str(args.get("key") or "")
            if key not in RECEIPTS:
                return {"content": [{"type": "text", "text": "unknown receipt key: %s" % key}], "isError": True}
            return self.read_resource("via://" + key, as_tool=True)
        if name not in READ_VERBS:
            return {"content": [{"type": "text", "text": "tool not allowed (只露唯讀動詞): %s" % name}], "isError": True}
        argv = list(READ_VERBS[name][0])
        if name == "vcgc_chain":
            fam = str(args.get("family") or "").strip()
            if not fam or any(ch in fam for ch in " /\\;|&$`") or any(w in fam for w in WRITE_VERBS_DENIED):
                return {"content": [{"type": "text", "text": "family 參數不合(只收家族名)"}], "isError": True}
            argv.append(fam)
        if name == "vcgc_events":
            argv.append(str(int(args.get("n") or 20)))
        if any(w in " ".join(argv) for w in WRITE_VERBS_DENIED):
            return {"content": [{"type": "text", "text": "denied: 會寫冊 / 鎖 / 推送的動詞不露"}], "isError": True}
        if not self.console or not self.console.is_file():
            return {"content": [{"type": "text", "text": "VCGC 主控台不在:%s" % self.console}], "isError": True}
        r = run_console(self.console, self.via, argv)
        return {"content": [{"type": "text", "text": r["out"]}], "isError": r["rc"] not in (0, 2),
                "structuredContent": {"rc": r["rc"], "lamp": "GREEN" if r["rc"] == 0 else ("YELLOW" if r["rc"] == 2 else "RED"), "argv": argv}}

    def read_resource(self, uri: str, as_tool: bool = False) -> dict:
        key = uri[len("via://"):] if uri.startswith("via://") else uri
        if key not in RECEIPTS:
            raise ValueError("unknown resource: %s" % uri)
        p = (self.via / RECEIPTS[key]).resolve()
        if not str(p).startswith(str(self.via.resolve())):
            raise ValueError("outside VIA root")
        if not p.is_file():
            text, mime = "(這台機器還沒有這份收據:%s)" % RECEIPTS[key], "text/plain"
        else:
            text = p.read_text(encoding="utf-8", errors="replace")[:MAX_OUT]
            mime = "text/markdown" if p.suffix == ".md" else "application/json"
        if as_tool:
            return {"content": [{"type": "text", "text": text}], "isError": not p.is_file()}
        return {"contents": [{"uri": "via://" + key, "mimeType": mime, "text": text}]}


def serve(via: Path, console: Path | None, inp=None, outp=None) -> int:
    """stdio 傳輸:一行一個 JSON-RPC 訊息(MCP stdio);回應寫 stdout,日誌寫 stderr。"""
    inp = inp or sys.stdin
    outp = outp or sys.stdout
    srv = Server(via, console)
    for line in inp:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            outp.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}) + "\n")
            outp.flush()
            continue
        resp = srv.handle(msg) if isinstance(msg, dict) else {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}
        if resp is not None:
            outp.write(json.dumps(resp, ensure_ascii=False) + "\n")
            outp.flush()
    return 0


def client_config(via: Path) -> dict:
    """給 Claude Desktop / Manus 等 MCP 用戶端貼的 mcpServers 設定(command 指到本檔 · 只讀)。"""
    return {"mcpServers": {"vcgc": {"command": "python", "args": [str(Path(__file__).resolve()), "--serve", "--root", str(via)],
                                     "env": {"PYTHONUTF8": "1"}}}}


def selftest() -> int:
    import io
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))
    with tempfile.TemporaryDirectory(prefix="via_mcp_") as td:
        d = Path(td)
        via = d / "repo" / "VeritasIntelligenceAnalytics"
        (via / "supportive modules" / "registry").mkdir(parents=True)
        (via / "VIA_Reports" / "vcgc").mkdir(parents=True)
        (via / "VIA_Reports" / "vcgc" / "TEST_latest.json").write_text('{"lamp": "YELLOW", "counts": {"GREEN": 9}}', encoding="utf-8")
        fake = via / "supportive modules" / "registry" / "CGC_MDL149_VeritasCentralGovernanceConsole_v9999.py"
        fake.write_text("import sys,os\nprint('FAKE', ' '.join(sys.argv[1:]), 'VIA_FROM_VCGC=' + os.environ.get('VIA_FROM_VCGC',''))\nsys.exit(2 if sys.argv[1]=='sdd' else 0)\n", encoding="utf-8")
        srv = Server(via, find_console(via))
        chk("① 找主控台:取 registry 尾版", srv.console == fake)
        r = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        chk("② initialize:協定版 · tools + resources 能力 · serverInfo vcgc", r["result"]["protocolVersion"] == PROTOCOL and "tools" in r["result"]["capabilities"] and r["result"]["serverInfo"]["name"] == "vcgc")
        chk("③ notifications/initialized 不回應 · ping 回 {}", srv.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None and srv.handle({"jsonrpc": "2.0", "id": 2, "method": "ping"})["result"] == {})
        tl = srv.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})["result"]["tools"]
        names = {t["name"] for t in tl}
        chk("④ tools/list:%d 個 · 全是唯讀白名單 + via_receipt · 每個有 inputSchema" % len(tl), names == set(READ_VERBS) | {"via_receipt"} and all("inputSchema" in t for t in tl))
        c = srv.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "vcgc_status", "arguments": {}}})["result"]
        chk("⑤ tools/call 走子行程主控台:VIA_FROM_VCGC=YES · argv status · rc 0 → GREEN", "FAKE status VIA_FROM_VCGC=YES" in c["content"][0]["text"] and c["structuredContent"]["lamp"] == "GREEN" and not c["isError"])
        c2 = srv.handle({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "vcgc_sdd", "arguments": {}}})["result"]
        chk("⑥ rc 2 → YELLOW · 不算 isError(黃不是紅 · 也不是綠)", c2["structuredContent"]["lamp"] == "YELLOW" and not c2["isError"])
        bad = [srv.handle({"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": n, "arguments": a}})["result"]["isError"]
               for n, a in (("vcgc_checkpoint", {}), ("vcgc_chain", {"family": "x; rm -rf /"}), ("vcgc_chain", {"family": "tools activate"}), ("via_receipt", {"key": "../etc"}))]
        chk("⑦ 拒絕:不在白名單的動詞 · 帶殼字元的 family · 寫冊字樣 · 未知收據 key → 全部 isError", all(bad), bad)
        ch = srv.handle({"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "vcgc_chain", "arguments": {"family": "CGC_MDL149_VeritasCentralGovernanceConsole"}}})["result"]
        chk("⑧ chain 帶家族名到主控台", "FAKE chain CGC_MDL149_VeritasCentralGovernanceConsole" in ch["content"][0]["text"])
        rl = srv.handle({"jsonrpc": "2.0", "id": 8, "method": "resources/list"})["result"]["resources"]
        rr = srv.handle({"jsonrpc": "2.0", "id": 9, "method": "resources/read", "params": {"uri": "via://vcgc/test"}})["result"]["contents"][0]
        miss = srv.handle({"jsonrpc": "2.0", "id": 10, "method": "resources/read", "params": {"uri": "via://vqg/closeout"}})["result"]["contents"][0]
        chk("⑨ resources:列 %d 份 · 讀到 TEST_latest(JSON)· 沒有的收據照實說「還沒有」不炸" % len(rl), len(rl) == len(RECEIPTS) and '"lamp": "YELLOW"' in rr["text"] and rr["mimeType"] == "application/json" and "還沒有" in miss["text"])
        err = srv.handle({"jsonrpc": "2.0", "id": 11, "method": "nope/x", "params": {}})
        chk("⑩ 未知方法 → -32601", err["error"]["code"] == -32601)
        inp = io.StringIO('{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n{"jsonrpc":"2.0","method":"notifications/initialized"}\nnot json\n{"jsonrpc":"2.0","id":2,"method":"tools/list"}\n')
        outp = io.StringIO()
        serve(via, fake, inp, outp)
        lines = [json.loads(x) for x in outp.getvalue().splitlines()]
        chk("⑪ stdio 串流:一行一訊息 · 通知不回 · 壞 JSON 回 -32700 · 共 3 回應", len(lines) == 3 and lines[1]["error"]["code"] == -32700 and "tools" in lines[2]["result"])
        cfg = client_config(via)
        chk("⑫ client-config:command python · args 含 --serve 與 --root · 零網路(本檔不 import socket / http / urllib / requests)",
            cfg["mcpServers"]["vcgc"]["args"][1:3] == ["--serve", "--root"] and not re.search(r"^\s*(?:import|from)\s+(?:socket|http|urllib|requests)\b", Path(__file__).read_text(encoding="utf-8").split("def selftest")[0], re.M))
    bad_n = len(ok) - sum(ok)
    print("[%s] %s %s --selftest · %d 項 · 不過 %d" % ("PASS" if not bad_n else "FAIL", NAME, VERSION, len(ok), bad_n), flush=True)
    return 0 if not bad_n else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="%s_%s" % (NAME, VERSION), description="VCGC MCP 伺服器(stdio · 只讀)")
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--client-config", action="store_true")
    ap.add_argument("--root", help="倉根或 VIA 根(預設本檔往上找)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("verb", nargs="?", help="selftest 也可當位置動詞")
    a = ap.parse_args(argv)
    if a.selftest or a.verb in ("selftest", "test"):
        return selftest()
    via = Path(a.root).resolve() if a.root else VIA_DEFAULT
    if (via / "VeritasIntelligenceAnalytics").is_dir():
        via = via / "VeritasIntelligenceAnalytics"
    if a.client_config:
        print(json.dumps(client_config(via), ensure_ascii=False, indent=2))
        return 0
    if a.serve:
        print("[%s %s] serving MCP on stdio · VIA %s · console %s" % (NAME, VERSION, via, (find_console(via) or Path("?")).name), file=sys.stderr, flush=True)
        return serve(via, find_console(via))
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
