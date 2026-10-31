# VRN-2 一支 Python · VRN2_RoundAll_v0116.py(套件 v0158 不動 · 加速器 · 真百分比 · 收尾頁新版面)

`VRN2_RoundAll_v0116.py`(只用 Python 標準庫 · SHA-256 `e518022ba4d0`)= v0115 +

| 改了什麼 | 說明 |
|---|---|
| ①b 本行程點 VIA 加速器 | 套件裡的 `VIA_ExecutionBridge_v0103`(核對 VIA 工具鎖冊 · 跟啟動器同一支)→ 鎖版 VeritasCeleritas 把執行緒預算寫進環境 · 子行程照繼承;沒有套件 / 鎖冊 / 缺套件 → 灰照跑;鎖冊對不上 → 黃(收尾頁 VCGC)· `VRN2_NO_ACCEL=1` 不點 |
| `[進度] n/N` | 每一步依權重印一行 · ④ 啟動器的進度條換算進來 · ⑤ 自動修逐項;PowerShell 的 VIA 加速器進度模板(`Invoke-VIAPython`)照它畫真百分比;子行程自己的 `[進度]` 改標 `[子步驟]` 才轉播 |
| 收尾頁新版面 | 頂列狀態 + 段落導覽 · 結案卡 · 燈號環圈 · 負責方堆疊條 · 流程 · 待辦篩選 / 搜尋 / 空結果提示 · 檔案卡 · 複製提示框 · 淺 / 深 / 跟系統主題 · 可列印 |
| 小修 | 舊資料庫問句整行先印再等輸入 · `--launcher-args` 每段去掉外圍引號(PowerShell 傳進來的 `"--no-install"`) |

自測 64 項(v0115 的 59 項 + 60 ~ 64)。套件 `vrn2_release_v0158/VRN2_Closeout_v0158.zip`(SHA-256 `dfca4f6b13fb` · 本檔內已釘死)。**最省事:`VRN2_HandleAll_v0108.md` 的那一行(PowerShell / cmd 各一段)**。

```bat
python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0116.py" --only package,fix,report,closeout,pasteback
python "%USERPROFILE%\Downloads\VRN2_RoundAll_v0116.py"
```

PowerShell 把 `%USERPROFILE%` 換成 `$env:USERPROFILE`。直接跑 python 時收尾頁照舊由 RoundAll 自己開(Windows · `--no-open` / `VRN2_NO_UI=1` 不開)。
