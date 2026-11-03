# VRN-2 一支 Python · VRN2_RoundAll_v0131.py(套件 v0175 · ⑬a BookSource · OutputStore v0103 · Workbench v0109)

`VRN2_RoundAll_v0131.py`(只用 Python 標準庫 · SHA-256 `0f58b9464d95`)= v0130 +:

| 改了什麼 | 說明 |
|---|---|
| 套件 | `vrn2_release_v0175/VRN2_Closeout_v0175.zip`(SHA-256 `aa02705018bf` 已釘入本檔)· 啟動器 v0175 · runtime v0164 = v0163 + BookSource v0100 + OutputStore v0103 + Workbench v0109 |
| ⑤ source(新)| 輸出冊還沒有 SOURCE / BROKER_EN、或比上次寫欄新、或本輪重算 ⑬b / Combined → 只增不覆寫補放 BookSource v0100 → 寫最後兩欄 · 舊收據沒有 ⑬a 步驟就補一列在 ⑬ 前面 · 排在 store 之前 |
| ⑤ store | 補放鏈多 OutputStore v0103(雜湊不算兩欄 · 舊列補欄 · 先備份)· 增量庫收據沒有 derived_fill 也排 |
| ⑤ workbench | 頁面沒有 v0109 標記(`id="wb109-tpl"`)→ 補放 v0109 + v0108 + v0107 → 重渲染 |
| ③ 自測清單 | Workbench v0109 · OutputStore v0103 · BookSource v0100 |
| 貼回包 | 多 VRN2_BookSource_latest.json |
| 自測 | 103 項(v0130 的 100 項 + 101 · 101b · 101c · 舊項目在 VIA_VRN2_NO_BOOKSOURCE=1 下跑)|
| ⑥ 除錯 | Combined 最後兩欄是 ⑬a 實體欄 → 欄序照 ConsensusJoin 清單比(兩欄另記)|
