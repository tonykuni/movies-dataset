#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""
VDF_ENG054_TWDailyBackfill v0113 — 薄尾:worker 收 --start(大類起日)· 庫裡已有但起點太晚的代號往前補

操作員 2026-11-19 令:「啟動 VDF 更新 2021-01-01 至最新的數據」。VCGC 檢視參數樹的結果:
  ① 起日是按大類設的(VDF_MDL012_FetchGroups 的 start 動詞;台股大類 TW_MARKET 預設 2022-07-01),
     但這個起日只傳給了指數引擎(e232);日量價(本引擎)不收起日,沒資料的代號一律從寫死的 2022-07-01 抓。
  ② 增量只往後補:庫裡已有資料的代號只抓「最新日之後」,起日改早了也不會往前補。
本版(v0112 · v0111 · v0110 · v0109 一字不動):
  ① worker 收 --start YYYY-MM-DD:沒資料的代號從這天抓(取代寫死的 2022-07-01)。不給 --start = 照前版。
  ② 往前補:庫裡最早一天比起日晚 10 天以上的代號,從起日重抓到今天(寫庫照前版去重,不會重複列)。
     上市日本來就比起日晚的代號(往前根本沒資料)只試一次:試過的記在 tw_backfill_head_v0113.json(與檢查點同夾),
     同一個起日不再重試;起日改了才會再試。
  ③ 每輪印一行:要往前補幾檔、因為已試過而略過幾檔。
其餘(清單 · 清非主動式 ETF · 日價表 · 增量律 · 庫鎖)全照前版。不代設同意閘。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本檔自己不連網,連網的是回補本體。"""
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

import importlib.util
import json
import re
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG054_TWDailyBackfill"
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
HEAD_TOLERANCE_DAYS = 10
HEAD_BOOK = "tw_backfill_head_v0113.json"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("twbackfill_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)           # v0112(worker 動詞 · connect_retry 補路徑)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def split_start(argv: list) -> tuple:
    """從參數裡拿掉 --start X,回 (起日或 None, 其餘參數)。起日格式不對就丟 ValueError(不靜默改成預設)。"""
    a, start = list(argv), None
    if "--start" in a:
        i = a.index("--start")
        if i + 1 >= len(a):
            raise ValueError("--start 後面要接日期 YYYY-MM-DD")
        start = date.fromisoformat(a[i + 1]).isoformat()
        del a[i:i + 2]
    return start, a


def first_dates(m) -> dict:
    """各代號庫內最早一天(唯讀);庫或表不在 = {}。"""
    if not Path(m.DB_TW).is_file():
        return {}
    try:
        con = m.connect_retry(m.DB_TW, read_only=True)
        try:
            rows = con.execute("SELECT ticker, MIN(CAST(date AS VARCHAR)) FROM tw_daily_prices WHERE ticker <> '_NOOP_' GROUP BY ticker").fetchall()
        finally:
            con.close()
        return {r[0]: str(r[1])[:10] for r in rows if r[0]}
    except Exception:
        return {}


def head_book_path(m) -> Path:
    return Path(m.CKPT).with_name(HEAD_BOOK)


def read_head_book(m) -> dict:
    p = head_book_path(m)
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
    except (OSError, ValueError):
        return {}


def write_head_book(m, book: dict) -> None:
    p = head_book_path(m)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp%d" % __import__("os").getpid())
    tmp.write_text(json.dumps(book, ensure_ascii=False, indent=0), encoding="utf-8")
    __import__("os").replace(tmp, p)


def install(m, start: str, echo=print) -> dict:
    """把起日裝進回補本體:沒資料的代號從起日;起點太晚的代號往前補(試過的不再試)。回統計。"""
    m.START_DATE = start
    orig_plan = m.plan
    stats = {"start": start, "head": 0, "head_skipped": 0}

    def plan(listings, last, target, full=False, done=None):
        out = orig_plan(listings, last, target, full=full, done=done)
        if full:
            return out
        first = first_dates(m)
        book = read_head_book(m)
        limit = (date.fromisoformat(start) + timedelta(days=HEAD_TOLERANCE_DAYS)).isoformat()
        planned = {t for t, _s in out}
        head, tried = [], []
        for x in listings:
            t = x["yf_ticker"]
            fd = first.get(t)
            if fd is None or fd <= limit:
                continue
            if book.get(t) == start:
                stats["head_skipped"] += 1
                continue
            head.append(t)
        out = [(t, s) for t, s in out if t not in head] + [(t, start) for t in head]
        for t in head:
            book[t] = start
            tried.append(t)
        stats["head"] = len(head)
        if tried:
            write_head_book(m, book)
        echo("[起日 v%s] %s · 往前補 %d 檔(庫內最早一天晚於 %s)· 已試過略過 %d 檔 · 本輪待抓 %d(含增量 %d)"
             % (VERSION, start, len(head), limit, stats["head_skipped"], len(out), len([1 for t, _s in out if t in planned and t not in head])), flush=True)
        return out

    m.plan = plan
    return stats


def worker(argv: list) -> int:
    start, rest = split_start(argv)
    if start is None:
        return PRIOR.worker(rest)                        # 沒給起日:照前版
    m = PRIOR._load()
    install(m, start)
    saved = sys.argv
    sys.argv = [str(getattr(m, "__file__", "VDF_ENG054_worker"))] + list(rest)
    try:
        return int(m.main() or 0)
    finally:
        sys.argv = saved


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a and a[0] == "worker":
        try:
            return worker(a[1:])
        except ValueError as exc:
            print("[拒絕] " + str(exc) + "(零外呼 · 零寫入)")
            return 2
    if "--selftest" in a:
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {_STEM} v{VERSION} · 薄尾自測(零網路;庫與檢查點只在暫存夾;正式庫零觸碰)===")
    import os
    os.environ["VIA_FROM_VCGC"] = "YES"
    quiet = lambda *x, **k: None  # noqa: E731
    chk("① 拿掉 --start:回起日與其餘參數;沒給 = None", split_start(["--start", "2021-01-01", "--limit", "5"]) == ("2021-01-01", ["--limit", "5"]) and split_start(["--full"]) == (None, ["--full"]))
    bad = ""
    try:
        split_start(["--start", "2021-13-40"])
    except ValueError as exc:
        bad = str(exc)
    chk("② 起日格式不對 → 拒絕(不靜默改成預設)", bool(bad))
    try:
        import duckdb
    except ImportError:
        duckdb = None
    probe = PRIOR._load()
    formal_db, formal_ck = Path(probe.DB_TW), Path(probe.CKPT)

    def snap(p):
        return (p.stat().st_size, p.stat().st_mtime_ns) if p.is_file() else None

    before = (snap(formal_db), snap(formal_ck), snap(formal_ck.with_name(HEAD_BOOK)))
    if duckdb is None:
        chk("③ duckdb 在(不在就量不到往前補)", False, "缺件:SKIP 不是綠")
    else:
        with tempfile.TemporaryDirectory(prefix="eng054_v0113_") as td:
            m = PRIOR._load()
            m.DB_TW = Path(td) / "tw.duckdb"
            m.CKPT = Path(td) / "ck.json"
            con = duckdb.connect(str(m.DB_TW))
            con.execute(m.PRICE_DDL)
            rows = [("2021-01-04", "1101.TW"), ("2026-11-10", "1101.TW"),     # 已從起日開始:只要增量
                    ("2022-07-01", "2330.TW"), ("2026-11-17", "2330.TW"),     # 起點太晚:要往前補
                    ("2024-03-01", "6999.TWO"), ("2026-11-17", "6999.TWO")]   # 起點太晚(新上市):試一次
            con.executemany("INSERT INTO tw_daily_prices VALUES (?, ?, 1, 1, 1, 1, 1, 1)", rows)
            con.close()
            listings = [{"yf_ticker": t} for t in ("1101.TW", "2330.TW", "6999.TWO", "9999.TW")]
            last = m.last_dates()
            target = "2026-11-18"
            prior_plan = dict(m.plan(listings, last, target))
            stats = install(m, "2021-01-01", echo=quiet)
            p1 = dict(m.plan(listings, last, target))
            chk("③ 負控:前版沒資料的代號從寫死的起點抓、起點太晚的代號只補後面", prior_plan.get("9999.TW") not in (None, "2021-01-01") and prior_plan.get("2330.TW", "").startswith("2026-11"), prior_plan)
            chk("④ 沒資料的代號從起日 2021-01-01 抓", p1.get("9999.TW") == "2021-01-01", p1.get("9999.TW"))
            chk("⑤ 起點太晚的代號從起日往前補(2330 · 6999);已從起日開始的只補增量(1101)", p1.get("2330.TW") == "2021-01-01" and p1.get("6999.TWO") == "2021-01-01" and str(p1.get("1101.TW", "")).startswith("2026-11"), p1)
            hb = read_head_book(m)
            chk("⑥ 試過的記帳(同夾 tw_backfill_head_v0113.json);寫檔是原子換檔", hb == {"2330.TW": "2021-01-01", "6999.TWO": "2021-01-01"} and head_book_path(m).parent == Path(td), hb)
            p2 = dict(m.plan(listings, last, target))
            chk("⑦ 同一個起日再跑:試過的不再往前補(6999 新上市不會每天重抓整段)", str(p2.get("6999.TWO", "")).startswith("2026-11") and stats["head_skipped"] == 2, p2.get("6999.TWO"))
            m2 = PRIOR._load()
            m2.DB_TW, m2.CKPT = m.DB_TW, m.CKPT
            install(m2, "2020-01-01", echo=quiet)
            p3 = dict(m2.plan(listings, last, target))
            chk("⑧ 起日改更早:試過的帳以起日為鍵,會再試一次", p3.get("6999.TWO") == "2020-01-01" and p3.get("1101.TW") == "2020-01-01", p3)
            full = dict(m2.plan(listings, last, target, full=True, done=set()))
            chk("⑨ --full 照前版(不另加往前補)", set(full.values()) == {"2020-01-01"} and len(full) == 4)
    calls = []
    saved = PRIOR.worker
    PRIOR.worker = lambda a: calls.append(a) or 0
    try:
        rc_none = worker(["--limit", "3"])
        rc_bad = main(["worker", "--start", "bad"])
    finally:
        PRIOR.worker = saved
    chk("⑩ 沒給 --start 照前版 worker;起日壞掉 rc 2、零外呼", rc_none == 0 and calls == [["--limit", "3"]] and rc_bad == 2)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑪ 加速器橋真的匯入 · 網路工具橋在 · 不含本機路徑 · 不寫同意值", "import VIA_SuperAccel_Module as VIA_ACCEL" in src and "via_net_unified_v*.py" in src
        and ("C:" + "\\Users") not in src and ("_CONSENT\"] " + "=") not in src)
    rc = PRIOR.selftest()
    chk("⑫ 前版鏈自測照過(v0112 → v0111 → v0110 → v0109)", rc == 0, "rc %s" % rc)
    chk("⑬ 正式庫 · 檢查點 · 往前補帳零觸碰", (snap(formal_db), snap(formal_ck), snap(formal_ck.with_name(HEAD_BOOK))) == before)
    good = all(ok)
    print(f"[計] {_STEM} v{VERSION} 本版 {sum(ok)}/{len(ok)} · {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
