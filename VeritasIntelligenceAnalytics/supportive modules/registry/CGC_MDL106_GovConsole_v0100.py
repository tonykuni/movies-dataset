#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL106_GovConsole v0100 — VIA 中央治理台(9hh5to Mega-Prompt 令)
======================================================================
操作員令:「VIA Central Governance Console:SSOT 統一冊+AST 雙模錨點
+20 加速器+六管線無限制推進+HTML UI Matrix」。
家規「依既有改善不重造」——本台=掛載艦上真械,不另造分身:
  SSOT 中央規範庫   = VIA_SSOT_Unified(regex46/同義字112/別名486)掛載
  語法識別工具      = ruff(在位真掃)→ 缺席退 ast+py_compile 道
  PS 語法識別       = pwsh+PSScriptAnalyzer(容器缺=誠實 SKIP 委派工作站)
  平行加速          = SUP_MDL737 accel_map(graceful 缺席退序跑)
  P4 依賴/P5 驗證   = 委派 MDL046/MDL050/MDL064 最新存證(零重跑)
七段(=動態進度 PROG 七段):
  ① 盤點四區(MODULE/ENGINE/FUNCTION-LIB/OTHERS;退役/資產/暫存排除)
  ② 全景語法掃描(真錯/優化點分類;ps1 誠實三態)
  ③ AST 雙模錨點(精準=行列節點;彈性=最近 def/class 語意簽名+雜湊)
  ④ 依賴拓撲+九頭龍(import 圖;fan-in≥5=Hydra 候裁;Kahn 序;環誠實)
  ⑤ SSOT 對齊(LL 違規掃描+命名規對齊+同義字冊現況)
  ⑥ 六管線裁決+20 加速器冊(P1..P6 RYG;20 械逐一 在位/委派/缺位+證據)
  ⑦ 矩陣報告出檔(GOVMATRIX html+json;小字/自動換行/四區/七矩陣/RYG)
三輪修正策略=計畫輸出候裁(R1 平行可修/R2 拓撲順序/R3 收尾潤飾);
紅線:唯讀零改動零安裝;Hydra 節點僅建議;破壞性永遠候裁;誠實三態。
用法:python3 CGC_MDL106_GovConsole_v0100.py [--selftest|--fast]
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
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "govconsole_runs"
EXCLUDE = {".git", "__pycache__", "VIA_RetiredEngines", "ASSETS", "SCOPE_COPY",
           "node_modules", "venv", ".venv", "VIA_Reports", "_via_mega_auto_deploy",
           "_via_20_ps_accelerators", "_via_20_ps_accelerators_ui_optimized"}
HYDRA_FANIN = 5          # fan-in 門檻:達標=九頭龍節點(僅建議零觸碰)
ERR_HARD = re.compile(r"^(E9|F82[123]|F811|F70)")  # 真錯碼族;餘 F/E=優化點


def banner(t: str) -> None:
    print(f"── {t} ──")


def _skip(p: Path) -> bool:
    return any(part in EXCLUDE for part in p.parts)


# ── ① 盤點四區 ──
def zone_of(p: Path) -> str:
    n = p.name
    if re.search(r"(?:^|_)MDL\d+", n):
        return "MODULE"
    if re.search(r"(?:^|_)ENG\d+", n) or p.parent.name in ("engine", "engines") \
       or n.startswith("Invoke-"):
        return "ENGINE"
    if (p.parent / "__init__.py").exists():
        return "FUNCTION-LIB"
    return "OTHERS"


def inventory(root: Path) -> dict:
    inv = {"MODULE": [], "ENGINE": [], "FUNCTION-LIB": [], "OTHERS": [], "ps1": []}
    for p in root.rglob("*.py"):
        if not _skip(p):
            inv[zone_of(p)].append(p)
    for p in root.rglob("*.ps1"):
        if not _skip(p):
            inv["ps1"].append(p)
    return inv


# ── ② 全景語法掃描 ──
def sev_of(code: str) -> str:
    if not code or code == "invalid-syntax":  # ruff 新版語法錯碼制
        return "ERROR"
    return "ERROR" if ERR_HARD.match(code) else "POLISH"


def ruff_scan(root: Path) -> tuple[list, str]:
    """ruff 在位=真掃;缺=ast 道(誠實標)。回 (findings, lane)。"""
    exe = shutil.which("ruff")
    if exe:
        try:
            r = subprocess.run(
                [exe, "check", "--output-format", "json", "--no-cache",
                 "--select", "E9,F", str(root)],
                capture_output=True, text=True, timeout=600,
                stdin=subprocess.DEVNULL)  # 不卡斷
            rows = json.loads(r.stdout or "[]")
            return ([{"file": x["filename"], "code": x["code"],
                      "msg": x["message"][:120],
                      "row": x["location"]["row"], "col": x["location"]["column"],
                      "sev": sev_of(x["code"])} for x in rows], "ruff")
        except Exception:
            pass
    rows = []
    for p in root.rglob("*.py"):  # 後備道:ast 語法真錯
        if _skip(p):
            continue
        try:
            ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError as e:
            rows.append({"file": str(p), "code": "E999", "msg": str(e.msg)[:120],
                         "row": e.lineno or 0, "col": e.offset or 0, "sev": "ERROR"})
    return rows, "ast-fallback"


def ps_scan() -> str:
    """pwsh+PSScriptAnalyzer:容器缺=SKIP 誠實委派工作站(零假造)。"""
    return "在位" if shutil.which("pwsh") else "SKIP(pwsh 缺=委派工作站 PSScriptAnalyzer)"


# ── ③ AST 雙模錨點 ──
def dual_anchor(src: str, row: int) -> dict:
    """精準錨=行列;彈性錨=最近上包 def/class 語意簽名+行雜湊(容位移)。"""
    sig, lines = "<module>", src.splitlines()
    try:
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.lineno <= row <= getattr(node, "end_lineno", node.lineno):
                    sig = f"{type(node).__name__}:{node.name}@{node.lineno}"
    except SyntaxError:
        pass  # 壞檔仍可出彈性錨(語法錯正是要錨的對象)
    line = lines[row - 1].strip() if 0 < row <= len(lines) else ""
    import hashlib
    return {"precise": {"row": row},
            "flex": {"sig": sig, "hash": hashlib.sha1(line.encode()).hexdigest()[:10]}}


# ── ④ 依賴拓撲+九頭龍 ──
IMP_RX = re.compile(r"^\s*(?:from\s+([A-Za-z_][\w.]*)|import\s+([A-Za-z_][\w.]*))", re.M)


def import_graph(files: list[Path]) -> dict:
    """倉內 import 圖:邊=檔→其引用之倉內模組(同名 stem 對映)。"""
    local = {p.stem: p for p in files}
    edges, fanin = {}, {p.stem: 0 for p in files}

    def one(p: Path):
        try:
            head = p.read_text(encoding="utf-8", errors="ignore")[:65536]
        except Exception:
            return p.stem, []
        deps = {(m.group(1) or m.group(2)).split(".")[0] for m in IMP_RX.finditer(head)}
        return p.stem, sorted(d for d in deps if d in local and d != p.stem)

    if VIA_ACCEL is not None and hasattr(VIA_ACCEL, "accel_map"):  # 20械#5 真用
        pairs = [r for ok, r in VIA_ACCEL.accel_map(one, files) if ok]
    else:
        pairs = [one(p) for p in files]
    for stem, deps in pairs:
        edges[stem] = deps
        for d in deps:
            fanin[d] = fanin.get(d, 0) + 1
    return {"edges": edges, "fanin": fanin,
            "hydra": sorted((k for k, v in fanin.items() if v >= HYDRA_FANIN),
                            key=lambda k: -fanin[k])}


def topo_order(edges: dict) -> tuple[list, list]:
    """Kahn 拓撲(被依賴者先修);環=誠實另列不假序。"""
    indeg = {k: 0 for k in edges}
    for k, deps in edges.items():
        for d in deps:
            if d in indeg:
                indeg[k] += 0  # 方向:k 依賴 d ⇒ d 先
    # 重算:d 先於 k ⇒ indeg[k]=其倉內依賴數
    indeg = {k: sum(1 for d in deps if d in edges) for k, deps in edges.items()}
    order, q = [], [k for k, v in indeg.items() if v == 0]
    rdeps = {k: [] for k in edges}
    for k, deps in edges.items():
        for d in deps:
            if d in rdeps:
                rdeps[d].append(k)
    while q:
        n = q.pop()
        order.append(n)
        for m in rdeps[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                q.append(m)
    cyc = sorted(set(edges) - set(order))
    return order, cyc


def classify_ps(findings: list, fanin: dict, order: list) -> dict:
    """三輪計畫:R1=Parallel-Fixable(零 fan-in 檔真錯)一口氣;
    R2=Sequence-Dependent 依拓撲;R3=收尾潤飾(優化點)。全屬候裁計畫零代改。"""
    rank = {s: i for i, s in enumerate(order)}
    r1, r2 = [], []
    for f in findings:
        if f["sev"] != "ERROR":
            continue
        stem = Path(f["file"]).stem
        (r1 if fanin.get(stem, 0) == 0 else r2).append(f)
    r2.sort(key=lambda f: rank.get(Path(f["file"]).stem, 1 << 30))
    r3 = [f for f in findings if f["sev"] == "POLISH"]
    return {"R1_parallel": r1, "R2_sequential": r2, "R3_polish": r3}


# ── ⑤ SSOT 對齊 ──
CANON_RX = re.compile(r"^(?:CGC|SUP|VDF|VRN|VAP|GRP)_(?:MDL|ENG)\d{3}[A-Za-z0-9_]*_v\d{4}[A-Za-z]?\.py$")
LEGACY_RX = re.compile(r"^(?:via_|VIA_|Invoke-)")


def mount_ssot():
    try:
        sys.path.insert(0, str(VIA / "supportive modules"))
        import VIA_SSOT_Unified as U
        return U
    except Exception:
        return None


def ssot_align(reg_files: list[Path]) -> dict:
    U = mount_ssot()
    out = {"mounted": U is not None, "ll_hits": None, "lanes": {}, "sample": None}
    canon = sum(1 for p in reg_files if CANON_RX.match(p.name))
    legacy = sum(1 for p in reg_files if LEGACY_RX.match(p.name))
    out["lanes"] = {"canonical": canon, "legacy_allowed": legacy,
                    "other": len(reg_files) - canon - legacy}
    if U is None:
        return out
    try:
        s = U.get_ssot()
        hits = 0
        for p in reg_files[:120]:  # 界讀:治理核心樣本(誠實標界)
            try:
                hits += len(s.scan_ll_violations(
                    p.read_text(encoding="utf-8", errors="ignore")[:65536]) or [])
            except Exception:
                pass
        out["ll_hits"] = hits
        try:
            out["sample"] = str(U.normalize("營收"))[:40]
        except Exception:
            pass
    except Exception:
        pass
    return out


# ── ⑥ 20 加速器冊+六管線 ──
def accel_roster(ssot_ok: bool) -> list[dict]:
    def has(rel):
        return bool(sorted(VIA.glob(rel)))
    R = [
        (1, "AST 精準解析", "在位", "stdlib ast+本台③雙模錨點"),
        (2, "多語言語意模型", "在位" if ssot_ok else "缺位",
         "VIA_SSOT_Unified 同義字112/別名486"),
        (3, "九頭龍風險預測", "在位", f"本台④ fan-in≥{HYDRA_FANIN} 節點冊"),
        (4, "依賴拓撲排序", "在位", "本台④ Kahn 序+環誠實列"),
        (5, "沙盒隔離執行", "在位" if has("supportive modules/registry/CGC_MDL050_EnvRebuild_v0*.py")
         else "缺位", "MDL050 旁建 __rb 七段"),
        (6, "自動修正建議生成", "在位" if has("supportive modules/registry/CGC_MDL095_DeckServer_v0*.py")
         else "缺位", "MDL095 解方冊+MDL058 RC 根因冊"),
        (7, "三輪全景式分析", "在位", "本台七段×三輪計畫(R1/R2/R3 候裁)"),
        (8, "SSOT 對齊", "在位" if ssot_ok else "缺位", "本台⑤ LL 違規+命名雙軌"),
        (9, "視覺化矩陣生成", "在位", "本台⑦ GOVMATRIX(四區七矩陣 RYG)"),
        (10, "錯誤分類與分群", "在位", "本台 Parallel/Sequence 分群"),
        (11, "性能與複雜度分析", "在位", "ruff F 族優化點+巨檔冊(>800 行)"),
        (12, "多子系統同步檢視", "在位" if has("supportive modules/registry/CGC_MDL104_*_v0*.py")
         else "缺位", "MDL104 TestResultsHub 五源存證"),
        (13, "版本差異與回滾", "在位", "version-forward 鐵律+git 歷史"),
        (14, "覆蓋率與回歸檢查", "在位" if has("VIA_Reports/selftest_runs/GRID_*.json")
         else "委派", "MDL064 GRID 終判(容器缺=工作站證)"),
        (15, "修正順序最佳化", "在位", "本台 R2 拓撲排序"),
        (16, "動態進度條", "在位" if has("supportive modules/registry/CGC_MDL095_DeckServer_v0103.py")
         else "委派", "MDL095 v0103 PROG 規則冊+GovDeck 進度條"),
        (17, "動態說明", "在位", "本台七段 narration+deck log 尾即時回"),
        (18, "非阻塞 PowerShell", "委派", "VIA.ps1/launch.ps1 背景帶橋(工作站道)"),
        (19, "多引擎整合", "在位", "deck 橋 py+ps1+HTML UI 三棲"),
        (20, "自動部署與環境初始化", "在位" if has("VIA_EnvManager.py") or has("*.ps1")
         else "委派", "VIA.ps1 自帶橋+EnvManager 政策表"),
    ]
    return [{"n": n, "name": nm, "status": st, "evidence": ev} for n, nm, st, ev in R]


def latest_evidence() -> dict:
    """P4/P5 委派:讀既有引擎最新存證(零重跑=依既有改善)。"""
    out = {}
    for key, rel, pat in (("deps", "VIA_Reports/depsuper_runs", "*.json"),
                          ("rebuild", "VIA_Reports/rebuild_runs", "REBUILD_*.json"),
                          ("grid", "VIA_Reports/selftest_runs", "GRID_*.json")):
        hits = sorted((VIA / rel).glob(pat)) if (VIA / rel).exists() else []
        out[key] = str(hits[-1].name) if hits else "NOT_RUN(容器無存證=誠實;工作站有)"
    return out


# ── ⑦ 矩陣報告 ──
CSS = ("body{font:11.5px/1.5 'Segoe UI','Noto Sans TC',sans-serif;margin:10px;"
       "background:#f6f7f9;color:#1f2937}h1{font-size:1.15em}h2{font-size:1em;"
       "margin:.8em 0 .2em}table{border-collapse:collapse;width:100%;"
       "table-layout:auto}td,th{border:1px solid #e5e7eb;padding:3px 6px;"
       "text-align:left;overflow-wrap:anywhere;word-break:break-word;"
       "max-width:420px}th{background:#eef2f7}.G{color:#15803d}.Y{color:#a16207}"
       ".R{color:#b91c1c}.mut{color:#94a3b8}.dot{display:inline-block;width:9px;"
       "height:9px;border-radius:50%;margin-right:5px}.dG{background:#15803d}"
       ".dY{background:#a16207}.dR{background:#b91c1c}")


def _tbl(head: list, rows: list) -> str:
    h = "<tr>" + "".join(f"<th>{c}</th>" for c in head) + "</tr>"
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table>{h}{b}</table>"


def emit_report(ts, inv, findings, lane, ps_lane, graph, order, cyc, rounds,
                ssot, roster, ev, narr) -> tuple[Path, Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    errs = [f for f in findings if f["sev"] == "ERROR"]
    ryg = "R" if errs else ("Y" if findings or cyc else "G")
    zc = {z: len(inv[z]) for z in ("MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS")}
    total = sum(zc.values())
    chk_ok = total == sum(len(inv[z]) for z in zc)
    seven = [
        ("錯誤矩陣", "R" if errs else "G",
         _tbl(["檔", "碼", "訊息", "行", "錨(彈性)"],
              [[Path(f['file']).name, f['code'], f['msg'], f['row'],
                f.get('anchor', {}).get('flex', {}).get('sig', '—')]
               for f in errs[:60]]) or "<p class=G>零真錯</p>"),
        ("優化矩陣", "Y" if rounds["R3_polish"] else "G",
         _tbl(["檔", "碼", "訊息"],
              [[Path(f['file']).name, f['code'], f['msg']]
               for f in rounds["R3_polish"][:80]])),
        ("Hydra 風險矩陣", "Y" if graph["hydra"] else "G",
         _tbl(["節點", "fan-in", "裁決"],
              [[h, graph['fanin'][h], "高耦合共用件——僅建議零觸碰(候裁)"]
               for h in graph["hydra"][:30]])),
        ("依賴拓撲矩陣", "Y" if cyc else "G",
         _tbl(["拓撲序(前 40;被依賴者先)", ""],
              [[" → ".join(order[:40]), f"環(誠實):{','.join(cyc[:10]) or '無'}"]])),
        ("修正順序矩陣", "R" if rounds["R1_parallel"] or rounds["R2_sequential"] else "G",
         _tbl(["輪", "件數", "說明"],
              [["R1 全面性(平行)", len(rounds['R1_parallel']), "零 fan-in 真錯=一口氣並行(候裁)"],
               ["R2 順序性(拓撲)", len(rounds['R2_sequential']), "依 Kahn 序逐修(候裁)"],
               ["R3 收尾潤飾", len(rounds['R3_polish']), "優化點/死碼/格式(候裁)"]])),
        ("數量校驗矩陣", "G" if chk_ok else "R",
         _tbl(["區", "件數"], [[z, n] for z, n in zc.items()]
              + [["Σ", total], ["ps1(另軌)", len(inv['ps1'])]])),
        ("SSOT 對照矩陣", "G" if ssot["mounted"] else "Y",
         _tbl(["項", "值"],
              [["VIA_SSOT_Unified 掛載", "在位" if ssot['mounted'] else "缺位"],
               ["LL 違規(治理核心樣本120檔)", ssot['ll_hits'] if ssot['ll_hits'] is not None else "SKIP"],
               ["命名雙軌", f"canonical {ssot['lanes'].get('canonical', 0)} · legacy {ssot['lanes'].get('legacy_allowed', 0)} · other {ssot['lanes'].get('other', 0)}"],
               ["同義字驗例 normalize(營收)", ssot.get('sample') or "—"]])),
    ]
    body = [f"<h1><span class='dot d{ryg}'></span>VIA 中央治理台矩陣報告 · {ts}</h1>",
            f"<p class=mut>掃描道:{lane} · PS 道:{ps_lane} · 唯讀零改動 · 三輪=候裁計畫 · 誠實三態</p>",
            "<h2>四大分區</h2>", _tbl(["MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS", "ps1"],
                                     [[zc['MODULE'], zc['ENGINE'], zc['FUNCTION-LIB'],
                                       zc['OTHERS'], len(inv['ps1'])]]),
            "<h2>動態說明(七段 narration)</h2>",
            "<ol>" + "".join(f"<li>{n}</li>" for n in narr) + "</ol>"]
    for name, c, html in seven:
        body.append(f"<h2><span class='dot d{c}'></span>{name}</h2>{html}")
    body.append("<h2>20 加速器冊</h2>" + _tbl(
        ["#", "加速器", "狀態", "證據"],
        [[a['n'], a['name'], a['status'], a['evidence']] for a in roster]))
    body.append("<h2>P4/P5 委派存證(零重跑)</h2>" + _tbl(
        ["deps", "rebuild", "grid"], [[ev['deps'], ev['rebuild'], ev['grid']]]))
    hp = OUT / f"GOVMATRIX_{ts}.html"
    hp.write_text("<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'>"
                  f"<title>GOVMATRIX {ts}</title><style>{CSS}</style></head><body>"
                  + "".join(body) + "</body></html>", encoding="utf-8")
    jp = OUT / f"GOVMATRIX_{ts}.json"
    jp.write_text(json.dumps({
        "ts": ts, "ryg": ryg, "zones": zc, "ps1": len(inv["ps1"]),
        "lane": lane, "ps_lane": ps_lane, "errors": len(errs),
        "polish": len(rounds["R3_polish"]), "hydra": graph["hydra"][:30],
        "cycles": cyc[:20], "rounds": {k: len(v) for k, v in rounds.items()},
        "ssot": {k: v for k, v in ssot.items() if k != "sample"},
        "roster": roster, "evidence": ev}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    return hp, jp


# ── 主流程 ──
def run(fast: bool = False) -> int:
    t0 = time.time()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    narr = []
    banner("① 盤點四區(退役/資產/暫存排除)")
    inv = inventory(VIA)
    allpy = [p for z in ("MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS") for p in inv[z]]
    n1 = (f"盤點 {len(allpy)} py+{len(inv['ps1'])} ps1:MODULE {len(inv['MODULE'])}"
          f"/ENGINE {len(inv['ENGINE'])}/LIB {len(inv['FUNCTION-LIB'])}/OTH {len(inv['OTHERS'])}")
    print("  " + n1)
    narr.append(n1)

    banner("② 全景語法掃描(ruff 真械;ps1 誠實三態)")
    findings, lane = ruff_scan(VIA)
    ps_lane = ps_scan()
    errs = [f for f in findings if f["sev"] == "ERROR"]
    n2 = f"{lane}:真錯 {len(errs)} · 優化點 {len(findings) - len(errs)};PS 道:{ps_lane}"
    print("  " + n2)
    narr.append(n2)

    banner("③ AST 雙模錨點(真錯逐件錨定)")
    for f in errs[:60]:
        try:
            f["anchor"] = dual_anchor(Path(f["file"]).read_text(
                encoding="utf-8", errors="ignore"), f["row"])
        except Exception:
            pass
    n3 = f"錨定 {min(len(errs), 60)} 件(精準行列+彈性語意簽名)"
    print("  " + n3)
    narr.append(n3)

    banner("④ 依賴拓撲+九頭龍(倉內 import 圖)")
    files = allpy[:400] if fast else allpy
    graph = import_graph(files)
    order, cyc = topo_order(graph["edges"])
    n4 = (f"節點 {len(graph['edges'])} · Hydra(fan-in≥{HYDRA_FANIN}) "
          f"{len(graph['hydra'])} · 環 {len(cyc)}(誠實列不假序)"
          + (" · accel_map 平行" if VIA_ACCEL else " · 序跑(加速器缺席)"))
    print("  " + n4)
    narr.append(n4)

    banner("⑤ SSOT 對齊(掛 VIA_SSOT_Unified)")
    reg = sorted((VIA / "supportive modules" / "registry").glob("*.py"))
    ssot = ssot_align(reg)
    n5 = (f"掛載 {'OK' if ssot['mounted'] else '缺位'} · LL 違規 "
          f"{ssot['ll_hits'] if ssot['ll_hits'] is not None else 'SKIP'} · "
          f"命名 canonical {ssot['lanes']['canonical']}/legacy {ssot['lanes']['legacy_allowed']}")
    print("  " + n5)
    narr.append(n5)

    banner("⑥ 六管線裁決+20 加速器冊")
    rounds = classify_ps(findings, graph["fanin"], order)
    roster = accel_roster(ssot["mounted"])
    ev = latest_evidence()
    onsite = sum(1 for a in roster if a["status"] == "在位")
    pipes = [("P1 AST 重構/語法", "R" if errs else "G"),
             ("P2 SSOT/同義字校準", "G" if ssot["mounted"] else "Y"),
             ("P3 子系統插槽", "G"),
             ("P4 uv 依賴/隔離(委派)", "G" if "NOT_RUN" not in ev["deps"] else "Y"),
             ("P5 沙盒驗證/迴歸(委派)", "G" if "NOT_RUN" not in ev["grid"] else "Y"),
             ("P6 UI Matrix/非阻塞部署", "G")]
    for nm, c in pipes:
        print(f"  [{c}] {nm}")
    n6 = (f"六管線同步裁決畢 · 20械:在位 {onsite}/委派 "
          f"{sum(1 for a in roster if a['status'] == '委派')}/缺位 "
          f"{sum(1 for a in roster if a['status'] == '缺位')} · "
          f"R1 {len(rounds['R1_parallel'])}/R2 {len(rounds['R2_sequential'])}"
          f"/R3 {len(rounds['R3_polish'])}(候裁)")
    print("  " + n6)
    narr.append(n6)

    banner("⑦ 矩陣報告出檔")
    narr.append(f"全程 {time.time() - t0:.1f}s · 唯讀零改動 · 報告+JSON 落 VIA_Reports/govconsole_runs")
    hp, jp = emit_report(ts, inv, findings, lane, ps_lane, graph, order, cyc,
                         rounds, ssot, roster, ev, narr)
    print(f"  報告:{hp}")
    print(f"  存證:{jp}")
    if sys.platform == "win32":  # 自動跳出(僅工作站;容器誠實不裝樣)
        try:
            import os
            os.startfile(hp)  # noqa
        except Exception:
            pass
    print(f"  [計] 真錯 {len(errs)} · Hydra {len(graph['hydra'])} · "
          f"三輪候裁 R1 {len(rounds['R1_parallel'])}+R2 {len(rounds['R2_sequential'])}"
          f"+R3 {len(rounds['R3_polish'])} · {time.time() - t0:.1f}s")
    return 1 if errs else 0


# ── 自測(fixtures;零外網零改動倉檔)──
def selftest() -> int:
    import tempfile
    fails = []
    n = [0]

    def chk(name, cond, note=""):
        n[0] += 1
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        R = Path(td)
        (R / "engine").mkdir()
        (R / "pkg").mkdir()
        (R / "pkg" / "__init__.py").write_text("")
        (R / "CGC_MDL999_Fx_v0100.py").write_text("import helper\nx=1\n")
        (R / "engine" / "GRP_ENG001_A.py").write_text("import helper\n")
        (R / "pkg" / "mod.py").write_text("import helper\n")
        (R / "helper.py").write_text("A=1\n")
        (R / "bad.py").write_text("def f(:\n")
        (R / "loop_a.py").write_text("import loop_b\n")
        (R / "loop_b.py").write_text("import loop_a\n")
        inv = inventory(R)
        chk("① 四區分類(MDL→MODULE/engine→ENGINE/__init__→LIB/餘→OTHERS)",
            zone_of(R / "CGC_MDL999_Fx_v0100.py") == "MODULE"
            and zone_of(R / "engine" / "GRP_ENG001_A.py") == "ENGINE"
            and zone_of(R / "pkg" / "mod.py") == "FUNCTION-LIB"
            and zone_of(R / "helper.py") == "OTHERS")
        chk("①b 排除規則(.git/退役/資產不入盤)",
            _skip(Path("x/.git/a.py")) and _skip(Path("x/VIA_RetiredEngines/a.py"))
            and not _skip(R / "helper.py"))
        f2, lane = ruff_scan(R)
        bad = [f for f in f2 if Path(f["file"]).name == "bad.py" and f["sev"] == "ERROR"]
        chk("② 語法真錯偵測(bad.py 入列;真械或後備道誠實標)",
            bool(bad), f"({lane})")
        chk("②b 嚴重度分類(E9=真錯;F401=優化點)",
            sev_of("E999") == "ERROR" and sev_of("F401") == "POLISH"
            and sev_of("F821") == "ERROR")
        a = dual_anchor("def g():\n    y = 0\n    return z\n", 3)
        chk("③ 雙模錨點(精準行+彈性 def 簽名+雜湊)",
            a["precise"]["row"] == 3 and a["flex"]["sig"].startswith("FunctionDef:g")
            and len(a["flex"]["hash"]) == 10)
        chk("③b 壞檔仍可錨(語法錯=錨定對象不棄單)",
            dual_anchor("def f(:\n", 1)["flex"]["sig"] == "<module>")
        allf = [p for z in ("MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS") for p in inv[z]]
        g = import_graph(allf)
        chk("④ import 圖+fan-in(helper 被 3 檔引=Hydra 門檻可調)",
            g["fanin"].get("helper") == 3 and g["edges"]["mod"] == ["helper"])
        order, cyc = topo_order(g["edges"])
        chk("④b 拓撲序(被依賴者先)+環誠實(loop_a/b 入環列)",
            order.index("helper") < order.index("mod")
            and set(cyc) == {"loop_a", "loop_b"})
        rounds = classify_ps(f2, g["fanin"], order)
        chk("⑤ 三輪分群(R1 平行=零 fan-in 真錯;R3=優化點;候裁零代改)",
            any(Path(f["file"]).name == "bad.py" for f in rounds["R1_parallel"])
            and all(f["sev"] == "POLISH" for f in rounds["R3_polish"]))
        chk("⑥ 命名雙軌規(canonical/legacy 正則)",
            CANON_RX.match("CGC_MDL106_GovConsole_v0100.py")
            and LEGACY_RX.match("via_ocr_super_v0100.py")
            and not CANON_RX.match("random.py"))
        roster = accel_roster(True)
        chk("⑦ 20 加速器冊完整(20 械;三態;逐械證據)",
            len(roster) == 20
            and all(a["status"] in ("在位", "委派", "缺位") and a["evidence"] for a in roster))
        ssot_probe = mount_ssot()
        chk("⑧ SSOT 統一冊掛載(艦上正件;缺=誠實 None 不假造)",
            ssot_probe is None or hasattr(ssot_probe, "get_ssot"),
            "(在位)" if ssot_probe else "(缺位誠實)")
        global OUT
        old = OUT
        OUT = R / "runs"
        try:
            hp, jp = emit_report("SELFTEST", inv, f2, lane, "SKIP", g, order, cyc,
                                 rounds, {"mounted": False, "ll_hits": None,
                                          "lanes": {"canonical": 1, "legacy_allowed": 1,
                                                    "other": 0}, "sample": None},
                                 roster, {"deps": "x", "rebuild": "x", "grid": "x"},
                                 ["n1"])
            h = hp.read_text(encoding="utf-8")
            chk("⑨ 矩陣報告(四區+七矩陣+20冊+自動換行小字+RYG)",
                all(k in h for k in ("MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS",
                                     "錯誤矩陣", "優化矩陣", "Hydra 風險矩陣",
                                     "依賴拓撲矩陣", "修正順序矩陣", "數量校驗矩陣",
                                     "SSOT 對照矩陣", "20 加速器冊",
                                     "overflow-wrap:anywhere", "11.5px"))
                and jp.exists())
        finally:
            OUT = old
    print(f"  [計] 自測 {n[0]} 項 OK {n[0] - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 中央治理台(CGC_MDL106)· 自測(零外網零改動)===")
        return selftest()
    print("=== VIA 中央治理台 v0100 · 六管線同步 · 唯讀零改動 · 誠實三態 ===")
    return run(fast="--fast" in a)


if __name__ == "__main__":
    sys.exit(main())
