# VIA 收尾矩陣 · 2026-09-28 05:25(Asia/Taipei)· 容器重量 · VCGC Master Prompt 十步格式

側線 2026-09-28(主線批號由併線的手指定 L25)· PR #327 · 分支 `claude/vcgc-vrn-read-forward` · 樹 = 工作站線 15b7e409 + 本筆只增紀錄。
量測環境:**容器**(Linux · 無 pwsh · 無資料家 · 無 `C:\測試樣本報告`)。工作站那份是 `docs/VIA_Closeout_Matrix_20260928_0430.md`,兩份並列不互蓋。
**本筆沒有改任何一支引擎或 .ps1**:操作員 VCGC Master Prompt 規定修補先經 via 審核,所以找到的修補全部寫成提案 → `docs/VIA_Patch_Proposals_20260928.md`(P1–P6)。

## Step 1 · 政策確認結果

- 已讀:CLAUDE.md、倉根一頁交接 〇 接手提示 · 一 政策庫(L01/L03/L04/L05/L16/L20/L25/L50/L65/L70/L102/L103)、Master Prompt 全文。
- 禁止清單:TA-Lib(L50 第一條)· 未經 VCGC 批准不 `registry-sync --apply` · 不自動套 AST patch · 不自動載未知二進位 · 一行一指令。
- **政策衝突(停在部署前)**:Master Prompt 要 layout 載入 `SUP_MDL743_GenericLayoutHub_v0108` 並 `import VIA_SuperAccel_ModuleLayout`;樹上尾版是 **v0109**(6f772b92,已在 main),`VIA_SuperAccel_ModuleLayout` **全樹 0 支**。照 Master Prompt「衝突即停」「缺模組不得執行 layout」→ 不部署 layout、不改版號,等操作員裁(掉球 Z230)。
- 誠實揭露:Master Prompt 送達**之前**,本線照操作員前一道令(C 段)跑過一次 `registry-sync --layout-only --apply`(1/61/0 → 0/0/0)。那一筆後來被工作站線 15b7e409 蓋過(工作站也 apply 了);Master Prompt 之後**沒有再 apply**。

## Step 2 · 工具完整性

| 件 | 燈 | 證據 |
|---|---|---|
| VIA_SuperAccel_Module(加速器) | GREEN | import OK;尾版正主 VeritasCeleritas_v1141 載入 OK,檔內零 talib |
| VIA_SuperAccel_ModuleLayout | ABSENT | 全樹 0 支(Master Prompt 要求 → 衝突,Z230) |
| SUP_MDL743_GenericLayoutHub | YELLOW | v0104–v0109 都在;尾版 v0109 ≠ Master Prompt 指定 v0108;兩版都 LF、都帶標準加速橋,都沒 import ModuleLayout |
| SUP_MDL740 NetUnified | GREEN | v0115 · v0116 · v0117 在(尾版 v0117 ≥ v0115,沒降版) |
| VeritasAegisNexus v0116 | GREEN | `supportive modules/network/VeritasAegisNexus_v0116.py` 在 |
| NLP SUP_MDL866 v0105 | YELLOW | 在、帶加速橋;**沒有網路橋**(Master Prompt 寫「已加網路」,實量不符)。它不是 VDF 活件,是否需要網路橋請裁 |
| VDF 網路工具 | YELLOW | status:VDF 橋 加速器 78/78 · 網路 74/78(既有,未變) |
| TA-Lib | GREEN | CGC_MDL190 imports 0;L50 全景 尾版 516 · import 0 · 已裝 False;`find_spec('talib')` None |
| PY 加速橋 | RED | CGC_MDL183 [PY ] 缺 91(Z223) |
| PS 模板章 | GREEN | CGC_MDL183 [PS ] 基線外新缺 0(59 支由工作站線接;5 支 intake 記債 843) |

## Step 3 · 換行 / 哈希

| 件 | 燈 | 證據 |
|---|---|---|
| layout 鎖冊 11 來源 | GREEN | 容器 11/11 **原位元**相符,全 LF、0 個 CR。工作站「9 相符 + 2 CRLF(ENG112 · ENG110)」是 Windows 工作複本換行;去 `\r` 後比對即可,鎖冊哈希不改 |
| 附件比對(操作員指定最新版) | GREEN | NLP OneEngine v1.9.0 .py/.html 與樹位元同;bundle 89/90 同(差的 1 支 .log 被 .gitignore 擋,sha 與包內 MANIFEST 相符);Celeritas 1.14.0 40/41 同(og.jpg 被 *.jpg 擋,sha 與 SHA256SUMS 相符);layout v0104 包 35 同 · 9 支 .py 去掉加速橋後位元同 · InputConsole 冊包比樹多一項(Z228) |

## Step 4 · 掃描(輕量)

- 全樹 `.py` 用 `compile()` 掃(不只 `ast.parse`):`from __future__` 位置錯 → **3 支尾版 SyntaxError**(SUP_MDL749 v0114 · VDF_ENG088 v0103 · CGC_MDL180 v0100;根因 b12e82ff,Z226)。另 MDL116 v0106–v0110 的 f-string 反斜線是 py<3.12 語法限制,工作站 3.12 不受影響;退役夾 3 支語法壞檔照舊不動。
- NLP v0105 imports:VIA_SuperAccel_Module · importlib · json · os · pathlib · sys;無 subprocess、無 talib。
- 未自動載入任何二進位。

## Step 5 · AST 定位

| 檔 | 行 | 問題 |
|---|---|---|
| SUP_MDL749_VRNFieldRuleHub_v0114.py | 2–15 / 141 | 加速橋在 `from __future__`(141)之前;141 之後另有一段正確的橋 |
| VDF_ENG088_ConsensusFusionBridge_v0103.py | 3–16 / 57 | 同上;57 之後另有正確的橋 |
| CGC_MDL180_FreezeSealAudit_v0100.py | 3–16 / 56 | 橋只有這一段,位置在 `from __future__`(56)之前 |
| VIA_SYSTEM_MANAGER_v0149.py | 34–65 | 只暴露 selftest/main,沒轉 do_list/_build_page(CI 紅) |

## Step 6 · 建議 patch

全部在 `docs/VIA_Patch_Proposals_20260928.md`(純文字 diff):P1 `__future__` 橋位三支新版號 · P2 `VIA_SYSTEM_MANAGER_v0150` · P3 PS 模板章加固 · P4 邏輯索引冊 build · P5 InputConsole `vcgc_layout_review` · P6 主控台 layout 自測路由。

## Step 7 · 是否需要 via 審核

**是,P1–P6 全部要。** 本筆一件都沒套。

## Step 8 · 測試結果(容器,同一棵樹 15b7e409;未套修補)

| 區 | 件 | 燈 | 證據 |
|---|---|---|---|
| VCGC | CGC_MDL149 v0161 --selftest | GREEN | rc0 [OK] |
| VCGC | CGC_MDL226 --selftest | GREEN | rc0 [OK] |
| VCGC | CGC_MDL190 TALibLock | GREEN | talib GREEN · imports 0 |
| VCGC | CGC_MDL183 閘 | RED | PS 新缺 0 · 自測 OK 7 · FAIL 1(⑤ 批345,Z218)· PY 缺 91 → scan state RED |
| VCGC | CGC_MDL220 SuccessLedger | GREEN | lock_success true · missing [](工作站 04:30 記 false,要再量) |
| VCGC | registry-sync --layout-only | GREEN | 乾跑 0/0/0 |
| VCGC | 版面樞紐 SUP_MDL743 v0109 自測 | GREEN | rc0 [OK](直接量;`via-vcgc layout --selftest` 被主控台攔走,Z225) |
| VCGC | layout --manifest | GREEN | version v0104 · REGISTERED · errors [] |
| VCGC | status 邏輯庫 | RED | 索引冊過期 SUP_MDL743 v0105→v0109(P4) |
| VCGC | status 因子庫 | GREEN | OK · 130 列 |
| VCGC | status VRN 系統管理 | RED | logic RED · engine RED · handover STALE |
| VCGC | status VDF 系統管理 | GREEN | GREEN(engine 子燈 RED) |
| VCGC | status L50 全景 | GREEN | import 0 · 已裝 False |
| VCGC | status SSOT 連動 | RED | **BROKEN 4** · YELLOW 4 · ABSENT 2 · GREEN 2(P1 實測可轉 BROKEN 0) |
| VCGC | 全格子 CGC_MDL064 v0498 | RED | OK 300 · FAIL 46 · SKIP 15(修補前工作樹;無 base 對照,不宣稱本 PR 造成;再生件 stash 未 commit) |
| VCGC | CI Windows bundled Chromium UAT | RED | VIA_SYSTEM_MANAGER_v0149 沒轉 do_list(main 同病,Z229;PR 已留言) |
| VDF | VDF_SystemManager v0118 --selftest | GREEN | rc0 [OK](工作站記 rc2) |
| VDF | DATAHOME 目錄 · 四個 .duckdb | ABSENT | 容器無資料家;工作站 04:30 量到四庫都在(656.3 / 88.8 / 7.0 / 0.8 MB) |
| VDF | ENG087 v0104 個股清單 · ENG077 v0103 主動 ETF | GREEN | 7/7 · [OK];每日實跑未量(Z227) |
| VRN | VRN_SystemManager v0108 --selftest | GREEN | rc0 [OK](工作站記 rc1) |
| VRN | ENG111 v0104 · ENG112 v0100 · ENG110 v0116 | GREEN | 三支 rc0 [OK](工作站記 ENG110 rc1) |
| VRN | CGC_MDL193 七鎖 | GREEN | StockIdentity · VrnTab v0101 · TabField · FinancialRead · FinancialShown · GateMap · StatusLock v0105 全 lock_success true |
| VRN | layout --dir C:\測試樣本報告 | ABSENT | 容器無(工作站 04:30 記 RED,原因沒寫) |

**計:** GREEN 15 · RED 6 · ABSENT 2 · 共 23 格(Step 8)。容器與工作站同一件量出不同燈的有 5 件(SuccessLedger · VDF 管理器 · VRN 管理器 · ENG110 · 樣本批跑),都請工作站再量一次再定。

## Step 9 · 是否允許部署

**不允許。** 原因:① Master Prompt 與樹的 layout 版號衝突、`VIA_SuperAccel_ModuleLayout` 缺(Z230)② P1–P6 都還沒過 via 審核 ③ PR #327 CI 紅(base 的病)。

## Step 10 · VCGC 最終判定

**HOLD。** 紀錄已落冊(只增不減),修補全部寫成提案等 via 審核,layout 不部署。操作員要裁:

1. 併不併 PR #327(tonykuni/movies-dataset)。
2. Z218 批345 正本:退役還是放回。
3. Z230 layout 版號:用樹上尾版 v0109,還是回 v0108;`VIA_SuperAccel_ModuleLayout` 要不要造。
4. P1–P6 各准不准(P1 修 SSOT BROKEN 4;P2 只修 CI 的一半)。
5. Z223 PY 缺橋 91 逐支注還是記唯讀。
6. Z220 全樹 registry-sync(退役 854)准不准 apply。
7. Z227 兩清單的每日排程設不設。

## 工作站一貼(一行一個指令;驗 PS 模板章 Z224 · 鎖冊換行 Step 3)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
git fetch origin
git checkout claude/vcgc-vrn-read-forward
git pull --ff-only origin claude/vcgc-vrn-read-forward
git log --oneline -1
$joined = Get-ChildItem -Recurse -Filter *.ps1 | Where-Object { Select-String -LiteralPath $_.FullName -SimpleMatch '[VIA:PS-TEMPLATE:v0100]' -Quiet }
$bad = foreach ($f in $joined) { $t = $null; $e = $null; [void][System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$t, [ref]$e); if ($e.Count) { "PARSE-FAIL $($f.Name): $($e[0].Message)" } }
"[PS 接章] ParseFile 驗 $(@($joined).Count) 支 · 壞 $(@($bad).Count)"
$bad
$p0 = (Get-Process -Id $PID).PriorityClass
& .\Invoke-VIA-VCGC-Lock.ps1
$rc = $LASTEXITCODE
$p1 = (Get-Process -Id $PID).PriorityClass
"[Lock 真跑] rc=$rc · 優先權 前 $p0 後 $p1(前後相同 = 已還原)"
via-vcgc status
```

貼回:`[PS 接章]` 那一行(有 PARSE-FAIL 的話連它一起)、`[Lock 真跑]` 那一行,還有 `via-vcgc status` 裡「邏輯庫 / 因子庫 / VRN 系統管理 / VDF 系統管理 / L50 全景 / SSOT 連動」六行。**不要跑 `registry-sync --apply`。**
