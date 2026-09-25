"""台股月營收動能引擎 (Taiwan Stock Monthly Revenue Engine).

模組:
    fetch    -- 從 MOPS 公開資訊觀測站抓取全上市/上櫃月營收 (含產業別)
    store    -- parquet (SSOT) + duckdb 累計增量資料庫
    classify -- 產業分類 + 全市場六大週期類分流
    groups   -- VIA 熱門族群層 (龍頭/第二梯隊/落後) 與族群加總動能
    analyze  -- 三層動能分析引擎 (累計YoY / 多月YoY趨勢 / MoM vs 季節性)
    breakout -- 真突破偵測 (創歷史新高 + 年增強 + 排除低基期假象)
    report   -- 單頁 HTML 儀表板 (VIA 視覺鎖定, 紅▲成長 綠▼衰退)
    tests    -- 內建自我測試
    cli      -- 命令列進入點
"""

__version__ = "2.0.0"
