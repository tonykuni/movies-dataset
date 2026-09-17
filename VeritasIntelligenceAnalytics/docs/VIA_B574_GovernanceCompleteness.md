# 批574 · 制度健全度稽核 —— 「我們制度健全了嗎」的誠實答案

量測時間 2026-09-17 · 引擎 `CGC_MDL164_GovernanceCompletenessAudit_v0100.py`(13 檢全綠)
短令 `via-govaudit` / `制度稽核` · 全格子第 240 站 · 零網路、無 `--apply` 不寫任何檔

---

## 一、一句話結論

**框架是完整的(17/17 在),但深度不是。** 三本冊只有一個活讀者、七處有多冊並存。
框架完整最容易被讀成「健全」——這份文件存在的目的就是不讓它被這樣讀。

## 二、判準:三個條件,缺一不可

一本治理冊要算「健全」,不是看檔案在不在,而是三件同時成立:

| 條件 | 問題 | 不成立時 |
|---|---|---|
| **冊在** | 檔案存在嗎 | `ABSENT` |
| **有料** | 筆數 > 0 嗎 | `NODATA` |
| **有活讀者** | 尾版活檔裡真的有人 import / 讀它嗎 | **`ORPHAN`** |

`ORPHAN` 是三種裡最危險的:**它不是紅燈**(什麼都沒壞),但它也沒在治理任何東西,
而且它會讓制度**看起來**完整。所以引擎對 ORPHAN 一律加註「不是紅燈但也沒在治理」。

## 三、實測:14 庫 + 3 機制

```
GREEN 17 · PARTIAL 0 · ORPHAN 0 · NODATA 0 · ABSENT 0
```

| # | 冊 | 筆數 | 活讀者 |
|---|---|---|---|
| 1 | 政策庫 `VIA_Policy_Laws_SSOT_v0100.json` | 129 | 4 |
| 2 | 參數庫 `VIA_Central_Params_SSOT_v0100.json` | 25 | **1** |
| 3 | REGEX 規則庫 `VIA_SSOT_RegexDict_v0100.json` | 25 | 3 |
| 4 | 同義字管理庫 `VIA_Central_Synonym_Regex_v0100.json` | 12 | 5 |
| 5 | 邏輯庫 `VIA_Lib_Registry_v0100.json` | 21 | 2 |
| 6 | 因子庫 `VIA_Feature_Catalog_v0100.json` | 11 | **1** |
| 7 | 納管模組庫 | — | ✓ |
| 8 | 已用模組庫 `VIA_Unified_Register_v0100.json` | — | ✓ |
| 9 | 報表模板與視覺資產庫 `VIA_UI_TemplateSSOT_v0100.json` | — | ✓ |
| 10 | 工作流與任務排程庫 | — | ✓ |
| 11 | 外部端點與 API 路由庫 `VIA_NetGate_Wiring_Register_v0101.json` | 94 | **1** |
| 12 | 資料庫 `VIA_DB_Table_SSOT_v0100.json` | 54 | 3 |
| 13 | 審計帳本庫 `VIA_AutoCode_Registry_v0100.json` | 1113 | 139 |
| 14 | 異常與修復日誌庫 `VIA_Problem_Ledger_v0100.json` | 18 | 4 |
| A | INTERFACE 自適應快速對接 `VIA_Interface_Contract_Registry_v0100.json` | 承載件 6 | ✓ |
| B | 上下交互 / 向下核對 `CGC_MDL149` | 承載件 18 | ✓ |
| C | 合約自適應 `VIA_Engine_Contract_v0100.json` | 承載件 8 | ✓ |

## 四、不足之處(綠燈底下的兩件事)

### 4.1 單一讀者 3 本 —— 那一支引擎一動,這本冊就變孤兒

| 冊 | 唯一讀者 |
|---|---|
| 參數庫 | `via_params_central` |
| 因子庫 | `VDF_ENG061_FeatureStore` |
| 外部端點與 API 路由庫 | `via_net_injector` |

不是紅燈,是**單點**。補法有二:讓第二支真的去讀(而不是為了湊數字掛一行 import),
或承認它就是那一支的私有設定、從治理冊降級。**哪一種,是操作員的判斷。**

### 4.2 多冊並存 7 處 —— 哪一本是正本 = 操作員裁定(LL90)

| 冊 | 主 | 另 |
|---|---|---|
| REGEX 規則庫 | `VIA_SSOT_RegexDict_v0100.json` | `VIA_Central_Synonym_Regex_v0100.json` |
| **同義字管理庫** | `VIA_Central_Synonym_Regex_v0100.json`(12 筆) | `VRN_FieldRules_SSOT_v0100.json` |
| 已用模組庫 | `VIA_Unified_Register_v0100.json` | `VIA_Engine_Consolidation_Register_v0100.json` |
| 報表模板與視覺資產庫 | `VIA_UI_TemplateSSOT_v0100.json` | `VIA_Brand_SSOT_v0100.json` |
| 外部端點與 API 路由庫 | `VIA_NetGate_Wiring_Register_v0101.json` | `VDF_ENG046_FetchMatrixRegistry.py` · `..._v0100.json` |
| 資料庫 | `VIA_DB_Table_SSOT_v0100.json` | `VIA_DataHome_SSOT_v0100.json` |
| 審計帳本庫 | `VIA_AutoCode_Registry_v0100.json` | `..._v0100_sha1fbffae2.json` |

最該先看的是**同義字管理庫**:中央那本只有 **12 筆**,比它名義上治理的 `VRN_FieldRules_SSOT`
還薄——名義上的正本比下游還瘦,通常代表真正在用的是下游那本。
**引擎只點名,不改字**(LL90:同義的裁定權在操作員)。

## 五、Veritas 統一表頭:立為第四級 `TARGET`

操作員給的表頭規格(三行 13px/26px/13px、`#8C99A6`/`#F0F4F8`/`#737D87`、六個子系統定位)
已寫進 `CGC_MDL160_UIUnifyGate_v0101.py`,用 `via-uiunify header` 可印出正典供施工者抄。

**但它不判燈。** 先量再定級:本境 106 張活頁

```
vh_struct 0/106 · vh_brand 40/106 · vh_three 0/106 · vh_ink 0/106
GREEN 43 · YELLOW 20 · RED 43
```

判 LAW 會生 **106 盞假紅**、判 UNIFY 會生 106 盞黃,兩種都會把真正該修的 **43 紅**
(絕大多數是零 CDN 違規)淹掉。淹掉真紅的紅燈比假綠更傷,因為它讓人學會忽略紅燈。
所以加第四級:**`TARGET` = 已立契約、尚未施工、永不判燈,只報覆蓋率**,
而且 `plan` 不把 TARGET 列成待修——它不是債,是路線圖。

## 六、怎麼用

```powershell
via-govaudit              # 或 制度稽核 —— 14 庫 3 機制逐條
via-govaudit plan         # 只列不健全的,每列都講得出怎麼補
via-uiunify header        # 印 Veritas 統一表頭正典規格
via-uiunify scan          # 106 頁四級判燈 + 表頭覆蓋率
```

## 七、掉球(等操作員)

- 單一讀者 3 本:第二讀者 or 降級 —— 操作員決定
- 多冊並存 7 處:哪本是正本 —— 操作員裁定(LL90)
- 43 張 RED 頁:owner 引擎自己再生(閘不代改頁)
- Veritas 表頭 0/106:契約已立,施工待排
