# 批692B · 每一道指令都帶加速器(PY 100% · PS 100%)+ 動態進度條的真百分比(候 L70 許可)· 2026-09-21

> **撞號**:VRN 線的 批692(Z84 結案)先併 main(PR #69),本批依 LL334 改稱 **批692B**(已推 commit 主旨不改)。
> 操作員令(與批683 同句):「py 指令都要加入加速器;ps 指令都要加入 25 個加速器;動態進度條不卡斷、動態百分比」。
> 先量再動(L01):量到的欠帳只有 PS 的 21 支;PY 一支不欠;「動態百分比」欠的是**協定**不是套件。

## 一 · 量到什麼

| 尺 | 量到 | 動了什麼 |
|----|------|----------|
| `CGC_MDL124 --accel`(PY ACCEL 橋)| VDF 掃 281 · 已掛 217 · 缺 0 · 排除 64(收容原件/退役/凍結群)· **覆蓋 100%**;批683 四系已量 VDF 195/195 · VAP 247/247 · VRN 366/366 · VIA 1860/1860 | 不動(沒有欠帳) |
| `CGC_MDL124 --ps`(PS-ACCEL 25 加速器橋)| 掃 1028 · 已掛 814 · **缺 21**(Invoke-VIA-OneKey v0100 · OneShot v0100–0102 · VRN v0100 · VdfFetch v0100–0103 · launchers/AllInOne v0104–0110 · VRNAudit v0100–0104;全是版史,Z74 候「注」)· 排除 193 · 覆蓋 97.5% | 操作員令=「注」:`--ps --apply` 注入 21 支([VIA:PS-ACCEL:v0101] PS 25 加速器橋正典塊,逐字抄 Register 尾版)→ 再掃 **835/1028 · 缺 0 · 覆蓋 100%**;pwsh 逐支 ParseFile 21/21 OK;PS 語法閘棘輪 基線 5 支/53 筆不變 · 新壞 0 · 裁決 GREEN;MDL124 十二檢 12/12 |
| 25 加速器本體 | `supportive modules/VIA_PS_Accel_Module.ps1`(TOOL-101;$VIA_ACCEL20/$VIA_ACCEL25 冊 + Invoke-VIAGuarded 看門狗);832 支帶 v0100「20」字樣的註解 dot-source 的就是這一支 25 冊(Z76:註解統一成 v0101 是另一道裁定,改 794 支只動一行註解) | 不動(功能已是 25;Z76 留給你裁) |
| `VIA_PS_PyProgress_Module.ps1`(所有 py 指令的統一啟動包裝 Invoke-VIAPython;批486/542)| 動態條用 Write-Progress:**百分比 = (經過秒數 % 30) × 100 / 30 的脈動**——不是真進度,只是「還活著」;逾時 Kill 整樹=不卡斷已在 | 沒動:ps1 要 L70 逐次許可;提案見二 |

## 二 · 「動態百分比」要的是一條協定,不是新套件(候你一句「准改 PyProgress」)

現況:啟動器不知道引擎跑到哪,只能脈動。真百分比要引擎講、啟動器聽:

1. **引擎側(PY,零新依賴)**:凡有可數的迴圈,印一行 `[進度] n/N 說明`(stdout、flush)。格子已經這樣印(`70/281 24.9% · 剩約 79s`),其餘引擎逐支接——VRN 家族交 VRN 線,VDF/VAP/中央本線接。
2. **啟動器側(PS,`Invoke-VIAPython` 一處)**:轉播 stdout 時若最後一行符合 `(\d+)/(\d+)`,`-PercentComplete` 用 n/N 真值並印「n/N xx% · 剩約」;沒有就維持脈動。行本身照原樣進 pipeline(⑤ 檢:一行不少、stderr 不混)。
3. **不卡斷**:現有 `-TimeoutSec` Kill 整樹保留;另加「30 秒無輸出」的**心跳警示**(只警示不殺)。

這一步改的是 `supportive modules/VIA_PS_PyProgress_Module.ps1`(無版號冊=就地改),**L70:等你一句「准改 PyProgress」我就落地並補進 via-pyprog 六檢第七檢**。

## 三 · 你貼回的兩盞紅(Z84)——根因線索已到,交 VRN 線

| 站 | [FAIL] 行(工作站,樹在 claude/vrn-line-b691) | 誰 |
|----|----------------------------------------------|----|
| SUP_MDL746_PDFPlumberPlusHub | ⑦ 密度只當訊號不當判決——949×7448 長捲頁那件有 862 字真正文、密度 1.22e-04 低於門檻,光看密度會假紅;字數 ≥300 只標 THIN 不降級(批440…) | VRN 線(夾具/pdfplumber 版本差) |
| CGC_MDL141_ClosingGate | ⑫ CLI --db/--zones 真的傳到 vrn_closeout(批425);實跑證據=ENG080 報 GREEN/上漲已算… | VRN 線(收尾閘讀哪本庫;疑 Z88 第二顆頭) |

## 四 · 工作站樹的狀態(你的手)

`git pull origin claude/awesome-bardeen-h0wm5v` 被擋:「you have unmerged files」——工作站現在停在 VRN 線的分支 `claude/vrn-line-b691`(644663ee),而且有一個沒解完的 merge。先 `git status` 看是哪幾檔;不要那個 merge 就 `git merge --abort`,再切回本線分支拉。VRN 線若曾要你在它的分支上併東西,以它的說法為準。

## 五 · 全格子 v0445(容器;PATH 帶 /opt/pwsh)

OK 273 · FAIL 5 · SKIP 8 · TIMEOUT 0(231s;GRID_20260921_173357)——逐站與批690 收尾相同:新紅 0 · 消失 0。21 支 ps1 注入後 PS 語法閘仍 GREEN(棘輪 5/53 不變)。

**併 main 90c59c14**(PR #65 本線 批690 已併 · PR #68 VRN 線 批691 追記):掉球 Z114 撞號,VRN 線先併贏,本線 PyProgress 那條改 **Z115**;併後鏈綠(VCGC v0123 29/29 · 契約 OK);全格子 v0445 OK 273 · FAIL 5 逐站相同(GRID_20260921_174055)。批692 尚未併 main:要併請開新 PR(本線分支 claude/awesome-bardeen-h0wm5v)。

## 六 · 工作站側枝 `local/parallel-b692`(bee8a683;39 件 · 39,866 行)——VRN 件,交 VRN 線收容

操作員照 L25 把工作站未追蹤件推到側枝(原件零觸碰,再生物已用 MDL167 還原,工作樹只剩 `.bak_b600_*`)。件名:

| 夾 | 件 | 看起來是 |
|----|----|----------|
| `functional modules/VRN/engine/` | VIA_TW_Ticker_Master_v0210.py · VIA_VRN_FirstPageEngine.py(無版號)· VRN_AutoTestLoop.py · **VRN_Integrated_ReportDatabase_Engine.py**(批685 操作員上傳的那支)· **VRN_PanoramaProbe.py**(姊妹倉探針副本) | 別條線/探針落在母樹的引擎件;版號律與 Hydra 要 VRN 線對表(母樹已有 FirstPageEngine v0127) |
| `functional modules/VRN/tests/` | test_VRN_AutoTestLoop · test_VRN_FirstPageEngine · test_VRN_PanoramaProbe · test_VRN_ReportDatabase_Engine | 對應上列四支 |
| `functional modules/VRN/knowledge/` | SYNONYM_LIBRARY_v3.json · v4.json · VRN_WORKFLOW_SPEC_v0200.md | 同義字冊上傳更新候選(只增不減閘 MDL176/樞紐增補冊走) |
| `functional modules/VRN/references/intake/VIA_SSOT_Additive_Audit_v0100/` | ADDITIVE_CANDIDATE · ALIAS_COMPARISON · CROSS_REGISTRY_CONFLICTS · SYNONYM_LIBRARY · user_aliases · audit_ssot.py · ticker_regexes.py · baseline/(樞紐 v0110、SSOT 五冊、broker_list…)· _upload/*.zip | 「SSOT REGEX 同義字上傳更新」的稽核包(操作員批689B 令的正本材料);收容原件不編輯,只讀進候選 |
| 根 | Invoke-VRN-AutoTest.ps1 | 自動測試啟動器(ps1;L70) |

本線不動這些(VRN 線的);已轉交(見七)。
