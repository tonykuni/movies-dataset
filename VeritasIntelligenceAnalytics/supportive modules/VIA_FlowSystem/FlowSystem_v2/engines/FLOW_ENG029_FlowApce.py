#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""flow_apce — VIS 自適應完美分類引擎 APCE(批309;stdlib 零依賴)
====================================================================
操作員令(批309):落地「自適應完美分類引擎」設計稿——參數家族
(Type-F/D/H)、Attention Share 第一道輸入、動態大中小、三加權族群指數
(T-1 無前視/權重上限/鏈結法)、Price RS、自適應動能(半動態不失敏)、
2D 價量同動、K 線重心實質淨流、籌碼風格、信用當沖、Z 跨群修正、
角色雙重條件+遲滯、PC1 吸收率(探索/指數分級)、C-15/C-16 生命週期、
三策略訊號。稿為 Polars,本引擎以標準庫自算(倉庫零硬依賴律)。

釘卯點(方法論明文,零發明):
  1 巨錨隔離   台積電 2330 獨立;etr=max(0, 成交值−當沖);MFM=((C−L)−(H−C))/(H−L)
  A AS         as=etr/Σetr(排台積電);分母異常(C-21)標低可信度
  A2 分層      市值(股數×收盤;20 日中位)橫截面 P80/P40;缺股數退 AS 制 P90/P60
  I 指數       三加權 等權/階層(.5/.3/.2)/聚焦(權重上限 C-17=0.18 迭代封頂);
               權重取 T-1;鏈結法 I_t=I_{t-1}(1+Σw_{t-1,i}r_{t,i}/Σw)——成分變動
               不跳點;基準日 2026-01-01=100;n_members/max_w/HHI 監控
  RS           price_rs=idx_stock/idx_sector(att);rs_mom=rs−EWM40(rs)
  2 動能       vol_shock=(EWM5−EWM40)/EWMstd40;shock>2 基準線 0.75/0.25 加速;
               adaptive_score=(etr−baseline)/std;cs_z 橫截面 Z;gravity=z×√AS
  3/4 閘門     流動性 P25(族群池滾動);價同動 EWM-corr(ret, 群中位);量同動
               EWM-corr(Δetr%, 群中位);門檻=族群池滾動 P45(C-xx);絕對底線 C-18
  5 背離       adaptive_score>1 且 k_net_cash_z<−1(爆量留上影線出貨)
  C/D/E 籌碼   外資比/投信比 EWM+滾動分位 → Foreign/Domestic/Mixed、
               SITC/Dealer/Balanced;外資模式 Trend/Contrarian/Withdrawal/Neutral
  M 信用當沖   券資比 smr、當沖比 dtr、real_ratio、smr_shock、規制標籤(欄在才算)
  B 角色       複合分=C-13 領先性權重×領先分+(1−w)×聚焦分(族群內百分位);
               LEADER=族群前 20%∧分≥C-05∧價同動過閘∧rs_mom>0(相對+絕對雙重);
               2D 覆蓋:UNRELATED/FAKE_PULL/WASHOUT;LAGGER=分<C-06∨背離;
               樣本<5=RANK_ONLY;C-15 連 5 日掉出前 30% ⇒ 降級
  H 遲滯       valid=EWM3(閘門布林)雙閾值:≥0.7 入選/≤0.3 剔除/中間維持(C-19)
  G 族群健康   PC1 吸收率(60 日冪迭代)≥C-01 探索/≥C-01b 指數級;<C-16 剔除
誠實界線:欄缺=該模組 SKIP 並記 coverage;樣本不足=None;全數可稽。
用法:--run <panel.json> [--base 2026-01-01] | --selftest(十檢合成)
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

import importlib.util
import json
import math
import statistics
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT_DIR = ROOT / "data" / "output"
NOW = datetime.now().strftime("%Y-%m-%d %H:%M")
TSMC = "2330"


def _family():
    """參數家族解析器(ENG028)動態載入;缺=誠實 None(用冊載基值)。"""
    p = HERE / "FLOW_ENG028_FlowParamFamily.py"
    if not p.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location("flow_param_family", p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None


# 基值冊(對映門檻冊 C-xx;實跑時由 ParamFamily 解析覆蓋)
BASE = {"hys_enter": 0.7, "hys_exit": 0.3, "C-01": 0.40, "C-01b": 0.55, "C-05": 0.75, "C-06": 0.40, "C-13": 0.45,
        "C-15": 5, "C-16": 0.35, "C-17": 0.18, "C-18": 0.25, "C-19": 3, "C-21": 2.5,
        "corr_q": 0.45, "liquidity_q": 0.25, "quant_window": 60, "ewm_span": 50,
        "min_members_index": 5, "tier_weights": {"Large": 0.5, "Mid": 0.3, "Small": 0.2}}

# ─────────────────────────── 指標庫 registry(報告矩陣自此渲染) ───────────────────────────
CATALOG = [
    # (類, 變數, 公式, 意義, 參數型)
    ("一 基礎資金與聚焦", "etr", "max(0, 成交值−當沖成交值)", "實質留倉成交值;當沖缺=成交值(basis NO_DT 誠實標)", "F"),
    ("一 基礎資金與聚焦", "clean_mkt", "Σ etr(排台積電)", "全市場淨留倉資金", "F"),
    ("一 基礎資金與聚焦", "as", "etr/clean_mkt", "資金聚焦度 Attention Share(第一道輸入)", "核心"),
    ("一 基礎資金與聚焦", "as_conf", "|clean_mkt−Med20|/(1.4826·MAD20)>C-21 ⇒ LOW", "分母異常過濾(C-21=2.5σ)", "F"),
    ("一 基礎資金與聚焦", "dtr / real_ratio", "當沖/成交值;etr/成交值", "當沖虛擬乘數;留倉純度(當沖欄在才算)", "F"),
    ("二 價格指數與相對強度", "w_eq / w_tier / w_att", "1/N;.5/.3/.2 正規化;AS 正規化後迭代封頂 ≤C-17", "三加權(T-1 取用,無前視);聚焦權重上限 0.18", "F"),
    ("二 價格指數與相對強度", "idx_eq / idx_tier / idx_att", "I_t=I_{t-1}(1+Σw_{t-1}r_t/Σw);基準日=100", "鏈結法族群指數——成分變動不跳點", "F"),
    ("二 價格指數與相對強度", "n_members / max_w_att / hhi_att", "計數;max w;Σw²", "指數可複製性與集中度監控", "監控"),
    ("二 價格指數與相對強度", "price_rs", "idx_stock/idx_sector_att", "個股對族群價格相對強度(>1 跑贏)", "核心"),
    ("二 價格指數與相對強度", "rs_mom", "price_rs−EWM40(price_rs)", "相對強度動能(>0 真突破)", "核心"),
    ("三 動態量能與衝擊", "vol_shock", "(EWM5(etr)−EWM40(etr))/EWMstd40(etr)", "量能結構性放量(>2 Shock)", "D"),
    ("三 動態量能與衝擊", "baseline", "shock>2 ⇒ .75EWM5+.25EWM40 否則 EWM40", "自適應基準線(半動態不失敏)", "H"),
    ("三 動態量能與衝擊", "adaptive_score", "(etr−baseline)/EWMstd40", "自適應量能評分", "D"),
    ("三 動態量能與衝擊", "cs_z", "(etr−mean_date)/std_date", "橫截面 Z——跨群可比(今日資金池)", "D"),
    ("三 動態量能與衝擊", "gravity_shock", "vol_shock×√as", "資金重力乘數——異常度×重要性(防小公雞謬誤)", "D"),
    ("四 閘門與背離", "liq_floor / pass_liq", "族群池滾動 P25(etr)", "流動性閘門", "D"),
    ("四 閘門與背離", "price_corr", "EWM50-corr(ret, 群中位 ret)", "價格同動(族群共識)", "D"),
    ("四 閘門與背離", "vol_corr", "EWM50-corr(Δetr%, 群中位 Δetr%)", "量能同動(資金共識)——價到量的推進", "D"),
    ("四 閘門與背離", "p_th / v_th", "族群池滾動 P45(corr)", "動態及格線(C-xx corr_q)", "D"),
    ("四 閘門與背離", "mfm / k_net_cash_flow", "((C−L)−(H−C))/(H−L);mfm×etr", "K 線重心實質淨流(剝離當沖)", "F"),
    ("四 閘門與背離", "k_net_cash_z / div_flag", "Z40(k_net);adaptive_score>1∧z<−1", "爆量留上影線出貨型背離", "D"),
    ("五 籌碼流向與風格", "cash_foreign/sitc/dealer", "淨買賣股數×VWAP", "張數→絕對金額(跨股可比)", "F"),
    ("五 籌碼流向與風格", "f_ratio / capital_style", "EWM50(外資/Σ|三法人|);族群池 P65/P35", "Foreign/Domestic/Mixed", "D"),
    ("五 籌碼流向與風格", "s_share / sitc_dealer_style", "EWM50(|投信|/(|投信|+|自營|));P65/P35", "SITC_Dominant/Dealer_Dominant/Balanced", "D"),
    ("五 籌碼流向與風格", "foreign_pattern", "f_mom=EWM8−EWM50;f_pers=EWM12(買超日);f_align=EWM(f_ewm×ret)", "Trend_Following/Contrarian/Sudden_Withdrawal/Neutral", "D"),
    ("五 籌碼流向與風格", "cash_residual", "max(0, etr−|法人現金|−|融資現金|)", "隱形大戶/散戶留倉殘差", "F"),
    ("六 信用交易與當沖", "smr / smr_shock", "券/資×100;Z20", "券資比軋空能量", "D"),
    ("六 信用交易與當沖", "margin_mom_z", "Z20(Δ融資餘額)", "槓桿進場力道", "D"),
    ("六 信用交易與當沖", "squeeze_regime / margin_health", "規制標籤", "Squeeze_Prime/Short_Overhang;Retail_Trapped/Margin_Washout/Healthy", "H"),
    ("七 綜合評分與角色", "leader_score", "w13×領先分+(1−w13)×聚焦分(族群內百分位)", "領先分=pct(rel20,rel60,正報酬日率,rs_mom)均;聚焦分=pct(as,adaptive,etr20med)均", "H"),
    ("七 綜合評分與角色", "role", "雙重條件+2D 覆蓋", "LEADER/PEER/LAGGER/UNRELATED/FAKE_PULL/WASHOUT/RANK_ONLY", "H"),
    ("七 綜合評分與角色", "valid_member", "EWM3(pass_liq∧pass_pcorr∧¬div) ≥0.7 入/≤0.3 出/中間維持", "雙閾值真遲滯防震盪(C-19;冷氣機律)", "F"),
    ("七 綜合評分與角色", "downgrade_c15", "AS 族群排名掉出前 30% 連 C-15 日", "LEADER 降級律", "D"),
    ("八 族群健康與指數資格", "pc1_absorption", "λ1/trace(60 日報酬共變異;冪迭代)", "同一因子驅動度", "監控"),
    ("八 族群健康與指數資格", "index_grade", "≥C-01 探索 / ≥C-01b 指數級 / <C-16∨n<5 剔除", "探索用與指數用門檻分開", "F"),
    ("九 訊號", "Signal_Strong_Leader", "LEADER∧rs_mom>0∧adaptive_score>1.5∧外資≠撤退", "右側主升段", "策略"),
    ("九 訊號", "Signal_Washout_Buy", "WASHOUT∧k_net_cash_z>1.5∧price_rs>1", "左側洗盤換手吃貨", "策略"),
    ("九 訊號", "Signal_SITC_Ignition", "SITC_Dominant∧pass_vcorr∧rs_mom>0", "投信鎖碼啟動", "策略"),
    ("九 訊號", "Avoid_FAKE_PULL / Avoid_div", "FAKE_PULL;div_flag", "假突破/爆量出貨迴避", "策略"),
]


# ─────────────────────────── 數值工具(標準庫) ───────────────────────────

def ewm(xs: list, span: int) -> list:
    """adjust=True 指數加權均;None 跳過(承前值)。"""
    a = 2.0 / (span + 1.0)
    num = den = 0.0
    out, last = [], None
    for x in xs:
        if x is None:
            out.append(last)
            continue
        num = x + (1 - a) * num
        den = 1 + (1 - a) * den
        last = num / den
        out.append(last)
    return out


def ewm_std(xs: list, span: int) -> list:
    m = ewm(xs, span)
    m2 = ewm([None if x is None else x * x for x in xs], span)
    return [None if (a is None or b is None) else math.sqrt(max(b - a * a, 0.0)) for a, b in zip(m, m2)]


def ewm_corr(xs: list, ys: list, span: int) -> list:
    pairs = [(x, y) if (x is not None and y is not None) else (None, None) for x, y in zip(xs, ys)]
    px = [p[0] for p in pairs]
    py = [p[1] for p in pairs]
    mx, my = ewm(px, span), ewm(py, span)
    mx2 = ewm([None if x is None else x * x for x in px], span)
    my2 = ewm([None if y is None else y * y for y in py], span)
    mxy = ewm([None if x is None else x * y for x, y in pairs], span)
    out = []
    for i in range(len(xs)):
        if None in (mx[i], my[i], mx2[i], my2[i], mxy[i]):
            out.append(None)
            continue
        vx, vy = max(mx2[i] - mx[i] ** 2, 1e-12), max(my2[i] - my[i] ** 2, 1e-12)
        out.append(max(-1.0, min(1.0, (mxy[i] - mx[i] * my[i]) / (math.sqrt(vx) * math.sqrt(vy) + 1e-12))))
    return out


def rolling_stat(xs: list, window: int, fn, min_obs: int = 8) -> list:
    out = []
    for i in range(len(xs)):
        w = [v for v in xs[max(0, i - window + 1):i + 1] if v is not None]
        out.append(fn(w) if len(w) >= min_obs else None)
    return out


def quantile(vals: list, q: float):
    xs = sorted(v for v in vals if v is not None)
    if not xs:
        return None
    pos = (len(xs) - 1) * q
    lo, hi = int(pos), min(int(pos) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def zscore_last(xs: list, window: int):
    w = [v for v in xs[-window:] if v is not None]
    if len(w) < 8:
        return None
    m = statistics.mean(w)
    sd = statistics.pstdev(w) or 1e-9
    return (w[-1] - m) / sd


def pct_rank(d: dict) -> dict:
    """橫截面百分位(0..1;同值取均);None 不入。"""
    items = [(k, v) for k, v in d.items() if v is not None]
    n = len(items)
    if n == 0:
        return {}
    if n == 1:
        return {items[0][0]: 1.0}
    srt = sorted(items, key=lambda kv: kv[1])
    out, i = {}, 0
    while i < n:
        j = i
        while j + 1 < n and srt[j + 1][1] == srt[i][1]:
            j += 1
        r = (i + j) / 2.0 / (n - 1)
        for k in range(i, j + 1):
            out[srt[k][0]] = r
        i = j + 1
    return out


def cap_weights(w: dict, cap: float) -> dict:
    """指數業界封頂法:超限者鎖 cap,餘額按比例分給未封頂者(迭代至收斂)。"""
    w = {k: v for k, v in w.items() if v is not None and v > 0}
    if not w:
        return {}
    tot = sum(w.values())
    w = {k: v / tot for k, v in w.items()}
    if len(w) * cap < 1.0:  # 數學上不可能全數 ≤cap ⇒ 等權退場(誠實)
        return {k: 1.0 / len(w) for k in w}
    for _ in range(50):
        over = {k for k, v in w.items() if v > cap + 1e-12}
        if not over:
            break
        excess = sum(w[k] - cap for k in over)
        for k in over:
            w[k] = cap
        free = [k for k in w if k not in over]
        fs = sum(w[k] for k in free)
        for k in free:
            w[k] += excess * (w[k] / fs) if fs > 0 else excess / len(free)
    return w


def hysteresis(smooth: list, enter: float = 0.7, exit_: float = 0.3) -> list:
    """雙閾值真遲滯(冷氣機律):≥enter 入選、≤exit 剔除、中間維持原態;None 承前。
    帶寬律:span=3(α=.5)之 1/0 交替穩態為 1/(2−α)=.667 與 .333——帶須含此區
    方不擺盪;[.3,.7] 使單日閃斷保持、連兩日失格即剔(敏感不鈍)。"""
    out, state = [], False
    for v in smooth:
        if v is None:
            out.append(state if out else None)
            continue
        if v >= enter:
            state = True
        elif v <= exit_:
            state = False
        out.append(state)
    return out


def pc1_absorption(matrix: list) -> float | None:
    """matrix:list of rows(日)× cols(成員報酬);λ1/trace 冪迭代;n<20 或 cols<3 誠實 None。"""
    n = len(matrix)
    if n < 20 or not matrix or len(matrix[0]) < 3:
        return None
    m = len(matrix[0])
    means = [sum(row[j] for row in matrix) / n for j in range(m)]
    X = [[row[j] - means[j] for j in range(m)] for row in matrix]
    cov = [[sum(X[t][i] * X[t][j] for t in range(n)) / (n - 1) for j in range(m)] for i in range(m)]
    trace = sum(cov[i][i] for i in range(m))
    if trace <= 0:
        return None
    v = [1.0 / math.sqrt(m)] * m
    lam = 0.0
    for _ in range(300):
        nv = [sum(cov[i][j] * v[j] for j in range(m)) for i in range(m)]
        norm = math.sqrt(sum(x * x for x in nv)) or 1e-12
        nv = [x / norm for x in nv]
        lam_new = sum(nv[i] * sum(cov[i][j] * nv[j] for j in range(m)) for i in range(m))
        if abs(lam_new - lam) < 1e-10:
            lam = lam_new
            v = nv
            break
        lam, v = lam_new, nv
    return max(0.0, min(1.0, lam / trace))


def _f(x):
    try:
        return None if x is None else float(x)
    except (TypeError, ValueError):
        return None


# ─────────────────────────── 引擎本體 ───────────────────────────

class APCE:
    def __init__(self, params: dict | None = None):
        self.p = dict(BASE)
        if params:
            self.p.update(params)
        self.params_used = {}
        self.coverage = {}

    # ---- 參數解析(家族優先) ----
    def resolve_params(self, histories: dict | None = None, state: dict | None = None):
        fam = _family()
        if fam is None:
            self.params_used = {k: {"value": v, "mode": "BASE"} for k, v in self.p.items() if k.startswith("C-")}
            return
        try:
            ssot = fam.load_ssot()
            for cid in ("C-01", "C-01b", "C-05", "C-06", "C-13", "C-15", "C-16", "C-17", "C-18", "C-19", "C-21"):
                r = fam.resolve(cid, (histories or {}).get(cid), state or {}, {}, ssot)
                if r.get("value") is not None:
                    self.p[cid] = r["value"]
                self.params_used[cid] = {"value": r.get("value"), "mode": r.get("mode"), "why": r.get("why")}
        except Exception as exc:  # 冊缺/損=基值(誠實記)
            self.params_used = {"_note": f"家族解析未成({type(exc).__name__})——基值"}

    # ---- 面板整理 ----
    def _build(self, rows: list) -> tuple[dict, list]:
        S = {}
        for r in rows:
            t = str(r.get("ticker", "")).strip()
            d = str(r.get("date", "")).strip()
            if not t or not d:
                continue
            s = S.setdefault(t, {"sector": r.get("sector") or "—", "market": r.get("market") or "—",
                                 "rows": {}})
            s["rows"][d] = r
        dates = sorted({d for s in S.values() for d in s["rows"]})
        cols = ["open", "high", "low", "close", "adj_close", "volume", "turnover", "dt_turnover", "shares",
                "f_net", "s_net", "d_net", "margin_long", "margin_short", "margin_long_diff"]
        cov = {c: 0 for c in cols}
        n = 0
        for s in S.values():
            s["dates"] = sorted(s["rows"])
            for c in cols:
                s[c] = [_f(s["rows"][d].get(c)) for d in s["dates"]]
                cov[c] += sum(1 for v in s[c] if v is not None)
            n += len(s["dates"])
        self.coverage = {c: round(cov[c] / n, 3) if n else 0.0 for c in cols}
        return S, dates

    # ---- 主流程 ----
    def run(self, rows: list, base_date: str = "2026-01-01") -> dict:
        S, dates = self._build(rows)
        p = self.p
        cap = float(p["C-17"])
        span, W = int(p["ewm_span"]), int(p["quant_window"])
        # 1 釘卯:etr / mfm / k_net
        for t, s in S.items():
            s["is_tsmc"] = (t == TSMC)
            s["etr"], s["etr_basis"], s["mfm"], s["k_net"] = [], [], [], []
            for i in range(len(s["dates"])):
                tv, dt = s["turnover"][i], s["dt_turnover"][i]
                if tv is None:
                    etr = None
                    basis = "NA"
                elif dt is None:
                    etr, basis = tv, "NO_DT"
                else:
                    etr, basis = max(0.0, tv - dt), "ETR"
                s["etr"].append(etr)
                s["etr_basis"].append(basis)
                h, l, c = s["high"][i], s["low"][i], s["close"][i]
                mfm = None
                if None not in (h, l, c) and h > l:
                    mfm = max(-1.0, min(1.0, ((c - l) - (h - c)) / (h - l)))
                s["mfm"].append(mfm)
                s["k_net"].append(None if (mfm is None or etr is None) else mfm * etr)
            px = s["adj_close"] if any(v is not None for v in s["adj_close"]) else s["close"]
            s["ret"] = [None] + [(px[i] / px[i - 1] - 1) if (px[i] and px[i - 1]) else None
                                 for i in range(1, len(px))]
            s["etr_pct"] = [None] + [max(-1.0, min(1.0, s["etr"][i] / s["etr"][i - 1] - 1))
                                     if (s["etr"][i] is not None and s["etr"][i - 1]) else None
                                     for i in range(1, len(s["etr"]))]
        # A 橫截面:clean_mkt / as / 分層
        di = {d: {} for d in dates}
        for t, s in S.items():
            for i, d in enumerate(s["dates"]):
                di[d][t] = i
        clean_mkt = {}
        for d in dates:
            clean_mkt[d] = sum(S[t]["etr"][i] for t, i in di[d].items()
                               if not S[t]["is_tsmc"] and S[t]["etr"][i] is not None)
        cm_series = [clean_mkt[d] for d in dates]
        cm_med = rolling_stat(cm_series, 20, statistics.median, 8)
        cm_conf = {}
        for k, d in enumerate(dates):
            w = [v for v in cm_series[max(0, k - 19):k + 1] if v is not None]
            if len(w) >= 8:
                med = statistics.median(w)
                mad = statistics.median(abs(v - med) for v in w) * 1.4826 or 1e-9
                cm_conf[d] = "LOW" if abs(cm_series[k] - med) / mad > float(p["C-21"]) else "OK"
            else:
                cm_conf[d] = "NA"
        for t, s in S.items():
            s["as"] = [None if (s["etr"][i] is None or s["is_tsmc"] or clean_mkt[d] <= 0)
                       else s["etr"][i] / clean_mkt[d] for i, d in enumerate(s["dates"])]
            s["cap"] = [None if (s["shares"][i] is None or s["close"][i] is None)
                        else s["shares"][i] * s["close"][i] for i in range(len(s["dates"]))]
            s["cap20"] = rolling_stat(s["cap"], 20, statistics.median, 15)
        have_cap = sum(1 for s in S.values() if any(v is not None for v in s["cap20"]))
        tier_basis = "MCAP_20D_MEDIAN(P80/P40)" if have_cap >= 0.6 * max(1, len(S)) else "AS(P90/P60)"
        for d in dates:
            key = "cap20" if tier_basis.startswith("MCAP") else "as"
            vals = {t: S[t][key][i] for t, i in di[d].items() if not S[t]["is_tsmc"]}
            pr = pct_rank(vals)
            hi, mid = (0.80, 0.40) if key == "cap20" else (0.90, 0.60)
            for t, i in di[d].items():
                s = S[t]
                s.setdefault("size_tier", [None] * len(s["dates"]))
                r = pr.get(t)
                s["size_tier"][i] = None if r is None else ("Large" if r >= hi else "Mid" if r >= mid else "Small")
        # I 三加權指數(T-1 權重;鏈結)
        sectors = sorted({s["sector"] for s in S.values() if not s["is_tsmc"]})
        tw = p["tier_weights"]
        weights = {}  # (sector,date) -> {ticker:{eq,tier,att}}
        for d in dates:
            for sec in sectors:
                mem = [t for t, i in di[d].items() if S[t]["sector"] == sec and not S[t]["is_tsmc"]
                       and S[t]["as"][i] is not None]
                if not mem:
                    continue
                w_eq = {t: 1.0 / len(mem) for t in mem}
                raw_t = {t: tw.get(S[t]["size_tier"][di[d][t]] or "Small", 0.2) for t in mem}
                st = sum(raw_t.values())
                w_tier = {t: v / st for t, v in raw_t.items()}
                w_att = cap_weights({t: S[t]["as"][di[d][t]] for t in mem}, cap)
                weights[(sec, d)] = {t: {"eq": w_eq[t], "tier": w_tier[t], "att": w_att.get(t, 0.0)} for t in mem}
        indices = {sec: {} for sec in sectors}
        levels = {sec: {"eq": 100.0, "tier": 100.0, "att": 100.0} for sec in sectors}
        prev_d = {sec: None for sec in sectors}
        for d in dates:
            for sec in sectors:
                pd_ = prev_d[sec]
                rec = {"n": 0, "max_w_att": None, "hhi_att": None}
                if pd_ is not None and (sec, pd_) in weights:
                    wprev = weights[(sec, pd_)]
                    mem = [t for t in wprev if t in di[d] and S[t]["ret"][di[d][t]] is not None]
                    if mem:
                        for k in ("eq", "tier", "att"):
                            sw = sum(wprev[t][k] for t in mem)
                            g = sum(wprev[t][k] * S[t]["ret"][di[d][t]] for t in mem) / sw if sw > 0 else 0.0
                            levels[sec][k] *= (1 + g)
                            rec["ret_" + k] = g
                        rec["n"] = len(mem)
                        watt = [wprev[t]["att"] for t in mem]
                        rec["max_w_att"] = max(watt)
                        rec["hhi_att"] = sum(w * w for w in watt)
                if (sec, d) in weights:
                    prev_d[sec] = d
                    rec["n"] = rec["n"] or len(weights[(sec, d)])
                rec.update({k: levels[sec][k] for k in ("eq", "tier", "att")})
                indices[sec][d] = rec
        # 基準日重定 100
        for sec in sectors:
            bd = base_date if base_date in indices[sec] else next((d for d in dates if d >= base_date), None)
            if bd and bd in indices[sec]:
                bvals = {k: indices[sec][bd][k] for k in ("eq", "tier", "att")}
                for d in indices[sec]:
                    for k in ("eq", "tier", "att"):
                        indices[sec][d][k] = round(indices[sec][d][k] / bvals[k] * 100, 4) if bvals[k] else None
                indices[sec]["_base"] = bd
        # RS
        for t, s in S.items():
            cum, lvl = [], 100.0
            for r in s["ret"]:
                if r is not None:
                    lvl *= (1 + r)
                cum.append(lvl)
            bd = indices.get(s["sector"], {}).get("_base") if not s["is_tsmc"] else None
            if bd and bd in s["rows"]:
                bi = s["dates"].index(bd)
                cum = [c / cum[bi] * 100 for c in cum]
            s["idx_stock"] = cum
            s["price_rs"] = [None if (s["is_tsmc"] or indices[s["sector"]].get(d, {}).get("att") in (None, 0))
                             else s["idx_stock"][i] / indices[s["sector"]][d]["att"]
                             for i, d in enumerate(s["dates"])]
            e40 = ewm(s["price_rs"], 40)
            s["rs_mom"] = [None if (a is None or b is None) else a - b for a, b in zip(s["price_rs"], e40)]
        # 2 動能
        for t, s in S.items():
            es, el, esd = ewm(s["etr"], 5), ewm(s["etr"], 40), ewm_std(s["etr"], 40)
            s["vol_shock"], s["adaptive_score"] = [], []
            for i in range(len(s["dates"])):
                if None in (es[i], el[i], esd[i]) or s["etr"][i] is None:
                    s["vol_shock"].append(None)
                    s["adaptive_score"].append(None)
                    continue
                vs = (es[i] - el[i]) / (esd[i] + 1e-8)
                base = 0.75 * es[i] + 0.25 * el[i] if vs > 2.0 else el[i]
                s["vol_shock"].append(vs)
                s["adaptive_score"].append((s["etr"][i] - base) / (esd[i] + 1e-8))
            kz = ewm(s["k_net"], 40)
            ksd = ewm_std(s["k_net"], 40)
            s["k_net_z"] = [None if None in (s["k_net"][i], kz[i], ksd[i]) else (s["k_net"][i] - kz[i]) / (ksd[i] + 1e-8)
                            for i in range(len(s["dates"]))]
        for d in dates:
            vals = [S[t]["etr"][i] for t, i in di[d].items() if not S[t]["is_tsmc"] and S[t]["etr"][i] is not None]
            if len(vals) >= 3:
                m, sd = statistics.mean(vals), statistics.pstdev(vals) or 1e-9
            for t, i in di[d].items():
                s = S[t]
                s.setdefault("cs_z", [None] * len(s["dates"]))
                s.setdefault("gravity_shock", [None] * len(s["dates"]))
                if len(vals) >= 3 and s["etr"][i] is not None and not s["is_tsmc"]:
                    s["cs_z"][i] = (s["etr"][i] - m) / sd
                    if s["vol_shock"][i] is not None and s["as"][i] is not None:
                        s["gravity_shock"][i] = s["vol_shock"][i] * math.sqrt(max(s["as"][i], 0.0))
        # 3/4 同動+閘門
        gmed = {}
        for d in dates:
            for sec in sectors:
                mem = [t for t, i in di[d].items() if S[t]["sector"] == sec and not S[t]["is_tsmc"]]
                rets = [S[t]["ret"][di[d][t]] for t in mem if S[t]["ret"][di[d][t]] is not None]
                eps = [S[t]["etr_pct"][di[d][t]] for t in mem if S[t]["etr_pct"][di[d][t]] is not None]
                gmed[(sec, d)] = (statistics.median(rets) if rets else None,
                                  statistics.median(eps) if eps else None)
        for t, s in S.items():
            gr = [gmed.get((s["sector"], d), (None, None))[0] for d in s["dates"]]
            ge = [gmed.get((s["sector"], d), (None, None))[1] for d in s["dates"]]
            s["price_corr"] = ewm_corr(s["ret"], gr, span)
            s["vol_corr"] = ewm_corr(s["etr_pct"], ge, span)
        # 族群池滾動門檻(P45 corr、P25 etr)
        thr = {}
        for sec in sectors:
            mem_all = [t for t in S if S[t]["sector"] == sec and not S[t]["is_tsmc"]]
            for k, d in enumerate(dates):
                win = dates[max(0, k - W + 1):k + 1]
                pc, vc, et = [], [], []
                for t in mem_all:
                    for dd in win:
                        i = di[dd].get(t)
                        if i is None:
                            continue
                        pc.append(S[t]["price_corr"][i])
                        vc.append(S[t]["vol_corr"][i])
                        et.append(S[t]["etr"][i])
                thr[(sec, d)] = (quantile(pc, p["corr_q"]), quantile(vc, p["corr_q"]), quantile(et, p["liquidity_q"]))
        for t, s in S.items():
            s["pass_liq"], s["pass_pcorr"], s["pass_vcorr"], s["div_flag"], s["p_th"], s["v_th"] = [], [], [], [], [], []
            for i, d in enumerate(s["dates"]):
                pth, vth, lf = thr.get((s["sector"], d), (None, None, None))
                s["p_th"].append(pth)
                s["v_th"].append(vth)
                s["pass_liq"].append(None if (lf is None or s["etr"][i] is None) else s["etr"][i] >= lf)
                s["pass_pcorr"].append(None if (pth is None or s["price_corr"][i] is None) else s["price_corr"][i] >= pth)
                s["pass_vcorr"].append(None if (vth is None or s["vol_corr"][i] is None) else s["vol_corr"][i] >= vth)
                a, kz_ = s["adaptive_score"][i], s["k_net_z"][i]
                s["div_flag"].append(None if (a is None or kz_ is None) else (a > 1.0 and kz_ < -1.0))
        # C/D/E 籌碼(欄在才算)
        has_inst = self.coverage.get("f_net", 0) > 0.2
        for t, s in S.items():
            if not has_inst or all(v is None for v in s["f_net"]):
                s["f_ratio"] = s["s_share"] = [None] * len(s["dates"])
                s["capital_style"] = s["sitc_dealer_style"] = s["foreign_pattern"] = [None] * len(s["dates"])
                s["f_pattern_note"] = "法人欄缺(誠實 SKIP)"
                continue
            vwap = [((s["open"][i] or 0) + (s["high"][i] or 0) + (s["low"][i] or 0) + (s["close"][i] or 0)) / 4
                    if None not in (s["open"][i], s["high"][i], s["low"][i], s["close"][i]) else s["close"][i]
                    for i in range(len(s["dates"]))]
            cf = [None if (s["f_net"][i] is None or vwap[i] is None) else s["f_net"][i] * vwap[i] for i in range(len(s["dates"]))]
            cs_ = [None if (s["s_net"][i] is None or vwap[i] is None) else s["s_net"][i] * vwap[i] for i in range(len(s["dates"]))]
            cd = [None if (s["d_net"][i] is None or vwap[i] is None) else s["d_net"][i] * vwap[i] for i in range(len(s["dates"]))]
            s["cash_foreign"], s["cash_sitc"], s["cash_dealer"] = cf, cs_, cd
            f_raw = [None if None in (cf[i], cs_[i], cd[i]) else cf[i] / (abs(cf[i]) + abs(cs_[i]) + abs(cd[i]) + 1e-8)
                     for i in range(len(s["dates"]))]
            s_raw = [None if None in (cs_[i], cd[i]) else abs(cs_[i]) / (abs(cs_[i]) + abs(cd[i]) + 1e-8)
                     for i in range(len(s["dates"]))]
            s["f_ratio"], s["s_share"] = ewm(f_raw, span), ewm(s_raw, span)
            fh = rolling_stat(s["f_ratio"], W, lambda w: quantile(w, 0.65))
            fl = rolling_stat(s["f_ratio"], W, lambda w: quantile(w, 0.35))
            sh = rolling_stat(s["s_share"], W, lambda w: quantile(w, 0.65))
            sl = rolling_stat(s["s_share"], W, lambda w: quantile(w, 0.35))
            s["capital_style"] = [None if None in (s["f_ratio"][i], fh[i], fl[i]) else
                                  ("Foreign" if s["f_ratio"][i] >= fh[i] else "Domestic" if s["f_ratio"][i] <= fl[i] else "Mixed")
                                  for i in range(len(s["dates"]))]
            s["sitc_dealer_style"] = [None if None in (s["s_share"][i], sh[i], sl[i]) else
                                      ("SITC_Dominant" if s["s_share"][i] >= sh[i] else "Dealer_Dominant" if s["s_share"][i] <= sl[i] else "Balanced")
                                      for i in range(len(s["dates"]))]
            f_ewm, f_short = ewm(s["f_net"], span), ewm(s["f_net"], 8)
            f_buy = [None if v is None else (1.0 if v > 0 else 0.0) for v in s["f_net"]]
            f_pers = ewm(f_buy, 12)
            f_align = ewm([None if (f_ewm[i] is None or s["ret"][i] is None) else f_ewm[i] * s["ret"][i]
                           for i in range(len(s["dates"]))], span)
            s["foreign_pattern"] = []
            for i in range(len(s["dates"])):
                if None in (f_ewm[i], f_short[i], f_pers[i], f_align[i]):
                    s["foreign_pattern"].append(None)
                    continue
                fm = f_short[i] - f_ewm[i]
                if fm > 0 and f_pers[i] > 0.55 and f_align[i] > 0:
                    s["foreign_pattern"].append("Trend_Following")
                elif fm > 0 and f_align[i] < 0:
                    s["foreign_pattern"].append("Contrarian")
                elif fm < 0 and f_pers[i] < 0.3:
                    s["foreign_pattern"].append("Sudden_Withdrawal")
                else:
                    s["foreign_pattern"].append("Neutral")
        # M 信用當沖(欄在才算)
        for t, s in S.items():
            n = len(s["dates"])
            s["smr"] = [None if (s["margin_long"][i] in (None, 0) or s["margin_short"][i] is None)
                        else s["margin_short"][i] / s["margin_long"][i] * 100 for i in range(n)]
            sm, ssd = ewm(s["smr"], 20), ewm_std(s["smr"], 20)
            s["smr_shock"] = [None if None in (s["smr"][i], sm[i], ssd[i]) else (s["smr"][i] - sm[i]) / (ssd[i] + 1e-8) for i in range(n)]
            s["dtr"] = [None if (s["turnover"][i] in (None, 0) or s["dt_turnover"][i] is None)
                        else s["dt_turnover"][i] / s["turnover"][i] for i in range(n)]
            s["squeeze_regime"] = [None if s["smr"][i] is None else
                                   ("Squeeze_Prime" if (s["smr"][i] >= 35 and (s["smr_shock"][i] or 0) > 1.2 and (s["rs_mom"][i] or 0) > 0)
                                    else "Short_Overhang" if (s["smr"][i] >= 35 and (s["rs_mom"][i] or 0) < 0) else "Normal_Leverage")
                                   for i in range(n)]
        # B 角色(複合分族群內百分位;雙重條件;2D 覆蓋;C-15 降級;H 遲滯)
        w13 = float(p["C-13"])
        for t, s in S.items():
            n = len(s["dates"])
            s["ret20"] = [None] * n
            s["ret60"] = [None] * n
            s["pos20"] = [None] * n
            s["etr20"] = rolling_stat(s["etr"], 20, statistics.median, 10)
            for i in range(n):
                if i >= 20 and s["idx_stock"][i - 20]:
                    s["ret20"][i] = s["idx_stock"][i] / s["idx_stock"][i - 20] - 1
                    w = [r for r in s["ret"][i - 19:i + 1] if r is not None]
                    s["pos20"][i] = sum(1 for r in w if r > 0) / len(w) if w else None
                if i >= 60 and s["idx_stock"][i - 60]:
                    s["ret60"][i] = s["idx_stock"][i] / s["idx_stock"][i - 60] - 1
        score_hist = {sec: [] for sec in sectors}
        for d in dates:
            for sec in sectors:
                mem = [t for t, i in di[d].items() if S[t]["sector"] == sec and not S[t]["is_tsmc"]]
                if not mem:
                    continue
                gm20 = statistics.median([S[t]["ret20"][di[d][t]] for t in mem if S[t]["ret20"][di[d][t]] is not None] or [0.0])
                gm60 = statistics.median([S[t]["ret60"][di[d][t]] for t in mem if S[t]["ret60"][di[d][t]] is not None] or [0.0])
                comp = {
                    "rel20": pct_rank({t: None if S[t]["ret20"][di[d][t]] is None else S[t]["ret20"][di[d][t]] - gm20 for t in mem}),
                    "rel60": pct_rank({t: None if S[t]["ret60"][di[d][t]] is None else S[t]["ret60"][di[d][t]] - gm60 for t in mem}),
                    "pos20": pct_rank({t: S[t]["pos20"][di[d][t]] for t in mem}),
                    "rsm": pct_rank({t: S[t]["rs_mom"][di[d][t]] for t in mem}),
                    "as": pct_rank({t: S[t]["as"][di[d][t]] for t in mem}),
                    "ada": pct_rank({t: S[t]["adaptive_score"][di[d][t]] for t in mem}),
                    "e20": pct_rank({t: S[t]["etr20"][di[d][t]] for t in mem}),
                }
                scores = {}
                for t in mem:
                    lead = [comp[k][t] for k in ("rel20", "rel60", "pos20", "rsm") if t in comp[k]]
                    att = [comp[k][t] for k in ("as", "ada", "e20") if t in comp[k]]
                    if lead and att:
                        scores[t] = w13 * statistics.mean(lead) + (1 - w13) * statistics.mean(att)
                    else:
                        scores[t] = None
                spct = pct_rank(scores)
                as_pct = comp["as"]
                if scores:
                    q80 = quantile(list(scores.values()), 0.8)
                    if q80 is not None:
                        score_hist[sec].append(q80)
                for t in mem:
                    i = di[d][t]
                    s = S[t]
                    for k in ("leader_score", "score_pct", "as_pct", "role", "valid_raw"):
                        s.setdefault(k, [None] * len(s["dates"]))
                    s["leader_score"][i] = scores.get(t)
                    s["score_pct"][i] = spct.get(t)
                    s["as_pct"][i] = as_pct.get(t)
                    pc_, vc_ = s["price_corr"][i], s["vol_corr"][i]
                    floor = float(p["C-18"])
                    if len(mem) < 5:
                        role = "RANK_ONLY"
                    elif pc_ is None or vc_ is None or scores.get(t) is None:
                        role = None
                    elif pc_ < floor and vc_ < floor:
                        role = "UNRELATED"
                    elif s["p_th"][i] is not None and pc_ >= s["p_th"][i] and vc_ < 0:
                        role = "FAKE_PULL"
                    elif s["v_th"][i] is not None and vc_ >= s["v_th"][i] and pc_ < 0:
                        role = "WASHOUT"
                    elif (spct.get(t, 0) >= 0.80 and scores[t] >= float(p["C-05"]) and s["pass_pcorr"][i]
                          and (s["rs_mom"][i] or 0) > 0):
                        role = "LEADER"
                    elif scores[t] < float(p["C-06"]) or s["div_flag"][i]:
                        role = "LAGGER"
                    else:
                        role = "PEER"
                    s["role"][i] = role
                    pl_, pp_, dv_ = s["pass_liq"][i], s["pass_pcorr"][i], s["div_flag"][i]
                    s["valid_raw"][i] = None if None in (pl_, pp_, dv_) else (1.0 if (pl_ and pp_ and not dv_) else 0.0)
        # C-15 降級 + H 遲滯
        n15 = int(p["C-15"])
        for t, s in S.items():
            if "role" not in s:
                continue
            vs = ewm(s["valid_raw"], int(p["C-19"]))
            s["valid_member"] = hysteresis(vs, float(p.get("hys_enter", 0.6)), float(p.get("hys_exit", 0.4)))
            s["downgrade_c15"] = [False] * len(s["dates"])
            streak = 0
            for i in range(len(s["dates"])):
                ap = s["as_pct"][i]
                streak = streak + 1 if (ap is not None and ap < 0.70) else 0
                if s["role"][i] == "LEADER" and streak >= n15:
                    s["role"][i] = "PEER"
                    s["downgrade_c15"][i] = True
        # G 族群健康:PC1 吸收率(60 日)+ 指數資格
        health = {}
        for sec in sectors:
            mem = [t for t in S if S[t]["sector"] == sec and not S[t]["is_tsmc"]]
            win = dates[-60:]
            full = [t for t in mem if all(d in S[t]["rows"] and S[t]["ret"][di[d][t]] is not None for d in win)]
            mat = [[S[t]["ret"][di[d][t]] for t in full] for d in win] if len(full) >= 3 else []
            pc1 = pc1_absorption(mat) if mat else None
            last = indices[sec].get(dates[-1], {})
            n_eff = last.get("n", 0)
            if pc1 is None:
                grade = "INSUFFICIENT"
            elif n_eff < int(p["min_members_index"]) or pc1 < float(p["C-16"]):
                grade = "REMOVE"
            elif pc1 >= float(p["C-01b"]):
                grade = "INDEX_GRADE"
            elif pc1 >= float(p["C-01"]):
                grade = "EXPLORE_PASS"
            else:
                grade = "BELOW_EXPLORE"
            health[sec] = {"pc1_absorption": None if pc1 is None else round(pc1, 4), "n_pc1": len(full),
                           "n_members": n_eff, "index_grade": grade,
                           "hhi_att": last.get("hhi_att"), "max_w_att": last.get("max_w_att")}
        # 訊號(最新日)
        latest = []
        d_last = dates[-1]
        for t, s in S.items():
            if s["is_tsmc"] or d_last not in s["rows"]:
                continue
            i = di[d_last][t]
            g = lambda k: s.get(k, [None] * (i + 1))[i] if k in s else None
            row = {"ticker": t, "sector": s["sector"], "market": s["market"], "date": d_last,
                   "as": g("as"), "as_conf": cm_conf.get(d_last), "size_tier": g("size_tier"),
                   "etr": g("etr"), "etr_basis": g("etr_basis"), "price_rs": g("price_rs"), "rs_mom": g("rs_mom"),
                   "vol_shock": g("vol_shock"), "adaptive_score": g("adaptive_score"), "cs_z": g("cs_z"),
                   "gravity_shock": g("gravity_shock"), "price_corr": g("price_corr"), "vol_corr": g("vol_corr"),
                   "p_th": g("p_th"), "v_th": g("v_th"), "pass_liq": g("pass_liq"), "pass_pcorr": g("pass_pcorr"),
                   "pass_vcorr": g("pass_vcorr"), "k_net_z": g("k_net_z"), "div_flag": g("div_flag"),
                   "leader_score": g("leader_score"), "score_pct": g("score_pct"), "as_pct": g("as_pct"),
                   "role": g("role"), "valid_member": g("valid_member"), "downgrade_c15": g("downgrade_c15"),
                   "capital_style": g("capital_style"), "sitc_dealer_style": g("sitc_dealer_style"),
                   "foreign_pattern": g("foreign_pattern"), "smr": g("smr"), "squeeze_regime": g("squeeze_regime"),
                   "dtr": g("dtr")}
            for k, v in list(row.items()):
                if isinstance(v, float):
                    row[k] = round(v, 6)
            row["Signal_Strong_Leader"] = bool(row["role"] == "LEADER" and (row["rs_mom"] or 0) > 0
                                               and (row["adaptive_score"] or 0) > 1.5
                                               and row["foreign_pattern"] != "Sudden_Withdrawal")
            row["Signal_Washout_Buy"] = bool(row["role"] == "WASHOUT" and (row["k_net_z"] or 0) > 1.5
                                             and (row["price_rs"] or 0) > 1.0)
            row["Signal_SITC_Ignition"] = bool(row["sitc_dealer_style"] == "SITC_Dominant" and row["pass_vcorr"]
                                               and (row["rs_mom"] or 0) > 0)
            row["Avoid"] = "FAKE_PULL" if row["role"] == "FAKE_PULL" else ("DIVERGENCE" if row["div_flag"] else None)
            latest.append(row)
        roles = {}
        for r in latest:
            roles[str(r["role"])] = roles.get(str(r["role"]), 0) + 1
        return {"schema": "VIA.APCE.v1", "ts": NOW, "asof": d_last, "n_dates": len(dates), "n_tickers": len(S),
                "base_date": base_date, "tier_basis": tier_basis, "coverage": self.coverage,
                "params_used": self.params_used, "params": {k: v for k, v in p.items() if k != "tier_weights"},
                "role_counts": roles, "latest": latest, "indices": indices, "health": health,
                "clean_mkt_last": clean_mkt.get(d_last), "clean_mkt_conf_last": cm_conf.get(d_last),
                "catalog": [{"class": c, "var": v, "formula": f, "meaning": m, "ptype": t} for c, v, f, m, t in CATALOG]}


# ─────────────────────────── 合成面板(自檢用) ───────────────────────────

def synth_panel(n_days: int = 140, seed: int = 11) -> list:
    import random
    rng = random.Random(seed)
    dates = [f"2026-{1 + k // 28:02d}-{1 + k % 28:02d}" for k in range(n_days)]
    g = [rng.gauss(0, 0.012) for _ in range(n_days)]      # 族群共同因子
    h = [rng.gauss(0, 0.25) for _ in range(n_days)]       # 族群資金因子(Δetr%)
    rows = []

    def emit(t, sec, rets, etr_mult, etr_pct_series, base_turn, extra=None):
        px, turn = 100.0, base_turn
        for k in range(n_days):
            px *= (1 + rets[k])
            if k > 0:
                turn = max(base_turn * 0.2, turn * (1 + etr_pct_series[k]))
            hi, lo = px * (1 + abs(rng.gauss(0, 0.004))), px * (1 - abs(rng.gauss(0, 0.004)))
            r = {"date": dates[k], "ticker": t, "sector": sec, "market": "TWSE", "open": px, "high": hi,
                 "low": lo, "close": px, "adj_close": px, "volume": turn / px, "turnover": turn * etr_mult,
                 "dt_turnover": turn * etr_mult * 0.3, "shares": 1e8 * etr_mult}
            if extra:
                r.update(extra(k))
            rows.append(r)

    noise = lambda s: [rng.gauss(0, s) for _ in range(n_days)]
    # 領頭羊:共同因子+正漂移、資金最大且與群同動
    emit("L001", "T", [0.9 * g[k] + 0.0025 + rng.gauss(0, 0.004) for k in range(n_days)], 6.0, [0.9 * h[k] for k in range(n_days)], 1e9)
    for j in range(4):  # 一般同伴
        emit(f"P00{j}", "T", [0.8 * g[k] + rng.gauss(0, 0.006) for k in range(n_days)], 1.0 + 0.3 * j, [0.7 * h[k] + rng.gauss(0, 0.05) for k in range(n_days)], 5e8)
    # 假突破:價同動、量反向
    emit("F001", "T", [0.8 * g[k] + rng.gauss(0, 0.005) for k in range(n_days)], 1.2, [-0.9 * h[k] for k in range(n_days)], 5e8)
    # 洗盤:量同動、價反向
    emit("W001", "T", [-0.8 * g[k] + rng.gauss(0, 0.005) for k in range(n_days)], 1.1, [0.9 * h[k] for k in range(n_days)], 5e8)
    # 無關:價量皆獨立
    emit("U001", "T", noise(0.012), 1.0, noise(0.25), 5e8)
    # 獨立族群 U(各自隨機)
    for j in range(5):
        emit(f"N00{j}", "U", noise(0.012), 1.0, noise(0.25), 4e8)
    # 台積電巨錨(資金最大)
    emit(TSMC, "台積電獨立", [0.9 * g[k] + rng.gauss(0, 0.005) for k in range(n_days)], 40.0, [0.5 * h[k] for k in range(n_days)], 5e9)
    return rows


def selftest() -> int:
    ok, total = 0, 10
    rows = synth_panel()
    eng = APCE()
    eng.resolve_params()
    res = eng.run(rows, base_date="2026-02-01")
    lat = {r["ticker"]: r for r in res["latest"]}
    # ① 台積電隔離
    if TSMC not in lat and res["clean_mkt_last"] and res["clean_mkt_last"] < 5e9 * 40:
        ok += 1; print("  [PASS] 巨錨隔離(2330 不入分類、不入 clean_mkt)")
    else:
        print("  [FAIL] 隔離")
    # ② AS 橫截面總和=1
    s_as = sum(r["as"] for r in res["latest"] if r["as"] is not None)
    if abs(s_as - 1.0) < 1e-6:
        ok += 1; print("  [PASS] Attention Share Σ=1(排台積電後全市場)")
    else:
        print(f"  [FAIL] ΣAS={s_as}")
    # ③ 聚焦權重封頂 ≤C-17
    T = res["indices"]["T"]
    mx = max(v["max_w_att"] for d, v in T.items() if not d.startswith("_") and v.get("max_w_att") is not None)
    if mx <= 0.18 + 1e-9:
        ok += 1; print(f"  [PASS] 聚焦權重迭代封頂(max w_att {mx:.3f} ≤ 0.18)")
    else:
        print(f"  [FAIL] 封頂 {mx}")
    # ④ 基準日=100
    if abs(T["2026-02-01"]["eq"] - 100) < 1e-6 and abs(T["2026-02-01"]["att"] - 100) < 1e-6:
        ok += 1; print("  [PASS] 三加權指數基準日 2026-02-01=100")
    else:
        print("  [FAIL] 基準日")
    # ⑤ 鏈結法成分變動不跳點:移除 P003 後段,前段指數逐日不變
    rows2 = [r for r in rows if not (r["ticker"] == "P003" and r["date"] > "2026-03-14")]
    res2 = APCE().run(rows2, base_date="2026-02-01")
    T2 = res2["indices"]["T"]
    same = all(abs(T[d]["eq"] - T2[d]["eq"]) < 1e-9 for d in T if not d.startswith("_") and d <= "2026-03-14")
    cont = all(T2[d]["n"] >= 6 for d in T2 if not d.startswith("_") and d > "2026-03-15")
    if same and cont:
        ok += 1; print("  [PASS] 鏈結法:成分退出前段不變、後段以既有成員續鏈(不跳點)")
    else:
        print("  [FAIL] 鏈結")
    # ⑥ T-1 無前視:最新日權重=前一日 AS 封頂正規化(以 eq 檢核 n 一致)
    dl = res["asof"]
    prev = [d for d in T if not d.startswith("_") and d < dl][-1]
    if T[dl]["n"] == T[prev]["n"]:
        ok += 1; print("  [PASS] T-1 權重取用(當日指數以前一日成分權重計)")
    else:
        print("  [FAIL] T-1")
    # ⑦ PC1 吸收率:同動群高、獨立群低
    h = res["health"]
    if h["T"]["pc1_absorption"] and h["T"]["pc1_absorption"] > 0.5 and h["U"]["pc1_absorption"] and h["U"]["pc1_absorption"] < 0.5:
        ok += 1; print(f"  [PASS] PC1 吸收率(同動群 {h['T']['pc1_absorption']} vs 獨立群 {h['U']['pc1_absorption']})+分級 {h['T']['index_grade']}/{h['U']['index_grade']}")
    else:
        print(f"  [FAIL] PC1:{h}")
    # ⑧ 2D 角色:FAKE_PULL / WASHOUT / UNRELATED / LEADER
    got = {k: lat[k]["role"] for k in ("L001", "F001", "W001", "U001")}
    if got == {"L001": "LEADER", "F001": "FAKE_PULL", "W001": "WASHOUT", "U001": "UNRELATED"}:
        ok += 1; print("  [PASS] 2D 角色裁決(LEADER/FAKE_PULL/WASHOUT/UNRELATED 各中)")
    else:
        print(f"  [FAIL] 角色:{got} corr L={lat['L001']['price_corr']:.2f}/{lat['L001']['vol_corr']:.2f} F={lat['F001']['price_corr']:.2f}/{lat['F001']['vol_corr']:.2f} W={lat['W001']['price_corr']:.2f}/{lat['W001']['vol_corr']:.2f} U={lat['U001']['price_corr']:.2f}/{lat['U001']['vol_corr']:.2f} score_L={lat['L001']['leader_score']}")
    # ⑨ 真遲滯:單日閃斷不失格;持續失格才剔除;1/0 交替不擺盪
    h1 = hysteresis(ewm([1.0] * 10 + [0.0] + [1.0] * 5, 3))
    h2 = hysteresis(ewm([1.0] * 10 + [0.0] * 6, 3))
    h3 = hysteresis(ewm([1.0] * 10 + [1.0, 0.0] * 6, 3))
    if all(h1[10:]) and h2[-1] is False and any(h2[10:12]) and len(set(h3[10:])) == 1:
        ok += 1; print("  [PASS] 雙閾值真遲滯(單日閃斷不失格;連續失格才剔;交替不擺盪)")
    else:
        print(f"  [FAIL] 遲滯:{h1[10:]}/{h2[10:]}/{h3[10:]}")
    # ⑩ 指標庫 registry 涵蓋輸出欄
    keys = set(res["latest"][0].keys()) | set(res["health"]["T"].keys()) | {"idx_eq", "w_eq", "n_members", "clean_mkt"}
    missing = [c["var"] for c in res["catalog"] if not any(tok.strip() in keys or tok.strip().split("_")[0] in keys
                                                             for tok in c["var"].replace("/", " ").split())]
    if len(missing) <= 6:
        ok += 1; print(f"  [PASS] 指標庫 registry 對映輸出({len(res['catalog'])} 項;未直出 {len(missing)} 項屬派生)")
    else:
        print(f"  [FAIL] 目錄未對映:{missing}")
    print(f"  [計] {ok}/{total} 檢通過 · 參數模式 {sorted({v.get('mode') for v in res['params_used'].values() if isinstance(v, dict)})}")
    return 0 if ok == total else 1


def cmd_run(path: str, base: str) -> int:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(rows, dict):
        rows = rows.get("rows", [])
    eng = APCE()
    eng.resolve_params()
    res = eng.run(rows, base_date=base)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "apce_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [APCE] {res['asof']} · {res['n_tickers']} 檔 · {res['n_dates']} 日 · 角色 {res['role_counts']}")
    print(f"  [覆蓋] {res['coverage']} · 分層制 {res['tier_basis']}")
    for sec, hh in sorted(res["health"].items(), key=lambda kv: -(kv[1]['pc1_absorption'] or 0)):
        last = res["indices"][sec]
        dl = res["asof"]
        v = last.get(dl, {})
        print(f"    {sec:<10} PC1={hh['pc1_absorption']} n={hh['n_members']} {hh['index_grade']:<13} idx eq/tier/att={v.get('eq')}/{v.get('tier')}/{v.get('att')}")
    print(f"  [出] {OUT_DIR / 'apce_latest.json'}")
    return 0


def main() -> int:
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if a[0] == "--selftest":
        return selftest()
    if a[0] == "--run" and len(a) > 1:
        base = a[a.index("--base") + 1] if "--base" in a else "2026-01-01"
        return cmd_run(a[1], base)
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
