#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0151 — 薄尾:VDF 自己的資料庫 · 檢查缺什麼 + 搬到 VDF 自己的資料家(操作員令 2026-10-10:
「將最新資料傳入 …\\via_database\\vdf_database · 檢視資料庫查看缺啥」;VDF 獨立 = 自己的資料夾、自己的檢查,不載入 VCGC 程式)。
  db check [--home 夾] [--json]   逐本庫唯讀開(duckdb read_only),對表冊尾版 VIA_DB_Table_SSOT_v*.json(只讀資料冊):
                                  缺庫 · 缺表 · 空表 / 列數不足(< min_rows)= RED;列數比上次少 10%+ · 過舊(日頻 > 10 天 · 月頻 > 62 天)= YELLOW;
                                  冊上沒列的表 = INFO。哨兵列(1900-…)不算最新日。產出 VIA_Reports/vdf/DB_CHECK_latest.{html,csv,json}
                                  家:--home > env VIA_VDF_DB_HOME > 倉內 output_hub(接點照實解到真址)
  db move --to 夾 [--apply]       VDF 資料搬家(複製 → 驗證 → 切接點):乾跑只列計畫;--apply 複製到 <夾>\\output_hub(同檔跳過、
                                  同名不同內容 = 新家留著舊檔另存 _from_old_<sha8>),兩邊 db check 列數逐表一致 + 還原點 ≤ 24h 才切倉內接點;
                                  舊家資料一個位元都不刪(它本身就是還原點);帳 registry/VDF_DataHome_Ledger.jsonl。
其餘動詞照前版鏈。只收 VIA_FROM_VCGC=YES。不抓網、不代設同意閘、不碰 TA-Lib。
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

# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====

import datetime
import hashlib
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
REG = VIA / "supportive modules" / "registry"
_STEM = "VDF_SystemManager"
TAG = "v0151"
DATE_COLS = ("date", "trade_date", "dt", "asof_date", "as_of", "holding_date", "ym", "period", "published", "ts")
STALE_DAYS = {"daily": 10, "monthly": 62, "other": 120}
RESTORE_MAX_H = float(os.environ.get("VIA_RESTORE_MAX_H") or 24)


def _vnum_v0151(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0151(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0151(p) < _vnum_v0151(__file__)), key=_vnum_v0151)
PRIOR = _load_v0151(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _out() -> Path:
    return PRIOR._out()


def db_home(explicit: str | None = None) -> Path:
    """VDF 資料家:--home > env VIA_VDF_DB_HOME > 倉內 output_hub(接點照實解到真址)。"""
    if explicit:
        return Path(explicit)
    if os.environ.get("VIA_VDF_DB_HOME"):
        return Path(os.environ["VIA_VDF_DB_HOME"])
    return Path(os.path.realpath(HERE / "output_hub"))


def table_book(reg: Path | None = None) -> tuple:
    """表冊尾版(VIA_DB_Table_SSOT_v*.json;只讀資料冊,不載入 VCGC 程式)。"""
    reg = reg or REG
    hits = sorted(reg.glob("VIA_DB_Table_SSOT_v*.json"), key=_vnum_v0151)
    if not hits:
        return None, []
    return hits[-1], json.loads(hits[-1].read_text(encoding="utf-8")).get("tables") or []


def _find_db(home: Path, name: str) -> tuple:
    hits = [p for p in home.rglob(name) if "_repo_" not in p.name and "stash" not in str(p).lower() and "selftest" not in str(p).lower()]
    hits.sort(key=lambda p: (("mega" in p.parts) or ("active_tw_etf" in str(p)), p.stat().st_size), reverse=True)
    return (hits[0] if hits else None), len(hits)


def _cadence(col: str) -> str:
    return "monthly" if col in ("ym", "period") else ("daily" if col in ("date", "trade_date", "dt") else "other")


def _as_date(v):
    s = str(v or "").strip()
    m = re.match(r"^(\d{4})-?(\d{2})(?:-?(\d{2}))?", s)
    if not m:
        return None
    try:
        return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3) or 1))
    except ValueError:
        return None


def db_check(home: str | None = None, reg: Path | None = None, today: datetime.date | None = None, write: bool = True) -> dict:
    today = today or datetime.date.today()
    h = db_home(home)
    src, book = table_book(reg)
    try:
        import duckdb
    except ImportError:
        return {"verb": "db check", "home": str(h), "lamp": "NODATA", "why": "duckdb 不在本境(不代裝)", "rows": [], "summary": {}}
    rows, seen_tables = [], {}
    by_db = {}
    for t in book:
        by_db.setdefault(t["db"], []).append(t)
    for dbname, tables in sorted(by_db.items()):
        path, n_cand = _find_db(h, dbname)
        if path is None:
            for t in tables:
                rows.append({"庫": dbname, "表": t["table"], "狀態": "缺庫", "燈": "RED", "列數": None, "最少": t.get("min_rows", 1), "上次列數": t.get("rows_seen"),
                             "最新日": None, "落後天": None, "寫入者": " ".join(t.get("writers") or []), "檔": ""})
            continue
        try:
            con = duckdb.connect(str(path), read_only=True)
        except Exception as exc:                       # 庫鎖住 / 壞檔 = 照實紅
            for t in tables:
                rows.append({"庫": dbname, "表": t["table"], "狀態": "庫打不開:%s" % type(exc).__name__, "燈": "RED", "列數": None, "最少": t.get("min_rows", 1),
                             "上次列數": t.get("rows_seen"), "最新日": None, "落後天": None, "寫入者": " ".join(t.get("writers") or []), "檔": str(path)})
            continue
        have = {r[0]: r[1] for r in con.execute("select table_name, table_schema from information_schema.tables").fetchall()}
        seen_tables[dbname] = set(have)
        for t in tables:
            tn = t["table"]
            base = {"庫": dbname, "表": tn, "最少": t.get("min_rows", 1), "上次列數": t.get("rows_seen"), "寫入者": " ".join(t.get("writers") or []), "檔": str(path)}
            if tn not in have:
                rows.append(dict(base, 狀態="缺表", 燈="RED", 列數=None, 最新日=None, 落後天=None))
                continue
            q = '"%s"."%s"' % (have[tn], tn)
            n = con.execute("select count(*) from %s" % q).fetchone()[0]
            cols = [c[0] for c in con.execute("select column_name from information_schema.columns where table_name=? and table_schema=?", [tn, have[tn]]).fetchall()]
            dcol = next((c for c in DATE_COLS if c in cols), None)
            hi = None
            if dcol and n:
                try:
                    hi = _as_date(con.execute("select max(cast(%s as varchar)) from %s where cast(%s as varchar) not like '1900%%'" % (dcol, q, dcol)).fetchone()[0])
                except Exception:              # 日期欄型別怪 = 不判新鮮度(照列)
                    hi = None
            lag = (today - hi).days if hi else None
            st, lamp = "OK", "GREEN"
            if n < int(t.get("min_rows") or 1):
                st, lamp = ("空表" if n == 0 else "列數不足"), "RED"
            elif t.get("rows_seen") and n < 0.9 * int(t["rows_seen"]):
                st, lamp = "列數比上次少", "YELLOW"
            elif lag is not None and lag > STALE_DAYS[_cadence(dcol)]:
                st, lamp = "過舊", "YELLOW"
            rows.append(dict(base, 狀態=st, 燈=lamp, 列數=n, 最新日=str(hi) if hi else None, 落後天=lag))
        for extra in sorted(set(have) - {t["table"] for t in tables}):
            rows.append({"庫": dbname, "表": extra, "狀態": "冊上沒列", "燈": "INFO", "列數": None, "最少": None, "上次列數": None, "最新日": None, "落後天": None, "寫入者": "", "檔": str(path)})
        con.close()
    cnt = {k: sum(1 for r in rows if r["燈"] == k) for k in ("RED", "YELLOW", "GREEN", "INFO")}
    o = {"verb": "db check", "tag": "%s %s" % (_STEM, TAG), "ts": datetime.datetime.now().isoformat(timespec="seconds"), "home": str(h),
         "book": src.name if src else None, "rows": rows, "summary": cnt,
         "lamp": "RED" if cnt["RED"] else ("YELLOW" if cnt["YELLOW"] else ("GREEN" if rows else "NODATA"))}
    if write:
        o["files"] = _write_db(o)
    return o


def _write_db(o: dict) -> dict:
    out = _out()
    out.mkdir(parents=True, exist_ok=True)
    f = {"json": out / "DB_CHECK_latest.json", "csv": out / "DB_CHECK_latest.csv", "html": out / "DB_CHECK_latest.html"}
    f["json"].write_text(json.dumps(o, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    cols = ["庫", "表", "狀態", "燈", "列數", "最少", "上次列數", "最新日", "落後天", "寫入者", "檔"]
    try:
        import pandas as pd
        df = pd.DataFrame(o["rows"], columns=cols)
        df.to_csv(f["csv"], index=False, encoding="utf-8-sig")
        table = df.to_html(index=False, escape=True, border=0, classes="m")
    except ImportError:
        import csv
        with f["csv"].open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(o["rows"])
        table = "<table class='m'>%s</table>" % "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % html.escape(str(r.get(c))) for c in cols) for r in o["rows"])
    for w_, c_ in (("RED", "#dc2626"), ("YELLOW", "#b45309"), ("GREEN", "#16a34a"), ("INFO", "#6b7280")):
        table = table.replace("<td>%s</td>" % w_, "<td style='color:%s;font-weight:600'>%s</td>" % (c_, w_))
    page = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>VDF 資料庫檢查</title>"
            "<style>body{font:13px system-ui;margin:16px;background:#fafafa}table.m{border-collapse:collapse;font-size:12px;background:#fff}"
            "table.m td,table.m th{padding:3px 6px;border-bottom:1px solid #eee;text-align:left}th{background:#f1f5f9}</style>"
            "<h1>VDF 資料庫檢查 · 缺什麼</h1><p>%s · 家 %s · 冊 %s · %s</p>%s"
            % (html.escape(o["ts"]), html.escape(o["home"]), html.escape(str(o["book"])), html.escape(json.dumps(o["summary"], ensure_ascii=False)), table))
    f["html"].write_text(page, encoding="utf-8")
    return {k: str(v) for k, v in f.items()}


def _print_db(o: dict) -> None:
    if o.get("why"):
        print("  [%s] %s" % (o["lamp"], o["why"]))
    for r in o["rows"]:
        if r["燈"] in ("RED", "YELLOW"):
            print("  [%s] %-26s %-28s %s · 列 %s(最少 %s · 上次 %s)· 最新 %s%s" % (r["燈"], r["庫"], r["表"], r["狀態"], r["列數"], r["最少"], r["上次列數"], r["最新日"],
                                                                         (" · 寫入者 " + r["寫入者"]) if r["寫入者"] else ""))
    print("[計] VDF db check · 家 %s · 冊 %s · %s · %s%s" % (o["home"], o.get("book"), o["summary"], o["lamp"], (" · " + o["files"]["html"]) if o.get("files") else ""))


# ---------- db move:複製 → 驗證 → 切接點(舊家不刪) ----------
def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _restore_ok(reg: Path, now: datetime.datetime | None = None) -> tuple:
    led = reg / "VIA_RestorePoint_Ledger_v0100.jsonl"
    last = None
    if led.is_file():
        for line in led.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                row = {}
            last = row if row.get("ts") else last
    if not last:
        return False, "還原點帳沒有紀錄(先跑 CGC_MDL274_HealthMatrix restorepoint)"
    try:
        age = ((now or datetime.datetime.now()) - datetime.datetime.fromisoformat(str(last["ts"])[:19])).total_seconds() / 3600
    except ValueError:
        return False, "還原點時間讀不懂"
    age = 0.0 if -14 <= age < 0 else age              # 帳本是工作站本地時間,時區差視為剛建
    return 0 <= age <= RESTORE_MAX_H, "最近還原點 %s(%.1f 小時前)" % (last.get("stamp"), age)


def _is_link(p: Path) -> bool:
    if p.is_symlink():
        return True
    try:
        return os.path.realpath(p) != str(p.resolve(strict=False)) or (os.name == "nt" and bool(os.readlink(p)))
    except (OSError, ValueError):
        return False


def db_move(to: str, apply: bool = False, reg: Path | None = None, link_point: Path | None = None, ledger_dir: Path | None = None) -> dict:
    reg = reg or REG
    ledger_dir = ledger_dir or (HERE / "registry")
    point = link_point or (HERE / "output_hub")
    src = Path(os.path.realpath(point))
    dst = Path(to) / "output_hub"
    o = {"verb": "db move", "apply": apply, "point": str(point), "src": str(src), "dst": str(dst), "copy": 0, "skip": 0, "conflict": 0, "bytes": 0, "rows": []}
    if not src.is_dir():
        o.update(lamp="RED", why="來源不在:%s" % src)
        return o
    if src.resolve() == dst.resolve():
        o.update(lamp="GREEN", why="已在新家(接點已指 %s)" % dst)
        return o
    for p in sorted(x for x in src.rglob("*") if x.is_file()):
        rel = p.relative_to(src)
        q = dst / rel
        if q.exists():
            if q.stat().st_size == p.stat().st_size and _sha(q) == _sha(p):
                o["skip"] += 1
                continue
            alt = q.with_name("%s_from_old_%s%s" % (q.stem, _sha(p)[:8], q.suffix))
            o["conflict"] += 1
            o["rows"].append({"rel": str(rel), "act": "CONFLICT", "to": str(alt.relative_to(dst)), "why": "新家同名不同內容:新家留著,舊檔另存"})
            if apply:
                alt.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, alt)
            continue
        o["copy"] += 1
        o["bytes"] += p.stat().st_size
        o["rows"].append({"rel": str(rel), "act": "COPY"})
        if apply:
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, q)
    if not apply:
        o.update(lamp="YELLOW", why="乾跑:複製 %d 檔(%.1f MB)· 同檔跳過 %d · 衝突另存 %d;加 --apply 才動" % (o["copy"], o["bytes"] / 1e6, o["skip"], o["conflict"]))
        return o
    ok, why = _restore_ok(reg)
    o["restore"] = why
    a = db_check(str(src), reg, write=False)
    b = db_check(str(dst), reg, write=False)
    ra = {(r["庫"], r["表"]): r["列數"] for r in a["rows"] if r["列數"] is not None}
    rb = {(r["庫"], r["表"]): r["列數"] for r in b["rows"] if r["列數"] is not None}
    diff = sorted("%s::%s %s→%s" % (k[0], k[1], ra[k], rb.get(k)) for k in ra if rb.get(k) != ra[k])
    o["verify"] = {"tables": len(ra), "diff": diff[:20]}
    if diff:
        o.update(lamp="RED", why="驗證不過(新家列數不同 %d 表)→ 接點不切,舊家照用" % len(diff))
        return o
    if not ok:
        o.update(lamp="YELLOW", why="資料已複製且驗證通過,但%s → 接點不切(先建還原點再重跑)" % why)
        return o
    if not _is_link(point):
        o.update(lamp="YELLOW", why="倉內 output_hub 是實體目錄(不是接點)→ 不刪不切;資料已在新家,接點請你手動處理")
        return o
    try:
        if os.name == "nt":
            os.rmdir(point)                            # 只拆接點本身,不碰舊家資料
            r = subprocess.run(["cmd", "/c", "mklink", "/J", str(point), str(dst)], capture_output=True, text=True)
            okl = r.returncode == 0
        else:
            point.unlink()
            os.symlink(dst, point, target_is_directory=True)
            okl = True
    except OSError as exc:
        o.update(lamp="RED", why="切接點失敗 %s(舊家資料沒動)" % type(exc).__name__)
        return o
    o.update(lamp="GREEN" if okl and Path(os.path.realpath(point)).resolve() == dst.resolve() else "RED",
             why="接點已切:%s → %s(舊家 %s 原樣保留)" % (point, dst, src))
    try:
        with (ledger_dir / "VDF_DataHome_Ledger.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "from": str(src), "to": str(dst), "copied": o["copy"],
                                 "conflict": o["conflict"], "tables_verified": len(ra), "lamp": o["lamp"]}, ensure_ascii=False) + "\n")
    except OSError as exc:
        o["ledger"] = "寫不出 %s" % type(exc).__name__
    return o


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["db"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print("[VDF] 拒絕。只能經 VDF 啟動器 / via-vcgc(VIA_FROM_VCGC=YES)。")
            return 2

        def opt(flag):
            return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else None
        sub = args[1] if len(args) > 1 else "check"
        if sub == "check":
            o = db_check(opt("--home"))
            print(json.dumps({k: v for k, v in o.items() if k != "rows"}, ensure_ascii=False, indent=1)) if "--json" in args else _print_db(o)
            return {"GREEN": 0, "YELLOW": 0, "NODATA": 2}.get(o["lamp"], 1)
        if sub == "move":
            if not opt("--to"):
                print("  用法:db move --to <資料家,例 C:\\…\\via_database\\vdf_database> [--apply]")
                return 2
            o = db_move(opt("--to"), apply="--apply" in args)
            for r in o["rows"][:15]:
                if r["act"] == "CONFLICT":
                    print("  [衝突] %s → %s(%s)" % (r["rel"], r["to"], r["why"]))
            print("[計] VDF db move · %s → %s · %s · %s" % (o["src"], o["dst"], o["lamp"], o.get("why", "")))
            return 0 if o["lamp"] in ("GREEN", "YELLOW") else 1
        print("[拒跑] db 子動詞:check [--home 夾] · move --to 夾 [--apply]")
        return 2
    return PRIOR.main(args)


PRIOR.VERBS_ALL = tuple(PRIOR.VERBS_ALL) + ("db",)          # 未知動詞清單也列 db
PRIOR.CHAIN_NAMES_VDF = list(PRIOR.CHAIN_NAMES_VDF) + ["db_check", "db_move"]


def selftest() -> int:
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        p, f = (p + 1, f) if cond else (p, f + 1)
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · %s" % (note,)) if note != "" else ""))

    try:
        import duckdb
    except ImportError:
        duckdb = None
    keep = {k: os.environ.get(k) for k in ("VIA_VDF_HEALTH_OUT", "VIA_FROM_VCGC")}
    td = Path(tempfile.mkdtemp(prefix="vdfsm151-"))
    os.environ.update({"VIA_VDF_HEALTH_OUT": str(td / "out"), "VIA_FROM_VCGC": "YES"})
    try:
        reg = td / "reg"
        reg.mkdir()
        (reg / "VIA_DB_Table_SSOT_v0100.json").write_text(json.dumps({"tables": [
            {"db": "a.duckdb", "table": "px", "min_rows": 1, "rows_seen": 3}, {"db": "a.duckdb", "table": "gone", "min_rows": 1},
            {"db": "a.duckdb", "table": "rev", "min_rows": 5}, {"db": "a.duckdb", "table": "old", "min_rows": 1},
            {"db": "nodb.duckdb", "table": "x", "min_rows": 1}]}), encoding="utf-8")
        home = td / "home" / "output_hub"
        (home / "mega").mkdir(parents=True)
        if duckdb:
            c = duckdb.connect(str(home / "mega" / "a.duckdb"))
            c.execute("create table px(ticker varchar, date varchar)")
            c.execute("insert into px values ('_NOOP_','1900-01-01'),('2330','2026-10-08'),('2317','2026-10-08')")
            c.execute("create table rev(ym varchar)")
            c.execute("insert into rev values ('202609')")
            c.execute("create table old(date varchar)")
            c.execute("insert into old values ('2026-06-01')")
            c.execute("create table extra(x int)")
            c.close()
        o = db_check(str(home), reg, today=datetime.date(2026, 10, 10))
        by = {(r["庫"], r["表"]): r for r in o["rows"]}
        chk("① db check:px OK(哨兵列不算最新日)· gone 缺表 · rev 列數不足 · old 過舊 · nodb 缺庫 · extra 冊上沒列 · 寫出 html/csv/json",
            duckdb is not None and by[("a.duckdb", "px")]["燈"] == "GREEN" and by[("a.duckdb", "px")]["最新日"] == "2026-10-08"
            and by[("a.duckdb", "gone")]["狀態"] == "缺表" and by[("a.duckdb", "rev")]["狀態"] == "列數不足" and by[("a.duckdb", "old")]["狀態"] == "過舊"
            and by[("nodb.duckdb", "x")]["狀態"] == "缺庫" and by[("a.duckdb", "extra")]["燈"] == "INFO" and o["lamp"] == "RED"
            and all(Path(x).is_file() for x in o["files"].values()), o["summary"])
        point = td / "repo" / "output_hub"
        point.parent.mkdir()
        os.symlink(home, point, target_is_directory=True)
        new = td / "vdf_database"
        d0 = db_move(str(new), apply=False, reg=reg, link_point=point)
        chk("② db move 乾跑:列複製計畫 · 一檔都不寫", d0["copy"] >= 1 and not (new / "output_hub").exists() and d0["lamp"] == "YELLOW")
        d1 = db_move(str(new), apply=True, reg=reg, link_point=point, ledger_dir=reg)
        chk("③ --apply 沒還原點:資料複製 + 驗證列數一致,但接點不切 · 舊家原樣", (new / "output_hub" / "mega" / "a.duckdb").is_file()
            and Path(os.path.realpath(point)) == home.resolve() and "還原點" in d1["why"] and not d1["verify"]["diff"] and (home / "mega" / "a.duckdb").is_file(), d1["why"])
        (reg / "VIA_RestorePoint_Ledger_v0100.jsonl").write_text(json.dumps({"stamp": "x", "ts": datetime.datetime.now().isoformat(timespec="seconds")}) + "\n", encoding="utf-8")
        d2 = db_move(str(new), apply=True, reg=reg, link_point=point, ledger_dir=reg)
        chk("④ 有還原點 + 驗證過:接點切到新家 · 舊家資料原樣保留 · 同檔跳過不重複", d2["lamp"] == "GREEN"
            and Path(os.path.realpath(point)).resolve() == (new / "output_hub").resolve() and (home / "mega" / "a.duckdb").is_file() and d2["skip"] >= 1
            and (reg / "VDF_DataHome_Ledger.jsonl").is_file(), d2["why"])
        d3 = db_move(str(new), apply=True, reg=reg, link_point=point, ledger_dir=reg)
        chk("⑤ 再跑:已在新家 = GREEN 不動", d3["lamp"] == "GREEN" and "已在新家" in d3["why"])
        chk("⑥ 未知動詞清單含 db · db 子動詞錯 = rc2", "db" in PRIOR.VERBS_ALL and main(["db", "zz"]) == 2)
        body = Path(__file__).read_text(encoding="utf-8")
        chk("⑦ 三橋 · 不碰 TA-Lib · 不代設同意閘 · 不載入 VCGC 程式(只讀冊)", all(t in body for t in ("[VIA:ACCEL-BRIDGE:v0100]", "[VIA:NET-BRIDGE:v0100]", "[VIA:LIB-BRIDGE:v0100]"))
            and "import " + "talib" not in body and 'environ["VIA_NET_' + 'CONSENT"] = "' not in body and "CGC_MDL" + "123" not in body)
        print("  ── 前版鏈自測(原樣印出)──")
        prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
        chk("⑧ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(td, ignore_errors=True)
    print("[計] VDF_SystemManager_v0151 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
