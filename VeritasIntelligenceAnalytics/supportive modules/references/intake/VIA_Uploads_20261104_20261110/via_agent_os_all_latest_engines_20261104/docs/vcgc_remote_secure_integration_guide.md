# VCGC 遠端 MCP 正式安全對接指南

**文件用途：** 依目前 hardened VIA Agent OS 單檔提供安全設定與驗證流程。此文件與測試工具不會自行註冊連線、不登入、不送 OAuth token，也不呼叫 VCGC 工具。

## 1. 現況與重要區別

`tonykuni/movies-dataset` 是指定的 GitHub repository 識別，不是可直接連線的 VCGC MCP endpoint。此次工作環境沒有該 repository 的本機 checkout，也沒有 VCGC 遠端 MCP URL、OAuth issuer、client 註冊資料或帳號授權；因此目前**不能宣稱已與 VCGC 實際連線或完成遠端端到端測試**。

hardened Python 程式中的 `vcgc-status`／`via.vcgc.status` 是靜態狀態回報；MCP server 是本機 stdio read-only adapter，不是 remote Streamable HTTP client。遠端工具的 OAuth 互動與 MCP 連線要由使用者所選的 Claude／其他 Agent host，或 VCGC 官方 gateway 完成。`mcp config-example` 只列印本機 stdio 設定範例，並不改寫任何 Agent 設定。

建議採「**本機 preflight → Agent host 授權 → 只讀 tools/list 比對 → 經核准的小範圍 canary → 持續監控**」順序。只有使用者提供實際 endpoint 並在其 Agent host 完成登入後，才能做真正的遠端整合測試。

## 2. 上線前請由 VCGC 管理者提供／核准

1. 固定的 `https://` MCP endpoint，包含實際 path；不得以搜尋、URL redirect 或猜測服務名稱代替。
2. MCP transport、支援的 protocol version、MCP server 身分和 server owner。若服務版本不相容，先由 VCGC/host 管理者確認，不要在 client 端猜版本。
3. OAuth issuer URL、resource/audience 值、正式 OAuth scope 名稱，以及該 scope 對應的 server-side ACL。scope 必須只覆蓋核准的 read-only project/repository 和欄位。
4. 遠端 `tools/list` 的脫敏 JSON 匯出，及預期的精確唯讀 tool name allowlist。請不要把 access token、refresh token、cookie、Authorization header 或個人資料放進匯出檔。
5. TLS CA／企業代理設定（若需要）、網路 egress allowlist、稽核事件位置、rate limit、憑證輪替和服務停用／撤銷程序。
6. 經核准的測試專案 ID、最小可讀欄位，以及明確禁止讀取的資料範圍。若 server 端含 write/delete/execute/admin tool，須由 server-side ACL 移除；client-side UI 隱藏不等同安全隔離。

## 3. Profile 範本與本機設定

先複製 `VCGC_REMOTE_PROFILE.example.json` 為本機私有檔，例如 `VCGC_REMOTE_PROFILE.json`。只填入由 VCGC 管理者確認的 host/path、issuer/resource、read-only scope、approved data scope 與精確 tool names。不得新增任何 credential 欄位。

```bash
cp config/VCGC_REMOTE_PROFILE.example.json VCGC_REMOTE_PROFILE.json
chmod 600 VCGC_REMOTE_PROFILE.json
```

範例中的 `VCGC_HOST`、`AUTH_HOST`、`<...>` 都是刻意無效的 placeholder；在全部替換前應該驗證失敗。`enabled` 必須維持 `false`；`tls_verify=true`、`allow_redirects=false`、`write_tools_enabled=false`、`allow_private_network=false` 均為預設安全值。OAuth token 由 Agent host 的標準登入／credential store 管理，不放入 profile、環境變數範例、測試 JSON 或 ZIP。

設定檔先離線驗證：

```bash
python3 vcgc_remote_preflight.py --config VCGC_REMOTE_PROFILE.json
```

此命令只讀取本機 profile，進行 schema、HTTPS、host allowlist、issuer/resource、read-only scope、credential-key、tool allowlist、size 與 symlink 檢查；它不做 DNS、TCP、TLS、HTTP 或 MCP handshake。必須得到 `CONFIG_VALID` 且 `network_requests_performed` 為 0 才能進下一步。

## 4. 遠端 TLS 與 MCP allowlist 驗證

### 4.1 可選 TLS preflight

只有在網路管理者允許、endpoint 已確認且使用者同意從執行主機發出連線後，才執行：

```bash
python3 vcgc_remote_preflight.py --config VCGC_REMOTE_PROFILE.json --tls-check
```

它只解析設定中**單一固定 endpoint** 的 DNS，拒絕非 global IP（除非 profile 明確允許已核准的 RFC1918 network），然後做 TCP connect 與 TLS certificate/hostname verification。它不送 HTTP request、不送 OAuth token、不執行 MCP `initialize`；成功時結果欄位為 `tls_probe.status=TLS_OK`，**不代表** OAuth、MCP handshake 或 tool call 成功。預設拒絕 loopback、link-local、wildcard host、userinfo、query、fragment、HTTP、redirect 和未核准 private IP。

### 4.2 tools/list 精確 allowlist

由已登入的 Agent host／官方 VCGC client 完成正常 MCP handshake 後，將 `tools/list` response 匯出為 `vcgc_tools_list.json`。匯出前請刪除 token、headers、session ID 和任何使用者資料，只保留 MCP tool schema。執行：

```bash
python3 vcgc_remote_preflight.py \
  --config VCGC_REMOTE_PROFILE.json \
  --tools-json vcgc_tools_list.json
```

成功時頂層 `status` 仍為 `CONFIG_VALID`，並且 `tools_allowlist_check.status` 為 `PASS`；`unexpected`、`missing` 必須為空陣列，`duplicate_actual_names` 必須為 `false`。這個測試只比對工具名稱；**不呼叫任何工具，也不會從名稱或描述自動證明其語意為唯讀**。由 VCGC owner 逐一檢視每個 tool 的完整 input/output schema、副作用、scope/ACL 與 audit behavior，並在 server side 移除 write/delete/execute/admin 能力。若名稱多一個、少一個或重複，先停用連線並由管理者更新 ACL/profile，不得用 wildcard 或「先全部允許」繞過差異。

### 4.3 官方 host 中啟用

在所選 Agent host 的設定介面新增遠端 MCP server，填入核准 endpoint，使用該 host 支援的 OAuth 登入流程。每個 Agent／使用者分別註冊自己的 principal 和授權；可共用的是此 profile 的非秘密政策欄位和精確 allowlist，**不可共用 bearer token、refresh token 或 cookie**。如 host 有 tool-level approval、project scope、network policy 或 audit logging，全部啟用。

不要把本機 `mcp config-example` 的 stdio 命令直接當成遠端 HTTP 設定；兩者傳輸與身份驗證不同。建議先只對單一核准的測試專案展示 tool list 和 metadata read，確認結果來源、scope、稽核紀錄與無副作用後，再逐步擴大 read scope。

## 5. SDD / VIA 對接檢查

VIA 的 SDD bridge 只驗證一個 JSON contract；不會執行 SDD 中的 test commands 或部署內容。先取本機模板並另存於專案之外，再由 owner 填入經核准的欄位：

```bash
python3 src/via_agent_os_unified_readonly_hardened.py sdd template > sdd.contract.json
cat sdd.contract.json | python3 src/via_agent_os_unified_readonly_hardened.py sdd validate
cat sdd.contract.json | python3 src/via_agent_os_unified_readonly_hardened.py deploy-preflight --sdd-stdin
```

最後一條命令即使通過，也只會回報 `SAFE_READ_ONLY_SCAFFOLD`；它不是 production deployment approval。任何 SDD 輸入超過容量／深度／節點限制、包含禁止的 destructive/write/deploy 指令或缺少必要資訊，都應保持 BLOCKED／REVIEW，而非自行猜測。

## 6. 可重複測試命令與目前測試狀態

同目錄提供 `test_vcgc_remote_preflight.py`；套件使用標準函式庫、mock DNS/TLS、temporary directory 與合成工具清單，不會聯外：

```bash
python3 -m py_compile vcgc_remote_preflight.py test_vcgc_remote_preflight.py
python3 test_vcgc_remote_preflight.py
python3 src/via_agent_os_unified_readonly_hardened.py selftest
python3 src/via_agent_os_unified_readonly_hardened.py skills test
```

本次離線驗證：hardened VIA v1.0.2 單檔 **48/48 selftests PASS**；8 個 Skills **27/27 acceptance PASS**；remote profile/TLS/tools-list preflight **20/20 unit tests PASS**。這些結果驗證本機程式與拒絕條件，不代表遠端 VCGC 服務可用，也不代表成功 OAuth 登入或 remote MCP handshake。

## 7. 上線 gate、監控與撤銷

**啟用前 gate：** endpoint、TLS hostname、OAuth audience/resource 和 scope 與 VCGC owner 文件一致；tools/list 等於精確 allowlist；沒有 write/delete/execute/admin tool；本機 VIA tests 通過；測試專案和 read fields 有書面核准；使用者明確核准 remote OAuth 授權。

**啟用後監控：** 以稽核 log 比對 actor、tool name、時間、approved project、scope、輸出大小與 rate-limit；異常 tool name、資料越界或 redirect 即停用 connector。Token usage 要從 provider/host 真正回報欄位取得；VIA heuristic token estimates 不能代替 VCGC 或模型帳單。

**回復／撤銷：** 在 Agent host 停用 remote connector、撤銷 OAuth grant/refresh token、移除 server-side ACL、停掉已核准的 egress，並檢視稽核紀錄。若曾輸出 credential，依 VCGC 流程立即輪替；本指南產生的檔案不保存 credentials。

## 8. 限制與官方參考

- 未提供真實遠端 URL／OAuth issuer／scope，也未執行 live TLS、OAuth、MCP handshake 或 VCGC tool call；這些仍是正式上線前必要工作。
- 指定 GitHub repo 的 metadata check 與 remote VCGC MCP 是不同路徑；本機 `repo-check --remote`（若明確呼叫）只 GET 固定 GitHub branch metadata，不下載 repository contents 或 dataset。
- MCP transport 與安全需以 VCGC/Agent host 實際版本核對；以下為官方規格入口：
  - [MCP Streamable HTTP transport](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
  - [MCP authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)
  - [MCP security best practices](https://modelcontextprotocol.io/specification/2026-07-28/basic/security_best_practices)
