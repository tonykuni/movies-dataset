# VRN-2 一支 Python · VRN2_RoundAll_v0126.py(套件 v0170 · 共識欄快照補位 · Workbench v0105)

`VRN2_RoundAll_v0126.py`(只用 Python 標準庫 · SHA-256 `174df7b572c0`)= v0125 +:

| 改了什麼 | 說明 |
|---|---|
| 套件 | `vrn2_release_v0170/VRN2_Closeout_v0170.zip`(SHA-256 已釘入本檔)· 啟動器 v0170 · runtime v0160 = v0159 + Workbench v0105 + ConsensusJoin v0106 |
| ⑤ 自動修 | 新步 consensus_snapshot:收據是「同意閘未開 DENY · per_code 空」、閘仍關、碟上有共識快照 → 跑 ConsensusJoin v0106(快照補位 · 不連外 · 不代設閘)→ 重組 Combined → 增量庫 / Workbench 跟著 |
| 負責方 | ⑥f 列 detail 帶「快照補位」→ 提醒(Combined 已補 · ASOF 寫實 · 要最新:開閘再 repair)· 比「同意閘未開 → 人工」優先 |
| 自測 | 93 項(v0125 的 91 項 + 90 快照負責方 + 91 快照計畫)|
