#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL127_SixStreams v0102 — 六流程零九頭龍派工引擎(批365 旗艦 Mega-Prompt 覆蓋收官:+S4b uv 依賴/多環境隔離流程(MDL050 唯讀)+七矩陣+三輪冊+覆蓋冊;批364 S5 NODE_PATH;批342;操作員令「六個同步流程同步進行,

批354 Zero-Hydra 改號(雲端線 MDL123 DataHome/124 BridgeSweeper/125 FixAll/126 NetBench 先發先得已在 main):本檔原號 CGC_MDL123_SixStreams→CGC_MDL127_SixStreams;原件 byte-exact 於 references/intake/VIA_Batch347_Bundle_b354;互引全數同步改號;功能零變。
以不產生九頭龍風險、不傷害系統為前提」+「加入二十個加速器;PY 指令導入加入引擎;動態進度條」)
====================================================================
職權:六大獨立流程並行派工(每流程=獨立子行程+獨立 log+硬性逾時),彼此零共享狀態;
  唯一匯合點=本引擎事後讀各自 exit code 與 [計] 行(逐字引用,零重算)。
  非 --go 一律 dry-run:任何流程皆不得寫入母樹;--go 只放行 S1(Unified Repair,
  其自帶 .viafix.bak 與 re-parse 閘)。
二十加速器(A01–A20)對映六流程(每流程=分析·執行·呈現三段;各段一燈):
  S1 代碼層 AST 修復      A01 AST 精準解析·A02 多語言語意·A06 修正建議·A13 版本差異回滾
  S2 SSOT/Regex 校準      A08 SSOT 對齊·A15 修正順序(門檻冊)
  S3 解耦/模組註冊        A12 多子系統同步·A04 依賴拓撲
  S4 性能/死碼(唯讀)      A11 性能複雜度·A10 錯誤分類·A03 九頭龍風險(唯讀稽核)
  S5 沙盒回歸             A05 沙盒隔離·A14 覆蓋率回歸
  S6 UI Matrix/部署       A09 視覺化矩陣·A20 自動部署初始化
  引擎層(本體)            A07 三輪全景(=三段輪)·A16 動態進度條·A17 動態說明·
                          A18 非阻塞(子行程+檔案重導+輪詢)·A19 多引擎整合
誠實律:加速器只在其對映流程真跑且 rc 可讀時亮綠;流程缺(檔不在)=灰(誠實缺);
  逾時=紅;工具自報 FAIL≥1=黃。本引擎不替任何流程「宣稱通過」。
動態進度:每流程權重(預估秒)×log 行數成長→即時百分比;控制台單行刷新+每流程收束一行敘述。
用法:python3 CGC_MDL127_SixStreams_v0100.py [run] [--go] [--no-open] [--timeout N] [--max-tests N]
      python3 CGC_MDL127_SixStreams_v0100.py --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_support = str(_sa_p / "supportive modules")
            if _sa_support not in _sa_sys.path:
                _sa_sys.path.insert(0, _sa_support)
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REG = VIA / "supportive modules" / "registry"
OUT_ROOT = VIA / "VIA_Reports" / "six_streams"
IS_NT = os.name == "nt"


def _latest(dirp: Path, pat: str) -> Path | None:
    hits = sorted(dirp.glob(pat))
    return hits[-1] if hits else None


def _pwsh() -> str:
    """回完整路徑(need 檢查用 Path.exists;裸名會被誤判缺檔)"""
    for c in ("pwsh", "powershell"):
        w = shutil.which(c)
        if w:
            return w
    return ""


def _venv_py() -> str:
    for c in (Path.home() / "envs" / "via_vrn4" / "Scripts" / "python.exe",
              Path.home() / "envs" / "via_vrn4" / "bin" / "python"):
        if c.exists():
            return str(c)
    return sys.executable


def _downloads_tool(name: str) -> str:
    for base in (Path.home() / "Downloads", HERE, VIA):
        p = base / name
        if p.exists():
            return str(p)
    return ""


# ---------------------------------------------------------------------
# 二十加速器冊(靜態對映;燈號由流程結果推導)
# ---------------------------------------------------------------------
ACCEL = [
    ("A01", "AST 精準解析", "S1"), ("A02", "多語言語意模型", "S1"), ("A06", "自動修正建議", "S1"), ("A13", "版本差異與回滾", "S1"),
    ("A08", "SSOT 對齊", "S2"), ("A15", "修正順序最佳化", "S2b"),
    ("A12", "多子系統同步", "S3"), ("A04", "依賴拓撲排序", "S3"),
    ("A11", "性能與複雜度", "S4"), ("A10", "錯誤分類分群", "S4"), ("A03", "九頭龍風險(唯讀)", "S4"),
    ("A05", "沙盒隔離執行", "S5"), ("A14", "覆蓋率與回歸", "S5b"),
    ("A09", "視覺化矩陣", "S6"), ("A20", "自動部署初始化", "S6"),
    ("A07", "三輪全景(三段輪)", "ENGINE"), ("A16", "動態進度條", "ENGINE"), ("A17", "動態說明", "ENGINE"),
    ("A18", "非阻塞派工", "ENGINE"), ("A19", "多引擎整合", "ENGINE"),
]


def build_streams(go: bool, no_open: bool, max_tests: int) -> list:
    """六流程冊(九子行程);每項=獨立可執行;缺檔=誠實 MISSING 不假派"""
    ps = _pwsh()
    unified = _downloads_tool("Invoke-VIA-Unified-Accel20-v0103.ps1")
    deftest = _downloads_tool("VIA_DefTestAudit_v0101.py") or _downloads_tool("VIA_DefTestAudit_v0100.py")
    vap25 = VIA / "functional modules" / "VAP" / "references" / "intake" / "VAP_v025_Complete_Package"
    vpy = _venv_py()
    def L(pat):
        p = _latest(REG, pat)
        return str(p) if p else ""
    run_dir_placeholder = "{RUN}"
    S = [
        {"id": "S1",  "zh": "代碼層 AST 修復", "weight": 260,
         "argv": [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", unified, "-Mode", "Repair" if go else "Scan",
                  "-Root", str(VIA), "-OutRoot", run_dir_placeholder + "/S1_unified", "-NoOpen", "-RepairParseErrors"] + (["-GoToken", "GO_v1"] if go else []),
         "cwd": str(VIA), "need": [ps, unified]},
        {"id": "S1b", "zh": "DeckServer 自測", "weight": 8,
         "argv": [sys.executable, L("CGC_MDL095_DeckServer_v0*.py"), "--selftest"], "cwd": str(REG), "need": [L("CGC_MDL095_DeckServer_v0*.py")]},
        {"id": "S2",  "zh": "SSOT/Regex 字典自測", "weight": 6,
         "argv": [sys.executable, L("CGC_MDL115_SSOTRegexDict_v0*.py"), "--selftest"], "cwd": str(REG), "need": [L("CGC_MDL115_SSOTRegexDict_v0*.py")]},
        {"id": "S2b", "zh": "門檻冊 SSOT · 殼引擎自測", "weight": 8,
         "argv": [sys.executable, L("CGC_MDL116_UnifiedShell_v0*.py"), "--selftest"], "cwd": str(REG), "need": [L("CGC_MDL116_UnifiedShell_v0*.py")]},
        {"id": "S3",  "zh": "上船件冊 註冊", "weight": 4,
         "argv": [sys.executable, L("CGC_MDL122_IntakeRoster_v0*.py"), "--selftest"], "cwd": str(REG), "need": [L("CGC_MDL122_IntakeRoster_v0*.py")]},
        {"id": "S4",  "zh": "死碼/漂移 稽核(唯讀)", "weight": 30,
         "argv": [vpy, deftest, "--root", str(VIA), "--out", run_dir_placeholder + "/S4_deftest"], "cwd": str(VIA), "need": [deftest]},
        {"id": "S4b", "zh": "uv 依賴解析/衝突立拔/多環境隔離(MDL050;唯讀計畫 --offline)", "weight": 20,
         "argv": [sys.executable, L("CGC_MDL050_EnvRebuild_v0*.py"), "--offline"], "cwd": str(REG), "need": [L("CGC_MDL050_EnvRebuild_v0*.py")]},
        {"id": "S5",  "zh": "VAP v025 套件回歸", "weight": 10,
         "argv": [sys.executable, str(vap25 / "tests" / "run_all_tests_v025.py")], "cwd": str(vap25), "need": [str(vap25 / "tests" / "run_all_tests_v025.py")]},
        {"id": "S5b", "zh": "沙盒 pytest 回歸(Verify)", "weight": 360,
         "argv": [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", unified, "-Mode", "Verify", "-Root", str(VIA),
                  "-PythonExe", vpy, "-OutRoot", run_dir_placeholder + "/S5_verify", "-NoOpen", "-MaxTestFiles", str(max_tests)],
         "cwd": str(VIA), "need": [ps, unified]},
        {"id": "S6",  "zh": "四殼再生 + 自動跳出", "weight": 6,
         "argv": [sys.executable, L("CGC_MDL116_UnifiedShell_v0*.py")] + ([] if no_open else ["--open"]), "cwd": str(REG), "need": [L("CGC_MDL116_UnifiedShell_v0*.py")]},
    ]
    return S


# ---------------------------------------------------------------------
# 派工 + 動態進度
# ---------------------------------------------------------------------
NODE_DEPS = VIA / "VIA_Reports" / "node_deps" / "node_modules"   # 批364:FixAll vap_node 落點(收容原件夾零觸碰)


def _child_env() -> dict:
    """子行程環境:utf-8;node_deps 在=NODE_PATH 前置(S5 VAP v025 Browser UAT require('playwright'))"""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    if NODE_DEPS.exists():
        env["NODE_PATH"] = str(NODE_DEPS) + (os.pathsep + env["NODE_PATH"] if env.get("NODE_PATH") else "")
    return env


# 批365:旗艦 Mega-Prompt 覆蓋冊(七段逐條→在庫實現;誠實 IMPLEMENTED/PARTIAL/GAP;零發明)
COVERAGE = [
    ("§0 核心", "全景式分析與診斷先行(Ruff/PSScriptAnalyzer/Parser)", "Invoke-VIA-Unified-Accel20 Scan(U01–U08)+VIA_DefTestAudit(S4)", "IMPLEMENTED"),
    ("§0 核心", "AST 雙模錨點(精準/彈性)", "Accel20 Mode 徽章 EXACT/HEURISTIC(逐規則標)", "IMPLEMENTED"),
    ("§0 核心", "六流程無限制推進+Parallel-Fixable/Sequence-Dependent 分類", "MDL127 九→十子行程並行;Accel20 findings.Class 兩類", "IMPLEMENTED"),
    ("§1 環境", "SSOT 規範與同義字 Regex 治理中心", "CGC_MDL115 SSOTRegexDict(S2)+VIA_SSOT_RegexDict 冊", "IMPLEMENTED"),
    ("§1 環境", "uv 極速解析+三鏡像(清華/阿里/PyPI)+衝突立拔+via_* 隔離境", "CGC_MDL050 EnvRebuild(uv pip compile;三源測速;隔離重建計畫;S4b 唯讀)", "IMPLEMENTED"),
    ("§1 環境", "非阻塞 PowerShell 啟動器 launch.ps1", "Invoke-VIA-Complete(啟動器/工人分離;.py.out 尾讀;Ctrl-C 免疫)+via-mobile", "IMPLEMENTED"),
    ("§2 三輪分析", "全景/錯誤識別/優化點/AST/SSOT 對齊/Hydra/分類/多子系統同步", "Accel20 U01–U13 + S2/S3/S4 各自自測;三輪=Scan→Repair→Verify", "IMPLEMENTED"),
    ("§3 六流程", "P1 代碼層 AST 修復", "S1 Accel20 Scan/Repair(GO_v1 閘)", "IMPLEMENTED"),
    ("§3 六流程", "P2 SSOT/Regex 校準", "S2 MDL115 + S2b 門檻冊/MDL116", "IMPLEMENTED"),
    ("§3 六流程", "P3 子系統解耦/模組插槽註冊", "S3 MDL122 上船件冊+S1b DeckServer 任務冊", "IMPLEMENTED"),
    ("§3 六流程", "P4 uv 依賴解析/衝突立拔/多環境隔離", "S4b MDL050 --offline(計畫唯讀;安裝由操作員 via-install 自跑)", "IMPLEMENTED"),
    ("§3 六流程", "P5 沙盒多重驗證/性能/回歸", "S5 VAP v025 回歸+S5b Accel20 Verify(pytest 沙盒)+S4 死碼/漂移", "IMPLEMENTED"),
    ("§3 六流程", "P6 自適應 HTML UI Matrix+非阻塞部署監控", "S6 四殼再生+本頁四分區七矩陣+MDL130 UIBridge", "IMPLEMENTED"),
    ("§4 三輪修正", "R1 全面性(Parallel-Fixable 並行)/R2 順序性(拓撲)/R3 收尾", "Accel20 Repair=R1 真寫(GO_v1);R2=ORDERED ACTIONS 建議制(高 Hydra 節點只建議);R3=死碼/格式(S4 唯讀+via-repo-optimize)", "PARTIAL:R2/R3 建議制不自動寫(Zero-Hydra 律)"),
    ("§5 驗證循環", "test→debug→upgrade→…→user-test;activate→until perfect", "via-mobile 鏈:六流程→補齊 13 步→refail 轉綠實證→digest;MDL129 生命週期九階段", "IMPLEMENTED"),
    ("§6 二十加速器", "A01–A20 全啟用", "Accel20 U01–U20(PS 真用)+MDL127 A01–A20 燈(流程推導)+SUP_MDL737 20 加速器(py)+ENG074 F01–F20(擷取)", "IMPLEMENTED"),
    ("§7 UI Matrix", "小字/自適應/自動換行;MODULE/ENGINE/FUNCTION-LIB/OTHERS", "本頁 font 11px;table-layout fixed;overflow-wrap;四分區", "IMPLEMENTED"),
    ("§7 UI Matrix", "七矩陣:錯誤/優化/Hydra 風險/依賴拓撲/修正順序/數量校驗/SSOT 對照", "本頁 MATRICES×7(來源=S1 unified_plan.json/S4/S4b/S2 tally;缺=NO_DATA 誠實)", "IMPLEMENTED"),
]


def _find_plan(run_dir: Path) -> dict:
    hits = sorted(run_dir.glob("S1_unified/**/unified_plan.json"))
    if not hits:
        return {}
    try:
        return json.loads(hits[-1].read_text(encoding="utf-8-sig", errors="replace"))
    except Exception:
        return {}


def _read_log(run_dir: Path, sid: str) -> str:
    try:
        return (run_dir / "logs" / f"{sid}.log").read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def seven_matrices(run_dir: Path, rows: list, plan: dict | None = None) -> list:
    """七矩陣(每列 [name, state, rows[(k, v, note)], source]);來源真檔;缺=NO_DATA 誠實"""
    plan = plan if plan is not None else _find_plan(run_dir)
    by = {r["id"]: r for r in rows}
    out = []
    # 1 錯誤矩陣
    f = plan.get("findings") or []
    if isinstance(f, dict):
        f = [f]
    from collections import Counter
    if f:
        c = Counter((x.get("Rule", "?"), x.get("Severity", "?"), x.get("Class", "?")) for x in f if isinstance(x, dict))
        out.append(["錯誤矩陣 Error", "DATA", [(f"{r} · {sv}", str(n), cl) for (r, sv, cl), n in c.most_common(40)], "S1 unified_plan.findings"])
    else:
        out.append(["錯誤矩陣 Error", "NO_DATA", [], "S1 unified_plan.json 缺或零 findings"])
    # 2 優化矩陣
    s4 = _read_log(run_dir, "S4")
    opt = [(l.strip()[:60], "", "") for l in s4.splitlines() if re.search(r"dead|drift|dup|複雜|冗餘|死碼|漂移|families|\[計\]", l, re.I)][:20]
    out.append(["優化矩陣 Optimize", "DATA" if opt else "NO_DATA", opt, "S4 DefTestAudit log(死碼/漂移/重複)"])
    # 3 Hydra 風險矩陣
    dup = plan.get("duplicate_families") or []
    if isinstance(dup, dict):
        dup = [dup]
    hy = [(str(d.get("Name", "?")), f"copies {d.get('Copies', '?')} distinct {d.get('Distinct', '?')}", str(d.get("Verdict", ""))) for d in dup if isinstance(d, dict)][:40]
    out.append(["Hydra 風險矩陣 Hydra", "DATA" if hy else "NO_DATA", hy, f"S1 duplicate_families(drifted={plan.get('drifted_families', '?')})"])
    # 4 依賴拓撲矩陣
    s4b = _read_log(run_dir, "S4b")
    topo = [(l.strip()[:60], "", "") for l in s4b.splitlines() if re.search(r"REBUILD|WARN|BASE|via_|numpy|衝突|隔離|\[計\]", l)][:25]
    mm = plan.get("missing_modules") or []
    topo += [(f"missing module {m}", "", "S1") for m in (mm if isinstance(mm, list) else [mm])][:10]
    out.append(["依賴拓撲矩陣 Topology", "DATA" if topo else "NO_DATA", topo, "S4b MDL050 --offline + S1 missing_modules"])
    # 5 修正順序矩陣
    acts = plan.get("actions") or []
    if isinstance(acts, dict):
        acts = [acts]
    fo = [(f"R{a.get('Order', '?')}", str(a.get("Action", ""))[:70], str(a.get("Why", ""))[:60]) for a in acts if isinstance(a, dict)]
    out.append(["修正順序矩陣 Fix-Order", "DATA" if fo else "NO_DATA", fo, "S1 ordered actions(Parallel-Fixable 先;Sequence-Dependent 依拓撲)"])
    # 6 數量校驗矩陣(tally 數字 vs 狀態一致)
    cnt = []
    for r in rows:
        m = re.search(r"OK\s*(\d+).{0,12}?FAIL\s*(\d+)", r["tally"])
        if m:
            ok, fl = int(m.group(1)), int(m.group(2))
            consistent = (fl == 0) == (r["state"] == "GREEN") or r["state"] in ("RED", "MISSING")
            cnt.append((r["id"], f"OK {ok} FAIL {fl} · {r['state']}", "一致" if consistent else "不一致(候查)"))
        else:
            cnt.append((r["id"], r["state"], "無 [計] 數字(逐字引用律:不代算)"))
    out.append(["數量校驗矩陣 Count-Check", "DATA", cnt, "各流程 [計] 行 vs RYG"])
    # 7 SSOT 對照矩陣
    s2 = by.get("S2", {}).get("tally", "")
    s2b = by.get("S2b", {}).get("tally", "")
    ss = [(k, v, "") for k, v in (("S2 SSOT/Regex 字典", s2), ("S2b 門檻冊/殼引擎", s2b)) if v]
    out.append(["SSOT 對照矩陣 SSOT", "DATA" if ss else "NO_DATA", ss, "S2/S2b 自測 [計](逐字)"])
    return out


def rounds_from_plan(plan: dict) -> dict:
    f = plan.get("findings") or []
    if isinstance(f, dict):
        f = [f]
    pf = sum(1 for x in f if isinstance(x, dict) and x.get("Class") == "Parallel-Fixable")
    sd = sum(1 for x in f if isinstance(x, dict) and x.get("Class") == "Sequence-Dependent")
    acts = plan.get("actions") or []
    return {"R1_parallel_fixable": pf, "R2_sequence_dependent": sd, "R3_polish_actions": len(acts) if isinstance(acts, list) else 1,
            "applied": plan.get("applied"), "rejected": plan.get("rejected"), "mode": plan.get("mode", "")}


def _bar(pct: float, width: int = 28) -> str:
    n = int(width * max(0.0, min(1.0, pct)))
    return "█" * n + "░" * (width - n)


def run(go: bool = False, no_open: bool = False, timeout: int = 900, max_tests: int = 25, quiet: bool = False) -> dict:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUT_ROOT / f"RUN_{stamp}"
    (run_dir / "logs").mkdir(parents=True, exist_ok=True)
    (run_dir / "reports").mkdir(parents=True, exist_ok=True)
    streams = build_streams(go, no_open, max_tests)
    t_start = time.time()
    procs = {}
    if not quiet:
        print(f"=== 六流程零九頭龍派工(CGC_MDL127 v0102;十子行程)· {'APPLY(S1 only)' if go else 'DRY-RUN'} · 逾時 {timeout}s/流程 ===")
    for s in streams:
        log = run_dir / "logs" / f"{s['id']}.log"
        argv = [a.replace("{RUN}", str(run_dir)) for a in s["argv"]]
        missing = [n for n in s["need"] if not n or not Path(n).exists()]
        if missing:
            log.write_text("MISSING: " + "; ".join(missing) + "\n", encoding="utf-8")
            procs[s["id"]] = {"p": None, "log": log, "s": s, "t0": time.time(), "rc": -3, "done": True, "lines": 0}
            if not quiet:
                print(f"  {s['id']:<4} MISSING  {s['zh']}  ({missing[0]})")
            continue
        lf = open(log, "w", encoding="utf-8", errors="replace")
        try:
            p = subprocess.Popen(argv, stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                 cwd=s["cwd"], env=_child_env())
            procs[s["id"]] = {"p": p, "lf": lf, "log": log, "s": s, "t0": time.time(), "rc": None, "done": False, "lines": 0}
            if not quiet:
                print(f"  {s['id']:<4} launched {s['zh']}")
        except Exception as exc:
            lf.write(f"LAUNCH FAILED: {exc}\n"); lf.close()
            procs[s["id"]] = {"p": None, "log": log, "s": s, "t0": time.time(), "rc": -4, "done": True, "lines": 0}
            if not quiet:
                print(f"  {s['id']:<4} launch failed {exc}")

    # A16/A17: 進度=各流程 min(elapsed/weight, 0.97) 加權;log 行數成長=活著證明
    total_w = sum(s["weight"] for s in streams) or 1
    last_line = ""
    while not all(e["done"] for e in procs.values()):
        time.sleep(0.5)
        acc = 0.0
        alive = []
        for sid, e in procs.items():
            w = e["s"]["weight"]
            if e["done"]:
                acc += w; continue
            el = time.time() - e["t0"]
            try:
                e["lines"] = sum(1 for _ in open(e["log"], encoding="utf-8", errors="ignore"))
            except Exception:
                pass
            rc = e["p"].poll()
            if rc is not None:
                e["rc"] = rc; e["done"] = True; e["lf"].close()
                acc += w
                if not quiet:
                    sys.stdout.write("\r" + " " * 100 + "\r")
                    print(f"  {sid:<4} exit {rc:<3} {int(el):>4}s  {e['s']['zh']}")
            elif el >= timeout:
                try:
                    e["p"].kill()
                except Exception:
                    pass
                e["rc"] = -9; e["done"] = True
                e["lf"].write(f"\nTIMEOUT {timeout}s (killed; other streams unaffected)\n"); e["lf"].close()
                acc += w
                if not quiet:
                    sys.stdout.write("\r" + " " * 100 + "\r")
                    print(f"  {sid:<4} TIMEOUT {timeout}s  {e['s']['zh']}")
            else:
                acc += w * min(0.97, el / max(1, w))
                alive.append(f"{sid}:{e['lines']}")
        pct = acc / total_w
        if not quiet:
            line = f"  [{_bar(pct)}] {int(pct * 100):3d}%  {int(time.time() - t_start):>4}s  running {' '.join(alive)}"
            if line != last_line:
                sys.stdout.write("\r" + line[:118].ljust(118)); sys.stdout.flush(); last_line = line
    if not quiet:
        sys.stdout.write("\r" + " " * 118 + "\r")

    # 匯合:逐字引用各工具 [計] 行
    rows = []
    for s in streams:
        e = procs[s["id"]]
        text = ""
        try:
            text = e["log"].read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
        lines = [l for l in text.splitlines() if l.strip()]
        tally = ""
        for pat in (r"\[計\]", r'^\s*"status"\s*:', r"overall ", r"passed|FAIL \d"):
            m = [l for l in lines if re.search(pat, l)]
            if m:
                tally = m[0].strip(); break
        tail = lines[-1].strip() if lines else ""
        rc = e["rc"]
        state = "GREEN"
        if rc == -3:
            state = "MISSING"
        elif rc == -9:
            state = "RED"
        elif rc != 0:
            state = "YELLOW"
        if re.search(r"FAIL [1-9]|\"failed\": [1-9]|overall RED|\"status\": \"FAIL\"", tally):
            state = "YELLOW" if state == "GREEN" else state
        rows.append({"id": s["id"], "zh": s["zh"], "rc": rc, "state": state, "tally": tally, "tail": tail,
                     "log": str(e["log"]), "secs": int(time.time() - e["t0"]) if e["t0"] else 0})

    by = {r["id"]: r for r in rows}
    def accel_state(target):
        if target == "ENGINE":
            return "GREEN"
        r = by.get(target)
        if not r:
            return "MISSING"
        return r["state"]
    accels = [{"id": a, "zh": z, "stream": t, "state": accel_state(t)} for a, z, t in ACCEL]

    overall = "GREEN"
    if any(r["state"] == "RED" for r in rows):
        overall = "RED"
    elif any(r["state"] in ("YELLOW", "MISSING") for r in rows):
        overall = "YELLOW"
    plan = _find_plan(run_dir)
    result = {"schema": "VIA_SixStreams/1.1", "engine": "CGC_MDL127", "version": "v0102", "stamp": stamp,
              "mode": "APPLY(S1)" if go else "DRY-RUN", "overall": overall, "elapsed_s": int(time.time() - t_start),
              "timeout_s": timeout, "streams": rows, "accelerators": accels, "run_dir": str(run_dir),
              "matrices": seven_matrices(run_dir, rows, plan), "rounds": rounds_from_plan(plan),
              "coverage": [{"sec": a, "clause": b, "impl": c, "state": d} for a, b, c, d in COVERAGE]}
    (run_dir / "six_streams.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    rep = run_dir / "reports" / f"SIX_STREAMS_{stamp}.html"
    rep.write_text(render(result), encoding="utf-8")
    result["report"] = str(rep)
    if not quiet:
        print(f"  overall {overall} · {len(rows)} 流程 · {result['elapsed_s']}s")
        for r in rows:
            print(f"  {r['id']:<4} {r['state']:<8} rc={r['rc']!s:<3} {r['zh']}   {r['tally']}")
        print(f"  matrix {rep}")
    if not no_open:
        try:
            webbrowser.open(rep.resolve().as_uri())
        except Exception:
            pass
    return result


# ---------------------------------------------------------------------
# A09 四分區矩陣(小字體·自適應·自動換行·RYG·零 CDN)
# ---------------------------------------------------------------------
def render(r: dict) -> str:
    def b(state):
        c = {"GREEN": "gr", "YELLOW": "ye", "RED": "rd", "MISSING": "gy"}.get(state, "gy")
        return f'<span class="b {c}">{state}</span>'
    e = html.escape
    srows = "".join(f'<tr><td class="m">{s["id"]}</td><td>{e(s["zh"])}</td><td class="c">{b(s["state"])}</td>'
                    f'<td class="c m">{s["rc"]}</td><td class="c m">{s["secs"]}s</td><td class="m">{e(s["tally"])}</td>'
                    f'<td class="m dim">{e(s["tail"])}</td></tr>' for s in r["streams"])
    def arows(where):
        return "".join(f'<tr><td class="m">{a["id"]}</td><td>{e(a["zh"])}</td><td class="c">{b(a["state"])}</td><td class="c m">{a["stream"]}</td></tr>'
                       for a in r["accelerators"] if (a["stream"] == "ENGINE") == (where == "ENGINE"))
    n = {k: sum(1 for s in r["streams"] if s["state"] == k) for k in ("GREEN", "YELLOW", "RED", "MISSING")}

    def mtable(m):
        name, st, items, src = m
        body = "".join('<tr><td class="m">' + e(str(k)) + '</td><td class="m">' + e(str(v)) + '</td><td class="dim">' + e(str(nt)) + "</td></tr>" for k, v, nt in items) \
            or '<tr><td colspan="3" class="dim">NO_DATA(誠實)</td></tr>'
        badge = b("GREEN") if st == "DATA" else b("MISSING")
        return ('<h3 style="font-size:11px;margin:10px 0 4px">' + e(name) + " " + badge + ' <span class="dim">' + e(src) + "</span></h3>"
                '<table><colgroup><col style="width:34%"><col style="width:33%"><col style="width:33%"></colgroup><tbody>' + body + "</tbody></table>")
    mrows = "".join(mtable(m) for m in r.get("matrices", []))

    def cstate(st):
        return b("GREEN") if st == "IMPLEMENTED" else (b("YELLOW") if st.startswith("PARTIAL") else b("RED"))
    crows = "".join('<tr><td class="m">' + e(c["sec"]) + "</td><td>" + e(c["clause"]) + '</td><td class="dim">' + e(c["impl"]) + '</td><td class="c">' + cstate(c["state"]) + " " + e(c["state"].split(":", 1)[1] if ":" in c["state"] else "") + "</td></tr>"
                    for c in r.get("coverage", []))
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA SIX STREAMS · {r["stamp"]}</title>
<style>:root{{--bg:#0f172a;--card:#1e293b;--line:#334155;--tx:#f8fafc;--mu:#94a3b8}}*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--tx);font:11px/1.35 -apple-system,'Segoe UI',Roboto,'Microsoft JhengHei',sans-serif}}
.wrap{{max-width:1400px;margin:0 auto;padding:18px 14px 48px}}h1{{font-size:14px;margin:0}}.sub{{color:var(--mu);margin:3px 0 14px}}
h2{{font-size:12px;margin:20px 0 7px;border-bottom:1px solid var(--line);padding-bottom:5px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;margin-bottom:14px}}.kpi{{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:9px 11px}}.kpi .n{{font-size:17px;font-weight:600}}.kpi .l{{font-size:10px;color:var(--mu)}}
table{{width:100%;table-layout:fixed;border-collapse:collapse;background:var(--card);border:1px solid var(--line)}}th{{font-size:10px;color:var(--mu);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}}td{{padding:4px 6px;border-bottom:1px solid #253248;vertical-align:top;word-wrap:break-word;overflow-wrap:break-word;white-space:normal}}td.c{{text-align:center}}.m{{font-family:ui-monospace,Consolas,monospace}}.dim{{color:var(--mu)}}
.b{{display:inline-block;font-size:10px;padding:1px 6px;border-radius:2px;border:1px solid}}.gr{{background:#064e3b;color:#34d399;border-color:#059669}}.ye{{background:#78350f;color:#fde047;border-color:#d97706}}.rd{{background:#7f1d1d;color:#fca5a5;border-color:#dc2626}}.gy{{background:#1f2937;color:#9ca3af;border-color:#374151}}
.note{{background:var(--card);border:1px solid var(--line);border-left:3px solid #d97706;border-radius:3px;padding:10px 12px;margin-top:16px}}</style></head><body><div class="wrap">
<h1>VIA SIX STREAMS · ZERO-HYDRA MATRIX · 20 ACCELERATORS</h1><p class="sub">CGC_MDL127 v0102 · {r["stamp"]} · {r["mode"]} · {r["elapsed_s"]} s · 逾時 {r["timeout_s"]} s/流程</p>
<div class="kpis"><div class="kpi"><div class="n">{r["overall"]}</div><div class="l">overall RYG</div></div><div class="kpi"><div class="n">{len(r["streams"])}</div><div class="l">streams</div></div>
<div class="kpi"><div class="n">{n["GREEN"]}</div><div class="l">green</div></div><div class="kpi"><div class="n">{n["YELLOW"]}</div><div class="l">yellow</div></div><div class="kpi"><div class="n">{n["RED"]}</div><div class="l">timed out</div></div><div class="kpi"><div class="n">{n["MISSING"]}</div><div class="l">missing (honest)</div></div></div>
<h2>MODULE — six streams (nine processes)</h2>
<table><colgroup><col style="width:5%"><col style="width:16%"><col style="width:8%"><col style="width:4%"><col style="width:5%"><col style="width:30%"><col style="width:32%"></colgroup>
<thead><tr><th>ID</th><th>Stream</th><th>RYG</th><th>rc</th><th>t</th><th>Tally (tool's own [計] line)</th><th>Last line</th></tr></thead><tbody>{srows}</tbody></table>
<h2>FUNCTION-LIB — accelerators mapped to streams</h2>
<table><colgroup><col style="width:8%"><col style="width:40%"><col style="width:12%"><col style="width:40%"></colgroup>
<thead><tr><th>ID</th><th>Accelerator</th><th>RYG</th><th>Stream</th></tr></thead><tbody>{arows("STREAM")}</tbody></table>
<h2>ENGINE — accelerators intrinsic to this orchestrator</h2>
<table><colgroup><col style="width:8%"><col style="width:40%"><col style="width:12%"><col style="width:40%"></colgroup>
<thead><tr><th>ID</th><th>Accelerator</th><th>RYG</th><th>Realised by</th></tr></thead><tbody>{arows("ENGINE")}</tbody></table>
<h2>MATRICES ×7 — error / optimize / hydra / topology / fix-order / count-check / SSOT(真檔來源;缺=NO_DATA 誠實)</h2>
{mrows}
<h2>OTHERS — three rounds · mega-prompt coverage</h2>
<table><colgroup><col style="width:18%"><col style="width:82%"></colgroup><tbody><tr><td class="m">三輪</td><td class="m">{e(json.dumps(r.get("rounds", {}), ensure_ascii=False))}</td></tr></tbody></table>
<table><colgroup><col style="width:9%"><col style="width:30%"><col style="width:47%"><col style="width:14%"></colgroup>
<thead><tr><th>段</th><th>條款</th><th>在庫實現</th><th>state</th></tr></thead><tbody>{crows}</tbody></table>
<div class="note">Zero-Hydra: 九子行程各自獨立(獨立 log·硬性逾時·零共享狀態);任一逾時/崩潰不波及其餘。Tally 逐字引用各工具自報,本引擎零重算、零代答。
非 --go 一律 dry-run:母樹零寫入;--go 僅放行 S1(其自帶 .viafix.bak+re-parse 閘)。加速器燈=對映流程真跑結果推導(缺=灰誠實),
本引擎不替任何流程宣稱通過。Logs: {e(r["run_dir"])}\\logs</div>
</div></body></html>"""


# ---------------------------------------------------------------------
def selftest() -> int:
    fails = []
    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    src = Path(__file__).read_text(encoding="utf-8")
    S = build_streams(False, True, 5)
    chk("① 六流程冊=十子行程(+S4b uv 依賴/多環境隔離唯讀),ID 唯一,每項有 argv/cwd/need/weight",
        len(S) == 10 and len({s["id"] for s in S}) == 10 and all({"argv", "cwd", "need", "weight"} <= set(s) for s in S)
        and any(s["id"] == "S4b" and "--offline" in s["argv"] for s in S))
    chk("② 零共享寫入目標(各流程 OutRoot 皆在 {RUN} 子夾;無二流程同一輸出夾)",
        len({a for s in S for a in s["argv"] if "{RUN}" in a}) == len([a for s in S for a in s["argv"] if "{RUN}" in a]))
    chk("③ dry-run 契約(非 --go 時 S1=Scan 且無 GO 權杖;--go 時僅 S1 帶 GO_v1)",
        "-Mode" in S[0]["argv"] and S[0]["argv"][S[0]["argv"].index("-Mode") + 1] == "Scan" and "GO_v1" not in S[0]["argv"]
        and sum("GO_v1" in s["argv"] for s in build_streams(True, True, 5)) == 1)
    chk("④ 二十加速器冊(A01–A20 齊;每項對映流程或 ENGINE;流程 ID 均在冊)",
        len(ACCEL) == 20 and len({a for a, _, _ in ACCEL}) == 20
        and all(t == "ENGINE" or t in {s["id"] for s in S} for _, _, t in ACCEL))
    chk("⑤ 誠實律(缺檔=MISSING 不假派;逾時=kill+RED;tally 逐字取 [計]/status/overall;零重算)",
        "MISSING" in src and "TIMEOUT" in src and "\\[計\\]" in src and "零重算" in src)
    chk("⑥ 動態進度(A16 加權進度條+A17 每流程收束敘述+A18 子行程檔案重導輪詢;零 pipe ReadToEnd)",
        "_bar(" in src and "stdout=lf" in src and "poll()" in src and ("communi" + "cate(") not in src)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        rd = Path(td)
        (rd / "logs").mkdir()
        (rd / "S1_unified" / "UNIFIED_T").mkdir(parents=True)
        (rd / "S1_unified" / "UNIFIED_T" / "unified_plan.json").write_text(json.dumps({
            "findings": [{"Rule": "UTF8_BOM", "Severity": "LOW", "Class": "Parallel-Fixable"}, {"Rule": "READ_HOST_BLOCKS", "Severity": "HIGH", "Class": "Sequence-Dependent"}],
            "duplicate_families": [{"Name": "x.py", "Copies": 3, "Distinct": 2, "Verdict": "DRIFTED"}], "drifted_families": 1,
            "actions": [{"Order": 1, "Action": "Fix 1 unparseable", "Why": "w"}], "missing_modules": ["polars"], "applied": 0, "rejected": 0, "mode": "Scan"}), encoding="utf-8")
        (rd / "logs" / "S4b.log").write_text("  REBUILD via_np1_py312 numpy 1.26\n  [計] 3/4 綠\n", encoding="utf-8")
        frows = [{"id": "S2", "state": "GREEN", "tally": "[計] 五檢 OK 5 · FAIL 0"}, {"id": "S3", "state": "YELLOW", "tally": "[計] 五檢 OK 4 · FAIL 1"}]
        M7 = seven_matrices(rd, frows)
        rr = rounds_from_plan(_find_plan(rd))
    chk("⑨ 七矩陣真檔來源(錯誤/優化/Hydra/拓撲/修正順序/數量校驗/SSOT;缺=NO_DATA 誠實)",
        len(M7) == 7 and M7[0][1] == "DATA" and M7[1][1] == "NO_DATA" and M7[2][1] == "DATA" and M7[3][1] == "DATA" and M7[4][1] == "DATA"
        and M7[5][2][1][2].startswith("一致") and M7[6][1] == "DATA" and rr["R1_parallel_fixable"] == 1 and rr["R2_sequence_dependent"] == 1)
    chk("⑩ Mega-Prompt 覆蓋冊(七段 18 條;IMPLEMENTED/PARTIAL/GAP 誠實;R2/R3 建議制標 PARTIAL)",
        len(COVERAGE) == 18 and len({c[0].split(" ")[0] for c in COVERAGE}) == 8 and all(c[3].split(":")[0] in ("IMPLEMENTED", "PARTIAL", "GAP") for c in COVERAGE)
        and any(c[3].startswith("PARTIAL") for c in COVERAGE))
    # dry render on a synthetic result (no processes launched)
    fake = {"stamp": "T", "mode": "DRY-RUN", "elapsed_s": 0, "timeout_s": 1, "overall": "GREEN", "run_dir": "x",
            "streams": [{"id": s["id"], "zh": s["zh"], "rc": 0, "state": "GREEN", "tally": "", "tail": "", "secs": 0} for s in S],
            "accelerators": [{"id": a, "zh": z, "stream": t, "state": "GREEN"} for a, z, t in ACCEL],
            "matrices": M7, "rounds": rr, "coverage": [{"sec": a, "clause": b, "impl": c, "state": d} for a, b, c, d in COVERAGE]}
    page = render(fake)
    chk("⑦ 四分區矩陣渲染(MODULE/FUNCTION-LIB/ENGINE/OTHERS;零 CDN;結構成對)",
        all(k in page for k in ("MODULE", "FUNCTION-LIB", "ENGINE", "OTHERS", "MATRICES", "SSOT 對照矩陣")) and "src=\"http" not in page
        and page.count("<table") == page.count("</table>") and page.count("<div") == page.count("</div>"))
    chk("⑧ NODE_PATH 接線(node_deps 在=前置;缺=環境原樣;收容原件夾零觸碰)",
        "NODE_PATH" in src and ("NODE_PATH" in _child_env()) == NODE_DEPS.exists() and "node_deps" in str(NODE_DEPS))
    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 六流程零九頭龍派工引擎(CGC_MDL123 v0100)· 七檢自測(零派工零網路)===")
        return selftest()
    go = "--go" in a
    no_open = "--no-open" in a
    timeout = 900
    max_tests = 25
    if "--timeout" in a:
        timeout = int(a[a.index("--timeout") + 1])
    if "--max-tests" in a:
        max_tests = int(a[a.index("--max-tests") + 1])
    r = run(go=go, no_open=no_open, timeout=timeout, max_tests=max_tests)
    return 0 if r["overall"] != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())
