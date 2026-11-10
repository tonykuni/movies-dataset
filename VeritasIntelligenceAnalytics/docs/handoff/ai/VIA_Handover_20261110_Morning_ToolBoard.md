# 交接 · 2026-11-10 早 · 開工檢查備份 + VCGC 工具看板

操作員令:「檢查備份 · 讀取備份 · 並顯示 VCGC 有些功能工具 · 分類顯示 · 狀態燈號放一開始」。

## 1. 檢查備份(VIA_DailyBackup v0100 `check`)

| 項 | 值 |
|---|---|
| 燈 | **YELLOW** · 可開工 · 但:6 檔變了 / git 已前進 1acb6fd5 → cdfd81da |
| 備份時間 | 2026-11-09T15:57:02Z(9.8 小時前)· 6 系統 zip(VCGC 13 · VDF 17 · VRN2 59 · VQG 3 · VAP 6 · HANDOFF 262 = 360 檔) |
| zip | OK(SHA 全對) |
| 倉內檔 | 同 354 · 變 6 · 缺 0 |
| 變了的 6 檔 | Component_Inventory · Handoff_Continuity · Numbering_SSOT · FunctionLedger · DailyBackup v0100 本身 · evidence/vdf_ws_eng093_lists(全是昨晚備份後的閘鏈提交,預期) |
| 提醒(照舊) | Ponytail 未裝 · Graphify 收據不在本機 · 商業化 / 封裝 / 授權編號功能倉內沒有 |

黃 = 備份後倉又前進了,不是備份壞;今晚再 `backup` 一次即回綠。

## 2. 新引擎 `docs/handoff/ai/VIA_VCGCToolBoard_v0100.py`(只讀 · 零網路 · 不跑站 · 不發燈)

把 VCGC 自己落檔的收據攤成一張看板,**燈號放最前面**:

| 段 | 內容 |
|---|---|
| ① 燈號條 | 總燈(VCGC 自己收據取最差;互監另列不併入)+ 七盞:備份檢查 · 全功能串測 · 省 Token(V-token 站)· 流程閘 · 交接快照 · 五系統互監 · 工具鎖版席位;每盞帶時間 / 幾小時前 / 說明 / 來源檔;>48h = 過期(總燈至少黃) |
| ② 工具分類 × 最後一次串測燈 | 盤點冊 357 站依前綴分 10 類(V 動詞 · S 席位 · E 引擎 · I 整合 · L / L1 律 · P PowerShell · QG · SSOT · C 交接案);燈取 TEST_STATE 最後一次;沒跑過 = NOT_RUN(不算綠) |
| ③ 卡上的工具 | 鎖版席位 9(檔都在)· 省 Token 七工具 · AI 必用 13 步 · 門 14 · 禁止 9 · MCP 尾版 |
| 輸出 | `VIA_Reports/vcgc/TOOLBOARD_latest.{json,md,html}` + `toolboard_ledger.jsonl`(只增) |
| 自測 | 10/10(七盞 · 總燈規則 · 過期 · 分類 · 卡 · md/html 順序 · 落檔 + 只增帳 · 空樹 · --no-write · 邊界) |

### 2026-11-10 01:49Z 容器實跑

總燈 **YELLOW**(過期:gate · handoff)

| 燈 | 項 | 幾小時前 | 說明 |
|---|---|---|---|
| YELLOW | 備份檢查 | 0.1 | 可開工 · 6 檔變了 |
| YELLOW | 全功能串測 | 8.8 | quick · 站 11(綠 9 黃 2 紅 0)· head 958efbc |
| GREEN | 省 Token 工具 | 8.8 | V-token rc 0 · 交接證據 2026-11-06 rc 0 |
| GREEN(過期) | 流程閘 | 62 | gate-20261107 · blockers 0 → 桌機 `enter` 會重寫 |
| GREEN(過期) | 交接快照 | 917 | HANDOFF_latest 2026-10-02 · closeout YELLOW · pending 104 → `handoff checkpoint` 自 10-02 沒再寫(交接閘基線 RED 擋住) |
| RED | 五系統互監 | 9.8 | VCGC Y · VDF R · VRN2 R · VQG Y · VAP GRAY(他系統自報 · 只看不代修) |
| GREEN | 工具鎖版席位 | — | 9 席位正主檔都在 |

工具分類(357 站 · 沒跑過 38):

| 類 | 站 | 綠 | 黃 | 紅 | 沒跑過 | 類燈 |
|---|---|---|---|---|---|---|
| V 動詞 | 49 | 27 | 12 | 4 | 6 | RED(V-layout 無 PyMuPDF · V-probe / V-systems 還原點無紀錄 · V-gate) |
| S 席位 | 3 | 2 | 0 | 1 | 0 | RED(S-nlp 容器缺 NLP 套件) |
| E 引擎 | 12 | 6 | 1 | 0 | 5 | NOT_RUN |
| I 整合 | 10 | 10 | 0 | 0 | 0 | GREEN |
| L 律 | 7 | 7 | 0 | 0 | 0 | GREEN |
| L1 律 | 2 | 1 | 0 | 1 | 0 | RED |
| P PowerShell | 7 | 5 | 1 | 0 | 1 | NOT_RUN(容器無 pwsh) |
| QG | 5 | 5 | 0 | 0 | 0 | GREEN |
| SSOT | 2 | 1 | 1 | 0 | 0 | YELLOW |
| C 交接案 | 260 | 189 | 0 | 45 | 26 | RED(紅 45 多為容器環境:yfinance / fastparquet / PyMuPDF / NLP 套件;分類見 VCGC_ToolMatrix_20261106 §6) |

紅站是「最後一次跑」的歷史燈(多為 11-06 `test --full`),不是今天重跑;看板只攤開不代修。

## 3. 登冊(add-only)

| 冊 | 版 | 變 |
|---|---|---|
| 盤點 | v0214 → **v0215** | +站 `C-vcgc-toolboard`(自測 10 項)· coverage.case · WKF036 三步(STP001 由 C-daily-backup 代驗 · STP003 桌機看頁 exempt) |
| 需求 | v0238 → **v0239** | +`VCGC-REQ213` 工具看板(COVERED)|
| 工作流 VCGC | v0139 → **v0140** | +`VCGC-WKF036` morning_toolboard(check → run → open);**SDD X-COL 補齊** WKF032–036 tests(self / cross / real)· 每步 what · evidence 改 `self:` / `step:` 形式(原檔路徑移 evidence_file)· WKF030 / 031 STP003 同 |
| 交接冊 | v0100(活冊) | +案 `C-vcgc-toolboard`(timeout 300)· 工作項 REQ213 VERIFIED(handoff test rc 0 · marker true) |

SDD `sdd` 後:VCGC 冊 X-COL 0;剩 VDF-WKF016 / 017 · VRN-WKF010 三條(他系統冊,VCGC 不代改)。

## 4. 閘鏈實錄

| 步 | 結果 |
|---|---|
| handoff test C-vcgc-toolboard | rc 0 · marker true → `docs/handoff/evidence/C-vcgc-toolboard.json` |
| 提交 | 1449a5382 |
| CGC_MDL237 --apply --scope(5 檔:引擎 · 工作流 v0140 · 需求 v0239 · 盤點 v0215 · 政策 v0116) | +683 列(含 WKF / STP / REQ 補號;SDD X-NUM 昨列 59 個) |
| audit | 遺失 0 · 改身分 0 · 重號 0 · IMMUT 0 · DUPREG 0 · **冊內不一致紅列 54(基線:冊上宣告碼 ≠ 發出號 · 不改任何一邊)**→ YELLOW |
| registry-sync --apply | 撞號 0 · 改發 0 · 時間欄補 UTC 59 |
| test --quick | (見下)|
| handoff check | (見下)|

## 5. 明天開工一指令

```bash
cd VeritasIntelligenceAnalytics
python3 "docs/handoff/ai/VIA_DailyBackup_v0100.py" check && python3 "docs/handoff/ai/VIA_VCGCToolBoard_v0100.py" run --open
```

今晚收尾:`python3 "docs/handoff/ai/VIA_DailyBackup_v0100.py" backup`(隔天 check 才會綠)。

## 6. 誰的手

- 桌機:`enter`(重寫 GATE_latest)· `handoff checkpoint`(交接閘基線 RED 需先清 VRN 車道舊紅)· Ponytail · NON_STOCK_CORE 上傳 · FRED 鑰 · 三個 Gemini 連結文字。
- VDF / VRN 冊 X-COL 三條:各系統自己的冊,VCGC 不代改。
- MCP 多露 `vcgc/toolboard`:下一版 MCPServer v0103(今天沒做,避免再開一輪閘鏈)。

## 7. 第二輪(操作員「全部完工了嗎?五系統一庫 Parquet 增量 · DuckDB 管理 · 工具活動報告矩陣 · 啟動測 / 使用者測到完善 · 跳 HTML U/I」)

| 件 | 結果 |
|---|---|
| `supportive modules/VIA_ParquetLake_v0100.py`(五系統共用套件) | 一系統一湖:`<root>/<SYS>/<table>/part-<UTC>-<sha8>.parquet`(zstd · 原子換名)+ `_manifest.jsonl` 只增 + `<SYS>_catalog.duckdb` 一表一 VIEW(主鍵去重最新勝);同主鍵增量跳過;五系統名閘;自測 **10/10** |
| `docs/handoff/ai/VIA_LakeMatrix_v0100.py`(VCGC) | ① VCGC 七帳本入湖(function_ledger 839 · test_state 332 · backup_manifest 6 · toolboard 3 · mutual 2 · closeout 2 · gate 2;再跑 0 新入)② 五系統只讀盤點(湖 / 既有 duckdb · parquet;壞檔照實)③ 工具活動報告矩陣(事件 × 日 · 七日類別 book 106 family 11 verb 1 · 最活躍站 · 五系統 × 日)④ HTML U/I:燈號最前 · 系統鈕 · 搜尋 · 只看有資料 · 重設;自測 **12/12** |
| 實跑燈 | 總燈 **YELLOW**:VCGC GREEN(湖在 7 表)· VDF YELLOW(尚未入湖 · 既有 8 組 25,839 列)· VRN-2 YELLOW(3 組 1,258 列)· VQG YELLOW(12 組 4,800 列)· VAP YELLOW(1 組 7,234 列 · 2026-05 快照) |
| 使用者測試 | Playwright 1440 / 900 / 390 × 17 步 = **51 步 0 失敗 0 pageerror**(第一輪手機橫向溢出 533 > 390 → header meta `min-width:0` + `overflow-wrap:anywhere` → 第二輪綠)→ `VIA_Reports/lake/UI_UserTest_latest.{json,md}` + 三張截圖 |
| 湖根 | 容器無桌機資料家 → `VIA_Reports/lake`(來源照實標);桌機設 `VIA_DATA_HOME=…\via_database` 後自動讀真家 |
| 登冊 | 盤點 **v0216**(+C-parquet-lake · C-lake-matrix · WKF037 四步)· 需求 **v0240**(+VCGC-REQ214 **PARTIAL**)· 工作流 **v0141**(+WKF037 five_system_lake · tests / what / evidence 齊)· 交接冊 +2 案 + 操作員項 systems-adopt-lake OPEN |

**誠實邊界(L123)**:VCGC 不代建、不代寫他系統的湖。套件已給,VDF / VRN-2 / VQG / VAP 把既有 duckdb / parquet `append` 進自己的 `<VIA_DATA_HOME>/<SYS>` 是各系統的手;接上後矩陣燈自動轉綠。所以 REQ214 是 PARTIAL,不寫成完工。

## 8. 第三輪(操作員「實測自設自修正輸出 · 輸出見證 · HTML U/I 可操作 · 高自動化高整合 · 只有必要項目才用輸入 · 滑鼠動作:Windows I/O · 拖曳 · 下拉 · 勾選」)

| 件 | 結果 |
|---|---|
| `docs/handoff/ai/VIA_LakeConsole_v0100.py`(VCGC 本機橋操作台) | 只綁 127.0.0.1(預設隨機埠 · 桌機可 `--port 8766`)· 頁面注入當次權杖 · 副作用 POST 要同源 Origin + Sec-Fetch-Site + X-VIA-CSRF · 嚴格 JSON body · 白名單動作(檢查備份 · 工具看板 · 資料湖矩陣 · 四支自測 · 自修正鏈 · 全部自測鏈)· 子行程跑倉內尾版(單通道 · log 落盤)· 見證面板(每步 rc · 秒 · 收據連結 · 輸出尾段 · 燈)· 入湖:拖曳 / 選檔案 / 選資料夾(webkitdirectory)→ 預覽(格式 · 列 · 欄)→ 下拉表名 · 勾主鍵 · 勾增量 → VCGC 湖;他系統 → `_inbox/<SYS>`(L123 不代寫)· `/files` 只供 VIA_Reports 與湖根 |
| 自測(真橋) | **17/17**:403 / 400 / 202 / rc 127 RED / 入湖 3 列 · 再入 0 / _inbox / `..` 擋 / 燈轉綠 / 邊界 |
| 使用者測試(滑鼠) | Playwright 1440 / 900 / 390 × 13 步 = **39 步 0 失敗 0 pageerror**:下拉選套件自測 → 勾只看不寫 → 執行 → GREEN;下拉選資料湖矩陣 → 執行 → 收據連結;拖曳兩檔 → 預覽 2 檔 3 欄主鍵預勾 → 入湖 VCGC 新入;選檔案 → VDF → _inbox;選資料夾 → 預覽;頁內無權杖 POST 403;非白名單 400 → `VIA_Reports/lake/CONSOLE_UserTest_latest.{json,md}` + `console_shot_{pc,tablet,phone}.png` |
| 自測抓到並修的真 bug | ① 混型來源(jsonl 的 `3` vs csv 的 `"3"`)入同表 → pyarrow 炸 → 套件 `_arrow_from_rows` 逐欄推型、字串退路(跨分片 DuckDB union_by_name 升 VARCHAR 實測)· 套件自測 10 → **11**;② 處理器例外默默斷線 → 一律 JSON 500(見證要看得到錯);③ 容器 HTTPS_PROXY 會攔 127.0.0.1 → 自測用無代理 opener |
| 登冊 | 盤點 **v0217**(+C-lake-console · WKF038 三步)· 需求 **v0241**(+VCGC-REQ215 COVERED)· 工作流 **v0142**(+WKF038 lake_console)· 交接冊 +1 案 |
| 桌機開法 | `python3 "docs/handoff/ai/VIA_LakeConsole_v0100.py" serve`(操作員 2026-11-10「啟動後自動跳出 HTML U/I」→ 預設即開瀏覽器;`--no-open` 給 CI / 背景;之後可掛進 CGC_MDL095 DeckServer 當 `/lake` 路由,同一套權杖律) |

## 9. Codex PR #623 兩項 P2 → `VIA_LakeMatrix_v0101`(薄尾 · v0100 已在 main 不動)

| 發現 | 修法 | 驗證 |
|---|---|---|
| 五系統 × 日 只拿每表 first / last 兩個時間點:中間日漏算、單分片算兩次 | 逐分片:每個 `part-<UTC>-<sha8>.parquet` 檔名戳一片一計;既有資產照舊以檔案更新日計 | 自測 ⓑ 三天三片 → 1 / 1 / 2;實跑 VCGC 11-07 3 · 11-10 10 |
| 一表好一表壞仍 GREEN,壞表不出現在報表 | 任何壞表非綠(部分 YELLOW · 全壞 RED),說明點名,壞表列進資產明細(類 `lake(壞)` · 狀態 錯:…) | 自測 ⓐ YELLOW + 明細列 · ⓒ md / html 有壞表 · ⓓ 全壞 RED |

本版 4/4 + 前版鏈 12/12。登冊:盤點 v0218(+C-lake-matrix-v0101 · WKF037-STP002 → v0101)· 需求 v0242(REQ214 evidence)· 工作流 v0143 · 交接案。操作台 `VIA_LakeConsole` 的動作 glob `VIA_LakeMatrix_v*.py` 自動選到 v0101。

## 10. Codex PR #624 三項(P1 ×1 · P2 ×2)

| 發現 | 修法 | 驗證 |
|---|---|---|
| **P1** 套件 `VIA_ParquetLake_v0100` 已在 main(PR #623)卻被就地改(混型推型 · 微秒戳)→ 違反 AGENTS L10 add-only | v0100 還原成 main 版本一字不動;新行為出 **`VIA_ParquetLake_v0101`**;消費者改取尾版 glob:`VIA_LakeMatrix_v0101`(覆寫 `_lake_module`)· `VIA_LakeConsole`(本來就 glob)| v0100 10/10 · v0101 11/11 · 矩陣 v0101 4/4 + 鏈 · 操作台 19/19 |
| P2 `_inbox` 同名檔(`a/data.csv` · `b/data.csv` 同秒)互相覆蓋 | 目的檔 = `<微秒戳>-<內容 sha8>-<路徑消毒>`,`open("xb")` 絕不覆蓋,同名加序號;清單記來源路徑 | 自測 ⓜ2:同名不同夾 + 同檔再送 → 三個不同檔都在 |
| P2 見證燈只看 rc(引擎自報 YELLOW 仍 GREEN) | `step_lamp()`:本輪收據 JSON 的 lamp > stdout 首個 `[GREEN|YELLOW|RED|GRAY|PASS|FAIL]` > rc;行程失敗不可能綠 / 黃;整件 = 各步最差 | 自測 ⓗ:rc 0 + 收據 YELLOW → 步 YELLOW · 整件 YELLOW;ⓗ2 `[PASS]` → GREEN |

登冊:盤點 v0219(+C-parquet-lake-v0101 · C-parquet-lake 回 10 項 · C-lake-console 19 項 · WKF037-STP001 → v0101)· 需求 v0243 · 工作流 v0144 · 交接冊。操作台使用者測試重跑(新碼 · 埠 8767):Playwright 三視窗 **39 步 0 失敗 0 pageerror · GREEN**(2026-11-10T03:19:56Z · `VIA_Reports/lake/CONSOLE_UserTest_latest.{json,md}`;下拉自測 → 矩陣真跑收據連結 → 拖曳兩檔預覽 / 勾主鍵 / 入湖 VCGC → 選檔 VDF 落 `_inbox` → 選資料夾 → 無權杖 403 / 非白名單 400)。三串 Codex 已回覆並 resolve(8cf4d1b94);編號冊 +23 已提交(fa50dbae4)。

閘鏈第 16 輪(修後):`test --quick` **YELLOW**(站 9 綠 2 黃 0 紅 · case 267/267 · workflow 164/164 · 紀錄 +3)。`handoff check` **RED 143 → 141**:本輪兩項已清(C-vcgc-toolboard 收據重生,因 seat_path 修在收據之後;REQ214 systems-adopt-lake OPEN 不是合法態 → PENDING)。
**更正**:前幾輪交接文件寫的「handoff check 16 紅」是擷取只留尾 18 行的誤記;真實基線是 11-09 的 139 紅(EVIDENCE_INVALID 52 全為 11-06 席位冊 `VIA_VCGC_SubsystemSeat_v0100` 變更後的連鎖:chain / backup / numbering 等舊收據失效 → 其相依模組落成 CHANGED_CODE_WITHOUT_TEST 81),不是本輪新紅;要清要在桌機 `handoff test chain` / `backup` / `numbering` 重跑舊案後 `handoff checkpoint`。新案(lake · console · parquet v0101 · toolboard)紅 0。

## 11. 五系統啟動 via HTML U/I(操作員「PR 已合併 繼續併回 main 收尾 activate 5 system via html u/i and run」)

PR #624 已併入 main(04:00Z),分支併回(7598b4146)。新引擎 **`docs/handoff/ai/VIA_LakeConsole_v0101.py`**(v0100 薄尾,v0100 一字不動):

| 項 | 內容 |
|---|---|
| 白名單 +6 | `five_systems`(= `VIA_FiveSystemConstitution run --apply`:VCGC · VDF · VRN-2 · VQG · VAP 各走自己的入口並行實測 · 記進度帳 · 矩陣)· `activate_vcgc / vdf / vrn2 / vqg / vap`(單系統走它自己的入口 selftest)· 鏈 `activate_all`(逐一)。VRN-1 外部倉只讀,不在白名單(L123) |
| 燈 +6 盞 | 五系統總燈(憲法矩陣)+ 每系統一盞:實測燈 · 入口版 · 號 · 憲法性 · 進度(綠 / 跑 · 連綠)· 本台啟動比矩陣新就改用本台 |
| 頁面 | 「五系統啟動」按鈕列 7 顆(一鍵 = 下拉選好 + 執行;純滑鼠)· 仍是同一支 script · 見證表每步燈改用引擎自報 step lamp |
| 收據 | 矩陣正本仍在 `docs/handoff/ai/VIA_FiveSystemConstitution_{latest.json,latest.md,UI.html}`;本台把本輪新產的複製到 `VIA_Reports/lake/FIVE_SYSTEMS_latest.*` 給 `/files` 開;只看不寫 → 去 `--apply` 不記進度帳、不拿舊收據的燈 |
| 子行程 | 逾時依動作(五系統 1800 · VCGC 1500 · VDF / VRN-2 / VQG 900 · VAP 600)· `VIA_FROM_VCGC=YES` · 帳每步帶燈 |

**自測** 本版 11/11 + 前版鏈 v0100 19/19(前版鏈改走乾淨子行程:行程內 v0100 的 ACTIONS / lamps 已被換成五系統版)。
**容器實跑**(`serve --port 8768 --no-open`)· Playwright 三視窗 **31 步 0 失敗 0 pageerror · GREEN**(`VIA_Reports/lake/CONSOLE_UserTest_v0101_latest.{json,md}` + 三張截圖):燈 10 盞 → 按「五系統並行實測 + 矩陣」→ DONE 172.6s + 收據可開 → 按「啟動 VAP」「啟動 VRN-2」→ DONE GREEN → 系統盞改用本台 → 403 / 400。
**五系統各走自己入口 5/5 綠**:VCGC v0192 47.4s · VDF v0168 159.6s · VRN-2 v0262 6.9s · VQG v0109 170.0s · VAP v0100 0.1s;進度帳 +5(`VIA_FiveSystem_Progress_v0100.jsonl` 25 列)。
**誠實**:矩陣總燈 **RED** 不是實跑紅,是憲法性基線(11-09 已知):衝突冊 OPEN 6 項點到 VCGC / VDF / VRN-2(`CONFLICT_OPEN`)· VQG / VAP 未登 L122 治理冊(`NOT_IN_L122_GOVERNOR`)→ 憲法性 0/5;裁衝突 / 登治理冊是操作員的手。見證面板照實顯示 RED rc 1。

登冊:盤點 **v0220**(+C-lake-console-v0101;WKF038-STP001 → v0101;+WKF039 覆蓋)· 需求 **v0244**(+VCGC-REQ216 COVERED)· 工作流 **v0145**(+VCGC-WKF039 five_system_activate)· 交接冊 +1 案 VERIFIED(handoff test rc 0 · marker)。編號 +23(遺失 0 · 改身分 0 · 重號 0 · IMMUT 0 · DUPREG 0)· registry-sync 撞號 0。
桌機:`python3 "docs/handoff/ai/VIA_LakeConsole_v0101.py" serve`(自動開頁)→ 按「五系統並行實測 + 矩陣」。

## 12. VQG 產出進 TEMP 增量 Parquet 庫(操作員「VQG 產出的數據到 TEMP 存放 增量更新去重維護 用 PARQUET 一樣 刪除機制未定 先維持現況」)

`functional modules/VQG/VQG_AllInOne_v0110.py`(v0109 薄尾 · v0109 一字不動 · SHA 釘住)。儲存用五系統共用套件 `supportive modules/VIA_ParquetLake_v0101.py`(main 上;Parquet zstd 分片 · `_manifest.jsonl` 只增 · DuckDB `VQG_catalog.duckdb` 每表一個 VIEW 取最新)。

| 項 | 內容 |
|---|---|
| 位置 | TEMP 根 = `VIA_TEMP_ROOT` > Windows `%LOCALAPPDATA%\VIA_TEMP` > 系統 temp/VIA_TEMP(同 VDF ActivateVDF)→ `<TEMP 根>/VIA_Lake/VQG/`;`VIA_VQG_STORE_ROOT` 或 `--store-root` 可換 |
| 九表與去重鍵 | series(ticker, date)· indicators(ticker, observation_date)· indicator_results(ticker, observation_date, indicator_id, window_n, solution_id)· quant_analysis(ticker, observation_date)· backtest_curve(ticker, date)· backtest_summary(ticker, strategy)· factor_ic(date)· stats(ticker)· return_corr(ticker);另 store_runs 每次一列 |
| 去重 | 每列內容指紋 `vqg_row_sha`:新鍵 → 新增;同鍵同值 → 跳過;同鍵值變 → 追加新版本(VIEW 取最新,舊版本留在舊分片)。as_of · request_key · input_sha256 · engine_version · engine · formula_engine · link_id · source_files 每輪會變,不算進指紋 |
| 刪除 | 不刪(機制未定 · 維持現況);入庫程式碼沒有任何刪除呼叫(自測 ⑩ 以 AST 檢查) |
| 接法 | `export-vap` 跑完自動入庫(`--no-store` 不入);`store [--export-dir D]` 單獨入庫;`store status` 看各表原始列 / 鍵數 / 分片 |

驗證(容器):自測本版 11/11 + 前版鏈 v0109 14/14 · CLI 實跑 4 票夾具:第一次入庫 2543 列 · 同一匯出再入 0 新增 · 第二次匯出(新夾 · 同資料)0 新增 0 更新 · 值變 1 列 → 新版本 1 · 新一天 → 新增 1。

**注意**:REQ214 原定湖根是 `<VIA_DATA_HOME>/<SYS>`;VQG 依本令改放 TEMP,所以五系統湖矩陣(LakeMatrix)預設看不到 VQG 這座湖。要讓矩陣看到,把 `VIA_VQG_STORE_ROOT` 指到資料家目錄即可。系統暫存清理工具若清 TEMP,庫會跟著消失;刪除與保留機制待操作員決定。

登冊:需求 v0244 +`VCGC-REQ218` COVERED · 工作流 v0145 +`VCGC-WKF040` vqg_temp_store(3 步)· 盤點 v0220 +C-vqg-v0110 · 交接冊 +case + work item VERIFIED。
桌機:`python "functional modules/VQG/VQG_AllInOne_v0110.py" export-vap --root <VDF 庫>` → `... store status`。
