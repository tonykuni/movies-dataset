# v0100 (2026-08-10) NEW PARALLEL ENGINE LANE — 操作員令:IMPLEMENT SEABORN PLOTLY(28 圖型全譜)。
#   本檔為「seaborn/matplotlib(靜態 PNG)+ plotly(互動 HTML)」新引擎線,與零依賴 SVG 線
#   (canonical via_autoplot_engine_v001.py 與 chartlib_v002…v007)平行共存 — 全線零觸碰。
#   Do not edit in place - version forward instead.
# 治理:
#   ①SSOT 唯一真相:所有樣式數值一律讀 spec/ssot/vap_spec.json + vap_chartlib.json;
#     引擎源碼禁止寫死鎖定值(fill/gap/寬度/透明度),selftest 內建 visual-lock 自掃描
#     (v0111 系列 0.40→0.75 修復案的制度化預防)。
#   ②依賴誠實:seaborn/plotly 各自獨立探測;缺席=誠實 SKIP/FAIL + 一行安裝指令;
#     probe/list/spec 三動詞零第三方依賴可跑。
#   ③在地離線:plotly HTML 預設內嵌 plotly.js(單檔自足);demo/selftest 用 directory
#     模式(共用一份 plotly.min.js)以節省磁碟。零雲端、零 CDN 依賴。
#   ④VAP-CH-16(地圖)僅 plotly 後端(內建世界底圖);seaborn 後端誠實 UNSUPPORTED。
#   ⑤色彩治理:via combo 為 SSOT 視覺鎖定(locked)不可改;dataviz 驗證器 20260810 複測
#     與 chartlib_v003 紀錄一致(#4c78a8↔#7a6daa deutan ΔE 1.3 · normal 6.5 低於門檻)→
#     沿用其次要編碼鐵律:圖例常在、雙軸圖兩序列必用不同圖形、第二序列虛線、
#     堆疊段間紙面縫、語意色(漲紅跌綠)獨立於分類色序。
# -*- coding: utf-8 -*-
"""VIA · VeritasAutoPlot seaborn+plotly 引擎 v0100 — VAP-CH-01…28 全譜雙後端實作.

USAGE
  python via_autoplot_seaborn_plotly_v0100.py probe                     # 後端/SSOT 在位探測
  python via_autoplot_seaborn_plotly_v0100.py list                      # 28 圖型清單
  python via_autoplot_seaborn_plotly_v0100.py spec                      # 已解析樣式規格
  python via_autoplot_seaborn_plotly_v0100.py render --chart line --backend both --out out/
  python via_autoplot_seaborn_plotly_v0100.py render --chart VAP-CH-14 --backend plotly --out out/
  python via_autoplot_seaborn_plotly_v0100.py demo --out vap_demo/      # 28 型全渲染 + index.html
  python via_autoplot_seaborn_plotly_v0100.py selftest                  # 全譜自我驗證

資料輸入:--data data.json(欄位依 chartlib dataShape;未給即用內建確定性示範資料)。
"""
from __future__ import annotations

__version__ = "0100"

import argparse
import json
import math
import random
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

ENGINE_DIR = Path(__file__).resolve().parent


class VAPError(RuntimeError):
    """誠實 FAIL 基類。"""


class VAPUnsupported(VAPError):
    """該後端誠實不支援此圖型(非錯誤 — selftest 記 SKIP)。"""


# ============================================================================
# §1 SSOT 載入 — vap_spec.json + vap_chartlib.json(唯一真相,缺鍵誠實 FAIL)
# ============================================================================

def find_ssot_dir(override: Optional[str] = None) -> Path:
    if override:
        p = Path(override)
        if (p / "vap_spec.json").exists():
            return p
        raise VAPError("--ssot 指定目錄缺 vap_spec.json:%s" % p)
    for base in [ENGINE_DIR, *ENGINE_DIR.parents]:
        cand = base / "spec" / "ssot"
        if (cand / "vap_spec.json").exists():
            return cand
    raise VAPError("找不到 spec/ssot/vap_spec.json(自 %s 向上搜尋)— 可用 --ssot 指定" % ENGINE_DIR)


class Spec:
    """SSOT 讀取器:get('a.b.c') 缺鍵誠實 FAIL;鎖定值一律由此取得。"""

    def __init__(self, ssot_dir: Path):
        self.dir = ssot_dir
        self.spec = json.loads((ssot_dir / "vap_spec.json").read_text(encoding="utf-8"))
        self.chartlib = json.loads((ssot_dir / "vap_chartlib.json").read_text(encoding="utf-8"))

    def get(self, path: str, default: Any = KeyError) -> Any:
        node: Any = self.spec
        for key in path.split("."):
            if not isinstance(node, dict) or key not in node:
                if default is KeyError:
                    raise VAPError("vap_spec.json 缺鍵:%s(SSOT 為唯一真相,不得以寫死值替代)" % path)
                return default
            node = node[key]
        return node

    # -- 常用樣式解析(全部指回 SSOT)-------------------------------------
    @property
    def palette(self) -> List[str]:
        combos = self.get("palette.combos")
        return list(combos[self.get("palette.default")])

    @property
    def up(self) -> str:
        return self.get("palette.semantic.up")

    @property
    def down(self) -> str:
        return self.get("palette.semantic.down")

    @property
    def neutral(self) -> str:
        return self.get("palette.semantic.neutral")

    @property
    def line_width(self) -> float:
        return float(self.get("line.width"))

    @property
    def line_opacity(self) -> float:
        return float(self.get("line.opacity"))

    @property
    def dash_secondary(self) -> Tuple[float, float]:
        a, b = self.get("line.dashForSecondary").split()
        return float(a), float(b)

    def fill(self, key: str) -> float:
        return float(self.get("fill." + key))

    def bar_gap(self, kind: str) -> float:
        return float(self.get("bar.gapFactor")[kind])

    @property
    def bar_edge_width(self) -> float:
        return float(self.get("bar.edge.width"))

    @property
    def paper(self) -> str:
        return self.get("layout.paper")

    @property
    def plot_bg(self) -> str:
        return self.get("layout.plot")

    @property
    def grid_color(self) -> str:
        return self.get("layout.gridColor")

    @property
    def border_color(self) -> str:
        return self.get("layout.borderColor")

    @property
    def margins(self) -> Dict[str, int]:
        return dict(self.get("layout.margin"))

    def font_size(self, key: str) -> float:
        return float(self.get("typography.scale")[key])

    @property
    def font_families(self) -> List[str]:
        fams = self.get("typography.families")
        return [fams["text"], fams["cjk"], "Noto Sans CJK TC", "Microsoft JhengHei",
                "PingFang TC", "DejaVu Sans"]

    @property
    def corr_scale(self) -> List[Tuple[float, str]]:
        return [(float(p), c) for p, c in self.get("palette.correlation.scale")]

    @property
    def tick_multiples(self) -> List[float]:
        return [float(x) for x in self.get("axis.tickStepMultiples")]

    @property
    def headroom_ticks(self) -> int:
        return int(self.get("axis.headroomTicks"))

    @property
    def png_scale(self) -> int:
        return int(self.get("export.png.scale"))

    def ref_line(self, key: str) -> Dict[str, Any]:
        return dict(self.get("referenceLines." + key))

    # -- chartlib ------------------------------------------------------------
    def charts(self) -> "Dict[str, Dict[str, Any]]":
        out: Dict[str, Dict[str, Any]] = {}
        for grp in self.chartlib["groups"]:
            for ch in grp["charts"]:
                meta = dict(ch)
                meta["group"] = grp["id"]
                meta["group_zh"] = grp.get("zh", grp["id"])
                out[ch["id"]] = meta
        return out

    def chart_meta(self, key: str) -> Dict[str, Any]:
        charts = self.charts()
        if key in charts:
            return charts[key]
        for meta in charts.values():  # 也接受 VAP-CH-NN 代碼
            if meta.get("code", "").lower() == key.lower():
                return meta
        raise VAPError("未知圖型 %r(可用:%s)" % (key, ", ".join(sorted(charts))))

# ============================================================================
# §2 軸數學 — nice ticks(2/2.5/5/10 倍數)· headroom · 雙軸同格數對齊 · 格式化
# ============================================================================

def nice_step(raw: float, multiples: Sequence[float]) -> float:
    """最小的 multiple×10^k ≥ raw(SSOT tickStepMultiples 規則)。"""
    if raw <= 0 or not math.isfinite(raw):
        return 1.0
    mag = 10.0 ** math.floor(math.log10(raw))
    for k in (mag / 10.0, mag, mag * 10.0):
        for m in sorted(multiples):
            step = m * k / 10.0  # multiples 表意為 2/2.5/5/10 → 0.2k 0.25k 0.5k 1k
            if step >= raw - 1e-12:
                return step
    return mag * 10.0


def ticks_for(lo: float, hi: float, spec: Spec, n_intervals: int = 4,
              headroom: bool = True, include_zero: bool = False) -> List[float]:
    """固定 n_intervals 間隔(n+1 刻度)· 頂部依 SSOT headroomTicks 留格。"""
    if include_zero:
        lo, hi = min(lo, 0.0), max(hi, 0.0)
    if hi <= lo:
        hi = lo + 1.0
    span = hi - lo
    if headroom:
        span *= 1.0 + spec.headroom_ticks / float(n_intervals)
    step = nice_step(span / n_intervals, spec.tick_multiples)
    t0 = math.floor(lo / step) * step
    ticks = [t0 + i * step for i in range(n_intervals + 1)]
    while ticks[-1] < hi - 1e-9:  # 保證涵蓋資料(rangeWrapsData)
        step = nice_step(step * 1.01, spec.tick_multiples) if ticks[-1] <= t0 else step
        ticks = [t0 + i * step for i in range(n_intervals + 1)]
        if ticks[-1] >= hi - 1e-9:
            break
        t0 = math.floor(lo / step) * step
        step *= 2
        step = nice_step(step, spec.tick_multiples)
        ticks = [t0 + i * step for i in range(n_intervals + 1)]
    return [round(t, 10) for t in ticks]


def decimals_of(step: float) -> int:
    for d in range(0, 6):
        if abs(round(step, d) - step) < 1e-9:
            return d
    return 6


def fmt_tick(value: float, step: float, thousands: bool = True) -> str:
    """小數位一致 + 千分位(SSOT decimalUnify / thousandsSeparator)。"""
    d = decimals_of(step)
    text = ("{:,.%df}" % d).format(value) if thousands else ("{:.%df}" % d).format(value)
    return text


def dual_ticks(l_lo: float, l_hi: float, r_lo: float, r_hi: float,
               spec: Spec, n_intervals: int = 4) -> Tuple[List[float], List[float]]:
    """雙軸左右同刻度數 → 格線對齊(SSOT sameTickCountBothSides/dualAxisAligned)。"""
    return (ticks_for(l_lo, l_hi, spec, n_intervals),
            ticks_for(r_lo, r_hi, spec, n_intervals))


def thin_labels(labels: Sequence[str], max_labels: int = 8) -> Tuple[List[int], List[str]]:
    """交易日序軸:序數等距,僅抽樣顯示日期標籤(SSOT tradingDaySequence)。"""
    n = len(labels)
    if n <= max_labels:
        idx = list(range(n))
    else:
        stride = max(1, (n - 1) // (max_labels - 1))
        idx = list(range(0, n, stride))
        if idx[-1] != n - 1:
            idx.append(n - 1)
    return idx, [str(labels[i]) for i in idx]

# ============================================================================
# §3 確定性示範資料(stdlib random,種子固定;依 chartlib dataShape 供 28 型)
# ============================================================================

_SEED = 20260810


def _dates(n: int, start_year: int = 2024) -> List[str]:
    y, m = start_year, 1
    out = []
    for i in range(n):
        out.append("%04d-%02d" % (y, m))
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def _walk(rng: random.Random, n: int, start: float, vol: float, drift: float = 0.0) -> List[float]:
    vals, x = [], start
    for _ in range(n):
        x += drift + rng.gauss(0.0, vol)
        vals.append(round(x, 4))
    return vals


def demo_data(chart_id: str) -> Dict[str, Any]:
    rng = random.Random(_SEED)
    n = 36
    dates = _dates(n)
    if chart_id == "line":
        return {"date": dates, "value": _walk(rng, n, 100.0, 2.2, 0.6)}
    if chart_id == "area":
        return {"date": dates, "value": [abs(v) for v in _walk(rng, n, 55.0, 3.0, 0.4)]}
    if chart_id in ("bar", "hbar"):
        labels = ["食品", "居住", "交通", "醫療", "教育", "娛樂"]
        vals = [round(rng.uniform(-3.2, 4.6), 2) for _ in labels]
        return {"label": labels, "value": vals}
    if chart_id == "scatter":
        xs = [round(rng.uniform(0.5, 9.5), 2) for _ in range(48)]
        ys = [round(0.8 * x + rng.gauss(0, 1.4) + 1.0, 2) for x in xs]
        return {"x": xs, "y": ys}
    if chart_id in ("sarea", "sbar", "sbar100"):
        groups = ["稅課", "規費", "營業盈餘", "其他"]
        return {"date": dates[:12], "groups": {
            g: [round(abs(rng.gauss(20 + 8 * i, 4)), 1) for _ in range(12)]
            for i, g in enumerate(groups)}}
    if chart_id == "multi":
        panels = ["台股", "美股", "日股", "歐股"]
        return {"date": dates, "panels": {
            p: _walk(random.Random(_SEED + i), n, 100.0, 2.0, 0.3 + 0.2 * i)
            for i, p in enumerate(panels)}}
    if chart_id == "gbar":
        labels = ["Q1", "Q2", "Q3", "Q4"]
        return {"label": labels, "groups": {
            "官方": [round(rng.uniform(40, 90), 1) for _ in labels],
            "民間": [round(rng.uniform(40, 90), 1) for _ in labels]}}
    if chart_id == "dline":
        return {"date": dates, "left": _walk(rng, n, 3.0, 0.25),
                "right": [abs(v) for v in _walk(rng, n, 88.0, 2.5)]}
    if chart_id == "dbarline":
        return {"date": dates[:18],
                "bar": [round(abs(rng.gauss(220, 60)), 0) for _ in range(18)],
                "line": _walk(rng, 18, 4.1, 0.12, -0.02)}
    if chart_id == "evtmx":
        return {"date": dates, "value": _walk(rng, n, 100.0, 2.4, 0.2),
                "events": [{"date": dates[8], "label": "事件A"}, {"date": dates[22], "label": "事件B"}],
                "bands": [{"start": dates[12], "end": dates[16], "label": "衰退"}]}
    if chart_id == "corrheat":
        assets = ["股", "債", "金", "油", "匯", "REITs"]
        base = [[round(rng.uniform(-0.8, 0.9), 2) for _ in assets] for _ in assets]
        corr = [[1.0 if i == j else round((base[i][j] + base[j][i]) / 2, 2)
                 for j in range(len(assets))] for i in range(len(assets))]
        return {"labels": assets, "corr": corr}
    if chart_id == "brush":
        return {"date": dates, "value": _walk(rng, n, 120.0, 3.2, 0.3),
                "sel_start": 10, "sel_end": 24}
    if chart_id == "map":
        return {"region": ["United States", "Germany", "Japan", "Taiwan", "United Kingdom",
                           "France", "South Korea", "China"],
                "value": [round(rng.uniform(1.0, 5.0), 2) for _ in range(8)],
                "change": [round(rng.uniform(-1.5, 1.5), 2) for _ in range(8)]}
    if chart_id == "roll":
        return {"date": dates, "return": [round(rng.gauss(0.6, 2.8), 2) for _ in range(n)]}
    if chart_id == "rollcorr":
        return {"date": dates, "a": _walk(rng, n, 100, 2.0, 0.3), "b": _walk(rng, n, 60, 1.5, 0.2)}
    if chart_id == "rollsharpe":
        return {"date": dates, "sharpe": [round(rng.gauss(0.8, 0.5), 2) for _ in range(n)]}
    if chart_id == "sortino":
        sharpe = [round(0.7 + 0.5 * math.sin(i / 5.0) + rng.gauss(0, 0.12), 2) for i in range(n)]
        return {"date": dates, "sharpe": sharpe,
                "sortino": [round(s * rng.uniform(1.15, 1.5), 2) for s in sharpe]}
    if chart_id == "radar":
        metrics = ["波動", "MaxDD", "Beta", "集中度", "流動性"]
        return {"metric": metrics,
                "value": [round(rng.uniform(2.0, 4.6), 1) for _ in metrics],
                "benchmark": [round(rng.uniform(2.6, 4.0), 1) for _ in metrics]}
    if chart_id == "alpha":
        strat = _walk(rng, n, 100.0, 2.0, 0.8)
        bench = _walk(random.Random(_SEED + 7), n, 100.0, 1.6, 0.5)
        return {"date": dates, "strategy": strat, "benchmark": bench,
                "excess": [round(s - b, 2) for s, b in zip(strat, bench)]}
    if chart_id == "econcal":
        rows = []
        names = [("非農就業", 3), ("CPI 年增率", 3), ("零售銷售", 2), ("消費者信心", 2),
                 ("初領失業金", 1), ("工廠訂單", 1)]
        for i, (event, importance) in enumerate(names):
            forecast = round(rng.uniform(1.0, 5.0), 1)
            rows.append({"date": _dates(6)[i], "event": event, "importance": importance,
                         "actual": round(forecast + rng.uniform(-0.6, 0.9), 1),
                         "forecast": forecast, "previous": round(forecast + rng.uniform(-0.5, 0.5), 1)})
        return {"rows": rows}
    if chart_id == "consensus":
        return {"rows": [
            {"item": "dilutedEPS", "zh": "稀釋 EPS", "value": "23.4", "score": 0.8},
            {"item": "targetPrice", "zh": "目標價", "value": "1,180 (900–1,320)", "score": 0.7},
            {"item": "rating", "zh": "評等", "value": "Buy", "score": 0.9},
            {"item": "analystCount", "zh": "分析師數", "value": "28", "score": 0.6},
            {"item": "forwardPER", "zh": "預估 PER", "value": "18.2x", "score": 0.4},
            {"item": "forwardPBR", "zh": "預估 PBR", "value": "3.1x", "score": 0.3}]}
    if chart_id == "backtest":
        lags = list(range(1, 13))
        return {"lag": lags,
                "rankIC": [round(0.09 * math.exp(-i / 6.0) + rng.gauss(0, 0.008), 4) for i in lags],
                "tStat": [round(3.4 * math.exp(-i / 7.0) + rng.gauss(0, 0.15), 2) for i in lags],
                "pValue": [round(min(0.99, 0.02 * math.exp(i / 4.0)), 3) for i in lags]}
    if chart_id == "intraday":
        times = ["%02d:%02d" % (9 + t // 12, (t % 12) * 5) for t in range(54)]
        price = _walk(rng, 54, 612.0, 0.9)
        vol = [round(abs(rng.gauss(800, 350)), 0) for _ in range(54)]
        return {"time": times, "price": price, "volume": vol}
    if chart_id == "candle":
        n2 = 60
        dates2 = ["D%02d" % (i + 1) for i in range(n2)]
        close = _walk(rng, n2, 500.0, 6.0, 0.8)
        o, h, l, v = [], [], [], []
        prev = close[0]
        for c in close:
            oo = round(prev + rng.gauss(0, 2.0), 2)
            hh = round(max(oo, c) + abs(rng.gauss(0, 2.5)), 2)
            ll = round(min(oo, c) - abs(rng.gauss(0, 2.5)), 2)
            o.append(oo); h.append(hh); l.append(ll)
            v.append(round(abs(rng.gauss(1200, 500)), 0))
            prev = c
        return {"date": dates2, "open": o, "high": h, "low": l, "close": close, "volume": v}
    if chart_id == "spotfut":
        spot = _walk(rng, n, 78.0, 1.6, 0.1)
        return {"date": dates, "spot": spot,
                "futures": [round(s + rng.gauss(1.2, 0.5), 2) for s in spot]}
    raise VAPError("demo_data 未涵蓋圖型 %r" % chart_id)

# ============================================================================
# §4 共用工具 — 色彩轉換 · 滾動統計 · MaxDD · chartlib rule 數值抽取
# ============================================================================

def hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return "rgba(%d,%d,%d,%s)" % (r, g, b, round(alpha, 4))


def hex_to_mpl_rgba(hex_color: str, alpha: float) -> Tuple[float, float, float, float]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0, alpha)


def rolling_mean(vals: Sequence[float], w: int) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    for i in range(len(vals)):
        if i + 1 < w:
            out.append(None)
        else:
            out.append(sum(vals[i + 1 - w:i + 1]) / w)
    return out


def rolling_std(vals: Sequence[float], w: int) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    for i in range(len(vals)):
        if i + 1 < w:
            out.append(None)
        else:
            win = vals[i + 1 - w:i + 1]
            m = sum(win) / w
            out.append(math.sqrt(sum((x - m) ** 2 for x in win) / w))
    return out


def rolling_corr(a: Sequence[float], b: Sequence[float], w: int) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    for i in range(len(a)):
        if i + 1 < w:
            out.append(None)
            continue
        xa, xb = a[i + 1 - w:i + 1], b[i + 1 - w:i + 1]
        ma, mb = sum(xa) / w, sum(xb) / w
        cov = sum((x - ma) * (y - mb) for x, y in zip(xa, xb))
        va = math.sqrt(sum((x - ma) ** 2 for x in xa))
        vb = math.sqrt(sum((y - mb) ** 2 for y in xb))
        out.append(cov / (va * vb) if va > 0 and vb > 0 else None)
    return out


def max_drawdown(vals: Sequence[float]) -> Tuple[float, int, int]:
    """回傳 (最大回撤%, 峰索引, 谷索引)。"""
    peak, peak_i, mdd, lo_i, hi_i = vals[0], 0, 0.0, 0, 0
    for i, v in enumerate(vals):
        if v > peak:
            peak, peak_i = v, i
        dd = (v - peak) / peak * 100.0 if peak else 0.0
        if dd < mdd:
            mdd, hi_i, lo_i = dd, peak_i, i
    return round(mdd, 2), hi_i, lo_i


def rule_number(meta: Dict[str, Any], pattern: str, fallback: float) -> float:
    """自 chartlib 的 rule 文字抽取數值(規則文字為權威;抽不到誠實用後備)。"""
    m = re.search(pattern, str(meta.get("rule", "")))
    return float(m.group(1)) if m else fallback


def importance_color(spec: Spec, level: int) -> str:
    """經濟日曆重要度三階:紅(高)黃(中)綠(低)— 語意色 + via 色序之琥珀。"""
    return {3: spec.up, 2: spec.palette[1], 1: spec.down}.get(int(level), spec.neutral)

# ============================================================================
# §5 Seaborn / matplotlib 後端(靜態 PNG · export.png 規則)
# ============================================================================

def _module_available(name: str) -> bool:
    import importlib.util
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


class SeabornBackend:
    name = "seaborn"
    install_hint = "pip install seaborn matplotlib"

    @staticmethod
    def available() -> bool:
        return _module_available("seaborn") and _module_available("matplotlib")

    def __init__(self, spec: Spec):
        if not self.available():
            raise VAPError("seaborn/matplotlib 未安裝 — %s" % self.install_hint)
        self.spec = spec
        import logging as _logging
        _logging.getLogger("matplotlib.font_manager").setLevel(_logging.ERROR)
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import seaborn as sns
        self.plt, self.sns = plt, sns
        s = spec
        sns.set_theme(style="whitegrid", rc={
            "figure.facecolor": s.get("export.png.background"),
            "axes.facecolor": s.plot_bg,
            "axes.edgecolor": s.border_color,
            "axes.linewidth": 0.8,
            "grid.color": s.grid_color,
            "grid.linewidth": 0.7,
            "axes.titlesize": s.font_size("chartTitle") * 1.15,
            "axes.labelsize": s.font_size("axisTitle") * 1.15,
            "xtick.labelsize": s.font_size("tick") * 1.15,
            "ytick.labelsize": s.font_size("tick") * 1.15,
            "legend.fontsize": s.font_size("legend") * 1.15,
            "font.family": "sans-serif",
            "font.sans-serif": s.font_families,
            "axes.unicode_minus": False,
        })

    # -- 佈局 -----------------------------------------------------------------
    def _new_fig(self, rows: int = 1, height_ratios: Optional[Sequence[float]] = None,
                 polar: bool = False, width_px: int = 960):
        s = self.spec
        height_px = int(s.get("layout.stackStandardHeight")) * rows + 140
        fig = self.plt.figure(figsize=(width_px / 100.0, height_px / 100.0), dpi=100)
        m = s.margins
        fig.subplots_adjust(left=m["left"] / width_px, right=1 - m["right"] / width_px,
                            top=1 - (m["top"] + 26) / height_px, bottom=(m["bottom"] + 16) / height_px,
                            hspace=0.16)
        if rows == 1:
            ax = fig.add_subplot(111, polar=polar)
            return fig, [ax]
        gs = fig.add_gridspec(rows, 1, height_ratios=list(height_ratios or [1] * rows))
        axes = [fig.add_subplot(gs[i, 0]) for i in range(rows)]
        for ax in axes[:-1]:
            ax.tick_params(labelbottom=False)
        return fig, axes

    def _title(self, fig, meta: Dict[str, Any]) -> None:
        fig.suptitle("%s %s · %s(%s)" % (meta["code"], meta["zh"], meta["en"], meta.get("use", "")),
                     fontsize=self.spec.font_size("chartTitle") * 1.3, x=0.01, ha="left")

    def _seq_x(self, ax, labels: Sequence[str]) -> List[int]:
        idx, texts = thin_labels(labels)
        ax.set_xticks(idx)
        ax.set_xticklabels(texts)
        return list(range(len(labels)))

    def _y_ticks(self, ax, values: Sequence[float], include_zero: bool = False) -> List[float]:
        vals = [v for v in values if v is not None and math.isfinite(v)]
        if not vals:
            vals = [0.0, 1.0]
        ticks = ticks_for(min(vals), max(vals), self.spec, include_zero=include_zero)
        ax.set_yticks(ticks)
        ax.set_ylim(ticks[0], ticks[-1])
        step = ticks[1] - ticks[0]
        ax.set_yticklabels([fmt_tick(t, step) for t in ticks])
        return ticks

    def _dual_ticks(self, axl, axr, lvals: Sequence[float], rvals: Sequence[float],
                    include_zero_r: bool = False) -> None:
        lt = ticks_for(min(lvals), max(lvals), self.spec)
        rt = ticks_for(min(rvals), max(rvals), self.spec, include_zero=include_zero_r)
        for ax, ticks in ((axl, lt), (axr, rt)):
            ax.set_yticks(ticks)
            ax.set_ylim(ticks[0], ticks[-1])
            step = ticks[1] - ticks[0]
            ax.set_yticklabels([fmt_tick(t, step) for t in ticks])
        axr.grid(False)

    def _zero_axis(self, ax) -> None:
        z = self.spec.ref_line("zeroAxis")
        ax.axhline(0, color=z["color"], linewidth=float(z["width"]), zorder=3)

    def _bench_line(self, ax, y: float) -> None:
        b = self.spec.ref_line("benchmarkHorizontal")
        ax.axhline(y, color=b["color"], linewidth=float(b["width"]),
                   alpha=float(b["opacity"]), zorder=2)

    def _bar_face(self, color: str, dense: bool = False):
        s = self.spec
        key = "barFaceDense" if dense else "barFace"
        return dict(color=hex_to_mpl_rgba(color, s.fill(key)), edgecolor=color,
                    linewidth=s.bar_edge_width)

    # -- 渲染入口 -------------------------------------------------------------
    def build(self, chart_id: str, data: Dict[str, Any]):
        meta = self.spec.chart_meta(chart_id)
        fn = getattr(self, "r_" + meta["id"], None)
        if fn is None:
            raise VAPError("seaborn 後端缺少圖型 %r 實作" % meta["id"])
        fig = fn(data, meta)
        return fig, meta

    def render(self, chart_id: str, data: Dict[str, Any], out_path: Path,
               scale: Optional[int] = None) -> Path:
        fig, meta = self.build(chart_id, data)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, dpi=100 * (scale or self.spec.png_scale),
                    facecolor=self.spec.get("export.png.background"))
        self.plt.close(fig)
        return out_path

    # ------------------------------------------------------------------ 01-05
    def r_line(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        x = self._seq_x(ax, d["date"])
        ax.plot(x, d["value"], color=s.palette[0], linewidth=s.line_width, alpha=s.line_opacity)
        self._y_ticks(ax, d["value"])
        ax.annotate(fmt_tick(d["value"][-1], 0.01), (x[-1], d["value"][-1]),
                    textcoords="offset points", xytext=(4, 0),
                    fontsize=s.font_size("tick") * 1.15, color=s.palette[0])
        self._title(fig, meta)
        return fig

    def r_area(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        x = self._seq_x(ax, d["date"])
        ax.plot(x, d["value"], color=s.palette[0], linewidth=s.line_width, alpha=s.line_opacity)
        ax.fill_between(x, d["value"], color=s.palette[0],
                        alpha=s.fill("areaUnderLine"), linewidth=0)
        self._y_ticks(ax, d["value"], include_zero=True)
        self._title(fig, meta)
        return fig

    def r_bar(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        x = list(range(len(d["label"])))
        colors = [s.up if v >= 0 else s.down for v in d["value"]]
        for xi, v, c in zip(x, d["value"], colors):
            ax.bar(xi, v, width=s.bar_gap("normal"),
                   color=hex_to_mpl_rgba(c, s.fill("barFaceDense")),
                   edgecolor=c, linewidth=s.bar_edge_width)
        ax.set_xticks(x)
        ax.set_xticklabels(d["label"])
        self._y_ticks(ax, d["value"], include_zero=True)
        self._zero_axis(ax)
        self._title(fig, meta)
        return fig

    def r_hbar(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        y = list(range(len(d["label"])))
        for yi, v in zip(y, d["value"]):
            c = s.up if v >= 0 else s.down
            ax.barh(yi, v, height=s.bar_gap("normal"),
                    color=hex_to_mpl_rgba(c, s.fill("barFaceDense")),
                    edgecolor=c, linewidth=s.bar_edge_width)
        ax.set_yticks(y)
        ax.set_yticklabels(d["label"])
        ax.invert_yaxis()
        z = s.ref_line("zeroAxis")
        ax.axvline(0, color=z["color"], linewidth=float(z["width"]), zorder=3)
        ticks = ticks_for(min(d["value"] + [0]), max(d["value"] + [0]), s)
        ax.set_xticks(ticks)
        ax.set_xlim(ticks[0], ticks[-1])
        step = ticks[1] - ticks[0]
        ax.set_xticklabels([fmt_tick(t, step) for t in ticks])
        self._title(fig, meta)
        return fig

    def r_scatter(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        self.sns.regplot(x=d["x"], y=d["y"], ax=ax,
                         scatter_kws={"s": 30, "alpha": s.line_opacity,
                                      "color": s.palette[0], "edgecolor": s.plot_bg},
                         line_kws={"color": s.palette[1], "linewidth": s.line_width})
        self._y_ticks(ax, d["y"])
        self._title(fig, meta)
        return fig

    # ------------------------------------------------------------------ 06-10
    def _stack_common(self, d: Dict[str, Any], meta: Dict[str, Any], mode: str):
        s = self.spec
        fig, (ax,) = self._new_fig()
        names = list(d["groups"])
        x = self._seq_x(ax, d["date"] if "date" in d else d["label"])
        rows = [list(d["groups"][n]) for n in names]
        if mode == "sbar100":
            totals = [sum(col) or 1.0 for col in zip(*rows)]
            rows = [[v / t * 100.0 for v, t in zip(r, totals)] for r in rows]
        if mode == "sarea":
            ax.stackplot(x, rows, labels=names,
                         colors=[hex_to_mpl_rgba(c, s.fill("areaUnderLine")) for c in s.palette],
                         edgecolor=s.plot_bg, linewidth=1.0)
        else:
            width = s.bar_gap("tight")
            bottom = [0.0] * len(x)
            for name, row, color in zip(names, rows, s.palette):
                ax.bar(x, row, width=width, bottom=bottom, label=name,
                       color=hex_to_mpl_rgba(color, s.fill("barFace")),
                       edgecolor=s.plot_bg, linewidth=1.0)
                bottom = [b + v for b, v in zip(bottom, row)]
        totals = [sum(col) for col in zip(*rows)]
        if mode == "sbar100":
            ticks = [0, 25, 50, 75, 100]
            ax.set_yticks(ticks)
            ax.set_ylim(0, 100)
            ax.set_yticklabels([fmt_tick(t, 25) for t in ticks])
        else:
            self._y_ticks(ax, totals + [0.0])
        ax.legend(loc="upper left", ncols=min(4, len(names)), frameon=False)
        self._title(fig, meta)
        return fig

    def r_sarea(self, d, meta):
        return self._stack_common(d, meta, "sarea")

    def r_sbar(self, d, meta):
        return self._stack_common(d, meta, "sbar")

    def r_sbar100(self, d, meta):
        return self._stack_common(d, meta, "sbar100")

    def r_multi(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        grid = str(meta.get("override", {}).get("grid", "2x2"))
        rows, cols = (int(v) for v in grid.split("x"))
        width_px, hpx = 960, int(s.get("layout.stackStandardHeight")) * rows + 120
        fig = self.plt.figure(figsize=(width_px / 100.0, hpx / 100.0), dpi=100)
        m = s.margins
        fig.subplots_adjust(left=m["left"] / width_px, right=1 - m["right"] / width_px,
                            top=1 - (m["top"] + 30) / hpx, bottom=(m["bottom"] + 14) / hpx,
                            hspace=0.42, wspace=0.24)
        names = list(d["panels"])
        all_vals = [v for vs in d["panels"].values() for v in vs]
        ticks = ticks_for(min(all_vals), max(all_vals), s)  # 同軸比較:全面板同刻度
        step = ticks[1] - ticks[0]
        for i, name in enumerate(names[: rows * cols]):
            ax = fig.add_subplot(rows, cols, i + 1)
            idx, texts = thin_labels(d["date"], 4)
            ax.plot(range(len(d["date"])), d["panels"][name],
                    color=s.palette[i % len(s.palette)], linewidth=s.line_width,
                    alpha=s.line_opacity)
            ax.set_yticks(ticks)
            ax.set_ylim(ticks[0], ticks[-1])
            ax.set_yticklabels([fmt_tick(t, step) for t in ticks])
            ax.set_xticks(idx)
            ax.set_xticklabels(texts)
            ax.set_title(name, fontsize=s.font_size("axisTitle") * 1.2)
        self._title(fig, meta)
        return fig

    def r_gbar(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        names = list(d["groups"])
        slot = 2 * s.bar_gap("grouped")           # 兩組定義下的總佔位(0.88)
        width = slot / len(names)
        x0 = list(range(len(d["label"])))
        for gi, name in enumerate(names):
            xs = [xi - slot / 2 + width * (gi + 0.5) for xi in x0]
            color = s.palette[gi % len(s.palette)]
            ax.bar(xs, d["groups"][name], width=width, label=name,
                   color=hex_to_mpl_rgba(color, s.fill("barFaceDense")),
                   edgecolor=color, linewidth=s.bar_edge_width)
        ax.set_xticks(x0)
        ax.set_xticklabels(d["label"])
        all_vals = [v for vs in d["groups"].values() for v in vs]
        self._y_ticks(ax, all_vals + [0.0])
        ax.legend(loc="upper left", frameon=False)
        self._title(fig, meta)
        return fig

    # ------------------------------------------------------------------ 11-14
    def r_dline(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        axr = ax.twinx()
        x = self._seq_x(ax, d["date"])
        axr.fill_between(x, d["right"], color=s.palette[1],
                         alpha=s.fill("areaUnderLine"), linewidth=0, zorder=1)
        ax.plot(x, d["left"], color=s.palette[0], linewidth=s.line_width,
                alpha=s.line_opacity, zorder=3)
        self._dual_ticks(ax, axr, d["left"], d["right"], include_zero_r=True)
        ax.set_zorder(axr.get_zorder() + 1)
        ax.patch.set_visible(False)
        fig.legend(handles=[self.plt.Line2D([], [], color=s.palette[0], lw=s.line_width, label="左軸 折線"),
                            self.plt.Rectangle((0, 0), 1, 1,
                                               color=hex_to_mpl_rgba(s.palette[1], s.fill("areaUnderLine")),
                                               label="右軸 底色面積")],
                   loc="upper right", frameon=False, fontsize=s.font_size("legend") * 1.1)
        self._title(fig, meta)
        return fig

    def r_dbarline(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        axr = ax.twinx()
        x = self._seq_x(ax, d["date"])
        color_b, color_l = s.palette[0], s.palette[1]
        ax.bar(x, d["bar"], width=s.bar_gap("normal"),
               color=hex_to_mpl_rgba(color_b, s.fill("barFaceDense")),
               edgecolor=color_b, linewidth=s.bar_edge_width, zorder=2)
        axr.plot(x, d["line"], color=color_l, linewidth=s.line_width,
                 alpha=s.line_opacity, zorder=3)
        self._dual_ticks(ax, axr, d["bar"] + [0.0], d["line"])
        fig.legend(handles=[self.plt.Rectangle((0, 0), 1, 1,
                                               color=hex_to_mpl_rgba(color_b, s.fill("barFaceDense")),
                                               label="左軸 直條"),
                            self.plt.Line2D([], [], color=color_l, lw=s.line_width, label="右軸 折線")],
                   loc="upper right", frameon=False, fontsize=s.font_size("legend") * 1.1)
        self._title(fig, meta)
        return fig

    def r_evtmx(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        x = self._seq_x(ax, d["date"])
        pos = {lab: i for i, lab in enumerate(d["date"])}
        for band in d.get("bands", []):
            ax.axvspan(pos[band["start"]], pos[band["end"]],
                       color=s.neutral, alpha=s.fill("eventBand"), linewidth=0)
        ev = s.ref_line("eventVertical")
        for i, event in enumerate(d.get("events", [])):
            color = ev["colorOrder"][i % len(ev["colorOrder"])]
            ax.axvline(pos[event["date"]], color=color, linewidth=float(ev["width"]),
                       alpha=float(ev["opacity"]), linestyle="--")
            ax.annotate(event["label"], (pos[event["date"]], 1.0),
                        xycoords=("data", "axes fraction"), xytext=(3, -10),
                        textcoords="offset points", fontsize=s.font_size("tick") * 1.1,
                        color=color)
        ax.plot(x, d["value"], color=s.palette[0], linewidth=s.line_width, alpha=s.line_opacity)
        self._y_ticks(ax, d["value"])
        if s.get("referenceLines.noHorizontalOnEventMatrix"):
            ax.grid(False, axis="y")
        self._title(fig, meta)
        return fig

    def r_corrheat(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        from matplotlib.colors import LinearSegmentedColormap
        import numpy as np
        fig, (ax,) = self._new_fig()
        n = len(d["labels"])
        # 顯示下三角(上三角遮罩)— 必須用 numpy 布林陣列:seaborn 對純 list 遮罩會全遮
        mask = np.triu(np.ones((n, n), dtype=bool), k=1)
        cmap = LinearSegmentedColormap.from_list("via_corr", s.corr_scale)
        gap = float(s.get("palette.correlation.gap"))
        self.sns.heatmap([[v for v in row] for row in d["corr"]],
                         mask=mask, ax=ax, cmap=cmap,
                         center=float(s.get("palette.correlation.zmid")),
                         vmin=-1.0, vmax=1.0, annot=True, fmt=".2f",
                         annot_kws={"fontsize": s.font_size("tick") * 1.1},
                         linewidths=gap, linecolor=s.plot_bg, square=True,
                         xticklabels=d["labels"], yticklabels=d["labels"],
                         cbar_kws={"shrink": 0.8})
        self._title(fig, meta)
        return fig

    # ------------------------------------------------------------------ 15-16
    def r_brush(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        x = self._seq_x(ax, d["date"])
        ax.plot(x, d["value"], color=s.palette[0], linewidth=s.line_width, alpha=s.line_opacity)
        a, b = int(d.get("sel_start", 0)), int(d.get("sel_end", len(x) - 1))
        seg = d["value"][a:b + 1]
        ax.axvspan(a, b, color=s.palette[4], alpha=s.fill("eventBand"), linewidth=0)
        mdd, _, _ = max_drawdown(seg)
        info = "區間 %s→%s · 高 %s · 低 %s · MaxDD %s%% · 耗時 %d 期" % (
            d["date"][a], d["date"][b], fmt_tick(max(seg), 0.01), fmt_tick(min(seg), 0.01),
            mdd, b - a)
        ax.set_title(info, fontsize=s.font_size("hint") * 1.1, loc="right",
                     color=s.get("palette.semantic.benchmark"))
        self._y_ticks(ax, d["value"])
        self._title(fig, meta)
        return fig

    def r_map(self, d: Dict[str, Any], meta: Dict[str, Any]):
        raise VAPUnsupported("VAP-CH-16 地圖:seaborn 後端無底圖能力 — 請用 plotly 後端"
                             "(內建世界圖形,離線可用)")

    # ------------------------------------------------------------------ 17-22
    def r_roll(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        x = self._seq_x(ax, d["date"])
        vals = d["return"]
        up = [v if v >= 0 else 0.0 for v in vals]
        dn = [v if v < 0 else 0.0 for v in vals]
        ax.fill_between(x, up, color=s.up, alpha=s.fill("areaUnderLineWithShadow"), linewidth=0)
        ax.fill_between(x, dn, color=s.down, alpha=s.fill("areaUnderLineWithShadow"), linewidth=0)
        ax.plot(x, vals, color=s.palette[0], linewidth=s.line_width, alpha=s.line_opacity)
        self._y_ticks(ax, vals, include_zero=True)
        self._zero_axis(ax)
        self._title(fig, meta)
        return fig

    def r_rollcorr(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        x = self._seq_x(ax, d["date"])
        corr = rolling_corr(d["a"], d["b"], 12)
        xs = [i for i, c in zip(x, corr) if c is not None]
        cs = [c for c in corr if c is not None]
        ax.plot(xs, cs, color=s.palette[0], linewidth=s.line_width, alpha=s.line_opacity)
        ticks = [-1.0, -0.5, 0.0, 0.5, 1.0]
        ax.set_yticks(ticks)
        ax.set_ylim(-1.0, 1.0)
        ax.set_yticklabels([fmt_tick(t, 0.5) for t in ticks])
        self._zero_axis(ax)
        self._title(fig, meta)
        return fig

    def r_rollsharpe(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        x = self._seq_x(ax, d["date"])
        ax.plot(x, d["sharpe"], color=s.palette[0], linewidth=s.line_width, alpha=s.line_opacity)
        self._bench_line(ax, 1.0)
        self._y_ticks(ax, d["sharpe"] + [0.0, 1.0])
        self._title(fig, meta)
        return fig

    def r_sortino(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        axr = ax.twinx()
        x = self._seq_x(ax, d["date"])
        ax.plot(x, d["sharpe"], color=s.palette[0], linewidth=s.line_width,
                alpha=s.line_opacity, label="Sharpe(左)")
        axr.plot(x, d["sortino"], color=s.palette[1], linewidth=s.line_width,
                 alpha=s.line_opacity, dashes=s.dash_secondary, label="Sortino(右)")
        self._dual_ticks(ax, axr, d["sharpe"], d["sortino"])
        fig.legend(loc="upper right", frameon=False, fontsize=s.font_size("legend") * 1.1)
        self._title(fig, meta)
        return fig

    def r_radar(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig(polar=True)
        n = len(d["metric"])
        angles = [2 * math.pi * i / n for i in range(n)] + [0.0]
        val = list(d["value"]) + [d["value"][0]]
        ben = list(d["benchmark"]) + [d["benchmark"][0]]
        fill_a = rule_number(meta, r"α([0-9.]+)", s.fill("eventBand"))
        ax.plot(angles, val, color=s.palette[0], linewidth=s.line_width, alpha=s.line_opacity)
        ax.fill(angles, val, color=s.palette[0], alpha=fill_a)
        ax.plot(angles, ben, color=s.get("palette.semantic.benchmark"),
                linewidth=s.line_width, dashes=s.dash_secondary, label="基準")
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(d["metric"])
        ax.set_ylim(0, max(val + ben) * 1.2)
        ax.legend(loc="upper right", frameon=False, fontsize=s.font_size("legend") * 1.1)
        self._title(fig, meta)
        return fig

    def r_alpha(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        axr = ax.twinx()
        x = self._seq_x(ax, d["date"])
        ax.plot(x, d["strategy"], color=s.palette[0], linewidth=s.line_width,
                alpha=s.line_opacity, label="策略(左)", zorder=3)
        ax.plot(x, d["benchmark"], color=s.get("palette.semantic.benchmark"),
                linewidth=s.line_width, dashes=s.dash_secondary, label="基準(左)", zorder=3)
        for xi, v in zip(x, d["excess"]):
            c = s.up if v >= 0 else s.down
            axr.bar(xi, v, width=s.bar_gap("normal"),
                    color=hex_to_mpl_rgba(c, s.fill("barFace")), linewidth=0, zorder=1)
        self._dual_ticks(ax, axr, d["strategy"] + d["benchmark"], d["excess"] + [0.0],
                         include_zero_r=True)
        z = s.ref_line("zeroAxis")
        axr.axhline(0, color=z["color"], linewidth=float(z["width"]), zorder=2)
        ax.set_zorder(axr.get_zorder() + 1)
        ax.patch.set_visible(False)
        fig.legend(loc="upper left", frameon=False, fontsize=s.font_size("legend") * 1.1)
        self._title(fig, meta)
        return fig

    # ------------------------------------------------------------------ 23-25
    def r_econcal(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        ax.axis("off")
        cols = ["日期", "事件", "重要度", "實際", "預期", "前值"]
        cells, cell_colors, text_colors = [], [], []
        for row in d["rows"]:
            beat = row["actual"] is not None and row["actual"] > row["forecast"]
            cells.append([row["date"], row["event"], "●" * int(row["importance"]),
                          fmt_tick(row["actual"], 0.1), fmt_tick(row["forecast"], 0.1),
                          fmt_tick(row["previous"], 0.1)])
            cell_colors.append([s.plot_bg] * 6)
            text_colors.append(["#1e1d1a", "#1e1d1a", importance_color(s, row["importance"]),
                                s.up if beat else "#1e1d1a", "#1e1d1a", "#1e1d1a"])
        table = ax.table(cellText=cells, colLabels=cols, cellColours=cell_colors,
                         loc="center", cellLoc="center")
        table.auto_set_font_size(False)
        table.set_fontsize(s.font_size("legend") * 1.2)
        table.scale(1, 1.6)
        for (r, c), cell in table.get_celld().items():
            cell.set_edgecolor(s.grid_color)
            if r == 0:
                cell.set_facecolor(s.paper)
                cell.set_text_props(weight="bold")
            else:
                cell.set_text_props(color=text_colors[r - 1][c])
        self._title(fig, meta)
        return fig

    def r_consensus(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        from matplotlib.colors import LinearSegmentedColormap
        fig, (ax,) = self._new_fig()
        cmap = LinearSegmentedColormap.from_list("gyr", [s.down, s.palette[1], s.up])
        rows = d["rows"]
        y = list(range(len(rows)))
        for yi, row in zip(y, rows):
            ax.barh(yi, float(row["score"]), height=s.bar_gap("normal"),
                    color=cmap(float(row["score"])), edgecolor=s.border_color,
                    linewidth=s.bar_edge_width)
            ax.annotate("%s:%s" % (row["zh"], row["value"]), (0.02, yi),
                        va="center", fontsize=s.font_size("legend") * 1.2)
        ax.set_yticks(y)
        ax.set_yticklabels([r["item"] for r in rows])
        ax.invert_yaxis()
        ax.set_xlim(0, 1.0)
        ticks = [0, 0.25, 0.5, 0.75, 1.0]
        ax.set_xticks(ticks)
        ax.set_xticklabels([fmt_tick(t, 0.25) for t in ticks])
        self._title(fig, meta)
        return fig

    def r_backtest(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        axr = ax.twinx()
        x = list(range(len(d["lag"])))
        color_b, color_l = s.palette[4], s.palette[0]
        for xi, v in zip(x, d["rankIC"]):
            ax.bar(xi, v, width=s.bar_gap("normal"),
                   color=hex_to_mpl_rgba(color_b, s.fill("barFaceDense")),
                   edgecolor=color_b, linewidth=s.bar_edge_width, zorder=2)
        axr.plot(x, d["tStat"], color=color_l, linewidth=s.line_width,
                 alpha=s.line_opacity, zorder=3)
        t_ref = rule_number(meta, r"\|t\|=([0-9.]+)", 1.96)
        b = s.ref_line("benchmarkHorizontal")
        for yv in (t_ref, -t_ref):
            axr.axhline(yv, color=b["color"], linewidth=float(b["width"]),
                        alpha=float(b["opacity"]))
        ax.set_xticks(x)
        ax.set_xticklabels(["L%d" % v for v in d["lag"]])
        self._dual_ticks(ax, axr, d["rankIC"] + [0.0], d["tStat"] + [t_ref, -t_ref, 0.0])
        self._zero_axis(ax)
        fig.legend(handles=[self.plt.Rectangle((0, 0), 1, 1,
                                               color=hex_to_mpl_rgba(color_b, s.fill("barFaceDense")),
                                               label="Rank-IC(左)"),
                            self.plt.Line2D([], [], color=color_l, lw=s.line_width,
                                            label="t 統計量(右)")],
                   loc="upper right", frameon=False, fontsize=s.font_size("legend") * 1.1)
        self._title(fig, meta)
        return fig

    # ------------------------------------------------------------------ 26-28
    def r_intraday(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        hr = [rule_number(meta, r"\[(0?\.[0-9]+),", 0.72), 0.0]
        hr[1] = round(1.0 - hr[0], 4)
        fig, (ax_p, ax_v) = self._new_fig(rows=2, height_ratios=hr)
        x = list(range(len(d["time"])))
        ax_p.plot(x, d["price"], color=s.palette[0], linewidth=s.line_width, alpha=s.line_opacity)
        self._y_ticks(ax_p, d["price"])
        for xi, v in zip(x, d["volume"]):
            ax_v.bar(xi, v, width=s.bar_gap("tight"),
                     color=hex_to_mpl_rgba(s.neutral, s.fill("barFace")), linewidth=0)
        self._y_ticks(ax_v, d["volume"] + [0.0])
        idx, texts = thin_labels(d["time"])
        ax_v.set_xticks(idx)
        ax_v.set_xticklabels(texts)
        self._title(fig, meta)
        return fig

    def r_candle(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax, ax_v) = self._new_fig(rows=2, height_ratios=[0.72, 0.28])
        x = list(range(len(d["date"])))
        sma = rolling_mean(d["close"], 20)
        std = rolling_std(d["close"], 20)
        upper = [None if m is None else m + 2 * sd for m, sd in zip(sma, std)]
        lower = [None if m is None else m - 2 * sd for m, sd in zip(sma, std)]
        xs_bb = [i for i, m in enumerate(sma) if m is not None]
        ax.fill_between(xs_bb, [upper[i] for i in xs_bb], [lower[i] for i in xs_bb],
                        color=s.neutral, alpha=s.fill("eventBand"), linewidth=0, label="BB(20,2)")
        for i, (o, h, l, c) in enumerate(zip(d["open"], d["high"], d["low"], d["close"])):
            color = s.up if c >= o else s.down       # 漲紅跌綠(SSOT semantic)
            ax.plot([i, i], [l, h], color=color, linewidth=s.line_width)
            body_low, body_high = min(o, c), max(o, c)
            ax.add_patch(self.plt.Rectangle((i - 0.32, body_low), 0.64,
                                            max(body_high - body_low, 1e-9),
                                            facecolor=hex_to_mpl_rgba(color, s.fill("barFaceDense")),
                                            edgecolor=color, linewidth=s.bar_edge_width))
        ax.plot(xs_bb, [sma[i] for i in xs_bb], color=s.palette[4],
                linewidth=s.line_width, label="SMA20")
        ema, k = [], 2 / (12 + 1)
        for i, c in enumerate(d["close"]):
            ema.append(c if i == 0 else c * k + ema[-1] * (1 - k))
        ax.plot(x, ema, color=s.palette[1], linewidth=s.line_width,
                dashes=s.dash_secondary, label="EMA12")
        self._y_ticks(ax, d["low"] + d["high"])
        ax.legend(loc="upper left", ncols=3, frameon=False,
                  fontsize=s.font_size("legend") * 1.05)
        for i, v in enumerate(d["volume"]):
            color = s.up if d["close"][i] >= d["open"][i] else s.down
            ax_v.bar(i, v, width=s.bar_gap("tight"),
                     color=hex_to_mpl_rgba(color, s.fill("barFace")), linewidth=0)
        self._y_ticks(ax_v, d["volume"] + [0.0])
        idx, texts = thin_labels(d["date"])
        ax_v.set_xticks(idx)
        ax_v.set_xticklabels(texts)
        self._title(fig, meta)
        return fig

    def r_spotfut(self, d: Dict[str, Any], meta: Dict[str, Any]):
        s = self.spec
        fig, (ax,) = self._new_fig()
        x = self._seq_x(ax, d["date"])
        ax.plot(x, d["spot"], color=s.palette[0], linewidth=s.line_width,
                alpha=s.line_opacity, label="現貨(實線)")
        ax.plot(x, d["futures"], color=s.palette[1], linewidth=s.line_width,
                alpha=s.line_opacity, dashes=s.dash_secondary, label="期貨(虛線)")
        basis = d["futures"][-1] - d["spot"][-1]
        ax.annotate("基差 %+.2f" % basis, (x[-1], d["futures"][-1]),
                    textcoords="offset points", xytext=(6, 8),
                    fontsize=s.font_size("hint") * 1.1, color=s.palette[1])
        self._y_ticks(ax, d["spot"] + d["futures"])
        ax.legend(loc="upper left", frameon=False, fontsize=s.font_size("legend") * 1.1)
        self._title(fig, meta)
        return fig

# ============================================================================
# §6 Plotly 後端(互動 HTML · export.html 規則 · hover=x unified · 離線)
# ============================================================================

class PlotlyBackend:
    name = "plotly"
    install_hint = "pip install plotly"

    @staticmethod
    def available() -> bool:
        return _module_available("plotly")

    def __init__(self, spec: Spec):
        if not self.available():
            raise VAPError("plotly 未安裝 — %s" % self.install_hint)
        self.spec = spec
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        self.go, self.make_subplots = go, make_subplots

    # -- 佈局 -----------------------------------------------------------------
    def _layout(self, meta: Dict[str, Any], **overrides: Any) -> Dict[str, Any]:
        s = self.spec
        m = s.margins
        base: Dict[str, Any] = dict(
            title=dict(text="%s %s · %s(%s)" % (meta["code"], meta["zh"], meta["en"],
                                                meta.get("use", "")),
                       font=dict(size=s.font_size("chartTitle") * 1.4), x=0.01),
            paper_bgcolor=s.paper, plot_bgcolor=s.plot_bg,
            margin=dict(t=m["top"] + 44, r=m["right"] + 12, b=m["bottom"] + 12, l=m["left"]),
            font=dict(family=", ".join(s.font_families), size=s.font_size("tick") * 1.25),
            hovermode=("x unified" if s.get("interaction.hover") == "x unified" else "closest"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.0,
                        font=dict(size=s.font_size("legend") * 1.2)),
            height=int(s.get("layout.stackStandardHeight")) + 190, width=980,
            xaxis=dict(gridcolor=s.grid_color, zeroline=False, linecolor=s.border_color),
            yaxis=dict(gridcolor=s.grid_color, zeroline=False, linecolor=s.border_color),
        )
        base.update(overrides)
        return base

    def _seq_xaxis(self, labels: Sequence[str]) -> Dict[str, Any]:
        idx, texts = thin_labels(labels)
        return dict(tickmode="array", tickvals=idx, ticktext=texts,
                    gridcolor=self.spec.grid_color, zeroline=False,
                    linecolor=self.spec.border_color)

    def _tick_axis(self, vals: Sequence[float], include_zero: bool = False,
                   side: Optional[str] = None) -> Dict[str, Any]:
        clean = [v for v in vals if v is not None and math.isfinite(v)] or [0.0, 1.0]
        ticks = ticks_for(min(clean), max(clean), self.spec, include_zero=include_zero)
        step = ticks[1] - ticks[0]
        ax = dict(tickmode="array", tickvals=ticks, range=[ticks[0], ticks[-1]],
                  ticktext=[fmt_tick(t, step) for t in ticks],
                  gridcolor=self.spec.grid_color, zeroline=False,
                  linecolor=self.spec.border_color)
        if side == "right":
            ax.update(overlaying="y", side="right", showgrid=False)
        return ax

    def _vline(self, x: float, color: str, width: float, opacity: float,
               dash: str = "dash") -> Dict[str, Any]:
        return dict(type="line", x0=x, x1=x, y0=0, y1=1, yref="paper",
                    line=dict(color=color, width=width, dash=dash), opacity=opacity)

    def _hline(self, y: float, color: str, width: float, opacity: float,
               dash: str = "solid", yref: str = "y") -> Dict[str, Any]:
        return dict(type="line", x0=0, x1=1, xref="paper", y0=y, y1=y, yref=yref,
                    line=dict(color=color, width=width, dash=dash), opacity=opacity)

    def _line_trace(self, x, y, name, color, text=None, dashed=False, yaxis="y"):
        s = self.spec
        dash_style = ("%dpx,%dpx" % s.dash_secondary) if dashed else "solid"
        return self.go.Scatter(x=list(x), y=list(y), mode="lines", name=name,
                               line=dict(color=color, width=s.line_width * 1.6,
                                         dash=dash_style),
                               opacity=s.line_opacity, yaxis=yaxis, text=text,
                               hovertemplate="%{text}<br>%{y}" if text else None)

    # -- 渲染入口 -------------------------------------------------------------
    def build(self, chart_id: str, data: Dict[str, Any]):
        meta = self.spec.chart_meta(chart_id)
        fn = getattr(self, "p_" + meta["id"], None)
        if fn is None:
            raise VAPError("plotly 後端缺少圖型 %r 實作" % meta["id"])
        return fn(data, meta), meta

    def render(self, chart_id: str, data: Dict[str, Any], out_path: Path,
               plotlyjs: Any = True) -> Path:
        fig, meta = self.build(chart_id, data)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(str(out_path), include_plotlyjs=plotlyjs, full_html=True)
        return out_path

    # ------------------------------------------------------------------ 01-05
    def p_line(self, d, meta):
        s = self.spec
        x = list(range(len(d["date"])))
        fig = self.go.Figure(self._line_trace(x, d["value"], meta["zh"], s.palette[0],
                                              text=d["date"]))
        fig.update_layout(**self._layout(meta, xaxis=self._seq_xaxis(d["date"]),
                                         yaxis=self._tick_axis(d["value"]), showlegend=False))
        return fig

    def p_area(self, d, meta):
        s = self.spec
        x = list(range(len(d["date"])))
        tr = self._line_trace(x, d["value"], meta["zh"], s.palette[0], text=d["date"])
        tr.update(fill="tozeroy", fillcolor=hex_to_rgba(s.palette[0], s.fill("areaUnderLine")))
        fig = self.go.Figure(tr)
        fig.update_layout(**self._layout(meta, xaxis=self._seq_xaxis(d["date"]),
                                         yaxis=self._tick_axis(d["value"], include_zero=True),
                                         showlegend=False))
        return fig

    def p_bar(self, d, meta):
        s = self.spec
        colors = [hex_to_rgba(s.up if v >= 0 else s.down, s.fill("barFaceDense"))
                  for v in d["value"]]
        edges = [s.up if v >= 0 else s.down for v in d["value"]]
        fig = self.go.Figure(self.go.Bar(
            x=d["label"], y=d["value"],
            marker=dict(color=colors, line=dict(color=edges, width=s.bar_edge_width))))
        z = s.ref_line("zeroAxis")
        fig.update_layout(**self._layout(meta, bargap=1 - s.bar_gap("normal"),
                                         yaxis=self._tick_axis(d["value"] + [0.0]),
                                         shapes=[self._hline(0, z["color"], float(z["width"]), 1.0)],
                                         showlegend=False))
        return fig

    def p_hbar(self, d, meta):
        s = self.spec
        colors = [hex_to_rgba(s.up if v >= 0 else s.down, s.fill("barFaceDense"))
                  for v in d["value"]]
        edges = [s.up if v >= 0 else s.down for v in d["value"]]
        fig = self.go.Figure(self.go.Bar(
            y=d["label"], x=d["value"], orientation="h",
            marker=dict(color=colors, line=dict(color=edges, width=s.bar_edge_width))))
        z = s.ref_line("zeroAxis")
        xaxis = self._tick_axis(d["value"] + [0.0])
        fig.update_layout(**self._layout(meta, bargap=1 - s.bar_gap("normal"),
                                         xaxis=xaxis,
                                         yaxis=dict(autorange="reversed",
                                                    gridcolor=s.grid_color, zeroline=False),
                                         shapes=[dict(type="line", y0=0, y1=1, yref="paper",
                                                      x0=0, x1=0,
                                                      line=dict(color=z["color"],
                                                                width=float(z["width"])))],
                                         showlegend=False))
        return fig

    def p_scatter(self, d, meta):
        s = self.spec
        n = len(d["x"])
        mx, my = sum(d["x"]) / n, sum(d["y"]) / n
        varx = sum((v - mx) ** 2 for v in d["x"]) or 1.0
        slope = sum((a - mx) * (b - my) for a, b in zip(d["x"], d["y"])) / varx
        xs = [min(d["x"]), max(d["x"])]
        fig = self.go.Figure([
            self.go.Scatter(x=d["x"], y=d["y"], mode="markers", name="觀測",
                            marker=dict(color=hex_to_rgba(s.palette[0], s.line_opacity),
                                        size=9, line=dict(color=s.plot_bg, width=1))),
            self._line_trace(xs, [my + slope * (v - mx) for v in xs], "回歸線", s.palette[1])])
        fig.update_layout(**self._layout(meta, yaxis=self._tick_axis(d["y"]),
                                         hovermode="closest"))
        return fig

    # ------------------------------------------------------------------ 06-10
    def _p_stack(self, d, meta, mode):
        s = self.spec
        names = list(d["groups"])
        labels = d.get("date", d.get("label"))
        x = list(range(len(labels)))
        rows = [list(d["groups"][n]) for n in names]
        if mode == "sbar100":
            totals = [sum(col) or 1.0 for col in zip(*rows)]
            rows = [[v / t * 100.0 for v, t in zip(r, totals)] for r in rows]
        fig = self.go.Figure()
        for name, row, color in zip(names, rows, s.palette):
            if mode == "sarea":
                fig.add_trace(self.go.Scatter(
                    x=x, y=row, name=name, stackgroup="one", mode="lines",
                    line=dict(color=color, width=s.line_width),
                    fillcolor=hex_to_rgba(color, s.fill("areaUnderLine")), text=labels,
                    hovertemplate="%{text}<br>%{y}"))
            else:
                fig.add_trace(self.go.Bar(
                    x=x, y=row, name=name,
                    marker=dict(color=hex_to_rgba(color, s.fill("barFace")),
                                line=dict(color=s.plot_bg, width=1))))
        totals = [sum(col) for col in zip(*rows)]
        yaxis = (dict(tickmode="array", tickvals=[0, 25, 50, 75, 100], range=[0, 100],
                      gridcolor=s.grid_color, zeroline=False)
                 if mode == "sbar100" else self._tick_axis(totals + [0.0]))
        fig.update_layout(**self._layout(meta, barmode="stack",
                                         bargap=1 - s.bar_gap("tight"),
                                         xaxis=self._seq_xaxis(labels), yaxis=yaxis))
        return fig

    def p_sarea(self, d, meta):
        return self._p_stack(d, meta, "sarea")

    def p_sbar(self, d, meta):
        return self._p_stack(d, meta, "sbar")

    def p_sbar100(self, d, meta):
        return self._p_stack(d, meta, "sbar100")

    def p_multi(self, d, meta):
        s = self.spec
        grid = str(meta.get("override", {}).get("grid", "2x2"))
        rows, cols = (int(v) for v in grid.split("x"))
        names = list(d["panels"])[: rows * cols]
        fig = self.make_subplots(rows=rows, cols=cols, subplot_titles=names,
                                 shared_xaxes=True, vertical_spacing=0.14)
        all_vals = [v for vs in d["panels"].values() for v in vs]
        axis = self._tick_axis(all_vals)
        x = list(range(len(d["date"])))
        for i, name in enumerate(names):
            fig.add_trace(self._line_trace(x, d["panels"][name], name,
                                           s.palette[i % len(s.palette)], text=d["date"]),
                          row=i // cols + 1, col=i % cols + 1)
        fig.update_yaxes(tickmode="array", tickvals=axis["tickvals"],
                         ticktext=axis["ticktext"], range=axis["range"],
                         gridcolor=s.grid_color)
        idx, texts = thin_labels(d["date"], 4)
        fig.update_xaxes(tickmode="array", tickvals=idx, ticktext=texts,
                         gridcolor=s.grid_color)
        layout = self._layout(meta, showlegend=False)
        layout.pop("xaxis"), layout.pop("yaxis")
        layout["height"] = int(s.get("layout.stackStandardHeight")) * rows + 160
        fig.update_layout(**layout)
        return fig

    def p_gbar(self, d, meta):
        s = self.spec
        slot = 2 * s.bar_gap("grouped")
        fig = self.go.Figure()
        for gi, (name, vals) in enumerate(d["groups"].items()):
            color = s.palette[gi % len(s.palette)]
            fig.add_trace(self.go.Bar(
                x=d["label"], y=vals, name=name,
                marker=dict(color=hex_to_rgba(color, s.fill("barFaceDense")),
                            line=dict(color=color, width=s.bar_edge_width))))
        all_vals = [v for vs in d["groups"].values() for v in vs]
        fig.update_layout(**self._layout(meta, barmode="group", bargap=1 - slot,
                                         bargroupgap=0.0,
                                         yaxis=self._tick_axis(all_vals + [0.0])))
        return fig

    # ------------------------------------------------------------------ 11-14
    def p_dline(self, d, meta):
        s = self.spec
        x = list(range(len(d["date"])))
        area = self.go.Scatter(x=x, y=d["right"], name="右軸 底色面積", mode="lines",
                               line=dict(color=s.palette[1], width=s.line_width),
                               fill="tozeroy",
                               fillcolor=hex_to_rgba(s.palette[1], s.fill("areaUnderLine")),
                               yaxis="y2", text=d["date"], hovertemplate="%{text}<br>%{y}")
        line = self._line_trace(x, d["left"], "左軸 折線", s.palette[0], text=d["date"])
        fig = self.go.Figure([area, line])
        fig.update_layout(**self._layout(meta, xaxis=self._seq_xaxis(d["date"]),
                                         yaxis=self._tick_axis(d["left"]),
                                         yaxis2=self._tick_axis(d["right"], include_zero=True,
                                                                side="right")))
        return fig

    def p_dbarline(self, d, meta):
        s = self.spec
        x = list(range(len(d["date"])))
        bar = self.go.Bar(x=x, y=d["bar"], name="左軸 直條",
                          marker=dict(color=hex_to_rgba(s.palette[0], s.fill("barFaceDense")),
                                      line=dict(color=s.palette[0], width=s.bar_edge_width)))
        line = self._line_trace(x, d["line"], "右軸 折線", s.palette[1],
                                text=d["date"], yaxis="y2")
        fig = self.go.Figure([bar, line])
        fig.update_layout(**self._layout(meta, bargap=1 - s.bar_gap("normal"),
                                         xaxis=self._seq_xaxis(d["date"]),
                                         yaxis=self._tick_axis(d["bar"] + [0.0]),
                                         yaxis2=self._tick_axis(d["line"], side="right")))
        return fig

    def p_evtmx(self, d, meta):
        s = self.spec
        x = list(range(len(d["date"])))
        pos = {lab: i for i, lab in enumerate(d["date"])}
        fig = self.go.Figure(self._line_trace(x, d["value"], meta["zh"], s.palette[0],
                                              text=d["date"]))
        shapes, annotations = [], []
        for band in d.get("bands", []):
            shapes.append(dict(type="rect", x0=pos[band["start"]], x1=pos[band["end"]],
                               y0=0, y1=1, yref="paper", fillcolor=s.neutral,
                               opacity=s.fill("eventBand"), line=dict(width=0)))
        ev = s.ref_line("eventVertical")
        for i, event in enumerate(d.get("events", [])):
            color = ev["colorOrder"][i % len(ev["colorOrder"])]
            shapes.append(self._vline(pos[event["date"]], color, float(ev["width"]),
                                      float(ev["opacity"])))
            annotations.append(dict(x=pos[event["date"]], y=1.0, yref="paper",
                                    text=event["label"], showarrow=False,
                                    font=dict(color=color, size=s.font_size("tick") * 1.2),
                                    xanchor="left", yanchor="top"))
        yaxis = self._tick_axis(d["value"])
        yaxis["showgrid"] = not bool(s.get("referenceLines.noHorizontalOnEventMatrix"))
        fig.update_layout(**self._layout(meta, xaxis=self._seq_xaxis(d["date"]),
                                         yaxis=yaxis, shapes=shapes,
                                         annotations=annotations, showlegend=False))
        return fig

    def p_corrheat(self, d, meta):
        s = self.spec
        n = len(d["labels"])
        z = [[d["corr"][i][j] if j <= i else None for j in range(n)] for i in range(n)]
        gap = float(s.get("palette.correlation.gap"))
        fig = self.go.Figure(self.go.Heatmap(
            z=z, x=d["labels"], y=d["labels"],
            colorscale=[[p, c] for p, c in s.corr_scale],
            zmid=float(s.get("palette.correlation.zmid")), zmin=-1, zmax=1,
            xgap=gap, ygap=gap, texttemplate="%{z:.2f}",
            textfont=dict(size=s.font_size("tick") * 1.2),
            hovertemplate="%{y} × %{x}:%{z:.2f}<extra></extra>"))
        fig.update_layout(**self._layout(meta, yaxis=dict(autorange="reversed"),
                                         hovermode="closest", showlegend=False))
        return fig

    # ------------------------------------------------------------------ 15-16
    def p_brush(self, d, meta):
        s = self.spec
        x = list(range(len(d["date"])))
        fig = self.go.Figure(self._line_trace(x, d["value"], meta["zh"], s.palette[0],
                                              text=d["date"]))
        a, b = int(d.get("sel_start", 0)), int(d.get("sel_end", len(x) - 1))
        seg = d["value"][a:b + 1]
        mdd, _, _ = max_drawdown(seg)
        info = "區間 %s→%s · 高 %s · 低 %s · MaxDD %s%% · 耗時 %d 期" % (
            d["date"][a], d["date"][b], fmt_tick(max(seg), 0.01), fmt_tick(min(seg), 0.01),
            mdd, b - a)
        xaxis = self._seq_xaxis(d["date"])
        xaxis["rangeslider"] = dict(visible=True, thickness=0.08)
        fig.update_layout(**self._layout(
            meta, xaxis=xaxis, yaxis=self._tick_axis(d["value"]), showlegend=False,
            shapes=[dict(type="rect", x0=a, x1=b, y0=0, y1=1, yref="paper",
                         fillcolor=s.palette[4], opacity=s.fill("eventBand"),
                         line=dict(width=0))],
            annotations=[dict(x=0.99, y=1.08, xref="paper", yref="paper", text=info,
                              showarrow=False, xanchor="right",
                              font=dict(size=s.font_size("hint") * 1.2,
                                        color=s.get("palette.semantic.benchmark")))]))
        return fig

    def p_map(self, d, meta):
        s = self.spec
        tri = ["▲" if c >= 0 else "▼" for c in d["change"]]
        fig = self.go.Figure(self.go.Choropleth(
            locations=d["region"], locationmode="country names", z=d["change"],
            colorscale=[[p, c] for p, c in s.corr_scale], zmid=0,
            text=["%s %s %+0.2f(水準 %s)" % (r, t, c, v)
                  for r, t, c, v in zip(d["region"], tri, d["change"], d["value"])],
            hovertemplate="%{text}<extra></extra>",
            colorbar=dict(title="漲跌", thickness=12)))
        layout = self._layout(meta, hovermode="closest", showlegend=False)
        layout.pop("xaxis"), layout.pop("yaxis")
        layout["geo"] = dict(bgcolor=s.plot_bg, showframe=False, showcoastlines=True,
                             coastlinecolor=s.border_color, landcolor=s.paper)
        fig.update_layout(**layout)
        return fig

    # ------------------------------------------------------------------ 17-22
    def p_roll(self, d, meta):
        s = self.spec
        x = list(range(len(d["date"])))
        up = [v if v >= 0 else 0.0 for v in d["return"]]
        dn = [v if v < 0 else 0.0 for v in d["return"]]
        z = s.ref_line("zeroAxis")
        fig = self.go.Figure([
            self.go.Scatter(x=x, y=up, mode="none", fill="tozeroy", name="正報酬",
                            fillcolor=hex_to_rgba(s.up, s.fill("areaUnderLineWithShadow"))),
            self.go.Scatter(x=x, y=dn, mode="none", fill="tozeroy", name="負報酬",
                            fillcolor=hex_to_rgba(s.down, s.fill("areaUnderLineWithShadow"))),
            self._line_trace(x, d["return"], meta["zh"], s.palette[0], text=d["date"])])
        fig.update_layout(**self._layout(meta, xaxis=self._seq_xaxis(d["date"]),
                                         yaxis=self._tick_axis(d["return"], include_zero=True),
                                         shapes=[self._hline(0, z["color"],
                                                             float(z["width"]), 1.0)]))
        return fig

    def p_rollcorr(self, d, meta):
        s = self.spec
        corr = rolling_corr(d["a"], d["b"], 12)
        xs = [i for i, c in enumerate(corr) if c is not None]
        cs = [c for c in corr if c is not None]
        z = s.ref_line("zeroAxis")
        fig = self.go.Figure(self._line_trace(xs, cs, "12 期滾動相關", s.palette[0],
                                              text=[d["date"][i] for i in xs]))
        fig.update_layout(**self._layout(
            meta, xaxis=self._seq_xaxis(d["date"]),
            yaxis=dict(tickmode="array", tickvals=[-1, -0.5, 0, 0.5, 1], range=[-1, 1],
                       gridcolor=s.grid_color, zeroline=False),
            shapes=[self._hline(0, z["color"], float(z["width"]), 1.0)], showlegend=False))
        return fig

    def p_rollsharpe(self, d, meta):
        s = self.spec
        x = list(range(len(d["date"])))
        b = s.ref_line("benchmarkHorizontal")
        fig = self.go.Figure(self._line_trace(x, d["sharpe"], meta["zh"], s.palette[0],
                                              text=d["date"]))
        fig.update_layout(**self._layout(meta, xaxis=self._seq_xaxis(d["date"]),
                                         yaxis=self._tick_axis(d["sharpe"] + [0.0, 1.0]),
                                         shapes=[self._hline(1.0, b["color"], float(b["width"]),
                                                             float(b["opacity"]))],
                                         showlegend=False))
        return fig

    def p_sortino(self, d, meta):
        s = self.spec
        x = list(range(len(d["date"])))
        fig = self.go.Figure([
            self._line_trace(x, d["sharpe"], "Sharpe(左)", s.palette[0], text=d["date"]),
            self._line_trace(x, d["sortino"], "Sortino(右)", s.palette[1], text=d["date"],
                             dashed=True, yaxis="y2")])
        fig.update_layout(**self._layout(meta, xaxis=self._seq_xaxis(d["date"]),
                                         yaxis=self._tick_axis(d["sharpe"]),
                                         yaxis2=self._tick_axis(d["sortino"], side="right")))
        return fig

    def p_radar(self, d, meta):
        s = self.spec
        metrics = list(d["metric"]) + [d["metric"][0]]
        val = list(d["value"]) + [d["value"][0]]
        ben = list(d["benchmark"]) + [d["benchmark"][0]]
        fill_a = rule_number(meta, r"α([0-9.]+)", s.fill("eventBand"))
        fig = self.go.Figure([
            self.go.Scatterpolar(r=val, theta=metrics, name="投組", fill="toself",
                                 line=dict(color=s.palette[0], width=s.line_width * 1.6),
                                 fillcolor=hex_to_rgba(s.palette[0], fill_a)),
            self.go.Scatterpolar(r=ben, theta=metrics, name="基準(外圈虛線)",
                                 line=dict(color=s.get("palette.semantic.benchmark"),
                                           width=s.line_width * 1.6,
                                           dash="%dpx,%dpx" % s.dash_secondary))])
        layout = self._layout(meta, hovermode="closest")
        layout.pop("xaxis"), layout.pop("yaxis")
        layout["polar"] = dict(bgcolor=s.plot_bg,
                               radialaxis=dict(gridcolor=s.grid_color,
                                               range=[0, max(val + ben) * 1.2]),
                               angularaxis=dict(gridcolor=s.grid_color))
        fig.update_layout(**layout)
        return fig

    def p_alpha(self, d, meta):
        s = self.spec
        x = list(range(len(d["date"])))
        bars = self.go.Bar(x=x, y=d["excess"], name="超額報酬(右)", yaxis="y2",
                           marker=dict(color=[hex_to_rgba(s.up if v >= 0 else s.down,
                                                          s.fill("barFace"))
                                              for v in d["excess"]], line=dict(width=0)))
        fig = self.go.Figure([
            bars,
            self._line_trace(x, d["strategy"], "策略(左)", s.palette[0], text=d["date"]),
            self._line_trace(x, d["benchmark"], "基準(左)",
                             s.get("palette.semantic.benchmark"), text=d["date"], dashed=True)])
        z = s.ref_line("zeroAxis")
        fig.update_layout(**self._layout(
            meta, bargap=1 - s.bar_gap("normal"), xaxis=self._seq_xaxis(d["date"]),
            yaxis=self._tick_axis(d["strategy"] + d["benchmark"]),
            yaxis2=self._tick_axis(d["excess"] + [0.0], include_zero=True, side="right"),
            shapes=[self._hline(0, z["color"], float(z["width"]), 1.0, yref="y2")]))
        return fig

    # ------------------------------------------------------------------ 23-25
    def p_econcal(self, d, meta):
        s = self.spec
        rows = d["rows"]
        ink = "#1e1d1a"
        imp_colors = [importance_color(s, r["importance"]) for r in rows]
        actual_colors = [s.up if r["actual"] > r["forecast"] else ink for r in rows]
        fig = self.go.Figure(self.go.Table(
            header=dict(values=["日期", "事件", "重要度", "實際", "預期", "前值"],
                        fill_color=s.paper, font=dict(size=s.font_size("legend") * 1.3),
                        line_color=s.border_color, align="left"),
            cells=dict(values=[[r["date"] for r in rows], [r["event"] for r in rows],
                               ["●" * int(r["importance"]) for r in rows],
                               [fmt_tick(r["actual"], 0.1) for r in rows],
                               [fmt_tick(r["forecast"], 0.1) for r in rows],
                               [fmt_tick(r["previous"], 0.1) for r in rows]],
                       fill_color=s.plot_bg, line_color=s.grid_color, align="left",
                       height=30, font=dict(size=s.font_size("legend") * 1.25,
                                            color=[ink, ink, imp_colors,
                                                   actual_colors, ink, ink]))))
        layout = self._layout(meta, hovermode="closest", showlegend=False)
        layout.pop("xaxis"), layout.pop("yaxis")
        fig.update_layout(**layout)
        return fig

    def p_consensus(self, d, meta):
        s = self.spec
        rows = d["rows"]

        def gyr(score: float) -> str:  # 綠黃紅 spectrum(SSOT 語意色內插)
            lo, mid, hi = s.down, s.palette[1], s.up
            a, b, t = (lo, mid, score * 2) if score <= 0.5 else (mid, hi, (score - 0.5) * 2)
            ca = [int(a.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
            cb = [int(b.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
            return "#%02x%02x%02x" % tuple(int(x + (y - x) * t) for x, y in zip(ca, cb))

        fig = self.go.Figure(self.go.Table(
            header=dict(values=["項目", "指標", "共識值", "位階"], fill_color=s.paper,
                        font=dict(size=s.font_size("legend") * 1.3),
                        line_color=s.border_color, align="left"),
            cells=dict(values=[[r["item"] for r in rows], [r["zh"] for r in rows],
                               [r["value"] for r in rows],
                               ["█" * max(1, int(r["score"] * 10)) for r in rows]],
                       fill_color=s.plot_bg, line_color=s.grid_color, align="left", height=30,
                       font=dict(size=s.font_size("legend") * 1.25,
                                 color=["#1e1d1a", "#1e1d1a", "#1e1d1a",
                                        [gyr(float(r["score"])) for r in rows]]))))
        layout = self._layout(meta, hovermode="closest", showlegend=False)
        layout.pop("xaxis"), layout.pop("yaxis")
        fig.update_layout(**layout)
        return fig

    def p_backtest(self, d, meta):
        s = self.spec
        labels = ["L%d" % v for v in d["lag"]]
        x = list(range(len(labels)))
        t_ref = rule_number(meta, r"\|t\|=([0-9.]+)", 1.96)
        b = s.ref_line("benchmarkHorizontal")
        z = s.ref_line("zeroAxis")
        fig = self.go.Figure([
            self.go.Bar(x=x, y=d["rankIC"], name="Rank-IC(左)",
                        marker=dict(color=hex_to_rgba(s.palette[4], s.fill("barFaceDense")),
                                    line=dict(color=s.palette[4], width=s.bar_edge_width))),
            self._line_trace(x, d["tStat"], "t 統計量(右)", s.palette[0],
                             text=["p=%s" % p for p in d["pValue"]], yaxis="y2")])
        fig.update_layout(**self._layout(
            meta, bargap=1 - s.bar_gap("normal"),
            xaxis=dict(tickmode="array", tickvals=x, ticktext=labels,
                       gridcolor=s.grid_color, zeroline=False),
            yaxis=self._tick_axis(d["rankIC"] + [0.0], include_zero=True),
            yaxis2=self._tick_axis(d["tStat"] + [t_ref, -t_ref, 0.0], side="right"),
            shapes=[self._hline(t_ref, b["color"], float(b["width"]), float(b["opacity"]),
                                yref="y2"),
                    self._hline(-t_ref, b["color"], float(b["width"]), float(b["opacity"]),
                                yref="y2"),
                    self._hline(0, z["color"], float(z["width"]), 1.0)]))
        return fig

    # ------------------------------------------------------------------ 26-28
    def _rows2(self, meta, top: float):
        fig = self.make_subplots(rows=2, cols=1, shared_xaxes=True,
                                 row_heights=[top, round(1 - top, 4)],
                                 vertical_spacing=0.05)
        return fig

    def p_intraday(self, d, meta):
        s = self.spec
        top = rule_number(meta, r"\[(0?\.[0-9]+),", 0.72)
        fig = self._rows2(meta, top)
        x = list(range(len(d["time"])))
        fig.add_trace(self._line_trace(x, d["price"], "價格", s.palette[0], text=d["time"]),
                      row=1, col=1)
        fig.add_trace(self.go.Bar(x=x, y=d["volume"], name="成交量",
                                  marker=dict(color=hex_to_rgba(s.neutral, s.fill("barFace")),
                                              line=dict(width=0))), row=2, col=1)
        pa = self._tick_axis(d["price"])
        va = self._tick_axis(d["volume"] + [0.0])
        idx, texts = thin_labels(d["time"])
        fig.update_yaxes(tickmode="array", tickvals=pa["tickvals"], ticktext=pa["ticktext"],
                         range=pa["range"], gridcolor=s.grid_color, row=1, col=1)
        fig.update_yaxes(tickmode="array", tickvals=va["tickvals"], ticktext=va["ticktext"],
                         range=va["range"], gridcolor=s.grid_color, row=2, col=1)
        fig.update_xaxes(tickmode="array", tickvals=idx, ticktext=texts,
                         gridcolor=s.grid_color, row=2, col=1)
        layout = self._layout(meta, bargap=1 - s.bar_gap("tight"))
        layout.pop("xaxis"), layout.pop("yaxis")
        layout["height"] = int(s.get("layout.stackStandardHeight")) * 2 + 160
        fig.update_layout(**layout)
        return fig

    def p_candle(self, d, meta):
        s = self.spec
        fig = self._rows2(meta, 0.72)
        x = list(range(len(d["date"])))
        sma = rolling_mean(d["close"], 20)
        std = rolling_std(d["close"], 20)
        xs_bb = [i for i, m in enumerate(sma) if m is not None]
        upper = [sma[i] + 2 * std[i] for i in xs_bb]
        lower = [sma[i] - 2 * std[i] for i in xs_bb]
        fig.add_trace(self.go.Scatter(x=xs_bb + xs_bb[::-1], y=upper + lower[::-1],
                                      fill="toself", mode="none", name="BB(20,2)",
                                      fillcolor=hex_to_rgba(s.neutral, s.fill("eventBand"))),
                      row=1, col=1)
        fig.add_trace(self.go.Candlestick(
            x=x, open=d["open"], high=d["high"], low=d["low"], close=d["close"], name="K線",
            increasing=dict(line=dict(color=s.up, width=s.line_width),
                            fillcolor=hex_to_rgba(s.up, s.fill("barFaceDense"))),
            decreasing=dict(line=dict(color=s.down, width=s.line_width),
                            fillcolor=hex_to_rgba(s.down, s.fill("barFaceDense")))),
            row=1, col=1)
        fig.add_trace(self._line_trace(xs_bb, [sma[i] for i in xs_bb], "SMA20", s.palette[4]),
                      row=1, col=1)
        ema, k = [], 2 / (12 + 1)
        for i, c in enumerate(d["close"]):
            ema.append(c if i == 0 else c * k + ema[-1] * (1 - k))
        fig.add_trace(self._line_trace(x, ema, "EMA12", s.palette[1], dashed=True),
                      row=1, col=1)
        vol_colors = [hex_to_rgba(s.up if c >= o else s.down, s.fill("barFace"))
                      for o, c in zip(d["open"], d["close"])]
        fig.add_trace(self.go.Bar(x=x, y=d["volume"], name="成交量",
                                  marker=dict(color=vol_colors, line=dict(width=0))),
                      row=2, col=1)
        pa = self._tick_axis(d["low"] + d["high"])
        va = self._tick_axis(d["volume"] + [0.0])
        idx, texts = thin_labels(d["date"])
        fig.update_yaxes(tickmode="array", tickvals=pa["tickvals"], ticktext=pa["ticktext"],
                         range=pa["range"], gridcolor=s.grid_color, row=1, col=1)
        fig.update_yaxes(tickmode="array", tickvals=va["tickvals"], ticktext=va["ticktext"],
                         range=va["range"], gridcolor=s.grid_color, row=2, col=1)
        fig.update_xaxes(tickmode="array", tickvals=idx, ticktext=texts,
                         gridcolor=s.grid_color, rangeslider_visible=False, row=1, col=1)
        fig.update_xaxes(tickmode="array", tickvals=idx, ticktext=texts,
                         gridcolor=s.grid_color, row=2, col=1)
        layout = self._layout(meta, bargap=1 - s.bar_gap("tight"))
        layout.pop("xaxis"), layout.pop("yaxis")
        layout["height"] = int(s.get("layout.stackStandardHeight")) * 2 + 180
        fig.update_layout(**layout)
        return fig

    def p_spotfut(self, d, meta):
        s = self.spec
        x = list(range(len(d["date"])))
        basis = d["futures"][-1] - d["spot"][-1]
        fig = self.go.Figure([
            self._line_trace(x, d["spot"], "現貨(實線)", s.palette[0], text=d["date"]),
            self._line_trace(x, d["futures"], "期貨(虛線)", s.palette[1],
                             text=d["date"], dashed=True)])
        fig.update_layout(**self._layout(
            meta, xaxis=self._seq_xaxis(d["date"]),
            yaxis=self._tick_axis(d["spot"] + d["futures"]),
            annotations=[dict(x=x[-1], y=d["futures"][-1], text="基差 %+.2f" % basis,
                              showarrow=False, xanchor="left", yanchor="bottom",
                              font=dict(color=s.palette[1],
                                        size=s.font_size("hint") * 1.2))]))
        return fig

# ============================================================================
# §7 demo 索引頁(離線)· selftest(渲染全譜 + visual-lock 自掃描 + 內省)
# ============================================================================

BACKENDS: Dict[str, Any] = {"seaborn": SeabornBackend, "plotly": PlotlyBackend}


def build_demo_index(spec: Spec, out_dir: Path, results: List[Dict[str, str]]) -> Path:
    rows_by_group: Dict[str, List[Dict[str, str]]] = {}
    for r in results:
        rows_by_group.setdefault(r["group_zh"], []).append(r)
    css = ("body{background:%s;font:14px/1.6 'DM Sans','Noto Sans TC',sans-serif;"
           "color:#1e1d1a;max-width:1080px;margin:24px auto;padding:0 16px}"
           "h1{font-size:20px}h2{font-size:15px;margin:18px 0 6px}"
           "table{width:100%%;border-collapse:collapse;background:%s}"
           "td,th{border:1px solid %s;padding:6px 9px;text-align:left;font-size:13px}"
           "a{color:#4c78a8;text-decoration:none}.skip{color:#9c9890}"
           ) % (spec.paper, spec.plot_bg, spec.border_color)
    parts = ["<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'>",
             "<title>VIA · VAP seaborn+plotly demo 索引</title><style>", css, "</style></head><body>",
             "<h1>VAP-CH-01…28 · seaborn+plotly 引擎 v%s demo</h1>" % __version__,
             "<p>樣式權威:%s(唯一真相)· 漲紅跌綠 · via 色序鎖定</p>" % spec.dir]
    for group, rows in rows_by_group.items():
        parts.append("<h2>%s</h2><table><tr><th>代碼</th><th>圖型</th><th>seaborn PNG</th>"
                     "<th>plotly HTML</th></tr>" % group)
        for r in rows:
            def cell(key: str) -> str:
                v = r.get(key, "")
                return ("<a href='%s'>開啟</a>" % v) if v and not v.startswith("SKIP") \
                    else ("<span class='skip'>%s</span>" % (v or "—"))
            parts.append("<tr><td>%s</td><td>%s · %s</td><td>%s</td><td>%s</td></tr>"
                         % (r["code"], r["zh"], r["en"], cell("seaborn"), cell("plotly")))
        parts.append("</table>")
    parts.append("</body></html>")
    out = out_dir / "index.html"
    out.write_text("".join(parts), encoding="utf-8")
    return out


def run_demo(spec: Spec, out_dir: Path, backends: Sequence[str], scale: Optional[int],
             quiet: bool = False) -> List[Dict[str, str]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    active: Dict[str, Any] = {}
    for name in backends:
        cls = BACKENDS[name]
        if cls.available():
            active[name] = cls(spec)
        elif not quiet:
            print("  [SKIP] 後端 %s 未安裝(%s)" % (name, cls.install_hint))
    results = []
    for chart_id, meta in spec.charts().items():
        row = {"code": meta["code"], "zh": meta["zh"], "en": meta["en"],
               "group_zh": meta["group_zh"]}
        data = demo_data(chart_id)
        for name, backend in active.items():
            fname = "%s_%s.%s" % (meta["code"].lower().replace("-", "_"), chart_id,
                                  "png" if name == "seaborn" else "html")
            try:
                if name == "seaborn":
                    backend.render(chart_id, data, out_dir / fname, scale=scale)
                else:
                    backend.render(chart_id, data, out_dir / fname, plotlyjs="directory")
                row[name] = fname
                if not quiet:
                    print("  [OK  ] %s × %s → %s" % (meta["code"], name, fname))
            except VAPUnsupported as e:
                row[name] = "SKIP(誠實不支援)"
                if not quiet:
                    print("  [SKIP] %s × %s:%s" % (meta["code"], name, e))
        results.append(row)
    if active:
        idx = build_demo_index(spec, out_dir, results)
        if not quiet:
            print("  索引頁:%s" % idx)
    return results


def visual_lock_scan() -> List[str]:
    """源碼自掃描:①alpha/opacity 直寫數字=違規(必須經 SSOT)②fill 語境出現
    0.75/0.4 家族字面值=違規(v0111 視覺鎖回歸案的制度化預防)。"""
    violations = []
    src_lines = Path(__file__).read_text(encoding="utf-8").splitlines()
    ctx = re.compile("(alpha|opacity|fillcolor|fill_between|fill=)")
    lock_family = re.compile("(?<![" + "0-9.])0[.](?:75|40?)(?![0-9])")
    direct_num = re.compile("(alpha|opacity)" + r"\s*=\s*[0-9]")
    dict_num = re.compile("[\"']" + "(alpha|opacity)" + r"[\"']\s*:\s*[0-9]")
    for no, line in enumerate(src_lines, 1):
        if ctx.search(line) and lock_family.search(line):
            violations.append("L%d 鎖定值字面出現於填色語境:%s" % (no, line.strip()[:90]))
        if direct_num.search(line) or dict_num.search(line):
            violations.append("L%d alpha/opacity 直寫數字(須經 SSOT):%s" % (no, line.strip()[:90]))
    return violations


def selftest(spec: Spec, out_dir: Optional[Path] = None) -> int:
    import tempfile
    results: List[Tuple[str, str, str]] = []

    def check(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
            results.append((name, "PASS", ""))
        except VAPUnsupported as e:
            results.append((name, "SKIP", str(e)[:80]))
        except Exception as e:
            results.append((name, "FAIL", "%s: %s" % (type(e).__name__, str(e)[:100])))

    # ① 圖庫註冊完整性
    charts = spec.charts()
    check("registry_28", lambda: (_ for _ in ()).throw(AssertionError(len(charts)))
          if len(charts) != 28 else None)
    check("demo_data_28", lambda: [demo_data(cid) for cid in charts])
    # ② 軸數學
    def axis_math():
        t = ticks_for(0.0, 9.7, spec)
        assert len(t) == 5, t
        lt, rt = dual_ticks(0, 100, -3, 3, spec)
        assert len(lt) == len(rt) == 5
        assert fmt_tick(1250.0, 250) == "1,250"
        assert fmt_tick(0.2, 0.05) == "0.20"
    check("axis_math", axis_math)
    # ③ SSOT 誠實 FAIL
    def spec_honesty():
        try:
            spec.get("no.such.key")
        except VAPError:
            return
        raise AssertionError("缺鍵未誠實 FAIL")
    check("ssot_missing_key", spec_honesty)
    # ④ visual-lock 自掃描
    def lock_scan():
        v = visual_lock_scan()
        assert not v, "; ".join(v[:3])
    check("visual_lock_scan", lock_scan)
    # ⑤ 渲染全譜
    tmp = out_dir or Path(tempfile.mkdtemp(prefix="vap_selftest_"))
    for bname, cls in BACKENDS.items():
        if not cls.available():
            results.append(("backend_%s" % bname, "SKIP", "未安裝:%s" % cls.install_hint))
            continue
        backend = cls(spec)
        for cid, meta in charts.items():
            label = "%s_%s" % (bname, meta["code"])
            def render_one(cid=cid, backend=backend, bname=bname):
                data = demo_data(cid)
                ext = "png" if bname == "seaborn" else "html"
                out = tmp / ("%s_%s.%s" % (bname, cid, ext))
                if bname == "seaborn":
                    backend.render(cid, data, out, scale=1)
                    head = out.read_bytes()[:8]
                    assert head.startswith(b"\x89PNG"), "非 PNG:%s" % head
                else:
                    backend.render(cid, data, out, plotlyjs="directory")
                    text = out.read_text(encoding="utf-8", errors="ignore")
                    assert "plotly" in text and "<div" in text, "HTML 缺 plotly 圖"
                assert out.stat().st_size > 900, "檔案過小"
            check(label, render_one)
    # ⑥ visual-lock 內省:面積圖填色透明度必等於 SSOT fill.areaUnderLine
    want = spec.fill("areaUnderLine")
    if PlotlyBackend.available():
        def lock_plotly():
            fig, _ = PlotlyBackend(spec).build("area", demo_data("area"))
            fc = fig.data[0].fillcolor
            assert fc == hex_to_rgba(spec.palette[0], want), fc
        check("visual_lock_plotly_area", lock_plotly)
    if SeabornBackend.available():
        def lock_seaborn():
            backend = SeabornBackend(spec)
            fig, _ = backend.build("area", demo_data("area"))
            ax = fig.axes[0]
            alphas = [c.get_facecolor()[0][3] for c in ax.collections if len(c.get_facecolor())]
            assert any(abs(a - want) < 1e-9 for a in alphas), alphas
            backend.plt.close(fig)
        check("visual_lock_seaborn_area", lock_seaborn)

    width = max(len(n) for n, _, _ in results)
    print("=" * 70)
    print("VAP seaborn+plotly 引擎 v%s selftest(%d 項)" % (__version__, len(results)))
    print("=" * 70)
    fails = 0
    for name, status, note in results:
        if status == "FAIL":
            fails += 1
        mark = {"PASS": "PASS", "SKIP": "SKIP", "FAIL": "FAIL"}[status]
        print("  %-*s  %s%s" % (width, name, mark, ("  ← " + note) if note else ""))
    passed = sum(1 for _, st, _ in results if st == "PASS")
    skipped = sum(1 for _, st, _ in results if st == "SKIP")
    print("-" * 70)
    print("  合計:%d PASS / %d SKIP / %d FAIL(輸出:%s)" % (passed, skipped, fails, tmp))
    return 1 if fails else 0

# ============================================================================
# §8 CLI
# ============================================================================

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="via_autoplot_seaborn_plotly",
        description="VIA VAP seaborn+plotly 引擎 v%s — VAP-CH-01…28 全譜雙後端" % __version__)
    ap.add_argument("--ssot", help="SSOT 目錄(預設自動向上找 spec/ssot)")
    sub = ap.add_subparsers(dest="verb")
    sub.add_parser("probe", help="後端/SSOT 在位探測")
    sub.add_parser("list", help="28 圖型清單")
    sub.add_parser("spec", help="已解析樣式規格(JSON)")
    r = sub.add_parser("render", help="渲染單一圖型")
    r.add_argument("--chart", required=True, help="圖型 id 或 VAP-CH-NN 代碼")
    r.add_argument("--backend", default="both", choices=["seaborn", "plotly", "both"])
    r.add_argument("--data", help="輸入資料 JSON(欄位依 chartlib dataShape;缺省用示範資料)")
    r.add_argument("--out", default="vap_out", help="輸出目錄")
    r.add_argument("--scale", type=int, help="PNG 縮放(預設依 SSOT export.png.scale)")
    r.add_argument("--plotlyjs", default="inline", choices=["inline", "directory", "cdn"],
                   help="plotly.js 佈署:inline=單檔自足(預設) directory=共用一份 cdn=線上")
    d = sub.add_parser("demo", help="28 型全渲染 + 離線索引頁")
    d.add_argument("--out", default="vap_demo", help="輸出目錄")
    d.add_argument("--backend", default="both", choices=["seaborn", "plotly", "both"])
    d.add_argument("--scale", type=int, default=1, help="PNG 縮放(demo 預設 1 省磁碟)")
    st = sub.add_parser("selftest", help="全譜自我驗證")
    st.add_argument("--out", help="渲染輸出目錄(預設暫存)")
    args = ap.parse_args(argv)
    if not args.verb:
        ap.print_help()
        return 0
    spec = Spec(find_ssot_dir(args.ssot))

    if args.verb == "probe":
        print("SSOT:%s" % spec.dir)
        print("  vap_spec %s(%s)· vap_chartlib %s(%s)· 圖型 %d 型"
              % (spec.spec["meta"]["version"], spec.spec["meta"]["updated"],
                 spec.chartlib["meta"]["version"], spec.chartlib["meta"]["updated"],
                 len(spec.charts())))
        for name, cls in BACKENDS.items():
            if cls.available():
                mod = __import__("seaborn" if name == "seaborn" else "plotly")
                print("  [OK  ] %-8s %s" % (name, getattr(mod, "__version__", "?")))
            else:
                print("  [缺席] %-8s → %s(缺席時本引擎誠實 SKIP,零依賴 SVG 引擎線不受影響)"
                      % (name, cls.install_hint))
        return 0

    if args.verb == "list":
        for meta in spec.charts().values():
            print("%-10s %-10s %s · %s(%s 軸 · %s)" % (
                meta["code"], meta["id"], meta["zh"], meta["en"],
                meta["axes"], meta["dataShape"]))
        return 0

    if args.verb == "spec":
        resolved = {
            "ssot_dir": str(spec.dir), "palette": spec.palette,
            "semantic": {"up": spec.up, "down": spec.down, "neutral": spec.neutral},
            "line": {"width": spec.line_width, "opacity": spec.line_opacity,
                     "dash_secondary": spec.dash_secondary},
            "fill": {k: spec.fill(k) for k in ("areaUnderLine", "areaUnderLineWithShadow",
                                               "barFace", "barFaceDense", "eventBand")},
            "bar_gap": {k: spec.bar_gap(k) for k in ("seamless", "tight", "normal", "grouped")},
            "tick_multiples": spec.tick_multiples, "headroom_ticks": spec.headroom_ticks,
            "margins": spec.margins, "png_scale": spec.png_scale,
            "corr_scale_steps": len(spec.corr_scale),
        }
        print(json.dumps(resolved, ensure_ascii=False, indent=2))
        return 0

    if args.verb == "render":
        meta = spec.chart_meta(args.chart)
        data = (json.loads(Path(args.data).read_text(encoding="utf-8"))
                if args.data else demo_data(meta["id"]))
        out_dir = Path(args.out)
        wanted = ["seaborn", "plotly"] if args.backend == "both" else [args.backend]
        rc = 0
        for name in wanted:
            cls = BACKENDS[name]
            if not cls.available():
                print("[缺席] %s 未安裝 — %s" % (name, cls.install_hint))
                rc = 1
                continue
            try:
                ext = "png" if name == "seaborn" else "html"
                out = out_dir / ("%s_%s.%s" % (meta["code"].lower().replace("-", "_"),
                                               name, ext))
                if name == "seaborn":
                    cls(spec).render(meta["id"], data, out, scale=args.scale)
                else:
                    mode = True if args.plotlyjs == "inline" else args.plotlyjs
                    cls(spec).render(meta["id"], data, out, plotlyjs=mode)
                print("[OK  ] %s × %s → %s" % (meta["code"], name, out))
            except VAPUnsupported as e:
                print("[SKIP] %s × %s:%s" % (meta["code"], name, e))
        return rc

    if args.verb == "demo":
        wanted = ["seaborn", "plotly"] if args.backend == "both" else [args.backend]
        run_demo(spec, Path(args.out), wanted, args.scale)
        return 0

    if args.verb == "selftest":
        return selftest(spec, Path(args.out) if args.out else None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
