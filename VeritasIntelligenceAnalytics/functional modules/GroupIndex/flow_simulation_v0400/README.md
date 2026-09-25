# VIA Taiwan Group Flow System v0.4.0

台股族群分類、驗證、指數、資金動能與五態輪動監控的單檔離線 Dashboard。

`FETCH → CLASSIFY → VALIDATE → INDEX → OBSERVE → FLOW → ROTATION`

每段輸出方法、版本、來源、日期與 evidence tier；下游只能維持或降低證據等級，不得把 `PROXY`、`ESTIMATED`、T2/T3、未驗證來源或 fixture 洗成 `MEASURED/T1`。

## v0.4.0 整合結果

- 2026-07-18 歷史輪動快照：18 群，五態為啟動 4、擴散 2、過熱 4、退潮 5、潛伏 3。
- `29` 是來源宣告的 registry 群數；`tw_group_registry.json` 未附，系統只保存計數，不捏造其 29 筆主檔。
- `31` 群、149 筆是受控 fixture 回歸基線；`49` 群、252 筆是候選驗整層；三套口徑互不覆寫。
- 歷史 18 群逐一對映 49 群：10 exact、3 alias、3 split parent、1 cross-group alias；石英/頻率元件維持未對映待 taxonomy review。
- 全部輪動列維持 `SOURCE_REPORTED_T2_T3_UNVERIFIED`，M3/VDF 真值化前 `0` 群可供指數使用。
- VDF 控制面板只抽取 U/I 契約：TWSE 1,200、TPEX 647、總數 1,847；Fetcher/Network 執行均為 0。
- 市場情報登錄：14 類、77 列，`NEEDS_FETCH_NO_FABRICATION`。
- 49 群目前 `0 / 49` 可生成指數；4 群待 VDF，面板/6116 重複登錄仍保留並阻擋。
- Gate：`ROTATION_T2_T3_REVIEW_CANDIDATE_49_BLOCKED_FIXTURE_REGRESSION_PASS`。

這不是即時市場快照，也不是投資績效或準確率宣稱。2026-07-18 不代表今天；L1/L2/L3 評價、ONE/FIS 全域模擬與控制面板示意值都不會進入 runtime measured facts。

## 核心模組

- `engine/via_rotation_snapshot_engine.py`：五態快照、來源契約逐列核對、歷史→49 群對映、接棒分、falsifier、狀態轉移與 append-only 寫入。
- `ssot/VIA_Rotation_Snapshot_20260718_v0400.json`：由本輪使用者訊息固化的歷史來源契約；明記 T2/T3 與 canonical mutation=0。
- `engine/via_flowrot_candidate_intake.py`：解析 49 群、驗證 252/241 計數及 6116 衝突。
- `engine/via_version_chain.py`：證據單調降級；VALIDATE 未過即阻擋 INDEX。
- `engine/via_attention_share_engine.py`：M-1A 雙層扣除、2330 特例與平滑百分位。
- `engine/via_statistical_validation_engine.py`：PCA、±5 日 CCF、max-over-lags 置換檢定。
- `engine/via_dynamic_classification_engine.py`：動態分類、PCA 純度、規模與資金主導型態。
- `engine/via_rotation_backtest_engine.py`：t 日訊號、t+1 報酬、交易成本與風險利率的 walk-forward 回歸測試。
- `engine/dashboard_builder.py`：無 CDN、單檔、緊密響應式 U/I；預設顯示五態輪動監控。
- `ssot/VIA_Market_Intelligence_Registry_Summary_v0400.json`：14 類 77 列摘要契約。
- `ssot/VIA_TW_Group_Flow_Contract_v0400.json`：29/31/49、輪動與證據邊界。

## M-1A Attention Share

```text
AS = Val(個股 − 當沖)
     ÷ [Val(TWSE) + Val(TPEX) − Val(當沖) − Val(2330 非當沖)]
```

- TWSE/TPEX 任一缺漏、當沖缺漏或分母非正數時阻擋。
- ETF、權證不計入；2330 改列兩市非當沖占比。
- 4,128 + 892 − 1,406 − 512 = 3,102 億只作 `ESTIMATED_EXAMPLE_NOT_RUNTIME`。

## 執行與測試

```powershell
python -m pip install -r requirements.txt
python run_system.py all --config config/system_config.json
python -m unittest discover -s tests -v
node -e "const fs=require('fs');const h=fs.readFileSync('data/output/VIA_TW_Group_Flow_Simulation_System_v0400.html','utf8');new Function(h.match(/<script>([\\s\\S]*)<\\/script>/)[1])"
node tests/browser_smoke.js
```

`pyarrow` 是 Parquet 輸出的必要依賴；若缺少，引擎仍會輸出 CSV，但在 run summary 明確標記 `REVIEW_OPTIONAL_DEPENDENCY`，不會偽稱 Parquet 成功。

## 主要輸出

- `data/output/VIA_TW_Group_Flow_Simulation_System_v0400.html`
- `data/output/rotation_snapshots_v0400.csv|parquet`
- `data/output/candidate_group_validation_v21.csv|parquet`
- `data/output/candidate_membership_v21.csv|parquet`
- `data/output/pipeline_version_chain_v0400.csv|parquet`
- `data/output/group_index_daily.csv|parquet`（31 群 fixture 回歸）
- `data/output/group_flow_daily.csv|parquet`（31 群 fixture 回歸）
- `evidence/rotation_snapshot_quality.json`
- `evidence/vdf_contract_summary.json`
- `evidence/run_summary.json`
- `evidence/validation_ledger.csv`

## 真實啟用邊界

REAL_DATA 必須拒絕 fixture/demo、缺任一市場、缺當沖、未調整除權息、重複鍵、缺 PCA/CCF/置換證據，以及任何未標記的代理值。即使通過資料閘，引擎也只到人工啟用審查；不會自動修改 canonical、建立 GitHub PR、推送分支或連線下單。
