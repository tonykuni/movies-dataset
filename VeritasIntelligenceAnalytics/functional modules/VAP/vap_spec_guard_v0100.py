#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vap_spec_guard_v0100 — VAP 圖規鎖守衛(TOOL-083)
====================================================================
操作員上傳(批72,2026-08-20):VAP v017 全圖表規格五件——40
canonical 圖規清冊(json+html)+40 結構快照+工作台。本器為規格
一致性守衛:規格冊↔快照冊逐碼對勘+硬性軸契約稽核。
鎖(悉出自上傳冊,零發明):
  ① 軸鎖 — 單軸 4 間隔 5 刻度;雙軸左右各 4 間隔且刻度數相同;
     合法步階族 2/2.5/5×10ⁿ(10=下一十進位邊界)。
  ② 配色鎖 — palette=snsDeep(sns.color_palette() 十色循環);
     相關熱圖 diverging 15 stops、zmid=0、dtick 0.05。
  ③ 版本鎖 — Seaborn 0.13.2 grammar/Plotly 2.35.0/append-only。
  ④ 浮點容忍 0.000001。
用法:
  via-vapguard              → 對勘現役最新規格冊(動態 glob)
  via-vapguard --selftest   → 十檢(讀收容冊,零網路)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent          # functional modules/VAP
SPEC_DIR = HERE / "spec"
MOTTO = "VERITAS INTELLIGENCE ANALYTICS · OBSERVA · INTELLEGE · PRAEVIDE"


def newest(pattern: str) -> Path | None:
    hits = sorted(SPEC_DIR.glob(pattern))
    return hits[-1] if hits else None


def load_pair() -> tuple[dict | None, dict | None, str]:
    sp = newest("VIA_VAP_All_Chart_Specs_v0*.json")
    sn = newest("VIA_VAP_40_Structural_Snapshots_v0*.json")
    if sp is None or sn is None:
        return None, None, "規格冊/快照冊缺(誠實)"
    return (json.loads(sp.read_text(encoding="utf-8-sig")),
            json.loads(sn.read_text(encoding="utf-8-sig")),
            f"{sp.name} ↔ {sn.name}")


def audit(specs: dict, snaps: dict) -> dict:
    """規格↔快照對勘;回 {checks:[{rule,passed,note}], fails}"""
    out = []

    def add(rule, passed, note=""):
        out.append({"rule": rule, "passed": bool(passed), "note": note})

    charts = specs.get("charts", [])
    codes_sp = [c["code"] for c in charts]
    snap_list = snaps.get("snapshots", [])
    codes_sn = [s["code"] for s in snap_list]
    add("規格冊 40 碼唯一", len(codes_sp) == 40 and len(set(codes_sp)) == 40,
        f"{len(codes_sp)} 碼")
    add("快照冊 40 碼唯一+PASS", len(codes_sn) == 40 and len(set(codes_sn)) == 40
        and snaps.get("status") == "PASS" and snaps.get("coverage") == 40)
    add("逐碼對映零缺漏", set(codes_sp) == set(codes_sn),
        f"差集 {sorted(set(codes_sp) ^ set(codes_sn))[:4] or '∅'}")
    add("浮點容忍鎖", snaps.get("floatTolerance") == 0.000001)
    # 軸契約稽核(快照層)
    bad_axis = []
    for s in snap_list:
        ac = s.get("axisContract")
        if ac is None:
            continue
        if not (ac.get("intervalCount") == 4 and ac.get("tickCount") == 5
                and ac.get("stepFamily") == [2, 2.5, 5, 10]):
            bad_axis.append(s["code"])
        else:
            # 步階必屬 2/2.5/5/10×10ⁿ
            for step in (ac.get("leftStep"), ac.get("rightStep")):
                if step is None:
                    continue
                x = float(step)
                while x >= 20:
                    x /= 10
                while 0 < x < 2:
                    x *= 10
                if round(x, 6) not in (2.0, 2.5, 5.0, 10.0):
                    bad_axis.append(s["code"] + f"(step {step})")
    add("軸鎖 4間隔5刻度+步階族", not bad_axis, "、".join(bad_axis[:5]) or "全過")
    # 雙軸一致性:hasDualAxis ⇒ yaxis2 在 axisKeys
    bad_dual = [s["code"] for s in snap_list
                if s.get("hasDualAxis") and "yaxis2" not in s.get("axisKeys", [])
                and "xaxis2" not in s.get("axisKeys", [])]
    add("雙軸鍵一致", not bad_dual, "、".join(bad_dual[:5]) or "全過")
    # 配色鎖
    bad_pal = [s["code"] for s in snap_list if s.get("palette") != "snsDeep"]
    add("配色鎖 snsDeep 全覆蓋", not bad_pal, "、".join(bad_pal[:5]) or "40/40")
    hm = next((s.get("heatmap") for s in snap_list if s.get("heatmap")), None)
    add("熱圖鎖(15 stops·zmid0·dtick.05)",
        hm and hm.get("stops") == 15 and hm.get("zmid") == 0 and hm.get("dtick") == 0.05,
        (hm or {}).get("expression", "缺"))
    fails = [c for c in out if not c["passed"]]
    return {"checks": out, "fails": len(fails)}


def rich_matrix(title, rows):
    try:
        from rich import box
        from rich.console import Console
        from rich.table import Table
        t = Table(title=title, box=box.SIMPLE_HEAVY, title_style="bold",
                  header_style="bold cyan", pad_edge=False)
        for c in ["態", "鎖", "註"]:
            t.add_column(c, overflow="fold", no_wrap=False)
        for r in rows:
            st = "PASS" if r["passed"] else "FAIL"
            t.add_row(f"[{'green' if r['passed'] else 'red'}]{st}[/]", r["rule"], r["note"])
        Console().print(t)
    except Exception:
        for r in rows:
            print(f"  [{'PASS' if r['passed'] else 'FAIL'}] {r['rule']} {r['note']}")


def run() -> int:
    specs, snaps, src = load_pair()
    if specs is None:
        print(f"  [SKIP] {src}")
        return 0
    print(f"  [冊] {src}(動態最新)")
    r = audit(specs, snaps)
    rich_matrix("VAP 圖規鎖對勘矩陣(規格↔快照)", r["checks"])
    print(f"  [計] 鎖 {len(r['checks'])} · FAIL {r['fails']}(誠實)")
    return 1 if r["fails"] else 0


def selftest() -> int:
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    specs, snaps, src = load_pair()
    chk("雙冊在位(動態 glob)", specs is not None, f"({src})")
    if specs is None:
        return 1
    cov = specs.get("coverage") or {}
    chk("規格冊結構", cov.get("canonicalCharts") == 40 and len(specs.get("charts", [])) == 40
        and "axisContract" in specs and "palettes" in specs
        and cov.get("builderBaselineCharts") == 28
        and cov.get("appendOnlyStatisticalExtensions") == 12)
    chk("版本鎖", specs.get("version") == snaps.get("version") == "v017")
    r = audit(specs, snaps)
    chk("八鎖對勘全過", r["fails"] == 0, f"({len(r['checks'])} 鎖)")
    # 破壞性驗證:壞快照必抓
    import copy
    bad = copy.deepcopy(snaps)
    bad["snapshots"][0]["palette"] = "viridis"
    bad["snapshots"][10]["axisContract"]["tickCount"] = 6
    rb = audit(specs, bad)
    chk("壞冊必抓(配色/軸鎖)", rb["fails"] >= 2)
    # 清冊頁零外連+40 列
    page = newest("VIA_VAP_All_Chart_Specs_v0*.html")
    h = page.read_text(encoding="utf-8") if page else ""
    chk("清冊頁零外連+40 列", page is not None and 'src="http' not in h
        and h.count("VAP-CH-") >= 40 and "VISUAL LOCK" in h)
    # 工作台收容在位(ui 家族)
    wb = sorted((HERE / "ui").glob("VAP_Workbench_v0*.html"))
    chk("工作台家族(動態最新)", bool(wb), f"({wb[-1].name if wb else '缺'})")
    # 步階正規化器
    def fam(x):
        while x >= 20:
            x /= 10
        while 0 < x < 2:
            x *= 10
        return round(x, 6)
    chk("步階族正規化", fam(20000000) == 2.0 and fam(0.05) == 5.0
        and fam(2.5) == 2.5 and fam(0.25) == 2.5 and fam(3) == 3.0)
    n = 8 - len(fails)
    print(f"  [計] 八檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        print("=== VAP 圖規鎖守衛 v0100 · 八檢(讀收容冊零網路)===")
        sys.exit(selftest())
    print("=== VAP 圖規鎖守衛 v0100 · 規格↔快照對勘(TOOL-083)===")
    sys.exit(run())
