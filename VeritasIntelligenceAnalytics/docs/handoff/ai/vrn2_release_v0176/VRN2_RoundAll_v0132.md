# VRN-2 一支 Python · VRN2_RoundAll_v0132.py(套件 v0176 · BookSource v0101 · OutputStore v0104)

`VRN2_RoundAll_v0132.py`(只用 Python 標準庫 · SHA-256 `9b61c18d8e39`)= v0131 +:

| 改了什麼 | 說明 |
|---|---|
| 套件 | `vrn2_release_v0176/VRN2_Closeout_v0176.zip`(SHA-256 `90bcb8c5166a` 已釘入本檔)· 啟動器 v0176 · runtime v0165 = v0164 + BookSource v0101 + OutputStore v0104 |
| ⑤ source | 補放鏈 BookSource v0101 + v0100 · 上次寫欄的收據沒有 summary_cleanup(BookSource v0100 寫的:四點還帶符號 · 主題與摘要舊格式)→ 也排 ⑬a |
| ⑤ store | 補放鏈多 OutputStore v0104(不重複追加 · 舊列就地整理 · 先備份)· 增量庫收據沒有 summary_tidy 也排 |
| ③ 自測清單 | BookSource v0101(先跑 v0100 自測)· OutputStore v0104(先跑 v0103 自測)|
| ⑥ 除錯 | 新一列「四點 / 主題與摘要」:開頭還有符號幾格 · 主題與摘要不是 Name(…) - 標題 開頭幾列 · 評價點用調整後價幾列 |
| 自測 | 103 項(實跑計數:v0131 的 101 項 + 102 · 102b · 舊項目在 VIA_VRN2_NO_BOOKSOURCE=1 下跑)|
