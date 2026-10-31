# VRN-2 一支 Python · VRN2_RoundAll_v0118.py(套件 v0158 不動 · ⑥e 重抓上限 · 收尾頁合併)

`VRN2_RoundAll_v0118.py`(只用 Python 標準庫 · SHA-256 `9a770b113b34`)= v0117 +

| 改了什麼 | 說明 |
|---|---|
| ⑤ 重抓 ⑥e 上限 | 擷取(`--fetch`)2400 → 5400 秒(`VRN2_MARKET_FETCH_SEC` 可調 · 最少 600)· 填值(`--fill`)照舊 2400 秒 |
| 接著抓 | 收據 ⑥e 是「RoundAll 修正後 · 擷取 RED:逾時 N 秒」→ ⑤ 再排一次重抓(MOPS 回應 12 小時快取)|
| 收尾頁 | ⑤ 重抓 ⑥e / ⑥ 步驟 ⑥e / ⑥e 擷取錯誤 / 擷取鎖 = 同一項;⑥e 沒抓完時 ⑬b 三列也併進來;⑥e 完整了 ⑬b 自己一項 |

自測 72 項(v0117 的 69 項 + 70 ~ 72)。套件 `vrn2_release_v0158/VRN2_Closeout_v0158.zip`(SHA-256 `dfca4f6b13fb` · 本檔內已釘死)。**最省事:`VRN2_HandleAll_v0110.md`(cmd / PowerShell 各一段)**。

```bat
python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0118.py" --only package,fix,report,closeout,pasteback
python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0118.py"
```
