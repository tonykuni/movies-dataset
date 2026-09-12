# VIA 交接報告 · 批394(PowerShell AST 多輪並行安全修正引擎 → 一鍵全跑)

- 日期:2026-09-13
- 倉庫:`tonykuni/movies-dataset` · 分支 `main` 與 `claude/via-system-followup-tz7k9t`(每 commit 雙推)
- HEAD:見 §6 commit 清單首筆之後(本報告由收尾 commit 一併收束;以 `git log` 為準)· 工作樹乾淨 · 台帳 958 筆(append-only)
- 窗次:批394 與其續章(§6 列 9 筆;另有報告入庫與收尾自檢各一筆)

---

## 1 本窗起點與終點

**起點**:操作員令「啟動 PowerShell 指令語法多輪並行安全修正引擎,全套語法診斷工具 + AST 雙模錨點
+ 錯誤分流 + 並行安全修正 + 沙盒啟動驗證,直到系統啟動測試完全無誤。test debug optimize test debug
till they work.」

**終點**:該引擎完成(MDL146 v0104,十五檢全綠),並在過程中把散落的操作員待辦整合成單一啟動器
`via-oneshot`(九段);操作員工作站已實跑一次並解開卡住的倉庫。

---

## 2 新建與升版件(皆尾版 glob 解析,零寫死版號)

| 件 | 尾版 | 作用 |
|---|---|---|
| `CGC_MDL146_PsAstRepair` | v0104(十五檢) | PS AST 多輪並行安全修正引擎(T1 AST / T2 PSSA / T3 CommandAst;F1a/F1b 自動修;R1/R2/R4 只列) |
| `CGC_MDL143_MergeMedic` | v0104(十四檢) | 拉齊醫生(連字號版號、stash pop 不毀台帳、MERGE_HEAD 已解態) |
| `CGC_MDL144_CopyDoctor` | v0102(十一檢) | 副本醫生(+bootstrap 死結偵測與可貼指令產出) |
| `CGC_MDL064_SelftestGrid` | v0274 | 全矩陣 207 站(+寫庫站分組=鎖撞假紅歸零;站名校正至實檢數) |
| `CGC_MDL087_TestPyramid` | v0101 | 三級金字塔(I3 寫死版號修 + ②b 自我看守反測) |
| `Invoke-VIA-OneShot` | v0102 | **一個指令跑完全部**(九段;四態;紅站明細;資料數字健檢;pathspec 改 glob) |
| `Invoke-VIA-Unstick` | v0100 | 倉庫解卡啟動器(不依賴副本醫生版本;迴圈至與 origin 齊平) |
| `Register-VIA-Commands` | v0179 | 短令冊(+via-oneshot/一鍵、via-unstick/解卡、via-psrepair-ast/語法修) |
| `VAP_ENG007_RawWideRefresh` | v0101 | 寬表刷新器(FRED 鑰缺 → 誠實 SKIP) |
| `GRP_ENG040_GroupingRotationRunner` | v0102 | 族群輪動(核心第三方需求缺席 → SKIP 並印缺件名) |
| `VRN_ENG068_DailyBrief` | v0103 | 每日觀察摘要(市場寬度判準改相對守恆;存證/快照缺 → SKIP) |
| `VRN_ENG069_ConsensusDB` | v0103 | 驗證共識庫(公式實證解除單源綁死) |
| `InvokeVIA.ps1` | 無版號(就地修) | param 區塊上移(見 §3 第 1 枚) |

---

## 3 本窗抓到的真缺陷(七枚;皆有實測證據)

1. **`InvokeVIA.ps1` 的 `param` 區塊不在合法位置** — 前面已有加速器橋 `try{}`、`Set-StrictMode`
   等可執行語句,PowerShell 遂把 `param(...)` 當指令呼叫(實測 `InvalidOperation: called as if it
   were a method`),`-Run`/`-SafeProbe`/`-Plan` 三開關**永遠無法綁定**,這支 Guarded Root Entry
   的真跑路徑完全不可達。檔案解析仍綠,故 T1 解析閘、MDL145、PSScriptAnalyzer 全都不報,
   唯 T3 CommandAst 抓得到。已修並固化為回歸測。

2. **`CGC_MDL134_ParallelLanes` 尾版缺雙橋** — v0100 有 4 個橋標記,v0101 一個都沒有(新版建立時
   沒帶上 ACCEL/NET 橋)。全樹 127 件外呼中唯一網路缺就是它。以既有 MDL124 BridgeSweeper 注入後
   覆蓋 100%,自動總跑器六檢轉全綠。

3. **金字塔 I3 寫死版號** — `need = {"VDF_ENG054_TWDailyBackfill_v0100.py"}` 以完整檔名硬比,而
   參數映射只收同族尾版(ENG054 已到 v0104),此道自 ENG054 升版那刻起永遠紅。改族前綴判定,
   並加 ②b 反測掃本檔是否還有完整版號硬比字面(自我看守)。

4. **`stash pop` 衝突會毀台帳** — pop 衝突時 git 已把衝突標記寫入工作樹,台帳若在其中就當場變成
   非法 JSON(實錄:驗收讀取直接 JSONDecodeError)。改為 pop 起衝突後按律裁決:台帳聯集、
   同名雙物/再生物取合併後版;全解則 stash drop 不留殘渣。

5. **醫生漏認「MERGE_HEAD 在但 index 已乾淨」態** — 會把已解的成果連同髒樹 stash 走、再 merge
   一遍=白做一輪且徒增 pop 衝突風險。改為直接完成合併提交。

6. **市場寬度句判準與資料宇宙不符** — 門檻 `n_ma > 1000` 按「台股全市場 1800 檔」假設寫死,
   但本庫 `prices_canonical` 全庫最大單日僅 552 檔,該檢自設立起不可能綠。改用更嚴的相對守恆
   (該完整日因子覆蓋須 100% 且該日規模須等於庫內最大單日)。

7. **驗證共識庫判準綁死單一源** — 只查 `EXTERNAL_ANALYST` 的 2330,該源在雲端不存在故恆「缺」;
   但 `CNYES_FACTSET` 的 2330 三欄俱全(median 3175 / close 2410 / upside 0.317427),公式本可實證。

---

## 4 我自己犯的錯(十枚;誠實記錄,供接棒者避坑)

1. **F1 修法首猜錯** — 初版以為「把行尾註解搬走」就能解續行斷裂,pwsh 真測仍紅。真因是
   PowerShell 換行續接的唯一條件是「上一行以運算子結尾」。正解=運算子上提 + 註解搬續行末。

2. **F1 規則太窄** — 只認「行尾註解」那一種成因,所以我後來寫出無註解的跨行 `Write-Host` 時
   `detect_f1` 回零命中=漏抓。已擴充 F1b(附安全閘:只在該檔真有 ParseError 時啟用、
   只掃錯誤行 ±4 行、健康檔一律不碰)。

3. **T3 宣稱大於實作** — v0100 docstring 宣稱掃未知動詞,實作只有 regex 陷阱樣式。已真實作。

4. **T3 首跑假紅率 82%** — 11 枚裡只有 1 枚是真缺陷。已加五級分級
   (PLATFORM / CROSS / GUARDED / SYNTAX / ARCHIVE 皆非死路,只有尾版檔 TRUE 級才算)。

5. **R4 立規當輪自己誤判** — 把合法的 `@(if ($args) {...})` 也命中。pwsh 實測分辨:
   `@( )`/`$( )` 子運算式內可含語句故合法,裸 `( )` 當參數運算式才炸。

6. **Report-Only 規則名存實亡** — R1/R2/R4 原本只在「有 ParseError 的檔」上跑,而這三型正是
   解析綠卻執行紅——健康檔才是它們的主場。改為全樹掃描後立刻找出 12 枚真的 R2。

7. **把雲端實測結論誤套到操作員環境** — 我在已含新醫生的雲端倉庫實測,得出「不需手動
   `checkout --theirs`」,但操作員副本的醫生還是 v0101。**實測為真,結論為假**。
   教訓:實測環境與操作員環境的版本差必須先核對。治本=CopyDoctor v0102 自己偵測死結並印指令。

8. **OneShot 三枚(全靠真跑現形)** — `Start-Job` 是新工作階段故段內短令全 not recognized;
   輸出緩衝到結束才吐(長跑段畫面全白);判定式抓不到 python 缺檔錯誤造成 0.7s 假綠。

9. **OneShot 判定過嚴造成假紅** — 把引擎的誠實中間態 YELLOW/待裁一律算 FAIL。已加 WARN 態。

10. **git pathspec 也寫死了版號** — 我在 OneShot v0101 的 S1 與交接報告的指令裡都寫死
    `Invoke-VIA-Unstick-v0100.ps1` / `Invoke-VIA-OneShot-v0100.ps1`。「glob 尾版動態解析嚴禁
    寫死版號」律同樣適用於 git pathspec——啟動器一升版,那行就取到舊版。實測 `git checkout`
    支援 glob pathspec,已改取整族再由 `Sort-Object | Select -Last 1` 挑尾版(OneShot v0102)。

> 共通教訓:**AST 解析綠 ≠ 能跑**。`param` 位置錯、`if` 當參數運算式、型別假設錯(`Object[]`
> 沒有 `Trim()`)三者都解析全綠而執行必炸。靜態檢與真跑必須並用。

---

## 5 實測現況(誠實三態;勿以單側數字代表全系統)

### 雲端容器(程式面)
- 全矩陣 207 站:**OK 205 · FAIL 0 · SKIP 2 · 286s**
- PS 全樹:尾版 ParseError 0 · 解析綠 164 · T3 死路嫌疑 0 · Report-Only R2 十二枚(真)
- 封存版紅 4 枚:全為已被 v0103 取代的 `Invoke-VIA-PSRepair-v0102.ps1` → 封存律凍結不改
- 資料庫在 `output_hub/`(gitignored),容器回收即失,故雲端不代跑資料擷取

### 操作員工作站(OneShot 首跑實錄)
- 總計:**OK 10 · FAIL 5 · SKIP 1 · 3296s**
- 已成:倉庫解卡(醫生終態 OK)、冊升 v0179、加速器導入、價格 +680、對齊 GREEN、
  FRED 真跑(鑰在位)、PS AST 與 PS 真測閘全綠、via-pin 生效
- 兩枚 FAIL 實為假紅(已於 v0101 改判 WARN):`via-rungate` 判定 YELLOW(家族境未建走 base 退路)、
  `via-envgov` rc=1(有待裁段)
- 三枚真紅:全矩陣 **22 紅**、產品閘紅閘、四專案 overall RED
- 兩個數字警訊:籌碼**落庫 0 列**、價格 checkpoint **failed 1430 / done 1988**

---

## 6 本窗 commit(新→舊)

```
3e4e5cca  OneShot v0101(四態+紅站明細+資料數字健檢)+ PS AST v0104 F1b
53eb7e90  一個指令跑完全部(OneShot v0100 九段)+ Register v0179 via-oneshot
d773f8ed  倉庫解卡啟動器(端到端代跑驗證)+ 醫生 v0104 兩枚真缺陷 + R4 新規
2c361a4d  副本醫生 v0102 bootstrap 死結偵測(我把雲端實測結論誤套到操作員環境的更正)
184bbb95  格子 v0273 鎖撞假紅歸零 + 拉齊醫生 v0103 第⑫檢
53b266b1  金字塔 I3 寫死版號之錯修正(MDL087 v0101)+ ②b 自我看守反測
16f1bc6c  全矩陣 5 紅逐枚查根因並處置(2 真修 · 1 判準解綁 · 4 誠實 SKIP)
1cdd67bd  MDL146 v0102(T3 真實作+五級分級+並行)+ InvokeVIA.ps1 param 真缺陷修 + 格子 v0272
c8e2de8c  PS AST 多輪並行安全修正引擎(MDL146 v0100)+ Register v0177 + 格子 v0271
```

---

## 7 接棒者下一步

### 工作站(操作員)
```powershell
via-oneshot -SkipAccel -SkipData                 # 約 45 分;總表後附 22 紅站明細
via-oneshot -SkipAccel -SkipData -SkipMatrix     # 約 5 分;只看診斷
```
1. 取得 22 紅站清單 → 逐站查根因(雲端同矩陣 0 紅,差異來自真資料與真環境)
2. 籌碼落庫 0 列 → 查 checkpoint 是否已全標 done / 端點節流;`via-chip` 重跑或重置該段
3. 家族境未建 → `via-envgov apply --approve` 建 via_core/via_*,rungate 才由 YELLOW 轉綠
4. 價格 failed 1430 → 多為端點節流或代碼已下市;重試權保留,可重跑該段

### 副本若完全拿不到新檔(bootstrap 死結)
倉庫卡未合併時新檔進不來,但 git 可跨分支取單檔(pathspec 支援 glob=零寫死版號):
```powershell
$r="C:\Users\tonyk\OneDrive\Documents\movies-dataset"
git -C $r fetch origin main
git -C $r checkout origin/main -- "VeritasIntelligenceAnalytics/Invoke-VIA-OneShot-v*.ps1"
& (Get-ChildItem "$r\VeritasIntelligenceAnalytics\Invoke-VIA-OneShot-v*.ps1" |
    Sort-Object Name | Select-Object -Last 1).FullName -Root $r
```

### 倉庫若再卡住
```powershell
via-unstick            # 解到與 origin 齊平;-DryRun 只診斷
via-copies             # 會自己偵測 bootstrap 死結並印出可貼指令
```

### 不變常令(必須持續遵守)
hash 定生死整併去重 · 只增不減零刪除(讓位+manifest)· 正本 version-forward 不就地改
(無版號檔可就地)· **glob 尾版動態解析嚴禁寫死版號(程式與給操作員的指令皆適用)**·
每 commit 雙推 main 與 claude/via-system-followup-tz7k9t · 誠實三態 OK/FAIL/SKIP 不假綠 ·
台帳 append-only · Zero-Hydra(同名雙物讓位或聯集)· 中途令即時吸收 · TEST DEBUG till it works ·
不卡斷 · 「先發先得」命名律 · 雲端側選擇性 git add + 再生物 `git checkout --` 讓位 ·
**never force-push** · Follow Tony

### 安全紅線
FRED 鑰永不入 git(鑰檔僅 `functional modules/VDF/output_hub/mega/.fred_api_key`,gitignored;
只判在位,永不讀值印值)· 遮罩字串 `<REDACTED:VDF_FRED_API_KEY>` · 每次 commit 前跑鑰匙守衛 ·
model ID 永不入推送產物(commit message / PR / 程式註解皆禁)· VES `--apply` 永不經短令 ·
同意閘不覆蓋(`Set-VIAGateDefaults` 只在未設時補,操作員既設值一律尊重)

---

## 8 附:雲端自動快照

`via-handover md`(CGC_MDL140)可隨時重生雲端側接棒快照(燈板/環境/能跑閘/資料庫/VRN/VAP/
日更鏈/候操作員缺口冊/次步)。該快照反映**當前容器**狀態,與工作站狀態不同,判讀時須分辨兩側。
