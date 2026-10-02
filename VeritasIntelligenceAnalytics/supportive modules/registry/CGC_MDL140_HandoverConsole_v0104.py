#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL140_HandoverConsole v0104 — 薄尾:每日進度交接引擎 `daily`(十點 → 一張 panorama.manifest.json)

操作員 2026-10-02 令「我是指VIA系統每日進度HANDOVER … INTO ONE ENGINE」:十點每日交接清單 + 十個本地免費函式庫併成一支。
L30 相似整合律:交接的正主就是本家族 → 不另起引擎,在 v0103 上加 `daily` 動詞;check / checkpoint / test 照 v0103。
每點只讀既有正主、不另造來源;每點一盞燈 GREEN / YELLOW / RED / NODATA,整張取最差(NODATA 算黃:黃不是綠)。
  ① git      分支 · HEAD SHA-16 · 未提交 / 未追蹤 · stash · 對 origin/main 前後(只讀本機 ref,不 fetch)
  ② ledger   當日 VCGC 事件帳 VIA_Reports/vcgc/events/EVENTS_YYYYMMDD.jsonl(或 --ledger):次數 · 成功率 · 阻斷點;壞行 = 紅
  ③ data     DataFrame 鎖帳(表 · 列數 · data_sha)+ --data 夾內檔 SHA-256(xxhash 在再加 xxh3_64);資料不進 git,只記指紋
  ④ modules  當日動到的版號家族與子系統尾版;已存在的版號 .py/.ps1 被就地改 = 黃 · 被刪 = 紅(L04 只增不減)
  ⑤ schema   DataFrame 鎖帳同表 header_sha 前後不同 = 黃(Schema Mismatch,待確認)
  ⑥ tests    VCGC 串測 TEST_latest.json 的燈與計數;它的 head ≠ 現在 HEAD = 黃(證據過期)
  ⑦ flagged  當日非 OK 事件 + 交接待辦 BLOCKED + --flagged 夾 = Fail-Stop / Replay 佇列
  ⑧ cache    *.sdd_bak · *.tmp · OCR 快取夾 · __pycache__ · 進度暫存:只量、只印清理指令(-WhatIf / -print),不刪
  ⑨ next     T+1 原子任務 T01–T03:--next 先,其餘取交接閘 audit() 的 pending(與 handoff check 的「下一步」同序)
  ⑩ manifest docs/handoff/daily/panorama.manifest.json:契約驗過(pydantic;不在走標準庫同規則)才寫 · 自身 SHA-256;
             同夾只增帳 VIA_Daily_Handover_Ledger_v0100.jsonl 一行;本機 VIA_Reports/handover/daily/ 的 sqlite WAL 帳
             (觸發器擋 UPDATE / DELETE,--replay 重播)與全量 log(螢幕只印卡,L86)。
十個函式庫:GitPython · Rich · Pydantic · DuckDB · Polars · Loguru · xxhash 一律探針式載入,缺 = 走標準庫退路,
清單 toolset 照實記 used / fallback;sqlite3 · json / tomllib · pathlib 是標準庫。不裝套件 · 不連網 · 不執行被讀的檔。
  via-vcgc handoff daily [--dry-run] [--json] [--day YYYY-MM-DD] [--data 夾 …] [--ledger 帳] [--flagged 夾 …]
                         [--next "任務" …] [--config handover.toml] [--no-audit]  |  --verify  |  --replay [YYYY-MM-DD]
  設定檔(選填,預設 docs/handoff/daily/handover.toml):data_dirs · flagged_dirs · next = 字串清單;ledger = 字串。
  夾路徑可帶 {day}(換成 YYYY-MM-DD);相對路徑以倉根起算。
rc:GREEN 0 · YELLOW 2 · RED 1(與 handoff check 同);契約不過 = 1 且不寫。只收 VCGC 呼叫。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import argparse
import ast
import contextlib
import hashlib
import importlib
import importlib.util
import io
import json
import os
import platform
import re
import sqlite3
import subprocess
import sys
import tempfile
import tomllib
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Literal, Optional

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL140_HandoverConsole"
ENGINE = Path(__file__).stem
VERSION = "v0104"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + ENGINE, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
VIA = PRIOR.VIA
POLICY = PRIOR.POLICY
BASE = PRIOR.BASE                               # v0101:read · sha · fingerprint · atomic_json · newest · now · audit


def __getattr__(name: str):
    return getattr(PRIOR, name)


DAILY_REL = "docs/handoff/daily"                # 進版:清單 + 只增帳(極小)
LOCAL_REL = "VIA_Reports/handover/daily"        # 不進版(.gitignore VIA_Reports/*):sqlite 帳 · 全量 log
MANIFEST = "panorama.manifest.json"
LEDGER = "VIA_Daily_Handover_Ledger_v0100.jsonl"
STATE_DB = "VIA_Daily_Handover_State.sqlite"
CONFIG = "handover.toml"
SCHEMA = "VIA.Daily.Handover.Manifest.v1"
LAMPS = ("GREEN", "YELLOW", "RED", "NODATA")
LampT = Literal["GREEN", "YELLOW", "RED", "NODATA"]
_RANK = {"GREEN": 0, "NODATA": 1, "YELLOW": 1, "RED": 2}
RC = {"GREEN": 0, "YELLOW": 2, "RED": 1}
POINTS = (
    ("git", "① 程式碼與分支 Git SHA-16"),
    ("ledger", "② 運行日誌 Ledger Audit"),
    ("data", "③ 資料雜湊指紋"),
    ("modules", "④ 模組版本矩陣"),
    ("schema", "⑤ Schema 契約"),
    ("tests", "⑥ 測試綠燈"),
    ("flagged", "⑦ 例外與重試佇列"),
    ("cache", "⑧ 暫存與快取"),
    ("next", "⑨ T+1 原子任務"),
    ("manifest", "⑩ Panorama 清單"),
)
OPTIONAL = {   # 顯示名 → (import 名, 本引擎用在哪, 缺席時的標準庫退路)
    "GitPython": ("git", "① 讀 Git 狀態", "git CLI(只讀)"),
    "Rich": ("rich", "終端面板", "純文字表"),
    "Pydantic": ("pydantic", "⑩ 清單契約", "標準庫同規則"),
    "DuckDB": ("duckdb", "② 帳 SQL 彙總", "Python 彙總"),
    "Polars": ("polars", "③ Parquet 列數", "不量列數(只雜湊)"),
    "Loguru": ("loguru", "全量 log", "logging"),
    "xxhash": ("xxhash", "③ xxh3_64 快速指紋", "只算 SHA-256"),
}
STDLIB = {"sqlite3": "本機 WAL 只增帳(可重播)", "json/tomllib": "清單序列化 · 設定檔", "pathlib": "掃夾 · 量暫存"}
SUBSYSTEMS = {  # 子系統 → 尾版樣式(倉根相對;{via} = VIA 樹);無版號者記檔數與合併指紋
    "VCGC": "{via}/supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py",
    "HANDOFF": "{via}/supportive modules/registry/CGC_MDL140_HandoverConsole_v*.py",
    "VDF": "{via}/functional modules/VDF/VDF_SystemManager_v*.py",
    "VRN": "{via}/functional modules/VRN/VRN_SystemManager_v*.py",
    "VAP": "{via}/functional modules/VAP/VAP_SystemManager_v*.py",
    "NLP": "{via}/supportive modules/VIA_NLP_System/NLP_SystemManager_v*.py",
    "VPNS": "{via}/supportive modules/VPNS/*.py",
    "VSO": "VeritasStorageOptimizer/engine/*.py",
}
DATA_SUFFIXES = {".parquet", ".duckdb", ".db", ".sqlite", ".csv", ".jsonl", ".json", ".pdf", ".xlsx", ".feather", ".arrow"}
MAX_DATA_FILES = 5000                           # 指紋最多算這麼多檔(超過 = 黃,照實記封頂)
MAX_LISTED = 200                                # 清單只列前 200 檔(指紋 digest 涵蓋全部)
VER_RE = re.compile(r"^(?P<fam>.+)_v(?P<ver>\d{3,})\.(?P<ext>py|ps1|json|jsonl)$")
_OK = {"OK", "SUCCESS", "PASS", "PASSED", "GREEN", "DONE"}
_WARN = {"FINDING", "YELLOW", "WARN", "WARNING", "REVIEW", "SKIP", "SKIPPED", "NODATA"}
CACHE_RULES = (  # (類, 檔或夾, 判準, 要清?, 清理樣式)
    ("sdd_bak", "file", lambda n: n.endswith(".sdd_bak"), True, "*.sdd_bak"),
    ("tmp", "file", lambda n: n.endswith((".tmp", ".temp")) or n.startswith("~$"), True, "*.tmp"),
    ("ocr_cache", "dir", lambda n: "ocr_cache" in n.lower(), True, "*ocr_cache*"),
    ("pycache", "dir", lambda n: n == "__pycache__", False, "__pycache__"),
)
SKIP_DIRS = {".git", "node_modules", ".venv", "venv"}
_LIBS: dict = {}


def _lib(key: str):
    """探針式載入選用函式庫;不在 / 載入失敗 / VIA_DAILY_NO_OPTIONAL=1 → None(走標準庫退路,不裝套件)。"""
    if os.environ.get("VIA_DAILY_NO_OPTIONAL") == "1":
        return None
    if key not in _LIBS:
        name, mod = OPTIONAL[key][0], None
        if importlib.util.find_spec(name) is not None:
            try:
                mod = importlib.import_module(name)
            except Exception:  # 裝了但壞:照退路走,toolset 記 fallback
                mod = None
        _LIBS[key] = mod
    return _LIBS[key]


def toolset() -> list:
    rows = [{"lib": k, "role": role, "state": "used" if _lib(k) is not None else "fallback", "fallback": fb}
            for k, (_, role, fb) in OPTIONAL.items()]
    return rows + [{"lib": k, "role": role, "state": "stdlib", "fallback": ""} for k, role in STDLIB.items()]


def _pt(key, lamp, summary, data) -> dict:
    return {"lamp": lamp, "title": dict(POINTS)[key], "summary": summary, "data": data}


def _worst(lamps) -> str:
    worst = max(lamps, key=lambda x: _RANK[x], default="NODATA")
    return "YELLOW" if worst == "NODATA" else worst


def _rel(path, base) -> str:
    try:
        return Path(path).resolve().relative_to(Path(base).resolve()).as_posix()
    except ValueError:
        return str(path)


def _size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def _window(day: date):
    return f"{day.isoformat()} 00:00", f"{(day + timedelta(days=1)).isoformat()} 00:00"


def _resolve(raw, root, day) -> Path:
    p = Path(str(raw).replace("{day}", day.isoformat())).expanduser()
    return p if p.is_absolute() else Path(root) / p


def _git(root, *args):
    """只讀 git:GitPython 在就借它的 execute,不在或失敗走 git CLI;失敗回 None(誠實,不猜)。"""
    cmd = ["git", "-c", "core.quotepath=false", *args]
    gp = _lib("GitPython")
    if gp is not None:
        try:
            return gp.Repo(str(root), search_parent_directories=True).git.execute(cmd)
        except Exception:  # GitCommandError / 不是工作樹 → 換 git CLI 再問一次
            gp = None
    try:
        cp = subprocess.run(["git", "-C", str(root), *cmd[1:]], capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=60, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
    except (OSError, subprocess.SubprocessError):
        return None
    return cp.stdout.rstrip("\n") if cp.returncode == 0 else None


def repo_root(via=VIA) -> Path:
    top = _git(via, "rev-parse", "--show-toplevel")
    return Path(top) if top else Path(via).resolve().parent


def _jsonl(path):
    rows, bad = [], 0
    for ln in Path(path).read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if not ln.strip():
            continue
        try:
            row = json.loads(ln)
        except json.JSONDecodeError:
            bad += 1
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            bad += 1
    return rows, bad


# ── ① git ──────────────────────────────────────────────────────────────────────────────────────────
def point_git(root, day, exclude=""):
    head = _git(root, "rev-parse", "HEAD")
    if not head:
        return _pt("git", "NODATA", "不是 git 工作樹(或沒有 git)", {"sha16": "", "branch": None})
    since, until = _window(day)
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    entries = []
    for ln in (_git(root, "status", "--porcelain=v1", "--untracked-files=all") or "").splitlines():
        path = ln[3:].strip('"')
        if len(ln) > 3 and not (exclude and path.startswith(exclude)):
            entries.append((ln[:2], path))
    untracked = sum(1 for st, _ in entries if st == "??")
    changed = len(entries) - untracked
    stash = len((_git(root, "stash", "list") or "").splitlines())
    ab = (_git(root, "rev-list", "--left-right", "--count", "HEAD...origin/main") or "").split()
    ahead, behind = (int(ab[0]), int(ab[1])) if len(ab) == 2 else (None, None)
    last = (_git(root, "log", "-1", "--format=%cI%x09%s") or "\t").split("\t", 1)
    today = _git(root, "rev-list", "--count", "--since=" + since, "--until=" + until, "HEAD")
    notes = [n for n in (f"未提交 {changed}" if changed else "", f"未追蹤 {untracked}" if untracked else "",
                         f"stash {stash}" if stash else "",
                         f"落後 origin/main {behind}(本機 ref,未 fetch)" if behind else "") if n]
    data = {"branch": branch, "sha16": head[:16], "sha": head, "changed": changed, "untracked": untracked,
            "stash": stash, "ahead": ahead, "behind": behind, "base": "origin/main(本機 ref)",
            "last_commit": {"at": last[0], "subject": last[-1][:200]}, "commits_today": int(today or 0),
            "dirty_sample": [p for _, p in entries[:10]]}
    summary = f"{branch} @ {head[:16]} · 當日提交 {data['commits_today']} · " + (" · ".join(notes) if notes else "乾淨")
    return _pt("git", "YELLOW" if notes else "GREEN", summary, data)


# ── ② ledger ───────────────────────────────────────────────────────────────────────────────────────
def verdict(row) -> str:
    """一筆事件 → ok / warn / fail。rc 0 + OK 類 = ok;rc 2 或 FINDING 類 = warn;沒有判決欄 = warn(不能算成功)。"""
    rc = row.get("rc", row.get("returncode"))
    out = str(row.get("outcome") or row.get("status") or row.get("result") or "").upper()
    if (out in _OK and rc in (0, None)) or (not out and rc == 0):
        return "ok"
    if out in _WARN or rc == 2 or (not out and rc is None):
        return "warn"
    return "fail"


def _secs(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def ledger_stats(rows):
    """(計數 {ok,warn,fail}, 各動詞次數前 12, 總秒數, 彙總引擎)。DuckDB 在走 SQL,不在走 Python;兩路同序同值。"""
    recs = [(str(r.get("verb") or r.get("act") or r.get("step") or "?"), verdict(r), _secs(r.get("secs"))) for r in rows]
    duck = _lib("DuckDB")
    if duck is not None:
        try:
            con = duck.connect(":memory:")
            con.execute("CREATE TABLE ev(verb VARCHAR, verdict VARCHAR, secs DOUBLE)")
            if recs:
                con.executemany("INSERT INTO ev VALUES (?, ?, ?)", recs)
            counts = dict(con.execute("SELECT verdict, count(*) FROM ev GROUP BY verdict").fetchall())
            verbs = con.execute("SELECT verb, count(*) FROM ev GROUP BY verb ORDER BY 2 DESC, 1 LIMIT 12").fetchall()
            secs = float(con.execute("SELECT coalesce(sum(secs), 0) FROM ev").fetchone()[0])
            con.close()
            return ({k: int(counts.get(k, 0)) for k in ("ok", "warn", "fail")}, {v: int(n) for v, n in verbs},
                    round(secs, 1), "duckdb")
        except Exception:  # DuckDB 壞:照 Python 彙總,engine 照實記 python
            duck = None
    tally = {}
    for verb, _, _ in recs:
        tally[verb] = tally.get(verb, 0) + 1
    verbs = dict(sorted(tally.items(), key=lambda kv: (-kv[1], kv[0]))[:12])
    counts = {k: sum(1 for _, v, _ in recs if v == k) for k in ("ok", "warn", "fail")}
    return counts, verbs, round(sum(s for _, _, s in recs), 1), "python"


def point_ledger(via, day, ledger=None):
    path = Path(ledger) if ledger else Path(via) / "VIA_Reports" / "vcgc" / "events" / f"EVENTS_{day:%Y%m%d}.jsonl"
    rel = _rel(path, via)
    if not path.is_file():
        return _pt("ledger", "NODATA", f"當日帳不在:{rel}", {"file": rel, "total": 0}), []
    rows, bad = _jsonl(path)
    counts, verbs, secs, engine = ledger_stats(rows)
    total = len(rows)
    queue = [{"kind": "ledger", "verdict": verdict(r), "ts": r.get("ts"), "verb": r.get("verb") or r.get("act"),
              "target": r.get("target"), "rc": r.get("rc"), "outcome": r.get("outcome") or r.get("status"),
              "error": str(r.get("error") or "")[:160]} for r in rows if verdict(r) != "ok"]
    data = {"file": rel, "total": total, **counts, "bad_lines": bad,
            "success_rate": round(counts["ok"] / total, 4) if total else None,
            "fail_rate": round(counts["fail"] / total, 4) if total else None,
            "by_verb": verbs, "secs": secs, "engine": engine}
    if bad:
        lamp = "RED"
    elif not total:
        lamp = "NODATA"
    else:
        lamp = "YELLOW" if counts["fail"] or counts["warn"] else "GREEN"
    rate = f"{data['success_rate']:.0%}" if total else "—"
    summary = (f"{total} 次 · 成功 {counts['ok']} · 黃 {counts['warn']} · 紅 {counts['fail']} · 成功率 {rate} · {secs}s"
               + (f" · 壞行 {bad}(只增帳完整性)" if bad else ""))
    return _pt("ledger", lamp, summary, data), queue


# ── ③ data · ⑤ schema(同一本 DataFrame 鎖帳)──────────────────────────────────────────────────────────
def lock_rows(via):
    path = BASE.newest(via, "supportive modules/registry/VIA_DataFrame_Lock_Ledger_v*.jsonl")
    if path is None or not path.is_file():
        return None, [], 0
    rows, bad = _jsonl(path)
    return path, rows, bad


def _hash_file(path):
    h = hashlib.sha256()
    xx = _lib("xxhash")
    x = xx.xxh3_64() if xx is not None else None
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
            if x is not None:
                x.update(chunk)
    return h.hexdigest(), (x.hexdigest() if x is not None else None)


def _parquet_rows(path):
    pl = _lib("Polars")
    if pl is None or path.suffix.lower() != ".parquet":
        return None
    try:
        return int(pl.scan_parquet(str(path)).select(pl.len()).collect().item())
    except Exception:  # 壞檔 / 舊版 polars:不量列數,只雜湊
        return None


def point_data(via, root, day, dirs, lock):
    path, rows, bad = lock
    tables = {}
    for r in rows:
        if r.get("table"):
            tables[r["table"]] = {"subsystem": r.get("subsystem"), "rows": r.get("rows"), "data_sha": r.get("data_sha"),
                                  "header_sha": r.get("header_sha"), "at": r.get("at")}
    today = sum(1 for r in rows if str(r.get("at", "")).startswith(day.isoformat()))
    files, scanned, missing, truncated = [], [], [], False
    for raw in dirs:
        d = _resolve(raw, root, day)
        if not d.is_dir():
            missing.append(str(raw))
            continue
        hits = sorted(p for p in d.rglob("*") if p.is_file() and p.suffix.lower() in DATA_SUFFIXES)
        if len(files) + len(hits) > MAX_DATA_FILES:
            truncated, hits = True, hits[:max(0, MAX_DATA_FILES - len(files))]
        nbytes = 0
        for p in hits:
            sha256, xxh = _hash_file(p)
            size = p.stat().st_size
            nbytes += size
            files.append({"path": _rel(p, root), "bytes": size, "sha256": sha256, "xxh3_64": xxh, "rows": _parquet_rows(p)})
        scanned.append({"dir": _rel(d, root), "files": len(hits), "bytes": nbytes})
    digest = (BASE.fingerprint({"files": [[f["path"], f["sha256"]] for f in files],
                                "tables": {k: v["data_sha"] for k, v in sorted(tables.items())}})
              if files or tables else None)
    total = sum(f["bytes"] for f in files)
    data = {"digest": digest, "hash": "sha256" + ("+xxh3_64" if _lib("xxhash") is not None else ""),
            "lock_ledger": _rel(path, via) if path else None, "tables": tables, "tables_today": today,
            "lock_bad_lines": bad, "dirs": scanned, "missing_dirs": missing, "files_total": len(files),
            "bytes_total": total, "files": files[:MAX_LISTED], "truncated": truncated}
    if bad:
        lamp = "RED"
    elif not files and not today:
        lamp = "NODATA"
    else:
        lamp = "YELLOW" if missing or truncated else "GREEN"
    summary = (f"鎖帳 {len(tables)} 表(當日 {today})· 檔 {len(files)} · {_size(total)}"
               + (f" · 夾不在 {len(missing)}" if missing else "") + (" · 檔數封頂" if truncated else "")
               + ("" if dirs else " · 沒指定資料夾(--data / handover.toml)")
               + (f" · 指紋 {digest[:16]}" if digest else ""))
    return _pt("data", lamp, summary, data)


def point_schema(via, lock):
    path, rows, bad = lock
    hist = {}
    for r in rows:
        if r.get("table") and r.get("header_sha"):
            hist.setdefault(r["table"], []).append((r.get("at"), r["header_sha"], r.get("book")))
    drift = [{"table": t, "from": s[-2][1], "to": s[-1][1], "at": s[-1][0], "book": s[-1][2]}
             for t, s in sorted(hist.items()) if len(s) >= 2 and s[-1][1] != s[-2][1]]
    data = {"lock_ledger": _rel(path, via) if path else None, "tables": len(hist), "drift": drift,
            "locked": {t: s[-1][1] for t, s in sorted(hist.items())}, "bad_lines": bad}
    lamp = "RED" if bad else "NODATA" if not hist else "YELLOW" if drift else "GREEN"
    summary = f"鎖定 {len(hist)} 表 · 欄位漂移 {len(drift)}" + ((":" + ", ".join(d["table"] for d in drift[:5])) if drift else "")
    return _pt("schema", lamp, summary, data)


# ── ④ modules ──────────────────────────────────────────────────────────────────────────────────────
def classify_changes(rows) -> dict:
    """[(git 狀態 A/M/D, 路徑, 提交)] → 版號家族表。當日新增後再改 / 再刪的不算(前一天不存在);
    同一提交同家族有新增的刪 = 改號(撞號改編,例 4b3219d4),沒有 = 刪;JSON / JSONL 冊照記但不旗(冊與帳可就地增)。"""
    added = {p for st, p, _ in rows if st == "A"}
    adds = {(m["fam"], c) for st, p, c in rows if st == "A" and (m := VER_RE.match(Path(p).name))}
    fams = {}
    for st, path, commit in rows:
        m = VER_RE.match(Path(path).name)
        if not m:
            continue
        fam = fams.setdefault(m["fam"], {"new": [], "inplace": [], "renumbered": [], "deleted": [], "kind": m["ext"]})
        if st == "A":
            bucket = "new"
        elif path in added:
            continue
        elif st == "D":
            bucket = "renumbered" if (m["fam"], commit) in adds else "deleted"
        else:
            bucket = "inplace"
        tag = "v" + m["ver"]
        if tag not in fam[bucket]:
            fam[bucket].append(tag)
    for fam in fams.values():
        for key in ("new", "inplace", "renumbered", "deleted"):
            fam[key].sort()
    return fams


def _changes(root, day, include_worktree):
    """當日提交 + (今天才算)工作樹的 [(A/M/D, 路徑, 提交)];不偵測改名(改號由 classify_changes 判)。"""
    since, until = _window(day)
    rows, commit = [], ""
    log = _git(root, "log", "--since=" + since, "--until=" + until, "--name-status", "--no-renames",
               "--format=@%H", "HEAD")
    for ln in (log or "").splitlines():
        if ln.startswith("@"):
            commit = ln[1:]
            continue
        parts = ln.split("\t")
        if len(parts) >= 2 and parts[0]:
            rows.append((parts[0][:1], parts[-1], commit))
    if include_worktree:
        for ln in (_git(root, "status", "--porcelain=v1", "--no-renames", "--untracked-files=all") or "").splitlines():
            if len(ln) > 3:
                xy, path = ln[:2], ln[3:].strip('"')
                rows.append(("A" if ("?" in xy or "A" in xy) else "D" if "D" in xy else "M", path, "WORKTREE"))
    return rows


def _tails(root, via_rel) -> dict:
    out = {}
    for name, pattern in SUBSYSTEMS.items():
        hits = sorted(p for p in Path(root).glob(pattern.format(via=via_rel)) if p.is_file())
        versioned = [p for p in hits if _vnum(p) >= 0]
        if versioned:
            tail = max(versioned, key=_vnum)
            out[name] = {"tail": tail.name, "version": f"v{_vnum(tail):04d}", "versions": len(versioned),
                         "sha16": BASE.sha(tail)[:16]}
        elif hits:
            out[name] = {"tail": None, "files": len(hits),
                         "sha16": BASE.fingerprint({p.name: BASE.sha(p) for p in hits})[:16]}
        else:
            out[name] = {"tail": None, "files": 0}
    return out


def point_modules(root, via_rel, day, include_worktree):
    fams = classify_changes(_changes(root, day, include_worktree))
    engines = {k: v for k, v in fams.items() if v["kind"] in ("py", "ps1")}
    inplace = {k: v["inplace"] for k, v in engines.items() if v["inplace"]}
    renumbered = {k: v["renumbered"] for k, v in engines.items() if v["renumbered"]}
    deleted = {k: v["deleted"] for k, v in engines.items() if v["deleted"]}
    tails = _tails(root, via_rel)
    swapped = [n for n, t in tails.items() if t.get("tail") and (VER_RE.match(t["tail"]) or {"fam": None})["fam"] in fams]
    lamp = "RED" if deleted else "YELLOW" if inplace or renumbered else "GREEN"
    summary = (f"當日版號家族 {len(fams)} · 新版 {sum(len(v['new']) for v in fams.values())}"
               f" · 就地改 {sum(map(len, inplace.values()))} · 改號 {sum(map(len, renumbered.values()))}"
               f" · 刪 {sum(map(len, deleted.values()))}"
               + (f" · 子系統換尾 {','.join(swapped)}" if swapped else "")
               + " · " + " ".join(f"{n} {t['version']}" for n, t in tails.items() if t.get("tail")))
    return _pt("modules", lamp, summary, {"families": fams, "inplace_engines": inplace, "renumbered_engines": renumbered,
                                          "deleted_engines": deleted, "subsystems": tails, "subsystems_changed": swapped})


# ── ⑥ tests ────────────────────────────────────────────────────────────────────────────────────────
def point_tests(via, head):
    via = Path(via)
    snap = {}
    hand = via / "docs" / "handoff" / "HANDOFF_latest.json"
    if hand.is_file():
        try:
            h = BASE.read(hand)
            snap = {"handoff_at": h.get("at"), "handoff_lamp": h.get("lamp"), "closeout_lamp": h.get("closeout_lamp"),
                    "receipts": len(h.get("receipts") or {}), "reusable": len(h.get("reusable_successes") or [])}
        except (OSError, ValueError) as exc:
            snap = {"handoff_error": str(exc)[:160]}
    path = via / "VIA_Reports" / "vcgc" / "TEST_latest.json"
    if not path.is_file():
        return _pt("tests", "NODATA", "沒有串測報告:先跑 via-vcgc test --quick", {"report": None, **snap})
    try:
        t = BASE.read(path)
    except (OSError, ValueError) as exc:
        return _pt("tests", "RED", f"串測報告讀不了:{exc}"[:200], {"report": _rel(path, via), **snap})
    counts = t.get("counts") or {}
    t_head = str(t.get("head") or "")
    stale = bool(head and t_head and not head.startswith(t_head))
    lamp0 = t.get("lamp") if t.get("lamp") in LAMPS else "NODATA"
    lamp = "RED" if lamp0 == "RED" else "YELLOW" if (lamp0 != "GREEN" or stale) else "GREEN"
    not_green = [{"id": r.get("id"), "lamp": r.get("lamp"), "rc": r.get("rc"), "last": str(r.get("last") or "")[:160]}
                 for r in t.get("rows", []) if r.get("lamp") != "GREEN"]
    families = {k: (len(v) if isinstance(v, list) else v) for k, v in (t.get("families") or {}).items()}
    data = {"report": _rel(path, via), "lamp": lamp0, "mode": t.get("mode"), "at": t.get("at"), "head": t_head,
            "stale": stale, "counts": counts, "not_green": not_green, "families": families, **snap}
    summary = (f"串測 {lamp0}({t.get('mode')})· 綠 {counts.get('GREEN', 0)} · 黃 {counts.get('YELLOW', 0)}"
               f" · 紅 {counts.get('RED', 0)} · {t.get('at')}"
               + (f" · 過期:報告 head {t_head} ≠ HEAD" if stale else "")
               + (f" · 交接收據 {snap['receipts']}" if "receipts" in snap else ""))
    return _pt("tests", lamp, summary, data)


# ── ⑦ flagged · ⑧ cache · ⑨ next ────────────────────────────────────────────────────────────────────
def point_flagged(ledger_queue, report, dirs, root, day):
    queue = list(ledger_queue)
    if report:
        queue += [{"kind": "pending", "verdict": "blocked", "id": p.get("id"), "owner": p.get("owner"),
                   "next": str(p.get("next") or "")[:200], "reason": str(p.get("reason") or "")[:200]}
                  for p in report.get("pending", []) if p.get("state") == "BLOCKED"]
        queue += [{"kind": "handoff", "verdict": r.get("lamp"), "rule": r.get("rule"), "detail": str(r.get("detail"))[:200]}
                  for r in report.get("rows", []) if r.get("lamp") in ("RED", "YELLOW")]
    for raw in dirs:
        d = _resolve(raw, root, day)
        if not d.is_dir():
            queue.append({"kind": "dir", "verdict": "missing", "path": str(raw)})
            continue
        for p in sorted(x for x in d.rglob("*") if x.is_file())[:MAX_LISTED]:
            queue.append({"kind": "file", "verdict": "flagged", "path": _rel(p, root), "bytes": p.stat().st_size})
    counts = {}
    for q in queue:
        counts[q["kind"]] = counts.get(q["kind"], 0) + 1
    lamp = "YELLOW" if queue else ("GREEN" if report else "NODATA")
    summary = (" · ".join(f"{k} {n}" for k, n in counts.items()) if queue else "佇列空") + ("" if report else " · 交接閘沒跑")
    return _pt("flagged", lamp, "待處理 " + summary if queue else summary, {"counts": counts, "queue": queue})


def _dir_bytes(path) -> int:
    total = 0
    for dp, _, fns in os.walk(path):
        for fn in fns:
            with contextlib.suppress(OSError):
                total += os.path.getsize(os.path.join(dp, fn))
    return total


def point_cache(root):
    root = Path(root)
    stats = {k: {"count": 0, "bytes": 0, "clean": clean, "kind": kind, "glob": g, "sample": []}
             for k, kind, _, clean, g in CACHE_RULES}

    def hit(cls, full, nbytes):
        s = stats[cls]
        s["count"] += 1
        s["bytes"] += nbytes
        if len(s["sample"]) < 5:
            s["sample"].append(_rel(full, root))

    for dp, dns, fns in os.walk(root):
        keep = []
        for dn in dns:
            if dn in SKIP_DIRS:
                continue
            cls = next((k for k, kind, rule, _, _ in CACHE_RULES if kind == "dir" and rule(dn)), None)
            if cls:
                hit(cls, os.path.join(dp, dn), _dir_bytes(os.path.join(dp, dn)))
            else:
                keep.append(dn)
        dns[:] = keep
        for fn in fns:
            cls = next((k for k, kind, rule, _, _ in CACHE_RULES if kind == "file" and rule(fn)), None)
            if cls:
                with contextlib.suppress(OSError):
                    hit(cls, os.path.join(dp, fn), os.path.getsize(os.path.join(dp, fn)))
    progress = Path(tempfile.gettempdir()) / "VIA_progress"     # TestAuto 進度暫存:續跑要用,只量不清
    if progress.is_dir():
        stats["progress"] = {"count": sum(1 for p in progress.iterdir() if p.is_file()), "bytes": _dir_bytes(progress),
                             "clean": False, "kind": "dir", "glob": str(progress), "sample": []}
    commands = []
    for cls, s in stats.items():
        if not (s["clean"] and s["count"]):
            continue
        if s["kind"] == "file":
            commands.append({"cls": cls, "bash": f"find '{root}' -name '{s['glob']}' -type f -print   # 確認後把 -print 換成 -delete",
                             "pwsh": f"Get-ChildItem -LiteralPath '{root}' -Recurse -Force -File -Filter '{s['glob']}' | Remove-Item -WhatIf   # 確認後拿掉 -WhatIf"})
        else:
            commands.append({"cls": cls, "bash": f"find '{root}' -type d -name '{s['glob']}' -prune -print   # 確認後換成 -exec rm -rf {{}} +",
                             "pwsh": f"Get-ChildItem -LiteralPath '{root}' -Recurse -Force -Directory -Filter '{s['glob']}' | Remove-Item -Recurse -WhatIf   # 確認後拿掉 -WhatIf"})
    lamp = "YELLOW" if commands else "GREEN"
    summary = " · ".join(f"{k} {s['count']}({_size(s['bytes'])})" for k, s in stats.items() if s["count"]) or "乾淨"
    return _pt("cache", lamp, summary + (" · 要清的只印指令,不刪" if commands else ""), {"classes": stats, "commands": commands})


def point_next(report, manual, error=None):
    tasks = [{"id": "", "task": str(t)[:300], "source": "operator"} for t in manual if str(t).strip()]
    pending = (report or {}).get("pending", [])
    for p in pending:
        if len(tasks) >= 3:
            break
        tasks.append({"id": "", "task": str(p.get("next") or "")[:300], "ref": p.get("id"), "owner": p.get("owner"),
                      "state": p.get("state"), "source": "handoff"})
    for i, t in enumerate(tasks, 1):
        t["id"] = f"T{i:02d}"
    data = {"tasks": tasks, "pending_total": len(pending), "error": error}
    if report is None:
        return _pt("next", "NODATA", "交接閘沒跑" + (f":{error}" if error else "(--no-audit)") + f" · 任務 {len(tasks)}", data)
    data.update({"handoff_lamp": report.get("lamp"), "closeout_lamp": report.get("closeout_lamp"),
                 "handoff_summary": report.get("summary")})
    lamp = report.get("lamp") if report.get("lamp") in LAMPS else "NODATA"
    summary = (f"交接閘 {report.get('lamp')} · 驗收 {report.get('closeout_lamp')} · 待辦 {len(pending)}"
               + (f" · {tasks[0]['id']} {tasks[0]['task'][:60]}" if tasks else ""))
    return _pt("next", lamp, summary, data)


# ── ⑩ manifest:組 · 封 · 驗 · 寫 · 重播 ──────────────────────────────────────────────────────────────
def seal(manifest) -> str:
    return BASE.fingerprint({k: v for k, v in manifest.items() if k != "manifest_sha256"})


def build_daily(via=VIA, day=None, root=None, ledger=None, data_dirs=(), flagged_dirs=(), tasks=(), report=None,
                run_audit=True):
    via = Path(via)
    day = day or date.today()
    root = Path(root) if root else repo_root(via)
    via_rel = _rel(via, root)
    audit_error = None
    if report is None and run_audit:
        try:
            report = BASE.audit(via)
        except Exception as exc:  # 閘壞照實記進 ⑨,不當成功
            audit_error = f"{type(exc).__name__}: {exc}"[:300]
    git = point_git(root, day, _rel(via / DAILY_REL, root).rstrip("/") + "/")
    ledger_pt, queue = point_ledger(via, day, ledger)
    lock = lock_rows(via)
    points = {
        "git": git,
        "ledger": ledger_pt,
        "data": point_data(via, root, day, list(data_dirs), lock),
        "modules": point_modules(root, via_rel, day, include_worktree=(day == date.today())),
        "schema": point_schema(via, lock),
        "tests": point_tests(via, git["data"].get("sha", "")),
        "flagged": point_flagged(queue, report, list(flagged_dirs), root, day),
        "cache": point_cache(root),
        "next": point_next(report, list(tasks), audit_error),
    }
    validator = ("pydantic " + str(getattr(_lib("Pydantic"), "VERSION", ""))) if _lib("Pydantic") is not None else "stdlib"
    points["manifest"] = _pt("manifest", "GREEN", f"契約驗過才寫({validator})· 自身 SHA-256 · 只增帳 + 本機 sqlite",
                             {"path": f"{DAILY_REL}/{MANIFEST}", "ledger": f"{DAILY_REL}/{LEDGER}",
                              "state_db": f"{LOCAL_REL}/{STATE_DB}", "validator": validator})
    lamps = {k: points[k]["lamp"] for k, _ in POINTS}
    manifest = {"schema": SCHEMA, "engine": ENGINE, "version": VERSION, "day": day.isoformat(), "at": BASE.now(),
                "head16": git["data"].get("sha16", ""), "branch": git["data"].get("branch"), "repo": root.name,
                "via": via_rel, "host": {"system": platform.system(), "python": platform.python_version()},
                "lamp": _worst(lamps.values()), "lamps": lamps, "points": points, "toolset": toolset()}
    manifest["manifest_sha256"] = seal(manifest)
    return manifest


_TOP = ("schema", "engine", "version", "day", "at", "head16", "branch", "repo", "via", "host", "lamp", "lamps",
        "points", "toolset", "manifest_sha256")


def _stdlib_errors(m) -> list:
    """與 pydantic 模型同規則的標準庫檢查(pydantic 不在時用;自測兩路同判)。"""
    if not isinstance(m, dict):
        return ["manifest: 不是物件"]
    errs = [f"{k}: 缺必要欄位" for k in _TOP if k not in m] + [f"{k}: 多出欄位" for k in m if k not in _TOP]
    if m.get("schema") != SCHEMA:
        errs.append("schema: 不是 " + SCHEMA)
    errs += [f"{k}: 要是字串" for k in ("engine", "version", "at", "repo", "via") if not isinstance(m.get(k), str)]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(m.get("day", ""))):
        errs.append("day: 不是 YYYY-MM-DD")
    if not re.fullmatch(r"[0-9a-f]{16}", str(m.get("head16", ""))):
        errs.append("head16: 缺 Git SHA-16")
    if not re.fullmatch(r"[0-9a-f]{64}", str(m.get("manifest_sha256", ""))):
        errs.append("manifest_sha256: 不是 SHA-256")
    if m.get("lamp") not in LAMPS:
        errs.append("lamp: 不是四態燈")
    if not isinstance(m.get("lamps"), dict) or any(v not in LAMPS for v in m["lamps"].values()):
        errs.append("lamps: 要是 點 → 四態燈")
    if not isinstance(m.get("host"), dict):
        errs.append("host: 要是物件")
    if not isinstance(m.get("toolset"), list) or not all(isinstance(x, dict) for x in m["toolset"]):
        errs.append("toolset: 要是物件清單")
    pts = m.get("points") if isinstance(m.get("points"), dict) else {}
    ids = [k for k, _ in POINTS]
    errs += [f"points.{k}: 缺必要欄位" for k in ids if k not in pts] + [f"points.{k}: 多出欄位" for k in pts if k not in ids]
    for k in ids:
        p = pts.get(k)
        if not isinstance(p, dict):
            continue
        if set(p) != {"lamp", "title", "summary", "data"}:
            errs.append(f"points.{k}: 欄位要正好 lamp · title · summary · data")
        if p.get("lamp") not in LAMPS:
            errs.append(f"points.{k}.lamp: 不是四態燈")
        if not isinstance(p.get("title"), str) or not isinstance(p.get("summary"), str):
            errs.append(f"points.{k}: title / summary 要是字串")
        if not isinstance(p.get("data"), dict):
            errs.append(f"points.{k}.data: 要是物件")
    gdata = (pts.get("git") or {}).get("data") or {}
    if not re.fullmatch(r"[0-9a-f]{16}", str(gdata.get("sha16", ""))):
        errs.append("points.git.data.sha16: 缺 Git SHA-16")
    if isinstance(gdata, dict) and "branch" not in gdata:
        errs.append("points.git.data.branch: 缺必要欄位")
    if "digest" not in ((pts.get("data") or {}).get("data") or {}):
        errs.append("points.data.data.digest: 缺資料指紋欄")
    return errs


def _pydantic_errors(pd, m) -> list:
    strict, loose = pd.ConfigDict(extra="forbid"), pd.ConfigDict(extra="allow")
    point = pd.create_model("DailyPoint", __config__=strict, lamp=(LampT, ...), title=(str, ...), summary=(str, ...),
                            data=(dict[str, Any], ...))
    git_data = pd.create_model("DailyGitData", __config__=loose, sha16=(str, pd.Field(pattern=r"^[0-9a-f]{16}$")),
                               branch=(Optional[str], ...))
    data_data = pd.create_model("DailyDataData", __config__=loose, digest=(Optional[str], ...))
    kinds = {"git": pd.create_model("DailyGitPoint", __base__=point, data=(git_data, ...)),
             "data": pd.create_model("DailyDataPoint", __base__=point, data=(data_data, ...))}
    # ⑤ 的鍵 schema 撞 BaseModel 屬性:欄名加 _、別名照原鍵(契約不變,不出 shadow 警告)
    fields = {(k + "_" if hasattr(pd.BaseModel, k) else k): (kinds.get(k, point), pd.Field(alias=k)) for k, _ in POINTS}
    model = pd.create_model(
        "DailyManifest", __config__=strict,
        schema_=(Literal[SCHEMA], pd.Field(alias="schema")), engine=(str, ...), version=(str, ...),
        day=(str, pd.Field(pattern=r"^\d{4}-\d{2}-\d{2}$")), at=(str, ...),
        head16=(str, pd.Field(pattern=r"^[0-9a-f]{16}$")), branch=(Optional[str], ...), repo=(str, ...), via=(str, ...),
        host=(dict[str, Any], ...), lamp=(LampT, ...), lamps=(dict[str, LampT], ...),
        points=(pd.create_model("DailyPoints", __config__=strict, **fields), ...),
        toolset=(list[dict[str, Any]], ...), manifest_sha256=(str, pd.Field(pattern=r"^[0-9a-f]{64}$")))
    try:
        model.model_validate(m)
    except pd.ValidationError as exc:
        return [".".join(str(x) for x in e["loc"]) + ": " + e["msg"] for e in exc.errors()]
    return []


def _semantic_errors(m) -> list:
    ids = [k for k, _ in POINTS]
    errs = [] if list(m["lamps"]) == ids else ["lamps: 要正好十點且照序"]
    errs += [f"lamps.{k}: 與 points.{k}.lamp 不一致" for k in ids if m["lamps"].get(k) != m["points"][k]["lamp"]]
    if m["lamp"] != _worst(m["lamps"].values()):
        errs.append("lamp: 不是十點最差燈")
    if m["head16"] != m["points"]["git"]["data"]["sha16"]:
        errs.append("head16: 與 points.git.data.sha16 不一致")
    if m["manifest_sha256"] != seal(m):
        errs.append("manifest_sha256: 自身雜湊不符(清單被改過)")
    return errs


def validate_manifest(m):
    """(錯誤清單, 驗證器)。結構:pydantic 在走 pydantic,不在走標準庫同規則;結構過了再驗語意(燈 · SHA · 自身雜湊)。"""
    pd = _lib("Pydantic")
    if pd is not None:
        errs, how = _pydantic_errors(pd, m), "pydantic " + str(getattr(pd, "VERSION", ""))
    else:
        errs, how = _stdlib_errors(m), "stdlib"
    return (errs or _semantic_errors(m)), how


def _state_db(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript("""
        CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT NOT NULL, at TEXT NOT NULL,
            head16 TEXT, lamp TEXT NOT NULL, manifest_sha256 TEXT NOT NULL, manifest TEXT NOT NULL);
        CREATE TRIGGER IF NOT EXISTS runs_no_update BEFORE UPDATE ON runs BEGIN SELECT RAISE(ABORT, 'append-only'); END;
        CREATE TRIGGER IF NOT EXISTS runs_no_delete BEFORE DELETE ON runs BEGIN SELECT RAISE(ABORT, 'append-only'); END;
    """)
    return con


def write_daily(via, manifest) -> dict:
    """清單原子寫 → 只增帳一行 → 本機 sqlite 一筆。只在契約驗過後呼叫。"""
    via = Path(via)
    mpath, lpath = via / DAILY_REL / MANIFEST, via / DAILY_REL / LEDGER
    BASE.atomic_json(mpath, manifest)
    line = {"day": manifest["day"], "at": manifest["at"], "head16": manifest["head16"], "branch": manifest["branch"],
            "lamp": manifest["lamp"], "lamps": manifest["lamps"], "manifest_sha16": manifest["manifest_sha256"][:16],
            "host": manifest["host"].get("system"), "by": ENGINE}
    with open(lpath, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(line, ensure_ascii=False, sort_keys=True) + "\n")
    dbpath = via / LOCAL_REL / STATE_DB
    with contextlib.closing(_state_db(dbpath)) as con, con:
        con.execute("INSERT INTO runs(day, at, head16, lamp, manifest_sha256, manifest) VALUES (?, ?, ?, ?, ?, ?)",
                    (manifest["day"], manifest["at"], manifest["head16"], manifest["lamp"], manifest["manifest_sha256"],
                     json.dumps(manifest, ensure_ascii=False, sort_keys=True)))
    return {"manifest": mpath, "ledger": lpath, "state_db": dbpath}


def replay(via, day=None):
    dbpath = Path(via) / LOCAL_REL / STATE_DB
    if not dbpath.is_file():
        return None
    with contextlib.closing(sqlite3.connect(str(dbpath))) as con:
        sql = "SELECT manifest FROM runs" + (" WHERE day = ?" if day else "") + " ORDER BY id DESC LIMIT 1"
        row = con.execute(sql, (day,) if day else ()).fetchone()
    return json.loads(row[0]) if row else None


def verify(path):
    m = BASE.read(path)
    errs, how = validate_manifest(m)
    return errs, how, m


def _config(via, path=None) -> dict:
    p = Path(path) if path else Path(via) / DAILY_REL / CONFIG
    if not p.is_file():
        if path:
            raise FileNotFoundError(str(p))
        return {}
    with open(p, "rb") as fh:
        cfg = tomllib.load(fh)
    unknown = sorted(set(cfg) - {"data_dirs", "flagged_dirs", "next", "ledger"})
    if unknown:
        raise ValueError(f"{p.name}: 不認得的鍵 {unknown}")
    out = {}
    for key in ("data_dirs", "flagged_dirs", "next"):
        value = cfg.get(key, [])
        value = [value] if isinstance(value, str) else value
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            raise ValueError(f"{p.name}: {key} 要是字串清單")
        out[key] = value
    if "ledger" in cfg:
        if not isinstance(cfg["ledger"], str):
            raise ValueError(f"{p.name}: ledger 要是字串")
        out["ledger"] = cfg["ledger"]
    return out


def _open_log(via, day):
    """全量 log 落本機(L86:log 是全的,螢幕只印卡);stderr 只收 WARNING 以上。Loguru 在用它,不在用 logging。"""
    path = Path(via) / LOCAL_REL / "logs" / f"daily_{day:%Y%m%d}.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    lg = _lib("Loguru")
    if lg is not None:
        logger = lg.logger
        logger.remove()
        sinks = [logger.add(str(path), level="DEBUG", encoding="utf-8", rotation="10 MB"),
                 logger.add(sys.stderr, level="WARNING")]
        return (lambda lvl, msg: logger.log(lvl, msg)), (lambda: [logger.remove(s) for s in sinks]), "loguru"
    import logging
    lgr = logging.getLogger(ENGINE + ".daily")
    lgr.setLevel(logging.DEBUG)
    lgr.propagate = False
    fh = logging.FileHandler(path, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s"))
    err = logging.StreamHandler(sys.stderr)
    err.setLevel(logging.WARNING)
    for h in (fh, err):
        lgr.addHandler(h)

    def close():
        for h in (fh, err):
            lgr.removeHandler(h)
            h.close()
    return (lambda lvl, msg: lgr.log(getattr(logging, lvl), msg)), close, "logging"


def render(manifest, written=None, errs=None):
    pts, lamps = manifest["points"], manifest["lamps"]
    tally = {k: sum(1 for v in lamps.values() if v == k) for k in LAMPS}
    head = (f"[每日交接 {VERSION}] {manifest['lamp']} · {manifest['day']} · {manifest['branch']} @ {manifest['head16'] or '—'}"
            f" · 綠 {tally['GREEN']} · 黃 {tally['YELLOW']} · 紅 {tally['RED']} · 無資料 {tally['NODATA']}")
    rich = _lib("Rich")
    shown = False
    if rich is not None:
        try:
            escape = importlib.import_module("rich.markup").escape
            table = importlib.import_module("rich.table").Table(title=escape(head), title_justify="left")
            for col in ("點", "燈", "摘要"):
                table.add_column(col)
            style = {"GREEN": "green", "YELLOW": "yellow", "RED": "bold red", "NODATA": "dim"}
            for k, _ in POINTS:
                p = pts[k]
                table.add_row(p["title"], f"[{style[p['lamp']]}]{p['lamp']}[/]", escape(p["summary"]))
            importlib.import_module("rich.console").Console(soft_wrap=True).print(table)
            shown = True
        except Exception:  # Rich 壞:照純文字表印,不吞內容
            shown = False
    if not shown:
        print(head)
        for k, _ in POINTS:
            print(f"  [{pts[k]['lamp']:<6}] {pts[k]['title']} · {pts[k]['summary']}")
    queue = pts["flagged"]["data"].get("queue", [])
    fails = [q for q in queue if q.get("verdict") in ("fail", "RED")]
    others = [q for q in queue if q not in fails]
    for q in fails:                                 # L86:紅行不受上限,照印
        print("  [FAIL] " + json.dumps({k: v for k, v in q.items() if v not in (None, "")}, ensure_ascii=False)[:300])
    for q in others[:10]:
        print("  [佇列] " + json.dumps({k: v for k, v in q.items() if v not in (None, "")}, ensure_ascii=False)[:300])
    if len(others) > 10:
        print(f"  [佇列] 另 {len(others) - 10} 行在清單 points.flagged.data.queue")
    for t in pts["next"]["data"].get("tasks", []):
        print(f"  {t['id']} {t['task']}" + (f"({t['ref']} · {t.get('owner')})" if t.get("ref") else "(操作員)"))
    for c in pts["cache"]["data"].get("commands", []):
        print(f"  [清理·只印] {c['cls']}: {c['pwsh']}")
        print(f"  [清理·只印] {c['cls']}: {c['bash']}")
    for e in errs or []:
        print(f"  [契約] {e}")
    if written:
        print(f"  [寫入] 清單 {_rel(written['manifest'], VIA)} · 只增帳 {_rel(written['ledger'], VIA)} +1 行"
              f" · 本機帳 {_rel(written['state_db'], VIA)}")
    print(json.dumps({"daily": VERSION, "day": manifest["day"], "lamp": manifest["lamp"], "head16": manifest["head16"],
                      "lamps": lamps, "manifest_sha16": str(manifest.get("manifest_sha256", ""))[:16],
                      "written": bool(written), "contract": "FAIL" if errs else "PASS"}, ensure_ascii=False))


def daily_main(argv) -> int:
    ap = argparse.ArgumentParser(prog="via-vcgc handoff daily", description="每日進度交接十點 → panorama.manifest.json")
    ap.add_argument("--day", help="YYYY-MM-DD(預設今天,本機時區)")
    ap.add_argument("--ledger", help="改讀這本帳(例:universal_ledger.jsonl)")
    ap.add_argument("--data", action="append", default=[], help="要算指紋的資料夾(可重複;可帶 {day})")
    ap.add_argument("--flagged", action="append", default=[], help="例外暫存夾(可重複)")
    ap.add_argument("--next", action="append", default=[], dest="tasks", help="T+1 任務(可重複;排在交接待辦前)")
    ap.add_argument("--config", help="TOML 設定檔(預設 docs/handoff/daily/handover.toml,在才讀)")
    ap.add_argument("--dry-run", action="store_true", help="只算只印,不寫清單 / 帳")
    ap.add_argument("--json", action="store_true", help="印整份清單")
    ap.add_argument("--no-audit", action="store_true", help="不跑交接閘 audit(⑦ ⑨ 照實記沒跑)")
    ap.add_argument("--verify", action="store_true", help="驗現有清單:契約 + 自身雜湊")
    ap.add_argument("--replay", nargs="?", const="", metavar="DAY", help="從本機 sqlite 帳重播某日最後一份")
    a = ap.parse_args(argv)
    if a.verify:
        path = VIA / DAILY_REL / MANIFEST
        if not path.is_file():
            print(f"[每日交接 驗清單] 沒有清單:{DAILY_REL}/{MANIFEST}")
            return 2
        errs, how, m = verify(path)
        print(f"[每日交接 驗清單] {'PASS' if not errs else 'FAIL'} · {how} · {m.get('day')} · {m.get('lamp')}"
              f" · sha16 {str(m.get('manifest_sha256'))[:16]}")
        for e in errs:
            print("  [契約] " + e)
        return 1 if errs else 0
    if a.replay is not None:
        m = replay(VIA, a.replay or None)
        if m is None:
            print(f"[每日交接 重播] 本機帳沒有紀錄({a.replay or '最近一份'})· {LOCAL_REL}/{STATE_DB}")
            return 2
        if a.json:
            print(json.dumps(m, ensure_ascii=False, indent=2))
        else:
            render(m)
        return RC[m["lamp"]]
    try:
        cfg = _config(VIA, a.config)
        day = date.fromisoformat(a.day) if a.day else date.today()
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(f"[每日交接] 參數 / 設定檔錯:{exc}")
        return 1
    log, close_log, how_log = _open_log(VIA, day)
    try:
        m = build_daily(VIA, day, ledger=a.ledger or cfg.get("ledger") or None,
                        data_dirs=[*cfg.get("data_dirs", []), *a.data], flagged_dirs=[*cfg.get("flagged_dirs", []), *a.flagged],
                        tasks=[*a.tasks, *cfg.get("next", [])], run_audit=not a.no_audit)
        for k, _ in POINTS:
            log("INFO", f"{k} {m['points'][k]['lamp']} {m['points'][k]['summary']}")
        log("DEBUG", json.dumps(m, ensure_ascii=False, sort_keys=True))
        errs, how = validate_manifest(m)
        written = None
        if errs:
            log("WARNING", f"清單契約不過({how}),不寫:" + " | ".join(errs))
            m["points"]["manifest"]["lamp"] = m["lamps"]["manifest"] = "RED"
            m["points"]["manifest"]["summary"] = f"契約不過({how}),不寫 · {len(errs)} 條"
            m["lamp"] = "RED"
        elif not a.dry_run:
            written = write_daily(VIA, m)
            log("INFO", f"寫入 {written['manifest']} · sha256 {m['manifest_sha256']} · log {how_log}")
        if a.json:
            print(json.dumps(m, ensure_ascii=False, indent=2))
        else:
            render(m, written, errs)
        return 1 if errs else RC[m["lamp"]]
    finally:
        close_log()


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ["daily"] or args in (["--selftest"], ["--selftest-tail"]):
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print("[DENY] VCGC entry required")
            return 2
        if args[:1] == ["daily"]:
            return daily_main(args[1:])
        return selftest_tail() if args == ["--selftest-tail"] else selftest()
    return PRIOR.main(argv)


def selftest():
    rc = PRIOR.selftest()
    return 0 if rc == 0 and selftest_tail() == 0 else 1


def _sh(cwd, *args, when=None):
    env = {**os.environ, "GIT_AUTHOR_NAME": "via", "GIT_AUTHOR_EMAIL": "via@example.invalid",
           "GIT_COMMITTER_NAME": "via", "GIT_COMMITTER_EMAIL": "via@example.invalid"}
    if when:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = when
    subprocess.run(["git", "-c", "commit.gpgsign=false", *args], cwd=str(cwd), env=env, check=True, capture_output=True)


def _selftest_body(chk):
    import socket
    today = date.today()
    yday = today - timedelta(days=1)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        via = root / "VIA"
        reg = via / "supportive modules" / "registry"
        reg.mkdir(parents=True)
        _sh(root, "init", "-q")
        _sh(root, "symbolic-ref", "HEAD", "refs/heads/main")
        (root / ".gitignore").write_text("VIA/VIA_Reports/handover/\nVIA/VIA_Reports/vcgc/TEST_latest.json\n", encoding="utf-8")
        (reg / "CGC_MDL999_Demo_v0100.py").write_text("x = 1\n", encoding="utf-8")
        (reg / "CGC_MDL998_Gone_v0100.py").write_text("y = 1\n", encoding="utf-8")
        _sh(root, "add", "-A")
        _sh(root, "commit", "-q", "-m", "base", when=f"{yday.isoformat()}T12:00:00")
        (reg / "CGC_MDL999_Demo_v0101.py").write_text("x = 2\n", encoding="utf-8")       # 當日新版
        (reg / "CGC_MDL999_Demo_v0100.py").write_text("x = 1  # 改\n", encoding="utf-8")  # 就地改已存在的版號檔
        events = via / "VIA_Reports" / "vcgc" / "events"
        events.mkdir(parents=True)
        ev = [{"verb": "token", "outcome": "OK", "rc": 0, "secs": 1.0}] * 3 + [
            {"verb": "handoff", "outcome": "FINDING", "rc": 2, "secs": 2.0},
            {"verb": "run", "target": "X", "outcome": "FAIL", "rc": 1, "secs": 0.5, "error": "boom"}]
        (events / f"EVENTS_{today:%Y%m%d}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in ev), encoding="utf-8")
        lock = [{"table": "t1", "header_sha": "aaaa", "data_sha": "d1", "rows": 3, "at": f"{yday}T01:00:00+00:00"},
                {"table": "t2", "header_sha": "bbbb", "data_sha": "d2", "rows": 1, "at": f"{today}T01:00:00+00:00"},
                {"table": "t1", "header_sha": "cccc", "data_sha": "d3", "rows": 4, "at": f"{today}T02:00:00+00:00"}]
        (reg / "VIA_DataFrame_Lock_Ledger_v0100.jsonl").write_text("".join(json.dumps(r) + "\n" for r in lock), encoding="utf-8")
        out = root / "out" / today.isoformat()
        out.mkdir(parents=True)
        blob = b"PAR1-demo-bytes"
        (out / "a.parquet").write_bytes(blob)
        (via / "stale.sdd_bak").write_text("old", encoding="utf-8")
        _sh(root, "add", "-A")
        _sh(root, "commit", "-q", "-m", "today", when=f"{today.isoformat()}T12:00:00")
        head = _git(root, "rev-parse", "HEAD") or ""
        (via / "VIA_Reports" / "vcgc" / "TEST_latest.json").write_text(json.dumps(
            {"lamp": "GREEN", "head": head[:12], "mode": "quick", "at": "2026-10-02T00:00:00", "rows": [],
             "counts": {"GREEN": 7, "YELLOW": 0, "RED": 0}}), encoding="utf-8")
        report = {"lamp": "GREEN", "closeout_lamp": "YELLOW", "summary": {"pending": 2}, "rows": [], "pending": [
            {"id": "REQ1:a", "state": "PENDING", "owner": "AI", "next": "做 a", "reason": "r"},
            {"id": "REQ2:b", "state": "BLOCKED", "owner": "操作員", "next": "做 b", "reason": "r"}]}
        calls = []
        real_connect = socket.socket.connect

        def deny(self, *a, **k):
            calls.append(a)
            raise OSError("selftest: 不准連網")
        socket.socket.connect = deny
        try:
            m = build_daily(via, today, root=root, data_dirs=["out/{day}"], tasks=["修表格跨頁縫合"], report=report)
        finally:
            socket.socket.connect = real_connect
        P = m["points"]
        g = P["git"]["data"]
        chk("① git:分支 main · SHA-16 = HEAD · 當日 1 提交 · 乾淨 = 綠",
            (g["sha16"], g["branch"], g["commits_today"], P["git"]["lamp"]) == (head[:16], "main", 1, "GREEN"), P["git"]["summary"])
        L = P["ledger"]["data"]
        chk("② ledger:5 次 · 成功 3 · 黃 1 · 紅 1 · 成功率 0.6 = 黃",
            (L["total"], L["ok"], L["warn"], L["fail"], L["success_rate"], P["ledger"]["lamp"]) == (5, 3, 1, 1, 0.6, "YELLOW"),
            P["ledger"]["summary"])
        bad = Path(tmp) / "universal_ledger.jsonl"
        bad.write_text('{"step": "x", "status": "success", "rc": 0}\nnot-json\n', encoding="utf-8")
        pt, _ = point_ledger(via, today, str(bad))
        chk("② ledger:--ledger 讀別本帳(status=success 算成功)· 壞行 = 紅",
            pt["lamp"] == "RED" and pt["data"]["bad_lines"] == 1 and pt["data"]["ok"] == 1, pt["summary"])
        D = P["data"]["data"]
        f0 = (D["files"] or [{}])[0]
        chk("③ data:檔 SHA-256 = hashlib · 鎖帳 2 表 · 當日 2 筆 · 指紋在 = 綠",
            f0.get("sha256") == hashlib.sha256(blob).hexdigest() and f0.get("path") == f"out/{today}/a.parquet"
            and len(D["tables"]) == 2 and D["tables_today"] == 2 and bool(D["digest"]) and P["data"]["lamp"] == "GREEN",
            P["data"]["summary"])
        Mo = P["modules"]["data"]
        chk("④ modules:CGC_MDL999_Demo 新 v0101 · 就地改 v0100 = 黃",
            Mo["families"].get("CGC_MDL999_Demo", {}).get("new") == ["v0101"]
            and Mo["inplace_engines"] == {"CGC_MDL999_Demo": ["v0100"]} and P["modules"]["lamp"] == "YELLOW",
            P["modules"]["summary"])
        fam = classify_changes([("A", "r/CGC_MDL1_A_v0102.py", "c1"), ("M", "r/CGC_MDL1_A_v0102.py", "c2"),
                                ("D", "r/CGC_MDL2_B_v0100.py", "c3"),
                                ("D", "r/CGC_MDL3_C_v0101.py", "c4"), ("A", "r/CGC_MDL3_C_v0102.py", "c4"),
                                ("M", "r/VIA_Book_v0100.json", "c5")])
        chk("④ 純函式:當日新增再改不算就地改 · 同提交同家族新增的刪 = 改號 · 單純刪 = 刪 · JSON 冊照記",
            fam["CGC_MDL1_A"] == {"new": ["v0102"], "inplace": [], "renumbered": [], "deleted": [], "kind": "py"}
            and fam["CGC_MDL2_B"]["deleted"] == ["v0100"]
            and (fam["CGC_MDL3_C"]["renumbered"], fam["CGC_MDL3_C"]["deleted"], fam["CGC_MDL3_C"]["new"]) == (["v0101"], [], ["v0102"])
            and fam["VIA_Book"]["kind"] == "json", fam)
        S = P["schema"]
        chk("⑤ schema:t1 header aaaa → cccc 漂移 = 黃",
            [d["table"] for d in S["data"]["drift"]] == ["t1"] and S["lamp"] == "YELLOW", S["summary"])
        stale = point_tests(via, "f" * 40)
        chk("⑥ tests:報告 head = HEAD → 綠;≠ HEAD → 黃(過期)",
            P["tests"]["lamp"] == "GREEN" and stale["lamp"] == "YELLOW" and stale["data"]["stale"] is True, stale["summary"])
        F = P["flagged"]
        chk("⑦ flagged:非 OK 事件 2 + BLOCKED 1 · 黃", F["data"]["counts"] == {"ledger": 2, "pending": 1}
            and F["lamp"] == "YELLOW", F["summary"])
        C = P["cache"]["data"]
        chk("⑧ cache:sdd_bak 1 · 只印 -WhatIf / -print 指令 · 檔還在 · 黃",
            C["classes"]["sdd_bak"]["count"] == 1 and C["commands"]
            and all("-WhatIf" in c["pwsh"] and "-print" in c["bash"] for c in C["commands"])
            and (via / "stale.sdd_bak").exists() and P["cache"]["lamp"] == "YELLOW", P["cache"]["summary"])
        T = P["next"]["data"]["tasks"]
        chk("⑨ next:T01 手寫優先 · T02 / T03 照交接待辦序",
            [t["id"] for t in T] == ["T01", "T02", "T03"] and T[0]["source"] == "operator"
            and T[1].get("ref") == "REQ1:a" and T[2].get("ref") == "REQ2:b", [t.get("ref") for t in T])
        chk("⑩ 整張燈 = 最差(黃)· 十點照序 · 零網路", m["lamp"] == "YELLOW" and list(m["lamps"]) == [k for k, _ in POINTS]
            and not calls, m["lamps"])
        errs, how = validate_manifest(m)
        broken = json.loads(json.dumps(m))
        broken["points"]["git"]["data"].pop("sha16")
        extra = json.loads(json.dumps(m))
        extra["surprise"] = 1
        tampered = json.loads(json.dumps(m))
        tampered["points"]["ledger"]["summary"] = "改過"
        e_bad, e_extra, e_tamp = (validate_manifest(x)[0] for x in (broken, extra, tampered))
        chk("⑩ 契約(標準庫):好清單過 · 缺 Git SHA-16 攔 · 多欄攔 · 被改 = 自身雜湊不符",
            not errs and how == "stdlib" and any("sha16" in e for e in e_bad) and bool(e_extra)
            and any("manifest_sha256" in e for e in e_tamp), (errs + e_bad + e_extra + e_tamp)[:4])
        os.environ.pop("VIA_DAILY_NO_OPTIONAL", None)
        try:
            if _lib("Pydantic") is not None:
                verdicts = [bool(validate_manifest(x)[0]) for x in (m, broken, extra, tampered)]
                chk("⑩ pydantic 與標準庫同判(好 過 · 缺 SHA / 多欄 / 被改 攔)", verdicts == [False, True, True, True],
                    validate_manifest(m)[1])
        finally:
            os.environ["VIA_DAILY_NO_OPTIONAL"] = "1"
        written = write_daily(via, m)
        errs2, _, m2 = verify(written["manifest"])
        chk("⑩ 寫入:清單讀回 = 原清單 · 驗過", not errs2 and m2 == m, errs2[:2])
        m_b = build_daily(via, today, root=root, report=report)
        write_daily(via, m_b)
        lines = (via / DAILY_REL / LEDGER).read_text(encoding="utf-8").splitlines()
        chk("⑩ 只增帳:兩次 = 兩行 · 第一行沒動 · 清單不算未提交",
            len(lines) == 2 and json.loads(lines[0])["manifest_sha16"] == m["manifest_sha256"][:16]
            and m_b["points"]["git"]["lamp"] == "GREEN", m_b["points"]["git"]["summary"])
        blocked = False
        with contextlib.closing(sqlite3.connect(str(written["state_db"]))) as con:
            try:
                con.execute("UPDATE runs SET lamp = 'GREEN'")
            except sqlite3.DatabaseError:
                blocked = True
            n = con.execute("SELECT count(*) FROM runs").fetchone()[0]
        chk("⑩ 本機 sqlite 帳:UPDATE 被觸發器擋 · 2 筆 · 重播 = 第二份", blocked and n == 2
            and replay(via, today.isoformat()) == m_b)
        ts = {r["lib"]: r["state"] for r in m["toolset"]}
        chk("十個函式庫:7 選用照實記 fallback(VIA_DAILY_NO_OPTIONAL=1)· 3 標準庫",
            all(ts[k] == "fallback" for k in OPTIONAL) and list(ts.values()).count("stdlib") == 3, ts)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            render(m, written)
        txt = buf.getvalue()
        chk("面板:十點各一行 · [FAIL] 照印 · T01 · 清理只印 · 判決行",
            all(t in txt for _, t in POINTS) and "[FAIL]" in txt and "T01" in txt and "[清理·只印]" in txt
            and '"daily": "v0104"' in txt)
        (reg / "CGC_MDL998_Gone_v0100.py").unlink()
        red = point_modules(root, "VIA", today, True)
        chk("④ 刪既有版號引擎 = 紅(只增不減)", red["lamp"] == "RED"
            and red["data"]["deleted_engines"] == {"CGC_MDL998_Gone": ["v0100"]}, red["summary"])
        cfg = Path(tmp) / "handover.toml"
        cfg.write_text('data_dirs = ["out/{day}"]\nnext = "T: 一條"\n', encoding="utf-8")
        got = _config(via, str(cfg))
        cfg.write_text('surprise = 1\n', encoding="utf-8")
        try:
            _config(via, str(cfg))
            refused = False
        except ValueError:
            refused = True
        chk("設定檔 tomllib:字串轉清單 · 不認得的鍵拒收", got == {"data_dirs": ["out/{day}"], "flagged_dirs": [],
                                                       "next": ["T: 一條"]} and refused, got)


def selftest_tail():
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:200]) if note and not cond else ''}")
    saved = os.environ.get("VIA_DAILY_NO_OPTIONAL")
    os.environ["VIA_DAILY_NO_OPTIONAL"] = "1"       # 自測走標準庫退路,結果不隨機器上裝了什麼而變
    try:
        _selftest_body(chk)
    except Exception as exc:  # 自測本身炸 = 紅,照印原因
        chk("自測執行", False, f"{type(exc).__name__}: {exc}")
    finally:
        if saved is None:
            os.environ.pop("VIA_DAILY_NO_OPTIONAL", None)
        else:
            os.environ["VIA_DAILY_NO_OPTIONAL"] = saved
    gate = os.environ.pop("VIA_FROM_VCGC", None)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            rc = main(["daily", "--dry-run"])
    finally:
        if gate is not None:
            os.environ["VIA_FROM_VCGC"] = gate
    chk("只收 VCGC 呼叫:沒帶 VIA_FROM_VCGC → DENY rc 2", rc == 2)
    text = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(text)
    top = ({a.name.split(".")[0] for n in tree.body if isinstance(n, ast.Import) for a in n.names}
           | {n.module.split(".")[0] for n in tree.body if isinstance(n, ast.ImportFrom) and n.module})
    chk("檔頭:加速器橋 · 網路橋在 · 不碰 TA-Lib · 頂層只 import 標準庫(選用庫全探針)",
        "VIA:ACCEL-BRIDGE" in text and "VIA:NET-BRIDGE" in text and not re.search(r"^\s*(import|from)\s+talib", text, re.M)
        and not (top & {v[0] for v in OPTIONAL.values()}), sorted(top))
    passed = bool(ok) and all(ok)
    print(f"[交接 {VERSION}] 本版 {sum(ok)}/{len(ok)} · 每日交接十點 · {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
