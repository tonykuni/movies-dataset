#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flow_tw_monthly_revenue — 台股月營收整體+族群異常值引擎(批308)
====================================================================
操作員令(批308):「月營收分析整體全部分析族群一起分析異常值挑出來
成長過高因為低基期不算;透過 VDF 擷取資料也分為 TWSE/TPEX」。

方法論(明文,零發明):
  資料面:官方月營收彙總(上市 t187ap05_L+上櫃 mopsfin_t187ap05_O)
    ——市場標記由資料道決定(TWSE/TPEX 分道擷取);側車庫按
    (資料年月, 公司代號) 累積去重,單快照亦可析。
  低基期律(成長過高因低基期不算):
    基期強度 s = 去年當月營收 / (去年累計營收 ÷ 月序)
    —— s 衡量「去年同月相對去年平均月」之高低;s < θ_low ⇒ 該公司
    YoY 高成長標 LOW_BASE_EXCLUDED 不入異常榜(低基灌水誠實剔除);
    θ_low = 全體 s 之 P25(算出非設定;動態參數律);去年當月=0 ⇒ 必屬低基。
  異常值律(整體+族群一起):
    穩健 z = (YoY − 中位數) / (1.4826 × MAD) —— 營收成長右偏,
    均值/標準差易被極值拖動,取中位數/MAD 穩健制;
    |z| ≥ 3.0(估計超參數,非權重)⇒ 異常;整體榜+逐族群榜
    (族群樣本 < 8 誠實不出族群 z);族群=TW_Group_Classification 31 群。
  族群聚合:群 YoY = (Σ當月 − Σ去年當月) / Σ去年當月(加總制,免小司噪音)。
用法:
  --fetch      實連上市+上櫃月營收(同意閘)併側車庫
  --analyze    整體+族群分析(異常榜+低基剔除帳+族群聚合)
  --selftest   八檢(合成沙盒零網路)
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
import statistics
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CFG = ROOT / "config"
DB_PATH = ROOT / "data" / "input" / "tw_monthly_revenue_db.json"
OUT_PATH = ROOT / "data" / "output" / "tw_monthly_revenue_analysis.json"
GROUP_PATH = (sorted(CFG.glob("TW_Group_Classification_v*.json")) or [CFG / "TW_Group_Classification_v0110.json"])[-1]  # glob 最新版
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")

ENDPOINTS = {
    "TWSE": "https://openapi.twse.com.tw/v1/opendata/t187ap05_L",
    "TPEX": "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap05_O",
}
Z_GATE = 3.0     # 穩健 z 異常閘(估計超參數;非權重——榜單附 z 全可稽)
LOWBASE_PCT = 0.25  # θ_low=全體基期強度 P25(分位為估計超參數;θ 值算出)


def _f(x) -> float | None:
    try:
        return float(str(x).replace(",", ""))
    except (TypeError, ValueError):
        return None


def norm_row(r: dict, market: str) -> dict | None:
    """官方列 → 標準列;鍵缺=誠實 None。"""
    code = str(r.get("公司代號", "")).strip()
    ym = str(r.get("資料年月", "")).strip()
    if not code or not ym:
        return None
    return {"ym": ym, "code": code, "name": str(r.get("公司名稱", "")).strip(),
            "industry": str(r.get("產業別", "")).strip(), "market": market,
            "rev": _f(r.get("營業收入-當月營收")),
            "rev_prev": _f(r.get("營業收入-上月營收")),
            "rev_ly": _f(r.get("營業收入-去年當月營收")),
            "mom_pct": _f(r.get("營業收入-上月比較增減(%)")),
            "yoy_pct": _f(r.get("營業收入-去年同月增減(%)")),
            "cum": _f(r.get("累計營業收入-當月累計營收")),
            "cum_ly": _f(r.get("累計營業收入-去年累計營收"))}


def base_strength(row: dict) -> float | None:
    """基期強度 s=去年當月/(去年累計÷月序);去年當月 0 或缺=0(必屬低基)。"""
    ym = row.get("ym", "")
    try:
        month_no = int(ym[-2:])
    except ValueError:
        return None
    ly, cum_ly = row.get("rev_ly"), row.get("cum_ly")
    if not cum_ly or month_no < 1:
        return None  # 去年累計缺——s 不可算(誠實 None,不入低基判)
    if not ly:
        return 0.0
    return ly / (cum_ly / month_no)


def robust_z(vals: list[float]) -> tuple[float, float]:
    """(中位數, 1.4826×MAD);MAD=0 時退 1e-9 防除零。"""
    med = statistics.median(vals)
    mad = statistics.median(abs(v - med) for v in vals)
    return med, (1.4826 * mad) or 1e-9


def load_groups() -> dict[str, str]:
    """ticker → 族群名(31 群冊;缺件誠實空冊)。"""
    if not GROUP_PATH.exists():
        return {}
    g = json.loads(GROUP_PATH.read_text(encoding="utf-8"))
    out = {}
    for gname, members in g.get("groups", {}).items():
        for m in members:
            t = str(m.get("ticker", "")).strip()
            if t:
                out[t] = gname
    return out


def analyze(rows: list[dict], groups: dict[str, str]) -> dict:
    """整體+族群一起:低基剔除→穩健 z 異常榜→族群聚合。全數算出可稽。"""
    latest_ym = max((r["ym"] for r in rows), default="")
    cur = [r for r in rows if r["ym"] == latest_ym and r.get("yoy_pct") is not None]
    # ① 低基期律
    strengths = [(r, base_strength(r)) for r in cur]
    s_vals = sorted(s for _, s in strengths if s is not None)
    theta = s_vals[int(len(s_vals) * LOWBASE_PCT)] if len(s_vals) >= 8 else None
    included, low_base = [], []
    for r, s in strengths:
        r2 = dict(r, base_strength=(round(s, 3) if s is not None else None),
                  group=groups.get(r["code"]))
        if theta is not None and s is not None and s < theta and (r.get("yoy_pct") or 0) > 0:
            low_base.append(r2)  # 高成長且低基期——剔除帳(不入異常榜)
        else:
            included.append(r2)
    # ② 整體異常榜(穩健 z)
    yoys = [r["yoy_pct"] for r in included]
    anomalies, med = [], None
    if len(yoys) >= 8:
        med, scale = robust_z(yoys)
        for r in included:
            z = (r["yoy_pct"] - med) / scale
            if abs(z) >= Z_GATE:
                anomalies.append(dict(r, z=round(z, 2)))
        anomalies.sort(key=lambda r: -abs(r["z"]))
    # ③ 族群榜+族群聚合
    by_group: dict[str, list] = {}
    for r in included:
        if r.get("group"):
            by_group.setdefault(r["group"], []).append(r)
    group_stats, group_anoms = [], []
    for gname, mem in sorted(by_group.items()):
        s_rev = sum(r["rev"] or 0 for r in mem)
        s_ly = sum(r["rev_ly"] or 0 for r in mem)
        g_yoy = (s_rev - s_ly) / s_ly * 100 if s_ly else None
        st = {"group": gname, "n": len(mem),
              "group_yoy_pct": round(g_yoy, 2) if g_yoy is not None else None}
        if len(mem) >= 8:
            gm, gs = robust_z([r["yoy_pct"] for r in mem])
            for r in mem:
                z = (r["yoy_pct"] - gm) / gs
                if abs(z) >= Z_GATE:
                    group_anoms.append(dict(r, z=round(z, 2), scope=f"族群:{gname}"))
        else:
            st["note"] = "樣本<8 族群 z 誠實不出"
        group_stats.append(st)
    group_stats.sort(key=lambda s: -(s["group_yoy_pct"] if s["group_yoy_pct"] is not None else -1e9))
    n_mkt = {}
    for r in cur:
        n_mkt[r["market"]] = n_mkt.get(r["market"], 0) + 1
    return {"ym": latest_ym, "n_companies": len(cur), "by_market": n_mkt,
            "theta_low_dynamic": round(theta, 3) if theta is not None else None,
            "n_low_base_excluded": len(low_base),
            "low_base_ledger": sorted(low_base, key=lambda r: -(r["yoy_pct"] or 0))[:40],
            "market_median_yoy": round(med, 2) if med is not None else None,
            "anomalies_market": anomalies[:60], "anomalies_group": group_anoms[:60],
            "group_stats": group_stats,
            "rules": {"low_base": "s=去年當月/(去年累計÷月序);s<θ_low(P25 算出)且 YoY>0 ⇒ 剔除",
                      "anomaly": f"穩健 z=(YoY−中位)/(1.4826×MAD);|z|≥{Z_GATE} ⇒ 異常",
                      "group_agg": "群 YoY=(Σ當月−Σ去年當月)/Σ去年當月"}}


# ─────────────────────────── 命令 ───────────────────────────

def load_db() -> dict:
    if DB_PATH.exists():
        return json.loads(DB_PATH.read_text(encoding="utf-8"))
    return {"schema": "tw-monthly-revenue-db-v1", "rows": []}


def cmd_fetch() -> int:
    if VIA_ACCEL is None:
        print("  [SKIP] SuperAccel 未載——無網路道(誠實)")
        return 0
    db = load_db()
    seen = {(r["ym"], r["code"]) for r in db["rows"]}
    n_new = 0
    for market, url in ENDPOINTS.items():
        raw = VIA_ACCEL.fetch(url, timeout=90, cache=False)
        if not raw:
            print(f"  [SKIP] {market} 月營收未達(同意閘未開/限流;誠實缺席)")
            continue
        try:
            rows = json.loads(raw)
        except Exception as e:
            print(f"  [FAIL] {market} 解析:{e}")
            continue
        n = 0
        for r in rows:
            nr = norm_row(r, market)
            if nr and (nr["ym"], nr["code"]) not in seen:
                db["rows"].append(nr)
                seen.add((nr["ym"], nr["code"]))
                n += 1
        n_new += n
        print(f"  [OK] {market} 月營收 — 收 {len(rows)} 筆 · 新 {n}")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.write_text(json.dumps(db, ensure_ascii=False), encoding="utf-8")
    print(f"  [庫] +{n_new} · 共 {len(db['rows'])} 列(側車 {DB_PATH.name})")
    return 0


def cmd_analyze() -> int:
    db = load_db()
    if not db["rows"]:
        print("  [SKIP] 庫空——先 --fetch(誠實)")
        return 0
    res = analyze(db["rows"], load_groups())
    print(f"  ═ 月營收分析(資料年月 {res['ym']};{res['n_companies']} 家 · {res['by_market']})═")
    print(f"    低基期律:θ_low={res['theta_low_dynamic']}(P25 算出)· 剔除 {res['n_low_base_excluded']} 家")
    print(f"    整體:中位 YoY {res['market_median_yoy']}% · 異常 {len(res['anomalies_market'])} 家(|z|≥{Z_GATE})")
    for r in res["anomalies_market"][:8]:
        print(f"      {r['code']} {r['name'][:6]:<6} {r['market']} YoY {r['yoy_pct']:>9.1f}% z={r['z']:>6.1f}"
              f"{' 群:' + r['group'] if r.get('group') else ''}")
    print(f"    族群異常 {len(res['anomalies_group'])} 家;族群聚合前五:")
    for s in res["group_stats"][:5]:
        print(f"      {s['group']:<8} n={s['n']:<3} 群YoY {s['group_yoy_pct']}%")
    print(f"    低基剔除帳前五(高成長不入榜):")
    for r in res["low_base_ledger"][:5]:
        print(f"      {r['code']} {r['name'][:6]:<6} YoY {r['yoy_pct']:>9.1f}% 基期強度 {r['base_strength']}")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [出] {OUT_PATH.name}")
    return 0


def selftest() -> int:
    ok, total = 0, 8
    # ① 標準化(市場標記+數值化)
    r = norm_row({"資料年月": "11507", "公司代號": "1101", "公司名稱": "台泥",
                  "產業別": "水泥工業", "營業收入-當月營收": "13744103",
                  "營業收入-去年同月增減(%)": "1.53"}, "TWSE")
    if r and r["market"] == "TWSE" and r["rev"] == 13744103.0 and r["yoy_pct"] == 1.53:
        ok += 1; print("  [PASS] 官方列標準化+市場標記(TWSE/TPEX 分道)")
    else:
        print(f"  [FAIL] 標準化:{r}")
    # ② 基期強度式
    s = base_strength({"ym": "11507", "rev_ly": 50.0, "cum_ly": 700.0})
    if s == 0.5:  # 700/7=100 月均;50/100=0.5
        ok += 1; print("  [PASS] 基期強度 s=去年當月/(去年累計÷月序)")
    else:
        print(f"  [FAIL] 基期強度:{s}")
    # ③ 去年零營收=必屬低基;累計缺=誠實 None
    if base_strength({"ym": "11507", "rev_ly": 0, "cum_ly": 700.0}) == 0.0 and \
       base_strength({"ym": "11507", "rev_ly": 50.0, "cum_ly": None}) is None:
        ok += 1; print("  [PASS] 零基期=0+累計缺誠實 None")
    else:
        print("  [FAIL] 低基邊界")
    # 合成市場:30 家正常(YoY≈5%)+1 真異常(YoY 400%,基期正常)+1 低基灌水(YoY 900%,s 低)
    rows = []
    for i in range(30):
        rows.append({"ym": "11507", "code": f"N{i:03d}", "name": f"常{i}", "industry": "泛",
                     "market": "TWSE", "rev": 105.0, "rev_prev": 100.0, "rev_ly": 100.0,
                     "mom_pct": 5.0, "yoy_pct": 5.0 + (i % 5) * 0.1,
                     "cum": 735.0, "cum_ly": 700.0})
    rows.append({"ym": "11507", "code": "A001", "name": "真異", "industry": "泛",
                 "market": "TWSE", "rev": 500.0, "rev_prev": 480.0, "rev_ly": 100.0,
                 "mom_pct": 4.0, "yoy_pct": 400.0, "cum": 3500.0, "cum_ly": 700.0})
    rows.append({"ym": "11507", "code": "L001", "name": "低基", "industry": "泛",
                 "market": "TPEX", "rev": 100.0, "rev_prev": 90.0, "rev_ly": 10.0,
                 "mom_pct": 11.0, "yoy_pct": 900.0, "cum": 700.0, "cum_ly": 700.0})
    groups = {f"N{i:03d}": "泛族群" for i in range(30)}
    groups["A001"] = "泛族群"
    res = analyze(rows, groups)
    # ④ 低基剔除(900% 不入異常榜)
    anom_codes = {r["code"] for r in res["anomalies_market"]}
    if "L001" not in anom_codes and res["n_low_base_excluded"] == 1 and \
       res["low_base_ledger"][0]["code"] == "L001":
        ok += 1; print("  [PASS] 低基灌水剔除(YoY 900% 不入榜,入剔除帳)")
    else:
        print(f"  [FAIL] 低基剔除:{anom_codes}/{res['n_low_base_excluded']}")
    # ⑤ 真異常入榜(穩健 z)
    if "A001" in anom_codes and all(c.startswith("A") for c in anom_codes):
        ok += 1; print("  [PASS] 穩健 z 異常榜(真異常 400% 入榜;常態群不入)")
    else:
        print(f"  [FAIL] 異常榜:{anom_codes}")
    # ⑥ θ_low 動態算出
    if res["theta_low_dynamic"] is not None and 0 < res["theta_low_dynamic"] <= 1.1:
        ok += 1; print(f"  [PASS] θ_low 動態算出(P25={res['theta_low_dynamic']},非設定)")
    else:
        print(f"  [FAIL] θ_low:{res['theta_low_dynamic']}")
    # ⑦ 族群聚合(加總制)+族群異常
    gs = {s["group"]: s for s in res["group_stats"]}
    exp = (105.0 * 30 + 500 - (100.0 * 30 + 100)) / (100.0 * 30 + 100) * 100
    if abs(gs["泛族群"]["group_yoy_pct"] - round(exp, 2)) < 0.01 and \
       any(r["code"] == "A001" for r in res["anomalies_group"]):
        ok += 1; print("  [PASS] 族群聚合 YoY(加總制)+族群內異常一起挑")
    else:
        print(f"  [FAIL] 族群:{gs}")
    # ⑧ 市場分計(TWSE/TPEX)
    if res["by_market"] == {"TWSE": 31, "TPEX": 1}:
        ok += 1; print("  [PASS] TWSE/TPEX 分計(VDF 分道擷取對映)")
    else:
        print(f"  [FAIL] 市場分計:{res['by_market']}")
    print(f"  [計] {ok}/{total} 檢通過")
    return 0 if ok == total else 1


def main() -> int:
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if a[0] == "--selftest":
        return selftest()
    if a[0] == "--fetch":
        return cmd_fetch()
    if a[0] == "--analyze":
        return cmd_analyze()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
