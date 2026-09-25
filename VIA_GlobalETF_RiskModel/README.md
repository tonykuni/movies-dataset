# VIA_GlobalETF_RiskModel — 全球 ETF 風險同步觀測引擎（MDL009 ETFRISK）

> 用 ETF 看全球價格正在怎麼投票，再用美元、利率、Fed、財政、經常帳與商品去拆解投票原因。

`VIA-MDL008-ETFFLOW`（VIA_GlobalETFFlow，T1 真流）的姊妹引擎：MDL008 回答「錢往哪裡走」，
本引擎（MDL009）回答「這個方向處在什麼風險狀態、由什麼因子驅動、盈餘與估值撐不撐得住」。
純 Python 標準庫，零外部依賴，離線可跑。

## 快速開始

```bash
python3 run_monitor.py                # T4 合成 demo 世界 → output/RUN_*/dashboard.html
python3 run_monitor.py --selftest     # 離線驗收閘（15 gates，EXIT 0/1）
python3 -m unittest discover -s tests # 單元測試（22 案例）

# 接真實資料（T3 價量估算層）
python3 run_monitor.py --source csv --prices prices.csv --macro macro.csv
```

CSV 格式：寬表，第一欄 `date`（YYYY-MM-DD 升冪），其餘欄名＝ticker；
`macro.csv` 需含 `DGS2, DGS10, DFII10, T10YIE`（FRED 序列名）。缺值自動向前補。

## 模組地圖（MCFL）

| MCFL | 檔案 | 職責 |
|---|---|---|
| M00 | `engine/mathkit.py` | robust-z（MAD，與 MDL008 FIS 同式）、`100·tanh(z/2)`、corr、lead-lag、PC1 冪迭代 |
| M10 | `engine/data_layer.py` | CSV 載入、T4 demo 世界（regime 腳本化、種子再現） |
| M15 | `engine/factors.py` | 因子面板 + SSOT 指標文法解析（`ret_20_UUP`、`dd_60_HYG_IEF`…） |
| M20 | `engine/scores.py` | 美元壓力 / 利率衝擊 / 信用壓力 / 商品通膨 + 財政脆弱度 + 跨資產 Pulse + 區域利差×匯率勢能 |
| M22 | `engine/rotation.py` | RRG 象限輪動：X=RS 水位 z、Y=RS 動能；Q1領先 / Q2改善★ / Q3落後 / Q4轉弱⚠ |
| M25 | `engine/sync.py` | ETF×因子同步矩陣（20/60/120d）、領先滯後、回撤同步、離散度、PC1 共振占比 |
| M28 | `engine/regime.py` | 9 態規則 Regime（規則全在 config，逐訊號可稽核） |
| M35 | `engine/earnings.py` | Forward P/E 倒算 EPS 結轉（Calculated_NotOriginal）、staleness 五級、ERP / USD-adj ERP、惡魔驗證 |
| M40 | `engine/report.py` | JSON 輸出、`run_ledger.jsonl`（append-only）、Visual Lock 儀表板 |

SSOT：`config/global_etf_risk_config.json`（宇宙 53 檔、分數組件、Regime 規則、輪動/同步/結轉參數全在此，改規則不改碼）。

## 五大分數（合成式與 MDL008 FIS 對齊）

```
component_z = robust_z( metric[t], metric[t-252 .. t-1] )   # T-1：樣本不含當日
fis         = 100 · tanh( weighted_mean_z / 2 )             # ±100
risk        = 50 + fis/2                                    # 0..100
分級：<30 低 · <60 中 · <80 高 · ≤100 極端（同 Crash Score 分帶）
```

| 分數 | 組件 |
|---|---|
| 美元壓力 | UUP 20d 動能、Δ實質利率、HYG/EMB 相對美債落後、EMLC 弱勢 |
| 利率衝擊 | Δ2Y、Δ10Y、Δ實質利率、TLT 下跌 |
| 信用壓力 | HYG/IEF、LQD/IEF 比值 60d 回撤、EMB 回撤 |
| 商品通膨 | USO / CPER / DBC 60d 動能 |
| 財政脆弱度 | 跨國百分位合成（債務、財政、經常帳、外債、外儲、利息負擔…）＋ ETF 市場印證（雙弱旗標） |

另有：跨資產 Risk Pulse `(SPY+1.5·IBIT) − (IEF+0.8·VNQ)` 的 60d z、
區域利差×匯率勢能 `(local10Y − US10Y) × ret20(FX ETF)`。

## Regime（9 態，規則式可稽核基線）

risk_on_global_reflation · usd_squeeze · rate_shock · growth_scare · stagflation ·
credit_stress · fiscal_dominance · china_demand_shock · ai_concentration_boom

每條訊號輸出「實際值 / 門檻 / 命中與否 / 權重」，惡魔驗證可逐條覆核。
HMM / MS-VAR / DTW / Optimal Transport 屬 Tier-2 升級，登錄於
`ssot/SSOT_ModuleRegistry.v023.json`，必須在外部標籤上打贏本基線才可取代（反循環）。

## Forward Earnings 結轉規則（M35）

1. 發布日：`Implied_EPS = Index_Level / Forward_PE` → 標 `Calculated_NotOriginal`
2. 下次更新前 EPS 凍結；**每日重算的是估值不是盈餘**：`PE_daily = PE_pub × (Proxy今價/發布日價)`
3. staleness：≤7 FRESH · ≤21 USABLE · ≤45 STALE_WARNING · ≤90 NEEDS_REFRESH · >90 REJECT
4. `ERP = 100/PE_daily − Local10Y`；`USD_adj_ERP = ERP − FX貶值風險 − 美元資金壓力`
5. 惡魔旗標：rounding（>0.05%）、來源分歧（>5%）、估值急速變貴（proxy +8% 而 EPS 凍結）、proxy 錯位、horizon/index_type 未標

## 真值階梯與治理

- **T1 真流**：`ΔShares × NAV`——只有 MDL008 產生；本引擎不畫金額箭頭（防 T4 偽裝 T1）
- **T3 估算**：本引擎全部輸出（分數/輪動/同步/隱含EPS），evidence 一律 `Der`/`Est`
- **T4 模擬**：demo 世界，provenance 全鏈掛 `synthetic_demo`，儀表板 critical 橫幅
- 只增不減：`output/RUN_*` append-only、`run_ledger.jsonl` 只追加；來源檔只讀
- UTF-8（no BOM）；z 樣本一律截至 t−1（T-1 紀律）；權重門檻只在 SSOT，禁對自身分數校準
- 誤判因素登錄（G01–G12）見 `ssot/SSOT_RiskFlowFormulaRegistry.v023.json`

## 真實資料化路徑

| 需求 | 來源 | 接法 |
|---|---|---|
| ETF 日價 | Stooq / Yahoo（MDL008 已有抓取器） | 導出寬表 CSV → `--prices` |
| 利率宏觀 | FRED：DGS2 / DGS10 / DFII10 / T10YIE | CSV → `--macro` |
| 財政/外部 | IMF WEO / World Bank WDI / BIS | 覆寫 `data/demo_macro_fundamentals.json` 並改 evidence |
| Forward P/E | FactSet Earnings Insight（公開引述）/ MSCI 月報 / LSEG | 覆寫 `data/demo_forward_pe.json`（append-only 版本化） |
| T1 真流疊加 | MDL008 `etf_matrix.json` | config `def_flow_overlay`（介面已留） |

## 輸出

`output/RUN_<stamp>_VIA_GLOBAL_ETF_RISK/`：
`dashboard.html`（單檔自足、Visual Lock、紅漲綠跌）、`scores.json`、`regime.json`、
`rotation.json`、`sync.json`、`fragility.json`、`forward_earnings_ledger.json`、
`run_summary.json`；根目錄 `run_ledger.jsonl` 逐 run 追加。
