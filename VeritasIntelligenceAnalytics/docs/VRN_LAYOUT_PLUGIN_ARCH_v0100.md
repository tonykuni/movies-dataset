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
