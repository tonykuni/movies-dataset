# VRN P1VIEW 擷取列契約 · v0100 · VIA.VRN.P1ViewRecordsContract.v1
產生者:VRN_ENG397_P1Segment (v0108+ 每次執行自動寫出) via VRN_SystemManager p1view / p1loop

## 檔案
- **records_csv**:C:\Users\tonyk\AppData\Local\Temp\vrn2_idem_jw9kecwf\rep\p1view\P1VIEW_records_latest.csv
- **json**:C:\Users\tonyk\AppData\Local\Temp\vrn2_idem_jw9kecwf\rep\p1view\P1VIEW_latest.json
- **md**:C:\Users\tonyk\AppData\Local\Temp\vrn2_idem_jw9kecwf\rep\p1view\P1VIEW_latest.md
- **lock**:VIA_Reports/vrn/p1view/VRN_P1View_Lock_latest.json (綠燈檔案鎖定 · 只增不減)
- **rounds**:VIA_Reports/vrn/p1view/VRN_P1View_Rounds.jsonl (每輪 append-only)
- **ocr_queue**:C:\Users\tonyk\AppData\Local\Temp\vrn2_idem_jw9kecwf\rep\p1view\ocr_queue

## 範圍
- input:C:\測試樣本報告 (VRN input_dir)
- pages:每份 PDF:第 1 頁 + 年度財報頁(≤4 頁 · 關鍵字 + 數字比例 ≥18% 或 期間表頭列 ≥2)
- skipped:Word / TXT / 圖片 暫不處理(只計數)

## 座標
- origin:頁面左上角
- unit:pt(PDF 點 · pdfplumber 座標)
- fields:X0 / TOP / X1 / BOTTOM 為區塊外框;表格儲存格座標在 JSON 的 rows 不保留 · 以區塊框 + ROW/COL 定位

## 欄位(records_csv)
| 欄 | 型別 | 說明 |
|---|---|---|
| FILE | str | PDF 檔名 |
| PAGE | int | 頁碼(1 起算) |
| ZONE | str | 區編號 P{頁}·{大類}·{序號 2 位}·{小類} · 例 P2·FL·03·TB |
| MAJOR | enum | 頁首=T · 頁尾=B · 左資訊區=L · 右資訊區=R · 本文=M · 財報全幅=F · 財報左半=FL · 財報右半=FR |
| MINOR | enum | 標題=TT · 文字=TX · 本文段落=TX · 本文(全幅)=TX · 全幅文字=TX · 表格=TB(有格線) · 財報表=TB(無格線 · 逐格) · 表名 / 標題=TT · 評等 / 目標價=RT · 股價資料=SD · 分析師=AN · 免責 / 揭露=DS · 日期 / 報告資訊=DT · 圖=IMG(點陣) · 圖表(向量)=FG |
| KIND | enum | 文 / 表 / 表文 / 圖 |
| X0 | float |  |
| TOP | float |  |
| X1 | float |  |
| BOTTOM | float |  |
| ROW | int | 表格:列序(0 起);文字:記錄序 |
| COL | int|empty | 表格:欄序(0 = 科目 · 1.. = 期間欄);文字:空 |
| REC_KIND | enum | 標題=無句號一行一筆(行首項目符號已去) · 句=到句號一句一筆(跨行已接 · 不接到標題) · 資訊=資訊區一行一筆(標籤:值 · 不串句) · 格=表格儲存格 |
| TEXT | str | 已 TRIM · 中文字間無空格 · 全形英數轉半形 · 私用區 / (cid:N) 已去 · 不含亂碼修復以外的改寫 · v0113 起含擷取後修復(數字接回 · 字母間距 · 錯字表)· 原文留 JSON raw |
| ENGINE | str | pdfplumber | pdfplumber(期間欄對齊) | pypdfium2(換) | pypdfium2(逐格換) | pypdfium2(期間欄對齊 · 逐格換) | pymupdf(換) | ... · 仍錯碼 → OCR 排隊 |
| GARBLED | float | 亂碼比例(0~1):私用區 / 替代字元 / 非行首 (cid:N);常用字比例另見 JSON common |

## 表格列規則
- header_row:COL=0 為空、COL≥1 為期間(2024A / 2025F / FY25 / 1H25 / 112年 / 113F …)的那一列 = 期間表頭;其後每列 COL=0 科目 · COL≥1 數值文字(原樣 · 含千分位 / 括號 / 負號)
- missing_cell:缺格留空(不位移)
- section_rows:只有 COL=0 的列 = 表名或分節標題(如 Valuation)
- blank_rows:表內空白行已併回同一張表

## 燈號
- RED:任一區 needs_ocr(錯碼 · 已切 PNG 排 OCR)
- YELLOW:原因之一:沒找到財報頁 | 財報頁沒切出財報表 | 財報表沒對到期間欄 n/m | 首頁沒抓到評等 / 目標價
- GREEN:以上皆無
- layout_info_only:側欄型(左) / 側欄型(右) / 頁首資訊型 / 單欄型 不影響燈號

## 給 VRN_Main G06 的用法
- use:VRN_Main G06 改吃 records_csv:KIND in ('表','表文') 的列即財報列;依 ZONE 聚合成表 · 以 ROW=header_row 的期間欄對齊
- do_not:不要重算座標;不要去 TEXT 的括號 / 負號(保留給驗算);不要把 TT / 分節列當科目

## 穩定性
- 欄位只增不減 · 新欄位加在最後 · 版本改變時 schema 版號 +1 並留舊欄位
