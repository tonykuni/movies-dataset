# VRN-2 一支 Python · VRN2_RoundAll_v0128.py(套件 v0172 · VRN P0 三項)

`VRN2_RoundAll_v0128.py`(只用 Python 標準庫 · SHA-256 `e1c9178f608c`)= v0127 +:

| 改了什麼 | 說明 |
|---|---|
| 套件 | `vrn2_release_v0172/VRN2_Closeout_v0172.zip`(SHA-256 `bd952da149bd` 已釘入本檔)· 啟動器 v0172 · runtime v0162 = v0160 + HistoryAlign v0103 + ConsensusJoin v0107 + Workbench v0107 |
| ⑤ 自動修 | history ← 歷史對齊收據的 Parquet「(沒寫…」(先只增不覆寫補放 HistoryAlign v0103 鏈)· combined ← Combined 沒有 UPSIDE_ADJ(補放 ConsensusJoin v0107)· workbench ← 頁不是 v0107(補放 Workbench v0107)· 增量庫照舊跟著補寫 |
| ⑥ 除錯 | Combined 欄序以 v0107 為準(UPSIDE_ADJ 緊接 UPSIDE_PCT(ADJ))· Workbench 標記多「Basic Info 合併檢視」|
| ③ 自測清單 | HistoryAlign v0103 · ConsensusJoin v0107 · Workbench v0107(前版照舊由鏈自測)|
| 自測 | 98 項(v0127 的 94 項 + 93 欄序 · 94 小數欄計畫 · 95 Parquet 計畫 · 96 只增不覆寫補放)|
