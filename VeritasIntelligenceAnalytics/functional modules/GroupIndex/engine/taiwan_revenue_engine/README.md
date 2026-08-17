# 台股月營收動能引擎 (Taiwan Stock Monthly Revenue Engine)

一套「抓取 + 分析 + 儀表板」的月營收動能系統,實作三層動能模型,並把原物料/週期股分流。
資料來源為官方 **MOPS 公開資訊觀測站**,涵蓋全上市 (TWSE) + 上櫃 (TPEX),預設保留近 36 個月。

---

## 1. 這套引擎在做什麼

三層動能模型 (對應你的框架):

| 層級 | 判準 | 角色 | 對應 MOPS 官方欄位 |
|------|------|------|--------------------|
| **Layer 1** | 累計 YoY | 主判準 · 年度大局錨點,最不易被騙 | 累計營業收入－前期比較增減(%) |
| **Layer 2** | 多月 YoY 趨勢 | 第二判準 · 成長品質 (連續正月數 / 均值 / 波動) | 營業收入－去年同月增減(%) |
| **Layer 3** | MoM vs 季節性 | 第三判準 · 動能拐點 (淡季不淡 / 旺季不旺) | 營業收入－上月比較增減(%) |
| 輔助 | 2 年 CAGR | 修正基期扭曲 (疫情 / 庫存循環) | 由當月營收序列計算 |

**原物料 / 週期股分流**:水泥、塑膠、橡膠、鋼鐵、造紙、玻璃陶瓷、油電燃氣、航運、化學等產業,
月營收 = 價格 × 量,價格波動遠大於量,月營收 YoY·MoM 嚴重失真。這些公司會被 **排除於月營收排名**,
並提示改看:價格 YoY / 庫存 YoY / 產能利用率 / 毛利率 YoY。

**輸出**:
- `data/monthly_revenue.csv` — 全市場長格式原始資料 (公司-月份矩陣)
- `data/analysis.csv` — 每家公司最新月的動能指標、分數、型態、分級
- `output/monthly_revenue_dashboard.html` — 單頁 HTML 儀表板 (可離線開啟)

---

## 2. 安裝

```bash
cd taiwan_revenue_engine
pip install -r requirements.txt
```

需 Python 3.9+。

---

## 3. 使用

```bash
# (0) 免連網先看效果: 用合成資料跑通全流程 (含增量資料庫), 產生範例儀表板
python -m twrevenue.cli demo

# (1) 抓取 MOPS 全上市+上櫃近 36 個月 -> 增量寫入 parquet/duckdb
python -m twrevenue.cli fetch

# (2) 分析 (自 parquet 讀 36 個月視窗) -> data/analysis.csv
python -m twrevenue.cli analyze

# (3) 產生 HTML 儀表板 -> output/monthly_revenue_dashboard.html
python -m twrevenue.cli report

# 一條龍 (fetch + analyze + report)
python -m twrevenue.cli run

# 顯示 + 驗證族群分類 (編輯 twrevenue/groups.csv 後執行)
python -m twrevenue.cli groups

# 跑全套內建測試 (解析/歸類/資料庫/公式, 8 項)
python -m twrevenue.cli selftest
```

### 累計增量資料庫 (parquet + duckdb)

- `data/revenue.parquet` — **SSOT**。歷來抓過的所有月份、所有個股永久累積 (不只 36 個月),
  主鍵 `(stock_id, year, month)` 去重;公司更正月營收時以最新公告覆蓋。
- `data/revenue.duckdb` — SQL 查詢層,每次更新後自 parquet 重建 `monthly_revenue` 表:
  ```sql
  -- 例: 查台積電近 12 個月
  SELECT * FROM monthly_revenue WHERE stock_id='2330' ORDER BY date DESC LIMIT 12;
  ```
- 每月只需重跑 `fetch`:已快取月份不重抓、資料庫只增量合併新月份 (跑第二次淨增 0,冪等)。
- 分析永遠取「最近 `months_back` 個月」視窗,歷史完整保留供回測。

> **重要 — 關於抓取**:此引擎是為在**你自己的電腦**執行而設計。
> 首次 `fetch` 會抓 36 個月 × (上市/上櫃) × (國內/KY) ≈ 上百個頁面,
> 每次請求間隔 5 秒 (見 config),完整抓一次約需 10–20 分鐘,屬正常。
> 抓過的月份會快取在 `data/raw_cache/`,之後每月只需補抓最新一個月。

---

## 4. 設定 (`config.yaml`)

重點參數:

- `fetch.months_back` — 抓幾個月 (預設 36)
- `fetch.request_delay_sec` — 請求間隔秒數 (MOPS 有速率限制,建議 ≥ 3)
- `fetch.base_hosts` — 主域名與備援域名 (MOPS 曾多次遷移網域,若主域連不到會自動改試備援)
- `analyze.cum_yoy_strong` — 累計 YoY 優選門檻 (預設 10%)
- `analyze.mean_yoy_strong` — 近期平均 YoY 品質門檻 (預設 15%)
- `analyze.yoy_std_high` — YoY 標準差高波動門檻 (預設 40)
- `cyclical_industries` — 要被分流排除的週期產業清單

---

## 5. 分級與型態說明

**分級 (tier)**
- **優選** — 累計 YoY ≥ 門檻、未連續下滑、連續 ≥3 月 YoY 為正
- **觀察** — 中性,或動能減速但仍強 (成長趨緩)
- **警戒** — 累計 YoY 轉負、由高轉低跌破門檻、或旺季不旺且 YoY 為負
- **排除(週期股)** — 原物料/週期股,改看價格/庫存/毛利率

**動能型態 (pattern)**:穩定成長型 / 成長趨緩型 / 季節性緩成長型 / 高波動訂單型 / 見頂衰退型 / 原物料週期型

**綜合動能分數 (0–100,僅非週期股)** — 透明加權,便於稽核:
Layer1 累計YoY 45% + Layer2 多月趨勢 35% + Layer3 季節/加速 20%。

---

## 5b. 熱門族群動能層 (VIA 族群 × 實證營收)

引擎內建 `twrevenue/groups.csv` — 由 VIA 族群分類 v1.1 抽取的 **31 個熱門族群、149 檔**,
每檔標註族群、角色 (L 龍頭 / P 第二梯隊 / G 落後)、市場。

**分工**:VIA 檔提供「族群骨架 + 龍頭角色」(策展層);本引擎用 MOPS **真實月營收** 回填每個族群的
實證動能 — **不採用** VIA 檔內的 hot/lead/chg (那些是合成佔位、待其 VDF 引擎回填)。

`analyze` 會另外產出 `data/group_analysis.csv`,並在儀表板頂部加入「熱門族群動能矩陣」。
每個族群一列 (加總表現),**點擊可展開看族群內個別成員表現**:

**族群加總表現 (summary 列)**
- **加總累計YoY / 加總YoY** — 族群營收加權 (Σ本期營收 / Σ去年同期 − 1),反映族群真實體量,
  比中位數更能代表龍頭權重 (例:半導體中位YoY可能為負,但台積電體量大 → 加總YoY為正)
- **族群分數** — 成員動能分數中位數
- **廣度 (breadth)** — 族群內 YoY 為正的成員比例
- **優選/涵蓋** — 族群內優選檔數 / 有資料檔數
- **龍頭確認** — 龍頭營收動能是否 ≥ 族群中位;**✘ 背離** 代表龍頭營收沒跟上,值得警覺
- **動能判定** — 族群加速 / 分歧中性 / 族群轉弱 (以加總累計YoY為錨)

**個別表現 (展開後)**
- 族群內每一檔:角色 (龍頭/第二梯隊/落後)、動能分數、累計YoY、單月YoY、MoM、季節訊號、分級

> 股票代號規則:四碼數字、第一碼不可為零 (`^[1-9][0-9]{3}$`),自動排除 00xx ETF、
> 6 碼 TDR/權證等無月營收標的。可於 `config.fetch.stock_id_regex` 調整。

**週期分流 · 全市場六大類 (TWSE+TPEX 全覆蓋)**:
`水泥 / 鋼鐵 / 石化 / 化工 / 貨櫃航運 / 散裝航運` (+ 航運其他、其他週期)。
歸類方式:fetcher 直接解析 MOPS 頁面的「產業別」標題,**每家公司自動帶產業別**,
再依對映表歸入週期類 — 全市場零遺漏、免手工維護名單:

| MOPS 產業別 | 週期類 |
|---|---|
| 水泥工業 | 水泥 |
| 鋼鐵工業 | 鋼鐵 |
| 塑膠工業、油電燃氣業 | 石化 |
| 化學工業 | 化工 |
| 航運業 (貨櫃代號清單) | 貨櫃航運 |
| 航運業 (散裝代號清單) | 散裝航運 |
| 航運業 (其餘: 港埠/物流/貨代) | 航運其他 |
| 橡膠、造紙、玻璃陶瓷 | 其他週期 |

航空 (2610/2618/2646) 豁免於週期分流,照 VIA 航空族群以動能對待。
週期類公司一律排除於月營收排名,改看價格/庫存/毛利率
(它們的營收 YoY 常出現 +147%、−62% 這種因價格與基期造成的假訊號)。
`金融` 標為非典型月營收 (僅提示)。輸出於 `data/cyclical_sectors.csv` 與儀表板週期區 (可展開個別成員)。

> 更新族群:直接編輯 `twrevenue/groups.csv` (欄位 stock_id, name, group, role, market) 即可,
> 新增/刪除族群或成員都會自動反映到分析與儀表板。

---

## 6. 資料來源與欄位

MOPS 月營收頁面:
```
https://mops.twse.com.tw/nas/t21/{market}/t21sc03_{民國年}_{月}_{i}.html
  market : sii=上市(TWSE), otc=上櫃(TPEX)
  民國年 : 西元 - 1911
  i      : 0=國內公司, 1=國外KY公司  (每月抓 4 個組合才完整)
  編碼   : Big5
```
每月營收於**次月 10 號前後**公布,故「最新可抓月份」= 上個月。

---

## 7. 每月工作機制 (Day 1–10)

- **Day 1–3** 抓取更新月營收,維護 36 個月矩陣
- **Day 4–6** Layer1 濾網:累計 YoY ≥ 10% 且未連續下滑,標記加速/減速
- **Day 7–8** Layer2:連續 ≥3 月 YoY 正、平均 YoY ≥ 15%、低波動
- **Day 9** Layer3 + 產業/型態分群,週期股分流
- **Day 10** 產出當月結論 + 規則檢討 (是否過度依賴單月?是否忽略基期?是否營收成長但獲利惡化?)

---

## 8. 已知限制 / 後續可增強

- **月營收僅反映營收面**,不含毛利率/ROE。建議候選池再疊加獲利指標 (可另接財報 API)。
- 週期股的價格/庫存/產能利用率資料**不在 MOPS 月營收內**,需另接資料源 (期交所、產業報告)。
- 產業別 (industry) 依 MOPS 頁面群組標題擷取;若某月頁面結構特殊導致缺漏,可在 `config.cyclical_industries`
  或另建 stock_id→industry 對照表補強。
- 若 MOPS 再次遷移網域,請更新 `config.fetch.base_hosts`。

> 本工具為量化篩選輔助,非投資建議。
