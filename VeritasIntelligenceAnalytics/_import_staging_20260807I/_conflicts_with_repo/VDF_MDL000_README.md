# VDF Ecosystem · 完整編號最終版

**Build:** 2026-06-04 · **Total files:** 19 · **Total lines:** ~14,000

---

## 📂 完整模組編號表

### 🎯 MDL 001-099: 核心擷取引擎 (Data Engines)
| 編號 | 檔名 | 角色 | Lines |
|---|---|---|---|
| MDL001 | `VDF_MDL001_TWUniverseVerify.py` | SSOT regex 驗證 TWSE/TPEX universe | 585 |
| MDL002 | `VDF_MDL002_YFinanceFetchingEngine.py` | 175 tickers · 19 groups | 1,802 |
| MDL003 | `VDF_MDL003_SentimentMacroEngine.py` | AAII + CNN + FRED 47 + AKShare 13 | 1,466 |
| MDL004 | `VDF_MDL004_TWFullMarketEngine.py` | **TW 全市場 ~1,900 檔 · Daily+SMA+AvgVol+MCap+Consensus** ⭐ | 1,071 |
| MDL005 | `VDF_MDL005_TWStockFilter.py` | Consensus + Upside + PER + DPS Yield | 1,003 |
| MDL006 | `VDF_MDL006_FinancialModel.py` | 三大報表 + PE/PB Band Charts | 1,385 |
| MDL007 | `VDF_MDL007_SSOTResolver.py` | **SSOT 個股解析器 · 4 源 union (TWSE/TPEX/MOPS/YF)** ⭐ | 1,221 |

### 📚 MDL 101-199: 共用函式庫 (Libraries)
| 編號 | 檔名 | 角色 | Lines |
|---|---|---|---|
| MDL101 | `VDF_MDL101_OutputManager.py` | 5 格式輸出 SSOT (Parquet/DuckDB/CSV/JSON/GSheet) | 341 |
| MDL102 | `VDF_MDL102_FormatUpgrader.py` | Retrofit MDL001/002 既有輸出加 5 格式 | 340 |
| MDL103 | `VDF_MDL103_MasterRegistry.py` | 31 模組生態註冊中樞 | 723 |
| MDL104 | `VDF_MDL104_RegistryLoader.py` | JSON registry 載入 + 派發 fetcher | 472 |
| MDL105 | `VDF_MDL105_CrossValidator.py` | 5 種 consensus + 3 traffic lights | 467 |

### 🛠️ MDL 201-299: 工具腳本 (Tools)
| 編號 | 檔名 | 角色 | Lines |
|---|---|---|---|
| MDL201 | `VDF_MDL201_GenerateFullRegistry.py` | 從 MDL002/003 自動產 238-item registry | 484 |

### 🧪 MDL 301-399: 測試套件 (Test Suites)
| 編號 | 檔名 | 角色 | Lines |
|---|---|---|---|
| MDL301 | `VDF_MDL301_SystemTest.py` | 系統測試 8 個 Rich tables | 459 |
| MDL302 | `VDF_MDL302_FinalActivation.py` | 9-phase E2E 端到端 + 12 Rich tables | 1,058 |
| MDL303 | `VDF_MDL303_RegistryActivation.py` | Registry 4-phase 整合測試 + 6 Rich tables | 367 |

### 📋 MDL 401-499: Registry 資料 (JSON)
| 編號 | 檔名 | 角色 | Items |
|---|---|---|---|
| MDL401 | `VDF_MDL401_RegistrySchema.json` | Draft-07 schema (JSON 結構規範) | — |
| MDL402 | `VDF_MDL402_RegistrySample.json` | 18-item 示範 registry | 18 |
| MDL403 | `VDF_MDL403_RegistryFull.json` | **238-item 全 inventory** | 238 |
| MDL404 | `VDF_MDL404_CoverageReport.json` | Inventory 盤點 + gap 建議 | — |

### 🌐 MDL 501-599: 前端 UI
| 編號 | 檔名 | 角色 |
|---|---|---|
| MDL501 | `VDF_MDL501_DataModuleController.html` | 8-tab 全生態 UI (31 模組總覽) |

---

## 🚀 Windows 跑法（按依賴順序）

```powershell
# 一鍵全系統驗證 (跑所有 9 phases)
python VDF_MDL302_FinalActivation.py --no-pause

# 生產執行 (依依賴順序)
python VDF_MDL001_TWUniverseVerify.py --no-pause          # 1. TW universe
python VDF_MDL002_YFinanceFetchingEngine.py --no-pause    # 2. YF 175 tickers
python VDF_MDL003_SentimentMacroEngine.py --no-pause      # 3. AAII+CNN+FRED+AKShare
python VDF_MDL005_TWStockFilter.py --no-pause             # 4. Consensus
python VDF_MDL006_FinancialModel.py --no-pause            # 5. PE/PB Band

# 跨來源驗證系統
python VDF_MDL201_GenerateFullRegistry.py --validate      # 6. 重建 238-item registry
python VDF_MDL104_RegistryLoader.py --themes Rates,Inflation --dry-run  # 7. 載入 + 派發
python VDF_MDL105_CrossValidator.py --selftest            # 8. 跨來源驗證 self-test
python VDF_MDL303_RegistryActivation.py                   # 9. Registry 4-phase 整合測試

# Retrofit 升級 (補 MDL001/002 既有輸出多格式)
python VDF_MDL102_FormatUpgrader.py --no-pause            # 10. Multi-format upgrade

# 註冊中樞 (產 0-0-MasterRegistry/)
python VDF_MDL103_MasterRegistry.py --no-pause            # 11. 31 modules registry

# 開 UI
start VDF_MDL501_DataModuleController.html
```

---

## 🔗 依賴關係圖

```
VDF_MDL101_OutputManager       (核心函式庫,所有寫檔模組依賴)
       ↑
       │  imports
       │
  ┌────┴────┬────────────┬────────────┬────────────┐
  │         │            │            │            │
MDL003    MDL005      MDL006      MDL102      MDL104
                                              CrossValidator
                                                  ↑
                                                  │
                                              MDL105
                                              CrossValidator
                                                  ↑
                                                  │
                                              MDL303
                                              RegistryActivation
                                                  ↑
                                                  │
                                              MDL302
                                              FinalActivation
```

---

## 📊 系統規模

```
全生態        : 19 個編號檔案 + ~14,000 行
擷取項目      : 238 unique via_code (FRED 47 + YF 175 + AKShare 13 + Sentiment 2 + TW dynamic 1)
跨來源驗證    : 14 個 multi-source 項目 · 13 個 cross-check 啟用
輸出格式      : Parquet (必選) + DuckDB + CSV (utf-8-sig) + JSON + GSheet (stub)
測試覆蓋      : 4 套測試 · 9 phases · 68 files integrity
最終驗證      : ✅✅✅ ALL PERFECT
```
