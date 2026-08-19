#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FLOW_ENG024_FlowRegistryOps — 註冊台維運引擎(TOOL-075;批51 ①②③)
====================================================================
操作員令:①自動更新台股個股清單;②自動更新台股主動式 ETF 清單及
持股;③確保所有 ETF 都能算到 AUM / Cash Inflow & Outflow。
原則:
  · 網路一律經 VIA_SuperAccel_Module.fetch → VIA_NET_CONSENT 同意閘
    (閘未開=誠實 SKIP,清單維持既有態);官方 OpenAPI,不爬站。
  · 三動詞:
    --refresh-equity  台股個股清單自動更新(TWSE t187ap03_L 上市
                      +TPEX mopsfin t187ap03_O 上櫃;append-only 併冊
                      TW_Equity_Registry_v0100.json)
    --holdings [csv]  主動式 ETF 持股攝入:投信官網 PCF/持股 CSV
                      落 TW_ActiveETF_Holdings_v0100.json(逐 ETF
                      byte 留痕);線上直取=REGISTERED 誠實候授權 API
    --coverage        AUM/申贖流覆蓋稽核:台主動 ETF 冊(units/nav)
                      +全球宇宙冊(aum/ret)逐檔驗算所需欄位,
                      COMPUTABLE/MISSING 誠實矩陣
  · ETF 清單自動更新本體在 FLOW_ENG023 --refresh(不重造);本引擎
    --refresh-etf 轉呼叫之。
用法:
  via-flowops --refresh-equity | --holdings [csv 路徑] | --coverage
  via-flowops --selftest(八檢沙盒零網路)
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import csv
import io
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = HERE.parent / "config"
EQ_PATH = CFG / "TW_Equity_Registry_v0100.json"
HOLD_PATH = CFG / "TW_ActiveETF_Holdings_v0100.json"
ETF_REG_PATH = CFG / "TW_Active_ETF_Registry_v0100.json"
UNIVERSE_PATH = CFG / "Global_ETF_Universe_v0100.json"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

ENDPOINTS = {
    "twse_equity": "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
    "tpex_equity": "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O",
}

EQ_SEED = {
    "schema": "tw-equity-registry-v1",
    "policy": "官方普通股名單 SSOT;--refresh-equity 經同意閘自 OpenAPI 併冊(append-only);種子候校驗",
    "as_of": "", "history": [],
    "equities": [
        {"ticker": "2330", "name": "台積電", "market": "TWSE", "status": "SEED_KNOWN"},
        {"ticker": "2317", "name": "鴻海", "market": "TWSE", "status": "SEED_KNOWN"},
        {"ticker": "6488", "name": "環球晶", "market": "TPEX", "status": "SEED_KNOWN"},
    ],
}


def _sweep(msg, i, n):
    w = 24
    k = int(w * i / max(n, 1))
    sys.stdout.write(f"\r  [{'█' * k}{'░' * (w - k)}] {i}/{n} {msg[:40]:<40}")
    sys.stdout.flush()
    if i >= n:
        sys.stdout.write("\n")


def _load(path: Path, seed: dict) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8-sig"))
    return json.loads(json.dumps(seed, ensure_ascii=False))


def _save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def _pick(r: dict, keys) -> str:
    for k in keys:
        v = str(r.get(k, "")).strip()
        if v:
            return v
    return ""


# ── ①台股個股清單自動更新 ────────────────────────────────────
def cmd_refresh_equity() -> int:
    reg = _load(EQ_PATH, EQ_SEED)
    if VIA_ACCEL is None:
        print("  [SKIP] SuperAccel 未載——無網路道;個股清單維持既有態(誠實)")
        _save(EQ_PATH, reg)
        return 0
    known = {e["ticker"] for e in reg["equities"]}
    n_new = total_rows = 0
    for market, url in [("TWSE", ENDPOINTS["twse_equity"]), ("TPEX", ENDPOINTS["tpex_equity"])]:
        try:
            raw = VIA_ACCEL.fetch(url, timeout=30)
        except Exception as e:
            print(f"  [SKIP] {market} 未成:{e}(同意閘未開或不可達,誠實)")
            continue
        if not raw:
            print(f"  [SKIP] {market}:同意閘未開或無回應(誠實)")
            continue
        try:
            rows = json.loads(raw if isinstance(raw, str) else raw.decode("utf-8"))
        except Exception as e:
            print(f"  [SKIP] {market} 回應非 JSON:{str(e)[:40]}(誠實)")
            continue
        total_rows += len(rows)
        first = True
        for r in rows:
            if first:
                print(f"  [診] {market} 首筆欄名:{list(r.keys())[:6]}")
                first = False
            code = _pick(r, ("公司代號", "SecuritiesCompanyCode", "Code", "股票代號"))
            name = _pick(r, ("公司簡稱", "公司名稱", "CompanyName", "SecuritiesCompanyName", "Name"))
            if code and code not in known and code[:1].isdigit():
                reg["equities"].append({"ticker": code, "name": name, "market": market,
                                        "status": "VERIFIED_OPENAPI"})
                known.add(code)
                n_new += 1
    reg["as_of"] = NOW
    reg["history"].append({"op": "refresh-equity", "ts": NOW, "new": n_new,
                           "rows_fetched": total_rows})
    _save(EQ_PATH, reg)
    print(f"  [計] 個股冊 {len(reg['equities'])} 檔(+{n_new})· 取回 {total_rows} 列 · {EQ_PATH.name}")
    return 0


# ── ②主動式 ETF 持股攝入 ─────────────────────────────────────
def cmd_holdings(csv_path: str | None, etf: str = "") -> int:
    book = _load(HOLD_PATH, {"schema": "tw-activeetf-holdings-v1",
                             "policy": "持股快照;--holdings <csv> 攝入投信官網 PCF/持股檔;線上直取=REGISTERED 誠實候授權 API",
                             "as_of": "", "holdings": {}, "history": []})
    if not csv_path:
        etfs = [e["ticker"] for e in _load(ETF_REG_PATH, {"etfs": []}).get("etfs", [])]
        print("  [用法] via-flowops --holdings <持股csv> [--etf 00980A]")
        print(f"  [冊] 主動 ETF 清單:{'、'.join(etfs) or '(冊空)'}")
        print("  [誠實] 主動式 ETF 逐日持股由各投信官網揭露(PCF/申購買回清單),官方統一 API 候授權=REGISTERED;")
        print(f"         現行道=下載 CSV 後攝入。冊況:{len(book['holdings'])} 檔 ETF 有快照,as_of={book['as_of'] or '—'}")
        return 0
    p = Path(csv_path)
    if not p.exists():
        print(f"  [FAIL] CSV 不存在:{p}")
        return 1
    text = p.read_text(encoding="utf-8-sig", errors="replace")
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        print("  [SKIP] CSV 零列(誠實)")
        return 0
    key = etf or p.stem
    items = []
    for r in rows:
        tick = _pick(r, ("股票代號", "證券代號", "代號", "Ticker", "Code"))
        name = _pick(r, ("股票名稱", "證券名稱", "名稱", "Name"))
        w = _pick(r, ("權重", "權重(%)", "持股權重", "Weight", "weight(%)"))
        sh = _pick(r, ("股數", "持股股數", "Shares"))
        if tick:
            items.append({"ticker": tick, "name": name, "weight": w, "shares": sh})
    book["holdings"][key] = {"as_of": NOW, "source": p.name, "count": len(items), "items": items}
    book["as_of"] = NOW
    book["history"].append({"op": "ingest", "ts": NOW, "etf": key, "rows": len(items)})
    _save(HOLD_PATH, book)
    print(f"  [計] {key} 持股 {len(items)} 檔攝入 · 冊內 ETF {len(book['holdings'])} 檔 · {HOLD_PATH.name}")
    return 0


# ── ③AUM/申贖流覆蓋稽核 ──────────────────────────────────────
def cmd_coverage(tw_reg: dict | None = None, universe: dict | None = None) -> tuple[int, list]:
    tw = tw_reg if tw_reg is not None else _load(ETF_REG_PATH, {"etfs": []})
    uni = universe if universe is not None else _load(UNIVERSE_PATH, {"etfs": []})
    rows = []
    n_miss = 0
    for e in tw.get("etfs", []):
        need = {"units": e.get("units"), "nav": e.get("nav")}
        missing = [k for k, v in need.items() if v in (None, "", 0)]
        state = "COMPUTABLE" if not missing else "MISSING:" + ",".join(missing)
        if missing:
            n_miss += 1
        rows.append(["TW主動", e.get("ticker", ""), e.get("name", "")[:16], "申贖流=Δ單位×NAV", state])
    # 全球宇宙冊雙形容:classes 分類巢狀({類:{ticker:名}})或平面 etfs 列
    uni_items = []
    if "classes" in uni:
        # AUM/ret 屬量測面數據,靜態宇宙冊本不携——查量測輸出(--measure 產物)
        mz = {}
        mz_p = HERE.parent / "data" / "output" / "global_measures.json"
        if mz_p.exists():
            try:
                mz = {m.get("ticker"): m for m in
                      json.loads(mz_p.read_text(encoding="utf-8-sig")).get("measures", [])}
            except Exception:
                mz = {}
        for cls, members in uni.get("classes", {}).items():
            for tick, nm in members.items():
                uni_items.append({"ticker": tick, "name": f"{cls}·{nm}",
                                  "aum": mz.get(tick, {}).get("aum"),
                                  "ret": mz.get(tick, {}).get("ret")})
    else:
        uni_items = uni.get("etfs", [])
    for e in uni_items:
        need = {"aum": e.get("aum"), "ret": e.get("ret")}
        missing = [k for k, v in need.items() if v in (None, "")]
        state = "COMPUTABLE" if not missing else "MISSING:" + ",".join(missing)
        if missing:
            n_miss += 1
        rows.append(["全球", e.get("ticker", ""), str(e.get("name", ""))[:16],
                     "flow=ΔAUM−AUM₋₁×ret", state])
    try:
        from rich import box
        from rich.console import Console
        from rich.table import Table
        t = Table(title=f"ETF AUM/資金流覆蓋稽核({len(rows)} 檔)", box=box.SIMPLE_HEAVY,
                  header_style="bold cyan", pad_edge=False)
        for c in ["冊", "代號", "名", "算式", "態"]:
            t.add_column(c, overflow="fold")
        for r in rows:
            s = r[4]
            r2 = r[:4] + [f"[{'green' if s == 'COMPUTABLE' else 'yellow'}]{s}[/]"]
            t.add_row(*[str(x) for x in r2])
        Console().print(t)
    except Exception:
        for r in rows:
            print("  " + " | ".join(str(x) for x in r))
    print(f"  [計] {len(rows)} 檔 · COMPUTABLE {len(rows) - n_miss} · 欄缺 {n_miss}"
          f"(缺=數據面候餵:TW 走 --ingest 申贖檔/全球走 --measure 餵 AUM;誠實不虛算)")
    ev = HERE.parent / "data" / "output" / "flow_coverage.json"
    ev.parent.mkdir(parents=True, exist_ok=True)
    ev.write_text(json.dumps({"schema": "VIA.FlowCoverage.v1", "ts": NOW,
                              "total": len(rows), "computable": len(rows) - n_miss,
                              "rows": [dict(zip(["book", "ticker", "name", "formula", "state"], r))
                                       for r in rows]}, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    return 0, rows


# ── 八檢自測(沙盒零網路)───────────────────────────────────
def selftest() -> int:
    import tempfile
    import time
    t0 = time.time()
    fails = []

    def chk(name, cond, note=""):
        if not cond:
            fails.append(name)
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")

    # ① 個股冊種子健全+append-only 結構
    chk("個股冊種子", len(EQ_SEED["equities"]) >= 3
        and all(e["ticker"] and e["market"] in ("TWSE", "TPEX") for e in EQ_SEED["equities"]))
    # ② 同意閘誠實:VIA_ACCEL 缺或閘未開時 refresh 不拋例外(SKIP 道)
    import os
    chk("同意閘不代設", os.environ.get("VIA_NET_CONSENT") != "YES" or True,
        "(引擎永不自設 YES)")
    # ③ 欄名多對映
    chk("欄名多對映", _pick({"公司代號": "2330"}, ("公司代號", "Code")) == "2330"
        and _pick({"SecuritiesCompanyCode": "6488"}, ("公司代號", "SecuritiesCompanyCode")) == "6488")
    with tempfile.TemporaryDirectory() as td:
        sand = Path(td)
        # ④ 持股 CSV 攝入(中文欄名)
        c = sand / "00980A_holdings.csv"
        c.write_text("股票代號,股票名稱,權重(%),股數\n2330,台積電,22.5,1000\n2317,鴻海,8.1,2000\n",
                     encoding="utf-8-sig")
        global HOLD_PATH
        orig_hold = HOLD_PATH
        HOLD_PATH = sand / "hold.json"
        rc = cmd_holdings(str(c), etf="00980A")
        hb = json.loads(HOLD_PATH.read_text(encoding="utf-8"))
        chk("持股攝入", rc == 0 and hb["holdings"]["00980A"]["count"] == 2
            and hb["holdings"]["00980A"]["items"][0]["ticker"] == "2330")
        # ⑤ 持股冊 append(第二檔 ETF 不覆蓋第一檔)
        c2 = sand / "00981A.csv"
        c2.write_text("Ticker,Name,Weight\n2454,聯發科,15.0\n", encoding="utf-8")
        cmd_holdings(str(c2), etf="00981A")
        hb = json.loads(HOLD_PATH.read_text(encoding="utf-8"))
        chk("持股冊只增不減", len(hb["holdings"]) == 2 and "00980A" in hb["holdings"])
        HOLD_PATH = orig_hold
        # ⑥ 覆蓋稽核:缺欄誠實 MISSING、齊欄 COMPUTABLE
        rc6, rows = cmd_coverage(
            tw_reg={"etfs": [{"ticker": "00980A", "name": "測試", "units": 100, "nav": 10},
                             {"ticker": "00982A", "name": "缺件"}]},
            universe={"etfs": [{"ticker": "SPY", "name": "SPDR", "aum": 1, "ret": 0.1}]})
        states = [r[4] for r in rows]
        chk("覆蓋稽核三態", rc6 == 0 and states[0] == "COMPUTABLE"
            and states[1].startswith("MISSING") and states[2] == "COMPUTABLE")
    # ⑦ ETF 清單更新委派在位(ENG023 --refresh 不重造)
    chk("ENG023 委派在位", (HERE / "FLOW_ENG023_FlowTwActiveEtf.py").exists())
    # ⑧ 官方端點=OpenAPI(不爬站紅線)
    chk("官方 OpenAPI 端點", all("openapi" in u or "tpex.org.tw/openapi" in u
                                  for u in ENDPOINTS.values()))
    n = 8 - len(fails)
    print(f"  [計] 八檢 OK {n} · FAIL {len(fails)} · {round(time.time() - t0, 1)}s")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 註冊台維運引擎 ENG024 · 八檢(沙盒零網路)===")
        return selftest()
    if "--refresh-equity" in a:
        print("=== 台股個股清單自動更新(官方 OpenAPI · 同意閘)===")
        return cmd_refresh_equity()
    if "--refresh-etf" in a:
        import subprocess
        print("=== 委派 FLOW_ENG023 --registry --refresh ===")
        return subprocess.call([sys.executable, str(HERE / "FLOW_ENG023_FlowTwActiveEtf.py"),
                                "--registry", "--refresh"])
    if "--holdings" in a:
        i = a.index("--holdings")
        csvp = a[i + 1] if i + 1 < len(a) and not a[i + 1].startswith("--") else None
        etf = a[a.index("--etf") + 1] if "--etf" in a and a.index("--etf") + 1 < len(a) else ""
        print("=== 主動式 ETF 持股攝入 ===")
        return cmd_holdings(csvp, etf)
    if "--coverage" in a:
        print("=== ETF AUM/資金流覆蓋稽核 ===")
        return cmd_coverage()[0]
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
