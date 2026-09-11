"""台股月營收動能引擎 (Taiwan Stock Monthly Revenue Engine).

模組:
    fetch    -- 從 MOPS 公開資訊觀測站抓取全上市/上櫃月營收
    classify -- 產業分類 + 原物料/週期股分流
    analyze  -- 三層動能分析引擎 (累計YoY / 多月YoY趨勢 / MoM vs 季節性)
    report   -- 產生單頁 HTML 儀表板
    cli      -- 命令列進入點 (fetch / analyze / report / run)
"""

__version__ = "1.0.0"
