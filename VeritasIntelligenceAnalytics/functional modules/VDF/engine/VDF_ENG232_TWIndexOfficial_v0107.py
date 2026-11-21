#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VDF_ENG232_TWIndexOfficial v0107 — 薄尾:加權回空的那段若櫃買同段也沒有交易日(前後都有)= 休市,不是洞,往下抓。

操作員 2026-11-21 令:「三個都是獨立系統 授權給你做到 VDF 輸出資料且快」。
容器開閘實跑(VDF 啟動器 v0106 · 擷取群 VDF_TWIndex_Daily · e232 → v0106):每輪 rc 2 · GAP「TAIEX 2025-01-23」,
庫內加權只到 2025-01-22,之後約 22 個月全缺;櫃買照常到 2026-11-20(2025-01-22 → 2025-02-03 中間沒有列)。
根因:2025 春節台股 01-22 封關、02-03 開紅盤;加權接續段 2025-01-23 → 01-31 整段休市,來源照實回空,
v0103 的判洞「整段在過去、跨 5 天以上回空 = 洞,停在這裡下次從同一天接著抓」→ 每一輪都停在同一天,永遠過不去。
(v0106 的分段已知道春節要寬容 16 天,但那是排段;按月抓時的判洞仍是 v0103 的 5 天。)
本版只改一件事:v0103 的判洞多看一個交易日曆 —— 同一個庫裡的櫃買指數(同一個台股交易日曆):
  回空的那段 [a, b] 跨距 ≤ 16 天,櫃買在 [a, b] 內 0 列,而且 a 之前 16 天內與 b 之後 16 天內都有櫃買列 → 休市,不算洞(照 EMPTY 往下一段);
  其餘照 v0103(真的回空仍停在那裡、不跳過、不留洞)。櫃買在這段也有列 / 前後缺一邊 / 跨距更長 → 照判洞。
其他(分段 · 按月寫庫 · 一個指數停了不擋另一個 · 閘)全照 v0106。不代設同意閘;零網路(自測用假內層與暫存庫)。
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
import types
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG232_TWIndexOfficial"
ENGINE_TAG = Path(__file__).stem
HOLIDAY_MAX_DAYS = 16              # 同 v0106 GAP_DAYS:台股最長連假(春節)回空不超過這麼多天
CAL_INDEX = "TPEX"                 # 交易日曆:同庫的櫃買指數(加權與櫃買同一個台股交易日曆)


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_vdf_eng232_prior_for_" + ENGINE_TAG, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0106
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V2 = PRIOR.V2
BASE = PRIOR.BASE


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain() -> list:
    out, m = [], PRIOR
    while isinstance(m, types.ModuleType) and m not in out:
        out.append(m)
        m = getattr(m, "PRIOR", None)
    return out


V0103 = next(m for m in _chain() if callable(vars(m).get("is_gap")) and "GAP_MIN_DAYS" in vars(m))
_IS_GAP_V0103 = V0103.is_gap
_RUN_V0106 = PRIOR.run
_CAL_DB = None                     # 本輪的庫(run 設定;沒設 = BASE.DB_IDX)


def market_closed(a: str, b: str, db=None) -> bool:
    """[a, b] 是不是休市:跨距 ≤ 16 天 · 櫃買在段內 0 列 · 段前與段後 16 天內都有櫃買列(唯讀;庫或表不在 = False)。"""
    try:
        da, db_ = date.fromisoformat(str(a)[:10]), date.fromisoformat(str(b)[:10])
    except ValueError:
        return False
    if (db_ - da).days + 1 > HOLIDAY_MAX_DAYS:
        return False
    lo, hi = (da - timedelta(days=HOLIDAY_MAX_DAYS)).isoformat(), (db_ + timedelta(days=HOLIDAY_MAX_DAYS)).isoformat()
    ds = PRIOR.dates_in(db or _CAL_DB or BASE.DB_IDX, lo, hi).get(CAL_INDEX) or []
    a_s, b_s = da.isoformat(), db_.isoformat()
    inside = any(a_s <= d <= b_s for d in ds)
    return (not inside) and any(d < a_s for d in ds) and any(d > b_s for d in ds)


def is_gap_v0107(a: str, b: str, end: str, state: str) -> bool:
    """同 v0103 判洞;但這段是休市(櫃買日曆前後有列、段內沒有)→ 不算洞。"""
    if not _IS_GAP_V0103(a, b, end, state):
        return False
    return not market_closed(a, b)


def run(start=None, end=None, net=None, db=None, dry: bool = False, inner=None, http=None, echo=print, sleep=None) -> dict:
    """同 v0106 run;判洞用的交易日曆讀本輪的庫。"""
    global _CAL_DB
    keep = _CAL_DB
    _CAL_DB = db or BASE.DB_IDX
    try:
        r = _RUN_V0106(start, end, net=net, db=db, dry=dry, inner=inner, http=http, echo=echo, sleep=sleep)
    finally:
        _CAL_DB = keep
    if isinstance(r, dict):
        r["engine"] = ENGINE_TAG
    return r


def _install() -> None:
    V0103.is_gap = is_gap_v0107                # v0103 run 的 guard 以模組全域叫 is_gap
    PRIOR.run = run                            # v0106 的 main 處理 run 動詞時以模組全域叫 run


def _restore() -> None:
    V0103.is_gap = _IS_GAP_V0103
    PRIOR.run = _RUN_V0106


_install()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    return PRIOR.main(argv)                    # run 動詞 → v0106 main → 本版 run(已換裝)


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    _restore()
    try:
        rc0 = PRIOR.selftest()
    finally:
        _install()
    print(f"=== {ENGINE_TAG} · 薄尾自測(休市不算洞 · 櫃買交易日曆)===")
    chk("⓪ 前版 v0106(含 v0105 → v0100 鏈)自測過", rc0 == 0, f"rc {rc0}")
    quiet = lambda *x, **k: None  # noqa: E731
    row = lambda d, code: {"date": d, "index_code": code, "index_name": "x", "open": 1.0, "low": 1.0, "high": 1.0, "close": 1.0,  # noqa: E731
                           "volume": 1.0, "turnover": 1.0, "inst_foreign_net": None, "inst_trust_net": None, "inst_dealer_net": None,
                           "source": "s", "note": ""}
    tpex = ["2025-01-20", "2025-01-21", "2025-01-22", "2025-02-03", "2025-02-04", "2025-02-05", "2025-03-03"]

    class NoTpex:
        def get_json(self, url, params=None, timeout=30):
            return {}

    with tempfile.TemporaryDirectory(prefix="eng232_v0107_") as td:
        cal = Path(td) / "cal.duckdb"
        V0103.ensure_schema(cal)
        V0103.PRIOR._write(cal, [row(d, "TPEX") for d in tpex])
        chk("① 2025 春節 01-23 → 01-31:櫃買段內 0 列、前後都有 → 休市", market_closed("2025-01-23", "2025-01-31", cal))
        chk("② 櫃買在段內有列(01-27)→ 不是休市(真的回空 = 洞)", not market_closed("2025-01-23", "2025-01-31", Path(td) / "x.duckdb")
            and (V0103.PRIOR._write(Path(td) / "in.duckdb", [row(d, "TPEX") for d in tpex + ["2025-01-27"]]) or True)
            and not market_closed("2025-01-23", "2025-01-31", Path(td) / "in.duckdb"))
        chk("③ 跨距 > 16 天(整月)→ 不當休市", not market_closed("2025-01-23", "2025-02-28", cal))
        V0103.PRIOR._write(Path(td) / "noafter.duckdb", [row(d, "TPEX") for d in tpex[:3]])
        chk("④ 櫃買段後沒有列(日曆不完整)→ 不當休市", not market_closed("2025-01-23", "2025-01-31", Path(td) / "noafter.duckdb"))

        def scenario(use_new: bool, name: str):
            db = Path(td) / name
            V0103.ensure_schema(db)
            V0103.PRIOR._write(db, [row(d, "TPEX") for d in tpex] + [row("2025-01-22", "TAIEX")])
            calls = []

            def fake(a, b, net=None, db=None, dry=False):
                calls.append(a)
                if a.startswith("2025-01"):
                    return {"state": "EMPTY", "fetched": 0, "added": 0, "calls": 1}
                n = V0103.PRIOR._write(db, [row(b, "TAIEX")])
                return {"state": "OK", "fetched": 1, "added": n, "calls": 1}
            global _CAL_DB
            if not use_new:
                _restore()
            keep = _CAL_DB
            _CAL_DB = db
            try:
                r = V0103.run("2025-01-23", "2025-03-31", inner=fake, http=NoTpex(), db=db, echo=quiet)
            finally:
                _CAL_DB = keep
                _install()
            return r, calls, BASE.count(db).get("TAIEX", (0,))[0]
        r_old, c_old, n_old = scenario(False, "old.duckdb")
        chk("⑤ 重現:前版判洞 → 加權停在 2025-01-23(GAP)、2 月 3 月沒被叫到", r_old["state"] == "GAP" and c_old == ["2025-01-23"] and n_old == 1,
            (r_old.get("state"), c_old, r_old.get("stopped_at")))
        r_new, c_new, n_new = scenario(True, "new.duckdb")
        tx = (r_new.get("by_index") or {}).get("TAIEX") or {}
        chk("⑥ 本版:春節段當休市往下抓 → 2 月 · 3 月都抓到、寫庫(加權 1 → 3 列)· 加權分項 OK、沒有停點(假櫃買回空的停點照記在櫃買)",
            tx.get("state") == "OK" and "stopped_at" not in tx and c_new == ["2025-01-23", "2025-02-01", "2025-03-01"] and n_new == 3
            and "TAIEX" not in str(r_new.get("stopped_at")), (tx, c_new, n_new, r_new.get("stopped_at")))
    chk("⑦ 換裝:v0103 判洞 = 本版 · v0106 的 run = 本版(main 的 run 動詞叫得到)",
        V0103.is_gap is is_gap_v0107 and PRIOR.run is run and _CAL_DB is None)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑧ 加速器橋 · 網路橋在;不碰 TA-Lib;不寫同意閘", "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src and "def _via_net" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", body))
    names = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("⑨ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in names), f"{len(names)} 支")
    print(f"  [計] {ENGINE_TAG} 本版 {sum(ok)}/{len(ok)} · 合計 {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
