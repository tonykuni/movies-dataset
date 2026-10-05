#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL269_PyCommandHub v0101 — 短指令 PY 樞紐(批1657)+ 稽核與合併計畫(2026-10-06 操作員令
「列出這兩天常用的短指令轉 PY 化 用模組化寫 AST 分類詳述 有無重複 有無同功能較新 有無缺失 列清單合併計畫」)。

v0100→v0101 新三動詞(v0100 四動詞一字不動):
  recent               這兩天實用短令清單(對話實錄彙整)→ 各令的 PY 正主與 PY 化狀態
  audit                結構化(AST 式)分類詳述:① 重複=同名多檔定義(鏈=點源疊加,最新檔的定義才活,
                       其餘=被取代);② 同功能=本體正規化雜湊相同(異名同體);③ 較新=同 PY 正主
                       多令取最新定義;④ 缺失=轉發目標在樹上找不到尾版(誠實列);⑤ 本體形狀分類
                       (純轉發/帶邏輯/啟動開頁/環境閘)
  plan                 合併計畫:活令依 PY 正主分群 → 「動作不多、指令誇張多」收斂表(N 令 → M 群),
                       只列計畫不動 .ps1(L70)

PY 功能律(正典 四之三之一)的總盤口:
  inventory            盤點 Register-VIA-Commands-v*.ps1 整條鏈的 via-* 短令——每令列出別名、
                       轉發的 PY 正主(via-vcgc run <模組> …)、PS 殘留邏輯跡象(Read-Host/Start-Process/
                       ConvertTo-*),燈:綠=純轉發 PY · 黃=帶 PS 邏輯(PY 化待辦,誠實列不消失)
  run <短令> [args…]    PY 車道直跑:解析該短令的第一個 PY 轉發目標,經 VCGC console(政策閘照走)執行
                       ——不經 PowerShell;PS 剩啟動與開頁(L70:.ps1 零觸碰)
  edit-parse <一行>     邏輯移植首例:ConvertTo-VIAVdfEdit 的解析律 PY 化(大類=日期→--start ·
                       +族群=值→--add · -族群=值→--remove · 其他=誠實 None)
  gates                雙閘現況(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT;只讀不代設)
唯讀盤點、不改 .ps1、不寫冊;帶加速器橋(L103/L102)。VIA_FROM_VCGC 閘:缺=自立閘座(獨立 MAIN 律)。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
TAG = "CGC_MDL269_PyCommandHub_v0101"

_FN_RX = re.compile(r"^function\s+global:([A-Za-z0-9_\-]+)", re.M)
_ALIAS_RX = re.compile(r"Set-Alias\s+-Name\s+(\S+)\s+-Value\s+(\S+)")
_RUN_RX = re.compile(r"via-vcgc\s+run\s+((?:@?\(?[^\n]|[^\n])*)")
_PY_TARGET_RX = re.compile(r"'((?:CGC|VDF|VRN|SUP)_[A-Za-z0-9_]+)'|\"((?:CGC|VDF|VRN|SUP)_[A-Za-z0-9_]+)\"|\b((?:CGC|VDF|VRN|SUP)_MDL\d+\w*|VDF_SystemManager|VRN_SystemManager|CGC_SystemManager)\b")
_PS_LOGIC_HINTS = ("Read-Host", "Start-Process", "ConvertTo-", "if (", "while (", "-match")


def _reg_files() -> list:
    return sorted(VIA.glob("Register-VIA-Commands-v*.ps1"))


def inventory() -> dict:
    """盤點整條 PS 短令鏈:誰轉發到哪支 PY 正主、誰還帶 PS 邏輯(黃=PY 化待辦)。唯讀。"""
    rows, seen = [], set()
    files = _reg_files()
    for f in reversed(files):   # 尾版優先;同名短令以最新定義為準
        text = f.read_text(encoding="utf-8", errors="replace")
        aliases = {}
        for m in _ALIAS_RX.finditer(text):
            aliases.setdefault(m.group(2), []).append(m.group(1))
        marks = list(_FN_RX.finditer(text))
        for i, m in enumerate(marks):
            name = m.group(1)
            if name in seen:
                continue
            seen.add(name)
            body = text[m.end():(marks[i + 1].start() if i + 1 < len(marks) else len(text))]
            tgts = sorted({g for mm in _PY_TARGET_RX.finditer(body) for g in mm.groups() if g})
            hints = sorted({h for h in _PS_LOGIC_HINTS if h in body})
            run_fwd = "via-vcgc run" in body or "via-vcgc " in body
            lamp = "綠" if run_fwd and len(hints) <= 1 else ("黃" if run_fwd or tgts else "白")
            rows.append({"filename": name, "file": f.name, "aliases": aliases.get(name, []),
                         "py_targets": tgts, "ps_logic": hints, "forwards_vcgc": run_fwd,
                         "state": "PY轉發" if lamp == "綠" else ("PS邏輯待PY化" if lamp == "黃" else "PS原生"),
                         "lamp": lamp})
    from collections import Counter
    tally = dict(Counter(r["lamp"] for r in rows))
    return {"verb": "inventory", "hub": TAG, "reg_files": [f.name for f in files],
            "commands": len(rows), "tally": tally,
            "rule": "綠=純轉發 PY · 黃=帶 PS 邏輯(待辦帶理由轉態,不消失)· 白=PS 原生(啟動/UI 職能,留 PS)",
            "rows": rows}


def _console_tail() -> Path | None:
    hits = sorted(HERE.glob("CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"))
    return hits[-1] if hits else None


def run_cmd(args: list) -> int:
    """PY 車道直跑一個短令:取其第一個 PY 轉發目標,經 VCGC console run 執行(政策閘照走)。"""
    inv = inventory()
    row = next((r for r in inv["rows"] if r["filename"] == args[0] or args[0] in r["aliases"]), None)
    if row is None:
        print(f"[拒跑] 短令 {args[0]} 不在盤點內(via-vcgc hub inventory 看清單)")
        return 2
    if not row["py_targets"]:
        print(f"[誠實] {args[0]} 無 PY 轉發目標(PS 原生:啟動/UI 職能)——照 PY 功能律留 PS,不硬跑")
        return 3
    con = _console_tail()
    if con is None:
        print("[誠實] VCGC console 不在,PY 車道停")
        return 3
    cmd = [sys.executable, str(con), "run", row["py_targets"][0]] + args[1:]
    print(f"[PY車道] {args[0]} → {row['py_targets'][0]}(經 VCGC 政策閘)")
    env = dict(os.environ, VIA_FROM_VCGC="YES")
    return subprocess.run(cmd, env=env).returncode


def edit_parse(line: str):
    """ConvertTo-VIAVdfEdit 解析律 PY 化(邏輯移植;與 PS 版同判):
    +族群=值 → ('--add','族群=值') · -族群=值 → ('--remove',…) · 大類=YYYY-MM-DD|default → ('--start',…) · 其他=None。"""
    t = (line or "").strip()
    m = re.match(r"^\+\s*([A-Za-z0-9_]+)\s*=\s*(.+)$", t)
    if m:
        return ["--add", f"{m.group(1)}={m.group(2).strip()}"]
    m = re.match(r"^-\s*([A-Za-z0-9_]+)\s*=\s*(.+)$", t)
    if m:
        return ["--remove", f"{m.group(1)}={m.group(2).strip()}"]
    m = re.match(r"^([A-Za-z0-9_]+)\s*=\s*(\d{4}-\d{2}-\d{2}|default)$", t)
    if m:
        return ["--start", f"{m.group(1)}={m.group(2)}"]
    return None


def gates() -> dict:
    """雙閘現況(只讀,永不代設;PS 的閘判斷邏輯 PY 化)。"""
    net = os.environ.get("VIA_NET_CONSENT")
    scrape = os.environ.get("VIA_SCRAPE_CONSENT")
    open_ = net == "YES" and bool(scrape) and scrape != "OFF"
    return {"verb": "gates", "VIA_NET_CONSENT": net, "VIA_SCRAPE_CONSENT": scrape,
            "both_open": open_, "note": "本樞紐只讀不寫;要開=操作員本視窗自設(永不代設)"}


RECENT_TWO_DAYS = [
    # (短令, PY 正主, 現況)——2026-10-05/06 兩日對話實錄彙整
    ("via-vcgc token", "CGC_MDL149 console", "PY"),
    ("via-vcgc functions", "CGC_MDL149 console", "PY"),
    ("via-vcgc handoff check/test/checkpoint", "CGC_MDL149 console", "PY"),
    ("via-vcgc test --quick", "CGC_MDL149 console", "PY"),
    ("via-vcgc ssot panorama", "CGC_MDL247_SSOTPanorama", "PY"),
    ("via-vcgc registry-sync --apply", "CGC_MDL149 console", "PY"),
    ("via-vcgc sdd check", "CGC_MDL149 console", "PY"),
    ("via-vcgc run VRN_SystemManager deepread/layout-check/reconstruct", "VRN_SystemManager 尾版", "PY(v0123 獨立 MAIN 可直跑)"),
    ("via-vcgc run VRN_SystemManager intake/eps-check/real-test/vdf-fetch", "VRN_SystemManager 尾版", "PY(同上)"),
    ("via-vcgc run VRN_SystemManager ssot adopt/diff/number pull", "VRN_SystemManager v0120-0122", "PY"),
    ("via-vcgc run --family vrn VRN_ENG088 drift", "VRN_ENG088_SsotAdditiveBridge", "PY"),
    ("via-panorama read/slice/digest/pack", "CGC_MDL158_VIAPanoramaAuditRepair", "PY"),
    ("via-activate-vdf", "CGC_MDL265 + CGC_MDL261 + VDF_SystemManager activate", "黃:互動迴圈/開頁在 PS(edit-parse 已移植)"),
    ("via-vdf-refill", "VDF_SystemManager refill → VDF_MDL012", "綠:純轉發(雙閘判斷已移植 gates)"),
    ("git pull/add/commit/push", "git(版控)", "不 PY 化(工具本體)"),
]


def recent() -> dict:
    """這兩天實用短令 → PY 正主對照(對話實錄彙整;PY 化現況誠實標)。"""
    rows = [{"filename": c, "py_owner": o, "state": st,
             "lamp": "綠" if st.startswith(("PY", "綠")) else ("黃" if st.startswith("黃") else "白")}
            for c, o, st in RECENT_TWO_DAYS]
    return {"verb": "recent", "hub": TAG, "days": "2026-10-05/06", "commands": len(rows), "rows": rows}


def _norm_body(body: str) -> str:
    out = []
    for ln in body.splitlines():
        t = ln.split("#", 1)[0].strip()
        if t:
            out.append(re.sub(r"\s+", " ", t))
    return "\n".join(out)


def _shape(body: str) -> str:
    """本體形狀分類(結構化分類詳述):純轉發 / 帶邏輯 / 啟動開頁 / 環境閘 / 其他。"""
    fwd = "via-vcgc" in body
    logic = any(k in body for k in ("Read-Host", "while (", "ConvertTo-", "-match"))
    launch = any(k in body for k in ("Start-Process", "msedge", "Invoke-Item"))
    envg = "$env:" in body
    if fwd and not logic and not launch:
        return "純轉發"
    if logic:
        return "帶邏輯(PY 化對象)"
    if launch:
        return "啟動開頁(照律留 PS)"
    if envg:
        return "環境閘(gates 已有 PY 口)"
    return "其他"


def audit() -> dict:
    """結構化稽核:重複(同名多檔,最新活)· 同功能(異名同體,正規化雜湊)· 缺失(轉發目標無尾版)· 形狀分類。"""
    import hashlib
    files = _reg_files()
    defs = {}      # name -> [(file, body)]
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        marks = list(_FN_RX.finditer(text))
        for i, m in enumerate(marks):
            body = text[m.end():(marks[i + 1].start() if i + 1 < len(marks) else len(text))]
            defs.setdefault(m.group(1), []).append((f.name, body))
    dup_rows = [{"filename": n, "defs": len(v), "active": v[-1][0], "superseded": [fn for fn, _ in v[:-1]],
                 "state": "重複定義(最新活)", "lamp": "黃"}
                for n, v in sorted(defs.items()) if len(v) > 1]
    by_hash = {}
    for n, v in defs.items():
        h = hashlib.md5(_norm_body(v[-1][1]).encode("utf-8")).hexdigest()[:10]
        by_hash.setdefault(h, []).append(n)
    same_rows = [{"filename": "+".join(sorted(ns)), "n": len(ns), "state": "異名同體(同功能)", "lamp": "黃"}
                 for h, ns in sorted(by_hash.items()) if len(ns) > 1]
    roots = [HERE, VIA / "functional modules" / "VRN", VIA / "functional modules" / "VDF",
             VIA / "supportive modules" / "70_VRN_Rules", VIA / "supportive modules",
             VIA / "supportive modules" / "network"]
    missing = []
    for n, v in sorted(defs.items()):
        for mm in _PY_TARGET_RX.finditer(v[-1][1]):
            t = next(g for g in mm.groups() if g)
            if not any(list(r.glob(t + "*_v*.py")) or list(r.glob(t + "_v*.py")) or list(r.glob(t + "*.py")) for r in roots):
                missing.append({"filename": n, "target": t, "state": "缺失:轉發目標無尾版", "lamp": "紅"})
    shapes = {}
    for n, v in defs.items():
        shapes[_shape(v[-1][1])] = shapes.get(_shape(v[-1][1]), 0) + 1
    return {"verb": "audit", "hub": TAG, "reg_files": len(files), "functions": len(defs),
            "重複": len(dup_rows), "異名同體": len(same_rows), "缺失": len(missing), "形狀": shapes,
            "rows": dup_rows + same_rows + missing}


def plan() -> dict:
    """合併計畫(只列不動 .ps1):活令依第一個 PY 正主分群——動作不多、指令誇張多 → N 令收斂成 M 群。"""
    inv = inventory()
    groups = {}
    for r in inv["rows"]:
        key = (r["py_targets"][0] if r["py_targets"] else ("PS原生:" + ("啟動開頁" if r["lamp"] == "白" else "邏輯")))
        groups.setdefault(key, []).append(r["filename"])
    rows = [{"filename": k, "cmds": len(v), "members": v[:8] + (["…+%d" % (len(v) - 8)] if len(v) > 8 else []),
             "proposal": ("併入 hub run " + k if not k.startswith("PS原生") else
                          ("留 PS(啟動/UI 職能)" if "啟動" in k else "逐批 PY 化(黃單)")),
             "lamp": "綠" if not k.startswith("PS原生") else ("白" if "啟動" in k else "黃")}
            for k, v in sorted(groups.items(), key=lambda kv: -len(kv[1]))]
    return {"verb": "plan", "hub": TAG, "total_cmds": inv["commands"], "groups": len(rows),
            "収斂": f"{inv['commands']} 令 → {len(rows)} 群(PY 正主為單位)",
            "rule": "綠群=hub run 一口打通 · 黃群=邏輯移植排程 · 白群=照 PY 功能律留 PS;.ps1 零觸碰",
            "rows": rows}


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":   # 獨立 MAIN 律:自立閘座,入口誠實記
        os.environ["VIA_FROM_VCGC"] = "YES"
        print(f"[HUB] 獨立 MAIN(standalone)· {TAG}")
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["recent"]:
        print(json.dumps(recent(), ensure_ascii=False, indent=1))
        return 0
    if args[:1] == ["audit"]:
        print(json.dumps(audit(), ensure_ascii=False, indent=1))
        return 0
    if args[:1] == ["plan"]:
        print(json.dumps(plan(), ensure_ascii=False, indent=1))
        return 0
    if args[:1] == ["inventory"]:
        out = inventory()
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    if args[:1] == ["run"]:
        if len(args) < 2:
            print("[拒跑] run <短令> [args…]")
            return 2
        return run_cmd(args[1:])
    if args[:1] == ["edit-parse"]:
        print(json.dumps({"line": " ".join(args[1:]), "flags": edit_parse(" ".join(args[1:]))}, ensure_ascii=False))
        return 0
    if args[:1] == ["gates"]:
        print(json.dumps(gates(), ensure_ascii=False, indent=1))
        return 0
    print(__doc__)
    return 0


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        p, f = (p + 1, f) if cond else (p, f + 1)
        print(f"  [{'OK' if cond else 'FAIL'}] {name}")

    inv = inventory()
    chk("① 盤點:PS 短令鏈讀得到 · 至少 10 令 · 每列帶 py_targets/ps_logic/燈",
        inv["commands"] >= 10 and all("py_targets" in r and "lamp" in r for r in inv["rows"]))
    chk("② 盤點誠實:有綠(純轉發)也有黃(PS 邏輯待 PY 化)——不假全綠",
        inv["tally"].get("綠", 0) >= 1 and (inv["tally"].get("黃", 0) + inv["tally"].get("白", 0)) >= 1)
    chk("③ 邏輯移植 edit-parse 三式同 PS 判:+add · -remove · start=日期 · 其他 None",
        edit_parse("+TW_FIN=2330") == ["--add", "TW_FIN=2330"]
        and edit_parse("-TW_FIN=2330") == ["--remove", "TW_FIN=2330"]
        and edit_parse("TW_MARKET=2022-01-01") == ["--start", "TW_MARKET=2022-01-01"]
        and edit_parse("隨便一句") is None)
    g = gates()
    chk("④ 雙閘只讀不代設:回報現況 · 本檔不寫 CONSENT",
        "both_open" in g and "environ[\"VIA_NET_CONSENT\"] =" not in Path(__file__).read_text(encoding="utf-8"))
    chk("⑤ run 未知短令誠實拒 rc2;帶加速器橋", run_cmd(["via-不存在的令"]) == 2
        and "[VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    rc_r, rc_a, rc_p = recent(), audit(), plan()
    chk("⑥ recent:兩日短令清單 ≥ 12 令 · 各帶 PY 正主與燈", rc_r["commands"] >= 12
        and all(r.get("py_owner") and r.get("lamp") for r in rc_r["rows"]))
    chk("⑦ audit:重複/異名同體/缺失/形狀四類都有數字(誠實,缺失可為 0)",
        all(k in rc_a for k in ("重複", "異名同體", "缺失", "形狀")) and rc_a["functions"] > 100)
    chk("⑧ plan:收斂群數 < 令數 · 每群帶 proposal", rc_p["groups"] < rc_p["total_cmds"]
        and all(r.get("proposal") for r in rc_p["rows"]))
    print(f"[計] {TAG} 自測 {p}/{p + f} · {'PASS' if f == 0 else 'FAIL'}")
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
