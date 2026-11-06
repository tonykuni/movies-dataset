# VRN-2 桌機交接 · 2026-11-01(給 Tony 與桌面端 Claude · 短版)

> 長版技術交接:`docs/handoff/ai/VRN2_Handover_v0168.md`(在分支 `claude/optimistic-goodall-yhalc5`)。本檔只寫桌機要做什麼。
> 原則照舊:只增不減 · 薄尾新版 · 前版不動 · 四系統對等(VRN-1 / VRN-2 / VDF / VCGC 互不代改)· AI 不代設同意閘、不代打 `--confirm`。

## 1. 現在在哪

| 項目 | 狀態 |
|---|---|
| 上一次桌機實跑 | 2026-11-01 09:19 · Handle-All v0114 整輪 · 5434 秒 · 套件 v0166 |
| 那一輪結果 | 年度數據 11505 → 11865 筆(欣銓 3264 · Daiwa-6278 年度表補回)· ⑪ 獨立驗證錯值 0 · 缺項只剩華南 6143 |
| 收尾頁當時 | OPEN「VRN-2 1 項」= 步驟列截字誤判(「失敗 0」被截掉)→ RoundAll v0123 修 |
| 用 v0123 重算(沙盒 · 只讀貼回包) | **REVIEW** · VRN-2 0 · 人工 2 · 資料源 3 |
| 結論 | VRN-2 側沒有待修。REVIEW 不是成功;要你看完原文、親手 `--confirm` 才往下走 |

## 2. 現役版本(現役線在分支 `claude/optimistic-goodall-yhalc5`)

| 元件 | 版本 | SHA-256(前 12) |
|---|---|---|
| 一行入口 Handle-All | v0115 | 開機檔 `a25ea4d00f1e` · 一行 `ded97b49bb12` |
| 一支 Python RoundAll | v0123(自測 89 項 · 不過 0) | `fc9f640cacd7` |
| 套件 VRN2_Closeout | v0166(啟動器 v0166 · runtime v0158 · 管理器 v0258) | `68d6d03d3fd1` |
| 擷取 / 驗證 / 共識 | ENG397 v0129 · IndependentVerifier v0114 · ConsensusJoin v0105 · 共識引擎 v0122 | — |
| 國內財報 | 不用 MOPS,一律 TWSE / TPEX(操作員 2026-10-31 令) | — |

雲端 2026-11-01 已核對:分支上的開機檔雜湊 = `a25ea4d00f1e` 相符。

## 3. 桌機要做的(依序)

1. **開新的 PowerShell 7 視窗**。要經 VIA 網路工具抓共識,先貼(你決定 · AI 不代設):
   ```powershell
   $env:VIA_SCRAPE_CONSENT = 'YES'
   ```
2. **貼這一行(443 字元)**:
   ```powershell
   $r="$HOME\OneDrive\Documents\movies-dataset";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;$c=(git -C $r show "FETCH_HEAD:VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0167/VRN2_HandleAll_v0115_boot.txt")-join"`n";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]][char[]]$c))).Hash-eq'a25ea4d00f1ec86fa7f4ce7da1ad04eb5ca2c1b3ffe028505591343e63c64e58'){iex $c}else{'[RED] boot SHA-256 mismatch - not run'}
   ```
   第一行應是 `[GREEN] boot: Handle-All v0115 SHA-256 OK`。收據已是 v0166 → 自動選 **repair**(幾分鐘,不整輪)。cmd 視窗版在 `vrn2_release_v0167/VRN2_HandleAll_v0115.md`。
3. **看自動跳出的收尾頁**(`VIA_Reports\vrn2\VRN2_CloseoutUI_latest.html`)。預期 REVIEW · VRN-2 0 · 人工 2 · 資料源 3。
   - 若是 **OPEN**(VRN-2 > 0)→ 把 `Downloads\VRN2_PasteBack_<時間>.zip` 上傳給 AI。
4. **人工 2 項**(看原文後才記):
   - MQ-1560 影像頁四點(代碼 `H-fd2ea35f`):對原圖看四點與摘錄是否一致。
   - 華南投顧-6143 缺項:原文沒上傳過 → 上傳原 PDF 給 AI,或確認原文本來就沒有年度表。
   ```bat
   python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0123.py" --confirm list
   python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0123.py" --confirm H-xxxxxxxx --note "原圖四點與摘錄一致"
   ```
   撤銷:`--confirm revoke H-xxxxxxxx`。代碼照收尾頁那一項。
5. **資料源 3 項**:外部來源本來沒有的(收尾頁附證據),不用動,VRN-2 不繞道。

## 4. 需要你決定的事

1. **要不要把現役線併進 main。** v0159 ~ v0167 共 14 筆提交只在分支 `claude/optimistic-goodall-yhalc5`,main 停在 v0158。
   一行入口先讀那條分支、讀不到才退 main;分支若被刪,入口會退到 main 而找不到 v0167 → 紅。雲端已試:那條分支可乾淨併入 main(無衝突)。
2. **VRN-2 自己的 4 本冊只在桌機**:VRN2_BasicInfo_Headers_v0100 · VRN2_Regex_v0100 · VRN2_RestoreRiskCatalog_v0100 · VRN2_Publish_Config_v0100。
   倉上的 v0256 / v0258 缺冊會亮黃、不假裝過。要入倉就在桌機跑 ChainShip `ship`(只增 · 同名不同內容出 v+1);Publish_Config 若含憑證路徑先拿掉再上船。

## 5. 還沒做(不在這一輪)

- 3014TT 四點品質(第 2 點從句中開始 · 第 1 / 3 點重複)、MQ-1560 OCR 字詞錯 → 摘要器 / OCR 要另出新版,需要整輪。
- Google Sheet(要你的憑證)· `--autostart`(本授權不含)· 管理器壓平(只提計畫,等你確認)。

## 6. 貼回格式(每次只貼這些 · ≤ 80 行)

```
## 回報 · <日期時間>
[計] 跑了什麼(repair / full)· RoundAll 結束碼 · 秒數
===== 收尾 · <狀態> · VRN-2 n · VCGC n · 人工 n · 資料源 n(主控台黃字那幾行原文)
[計] --confirm 記了哪幾項(代碼)
NEXT: <收尾頁印的下一步>
```

## 7. 停下來的條件

收尾頁 OPEN 且 VRN-2 > 0 · 開機行印 `[RED]` · 需要刪改既有版本檔 · 需要改 VRN-1 / VDF / VCGC / v1652 合規層 · 同家族連兩版仍不轉綠 → 停,貼回包給 AI。

## 8. 更新 · 2026-11-01 晚(現役線已併 main · VRN-2 版本鎖)

- **現役線已併進 main**:PR #583(合併提交 `0d5383a7`)· v0159 ~ v0167 共 14 筆 · 89 檔全新增 · Windows CI 三項綠。第 4 節第 1 條已完成:一行入口讀分支或 main 都拿得到 v0167。
- **VRN-2 版本鎖**:`docs/handoff/ai/VRN2_FreezeLock_v0100.json`。鎖的是現役版本檔與 SHA-256,不是驗收:`closeout_state = REVIEW`(VRN-2 0 · 人工 2 · 資料源 3)。
  鎖住後 VRN-2 不再出新版;要解鎖只能由操作員下令,出 `VRN2_FreezeLock_v0101.json`(只增,v0100 不動)。其他系統可以照這把鎖進行自己的 CLOSE OUT。

### 桌機同步(讓桌機與 GitHub 一致 · 在 PowerShell 7 依序貼)

1. 拉 main:
   ```powershell
   git -C "$HOME\OneDrive\Documents\movies-dataset" pull --ff-only origin main
   ```
   `--ff-only` 不成功 = 桌機有沒推的提交 → 先貼回給 AI,不要強推。
2. 核對鎖(全部 OK 才算一致;只讀):
   ```powershell
   python -c "import json,hashlib,pathlib,sys;r=pathlib.Path(r'$HOME\OneDrive\Documents\movies-dataset');L=json.load(open(r/'VeritasIntelligenceAnalytics/docs/handoff/ai/VRN2_FreezeLock_v0100.json',encoding='utf-8'));bad=[f for f,h in L['files'].items() if not (r/f).is_file() or hashlib.sha256((r/f).read_bytes().replace(b'\r\n',b'\n')).hexdigest()!=h];print('[GREEN] VRN-2 鎖一致' if not bad else '[RED] 不一致: '+', '.join(bad))"
   ```
3. 桌機那 4 本 VRN-2 自己的冊上船:貼 `VRN2_ChainShip_v0101.md` §3 的一鍵(`ship` 先找本機的冊 → 只增上船)。`VRN2_Publish_Config_v0100.json` 若有憑證路徑,先拿掉再跑。
4. 跑第 3 節的一行入口(repair)→ 收尾頁 REVIEW → 看原文 → `--confirm`。兩項人工都確認、華南 6143 有交代之後,收尾頁才會到 PASS / DATA_GAP。

## 9. 更新 · 2026-11-01 夜(U/I:右面板第一頁「00 系統現況」· v0168)

操作員令:以目前 HTML U/I 為基礎,把 `taiwan_stock_data_matrix.html` 的版面與字體階層加進視覺鎖,右面板第一頁放系統現況 SUMMARY(含 DataFrame 表頭),原有功能不改。

- **新版**:Workbench v0103 · 啟動器 v0168 · 套件 v0168 · RoundAll v0124 · Handle-All v0116(發行夾 `vrn2_release_v0168`)。輸出冊不變。
- **00 系統現況**(開頁預設):輸出冊 × 來源 × 端點 × 真實欄名 × 燈 · 本輪步驟 · VDF / VCGC / VRN-1 只讀互看 · 點一列看全部欄 · 圖例篩選。01 ~ 04 不動。
- **版本鎖**:`VRN2_FreezeLock_v0101.json`(v0100 不動)。第 8 節第 2 步的核對一行,把檔名 `v0100` 換成 `v0101` 再貼。
- **取件分支**:這一輪放在 `claude/vrn2-closeout-authorization-y4ixl7`(退路 main)。

### 桌機要做的

1. 開新的 PowerShell 7 視窗。要經 VIA 網路工具抓共識,先貼 `$env:VIA_SCRAPE_CONSENT = 'YES'`(你決定)。
2. 貼這一行(第 3 節那行換成這行):
   ```powershell
   $r="$HOME\OneDrive\Documents\movies-dataset";git -C $r fetch -q origin claude/vrn2-closeout-authorization-y4ixl7;$c=(git -C $r show "FETCH_HEAD:VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0168/VRN2_HandleAll_v0116_boot.txt")-join"`n";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]][char[]]$c))).Hash-eq'd50fd1ac12b33ac6527b391eb3c85f1fe7f114ea3d6dfc2036fc357c84d4df7d'){iex $c}else{'[RED] boot SHA-256 mismatch - not run'}
   ```
   第一行應是 `[GREEN] boot: Handle-All v0116 SHA-256 OK`。auto 選 repair(幾分鐘),⑤ 會把 Workbench v0103 補放進 runtime 夾並重渲染。
3. 自動跳出的 Workbench 開頁就是「00 系統現況」。收尾仍應是 REVIEW(VRN-2 0 · 人工 2 · 資料源 3)。人工兩項照第 3 節第 4 步。

雲端沒有 PowerShell:這一行沒在 pwsh 實跑過,雜湊在 Python 端核過。若印 `[RED]`,貼回給 AI。

## 10. 更新 · 2026-11-01 深夜(VeritasReportNova · 印章 · v0169 · 取代第 9 節那一行)

- **第 9 節那行在桌機印 `[RED] boot SHA-256 mismatch`**:是 AI 在對話裡手打的雜湊打錯,不是檔案壞了。這一節的一行直接從檔案複製。
- **新版**:Workbench v0104 · 啟動器 v0169 · 套件 v0169 · RoundAll v0125 · Handle-All v0117(發行夾 `vrn2_release_v0169`)· 版本鎖 `VRN2_FreezeLock_v0102.json`。輸出冊不變。
- **畫面**:名稱 VeritasReportNova / VRN(檔名與指令不改)· 00 頁只讀互看列 VDF · VCGC · 印章透明去背無框無特效 · 主印框上下緣對齊頁首文字 · 小印垂右下。
- **印章來源**:桌機沒有 `VRN2_Logo.*` 時用內建的這顆;桌機有自己的 logo 檔照舊用桌機的。

### 桌機要做的

1. 新的 PowerShell 7 視窗;要經 VIA 網路工具抓共識,先貼 `$env:VIA_SCRAPE_CONSENT = 'YES'`(你決定)。
2. 貼這一行:
   ```powershell
   $r="$HOME\OneDrive\Documents\movies-dataset";git -C $r fetch -q origin claude/vrn2-closeout-authorization-y4ixl7;$c=(git -C $r show "FETCH_HEAD:VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0169/VRN2_HandleAll_v0117_boot.txt")-join"`n";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]][char[]]$c))).Hash-eq'0b9eb106465d3dcc3098131f176834f74089630d3c47c1ea24df41d9b975f259'){iex $c}else{'[RED] boot SHA-256 mismatch - not run'}
   ```
   第一行應是 `[GREEN] boot: Handle-All v0117 SHA-256 OK` → auto 選 repair(幾分鐘)→ 自動跳出的 Workbench 標題是 VeritasReportNova。
3. 收尾仍應是 REVIEW(VRN 0 · 人工 2 · 資料源 3);人工兩項照第 3 節第 4 步。印 `[RED]` → 整段貼回。

## 11. VDF / VCGC 同一 U/I 模板(2026-11-01 深夜)

VRN 之後照令做 VDF / VCGC:共用模板冊 `VIA_UI_Template_SSOT_v0104.json`(= VeritasReportNova Workbench 範本)+ 共用印章 / 字型;
VCGC `CGC_MDL274_HealthMatrix_v0116`(操作台印章頁首 · VRN 分頁改指 VeritasReportNova)· VDF `VDF_ENG236_FetchMatrixUI_v0101`(DataFrame 表頭欄 · 印章頁首)+ `VDF_SystemManager_v0167`。
細節、測試與桌機步驟:`docs/handoff/ai/VIA_UI_TemplateLock_Closeout_20261101.md`。桌機:拉分支後跑 `via-vcgc` 與 `via-vdf` 看頁首;VDF 表頭欄第一次會讀庫。

## 12. 更新 · 2026-11-02(Release Closure 令 · VRN 兩個缺陷修正 · 取代第 10 節那一行)

桌機 2026-11-02 04:24 用第 10 節那一行跑完 v0169(RoundAll v0125 · repair 45 秒)→ Workbench v0104 畫面已是 VeritasReportNova · 收尾 **REVIEW**(VRN 0 · VCGC 0 · 人工 2 · 資料源 3)。同一段主控台有兩個 VRN 自己的缺陷:

| # | 現象(桌機原文) | 根因 | 修正(新版號 · 前版一字不改) |
|---|---|---|---|
| 1 | `Write-Host: 無法繫結參數 'ForegroundColor' … "Yellow · 看過原文沒問題 → …"`(兩次) | Handle-All v0117 收尾燈顏色表的 REVIEW 值寫成「顏色 + 一句提示」 | `VRN2_HandleAll_v0118.md`:REVIEW 顏色只寫 `Yellow`,提示句移到「下一步」那一行 |
| 2 | `UserWarning: Duplicate name: 'vrn2/VRN2_Closeout_v0166.json'`(兩次) | 沿用前版收據時 extra 跟貼回清單同名 → 同一檔寫進 zip 兩次 | `VRN2_RoundAll_v0126.py`:貼回清單先去重(先後照舊)· 自測 90 / 90(新增第 90 項) |

套件、啟動器、Workbench、輸出冊都不變(仍是 `VRN2_Closeout_v0169`)。版本鎖換 `VRN2_FreezeLock_v0103.json`(v0102 不動)。

### 桌機要做的(PowerShell 7 · 依序貼)

1. **先讓桌機跟 GitHub 一致**(桌機落後 719 個提交、另有 2 個沒推的提交 → `--ff-only` 一直不成功,所以 VDF 還在跑舊的 v0162)。這一行用合併(不 rebase、不強推、不丟桌機的提交);不成功會自動還原:
   ```powershell
   $r="$HOME\OneDrive\Documents\movies-dataset";git -C $r pull --no-rebase --no-edit origin claude/vrn2-closeout-authorization-y4ixl7;if($LASTEXITCODE){git -C $r merge --abort 2>$null;'[RED] pull 沒成功 - 已還原 · 把上面整段貼回給 AI'}else{'[GREEN] 桌機已跟 GitHub 同步'}
   ```
2. VRN 一行(從檔案複製 · 開機檔 `VRN2_HandleAll_v0118_boot.txt`):
   ```powershell
   $r="$HOME\OneDrive\Documents\movies-dataset";git -C $r fetch -q origin claude/vrn2-closeout-authorization-y4ixl7;$c=(git -C $r show "FETCH_HEAD:VeritasIntelligenceAnalytics/docs/handoff/ai/vrn2_release_v0169/VRN2_HandleAll_v0118_boot.txt")-join"`n";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]][char[]]$c))).Hash-eq'dfbfd9fd0109cbfc07d1a85fcb59fed54226c35d1610412391c3f9d4e9082a03'){iex $c}else{'[RED] boot SHA-256 mismatch - not run'}
   ```
   第一行應是 `[GREEN] boot: Handle-All v0118 SHA-256 OK` → repair 幾分鐘 → 收尾仍 REVIEW,但不再有 ForegroundColor 紅字與 Duplicate name 警告。
3. VDF:`via-vdf`(ui)。

### VDF ui RED(桌機 04:35 · `VDF_SystemManager_v0162.py ui · rc 1`)

- 桌機的 VDF 尾版是 v0162;GitHub 上 main 已到 v0166、本分支 v0167(v0163 起修過 Windows 一般帳號的前版鏈問題)。桌機落後是因為第 1 步一直沒成功。
- 雲端容器用 v0162 那一代的樹(`efeea85a4^`)、用現在的樹(v0167)、裝上 duckdb、換工作目錄各跑一次 `ui` → **都是 rc 0 GREEN**,在容器裡重現不出來。
- 紅字只有前版鏈轉手那兩行(v0128 第 104 行 → v0127 第 108 行 `__getattr__`),最後一行錯誤訊息被截掉了。
- **第 1 步做完再跑 `via-vdf`**;還是紅 → 把 `VIA_Reports\review\ps_<時間>\B.python.log` 整個檔上傳給 AI(最後一行才是真正的錯誤名)。VRN 不改 VDF 的檔(四系統互不干涉)。

## 13. 一支收尾全部 · VIA_SettleAll_v0101(2026-11-02 · 取代第 12 節的三步)

操作員 2026-11-02「全景式分析檢視 · 識別問題 · AST 定位 · GENERATE A CODE TO SETTLE DOWN AND HANDLE ALL ABOVE」→ `docs/handoff/ai/VIA_SettleAll_v0101.py`(v0101 修 PR #585 Codex 三項:舊收據 / 交接閘紅 / 黃燈不再被報成綠 · Python · PowerShell 只負責取檔與核雜湊)。

| 步 | 做什麼 | 寫什麼 |
|---|---|---|
| ① 環境 | Python · duckdb · pyarrow · pwsh 有沒有 | — |
| ② AST 全景 | 8 個家族(VRN / VDF / VCGC 管理器 · ENG236 · UIEngine · HealthMatrix · TestAuto · RoundAll)全部版本 `ast.parse` + `compile`(只在記憶體 · 不執行)· 錯誤與警告記檔:行 | — |
| ③ 同步 | 比 GitHub 少幾個 / 多幾個沒推 → **合併**(不 rebase · 不強推 · 桌機的提交保留)· 有沒提交的改動就不合併 · 失敗自動 `merge --abort` | git 合併提交 |
| ④ VDF ui | 跑 VDF 尾版 `ui` 拿全文;紅 → traceback 逐框 **AST 定位**(在哪個 def · 原文那一行)· AttributeError 掃同家族每一版誰定義 / 誰先讀(前版鏈轉手落空)· 遞迴偵測 | VDF 自己的頁 |
| ⑤ VRN | 跑 RoundAll 尾版 repair(= Handle-All 那一輪)· 讀收尾頁燈與負責方 | VRN 自己的收據 |
| ⑥ VCGC | `handoff check`(交接閘紅分類計數)+ `test --quick`(串測總行 · 紅站) | VCGC 自己的紀錄冊 |
| ⑦ 報告 | `VIA_Reports\settle\SETTLE_latest.json / .md` + `Downloads\VIA_Settle_<時間>.zip` | 只寫這兩處 |

各系統只經自己的入口跑(四系統對等 · 不改他系統的檔)。容器實測:自測 13 / 13(含假遠端真 git 合併 · 有改動拒合併)· 實跑 AST 286 檔錯 0 · VDF ui 6 GREEN · VCGC 紅站 0(但交接閘既有紅 → ⑥ 照實 RED)。

### 桌機要做的(PowerShell 7 · 一行 · 從檔案複製)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0101";git -C $r fetch -q origin claude/vrn2-closeout-authorization-y4ixl7;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0101.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0101.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'BE95A346FE46DEDBA139C7C81C575D60C2FC09D3D2D3133CD8203B15E45CBB06'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

跑完看最後一行 `NEXT:`;不是 GREEN → 把 `Downloads\VIA_Settle_<時間>.zip` 上傳給 AI(VDF 紅字的 AST 定位在裡面)。VRN 收尾 REVIEW 的兩個人工項仍要你看原文後 `--confirm`。

## 14. 一支收尾全部 · VIA_SettleAll_v0102(2026-11-04 · 取代第 13 節 · 多 Graphify / VQG / Agent OS 三段 · VRN 預設只讀狀態)

操作員 2026-11-04 桌機四條貼回(Graphify VCGC 記憶體跳過 · VQG NO_DAILY_PRICES · Agent OS selftest rc 2 · VRN-2 confirm 已記)→ 「integrate into one code to handle above」
→ `docs/handoff/ai/VIA_SettleAll_v0102.py`;根因、段表與預期在 `docs/handoff/ai/VIA_SettleAll_v0102.md`。一行(從檔案複製):

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0102";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0102.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0102.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'AD2036AD24B165BD6D9BA12E23BE78D679B8B5A04BDBB7AD500498095ABE7373'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

## 15. VIA_SettleAll_v0103(2026-11-04 · 取代第 14 節:同步會自己 stash 收據類改動 · 分支尾版對照 · VCGC 輸出入報告 · Graphify 實測用量)

桌機 v0102 貼回:VQG 第一次算出來(黃 · 351 日線檔 · 0050.TW)· Agent OS 黃(symlink 權限)· Graphify VCGC 吃 ≥ 3.2 GB 被看門狗殺 · VDF ui / VCGC 紅 = 桌機工作樹停在 main 舊版(38 個已追蹤改動讓 ③ 不合併)。細節 `docs/handoff/ai/VIA_SettleAll_v0103.md`。一行(從檔案複製):

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0103";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0103.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0103.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'F673698309AB6FDE77A6DA5A6EEFDA7A2EBF3CA0B4C62F690BDECB36BE0871B2'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

## 16. VIA_SettleAll_v0104(2026-11-05 · 取代第 15 節:改動分類 bridge / state / eol 自動合併 · ④⑤⑧⑨ 併行 · VCGC 事件冊 · Graphify 1 worker · ⓫ L103 政策全景只讀)

桌機 v0103 貼回:37 個「其他」改動 = VRN 舊版注入橋塊 + VCGC 狀態冊等 → v0104 逐檔算類別,只有真的改了程式才停。細節 `docs/handoff/ai/VIA_SettleAll_v0104.md`。一行(從檔案複製):

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0104";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0104.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0104.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'F6F6EF1052B435E8BB6D3E8F2CCE30B10A1A2B12CBB11D1C2FAC38BF9FF0F086'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

## 17. VIA_SettleAll_v0105(2026-11-05 · other 類改動逐檔 +/− 與差異取樣 · VCGC 壞 JSON 定位 · 政策全景不算 venv)

兩日全景收尾見 `docs/handoff/ai/VIA_Closeout_Panorama_20261105.md`。一行(從檔案複製):

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0105";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0105.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0105.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'3C4EE4C554B48E7E7851A93404382D4757946DA32AB322F343C5410C62815738'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

## 18. VIA_SettleAll_v0106(2026-11-06 · 快:圖沒變沿用 · 記憶體不夠不跑 · 政策全景快取 · 舊樹不白跑 · 每段秒數)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0106";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0106.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0106.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'87062098DB3568DE512FE96F765AE1C24B1A6789C2BFE5638447D997032EAC78'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

## 19. VIA_SettleAll_v0107(2026-11-06 · 改動差異比 HEAD(已 git add 也抓得到)· 壞 JSON 掃描不受 ⑥ 略過影響)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0107";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0107.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0107.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'F40722F5B68F40A95A5DC020D4045ED1EFB2952D887AAF480E2F911CE298AACA'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

## 20. VIA_SettleAll_v0108(2026-11-06 · ⑫ 系統矩陣:三種燈 · 版本 · 狀態 · 只增帳記綠 · HTML 自動開 · Agent OS / Graphify / MCP 掛 VCGC)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0108";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0108.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0108.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'A628681884170D4188CE3487BBE13ED2149CBF6B7681839F919B916BCEEE0741'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

## 21. VIA_SettleAll_v0109(2026-11-06 · git rm 的舊版從 HEAD 還原 · 壞 JSON 備份還原 · VCGC 編號欄 · ⑬ VDF 全引擎自測掃描)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0109";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0109.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0109.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'C8C529A6DE27F758C3FCAD1159AFE697A8D3E634C765DD2E0C0A14AEE331FFD1'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```


## 22. VIA_SettleAll_v0110(2026-11-06 · ⑭ 模組矩陣:SYSTEM 燈 / FUNCTION / DESCRIPTION / MDL-ENG NAME + VCGC 編號 / CLS / FNC / LIBS / ERROR & AST / STATUS · 只讀 AST · STATUS 只從 ⑬ 自測 / VCGC 功能帳 / 入口步燈取)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0110";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0110.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0110.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'7CAAD8650A332FD7149CBFE05D30CF196355232E27F509A894967BEF149B674E'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

容器實跑:508 模組尾版 · 🟢 361 🟡 9 🔴 10 ⚪ 128 · AST 錯 0 · 5 秒;文件 `VIA_SettleAll_v0110.md`。操作員上傳的 VIA_SystemIntegrationEngine v1.0 入倉在 `sie_v1_0_intake/`(只留證 · 不接線)。架構基線 B1–B5 對照:`VIA_Blueprint_B1B5_Mapping_20261106.md`。

## 23. VIA_SettleAll_v0111(2026-11-06 · ⑭ VCGC 編號改查 MDL + ENG 兩本冊 → 508 列未登號 0 · 取代 §22 那行)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0111";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0111.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0111.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'D04B90BD5A302A9D28628EBEF21BD16C5B7A48EAE8A24A6DC73114355F95CD91'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

## 24. VIA_SettleAll_v0112(2026-11-06 · 桌機 22:19 貼回:26 舊版 + 2 壞 JSON 已還原 · 剩 SM v0152 / v0153 被改 → 新類 frozen 備份後還原 HEAD · 未追蹤檔摘要 · 取代 §23 那行)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0112";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0112.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0112.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'322F1D0B1B23F4387F1921A8A553340195C49AF97E75FADD14C38D388B1DD587'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

## 25. VIA_SettleAll_v0113(2026-11-06 · ⑮ VAP v0300 實測燈 · ⑫ VCGC 站表矩陣 319 站(類型 / 測試型 / 版本 / 編號 / 功能帳 / 耗時 / 時間)· 取代 §24 那行)

```powershell
$r="$HOME\OneDrive\Documents\movies-dataset";$t="$HOME\Downloads\VIA_Settle_v0113";git -C $r fetch -q origin claude/optimistic-goodall-yhalc5;git -C $r archive --format=zip -o "$t.zip" FETCH_HEAD VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_SettleAll_v0113.py;Expand-Archive "$t.zip" $t -Force;$f="$t\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_SettleAll_v0113.py";if((Get-FileHash -InputStream ([IO.MemoryStream]::new([byte[]]([IO.File]::ReadAllBytes($f) -ne 13)))).Hash-eq'B5B75B7B9DBFDE3A10CB4A70B193B337CD9C08174FE0A460C88A335A0F9852B0'){python $f --root $r}else{'[RED] SettleAll SHA-256 mismatch - not run'}
```

## 26. 雙橋 100%(2026-11-06 · VCGC 橋掃器 --apply:ALL/accel 1800/1800 · VDF/net 146/146 · PS 1009/1009;注 11 支 · 豁免名冊 v0115 +4;一行釘住件還原 bytes 不注)

詳 `VIA_BridgeSweep_20261106.md`;審計矩陣 `VIA_Closeout_Audit_Matrix_20261106.md / .html`。桌機一行仍用 §25(v0113);桌機的 ③ 會把這 11 支當「bridge」類自動合併。
