#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG054_TWDailyBackfill v0114 — 薄尾:往前補的「試過了」帳,抓完才記(PR 688 審查 P1)。

v0113 在排計畫的那一刻就把每個往前補的代號記成「這個起日試過了」;
之後本體 v0109 再用 --limit 截掉後面的、或中途斷掉、或某批回失敗 —— 那些代號其實沒抓到,下次同一個起日卻被略過,舊歷史永遠補不回來。
本版:
  ① 排計畫時只決定誰要往前補,不寫帳。
  ② 每一批以起日去抓(本體的 _fetch_group)回來後,這批裡往前補的代號 —— 沒在失敗名單的才記「試過」(來源回了 = 試過;
     新上市的回來沒有更早的列也算試過,不會每天重抓整段);失敗的、被 --limit 截掉的、中途斷掉沒輪到的都不記,下次照樣排。
  ③ 帳換新檔 tw_backfill_head_v0114.json(v0113 的帳可能記了沒抓到的,不沿用;第一次跑會把起點太晚的代號各再試一次)。
其他照 v0113:沒給 --start 照前版 worker;起日格式不對 rc 2 零外呼。不代設同意閘。
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
import os
import re
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG054_TWDailyBackfill"
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
HEAD_TOLERANCE_DAYS = 10
HEAD_BOOK = "tw_backfill_head_v0114.json"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("twbackfill_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)           # v0113(split_start · first_dates)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
split_start = PRIOR.split_start
first_dates = PRIOR.first_dates


def __getattr__(name: str):
    return getattr(PRIOR, name)


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
    tmp = p.with_name("%s.tmp%d" % (p.name, os.getpid()))
    tmp.write_text(json.dumps(book, ensure_ascii=False, indent=0), encoding="utf-8")
    os.replace(tmp, p)


def install(m, start: str, echo=print) -> dict:
    """把起日裝進回補本體:沒資料的代號從起日;起點太晚的代號往前補;「試過」等那一批抓回來、沒失敗才記。回統計。"""
    m.START_DATE = start
    orig_plan, orig_fetch = m.plan, m._fetch_group
    stats = {"start": start, "head": 0, "head_skipped": 0, "head_done": 0, "head_failed": 0}
    head_set = set()

    def plan(listings, last, target, full=False, done=None):
        out = orig_plan(listings, last, target, full=full, done=done)
        if full:
            return out
        first = first_dates(m)
        book = read_head_book(m)
        limit = (date.fromisoformat(start) + timedelta(days=HEAD_TOLERANCE_DAYS)).isoformat()
        planned = {t for t, _s in out}
        head = []
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
        head_set.clear()
        head_set.update(head)
        stats["head"] = len(head)
        echo("[起日 v%s] %s · 往前補 %d 檔(庫內最早一天晚於 %s)· 已試過略過 %d 檔 · 本輪待抓 %d(含增量 %d)· 抓完沒失敗才記試過"
             % (VERSION, start, len(head), limit, stats["head_skipped"], len(out), len([1 for t, _s in out if t in planned and t not in head])), flush=True)
        return out

    def fetch_group(net, batch, st, ee, *a, **k):
        rc = orig_fetch(net, batch, st, ee, *a, **k)
        if st != start:
            return rc
        mine = [t for t in batch if t in head_set]
        if mine:
            failed = {f.get("ticker") for f in ((rc or {}).get("failed") or []) if isinstance(f, dict)}
            book, n = read_head_book(m), 0
            for t in mine:
                if t in failed:
                    stats["head_failed"] += 1
                    continue
                book[t] = start
                n += 1
            if n:
                write_head_book(m, book)
                stats["head_done"] += n
        return rc

    m.plan = plan
    m._fetch_group = fetch_group
    return stats


def worker(argv: list) -> int:
    start, rest = split_start(argv)
    if start is None:
        return PRIOR.worker(rest)                        # 沒給起日:照前版
    m = PRIOR._load()
    stats = install(m, start)
    saved = sys.argv
    sys.argv = [str(getattr(m, "__file__", "VDF_ENG054_worker"))] + list(rest)
    try:
        return int(m.main() or 0)
    finally:
        sys.argv = saved
        print("[起日 v%s] 往前補記試過 %d 檔 · 失敗留待下次 %d 檔(帳 %s)" % (VERSION, stats["head_done"], stats["head_failed"], HEAD_BOOK), flush=True)


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


def _calls_global_fetch(m) -> bool:
    """本體的跑迴圈以模組全域名字叫 _fetch_group(包在 m 上才會生效)。用語法樹看,不用字串搜。"""
    import ast
    tree = ast.parse(Path(m.__file__).read_text(encoding="utf-8"))
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_fetch_group" for n in ast.walk(tree))


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {_STEM} v{VERSION} · 薄尾自測(抓完才記試過;零網路;庫與帳只在暫存夾;正式庫零觸碰)===")
    os.environ["VIA_FROM_VCGC"] = "YES"
    quiet = lambda *x, **k: None  # noqa: E731
    try:
        import duckdb
    except ImportError:
        duckdb = None
    probe = PRIOR._load()
    formal_db, formal_ck = Path(probe.DB_TW), Path(probe.CKPT)

    def snap(p):
        return (p.stat().st_size, p.stat().st_mtime_ns) if p.is_file() else None

    before = (snap(formal_db), snap(formal_ck), snap(formal_ck.with_name(HEAD_BOOK)))
    chk("① 本體以全域名字叫 _fetch_group(語法樹)", _calls_global_fetch(probe), getattr(probe, "__file__", ""))
    if duckdb is None:
        chk("② duckdb 在(不在就量不到往前補)", False, "缺件:SKIP 不是綠")
    else:
        with tempfile.TemporaryDirectory(prefix="eng054_v0114_") as td:
            def fresh():
                m = PRIOR._load()
                m.DB_TW = Path(td) / "tw.duckdb"
                m.CKPT = Path(td) / "ck.json"
                return m
            m = fresh()
            con = duckdb.connect(str(m.DB_TW))
            con.execute(m.PRICE_DDL)
            rows = [("2021-01-04", "1101.TW"), ("2026-11-10", "1101.TW"),
                    ("2022-07-01", "2330.TW"), ("2026-11-17", "2330.TW"),
                    ("2024-03-01", "6999.TWO"), ("2026-11-17", "6999.TWO"),
                    ("2023-05-02", "8888.TW"), ("2026-11-17", "8888.TW")]
            con.executemany("INSERT INTO tw_daily_prices VALUES (?, ?, 1, 1, 1, 1, 1, 1)", rows)
            con.close()
            listings = [{"yf_ticker": t} for t in ("1101.TW", "2330.TW", "6999.TWO", "8888.TW", "9999.TW")]
            last, target = m.last_dates(), "2026-11-18"
            # 負控:v0113 排計畫那一刻就記帳
            m0 = fresh()
            PRIOR.install(m0, "2021-01-01", echo=quiet)
            m0.plan(listings, last, target)
            chk("② 負控:v0113 一排計畫就把 3 檔記成試過(還沒抓)", len(PRIOR.read_head_book(m0)) == 3, PRIOR.read_head_book(m0))
            seen = []

            def fake_fetch(net, batch, st, ee):
                seen.append((list(batch), st))
                return {"rows": [], "failed": [{"ticker": "6999.TWO", "note": "429"}]}

            m._fetch_group = fake_fetch
            stats = install(m, "2021-01-01", echo=quiet)
            p1 = dict(m.plan(listings, last, target))
            chk("③ 排計畫:2330 · 6999 · 8888 往前補、9999 從起日、1101 只補增量;帳還是空的",
                p1.get("2330.TW") == p1.get("6999.TWO") == p1.get("8888.TW") == p1.get("9999.TW") == "2021-01-01"
                and str(p1.get("1101.TW", "")).startswith("2026-11") and read_head_book(m) == {}, (p1, read_head_book(m)))
            m._fetch_group(None, ["2330.TW", "6999.TWO", "9999.TW"], "2021-01-01", 0)   # 8888 被 --limit 截掉:沒輪到
            hb = read_head_book(m)
            chk("④ 抓回來才記:2330 記試過;6999 失敗不記;8888 沒輪到不記;9999 不是往前補的不記",
                hb == {"2330.TW": "2021-01-01"} and stats["head_done"] == 1 and stats["head_failed"] == 1, (hb, stats))
            m._fetch_group(None, ["1101.TW"], "2026-11-11", 0)
            chk("⑤ 增量批(起點不是起日)不碰帳", read_head_book(m) == {"2330.TW": "2021-01-01"})
            m2 = fresh()
            m2._fetch_group = fake_fetch
            install(m2, "2021-01-01", echo=quiet)
            p2 = dict(m2.plan(listings, last, target))
            chk("⑥ 下一輪:6999(失敗)· 8888(沒輪到)照樣往前補;2330(試過)只補增量",
                p2.get("6999.TWO") == p2.get("8888.TW") == "2021-01-01" and str(p2.get("2330.TW", "")).startswith("2026-11"), p2)
            boom = fresh()
            boom._fetch_group = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("斷線"))
            install(boom, "2021-01-01", echo=quiet)
            boom.plan(listings, last, target)
            try:
                boom._fetch_group(None, ["8888.TW"], "2021-01-01", 0)
            except RuntimeError:
                pass
            chk("⑦ 抓的時候中斷(例外)→ 不記", "8888.TW" not in read_head_book(boom))
            chk("⑧ 帳是新檔 tw_backfill_head_v0114.json,寫在檢查點同夾", head_book_path(m) == Path(td) / HEAD_BOOK)
    calls = []
    saved = PRIOR.worker
    PRIOR.worker = lambda a: calls.append(a) or 0
    try:
        rc_none = worker(["--limit", "3"])
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            rc_bad = main(["worker", "--start", "bad"])
    finally:
        PRIOR.worker = saved
    chk("⑨ 沒給 --start 照前版 worker;起日壞掉 rc 2、零外呼", rc_none == 0 and calls == [["--limit", "3"]] and rc_bad == 2)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 加速器橋真的匯入 · 網路工具橋在 · 不含本機路徑 · 不寫同意值", "import VIA_SuperAccel_Module as VIA_ACCEL" in src and "via_net_unified_v*.py" in src
        and ("C:" + "\\Users") not in src and ("_CONSENT\"] " + "=") not in src)
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        rc = PRIOR.selftest()
    chk("⑪ 前版鏈自測照過(v0113 → … → v0109)", rc == 0, "rc %s" % rc)
    chk("⑫ 正式庫 · 檢查點 · 往前補帳零觸碰", (snap(formal_db), snap(formal_ck), snap(formal_ck.with_name(HEAD_BOOK))) == before)
    good = all(ok)
    print(f"[計] {_STEM} v{VERSION} 本版 {sum(ok)}/{len(ok)} · {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
