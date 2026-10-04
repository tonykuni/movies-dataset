# VRN LAYOUT 插件架構正本 v0100(操作員 20261004 裁定)

維度:**處理方式 × 資料類型**;插件獨立,選用/升級交 System Manager;LAYOUT 是共用區域切割能力,不等同重型 OCR。

| 處理層級 | TEXT | TABLE | GRAPH |
|---|---|---|---|
| NON_OCR | 原生文字/座標/字體/閱讀順序 | 線框/空白間距/欄列對齊/合併儲存格 | 嵌入圖片/向量/SVG/原生圖中文字 |
| OCR 基礎 | 無文字層或缺字區辨識 | 已切好表格的文字數字重建欄列 | 圖名/座標軸/圖例/資料標籤 |
| OCR 重型 | 複雜混排/旋轉/低品質/衝突 | 複雜表頭/跨欄列/無框線結構 | 圖表結構/曲線柱形數值還原(需另驗) |

鐵律:圖中文字辨識、圖片抽取、圖表數值還原是**三個功能**;抽出圖片 ≠ 取得圖中數據。

## 結構:6 功能引擎 + 1 外部調度器
TEXT / TABLE / GRAPH / LAYOUT(共用切割)/ VALIDATE(分類型驗證)/ STORE —— 每引擎內插件可插拔;新函式庫=加插件,不加主引擎。外部調度 = System Manager(按 `VIA_LayoutPlugins_Registry_v0100.json` 選用)。

## 執行路徑(由輕到重,成功區鎖定只補救失敗區)
1. pdfplumber 單引擎+輕量 LAYOUT:一次取文字/字體/座標/線條,重用解析;先分首頁本文/資訊區,再切上下左右表格。
2. 每區分別驗證:同頁可同時 TEXT 綠、TABLE 紅、GRAPH 待;綠區鎖定。
3. 補一個互補 NON_OCR 引擎:雙引擎各留結果與來源,不覆蓋。
4. 無文字層才進**局部**基礎 OCR:結果回填 LAYOUT 區座標;pdfplumber 只做原生對照,不 OCR。
5. 少數失敗區才重型 OCR/結構模型;只有解析度不足最後才 350 DPI(欄列切錯不靠 DPI 解)。

## 驗證分型
TEXT:缺字/重複/閱讀順序/數字單位 · TABLE:列欄數/表頭期間/單位/堆積/合計比率 · GRAPH:圖名圖例軸單位來源齊全+還原值對原圖 · LAYOUT:重疊/漏區/本文資訊混入/異表黏合。
綠=指定驗證過;黃=有產出未全驗;紅=失敗。雙引擎一致仍須對照來源。

## 現況
- `functional modules/VRN/VRN_NewPlugins_v0102.py`:9 支 NON_OCR 插件(pdfium/pdfrw/pikepdf/xpdf/qpdf/pdfcpu/exiftool/ghostscript/pdf2json),錯誤隔離,get_plugins()/ast_catalog() 容器實測可載。
- `supportive modules/registry/VIA_LayoutPlugins_Registry_v0100.json`:規格冊(PLUGIN_SPEC 映射;validation 全 UNTESTED 誠實標示;plugin_id/central_id 待 VCGC 配發)。
- OCR 基礎/重型層:未含,沿同一插件契約後補。

## 現況更新(2026-10-05;上段照不刪字律保留)
- **OCR 基礎層已入倉**:`functional modules/VRN/VRN_OCRPlugins_v0100.py` 三功能三支(鐵律一功能一支):
  `ocr.image_extract`(抽圖≠取數,ocr_used 恆 False)· `ocr.text_recognition`(字框+信心值,低信心丟棄)·
  `ocr.chart_restore`(基礎層:軸刻度 OCR+等差校驗;逐點還原屬重型層,series_values 誠實 None+NEEDS_HEAVY)。
  宿主自測 12/12 實跑綠(PR #451)。
- **20 支 local free libs 清點收口**:16 支真轉接器在位實證;`VRN_LibPlugins_v0100.py` 補位 5 支
  (mutool/pdfbox/borb 真接頭;lopdf/itext 座位制=收自備接頭路徑,缺=誠實 UNAVAILABLE 非空殼)。
  覆蓋矩陣入冊 `VIA_LayoutPlugins_Registry_v0102.json`(17 支;v0100/v0101 凍結)(PR #452)。
- **六引擎殼實體化**:`VRN_ENG400_SixEngineShell_v0100.py`——FILE(全新)/LAYOUT(ENG394 委派)/
  TEXT/TABLE(吃 LAYOUT 產物;寬表+長表)/GRAPH(插件)/OCR(共用一套+px→pt 回填);
  五段結構 · 四階段配方存殼選用交 System Manager(`view` 動詞)· 統一產物鏈
  文件ID→頁碼→區域ID/座標→引擎與插件版本→參數→驗證結果。雙環境 12/12(PR #453)。
- **中央編號**:ENG400+插件批 78 席已入冊(registry-sync APPLIED · AST錯 0 · 撞號 0;audit 三零)。
- 仍待:OCR 重型層(掛 ENG400.OCR heavy 座位,需另驗)· lopdf/iText 自備接頭(cargo 專案+jar)·
  真 PDF 逐件認證(validation 欄待宿主轉綠)· borb/lopdf/iText 以外的 PENDING 無。
