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
