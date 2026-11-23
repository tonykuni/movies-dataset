#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL269_PyCommandHub v0100 — 短指令 PY 樞紐(批1657 操作員令「所有短指令 PY 化整合化包含邏輯 加入加速器」)。

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
TAG = "CGC_MDL269_PyCommandHub_v0100"

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


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":   # 獨立 MAIN 律:自立閘座,入口誠實記
        os.environ["VIA_FROM_VCGC"] = "YES"
        print(f"[HUB] 獨立 MAIN(standalone)· {TAG}")
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
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
    print(f"[計] {TAG} 自測 {p}/{p + f} · {'PASS' if f == 0 else 'FAIL'}")
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
