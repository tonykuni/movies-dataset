#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL009_TWStockList v0104 — 薄尾(v0100–v0103 一字不改):名稱字形檢查 V10 + 前一份名單的亂碼名稱反解

2026-11-20 容器實錄:VRN 開閘整輪的 ENG049 矩陣名稱出現「жҢҜжӣң」(6143 振曜)。追到 VDF 本引擎的名單:1986 檔有 892 檔上櫃名稱是亂碼,
驗收報告卻是 GREEN —— 網路工具 http_json 吃了 requests 猜的字集(ptcp154 / cp1256)。網路工具已出 SUP_MDL740_NetUnified v0120
(先位元組再自己解碼),重抓後當天的列已全是正字;但「增量維護」會把前一份名單的列帶過來(例:8291 尚茂今天不在報價表 → 標 DELISTED,
名稱沿用前一份的亂碼)。本版:
  ① 讀前一份名單時,名稱欄(name · name_en)逐列做可逆反解(單位元組字集 → UTF-8,只在反解後出現中日韓字、原字串沒有時才換)。
  ② 驗收加 V10「名稱字形」:最後要寫出的每一列,名稱不得含西里爾 / 阿拉伯 / 製表符 / 拉丁補充區的亂碼特徵;有一列 → RED(不寫入)並逐檔點名。
  ③ fixnames [--data-home 夾] [--apply]:已入庫的亂碼名稱就地反解(DuckDB 名單表 + 每日 parquet + latest csv),乾跑只數;--apply 先整份備份再寫,寫後再驗。
其餘(抓取 · 補欄 · ISIN · 日差 · DuckDB 增量)全部照 v0103。This file does not fetch on import.
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

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_MDL009_TWStockList"


def _vnum_v0104(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0104(p) < _vnum_v0104(__file__)), key=_vnum_v0104)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
P1 = PRIOR.P1                                          # v0101(run_v0101 所在;它的全域決定 run 叫誰)
for _n, _v in vars(PRIOR).items():                     # 前版公開名稱全數轉接(TAILAPI)
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v

TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
NAME_FIELDS_V0104 = ("name", "name_en")
MOJIBAKE_CODECS_V0104 = ("ptcp154", "cp1251", "cp1256", "cp1252", "latin-1", "koi8_r", "cp866", "cp1253", "cp1254", "cp1255", "cp1257", "mac_roman")
_CJK_V0104 = re.compile(r"[㐀-鿿豈-﫿]")
GARBLED_V0104 = re.compile(r"[Ѐ-ӿ؀-ۿ─-╿À-ÿ�]")
_ORIG_LOAD_PREV_V0104 = P1.load_previous_v0100
_ORIG_VERIFY_V0104 = P1.verify_v0101                   # = v0103 的 verify_v0103(v0103 已接線)
_STAT_V0104 = {"prev_fixed": 0, "prev_rows": 0}


def unmojibake_v0104(s):
    """回 (正字, 字集);不是可逆亂碼就 (原字, None)。英數 / 正常中文 / 西文重音字不動。"""
    if not isinstance(s, str) or not s or s.isascii() or _CJK_V0104.search(s):
        return s, None
    for enc in MOJIBAKE_CODECS_V0104:
        try:
            fixed = s.encode(enc).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if _CJK_V0104.search(fixed):
            return fixed, enc
    return s, None


def load_previous_v0104(out_root, out_dir, stem) -> list:
    rows = _ORIG_LOAD_PREV_V0104(out_root, out_dir, stem)
    fixed = 0
    for r in rows:
        for f in NAME_FIELDS_V0104:
            new, enc = unmojibake_v0104(r.get(f))
            if enc:
                r[f] = new
                fixed += 1
    _STAT_V0104.update(prev_fixed=fixed, prev_rows=len(rows))
    return rows


def garbled_v0104(rows) -> list:
    return [f"{r.get('ticker')} {r.get(f)}" for r in rows or [] for f in NAME_FIELDS_V0104
            if isinstance(r.get(f), str) and GARBLED_V0104.search(r.get(f)) and not _CJK_V0104.search(r.get(f))]


def verify_v0104(rows, rejected, states, prev, day, mins, zone) -> dict:
    v = _ORIG_VERIFY_V0104(rows, rejected, states, prev, day, mins, zone)
    final = (v.get("diff") or {}).get("rows") or rows
    bad = garbled_v0104(final)
    v["checks"].append({"id": "V10", "name": "名稱字形(無亂碼)", "lamp": "RED" if bad else "GREEN",
                        "note": (f"亂碼 {len(bad)} 列:{bad[:12]}" if bad else f"寫出 {len(final)} 列名稱全為正字")
                                + f" · 前一份名單反解 {_STAT_V0104['prev_fixed']} 格 / {_STAT_V0104['prev_rows']} 列"})
    v["lamp"] = PRIOR.lamp_v0100(v["checks"])
    return v


def _wire_v0104(on: bool) -> None:
    if on:
        P1.load_previous_v0100 = load_previous_v0104
        P1.verify_v0101 = verify_v0104
    else:
        P1.load_previous_v0100 = _ORIG_LOAD_PREV_V0104
        P1.verify_v0101 = _ORIG_VERIFY_V0104


_wire_v0104(True)


LIST_DIRS_V0104 = ("0-1-TWStockList", "0-2-ActiveETFList")
LIST_STEMS_V0104 = {"0-1-TWStockList": "tw_stock_list", "0-2-ActiveETFList": "active_etf_list"}
DB_TABLES_V0104 = ("tw_stock_list", "tw_active_etf_list")


def fixnames_v0104(out_root, apply: bool = False) -> dict:
    """已入庫的亂碼名稱就地反解(增量維護,不重抓):DuckDB 名單表 + 每日 parquet + latest csv。
    乾跑只數;--apply 先把要動的檔整份備份到 <資料家>/_backup/fixnames_<UTC>/,再寫(parquet / csv 暫存檔 + 原子換檔)。"""
    import os
    import shutil
    import tempfile
    from datetime import datetime, timezone
    import pandas as pd
    root = Path(out_root)
    rep = {"root": str(root), "apply": apply, "files": [], "db": {}, "backup": None, "left": 0}
    targets = [f for d in LIST_DIRS_V0104 for f in sorted((root / d).glob("*.parquet")) + sorted((root / d).glob("*.csv"))]
    db = root / "vdf_master_lists.duckdb"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bdir = root / "_backup" / f"fixnames_{stamp}"

    ref = {}                                           # 位元組已丟、反解不回 → 用最新一份正字名單同代號的名稱(當日官方報價表)
    for d in LIST_DIRS_V0104:
        lp = root / d / f"{LIST_STEMS_V0104[d]}_latest.parquet"
        if lp.is_file():
            for r in pd.read_parquet(lp).to_dict("records"):
                for f in NAME_FIELDS_V0104:
                    v = r.get(f)
                    if isinstance(v, str) and v and not garbled_v0104([{"ticker": "", f: v}]):
                        ref[(str(r.get("ticker")), f)] = v
    rep["ref_names"] = len(ref)
    rep["ref_filled"] = 0

    def fix_one(val, ticker, f):
        new, enc = unmojibake_v0104(val)
        if not enc and isinstance(val, str) and garbled_v0104([{"ticker": "", f: val}]) and (str(ticker), f) in ref:
            rep["ref_filled"] += 1
            return ref[(str(ticker), f)]
        return new

    def fix_df(df):
        n = 0
        for f in NAME_FIELDS_V0104:
            if f in df.columns:
                tick = df["ticker"] if "ticker" in df.columns else [""] * len(df)
                new = pd.Series([fix_one(x, t, f) if isinstance(x, str) else x for x, t in zip(df[f], tick)], index=df.index)
                n += int((new != df[f]).sum())
                df[f] = new
        return n
    plan = []
    for f in targets:
        df = pd.read_csv(f, dtype=str, keep_default_na=False, encoding="utf-8-sig") if f.suffix == ".csv" else pd.read_parquet(f)
        n = fix_df(df)
        rep["files"].append({"file": str(f.relative_to(root)), "fixed": n})
        if n:
            plan.append((f, df))
    db_fix = {}
    if db.is_file():
        import duckdb
        con = duckdb.connect(str(db), read_only=True)
        try:
            have = {r[0] for r in con.execute("select table_name from information_schema.tables").fetchall()}
            for t in DB_TABLES_V0104:
                if t not in have:
                    continue
                cols = {r[0] for r in con.execute(f"select column_name from information_schema.columns where table_name = '{t}'").fetchall()}
                for f in NAME_FIELDS_V0104:
                    if f not in cols:
                        continue
                    pairs = []
                    tcol = "ticker" if "ticker" in cols else None
                    q = f'select "{f}", {tcol or "null"}, count(*) from {t} group by 1, 2'
                    for (val, tk, cnt) in con.execute(q).fetchall():
                        new = fix_one(val, tk, f) if isinstance(val, str) else val
                        if new != val:
                            pairs.append((new, val, tk, cnt))
                    if pairs:
                        db_fix[(t, f)] = pairs
                        rep["db"][f"{t}.{f}"] = sum(c for *_, c in pairs)
        finally:
            con.close()
    if apply and (plan or db_fix):
        bdir.mkdir(parents=True, exist_ok=True)
        rep["backup"] = str(bdir)
        for f, _ in plan:
            dst = bdir / f.relative_to(root)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst)
        if db_fix:
            shutil.copy2(db, bdir / db.name)
        for f, df in plan:
            fd, tmp = tempfile.mkstemp(prefix=f.stem + ".", suffix=f.suffix + ".tmp", dir=str(f.parent))
            os.close(fd)
            if f.suffix == ".csv":
                df.to_csv(tmp, index=False, encoding="utf-8-sig")
            else:
                df.to_parquet(tmp, index=False)
            os.replace(tmp, f)
        if db_fix:
            import duckdb
            con = duckdb.connect(str(db))
            try:
                con.execute("begin")
                for (t, f), pairs in db_fix.items():
                    if "ticker" in {r[0] for r in con.execute(f"select column_name from information_schema.columns where table_name = '{t}'").fetchall()}:
                        con.executemany(f'update {t} set "{f}" = ? where "{f}" = ? and ticker = ?', [(new, old, tk) for new, old, tk, _ in pairs])
                    else:
                        con.executemany(f'update {t} set "{f}" = ? where "{f}" = ?', [(new, old) for new, old, _, _ in pairs])
                con.execute("commit")
            finally:
                con.close()
    left = 0
    if apply:
        for f in targets:
            df = pd.read_csv(f, dtype=str, keep_default_na=False, encoding="utf-8-sig") if f.suffix == ".csv" else pd.read_parquet(f)
            left += len(garbled_v0104(df.to_dict("records")))
        if db.is_file():
            import duckdb
            con = duckdb.connect(str(db), read_only=True)
            try:
                have = {r[0] for r in con.execute("select table_name from information_schema.tables").fetchall()}
                for t in DB_TABLES_V0104:
                    if t in have:
                        left += len(garbled_v0104(con.execute(f"select * from {t}").fetchdf().to_dict("records")))
            finally:
                con.close()
    rep["left"] = left
    rep["fixed_files"] = sum(x["fixed"] for x in rep["files"])
    rep["fixed_db"] = sum(rep["db"].values())
    return rep


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if args[:1] == ["fixnames"]:
        root = args[args.index("--data-home") + 1] if "--data-home" in args else Path.cwd()
        if "--apply" in args and not entry_ok_v0100():
            print(f"[{TAG}] fixnames --apply 拒跑:沒有總控入口(VIA_FROM_VDFSM / VIA_FROM_VCGC)· 零寫入")
            return 2
        if not Path(root).is_dir():
            print(f"[{TAG}] fixnames 拒跑:資料家不存在 {root}(零寫入)")
            return 1
        r = fixnames_v0104(Path(root).resolve(), apply="--apply" in args)
        print(f"[{TAG}] fixnames {'寫入' if r['apply'] else '乾跑'} · 資料家 {r['root']} · 檔 {r['fixed_files']} 格 · 庫 {r['fixed_db']} 列 {r['db']}"
              + f" · 其中位元組已丟、以最新正字名單同代號補 {r['ref_filled']} 格" + (f" · 備份 {r['backup']}" if r["backup"] else "") + (f" · 寫後剩亂碼 {r['left']}" if r["apply"] else " · 加 --apply 才寫(先整份備份)"))
        for x in r["files"]:
            if x["fixed"]:
                print(f"  {x['file']} · {x['fixed']} 格")
        return 0 if (not r["apply"] or r["left"] == 0) else 1
    PRIOR.TAG = TAG
    rc = PRIOR.main(args)
    P1.TAG = PRIOR.TAG = TAG
    return rc


def selftest() -> int:
    import tempfile
    ok = []

    def ck(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:240]) if note and not cond else ''}", flush=True)

    print(f"=== {TAG} 薄尾自測(名稱字形 V10 · 前一份名單反解;零網路)===", flush=True)
    good = [("6143", "振曜"), ("1240", "茂生農經"), ("8291", "尚茂"), ("00400A", "主動國泰動能高息")]
    for (code, zh), enc in zip(good, ("ptcp154", "ptcp154", "ptcp154", "cp1256")):
        g = zh.encode("utf-8").decode(enc)
        ck(f"① 反解 {code} {g} → {zh}({enc})", unmojibake_v0104(g) == (zh, enc), unmojibake_v0104(g))
    ck("② 不亂改:正常中文 · 英數 · 西文重音字", all(unmojibake_v0104(s)[1] is None for s in ("台積電", "TSMC 2330", "Société", "")))
    import pandas as pd
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "0-1-TWStockList"
        d.mkdir()
        pd.DataFrame([{"ticker": "8291", "name": "尚茂".encode("utf-8").decode("ptcp154"), "name_en": "", "market": "TPEX"},
                      {"ticker": "2330", "name": "台積電", "name_en": "TSMC", "market": "TWSE"}]).to_parquet(d / "tw_stock_list_latest.parquet", index=False)
        prev = P1.load_previous_v0100(Path(td), "0-1-TWStockList", "tw_stock_list")
        ck("③ run 讀前一份名單走本版:8291 名稱反解成「尚茂」· 2330 不動 · 計數 1", [r["name"] for r in prev] == ["尚茂", "台積電"] and _STAT_V0104["prev_fixed"] == 1, prev)
    ck("④ V10 抓亂碼:西里爾 / 阿拉伯 / 製表符特徵點名;正字 · 英數 · 空名不誤報",
       garbled_v0104([{"ticker": "6143", "name": "жҢҜжӣң"}, {"ticker": "00401A", "name": "ن¸»ه‹•"}, {"ticker": "2330", "name": "台積電", "name_en": "TSMC"}, {"ticker": "1", "name": ""}]) == ["6143 жҢҜжӣң", "00401A ن¸»ه‹•"])
    calls = {}

    def fake_verify(rows, rejected, states, prev, day, mins, zone):
        calls["n"] = 1
        return {"checks": [{"id": "V1", "lamp": "GREEN"}], "diff": {"rows": rows}, "lamp": "GREEN"}
    keep = globals()["_ORIG_VERIFY_V0104"]
    globals()["_ORIG_VERIFY_V0104"] = fake_verify
    try:
        v_bad = verify_v0104([{"ticker": "6143", "name": "жҢҜжӣң"}], [], {}, [], "2026-11-20", {}, [])
        v_ok = verify_v0104([{"ticker": "6143", "name": "振曜"}], [], {}, [], "2026-11-20", {}, [])
    finally:
        globals()["_ORIG_VERIFY_V0104"] = keep
    ck("⑤ 驗收:有亂碼 → V10 RED · 總燈 RED(不寫入);全正字 → GREEN", v_bad["lamp"] == "RED" and v_bad["checks"][-1]["id"] == "V10" and v_ok["lamp"] == "GREEN", (v_bad["lamp"], v_ok["lamp"]))
    ck("⑥ 接線:v0101 的 run 叫的是本版讀前份 / 驗收", P1.load_previous_v0100 is load_previous_v0104 and P1.verify_v0101 is verify_v0104)
    src = Path(__file__).read_text(encoding="utf-8")
    ck("⑦ 加速器橋 + 網路橋真的匯入 · 不碰 TA-Lib · 不設同意閘 · 不含本機路徑",
       "import VIA_SuperAccel_Module as VIA_ACCEL" in src and "[VIA:NET-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
       and not re.search(r"environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src) and ("C:" + "\\Users") not in src)
    with tempfile.TemporaryDirectory() as td:
        import duckdb
        root = Path(td)
        (root / "0-1-TWStockList").mkdir()
        g = "振曜".encode("utf-8").decode("ptcp154")
        df = pd.DataFrame([{"date": "2026-11-19", "ticker": "6143", "name": g, "name_en": ""}, {"date": "2026-11-19", "ticker": "2330", "name": "台積電", "name_en": "TSMC"},
                           {"date": "2026-11-19", "ticker": "1813", "name": "еҜ¶еҲ©еҫ", "name_en": ""}])
        pd.DataFrame([{"date": "2026-11-20", "ticker": "1813", "name": "寶利徠", "name_en": ""}]).to_parquet(root / "0-1-TWStockList" / "tw_stock_list_latest.parquet", index=False)
        df.to_parquet(root / "0-1-TWStockList" / "tw_stock_list_2026-11-19.parquet", index=False)
        df.to_csv(root / "0-1-TWStockList" / "tw_stock_list_latest.csv", index=False, encoding="utf-8-sig")
        con = duckdb.connect(str(root / "vdf_master_lists.duckdb"))
        con.execute("create table tw_stock_list as select * from df")
        con.close()
        dry = fixnames_v0104(root, apply=False)
        still = pd.read_parquet(root / "0-1-TWStockList" / "tw_stock_list_2026-11-19.parquet")["name"].tolist()[0] == g
        wet = fixnames_v0104(root, apply=True)
        con = duckdb.connect(str(root / "vdf_master_lists.duckdb"), read_only=True)
        dbn = con.execute("select name from tw_stock_list order by ticker desc").fetchall()
        dbn = [x for x in dbn if x != ("寶利徠",)] if ("寶利徠",) in dbn else dbn + [("缺 1813",)]
        con.close()
        bk = Path(wet["backup"] or "")
        ck("⑨ fixnames:乾跑只數不寫(檔 4 格 · 庫 2 列;位元組已丟的 1813 以最新正字名單同代號補)· --apply 先整份備份(3 檔)再寫 · 庫與 parquet / csv 都成正字 · 寫後剩亂碼 0 · 正字列不動",
           dry["fixed_files"] == 4 and dry["fixed_db"] == 2 and still and wet["left"] == 0 and dbn == [("振曜",), ("台積電",)]
           and bk.is_dir() and len([p for p in bk.rglob("*") if p.is_file()]) == 3
           and pd.read_parquet(root / "0-1-TWStockList" / "tw_stock_list_2026-11-19.parquet")["name"].tolist() == ["振曜", "台積電", "寶利徠"], (dry, wet, dbn))
        again = fixnames_v0104(root, apply=True)
        ck("⑩ 再跑一次 = 零改動、不再備份(增量不重工)", again["fixed_files"] == 0 and again["fixed_db"] == 0 and again["backup"] is None, again)
    _wire_v0104(False)
    try:
        rc = PRIOR.main(["--selftest"])
    finally:
        _wire_v0104(True)
    ck(f"⑧ 前版 {PRIOR_PATH.stem} 自測照過(跑前拆本版接線,跑完接回)", rc == 0, f"rc {rc}")
    print(f"[計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
