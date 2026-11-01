# VRN-2 一支 Python · VRN2_RoundAll_v0117.py(套件 v0158 不動 · ⑥e 過期擷取鎖)

`VRN2_RoundAll_v0117.py`(只用 Python 標準庫 · SHA-256 `9136cc21a230`)= v0116 +

| 改了什麼 | 說明 |
|---|---|
| ⑥e 擷取鎖 | VDF 引擎在 `VIA_Reports\vrn2\market\vdf\RUNNING.lock` 留下的鎖:PID 已不在 / 號碼被重用 / 比鎖晚起 → 移到 `RUNNING.lock.stale_<時間>`(不刪)· PID 還在跑 → 不動 |
| ④ 跑啟動器前 | 先看一次擷取鎖 |
| ⑤ 自動修 | 鎖過期 → 移開 · 上一輪 ⑥e 被鎖擋住 → 重抓 ⑥e(repair 沒跑 ② 也自己找共用夾的 MarketFetch 最高版號)|
| last_error.txt | ④ 跑啟動器前 / ⑤ 重抓前把上一輪的移到 `last_error.before_<時間>.txt`(MarketFetch 只在失敗時寫 · 這輪抓成功就不會留著舊錯誤)|
| 除錯報告 / 收尾頁 | 「⑥e 擷取錯誤」錯誤在前 · CMD 在後(代號縮成「N 檔」)· 新列「⑥e 擷取鎖擋住」· 鎖還在跑 = 人工 · 過期 / 已移開 = VRN-2 · 三列合一列 · 貼回包帶 `RUNNING.lock` |

自測 69 項(v0116 的 64 項 + 65 ~ 69)。套件 `vrn2_release_v0158/VRN2_Closeout_v0158.zip`(SHA-256 `dfca4f6b13fb` · 本檔內已釘死)。**最省事:`VRN2_HandleAll_v0109.md`(cmd / PowerShell 各一段)**。

```bat
python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0117.py" --only package,fix,report,closeout,pasteback
python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0117.py"
```
