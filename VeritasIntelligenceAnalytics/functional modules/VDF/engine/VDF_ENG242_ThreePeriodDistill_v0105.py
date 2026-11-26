#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_ENG242_ThreePeriodDistill v0105 — 薄尾(v0100–v0104 一字不動):桌機 distill RED 的三個成因 + 收據逐表

操作員 2026-11-26 桌機 lake(VIA_HostBoot v0103)→ three distill / reconcile RED;distill.parquet 逐表:
  · US_MACRO us_macro:主鍵 (series, date) 同鍵不同值 2 組 → PK_CONFLICT → 總燈 RED。
  · 7 張表 NO_DATE_COL(TW_CHIP ×2 · TW_MONTHLY_REV · TW_ACTIVE_ETF ×2 · TW_FIN · aaii_sentiment):冊上沒給 date_col,
    湖(ENG239)卻量得到其中幾張的日期欄(tw_chip_* date · tw_financial Date · aaii date)。
  · TW_PRICE_VOL 兩表都 OK(6063 · 7105 列),reconcile 卻 compared 0:鍵 (code, date) 一筆都沒對上(代號格式或日期型別不同)。
  · SUMMARY.json 只寫總數,看不到是哪一張表 → 要操作員另貼指令才查得到。
本版:
  ① 日期欄推斷:冊上沒給或表裡沒有 → 同義冊正規名 date → 常見日期欄名 → 唯一的 DATE / TIMESTAMP 型別欄;推到記 date_inferred。
     推不到照舊 NO_DATE_COL(真的沒有日期的快照表,照實黃)。
  ② 主鍵衝突先試「第三個鍵」:同鍵不同值時,逐一試表裡的分類欄(source · vintage · realtime_start · freq · unit · country …
     以及其他文字 / 日期型別欄),加進主鍵後整表不再有同鍵不同值才採用,記 key_extended;值一個都不改、不猜。
     試不到 → 照舊 PK_CONFLICT(紅),並點名「哪幾欄在衝突列裡值不同」(只寫欄名,不寫值)。
  ③ reconcile 先把鍵對齊再比:日期欄 TRY_CAST 成 DATE;代號類鍵轉文字 · 去空白 · 大寫 · 去 .TW / .TWO 尾綴。
     兩邊都有列卻一筆都對不上 → NO_OVERLAP(黃,不冒充 OK)。
  ④ SUMMARY.json 加 tables:逐表的 group · view · state · rows(列數)· pk · pk_conflicts · key/date 推斷 · 衝突欄名;
     只有結構與計數,不含任何資料值(資料邊界)。
PR #754 Codex(兩筆,本檔未發布 · 未鎖,就地修):合成鍵改「長度:值」串接(值裡有 | 也不撞);補鍵候選先寫旁邊的試寫檔,
驗過 OK 才換上,失敗不留候選結果;SUMMARY 的 tool 寫實際跑的尾版(BASE.TAG);對核的期間鍵能轉日期才轉,
月份鍵(ym 202607)保留原值去分隔字元,不再變 NULL。
不動來源冊(FetchGroups_SSOT 是 VDF 的冊);唯讀開湖;不出網;不用 TA-Lib;不設同意閘。
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
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_ENG242_ThreePeriodDistill"
VERSION = "v0105"
TAG = f"{STEM} {VERSION}"
DATE_NAMES = ("date", "trade_date", "data_date", "as_of", "asof", "as_of_date", "snapshot_date", "report_date", "dt", "day",
              "period", "ym", "year_month", "日期", "資料日期", "交易日期", "年月")
EXT_NAMES = ("source", "src", "provider", "vintage", "realtime_start", "realtime_end", "freq", "frequency", "unit", "units",
             "country", "region", "market", "exchange", "currency", "adjust", "field", "metric", "category", "type", "kind")
SUMMARY_KEYS = ("group", "view", "state", "rows", "pk", "pk_conflicts", "renamed", "key_inferred", "key_extended",
                "date_inferred", "conflict_cols", "note", "file", "pair", "compared", "mismatch", "columns",
                "key_normalized", "a_rows", "b_rows")
EXT_TRIES = 12
_KCOL = "__vdf_k"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{PRIOR_PATH.stem}_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE                                   # v0100 本體(do_distill / main 依模組全域名叫)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _q(c) -> str:
    return '"' + str(c).replace('"', '""') + '"'


def _describe(con, rel: str) -> list:
    return [(r[0], str(r[1]).upper()) for r in con.execute(f"DESCRIBE SELECT * FROM {rel}").fetchall()]


def infer_date(cols: list, nb: dict, key_col) -> str | None:
    """cols = [(名, 型別)]。同義冊正規名 date → 常見日期欄名 → 唯一的 DATE / TIMESTAMP 欄;鍵欄不算。推不到回 None。"""
    rev = (nb or {}).get("rev") or {}
    nn = BASE.norm_name
    names = [c for c, _ in cols if c != key_col]
    for c in names:
        if rev.get(nn(c)) == "date":
            return c
    low = {nn(x): i for i, x in enumerate(DATE_NAMES)}
    hits = sorted((low[nn(c)], c) for c in names if nn(c) in low)
    if hits:
        return hits[0][1]
    typed = [c for c, t in cols if c != key_col and (t.startswith("DATE") or t.startswith("TIMESTAMP"))]
    return typed[0] if len(typed) == 1 else None


def _dup_groups(con, rel: str, keys: list) -> int:
    k = ", ".join(_q(x) for x in keys)
    return con.execute(f"SELECT count(*) FROM (SELECT {k} FROM (SELECT DISTINCT * FROM {rel}) GROUP BY ALL HAVING count(*) > 1)").fetchone()[0]


def _ext_candidates(cols: list, used: set) -> list:
    nn = BASE.norm_name
    rank = {nn(x): i for i, x in enumerate(EXT_NAMES)}
    pool = [(c, t) for c, t in cols if c not in used and c != _KCOL]
    named = sorted((rank[nn(c)], c) for c, _ in pool if nn(c) in rank)
    typed = sorted(c for c, t in pool if nn(c) not in rank and (t.startswith("VARCHAR") or t.startswith("DATE")
                                                               or t.startswith("TIMESTAMP") or t == "BOOLEAN"))
    return ([c for _, c in named] + typed)[:EXT_TRIES]


def conflict_cols(con, rel: str, keys: list, cols: list) -> list:
    """衝突鍵組裡值不同的欄名(只回欄名,不回值)。"""
    k = ", ".join(_q(x) for x in keys)
    others = [c for c, _ in cols if c not in keys and c != _KCOL]
    if not others:
        return []
    agg = ", ".join(f"max(n{i})" for i in range(len(others)))
    inner = ", ".join(f"count(DISTINCT {_q(c)}) AS n{i}" for i, c in enumerate(others))
    row = con.execute(f"SELECT {agg} FROM (SELECT {inner} FROM (SELECT DISTINCT * FROM {rel}) GROUP BY {k} HAVING count(*) > 1)").fetchone()
    return [c for c, v in zip(others, row or ()) if v and v > 1]


def key_expr(parts: list) -> str:
    """多欄合成鍵:每欄寫成「長度:值」(NULL 寫 ~)再串起來 → 不同欄值組合不會撞成同一個字串(不用分隔字元)。"""
    seg = [f"CASE WHEN {_q(x)} IS NULL THEN '~' ELSE length({_q(x)}::VARCHAR)::VARCHAR || ':' || {_q(x)}::VARCHAR END" for x in parts]
    return "concat(" + ", ".join(seg) + ")"


_ORIG = BASE.distill_one                            # = v0104 的 distill_one(標的鍵推斷 · NO_KEY)


def distill_one(con, rel: str, date_col, key_col, nb: dict, n: int, out_path: Path) -> dict:
    cols = _describe(con, rel)
    names = [c for c, _ in cols]
    d_inf = None
    if not date_col or date_col not in names:
        d_inf = infer_date(cols, nb, key_col)
        date_col = d_inf or date_col
    res = _ORIG(con, rel, date_col, key_col, nb, n, out_path)
    if d_inf and res.get("state") != "NO_DATE_COL":
        res["date_inferred"] = d_inf
    if res.get("state") != "PK_CONFLICT":
        return res
    key = res.get("key_inferred") or (key_col if key_col in names else None)
    base_keys = [x for x in (key, date_col) if x]
    for ext in _ext_candidates(cols, set(base_keys)):
        if _dup_groups(con, rel, base_keys + [ext]):
            continue
        parts = [x for x in (key, ext) if x]
        probe = out_path.with_name(out_path.name + f".{os.getpid()}.ext.probe.parquet")   # 先寫旁邊,驗過才換上
        try:
            if len(parts) == 1:
                r2 = _ORIG(con, rel, date_col, parts[0], nb, n, probe)
            else:
                sub = f"(SELECT *, {key_expr(parts)} AS {_KCOL} FROM {rel})"
                r2 = _ORIG(con, sub, date_col, _KCOL, nb, n, probe)
                if r2.get("state") == "OK" and probe.exists():
                    tmp = probe.with_name(probe.name + ".sdd_tmp")
                    con.execute(f"COPY (SELECT * EXCLUDE ({_KCOL}) FROM read_parquet('{probe.as_posix()}') ORDER BY ALL) "
                                f"TO '{tmp.as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)")
                    os.replace(tmp, probe)
                ren = BASE._canon_cols(names, nb)
                r2["pk"] = [ren.get(x, x) for x in parts + [date_col]]
                r2.pop("renamed", None)
                r2["renamed"] = {k: v for k, v in ren.items() if k != v}
            if r2.get("state") == "OK":
                if probe.exists():
                    os.replace(probe, out_path)
                r2["key_extended"] = ext
                if res.get("key_inferred"):
                    r2["key_inferred"] = res["key_inferred"]
                if d_inf:
                    r2["date_inferred"] = d_inf
                return r2
        finally:
            if probe.exists():
                probe.unlink()
    res["conflict_cols"] = conflict_cols(con, rel, base_keys, cols)
    return res


_ORIG_REC = BASE.reconcile_pair


def _norm_rel(con, rel: str, pk: list) -> tuple:
    cols = dict(_describe(con, rel))
    rep = []
    for k in pk:
        if k not in cols:
            continue
        if BASE.norm_name(k) in {BASE.norm_name(x) for x in DATE_NAMES} or cols[k].startswith(("DATE", "TIMESTAMP")):
            d = f"TRY_CAST({_q(k)} AS DATE)"                 # 能轉日期 → YYYY-MM-DD;不能(例 ym 202607)→ 原值去分隔字元,不變 NULL
            rep.append(f"CASE WHEN {d} IS NOT NULL THEN strftime({d}, '%Y-%m-%d') "
                       f"ELSE regexp_replace(trim(CAST({_q(k)} AS VARCHAR)), '[^0-9A-Za-z]', '', 'g') END AS {_q(k)}")
        else:
            rep.append(f"regexp_replace(upper(trim(CAST({_q(k)} AS VARCHAR))), '\\.(TWO|TW)$', '') AS {_q(k)}")
    sub = f"(SELECT * REPLACE ({', '.join(rep)}) FROM {rel})" if rep else rel
    return sub, con.execute(f"SELECT count(*) FROM {rel}").fetchone()[0]


def reconcile_pair(con, a_rel: str, b_rel: str, pk: list, tol: float, out_path: Path) -> dict:
    na, ra = _norm_rel(con, a_rel, pk)
    nb_, rb = _norm_rel(con, b_rel, pk)
    r = _ORIG_REC(con, na, nb_, pk, tol, out_path)
    r["key_normalized"] = True
    r["a_rows"], r["b_rows"] = ra, rb
    if r.get("state") == "OK" and not r.get("compared") and ra and rb:
        r["state"] = "NO_OVERLAP"
        r["note"] = "兩邊都有列,鍵對齊後仍一筆都對不上(代號 / 日期範圍不同)"
    return r


_ORIG_DD = BASE.do_distill


def do_distill(mod, prm: dict, nb: dict, lake: Path) -> dict:
    res = _ORIG_DD(mod, prm, nb, lake)
    bad = [r for r in res.get("reconcile") or [] if r.get("state") != "OK"]
    if bad:
        res.setdefault("counts", {})["reconcile_not_ok"] = len(bad)
        if res.get("lamp") == "GREEN":
            res["lamp"] = "YELLOW"
    return res


_ORIG_SAVE = BASE.save


def summary_tables(rows: list) -> list:
    return [{k: r[k] for k in SUMMARY_KEYS if k in r} for r in rows or [] if isinstance(r, dict)]


def save(verb: str, res: dict, root: Path = None) -> Path:
    od = _ORIG_SAVE(verb, res) if root is None else _ORIG_SAVE(verb, res, root)
    if verb in ("distill", "reconcile") and od:
        p = Path(od) / "SUMMARY.json"
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
            s["tables"] = summary_tables(res.get("rows"))
            s["tool"] = BASE.TAG                      # 實際跑的尾版(v0106 以後換裝時是它的 TAG)
            tmp = p.with_name(p.name + f".{os.getpid()}.sdd_tmp")
            tmp.write_text(json.dumps(s, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
            os.replace(tmp, p)
        except (OSError, ValueError) as exc:
            print(f"[黃] SUMMARY 逐表沒寫進去:{exc}", flush=True)
    return od


def _install():
    BASE.distill_one = distill_one
    BASE.reconcile_pair = reconcile_pair
    BASE.do_distill = do_distill
    BASE.save = save
    BASE.TAG = TAG


def _uninstall():
    BASE.distill_one = _ORIG
    BASE.reconcile_pair = _ORIG_REC
    BASE.do_distill = _ORIG_DD
    BASE.save = _ORIG_SAVE
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
    chk("已裝進 v0100 本體(distill_one · reconcile_pair · do_distill · save)· 橫幅寫本版",
        BASE.distill_one is distill_one and BASE.reconcile_pair is reconcile_pair and BASE.do_distill is do_distill
        and BASE.save is save and BASE.TAG == TAG)
    duckdb = BASE._duck()
    nb = BASE.name_book() if callable(getattr(BASE, "name_book", None)) else {"rev": {}}
    con = duckdb.connect()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        # ① 日期欄推斷(冊上 date_col 沒給)
        con.execute("CREATE TABLE chip AS SELECT * FROM (VALUES ('2026-11-24','2330',1.0),('2026-11-25','2330',2.0),"
                    "('2026-11-25','2317',3.0)) t(Date, code, margin)")
        r1 = distill_one(con, "chip", None, None, nb, 3, td / "chip.parquet")
        chk("① 冊上沒給 date_col → 推到 Date · 照常蒸餾 3 列(不再 NO_DATE_COL)",
            r1["state"] == "OK" and r1["rows"] == 3 and r1.get("date_inferred") == "Date", r1)
        con.execute("CREATE TABLE snap AS SELECT * FROM (VALUES ('A',1.0),('B',2.0)) t(etf_ticker, w)")
        r1b = distill_one(con, "snap", None, None, nb, 3, td / "snap.parquet")
        chk("① 真的沒有日期欄的快照表 → 照舊 NO_DATE_COL(照實黃,不硬猜)", r1b["state"] == "NO_DATE_COL", r1b)
        # ② 主鍵衝突:補第三個鍵
        con.execute("CREATE TABLE macro AS SELECT * FROM (VALUES ('2026-10-01','CPI','fred',1.0),('2026-10-01','CPI','bls',1.1),"
                    "('2026-11-01','CPI','fred',2.0),('2026-11-01','GDP','fred',3.0)) t(date, series, source, value)")
        r2 = distill_one(con, "macro", "date", "series", nb, 3, td / "macro.parquet")
        cols2 = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{(td / 'macro.parquet').as_posix()}')").fetchall()]
        chk("② (series, date) 同鍵不同值 → 試到 source 當第三鍵 → OK · 4 列全留 · 主鍵寫三欄 · 輸出不帶內部鍵欄",
            r2["state"] == "OK" and r2["rows"] == 4 and r2.get("key_extended") == "source" and len(r2.get("pk") or []) == 3
            and _KCOL not in cols2, (r2, cols2))
        con.execute("CREATE TABLE macro2 AS SELECT * FROM (VALUES ('2026-10-01','CPI',1.0,'x'),('2026-10-01','CPI',1.1,'x'),"
                    "('2026-11-01','CPI',2.0,'x')) t(date, series, value, note)")
        r2b = distill_one(con, "macro2", "date", "series", nb, 3, td / "macro2.parquet")
        chk("② 找不到能分開的欄 → 照舊 PK_CONFLICT(紅)· 點名衝突欄 value(只寫欄名)",
            r2b["state"] == "PK_CONFLICT" and r2b.get("conflict_cols") == ["value"] and "key_extended" not in r2b, r2b)
        con.execute("CREATE TABLE pipe AS SELECT * FROM (VALUES ('2026-10-01','a|b','c',1.0),('2026-10-01','a','b|c',2.0),"
                    "('2026-11-01','X','s1',1.0),('2026-11-01','X','s2',2.0)) t(date, series, source, value)")
        r2c = distill_one(con, "pipe", "date", "series", nb, 3, td / "pipe.parquet")
        n2c = con.execute(f"SELECT count(*) FROM read_parquet('{(td / 'pipe.parquet').as_posix()}')").fetchone()[0]
        chk("② 值裡有 | 也不撞鍵:('a|b','c') 與 ('a','b|c') 各自一列 · 補 source 後 4 列全留 · 不留試寫檔",
            r2c["state"] == "OK" and r2c["rows"] == 4 and n2c == 4 and r2c.get("key_extended") == "source"
            and not list(td.glob("*.probe.parquet")), (r2c, n2c))
        n2b = con.execute(f"SELECT count(*) FROM read_parquet('{(td / 'macro2.parquet').as_posix()}')").fetchone()[0]
        chk("② 補鍵失敗時輸出檔 = 回報的那份(列數一致,不被候選結果蓋掉)", n2b == r2b["rows"], (n2b, r2b["rows"]))
        # ③ reconcile 鍵對齊
        con.execute("CREATE TABLE pa AS SELECT * FROM (VALUES ('2330.TW', TIMESTAMP '2026-11-25 00:00:00', 100.0),"
                    "('2317.TW', TIMESTAMP '2026-11-25 00:00:00', 50.0)) t(code, date, close)")
        con.execute("CREATE TABLE pb AS SELECT * FROM (VALUES ('2330', DATE '2026-11-25', 100.0),('2317 ', DATE '2026-11-25', 51.0)) t(code, date, close)")
        _uninstall()
        try:
            r0 = BASE.reconcile_pair(con, "pa", "pb", ["code", "date"], 0.001, td / "rec0.parquet")
        finally:
            _install()
        r3 = reconcile_pair(con, "pa", "pb", ["code", "date"], 0.001, td / "rec.parquet")
        chk("③ 重現桌機:v0100 代號帶 .TW / 日期型別不同 → compared 0;本版對齊後 compared 2 · mismatch 1",
            r0.get("compared") == 0 and r3["state"] == "OK" and r3["compared"] == 2 and r3["mismatch"] == 1 and r3.get("key_normalized"), (r0, r3))
        con.execute("CREATE TABLE ma AS SELECT * FROM (VALUES ('2330','202607',10.0),('2330','202608',11.0)) t(code, ym, revenue)")
        con.execute("CREATE TABLE mb AS SELECT * FROM (VALUES ('2330','2026-07',10.0),('2330','202608',12.0)) t(code, ym, revenue)")
        r3m = reconcile_pair(con, "ma", "mb", ["code", "ym"], 0.001, td / "recm.parquet")
        chk("③ 月份鍵 ym(202607 / 2026-07)不被轉成 NULL:兩列都對上 · compared 2 · mismatch 1(不報 NO_OVERLAP)",
            r3m["state"] == "OK" and r3m["compared"] == 2 and r3m["mismatch"] == 1, r3m)
        con.execute("CREATE TABLE pc AS SELECT * FROM (VALUES ('9999', DATE '2020-01-01', 1.0)) t(code, date, close)")
        r3b = reconcile_pair(con, "pa", "pc", ["code", "date"], 0.001, td / "rec2.parquet")
        chk("③ 兩邊都有列卻一筆對不上 → NO_OVERLAP(不冒充 OK)", r3b["state"] == "NO_OVERLAP" and r3b["a_rows"] == 2, r3b)
        # ④ SUMMARY 逐表(只結構與計數)
        rows = [{"group": "G", "view": "v_x", "state": "PK_CONFLICT", "rows": 3, "pk": ["series", "date"], "pk_conflicts": 2,
                 "conflict_cols": ["value"], "secret_values": [1.23]}]
        keep_via = getattr(BASE, "VIA", None)
        od = save("distill", {"rows": rows, "lamp": "RED", "counts": {"tables": 1}}, td)
        s = json.loads((Path(od) / "SUMMARY.json").read_text(encoding="utf-8"))
        chk("④ SUMMARY.json 帶 tables 逐表(state · pk · 衝突欄名)· 不帶白名單外欄位 · 不留暫存檔",
            s.get("tables") and s["tables"][0]["state"] == "PK_CONFLICT" and s["tables"][0]["conflict_cols"] == ["value"]
            and "secret_values" not in s["tables"][0] and s.get("tool") == TAG and not list(Path(od).glob("*.sdd_tmp")), s.get("tables"))
        _ = keep_via
    con.close()
    _uninstall()
    try:
        rc = PRIOR.selftest()
    finally:
        _install()
    chk("前版 v0104 鏈自測(本版換裝卸下)照過", rc == 0, rc)
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
