# 報告規格:矩陣 · 專業 · 字小 · 版面自動調節

## 1. 三種輸出(同一份資料)
- `panorama_<runid>.html` + `panorama_latest.html`
- `panorama_latest.txt`(給貼回對話 / 終端機;各段 `fit_table` 純文字表)
- `panorama_latest.json`(全部原始欄位,給下一輪或別的工具);另一行 append 到 `universal_ledger.jsonl`
- 標準輸出只印**省 Token 卡**(≤ 15 行);`--json-only` 只印 JSON 路徑;`--rich` 且有裝 rich 時另把各段表印到終端。

## 2. 頁面結構(固定次序;每段一張矩陣)
1. **總燈列**(小卡):目標 · 來源(local/github)· SHA16 · 檔數 · 範圍 · 總判 · 棘輪(昨/今/差)· 秒 ·(有隔離區時)名數 / 組數。
2. **總覽矩陣**:段 × 燈 × 紅數 × 非綠列 × HOLD —— 先看這張。
3. **A 拓樸快照**(OP-100):語言 × 檔數 × 位元組 × 尾版 × 舊版 × 未追蹤;細項:大檔 · 重複群前 20。
4. **B 家族尾版**:家族 · 尾版檔名 · 版數 · 最舊 · 最新 · 燈(同族分散多夾 = 黃;隔離區 = HOLD)。非綠排前面。
5. **C 靜態合規**(OP-200;Tier-0 標記,`--static` 時加 AST 列):標記 · 有 · 缺 · HOLD · 覆蓋率 · 第一個缺的路徑;細項:各標記缺的路徑。
6. **D 治理資料**:工具鎖(鎖版 = 樹上最新?)· 樹上最新釘版 · 隔離區 Q1–Q4 與逐名 HOLD · 交接冊與驗收燈 · 帳本末筆燈 · 治理檔可解析。
7. **E 漂移**(有 git 時):分支 · HEAD 本機/origin · 領先/落後 · 未提交 · 未追蹤 · stash · worktree · merge 預測(`--predict`)· 尾版本機 ↔ origin;細項:本機獨有 commit 分類 · 原因表(位置 · 問題 · 影響 · 解法)。
8. **F 分級佇列**(OP-300/400/500):各級數量;細項:OP-300 路徑 · OP-400 簽名 → 檔 · OP-500 濃縮包(路徑:行號 · 簽名,無原文)。
9. **G 棘輪**:前一筆 · 本筆 · 差 · 判定(RETROGRESS / OK / NODATA)。
10. **H 邊界**(照實):量了什麼 · 沒量什麼 · 引擎降級次數 · 名冊 ≠ 權限 · 棘輪基準。
11. **歷史矩陣**:同目標最近 12 輪 × 各段燈 × 紅數 × 秒。
每段 > 25 列時只放前 25,其餘收進可展開的 `<details>`;> 500 列見 JSON。

## 3. 版面自動調節(`fit_table()`)
- 量寬:`--width`(預設 140 欄;窄終端給 80)。每欄算內容最大寬,並有上限(key 64 · 說明 60 · 數值 14 · 燈 6)。
- **欄優先級**:`key`(路徑/名稱)> `lamp` > 數值欄 > 說明欄。空間不夠時依序:說明欄縮到 12 並以 `…` 截斷 → key 縮到 24 → 最後才隱藏說明欄(表尾註明「省略欄:…」)。
- **密度**:> 200 列只印前 N(`--top`,預設 60)+ 尾 5 + 「其餘 n 列見 JSON」。有 rich 時:≤ 25 列 `box.SIMPLE_HEAD`、`padding=(0,1)`;其餘 `box.MINIMAL`、`padding=(0,0)`、`row_styles=["", "dim"]`。
- **燈欄固定 6 字寬**;數值右靠;路徑左靠、以 `…` 中段截斷(保留檔名尾 24 字寬);全形字算 2 寬。
- **顏色**:專業、低飽和。GREEN `#2e7d32`、YELLOW `#b58900`、RED `#c62828`、HOLD `#6d6d6d`(斜體)、ABSENT/NODATA `#8a8a8a`。不畫 emoji,不用漸層;寬終端與窄終端(80 欄)都要能看;手機寬度 HTML 無水平捲動(已用無頭 Chromium 390 px 驗過)。

## 4. HTML CSS(注入 `<style>`;字小、專業)
```css
body{margin:0;padding:20px;background:#fafafa;color:#222;font:11px/1.45 "JetBrains Mono","Cascadia Code","SF Mono",Consolas,"Noto Sans Mono CJK TC",monospace}
pre{font-size:11px;line-height:1.35;white-space:pre;overflow-x:auto;margin:0}
h1,h2{font-weight:600;font-size:12.5px;letter-spacing:.02em;margin:14px 0 4px;color:#333}
@media(prefers-color-scheme:dark){body{background:#111318;color:#d8d8d8}h1,h2{color:#cfd3da}}
```
(引擎另加表格、小卡、`<details>` 與深色模式的表格線樣式。)

## 5. 結束碼
`0` = 總判 GREEN(隔離區 HOLD 不算紅;不適用的段如非 git 的 E 段不計)· `2` = 有 YELLOW / ABSENT / NODATA · `1` = 有 RED 或棘輪 RETROGRESS · `3` = 目標讀不到。

## 6. 輸出夾
`--out <夾>`;沒給時:`via` profile 落 git 忽略的 `<VIA>/VIA_Reports/panorama`(`git check-ignore` 核過才用);其他本機目標落 `<cwd>/.panorama`,cwd 在目標內則 `~/.via_panorama`;GitHub 目標落 `<cwd>/.panorama`。
