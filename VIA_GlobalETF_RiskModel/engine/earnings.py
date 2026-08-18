# -*- coding: utf-8 -*-
"""
earnings.py — M35_ForwardEarnings：隱含共識 EPS 結轉 + 估值 + 惡魔驗證
=============================================================================
MODULE M35_ForwardEarnings
  [MCFL-M35-C35-F350] build_earnings_ledger — Implied Consensus Forward EPS

規則（SSOT 定案，對應 2026-08 討論串「發布 Forward P/E 當日倒算 EPS」）：
  1. 發布日：Implied_EPS = Published_Index_Level / Published_Forward_PE
  2. 下次更新前：Carry_Forward_EPS 凍結不動（EPS 不得每日跟價格重算）
  3. 每日重算的是估值：Daily_Repriced_PE = PE_pub × (Proxy今價/Proxy發布日價)
  4. 倒算值一律 evidence=Der / status=Calculated_NotOriginal，不得標 Original
  5. staleness 分級 Fresh/Usable/StaleWarning/NeedsRefresh/Reject
  6. ERP = EarningsYield − Local10Y；USD_Adj_ERP 再扣 FX 貶值風險與美元資金壓力
狀態機：SOURCE_PUBLISHED → IMPLIED_EPS_CALCULATED → CARRY_FORWARD_ACTIVE
        → DAILY_REPRICED_VALUATION → STALE_WARNING → SOURCE_REFRESHED(append-only)
"""
from __future__ import annotations

import datetime as _dt


def _staleness_state(days, cfg):
    if days <= cfg["fresh"]:
        return "FRESH", "good"
    if days <= cfg["usable"]:
        return "USABLE", "good"
    if days <= cfg["stale_warning"]:
        return "STALE_WARNING", "warning"
    if days <= cfg["needs_refresh"]:
        return "NEEDS_REFRESH", "serious"
    return "REJECT_FOR_CURRENT_VALUATION", "critical"


def _price_on_or_before(dates, prices, target):
    """回傳 target（ISO 日期字串）當日或之前最近的收盤價。"""
    best = None
    for d, p in zip(dates, prices):
        if d <= target and p:
            best = p
        elif d > target:
            break
    return best


def build_earnings_ledger(market, config, fundamentals, snapshots, usd_stress_risk):
    """[MCFL-M35-C35-F350]
    snapshots: data/demo_forward_pe.json 的 list（或使用者換上的真實來源檔）。"""
    ecfg = config["def_earnings"]
    carry_cfg = ecfg["carry_forward_days"]
    proxy_map = ecfg["index_proxy_map"]
    country_map = ecfg["index_country_map"]
    tol = float(ecfg.get("rounding_mismatch_tolerance", 0.0005))
    funding_pp = float(ecfg.get("usd_funding_stress_pp_at_100", 1.0))
    asof = _dt.date.fromisoformat(market.asof)

    rows = []
    by_index = {}
    for snap in snapshots:
        idx = snap["index_name"]
        pub_date = snap["source_publish_date"]
        level = float(snap["index_level_used"])
        fpe = float(snap["published_forward_pe"])
        devil = []

        implied_eps = level / fpe if fpe > 0 else None
        if implied_eps is None:
            devil.append({"flag": "invalid_forward_pe", "detail": "P/E <= 0"})

        # 惡魔：發布方同時給了 EPS → 檢查倒算差（rounding 偵測）
        pub_eps = snap.get("published_forward_eps")
        if implied_eps and pub_eps:
            diff = abs(implied_eps - float(pub_eps)) / float(pub_eps)
            if diff > tol:
                devil.append({"flag": "forward_pe_rounding",
                              "detail": "倒算EPS %.2f vs 發布EPS %.2f（差 %.3f%%）——"
                                        "P/E 四捨五入造成，倒算值僅可當 proxy"
                                        % (implied_eps, float(pub_eps), diff * 100)})

        # staleness / carry-forward 狀態
        stale_days = (asof - _dt.date.fromisoformat(pub_date)).days
        if stale_days < 0:
            # 未來日期不是「新鮮」，是資料錯誤：來源日期打錯或時區/格式問題
            stale_state, stale_status = "FUTURE_DATED", "critical"
            machine_state = "NEEDS_SOURCE_REVIEW"
            devil.append({"flag": "publish_date_in_future",
                          "detail": "發布日 %s 晚於 asof %s（%d 天）——日期錯置，"
                                    "本列不得用於當前估值" % (pub_date, market.asof,
                                                              -stale_days)})
        else:
            stale_state, stale_status = _staleness_state(stale_days, carry_cfg)
            machine_state = ("CARRY_FORWARD_ACTIVE"
                             if stale_state in ("FRESH", "USABLE")
                             else "STALE_WARNING" if stale_state == "STALE_WARNING"
                             else "NEEDS_SOURCE_REFRESH")

        # 每日重算估值：用 proxy ETF 總報酬比推指數位移（標 Der + devil 註記）
        proxy = proxy_map.get(idx)
        repriced_pe = ey = erp = usd_adj_erp = ratio = None
        if proxy and market.prices.get(proxy):
            p_pub = _price_on_or_before(market.dates, market.prices[proxy], pub_date)
            p_now = market.prices[proxy][-1]
            if p_pub and p_now:
                ratio = p_now / p_pub
                repriced_pe = fpe * ratio
                ey = 100.0 / repriced_pe
                if ratio > 1.08:
                    devil.append({"flag": "valuation_expansion_warning",
                                  "detail": "發布日以來 proxy +%.1f%% 而 EPS 凍結"
                                            "→ 估值快速變貴" % ((ratio - 1) * 100)})
                if ratio < 0.92:
                    devil.append({"flag": "valuation_compression",
                                  "detail": "發布日以來 proxy %.1f%%，重算 P/E 已回落"
                                            % ((ratio - 1) * 100)})
            else:
                devil.append({"flag": "proxy_price_gap",
                              "detail": "proxy %s 無發布日價格，無法重算" % proxy})
            devil.append({"flag": "proxy_repricing",
                          "detail": "以 %s 總報酬比近似指數位移（非官方指數）" % proxy})
        else:
            devil.append({"flag": "no_proxy", "detail": "無 proxy ETF，僅保留發布值"})

        country = country_map.get(idx)
        fnd = fundamentals.get(country, {}) if country else {}
        local_10y = fnd.get("local_10y")
        fx_dep = fnd.get("fx_dep_risk_pp", 0.0)
        if ey is not None and local_10y is not None:
            erp = ey - local_10y
            usd_adj_erp = erp - fx_dep - (usd_stress_risk or 0.0) / 100.0 * funding_pp

        if snap.get("forward_horizon") not in ("NTM", "FY1", "FY2"):
            devil.append({"flag": "horizon_unknown",
                          "detail": "forward_horizon 未標 NTM/FY1/FY2"})
        if snap.get("index_type") not in ("price", "total_return"):
            devil.append({"flag": "index_type_unknown",
                          "detail": "未標 price / total_return index"})

        row = {
            "index_name": idx, "region": snap.get("region"),
            "source_name": snap.get("source_name"),
            "source_publish_date": pub_date, "asof_date": market.asof,
            "index_level_used": level, "published_forward_pe": fpe,
            "implied_forward_eps": None if implied_eps is None else round(implied_eps, 2),
            "eps_status": "Calculated_NotOriginal",
            "carry_forward_state": machine_state,
            "stale_days": stale_days,
            "staleness": {"state": stale_state, "status": stale_status},
            "proxy_etf": proxy,
            "proxy_ratio_since_publish": None if ratio is None else round(ratio, 4),
            "daily_repriced_pe": None if repriced_pe is None else round(repriced_pe, 2),
            "earnings_yield_pct": None if ey is None else round(ey, 3),
            "local_10y": local_10y,
            "erp_pp": None if erp is None else round(erp, 3),
            "usd_adj_erp_pp": None if usd_adj_erp is None else round(usd_adj_erp, 3),
            "forward_horizon": snap.get("forward_horizon", "?"),
            "index_type": snap.get("index_type", "?"),
            "evidence": "Der", "truth_tier": "T3",
            "devil_warnings": devil,
        }
        rows.append(row)
        prev = by_index.get(idx)
        if prev is None or pub_date > prev["source_publish_date"]:
            by_index[idx] = row

    # 同指數多來源 → 分歧檢查（source divergence）
    seen = {}
    for r in rows:
        seen.setdefault(r["index_name"], []).append(r)
    for idx, group in seen.items():
        if len(group) >= 2:
            pes = [g["published_forward_pe"] for g in group]
            spread = (max(pes) - min(pes)) / min(pes)
            if spread > 0.05:
                for g in group:
                    g["devil_warnings"].append(
                        {"flag": "source_divergence",
                         "detail": "%s 多來源 forward P/E 差 %.1f%%" % (idx, spread * 100)})

    return {
        "mcfl": config["def_earnings"].get("mcfl", ""),
        "rows": rows,
        "active": list(by_index.values()),
        "rules": {
            "carry_forward_days": carry_cfg,
            "eps_daily_mutation": "禁止（EPS 凍結，每日只重算估值）",
            "labeling": "倒算值=Calculated_NotOriginal，不得標 Original",
        },
    }
