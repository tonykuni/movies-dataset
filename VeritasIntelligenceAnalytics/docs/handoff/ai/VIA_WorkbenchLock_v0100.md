# VIA 自建工作台視覺鎖定 v0100(操作員 2026-11-09「視覺鎖定這個 HTML U/I 自建工作台」)

## 一、正本從哪來、鎖什麼

操作員上傳審查包 `VIA_Subsystem_Workspaces_Review_Kit_v0106_4_20261106.zip`(SHA-256 `77d8feb5…`,與 sidecar 一致;收據 PASS_ACTUAL_ZIP_CLEAN_EXTRACT · 55 檔)。
它的 U/I 自稱 **ENG049 v0102 VISUAL LOCK**。本輪把它的四個視覺檔抽出來位元組鎖在 `review/VIA_Workbench_LockSite_v0106_4/`
(css 22,575 B · 頁模板 10,644 B · js 48,105 B · 標誌 png 278,282 B;`SHA256SUMS.txt` 4/4 OK)。

鎖的內容(由 `VIA_WorkbenchLock_v0100.py kit` 從正本抽,不手抄):
- `:root` token **20 個**(bg #f2f1ec · ink #33403f · line · row · title · muted · green / g-bg / g-ink · y-bg / y-ink · r-bg / r-ink · white · head 126px · center-head 43px · tabs-height 43px · sans / serif / mono),區塊 sha256 `54e5f62638d0dd98…`。
- 版面契約:左「輸入」· 中「系統摘要 / 驗證結果 / 管理矩陣」三分頁 · 右「Evidence / Inspector」;左右可收合;管理矩陣九分類(systems · io · commands · files · environment · policy · conflicts · requirements · tests);前四欄固定(燈號 · 編號 · SSOT 名稱 · 分類)、末欄錯誤詳細說明;每頁 50 列。
- 燈號律:只有 RED 2.8 秒慢 pulse(reduced-motion 時靜態);黃綠靜態;燈不能用按鈕解除。
- 斷點:1100px · 720px · reduced-motion · print。

## 二、自建 = 本倉真資料,不是審查包的資料

審查包自己的燈(OBS-0001 / 0186 / 0194 …)、36,837 列合併模型、Tony-NB UNAVAILABLE 等,是它那輪的 scope,**不進本工作台**。
`build` 只讀本倉自己的冊:

| 分類 | 來源冊 | 燈 |
|---|---|---|
| systems | `VIA_FiveSystemConstitution_latest.json`(入口尾版 · 編號 · 憲法燈) | 憲法矩陣的 lamp |
| io | 同上 `ssot[]`(各系統自己的冊) | 冊在 GREEN / 不在 RED |
| commands | `VIA_VCGC_FunctionInventory_SSOT_v*.json` 尾版(站表,依系統 token 分) | 一律 YELLOW:本次 build 未執行,未跑 ≠ 綠 |
| files | 入口尾版檔 | 在 GREEN |
| environment | `VIA_ToolVersion_Lock_v0100.json` 啟用家族 | 路徑在 GREEN |
| policy | `VIA_Policy_Laws_SSOT_v*.json`(提到本系統 + L120/L122/L123/L125) | ACTIVE GREEN |
| conflicts | 憲法矩陣 `conflicts_open`(VCGC 偵測方全列;他系統列提到自己的) | OPEN RED |
| requirements | `HANDOFF_latest.json` pending(提到本系統) | VERIFIED GREEN · BLOCKED RED · 其餘 YELLOW |
| tests | `VIA_FiveSystem_Progress_v0100.jsonl` + `docs/handoff/evidence/*.json` 收據 | run_lamp / rc |

共享證據(separate):憲法總燈 · L122 治理器 dry-run · 交接冊燈(≠ 驗收)· VRN-1 外倉只讀列。
payload 走正本 js 要求的信封(gzip + base64 + raw / gzip sha256;`bundle.version` 必須 = `v0106.4` 是 **U/I 契約版**,工作台版另記 `workbench_engine`)。

## 三、本輪實測(容器 2026-11-09)

- `--selftest` **14/14**(鎖站 4/4 · 抽 token · 契約 · 信封往返 · 燈號律 · 系統辨識(VRN-2 不吃 VRN-1)· CSP sha · 真資料 build 五頁 + hub · check 綠 · 篡改 token 紅 · 刪結構 id 紅 · VCGC 頁 policy / conflicts · hub)。
- `all`:五頁 rows VCGC 415 · VDF 307 · VRN-2 159 · VQG 19 · VAP 21;check 6/6 GREEN。
- Playwright(Chromium 1440×900):五頁 pageerror **0**、console error **0**;KPI 由 payload 算出(VCGC 415 / 9 / 16 / 135)· 分類頁籤 10 · 點列 Inspector 顯示編號(VIA-VCGC-MDL1625 …);hub 400px 不橫向捲。
- 輸出在 `VIA_Reports/workbench/`(不提交);桌機:`python docs/handoff/ai/VIA_WorkbenchLock_v0100.py all --open` 自動開 hub。

## 四、與 Atlas 鎖(VIA_VisualLock v0100 · 2026-11-07)的關係

兩個鎖並存、各管各的頁:Atlas `--vl-*` 管個股 / 對帳 / 矩陣頁(GovCoreChain · FiveSystemConstitution UI …);本鎖管「五系統工作台」頁。
兩者 token 值重疊(bg / ink / title / muted / green 相同來源),沒有衝突;要合併成一個正本是操作員裁定(W2)。

## 五、界線

不執行審查包任何 `.py` / `.ps1`(mcp_stdio_smoke · stage · build 都只讀);不發號、不改燈、不寫任何系統的冊;hub 與五頁都是離線單檔(CSP default-src 'none')。
