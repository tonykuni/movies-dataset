#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG231_GlobalListings v0100 — 美 · 日 · 台 個股總清單 + 每日主動式台股 ETF 總清單(一個出口)

操作員 2026-09-28:「檢查有無能生成美日台股個股總清單 · 每日主動式台股 ETF 總清單」。
盤點結果:台股與主動式 ETF 已有正主 VDF_ENG087 MarketListGovernance(工作站 1981 檔 · 22 檔全驗證);美、日兩地樹上沒有任何清單來源。
本支補美、日,台灣一律委派 ENG087(不另立第二份清單 L05):

  美股  NASDAQ Trader 官方代號目錄(每日更新,免費、免金鑰):
        nasdaqlisted.txt(NASDAQ)+ otherlisted.txt(NYSE / NYSE American / NYSE Arca / Cboe BZX / IEX)
        剔除測試代號(Test Issue=Y);ETF 另欄標記(stock = 非 ETF);交易所代碼照官方對照。
  日股  JPX 東証上場銘柄一覧 data_j.xls(月更):只收「内国株式」(プライム / スタンダード / グロース);ETF · REIT · ETN · 外国株另計不收。
        .xls 要 xlrd(工作站讀 AAII .xls 已在用);讀不動 = 照實 ABSENT 具名套件,不裝。
  台股  VDF_ENG087.load_stock_list()(加權 + 櫃買普通股)· 主動式 ETF VDF_ENG087.load_active_etfs()(總清單 + 有持股 = 已驗證)。

外呼一律走統包網路工具 SUP_MDL740 尾版 curl_bytes(雙閘在工具裡;閘沒開 = DENY、零外呼、零寫入;AI 永不代設同意閘)。
入庫走正典 VIA_LibCanon.UTILS.upsert_rows:vdf_global_market.duckdb · us_listings / jp_listings(鍵 code;replace=True 以最新清單為準,
as_of 欄記清單日期)。輸出 VIA_Reports/lists/GLOBAL_LISTS_latest.json(+ 三地 CSV)。

用法(經 VCGC;VIA_FROM_VCGC=YES):
  python VDF_ENG231_GlobalListings_v0100.py status            # 唯讀:三地各幾檔 · 清單日期 · 主動式 ETF 幾檔已驗證
  python VDF_ENG231_GlobalListings_v0100.py run [--only us,jp] [--dry]
  python VDF_ENG231_GlobalListings_v0100.py lists [--json]    # 出總清單檔(讀庫 + ENG087,不外呼)
  python VDF_ENG231_GlobalListings_v0100.py --selftest        # 假網路工具 + 暫存庫,零外呼
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
# ===== [VIA:LIB-BRIDGE:v0100] 三庫正典橋(批597;缺席大聲拋,不 graceful) =====
import sys as _lb_sys
from pathlib import Path as _lb_Path
_lb_p = _lb_Path(__file__).resolve()
while _lb_p.parent != _lb_p:
    if (_lb_p / "supportive modules").is_dir():
        _lb_sys.path.insert(0, str(_lb_p / "supportive modules"))
        break
    _lb_p = _lb_p.parent
import VIA_LibCanon as _LIB          # 正典缺席=大聲拋,不假裝有(LL151)
# ===== [VIA:LIB-BRIDGE:END] =====
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
import io
import json
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
DB_GL = VDF / "output_hub" / "mega" / "vdf_global_market.duckdb"
OUT = VIA / "VIA_Reports" / "lists"
URL_NASDAQ = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
URL_OTHER = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"
URL_JPX = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls"
US_EXCH = {"A": "NYSE American", "N": "NYSE", "P": "NYSE Arca", "Z": "Cboe BZX", "V": "IEX"}
JP_STOCK_SEGMENTS = ("プライム（内国株式）", "スタンダード（内国株式）", "グロース（内国株式）")
ENGINE_TAG = "VDF_ENG231_GlobalListings_v" + Path(__file__).stem.rsplit("_v", 1)[-1]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def net_tool():
    hits = sorted((VIA / "supportive modules" / "network").glob("SUP_MDL740_NetUnified_v*.py"))
    return _load(hits[-1], "via_net_for_eng231") if hits else None


def tw_owner():
    """台灣清單正主 VDF_ENG087 尾版(只讀)。"""
    hits = sorted(HERE.glob("VDF_ENG087_MarketListGovernance_v*.py"))
    return _load(hits[-1], "vdf_eng087_for_eng231") if hits else None


# ---------------------------------------------------------------- 美股
def parse_nasdaq_dir(text: str, kind: str) -> tuple:
    """NASDAQ Trader 管線分隔檔 → (列, 清單日期)。kind = nasdaq | other。剔除測試代號;最後一行是檔案建立時間。"""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    as_of = None
    if lines and lines[-1].startswith("File Creation Time"):
        m = re.search(r"(\d{2})(\d{2})(\d{4})", lines[-1])
        as_of = f"{m.group(3)}-{m.group(1)}-{m.group(2)}" if m else None
        lines = lines[:-1]
    rows = []
    rd = csv.DictReader(io.StringIO("\n".join(lines)), delimiter="|")
    for r in rd:
        if (r.get("Test Issue") or "").strip() == "Y":
            continue
        sym = (r.get("Symbol") if kind == "nasdaq" else r.get("ACT Symbol")) or ""
        sym = sym.strip()
        if not sym:
            continue
        exch = "NASDAQ" if kind == "nasdaq" else US_EXCH.get((r.get("Exchange") or "").strip(), (r.get("Exchange") or "").strip())
        etf = (r.get("ETF") or "").strip() == "Y"
        rows.append({"market": "US", "code": sym, "name": (r.get("Security Name") or "").strip(), "exchange": exch,
                     "is_etf": etf, "is_stock": not etf, "as_of": as_of or "", "source": "NASDAQ_TRADER_SYMDIR"})
    return rows, as_of


# ---------------------------------------------------------------- 日股
def frame_from_xls(data: bytes):
    """JPX .xls → DataFrame。要 xlrd;缺 = ImportError(呼叫端照實 ABSENT)。"""
    import pandas as pd
    return pd.read_excel(io.BytesIO(data), dtype=str)


def parse_jpx_frame(df) -> tuple:
    """JPX 上場銘柄一覧(日文欄名)→ (只收内国株式的列, 清單日期)。"""
    cols = {str(c).strip(): c for c in df.columns}
    need = ("日付", "コード", "銘柄名", "市場・商品区分")
    miss = [c for c in need if c not in cols]
    if miss:
        raise ValueError(f"JPX 欄位認不得:缺 {miss}")
    rows, as_of = [], None
    for _, r in df.iterrows():
        seg = str(r[cols["市場・商品区分"]]).strip()
        if seg not in JP_STOCK_SEGMENTS:
            continue
        d = str(r[cols["日付"]]).strip()
        as_of = as_of or (f"{d[:4]}-{d[4:6]}-{d[6:8]}" if re.fullmatch(r"\d{8}", d) else d)
        rows.append({"market": "JP", "code": str(r[cols["コード"]]).strip(), "name": str(r[cols["銘柄名"]]).strip(),
                     "exchange": "TSE " + seg.split("（")[0], "is_etf": False, "is_stock": True,
                     "industry": str(r[cols["33業種区分"]]).strip() if "33業種区分" in cols else "",
                     "as_of": as_of or "", "source": "JPX_DATA_J"})
    return rows, as_of


# ---------------------------------------------------------------- 抓 · 存 · 讀
def _get(net, url: str) -> dict:
    if net is None or not hasattr(net, "curl_bytes"):
        return {"state": "FAIL", "note": "網路工具缺(要 SUP_MDL740 v0114+ 的 curl_bytes)"}
    return net.curl_bytes(url, timeout=40, follow=True, headers={"User-Agent": "Mozilla/5.0 VIA-GlobalListings", "Accept": "*/*"})


def fetch_us(net) -> dict:
    out, as_of = [], None
    for url, kind in ((URL_NASDAQ, "nasdaq"), (URL_OTHER, "other")):
        rb = _get(net, url)
        if rb.get("state") != "OK":
            return {"state": rb.get("state") or "FAIL", "note": f"{url}:{rb.get('note', '')}"[:120], "rows": []}
        rows, d = parse_nasdaq_dir((rb.get("data") or b"").decode("utf-8", "replace"), kind)
        out += rows
        as_of = as_of or d
    uniq = {r["code"]: r for r in out}
    return {"state": "OK" if uniq else "EMPTY", "rows": [uniq[k] for k in sorted(uniq)], "as_of": as_of}


def fetch_jp(net) -> dict:
    rb = _get(net, URL_JPX)
    if rb.get("state") != "OK":
        return {"state": rb.get("state") or "FAIL", "note": f"JPX:{rb.get('note', '')}"[:120], "rows": []}
    try:
        df = frame_from_xls(rb.get("data") or b"")
    except ImportError as e:
        return {"state": "ABSENT", "note": f"讀 .xls 要 xlrd(缺件≠壞掉 L16;工作站讀 AAII 已有就能讀):{e}"[:160], "rows": []}
    except Exception as e:               # 檔壞 / 擋頁回來的不是 xls:照實 FAIL,不入庫
        return {"state": "FAIL", "note": f"JPX 檔讀不動:{type(e).__name__}: {e}"[:160], "rows": []}
    try:
        rows, as_of = parse_jpx_frame(df)
    except ValueError as e:
        return {"state": "FAIL", "note": str(e)[:160], "rows": []}
    return {"state": "OK" if rows else "EMPTY", "rows": rows, "as_of": as_of}


def store(rows: list, table: str, db: Path = DB_GL) -> tuple:
    if not rows:
        return 0, 0
    db.parent.mkdir(parents=True, exist_ok=True)
    n, t = _LIB.UTILS.upsert_rows(db, table, rows, ["code"], replace=True, counts=True)
    return int(n), int(t)


def read_table(table: str, db: Path = DB_GL) -> list:
    if not Path(db).is_file():
        return []
    import duckdb
    con = duckdb.connect(str(db), read_only=True)
    try:
        if table not in {r[0] for r in con.execute("SHOW TABLES").fetchall()}:
            return []
        cur = con.execute(f'SELECT * FROM "{table}" ORDER BY code')
        names = [d[0] for d in cur.description]
        return [dict(zip(names, r)) for r in cur.fetchall()]
    finally:
        con.close()


def run(only=("us", "jp"), net=None, db: Path = DB_GL, dry: bool = False) -> dict:
    net = net if net is not None else net_tool()
    res = {}
    for key, fn, table in (("us", fetch_us, "us_listings"), ("jp", fetch_jp, "jp_listings")):
        if key not in only:
            continue
        f = fn(net)
        added, total = (0, 0) if dry else store(f["rows"], table, db)
        stocks = sum(1 for r in f["rows"] if r.get("is_stock"))
        res[key] = {"state": f["state"], "rows": len(f["rows"]), "stocks": stocks, "as_of": f.get("as_of"),
                    "added": added, "table_rows": total, "note": f.get("note", "")}
    states = [v["state"] for v in res.values()]
    state = "OK" if states and all(s == "OK" for s in states) else ("DENY" if "DENY" in states else ("PARTIAL" if "OK" in states else (states[0] if states else "NODATA")))
    return {"engine": ENGINE_TAG, "state": state, "markets": res, "dry": dry}


def build_lists(db: Path = DB_GL, owner=None) -> dict:
    """三地總清單 + 主動式 ETF(讀庫與 ENG087,不外呼)。"""
    us = read_table("us_listings", db)
    jp = read_table("jp_listings", db)
    owner = owner if owner is not None else tw_owner()
    tw = owner.load_stock_list() if owner else {"state": "ABSENT", "rows": [], "why": "VDF_ENG087 不在"}
    etf = owner.load_active_etfs() if owner else {"state": "ABSENT", "rows": [], "why": "VDF_ENG087 不在"}
    def pack(state, rows, **kw):
        return dict({"state": state, "count": len(rows), "rows": rows}, **kw)
    return {"engine": ENGINE_TAG, "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "us_stocks": pack("GREEN" if us else "NODATA", [r for r in us if r.get("is_stock")], as_of=(us[0].get("as_of") if us else None)),
            "us_etfs": pack("GREEN" if us else "NODATA", [r for r in us if r.get("is_etf")]),
            "jp_stocks": pack("GREEN" if jp else "NODATA", jp, as_of=(jp[0].get("as_of") if jp else None)),
            "tw_stocks": pack(tw.get("state", "NODATA"), tw.get("rows") or [], why=tw.get("why", "")),
            "tw_active_etfs": pack(etf.get("state", "NODATA"), etf.get("rows") or [], why=etf.get("why", ""))}


def write_lists(payload: dict, out: Path = OUT) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    paths = {}
    for key in ("us_stocks", "jp_stocks", "tw_stocks", "tw_active_etfs"):
        rows = payload[key]["rows"]
        if not rows:
            continue
        p = out / f"{key.upper()}_latest.csv"
        cols = sorted({k for r in rows for k in r})
        with p.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        paths[key] = str(p)
    slim = {k: ({kk: vv for kk, vv in v.items() if kk != "rows"} if isinstance(v, dict) else v) for k, v in payload.items()}
    (out / "GLOBAL_LISTS_latest.json").write_text(json.dumps(dict(slim, files=paths), ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    paths["summary"] = str(out / "GLOBAL_LISTS_latest.json")
    return paths


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "只經 VCGC(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
        return 2
    verb = next((x for x in a if not x.startswith("-")), "status")
    if verb in ("status", "lists"):
        p = build_lists()
        for k in ("us_stocks", "us_etfs", "jp_stocks", "tw_stocks", "tw_active_etfs"):
            v = p[k]
            print(f"  [{k:15s}] {v['state']:7s} {v['count']:>6,} 檔" + (f" · 清單日 {v.get('as_of')}" if v.get("as_of") else "") + (f" · {v.get('why')}" if v.get("why") else ""))
        if verb == "lists":
            paths = write_lists(p)
            print(f"  [總清單] {paths.get('summary')}")
        return 0 if all(p[k]["state"] in ("GREEN", "AMBER") for k in ("us_stocks", "jp_stocks", "tw_stocks")) else 2
    if verb == "run":
        only = tuple(a[a.index("--only") + 1].split(",")) if "--only" in a and a.index("--only") + 1 < len(a) else ("us", "jp")
        r = run(only=only, dry="--dry" in a)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return {"OK": 0, "DENY": 4, "PARTIAL": 1}.get(r["state"], 2)
    print(__doc__)
    return 2


# ---------------------------------------------------------------- 自測(假網路工具 + 暫存庫 + 假 ENG087;零外呼)
class _FakeNet:
    def __init__(self, table: dict, deny: bool = False):
        self.table, self.deny, self.calls = table, deny, []

    def curl_bytes(self, url, headers=None, timeout=30, follow=True):
        self.calls.append(url)
        if self.deny:
            return {"state": "DENY", "note": "gate"}
        for k, v in self.table.items():
            if k in url:
                return {"state": "OK", "data": v}
        return {"state": "FAIL", "note": "no fixture"}


class _FakeOwner:
    def load_stock_list(self):
        return {"state": "GREEN", "rows": [{"code": "2330", "name": "台積電", "market": "TWSE"}, {"code": "6488", "name": "環球晶", "market": "TPEX"}]}

    def load_active_etfs(self):
        return {"state": "GREEN", "rows": [{"code": "00980A", "verified": True}]}


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    nasdaq = ("Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares\n"
              "AAPL|Apple Inc. - Common Stock|Q|N|N|100|N|N\nQQQ|Invesco QQQ Trust|G|N|N|100|Y|N\nZZZT|Test Issue Co|Q|Y|N|100|N|N\n"
              "File Creation Time: 0928202609:00|||||||\n").encode()
    other = ("ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol\n"
             "IBM|International Business Machines|N|IBM|N|100|N|IBM\nSPY|SPDR S&P 500 ETF Trust|P|SPY|Y|100|N|SPY\n"
             "File Creation Time: 0928202609:00|||||||\n").encode()
    rows, as_of = parse_nasdaq_dir(nasdaq.decode(), "nasdaq")
    chk("① NASDAQ 目錄:剔除測試代號、ETF 另標、清單日期讀檔尾", [r["code"] for r in rows] == ["AAPL", "QQQ"] and rows[1]["is_etf"] and as_of == "2026-09-28", str(as_of))
    import pandas as pd
    df = pd.DataFrame({"日付": ["20260831"] * 4, "コード": ["7203", "1306", "4385", "9999"], "銘柄名": ["トヨタ自動車", "TOPIX連動型ETF", "メルカリ", "外国株X"],
                       "市場・商品区分": ["プライム（内国株式）", "ETF・ETN", "グロース（内国株式）", "外国株式"], "33業種区分": ["輸送用機器", "-", "情報・通信業", "-"]})
    jr, jd = parse_jpx_frame(df)
    chk("② JPX:只收内国株式(ETF / 外国株不收)、清單日期轉 ISO", [r["code"] for r in jr] == ["7203", "4385"] and jd == "2026-08-31", f"{[r['code'] for r in jr]} · {jd}")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        db = td / "gl.duckdb"
        fake = _FakeNet({"nasdaqlisted": nasdaq, "otherlisted": other})
        r = run(only=("us",), net=fake, db=db)
        chk("③ 美股經統包工具抓兩檔、合併去重入庫(4 檔:股 2 · ETF 2)", r["markets"]["us"]["rows"] == 4 and r["markets"]["us"]["stocks"] == 2 and len(fake.calls) == 2,
            json.dumps(r["markets"]["us"], ensure_ascii=False))
        r2 = run(only=("us",), net=fake, db=db)
        chk("④ 正典 upsert(replace):再跑一次表內仍 4 列", r2["markets"]["us"]["table_rows"] == 4)
        dn = _FakeNet({}, deny=True)
        d = run(only=("us", "jp"), net=dn, db=td / "deny.duckdb")
        chk("⑤ 同意閘沒開 = DENY:零寫入、庫沒建", d["state"] == "DENY" and not (td / "deny.duckdb").exists())
        jx = run(only=("jp",), net=_FakeNet({"data_j.xls": b"\xd0\xcf\x11\xe0 not really xls"}), db=td / "jp.duckdb")
        chk("⑥ 讀不動 .xls(缺 xlrd 或檔壞)照實報,不當成功、不入庫", jx["markets"]["jp"]["state"] in ("ABSENT", "FAIL") or jx["markets"]["jp"]["rows"] == 0,
            jx["markets"]["jp"]["state"] + " · " + jx["markets"]["jp"]["note"][:60])
        store(jr, "jp_listings", db)
        p = build_lists(db, owner=_FakeOwner())
        chk("⑦ 總清單:美股 2 · 美 ETF 2 · 日股 2 · 台股委派 ENG087 · 主動式 ETF 委派 ENG087",
            (p["us_stocks"]["count"], p["us_etfs"]["count"], p["jp_stocks"]["count"], p["tw_stocks"]["count"], p["tw_active_etfs"]["count"]) == (2, 2, 2, 2, 1))
        paths = write_lists(p, td / "lists")
        chk("⑧ 四份 CSV + 摘要 JSON 落地", all(Path(paths[k]).is_file() for k in ("us_stocks", "jp_stocks", "tw_stocks", "tw_active_etfs", "summary")))
    real = tw_owner()
    chk("⑨ 台灣正主 VDF_ENG087 尾版在且有 load_stock_list / load_active_etfs", real is not None and hasattr(real, "load_stock_list") and hasattr(real, "load_active_etfs"))
    keep = os.environ.pop("VIA_FROM_VCGC", None)
    denied = main(["status"]) == 2
    if keep is not None:
        os.environ["VIA_FROM_VCGC"] = keep
    chk("⑩ 不經 VCGC 就拒跑", denied)
    ok = all(results)
    print(f"  [計] {ENGINE_TAG} 自測 {sum(results)}/{len(results)} · {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
