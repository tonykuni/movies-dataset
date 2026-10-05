#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC PanoramaConsistency v0101 — VCGC 全景一致性檢視(v0101:K1/K2 只看 def selftest( 之前的正文,夾具字串不當出網/橋;其餘同 v0100)(唯讀;操作員令 2026-10-06 八項)。

只讀整棵樹,只寫自己兩處:docs/handoff/ai/VCGC_PanoramaCard_<日>.md/.json 與 VIA_Reports/review/vcgc_panorama/PANORAMA_latest.json。
不改 VDF / VRN / 任何冊(L111 ②);修正由操作員+AI 看卡後出薄尾。
只看「尾版」:同夾同族取最大版號;前版是凍結件(只增不減),不算帳。
K1 加速器   每支尾版 .py 要有 [VIA:ACCEL-BRIDGE] / VeritasCeleritas_v1141;每支尾版 .ps1 要有 [VIA:PS-ACCEL] / VeritasCeleritas.PS7 / Initialize-VCAccel   缺=紅
K2 VDF 網路 VDF 尾版 .py 有出網字樣(requests/httpx/yfinance/akshare/fredapi/urllib…)就要掛 [VIA:NET-BRIDGE] / VIA_NetSupport / via_net_unified  缺=紅;無同意閘 VIA_NET_CONSENT/VIA_NO_NET=黃
K3 掌握力   VDF / VRN SystemManager 尾版:--selftest · status/inventory 類動詞 · 讀自己 SSOT/registry · RESULT 新鮮度(>7 天=黃)
K4 SSOT 下放 中央 registry 各家族冊數 vs 子系統自己的 SSOT/ 與 Index;VDF 未下放=紅;VRN 有 Index+號=綠;其他家族=黃(未納入計畫)
K5 一致性   同族冊散在 ≥2 處:頂層欄位不同=紅、同頭內容漂移=黃;regex 跨子系統拷貝=黃
K6 邊界     尾版檔內出現別子系統路徑字樣:附近 3 行有寫檔動詞=紅(疑似越界寫);只讀=黃(列出給人看)
K7 LIB 環境 尾版 import 的第三方套件 vs requirements*/VIA_Env_Requirements* 聯集;未列=黃;本直譯器 import 不到=黃(註明直譯器)
K8 VRN 短指令 Register-VIA-Commands 鏈所有 via-*vrn* / 內含 VRN_ 的函式(後版覆蓋前版):走 via-vcgc run=綠 · 直呼 python=黃(待歸 VCGC 動詞)· 純 PS 邏輯=黃(待 PY 化);所在檔無 PS-ACCEL=紅
動詞: audit [--json] · --selftest    沙盒鍵: VIA_ROOT
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

ME = Path(__file__).resolve()
NAME = ME.stem
TAG = "v0101"
EXCL = {"references", "intake", "_superseded", "VIA_RetiredEngines", "_quarantine_pip_vendor", "__pycache__", ".venv", "venv", "node_modules", ".git", "docs", "VIA_Reports", "_quarantine"}
PY_ACCEL = re.compile(r"\[VIA:ACCEL-BRIDGE|VeritasCeleritas_v1141|import VIA_SuperAccel_Module")
PS_ACCEL = re.compile(r"\[VIA:PS-ACCEL|VeritasCeleritas\.PS7|Initialize-VCAccel|VIA_PS_Accel_Module")
PY_ACCEL_EXEMPT = re.compile(r"^(VIA_SuperAccel_Module|VeritasCeleritas_v\d+|__init__|setup|conftest)")
PS_ACCEL_EXEMPT = re.compile(r"^(VeritasCeleritas\.PS7|VIA_PS_Accel_Module)")
NET_USE = re.compile(r"\b(requests\.|import requests|httpx|aiohttp|urllib\.request|yfinance|akshare|fredapi|pandas_datareader|http\.client|socket\.create_connection|urlopen\()")
NET_TOOL = re.compile(r"\[VIA:NET-BRIDGE|VIA_NetSupport|via_net_unified|SUP_MDL740|NetUnified")
NET_GATE = re.compile(r"VIA_NET_CONSENT|VIA_NO_NET|VIA_SCRAPE_CONSENT")
WRITE_PY = re.compile(r"write_text\(|write_bytes\(|open\([^)]*['\"][wax]|to_json\(|to_csv\(|to_excel\(|to_parquet\(|shutil\.(copy|move)|os\.(rename|replace|remove)|\.unlink\(|mkdir\(|json\.dump\(")
WRITE_PS = re.compile(r"Set-Content|Out-File|Copy-Item|Move-Item|Remove-Item|New-Item|\[IO\.File\]::Write|Add-Content")
LOCAL_PREFIX = re.compile(r"^(VIA|via|VRN|vrn|VDF|vdf|CGC|SUP|VAP|GIF|VRM|_sa_)")
REGEX_KEYS = ("pattern", "regex", "re", "rx", "strict", "extraction", "catch_all")
SUBS = ("VCGC", "VDF", "VRN")
CROSS = {"VRN": [r"functional modules[\\/]+VDF", r"supportive modules[\\/]+registry"],
         "VDF": [r"functional modules[\\/]+VRN", r"supportive modules[\\/]+registry"],
         "VCGC": [r"functional modules[\\/]+VDF", r"functional modules[\\/]+VRN"]}
REQ_GLOBS = ("requirements*.txt", "supportive modules/registry/VIA_Env_Requirements*.txt", "**/requirements*.txt")


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _root() -> Path:
    if os.environ.get("VIA_ROOT"):
        return Path(os.environ["VIA_ROOT"])
    p = ME
    while p.parent != p:
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p
        p = p.parent
    return ME.parents[2]


def _paths() -> dict:
    r = _root()
    return {"root": r, "registry": r / "supportive modules" / "registry", "sup": r / "supportive modules",
            "vdf": r / "functional modules" / "VDF", "vrn": r / "functional modules" / "VRN",
            "cards": r / "docs" / "handoff" / "ai", "report": r / "VIA_Reports" / "review" / "vcgc_panorama"}


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _vnum(name: str) -> int:
    m = re.search(r"_v(\d{2,4})(?:[A-Za-z0-9]*)?(?:\.[A-Za-z0-9]+)?$", name)
    if m:
        return int(m.group(1))
    m = re.search(r"-v(\d{2,4})\.", name)
    return int(m.group(1)) if m else -1


def _family(name: str) -> str:
    stem = re.sub(r"_sha[0-9a-f]{8,}$", "", Path(name).stem)
    stem = re.sub(r"[_-]v\d{2,4}[A-Za-z0-9]*$", "", stem)
    return stem


def _read(p: Path) -> str:
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "utf-16", "cp950", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return ""


def _skip(p: Path, root: Path) -> bool:
    try:
        parts = set(p.relative_to(root).parts[:-1])
    except ValueError:
        parts = set(p.parts)
    return bool(parts & EXCL)


def _tails(dirs, root: Path, exts, recursive=True) -> list:
    """每(夾, 族, 副檔名)取最大版號;無版號視為自己一族。"""
    best: dict = {}
    for d in dirs:
        if not d.is_dir():
            continue
        it = d.rglob("*") if recursive else d.glob("*")
        for p in it:
            if not p.is_file() or p.suffix.lower() not in exts or _skip(p, root):
                continue
            k = (p.parent, _family(p.name), p.suffix.lower())
            v = _vnum(p.name)
            if k not in best or v > best[k][0] or (v == best[k][0] and p.name > best[k][1].name):
                best[k] = (v, p)
    return sorted((v[1] for v in best.values()), key=lambda q: str(q))


def _sub_of(p: Path, P: dict) -> str:
    s = str(p)
    if s.startswith(str(P["vrn"])):
        return "VRN"
    if s.startswith(str(P["vdf"])):
        return "VDF"
    return "VCGC"


def _rel(p: Path, P: dict) -> str:
    try:
        return str(p.relative_to(P["root"]))
    except ValueError:
        return str(p)


# ───────────────────────── K1 加速器 ─────────────────────────
def k1_accel(P: dict) -> dict:
    pys = _tails([P["vrn"], P["vdf"], P["sup"]], P["root"], {".py"})
    pss = _tails([P["vrn"], P["vdf"], P["sup"]], P["root"], {".ps1"}) + _tails([P["root"]], P["root"], {".ps1"}, recursive=False)
    rows = []
    per = {s: {"py_total": 0, "py_missing": 0, "ps_total": 0, "ps_missing": 0} for s in SUBS}
    for p in pys:
        if PY_ACCEL_EXEMPT.match(p.stem):
            continue
        txt = _read(p)
        if txt.count("\n") < 12:
            continue
        s = _sub_of(p, P)
        per[s]["py_total"] += 1
        if not PY_ACCEL.search(txt):
            per[s]["py_missing"] += 1
            rows.append({"sub": s, "kind": "py", "file": _rel(p, P), "lamp": "RED"})
    for p in pss:
        if PS_ACCEL_EXEMPT.match(p.stem):
            continue
        txt = _read(p)
        if txt.count("\n") < 12:
            continue
        s = _sub_of(p, P)
        per[s]["ps_total"] += 1
        if not PS_ACCEL.search(txt):
            per[s]["ps_missing"] += 1
            rows.append({"sub": s, "kind": "ps1", "file": _rel(p, P), "lamp": "RED"})
    lamp = "RED" if rows else "GREEN"
    return {"k": "K1", "zh": "加速器", "lamp": lamp, "per": per, "rows": rows}


# ───────────────────────── K2 VDF 網路工具 ─────────────────────────
def k2_vdf_net(P: dict) -> dict:
    rows = []
    n_net = 0
    for p in _tails([P["vdf"]], P["root"], {".py"}):
        txt = _read(p).split("\ndef selftest(")[0]
        if not NET_USE.search(txt):
            continue
        n_net += 1
        tool, gate = bool(NET_TOOL.search(txt)), bool(NET_GATE.search(txt))
        if not tool:
            rows.append({"file": _rel(p, P), "lamp": "RED", "why": "出網但無網路工具橋([VIA:NET-BRIDGE]/VIA_NetSupport/via_net_unified)"})
        elif not gate:
            rows.append({"file": _rel(p, P), "lamp": "YELLOW", "why": "有橋但無同意閘字樣(VIA_NET_CONSENT/VIA_NO_NET)"})
    red = sum(1 for x in rows if x["lamp"] == "RED")
    return {"k": "K2", "zh": "VDF 網路工具", "lamp": "RED" if red else ("YELLOW" if rows else "GREEN"), "net_files": n_net, "rows": rows}


# ───────────────────────── K3 System Manager 掌握力 ─────────────────────────
def _manager_tail(d: Path, stem: str):
    hits = sorted(d.glob(stem + "_v*.py"), key=lambda q: _vnum(q.name)) if d.is_dir() else []
    return hits[-1] if hits else None


def k3_managers(P: dict) -> dict:
    rows = []
    for sub, d, stem, own in (("VDF", P["vdf"], "VDF_SystemManager", ["registry", "SSOT"]), ("VRN", P["vrn"], "VRN_SystemManager", ["SSOT", "registry", "knowledge"])):
        t = _manager_tail(d, stem)
        if not t:
            rows.append({"sub": sub, "tail": None, "lamp": "RED", "why": "SystemManager 尾版不在"})
            continue
        txt = _read(t)
        chain = len(list(d.glob(stem + "_v*.py")))
        has_self = "--selftest" in txt
        has_status = bool(re.search(r"\b(status|inventory|census|panorama|health)\b", txt))
        reads_own = any(o in txt for o in own)
        own_dirs = {o: (d / o).is_dir() for o in own}
        rep = P["root"] / "VIA_Reports" / sub.lower()
        newest = None
        if rep.is_dir():
            fs = [f for f in rep.rglob("RESULT_*_latest.json")]
            if fs:
                newest = max(f.stat().st_mtime for f in fs)
        age = (time.time() - newest) / 86400 if newest else None
        flags = []
        if not has_self:
            flags.append("無 --selftest")
        if not has_status:
            flags.append("無 status/inventory 類動詞")
        if not reads_own:
            flags.append("未讀自己的 SSOT/registry")
        if age is None:
            flags.append("無 RESULT_*_latest.json(從未留結果)")
        elif age > 7:
            flags.append("RESULT 最新 %.0f 天前" % age)
        lamp = "RED" if (not has_self or not reads_own) else ("YELLOW" if flags else "GREEN")
        rows.append({"sub": sub, "tail": t.name, "chain_len": chain, "selftest": has_self, "status_verb": has_status, "reads_own": reads_own,
                     "own_dirs": own_dirs, "result_age_days": (round(age, 1) if age is not None else None), "lamp": lamp, "why": ";".join(flags)})
    lamp = "RED" if any(r["lamp"] == "RED" for r in rows) else ("YELLOW" if any(r["lamp"] == "YELLOW" for r in rows) else "GREEN")
    return {"k": "K3", "zh": "SystemManager 掌握力", "lamp": lamp, "rows": rows}


# ───────────────────────── K4 SSOT 下放 ─────────────────────────
def _fam_owner(fam: str) -> str:
    f = fam.upper()
    if f.startswith(("VRN_", "VIA_VRN", "VIA_POLICY_VRN", "VIA_ESSENTIA_CARDBOOK_VRN", "VIA_WORKFLOW_VRN")):
        return "VRN"
    if f.startswith(("VDF_", "VIA_VDF", "VDF2_")):
        return "VDF"
    if f.startswith(("CGC_", "VIA_POLICY", "VIA_NUMBERING", "VIA_SSOT_", "VIA_CENTRAL", "VIA_UI_", "VIA_WORKFLOW", "VIA_ESSENTIA", "SUP_", "VIA_ENV", "VIA_LIB", "VIA_FINAL", "VIA_TOOL", "VIA_HANDOFF")):
        return "VCGC"
    return "OTHER"


def k4_ssot_down(P: dict) -> dict:
    fams: dict = defaultdict(set)
    if P["registry"].is_dir():
        for p in P["registry"].glob("*"):
            if p.is_file() and p.suffix.lower() in (".json", ".csv") and not _skip(p, P["root"]):
                fams[_fam_owner(_family(p.name))].add((_family(p.name), p.suffix.lower()))
    rows = []
    for sub, d, idx_glob in (("VRN", P["vrn"], "registry/VRN_SSOT_Index_v*.json"), ("VDF", P["vdf"], "registry/VDF_SSOT_Index_v*.json")):
        idx = sorted(d.glob(idx_glob), key=lambda q: _vnum(q.name)) if d.is_dir() else []
        ssot_n = len([x for x in (d / "SSOT").glob("*") if x.is_file()]) if (d / "SSOT").is_dir() else 0
        numbered = 0
        n_idx = 0
        if idx:
            try:
                dd = json.loads(_read(idx[-1]))
                ents = dd.get("entries", {})
                live = [e for e in ents.values() if isinstance(e, dict) and e.get("status") != "RETIRED"]
                n_idx = len(live)
                numbered = sum(1 for e in live if e.get("ssot_no"))
            except ValueError:
                pass
        central = len(fams.get(sub, ()))
        if not idx or ssot_n == 0:
            lamp, why = ("RED" if central else "GRAY"), ("中央有 %d 冊,子系統無 SSOT/ 與 Index → 未下放" % central if central else "中央無此家族冊")
        elif numbered < n_idx:
            lamp, why = "YELLOW", "Index %d 鍵,發號 %d,未發 %d" % (n_idx, numbered, n_idx - numbered)
        else:
            lamp, why = "GREEN", "Index %d 鍵全有號 · SSOT/ %d 冊" % (n_idx, ssot_n)
        rows.append({"sub": sub, "central_books": central, "ssot_files": ssot_n, "index": (idx[-1].name if idx else None), "index_keys": n_idx, "numbered": numbered, "lamp": lamp, "why": why})
    other = sorted({f for f, _ in fams.get("OTHER", ())})
    rows.append({"sub": "VCGC", "central_books": len(fams.get("VCGC", ())), "lamp": "GREEN", "why": "VCGC 自己的冊留中央(長相契約 · 政策 · 編號)"})
    rows.append({"sub": "OTHER", "central_books": len(fams.get("OTHER", ())), "families": other[:40], "lamp": ("YELLOW" if other else "GRAY"), "why": "其他家族 %d 族未納入下放計畫" % len(other)})
    lamp = "RED" if any(r["lamp"] == "RED" for r in rows) else ("YELLOW" if any(r["lamp"] == "YELLOW" for r in rows) else "GREEN")
    return {"k": "K4", "zh": "SSOT 下放", "lamp": lamp, "rows": rows}


# ───────────────────────── K5 一致性 ─────────────────────────
def _head(p: Path):
    if p.suffix.lower() == ".json":
        try:
            d = json.loads(_read(p))
        except ValueError:
            return ("<bad-json>",)
        if isinstance(d, dict):
            return tuple(sorted(d.keys()))
        if isinstance(d, list) and d and isinstance(d[0], dict):
            return tuple(sorted(d[0].keys()))
        return ("<non-object>",)
    if p.suffix.lower() == ".csv":
        t = _read(p).splitlines()
        return tuple(t[0].split(",")) if t else None
    return None


def _regex_strings(obj, acc: set, parent_key: str = ""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            _regex_strings(v, acc, str(k))
    elif isinstance(obj, list):
        for v in obj:
            _regex_strings(v, acc, parent_key)
    elif isinstance(obj, str):
        s = obj.strip()
        if len(s) >= 8 and (parent_key.lower() in REGEX_KEYS or re.search(r"\\[dswbDSW(]|\(\?[:<!=]", s)):
            acc.add(s)


def k5_consistency(P: dict) -> dict:
    books = _tails([P["vrn"], P["vdf"], P["registry"]], P["root"], {".json", ".csv"})
    by_fam: dict = defaultdict(list)
    for p in books:
        if p.stat().st_size > 20_000_000:
            continue
        by_fam[(_family(p.name), p.suffix.lower())].append(p)
    dup_rows = []
    for (fam, ext), ps in sorted(by_fam.items()):
        dirs = {p.parent for p in ps}
        if len(dirs) < 2:
            continue
        heads = {}
        for p in ps:
            heads[p] = _head(p)
        hs = {h for h in heads.values() if h is not None}
        shas = {_sha(p) for p in ps}
        if len(hs) > 1:
            dup_rows.append({"family": fam + ext, "lamp": "RED", "where": [_rel(p, P) for p in ps], "why": "同族異頭(頂層欄位不同)"})
        elif len(shas) > 1:
            dup_rows.append({"family": fam + ext, "lamp": "YELLOW", "where": [_rel(p, P) for p in ps], "why": "同頭內容漂移"})
    # regex 跨子系統拷貝
    pat_sub: dict = defaultdict(set)
    for p in books:
        if p.suffix.lower() != ".json" or p.stat().st_size > 5_000_000:
            continue
        try:
            d = json.loads(_read(p))
        except ValueError:
            continue
        acc: set = set()
        _regex_strings(d, acc)
        for s in acc:
            pat_sub[s].add(_sub_of(p, P))
    cross = {s: sorted(v) for s, v in pat_sub.items() if len(v) >= 2}
    red = sum(1 for r in dup_rows if r["lamp"] == "RED")
    lamp = "RED" if red else ("YELLOW" if (dup_rows or cross) else "GREEN")
    return {"k": "K5", "zh": "一致性", "lamp": lamp, "dup_rows": dup_rows, "regex_cross": len(cross),
            "regex_cross_samples": [{"pattern": (k[:60] + "…") if len(k) > 60 else k, "subs": v} for k, v in list(cross.items())[:10]]}


# ───────────────────────── K6 邊界 ─────────────────────────
def k6_boundary(P: dict) -> dict:
    rows = []
    files = _tails([P["vrn"], P["vdf"]], P["root"], {".py", ".ps1"}) + _tails([P["registry"]], P["root"], {".py"}, recursive=False) + _tails([P["root"]], P["root"], {".ps1"}, recursive=False)
    for p in files:
        s = _sub_of(p, P)
        if s == "VCGC" and not p.name.startswith(("CGC_", "Invoke-VIA-VCGC", "Invoke-VIA-")):
            continue
        if p.resolve() == ME:
            continue
        txt = _read(p)
        lines = txt.splitlines()
        stop = len(lines)
        for i, ln in enumerate(lines):                      # def selftest( 之後是沙盒夾具,不算邊界
            if re.match(r"\s*def selftest\(", ln):
                stop = i
                break
        wre = WRITE_PY if p.suffix.lower() == ".py" else WRITE_PS
        hit = None
        for pat in CROSS[s]:
            cre = re.compile(pat)
            for i, ln in enumerate(lines[:stop]):
                if cre.search(ln):
                    window = "\n".join(lines[max(0, i - 3): i + 4])
                    lamp = "RED" if wre.search(window) else "YELLOW"
                    if hit is None or (lamp == "RED" and hit["lamp"] != "RED"):
                        hit = {"sub": s, "file": _rel(p, P), "line": i + 1, "lamp": lamp,
                               "why": "別子系統路徑 + 附近有寫檔動詞(疑似越界寫)" if lamp == "RED" else "引用別子系統路徑(只讀,列出給人看)"}
                    if lamp == "RED":
                        break
        if hit:
            rows.append(hit)
    red = [r for r in rows if r["lamp"] == "RED"]
    return {"k": "K6", "zh": "邊界", "lamp": "RED" if red else ("YELLOW" if rows else "GREEN"), "rows": rows}


# ───────────────────────── K7 LIB 環境 ─────────────────────────
def _req_names(P: dict) -> set:
    names: set = set()
    seen: set = set()
    for g in REQ_GLOBS:
        for p in P["root"].glob(g):
            if not p.is_file() or p in seen or _skip(p, P["root"]):
                continue
            seen.add(p)
            for ln in _read(p).splitlines():
                ln = ln.strip()
                if not ln or ln.startswith(("#", "-")):
                    continue
                m = re.match(r"([A-Za-z0-9_.\-]+)", ln)
                if m:
                    names.add(m.group(1).lower().replace("-", "_"))
    return names


_IMPORT_ALIAS = {"cv2": "opencv_python", "PIL": "pillow", "sklearn": "scikit_learn", "yaml": "pyyaml", "bs4": "beautifulsoup4", "fitz": "pymupdf", "dateutil": "python_dateutil",
                 "dotenv": "python_dotenv", "attr": "attrs", "OpenSSL": "pyopenssl", "Crypto": "pycryptodome", "talib": "ta_lib", "lxml": "lxml", "win32com": "pywin32", "win32api": "pywin32", "pythoncom": "pywin32"}


def k7_libs(P: dict) -> dict:
    std = set(getattr(sys, "stdlib_module_names", ()))
    req = _req_names(P)
    per: dict = {s: defaultdict(set) for s in SUBS}
    for p in _tails([P["vrn"], P["vdf"], P["registry"]], P["root"], {".py"}):
        txt = _read(p)
        s = _sub_of(p, P)
        for m in re.finditer(r"^\s*(?:from\s+([A-Za-z_][\w]*)|import\s+([A-Za-z_][\w]*))", txt, re.M):
            mod = m.group(1) or m.group(2)
            if mod in std or LOCAL_PREFIX.match(mod) or mod in ("_sa_sys", "_sa_Path"):
                continue
            per[s][mod].add(p.name)
    rows = []
    for s in SUBS:
        for mod, files in sorted(per[s].items()):
            pkg = _IMPORT_ALIAS.get(mod, mod).lower()
            listed = pkg in req or mod.lower() in req
            importable = importlib.util.find_spec(mod) is not None
            if listed and importable:
                continue
            rows.append({"sub": s, "module": mod, "listed_in_requirements": listed, "importable_here": importable, "n_files": len(files), "lamp": "YELLOW"})
    return {"k": "K7", "zh": "LIB 環境", "lamp": "YELLOW" if rows else "GREEN", "interpreter": sys.executable, "requirements_names": len(req), "rows": rows}


# ───────────────────────── K8 VRN 短指令 PY 化 ─────────────────────────
def k8_vrn_cmds(P: dict) -> dict:
    regs = sorted(P["root"].glob("Register-VIA-Commands-v*.ps1"), key=lambda q: _vnum(q.name))
    defs: dict = {}
    accel_file: dict = {}
    frx = re.compile(r"^\s*function\s+(?:global:)?(via-[\w-]+)\s*\{", re.M)
    for r in regs:
        txt = _read(r)
        has_accel = bool(PS_ACCEL.search(txt))
        ms = list(frx.finditer(txt))
        for i, m in enumerate(ms):
            body = txt[m.end(): (ms[i + 1].start() if i + 1 < len(ms) else len(txt))]
            defs[m.group(1)] = (r.name, body)
            accel_file[m.group(1)] = has_accel
    rows = []
    for name, (fname, body) in sorted(defs.items()):
        if "vrn" not in name.lower() and "VRN_" not in body:
            continue
        if re.search(r"via-vcgc\s+run", body):
            mode, lamp = "VCGC 動詞橋", "GREEN"
        elif re.search(r"Invoke-VCPython|\bpython(?:3)?\b|\.py\b", body):
            mode, lamp = "直呼 python", "YELLOW"
        else:
            mode, lamp = "純 PS 邏輯", "YELLOW"
        if not accel_file.get(name):
            lamp = "RED"
        rows.append({"cmd": name, "defined_in": fname, "mode": mode, "file_accel": accel_file.get(name, False), "lamp": lamp})
    n = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    for r in rows:
        n[r["lamp"]] += 1
    lamp = "RED" if n["RED"] else ("YELLOW" if n["YELLOW"] else ("GREEN" if rows else "GRAY"))
    return {"k": "K8", "zh": "VRN 短指令 PY 化", "lamp": lamp, "registers": len(regs), "tail": (regs[-1].name if regs else None), "counts": n, "rows": rows}


# ───────────────────────── 彙整 ─────────────────────────
def audit(P: dict | None = None) -> dict:
    P = P or _paths()
    ks = [k1_accel(P), k2_vdf_net(P), k3_managers(P), k4_ssot_down(P), k5_consistency(P), k6_boundary(P), k7_libs(P), k8_vrn_cmds(P)]
    order = {"RED": 3, "YELLOW": 2, "GREEN": 1, "GRAY": 0}
    lamp = max((k["lamp"] for k in ks), key=lambda x: order[x])
    return {"verb": "audit", "engine": NAME, "ts": _now(), "root": str(P["root"]), "lamp": lamp, "checks": ks}


def paste_pack(res: dict, cap_red: int = 12, cap_yel: int = 8) -> list:
    L = ["[計] vcgc panorama · %s · 總燈 %s · %s" % (res["ts"], res["lamp"], " ".join("%s=%s" % (k["k"], k["lamp"]) for k in res["checks"]))]
    for k in res["checks"]:
        kk = k["k"]
        if kk == "K1":
            per = k["per"]
            L.append("[計] K1 加速器 · " + " · ".join("%s py 缺 %d/%d ps 缺 %d/%d" % (s, per[s]["py_missing"], per[s]["py_total"], per[s]["ps_missing"], per[s]["ps_total"]) for s in SUBS) + " · %s" % k["lamp"])
            for r in k["rows"][:cap_red]:
                L.append("  [RED] K1 %s %s" % (r["sub"], r["file"]))
            if len(k["rows"]) > cap_red:
                L.append("  [RED] K1 … 另 %d 支(全清單在卡)" % (len(k["rows"]) - cap_red))
        elif kk == "K2":
            L.append("[計] K2 VDF 網路工具 · 出網尾版 %d · 無橋 %d · 無閘 %d · %s" % (k["net_files"], sum(1 for r in k["rows"] if r["lamp"] == "RED"), sum(1 for r in k["rows"] if r["lamp"] == "YELLOW"), k["lamp"]))
            for r in [x for x in k["rows"] if x["lamp"] == "RED"][:cap_red]:
                L.append("  [RED] K2 %s" % r["file"])
            for r in [x for x in k["rows"] if x["lamp"] == "YELLOW"][:cap_yel]:
                L.append("  [YEL] K2 %s" % r["file"])
        elif kk == "K3":
            L.append("[計] K3 SystemManager 掌握力 · %s" % k["lamp"])
            for r in k["rows"]:
                L.append("  [%s] K3 %s %s · 鏈 %s · selftest %s · 讀自家 %s · RESULT %s 天 · %s" % ("RED" if r["lamp"] == "RED" else ("YEL" if r["lamp"] == "YELLOW" else "OK"), r["sub"], r.get("tail"), r.get("chain_len"), r.get("selftest"), r.get("reads_own"), r.get("result_age_days"), r.get("why") or "—"))
        elif kk == "K4":
            L.append("[計] K4 SSOT 下放 · %s" % k["lamp"])
            for r in k["rows"]:
                L.append("  [%s] K4 %s 中央 %d 冊 · %s" % ("RED" if r["lamp"] == "RED" else ("YEL" if r["lamp"] == "YELLOW" else "OK"), r["sub"], r.get("central_books", 0), r.get("why")))
                if r["sub"] == "OTHER" and r.get("families"):
                    L.append("      族:" + ", ".join(r["families"][:25]))
        elif kk == "K5":
            L.append("[計] K5 一致性 · 同族散落 紅 %d 黃 %d · regex 跨子系統 %d · %s" % (sum(1 for r in k["dup_rows"] if r["lamp"] == "RED"), sum(1 for r in k["dup_rows"] if r["lamp"] == "YELLOW"), k["regex_cross"], k["lamp"]))
            for r in [x for x in k["dup_rows"] if x["lamp"] == "RED"][:cap_red]:
                L.append("  [RED] K5 %s · %s" % (r["family"], " | ".join(r["where"][:3])))
            for r in [x for x in k["dup_rows"] if x["lamp"] == "YELLOW"][:cap_yel]:
                L.append("  [YEL] K5 %s · %s" % (r["family"], " | ".join(r["where"][:3])))
        elif kk == "K6":
            L.append("[計] K6 邊界 · 疑似越界寫 %d · 只讀引用 %d · %s" % (sum(1 for r in k["rows"] if r["lamp"] == "RED"), sum(1 for r in k["rows"] if r["lamp"] == "YELLOW"), k["lamp"]))
            for r in [x for x in k["rows"] if x["lamp"] == "RED"][:cap_red]:
                L.append("  [RED] K6 %s %s:%d" % (r["sub"], r["file"], r["line"]))
            for r in [x for x in k["rows"] if x["lamp"] == "YELLOW"][:cap_yel]:
                L.append("  [YEL] K6 %s %s:%d" % (r["sub"], r["file"], r["line"]))
        elif kk == "K7":
            L.append("[計] K7 LIB 環境 · requirements 名 %d · 未列/import 不到 %d · 直譯器 %s · %s" % (k["requirements_names"], len(k["rows"]), k["interpreter"], k["lamp"]))
            for r in k["rows"][:cap_yel + 6]:
                L.append("  [YEL] K7 %s %s · 列入 %s · 可 import %s · %d 檔" % (r["sub"], r["module"], r["listed_in_requirements"], r["importable_here"], r["n_files"]))
        elif kk == "K8":
            c = k["counts"]
            L.append("[計] K8 VRN 短指令 · 鏈 %d 檔(尾 %s)· 綠 %d 黃 %d 紅 %d · %s" % (k["registers"], k["tail"], c["GREEN"], c["YELLOW"], c["RED"], k["lamp"]))
            for r in [x for x in k["rows"] if x["lamp"] == "RED"][:cap_red]:
                L.append("  [RED] K8 %s · %s · %s · 檔無 PS-ACCEL" % (r["cmd"], r["mode"], r["defined_in"]))
            for r in [x for x in k["rows"] if x["lamp"] == "YELLOW"][:cap_yel + 8]:
                L.append("  [YEL] K8 %s · %s · %s" % (r["cmd"], r["mode"], r["defined_in"]))
    reds = sum(1 for k in res["checks"] if k["lamp"] == "RED")
    L.append("NEXT: " + ("把 [RED] 行貼給 AI,按 K 分批出薄尾(每批只動一個子系統,不改別人)" if reds else "零紅 → 黃表留卡逐批裁;VDF 下放 / 短指令 PY 化 排下一段"))
    return L[:300]


def write_outputs(res: dict, P: dict | None = None) -> dict:
    P = P or _paths()
    day = datetime.datetime.now().strftime("%Y%m%d")
    P["cards"].mkdir(parents=True, exist_ok=True)
    P["report"].mkdir(parents=True, exist_ok=True)
    pack = paste_pack(res)
    md = P["cards"] / ("VCGC_PanoramaCard_%s.md" % day)
    L = ["# VCGC 全景一致性資訊卡(%s)" % day, "", "> 唯讀。紅 = 要修(出薄尾);黃 = 列卡待裁;灰 = 尚未適用。只看尾版。", "", "## 貼回包", "```"] + pack + ["```", ""]
    for k in res["checks"]:
        L += ["## %s %s · %s" % (k["k"], k["zh"], k["lamp"]), ""]
        rows = k.get("rows") or k.get("dup_rows") or []
        for r in rows[:400]:
            L.append("- " + json.dumps(r, ensure_ascii=False))
        if k["k"] == "K5" and k.get("regex_cross_samples"):
            L.append("- regex 跨子系統樣本:" + json.dumps(k["regex_cross_samples"], ensure_ascii=False))
        L.append("")
    md.write_text("\n".join(L), encoding="utf-8")
    js = P["cards"] / ("VCGC_PanoramaCard_%s.json" % day)
    js.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    (P["report"] / "PANORAMA_latest.json").write_text(json.dumps({"ts": res["ts"], "lamp": res["lamp"], "checks": {k["k"]: k["lamp"] for k in res["checks"]}}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"md": str(md), "json": str(js), "pack": pack}


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VCGC] 拒絕。只能經 via-vcgc。")
        return 2
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a[:2]:
        return selftest()
    if a[:1] != ["audit"]:
        print("[拒跑] audit [--json] | --selftest")
        return 2
    res = audit()
    out = write_outputs(res)
    if "--json" in a:
        print(json.dumps(res, ensure_ascii=False))
    for ln in out["pack"]:
        print(ln)
    print("  [卡] %s" % out["md"])
    return 1 if res["lamp"] == "RED" else 0


def _w(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


_ACCEL_PY = "# ===== [VIA:ACCEL-BRIDGE:v0100] =====\ntry:\n    import VIA_SuperAccel_Module as VIA_ACCEL\nexcept ImportError:\n    VIA_ACCEL = None\n"
_PAD = "\n".join("# pad %d" % i for i in range(14)) + "\n"


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="cgcpano-"))
    os.environ["VIA_ROOT"] = str(td)
    P = _paths()
    chk("① 沙盒:VIA_ROOT 指 temp", all(str(v).startswith(str(td)) for v in P.values()))
    vrn, vdf, reg, root = P["vrn"], P["vdf"], P["registry"], P["root"]
    # K1 夾具:VRN 有橋 + 無橋;前版無橋(不算);PS 有/無
    _w(vrn / "VRN_ENG001_A_v0100.py", _PAD + "x=1\n")
    _w(vrn / "VRN_ENG001_A_v0101.py", _ACCEL_PY + _PAD + "x=2\n")
    _w(vrn / "VRN_ENG002_B_v0100.py", _PAD + "import requests\n")
    _w(root / "Invoke-VIA-Thing-v0100.ps1", _PAD + "Write-Host 1\n")
    _w(root / "Invoke-VIA-Thing-v0101.ps1", "# ===== [VIA:PS-ACCEL:v0101] =====\n" + _PAD + "Write-Host 2\n")
    _w(root / "Invoke-VIA-Bare-v0100.ps1", _PAD + "Write-Host 3\n")
    # K2:VDF 出網無橋 / 有橋無閘 / 有橋有閘
    _w(vdf / "VDF_ENG001_Fetch_v0100.py", _ACCEL_PY + _PAD + "import requests\nrequests.get('x')\n")
    _w(vdf / "VDF_ENG002_Fetch_v0100.py", _ACCEL_PY + "# [VIA:NET-BRIDGE]\n" + _PAD + "import requests\n")
    _w(vdf / "VDF_ENG003_Fetch_v0100.py", _ACCEL_PY + "# [VIA:NET-BRIDGE]\nif os.environ.get('VIA_NET_CONSENT')!='YES': pass\n" + _PAD + "import requests\n")
    _w(vdf / "VDF_ENG004_Local_v0100.py", _ACCEL_PY + _PAD + "y=1\n")
    # K3:VRN 管理器完整;VDF 管理器無 selftest 不讀自家
    _w(vrn / "VRN_SystemManager_v0122.py", _ACCEL_PY + _PAD + "if '--selftest' in a: pass\nstatus=1\nSSOT='SSOT'\n")
    _w(vdf / "VDF_SystemManager_v0130.py", _ACCEL_PY + _PAD + "run=1\n")
    _w(root / "VIA_Reports" / "vrn" / "RESULT_x_latest.json", {"a": 1})
    # K4:中央 VRN 冊 + VDF 冊;VRN 有 Index 全號;VDF 無
    _w(reg / "VIA_VRN_DocClass_SSOT_v0101.json", {"c": 1})
    _w(reg / "VDF_Universe_SSOT_v0100.json", {"u": {"pattern": r"(?<!\d)([1-9]\d{3})(?!\d)"}})
    _w(reg / "VDF_Rules_SSOT_v0100.json", {"r": 1})
    _w(reg / "GIF_Flow_SSOT_v0100.json", {"g": 1})
    _w(reg / "VIA_Policy_Laws_SSOT_v0106.json", {"laws": []})
    _w(vrn / "SSOT" / "VRN_DocClass_SSOT_v0101.json", {"c": 1})
    _w(vrn / "SSOT" / "VRN_Rx_SSOT_v0100.json", {"x": {"pattern": r"(?<!\d)([1-9]\d{3})(?!\d)"}})
    _w(vrn / "registry" / "VRN_SSOT_Index_v0100.json", {"entries": {"k1": {"ssot_no": "SSOT-VCGC-VRN-BOOK0001"}, "k2": {"ssot_no": "SSOT-VCGC-VRN-BOOK0002", "status": "RETIRED"}}})
    # K5:同族異頭(VRN knowledge vs registry)· 同頭漂移
    _w(vrn / "knowledge" / "VIA_VRN_DocClass_SSOT_v0099.json", {"c": 1, "d": 2})
    _w(vdf / "registry" / "VDF_Rules_SSOT_v0100.json", {"r": 2})
    # K6:VRN 檔寫 VDF 夾(紅)· VDF 檔只讀 VRN(黃)
    _w(vrn / "VRN_ENG003_Bad_v0100.py", _ACCEL_PY + _PAD + "p = ROOT / 'functional modules/VDF/x.json'\np.write_text('x')\n")
    _w(vdf / "VDF_ENG005_Read_v0100.py", _ACCEL_PY + _PAD + "q = ROOT / 'functional modules/VRN/SSOT'\nprint(q)\n")
    # K7:requirements 列 requests;VRN import 一個不存在的套件
    _w(root / "requirements.txt", "requests>=2\npandas\n")
    _w(vrn / "VRN_ENG004_Lib_v0100.py", _ACCEL_PY + _PAD + "import requests\nimport nosuchpkg_zz\n")
    # K8:Register 鏈兩檔:v0100 無 PS-ACCEL 定義 via-vrnold(純 PS);v0101 有 PS-ACCEL 定義 via-vrnrun(走 vcgc)+ via-vrnpy(直呼 python)+ 覆蓋 via-vrnold
    _w(root / "Register-VIA-Commands-v0100.ps1", "function global:via-vrnold {\n  Write-Host 1\n}\nfunction global:via-vrnlegacy {\n  Write-Host 2\n}\n")
    _w(root / "Register-VIA-Commands-v0101.ps1", "# [VIA:PS-ACCEL:v0101]\n. (Join-Path $PSScriptRoot 'Register-VIA-Commands-v0100.ps1')\nfunction global:via-vrnrun {\n  via-vcgc run --family vrn VRN_SystemManager intake\n}\nfunction global:via-vrnpy {\n  python 'VRN_X.py'\n}\nfunction global:via-vrnold {\n  Write-Host 3\n}\n")
    res = audit(P)
    K = {k["k"]: k for k in res["checks"]}
    k1 = K["K1"]
    chk("② K1 只算尾版:VRN_ENG001 尾版有橋不計,ENG002 缺=紅;PS Thing 尾版有橋,Bare 缺=紅", {r["file"].split(os.sep)[-1] for r in k1["rows"]} == {"VRN_ENG002_B_v0100.py", "Invoke-VIA-Bare-v0100.ps1"} and k1["lamp"] == "RED")
    k2 = K["K2"]
    chk("③ K2:出網 3 支 · 無橋 1 紅 · 有橋無閘 1 黃 · 不出網不計", k2["net_files"] == 3 and sum(1 for r in k2["rows"] if r["lamp"] == "RED") == 1 and sum(1 for r in k2["rows"] if r["lamp"] == "YELLOW") == 1)
    k3 = {r["sub"]: r for r in K["K3"]["rows"]}
    chk("④ K3:VRN 管理器綠(selftest·讀自家·RESULT 新)· VDF 紅(無 selftest 不讀自家)", k3["VRN"]["lamp"] == "GREEN" and k3["VDF"]["lamp"] == "RED")
    k4 = {r["sub"]: r for r in K["K4"]["rows"]}
    chk("⑤ K4:VRN Index 1 活鍵全號綠(退役不計)· VDF 中央 2 冊未下放紅 · OTHER 1 族黃", k4["VRN"]["lamp"] == "GREEN" and k4["VRN"]["index_keys"] == 1 and k4["VDF"]["lamp"] == "RED" and k4["VDF"]["central_books"] == 2 and k4["OTHER"]["lamp"] == "YELLOW")
    k5 = K["K5"]
    chk("⑥ K5:DocClass 同族異頭紅 · Rules 同頭漂移黃 · regex 跨子系統 1", {(r["family"], r["lamp"]) for r in k5["dup_rows"]} == {("VIA_VRN_DocClass_SSOT.json", "RED"), ("VDF_Rules_SSOT.json", "YELLOW")} and k5["regex_cross"] == 1)
    k6 = K["K6"]
    chk("⑦ K6:VRN 寫 VDF 夾=紅 1 · VDF 讀 VRN=黃 1", sum(1 for r in k6["rows"] if r["lamp"] == "RED" and r["sub"] == "VRN") == 1 and sum(1 for r in k6["rows"] if r["lamp"] == "YELLOW" and r["sub"] == "VDF") == 1)
    k7 = K["K7"]
    chk("⑧ K7:nosuchpkg_zz 未列且 import 不到=黃;requests 有列不計", any(r["module"] == "nosuchpkg_zz" for r in k7["rows"]) and not any(r["module"] == "requests" and r["listed_in_requirements"] for r in k7["rows"]))
    k8 = {r["cmd"]: r for r in K["K8"]["rows"]}
    chk("⑨ K8:後版覆蓋(via-vrnold 定義於 v0101)· vcgc 綠 · python 黃 · 純 PS 黃 · legacy 檔無 PS-ACCEL 紅",
        k8["via-vrnold"]["defined_in"] == "Register-VIA-Commands-v0101.ps1" and k8["via-vrnrun"]["lamp"] == "GREEN" and k8["via-vrnpy"]["mode"] == "直呼 python"
        and k8["via-vrnold"]["mode"] == "純 PS 邏輯" and k8["via-vrnold"]["lamp"] == "YELLOW" and k8["via-vrnlegacy"]["lamp"] == "RED")
    before = sorted(str(x) for x in root.rglob("*") if x.is_file() and "docs" not in x.parts and "VIA_Reports" not in x.parts)
    out = write_outputs(res, P)
    after = sorted(str(x) for x in root.rglob("*") if x.is_file() and "docs" not in x.parts and "VIA_Reports" not in x.parts)
    pack = out["pack"]
    chk("⑩ 唯讀:audit+出卡後 docs/VIA_Reports 以外零新檔 · 卡 md/json 在 · 貼回包 ≤300 行且結尾 NEXT:", before == after and Path(out["md"]).exists() and Path(out["json"]).exists() and len(pack) <= 300 and pack[-1].startswith("NEXT:"))
    chk("⑪ 貼回包首行總燈 RED 且八 K 都有燈", pack[0].startswith("[計] vcgc panorama") and "總燈 RED" in pack[0] and all(("K%d=" % i) in pack[0] for i in range(1, 9)))
    body = ME.read_text(encoding="utf-8")
    chk("⑫ 帶加速器橋 · VIA_FROM_VCGC 閘", "[VIA:ACCEL-BRIDGE:v0100]" in body and "VIA_FROM_VCGC" in body)
    os.environ.pop("VIA_ROOT", None)
    shutil.rmtree(td, ignore_errors=True)
    print("[計] %s 自測 %d/%d · %s" % (NAME, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
