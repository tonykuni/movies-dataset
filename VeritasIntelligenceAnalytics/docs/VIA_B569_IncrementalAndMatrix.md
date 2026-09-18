# 批569:增量擷取閘 · VRN 驗證矩陣 · PEIS 家族參數修(2026-09-17)

操作員三令 + 一個我自己造的坑。

---

## 〇、先修我自己弄壞的:`via-peis scan --family vdf,vrn` 回 ABSENT

```
[CGC_MDL158 v0100] scan · ABSENT
               why : 家族沒有可掃的起點:['vdf vrn']
```

PowerShell 把 `vdf,vrn` 當**陣列**傳,轉成行程參數時用空白相連,argparse 收到的是**一個字**。

難看的是:**冊裡早就有這一課**。短令冊裡 `ConvertTo-VIACleanArgs` 的註解逐字寫著

> 「PowerShell 把 `vrn,vap` 這種逗號寫法當**陣列**傳進來(不是字串);要攤平成逐個 token,
> 不然 `"$t"` 會變成 `"vrn vap"`(空白相連),家族驗證就把合法輸入擋掉。」

那是前面某一批繳過的學費。我加 `via-peis` 時沒去看既有輔助函式解過什麼坑。

**兩邊都修**(邊界上的東西只修一邊,換個殼就再壞一次):
- `Register v0216`:`via-peis` 走 `ConvertTo-VIACleanArgs`
- `CGC_MDL158 v0101`:自己切 `[,\s;]+`,四種寫法同解 —— `'vdf vrn'` · `'vdf,vrn'` · `['vdf,vrn','vap']` · `'VDF, VRN ;vap'`
- 認不得的家族**指名**並列出合法家族(不丟一個字典讓人猜)

你那一句原樣重跑:**674 檔 · 14,984 函式 → 2,606 能力 · 折疊 10,436 · 省 99.92%**。

---

## 一、VDF 增量擷取閘(`via-vdfinc`)—— 「不要重複 BATCH FETCHING」

> 同一句話你**批383 就說過一次**:「抓過的資料不必再抓」。說第二次=還在重抓。

照 L61 只做第一步、**零改線**:不動任何現役擷取引擎,先把真相攤開。

| 動詞 | 做什麼 |
|---|---|
| `scan` | 每張表的水位:列數 · 日期欄 · 最早 · 最新(**複用 MDL123 資料家 catalog**,不自己再寫一份掃庫) |
| `plan` | 自 `2023-01-01` 到最新,**只列缺口**(頭段缺 / 尾段缺 / 兩段都缺),並誠實說「目錄只看得到最早與最新兩點,**中間的洞看不到**」 |
| `plan --deep` | **逐日反連結**:庫裡 distinct 日期 vs 區間的差集,週末不算缺 —— 這才是真正的「照這份抓就不會重抓」清單 |
| `audit` | 靜態指名:哪幾支尾版擷取引擎**抓之前沒看庫** |

### `audit` 本境實測

```
觸網尾版 37 支 · 有看庫 31 · **重抓風險 4**
   ENG047_USMacroDetailFetcher v0101
   ENG050_OrderFetch           v0101
   ENG058_IndustryUnifiedMap   v0100
   ENG072_StoryRotationBridge  v0100
```

> ⚠️ 輸出裡明講了:這是**程式碼層的代理指標**,只能說「這支檔裡找不到看庫的痕跡」,
> **不等於「它一定重抓」**。真憑實據是你機器上跑 `plan --deep` 出來的逐日缺口。

**紀律**:零網路 · 連線一律 `read_only` · **沒有 `--apply`**(要真的去抓是你的手)。

---

## 二、VRN 驗證矩陣(`via-vrnmatrix`)—— 重點在「驗證過」三個字

「有值」不等於「對」。所以每一格不是「有沒有抓到」,是**「抓到而且驗得過」**,
而且**七欄的驗法都寫在檔裡、跑出來逐欄印** —— 你看得到我用什麼尺量。

| 欄位 | 驗法 |
|---|---|
| 股票代號 | 四到六碼,且與檔名對得上 |
| 報告日 | 解析得出,且**不是未來日** |
| 券商 | 非空,且 `broker_src` 標明出自正典冊 |
| 評等 | 落在樞紐(SUP_MDL749)的正典評等詞彙 |
| 目標價 | `> 0` 且 目標價/現價 落在 `0.2–5.0` |
| 上漲空間 | `upside_state` 是 `EXACT_MATCH_DB` / `ROUNDING_ONLY_DB`(**重算對得上**才算驗過) |
| 分析師 | `analyst_n ≥ 1` |

**四態**:`GREEN` 擷到且驗過 · `YELLOW` 擷到但**驗不過或驗不了**(兩者理由分得開)·
`NODATA` 沒擷到 · `ABSENT` 庫裡沒這一欄。

**零九頭龍**:`run` 只依序代跑 `ENG072`(首頁三法)→ `ENG073`(結構化入庫),不自己再寫一條擷取鏈。
零網路 · 唯讀連線(跑完比 mtime 證明沒寫) · 零 CDN 頁 · 無 `--apply`。

---

## 三、一貼即用

```powershell
Set-Location 'D:\OneDrive\文件\GitHub\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName

# ① PEIS 現在吃得下逗號了
via-peis scan --family vdf,vrn
via-peis run misc.upside --params '{"target":180,"current":120}'

# ② VDF 增量缺口(先讓資料家清點一次,再算缺口)
via-datahome catalog
via-vdfinc scan
via-vdfinc plan --since 2023-01-01
via-vdfinc plan --deep            # 逐日反連結:真正的不重抓清單
via-vdfinc audit                  # 誰抓之前沒看庫

# ③ VRN 驗證矩陣(你的樣本夾)
via-vrnmatrix run --in "C:\測試樣本報告"
#   → 主控台逐欄印 GREEN/YELLOW/NODATA/ABSENT
#   → VIA_Reports\vrn\matrix\VRN_MATRIX_latest.html(零 CDN,可直接開)
```

---

## 四、這一批自己抓到自己兩件(都是邊界值)

1. **夾具不「純」**:增量閘的「純頭缺」測表 `hi` 比 `until` 少一天,於是它**同時**有頭缺和一天尾缺,
   斷言算 366 而我期望 365 —— **程式是對的,錯的是尺**。修夾具不動程式,並補一張頭尾都缺的表。
2. **`in (None, "", 0)` 判空**:上漲空間 `0.0` 是**合法值**,會被誤判成「沒擷到」。
   第一版我開特例閃它,結果空的 upside 變 YELLOW,跟其他欄不一致(沒擷到 ≠ 擷到但錯)。
   正解是一條規則管到底,並補一檢專釘 `0.0`。

寫在 LL118 / LL119。
