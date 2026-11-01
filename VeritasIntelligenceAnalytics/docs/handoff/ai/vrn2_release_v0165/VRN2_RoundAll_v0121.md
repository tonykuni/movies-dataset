# VRN-2 一支 Python · VRN2_RoundAll_v0121.py(套件 v0164 · 人工確認紀錄 · repair 也送 SSOT 新提案)

`VRN2_RoundAll_v0121.py`(只用 Python 標準庫 · SHA-256 `627f6af3fd9b`)= v0120 +:

| 改了什麼 | 說明 |
|---|---|
| `--confirm` | `list` 列出上一輪收尾頁的人工核對項(代碼 · 內容 · 指令)· `H-xxxxxxxx [--note …]` 記一筆確認 · `revoke H-xxxxxxxx` 記一筆撤銷 · 打錯 / 內容已變的代碼不記 · 確認後用上一輪的結果重做收尾頁 |
| 收尾頁 | 人工項帶代碼 + 一行可複製的 `--confirm` 指令 · 有效確認 → 「人工已核」不計入結案狀態(例:REVIEW → DATA_GAP)· 「輸出冊 · 缺項 N 份」寫出哪幾份 |
| ⑤ ssot | 套件 runtime 的提案冊比 ⑤b 核號請求用的新 → 補放提案冊 v0101 + SSOTSync 鏈(只增不覆寫)→ 跑一次 ⑤b sync(VRN-2 自己的核號請求 · 不改 VCGC 的冊)|
| 貼回包 | 多收 `VRN2_HumanConfirm.json` |

只有操作員親手打 `--confirm` 才會寫確認冊;RoundAll 的流程(含 ⑤ 自動修)永遠不呼叫它。自測 83 項(v0120 的 78 項 + 79 ~ 83)。套件 `vrn2_release_v0164/VRN2_Closeout_v0164.zip`(SHA-256 `84834e330fac` · 本檔內已釘死)。
