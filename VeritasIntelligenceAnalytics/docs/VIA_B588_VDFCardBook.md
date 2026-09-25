# 批588 — VDF 全境:能跑不能跑 · 哪些是債哪些是律 · 一本卡書取代掃描

操作員令:`先幫我檢查測試VDF引擎有哪些 · 先將所有參數庫邏輯庫政策庫整理好與VDF相關的 ·
整合去重去衝突 · 引擎類似的整合勿遺失 · 用 [Essentia] · 讓AI讀取時不需要大量掃描而是一看就知道它的功能`

中途操作員問:**「用它來執行不是不耗費 TOKEN?」**

那句話點中了。前半段我拿 VDF 40 支引擎逐支跑 `--selftest`、逐行印出來 —— 那正是 Essentia
要取代的事,而且**下一次還要再燒一次**。後半段全部改走能力庫,只出聚合。
F1 那一趟仍然留著,因為它問的是原始碼答不出的問題:**跑不跑得動**。

---

## 一、VDF 引擎有哪些 · 能不能跑(F1)

`functional modules/VDF/engine` 尾版 **45 支**,其中有 `--selftest` 的 **40 支**:

| | 支 | |
|---|---|---|
| GREEN | 36 | |
| RED | 3 | ENG061_FeatureStore · ENG062_GroupFeatureLayer 是 **duckdb 鎖衝突**(平行搶 `vdf_tw_market.duckdb`,序跑即綠=併發假紅)<br>**ENG070_GroupClassificationIndex_v0111 是真紅**:十八檢 OK 11 · FAIL 7(⑦故事性分群 ⑧故事階層守恆 ⑩跨窗比較) |
| NODATA | 1 | ENG072_StoryRotationBridge_v0101(上游表缺,誠實多態) |

另有 **5 支沒有 `--selftest`**:`ENG051_ActiveTWETF_Holdings_v0102` · `VDF_MDL002` ·
`VDF_MDL003` · `VDF_MDL007` · `sector_rotation_capital_flow_engine`。

---

## 二、去重去衝突:**同一件事出現 N 次,不一定是債**

VDF 144 檔 / 2522 函式 → **471 能力**,折疊 1555、近似 468,省 99.53%。
`members>1` 的重複實作總共 **1497 份**。

但最上面那幾個是**律規定每一檔都要有**的:

| 能力 | 份 | 為什麼它不是債 |
|---|---|---|
| `misc.via_net` | 110 | 批115 VDF 全檔掛網路工具令 · 統包網路工具橋 |
| `misc.status` | 87 | 統一調度契約動詞 `status()` |
| `misc.net_none` | 40 | 同一條橋的伴生 `_net_or_none`:工具缺席回 None |
| `validate.open` | 40 | 法遵雙閘 `gate_open(env)`:每檔自己驗,不靠上游代驗 |
| `misc.net` | 23 | 同一條橋的伴生 `_net` |
| `misc.probe` | 17 | 統一調度契約動詞 `probe()` |

**照著這些去「整合」,等於拆掉律要求的東西。**那是判錯的紅燈,而且是會被照做的那一種。
→ **L74 契約不是債律**:分三層報,分層依據寫在程式裡、可以被質疑。

```
VDF 1497 份重複
  ├ 契約  6 類 /  311 份   律規定每檔都有 → 報數字,不計債
  ├ 泛名  9 類 /  554 份   build.any / misc.tuple 這種語意空殼 → 不計債
  └ 真債 272 類 / 1186 份   同一件事各寫一份 → 附函式名與簽章
```

**真債前幾名**(每一筆都是同一個簽章各寫一份):

| 能力 | 份 | 簽章 |
|---|---|---|
| `load.ckpt` / `save.ckpt` | 32 / 32 | `load_ckpt()` · `save_ckpt(ck)` |
| `misc.connect_ro` | 25 | `_connect_ro(dbp)` |
| `misc.num` | 24 | `_num(v)` |
| `misc.diag` | 23 | `_diag(exc)` |
| `save.parquet` | 23 | `write_parquet(rows, lane, out_root)` |
| `misc.ready` | 21 | `_data_ready()` |
| `misc.insert_missing` | 15 | `_insert_missing(con, table, rows)` |
| `misc.fred_key` / `misc.trading_days` | 14 / 14 | `_fred_key()` · `trading_days()` |
| `lane_*` 十餘條(etf_book / global / us_macro / valuation…) | 各 12 | ETF 與總經車道,一條一條各寫一份 |

**勿遺失**:本批**一份都沒有併**。`debt` 只攤開帳,附函式名與簽章讓人核對;
併不併、併成什麼,是操作員的裁定(LL90)。

---

## 三、與 VDF 相關的四庫:冊都在,但**沒有覆蓋 VDF 真正的重複**

四冊都在位、名實相符:
`VIA_Central_Params_SSOT`(參數)· `VIA_Lib_Registry`(邏輯)·
`VIA_Policy_Laws_SSOT`(政策)· `VIA_Feature_Catalog`(因子)。

拿 VDF 前 40 大真債逐筆對四冊(**詞界比對**,不用子字串 —— LL137:`num` 會被
`number`/`enum` 亂命中,兩個方向都會錯):

> **35 / 40 四冊都查無。**

也就是說:VDF 重複最兇的那些東西 —— checkpoint 讀寫、唯讀連線、parquet 落檔、
交易日曆、FRED 金鑰、十餘條資料車道 —— **一本冊都沒收**。
冊不是壞的,是**沒伸到 VDF 這一塊**。

---

## 四、「一看就知道它的功能」—— 能力卡書

`via-peis book --family vdf` → `supportive modules/registry/VIA_Essentia_CardBook_VDF_v0100.json`

```
VDF 45 支引擎   原始碼 519,902 token  →  卡書 8,392 token   省 98.39%
```

一張卡回答五件事,不多不少:**它是誰 · 它做什麼 · 怎麼叫它 · 它碰哪些資料 · 它靠誰**。

```json
{ "engine": "VDF_ENG056_ChipBackfill_v0102",
  "purpose": "VDF_ENG056_ChipBackfill — 台股籌碼欄歷史回補(批140;via-chip)",
  "verbs": [], "flags": ["--days", "--derive", "--status", "--workers"],
  "contract": ["run", "selftest", "status"],
  "tables": ["tw_chip_derived", "tw_chip_inst", "tw_chip_margin", "tw_daily_prices"],
  "deps": ["SUP_MDL740_NetUnified"], "owns_n": 18 }
```

欄位全部由 **AST 與能力庫推導**,沒有一個字是形容詞;推不出來就留空,**留空不補話**。

覆蓋率:用途欄 45 缺 **1** · 叫不出來(無動詞無旗標無契約)只剩 **2 支**
(`VDF_MDL007_SSOTResolver` 與 `sector_rotation_capital_flow_engine` —— 它們本來就是
沒有 CLI 的函式庫,和 F1 量到「沒有 `--selftest`」對得上)。

### 做這本書時踩的三個洞,三個都是**尺的洞不是引擎的洞**

| 欄 | 第一版 | 結果 | 根因 |
|---|---|---|---|
| `purpose` | 正則從檔頭抓 docstring | 45 支**空 21** | **批115 的網路橋注在 docstring 前面**,檔頭第一個字串早就不是 docstring 了 → 改用 `ast.get_docstring`(問語法樹,不問長相) |
| `verbs` | 只認 argparse `choices=[...]` | 45 支**空 42** | 本樹最常見的是 `"--status" in args` 手寫分派;四種寫法都要認 |
| `tables` | `from|join\s+(\w+)` | 把 `from datetime import` 當成一張表 | 沒排掉 import 行 |

**卡上出現空欄的時候,先問是引擎沒說,還是尺沒抓到。**這三次都是後者。
四種分派寫法現在用合成語料釘進自測 ㉖;再出現第五種會空,但會空得有紀錄。→ **LL141**

---

## 五、鎖住 · 但未來可改

卡書是**再生的**,不是手抄的:引擎變了就重跑 `via-peis book --family vdf`,卡書跟著變。
所以「鎖住」鎖的不是內容,是**產生方式** —— 卡書只寫一個檔、不碰任何來源檔(正本零觸碰),
四種分派寫法與三個抽取洞都有自測守著。要改模塊化,改的是引擎,卡書自己會跟上。

## 六、登錄(L70:沒有動任何 `.ps1`)

- `CGC_MDL161_PEISCapabilityEngine_v0105.py` —— `debt` / `book` 是既有短令 `via-peis`
  的新動詞,不是新短令;自測 25 → **29 檢**
- `VIA_Essentia_CardBook_VDF_v0100.json` —— 卡書本身(入倉,因為它就是要被讀的正本)
- `CGC_MDL064_SelftestGrid_v0356.py` —— PEIS 站 二十五 → 二十九檢
- `VIA_Essentia_Product_SSOT_v0100.json` —— 動詞 6 → 8;實測補 VDF 專段;已知債 +1
- `VIA_Policy_Laws_SSOT_v0100.json` —— **L74** · **LL141**(律 71→72,課 140→141)
- `VIA_AutoCode_Registry_v0100.json` —— 台帳 1143→1146
