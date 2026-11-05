# VIA Atlas Local GitHub Site · v0100

這是靜態 review-site source package，預定存放於公開 GitHub repository 的獨立 review branch；**網站本身不部署、不設定 GitHub Pages、不連接任何 VIA runtime**。GitHub source files 對公眾可見，這不等於已把頁面部署成網站。

## 頁面

- `index.html`：VIA Workflow Atlas v0103，包含六系統、五項阻礙、狀態矩陣、契約、32 項工具與純記憶體模擬除錯。
- `architecture.html`：VIA System Architecture & Integration Blueprint v0103。
- 兩頁以相對連結互通，CSS/JavaScript 內嵌，可直接以瀏覽器開啟 `index.html`（`file://`）；不需要 Node、HTTP server、CDN、資料庫或憑證。

## 公開 repository branch

核准目標：`tonykuni/movies-dataset` branch `via-atlas-static-site-v0100`，路徑 `VeritasIntelligenceAnalytics/review/VIA_Atlas_LocalSite_v0100/`。此處僅存放靜態頁面原始檔，不放入任何 canonical engine 目錄；不建立 Pages workflow/CNAME，不合併至 `main`。

目標 repository 是公開的。本 package 包含六系統狀態、B1–B5 阻礙、來源版本及路徑/雜湊摘要；這些內容會隨 branch 對公眾可見。使用者已明確核准此公開 branch 提交。

## 放入本機 checkout（此步驟尚未執行）

若要把相同的靜態檔案放入 Tony-NB 本機 checkout，可解壓至既有 repository 的 `review` folder：

```powershell
$RepoRoot = 'C:/Users/tonyk/OneDrive/Documents/VeritasIntelligenceAnalytics'
$ReviewRoot = Join-Path $RepoRoot 'review'
New-Item -ItemType Directory -Path $ReviewRoot -Force | Out-Null
Expand-Archive -LiteralPath './VIA_Atlas_LocalGitHub_Build_v0100.zip' -DestinationPath $ReviewRoot
```

此 PowerShell 範例只解壓檔案，不會自動 `git add`、`commit` 或 `push`；本輪遠端分支提交與 Tony-NB 本機 checkout 是兩個分開的操作。

## 安全及證據邊界

- Atlas 的除錯只用合成資料；按下模擬按鈕不會修復或改變真實 RED/BLOCKED 狀態。
- 靜態頁面不連線 VCGC、VDF、VRN、VQG、VAP、Database，也不執行系統引擎。
- `manifest.json` 記錄來源和輸出 SHA-256；`SHA256SUMS.txt` 可用來核對 package 檔案。
- 此 package 是公開 repository 中的靜態 source files，不是 production release、整合完成證明或已部署網站。
