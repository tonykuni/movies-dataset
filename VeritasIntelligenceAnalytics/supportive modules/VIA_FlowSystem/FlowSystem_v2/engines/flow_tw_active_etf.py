#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flow_tw_active_etf — 台灣主動式 ETF 清單+資金流引擎(TOOL-060)
====================================================================
操作員令(批21):台灣主動式 ETF 清單更新及相關數據擷取全自動;
三大法人買賣超含主動式台股 ETF 資金流進流出。

誠實界線(AI 只整理不發明):
  · 種子清單 SEED_KNOWN 標 as_of+verify_required=True——線上校驗
    (--refresh,官方 TWSE OpenAPI 名錄,非爬站)為準,種子僅起手。
  · 網路一律經 VIA_SuperAccel_Module.fetch → VIA_NET_CONSENT 同意閘;
    未同意=誠實 SKIP,絕不代設。
  · 資金流估算式全數列印可驗:申贖流 ≈ Δ在外單位數 × NAV。
  · 三大法人買賣超=輸入 JSON-rows(工作站擷取後餵入),引擎不捏數。

用法:
  --registry            清單 SSOT(種子+校驗態)
  --refresh             線上更新清單(同意閘;TWSE OpenAPI 名錄端點)
  --ingest <json>       餵數據(rows:date,ticker,nav,units_out,
                        foreign_net,invest_trust_net,dealer_net)
  --flows               資金流矩陣(方向+規模:%AUM+z)
  --selftest            六檢
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(路徑引導版;graceful 零行為變更) =====
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

import json
import math
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = HERE.parent / "config"
REG_PATH = CFG / "TW_Active_ETF_Registry_v0100.json"
DATA_PATH = CFG / "TW_Active_ETF_Data_v0100.json"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")

# 種子(as_of 2026-01 模型整理;verify_required——--refresh 官方名錄為準)
SEED_ETFS = [
    {"ticker": "00980A", "name": "主動統一台股增長", "issuer": "統一投信"},
    {"ticker": "00981A", "name": "主動群益台灣強棒", "issuer": "群益投信"},
    {"ticker": "00982A", "name": "主動野村臺灣優選", "issuer": "野村投信"},
]
# 官方端點名錄(非爬站;OpenAPI 開放資料;fetch 走同意閘)
ENDPOINTS = {
    "twse_etf_list": "https://openapi.twse.com.tw/v1/opendata/t187ap47_L",
    "twse_inst_net": "https://openapi.twse.com.tw/v1/fund/T86",
}


def load_registry() -> dict:
    if REG_PATH.exists():
        return json.loads(REG_PATH.read_text(encoding="utf-8"))
    return {"schema": "tw-active-etf-registry-v1", "as_of": "2026-01(種子)",
            "verify_required": True,
            "note": "種子=模型整理候校驗;--refresh 官方 OpenAPI 名錄為準(同意閘)",
            "etfs": [dict(e, status="SEED_KNOWN") for e in SEED_ETFS],
            "endpoints": ENDPOINTS, "history": []}


def save_registry(reg: dict):
    CFG.mkdir(parents=True, exist_ok=True)
    if REG_PATH.exists():
        bak = REG_PATH.with_suffix(f".pre_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak")
        bak.write_bytes(REG_PATH.read_bytes())
    REG_PATH.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_registry() -> int:
    reg = load_registry()
    save_registry(reg)
    print(f"  [清單] {len(reg['etfs'])} 檔 · as_of {reg['as_of']} · 校驗必要={reg['verify_required']}")
    for e in reg["etfs"]:
        print(f"    {e['ticker']} · {e['name']} · {e['issuer']} · {e.get('status','?')}")
    print("  [誠實] 種子候線上校驗;via-etfflow tw --refresh(需 VIA_NET_CONSENT=YES)為準")
    return 0


def cmd_refresh() -> int:
    reg = load_registry()
    if VIA_ACCEL is None:
        print("  [SKIP] SuperAccel 未載——無網路道;清單維持種子態(誠實)")
        return 0
    try:
        raw = VIA_ACCEL.fetch(ENDPOINTS["twse_etf_list"], timeout=30)
    except Exception as e:
        print(f"  [SKIP] 線上更新未成:{e}(同意閘未開或網路不可達;清單維持既有態,誠實)")
        return 0
    if not raw:  # fetch 同意閘拒絕/失敗時回 None 不拋例外
        print("  [SKIP] 線上更新未成:同意閘未開或無回應(清單維持既有態,誠實)")
        return 0
    try:
        rows = json.loads(raw if isinstance(raw, str) else raw.decode("utf-8"))
        n_new = 0
        known = {e["ticker"] for e in reg["etfs"]}
        for r in rows:
            code = str(r.get("證券代號", r.get("Code", ""))).strip()
            name = str(r.get("證券名稱", r.get("Name", ""))).strip()
            # 主動式台股 ETF:代號尾 A 且名稱含「主動」
            if code.endswith("A") and "主動" in name and code not in known:
                reg["etfs"].append({"ticker": code, "name": name, "issuer": "",
                                    "status": "VERIFIED_OPENAPI"})
                n_new += 1
        for e in reg["etfs"]:
            if e.get("status") == "SEED_KNOWN" and any(
                    str(r.get("證券代號", "")).strip() == e["ticker"] for r in rows):
                e["status"] = "VERIFIED_OPENAPI"
        reg["as_of"] = NOW
        reg["verify_required"] = any(e.get("status") == "SEED_KNOWN" for e in reg["etfs"])
        reg["history"].append({"op": "refresh", "ts": NOW, "new": n_new})
        save_registry(reg)
        print(f"  [更新] 官方名錄比對完成 · 新增 {n_new} · 總 {len(reg['etfs'])} 檔")
        return 0
    except Exception as e:
        print(f"  [FAIL] 名錄解析:{e}")
        return 2


def cmd_ingest(path: str) -> int:
    p = Path(path)
    if not p.exists():
        print(f"  [FAIL] 檔不存在:{path}")
        return 2
    rows = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(rows, dict):
        rows = rows.get("rows", [])
    db = json.loads(DATA_PATH.read_text(encoding="utf-8")) if DATA_PATH.exists() else {"rows": []}
    seen = {(r.get("date"), r.get("ticker")) for r in db["rows"]}
    n = 0
    for r in rows:
        k = (r.get("date"), r.get("ticker"))
        if k not in seen and r.get("date") and r.get("ticker"):
            db["rows"].append(r)
            seen.add(k)
            n += 1
    CFG.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [餵入] +{n} 列(去重後)· 庫 {len(db['rows'])} 列")
    return 0


def compute_flows(rows: list) -> list:
    """申贖流 ≈ Δunits_out × NAV;方向=正負;規模=%AUM+橫斷 z。"""
    by_t = {}
    for r in sorted(rows, key=lambda x: (x.get("ticker", ""), x.get("date", ""))):
        by_t.setdefault(r["ticker"], []).append(r)
    out = []
    for t, rs in by_t.items():
        if len(rs) < 2:
            out.append({"ticker": t, "flow": None, "note": "樣本<2 誠實不算"})
            continue
        a, b = rs[-2], rs[-1]
        nav = b.get("nav")
        du = (b.get("units_out") or 0) - (a.get("units_out") or 0)
        flow = du * nav if (nav is not None and a.get("units_out") is not None
                            and b.get("units_out") is not None) else None
        aum = (a.get("units_out") or 0) * (a.get("nav") or 0) or None
        inst = sum(b.get(k) or 0 for k in ("foreign_net", "invest_trust_net", "dealer_net"))
        out.append({"ticker": t, "date": b.get("date"), "flow": flow,
                    "flow_pct_aum": (round(flow / aum * 100, 3) if flow is not None and aum else None),
                    "inst_net_3": inst if any(b.get(k) is not None for k in
                                              ("foreign_net", "invest_trust_net", "dealer_net")) else None,
                    "direction": ("流入" if flow > 0 else "流出" if flow < 0 else "持平")
                    if flow is not None else "—"})
    vals = [o["flow_pct_aum"] for o in out if o.get("flow_pct_aum") is not None]
    if len(vals) >= 2:
        m = sum(vals) / len(vals)
        sd = math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals)) or 1e-9
        for o in out:
            if o.get("flow_pct_aum") is not None:
                o["z"] = round((o["flow_pct_aum"] - m) / sd, 2)
    return out


def cmd_flows() -> int:
    if not DATA_PATH.exists():
        print("  [SKIP] 尚無數據——先 --ingest(工作站擷取餵入;誠實不捏數)")
        return 0
    db = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    res = compute_flows(db["rows"])
    print(f"  [資金流] {len(res)} 檔(式:申贖流≈Δ在外單位×NAV;規模=%AUM+z)")
    for o in res:
        if o.get("flow") is not None:
            print(f"    {o['ticker']} {o['date']} · {o['direction']} {o['flow']:,.0f}"
                  f" · {o['flow_pct_aum']}%AUM · z={o.get('z','—')} · 三大法人合計 {o.get('inst_net_3','—')}")
        else:
            print(f"    {o['ticker']} · {o.get('note','—')}")
    return 0


def selftest() -> int:
    ok, total = 0, 6
    reg = load_registry()
    if len(reg["etfs"]) >= 3 and all(e.get("status") for e in reg["etfs"]):
        ok += 1; print("  [PASS] 清單 SSOT(種子態+校驗旗標誠實)")
    else:
        print("  [FAIL] 清單")
    if reg["verify_required"] and "OpenAPI" in reg["note"]:
        ok += 1; print("  [PASS] 誠實旗標:種子候校驗+官方名錄端點(非爬站)")
    else:
        print("  [FAIL] 旗標")
    fix = [  # 測試合成數據(僅 selftest 用,不落庫)
        {"date": "D1", "ticker": "00980A", "nav": 10.0, "units_out": 1000,
         "foreign_net": 5, "invest_trust_net": 3, "dealer_net": -1},
        {"date": "D2", "ticker": "00980A", "nav": 10.2, "units_out": 1100,
         "foreign_net": 8, "invest_trust_net": 2, "dealer_net": 0},
        {"date": "D1", "ticker": "00981A", "nav": 20.0, "units_out": 500},
        {"date": "D2", "ticker": "00981A", "nav": 19.8, "units_out": 450},
    ]
    res = {o["ticker"]: o for o in compute_flows(fix)}
    if res["00980A"]["direction"] == "流入" and abs(res["00980A"]["flow"] - 100 * 10.2) < 1e-6:
        ok += 1; print("  [PASS] 申贖流公式(Δ單位×NAV)+方向判定")
    else:
        print("  [FAIL] 流公式")
    if res["00981A"]["direction"] == "流出" and res["00981A"]["flow_pct_aum"] is not None:
        ok += 1; print("  [PASS] 流出向+%AUM 規模")
    else:
        print("  [FAIL] 規模")
    if res["00980A"]["inst_net_3"] == 10 and res["00981A"]["inst_net_3"] is None:
        ok += 1; print("  [PASS] 三大法人合計(缺值誠實 None)")
    else:
        print("  [FAIL] 法人")
    one = compute_flows([{"date": "D1", "ticker": "X", "nav": 1, "units_out": 1}])
    if one[0]["flow"] is None and "誠實" in one[0]["note"]:
        ok += 1; print("  [PASS] 樣本不足誠實不算")
    else:
        print("  [FAIL] 樣本閘")
    print(f"  [計] {ok}/{total} 檢通過")
    return 0 if ok == total else 1


def main() -> int:
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if a[0] == "--selftest":
        return selftest()
    if a[0] == "--registry":
        return cmd_registry()
    if a[0] == "--refresh":
        return cmd_refresh()
    if a[0] == "--ingest" and len(a) > 1:
        return cmd_ingest(a[1])
    if a[0] == "--flows":
        return cmd_flows()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
