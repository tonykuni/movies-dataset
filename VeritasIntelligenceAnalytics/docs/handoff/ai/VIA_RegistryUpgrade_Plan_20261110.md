# 自動註冊 / 編號機制優化規劃 · 2026-11-10(待操作員排序;本檔不改任何冊)

操作員令:「優化自動註冊 LOG · REGISTER 成功的指令或更新的文件版本號註冊給號 · 檔名依規定並註記版本號 · 自動成功加強模組測試 ·
時間詳細到分鐘 · 同步優化所有編號機制 · 檔案大小 · 檔案格式 · HEADER 排列 · 自動編號註冊衝突重複檢測 · 主資料多矩陣顯示 ·
結合 Graphify / OmniRoute · 圖像 WORKFLOW · 編號功能今天算才嚴格啟用 · 取捨資料請小心」。

## 一、現況實測(VIA_NumberBooks,不含 FNC / CLS 細項冊)
| 項 | 實測 | 對應憲法 |
|---|---|---|
| 列數 | 20,117 | — |
| 時間 | 有時區到秒 17,482 · 無時區到秒 9 · 只到日 22 · 空 / 其他 2,604 | CONST-030 |
| 同碼多列 | 0 | CONST-008 |
| 同檔多碼 | 821(多為同檔不同種類:ENG + ENV 等,設計如此;要逐筆分「設計 / 真重號」) | CONST-007 |
| UUID · Operator · 檔案大小 · 格式 · sha256 欄 | **全為 0** | CONST-030(gap) |
| 稽核 | 遺失 0 · 改身分 0 · 重號 0 · IMMUT 0 · 撞號 0(CGC_MDL237 audit · registry-sync) | CONST-007 / 008 / 012 |
| 尾版有號覆蓋 | 3,588 支尾版中有號 2,225 · 空號 1,363(SystemCard G5) | CONST-007 |

## 二、取捨原則(「取捨資料請小心」)
1. **舊列一字不改**:2,635 列時間缺漏、821 同檔多碼、1,363 空號全部照實保留;只在新列加欄。
2. **嚴格啟用日 = 2026-11-10**:之後發的號,缺 UUID / Operator / 時間到分鐘(含時區)/ 大小 / 格式 / sha 的,視為不合格(黃)。之前的列不回溯判紅。
3. **新欄只增**:uuid · operator(AI 或操作員)· registered_at(YYYY-MM-DD HH:MM +00:00)· bytes · format(副檔名)· sha256 · header_order_ok。

## 三、分段計畫(每段一個新版號檔 + 自測 + 交接案 + 編號)
| 段 | 內容 | 落點(既有工具,不另起爐灶) |
|---|---|---|
| P1 | 註冊收據補欄(UUID · Operator · 分鐘時間 · bytes · format · sha256)· 只對新列 | CGC_MDL237 NumberingSystem 新版號薄尾 |
| P2 | 檔名規則閘:`<族>_v<NNNN>.<ext>`、版號只增、不撞同族;不合格不給號 | CGC_MDL237 + VIA_ConstitutionCheck v0101 |
| P3 | 衝突 / 重複檢測加強:同檔多碼逐筆分「設計 vs 真重號」· 同號異名(CONFLICT-00006)· 跨倉借號 | CGC_MDL237 audit 新版 + SystemCard numbers |
| P4 | HEADER 排列:號冊 / 輸出表頭固定欄序(code · version · registered_at · source · bytes · format · sha256 · uuid · operator) | VIA_Output_Header_SSOT 新版 |
| P5 | 主資料多矩陣:系統 × 種類 × 狀態 · 號 × 版 × 時間 · 缺號 × 尾版 | VIA_SystemCard 新版(Hub 頁)+ VisualSpecLock 視覺 |
| P6 | 圖像 WORKFLOW:註冊流程圖(改檔 → 自測 → 交接案 → 提交 → 給號 → 稽核 → 同步 → 串測 → 推送)| WorkflowViz v0100 + Graphify v0101(桌機) |
| P7 | 跨 AI 共用:同一組 MCP 給 Claude / ChatGPT / Gemini / Copilot 查號 | VIA_MCP_Engine v0103 parity + OmniRoute(桌機,未裝) |

建議先做 P1 → P2 → P3(都在 VCGC 自己的編號機制內,直接補 CONST-030 缺口);P4–P7 偏顯示與整合,排後。

## 四、進度(只增)
- **P1 完成 · 2026-11-10 17:26 +00:00** · `CGC_MDL237_NumberingSystem_v0120.py` = VIA-VCGC-MDL1637(ENV115)· 自測 20/20 · 前版鏈 v0119 PASS · 交接案 `C-cgc237-v0120-receipts` rc 0。
  - 收據帳 `supportive modules/registry/VIA_RegistrationReceipts_v0100.jsonl`(只增;不在號冊夾,號冊一字不動)。
  - 欄:code · book · version · source · registered_at(分鐘 + 時區)· uuid · operator · bytes · format · sha256 · kind(new / version / backfill)· engine · functions(函式子號併母號,不單發)。
  - `--apply` 成功後自動發;重跑零新增;同號同版異 sha 標 conflict 不蓋。`receipts` 檢查:嚴格啟用日起 581 列 · 收據 581 · 缺 0 · 欄不全 0 · 衝突 0 = GREEN。
  - 今天先前編號的 581 列以 `receipts --backfill --apply` 補收據(kind=backfill,時間取 numbered_at);2026-11-10 前的列不回溯。
- 下一段:P2 檔名規則閘 → P3 衝突 / 重複檢測加強。
- **P2 完成 · 2026-11-10 17:48 +00:00** · `CGC_MDL237_NumberingSystem_v0121.py` = VIA-VCGC-MDL1638 · 自測 19/19(前版 v0120 20/20)· 交接案 `C-cgc237-v0121-gate`。
  - 閘只管「本批要發號、還沒登過號的程式檔(.py / .ps1)」;已登號舊檔 · 冊 · 文件照前版(不回溯)。
  - N1 檔名 `<族>_v<NNNN>.<py|ps1>` · N2 同族同版已在樹上別處(參考 / 收件 / 報表 / 退役夾除外)= FAIL · N3 同夾同族已有更大版號 = HOLD(`--allow-gap <檔>` 明說補環)。
  - 擋下的檔不給號、其餘照發;全擋 rc 2 一列不寫。每個判定寫只增 LOG `supportive modules/registry/VIA_RegistrationGate_v0100.jsonl`(分鐘時間 · operator · 規則 · 原因)。`gate <檔…>` 只判不寫。
  - 首批實跑:3 支過閘 → MDL1638 · VDF MDL247(MDL008 v0108)· VDF ENG361(ENG238 v0101)· 收據 584/584 GREEN。
  - 同輪附帶:VCGC 衝突閘擋下 VDF 擷取冊 v0108 進編號範圍(子系統邊界,L123)→ 冊不由 VCGC 編號,只登程式檔。
- 下一段:P3 衝突 / 重複檢測加強(同檔多碼逐筆分「設計 vs 真重號」· 同號異名 · 跨倉借號)。
