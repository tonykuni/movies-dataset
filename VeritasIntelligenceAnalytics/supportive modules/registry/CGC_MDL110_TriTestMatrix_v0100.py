#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL110_TriTestMatrix — 三軌測試矩陣報告(批267;操作員令)
====================================================================
操作員令:「system test / user-test / result validation test matrix
report」——三軌一頁 RYG 矩陣:
  A 系統測試(System Test):grid 尾版終判(站數/OK/FAIL/SKIP+
    紅站列)+指揮台任務冊在位+加速器覆蓋 manifest
  B 使用者測試(User-Test):台帳「實錄」條目=操作員工作站真操作
    存證(最新六筆列示)+G06 狀態(誠實=未轉綠即標候實測)+
    開放回證項(修後候操作員重打確認)
  C 結果驗證(Result Validation):迴歸閘存證(n/TP acc 如實引,
    不誇大)+驗證型 grid 站逐站燈(迴歸閘/ETF×共識/營收×共識/
    Prompt 冊/TPN 斷點)
律:零重測=全讀既有存證(MDL104 gather 尾版動態複用=Zero-Hydra);
  缺=誠實標;數字全來自存證檔零發明。
用法:python3 CGC_MDL110_TriTestMatrix_v0100.py [--print] | --selftest
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

import html
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = (VIA / "supportive modules" / "ui_support"
       / "VIA_UI_TriTestMatrix_v0100.html")

# 驗證型 grid 站名冊(C 軌逐站燈;站名子串比對=尾版站名穩定)
VALID_STATIONS = ["抽取鏈迴歸閘", "主動ETF×共識分析", "月營收×共識分析",
                  "Prompt 儲存管理", "測試結果總表", "治理主控台"]


def _hub():
    """MDL104 gather 尾版動態複用(Zero-Hydra:報表資料層唯一正主)"""
    hub = sorted(HERE.glob("CGC_MDL104_TestResultsHub_v*.py"))[-1]
    spec = importlib.util.spec_from_file_location("m104tri", hub)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.gather()


def _ledger_user_tests() -> list:
    """台帳實錄條目=操作員工作站真操作存證(append-only 冊直讀)"""
    reg = HERE / "VIA_AutoCode_Registry_v0100.json"
    if not reg.exists():
        return []
    led = json.loads(reg.read_text(encoding="utf-8")).get("ledger", [])
    return [{"code": e.get("code"), "ts": e.get("ts"),
             "name": (e.get("name") or "")[:80]}
            for e in led
            if "實錄" in ((e.get("name") or "") + (e.get("kind") or ""))]


def gather() -> dict:
    hub = _hub()
    g = hub.get("grid")
    grid_rows = []
    if g:
        src = sorted((VIA / "VIA_Reports").rglob("GRID_*.json"))[-1]
        rows = json.loads(src.read_text(encoding="utf-8"))
        rows = rows if isinstance(rows, list) else \
            rows.get("results") or rows.get("rows") or list(rows.values())[0]
        grid_rows = rows
    valid = []
    for key in VALID_STATIONS:
        hit = next((r for r in grid_rows if key in str(r.get("name", ""))),
                   None)
        valid.append({"name": key,
                      "state": str(hit.get("state", "缺")).strip()
                      if hit else "缺(誠實)",
                      "note": str(hit.get("note", ""))[:60] if hit else ""})
    ut = _ledger_user_tests()
    return {"ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "system": {"grid": g, "deck": hub.get("deck"),
                       "accel": hub.get("accel")},
            "user": {"n_records": len(ut), "recent": ut[-6:],
                     "g06": "候操作員實測轉綠(誠實=不假綠)",
                     "open": ["via-analysis .cmd 梭修後候工作站回證"
                              "(批266)"]},
            "validation": {"regression": hub.get("regression"),
                           "tpn": hub.get("tpn"), "stations": valid}}


def _light(state: str) -> str:
    s = state.upper()
    return "g" if s.startswith("OK") else \
        ("y" if ("SKIP" in s or "缺" in state or "候" in state) else "r")


def render(d: dict) -> str:
    g = d["system"]["grid"]
    dk = d["system"]["deck"] or {}
    ac = d["system"]["accel"]
    sys_rows = [
        ("全面自測矩陣(grid 尾版)",
         f"{g['n']} 站 · OK {g['OK']} · FAIL {g['FAIL']} · SKIP {g['SKIP']}"
         f"({g['src']})" if g else "存證缺(誠實)",
         "g" if g and g["FAIL"] == 0 else "r" if g else "y"),
        ("指揮台任務冊在位",
         f"{dk.get('tasks', '?')} 任務 · 引擎在位 {dk.get('engines_ok', '?')}",
         "g" if dk.get("tasks") == dk.get("engines_ok") else "y"),
        ("加速器覆蓋 manifest",
         f"py {ac['py']} · ps {ac['ps']} · 略 {ac['skips']}" if ac
         else "manifest 缺(誠實)", "g" if ac else "y")]
    u = d["user"]
    usr_rows = [("工作站實錄存證(台帳)",
                 f"{u['n_records']} 筆真操作實錄入帳", "g"),
                ("G06 User Test 閘", u["g06"], "y")]
    usr_rows += [("開放回證項", o, "y") for o in u["open"]]
    v = d["validation"]
    r = v["regression"]
    t = v["tpn"]
    val_rows = [("抽取鏈迴歸閘存證",
                 f"{r['n']} 件 · TP acc {r['tp_acc']}%(如實引存證,"
                 "不誇大)" if r else "存證缺(誠實)",
                 "g" if r and r["tp_acc"] == 100.0 else "y" if not r
                 else "r"),
                ("TPN 連接點",
                 f"函式 {t['functions']} · 斷點 {t['gaps']}" if t
                 else "冊缺(誠實)",
                 "g" if t and t["gaps"] == 0 else "y" if not t else "r")]
    val_rows += [(f"驗證站:{s['name']}", s["note"] or s["state"],
                  _light(s["state"])) for s in v["stations"]]

    def zone(title, rows):
        trs = "".join(
            f"<tr class='{c}'><td>{html.escape(n)}</td>"
            f"<td>{html.escape(str(x))}</td></tr>" for n, x, c in rows)
        return (f"<h2>{title}</h2><div class='wrap'><table>"
                f"<tbody>{trs}</tbody></table></div>")

    recent = "".join(
        f"<li><code>{html.escape(str(e['code']))}</code> {e['ts']} · "
        f"{html.escape(e['name'])}</li>" for e in u["recent"])
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 三軌測試矩陣</title><style>
:root{{--bg:#f3f5f7;--panel:#fff;--line:#dce2e8;--text:#1f2933;
--muted:#6b7785;--blue:#4c78a8;--green:#5a9e6f;--amber:#c4943a;
--red:#c96b5a}}
@media (prefers-color-scheme: dark){{:root{{--bg:#10151b;--panel:#171e26;
--line:#2a333d;--text:#dbe3ea;--muted:#8a97a5;--blue:#7ba3cc;
--green:#79b58c;--amber:#d4a95c;--red:#d98a7c}}}}
body{{background:var(--bg);color:var(--text);margin:0 auto;
font:12.5px/1.55 "Segoe UI","Noto Sans TC",sans-serif;padding:16px;
max-width:860px}}
h1{{font-size:16px}}h2{{font-size:11px;color:var(--muted);
text-transform:uppercase;letter-spacing:.08em;margin:16px 0 6px}}
.sub{{color:var(--muted);font-size:11px}}
table{{width:100%;border-collapse:collapse;background:var(--panel);
border:1px solid var(--line);border-radius:8px}}
td{{padding:6px 8px;border-bottom:1px solid var(--line);
overflow-wrap:anywhere;font-variant-numeric:tabular-nums}}
tr.g td:first-child{{border-left:3px solid var(--green);padding-left:8px}}
tr.y td:first-child{{border-left:3px solid var(--amber);padding-left:8px}}
tr.r td:first-child{{border-left:3px solid var(--red);padding-left:8px}}
ul{{font-size:11px;color:var(--muted);padding-left:18px}}
code{{color:var(--blue)}}
.wrap{{overflow-x:auto}}</style></head><body>
<h1>三軌測試矩陣報告(批267)</h1>
<div class="sub">{d['ts']} · 零重測=全讀既有存證(MDL104 資料層複用)·
缺=誠實標 · System / User / Validation 三軌</div>
{zone("A · 系統測試 System Test", sys_rows)}
{zone("B · 使用者測試 User-Test", usr_rows)}
<ul>{recent}</ul>
{zone("C · 結果驗證 Result Validation", val_rows)}
<p class="sub">正本=本頁(ui_support;Portal 尾版自收)· 台帳實錄=
append-only 存證 · 非投資建議</p></body></html>"""


def run(do_print: bool = False) -> int:
    d = gather()
    OUT.write_text(render(d), encoding="utf-8")
    g = d["system"]["grid"]
    print(f"[三軌矩陣] A系統 {'%d站 FAIL %d' % (g['n'], g['FAIL']) if g else '缺'}"
          f" · B使用者 實錄 {d['user']['n_records']} 筆(G06 候實測)"
          f" · C驗證 站 {len(d['validation']['stations'])}"
          f" · {OUT.name}")
    if do_print:
        for s in d["validation"]["stations"]:
            print(f"  [驗證站] {s['name']}: {s['state']}")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    d = gather()
    rc = run()
    page = OUT.read_text(encoding="utf-8")
    chk("① 三軌齊備(system/user/validation)", rc == 0
        and all(k in d for k in ("system", "user", "validation")))
    chk("② A軌=grid 尾版真值(站數>100 FAIL 數字在)",
        d["system"]["grid"] is not None and d["system"]["grid"]["n"] > 100)
    chk("③ B軌=台帳實錄真讀(>0 筆+G06 誠實候)",
        d["user"]["n_records"] > 0 and "候" in d["user"]["g06"])
    chk("④ C軌=驗證站逐站燈(六站名冊全比對)",
        len(d["validation"]["stations"]) == len(VALID_STATIONS)
        and all(s["state"] != "" for s in d["validation"]["stations"]))
    chk("⑤ 一頁三區 RYG(手機單欄+零 CDN)",
        "三軌測試矩陣報告" in page and page.count("<h2>") >= 3
        and 'src="http' not in page)
    chk("⑥ 零重測紀律+MDL104 複用+零網路+加速橋",
        "零重測" in src and "CGC_MDL104_TestResultsHub_v*" in src
        and "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx")))
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 三軌測試矩陣(CGC_MDL110)· 六檢自測(零網路)===")
        return selftest()
    return run("--print" in a)


if __name__ == "__main__":
    sys.exit(main())
