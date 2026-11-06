# VIA Atlas · Manus HTML U/I 視覺鎖定紀錄(2026-11-06)

操作員令:「https://manus.im/share/jlcCGjChDJG1KgzkR8YtIz · https://viaatlas-39ozanmz.manus.space 以他的 HTML U/I 為視覺鎖定版本 · 不可動 · 只能動內容」。

## 1. 鎖的是什麼(倉內正本 · 外站只是展示)

| 項 | 倉內路徑 | 版本 | 鎖法 |
|---|---|---|---|
| VIA System Atlas(Workflow Atlas) | `review/VIA_Atlas_LocalSite_v0100/index.html` | v0103 頁 · 站包 v0100 | 位元組鎖:`SHA256SUMS.txt` 四檔 `sha256sum -c` 全 OK(2026-11-06 容器) |
| VIA System Architecture & Integration Blueprint | `review/VIA_Atlas_LocalSite_v0100/architecture.html` | v0103 頁 | 同上 |
| 站包說明 / 清單 | `README.md` · `manifest.json`(`VIA.LocalStaticSiteManifest.v1` · `source_inputs` 兩份 v0103 HTML 的 SHA) | v0100 | 同上 |
| VAP 自動繪圖工作台 U/I(Manus) | `functional modules/VAP/intake/allinone_v0300/VAP_AllInOne_UI_v0300.html`(原件 · 一字不動)· `VAP_AllInOne_UI_v0301.html`(Codex P1 一行修) | v0300 / v0301 | 原件位元組在 `SHA256.txt`;v0302 引擎沒改 U/I |

外站(manus.space / manus.im 分享頁)VIA 不抓、不部署、不連:`manifest.json` 寫明 `website_deployment: NOT_DEPLOYED` · `builder_contacts_github: false`;內容真相 = 倉內檔案。

## 2. 規則(不可動 / 只能動內容)

1. **不可動**:上表四檔與 VAP U/I 的 HTML 結構 · CSS · 內嵌 JavaScript · 版面 · 色盤 · 字級 · 導覽(「VISUAL LOCK」標頭就是這個意思)。不在原檔上改一個位元組;SHA 對不上就不是鎖定版。
2. **只能動內容**:
   - Atlas 兩頁的內容(六系統狀態 · B1–B5 阻礙 · 狀態矩陣 · 契約 · 工具清單)來自 `manifest.json.source_inputs` 的兩份 v0103 HTML;要改內容 = 由同一條 Manus 產線出新版頁(v0104)→ 新站包夾 `review/VIA_Atlas_LocalSite_v0101/`(add-only · 自帶 `SHA256SUMS.txt` 與 `manifest.json`)。v0100 夾永不改。
   - VAP U/I 的內容 = 資料:VQG `export-vap` 給的表(SERIES / INDICATOR_RESULT)· 連線證據 · 模板;U/I 只讀 runtime(`/api/catalog`),畫面上的表名 / 欄名 / 語意都從資料來,U/I 檔不動。
3. 需要修 U/I 本身的缺陷(例 v0301 的 `fallback is not a function`)= 出新版號檔(`_UI_v0301.html`)+ 引擎 `DEFAULT_UI_RELATIVE_PATH` 指過去;原件留存。這是「修缺陷」不是「動視覺」:結構 · 樣式 · 版面不變。
4. SettleAll ⑯ 衝突偵測會列出同名不同內容;`review/` 與 `reference` 夾算軟夾(撞號只黃不紅)。

## 3. 本輪實測證據(容器 Chromium · 2026-11-06)

| 頁 | 視窗 | 結果 |
|---|---|---|
| `index.html` | 1366×900 | 標題「VIA System Atlas · v0103」· h1「VIA System Atlas / ENG049 v0102 VISUAL LOCK」· 表 3 · 區 18 · 文字 11,858 字 · 0 主控台錯 · 0 外連請求 · 頁面不橫向捲動(scrollW = clientW) |
| `index.html` | 390×844(手機) | 同上 · scrollW 390 = clientW 390(不橫向捲動) |
| `architecture.html` | 1366×900 | 標題「VIA System Architecture & Integration Blueprint · v0103」· 表 5 · 區 18 · 0 錯 · 0 外連 · 相對連結 `index.html` 互通 |
| `SHA256SUMS.txt` | — | `index.html: OK` · `architecture.html: OK` · `README.md: OK` · `manifest.json: OK` |
| VAP U/I v0301(v0302 引擎) | 1366×900 | 12 個導覽面板 · 資料庫對接 → 更新所有連線 → 配對繪圖 4 張 VQG 表 → 雙軸圖畫出 · 使用者流程 01–07 PASS · 0 主控台錯(見 `VIA_VQG_to_VAP_Contract_20261106.md` §6) |

截圖(容器 · 不入倉):`atlas_index_desktop.png` · `atlas_index_phone.png` · `atlas_architecture_desktop.png` · `vap_v0302_render_indicators_2330_TW.png`。

## 4. 操作員要看時

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics\review\VIA_Atlas_LocalSite_v0100"
Get-FileHash "$r\index.html","$r\architecture.html","$r\README.md","$r\manifest.json" -Algorithm SHA256 | Format-Table Hash,Path   # 對 SHA256SUMS.txt
Start-Process "$r\index.html"    # file:// 直接開 · 不需伺服器
```
