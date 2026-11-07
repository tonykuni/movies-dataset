# workflow_viz_v0100 — 操作員 2026-11-07 上傳整合 + VIA_WorkflowViz v0100

## 一、這夾裡是什麼(操作員上傳,原樣入倉)

| 檔 | 來源 | SHA-256(前 16) | 處置 |
|---|---|---|---|
| `WorkflowViz_Plan_v0100.md` | 上傳「工作流架構視覺化實作計畫」 | `f67cf960c946bf74` | 原樣保留(兩份上傳位元組相同,去重保留一份) |
| `demo_quant_pipeline.mmd.md` | 上傳 Mermaid 匯出範例 | `cc73467b2ad4cd96` | 原樣保留(參考格式) |
| `upstream_demo_dashboard_phase3.html` | 上傳 Phase 3 互動 demo(4.97 MB · 內嵌 plotly.js) | `8cc97d29fd281ad3` | 原樣保留(驗收對照用,不是本倉產出) |

同批上傳的 `Invoke-VIA-AllInOne-v0100.ps1` 放在上一層
`docs/handoff/ai/Invoke-VIA-AllInOne-v0100.ps1.reference`(SHA `85d435aef4bb94e2`)。
**不代跑**:它會在桌機建 `via_vcgc_0194` venv、載 hash 釘住的 v0194 引擎、對 PyPI 裝 pyarrow、
並寫 `%LOCALAPPDATA%` —— 那是操作員的手與桌機環境,雲端會話不代替執行(零安裝律 + 不碰他人環境)。
副檔名加 `.reference` 是為了不讓它被誤當成可直接跑的啟動器。

去重判定:兩份 `.md` 位元組完全相同(同一 SHA)→ 只留一份,**不是**「值相同就合併編號」那種禁止的合併
(那條規矩管的是不同資料來源的編號;這裡是同一份檔案的兩個副本)。

## 二、計畫選的技術棧 vs 本倉實作(為什麼不一樣)

計畫選 NetworkX + Graphviz + Plotly + Seaborn。本倉受 **零安裝律**
(裝只經 VCGC 的 `via-envgov tools --apply --approve`),容器與多數桌機實測:

| 層 | 計畫 | 容器實測 | `VIA_WorkflowViz_v0100.py` 的作法 |
|---|---|---|---|
| 拓撲 | NetworkX | ✗ 不在 | 純標準庫 **Tarjan 強連通元件 → 縮點 → 分層** + 冪法 PageRank;有 networkx 就用它 |
| 佈局 | Graphviz `dot` | ✗ 不在 | 自己做分層佈局(層內按車道 + 中心性排序降低交叉) |
| 互動圖 | Plotly | ✗ 不在 | 內嵌 **SVG + 原生 JS**;**397 KB**(上游 demo 4.97 MB,小 12.5 倍)且零外部請求 |
| 熱力圖 | Seaborn | ✓ 在 | 真用 seaborn 畫,base64 內嵌;缺席時走純 CSS 色階表並照實說沒畫 |
| 資料層 | DuckDB + Parquet | ✓ 在 | 真寫 `workflow.duckdb` + `.parquet`;缺席走 JSONL + CSV,**一律** 吐出 DDL 讓桌機照貼 |

驗收標準第 5 條「全離線、無 CDN」因此是**主路徑**而不是退路。

## 三、資料不是 demo:三表全部由本倉收據生成

| 表 | 來源(本倉自己的收據與冊) |
|---|---|
| `nodes` | 盤點冊 `VIA_VCGC_FunctionInventory_SSOT_v*.json` 的 329 站 · 功能帳的 338 個 id · 交接冊 `work_items` · 固定車道 |
| `edges` | 站 argv → 家族 · 車道 → 站 · 工作項 → 案站 · **跨車道交接**(某車道的站用了別車道的家族 → 車道 → 車道) |
| `metrics_ts` | 功能帳 `VIA_VCGC_FunctionLedger_v0100.jsonl`(2026-09-30 ~ 現在)+ 串測 `TEST_latest.json` 的站燈與秒 |

**會籍不畫邊**:誰屬於哪個車道用 `layer` 欄位表達。畫成邊會讓
`lane → station → family → lane` 必然成環 —— 實錄:第一版就是這樣,933 個節點有 441 個被判成環,
分層佈局塌成一層。修正後真的在環裡只有 2 個(見下)。

## 四、容器實測(2026-11-07)

```
節點 933 · 邊 983 · 指標 761 列 · 總燈 RED(照實:有 8 個紅節點)
拓撲 stdlib(Tarjan 縮點 + 冪法 PageRank)· 元件 932
  真的在環裡 2 個:lane:VCGC ⇄ lane:VQG(回邊 2 條)
  只是在環下游 766 個 —— 這兩者分開報,不混成一類
DuckDB workflow.duckdb:nodes 933 · edges 983 · metrics_ts 761 · 同鍵重複 0
車道節點:VCGC 854 · VDF 50 · VRN-2 13 · VQG 9 · VAP 3 · UNKNOWN 3 · VRN-1 1
燈:GRAY 487(沒收據,照實不猜)· GREEN 379 · YELLOW 59 · RED 8
跨車道交接(throughput):VCGC→VDF 68 · VCGC→VRN-2 12 · VCGC→VQG 3 · VQG→VDF 4 · VCGC→VAP 2 · VQG→VCGC 1
HTML 397 KB(離線單檔)· Mermaid 7.2 KB · 熱力圖 seaborn 22 節點 × 14 日
增量:第二次跑同一行 appended 0(鍵 node_id + ts + run)
自測 27/27 PASS
```

`lane:VCGC ⇄ lane:VQG` 是**真的互相依賴**,不是越界:VQG 的站用 VCGC 的編號家族
(`station:QG-CGC_MDL237_NumberingSystem`),VCGC 的站測 VQG 的家族。符合 L123「只讀互看 · 各走自己入口」。

## 五、怎麼跑

```bash
# 容器 / 桌機都一樣(DuckDB 要非隔離模式才看得到 user site-packages)
python3 "VeritasIntelligenceAnalytics/docs/handoff/ai/VIA_WorkflowViz_v0100.py" all --via . --top 150
python3 ".../VIA_WorkflowViz_v0100.py" schema        # 印資料合約 + DuckDB DDL,不寫檔
python3 ".../VIA_WorkflowViz_v0100.py" --selftest    # 27/27(零網路 · 只寫沙盒)
```

輸出在 `<VIA>/VIA_Reports/workflow_viz/`(VIA_Reports 不進 git):
`VIA_WorkflowViz.html`(離線單檔)· `VIA_WorkflowViz.mmd` / `_mermaid.md` ·
`workflow.duckdb` · `nodes|edges|metrics_ts_snapshot.{json,csv,parquet}` · `metrics_ts.json`(累積庫)·
`metrics_ts.ddl.sql` · `WORKFLOW_VIZ.json`(本輪收據)。

**快照與累積庫分開**:`persist` 只寫本輪快照 `metrics_ts_snapshot.*`;累積庫 `metrics_ts.json` 與
DuckDB 的 `metrics_ts` 表只由 `etl` 以 anti-join 累加,**只增不刪**。
第一版把兩者混用,重跑一次就會把時序歷史洗掉 —— 已修,並留了回歸測。

## 六、照實沒做到的

- 上游 Phase 3 的 Plotly 下鑽與 Streamlit 儀表板:沒有 plotly / streamlit,不裝;本支的 SVG 下鑽是等效實作,不是同一份程式。
- Perplexity 專案(`workflow-visualization-archite-Oadu7y92TWqCwA4kZ.qWnw`)與 ChatGPT 分享頁
  `6aef5161-…`:兩個都是登入牆,容器讀回 `NO_CONTENT`,**沒讀到內容**;要整合請貼文字或上傳匯出檔。
- `C:\測試樣本報告` 的 VRN 實測:桌機未經 Remote Control 供出資料夾(`folders` 空),雲端讀不到。
