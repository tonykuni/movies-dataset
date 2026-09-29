# 側線 2026-09-29 a:省 Token 工具經 VCGC 啟用 · 成為 VCGC 第一步 · 要求 AI 先用

主線批號由併線的手指定(L25)。本批接在 PR #365(0cebb651)之後。

## 一、操作員令(原文)

- 「token saving tools registered. activate them and request ai to utilize them as the first step in vcgc.」

## 二、實量到的缺口(先量再改)

| 量到的 | 位置 |
|---|---|
| 省 Token 排**第二步**(1 入口 · 2 省Token),而且只「嗅」全景檔裡有沒有 `"read"` 這幾個字——字在 ≠ 工具能用 | CGC_MDL226 v0100 `token_tools()` |
| 省 Token 工具**沒進鎖冊**、不經啟用檢查:哪一版在用還是「尾版律取最新檔」 | CGC_MDL233 v0101 只管加速器 · 網路 · LAYOUT · NLP |
| 引擎版號冊沒有全景的列(啟用檢查「冊上已登錄」過不了) | VIA_EngineVersion_Register_v0100.json |
| **沒有一句話叫 AI 先用** | 整條 VCGC |
| 步驟門只擋「走得到 v0161 的動詞」;`tools` / `run` / `go` / `events` / `workflow` / `sdd` 由 v0163–v0169 直接接走,從沒過步驟門 | VCGC v0161(DOOR 還字串釘 v0100) |

## 三、改了什麼

| 件 | 做什麼 |
|---|---|
| 引擎版號冊 +1 列 | `VIA-TOOL-0194` token / engine / CGC_MDL158_VIAPanoramaAuditRepair_v0116.py(LL334:全 241 條分支最大 0193) |
| **CGC_MDL233 v0102** | 第五家 `token`(全景;必備 API pack_payload · digest_log · main · selftest),檢查照 v0100 原樣;自測 ⑭–⑰ |
| **經 VCGC 啟用** | `via-vcgc tools activate token CGC_MDL158_VIAPanoramaAuditRepair_v0116.py --apply` → 鎖冊 `VIA_ToolVersion_Lock_v0100.json` 多一格 `token`(v0116 · sha 5d5216aa…) |
| **CGC_MDL226 v0101** | 次序 `token → enter → accel_net → policy → number → ps_template → env → subsystem`(一步不刪,只把 token 提到最前);啟用 = 鎖冊說了算(pinned token / nlp 位元吻合,CRLF 容忍);**實測**六件 read · slice · digest · pack · `--if-etag`(要回 304)· NLP `--brief`(樣本在暫存夾);同一組位元只測一次(快取 `VIA_Reports/vcgc/token_activation_latest.json`,沒過的不快取);卡上 `ai_directive`(指令原樣可貼 · 什麼時候不用)與 `ai_line`(短版);自測十檢 |
| **VCGC v0170** | 進門之後、任何動詞之前先跑第一步,**第一行印 ai_line**(`--json` 時走 stderr,stdout 保持純 JSON);紅就停在第一步(不讀政策、不開子系統,印啟用短令,rc2);新動詞 `token` 印整張卡(事件照 v0168 記);v0161 的 DOOR 改指步驟矩陣尾版、它寫死的舊次序那一行換成新次序的實際燈號;自測七檢後串前一版(整條鏈 11 秒全過) |
| **政策小冊 TOKEN-1** | `VIA_Policy_TokenFirst_v0100.json`(照 FLOW-1 的做法另開小冊,不改鎖住的法冊);步驟矩陣自測 ⑩ 核對兩邊一字不差 |
| **CLAUDE.md** | 開頭加「第一步」:`VIA_FROM_VCGC=YES python3 <VCGC 尾版> token`,照卡讀檔;全景路徑改取鎖冊的 `token.path`(不再自己取尾版) |
| **CGC_MDL187 v0102**(擊斃閘) | ①新版檔沿襲**已進線**前一版逐字相同的禁行 → 記債不擊斃;同一行多一份照殺;前一版是這一批新造的不算(防洗白)。v0101 會把每一次升版裡原有的**偵測器**字面(查同意閘有沒有被代設的比對字串)當新增行擊斃。②**薄尾委派前版自測**(本批 S4 實判咬到:VCGC v0170 · CGC_MDL233 v0102 被判 KILL-10「刪掉檢號」):新版 selftest() 真的呼叫 `PRIOR.selftest()`(AST 認碼)→ 前版檢號照跑,記債不擊斃;沒串 / 只在說明文字 / 已進 HEAD 自刪 照殺。自測 27 檢,突變 7/7 全抓 |
| **格子 v0499** | +2 站(步驟矩陣十檢 · 工具啟用閘五家);站名檢數 擊斃閘 廿五 → 廿七(LL213 只換數字) |

## 四、AI 怎麼用(卡上原文,鎖版變了卡跟著變)

```
[第一步 · 省Token] 已啟用 6/6(鎖版 v0116 · NLP v0105)· AI 先用:read → slice → digest · --if-etag 免重讀 · pack 整夾 · --brief 長文
```

- 大檔(約 >200 行)或整夾 → `read`(骨架卡)· 要看內文 → `slice <檔> <定義名>` · 跑測日誌 → `digest`(紅日誌誠實回 rc1)
- 同一支再讀 → 加 `--if-etag <上一張卡的 etag>`,回 304 = 沒變 · 整夾索引 → `pack` · 長文 → NLP `text --file <檔> --brief`
- 不用的時候:原檔比卡片小(約 40 行內)直接看;不把原文貼回對話
- 工具換版只經 `via-vcgc tools activate token <檔> --apply`

## 五、驗證

| 項 | 結果 |
|---|---|
| CGC_MDL233 v0102 自測 | v0100/v0101 前鏈全過 + 新 4/4(五家 · token 過全部檢查 · 家別不對擋下 · 已啟用位元吻合) |
| CGC_MDL226 v0101 自測 | 10/10(首測 2.3s、快取 0.5s;負控:沒啟用六件全紅、假全景六件全 ✗、多一個位元 sha 對不上;真快取與真鎖冊零足跡) |
| VCGC v0170 自測 | 7/7 + 串前一版整條鏈全過(11s);真事件夾零足跡 |
| CGC_MDL187 v0102 自測 | 27/27 · 突變 7/7 |
| 格子 v0499 | 自測 8/8;`--only` 步驟矩陣 · 工具啟用閘 · 擊斃閘 · VCGC 控管台 四站全綠(擊斃閘加 ㉗ 後重跑),沒重寫任何已追蹤檔 |
| 端到端 | `via-vcgc token` 印整張卡(快取 0.74s);`via-vcgc help` 第一行 = ai_line、第二行 = `[步驟] 1 省Token GREEN · 2 入口 GREEN · 3 加速器與網路 GREEN` |

## 六、教訓(照實記)

- **嗅字串不是啟用**:v0100 看到 `"read"` 就綠;工具真的壞了也綠。第一步改成真跑、認判讀記號,同位元快取省時間。
- **門只擋走得到它的動詞**:新動詞一路加在上層薄尾,就一路繞過下層的門。要「每個動作的第一步」,只能放在最上層。
- **量測本身會留痕**:用 `| head` 截 VCGC 輸出,BrokenPipe 被 v0168 記成 VCGC 失敗寫進已追蹤的教訓帳(VF-028/029)——已按檔名還原;CLAUDE.md 改成導到檔案再看。
- **撞號要先掃**:本批原本在舊基底上做的 B+C(交接紀錄 · 入口探針 · 三輪沙盒 · 工作流編號)在主線前進 613 個提交後,版號與引擎號(MDL189 已是 GitHubSyncEngine)全撞;工作流三系統編號主線已由 R33 做完(VIA_Workflow_<子系統>_SSOT + CGC_MDL237 WKF/STP/REQ + CGC_MDL245),**不移植,免得兩套編號**(九頭龍)。舊成果只留在工作階段備份,不入倉。

## 七、還原

- 碼:刪本批新檔(CGC_MDL149 v0170 · CGC_MDL226 v0101 · CGC_MDL233 v0102 · CGC_MDL187 v0102 · CGC_MDL064 v0499)即回到尾版律的前一版。
- 啟用:`git restore --source=0cebb651 -- "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_ToolVersion_Lock_v0100.json"`(鎖冊的 `token` 格拿掉,步驟矩陣第一步就會紅並印啟用短令)。
