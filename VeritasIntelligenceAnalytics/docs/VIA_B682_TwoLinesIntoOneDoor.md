# 批682 · 兩條線的 VRN,收進同一扇門 —— 對接口可為獨立系統、可為子系統

操作員令:「https://claude.ai/code/session_01RLMQGZLcigd5Bt5aN6J4Ck  https://claude.ai/code/session_01YJPv4NqSj3YsMkkcrywaHw
將這兩個部分的 VRN 資訊全數擷取過來。這個系統單獨處理 VRN,可為獨立系統可做子系統。VRN_SystemManager 掌握上下對接,可為獨立系統可為子系統。」

## 一 · 先量:兩個 session 留下了什麼(對話讀不到,檔案讀得到)

| session | 落在哪裡 | 讀法 |
|---|---|---|
| `session_01RLMQGZLcigd5Bt5aN6J4Ck`(VIA Integration;主線) | main 上 批663–679d:15 份 `docs/VIA_B6xx_*.md`、B664 逐批、律冊、索引冊、引擎;**批680 五檔只 stage 未 commit(Z57)** | 全部已在本線(本線 = main + 批681) |
| `session_01YJPv4NqSj3YsMkkcrywaHw`(VDF 專案 VIA 管理邏輯;側線 `claude/busy-bell-97sa4f` · PR #53) | 7 commits · 46 檔:ENG088 增補審計橋 · SUP_MDL749 v0111 · 31 件收容包 · 單元測試 · 交接文 · Register v0241 / Deck v0158 / Manager v0147 / Grid v0431 · 啟動器 v0101 修 · VDF 現況審視文 | 本批**原樣收進**(見二);該 session 現況:`awaiting push of claude/brave-goldberg-ri5k42 to read session VRN logic`——**第三條線**要來了(Z70) |

兩個 session 的對話本身沒有工具可讀(CCR 只給 metadata);「對話會卡斷,檔案不會」——所以擷取的是檔案,不是聊天紀錄。

## 二 · 收進來的件(每一件都在**本樹**跑過)

| 件 | 檔 | 本樹實測 | 處置 |
|---|---|---|---|
| SSOT 增補審計橋 | `functional modules/VRN/VRN_ENG088_SsotAdditiveBridge_v0100.py` | 十九檢 **19/19** | 原樣 |
| 六欄規則樞紐 | `supportive modules/70_VRN_Rules/SUP_MDL749_VRNFieldRuleHub_v0111.py` | 四十八檢 **48/48** | 原樣;索引冊 `via-vrnbook build` 重指(守門 GREEN 50/50) |
| 收容包 | `functional modules/VRN/references/intake/VIA_SSOT_Additive_Audit_v0100_b20260921/`(31 件含 manifest) | 零觸碰(位元同側線) | 原樣 |
| 單元測試 | `supportive modules/registry/tests/test_vrn_ssot_additive_v0100.py` | **20/20** | 原樣 |
| 交接文 | `docs/VIA_S20260921_SsotAdditiveAudit.md` | — | 原樣 |
| Deck 任務 / Manager 正式名稱 | `CGC_MDL095_DeckServer_v0158.py` · `VIA_SYSTEM_MANAGER_v0147.py` | Deck **25/25** · Manager **10/10** · 總控頁再生 · 契約測試 **19/19** | 原樣(與 PR #53 位元相同,將來併 PR 不撞) |
| 規格項 | `VIA_InputConsole_Spec_v0100.json` +`vrn_ssot_additive`(pipeline 群;原檔格式位元不差) | — | 併入 |
| 台帳 | `VIA_AutoCode_Registry_v0100.json` +側線 4 筆(原文照錄,加 `origin` 欄) | — | 只增不減 |
| 啟動器修 | `Invoke-VIA-VRN-v0101.ps1`(一行:V2 單元素陣列被拆成字串,LL284 同族;**工作站已驗證通過**) | 容器無 pwsh | 原樣(見四) |
| Register + 梭 | `Register-VIA-Commands-v0241.ps1`(+`via-ssotadd`)· `via-ssotadd.cmd` · `bin/via-ssotadd.cmd` | — | 原樣(見四) |

**沒收的,以及為什麼**:Grid v0431(它的三站 批679c 已併進 v0432/v0433)· `docs/VIA_VDF_StatusReview_20260921.md`(VDF 不是 VRN,留在 PR #53)·
它的元件冊/索引冊/總控頁(本樹自己再生,不抄側線的再生物 LL49)。

## 三 · 對接口 v0101:可為獨立系統、可為子系統

`VRN_SystemManager_v0101.py`(廿五檢)——**模式是量出來的,不是設定**:

| 模式 | 判準 | 六域怎麼讀 |
|---|---|---|
| **subsystem**(子系統) | VCGC(VIA 唯一對接口 L20)在位且載得起 | 四庫+鏈快照+交接照讀;五面(規格/格子/短令/Deck/元件冊)、七處、掉球 n/open 經 VCGC 的讀器 |
| **standalone**(獨立系統) | VCGC 不在,或 `--standalone` | 四庫+鏈快照+交接照讀;尾版家族改自家 glob **並講明**;VIA 的面一律標 `STANDALONE` **不代讀、不猜**;上行 `vcgc=STANDALONE` |

新增 `records` 域(read records / `records` 動詞)= **兩線 VRN 紀錄索引**(指標不複本 L05):
- 血脈:由 git 尾註 `Claude-Session:` 量出來——哪個 session、幾筆 commit、批號範圍、最新主題;
- VRN 文:docs 檔名含 VRN 或提及 ≥8 次;收容包:`references/intake` 逐夾(檔數 · 批標);活線:遠端分支數與含 vrn 的分支名。

自測新增 ㉓ 雙模式(強制 standalone 跑一次 collect,六域都在、五面標 STANDALONE、關掉後回 subsystem)· ㉔ 紀錄索引(本 session 在血脈裡、≥2 session、全景文與 b20260921 收容包在列)· ㉕ 側線件在位(ENG088 / 749≥v0111 / 單元測試)。

## 四 · L70 的交代(.ps1 三支是側線的件,本批只搬不改)

`Register-VIA-Commands-v0241.ps1`、`Invoke-VIA-VRN-v0101.ps1`、兩支 `via-ssotadd.cmd` 都是**側線 session 在操作員令「註冊這些」「更新完 VRN 相關可以進行最後一次實測收尾」之下造的**
(它的交接文第二節第 3 列把 L70 逐次許可寫明了)。本批一個位元都沒改,只把它們原樣搬到本線——理由是這一令要「全數擷取」。
若不認可:刪掉那三個新版號檔就回退(尾版律);`via-vrnsys` 仍**未登**(Z65 照舊候「准改 Register」;下一版是 v0242)。

## 五 · 側線帶回來的工作站數字(從它的台帳原文讀出,不是我跑的)

```
via-vrnrun(工作站;Invoke-VIA-VRN v0101):
  V1 冊重建 rc=0 · V2 六層鏈 GREEN 29 · RED 3 · GATED 0 · NODATA 14(與直跑 via-vrnchain run 同答)
  V3 庫價重算 39 筆 ADJ · V4 判對率 100.0% = 461/461 · 可判率 62.7% / 67.1% · V5 落頁
```
容器對照(本批,套件補齊):六層鏈 GREEN 16 · RED 16(缺件 11 · 缺料 1 · 其餘 4)——**同一條鏈,工作站與容器差在料與境,不在碼**。

## 六 · 容器實測(本批)

```
對接口 v0101 status(subsystem):
  政策 GREEN · 邏輯 GREEN(守門 50/50 · 索引 v0104 建於 v0105 builder)· 因子 GREEN 130 列 · 參數 GREEN 38 冊
  引擎 RED(鏈快照 = 套件補齊後的第二跑:GREEN 31 · RED 1(ENG068 features_daily 缺料)· NODATA 13 · GATED 1)· 樣本 ABSENT(C:\測試樣本報告 = 工作站路徑)
  交接 STALE(一頁 批554 < 律冊 批662)· 紀錄 GREEN(session 6 · commit 600 · VRN 文 32 · 收容包 20 · 活線 31)
  上行 七處 4/7(規格 ✅ 格子 ✅ 元件冊 VIA-SYS-0011 ✅ 交接 ✅;短令/Deck/Manager ❌=L70 候令)· 連結 159 · rc 2
對接口 v0101 status --standalone:模式 standalone · 上接 VCGC ABSENT · 家族 69(自家 glob)· 五面 STANDALONE 不代讀 · 六域照讀 · rc 2
自測:VRN_SystemManager 廿五檢 25/25 · VCGC v0118 廿四檢 24/24(via v0101 · 連結 158)· 索引冊 v0105 十六檢 16/16 · 守門 50/50
側線件:SUP_MDL749 v0111 48/48 · ENG088 19/19 · test_vrn_ssot_additive 20/20 · Deck v0158 25/25 · Manager v0147 10/10 · 總控頁契約 19/19
元件冊:registry-sync --apply 活 5991 · 新 36 · 變更 248 · 退役 0;家族 270 已登 270 未登 0;Deck 90 · 規格 65 · 格子 287 · Register 166
格子 --only:VRN 子系統管理 2/2 · SSOT 增補 2/2 · 研報六欄規則正本樞紐 2/2 · 索引冊十六檢 1/1
全格子(FAST · 套件補齊):OK 254 · FAIL 21 · SKIP 6 · TIMEOUT 0(281 站;GRID_20260921_081452)· FAIL 集合與 批681 第二跑(21)逐站相同:只在本批紅 0 · 只在 批681 紅 0;第三跑多出的一紅(索引冊 ⑧ ENG088 未交代)已由 v0105 收
```

## 七 · 你的手

1. 第三條線 `claude/brave-goldberg-ri5k42`:側線 session 在等它推上來;推了之後三線要對表(版號 · 台帳 · 冊)才併(Z70)。
2. PR #53 現在與本線有 11 個位元相同的檔、5 個會衝突的再生冊(元件冊/台帳/索引冊/規格冊/總控頁):併它時**以本線為準再 `via-vcgc registry-sync --apply`**,或關掉 PR #53 改併本線(Z69)。
3. 批680 五檔(Z57)· 「准改 Register」給 `via-vrnsys`(Z65)· 開閘補上市所 ADJ(Z62)· `via-vcgc page --publish`(Z58)。

## 八 · 一貼即用(前兩行固定;本線在 `claude/awesome-bardeen-h0wm5v`)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
git fetch origin claude/awesome-bardeen-h0wm5v
git switch claude/awesome-bardeen-h0wm5v
$m = (Get-ChildItem ".\functional modules\VRN\VRN_SystemManager_v*.py" | Sort-Object Name | Select-Object -Last 1).FullName
python $m --selftest
python $m status
python $m records
python $m status --standalone
via-ssotadd status
via-vrnrun
via-vcgc status
```

貼回:`python $m status` 全段、`python $m records` 前十行、`via-vrnrun` 的 V2/V4 兩行、`via-vcgc status` 的「VRN 系統管理」與「註冊稽核」兩行。

## 九 · 實測樣本夾(操作員 2026-09-21 令:「實測樣本(隨時更新):C:\測試樣本報告」)

- 登進**冊**不是引擎:`via-console set vrn-dir=C:\測試樣本報告`(MDL139 報告夾律唯一正本:`--dir > user.vrn_dir > dir_default`;changelog 自帶留痕)。
  以後 `via-vrnrun` / `via-firstpage` / `via-vrnmatrix run` 不帶 `--in` 就吃這個夾;帶 `--in` 照舊優先(輸入位置解放律不變)。
- 對接口 status 多一行「樣本」:讀冊上 `user.vrn_dir`、現量本機在不在與檔數——**容器 ABSENT 是誠實**(工作站路徑),工作站應印 60 PDF + 4 DOCX 上下(隨時更新,以你貼回為準)。
- 冊上 `extensions` 仍是 `[.pdf,.docx]`(舊引擎依它 glob;影像件走 `intake`)——沒動,批465 的只增不減。
- Z51「64 份未掛進任何 AI 境」仍成立:容器沒有這個夾;掛進去=你的手。

## 十 · 索引冊 v0105:新家族要被交代,尺也要能容得下「未來」

收進 ENG088 之後全格子當場照紅一站:「VRN 邏輯架構索引冊十六檢 ⑧ 樹上每一個 VRN_ENG 家族都要被交代」——**尺對,樹上真的多了一支沒被交代的家族**。
照冊自己的規矩掛進 `OFF_BOOK_PENDING`(它的規格項寫著「不在六層鏈上,是稽核件」;上不上冊、上哪一層=架構裁定,Z73),`via-vrnbook build` 重建。
接著 ⑩ 紅:它釘著 `OFF_BOOK_PENDING == []`——可是 docstring 自己說這張表「只留未來樹上新冒出來的」,要求它永遠空等於要求未來永遠不准有新引擎(LL332)。
`via_vrn_logic_book_v0105`:⑩ 改成不變量「歸位的 15 支不得同時掛待裁定」;十六檢 16/16、守門 50/50、格子那一站轉綠。**其餘一字不動。**
