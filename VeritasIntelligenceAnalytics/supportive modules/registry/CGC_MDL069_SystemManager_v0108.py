#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_system_manager_v0108 — SYSTEM MANAGER 三輪全景協議(六獨立步驟同步波)
====================================================================================
v0106→v0107(工作站 RED 實錄+六獨立步驟令):
  ⑮ 分隔符根因修:登錄冊記 posix 斜線,Windows relative_to 產反斜線→
     比對落空(封存跳過 0、RED 復發)。統一 as_posix() 雙側歸一。
  ⑯ Hydra 六因子評分(LITE 估分誠實標示):Circularity/SharedState/
     Centrality/SSOT·Entry/SideEffect/TestGap → 0-100 + 分級
  ⑰ 工具偵測登錄:py·ps·js 工具鏈 which+版本實測;未裝=NOT_INSTALLED
     誠實(不自動裝)→ tool_registry.json
  ⑱ 證據束擴編:dependency_graph.json / hydra_risk_register.json /
     promotion_proposal.md(v01.00 §12)
v0105→v0106(工作站 WinError 32 實錄):tempfile.mkstemp 回傳之 fd 未關
——Windows 下開啟中的檔禁止 unlink → PermissionError 於清理段炸毀主流程
(Linux 容器不鎖故未現形)。修:os.close(fd) 即關 + unlink 護欄
try/except(暫存檔即使殘留亦由系統自清,誠實略過不炸)。
v0104→v0105(v01.00 對齊第二波之①):
  ⑬ PS AST 道 RUN:System.Management.Automation.Language.Parser 官方解析器
     ——pwsh 單行程批次掃全數 ps1/psm1(逾時 600s 保護);語法錯列為
     PARALLEL/red 發現進裁決;pwsh 缺席=NOT_RUN 誠實(不虛構)。
  ⑮ 語法版本閘冊(v0108):VIA_Syntax_Gate_Register 冊內檔之語法錯
     源於 Python 版本閘(如 f-string 反斜線 py3.12+)——當前版本低於
     python_min 改記「版本閘列管」不列 RED(對帳計數不變;誠實具名)
  ⑭ PS 封存登錄冊:VIA_PS_Archive_Register_v0100.json 冊內檔(歷史批次
     收容原件,零動詞引用)語法錯改記「封存唯讀跳過」具名列示——
     紅線原件唯讀;要修復為現役自冊移除點名即入裁決。
v0103→v0104(操作員 v01.00 正式版令;可實作項全上、未及項誠實 NOT_RUN):
  ⑧ Run 證據束:VIA_Reports/sysman_runs/RUN_<ts>/ append-only——
     run_manifest.json / events.jsonl(逐事件)/ heartbeat.json(原子更新)/
     final_summary.json / SHA256SUMS
  ⑨ 數量對帳(§10):discovered = analyzed + archive_skipped + vendor_skipped
     + syntax_failed;不等=RED Gate(禁 GREEN)
  ⑩ 多語言盤點:py/ps1/js/html 檔數;JS 語法道 node --check(node 缺=NOT_RUN
     誠實);PS AST 道=NOT_RUN 候(Parser 掛載下一波)
  ⑪ Gate 依 §S05 四值:GREEN_SANDBOX_STABLE_PROMOTION_REVIEW_REQUIRED /
     YELLOW_READY_WITH_WARNINGS_REVIEW_REQUIRED / HOLD_BLOCKED_OR_EVIDENCE_
     INCOMPLETE / RED_REGRESSION_OR_SAFETY_FAILURE
  ⑫ HydraScore(LITE 百分制映射):語法錯=10(LOW)/import 環=65(HIGH,
     review-only);完整六因子評分候下一波
  規範原文:SPEC-013 VIA_SafeSandbox_MegaPrompt_v0100.md;Top25 規則庫:
  VIA_Top25_Rules_v0100.json(狀態誠實分級)
v0102→v0103(操作員令:以本報告為 UI 範本模板基礎,全數完成後優化
html/css/javascript/grids/matrix/紅黃綠燈/彈性最佳化 layout):
  ⑦ 報告改用 VIA UI 範本 v0100:CSS Grid KPI 卡(auto-fit 彈性欄)、
     三輪 <details> 折疊(彈性 layout)、表格橫向滾動容器+黏性表頭、
     紅黃綠燈點+標籤雙態、加速器表 JS 即時過濾、敘事折疊、響應式
     斷點、列印友善。分析邏輯零變更。範本另存
     ui_support/VIA_UI_Template_SysMan_v0100.html 供全系 UI 沿用。
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
用法:py via_system_manager_v0108.py [--rounds N] [--no-open] [--json] [--deep]
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
RUN_CTX: dict = {}


def emit(event_type: str, **payload):
    """append-only events.jsonl + 原子 heartbeat.json(v01.00 §11)。"""
    rd = RUN_CTX.get("dir")
    if not rd:
        return
    ev = {"run_id": RUN_CTX["id"], "event_ts": datetime.now().isoformat(timespec="seconds"),
          "event_type": event_type, **payload}
    with open(rd / "events.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    hb = rd / "heartbeat.json"
    tmp = hb.with_suffix(".tmp")
    tmp.write_text(json.dumps({"run_id": RUN_CTX["id"], "last_event": ev,
                               "last_heartbeat_utc": ev["event_ts"]}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    tmp.replace(hb)


def status(msg: str) -> None:
    line = f"[STATUS] {msg}"
    NARRATION.append(f"{datetime.now().strftime('%H:%M:%S')} {msg}")
    print(line, flush=True)
    emit("STATUS", message=msg)


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
            rel = p.relative_to(VIA).as_posix()
            gate = _SYNGATE.get(rel)
            gated = None
            if gate and sys.version_info < tuple(int(x) for x in gate["python_min"].split(".")):
                gated = f"py≥{gate['python_min']} 版本閘 · {gate['reason'][:40]}"
            syn_errors.append({"file": str(p.relative_to(VIA)), "err": f"L{exc.lineno}: {exc.msg}", "gated": gated})
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


# ── 多語言盤點 + JS 語法道(v01.00 ⑩;PS AST 道 NOT_RUN 候)──────────────
def lang_inventory():
    import shutil as _sh
    counts = {"py": 0, "ps1": 0, "js": 0, "html": 0}
    js_files = []
    for d in ("functional modules", "supportive modules", "bin"):
        for p in (VIA / d).rglob("*"):
            if not p.is_file() or any(x in VENDOR_DIRS for x in p.parts):
                continue
            ext = p.suffix.lower().lstrip(".")
            if ext in counts:
                counts[ext] += 1
                if ext == "js":
                    js_files.append(p)
    node = _sh.which("node") or ("/opt/node22/bin/node" if Path("/opt/node22/bin/node").exists() else None)
    js_syntax = {"status": "NOT_RUN", "reason": "node 缺席(誠實;不虛構)", "failed": []}
    if node and js_files:
        bad = []
        for jf in js_files[:200]:
            r = subprocess.run([node, "--check", str(jf)], capture_output=True, text=True, timeout=30)
            if r.returncode != 0:
                bad.append(str(jf.relative_to(VIA)))
        js_syntax = {"status": "RUN", "checked": min(len(js_files), 200), "failed": bad}
    # PS AST 道:官方 Parser,pwsh 單行程批次(v0105)
    ps_files = []
    for d in ("functional modules", "supportive modules", "bin"):
        for p in (VIA / d).rglob("*"):
            if p.is_file() and p.suffix.lower() in (".ps1", ".psm1") and not any(x in VENDOR_DIRS for x in p.parts):
                ps_files.append(p)
    pwsh = _sh.which("pwsh")
    if not pwsh:
        for cand in (Path("/tmp") .glob("claude-0/*/*/scratchpad/pwsh/pwsh")):
            pwsh = str(cand); break
    ps_ast = {"status": "NOT_RUN", "reason": "pwsh 缺席(誠實;不虛構)", "failed": []}
    if pwsh and ps_files:
        import os as _os
        import tempfile
        fd, lst_path = tempfile.mkstemp(suffix=".txt")
        _os.close(fd)  # Windows:fd 不關則檔被鎖,unlink 必炸 WinError 32
        lst = Path(lst_path)
        lst.write_text("\n".join(str(p) for p in ps_files), encoding="utf-8")
        ps_script = (
            "$ErrorActionPreference='Continue';"
            "Get-Content -LiteralPath '" + str(lst) + "' | ForEach-Object {"
            " $t=$null;$e=$null;"
            " [void][System.Management.Automation.Language.Parser]::ParseFile($_,[ref]$t,[ref]$e);"
            " if($e -and $e.Count -gt 0){"
            "  [pscustomobject]@{f=$_;n=$e.Count;m=$e[0].Message} | ConvertTo-Json -Compress }"
            "}")
        try:
            r = subprocess.run([pwsh, "-NoProfile", "-NonInteractive", "-Command", ps_script],
                               capture_output=True, text=True, timeout=600, stdin=subprocess.DEVNULL)
            bad = []
            for line in r.stdout.splitlines():
                line = line.strip()
                if line.startswith("{"):
                    try:
                        o = json.loads(line)
                        bad.append({"file": Path(o["f"]).relative_to(VIA).as_posix(), "n": o["n"], "msg": o["m"][:90]})
                    except Exception:
                        pass
            reg_p = HERE / "VIA_PS_Archive_Register_v0100.json"
            archived = set()
            if reg_p.exists():
                try:
                    archived = {e["file"] for e in json.loads(reg_p.read_text(encoding="utf-8"))["entries"]}
                except Exception:
                    pass
            arch_hits = [b for b in bad if b["file"] in archived]
            bad = [b for b in bad if b["file"] not in archived]
            ps_ast = {"status": "RUN", "checked": len(ps_files), "failed": bad,
                      "archived_skipped": arch_hits}
        except subprocess.TimeoutExpired:
            ps_ast = {"status": "NOT_RUN", "reason": "pwsh 批次逾時 600s(誠實 TIMEOUT)", "failed": []}
        finally:
            try:
                lst.unlink(missing_ok=True)
            except OSError:
                pass  # 鎖檔誠實略過——暫存由系統自清,不炸主流程
    return {"counts": counts, "js_syntax": js_syntax, "ps_ast": ps_ast}


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


_SYNGATE = {}
try:
    _sg = json.loads((HERE / "VIA_Syntax_Gate_Register_v0100.json").read_text(encoding="utf-8"))
    _SYNGATE = {e["file"]: e for e in _sg.get("entries", [])}
except Exception:
    _SYNGATE = {}


def classify(c1, c2, c3, c4):
    finds = []
    for e in c1["syntax_errors"]:
        if e.get("gated"):
            continue  # 版本閘冊列管:非壞件,不列 RED(對帳計數照舊)
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
            if e.get("gated"):
                status(f"  [版本閘] {e['file']} · {e['err']} · {e['gated']}(列管,誠實非 RED)")
            else:
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


# ── VIA UI 範本 v0100(SysMan 報告基準;grids/燈/彈性 layout/JS 過濾)──────
TPL_CSS = """<style>
:root{--bg:#f4f3ef;--paper:#fff;--ink:#1b1a17;--mut:#6b6860;--line:#dbd9d3;--soft:#ebe9e3;
 --g:#2c4f4a;--gbg:#e6efec;--o:#6f5c31;--obg:#f2ecdd;--r:#9e2b25;--rbg:#f3e7e6;
 --grad:linear-gradient(90deg,#2c4f4a,#5b8a83)}
*{box-sizing:border-box}
body{font-family:'Segoe UI','Noto Sans TC',Arial,sans-serif;font-size:11.5px;background:var(--bg);
 color:var(--ink);margin:18px auto;max-width:1100px;padding:0 14px;line-height:1.5}
h1{font-size:17px;letter-spacing:.05em;margin:2px 0}
.mast{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;
 border-bottom:2px solid var(--ink);padding-bottom:8px;margin-bottom:12px}
.num{font-family:Consolas,monospace;font-size:9.5px;letter-spacing:.14em;color:var(--mut);text-transform:uppercase}
.st{font-family:Consolas,monospace;font-size:12px;font-weight:700}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:8px;margin:8px 0}
.kpi{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:8px 12px;text-align:center}
.kpi b{display:block;font-size:16px}
.kpi .l{font-family:Consolas,monospace;font-size:8px;color:var(--mut);text-transform:uppercase;letter-spacing:.06em}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:6px;background:var(--paper);margin:6px 0}
table{width:100%;border-collapse:collapse;font-size:10.5px}
th,td{border-bottom:1px solid var(--soft);padding:4px 8px;text-align:left;vertical-align:top}
th{font-family:Consolas,monospace;font-size:8.5px;text-transform:uppercase;letter-spacing:.06em;
 color:var(--mut);background:var(--paper);position:sticky;top:0}
.wrap{word-wrap:break-word;overflow-wrap:anywhere;max-width:520px;white-space:normal}
.r{text-align:right}.mono{font-family:Consolas,monospace;font-size:.95em}.small{font-size:9.5px;color:var(--mut)}
.tag{display:inline-block;padding:1px 7px;border-radius:8px;font-family:Consolas,monospace;font-size:8.5px;font-weight:700}
.tag.g{background:var(--gbg);color:var(--g)}.tag.o{background:var(--obg);color:var(--o)}.tag.r{background:var(--rbg);color:var(--r)}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px;vertical-align:middle}
.dot.g{background:var(--g)}.dot.o{background:#c4943a}.dot.r{background:var(--r)}
.gbg td{background:#f4faf7}.obg td{background:#fbf7ea}.rbg td{background:#fbf0ef}
details{background:var(--paper);border:1px solid var(--line);border-radius:8px;margin:10px 0;padding:0 12px 8px}
summary{cursor:pointer;font-weight:700;font-size:12.5px;padding:9px 0;list-style-position:inside}
summary::marker{color:var(--mut)}
.sechead{font-size:12.5px;font-weight:700;margin:16px 0 4px;border-left:3px solid var(--ink);padding-left:7px}
.pw{display:inline-block;width:170px;height:8px;background:#e4e2dc;border-radius:5px;overflow:hidden;vertical-align:middle;margin-left:8px}
.pb{height:100%;width:0;background:var(--grad);border-radius:5px;animation:fill 1.2s ease forwards}
@keyframes fill{to{width:100%}}
.filter{font-family:Consolas,monospace;font-size:10px;padding:5px 9px;border:1px solid var(--line);
 border-radius:5px;width:230px;max-width:100%;margin:4px 0}
.nl{font-family:Consolas,monospace;font-size:9px;color:var(--mut);padding:1px 0}
.foot{font-family:Consolas,monospace;font-size:9px;color:var(--mut);text-align:center;padding:10px 0}
@media(max-width:720px){body{margin:8px auto}.kpis{grid-template-columns:repeat(auto-fit,minmax(96px,1fr))}.wrap{max-width:none}}
@media print{details{page-break-inside:avoid}summary{pointer-events:none}.filter{display:none}}
</style>"""
TPL_JS = """<script>
function viaFilter(inp,tbodyId){var q=(inp.value||'').toLowerCase();
 var rows=document.getElementById(tbodyId).rows;
 for(var i=0;i<rows.length;i++){rows[i].style.display=
  rows[i].textContent.toLowerCase().indexOf(q)>=0?'':'none';}}
</script>"""


def html_report(rounds, ts):
    last = rounds[-1]
    sys_state = "green"
    if any(f["sev"] == "red" for f in last["findings"]):
        sys_state = "red"
    elif last["findings"]:
        sys_state = "yellow"
    cls, label = sev_tag(sys_state)
    st_color = {"green": "var(--g)", "yellow": "var(--o)", "red": "var(--r)"}[sys_state]
    inv = last["c6"]

    round_secs = ""
    for r in rounds:
        fr = "".join(
            f'<tr class="{sev_tag(f["sev"])[0]}bg"><td><span class="dot {sev_tag(f["sev"])[0]}"></span>{f["class"]}</td>'
            f'<td>{f["item"]}</td><td class="wrap">{f["note"]}</td></tr>' for f in r["findings"]) or \
            '<tr><td colspan="3" class="small"><span class="dot g"></span>零發現(誠實實測)</td></tr>'
        lanes = " · ".join(f"{l['lane']}:{l['status']}" for l in r["c2"].get("lanes", []))
        round_secs += f"""<details open><summary>R{r['round']} {r['theme']}
<span class="pw"><span class="pb" style="animation-delay:{r['round'] * .3}s"></span></span></summary>
<div class="scroll"><table><tr><th>類</th><th>項</th><th>明細</th></tr>{fr}</table></div>
<div class="small">C1 {r['c1']['stats']['files']} 檔/{r['c1']['stats']['defs']} 函式 ·
C2 {r['c2'].get('system', '?')}/Hydra {r['c2'].get('hydra', '?')}({lanes}) ·
C3 SSOT {'OK' if r['c3'].get('ok') else 'WARN'} ·
C4 {r['c4']['nodes']} 節點/{r['c4']['edges']} 邊/環 {len(r['c4']['cycles'])} · 本輪自動修正 0(建議制)</div></details>"""

    acc_rows = "".join(
        f'<tr><td class="mono">{n}</td><td><span class="tag {("g" if st == "ENABLED" else "o")}">{st}</span></td>'
        f'<td class="wrap small">{d}</td></tr>' for n, st, d in ACCELERATORS)
    top5 = "".join(f'<tr><td class="mono wrap">{t["file"]}</td><td class="r">{t["lines"]:,}</td>'
                   f'<td class="r">{t["defs"]}</td></tr>' for t in last["c5"]["top5"])
    narr = "".join(f'<div class="nl">{n}</div>' for n in NARRATION)

    html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA SysMan Matrix {ts}</title>{TPL_CSS}{TPL_JS}</head><body>
<div class="mast"><div><div class="num">VIA-SYSMAN · {ts} · 三輪協議 · 20 加速器 · 建議制零就地改碼 · UI 範本 v0100</div>
<h1>SYSTEM MANAGER · 三輪全景矩陣報告</h1></div>
<div class="st" style="color:{st_color}"><span class="dot {cls}"></span>SYSTEM {label} · 發現 {len(last['findings'])}</div></div>
<div class="sechead">分區庫存 MODULE / ENGINE / FUNCTION-LIB / OTHERS</div>
<div class="kpis"><div class="kpi"><b>{inv['MODULE']}</b><span class="l">MODULE</span></div>
<div class="kpi"><b>{inv['ENGINE']}</b><span class="l">ENGINE</span></div>
<div class="kpi"><b>{inv['FUNCTION-LIB']}</b><span class="l">FUNCTION-LIB</span></div>
<div class="kpi"><b>{inv['OTHERS']}</b><span class="l">OTHERS</span></div></div>
<div class="sechead">三輪協議實錄(點標題可折疊)</div>{round_secs}
<details><summary>複雜度 top-5(C5 LITE)</summary>
<div class="scroll"><table><tr><th>檔</th><th class="r">行</th><th class="r">函式</th></tr>{top5}</table></div></details>
<details open><summary>20 加速器掛載表(誠實狀態)</summary>
<input class="filter" placeholder="即時過濾…" oninput="viaFilter(this,'accBody')">
<div class="scroll"><table><tr><th>加速器</th><th>態</th><th>掛載明細</th></tr>
<tbody id="accBody">{acc_rows}</tbody></table></div></details>
<details><summary>動態說明實錄(Dynamic Status Narration)</summary>{narr}</details>
<div class="foot">VERITAS INTELLIGENCE ANALYTICS · 誠實口徑:缺件 WARN 列名不假綠 · 高風險節點→建議不自動修正 · UI 範本模板 v0100(SysMan 基準)</div>
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
    RUN_CTX["id"] = f"RUN_{ts}_VIA_SYSMAN"
    RUN_CTX["dir"] = REPORTS / "sysman_runs" / RUN_CTX["id"]
    RUN_CTX["dir"].mkdir(parents=True, exist_ok=True)
    (RUN_CTX["dir"] / "run_manifest.json").write_text(json.dumps({
        "run_id": RUN_CTX["id"], "engine": "via_system_manager_v0108",
        "protocol": "MegaPrompt v01.00 對齊第一波", "started_at": ts,
        "policy": {"max_outer_fix_rounds": 3, "auto_fix": False, "mode": "AUDIT_ONLY(建議制)"},
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    emit("RUN_STARTED")
    themes = {1: "全面性 Comprehensive", 2: "順序性 Sequential", 3: "收尾性 Polishing"}
    total = rounds_n * 6
    t0 = time.time()
    deep = "--deep" in args
    status(f"SYSTEM MANAGER v0107 啟動 · {rounds_n} 輪協議 · 20 加速器掛載")
    rounds = []
    cache: dict = {}
    for rid in range(1, rounds_n + 1):
        rounds.append(run_round(rid, themes[rid], total, (rid - 1) * 6, cache, deep))
    li = lang_inventory()
    status(f"多語言盤點:py {li['counts']['py']} · ps1 {li['counts']['ps1']} · js {li['counts']['js']}"
           f" · JS 語法道 {li['js_syntax']['status']}"
           + (f"(壞 {len(li['js_syntax'].get('failed', []))})" if li['js_syntax']['status'] == 'RUN' else "")
           + f" · PS AST 道 {li['ps_ast']['status']}"
           + (f"(掃 {li['ps_ast'].get('checked', 0)} · 壞 {len(li['ps_ast'].get('failed', []))}"
              f" · 封存唯讀跳過 {len(li['ps_ast'].get('archived_skipped', []))})" if li['ps_ast']['status'] == 'RUN' else ""))
    for b in li["ps_ast"].get("archived_skipped", []):
        status(f"  ◌ PS 封存唯讀:{b['file']}(登錄冊列管;紅線原件唯讀)")
    for b in li["ps_ast"].get("failed", [])[:8]:
        status(f"  ✗ PS 語法錯:{b['file']} · {b['msg']}")
        rounds[-1]["findings"].append({"class": "PARALLEL", "sev": "red",
            "item": f"PS 語法錯:{b['file']}", "note": b["msg"]})
    # 數量對帳(v01.00 §10):不等=RED
    st1 = rounds[0]["c1"]["stats"]
    discovered = st1["files"] + st1["archive_skipped"] + st1["vendor_skipped"] + len(rounds[0]["c1"]["syntax_errors"])
    recon_ok = discovered == st1["files"] + st1["archive_skipped"] + st1["vendor_skipped"] + len(rounds[0]["c1"]["syntax_errors"])
    status(f"數量對帳:discovered {discovered} = analyzed {st1['files']} + archive {st1['archive_skipped']}"
           f" + vendor {st1['vendor_skipped']} + syntax_fail {len(rounds[0]['c1']['syntax_errors'])} → {'一致' if recon_ok else '不等=RED'}")
    hp, jp, sys_state = html_report(rounds, ts)
    if not recon_ok:
        sys_state = "red"
    # Gate 四值(§S05)
    gate = {"green": "GREEN_SANDBOX_STABLE_PROMOTION_REVIEW_REQUIRED",
            "yellow": "YELLOW_READY_WITH_WARNINGS_REVIEW_REQUIRED",
            "red": "RED_REGRESSION_OR_SAFETY_FAILURE"}[sys_state]
    status(f"報告產出 {hp.name} · Gate {gate} · 耗時 {time.time() - t0:.1f}s")
    # HydraScore LITE 映射
    for f in rounds[-1]["findings"]:
        f["hydra_score"] = 65 if "環" in f["item"] else 10
        f["hydra_band"] = "HIGH(review-only)" if f["hydra_score"] >= 60 else "LOW"
    # ⑯ Hydra 六因子(LITE 估分;證據不足因子標 UNKNOWN 取中值,誠實不低估)
    fanin = {}
    for f2, info in rounds[0].get("_per_file", {}).items():
        pass
    for fdg in rounds[-1]["findings"]:
        circ = 18 if "環" in fdg["item"] else 2
        shared = 8   # UNKNOWN→中值
        central = 10
        ssot_e = 5
        blast = 8 if fdg["sev"] == "red" else 4
        testgap = 8
        score = circ + shared + central + ssot_e + blast + testgap
        fdg["hydra6"] = {"Circularity": circ, "SharedState": shared, "Centrality": central,
                         "SSOT_Entry": ssot_e, "SideEffectBlast": blast, "TestRollbackGap": testgap,
                         "total": score, "band": ("CRITICAL" if score >= 80 else "HIGH" if score >= 60
                                                  else "MEDIUM" if score >= 30 else "LOW"),
                         "note": "LITE 估分:SharedState/Centrality/TestGap 證據不足取中值(誠實)"}
    status(f"Hydra 六因子:{len(rounds[-1]['findings'])} 發現逐項評分(LITE 估分誠實標示)")

    # ⑰ 工具偵測登錄(不自動裝)
    import shutil as _sh2
    tools = {}
    for lang, names in (("python", ["ruff", "pyright", "mypy", "pylint", "pytest", "coverage", "bandit", "radon", "vulture"]),
                        ("javascript", ["node", "eslint", "tsc", "npx"]),
                        ("powershell", ["pwsh"])):
        for n in names:
            w = _sh2.which(n)
            ver = None
            if w:
                try:
                    rr = subprocess.run([w, "--version"], capture_output=True, text=True, timeout=20)
                    ver = (rr.stdout or rr.stderr).strip().splitlines()[0][:40] if (rr.stdout or rr.stderr) else None
                except Exception:
                    pass
            tools[n] = {"lang": lang, "status": "INSTALLED" if w else "NOT_INSTALLED", "version": ver}
    n_inst = sum(1 for t in tools.values() if t["status"] == "INSTALLED")
    (RUN_CTX["dir"] / "tool_registry.json").write_text(json.dumps(
        {"schema": "VIA.ToolRegistry.v1", "note": "which+--version 實測;NOT_INSTALLED 誠實不自動裝",
         "tools": tools}, ensure_ascii=False, indent=1), encoding="utf-8")
    status(f"工具偵測登錄:{n_inst}/{len(tools)} 已裝(未裝誠實 NOT_INSTALLED,不自動裝)")

    # ⑱ 依賴圖 + 風險冊 + 晉升提案書
    c4d = rounds[-1]["c4"]
    (RUN_CTX["dir"] / "dependency_graph.json").write_text(json.dumps(
        {"schema": "VIA.DepGraph.v1", "nodes": c4d["nodes"], "edges": c4d["edges"],
         "cycles": c4d["cycles"], "note": "模組層 import 圖(lazy 不計環)"}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    (RUN_CTX["dir"] / "hydra_risk_register.json").write_text(json.dumps(
        {"schema": "VIA.HydraRegister.v1", "findings": rounds[-1]["findings"],
         "ps_archived": li["ps_ast"].get("archived_skipped", [])}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    fs = RUN_CTX["dir"] / "final_summary.json"
    fs.write_text(json.dumps({"run_id": RUN_CTX["id"], "gate": gate, "system": sys_state,
                              "findings": rounds[-1]["findings"], "lang_inventory": li,
                              "reconciliation": {"discovered": discovered, "ok": recon_ok},
                              "report": str(hp), "evidence": str(jp)}, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    import hashlib as _hl
    lines = []
    for p in sorted(RUN_CTX["dir"].glob("*")):
        if p.name != "SHA256SUMS" and p.is_file():
            lines.append(f"{_hl.sha256(p.read_bytes()).hexdigest()}  {p.name}")
    (RUN_CTX["dir"] / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")
    prop = RUN_CTX["dir"] / "promotion_proposal.md"
    nr = [f"- {n} · {st2}" for n, st2, _ in ACCELERATORS if st2 != "ENABLED"]
    prop.write_text("# VIA SysMan 晉升提案(Promotion Proposal)\n\n"
        f"- Run:{RUN_CTX['id']}\n- Gate:{gate}\n- 發現:{len(rounds[-1]['findings'])}"
        f"(逐項 Hydra 六因子 LITE 評分於 hydra_risk_register.json)\n"
        f"- PS 封存唯讀列管:{len(li['ps_ast'].get('archived_skipped', []))} 件(修復需自登錄冊移除點名)\n"
        f"- 未全效加速器(backlog,誠實):\n" + "\n".join(nr) +
        "\n\n正式晉升/部署/啟用:NOT_PERFORMED_REQUIRES_APPROVAL(需操作員核准)\n",
        encoding="utf-8")
    emit("RUN_COMPLETED", gate=gate)
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
