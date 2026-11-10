#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA_MCP_Engine v0103 — v0102 薄尾(v0102 一字不改 · SHA 釘住):同一組 MCP 給所有 AI(Claude 有的,ChatGPT / Manus / Gemini / Copilot 一樣有)。

操作員 2026-11-10:「OMNIROUTE 跨 AI 工具都要導入 · CLAUDE 專屬相對應同樣的 CHATGPT / MANUS / GEMINI / COPILOT MCP TO CONNECT」
+「自建構省 TOKEN」。先查既有才寫(不重工):v0102 已有 13 個平台的設定格式(mcp_json / codex_toml / vscode_json / 遠端橋接)與目錄;
本版只補三件它沒有的:
  ① 目錄 +3:
     • via-systemcard —— VIA_SystemCard 尾版的 `mcp` 動詞(stdio · 只讀 6 工具:via_card / via_find / via_where / via_system / via_numbers / via_slice)
       = 本倉自建的省 Token MCP(先卡 → 定位 → 只切一段,不整檔讀)。
     • via-vcgc —— CGC_MDL279_MCPServer 尾版(VCGC 自己的只讀 MCP;.mcp.json 現用的那支)。
     • omniroute —— OmniRoute 自架 AI 閘道內建的 MCP(`omniroute --mcp` stdio;HTTP 版 http://127.0.0.1:20128/api/mcp/stream 要 Bearer 金鑰)。
       需 Node 22.22–22.x 或 24–26 · 出網 · 供應商金鑰由操作員在 OmniRoute 儀表板設定;本引擎不代裝、不碰金鑰。
  ② 執行器 +python:用跑本引擎的那支 Python 啟動倉內 .py(Windows / Linux 同一套;不經 pip、不碰 VIA 環境)。
  ③ 動詞 parity:把同一組 MCP(預設 via-systemcard · via-vcgc · omniroute)套到每個有 MCP 入口的 AI 平台,
     出一張「平台 × MCP」矩陣(本機寫檔 / 貼上 / 遠端橋接 / 無入口)+ 各平台設定文字;預設只渲染不寫檔,
     `--write` 才走 v0102 的 apply(先備份、只合併本引擎管理的名稱);`--probe` 對本機能跑的條目真握手(initialize → tools/list)。
     遠端平台(ChatGPT Chat · Manus · Copilot github.com · Claude Design)只收 HTTPS URL:stdio 條目給 supergateway 橋接指令,
     OmniRoute 給它自己的 HTTP 端點;兩者都還要 HTTPS 隧道 —— 這一步是操作員的手,本引擎照實標「需隧道」,不冒充已接通。

用法:
  python VIA_MCP_Engine/VIA_MCP_Engine_v0103.py parity [--servers via-systemcard,via-vcgc,omniroute] [--platforms a,b] [--write] [--probe] [--out DIR]
  python VIA_MCP_Engine/VIA_MCP_Engine_v0103.py <v0102 任一子指令>      (serve · doctor · catalog · add · apply · probe …原樣下放)
  python VIA_MCP_Engine/VIA_MCP_Engine_v0103.py --selftest              (先 v0102 自測,再本版)
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更)=====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "VeritasIntelligenceAnalytics" / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "VeritasIntelligenceAnalytics" / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

VERSION = "v0103"
ENGINE = "VIA_MCP_Engine_" + VERSION
HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PRIOR_PATH = HERE / "VIA_MCP_Engine_v0102.py"
PRIOR_SHA256 = "b25c6335be6ce04170fbe7bc4c031f03996d344a70a566c2432eca24e196ba42"
PRIOR_SHA_OK = hashlib.sha256(PRIOR_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == PRIOR_SHA256
_spec = importlib.util.spec_from_file_location("via_mcp_engine_v0102", PRIOR_PATH)
BASE = importlib.util.module_from_spec(_spec)
sys.modules["via_mcp_engine_v0102"] = BASE
_spec.loader.exec_module(BASE)


def __getattr__(name: str):
    """前版公開名稱全轉接(serve · apply_platform · probe_command …),薄尾不少 API。"""
    return getattr(BASE, name)

VIA = REPO / "VeritasIntelligenceAnalytics"
MAX_SERVERS_PER_PLATFORM = BASE.MAX_SERVERS_PER_PLATFORM      # 主控台 v0192 契約:模組層上限 5
ENGINE_NAME = BASE.ENGINE_NAME
HTML_FILE = HERE / (Path(__file__).stem + ".html")             # 前端與後端同 stem 同版號(v0103.html = v0102.html 只換版號字樣)
FAMILIES = ["claude-code", "claude-desktop", "chatgpt-codex", "chatgpt-chat", "manus", "gemini-cli", "copilot-vscode", "copilot-web"]
DEFAULT_SERVERS = ["via-systemcard", "via-vcgc", "omniroute"]
OMNI_HTTP = "http://127.0.0.1:20128/api/mcp/stream"


def _tail(folder: Path, pattern: str) -> Path | None:
    c = sorted(folder.glob(pattern))
    return c[-1] if c else None


SYSTEMCARD = _tail(VIA / "docs" / "handoff" / "ai", "VIA_SystemCard_v[0-9][0-9][0-9][0-9].py")
VCGC_MCP = _tail(VIA / "supportive modules" / "registry", "CGC_MDL279_MCPServer_v[0-9][0-9][0-9][0-9].py")

NEW_CATALOG: List[Dict[str, Any]] = [
    {"id": "via-systemcard", "name": "VIA SystemCard(省 Token)", "group": "VIA", "safety": 5, "free": True, "open_source": True,
     "maintainer": "本倉(VCGC 工具)", "local_only": True, "recommended": True,
     "desc": "全景卡 → find / where → slice 一段;只讀 · 零網路 · 索引外的檔不讀",
     "runner": "python", "script": str(SYSTEMCARD) if SYSTEMCARD else "", "args": ["mcp", "--out", "{out}"],
     "params": [{"key": "out", "type": "folder", "label": "SystemCard 掃描輸出夾(scan --out)", "required": True}]},
    {"id": "via-vcgc", "name": "VIA VCGC(治理只讀)", "group": "VIA", "safety": 5, "free": True, "open_source": True,
     "maintainer": "本倉(VCGC)", "local_only": True, "recommended": True,
     "desc": "VCGC 冊 / 收據 / 矩陣只讀(CGC_MDL279 尾版)",
     "runner": "python", "script": str(VCGC_MCP) if VCGC_MCP else "", "args": ["--serve", "--root", str(VIA)],
     "fixed_env": {"PYTHONUTF8": "1", "VIA_FROM_VCGC": "YES"}, "params": []},
    {"id": "omniroute", "name": "OmniRoute(AI 閘道 MCP)", "group": "AI 閘道", "safety": 3, "free": True, "open_source": True,
     "maintainer": "社群(diegosouzapw/OmniRoute · MIT)", "local_only": False, "recommended": False,
     "desc": "自架 OpenAI 相容閘道(127.0.0.1:20128/v1)內建 MCP;需 Node ≥22.22 <23 或 24–26、出網、金鑰在它的儀表板",
     "runner": "npx", "package": "omniroute", "args": ["--mcp"], "alt_runner": {"binary": "omniroute", "args": ["--mcp"]},
     "http_url": OMNI_HTTP, "params": []},
]

# ── 掛進 v0102(同一個 list / dict 物件:前端 serve 與 catalog 指令一起看得到)──
for _c in NEW_CATALOG:
    if _c["id"] not in BASE.CATALOG_BY_ID:
        BASE.CATALOG.append(_c)
        BASE.CATALOG_BY_ID[_c["id"]] = _c
for _g in ("VIA", "AI 閘道"):
    if _g not in BASE.GROUP_ORDER:
        BASE.GROUP_ORDER.insert(0 if _g == "VIA" else len(BASE.GROUP_ORDER) - 1, _g)

_base_command, _pick_runner, _doctor, _fill_args = BASE.base_command, BASE.pick_runner, BASE.doctor, BASE.fill_args


def base_command(cat, runner, args, env_passthrough):
    if runner == "python":
        return sys.executable or "python", [cat["script"], *args]
    return _base_command(cat, runner, args, env_passthrough)


def pick_runner(cat, runners):
    if cat.get("runner") == "python":
        return ("python", None) if cat.get("script") and Path(cat["script"]).is_file() else ("python", "%s:倉內腳本不在(%s)" % (cat["name"], cat.get("script")))
    if cat.get("alt_runner") and not runners.get(cat["runner"]) and BASE.which(cat["alt_runner"].get("binary", "")):
        return "binary", "%s:缺 %s,改用本機 %s" % (cat["name"], cat["runner"], cat["alt_runner"]["binary"])
    return _pick_runner(cat, runners)


def fill_args(cat, params):
    args, env = _fill_args(cat, params)
    env.update(cat.get("fixed_env") or {})
    return args, env


def doctor(project=None):
    d = _doctor(project)
    d["runners"]["python"] = True
    d["runners"]["binary"] = d["runners"].get("binary") or bool(BASE.which("omniroute"))
    d["tools"]["omniroute"] = {"found": bool(BASE.which("omniroute")), "path": BASE.which("omniroute"), "version": None}
    d["engine_tail"] = ENGINE
    return d


BASE.base_command, BASE.pick_runner, BASE.doctor, BASE.fill_args = base_command, pick_runner, doctor, fill_args


# ── parity:同一組 MCP 給所有 AI ──
def parity(servers: List[str], platforms: List[str], params: Dict[str, Dict[str, Any]], project: str | None = None,
           write: bool = False, probe: bool = False, probe_timeout: float = 60.0) -> Dict[str, Any]:
    st = BASE.load_state() if write else {"schema": "VIA.MCP.ENGINE.STATE/1", "project_dir": project or str(REPO), "assignments": {},
                                           "secret_mode": "auto", "history": []}
    if project:
        st["project_dir"] = project
    env_info = doctor(st.get("project_dir"))
    rows, configs, probes = [], {}, {}
    for pid in platforms:
        p = BASE.PLATFORM_BY_ID[pid]
        if p["mode"] == "none":
            rows.append({"platform": pid, "name": p["name"], "vendor": p["vendor"], "mode": "none", "servers": {}, "lamp": "GRAY", "note": p.get("note", "")})
            continue
        have = {a["name"] for a in st["assignments"].get(pid, [])}
        for sid in servers:
            if sid not in have:
                try:
                    BASE.assign(st, pid, sid, params.get(sid), name=sid)
                except ValueError as exc:
                    rows.append({"platform": pid, "name": p["name"], "vendor": p["vendor"], "mode": p["mode"], "servers": {}, "lamp": "RED", "note": str(exc)})
                    break
        r = BASE.render_platform(st, pid, env_info)
        cell = {}
        for sid in servers:
            cat = BASE.CATALOG_BY_ID[sid]
            if p["mode"] == "remote":
                cell[sid] = "遠端:" + ("原生 HTTP %s(需 HTTPS 隧道 + Bearer)" % cat["http_url"] if cat.get("http_url") else "supergateway 橋接(需 HTTPS 隧道)")
            elif p["mode"] == "paste":
                cell[sid] = "貼上 JSON"
            else:
                cell[sid] = "寫 %s" % (r.get("config_path") or "?")
        warn = [w for w in r.get("warnings", []) if w]
        lamp = "YELLOW" if p["mode"] == "remote" else ("YELLOW" if any("未安裝" in w or "不在" in w for w in warn) else "GREEN")
        row = {"platform": pid, "name": p["name"], "vendor": p["vendor"], "mode": p["mode"], "servers": cell, "lamp": lamp,
               "config_path": r.get("config_path"), "warnings": warn}
        if p["mode"] == "remote":
            omni = [s for s in servers if BASE.CATALOG_BY_ID[s].get("http_url")]
            extra = "".join("\n\n# %s(原生 HTTP,不用 supergateway)\n# URL: %s · Header: Authorization: Bearer <OmniRoute 儀表板金鑰>" % (s, BASE.CATALOG_BY_ID[s]["http_url"]) for s in omni)
            configs[pid] = (r.get("bridge") or "") + extra
        else:
            configs[pid] = r.get("text") or ""
        if write and p["mode"] == "local":
            res = BASE.apply_platform(st, pid, dry_run=False, env_info=env_info)
            row["applied"] = {k: res.get(k) for k in ("written", "backup", "config_path") if k in res}
        if probe and p["mode"] in ("local", "paste") and "servers" in r:
            for name, srv in r["servers"].items():
                key = "%s|%s" % (srv["command"], " ".join(srv["args"]))
                if key not in probes:
                    probes[key] = dict(BASE.probe_command(srv["command"], srv["args"], srv.get("env") or {}, timeout=probe_timeout, cwd=str(REPO)), server=name)
                pr = probes[key]
                row.setdefault("probe", {})[name] = "GREEN · 工具 %d" % pr["tool_count"] if pr["ok"] else "RED · %s" % (pr.get("error") or pr.get("stage"))
            if any(v.startswith("RED") for v in row.get("probe", {}).values()):
                row["lamp"] = "RED"
        rows.append(row)
    if write:
        BASE.save_state(st)
    lamps = [r["lamp"] for r in rows]
    overall = "RED" if "RED" in lamps else ("GREEN" if all(x in ("GREEN", "GRAY") for x in lamps) else "YELLOW")
    return {"engine": ENGINE, "at": BASE.now_iso(), "servers": servers, "platforms": platforms, "lamp": overall, "rows": rows,
            "configs": configs, "probes": [{k: v for k, v in x.items() if k in ("server", "ok", "tool_count", "tools", "error", "stage", "elapsed", "server")} for x in probes.values()],
            "write": write, "prior_sha_ok": PRIOR_SHA_OK,
            "honest": "遠端平台(ChatGPT Chat · Manus · Copilot github.com · Claude Design)要 HTTPS 隧道才連得上,這步在操作員;黃 ≠ 綠。"}


def render_md(res: Dict[str, Any]) -> str:
    L = ["# 同一組 MCP 給所有 AI · %s · %s" % (res["lamp"], res["at"]), "",
         "| 燈 | 平台 | 廠商 | 模式 | " + " | ".join(res["servers"]) + " | 握手 |", "|---|---|---|---|" + "---|" * len(res["servers"]) + "---|"]
    for r in res["rows"]:
        L.append("| %s | %s | %s | %s | %s | %s |" % (r["lamp"], r["name"], r["vendor"], r["mode"],
                                                    " | ".join(r["servers"].get(s, "—") for s in res["servers"]),
                                                    " · ".join("%s %s" % kv for kv in (r.get("probe") or {}).items()) or "—"))
    L += ["", res["honest"], ""]
    for pid, text in res["configs"].items():
        if text:
            L += ["## %s" % pid, "```", text.strip(), "```", ""]
    return "\n".join(L) + "\n"


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · %s" % note) if note else ""), flush=True)

    print("[%s selftest]" % ENGINE)
    chk("① v0102 一字不改(SHA 釘住)", PRIOR_SHA_OK)
    chk("①b 主控台 v0192 契約:同 stem .html 在 · VERSION = 檔名版號 · 模組層上限 5 · main 可呼叫",
        HTML_FILE.is_file() and HTML_FILE.stem == Path(__file__).stem and VERSION in Path(__file__).stem and MAX_SERVERS_PER_PLATFORM == 5
        and "VIA MCP Engine" in HTML_FILE.read_text(encoding="utf-8"))
    chk("② 目錄 +3(via-systemcard · via-vcgc · omniroute)且 v0102 前端 / catalog 看得到(同一物件)",
        all(c in BASE.CATALOG_BY_ID for c in DEFAULT_SERVERS) and "VIA" in BASE.GROUP_ORDER)
    chk("③ 倉內腳本找得到尾版", SYSTEMCARD and SYSTEMCARD.is_file() and VCGC_MCP and VCGC_MCP.is_file(), "%s · %s" % (SYSTEMCARD and SYSTEMCARD.name, VCGC_MCP and VCGC_MCP.name))
    with tempfile.TemporaryDirectory() as td:
        os.environ["VIA_MCP_HOME"] = td
        os.environ.setdefault("VIA_MCP_SKIP_VERSIONS", "1")
        # SystemCard 先掃一個小夾,MCP 才有索引可讀
        fx = Path(td) / "fx" / "VeritasIntelligenceAnalytics" / "supportive modules" / "registry"
        fx.mkdir(parents=True)
        (fx / "CGC_MDL001_Tool_v0100.py").write_text('"""工具"""\ndef go():\n    return 1\n', encoding="utf-8")
        out = Path(td) / "sc"
        import subprocess
        subprocess.run([sys.executable, str(SYSTEMCARD), "scan", str(Path(td) / "fx"), "--out", str(out)], capture_output=True, timeout=120)
        res = parity(["via-systemcard", "via-vcgc", "omniroute"], FAMILIES + ["gemini-chat"], {"via-systemcard": {"out": str(out)}},
                     project=str(Path(td) / "proj"), write=False, probe=True, probe_timeout=60)
        by = {r["platform"]: r for r in res["rows"]}
        chk("④ 八個 AI 平台都拿到同一組三支(Claude Code · Desktop · Codex · ChatGPT · Manus · Gemini CLI · Copilot VS Code / web)",
            all(set(by[p]["servers"]) == set(DEFAULT_SERVERS) for p in FAMILIES), {p: by[p]["mode"] for p in FAMILIES})
        cc = json.loads(res["configs"]["claude-code"])["mcpServers"]
        gm = json.loads(res["configs"]["gemini-cli"])["mcpServers"]
        vs = json.loads(res["configs"]["copilot-vscode"])["servers"]
        chk("⑤ 格式各照各的:Claude / Gemini = mcpServers · Copilot = servers(type stdio)· Codex = TOML [mcp_servers.*]",
            cc["via-systemcard"]["args"][-3:] == ["mcp", "--out", str(out)] and gm["via-vcgc"]["env"]["VIA_FROM_VCGC"] == "YES"
            and vs["omniroute"]["type"] == "stdio" and "[mcp_servers.via-systemcard]" in res["configs"]["chatgpt-codex"])
        chk("⑥ 遠端平台照實:ChatGPT / Manus / Copilot web 給 supergateway 橋 + OmniRoute 原生 HTTP · 燈黃(要隧道)",
            all(by[p]["lamp"] == "YELLOW" and "supergateway" in res["configs"][p] and OMNI_HTTP in res["configs"][p] for p in ("chatgpt-chat", "manus", "copilot-web")))
        chk("⑦ 無 MCP 入口的平台 = GRAY,不冒充", by["gemini-chat"]["lamp"] == "GRAY")
        pr = by["claude-code"].get("probe", {})
        chk("⑧ 真握手:via-systemcard 6 工具 · via-vcgc 有工具(omniroute 沒裝 = RED 照實,不擋本項)",
            pr.get("via-systemcard", "").startswith("GREEN · 工具 6") and pr.get("via-vcgc", "").startswith("GREEN"), pr)
        chk("⑨ 預設不寫檔(沒 --write → 使用者設定 / state 都沒動)", not (Path(td) / "proj" / ".mcp.json").exists() and not (Path(td) / "state.json").exists())
        md = render_md(res)
        chk("⑩ 矩陣 md:每平台一列 · 三欄 MCP · 設定文字附在後", md.count("\n| ") >= len(FAMILIES) + 2 and "## claude-code" in md)
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", ENGINE, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if raw in (["--selftest"], ["selftest"]):
        rc0 = BASE.selftest()
        return max(rc0, selftest())
    if raw[:1] == ["version"]:
        print("VIA_MCP_Engine %s(v0102 薄尾)" % VERSION)
        return 0
    if raw[:1] == ["parity"]:
        import argparse
        ap = argparse.ArgumentParser(prog="VIA_MCP_Engine_v0103 parity")
        ap.add_argument("--servers", default=",".join(DEFAULT_SERVERS))
        ap.add_argument("--platforms", default=",".join(FAMILIES + ["gemini-chat"]))
        ap.add_argument("--systemcard-out", default=str(VIA / "VIA_Reports" / "systemcard" / "B"))
        ap.add_argument("--project", default=None)
        ap.add_argument("--write", action="store_true")
        ap.add_argument("--probe", action="store_true")
        ap.add_argument("--out", default=str(VIA / "VIA_Reports" / "mcp_parity"))
        a = ap.parse_args(raw[1:])
        res = parity([s for s in a.servers.split(",") if s], [p for p in a.platforms.split(",") if p],
                     {"via-systemcard": {"out": a.systemcard_out}}, a.project, a.write, a.probe)
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "MCP_Parity_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        (out / "MCP_Parity_latest.md").write_text(render_md(res), encoding="utf-8")
        print("[%s] %s parity · %d 平台 × %d MCP · %s" % (res["lamp"], ENGINE, len(res["rows"]), len(res["servers"]), out / "MCP_Parity_latest.md"))
        for r in res["rows"]:
            print("  %-6s %-34s %-6s %s" % (r["lamp"], r["name"], r["mode"], " · ".join("%s %s" % kv for kv in (r.get("probe") or {}).items())))
        return 0 if res["lamp"] != "RED" else 1
    if not raw or raw[0] == "serve":
        BASE.HTML_FILE = HTML_FILE        # 只在開前端時換成本版 html(v0102 自測仍驗它自己的 stem)
    return BASE.main(raw)


if __name__ == "__main__":
    sys.exit(main())
