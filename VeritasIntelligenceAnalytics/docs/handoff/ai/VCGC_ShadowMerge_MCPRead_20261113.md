# VCGC 影子整併 + MCP 讀檔三動詞(2026-11-13)

> 操作員令:「接進 VCGC 並補上 MCP 的 read slice digest」(前文:「整合要先複製不影響舊的 … 合併去重測試」「VCGC TOKEN SAVING 工具看要如何整合 搭配 GRAPHIFY OMNIROUTE」)
> 需求 VCGC-REQ223(PARTIAL)· VCGC-REQ224(COVERED)· 工作流 VCGC-WKF043 · WKF042-STP004

## 一、先量再寫(L116)

| 既有 | 做什麼 | 為什麼不夠 |
|---|---|---|
| CGC_MDL092 / 166 / 045 / 086 / 143 | 稽核冊 · 稽核四庫 · 去重索引 · 雙位置正典裁定 · 修合併衝突 | 沒有一支做「兩支引擎逐定義比對 → 影子合併 → 零遺失證明」 |
| PEIS 函式正規化 | 跨檔分群 | 字串常數一律遮成同一個值:只差一條路徑 / 一句 SQL 的兩支會被當成重複 → 拿來去重違 L67 / L75 |
| token 工具 `chain` | 薄尾版本鏈 | 正好拿來判薄尾,不另寫尺 |
| `via-vcgc` MCP(CGC_MDL279 v0102) | 16 個只讀動詞 + 收據 | 有 `vcgc_token` 卻沒有 read / slice / digest → 經 OmniRoute 進來的 AI 只能整檔讀 |

## 二、新件

**CGC_MDL281_ShadowMerge v0100**(MDL280 已被 `optimistic-goodall-yhalc5` 分支的 AgentOSHub 用掉)

```
VIA_FROM_VCGC=YES python3 "$V" run CGC_MDL281_ShadowMerge compare <A.py> <B.py> [--json]
```

- 原檔 sha256 記帳 → 影子副本唯讀 → 結束再量(變了 rc 2)。產物只在 `VIA_Reports/shadow_merge/<UTC>_<sha8>/`。
- 分類:SAME(含常數完整 AST 相同,可去重)· DOC_ONLY · SAME_SIG_DIFF_BODY · DIFF_SIG(後兩者**不准遷**,L75)· ONLY_A · ONLY_B。
- 合併候選:環繞斷言(影子 A sha + 錨點行)· 避開 `__main__` · 用到合併檔沒有的名字 = RISK 不搬。
- 證明:parse + compile · A 全數原樣 · B 每個定義原樣在或列「未遷」附理由。全對 = PROVEN_ZERO_LOSS(rc 0),否則 BLOCKED_NEEDS_RULING(rc 1)。
- LibCST:本境沒裝,AI 不裝套件 → 走標準庫 ast(判準相同)。有 LibCST 時只拿來取帶前置註解的原文;**這條路沒實測**。

**CGC_MDL279_MCPServer v0103**(薄尾;`.mcp.json` 原本還停在 v0101,已指到 v0103)

- `vcgc_read {path, depth?, if_etag?}` · `vcgc_slice {path, name}` · `vcgc_digest {path}`,全部委派鎖版 token 工具(鎖冊 sha 不符即停)。
- 路徑:先判倉內外(倉外一律拒,不透露存在與否)· `.git/` `private/` `.env*` 金鑰檔拒讀 · 參數照 argv 傳不經殼。
- rc 0 / 1(紅日誌)/ 3(NODATA)是答案不是錯。

**CGC_MDL245_SDDValidator v0108**(順手修的既有故障)

- 自 2026-11-10(REQ222 把 `../VIA_MCP_Engine/…` 登進 WKF042)起,SDD 在 v0100 `rel()` 丟 ValueError 整支炸 → closeout 停在 ⑥,沒有人能 checkpoint。乾淨 main 上重現。
- v0108 只換 `rel()`:VIA 根內同 v0100;倉根內 VIA 根外回 `../<相對倉根>`;倉外照舊丟錯。`sdd` 交接案回到 rc 0(尾版鏈 v0108→v0100 全 PASS)。

## 三、實測(容器 2026-11-13)

| 項 | 結果 |
|---|---|
| CGC_MDL281 自測(經 VCGC run) | 13/13 |
| 真檔 MergeMedic v0101 × v0104 | SAME 11 · SAME_SIG_DIFF_BODY 4 · BLOCKED_NEEDS_RULING · 原檔未動 |
| 真檔 MergeMedic v0104 × v0105 | chain 判 v0105 薄尾(glob 取前版)· ONLY_B 兩支 RISK 不搬 |
| MCP v0103 自測 | 本版 10 項 + v0102/v0101/v0100 鏈 rc 0 |
| MCP stdio 真握手 | tools 20(+3)· vcgc_slice 回定義 · 倉外拒讀 |
| registry-sync --apply | 新 38 · 變 113 · 退役 606(含 11-10 起累積漂移)· 冊遺失 0 · 改號 0 |
| 編號 --scope | +180 列 · 遺失 0 · 改身分 0 · 重號 0 |
| handoff test | C-shadow-merge-v0100 / C-mcp-server-v0103 / sdd 全 rc 0 |
| VCGC test --quick | 紅 0 · 黃 2(既有:交接閘 RED · 容器無 pwsh)· case 279/279 · workflow 180/180 |
| VCGC test(整輪) | 380 站:綠 300 · 黃 20 · 紅 60;本批 6 站全綠。**60 紅站逐站在乾淨 main(9ed1bb138)重跑 → 60/60 同樣非 0 = 全為既有**(多為容器缺件:reportlab · pydantic 等)|

## 四、還開著(不是本批造成的,只報不代改)

- SDD 仍 RED:VDF-WKF016/017、VRN-WKF010 欄位不齊(他系統的冊,互不干涉)· X-REQ 歸屬指到不存在的檔(REQ206/207/208)· `VIA_MCP_Engine_v0103.py` 在 VIA 根外,未註冊 / 未編號 · X-LOCK 14 處尾版換了要重驗。
- 交接閘本來就 RED(244 項)→ checkpoint 會被擋。
- ssot panorama「上下連結@VCGC」:前測是「正主呼叫失敗 ValueError」(當機);SDD v0108 之後同一盞改為真判定「中央結構檢 RED」(上列他系統 / 既有項),不再當機。燈數前後同為紅 1 · 黃 9。

## 五、待操作員

- **VCGC-REQ223:rulings**:指定要整併的家族 → `compare` → 逐群裁定 BLOCKED 的群,才出新版正典(L75 · L61)。
- **VCGC-REQ224:remote-platforms**:桌機 Claude Desktop 重新載入 MCP;遠端 ChatGPT / Manus / Copilot web 走 `VIA_MCP_Engine parity --write` + HTTPS 隧道。
