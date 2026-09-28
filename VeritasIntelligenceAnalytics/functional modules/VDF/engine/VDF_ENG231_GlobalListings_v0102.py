#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG231_GlobalListings v0102 — 每日台股清單(台股個股 + 主動式台股 ETF);美股 · 日股撤下

操作員 2026-09-28:「不對 每日台股清單 其他刪除」。
v0100 / v0101 做了美 · 日 · 台三地;本版只留每日台股清單,美股(NASDAQ Trader)與日股(JPX)整段撤下 —— 不抓、不寫、不上網。
v0100 / v0101 依 L04 留作版史(尾版是本支,短令 via-lists 與一鍵都取尾版,舊版不再被執行)。

  台股個股      VDF_ENG087.load_stock_list()(加權 + 櫃買普通股;正主判 GREEN / AMBER / RED)
  主動式台股 ETF VDF_ENG087.load_active_etfs()(總清單 + 有持股 = 已驗證)
  本支不另立第二份清單(L05):只讀 ENG087 的結果,每天落一份帶日期的檔:
    VIA_Reports/lists/TW_STOCKS_<YYYYMMDD>.csv · TW_ACTIVE_ETFS_<YYYYMMDD>.csv · DAILY_TW_LISTS_<YYYYMMDD>.json(+ 各一份 _latest)

撤表(L10 刪資料是操作員的手):工作站 vdf_global_market.duckdb 裡 v0100 寫過的 us_listings(jp_listings 從沒落地)
  不自動刪。`retire` 只列出要撤哪幾張、各幾列;操作員親手加 --yes 才 DROP。庫表冊 VIA_DB_Table_SSOT_v0102 已撤下這兩張。

用法(經 VCGC;VIA_FROM_VCGC=YES):
  python VDF_ENG231_GlobalListings_v0102.py status            # 唯讀:台股幾檔 · 主動式 ETF 幾檔已驗證
  python VDF_ENG231_GlobalListings_v0102.py lists             # 出今天的每日台股清單檔(讀 ENG087,不外呼)
  python VDF_ENG231_GlobalListings_v0102.py run               # 同 lists(v0102 起不再上網抓美日)
  python VDF_ENG231_GlobalListings_v0102.py retire [--yes]    # 撤 us_listings / jp_listings;不加 --yes 只列計畫
  python VDF_ENG231_GlobalListings_v0102.py --selftest        # 假正主 + 暫存夾 / 暫存庫
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
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
DB_GL = VDF / "output_hub" / "mega" / "vdf_global_market.duckdb"
OUT = VIA / "VIA_Reports" / "lists"
RETIRED = ("us_listings", "jp_listings")
LISTS = (("tw_stocks", "TW_STOCKS", "load_stock_list", "台股個股"), ("tw_active_etfs", "TW_ACTIVE_ETFS", "load_active_etfs", "主動式ETF"))
ENGINE_TAG = "VDF_ENG231_GlobalListings_v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def tw_owner():
    """台灣清單正主 VDF_ENG087 尾版(只讀)。"""
    hits = sorted(HERE.glob("VDF_ENG087_MarketListGovernance_v*.py"))
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("vdf_eng087_for_eng231", hits[-1])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def build(owner=None, day: date | None = None) -> dict:
    """今天的台股兩張清單(全照 ENG087 的判定,不另判)。"""
    owner = owner if owner is not None else tw_owner()
    out = {"engine": ENGINE_TAG, "date": (day or date.today()).isoformat(), "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    for key, _stem, fn, _zh in LISTS:
        r = getattr(owner, fn)() if owner is not None else {"state": "ABSENT", "why": "VDF_ENG087 不在", "rows": []}
        out[key] = {"state": r.get("state", "NODATA"), "why": r.get("why", ""), "count": len(r.get("rows") or []),
                    "counts": r.get("counts") or {}, "checks": r.get("checks") or [], "rows": r.get("rows") or []}
    return out


def write_daily(payload: dict, out: Path = OUT) -> dict:
    """每張清單落 <STEM>_<YYYYMMDD>.csv + _latest.csv;摘要 JSON 同樣兩份。
    空清單不寫空 CSV,而且把本支先前寫的「今天那份」與 _latest 撤掉(Codex #343 P1:舊名單不能冒充今天的清單);
    撤掉的檔名記在 paths["removed"],摘要 JSON 照實 NODATA。只動本支自己產生的這兩個檔名,不碰其他檔。"""
    out.mkdir(parents=True, exist_ok=True)
    tag = payload["date"].replace("-", "")
    paths = {}
    for key, stem, _fn, _zh in LISTS:
        rows = payload[key]["rows"]
        if not rows:
            for name in (f"{stem}_{tag}.csv", f"{stem}_latest.csv"):
                stale = out / name
                if stale.is_file():
                    stale.unlink()
                    paths.setdefault("removed", []).append(name)
            continue
        cols = list(dict.fromkeys(k for r in rows for k in r))
        for name in (f"{stem}_{tag}.csv", f"{stem}_latest.csv"):
            with (out / name).open("w", encoding="utf-8-sig", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=cols)
                w.writeheader()
                w.writerows(rows)
        paths[key] = str(out / f"{stem}_{tag}.csv")
    slim = {k: ({kk: vv for kk, vv in v.items() if kk != "rows"} if isinstance(v, dict) else v) for k, v in payload.items()}
    text = json.dumps(dict(slim, files=paths), ensure_ascii=False, indent=1, default=str)
    for name in (f"DAILY_TW_LISTS_{tag}.json", "DAILY_TW_LISTS_latest.json"):
        (out / name).write_text(text, encoding="utf-8")
    paths["summary"] = str(out / f"DAILY_TW_LISTS_{tag}.json")
    return paths


def lines(payload: dict) -> list:
    out = []
    for key, _stem, _fn, zh in LISTS:
        v = payload[key]
        c = v.get("counts") or {}
        extra = (f"(加權 {c.get('TWSE', 0):,} · 櫃買 {c.get('TPEX', 0):,})" if key == "tw_stocks" and c
                 else (f" · 已驗證 {c.get('verified', 0)} · 未驗證 {c.get('unverified', 0)}" if c else ""))
        out.append(f"  [{zh}] {v['state']:7s} {v['count']:>6,} 檔{extra}" + ("" if v["state"] == "GREEN" else f" · {v.get('why') or '—'}"))
    return out


def retire(db: Path = DB_GL, yes: bool = False) -> dict:
    """撤 v0100 寫過的美 / 日清單表。不加 yes 只列計畫(L10:刪資料是操作員的手)。"""
    db = Path(db)
    if not db.is_file():
        return {"state": "NODATA", "why": f"{db.name} 不在", "tables": {}}
    import duckdb
    con = duckdb.connect(str(db), read_only=not yes)
    try:
        have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        found = {t: con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for t in RETIRED if t in have}
        if not found:
            return {"state": "OK", "why": "兩張都不在,不用撤", "tables": {}}
        if not yes:
            return {"state": "PLAN", "why": "只列計畫;操作員親手加 --yes 才撤", "tables": found}
        for t in found:
            con.execute(f'DROP TABLE "{t}"')
        return {"state": "DROPPED", "why": "操作員 --yes 撤表", "tables": found}
    finally:
        con.close()


# v0100 / v0101 的美 · 日公開面已撤:函式一律回 RETIRED(照實,不假裝有資料);常數名撤了就說撤了(不默默給 None)
_RETIRED_FUNCS = ("run", "fetch_us", "fetch_jp", "parse_nasdaq_dir", "frame_from_xls", "parse_jpx_frame", "sniff", "summarize",
                  "store", "read_table", "build_lists", "write_lists", "net_tool")
_RETIRED_NAMES = ("URL_NASDAQ", "URL_OTHER", "URL_JPX", "US_EXCH", "JP_STOCK_SEGMENTS", "MARKET_ZH", "PRIOR", "PRIOR_PATH")
_RETIRED_WHY = "美股 · 日股清單已撤(操作員 2026-09-28「不對 每日台股清單 其他刪除」);台股請用 build / write_daily"


def __getattr__(name):
    if name in _RETIRED_FUNCS:
        def _retired(*_a, **_k):
            return {"engine": ENGINE_TAG, "state": "RETIRED", "why": f"{name}:{_RETIRED_WHY}"}
        _retired.__name__ = name
        return _retired
    if name in _RETIRED_NAMES:
        raise AttributeError(f"{name}:{_RETIRED_WHY}")
    raise AttributeError(name)

def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "只經 VCGC(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    verb = next((x for x in a if not x.startswith("-")), "status")
    if verb in ("status", "lists", "run"):
        p = build()
        for ln in lines(p):
            print(ln)
        if verb != "status":
            paths = write_daily(p)
            print(f"  [每日台股清單] {p['date']} · " + " · ".join(Path(paths[k]).name for k in ("tw_stocks", "tw_active_etfs") if k in paths)
                  + f" · 摘要 {paths['summary']}")
            if verb == "run":
                print("  [註] v0102 起 run = lists:美股 · 日股已撤(操作員令),不上網")
        return 0 if all(p[k]["state"] in ("GREEN", "AMBER") for k, *_ in LISTS) else 2
    if verb == "retire":
        r = retire(yes="--yes" in a)
        print(f"  [撤表] {r['state']} · {r['why']}" + ("" if not r["tables"] else " · " + " · ".join(f"{t} {n:,} 列" for t, n in r["tables"].items())))
        return 0 if r["state"] in ("OK", "PLAN", "DROPPED", "NODATA") else 2
    print(__doc__)
    return 2


# ---------------------------------------------------------------- 自測(假正主 + 暫存夾 / 暫存庫;零外呼)
class _FakeOwner:
    def load_stock_list(self):
        return {"state": "GREEN", "why": "股票清單 2 檔", "counts": {"TWSE": 1, "TPEX": 1},
                "rows": [{"code": "2330", "name": "台積電", "market": "TWSE"}, {"code": "6488", "name": "環球晶", "market": "TPEX"}]}

    def load_active_etfs(self):
        return {"state": "AMBER", "why": "1 檔還沒有持股", "counts": {"listed": 2, "verified": 1, "unverified": 1},
                "rows": [{"ticker": "00980A", "verified": True}, {"ticker": "00991A", "verified": False}]}


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    p = build(_FakeOwner(), day=date(2026, 9, 28))
    chk("① 只剩台股兩張清單(美股 · 日股已撤)", set(k for k in p if k.startswith(("tw_", "us_", "jp_"))) == {"tw_stocks", "tw_active_etfs"})
    chk("② 狀態全照正主 ENG087(不另判)", (p["tw_stocks"]["state"], p["tw_active_etfs"]["state"], p["tw_stocks"]["count"], p["tw_active_etfs"]["count"]) == ("GREEN", "AMBER", 2, 2))
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        paths = write_daily(p, td)
        names = sorted(x.name for x in td.iterdir())
        chk("③ 每日一份帶日期的檔 + latest", names == sorted(["TW_STOCKS_20260928.csv", "TW_STOCKS_latest.csv", "TW_ACTIVE_ETFS_20260928.csv",
                                                               "TW_ACTIVE_ETFS_latest.csv", "DAILY_TW_LISTS_20260928.json", "DAILY_TW_LISTS_latest.json"]), ", ".join(names))
        with open(paths["tw_stocks"], encoding="utf-8-sig") as fh:
            got = list(csv.DictReader(fh))
        chk("④ CSV 內容 = 正主的列(欄序照原樣)", [r["code"] for r in got] == ["2330", "6488"] and list(got[0])[:3] == ["code", "name", "market"])
        summ = json.loads((td / "DAILY_TW_LISTS_latest.json").read_text(encoding="utf-8"))
        chk("⑤ 摘要 JSON 不含整份列(只留狀態 · 數 · 檢查 · 檔名)", "rows" not in summ["tw_stocks"] and summ["date"] == "2026-09-28" and "files" in summ)
        empty = build(type("E", (), {"load_stock_list": lambda self: {"state": "NODATA", "why": "空", "rows": []},
                                     "load_active_etfs": lambda self: {"state": "NODATA", "why": "空", "rows": []}})(), day=date(2026, 9, 29))
        (td / "e").mkdir()
        for name in ("TW_STOCKS_20260929.csv", "TW_STOCKS_latest.csv", "TW_STOCKS_20260928.csv", "OTHER.csv"):
            (td / "e" / name).write_text("code\n2330\n", encoding="utf-8")
        p2 = write_daily(empty, td / "e")
        left_e = sorted(x.name for x in (td / "e").iterdir())
        chk("⑥ 清單空 = 不寫空 CSV,且撤掉本支先前寫的今天那份與 latest(舊名單不冒充今天;別天、別的檔不動)",
            set(p2) == {"summary", "removed"} and sorted(p2["removed"]) == ["TW_STOCKS_20260929.csv", "TW_STOCKS_latest.csv"]
            and "TW_STOCKS_20260928.csv" in left_e and "OTHER.csv" in left_e and "TW_STOCKS_latest.csv" not in left_e, ", ".join(left_e))
        ln = lines(p)
        chk("⑦ 白話兩行:GREEN 只報數;非 GREEN 帶原因", len(ln) == 2 and "加權 1" in ln[0] and "1 檔還沒有持股" in ln[1], ln[1].strip())
        import duckdb
        db = td / "gl.duckdb"
        con = duckdb.connect(str(db))
        con.execute("CREATE TABLE us_listings AS SELECT 'AAPL' AS code UNION ALL SELECT 'IBM'")
        con.execute("CREATE TABLE fwd_valuation_daily AS SELECT 1 AS x")
        con.close()
        plan = retire(db)
        con = duckdb.connect(str(db), read_only=True)
        still = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        con.close()
        chk("⑧ retire 不加 --yes = 只列計畫、一張都不動(L10)", plan["state"] == "PLAN" and plan["tables"] == {"us_listings": 2} and "us_listings" in still)
        done = retire(db, yes=True)
        con = duckdb.connect(str(db), read_only=True)
        left = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        con.close()
        chk("⑨ --yes 只撤美 / 日清單表,同庫其他表不動", done["state"] == "DROPPED" and left == {"fwd_valuation_daily"}, str(sorted(left)))
        chk("⑩ 再撤一次 = 兩張都不在,不用撤", retire(db, yes=True)["state"] == "OK")
    real = tw_owner()
    chk("⑪ 台灣正主 VDF_ENG087 尾版在且有 load_stock_list / load_active_etfs", real is not None and hasattr(real, "load_stock_list") and hasattr(real, "load_active_etfs"))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑫ 本支不外呼(沒有 curl_bytes / 網址)", "curl_bytes(" not in src.split("# ---------------------------------------------------------------- 自測")[0].split("[VIA:NET-BRIDGE:END]")[-1]
        and "https://" not in src.split("[VIA:NET-BRIDGE:END]")[-1])
    mod = sys.modules.get(__name__)
    r = getattr(mod, "fetch_us")(None) if mod is not None else {}
    try:
        getattr(mod, "URL_JPX")
        said = False
    except AttributeError as e:
        said = "已撤" in str(e)
    chk("⑭ 撤下的舊公開面有轉接:函式回 RETIRED 附原因、常數名說明已撤(不讓呼叫端 AttributeError 摸不著頭緒)",
        r.get("state") == "RETIRED" and "每日台股清單" in r.get("why", "") and said)
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    denied = main(["lists"]) == 2
    if keep is not None:
        os.environ["VIA_FROM_VCGC"] = keep
    chk("⑮ 不經 VCGC 就拒跑", denied)
    ok = all(results)
    print(f"  [計] {ENGINE_TAG} 自測 {sum(results)}/{len(results)} · {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
