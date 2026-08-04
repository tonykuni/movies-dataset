# DRAFT · TickerRegex SSOT 過渡裁決書 v0100

**狀態:草案(review_before_apply,未生效)** · 2026-08-04

## 1. 爭點

| | 舊規則(v029SSOT1B 系) | 新規則(VIS_VRN_TickerFilenameSSOT_v0100) |
|---|---|---|
| Regex | `(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})` | `(?<!\d)([1-9]\d{3})(?!\d)` + 年份消歧層 |
| 2021–2030 帶 | 一律排除(regex 內建) | 保留為候選,由消歧層裁決 |
| 已證缺陷 | 誤殺 10 檔真實股號:2021 中鋼構、2022 聚亨、2023 燁輝、2024 志聯、2025 千興、2027 大成鋼、2028 威致、2029 盛餘、2030 彰源、2026(保留) | 消歧依據:首頁資訊區股號比對(0.97)、官方清單(0.9)、日期線索 年/Q/FY/季(0.9→YEAR)、無佐證→AMBIGUOUS 人工覆核 |

## 2. 影響面(2026-08-04 全庫掃描,排除 _superseded 與新模組本身)

**69 個檔案**仍含舊排除式,分佈:

- **SSOT 正本(最高優先)**:`ssot/VRN_TickerRegexSSOT_v029SSOT1B.json`、`ssot/vrn_unified_ssot_builder_v029ssot1b.py`、`VIA_SSOT_Unified.py` ×4 份(root/20_Registry_SSOT/ssot/Standalone bundle)、`VIA_Parameters_SSOT.json`、`VIA_FinalParameters_CanonicalRegistry.json`
- **VRN 生產線 v1.1.0**:MDL001 Converter/Pipeline、MDL002–008、HealthCheck、d8b filename parser(共 12 檔)
- **VDF 引擎**:MDL001_TWUniverse_Verify、VIA_TW_Universe_Builder、MDL002_YFinance、MDL103/201 registry 產生器、MDL402/403/404 registry JSON
- **支援層**:VeritasAegisNexus ×4、VeritasCeleritas ×4、TWOfficialYFinance ×2、NewReportCompatibilityGate ×2、audit_tools 治理紀錄群

## 3. 過渡提案(分階段,不做全庫突變)

- **P0(立即,已完成)**:新模組 `VIS_VRN_TickerFilenameSSOT_v0100.py` 入庫為 append-only 新真相;本裁決書入庫為爭點記錄。
- **P1(核准後)**:發行 `VRN_TickerRegexSSOT_v0100.json`(新版 SSOT JSON,含新 regex + KNOWN_REAL_TICKERS_IN_BAND + 消歧規則),與 v029SSOT1B **並存**;SSOT 指針改指 v0100,舊檔封存不刪除。
- **P2(逐檔,執行期墊片優先)**:執行入口以 runtime 墊片(in-memory patch,同 Tower RelatedPath 手法)將舊 regex 常數替換為新模組匯入;正本檔案不動,待各模組自然升版時才落地改寫。
- **P3(觀察)**:audit_tools 內的歷史治理紀錄 JSON **永不改寫**(它們是當時狀態的證據)。
- **檢核閘**:任何 P1/P2 動作各自獨立 hash-locked 交易 + 操作員核准;2021–2030 帶內股號在消歧層回報 AMBIGUOUS 時一律進人工覆核,不自動判 YEAR。

## 4. 待操作員核准事項

- [ ] 核准 P1:發行 v0100 SSOT JSON 並轉指針
- [ ] 核准 P2:對現役執行入口(Invoke-VRN 系)加 runtime 墊片
