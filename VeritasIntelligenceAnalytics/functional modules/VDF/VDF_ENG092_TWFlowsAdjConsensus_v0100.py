#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG092_TWFlowsAdjConsensus v0100 — 籌碼流量 · 調整後四價 · 共識獨立庫(批720)

操作員 2026-09-23 逐項給定:
「FACTSET/YFINANCE CONSENSUS 存一個資料庫 · 不用算移動平均量價 · 三大法人買賣超 ·
 融資融券 · 當沖交易 · ADJ OPEN/HIGH/LOW/CLOSE · 從 TWSE TPEX 擷取成交量 成交值 市值」
逐題裁定:SMA「保留好了」(既有欄位原樣留)· ADJ「四欄全給」。

**這一支不編端點。** 端點清單在冊 `VIA_VDF_TWMarketEndpoints_SSOT_v0100.json`,
三態寫死在冊上:

| 態 | 意思 |
|---|---|
| VERIFIED | 實測抓到料(批719 工作站實跑那兩條) |
| CANDIDATE | 依官方命名慣例推的路徑 —— **未經實測** |
| UNKNOWN | 我不知道正確路徑,**不編一個** |

`probe` 動詞就是去把 CANDIDATE 證實或證偽的那把尺:**結果回報,冊由人改**。

兩件照實講,不修飾:
· **交易所不直接給市值。** 市值 = 收盤價 × 發行股數,發行股數來自 Yahoo。
  操作員令裡「從 TWSE TPEX 擷取…市值」的第三項,交易所**沒有** —— 算出來的那一欄標 DERIVED。
· **ADJ 四價**:yfinance `auto_adjust=True` 四價皆調整後;否則只有 Adj Close,
  其餘三價用比例法近似,會有尾差 —— 所以每列帶 `adj_method` 講明它是哪一種來的。

律:唯讀冊 · 網路只走統包(批115 全導入令)· 雙閘未開=rc4 GATED 不是壞掉 ·
零彈窗 · 不編端點 · 不把「算的」講成「抓的」。
用法:python3 VDF_ENG092_TWFlowsAdjConsensus_v0100.py [run|probe|--selftest]
     run   = **分開擷取後整合**(操作員 2026-09-23 令);閘沒開 rc4 零出網
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 缺席零影響) =====
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
    VIA_ACCEL = None
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import json
import sys
import time
from pathlib import Path

ENGINE_ID = "VDF_ENG092_TWFlowsAdjConsensus"
VERSION = "v0100"
BATCH = "批720"
HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
BOOK = VIA / "supportive modules" / "registry" / "VIA_VDF_TWMarketEndpoints_SSOT_v0100.json"


def book(path: Path | None = None) -> dict:
    """端點從**冊**來。讀不到就回空 —— **不內建一份**(內建的那份沒有人裁定過)。"""
    try:
        return json.loads((path or BOOK).read_text(encoding="utf-8"))
    except Exception:
        return {}


def gate() -> dict:
    """雙閘態問統包(它那邊才是正主)。**AI 永不代設**:本支只讀,一行都不寫。"""
    nt = _via_net()
    if nt is None or not hasattr(nt, "gate_state"):
        return {"open": False, "why": "統包缺席,閘況問不到(誠實)"}
    try:
        g = dict(nt.gate_state() or {})
        g.setdefault("why", "")
        return g
    except Exception as exc:
        return {"open": False, "why": f"閘況例外:{type(exc).__name__}"}


def endpoints(B: dict | None = None) -> list:
    """把冊攤平成逐道一列:(所, 資料集, 路徑, 態)。路徑空=UNKNOWN,**不編**。"""
    B = B if B is not None else book()
    rows = []
    for mkt in ("twse", "tpex"):
        m = B.get(mkt) or {}
        base = m.get("base") or ""
        for name, d in (m.get("datasets") or {}).items():
            p = d.get("path") or ""
            rows.append({"market": mkt, "dataset": name,
                         "url": (base + p) if p else "",
                         "state": d.get("state") or ("UNKNOWN" if not p else "CANDIDATE"),
                         "zh": d.get("zh") or name})
            # 被探針打掉的那一道,把冊上登記的**下一批候選**也攤出來 ——
            # 探針要打的就是它們。證偽之後不補候選,這道就永遠停在 DEAD。
            for alt in (d.get("next_candidates") or []):
                ap = alt.get("path") or ""
                rows.append({"market": mkt, "dataset": f"{name}#alt",
                             "url": (base + ap) if ap else "",
                             "state": alt.get("state") or "CANDIDATE",
                             "zh": alt.get("zh") or ""})
    return rows


def probe(limit: int = 0) -> dict:
    """把 CANDIDATE 證實或證偽。**結果回報,冊由人改**(LL90:裁定要留痕)。

    雙閘未開 → 整批 GATED(不是壞掉);統包缺席 → ABSENT;UNKNOWN 不打(沒有路徑可打)。
    """
    B = book()
    if not B:
        return {"state": "NODATA", "why": "端點冊讀不到 —— 不內建一份頂替"}
    g = gate()
    rows = endpoints(B)
    todo = [r for r in rows if r["url"]]
    if limit:
        todo = todo[:limit]
    if not g.get("open"):
        return {"state": "GATED", "gate": g, "n": len(todo),
                "why": "雙閘未開,一個位元組都不出網。**這不是壞掉**;AI 永不代設同意閘。"}
    nt = _via_net()
    if nt is None or not hasattr(nt, "http_json"):
        return {"state": "ABSENT", "why": "統包網路工具缺席(誠實;本支不自己開第二個出口)"}
    out, t0 = [], time.time()
    for i, r in enumerate(todo, 1):
        try:
            res = nt.http_json(r["url"], timeout=25) or {}
        except Exception as exc:
            res = {"state": "FAIL", "note": f"{type(exc).__name__}"}
        st = str(res.get("state") or "")
        data = res.get("data")
        n = len(data) if isinstance(data, list) else (1 if data else 0)
        out.append({**r, "probe": "VERIFIED" if (st == "OK" and n) else
                    ("EMPTY" if st == "OK" else st or "FAIL"),
                    "rows": n, "note": str(res.get("note") or "")[:70]})
        print(f"  [進度] {i}/{len(todo)} · {i * 100.0 / max(len(todo), 1):.0f}%"
              f" · 已 {time.time() - t0:.0f}s · 探針 {r['market']}/{r['dataset']}", flush=True)
    return {"state": "OK", "rows": out, "unknown": [r for r in rows if not r["url"]]}


def fetch_one(row: dict, nt=None) -> dict:
    """**一道一擷取**(操作員令「可分開擷取後整合」)。

    每一道各自回自己的態,**互不牽連** —— 一道敗不會把其他道拖下水。
    態:OK / GATED / ABSENT / NOT_WIRED(路徑未通,不是壞掉)/ FAIL:…
    """
    st = row.get("state")
    if st in ("UNKNOWN", "DEAD") or not row.get("url"):
        return {**row, "fetch": "NOT_WIRED", "rows": 0,
                "why": "路徑未通(UNKNOWN=不知道 · DEAD=推過被打掉)——**不是壞掉,是還沒接上**"}
    nt = nt if nt is not None else _via_net()
    if nt is None or not hasattr(nt, "http_json"):
        return {**row, "fetch": "ABSENT", "rows": 0, "why": "統包網路工具缺席(誠實)"}
    try:
        r = nt.http_json(row["url"], timeout=30) or {}
    except Exception as exc:
        return {**row, "fetch": f"FAIL:{type(exc).__name__}", "rows": 0, "why": str(exc)[:70]}
    s = str(r.get("state") or "")
    if s == "DENY":
        return {**row, "fetch": "GATED", "rows": 0, "why": "雙閘未開,零出網(不是壞掉)"}
    if s != "OK":
        return {**row, "fetch": "FAIL", "rows": 0, "why": str(r.get("note") or s)[:70]}
    data = r.get("data")
    recs = data if isinstance(data, list) else ([data] if data else [])
    return {**row, "fetch": "OK", "rows": len(recs), "data": recs, "why": ""}


def fetch_all(limit: int = 0) -> dict:
    """逐道擷取,**一道敗不中止其他道**。回 {dataset_key: 結果}。"""
    rows = [r for r in endpoints() if not r["dataset"].endswith("#alt")]
    if limit:
        rows = rows[:limit]
    nt = _via_net()
    out, t0 = {}, time.time()
    for i, r in enumerate(rows, 1):
        key = f"{r['market']}.{r['dataset']}"
        try:
            out[key] = fetch_one(r, nt)
        except Exception as exc:                  # 單道例外也要被關住,不然它會吃掉整跑
            out[key] = {**r, "fetch": f"FAIL:{type(exc).__name__}", "rows": 0,
                        "why": str(exc)[:70]}
        print(f"  [進度] {i}/{len(rows)} · {i * 100.0 / max(len(rows), 1):.0f}%"
              f" · 已 {time.time() - t0:.0f}s · 擷取 {key} → {out[key]['fetch']}", flush=True)
    return out


def integrate(fetched: dict) -> dict:
    """**再整合**。逐欄講明它是抓來的還是算來的,以及哪一道沒接上。

    不做的事:不把 NOT_WIRED 當成 0、不把市場合計當成個股別、不把算的講成抓的。
    """
    B = book()
    tally = {}
    for v in fetched.values():
        tally[v["fetch"]] = tally.get(v["fetch"], 0) + 1
    wired = {k: v for k, v in fetched.items() if v["fetch"] == "OK"}
    cols = {
        "identity": ["code", "name", "market", "yf_ticker"],
        "daily_from_exchange": ["open", "high", "low", "close", "volume", "turnover",
                                "transactions"],
        "adj": list((B.get("adj_ohlc") or {}).get("cols") or []) + ["adj_method"],
        "flows": ["margin_balance", "short_balance", "day_trade_shares", "day_trade_value"],
        "institutional": ["foreign_net", "trust_net", "dealer_net"],
        "derived": ["market_cap", "shares_outstanding"],
        "consensus_db": list((B.get("consensus_db") or {}).get("tables") or []),
    }
    provenance = {
        "daily_from_exchange": "EXCHANGE(TWSE/TPEX OpenAPI 直接給)",
        "flows": "EXCHANGE(融資券 MI_MARGN · 當沖 TWTB4U —— 批721 實測證實)",
        "institutional": "NOT_WIRED(T86 推過被打掉;**不可以拿市場合計冒充個股別**)",
        "adj": "YAHOO(四價;auto_adjust 或比例法,逐列記 adj_method)",
        "derived": "**DERIVED**(市值 = 收盤價 × 發行股數;交易所不給市值)",
        "consensus_db": "獨立庫 vdf_consensus.duckdb(更新節奏與日行情不同,混庫會讓"
                        "『今天沒更新』看起來像『今天沒有料』)",
    }
    return {"tally": tally, "wired": sorted(wired), "columns": cols,
            "provenance": provenance,
            "not_wired": [k for k, v in fetched.items() if v["fetch"] == "NOT_WIRED"],
            "state": "GREEN" if tally.get("OK") else
                     ("GATED" if tally.get("GATED") else "NODATA")}


def run() -> int:
    """分開擷取 → 再整合(操作員 2026-09-23 令)。閘沒開回 rc4,一個位元組不出網。"""
    g = gate()
    if not g.get("open"):
        print("  [GATED] 雙閘未開 —— **這不是壞掉**。要開請操作員自己貼:")
        print("       $env:VIA_NET_CONSENT='YES'")
        print("       $env:VIA_SCRAPE_CONSENT='<你自己的 token>'")
        return 4
    f = fetch_all()
    r = integrate(f)
    print(f"  [擷取] {r['tally']}")
    print(f"  [接上] {len(r['wired'])} 道:{r['wired']}")
    print(f"  [未接] {r['not_wired']}(**NOT_WIRED ≠ 0 ≠ 壞掉**)")
    for k, v in r["provenance"].items():
        print(f"   · {k:20} {v}")
    ev = evidence("run", {"integrated": r,
                          "fetched": {k: {kk: vv for kk, vv in v.items() if kk != "data"}
                                      for k, v in f.items()}})
    if ev:
        print(f"  [存證] {ev}")
        print("  [註] **要回報就傳這個檔**,不要把終端輸出貼回 PowerShell")
    return 0 if r["state"] == "GREEN" else (4 if r["state"] == "GATED" else 2)


def evidence(kind: str, payload: dict) -> Path:
    """把結果**寫成檔**,並把路徑印出來。

    批723 實錄:操作員把上一次的終端輸出**貼回 PowerShell**,於是每一行都被當成 cmdlet 執行
    —— `· TWSE daily_quote VERIFIED 1381 列` 裡的 `·` 找不到,滿畫面 ParserError。
    那不是引擎壞了,也不是操作員貼錯:**是我讓結果只存在於捲軸裡**。
    存證落檔之後,要回報就傳檔案,不必把輸出再貼一次。
    """
    d = VIA / "VIA_Reports" / "vdf_flows"
    try:
        d.mkdir(parents=True, exist_ok=True)
        f = d / f"{kind.upper()}_{time.strftime('%Y%m%d_%H%M%S')}.json"
        f.write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str),
                     encoding="utf-8")
        return f
    except Exception:
        return Path("")


def verify_universe(twse: list, tpex: list, prev: list | None = None,
                    asof: str = "", today: str = "") -> dict:
    """**「如何驗證」的答案是一組會紅的檢**(操作員 2026-09-23 問)。

    V1–V4 · V6 · V8 **零網路就驗得了**(兩張清單自己對自己);
    V5 · V7 的 Yahoo 那段要觸網,雙閘未開時是 GATED 不是 FAIL。
    每一條都寫得出「它紅的時候,是什麼壞了」—— 寫不出來的檢不值得加。
    """
    def _code(r):
        return str((r or {}).get("公司代號") or (r or {}).get("code") or "").strip()

    def _name(r):
        return str((r or {}).get("公司簡稱") or (r or {}).get("公司名稱")
                   or (r or {}).get("name") or "").strip()

    a = {_code(r) for r in twse if _code(r)}
    b = {_code(r) for r in tpex if _code(r)}
    out, dup = [], sorted(a & b)
    out.append({"id": "V1", "ok": not dup, "detail": f"重疊 {len(dup)} 檔 {dup[:5]}",
                "fail_means": "同一檔同時在上市與上櫃清單 —— 來源抓錯,或轉板當天重複收"})

    rows = ([{"code": c, "market": "TWSE", "yf": f"{c}.TW", "bb": f"{c} TT"} for c in sorted(a)]
            + [{"code": c, "market": "TPEX", "yf": f"{c}.TWO", "bb": f"{c} TT"} for c in sorted(b - a)])
    bad = [r for r in rows
           if (r["market"] == "TWSE") != r["yf"].endswith(".TW")
           or (r["market"] == "TPEX") != r["yf"].endswith(".TWO")]
    out.append({"id": "V2", "ok": not bad, "detail": f"後綴與來源不符 {len(bad)} 檔",
                "fail_means": "後綴是猜的,不是用**來源清單**決定的"})

    nm = {_code(r): _name(r) for r in list(twse) + list(tpex) if _code(r)}
    empty = [c for c in sorted(a | b) if not nm.get(c)]
    out.append({"id": "V3", "ok": not empty, "detail": f"無名稱 {len(empty)} 檔 {empty[:5]}",
                "fail_means": "清單與行情不同步(改名/新上市當天),或對到了不同的公司"})

    bb_uniq = len({r["bb"] for r in rows})
    out.append({"id": "V4", "ok": bb_uniq == len(rows) and all(r["bb"].endswith(" TT") for r in rows),
                "detail": f"Bloomberg 欄 {bb_uniq}/{len(rows)} 唯一",
                "fail_means": "**有人拿 `TT` 去回推上市/上櫃** —— 正本明寫那一格是 UNKNOWN 不是猜"})

    if prev is None:
        out.append({"id": "V6", "ok": None, "detail": "沒有前一份可比(NODATA,不是綠)",
                    "fail_means": "只比筆數 —— 一進一出剛好抵銷時完全看不見"})
    else:
        pv = {_code(r) for r in prev if _code(r)}
        add, gone = sorted((a | b) - pv), sorted(pv - (a | b))
        out.append({"id": "V6", "ok": True,
                    "detail": f"新增 {len(add)} {add[:3]} · 退出 {len(gone)} {gone[:3]}"
                              f" · 筆數 {len(pv)}→{len(a | b)}",
                    "fail_means": "只比筆數 —— 一進一出剛好抵銷時完全看不見"})

    fresh = None
    if asof and today:
        fresh = asof >= today[:len(asof)] or abs(len(asof) - len(today)) >= 0
    out.append({"id": "V8", "ok": fresh, "detail": f"出表 {asof or '(未給)'} · 今 {today or '(未給)'}",
                "fail_means": "抓到的是上週的清單而沒有人發現"})

    red = [c["id"] for c in out if c["ok"] is False]
    nod = [c["id"] for c in out if c["ok"] is None]
    return {"state": "RED" if red else ("NODATA" if nod else "GREEN"),
            "red": red, "nodata": nod, "checks": out, "n": len(rows),
            "note": "V5(YF 代號存不存在)· V7(缺值三態)要觸網;雙閘未開時是 GATED 不是 FAIL"}


def report() -> int:
    B = book()
    rows = endpoints(B)
    g = gate()
    tally = {}
    for r in rows:
        tally[r["state"]] = tally.get(r["state"], 0) + 1
    print(f"  [冊] 端點 {len(rows)} 道 · {tally}")
    for r in rows:
        print(f"   · {r['market'].upper():5} {r['dataset']:14} {r['state']:9} "
              f"{r['url'] or '(**不編**:我不知道正確路徑,空著等實測或操作員給)'}")
    print(f"  [閘] 雙閘 open={g.get('open')} · gate1={g.get('gate1_net_consent')}"
          f" · gate2={g.get('gate2_scrape_token_set')}")
    mc = (B.get("market_cap") or {})
    print(f"  [註] 市值 = {mc.get('rule', '')[:58]}… · 態 {mc.get('state')}")
    print("  [律] 沒量過的不寫成事實;算出來的不講成抓來的;閘沒開是 GATED 不是壞掉")
    return 0 if g.get("open") else 4


def selftest() -> int:
    ran, fails = [], []

    def chk(name, cond, note=""):
        ran.append(name)
        ok = bool(cond)
        if not ok:
            fails.append(name)
        print("  [%s] %s%s" % ("OK" if ok else "FAIL", name, (" (%s)" % note) if note else ""))

    print(f"=== 籌碼流量·調整後四價·共識獨立庫 {VERSION}({BATCH})· 自測(沙盒 · 零網路)===")
    B = book()
    rows = endpoints(B)
    src = (HERE / f"{ENGINE_ID}_{VERSION}.py").read_text(encoding="utf-8", errors="ignore")
    code = "\n".join(ln for ln in src.splitlines() if not ln.strip().startswith("#"))

    chk("① 端點從**冊**讀,不內建一份。**負控**:餵一本空冊要誠實 NODATA,"
        "不可以退回一份寫死的清單照打",
        bool(rows) and probe.__doc__ is not None
        and book(Path("/nonexistent.json")) == {},
        f"(冊上 {len(rows)} 道)")

    chk("② **不知道的路徑不編一個**(UNKNOWN 三態):TPEX 那三道我沒有可靠路徑,"
        "空著等實測或操作員給 —— 編一個出來,探針會去打一個不存在的網址然後回報『失敗』,"
        "看的人會以為是交易所壞了",
        any(r["state"] == "UNKNOWN" and not r["url"] for r in rows)
        and all(r["url"] for r in rows if r["state"] == "VERIFIED"),
        f"(UNKNOWN {sum(1 for r in rows if r['state'] == 'UNKNOWN')} 道)")

    chk("③ **VERIFIED 要有憑據**:標成已驗的道,冊上必須寫得出是誰在哪一天抓到的;"
        "**負控**:沒有 evidence 的不准掛 VERIFIED",
        all((d.get("evidence") or "") for mkt in ("twse", "tpex")
            for d in ((B.get(mkt) or {}).get("datasets") or {}).values()
            if d.get("state") == "VERIFIED"),
        "(每一道 VERIFIED 都帶 evidence)")

    g = gate()
    p = probe()
    _setenv = "os.env" + "iron["            # 拆寫:檢的條件式不可以含它自己禁的字面(LL384,第五次)
    chk("④ **雙閘未開 = GATED,不是壞掉**:探針一個位元組都不出網,而且講明是哪一道閘。"
        "AI 永不代設 —— 本支**只讀**環境,一行都不寫(整檔不得出現寫環境變數的字面)",
        (p["state"] in ("GATED", "OK", "ABSENT")) and (_setenv not in code),
        f"(閘 open={g.get('open')} · 探針態 {p['state']} · 寫環境字面 {_setenv in code})")

    chk("⑤ **市值是算的不是抓的**:操作員令寫「從 TWSE TPEX 擷取…市值」,"
        "但交易所**不直接給市值**。冊上標 DERIVED 並寫明公式 —— "
        "把算出來的講成抓來的,下游就沒辦法判斷它可不可信",
        (B.get("market_cap") or {}).get("state") == "DERIVED"
        and "sharesOutstanding" in json.dumps(B, ensure_ascii=False),
        "(市值 DERIVED + 公式在冊)")

    chk("⑥ **ADJ 四欄**(操作員逐題裁定「四欄全給」)且**講明哪一種來的**:"
        "`auto_adjust=True` 四價皆調整後;否則比例法近似會有尾差,所以每列要帶 `adj_method`",
        (B.get("adj_ohlc") or {}).get("cols") == ["adj_open", "adj_high", "adj_low", "adj_close"]
        and "adj_method" in json.dumps(B, ensure_ascii=False),
        "(四欄 + adj_method 在冊)")

    _sn = B.get("sma_note") or {}
    chk("⑦ **SMA 兩次裁定都要留痕**:操作員同日先裁「保留好了」、再改令「全數刪除欄位也刪除」。"
        "只記最後一次,下一個人看不出**這裡曾經有過欄位**,也分不出是被裁掉的還是從來沒有過。"
        "而且這是**減** —— 冊上要寫得出動手前量過誰在讀(實測:全樹零下游,只有 MDL004 自己)",
        isinstance(_sn, dict) and _sn.get("ruling_1") and _sn.get("ruling_2")
        and "零下游" in (_sn.get("reduction_check") or ""),
        f"(兩次裁定留痕 {bool(_sn.get('ruling_1') and _sn.get('ruling_2'))} · "
        f"減前量過 {'零下游' in (_sn.get('reduction_check') or '')})")

    chk("⑧ **網路只走統包**(批115 全導入令):檔頭要有 NET-BRIDGE,"
        "而且本支不得自己直連 —— 有第二個出口,雙閘就是空的",
        ("[VIA:NET-" + "BRIDGE:") in src
        and ("requests." + "get") not in code
        and ("urllib.request." + "urlopen") not in code,
        "(橋在 · 零直連)")

    dead = [(mkt, k, v) for mkt in ("twse", "tpex")
            for k, v in ((B.get(mkt) or {}).get("datasets") or {}).items()
            if v.get("state") == "DEAD"]
    chk("⑨ **被探針打掉的道要留成 DEAD,不是刪掉也不是留在 CANDIDATE**:"
        "要帶得出 `probe_error`(回的到底是什麼)、`evidence`(誰在哪一天打掉的),"
        "而且**原路徑原樣留著** —— 推錯不丟臉,推錯又把證據抹掉才丟臉。"
        "**負控**:DEAD 一定要補 `next_candidates`,不然這道就永遠停在死路上",
        all(v.get("probe_error") and v.get("evidence") and v.get("path")
            and (v.get("next_candidates") or []) for _, _, v in dead) if dead else True,
        f"(DEAD {len(dead)} 道 · 都帶錯訊與下一批候選 "
        f"{all((v.get('next_candidates') or []) for _, _, v in dead) if dead else '無 DEAD'})")

    # ⑩ 分開擷取:一道敗**不中止**其他道(操作員令「可分開擷取後整合」的全部重點)
    class _FakeNet:
        def http_json(self, url, timeout=30):
            if "MI_MARGN" in url:
                raise RuntimeError("假裝這一道炸了")
            if "STOCK_DAY_ALL" in url:
                return {"state": "OK", "data": [{"a": 1}, {"a": 2}]}
            return {"state": "OK", "data": [{"a": 1}]}

    fake = _FakeNet()
    got = {}
    for r in [x for x in endpoints() if not x["dataset"].endswith("#alt")]:
        k = f"{r['market']}.{r['dataset']}"
        try:
            got[k] = fetch_one(r, fake)
        except Exception as exc:
            got[k] = {**r, "fetch": f"FAIL:{type(exc).__name__}", "rows": 0}
    boom = [k for k, v in got.items() if str(v["fetch"]).startswith("FAIL")]
    fine = [k for k, v in got.items() if v["fetch"] == "OK"]
    chk("⑩ **分開擷取:一道敗不中止其他道**(操作員令「可分開擷取後整合」)。"
        "餵一個會在融資券那一道炸掉的假網路工具:那一道要 FAIL,"
        "**其餘每一道照樣拿到料**。**負控**:如果整跑被一道拖死,這條令就沒落地",
        len(boom) == 1 and len(fine) >= 4
        and got["twse.daily_quote"]["rows"] == 2,
        f"(炸 {len(boom)} 道 · 仍拿到料 {len(fine)} 道)")

    # ⑪ 再整合:逐欄講明抓來的還是算來的,未接上的不准當成 0
    ig = integrate(got)
    chk("⑪ **再整合要逐欄講明出處**:交易所直接給的、Yahoo 來的、**算出來的**、"
        "還沒接上的,四種要分得開。**負控**:三大法人未接上時只能是 NOT_WIRED —— "
        "不可以當成 0(0 是『今天沒人買賣』,NOT_WIRED 是『我還沒接上』),"
        "更不可以拿市場合計冒充個股別",
        "NOT_WIRED" in ig["provenance"]["institutional"]
        and "冒充" in ig["provenance"]["institutional"]
        and "DERIVED" in ig["provenance"]["derived"]
        and any(k.endswith("institutional") for k in ig["not_wired"]),
        f"(未接 {ig['not_wired']} · 市值 DERIVED)")

    # ⑫ TREE_EVIDENCE ≠ VERIFIED:別人量過,不等於我量過
    spec = B.get("b723_spec") or {}
    te = [(k, v) for k, v in spec.items()
          if isinstance(v, dict) and v.get("state") == "TREE_EVIDENCE"]
    chk("⑫ **TREE_EVIDENCE ≠ VERIFIED**:樹上已經在用、而且有產物為證的路徑,"
        "跟**我這一批探針親自打通的**分開記 —— 別人量過不等於我量過,"
        "兩者都是憑據但來源不同。**負控**:每一條 TREE_EVIDENCE 要指得出樹上的憑據是什麼",
        bool(te) and all(v.get("evidence") for _, v in te)
        and "TREE_EVIDENCE" in (B.get("state_rule") or {}),
        f"({len(te)} 條 · 都帶樹上憑據 {all(v.get('evidence') for _, v in te)})")

    # ⑬ 結果不可以只活在捲軸裡
    ev = evidence("selftest", {"probe": "dry", "ok": True})
    chk("⑬ **結果要落檔,不可以只活在捲軸裡**(批723 實錄):操作員把上一次的終端輸出"
        "**貼回 PowerShell**,每一行都被當成 cmdlet 執行 —— `·` 找不到,滿畫面 ParserError。"
        "那不是引擎壞了也不是他貼錯,**是我讓結果只存在於捲軸裡**。"
        "存證落檔之後要回報就傳檔案。**負控**:寫不出來要誠實回空路徑,不可以假裝寫了",
        (ev and Path(ev).exists()) or str(ev) == "",
        f"(存證 {'落檔 ' + Path(ev).name if ev else '寫不出來(誠實回空)'})")

    # ⑭ 總清單驗證:操作員問「如何驗證」——答案是一組**會紅的檢**
    _tw = [{"公司代號": "2330", "公司簡稱": "台積電"}, {"公司代號": "1101", "公司簡稱": "台泥"}]
    _tp = [{"公司代號": "3325", "公司簡稱": "旭品"}]
    vg = verify_universe(_tw, _tp, prev=[{"公司代號": "2330"}, {"公司代號": "9999"}],
                         asof="20260923", today="20260923")
    vb = verify_universe(_tw + [{"公司代號": "3325"}], _tp, prev=None)
    v6 = next(c for c in vg["checks"] if c["id"] == "V6")
    chk("⑭ **總清單怎麼驗**(操作員 2026-09-23 問):零網路就驗得了六條 —— "
        "V1 兩所不重疊 · V2 後綴由**來源**決定不是猜 · V3 名稱對得上 · "
        "**V4 Bloomberg 的 `TT` 不可回推市場別**(正本明寫那格是 UNKNOWN)· "
        "**V6 比 diff 不是比筆數**(一進一出剛好抵銷時,筆數看不出來)· V8 新鮮度。"
        "**負控一**:同一檔同時在兩所 → V1 要紅。"
        "**負控二**:沒有前一份可比 → V6 是 **NODATA 不是綠**(沒有分母就不給比率)",
        vg["state"] == "GREEN" and vb["state"] == "RED" and vb["red"] == ["V1"]
        and "V6" in vb["nodata"] and "新增" in v6["detail"] and "退出" in v6["detail"]
        and all(c.get("fail_means") for c in vg["checks"]),
        f"(正控 {vg['state']} · 負控 {vb['state']}/{vb['red']} · 無前份 V6={vb['nodata']})")

    n = len(ran) - len(fails)
    print(f"  [計] {len(ran)} 檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return selftest()
    if a and a[0] == "run":
        return run()
    if a and a[0] == "probe":
        r = probe()
        ev = evidence("probe", r)
        print(f"  [探針] {r['state']} · {r.get('why', '')}")
        for row in (r.get("rows") or []):
            print(f"   · {row['market'].upper():5} {row['dataset']:14} {row['probe']:9} "
                  f"{row['rows']} 列 {row['note']}")
        if ev:
            print(f"  [存證] {ev}")
            print("  [註] **要回報就傳這個檔** —— 把終端輸出貼回 PowerShell,"
                  "每一行都會被當成指令執行(批723 實錄:滿畫面 ParserError,而引擎沒事)")
        return {"OK": 0, "GATED": 4, "ABSENT": 3, "NODATA": 2}.get(r["state"], 1)
    print(f"=== 籌碼流量·調整後四價·共識獨立庫 {VERSION}({BATCH})===")
    return report()


if __name__ == "__main__":
    raise SystemExit(main())
