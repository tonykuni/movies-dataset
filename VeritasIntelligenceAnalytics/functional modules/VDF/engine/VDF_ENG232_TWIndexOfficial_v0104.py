#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG232_TWIndexOfficial v0104 — 薄尾:櫃買某個歷史月份來源回空也停在那裡(不跳過、不留洞)。

PR 審查(2026-11-18)點出:v0103 只替加權補了「回空就停」;櫃買那一半(v0102 的按月迴圈)某個月回空時照樣往後寫,
只要後面有月份成功就回 OK。增量起點只看各指數的最新日 → 中間那個月永遠不會回補。
本版(v0103 · v0102 一字不動):櫃買逐月抓時,整個月在過去(判法同 v0103 的加權:跨 5 天以上、在迄日前 3 天以前)卻一列都沒有
→ 記下那個月、之後的月份這一輪不再抓(零外呼),結果狀態 GAP(rc 2)並點名停在哪個月;之前的月份已寫庫。
下一次櫃買的增量起點是庫裡最後一天的隔天,會從缺的那個月接著抓。加權那一半照 v0103 繼續跑,不受櫃買影響。
當月(資料可能還沒出)回空不算洞。其餘全照 v0103。不代設同意閘。
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
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG232_TWIndexOfficial"
ENGINE_TAG = Path(__file__).stem


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_vdf_eng232_prior_for_" + ENGINE_TAG, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0103(欄型 · 加權不留洞)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V2 = PRIOR.PRIOR                                        # v0102(櫃買按月迴圈在這裡;它以模組全域叫 tpex_month_rows)
BASE = PRIOR.BASE
_V3_RUN = PRIOR.run


def __getattr__(name):
    return getattr(PRIOR, name)


def month_span(y: int, m: int) -> tuple:
    first = date(y, m, 1)
    last = (first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    return first.isoformat(), last.isoformat()


def run(start=None, end=None, net=None, db=None, dry: bool = False, inner=None, http=None, echo=print, sleep=None) -> dict:
    end_s = end or date.today().isoformat()
    orig = V2.tpex_month_rows
    gap = {"at": None, "skipped": 0}

    def guarded(h, y, m):
        if gap["at"] is not None:                         # 洞之後的月份這一輪不抓(零外呼),免得把洞埋在後面
            gap["skipped"] += 1
            return []
        rows = orig(h, y, m)
        a, b = month_span(y, m)
        if not rows and PRIOR.is_gap(a, b, end_s, "EMPTY"):
            gap["at"] = "%04d-%02d" % (y, m)
            echo("  [TW 指數] 櫃買 %s 整個月來源回空 → 停在這個月(之後 %s 起這一輪不抓),下次從這裡接著抓" % (gap["at"], gap["at"]), flush=True)
        return rows

    V2.tpex_month_rows = guarded
    try:
        res = _V3_RUN(start, end, net=net, db=db, dry=dry, inner=inner, http=http, echo=echo, sleep=sleep)
    finally:
        V2.tpex_month_rows = orig
    if gap["at"] is not None:
        res.setdefault("by_index", {}).setdefault("TPEX", {})["state"] = "GAP"
        res["by_index"]["TPEX"]["stopped_at"] = gap["at"]
        res["by_index"]["TPEX"]["months_not_fetched"] = gap["skipped"]
        if res.get("state") in ("OK", "EMPTY", "UP_TO_DATE"):
            res["state"] = "GAP"
            res["stopped_at"] = "TPEX " + gap["at"]
            res["note"] = "櫃買 %s 整個月來源回空;停在這裡,下次從同一個月接著抓(不跳過)" % gap["at"]
    return res


PRIOR.run = run          # v0103 的 main 以模組全域叫 run()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return PRIOR.main(argv)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""))

    quiet = lambda *x, **k: None  # noqa: E731
    print("=== %s 薄尾自測(櫃買不留洞;零網路;庫只在暫存夾)===" % ENGINE_TAG)
    chk("① 月份頭尾:2024-02 是閏月 29 天", month_span(2024, 2) == ("2024-02-01", "2024-02-29") and month_span(2026, 12) == ("2026-12-01", "2026-12-31"))

    class FakeHttp:
        def __init__(self, empty=()):
            self.urls, self.empty = [], set(empty)

        def get_json(self, url, params=None, timeout=30):
            ym = (params or {}).get("date", "")[:7].replace("/", "-")
            self.urls.append((url.rsplit("/", 1)[-1], ym))
            if ym in self.empty:
                return {}
            y, m = int(ym[:4]), int(ym[5:7])
            if url == V2.TPEX_INX:
                return {"tables": [{"data": [["%04d/%02d/02" % (y, m), "10", "11", "9", "10.5", "0.1"], ["%04d/%02d/03" % (y, m), "10", "11", "9", "10.6", "0.1"]]}]}
            return {"tables": [{"data": [["%d/%02d/02" % (y - 1911, m), "1,000", "2,000", "5", 10.5, 0.1], ["%d/%02d/03" % (y - 1911, m), "1,000", "2,000", "5", 10.6, 0.1]]}]}

    taiex_calls = []

    def fake_taiex(a, b, net=None, db=None, dry=False):
        taiex_calls.append(a)
        return {"state": "OK", "fetched": 0, "added": 0, "calls": 1}

    try:
        import duckdb  # noqa: F401
        have = True
    except ImportError:
        have = False
    if not have:
        chk("② duckdb 在(不在就量不到寫庫)", False, "缺件:SKIP 不是綠")
    else:
        with tempfile.TemporaryDirectory(prefix="eng232_v0104_") as td:
            fh = FakeHttp(empty={"2024-02"})
            gdb = Path(td) / "gap.duckdb"
            lines = []
            r = run("2024-01-01", "2024-04-30", inner=fake_taiex, http=fh, db=gdb, echo=lambda *x, **k: lines.append(x[0]))
            months = sorted({ym for _u, ym in fh.urls})
            chk("② 櫃買 2 月整個月回空 → 狀態 GAP、點名停在 2024-02;3、4 月零外呼;1 月已寫庫",
                r["state"] == "GAP" and r["by_index"]["TPEX"]["stopped_at"] == "2024-02" and months == ["2024-01", "2024-02"]
                and r["by_index"]["TPEX"]["months_not_fetched"] == 2 and BASE.count(gdb).get("TPEX", (0,))[0] == 2, "%s · 抓過的月 %s" % (r["state"], months))
            chk("③ 下一次櫃買的增量起點在洞之前(會從 2 月接著抓)", V2.starts(gdb)["TPEX"] == "2024-01-04", V2.starts(gdb)["TPEX"])
            chk("④ 加權那一半照跑,不受櫃買的洞影響", len(taiex_calls) == 4 and any("停在這個月" in x for x in lines), "%d 段" % len(taiex_calls))
            taiex_calls.clear()
            fh_neg = FakeHttp(empty={"2024-02"})
            ndb = Path(td) / "neg.duckdb"
            r_neg = _V3_RUN("2024-01-01", "2024-04-30", inner=fake_taiex, http=fh_neg, db=ndb, echo=quiet)
            c_neg = BASE.count(ndb).get("TPEX", (0, "", ""))
            chk("⑤ 負控:前版同一份輸入回 OK、3、4 月照寫,2 月的洞被埋住(審查點出的就是這個)", r_neg["state"] == "OK" and c_neg[0] == 6 and str(c_neg[2]).startswith("2024-04"), "%s · %s 列到 %s" % (r_neg["state"], c_neg[0], c_neg[2]))
            fh_ok = FakeHttp()
            r_ok = run("2024-01-01", "2024-04-30", inner=fake_taiex, http=fh_ok, db=Path(td) / "ok.duckdb", echo=quiet)
            chk("⑥ 沒有洞:四個月照常抓完、狀態 OK", r_ok["state"] == "OK" and BASE.count(Path(td) / "ok.duckdb")["TPEX"][0] == 8 and "stopped_at" not in r_ok["by_index"]["TPEX"])
            today = date.today()
            cur = "%04d-%02d" % (today.year, today.month)
            fh_cur = FakeHttp(empty={cur})
            r_cur = run(today.replace(day=1).isoformat(), today.isoformat(), inner=fake_taiex, http=fh_cur, db=Path(td) / "cur.duckdb", echo=quiet)
            chk("⑦ 當月回空(資料可能還沒出)不算洞", r_cur["state"] != "GAP" and r_cur["by_index"]["TPEX"].get("state") != "GAP", r_cur["state"])
            fh_resume = FakeHttp()
            r_res = run(None, "2024-04-30", inner=fake_taiex, http=fh_resume, db=gdb, echo=quiet)
            got = sorted({ym for _u, ym in fh_resume.urls})
            chk("⑧ 來源恢復後再跑:從 1 月的隔天接著抓,2、3、4 月補進來", r_res["by_index"]["TPEX"].get("state") == "OK" and got[0] == "2024-01" and "2024-02" in got and BASE.count(gdb)["TPEX"][0] == 8, got)
    chk("⑨ 跑完還原:v0102 的 tpex_month_rows 是原件;裝進前版的是本版的 run", V2.tpex_month_rows.__name__ == "tpex_month_rows" and PRIOR.run is run)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑩ 加速器橋真的匯入 · 網路工具橋在 · 不含本機路徑 · 不寫同意值 · 不刪列", "import VIA_SuperAccel_Module as VIA_ACCEL" in src and "via_net_unified_v*.py" in src
        and ("C:" + "\\Users") not in src and ("_CONSENT\"] " + "=") not in src and ("DELETE " + "FROM") not in src)
    PRIOR.run = _V3_RUN
    try:
        rc = PRIOR.selftest()
    finally:
        PRIOR.run = run
    chk("⑪ 前版自測照過", rc == 0, "rc %s" % rc)
    good = all(ok)
    print("[計] %s 本版 %d/%d · %s" % (ENGINE_TAG, sum(ok), len(ok), "PASS" if good else "FAIL"))
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
