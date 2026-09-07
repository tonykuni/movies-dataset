#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch310_stress_core — APCE 壓力測試砲台(批310;魔鬼代言人波)
====================================================================
操作員令:「keep testing」。對批309 APCE 於真實面板(145 檔 × 165 日)做
對抗式與統計效度測試——稿中提及但未執行者全數落地:
  T1  全引擎迴歸(子行程跑各 selftest)
  T2  面板資料完整性(PROXY 成交值 vs 官方值比、缺日稽核、還原價一致)
  T3  IC 檢定:各因子 vs 前瞻 5/20 日報酬(逐日橫截面 Spearman;t 值;勝率)
  T4  角色前瞻報酬(LEADER/PEER/LAGGER/UNRELATED/FAKE_PULL/WASHOUT)
  T5  周轉率:角色日變動率;遲滯前後 valid 翻轉率(降幅)
  T6  前視偏誤量化:T-1 vs T0 權重之聚焦指數差
  T7  倖存者偏差量化:鏈結法(在籍至退出)vs 回填法(剔除全史)
  T8  封頂統計:cap 綁定日占比、不可行族群(n×cap<1)數
  T9  PC1 穩定性:40/60/90 窗排序 Spearman、資格翻轉
  T10 高原測試:corr_q / quant_window / ewm_span 單軸掃描 → 角色一致率
  T11 閹割測試:拔量能同動 / 背離 / RS 條件 → 角色變動率
  T12 置換檢定+FDR:族群 att 指數 vs Δclean_mkt% CCF ±5、B=200、BH q=0.10
  T13 小公雞謬誤量化:vol_shock Top10 vs gravity Top10 之 Small 占比
  T14 參數家族實值校準(真實歷史餵 C-05/C-06;鎖觸狀態評估)
判定:PASS/WARN/FAIL/INFO/SKIP(統計結果為 INFO 誠實列數,不美化)。
輸出:Batch310_StressTest_Results.json
"""
from __future__ import annotations

import importlib.util
import json
import math
import random
import statistics
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
FS = VIA / "supportive modules" / "VIA_FlowSystem" / "FlowSystem_v2"
ENG = FS / "engines"
PANEL = FS / "data" / "input" / "tw_apce_panel.json"
OUT = HERE / "Batch310_StressTest_Results.json"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
TSMC = "2330"
RESULTS: list[dict] = []
STATS: dict = {}


def check(cid, name, status, detail, **kw):
    RESULTS.append({"id": cid, "name": name, "status": status, "detail": detail, **kw})
    print(f"  [{status}] {cid} {name} — {detail[:150]}")


def load_mod(name: str, fname: str):
    spec = importlib.util.spec_from_file_location(name, ENG / fname)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def pearson(x, y):
    n = len(x)
    if n < 3:
        return None
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((v - mx) ** 2 for v in x)) or 1e-12
    sy = math.sqrt(sum((v - my) ** 2 for v in y)) or 1e-12
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def ranks(vals):
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    r = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2.0
        i = j + 1
    return r


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def tstat(vals):
    n = len(vals)
    if n < 3:
        return None
    m = statistics.mean(vals)
    sd = statistics.pstdev(vals) or 1e-12
    return m / (sd / math.sqrt(n))


# ─────────────────────────── T1 迴歸 ───────────────────────────

def t1_regression():
    print("\n═══ T1 全引擎迴歸 ═══")
    tests = [
        ("FLOW_ENG020_FlowLeadlag.py", ENG), ("FLOW_ENG023_FlowTwActiveEtf.py", ENG),
        ("FLOW_ENG025_FlowUsMacroOpenData.py", ENG), ("FLOW_ENG026_FlowTwBaseline.py", ENG),
        ("FLOW_ENG027_FlowTwMonthlyRevenue.py", ENG), ("FLOW_ENG028_FlowParamFamily.py", ENG),
        ("FLOW_ENG029_FlowApce.py", ENG), ("FLOW_ENG030_FlowTwPanel.py", ENG),
        ("SUP_MDL737_SuperAccelModule_v0104.py", VIA / "supportive modules"),
    ]
    rows, n_ok = [], 0
    for f, d in tests:
        r = subprocess.run([sys.executable, str(d / f), "--selftest"], capture_output=True, text=True,
                           timeout=600, cwd=str(d))
        last = [ln for ln in r.stdout.splitlines() if "[計]" in ln]
        ok = r.returncode == 0
        n_ok += ok
        rows.append({"engine": f, "rc": r.returncode, "tally": last[-1].strip() if last else r.stdout[-120:]})
    STATS["regression"] = rows
    check("T1", "全引擎 selftest 迴歸", "PASS" if n_ok == len(tests) else "FAIL",
          f"{n_ok}/{len(tests)} 引擎自檢全過;" + "; ".join(f"{r['engine'].split('_')[1]}:{r['tally'].split('·')[0].strip()}" for r in rows))


# ─────────────────────────── T2 面板完整性 ───────────────────────────

def t2_panel(rows):
    print("\n═══ T2 面板資料完整性 ═══")
    by_t = {}
    for r in rows:
        by_t.setdefault(r["ticker"], []).append(r)
    dates = sorted({r["date"] for r in rows})
    # 缺日稽核
    miss = {t: 1 - len(rs) / len(dates) for t, rs in by_t.items()}
    bad = {t: round(v, 3) for t, v in miss.items() if v > 0.05}
    check("T2a", "成員缺日稽核(>5% 缺列標)", "PASS" if not bad else "WARN",
          f"{len(by_t)} 檔 × {len(dates)} 日;缺日>5%:{len(bad)} 檔 {dict(list(bad.items())[:5])}")
    # PROXY vs OFFICIAL 比:官方成交值列同時保有 volume×close
    ratios = []
    for r in rows:
        if r.get("turnover_basis") == "OFFICIAL" and r.get("volume") and r.get("close") and r.get("turnover"):
            ratios.append(r["turnover"] / (r["volume"] * r["close"]))
    if len(ratios) >= 20:
        med = statistics.median(ratios)
        q1, q3 = sorted(ratios)[len(ratios) // 4], sorted(ratios)[3 * len(ratios) // 4]
        out = sum(1 for x in ratios if abs(x - 1) > 0.2)
        STATS["proxy_ratio"] = {"n": len(ratios), "median": round(med, 4), "q1": round(q1, 4), "q3": round(q3, 4), "n_out20": out}
        check("T2b", "PROXY(量×收盤)vs 官方成交值比", "PASS" if abs(med - 1) < 0.05 and out / len(ratios) < 0.1 else "WARN",
              f"n={len(ratios)} 中位 {med:.4f} IQR [{q1:.4f},{q3:.4f}] 偏離>20%:{out}({out / len(ratios):.1%})——代理誤差量化")
    else:
        check("T2b", "PROXY vs 官方成交值比", "SKIP", "官方重疊列不足")
    # 還原價 vs 收盤(近 20 日應一致,除息除權外)
    diff = [abs(r["adj_close"] / r["close"] - 1) for r in rows if r.get("adj_close") and r.get("close") and r["date"] >= dates[-20]]
    n_adj = sum(1 for d in diff if d > 1e-6)
    check("T2c", "近 20 日還原收盤=收盤(除權息外)", "PASS" if n_adj / max(1, len(diff)) < 0.05 else "WARN",
          f"{n_adj}/{len(diff)} 列有還原差(={n_adj / max(1, len(diff)):.1%};除權息期屬常態)")
    # 極端報酬稽核(|ret|>50% 單日=資料錯誤嫌疑)
    ext = []
    for t, rs in by_t.items():
        rs = sorted(rs, key=lambda r: r["date"])
        for a, b in zip(rs, rs[1:]):
            if a.get("adj_close") and b.get("adj_close"):
                ch = b["adj_close"] / a["adj_close"] - 1
                if abs(ch) > 0.5:
                    ext.append((t, b["date"], round(ch, 3)))
    check("T2d", "單日極端報酬(|r|>50%)稽核", "PASS" if not ext else "WARN",
          "零極端" if not ext else f"{len(ext)} 筆:{ext[:4]}(減資/資料錯誤候查)")


# ─────────────────────────── T3/T4 IC 與角色前瞻 ───────────────────────────

def fwd_returns(S, k):
    out = {}
    for t, s in S.items():
        idx = s["idx_stock"]
        out[t] = [idx[i + k] / idx[i] - 1 if (i + k < len(idx) and idx[i] and idx[i + k]) else None for i in range(len(idx))]
    return out


def t3_ic(eng):
    print("\n═══ T3 IC 檢定(橫截面 Spearman vs 前瞻報酬)═══")
    S, dates, di = eng.S, eng.dates, eng.di
    f5, f20 = fwd_returns(S, 5), fwd_returns(S, 20)
    feats = ["leader_score", "adaptive_score", "gravity_shock", "rs_mom", "cs_z", "price_rs", "vol_corr", "price_corr", "as", "vol_shock"]
    table = []
    for feat in feats:
        for horizon, fwd in (("5d", f5), ("20d", f20)):
            ics = []
            for k, d in enumerate(dates):
                if k < 60 or k > len(dates) - (6 if horizon == "5d" else 21):
                    continue
                xs, ys = [], []
                for t, i in di[d].items():
                    s = S[t]
                    if s["is_tsmc"] or feat not in s:
                        continue
                    v, y = s[feat][i], fwd[t][i]
                    if v is not None and y is not None:
                        xs.append(v)
                        ys.append(y)
                if len(xs) >= 30:
                    ic = spearman(xs, ys)
                    if ic is not None:
                        ics.append(ic)
            if len(ics) >= 10:
                m, t = statistics.mean(ics), tstat(ics)
                hit = sum(1 for v in ics if v > 0) / len(ics)
                table.append({"feature": feat, "horizon": horizon, "n_days": len(ics), "mean_ic": round(m, 4),
                              "t": round(t, 2), "hit": round(hit, 3)})
    STATS["ic"] = table
    sig = [r for r in table if abs(r["t"]) >= 2.0]
    neg = [r for r in table if r["feature"] == "leader_score" and r["mean_ic"] < 0]
    top = sorted(table, key=lambda r: -abs(r["t"]))[:4]
    check("T3", "因子 IC(逐日 Spearman;|t|≥2 顯著)", "INFO" if not neg else "WARN",
          f"{len(table)} 組;顯著 {len(sig)};最強:" + "; ".join(f"{r['feature']}@{r['horizon']} IC={r['mean_ic']:+.3f} t={r['t']:+.1f} 勝率 {r['hit']:.0%}" for r in top)
          + (";leader_score 為負 IC(誠實)" if neg else ""))


def t4_roles(eng):
    print("\n═══ T4 角色前瞻報酬 ═══")
    S, dates, di = eng.S, eng.dates, eng.di
    f5, f20 = fwd_returns(S, 5), fwd_returns(S, 20)
    buckets = {}
    for k, d in enumerate(dates):
        if k < 60 or k > len(dates) - 21:
            continue
        for t, i in di[d].items():
            s = S[t]
            if s["is_tsmc"] or "role" not in s:
                continue
            role = s["role"][i]
            if role and f5[t][i] is not None and f20[t][i] is not None:
                b = buckets.setdefault(role, {"f5": [], "f20": []})
                b["f5"].append(f5[t][i])
                b["f20"].append(f20[t][i])
    table = []
    for role, b in buckets.items():
        table.append({"role": role, "n": len(b["f5"]), "fwd5_mean": round(statistics.mean(b["f5"]) * 100, 3),
                      "fwd20_mean": round(statistics.mean(b["f20"]) * 100, 3), "t5": round(tstat(b["f5"]) or 0, 2),
                      "t20": round(tstat(b["f20"]) or 0, 2)})
    table.sort(key=lambda r: -r["fwd20_mean"])
    STATS["role_fwd"] = table
    L = next((r for r in table if r["role"] == "LEADER"), None)
    G = next((r for r in table if r["role"] == "LAGGER"), None)
    spread = (L["fwd20_mean"] - G["fwd20_mean"]) if (L and G) else None
    check("T4", "角色前瞻報酬(fwd5/fwd20 均,%;重疊樣本 t 值僅供參)", "INFO",
          "; ".join(f"{r['role']} n={r['n']} f5={r['fwd5_mean']:+.2f}% f20={r['fwd20_mean']:+.2f}%" for r in table)
          + (f";LEADER−LAGGER 20 日價差 {spread:+.2f}%" if spread is not None else ""))


# ─────────────────────────── T5 周轉率 ───────────────────────────

def t5_turnover(eng):
    print("\n═══ T5 周轉率與遲滯 ═══")
    S, dates, di = eng.S, eng.dates, eng.di
    chg, tot = 0, 0
    raw_flip = mem_flip = raw_n = 0
    for t, s in S.items():
        if s["is_tsmc"] or "role" not in s:
            continue
        roles = s["role"]
        for i in range(61, len(roles)):
            if roles[i] and roles[i - 1]:
                tot += 1
                chg += roles[i] != roles[i - 1]
        vr, vm = s["valid_raw"], s["valid_member"]
        for i in range(61, len(vr)):
            if vr[i] is not None and vr[i - 1] is not None:
                raw_n += 1
                raw_flip += vr[i] != vr[i - 1]
                if vm[i] is not None and vm[i - 1] is not None:
                    mem_flip += vm[i] != vm[i - 1]
    rate = chg / tot if tot else None
    rf, mf = (raw_flip / raw_n if raw_n else None), (mem_flip / raw_n if raw_n else None)
    STATS["turnover"] = {"role_change_rate": rate, "valid_raw_flip": rf, "valid_member_flip": mf}
    red = (1 - mf / rf) if (rf and mf is not None) else None
    check("T5", "角色日變動率+遲滯翻轉降幅", "PASS" if (red is not None and red > 0.3) else "WARN",
          f"角色日變動率 {rate:.1%};valid 翻轉率 遲滯前 {rf:.2%} → 遲滯後 {mf:.2%}(降 {red:.0%})" if rate is not None else "樣本不足")


# ─────────────────────────── T6/T7 前視與倖存 ───────────────────────────

def chain(eng, sec, use_t0=False, exclude=None, exclude_from=None, w_key="att"):
    """重建鏈結指數:use_t0=用當日權重(前視);exclude/exclude_from=模擬退出。"""
    S, dates, di, W = eng.S, eng.dates, eng.di, eng.weights
    lvl, prev = 100.0, None
    path = {}
    for d in dates:
        wd = W.get((sec, d if use_t0 else (prev or d)))
        if prev is not None and wd:
            mem = [t for t in wd if t in di[d] and S[t]["ret"][di[d][t]] is not None
                   and not (t == exclude and (exclude_from is None or d >= exclude_from))]
            if mem:
                sw = sum(wd[t][w_key] for t in mem)
                g = sum(wd[t][w_key] * S[t]["ret"][di[d][t]] for t in mem) / sw if sw > 0 else 0.0
                lvl *= (1 + g)
        if (sec, d) in W:
            prev = d
        path[d] = lvl
    return path


def t6_lookahead(eng):
    print("\n═══ T6 前視偏誤量化(T-1 vs T0 權重)═══")
    diffs = []
    for sec, hh in eng.health.items():
        if hh["n_members"] < 6:
            continue
        p1, p0 = chain(eng, sec, use_t0=False), chain(eng, sec, use_t0=True)
        dl = eng.dates[-1]
        diffs.append((sec, p1[dl], p0[dl], p0[dl] / p1[dl] - 1))
    STATS["lookahead"] = [{"sector": s, "t1": round(a, 2), "t0": round(b, 2), "bias": round(c, 4)} for s, a, b, c in diffs]
    if diffs:
        mean_bias = statistics.mean(c for _, _, _, c in diffs)
        worst = max(diffs, key=lambda x: abs(x[3]))
        check("T6", "T0 當日權重相對 T-1 之終值偏誤", "PASS" if mean_bias > 0 else "INFO",
              f"{len(diffs)} 群(n≥6)平均偏誤 {mean_bias:+.2%}(T0 高估=前視獎勵);最大 {worst[0]} {worst[3]:+.2%}")
    else:
        check("T6", "前視偏誤", "SKIP", "無 n≥6 族群")


def t7_survivorship(eng):
    print("\n═══ T7 倖存者偏差量化(鏈結在籍法 vs 回填剔除法)═══")
    rows = []
    mid = eng.dates[len(eng.dates) // 2]
    for sec, hh in eng.health.items():
        if hh["n_members"] < 6:
            continue
        mem = [t for t in eng.S if eng.S[t]["sector"] == sec and not eng.S[t]["is_tsmc"]]
        worst = min(mem, key=lambda t: eng.S[t]["idx_stock"][-1])
        p_chain = chain(eng, sec, exclude=worst, exclude_from=mid)   # 在籍至中途退出
        p_back = chain(eng, sec, exclude=worst, exclude_from=None)   # 回填:全史剔除(倖存者)
        dl = eng.dates[-1]
        rows.append({"sector": sec, "removed": worst, "chain": round(p_chain[dl], 2), "backfill": round(p_back[dl], 2),
                     "bias": round(p_back[dl] / p_chain[dl] - 1, 4)})
    STATS["survivorship"] = rows
    if rows:
        mb = statistics.mean(r["bias"] for r in rows)
        check("T7", "回填法相對鏈結法之終值高估(最弱成員中途退出情境)", "PASS" if mb >= 0 else "INFO",
              f"{len(rows)} 群 平均高估 {mb:+.2%};最大 {max(rows, key=lambda r: r['bias'])['sector']} "
              f"{max(r['bias'] for r in rows):+.2%}——倖存者偏差=鏈結法所除")
    else:
        check("T7", "倖存者偏差", "SKIP", "無 n≥6 族群")


# ─────────────────────────── T8 封頂 ───────────────────────────

def t8_cap(eng, cap=0.18):
    print("\n═══ T8 封頂統計 ═══")
    bind = tot = 0
    infeasible = []
    for sec, idx in eng.indices.items():
        n = eng.health[sec]["n_members"]
        if n * cap < 1.0:
            infeasible.append((sec, n))
            continue  # 不可行群=等權退場,不計綁定(批310 修正:原統計誤計為 100%)
        for d, v in idx.items():
            if d.startswith("_") or v.get("max_w_att") is None:
                continue
            tot += 1
            bind += v["max_w_att"] >= cap - 1e-9
    STATS["cap"] = {"bind_share": bind / tot if tot else None, "infeasible": infeasible, "n_feasible": len(eng.indices) - len(infeasible)}
    check("T8", "聚焦權重封頂綁定率(可行群)+不可行族群(n×0.18<1 ⇒ 等權退場)", "WARN" if infeasible else "PASS",
          (f"可行 {len(eng.indices) - len(infeasible)} 群綁定日占比 {bind / tot:.1%};" if tot else "可行群無資料;")
          + f"不可行 {len(infeasible)}/{len(eng.indices)} 群(att 指數退化=等權):{[s for s, _ in infeasible][:8]}…")


def t8b_cap_relax(apce, rows, eng):
    """實驗:小族群封頂放寬律 cap_eff=max(C-17, 1.2/n)(預設關;憲法不動)——量化聚焦資訊回復。"""
    print("\n═══ T8b 小族群封頂放寬實驗(cap_eff=max(0.18, 1.2/n))═══")
    e = apce.APCE({"cap_relax": True}); e.resolve_params(); e.run(rows, base_date="2026-01-01")
    dl = eng.dates[-1]
    diffs = []
    for sec, n in STATS["cap"]["infeasible"]:
        a0 = eng.indices[sec].get(dl, {}); a1 = e.indices[sec].get(dl, {})
        if a0.get("att") and a1.get("att") and a0.get("eq"):
            diffs.append({"sector": sec, "n": n, "eq": round(a0["eq"], 2), "att_fixed": round(a0["att"], 2),
                          "att_relaxed": round(a1["att"], 2), "max_w_relaxed": round(a1.get("max_w_att") or 0, 3)})
    STATS["cap_relax"] = diffs
    if diffs:
        mad = statistics.mean(abs(r["att_relaxed"] / r["eq"] - 1) for r in diffs)
        check("T8b", "放寬律回復之聚焦傾斜(不可行群 att_relaxed vs eq 終值差)", "INFO",
              f"{len(diffs)} 群 平均 |att_relaxed/eq−1|={mad:.2%};max w 放寬後 ≤{max(r['max_w_relaxed'] for r in diffs):.2f};"
              f"憲法 C-17 不動——是否採放寬律候操作員定奪")
    else:
        check("T8b", "放寬律實驗", "SKIP", "無不可行群")


# ─────────────────────────── T9 PC1 穩定 ───────────────────────────

def t9_pc1(eng, apce):
    print("\n═══ T9 PC1 穩定性(40/60/90 窗)═══")
    S, dates, di = eng.S, eng.dates, eng.di
    res = {}
    for W in (40, 60, 90):
        win = dates[-W:]
        for sec in eng.indices:
            mem = [t for t in S if S[t]["sector"] == sec and not S[t]["is_tsmc"]]
            full = [t for t in mem if all(d in S[t]["rows"] and S[t]["ret"][di[d][t]] is not None for d in win)]
            mat = [[S[t]["ret"][di[d][t]] for t in full] for d in win] if len(full) >= 3 else []
            res.setdefault(sec, {})[W] = apce.pc1_absorption(mat) if mat else None
    secs = [s for s in res if all(res[s][w] is not None for w in (40, 60, 90))]
    rho = spearman([res[s][40] for s in secs], [res[s][90] for s in secs]) if len(secs) >= 5 else None
    flips = [s for s in secs if (res[s][60] >= 0.55) != (res[s][90] >= 0.55)]
    STATS["pc1"] = {s: {str(w): (round(v, 3) if v is not None else None) for w, v in d.items()} for s, d in res.items()}
    check("T9", "PC1 吸收率跨窗穩定(40 vs 90 窗 Spearman;0.55 資格翻轉)", "PASS" if (rho or 0) > 0.6 else "WARN",
          f"{len(secs)} 群 ρ(40,90)={rho:.3f};60↔90 窗資格翻轉 {len(flips)} 群:{flips[:6]}" if rho is not None else "樣本不足")


# ─────────────────────────── T10/T11 高原與閹割 ───────────────────────────

def run_variant(apce, rows, params):
    e = apce.APCE(params)
    e.resolve_params()
    r = e.run(rows, base_date="2026-01-01")
    return {x["ticker"]: x["role"] for x in r["latest"]}


def agree(a, b):
    ks = [k for k in a if k in b and a[k] and b[k]]
    return (sum(1 for k in ks if a[k] == b[k]) / len(ks)) if ks else None


def jaccard(a, b):
    A = {k for k, v in a.items() if v == "LEADER"}
    B = {k for k, v in b.items() if v == "LEADER"}
    return len(A & B) / len(A | B) if (A | B) else 1.0


def t10_plateau(apce, rows, base_roles):
    print("\n═══ T10 高原測試(單軸掃描)═══")
    grid = [("corr_q", 0.35), ("corr_q", 0.55), ("quant_window", 40), ("quant_window", 80),
            ("ewm_span", 30), ("ewm_span", 70)]
    table = []
    for k, v in grid:
        roles = run_variant(apce, rows, {k: v})
        table.append({"param": k, "value": v, "role_agreement": round(agree(base_roles, roles) or 0, 3),
                      "leader_jaccard": round(jaccard(base_roles, roles), 3),
                      "n_leader": sum(1 for r in roles.values() if r == "LEADER")})
    STATS["plateau"] = table
    mn = min(r["role_agreement"] for r in table)
    check("T10", "參數高原(角色一致率最低值 ≥0.80=高原;<0.80=孤峰)", "PASS" if mn >= 0.80 else "WARN",
          "; ".join(f"{r['param']}={r['value']}:一致 {r['role_agreement']:.2f}/LEADER J={r['leader_jaccard']:.2f}(n={r['n_leader']})" for r in table))


def t11_ablation(apce, rows, base_roles):
    print("\n═══ T11 閹割測試 ═══")
    table = []
    for ab in ("vol", "div", "rs"):
        roles = run_variant(apce, rows, {"ablate": [ab]})
        ch = 1 - (agree(base_roles, roles) or 1)
        table.append({"ablate": ab, "role_change": round(ch, 3),
                      "n_leader": sum(1 for r in roles.values() if r == "LEADER"),
                      "n_fake_wash": sum(1 for r in roles.values() if r in ("FAKE_PULL", "WASHOUT"))})
    STATS["ablation"] = table
    check("T11", "閹割貢獻(拔閘門後角色變動率;越大=閘門越有作用)", "INFO",
          "; ".join(f"拔 {r['ablate']}:變動 {r['role_change']:.1%} LEADER {r['n_leader']} FAKE/WASH {r['n_fake_wash']}" for r in table))


def t11b_volcorr(eng):
    """2D 覆蓋不觸發之診斷:vol_corr 分佈(近零=Δetr% 噪音淹沒共識)。"""
    print("\n═══ T11b vol_corr 分佈診斷 ═══")
    vals, pvals = [], []
    for t, i in eng.di[eng.dates[-1]].items():
        s = eng.S[t]
        if s["is_tsmc"]:
            continue
        if s["vol_corr"][i] is not None: vals.append(s["vol_corr"][i])
        if s["price_corr"][i] is not None: pvals.append(s["price_corr"][i])
    if len(vals) < 20:
        check("T11b", "vol_corr 分佈", "SKIP", "樣本不足"); return
    vs = sorted(vals); ps = sorted(pvals)
    q = lambda a, x: a[int(x * (len(a) - 1))]
    neg = sum(1 for v in vals if v < 0) / len(vals)
    STATS["volcorr"] = {"median": round(q(vs, .5), 3), "p10": round(q(vs, .1), 3), "p90": round(q(vs, .9), 3), "neg_share": round(neg, 3),
                        "price_median": round(q(ps, .5), 3), "price_p10": round(q(ps, .1), 3)}
    check("T11b", "vol_corr 分佈(原稿 FAKE/WASH 以 <0 為條件之可行性診斷)", "WARN" if neg == 0 else "INFO",
          f"vol_corr 中位 {q(vs, .5):+.3f} P10 {q(vs, .1):+.3f} P90 {q(vs, .9):+.3f} 負占比 {neg:.0%};price_corr 中位 {q(ps, .5):+.3f} P10 {q(ps, .1):+.3f}"
          f"——原稿 <0 為死條件(0% 觸發);批310 改族群池 P20 動態低分位後 2D 覆蓋方可觸發")


# ─────────────────────────── T12 置換+FDR ───────────────────────────

def t12_permutation(eng, leadlag, B=200, k=5, q=0.10, seed=7):
    print("\n═══ T12 置換檢定+FDR(族群 att 指數 vs Δclean_mkt%)═══")
    rng = random.Random(seed)
    dates = eng.dates
    cm = [eng.clean_mkt.get(d) for d in dates]
    y = [None] + [(cm[i] / cm[i - 1] - 1) if (cm[i] and cm[i - 1]) else None for i in range(1, len(cm))]
    rows = []
    for sec, idx in eng.indices.items():
        lv = [idx.get(d, {}).get("att") for d in dates]
        x = [None] + [(lv[i] / lv[i - 1] - 1) if (lv[i] and lv[i - 1]) else None for i in range(1, len(lv))]
        pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
        if len(pairs) < 2 * k + 8:
            continue
        xs, ys = [p[0] for p in pairs], [p[1] for p in pairs]
        obs = leadlag.edge_leadlag(xs, ys, k)
        if obs.get("verdict") == "INSUFFICIENT":
            continue
        o = abs(obs["ic"])
        cnt = 0
        for _ in range(B):
            yy = ys[:]
            rng.shuffle(yy)
            e = leadlag.edge_leadlag(xs, yy, k)
            if abs(e.get("ic", 0)) >= o:
                cnt += 1
        p = (1 + cnt) / (B + 1)
        rows.append({"sector": sec, "peak_lag": obs["peak_lag"], "ic": obs["ic"], "p": round(p, 4),
                     "direction": "族群領先市場" if obs["peak_lag"] > 0 else "市場領先族群" if obs["peak_lag"] < 0 else "同期"})
    # BH FDR
    rows.sort(key=lambda r: r["p"])
    m = len(rows)
    sig = 0
    for i, r in enumerate(rows, 1):
        r["bh_crit"] = round(q * i / m, 4)
        if r["p"] <= q * i / m:
            sig = i
    for i, r in enumerate(rows, 1):
        r["fdr_sig"] = i <= sig
    STATS["permutation"] = rows
    n_raw = sum(1 for r in rows if r["p"] <= 0.05)
    check("T12", f"CCF ±{k} 置換檢定 B={B}(C-02 p≤0.05)+BH FDR q={q}(C-02b)", "INFO",
          f"{m} 群:raw p≤0.05 {n_raw} 群 → FDR 後 {sig} 群顯著;" +
          "; ".join(f"{r['sector']} lag={r['peak_lag']:+d} IC={r['ic']:+.2f} p={r['p']}" for r in rows[:4]))


# ─────────────────────────── T13 小公雞 ───────────────────────────

def t13_smallcap(eng):
    print("\n═══ T13 小公雞謬誤量化 ═══")
    dl = eng.dates[-1]
    rows = []
    for t, i in eng.di[dl].items():
        s = eng.S[t]
        if s["is_tsmc"] or s.get("vol_shock", [None])[i] is None or s.get("gravity_shock", [None])[i] is None:
            continue
        rows.append((t, s["vol_shock"][i], s["gravity_shock"][i], s["size_tier"][i]))
    if len(rows) < 20:
        check("T13", "小公雞謬誤", "SKIP", "樣本不足")
        return
    top_v = sorted(rows, key=lambda r: -r[1])[:10]
    top_g = sorted(rows, key=lambda r: -r[2])[:10]
    sv = sum(1 for r in top_v if r[3] == "Small")
    sg = sum(1 for r in top_g if r[3] == "Small")
    STATS["smallcap"] = {"vol_shock_top10_small": sv, "gravity_top10_small": sg,
                         "top_vol": [r[0] for r in top_v], "top_gravity": [r[0] for r in top_g]}
    check("T13", "時序 Z(vol_shock)Top10 vs 重力乘數 Top10 之 Small 占比", "PASS" if sg <= sv else "WARN",
          f"vol_shock Top10 含 Small {sv} 檔 → gravity Top10 含 Small {sg} 檔(重力乘數壓小公雞);gravity Top:{[r[0] for r in top_g[:5]]}")


# ─────────────────────────── T14 家族校準 ───────────────────────────

def t14_family(eng, fam):
    print("\n═══ T14 參數家族實值校準 ═══")
    S, dates, di = eng.S, eng.dates, eng.di
    hist05, hist06 = [], []
    for d in dates:
        sc = [S[t]["leader_score"][i] for t, i in di[d].items() if "leader_score" in S[t] and S[t]["leader_score"][i] is not None]
        if len(sc) >= 20:
            srt = sorted(sc)
            hist05.append(srt[int(0.8 * (len(srt) - 1))])
            hist06.append(srt[int(0.5 * (len(srt) - 1))])
    cm = [eng.clean_mkt.get(d) for d in dates]
    w = [v for v in cm[-20:] if v]
    cm_z = (cm[-1] - statistics.mean(w)) / (statistics.pstdev(w) or 1e-9) if len(w) >= 8 else 0.0
    def breadth(k):
        d = dates[k]
        vals = [S[t]["ret20"][i] for t, i in di[d].items() if "ret20" in S[t] and S[t]["ret20"][i] is not None]
        return sum(1 for v in vals if v > 0) / len(vals) if vals else None
    b_now, b_prev = breadth(len(dates) - 1), breadth(len(dates) - 21)
    breadth_change = (b_now - b_prev) if (b_now is not None and b_prev is not None) else 0.0
    regime = "RISK_ON" if (b_now or 0) >= 0.5 else "RISK_OFF"
    state = {"clean_mkt_z": round(cm_z, 3), "breadth_change": round(breadth_change, 3), "member_ratio": 1.0,
             "group_as_median_z": 0.0, "regime": regime, "n_obs": len(dates)}
    entry = fam.calibrate({"C-05": hist05, "C-06": hist06}, state, write=True)
    STATS["family"] = {"state": state, "modes": entry["modes"], "fired": entry["fired_triggers"],
                       "C-05": next(r for r in entry["params"] if r["id"] == "C-05"),
                       "C-06": next(r for r in entry["params"] if r["id"] == "C-06"),
                       "C-13": next(r for r in entry["params"] if r["id"] == "C-13")}
    c05 = STATS["family"]["C-05"]
    check("T14", "家族以真實歷史校準(C-05/C-06 滾動;鎖觸狀態實評)", "PASS" if c05["mode"] in ("ROLLING", "LOCKED") else "WARN",
          f"state={state};模式 {entry['modes']};觸發 {entry['fired_triggers'] or '無'};C-05={c05['value']}({c05['mode']});"
          f"C-13={STATS['family']['C-13']['value']}({STATS['family']['C-13']['mode']})")


# ─────────────────────────── 主流程 ───────────────────────────

def main() -> int:
    print("=" * 72)
    print(" 批310 APCE 壓力測試砲台(真實面板)")
    print("=" * 72)
    t1_regression()
    rows = json.loads(PANEL.read_text(encoding="utf-8"))["rows"]
    # T0 樣本選擇偏差:族群冊策展日 vs 面板起日(事後贏家入冊=回測全史受污染)
    cfg = sorted((FS / "config").glob("TW_Group_Classification_v*.json"))[-1]
    book = json.loads(cfg.read_text(encoding="utf-8"))
    curated = str(book.get("generated") or book.get("asof") or (book.get("history") or [{}])[0].get("ts") or "2026-08")[:10]
    d0 = min(r["date"] for r in rows)
    check("T0", "樣本選擇偏差警示(族群冊策展日 vs 面板起日)", "WARN",
          f"族群冊 {cfg.name} 策展於 {curated}(批52 熱門族群總表),面板自 {d0} 起——策展前之歷史屬事後選擇(hindsight),"
          f"T3/T4 之 IC 與角色前瞻報酬為樣本內數,不得解讀為樣本外效度;真效度須自 {curated} 起滾動累積")
    t2_panel(rows)
    apce = load_mod("flow_apce", "FLOW_ENG029_FlowApce.py")
    leadlag = load_mod("flow_leadlag", "FLOW_ENG020_FlowLeadlag.py")
    fam = load_mod("flow_param_family", "FLOW_ENG028_FlowParamFamily.py")
    eng = apce.APCE()
    eng.resolve_params()
    res = eng.run(rows, base_date="2026-01-01")
    base_roles = {x["ticker"]: x["role"] for x in res["latest"]}
    STATS["baseline"] = {"asof": res["asof"], "roles": res["role_counts"], "n": res["n_tickers"]}
    t3_ic(eng)
    t4_roles(eng)
    t5_turnover(eng)
    t6_lookahead(eng)
    t7_survivorship(eng)
    t8_cap(eng)
    t8b_cap_relax(apce, rows, eng)
    t9_pc1(eng, apce)
    t10_plateau(apce, rows, base_roles)
    t11_ablation(apce, rows, base_roles)
    t11b_volcorr(eng)
    t12_permutation(eng, leadlag)
    t13_smallcap(eng)
    t14_family(eng, fam)
    n = {}
    for r in RESULTS:
        n[r["status"]] = n.get(r["status"], 0) + 1
    verdict = "HAS_FAILURES" if n.get("FAIL") else ("GREEN_WITH_NOTES" if n.get("WARN") else "ALL_GREEN")
    OUT.write_text(json.dumps({"schema": "batch310-stress-v1", "ts": NOW, "counts": n, "verdict": verdict,
                               "checks": RESULTS, "stats": STATS}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n" + "=" * 72)
    print(f"  [計] {n} → {verdict}")
    print(f"  [出] {OUT.name}")
    return 0 if not n.get("FAIL") else 1


if __name__ == "__main__":
    raise SystemExit(main())
