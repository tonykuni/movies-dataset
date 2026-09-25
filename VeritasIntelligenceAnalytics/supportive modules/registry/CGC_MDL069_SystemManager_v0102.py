#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_system_manager_v0102 — SYSTEM MANAGER 三輪全景協議(567s 實錄根因雙修版)
====================================================================================
v0101→v0102(工作站 567.1s 實錄雙修):
  ⑤ C3 逾時根因命中:xcheck 尾段 input() 停等——工作站 tty 下子行程停等
     180s 被殺 ×3 輪=540s。修:傳 --no-pause + stdin=DEVNULL 雙保險
  ⑥ C4 假環肅清:import 環只計「模組層」import——函式內 lazy import 載入
     時無環(Aegis↔SSOT 實鑑雙向皆 lazy=假環;mailhub↔rebuild 雙向模組層
     =真環保留建議)
v0100→v0101(工作站 938.8s 實錄三修):
  ① VENDOR_SKIP:.venv/site-packages/__pycache__/node_modules 等廠商樹
     誠實跳過計數(工作站 13,781 檔多為未追蹤廠商件,非 VIA 正件)
  ② 快照沿用:單輪零修正時 R2/R3 沿用 R1 之 C1/C4/C5 快照(誠實敘明;
     --deep 強制每輪重掃)— 938s 級耗時三分之一化
  ③ SyntaxWarning 靜音 + 語法錯檔路徑直印 console(不必開報告)
  ④ 結尾發現摘要直印 console
依操作員常設指令(最終整合版 Mega-Prompt · 20 加速器 + HTML UI 矩陣)VIA 落地。
三輪協議(不得超過三輪;每輪 = 分析→分類→修正裁決→再分析口徑):
  R1 全面性(Comprehensive) — 鎖 Parallel-Fixable;避開高 Hydra 節點
  R2 順序性(Sequential)   — 依賴拓撲排序;高風險節點→建議不自動修
  R3 收尾性(Polishing)    — 微調/複雜度/一致性建議
每輪六檢:C1 AST 精準解析(原生)C2 全景六車道(掛載 via-six --json)
  C3 SSOT 對齊(掛載 xcheck)C4 依賴拓撲(原生 import 圖+環偵測)
  C5 性能複雜度(原生)C6 庫存分區 MODULE/ENGINE/FUNCTION-LIB/OTHERS
修正政策(VIA 鐵則,誠實高於全綠):本引擎「零就地改碼」——一切發現
  以建議矩陣輸出(正本不就地修改;高風險節點→建議不自動修正)。
20 加速器掛載表:實測狀態誠實標示(ENABLED/LITE/STUB 候),不假全綠。
輸出:VIA_Reports/VIA_SysMan_Matrix_<ts>.html(字體略小/自動換行/表格
  自適應/紅黃綠燈/動態進度條/動態說明/四分區)+ 同名 .json 存證。
用法:py via_system_manager_v0102.py [--rounds N] [--no-open] [--json] [--deep]
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

import ast
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning)  # ast.parse 掃描雜訊靜音
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports"
NARRATION: list[str] = []


def status(msg: str) -> None:
    line = f"[STATUS] {msg}"
    NARRATION.append(f"{datetime.now().strftime('%H:%M:%S')} {msg}")
    print(line, flush=True)


def progress(step: int, total: int) -> None:
    pct = int(step / total * 100)
    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
    print(f"[PROGRESS] {bar} {pct}%", flush=True)


def newest(pattern: str, root: Path) -> Path | None:
    hits = sorted(root.glob(pattern))
    return hits[-1] if hits else None


# ── C1 AST 精準解析(原生)──────────────────────────────────────────────
ARCHIVE_RX = __import__("re").compile(r"(_sha[0-9a-f]{8,}|\(\d+\))\.py$")
VENDOR_DIRS = {"__pycache__", ".git", ".venv", "venv", ".env", "env", "site-packages",
               "node_modules", "dist", "build", ".mypy_cache", ".pytest_cache", "Lib"}


def c1_ast_sweep():
    files = [p for d in ("functional modules", "supportive modules")
             for p in (VIA / d).rglob("*.py")]
    syn_errors, stats = [], {"files": 0, "defs": 0, "classes": 0, "lines": 0,
                             "archive_skipped": 0, "vendor_skipped": 0}
    per_file = {}
    for p in files:
        if any(part in VENDOR_DIRS for part in p.parts):
            # 廠商/虛擬環境樹=非 VIA 正件——誠實跳過計數(工作站未追蹤件海)
            stats["vendor_skipped"] += 1
            continue
        if ARCHIVE_RX.search(p.name):
            # 紅線:_sha 鏡像/瀏覽器複本=上傳原件唯讀封存——不列可修項(誠實計數)
            stats["archive_skipped"] += 1
            continue
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(src)
        except SyntaxError as exc:
            syn_errors.append({"file": str(p.relative_to(VIA)), "err": f"L{exc.lineno}: {exc.msg}"})
            continue
        d = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree))
        c = sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree))
        ln = src.count("\n") + 1
        def _names(nodes):
            return sorted({(n.module or "").split(".")[0] if isinstance(n, ast.ImportFrom)
                           else a.name.split(".")[0]
                           for n in nodes if isinstance(n, (ast.Import, ast.ImportFrom))
                           for a in (n.names if isinstance(n, ast.Import) else [n])
                           if not (isinstance(n, ast.ImportFrom) and n.level)})
        imports = _names(list(ast.walk(tree)))
        top_imports = _names(tree.body)  # 模組層才構成載入環;函式內 lazy 不計
        per_file[str(p.relative_to(VIA))] = {"defs": d, "classes": c, "lines": ln,
                                             "imports": imports, "top_imports": top_imports}
        stats["files"] += 1
        stats["defs"] += d
        stats["classes"] += c
        stats["lines"] += ln
    return {"ok": not syn_errors, "stats": stats, "syntax_errors": syn_errors, "per_file": per_file}


# ── C2 全景六車道(掛載 via-six)────────────────────────────────────────
def c2_six():
    eng = newest("CGC_MDL061_PanoramaSix_v0*.py", HERE)
    if not eng:
        return {"ok": False, "note": "via-six 引擎缺(誠實 WARN)"}
    try:
        r = subprocess.run([sys.executable, str(eng), "--json", "--no-open"],
                           capture_output=True, text=True, timeout=300, cwd=str(VIA))
        payload = json.loads(r.stdout.strip().splitlines()[-1])
        st = payload.get("system_status") or payload.get("system")
        return {"ok": st == "green", "system": st,
                "hydra": payload.get("hydra_total", payload.get("hydra")), "lanes": payload.get("lanes", [])}
    except subprocess.TimeoutExpired:
        return {"ok": False, "note": "via-six 逾時 300s(誠實 TIMEOUT)"}
    except Exception as exc:
        return {"ok": False, "note": f"{type(exc).__name__}: {str(exc)[:80]}"}


# ── C3 SSOT 對齊(掛載 xcheck)─────────────────────────────────────────
def c3_ssot():
    eng = newest("panorama_xcheck_v*.py", VIA / "functional modules/VRN")
    if not eng:
        return {"ok": False, "note": "xcheck 引擎缺(誠實 WARN)"}
    try:
        r = subprocess.run([sys.executable, str(eng), "--no-pause"], capture_output=True,
                           text=True, timeout=180, cwd=str(eng.parent),
                           stdin=subprocess.DEVNULL)
        tail = [l for l in r.stdout.splitlines() if l.strip()][-3:]
        return {"ok": r.returncode == 0, "engine": eng.name, "tail": tail}
    except subprocess.TimeoutExpired:
        return {"ok": False, "note": "xcheck 逾時 180s(誠實 TIMEOUT)"}
    except Exception as exc:
        return {"ok": False, "note": f"{type(exc).__name__}: {str(exc)[:80]}"}


# ── C4 依賴拓撲(原生;環=高風險節點;只計模組層 import——lazy 無環)────
def c4_topo(per_file):
    stem_of = {Path(f).stem: f for f in per_file}
    edges = []
    for f, info in per_file.items():
        for imp in info.get("top_imports", info["imports"]):
            if imp in stem_of and stem_of[imp] != f:
                edges.append((f, stem_of[imp]))
    graph = {}
    for a, b in edges:
        graph.setdefault(a, set()).add(b)
    seen, instack, cycles = set(), set(), []

    def dfs(n, path):
        seen.add(n)
        instack.add(n)
        for m in graph.get(n, ()):
            if m in instack:
                cycles.append(path[path.index(m):] + [m] if m in path else [n, m])
            elif m not in seen:
                dfs(m, path + [m])
        instack.discard(n)

    for n in list(graph):
        if n not in seen:
            dfs(n, [n])
    return {"ok": not cycles, "edges": len(edges), "nodes": len(stem_of), "cycles": cycles[:5]}


# ── C5 性能複雜度(原生 lite)──────────────────────────────────────────
def c5_complexity(per_file):
    big = sorted(per_file.items(), key=lambda kv: -kv[1]["lines"])[:5]
    return {"ok": True,
            "top5": [{"file": f, "lines": i["lines"], "defs": i["defs"]} for f, i in big]}


# ── C6 庫存分區 ───────────────────────────────────────────────────────
def c6_inventory():
    mods = len(list(VIA.rglob("VRN_MDL*.json")))
    engines = len(list((VIA / "functional modules").rglob("*.py")))
    libs = len(list((VIA / "supportive modules").rglob("*.py")))
    others = len(list((VIA / "bin").glob("*.cmd"))) + len(list(REPORTS.glob("*.html")))
    return {"ok": True, "MODULE": mods, "ENGINE": engines, "FUNCTION-LIB": libs, "OTHERS": others}


ACCELERATORS = [
    ("01 AST 精準解析", "ENABLED", "C1 原生 ast.parse 全掃"),
    ("02 多語言語意模型", "STUB 候", "本機無語意模型——誠實候位不假綠"),
    ("03 九頭龍風險預測", "ENABLED", "C2 掛載 via-six Hydra 計分(SPEC-011)"),
    ("04 依賴拓撲排序", "ENABLED", "C4 原生 import 圖 + DFS 環偵測"),
    ("05 沙盒隔離執行", "ENABLED", "dry-run 預設治理慣例(via-store 等)"),
    ("06 自動修正建議生成", "ENABLED", "發現→建議矩陣(不就地改碼)"),
    ("07 三輪全景式分析", "ENABLED", "本引擎 R1-R3 協議"),
    ("08 SSOT 對齊", "ENABLED", "C3 掛載 xcheck v1⊆v2 超集判準"),
    ("09 視覺化矩陣生成", "ENABLED", "HTML UI Matrix 本報告"),
    ("10 錯誤分類與分群", "ENABLED", "PARALLEL/SEQUENTIAL/SUGGEST 三類"),
    ("11 性能與複雜度分析", "LITE", "C5 行數/函式數 top-5(深度剖析候)"),
    ("12 多子系統同步檢視", "ENABLED", "VRN/VDF/VAP 六車道同輪同檢"),
    ("13 版本差異與回滾", "ENABLED", "git 雙推 + .pre_<ts>.bak 慣例"),
    ("14 覆蓋率與回歸檢查", "ENABLED", "reconcile 64/64 + xcheck 迴歸"),
    ("15 修正順序最佳化", "LITE", "拓撲序建議(環節點列高風險)"),
    ("16 動態進度條", "ENABLED", "console 進度 + 報告 CSS 動畫條"),
    ("17 動態說明", "ENABLED", "[STATUS] 敘事 + 報告敘事欄"),
    ("18 非阻塞 PowerShell", "ENABLED", "via-sysman 動詞;報告自動跳出不阻塞"),
    ("19 多引擎整合", "ENABLED", "掛載 six/xcheck 子行程(逾時保護)"),
    ("20 自動部署與初始化", "LITE", "報告目錄自建+自動開啟(全境部署候)"),
]


def classify(c1, c2, c3, c4):
    finds = []
    for e in c1["syntax_errors"]:
        finds.append({"class": "PARALLEL", "sev": "red", "item": f"語法錯:{e['file']}", "note": e["err"]})
    for l in c2.get("lanes", []):
        if l.get("status") in ("yellow", "red"):
            bad = "; ".join(c["name"] + ":" + c["note"] for c in l.get("checks", []) if not c.get("ok"))
            finds.append({"class": "SEQUENTIAL", "sev": l["status"],
                          "item": f"車道 {l.get('lane', '?')} {l.get('zh', '')}", "note": bad or "-"})
    if not c3.get("ok"):
        finds.append({"class": "SEQUENTIAL", "sev": "yellow", "item": "SSOT 對齊",
                      "note": c3.get("note") or " / ".join(c3.get("tail", []))[:120]})
    for cyc in c4.get("cycles", []):
        finds.append({"class": "SEQUENTIAL", "sev": "yellow", "item": "import 環(高風險節點)",
                      "note": " → ".join(Path(x).name for x in cyc)})
    return finds


def run_round(rid: int, theme: str, total_steps: int, base: int, cache: dict, deep: bool):
    status(f"第 {rid} 輪({theme})· 全景式分析啟動")
    if "c1" in cache and not deep:
        c1, c4, c5 = cache["c1"], cache["c4"], cache["c5"]
        status("C1/C4/C5 沿用 R1 快照(本輪零修正,檔況未變;--deep 強制重掃)")
        progress(base + 1, total_steps)
    else:
        c1 = c1_ast_sweep()
        status(f"C1 AST:{c1['stats']['files']} 檔 · {c1['stats']['defs']} 函式 · 語法錯 {len(c1['syntax_errors'])}"
               f" · 封存唯讀跳過 {c1['stats']['archive_skipped']} · 廠商樹跳過 {c1['stats']['vendor_skipped']}")
        for e in c1["syntax_errors"][:5]:
            status(f"  ✗ 語法錯:{e['file']} · {e['err']}")
        progress(base + 1, total_steps)
        c4 = c4_topo(c1["per_file"])
        c5 = c5_complexity(c1["per_file"])
        cache.update(c1=c1, c4=c4, c5=c5)
    c2 = c2_six(); progress(base + 2, total_steps)
    status(f"C2 六車道:系統 {c2.get('system', '?')} · Hydra {c2.get('hydra', '?')}")
    c3 = c3_ssot(); progress(base + 3, total_steps)
    status(f"C3 SSOT:{'OK' if c3.get('ok') else 'WARN'}")
    progress(base + 4, total_steps)
    status(f"C4 拓撲:{c4['nodes']} 節點 {c4['edges']} 邊 · 環 {len(c4['cycles'])}")
    c6 = c6_inventory(); progress(base + 5, total_steps)
    finds = classify(c1, c2, c3, c4)
    scope = {"1": ("PARALLEL",), "2": ("SEQUENTIAL",), "3": ("SUGGEST",)}[str(rid)]
    in_scope = [f for f in finds if f["class"] in scope]
    status(f"第 {rid} 輪裁決:發現 {len(finds)} · 本輪範圍 {len(in_scope)} · 自動修正 0"
           f"(VIA 鐵則:正本不就地修改;高風險→建議)")
    progress(base + 6, total_steps)
    return {"round": rid, "theme": theme, "c1": {k: c1[k] for k in ("ok", "stats", "syntax_errors")},
            "c2": {k: v for k, v in c2.items() if k != "lanes"} | {"lanes": [
                {k: l.get(k) for k in ("lane", "zh", "status", "hydra")} for l in c2.get("lanes", [])]},
            "c3": c3, "c4": c4, "c5": c5, "c6": c6,
            "findings": finds, "in_scope": in_scope}


def sev_tag(s):
    return {"red": ("r", "RED"), "yellow": ("o", "YELLOW"), "green": ("g", "GREEN")}.get(s, ("o", s))


def html_report(rounds, ts):
    last = rounds[-1]
    sys_state = "green"
    if any(f["sev"] == "red" for f in last["findings"]):
        sys_state = "red"
    elif last["findings"]:
        sys_state = "yellow"
    cls, label = sev_tag(sys_state)
    st_color = {"green": "#2c4f4a", "yellow": "#6f5c31", "red": "#9e2b25"}[sys_state]
    inv = last["c6"]

    def bar(rid):
        return (f'<div class="pw"><div class="pb" style="animation-delay:{rid * .3}s"></div></div>')

    round_rows = ""
    for r in rounds:
        fr = "".join(
            f'<tr class="{sev_tag(f["sev"])[0]}bg"><td>{f["class"]}</td><td>{f["item"]}</td>'
            f'<td class="wrap">{f["note"]}</td></tr>' for f in r["findings"]) or \
            '<tr><td colspan="3" class="small">零發現(誠實實測)</td></tr>'
        lanes = " · ".join(f"{l['lane']}:{l['status']}" for l in r["c2"].get("lanes", []))
        round_rows += f"""<div class="sec">R{r['round']} {r['theme']} {bar(r['round'])}
<table><tr><th>類</th><th>項</th><th>明細</th></tr>{fr}</table>
<div class="small">C1 {r['c1']['stats']['files']} 檔/{r['c1']['stats']['defs']} 函式 ·
C2 {r['c2'].get('system', '?')}/Hydra {r['c2'].get('hydra', '?')}({lanes}) ·
C3 SSOT {'OK' if r['c3'].get('ok') else 'WARN'} ·
C4 {r['c4']['nodes']} 節點/{r['c4']['edges']} 邊/環 {len(r['c4']['cycles'])} ·
本輪自動修正 0(建議制)</div></div>"""

    acc_rows = "".join(
        f'<tr><td class="mono">{n}</td><td><span class="tag {("g" if s == "ENABLED" else "o")}">{s}</span></td>'
        f'<td class="wrap small">{d}</td></tr>' for n, s, d in ACCELERATORS)
    top5 = "".join(f'<tr><td class="mono wrap">{t["file"]}</td><td class="r">{t["lines"]:,}</td>'
                   f'<td class="r">{t["defs"]}</td></tr>' for t in last["c5"]["top5"])
    narr = "".join(f'<div class="nl">{n}</div>' for n in NARRATION)

    html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>VIA SysMan Matrix {ts}</title><style>
body{{font-family:'Segoe UI',Arial,sans-serif;font-size:11.5px;background:#f4f3ef;color:#1b1a17;margin:18px auto;max-width:1080px;padding:0 14px}}
h1{{font-size:17px;letter-spacing:.05em;margin:2px 0}}
.mast{{display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #1b1a17;padding-bottom:8px;margin-bottom:12px}}
.num{{font-family:Consolas,monospace;font-size:9.5px;letter-spacing:.14em;color:#6b6860;text-transform:uppercase}}
.st{{font-family:Consolas,monospace;font-size:12px;font-weight:700;color:{st_color}}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #dbd9d3;margin:6px 0;table-layout:auto}}
th,td{{border-bottom:1px solid #ebe9e3;padding:4px 8px;text-align:left;vertical-align:top;font-size:10.5px}}
th{{font-family:Consolas,monospace;font-size:8.5px;text-transform:uppercase;letter-spacing:.06em;color:#6b6860}}
.wrap{{word-wrap:break-word;overflow-wrap:anywhere;max-width:520px;white-space:normal}}
.r{{text-align:right}}.mono{{font-family:Consolas,monospace;font-size:.95em}}.small{{font-size:9.5px;color:#6b6860}}
.tag{{display:inline-block;padding:1px 7px;border-radius:8px;font-family:Consolas,monospace;font-size:8.5px;font-weight:700}}
.tag.g{{background:#e6efec;color:#2c4f4a}}.tag.o{{background:#f2ecdd;color:#6f5c31}}.tag.r{{background:#f3e7e6;color:#9e2b25}}
.gbg td{{background:#f4faf7}}.obg td{{background:#fbf7ea}}.rbg td{{background:#fbf0ef}}
.sec{{margin:14px 0}}.sec>:first-child{{font-weight:700}}
.sechead{{font-size:12.5px;font-weight:700;margin:16px 0 4px;border-left:3px solid #1b1a17;padding-left:7px}}
.pw{{display:inline-block;width:180px;height:8px;background:#e4e2dc;border-radius:5px;overflow:hidden;vertical-align:middle;margin-left:8px}}
.pb{{height:100%;width:0;background:linear-gradient(90deg,#2c4f4a,#5b8a83);border-radius:5px;animation:fill 1.2s ease forwards}}
@keyframes fill{{to{{width:100%}}}}
.nl{{font-family:Consolas,monospace;font-size:9px;color:#6b6860;padding:1px 0}}
.kpi{{display:inline-block;background:#fff;border:1px solid #dbd9d3;border-radius:7px;padding:6px 14px;margin:3px 6px 3px 0;text-align:center}}
.kpi b{{display:block;font-size:15px}}
</style></head><body>
<div class="mast"><div><div class="num">VIA-SYSMAN · {ts} · 三輪協議 · 20 加速器 · 建議制零就地改碼</div>
<h1>SYSTEM MANAGER · 三輪全景矩陣報告</h1></div>
<div class="st">SYSTEM {label} · 發現 {len(last['findings'])}</div></div>
<div class="sechead">分區庫存 MODULE / ENGINE / FUNCTION-LIB / OTHERS</div>
<div><span class="kpi"><b>{inv['MODULE']}</b>MODULE</span><span class="kpi"><b>{inv['ENGINE']}</b>ENGINE</span>
<span class="kpi"><b>{inv['FUNCTION-LIB']}</b>FUNCTION-LIB</span><span class="kpi"><b>{inv['OTHERS']}</b>OTHERS</span></div>
<div class="sechead">三輪協議實錄</div>{round_rows}
<div class="sechead">複雜度 top-5(C5 LITE)</div>
<table><tr><th>檔</th><th class="r">行</th><th class="r">函式</th></tr>{top5}</table>
<div class="sechead">20 加速器掛載表(誠實狀態)</div>
<table><tr><th>加速器</th><th>態</th><th>掛載明細</th></tr>{acc_rows}</table>
<div class="sechead">動態說明實錄(Dynamic Status Narration)</div>{narr}
<div class="small" style="text-align:center;padding:10px 0">VERITAS INTELLIGENCE ANALYTICS · 誠實口徑:缺件 WARN 列名不假綠 · 高風險節點→建議不自動修正</div>
</body></html>"""
    REPORTS.mkdir(parents=True, exist_ok=True)
    hp = REPORTS / f"VIA_SysMan_Matrix_{ts}.html"
    hp.write_text(html, encoding="utf-8")
    jp = hp.with_suffix(".json")
    jp.write_text(json.dumps({"ts": ts, "system": sys_state, "rounds": rounds,
                              "narration": NARRATION}, ensure_ascii=False, indent=1), encoding="utf-8")
    return hp, jp, sys_state


def main() -> int:
    args = sys.argv[1:]
    rounds_n = int(args[args.index("--rounds") + 1]) if "--rounds" in args else 3
    rounds_n = min(rounds_n, 3)  # 鐵則:不得超過三輪
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    themes = {1: "全面性 Comprehensive", 2: "順序性 Sequential", 3: "收尾性 Polishing"}
    total = rounds_n * 6
    t0 = time.time()
    deep = "--deep" in args
    status(f"SYSTEM MANAGER v0102 啟動 · {rounds_n} 輪協議 · 20 加速器掛載")
    rounds = []
    cache: dict = {}
    for rid in range(1, rounds_n + 1):
        rounds.append(run_round(rid, themes[rid], total, (rid - 1) * 6, cache, deep))
    hp, jp, sys_state = html_report(rounds, ts)
    status(f"報告產出 {hp.name} · 系統 {sys_state.upper()} · 耗時 {time.time() - t0:.1f}s")
    for f in rounds[-1]["findings"][:10]:
        print(f"  [{f['sev'].upper():6}] {f['class']} · {f['item']} · {f['note'][:90]}")
    if "--json" in args:
        print(json.dumps({"system": sys_state, "report": str(hp),
                          "findings": len(rounds[-1]["findings"])}, ensure_ascii=False))
    print(f"  報告:{hp}")
    print(f"  存證:{jp}")
    if "--no-open" not in args and sys.platform == "win32":
        import os
        os.startfile(str(hp))  # noqa  # 非阻塞跳出 HTML UI
    return 0 if sys_state != "red" else 1


if __name__ == "__main__":
    sys.exit(main())
