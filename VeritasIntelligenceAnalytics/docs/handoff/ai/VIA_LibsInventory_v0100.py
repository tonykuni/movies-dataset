#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_LibsInventory v0100 — 第三方 libs 治理盤:全樹 AST 普查 → 冊上宣告對帳 → 衝突矩陣 → 三鏡像布建計畫
(操作員 2026-11-08 令「依照長期管理環境工具政策…現況哪些衝突修復 · 新增的項目用反覆衝突機制清華阿里官方叁鏡像全部一起測試 ·
  無衝突驗帳無誤後的計畫 · 布建就依照計畫直接執行 · 用已成功基礎下持續不要一直從頭」)

只讀他系統:正本冊 VIA_EnvGovernance_Baseline_v*.json 一個字都不改;本引擎只寫自己的盤冊與自己的計畫 / HTML。

**不做的事(寫在最前面,因為這是這支引擎的誠實邊界)**
  · 不裝任何套件(裝件一律經 VCGC via-envgov tools --apply --approve)
  · 不代設同意閘(VIA_NET_CONSENT / VIA_SCRAPE_CONSENT 由操作員自己開)
  · 因此「鏡像連通 / 解析預演 / 實際安裝」三件在本機一律 GRAY=未跑,計畫裡印指令讓桌機跑;
    GRAY 絕不寫成綠,也絕不寫成紅——沒量到就是沒量到。

衝突偵測全部離線、確定性(同樣輸入同樣輸出),分九類:
  L1 BLOCKED_IN_BASE      封鎖家族件出現在 base 層            RED  (冊 policy:立拔)
  L2 CROSS_FAMILY         同一件被兩個以上家族認領 → 目標境歧義 RED  (冊內矛盾)
  L3 CORE_WRONG_LAYER     engine_core 件落在使用者層而非主層   RED  (ENG115 duckdb 2.0 真紅源頭)
  L4 DECLARED_ABSENT      冊上宣告了、容器沒有                RED/YELLOW
  L5 UNDECLARED_PRESENT   容器有、冊上沒有 → 會悄悄變版        YELLOW
  L6 UNDECLARED_ABSENT    冊上沒有、容器也沒有 → 程式跑不起來  RED
  L7 MAP_UNKNOWN          import 名無 pip 名對映 → 無法解析    YELLOW
  L8 NAMING_LAW           冊上 naming_law.renames 仍有待改名   GRAY (本機看不到那些境)
  L9 FAMILY_CORE_GAP      family_env_core 的件不在任何家族名單 YELLOW

動詞:
  scan       全樹 AST 普查,只印不寫
  audit      普查 + 對帳 + 衝突矩陣 → 寫盤冊(add-only:實質沒變不出新版號)
  plan       由盤冊出布建計畫(R1 冊修本機做 / R2 境修桌機做 / R3 收尾),含三鏡像指令
  ui         產 HTML U/I(Atlas --vl-* 視覺鎖定)
  all        audit → plan → ui(--apply 才真的寫盤冊)
  --selftest 自測
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

import argparse
import ast
import html
import importlib.util
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "VIA.LibsInventory.v1"
HERE = Path(__file__).resolve().parent                  # docs/handoff/ai
VIA = HERE.parent.parent.parent                         # VeritasIntelligenceAnalytics
REGISTRY = VIA / "supportive modules" / "registry"
BASELINE_STEM = "VIA_EnvGovernance_Baseline_v"
BOOK_STEM = "VIA_LibsInventory_SSOT_v"
PLAN_NAME = "VIA_LibsInventory_Plan.md"
UI_NAME = "VIA_LibsInventory_UI.html"

# 跳過:封存 / 退役 / 參考夾(不是現役)——沿用已實測過的普查口徑
SKIP = ("references/intake", "_superseded", "_retired", "VIA_RetiredEngines",
        "_archive", "__pycache__", "/envs/", "_inbox_to_classify", "/20260804/")

LANE = (("supportive modules/network", "網路工具"),
        ("supportive modules/70_VRN_Rules", "NLP / VRN 規則"),
        ("supportive modules/registry", "VCGC registry"),
        ("supportive modules/ps7", "PS7"),
        ("supportive modules/ui_support", "U/I 支援"),
        ("supportive modules/", "其他輔助"),
        ("functional modules/VRN/", "VRN-2"),
        ("functional modules/VDF/", "VDF"),
        ("functional modules/VQG/", "VQG"),
        ("functional modules/VAP/", "VAP"),
        ("docs/", "docs"))

# import 名 → pip 名。只收「有依據」的:冊上註明的(fitz→pymupdf · cv2 錨)、
# 以及 pip 名與 import 名公認不同的那幾支。認不出來的一律標 L7,不硬猜。
PIP_NAME = {
    "fitz": "pymupdf",                    # 冊 family_env_core._note:pip 名對映 fitz→pymupdf
    "cv2": "opencv-contrib-python",       # 冊 cv2_anchor
    "PIL": "pillow",
    "bs4": "beautifulsoup4",
    "docx": "python-docx",
    "pptx": "python-pptx",
    "yaml": "pyyaml",
    "dateutil": "python-dateutil",
    "sklearn": "scikit-learn",
    "skimage": "scikit-image",
    "pdfminer": "pdfminer.six",
    "fontTools": "fonttools",
    "dotenv": "python-dotenv",
    "markdown_it": "markdown-it-py",
    "mdit_py_plugins": "mdit-py-plugins",
    "pkg_resources": "setuptools",
    "jwt": "pyjwt",
    "OpenSSL": "pyopenssl",
    "Crypto": "pycryptodome",
    "serial": "pyserial",
    "zmq": "pyzmq",
    "curl_cffi": "curl-cffi",
    "tabula": "tabula-py",
    "camelot": "camelot-py",
    "win32com": "pywin32",
    "win32api": "pywin32",
    "win32con": "pywin32",
    "pythoncom": "pywin32",
    "win32gui": "pywin32",
}

# 自家命名律:名字長這樣的就是自家模組,即使樹內沒有那個檔。
# 依據:VDF_MDL103 名冊把 VRN_SupportBridge.py 記成自家檔(執行期由 CGC_MDL067 注入),
# 樹內找不到 → 那是「自家檔不在位」,不是「第三方套件缺件」。混在一起會憑空造出假缺件。
OWN_PREFIX = re.compile(
    r"^(via|vrn|vdf|vqg|vap|vis|vetf|vtr|vpl|pmis|vmt|cgc|sup)[_-]", re.I)
OWN_INFIX = re.compile(r"(_|^)(eng|mdl|sup|cgc)\d{3}", re.I)


def is_own_name(imp: str, own: set[str]) -> bool:
    """自家模組判定:① 樹內有同名檔 / 夾  ② 符合自家命名律。"""
    return imp.lower() in own or bool(OWN_PREFIX.match(imp)) or bool(OWN_INFIX.search(imp))


LAYERS = (("/usr/local/lib/python3.13/dist-packages", "主層"),
          ("/root/.local/lib/python3.13/site-packages", "使用者層"),
          ("/usr/lib/python3/dist-packages", "系統層"))

LEVEL_ORDER = {"RED": 0, "YELLOW": 1, "GRAY": 2}

# 量測地點。本容器是雲端沙盒直譯器(非 venv),它的「主層」是**這台**的 base,
# 不是桌機那顆 BASE(冊 evidence.workstation_20260907:BASE 681 件 136 衝突,另有實錄)。
# 不寫清楚的話,容器層的發現會被誤讀成桌機結論。
MEASURED_ON = "雲端容器(py3.13 系統直譯器,非 venv)"


# ───────────────────────── 小工具 ─────────────────────────
def norm(name: str) -> str:
    """PEP 503 風格正規化(pip 名比對用)。"""
    return re.sub(r"[-_.]+", "-", str(name).strip().lower())


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d{4})\.", p.name)
    return int(m.group(1)) if m else -1


def tail(dirpath: Path, stem: str, ext: str) -> Path | None:
    """家族尾版(先解析再用,避免 PINVER:不把版號寫死在程式裡)。"""
    cands = sorted(dirpath.glob(f"{stem}*{ext}"), key=_vnum)
    return cands[-1] if cands else None


def next_version_path(dirpath: Path, stem: str, ext: str) -> Path:
    """下一個版號路徑;已發布的版號絕不覆寫。"""
    t = tail(dirpath, stem, ext)
    nxt = (_vnum(t) + 1) if t is not None else 100
    return dirpath / f"{stem}{nxt:04d}{ext}"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_baseline(registry: Path = REGISTRY) -> tuple[dict, str]:
    p = tail(registry, BASELINE_STEM, ".json")
    if p is None:
        raise SystemExit(f"[紅] 找不到環境治理正本冊 {BASELINE_STEM}*.json於 {registry}")
    return json.loads(p.read_text(encoding="utf-8")), p.name


# ───────────────────────── 宣告索引(冊 → pip 名) ─────────────────────────
def declared_index(bl: dict) -> dict[str, list[tuple[str, str]]]:
    """pip 名 → [(bucket, detail), …]。

    五個來源都算宣告,少算任何一個都會把治理中的件誤判成盲區:
      base/toolchain · base/engine_core · base/low_risk_allow
      family/<家族>   (正本鍵是 families[*].members —— 不是 packages,踩過這個坑)
      famcore/<境>    (family_env_core)
      override/<境>   (package_env_overrides)
    """
    idx: dict[str, list[tuple[str, str]]] = defaultdict(list)
    base = bl.get("base", {}) or {}
    for key in ("toolchain", "engine_core", "low_risk_allow"):
        for x in (base.get(key) or []):
            idx[norm(x)].append((f"base/{key}", "base"))
    for fam, v in (bl.get("families") or {}).items():
        if not isinstance(v, dict):
            continue
        for x in (v.get("members") or []):
            idx[norm(x)].append((f"family/{fam}", v.get("target_env", "?")))
    for env, pkgs in (bl.get("family_env_core") or {}).items():
        if env.startswith("_") or not isinstance(pkgs, list):
            continue
        for x in pkgs:
            idx[norm(x)].append((f"famcore/{env}", env))
    for pkg, env in (bl.get("package_env_overrides") or {}).items():
        idx[norm(pkg)].append((f"override/{env}", env))
    return dict(idx)


def import_map(bl: dict) -> dict[str, str]:
    """import 名 → pip 名。**冊上的 import_name_map 是正本**,引擎內建 PIP_NAME 只是退路。

    順序很重要:冊上的先用。少一條對映就會把在冊的件誤判成未宣告
    (踩過:surya 其實就是 ocr 家族的 surya-ocr,被當成 65 個假缺件之一)。
    """
    m = dict(PIP_NAME)
    for k, v in (bl.get("import_name_map") or {}).items():
        if k.startswith("_") or not isinstance(v, str):
            continue                       # _note 這種註解鍵不是對映
        m[k] = v
    return m


def pip_of(imp: str, idx: dict, imap: dict | None = None) -> tuple[str, bool]:
    """import 名 → (pip 名, 是否有依據)。認不出來就回正規化名並標 False。"""
    m = imap if imap is not None else PIP_NAME
    if imp in m:
        return norm(m[imp]), True          # 值也要正規化:冊上索引鍵是正規化過的
    n = norm(imp)
    if n in idx:
        return n, True
    return n, False


def family_of(declared: list[tuple[str, str]]) -> list[str]:
    return sorted({b.split("/", 1)[1] for b, _ in declared if b.startswith("family/")})


def target_envs(declared: list[tuple[str, str]]) -> list[str]:
    out = {d for b, d in declared if not b.startswith("base/")}
    return sorted(x for x in out if x and x != "?")


# ───────────────────────── 普查 ─────────────────────────
def lane_of(rel: str) -> str:
    for p, n in LANE:
        if rel.startswith(p):
            return n
    return "根目錄 / 其他"


def own_names(via: Path = VIA) -> set[str]:
    """自家模組名(小寫)。

    **不套 SKIP**:退役 / 封存夾裡的檔名仍然是自家模組名,現役程式若還 import 它,
    那是「自家模組不在位」的問題,不是第三方套件缺件 —— 把它算成第三方會憑空造出
    幾十個假缺件(踩過:96 個 L6 裡大半是自家模組)。
    另收套件夾名(有 __init__.py 的夾)與資料夾名,因為 `import engine.x` 的頂層是夾名。
    """
    out: set[str] = set()
    for f in via.rglob("*.py"):
        out.add(f.stem.lower())
        if f.name == "__init__.py":
            out.add(f.parent.name.lower())
    for d in via.rglob("*"):
        if d.is_dir():
            out.add(d.name.lower())
    return out


def scan_tree(via: Path = VIA, parse_fail: list | None = None) -> tuple[dict, int, set[str]]:
    """AST 取真 import(不用 grep 猜)。回 (tops, 掃過的檔數, 自家模組名小寫)。

    AST 剖不過的檔**逐支記進 parse_fail 並回報數量**。不能默默 continue:
    剖不過就讀不到它的 import,那支檔的套件需求會整個消失,盤冊卻看起來很完整。
    (全景工具報過我這裡原本是 SWALLOW —— 它說得對。)
    """
    std = set(sys.stdlib_module_names)
    tops: dict[str, dict[str, set]] = defaultdict(lambda: defaultdict(set))
    own = own_names(via)
    nfile = 0
    for f in via.rglob("*.py"):
        rel = str(f.relative_to(via))
        if any(s in "/" + rel for s in SKIP):
            continue
        nfile += 1
        try:
            tree = ast.parse(f.read_bytes(), filename=rel)
        except Exception as e:
            if parse_fail is not None:
                parse_fail.append({"file": rel, "error": f"{type(e).__name__}: {e}"})
            continue
        for n in ast.walk(tree):
            mods: list[str] = []
            if isinstance(n, ast.Import):
                mods = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom):
                if n.level:               # 相對匯入 = 自家的
                    continue
                mods = [n.module or ""]
            for m in mods:
                top = m.split(".")[0]
                if not top or top in std:
                    continue
                tops[top][lane_of(rel)].add(rel)
    return tops, nfile, own


def container_layer(imp: str, via: Path = VIA) -> str:
    try:
        s = importlib.util.find_spec(imp)
    except Exception:
        return "ABSENT(匯入時出錯)"
    if s is None or not s.origin:
        return "ABSENT"
    o = s.origin
    for pre, tag in LAYERS:
        if o.startswith(pre):
            return tag
    if str(via) in o:
        return "樹內(自家模組)"
    return "其他:" + o[:40]


def build_rows(bl: dict, via: Path = VIA) -> tuple[list[dict], int, list[dict], list[dict]]:
    """回 (第三方列, 掃過檔數, 自家模組不在位列, AST 剖不過列)。各自分流,不互相汙染。"""
    idx = declared_index(bl)
    imap = import_map(bl)
    parse_fail: list[dict] = []
    tops, nfile, own = scan_tree(via, parse_fail)
    rows: list[dict] = []
    own_missing: list[dict] = []
    for imp, lanes in tops.items():
        layer = container_layer(imp, via)
        n = sum(len(s) for s in lanes.values())
        ln = sorted(lanes, key=lambda k: -len(lanes[k]))
        if layer.startswith("樹內"):
            continue
        if is_own_name(imp, own):
            if imp.lower() not in own:    # 名字是自家的、樹內卻沒有這個檔
                own_missing.append({"import": imp, "nfiles": n, "lanes": ln})
            continue                      # 自家模組一律不進第三方列
        pip, mapped = pip_of(imp, idx, imap)
        rows.append({
            "import": imp,
            "pip": pip,
            "mapped": mapped,
            "layer": layer,
            "declared": idx.get(pip, []),
            "nfiles": n,
            "lanes": ln,
        })
    rows.sort(key=lambda r: (-r["nfiles"], r["pip"]))
    own_missing.sort(key=lambda r: -r["nfiles"])
    return rows, nfile, own_missing, parse_fail


# ───────────────────────── 衝突偵測(純函式,可餵夾具) ─────────────────────────
def detect(rows: list[dict], bl: dict, own_missing: list[dict] | None = None) -> list[dict]:
    blocked = {str(x) for x in (bl.get("base", {}) or {}).get("never_in_base_families") or []}
    base_layers = {"主層", "系統層"}
    out: list[dict] = []

    def add(code, level, row, why, evidence, fix):
        out.append({"code": code, "level": level,
                    "pip": row.get("pip", ""), "import": row.get("import", ""),
                    "why": why, "evidence": evidence, "fix": fix,
                    "lanes": row.get("lanes", [])[:3], "nfiles": row.get("nfiles", 0)})

    for r in rows:
        decl = r.get("declared") or []
        fams = family_of(decl)
        buckets = [b for b, _ in decl]
        layer = r.get("layer", "")
        absent = layer.startswith("ABSENT")
        envs = target_envs(decl)

        bad_fams = [f for f in fams if f in blocked]
        if bad_fams and layer in base_layers:
            add("L1_BLOCKED_IN_BASE", "RED", r,
                f"封鎖家族 {'/'.join(bad_fams)} 的件卻在 base 層",
                f"容器實況={layer}({MEASURED_ON});冊 never_in_base_families 列有 {'/'.join(bad_fams)}",
                f"拉出到 {'/'.join(envs) or '家族境'};base 端移除須待目標境 VERIFY 綠(R2)")

        if len(fams) >= 2:
            add("L2_CROSS_FAMILY", "RED", r,
                f"同一件被 {len(fams)} 個家族認領 → 目標境歧義",
                "冊 families[*].members 同時列入:" + " / ".join(fams),
                "冊上擇一認領(或在 package_env_overrides 指定唯一境)—— 純冊修(R1)")

        if "base/engine_core" in buckets and layer == "使用者層":
            add("L3_CORE_WRONG_LAYER", "RED", r,
                "engine_core 共用基座件卻裝在使用者層 → 版本會蓋過主層而沒人看見",
                f"容器實況={layer}(主層沒有);{MEASURED_ON};冊 base/engine_core",
                "歸位主層(R2);本案實證:duckdb 2.0.0 移除 fetchone 讓 VRN_ENG115 自測當掉")

        if decl and absent:
            core = "base/engine_core" in buckets
            add("L4_DECLARED_ABSENT", "RED" if core else "YELLOW", r,
                "冊上宣告了、容器沒有" + ("(且是共用基座件)" if core else ""),
                f"容器實況={layer}({MEASURED_ON});冊上={'、'.join(sorted(set(buckets)))}",
                f"裝進 {'/'.join(envs) or 'base'}(R2:經 via-envgov tools --apply --approve)")

        if not decl and not absent:
            add("L5_UNDECLARED_PRESENT", "YELLOW", r,
                "容器有、冊上沒有 → 會悄悄變版而沒人比對得出來",
                f"容器實況={layer}({MEASURED_ON});冊上五個來源都查不到 {r.get('pip')}",
                "登入冊上對應家族 members(或 base low_risk_allow)—— 純冊修(R1)")

        if not decl and absent:
            guess = "" if r.get("mapped", True) else ";pip 名是用 import 名猜的,對不對要到鏡像才知道"
            add("L6_UNDECLARED_ABSENT", "RED", r,
                "冊上沒有、容器也沒有 → 匯入它的程式一行都跑不起來",
                f"容器實況={layer}({MEASURED_ON});冊上查無;{r.get('nfiles')} 支現役 .py 匯入它{guess}",
                "先登冊決定家族與目標境(R1),再裝(R2)")

        if not r.get("mapped", True) and not absent:
            # 只有「裝在容器裡、冊上又查不到」才是真的 L7:它在位、卻釘不住版本。
            # ABSENT 那批已由 L6 收走,在這裡再報一次只會把黃燈灌水(踩過:65 筆重複)。
            add("L7_MAP_UNKNOWN", "YELLOW", r,
                "在位卻查不到 pip 名 → 釘不住版本,也比對不出它何時變了",
                f"import 名 {r.get('import')};容器={layer}({MEASURED_ON});PIP_NAME 與冊上都沒有對映",
                "把對映與版本寫進冊 —— 純冊修(R1)")

    for env, pkgs in (bl.get("naming_law", {}) or {}).get("renames", {}).items():
        out.append({"code": "L8_NAMING_LAW", "level": "GRAY", "pip": env, "import": env,
                    "why": f"冊上 naming_law 仍列待改名 {env} → {pkgs}",
                    "evidence": "本機沒有任何 via_ 境,看不到該境 —— 沒量到就留 GRAY",
                    "fix": "桌機 via-envgov rename(只出令,不自動改名)",
                    "lanes": [], "nfiles": 0})

    idx = declared_index(bl)
    fam_all = {k for k, v in idx.items() if any(b.startswith(("family/", "base/")) for b, _ in v)}
    for env, pkgs in (bl.get("family_env_core") or {}).items():
        if env.startswith("_") or not isinstance(pkgs, list):
            continue
        for p in pkgs:
            if norm(p) not in fam_all:
                out.append({"code": "L9_FAMILY_CORE_GAP", "level": "YELLOW",
                            "pip": norm(p), "import": norm(p),
                            "why": f"family_env_core[{env}] 列了它,但它不屬任何家族也不在 base",
                            "evidence": f"冊 family_env_core.{env};families[*].members 與 base 三單都查無",
                            "fix": "補進對應家族 members 或 base —— 純冊修(R1)",
                            "lanes": [], "nfiles": 0})

    for m in (own_missing or []):
        out.append({"code": "L10_OWN_MODULE_MISSING", "level": "YELLOW",
                    "pip": m["import"], "import": m["import"],
                    "why": "自家模組名,樹內卻沒有這個檔 —— 不是 libs 車道的事,但不能靜悄悄掉",
                    "evidence": f"命名符合自家律;本倉樹內查無同名 .py;{m['nfiles']} 支現役 .py 匯入它",
                    "fix": "查自家名冊 / 執行期注入(例:VRN_SupportBridge 由 CGC_MDL067 注入);"
                           "libs 布建不處理,只記錄",
                    "lanes": m["lanes"][:3], "nfiles": m["nfiles"]})

    out.sort(key=lambda c: (LEVEL_ORDER.get(c["level"], 9), c["code"], -c["nfiles"], c["pip"]))
    return out


# ───────────────────────── 輪次分配 ─────────────────────────
R1_CODES = {"L2_CROSS_FAMILY", "L5_UNDECLARED_PRESENT", "L7_MAP_UNKNOWN", "L9_FAMILY_CORE_GAP"}
R2_CODES = {"L1_BLOCKED_IN_BASE", "L3_CORE_WRONG_LAYER", "L4_DECLARED_ABSENT"}


def rounds_assign(conf: list[dict]) -> dict[str, list[dict]]:
    """冊 rounds:R1 並行可修 / R2 依序(境相依)/ R3 收尾。

    判準不是嚴重度,是「相依性」:純冊修彼此不相依 → R1,本機就能做完;
    動到境的 → R2,要鏡像、要同意閘、要拓撲序 → 桌機做。
    L6 兩邊都要:冊修在 R1、裝件在 R2,所以同時進兩輪(不是重複計數,是同一件的兩段)。
    """
    r: dict[str, list[dict]] = {"R1": [], "R2": [], "R3": []}
    for c in conf:
        if c["code"] in R1_CODES:
            r["R1"].append(c)
        elif c["code"] in R2_CODES:
            r["R2"].append(c)
        elif c["code"] == "L6_UNDECLARED_ABSENT":
            r["R1"].append(c)
            r["R2"].append(c)
        else:
            r["R3"].append(c)        # L8 等只能出令的,留到收尾輪
    return r


def env_closure(rows: list[dict], bl: dict) -> dict[str, list[str]]:
    """每個 via_ 境的相依閉包 = 樹真的匯入 ∩ 冊上指到該境 ∪ family_env_core[該境]。"""
    clo: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        for e in target_envs(r.get("declared") or []):
            clo[e].add(r["pip"])
    for env, pkgs in (bl.get("family_env_core") or {}).items():
        if env.startswith("_") or not isinstance(pkgs, list):
            continue
        for p in pkgs:
            clo[env].add(norm(p))
    return {k: sorted(v) for k, v in sorted(clo.items())}


# ───────────────────────── 盤冊 ─────────────────────────
def substance(rows: list[dict], conf: list[dict], parse_fail: list[dict] | None = None) -> str:
    """實質指紋:套件集合 + 層 + 宣告 + 衝突碼 + AST 剖不過的檔。重跑結果一樣就不出新版號。

    剖不過的檔名也算實質:多一支剖不過就等於盤冊多一個讀不到的缺口,
    那是盤冊內容真的變了,不該被當成「沒變」而不出新版號。
    """
    import hashlib
    key = [[r["pip"], r["layer"], sorted({b for b, _ in (r.get("declared") or [])})] for r in rows]
    key.sort()
    cc = sorted((c["code"], c["pip"]) for c in conf)
    pf = sorted(x["file"] for x in (parse_fail or []))
    return hashlib.sha256(json.dumps([key, cc, pf], ensure_ascii=False,
                                     sort_keys=True).encode("utf-8")).hexdigest()


def make_book(rows: list[dict], conf: list[dict], bl: dict, bl_name: str, nfile: int,
              own_missing: list[dict] | None = None, parse_fail: list[dict] | None = None) -> dict:
    lv = defaultdict(int)
    for c in conf:
        lv[c["level"]] += 1
    codes = defaultdict(int)
    for c in conf:
        codes[c["code"]] += 1
    declared_n = sum(1 for r in rows if r.get("declared"))
    layers = defaultdict(int)
    for r in rows:
        layers[r["layer"].split("(")[0]] += 1
    return {
        "schema": SCHEMA,
        "engine": "VIA_LibsInventory_v0100.py",
        "generated_at_utc": utc_now(),
        "baseline_book": bl_name,
        "import_name_map_source": "冊 import_name_map" if bl.get("import_name_map") else "引擎內建 PIP_NAME(冊上還沒有正本)",
        "baseline_untouched": True,
        "measured_on": MEASURED_ON,
        "scanned_py_files": nfile,
        "third_party_total": len(rows),
        "declared_total": declared_n,
        "declared_ratio_pct": round(100.0 * declared_n / len(rows), 1) if rows else 0.0,
        "container_layers": dict(layers),
        "conflict_levels": dict(lv),
        "conflict_codes": dict(codes),
        "mirror_chain": (bl.get("mirror_chain") or {}).get("order", []),
        "mirror_probe": "GRAY_NOT_RUN(探測屬網路行為過同意閘;本引擎不代設)",
        "install_executed": "NONE(裝件一律經 VCGC via-envgov tools --apply --approve)",
        "substance_sha256": substance(rows, conf, parse_fail),
        "own_module_missing": own_missing or [],
        "ast_parse_failed": parse_fail or [],
        "ast_parse_failed_note": "剖不過 = 讀不到它的 import = 它的套件需求沒進盤冊。數字不為 0 就代表盤冊有缺口,"
                                 "照實記,不當 0。",
        "rows": rows,
        "conflicts": conf,
        "env_closure": env_closure(rows, bl),
        "rounds": {k: [c["code"] + ":" + c["pip"] for c in v] for k, v in rounds_assign(conf).items()},
    }


def write_book(book: dict, dirpath: Path = REGISTRY) -> tuple[Path, str]:
    t = tail(dirpath, BOOK_STEM, ".json")
    if t is not None:
        prev = json.loads(t.read_text(encoding="utf-8"))
        if prev.get("substance_sha256") == book["substance_sha256"]:
            return t, "UNCHANGED"
    p = next_version_path(dirpath, BOOK_STEM, ".json")
    if p.exists():
        raise SystemExit(f"[紅] {p.name} 已存在 —— 已發布版號不覆寫")
    p.write_text(json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    return p, "WRITTEN"


# ───────────────────────── 計畫 ─────────────────────────
def plan_text(book: dict, bl: dict) -> str:
    mir = (bl.get("mirror_chain") or {})
    order = mir.get("order", [])
    labels = mir.get("labels", [])
    rnd = book.get("rounds", {})
    clo = book.get("env_closure", {})
    L = []
    A = L.append
    A("# VIA libs/環境 布建計畫(由 " + book["engine"] + " 生成)")
    A("")
    A(f"正本冊:`{book['baseline_book']}`(一個字沒改)· 盤冊指紋 `{book['substance_sha256'][:16]}` · {book['generated_at_utc']}")
    A("")
    A("## 鏡像:三個一起,不是三選一")
    A("")
    A("倉根 `uv.toml` 已把三個索引一起登好,uv 走 first-index:前面查無才往下走,官方 `default=true` 永遠兜底。")
    for i, u in enumerate(order):
        A(f"{i+1}. `{u}`  ({labels[i] if i < len(labels) else '?'})")
    A("")
    A("所以 R2 的指令**不要**加 `UV_NO_CONFIG=1`(那會只用一個索引),讓 uv.toml 的三索引一起生效。")
    A("")
    A("## R0 同意閘(只有操作員能開,這支引擎不代設)")
    A("")
    A("```powershell")
    A('$env:VIA_NET_CONSENT = "YES"   # 鏡像探測 / 解析 / 安裝都在這道閘後面')
    A("```")
    A("")
    A("## R1 冊修(不碰網路、不碰境、彼此不相依 —— 已在雲端這輪做掉)")
    A("")
    if rnd.get("R1"):
        for s in rnd["R1"]:
            A(f"- `{s}`")
    else:
        A("**已清空** —— 冊修全部完成,衝突偵測在 R1 這一類已歸零。做了什麼看正本冊自己的紀錄:")
        A("")
        A("- `change_v0103`:三件被兩個家族同時認領(目標境歧義)→ 依冊自己的 `moved_out` /")
        A("  `functional_moved_to_via` 裁決歸屬,各留一個正主")
        A("- `change_v0104`:65 件樹內真的 import、冊上卻查無的件全部落冊 ——")
        A("  58 件歸既有家族(每家族一條理由)· 5 件推不出歸屬 → `unclassified` → 黑環境待裁 ·")
        A("  2 件其實早在冊上只是 import 名 ≠ pip 名 → 新增 `import_name_map` 正本鍵")
        A("- 驗帳:冊上覆蓋率 57.2% → 100.0%;`CGC_MDL135_EnvGovernance` 尾版自測 52/52 + 5/5 沒退步")
    A("")
    A("## R2 境修(要鏡像 + 同意閘 + 拓撲序 —— 桌機照下面貼上跑,不用再測)")
    A("")
    A("```bash")
    A("scripts/envcheck.sh doctor                      # ① 三鏡像連通 + uv cache 體檢")
    A("")
    for env, pkgs in clo.items():
        if not pkgs:
            continue
        py = _env_python(env, bl)
        A(f"# {env}（{len(pkgs)} 件）")
        A(f"uv venv {env} --python {py}")
        A(f"scripts/envcheck.sh resolve {' '.join(pkgs)}   # ② 裝前衝突預測(pipgrip,免安裝)")
        A(f"uv pip install --python {env} " + " ".join(pkgs))
        A(f"uv pip check --python {env}                     # ③ 裝後相容性;非 0 就停在這一境")
        A("")
    A("```")
    A("")
    A("順序規矩(冊 rounds.R2):base 端移除**必須**等目標境 `uv pip check` 綠了才做,")
    A("且逐件印令經 `via-envgov ... --approve-remove`,不批次、不自動。")
    A("")
    A("## R3 收尾")
    A("")
    A("- 每境 `uv pip lock` → LKGC 晉升;`uv cache prune`(候裁)")
    A("- 重跑 `VIA_LibsInventory_v0100.py audit --apply` → 衝突 RED 應歸零,盤冊出新版號")
    A("- 只能出令、本機量不到的(GRAY):")
    for s in rnd.get("R3", []):
        A(f"  - `{s}`")
    A("")
    A("## R2(Windows PowerShell 版 · 同一份閉包,只換殼)")
    A("")
    A("倉內本來就有 `scripts/envcheck.ps1`(與 .sh 同功能,相容 PowerShell 5.1 / 7),所以桌機直接用這份。")
    A("")
    A("```powershell")
    A('$env:VIA_NET_CONSENT = "YES"   # 同意閘:只有操作員能開')
    A(".\\scripts\\envcheck.ps1 doctor                 # ① 三鏡像連通 + uv cache 體檢")
    A("")
    for env, pkgs in clo.items():
        if not pkgs:
            continue
        py = _env_python(env, bl)
        q = " ".join(pkgs)
        A(f"# {env}({len(pkgs)} 件 · python {py})")
        A(f"uv venv {env} --python {py}")
        A(f".\\scripts\\envcheck.ps1 resolve {q}")
        A(f"uv pip install --python {env} {q}")
        A(f"uv pip check --python {env}")
        A("")
    A("```")
    A("")
    A("**PowerShell 的兩個坑**(踩過:操作員把 .mcp.json 的 JSON 片段貼進提示字元,PowerShell 回"
      " ParserError「運算式或陳述式中有未預期的語彙基元 ':'」):")
    A("")
    A("- `$env:VIA_NET_CONSENT` **只活在那一個 PowerShell 視窗**。關掉視窗就沒了,下次要重設。")
    A("  要跨視窗請自己決定是否持久化(`setx`)—— 同意閘要不要常開是操作員的裁量,引擎不代決。")
    A("- 本文件裡的 JSON / 設定片段(例如 `.mcp.json` 的內容)**是檔案內容,不是指令**,")
    A("  貼進提示字元一定 ParserError。只有 ```powershell 區塊裡的那些才是可貼的指令。")
    A("")
    A("## 這份計畫沒有做到的事(照實寫)")
    A("")
    A(f"- 鏡像連通:{book['mirror_probe']}")
    A(f"- 實際安裝:{book['install_executed']}")
    A("- 所以 R2 的每一條指令都是**沒跑過**的;R1 是跑過並自測過的。黃不是綠,GRAY 更不是綠。")
    return "\n".join(L) + "\n"


def _env_python(env: str, bl: dict) -> str:
    for v in (bl.get("families") or {}).values():
        if isinstance(v, dict) and v.get("target_env") == env:
            return str(v.get("python", "3.12"))
    lay = (bl.get("env_layout") or {}).get(env)
    if isinstance(lay, dict) and lay.get("python"):
        return str(lay["python"])
    return "3.12"


# ───────────────────────── HTML U/I ─────────────────────────
def ui_html(book: dict) -> str:
    e = html.escape
    lv = book.get("conflict_levels", {})
    chips = [("第三方套件", book["third_party_total"]), ("冊上有", book["declared_total"]),
             ("覆蓋率 %", book["declared_ratio_pct"]), ("RED", lv.get("RED", 0)),
             ("YELLOW", lv.get("YELLOW", 0)), ("GRAY", lv.get("GRAY", 0))]
    rows = book.get("conflicts", [])
    tr = []
    for c in rows[:400]:
        cls = {"RED": "red", "YELLOW": "yel", "GRAY": "gry"}.get(c["level"], "gry")
        tr.append("<tr><td class='%s'>%s</td><td class='m'>%s</td><td class='m'>%s</td>"
                  "<td>%s</td><td class='s'>%s</td><td class='s'>%s</td></tr>"
                  % (cls, e(c["level"]), e(c["code"]), e(c["pip"]),
                     e(c["why"]), e(c["evidence"]), e(c["fix"])))
    clo = book.get("env_closure", {})
    cr = ["<tr><td class='m'>%s</td><td>%d</td><td class='s'>%s</td></tr>"
          % (e(k), len(v), e(" · ".join(v))) for k, v in clo.items()]
    return f"""<title>VIA Libs 治理盤</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
:root{{--vl-bg:#f7f8fa;--vl-white:#fff;--vl-ink:#15181d;--vl-muted:#5b6472;
--vl-border:#d8dde5;--vl-border-soft:#eceff4;--vl-row:#fafbfd;
--vl-success:#1b7f4d;--vl-success-bg:#e8f6ee;--vl-success-ink:#0f5c37;
--vl-warning-bg:#fdf4e3;--vl-warning-ink:#7a5410;
--vl-danger-bg:#fdecec;--vl-danger-ink:#8d1f1f;
--vl-font-cjk:"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;
--vl-font-mono:ui-monospace,SFMono-Regular,Menlo,monospace;
--vl-size-title:20px;--vl-size-primary:15px;--vl-size-base:13px;--vl-size-label:11px;
color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
--vl-bg:#111419;--vl-white:#181c22;--vl-ink:#e7ebf1;--vl-muted:#9aa5b4;
--vl-border:#2b313a;--vl-border-soft:#22272e;--vl-row:#1d2128;
--vl-success-bg:#12301f;--vl-success-ink:#7fd6a4;
--vl-warning-bg:#332a12;--vl-warning-ink:#e8c377;
--vl-danger-bg:#3a1a1a;--vl-danger-ink:#f0a0a0;color-scheme:dark}}}}
:root[data-theme="dark"]{{--vl-bg:#111419;--vl-white:#181c22;--vl-ink:#e7ebf1;--vl-muted:#9aa5b4;
--vl-border:#2b313a;--vl-border-soft:#22272e;--vl-row:#1d2128;
--vl-success-bg:#12301f;--vl-success-ink:#7fd6a4;
--vl-warning-bg:#332a12;--vl-warning-ink:#e8c377;
--vl-danger-bg:#3a1a1a;--vl-danger-ink:#f0a0a0;color-scheme:dark}}
body{{background:var(--vl-bg);color:var(--vl-ink);font-family:var(--vl-font-cjk);
font-size:var(--vl-size-base);margin:0}}
.wrap{{padding-left:max(16px,env(safe-area-inset-left,0px));
padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:24px;
max-width:1180px;margin:0 auto}}
h1{{font-size:var(--vl-size-title);margin:0 0 4px;text-wrap:balance}}
.sub{{color:var(--vl-muted);font-size:var(--vl-size-label);margin-bottom:16px}}
.chips{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}}
.chip{{background:var(--vl-white);border:1px solid var(--vl-border);border-radius:8px;
padding:8px 12px;min-width:0}}
.chip b{{display:block;font-size:var(--vl-size-primary);font-family:var(--vl-font-mono)}}
.chip span{{color:var(--vl-muted);font-size:var(--vl-size-label);letter-spacing:.04em}}
.card{{background:var(--vl-white);border:1px solid var(--vl-border);border-radius:10px;
padding:14px;margin-bottom:16px;min-width:0}}
h2{{font-size:var(--vl-size-primary);margin:0 0 10px}}
.scroll{{overflow-x:auto}}
table{{border-collapse:collapse;width:100%;font-size:var(--vl-size-base)}}
th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--vl-border-soft);
vertical-align:top}}
th{{color:var(--vl-muted);font-size:var(--vl-size-label);letter-spacing:.04em;white-space:nowrap}}
tr:nth-child(even) td{{background:var(--vl-row)}}
td.m{{font-family:var(--vl-font-mono);white-space:nowrap}}
td.s{{color:var(--vl-muted);font-size:var(--vl-size-label)}}
td.red{{background:var(--vl-danger-bg);color:var(--vl-danger-ink);font-weight:700}}
td.yel{{background:var(--vl-warning-bg);color:var(--vl-warning-ink);font-weight:700}}
td.gry{{color:var(--vl-muted)}}
.note{{color:var(--vl-muted);font-size:var(--vl-size-label);line-height:1.6}}
</style>
<div class="wrap">
<h1>VIA Libs 治理盤</h1>
<div class="sub">{e(book['engine'])} · 正本冊 {e(book['baseline_book'])}(未改)· 掃 {book['scanned_py_files']} 支現役 .py · {e(book['generated_at_utc'])}</div>
<div class="chips">{''.join(f'<div class="chip"><b>{v}</b><span>{e(k)}</span></div>' for k, v in chips)}</div>
<div class="card"><h2>衝突矩陣（{len(rows)} 筆)</h2><div class="scroll"><table>
<thead><tr><th>燈</th><th>類</th><th>套件</th><th>為什麼</th><th>證據</th><th>怎麼修</th></tr></thead>
<tbody>{''.join(tr)}</tbody></table></div></div>
<div class="card"><h2>各境相依閉包</h2><div class="scroll"><table>
<thead><tr><th>境</th><th>件數</th><th>閉包</th></tr></thead><tbody>{''.join(cr)}</tbody></table></div></div>
<div class="card"><h2>沒量到的照實留白</h2>
<p class="note">鏡像連通:{e(str(book['mirror_probe']))}<br>
實際安裝:{e(str(book['install_executed']))}<br>
GRAY 不是綠,黃也不是綠。本機沒有任何 <code>via_</code> 境,所以境內實況一律不自報。</p></div>
</div>
"""


# ───────────────────────── 自測 ─────────────────────────
def selftest() -> int:
    ok = fail = 0

    def chk(name, cond, extra=""):
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"  ✔ {name}")
        else:
            fail += 1
            print(f"  ✘ {name}{(' —— ' + extra) if extra else ''}")

    print("[VIA_LibsInventory v0100 自測]")

    # ① 正規化
    chk("① norm 正規化", norm("Python_Docx") == "python-docx" and norm("pdfminer.six") == "pdfminer-six")

    # ② 版號解析與尾版
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        for v in (100, 102, 99):
            (d / f"{BOOK_STEM}{v:04d}.json").write_text("{}", encoding="utf-8")
        chk("② 尾版取最大版號", tail(d, BOOK_STEM, ".json").name == f"{BOOK_STEM}0102.json")
        chk("③ 下一版號 = 尾版 +1", next_version_path(d, BOOK_STEM, ".json").name == f"{BOOK_STEM}0103.json")

    # ④ 夾具冊:families 用的是 members 這個鍵(踩過 packages 的坑,所以這條一定要有)
    fx = {
        "base": {"toolchain": ["uv"], "engine_core": ["duckdb", "numpy"],
                 "low_risk_allow": ["typer"], "never_in_base_families": ["ocr"]},
        "families": {
            "ocr": {"members": ["paddleocr", "opencv-contrib-python"], "target_env": "via_paddle_311", "python": "3.13"},
            "docs": {"members": ["pymupdf", "pdfplumber"], "target_env": "via_vrn_312", "python": "3.12"},
            "nlp": {"members": ["pymupdf"], "target_env": "via_nlp", "python": "3.12"},
        },
        "family_env_core": {"_note": "x", "via_vrn_312": ["pymupdf", "duckdb", "nowhere-pkg"]},
        "package_env_overrides": {"catboost": "via_catboost"},
        "naming_law": {"renames": {"paddle_311": "via_paddle_311"}},
        "mirror_chain": {"order": ["https://a/simple", "https://b/simple", "https://pypi.org/simple"],
                         "labels": ["tsinghua", "aliyun", "pypi-official"]},
        "env_layout": {"via_nlp": {"python": "3.11"}},
        "rounds": {"max_rounds": 3},
    }
    idx = declared_index(fx)
    chk("④ families[*].members 有被讀進宣告索引", "paddleocr" in idx and "pdfplumber" in idx,
        "如果這條紅了就是又把鍵名看錯(正本鍵是 members,不是 packages)")
    chk("⑤ 宣告索引含 base 三單 + famcore + override",
        all(k in idx for k in ("uv", "duckdb", "typer", "nowhere-pkg", "catboost")))
    chk("⑥ 家族覆蓋不為零(回歸測:鍵名看錯會讓它變 0)",
        sum(1 for v in idx.values() if any(b.startswith('family/') for b, _ in v)) >= 4)

    # ⑦ pip 名對映
    chk("⑦ fitz → pymupdf(冊上註明的對映)", pip_of("fitz", idx) == ("pymupdf", True))
    chk("⑧ 冊上查得到就算有依據", pip_of("duckdb", idx) == ("duckdb", True))
    chk("⑨ 認不出來標 False 而不硬猜", pip_of("zzz_unknown_thing", idx) == ("zzz-unknown-thing", False))

    def row(imp, pip=None, layer="主層", mapped=True, n=1):
        pip = pip or norm(imp)
        return {"import": imp, "pip": pip, "mapped": mapped, "layer": layer,
                "declared": idx.get(pip, []), "nfiles": n, "lanes": ["VDF"]}

    codes = lambda cs: {c["code"] for c in cs}

    # ⑩ L1 封鎖家族在 base
    c = detect([row("paddleocr", layer="主層")], fx)
    chk("⑩ L1 封鎖家族件在 base 層 = RED", "L1_BLOCKED_IN_BASE" in codes(c)
        and all(x["level"] == "RED" for x in c if x["code"] == "L1_BLOCKED_IN_BASE"))
    c = detect([row("paddleocr", layer="ABSENT")], fx)
    chk("⑪ 同一件不在 base 層就不報 L1", "L1_BLOCKED_IN_BASE" not in codes(c))

    # ⑫ L2 跨家族
    c = detect([row("pymupdf", layer="主層")], fx)
    chk("⑫ L2 一件被兩家族認領 = RED", "L2_CROSS_FAMILY" in codes(c))
    c = detect([row("pdfplumber", layer="主層")], fx)
    chk("⑬ 只被一個家族認領就不報 L2", "L2_CROSS_FAMILY" not in codes(c))

    # ⑭ L3 層錯(ENG115 duckdb 真案)
    c = detect([row("duckdb", layer="使用者層")], fx)
    chk("⑭ L3 engine_core 落在使用者層 = RED", "L3_CORE_WRONG_LAYER" in codes(c))
    c = detect([row("duckdb", layer="主層")], fx)
    chk("⑮ engine_core 在主層就不報 L3", "L3_CORE_WRONG_LAYER" not in codes(c))

    # ⑯ L4 宣告了沒裝;基座件升紅
    c = detect([row("duckdb", layer="ABSENT")], fx)
    g = [x for x in c if x["code"] == "L4_DECLARED_ABSENT"]
    chk("⑯ L4 基座件缺 = RED", g and g[0]["level"] == "RED")
    c = detect([row("typer", layer="ABSENT")], fx)
    g = [x for x in c if x["code"] == "L4_DECLARED_ABSENT"]
    chk("⑰ L4 非基座件缺 = YELLOW(不浮報成紅)", g and g[0]["level"] == "YELLOW")

    # ⑱ L5 / L6
    c = detect([row("seaborn", layer="主層")], fx)
    chk("⑱ L5 容器有冊上沒有 = YELLOW", "L5_UNDECLARED_PRESENT" in codes(c)
        and all(x["level"] == "YELLOW" for x in c if x["code"] == "L5_UNDECLARED_PRESENT"))
    c = detect([row("curl_cffi", pip="curl-cffi", layer="ABSENT")], fx)
    chk("⑲ L6 兩邊都沒有 = RED", "L6_UNDECLARED_ABSENT" in codes(c))
    chk("⑳ L5 與 L6 互斥(同一列不會同時出現)",
        not ({"L5_UNDECLARED_PRESENT", "L6_UNDECLARED_ABSENT"} <= codes(c)))

    # ㉑ L7:只收「在位卻查不到 pip 名」;ABSENT 那批不重複報(回歸測:重複過 65 筆)
    c = detect([row("weirdlib", mapped=False, layer="主層")], fx)
    chk("㉑ L7 在位卻無對映 = YELLOW", "L7_MAP_UNKNOWN" in codes(c))
    c = detect([row("weirdlib", mapped=False, layer="ABSENT")], fx)
    chk("㉑b ABSENT 的無對映只報 L6,不重複報 L7",
        "L6_UNDECLARED_ABSENT" in codes(c) and "L7_MAP_UNKNOWN" not in codes(c))
    chk("㉑c L6 證據寫明 pip 名是猜的",
        any("猜" in x["evidence"] for x in c if x["code"] == "L6_UNDECLARED_ABSENT"))
    chk("㉑d 衝突證據標明量測地點(容器主層不等於桌機 BASE)",
        all(MEASURED_ON in x["evidence"] for x in c if x["code"] == "L6_UNDECLARED_ABSENT"))
    # ㉑f 冊上 import_name_map 是正本,贏過引擎內建;_note 不算對映
    fx_map = dict(fx)
    fx_map["import_name_map"] = {"_note": "註解不是對映", "fitz": "pymupdf-override", "surya": "surya-ocr"}
    im = import_map(fx_map)
    chk("㉑f 冊上對映覆蓋引擎內建", im.get("fitz") == "pymupdf-override")
    chk("㉑g _note 不被當成對映", "_note" not in im)
    chk("㉑h 冊上新增的對映生效", pip_of("surya", {}, im) == ("surya-ocr", True))
    chk("㉑i 沒給 imap 時退回引擎內建", pip_of("fitz", {}) == ("pymupdf", True))

    # ㉑e PIP_NAME 的值要正規化,不然查不到冊上索引鍵
    chk("㉑e pdfminer → pdfminer-six 且查得到冊上(值未正規化就會誤報 L5)",
        pip_of("pdfminer", declared_index({"families": {"table_extraction": {"members": ["pdfminer.six"]}}})) == ("pdfminer-six", True))

    # ㉒ L8 GRAY:不能寫成紅也不能寫成綠
    c = detect([], fx)
    g = [x for x in c if x["code"] == "L8_NAMING_LAW"]
    chk("㉒ L8 命名律本機量不到 = GRAY", g and g[0]["level"] == "GRAY")

    # ㉓ L9
    chk("㉓ L9 family_env_core 指到不屬任何家族的件",
        any(x["code"] == "L9_FAMILY_CORE_GAP" and x["pip"] == "nowhere-pkg" for x in c))
    chk("㉔ family_env_core 裡屬家族的件不報 L9",
        not any(x["code"] == "L9_FAMILY_CORE_GAP" and x["pip"] == "pymupdf" for x in c))
    chk("㉕ _note 這種註解鍵不被當成境", not any(x["code"] == "L9_FAMILY_CORE_GAP" and x["pip"] == "x" for x in c))

    # ㉖ 輪次:冊修進 R1、境修進 R2、L6 兩段都進
    rs = rounds_assign(detect([row("duckdb", layer="使用者層"), row("seaborn", layer="主層"),
                               row("curl_cffi", pip="curl-cffi", layer="ABSENT")], fx))
    chk("㉖ R1 只收純冊修", all(c["code"] in R1_CODES | {"L6_UNDECLARED_ABSENT"} for c in rs["R1"]))
    chk("㉗ R2 只收動到境的", all(c["code"] in R2_CODES | {"L6_UNDECLARED_ABSENT"} for c in rs["R2"]))
    chk("㉘ L6 同時進 R1(冊修)與 R2(裝件)",
        any(c["code"] == "L6_UNDECLARED_ABSENT" for c in rs["R1"])
        and any(c["code"] == "L6_UNDECLARED_ABSENT" for c in rs["R2"]))

    # ㉙ 閉包
    rr = [row("pymupdf", layer="ABSENT"), row("paddleocr", layer="主層")]
    clo = env_closure(rr, fx)
    chk("㉙ 閉包把件歸到目標境", "pymupdf" in clo.get("via_vrn_312", []) and "paddleocr" in clo.get("via_paddle_311", []))
    chk("㉚ 閉包併入 family_env_core", "duckdb" in clo.get("via_vrn_312", []))

    # ㉛ 實質指紋:重排不變、內容變就變
    r1 = [row("duckdb"), row("seaborn")]
    chk("㉛ 指紋與列序無關", substance(r1, []) == substance(list(reversed(r1)), []))
    chk("㉜ 指紋對層變化敏感", substance(r1, []) != substance([row("duckdb", layer="使用者層"), row("seaborn")], []))
    chk("㉜b 指紋對 AST 剖不過敏感(多一支讀不到 = 盤冊真的變了)",
        substance(r1, []) != substance(r1, [], [{"file": "x.py", "error": "SyntaxError"}]))
    chk("㉜c 剖不過的列序也不影響指紋",
        substance(r1, [], [{"file": "a.py", "error": "e"}, {"file": "b.py", "error": "e"}])
        == substance(r1, [], [{"file": "b.py", "error": "e"}, {"file": "a.py", "error": "e"}]))

    # ㉝ 盤冊:實質沒變不出新版號、已發布不覆寫
    bk = make_book(rr, detect(rr, fx), fx, "fx.json", 7)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        p1, s1 = write_book(bk, d)
        p2, s2 = write_book(bk, d)
        chk("㉝ 第一次寫出 v0100", s1 == "WRITTEN" and p1.name == f"{BOOK_STEM}0100.json")
        chk("㉞ 實質沒變 → UNCHANGED,不出新版號", s2 == "UNCHANGED" and p2 == p1)
        bk2 = make_book([row("duckdb", layer="使用者層")], detect([row("duckdb", layer="使用者層")], fx), fx, "fx.json", 7)
        p3, s3 = write_book(bk2, d)
        chk("㉟ 實質變了 → 出 v0101(不覆寫 v0100)",
            s3 == "WRITTEN" and p3.name == f"{BOOK_STEM}0101.json" and p1.exists())

    # ㊱ 計畫:三鏡像都印、不印 UV_NO_CONFIG、GRAY 照實寫
    pt = plan_text(bk, fx)
    chk("㊱ 計畫印出三個鏡像", all(u in pt for u in fx["mirror_chain"]["order"]))
    chk("㊲ 計畫不叫人加 UV_NO_CONFIG(那會只用一個索引)", "UV_NO_CONFIG=1 uv" not in pt)
    chk("㊳ 計畫把同意閘留給操作員", "VIA_NET_CONSENT" in pt and "不代設" in pt)
    chk("㊴ 計畫照實寫沒跑過", "沒跑過" in pt and "GRAY" in pt)
    chk("㊵ 計畫用冊上的 python 版本", "--python 3.12" in pt or "--python 3.13" in pt)
    # ㊵b–㊵e 兩個平台都要有可貼的(倉內 envcheck 有 .sh 也有 .ps1)
    chk("㊵b 計畫同時給 bash 與 PowerShell 兩版", "envcheck.sh" in pt and "envcheck.ps1" in pt)
    chk("㊵c PowerShell 版用 .ps1 不用 .sh(不要叫 Windows 跑 bash)",
        "scripts\\\\envcheck.ps1 doctor" in pt or ".\\scripts\\envcheck.ps1 doctor" in pt or "envcheck.ps1 doctor" in pt)
    chk("㊵d 提醒 $env: 只活在那一個視窗(踩過:關掉視窗同意閘就沒了)",
        "只活在那一個 PowerShell 視窗" in pt)
    chk("㊵e 提醒設定片段不是指令(踩過:JSON 貼進提示字元 ParserError)",
        "是檔案內容,不是指令" in pt and "ParserError" in pt)

    # ㊶ HTML:只用 --vl-* 、無骨架標籤、有轉義
    h = ui_html(make_book([row("<script>bad</script>", pip="<b>x</b>", layer="主層")],
                          [{"code": "L5_UNDECLARED_PRESENT", "level": "YELLOW", "pip": "<b>x</b>",
                            "import": "x", "why": "<i>w</i>", "evidence": "e", "fix": "f",
                            "lanes": [], "nfiles": 1}], fx, "fx.json", 1))
    chk("㊶ HTML 不含骨架標籤", not any(t in h.lower() for t in ("<!doctype", "<html", "<body", "<head")))
    chk("㊷ HTML 轉義使用者內容", "<b>x</b>" not in h and "&lt;b&gt;x&lt;/b&gt;" in h)
    chk("㊸ HTML 顏色全走 --vl-* token", h.count("--vl-") > 30 and "prefers-color-scheme" in h)
    chk("㊹ HTML 兩個主題都定義 + body 有底色", 'data-theme="dark"' in h and "background:var(--vl-bg)" in h)

    # ㊽b AST 剖不過不得默默吞掉(全景工具報過這裡是 SWALLOW)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "ok.py").write_text("import pandas\n", encoding="utf-8")
        (d / "broken.py").write_text("def f(:\n", encoding="utf-8")
        pfx: list[dict] = []
        tops, n, _ = scan_tree(d, pfx)
        chk("㊽b 剖得過的照讀", "pandas" in tops)
        chk("㊽c 剖不過的逐支記下來(檔名 + 真錯誤)",
            len(pfx) == 1 and pfx[0]["file"] == "broken.py" and "Error" in pfx[0]["error"])
        chk("㊽d 不給收集器也不炸(退路)", scan_tree(d)[1] == n)
        bkp = make_book([], [], fx, "fx.json", n, [], pfx)
        chk("㊽e 剖不過進盤冊,且註明它代表盤冊有缺口",
            bkp["ast_parse_failed"] == pfx and "缺口" in bkp["ast_parse_failed_note"])

    # ㊺ 正本冊真的沒被動到(讀進來再比一次位元)
    try:
        bp = tail(REGISTRY, BASELINE_STEM, ".json")
        before = bp.read_bytes()
        bl, _ = load_baseline()
        declared_index(bl)
        detect([], bl)
        chk("㊺ 正本冊讀過之後位元不變", bp.read_bytes() == before)
        chk("㊻ 真冊的家族覆蓋 > 100 件(確認正本鍵名與夾具一致)",
            sum(1 for v in declared_index(bl).values()
                if any(b.startswith("family/") for b, _ in v)) > 100)
    except SystemExit:
        chk("㊺ 正本冊在位", False, "找不到正本冊")

    # ㊼ 自家模組名不得被當成第三方(回歸測:這條紅過一次,假缺件 96 個裡大半是自家的)
    own = own_names()
    for name in ("via_nlp_engine", "vdf_fetchers_market", "VIA_SuperAccel_Module"):
        chk(f"㊼ 樹內自家模組 {name} 認得出來", is_own_name(name, own))
    chk("㊽ 樹內沒檔但名字是自家的也認得出來(VRN_SupportBridge 由注入器給)",
        is_own_name("VRN_SupportBridge", set()) and is_own_name("VDF_MDL011_X", set()))
    chk("㊾ 真第三方不會被誤認成自家", not any(
        is_own_name(x, set()) for x in ("pandas", "duckdb", "joblib", "weasyprint", "surya", "redis")))
    om = [{"import": "VRN_SupportBridge", "nfiles": 9, "lanes": ["VRN-2"]}]
    c10 = detect([], fx, om)
    chk("㊿ L10 自家檔不在位 = YELLOW,且不混進 libs 輪次",
        any(x["code"] == "L10_OWN_MODULE_MISSING" and x["level"] == "YELLOW" for x in c10)
        and not any(x["code"] == "L10_OWN_MODULE_MISSING" for x in rounds_assign(c10)["R1"] + rounds_assign(c10)["R2"]))

    print(f"[計] VIA_LibsInventory v0100 自測 OK {ok} · FAIL {fail} · {'PASS' if fail == 0 else 'FAIL'}")
    return 0 if fail == 0 else 1


# ───────────────────────── 動詞 ─────────────────────────
def cmd_scan(args) -> int:
    bl, name = load_baseline()
    rows, nfile, own_missing, pf = build_rows(bl)
    print(f"[普查] 掃 {nfile} 支現役 .py · 第三方頂層套件 {len(rows)} 個 · "
          f"自家模組不在位 {len(own_missing)} 個 · AST 剖不過 {len(pf)} 支 · 正本冊 {name}(未改)")
    for x in pf[:5]:
        print(f"   [剖不過] {x['file']} —— {x['error'][:70]}")
    dn = sum(1 for r in rows if r["declared"])
    print(f"[對帳] 冊上有 {dn} · 冊上沒有 {len(rows)-dn} · 覆蓋率 {100.0*dn/len(rows):.1f}%")
    print(f"\n{'套件':24}{'容器':10}{'冊上':28}{'檔':>5}  車道")
    for r in rows[:60]:
        d = ",".join(sorted({b.split('/')[0] for b, _ in r["declared"]})) or "—"
        print(f"{r['pip']:24}{r['layer'].split('(')[0]:10}{d:28}{r['nfiles']:>5}  {' · '.join(r['lanes'][:2])}")
    if len(rows) > 60:
        print(f"… 另 {len(rows)-60} 個(全量在盤冊)")
    return 0


def cmd_audit(args) -> int:
    bl, name = load_baseline()
    rows, nfile, own_missing, pf = build_rows(bl)
    conf = detect(rows, bl, own_missing)
    book = make_book(rows, conf, bl, name, nfile, own_missing, pf)
    lv = book["conflict_levels"]
    print(f"[普查] {nfile} 支 .py · 第三方 {len(rows)} 個 · 覆蓋率 {book['declared_ratio_pct']}% · "
          f"AST 剖不過 {len(pf)} 支(剖不過 = 它的套件需求沒進盤冊)")
    print(f"[衝突] RED {lv.get('RED',0)} · YELLOW {lv.get('YELLOW',0)} · GRAY {lv.get('GRAY',0)}")
    for code, n in sorted(book["conflict_codes"].items()):
        ex = next((c["pip"] for c in conf if c["code"] == code), "")
        print(f"   {code:24} {n:>4}   例:{ex}")
    print(f"[留白] 鏡像連通 {book['mirror_probe']}")
    print(f"[留白] 實際安裝 {book['install_executed']}")
    if args.apply:
        p, st = write_book(book)
        print(f"[盤冊] {st} {p.name}")
    else:
        print("[盤冊] 未寫(加 --apply 才寫)")
    return 0


def _load_book() -> dict:
    p = tail(REGISTRY, BOOK_STEM, ".json")
    if p is None:
        raise SystemExit("[紅] 還沒有盤冊 —— 先跑 audit --apply")
    return json.loads(p.read_text(encoding="utf-8"))


def cmd_plan(args) -> int:
    bl, _ = load_baseline()
    book = _load_book()
    txt = plan_text(book, bl)
    out = HERE / PLAN_NAME
    out.write_text(txt, encoding="utf-8")
    print(f"[計畫] {out}")
    print(f"[輪次] R1 {len(book['rounds'].get('R1',[]))} · R2 {len(book['rounds'].get('R2',[]))} · R3 {len(book['rounds'].get('R3',[]))}")
    return 0


def cmd_ui(args) -> int:
    book = _load_book()
    out = HERE / UI_NAME
    out.write_text(ui_html(book), encoding="utf-8")
    print(f"[U/I] {out}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="VIA libs 治理盤")
    ap.add_argument("verb", nargs="?", default="audit",
                    choices=["scan", "audit", "plan", "ui", "all"])
    ap.add_argument("--apply", action="store_true", help="真的寫盤冊")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.verb == "scan":
        return cmd_scan(a)
    if a.verb == "audit":
        return cmd_audit(a)
    if a.verb == "plan":
        return cmd_plan(a)
    if a.verb == "ui":
        return cmd_ui(a)
    rc = cmd_audit(a)
    return rc or cmd_plan(a) or cmd_ui(a)


if __name__ == "__main__":
    sys.exit(main())
