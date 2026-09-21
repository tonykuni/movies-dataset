# 批683 · 每一扇門都掛同一具引擎 —— PY 橋 100% 量出來的,PS 補到 100% 是注進去的

操作員令:「PY 都要導入加速器;PS 都要加入 25 個加速器;不卡斷;動態進度條;不然指令速度太慢」。

## 一 · 先量(LL329),量出來的是「PY 沒欠帳,PS 欠 15 支」

| 面 | 尺 | 量到 |
|---|---|---|
| PY 加速器橋 `[VIA:ACCEL-BRIDGE]` | `CGC_MDL124 --accel --subsystems`(在冊 .py;排除收容/退役/唯讀正典/凍結夾) | VDF **195/195** · VAP **247/247** · VRN **366/366** · VIA **1860/1860** = 100%;ALL 2854/2875(差的 21 支全是排除件) |
| PY 網路橋 `[VIA:NET-BRIDGE]` | `--net --net-callers`(批402:只算真向外擷取) | VDF 真擷取 **28/28** = 100%;預設尺報的「缺 8」是非擷取件(NOCALL),不是缺口 |
| PS 加速器橋 `[VIA:PS-ACCEL]` | `--ps`(在冊 .ps1 1,027 支) | 已掛 798 · **缺 55**:版史 20(同族非尾版)· VAP 上傳原件與 `_output` 快照夾 17 · `_patches` 1 · 25 冊本體 1(注進去=模組 dot-source 冊、冊 dot-source 模組=循環)· **真缺 15**(尾版啟動器) |
| 不卡斷 · 動態進度條 | 正典=`VIA_PS_PyProgress_Module.ps1`(批486:每一次 python 子行程邊跑邊轉播、`Write-VIAProgress` 動態條、逾時 Kill 整樹)+ `VIA_PS_Accel_Module.ps1`(`Invoke-VIAGuarded` 18 非阻塞看門狗 · 16/17 動態進度/說明) | Register v0241:python 呼叫 **148 處全部走 `Invoke-VIAPython`,直呼 0**;啟動器:VRN v0101 全走短令(✅)· OneKey v0101 自帶 `Start-Process -PassThru` 非阻塞包裝(2 處 EnvManager 直呼:--help / ocr --repair)· Complete v0102 / All v0105 自帶分離工人+直播尾讀(批340) |

PS 25 車道本體早就在:`VIA_PS_Accel_Module.ps1` 載 `VIA_PS_Accelerators_25_Roster_v0100.ps1`,容器 pwsh 實載 **ACCEL20 20 · ACCEL25 25 · Write-VIAProgress · Invoke-VIAGuarded 都在**。
832 支帶 v0100 標記的檔 dot-source 的是**同一個模組**,所以它們早就是 25 條——不為了改一行註解去動 832 支(LL333)。

## 二 · 做了什麼

| 件 | 檔 | 證據 |
|---|---|---|
| 橋掃器 v0106 | `CGC_MDL124_BridgeSweeper_v0106.py`(十二檢 12/12) | ① PS 正典塊改抄 Register 尾版 **v0101(PS 25)** 逐字;HAS 同時認 v0100/v0101 ② `--ps-tail` 只注尾版,版史列 HISTORY ③ PS 專用排除:`SOURCE_VAP_MODULE` / `_output` / `_patches` / `_sha` 凍結副本;PS 不可動:模組本體 · 20/25 冊 · PyProgress ④ +⑫ 檢(合成族 X/Y/Solo 負控) |
| 注入 15 支尾版 | 根 7(FixAll v0100 · OneKey v0101 · PDFPlumberPlus v0100 · Unstick v0100 · **VRN v0101** · VdfFetch v0104 · B535 PANORAMA)· VDF 3(Invoke-VDF / Invoke-VDF-Fetch / VIA-VDF-Path-Contract)· launchers 5(AcceleratedTest v0103 · AllInOne v0111 · VRNAudit v0105 · Sync-VIA-Bootstrap v0100 · Unstick-VIA-Paste v0100) | 每支 **+10 行 0 刪**(150/0);插在 `param(...)` 之後;重掃 缺 0 · 覆蓋 100.0% |
| 解析 | 容器裝了 pwsh 7.4.6(只為量,不入倉) | 15 支 `Parser::ParseFile` **errors 0**;`CGC_MDL168` PS 閘 A 語法道/B 參數道/C 轉義道 **GREEN**,棘輪基線 5 支/53 筆舊債(具名,不是這批弄壞的)· 新壞 0;格子「PowerShell 語法與參數名閘」轉綠(之前容器沒 pwsh 一直紅) |
| 登冊 | `registry-sync --apply` 活 5993 · 新 2 · 變更 17 | — |
| 全格子(LL117) | OK 255 · FAIL 20 · SKIP 6 · TIMEOUT 0(281 站;GRID_20260921_084039;容器 PATH 含 pwsh)· 對 批682 第四跑(FAIL 21):只在本批紅 0 · 只在 批682 紅 1 = PS 語法閘站(pwsh 到位後轉綠);其餘 20 紅仍是容器缺料缺件,逐站同 | 第五跑照出兩盞我自己的紅:總控頁沒隨元件冊再生(test_11)、規劃器把還沒進 git 索引的新版橋掃器判「未在冊」——再生 + 加進索引後第六跑收 |

**沒做的,以及為什麼(L87)**:版史 21 支不注(批670:尺不把版史當資產;要注一句話 Z75)· VAP 上傳原件/快照夾 17 支與 `_patches` 不注(收容/一次性件)· OneKey 那 2 處 EnvManager 直呼不改(它自己的 Start-Process 包裝已是非阻塞;改呼叫形狀是另一批)· 832 支 v0100 註解不改 20→25(模組同一個)。

## 三 · L70 的交代

這 15 支 `.ps1` 各加 10 行,一個既有字元都沒動。逐次許可=本批操作員令原文「PS 都要加入 25 個加速器」;注入器是既有正典 `CGC_MDL124 --ps`(批355 同一條路),不是我手改。要回退:`git checkout` 那 15 支即可,或刪 v0106 讓尾版回 v0105。

## 四 · 為什麼還會覺得慢(量到的,不是猜的)

- 慢多半不在「沒掛加速器」,在**料**:工作站六層鏈 GREEN 29 · RED 3 · NODATA 14(側線台帳),NODATA 的站每跑一次都在等一個不存在的表;`via-ryg vrn -Timeout 600` 那種 600 秒就是這樣來的。
- `Show-VIAAccel20` 第一次點亮會拉 SUP_MDL737 `--activate`(批487 已改快取優先;`VIA_ACCEL_LIT` 快取一窗一次)。
- 貼回工作站 `via-vrnrun` 的 V2 秒數與 `via-vcgc status` 的秒數,我才知道慢在哪一站——這一批把「看得見」補齊了,下一批才談「快」。

## 五 · 一貼即用

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
git fetch origin claude/awesome-bardeen-h0wm5v
git switch claude/awesome-bardeen-h0wm5v
python "supportive modules\registry\CGC_MDL124_BridgeSweeper_v0106.py" --ps --ps-tail
python "supportive modules\registry\CGC_MDL124_BridgeSweeper_v0106.py" --accel --subsystems
via-vrnrun -Quick
via-vcgc status
```

貼回:兩行 `[橋掃]` 總表、`via-vrnrun -Quick` 的 V1–V5 各站秒數、`via-vcgc status` 全段。
