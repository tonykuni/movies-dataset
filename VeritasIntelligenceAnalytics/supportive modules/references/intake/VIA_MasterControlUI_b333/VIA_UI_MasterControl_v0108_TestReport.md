# VIA Plotly Dashboard／MasterControl v0108 測試報告

- 批次：304
- 測試日期：2026-09-01（UTC）
- 目標分支：`claude/via-system-followup-tz7k9t`
- 正主管理器：`VIA_SYSTEM_MANAGER_v0108.py`
- 本機安全橋：`CGC_MDL095_DeckServer_v0114.py`
- 正式啟用裁決：**待人工啟用審查**

## 結論

本機可執行的生成器、資料契約、HTTP 安全、名稱、DOM、同步保護、離線
Plotly 與 JavaScript 靜態驗證均已通過。真實瀏覽器幾何、焦點與互動 UAT 已建成
Windows bundled Chromium 工作，但本環境沒有 Chromium binary，且下載來源逾時，
所以尚未宣稱瀏覽器驗收或正式啟用已通過。分支成功寫入 GitHub 後，workflow 才能
執行這一層驗收。

## 已執行結果

| 測試層 | 結果 | 驗證內容 |
|---|---:|---|
| Python 語法編譯 | 通過 | 管理器、安全橋、同步狀態台、Plotly 產生器與契約測試 |
| 管理器自我測試 | 10 / 10 通過 | 清冊、左側輸入、七分頁、可讀名稱、Plotly 降級、狀態安全、白名單與模板保護 |
| DeckServer v0114 自我測試 | 19 / 19 通過 | POST／CSRF／同源、`run_id`、全域互斥、狀態封套、安全收件、Windows 保留名與 HTTP 錯誤收斂 |
| SyncStatus 自我測試 | 10 / 10 通過 | 唯讀同步狀態、未知完成率、XSS 編碼、原子輸出與測試隔離 |
| Plotly 產生器缺料模式 | 2 / 2 通過 | 缺少共識／月營收資料時誠實停止，不產生假圖；序列化防注入 |
| MasterControl／HTTP 契約 | 19 / 19 通過 | DOM、正式名稱、生成頁新鮮度、六個副作用 GET 封鎖、Host／Origin／CSRF、參數回傳與 Windows 收件 |
| JavaScript 語法 | 通過 | 生成頁 inline JavaScript 與 Playwright UAT 程式皆通過 `node --check` |
| Workflow／差異品質 | 通過 | YAML 可解析；所有 native 指令顯式檢查結束碼；`git diff --check` 無格式問題 |

未在本機執行的兩項為 Windows PowerShell AST parser 與 bundled Chromium UAT；兩者均已
列入 `.github/workflows/via-master-control-ui.yml`，不可在 CI 綠燈前視為已通過。

## 清冊與介面契約

| 項目 | 驗證值 | 說明 |
|---|---:|---|
| 正式工作項目 | 32 | 主要介面只顯示正式中文名稱；技術鍵值只作傳輸值 |
| 現役引擎 | 76 | 狀態為「已盤點・尚未執行」，不冒充註冊或本次成功 |
| 退役來源引擎 | 119 | 其中 1 項與現役正本同識別碼；主清冊去重後列 118 項 |
| 引擎唯一主列 | 194 | 主名稱無重複、無程式識別碼；技術識別碼預設隱藏 |
| 中央治理模組 | 85 | 人工未核定者使用可讀候核名稱與唯一 E／M 候核序號 |
| 右側報告分頁 | 7 | 運轉總覽、結果矩陣、分析圖表、引擎、模組、讀取規劃、系統連線 |

所有工作參數、批次選擇、收件、目錄搜尋與維運開關均集中於可收合左欄；頁首與頁尾
固定。桌機採橫向工作區，窄螢幕改為抽屜式左欄。可編輯 HTML 模板獨立產生，後續
執行 `ui --no-open` 不會覆寫使用者在模板內的設計調整。

## Windows bundled Chromium UAT 契約

工作檔：`.github/workflows/via-master-control-ui.yml`

分支寫入後，Windows 工作會自動驗證：

1. 1600×900、390×844、320×700 三種視窗無整頁水平溢位。
2. 真捲動後 Header／Footer 仍固定；左側輸入收合後主區完成轉場並擴張。
3. 手機抽屜的 `inert`、ARIA、Escape、backdrop 與焦點回復。
4. 任務只顯示必要參數；日期、代號與分類摘要同步。
5. 七分頁 ARIA 與方向鍵切換，32／194／85 清冊數量一致。
6. `/ping`、收件與工作執行確實使用同源 POST、CSRF、`run_id` 與原參數封套。
7. 第二項批次工作只在第一項同一 `run_id` 進入終態後啟動；任一失敗即停止。
8. API 惡意 HTML 字串只作文字顯示；進度限制在 0–100，無假綠燈。
9. `file://` 只可預覽；即使直接呼叫執行函式或點擊收件區也不送出 mutation。
10. 零 CDN、零外部請求、零未捕捉頁面錯誤，並輸出桌機與手機截圖。

## 已修正的高風險問題

- 移除固定假 `LIVE` 與假綠燈；初始狀態改為「尚未檢測」。
- 狀態與檔名以安全 DOM API 顯示，不用 `innerHTML` 插入外部值。
- `/run` 與 `/intake` 改為同源 JSON POST，要求 Origin、Sec-Fetch-Site、Host 與每次啟動 CSRF token。
- 六個有副作用的舊 GET 路徑固定回 405；狀態回應只保留前端允許欄位。
- 每次工作使用唯一 `run_id` 與精確 `accepted_params`；全域執行租約阻止平行撞車。
- 收件採同目錄暫存、`fsync` 與排他 hard-link；Windows 保留裝置名拒收。
  檔案系統不支援 hard-link 時回結構化 HTTP 500、清掉暫存檔且不覆寫。
- `VIA.ps1` 先以唯一 stash hash 保存 staged／unstaged／untracked 變更，僅允許
  fast-forward，同步失敗不 reset／checkout／clean，stash 套回失敗時保留備份。
- SyncStatus 只讀取／fetch 狀態，不 pull 或改寫工作樹；完成率缺乏可靠分母時顯示未知。
- Plotly payload 防止 `</script>`、`<>&` 與 Unicode 行分隔符注入，輸出採原子替換。

## Plotly 資料就緒狀態

目前標準 Plotly 正本需要的市場共識／月營收前置資料尚未建立，因此主控頁顯示
「等待來源資料」與正確執行次序，不顯示模擬行情或假圖。完成一次 `via` 日更的
⑦b–⑦e 後，可再執行 `via-analysis`；既有離線 Plotly 正本會由同源精確路徑載入，
仍不使用 CDN。

## 重跑命令

```powershell
python .\VIA_SYSTEM_MANAGER_v0108.py ui --no-open
python .\VIA_SYSTEM_MANAGER_v0108.py --selftest
python ".\supportive modules\registry\CGC_MDL095_DeckServer_v0114.py" --selftest
python ".\supportive modules\registry\CGC_MDL096_SyncStatus_v0102.py" --selftest
python ".\functional modules\VAP\engine\VAP_ENG014_StdDashboardTemplate_v0101.py" --selftest
python ".\supportive modules\registry\test_master_control_contract_v0100.py"
node --check ".\supportive modules\registry\uxtest_master_control_v0100.js"
node ".\supportive modules\registry\uxtest_master_control_v0100.js"
```
