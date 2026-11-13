#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_VCGC ToolMatrix v0100 — VCGC 工具矩陣:中央管理(MDL)· 省 Token / 支援(SUP)· 整合進來(INT)· 收尾,一頁 HTML,隨時自動重出。

操作員 2026-11-13 原文(節):「矩陣顯示目前VCGC本身中央控管功能及節省TOKEN工具所有工具即被整合進來的所有工具
為了將自動隨時更新於HTML矩陣化管理來進行使用」「VCGC節省或支援工具VIA_VCGC_SUP001_ VCGC本身中央管理VIA_VCGC_MDL001
相同要有版本號 依照命名規定」「將我指令視覺鎖定模板整合進來併用它來顯示VCGC進行VCGC收尾」(政策 L129)

畫面一律走操作員的視覺鎖定 U/I(docs/handoff/ai/VIA_VisualLock_v* 尾版:token 從鎖定正本抽、不手抄),
出頁後當場過鎖定閘(token sha · 不寫死色 · 0 外連 · 手機側邊槽);閘紅 = 本頁不算完成。

動詞(他系統一律只讀;本支只寫自己的輸出與命名帳):
  build [--no-ast] [--quiet] [--out 夾]   → VIA_Reports/vcgc/VCGC_ToolMatrix_latest.html / .json(.gitignore 內;每輪重出)
  naming [--apply]                       命名對照:VIA_VCGC_<MDL|SUP>###_<英文名>。乾跑列 已發 · 擬發 · 留白 · 衝突;
                                         --apply 只把「無衝突且已有中央編號」的只增寫進 VIA_VCGC_ToolNaming_v0100.jsonl
  check                                  獨立性 / 衝突檢(他系統釘 VCGC 版 · VCGC 釘他系統版 · TA-Lib 使用 · 命名衝突);有紅 rc 1
  watch [--interval 秒]                  VCGC 冊 / 收據有變就重出 build(本機背景用;Ctrl-C 停)
  --selftest
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
_STEM = re.match(r"(.+?)_v(\d{4})$", Path(__file__).stem)
NAME = _STEM.group(1) if _STEM else Path(__file__).stem
VERSION = "v" + (_STEM.group(2) if _STEM else "0000")
OUT = VIA / "VIA_Reports" / "vcgc"
HTML_NAME, JSON_NAME = "VCGC_ToolMatrix_latest.html", "VCGC_ToolMatrix_latest.json"
LEDGER_NAME = "VIA_VCGC_ToolNaming_v0100.jsonl"
BOOK_VERSION = "v0100"

# L77 掃描根排除:收容正本 · 退役 · 備份 · 影子 · 報表 · 測試夾不是活樹
EXCL_PARTS = ("references/intake", "/intake/", "_superseded", "RetiredEngines", "SCOPE_COPY", "new modules engines",
              "quarantine", "VIA_Reports", "__pycache__", "node_modules", ".git")
EXCL_DIRS = {"backup", "_backup", "tests", "test_logs"}
TEXT_EXT = {".py", ".ps1", ".psm1", ".cmd", ".bat", ".sh", ".json", ".jsonl", ".md", ".txt", ".yml", ".yaml",
            ".toml", ".cfg", ".ini", ".html", ".js"}
CODE_EXT = {".py", ".ps1", ".psm1", ".cmd", ".bat", ".sh"}
MAX_BYTES = 8 * 1024 * 1024

FAM_RX = re.compile(r"^(CGC_MDL\d{3}_[A-Za-z0-9_]+?|VIA_VCGC_(?:MDL|SUP)\d{3,4}_[A-Za-z0-9_]+?)_v(\d{4})\.py$")
NEW_RX = re.compile(r"^VIA_VCGC_(MDL|SUP)(\d{3,4})_([A-Za-z0-9_]+)$")
VER_RX = re.compile(r"_v(\d{3,4})(?:\.[A-Za-z0-9]+)?$")   # .py / .json / .jsonl 冊都認得版號
# 他系統載入 VCGC:釘版檔名(升級後對方停在舊版或失效)= 紅;只用家族名且帶載入字樣 = 黃
PIN_RX = re.compile(r"\b(CGC_MDL\d{3}_[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*?)_v\d{4}\.py")
NAMEREF_RX = re.compile(r"\b(CGC_MDL\d{3}_[A-Za-z0-9]+)")
LOAD_HINT_RX = re.compile(r"import|spec_from_file_location|\.glob\(|run_path|exec\(|subprocess|Popen|\.py\b")
OTHER_PIN_RX = re.compile(r"\b((?:VDF_|VRN2_|VRN_|VQG_|VAP_)[A-Za-z0-9_]+?)_v\d{3,4}\.py")
# TA-Lib:程式碼裡的使用 = 紅;任何文字的出現 = 照實點名(守門 / 法條的必要提及另列)
# .py 的使用 = import / from / talib.X( / 經 subprocess 叫 pip 裝;說明文字裡寫到「pip install TA-Lib」只算出現
# (talib.SMA( 這種大寫函式 / abstract / stream 才算;叫 talib 的清單變數 .append( 不算 —— 區分大小寫)
TALIB_USE_RX = re.compile(r"^[ \t]*(?:import[ \t]+talib\b|from[ \t]+talib\b)|\btalib\.(?:[A-Z][A-Z0-9_]*\s*\(|abstract\b|stream\b)", re.M)
TALIB_PIP_PY_RX = re.compile(r"(?:subprocess|os\.system|check_call|check_output|Popen)[^\n]*\bpip3?\b[^\n]*\bta-?lib\b", re.I | re.M)
TALIB_SH_USE_RX = re.compile(r"^(?![ \t]*(?:#|rem\b|::))[^\n]*\bpip3?\s+install\s+[^\n]*\bta-?lib\b", re.I | re.M)
TALIB_MENTION_RX = re.compile(r"\bta[-_]?lib\b", re.I)
TALIB_GUARD_RX = re.compile(r"(?i)talib|quantguard|policy_laws|constitution|lessons|toolmatrix|ta_lib_policy")
OTHER_SYSTEMS = ("VDF", "VRN-2", "VQG", "VAP")

# 省 Token / 支援工具的判準(看英文名;其餘 = 中央管理 MDL)。每一條都寫理由,操作員可裁定改判。
SUP_RULES = [
    (re.compile(r"^(VIAPanoramaAuditRepair|MCPServer|ShadowMerge)$"), "省 Token 讀檔 · 比對(token 鎖席 · MCP 三動詞 · 影子比對)"),
    (re.compile(r"Accel|BridgeSweeper|SupportBridgeInject|SupportImportAudit|SupportTier|DuckTempHook"), "加速器 / 支援橋"),
    (re.compile(r"^Nlp|NlpLayoutDoor|^Layout(Engine|Codes)$"), "NLP / Layout 支援"),
    (re.compile(r"^Ai(VerbBridge|VerbLadder|ToolPanel|Ops)$"), "AI 平台支援"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def vnum(p) -> int:
    m = VER_RX.search(Path(str(p)).name)
    return int(m.group(1)) if m else -1


def rel(p: Path, via: Path = VIA) -> str:
    try:
        return Path(p).resolve().relative_to(via.resolve()).as_posix()
    except ValueError:
        return str(p)


def tail_of(folder: Path, pattern: str):
    hits = [q for q in folder.glob(pattern) if q.is_file() and vnum(q) >= 0]
    return max(hits, key=vnum) if hits else None


def load_json(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def read_jsonl(p) -> list:
    rows = []
    try:
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                rows.append({"_bad": line[:80]})
    except OSError:
        pass
    return rows


def load_module(path: Path, alias: str):
    spec = importlib.util.spec_from_file_location(alias, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


def english_of(family: str) -> str:
    m = NEW_RX.match(family)
    if m:
        return m.group(3)
    return re.sub(r"^(?:CGC|SUP)_MDL\d{3}_", "", family)


def system_of(r: str) -> str:
    """路徑 / 檔名 → 歸屬系統(L123 分開命名:本倉 VRN_* 是 VRN-2 的底座)。"""
    n = r.rsplit("/", 1)[-1]
    if n.startswith(("CGC_", "VIA_VCGC_")):
        return "VCGC"
    if n.startswith("VRN2_") or "/vrn2_ship/" in r:
        return "VRN-2"
    if n.startswith("VDF_") or r.startswith("functional modules/VDF/"):
        return "VDF"
    if n.startswith("VRN") or r.startswith("functional modules/VRN/"):
        return "VRN-2"
    if n.startswith("VQG_") or "/VQG/" in "/" + r:
        return "VQG"
    if n.startswith("VAP_") or "/VAP/" in "/" + r:
        return "VAP"
    if r.startswith("supportive modules/registry/"):
        return "VCGC"
    return "共用"


def classify(english: str, seat: str = "", declared: str = "", family: str = "") -> tuple:
    if declared:
        return declared, "檔名自帶類別(新命名)"
    if seat:
        return "SUP", "VCGC 工具鎖冊席位 %s" % seat
    if family.startswith("SUP_MDL"):
        return "SUP", "支援模組(SUP_MDL 前綴 · VCGC 測站在用)"
    for rx, why in SUP_RULES:
        if rx.search(english):
            return "SUP", why
    return "MDL", "中央管理(預設;不屬省 Token / 支援四類)"


# ---------------------------------------------------------------- 來源(全部只讀)
def number_book(via: Path = VIA) -> dict:
    """中央編號 MDL 冊(CGC_MDL237):家族 → 這一族在冊上的每一列(版本 · 來源 · 號 · 時間)。
    挑號用 reg_for():**尾版實際路徑**那一列優先 —— 收容夾 / 別處同名高版本的副本不能冒充活樹那支的號。"""
    out = {}
    for row in read_jsonl(via / "supportive modules" / "registry" / "VIA_NumberBooks" / "VIA_NumberBook_MDL_v0100.jsonl"):
        name = row.get("name") or ""
        if not row.get("code"):
            continue
        fam = re.sub(r"_v\d{3,4}$", "", name)
        v = vnum(name) if vnum(name) >= 0 else vnum("x_" + str(row.get("version", "")))
        src = str(row.get("source") or "").split(" · ")[0].strip()
        out.setdefault(fam, []).append({"code": row["code"], "version": row.get("version") or ("v%04d" % v if v >= 0 else ""),
                                        "updated_at": row.get("updated_at", ""), "lamp": row.get("lamp", ""), "_v": v, "source": src})
    return out


def reg_for(fam: str, tail, numbers: dict, via: Path = VIA) -> dict:
    rows = numbers.get(fam) or []
    if not rows:
        return {}
    r_tail = rel(tail, via) if tail else ""
    exact = [x for x in rows if r_tail and x["source"] == r_tail]
    if exact:
        return max(exact, key=lambda x: x["_v"])
    same = [x for x in rows if tail and x["_v"] == vnum(tail) and not any(e in "/" + x["source"] for e in EXCL_PARTS)]
    if same:
        return max(same, key=lambda x: x["_v"])
    live = [x for x in rows if not any(e in "/" + x["source"] for e in EXCL_PARTS) and "/intake" not in x["source"]]
    return max(live, key=lambda x: x["_v"]) if live else {}


def register_view(via: Path = VIA) -> dict:
    """各系統自行登錄、VCGC 檢視:編號冊逐冊數 系統 × 類,最後登錄時間。"""
    view = {}
    folder = via / "supportive modules" / "registry" / "VIA_NumberBooks"
    for p in sorted(folder.glob("VIA_NumberBook_*_v*.jsonl")):
        kind = re.sub(r"^VIA_NumberBook_|_v\d+\.jsonl$", "", p.name).split("_")[0]
        for row in read_jsonl(p):
            sub = row.get("sub") or "?"
            cell = view.setdefault(sub, {}).setdefault(kind, {"n": 0, "last": ""})
            cell["n"] += 1
            at = str(row.get("updated_at") or "")
            if at > cell["last"]:
                cell["last"] = at
    return view


def stations(via: Path = VIA) -> tuple:
    p = tail_of(via / "supportive modules" / "registry", "VIA_VCGC_FunctionInventory_SSOT_v*.json")
    d = load_json(p) if p else None
    by_fam, run_stems = {}, set()
    for s in (d or {}).get("stations", []):
        argv = s.get("argv") or []
        if argv and argv[0] == "run":
            rest, i = argv[1:], 0
            while i < len(rest) and rest[i].startswith("-"):
                i += 2 if rest[i] == "--family" else 1
            if i < len(rest):
                run_stems.add(rest[i])
                by_fam.setdefault(rest[i], []).append(s["id"])
        for dep in s.get("deps") or []:
            m = re.match(r".*/([^/]+?)_v\*\.py$", dep)
            if m and s["id"] not in by_fam.get(m.group(1), []):
                by_fam.setdefault(m.group(1), []).append(s["id"])
    return (p.name if p else ""), by_fam, run_stems


def ledger_last(via: Path = VIA) -> dict:
    out = {}
    for row in read_jsonl(via / "supportive modules" / "registry" / "VIA_VCGC_FunctionLedger_v0100.jsonl"):
        fid = str(row.get("id", ""))
        if fid.startswith("family:"):
            out[fid[7:]] = {"lamp": row.get("lamp", ""), "ts": row.get("ts", ""), "version": row.get("version", ""), "sha16": row.get("sha16", "")}
    return out


def lock_seats(via: Path = VIA) -> dict:
    d = load_json(via / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json") or {}
    seats = {}
    for k, v in d.items():
        if isinstance(v, dict) and v.get("path"):
            p = Path(v["path"])
            if not p.is_absolute():
                p = via.parent / p if (via.parent / p).exists() else via / p
            seats[k] = p
    return seats


def discover(via: Path = VIA) -> tuple:
    """VCGC 自己的工具家族:registry 的 CGC_MDL / VIA_VCGC_* + 工具鎖冊席位 + VCGC 測站在跑的支援件。"""
    reg = via / "supportive modules" / "registry"
    fams, skipped = {}, []
    for p in reg.glob("*.py"):
        m = FAM_RX.match(p.name)
        if not m:
            if p.name.startswith(("CGC_MDL", "VIA_VCGC_")):
                skipped.append(p.name)
                if re.match(r"^CGC_MDL\d{3}_[A-Za-z0-9_]+\.py$", p.name) and not VER_RX.search(p.name):
                    fams.setdefault(p.stem, {"files": [p], "src": "registry", "seat": "", "unversioned": True})
            continue
        f = fams.setdefault(m.group(1), {"files": [], "src": "registry", "seat": ""})
        f["files"].append(p)
    excluded = []
    for seat, p in lock_seats(via).items():
        r = rel(p, via)
        fam = re.sub(r"_v\d{3,4}$", "", p.stem)
        if system_of(r) in OTHER_SYSTEMS:
            excluded.append({"seat": seat, "file": r, "why": "他系統的引擎(%s)· VCGC 只讀,不給 VCGC 名碼(L123)" % system_of(r)})
            continue
        f = fams.setdefault(fam, {"files": [], "src": "seat", "seat": seat})
        f["seat"] = seat
        if p.is_file() and p not in f["files"]:
            f["files"].append(p)
    _src, _by, run_stems = stations(via)
    sm = via / "supportive modules"
    for stem in sorted(run_stems):
        if stem in fams or stem.startswith(("CGC_", "VIA_VCGC_")):
            continue
        hits = [q for q in sm.rglob(stem + "_v*.py") if not any(x in rel(q, via) for x in EXCL_PARTS)]
        if not hits:
            continue
        r = rel(hits[0], via)
        if system_of(r) in OTHER_SYSTEMS:
            continue
        fams[stem] = {"files": hits, "src": "station", "seat": ""}
    for f in fams.values():
        f["tail"] = max(f["files"], key=vnum) if f["files"] else None
        f["versions"] = len(f["files"])
    return fams, sorted(skipped), excluded


def scan_tree(via: Path = VIA, sup_stems=()) -> dict:
    """活樹一次掃完:他系統載入 VCGC(釘版 / 名引)· VCGC 釘他系統版 · TA-Lib 使用與出現 · 活樹家族名。"""
    res = {"files": 0, "skipped_big": 0, "in_pin": {}, "in_name": {}, "out_pin": {}, "talib": [], "live_stems": set(),
           "pairs": [], "seen": [], "out_pin_files": {}, "refs": {}, "sup_use": {}}
    sup_rx = re.compile(r"\b(" + "|".join(sorted((re.escape(x) for x in sup_stems), key=len, reverse=True)) + r")(?:_v\d{3,4}|\b)") if sup_stems else None
    for root, dirs, files in os.walk(via):
        r_root = rel(Path(root), via)
        dirs[:] = [d for d in dirs if d not in EXCL_DIRS and not any(x in (r_root + "/" + d) for x in EXCL_PARTS)]
        for fn in files:
            p = Path(root) / fn
            if p.suffix.lower() not in TEXT_EXT:
                continue
            r = rel(p, via)
            res["seen"].append(r)
            if p.suffix == ".py":
                res["live_stems"].add(re.sub(r"_v\d{3,4}$", "", p.stem))
            try:
                big_ok = r.startswith("supportive modules/registry/") and p.stat().st_size <= 8 * MAX_BYTES   # VCGC 冊夾的大冊照讀(不留盲點)
                if p.stat().st_size > MAX_BYTES and not big_ok:
                    res["skipped_big"] += 1
                    continue
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            res["files"] += 1
            sysname = system_of(r)
            if not DEP_SKIP_RX.search(r) and p.suffix.lower() in (".py", ".ps1", ".psm1", ".cmd", ".json"):
                for name in set(OLDREF_RX.findall(text)):
                    if name != p.name:
                        res["refs"].setdefault(name, set()).add(r)
            if p.suffix == ".py":
                lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]
                if sysname in OTHER_SYSTEMS:
                    if sup_rx is not None:
                        for ln in lines:
                            if LOAD_HINT_RX.search(ln):
                                for m in sup_rx.finditer(ln):
                                    res["sup_use"].setdefault(m.group(1), {}).setdefault(sysname, set()).add(r)
                    for ln in lines:
                        for m in PIN_RX.finditer(ln):
                            res["in_pin"].setdefault(m.group(1), {}).setdefault(sysname, set()).add(r)
                            res["pairs"].append({"from": r, "sys": sysname, "to": m.group(1), "kind": "PIN"})
                        if LOAD_HINT_RX.search(ln):
                            for m in NAMEREF_RX.finditer(ln):
                                if not PIN_RX.search(ln[m.start():m.start() + len(m.group(0)) + 7]):
                                    res["in_name"].setdefault(m.group(1), {}).setdefault(sysname, set()).add(r)
                elif sysname == "VCGC":
                    fam = FAM_RX.match(p.name)
                    key = fam.group(1) if fam else p.stem
                    for ln in lines:
                        for m in OTHER_PIN_RX.finditer(ln):
                            res["out_pin_files"].setdefault(r, (key, set()))[1].add(m.group(1))
            mention = len(TALIB_MENTION_RX.findall(text))
            use = talib_use(text, p.suffix.lower())
            if mention or use:
                res["talib"].append({"file": r, "sys": sysname, "use": use, "mention": mention,
                                     "guard": bool(TALIB_GUARD_RX.search(p.name)) or r.endswith(Path(__file__).name)})
    mark_tails(res)
    return res


def talib_use(text: str, suffix: str) -> int:
    if suffix == ".py":
        return len(TALIB_USE_RX.findall(text)) + len(TALIB_PIP_PY_RX.findall(text))
    if suffix in CODE_EXT:
        return len(TALIB_SH_USE_RX.findall(text))
    return 0


def mark_tails(res: dict) -> None:
    """同夾同家族只有版號最大那支是尾版;舊版是版史(只增不減,不能刪),KPI 與紅燈只算尾版。"""
    best = {}
    for r in res["seen"]:
        d, n = r.rsplit("/", 1) if "/" in r else ("", r)
        stem, suf = os.path.splitext(n)
        d = re.sub(r"_v\d{3,4}(?=/|$)", "", d)            # 版號資料夾(vrn2_release_v0179/…)也是同一家族的版史
        key = (d, re.sub(r"_v\d{3,4}$", "", stem), suf)
        v = vnum(stem)
        if key not in best or v > best[key][0]:
            best[key] = (v, r)
    tails = {r for _v, r in best.values()}
    for x in res["talib"]:
        x["tail"] = x["file"] in tails
    for stem, d in res["sup_use"].items():
        for sysname in list(d):
            d[sysname] = d[sysname] & tails
            if not d[sysname]:
                d.pop(sysname)
    for p in res["pairs"]:
        p["tail"] = p["from"] in tails
    for r, (key, targets) in res["out_pin_files"].items():
        if r in tails:
            res["out_pin"].setdefault(key, set()).update(targets)
    res["tails"] = tails


def intake_view(live_stems: set, via: Path = VIA) -> list:
    root = via / "supportive modules" / "references" / "intake"
    out = []
    for d in sorted(x for x in root.iterdir() if x.is_dir()) if root.is_dir() else []:
        files = [q for q in d.rglob("*") if q.is_file()]
        pys = [q for q in files if q.suffix == ".py"]
        same = sum(1 for q in pys if re.sub(r"_v\d{3,4}$", "", q.stem) in live_stems)
        man = [q.name for q in files if q.name.upper().startswith(("MANIFEST", "SHA256SUMS"))]
        out.append({"folder": d.name, "files": len(files), "py": len(pys), "same_name_live": same,
                    "manifest": man[:3], "batch": (re.search(r"(b\d{3,4}|20\d{6})", d.name) or [""])[0]})
    return out


def receipts(via: Path = VIA) -> dict:
    co = load_json(via / "VIA_Reports" / "closeout" / "CLOSEOUT_latest.json") or {}
    te = load_json(via / "VIA_Reports" / "vcgc" / "TEST_latest.json") or {}
    ho = load_json(via / "docs" / "handoff" / "HANDOFF_latest.json") or {}
    return {
        "closeout": {"at": co.get("at", ""), "rc": co.get("rc"), "run": co.get("run", ""), "head": co.get("head", ""),
                     "steps": [{k: s.get(k) for k in ("step", "name", "lamp", "note", "sec")} for s in co.get("steps", [])]},
        "test": {"at": te.get("at", ""), "lamp": te.get("lamp", ""), "counts": te.get("counts", {}), "mode": te.get("mode", "")},
        "handoff": {"at": ho.get("at", ""), "lamp": ho.get("lamp", ""), "closeout_lamp": ho.get("closeout_lamp", ""),
                    "summary": ho.get("summary", {})},
    }


def policy_law(lid: str, via: Path = VIA) -> dict:
    p = tail_of(via / "supportive modules" / "registry", "VIA_Policy_Laws_SSOT_v*.json")
    for law in (load_json(p) or {}).get("laws", []) if p else []:
        if law.get("id") == lid:
            return {"book": p.name, "id": lid, "zh": law.get("zh", ""), "status": law.get("status", "")}
    return {"book": p.name if p else "", "id": lid, "zh": "", "status": "未入冊"}


# ---------------------------------------------------------------- 命名對照
def naming_plan(fams: dict, numbers: dict, ledger_rows: list, via: Path = VIA) -> dict:
    """號跟家族走:發了不收回、不改、不重發(L125 ③)。留白 = 沒中央編號;衝突 = 不發。"""
    issued, owner, conflicts = {}, {}, []
    for e in ledger_rows:
        if e.get("event") != "issued":
            continue
        f, c = e.get("family"), e.get("code")
        if f in issued and issued[f]["code"] != c:
            conflicts.append({"kind": "一家族兩個名碼", "family": f, "code": c})
            continue
        if c in owner and owner[c] != f:
            conflicts.append({"kind": "同一名碼兩個家族", "family": f, "code": c})
            continue
        issued[f], owner[c] = e, f
    plan, reserved = {}, {}
    for fam in sorted(fams):
        m = NEW_RX.match(fam)
        if not m:
            continue
        code = "VIA_VCGC_%s%s" % (m.group(1), m.group(2))
        if fam in issued:
            continue
        if code in owner and owner[code] != fam:
            conflicts.append({"kind": "檔名自帶的名碼已發給別的家族", "family": fam, "code": code, "owner": owner[code]})
            plan[fam] = {"status": "BLOCKED", "code": code, "why": "名碼已屬 %s" % owner[code]}
            continue
        if code in reserved:
            conflicts.append({"kind": "兩支新檔自帶同一名碼", "family": fam, "code": code, "owner": reserved[code]})
            plan[fam] = {"status": "BLOCKED", "code": code, "why": "與 %s 同碼" % reserved[code]}
            continue
        reserved[code] = fam
        plan[fam] = {"status": "DECLARED", "code": code, "cls": m.group(1)}
    used = {"MDL": set(), "SUP": set()}
    for c in list(owner) + list(reserved):
        m = re.match(r"VIA_VCGC_(MDL|SUP)(\d+)$", c)
        if m:
            used[m.group(1)].add(int(m.group(2)))

    def order(fam):
        m = re.match(r"(?:CGC|SUP)_MDL(\d{3})_", fam)
        return (0 if fam.startswith("CGC_") else 1, int(m.group(1)) if m else 9999, fam)

    for fam in sorted(fams, key=order):
        info = fams[fam]
        if fam in issued or fam in plan:
            continue
        tail = info.get("tail")
        sysname = system_of(rel(tail, via)) if tail else "?"
        if sysname in OTHER_SYSTEMS:
            plan[fam] = {"status": "BLOCKED", "why": "他系統的檔(%s)不給 VCGC 名碼(L123)" % sysname}
            conflicts.append({"kind": "他系統家族", "family": fam, "code": ""})
            continue
        if info.get("unversioned"):
            plan[fam] = {"status": "PENDING", "why": "檔名沒有版本號(L126 ②)→ 先出帶 _vNNNN 的新版才發名"}
            continue
        if not reg_for(fam, tail, numbers, via):
            plan[fam] = {"status": "PENDING", "why": "還沒有中央編號(CGC_MDL237)→ 名碼留白(L125 ②)"}
            continue
        cls, why = classify(english_of(fam), info.get("seat", ""), family=fam)
        seq = 1
        while seq in used[cls]:
            seq += 1
        used[cls].add(seq)
        plan[fam] = {"status": "PROPOSED", "code": "VIA_VCGC_%s%03d" % (cls, seq), "cls": cls, "class_why": why}
    for fam, p in plan.items():
        if p["status"] == "DECLARED" and not reg_for(fam, fams[fam].get("tail"), numbers, via):
            p["why"] = "檔名已帶名碼;等 CGC_MDL237 編號後才發(L125 ②)"
    return {"issued": issued, "plan": plan, "conflicts": conflicts}


def naming_apply(fams: dict, numbers: dict, ledger: Path, via: Path = VIA) -> list:
    rows = read_jsonl(ledger)
    np_ = naming_plan(fams, numbers, rows, via)
    if np_["conflicts"]:
        hard = [c for c in np_["conflicts"] if c["kind"] != "他系統家族"]
        if hard:
            return []                                     # 有衝突一律不發(衝突要操作員與 AI 一起解,L125 ③)
    new_lines, now = [], utc_now()
    for fam in sorted(np_["plan"]):
        p = np_["plan"][fam]
        info = fams[fam]
        reg = reg_for(fam, info.get("tail"), numbers, via)
        if p["status"] not in ("PROPOSED", "DECLARED") or not reg:
            continue
        cls = p.get("cls") or classify(english_of(fam), info.get("seat", ""), family=fam)[0]
        why = p.get("class_why") or classify(english_of(fam), info.get("seat", ""), cls if NEW_RX.match(fam) else "", family=fam)[1]
        tail = info.get("tail")
        new_lines.append({
            "ts": now, "event": "issued", "code": p["code"], "cls": cls, "family": fam,
            "new_stem": fam if NEW_RX.match(fam) else "%s_%s" % (p["code"], english_of(fam)),
            "english": english_of(fam), "class_why": why, "reg_code": reg["code"],
            "reg_version": reg["version"], "tail": tail.name if tail else "",
            "tail_version": "v%04d" % vnum(tail) if tail else "", "book_version": BOOK_VERSION,
            "updated_at": now, "by": "%s %s" % (NAME, VERSION)})
    if new_lines:
        with open(ledger, "a", encoding="utf-8") as fh:
            for line in new_lines:
                fh.write(json.dumps(line, ensure_ascii=False) + "\n")
    return new_lines


# ---------------------------------------------------------------- 視覺鎖定
def visual_lock(via: Path = VIA) -> dict:
    p = tail_of(via / "docs" / "handoff" / "ai", "VIA_VisualLock_v*.py")
    if not p:
        return {"ok": False, "why": "找不到 docs/handoff/ai/VIA_VisualLock_v* 尾版"}
    try:
        vl = load_module(p, "_vcgc_toolmatrix_visuallock")
        page = via / vl.LOCK_PAGE
        if not page.is_file():
            return {"ok": False, "why": "找不到視覺鎖定正本 %s" % rel(page, via), "tool": p.name}
        site = vl.verify_lock_site(via)
        info = vl.extract_tokens(page)
        return {"ok": bool(site.get("ok")), "tool": p.name, "mod": vl, "sha256": info["sha256"], "count": info["count"],
                "kit": vl.build_kit(info), "site": {k: site.get(k) for k in ("ok", "checked", "failed")},
                "source": rel(page, via)}
    except Exception as exc:  # noqa: BLE001 — 鎖定工具壞掉照實回報,不讓矩陣當機
        return {"ok": False, "why": "視覺鎖定工具載入失敗:%s: %s" % (type(exc).__name__, exc), "tool": p.name}


def t(s) -> str:
    """HTML 轉義;另把 # 與 :// 換成具名實體 —— 資料裡的「#123」「https://」不能被鎖定閘當成寫死色或外連。"""
    s = "" if s is None else str(s)
    for a, b in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"), ('"', "&quot;"), ("'", "&apos;"),
                 ("#", "&num;"), ("://", ":&sol;&sol;")):
        s = s.replace(a, b)
    return s


PILL = {"GREEN": ("ok", "綠"), "YELLOW": ("warn", "黃"), "RED": ("bad", "紅"), "AMBER": ("warn", "黃")}


def pill(lamp, text=None) -> str:
    cls, zh = PILL.get(str(lamp or "").upper(), ("gray", "灰"))
    return '<span class="vl-pill %s">%s</span>' % (cls, t(text if text is not None else zh))


def worst(*lamps) -> str:
    rank = {"RED": 3, "YELLOW": 2, "AMBER": 2, "GREEN": 1}
    best = max((rank.get(str(x or "").upper(), 0) for x in lamps), default=0)
    return {3: "RED", 2: "YELLOW", 1: "GREEN"}.get(best, "GRAY")


EXTRA_CSS = """
.vm-tabs{display:flex;flex-wrap:wrap;gap:4px;margin:0 0 10px}
.vm-tabs button{font:inherit;font-size:var(--vl-size-label);padding:4px 10px;border:1px solid var(--vl-border);
  background:var(--vl-white);color:var(--vl-ink);cursor:pointer}
.vm-tabs button[aria-selected="true"]{background:var(--vl-row);color:var(--vl-title);border-color:var(--vl-ink)}
.vm-filter{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 8px;align-items:center}
.vm-filter input,.vm-filter select{font:inherit;font-size:var(--vl-size-label);padding:3px 6px;border:1px solid var(--vl-border);
  background:var(--vl-white);color:var(--vl-ink);min-width:0}
.vm-filter input[type="search"]{flex:1 1 200px}
.vm-filter label{color:var(--vl-muted);font-size:var(--vl-size-label)}
th[data-sort]{cursor:pointer}
.vm-mono,code{font-family:var(--vl-font-mono);word-break:break-all}
.vm-dim{color:var(--vl-muted)}
[hidden]{display:none !important}
"""

JS = """
(function(){
  var tabs=document.querySelectorAll('.vm-tabs button');
  function show(name){
    tabs.forEach(function(b){b.setAttribute('aria-selected', b.dataset.tab===name?'true':'false');});
    document.querySelectorAll('[data-pane]').forEach(function(p){p.hidden=(p.dataset.pane!==name);});
    try{localStorage.setItem('vcgc_toolmatrix_tab',name);}catch(e){}
  }
  tabs.forEach(function(b){b.addEventListener('click',function(){show(b.dataset.tab);});});
  var start='two'; try{start=localStorage.getItem('vcgc_toolmatrix_tab')||'two';}catch(e){}
  if(!document.querySelector('[data-pane="'+start+'"]')){start='two';}
  show(start);
  document.querySelectorAll('[data-filter]').forEach(function(box){
    var tb=document.getElementById(box.dataset.filter); if(!tb){return;}
    var q=box.querySelector('input[type="search"]'), sels=box.querySelectorAll('select'), n=box.querySelector('.vm-count');
    function apply(){
      var s=(q&&q.value||'').toLowerCase(), shown=0;
      tb.querySelectorAll('tr').forEach(function(tr){
        var ok=!s||tr.textContent.toLowerCase().indexOf(s)>=0;
        sels.forEach(function(sel){ if(sel.value&&tr.dataset[sel.name]!==sel.value){ok=false;} });
        tr.hidden=!ok; if(ok){shown++;}
      });
      if(n){n.textContent=shown+' 列';}
    }
    if(q){q.addEventListener('input',apply);} sels.forEach(function(sel){sel.addEventListener('change',apply);}); apply();
  });
  document.querySelectorAll('th[data-sort]').forEach(function(th){
    th.addEventListener('click',function(){
      var table=th.closest('table'), tb=table.tBodies[0], i=Array.prototype.indexOf.call(th.parentNode.children,th);
      var dir=th.dataset.dir==='asc'?'desc':'asc'; th.dataset.dir=dir;
      var rows=Array.prototype.slice.call(tb.rows);
      rows.sort(function(a,b){
        var x=a.cells[i].textContent.trim(), y=b.cells[i].textContent.trim();
        var nx=parseFloat(x), ny=parseFloat(y), c;
        c=(!isNaN(nx)&&!isNaN(ny))?nx-ny:x.localeCompare(y,'zh-Hant');
        return dir==='asc'?c:-c;
      });
      rows.forEach(function(r){tb.appendChild(r);});
    });
  });
  var auto=document.getElementById('vm-auto');
  if(auto){
    try{auto.checked=localStorage.getItem('vcgc_toolmatrix_auto')!=='off';}catch(e){}
    auto.addEventListener('change',function(){try{localStorage.setItem('vcgc_toolmatrix_auto',auto.checked?'on':'off');}catch(e){}});
    setInterval(function(){
      var busy=document.activeElement&&/INPUT|SELECT/.test(document.activeElement.tagName);
      if(auto.checked&&!busy){location.reload();}
    },300000);
  }
})();
"""


def render_html(rep: dict, kit: str) -> str:
    rows, k = rep["tools"], rep["kpi"]
    rc = rep["receipts"]
    kpis = [("工具家族", k["tools"]), ("VIA 中央管理工具", k["mdl"]), ("VIA 支援工具", k["sup"]),
            ("已發名碼", k["issued"]), ("擬發 / 留白", "%d / %d" % (k["proposed"], k["pending"])),
            ("命名衝突", k["conflicts"]), ("TA-Lib 程式使用(尾版)", k["talib_use"]), ("他系統釘 VCGC 版(尾版)", k["in_pin_files"]),
            ("鎖定閘", rep["visual_lock"].get("gate", "—"))]
    h = ['<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">',
         '<title>VCGC 工具矩陣</title><style>', kit, EXTRA_CSS, '</style></head><body>',
         '<header class="vl-topbar"><h1>VCGC 工具矩陣</h1><div class="vl-kpis">']
    for label, val in kpis:
        h.append('<div class="vl-kpi"><span class="vl-label">%s</span><span class="vl-value">%s</span></div>' % (t(label), t(val)))
    h.append('</div></header>')
    h.append('<p class="vl-sub">%s %s · 生成 %s(UTC)· 視覺鎖定 %s · token %s 個 · sha %s · '
             '<label><input type="checkbox" id="vm-auto" checked> 每 5 分鐘自動重整</label></p>'
             % (t(NAME), t(VERSION), t(rep["at"]), t(rep["visual_lock"].get("tool", "—")),
                t(rep["visual_lock"].get("count", "—")), t(str(rep["visual_lock"].get("sha256", ""))[:16])))
    tabs = [("two", "兩大功能"), ("mdl", "VIA 中央管理工具"), ("sup", "VIA 支援工具"), ("flat", "單檔收斂"),
            ("close", "VCGC 收尾"), ("int", "整合進來 INT"), ("indep", "獨立性 / 衝突"),
            ("talib", "TA-Lib"), ("reg", "各系統登錄"), ("rule", "命名與政策")]
    h.append('<nav class="vm-tabs" role="tablist">' + "".join(
        '<button type="button" role="tab" data-tab="%s">%s</button>' % (a, t(b)) for a, b in tabs) + '</nav>')

    # ① 收尾
    co, te, ho = rc["closeout"], rc["test"], rc["handoff"]
    h.append('<section data-pane="close" hidden><div class="vl-board">')
    h.append('<div class="vl-panel" data-span="6"><div class="vl-head"><h2>VCGC 收尾(closeout 收據)</h2>'
             '<span class="vl-why">%s · rc %s · run %s</span></div>' % (t(co["at"] or "還沒有收據"), t(co["rc"]), t(co["run"])))
    if co["steps"]:
        h.append('<div class="vl-scroll"><table><thead><tr><th>步</th><th>名稱</th><th>燈</th><th>說明</th><th>秒</th></tr></thead><tbody>')
        for s in co["steps"]:
            h.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class="vl-num">%s</td></tr>'
                     % (t(s.get("step")), t(s.get("name")), pill(s.get("lamp")), t(str(s.get("note") or "")[:400]), t(s.get("sec"))))
        h.append('</tbody></table></div>')
    else:
        h.append('<p class="vl-note">還沒有 closeout 收據:跑 <code>via-vcgc closeout</code> 後重出本頁。</p>')
    h.append('</div><div class="vl-panel" data-span="6"><div class="vl-head"><h2>串測與交接</h2></div><div class="vl-grid">')
    cnt = te.get("counts") or {}
    cells = [("VCGC test 總燈", pill(te.get("lamp"))), ("test 時間", t(te.get("at") or "—")),
             ("綠 / 黃 / 紅", t("%s / %s / %s" % (cnt.get("GREEN", 0), cnt.get("YELLOW", 0), cnt.get("RED", 0)))),
             ("交接快照燈", pill(ho.get("lamp"))), ("驗收燈 closeout_lamp", pill(ho.get("closeout_lamp"))),
             ("交接快照時間", t(ho.get("at") or "—"))]
    for label, val in cells:
        h.append('<div class="vl-cell"><span class="vl-label">%s</span><span class="vl-value">%s</span></div>' % (t(label), val))
    h.append('</div><p class="vl-note">綠燈只代表「交接資料完整」;驗收看 closeout_lamp。BLOCKED / REVIEW / 缺證據不寫成成功。'
             '交接快照時間若很舊,代表 checkpoint 一直被交接閘擋住(照實顯示,不刷新假綠)。</p></div>')
    h.append('</div></section>')

    # ② 兩大功能矩陣 + 中央管理工具 / 支援工具兩表 + 單檔收斂
    two = rep.get("two") or []
    h.append('<section data-pane="two"><div class="vl-panel"><div class="vl-head"><h2>VCGC 兩大功能</h2>'
             '<span class="vl-why">VIA 中央管理工具(MDL)· VIA 支援工具(SUP:Token-Saving 與其他工具組);分組依名稱 / 席位,只影響顯示,不影響名碼</span></div>')
    h.append('<div class="vl-scroll"><table><thead><tr>' + "".join('<th data-sort>%s</th>' % t(c) for c in (
        "大類", "分組", "家族", "已發名碼", "綠", "黃", "紅", "加速器 OK", "有測站", "有實測", "單檔", "可刪舊版", "待合成", "舊版被點名", "他系統在用"))
        + '</tr></thead><tbody>')
    last = None
    for g in two:
        if g["super"] != last:
            h.append('<tr><th colspan="15">%s</th></tr>' % t(g["super"]))
            last = g["super"]
        h.append('<tr><td>%s</td><td>%s</td>%s<td>%s</td></tr>' % (t(g["super"]), t(g["label"]), "".join(
            '<td class="vl-num">%s</td>' % t(x) for x in (g["n"], g["issued"], g["lamps"]["GREEN"], g["lamps"]["YELLOW"], g["lamps"]["RED"],
                                                       g["accel"], g["station"], g["tested"], g["single"], g["ready"], g["flatten"], g["blocked"])),
            t(" · ".join(g["used_by"]) or "—")))
    h.append('</tbody></table></div><p class="vl-note">單檔 = 只有一版 · 可刪舊版 = 尾版不載前版且舊版無人點名(驗證後刪,L130)· 待合成 = 薄尾鏈要先合成單檔並證零遺失 ·'
             ' 他系統在用 = VDF / VRN-2 / VQG / VAP 的尾版直接載入這組支援工具(L130 ④:應改為各存一份同版副本)</p></div></section>')
    cols = ["燈", "分組", "名碼", "名碼狀態", "家族(現名)", "尾版", "版數", "收斂", "中央編號", "編號時間", "最後提交", "實測帳", "測站",
            "加速器", "AST", "TA-Lib", "他系統載入", "指令"]

    def tool_table(pane, tbid, title, why, picked):
        groups = sorted({r["group_label"] for r in picked})
        h.append('<section data-pane="%s" hidden><div class="vl-panel"><div class="vl-head"><h2>%s(%d 家族)</h2><span class="vl-why">%s</span></div>'
                 % (pane, t(title), len(picked), t(why)))
        h.append('<div class="vm-filter" data-filter="%s"><input type="search" placeholder="搜尋名稱 · 名碼 · 編號 · 指令" aria-label="搜尋">'
                 '<label>分組 <select name="grp"><option value="">全部</option>%s</select></label>'
                 '<label>燈 <select name="lamp"><option value="">全部</option><option>GREEN</option><option>YELLOW</option><option>RED</option></select></label>'
                 '<label>收斂 <select name="rd"><option value="">全部</option><option>SINGLE</option><option>READY</option><option>NEEDS_FLATTEN</option>'
                 '<option>BLOCKED_REF</option><option>EXEMPT</option></select></label><span class="vm-count vm-dim"></span></div>'
                 % (tbid, "".join("<option>%s</option>" % t(g) for g in groups)))
        h.append('<div class="vl-scroll"><table><thead><tr>' + "".join('<th data-sort>%s</th>' % t(c) for c in cols) + '</tr></thead><tbody id="%s">' % tbid)
        for r in picked:
            ast = " ".join("%s%d" % (a, n) for a, n in sorted((r.get("ast") or {}).items())) or "0"
            use = " · ".join("%s %d" % kv for kv in sorted(r.get("sup_use", {}).items()))
            h.append('<tr data-grp="%s" data-lamp="%s" data-rd="%s">' % (t(r["group_label"]), t(r["lamp"]), t(r["ready"]))
                     + "".join("<td>%s</td>" % x for x in (
                         pill(r["lamp"]), t(r["group_label"]), '<span class="vm-mono">%s</span>' % t(r["name_code"] or "—"),
                         t(r["name_status"]), '<span class="vm-mono">%s</span><br><span class="vm-dim">%s</span>' % (t(r["family"]), t(r["class_why"])),
                         t(r["version"]), t(r["versions"]), '%s<br><span class="vm-dim">%s</span>' % (t(r["ready"]), t("; ".join(r["ready_refs"][:2]))),
                         '<span class="vm-mono">%s</span>' % t(r["reg_code"] or "未編號"), t(r["reg_at"] or "—"), t(r["updated"] or "—"),
                         (pill(r["test_lamp"]) + " " + t(r["test_at"][:16])) if r["test_lamp"] else pill(None, "沒量"),
                         t(", ".join(r["stations"][:3]) + (" …" if len(r["stations"]) > 3 else "") or "—"),
                         t(r["accel"]), t(ast), t("%d / %d" % (r["talib_use"], r["talib_mention"])),
                         t(("釘 %d · 名 %d" % (r["in_pin"], r["in_name"])) + ((" · 在用 " + use) if use else "")),
                         '<span class="vm-mono">%s</span>' % t(r["run"]))) + '</tr>')
        h.append('</tbody></table></div></div></section>')

    tool_table("mdl", "tb-mdl", "VIA 中央管理工具", "MDL = VCGC 本身中央控管:主控台 · 編號 / 註冊 · 測試 / 閘 · 交接 / 收尾 · 環境 · 流程 · UI",
               [r for r in rows if r["cls"] == "MDL"])
    tool_table("sup", "tb-sup", "VIA 支援工具(Token-Saving 與其他工具組)",
               "SUP = 省 Token(read · slice · digest · MCP · NLP brief)與其他工具組(加速器 · 網路 · NLP / Layout / OCR · AI 平台 · 整併 / 資料);"
               "「他系統載入」的「在用」= 他系統尾版直接載入本支(L130 ④ 應改為各存一份同版副本)",
               sorted([r for r in rows if r["cls"] == "SUP"], key=lambda r: (r["super"] != SUPER["TOKEN"], r["group_label"], r["family"])))
    fl = rep.get("flatten") or {}
    h.append('<section data-pane="flat" hidden><div class="vl-panel"><div class="vl-head"><h2>單檔收斂(L130:全部薄尾家族合成單檔 · 驗證後刪舊版)</h2>'
             '<span class="vl-why">只收斂 VCGC 自己的家族;VDF · VRN-2 · VQG · VAP 各自收斂(L123)· 凍結件與收容原件不動</span></div><div class="vl-grid">')
    for k2, label in (("SINGLE", "已是單檔"), ("READY", "可刪舊版(家族)"), ("old_files_ready", "可刪的舊版檔"), ("NEEDS_FLATTEN", "薄尾待合成"),
                      ("BLOCKED_REF", "舊版仍被點名"), ("EXEMPT", "凍結不收斂")):
        h.append('<div class="vl-cell"><span class="vl-label">%s</span><span class="vl-value">%s</span></div>' % (t(label), t(fl.get(k2, 0))))
    h.append('</div><p class="vl-note">驗證(缺一不刪):尾版自測通過 · 尾版不在執行期載入舊版 · 活樹程式與冊(交接案相依 · 盤點冊 deps · 工具鎖冊 · 工作流 · 需求)'
             '沒有任何一處點名要刪的舊版檔;薄尾鏈先合成單檔並證零遺失(CGC_MDL281 PROVEN_ZERO_LOSS + 自測等價)。刪除前記刪除帳(檔名 · sha256 · 大小),git 歷史存原文。'
             '逐家族明細在「VIA 中央管理工具」/「VIA 支援工具」兩表的「收斂」欄(可篩)。</p></div></section>')

    # ③ 整合進來
    it = rep["intake"]
    h.append('<section data-pane="int" hidden><div class="vl-panel"><div class="vl-head"><h2>整合進來(收容 %d 批)</h2>'
             '<span class="vl-why">收容正本零觸碰(L03);「活樹同名」只比家族名,不是內容零損失證明 —— 證明要跑 CGC_MDL281 compare</span></div>' % len(it))
    h.append('<div class="vm-filter" data-filter="tb-int"><input type="search" placeholder="搜尋收容批" aria-label="搜尋收容批"><span class="vm-count vm-dim"></span></div>')
    h.append('<div class="vl-scroll"><table><thead><tr><th data-sort>收容批</th><th data-sort>批號</th><th data-sort>檔</th>'
             '<th data-sort>.py</th><th data-sort>活樹同名</th><th>MANIFEST / SHA256SUMS</th></tr></thead><tbody id="tb-int">')
    for x in it:
        h.append('<tr><td class="vm-mono">%s</td><td>%s</td><td class="vl-num">%d</td><td class="vl-num">%d</td><td class="vl-num">%d</td><td>%s</td></tr>'
                 % (t(x["folder"]), t(x["batch"]), x["files"], x["py"], x["same_name_live"], t(", ".join(x["manifest"]) or "—")))
    h.append('</tbody></table></div></div></section>')

    # ④ 獨立性
    ind = rep["independence"]
    h.append('<section data-pane="indep" hidden><div class="vl-board">')
    h.append('<div class="vl-panel" data-span="6"><div class="vl-head"><h2>他系統載入 VCGC 內部模組</h2><span class="vl-why">'
             '釘版 = VCGC 一升級對方就停在舊版或失效(紅)· 名引 = 照家族名載入(黃)· 走 via-vcgc 指令 / 收據 = 契約(L127,不列)。'
             '他系統的檔 VCGC 只攤開、不代改(L123)</span></div>')
    h.append('<div class="vl-scroll"><table><thead><tr><th data-sort>燈</th><th data-sort>他系統檔</th><th data-sort>系統</th><th data-sort>尾版</th>'
             '<th data-sort>釘到的 VCGC 家族</th></tr></thead><tbody>')
    for p in ind["pins"][:400]:
        h.append('<tr><td>%s</td><td class="vm-mono">%s</td><td>%s</td><td>%s</td><td class="vm-mono">%s</td></tr>'
                 % (pill("RED" if p["tail"] else "YELLOW"), t(p["from"]), t(p["sys"]), "尾版" if p["tail"] else "舊版", t(p["to"])))
    if not ind["pins"]:
        h.append('<tr><td colspan="5">0 —— 沒有他系統釘 VCGC 版號</td></tr>')
    h.append('</tbody></table></div></div>')
    h.append('<div class="vl-panel" data-span="6"><div class="vl-head"><h2>VCGC 釘他系統版號</h2><span class="vl-why">VCGC 自己的債:'
             '改為讀對方自報的收據 / 走對方 manager(黃)</span></div><div class="vl-scroll"><table><thead><tr><th data-sort>VCGC 家族</th>'
             '<th data-sort>釘到的他系統檔</th></tr></thead><tbody>')
    for fam, tg in sorted(ind["out_pin"].items()):
        h.append('<tr><td class="vm-mono">%s</td><td class="vm-mono">%s</td></tr>' % (t(fam), t(", ".join(sorted(tg)[:6]) + (" …" if len(tg) > 6 else ""))))
    if not ind["out_pin"]:
        h.append('<tr><td colspan="2">0</td></tr>')
    h.append('</tbody></table></div></div>')
    h.append('<div class="vl-panel" data-span="12"><div class="vl-head"><h2>命名衝突</h2></div><div class="vl-scroll"><table><thead><tr>'
             '<th>類</th><th>家族</th><th>名碼</th></tr></thead><tbody>')
    for c in rep["naming"]["conflicts"]:
        h.append('<tr><td>%s</td><td class="vm-mono">%s</td><td class="vm-mono">%s</td></tr>' % (t(c["kind"]), t(c.get("family")), t(c.get("code"))))
    if not rep["naming"]["conflicts"]:
        h.append('<tr><td colspan="3">0 —— 無衝突</td></tr>')
    h.append('</tbody></table></div></div></div></section>')

    # ⑤ TA-Lib
    tl = rep["talib"]
    h.append('<section data-pane="talib" hidden><div class="vl-panel"><div class="vl-head"><h2>TA-Lib:不可用、不可出現(L50 · L129)</h2>'
             '<span class="vl-why">尾版程式使用 %d 處(紅)· 舊版版史 %d 處(黃:只增不減不能刪,出新版時拿掉)· 守門檔內樣本 %d 處 · '
             '文字出現 %d 檔(守門 / 法條必要提及 %d 檔)· 收容夾不掃(L03)</span></div>'
             % (tl["use"], tl.get("use_history", 0), tl["use_in_guard"], tl["files"], tl["guard_files"]))
    h.append('<div class="vm-filter" data-filter="tb-talib"><input type="search" placeholder="搜尋檔名" aria-label="搜尋檔名">'
             '<label>系統 <select name="sys"><option value="">全部</option>' + "".join("<option>%s</option>" % t(s) for s in tl["by_sys"]) +
             '</select></label><span class="vm-count vm-dim"></span></div>')
    h.append('<div class="vl-scroll"><table><thead><tr><th data-sort>燈</th><th data-sort>檔</th><th data-sort>系統</th>'
             '<th data-sort>尾版</th><th data-sort>使用</th><th data-sort>出現</th><th>守門</th></tr></thead><tbody id="tb-talib">')
    for x in tl["rows"][:800]:
        lamp = ("RED" if x["tail"] else "YELLOW") if x["use"] and not x["guard"] else ("YELLOW" if (x["use"] or not x["guard"]) else "GREEN")
        h.append('<tr data-sys="%s"><td>%s</td><td class="vm-mono">%s</td><td>%s</td><td>%s</td><td class="vl-num">%d</td><td class="vl-num">%d</td><td>%s</td></tr>'
                 % (t(x["sys"]), pill(lamp), t(x["file"]), t(x["sys"]), "尾版" if x["tail"] else "舊版", x["use"], x["mention"],
                    "是" if x["guard"] else ""))
    h.append('</tbody></table></div></div></section>')

    # ⑥ 各系統登錄
    rv = rep["register_view"]
    kinds = sorted({kd for v in rv.values() for kd in v})
    h.append('<section data-pane="reg" hidden><div class="vl-panel"><div class="vl-head"><h2>各系統自行登錄 · VCGC 檢視</h2>'
             '<span class="vl-why">編號冊逐冊:系統 × 類 · 最後登錄時間。子系統自己登自己的冊(L126 ③),VCGC 只讀、只看</span></div>')
    h.append('<div class="vl-scroll"><table><thead><tr><th data-sort>系統</th>' + "".join('<th data-sort>%s</th>' % t(kd) for kd in kinds)
             + '<th data-sort>最後登錄</th></tr></thead><tbody>')
    for sub in sorted(rv):
        last = max((c["last"] for c in rv[sub].values()), default="")
        h.append('<tr><td>%s</td>%s<td>%s</td></tr>' % (t(sub), "".join(
            '<td class="vl-num">%s</td>' % t(rv[sub][kd]["n"] if kd in rv[sub] else "") for kd in kinds), t(last[:19])))
    h.append('</tbody></table></div></div></section>')

    # ⑦ 命名與政策
    law = rep["policy"]
    h.append('<section data-pane="rule" hidden><div class="vl-board"><div class="vl-panel" data-span="6"><div class="vl-head"><h2>命名規定</h2></div>'
             '<p><code>VIA_&lt;系統&gt;_&lt;類&gt;###_&lt;英文名&gt;_v&lt;NNNN&gt;.py</code></p>'
             '<p class="vl-note">VCGC:中央管理 = <code>VIA_VCGC_MDL###</code> · 省 Token / 支援 = <code>VIA_VCGC_SUP###</code>。'
             '版本號照 L126 ② 用 <code>_vNNNN</code>;登錄時間記在命名帳(issued_at / updated_at)。'
             '舊檔不改名(L02 只增不減 · L04 尾版律 · 薄尾 glob 鏈),由命名帳給新名;新家族一律用新名。</p>'
             '<p class="vl-note">命名帳:<code>%s</code> · 已發 %d · 擬發 %d · 留白 %d · 衝突 %d</p></div>'
             % (t(LEDGER_NAME), k["issued"], k["proposed"], k["pending"], k["conflicts"]))
    h.append('<div class="vl-panel" data-span="6"><div class="vl-head"><h2>%s %s</h2><span class="vl-why">%s · %s</span></div><p>%s</p></div>'
             % (t(law["id"]), t(law["status"]), t(law["book"]), t("政策冊尾版"), t(law["zh"] or "(未入冊)")))
    h.append('</div></section>')
    h.append('<footer class="vl-foot">%s %s · 只讀他系統 · 只寫 VIA_Reports/vcgc/ 與命名帳 · 鎖定閘 %s · 來源:%s</footer>'
             % (t(NAME), t(VERSION), t(rep["visual_lock"].get("gate", "—")), t(" · ".join(rep["sources"]))))
    h.append('<script>' + JS + '</script></body></html>')
    return "".join(h)


# ---------------------------------------------------------------- 兩大功能分組 · 單檔收斂 · 支援工具使用者
SUP_GROUPS = [   # (鍵, 名稱, 判準(家族, 英文名, 席位));先中先得。Token-Saving 一組,其餘 = 其他工具組
    ("TOKEN", "Token-Saving 省 Token", lambda f, e, s: s in ("token", "nlp") or f == "CGC_MDL279_MCPServer"),
    ("ACCEL", "加速器 / 支援橋", lambda f, e, s: s == "accelerator" or re.search(r"Accel|BridgeSweeper|SupportBridge|SupportImport|SupportTier|DuckTempHook|Celeritas", e)),
    ("NET", "網路工具", lambda f, e, s: s == "network" or re.search(r"NetUnified|SmartDecode|Aegis", e)),
    ("DOC", "NLP / Layout / OCR / PDF", lambda f, e, s: s in ("layout", "pdfplumber", "ocr", "praddle") or re.search(r"Nlp|NLP|Layout|PDFPlumber|ocr|FieldRule", e)),
    ("AI", "AI 平台", lambda f, e, s: re.match(r"Ai[A-Z]", e)),
    ("DATA", "整併 / 資料 / 測試工具", lambda f, e, s: s in ("frame", "graphify", "playwright", "duckdb") or re.search(r"ShadowMerge|Polars|Lake|Graphify|Playwright", e)),
]
MDL_GROUPS = [
    ("CONSOLE", "主控台 / 入口", r"^VeritasCentralGovernanceConsole$|Console|Shell|Deck|Portal|Entry|Hub$|CommandCenter|SystemManager|MasterHub"),
    ("NUMBER", "編號 / 註冊 / SSOT", r"Number|Registry|Namereg|Naming|SSOT|Synonym|Regex|Book|Catalog|Inventory|Ledger|AutoCode|Union|Code"),
    ("GATE", "測試 / 閘 / 稽核", r"Test|Gate|Selftest|Audit|Check|Probe|Verify|Validator|Lock|Freeze|Seal|Ratchet|Triage|Arbiter|Medic|Doctor|Rescue|Repair|Pyramid|Matrix$"),
    ("CLOSE", "交接 / 收尾 / 備份", r"Handover|Closeout|Wrapup|Progress|Success|Backup|Shutdown|Journal|Completion|Closing|Record"),
    ("ENV", "環境 / 安裝 / 工具鏈", r"Env|Install|Provision|Dep|Camelot|Toolkit|Tool|Accel"),
    ("FLOW", "流程 / 工作流 / 同步", r"Flow|Workflow|Step|Chain|Run|Lane|Route|Sync|Bus|Pilot|Autorun|Composer|Deploy|Intake|Fetch|Organizer|Merge|Copy"),
    ("UI", "UI / 頁面 / 報表", r"UI|Ui|Page|Template|View|Report|Card|Atlas|Blueprint|Spec|Charter|Article|Prompt|Chat"),
]
SUPER = {"MDL": "VIA 中央管理工具", "TOKEN": "VIA 支援工具 · Token-Saving", "OTHER": "VIA 支援工具 · 其他工具組"}
FROZEN_SEATS = {"accelerator", "network"}               # 批345 不可動(VeritasCeleritas / VeritasAegisNexus 本體)
DEP_SKIP_RX = re.compile(r"VIA_NumberBooks/|VIA_Component_Inventory|VIA_VCGC_FunctionLedger|VIA_Numbering_SSOT|VIA_VCGC_ToolNaming|VCGC_FunctionMatrix_v"
                         r"|VIA_RegistryNumbers|docs/handoff/evidence/|/history/|VIA_EngineVersion_Register|\.md$|\.txt$|\.html$|\.jsonl$")
OLDREF_RX = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*_v\d{4}\.py)\b")


def group_of(cls: str, fam: str, seat: str = "") -> tuple:
    """顯示分組(依名稱 · 席位;只影響畫面,不影響名碼)→ (鍵, 名稱, 大類)。"""
    eng = english_of(fam)
    if cls == "SUP":
        for key, label, rule in SUP_GROUPS:
            if rule(fam, eng, seat or ""):
                return key, label, SUPER["TOKEN" if key == "TOKEN" else "OTHER"]
        return "SUPX", "其他支援", SUPER["OTHER"]
    if fam.startswith("CGC_MDL149_"):
        return "CONSOLE", "主控台 / 入口", SUPER["MDL"]
    for key, label, rx in MDL_GROUPS:
        if re.search(rx, eng):
            return key, label, SUPER["MDL"]
    return "MDLX", "其他中央管理", SUPER["MDL"]


def readiness(fam: str, info: dict, refs: dict, via: Path = VIA) -> tuple:
    """單檔收斂就緒度(L130):SINGLE 已單檔 · READY 可刪舊版 · NEEDS_FLATTEN 薄尾鏈先合成單檔 · BLOCKED_REF 舊版仍被點名 · EXEMPT 凍結。"""
    files = [f for f in info.get("files", []) if f]
    tail = info.get("tail")
    if len(files) <= 1 or tail is None:
        return "SINGLE", "已是單檔", []
    if info.get("seat") in FROZEN_SEATS:
        return "EXEMPT", "批345 不可動本體 · 不收斂", []
    try:
        text = tail.read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""
    if re.search(r"glob\(|spec_from_file_location|run_path", text) and (fam in text or "_STEM" in text or "NAME +" in text):
        return "NEEDS_FLATTEN", "尾版是薄尾(執行期載入前版)→ 先合成單檔 + 零遺失證明(CGC_MDL281)才可刪", []
    own = {rel(f, via) for f in files}
    hits = []
    for f in files:
        if f == tail:
            continue
        for who in sorted(refs.get(f.name, set()) - own)[:3]:
            hits.append("%s ← %s" % (f.name, who))
    if hits:
        return "BLOCKED_REF", "舊版仍被活樹程式 / 冊點名(要先改那些點名)", hits[:5]
    return "READY", "尾版單檔不載前版 · 舊版無人點名 → 驗證(尾版自測)後可刪舊版", []


# ---------------------------------------------------------------- 組裝
def collect(via: Path = VIA, ast: bool = True) -> dict:
    t0 = time.time()
    fams, skipped, seats_excluded = discover(via)
    numbers = number_book(via)
    fi_name, by_station, _stems = stations(via)
    led = ledger_last(via)
    ledger = HERE / LEDGER_NAME if via == VIA else via / "supportive modules" / "registry" / LEDGER_NAME
    np_ = naming_plan(fams, numbers, read_jsonl(ledger), via)
    sup_stems = [f for f in fams if (np_["issued"].get(f, {}).get("cls") or np_["plan"].get(f, {}).get("cls")
                                      or classify(english_of(f), fams[f].get("seat", ""), family=f)[0]) == "SUP"]
    tree = scan_tree(via, sup_stems)
    ast_rows = {}
    if ast:
        try:
            m253 = load_module(tail_of(via / "supportive modules" / "registry", "CGC_MDL253_ToolingInventory_v*.py"), "_vcgc_toolmatrix_253")
            res = m253.scan(paths=[str(f["tail"]) for f in fams.values() if f.get("tail")], quiet=True)
            for r in res.get("rows", []):
                ast_rows[r["family"]] = r
        except Exception as exc:  # noqa: BLE001 — 盤點工具壞了照實標「沒量」,不冒充綠
            ast_rows = {"__error__": "%s: %s" % (type(exc).__name__, exc)}
    talib_by_file = {x["file"]: x for x in tree["talib"]}
    tools = []
    for fam in sorted(fams):
        info = fams[fam]
        tail = info.get("tail")
        r_tail = rel(tail, via) if tail else ""
        iss = np_["issued"].get(fam)
        pl = np_["plan"].get(fam, {})
        if iss:
            cls, why, code, status = iss.get("cls", ""), iss.get("class_why", ""), iss.get("code", ""), "ISSUED"
        else:
            m = NEW_RX.match(fam)
            cls, why = (pl.get("cls"), pl.get("class_why")) if pl.get("cls") else classify(english_of(fam), info.get("seat", ""), m.group(1) if m else "", fam)
            code, status = pl.get("code", ""), pl.get("status", "PENDING")
            why = why or pl.get("why", "")
        num = reg_for(fam, tail, numbers, via)
        a = ast_rows.get(fam) or {}
        tl = talib_by_file.get(r_tail, {"use": 0, "mention": 0, "guard": False})
        in_pin = sum(len(v & tree["tails"]) for v in tree["in_pin"].get(fam, {}).values())
        in_name = sum(len(v & tree["tails"]) for v in tree["in_name"].get(fam, {}).values())
        tl_lamp = "RED" if tl["use"] and not tl["guard"] else ("YELLOW" if tl["mention"] and not tl["guard"] else "GREEN")
        lamp = worst(a.get("lamp") if a else None, "YELLOW" if a and a.get("l103", {}).get("py_accel") == "MISS" else None,
                     led.get(fam, {}).get("lamp") if led.get(fam, {}).get("lamp") == "RED" else None, tl_lamp,
                     "YELLOW" if in_pin else None, "RED" if status == "BLOCKED" else None)
        tools.append({
            "lamp": lamp, "cls": cls or "MDL", "class_why": why or "", "name_code": code, "name_status": status,
            "family": fam, "seat": info.get("seat", ""), "src": info.get("src", ""), "path": r_tail,
            "version": "v%04d" % vnum(tail) if tail and vnum(tail) >= 0 else "—", "versions": info.get("versions", 0),
            "reg_code": num.get("code", ""), "reg_at": str(num.get("updated_at", ""))[:19],
            "updated": a.get("updated", "") if a else "", "test_lamp": led.get(fam, {}).get("lamp", ""),
            "test_at": led.get(fam, {}).get("ts", ""), "stations": by_station.get(fam, []),
            "accel": (a.get("l103", {}) or {}).get("py_accel", "沒量") if a else "沒量",
            "ast": a.get("issues", {}) if a else {}, "talib_use": tl["use"], "talib_mention": tl["mention"],
            "in_pin": in_pin, "in_name": in_name, "out_pin": sorted(tree["out_pin"].get(fam, set())),
            "run": a.get("run", "") if a else ("via-vcgc run %s" % fam),
        })
        g = group_of(tools[-1]["cls"], fam, info.get("seat", ""))
        rd = readiness(fam, info, tree["refs"], via)
        tools[-1].update({"group": g[0], "group_label": g[1], "super": g[2], "ready": rd[0], "ready_why": rd[1], "ready_refs": rd[2],
                          "sup_use": {k2: len(v) for k2, v in tree["sup_use"].get(fam, {}).items()}})
    tl_rows = sorted(tree["talib"], key=lambda x: (-bool(x["use"] and not x["guard"] and x["tail"]), x["guard"], not x["tail"],
                                                   x["sys"], x["file"]))
    by_sys = sorted({x["sys"] for x in tl_rows})
    pins = sorted(tree["pairs"], key=lambda p: (not p["tail"], p["sys"], p["from"]))
    uniq_pins = []
    seen = set()
    for p in pins:
        key = (p["from"], p["to"])
        if key not in seen:
            seen.add(key)
            uniq_pins.append(p)
    kpi = {"tools": len(tools), "mdl": sum(1 for r in tools if r["cls"] == "MDL"), "sup": sum(1 for r in tools if r["cls"] == "SUP"),
           "issued": sum(1 for r in tools if r["name_status"] == "ISSUED"),
           "proposed": sum(1 for r in tools if r["name_status"] in ("PROPOSED", "DECLARED")),
           "pending": sum(1 for r in tools if r["name_status"] == "PENDING"),
           "conflicts": len([c for c in np_["conflicts"] if c["kind"] != "他系統家族"]),
           "talib_use": sum(x["use"] for x in tree["talib"] if not x["guard"] and x["tail"]),
           "talib_use_history": sum(x["use"] for x in tree["talib"] if not x["guard"] and not x["tail"]),
           "in_pin_files": len({p["from"] for p in uniq_pins if p["tail"]}),
           "in_pin_history": len({p["from"] for p in uniq_pins if not p["tail"]}),
           "lamps": {k2: sum(1 for r in tools if r["lamp"] == k2) for k2 in ("GREEN", "YELLOW", "RED", "GRAY")}}
    order = [k2 for k2, _l, _r in MDL_GROUPS] + ["MDLX"] + [k2 for k2, _l, _r in SUP_GROUPS] + ["SUPX"]
    two = []
    for gk in order:
        rs = [r for r in tools if r["group"] == gk]
        if not rs:
            continue
        two.append({"key": gk, "label": rs[0]["group_label"], "super": rs[0]["super"], "n": len(rs),
                    "issued": sum(1 for r in rs if r["name_status"] == "ISSUED"),
                    "lamps": {k2: sum(1 for r in rs if r["lamp"] == k2) for k2 in ("GREEN", "YELLOW", "RED")},
                    "accel": sum(1 for r in rs if r["accel"] == "OK"), "station": sum(1 for r in rs if r["stations"]),
                    "tested": sum(1 for r in rs if r["test_lamp"]), "single": sum(1 for r in rs if r["ready"] == "SINGLE"),
                    "ready": sum(1 for r in rs if r["ready"] == "READY"), "flatten": sum(1 for r in rs if r["ready"] == "NEEDS_FLATTEN"),
                    "blocked": sum(1 for r in rs if r["ready"] == "BLOCKED_REF"),
                    "used_by": sorted({s2 for r in rs for s2 in r["sup_use"]})})
    flat = {k2: sum(1 for r in tools if r["ready"] == k2) for k2 in ("SINGLE", "READY", "NEEDS_FLATTEN", "BLOCKED_REF", "EXEMPT")}
    flat["old_files_ready"] = sum(r["versions"] - 1 for r in tools if r["ready"] == "READY")
    rep = {
        "tool": "%s %s" % (NAME, VERSION), "at": utc_now(), "via": str(via), "secs": None, "two": two, "flatten": flat,
        "kpi": kpi, "tools": tools, "skipped_bad_name": skipped, "seats_excluded": seats_excluded,
        "naming": {"ledger": LEDGER_NAME, "conflicts": np_["conflicts"],
                   "plan": {f: p for f, p in np_["plan"].items()}, "issued": len(np_["issued"])},
        "intake": intake_view(tree["live_stems"], via),
        "independence": {"pins": uniq_pins, "out_pin": {k2: sorted(v) for k2, v in tree["out_pin"].items()},
                         "name_refs": {f: {s: len(v) for s, v in d.items()} for f, d in tree["in_name"].items()}},
        "talib": {"rows": tl_rows, "files": len(tl_rows), "guard_files": sum(1 for x in tl_rows if x["guard"]),
                  "use": sum(x["use"] for x in tl_rows if not x["guard"] and x["tail"]),
                  "use_history": sum(x["use"] for x in tl_rows if not x["guard"] and not x["tail"]),
                  "use_in_guard": sum(x["use"] for x in tl_rows if x["guard"]),
                  "by_sys": by_sys},
        "register_view": register_view(via), "receipts": receipts(via), "policy": policy_law("L129", via),
        "scan": {"files": tree["files"], "skipped_big": tree["skipped_big"],
                 "ast": "error: " + ast_rows["__error__"] if "__error__" in ast_rows else ("on" if ast else "off")},
        "sources": [fi_name, "VIA_NumberBook_MDL_v0100.jsonl", "VIA_VCGC_FunctionLedger_v0100.jsonl", "VIA_ToolVersion_Lock_v0100.json",
                    LEDGER_NAME, "CLOSEOUT_latest.json", "TEST_latest.json"],
    }
    rep["secs"] = round(time.time() - t0, 1)
    return rep


def build(via: Path = VIA, out: Path | None = None, ast: bool = True, quiet: bool = False) -> tuple:
    out = Path(out) if out else (OUT if via == VIA else via / "VIA_Reports" / "vcgc")
    out.mkdir(parents=True, exist_ok=True)
    vl = visual_lock(via)
    rep = collect(via, ast=ast)
    rep["visual_lock"] = {k: v for k, v in vl.items() if k not in ("mod", "kit")}
    if not vl.get("kit"):
        rep["visual_lock"]["gate"] = "RED"
        (out / JSON_NAME).write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=list), encoding="utf-8")
        print("[%s] RED · 視覺鎖定不可用:%s(不用別的樣式冒充)" % (NAME, vl.get("why")), flush=True)
        return 1, rep
    rep["visual_lock"]["gate"] = "…"
    page = out / HTML_NAME
    page.write_text(render_html(rep, vl["kit"]), encoding="utf-8")
    gate = vl["mod"].check_page(page, vl["sha256"])
    rep["visual_lock"]["gate"] = gate["lamp"]
    rep["visual_lock"]["findings"] = gate["findings"]
    page.write_text(render_html(rep, vl["kit"]), encoding="utf-8")   # 把閘結果印回頁上(內容只多一個字,不影響閘)
    gate2 = vl["mod"].check_page(page, vl["sha256"])
    rep["visual_lock"]["gate"] = gate2["lamp"]
    rep["visual_lock"]["findings"] = gate2["findings"]
    (out / JSON_NAME).write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=list), encoding="utf-8")
    k = rep["kpi"]
    if not quiet or gate2["lamp"] != "GREEN":
        print("[%s %s] %s · 工具 %d(MDL %d · SUP %d)· 名碼 已發 %d · 擬發 %d · 留白 %d · 衝突 %d · TA-Lib 程式使用 %d · "
              "他系統釘 VCGC %d 檔 · 鎖定閘 %s · %ss\n  頁 %s" % (
                  NAME, VERSION, "GREEN" if gate2["lamp"] == "GREEN" else "RED", k["tools"], k["mdl"], k["sup"], k["issued"],
                  k["proposed"], k["pending"], k["conflicts"], k["talib_use"], k["in_pin_files"], gate2["lamp"], rep["secs"], page),
              flush=True)
        for f in gate2["findings"]:
            print("  [鎖定閘] %s" % f, flush=True)
    return (0 if gate2["lamp"] == "GREEN" else 1), rep


def check(via: Path = VIA) -> int:
    rep = collect(via, ast=False)
    k = rep["kpi"]
    reds = []
    if k["talib_use"]:
        reds.append("TA-Lib 程式使用 %d 處" % k["talib_use"])
    if k["conflicts"]:
        reds.append("命名衝突 %d" % k["conflicts"])
    if k["in_pin_files"]:
        reds.append("他系統 %d 檔釘 VCGC 版號(升級會連動 · 對方的檔只攤開不代改)" % k["in_pin_files"])
    yel = len(rep["independence"]["out_pin"])
    print("[%s check] %s · TA-Lib 使用 %d · 命名衝突 %d · 他系統釘 VCGC %d 檔 · VCGC 釘他系統 %d 家族(黃)" % (
        NAME, "RED" if reds else ("YELLOW" if yel else "GREEN"), k["talib_use"], k["conflicts"], k["in_pin_files"], yel), flush=True)
    for p in [p for p in rep["independence"]["pins"] if p["tail"]][:30]:
        print("  [釘] %s(%s)→ %s" % (p["from"], p["sys"], p["to"]), flush=True)
    print("  (舊版版史:他系統釘 VCGC %d 檔 · TA-Lib 使用 %d 處 —— 只增不減,出新版時改)" % (k["in_pin_history"], k["talib_use_history"]), flush=True)
    for x in [x for x in rep["talib"]["rows"] if x["use"] and not x["guard"] and x["tail"]][:20]:
        print("  [TA-Lib] %s · 使用 %d" % (x["file"], x["use"]), flush=True)
    for c in rep["naming"]["conflicts"][:20]:
        print("  [命名] %s · %s · %s" % (c["kind"], c.get("family"), c.get("code")), flush=True)
    return 1 if reds else 0


def naming_cmd(apply: bool, via: Path = VIA) -> int:
    fams, _sk, _ex = discover(via)
    numbers = number_book(via)
    ledger = HERE / LEDGER_NAME if via == VIA else via / "supportive modules" / "registry" / LEDGER_NAME
    np_ = naming_plan(fams, numbers, read_jsonl(ledger), via)
    cnt = {}
    for p in np_["plan"].values():
        cnt[p["status"]] = cnt.get(p["status"], 0) + 1
    print("[%s naming] 已發 %d · %s · 衝突 %d" % (NAME, len(np_["issued"]), " · ".join("%s %d" % kv for kv in sorted(cnt.items())),
                                              len(np_["conflicts"])), flush=True)
    for fam, p in sorted(np_["plan"].items(), key=lambda kv: kv[1].get("code", "~")):
        if p["status"] in ("PROPOSED", "DECLARED", "BLOCKED"):
            print("  %-9s %-16s %s%s" % (p["status"], p.get("code", ""), fam, (" · " + p["why"]) if p.get("why") else ""), flush=True)
    for c in np_["conflicts"]:
        print("  [衝突] %s · %s · %s" % (c["kind"], c.get("family"), c.get("code")), flush=True)
    if not apply:
        print("  (乾跑;--apply 才只增寫入 %s)" % ledger.name, flush=True)
        return 1 if [c for c in np_["conflicts"] if c["kind"] != "他系統家族"] else 0
    lines = naming_apply(fams, numbers, ledger, via)
    print("  [--apply] 寫入 %d 列 → %s" % (len(lines), rel(ledger, via)), flush=True)
    return 0 if lines or not [p for p in np_["plan"].values() if p["status"] in ("PROPOSED", "DECLARED")] else 1


PRUNE_LEDGER = "VIA_VCGC_PruneLedger_v0100.jsonl"


def _selftest_of(path: Path, tag: str) -> int:
    """同行程載入尾版跑 selftest()(輸出吞掉,只看 rc);載入失敗 = 1。"""
    import contextlib
    import io
    try:
        mod = load_module(path, "_vcgc_prune_%s_%d" % (tag, int(time.time() * 1000)))
        fn = getattr(mod, "selftest", None)
        if not callable(fn):
            return 1
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return int(fn() or 0)
    except BaseException:  # noqa: BLE001 — 自測炸掉 = 沒驗證過,照實回 1
        return 1


def prune_plan(via: Path = VIA) -> list:
    """L130 ②:只挑 READY(尾版單檔 · 舊版無人點名)且實測帳 GREEN 對到現在尾版 sha 的家族。"""
    rep = collect(via, ast=False)
    fams, _sk, _ex = discover(via)
    led = ledger_last(via)
    out = []
    for r in rep["tools"]:
        if r["ready"] != "READY":
            continue
        info = fams[r["family"]]
        tail = info["tail"]
        sha16 = hashlib.sha256(tail.read_bytes()).hexdigest()[:16]
        lg = led.get(r["family"], {})
        ok = lg.get("lamp") == "GREEN" and lg.get("sha16") == sha16
        out.append({"family": r["family"], "tail": tail, "old": sorted((f for f in info["files"] if f != tail), key=vnum),
                    "verified": ok, "why": "實測帳 GREEN · sha 對到尾版" if ok else "實測帳沒有對到現在尾版的 GREEN(%s · %s)" % (lg.get("lamp") or "沒量", lg.get("sha16") or "—")})
    return out


def prune_apply(plan: list, ledger: Path, via: Path = VIA) -> list:
    """刪前尾版自測 → 刪舊版 → 刪後自測;不過就還原。刪除帳只增(檔名 · sha256 · 大小 · 證據)。"""
    recs, now = [], utc_now()
    for item in plan:
        if not item["verified"] or not item["old"]:
            continue
        tail = item["tail"]
        before = _selftest_of(tail, "pre")
        if before != 0:
            recs.append({"ts": now, "event": "skipped", "family": item["family"], "why": "刪前尾版自測 rc %d" % before})
            continue
        saved = [(f, f.read_bytes()) for f in item["old"]]
        for f, _b in saved:
            f.unlink()
        after = _selftest_of(tail, "post")
        if after != 0:
            for f, b in saved:
                f.write_bytes(b)
            recs.append({"ts": now, "event": "restored", "family": item["family"], "why": "刪後尾版自測 rc %d → 還原" % after})
            continue
        for f, b in saved:
            recs.append({"ts": now, "event": "pruned", "family": item["family"], "file": rel(f, via), "sha256": hashlib.sha256(b).hexdigest(),
                         "bytes": len(b), "tail": tail.name, "tail_version": "v%04d" % vnum(tail),
                         "proof": {"ledger": item["why"], "selftest_before": before, "selftest_after": after, "refs": 0, "thin": False},
                         "law": "L130", "by": "%s %s" % (NAME, VERSION)})
    if recs:
        with open(ledger, "a", encoding="utf-8") as fh:
            for x in recs:
                fh.write(json.dumps(x, ensure_ascii=False) + "\n")
    return recs


def prune_cmd(apply: bool, via: Path = VIA) -> int:
    plan = prune_plan(via)
    print("[%s prune] READY %d 族 · 已驗證 %d · 舊版檔 %d" % (NAME, len(plan), sum(1 for x in plan if x["verified"]),
                                                       sum(len(x["old"]) for x in plan if x["verified"])), flush=True)
    for x in plan:
        print("  %s %s → 留 %s · 刪 %s · %s" % ("✓" if x["verified"] else "✗", x["family"], x["tail"].name,
                                          ", ".join(f.name for f in x["old"]), x["why"]), flush=True)
    if not apply:
        print("  (乾跑;--apply 才刪 —— 刪前 / 刪後各跑一次尾版自測,刪後不過就還原)", flush=True)
        return 0
    recs = prune_apply(plan, HERE / PRUNE_LEDGER if via == VIA else via / "supportive modules" / "registry" / PRUNE_LEDGER, via)
    cnt = {}
    for x in recs:
        cnt[x["event"]] = cnt.get(x["event"], 0) + 1
    print("  [--apply] %s → %s" % (" · ".join("%s %d" % kv for kv in sorted(cnt.items())) or "無動作", PRUNE_LEDGER), flush=True)
    return 0 if not cnt.get("restored") else 1


def signature(via: Path = VIA) -> str:
    h = hashlib.sha256()
    reg = via / "supportive modules" / "registry"
    for p in sorted(list(reg.glob("*.py")) + list(reg.glob("*.json")) + list(reg.glob("*.jsonl"))
                    + [via / "VIA_Reports" / "closeout" / "CLOSEOUT_latest.json", via / "VIA_Reports" / "vcgc" / "TEST_latest.json"]):
        try:
            st = p.stat()
            h.update(("%s|%d|%d\n" % (p.name, st.st_mtime_ns, st.st_size)).encode())
        except OSError:
            continue
    return h.hexdigest()[:16]


def watch(interval: int = 300, via: Path = VIA, rounds: int = 0) -> int:
    last, n = None, 0
    while True:
        sig = signature(via)
        if sig != last:
            rc, _rep = build(via, quiet=True)
            print("[%s watch] %s · 簽章 %s · rc %d" % (NAME, utc_now(), sig, rc), flush=True)
            last = sig
        n += 1
        if rounds and n >= rounds:
            return 0
        try:
            time.sleep(max(30, interval))
        except KeyboardInterrupt:
            return 0


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import shutil
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    chk("① 歸屬:CGC → VCGC · VDF 夾 → VDF · VRN_ENG → VRN-2 · VRN2_ → VRN-2 · registry 的 via_* → VCGC · 其他 → 共用",
        system_of("supportive modules/registry/CGC_MDL149_X_v0100.py") == "VCGC" and system_of("functional modules/VDF/engine/a.py") == "VDF"
        and system_of("functional modules/VRN/VRN_ENG001_A_v0100.py") == "VRN-2" and system_of("x/VRN2_Rows_v0101.py") == "VRN-2"
        and system_of("supportive modules/registry/via_ocr_super_v0102.py") == "VCGC" and system_of("supportive modules/SUP_MDL1_A.py") == "共用")
    chk("② 分類:token 席位 → SUP · ShadowMerge → SUP · AccelBridge → SUP · NlpLayoutDoor → SUP · 主控台 → MDL · 檔名自帶 → 照檔名",
        classify("X", "token")[0] == "SUP" and classify("ShadowMerge")[0] == "SUP" and classify("AccelBridge")[0] == "SUP"
        and classify("NlpLayoutDoor")[0] == "SUP" and classify("VeritasCentralGovernanceConsole")[0] == "MDL"
        and classify("ToolMatrix", "", "MDL") == ("MDL", "檔名自帶類別(新命名)")
        and classify("NetUnified", family="SUP_MDL740_NetUnified")[0] == "SUP" and classify("Panorama", family="VIA_Panorama")[0] == "MDL")
    chk("③b 版號:_v0225.json · _v0100.jsonl · _v0117.py 都認得;沒版號 = -1",
        vnum("VIA_VCGC_FunctionInventory_SSOT_v0225.json") == 225 and vnum("X_v0100.jsonl") == 100 and vnum("CGC_MDL1_A_v0117.py") == 117
        and vnum("CGC_MDL023_AutoCodeRegistryEngine.py") == -1)
    chk("③ 英文名:CGC_MDL158_VIAPanoramaAuditRepair → VIAPanoramaAuditRepair · VIA_VCGC_SUP002_Foo → Foo",
        english_of("CGC_MDL158_VIAPanoramaAuditRepair") == "VIAPanoramaAuditRepair" and english_of("VIA_VCGC_SUP002_Foo") == "Foo")
    txt = 'import talib\nx = talib.SMA(c)\n# 註解 TA-Lib\nsubprocess.run("pip install TA-Lib")\n說明:有人貼了 pip install TA-Lib 的舊區塊\n'
    chk("④ TA-Lib:.py 的 import / talib.SMA( / subprocess 叫 pip 算使用(3);說明文字只算出現 · .ps1 的 pip 行算使用、# 註解不算",
        talib_use(txt, ".py") == 3 and len(TALIB_MENTION_RX.findall(txt)) >= 3
        and talib_use("talib = []\ntalib.append(x)\nif TALIB.search(line):\n    pass\n", ".py") == 0
        and talib_use("pip install TA-Lib\n# pip install TA-Lib\n", ".ps1") == 1)
    chk("⑤ 釘版偵測:CGC_MDL149_VeritasCentralGovernanceConsole_v0192.py 抓得到家族;只寫家族名不算釘版",
        [m.group(1) for m in PIN_RX.finditer('p = "CGC_MDL149_VeritasCentralGovernanceConsole_v0192.py"')] == ["CGC_MDL149_VeritasCentralGovernanceConsole"]
        and not PIN_RX.search("glob('CGC_MDL149_VeritasCentralGovernanceConsole_v*.py')"))
    esc = t('<script>#ff0000 https://x.example "q"</script>')
    chk("⑥ 轉義:< > 引號轉掉 · # 與 :// 換具名實體(鎖定閘不會誤判寫死色 / 外連)",
        "<script>" not in esc and "#" not in esc and "://" not in esc and "&num;ff0000" in esc)

    with tempfile.TemporaryDirectory(prefix="via_toolmatrix_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        reg = via / "supportive modules" / "registry"
        (reg / "VIA_NumberBooks").mkdir(parents=True)
        for n in ("CGC_MDL001_Alpha_v0100.py", "CGC_MDL001_Alpha_v0101.py", "CGC_MDL158_VIAPanoramaAuditRepair_v0117.py",
                  "CGC_MDL002_Beta_v0100.py", "CGC_MDL003_NoNumber_v0100.py", "VIA_VCGC_MDL005_Gamma_v0100.py"):
            (reg / n).write_text("# x\n", encoding="utf-8")
        nb = [{"code": "VIA-VCGC-MDL%04d" % i, "name": n, "version": "v0100", "updated_at": "2026-11-13T00:00:00Z", "sub": "VCGC"}
              for i, n in enumerate(["CGC_MDL001_Alpha_v0101", "CGC_MDL158_VIAPanoramaAuditRepair_v0117", "CGC_MDL002_Beta_v0100",
                                     "VIA_VCGC_MDL005_Gamma_v0100"], 1)]
        nb[2]["source"] = "supportive modules/registry/CGC_MDL002_Beta_v0100.py"
        nb.append({"code": "VIA-VCGC-MDL9999", "name": "CGC_MDL002_Beta_v0195", "version": "v0195", "updated_at": "2026-11-13T00:00:00Z",
                   "sub": "VCGC", "source": "docs/handoff/ai/intake_x/v0195/CGC_MDL002_Beta_v0195.py"})   # 收容副本:版號較高,不能冒充
        (reg / "VIA_NumberBooks" / "VIA_NumberBook_MDL_v0100.jsonl").write_text("\n".join(json.dumps(x) for x in nb) + "\n", encoding="utf-8")
        (reg / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps({"token": {"path": "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL158_VIAPanoramaAuditRepair_v0117.py"}}), encoding="utf-8")
        fams, _sk, _ex = discover(via)
        numbers = number_book(via)
        np_ = naming_plan(fams, numbers, [], via)
        pl = np_["plan"]
        chk("⑦ 發名乾跑:舊家族照舊號序給號、跳過新檔自帶的 MDL005 · token 席位 → SUP001 · 沒編號 → 留白 · 新檔有編號 → DECLARED",
            pl["CGC_MDL001_Alpha"]["code"] == "VIA_VCGC_MDL001" and pl["CGC_MDL002_Beta"]["code"] == "VIA_VCGC_MDL002"
            and pl["CGC_MDL158_VIAPanoramaAuditRepair"]["code"] == "VIA_VCGC_SUP001" and pl["CGC_MDL003_NoNumber"]["status"] == "PENDING"
            and pl["VIA_VCGC_MDL005_Gamma"]["status"] == "DECLARED" and fams["CGC_MDL001_Alpha"]["versions"] == 2, pl)
        rb = reg_for("CGC_MDL002_Beta", fams["CGC_MDL002_Beta"]["tail"], numbers, via)
        chk("⑦b 對號:收容夾裡同名更高版(v0195)的編號不冒充活樹尾版 —— 取尾版實際路徑那一列",
            rb.get("code") == "VIA-VCGC-MDL0003", rb)
        led = reg / LEDGER_NAME
        first = naming_apply(fams, numbers, led, via)
        second = naming_apply(fams, numbers, led, via)
        rows = read_jsonl(led)
        chk("⑧ --apply 只增:第一次寫 4 列(每列帶 版本 · 時間 · 中央編號)· 第二次 0 列(號跟家族走,不重發)",
            len(first) == 4 and second == [] and all(r.get("updated_at") and r.get("tail_version") and r.get("reg_code") for r in rows), len(first))
        (reg / "VIA_VCGC_MDL001_Clash_v0100.py").write_text("# x\n", encoding="utf-8")
        fams2, _a, _b = discover(via)
        np2 = naming_plan(fams2, numbers, read_jsonl(led), via)
        third = naming_apply(fams2, numbers, led, via)
        chk("⑨ 衝突:新檔自帶的 MDL001 已發給 Alpha → BLOCKED · 有衝突一律不發(0 列)",
            np2["plan"]["VIA_VCGC_MDL001_Clash"]["status"] == "BLOCKED" and third == [] and np2["conflicts"])
        (reg / "VIA_VCGC_MDL001_Clash_v0100.py").unlink()
        vdf = via / "functional modules" / "VDF" / "engine"
        vdf.mkdir(parents=True)
        (vdf / "VDF_ENG001_A_v0100.py").write_text(
            'p = "CGC_MDL001_Alpha_v0101.py"\nimport importlib\nq = glob("CGC_MDL002_Beta_v*.py")\n# CGC_MDL158_VIAPanoramaAuditRepair_v0117.py 只是註解\n',
            encoding="utf-8")
        (reg / "CGC_MDL002_Beta_v0100.py").write_text('x = "VDF_ENG001_A_v0100.py"\n', encoding="utf-8")
        tree = scan_tree(via)
        chk("⑩ 獨立性:VDF 釘 Alpha 版號 → 抓到 · 名引 Beta(glob)→ 黃 · 註解不算 · VCGC 的 Beta 釘 VDF 版 → 抓到",
            "VDF" in tree["in_pin"].get("CGC_MDL001_Alpha", {}) and "CGC_MDL158_VIAPanoramaAuditRepair" not in tree["in_pin"]
            and "VDF" in tree["in_name"].get("CGC_MDL002_Beta", {}) and "VDF_ENG001_A" in tree["out_pin"].get("CGC_MDL002_Beta", set()),
            {k2: list(v) for k2, v in tree["in_pin"].items()})
        out = Path(td) / "out"
        rep = collect(via, ast=False)
        html_text = render_html(dict(rep, visual_lock={"gate": "—"}), ":root{--vl-bg:x}")
        chk("⑪ 出頁:十個分頁(兩大功能 · 中央管理工具 · 支援工具 · 單檔收斂 · 收尾 …)都在 · 表格有資料 · 0 外連 · 沒有寫死 # 色",
            all('data-pane="%s"' % p in html_text for p in ("two", "mdl", "sup", "flat", "close", "int", "indep", "talib", "reg", "rule"))
            and "VIA_VCGC_SUP001" in html_text and "http" not in html_text.replace("http-equiv", "")
            and not re.search(r"(?<![\w-])#[0-9a-fA-F]{3,8}\b", html_text))
        shutil.rmtree(out, ignore_errors=True)

    with tempfile.TemporaryDirectory(prefix="via_toolmatrix_prune_") as td3:
        via = Path(td3) / "VeritasIntelligenceAnalytics"
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        (reg / "CGC_MDL001_Alpha_v0100.py").write_text("def selftest():\n    return 0\n", encoding="utf-8")
        tail = reg / "CGC_MDL001_Alpha_v0101.py"
        tail.write_text("def selftest():\n    return 0\n", encoding="utf-8")
        (reg / "CGC_MDL002_Beta_v0100.py").write_text("def selftest():\n    return 0\n", encoding="utf-8")
        (reg / "CGC_MDL002_Beta_v0101.py").write_text("def selftest():\n    return 0\n", encoding="utf-8")
        sha = hashlib.sha256(tail.read_bytes()).hexdigest()[:16]
        (reg / "VIA_VCGC_FunctionLedger_v0100.jsonl").write_text(
            json.dumps({"id": "family:CGC_MDL001_Alpha", "lamp": "GREEN", "sha16": sha, "ts": "x"}) + "\n"
            + json.dumps({"id": "family:CGC_MDL002_Beta", "lamp": "GREEN", "sha16": "0000000000000000", "ts": "x"}) + "\n", encoding="utf-8")
        plan = {x["family"]: x for x in prune_plan(via)}
        recs = prune_apply(list(plan.values()), reg / PRUNE_LEDGER, via)
        chk("⑭ prune:READY 且實測帳 GREEN 對到尾版 sha → 刪舊版並記帳(sha256 · 大小 · 證據)· 帳的 sha 對不上 → 不刪",
            plan.get("CGC_MDL001_Alpha", {}).get("verified") and not plan.get("CGC_MDL002_Beta", {}).get("verified")
            and not (reg / "CGC_MDL001_Alpha_v0100.py").exists() and (reg / "CGC_MDL002_Beta_v0100.py").exists()
            and [x["event"] for x in recs] == ["pruned"] and recs[0]["sha256"] and recs[0]["bytes"] > 0, [x["event"] for x in recs])
        (reg / "CGC_MDL003_Gamma_v0100.py").write_text("def selftest():\n    return 0\n", encoding="utf-8")
        g = reg / "CGC_MDL003_Gamma_v0101.py"
        g.write_text("from pathlib import Path\ndef selftest():\n    return 0 if (Path(__file__).parent / ('CGC_MDL003_Gamma_v' + '0100.py')).exists() else 1\n", encoding="utf-8")
        recs2 = prune_apply([{"family": "CGC_MDL003_Gamma", "tail": g, "old": [reg / "CGC_MDL003_Gamma_v0100.py"], "verified": True, "why": "t"}],
                            reg / PRUNE_LEDGER, via)
        chk("⑮ prune 刪後尾版自測不過 → 舊版還原 · 帳記 restored(不留半刪)",
            (reg / "CGC_MDL003_Gamma_v0100.py").exists() and [x["event"] for x in recs2] == ["restored"], [x["event"] for x in recs2])

    # 真樹:視覺鎖定 kit 套上去 · 當場過鎖定閘 · 只寫自己的輸出(命名帳 / 號冊 / 盤點冊不動)
    vl = visual_lock(VIA)
    if not vl.get("kit"):
        chk("⑫ 真樹視覺鎖定可用", False, vl.get("why"))
    else:
        watch_files = [HERE / LEDGER_NAME, HERE / "VIA_NumberBooks" / "VIA_NumberBook_MDL_v0100.jsonl",
                       HERE / "VIA_ToolVersion_Lock_v0100.json"]
        before = {str(p): (p.read_bytes() if p.is_file() else None) for p in watch_files}
        with tempfile.TemporaryDirectory(prefix="via_toolmatrix_out_") as td2:
            rc, rep = build(VIA, out=Path(td2), ast=False, quiet=True)
            page = Path(td2) / HTML_NAME
            gate = vl["mod"].check_page(page, vl["sha256"]) if page.is_file() else {"lamp": "RED", "findings": ["沒出頁"]}
            k = rep["kpi"]
            chk("⑫ 真樹出頁:工具家族 ≥ 280 · token 工具判 SUP(鎖席)· 主控台判 MDL · 視覺鎖定閘 GREEN",
                rc == 0 and k["tools"] >= 280 and gate["lamp"] == "GREEN"
                and any(r["family"] == "CGC_MDL158_VIAPanoramaAuditRepair" and r["cls"] == "SUP" for r in rep["tools"])
                and any(r["family"] == "CGC_MDL149_VeritasCentralGovernanceConsole" and r["cls"] == "MDL" for r in rep["tools"]),
                "工具 %d · 閘 %s %s" % (k["tools"], gate["lamp"], gate["findings"][:2]))
            tok = next((r for r in rep["tools"] if r["family"] == "CGC_MDL158_VIAPanoramaAuditRepair"), {})
            con = next((r for r in rep["tools"] if r["family"] == "CGC_MDL149_VeritasCentralGovernanceConsole"), {})
            chk("⑫c 兩大功能:token 工具在「Token-Saving」組 · 主控台在「主控台 / 入口」組且薄尾待合成 · 總覽每組有列 · 收斂五態加總 = 家族數",
                tok.get("group") == "TOKEN" and con.get("group") == "CONSOLE" and con.get("ready") == "NEEDS_FLATTEN" and rep["two"]
                and sum(rep["flatten"][k3] for k3 in ("SINGLE", "READY", "NEEDS_FLATTEN", "BLOCKED_REF", "EXEMPT")) == k["tools"],
                (tok.get("group"), con.get("group"), con.get("ready"), rep["flatten"]))
            chk("⑫b 真樹:盤點冊尾版讀得到(token 工具對到測站 C-token)· 政策冊尾版讀得到 L129",
                "C-token" in tok.get("stations", []) and rep["policy"]["status"] == "ACTIVE", (tok.get("stations"), rep["policy"]["status"]))
        after = {str(p): (p.read_bytes() if p.is_file() else None) for p in watch_files}
        chk("⑬ 唯讀:build 不動命名帳 / 號冊 / 工具鎖冊", before == after)
    bad = len(ok) - sum(ok)
    print("[%s] %s %s --selftest · %d/%d" % ("PASS" if not bad else "FAIL", NAME, VERSION, len(ok) - bad, len(ok)), flush=True)
    return 0 if not bad else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "help"):
        print(__doc__)
        return 0
    if "--selftest" in args or args[0] in ("selftest", "test"):
        return selftest()
    verb = args[0]
    if verb == "build":
        out = Path(args[args.index("--out") + 1]) if "--out" in args else None
        return build(VIA, out=out, ast="--no-ast" not in args, quiet="--quiet" in args)[0]
    if verb == "naming":
        return naming_cmd("--apply" in args)
    if verb == "check":
        return check(VIA)
    if verb == "prune":
        return prune_cmd("--apply" in args)
    if verb == "watch":
        iv = int(args[args.index("--interval") + 1]) if "--interval" in args else 300
        return watch(iv)
    print("[%s] 不認得的動詞:%s(build · naming · check · prune · watch · --selftest)" % (NAME, verb), flush=True)
    return 2


if __name__ == "__main__":
    sys.exit(main())
