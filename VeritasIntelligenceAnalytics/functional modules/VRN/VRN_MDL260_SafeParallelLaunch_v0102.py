#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_MDL260_SafeParallelLaunch v0102 — 一個指令:就緒檢查 → 輸入分群 → 擷取 + 文件整輪同時跑 → 矩陣 → 結果併進總燈。

操作員 2026-11-16:「one ps code to handle all · check vcgc all token-saving tools & supporting tools for vrn · 單一引擎最強化 ·
自動實測」「輸入項目分群分類方便集體設定參數 · 參數本身整合為一個 JSON」。
容器實測(24 份真 PDF)查到 v0101 的三個缺口,本版補上(v0101 一字不動;本版薄尾,只換它的四個名字):
  ① 就緒檢查(新):起跑前先說清楚「缺哪個工具、哪一步會因此失敗」——支援工具(pdfplumber · pymupdf · camelot · tabula + Java ·
     OCR · python-docx · Pillow · duckdb · pyarrow · yfinance)用 find_spec 查,不匯入、不安裝;省 Token 工具只讀 VCGC 鎖冊自報。
     實測:容器沒有 pymupdf,文件整輪的「一標題四重點」19 份全紅(ModuleNotFoundError)——這種要在起跑前就點名。
  ② 兩條擷取路一起跑(互補):VRN-2 文件整輪(基本資料 · 年度數據 · 四重點 · 驗證)+ 管理器 extract(逐表算術驗證)。
     `--source <夾>` 一個參數餵兩邊(路徑有空白也行;v0101 的 --roundall-args 會被空白切開)。
  ③ 結果併燈:管理器 extract 回 0 但有 REVIEW / NODATA、ENG049 矩陣回 0 但整張是 YELLOW / NODATA 時,v0101 都記成綠。
     本版讀本輪寫進帳的列與矩陣日誌,有待看的就是黃並逐檔點名;要求的檔沒有結果也點名(缺一不綠)。
  ④ 參數一本 JSON:VRN_ParamControl_SSOT 尾版(v0101 起有 run_params · input_groups · file_overrides)。
     輸入照檔名分群(個股 / 產業 / 晨會日報 / 其他),一組一套參數;先後:指令列 > 單檔例外 > 組 > run_params > 內建。
  ⑤ 與上次比:每輪結果只增寫 VRN_Launch_history.jsonl,起跑前印上一輪、跑完印差異。
不做的:不安裝套件、不設同意閘、不改 .ps1、不出網;輸入檔只讀(分群用硬連結 / 複製到 TEMP)。
rc:0 全綠 · 2 有黃 · 1 有紅。
用法:py VRN_MDL260_SafeParallelLaunch_v0102.py run --source <樣本夾> [--params <冊.json>] [--dry] [--no-open] [v0101 的旗標照用]
      py VRN_MDL260_SafeParallelLaunch_v0102.py preflight [--source <夾>]     (只做降壓 + 就緒檢查,不起流程)
      py VRN_MDL260_SafeParallelLaunch_v0102.py params [--source <夾>] [--csv]  (印生效參數與分群表)
      py VRN_MDL260_SafeParallelLaunch_v0102.py --selftest
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
VIA_NET_TOOL_PATH = None   # VRN 只強制加速器(操作員令);本啟動器不出網

import csv
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SYSTEM = "VRN"
STEM = "VRN_MDL260_SafeParallelLaunch"
VERSION = "v0102"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / f"{STEM}_v0101.py"
PARAM_STEM = "VRN_ParamControl_SSOT"
EXTS = (".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".txt", ".md")
OK_STATUS = ("READ", "TEXT_DOC")
RC = {"GREEN": 0, "YELLOW": 2, "RED": 1}


def _load(path: Path, name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


B = _load(PRIOR_PATH, "vrn_launch_prior_for_" + VERSION)        # 前版 v0101:降壓 · 監工 · 橋閘 · 頁面
VIA = B.VIA
_ORIG = {}
_CTX = {"a": None, "ledger_n0": 0}


def __getattr__(name):
    """尾版律 TAILAPI:前版公開名稱經本檔轉接。"""
    return getattr(B, name)


# ───────── ④ 參數冊(一本 JSON)─────────
BUILTIN = {"slots": "auto", "slots_min": 3, "slots_max": 5, "cpu_soft": 70, "cpu_hard": 90, "mem_floor_gb": 2, "calm_wait_s": 180,
           "timeout_s": 21600, "extract_workers": "auto", "extract_timeout_s": 7200, "run_roundall": True, "run_extract": True}
GROUP_KEYS = ("enabled", "extract_workers", "extract_timeout_s")
FLAG_OF = {"slots": "--slots", "cpu_soft": "--cpu-soft", "cpu_hard": "--cpu-hard", "mem_floor_gb": "--mem-floor-gb",
           "calm_wait_s": "--calm-wait", "timeout_s": "--timeout"}
BUILTIN_GROUPS = [{"key": "EQUITY", "name": "個股報告", "match": {"ticker": True}, "params": {}},
                  {"key": "OTHER", "name": "其他", "match": {"else": True}, "params": {}}]


def _opt(argv: list, name: str, default=None):
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default


def params_path(arg=None):
    if arg:
        return Path(arg)
    return B.tail(HERE, PARAM_STEM + "_v*.json")


def _type_ok(key: str, v) -> bool:
    if key in ("run_roundall", "run_extract", "enabled"):
        return isinstance(v, bool)
    if key in ("slots", "extract_workers"):
        return v == "auto" or (isinstance(v, int) and not isinstance(v, bool) and 1 <= v <= 8)
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0


def load_params(path) -> tuple:
    """→ (生效冊 dict, 問題清單)。錯鍵 / 錯型別點名後不採用(退回上一層),不默默吃掉。"""
    probs = []
    book = {"path": str(path) if path else None, "run": dict(BUILTIN), "groups": [dict(g) for g in BUILTIN_GROUPS], "overrides": {}, "version": None}
    if not path:
        probs.append("找不到 %s_v*.json → 全部用程式內建預設" % PARAM_STEM)
        return book, probs
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        probs.append("參數冊讀不進來(%s:%s)→ 全部用程式內建預設" % (type(exc).__name__, str(exc)[:80]))
        return book, probs
    book["version"] = raw.get("version")
    for k, v in (raw.get("run_params") or {}).items():
        if k not in BUILTIN:
            probs.append("run_params.%s 不是認得的參數 → 不採用" % k)
        elif not _type_ok(k, v):
            probs.append("run_params.%s = %r 型別 / 範圍不對 → 用內建 %r" % (k, v, BUILTIN[k]))
        else:
            book["run"][k] = v
    groups = []
    for i, g in enumerate(raw.get("input_groups") or []):
        key, match = str(g.get("key") or "").strip(), g.get("match") or {}
        if not key or not isinstance(match, dict) or not (match.get("ticker") or match.get("keywords") or match.get("else")):
            probs.append("input_groups[%d] 少 key 或 match(ticker / keywords / else 擇一)→ 這一組不採用" % i)
            continue
        ps = {}
        for k, v in (g.get("params") or {}).items():
            if k not in GROUP_KEYS:
                probs.append("input_groups[%s].params.%s 不是認得的參數 → 不採用" % (key, k))
            elif not _type_ok(k, v):
                probs.append("input_groups[%s].params.%s = %r 型別 / 範圍不對 → 用 run_params" % (key, k, v))
            else:
                ps[k] = v
        groups.append({"key": key, "name": str(g.get("name") or key), "id": g.get("id"), "match": match, "params": ps})
    if groups:
        if not any(g["match"].get("else") for g in groups):
            groups.append({"key": "OTHER", "name": "其他", "match": {"else": True}, "params": {}})
            probs.append("input_groups 沒有 else 組 → 補一組 OTHER 接住認不出的檔")
        book["groups"] = groups
    ov = raw.get("file_overrides") or {}
    if isinstance(ov, dict):
        keys = {g["key"] for g in book["groups"]}
        for name, o in ov.items():
            if not isinstance(o, dict) or ("group" in o and o["group"] not in keys) or ("enabled" in o and not isinstance(o["enabled"], bool)):
                probs.append("file_overrides[%s] 寫法不對(group 要是既有的組 · enabled 要是 true / false)→ 不採用" % name)
            else:
                book["overrides"][name] = o
    return book, probs


def group_params(book: dict, g: dict) -> dict:
    out = {"enabled": True, "extract_workers": book["run"]["extract_workers"], "extract_timeout_s": book["run"]["extract_timeout_s"]}
    out.update(g.get("params") or {})
    return out


# ───────── 輸入分群 ─────────
_COPY_STAMP = re.compile(r"\s*[((]20\d{6}-\d{6}[))]")
_DATE_RX = re.compile(r"(?<!\d)(?:20\d{6}|1\d{6}|\d{6})(?!\d)")
_CODE_RX = re.compile(r"(?<![\dA-Za-z])\d{4}(?!\d)")
_YEARISH = re.compile(r"20[2-4]\d")


def classify(name: str, book: dict) -> str:
    """檔名 → 組 key。單檔例外優先;再由上往下第一個符合的組。"""
    ov = book["overrides"].get(name) or {}
    if ov.get("group"):
        return ov["group"]
    stem = Path(name).stem
    core = _DATE_RX.sub(" ", _COPY_STAMP.sub("", stem))
    codes = _CODE_RX.findall(core)
    real = [c for c in codes if not _YEARISH.fullmatch(c)]
    low = stem.lower()
    kw_hit = [g["key"] for g in book["groups"] if any(str(w).lower() in low for w in (g["match"].get("keywords") or []))]
    for g in book["groups"]:
        m = g["match"]
        if m.get("ticker") and (real or (codes and not kw_hit)):
            return g["key"]
        if m.get("keywords") and g["key"] in kw_hit:
            return g["key"]
        if m.get("else"):
            return g["key"]
    return book["groups"][-1]["key"]


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def scan_source(src, book: dict) -> dict:
    """只讀清點來源夾(不遞迴):分群 · 略過 · 同內容重複 · 不認得的副檔名。"""
    out = {"source": str(src) if src else None, "exists": bool(src and Path(src).is_dir()), "groups": {}, "skipped": [], "dups": [], "other_ext": [], "total": 0}
    for g in book["groups"]:
        out["groups"][g["key"]] = {"name": g["name"], "id": g.get("id"), "files": [], "params": group_params(book, g)}
    if not out["exists"]:
        return out
    seen = {}
    for p in sorted(Path(src).iterdir(), key=lambda q: q.name):
        if not p.is_file():
            continue
        if p.suffix.lower() not in EXTS:
            out["other_ext"].append(p.name)
            continue
        out["total"] += 1
        key = classify(p.name, book)
        grp = out["groups"][key]
        if (book["overrides"].get(p.name) or {}).get("enabled") is False or not grp["params"]["enabled"]:
            out["skipped"].append({"file": p.name, "group": key, "why": "單檔例外 enabled=false" if (book["overrides"].get(p.name) or {}).get("enabled") is False else "整組 enabled=false"})
            continue
        grp["files"].append(p.name)
        d = _sha(p)
        if d in seen:
            out["dups"].append({"file": p.name, "same_as": seen[d]})
        else:
            seen[d] = p.name
    return out


def stage(scan: dict, root: Path, do: bool = True) -> dict:
    """要分組跑或有略過時,把要跑的檔硬連結(不行就複製)到 TEMP;原夾不動。→ {組 key 或 '_all': 夾}。"""
    live = {k: g for k, g in scan["groups"].items() if g["files"]}
    if not scan["exists"] or not live:
        return {}
    src = Path(scan["source"])
    whole = not scan["skipped"] and not scan["other_ext"]
    out = {}
    if whole:
        out["_all"] = src                                          # 沒有略過、沒有雜檔:整輪直接用原夾
    if len(live) == 1 and whole:
        out[next(iter(live))] = src
        return out
    plan = dict(live)
    if not whole:
        plan["_all"] = {"files": [f for g in live.values() for f in g["files"]]}
    for key, g in plan.items():
        d = Path(root) / "vrn_input" / key
        out[key] = d
        if not do:
            continue
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        for f in g["files"]:
            try:
                os.link(src / f, d / f)
            except OSError:
                shutil.copy2(src / f, d / f)
    return out


# ───────── ① 就緒檢查 ─────────
SUPPORT = [  # (模組, 必要, 缺了會怎樣)
    ("pdfplumber", True, "文字 PDF 讀不了:extract 與文件整輪都沒有主讀取器"),
    ("duckdb", True, "增量庫 / 矩陣寫不了"),
    ("fitz", False, "pymupdf:文件整輪的「一標題四重點」摘要與原文核對會全數失敗(容器實測 19/19 紅)"),
    ("pyarrow", False, "Parquet 輸出寫不了(只剩 JSON / CSV)"),
    ("pandas", False, "矩陣 / 增量庫整理變慢或跳過"),
    ("camelot", False, "extract 第二讀取器:pdfplumber 找不到表的報告(例 Daiwa · 3014TT)會留在 REVIEW"),
    ("tabula", False, "extract 第三讀取器(另需 Java):同上"),
    ("docx", False, "python-docx:Word 輸入讀不了"),
    ("PIL", False, "Pillow:圖片輸入 / OCR 前處理做不了"),
    ("yfinance", False, "共識 / ADJ CLOSE 補不了(另需操作員自己開同意閘)"),
]
OCR_MODS = ("rapidocr_onnxruntime", "paddleocr", "pytesseract", "easyocr")


def _has(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except (ImportError, ValueError):
        return False


def token_tools() -> dict:
    """VCGC 省 Token 工具:只讀它的鎖冊自報(不執行、不改)。"""
    reg = VIA / "supportive modules" / "registry"
    lock = B.tail(reg, "VIA_ToolVersion_Lock_v*.json")
    out = {"lock": lock.name if lock else None, "fams": {}}
    if not lock:
        return out
    try:
        book = json.loads(lock.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return out
    for fam, v in book.items():
        if isinstance(v, dict) and v.get("path"):
            out["fams"][fam] = {"file": Path(str(v["path"])).name, "present": (VIA.parent / str(v["path"])).is_file()}
    return out


def last_run() -> dict | None:
    hist = B.out_dir() / "VRN_Launch_history.jsonl"
    try:
        lines = [ln for ln in hist.read_text(encoding="utf-8").splitlines() if ln.strip()]
        return json.loads(lines[-1]) if lines else None
    except (OSError, ValueError):
        return None


def preflight_rows(a: dict) -> list:
    rows = []

    def add(item, lamp, detail):
        rows.append({"item": item, "lamp": lamp, "detail": detail})
    book, probs, scan = a["book"], a["book_problems"], a["scan"]
    add("參數冊(一本 JSON)", "YELLOW" if probs else "GREEN",
        "%s%s" % (Path(book["path"]).name if book["path"] else "內建預設", (" · 問題 %d:" % len(probs) + ";".join(probs[:4])) if probs else " · 先後 指令列 > 單檔例外 > 組 > run_params > 內建"))
    if a.get("source"):
        if not scan["exists"]:
            add("來源夾", "RED", "%s 不存在或不是資料夾" % a["source"])
        elif not scan["total"]:
            add("來源夾", "RED", "%s 裡沒有認得的檔(%s)" % (a["source"], " ".join(EXTS)))
        else:
            add("來源夾(只讀)", "GREEN", "%s · 認得 %d 檔 · 不認得副檔名 %d(不送)" % (a["source"], scan["total"], len(scan["other_ext"])))
            for key, g in scan["groups"].items():
                skipped = [s["file"] for s in scan["skipped"] if s["group"] == key]
                if not g["files"] and not skipped:
                    continue
                p = g["params"]
                add("分群 %s" % key, "YELLOW" if skipped else "INFO",
                    "%s · 跑 %d 份 · 略過 %d 份 · extract 行程 %s · 上限 %ss" % (g["name"], len(g["files"]), len(skipped), p["extract_workers"], p["extract_timeout_s"])
                    + ((" · 略過:" + "、".join(skipped[:5])) if skipped else ""))
            if scan["dups"]:
                add("同內容重複", "INFO", "%d 份(會各跑一次、各算一列):" % len(scan["dups"]) + "、".join("%s = %s" % (d["file"], d["same_as"]) for d in scan["dups"][:5]))
    else:
        add("來源夾", "YELLOW", "沒給 --source → 管理器 extract 不跑;文件整輪用它自己記得的來源")
    miss_need = [m for m, need, _ in SUPPORT if need and not _has(m)]
    for m, need, why in SUPPORT:
        ok = _has(m)
        if not ok:
            add("支援工具 %s" % m, "RED" if need else "YELLOW", "沒裝 → %s;經 VCGC InstallGate 安裝(本啟動器不裝)" % why)
    have = [m for m, _, _ in SUPPORT if _has(m)]
    add("支援工具(在位)", "RED" if miss_need else "GREEN", "%d/%d:%s" % (len(have), len(SUPPORT), " · ".join(have)))
    java = shutil.which("java")
    if _has("tabula") and not java:
        add("Java", "YELLOW", "tabula 在、Java 不在 → 第三讀取器跑不了")
    ocr = [m for m in OCR_MODS if _has(m)]
    add("OCR(掃描件)", "GREEN" if ocr else "YELLOW",
        ("本環境有 " + " · ".join(ocr)) if ocr else "本環境沒有 OCR 套件 → 無文字的掃描 PDF 會是 NODATA;VRN-2 另有隔離 OCR 環境,以它在整輪裡自報的為準")
    tk = token_tools()
    fams = tk["fams"]
    absent = [f for f, v in fams.items() if not v["present"]]
    add("省 Token 工具(VCGC 鎖冊自報 · 只讀)", "GREEN" if fams and not absent else "YELLOW",
        ("%s · %d 家族在位:" % (tk["lock"], len(fams) - len(absent)) + " · ".join("%s=%s" % (f, v["file"]) for f, v in list(fams.items())[:8])
         + ((" · 檔不在:" + "、".join(absent)) if absent else "")) if fams else "讀不到 VCGC 鎖冊(VRN 照跑;AI 讀檔省 Token 卡請用 via-vcgc token 看)")
    prev = last_run()
    if prev:
        add("上一輪(接近成功紀錄)", "INFO", "%s · %s · %s" % (prev.get("at"), prev.get("lamp"), prev.get("summary") or ""))
    return rows


# ───────── 換上前版的四個名字 ─────────
def parse(argv: list) -> dict:
    book, probs = load_params(params_path(_opt(argv, "--params")))
    inject = []
    for k, flag in FLAG_OF.items():
        if flag not in argv and book["run"][k] != BUILTIN[k]:
            inject += [flag, str(book["run"][k])]
    a = _ORIG["parse"](list(argv) + inject)
    B.MIN_SLOTS, B.MAX_SLOTS = int(book["run"]["slots_min"]), int(book["run"]["slots_max"])
    if "--skip-roundall" not in argv and not book["run"]["run_roundall"]:
        a["skip_roundall"] = True
    a["skip_extract"] = "--skip-extract" in argv or not book["run"]["run_extract"]
    a["source"] = _opt(argv, "--source")
    a["book"], a["book_problems"] = book, probs
    a["scan"] = scan_source(a["source"], book)
    _CTX["a"] = a
    _CTX["ledger_n0"] = _ledger_len()
    return a


def env_check(t=None, run_manager=None, bridges=True, data_home=None) -> dict:
    env = _ORIG["env_check"](t, run_manager, bridges, data_home)
    if _CTX["a"] is not None:
        env["rows"] += preflight_rows(_CTX["a"])
        lamps = [r["lamp"] for r in env["rows"]]
        env["lamp"] = "RED" if "RED" in lamps else "YELLOW" if "YELLOW" in lamps else "GREEN"
    return env


def build_jobs(t: dict, a: dict, py: str = sys.executable) -> list:
    jobs = _ORIG["build_jobs"](t, a, py)
    scan = a.get("scan") or {"exists": False, "groups": {}}
    staged = stage(scan, B.temp_root(), do=not a.get("dry")) if scan.get("exists") else {}
    a["staged"] = {k: str(v) for k, v in staged.items()}
    for j in jobs:
        if j["id"] == "roundall" and staged.get("_all") and "--source" not in j["cmd"]:
            j["cmd"] = list(j["cmd"]) + ["--source", str(staged["_all"])]      # 清單元素:路徑有空白也不會被切開
    if a.get("skip_extract") or not t.get("manager"):
        return jobs
    prev, added = None, []
    for key, g in scan["groups"].items():
        if not g["files"] or key not in staged:
            continue
        p = g["params"]
        jid = "extract_" + key.lower()
        cmd = [py, "-B", str(t["manager"]), "extract", "--dir", str(staged[key])]
        if p["extract_workers"] != "auto":
            cmd += ["--workers", str(p["extract_workers"])]
        added.append({"id": jid, "title": "①b 管理器 extract · %s %d 份(逐表算術驗證)" % (g["name"], len(g["files"])), "cmd": cmd,
                      "needs": ["gate"], "after": [prev] if prev else [], "soft": (2,), "timeout": int(p["extract_timeout_s"])})
        prev = jid
    if not added:
        return jobs
    at = next((i for i, j in enumerate(jobs) if j["id"] == "matrix"), len(jobs))
    for j in jobs:
        if j["id"] == "matrix":
            j["after"] = list(j.get("after") or []) + [prev]
    return jobs[:at] + added + jobs[at:]


# ───────── ③ 結果併燈 ─────────
def _ledger() -> Path:
    return VIA / "VIA_Reports" / "vrn" / "extract" / "VRN_Extract_Ledger.jsonl"


def _ledger_len() -> int:
    try:
        with _ledger().open("r", encoding="utf-8") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def extract_summary(n0: int, wanted: list, ledger: Path | None = None) -> dict:
    """本輪寫進帳的列(第 n0 列之後)→ 計數 · 待看清單 · 沒有結果的檔。"""
    rows = {}
    try:
        with (ledger or _ledger()).open("r", encoding="utf-8") as fh:
            for i, ln in enumerate(fh):
                if i >= n0 and ln.strip():
                    try:
                        r = json.loads(ln)
                    except ValueError:
                        continue
                    rows[str(r.get("file"))] = r
    except OSError:
        pass
    counts = {}
    for r in rows.values():
        counts[r.get("status")] = counts.get(r.get("status"), 0) + 1
    todo = [{"file": f, "status": r.get("status"), "why": r.get("why")} for f, r in rows.items() if r.get("status") not in OK_STATUS]
    return {"files": len(rows), "counts": counts, "todo": todo, "missing": [f for f in wanted if f not in rows]}


_MATRIX_RX = re.compile(r"\[(個股統一矩陣|非個股矩陣)\]\s*(\d+)\s*份\s*·\s*燈\s*(\{.*?\})")


def matrix_summary(log_text: str) -> dict:
    out = {}
    for name, n, lamps in _MATRIX_RX.findall(log_text or ""):
        try:
            out[name] = {"n": int(n), "lamps": json.loads(lamps)}
        except ValueError:
            out[name] = {"n": int(n), "lamps": {}}
    return out


def fold_results(rep: dict, out: Path) -> None:
    """跑完才做:extract 帳與矩陣日誌併進總燈(回傳碼 0 不等於結果都對)。"""
    a = _CTX["a"]
    run = rep.get("run")
    if not run or a is None:
        return
    rows, ids = [], {j["id"]: j for j in run["jobs"]}
    ex_jobs = [j for jid, j in ids.items() if jid.startswith("extract_")]
    summary = []
    if ex_jobs:
        wanted = [f for g in a["scan"]["groups"].values() for f in g["files"]]
        es = extract_summary(_CTX["ledger_n0"], wanted)
        rep["extract"] = es
        bad = bool(es["todo"] or es["missing"])
        rows.append({"item": "結果 · 管理器 extract", "lamp": "YELLOW" if bad else "GREEN",
                     "detail": "本輪 %d 檔 · " % es["files"] + " ".join("%s %d" % kv for kv in sorted(es["counts"].items(), key=lambda kv: str(kv[0])))
                     + ((" · 沒有結果 %d:" % len(es["missing"]) + "、".join(es["missing"][:6])) if es["missing"] else "")})
        for t in es["todo"][:40]:
            rows.append({"item": "  待看 %s" % t["status"], "lamp": "YELLOW", "detail": "%s · %s" % (t["file"], t["why"])})
        summary.append("extract " + "/".join("%s %d" % kv for kv in sorted(es["counts"].items(), key=lambda kv: str(kv[0]))))
    if "matrix" in ids and ids["matrix"].get("log"):
        try:
            ms = matrix_summary(Path(ids["matrix"]["log"]).read_text(encoding="utf-8", errors="replace"))
        except OSError:
            ms = {}
        rep["matrix"] = ms
        for name, m in ms.items():
            not_green = {k: v for k, v in m["lamps"].items() if k != "GREEN" and v}
            rows.append({"item": "結果 · ENG049 %s" % name, "lamp": "YELLOW" if not_green or not m["n"] else "GREEN",
                         "detail": "%d 份 · " % m["n"] + " ".join("%s %d" % kv for kv in m["lamps"].items())})
            summary.append("%s %s" % (name, " ".join("%s %d" % kv for kv in m["lamps"].items())))
    if "roundall" in ids:
        summary.append("整輪 %s" % ids["roundall"].get("lamp"))
    rep["env"]["rows"] += rows
    if rep.get("lamp") == "GREEN" and any(r["lamp"] == "YELLOW" for r in rows):
        rep["lamp"] = "YELLOW"
    prev, n_before = last_run(), len(rep["env"]["rows"])
    now_line = {"at": rep.get("at"), "lamp": rep.get("lamp"), "engine": TAG, "jobs": {j["id"]: j.get("lamp") for j in run["jobs"]},
                "extract": (rep.get("extract") or {}).get("counts"), "summary": " · ".join(summary)}
    if prev:
        diff = [k for k in sorted(set(now_line["jobs"]) | set(prev.get("jobs") or {})) if now_line["jobs"].get(k) != (prev.get("jobs") or {}).get(k)]
        rep["env"]["rows"].append({"item": "與上一輪比", "lamp": "INFO",
                                   "detail": "上一輪 %s %s → 本輪 %s" % (prev.get("at"), prev.get("lamp"), rep.get("lamp"))
                                   + ((" · 變了:" + " · ".join("%s %s→%s" % (k, (prev.get("jobs") or {}).get(k), now_line["jobs"].get(k)) for k in diff)) if diff else " · 各流程燈號沒變")
                                   + " · extract %s → %s" % (prev.get("extract"), now_line["extract"])})
    out.mkdir(parents=True, exist_ok=True)
    with (out / "VRN_Launch_history.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(now_line, ensure_ascii=False) + "\n")
    for r in rows + rep["env"]["rows"][n_before:]:
        print(f"  {r['lamp']:<7}{r['item']:<22}{r['detail']}", flush=True)


def _save(rep: dict, out: Path, a: dict) -> None:
    fold_results(rep, out)
    rep["params"] = {"book": a["book"]["path"], "version": a["book"]["version"], "run": a["book"]["run"], "problems": a["book_problems"],
                     "groups": {k: {"name": g["name"], "n": len(g["files"]), "params": g["params"]} for k, g in a["scan"]["groups"].items()},
                     "skipped": a["scan"]["skipped"], "dups": a["scan"]["dups"], "staged": a.get("staged")}
    for k in ("book", "scan", "book_problems"):
        rep.get("args", {}).pop(k, None)
    _ORIG["_save"](rep, out, a)


def install() -> None:
    if _ORIG:
        return
    _ORIG.update(parse=B.parse, env_check=B.env_check, build_jobs=B.build_jobs, _save=B._save, TAG=B.TAG, VERSION=B.VERSION,
                 slots=(B.MIN_SLOTS, B.MAX_SLOTS))
    B.parse, B.env_check, B.build_jobs, B._save, B.TAG, B.VERSION = parse, env_check, build_jobs, _save, TAG, VERSION


def uninstall() -> None:
    if not _ORIG:
        return
    B.parse, B.env_check, B.build_jobs, B._save, B.TAG, B.VERSION = (_ORIG[k] for k in ("parse", "env_check", "build_jobs", "_save", "TAG", "VERSION"))
    B.MIN_SLOTS, B.MAX_SLOTS = _ORIG["slots"]
    _ORIG.clear()
    _CTX["a"] = None


# ───────── 動詞 ─────────
def cmd_run(argv: list, check_only=False) -> int:
    install()
    try:
        return B.cmd_run(argv, check_only=check_only)
    finally:
        uninstall()


def cmd_params(argv: list) -> int:
    path = params_path(_opt(argv, "--params"))
    book, probs = load_params(path)
    print(f"=== {TAG} 參數(一本 JSON:{Path(book['path']).name if book['path'] else '內建預設'})===")
    print("  先後:指令列旗標 > file_overrides > input_groups[組].params > run_params > 程式內建")
    for k, v in book["run"].items():
        print(f"  run_params.{k:<20}{v!s:<8}{'(內建)' if v == BUILTIN[k] else '(冊)'}")
    scan = scan_source(_opt(argv, "--source"), book)
    rows = []
    for g in book["groups"]:
        gp, sg = group_params(book, g), scan["groups"][g["key"]]
        rule = "有 4 位數代號" if g["match"].get("ticker") else ("關鍵字 " + "/".join(map(str, g["match"]["keywords"]))) if g["match"].get("keywords") else "其餘"
        rows.append({"group": g["key"], "name": g["name"], "rule": rule, "enabled": gp["enabled"], "extract_workers": gp["extract_workers"],
                     "extract_timeout_s": gp["extract_timeout_s"], "files": len(sg["files"]), "file_names": " | ".join(sg["files"])})
        print(f"  組 {g['key']:<9}{g['name']:<18}{rule[:44]:<46}啟用 {gp['enabled']!s:<6}行程 {gp['extract_workers']!s:<5}上限 {gp['extract_timeout_s']}s"
              + (f" · {len(sg['files'])} 份" if scan["exists"] else ""))
    for s in scan["skipped"]:
        print(f"  略過 {s['file']} · {s['why']}")
    for p in probs:
        print(f"  [問題] {p}")
    if "--csv" in argv:
        out = B.out_dir()
        out.mkdir(parents=True, exist_ok=True)
        dst = out / "VRN_Params_latest.csv"
        with dst.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"[表] {dst}(只是檢視用;正本是 JSON)")
    return 2 if probs else 0


def selftest() -> int:
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)
    print(f"[計] {TAG} 自測開始(本版 + 前版 {PRIOR_PATH.name} 另起行程)", flush=True)
    real, rp = load_params(params_path())
    ck("P1 倉裡的參數冊尾版讀得進來 · 沒有問題 · 有 run_params 與 else 組", real["path"] and not rp and any(g["match"].get("else") for g in real["groups"])
       and len(real["groups"]) >= 3, rp)
    names = {"MS-2308 20251128.pdf": "EQUITY", "3014TT-20231005.pdf": "EQUITY", "瑞基(4171,NR_未評等)-CTBC251208(20261006-122004).pdf": "EQUITY",
             "20260916兆豐台灣產業專題-航太產業.pdf": "INDUSTRY", "20251208_台新台股盤勢分析.pdf": "DAILY", "20251205兆豐晨會報告(二)-公司訪談摘要.pdf": "DAILY",
             "第一場 2026年投資大趨勢 - 華南投顧 -11412.pdf": "INDUSTRY", "【中信｜債券ETF周報】油價攀升_CTBC260915.pdf": "DAILY", "凱基美股分析20251205-Meta.pdf": "OTHER",
             "2027 大成鋼 20251001.pdf": "EQUITY"}
    got = {n: classify(n, real) for n in names}
    ck("P2 分群:代號 → 個股(日期 · 下載時間戳 · 年份不當代號;2027 這種年份樣的代號沒有別的關鍵字時仍是個股)· 關鍵字 → 產業 / 晨會日報 · 其餘 → 其他",
       got == names, {k: v for k, v in got.items() if v != names[k]})
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        bad = td / "bad.json"
        bad.write_text(json.dumps({"version": "vX", "run_params": {"slots": 99, "cpu_soft": 60, "nope": 1, "run_extract": "yes"},
                                   "input_groups": [{"key": "A", "match": {"keywords": ["甲"]}, "params": {"enabled": False, "x": 1}}, {"name": "沒 key"}],
                                   "file_overrides": {"a.pdf": {"group": "ZZ"}, "b.pdf": {"enabled": False}}}, ensure_ascii=False), encoding="utf-8")
        bk, pr = load_params(bad)
        ck("P3 錯鍵 / 錯型別逐項點名、不採用;對的照用;沒有 else 組自動補",
           bk["run"]["slots"] == "auto" and bk["run"]["cpu_soft"] == 60 and bk["run"]["run_extract"] is True and "nope" not in bk["run"]
           and [g["key"] for g in bk["groups"]] == ["A", "OTHER"] and bk["groups"][0]["params"] == {"enabled": False}
           and list(bk["overrides"]) == ["b.pdf"] and len(pr) == 7, pr)
        bk2, pr2 = load_params(td / "none.json")
        ck("P4 冊讀不到 → 內建預設 + 點名(不當掉)", bk2["run"] == BUILTIN and len(pr2) == 1 and load_params(None)[1])
        src = td / "in"
        src.mkdir()
        for n, body in (("MS-2308 20251128.pdf", b"a"), ("MS-2308 copy(20261006-122004).pdf", b"a"), ("20251208_盤勢分析.pdf", b"b"), ("甲報告.pdf", b"c"),
                        ("b.pdf", b"d"), ("note.xyz", b"e")):
            (src / n).write_bytes(body)
        sc = scan_source(src, real)
        ck("S1 清點:分群 · 同內容重複點名 · 不認得的副檔名不送", sc["total"] == 5 and len(sc["groups"]["EQUITY"]["files"]) == 2
           and sc["dups"] == [{"file": "MS-2308 copy(20261006-122004).pdf", "same_as": "MS-2308 20251128.pdf"}] and sc["other_ext"] == ["note.xyz"], sc)
        st = stage(sc, td / "tmp")
        ck("S2 分組暫存:每組一夾(硬連結 / 複製)· 有雜檔時整輪用乾淨的 _all 夾 · 原夾不動",
           sorted(p.name for p in st["EQUITY"].iterdir()) == sorted(sc["groups"]["EQUITY"]["files"]) and st["_all"] != src
           and len(list(st["_all"].iterdir())) == 5 and len(list(src.iterdir())) == 6, {k: str(v) for k, v in st.items()})
        sc3 = scan_source(src, bk)                                    # 冊 bk:A 組 enabled=false · b.pdf 單檔略過
        ck("S3 整組 enabled=false 與單檔例外都列進略過、不送", sorted(s["file"] for s in sc3["skipped"]) == ["b.pdf", "甲報告.pdf"]
           and sc3["groups"]["A"]["files"] == [] and len(sc3["groups"]["OTHER"]["files"]) == 3, sc3["skipped"])
        one = td / "one"
        one.mkdir()
        (one / "MS-2308 20251128.pdf").write_bytes(b"a")
        st1 = stage(scan_source(one, real), td / "tmp1")
        ck("S4 只有一組、沒有略過 → 直接用原夾(不複製)", st1 == {"_all": one, "EQUITY": one} and not (td / "tmp1").exists(), st1)
        install()
        try:
            a = parse(["--source", str(src), "--params", str(bad), "--dry"])
            a2 = parse(["--source", str(src), "--params", str(bad), "--cpu-soft", "55"])
            t = {"manager": HERE / "VRN_SystemManager_v9999.py", "eng049": HERE / "x.py", "roundall": td / "R.py"}
            a_ok = parse(["--source", str(src), "--dry"])
            jobs = build_jobs(t, a_ok, "py")
            jid = [j["id"] for j in jobs]
            ra = next(j for j in jobs if j["id"] == "roundall")
            mx = next(j for j in jobs if j["id"] == "matrix")
            ex = [j for j in jobs if j["id"].startswith("extract_")]
            ck("J1 參數先後:冊的 cpu_soft 60 生效 · 指令列 --cpu-soft 55 蓋過冊", a["limits"]["cpu_soft"] == 60.0 and a2["limits"]["cpu_soft"] == 55.0, (a["limits"], a2["limits"]))
            ck("J2 工作圖:每個有檔的組一支 extract(彼此依序、都等橋閘)· 整輪帶 --source(清單元素)· 矩陣排在最後一支 extract 之後 · --dry 不建暫存夾",
               len(ex) == 3 and all(j["needs"] == ["gate"] for j in ex) and ex[1]["after"] == [ex[0]["id"]] and ex[0]["after"] == []
               and ra["cmd"][-2] == "--source" and ex[-1]["id"] in mx["after"] and "roundall" in mx["after"] and jid.index("matrix") > jid.index(ex[-1]["id"])
               and not (B.temp_root() / "vrn_input" / "__selftest__").exists(), (jid, ra["cmd"][-2:], mx.get("after")))
            a_no = parse(["--skip-extract", "--skip-roundall"])
            ck("J3 --skip-extract / --skip-roundall / 沒給 --source:不加 extract、不帶 --source",
               not any(j["id"].startswith("extract_") or j["id"] == "roundall" for j in build_jobs(t, a_no, "py")))
            _CTX["a"] = a_ok
            rows = preflight_rows(a_ok)
            items = " ".join(r["item"] for r in rows)
            ck("R1 就緒檢查列:參數冊 · 來源夾 · 分群 · 同內容重複 · 支援工具 · OCR · 省 Token 工具;缺的非必要工具是黃、不是綠",
               all(k in items for k in ("參數冊", "來源夾", "分群 EQUITY", "同內容重複", "支援工具(在位)", "OCR", "省 Token 工具"))
               and all(r["lamp"] in ("YELLOW", "RED") for r in rows if r["item"].startswith("支援工具 ")), items)
            a_bad = parse(["--source", str(td / "不存在")])
            ck("R2 來源夾不存在 → 紅(不起流程)", any(r["item"] == "來源夾" and r["lamp"] == "RED" for r in preflight_rows(a_bad)))
        finally:
            uninstall()
        led = td / "ledger.jsonl"
        led.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in (
            {"file": "old.pdf", "status": "REVIEW", "why": "舊"}, {"file": "a.pdf", "status": "READ", "why": "ok"},
            {"file": "b.pdf", "status": "REVIEW", "why": "FIN 1 表全有算術問題"}, {"file": "c.pdf", "status": "NODATA", "why": "掃描件"},
            {"file": "d.pdf", "status": "TEXT_DOC", "why": "ok"})) + "\n", encoding="utf-8")
        es = extract_summary(1, ["a.pdf", "b.pdf", "c.pdf", "d.pdf", "e.pdf"], led)
        ck("F1 extract 併燈:只算本輪的列 · READ / TEXT_DOC 才算過 · 待看逐檔點名 · 沒有結果的檔點名",
           es["files"] == 4 and es["counts"] == {"READ": 1, "REVIEW": 1, "NODATA": 1, "TEXT_DOC": 1}
           and [t["file"] for t in es["todo"]] == ["b.pdf", "c.pdf"] and es["missing"] == ["e.pdf"], es)
    ms = matrix_summary('x\n  [matrix] [個股統一矩陣] 42 份 · 燈 {"YELLOW": 15, "NODATA": 27}\n  [matrix] [非個股矩陣] 22 份 · 燈 {"NODATA": 22}\n')
    ck("F2 矩陣日誌:份數與燈號計數讀得出來(回傳碼 0 但整張黃 / NODATA 不算綠)",
       ms == {"個股統一矩陣": {"n": 42, "lamps": {"YELLOW": 15, "NODATA": 27}}, "非個股矩陣": {"n": 22, "lamps": {"NODATA": 22}}}, ms)
    ck("F3 還原:跑完前版四個名字與道數上下限都是原件", not _ORIG and B.parse.__module__ == B.__name__ and B.TAG.endswith("v0101") and (B.MIN_SLOTS, B.MAX_SLOTS) == (3, 5))
    text = Path(__file__).read_text(encoding="utf-8")
    ck("F4 檔面:加速器橋標記 · 不匯入 TA-Lib · 不寫同意閘 · 不 pip · 沒有本機使用者路徑",
       "[VIA:ACCEL-BRIDGE:v0100]" in text and "import " + "talib" not in text and "_CONSENT\"] " + "=" not in text
       and "pip " + "install" not in text and "C:\\" + "Users" not in text and "/home" + "/" not in text)
    pr = subprocess.run([sys.executable, "-B", str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    ck("F5 前版 %s 自測照過(另起行程)" % PRIOR_PATH.name, pr.returncode == 0, (pr.stdout or "")[-300:])
    n = sum(ok)
    print(f"[計] {STEM} {VERSION} 自測 {n}/{len(ok)} {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if args[0] in ("--selftest", "selftest"):
        return selftest()
    if args[0] == "bridge-gate":
        return B.cmd_bridge_gate()
    if args[0] in ("check", "preflight"):
        return cmd_run(args[1:] + ["--no-open"], check_only=True)
    if args[0] == "params":
        return cmd_params(args[1:])
    if args[0] == "run":
        return cmd_run(args[1:])
    print(f"[{TAG}] 未知動詞 {args[0]}(run · preflight · params · bridge-gate · --selftest)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
