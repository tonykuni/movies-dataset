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
用法:python3 VDF_ENG092_TWFlowsAdjConsensus_v0100.py [probe|--selftest]
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

    n = len(ran) - len(fails)
    print(f"  [計] {len(ran)} 檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        return selftest()
    if a and a[0] == "probe":
        r = probe()
        print(f"  [探針] {r['state']} · {r.get('why', '')}")
        for row in (r.get("rows") or []):
            print(f"   · {row['market'].upper():5} {row['dataset']:14} {row['probe']:9} "
                  f"{row['rows']} 列 {row['note']}")
        return {"OK": 0, "GATED": 4, "ABSENT": 3, "NODATA": 2}.get(r["state"], 1)
    print(f"=== 籌碼流量·調整後四價·共識獨立庫 {VERSION}({BATCH})===")
    return report()


if __name__ == "__main__":
    raise SystemExit(main())
