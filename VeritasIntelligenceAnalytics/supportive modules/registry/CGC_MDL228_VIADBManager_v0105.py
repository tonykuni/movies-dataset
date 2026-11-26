#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL228_VIADBManager v0105 — 薄尾(v0104 以前一字不動):系統庫 syscat(VIA 自己的檔 · 引擎版本 · 冊 · 號,建成一個 DuckDB)

操作員 2026-11-26:附件「以 DuckDB 作為核心資料庫,搭配本機 UI 介面來管理系統文件、引擎版本與檔案資產 · 系統庫呢」+「token-saving +」。
VIA 版取捨(只增不減 · 已有同功能就掛動詞):
  · 庫:VCGC 資料庫管理器底下加一個動詞 syscat,建「系統庫」VIA_Reports/vcgc/syscat/VIA_SystemCatalog.duckdb。
    它是衍生檔:由 git 追蹤的程式與冊 + 既有各冊算出來,隨時可重建,不是正本(正本仍是各冊;不另立新冊)。
  · 表:files(路徑 · 系統 · 家族 · 版號 · 行數 · LF 雜湊)· families(版數 · 首尾版 · 尾版號 · 首行說明)· numbers(全部編號冊)·
    tools(鎖版工具 × VIA-TOOL 號)· requirements · workflows(各系統工作流冊尾版)· stations · verbs(功能盤點冊)·
    ledger(串測紀錄冊)· locks(成功鎖定帳)· changes(跟上一次 build 比:新增 · 改了 · 不見)· meta(建庫時間 · HEAD · 三數 · 來源冊雜湊)。
    附件的 sys.audit_logs / 版本差異 = changes + ledger;sys.system_config = meta;engine_versions = families + tools。
  · 省 Token:AI 要回答「某家族現在第幾版、幾號」「某號是誰」「某需求到哪了」不必整本讀幾百 KB 的冊,
    下 syscat q @fam / @code / @req / @wkf / @file / @tool / @lamp / @changed 或一句 SELECT,只回一張小卡(預設 40 列,帶 token 帳)。
  · 只讀:q 只准 SELECT · WITH · DESCRIBE · SUMMARIZE · SHOW · PRAGMA table_info;擋寫入、讀檔(read_* · FROM '檔' · glob)、出網;
    連線是唯讀且關掉外部存取(DuckDB enable_external_access=false),關鍵字檢查被繞過也讀不到檔。
  · 資料邊界:只收程式結構、冊的中繼資料與號;不收 VIA_Reports、資料湖、研報、.parquet / .duckdb / .csv / .pdf。
  · 不採 Streamlit / DuckDB 內建 UI:要起伺服器(CM-90 · L118 靜態頁);要看頁面用既有卡片矩陣引擎。
  · syscat page:後端讀庫(唯讀)→ 前端一個靜態 HTML(VIA_SystemCatalog.html,不起伺服器、資料內嵌、
    左欄 關鍵字 · 系統 · 分頁,右側表格可點欄排序;色與字只取 VIA_UI_Template_SSOT 尾版 token,燈四色白字、紅燈慢閃)。
  · 參數(掃描範圍 · 輸出夾 · 卡片大小 · 八個預設查詢)在參數冊 VIA_VCGC_SysCat_Params 尾版(SDD v0101 L4:參數從參數冊讀);
    冊不在就用程式內建預設照跑,燈降黃並點名。
  · 沒有 duckdb 的機器:用 Python 內建 sqlite 代替(同表同欄),燈降黃並印安裝指令;不自己裝套件。
用法(其餘動詞照 v0104):
  syscat build [--sqlite] · syscat q "SELECT …" | syscat q @<預設> [字] [--limit N] [--json] · syscat stats · syscat diff  [--out <夾>]
rc:綠 0 · 黃 2(sqlite 代替 / 過期 / 用法錯)· 紅 1。零網路 · 不碰 TA-Lib · 不讀寫同意閘 · 只寫 VIA_Reports/vcgc/syscat。
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

import datetime as _dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ENGINE = "CGC_MDL228_VIADBManager_v0105"
VERSION = "v0105"
HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL228_VIADBManager"
PRIOR_NAME = "CGC_MDL228_VIADBManager_v0104.py"
_spec = importlib.util.spec_from_file_location("cgc_mdl228_prior_for_" + Path(__file__).stem, HERE / PRIOR_NAME)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE

VIA = HERE.parents[1]
OUT_DEFAULT = VIA / "VIA_Reports" / "vcgc" / "syscat"
DB_NAME = "VIA_SystemCatalog"
EXTS = (".py", ".ps1", ".psm1", ".json", ".jsonl", ".md", ".yaml", ".yml", ".toml", ".sh", ".txt")
SKIP_DIRS = ("VIA_Reports/", "__pycache__/", ".git/")
VERS = re.compile(r"^(?P<fam>.+?)_v(?P<ver>\d{4})(?:\.[A-Za-z0-9]+)+$")
SYS_PREFIX = (("CGC_", "VCGC"), ("VDF_", "VDF"), ("VRN2_", "VRN"), ("VRN_", "VRN"), ("VQG_", "VQG"), ("VAP_", "VAP"), ("SUP_", "SUP"), ("VIA_", "VIA"))
MAX_LIMIT = 500
CELL = 80

TABLES = {   # 表 → 欄(全部只放程式結構、冊的中繼資料與號;不放市場資料、研報、庫內容)
    "meta": [("key", "VARCHAR"), ("value", "VARCHAR")],
    "files": [("path", "VARCHAR"), ("folder", "VARCHAR"), ("name", "VARCHAR"), ("ext", "VARCHAR"), ("system", "VARCHAR"),
              ("family", "VARCHAR"), ("version", "VARCHAR"), ("bytes", "BIGINT"), ("lines", "BIGINT"), ("sha256_lf", "VARCHAR"), ("mtime_ns", "BIGINT")],
    "families": [("family", "VARCHAR"), ("system", "VARCHAR"), ("folder", "VARCHAR"), ("ext", "VARCHAR"), ("versions", "INTEGER"),
                 ("first_version", "VARCHAR"), ("tail_version", "VARCHAR"), ("tail_path", "VARCHAR"), ("tail_code", "VARCHAR"), ("tail_doc", "VARCHAR")],
    "numbers": [("book", "VARCHAR"), ("code", "VARCHAR"), ("name", "VARCHAR"), ("system", "VARCHAR"), ("raw", "VARCHAR")],
    "tools": [("family", "VARCHAR"), ("version", "VARCHAR"), ("path", "VARCHAR"), ("sha256", "VARCHAR"), ("activated_at", "VARCHAR"), ("code", "VARCHAR")],
    "requirements": [("book", "VARCHAR"), ("code", "VARCHAR"), ("subsystem", "VARCHAR"), ("status", "VARCHAR"), ("topic", "VARCHAR"), ("next", "VARCHAR")],
    "workflows": [("book", "VARCHAR"), ("code", "VARCHAR"), ("name", "VARCHAR"), ("kind", "VARCHAR"), ("version", "VARCHAR"), ("steps", "INTEGER")],
    "stations": [("id", "VARCHAR"), ("name", "VARCHAR"), ("argv", "VARCHAR"), ("version", "VARCHAR")],
    "verbs": [("verb", "VARCHAR"), ("state", "VARCHAR")],
    "ledger": [("kind", "VARCHAR"), ("id", "VARCHAR"), ("event", "VARCHAR"), ("lamp", "VARCHAR"), ("file", "VARCHAR"), ("ts", "VARCHAR")],
    "locks": [("path", "VARCHAR"), ("version", "VARCHAR"), ("vcgc_code", "VARCHAR"), ("sha256_lf", "VARCHAR"), ("locked_at", "VARCHAR"), ("what", "VARCHAR")],
    "changes": [("path", "VARCHAR"), ("change", "VARCHAR"), ("prev_sha", "VARCHAR"), ("sha", "VARCHAR")],
}

PRESETS = {   # @名 參數 → (SQL, 說明, 這題原本要讀的來源)
    "fam": ("SELECT family, system, folder, versions, first_version, tail_version, tail_code, tail_doc FROM families WHERE lower(family) LIKE lower(?) ORDER BY family, folder",
            "家族:版數 · 首尾版 · 尾版號 · 首行說明", ("files",)),
    "code": ("SELECT book, code, name, system FROM numbers WHERE code = ? OR lower(name) LIKE lower(?) ORDER BY book, code",
             "號 ↔ 名(全部編號冊)", ("numbers",)),
    "req": ("SELECT code, subsystem, status, topic, next FROM requirements WHERE code = ? OR lower(topic) LIKE lower(?) ORDER BY code",
            "需求冊尾版", ("requirements",)),
    "wkf": ("SELECT book, code, name, kind, version, steps FROM workflows WHERE code = ? OR lower(name) LIKE lower(?) ORDER BY book, code",
            "各系統工作流冊尾版", ("workflows",)),
    "file": ("SELECT path, system, version, bytes, lines FROM files WHERE lower(path) LIKE lower(?) ORDER BY path",
             "檔案(只含程式與冊)", ("files",)),
    "tool": ("SELECT family, version, code, activated_at, path FROM tools ORDER BY family", "鎖版工具", ("tools",)),
    "lamp": ("SELECT kind, id, event, lamp, file, ts FROM ledger WHERE lower(id) LIKE lower(?) ORDER BY ts DESC", "串測紀錄冊(最新在前)", ("ledger",)),
    "changed": ("SELECT change, path, prev_sha, sha FROM changes ORDER BY change, path", "跟上一次 build 比:新增 · 改了 · 不見", ("changes",)),
}

PARAM_STEM = "VIA_VCGC_SysCat_Params"


def load_params(reg: Path = HERE) -> tuple:
    """參數冊尾版 → (params, presets, 說明)。冊不在或壞了:回 (None, None, 原因),呼叫端用程式內建預設並降黃。"""
    hits = sorted(reg.glob(PARAM_STEM + "_v[0-9][0-9][0-9][0-9].json"))
    if not hits:
        return None, None, "參數冊 %s 不在,用程式內建預設" % PARAM_STEM
    try:
        d = json.loads(hits[-1].read_text(encoding="utf-8"))
        prm, pre = d["params"], {k: (v["sql"], v["what"], tuple(v.get("sources") or ())) for k, v in d["presets"].items()}
        for k in ("extensions", "skip_prefixes", "out_dir", "db_name", "default_limit", "max_limit", "cell_chars"):
            prm[k]
        return prm, pre, hits[-1].name
    except (OSError, ValueError, KeyError, TypeError) as e:
        return None, None, "參數冊 %s 讀不懂(%s),用程式內建預設" % (hits[-1].name, type(e).__name__)


def apply_params(reg: Path = HERE) -> str:
    """把參數冊的值套到模組常數;回參數來源說明。"""
    global EXTS, SKIP_DIRS, OUT_DEFAULT, DB_NAME, DEFAULT_LIMIT, MAX_LIMIT, CELL, PRESETS, PARAM_NOTE, PARAM_OK
    prm, pre, note = load_params(reg)
    PARAM_OK = prm is not None
    if PARAM_OK:
        EXTS, SKIP_DIRS = tuple(x.lower() for x in prm["extensions"]), tuple(prm["skip_prefixes"])
        OUT_DEFAULT, DB_NAME = VIA / prm["out_dir"], prm["db_name"]
        DEFAULT_LIMIT, MAX_LIMIT, CELL = int(prm["default_limit"]), int(prm["max_limit"]), int(prm["cell_chars"])
        PRESETS = pre
    PARAM_NOTE = note
    return note


DEFAULT_LIMIT = 40
PARAM_NOTE, PARAM_OK = "", False

FORBID = re.compile(r"\b(attach|detach|copy|export|import|install|load|create|insert|update|delete|drop|alter|set|reset|call|checkpoint|vacuum|"
                    r"begin|commit|rollback|truncate|replace|merge|grant|revoke|use)\b|\bread_\w+\s*\(|\bglob\s*\(|\bquery(?:_table)?\s*\(|"
                    r"\bsniff_csv\s*\(|\bparquet_\w+\s*\(|://|\b(?:from|join)\s+['\"]", re.I)
ALLOW_HEAD = re.compile(r"^\s*(select|with|describe|summarize|show|pragma\s+table_info)\b", re.I)


def tok(text: str) -> int:
    """與 CGC_MDL158 同一把估算:ASCII ≈ 4 字元 / token · CJK ≈ 1 字元 / token。"""
    a = sum(1 for c in text if ord(c) < 128)
    return a // 4 + (len(text) - a)


def sha_lf(b: bytes) -> str:
    return hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()


def system_of(name: str, rel: str) -> str:
    for p, s in SYS_PREFIX:
        if name.startswith(p):
            return s
    low = rel.lower()
    for key, s in (("vrn", "VRN"), ("vdf", "VDF"), ("vqg", "VQG"), ("vap", "VAP")):
        if "/" + key in low or low.startswith(key):
            return s
    return "VIA"


def _tail(reg: Path, stem: str):
    hits = sorted((p for p in reg.glob(stem + "_v[0-9][0-9][0-9][0-9]*.json")), key=lambda p: p.name)
    return hits[-1] if hits else None


def _load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def list_files(via: Path):
    """應掃:git 追蹤中、副檔名是程式或冊的檔(不含 VIA_Reports 與資料);沒有 git 就走 registry 與 docs。回 (清單, 來源說明)。"""
    import subprocess          # 匯入層不開子行程:只在這裡用
    try:
        cp = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", "-z"], cwd=str(via), capture_output=True, timeout=120)
        if cp.returncode == 0:
            rels = [r for r in cp.stdout.decode("utf-8", "replace").split("\0") if r]
            return [r for r in rels if r.lower().endswith(EXTS) and not r.startswith(SKIP_DIRS) and "/__pycache__/" not in r], "git ls-files"
    except (OSError, subprocess.SubprocessError):
        pass
    rels = []
    for root in (via / "supportive modules", via / "docs"):
        for p in root.rglob("*"):
            r = p.relative_to(via).as_posix()
            if p.is_file() and r.lower().endswith(EXTS) and "/__pycache__/" not in r:
                rels.append(r)
    return sorted(rels), "走訪 supportive modules · docs(沒有 git)"


def _hash_one(args):
    via, rel, prev = args
    st = (via / rel).stat()
    old = prev.get(rel)
    if old and old[0] == st.st_size and old[1] == st.st_mtime_ns:      # 大小與修改時間都沒變:沿用上一版庫的雜湊
        return rel, st.st_size, old[2], old[3], st.st_mtime_ns
    b = (via / rel).read_bytes()
    return rel, len(b), b.count(b"\n") + (1 if b and not b.endswith(b"\n") else 0), sha_lf(b), st.st_mtime_ns


def pmap(fn, items):
    """經加速器並行;加速器缺席就照順序(同結果)。"""
    if BASE_ACCEL is not None and hasattr(BASE_ACCEL, "accel_map") and len(items) > 64:
        try:
            out = BASE_ACCEL.accel_map(fn, items)
            if len(out) == len(items):
                return [(ok, r) for ok, r in out]
        except Exception as e:      # 加速器出錯就退回順序跑,照實記
            print("[syscat] 加速器並行失敗,改順序跑:%s" % type(e).__name__, flush=True)
    res = []
    for it in items:
        try:
            res.append((True, fn(it)))
        except OSError as e:
            res.append((False, "%s: %s" % (it[1], type(e).__name__)))
    return res


BASE_ACCEL = globals().get("VIA_ACCEL")


def collect(via: Path, prev_stat=None) -> tuple:
    """把冊與檔整理成各表的列。回 (rows, three, sources)。只讀。prev_stat = 上一版庫的 {路徑: (大小, 修改時間, 行數, 雜湊)}。"""
    reg = via / "supportive modules" / "registry"
    rels, how = list_files(via)
    prev_stat = prev_stat or {}
    got = pmap(_hash_one, [(via, r, prev_stat) for r in rels])
    rows = {k: [] for k in TABLES}
    skipped = []
    for (ok, r), rel in zip(got, rels):
        if not ok:
            skipped.append(r if isinstance(r, str) else rel)
            continue
        rel2, size, lines, sha, mt = r
        name = rel2.rsplit("/", 1)[-1]
        m = VERS.match(name)
        rows["files"].append([rel2, rel2.rsplit("/", 1)[0] if "/" in rel2 else "", name, ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else "",
                              system_of(name, rel2), m.group("fam") if m else "", ("v" + m.group("ver")) if m else "", size, lines, sha, mt])
    # 編號冊
    num_by_name = {}
    for nb in sorted((reg / "VIA_NumberBooks").glob("VIA_NumberBook_*.jsonl")):
        book = nb.stem
        for line in nb.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            code, name = str(d.get("code") or ""), str(d.get("name") or d.get("file") or "")
            rows["numbers"].append([book, code, name, str(d.get("system") or ""), json.dumps(d, ensure_ascii=False)[:2000]])
            if name and code:
                num_by_name[name] = code
    # 家族(由檔算)
    fam = {}
    for f in rows["files"]:
        if f[5]:
            fam.setdefault((f[5], f[1], f[3]), []).append(f)
    for (family, folder, ext), fs in sorted(fam.items()):
        fs.sort(key=lambda r: r[6])
        tail = fs[-1]
        doc = ""
        if ext == ".py":
            try:
                head = (via / tail[0]).read_text(encoding="utf-8", errors="replace")[:1500]
                mm = re.search(r'(?:"""|r""")(.*?)(?:\n|""")', head, re.S)
                doc = re.sub(r"^\S+\s+v\d{4}\s*[—\-:]\s*", "", (mm.group(1) if mm else "").strip())[:160]
            except OSError:
                doc = ""
        rows["families"].append([family, tail[4], folder, ext, len(fs), fs[0][6], tail[6], tail[0],
                                 num_by_name.get(tail[2].rsplit(".", 1)[0], ""), doc])
    sources = {}

    def src(p):
        if p and Path(p).exists():
            sources[Path(p).name] = sha_lf(Path(p).read_bytes())
        return p
    lock = _load(src(reg / "VIA_ToolVersion_Lock_v0100.json")) or {}
    evr = _load(src(reg / "VIA_EngineVersion_Register_v0100.json")) or {}
    seat = {r.get("family"): r.get("code") for r in evr.get("rows", []) if isinstance(r, dict) and r.get("role") == "engine"}
    for k, v in lock.items():
        if isinstance(v, dict) and "path" in v:
            rows["tools"].append([k, str(v.get("version", "")), v["path"], str(v.get("sha256", "")), str(v.get("activated_at", "")), str(seat.get(k, ""))])
    req = _load(src(_tail(reg, "VIA_Requirements_SSOT"))) or {}
    for r in req.get("requirements", []):
        rows["requirements"].append([Path(str(_tail(reg, "VIA_Requirements_SSOT"))).name, r.get("code"), r.get("subsystem"), r.get("status"),
                                     str(r.get("topic") or "")[:300], str(r.get("next") or "")[:300]])
    stems = sorted({re.sub(r"_v\d{4}\.json$", "", p.name) for p in reg.glob("VIA_Workflow_*_SSOT_v[0-9][0-9][0-9][0-9].json")})
    for st in stems:
        w = _load(src(_tail(reg, st))) or {}
        for x in w.get("workflows", []) if isinstance(w, dict) else []:
            if isinstance(x, dict):
                rows["workflows"].append([_tail(reg, st).name, x.get("code"), x.get("name"), x.get("kind"), x.get("version"), len(x.get("steps") or [])])
    inv = _load(src(_tail(reg, "VIA_VCGC_FunctionInventory_SSOT"))) or {}
    for s in inv.get("stations", []):
        rows["stations"].append([s.get("id"), s.get("name"), json.dumps(s.get("argv"), ensure_ascii=False), s.get("version")])
    for v, st in ((inv.get("coverage") or {}).get("verb") or {}).items():
        rows["verbs"].append([v, json.dumps(st, ensure_ascii=False)])
    for line in (src(reg / "VIA_VCGC_FunctionLedger_v0100.jsonl") or Path("/nonexistent")).read_text(encoding="utf-8").splitlines() if (reg / "VIA_VCGC_FunctionLedger_v0100.jsonl").exists() else []:
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if isinstance(d, dict):
            rows["ledger"].append([d.get("kind"), d.get("id"), d.get("event"), d.get("lamp"), d.get("file"), d.get("ts")])
    lk = via / "docs" / "handoff" / "daily" / "VIA_SuccessLock_Ledger_v0100.jsonl"
    if lk.exists():
        src(lk)
        for line in lk.read_text(encoding="utf-8").splitlines():
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if isinstance(d, dict):
                rows["locks"].append([d.get("path"), d.get("version"), d.get("vcgc_code"), d.get("sha256_lf"), d.get("locked_at"), str(d.get("what") or "")[:200]])
    three = {"should": len(rels), "done": len(rows["files"]), "skipped": skipped, "how": how}
    return rows, three, sources


def _backend(force: str = ""):
    if force != "sqlite":
        try:
            import duckdb
            return "duckdb", duckdb
        except ImportError:
            pass
    import sqlite3
    return "sqlite", sqlite3


def _connect(path: Path, kind: str, mod, read_only: bool):
    if kind == "duckdb":
        cfg = {"enable_external_access": False} if read_only else {}
        return mod.connect(str(path), read_only=read_only, config=cfg)
    if read_only:
        return mod.connect("file:%s?mode=ro" % path.as_posix(), uri=True)
    return mod.connect(str(path))


def db_path(out: Path):
    for ext in (".duckdb", ".sqlite"):
        p = out / (DB_NAME + ext)
        if p.exists():
            return p
    return None


def _write(path: Path, kind: str, mod, rows: dict, meta: dict) -> None:
    con = _connect(path, kind, mod, False)
    try:
        for t, cols in TABLES.items():
            con.execute("CREATE TABLE %s (%s)" % (t, ", ".join("%s %s" % (c, ty if kind == "duckdb" else ("INTEGER" if ty in ("BIGINT", "INTEGER") else "TEXT")) for c, ty in cols)))
            data = rows.get(t) or ([[k, v] for k, v in meta.items()] if t == "meta" else [])
            if not data:
                continue
            if kind == "duckdb":
                tmp = path.with_name("%s.%s.%d.ndjson" % (path.stem, t, os.getpid()))
                with tmp.open("w", encoding="utf-8") as fh:
                    for r in data:
                        fh.write(json.dumps(dict(zip([c for c, _ in cols], r)), ensure_ascii=False) + "\n")
                con.execute("INSERT INTO %s SELECT * FROM read_json(?, format='newline_delimited', columns={%s})"
                            % (t, ", ".join("'%s': '%s'" % (c, ty) for c, ty in cols)), [str(tmp)])
                tmp.unlink()
            else:
                con.executemany("INSERT INTO %s VALUES (%s)" % (t, ",".join("?" * len(cols))), data)
        if kind == "sqlite":
            con.commit()
    finally:
        con.close()


def _head(via: Path) -> str:
    import subprocess
    try:
        cp = subprocess.run(["git", "rev-parse", "--short=9", "HEAD"], cwd=str(via), capture_output=True, text=True, timeout=30)
        return cp.stdout.strip() if cp.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def build(via: Path = VIA, out: Path = OUT_DEFAULT, force: str = "") -> int:
    t0 = _dt.datetime.now(_dt.timezone.utc)
    kind, mod = _backend(force)
    out.mkdir(parents=True, exist_ok=True)
    old = db_path(out)
    prev, prev_stat = {}, {}
    if old is not None:
        okind, omod = _backend("" if old.suffix == ".duckdb" else "sqlite")
        if okind == ("duckdb" if old.suffix == ".duckdb" else "sqlite"):
            try:
                c = _connect(old, okind, omod, True)
                cols = [r[1] for r in c.execute("PRAGMA table_info('files')").fetchall()]
                q = "SELECT path, sha256_lf, bytes, %s, lines FROM files" % ("mtime_ns" if "mtime_ns" in cols else "NULL")
                for path, sha, size, mt, ln in c.execute(q).fetchall():
                    prev[path] = sha
                    if mt is not None:
                        prev_stat[path] = (size, mt, ln, sha)
                c.close()
            except Exception as e:
                print("[syscat] 上一版庫讀不到(%s),這次不算差異、全部重算雜湊" % type(e).__name__, flush=True)
    rows, three, sources = collect(via, prev_stat)
    reused = sum(1 for f in rows["files"] if f[0] in prev_stat and prev_stat[f[0]][1] == f[10])
    now = {f[0]: f[9] for f in rows["files"]}
    if prev:
        rows["changes"] = ([[p, "新增", "", now[p]] for p in sorted(set(now) - set(prev))] +
                           [[p, "改了", prev[p], now[p]] for p in sorted(set(now) & set(prev)) if prev[p] != now[p]] +
                           [[p, "不見", prev[p], ""] for p in sorted(set(prev) - set(now))])
    meta = {"engine": ENGINE, "backend": kind, "built_at": t0.strftime("%Y-%m-%dT%H:%M:%SZ"), "git_head": _head(via),
            "should": str(three["should"]), "done": str(three["done"]), "skipped": json.dumps(three["skipped"], ensure_ascii=False),
            "how": three["how"], "sources": json.dumps(sources, ensure_ascii=False), "prev": "yes" if prev else "no", "params": PARAM_NOTE}
    final = out / (DB_NAME + (".duckdb" if kind == "duckdb" else ".sqlite"))
    tmp = out / (".%s.%d.tmp%s" % (DB_NAME, os.getpid(), final.suffix))
    if tmp.exists():
        tmp.unlink()
    _write(tmp, kind, mod, rows, meta)
    os.replace(str(tmp), str(final))
    for other in (out / (DB_NAME + ".duckdb"), out / (DB_NAME + ".sqlite")):
        if other != final and other.exists():
            other.unlink()            # 換了後端:舊的那一份是本動詞自己產的衍生檔
    ok = three["should"] == three["done"] + len(three["skipped"])
    lamp = "RED" if not ok else ("YELLOW" if (kind != "duckdb" or three["skipped"] or not PARAM_OK) else "GREEN")
    secs = (_dt.datetime.now(_dt.timezone.utc) - t0).total_seconds()
    print("[syscat build] %s · %s · 應掃 %d · 已掃 %d · 略過 %d · %.1f 秒(沿用上一版雜湊 %d 檔)· %s" % (lamp, kind, three["should"], three["done"], len(three["skipped"]), secs, reused, final))
    print("  " + " · ".join("%s %d" % (t, len(rows.get(t) or [])) for t in TABLES if t not in ("meta",)))
    print("  [參數] " + (PARAM_NOTE if PARAM_OK else "[黃] " + PARAM_NOTE))
    if kind != "duckdb":
        print("  [黃] 這台沒有 duckdb,先用 Python 內建 sqlite 代替(同表同欄);裝:via-install duckdb(經安裝閘)")
    for s in three["skipped"][:10]:
        print("  [略過] " + s)
    print("NEXT: %s" % ('via-vcgc run CGC_MDL228_VIADBManager syscat q "@fam CGC_MDL158"(或任一 SELECT)' if ok else "對帳不符,先看略過清單"))
    return 0 if lamp == "GREEN" else (2 if lamp == "YELLOW" else 1)


def guard(sql: str) -> str:
    """只准讀:回空字串 = 過;否則回擋下的理由。"""
    s = re.sub(r"--[^\n]*|/\*.*?\*/", " ", sql, flags=re.S).strip()
    if not s:
        return "空的查詢"
    if ";" in s.rstrip(";"):
        return "一次只准一句"
    if not ALLOW_HEAD.match(s):
        return "只准 SELECT · WITH · DESCRIBE · SUMMARIZE · SHOW · PRAGMA table_info"
    s2 = re.sub(r"'(?:[^']|'')*'", "''", s)        # 字串內容不算關鍵字(但 FROM '檔' 另擋)
    m = FORBID.search(s2) or re.search(r"\b(?:from|join)\s+'", s, re.I)
    return ("不准:%s(只讀庫、不准讀檔或出網)" % m.group(0).strip()) if m else ""


def card(cols, data, limit, title, cost_note=""):
    shown = data[:limit]

    def cell(v):
        t = "" if v is None else str(v).replace("\n", " ").replace("|", "¦")
        return t if len(t) <= CELL else t[:CELL - 1] + "…"
    lines = ["[syscat q] %s · 共 %d 列 · 顯示 %d%s" % (title, len(data), len(shown), (" · 截斷(加 --limit N,最多 %d)" % MAX_LIMIT) if len(data) > len(shown) else "")]
    lines.append("| " + " | ".join(cols) + " |")
    lines += ["| " + " | ".join(cell(v) for v in r) + " |" for r in shown]
    body = "\n".join(lines)
    return body + "\n[token 帳] 卡≈%d%s" % (tok(body), cost_note)


def _open(out: Path):
    p = db_path(out)
    if p is None:
        return None, None, "還沒有系統庫:先跑 syscat build"
    kind, mod = _backend("" if p.suffix == ".duckdb" else "sqlite")
    if (kind == "duckdb") != (p.suffix == ".duckdb"):
        return None, None, "庫是 %s,但這台沒有 duckdb" % p.name
    return _connect(p, kind, mod, True), p, ""


def query(args: list, out: Path = OUT_DEFAULT) -> int:
    as_json = "--json" in args
    limit = DEFAULT_LIMIT
    if "--limit" in args:
        try:
            limit = max(1, min(MAX_LIMIT, int(args[args.index("--limit") + 1])))
        except (IndexError, ValueError):
            print("[syscat q] --limit 要接數字")
            return 2
        args = [a for i, a in enumerate(args) if a != "--limit" and (i == 0 or args[i - 1] != "--limit")]
    args = [a for a in args if a != "--json"]
    if not args:
        print('[syscat q] 用法:syscat q "SELECT …" | syscat q @<%s> [字]' % "|".join(PRESETS))
        return 2
    text = " ".join(args).strip()
    params, title, cost = [], "", ""
    if text.startswith("@"):
        name, _, word = text[1:].partition(" ")
        if name not in PRESETS:
            print("[syscat q] 沒有這個預設:@%s(有:%s)" % (name, " · ".join("@" + k for k in PRESETS)))
            return 2
        sql, title, _src = PRESETS[name]
        word = word.strip()
        n = sql.count("?")
        params = ([word, "%" + word + "%"] if n == 2 else ["%" + word + "%"]) if n else []
        title = "@%s %s · %s" % (name, word, title)
    else:
        sql = text
        why = guard(sql)
        if why:
            print("[syscat q] 擋下:%s" % why)
            return 2
        title = "SQL"
    con, p, err = _open(out)
    if con is None:
        print("[syscat q] %s" % err)
        return 2
    try:
        cur = con.execute(sql, params)
        cols = [d[0] for d in cur.description]
        data = cur.fetchall()
        meta = dict(con.execute("SELECT key, value FROM meta").fetchall())
    except Exception as e:
        print("[syscat q] 查詢錯:%s" % str(e).splitlines()[0][:200])
        return 1
    finally:
        con.close()
    stale = _stale(meta)
    if as_json:
        print(json.dumps({"title": title, "columns": cols, "rows": [list(r) for r in data[:limit]], "total": len(data),
                          "built_at": meta.get("built_at"), "stale": stale}, ensure_ascii=False, default=str))
        return 0
    print(card(cols, data, limit, title))
    print("[庫] %s · 建於 %s · HEAD %s%s" % (p.name, meta.get("built_at"), meta.get("git_head"), (" · 過期:%s(重跑 syscat build)" % "、".join(stale[:4])) if stale else " · 新鮮"))
    return 0


def _stale(meta: dict) -> list:
    out = []
    reg = VIA / "supportive modules" / "registry"
    try:
        src = json.loads(meta.get("sources") or "{}")
    except ValueError:
        src = {}
    for name, sha in src.items():
        cand = [reg / name, VIA / "docs" / "handoff" / "daily" / name]
        p = next((c for c in cand if c.exists()), None)
        if p is None or sha_lf(p.read_bytes()) != sha:
            out.append(name)
    head = _head(VIA)
    if head and meta.get("git_head") and head != meta.get("git_head"):
        out.append("HEAD %s → %s" % (meta.get("git_head"), head))
    return out


def stats(out: Path = OUT_DEFAULT) -> int:
    con, p, err = _open(out)
    if con is None:
        print("[syscat stats] 灰 · %s" % err)
        return 2
    try:
        meta = dict(con.execute("SELECT key, value FROM meta").fetchall())
        counts = [(t, con.execute("SELECT count(*) FROM %s" % t).fetchone()[0]) for t in TABLES if t != "meta"]
    finally:
        con.close()
    st = _stale(meta)
    lamp = "YELLOW" if st or meta.get("backend") != "duckdb" else "GREEN"
    print("[syscat stats] %s · %s(%s)· 建於 %s · HEAD %s · 應掃 %s · 已掃 %s · 略過 %d" % (
        lamp, p.name, meta.get("backend"), meta.get("built_at"), meta.get("git_head"), meta.get("should"), meta.get("done"),
        len(json.loads(meta.get("skipped") or "[]"))))
    print("  " + " · ".join("%s %d" % c for c in counts))
    if st:
        print("  [過期] " + "、".join(st[:8]))
    print("  預設:" + " · ".join("@%s(%s)" % (k, v[1]) for k, v in PRESETS.items()))
    return 0 if lamp == "GREEN" else 2


def diff(out: Path = OUT_DEFAULT) -> int:
    return query(["@changed", "--limit", "60"], out)


PAGE_TABS = (  # (分頁, 表, 欄, 排序, 上限)
    ("家族尾版", "families", "system, family, folder, versions, tail_version, tail_code, tail_doc", "system, family", 4000),
    ("工具鎖", "tools", "family, version, code, activated_at, path", "family", 200),
    ("需求", "requirements", "code, subsystem, status, topic, next, book", "code DESC", 2000),
    ("工作流", "workflows", "code, name, kind, version, steps, book", "code DESC", 1000),
    ("帳燈", "ledger", "lamp, kind, id, event, file, ts", "ts DESC", 1500),
    ("鎖定", "locks", "path, version, vcgc_code, locked_at, what", "locked_at DESC", 1000),
    ("變更", "changes", "change, path", "change, path", 2000),
)


def _ui_tokens(reg: Path = HERE) -> tuple:
    """視覺值只取鎖定冊 VIA_UI_Template_SSOT 尾版的 tokens;本檔不帶色碼。"""
    hits = sorted(reg.glob("VIA_UI_Template_SSOT_v[0-9][0-9][0-9][0-9].json"))
    if not hits:
        return "", "UI_TOKENS=灰(鎖定冊不在)"
    tk = json.loads(hits[-1].read_text(encoding="utf-8")).get("tokens") or {}
    root = ":root{" + ";".join("--%s:%s" % (k, v) for k, v in tk.items() if "<" not in str(v) and "}" not in str(v) and ";" not in str(v)) + "}"
    return root, hits[-1].name


PAGE_CSS = """*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:var(--fs)/var(--lh) var(--font)}
.wrap{display:grid;grid-template-columns:var(--aside-w) 1fr;min-height:100vh}
aside{background:var(--panel);border-right:1px solid var(--line);padding:12px;position:sticky;top:0;height:100vh;overflow:auto}
aside h1{font:var(--w-bold) var(--fs-h) var(--serif);margin:0 0 2px}aside .sub{color:var(--dim);font-size:var(--fs-note);margin-bottom:10px}
aside label{display:block;color:var(--dim);font-size:var(--fs-note);margin:10px 0 3px}
aside input,aside select{width:100%;padding:5px 6px;border:1px solid var(--line);border-radius:var(--radius);background:var(--chip);color:var(--txt);font:inherit}
.tabs button{display:block;width:100%;text-align:left;margin:3px 0;padding:5px 8px;border:1px solid var(--line);border-radius:var(--radius);background:var(--chip);color:var(--txt);font:inherit;cursor:pointer}
.tabs button.on{background:var(--acc);color:var(--head);border-color:var(--acc)}
.tabs button span{float:right;color:inherit;opacity:.7}
main{padding:14px;min-width:0}.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;margin-bottom:12px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);padding:8px}.card b{display:block;font-size:var(--fs-title)}.card i{color:var(--dim);font-style:normal;font-size:var(--fs-note)}
.note{color:var(--dim);font-size:var(--fs-note);margin:4px 0 8px}
table{width:100%;border-collapse:collapse;table-layout:fixed;background:var(--panel);border:1px solid var(--line)}
th{background:var(--head);color:var(--head-txt);text-align:left;padding:4px var(--pad);border-bottom:1px solid var(--line);cursor:pointer;position:sticky;top:0}
td{padding:3px var(--pad);border-bottom:1px solid var(--hair);overflow-wrap:anywhere;vertical-align:top}tr:nth-child(even) td{background:var(--zebra)}
td.m{font-family:var(--mono)}.lamp{display:inline-block;min-width:3.2em;text-align:center;border-radius:var(--radius);padding:0 6px;color:var(--head);font-weight:var(--w-bold)}
.l-g{background:var(--lamp-green)}.l-y{background:var(--lamp-yellow)}.l-r{background:var(--lamp-red);animation:bl 2.4s ease-in-out infinite}.l-x{background:var(--lamp-gray)}
@keyframes bl{50%{opacity:.45}}@media(max-width:760px){.wrap{grid-template-columns:1fr}aside{position:static;height:auto}}"""

PAGE_JS = """const D=JSON.parse(document.getElementById('d').textContent);let cur=D.tabs[0].name,sortK=null,sortD=1;
const q=document.getElementById('q'),sy=document.getElementById('sy'),T=document.getElementById('tabs'),M=document.getElementById('m');
function lamp(v){const s=String(v||'').toUpperCase();const c=/GREEN|綠|PASS|OK/.test(s)?'g':/YELLOW|黃|WARN|REVIEW/.test(s)?'y':/RED|紅|FAIL/.test(s)?'r':'x';
const w={g:'綠',y:'黃',r:'紅',x:'灰'}[c];return '<span class="lamp l-'+c+'">'+w+'</span>'}
function esc(v){return String(v==null?'':v).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
function tabs(){T.innerHTML=D.tabs.map(t=>'<button class="'+(t.name==cur?'on':'')+'" data-n="'+esc(t.name)+'">'+esc(t.name)+'<span>'+t.rows.length+'</span></button>').join('');
T.querySelectorAll('button').forEach(b=>b.onclick=()=>{cur=b.dataset.n;sortK=null;draw()})}
function draw(){tabs();const t=D.tabs.find(x=>x.name==cur),k=q.value.trim().toLowerCase(),s=sy.value;
let r=t.rows.filter(row=>(!s||t.cols.indexOf('system')<0||row[t.cols.indexOf('system')]==s||(t.cols.indexOf('subsystem')>=0&&row[t.cols.indexOf('subsystem')]==s))&&(!k||row.join(' ').toLowerCase().includes(k)));
if(s&&t.cols.indexOf('system')<0&&t.cols.indexOf('subsystem')>=0)r=r.filter(row=>String(row[t.cols.indexOf('subsystem')]).toUpperCase().includes(s));
if(sortK!=null)r=r.slice().sort((a,b)=>String(a[sortK]).localeCompare(String(b[sortK]),'zh',{numeric:true})*sortD);
const shown=r.slice(0,500),li=t.cols.indexOf('lamp');
M.innerHTML='<div class="note">'+esc(t.name)+' · 顯示 '+shown.length+' / 符合 '+r.length+' / 本頁收 '+t.rows.length+' / 庫內 '+t.total+(t.total>t.rows.length?' · 本頁只收前 '+t.rows.length+' 列,其餘用 syscat q 查':'')+'</div>'+
'<table><thead><tr>'+t.cols.map((c,i)=>'<th data-i="'+i+'">'+esc(c)+(sortK==i?(sortD>0?' ▲':' ▼'):'')+'</th>').join('')+'</tr></thead><tbody>'+
shown.map(row=>'<tr>'+row.map((v,i)=>'<td class="'+(/path|code|file|version|sha/.test(t.cols[i])?'m':'')+'">'+(i==li?lamp(v):esc(v))+'</td>').join('')+'</tr>').join('')+'</tbody></table>';
M.querySelectorAll('th').forEach(h=>h.onclick=()=>{const i=+h.dataset.i;sortD=sortK==i?-sortD:1;sortK=i;draw()})}
q.oninput=draw;sy.onchange=draw;draw();"""


def page(out: Path) -> int:
    """後端讀系統庫(唯讀) → 前端一個靜態 HTML(不起伺服器;資料內嵌;色與字只取鎖定 token)。"""
    con, p, why = _open(out)
    if con is None:
        print("[syscat page] 灰 · " + why)
        return 2
    import html as _h
    tabs, three = [], {"should": len(PAGE_TABS), "done": 0, "skipped": []}
    try:
        meta = dict(con.execute("SELECT key, value FROM meta").fetchall())
        for name, tbl, cols, order, cap in PAGE_TABS:
            try:
                total = con.execute("SELECT count(*) FROM %s" % tbl).fetchone()[0]
                rows = con.execute("SELECT %s FROM %s ORDER BY %s LIMIT %d" % (cols, tbl, order, cap)).fetchall()
            except Exception as e:  # 表不在 = 這一頁略過並點名
                three["skipped"].append("%s(%s)" % (tbl, type(e).__name__))
                continue
            tabs.append({"name": name, "cols": [c.strip() for c in cols.split(",")], "total": total,
                         "rows": [[("" if v is None else (str(v)[:CELL * 2] if isinstance(v, str) else v)) for v in r] for r in rows]})
            three["done"] += 1
    finally:
        con.close()
    root, src = _ui_tokens()
    counts = {t["name"]: t["total"] for t in tabs}
    cards = "".join('<div class="card"><i>%s</i><b>%s</b></div>' % (_h.escape(k), v) for k, v in counts.items())
    data = json.dumps({"tabs": tabs}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    systems = "".join('<option value="%s">%s</option>' % (s, s) for s in ("VCGC", "VDF", "VRN", "VQG", "VAP"))
    doc = ("<!DOCTYPE html><html lang=\"zh-Hant\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
           "<title>VCGC 系統庫</title><style>%s\n%s</style></head><body><div class=\"wrap\"><aside><h1>VCGC 系統庫</h1>"
           "<div class=\"sub\">建庫 %s · HEAD %s · %s</div><label>關鍵字</label><input id=\"q\" placeholder=\"家族 · 號 · 路徑 · 字\">"
           "<label>系統</label><select id=\"sy\"><option value=\"\">全部</option>%s</select><label>分頁</label><div class=\"tabs\" id=\"tabs\"></div>"
           "<div class=\"sub\" style=\"margin-top:12px\">只含程式結構與冊的中繼資料;不含市場資料、研報或庫內容。視覺 token:%s</div></aside>"
           "<main><div class=\"cards\">%s</div><div id=\"m\"></div></main></div>"
           "<script type=\"application/json\" id=\"d\">%s</script><script>%s</script></body></html>") % (
        root, PAGE_CSS, _h.escape(str(meta.get("built_at", "?"))), _h.escape(str(meta.get("git_head", "?"))[:9]),
        _h.escape(p.name), systems, _h.escape(src), cards, data, PAGE_JS)
    out.mkdir(parents=True, exist_ok=True)
    dst = out / (DB_NAME + ".html")
    tmp = out / (".%s.%d.tmp.html" % (DB_NAME, os.getpid()))
    tmp.write_text(doc, encoding="utf-8", newline="\n")
    os.replace(str(tmp), str(dst))
    ok = three["should"] == three["done"] + len(three["skipped"])
    lamp = "RED" if not ok else ("YELLOW" if (three["skipped"] or not root) else "GREEN")
    print("[syscat page] %s · 應收 %d · 已收 %d · 略過 %d%s" % (lamp, three["should"], three["done"], len(three["skipped"]),
          (" " + "、".join(three["skipped"])) if three["skipped"] else ""))
    print("  頁:%s(%d KB)· 視覺 token:%s" % (dst, dst.stat().st_size // 1024, src))
    print("NEXT: 開這一頁;要的列不在頁上 → syscat q @<預設> <字>")
    return {"GREEN": 0, "YELLOW": 2, "RED": 1}[lamp]


def syscat(args: list) -> int:
    apply_params()
    out = OUT_DEFAULT
    if "--out" in args:
        out = Path(args[args.index("--out") + 1])
        args = [a for i, a in enumerate(args) if a != "--out" and (i == 0 or args[i - 1] != "--out")]
    sub = args[0] if args else "stats"
    rest = args[1:]
    if sub == "build":
        return build(VIA, out, "sqlite" if "--sqlite" in rest else "")
    if sub in ("q", "query"):
        return query(rest, out)
    if sub == "stats":
        return stats(out)
    if sub == "diff":
        return diff(out)
    if sub == "page":
        return page(out)
    print("[syscat] 用法:syscat build [--sqlite] | page | q \"SELECT …\" | q @<%s> [字] [--limit N] [--json] | stats | diff  [--out <夾>]" % "|".join(PRESETS))
    return 2


def __getattr__(name):  # 薄尾轉接
    return getattr(PRIOR, name)


def selftest() -> int:
    import subprocess
    fails = []

    def chk(name, cond, got=None):
        print("  [%s] %s%s" % ("過" if cond else "敗", name, "" if cond else " · 得到 %r" % (got,)), flush=True)
        if not cond:
            fails.append(name)
    print("=== %s 自測(系統庫 syscat)===" % ENGINE, flush=True)
    chk("① 直接前版 v0104 自測過(甲 裁定:只驗自己與直接前版)", PRIOR.selftest() == 0)
    note = apply_params(HERE)
    chk("①b 真倉:參數冊尾版讀得到,八個預設查詢與掃描範圍都從冊來", PARAM_OK and note.startswith(PARAM_STEM) and len(PRESETS) >= 8 and ".py" in EXTS, note)
    global VIA
    keep = VIA
    tmp = Path(tempfile.mkdtemp(prefix="via_syscat_st_"))
    try:
        via = tmp / "via"
        reg = via / "supportive modules" / "registry"
        (reg / "VIA_NumberBooks").mkdir(parents=True)
        (via / "docs" / "handoff" / "daily").mkdir(parents=True)
        (via / "VIA_Reports").mkdir()
        (reg / "CGC_MDL900_Demo_v0100.py").write_text('"""CGC_MDL900_Demo v0100 — 示範本體"""\nX = 1\n', encoding="utf-8")
        (reg / "CGC_MDL900_Demo_v0101.py").write_bytes(b'"""CGC_MDL900_Demo v0101 \xe2\x80\x94 \xe8\x96\x84\xe5\xb0\xbe"""\r\nY = 2\r\n')   # CRLF
        (reg / "VDF_ENG001_Fetch_v0100.py").write_text("Z = 3\n", encoding="utf-8")
        (reg / "VIA_NumberBooks" / "VIA_NumberBook_MDL_v0100.jsonl").write_text(
            json.dumps({"code": "VIA-VCGC-MDL9001", "name": "CGC_MDL900_Demo_v0101", "system": "VCGC"}) + "\n", encoding="utf-8")
        (reg / "VIA_ToolVersion_Lock_v0100.json").write_text(json.dumps({"token": {"version": "v0101", "path": "x/CGC_MDL900_Demo_v0101.py", "sha256": "ab"}}), encoding="utf-8")
        (reg / (PARAM_STEM + "_v0100.json")).write_text((HERE / sorted(HERE.glob(PARAM_STEM + "_v*.json"))[-1].name).read_text(encoding="utf-8"), encoding="utf-8")
        (reg / "VIA_EngineVersion_Register_v0100.json").write_text(json.dumps({"rows": [{"family": "token", "role": "engine", "code": "VIA-TOOL-9999"}]}), encoding="utf-8")
        (reg / "VIA_Requirements_SSOT_v0001.json").write_text(json.dumps({"requirements": [{"code": "VCGC-REQ001", "subsystem": "VCGC", "status": "COVERED", "topic": "示範需求"}]}, ensure_ascii=False), encoding="utf-8")
        (reg / "VIA_Workflow_VCGC_SSOT_v0001.json").write_text(json.dumps({"workflows": [{"code": "VCGC-WKF001", "name": "示範", "kind": "procedure", "version": "v0100", "steps": [1, 2]}]}, ensure_ascii=False), encoding="utf-8")
        (reg / "VIA_VCGC_FunctionInventory_SSOT_v0001.json").write_text(json.dumps({"stations": [{"id": "V-x", "name": "x", "argv": ["x"], "version": "v1"}], "coverage": {"verb": {"x": {"station": "V-x"}}}}), encoding="utf-8")
        (reg / "VIA_VCGC_FunctionLedger_v0100.jsonl").write_text(json.dumps({"kind": "family", "id": "family:CGC_MDL900_Demo", "event": "changed", "lamp": "GREEN", "file": "CGC_MDL900_Demo_v0101.py", "ts": "2026-11-26T00:00:00Z"}) + "\n", encoding="utf-8")
        (via / "VIA_Reports" / "secret.json").write_text("{}", encoding="utf-8")
        (via / "data.parquet").write_bytes(b"PAR1")
        g = dict(os.environ, GIT_AUTHOR_NAME="st", GIT_AUTHOR_EMAIL="st@example.invalid", GIT_COMMITTER_NAME="st", GIT_COMMITTER_EMAIL="st@example.invalid")
        for a in (["init", "-q"], ["add", "-A", "-f"], ["commit", "-q", "-m", "st"]):
            subprocess.run(["git", *a], cwd=str(via), env=g, capture_output=True, check=True)
        VIA = via
        out = via / "VIA_Reports" / "vcgc" / "syscat"
        before = sorted(p.relative_to(via).as_posix() for p in via.rglob("*") if ".git/" not in p.as_posix() + "/" and "VIA_Reports" not in p.as_posix())
        apply_params(reg)
        rc = build(via, out)
        p = db_path(out)
        chk("② build:duckdb 庫寫在 VIA_Reports/vcgc/syscat(衍生檔,可重建)", rc in (0, 2) and p is not None and p.suffix == ".duckdb", (rc, p))
        con = _connect(p, "duckdb", _backend()[1], True)
        meta = dict(con.execute("SELECT key, value FROM meta").fetchall())
        files = [r[0] for r in con.execute("SELECT path FROM files ORDER BY path").fetchall()]
        chk("③ 三數對得上;只收 git 追蹤的程式與冊:VIA_Reports 與 .parquet 不進庫", meta["should"] == meta["done"] and not any("VIA_Reports" in f or f.endswith(".parquet") for f in files), (meta["should"], meta["done"], files))
        sh = dict(con.execute("SELECT name, sha256_lf FROM files").fetchall())
        chk("④ CRLF 檔的雜湊先統一成 LF", sh["CGC_MDL900_Demo_v0101.py"] == hashlib.sha256('"""CGC_MDL900_Demo v0101 — 薄尾"""\nY = 2\n'.encode("utf-8")).hexdigest())
        fam = con.execute("SELECT versions, tail_version, tail_code, system FROM families WHERE family = 'CGC_MDL900_Demo'").fetchone()
        chk("⑤ 家族:2 版 · 尾版 v0101 · 尾版號取自編號冊 · 系統 VCGC", tuple(fam) == (2, "v0101", "VIA-VCGC-MDL9001", "VCGC"), fam)
        chk("⑥ 工具 · 需求 · 工作流 · 站 · 動詞 · 紀錄各有列", all(con.execute("SELECT count(*) FROM %s" % t).fetchone()[0] == 1 for t in ("tools", "requirements", "workflows", "stations", "verbs", "ledger")))
        con.close()
        chk("⑦ build 不改倉內任何檔(只寫 VIA_Reports)", before == sorted(p.relative_to(via).as_posix() for p in via.rglob("*") if ".git/" not in p.as_posix() + "/" and "VIA_Reports" not in p.as_posix()))
        for bad in ("COPY files TO 'x.csv'", "ATTACH 'x.db'", "SELECT * FROM read_csv('a.csv')", "SELECT * FROM 'data.parquet'",
                    "SELECT 1; DROP TABLE files", "INSERT INTO meta VALUES ('a','b')", "SELECT * FROM read_text('/etc/passwd')",
                    "SELECT * FROM glob('*')", "PRAGMA enable_external_access", "SELECT * FROM 'https://example.invalid/a.csv'", "WITH a AS (SELECT 1) SELECT * FROM a JOIN \"x.csv\" ON true",
                    "INSTALL httpfs"):
            if not guard(bad):
                chk("⑧ 擋下寫入 / 讀檔 / 出網:%s" % bad, False)
        chk("⑧ 十二種寫入 / 讀檔 / 出網的查詢全擋下(只是字串裡有網址不算出網,不擋)", guard("SELECT 'http://x' AS note") == "" and not any(f.startswith("⑧") for f in fails))
        chk("⑨ 字串裡出現關鍵字不誤擋(name LIKE '%update%')", guard("SELECT name FROM files WHERE name LIKE '%update%'") == "")
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r1 = query(["@fam", "MDL900"], out)
            r2 = query(["SELECT", "count(*)", "AS", "n", "FROM", "files"], out)
            r3 = query(["@code", "VIA-VCGC-MDL9001", "--json"], out)
            r4 = query(["SELECT * FROM read_csv('x')"], out)
        txt = buf.getvalue()
        chk("⑩ 預設 @fam · 任意 SELECT · @code --json 都回小卡;帶 token 帳與庫的新鮮度", r1 == r2 == r3 == 0 and "[token 帳] 卡≈" in txt and "新鮮" in txt and '"VIA-VCGC-MDL9001"' in txt, txt[-300:])
        chk("⑪ 擋下的查詢 rc 2,不碰庫", r4 == 2 and "擋下" in txt)
        (reg / "CGC_MDL900_Demo_v0101.py").write_text("Y = 3\n", encoding="utf-8")
        (reg / "CGC_MDL900_Demo_v0102.py").write_text("W = 4\n", encoding="utf-8")
        (reg / "VDF_ENG001_Fetch_v0100.py").unlink()
        for a in (["add", "-A"], ["commit", "-q", "-m", "st2"]):
            subprocess.run(["git", *a], cwd=str(via), env=g, capture_output=True, check=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            s1 = stats(out)
        chk("⑫ 倉變了:stats 照實說過期(HEAD 變了)", s1 == 2 and "過期" in buf.getvalue(), buf.getvalue()[-200:])
        with contextlib.redirect_stdout(io.StringIO()):
            build(via, out)
        con = _connect(db_path(out), "duckdb", _backend()[1], True)
        ch = sorted(con.execute("SELECT change, path FROM changes").fetchall())
        con.close()
        chk("⑬ 第二次 build 記下差異:新增 1 · 改了 1 · 不見 1", [c for c, _ in ch] == ["不見", "改了", "新增"] and any(p.endswith("v0102.py") for _, p in ch), ch)
        os.utime(reg / "CGC_MDL900_Demo_v0100.py", ns=(1, 1))
        (reg / "CGC_MDL900_Demo_v0100.py").write_text('"""CGC_MDL900_Demo v0100 — 示範本體"""\nX = 9\n', encoding="utf-8")   # 同大小、新時間
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            build(via, out)
        con = _connect(db_path(out), "duckdb", _backend()[1], True)
        sha0 = con.execute("SELECT sha256_lf FROM files WHERE name = 'CGC_MDL900_Demo_v0100.py'").fetchone()[0]
        con.close()
        chk("⑬b 沒變的檔沿用上一版雜湊;改過的(大小同、時間變)重算", "沿用上一版雜湊 " in buf.getvalue() and sha0 == hashlib.sha256('"""CGC_MDL900_Demo v0100 — 示範本體"""\nX = 9\n'.encode("utf-8")).hexdigest(), buf.getvalue()[:200])
        with contextlib.redirect_stdout(io.StringIO()):
            r5 = build(via, out, "sqlite")
        p2 = db_path(out)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r6 = query(["@fam", "MDL900"], out)
        chk("⑭ 沒有 duckdb 時用內建 sqlite:同表同欄、可查,燈降黃(rc 2)", r5 == 2 and p2.suffix == ".sqlite" and r6 == 0 and "v0102" in buf.getvalue() and not (out / (DB_NAME + ".duckdb")).exists(), (r5, p2))
        with contextlib.redirect_stdout(io.StringIO()):
            build(via, out)
        con = _connect(db_path(out), "duckdb", _backend()[1], True)
        try:
            con.execute("SELECT * FROM read_text('%s')" % (reg / "CGC_MDL900_Demo_v0100.py").as_posix()).fetchall()
            blocked = False
        except Exception:
            blocked = True
        con.close()
        chk("⑮ 就算繞過關鍵字檢查,唯讀連線也關了外部存取(讀不到檔)", blocked)
        chk("⑯ 暫存檔都清掉了", not list(out.glob(".*tmp*")) and not list(out.glob("*.ndjson")))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r8 = page(out)
        hp = out / (DB_NAME + ".html")
        h = hp.read_text(encoding="utf-8") if hp.exists() else ""
        body = h.split("</style>", 1)[-1]
        chk("⑱ 前端一頁:靜態檔、資料內嵌、色只走 var(--token)(頁身沒有任何色碼)、燈四色白字", r8 in (0, 2) and "<script type=\"application/json\" id=\"d\">" in h
            and not re.search(r"#[0-9a-fA-F]{6}\b", PAGE_CSS + body.split("<script>", 1)[-1]) and "var(--lamp-red)" in h and "http" not in body.split("id=\"d\">", 1)[0], buf.getvalue()[:200])
        dj = json.loads(h.split('id="d">', 1)[1].split("</script>", 1)[0].replace("<\\/", "</"))
        chk("⑲ 頁上七個分頁都在,家族頁真的有列,暫存頁檔清掉", len(dj["tabs"]) == 7 and dj["tabs"][0]["rows"] and not list(out.glob(".*tmp.html")))
        (reg / (PARAM_STEM + "_v0100.json")).unlink()
        apply_params(reg)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            r7 = build(via, out)
        chk("⑰ 參數冊不在:用內建預設照建,燈降黃並點名參數冊", r7 == 2 and "參數冊 %s 不在" % PARAM_STEM in buf.getvalue(), buf.getvalue()[:160])
    finally:
        VIA = keep
        apply_params(HERE)
        shutil.rmtree(str(tmp), ignore_errors=True)
    print("[selftest] %s · %d 敗 · %s" % ("GREEN" if not fails else "RED", len(fails), ENGINE), flush=True)
    return 0 if not fails else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a and a[0] in ("--selftest", "selftest"):
        return selftest()
    if a and a[0] == "syscat":
        return syscat(a[1:])
    if a and a[0] == "version":
        print("%s · %s(薄尾,前版 %s)" % (Path(__file__).name, ENGINE, PRIOR_NAME))
        return 0
    if "--selftest" in a:
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    sys.exit(main())
