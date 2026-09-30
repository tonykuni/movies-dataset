#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL249_DataFrameLock v0100 — 輸出表頭定案 → DataFrame 鎖定(輸出即驗證即結果驗證)
操作員(R34,2026-09-30):「將輸出 HEADER 檢視定案後建立 DATAFRAME 鎖定 以 DATAFRAME 中資料的輸出即驗證即結果驗證為範圍目標不發散」
正本:VIA_Output_Header_SSOT 尾版(每張輸出表:子系統 · 正主引擎 · 來源〔duckdb / parquet / csv / json〕· 欄位〔名 · 型別 · 必填 · 主鍵〕· 最少列數)。
本支只讀資料:把每張表載成 pandas DataFrame,逐項核:
  欄位 = 表頭(缺必填欄 = RED;多出冊上沒有的欄 = YELLOW,表頭沒定案)· 型別可轉 · 必填不空 · 主鍵不重複 · 列數 ≥ 最少列數;
  來源不在 = NODATA(照實,不冒充綠)。
動詞:
  plan                     列每張表:來源在不在、欄數、主鍵(不讀資料)
  check [--table id] [--data-home 夾] [--json]   載入 + 核 → VIA_Reports/dataframe_lock/DFLOCK_latest.json;全綠 rc 0 · 有黃 / NODATA rc 2 · 有紅 rc 1
  lock [--apply]           只把 check 綠的表寫進鎖帳 VIA_DataFrame_Lock_Ledger_v0100.jsonl(只增:表 · 表頭指紋 · 列數 · 主鍵數 · 資料指紋 · 時間 · 輪號);
                           同一張表的表頭指紋換了而冊沒出新版 = 拒寫(表頭鎖死;要改先出冊新版)
  --selftest               暫存夾造 duckdb / parquet / csv 三種來源,驗全部判法
來源路徑:path 可含 ${VIA_DATA_HOME} · ${VIA} · 環境變數;db_env 指名的環境變數優先。VIA_FROM_VCGC:只收 VCGC 呼叫。不用 TA-Lib。
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

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENGINE = Path(__file__).stem
BOOK_GLOB = "VIA_Output_Header_SSOT_v*.json"
LEDGER = HERE / "VIA_DataFrame_Lock_Ledger_v0100.jsonl"
OUT = VIA / "VIA_Reports" / "dataframe_lock"
DTYPES = ("str", "int", "float", "date", "datetime", "bool")


def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


def book_path(folder: Path = HERE) -> Path | None:
    hits = sorted(folder.glob(BOOK_GLOB), key=_vnum)
    return hits[-1] if hits else None


def load_book(p: Path | None = None) -> dict:
    p = p or book_path()
    if not p or not p.is_file():
        return {"tables": {}, "_path": None}
    d = json.loads(p.read_text(encoding="utf-8"))
    d["_path"] = str(p)
    return d


def header_sha(spec: dict) -> str:
    cols = [(c.get("name"), c.get("dtype"), bool(c.get("required")), bool(c.get("key"))) for c in spec.get("columns") or []]
    return hashlib.sha256(json.dumps(cols, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def resolve_source(src: dict, data_home: str | None = None) -> Path | None:
    env = src.get("db_env")
    if env and os.environ.get(env):
        return Path(os.environ[env])
    raw = str(src.get("path") or "")
    if not raw:
        return None
    home = data_home or os.environ.get("VIA_DATA_HOME") or ""
    raw = raw.replace("${VIA_DATA_HOME}", home).replace("${VIA}", str(VIA))
    raw = os.path.expandvars(raw)
    p = Path(raw)
    return p if p.is_absolute() else (VIA / p)


def load_frame(src: dict, path: Path):
    """The table as a pandas DataFrame (read only)."""
    import pandas as pd
    kind = src.get("kind")
    if kind == "duckdb":
        import duckdb
        con = duckdb.connect(str(path), read_only=True)
        try:
            return con.execute(f'SELECT * FROM "{src["table"]}"').df()
        finally:
            con.close()
    if kind == "parquet":
        return pd.read_parquet(path)
    if kind == "csv":
        return pd.read_csv(path, dtype=str, keep_default_na=False)
    if kind == "json":
        d = json.loads(path.read_text(encoding="utf-8"))
        for k in [x for x in str(src.get("table") or "").split(".") if x]:
            d = d.get(k) if isinstance(d, dict) else d
        return pd.DataFrame(d if isinstance(d, list) else [])
    raise ValueError(f"unknown source kind {kind!r}")


def _castable(series, dtype: str) -> int:
    """How many non-empty values fail to parse as dtype."""
    import pandas as pd
    s = series[series.notna() & (series.astype(str).str.strip() != "")]
    if dtype == "str" or s.empty:
        return 0
    if dtype in ("int", "float"):
        bad = pd.to_numeric(s, errors="coerce").isna()
        if dtype == "int" and not bad.all():
            num = pd.to_numeric(s, errors="coerce")
            bad = bad | ((num.notna()) & (num % 1 != 0))
        return int(bad.sum())
    if dtype in ("date", "datetime"):
        return int(pd.to_datetime(s.astype(str), errors="coerce").isna().sum())
    if dtype == "bool":
        return int((~s.astype(str).str.lower().isin(["true", "false", "1", "0", "yes", "no", "y", "n"])).sum())
    return 0


def check_table(tid: str, spec: dict, data_home: str | None = None, frame=None) -> dict:
    src = spec.get("source") or {}
    row = {"table": tid, "subsystem": spec.get("subsystem"), "owner": spec.get("owner"), "header_sha": header_sha(spec),
           "lamp": "GREEN", "problems": [], "rows": None, "source": None}
    if frame is None:
        path = resolve_source(src, data_home)
        row["source"] = str(path) if path else None
        if not path or not path.exists():
            row.update(lamp="NODATA", problems=[f"來源不在:{path or '(沒有 path / db_env)'}"])
            return row
        try:
            frame = load_frame(src, path)
        except Exception as exc:
            row.update(lamp="NODATA" if "Catalog Error" in str(exc) or "does not exist" in str(exc) else "RED",
                       problems=[f"載不進 DataFrame:{type(exc).__name__}: {str(exc)[:160]}"])
            return row
    cols = [c for c in spec.get("columns") or [] if c.get("name")]
    names = [c["name"] for c in cols]
    have = [str(c) for c in frame.columns]
    miss_req = [c["name"] for c in cols if c.get("required") and c["name"] not in have]
    miss_opt = [c["name"] for c in cols if not c.get("required") and c["name"] not in have]
    extra = [c for c in have if c not in names]
    red, yellow = [], []
    if miss_req:
        red.append(f"缺必填欄 {miss_req[:8]}")
    if miss_opt:
        yellow.append(f"缺非必填欄 {miss_opt[:8]}")
    if extra:
        yellow.append(f"多出冊上沒有的欄(表頭未定案){extra[:8]}")
    for c in cols:
        n = c["name"]
        if n not in have:
            continue
        if c.get("dtype") not in DTYPES:
            red.append(f"{n}:冊上型別 {c.get('dtype')!r} 不在 {DTYPES}")
            continue
        bad = _castable(frame[n], c["dtype"])
        if bad:
            red.append(f"{n}:{bad} 筆不是 {c['dtype']}")
        if c.get("required"):
            empty = int((frame[n].isna() | (frame[n].astype(str).str.strip() == "")).sum())
            if empty:
                red.append(f"{n}:必填但 {empty} 筆空")
    keys = [c["name"] for c in cols if c.get("key") and c["name"] in have]
    if keys:
        dup = int(frame.duplicated(subset=keys).sum())
        if dup:
            red.append(f"主鍵 {keys} 重複 {dup} 筆")
    n_rows = int(len(frame))
    if n_rows < int(spec.get("min_rows") or 0):
        red.append(f"列數 {n_rows} < 最少 {spec.get('min_rows')}")
    row["rows"] = n_rows
    row["keys"] = keys
    row["data_sha"] = hashlib.sha256(frame.sort_values(by=keys or list(frame.columns[:1])).to_csv(index=False).encode("utf-8")).hexdigest()[:16] \
        if n_rows else ""
    row["problems"] = red + yellow
    row["lamp"] = "RED" if red else "YELLOW" if yellow else "GREEN"
    return row


def check(only: str | None = None, data_home: str | None = None, book: dict | None = None, write: bool = True) -> dict:
    book = book or load_book()
    rows = [check_table(tid, spec, data_home) for tid, spec in sorted((book.get("tables") or {}).items()) if not only or tid == only]
    lamps = {r["lamp"] for r in rows}
    verdict = "RED" if "RED" in lamps else "YELLOW" if lamps & {"YELLOW", "NODATA"} or not rows else "GREEN"
    rep = {"engine": ENGINE, "book": book.get("_path"), "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "run": os.environ.get("VIA_HUB_RUN", ""), "verdict": verdict, "tables": rows}
    if write:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "DFLOCK_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return rep


def read_ledger(path: Path = LEDGER) -> list:
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def lock(apply: bool = False, rep: dict | None = None, ledger: Path = LEDGER, book: dict | None = None) -> dict:
    book = book or load_book()
    rep = rep or check(book=book, write=False)
    prev = {}
    for e in read_ledger(ledger):
        prev[e["table"]] = e
    new, refused = [], []
    for r in rep["tables"]:
        if r["lamp"] != "GREEN":
            continue
        p = prev.get(r["table"])
        if p and p.get("header_sha") != r["header_sha"] and p.get("book") == Path(str(book.get("_path"))).name:
            refused.append(f"{r['table']}:表頭指紋 {p['header_sha']} → {r['header_sha']},冊沒出新版(表頭鎖死)")
            continue
        if p and p.get("header_sha") == r["header_sha"] and p.get("data_sha") == r.get("data_sha"):
            continue                              # 同表頭 · 同資料 = 已鎖,不重寫
        new.append({"table": r["table"], "subsystem": r["subsystem"], "owner": r["owner"], "header_sha": r["header_sha"],
                    "rows": r["rows"], "keys": r.get("keys"), "data_sha": r.get("data_sha"),
                    "book": Path(str(book.get("_path"))).name, "at": rep["at"], "run": rep.get("run"), "by": ENGINE})
    if apply and new:
        with ledger.open("a", encoding="utf-8") as f:
            for e in new:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return {"new": new, "refused": refused, "applied": bool(apply and new)}


def plan(book: dict | None = None, data_home: str | None = None) -> list:
    book = book or load_book()
    out = []
    for tid, spec in sorted((book.get("tables") or {}).items()):
        p = resolve_source(spec.get("source") or {}, data_home)
        out.append({"table": tid, "subsystem": spec.get("subsystem"), "owner": spec.get("owner"), "kind": (spec.get("source") or {}).get("kind"),
                    "source": str(p) if p else None, "exists": bool(p and p.exists()), "columns": len(spec.get("columns") or []),
                    "keys": [c["name"] for c in spec.get("columns") or [] if c.get("key")], "header_sha": header_sha(spec)})
    return out


def _arg(a: list, key: str) -> str | None:
    if key in a:
        i = a.index(key)
        return a[i + 1] if i + 1 < len(a) else None
    return None


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    verb = a[0] if a else "check"
    home = _arg(a, "--data-home")
    if verb == "plan":
        rows = plan(data_home=home)
        print(f"[DataFrame 鎖 · plan] 冊 {load_book().get('_path')} · 表 {len(rows)}")
        for r in rows:
            print(f"  {'在' if r['exists'] else '不在':<3} {r['table']:<24} {r['subsystem'] or '':<5} {r['kind'] or '':<8} 欄 {r['columns']:<3} 鍵 {r['keys']} · {r['source']}")
        return 0
    if verb == "check":
        rep = check(_arg(a, "--table"), home)
        if "--json" in a:
            print(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
        print(f"[DataFrame 鎖 · check] {rep['verdict']} · 表 {len(rep['tables'])} · " +
              " · ".join(f"{k} {sum(1 for r in rep['tables'] if r['lamp'] == k)}" for k in ("GREEN", "YELLOW", "NODATA", "RED")))
        for r in rep["tables"]:
            print(f"  {r['lamp']:<7} {r['table']:<24} 列 {r['rows']} · {'; '.join(r['problems'])[:160]}")
        return {"GREEN": 0, "YELLOW": 2, "RED": 1}[rep["verdict"]]
    if verb == "lock":
        res = lock("--apply" in a)
        print(f"[DataFrame 鎖 · lock] 新鎖 {len(res['new'])} · 拒寫 {len(res['refused'])} · {'已寫 ' + LEDGER.name if res['applied'] else '乾跑(--apply 才寫)'}")
        for x in res["refused"]:
            print(f"  [拒寫] {x}")
        return 1 if res["refused"] else 0
    print("  用法:plan | check [--table id] [--data-home 夾] [--json] | lock [--apply] | --selftest")
    return 2


def selftest() -> int:
    import shutil
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")
    try:
        import pandas as pd
    except ImportError:
        print("  [ABSENT] pandas 不在(不裝套件);自測無法量")
        return 2
    tmp = Path(tempfile.mkdtemp(prefix="via_dflock_"))
    try:
        rows = [{"code": "2330", "name": "台積電", "market": "TWSE", "status": "ACTIVE"},
                {"code": "6488", "name": "環球晶", "market": "TPEX", "status": "ACTIVE"}]
        pd.DataFrame(rows).to_csv(tmp / "list.csv", index=False)
        pd.DataFrame([{"date": "2026-09-30", "etf_ticker": "00980A", "aum": 1.5e10, "nav": 10.2}]).to_parquet(tmp / "m.parquet")
        have_duck = True
        try:
            import duckdb
            con = duckdb.connect(str(tmp / "t.duckdb"))
            con.execute("CREATE TABLE holdings(etf_ticker VARCHAR, holding_ticker VARCHAR, weight_pct DOUBLE)")
            con.execute("INSERT INTO holdings VALUES ('00980A','2330',9.5),('00980A','2330',1.0)")
            con.close()
        except ImportError:
            have_duck = False
        book = {"_path": str(tmp / "VIA_Output_Header_SSOT_v0100.json"), "tables": {
            "tw_list": {"subsystem": "VDF", "owner": "X", "source": {"kind": "csv", "path": str(tmp / "list.csv")},
                        "columns": [{"name": "code", "dtype": "str", "required": True, "key": True},
                                    {"name": "name", "dtype": "str", "required": True},
                                    {"name": "market", "dtype": "str", "required": True},
                                    {"name": "status", "dtype": "str", "required": True}], "min_rows": 2},
            "etf_metrics": {"subsystem": "VDF", "owner": "Y", "source": {"kind": "parquet", "path": "${VIA_DATA_HOME}/m.parquet"},
                            "columns": [{"name": "date", "dtype": "date", "required": True, "key": True},
                                        {"name": "etf_ticker", "dtype": "str", "required": True, "key": True},
                                        {"name": "aum", "dtype": "float", "required": True},
                                        {"name": "nav", "dtype": "float", "required": True},
                                        {"name": "net_flow_value", "dtype": "float", "required": True}], "min_rows": 1},
            "gone": {"subsystem": "VRN", "owner": "Z", "source": {"kind": "csv", "path": str(tmp / "nope.csv")}, "columns": [{"name": "a", "dtype": "str"}]}}}
        if have_duck:
            book["tables"]["holdings"] = {"subsystem": "VDF", "owner": "W", "source": {"kind": "duckdb", "path": str(tmp / "t.duckdb"), "table": "holdings"},
                                          "columns": [{"name": "etf_ticker", "dtype": "str", "required": True, "key": True},
                                                      {"name": "holding_ticker", "dtype": "str", "required": True, "key": True},
                                                      {"name": "weight_pct", "dtype": "float", "required": True}]}
        rep = check(book=book, data_home=str(tmp), write=False)
        by = {r["table"]: r for r in rep["tables"]}
        chk("欄位 = 表頭 · 型別 · 必填 · 主鍵 · 列數全對 = GREEN", by["tw_list"]["lamp"] == "GREEN" and by["tw_list"]["rows"] == 2)
        chk("缺必填欄(net_flow_value)= RED,並點名", by["etf_metrics"]["lamp"] == "RED" and "net_flow_value" in " ".join(by["etf_metrics"]["problems"]))
        chk("${VIA_DATA_HOME} 路徑展開到資料家", by["etf_metrics"]["source"] and by["etf_metrics"]["source"].startswith(str(tmp)))
        chk("來源不在 = NODATA(不冒充綠)", by["gone"]["lamp"] == "NODATA")
        if have_duck:
            chk("duckdb 來源:主鍵重複 = RED", by["holdings"]["lamp"] == "RED" and "重複" in " ".join(by["holdings"]["problems"]))
        df_extra = pd.DataFrame(rows).assign(extra_col=1)
        chk("多出冊上沒有的欄 = YELLOW(表頭未定案)", check_table("tw_list", book["tables"]["tw_list"], frame=df_extra)["lamp"] == "YELLOW")
        df_bad = pd.DataFrame([{"date": "not-a-date", "etf_ticker": "A", "aum": "x", "nav": 1, "net_flow_value": 0}])
        r_bad = check_table("etf_metrics", book["tables"]["etf_metrics"], frame=df_bad)
        chk("型別不符(date · float)= RED", r_bad["lamp"] == "RED" and "date" in " ".join(r_bad["problems"]) and "aum" in " ".join(r_bad["problems"]))
        chk("總判取最差(有紅 = RED)", rep["verdict"] == "RED")
        led = tmp / "ledger.jsonl"
        res1 = lock(apply=True, rep=rep, ledger=led, book=book)
        chk("lock 只寫綠的表(tw_list)", [e["table"] for e in res1["new"]] == ["tw_list"] and len(read_ledger(led)) == 1)
        res2 = lock(apply=True, rep=rep, ledger=led, book=book)
        chk("同表頭同資料 = 已鎖不重寫", not res2["new"] and len(read_ledger(led)) == 1)
        book2 = json.loads(json.dumps(book))
        book2["tables"]["tw_list"]["columns"][3]["required"] = False   # 同一本冊、表頭改了(資料仍全綠)
        rep2 = check(book=book2, data_home=str(tmp), write=False)
        res3 = lock(apply=True, rep=rep2, ledger=led, book=book2)
        chk("表頭指紋變了而冊沒出新版 = 拒寫(表頭鎖死)", res3["refused"] and len(read_ledger(led)) == 1)
        chk("plan 列來源在不在與主鍵", {r["table"]: r["exists"] for r in plan(book=book, data_home=str(tmp))}["gone"] is False)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("帶加速器橋 · VIA_FROM_VCGC 標記 · 不匯入 TA-Lib", "[VIA:ACCEL-BRIDGE" in body and "VIA_FROM_VCGC" in body
        and not re.search(r"^\s*(import|from)\s+" + "ta" + r"lib\b", body, re.M))
    print(f"[DataFrame 鎖] 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
