# VIA 交接續頁(latest)

本檔首次進 git:2026-11-07。此前各輪的 §1~§36 **不在本檔**,而是記在每輪自己的
`docs/handoff/ai/*.md`(那些都已在 main;例如 `VCGC_MCP_v0101_activation_20261107.md`、
`VIA_FiveDay_Panorama_20261107.md`、`VIA_Closeout_Audit_Matrix_20261106.md`)。
之前幾輪曾在雲端容器裡維護同名檔但**從未提交**,容器回收即消失 —— 本輪把它納入版控,
以後只往後 append,不改既有段。段號沿用歷史編號(本輪 = §37),中間缺號指向上述各輪文件。

## §37 工作流圖接真收據 + 五日全景 + MCP SYNC(操作員 2026-11-07 大令 · VCGC-REQ194)

**`docs/handoff/ai/VIA_WorkflowViz_v0100.py`** —— 功能資訊流 + Interface 架構的工作流圖,
三表(nodes / edges / metrics_ts)**全部由本倉五系統自己的收據與冊生成**,不是 demo:
盤點冊 330 站 · 功能帳 760 列 / 338 id(2026-09-30 起)· 串測 `TEST_latest.json` 站燈與秒 · 交接冊 `work_items`。

```bash
# 桌機 / 容器一行(DuckDB 要非隔離模式才看得到 user site-packages)
python "...\VeritasIntelligenceAnalytics\docs\handoff\ai\VIA_WorkflowViz_v0100.py" all --via "...\movies-dataset" --top 150
# 只看資料合約 + DuckDB DDL(不寫檔):… schema      自測:… --selftest
```

輸出在 `<VIA>\VIA_Reports\workflow_viz\`:`VIA_WorkflowViz.html`(離線單檔 397 KB · 三視圖 + 節點下鑽 +
車道×種類矩陣 + seaborn 熱力圖)· `VIA_WorkflowViz.mmd`/`_mermaid.md` · `workflow.duckdb` ·
三表 `.json`/`.csv`/`.parquet` · `metrics_ts.json`(累積庫)· `metrics_ts.ddl.sql` · `WORKFLOW_VIZ.json`。

零安裝律下的技術選擇:容器無 networkx / graphviz / plotly / dot → 自己算
(Tarjan 縮點分層 + 冪法 PageRank + 內嵌 SVG/JS);seaborn / duckdb / pyarrow 有就真用。
**快照與累積庫分開**:`persist` 只寫 `metrics_ts_snapshot.*`;累積庫與 DuckDB 的 `metrics_ts`
只由 `etl` anti-join(鍵 `node_id + ts + run`)累加,**只增不刪**。

容器實測:節點 933 · 邊 983 · 指標 761 · 真環只有 `lane:VCGC ⇄ lane:VQG`(2 個,其餘 766 只是在環下游,兩者分開報)·
DuckDB 三表 933/983/761 同鍵重複 0 · 第二次跑 appended 0 · 自測 28/28(有 duckdb)/ 27/27(`-I` 無 duckdb)·
站 `C-workflow-viz-v0100` 經主控台 GREEN rc 0。

另出兩份文件:`VIA_FiveDay_Panorama_20261107.md`(main 168 提交 · 18 PR · 五系統 × 五日 · 10 條流程錯誤根因)·
`VCGC_MCP_v0102_sync_20261107.md`(兩根 + 22 條桌機路徑現狀 · 三來源同步表 · 要我直讀桌機的開法)。

**照實 BLOCKED(不假裝做過)**:`C:\測試樣本報告` 的 VRN 實測、Downloads 其餘 18 條路徑 ——
桌機未經 Remote Control 供出資料夾(`folders` 空);ChatGPT / Perplexity / Manus 四個連結全是登入牆
(`NO_CONTENT`),agentmemory / Ponytail / OmniRoute 要貼內容才能往下。
上傳的 `Invoke-VIA-AllInOne-v0100.ps1` 原樣入倉為 `.reference`,**不代跑**(它會建 venv、載 hash 釘住的
v0194 引擎、對 PyPI 裝 pyarrow)。

## §38 本系統標準視覺鎖定 U/I(操作員 2026-11-07 · VCGC-REQ195)

**`docs/handoff/ai/VIA_VisualLock_v0100.py`**(+ 同名 `.md` 標準文件)。

操作員給的兩個連結本會話都讀不到(Manus 站 302 轉 `manus.im/app-auth` 登入牆;
Claude Design 連結 Artifact 工具明確不支援),**但兩者的正本倉內都有**,所以不靠外站完成:

| 角色 | 倉內正本 |
|---|---|
| 格式(鎖) | `review/VIA_Atlas_LocalSite_v0100/index.html` —— 2026-11-06 已位元組鎖定 |
| 版面(個股) | `functional modules/VAP/ASSETS/VIA_TW_Stock_Dashboard_standalone.html` |

**鎖是抽出來的不是手抄的**:`kit` 從正本 `:root{}` 抽 `--vl-*`(24 個)算區塊 sha256。
正本改了 kit 跟著改,`check` 立刻看得出來。

**鎖定閘四判**:① token 區塊 sha 必須等於正本 ② 色彩只准 `var(--vl-*)` ③ 0 外連
④ 手機側邊槽 + `overflow-x`。自測實證三種違規都抓到(寫死色 / 外連 / 改 `--vl-bg`)。

**個股頁**:版面照模板撈出的區段清單(含共振堆疊圖 7 卡共用時間索引),樣式接鎖定 kit
(不沿用模板自己的 `--color-*` 冷灰藍),值只來自 VRN-2 自報;
缺的印「—」標 GRAY 並寫明原因,**技術 / 籌碼面沒有 VDF 日資料就照實 GRAY,絕不畫假 K 線**。

```bash
python3 ".../VIA_VisualLock_v0100.py" all --via . --top 3    # tokens → kit → index → stock → check
python3 ".../VIA_VisualLock_v0100.py" --selftest             # 19/19
```

容器實測:正本 4/4 OK · token 24 · kit 4307 bytes · 盤點 47 檔有料 · 出頁 3 張全過閘 GREEN ·
總燈 YELLOW(照實) · 站 `C-visual-lock-v0100`。

**照實 BLOCKED**:20+ 條 `Downloads` 路徑 · `NON_STOCK_CORE_v0400.zip`(操作員說可取代 v0300)·
「持續監控 PS 跑完自動擷取」(桌機正在跑 MCP SYNC,但雲端看不到它的行程與輸出夾)——
全部因為 Remote Control 未供出資料夾。
