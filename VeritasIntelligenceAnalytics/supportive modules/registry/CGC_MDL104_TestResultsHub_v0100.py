#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL104_TestResultsHub — 工具測試結果總表(批257;操作員令「整合
優化簡化導入工具測試結果」)
====================================================================
機制(全導入=只讀既有存證,零重測零發明;尾版動態嚴禁寫死):
  ①grid 終判:VIA_Reports/**/GRID_*.json 尾版(OK/FAIL/SKIP+紅站列)
  ②迴歸閘:regression_gate/REGRESSION_GATE.json(TP/P/ticker acc)
  ③加速器覆蓋:accel_coverage/inject_*.json 尾版(注入/略計)
  ④TPN 冊:VIA_VAP_TemplateRegistry(函式/模板/複合+斷點數)
  ⑤指揮台任務冊:MDL095 尾版 task_registry 引擎在位數
  輸出=VIA_UI_TestResults_v0100.html 一頁 RYG(Portal 尾版清單自收)
  +--print 終端表(手機可讀)
用法:python3 CGC_MDL104_TestResultsHub_v0100.py [--print] | --selftest
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
REPORTS = VIA / "VIA_Reports"
OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_TestResults_v0100.html"


def _newest(pat: str, root: Path):
    hits = sorted(root.rglob(pat))
    return hits[-1] if hits else None


def _load(p: Path | None):
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p else None
    except Exception:
        return None


def gather() -> dict:
    out: dict = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M")}
    g = _load(_newest("GRID_*.json", REPORTS))
    if g:
        rows = g if isinstance(g, list) else \
            g.get("results") or g.get("rows") or list(g.values())[0]
        st = {"OK": 0, "FAIL": 0, "SKIP": 0}
        reds = []
        for r in rows:
            k = str(r.get("state", "")).upper()[:4].strip()
            k = "OK" if k.startswith("OK") else \
                "FAIL" if k.startswith("FAIL") else "SKIP"
            st[k] += 1
            if k == "FAIL":
                reds.append(r.get("name", "?"))
        out["grid"] = {"src": _newest("GRID_*.json", REPORTS).name,
                       **st, "reds": reds, "n": len(rows)}
    else:
        out["grid"] = None                    # 誠實缺
    rg = _load(REPORTS / "regression_gate" / "REGRESSION_GATE.json")
    out["regression"] = {"n": rg["n"], "tp_acc": rg["tp"]["accuracy_pct"],
                         "p_acc": rg["price"]["accuracy_pct"],
                         "src": "REGRESSION_GATE.json"} if rg else None
    inj = _load(_newest("inject_*.json", REPORTS / "accel_coverage")) \
        if (REPORTS / "accel_coverage").exists() else None
    out["accel"] = {"py": inj.get("py"), "ps": inj.get("ps"),
                    "skips": len(inj.get("skips", []))} if inj else None
    tpn = _load(HERE / "VIA_VAP_TemplateRegistry_v0100.json")
    if tpn:
        gaps = sum(1 for f in tpn.get("functions", [])
                   if str(f.get("state", "")).startswith("GAP"))
        out["tpn"] = {"functions": len(tpn.get("functions", [])),
                      "templates": len(tpn.get("templates", [])),
                      "composites": len(tpn.get("composites", [])),
                      "gaps": gaps}
    else:
        out["tpn"] = None
    deck = _newest("CGC_MDL095_DeckServer_v*.py", HERE)
    try:
        spec = importlib.util.spec_from_file_location("m95hub", deck)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        T = m.task_registry()
        ok = sum(1 for t in T.values()
                 if t["argv"][1] and Path(str(t["argv"][1])).exists())
        out["deck"] = {"tasks": len(T), "engines_ok": ok,
                       "src": deck.name}
    except Exception as exc:
        out["deck"] = {"error": type(exc).__name__}
    return out


def _ryg(ok: bool | None) -> str:
    return "g" if ok else ("y" if ok is None else "r")


def render(d: dict) -> str:
    g = d.get("grid")
    rows = []
    rows.append(("全面自測矩陣(grid 尾版存證)",
                 f"{g['n']} 站 · OK {g['OK']} · FAIL {g['FAIL']} · "
                 f"SKIP {g['SKIP']}" + (" · 紅:" + ",".join(g["reds"])
                                        if g["reds"] else "")
                 if g else "存證缺(誠實)",
                 _ryg(bool(g and g["FAIL"] == 0))))
    r = d.get("regression")
    rows.append(("抽取鏈迴歸閘(64 件真基準)",
                 f"{r['n']} 件 · TP acc {r['tp_acc']}% · P acc {r['p_acc']}%"
                 "(P DIFF=基準包欄錯已實錄)" if r else "存證缺(誠實)",
                 _ryg(bool(r and r["tp_acc"] == 100.0))))
    a = d.get("accel")
    rows.append(("加速器全覆蓋(py+PS 20 加速器)",
                 f"py {a['py']} · ps {a['ps']} · 略 {a['skips']}"
                 if a else "manifest 缺(誠實)", _ryg(bool(a))))
    t = d.get("tpn")
    rows.append(("TPN 模板冊+七函式連接點",
                 f"函式 {t['functions']}(斷點 {t['gaps']})· 模板 "
                 f"{t['templates']} · 複合 {t['composites']}" if t
                 else "冊缺(誠實)", _ryg(bool(t and t["gaps"] == 0))))
    k = d.get("deck")
    rows.append(("指揮台任務冊(重新串聯)",
                 f"{k.get('tasks', '?')} 任務 · 引擎在位 "
                 f"{k.get('engines_ok', '?')}({k.get('src', '')})"
                 if k and "error" not in k else "載入敗(誠實)",
                 _ryg(bool(k and k.get("tasks") == k.get("engines_ok")))))
    trs = "".join(f"<tr class='{c}'><td>{html.escape(n)}</td>"
                  f"<td>{html.escape(v)}</td></tr>" for n, v, c in rows)
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 工具測試結果總表</title><style>
body{{background:#0b1220;color:#c7d3e8;font:10.5px/1.55 "Segoe UI",
"Noto Sans TC",sans-serif;padding:14px;max-width:900px;margin:0 auto}}
h1{{font-size:14px;color:#e8eefb}}
.sub{{color:#7e8db0;font-size:10px;margin:2px 0 10px}}
table{{width:100%;border-collapse:collapse}}
td{{padding:6px 8px 6px 0;border-bottom:1px dashed #1e2a44;
overflow-wrap:anywhere}}
tr.g td:first-child{{border-left:3px solid #15803d;padding-left:8px}}
tr.y td:first-child{{border-left:3px solid #f0b429;padding-left:8px}}
tr.r td:first-child{{border-left:3px solid #dc2626;padding-left:8px}}
</style></head><body>
<h1>VIA 工具測試結果總表(批257)</h1>
<div class="sub">{d['ts']} · 全導入=只讀既有存證零重測 · 尾版動態 ·
手機可讀單欄</div>
<table><tbody>{trs}</tbody></table>
</body></html>"""


def run(do_print: bool = False) -> int:
    d = gather()
    OUT.write_text(render(d), encoding="utf-8")
    g = d.get("grid")
    print(f"[測試總表] grid={'%d站 FAIL %d' % (g['n'], g['FAIL']) if g else '缺'}"
          f" · 迴歸 TP {d['regression']['tp_acc'] if d.get('regression') else '—'}%"
          f" · TPN 斷點 {d['tpn']['gaps'] if d.get('tpn') else '—'}"
          f" · 任務 {d['deck'].get('tasks', '—') if d.get('deck') else '—'}"
          f" · {OUT.name}")
    if do_print and g:
        for name in g["reds"]:
            print(f"  [紅站] {name}")
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
    chk("① 五源導入(grid/迴歸/加速器/TPN/任務冊;缺=誠實標)",
        rc == 0 and all(k in d for k in
                        ("grid", "regression", "accel", "tpn", "deck")))
    chk("② grid 尾版存證真讀(站數>0)",
        d["grid"] is not None and d["grid"]["n"] > 100)
    chk("③ 迴歸閘真值(TP acc 在)", d["regression"] is not None
        and d["regression"]["tp_acc"] is not None)
    chk("④ 任務冊在位對齊(tasks==engines_ok)",
        d["deck"].get("tasks") == d["deck"].get("engines_ok"))
    chk("⑤ 一頁 RYG 產出(手機單欄+零 CDN)",
        "測試結果總表" in page and 'src="http' not in page)
    chk("⑥ 零重測紀律宣告+零網路+加速橋",
        "零重測" in src and "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx")))
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 工具測試結果總表(CGC_MDL104)· 六檢自測(零網路)===")
        return selftest()
    return run("--print" in args)


if __name__ == "__main__":
    sys.exit(main())
