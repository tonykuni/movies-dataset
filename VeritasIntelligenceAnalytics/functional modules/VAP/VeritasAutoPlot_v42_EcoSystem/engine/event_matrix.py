"""
VeritasAutoPlot™ Event Matrix Engine
======================================
Historical financial crisis events (1995-Present)
Each event includes: period, sub-events, news verification URLs, cycle type
"""

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
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
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
EVENT_MATRIX = [
    {
        "id": "ASIAN_CRISIS",
        "name": "1997 亞洲金融風暴",
        "start": "1997-07-01", "end": "1998-12-31",
        "color": "#C44E52", "cycle_type": "Bear",
        "urls": [
            "https://www.imf.org/external/pubs/ft/history/2012/pdf/c10.pdf",
            "https://www.federalreservehistory.org/essays/asian-financial-crisis",
            "https://www.pbs.org/wgbh/pages/frontline/shows/crash/etc/cron.html"
        ],
        "subEvents": [
            {"date": "1997-07-02", "label": "泰銖放寬匯率 (風暴起點)", "color": "#C44E52"},
            {"date": "1997-10-23", "label": "港股恆指暴跌", "color": "#C44E52"},
            {"date": "1998-08-17", "label": "俄羅斯債務違約", "color": "#C44E52"},
            {"date": "1998-09-23", "label": "LTCM 基金倒閉", "color": "#DD8452"},
        ]
    },
    {
        "id": "921_EARTHQUAKE",
        "name": "1999 921大地震",
        "start": "1999-09-21", "end": "1999-10-21",
        "color": "#8C8C8C", "cycle_type": "Shock",
        "urls": [
            "https://en.wikipedia.org/wiki/1999_Jiji_earthquake",
            "https://www.bbc.co.uk/news/world-asia-49752062",
            "https://earthquake.usgs.gov/earthquakes/eventpage/usp0009eq0"
        ],
        "subEvents": [
            {"date": "1999-09-21", "label": "921 集集大地震 (M7.3)", "color": "#C44E52"},
        ]
    },
    {
        "id": "DOT_COM",
        "name": "2000 達康泡沫",
        "start": "2000-03-10", "end": "2002-10-09",
        "color": "#C44E52", "cycle_type": "Bear",
        "urls": [
            "https://money.cnn.com/2000/03/10/markets/markets_newyork/",
            "https://www.wallstreetmojo.com/dot-com-bubble/",
            "https://en.wikipedia.org/wiki/Dot-com_bubble"
        ],
        "subEvents": [
            {"date": "2000-03-10", "label": "Nasdaq 歷史高點 (5048)", "color": "#55A868"},
            {"date": "2001-09-11", "label": "911 恐怖攻擊", "color": "#1e1d1a"},
            {"date": "2001-12-02", "label": "Enron 申請破產", "color": "#C44E52"},
            {"date": "2002-10-09", "label": "市場觸底 (熊市結束)", "color": "#55A868"},
        ]
    },
    {
        "id": "SARS",
        "name": "2003 SARS 疫情",
        "start": "2002-11-16", "end": "2003-07-05",
        "color": "#8172B3", "cycle_type": "Shock",
        "urls": [
            "https://www.who.int/health-topics/severe-acute-respiratory-syndrome",
            "https://www.cdc.gov/sars/about/fs-sars.html",
            "https://en.wikipedia.org/wiki/2002%E2%80%932004_SARS_outbreak"
        ],
        "subEvents": [
            {"date": "2003-03-14", "label": "WHO 全球警報", "color": "#C44E52"},
            {"date": "2003-04-21", "label": "台灣和平醫院封院", "color": "#C44E52"},
        ]
    },
    {
        "id": "GFC",
        "name": "2008 金融海嘯",
        "start": "2007-10-09", "end": "2009-03-09",
        "color": "#C44E52", "cycle_type": "Bear",
        "urls": [
            "https://www.nytimes.com/2008/09/15/business/15lehman.html",
            "https://www.federalreservehistory.org/essays/great-recession-of-200709",
            "https://money.cnn.com/2008/09/29/markets/markets_newyork/"
        ],
        "subEvents": [
            {"date": "2007-08-09", "label": "BNP 凍結基金 (次貸爆發)", "color": "#DD8452"},
            {"date": "2008-03-14", "label": "Bear Stearns 倒閉", "color": "#C44E52"},
            {"date": "2008-09-15", "label": "雷曼兄弟破產", "color": "#C44E52"},
            {"date": "2008-11-25", "label": "Fed 啟動 QE1", "color": "#4C72B0"},
            {"date": "2009-03-09", "label": "S&P 500 觸底 (666點)", "color": "#55A868"},
        ]
    },
    {
        "id": "EURO_DEBT",
        "name": "2011 歐債危機",
        "start": "2011-04-01", "end": "2012-07-26",
        "color": "#8172B3", "cycle_type": "Bear",
        "urls": [
            "https://www.ecb.europa.eu/ecb/educational/explainers/tell-me-more/html/sovereign-debt-crisis.en.html",
            "https://en.wikipedia.org/wiki/European_debt_crisis",
            "https://www.reuters.com/article/us-eurozone-crisis-timeline-idUSBRE8B10TQ20121202"
        ],
        "subEvents": [
            {"date": "2011-08-05", "label": "美債評級遭降 (AAA→AA+)", "color": "#C44E52"},
            {"date": "2012-07-26", "label": "Draghi: Whatever it takes", "color": "#55A868"},
        ]
    },
    {
        "id": "CHINA_CRASH",
        "name": "2015 陸股熔斷",
        "start": "2015-06-12", "end": "2016-02-29",
        "color": "#DD8452", "cycle_type": "Bear",
        "urls": [
            "https://en.wikipedia.org/wiki/2015%E2%80%932016_Chinese_stock_market_turbulence",
            "https://www.bbc.com/news/business-33403170",
            "https://www.reuters.com/article/us-china-markets-idUSKCN0PI04R20150709"
        ],
        "subEvents": [
            {"date": "2015-06-12", "label": "上證指數見頂 (5178)", "color": "#55A868"},
            {"date": "2016-01-04", "label": "A股熔斷機制首次觸發", "color": "#C44E52"},
        ]
    },
    {
        "id": "TRADE_WAR",
        "name": "2018 美中貿易戰",
        "start": "2018-01-22", "end": "2018-12-24",
        "color": "#DD8452", "cycle_type": "Bear",
        "urls": [
            "https://www.bbc.com/news/business-45899310",
            "https://en.wikipedia.org/wiki/China%E2%80%93United_States_trade_war",
            "https://www.reuters.com/article/us-usa-trade-china-timeline-idUSKCN1LG0D2"
        ],
        "subEvents": [
            {"date": "2018-03-22", "label": "川普簽署 301 調查", "color": "#DD8452"},
            {"date": "2018-12-24", "label": "聖誕夜崩盤 (S&P 2351)", "color": "#C44E52"},
        ]
    },
    {
        "id": "COVID_19",
        "name": "2020 Covid-19 崩盤",
        "start": "2020-02-19", "end": "2020-03-23",
        "color": "#1e1d1a", "cycle_type": "Crash",
        "urls": [
            "https://www.cnbc.com/2020/03/09/stock-market-today-live.html",
            "https://www.who.int/news/item/27-04-2020-who-timeline---covid-19",
            "https://www.federalreserve.gov/monetarypolicy/2020-03-15-statement.htm"
        ],
        "subEvents": [
            {"date": "2020-03-09", "label": "第一次熔斷 (-7%)", "color": "#C44E52"},
            {"date": "2020-03-12", "label": "第二次熔斷 (-9.5%)", "color": "#C44E52"},
            {"date": "2020-03-16", "label": "第三次熔斷 (-12%)", "color": "#C44E52"},
            {"date": "2020-03-23", "label": "Fed 無限 QE (市場觸底)", "color": "#55A868"},
        ]
    },
    {
        "id": "INFLATION",
        "name": "2022 通膨升息循環",
        "start": "2022-01-03", "end": "2022-10-13",
        "color": "#8C8C8C", "cycle_type": "Bear",
        "urls": [
            "https://www.bloomberg.com/news/articles/2022-06-15/fed-hikes-75-basis-points",
            "https://www.reuters.com/markets/us/inflation-hit-40-year-high-2022-2023-01-12/",
            "https://www.wsj.com/articles/cpi-inflation-data-january-2022-11644453578"
        ],
        "subEvents": [
            {"date": "2022-03-16", "label": "Fed 首次升息", "color": "#4C72B0"},
            {"date": "2022-06-15", "label": "升息 3碼 (75bp)", "color": "#C44E52"},
            {"date": "2022-10-13", "label": "CPI 見頂反轉", "color": "#55A868"},
        ]
    },
    {
        "id": "AI_CORRECTION",
        "name": "2024 AI 修正與川普 2.0",
        "start": "2024-07-11", "end": "2025-02-14",
        "color": "#9c9890", "cycle_type": "Correction",
        "urls": [
            "https://www.reuters.com/technology/chatgpt-launch-sparked-ai-race-2023-11-29/",
            "https://nvidianews.nvidia.com/",
            "https://www.cnbc.com/2024/08/05/stock-market-today-live-updates.html"
        ],
        "subEvents": [
            {"date": "2024-08-05", "label": "日圓套利平倉崩盤", "color": "#C44E52"},
            {"date": "2024-11-06", "label": "川普當選 (Trump 2.0)", "color": "#55A868"},
        ]
    },
]


# ── TW Stock Sector Map ─────────────────────────────────────────
TW_SECTOR_MAP = {
    "Foundry (晶圓代工)":     ["2330", "2303", "5347", "TSMC", "UMC"],
    "IC Design (IC設計)":     ["2454", "2379", "3034", "MediaTek", "Realtek"],
    "Shipping (航運)":        ["2603", "2609", "2615", "Evergreen", "YangMing"],
    "AI Server (AI伺服器)":   ["2382", "3231", "6669", "2317", "Quanta", "Wistron"],
    "Financial (金融)":       ["2881", "2882", "2891", "Fubon", "Cathay"],
    "ETF":                    ["0050", "0056", "00878", "00929", "SPY", "QQQ"],
    "Semiconductor (半導體)":  ["2308", "3711", "6415", "3443"],
    "Telecom (電信)":         ["2412", "3045", "4904"],
    "Steel (鋼鐵)":          ["2002", "2014", "2015"],
    "Biotech (生技)":         ["4743", "6547", "1760"],
}


def detect_sector(filename: str) -> str:
    """Auto-tag file based on TW_SECTOR_MAP keywords."""
    for sector, keywords in TW_SECTOR_MAP.items():
        for key in keywords:
            if key in filename:
                return sector
    return "Uncategorized"
