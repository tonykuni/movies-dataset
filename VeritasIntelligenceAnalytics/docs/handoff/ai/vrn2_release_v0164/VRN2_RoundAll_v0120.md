# VRN-2 一支 Python · VRN2_RoundAll_v0120.py(套件 v0164 · 增量庫清 MOPS 列 · TARGET_PRICE(ADJ) 同步還原 · TWSE / TPEX 格式合併)

`VRN2_RoundAll_v0120.py`(只用 Python 標準庫 · SHA-256 `860cdd5b5fd4`)= v0119 + 操作員 2026-11-01:

| 改了什麼 | 說明 |
|---|---|
| 套件 v0164 | 啟動器 v0164 · runtime v0157 = v0156(192 個成員不動)+ ConsensusJoin v0105 + OutputStore v0102 + SSOTSync v0102 + 提案冊 v0101(這輪新規則 8 條 · 沒有編號 · 等 VCGC 核發)|
| ⑤ combined | 還沒同步還原 / 合併過 → 補放 ConsensusJoin v0105 鏈(只增不覆寫)→ 重組 Combined(TARGET_PRICE(ADJ) 同步還原 · 共識照 TWSE / TPEX 格式落盤 · 合併)|
| ⑤ store | 增量庫還沒確認乾淨 → 補放 OutputStore v0102 鏈 → sync(先清 MOPS 算的列 · 整檔備份到 `_mops_purge_<時間>` · 可 `restore-purge`)|
| 收尾頁 | ⑥e「擷取 YELLOW · 失敗 0」= VDF rc 2 PARTIAL → 資料源(寫錨點)· 「不用 MOPS」的說明字不再被當成 MOPS DENY · Combined MISSING 原因不因日期 / 比值拆類 |
| 貼回包 | 多收 `VRN2_StorePurge_latest.json` · `market\\VRN2_TPAdjSync_latest.json` · `market\\vdf\\status.json` · `output\\VRN2_MarketConsensus_latest.csv` |

自測 78 項(v0119 的 74 項 + 75 ~ 78)。套件 `vrn2_release_v0164/VRN2_Closeout_v0164.zip`(SHA-256 `84834e330fac` · 本檔內已釘死)。**最省事:`VRN2_HandleAll_v0112.md`(cmd / PowerShell 各一段)**。

```bat
python "%USERPROFILE%\\Downloads\\VRN2_RoundAll_v0120.py" --only package,fix,report,closeout,pasteback
python "%USERPROFILE%\\Downloads\\VRN2_RoundAll_v0120.py"
```
