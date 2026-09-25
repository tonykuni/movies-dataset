# VRN 報告擷取+摘要規格書(操作員批236 貼入;收容摘錄)
血統:操作員對話貼入 2026-08-28;本檔=忠實摘錄契約錨點;
實作進度:批236 已落=分區 LAYOUT/本文修復/字級階層(ENG072 v0101);
其餘=分波候令。

## 擷取契約(12 def 摘錄)
- 四路來源:Filename(候選值不覆寫)/第一頁本文/上左上右資訊區(BBox 分區)/財報頁
- 兩類資料:Basic Info 30 欄+Financial Data 76 欄;每欄保存原文/修復值/標準值/來源位置/信心/裁決
- 分區:Top Header(y0-18%)/Upper Left(x0-55%)/Upper Right(x55-100%)/Main Narrative/Footer;動態版型偵測非死切
- 修復順序:Unicode→中文→英文→數字(O/0,I/1)→負數((1,250)/△)→期間(24E→2024E)→單位→科目(SynonymEngine lookup)
- 三層隔離:REPORT_ACTUAL/REPORT_ESTIMATE/OFFICIAL_ACTUAL 不互覆寫
- 對照前置九條件(公司/期間/頻率/合併範圍/AEC 狀態/幣別/單位/重編/口徑/EPS 基稀)
- 三級對照:文件內→跨頁→外部(MOPS/TWSE 僅驗證不取代文件事實)
- 公式驗證:GP≈Rev-COGS/OI≈GP-OpEx/EPS≈歸母淨利÷加權股數/年≈四季和
- 差異分類 12 態:EXACT_MATCH…MANUAL_REVIEW(UNIT/PERIOD/SCOPE/STATUS_MISMATCH 先於 VALUE_MISMATCH)
- 雙 SSOT:DOCUMENT_TRUTH+ECONOMIC_TRUTH;衝突=KEEP_BOTH 永不靜默覆寫
- 欄位稽核 JSON:raw/repaired/canonical/currency/unit/period/status/page/bbox/method/confidence/comparison_status
- 目標價驗證:Upside=TP/Price-1;差=ROUNDING_ONLY 或 FORMULA_MISMATCH

## 摘要契約(13 def 摘錄)
- 架構:決定性擷取→多引擎候選→證據排序→本機 LLM 修整→數值防幻覺驗證;LLM 只重組不創造
- SSOT:標題「券商-Ticker公司-評等-日期」+四點中英雙語(投資結論/財務成長/產業公司/催化劑風險);每句連回 Evidence ID;缺=「報告未提供」
- 評分:0.25Section+0.20Materiality+0.15Numeric+0.15Title+0.10Source+0.10Novelty+0.05Confidence
- Hard Gate:數字全在 Evidence/Derived 冊;中英數字一致;評等目標價過 Basic Info 對照;EPS 過 Financial 對照;衝突不選邊
- 信心:0.30Evidence+0.25Numeric+0.20SourceAgree+0.15Layout+0.10Bilingual;≥0.90 AUTO/0.80 WARN/0.65 REVIEW/<0.65 REJECT
- 估值重算:LatestForwardPE=AdjClose÷DilutedEPS(Est) 必標 DERIVED_CALCULATION 不冒充報告值

## 優化五維(操作員 Gemini 對談摘錄)
降噪(圖表座標軸數字/浮水印/免責)/表格重建(壓平列→Markdown|JSON)/
Metadata 層級化/斷句重組/內容標籤(摘要|財測|QA|展望)
