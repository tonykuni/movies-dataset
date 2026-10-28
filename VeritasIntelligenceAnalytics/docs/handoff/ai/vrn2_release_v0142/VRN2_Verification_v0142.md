# VRN-2 v0142 容器實測紀錄(2026-10-28)

操作員令:回到電腦本地實測修正(貼回 v0136 線 52 份輸出:四點截斷 / 頁首混入 · 剔除 654 · 缺項 10) / 模板視覺鎖定作為前端 html u/i 與後端連棟整合為一個系統 · 透明去背 logo 無框無特效取代模板 logo(上傳 VIA_VRN-2_Workbench_-_Standalone.html)

## 1. 本輪改了什麼

| 元件 | 版本 | 內容 |
|---|---|---|
| 摘要器 ENG062 | v0117 | after v0116 selection, the left edge of a chosen span is moved past leading page-banner lines (Company | Asia Pacific), lines that are (part of) the report title (also when glued to the first sentence), and short section headings followed by a new sentence; wrapped first words and preposition-led lines are kept; remaining span must still be eligible; raw_span/quote/quote_sha256 rewritten; validate_summary re-checked |
| Workbench U/I | VRN2_Workbench v0100 + Assets v0100 | template CSS/markup locked verbatim; {{ fields }} / sc-for / sc-if expanded server-side from receipts + output books; vrn2:// actions; gates only for registered entries; dataset paging / CSV / extract / page export in vanilla JS; logo auto-transparent (white → alpha, un-premultiplied edges, cropped) as data URI with no background / radius / shadow; fonts from VRN2_Workbench_Assets_v0100.zip (117 woff2) referenced relatively; falls back to system fonts and the template glyph |
| 啟動器 | ActivateVRN-2 v0142 | v0141 + runtime v0142; after the closeout receipt: render Workbench, add a link bar to the legacy U/I page, open the Workbench (fallback legacy); receipt gains 'workbench' |

## 2. 自測

| 項 | 結果 |
|---|---|
| ENG062_v0117 | PASS (banner / title / glued title / heading trimmed · wrapped word · preposition · CJK heading · exact spans · tamper rejected) |
| Workbench_v0100 | 16/16 |
| manager_v0243_with_v0117 | PASS |
| launcher_v0142 | PASS (+ workbench link / render fallback / open fallback) |

## 3. 摘要器 v0117 · 容器 9 份真檔(操作員 52 份裡在容器的真檔)

| 檔 | 點 | v0116 | v0117 |
|---|---|---|---|
| GS-6415 20260517.pdf | P1 | Dual growth engines moving into focus  ⏎We are turning more constructive on Sile | We are turning more constructive on Silergy and upgrading the stock ⏎to Buy from |
| MS-3661 20251203.pdf | P2 | Alchip Technologies Ltd \| Asia Pacific⏎Read-across from AWS re:Invent ⏎and Marve | Trainium3's revenue contribution to Alchip should stay intact, ⏎while Alchip sho |

其餘 8 份的點逐字相同。操作員貼回的 v0114 輸出:52 份 · 三點裡沒有句尾的 87 個(截斷 / 頁首 / 標題重複 · v0115 起的逐字切句已無此類;v0117 再去掉開頭的頁首 / 標題 / 小標題列)。

## 4. 沙盒全流程(套件 v0142 · 19 份真檔)

| 項 | 結果 |
|---|---|
| 收尾 rc | 1(③ 環境檢查 RED in the Linux sandbox only (accelerator deps not in venv; --no-install); every VRN-2 gate GREEN unless listed)|
| 非綠步驟 | [['③ 環境檢查與補裝', 'RED'], ['⑥c U/I 操作協定', 'GRAY'], ['⑨ 上船 GitHub', 'GRAY'], ['⑩ 整併封存', 'GRAY'], ['⑫a VRN-1 倉同步(借工具前 · 只 fast-forward)', 'GRAY'], ['⑫ PIVOT 資料庫(借用 VRN-1)', 'GRAY']] |
| 輪數 / 冪等 | [[1, 0, 'idempotence GREEN']] · GREEN |
| ⑧ 完成判定 | 完成 · 紅 0 黃 3 · VRN-2 SystemManager v0243 |
| ⑦ 個股四項 | 14 份 · 全綠 14 |
| 四點原文核對 | {'PASS': 52, 'OCR_PENDING': 4} · 缺項 [{'book': '四點原文核對', 'reason': "REVIEW_OCR · {'PASS': 52, 'OCR_PENDING': 4}"}] |
| 摘要 | 14 份 · 四點齊 True · 層級 {'strict': 56} |
| ⑪ 獨立驗證 | VRN2_IndependentVerifier_v0110 · 錯值 0 · 基本資料 {'PASS': 193, 'OCR': 2} · 四點 {'PASS': 65, 'OCR': 5} · 年度 4905 筆 {'ALIGNED': 4378, 'TRANSALIGNED': 75, 'SUBALIGNED': 452} |
| Workbench | GREEN · …ad/v142/t142/VIA/VIA_Reports/vrn2/VRN2_Workbench_latest.html · 舊版 U/I 連結 True |

## 5. 真瀏覽器(Chromium · Playwright)

| 頁 | 結果 |
|---|---|
| Workbench(t141f 收據)| 17/17 |
| Workbench(本輪全跑收據)| 17/17 |
| 舊版 U/I(含 Workbench 連結列)| 35/35 |
| 一鍵情境(pwsh · 第一次從假 GitHub 分支下載套件 → 再貼(本機已驗證)→ 竄改啟動器(偵測 · 從已驗證 zip 重解))| first rc 1 · again rc 1 · tamper rc 1 · done(rc 1 = 沙盒 ③ 環境檢查 RED,與 §4 同;③ 取件 / 雜湊 / 逐檔核對 / 竄改偵測 / Workbench 皆綠)|

## 6. 沒有宣稱的

- Windows run on C:\測試樣本報告 (52): only 9 of those PDFs are real in the container; the other 43 are synthetic stand-ins — the v0117 trim is proven on the 9 real + the sandbox 19, not on all 52
- The seal logo image was shown in chat but not uploaded as a file: the Workbench ships with the logo slot + auto-transparency and renders the template glyph until VRN2_Logo.png/jpg is placed
- Workbench 矩陣一 delete / restore (recycle) and the dedupe plan are read-only in v0100 (buttons explain); the vrn2:// handler v0104 still reopens the legacy U/I after pick/run (it now carries a Workbench link bar)
- 剔除冊 654 / 一格多值 / 表頭在表外 (desktop line v0254 work) untouched; MQ-1560 four points stay OCR_PENDING by design
