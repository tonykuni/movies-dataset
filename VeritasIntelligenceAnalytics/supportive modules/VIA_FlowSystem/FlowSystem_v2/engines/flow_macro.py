# -*- coding: utf-8 -*-
"""VDF-FLOW-MACRO flow_macro.py — 宏觀對照層 v2(自適應權重;操作員 2026/08/12 令)。

v2(重因素全考量 · 權重鐵律):
  因子全譜:五幣匯率(TWD/JPY/GBP/EUR/CNH)· 各區政策利率 · 長中短期公債殖利率
  (2y/10y/30y + 期限斜率)· 黃金現貨+期貨(動能+基差)· 總體經濟 · 貿易收支 ·
  財政收支 · 通膨 · 美元指數 · 加密貨幣(BTC 風險胃納)— 13 因子/區。
  **權重鐵律:任何參數權重全都是算出來的、變動的、不可固定** —
    weight_i(t) = 滾動 rank-IC(因子_i, 次期區域 FIS) / Σ|IC|(帶號正規化)
    · 連「方向」都由 IC 符號決定 — 引擎零手寫因子符號、零固定權重
    · 視窗自適應:掃 {20,40,60} 取 |平均IC| 最高者(逐區各自選)
    · 樣本 < min_obs 之因子誠實閒置(不進權重);全閒置=判讀留白「樣本不足」
    · 每輪重算 → 權重是輸出不是設定;weights_derivation 全程可稽
v1(2026/08/12):固定權重四因子 — 已依鐵律廢除,config 不再有 weights 鍵。
資料:data/input/macro_data.json 側車 v2(records 長表 {date,series,value};零爬站);
缺=合成 demo(注入與 FIS 相關結構供權重推導示範,明標 synthetic)。
產物:data/output/macro_overlay.json — rows[].weights(前 N 主導因子)+ 全權重表。
"""
import json
import math
import random
from pathlib import Path

from flow_core import bucket_fis, load_json, load_universe, _mean, _std

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CFG = ROOT / "config" / "macro.json"
INP = ROOT / "data" / "input" / "macro_data.json"
OUTP = ROOT / "data" / "output" / "macro_overlay.json"

# 因子目錄:id → (中文名, 取值函數鍵);值一律轉動能/差分/z — 符號交給 IC,不手寫
FACTORS = [
    ("flow_mom", "資金流自身動能"), ("flow_chg", "資金流變化率"),
    ("fx_mom", "本幣匯率動能"), ("rate_diff", "政策利差(區−美)"),
    ("y2_diff", "短債殖利差 2y"), ("y10_diff", "長債殖利差 10y"),
    ("y30_diff", "超長債殖利差 30y"), ("curve_slope", "期限斜率(10y−2y)"),
    ("econ", "總體經濟強弱"), ("trade", "貿易收支"), ("fiscal", "財政收支"),
    ("infl", "通膨"), ("dxy_mom", "美元指數動能"),
    ("gold_mom", "黃金現貨動能"), ("gold_basis", "黃金期現基差"),
    ("btc_mom", "加密貨幣動能"),
]

# 為何用它(每因子一行白話 — 操作員「用何指標判讀 為何用他」)
WHY = {
    "flow_mom": "錢有慣性:今天在流入的地方,明天多半還在流入 — 文獻與實務最穩的單一預測子",
    "flow_chg": "慣性之外看加速度:流入正在加速還是減速,抓轉折比水位早",
    "fx_mom": "本幣走強通常伴隨外資匯入 — 匯率是資金進出的即時腳印",
    "rate_diff": "利差=錢的地心引力:哪邊利率高(相對美國),游資往哪邊爬",
    "y2_diff": "短債殖利差反映貨幣政策預期差 — 快錢對它最敏感",
    "y10_diff": "長債殖利差反映長期資金配置吸引力",
    "y30_diff": "超長端看保險/退休金等超長線資金的動向",
    "curve_slope": "殖利率曲線斜率=景氣預期:倒掛常先於資金避險",
    "econ": "經濟強弱(PMI)決定基本面資金要不要來",
    "trade": "貿易順差=經常帳美元流入的底盤",
    "fiscal": "財政赤字擴大會擠壓債市、影響主權資金信心",
    "infl": "通膨決定實質報酬 — 錢怕被通膨吃掉",
    "dxy_mom": "美元走強=全球資金抽回美元體系,新興區首當其衝",
    "gold_mom": "黃金是避險體溫計:金價急漲=資金在躲",
    "gold_basis": "期現基差看槓桿投機情緒(期貨溢價擴大=投機加碼)",
    "btc_mom": "加密是風險胃納的極端哨兵:BTC 衝=最敢衝的錢出動了",
}
FX_NAME = {"Taiwan": "USDTWD", "Japan": "USDJPY", "Europe": "EURUSD", "UK": "GBPUSD",
           "China": "USDCNH", "US": "DXY", "Korea": "USDKRW", "India": "USDINR",
           "EM": "EEM_FX", "LatAm": "USDBRL", "AsiaExJP": "ADXY", "DM": "DXY",
           "Global": "DXY"}


def load_macro_cfg():
    return load_json(CFG, {}) or {}


def _rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    rk = [0.0] * len(xs)
    for pos, i in enumerate(order):
        rk[i] = pos
    return rk


def _rank_ic(a, b):
    pairs = [(x, y) for x, y in zip(a, b)
             if x is not None and y is not None and math.isfinite(x) and math.isfinite(y)]
    if len(pairs) < 3:
        return None, 0
    ra, rb = _rank([p[0] for p in pairs]), _rank([p[1] for p in pairs])
    ma, mb = _mean(ra), _mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return (num / den if den > 1e-12 else 0.0), len(pairs)


def _mom(series, k=10):
    out = [None] * len(series)
    for i in range(k, len(series)):
        a, b = series[i], series[i - k]
        if a is not None and b not in (None, 0):
            out[i] = (a / b - 1.0) * 100.0
    return out


NO_Z = {"flow_mom", "flow_chg"}  # 已是分數單位(FIS 本身=標準化分數)— 二次 z 會洗掉水準/慣性資訊


def _z_last(vals, w=40, fid=None):
    v = [x for x in vals if x is not None][-w:]
    if not v:
        return None
    if fid in NO_Z:
        return max(-3.0, min(3.0, 3.0 * v[-1] / 100.0))  # 等值刻度,保留水準符號
    if len(v) < 3:
        return None
    sd = _std(v)
    return (v[-1] - _mean(v)) / sd if sd > 1e-9 else 0.0


def _synth_macro(cfg, region_fis, seed=23):
    """合成 demo(明標):所有 series 注入部分 FIS 相關結構 — 供自適應權重推導示範;
    真實側車到位即棄用。長表 {date, series, value}。"""
    rng = random.Random(seed)
    regions = list(cfg.get("regions", {}).keys())
    dates = sorted({d for rs in region_fis.values() for d in rs})
    if not dates:
        return {"source": "synthetic demo", "records": []}
    recs = []
    glob = {"DXY": 103.0, "GOLD_SPOT": 2400.0, "GOLD_FUT": 2415.0, "BTC": 62000.0}
    state = {}
    for r in regions:
        state[r] = {"FX": 100.0, "RATE": rng.uniform(0.5, 6.0), "Y2": rng.uniform(1, 5),
                    "Y10": rng.uniform(2, 6), "Y30": rng.uniform(2.5, 6.5),
                    "ECON": 50.0, "TRADE": 0.0, "FISCAL": -2.0, "CPI": 2.5}
    for i, d in enumerate(dates):
        risk = _mean([list(region_fis.get(r, {}).values())[min(i, len(region_fis.get(r, {})) - 1)]
                      if region_fis.get(r) else 0.0 for r in regions[:4]]) / 100.0
        glob["DXY"] *= 1 + rng.gauss(-0.002 * risk, 0.003)
        glob["GOLD_SPOT"] *= 1 + rng.gauss(-0.001 * risk, 0.004)
        glob["GOLD_FUT"] = glob["GOLD_SPOT"] * (1 + rng.gauss(0.004, 0.002))
        glob["BTC"] *= 1 + rng.gauss(0.004 * risk, 0.012)
        for k, v in glob.items():
            recs.append({"date": d, "series": k, "value": round(v, 3)})
        for r in regions:
            st = state[r]
            f = region_fis.get(r, {})
            fis_d = list(f.values())[min(i, len(f) - 1)] / 100.0 if f else 0.0
            st["FX"] *= 1 + rng.gauss(0.001 * fis_d, 0.004)
            st["ECON"] = max(38, min(62, st["ECON"] + rng.gauss(0.25 * fis_d, 0.3)))
            st["TRADE"] += rng.gauss(0.1 * fis_d, 0.25)
            st["FISCAL"] += rng.gauss(0.02 * fis_d, 0.08)
            st["CPI"] = max(-1, min(9, st["CPI"] + rng.gauss(0, 0.05)))
            st["Y2"] = max(0, st["Y2"] + rng.gauss(0, 0.02))
            st["Y10"] = max(0, st["Y10"] + rng.gauss(0, 0.02))
            st["Y30"] = max(0, st["Y30"] + rng.gauss(0, 0.015))
            for k in ("FX", "RATE", "Y2", "Y10", "Y30", "ECON", "TRADE", "FISCAL", "CPI"):
                recs.append({"date": d, "series": "%s_%s" % (k, r), "value": round(st[k], 4)})
    return {"source": "synthetic demo(注入 FIS 相關結構供權重推導示範;接 macro_data.json 即真)",
            "records": recs}


def _series_map(data):
    m = {}
    for rec in data.get("records", []):
        m.setdefault(str(rec["series"]), {})[str(rec["date"])] = rec["value"]
    return m


def _aligned(smap, name, dates):
    s = smap.get(name, {})
    return [s.get(d) for d in dates]


def _factor_series(smap, region, dates, us="US", fis_series=None):
    """16 因子逐日序列(值層;符號交給 IC)。flow_mom/flow_chg=資金流自身動能(AR 慣性,walk-forward 合法:只用 t 當下)。"""
    fx = _aligned(smap, "FX_%s" % region, dates)
    out = {"fx_mom": _mom(fx)}
    fs = [(fis_series or {}).get(d) for d in dates]
    out["flow_mom"] = fs
    out["flow_chg"] = [None if (a is None or b is None) else a - b
                       for a, b in zip(fs, [None] + fs[:-1])]
    for fid, key in (("rate_diff", "RATE"), ("y2_diff", "Y2"),
                     ("y10_diff", "Y10"), ("y30_diff", "Y30")):
        a = _aligned(smap, "%s_%s" % (key, region), dates)
        b = _aligned(smap, "%s_%s" % (key, us), dates)
        out[fid] = [None if (x is None or y is None) else x - y for x, y in zip(a, b)]
    y2 = _aligned(smap, "Y2_%s" % region, dates)
    y10 = _aligned(smap, "Y10_%s" % region, dates)
    out["curve_slope"] = [None if (a is None or b is None) else b - a for a, b in zip(y2, y10)]
    out["econ"] = _aligned(smap, "ECON_%s" % region, dates)
    out["trade"] = _aligned(smap, "TRADE_%s" % region, dates)
    out["fiscal"] = _aligned(smap, "FISCAL_%s" % region, dates)
    out["infl"] = _aligned(smap, "CPI_%s" % region, dates)
    out["dxy_mom"] = _mom(_aligned(smap, "DXY", dates))
    gs = _aligned(smap, "GOLD_SPOT", dates)
    gf = _aligned(smap, "GOLD_FUT", dates)
    out["gold_mom"] = _mom(gs)
    out["gold_basis"] = [None if (a in (None, 0) or b is None) else (b - a) / a * 100.0
                         for a, b in zip(gs, gf)]
    out["btc_mom"] = _mom(_aligned(smap, "BTC", dates))
    return out


def _t_of_ic(ic, n):
    if n < 4 or abs(ic) >= 1.0:
        return 0.0
    return ic * math.sqrt((n - 2) / max(1e-9, 1.0 - ic * ic))


def _adaptive_weights(fmat, fis_series, dates, windows, min_obs, t_gate=1.5):
    """權重鐵律核心 v2(準確度三升級):
    ①顯著閘:|t(IC)| < t_gate 之因子閒置(雜訊不給話語權 — FDR-lite)
    ②收縮:IC×n/(n+20) 向 0 收縮(小樣本不給大權重,防過擬合)
    ③三視窗「集成」取代單視窗挑選(挑最好=過擬合;平均=穩)— 信度↑
    weight = 收縮IC/Σ|收縮IC|(帶號);全輸出可稽,仍是每輪算出、絕不固定。"""
    y_next = [fis_series.get(dates[i + 1]) if i + 1 < len(dates) else None
              for i in range(len(dates))]
    ens = {}
    detail = {}
    n_win = 0
    for w in windows:
        ics = {}
        for fid, _zh in FACTORS:
            xs = fmat[fid][-w - 1:-1] if len(fmat[fid]) > w else fmat[fid][:-1]
            ys = y_next[-w - 1:-1] if len(y_next) > w else y_next[:-1]
            ic, n = _rank_ic(xs, ys)
            if ic is None or n < min_obs:
                continue
            t = _t_of_ic(ic, n)
            if abs(t) < t_gate:
                detail.setdefault(fid, []).append({"w": w, "ic": round(ic, 4), "t": round(t, 2), "gate": "閒置(未達顯著)"})
                continue
            shrunk = ic * n / (n + 20.0)
            ics[fid] = shrunk
            detail.setdefault(fid, []).append({"w": w, "ic": round(ic, 4), "t": round(t, 2), "shrunk": round(shrunk, 4)})
        if ics:
            n_win += 1
            for fid, v in ics.items():
                ens[fid] = ens.get(fid, 0.0) + v
    weights = {}
    if n_win:
        for fid in list(ens):
            ens[fid] /= n_win
        tot = sum(abs(v) for v in ens.values())
        if tot > 1e-9:
            weights = {fid: round(v / tot, 4) for fid, v in ens.items()}
    return weights, {"window": "ens%s" % windows, "ics": {k: {"ic": round(v, 4), "n": min_obs}
                                                          for k, v in ens.items()},
                     "detail": detail, "n_windows": n_win, "t_gate": t_gate}


# 誠實缺口清單(操作員「我們少考量甚麼」;白話一行+補法;只增不減)
GAPS = [
    ("真實資料", "現在是示範資料在跑 — 這是最大缺口", "把真實序列放進 macro_data.json 即接上"),
    ("波動率 VIX", "市場怕不怕沒看 — 恐慌時資金行為不一樣", "加 VIX 與期限結構為因子"),
    ("信用利差", "公司債借錢貴不貴沒看 — 這常比股市先反應", "加 HY−IG 利差因子"),
    ("油價/商品", "只看了黃金 — 油銅是景氣的體溫計", "加 WTI/銅動能因子"),
    ("流動性", "量沒看 — 只看方向不看深淺會誤判力道", "加成交量/買賣價差因子"),
    ("資金面", "美元體系水位(RRP/準備金)沒看", "加 Fed 資金面序列"),
    ("政策行事曆", "FOMC/CPI 公布日前後行為不同,系統不知道日曆", "加事件日旗標,事件窗另計"),
    ("市場情緒", "散戶/選擇權情緒(Put-Call)沒看", "加情緒指標因子"),
    ("因子重疊", "14 因子彼此有重疊(如利差與匯率相關)— 同一訊號可能被算兩次", "因子正交化或分群後再配權"),
    ("牛熊分段", "權重是滾動算,但牛市熊市的有效因子本就不同", "依 regime 分段各自推導權重"),
    ("多重檢定", "14 因子×13 區一起找關聯,總會撞到假訊號", "加 FDR 假發現率控制"),
    ("季節性", "月底/季底資金例行移動沒排除", "加日曆效應校正"),
]


def _validity_reliability(region_fis, smap, dates, cfg, windows, min_obs):
    """效度+信度量測(全算出、走樣本外,誠實):
    效度 = walk-forward 命中率:只用 t 以前資料算權重+打分,對 t+1 FIS 方向 — 丟銅板=50%
    信度 = ①對半重算:前 2/3 vs 後 2/3 各算權重,答案相似度(共同因子權重排名相關)
           ②判讀穩定:walk-forward 中宏觀分翻號頻率(翻來翻去=不可靠)"""
    hits = tries = flips = 0
    halves = []
    scored = []  # (|score|, hit) — 強度校準:強訊號應更準
    for region in cfg.get("regions", {}):
        fis_s = region_fis.get(region, {})
        if len(fis_s) < 34:
            continue
        prev_sign = None
        for i in range(30, len(dates) - 1, 5):
            sub = dates[:i + 1]
            fmat = _factor_series(smap, region, sub, fis_series=fis_s)
            w8, deriv = _adaptive_weights(fmat, fis_s, sub, windows, min_obs)
            if not w8:
                continue
            score = 0.0
            zw = int(_mean(windows))
            for fid, wt in w8.items():
                z = _z_last(fmat[fid], zw, fid)
                if z is not None:
                    score += wt * max(-3.0, min(3.0, z))
            nxt = fis_s.get(dates[i + 1])
            if nxt is None or abs(nxt) < 1e-9:
                continue
            tries += 1
            hit_i = (score >= 0) == (nxt >= 0)
            if hit_i:
                hits += 1
            scored.append((abs(score), hit_i))
            sgn = score >= 0
            if prev_sign is not None and sgn != prev_sign:
                flips += 1
            prev_sign = sgn
        k = len(dates)
        a, _ = _adaptive_weights(_factor_series(smap, region, dates[:2 * k // 3], fis_series=fis_s),
                                 fis_s, dates[:2 * k // 3], windows, min_obs)
        b, _ = _adaptive_weights(_factor_series(smap, region, dates[k // 3:], fis_series=fis_s),
                                 fis_s, dates[k // 3:], windows, min_obs)
        common = set(a) & set(b)
        if len(common) >= 4:
            ra = _rank([a[f] for f in common])
            rb = _rank([b[f] for f in common])
            ma, mb = _mean(ra), _mean(rb)
            num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
            den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
            if den > 1e-12:
                halves.append(num / den)
    hit = (hits / tries) if tries else None
    hs = hw = None
    if len(scored) >= 30:
        scored.sort(key=lambda x: x[0])
        k3 = len(scored) // 3
        weak, strong = scored[:k3], scored[-k3:]
        hw = sum(1 for _, h in weak if h) / len(weak)
        hs = sum(1 for _, h in strong if h) / len(strong)
    return {
        "hit_strong": round(hs, 3) if hs is not None else None,
        "hit_weak": round(hw, 3) if hw is not None else None,
        "validity_hit_rate": round(hit, 3) if hit is not None else None,
        "validity_n": tries,
        "reliability_split_half": round(_mean(halves), 3) if halves else None,
        "reliability_flip_rate": round(flips / tries, 3) if tries else None,
        "plain": ("【白話】效度=判讀準不準:把時間切回過去,只用當時以前的資料打分,看隔天資金流方向有沒有跟上 — "
                  "命中率 %s(丟銅板=50%%,樣本 %d 次)。信度=說法穩不穩:資料切前後兩段各算一次權重,"
                  "兩份答案相似度 %s(1=完全一致);判讀翻號頻率 %s(越低越穩)。"
                  % ("%.0f%%" % (100 * hit) if hit is not None else "樣本不足",
                     tries,
                     "%.2f" % _mean(halves) if halves else "樣本不足",
                     ("%.0f%%" % (100 * flips / tries)) if tries else "—")
                  + ("強度校準:強訊號命中 %.0f%% vs 弱訊號 %.0f%%(強>弱=分數大小有意義,可依強度分配注意力)。"
                     % (100 * hs, 100 * hw) if hs is not None else "")),
        "honest": "命中率為樣本外 walk-forward(每步只用當步以前的資料),非事後諸葛;樣本仍少,數字會隨資料增長收斂",
    }


def build_overlay(rows, write=True):
    cfg = load_macro_cfg()
    ad = cfg.get("adaptive", {})
    windows = [int(x) for x in ad.get("windows", [20, 40, 60])]
    min_obs = int(ad.get("min_obs", 20))
    top_show = int(ad.get("top_show", 3))
    uni = load_universe()
    zh_map = dict(FACTORS)
    # 每區逐日 FIS 序列
    by_d = {}
    for r in rows or []:
        by_d.setdefault(str(r["date"]), []).append(r)
    dates = sorted(by_d)
    region_fis = {}
    for d in dates:
        agg = bucket_fis(by_d[d], lambda r, u: u.get("region", "US"), universe=uni)
        for reg, v in agg.items():
            region_fis.setdefault(reg, {})[d] = v
    data = load_json(INP, None)
    real = bool(data and data.get("records") and
                not str(data.get("source", "")).startswith("synthetic"))
    if not (data and data.get("records")):
        data = _synth_macro(cfg, region_fis)
    smap = _series_map(data)
    dxy_last = _mom(_aligned(smap, "DXY", dates))
    dxy_m = next((v for v in reversed(dxy_last) if v is not None), 0.0)
    dxy_regime = "美元走強" if dxy_m > 0.5 else ("美元走弱" if dxy_m < -0.5 else "美元持平")
    out_rows, weights_table = [], {}
    for region in cfg.get("regions", {}):
        fis_s = region_fis.get(region, {})
        fis = fis_s.get(dates[-1]) if dates else None
        fmat = _factor_series(smap, region, dates, fis_series=fis_s)
        weights, deriv = _adaptive_weights(fmat, fis_s, dates, windows, min_obs)
        if not weights:
            out_rows.append({"region": region, "fis": fis, "macro_score": None,
                             "weights": [], "verdict": "樣本不足 — 權重未定,判讀留白(誠實)",
                             "vk": "na", "window": None})
            continue
        w = deriv["window"]
        zw = int(_mean(windows))
        score = 0.0
        contrib = []
        for fid, wt in weights.items():
            z = _z_last(fmat[fid], zw, fid)
            if z is None:
                continue
            score += wt * max(-3.0, min(3.0, z))
            contrib.append({"f": fid, "zh": zh_map[fid], "w": wt,
                            "z": round(z, 2), "c": round(wt * max(-3, min(3, z)), 3)})
        score = round(100.0 * math.tanh(score), 1)
        contrib.sort(key=lambda c: -abs(c["c"]))
        weights_table[region] = {"window": w, "weights": weights,
                                 "ics": deriv["ics"]}
        if fis is None:
            verdict, vk = "無流量樣本", "na"
        elif fis >= 0 and score >= 0:
            verdict, vk = "順風流入(宏觀支撐)", "ok"
        elif fis < 0 and score < 0:
            verdict, vk = "順風流出(宏觀同向)", "ok"
        elif fis >= 0:
            verdict, vk = "背離:流入無宏觀支撐 — 慎追", "warn"
        else:
            verdict, vk = "背離:流出但宏觀轉佳 — 關注轉折", "turn"
        out_rows.append({"region": region, "fis": fis, "macro_score": score,
                         "weights": contrib[:top_show], "window": w,
                         "n_factors": len(weights), "verdict": verdict, "vk": vk})
    out_rows.sort(key=lambda r: -(abs(r["fis"]) if r["fis"] is not None else -1))
    valid = [r for r in out_rows if r["fis"] is not None]
    vr = _validity_reliability(region_fis, smap, dates, cfg, windows, min_obs)
    result = {"version": "v2", "real_data": real, "source": data.get("source", ""),
              "validity_reliability": vr,
              "gaps": [{"name": n, "plain": p, "fix": f} for n, p, f in GAPS],
              "dxy": {"momentum": round(dxy_m, 2), "regime": dxy_regime},
              "overall_strength": round(_mean([abs(r["fis"]) for r in valid]) if valid else 0.0, 1),
              "factor_catalog": [{"id": f, "zh": z, "why": WHY.get(f, "")} for f, z in FACTORS],
              "rows": out_rows, "weights_table": weights_table,
              "weights_derivation": "權重鐵律:weight_i = 滾動 rank-IC(因子_i, 次期區域 FIS)/Σ|IC|(帶號);"
                                    "視窗自適應掃 %s;樣本<%d 之因子閒置;每輪重算 — 權重是輸出不是設定,連方向都由 IC 決定" % (windows, min_obs),
              "honest_note": "宏觀分=自適應規則組合非預測;" + ("真實側車資料" if real else "合成 demo(注入相關結構供權重推導示範)— 接 macro_data.json 即真")}
    if write:
        OUTP.parent.mkdir(parents=True, exist_ok=True)
        OUTP.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result
