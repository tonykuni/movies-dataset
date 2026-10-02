#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0121 — 薄尾:輸入範圍與輸出項目 / 表頭歸 VDF 管理員管(動詞 universe)

操作員(R49 2026-10-02):「只有台灣個股全部及主動式台股ETF為主動式股票ETF中可以依規定抓到每日台股持股資訊的ETF
加權 櫃買資訊跟上面全抓當輸入 VDF SYSTEM MANAGER管理 輸出項目及HEADER也是他管理」。
冊:VDF_InputUniverse_SSOT_v*.json(尾版)。三組輸入:IN-01 全部個股(加權 + 櫃買)· IN-02 主動式台股股票 ETF(有每日台股持股)·
IN-03 加權 / 櫃買指數。五項輸出:OUT-01 輸入清單 · OUT-02 個股日資料 · OUT-03 每日持股 · OUT-04 持股異動 · OUT-05 指數日資料。
本版只加動詞(其餘全照前版):
  universe headers [--json]       每項輸出的欄位與中文表頭(有正本的照正本指標解析,不抄)
  universe list [--out <dir>]     經 VDF_ENG087 唯讀讀取口組三組清單,寫 VDF_UNIVERSE_latest.csv / .json(中文表頭;再生件)
  universe check                  冊的規則與讀取口對得上(regex · 指標可解析 · 讀取口函式在)
  universe loop                   順序(照 main 工作流冊 VDF-WKF010 → 006 → 004):E-01…E-11 每站引擎尾版在不在 · 觸網 · 缺口
  universe frame <OUT-xx>         輸出表頭 → pandas DataFrame(欄名 / 欄序 / 型別照冊;中央表頭冊有的照它)
  universe validate [OUT-xx] [--file <csv|parquet>]  輸出驗證 = CGC_MDL249 check_table(必填 · 型別 · 主鍵 · 最少列)+ 本冊範圍規則
輸入 IN-xx · 輸出 OUT-xx · 引擎 E-xx 三套分開編號,都在冊上;表頭不抄第二份(中央表頭冊 / DailyRow 冊指標)。
不抓網、不寫庫、不代設同意閘、不碰 TA-Lib。只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。
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

import csv
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
_STEM = "VDF_SystemManager"
REPORTS = VIA / "VIA_Reports" / "vdf" / "universe"


def _vnum(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
PRIOR = _load(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)
ENGINE_TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"


def __getattr__(name):
    return getattr(PRIOR, name)


def collect() -> dict:
    return PRIOR.collect()


def book_path() -> Path:
    hits = sorted(HERE.glob("VDF_InputUniverse_SSOT_v[0-9][0-9][0-9][0-9].json"), key=_vnum)
    if not hits:
        raise FileNotFoundError("VDF_InputUniverse_SSOT_v*.json 不在")
    return hits[-1]


def book() -> dict:
    return json.loads(book_path().read_text(encoding="utf-8"))


def _dig(obj, dotted: str):
    for k in dotted.split("."):
        obj = obj.get(k) if isinstance(obj, dict) else None
    return obj


REG = VIA / "supportive modules" / "registry"


def header_book() -> dict:
    """中央表頭冊尾版(VIA_Output_Header_SSOT;CGC_MDL249 鎖)。"""
    hits = sorted(REG.glob("VIA_Output_Header_SSOT_v[0-9][0-9][0-9][0-9].json"), key=_vnum)
    return json.loads(hits[-1].read_text(encoding="utf-8")) if hits else {}


def resolve_columns(item: dict) -> list:
    """一項輸出的欄位 [{key, zh, dtype}]:中央表頭冊 table id → 冊上直寫 → columns_ref 正本指標(都不抄)。"""
    if item.get("header_ref"):
        spec = (header_book().get("tables") or {}).get(item["header_ref"])
        if not spec:
            raise ValueError(f"{item['id']} 中央表頭冊沒有 table {item['header_ref']}")
        return [{"key": c["name"], "zh": c.get("zh") or c["name"], "dtype": c.get("dtype", "")} for c in spec["columns"]]
    if item.get("columns"):
        return [dict(c) for c in item["columns"]]
    ref = item.get("columns_ref") or {}
    src = VIA / ref.get("path", "")
    if not src.is_file():
        raise FileNotFoundError(f"{item['id']} 表頭正本不在:{ref.get('path')}")
    raw = _dig(json.loads(src.read_text(encoding="utf-8")), ref.get("key", ""))
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{item['id']} 表頭正本 {ref.get('path')}::{ref.get('key')} 不是欄位清單")
    zh = item.get("zh_for_ref") or {}
    out = []
    for c in raw:
        if isinstance(c, dict):
            out.append({"key": c.get("name") or c.get("key"), "zh": c.get("zh") or zh.get(c.get("name"), c.get("name")),
                        "dtype": c.get("dtype", "")})
        else:
            out.append({"key": str(c), "zh": zh.get(str(c), str(c)), "dtype": ""})
    return out


def headers() -> dict:
    bk = book()
    return {"book": book_path().name,
            "outputs": [{"id": o["id"], "item": o["item"], "zh": o["zh"], "table": o.get("table", ""),
                         "columns": resolve_columns(o)} for o in bk["outputs"]]}


def _eng087():
    tail = max((HERE / "engine").glob("VDF_ENG087_MarketListGovernance_v*.py"), key=_vnum)
    return _load(tail, "_vdf_eng087_for_universe")


def build_universe(lists=None) -> dict:
    """三組合一。lists 可注入(自測用);預設經 VDF_ENG087 唯讀讀取口。"""
    bk = book()
    ins = {i["id"]: i for i in bk["inputs"]}
    if lists is None:
        L = _eng087()
        lists = {"stock": L.load_stock_list(), "etf": L.load_active_etfs()}
    rx_stock = re.compile(ins["IN-01"]["code_regex"])
    rx_etf = re.compile(ins["IN-02"]["code_regex"])
    rows, notes = [], []
    st = lists.get("stock") or {}
    if st.get("state") in (None, "ABSENT", "RED") and not st.get("rows"):
        notes.append(f"IN-01 {st.get('state', 'ABSENT')}:{st.get('why', '讀取口沒回')}")
    for r in st.get("rows") or []:
        code = str(r.get("code") or "")
        if not rx_stock.fullmatch(code):
            continue
        rows.append({"group": "TW_STOCK", "code": code, "name": r.get("name") or "", "market": r.get("market") or "",
                     "yf_ticker": r.get("yf_ticker") or "", "bb_ticker": f"{code} TT", "industry": r.get("industry") or "",
                     "issuer": "", "verified": "", "last_holdings_date": "", "source": "VDF_ENG087.load_stock_list",
                     "state": "OK" if r.get("market") else "CHECK"})
    et = lists.get("etf") or {}
    if et.get("state") in (None, "ABSENT", "RED") and not et.get("rows"):
        notes.append(f"IN-02 {et.get('state', 'ABSENT')}:{et.get('why', '讀取口沒回')}")
    skipped = 0
    for r in et.get("rows") or []:
        code = str(r.get("ticker") or "")
        if not rx_etf.fullmatch(code):
            continue
        if not r.get("verified"):                      # 規則:要有每日台股持股
            skipped += 1
            continue
        rows.append({"group": "TW_ACTIVE_EQUITY_ETF", "code": code, "name": r.get("name") or "", "market": "",
                     "yf_ticker": f"{code}.TW", "bb_ticker": f"{code} TT", "industry": "", "issuer": r.get("issuer") or "",
                     "verified": True, "last_holdings_date": r.get("last_holdings_date") or "",
                     "source": "VDF_ENG087.load_active_etfs(verified)", "state": "OK"})
    if skipped:
        notes.append(f"IN-02 未列 {skipped} 檔:在總清單但沒有每日持股(規則要求可抓每日台股持股)")
    for m in ins["IN-03"]["members"]:
        rows.append({"group": "TW_INDEX", "code": m["code"], "name": m["zh"], "market": m["market"], "yf_ticker": m["yf_proxy"],
                     "bb_ticker": "", "industry": "", "issuer": "", "verified": "", "last_holdings_date": "",
                     "source": f"{m['official']}(yfinance {m['yf_proxy']} 只當代理)", "state": "OK"})
    for i, r in enumerate(rows, 1):
        r["seq"] = i
    tally = {}
    for r in rows:
        tally[r["group"]] = tally.get(r["group"], 0) + 1
    return {"rows": rows, "tally": tally, "notes": notes, "book": book_path().name}


def write_universe(rep: dict, out_dir: Path | None = None) -> dict:
    out_dir = Path(out_dir) if out_dir else REPORTS
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = resolve_columns(next(o for o in book()["outputs"] if o["id"] == "OUT-01"))
    csv_p, json_p = out_dir / "VDF_UNIVERSE_latest.csv", out_dir / "VDF_UNIVERSE_latest.json"
    with open(csv_p, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([c["zh"] for c in cols])
        for r in rep["rows"]:
            w.writerow([r.get(c["key"], "") for c in cols])
    json_p.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"csv": str(csv_p), "json": str(json_p)}


def check() -> dict:
    bk = book()
    probs = []
    for o in bk["outputs"]:
        try:
            if not resolve_columns(o):
                probs.append(f"{o['id']} 沒有欄位")
        except (OSError, ValueError) as exc:
            probs.append(str(exc))
    try:
        L = _eng087()
        for i in bk["inputs"]:
            call = (i.get("reader") or {}).get("call")
            if call and not callable(getattr(L, call, None)):
                probs.append(f"{i['id']} 讀取口 {call} 不在 ENG087 尾版")
        if hasattr(L, "STOCK_CODE") and getattr(L, "STOCK_CODE").pattern != bk["inputs"][0]["code_regex"]:
            probs.append(f"IN-01 regex 與 ENG087 STOCK_CODE 不同:{L.STOCK_CODE.pattern}")
        if hasattr(L, "ACTIVE_ETF_CODE") and getattr(L, "ACTIVE_ETF_CODE").pattern != bk["inputs"][1]["code_regex"]:
            probs.append(f"IN-02 regex 與 ENG087 ACTIVE_ETF_CODE 不同:{L.ACTIVE_ETF_CODE.pattern}")
    except Exception as exc:                            # 讀取口載不起來就照實報
        probs.append(f"ENG087 載入失敗:{exc}")
    return {"state": "GREEN" if not probs else "RED", "problems": probs, "book": book_path().name}


def _mdl249():
    tail = max(REG.glob("CGC_MDL249_DataFrameLock_v*.py"), key=_vnum)
    return _load(tail, "_cgc_mdl249_for_vdf_universe")


def _item(out_id: str) -> dict:
    hit = [o for o in book()["outputs"] if o["id"] == out_id]
    if not hit:
        raise KeyError(f"沒有輸出項 {out_id}(有:{', '.join(o['id'] for o in book()['outputs'])})")
    return hit[0]


def spec_for(out_id: str) -> dict:
    """CGC_MDL249 check_table 吃的 spec:中央表頭冊有的照它;其餘由本冊欄位 + 主鍵 + 必填 + 最少列組成。"""
    it = _item(out_id)
    if it.get("header_ref"):
        return dict((header_book().get("tables") or {})[it["header_ref"]])
    dmap = book()["validation"]["dtype_map"]
    keys, req = set(it.get("keys") or []), set(it.get("required") or [])
    cols = []
    for c in resolve_columns(it):
        dt = c.get("dtype") or ""
        dt = dmap.get(dt.upper(), dt) if dt else "str"
        cols.append({"name": c["key"], "dtype": dt if dt in ("str", "int", "float", "date", "datetime", "bool") else "str",
                     "required": c["key"] in req or c["key"] in keys, "key": c["key"] in keys})
    return {"subsystem": "VDF", "owner": ENGINE_TAG, "source": {}, "columns": cols, "min_rows": it.get("min_rows", 0),
            "extra_ok": bool(it.get("extra_columns"))}


def frame(out_id: str, rows: list | None = None):
    """輸出表頭 → pandas DataFrame:欄名 / 欄序照冊,型別照冊轉(空表也帶正確欄)。"""
    import pandas as pd
    spec = spec_for(out_id)
    names = [c["name"] for c in spec["columns"]]
    df = pd.DataFrame(rows or [], columns=names)
    conv = {"str": "string", "int": "Int64", "float": "Float64", "bool": "boolean"}
    for c in spec["columns"]:
        n, dt = c["name"], c["dtype"]
        if dt in ("date", "datetime"):
            df[n] = pd.to_datetime(df[n], errors="coerce")
            if dt == "date":
                df[n] = df[n].dt.normalize()
        elif dt in conv:
            if dt in ("int", "float"):
                df[n] = pd.to_numeric(df[n], errors="coerce")
            elif dt == "bool":
                truth = {"true": True, "1": True, "t": True, "yes": True, "false": False, "0": False, "f": False, "no": False}
                df[n] = df[n].map(lambda v: v if isinstance(v, bool) else truth.get(str(v).strip().lower(), pd.NA))
            df[n] = df[n].astype(conv[dt])
    return df


def validate(out_id: str, df=None, universe_rep: dict | None = None) -> dict:
    """輸出驗證 = CGC_MDL249 check_table(必填 · 型別 · 主鍵 · 最少列)+ 本冊範圍規則。df 不給 = 照冊來源讀(不在 = NODATA)。"""
    it = _item(out_id)
    tid = it.get("header_ref") or f"vdf_universe_{out_id.lower()}"
    spec = spec_for(out_id)
    m = _mdl249()
    if df is None and not spec.get("source"):
        if out_id == "OUT-01":
            rep = universe_rep or build_universe()
            df = frame("OUT-01", rep["rows"])
        else:
            return {"table": tid, "lamp": "NODATA", "problems": [f"{out_id} 本冊沒有可直讀來源;給 --file 或經產出引擎({', '.join(it.get('engines') or [])})"]}
    row = m.check_table(tid, spec, frame=df) if df is not None else m.check_table(tid, spec)
    extra = []
    if df is not None and out_id == "OUT-01" and len(df):
        ins = {i["id"]: i for i in book()["inputs"]}
        g = df["group"].astype(str)
        bad_s = df[(g == "TW_STOCK") & ~df["code"].astype(str).str.fullmatch(ins["IN-01"]["code_regex"])]
        bad_e = df[(g == "TW_ACTIVE_EQUITY_ETF") & ~df["code"].astype(str).str.fullmatch(ins["IN-02"]["code_regex"])]
        if len(bad_s) or len(bad_e):
            extra.append(f"代號不合規則:個股 {len(bad_s)} · 主動 ETF {len(bad_e)}")
        idx = set(df.loc[g == "TW_INDEX", "code"].astype(str))
        if idx != {m_["code"] for m_ in ins["IN-03"]["members"]}:
            extra.append(f"指數列不齊:{sorted(idx)}")
        fl = ins["IN-01"]["floor"]
        for mk in ("TWSE", "TPEX"):
            n = int(((g == "TW_STOCK") & (df["market"].astype(str) == mk)).sum())
            if n == 0:
                extra.append(f"{mk} 0 家(RED)")
            elif n < fl[mk]:
                row.setdefault("warn", []).append(f"{mk} {n} 家 < 下限 {fl[mk]}(AMBER)")
    if extra:
        row["problems"] = list(row.get("problems") or []) + extra
        row["lamp"] = "RED"
    return row


def loop_plan() -> list:
    """順序(冊 loop.order):每站的引擎尾版在不在 · 觸網 · 缺口。只看,不跑。"""
    bk = book()
    eng = {e["id"]: e for e in bk["engines"]}
    out = []
    for step in bk["loop"]["order"]:
        eid = step.split(":")[0]
        e = eng[eid]
        pat = e["engine"]
        hits = sorted((VIA / Path(pat).parent).glob(Path(pat).name), key=_vnum) if "*" in pat else []
        state = e.get("state") or ("OK" if hits else "ABSENT")
        out.append({"step": step, "engine": Path(hits[-1]).name if hits else pat, "verb": e.get("verb", ""), "item": e.get("item", ""),
                    "wkf": e.get("wkf", ""), "net": bool(e.get("net")), "role": e.get("role", ""), "state": state})
    return out


def universe(args: list) -> int:
    sub = args[0] if args else "headers"
    if sub == "loop":
        print(f"[VDF 順序] 冊 {book_path().name}(照 main 工作流冊 VDF-WKF010 → 006 → 004)")
        for s in loop_plan():
            print(f"  {s['step']:<12} {s['state']:<16} {'觸網' if s['net'] else '離線'}  {s['engine']}  {s['verb']}  {s['wkf']}  · {s['role']}")
        return 0
    if sub == "frame" and len(args) >= 2:
        df = frame(args[1])
        print(f"[VDF 表頭 → DataFrame] {args[1]} · {len(df.columns)} 欄")
        print(df.dtypes.to_string())
        return 0
    if sub == "validate":
        ids = [a for a in args[1:] if a.startswith("OUT-")] or [o["id"] for o in book()["outputs"]]
        worst = 0
        for oid in ids:
            df = None
            if "--file" in args:
                import pandas as pd
                fp = args[args.index("--file") + 1]
                df = pd.read_parquet(fp) if fp.endswith(".parquet") else pd.read_csv(fp, encoding="utf-8-sig", dtype=str)
            r = validate(oid, df)
            lamp = r.get("lamp")
            worst = max(worst, {"GREEN": 0, "YELLOW": 0, "NODATA": 0}.get(lamp, 1))
            print(f"  [{lamp}] {oid} {r.get('table')} · 列 {r.get('rows')} · " + " ; ".join((r.get("problems") or []) + (r.get("warn") or [])))
        return worst
    if sub == "headers":
        h = headers()
        if "--json" in args:
            print(json.dumps(h, ensure_ascii=False, indent=1))
        else:
            print(f"[VDF 輸出表頭] 冊 {h['book']}")
            for o in h["outputs"]:
                print(f"  {o['id']} {o['zh']}({o['item']} · {o['table']})")
                print("     " + " | ".join(f"{c['zh']}({c['key']})" for c in o["columns"]))
        return 0
    if sub == "list":
        rep = build_universe()
        out = write_universe(rep, args[args.index("--out") + 1] if "--out" in args else None)
        t = rep["tally"]
        print(f"[VDF 輸入清單] 個股 {t.get('TW_STOCK', 0)} · 主動股票 ETF(有每日持股){t.get('TW_ACTIVE_EQUITY_ETF', 0)} · "
              f"指數 {t.get('TW_INDEX', 0)} · 冊 {rep['book']} · {out['csv']}")
        for n in rep["notes"]:
            print("  [註] " + n)
        return 0 if t.get("TW_STOCK") and t.get("TW_ACTIVE_EQUITY_ETF") else 2
    if sub == "check":
        c = check()
        print(f"[VDF 範圍冊檢查] {c['state']} · 冊 {c['book']}" + "".join("\n  · " + p for p in c["problems"]))
        return 0 if c["state"] == "GREEN" else 1
    print(f"[VDF universe] 不認得:{sub}(headers / list / check / loop / frame / validate)")
    return 2


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    a = sys.argv[1:]
    if a and a[0] == "universe":
        return universe(a[1:])
    return PRIOR.main()


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE_TAG} · 薄尾自測(輸入範圍 · 輸出項目與表頭)===")
    bk = book()
    chk("① 冊:三組輸入(個股 · 主動股票 ETF · 指數)+ 五項輸出", [i["group"] for i in bk["inputs"]] ==
        ["TW_STOCK", "TW_ACTIVE_EQUITY_ETF", "TW_INDEX"] and len(bk["outputs"]) == 5)
    h = headers()
    cols = {o["id"]: o["columns"] for o in h["outputs"]}
    chk("② 表頭全可解析;指標正本解出(個股日資料 26 欄 · 指數 12 欄,中文齊)",
        len(cols["OUT-02"]) == 26 and len(cols["OUT-05"]) == 12 and all(c["zh"] for v in cols.values() for c in v),
        {k: len(v) for k, v in cols.items()})
    fake = {"stock": {"state": "GREEN", "rows": [{"code": "2330", "name": "台積電", "market": "TWSE", "yf_ticker": "2330.TW", "industry": "半導體"},
                                                  {"code": "6488", "name": "環球晶", "market": "TPEX", "yf_ticker": "6488.TWO", "industry": "半導體"},
                                                  {"code": "0050", "name": "元大台灣50", "market": "TWSE"}]},
            "etf": {"state": "AMBER", "rows": [{"ticker": "00981A", "name": "主動統一台股增長", "issuer": "統一", "verified": True, "last_holdings_date": "2026-10-01"},
                                               {"ticker": "00999A", "name": "沒持股", "verified": False},
                                               {"ticker": "00980D", "name": "主動債", "verified": True}]}}
    rep = build_universe(fake)
    t = rep["tally"]
    chk("③ 只收:個股四碼(0050 不算個股)· 主動 A 尾且有每日持股(D 尾 · 沒持股不收)· 兩個指數",
        t == {"TW_STOCK": 2, "TW_ACTIVE_EQUITY_ETF": 1, "TW_INDEX": 2} and any("未列 1 檔" in n for n in rep["notes"]), t)
    idx = [r for r in rep["rows"] if r["group"] == "TW_INDEX"]
    chk("④ 指數:TAIEX / TPEX 官方為準,yfinance 只標代理", [r["code"] for r in idx] == ["TAIEX", "TPEX"]
        and all("只當代理" in r["source"] for r in idx))
    with tempfile.TemporaryDirectory() as td:
        out = write_universe(rep, Path(td))
        lines = Path(out["csv"]).read_text(encoding="utf-8-sig").splitlines()
        chk("⑤ 輸出清單表頭 = 冊 OUT-01 中文欄名、欄序照冊;列數對", lines[0].split(",") == [c["zh"] for c in cols["OUT-01"]]
            and len(lines) == 1 + len(rep["rows"]))
    empty = build_universe({"stock": {"state": "ABSENT", "why": "庫缺"}, "etf": {"state": "ABSENT", "why": "庫缺"}})
    chk("⑥ 讀取口缺 = 照實記(不假填),只剩指數兩列", empty["tally"] == {"TW_INDEX": 2} and len(empty["notes"]) == 2)
    c = check()
    chk("⑦ check:冊規則與 ENG087 尾版讀取口 / regex 對得上", c["state"] == "GREEN", c["problems"])
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    try:
        chk("⑧ 不經 VCGC 拒跑", main() == 2)
    finally:
        if keep is not None:
            os.environ["VIA_FROM_VCGC"] = keep
    lp = loop_plan()
    chk("⑩ 順序:12 站照 main 工作流冊(E-01 清單起 · E-11 驗證收);E-10 指數正主 = VDF_ENG232 尾版在",
        len(lp) == 12 and lp[0]["step"] == "E-01" and lp[-1]["step"] == "E-11:validate"
        and any(x["step"] == "E-10" and x["state"] == "OK" and x["engine"].startswith("VDF_ENG232_") for x in lp)
        and all(x["state"] == "OK" for x in lp), [x["state"] for x in lp])
    f3 = frame("OUT-03")
    cen = [c["name"] for c in header_book()["tables"]["etf_holdings_daily"]["columns"]]
    chk("⑪ 表頭 → DataFrame:OUT-03 欄 = 中央表頭冊 etf_holdings_daily(不抄);日期欄是時間型",
        list(f3.columns) == cen and str(f3["portfolio_date"].dtype).startswith("datetime"))
    v1 = validate("OUT-01", frame("OUT-01", rep["rows"]))
    chk("⑫ 驗證 OUT-01 走 CGC_MDL249:列數 < 1600 記紅(假資料只有 5 列),主鍵不重", v1["lamp"] == "RED"
        and any("列數" in p for p in v1["problems"]) and not any("主鍵" in p for p in v1["problems"]), v1["problems"])
    dup = frame("OUT-04", [{"portfolio_date": "2026-10-01", "previous_date": "2026-09-30", "etf_ticker": "00981A",
                            "holding_ticker": "2330", "change_type": "ADD"}] * 2)
    v4 = validate("OUT-04", dup)
    chk("⑬ 驗證抓得到主鍵重複(OUT-04 同一筆兩列)", v4["lamp"] == "RED" and any("主鍵" in p for p in v4["problems"]), v4["problems"])
    chk("⑭ 本冊沒有可直讀來源的項不假造:不給資料 = NODATA", validate("OUT-02")["lamp"] == "NODATA")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑨ 加速器橋 · 網路橋在;不碰 TA-Lib;不代設同意閘",
        "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and "VIA_NET_CONSENT\"] =" not in src)
    os.environ["VIA_FROM_VCGC"] = "YES"
    rc = PRIOR.selftest()
    good = all(ok)
    print(f"  [計] {ENGINE_TAG} 薄尾 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if good and rc == 0 else 'FAIL'}")
    return 0 if good and rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
