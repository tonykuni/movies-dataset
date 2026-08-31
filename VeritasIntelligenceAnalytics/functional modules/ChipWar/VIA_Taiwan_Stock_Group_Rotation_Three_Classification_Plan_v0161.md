# VERITAS INTELLIGENCE ANALYTICS

DISCIPLINA • PRUDENTIA • INTEGRITAS

## VIA Taiwan Stock Group Rotation Simulation · Three-Classification Text Plan v0161

本版只更新文字規格與 VDF 資料請求，不建立、修改或啟用分類引擎。

## def 01 · 核心原則

- 所有日期、視窗、權重、分界、熱門股數量、再平衡頻率與信心門檻均為 runtime 參數或 walk-forward 學習結果；不得在模型內永久固定。
- 不以固定成交量或固定成交值界定大型／中型／小型；每個再平衡日只使用當時可得資料，重新估計橫斷面分布與三群邊界。
- 不允許模擬或隨機生成法人、融資融券、當沖與維持率資料。缺資料必須保留空白、來源狀態與原因。
- 價格空白可引用同一證券前一交易日作為基準並加旗標；成交量、成交值、法人、信用與當沖不得向前填補。
- 美股與全球資產以來源市場交易日保存，另建立 `Taiwan Effective Date` 對齊下一個台股交易日，禁止未來資訊。

## def 02 · 三個分類引擎

### def A · Dynamic Liquidity Size Classification

輸出「交易型大型股／交易型中型股／交易型小型股」，避免與法定或傳統市值分類混稱。

- 原始特徵：調整後成交量、成交值、成交天數、成交穩定度、零成交率、價格衝擊、換手率與可取得時的自由流通市值。
- 各特徵先做橫斷面 robust scaling，再由 walk-forward 驗證決定特徵權重；不得固定權重。
- 每個再平衡日以三狀態分群模型估計邊界，再依各群成交值中位數排序為大型、中型、小型。
- 使用動態遲滯與最短持有狀態降低頻繁跳級；遲滯幅度由歷史交易成本與分類穩定度共同校準。
- 輸出：主分類、三群機率、信心值、有效起訖日、邊界快照、模型版本與資料截至日。

### def B · Ownership and Control Classification

主標籤為「外資偏好／內資法人控盤／大戶控盤」，同時保存三個連續分數，避免只靠單日買賣超強迫分類。

- 外資偏好：外資買賣超持續性、成交占比、持股趨勢、買賣超對報酬的價格衝擊與不同市場狀態下的一致性。
- 內資法人控盤：投信與自營商淨流量、連續買賣、流量占成交值、外資相對弱度與報酬反應。
- 大戶控盤：TDCC 大戶持股分級、持股集中度、券商分點集中度、量價反應與籌碼穩定度；若尚未接入 TDCC／分點資料，只能輸出 `Large Holder Control Proxy`，不可輸出精確結論。
- 標籤依三分數的動態相對優勢決定；若差距不足或資料不足，仍保留最高分標籤，但必須標示 `LOW_CONFIDENCE` 或 `MIXED_EVIDENCE`。
- 輸出：三分數、主標籤、信心值、證據覆蓋率、主導來源、有效起訖日與資料缺口。

### def C · Latest Group Taxonomy Classification

- 所有台股至少有兩層：`Primary Industry` 與 `Value Chain / Business Role`。
- 最新熱門股集合再增加第三層：`Active Theme / Rotation Group`；熱門股數量由動態流動性選股決定，不固定為某個數字。
- 同一股票可屬多個族群，使用 membership weight，而非只有一個硬標籤。
- 同義字、縮寫、公司別名與 Regex 由 VIA Central Government Console 統一管理；VDF 只消費已核准 SSOT。
- 每個分類必須保存來源、證據、信心值、版本、有效日期與 superseded 關係，才能重建任一歷史交易日當時可知的族群。

## def 03 · 整合輸出

三個分類以 `Date + Ticker + Classification Version` 合併，但各引擎仍保持獨立分數與證據：

| Layer | 必要輸出 |
| --- | --- |
| Liquidity Size | Large / Mid / Small、三群機率、動態邊界 |
| Ownership Control | Foreign / Domestic Institution / Large Holder、三分數、信心 |
| Group Taxonomy | Industry、Value Chain、Active Theme、membership weight |

整合後才交給 Group Rotation Simulation 建立等權、成交值權重與自由流通市值權重三種族群指數，並分開回測，不能先選表現最佳的分類再回填歷史。

## def 04 · VDF 資料底座（2023-01-02 至最新為本輪預設，可覆寫）

| Dataset | 主要內容 | 主要來源 |
| --- | --- | --- |
| TW Equity Daily Market | Adj O/H/L/C、Volume、Turnover、TAIEX、TPEX Index | TWSE／TPEX；YFinance 僅作價格備援 |
| TW Equity Daily Institutional | 外資、投信、自營商買／賣／淨額 | TWSE／TPEX |
| TW Equity Daily Margin | 融資融券進出與餘額、券資比、維持率代理值 | TWSE／TPEX；精確維持率須帳戶級資料 |
| TW Equity Daily Day Trade | 當沖量、買賣與成交值、占比 | TWSE／TPEX |
| Global Macro Daily | S&P 500、SOX、KOSPI、DXY、匯率、原油、黃金、VIX、Bitcoin、利率 | YFinance／FRED／TPEX／BOJ／ECB |

標準輸出同時產生 Parquet 與 CSV，採增量更新、斷點續傳、去重、來源血緣、資料品質旗標與 append-only manifest。Parquet 建議按 `Dataset / Market / Year` 分割，避免將全部資料載入記憶體。

## def 05 · 後續測試順序

1. 資料契約與來源覆蓋測試。
2. 2023-01-02 起的完整回補與最新日增量測試。
3. 日期、ticker、市場、重複鍵、調整價、法人合計、券資比與當沖占比校驗。
4. 無未來資訊的 walk-forward 分類回測。
5. `test → debug → optimize → test → debug → consolidate → test → debug → user-test → debug → activate → test → debug`。

啟用條件：熱門股三層分類覆蓋、全市場至少兩層分類覆蓋、所有來源血緣可追溯、三輪結果穩定、Hydra 衝突為零，才可進入 activation。
