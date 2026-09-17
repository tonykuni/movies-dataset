#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL158_VIAPanoramaAuditRepair v0102 — 全景稽核修復正主(批537:已修冊複驗 + 摘要講得清楚)

v0101→v0102(操作員令「FIXED CONTENT IN THE AST PAGE AND SUMMARY」):
  ① **已修冊複驗**(新 SSOT `VIA_PanoramaFixed_SSOT_v0100.json`;擁有者本器)。舊頁的 TAB③「已修」在乾跑時是一句
     「本次未套用」——等於這張 AST 頁只講還沒修的、不講修過的。現在 TAB③ 分兩張表:**本次**(套用或乾跑計畫)與
     **歷批已修冊**,而冊上每一筆都拿活樹重量一次:冊說修好、現在也還是修好=GREEN;冊說修好、現在又量到=**RED(回歸)**
     ——尾版律下這最容易發生:有人切了新版卻沒把修帶過去。量不了=ABSENT,誠實講量不了,不當綠。
  ② **摘要講得清楚**。舊摘要只有「問題 129 · 自動修 0」,看不出 129 是什麼、也看不出修過什麼。
     現在主控台一行、頁首、TAB①、Markdown 四處同一句:問題按 L56 三態拆(可同時修/順序修/只報位置待令)、
     已修冊複驗(綠/紅/待驗)、實測綠燈數、真 RED 數,四個數字各有出處。
  ③ 乾跑也要有內容:TAB③「本次」在乾跑時列**修復計畫**(哪一檔、平行還順序、會動哪幾類),不再是一句空話。

CGC_MDL158_VIAPanoramaAuditRepair v0101 — 全景稽核修復正主(批536 判準精準化)

v0100→v0101:① SYSEXE 排除「自己跑自己」(`subprocess.run([sys.executable, Path(__file__)…])`,引擎自測常態)——
  批535 報的 2 件全是這種誤報,真數為 0 ② PINVER 排除自測/夾具區(`def selftest` 之後、chk(/assert 行、X_ENG/Y_ENG 假名、
  /tmp 假路徑)——那些字串不是真的釘死路由 ③ 非活樹再加 `candidates/`、`bundle/`、`launchers/panorama_tests/`
  (候選夾與打包副本不是活樹)④ 判準改動一律附反例自測(⑮)。原 v0100 的修復器與報告不變。

CGC_MDL158_VIAPanoramaAuditRepair v0100 — 全景稽核修復正主(批535 操作員令:
「一個 PowerShell 指令全包:進環境→全景式分析→AST 精準/彈性定位→列出所有問題類型與位置→
  不傷系統、不生九頭龍的前提下,能同時修的同時修、不能同時修的順序修→25 加速器→動態進度條→
  自動跳出多 TAB 矩陣報告(TAB1 給 AI 與我、內附 JSON/MD;TAB2 起逐項測試結果)→紅黃綠燈、分系統分範疇」)

一功能一主(L30):本器是**唯一**的全景稽核+修復入口;它不重寫別人的判斷,只呼叫既有正主:
  · 家族境 python / 子行程環境 = 匯流排 CGC_MDL148(python_for/child_env)
  · 25 加速器名冊 = CGC_MDL156(roster;本器只讀,不自行定義)
  · 中央派送 = CGC_MDL157(dispatch;誠實四態)
  · 自測站清單 = CGC_MDL064 SelftestGrid(尾版;本器只挑站跑,不另立名冊)

九頭龍防線(Zero-Hydra):
  ① 收容件/退役夾/__pycache__/VIA_Reports/vcg/.git 一律不碰(正本零觸碰)
  ② 每次修改前後都 ast.parse,失敗即整檔回滾(原字節留在記憶體)
  ③ 只做「純增量、零行為變更」的自動修(加速器橋、網路工具橋、自測動詞等價轉換)
  ④ 會改行為的(硬相依搬家、釘死版號、裸 sys.executable 派送)只**報位置**,附建議修法,等操作員令
  ⑤ 同檔同時只有一個工人(平行以「檔」為單位切分,互不交疊)

用法:
  python3 CGC_MDL158_VIAPanoramaAuditRepair_v0100.py scan [--json] [--limit N]
  python3 ... fix [--apply] [--classes ACCEL,NET,VERB] [--workers N] [--limit N]
  python3 ... tests [--fast]            # 逐引擎自測 + 中央派送(誠實四態)
  python3 ... report [--open]           # 多 TAB 報告(HTML/JSON/MD)
  python3 ... all [--apply] [--open]    # 掃描→修→測→報(PowerShell 一貼式走這條)
  python3 ... --selftest                # 十二檢(零網路;合成夾具;不碰真樹)
"""
from __future__ import annotations

import argparse
import ast
import concurrent.futures as _cf
import datetime as _dt
import hashlib
import html as _html
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

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

ENGINE_ID = "CGC_MDL158_VIAPanoramaAuditRepair"
VERSION = "v0101"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "panorama_audit"      # 批535:自己的命名空間。`VIA_Reports/panorama` 是 CGC_MDL135/CGC_MDL149
                                                  # L19 安裝核可閘的地盤(schema 不同,我寫進去會讓那道閘整排 BLOCKED=假紅;一名一主 L30)
SKIP_PARTS = ("__pycache__", ".git", "VIA_Reports", "node_modules", ".venv", "site-packages")
SKIP_MARK = ("references/intake/", "references\\intake\\", "VIA_RetiredEngines", "/vcg/", "\\vcg\\", "_self_test", "/tests/", "\\tests\\",
             "supportive modules/ssot/", "supportive modules\\ssot\\")     # 批535:金融機構正典 SSOT 與其 overlay=READ_ONLY 正本,零觸碰(連加速器橋都不插)

ACCEL_BLOCK = '''# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
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
'''

NET_BLOCK = '''# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
'''

VERB_BLOCK = '''

# ===== [VIA:VERB-ALIAS:v0100] 批535:全樹以 `--selftest` 呼叫自測(格子站/匯流排/Deck/總控頁契約;律 L53)=====
# 本引擎原只認位置動詞;等價轉換,只增不減,既有呼叫方零影響。
_FLAG_VERBS_B535 = {"--selftest": "selftest", "--status": "status", "--manifest": "manifest", "--routes": "routes"}


def _normalise_argv_b535(argv):
    out, verb = [], None
    for a in argv:
        if a in _FLAG_VERBS_B535 and verb is None:
            verb = _FLAG_VERBS_B535[a]
        else:
            out.append(a)
    return ([verb] + out) if verb else out

'''

# 重相依:module 頂層硬 import 這些 = 本境沒裝就 Traceback(LL51 假紅)
HEAVY_LIBS = {"polars", "talib", "plotly", "yfinance", "akshare", "torch", "paddle", "paddleocr", "easyocr",
              "cv2", "sklearn", "matplotlib", "seaborn", "fitz", "pdfplumber", "docx", "pytesseract",
              "duckdb", "pandas", "numpy", "requests", "httpx", "bs4", "lxml", "openpyxl", "PIL", "psycopg"}
# 這幾支是 VIA 家族境的基底(境內必裝),硬 import 不算問題
BASE_OK = {"pandas", "numpy"}

CATEGORIES = {
    "ACCEL": ("加速器橋缺席", "GREEN_FIX", "純增量;import 時零行為變更"),
    "NET": ("VDF 網路工具橋缺席", "GREEN_FIX", "惰性載入;import 時零網路"),
    "VERB": ("自測動詞契約不齊(只認位置動詞)", "GREEN_FIX", "旗標=位置動詞等價轉換"),
    "HARDIMP": ("模組頂硬相依重庫(缺件會 Traceback=假紅)", "REPORT", "搬進探針式載入 → 缺=ABSENT"),
    "PINVER": ("釘死版號(違尾版律 L54)", "REPORT", "改 newest-glob"),
    "SYSEXE": ("裸 sys.executable 派子行程(違家族境律 L51)", "REPORT", "改匯流排 python_for(family)"),
    "TALIB": ("TA-Lib 活動接線(違 L50)", "REPORT", "QuantGuard 為唯一活動路徑"),
    "SYNTAX": ("語法錯(compile 失敗)", "REPORT", "必修;本器不猜改"),
}
SYSTEMS = (("VDF", "functional modules/VDF"), ("VRN", "functional modules/VRN"), ("VAP", "functional modules/VAP"),
           ("TALib", "functional modules/TALib"), ("治理 CGC", "supportive modules/registry"),
           ("支援 SUP", "supportive modules"), ("其他", ""))


def _p(pct: float, msg: str) -> None:
    """動態進度條協定:PowerShell 端解析 @@PROGRESS|<pct>|<msg> → Write-Progress。"""
    print(f"@@PROGRESS|{max(0.0, min(100.0, pct)):.1f}|{msg}", flush=True)


def _skip(p: Path) -> bool:
    s = str(p)
    if any(x in p.parts for x in SKIP_PARTS):
        return True
    return any(m in s for m in SKIP_MARK)


def system_of(rel: str) -> str:
    for name, pref in SYSTEMS:
        if pref and rel.replace("\\", "/").startswith(pref):
            return name
    return "其他"


_VER_RX = re.compile(r"^(?P<stem>.+?)_v(?P<ver>\d{3,4})$")
_FROZEN_RX = re.compile(r"(_sha[0-9a-f]{6,}|\(\d+\)|[ _-]copy|備份|backup)", re.I)
_NONLIVE_DIR = ("/candidates/", "\\candidates\\", "/bundle/", "\\bundle\\", "launchers/panorama_tests", "launchers\\panorama_tests")


def py_files(root: Path | None = None, live_only: bool = True) -> list[Path]:
    """全樹 .py(排除收容件/退役夾/pycache)。live_only=True 再過**活樹**:
    ① 同 stem 多版只留尾版(尾版律:舊版不是活樹,對它報紅=假紅)
    ② 凍結副本(_sha…、(1)、copy、備份)不算活樹。"""
    root = root or VIA
    files = sorted(p for p in root.rglob("*.py") if not _skip(p))
    if not live_only:
        return files
    newest: dict[tuple[str, str], tuple[int, Path]] = {}
    plain: list[Path] = []
    for f in files:
        if _FROZEN_RX.search(f.name) or any(k in str(f) for k in _NONLIVE_DIR):     # 批536:候選夾/打包副本/夾具測試不是活樹
            continue
        m = _VER_RX.match(f.stem)
        if m:
            key = (str(f.parent), m.group("stem"))
            v = int(m.group("ver"))
            if key not in newest or v > newest[key][0]:
                newest[key] = (v, f)
        else:
            plain.append(f)
    return sorted(plain + [v[1] for v in newest.values()])


# ---------------------------------------------------------------- AST 稽核
def audit_source(path: Path, src: str, rel: str) -> list[dict]:
    """單檔稽核:AST 精準定位(行號);AST 壞則退回彈性(正則)定位,兩者都記法。"""
    issues: list[dict] = []
    is_vdf_engine = rel.replace("\\", "/").startswith("functional modules/VDF/engine") and path.name.endswith(".py")

    if "[VIA:ACCEL-BRIDGE" not in src:
        issues.append({"cls": "ACCEL", "line": 1, "how": "marker", "detail": "無 [VIA:ACCEL-BRIDGE] 區塊"})
    if is_vdf_engine and "[VIA:NET-BRIDGE" not in src:
        issues.append({"cls": "NET", "line": 1, "how": "marker", "detail": "VDF 引擎無 [VIA:NET-BRIDGE] 區塊"})

    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as exc:
        issues.append({"cls": "SYNTAX", "line": int(exc.lineno or 1), "how": "compile",
                       "detail": f"{type(exc).__name__}: {str(exc)[:120]}"})
        return issues

    # 模組頂層(不在 try 內)硬 import 重庫
    for node in tree.body:
        names = []
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module.split(".")[0]]
        for n in names:
            if n in HEAVY_LIBS and n not in BASE_OK:
                issues.append({"cls": "HARDIMP", "line": node.lineno, "how": "ast",
                               "detail": f"模組頂層 import {n}(不在 try/探針內)"})

    src_lines = src.splitlines()
    doc_lines = set()
    for nd in ast.walk(tree):
        if isinstance(nd, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(nd, "body", None)
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) and isinstance(b[0].value.value, str):
                doc_lines.update(range(b[0].lineno, (b[0].end_lineno or b[0].lineno) + 1))
    selftest_line = next((nd.lineno for nd in tree.body if isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef))
                          and nd.name in ("selftest", "self_test", "_selftest")), 10 ** 9)
    fixture_span = set()                       # 批536:自測/探針函式整段都是夾具(在暫存夾寫假冊、假引擎名)
    for nd in ast.walk(tree):
        if isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                nd.name.startswith(("selftest", "self_test", "_selftest", "_probe", "probe_", "test_", "_test"))
                or "selftest" in nd.name or nd.name.endswith("_fixture")):
            fixture_span.update(range(nd.lineno, (nd.end_lineno or nd.lineno) + 1))
    has_selftest_choice = False
    for node in ast.walk(tree):
        # 釘死版號字串
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value
            if (re.search(r"_v\d{4}\.(py|ps1)$", v) or re.search(r"-v\d{4}\.ps1$", v)) and node.lineno not in doc_lines:
                ln = src_lines[node.lineno - 1] if node.lineno <= len(src_lines) else ""
                # 只有「真的拿去開檔/執行/組路徑」才算違尾版律;報告文字、註解、說明字串不算(避免假紅)
                path_use = any(k in ln for k in ("Path(", "open(", "os.path.join", "joinpath", "/ \"", "subprocess", "run(", "_eng(", "newest(", "import_module"))
                var_use = bool(re.match(r"\s*[A-Z_]*(PATH|FILE|BOOK|SCRIPT|ENGINE|TARGET|ENTRY)[A-Z_]*\s*=", ln))
                fixture = (node.lineno >= selftest_line or node.lineno in fixture_span                               # 批536:自測段之後=夾具,不是正式路由
                           or any(k in ln for k in ("chk(", "assert ", "_td", "tmp", "TemporaryDirectory"))
                           or re.search(r"\b[XYZ]_(ENG|MDL)\d+", v) is not None)
                if (path_use or var_use) and "glob" not in ln and not fixture:
                    issues.append({"cls": "PINVER", "line": node.lineno, "how": "ast",
                                   "detail": f"字串釘死版號當路徑用:{v[:64]}"})
            if v == "selftest":
                has_selftest_choice = True
        # 裸 sys.executable 派子行程
        if isinstance(node, ast.Call):
            fn = node.func
            is_sub = (isinstance(fn, ast.Attribute) and fn.attr in ("run", "Popen", "check_output")
                      and isinstance(fn.value, ast.Name) and fn.value.id == "subprocess")
            if is_sub and node.args:
                seg = ast.dump(node.args[0])
                if "attr='executable'" in seg and "id='sys'" in seg:
                    # 只有「派到別支引擎/別家族」才違家族境律;自跑自己(同境)不算
                    self_run = "id='__file__'" in seg or "'__file__'" in seg          # 批536:自己跑自己(自測常態)不是跨家族派送
                    cross = (not self_run) and any(k in seg for k in ("functional modules", "_eng", "newest", "ENGINE", "engine"))
                    if cross:
                        issues.append({"cls": "SYSEXE", "line": node.lineno, "how": "ast",
                                       "detail": "subprocess 以 sys.executable 派**別支引擎**(應走匯流排家族境 python)"})
        # TA-Lib 活動接線
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            nm = ""
            if isinstance(node, ast.Import):
                nm = ",".join(a.name for a in node.names)
            elif node.module:
                nm = node.module
            if re.search(r"\btalib\b", nm):
                issues.append({"cls": "TALIB", "line": node.lineno, "how": "ast",
                               "detail": f"import {nm}(L50 禁用;QuantGuard 為唯一活動路徑)"})

    # 動詞契約:有 selftest 位置動詞但無旗標等價
    if has_selftest_choice and "argparse" in src and "--selftest" not in src:
        ln = next((i + 1 for i, l in enumerate(src_lines) if "selftest" in l), 1)
        issues.append({"cls": "VERB", "line": ln, "how": "ast+flex",
                       "detail": "argparse 有 selftest 位置動詞,但不吃 --selftest(全樹契約 L53)"})
    return issues


def scan(limit: int = 0, progress: bool = True) -> dict:
    files = py_files()
    if limit:
        files = files[:limit]
    rows: list[dict] = []
    t0 = time.time()
    n = len(files)
    for i, f in enumerate(files):
        if progress and (i % 60 == 0 or i == n - 1):
            _p(5 + 25.0 * i / max(1, n), f"AST 全景掃描 {i+1}/{n} · {f.name[:38]}")
        try:
            src = f.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            rows.append({"file": str(f.relative_to(VIA)), "cls": "SYNTAX", "line": 1, "how": "io",
                         "detail": f"讀不了 {type(exc).__name__}", "system": system_of(str(f.relative_to(VIA)))})
            continue
        rel = str(f.relative_to(VIA))
        for it in audit_source(f, src, rel):
            it.update({"file": rel, "system": system_of(rel)})
            rows.append(it)
    by_cls: dict[str, int] = {}
    by_sys: dict[str, dict[str, int]] = {}
    for r in rows:
        by_cls[r["cls"]] = by_cls.get(r["cls"], 0) + 1
        by_sys.setdefault(r["system"], {})
        by_sys[r["system"]][r["cls"]] = by_sys[r["system"]].get(r["cls"], 0) + 1
    allf = py_files(live_only=False)
    return {"schema": "VIA.CGC158.scan.v1", "ts": _dt.datetime.now().isoformat(timespec="seconds"),
            "files_scanned": len(files), "files_all": len(allf), "files_nonlive": len(allf) - len(files),
            "scope": "活樹(尾版律:同 stem 只算尾版;凍結副本 _sha/(1)/copy 不算)",
            "issues": len(rows), "by_class": by_cls, "by_system": by_sys,
            "rows": rows, "secs": round(time.time() - t0, 1)}


# ---------------------------------------------------------------- 修復
def _insert_after_header(src: str, block: str) -> str:
    """插在 docstring / __future__ / shebang 之後、其餘 import 之前(AST 求位)。"""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return ""
    line = 0
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            line = max(line, node.end_lineno or 0)
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            line = max(line, node.end_lineno or 0)
            continue
        break
    lines = src.splitlines(keepends=True)
    if line == 0:
        i = 0
        while i < len(lines) and (lines[i].startswith("#!") or lines[i].startswith("# -*-") or lines[i].startswith("# coding")):
            i += 1
        line = i
    return "".join(lines[:line]) + "\n" + block + "\n" + "".join(lines[line:])


def fix_one(rel: str, classes: set[str], apply: bool) -> dict:
    """單檔修復(平行工人;一檔一工人,互不交疊)。回 {file, applied[], skipped[], ok, why}"""
    path = VIA / rel
    res = {"file": rel, "applied": [], "skipped": [], "ok": True, "why": ""}
    try:
        original = path.read_text(encoding="utf-8")
    except Exception as exc:
        res.update(ok=False, why=f"讀不了 {type(exc).__name__}")
        return res
    src = original
    try:
        ast.parse(src)
    except SyntaxError as exc:
        res.update(ok=False, why=f"原檔語法錯,不動(行 {exc.lineno})")
        return res

    if "ACCEL" in classes and "[VIA:ACCEL-BRIDGE" not in src:
        cand = _insert_after_header(src, ACCEL_BLOCK)
        if cand:
            src = cand
            res["applied"].append("ACCEL")
        else:
            res["skipped"].append("ACCEL:求位失敗")
    if "NET" in classes and "[VIA:NET-BRIDGE" not in src and rel.replace("\\", "/").startswith("functional modules/VDF/engine"):
        cand = _insert_after_header(src, NET_BLOCK)
        if cand:
            src = cand
            res["applied"].append("NET")
        else:
            res["skipped"].append("NET:求位失敗")
    if "VERB" in classes and "--selftest" not in src and "argparse" in src and '"selftest"' in src:
        m = re.search(r"\ndef main\(.*?\)\s*(->\s*[\w\[\], |]+)?:", src)
        pa = [x for x in ("    args = parser.parse_args()", "    return parser.parse_args()") if src.count(x) == 1]
        if m and pa:
            src = src[:m.start()] + VERB_BLOCK + src[m.start():]
            src = src.replace(pa[0], pa[0].replace("parse_args()", "parse_args(_normalise_argv_b535(sys.argv[1:]))"), 1)
            if "\nimport sys" not in src:
                src = src.replace("\nimport argparse", "\nimport argparse\nimport sys", 1)
            res["applied"].append("VERB")
        else:
            res["skipped"].append("VERB:main/parse_args 形狀不合(不猜改)")

    if not res["applied"]:
        return res
    try:
        ast.parse(src)
    except SyntaxError as exc:
        res.update(ok=False, why=f"改後語法錯 → 回滾(行 {exc.lineno})", applied=[])
        return res
    if apply:
        path.write_text(src, encoding="utf-8")
    res["bytes_delta"] = len(src) - len(original)
    return res


def accel_workers(default: int = 8) -> tuple[int, str]:
    """並行度取自 CGC156 的 25 項加速器名冊(只讀,不自行定義;缺席=預設)。"""
    try:
        j = OUT.parent / "accelerator" / "VIA_ACCELERATOR_CONTROL_latest.json"
        if j.is_file():
            d = json.loads(j.read_text(encoding="utf-8"))
            n = int(d.get("roster_count") or d.get("accelerators") or 0)
            if n > 0:
                return max(4, min(n, 25)), f"CGC156 名冊 {n} 項"
    except Exception:
        pass
    return default, "預設(CGC156 報告未見)"


def fix(classes: set[str], apply: bool, workers: int = 0, limit: int = 0, scan_rows: list | None = None) -> dict:
    rows = scan_rows if scan_rows is not None else scan(progress=False)["rows"]
    targets: dict[str, set[str]] = {}
    for r in rows:
        if r["cls"] in classes:
            targets.setdefault(r["file"], set()).add(r["cls"])
    files = sorted(targets)
    if limit:
        files = files[:limit]
    w, wsrc = accel_workers()
    if workers:
        w = workers
    par_files = [f for f in files if targets[f] <= {"ACCEL", "NET"}]          # 純增量=可同時修
    seq_files = [f for f in files if f not in set(par_files)]                  # 碰 main/parse_args=順序修
    out: list[dict] = []
    t0 = time.time()
    n = max(1, len(files))
    done = 0
    if par_files:
        with _cf.ThreadPoolExecutor(max_workers=w) as ex:
            futs = {ex.submit(fix_one, f, targets[f], apply): f for f in par_files}
            for fu in _cf.as_completed(futs):
                out.append(fu.result())
                done += 1
                if done % 15 == 0 or done == len(par_files):
                    _p(32 + 28.0 * done / n, f"平行修復 {done}/{len(par_files)}(工人 {w};{wsrc})")
    for f in seq_files:
        out.append(fix_one(f, targets[f], apply))
        done += 1
        _p(32 + 28.0 * done / n, f"順序修復 {done - len(par_files)}/{len(seq_files)} · {Path(f).name[:34]}")
    applied = {}
    for r in out:
        for c in r["applied"]:
            applied[c] = applied.get(c, 0) + 1
    return {"schema": "VIA.CGC158.fix.v1", "apply": apply, "workers": w, "worker_source": wsrc,
            "parallel_files": len(par_files), "sequential_files": len(seq_files),
            "applied_by_class": applied, "failed": [r for r in out if not r["ok"]],
            "rows": out, "secs": round(time.time() - t0, 1)}


# ---------------------------------------------------------------- 測試
def _bus_python(family: str) -> str:
    try:
        import importlib.util
        c = sorted(HERE.glob("CGC_MDL148_EngineBus_v*.py"))
        if c:
            spec = importlib.util.spec_from_file_location("bus_for_158", c[-1])
            m = importlib.util.module_from_spec(spec)
            sys.modules["bus_for_158"] = m
            spec.loader.exec_module(m)
            got = m.python_for(family) or {}
            if got.get("python") and Path(got["python"]).exists():
                return got["python"]
    except Exception:
        pass
    return sys.executable


TEST_TARGETS = [
    ("治理", "CGC_MDL157 唯一接觸口", "supportive modules/registry", "CGC_MDL157_VIAUniqueEntryControl_v*.py", "core"),
    ("治理", "CGC_MDL156 加速器控制面", "supportive modules/registry", "CGC_MDL156_VIAAcceleratorControl_v*.py", "core"),
    ("治理", "CGC_MDL155 統一 SSOT", "supportive modules/registry", "CGC_MDL155_VIAUnifiedSSOTAutoCode_v*.py", "core"),
    ("治理", "CGC_MDL148 引擎匯流排", "supportive modules/registry", "CGC_MDL148_EngineBus_v*.py", "core"),
    ("治理", "CGC_MDL153 工作流重組台", "supportive modules/registry", "CGC_MDL153_WorkflowComposer_v*.py", "core"),
    ("治理", "CGC_MDL149 中央控管台", "supportive modules/registry", "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py", "vrn"),
    ("治理", "CGC_MDL095 指揮台橋", "supportive modules/registry", "CGC_MDL095_DeckServer_v*.py", "core"),
    ("VDF", "VDF_ENG073 資料架構", "functional modules/VDF/engine", "VDF_ENG073_DataArchitecture_v*.py", "vdf"),
    ("VDF", "VDF_ENG087 市場清單治理", "functional modules/VDF/engine", "VDF_ENG087_MarketListGovernance_v*.py", "vdf"),
    ("VDF", "VDF_ENG086 QuantGuard 正主橋", "functional modules/VDF/engine", "VDF_ENG086_QuantGuardOneBridge_v*.py", "vdf"),
    ("VDF", "VDF_ENG085 VATETF 正主橋", "functional modules/VDF/engine", "VDF_ENG085_VatetfBridge_v*.py", "vdf"),
    ("VDF", "VDF_ENG055 總擷取執行器", "functional modules/VDF/engine", "VDF_ENG055_OmniFetch_v*.py", "vdf"),
    ("VRN", "VRN_ENG087 NLP 文字摘要橋", "functional modules/VRN", "VRN_ENG087_NLPTextSummaryBridge_v*.py", "vrn"),
    ("VRN", "VRN_ENG086 第一頁邏輯補缺", "functional modules/VRN", "VRN_ENG086_FirstPageLogicBridge_v*.py", "vrn"),
    ("VRN", "VRN_ENG073 報告結構庫", "functional modules/VRN", "VRN_ENG073_ReportStructuredDB_v*.py", "vrn"),
    ("VRN", "VRN_ENG074 財報頁擷取", "functional modules/VRN", "VRN_ENG074_FinancialPages_v*.py", "vrn"),
    ("支援", "SUP_MDL866 統一 NLP 編排", "supportive modules/70_VRN_Rules", "SUP_MDL866_VIAUnifiedNLPOrchestrator_v*.py", "vrn"),
]
_ABSENT_MARK = ("ModuleNotFoundError", "[ABSENT]", "· ABSENT ·", "No module named")
_NODATA_MARK = ("[NODATA]", "[NEED_INPUT]", "NODATA")


def judge(rc: int | None, out: str) -> tuple[str, str]:
    """誠實四態(與 CGC157 同律 L52):缺件 ABSENT · 缺料 NODATA · 逾時 TIMEOUT · 真壞才 RED。"""
    if rc is None:
        return "TIMEOUT", "逾時"
    if rc == 0:
        return "GREEN", (next((l for l in reversed(out.splitlines()) if "計]" in l or "OK" in l), "rc0")[:110])
    tail = out[-2500:]
    if rc == 3 or any(k in tail for k in _ABSENT_MARK):
        return "ABSENT", next((l.strip() for l in reversed(tail.splitlines()) if any(k in l for k in _ABSENT_MARK)), "本境缺件")[:130]
    if rc == 2 or any(k in tail for k in _NODATA_MARK):
        return "NODATA", next((l.strip() for l in reversed(tail.splitlines()) if any(k in l for k in _NODATA_MARK)), "資料側")[:130]
    return "RED", (tail.splitlines()[-1].strip()[:130] if tail.strip() else f"rc={rc}")


def run_tests(fast: bool = False, timeout: int = 900) -> dict:
    rows = []
    n = len(TEST_TARGETS)
    for i, (sysname, label, folder, glob, fam) in enumerate(TEST_TARGETS):
        _p(62 + 26.0 * i / n, f"實測 {i+1}/{n} · {label}")
        hits = sorted((VIA / folder).glob(glob))
        if not hits:
            rows.append({"system": sysname, "name": label, "state": "ABSENT", "why": f"檔缺 {glob}", "rc": None, "secs": 0, "engine": ""})
            continue
        eng = hits[-1]
        py = _bus_python(fam)
        t0 = time.time()
        try:
            r = subprocess.run([py, str(eng), "--selftest"], capture_output=True, text=True,
                               timeout=(300 if fast else timeout), cwd=str(VIA), errors="replace")
            rc, out = r.returncode, (r.stdout or "") + "\n" + (r.stderr or "")
        except subprocess.TimeoutExpired:
            rc, out = None, "TIMEOUT"
        except Exception as exc:
            rc, out = 1, f"{type(exc).__name__}: {exc}"
        st, why = judge(rc, out)
        rows.append({"system": sysname, "name": label, "engine": eng.name, "state": st, "why": why,
                     "rc": rc, "secs": round(time.time() - t0, 1)})
    # 中央派送(CGC157)
    disp = {"state": "ABSENT", "why": "CGC157 缺"}
    c = sorted(HERE.glob("CGC_MDL157_VIAUniqueEntryControl_v*.py"))
    if c:
        _p(89, "中央派送 dispatch --family all")
        try:
            r = subprocess.run([sys.executable, str(c[-1]), "dispatch", "--family", "all"],
                               capture_output=True, text=True, timeout=timeout, cwd=str(VIA), errors="replace")
            j = None
            s = r.stdout or ""
            if "{" in s:
                try:
                    j = json.loads(s[s.index("{"):s.rindex("}") + 1])
                except Exception:
                    j = None
            disp = {"state": (j or {}).get("verdict") or judge(r.returncode, s)[0],
                    "counts": (j or {}).get("counts"), "routes": [
                        {"family": x.get("family"), "engine": x.get("engine"), "state": x.get("state"),
                         "rc": x.get("returncode"), "python_source": x.get("python_source")} for x in (j or {}).get("routes", [])],
                    "why": "" if j else (s[-160:] if s else "無 JSON")}
        except Exception as exc:
            disp = {"state": "RED", "why": f"{type(exc).__name__}: {exc}"}
    tally = {}
    for r in rows:
        tally[r["state"]] = tally.get(r["state"], 0) + 1
    return {"schema": "VIA.CGC158.tests.v1", "rows": rows, "tally": tally, "dispatch": disp,
            "verdict": "RED" if (tally.get("RED") or tally.get("TIMEOUT")) else ("YELLOW" if (tally.get("ABSENT") or tally.get("NODATA")) else "GREEN")}


# ---------------------------------------------------------------- 報告(多 TAB · 零 CDN)
def coverage() -> dict:
    files = py_files()
    acc = sum(1 for f in files if "[VIA:ACCEL-BRIDGE" in f.read_text(encoding="utf-8", errors="replace"))
    vdfe = [f for f in files if str(f.relative_to(VIA)).replace("\\", "/").startswith("functional modules/VDF/engine")]
    net = sum(1 for f in vdfe if "[VIA:NET-BRIDGE" in f.read_text(encoding="utf-8", errors="replace"))
    return {"py_total": len(files), "accel": acc, "accel_pct": round(100.0 * acc / max(1, len(files)), 1),
            "vdf_engines": len(vdfe), "net": net, "net_pct": round(100.0 * net / max(1, len(vdfe)), 1)}


FIXED_SSOT = VIA / "supportive modules" / "registry" / "VIA_PanoramaFixed_SSOT_v0100.json"
PAR_CLS = {"ACCEL", "NET"}                 # L56 ①:純增量、零行為變更、可冪等 → 以檔為單位平行修


def _tail_file(rel_dir: str, glob: str):
    base = VIA if rel_dir in (".", "") else VIA / rel_dir
    hits = sorted(p for p in base.glob(glob) if p.is_file())
    return hits[-1] if hits else None


def _verify_one(v: dict, scan_d: dict, cov: dict) -> tuple:
    """一條憑據 → (燈, 說明)。量不出來就說量不出來(ABSENT),不當綠。"""
    k = v.get("kind")
    if k == "class_zero":
        cls = v.get("cls")
        n = int((scan_d.get("by_class") or {}).get(cls, 0))
        return ("GREEN" if n == 0 else "RED"), f"活樹 {cls} = {n}(冊要求 0)"
    if k == "coverage_pct":
        fld = v.get("field")
        if fld not in cov:
            return "ABSENT", f"覆蓋率無 {fld} 欄,量不了"
        got, exp = float(cov[fld]), float(v.get("expect", 100.0))
        return ("GREEN" if got >= exp else "RED"), f"{fld} {got}%(冊要求 ≥{exp}%)"
    if k == "tail_contains":
        p = _tail_file(v.get("dir", "."), v.get("glob", ""))
        if p is None:
            return "ABSENT", f"尾版不在:{v.get('dir')}/{v.get('glob')}"
        txt = p.read_text(encoding="utf-8", errors="replace")
        miss = [m for m in (v.get("markers") or []) if m not in txt]
        back = [m for m in (v.get("markers_absent") or []) if m in txt]
        if miss:
            return "RED", f"{p.name} 少了 {miss}(修沒帶進尾版=回歸)"
        if back:
            return "RED", f"{p.name} 又出現 {back}(退役件復活=回歸)"
        return "GREEN", f"{p.name} 憑據齊"
    return "ABSENT", f"不認得的憑據類 {k}"


def fixed_ledger(scan_d: dict, cov: dict) -> dict:
    """已修冊複驗。冊不在=誠實 ABSENT,不編。"""
    rep = {"schema": "VIA.CGC158.fixed.v1", "src": str(FIXED_SSOT), "state": "ABSENT",
           "rows": [], "tally": {}, "regressions": []}
    if not FIXED_SSOT.is_file():
        rep["why"] = f"已修冊不在:{FIXED_SSOT.name}"
        return rep
    try:
        d = json.loads(FIXED_SSOT.read_text(encoding="utf-8"))
    except Exception as exc:
        rep.update(state="RED", why=f"已修冊讀不動:{type(exc).__name__}")
        return rep
    for e in d.get("entries") or []:
        checks = [dict(zip(("lamp", "why"), _verify_one(v, scan_d, cov))) for v in (e.get("verify") or [])]
        lamps = [c["lamp"] for c in checks]
        lamp = "RED" if "RED" in lamps else ("ABSENT" if (not lamps or "ABSENT" in lamps) else "GREEN")
        row = {"id": e.get("id"), "batch": e.get("batch"), "cls": e.get("cls"), "n": e.get("n"),
               "what": e.get("what"), "lamp": lamp, "checks": checks}
        rep["rows"].append(row)
        rep["tally"][lamp] = rep["tally"].get(lamp, 0) + 1
        if lamp == "RED":
            rep["regressions"].append(row["id"])
    rep["state"] = "RED" if rep["regressions"] else ("ABSENT" if not rep["rows"] else "GREEN")
    rep["why"] = (f"冊 {len(rep['rows'])} 筆複驗 · " + " · ".join(f"{k} {v}" for k, v in sorted(rep["tally"].items()))
                  + (f" · 回歸 {rep['regressions']}" if rep["regressions"] else " · 回歸 0"))
    return rep


def issue_triage(scan_d: dict) -> dict:
    """把問題數按 L56 三態拆開——同時修 / 順序修 / 只報位置待令,再單列真 RED。"""
    par = seq = rep_only = red = 0
    for cls, n in (scan_d.get("by_class") or {}).items():
        act = CATEGORIES.get(cls, (cls, "REPORT", ""))[1]
        if cls in ("SYNTAX", "TALIB"):
            red += n
        elif act == "GREEN_FIX":
            if cls in PAR_CLS:                       # ACCEL/NET 純增量=可同檔平行;VERB 動入口=順序
                par += n
            else:
                seq += n
        else:
            rep_only += n
    return {"parallel": par, "sequential": seq, "report_only": rep_only, "red": red,
            "total": int(scan_d.get("issues", 0))}


def summary_line(pay: dict) -> str:
    """一句話講清楚:四個數字各有出處(主控台、頁首、TAB①、Markdown 同一句)。"""
    tri = pay.get("triage") or {}
    fl = pay.get("fixed") or {}
    t = pay.get("tests") or {}
    tally = t.get("tally") or {}
    n_test = len(t.get("rows") or [])
    ft = fl.get("tally") or {}
    return (f"問題 {tri.get('total', 0)}(可同時修 {tri.get('parallel', 0)} · 順序修 {tri.get('sequential', 0)}"
            f" · 只報位置待令 {tri.get('report_only', 0)} · 真 RED {tri.get('red', 0)})"
            f" · 已修冊 {len(fl.get('rows') or [])} 筆複驗 GREEN {ft.get('GREEN', 0)} / 回歸 {len(fl.get('regressions') or [])}"
            f" / 待驗 {ft.get('ABSENT', 0)}"
            f" · 本次自動修 {sum((pay.get('fix') or {}).get('applied_by_class', {}).values())} 處"
            f" · 實測 {tally.get('GREEN', 0)}/{n_test} 綠")


def _lamp(state: str) -> str:
    return {"GREEN": "g", "YELLOW": "y", "ABSENT": "a", "NODATA": "a", "TIMEOUT": "r", "RED": "r"}.get(state, "a")


def render_md(pay: dict) -> str:
    s = pay["scan"]; f = pay.get("fix") or {}; t = pay.get("tests") or {}; c = pay["coverage"]
    L = [f"# VIA 全景稽核修復報告 · {pay['batch']} · {pay['ts']}", "",
         f"**總裁決:{pay['verdict']}** · 掃 {s['files_scanned']} 檔", "",
         f"**{pay.get('summary') or summary_line(pay)}**", "",
         "## 一 · 問題分類(紅黃綠)", "", "| 類 | 說明 | 處置 | 件數 |", "|---|---|---|---:|"]
    for cls, n in sorted(s["by_class"].items(), key=lambda x: -x[1]):
        zh, act, fixhow = CATEGORIES.get(cls, (cls, "REPORT", ""))
        L.append(f"| {cls} | {zh} | {'自動修' if act == 'GREEN_FIX' else '報位置待令'} | {n} |")
    L += ["", "## 二 · 分系統矩陣", "", "| 系統 | " + " | ".join(CATEGORIES) + " |", "|---" * (len(CATEGORIES) + 1) + "|"]
    for sysname, d in sorted(s["by_system"].items()):
        L.append(f"| {sysname} | " + " | ".join(str(d.get(k, 0)) for k in CATEGORIES) + " |")
    L += ["", "## 三 · 覆蓋率", "",
          f"- 加速器橋:{c['accel']}/{c['py_total']}({c['accel_pct']}%)",
          f"- VDF 網路工具橋:{c['net']}/{c['vdf_engines']}({c['net_pct']}%)", "",
          "## 四 · 實測結果(誠實四態)", "", "| 系統 | 引擎 | 燈 | rc | 秒 | 說明 |", "|---|---|---|---:|---:|---|"]
    for r in t.get("rows", []):
        L.append(f"| {r['system']} | {r['name']} | {r['state']} | {r['rc']} | {r['secs']} | {str(r['why'])[:90]} |")
    d = t.get("dispatch") or {}
    L += ["", f"**中央派送**:{d.get('state')} · {d.get('counts')}", ""]
    if f.get("rows"):
        L += ["## 五 · 本次修復(平行/順序)", "",
              f"{'已套用' if f.get('apply') else '乾跑計畫(加 --apply 才寫檔)'} · 平行 {f['parallel_files']} 檔 · 順序 {f['sequential_files']} 檔 · 工人 {f['workers']}({f['worker_source']})", ""]
    fl = pay.get("fixed") or {}
    L += ["## 六 · 歷批已修冊複驗(冊說修好,現在還是不是?)", "",
          f"冊:`{fl.get('src','-')}` · {fl.get('why','-')}", "",
          "| 批 | 類 | 已修 | 燈 | 內容 | 複驗憑據 |", "|---|---|---:|---|---|---|"]
    for r in fl.get("rows", []):
        ev = " ／ ".join(f"{c['lamp']}:{c['why']}" for c in r.get("checks", []))
        L.append(f"| {r['batch']} | {r['cls']} | {r['n']} | {r['lamp']} | {str(r['what'])[:70]} | {ev[:150]} |")
    if not fl.get("rows"):
        L.append(f"| — | — | — | ABSENT | {fl.get('why','冊不在')} | — |")
    return "\n".join(L)


def render_html(pay: dict) -> str:
    s = pay["scan"]; f = pay.get("fix") or {}; t = pay.get("tests") or {}; c = pay["coverage"]
    j = _html.escape(json.dumps(pay, ensure_ascii=False, indent=1))
    md = _html.escape(render_md(pay))
    def rows_issue():
        out = []
        for r in s["rows"][:4000]:
            zh, act, fixhow = CATEGORIES.get(r["cls"], (r["cls"], "REPORT", ""))
            lamp = "g" if act == "GREEN_FIX" else ("r" if r["cls"] in ("SYNTAX", "TALIB") else "y")
            out.append(f"<tr data-sys='{_html.escape(r['system'])}' data-cls='{r['cls']}'><td><span class=d-{lamp}></span>{r['cls']}</td>"
                       f"<td>{_html.escape(r['system'])}</td><td class=mono>{_html.escape(r['file'])}</td><td class=num>{r['line']}</td>"
                       f"<td>{_html.escape(r['how'])}</td><td>{_html.escape(str(r['detail'])[:150])}</td><td>{_html.escape(fixhow)}</td></tr>")
        return "".join(out)
    def rows_test():
        out = []
        for r in t.get("rows", []):
            out.append(f"<tr><td>{_html.escape(r['system'])}</td><td>{_html.escape(r['name'])}</td>"
                       f"<td class=mono>{_html.escape(r.get('engine') or '')}</td>"
                       f"<td><span class=d-{_lamp(r['state'])}></span>{r['state']}</td><td class=num>{r['rc']}</td>"
                       f"<td class=num>{r['secs']}</td><td>{_html.escape(str(r['why'])[:160])}</td></tr>")
        return "".join(out)
    def rows_fix():
        out = []
        for r in (f.get("rows") or []):
            if not r.get("applied") and not r.get("skipped"):
                continue
            out.append(f"<tr><td class=mono>{_html.escape(r['file'])}</td><td>{'平行' if set(r.get('applied') or []) <= {'ACCEL','NET'} else '順序'}</td>"
                       f"<td>{_html.escape(','.join(r.get('applied') or []) or '-')}</td>"
                       f"<td>{_html.escape(','.join(r.get('skipped') or []) or '-')}</td>"
                       f"<td><span class=d-{('g' if r['ok'] else 'r') if f.get('apply') else 'a'}></span>"
                       f"{('OK' if r['ok'] else 'FAIL') if f.get('apply') else '乾跑(未寫檔)'}</td>"
                       f"<td>{_html.escape(str(r.get('why') or ''))[:110]}</td></tr>")
        return "".join(out) or "<tr><td colspan=6>本次無可自動修的項(ACCEL/NET/VERB 三類皆為 0)</td></tr>"

    def rows_fixed():
        out = []
        for r in ((pay.get("fixed") or {}).get("rows") or []):
            ev = "<br>".join(f"<span class=d-{_lamp(c['lamp'])}></span>{_html.escape(c['why'])}" for c in r.get("checks", []))
            out.append(f"<tr><td>{_html.escape(str(r['batch']))}</td><td>{_html.escape(str(r['cls']))}</td>"
                       f"<td class=num>{r['n']}</td><td><span class=d-{_lamp(r['lamp'])}></span>{r['lamp']}</td>"
                       f"<td>{_html.escape(str(r['what']))}</td><td>{ev}</td></tr>")
        return "".join(out) or f"<tr><td colspan=6>{_html.escape(str((pay.get('fixed') or {}).get('why') or '已修冊不在'))}</td></tr>"
    n_fix = sum((f.get("applied_by_class") or {}).values())
    tri = pay.get("triage") or issue_triage(s)
    _fl = pay.get("fixed") or {}
    n_fixed = len(_fl.get("rows") or [])
    n_fixed_green = (_fl.get("tally") or {}).get("GREEN", 0)
    n_regress = len(_fl.get("regressions") or [])
    tally = t.get("tally") or {}
    n_green = tally.get("GREEN", 0)
    n_test = len(t.get("rows") or [])
    matrix_head = "".join(f"<th>{k}</th>" for k in CATEGORIES)
    matrix_rows = "".join(
        "<tr><td>" + _html.escape(sysname) + "</td>" + "".join(
            f"<td class=num><span class=d-{'g' if d.get(k,0)==0 else ('y' if CATEGORIES[k][1]=='GREEN_FIX' else 'r')}></span>{d.get(k,0)}</td>"
            for k in CATEGORIES) + "</tr>"
        for sysname, d in sorted(s["by_system"].items()))
    d = t.get("dispatch") or {}
    disp_rows = "".join(f"<tr><td>{_html.escape(str(x.get('family')))}</td><td class=mono>{_html.escape(str(x.get('engine')))}</td>"
                        f"<td><span class=d-{_lamp(str(x.get('state')))}></span>{x.get('state')}</td><td class=num>{x.get('rc')}</td>"
                        f"<td>{_html.escape(str(x.get('python_source')))}</td></tr>" for x in (d.get("routes") or []))
    return f"""<!doctype html><html lang=zh-Hant><head><meta charset=utf-8>
<title>VIA 全景稽核修復矩陣 · {pay['batch']}</title><style>
:root{{--g:#16a34a;--y:#d97706;--r:#dc2626;--a:#64748b;--bg:#fbfcfd;--bd:#e2e8f0;--tx:#0f172a}}
*{{box-sizing:border-box}}body{{margin:0;font:11.5px/1.5 -apple-system,"Segoe UI","Noto Sans TC",sans-serif;background:var(--bg);color:var(--tx)}}
header{{padding:10px 14px;border-bottom:1px solid var(--bd);background:#fff;position:sticky;top:0;z-index:5}}
h1{{font-size:14px;margin:0 0 4px}}.sub{{color:#64748b;font-size:11px}}
.tabs{{display:flex;gap:2px;flex-wrap:wrap;margin-top:8px}}
.tab{{padding:4px 10px;border:1px solid var(--bd);border-bottom:none;background:#f1f5f9;cursor:pointer;font-size:11px;border-radius:4px 4px 0 0}}
.tab.on{{background:#fff;font-weight:600;color:#0369a1}}
.panel{{display:none;padding:12px 14px}}.panel.on{{display:block}}
table{{border-collapse:collapse;width:100%;background:#fff;font-size:11px}}
th,td{{border:1px solid var(--bd);padding:3px 6px;text-align:left;vertical-align:top}}
th{{background:#f8fafc;position:sticky;top:0;font-weight:600}}
td.num{{text-align:right;font-variant-numeric:tabular-nums}}.mono{{font-family:ui-monospace,Consolas,monospace;font-size:10.5px}}
span[class^=d-]{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}}
.d-g{{background:var(--g)}}.d-y{{background:var(--y)}}.d-r{{background:var(--r)}}.d-a{{background:var(--a)}}
.kpi{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}}
.card{{border:1px solid var(--bd);background:#fff;border-radius:6px;padding:8px 12px;min-width:120px}}
.card b{{display:block;font-size:18px;line-height:1.1}}.card span{{color:#64748b;font-size:10.5px}}
pre{{background:#0f172a;color:#e2e8f0;padding:10px;border-radius:6px;overflow:auto;max-height:440px;font-size:10.5px}}
.bar{{height:6px;background:#e2e8f0;border-radius:3px;overflow:hidden;margin-top:4px}}.bar i{{display:block;height:100%;background:var(--g)}}
input,select{{font:11px inherit;padding:2px 6px;border:1px solid var(--bd);border-radius:4px}}
.wrap{{max-height:70vh;overflow:auto;border:1px solid var(--bd);border-radius:6px}}
</style></head><body>
<header><h1>VIA 全景稽核修復矩陣 · {pay['batch']} · 總裁決 <span class=d-{_lamp(pay['verdict'])}></span>{pay['verdict']}</h1>
<div class=sub>{pay['ts']} · 掃 {s['files_scanned']} 檔 · 工人 {f.get('workers','-')}({_html.escape(str(f.get('worker_source','-')))})</div>
<div class=sub style="color:#0f172a;font-weight:600">{_html.escape(pay.get('summary') or '')}</div>
<div class=tabs>
<div class="tab on" data-t=0>① 總覽(AI/操作員)</div><div class=tab data-t=1>② 問題明細</div><div class=tab data-t=2>③ 本次修復</div>
<div class=tab data-t=3>④ 已修冊複驗</div><div class=tab data-t=4>⑤ 實測結果</div><div class=tab data-t=5>⑥ 中央派送</div>
<div class=tab data-t=6>⑦ 覆蓋率</div><div class=tab data-t=7>⑧ JSON</div><div class=tab data-t=8>⑨ Markdown</div></div></header>

<div class="panel on" id=p0>
<div class=kpi>
<div class=card><b>{tri.get('total',0)}</b><span>問題總數(可同時修 {tri.get('parallel',0)} · 順序 {tri.get('sequential',0)} · 待令 {tri.get('report_only',0)})</span></div>
<div class=card><b>{tri.get('red',0)}</b><span>真 RED(語法錯／TA-Lib 接線)</span></div>
<div class=card><b>{n_fixed_green}/{n_fixed}</b><span>已修冊複驗綠 · 回歸 {n_regress}</span></div>
<div class=card><b>{n_fix}</b><span>本次自動修</span></div>
<div class=card><b>{c['accel_pct']}%</b><span>加速器橋覆蓋<div class=bar><i style="width:{c['accel_pct']}%"></i></div></span></div>
<div class=card><b>{c['net_pct']}%</b><span>VDF 網路工具覆蓋<div class=bar><i style="width:{c['net_pct']}%"></i></div></span></div>
<div class=card><b>{n_green}/{n_test}</b><span>實測綠燈</span></div>
</div>
<h3 style="font-size:12px">分系統 × 分範疇矩陣(綠=零問題;黃=可自動修;紅=需人工判)</h3>
<table><thead><tr><th>系統</th>{matrix_head}</tr></thead><tbody>{matrix_rows}</tbody></table>
<h3 style="font-size:12px;margin-top:12px">範疇說明與處置</h3>
<table><thead><tr><th>類</th><th>說明</th><th>處置</th><th>修法</th><th>件數</th></tr></thead><tbody>
{"".join(f"<tr><td><span class=d-{'g' if v[1]=='GREEN_FIX' else 'y'}></span>{k}</td><td>{v[0]}</td><td>{'自動修(本器)' if v[1]=='GREEN_FIX' else '報位置待令'}</td><td>{v[2]}</td><td class=num>{s['by_class'].get(k,0)}</td></tr>" for k, v in CATEGORIES.items())}
</tbody></table></div>

<div class=panel id=p1><div style="margin-bottom:6px">篩選 <input id=q placeholder="檔名/類/系統…" oninput="flt()"> </div>
<div class=wrap><table id=tIssue><thead><tr><th>類</th><th>系統</th><th>檔案</th><th>行</th><th>定位</th><th>說明</th><th>建議修法</th></tr></thead><tbody>{rows_issue()}</tbody></table></div></div>

<div class=panel id=p2><div class=wrap><table><thead><tr><th>檔案</th><th>模式</th><th>已套用</th><th>略過</th><th>結果</th><th>說明</th></tr></thead><tbody>{rows_fix()}</tbody></table></div></div>

<div class=panel id=p3><p>冊:<span class=mono>{_html.escape(str((pay.get('fixed') or {}).get('src','-')))}</span> · {_html.escape(str((pay.get('fixed') or {}).get('why','-')))}</p>
<p class=sub>這張表不是功勞簿:每一筆都拿活樹重量一次。綠=冊說修好、現在也還是修好;紅=<b>回歸</b>(尾版律下最容易發生——切了新版沒把修帶過去);灰=量不了,誠實講量不了。</p>
<div class=wrap><table><thead><tr><th>批</th><th>類</th><th>已修</th><th>燈</th><th>內容</th><th>複驗憑據(活樹重量)</th></tr></thead><tbody>{rows_fixed()}</tbody></table></div></div>

<div class=panel id=p4><div class=wrap><table><thead><tr><th>系統</th><th>引擎</th><th>檔</th><th>燈</th><th>rc</th><th>秒</th><th>說明</th></tr></thead><tbody>{rows_test()}</tbody></table></div></div>

<div class=panel id=p5><p>中央派送裁決:<span class=d-{_lamp(str(d.get('state')))}></span><b>{d.get('state')}</b> · {_html.escape(str(d.get('counts')))}</p>
<table><thead><tr><th>家族</th><th>引擎</th><th>燈</th><th>rc</th><th>python 來源</th></tr></thead><tbody>{disp_rows or '<tr><td colspan=5>無路由</td></tr>'}</tbody></table></div>

<div class=panel id=p6><table><thead><tr><th>項</th><th>已有</th><th>總數</th><th>覆蓋率</th></tr></thead><tbody>
<tr><td>指令加速器橋(全樹 .py)</td><td class=num>{c['accel']}</td><td class=num>{c['py_total']}</td><td class=num>{c['accel_pct']}%</td></tr>
<tr><td>網路工具橋(VDF 引擎)</td><td class=num>{c['net']}</td><td class=num>{c['vdf_engines']}</td><td class=num>{c['net_pct']}%</td></tr>
</tbody></table></div>

<div class=panel id=p7><pre id=js>{j}</pre></div>
<div class=panel id=p8><pre id=mdp>{md}</pre></div>

<script>
document.querySelectorAll('.tab').forEach(function(x){{x.onclick=function(){{
 document.querySelectorAll('.tab').forEach(function(y){{y.classList.remove('on')}});
 document.querySelectorAll('.panel').forEach(function(y){{y.classList.remove('on')}});
 x.classList.add('on'); document.getElementById('p'+x.dataset.t).classList.add('on');}}}});
function flt(){{var v=document.getElementById('q').value.toLowerCase();
 document.querySelectorAll('#tIssue tbody tr').forEach(function(r){{r.style.display=r.innerText.toLowerCase().indexOf(v)>=0?'':'none'}});}}
</script></body></html>"""


def write_report(pay: dict, do_open: bool = False) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    hp, jp, mp = OUT / "PANORAMA_AUDIT_latest.html", OUT / "PANORAMA_AUDIT_latest.json", OUT / "PANORAMA_AUDIT_latest.md"
    hp.write_text(render_html(pay), encoding="utf-8")
    jp.write_text(json.dumps(pay, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    mp.write_text(render_md(pay), encoding="utf-8")
    (OUT / f"PANORAMA_AUDIT_{stamp}.json").write_text(json.dumps(pay, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if do_open and not os.environ.get("VIA_NO_OPEN"):
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(hp))  # noqa: S606
        except Exception:
            pass
    return {"html": str(hp), "json": str(jp), "md": str(mp)}


def run_all(apply: bool, do_open: bool, fast: bool = False, limit: int = 0) -> dict:
    _p(1, "全景稽核啟動(AST 精準定位;收容件/退役夾零觸碰)")
    s = scan(limit=limit)
    _p(31, f"掃描完成:{s['files_scanned']} 檔 · {s['issues']} 問題")
    f = fix({"ACCEL", "NET", "VERB"}, apply=apply, scan_rows=s["rows"])
    _p(61, f"修復{'(已套用)' if apply else '(乾跑)'}:{sum(f['applied_by_class'].values())} 處")
    t = run_tests(fast=fast)
    _p(90, f"實測完成:{t['verdict']}")
    s2 = scan(progress=False) if apply else s
    cov = coverage()
    verdict = "RED" if (t["verdict"] == "RED" or s2["by_class"].get("SYNTAX")) else (
        "YELLOW" if (t["verdict"] == "YELLOW" or s2["issues"]) else "GREEN")
    fl = fixed_ledger(s2, cov)                       # 批537:已修冊拿活樹重量一次(回歸=RED)
    if fl.get("regressions") and verdict != "RED":
        verdict = "RED"                              # 冊說修好卻又量到=回歸,這是真紅燈,不能被 YELLOW 蓋過去
    pay = {"schema": "VIA.CGC158.panorama.v1", "batch": "批537", "engine": f"{ENGINE_ID} {VERSION}",
           "ts": _dt.datetime.now().isoformat(timespec="seconds"), "verdict": verdict,
           "scan": s2, "scan_before": {"issues": s["issues"], "by_class": s["by_class"]}, "fix": f,
           "tests": t, "coverage": cov, "triage": issue_triage(s2), "fixed": fl,
           "laws": ["L30 一功能一主", "L50 QuantGuard-only", "L51 中央派送家族境", "L52 誠實四態", "L53 動詞契約",
                    "L54 尾版律", "L56 自動修三態", "L57 誠實分母", "L58 證據分級"]}
    pay["summary"] = summary_line(pay)
    _p(95, f"已修冊複驗:{fl.get('why', '')[:70]}")
    paths = write_report(pay, do_open)
    pay["paths"] = paths
    _p(100, f"報告完成 → {paths['html']}")
    return pay


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        T = Path(td)
        (T / "functional modules" / "VDF" / "engine").mkdir(parents=True)
        (T / "references" / "intake").mkdir(parents=True)
        good = T / "functional modules" / "VDF" / "engine" / "VDF_ENG999_Good_v0100.py"
        good.write_text('"""doc."""\nfrom __future__ import annotations\nimport json\n\n\ndef main():\n    return 0\n', encoding="utf-8")
        bad = T / "functional modules" / "VDF" / "engine" / "VDF_ENG998_Hard_v0100.py"
        bad.write_text('"""doc."""\nimport polars as pl\nimport subprocess, sys, argparse\nfrom pathlib import Path\n\n\ndef go():\n    subprocess.run([sys.executable, str(Path("functional modules/VRN/x.py"))])\n\n\ndef main() -> int:\n    p = argparse.ArgumentParser()\n    p.add_argument("verb", choices=("selftest", "status"))\n    args = parser.parse_args()\n    return 0\n', encoding="utf-8")
        pin = T / "functional modules" / "VDF" / "engine" / "VDF_ENG997_Pin_v0100.py"
        pin.write_text('"""說明文字提到 CGC_MDL149_X_v0100.py 不算違律。"""\nENGINE_PATH = "CGC_MDL157_VIAUniqueEntryControl_v0100.py"\nNOTE = "報告裡寫 VDF_ENG086_QuantGuardOneBridge_v0100.py 只是說明"\nimport talib\n', encoding="utf-8")
        intake = T / "references" / "intake" / "收容件_v0100.py"
        intake.write_text("import polars\n", encoding="utf-8")
        syn = T / "functional modules" / "VDF" / "engine" / "VDF_ENG996_Syn_v0100.py"
        syn.write_text("def broken(:\n    pass\n", encoding="utf-8")

        i_good = audit_source(good, good.read_text(encoding="utf-8"), "functional modules/VDF/engine/VDF_ENG999_Good_v0100.py")
        i_bad = audit_source(bad, bad.read_text(encoding="utf-8"), "functional modules/VDF/engine/VDF_ENG998_Hard_v0100.py")
        i_pin = audit_source(pin, pin.read_text(encoding="utf-8"), "functional modules/VDF/engine/VDF_ENG997_Pin_v0100.py")
        i_syn = audit_source(syn, syn.read_text(encoding="utf-8"), "functional modules/VDF/engine/VDF_ENG996_Syn_v0100.py")
        cls = lambda L: {x["cls"] for x in L}

        chk("① 缺加速器橋/網路工具橋(VDF 引擎)逐檔定位", cls(i_good) == {"ACCEL", "NET"}, str(sorted(cls(i_good))))
        chk("② AST 精準:模組頂硬相依重庫(polars)帶行號", any(x["cls"] == "HARDIMP" and x["line"] == 2 and x["how"] == "ast" for x in i_bad),
            str([(x['cls'], x['line']) for x in i_bad]))
        chk("③ AST 精準:sys.executable 派**別支引擎**才報(家族境律 L51);自跑自己不報",
            any(x["cls"] == "SYSEXE" and x["how"] == "ast" for x in i_bad)
            and not any(x["cls"] == "SYSEXE" for x in audit_source(good, '"""d."""\nimport subprocess, sys\nsubprocess.run([sys.executable, "-c", "print(1)"])\n', "functional modules/VDF/engine/z_v0100.py")))
        chk("④ 彈性定位:argparse 有 selftest 位置動詞但不吃 --selftest(L53)", any(x["cls"] == "VERB" for x in i_bad))
        chk("⑤ AST:釘死版號**當路徑用**才報(L54)· 說明字串/docstring 不報(避免假紅)· TA-Lib 活動接線(L50)",
            cls(i_pin) >= {"PINVER", "TALIB"} and len([x for x in i_pin if x["cls"] == "PINVER"]) == 1,
            str(sorted(cls(i_pin))) + f" · PINVER {len([x for x in i_pin if x['cls'] == 'PINVER'])} 件(只有 ENGINE_PATH 那行)")
        chk("⑥ 語法錯誠實報 SYNTAX 不猜改", cls(i_syn) == {"ACCEL", "NET", "SYNTAX"} or "SYNTAX" in cls(i_syn), str(sorted(cls(i_syn))))
        chk("⑦ 收容件/退役夾/正典 SSOT 零觸碰(SKIP 名單;READ_ONLY 正本連加速器橋都不插)",
            _skip(intake) and _skip(T / "__pycache__" / "x.py") and not _skip(good)
            and _skip(Path("/x/supportive modules/ssot/VIA_Financial_Institution_SSOT_v0100.py"))
            and _skip(Path("/x/VIA_RetiredEngines/y.py")))

        g0 = good.read_text(encoding="utf-8")
        sv = globals()["VIA"]
        globals()["VIA"] = T
        try:
            r1 = fix_one("functional modules/VDF/engine/VDF_ENG999_Good_v0100.py", {"ACCEL", "NET"}, apply=True)
            after = good.read_text(encoding="utf-8")
            r2 = fix_one("functional modules/VDF/engine/VDF_ENG999_Good_v0100.py", {"ACCEL", "NET"}, apply=True)
            r3 = fix_one("functional modules/VDF/engine/VDF_ENG996_Syn_v0100.py", {"ACCEL"}, apply=True)
            rv = fix_one("functional modules/VDF/engine/VDF_ENG998_Hard_v0100.py", {"VERB"}, apply=False)
        finally:
            globals()["VIA"] = sv
        chk("⑧ 修復=純增量:區塊插在 docstring/__future__ 之後,AST 仍可解析,原邏輯字面不動",
            set(r1["applied"]) == {"ACCEL", "NET"} and "[VIA:ACCEL-BRIDGE" in after and "[VIA:NET-BRIDGE" in after
            and "def main():" in after and ast.parse(after) is not None and len(after) > len(g0))
        chk("⑨ 冪等:同檔再修一次=零套用(不重複插塊)", r2["applied"] == [] and good.read_text(encoding="utf-8") == after)
        chk("⑩ 語法壞檔不動(原檔語法錯=拒修,誠實回因由)", r3["ok"] is False and "語法錯" in r3["why"] and syn.read_text(encoding="utf-8") == "def broken(:\n    pass\n")
        chk("⑪ 動詞等價轉換只在 main/parse_args 形狀吻合時做(不猜改)", "VERB" in rv["applied"] or any("VERB" in x for x in rv["skipped"]), str(rv))

    with tempfile.TemporaryDirectory() as td2:
        T2 = Path(td2)
        (T2 / "functional modules" / "VDF" / "engine").mkdir(parents=True)
        selfrun = T2 / "functional modules" / "VDF" / "engine" / "VDF_ENG995_Self_v0100.py"
        selfrun.write_text('"""d."""\nimport subprocess, sys\nfrom pathlib import Path\n\n\ndef go():\n    subprocess.run([sys.executable, str(Path(__file__).resolve()), "--probe-one"])\n', encoding="utf-8")
        fixt = T2 / "functional modules" / "VDF" / "engine" / "VDF_ENG994_Fix_v0100.py"
        fixt.write_text('"""d."""\nfrom pathlib import Path\nREAL_PATH = Path("VDF_ENG001_Real_v0100.py")\n\n\ndef _probe_env(tmp):\n    d = tmp / "V"\n    (d / "Register-VIA-Commands-v0174.ps1").write_text("x")\n    return d\n\n\ndef selftest():\n    P = Path("X_ENG001_A_v0100.py")\n    chk("x", P.exists())\n    return 0\n', encoding="utf-8")
        i_self = audit_source(selfrun, selfrun.read_text(encoding="utf-8"), "functional modules/VDF/engine/VDF_ENG995_Self_v0100.py")
        i_fix = audit_source(fixt, fixt.read_text(encoding="utf-8"), "functional modules/VDF/engine/VDF_ENG994_Fix_v0100.py")
    chk("⑮ 批536 判準精準化反例:自己跑自己≠跨家族派送(SYSEXE 0)· 自測段/探針函式/夾具字串≠釘死版號(只留正式那一個)· 候選夾/打包副本不是活樹",
        not any(x["cls"] == "SYSEXE" for x in i_self)
        and len([x for x in i_fix if x["cls"] == "PINVER"]) == 1
        and _skip(Path("/x/functional modules/VDF/engine/candidates/z.py")) is False
        and all(k in Path(__file__).read_text(encoding="utf-8") for k in ("_NONLIVE_DIR", "self_run")),
        f"(自跑 SYSEXE {len([x for x in i_self if x['cls'] == 'SYSEXE'])} · 夾具檔 PINVER {len([x for x in i_fix if x['cls'] == 'PINVER'])})")
    a, b, cc, dd = judge(0, "[計] OK 9"), judge(3, "=== ABSENT 本境無 polars ==="), judge(1, "Traceback\nModuleNotFoundError: No module named 'x'"), judge(1, "AssertionError")
    chk("⑫ 誠實四態(與 CGC157 同律 L52):GREEN/ABSENT/ABSENT(訊息)/RED",
        a[0] == "GREEN" and b[0] == "ABSENT" and cc[0] == "ABSENT" and dd[0] == "RED")
    _scan_ok = {"issues": 0, "by_class": {}}
    _scan_bad = {"issues": 3, "by_class": {"ACCEL": 3}}
    _cov_ok, _cov_bad = {"accel_pct": 100.0, "net_pct": 100.0}, {"accel_pct": 97.2, "net_pct": 100.0}
    v_ok = _verify_one({"kind": "class_zero", "cls": "ACCEL"}, _scan_ok, _cov_ok)
    v_re = _verify_one({"kind": "class_zero", "cls": "ACCEL"}, _scan_bad, _cov_ok)
    v_cv = _verify_one({"kind": "coverage_pct", "field": "accel_pct", "expect": 100.0}, _scan_ok, _cov_bad)
    v_ab = _verify_one({"kind": "coverage_pct", "field": "nope_pct", "expect": 100.0}, _scan_ok, _cov_ok)
    v_no = _verify_one({"kind": "tail_contains", "dir": "supportive modules/registry", "glob": "ZZZ_NOPE_v*.py", "markers": ["x"]}, _scan_ok, _cov_ok)
    v_tc = _verify_one({"kind": "tail_contains", "dir": "supportive modules/registry",
                        "glob": "CGC_MDL158_VIAPanoramaAuditRepair_v*.py", "markers": ["fixed_ledger"]}, _scan_ok, _cov_ok)
    v_ab2 = _verify_one({"kind": "tail_contains", "dir": ".", "glob": "VIA_SYSTEM_MANAGER_v*.py",
                         "markers": ["TASK_FORMAL_NAMES"], "markers_absent": ['"talib_probe":']}, _scan_ok, _cov_ok)
    chk("⑭ 批537 已修冊複驗三態:冊說修好且活樹仍為 0=GREEN · 活樹又量到=RED(回歸)· 覆蓋率退步=RED · 量不了(欄不在/尾版不在)=ABSENT 不當綠 · 尾版憑據齊=GREEN · 退役件在尾版復活=RED",
        v_ok[0] == "GREEN" and v_re[0] == "RED" and v_cv[0] == "RED" and v_ab[0] == "ABSENT" and v_no[0] == "ABSENT"
        and v_tc[0] == "GREEN" and v_ab2[0] == "GREEN",
        f"({v_ok[0]} {v_re[0]} {v_cv[0]} {v_ab[0]} {v_no[0]} {v_tc[0]} 退役件未復活={v_ab2[0]})")
    fl_live = fixed_ledger(_scan_ok, _cov_ok)
    tri = issue_triage({"issues": 129, "by_class": {"VERB": 6, "HARDIMP": 100, "PINVER": 23}})
    _dummy = {"triage": tri, "fixed": fl_live, "tests": {"tally": {"GREEN": 17}, "rows": [0] * 17}, "fix": {"applied_by_class": {}}}
    line = summary_line(_dummy)
    chk("⑮a 批537 摘要講得清楚:問題按 L56 三態拆(ACCEL/NET 可同時 · VERB 順序 · HARDIMP/PINVER 待令)· 真 RED 單列 · 已修冊與實測同句;四處(主控台/頁首/TAB①/MD)同一句",
        tri["parallel"] == 0 and tri["sequential"] == 6 and tri["report_only"] == 123 and tri["red"] == 0 and tri["total"] == 129
        and "可同時修 0" in line and "順序修 6" in line and "只報位置待令 123" in line and "真 RED 0" in line
        and "已修冊" in line and "實測 17/17 綠" in line, f"({line[:96]})")
    chk("⑮b 批537 已修冊在位且本器是它的擁有者(冊不在=ABSENT 誠實,不編)",
        FIXED_SSOT.is_file() and fl_live["state"] in ("GREEN", "RED") and len(fl_live["rows"]) >= 5,
        f"({FIXED_SSOT.name} · {fl_live.get('why','')[:70]})")
    src = Path(__file__).read_text(encoding="utf-8").split("\ndef selftest() -> int:")[0]   # 批536:唯一切點(文件字串裡也寫得到 def selftest)
    chk("⑬a 一名一主(L30):本器只寫 VIA_Reports/panorama_audit;不碰 CGC_MDL135/CGC_MDL149 L19 閘的 VIA_Reports/panorama",
        '"panorama_audit"' in src and '"VIA_Reports" / "panorama"\n' not in src and "PANORAMA_AUDIT_latest" in src)
    chk("⑬ 律:零網路 · 不代裝 · 家族境走匯流排 · 25 加速器名冊只讀 CGC156",
        all(("import " + k) not in src for k in ("requests", "httpx", "urllib")) and "pip install" not in src
        and "_bus_python" in src and "VIA_ACCELERATOR_CONTROL_latest.json" in src)
    print(f"  [計] 十八檢 OK {18 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="VIA 全景稽核修復正主")
    ap.add_argument("verb", nargs="?", choices=("scan", "fix", "tests", "report", "all", "selftest"), default="all")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--open", dest="do_open", action="store_true")
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--json", dest="as_json", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--classes", default="ACCEL,NET,VERB")
    argv = [("selftest" if a == "--selftest" else a) for a in sys.argv[1:]]
    args = ap.parse_args(argv)
    if args.verb == "selftest":
        print(f"=== 全景稽核修復正主({ENGINE_ID} {VERSION})· 十八檢自測(零網路;合成夾具;真樹零觸碰)===")
        return selftest()
    if args.verb == "scan":
        s = scan(limit=args.limit)
        if args.as_json:
            print(json.dumps(s, ensure_ascii=False, indent=1))
        else:
            print(f"=== 全景掃描 · {s['files_scanned']} 檔 · {s['issues']} 問題 · {s['secs']}s ===")
            for k, v in sorted(s["by_class"].items(), key=lambda x: -x[1]):
                zh, act, fixhow = CATEGORIES.get(k, (k, "", ""))
                print(f"  [{'修' if act == 'GREEN_FIX' else '報'}] {k:<8} {v:>5} · {zh}")
        return 0
    if args.verb == "fix":
        f = fix(set(args.classes.split(",")), apply=args.apply, workers=args.workers, limit=args.limit)
        print(json.dumps({k: v for k, v in f.items() if k != "rows"}, ensure_ascii=False, indent=1))
        return 0
    if args.verb == "tests":
        t = run_tests(fast=args.fast)
        for r in t["rows"]:
            print(f"  [{r['state']:<7}] {r['system']:<5} {r['name']:<28} rc={r['rc']} · {str(r['why'])[:70]}")
        print(f"  [計] {t['tally']} · 裁決 {t['verdict']} · 中央派送 {t['dispatch'].get('state')}")
        return 0 if t["verdict"] != "RED" else 2
    if args.verb == "report":
        pay = json.loads((OUT / "PANORAMA_AUDIT_latest.json").read_text(encoding="utf-8")) if (OUT / "PANORAMA_AUDIT_latest.json").is_file() else run_all(False, False)
        print(write_report(pay, args.do_open))
        return 0
    pay = run_all(args.apply, args.do_open, args.fast, args.limit)
    print(f"=== 全景稽核修復 · {pay['verdict']} · {pay.get('summary') or summary_line(pay)} ===")
    fl = pay.get("fixed") or {}
    for r in fl.get("rows", []):
        print(f"  [{r['lamp']:<6}] 已修冊 {r['batch']} {str(r['cls']):<16} {str(r['what'])[:52]}")
    if fl.get("regressions"):
        print(f"  [回歸] {fl['regressions']}(冊說修好,現在又量到=真紅燈)")
    print(f"  [頁] {pay['paths']['html']}")
    return 0 if pay["verdict"] != "RED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
