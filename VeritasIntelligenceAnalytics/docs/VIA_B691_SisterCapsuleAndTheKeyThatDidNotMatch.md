# 批691 · 姊妹倉 VRN 膠囊收件:量了才知道洞不在解析器,在正典鍵對映沒對到活表的鍵

> 本線=VRN 線(分支 `claude/vrn-line-b691`,從 main 7804493c 起算);批號 691 取號前掃過全部遠端分支(LL334):批690 在 awesome-bardeen 未併,691 空。
> 版號:ENG086 取 **v0113**。開 PR 時 main 已前進(PR #53/#59 併入:ENG086 v0112 聯集版 · Grid v0443 · VCGC v0122 · 總管 v0104),本線併 main 後把 v0113 **重疊在 v0112 上**(v0112 的別名層/文字層拒絕閘 ㉓–㉖ 判準不動;㉕ 期望值改走正典鍵;本批的檢成 ㉗,二十七檢)· Grid **不開新版**(v0440–v0443 一天四版,見 Z112)· 掉球本線五列因 main 已到 Z108 改號 Z109–Z113 · 台帳聯集 1299+1 · 元件冊/索引冊/一頁交接取 main 後以尾版重跑。

來件:母線 awesome-bardeen 批690 轉交(2026-09-21 13:21Z)——姊妹倉 `tonykuni/VIA-VDF-VRN` 的 Claude session 依操作員令「將專案中所有的 VRN 接到此處理」送來 VRN 交接膠囊。
正本已對:分支 `claude/festive-ptolemy-ts2yyh` c1989e6 `docs/VIA_VRN_HANDOVER.md` 103 行;PR #23 **未併**其 main。母線只記進 B690 文五與掉球 A/Z67/Z68;a/c/e 的 AI 端交本線。

## 一 · 先量(容器;唯讀,姊妹倉零觸碰)

| 面 | 量到 | 讀法 |
|---|---|---|
| 探針原樣跑(姊妹倉根,名冊 64 件) | S01 OK 64 · S02 BLOCKED 64 · S06 OK 41/WARN 23 · S07 SKIP 64 · S08–S10 BLOCKED 64;verdict AMBER;根因 RC1–RC6 | 與膠囊、全景頁一致 |
| 探針 `--vrn-root` 指到母 VRN 根 | **RC2「正典樹缺 MDL001–008」消失**;剩 RC1 無位元組 · RC3 套件 9/18 · RC4 橋找舊名 `VIA_SuperAccel_Module`(母正本 SUP_MDL737 v0105)· RC5 黃燈 23 · RC6 閘關 | 落地母樹能解一根;真結果仍要工作站位元組(膠囊 b=操作員的手) |
| 64 件檔名 × 三把尺(現場算,不寫死) | 無版號 `vrn_d8b_filename_parser` 47/64 · 探針 59/64 · **母閘路**(SUP_MDL749.broker_of → ENG086)59/64;閘路缺而探針有 = **0** | 膠囊說的「母解析器 50/64、改 d8b 前綴比對」指的是 d8b;d8b 不在六層冊(0 引用)、格子無站,只被冊/manifest 引——改它=第二套判準(L05),不改 |
| 同一 64 件,閘路回的**鍵** | Daiwa ×4 回 `DAIWASECURITIES`、JP ×2 回 `J.P.MORGAN`;只有 MEGABANK→MEGA 中 | MDL176 裁定拼法「DAIWA SECURITIES」「J.P. MORGAN」有空白;三表合併後的正典鍵沒空白;`_canon_key` 逐字 upper() 查表查不到 → **同一家仍兩個名**。v0110 ㉒ 拿裁定冊自己的拼法驗,所以一直綠(自測讀的是裁定冊的字串,不是活表的鍵) |
| via-envmanager 線的 ENG086 v0112 | `_canon_key` 與 v0110 逐字相同,沒修這個 | 本線 v0113 是新工,不是重工;併線時兩邊拒絕閘取聯集,對映摺鍵以 v0113 為準 |

## 二 · 做了什麼(一支引擎新版 + 三本冊刷新;冊零觸碰:正典冊/裁定冊/疊加層一個字沒動)

| 件 | 檔 | 改了什麼 | 驗 |
|---|---|---|---|
| 正典鍵對映對活表鍵生效 | `functional modules/VRN/VRN_ENG086_FirstPageLogicBridge_v0113.py` | `_norm_key()` 摺掉非字母數字;`_gate176` 多存 `rulings_norm`;`_canon_key` 先逐字查、查不到再以摺鍵查(六條裁定一條不動,`rulings` 計數仍 6)| **二十三檢 23/23**;+㉓ 裁定冊 × 活券商表現場取交集 **4/4**(DAIWASECURITIES→DAIWA · IBF→WATERLAND · J.P.MORGAN→JPM · MEGABANK→MEGA)漏 0 |
| 四支消費者一起生效 | (樞紐 SUP_MDL749 v0112 零改,`matchers()` 尾版 glob 自動接 v0113) | — | 樞紐 49/49(㊼ 經 v0113);64 件複量 Daiwa→DAIWA · JP→JPM;閘路仍 59/64 |
| 索引冊 | `VIA_VRN_LogicArchitecture_SSOT_v0100.json` | `via-vrnbook build`(v0106 冪等):ENG086 指標 → v0113 | 指標 50 · 在位且尾版 50 · 過期 0;總管連結 RED 2 → **GREEN 164**(Z113) |
| 聯集冊 | `VIA_SSOT_SynonymUnion_v0100.json` | MDL176 `--apply`:內容不變(只增不減先證),gate_bypass 旗 → v0113 過閘 | 沒過閘 7 / 讀冊 10(同批689B;7 支=Z91) |
| 元件冊 | `VIA_Component_Inventory_SSOT_v0100.json` | VCGC v0119 registry-sync `--apply`:活 6019 · 新 1 · 變更 65 · 退役 0 | VCGC 二十五檢 25/25(⑬ 6019/6019 · ㉔ 經總管 v0103) |
| 掉球 | `docs/VIA_DroppedBalls_B507.md` | +Z109(膠囊 a 三選一)· ~~Z110~~(c 已結)· +Z111(e 等 a)· +Z112(Grid 站名不開新版)· +Z113(尾版檔 → 冊落後) | 只增不減;A/Z67/Z68 三列母線批690 已改、本線不動(併線取聯集) |

**沒動的**:`vrn_d8b_filename_parser.py`(不在活路)· Grid(Z112)· 樞紐 · 正典冊/裁定冊/疊加層 · 姊妹倉任何檔 · `references/intake`。

## 三 · 膠囊六節「你的手」逐條處置

| 膠囊 | 誰 | 本批 |
|---|---|---|
| a. 探針落地方式 | 操作員裁(Z109 三選一;本線建議 ②:落地 ENG089 但 S06 改綁樞紐,不帶第二套券商表) | 量好了,等裁 |
| b. 工作站真跑探針把 64 件 BLOCKED 變真結果 | 操作員的手 | PS 區塊在七 |
| c. 券商正本對齊 | AI | **已結**(Z110):洞在對映,不在解析器;ENG086 v0113 |
| d. 注入器 `--apply` | 操作員的手(L08);dry-run 母線 B690 四節已記 | 不動 |
| e. 七處登冊 + A/Z67 劃線 + Z68 復核 | 登冊等 a(Z111);A/Z67 劃不劃、#2/#3/#5/#21/#29 關不關=操作員;Z68 等工作站貼回 | 等裁 |

## 四 · 全格子(LL117;容器;PATH 帶 /opt/pwsh)

| 跑 | 數 | 讀法 |
|---|---|---|
| 第一跑(容器原境) | OK 254 · FAIL 28 · SKIP 5(GRID_20260921_133151) | 容器缺 pydantic / pdfplumber / polars:疊加層 ①「正典載入失敗 ModuleNotFoundError pydantic」、入庫 ㉑㉒㉓、首頁擷取 ⑪ 法B pdfplumber、統一報告引擎——**把本批改動整棵 stash 掉在原樹跑同 4 站,一樣紅**=境不是件;另有 6 站要前一份 GRID 存證(新容器第一跑必紅) |
| 第二跑(沙盒補三件) | **OK 268 · FAIL 15 · SKIP 4 · TIMEOUT 0**(260s;GRID_20260921_134001) | VRN 家族全綠、六層鏈實跑 OK;15 盞 = Z92 一族 13 + PowerShell 語法閘(pwsh 不在=容器固定紅)+ 矩陣式報告排版規格(非 VRN,兩跑同紅,未追根)。對 批689B 收尾的 FAIL 14:新紅 0(排版規格那站在那次容器也不在 Z92 名單,待下次對 GRID 存證) |

| 第三跑(併 main 後;Grid v0443 · 291 站) | **OK 274 · FAIL 12 · SKIP 5 · TIMEOUT 0**(267s;GRID_20260921_135042) | 12 盞=Z92 一族 + Yahoo 共識(容器無網);VRN 家族全綠;VCGC v0122 二十八檢 28/28 · 總管 v0104 連結 GREEN 171 · 沒過閘 6/讀冊 10(main 併入 SUP_MDL015 v0101 過閘,Z91 剩 6) |

ENG086 v0113 在「第一頁邏輯補缺正主橋二十六檢」站上 OK(站名待改,Z112)。格子再生 30 件 `git stash push -- <paths>` 收起不 commit(LL117 ③)。

## 五 · 你的手

1. **Z109**:探針落地三選一(①不落地 · ②落地 ENG089 改綁樞紐 · ③併 PR #23 原樣)。
2. **Z91**:改綁候 2(SUP_MDL015 · VRN_ENG062)/ 退役候 3(Extension v0224 · Q1_AliasRoutePatch · Compatibility v0222)/ 候 2(PDFTextLayerFallbackPlan · vrn_report_digest)——裁「改綁/退役」。
3. **Z82**:一句話登錄 cogs / opex / op_margin / net_margin / shares(全部或其中幾個)。
4. 先追哪顆(或「依你建議進行」:Z91 改綁 → Z82 → Z84/Z89 貼回 → Z88 封存)。

## 六 · 一貼即用

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
git log --oneline -1
git checkout -- "supportive modules/registry/VIA_VRN_LogicArchitecture_SSOT_v0100.json"
git fetch origin claude/vrn-line-b691; git checkout claude/vrn-line-b691; git log --oneline -1
via-fplogic --selftest
via-vrnrun
```

膠囊 b(工作站真跑探針;姊妹倉副本在 `C:\Users\tonyk\VIA-VDF-VRN` 或 `C:\Users\tonyk\Github\VIA-VDF-VRN`,先看哪個在):

```powershell
Set-Location 'C:\Users\tonyk\VIA-VDF-VRN'
git fetch origin claude/festive-ptolemy-ts2yyh; git checkout claude/festive-ptolemy-ts2yyh
python "functional modules\VRN\engine\VRN_PanoramaProbe.py" --incoming "C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics\functional modules\VRN\input\incoming" --vrn-root "C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics\functional modules\VRN" --html "$env:TEMP\vrn_panorama.html" --json "$env:TEMP\vrn_panorama.json"
```

貼回:`via-fplogic --selftest` 的 `[計]` 行與 ㉓ 行;`via-vrnrun` 的 SUP_MDL746 / CGC_MDL141 兩格 `[FAIL]` 行(Z84);探針的 `stage_summary` 十行(Z109 的料)。
