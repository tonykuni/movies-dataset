# 批656 · 我又隔空猜了一次 —— 這次讓下一跑自己回答

## 先更正批655

我斷定「寫的人跟讀的人指到兩本不同的庫」。

**但你同一跑的 `candidates` 讀的是 `output\vrn_reports.duckdb`,量到券商缺口 9+6=15,
和 ENG073 那一行 `券商正典鍵 90/105` 完全吻合。**

一本**舊表**也可能給出同樣的數字(同樣 105 份、同樣的引擎邏輯),
所以兩種說法**都還站得住** —— 而我沒有你的機器。

LL288 我寫過一次「不能猜第二次」。這是第三次。 → **LL294**

而且批655 我還把「資料家優先」寫死進選庫次序,理由是 ENG073 這樣解 ——
**但那支 `_resolve_db()` 解的是價表(`vdf_tw_market.duckdb`)**,
結構表落在哪一本要看當時的環境。固定次序一旦猜錯,會把矩陣指到**更舊**的表,比原本的問題還糟。

---

## 不再猜:把判別式搬進輸出

### ① 任何一欄 GREEN 0,就印出它底下的原始值分佈

零綠**只有兩種可能**:缺料,或尺與值對不上。看一眼原始值就分得開。

容器實跑,一行就說完:

```
[**整欄零綠**] 上漲空間(upside_calc)—— 零綠只有兩種可能:缺料,或尺與值對不上。底下的原始值分佈:
     upside_state:MISSING_SOURCE×51 · SINGLE_SOURCE×23 · EXACT_MATCH×5 · ROUNDING_ONLY×2
     upside_report:(NULL)×74 · 22.7×1 · 41.9×1 · 23.0×1 · 28.0×1 · 44.7×1 · 32.0×1 · 38.9×1
     upside_db:(NULL)×81
```

**`upside_db` 全是 NULL** → 容器沒有台股價,`_DB` 永遠升不起來 → 這裡的零綠是**純缺料**。
不用我推論,它自己講完了。

> 探針從 **判燈用的同一份 `rows`** 數。
> 第一版我拿已經 `close()` 掉的 `con` 去查,印出三行 `ConnectionException` ——
> **印的跟判的不是同一批,那比不印還糟。**

### ② 候選庫全部列出來,連列數與最後寫入時間

```
[庫] …\vrn_reports.duckdb
     ← VRN 舊路徑 output/vrn_reports.duckdb(候選中**最後被寫過**的一本)
[**第二顆頭**] 另有 1 本庫也有 vrn_report_basic ——
       105 列 · 最後寫於 2026-09-22 07:14 · 資料家目錄頁 VIA_DB_VDF_TW_MARKET
             C:\Users\tonyk\VIA System\…\vdf_tw_market.duckdb
       105 列 · 最後寫於 2026-09-19 21:44 · VRN 舊路徑 output/vrn_reports.duckdb
             C:\…\functional modules\VRN\output\vrn_reports.duckdb
```

選的是**最後被寫過的那一本**,不是我猜的次序。
兩本的時間一擺出來,是不是第二顆頭、哪一本是舊的,你一眼就看得到。

---

## 你這一跑會直接告訴我們答案

```powershell
git pull origin claude/via-envmanager-governance-7cls8h
. .\VeritasIntelligenceAnalytics\Register-VIA-Commands-v0231.ps1
via-run25 --only structdb,matrix
```

矩陣會印出:

- **它讀的是哪一本庫**、有沒有第二本、各自的列數與最後寫入時間
- 上漲空間那一欄**底下的 `upside_state` 分佈**

如果分佈裡有 `EXACT_MATCH_DB` 卻還是零綠 → 那是尺的事,我來修。
如果分佈裡**沒有** `_DB` → 那就是寫的那一本不是讀的這一本(批655 是對的),
時間戳會直接把它指出來。

**兩種答案都不需要我再猜一次。**

---

## 順帶:你那 5 個券商候選

```
2 份 · 'MORGANSTANLEY'   2 份 · 'UBS'   2 份 · 'GF'   2 份 · 'CAPITAL'   1 份 · 'DAIWA'
```

這五個都是**大券商的正規名稱**卻查不到正典鍵 —— 看起來不是「少一個同義字」,
而是**檔名走的那一條 SSOT 查詢沒命中**(例:`260910_ms_iphone-18-optical` 這種純檔名件)。

要不要收進 `VIA_Financial_Institution_SSOT_v0100.py`(READ_ONLY 正典),**裁定權在你**。
我一個字都沒寫。
