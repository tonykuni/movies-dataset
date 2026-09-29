# 側線 2026-09-29 i:SSOT 全景上下單向檢測 · 編號只增自核 · 註冊沿鏈讀 · 省 Token v0117 · AI 必用功能卡

主線批號由併線的手指定(L25)。本批第一段接在 PR #375(`codex/vcgc-closeout-20260929`,d1034c48a)之上,版號 LL334 全分支掃過,未撞號。

- 第一段 f4dff4616 已由 PR #376 併入 main(d6c304d92,PR #375 同時併入)。
- PR #376 的 Windows UAT 在最後一步 `handoff check` 紅:panorama / token 兩案沒有收據 · 5 支新尾版沒有測試收據 · 交接冊改過使 numbering 收據失效。
- 本段收尾接在 main 之上,補齊收據與快照,讓這一步回綠。
- 同一輪 CI 還量到合約測試 `test_11_committed_page_matches_generator` 紅:第一段新增 CGC_MDL247 後,中央治理模組 255 → 256,但追蹤中的總控頁沒重產。照 LL49 在只含已追蹤檔的乾淨工作樹用 `VIA_SYSTEM_MANAGER_v0150.py ui --no-open` 重產,差異只有產生時間 · 模組數兩處 · 模組清單多一列。合約測試 19/19 過 · 桌機 / 手機瀏覽器 UAT 過(模組 256 · 頁面錯誤 0 · 外部請求 0)。

## 一、操作員原話(逐字)

| # | 原話 | 入冊 |
|---|---|---|
| 1 | VCGC TO VDF TO VRN 全部檢測 將VCGC將SSOT REGEX 同義字 自動編號 命名 註冊功能強化 SSOT全景式檢視 優化 自動化 自動自適應式上下單向檢測到底更新整合優化 只增不減只要不發生衝突政策 | VCGC-REQ077 · 078 · 079 · 080 |
| 2 | VCGC TO VDF TO VRN SSOT相關功能進一步升級強化一次 PLEASE ADVIS TOP 15 LOCAL FREE LIBS TO IMPROVE STREAMLIT RICH LIB TO DEPLOY. | VCGC-REQ077 · 083 |
| 3 | VCGC TO VDF TO VRN盤點一個中央控管功能架構還那些缺漏 補強 有新增功能每個功能可增TOP 10 LOCAL FREE LIBS既有的工具功能下再進一步升級優化TOKEN SAVING工具並且AI進入讀取後開始使用要求充分讓AI知道功能及使用及必用功能寫入 | VCGC-REQ079 · 081 · 082 · 083 |
| 4 | 註冊編號SSOT化更新全部SYNC ALL TO GITHUB | VCGC-REQ078(原話入冊)· VCGC-REQ057 |
| 5 | 既有範圍內註冊 不要擴張範圍 | VCGC-REQ078(原話入冊);見第三節 |
| 6 | SYNC ALL TO GITHUB. | VCGC-REQ057 |
| 7 | 收尾工作 / 交接 | VCGC-REQ058 · VCGC-REQ075 |

非需求 3 則(照答,不入冊):暫停更新紀錄 · 現況提問 · 流程矩陣提問。需求冊 v0104 的 reviewed 從 144 則改記為 149 則。

## 二、本批交付

| 檔 | 做什麼 | 驗證(實跑) |
|---|---|---|
| `CGC_MDL247_SSOTPanorama_v0100.py`(新) | 六族(正則 · 同義字 · 自動編號 · 命名 · 註冊 · 上下連結)× 四層(VCGC → VDF → VRN → SUP)全景。由上而下單向檢測:上層紅,下層同族標「上游紅」,照量不停,一直到底。輸入指紋沒變就沿用上一次結果。每格都呼叫既有正主,只讀 | 自測 fail=0 · 交接 case `panorama` 收據 rc 0 |
| `CGC_MDL237_NumberingSystem_v0108.py` | 活檔判定只看目錄,檔名不算隔離(Z280 真因:檔名含 `_quarantine` 的活檔被誤排)· 唯讀只增稽核 `audit` · `--apply` 寫後自核,違反只增就整批還原 | 自測 46 OK · 交接 case `numbering` 收據 rc 0 |
| `CGC_MDL245_SDDValidator_v0104.py` | X-REQ-BACK:需求歸屬指到的工作流(含其步)必須回指該需求 | 單向 4 條由工作流冊 v0103 補齊 → X-REQ-BACK 綠 · case `sdd` 收據 rc 0 |
| `CGC_MDL149_VeritasCentralGovernanceConsole_v0178.py` | `manager_names` 沿系統管理器薄尾鏈讀名冊(VDF / VRN 上行七處 6/7 假缺 → 7/7)· `ssot panorama` · `functions` · token 卡尾印必用摘要 | case `entry` 收據 rc 0 |
| `CGC_MDL158_VIAPanoramaAuditRepair_v0117.py` | 省 Token:.json 兩層卡 · .jsonl 欄位卡 · JSON 路徑切片(`a.b[0]` · `[-1]` · `[*]` · `[鍵=值]`)· `chain` 薄尾版本鏈圖 | 本版 9/9 · 前版 45/45 · 啟用閘 10 項全過 · 鎖冊 token → v0117(VIA-TOOL-0212)· case `token` 收據 rc 0 |
| `VIA_AI_FunctionCard_SSOT_v0100.json`(新) | AI 必用功能卡唯一正本:12 步必用順序 · 指令 · 時機 · 禁止。CLAUDE.md / AGENTS.md 只指向本冊 | `via-vcgc functions` rc 0 |
| 需求冊 v0104 · VCGC 工作流冊 v0103 · VRN 工作流冊 v0103 | +VCGC-REQ077–083 · +VCGC-WKF001-STP007 · 回指補齊 | SDD X-REQ · X-REQ-BACK · X-NUM 綠 |
| 交接冊(就地只增) | +case panorama / token · 本批工作項 6 件 VERIFIED · 4 件帶理由待辦 | 交接 GREEN · 驗收 YELLOW |

## 三、範圍令:編號只登本批的列

操作員令:「既有範圍內註冊 不要擴張範圍」。

先用 `--apply` 全量重建,量得整樹 +1,862 列:本批的列,加上範圍外的積壓,再加上既有列 `updated_at` / `lamp` / `gone` 的翻動(24 本冊,+39,358 / −14,948 行)。依令處理如下:

- HEAD 的編號冊一字不動。
- 只把本批自己的列插回去,號碼照引擎發的原字照搬。
- 舊列的相對次序不變;每本冊都是只增,刪 0 行。

| 冊 | 本批 + | 內容 |
|---|---|---|
| MDL | 6 | 5 支新模組 + Z280 修好後被正確認成活檔的 1 支(`vdf_akshare_dedup_invalid_quarantine_gate_v02783.py`,本批修正的直接對象) |
| FNC | 103 | 上面 6 支的函式(VCGC 102 · SUP 1) |
| REQ · STP | 7 · 1 | VCGC-REQ077–083 · VCGC-WKF001-STP007 |
| TOOL · ENV | 2 · 1 | token v0117 的兩列工具號(VIA-TOOL-0194 · VIA-TOOL-0212)· 鎖冊 token@v0117 |
| LGC | 12 | 交接冊新增的 2 案 + 10 件工作項 |
| SSOT(rows) | 4 | 功能卡 · 需求冊 v0104 · 兩本工作流冊 v0103;另外元件冊、交接冊兩本就地改過的冊換內容指紋 |
| 分類碼 | 7 | FNC-C3946–C3951 · TOOL-C019 |

**範圍外,不寫**(掛交接待辦 `VCGC-REQ078:backlog`,等操作員令):

- FM 股票清單 862 列 · SYN 同義 862 列 · TST 測試 5 列,合計 1,729 列。
- 既有列的 `updated_at` / `lamp` / `gone` 翻動,以及 `notes.ins`。
- 完整重建差異只留在 AI 暫存,不入倉。

## 四、收尾實測

| 檢 | 命令(經 VCGC) | 結果 | 燈 |
|---|---|---|---|
| 第一步 省 Token | `token` | 已啟用 6/6(鎖版 v0117 · NLP v0105) | 綠 |
| 註冊冊乾跑 | `registry-sync` | 活元件 13,820 · 新 0 · 變更 0 · 退役 0 · AST 錯 0 · 他冊已發 18 號 · 撞號 0 | 綠 |
| 編號只增稽核 | `run CGC_MDL237_NumberingSystem audit` | 基準 main d6c304d92 · 101,489 → 101,625(+136)· 遺失 0 · 改身分 0 · 重號 0 · 冊內紅列 21(對 PR #375 前的 main cb3727e78:96,502 → 101,625,遺失 / 改身分 / 重號也都是 0) | 黃(紅列 21 在 HEAD 已是 21,本批沒加;法條缺號 Z263 · 同義一詞兩主 Z264 待裁) |
| SDD 交叉檢 | `run CGC_MDL245_SDDValidator check` | 工作流 30 · 步 110 · 需求 109 · 綠 14 項(X-REG · X-NUM ×2 · X-REQ · X-REQ-BACK · X-CONFLICT …) | 黃:X-REQ-OPEN 17(各有歸屬與下一步)· X-LOCK 6(見第五節) |
| 交接測試 | `handoff test <case>` × 8 | handoff 68s · provenance 35s · entry 45s · manager 35s · sdd 38s · numbering 76s · panorama 35s · token 38s,全部 rc 0 且見到標記 | 綠 |
| 交接快照 | `handoff checkpoint` | 需求 109 · 監看檔 2,745 · 待辦 25 · 可沿用 12 · findings 0 | 交接綠 · **驗收黃**(有待辦就不寫成成功) |
| SSOT 全景 | `ssot panorama` | 探針 7 · 8.2 s(矩陣見下表) | 黃 |

SSOT 全景矩陣(`—` = 該層沒有這族的正主探針,不是綠):

| 族 | VCGC | VDF | VRN | SUP | 非綠原因 |
|---|---|---|---|---|---|
| 正則 | 黃 | — | — | — | E4 台股代號 4 本冊判法不同(各為操作員裁定的範疇,收斂與否由操作員裁) |
| 同義字 | 黃 | — | 黃 | — | 同詞多義 10 條 · 網域冊 NONCANONICAL 1 · VRN 下游落差 3 支 · 拒絕閘漏口 8 |
| 自動編號 | 黃 | 綠 | 綠 | 綠 | 冊內紅列 21(既有) |
| 命名 | 黃 | 黃 | 黃 | 黃 | 同號異名 12 組 · 版號異形 44 · 沒版號 .py 841(Z279 / Z281,操作員裁) |
| 註冊 | 綠 | 綠 | 綠 | 綠 | — |
| 上下連結 | 黃 | 綠 | 綠 | 綠 | 待重驗鎖 VCGC-WKF003 / 004 / 009 |

## 五、收尾時量到的問題(都入交接待辦,不默默略過)

1. **交接收據「沿用成功」的盲點**(`VCGC-REQ075:reuse-glob`)
   - 現象:CGC_MDL140 v0101 的 `run_case` 判沿用時,只比收據上記的相依雜湊,不重掃宣告的相依樣式。
   - 後果:新尾版 CGC_MDL149 v0178 · CGC_MDL245 v0104 雖符合 `_v*.py`,卻沒進舊收據。第一次跑時 `entry` / `sdd` 被判「沿用成功」,實際沒測到新尾版。
   - 本批處置:把相依集合變了的 5 張收據(handoff · provenance · entry · manager · sdd),照工具原格式存進 `evidence/history/`,再真跑。
   - 下一步:出 v0102 薄尾,沿用前重掃相依樣式,集合不同就重跑;自測加負控。
2. **X-LOCK 6 處要重驗**(`VCGC-REQ030:relock`)
   - 現象:已鎖工作流 VCGC-WKF003 / 004 / 009 的正主尾版換了,其中 4 處是 #373–#375 就有的。
   - 為什麼本批不做:重鎖要先提交,再在同一個 HEAD 跑 `real`,之後才准寫下一版燈鎖冊。這屬於收尾驗收輪,本批不擴張。
3. **編號積壓**(`VCGC-REQ078:backlog`):見第三節。
4. **命名裁定**(`VCGC-REQ080:naming`):同號異名 12 組,要分辨是同家族伴隨模組還是真撞號,由操作員裁;不自動改名。

## 六、中央控管功能架構盤點:缺漏與補強

| 層 | 正主 | 本批前的缺漏(實測) | 本批補強 | 仍待(交接待辦) |
|---|---|---|---|---|
| 入口 / 第一步 | VCGC `token` → `enter` | AI 進場只看到工具卡,不知道必用順序 | `functions` 12 步必用卡;token 卡尾印必用摘要 | — |
| 讀檔省 Token | CGC_MDL158(鎖冊 token) | JSON / JSONL 大冊只能整檔讀;看不出薄尾鏈 | v0117:兩層卡 · 欄位卡 · 路徑切片 · 鏈圖 | — |
| SSOT 六族總覽 | 第四扇門 · C3 · 各族正主 | 各族各一支,沒有總表,也沒有上下串流 | CGC_MDL247 全景 · 上游紅串流 · 自適應沿用 | 正則 / 同義字在 VDF / SUP 層沒有探針 |
| 自動編號 | CGC_MDL237 | Z280 誤排活檔;沒有唯讀稽核;寫壞不會自己還原 | v0108 目錄判定 · `audit` · 寫後自核還原 | 積壓 1,729 列待令 |
| 註冊 | registry-sync · 系統管理器 | 薄尾只讀尾版 → 上行七處 6/7 假缺 | v0178 沿鏈讀 → 7/7 | — |
| 需求 ↔ 工作流 | 需求冊 · 工作流冊 · CGC_MDL245 | 單向 4 條沒被抓到 | v0104 X-REQ-BACK · 工作流冊 v0103 回指 | — |
| 命名 | (全景命名族只報) | 沒有普查 | 全景命名族四層普查 | 12 組待操作員裁 |
| 交接 | CGC_MDL140 v0101 | 沿用判定看不到新尾版 | 本批存史重跑 5 張收據 | v0102 重掃相依樣式 |
| 驗收鎖 | CGC_MDL245 `lock` | 4 處尾版已換未重鎖 | — | 6 處重驗 |

## 七、本機免費函式庫建議(VCGC-REQ083;只建議)

安裝是操作員的手,經 ENV MANAGER 照順序:盤點 → 相減 → 偵測 → 隔離 → 還原點 → 再新增 → 通過才執行。AI 不裝套件,TA-Lib 一律不列(L50)。

下表「本倉」是 `import` 該庫的 .py 檔數;「容器」是本 AI 容器實測 `find_spec`,只代表容器,不代表工作站。

### 7.1 TOP 15

| # | 庫 | 用在哪 | 本倉 | 容器 |
|---|---|---|---|---|
| 1 | rich | 全景矩陣 / 樹狀串流 / 進度條在終端直接上色;`Console(record=True).save_html()` 出頁 | 166 | 未裝 |
| 2 | streamlit | 本機唯讀頁:讀 `SSOT_PANORAMA_latest.json` 畫矩陣,不呼叫引擎 | 1 | 未裝 |
| 3 | textual | 以 Rich 為底的終端互動台:點格看原因、下一步 | 0 | 未裝 |
| 4 | polars | 表格層正主(Polars canon);大冊聚合 | 55 | 未裝 |
| 5 | duckdb | `read_json_auto` 直接查 JSONL 編號冊,不先載入記憶體 | 897 | 1.5.5 |
| 6 | pydantic | SSOT 冊的欄位模型;讀冊即驗型 | 46 | 未裝 |
| 7 | jsonschema | 冊檔對 schema 驗證,可放 CI | 15 | 未裝 |
| 8 | orjson | 1.4 MB 編號 SSOT 與 3 MB JSONL 冊的快速讀寫 | 2 | 未裝 |
| 9 | rapidfuzz | 同義字 / 命名的近似候選(只列候選,裁定仍在操作員) | 13 | 未裝 |
| 10 | regex | Unicode 屬性(`\p{Han}`)正則,給正則族 | 2 | 2026.9.10 |
| 11 | opencc | 繁簡正規化,給同義字族 | 24 | 未裝 |
| 12 | networkx | 需求 ↔ 工作流 ↔ 步的圖;上下串流與回指檢 | 5 | 3.6.1 |
| 13 | deepdiff | SSOT JSON 結構化只增差異 | 1 | 未裝 |
| 14 | watchdog | 檔案事件觸發全景自適應重探,不用輪詢 | 2 | 未裝 |
| 15 | diskcache | 全景格、骨架卡依指紋持久快取 | 0 | 未裝 |

### 7.2 每個新功能 TOP 10

| 新功能 | TOP 10 |
|---|---|
| SSOT 全景(CGC_MDL247) | rich · textual · streamlit · networkx · duckdb · polars · diskcache · watchdog · plotly · xxhash |
| 編號只增稽核(CGC_MDL237 v0108) | orjson · msgspec · deepdiff · duckdb · polars · hypothesis(只增不變式性質測試)· xxhash · jsonschema · pydantic · rich |
| 註冊 / 回指(CGC_MDL245 v0104 · VCGC v0178) | networkx · pydantic · jsonschema · deepdiff · rapidfuzz · duckdb · hypothesis · pytest · rich · pyvis |
| 省 Token(CGC_MDL158 v0117) | libcst · tree-sitter · ijson(串流讀大 JSON)· orjson · jmespath · xxhash(etag)· diskcache · pygments · radon · rich |
| AI 必用功能卡(functions) | pydantic · jsonschema · rich · textual · typer · click · markdown-it-py · jinja2 · pyyaml · streamlit |

### 7.3 Streamlit / Rich 部署建議

**Streamlit**
- 安裝:獨立一個 `via_` 境。Streamlit 會釘 protobuf / pyarrow / pandas 範圍,不要進主境。
- 設定:`.streamlit/config.toml` 設 `server.address = "127.0.0.1"` · `server.headless = true` · `browser.gatherUsageStats = false`(遙測關)· `server.fileWatcherType = "none"`。
- 頁的行為:只讀 `VIA_Reports/ssot_panorama/SSOT_PANORAMA_latest.json` 與 `SDD_CHECK_latest.json`,`st.cache_data` 以檔案 sha 為鍵。頁上不放任何寫入或執行鈕。
- 入口:日後要經 VCGC 新動詞進入,改 `.ps1` 要 L70 逐次許可。

**Rich**
- 用 `Table`(矩陣)· `Tree`(上游紅串流)· `Live`(長跑進度)· `Console(record=True)` 出 HTML。
- 尊重 `NO_COLOR`;Windows Terminal 下 `legacy_windows=False`。
- 容器沒有 Rich 時照純文字輸出(現行 VCGC 輸出就是純文字)。

## 八、交接(下一手照做)

1. 進場依序跑:`token` → `functions` → `handoff check`,讀待辦 25 件。本批帶理由待辦 4 件:
   - `VCGC-REQ080:naming`
   - `VCGC-REQ030:relock`
   - `VCGC-REQ078:backlog`
   - `VCGC-REQ075:reuse-glob`
2. 驗收輪:`run CGC_MDL245_SDDValidator real` → `lock --apply`,X-LOCK 回綠才可寫驗收。
3. 編號積壓:操作員下令才跑 `run CGC_MDL237_NumberingSystem --apply`,之後 `audit` 必須遺失 0 · 改身分 0 · 重號 0。
4. 仍保留的舊待辦:
   - Codex #373 P2(Register v0264 · 負數逾時,要 L70 許可)
   - U/I 原始模板 v0101
   - VRN 路由暫停
