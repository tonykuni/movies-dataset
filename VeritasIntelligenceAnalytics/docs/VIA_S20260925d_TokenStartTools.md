# 2026-09-25d · 政策二 · 被啟動的省 TOKEN 工具

操作員令：把輔助工具裡的省 TOKEN 做法列成書。全景式讀取、AST 五類、向下切一個定義。AI 啟動它就夠，不用把原始碼讀進對話。對話框裡的省法收成啟動項，不另造一支引擎。

這一頁掛在政策一下面：先過 VCGC，再啟動這些短令。正主已經優化完，批707 寫明不另立引擎。

## 啟動項

尾版 `CGC_MDL158_VIAPanoramaAuditRepair_v0106.py`。短令仍是 `via-panorama`，不寫死版號。

| 啟動 | 做什麼 | 不做什麼 |
| --- | --- | --- |
| `via-panorama read <檔或夾>` | 骨架卡：匯入、定義樹、行號、AST 五類 | 不把原檔貼進對話 |
| `via-panorama slice <檔> <定義名>` | 只回那一個定義，向下一層 | 不把整支讀完 |
| `via-panorama digest <跑測日誌>` | 只留判決行。同一站以最後一列為準 | 不 grep 整份日誌 |

AST 五類就在 `read` 裡，不另開五支：`DUPDEF` · `UNREACH` · `BAREEXC` · `SWALLOW` · `MUTDEF`。PowerShell 另兩類 `PSDUPFN` · `PSDOCSTR`，不算進這五類。

批708 實測：日誌 30634 token → `digest` 371 token。骨架卡對單檔約省 95%。尺要用 v0106 的 CJK 感知算法，不用 `字元數 // 4`。

## 一起啟動，也不另造

| 已有 | 怎麼省 |
| --- | --- |
| 批607 · L86 | 畫面壓到上限。紅燈、判決不壓。log 全留 |
| VCGC `help` | 只印用法段。`help --full` 才印版史 |
| 批728 `via-vcgc ssot` | 輕檢委派正主。不把同義字庫整本讀進來 |

## 啟動順序

1. 先過 VCGC（政策一）。
2. 要看一支檔：`read`。要看某一個定義：再 `slice`。
3. 要看跑測：`digest`。沒有 `[計]` 就是 NODATA，不編一個結論。
4. 零寫檔、不執行被讀的檔。

這台預覽沒載 CGC_MDL158，所以這三個動詞在這裡是 ABSENT。不用另一支讀檔器頂替。
