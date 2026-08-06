# VIA｜攝入分類 Schema：讓後續比較有意義 v001

Generated: 2026-07-05 · 攝入層(ingestion) 分類規格 · 承接證據等級(V/M/P/Est/Syn) 與計分標準化(R1–R9)
核心命題：**兩個數字能不能比，不看它們長得像不像，看它們的「型別・口徑・單位・季調・頻率」是否一致。分類軸選對，比較才有意義。**

---

## 0. 三個你點到的痛點 → 對策
1. **從圖表/graph 摳數字常出錯**（OCR/vision 不可靠）→ 來源型態分級，**GRAPH_OCR 一律標低信度、不得單獨計分**，須與結構化源交叉。
2. **Evernote 連結 URL 跑得進去** → 用 Evernote 當**原始擷取 inbox**（URL 可 fetch），先落地再解析分類。
3. **如何分類才好比** → 下面的**分類軸 + 可比性規則 + 統一正規化層**。

---

## 1. 來源型態路由（先分「怎麼來的」，決定可信度）

| source_form | 可信度 | 處理 |
|---|---|---|
| `API` / `TABLE`（CSV/XLSX/官方數列）| 高 | 直接解析入庫 |
| `TEXT`（md/txt/新聞正文）| 中 | 依 schema 抽取，保留原句供稽核 |
| `EVERNOTE`（筆記/剪報/URL）| 中 | 當 raw-capture inbox；fetch URL→解析→轉結構化 |
| `GRAPH_OCR`（圖表/截圖摳出）| **低** | **標低信度、必須與結構化源交叉；禁止單獨計分** |

**優先序：API/TABLE > TEXT/EVERNOTE > GRAPH_OCR。** 同一數字若同時有結構化與圖表來源，永遠採結構化，圖表僅作對帳。

---

## 2. 分類軸（決定可比性的欄位——這是重點）

每筆資料入庫時，一律打上這 11 個軸；**只有軸一致的兩筆才可直接比**。

| # | 軸 | 值域範例 | 為何影響可比性 |
|---|---|---|---|
| 1 | entity | 指標/股票/族群 id | 比誰跟誰 |
| 2 | region | US / TW / KR / EU… | 跨區不可混 |
| 3 | **data_type** | LEVEL / RATE_PCT / YOY / MOM / QOQ / INDEX / **DIFFUSION** / RATIO / SHARE_PCT / ZSCORE | **最關鍵**：年增率≠擴散指數≠絕對水位 |
| 4 | unit | %、點、千人、億元、倍、口、週 | 單位不同不能比 |
| 5 | seasonal_adj | SA / NSA | 季調與否不可混 |
| 6 | scope（口徑）| official/non-official、nominal/real、headline/core、first-print/revised | 口徑不同=不同東西 |
| 7 | freq | D / W / M / Q | 頻率要對齊才可比 |
| 8 | as_of | 抓取/報告基準日 | 版本對齊 |
| 9 | reference_period | 資料所屬期間 | 時間對齊 |
| 10 | evidence_status | V / M / P / Est / Syn | 品質分層 |
| 11 | provenance | url / file / evernote_note_id | 稽核 |

---

## 3. 可比性規則（什麼跟什麼才能比）

**硬規則：兩筆可「直接比」的充要條件 = data_type 同 ＋ unit 同 ＋ seasonal_adj 同 ＋ scope 同 ＋ freq 對齊。**

違反任一條就**不能直接比**，必須先轉換：
- 不同 data_type（如 CPI 的 YOY vs ISM 的 DIFFUSION vs 非農的 LEVEL）→ **先各自轉成統一基準**再比（見 §4）。
- nominal vs real、SA vs NSA、official vs non-official → **同軸才比**，跨軸只能做「背離分析」（差異本身是訊號，不是可比值）。
- first-print vs revised → 版本要標，別把首報跟終值當同一數列。
- 日 vs 月 → 對齊到共同頻率（升頻用期末/累積，降頻用彙總）。

---

## 4. 統一正規化層（跨異質指標比較的唯一正解）

要把「CPI 4.2%」「PMI 53.3」「非農 +57k」放在同一張圖比強弱——**不能比原值，要先轉成無量綱**：

- 每個 data_type 各自 → **對 N 日/月窗的 z 分數或百分位**（穩健 z：中位/MAD）。
- 之後所有比較都在 z/百分位空間做（承 ScoringSpec 標準化）。
- 這樣 %、點、千人、倍… 全部落到同一把尺，才「有意義地可比」。
- **GRAPH_OCR 來源的值**：轉 z 前先過人工/交叉驗證閘；未過 → 不進正規化、不進比較。

**三種比較模式**（都在正規化後做）：
1. **時序比較**（同 entity 跨時間）→ 趨勢/動能 z。
2. **橫斷比較**（同 data_type 跨 entity）→ 相對強弱排名。
3. **背離比較**（official vs non-official、nominal vs real、機構 vs 家庭）→ 差異 z（差異本身=訊號）。

---

## 5. Evernote 原始擷取 inbox 模式

```
Evernote 筆記/剪報/URL（原始，可 fetch）
      │  capture 時打標：source, date, topic
      ▼
fetch URL / 讀筆記正文
      ▼
依 §2 分類軸 抽取 → 結構化 record
      ▼
落 warehouse（parquet），evernote_note_id 當 provenance
```
- Evernote 只當**原始層**（raw capture），不直接進比較；一定要先解析、打分類軸、標 evidence。
- URL 可 fetch 是優點（比圖表可靠）→ 但抓進來的若是「圖表頁」，仍歸 GRAPH_OCR 低信度。

---

## 6. 攝入 record 範例（JSON）
```json
{
  "entity": "US_CPI_headline",
  "region": "US",
  "data_type": "YOY",
  "unit": "%",
  "seasonal_adj": "NSA",
  "scope": "official/headline",
  "freq": "M",
  "as_of": "2026-06-11",
  "reference_period": "2026-05",
  "value": 4.2,
  "evidence_status": "V",
  "source_form": "TABLE",
  "provenance": "bls.gov/cpi"
}
```

---

## 7. 落地順序
1. 攝入器先判 `source_form`（API/TABLE/TEXT/EVERNOTE/GRAPH_OCR）→ 定可信度。
2. 依 §2 打 11 軸；缺軸→標 Pending，不硬填。
3. GRAPH_OCR → 進「待驗證」暫存，交叉過才放行。
4. 入庫後，比較一律走 §4 正規化層（z/百分位），禁止原值跨型別比。
5. 全程 append-only、provenance 必附、evidence 分層。

---

## 8. 一句話
**分類的軸選對（尤其 data_type / scope / seasonal_adj / unit），比較才有意義；圖表摳出的數字一律低信度要交叉；Evernote 當原始 inbox 先落地再分類；最後所有異質指標都轉 z/百分位，才放到同一張尺上比。**
