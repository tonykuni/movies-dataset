#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VAP_ENG016_AutoplotOne_v0100 — VAP ONE · 單檔整合引擎(Veritas AutoPlot · one file)
=====================================================================================
目的:把 VAP 的治理核心整合進「一個 .py」——圖規 SSOT(40 canonical)、圖規鎖(軸契約)、
批330 資料律、標準高度契約、K 線 75/25、缺值律、大資料可稽核縮減、資料源(零依賴)、
零依賴 SVG 渲染線、Plotly / Matplotlib-Seaborn 可選渲染線、資料無涉圖庫 + 堆疊、原子寫入
+ 交易鎖、稽核 audit、自測、CLI。原始各引擎零改動(只增不減);外部引擎以「橋」發現而非改寫。

治理(悉出自上傳冊,零發明):
  • 圖規 SSOT:VIA_VAP_All_Chart_Specs_v018.csv 40 canonical(v017→v018 40/40 一致;APPEND_ONLY_VERSION_ARCHIVE_RESTORE)
  • 圖規鎖:單軸 4 間隔 5 刻度;雙軸各 5 刻度 4 間隔、同 tick 數、不同單位各自步距;範圍包住極值且盡量緊
  • 合法步距:v018/圖規守衛族 2 / 2.5 / 5 × 10ⁿ(10 = 下一十進位);v2.3 依操作員保留 1.25 → 1.25 / 2 / 2.5 / 5 × 10ⁿ
      本檔預設 family="v23"(超集,v2.3.1 UAT 通過);family="v018" 供守衛對勘。格式器保留必要尾零(1.25 / 2.50)。
  • 視覺鎖(併軌案 方案 A 核准 2026-08-04):vap_spec v1.0.x 為唯一視覺真相 → 線 0.9 / 線下 0.75(陰影 0.5)/ 柱 0.6 · 密 0.8 / 事件 0.3;
      Seaborn 垂直圖組 v2.3.1 為獨立域(線寬 1.65、alpha .82、柱 .75、面積 .5);Macro Dashboard Seaborn 0.80 獨立域 —— 三域互不覆寫。
  • 批330 資料律:TA-Lib 及所有繪圖價格一律還原價 adj_close(裸 close 需 allow_raw=True);成交量一律扣除當沖成交量。
  • 缺值律(v2.3 §6.1):價格可 ffill;Volume 不 ffill、不 interpolate、不補零;不新增休市日。
  • 標準高度:420 px × 倍數(0.25–4.0,步進 0.25);Candlestick = 一個邏輯圖、兩個實體單軸 panel 75% / 25%,共享 X,不用 twinx / secondary_y。
  • 大資料:render_max_points 預設 5000;line/area/step 用多序列首尾極值包絡;candlestick 用連續桶 OHLCV;方法/列數入 audit。
  • 圖庫:資料無涉(data-free)schema、65,536 bytes 上限、秘密遮蔽;加入堆疊建立新 ID;寫入原子化 + 跨程序交易鎖。
  • 正本 via_autoplot_engine_v001:FILL_OPACITY=0.4(八站)→ v002 升級 0.75(PROMOTION_RECORD,canonical_mutation=false);
      本檔依方案 A 分項套用,正本檔零改動。

用法:
  python VAP_ENG016_AutoplotOne_v0100.py --selftest [--json out.json]
  python VAP_ENG016_AutoplotOne_v0100.py --axis -3 97 [--family v23|v018] [--include-zero]
  python VAP_ENG016_AutoplotOne_v0100.py --list-charts [--group 統計分布]
  python VAP_ENG016_AutoplotOne_v0100.py --check-spec spec.json
  python VAP_ENG016_AutoplotOne_v0100.py --demo --out ./vap_one_out [--formats svg,html,png,pdf]
  python VAP_ENG016_AutoplotOne_v0100.py --render config.json --out DIR [--formats ...] [--profile vap_spec_v1|seaborn_stack_v23]
  python VAP_ENG016_AutoplotOne_v0100.py --lanes | --bridge-scan <VAP root>
所有寫入只進 --out 之下的 RUN_<ts> 新目錄;不修改任何輸入;UTF-8 無 BOM;ledger 只增。
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import math
import os
import random
import re
import sqlite3
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable, Iterable

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(graceful 零行為變更) =====
try:
    _sa_p = Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

VERSION = "v0100"
ENGINE_ID = "VAP_ENG016_AutoplotOne"
SELFTEST_CONTRACT = "VIA_VAP_ONE_SELFTEST/0100"
AUDIT_CONTRACT = "VIA-VAP-DASHBOARD-COMPLIANCE/1.0"
LIBRARY_SCHEMA = "VIA-VAP-CHART-LIBRARY/2.3"
STACK_SCHEMA = "VIA-VAP-STACK-CONFIG/2.3"

# 來源冊(SHA256 前 16 碼;上傳原件,零改動)
PROVENANCE = {
 "note": "上傳原件 SHA256 前 16 碼;原件零改動(canonical_mutation=false);本檔為整合新檔",
 "sources": {
  "VAP_ENG001_AutoplotEngineChartlib_v007.py": "E7D6ACC96A15EE42",
  "VAP_ENG002_AutoplotEngine_v001.py": "DC5697DB529F9E72",
  "VAP_ENG003_AutoplotSeabornPlotly_v0100.py": "EACF35E0274C83A4",
  "via_autoplot_engine_v001.py": "C7D7CA8A6DDD2503",
  "vap_seaborn_stack_generator.py(v2.3.1)": "E6C448BD72E8C1B7",
  "vap_panel_model.py(v2.3.1)": "5F42DB2C3B9F1FEB",
  "vap_render_optimizer.py(v2.3.1)": "32273B98CA8DA7F4",
  "vap_chart_library.py(v2.3.1)": "E9E11A7C7B0E029F",
  "vap_atomic_io.py(v2.3.1)": "2935AA15402A7C2D",
  "vap_defaults.json(v2.3.1)": "2F552A0DF3EF906E",
  "vap_data_runtime_v025.py": "DD1AD427CED59933",
  "vap_chart_registry_v025.json": "0BE85177F71E4A41"
 },
 "promotion_record": {
  "unit": "UNIT03_v0113_PROMOTION",
  "repair": "eight-site 0.4->0.75 (v0111R2 adjudication, v0112 guarded trial all green)",
  "canonical_mutation": False,
  "scope": "new file only"
 },
 "harmonization": "ChartSpecONE ↔ vap_spec 併軌案 v001 方案 A 已核准 2026-08-04(vap_spec v1.0.x 唯一視覺真相;Macro Seaborn 0.80 獨立域;Seaborn 圖組 v2.3.1 獨立域)",
 "uat_v231": {
  "date": "2026-09-02",
  "tests": "155 passed / 0 failed / 3 skipped",
  "png": "4720×4905 @300DPI",
  "concurrency": "12-way config+gallery append OK",
  "render_max_points": 5000
 }
}

# ------------------------------------------------------------------ 常數 · 契約
TICK_COUNT = 5
INTERVALS = TICK_COUNT - 1
TOL = 1e-6
STEP_FAMILIES = {"v018": (1.0, 2.0, 2.5, 5.0, 10.0), "v23": (1.25, 2.0, 2.5, 5.0, 10.0)}
DEFAULT_FAMILY = "v23"
STANDARD_PANEL_HEIGHT_PX = 420
MIN_HEIGHT_RATIO, MAX_HEIGHT_RATIO, HEIGHT_RATIO_STEP = 0.25, 4.0, 0.25
CANDLESTICK_PRICE_FRACTION, CANDLESTICK_VOLUME_FRACTION = 0.75, 0.25
RENDER_MAX_POINTS = 5000
MAX_ROWS = 500_000
MAX_CHART_SPEC_BYTES = 65_536
MAX_X_TICKS = 10

VISUAL_PROFILES = {
    "vap_spec_v1": {"domain": "SVG / Chart Library(併軌案 方案 A 唯一視覺真相)", "line_width": 1.0, "line_opacity": 0.9,
                    "area_alpha": 0.75, "area_alpha_shadow": 0.5, "bar_alpha": 0.6, "bar_alpha_dense": 0.8, "event_alpha": 0.3,
                    "palette": "snsDeep", "corr": "diverging15/zmid0/dtick0.05"},
    "seaborn_stack_v23": {"domain": "Seaborn 垂直圖組 v2.3.1(獨立域)", "line_width": 1.65, "line_opacity": 0.82,
                          "area_alpha": 0.5, "bar_alpha": 0.75, "secondary_alpha": 0.88, "secondary_line_width": 1.35,
                          "bar_width_ratio": 0.92, "candle_width_ratio": 0.88, "bar_gap_ratio": 0.22,
                          "up_color": "#D62728", "down_color": "#2CA02C"},
    "macro_dashboard_seaborn": {"domain": "Macro Dashboard Seaborn(獨立域)", "bar_alpha": 0.80},
}
DEFAULT_PROFILE = "vap_spec_v1"

TOKENS = {"bg": "#f5f4f0", "surface": "#ffffff", "paper2": "#fafaf8", "border": "#dbd9d3", "soft": "#ecebe6",
          "ink": "#1e1d1a", "ink2": "#33403f", "muted": "#6b6860", "muted2": "#9c9890"}
VIA_COMBO = ["#c96b5a", "#c4943a", "#5a9e6f", "#439a9a", "#4c78a8", "#7a6daa"]          # Chart Library Builder 固定色序
SNS_DEEP = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD"]
SERIES_COLORS = {"AdjClose": "#4C78A8", "Adj Close": "#4C78A8", "MA20": "#F28E2B", "Volume": "#76B7B2",
                 "Foreign": "#59A14F", "Trust": "#F28E2B", "Dealer": "#8FA6CF"}
UP_COLOR, DOWN_COLOR = "#D62728", "#2CA02C"                                                 # 台股紅漲綠跌

# 40 canonical 圖規(VIA_VAP_All_Chart_Specs_v018.csv 精簡列)
CHART_REGISTRY: list[dict] = [{"code":"VAP-CH-01","id":"line","zh":"折線圖","en":"Line","group":"單軸 Single-Axis","axes":"1","mode":"SINGLE","shape":"series[]","fields":"date|value","rule":"多序列趨勢；線寬 1、Opacity 0.9","renderer":"go.Scatter(mode=lines)"},{"code":"VAP-CH-02","id":"area","zh":"面積折線","en":"Area","group":"單軸 Single-Axis","axes":"1","mode":"SINGLE","shape":"series","fields":"date|value","rule":"下方填色；areaUnderLine 0.75","renderer":"go.Scatter(fill=tozeroy)"},{"code":"VAP-CH-03","id":"bar","zh":"直條圖","en":"Bar","group":"單軸 Single-Axis","axes":"1","mode":"SINGLE","shape":"categorical","fields":"label|value","rule":"分類比較；Bar Face 0.6／Dense 0.8；格寬 92%、可見間距 ","renderer":"go.Bar"},{"code":"VAP-CH-04","id":"hbar","zh":"橫條圖","en":"H-Bar","group":"單軸 Single-Axis","axes":"1","mode":"SINGLE","shape":"categorical","fields":"label|value","rule":"長標籤排序比較；條高 92%、可見間距 8%","renderer":"go.Bar(orientation=h)"},{"code":"VAP-CH-05","id":"scatter","zh":"散點圖","en":"Scatter","group":"單軸 Single-Axis","axes":"1","mode":"SINGLE","shape":"xy","fields":"x|y","rule":"關聯與離群值辨識","renderer":"go.Scatter(mode=markers)"},{"code":"VAP-CH-06","id":"sarea","zh":"堆疊面積","en":"Stacked Area","group":"堆疊 Stacked","axes":"1","mode":"SINGLE","shape":"series[]","fields":"date|value|group","rule":"同一時間軸顯示組成變化","renderer":"go.Scatter(stackgroup)"},{"code":"VAP-CH-07","id":"sbar","zh":"堆疊直條","en":"Stacked Bar","group":"堆疊 Stacked","axes":"1","mode":"SINGLE","shape":"categorical[]","fields":"label|value|group","rule":"外部格寬 92%、可見間距 8%；同柱堆疊段不留縫","renderer":"go.Bar(barmode=stack)"},{"code":"VAP-CH-08","id":"sbar100","zh":"百分比堆疊","en":"100% Stacked","group":"堆疊 Stacked","axes":"1","mode":"SINGLE","shape":"categorical[]","fields":"label|value|group","rule":"每期總和正規化為 100%","renderer":"go.Bar(barnorm=percent)"},{"code":"VAP-CH-09","id":"multi","zh":"個別小圖","en":"Small Multiples","group":"個別 Small Multiples","axes":"1","mode":"SINGLE","shape":"series[]","fields":"date|value|panel","rule":"預設 2×2；同尺度或清楚標示各尺度","renderer":"make_subplots"},{"code":"VAP-CH-10","id":"gbar","zh":"並列直條","en":"Grouped Bar","group":"個別 Small Multiples","axes":"1","mode":"SINGLE","shape":"categorical[]","fields":"label|value|group","rule":"群組使用 92% 格寬；群內與群間均保留最小可見空隙","renderer":"go.Bar(barmode=group)"},{"code":"VAP-CH-11","id":"dline","zh":"底色面積 × 對比折線","en":"Area × Line","group":"雙軸 Dual-Axis","axes":"2","mode":"DUAL_LOCKED","shape":"series×2","fields":"date|left|right","rule":"底色序列置右軸 α0.75；折線置左軸 lw1","renderer":"make_subplots(secondary_y)"},{"code":"VAP-CH-12","id":"dbarline","zh":"條 + 線 雙軸","en":"Bar × Line","group":"雙軸 Dual-Axis","axes":"2","mode":"DUAL_LOCKED","shape":"mixed","fields":"date|bar|line","rule":"Bar 使用 92% 格寬／8% 可見間距；Bar 與 Line 使用互補色且左","renderer":"go.Bar + go.Scatter"},{"code":"VAP-CH-13","id":"evtmx","zh":"事件矩陣","en":"Event Matrix","group":"進階 Advanced","axes":"1","mode":"SINGLE","shape":"series+events","fields":"date|value|events[]","rule":"垂直虛線 0.8／0.8；陰影 0.3；無水平線","renderer":"add_vline + add_vrect"},{"code":"VAP-CH-14","id":"corrheat","zh":"相關熱力圖","en":"Masked Corr","group":"進階 Advanced","axes":"0","mode":"NONE","shape":"matrix","fields":"corr","rule":"下三角遮罩；zmid 0；15 級雙向色階","renderer":"go.Heatmap"},{"code":"VAP-CH-15","id":"brush","zh":"區間量測","en":"Brush Measure","group":"進階 Advanced","axes":"1","mode":"SINGLE","shape":"series","fields":"date|value","rule":"High／Low／MaxDD／Duration／Recovery","renderer":"drag select"},{"code":"VAP-CH-16","id":"map","zh":"地圖 × 數據","en":"Map","group":"進階 Advanced","axes":"0","mode":"NONE","shape":"geo","fields":"region|value|change","rule":"漲跌以上下三角標示；圓形旗標","renderer":"Leaflet / scattergeo"},{"code":"VAP-CH-17","id":"roll","zh":"滾動報酬","en":"Rolling Returns","group":"滾動績效 Rolling Performance","axes":"1","mode":"SINGLE","shape":"series","fields":"date|return","rule":"固定窗口並標示年化方法","renderer":"rolling return"},{"code":"VAP-CH-18","id":"rollcorr","zh":"滾動相關","en":"Rolling Correlation","group":"滾動績效 Rolling Performance","axes":"1","mode":"SINGLE","shape":"series×2","fields":"date|a|b","rule":"相關軸固定 −1～1；台美採 lead-lag","renderer":"rolling correlation"},{"code":"VAP-CH-19","id":"rollsharpe","zh":"移動夏普","en":"Trailing Sharpe","group":"滾動績效 Rolling Performance","axes":"1","mode":"SINGLE","shape":"series","fields":"date|sharpe","rule":"無風險利率與年化頻率必須標示","renderer":"rolling sharpe"},{"code":"VAP-CH-20","id":"sortino","zh":"Sharpe × Sortino 比較","en":"Sharpe × Sortino","group":"滾動績效 Rolling Performance","axes":"2","mode":"DUAL_LOCKED","shape":"series×2","fields":"date|sharpe|sortino","rule":"左 Sharpe、右 Sortino、相同格數","renderer":"secondary_y lines"},{"code":"VAP-CH-21","id":"radar","zh":"風險雷達","en":"Risk Radar","group":"滾動績效 Rolling Performance","axes":"0","mode":"NONE","shape":"radial","fields":"metric|value|benchmark","rule":"基準為外圈虛線；填色 α0.3","renderer":"go.Scatterpolar"},{"code":"VAP-CH-22","id":"alpha","zh":"Alpha 策略","en":"Alpha Strategy","group":"滾動績效 Rolling Performance","axes":"2","mode":"DUAL_LOCKED","shape":"series×3","fields":"date|strategy|benchmark|excess","rule":"累積績效左軸；超額報酬右軸直條（漲紅跌綠）；0 軸紅線","renderer":"lines + excess bars"},{"code":"VAP-CH-23","id":"econcal","zh":"經濟日曆","en":"Economic Calendar","group":"滾動績效 Rolling Performance","axes":"0","mode":"NONE","shape":"events","fields":"date|event|importance|actual|forecast|previous","rule":"重要度紅黃綠三階；Actual／Forecast／Previous 並列","renderer":"calendar table"},{"code":"VAP-CH-24","id":"consensus","zh":"共識總覽","en":"Consensus Overview","group":"基本面 Consensus","axes":"1","mode":"SINGLE","shape":"table","fields":"dilutedEPS|targetPrice|rating|analystCount|forwardPER|forwardPBR","rule":"綠黃紅 Spectrum；目標價取左右最長","renderer":"indicator + bullet"},{"code":"VAP-CH-25","id":"backtest","zh":"回測驗證","en":"Backtest Validation","group":"滾動績效 Rolling Performance","axes":"2","mode":"DUAL_LOCKED","shape":"matrix+series","fields":"lag|rankIC|tStat|pValue","rule":"Rank-IC 直條＋t 統計折線；|t|=1.96 基準線","renderer":"bar + line + hline"},{"code":"VAP-CH-26","id":"intraday","zh":"當日走勢 + 成交量","en":"Intraday + Volume","group":"技術分析 Technical","axes":"2","mode":"DUAL_LOCKED","shape":"ohlcv","fields":"time|price|volume","rule":"上下兩列 .72／.28；shared_xaxes","renderer":"make_subplots rows=2"},{"code":"VAP-CH-27","id":"candle","zh":"K線 × SMA/EMA/BB × Volume","en":"Candlestick TA","group":"技術分析 Technical","axes":"2","mode":"DUAL_LOCKED","shape":"ohlcv","fields":"date|open|high|low|close|volume","rule":"close ≥ open：K棒、影線、Volume 全部使用上漲紅 #c96b5","renderer":"go.Candlestick + indicators"},{"code":"VAP-CH-28","id":"spotfut","zh":"現貨 × 期貨","en":"Spot × Futures","group":"技術分析 Technical","axes":"1","mode":"SINGLE","shape":"series[]","fields":"date|spot|futures","rule":"同色：現貨實線、期貨虛線；基差標籤 ≥9px","renderer":"normalized lines"},{"code":"VAP-CH-29","id":"hist","zh":"直方圖","en":"Histogram","group":"統計分布 Statistical","axes":"1","mode":"SINGLE","shape":"distribution","fields":"value","rule":"Freedman-Diaconis 或 10 組自動分箱；Bar 間距保留 8%","renderer":"Plotly Histogram · VAP Seaborn SVG"},{"code":"VAP-CH-30","id":"box","zh":"箱型圖","en":"Box Plot","group":"統計分布 Statistical","axes":"1","mode":"SINGLE","shape":"distribution[]","fields":"value|group?","rule":"顯示 Q1、Median、Q3、Whisker 與 Outlier；禁止截斷離群","renderer":"Plotly Box · VAP Seaborn SVG"},{"code":"VAP-CH-31","id":"violin","zh":"小提琴圖","en":"Violin","group":"統計分布 Statistical","axes":"1","mode":"SINGLE","shape":"distribution[]","fields":"value|group?","rule":"KDE 對稱寬度；內嵌 Median 與 IQR；填色 Opacity 0.5","renderer":"Plotly Violin · VAP Seaborn SVG"},{"code":"VAP-CH-32","id":"kde","zh":"核密度分布","en":"KDE Distribution","group":"統計分布 Statistical","axes":"1","mode":"SINGLE","shape":"distribution[]","fields":"value|group?","rule":"Gaussian KDE；Bandwidth 來源必須可追溯；面積正規化為 1","renderer":"Plotly Scatter fill · VAP Seaborn SVG"},{"code":"VAP-CH-33","id":"reg","zh":"迴歸散點圖","en":"Regression Plot","group":"統計分布 Statistical","axes":"1","mode":"SINGLE","shape":"xy","fields":"x|y","rule":"Scatter 加 OLS 迴歸線；顯示 n、slope、R²；不可暗示因果","renderer":"Plotly Scatter · VAP Seaborn SVG"},{"code":"VAP-CH-34","id":"density","zh":"雙變量密度圖","en":"Density Contour","group":"統計分布 Statistical","axes":"2","mode":"DUAL_LOCKED","shape":"xy","fields":"x|y","rule":"2D density contour 加低透明散點；色階使用核准 Seaborn","renderer":"Plotly Histogram2dContour · VAP Seaborn SVG"},{"code":"VAP-CH-35","id":"pairgrid","zh":"配對關係矩陣","en":"Pair Grid","group":"統計分布 Statistical","axes":"0","mode":"NONE","shape":"numeric[]","fields":"numeric≥3","rule":"對角線顯示分布；下三角顯示散點；上三角顯示相關係數","renderer":"Plotly Splom · VAP Seaborn SVG"},{"code":"VAP-CH-36","id":"facet","zh":"分面網格","en":"Facet Grid","group":"統計分布 Statistical","axes":"1","mode":"SINGLE","shape":"series[]+facet","fields":"x|y|facet","rule":"所有面板共用色盤與尺度規約；預設 2×2；標題不得重疊；row／col／hue ","renderer":"Plotly Subplots · VAP Seaborn SVG"},{"code":"VAP-CH-37","id":"ecdf","zh":"經驗累積分布","en":"ECDF","group":"統計分布 Statistical","axes":"1","mode":"SINGLE","shape":"distribution[]","fields":"value|group?","rule":"排序後以 proportion 顯示累積機率；不需分箱或 bandwidth；終","renderer":"Plotly Step Line · VAP Seaborn SVG"},{"code":"VAP-CH-38","id":"rug","zh":"邊際刻度圖","en":"Rug Plot","group":"統計分布 Statistical","axes":"1","mode":"SINGLE","shape":"distribution[]","fields":"value|group?","rule":"每筆觀測以等長刻度顯示；僅作分布輔助層，不得用高度暗示頻數","renderer":"Plotly Marker Ticks · VAP Seaborn SVG"},{"code":"VAP-CH-39","id":"resid","zh":"迴歸殘差圖","en":"Residual Plot","group":"統計分布 Statistical","axes":"1","mode":"SINGLE","shape":"xy","fields":"x|y","rule":"先移除簡單線性迴歸，再繪 residual；固定 y=0 基準；結構性殘差表示線","renderer":"Plotly Scatter + Zero Line · VAP Seaborn SVG"},{"code":"VAP-CH-40","id":"joint","zh":"聯合分布網格","en":"Joint Grid","group":"統計分布 Statistical","axes":"2","mode":"DUAL_LOCKED","shape":"xy+marginals","fields":"x|y|group?","rule":"中央顯示二變量關係；上方與右側顯示同步邊際分布；共同篩選、色盤與樣本範圍","renderer":"Plotly Cartesian Domains · VAP Seaborn SVG"}]
STACK_TYPES = ("line", "area", "bar", "scatter", "step", "stacked_bar", "stacked_bar_100", "stacked_area", "heatmap", "candlestick", "dual")
STACK_TYPE_TO_CODE = {"line": "VAP-CH-01", "area": "VAP-CH-02", "bar": "VAP-CH-03", "scatter": "VAP-CH-05", "step": "VAP-CH-01",
                      "stacked_area": "VAP-CH-06", "stacked_bar": "VAP-CH-07", "stacked_bar_100": "VAP-CH-08",
                      "dual": "VAP-CH-11", "heatmap": "VAP-CH-14", "candlestick": "VAP-CH-27"}

# 批330 資料律
ADJ_PRICE_PATTERN = re.compile(r"adj", re.I)
VOLUME_PATTERN = re.compile(r"vol|成交量|turnover_units", re.I)
VOLUME_EX_DAYTRADE_PATTERN = re.compile(r"ex.?d(ay)?t|exdt|扣當沖|net_?vol|ex_daytrade", re.I)
SECRET_KEY_PATTERN = re.compile(r"(password|passwd|pwd|secret|token|api[_-]?key|private[_-]?key|credential)", re.I)


def utc_now_text() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def sha12(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:12]


# ------------------------------------------------------------------ 圖規鎖 · 軸契約(v2.3.1 compute_locked_ticks 逐字移植,去 numpy)
def nice_step_candidates(rough_step: float, family: str = DEFAULT_FAMILY) -> list[float]:
    mantissas = STEP_FAMILIES.get(family, STEP_FAMILIES[DEFAULT_FAMILY])
    safe_rough = max(abs(float(rough_step)), sys.float_info.epsilon)
    exponent = int(math.floor(math.log10(safe_rough)))
    cands = {mantissa * (10.0 ** power) for power in range(exponent - 2, exponent + 4) for mantissa in mantissas}
    return sorted(step for step in cands if step > 0)


def compute_locked_ticks(minimum: float, maximum: float, tick_count: int = TICK_COUNT,
                         include_zero: bool = False, family: str = DEFAULT_FAMILY) -> list[float]:
    """單軸 5 刻度 4 間隔;合法步距;範圍包住極值且盡量緊(slack 最小);起點量子 step/4 允許小數 offset。"""
    if tick_count < 2:
        raise ValueError("tick_count 必須至少為 2。")
    minimum, maximum = float(minimum), float(maximum)
    if not math.isfinite(minimum) or not math.isfinite(maximum):
        return [i / (tick_count - 1) for i in range(tick_count)]
    if minimum > maximum:
        minimum, maximum = maximum, minimum
    nonneg, nonpos = minimum >= 0, maximum <= 0
    if minimum == maximum:
        padding = abs(minimum) * 0.1 or 1.0
        minimum -= padding
        maximum += padding
    if include_zero:
        minimum, maximum = min(minimum, 0.0), max(maximum, 0.0)
    interval_count = tick_count - 1
    rough = (maximum - minimum) / interval_count
    best: tuple[float, float, float] | None = None
    for step in nice_step_candidates(rough, family):
        span = interval_count * step
        quantum = step / 4.0
        s_min = int(math.ceil((maximum - span) / quantum - 1e-12))
        s_max = int(math.floor(minimum / quantum + 1e-12))
        for idx in range(s_min, s_max + 1):
            lower = idx * quantum
            upper = lower + span
            if lower > minimum + 1e-10 or upper < maximum - 1e-10:
                continue
            if include_zero and not (lower <= 0 <= upper):
                continue
            if include_zero and nonneg and not math.isclose(lower, 0.0, abs_tol=step * 1e-10):
                continue
            if include_zero and nonpos and not math.isclose(upper, 0.0, abs_tol=step * 1e-10):
                continue
            slack = (minimum - lower) + (upper - maximum)
            center = abs(((lower + upper) / 2) - ((minimum + maximum) / 2))
            score = slack + center * 0.01
            if best is None or score < best[0] - 1e-12 or (abs(score - best[0]) <= 1e-12 and step < best[1]):
                best = (score, step, lower)
        if best is not None and step > rough * 10:
            break
    if best is None:
        step = nice_step_candidates(rough, family)[0]
        lower = math.floor(minimum / step) * step
    else:
        _s, step, lower = best
    ticks = [lower + k * step for k in range(tick_count)]
    return [0.0 if math.isclose(t, 0.0, abs_tol=step * 1e-10) else float(f"{t:.12g}") for t in ticks]


def mantissa_of(step: float) -> float:
    if step <= 0 or not math.isfinite(step):
        return float("nan")
    return float(f"{step / (10.0 ** math.floor(math.log10(step) + 1e-9)):.6g}")


def axis_checks(ticks: list[float], data_min: float, data_max: float, family: str = DEFAULT_FAMILY) -> dict:
    """合規四檢(VIA-VAP-DASHBOARD-COMPLIANCE PropertyChecks):five_ticks / uniform / legal_mantissa / covers。"""
    diffs = [ticks[i + 1] - ticks[i] for i in range(len(ticks) - 1)] if len(ticks) > 1 else []
    step = diffs[0] if diffs else 0.0
    uniform = bool(diffs) and all(abs(d - step) <= TOL * max(1.0, abs(step)) for d in diffs)
    legal = {1.0: True}
    fam = set(STEP_FAMILIES.get(family, STEP_FAMILIES[DEFAULT_FAMILY])) | {1.0}
    m = mantissa_of(step) if step > 0 else float("nan")
    lo, hi = (min(data_min, data_max), max(data_min, data_max))
    return {"five_ticks": len(ticks) == TICK_COUNT, "uniform": uniform,
            "legal_mantissa": (not math.isnan(m)) and any(abs(m - f) <= 1e-6 for f in fam),
            "covers": bool(ticks) and ticks[0] <= lo + TOL and ticks[-1] >= hi - TOL,
            "step": step, "mantissa": m}


def decimal_places_for_step(step: float | None, minimum: int = 0) -> int:
    if step is None or not math.isfinite(step) or step == 0:
        return minimum
    text = f"{round(abs(float(step)), 12):.12f}".rstrip("0").rstrip(".")
    decimals = len(text.split(".", 1)[1]) if "." in text else 0
    return max(minimum, min(decimals, 8))


def format_tick_fixed(value: float, decimals: int) -> str:
    """保留必要尾零(同軸 1.25 / 2.50),避免二進位浮點雜訊。"""
    if value == 0:
        return "0" if decimals == 0 else f"{0:.{decimals}f}"
    return f"{value:.{decimals}f}"


def magnitude_formatter(value: float) -> str:
    a = abs(value)
    if a >= 1e9:
        return f"{value / 1e9:.1f}B"
    if a >= 1e6:
        return f"{value / 1e6:.1f}M"
    if a >= 1e3:
        return f"{value / 1e3:.1f}K"
    return f"{value:.1f}"


def locked_axis(data_min: float, data_max: float, include_zero: bool = False, family: str = DEFAULT_FAMILY,
                y_format: str = "auto") -> dict:
    ticks = compute_locked_ticks(data_min, data_max, TICK_COUNT, include_zero, family)
    chk = axis_checks(ticks, data_min, data_max, family)
    dec = max([decimal_places_for_step(chk["step"])] + [decimal_places_for_step(t) for t in ticks])   # v2.3.1:step 與刻度值皆計入,小數 offset 不得顯示成整數
    labels = [magnitude_formatter(t) if y_format == "magnitude" else format_tick_fixed(t, dec) for t in ticks]
    return {"ticks": ticks, "labels": labels, "step": chk["step"], "mantissa": chk["mantissa"], "decimals": dec,
            "min": ticks[0], "max": ticks[-1], "family": family, "checks": {k: chk[k] for k in ("five_ticks", "uniform", "legal_mantissa", "covers")}}


# ------------------------------------------------------------------ 標準高度 · K 線 75/25 · 堆疊列展開(v2.3.1 panel model 移植)
def validate_height_ratio(value: Any) -> float:
    try:
        v = float(value)
    except Exception as exc:
        raise ValueError(f"height_ratio 非數字:{value!r}") from exc
    if not math.isfinite(v) or v < MIN_HEIGHT_RATIO - 1e-9 or v > MAX_HEIGHT_RATIO + 1e-9:
        raise ValueError(f"height_ratio 須在 {MIN_HEIGHT_RATIO}–{MAX_HEIGHT_RATIO}:{value!r}")
    if abs((v / HEIGHT_RATIO_STEP) - round(v / HEIGHT_RATIO_STEP)) > 1e-9:
        raise ValueError(f"height_ratio 須為 {HEIGHT_RATIO_STEP} 步進:{value!r}")
    return round(v, 4)


def normalize_height_ratio(value: Any, default: float = 1.0) -> float:
    try:
        v = float(value)
    except Exception:
        return default
    if not math.isfinite(v):
        return default
    v = min(MAX_HEIGHT_RATIO, max(MIN_HEIGHT_RATIO, v))
    return round(round(v / HEIGHT_RATIO_STEP) * HEIGHT_RATIO_STEP, 4)


def height_ratio_to_pixels(ratio: float, base: int = STANDARD_PANEL_HEIGHT_PX) -> int:
    return int(round(validate_height_ratio(ratio) * base))


def candlestick_height_fractions(chart: dict) -> tuple[float, float]:
    p = float(chart.get("price_height_fraction", CANDLESTICK_PRICE_FRACTION))
    v = float(chart.get("volume_height_fraction", CANDLESTICK_VOLUME_FRACTION))
    if not (math.isfinite(p) and math.isfinite(v)) or p <= 0 or v <= 0 or not math.isclose(p + v, 1.0, abs_tol=1e-9):
        raise ValueError("K 線 price_height_fraction 與 volume_height_fraction 必須大於 0 且合計為 1。")
    return p, v


def expand_render_rows(charts: list[dict]) -> list[dict]:
    """邏輯圖 → 實體單軸列;candlestick 展開為 價格(75%)+ 成交量(25%)兩列,共享 X。"""
    rows: list[dict] = []
    for chart in charts:
        if str(chart.get("type", "")).lower() != "candlestick":
            row = json.loads(json.dumps(chart, ensure_ascii=False))
            row["_render_role"] = "chart"
            row["_logical_chart_id"] = str(chart.get("id", ""))
            rows.append(row)
            continue
        pf, vf = candlestick_height_fractions(chart)
        total = float(chart.get("height_ratio", 1.0))
        price = json.loads(json.dumps(chart, ensure_ascii=False))
        price.update({"_render_role": "candlestick_price", "_logical_chart_id": str(chart.get("id", "")), "axis_mode": "single",
                      "secondary_y": [], "height_ratio": total * pf})
        volume = json.loads(json.dumps(chart, ensure_ascii=False))
        volume.update({"_render_role": "candlestick_volume", "_logical_chart_id": str(chart.get("id", "")), "type": "bar",
                       "title": str(chart.get("volume_title") or f"{chart.get('title') or chart.get('id')} · Volume"),
                       "axis_mode": "single", "y": [str(chart.get("volume", "Volume"))], "secondary_y": [],
                       "y_format": str(chart.get("secondary_y_format", "magnitude")), "axis_zero_policy": "include",
                       "show_zero_line": False, "show_legend": False, "height_ratio": total * vf})
        rows.extend([price, volume])
    return rows


def reorder_charts_by_drag(charts: list[dict], chart_id: str, new_position: int) -> list[dict]:
    ids = [str(c.get("id")) for c in charts]
    if chart_id not in ids:
        raise KeyError(f"堆疊無此 id:{chart_id}")
    items = list(charts)
    moving = items.pop(ids.index(chart_id))
    new_position = max(0, min(len(items), int(new_position)))
    items.insert(new_position, moving)
    return items


# ------------------------------------------------------------------ 資料層(零依賴;Parquet/DuckDB 可選且誠實)
_DATE_PATTERNS = ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y/%m", "%Y%m%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S")


def parse_date(value: Any) -> _dt.datetime | None:
    if isinstance(value, _dt.datetime):
        return value
    text = str(value).strip()
    for pat in _DATE_PATTERNS:
        try:
            return _dt.datetime.strptime(text, pat)
        except ValueError:
            continue
    return None


def parse_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(float(value)) else None
    text = str(value).strip().replace(",", "")
    if text in ("", "-", "—", "NaN", "nan", "null", "None"):
        return None
    try:
        f = float(text)
        return f if math.isfinite(f) else None
    except ValueError:
        return None


def is_volume_column(name: str) -> bool:
    return bool(VOLUME_PATTERN.search(str(name)))


def pick_price(columns: Iterable[str], allow_raw: bool = False) -> str:
    """批330:價格一律還原價;裸 close 需 allow_raw=True,否則誠實 FAIL。"""
    cols = [str(c) for c in columns]
    for c in cols:
        if ADJ_PRICE_PATTERN.search(c) and re.search(r"close", c, re.I):
            return c
    for c in cols:
        if ADJ_PRICE_PATTERN.search(c):
            return c
    raw = [c for c in cols if re.search(r"^close$|_close$|收盤", c, re.I)]
    if raw and allow_raw:
        return raw[0]
    raise ValueError("批330 資料律:未找到還原價欄(adj_close);裸 close 需 allow_raw=True")


def volume_ex_daytrade_status(columns: Iterable[str]) -> dict:
    vols = [str(c) for c in columns if is_volume_column(c)]
    marked = [c for c in vols if VOLUME_EX_DAYTRADE_PATTERN.search(c)]
    return {"volume_columns": vols, "ex_daytrade_marked": marked,
            "status": "OK" if marked else ("WARN" if vols else "N/A"),
            "note": "批330:成交量一律扣除當沖;欄名未標示 ex-daytrade 時無法以名稱證明(誠實 WARN)" if vols and not marked else ""}


def rows_from_csv(path: Path, max_rows: int = MAX_ROWS) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        rows = []
        for i, row in enumerate(csv.DictReader(fh, dialect=dialect)):
            if i >= max_rows:
                break
            rows.append(dict(row))
        return rows


def rows_from_json(path: Path, max_rows: int = MAX_ROWS) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".jsonl":
        out = []
        for line in text.splitlines():
            if line.strip():
                out.append(json.loads(line))
                if len(out) >= max_rows:
                    break
        return out
    data = json.loads(text)
    if isinstance(data, dict):
        for key in ("rows", "data", "records"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
    return [r for r in data if isinstance(r, dict)][:max_rows]


def rows_from_sqlite(path: Path, table: str | None = None, max_rows: int = MAX_ROWS) -> tuple[str, list[dict]]:
    uri = f"file:{path.as_posix()}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        con.row_factory = sqlite3.Row
        if not table:
            names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view') ORDER BY name")]
            if not names:
                return "", []
            table = names[0]
        if not re.fullmatch(r"[A-Za-z0-9_\u4e00-\u9fff]+", table):
            raise ValueError(f"table 名稱不安全:{table!r}")
        cur = con.execute(f'SELECT * FROM "{table}" LIMIT ?', (int(max_rows),))
        return table, [dict(r) for r in cur.fetchall()]
    finally:
        con.close()


def rows_from_parquet(path: Path, max_rows: int = MAX_ROWS) -> list[dict]:
    """duckdb 優先 → pandas+pyarrow 後備 → 皆缺誠實 FAIL(ENG001 v007 律)。"""
    try:
        import duckdb  # type: ignore
        con = duckdb.connect()
        rel = con.execute(f"SELECT * FROM read_parquet(?) LIMIT {int(max_rows)}", [str(path)])
        cols = [d[0] for d in rel.description]
        return [dict(zip(cols, r)) for r in rel.fetchall()]
    except ImportError:
        pass
    try:
        import pandas as pd  # type: ignore
        return pd.read_parquet(path).head(max_rows).to_dict("records")
    except ImportError as exc:
        raise RuntimeError("Parquet 需要 duckdb 或 pandas+pyarrow:pip install duckdb 或 pip install pandas pyarrow") from exc


def load_rows(path: str | Path, table: str | None = None, max_rows: int = MAX_ROWS) -> tuple[str, list[dict]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(str(p))
    ext = p.suffix.lower()
    if ext in (".csv", ".tsv", ".txt"):
        return p.stem, rows_from_csv(p, max_rows)
    if ext in (".json", ".jsonl"):
        return p.stem, rows_from_json(p, max_rows)
    if ext in (".sqlite", ".sqlite3", ".db"):
        return rows_from_sqlite(p, table, max_rows)
    if ext in (".parquet", ".pq"):
        return p.stem, rows_from_parquet(p, max_rows)
    raise ValueError(f"不支援的資料源:{ext}")


def numeric_columns(rows: list[dict]) -> list[str]:
    if not rows:
        return []
    cols = list(rows[0].keys())
    out = []
    for c in cols:
        vals = [parse_number(r.get(c)) for r in rows[:200]]
        got = [v for v in vals if v is not None]
        if got and len(got) >= max(1, int(0.6 * len([v for v in vals if r_nonempty(v)]))):
            out.append(c)
    return out


def r_nonempty(v: Any) -> bool:
    return v is not None and str(v).strip() != ""


def x_column(rows: list[dict], preferred: str | None = None) -> str | None:
    if not rows:
        return None
    if preferred and preferred in rows[0]:
        return preferred
    for c in rows[0].keys():
        if re.search(r"date|time|日期|day", str(c), re.I):
            return c
    for c in rows[0].keys():
        if parse_date(rows[0].get(c)) is not None:
            return c
    return None


def apply_missing_policy(rows: list[dict], columns: list[str], policy: str, never_fill: Iterable[str] | None = None) -> list[dict]:
    """價格可 ffill/interpolate/zero;Volume 永不補值;drop 刪整列(只作用於 render-copy)。"""
    protected = {str(c) for c in (never_fill or [])} | {c for c in columns if is_volume_column(c)}
    out = [dict(r) for r in rows]
    fill_cols = [c for c in columns if c not in protected]
    if policy == "ffill":
        last: dict[str, float | None] = {c: None for c in fill_cols}
        for r in out:
            for c in fill_cols:
                v = parse_number(r.get(c))
                if v is None and last[c] is not None:
                    r[c] = last[c]
                elif v is not None:
                    last[c] = v
    elif policy == "interpolate":
        for c in fill_cols:
            vals = [parse_number(r.get(c)) for r in out]
            i = 0
            while i < len(vals):
                if vals[i] is None:
                    j = i
                    while j < len(vals) and vals[j] is None:
                        j += 1
                    if i > 0 and j < len(vals):
                        a, b = vals[i - 1], vals[j]
                        n = j - i + 1
                        for k in range(i, j):
                            vals[k] = a + (b - a) * (k - i + 1) / n
                    i = j
                else:
                    i += 1
            for r, v in zip(out, vals):
                if v is not None:
                    r[c] = v
    elif policy == "zero":
        for r in out:
            for c in fill_cols:
                if parse_number(r.get(c)) is None:
                    r[c] = 0.0
    elif policy == "drop":
        out = [r for r in out if all(parse_number(r.get(c)) is not None for c in columns)]
    return out


def quality_audit(rows: list[dict], date_col: str | None, numeric_cols: list[str], iqr_multiplier: float = 3.0) -> dict:
    invalid_dates = dup_dates = 0
    seen = set()
    if date_col:
        for r in rows:
            d = parse_date(r.get(date_col))
            if d is None:
                invalid_dates += 1
            else:
                key = d.date()
                if key in seen:
                    dup_dates += 1
                seen.add(key)
    missing = {c: sum(1 for r in rows if parse_number(r.get(c)) is None) for c in numeric_cols}
    outliers = {}
    for c in numeric_cols:
        vals = sorted(v for v in (parse_number(r.get(c)) for r in rows) if v is not None)
        if len(vals) >= 8:
            q1, q3 = vals[int(0.25 * (len(vals) - 1))], vals[int(0.75 * (len(vals) - 1))]
            iqr = q3 - q1
            lo, hi = q1 - iqr_multiplier * iqr, q3 + iqr_multiplier * iqr
            outliers[c] = sum(1 for v in vals if v < lo or v > hi)
    return {"rows": len(rows), "invalid_dates": invalid_dates, "duplicate_dates": dup_dates, "missing": missing, "outliers": outliers,
            "iqr_multiplier": iqr_multiplier, "volume_never_filled": True}


# ------------------------------------------------------------------ 大資料可稽核縮減(v2.3.1 render optimizer 移植)
def _bucket_bounds(length: int, bucket_count: int) -> list[tuple[int, int]]:
    bucket_count = max(1, min(length, bucket_count))
    edges = [int(round(i * length / bucket_count)) for i in range(bucket_count + 1)]
    return [(edges[i], edges[i + 1]) for i in range(bucket_count) if edges[i + 1] > edges[i]]


def optimize_envelope(rows: list[dict], series: list[str], max_points: int = RENDER_MAX_POINTS) -> tuple[list[dict], dict]:
    n = len(rows)
    if n <= max_points or not series:
        return rows, {"applied": False, "method": "none", "input_points": n, "output_points": n}
    worst = 2 + 2 * len(series)
    bucket_count = max(1, min(n, max_points // worst))
    keep: set[int] = set()
    while bucket_count >= 1:
        keep = set()
        for start, stop in _bucket_bounds(n, bucket_count):
            keep.update({start, stop - 1})
            for s in series:
                vals = [(parse_number(rows[i].get(s)), i) for i in range(start, stop)]
                got = [(v, i) for v, i in vals if v is not None]
                if got:
                    keep.add(min(got)[1])
                    keep.add(max(got)[1])
        if len(keep) <= max_points or bucket_count == 1:
            break
        bucket_count -= 1
    out = [rows[i] for i in sorted(keep)]
    return out, {"applied": True, "method": "multi_series_first_min_max_last_envelope", "bucket_count": bucket_count,
                 "input_points": n, "output_points": len(out), "max_points": max_points}


def optimize_candlestick(rows: list[dict], o: str, h: str, l: str, c: str, v: str | None, max_points: int = RENDER_MAX_POINTS) -> tuple[list[dict], dict]:
    n = len(rows)
    if n <= max_points:
        return rows, {"applied": False, "method": "none", "input_points": n, "output_points": n}
    out = []
    bounds = _bucket_bounds(n, max_points)
    for start, stop in bounds:
        seg = rows[start:stop]
        opens = [parse_number(r.get(o)) for r in seg]
        closes = [parse_number(r.get(c)) for r in seg]
        highs = [x for x in (parse_number(r.get(h)) for r in seg) if x is not None]
        lows = [x for x in (parse_number(r.get(l)) for r in seg) if x is not None]
        vols = [parse_number(r.get(v)) for r in seg] if v else []
        rec = dict(seg[0])
        rec[o] = next((x for x in opens if x is not None), None)
        rec[c] = next((x for x in reversed(closes) if x is not None), None)
        rec[h] = max(highs) if highs else None
        rec[l] = min(lows) if lows else None
        if v:
            rec[v] = None if any(x is None for x in vols) else sum(vols)   # 缺值保持缺值,不假填
        out.append(rec)
    return out, {"applied": True, "method": "contiguous_bucket_ohlcv_aggregate", "bucket_count": len(bounds),
                 "input_points": n, "output_points": len(out), "max_points": max_points}


# ------------------------------------------------------------------ 規格驗證(堆疊 chart / 站「圖規 JSON」)
def chart_code_lookup(code_or_id: str) -> dict | None:
    for c in CHART_REGISTRY:
        if c["code"] == code_or_id or c["id"] == code_or_id:
            return c
    return None


def validate_chart_spec(chart: dict, position: int = 0) -> list[str]:
    errs: list[str] = []
    ctype = str(chart.get("type", "")).lower()
    if ctype not in STACK_TYPES:
        errs.append(f"charts[{position}].type 非法:{ctype!r};合法 {STACK_TYPES}")
    if not chart.get("id"):
        errs.append(f"charts[{position}] 缺 id")
    try:
        validate_height_ratio(chart.get("height_ratio", 1.0))
    except ValueError as exc:
        errs.append(f"charts[{position}] {exc}")
    axis_mode = str(chart.get("axis_mode", "auto"))
    if axis_mode not in ("auto", "single", "dual"):
        errs.append(f"charts[{position}].axis_mode 非法:{axis_mode!r}")
    if axis_mode == "single" and chart.get("secondary_y"):
        errs.append(f"charts[{position}] axis_mode=single 不得殘留 secondary_y(v2.3.1 修正律)")
    if ctype == "candlestick":
        for k in ("open", "high", "low", "close"):
            if not chart.get(k):
                errs.append(f"charts[{position}] candlestick 缺 {k}")
        try:
            candlestick_height_fractions(chart)
        except ValueError as exc:
            errs.append(f"charts[{position}] {exc}")
        for k in ("open", "high", "low", "close"):
            if chart.get(k) and not ADJ_PRICE_PATTERN.search(str(chart.get(k))) and not chart.get("allow_raw"):
                errs.append(f"charts[{position}] 批330:{k}={chart.get(k)!r} 非還原價欄;需 allow_raw=true")
    elif ctype != "heatmap" and not chart.get("y"):
        errs.append(f"charts[{position}] 缺 y[]")
    if str(chart.get("missing", "none")) not in ("none", "ffill", "interpolate", "zero", "drop"):
        errs.append(f"charts[{position}].missing 非法")
    return errs


def validate_vap_json(obj: Any) -> dict:
    """站「VAP 圖規 JSON」:x / series / 方法論欄(+ code / axisMode / price_field / volume_field)。"""
    res = {"ok": False, "errors": [], "warnings": [], "info": {}}
    if not isinstance(obj, dict):
        res["errors"].append("頂層須為物件")
        return res
    if not isinstance(obj.get("x"), list):
        res["errors"].append("缺 x[]")
    series = obj.get("series")
    if not isinstance(series, list) or not series:
        res["errors"].append("缺 series[](至少一序列)")
    else:
        for i, s in enumerate(series):
            if not isinstance(s, dict):
                res["errors"].append(f"series[{i}] 非物件")
                continue
            if not isinstance(s.get("y"), list):
                res["errors"].append(f"series[{i}] 缺 y[]")
            elif isinstance(obj.get("x"), list) and len(s["y"]) != len(obj["x"]):
                res["warnings"].append(f"series[{i}] y 長度 {len(s['y'])} ≠ x {len(obj['x'])}")
            if not s.get("name"):
                res["warnings"].append(f"series[{i}] 缺 name")
    meth = obj.get("methodology") or obj.get("方法論") or obj.get("method")
    if not meth or not str(meth).strip():
        res["errors"].append("缺 方法論欄(methodology / 方法論)")
    code = obj.get("code")
    if code:
        reg = chart_code_lookup(str(code))
        if not reg:
            res["errors"].append(f"code {code} 不在 40 圖規冊")
        else:
            res["info"]["chart"] = f"{reg['code']} {reg['zh']}({reg['mode']} · {reg['shape']})"
            if obj.get("axisMode") and str(obj["axisMode"]) != reg["mode"]:
                res["warnings"].append(f"axisMode {obj['axisMode']} ≠ 圖規 {reg['mode']}")
    else:
        res["warnings"].append("未指定 code(VAP-CH-xx)")
    if "price_field" in obj and not ADJ_PRICE_PATTERN.search(str(obj["price_field"])):
        res["warnings"].append("批330 資料律:價格應為還原價 adj_close;裸 close 需 allow_raw=True")
    if "volume_field" in obj and not VOLUME_EX_DAYTRADE_PATTERN.search(str(obj["volume_field"])):
        res["warnings"].append("批330 資料律:成交量應扣除當沖(欄名未標示)")
    res["ok"] = not res["errors"]
    return res


# ------------------------------------------------------------------ 圖庫(資料無涉)· 堆疊 · 原子寫入 · 交易鎖(v2.3.1 移植)
_THREAD_LOCKS: dict[str, threading.RLock] = {}
_THREAD_LOCKS_GUARD = threading.Lock()


def _canonical_key(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def _thread_lock(key: str) -> threading.RLock:
    with _THREAD_LOCKS_GUARD:
        return _THREAD_LOCKS.setdefault(key, threading.RLock())


class file_transaction_lock:
    """跨執行緒(RLock)+ 跨程序(fcntl / msvcrt)交易鎖;可重入。"""

    def __init__(self, path: str | Path):
        self.key = _canonical_key(path)
        self.lock = _thread_lock(self.key)
        self.handle = None

    def __enter__(self):
        self.lock.acquire()
        root = Path(tempfile.gettempdir()) / "vap-one-locks"
        root.mkdir(parents=True, exist_ok=True)
        lock_path = root / (hashlib.sha256(self.key.encode("utf-8")).hexdigest() + ".lock")
        self.handle = lock_path.open("a+b")
        try:
            if os.name == "nt":
                import msvcrt  # type: ignore
                msvcrt.locking(self.handle.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl  # type: ignore
                fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX)
        except Exception:
            pass
        return self

    def __exit__(self, *exc):
        try:
            if self.handle is not None:
                try:
                    if os.name == "nt":
                        import msvcrt  # type: ignore
                        msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        import fcntl  # type: ignore
                        fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass
                self.handle.close()
        finally:
            self.lock.release()
        return False


def atomic_write_text(path: str | Path, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=p.name + ".", suffix=".tmp", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, str(p))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def atomic_write_json(path: str | Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=1))


def append_jsonl(path: str | Path, record: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with file_transaction_lock(p):
        with p.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def redact_secrets(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if SECRET_KEY_PATTERN.search(str(k)):
                out[k] = "***REDACTED***"
            elif isinstance(v, str) and re.search(r"://[^/\s:]+:[^@\s]+@", v):
                out[k] = re.sub(r"(://[^/\s:]+:)[^@\s]+@", r"\1***@", v)
            else:
                out[k] = redact_secrets(v)
        return out
    if isinstance(value, list):
        return [redact_secrets(v) for v in value]
    return value


def assert_data_free(value: Any, path: str = "chart") -> None:
    """圖庫只保存規格,不保存資料:拒絕 records / 數值陣列 / rows / data。"""
    if isinstance(value, dict):
        for k, v in value.items():
            if str(k).lower() in ("records", "rows", "data", "values", "dataset"):
                raise ValueError(f"{path}.{k}:圖庫為資料無涉,不得嵌入資料內容")
            assert_data_free(v, f"{path}.{k}")
    elif isinstance(value, list):
        if len(value) > 64 and all(isinstance(x, (int, float)) for x in value):
            raise ValueError(f"{path}:疑似數值陣列資料(>64),圖庫拒收")
        for i, v in enumerate(value[:200]):
            assert_data_free(v, f"{path}[{i}]")


def default_chart_library() -> dict:
    return {"schema": LIBRARY_SCHEMA, "version": "2.3.1", "created": utc_now_text(), "items": []}


def _safe_identifier(text: str, fallback: str = "chart") -> str:
    s = re.sub(r"[^A-Za-z0-9_\u4e00-\u9fff]+", "_", str(text)).strip("_").lower()
    return (s or fallback)[:48]


def library_add(library: dict, chart_spec: dict, name: str, tags: Iterable[str] | None = None) -> dict:
    spec = redact_secrets(json.loads(json.dumps(chart_spec, ensure_ascii=False)))
    assert_data_free(spec)
    size = len(json.dumps(spec, ensure_ascii=False).encode("utf-8"))
    if size > MAX_CHART_SPEC_BYTES:
        raise ValueError(f"chart_spec 超過 {MAX_CHART_SPEC_BYTES // 1024} KiB;圖庫只保存精簡規格")
    ids = {it["id"] for it in library.get("items", [])}
    base = _safe_identifier(name)
    lid = base
    n = 2
    while lid in ids:
        lid = f"{base}_{n}"
        n += 1
    item = {"id": lid, "name": str(name), "tags": sorted({str(t).strip().lower() for t in (tags or []) if str(t).strip()}),
            "type": str(spec.get("type", "")), "fields": sorted({str(x) for k in ("x", "y", "secondary_y", "open", "high", "low", "close", "volume")
                                                                 for x in (spec.get(k) if isinstance(spec.get(k), list) else [spec.get(k)]) if x}),
            "chart_spec": spec, "created": utc_now_text()}
    library.setdefault("items", []).append(item)
    return item


def library_search(library: dict, query: str) -> list[dict]:
    q = str(query or "").strip().lower()
    if not q:
        return list(library.get("items", []))
    out = []
    for it in library.get("items", []):
        hay = " ".join([it.get("id", ""), it.get("name", ""), it.get("type", ""), " ".join(it.get("tags", [])),
                        " ".join(it.get("fields", [])), str(it.get("chart_spec", {}).get("title", ""))]).lower()
        if q in hay:
            out.append(it)
    return out


def stack_append_from_library(config: dict, item: dict) -> dict:
    """由圖庫加入堆疊:建立新 chart ID,不改圖庫原件;預設放最下方。"""
    charts = config.setdefault("charts", [])
    ids = {str(c.get("id")) for c in charts}
    base = _safe_identifier(item.get("id", "chart"))
    cid = base
    n = 2
    while cid in ids:
        cid = f"{base}_{n}"
        n += 1
    chart = json.loads(json.dumps(item["chart_spec"], ensure_ascii=False))
    chart["id"] = cid
    chart["_library_ref"] = {"id": item.get("id"), "created": item.get("created")}
    charts.append(chart)
    return chart


def stack_copy(config: dict, chart_id: str) -> dict:
    charts = config.setdefault("charts", [])
    src = next((c for c in charts if str(c.get("id")) == chart_id), None)
    if src is None:
        raise KeyError(chart_id)
    dup = json.loads(json.dumps(src, ensure_ascii=False))
    ids = {str(c.get("id")) for c in charts}
    n = 2
    cid = f"{chart_id}_copy"
    while cid in ids:
        cid = f"{chart_id}_copy{n}"
        n += 1
    dup["id"] = cid
    dup["title"] = f"{src.get('title') or chart_id} 副本"
    charts.insert(charts.index(src) + 1, dup)
    return dup


def stack_set_enabled(config: dict, chart_id: str, enabled: bool) -> bool:
    for c in config.get("charts", []):
        if str(c.get("id")) == chart_id:
            c["enabled"] = bool(enabled)
            return True
    return False


# ------------------------------------------------------------------ 零依賴 SVG 渲染線(正本擴充:堆疊列、K 線 75/25、鎖刻度、方案 A 分項)
def _esc(text: Any) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _scale(value: float, lo: float, hi: float, px_lo: float, px_hi: float) -> float:
    if hi <= lo:
        return (px_lo + px_hi) / 2
    return px_lo + (value - lo) / (hi - lo) * (px_hi - px_lo)


def _series_color(name: str, idx: int, palette: list[str]) -> str:
    return SERIES_COLORS.get(name) or palette[idx % len(palette)]


def _row_frame(rows: list[dict], row: dict) -> tuple[list[str], list[dict]]:
    """依 chart.missing 產生 render-copy(不動原始 rows);Volume 永不補值。"""
    cols = [c for k in ("y", "secondary_y") for c in (row.get(k) or [])] + [row.get(k) for k in ("open", "high", "low", "close", "volume") if row.get(k)]
    frame = apply_missing_policy(rows, [c for c in cols if c], str(row.get("missing", "none")))
    return cols, frame


def render_svg_stack(rows: list[dict], config: dict, profile: str = DEFAULT_PROFILE, family: str = DEFAULT_FAMILY,
                     max_points: int = RENDER_MAX_POINTS) -> tuple[str, dict]:
    """把 config.charts[] 依序渲染成一張垂直堆疊 SVG(共享 X);回傳 (svg, audit)。"""
    prof = VISUAL_PROFILES.get(profile, VISUAL_PROFILES[DEFAULT_PROFILE])
    palette = SNS_DEEP if prof.get("palette") == "snsDeep" else VIA_COMBO
    project = config.get("project", {})
    charts = [c for c in config.get("charts", []) if c.get("enabled", True)]
    physical = expand_render_rows(charts)
    date_col = project.get("date_column") or x_column(rows) or (list(rows[0].keys())[0] if rows else "x")
    labels_all = [str(r.get(date_col, "")) for r in rows]
    width = int(project.get("width_px", 960))
    pad_l, pad_r, pad_t, pad_b, gap = 72, 72, 26, 34, 14
    plot_w = width - pad_l - pad_r
    audit_rows = []
    y_cursor = 8
    parts: list[str] = []
    total_h = 8
    for prow in physical:
        total_h += height_ratio_to_pixels(normalize_height_ratio(prow.get("height_ratio", 1.0))) + gap
    parts.append(f'<svg viewBox="0 0 {width} {total_h + 8}" width="{width}" xmlns="http://www.w3.org/2000/svg" '
                 f'font-family="Microsoft JhengHei,Segoe UI,system-ui,sans-serif" font-size="11" style="background:{TOKENS["surface"]}">')
    for prow in physical:
        h_px = height_ratio_to_pixels(normalize_height_ratio(prow.get("height_ratio", 1.0)))
        plot_h = h_px - pad_t - pad_b
        top = y_cursor + pad_t
        role = prow.get("_render_role", "chart")
        ctype = str(prow.get("type", "line")).lower()
        cols, frame = _row_frame(rows, prow)
        # 大資料縮減(可稽核)
        reduction: dict
        if role == "candlestick_price":
            frame, reduction = optimize_candlestick(frame, prow["open"], prow["high"], prow["low"], prow["close"], prow.get("volume"), max_points)
        else:
            frame, reduction = optimize_envelope(frame, [c for c in (prow.get("y") or []) + (prow.get("secondary_y") or []) if c], max_points)
        labels = [str(r.get(date_col, "")) for r in frame]
        n = max(1, len(frame))
        slot = plot_w / n
        xc = lambda i: pad_l + slot * i + slot / 2  # noqa: E731
        title = str(prow.get("title") or prow.get("id") or "")
        parts.append(f'<text x="{pad_l}" y="{y_cursor + 16}" font-size="12" font-weight="700" fill="{TOKENS["ink"]}">{_esc(title)}</text>')
        row_audit = {"id": prow.get("_logical_chart_id"), "role": role, "type": ctype, "height_px": h_px, "reduction": reduction, "axes": {}}

        def draw_axis_grid(ax: dict, side: str):
            color = TOKENS["muted2"] if side == "left" else TOKENS["ink2"]
            for k, (t, lab) in enumerate(zip(ax["ticks"], ax["labels"])):
                y = top + plot_h - plot_h * k / INTERVALS
                if side == "left":
                    parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" y2="{y:.1f}" stroke="{TOKENS["soft"]}" stroke-width="1"/>')
                    parts.append(f'<text x="{pad_l - 6}" y="{y + 3:.1f}" text-anchor="end" fill="{color}" font-family="Consolas,monospace" font-size="10">{_esc(lab)}</text>')
                else:
                    parts.append(f'<text x="{width - pad_r + 6}" y="{y + 3:.1f}" text-anchor="start" fill="{color}" font-family="Consolas,monospace" font-size="10">{_esc(lab)}</text>')

        if role == "candlestick_price":
            o, h, l, c = prow["open"], prow["high"], prow["low"], prow["close"]
            hi_vals = [v for v in (parse_number(r.get(h)) for r in frame) if v is not None]
            lo_vals = [v for v in (parse_number(r.get(l)) for r in frame) if v is not None]
            ax = locked_axis(min(lo_vals) if lo_vals else 0, max(hi_vals) if hi_vals else 1, False, family, str(prow.get("y_format", "auto")))
            row_audit["axes"]["price"] = ax
            draw_axis_grid(ax, "left")
            parts.append(f'<rect x="{pad_l}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="{TOKENS["border"]}"/>')
            yv = lambda v: _scale(v, ax["min"], ax["max"], top + plot_h, top)  # noqa: E731
            cw = max(1.5, slot * float(prof.get("candle_width_ratio", 0.88)))
            up_c, dn_c = prof.get("up_color", UP_COLOR), prof.get("down_color", DOWN_COLOR)
            for i, r in enumerate(frame):
                po, ph, pl, pc = (parse_number(r.get(k)) for k in (o, h, l, c))
                if None in (po, ph, pl, pc):
                    continue
                color = up_c if pc >= po else dn_c
                x = xc(i)
                parts.append(f'<line x1="{x:.1f}" y1="{yv(ph):.1f}" x2="{x:.1f}" y2="{yv(pl):.1f}" stroke="{color}" stroke-width="1"/>')
                y0, y1 = sorted((yv(po), yv(pc)))
                parts.append(f'<rect x="{x - cw / 2:.1f}" y="{y0:.1f}" width="{cw:.1f}" height="{max(1.0, y1 - y0):.1f}" fill="{color}" stroke="{color}"/>')
        elif role == "candlestick_volume":
            vcol = prow["y"][0]
            o, c = prow["open"], prow["close"]
            vals = [v for v in (parse_number(r.get(vcol)) for r in frame) if v is not None]
            ax = locked_axis(0.0, max(vals) if vals else 1.0, True, family, "magnitude")
            row_audit["axes"]["volume"] = ax
            draw_axis_grid(ax, "left")
            parts.append(f'<rect x="{pad_l}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="{TOKENS["border"]}"/>')
            yv = lambda v: _scale(v, ax["min"], ax["max"], top + plot_h, top)  # noqa: E731
            bw = max(1.5, slot * float(prof.get("bar_width_ratio", 0.92)))
            up_c, dn_c = prof.get("up_color", UP_COLOR), prof.get("down_color", DOWN_COLOR)
            alpha = prof.get("bar_alpha", 0.75)
            for i, r in enumerate(frame):
                pv = parse_number(r.get(vcol))
                if pv is None:
                    continue   # Volume 缺值保持缺值(不補零)
                po, pc = parse_number(r.get(o)), parse_number(r.get(c))
                color = up_c if (po is not None and pc is not None and pc >= po) else dn_c
                parts.append(f'<rect x="{xc(i) - bw / 2:.1f}" y="{yv(pv):.1f}" width="{bw:.1f}" height="{max(1.0, yv(0) - yv(pv)):.1f}" fill="{color}" fill-opacity="{alpha}"/>')
        elif ctype == "heatmap":
            mcols = [c for c in (prow.get("y") or []) if c]
            mat = [[parse_number(r.get(c)) for c in mcols] for r in frame]
            zmax = max((abs(v) for row_ in mat for v in row_ if v is not None), default=1.0) or 1.0
            cw_, ch_ = plot_w / max(1, len(mcols)), plot_h / n
            for i, row_ in enumerate(mat):
                for j, v in enumerate(row_):
                    if v is None:
                        continue
                    t = max(-1.0, min(1.0, v / zmax))   # diverging · zmid 0
                    color = f"rgb({int(255 * max(0, t))},{int(80 * (1 - abs(t)))},{int(255 * max(0, -t))})"
                    parts.append(f'<rect x="{pad_l + j * cw_:.1f}" y="{top + i * ch_:.1f}" width="{cw_:.1f}" height="{ch_:.1f}" fill="{color}"/>')
            row_audit["axes"]["heatmap"] = {"zmax": zmax, "zmid": 0, "cells": len(mcols) * n}
        else:
            y_cols = [c for c in (prow.get("y") or []) if c]
            s_cols = [c for c in (prow.get("secondary_y") or []) if c] if str(prow.get("axis_mode", "auto")) != "single" else []
            include_zero = str(prow.get("axis_zero_policy", "auto")) == "include" or (
                str(prow.get("axis_zero_policy", "auto")) == "auto" and ctype in ("bar", "stacked_bar", "stacked_bar_100", "area", "stacked_area"))
            stack_mode = "percent100" if ctype == "stacked_bar_100" else ("absolute" if ctype in ("stacked_bar", "stacked_area") else "none")
            series_vals = {c: [parse_number(r.get(c)) for r in frame] for c in y_cols}
            if stack_mode == "percent100":
                totals = [sum(series_vals[c][i] or 0.0 for c in y_cols) or 1.0 for i in range(n)]
                series_vals = {c: [(series_vals[c][i] or 0.0) / totals[i] for i in range(n)] for c in y_cols}
                ax = {"ticks": [0, .25, .5, .75, 1], "labels": ["0%", "25%", "50%", "75%", "100%"], "min": 0.0, "max": 1.0, "step": .25,
                      "family": family, "decimals": 2, "mantissa": 2.5, "checks": {"five_ticks": True, "uniform": True, "legal_mantissa": True, "covers": True}}
            else:
                if stack_mode == "absolute":
                    cum_hi = [sum((series_vals[c][i] or 0.0) for c in y_cols if (series_vals[c][i] or 0.0) > 0) for i in range(n)]
                    cum_lo = [sum((series_vals[c][i] or 0.0) for c in y_cols if (series_vals[c][i] or 0.0) < 0) for i in range(n)]
                    dmin, dmax = min(cum_lo + [0.0]), max(cum_hi + [0.0])
                else:
                    flat = [v for c in y_cols for v in series_vals[c] if v is not None]
                    dmin, dmax = (min(flat), max(flat)) if flat else (0.0, 1.0)
                ax = locked_axis(dmin, dmax, include_zero, family, str(prow.get("y_format", "auto")))
            row_audit["axes"]["left"] = ax
            draw_axis_grid(ax, "left")
            yv = lambda v: _scale(v, ax["min"], ax["max"], top + plot_h, top)  # noqa: E731
            ax2 = None
            if s_cols:
                flat2 = [v for c in s_cols for v in (parse_number(r.get(c)) for r in frame) if v is not None]
                inc2 = str(prow.get("secondary_type", "line")) == "bar"
                ax2 = locked_axis(min(flat2) if flat2 else 0, max(flat2) if flat2 else 1, inc2, family, str(prow.get("secondary_y_format", "auto")))
                row_audit["axes"]["right"] = ax2
                draw_axis_grid(ax2, "right")
            parts.append(f'<rect x="{pad_l}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="{TOKENS["border"]}"/>')
            lw, lop = prof.get("line_width", 1.0), prof.get("line_opacity", 0.9)
            bar_alpha, area_alpha = prof.get("bar_alpha", 0.6), prof.get("area_alpha", 0.75)
            base_cum = [0.0] * n
            for si, cname in enumerate(y_cols):
                color = _series_color(cname, si, palette)
                vals = series_vals[cname]
                if ctype in ("bar", "stacked_bar", "stacked_bar_100"):
                    group_n = 1 if stack_mode != "none" else len(y_cols)
                    bw = max(1.5, slot * float(prof.get("bar_width_ratio", 0.92)) / group_n)
                    for i, v in enumerate(vals):
                        if v is None:
                            continue
                        b = base_cum[i] if stack_mode != "none" else 0.0
                        x = xc(i) if stack_mode != "none" else pad_l + slot * i + slot * (0.04 + (0.92 / group_n) * (si + 0.5))
                        y0, y1 = sorted((yv(b), yv(b + v)))
                        parts.append(f'<rect x="{x - bw / 2:.1f}" y="{y0:.1f}" width="{bw:.1f}" height="{max(1.0, y1 - y0):.1f}" fill="{color}" fill-opacity="{bar_alpha}"/>')
                        if stack_mode != "none":
                            base_cum[i] = b + v
                else:
                    pts, poly = [], []
                    for i, v in enumerate(vals):
                        if v is None:
                            continue
                        yy = (base_cum[i] + v) if stack_mode != "none" else v
                        pts.append((xc(i), yv(yy)))
                        if stack_mode != "none":
                            poly.append((xc(i), yv(base_cum[i])))
                            base_cum[i] = base_cum[i] + v
                    if not pts:
                        continue
                    if ctype in ("area", "stacked_area"):
                        floor_y = yv(max(0.0, ax["min"])) if ax["min"] <= 0 <= ax["max"] else yv(ax["min"])
                        lower = list(reversed(poly)) if poly else [(pts[-1][0], floor_y), (pts[0][0], floor_y)]
                        pl_ = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts + lower)
                        parts.append(f'<polygon points="{pl_}" fill="{color}" fill-opacity="{area_alpha}"/>')
                    if ctype == "step":
                        d = " ".join((f"{pts[0][0]:.1f},{pts[0][1]:.1f}" if i == 0 else f"{x:.1f},{pts[i - 1][1]:.1f} {x:.1f},{y:.1f}") for i, (x, y) in enumerate(pts))
                    else:
                        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
                    if ctype == "scatter":
                        for x, y in pts:
                            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" fill="{color}" fill-opacity="{lop}"/>')
                    else:
                        parts.append(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{lw}" stroke-opacity="{lop}" stroke-linejoin="round" stroke-linecap="round"/>')
            if ax2 is not None:
                yv2 = lambda v: _scale(v, ax2["min"], ax2["max"], top + plot_h, top)  # noqa: E731
                stype = str(prow.get("secondary_type", "line"))
                for si, cname in enumerate(s_cols):
                    color = _series_color(cname, len(y_cols) + si, palette)
                    vals = [parse_number(r.get(cname)) for r in frame]
                    if stype == "bar":
                        bw = max(1.5, slot * 0.92 / 2)
                        for i, v in enumerate(vals):
                            if v is None:
                                continue
                            y0, y1 = sorted((yv2(0.0), yv2(v)))
                            parts.append(f'<rect x="{xc(i) - bw / 2:.1f}" y="{y0:.1f}" width="{bw:.1f}" height="{max(1.0, y1 - y0):.1f}" fill="{color}" fill-opacity="{prof.get("bar_alpha", 0.6)}"/>')
                    else:
                        pts = [(xc(i), yv2(v)) for i, v in enumerate(vals) if v is not None]
                        if pts:
                            d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
                            parts.append(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{prof.get("secondary_line_width", lw)}" '
                                         f'stroke-opacity="{prof.get("secondary_alpha", lop)}" stroke-dasharray="5 3" stroke-linejoin="round"/>')
        # 事件線 / 區間帶(方案 A event 0.3)
        for ev in prow.get("events", []) or []:
            try:
                i0 = labels.index(str(ev.get("x") or ev.get("start")))
                i1 = labels.index(str(ev.get("end"))) if ev.get("end") else i0
                x0, x1 = pad_l + slot * min(i0, i1), pad_l + slot * (max(i0, i1) + 1)
                parts.append(f'<rect x="{x0:.1f}" y="{top}" width="{max(1.0, x1 - x0):.1f}" height="{plot_h}" fill="{ev.get("color", "#c4943a")}" fill-opacity="{prof.get("event_alpha", 0.3)}"/>')
            except ValueError:
                row_audit.setdefault("warnings", []).append(f"event x 不在 X 軸:{ev}")
        # X 標籤(共享 X;上方列省略,只在最後一列標)
        if prow is physical[-1]:
            every = max(1, math.ceil(n / MAX_X_TICKS))
            for i in range(0, n, every):
                parts.append(f'<text x="{xc(i):.1f}" y="{top + plot_h + 15}" text-anchor="middle" fill="{TOKENS["muted"]}">{_esc(labels[i][:10])}</text>')
        audit_rows.append(row_audit)
        y_cursor += h_px + gap
    wm = project.get("watermark", "理 · VAP")
    parts.append(f'<text x="{width - pad_r}" y="{total_h + 2}" text-anchor="end" fill="{TOKENS["muted2"]}" font-size="10">{_esc(wm)} · {ENGINE_ID} {VERSION}</text>')
    parts.append("</svg>")
    audit = {"contract": AUDIT_CONTRACT, "engine": f"{ENGINE_ID} {VERSION}", "ts": utc_now_text(), "profile": profile, "family": family,
             "logical_charts": len(charts), "physical_rows": len(physical), "rows_total": len(rows), "date_column": date_col,
             "rows": audit_rows, "standard_panel_height_px": STANDARD_PANEL_HEIGHT_PX, "shared_x": True,
             "checks_all_true": all(all(ax.get("checks", {}).values()) for ra in audit_rows for ax in ra["axes"].values() if "checks" in ax)}
    return "".join(parts), audit


def wrap_html(svg: str, title: str, subtitle: str = "", audit: dict | None = None) -> str:
    """自包含 HTML(零 CDN、手機單欄);SVG 內嵌;hover 用原生 <title>。"""
    meta = json.dumps(audit or {}, ensure_ascii=False)
    return ("<!doctype html><html lang=\"zh-Hant\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{_esc(title)}</title><style>body{{margin:0;background:{TOKENS['bg']};color:{TOKENS['ink']};font-family:Microsoft JhengHei,Segoe UI,system-ui,sans-serif}}"
            ".wrap{max-width:1000px;margin:0 auto;padding:12px}h1{font-size:16px;margin:0 0 2px}.sub{color:#6b6860;font-size:12px;margin-bottom:8px}"
            f"svg{{width:100%;height:auto;border:1px solid {TOKENS['border']};border-radius:6px;background:#fff}}.meta{{font-size:10px;color:#9c9890;margin-top:6px;word-break:break-all}}</style></head>"
            f"<body><div class=\"wrap\"><h1>{_esc(title)}</h1><div class=\"sub\">{_esc(subtitle)}</div>{svg}"
            f"<div class=\"meta\">audit: {_esc(meta[:1200])}</div></div></body></html>")


# ------------------------------------------------------------------ 可選渲染線(Plotly · Matplotlib/Seaborn)· 誠實降級
def lane_status() -> dict:
    out = {"svg": {"available": True, "note": "零依賴,永遠可用"}}
    for mod, key, hint in (("plotly", "plotly", "pip install plotly"), ("matplotlib", "matplotlib", "pip install matplotlib"),
                           ("seaborn", "seaborn", "pip install seaborn"), ("pandas", "pandas", "pip install pandas"),
                           ("duckdb", "duckdb", "pip install duckdb"), ("pyarrow", "pyarrow", "pip install pyarrow")):
        try:
            m = __import__(mod)
            out[key] = {"available": True, "version": str(getattr(m, "__version__", "?"))}
        except Exception as exc:
            out[key] = {"available": False, "install": hint, "error": type(exc).__name__}
    return out


def render_plotly_html(rows: list[dict], config: dict, out_path: Path, family: str = DEFAULT_FAMILY) -> dict:
    try:
        import plotly.graph_objects as go  # type: ignore
        from plotly.subplots import make_subplots  # type: ignore
    except Exception as exc:
        return {"status": "NOT_AVAILABLE", "reason": f"plotly 缺席:{exc}", "install": "pip install plotly"}
    project = config.get("project", {})
    charts = [c for c in config.get("charts", []) if c.get("enabled", True)]
    physical = expand_render_rows(charts)
    date_col = project.get("date_column") or x_column(rows)
    x = [r.get(date_col) for r in rows]
    heights = [normalize_height_ratio(p.get("height_ratio", 1.0)) for p in physical]
    fig = make_subplots(rows=len(physical), cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=heights,
                        subplot_titles=[str(p.get("title") or p.get("id")) for p in physical])
    for ri, p in enumerate(physical, start=1):
        role = p.get("_render_role")
        if role == "candlestick_price":
            fig.add_trace(go.Candlestick(x=x, open=[parse_number(r.get(p["open"])) for r in rows], high=[parse_number(r.get(p["high"])) for r in rows],
                                         low=[parse_number(r.get(p["low"])) for r in rows], close=[parse_number(r.get(p["close"])) for r in rows],
                                         increasing_line_color=UP_COLOR, decreasing_line_color=DOWN_COLOR, name=str(p.get("id"))), row=ri, col=1)
            vals = [v for k in ("high", "low") for v in (parse_number(r.get(p[k])) for r in rows) if v is not None]
            ax = locked_axis(min(vals), max(vals), False, family)
        elif role == "candlestick_volume":
            vc = p["y"][0]
            vols = [parse_number(r.get(vc)) for r in rows]
            colors = [UP_COLOR if (parse_number(r.get(p["close"])) or 0) >= (parse_number(r.get(p["open"])) or 0) else DOWN_COLOR for r in rows]
            fig.add_trace(go.Bar(x=x, y=vols, marker_color=colors, opacity=0.75, name="Volume"), row=ri, col=1)
            ax = locked_axis(0.0, max(v for v in vols if v is not None) if any(v is not None for v in vols) else 1.0, True, family, "magnitude")
        else:
            flat = []
            for c in (p.get("y") or []):
                ys = [parse_number(r.get(c)) for r in rows]
                flat += [v for v in ys if v is not None]
                if str(p.get("type")) in ("bar", "stacked_bar", "stacked_bar_100"):
                    fig.add_trace(go.Bar(x=x, y=ys, name=c, opacity=0.6), row=ri, col=1)
                else:
                    fig.add_trace(go.Scatter(x=x, y=ys, mode="lines", name=c, line={"width": 1}, opacity=0.9,
                                             fill="tozeroy" if str(p.get("type")) in ("area", "stacked_area") else None), row=ri, col=1)
            ax = locked_axis(min(flat) if flat else 0, max(flat) if flat else 1, str(p.get("type")) in ("bar", "stacked_bar"), family)
        fig.update_yaxes(tickvals=ax["ticks"], ticktext=ax["labels"], range=[ax["min"], ax["max"]], row=ri, col=1)
    fig.update_layout(height=int(sum(STANDARD_PANEL_HEIGHT_PX * h for h in heights)) + 80, template="plotly_white", hovermode="x unified",
                      title=str(project.get("title", "VAP")), barmode="stack" if any(str(p.get("type", "")).startswith("stacked") for p in physical) else "group")
    fig.write_html(str(out_path), include_plotlyjs=True, full_html=True)
    return {"status": "OK", "path": str(out_path), "self_contained": True}


def render_matplotlib(rows: list[dict], config: dict, out_png: Path | None, out_pdf: Path | None, dpi: int = 300, family: str = DEFAULT_FAMILY) -> dict:
    try:
        import matplotlib  # type: ignore
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore
        import warnings
        warnings.filterwarnings("ignore", message="Glyph")
        plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "Noto Sans CJK TC", "PingFang TC", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False
    except Exception as exc:
        return {"status": "NOT_AVAILABLE", "reason": f"matplotlib 缺席:{exc}", "install": "pip install matplotlib"}
    project = config.get("project", {})
    charts = [c for c in config.get("charts", []) if c.get("enabled", True)]
    physical = expand_render_rows(charts)
    date_col = project.get("date_column") or x_column(rows)
    xs = list(range(len(rows)))
    labels = [str(r.get(date_col, ""))[:10] for r in rows]
    heights = [normalize_height_ratio(p.get("height_ratio", 1.0)) for p in physical]
    fig, axes = plt.subplots(len(physical), 1, figsize=(float(project.get("width_inch", 15.5)), sum(float(project.get("panel_height_inch", 2.55)) * h for h in heights)),
                             sharex=True, gridspec_kw={"height_ratios": heights}, squeeze=False)
    for ax_, p in zip(axes[:, 0], physical):
        role = p.get("_render_role")
        if role == "candlestick_price":
            o, h, l, c = p["open"], p["high"], p["low"], p["close"]
            vals = []
            for i, r in enumerate(rows):
                po, ph, pl, pc = (parse_number(r.get(k)) for k in (o, h, l, c))
                if None in (po, ph, pl, pc):
                    continue
                color = UP_COLOR if pc >= po else DOWN_COLOR
                ax_.plot([i, i], [pl, ph], color=color, linewidth=0.8)
                ax_.bar(i, abs(pc - po) or 1e-9, bottom=min(po, pc), width=0.88, color=color)
                vals += [pl, ph]
            axl = locked_axis(min(vals), max(vals), False, family) if vals else locked_axis(0, 1)
        elif role == "candlestick_volume":
            vc = p["y"][0]
            vols = [parse_number(r.get(vc)) for r in rows]
            for i, r in enumerate(rows):
                if vols[i] is None:
                    continue
                color = UP_COLOR if (parse_number(r.get(p["close"])) or 0) >= (parse_number(r.get(p["open"])) or 0) else DOWN_COLOR
                ax_.bar(i, vols[i], width=0.92, color=color, alpha=0.75)
            axl = locked_axis(0.0, max((v for v in vols if v is not None), default=1.0), True, family, "magnitude")
        else:
            flat = []
            for c in (p.get("y") or []):
                ys = [parse_number(r.get(c)) for r in rows]
                flat += [v for v in ys if v is not None]
                yy = [float("nan") if v is None else v for v in ys]
                if str(p.get("type")) in ("bar", "stacked_bar"):
                    ax_.bar(xs, [0 if math.isnan(v) else v for v in yy], alpha=0.75, label=c)
                else:
                    ax_.plot(xs, yy, linewidth=1.65, alpha=0.82, label=c)
                    if str(p.get("type")) == "area":
                        ax_.fill_between(xs, 0, [0 if math.isnan(v) else v for v in yy], alpha=0.5)
            axl = locked_axis(min(flat) if flat else 0, max(flat) if flat else 1, str(p.get("type")) in ("bar", "stacked_bar"), family)
            ax_.legend(loc="upper left", fontsize=7)
        ax_.set_ylim(axl["min"], axl["max"])
        ax_.set_yticks(axl["ticks"])
        ax_.set_yticklabels(axl["labels"])
        ax_.set_title(str(p.get("title") or p.get("id")), fontsize=9, loc="left")
        ax_.grid(True, alpha=0.3)
    every = max(1, math.ceil(len(rows) / MAX_X_TICKS))
    axes[-1, 0].set_xticks(xs[::every])
    axes[-1, 0].set_xticklabels(labels[::every], rotation=0, fontsize=7)
    fig.suptitle(str(project.get("title", "VAP")), fontsize=11)
    fig.tight_layout()
    res = {"status": "OK"}
    if out_png:
        fig.savefig(str(out_png), dpi=dpi)
        res["png"] = verify_output_artifact(out_png, "png")
    if out_pdf:
        fig.savefig(str(out_pdf), format="pdf")
        res["pdf"] = verify_output_artifact(out_pdf, "pdf")
    plt.close(fig)
    return res


def verify_output_artifact(path: Path, fmt: str) -> dict:
    """產物存在、非空、格式標頭正確(v2.3 §7:不能只顯示成功訊息卻沒有檔案)。"""
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        return {"path": str(p), "ok": False, "reason": "缺檔或空檔"}
    head = p.read_bytes()[:8]
    ok = {"png": head.startswith(b"\x89PNG"), "pdf": head.startswith(b"%PDF"), "svg": b"<svg" in p.read_bytes()[:400] or b"<?xml" in head,
          "html": b"<!doctype" in p.read_bytes()[:64].lower() or b"<html" in p.read_bytes()[:256].lower()}.get(fmt, True)
    return {"path": str(p), "ok": bool(ok), "bytes": p.stat().st_size, "sha12": sha12(p.read_bytes())}


# ------------------------------------------------------------------ 渲染總管(add-only 輸出 · ledger 只增)
def render_stack(config: dict, rows: list[dict], out_dir: Path, formats: Iterable[str] = ("svg", "html"),
                 profile: str = DEFAULT_PROFILE, family: str = DEFAULT_FAMILY, name: str = "vap_one") -> dict:
    errs = validate_config(config)
    if errs:
        return {"status": "INVALID", "errors": errs}
    run_dir = out_dir / f"RUN_{run_stamp()}"
    run_dir.mkdir(parents=True, exist_ok=False)
    fmts = {f.strip().lower() for f in formats if f.strip()}
    result = {"status": "OK", "run_dir": str(run_dir), "outputs": {}, "lanes": {}}
    svg, audit = render_svg_stack(rows, config, profile, family)
    if "svg" in fmts:
        p = run_dir / f"{name}.svg"
        atomic_write_text(p, svg)
        result["outputs"]["svg"] = verify_output_artifact(p, "svg")
    if "html" in fmts:
        p = run_dir / f"{name}.html"
        atomic_write_text(p, wrap_html(svg, str(config.get("project", {}).get("title", "VAP")), str(config.get("project", {}).get("subtitle", "")), audit))
        result["outputs"]["html"] = verify_output_artifact(p, "html")
    if "plotly" in fmts:
        result["lanes"]["plotly"] = render_plotly_html(rows, config, run_dir / f"{name}_plotly.html", family)
    if "png" in fmts or "pdf" in fmts:
        result["lanes"]["matplotlib"] = render_matplotlib(rows, config, run_dir / f"{name}.png" if "png" in fmts else None,
                                                          run_dir / f"{name}.pdf" if "pdf" in fmts else None, 300, family)
    audit["outputs"] = result["outputs"]
    audit["lanes"] = result["lanes"]
    atomic_write_json(run_dir / f"{name}_audit.json", audit)
    result["audit"] = str(run_dir / f"{name}_audit.json")
    append_jsonl(out_dir / "vap_one_ledger.jsonl", {"ts": utc_now_text(), "action": "RENDER", "run_dir": str(run_dir), "formats": sorted(fmts),
                                                    "profile": profile, "family": family, "svg_sha12": sha12(svg), "checks_all_true": audit["checks_all_true"]})
    return result


def validate_config(config: dict) -> list[str]:
    errs: list[str] = []
    if not isinstance(config, dict):
        return ["config 須為物件"]
    charts = config.get("charts")
    if not isinstance(charts, list) or not charts:
        errs.append("缺 charts[]")
        return errs
    ids = set()
    for i, c in enumerate(charts):
        errs += validate_chart_spec(c, i)
        cid = str(c.get("id"))
        if cid in ids:
            errs.append(f"charts[{i}] id 重複:{cid}")
        ids.add(cid)
    return errs


# ------------------------------------------------------------------ 橋:發現外部 VAP 引擎(不執行、不改寫)
BRIDGE_PATTERNS = {"ENG001": "VAP_ENG001_AutoplotEngineChartlib_v*.py", "ENG002": "VAP_ENG002_AutoplotEngine_v*.py",
                   "ENG003": "VAP_ENG003_AutoplotSeabornPlotly_v*.py", "ENG004": "VAP_ENG004_TAFactory_v*.py",
                   "ENG015": "VAP_ENG015_SeabornStackBridge_v*.py", "CORE": "via_autoplot_engine_v*.py",
                   "GUARD": "vap_spec_guard_v*.py", "V23_GEN": "vap_seaborn_stack_generator.py", "V025_RT": "vap_data_runtime_v*.py"}


def bridge_scan(root: str | Path) -> dict:
    root = Path(root)
    found = {}
    for key, pat in BRIDGE_PATTERNS.items():
        hits = sorted(root.rglob(pat), key=lambda p: p.name)
        hits = [h for h in hits if "BACKUP" not in h.parts and "_superseded" not in str(h)]
        if hits:
            tail = hits[-1]
            found[key] = {"path": str(tail), "sha12": sha12(tail.read_bytes()), "candidates": len(hits), "executed": False}
        else:
            found[key] = {"status": "NOT_FOUND"}
    return {"root": str(root), "engines": found, "policy": "discover-only · never execute · never modify"}


# ------------------------------------------------------------------ Demo 資料(合成,標示 SYNTHETIC)
def demo_rows(n: int = 120, seed: int = 20260907) -> list[dict]:
    rnd = random.Random(seed)
    rows, price, d = [], 100.0, _dt.date(2026, 3, 2)
    for i in range(n):
        while d.weekday() >= 5:
            d += _dt.timedelta(days=1)
        o = price
        c = max(1.0, o * (1 + rnd.gauss(0, 0.015)))
        h, l = max(o, c) * (1 + abs(rnd.gauss(0, 0.006))), min(o, c) * (1 - abs(rnd.gauss(0, 0.006)))
        vol = None if i % 37 == 5 else int(rnd.uniform(8e5, 3e6))       # 故意留缺值,證明 Volume 不補
        rows.append({"Date": d.isoformat(), "Adj Open": round(o, 2), "Adj High": round(h, 2), "Adj Low": round(l, 2), "Adj Close": round(c, 2),
                     "Volume_ExDT": vol, "Foreign": int(rnd.gauss(0, 4000)), "Trust": int(rnd.gauss(0, 1500)), "Dealer": int(rnd.gauss(0, 900)),
                     "MA20": round(c * (1 + rnd.gauss(0, 0.004)), 2)})
        price = c
        d += _dt.timedelta(days=1)
    return rows


def demo_config(data_path: str = "demo.csv") -> dict:
    return {"schema": STACK_SCHEMA, "version": "2.3.1", "project": {"title": "VIA · VAP ONE demo(SYNTHETIC)", "subtitle": "K 線 75/25 · 三大法人堆疊 · 雙軸 · 鎖刻度",
                                                                   "data_path": data_path, "date_column": "Date", "watermark": "理 · VAP"},
            "charts": [
                {"id": "candle", "type": "candlestick", "title": "2330 還原價 K 線 × Volume(扣當沖)", "open": "Adj Open", "high": "Adj High", "low": "Adj Low",
                 "close": "Adj Close", "volume": "Volume_ExDT", "missing": "ffill", "height_ratio": 1.5, "axis_mode": "single"},
                {"id": "chips", "type": "stacked_bar", "title": "三大法人買賣超(堆疊)", "y": ["Foreign", "Trust", "Dealer"], "height_ratio": 0.75, "axis_zero_policy": "include"},
                {"id": "dual", "type": "dual", "title": "Adj Close × MA20(雙軸)", "y": ["Adj Close"], "secondary_y": ["MA20"], "axis_mode": "dual", "height_ratio": 1.0,
                 "events": [{"x": "2026-04-01", "end": "2026-04-08", "color": "#c4943a"}]}
            ]}


# ------------------------------------------------------------------ 自測(輸出可被總控台載入的 JSON)
def run_selftest(verbose: bool = False) -> dict:
    checks: list[dict] = []

    def ck(name: str, fn: Callable[[], Any], skip_if: str | None = None):
        if skip_if:
            checks.append({"name": name, "status": "SKIP", "note": skip_if})
            return
        try:
            ok = bool(fn())
            checks.append({"name": name, "status": "PASS" if ok else "FAIL"})
        except Exception as exc:
            checks.append({"name": name, "status": "FAIL", "error": f"{type(exc).__name__}: {exc}"})

    # 圖規 SSOT
    ck("圖規冊 40", lambda: len(CHART_REGISTRY) == 40)
    ck("code 唯一", lambda: len({c["code"] for c in CHART_REGISTRY}) == 40)
    ck("9 群", lambda: len({c["group"] for c in CHART_REGISTRY}) == 9)
    ck("SINGLE26/DUAL9/NONE5", lambda: [sum(1 for c in CHART_REGISTRY if c["mode"] == m) for m in ("SINGLE", "DUAL_LOCKED", "NONE")] == [26, 9, 5])
    ck("stack type→code 全在冊", lambda: all(chart_code_lookup(v) for v in STACK_TYPE_TO_CODE.values()))
    # 軸契約
    ck("0..97 → [0,25,50,75,100]", lambda: compute_locked_ticks(0, 97) == [0.0, 25.0, 50.0, 75.0, 100.0])
    ck("13..14 → step 0.25", lambda: axis_checks(compute_locked_ticks(13, 14), 13, 14)["step"] == 0.25)
    ck("v23 家族含 1.25(0..4.6→step 1.25)", lambda: axis_checks(compute_locked_ticks(0, 4.6, family="v23"), 0, 4.6)["step"] == 1.25)
    ck("v018 家族不用 1.25", lambda: axis_checks(compute_locked_ticks(0, 4.6, family="v018"), 0, 4.6)["step"] != 1.25)
    ck("-3..97 → step 50(25 無法 4 間隔覆蓋;與總控台一致)", lambda: (lambda t: t[0] <= -3 and t[-1] >= 97 and axis_checks(t, -3, 97)["step"] == 50)(compute_locked_ticks(-3, 97)))
    ck("include_zero 非負→起點 0", lambda: compute_locked_ticks(5, 97, include_zero=True)[0] == 0.0)
    ck("include_zero 非正→終點 0", lambda: compute_locked_ticks(-97, -5, include_zero=True)[-1] == 0.0)
    ck("min>max 交換", lambda: compute_locked_ticks(97, 0)[0] <= 0)
    ck("min==max 退化", lambda: axis_checks(compute_locked_ticks(5, 5), 5, 5)["covers"])
    ck("NaN 回 0..1", lambda: compute_locked_ticks(float("nan"), 1) == [0.0, 0.25, 0.5, 0.75, 1.0])

    def prop200():
        rnd = random.Random(7)
        for _ in range(200):
            lo = rnd.uniform(-1e4, 1e4)
            hi = lo + abs(rnd.uniform(1e-3, 5e4))
            fam = rnd.choice(("v018", "v23"))
            t = compute_locked_ticks(lo, hi, include_zero=rnd.random() < 0.3, family=fam)
            c = axis_checks(t, lo, hi, fam)
            if not (c["five_ticks"] and c["uniform"] and c["legal_mantissa"] and c["covers"]):
                return False
        return True
    ck("200 隨機樣本 四檢全真(合規 PropertySamples 200)", prop200)
    ck("尾零 1.25 / 2.50", lambda: [format_tick_fixed(v, decimal_places_for_step(1.25)) for v in (1.25, 2.5)] == ["1.25", "2.50"])
    ck("小數 offset 不顯示成整數(v018 0..4.6 → -1.5…6.5)", lambda: locked_axis(0, 4.6, family="v018")["labels"] == ["-1.5", "0.5", "2.5", "4.5", "6.5"])
    ck("magnitude 1.2M", lambda: magnitude_formatter(1_234_567) == "1.2M")
    # 高度 · K 線
    ck("1.0×=420px", lambda: height_ratio_to_pixels(1.0) == 420)
    ck("1.5×=630px", lambda: height_ratio_to_pixels(1.5) == 630)
    ck("0.3 非法(步進)", lambda: (lambda: (validate_height_ratio(0.3), False))() if False else _raises(validate_height_ratio, 0.3))
    ck("normalize 0.3→0.25", lambda: normalize_height_ratio(0.3) == 0.25)
    ck("normalize 9→4.0 夾", lambda: normalize_height_ratio(9) == 4.0)
    ck("K 線展開 2 列 75/25", lambda: (lambda r: len(r) == 2 and math.isclose(r[0]["height_ratio"], 1.125) and math.isclose(r[1]["height_ratio"], 0.375))(
        expand_render_rows([{"id": "c", "type": "candlestick", "height_ratio": 1.5, "open": "o", "high": "h", "low": "l", "close": "c", "volume": "v"}])))
    ck("K 線 volume 列 axis include zero", lambda: expand_render_rows([{"id": "c", "type": "candlestick", "open": "o", "high": "h", "low": "l", "close": "c"}])[1]["axis_zero_policy"] == "include")
    ck("fractions 不合 1 拒", lambda: _raises(candlestick_height_fractions, {"price_height_fraction": 0.7, "volume_height_fraction": 0.2}))
    ck("拖曳重排", lambda: [c["id"] for c in reorder_charts_by_drag([{"id": "a"}, {"id": "b"}, {"id": "c"}], "c", 0)] == ["c", "a", "b"])
    # 資料律 · 缺值
    ck("pick_price 只認 adj", lambda: pick_price(["Close", "Adj Close"]) == "Adj Close")
    ck("裸 close 無 allow_raw 拒", lambda: _raises(pick_price, ["Close"]))
    ck("裸 close allow_raw 可", lambda: pick_price(["Close"], allow_raw=True) == "Close")
    ck("volume 未標示→WARN", lambda: volume_ex_daytrade_status(["Volume"])["status"] == "WARN")
    ck("volume 標示 ExDT→OK", lambda: volume_ex_daytrade_status(["Volume_ExDT"])["status"] == "OK")
    _rows = [{"d": "2026-01-01", "Adj Close": 1, "Volume": 10}, {"d": "2026-01-02", "Adj Close": None, "Volume": None}, {"d": "2026-01-03", "Adj Close": 3, "Volume": 30}]
    ck("ffill 價格補、Volume 不補", lambda: (lambda r: r[1]["Adj Close"] == 1 and r[1]["Volume"] is None)(apply_missing_policy(_rows, ["Adj Close", "Volume"], "ffill")))
    ck("interpolate 價格 2、Volume 不補", lambda: (lambda r: r[1]["Adj Close"] == 2 and r[1]["Volume"] is None)(apply_missing_policy(_rows, ["Adj Close", "Volume"], "interpolate")))
    ck("zero 不補 Volume", lambda: apply_missing_policy(_rows, ["Adj Close", "Volume"], "zero")[1]["Volume"] is None)
    ck("drop 刪缺列", lambda: len(apply_missing_policy(_rows, ["Adj Close"], "drop")) == 2)
    ck("quality audit 重複日期", lambda: quality_audit(_rows + [_rows[0]], "d", ["Adj Close"])["duplicate_dates"] == 1)
    # 縮減
    _big = [{"d": i, "y": math.sin(i / 10) * 100 + (500 if i == 4321 else 0)} for i in range(20000)]
    ck("envelope 縮減 ≤ max 且保極值", lambda: (lambda o, a: a["applied"] and len(o) <= 5000 and any(r["y"] > 400 for r in o))(*optimize_envelope(_big, ["y"], 5000)))
    ck("envelope 不需縮減時原樣", lambda: optimize_envelope(_big[:100], ["y"], 5000)[1]["applied"] is False)
    _ohlc = [{"d": i, "o": i, "h": i + 2, "l": i - 2, "c": i + 1, "v": (None if i == 3 else 1)} for i in range(10)]
    ck("candlestick 桶聚合 O首H最大L最小C尾", lambda: (lambda o: o[0]["o"] == 0 and o[0]["h"] == 6 and o[0]["l"] == -2 and o[0]["c"] == 5)(optimize_candlestick(_ohlc, "o", "h", "l", "c", "v", 2)[0]))
    ck("candlestick 桶含缺值 Volume→缺值", lambda: optimize_candlestick(_ohlc, "o", "h", "l", "c", "v", 2)[0][0]["v"] is None)
    # 規格驗證
    ck("spec single 殘留 secondary 拒", lambda: any("secondary_y" in e for e in validate_chart_spec({"id": "a", "type": "line", "y": ["x"], "axis_mode": "single", "secondary_y": ["b"]})))
    ck("spec candlestick 裸 close 拒", lambda: any("批330" in e for e in validate_chart_spec({"id": "c", "type": "candlestick", "open": "Open", "high": "High", "low": "Low", "close": "Close"})))
    ck("spec candlestick adj 可", lambda: not validate_chart_spec({"id": "c", "type": "candlestick", "open": "Adj Open", "high": "Adj High", "low": "Adj Low", "close": "Adj Close"}))
    ck("圖規 JSON 最小合格", lambda: validate_vap_json({"x": [1], "series": [{"name": "a", "y": [1]}], "methodology": "m"})["ok"])
    ck("圖規 JSON 缺方法論拒", lambda: not validate_vap_json({"x": [1], "series": [{"y": [1]}]})["ok"])
    ck("圖規 JSON code=candle→CH-27", lambda: "VAP-CH-27" in validate_vap_json({"code": "candle", "x": [1], "series": [{"y": [1]}], "方法論": "m"})["info"]["chart"])
    ck("圖規 JSON 裸 close 警", lambda: any("批330" in w for w in validate_vap_json({"x": [1], "series": [{"y": [1]}], "methodology": "m", "price_field": "close"})["warnings"]))
    # 圖庫 · 堆疊 · 原子寫入
    _lib = default_chart_library()
    ck("圖庫加入(資料無涉)", lambda: library_add(_lib, {"type": "line", "y": ["Adj Close"], "title": "t"}, "折線 A", ["price"])["id"] == "折線_a")
    ck("圖庫拒 records", lambda: _raises(library_add, _lib, {"type": "line", "records": [1, 2]}, "bad"))
    ck("圖庫拒 >64 數值陣列", lambda: _raises(library_add, _lib, {"type": "line", "y": ["a"], "cache": list(range(100))}, "bad2"))
    ck("圖庫遮蔽 secret", lambda: library_add(_lib, {"type": "line", "y": ["a"], "source": {"password": "x", "url": "postgresql://u:pw@h/db"}}, "sec")["chart_spec"]["source"]["password"] == "***REDACTED***")
    ck("圖庫搜尋", lambda: len(library_search(_lib, "折線")) == 1)
    _cfg = {"charts": []}
    ck("圖庫→堆疊 新 ID", lambda: stack_append_from_library(_cfg, _lib["items"][0])["id"] == "折線_a" and stack_append_from_library(_cfg, _lib["items"][0])["id"] == "折線_a_2")
    ck("堆疊複製 副本", lambda: stack_copy(_cfg, "折線_a")["title"].endswith("副本"))
    ck("堆疊停用不刪", lambda: stack_set_enabled(_cfg, "折線_a", False) and len(_cfg["charts"]) == 3)

    def atomic_rt():
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.json"
            with file_transaction_lock(p):
                atomic_write_json(p, {"a": 1})
            append_jsonl(Path(td) / "l.jsonl", {"k": 1})
            append_jsonl(Path(td) / "l.jsonl", {"k": 2})
            return json.loads(p.read_text(encoding="utf-8"))["a"] == 1 and len((Path(td) / "l.jsonl").read_text().splitlines()) == 2
    ck("原子寫入 + 鎖 + jsonl 只增", atomic_rt)
    # 渲染(SVG 零依賴)
    _r = demo_rows(80)
    _c = demo_config()
    _svg, _aud = render_svg_stack(_r, _c)
    ck("SVG 產生且合法", lambda: _svg.startswith("<svg") and _svg.endswith("</svg>"))
    ck("實體列 4(K線2+堆疊+雙軸)", lambda: _aud["physical_rows"] == 4)
    ck("每軸四檢全真", lambda: _aud["checks_all_true"])
    ck("K 線紅綠色出現", lambda: UP_COLOR in _svg and DOWN_COLOR in _svg)
    ck("雙軸右軸標籤出現", lambda: "right" in _aud["rows"][3]["axes"])
    ck("HTML 自包含零 CDN(無外部 script/link)", lambda: (lambda h: "<svg" in h and re.search(r"<(script|link)[^>]+(src|href)=[\"\']https?://", h) is None)(wrap_html(_svg, "t")))
    ck("事件帶 opacity 0.3", lambda: 'fill-opacity="0.3"' in _svg)
    ck("方案 A 線 0.9 / 柱 0.6 / 面積 0.75 常數", lambda: VISUAL_PROFILES["vap_spec_v1"]["line_opacity"] == 0.9 and VISUAL_PROFILES["vap_spec_v1"]["bar_alpha"] == 0.6 and VISUAL_PROFILES["vap_spec_v1"]["area_alpha"] == 0.75)
    ck("config 驗證通過", lambda: validate_config(_c) == [])

    def full_render():
        with tempfile.TemporaryDirectory() as td:
            res = render_stack(_c, _r, Path(td), ("svg", "html"), name="t")
            return res["status"] == "OK" and res["outputs"]["svg"]["ok"] and res["outputs"]["html"]["ok"] and (Path(td) / "vap_one_ledger.jsonl").exists()
    ck("render_stack svg+html+audit+ledger", full_render)
    lanes = lane_status()
    ck("lane 狀態可探", lambda: lanes["svg"]["available"])

    def mpl_render():
        with tempfile.TemporaryDirectory() as td:
            res = render_matplotlib(_r, _c, Path(td) / "a.png", Path(td) / "a.pdf", 300)
            return res["status"] == "OK" and res["png"]["ok"] and res["pdf"]["ok"]
    ck("matplotlib PNG300/PDF 產出可驗", mpl_render, skip_if=None if lanes["matplotlib"]["available"] else "matplotlib 缺席(誠實 SKIP)")

    def plotly_render():
        with tempfile.TemporaryDirectory() as td:
            res = render_plotly_html(_r, _c, Path(td) / "p.html")
            return res["status"] == "OK"
    ck("plotly 自包含 HTML", plotly_render, skip_if=None if lanes["plotly"]["available"] else "plotly 缺席(誠實 SKIP)")
    ck("parquet 缺依賴誠實 FAIL", lambda: True if (lanes["duckdb"]["available"] or lanes["pyarrow"]["available"]) else _raises(rows_from_parquet, Path("x.parquet")))
    passed = sum(1 for c in checks if c["status"] == "PASS")
    failed = sum(1 for c in checks if c["status"] == "FAIL")
    skipped = sum(1 for c in checks if c["status"] == "SKIP")
    out = {"contract": SELFTEST_CONTRACT, "engine": ENGINE_ID, "version": VERSION, "ts": utc_now_text(), "passed": passed, "failed": failed, "skipped": skipped,
           "total": len(checks), "verdict": "PASS" if failed == 0 else "FAIL", "lanes": lanes, "profile_default": DEFAULT_PROFILE, "family_default": DEFAULT_FAMILY,
           "registry": {"charts": len(CHART_REGISTRY), "groups": len({c["group"] for c in CHART_REGISTRY})}, "provenance": PROVENANCE, "checks": checks}
    if verbose:
        for c in checks:
            print(f"  [{c['status']:4}] {c['name']}" + (f"  ← {c.get('error', c.get('note', ''))}" if c["status"] != "PASS" else ""))
    return out


def _raises(fn: Callable, *args, **kwargs) -> bool:
    try:
        fn(*args, **kwargs)
        return False
    except Exception:
        return True


# ------------------------------------------------------------------ CLI(不 sys.exit 於函式內;main 回傳碼)
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog=ENGINE_ID, description="VAP ONE · 單檔整合引擎")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json", default="", help="自測結果輸出 JSON 路徑")
    ap.add_argument("--axis", nargs=2, type=float, metavar=("MIN", "MAX"))
    ap.add_argument("--family", default=DEFAULT_FAMILY, choices=sorted(STEP_FAMILIES))
    ap.add_argument("--include-zero", action="store_true")
    ap.add_argument("--list-charts", action="store_true")
    ap.add_argument("--group", default="")
    ap.add_argument("--check-spec", default="", help="驗證站「圖規 JSON」或堆疊 config")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--render", default="", help="堆疊 config.json")
    ap.add_argument("--data", default="", help="資料源(csv/tsv/json/jsonl/sqlite/parquet);省略則用 config.project.data_path")
    ap.add_argument("--table", default="")
    ap.add_argument("--out", default="./vap_one_out")
    ap.add_argument("--formats", default="svg,html")
    ap.add_argument("--profile", default=DEFAULT_PROFILE, choices=sorted(VISUAL_PROFILES))
    ap.add_argument("--lanes", action="store_true")
    ap.add_argument("--bridge-scan", default="")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args(argv)
    rc = 0
    if a.selftest:
        res = run_selftest(verbose=True)
        print(f"[{ENGINE_ID}] {res['verdict']} {res['passed']}/{res['total']} (skip {res['skipped']})")
        if a.json:
            atomic_write_json(a.json, res)
            print(f"  json → {a.json}")
        rc = 0 if res["failed"] == 0 else 1
    if a.axis:
        ax = locked_axis(a.axis[0], a.axis[1], a.include_zero, a.family)
        print(json.dumps(ax, ensure_ascii=False, indent=1))
    if a.list_charts:
        for c in CHART_REGISTRY:
            if not a.group or a.group in c["group"]:
                print(f"{c['code']}  {c['id']:10} {c['zh']:22} {c['group']:24} {c['mode']:12} {c['shape']:18} {c['fields']}")
    if a.check_spec:
        obj = json.loads(Path(a.check_spec).read_text(encoding="utf-8-sig"))
        res = validate_vap_json(obj) if "series" in obj else {"config_errors": validate_config(obj), "ok": not validate_config(obj)}
        print(json.dumps(res, ensure_ascii=False, indent=1))
        rc = rc or (0 if res.get("ok") else 1)
    if a.lanes:
        print(json.dumps(lane_status(), ensure_ascii=False, indent=1))
    if a.bridge_scan:
        print(json.dumps(bridge_scan(a.bridge_scan), ensure_ascii=False, indent=1))
    if a.demo or a.render:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        if a.demo:
            rows = demo_rows()
            cfg = demo_config("demo_SYNTHETIC.csv")
            with (out / "demo_SYNTHETIC.csv").open("w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
            atomic_write_json(out / "demo_config.json", cfg)
        else:
            cfg = json.loads(Path(a.render).read_text(encoding="utf-8-sig"))
            data = a.data or cfg.get("project", {}).get("data_path", "")
            dp = Path(data) if Path(data).is_absolute() else (Path(a.render).parent / data)
            _tbl, rows = load_rows(dp, a.table or None)
        res = render_stack(cfg, rows, out, [f for f in a.formats.split(",")], a.profile, a.family)
        print(json.dumps(res, ensure_ascii=False, indent=1))
        rc = rc or (0 if res.get("status") == "OK" else 1)
    if not any((a.selftest, a.axis, a.list_charts, a.check_spec, a.lanes, a.bridge_scan, a.demo, a.render)):
        ap.print_help()
    return rc


if __name__ == "__main__":
    sys.exit(main())
