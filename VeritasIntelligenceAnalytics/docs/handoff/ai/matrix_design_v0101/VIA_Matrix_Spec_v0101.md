# VIA 多矩陣治理設計 v0101

設計更新：2026-11-07，Asia/Taipei。範圍：VCGC、VDF、VRN、VQG、VAP；VSW 為支援工具分類，VSC/VRS 可循同一契約擴充。這是治理介面、證據契約及導入設計，並非 Windows 已完成注入的證明。附帶 HTML 為可互動離線設計原型；預設示例與匯入觀察分開，不寫入引擎。

## 1. 繼承與修正

已核對前版 VIA_MultiMatrix_UI_Design_v0100.html、VIA_SystemIntegration_README(1).md、VIA_AgentOS_VCGC_README_v0300.md 及其 QA。保留三行 Header、理字標誌、綠金色、緊湊矩陣、系統自治、來源可追溯。前版提到的外部工具 NOT_CONNECTED、Windows 未測及 Parquet 驗收缺口，不會因改版介面就消失。

前版的 1 MiB／400 檔掃描限制不足以證明全樹覆蓋；新設計要求完整清冊、逐分片處理與明確錯誤列。前版掃描器只有 definitions 名稱清單、橋接字串及靜態呼叫候選，尚不足以產生已驗證 AST 級注入結論。此次原型可讀該清冊，缺少的節點、行號、正式編號、更新時間與測試證據仍顯示待採集。

## 2. 全站結構：14 個互相關聯的矩陣

| 編號 | 矩陣 | 每列單位 | 展開或連結 |
|---|---|---|---|
| M00 | 系統總覽 | 一個系統 | 大類 → 家族／引擎 → 明細矩陣 |
| M01 | 檔案與 AST 主矩陣 | 一個來源檔的版本 | 檔案 → class/def/PS function → 語句／呼叫／分支 |
| M02 | 加速與網路覆蓋 | 一個檔案或能力需求 | 要求 → 接線／載入 → 受治理呼叫與執行證據 |
| M03 | 輸入契約 | 一個資料來源／資料集版本 | 大類 → 資料集 → 欄位與樣本 |
| M04 | 輸出契約 | 一個產物或資料集版本 | 大類 → 產物 → schema／品質／血緣 |
| M05 | 參數與時間 | 一個具型別的參數 | 大類 → 參數組 → 實際解析值／來源／限制 |
| M06 | VQG 指標 | 一個指標定義版本 | 類別 → 指標 → 公式、視窗、單位及測試 |
| M07 | VAP 圖形 | 一個圖形模板版本 | 圖類 → 模板 → 資料綁定／樣式／互動／匯出 |
| M08 | SSOT 與依賴 | 一條契約或依賴邊 | 來源擁有者 → 規則／上下游 → 影響集合 |
| M09 | 測試與驗證 | 一個被測實體及其版本指紋 | U/I/S/R/C 階段 → 測試案例 → 收據／斷言 |
| M10 | 錯誤與衝突 | 一個有去重鍵的問題 | 根因 → 受影響 AST／產物 → 複核證據 |
| M11 | 全景修正 | 一個修正批次／patch | 第一輪發現 → 第二輪修復 → 第三輪回歸 |
| M12 | 執行與效能 | 一次 run 的步驟 | 階段 → 工作 → CPU/RAM/I/O/Token 指標 |
| M13 | 版本與稽核 | 一次不可覆寫事件或快照 | 實體 → 版史 → 差異／失效／回滾證據 |

各矩陣共用前四欄：燈號、編號、名稱含版本、更新日期。不能用不同矩陣各存一份狀態的方式實作；它們都是同一批實體與收據的不同檢視。篩選保留系統、家族、版本、run_id、環境、時間區間、目前／歷史、缺證據與失敗項。

## 3. M01 固定八欄

| 欄 | 名稱 | 必要內容與互動 |
|---|---|---|
| 1 | 紅黃綠燈號 | 狀態文字、主要原因、必測通過數／應測數。點擊帶同實體及版本前往 M09/M10；顏色不代替文字。 |
| 2 | 編號 | 正式 VCGC governance_id；未發號使用 TMP-識別碼並標候選。正式編號不由 UI 自編。可展開檔案、AST、問題、測試、patch ID 關係。 |
| 3 | 名稱含版本號 | 完整檔名、家族、語言、相對路徑、內容 SHA；目前尾版／鎖定版／版史／候選分開。長名稱換行或展開，禁止靠截字辨識。 |
| 4 | 更新日期 | content_updated_at 與來源；另展開 observed_at、scanned_at、verified_at。只有檔案 mtime 時標「mtime 觀察值」，不能冒充內容更新時間。 |
| 5 | AST 結構與細節向下展開 | 原生解析器、節點 ID、class/def/PS function、完整簽章、範圍行號、參數、輸入輸出、呼叫、分支與例外；每層有 U/I/S/R/C 狀態入口。 |
| 6 | 錯誤與 AST | issue_id、規則 ID/版本、嚴重度、AST node_id、行號、錯誤原文、來源收據、影響集合。可直接定位第 5 欄同節點。 |
| 7 | 解決方案 | patch_id、原因、完整 def／PS function 差異預覽、前置條件、影響、相依、可平行／必須循序、預期斷言與回滾。方案存在不代表已套用。 |
| 8 | 全景式修正及更新日期 | Round1/2/3、PLANNED/APPLIED/VERIFIED/ROLLED_BACK、來源與結果 SHA、套用時間、重測時間、操作者與收據。修正日期與測試日期分開。 |

表頭、前四欄可凍結；欄寬可調。檔案列預設折疊；一個操作只展開目前分支。大量語句節點按需展開，不一次渲染所有 AST。主矩陣保持八欄，四層測試的完整內容放 M09，M01 第 5 欄只顯示對應測試帶與入口。

## 4. 三層資訊模型與大量資料

UI 最多三層導航；更深 AST 使用第三層內的樹、麵包屑及右側詳情，不再增加第四級導航。每個節點顯示子項數、紅黃綠數、筆數或欄位數、版本及最新驗證時間。

| 系統 | 第一層大類 | 第二層 | 第三層 |
|---|---|---|---|
| VDF 輸入 | 價量、法人、財報、營收、估值、宏觀、清單 | 來源／市場／資料集 | schema、欄位、ticker/date 分區、少量樣本 |
| VRN 輸出 | 個股、產業、其他投資報告、新聞 | 報告集合／Headers V3／年度財務表／摘要產物 | 單報告欄位、原文頁碼／區域、年度、驗算及來源圖像索引 |
| VQG 指標 | 價量、動能、波動、流動性、籌碼、輪動、基本面、風險 | 指標家族／公式版本 | 視窗、單位、輸入契約、參數、結果與驗證 |
| VAP 圖形 | 趨勢、比較、分布、關聯、結構、事件、矩陣／熱圖 | 模板／圖形物件 | Dataset 綁定、軸、系列、樣式、互動、匯出與視覺 QA |
| VCGC 治理 | 規則、工具、環境、編號、測試、稽核 | 規則組／工具家族／測試群 | 版本、契約、衝突、核准、收據 |

不把每筆交易、每個報告字元、每組指標計算結果展成首頁欄位。預設每頁 50 列，支援 25/50/100；記錄總數與當頁範圍，過濾前後的分母分開。資料按 system/matrix/category/entity_version 分片；第三層才讀欄位及抽樣 20 筆。大表由 Parquet/DuckDB 在本機計算摘要，HTML 只載入索引與選取的分片。

離線模式由使用者選取索引或分片；不假設 file:// 可以 fetch 同夾任意檔案。這次單檔原型支援 JSON 清冊匯入，不代表正式版已完成海量資料查詢或瀏覽器容量驗收。正式容量驗收應使用實際 10k／100k 檔清冊與百萬級節點，量測首次顯示、展開、篩選時間及 RAM；這是測試規模，不是已達成效能。

## 5. 所有 PS/PY 加速與網路政策

### 適用集合

- 加速必要集合 A：兩個使用者授權根目錄內所有受專案管理的 PY、PS1、PSM1；PS 資料檔 PSD1 納入解析，但以模組載入契約驗證，不注入會破壞資料檔語法的程式碼。
- 網路引擎必要集合 N：全部 VDF 引擎，聯集其他系統任何向外擷取資料的引擎／模組，依 entity_id 去重。
- 網路呼叫集合 E：N 及其相依鏈中的 API、HTTP、RSS、搜尋、新聞、SDK、瀏覽器擷取、curl/子行程等實際出口。
- 全部 VDF 引擎都應綁定受治理網路能力；純本地轉換引擎可維持 offline/disabled，不為取得綠燈而新增外部請求。沒有網路呼叫時 E 的分母為 0，顯示 N/A（無出口），不能寫 100%。

| 覆蓋指標 | 分子／分母 | 100% 的意思 |
|---|---|---|
| 清冊覆蓋 | 已納入且有雜湊的來源／完整發現的必要來源 | 無未列入、無讀取失敗；未能列舉的目錄使分母 UNKNOWN |
| AST 解析覆蓋 | 原生 parser 成功的來源／必要程式來源 | Python ast 與 PowerShell Parser 均成功；詞法掃描不算 PS AST |
| 加速接線覆蓋 | 解析確認且能解析至鎖定加速器的來源／A | 是有效接線，不只是註解、字串、import 或 graceful=None |
| 網路引擎接線覆蓋 | 解析確認受治理網路能力的引擎／N | VDF 全引擎納管＋其他外擷取引擎納管 |
| 網路出口覆蓋 | 路由至核准轉接器的出口／E | SDK／子行程／動態入口無遺漏；未知出口未解決不得滿分 |
| 執行驗證覆蓋 | 具有效同版執行收據的必要接線案例／必要案例 | 有載入、預算傳遞、受控呼叫或離線契約證據 |
| 熱點採用率 | 已接加速 API 的適用熱點／已識別適用熱點 | 另列分母及不適用理由，不能靠增加註解提高 |

每項同時顯示 required、verified、failed、unknown、excluded、pending。只在分母已知且 verified=required、failed=unknown=pending=0 時顯示 100%。字串標記率、AST 解析率、接線率、動態程式碼行／分支覆蓋率、速度提升與資料正確率各自成欄，不互相替代。

範圍不得為了滿分而縮小：第三方套件、venv、生成資料與 Git 內部物件可依規則排除，但保留數量與理由。使用者自有舊版本、凍結版不能默默排除；同時呈現「全檔案」及「現役依賴鏈」兩個分母。如果舊版不可改而又缺接線，顯示政策衝突，透過版本化 wrapper／父層 context 傳遞及實測證明繼承，或取得明確裁定。未證明前全檔案 100% 不成立。

### 注入與修正機制

Python 以 AST 定位、CST／精確文字範圍保留註解和格式；PowerShell 用原生 AST/Token 的 Extent 定位，兩者不能混用 Python AST。不得直接對全檔 regex 全域置換；不得先 import 掃描目標來猜 API。檢查動態 import、exec、反射、SDK 及 shell 呼叫的未解析集合。

接線需冪等；第二次執行零重複。參數保持頂部、完整 def 定義；保留 __future__、docstring、PS #Requires/param 順序、既有簽章與輸出契約。對被匯入的純函式庫，在入口或受治理 context 取得加速預算，避免在 import 時建立 thread pool 或改全機設定。全檔加入加速支援不代表每個函式都必須平行。

每個 patch 先核對原 SHA，在隔離副本 dry-run，執行語法、Unit、Integration、System、Result 驗證後才原子替換／新增版本；保留備份。共享 registry、薄尾父子鏈、同一輸出、資源預算與鎖檔修正必須循序；互不相依的檔案可限額平行。測試失敗不改寫成 PASS，回滾本批產物後保留失敗證據。新增檔案與正式發號均沿既有 VCGC 流程。

## 6. Unit / Integration / System / Result Testing & Validation 在哪

| 階段 | 測試對象 | 顯示位置 | 代表斷言 |
|---|---|---|---|
| U / UNIT | 單一函式、公式、parser、PS function | M01 第 5 欄節點測試帶＋M09 | 輸入邊界、回傳型別、錯誤處理、公式金標 |
| I / INTEGRATION | 跨模組依賴與 I/O 契約 | M03/M04/M08 交界＋M09 | schema、單位、日期、主鍵、工具注入與參數傳遞 |
| S / SYSTEM | 獨立 SystemManager 的端到端流程 | M00 系統列＋M09/M12 | 真正入口、環境、續傳、隔離、完整產物 |
| R / RESULT TESTING & VALIDATION | 實際輸出與來源／金標／獨立驗算 | M04/M06/M07＋M09 | 數值、完整性、單位、來源回指、圖表綁定與視覺檢查 |
| C / CLOSE-OUT | 本次版本與全部必測證據 | M00 放行狀態＋M13 | 無未解阻擋、同版同環境、可重現、回滾與交接齊備 |

M09 前四欄後固定 U/I/S/R/C 五個階段格；每格顯示 PASS/FAIL/NOT_RUN/BLOCKED/STALE/WAIVED、passed/required、最後測試時間及秒數。再列 environment、run_id、source_sha、input_manifest_sha、rule_sha、dependency_fingerprint、receipt_id。點格展開案例、命令、rc、assertions 與產物 SHA。

pytest 綠只表示該批測試通過。Result 驗證必須獨立於被驗證計算路徑：VDF 對來源資料與增量結果核對；VRN 對原文頁面、年度欄及金標驗算；VQG 用獨立公式／可信基準檢查 ADJ、扣當沖、2330 因子、look-ahead、缺交易日與單位；VAP 驗證 Dataset、軸、系列、時間對齊及視覺輸出，不能偷偷重新計算 VQG 的金融指標。

N/A 必須有適用性規則與版本，不算 PASS。WAIVED 必須有裁定人、理由、期限；顯示「帶豁免」，不能混入無條件全綠。

## 7. 紅黃綠與證據失效

- 紅：已確認 FAIL、語法錯誤、破壞契約、未解嚴重衝突、必要依賴失敗。子項紅向上傳遞。
- 黃：未跑、缺資料／環境、解析不明、證據過期、待裁、僅靜態確認、帶豁免。子項沒有紅但有黃，父項黃。
- 綠：該層所有適用必要條件通過，且綁定同版來源、規則、資料與環境的新鮮證據。不可用平均分抵銷失敗。

RUNNING 以進度文字附在燈號旁，不把執行中當綠。測試狀態與目前系統健康分開；歷史 PASS 保留原時間，但 current_verdict 可以 STALE。

當 source_sha、依賴、工具鎖、schema、公式、資料快照或環境 fingerprint 改變，沿依賴 DAG 將受影響證據標 STALE。未變項可重用既有證據，仍顯示原測試時間及重用原因。不得每次掃描都把舊收據時間改成「現在」。資料時效、證據 TTL 與 dependency fingerprint 都要檢查。

## 8. 參數、日期與時間

M05 分為資料選擇、計算、執行資源、網路、儲存、顯示、時間七大類。每參數包含型別、default、effective_value、來源層級、單位、允許值／上下界、是否必填、作用域、相依、敏感性、版本、驗證時間。敏感值只顯示 credential_ref 或遮罩，不記錄金鑰。

可覆寫參數建議解析順序：內建預設 → 系統設定 → 專案設定 → 本次任務參數；鎖定工具與治理限制不能被 CLI/環境變數繞過。解析結果留 receipt，而非只展示預設值。VQG 的 5/10/20/60/120/240 視窗是參數列，不替每個視窗再發一個指標 ID；特殊視窗由指標定義覆寫並留版本。

時間欄分為資料期別／交易時區、報告日期、as_of、擷取時間、來源更新時間、程式內容更新、掃描、測試、修復、部署、TTL。儲存 ISO 8601 UTC，UI 顯示 Asia/Taipei +08:00 至秒；財務年度／季／月為 period_type+period_value，不能假裝是某一天。date 與 datetime 不混淆。

## 9. 身分、版本與最小資料模型

所有實體使用 entity_id（穩定 UUID）與 entity_version；正式 governance_id 可空，candidate_id 必須可追溯。版號不唯一，必須與 owner_system、namespace、kind、family_id、content_sha 一起比對；同名同版不同 SHA 為衝突列。

| 實體 | 核心欄位 | 關聯 |
|---|---|---|
| EntityVersion | entity_id, governance_id, version, kind, owner, name, path, sha, timestamps | 所有矩陣共同鍵 |
| ASTNode | node_id, entity_id/version, parent_id, kind, qualified_name, span, signature, semantic_fingerprint | issue、patch、test 指向 node_id |
| Contract/Field | contract_id/version, direction, schema_id, field_id, dtype, unit, nullability, keys, cadence, lineage | inputs/outputs、Integration、Result |
| ToolBinding | binding_id, tool_family/version/hash, site_node_id, required, route, verification_receipt | M02 覆蓋 |
| TestReceipt | test_id/version, stage, entity_id/version, environment, fingerprints, status, rc, assertions, artifact_hashes | M09 與各層摘要 |
| Issue/Patch | issue_id, rule/version, node_id, severity, patch_id, base_sha, target_sha, risk, round, timestamps | M10/M11 |
| Run/Event | run_id, event_id, parent_event, immutable timestamps, result, source_sha, receipt_ref | M12/M13 |

行號只是定位，不是 AST 穩定 ID。優先用 qualified name、父節點、種類與既有映射維持 node_id；內容指紋協助對照。rename/move 不確定時列 ID_MAPPING_REVIEW，不能自動把新節點當舊節點。正式編號由 VCGC 裁定，UI 的 TMP ID 不能回寫成正式號。

## 10. 三輪全景修正與收尾

R1 發現：完整清冊、語法、接線、網路出口、規則、I/O、依賴及舊證據有效性。輸出 issue baseline 和原始 SHA。

R2 修正：獨立項限額平行，共享依賴循序；完整差異預覽、依據 SHA 套用、新版號、冪等性與回滾。只重跑被影響的測試集合，不能憑感覺跳過相依。

R3 驗證：重建 AST、重算所有覆蓋分母，執行 U/I/S/R，再做來源差異與輸出核對、編號／註冊／SDD／交接。結果通過才寫 VERIFIED；有未完成就保留 PARTIAL/BLOCKED。M11 第八欄呈現每輪時間與前後證據，而非只放「已修好」。

## 11. 相較 GitHub 的管理粒度

GitHub 繼續負責來源提交、diff、分支、PR 和 CI。VCGC 在上層連結函式／AST 節點、工具接線、資料契約、指標公式、圖形模板、資料快照、環境及本次執行證據；這是更細的治理粒度，不是取代 Git 版控。commit 與工作樹 SHA 並存，未提交的本機版本也可辨識。每筆狀態可回到其 commit/file/node/receipt，並可從問題反查受影響產物與測試。

## 12. 實作分期與驗收

P1 清冊契約：補齊兩個根目錄完整清冊、PowerShell 真 AST、node/span、來源時間與工具鎖；原先 v0100 掃描輸出保留。P2 多矩陣唯讀 UI 與跨矩陣選取；匯入不觸發程式執行。P3 接線／注入規劃、精準 patch 與隔離回歸。P4 同步實機 U/I/S/R 收據、證據失效 DAG、原子更新與回滾。P5 容量、互動、長測及正式 closeout。

驗收至少包括：同版同 SHA 去重；同版異 SHA 衝突；未知分母不顯示滿分；過期 PASS 不能綠；PS 解析失敗不可用字串標記遮蓋；純本地 VDF 已納管但不產生請求；網路 DENY 不換路繞過；第二次注入零重複；完整 def 與 param 順序保留；修復失敗可回滾；結果驗證故意注入錯單位／錯日期／錯 ADJ 因子可攔下；大量資料分頁不失列；每項可回到來源與收據。

交付 HTML 的現有能力：14 矩陣導航、指定八欄、三層展開、U/I/S/R/C 測試詳情、篩選／分頁、設計資料匯出及 v0100 SOURCE_INVENTORY.json 唯讀匯入。它不執行原始碼、不修改 VCGC、不宣稱已補足 Windows AST 接線或真實測試。
