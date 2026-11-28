# VCGC Token-Saving Toolkit v0300 · 全景矩陣

已停止擴寫，凍結目前已完成工具後交付。正式系統發號、原生啟用與 PC 實機執行分開列帳。

| 項目 | 入口／版本 | 內容 | 狀態 |
| --- | --- | --- | --- |
| 1 模組整併 | unify／1 | 三輪→AST 同批→FNC-LIB→註冊候選→測試→回滾保護 | 已實作；原生註冊待驗 |
| 2 全景檢查 | sweep／2 | PC 指定範圍／AI 匯出／GitHub／Graphify／OmniRoute→修復→全面複驗 | 已實作；私人來源與 PC 待驗 |
| 兩動作共用 | both | 共用基準與三輪，避免重掃 | 已實作 |
| 省 Token 接線 | tools／token read,slice,digest,pack,chain,delta | 正式 token 鎖冊與精確 argv | 原工具原生執行待驗 |
| 加速器 | v1141 | SHA 驗證、thread_budget、parallel_map | API 接線已測；PC 效能未驗 |
| 網路工具 | v1652 | 來源辨識、工具橋、transport 契約 | 實際資料路由待驗 |
| 測試 | 107/107 | 61 原有＋46 新增；Linux 隔離 fixture | PASS（容器） |
| 備份快照全查 | 749／749／0 | 三輪與最後一次皆相同分母 | 6805 靜態規則命中；未寫回 |
| VCGC 正式主庫 | DuckDB／Parquet | 既有 owner manager gate 與寫入回證 | 待接入；無 SQLite 主庫替代 |
| GitHub Hub | 工作分支／版本化目錄 | 提交此次凍結工具與矩陣 | 不直接改 main |
| PC 同步 | Desktop/測試/VCGC/PanoramaFusion_v0300 | OneDrive 雲端文件同步 | 雲端上傳與桌機落地分開驗證 |

## 三輪與最後檢查

| 輪次 | 方向 | 驗證 | 應掃 | 已掃 | 略過 | 靜態 RED |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | FORWARD | ETAG_SKELETON | 749 | 749 | 0 | 6805 |
| 2 | REVERSE | ETAG_SKELETON | 749 | 749 | 0 | 6805 |
| 3 | FORWARD | FRESH_SHA_AST | 749 | 749 | 0 | 6805 |
| 4 | 全面複驗 | 實讀 SHA／AST | 749 | 749 | 0 | 6805 |

這是原 v0101 備份的探索盤點，未取得正式 manifest，不是目前 PC／GitHub 最新程式驗收。靜態規則命中須複核，不等同每項都是行為錯誤。

## 前 20 大風險：偵測與內建處置

| 編號 | 風險 | 如何偵測 | 內建處置 | 快照狀態 |
| --- | --- | --- | --- | --- |
| R01 | 漏掃／來源範圍不全 | manifest 分母、已掃、略過、AI 來源覆蓋 | 分母不明或漏項阻擋套用，列出缺失來源 | 有阻擋項 |
| R02 | 尾版／SHA／快取錯位 | Git SHA16、鎖冊完整 SHA、第三輪實讀 | 來源漂移立即停止；不依檔名字尾換版 | 待證據／接入 |
| R03 | 函式 API／行為回歸 | 參數綁定、原版與候選契約、已鎖成功數 | 完整 def 同簽章驗證；行為失敗回滾 | 待證據／接入 |
| R04 | 同名符號／別名覆蓋 | 每檔重複定義、路徑::符號、指令重號 | 拒絕碰撞；保留所有唯一功能與舊 action 別名 | 有阻擋項 |
| R05 | 依賴環／動態匯入漏判 | Graphify、AST import、任務 DAG 與循環 | 依賴層順序執行；循環與未知依賴列為待協同修復 | 待證據／接入 |
| R06 | 秘密／資料外送與提示注入 | AST 敏感常數、唯結構路由、來源權限 | 疑似憑證不送模型；業務資料禁止外送 | 待證據／接入 |
| R07 | 環境缺件／版本漂移／違禁依賴 | VCGC SSOT、精確版本、實際 import、所有 via_* | 缺權威分母不報 100%；既有安裝器在副本補裝重驗 | 待證據／接入 |
| R08 | 假加速／橋有標記但沒生效 | 完整 SHA、真實模組載入、逐檔橋執行探針 | 加速器無法載入阻擋；禁止以標記替代覆蓋率 | 待證據／接入 |
| R09 | 網路工具未接管實際擷取 | AST 別名／Session 呼叫、資料路由契約 | 載入工具與 transport 分開驗；未實測不放行 | 待證據／接入 |
| R10 | stdio MCP 的 stdout 污染 | MCP 名單、AST print、JSON 解析契約 | 安全 print 呼叫定位改成 stderr helper；不改協定回覆 | 已有指定範圍證據 |
| R11 | AST 座標／編碼／裝飾器損壞 | 位元座標、錨點、BOM／future、parse／compile | 先下後上合併切片；重疊拒絕，保留原始編碼 | 有阻擋項 |
| R12 | 自動註冊／發號／跨系統寫錯 | 正式 registry_stage、編號零遺失／重號、系統 owner | 由原管理器產生候選冊，同交易套用並驗 SDD | 待證據／接入 |
| R13 | 短指令錯綁／參數遺失 | alias 唯一性、argv 契約、正式指令註冊稽核 | 兩動作與 Token 工具共用入口；註冊未驗證不冒稱可用 | 待證據／接入 |
| R14 | 並行互撞／CPU 記憶體失控／誤殺 | 每檔任務分組、依賴排程、執行緒上限、PID 身分 | 同檔合併、跨檔受控並行；只停止本引擎持有的程序 | 已有指定範圍證據 |
| R15 | 備份／寫入／回滾造成遺失 | 備份 SHA、CAS、fsync、journal、回復比對 | 先驗新備份再輪替；多檔失敗整輪回滾 | 待證據／接入 |
| R16 | SSOT／Regex／參數／單位錯誤 | 各系統管理器的 ssot_verified 與資料契約 | 不得猜公式或強填數值；交各自 manager 修復再驗 | 待證據／接入 |
| R17 | 資料格式／ schema／重複入庫 | 唯讀 schema、SQLite／DuckDB／Parquet 契約 | 缺欄或缺套件列 PENDING；不以列數替代正確性 | 本快照無此資料範圍 |
| R18 | AI／GitHub／Graphify／OmniRoute 不同步 | 端點實測、來源快照、圖譜、遠端版本與 scope | NOT_CONNECTED 明列；無來源證據不回報全景全綠 | 待證據／接入 |
| R19 | 錯刪薄尾／外部呼叫／唯一能力 | closed-world、逐 API 契約、chain 及尾版動詞稽核 | 僅證實重複者可退役；保留原件、舊別名與回滾點 | 待證據／接入 |
| R20 | 假全綠／測試縮水／未做最終複驗 | 三輪一致性、紅燈棘輪、完整 manager、Windows／輸出／UI | 任何新增紅燈停機回滾；最後另跑完整覆蓋與 manager | 待證據／接入 |

## 兩動作與既有省 Token 指令

| 指令 | 目的 | 接線方式 |
| --- | --- | --- |
| 1 / unify | 模組化、簡化、FNC-LIB、註冊候選 | 內建三輪＋同批修復＋全面複驗 |
| 2 / sweep | VCGC 全景三輪、AST 修復、全面複驗 | PC／AI 匯出／GitHub adapter／Graphify／OmniRoute |
| both | 共用三輪檢查後完成兩動作 | 避免同一份來源重複讀取 |
| tools | 兩動作與省 Token 工具清單 | 顯示可用、未執行、待接入狀態 |
| risks | 前二十大風險與內建處理 | PASS／FAIL／PENDING／NOT_IN_SCOPE 分開 |
| token read | 鎖定 token 工具骨架卡 | 精確 argv，核對完整 SHA |
| token slice | 鎖定 token 工具符號切片 | imports＋目標完整 def |
| token digest | 鎖定 token 工具日誌蒸餾 | 不回傳整份 traceback |
| token pack | 鎖定 token 工具上下文包 | 有限預算與來源 SHA |
| token chain | 鎖定 token 工具薄尾依賴鏈 | 退役前辨識真實載入鏈 |
| token delta | 鎖定 token 工具增量差異 | 只看新增／已解問題 |
| token tools / verbs | 正式工具註冊與動詞卡 | 不另立工具版本正本 |
| read / slice | 本引擎離線骨架與切片 | ETag 304／AST imports／簽章／錨點 |
| graph | Graphify 節點與路徑 | 優先依賴定位，不做全文盲搜 |
| audit / backup / recover | 環境、快照與回滾 | 沿用 VCGC 安裝與交易閘 |
| boot / status / stop | 三獨立流程與收據 | 具 PID 身分驗證及負載上限 |

`via-fuse`、`via-panorama` 等是正式註冊候選別名；尚未宣稱已安裝進你 PC 的命令表。

## 32 項 Token-Saving 功能

| ID | 能力 | 實作狀態 |
| --- | --- | --- |
| TS01 | 來源清冊與內容指紋 | 已實作，隔離測試 |
| TS02 | 增量掃描與續跑 | 部分完成／待原生 |
| TS03 | read 與 ETag 重用 | 已實作，隔離測試 |
| TS04 | slice 與 AST 定位 | 部分完成／待原生 |
| TS05 | 本機中英文檢索 | 待既有管理器接入 |
| TS06 | Graphify 受影響範圍 | 部分完成／待原生 |
| TS07 | 精準 SQL 讀取 | 部分完成／待原生 |
| TS08 | 未命中與缺口摘要 | 已實作，隔離測試 |
| TS09 | FULL／DELTA 交接 | 待既有管理器接入 |
| TS10 | 證據卡與原文取回 | 部分完成／待原生 |
| TS11 | 工具輸出摘要 | 已實作，隔離測試 |
| TS12 | 故障指紋去重 | 部分完成／待原生 |
| TS13 | Headroom 類內容壓縮 | 待既有管理器接入 |
| TS14 | 必保欄位驗證 | 部分完成／待原生 |
| TS15 | 表格共用結構 | 待既有管理器接入 |
| TS16 | 相同內容重複傳送抑制 | 部分完成／待原生 |
| TS17 | 任務範圍裁剪 | 已實作，隔離測試 |
| TS18 | Skills 按需載入 | 待既有管理器接入 |
| TS19 | MCP 工具清單分組 | 部分完成／待原生 |
| TS20 | 固定規則前綴 | 部分完成／待原生 |
| TS21 | 分層記憶 | 部分完成／待原生 |
| TS22 | 記憶失效與衝突 | 部分完成／待原生 |
| TS23 | 跨 AI 接手摘要 | 已實作，隔離測試 |
| TS24 | 共用術語與規則版本 | 部分完成／待原生 |
| TS25 | 按能力與預算選模型 | 部分完成／待原生 |
| TS26 | 模型結果快取 | 待既有管理器接入 |
| TS27 | 重試與循環偵測 | 部分完成／待原生 |
| TS28 | 有條件的獨立覆核 | 部分完成／待原生 |
| TS29 | 有界任務與併行 | 已實作，隔離測試 |
| TS30 | Task Observer 改善回路 | 待既有管理器接入 |
| TS31 | Token 與費用帳本 | 部分完成／待原生 |
| TS32 | A/B 與發布決策 | 部分完成／待原生 |

## 13 項外部能力

| ID | 能力 | 本次狀態 |
| --- | --- | --- |
| EXT01 | Claude Code Setup | 列入整合清冊；此次未安裝，PC 原狀態待核對 |
| EXT02 | ECC | 列入整合清冊；此次未安裝，PC 原狀態待核對 |
| EXT03 | claude-mem | 列入整合清冊；此次未安裝，PC 原狀態待核對 |
| EXT04 | OmniRoute | 路由 adapter 已有；原生待驗 |
| EXT05 | Headroom | 列入整合清冊；此次未安裝，PC 原狀態待核對 |
| EXT06 | Task Observer | 列入整合清冊；此次未安裝，PC 原狀態待核對 |
| EXT07 | Hallmark | 列入整合清冊；此次未安裝，PC 原狀態待核對 |
| EXT08 | Anatomy | 列入整合清冊；此次未安裝，PC 原狀態待核對 |
| EXT09 | Impeccable | 列入整合清冊；此次未安裝，PC 原狀態待核對 |
| EXT10 | Ponytail | 列入整合清冊；此次未安裝，PC 原狀態待核對 |
| EXT11 | Matt Pocock Skills | 列入整合清冊；此次未安裝，PC 原狀態待核對 |
| EXT12 | Cloudflare Security Audit | 列入整合清冊；此次未安裝，PC 原狀態待核對 |
| EXT13 | REA | 列入整合清冊；此次未安裝，PC 原狀態待核對 |

來源：[VCGC v0103 工具計畫](https://chatgpt.com/space/page_8c4b2563fcdc8191877babacc033babc)；[GitHub 正式工具基準](https://github.com/tonykuni/movies-dataset/commit/519ad418ca48871d031b907c43c635648bb5f9af)。這份矩陣是交付快照，正式版本與號碼仍由 VCGC SSOT 管理。
