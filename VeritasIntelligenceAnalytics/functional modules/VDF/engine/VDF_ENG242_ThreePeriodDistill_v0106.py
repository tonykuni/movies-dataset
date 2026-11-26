#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_ENG242_ThreePeriodDistill v0106 — 薄尾(v0100–v0105 一字不動):桌機 v0105 實跑後的三件事

操作員 2026-11-26 桌機 lake(v0105):distill OK 5 → 11 · 對核 3 對 · 仍 RED(PK_CONFLICT 1)· mismatch 1366 · reconcile_not_ok 2。
SUMMARY 逐表看出:
  · TW_PRICE_VOL 對核 compared 7110(≈ 1422 鍵 × 5 欄)、mismatch 1366 ≈ 一整欄全不對 → 很像單位差(股 / 張 ×1000),
    但收據只給總數,看不出是哪一欄、差幾倍。
  · TW_CHIP(margin × derived)與 SENTIMENT(sentiment_daily × aaii)兩對 NO_COMMON_NUMERIC:兩表本來就沒有共同數值欄,
    不是錯,是「不可比」;v0105 把它算進 reconcile_not_ok 亮黃 → 誤報。
  · TW_ACTIVE_ETF holdings_daily 仍 NO_DATE_COL(日期欄名不在常見名單)。
  · US_MACRO (series, date) 同鍵不同值 2 組、其他欄全同(只 value 不同)→ 來源資料本身重複,照律紅、不猜(本版不動)。
本版:
  ① 對核逐欄:每欄 mismatch 數;不一致列的 a/b 比值中位數若落在 10 的整數次方(±2%)→ 記 unit_suspect(例 "×1000")
     與「照該倍數換算後仍不一致」的列數 mismatch_if_scaled。只寫倍數標籤與計數,不寫任何值(資料邊界);資料一律不改。
  ② NO_COMMON_NUMERIC 改記 NOT_COMPARABLE(灰):不算 reconcile_not_ok、不讓燈變黃;其他非 OK 照舊黃。
  ③ 日期欄推斷再補一條:欄名以 date / _dt / 日期 結尾、而且只有一欄 → 用它。
唯讀開湖;不出網;不用 TA-Lib;不設同意閘。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本支零外呼。"""
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

import importlib.util
import math
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_ENG242_ThreePeriodDistill"
VERSION = "v0106"
TAG = f"{STEM} {VERSION}"
UNIT_TOL = 0.02
NOT_COMPARABLE = "NOT_COMPARABLE"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{PRIOR_PATH.stem}_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


_q = PRIOR._q
_ORIG_INFER = PRIOR.infer_date


def infer_date(cols: list, nb: dict, key_col) -> str | None:
    hit = _ORIG_INFER(cols, nb, key_col)
    if hit:
        return hit
    nn = BASE.norm_name
    tail = [c for c, _ in cols if c != key_col and re.search(r"(date|_dt|日期)$", nn(c))]
    return tail[0] if len(tail) == 1 else None


PRIOR.infer_date = infer_date                       # v0105 distill_one 依模組全域名叫 infer_date


def unit_label(ratio) -> str | None:
    """比值中位數若在 10^k(k ≠ 0,|k| ≤ 6)的 ±2% 內 → '×10^k' 標籤;否則 None。"""
    if ratio is None or ratio <= 0 or not math.isfinite(ratio):
        return None
    k = round(math.log10(ratio))
    if k == 0 or abs(k) > 6:
        return None
    return f"×{10 ** k:g}" if abs(ratio / (10 ** k) - 1) <= UNIT_TOL else None


def per_column(con, out_path: Path, tol: float) -> dict:
    rel = f"read_parquet('{out_path.as_posix()}')"
    rows = con.execute(f"SELECT col, count(*) FILTER (WHERE rel_diff > {float(tol)}), "
                       f"median(a_val / nullif(b_val, 0)) FILTER (WHERE rel_diff > {float(tol)}) FROM {rel} GROUP BY col ORDER BY col").fetchall()
    out = {}
    for col, mism, ratio in rows:
        ent = {"mismatch": int(mism or 0)}
        lab = unit_label(ratio) if mism else None
        if lab:
            f = 10 ** round(math.log10(ratio))
            left = con.execute(f"SELECT count(*) FROM {rel} WHERE col = ? AND abs(a_val - b_val * {f}) / "
                               f"nullif(greatest(abs(a_val), abs(b_val * {f})), 0) > {float(tol)}", [col]).fetchone()[0]
            ent.update(unit_suspect=lab, mismatch_if_scaled=int(left))
        out[col] = ent
    return out


_ORIG_REC = BASE.reconcile_pair                     # = v0105 的 reconcile_pair(鍵對齊 · NO_OVERLAP)


def reconcile_pair(con, a_rel: str, b_rel: str, pk: list, tol: float, out_path: Path) -> dict:
    r = _ORIG_REC(con, a_rel, b_rel, pk, tol, out_path)
    if r.get("state") == "NO_COMMON_NUMERIC":
        r["state"] = NOT_COMPARABLE
        r["note"] = "兩表沒有共同數值欄:不可比(灰),不是錯"
    elif r.get("state") == "OK" and r.get("mismatch") and out_path.exists():
        r["by_column"] = per_column(con, out_path, tol)
    return r


_DD_V0100 = PRIOR._ORIG_DD                          # v0100 本體的 do_distill(v0105 的 do_distill 也包它)


def do_distill(mod, prm: dict, nb: dict, lake: Path) -> dict:
    res = _DD_V0100(mod, prm, nb, lake)
    rec = res.get("reconcile") or []
    bad = [r for r in rec if r.get("state") not in ("OK", NOT_COMPARABLE)]
    gray = [r for r in rec if r.get("state") == NOT_COMPARABLE]
    cnt = res.setdefault("counts", {})
    cnt["reconcile_not_ok"] = len(bad)
    cnt["not_comparable"] = len(gray)
    if bad and res.get("lamp") == "GREEN":
        res["lamp"] = "YELLOW"
    return res


for _k in ("by_column", "not_comparable"):
    if _k not in PRIOR.SUMMARY_KEYS:
        PRIOR.SUMMARY_KEYS = tuple(PRIOR.SUMMARY_KEYS) + (_k,)


def _install():
    BASE.reconcile_pair = reconcile_pair
    BASE.do_distill = do_distill
    PRIOR.infer_date = infer_date
    BASE.TAG = TAG


def _uninstall():
    BASE.reconcile_pair = _ORIG_REC
    BASE.do_distill = PRIOR.do_distill
    PRIOR.infer_date = _ORIG_INFER
    BASE.TAG = PRIOR.TAG


_install()


def main() -> int:
    if sys.argv[1:2] in (["--selftest"], ["selftest"]):
        return selftest()
    return BASE.main()


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(f"  [{'OK' if cond else 'NG'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, VIA_NET_TOOL_PATH)
    chk("已裝進(reconcile_pair · do_distill · infer_date)· 橫幅寫本版",
        BASE.reconcile_pair is reconcile_pair and BASE.do_distill is do_distill and PRIOR.infer_date is infer_date and BASE.TAG == TAG)
    chk("倍數標籤:1000.4 → ×1000 · 0.001 → ×0.001 · 1.3 / 1.0 / 37 → 無",
        unit_label(1000.4) == "×1000" and unit_label(0.001) == "×0.001" and unit_label(1.3) is None
        and unit_label(1.0) is None and unit_label(37.0) is None, (unit_label(1000.4), unit_label(0.001)))
    duckdb = BASE._duck()
    nb = BASE.name_book() if callable(getattr(BASE, "name_book", None)) else {"rev": {}}
    con = duckdb.connect()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        con.execute("CREATE TABLE pa AS SELECT * FROM (VALUES ('2330', DATE '2026-11-25', 100.0, 5000000.0),"
                    "('2317', DATE '2026-11-25', 50.0, 3000000.0),('2454', DATE '2026-11-25', 9.0, 1000.0)) t(code, date, close, volume)")
        con.execute("CREATE TABLE pb AS SELECT * FROM (VALUES ('2330', DATE '2026-11-25', 100.0, 5000.0),"
                    "('2317', DATE '2026-11-25', 50.0, 3000.0),('2454', DATE '2026-11-25', 9.0, 1.0)) t(code, date, close, volume)")
        r = reconcile_pair(con, "pa", "pb", ["code", "date"], 0.001, td / "rec.parquet")
        bc = r.get("by_column") or {}
        chk("① 逐欄:close 0 不一致 · volume 3 筆全不一致且標 ×1000 · 換算後 0(資料不改)",
            r["state"] == "OK" and r["mismatch"] == 3 and bc.get("close", {}).get("mismatch") == 0
            and bc.get("volume", {}).get("unit_suspect") == "×1000" and bc["volume"].get("mismatch_if_scaled") == 0, r)
        con.execute("CREATE TABLE ca AS SELECT * FROM (VALUES ('2330', DATE '2026-11-25', 1.0)) t(code, date, margin_buy)")
        con.execute("CREATE TABLE cb AS SELECT * FROM (VALUES ('2330', DATE '2026-11-25', 2.0)) t(code, date, short_ratio)")
        r2 = reconcile_pair(con, "ca", "cb", ["code", "date"], 0.001, td / "rec2.parquet")
        chk("② 沒有共同數值欄 → NOT_COMPARABLE(灰)", r2["state"] == NOT_COMPARABLE, r2)
        con.execute("CREATE TABLE hd AS SELECT * FROM (VALUES ('00980A','2330','2026-11-24',1.0),('00980A','2330','2026-11-25',2.0)) "
                    "t(etf_ticker, holding_ticker, holding_date, weight)")
        r3 = BASE.distill_one(con, "hd", None, None, nb, 3, td / "hd.parquet")
        chk("③ 欄名以 date 結尾的唯一欄 holding_date → 推得到 · 不再 NO_DATE_COL",
            r3["state"] == "OK" and r3.get("date_inferred") == "holding_date", r3)
    con.close()
    fake_rec = [{"state": "OK", "mismatch": 0}, {"state": NOT_COMPARABLE}, {"state": "NO_OVERLAP"}]
    keep = PRIOR._ORIG_DD
    try:
        globals()["_DD_V0100"] = lambda *a: {"rows": [], "reconcile": fake_rec[:2], "lamp": "GREEN", "counts": {}}
        g = do_distill(None, {}, {}, Path("."))
        globals()["_DD_V0100"] = lambda *a: {"rows": [], "reconcile": fake_rec, "lamp": "GREEN", "counts": {}}
        y = do_distill(None, {}, {}, Path("."))
    finally:
        globals()["_DD_V0100"] = keep
    chk("④ 燈:只有 NOT_COMPARABLE → 維持綠(不可比計 1);有 NO_OVERLAP → 黃(not_ok 1)",
        g["lamp"] == "GREEN" and g["counts"]["not_comparable"] == 1 and g["counts"]["reconcile_not_ok"] == 0
        and y["lamp"] == "YELLOW" and y["counts"]["reconcile_not_ok"] == 1, (g, y))
    chk("⑤ SUMMARY 白名單含 by_column(只倍數標籤與計數)", "by_column" in PRIOR.SUMMARY_KEYS)
    _uninstall()
    try:
        rc = PRIOR.selftest()
    finally:
        _install()
    chk("前版 v0105 鏈自測(本版換裝卸下)照過", rc == 0, rc)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("檔面:第 3 行加速器標記 · 雙橋在 · 零 TA-Lib · 不設同意閘 · 不含本機路徑",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and not re.search(r"^\s*(import|from)\s+(talib|requests)", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M)
        and "C:\\Users\\" + "tonyk" not in src)
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
