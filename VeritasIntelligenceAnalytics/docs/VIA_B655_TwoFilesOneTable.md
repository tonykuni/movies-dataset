# 批655 · 寫的人跟讀的人,指到兩個不同的檔案

## 先說結果:批654 的修**生效了**

你的畫面上:

```
[EXACT_MATCH_DB]   6873 泓德能源  升幅 報告=22.7 算=22.7 庫算=22.7
[ROUNDING_ONLY_DB] 6768 志強-KY   升幅 報告=23.0 算=22.9 庫算=22.9
[FORMULA_MISMATCH_DB] 3231 緯創   升幅 報告=44.7 算=44.7 庫算=50.7   ← 會變壞的那一半也出現了
```

`_DB` 後綴出來了,而且該降級的也降了。

## 但矩陣那一欄一個數字都沒動

```
上漲空間   upside_state 為 EXACT_MATCH_DB / ROUNDING_ONLY_DB     0     38     67
```

跟上一跑**完全相同**。

### 先證尺,不要先改尺

把 `_DB` 態灌進一本真庫,餵給 `matrix()`:

```
造出 EXACT_MATCH_DB 列數: 30
  上漲空間欄 → {'GREEN': 30, 'YELLOW': 0, 'NODATA': 51}
```

**尺是好的。** 它會給綠。

### 壞的是「在講哪一批資料」

| | 解出來的檔案 |
|---|---|
| **ENG073 寫** `_resolve_db()` → 批490 **資料家優先** | `…\VIA System\via_database\…\VDF\output_hub\mega\`**`vdf_tw_market.duckdb`** |
| **ENG083 讀** `DEFAULT_DB` → **寫死** | `functional modules\VRN\output\`**`vrn_reports.duckdb`** |

你的畫面第一行其實一直在講這件事:

```
[庫解析] 資料家目錄頁→C:\Users\tonyk\VIA System\via_database\…\vdf_tw_market.duckdb
```

**兩本都在、兩本都有 `vrn_report_basic`,所以沒有任何一支引擎會喊。**
矩陣只是安靜地讀了一張舊表 —— 而人會以為「修了沒用」。

### 容器結構上看不見這個洞

容器沒有資料家(`VIA_DATA_HOME` 沒設),兩條路解出同一個檔案。
所以這個分歧從來沒有在我這邊出現過。 → **LL293**

## 修法兩層

1. **讀的人照寫的人那一條路解**(`--db` 仍然最高優先)。
2. **把「另外還有幾本庫也有這張表」當場印出來** —— 第二顆頭要被看見,不是被猜:

```
  [庫] …\vdf_tw_market.duckdb
       ← 資料家目錄頁 VIA_DB_VDF_TW_MARKET(與 ENG073 同一條路)
  [**第二顆頭**] 另有 1 本庫也有 vrn_report_basic —— 寫的人與讀的人可能指到不同檔案
         105 列 · 資料家目錄頁 VIA_DB_VDF_TW_MARKET(與 ENG073 同一條路)
               C:\Users\tonyk\VIA System\…\vdf_tw_market.duckdb
         105 列 · VRN 舊路徑 output/vrn_reports.duckdb
               C:\…\functional modules\VRN\output\vrn_reports.duckdb
```

檢 (54) 造一本替代庫 + 設環境變數驗解析與頭數;**把那一行退回寫死 → (54) 當場 FAIL(53/54)**。

---

## 另外:你要的方法已存檔

`docs/methods/VIA_METHOD_MegaPrompt_20Accel_6Streams_v0100.md` —— 逐字保存,**只存不改正典**。

存檔件後面附了逐條對照,因為**存檔不等於施工**:

| 方法裡的項目 | 母系統正主 |
|---|---|
| 20 加速器 | `CGC_MDL156`(**25** 格) |
| 三輪全景式分析 | `CGC_MDL158`(`via-panorama`) |
| AST 彈性/精準定位 | `CGC_MDL146` · VCGC `registry-sync` |
| SSOT 對齊 | `CGC_MDL115`(`via-ssotregex`)· `CGC_MDL155` |
| 沙盒回歸 | 262 站自測格子 |
| 版本回滾 | 尾版律 · `CGC_MDL167_RegenRevert` |
| 非阻塞啟動 + 動態進度條 | `via-run25` · Id 11/12/13 |
| RYG HTML UI Matrix | `VRN_MATRIX_latest.html`(五態) |

**只有兩項是新的**:四大分區 `MODULE/ENGINE/FUNCTION-LIB/OTHERS`,以及固定六道流程的編號分工。
**要不要施工,裁定權在你。** 我一個引擎都沒建、一個正典都沒改、一個短令都沒加。

---

## 你這邊

```powershell
git pull origin claude/via-envmanager-governance-7cls8h
. .\VeritasIntelligenceAnalytics\Register-VIA-Commands-v0231.ps1
via-run25
```

矩陣這次會先印出**它讀的是哪一本庫**。如果印出「第二顆頭」,那就是你機器上真的有兩本 —— 
而上漲空間那一欄應該會第一次出現 GREEN。

`roster` 仍是 NODATA(6 檔老 ETF 缺價),補價要 `VIA_NET_CONSENT`,那是你的手。
