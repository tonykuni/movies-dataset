# VRN-2 v0163 驗證紀錄(2026-10-31 · 不用 MOPS · 套件 v0163 · RoundAll v0119 · Handle-All v0111)

## 1. 起因

操作員 2026-10-31:「**不可用 MOPS · 全部國內使用 TWSE TPEX**」。桌機 16:11 那輪 ⑤ 重抓 ⑥e 經借用的 VDF 引擎逐檔打 MOPS 財報
(引擎 `def_collect_financial` 讀 `mopsov.twse.com.tw/mops/web/ajax_t164sb…` · `latest` 只用 TWSE / TPEX 開放資料決定季別),
⑬b 歷史對齊與增量庫的 FinancialAligned 因此用了 MOPS 歷史。

## 2. 修法(共用 MarketFetch 與 VDF 引擎只讀不改 · 只改 VRN-2 傳的參數與 VRN-2 自己的輸出夾)

| 檔 | 內容 |
|---|---|
| 啟動器 v0163(`b3c4a0a75fad`)| ⑥e `MarketFetch --fetch` 一律 `--no-financial`(MarketFetch 原本就有這個開關)· ⑥e 前把已落盤的 MOPS 財報(`market/vdf/parquet/tw_financial` · `tw_financial.parquet`)移到 `market/vdf/_mops_quarantine_<時間>`(不刪 · 同一秒第二次加序號)· 步驟名「… · 不用 MOPS」· 收據 v0163 |
| 套件 v0163(`fd216929c5f1`)| 啟動器 v0163 + 其他成員跟 v0158 逐位元組相同 · runtime v0156 原樣 |
| RoundAll v0119(`0960759c8c24`)| 釘套件 v0163 · ④ 跑啟動器前先移 MOPS 財報 · ⑤ 有 MOPS 財報 → 移開 → 重抓價格(`--no-financial`)+ 重新填值 → ⑬b → Combined → 增量庫 → Workbench · ⑤ 重抓一律 `--no-financial` · 自測 74 |
| Handle-All v0111(一行 `62ce977ea539` · 開機檔 `1772092eda9a`)| 指向 RoundAll v0119 · 最短一行 443 字元 · cmd 一行 1240 字元 |

國內資料來源:價格 / 指數 / 代號清單 / 月營收 = TWSE / TPEX 官方(openapi.twse.com.tw · tpex.org.tw)· 財報不抓(TWSE / TPEX 開放資料只有最新一季 · 沒有多年財報 → ⑬b 灰「無歷史」)。

## 3. 測試

```text
[PASS] 73 不用 MOPS:已落盤的 MOPS 財報(tw_financial)→ ⑤ 先移到 _mops_quarantine(不刪 · 同一秒第二次加序號)再重抓價格 + 重新填值 · 沒有擷取 Python 也照移 · 移完就不再排 · 價格資料不動
[PASS] 74 ⑤ 重抓 ⑥e 的 --fetch 帶 --no-financial(--fill 不帶)· ④ 跑啟動器前先移 MOPS 財報 · 套件 / 啟動器 v0163(--no-financial 也在啟動器裡)
[PASS] VRN2_RoundAll v0119 --selftest · 74 項 · 不過 0
venv(有 PyMuPDF):[PASS] VRN2_RoundAll v0119 --selftest · 76 項 · 不過 0
啟動器 v0163 自測(從套件 zip 解開 · venv):
[PASS] v0163: step 6e never asks for MOPS · MarketFetch --fetch gets --no-financial (--fill unchanged) · MOPS financial data already on disk moved to market/vdf/_mops_qua
pwsh 7.4.6 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True
e2e:repair rc 0 · full rc 0 · tamper rc 0 · receipt ActivateVRN-2 v0163 · ⑥e 市場擷取(TWSE / TPEX / Yahoo · 借共用 MarketFetch · 不用 MOPS) · VRN2_MarketFetch_v0112.py · Python 沒有合 VDF 界線的(填值用 via_tw_fetch) · 不用 MOPS(--no-financial) · 擷取 YELLOW:沒有合 VDF 引擎版本界線的擷取 Python(--python via_tw_fetch(3.13.16):p · market {'no_mops': True, 'mops_quarantine': ''}
```

VCGC 全景骨架卡:RoundAll v0119 SWALLOW 10 項(同 v0118)· 啟動器 v0163 4 項(同 v0158)。

## 4. e2e(桌機 v0153 狀態沙盒 · 放假的 MOPS 財報 · 沙盒 GitHub 分支 · pwsh 7.4.6)

```text
[repair] [GREEN] boot: Handle-All v0111 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[repair] [計] ④ 模式 repair:取套件 v0163 → ⑤ 自動修(同意閘開:⑥f 共識改經 VIA 網路工具重抓 · ConsensusJoin v0104 + 引擎 v0122 · ⑥e 不用 MOPS(MOPS 財報移開 · 只用 TWSE / TPEX)· 擷取鎖過期 → 移開後重抓 ⑥e · 重組 Combined · 增量庫 · Workbench;閘關:現有共識不
[repair] [計] ⑤ 自動修計畫:MOPS 財報(操作員 2026-10-31:不可用 MOPS)移到 market\vdf\_mops_quarantine(不刪) · 市場資料比歷史對齊新 / 歷史對齊沒跑 → 重跑 ⑬b · Combined 比市場 / 共識舊(或不在)→ 重組 · ⑬ 增量庫補寫(本輪有修正) · Workbench 重渲染(最新收據)
[repair] [進度] 3/19 ⑤ 自動修 1/5 · MOPS 財報(操作員 2026-10-31:不可用 MOPS)移到 market\vdf\_mop
[repair] [GREEN] ⑤ 修 · MOPS 財報(操作員 2026-10-31:不可用 MOPS)移到 market\vdf\_mops_quaranti · MOPS 財報移到 market\vdf\_mops_quarantine_20261031_105646(不刪)
[repair] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 3 項等 VCGC 決定 / 安裝
[repair]   [VCGC] 3 項
[repair]   [人工] 2 項
[full] [GREEN] boot: Handle-All v0111 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[full] [GREEN] ④ 不用 MOPS · 已落盤的 MOPS 財報移到 market\vdf\_mops_quarantine_20261031_105719(不刪 · ⑬b 不再用它)
[full]   [計] ⑥e 市場擷取 · YELLOW · VRN2_MarketFetch_v0112.py · Python 沒有合 VDF 界線的(填值用 via_tw_fetch) · 不用 MOPS(--no-financial) · 擷取 YELLOW:沒有合 VDF 引擎版本界線的擷取 Python(--python via_tw_fetch(3.13.16):pandas
[full] [YELLOW] ⑥ 步驟 ⑥e 市場擷取(TWSE / TPEX / Yahoo · 借共用 Market · VRN2_MarketFetch_v0112.py · Python 沒有合 VDF 界線的(填值用 via_tw_fetch) · 不用 MOPS(--no-financial) · 擷取 YELLOW:沒有合 VDF 引擎版本界線的擷取 Python(--pyt
[full] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 7 項等 VCGC 決定 / 安裝
[full]   [VCGC] 7 項
[full]     · ⑥ 步驟 ⑥e 市場擷取(TWSE / TPEX / Yahoo · 借共用 Market · VRN2_MarketFetch_v0112.py · Python 沒有合 VDF 界線的(填值用 via_tw_fetch) · 不用 MOPS(--no-financial) · 擷取 YELLOW:沒有合 VDF 引擎版本界線的擷取 Python(--python
[full]   [人工] 1 項
[tamper] [RED] boot SHA-256 mismatch - not run
```

輸出夾事後:repair → ./_mops_quarantine_20261031_105646, ./_mops_quarantine_20261031_105646/parquet, ./_mops_quarantine_20261031_105646/tw_financial.parquet · full → ./_mops_quarantine_20261031_105646, ./_mops_quarantine_20261031_105646/parquet, ./_mops_quarantine_20261031_105646/tw_financial.parquet, ./_mops_quarantine_20261031_105719, ./_mops_quarantine_20261031_105719/parquet, ./_mops_quarantine_20261031_105719/tw_financial.parquet

**沒跑到的**:桌機上用 `--no-financial` 真的重抓價格(容器沒有合 VDF 界線的 Python)· 桌機上的 MOPS 財報(下一輪 repair 的 ⑤ 會移開)。

## 5. 還在用的非 TWSE / TPEX 來源(已問操作員)

- **Yahoo 還原價**:VDF 引擎日線的還原因子(yfinance · 引擎設定註明是「user-authorized」例外 · 引擎沒有關掉的開關 · VDF 的事)→ Combined 的 TARGET_PRICE(ADJ) 靠它。
- **YFinance 共識中位數**(⑥f · VRN-2 自己的)· **鉅亨 FactSet 共識**(⑥f)—— 這兩個是分析師共識,不是交易所資料。

## 6. 增量庫

OneDrive\VRN2_out 的增量庫在 16:11 那輪已追加 FinancialAligned 4584 列 / Deleted 38 列(用了 MOPS 歷史)· 增量庫只增不刪 · 沒動 · 要不要清由操作員決定。
