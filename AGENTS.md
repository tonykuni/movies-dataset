# VIA 接手必讀(跨 AI 版:ChatGPT · Codex · 其他代理)

本檔是 `CLAUDE.md` 的精簡版,給 Claude 以外的 AI 讀。完整規則、原文與待裁定清單以 `CLAUDE.md` 與政策冊 `VIA_Policy_Laws_SSOT` 尾版為準;兩邊對不上時以那兩份為準,並回報差異。
操作員授權與當則指令優先;不從舊對話推定沒跑過的實測已成功。〔VCGC-REQ263〕

## 0 系統身分
- 五個獨立系統:VCGC · VDF · VRN · VQG · VAP。各由自己的 SystemManager 管理,各是自己的入口;互不改對方的正本、冊、號、檔,只讀對方自報的燈與收據。
- VRN = VRN-2 為主(`ActivateVRN-2.py` → `VRN_SystemManager` 尾版),VRN-1 是另一團隊的倉,只讀借用。只有談來源時才分寫 VRN-1 / VRN-2。
- SSOT 只有一套,權限分開:每個系統只寫自己的冊與夾。各系統以自己的代碼註冊(VIA-VCGC-* · VIA-VDF-* · VIA-VRN-* …);VRN、VDF 自己的帳本號由自己發(2026-11-21 裁定)。

## 1 每次接手先做(依序)
```bash
V=$(ls "VeritasIntelligenceAnalytics/supportive modules/registry/"CGC_MDL149_VeritasCentralGovernanceConsole_v*.py | sort -V | tail -1)
VIA_FROM_VCGC=YES python3 "$V" token > /tmp/token_card.txt 2>&1; cat /tmp/token_card.txt   # 省 Token 卡;紅就停
E=$(python3 -c "import json;print(json.load(open('VeritasIntelligenceAnalytics/supportive modules/registry/VIA_ToolVersion_Lock_v0100.json',encoding='utf-8'))['token']['path'])")
python3 "$E" tools; python3 "$E" delta          # 工具註冊清單 · 只看新增 / 已解的問題
VIA_FROM_VCGC=YES python3 "$V" handoff check    # 讀 HANDOFF_latest.json 的 findings · pending · reusable_successes;紅 / 黃先處理差異
VIA_FROM_VCGC=YES python3 "$V" functions        # AI 必用功能卡,照卡上的順序用
```
- 開工第一則回覆先列前一日教訓(`VeritasIntelligenceAnalytics/docs/handoff/daily/VIA_DailyChecklist_latest.md`,只列條目)。

## 2 讀檔(省 Token)
- 約 >200 行的檔、整個資料夾、日誌:`python3 "$E" read` → `slice <檔> <定義名>` → `digest <日誌>` · `pack <夾>` · 重讀加 `--if-etag`。長文用 NLP `--brief`(token 卡上有指令)。不整檔讀、不把原文貼回對話。
- 清單上有現成功能就用,不自己另寫;不夠用時先寫一行「缺口:要做什麼 · 最接近的動詞 · 差在哪」,再用通用方法,記黃。
- 沒看過的工具先 `read` 骨架,不下 `--help`(`CGC_MDL064_SelftestGrid` 下 `--help` 會跑整張格子並改檔)。

## 3 改程式
- 只增不減:出新版號檔(薄尾),前版一字不動;已鎖成功的來源不改。改薄尾家族前先 `python3 "$E" chain <家族名>`;動 SSOT / 正則 / 同義字 / 編號 / 註冊前後各跑一次 `VIA_FROM_VCGC=YES python3 "$V" ssot panorama`。
- 不同資料來源保留不同編號,不因數值相同就去重合併。
- AST 節點手術:`read` 定位 → `slice` 取出 → 在 TEMP 改好放回(`ast.parse` 與 `compile` 都過)→ 該檔 `--selftest` + `handoff test <case>`。只重測相依有變的 case;測試經該系統自己的 manager,保留命令 · rc · SHA · 日誌。
- 每支新 `.py` 帶既有加速器橋 `[VIA:ACCEL-BRIDGE]`;對外擷取的再帶網路工具橋;以語法樹真的匯入 + 執行時載得到才算。
- PowerShell 只進環境與呼叫 Python 入口;邏輯全寫在 Python。不改既有 `.ps1`。禁用 TA-Lib。新檔不含本機路徑。
- 刪舊版:三條都過才刪(`chain` 沒人載入 · 拿掉後尾版每個動詞實跑過 · 已鎖成功數不變);薄尾鏈上的前版不刪。

## 4 編號 · 註冊 · 推送
- 出新版號、發號、推送、開 PR 前:`python3 "$(ls VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_ReworkGuard_v*.py | sort -V | tail -1)" check --fetch-prs`;紅不推。
- 新需求先登 `VIA_Requirements_SSOT` 尾版(出新版號)與相應工作流冊;待辦帶 ID、原因、負責者、下一步,不能消失。
- 先提交再編號:`registry-sync --apply` → `run CGC_MDL237_NumberingSystem --apply --scope <檔…>` → `audit`(遺失 0 · 改身分 0 · 重號 0;XCODE / DUPREG 0)→ `sdd check`。避開開著的 PR 已用的號。
- 只推工作分支、開 PR;不合併 PR、不推 main。

## 5 環境 · 安全 · 資料邊界
- 安裝只走 `via-health` / `via-install`(VCGC 安裝閘);不直接 pip;AI 不刪環境(重建由操作員下 `via-envgov apply --approve`)。
- 同意閘(`VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT`)和金鑰不寫進任何檔、不代設到操作員環境;不印出秘密的值。
- 能離開本機的只有程式碼結構與 schema;市場資料、研報、庫內容不送任何外部模型或代理。
- HTML U/I 已視覺鎖定:顏色字體版面只取鎖定尾版,不改視覺值。

## 6 收尾與回報
- 範圍以當則訊息為準;範圍外看到的問題只記下回報,寫出「範圍外改動檔數」。
- 容器跑出來的結果最多黃,標「容器」;收尾成功 = 主機實跑 + 輸出驗證 + U/I 無誤 + `closeout_lamp` 與 SDD。交接 GREEN 只代表可續接;主機 DB、全樣本、OCR 沒測就留未完成,不拿單元測試冒充主機實測。
- 成功只增不減:收工時已鎖成功數變少 = 紅並點名。回報用稽核寫法(發現幾項、關了幾項、沒關的缺什麼證據),附命令 · rc · SHA。
- 收工 `via-vcgc handoff daily`;當天新問題照「問題 → 根因 → 處理 → 下次怎麼檢查」加到 `VIA_DailyLessons_Ledger_v0100.jsonl` 帳尾。

## 7 不能跑指令時(ChatGPT 網頁版等)
- 只讀、不推定:請操作員在桌機跑指令,貼回黃 / 紅精簡包(≤300 行、結尾帶 `NEXT:`),只依貼回的證據判斷。
- 給操作員的指令一律一行,走各系統入口的短指令(`via-vcgc` · `via-vdf` · `via-vrn`),先想清楚 Windows 路徑與目前分支;同一件事不給兩種打法。
- 不自己發號、不宣告收尾成功;要改檔就交新版號檔或差異,說明放哪、怎麼驗。

當前操作與交付說明:`VeritasIntelligenceAnalytics/docs/handoff/README.md`。交接機器判準的正主:`VIA_Handoff_Continuity_SSOT_v0100.json`(`CGC_MDL140_HandoverConsole` 經 VCGC 管理)。
