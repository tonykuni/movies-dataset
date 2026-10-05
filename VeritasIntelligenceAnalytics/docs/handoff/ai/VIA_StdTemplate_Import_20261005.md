# VIA 標準模板導入(2026-10-05 · VCGC-REQ168)

操作員上傳 5 檔並令「導入模板」。

## 上傳檔核對

| 檔 | sha256(前 12) | 結論 |
|---|---|---|
| VIA-Standardized-Template-Updated-2026-09-20.zip | 437036d88360 | 與 `.sha256` 檔一致(19.3 MB · 275 檔) |
| VIA-Complete-System.html | d761a98d87b3 | = 倉根 VIA_HTML_UI = VIA/VIA_HTML_UI |
| VIA-UI-Standalone-NoServer.html | b2aeb8f6d7bf | = 倉根 VIA_HTML_UI(09-20);**舊於** VIA/VIA_HTML_UI(b71f4fa4f8a4,09-25 修正版) |
| VIA-SYNCHRONIZER-Standalone.html | 047e56235cf6 | = 倉根 VIA_HTML_UI(09-20);**舊於** VIA/VIA_HTML_UI(e19f2bcc7a20,09-25 修正版) |

zip 對正典:倉根 226 檔中 223 相同、manifest.json 不同;zip 另有 51 檔(多為 `qa/ci-reports/**` 跑測紀錄),
沒有倉內自加的 `REPOSITORY-INTEGRATION.md` 與 1 張截圖。VIA/VIA_HTML_UI 另有 2026-09-25 操作員授權修正
(SYNCHRONIZER 同時戳同版本重送 · 中央 UI toast 作用域)與 CHANGELOG。

## 做法

- **正典零觸碰**(批647 byte-exact · manifest 守):不以 09-20 上傳件覆蓋,避免倒退 09-25 修正。
- 導入 = 讓 U/I 引擎(CGC_MDL261)可選用:把**最新正典**(VIA/VIA_HTML_UI/ui,09-25)三入口以版號名放入
  `supportive modules/ui_support/ui_templates/`:
  - `VIA_StdTemplate_CompleteSystem_v0100.html`(啟動台)
  - `VIA_StdTemplate_CentralUI_v0100.html`(中央管理 UI)
  - `VIA_StdTemplate_Synchronizer_v0100.html`(SYNCHRONIZER)
- 實測:`via-uieng templates` 認得 5 份範本;三份各自 `build --template` 產頁(283 / 459 / 376 KB),
  headless Chromium 開啟 JS 錯誤 0、`window.VIA` 注入(tool · built · home · config · sources · duckdb · env)。
- 用法:`via-uieng build --template VIA_StdTemplate_CentralUI_v0100.html`,或 `via-uieng config` 設 active_template。
- 注意:啟動台頁的「開啟中央 UI / SYNCHRONIZER」連到同夾的兄弟檔;單獨產出時那兩個連結要另產同夾檔才點得開。

## 未做(待裁定)

- 倉根 `VIA_HTML_UI/` 與 `VeritasIntelligenceAnalytics/VIA_HTML_UI/` 兩份正典不一致(後者較新)。是否以後者同步前者 = 正典變更,需操作員點頭。
- zip 多出的 51 檔 QA 紀錄未入倉(產物,不是原始碼)。
