# VIA Agent OS hardened v1.0.2 — 22 檔依賴、函式覆蓋與並發審查

**審查對象：** 原始 `via_agent_os_complete_latest_20261104.zip` 的 22 個成員，以及其後建立的 hardened v1.0.2 單檔與遠端 VCGC preflight 工具。原 ZIP 保持不變；本報告不把它說成已包含新 hardening。

**最終 hardened source：** `via_agent_os_unified_readonly_hardened.py`，266,514 bytes，SHA-256 `ca3c38ee00d2d7df5af71bcaea59ab7e7c73a15ec1d1f7b03218127efaf62af5`，`UNIFIED_VERSION=1.0.2`。

**驗收狀態：** Python compile PASS；VIA selftest **48/48**（base 28 + integration 20）；8 Skills acceptance **27/27**；VCGC remote-profile preflight **20/20**。沒有實際 VCGC endpoint、OAuth login、TLS probe、遠端 MCP handshake 或 tool call；那些明確標示為尚未執行。

## 1. 架構摘要與功能呼叫路徑

![Hardened VIA 系統功能／安全流程圖](../assets/via_agent_os_hardened_system_flow.png)

核心產品仍是**一個 Python 檔**，只依賴 Python 標準函式庫。CLI 與 MCP 進入 Strict JSON／大小及政策閘，再同步呼叫純函式技能、TokenEngine、AST、SDD、mount/Git metadata 等功能。Dashboard 是 Python 組裝後的離線 HTML 快照，不是常駐服務。

### 單檔內主要責任與函式依賴

| 層 | 主要函式／類別 | 上游 → 下游 | 邊界／副作用 |
|---|---|---|---|
| JSON 安全 | `strict_json_loads`、`_unique_json_object`、`_reject_json_constant` | CLI/MCP/SDD/metrics → strict parser | 拒絕 duplicate keys、NaN/Infinity；呼叫 payload 有 bytes/shape limits。 |
| Token/Context | `TokenEngine.prepare`、`estimate_tokens`、`redact_secrets`、`stable_hash` | CLI `context`／MCP `via.token.prepare` → in-memory transform | Token 數是 heuristic，不等於 provider tokenizer/billing；有損抽取 opt-in；內容不持久化。 |
| 8 VIA Skills | `run_skill` → 八個 `via_*` runner | CLI/MCP → 純函式 Skill → structured status/data | 不呼叫模型或 Agent，不寫 repo；validation 缺資料回 `NEEDS_INPUT`/`INVALID_INPUT`。 |
| AST/模組 | `scan_project` → `_read_regular_file_nofollow` → `scan_source` → `_SymbolVisitor`/unsafe-call visitor | CLI/dashboard → AST index → metadata view | 不 import/exec 被掃描 source；限制目錄、候選檔、單檔 bytes、總 bytes。 |
| Dependency design | `via_architect` → `_topological_sort` | Architect Skill → stable dependency order | heap 保留 lexical deterministic order；missing/cycle 是 review，不執行程式。 |
| Mount/TriEngine | `discover_mounts`、`validate_mount`、`route_file` | CLI/dashboard → E1/E2/E3 routing metadata | 只驗 schema／路由，不啟動命令或載入 mount 程式。 |
| SSOT | `build_ssot_payload`、`merge_ssot`、`register_ssot`、`_atomic_json_write` | internal data → namespace merge / guarded writer | 支援函式仍在單檔中；本版本公開 CLI/MCP 不提供 register/apply 命令。測試只用 temp dirs。 |
| Metrics | `_normalize_metric_record`、`append_metric`、`read_metric_log` | optional internal writer / Dashboard reader | writer 是受限 append helper；公開唯讀 CLI/MCP 不提供 metrics append；讀取最多 16 MiB/10,000 events。 |
| SDD | `_sdd_template`、`_walk_for_forbidden_sdd_keys`、`validate_sdd_bridge` | stdin/MCP → schema/security validation | iterative walker；超限 fail closed；不執行 test descriptions／deploy instructions。 |
| GitHub/VIA/VCGC status | `inspect_local_git_metadata`、`fetch_pinned_github_main_metadata`、`via_html_ui_static_status`、`vcgc_static_status` | local metadata → status report | GitHub remote 僅在明確 `repo-check --remote` 時對固定 branch metadata 做 GET；VCGC status 是靜態文件掃描，不是連線。 |
| MCP | `MCPReadOnlyServer.handle`、`_validate_mcp_arguments`、`_mcp_serve`、`_write_mcp_line` | stdio JSON-RPC → one in-process allowlisted handler → one framed response | 同步序列處理；輸入／輸出各 1 MiB；session 300 messages/300s，tool-call 30。 |
| Dashboard/CLI | `build_dashboard_data`、`make_interactive_dashboard`、`upgrade_dashboard_document`、`_cmd_dashboard`、`_build_unified_parser` | tests/AST/metrics/mount/SSOT snapshot → local HTML | file:// 離線頁，無外部資源；輸出必須在掃描根目錄外，覆寫停用。 |
| Remote VCGC safety tool | `vcgc_remote_preflight.py` 的 `validate_profile`、`tls_probe`、`check_tools_list` | local profile/export → opt-in TLS-only / exact-name comparison | 與 VIA MCP server 分離；預設零網路；不做 OAuth、不做 MCP handshake、不呼叫工具。 |

## 2. 原 ZIP 的 22 個成員：逐檔用途與依賴

原始 release manifest 確認有 22 個檔案。下表的「原版狀態」是指原 ZIP 內的 v1.0.0 資產，不表示它們都被納入最新 hardened package。新 package 會使用一致版本的 source/dashboard/report，排除舊 snapshot。

| # | 原 ZIP 內路徑 | 用途與依賴關係 | 原版狀態／最新版處理 |
|---:|---|---|---|
| 1 | `VIA_Agent_OS_Latest/MANIFEST.json` | 記錄其他成員的 bytes 與 SHA-256；自身不列自身 hash。 | 原版 manifest 對應舊 source；新封裝需重算所有 hash。 |
| 2 | `VIA_Agent_OS_Latest/README.md` | 安裝、selftest、Dashboard、stdio MCP 說明；依賴 source 的 CLI interface/狀態。 | 原 README 記錄 34/34、23 cases、舊 source SHA；需以 48/48、27 cases、v1.0.2 更新。 |
| 3 | `assets/via_agent_os_bounded_concurrency.mmd` | 並發圖源；描述舊版 serial scan 與可選 worker。 | 已由 hardened 圖源取代，加入 128 MiB/10k dirs/MCP budgets。 |
| 4 | `assets/via_agent_os_bounded_concurrency.png` | 第 3 項 Mermaid 的 rendered PNG。 | 必須和新版 `.mmd` 成對更新；舊 PNG 不可當作目前 limits。 |
| 5 | `assets/via_agent_os_dashboard_overview_preview.png` | Dashboard overview 截圖，不是 runtime dependency。 | 舊測試計數快照；如要展示 v1.0.2 應重新截圖。 |
| 6 | `assets/via_agent_os_large_project_memory_profile.png` | 從舊 profile JSON 繪製的 Python traced peak 圖。 | 對應舊 source/profile；新版已產生 hardened profile/圖。 |
| 7 | `assets/via_agent_os_memory_report_mobile_preview.png` | 舊 memory report 手機版預覽圖。 | 靜態展示素材；舊 source snapshot，需和新版 HTML 重新截圖才可沿用。 |
| 8 | `assets/via_agent_os_performance_chart.png` | 舊版同輸入性能比較圖；依賴舊 comparison JSON。 | 不應與 hardened source 串用；新版 comparison/chart 另產。 |
| 9 | `assets/via_agent_os_system_flow.mmd` | 原版功能／安全流程圖源。 | 靜態說明文件；新版 hardened system-flow 圖源已取代。 |
| 10 | `assets/via_agent_os_system_flow.png` | 第 9 項 Mermaid render。 | 舊流程快照；需與新版圖源成對。 |
| 11 | `assets/via_agent_os_token_calculator_demo.png` | 舊 Dashboard 的 Token 計算器截圖；沒有執行依賴。 | Demo 輸入為人工試算，不是 provider usage；視覺快照需重新截圖。 |
| 12 | `assets/via_agent_os_token_flow.mmd` | Token heuristic／provider usage 分流圖源。 | Token 語義仍成立；打包前仍需核對文字／source version。 |
| 13 | `assets/via_agent_os_token_flow.png` | 第 12 項 Mermaid render。 | 靜態圖；只依賴圖源，不是 runtime code。 |
| 14 | `config/mcpServers.example.json` | Agent host 的**本機 stdio** MCP 設定，指向 Python source 和 `mcp serve`。 | 不是遠端 VCGC HTTP 設定；解壓後需填絕對路徑，host credentials 不放 JSON。 |
| 15 | `dashboard/via_agent_os_unified_readonly_dashboard.html` | Python 產生的離線互動 snapshot；內嵌 CSS/JS/data，沒有伺服器依賴。 | 原版與 v1.0.0 source/report 同步；已由 hardened dashboard 取代。 |
| 16 | `reports/via_agent_os_large_project_memory_concurrency_analysis.html` | 舊版完整視覺化記憶體／並發報告；依賴舊 source SHA、profile、chart、diagram。 | 舊 34-test snapshot；最新版需用 hardened profile 重新生成。 |
| 17 | `reports/via_agent_os_large_project_memory_concurrency_analysis.md` | 同第 16 項的 Markdown source/reference；相對連結依賴 ZIP 內資產。 | 同第 16 項，source/profile 摘要過時。 |
| 18 | `reports/via_agent_os_performance_analysis.html` | 舊版互動性能報告；依賴 comparison/profile JSON 與圖。 | 舊 34-test/source hash；不能作為 hardened performance evidence。 |
| 19 | `reports/via_agent_os_performance_analysis.md` | 同第 18 項的人類可讀源報告。 | 同第 18 項。 |
| 20 | `reports/via_agent_os_performance_monitoring_data.json` | 舊版 machine-readable performance/profile summary。 | 舊 source hash；新版本需保留測量範圍與 caveats 並重算。 |
| 21 | `reports/via_agent_os_performance_test_report.json` | 舊版自測／Skill acceptance 及 source hash。 | 34/34、23/23；由 hardened 48/48、27/27 報告取代。 |
| 22 | `src/via_agent_os_unified_readonly.py` | 原版單檔 runtime；原 ZIP 244,529 bytes，SHA-256 `c33449f1a96649cb0481ac7fa01ea908357c2409b41e89d8ab3f6cc68c40a62b`。 | 已被 v1.0.2 hardened source 取代；舊檔保留於原 ZIP，但不應被新版 README 誤指為 latest。 |

### 文件間的有向依賴

- `MANIFEST.json` → 封裝內每個檔案的 bytes/hash。
- `README.md` → source CLI、MCP config、Dashboard、test/performance reports；source/hash 更新時必須同步重寫。
- `.mmd` → 對應 `.png`；PNG 是呈現資產，不是程式依賴。
- `mcpServers.example.json` → 解壓後 `src/via_agent_os_unified_readonly.py` 的絕對路徑；它只設定本機 stdio MCP，不啟用 VCGC remote。
- Dashboard HTML → 產生時 snapshot 的 AST index、tests、Skills acceptance、mounts、SSOT summary、metrics；HTML 本身離線可用，但不會自動刷新。
- performance HTML/Markdown/chart → profile JSON、同輸入 before/after comparison、test report 與圖源；要能稱為「目前版本」必須 source SHA 一致。
- test report → 固定 source SHA + selftest/acceptance 報告；source 改一個 byte，報告即需重跑。

## 3. 實際同步與並發行為

![hardened scan 與 MCP 有界並發圖](../assets/via_agent_os_hardened_concurrency.png)

### 現況：同步、序列，不是 async server

目前單檔中沒有 `async def`、`asyncio`、thread pool 或 process pool。`scan_project()` 依排序後路徑逐檔讀取，一次只把一個 file 的 source/AST 送入 `scan_source()`；每份 AST 結果保留為 metadata。MCP stdio 只有一個 stdin reader，讀一行、strict parse、同步 `handle()`、完整寫一行 stdout，之後再讀下一筆。即使 host 同時送出多筆 request，這個 process 仍序列處理；沒有並行 tool call。

### 新增 hard limits

| 範圍 | v1.0.2 邊界 | 行為 |
|---|---:|---|
| Python 目錄遍歷 | 最多 10,000 visited directories | 超限停止並標記 `directory_limit_reached`。單一超寬目錄在 `os.walk` 交出 `dirs/names` 時仍會先 materialize，這個殘餘風險尚未完全消除。 |
| Python candidates | 最多 1,500 `.py` 路徑 | 確定性排序；symlink 和排除目錄略過。 |
| 單一 source | 最多 2 MiB | bounded no-follow file read；`scan_source()` 對 UTF-8 bytes 在 `ast.parse()` 前拒絕超限。 |
| 全專案 source | 最多 128 MiB 累積 bytes | 達上限即停止並標記 `total_byte_limit_reached`；若檔案在 `stat` 後被並行改大，單次最多可能多讀 2 MiB 才能做 post-read check，該檔不會再送 AST。 |
| AST visitor | 最多 50,000 nodes、depth 200、最多 250 symbols/file | node/depth check 發生在 `ast.parse()` 建 tree 後；不是 OS-level RSS ceiling。 |
| SDD walker | 50,000 nodes、depth 64、500 items/list、1,000 findings | iterative traversal；超限 fail closed。 |
| metrics | 最多 16 MiB、tail window 10,000 rows | 二進位逐列 decode/parse，保留最近 physical rows；內容不保存到 Dashboard。 |
| MCP request | 每行最多 1 MiB；總量 300 messages 或 300 s；最多 30 tool calls | JSON recursion error 被轉成 parse error；budget 用盡後 session 結束。時間閘在 request 邊界生效，不能中斷已開始的同步 call。 |
| MCP response | 最多 1 MiB | 超限改回小型 `-32002` error frame，不寫部分 JSON。 |
| Remote profile preflight | profile 128 KiB、tools/list 1 MiB、JSON 20,000 nodes / depth 64 / 1,000 list items | default offline；TLS-only 是明確 opt-in，無 HTTP/OAuth/MCP tool call。 |

### 未來並發建議，不是已啟用功能

AST parse、visitor、compile／JSON 序列化是 CPU-heavy；`asyncio` 只改善 I/O wait 協調，不會自行加速這些 CPU 工作。若實測證明掃描以 disk I/O wait 為瓶頸，可在另一次安全審查後評估小型有界 `ThreadPoolExecutor`：初始 `W=2`、in-flight task ≤ `W`、queue ≤ `2W`、限定總 input bytes、保留 ordinal 排序結果。不要先把所有 file 讀入 queue，也不要 `gather()` 全專案任務。

CPU process worker 會新增子程序、序列化複本及 worker runtime/RAM 倍增，與現行 no-subprocess default 不相容；沒有重新核准 sandbox/resource-limit contract 前，**不得預設開啟 ProcessPool**。要估 worker 數，先收集近上限 workload 的 process RSS/PSS p95，使用 `W_max = floor((RAM budget − parent peak − reserve)/(worker peak p95 + per-task buffers))`。目前不據單檔 tracemalloc 推算大型 repo 可用的 W。

## 4. 函式覆蓋與本輪補強結果

這一輪除回看所有核心入口，亦檢查了**未被先前 dashboard/性能分析涵蓋的 transport 與 scan limits**，發現並修補：

1. `scan_project()` 原先只有每檔 2 MiB／最多 1,500 files，理論 serial source bytes 可達 3,000 MiB，而且沒有目錄數及總 bytes cap。新增 10,000 visited-dir、128 MiB aggregate source budget、quota 型別驗證、bounded no-follow reads、source bytes/report flags、walk-error details cap。
2. MCP 原先有 tool-call 30 次與 300 秒 gate，但 discover/list/notification/格式錯誤行沒有共用 session-wide message budget。新增 300 messages/300 seconds 的 session gate，budget 達上限停止讀取。
3. MCP strict JSON parsing 可能遇到極深巢狀 JSON recursion。現在 `_mcp_serve()` 捕捉 `RecursionError` 回覆 parse error，不讓 process crash。
4. MCP stdout 原先沒有獨立 output size cap。新增 1 MiB response cap；超限只回傳有限大小 error frame。
5. 遠端 VCGC preflight 的 JSON 結構檢查原先使用 recursive walk。新增 iterative profile walker、20,000 node／depth 64／1,000 items per list limits，並將 parser recursion overflow 轉成安全拒絕。
6. 加入對應 regression：專案總 bytes／dir cap／quota type、MCP total message budget、deep JSON、output cap、remote profile deep/list structure，以及 CLI tools/list allowlist pass/mismatch。

### 仍在 source 中、但不由本版本 public CLI/MCP 暴露的 helper

`append_metric()`、`register_ssot()`、`_atomic_json_write()`、舊 wrapper `cmd_usage_add()`／`cmd_bootstrap()` 在單檔內仍存在，主要供內部/相容/隔離測試使用；本版本 unified parser 沒有公開 `usage-add`、`bootstrap` 或 SSOT apply command，MCP tool allowlist 也沒有 write tool。這是「公開 entrypoint read-only」而非「Python module 裡完全不存在任何 write-capable helper」；直接 import 並自行呼叫 low-level helper 的程式仍須把 root/path/payload 當成敏感操作處理。測試寫入只限自動清除的 TemporaryDirectory。

## 5. 效能／記憶體數據（source SHA 與測量範圍）

![同輸入效能與 tracemalloc 比較](../assets/via_agent_os_hardened_performance.png)

比較基線為原優化前單檔與 hardened source；每組使用相同本機 deterministic fixture、暖身後重複計時，結果逐欄相同。這是 code-level synthetic microbenchmark，不能外推為生產 SLA。

| 工作負載 | 基線中位數 | hardened 中位數 | 時間變化 | 輸出 |
|---|---:|---:|---:|---|
| ASCII estimator，1,000,000 chars | 121.212 ms | <0.001 ms | 快 100.00% | 相同 |
| CJK estimator，125,000 chars | 15.721 ms | 16.364 ms | 慢 4.09%（本次視為量測噪音／持平） | 相同 |
| TokenEngine prepare，1 MB ASCII | 331.553 ms | 76.269 ms | 快 77.00% | 相同 |
| `scan_source`，800 synthetic functions | 161.928 ms | 115.370 ms | 快 28.75% | 相同 |
| metrics，10,000 rows／14.7 MB | 157.854 ms | 145.501 ms | 快 7.83% | 相同 |
| topology，15,000 nodes | 43.653 ms | 25.798 ms | 快 40.90% | 相同 |

| same-input Python allocation peak | 基線 | hardened | 變化 |
|---|---:|---:|---:|
| TokenEngine prepare 1 MB | 1,001,443 B | 1,001,411 B | +0.00%（峰值配置下降為正） |
| AST scan 800 functions | 11,469,799 B | 11,469,815 B | -0.00%（峰值配置下降為正） |
| metrics 10,000 rows | 29,946,564 B | 5,629,601 B | +81.20%（峰值配置下降為正） |

最終 source profile（非完整大型專案壓力測試）：

| 操作 | 中位時間 | tracemalloc peak |
|---|---:|---:|
| 48 項 selftest | 50.190 ms | 3,557,425 B（3.39 MiB） |
| 27-case Skills acceptance | 4.513 ms | 141,035 B（0.13 MiB） |
| 1 MB TokenEngine.prepare | 76.513 ms | 1,001,007 B（0.95 MiB） |
| scan current 266,514-byte Python source | 354.727 ms | 21,792,213 B（20.78 MiB） |
| scan 1-file temporary project | 326.033 ms | 23,364,938 B（22.28 MiB） |
| 10k-row metrics fixture reader | 142.971 ms | 5,630,482 B（5.37 MiB） |
| end-to-end Dashboard snapshot | 404.809 ms | 23,440,325 B（22.35 MiB） |

`tracemalloc` 只記錄 Python allocation，不等於 process RSS/PSS；以上也沒有量測 1,500 files 或接近 128 MiB aggregate 的完整 repository。多檔結果 metadata 會累積，單一超寬目錄仍可使 `os.walk` 的目錄名稱表先佔記憶體；下一個最有價值的工作是使用受控真實專案量測 process RSS/PSS，再決定是否要 incremental output 或 worker pool。

## 6. Remote VCGC 的依賴邊界

遠端 VCGC profile、preflight script 和測試檔與 VIA 單檔分開；不是 22-file release 中現有 MCP remote transport 的延伸。`vcgc_remote_preflight.py`：

- Offline profile validation：不查 DNS、不開 socket。
- 選擇性 `--tls-check`：只針對 profile 指定 endpoint 執行 DNS/TCP/TLS；不送 HTTP、OAuth token、MCP message 或資料。
- `--tools-json`：只讀本機 Agent host 匯出的 `tools/list` JSON，比對精確名稱；不呼叫工具。名稱比對不能證明 tool 語意唯讀，必須由 VCGC owner 另驗 schemas 和 server-side ACL。
- 真正 OAuth/MCP handshake/canary 由使用者核准的 Agent host 完成；目前沒有 endpoint/issuer/scope/credential，因此 live integration 為 `NOT PERFORMED`。

完整步驟、CLI 命令、回復程序與來源連結見 `../docs/vcgc_remote_secure_integration_guide.md`。

## 7. 簡要重現命令

在解壓後封裝目錄中：

```bash
python3 -m py_compile src/via_agent_os_unified_readonly_hardened.py vcgc_remote_preflight.py test_vcgc_remote_preflight.py
python3 src/via_agent_os_unified_readonly_hardened.py selftest
python3 src/via_agent_os_unified_readonly_hardened.py skills test
python3 test_vcgc_remote_preflight.py
python3 src/via_agent_os_unified_readonly_hardened.py mcp config-example
```

最後一條只列印 local stdio 設定，不寫 Agent host config。實際 remote profile 需複製 placeholder 範本，使用核准 endpoint 和 scope，且不放 credential。
