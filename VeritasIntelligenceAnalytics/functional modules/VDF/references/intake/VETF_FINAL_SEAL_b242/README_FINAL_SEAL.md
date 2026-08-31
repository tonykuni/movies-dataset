# VETF FINAL SEAL · VIA Taiwan Active ETF Consensus

封裝日期：2026/08/29（Asia/Taipei）

## 封裝內容

- `01_ENGINES/Consensus_Enrichment_Adapter/`：主動式 ETF 持股 × Consensus 擴充 Adapter、README、SSOT、測試。
- `01_ENGINES/Legacy_Consensus_Engines/`：既有 CNYES／FactSet／YFinance Fusion 與 Matrix 引擎。
- `02_WEB_UI/React_Site_Source/`：已發布 React／Vinext 網站完整可維護原始碼。
- `02_WEB_UI/Standalone_Current/`：最新版分離式 HTML／CSS／JavaScript 與單檔 Standalone HTML。
- `02_WEB_UI/Standalone_Legacy/`：早期大型 Standalone 成品，保留相容與追溯用途。
- `03_CONTRACTS/`：Consensus Enrichment SSOT 資料契約。
- `04_TESTS/`：測試程式與既有測試報告。
- `90_PRIOR_PACKAGES/`：前一階段 Adapter ZIP 與 UI ZIP，不覆寫、不遺漏。
- `MANIFEST.json`：全部有效載荷檔案的大小與 SHA-256。
- `SHA256SUMS.txt`：有效載荷與 manifest 的 SHA-256 清單。

## 核心計算

- FactSet 與 YFinance 目標價 Low／Mean／Median／High 分開保存，不直接平均。
- `Forward P/E N = 最新可用 Adj Close ÷ FactSet EPS N`。
- 同理計算 N+1、N+2；EPS 缺失、零或負值採 fail-closed，不輸出誤導性倍數。
- ETF 投組估值使用持股權重加權 earnings yield，再取倒數。
- 實體辨識採 ticker／ISIN／名稱等雙重身分證據。

## 啟動方式

1. 直接開啟：`02_WEB_UI/Standalone_Current/VIA_Taiwan_Active_ETF_Consensus_Standalone.html`。
2. React 開發：進入 `02_WEB_UI/React_Site_Source`，依序執行 `npm ci`、`npm run dev`。
3. Adapter：參閱 `01_ENGINES/Consensus_Enrichment_Adapter/README_VETF_ConsensusEnrichment_v001.md`。

## 治理與排除項

- 預設維持 `CANDIDATE LOCKED`；未取得 P0/P1 核准前不寫入 canonical。
- 已排除可重建內容：`node_modules`、`.sites-runtime`、`.wrangler`、`.vinext`、Python bytecode 與部署身分設定。
- 排除項不是功能原始碼，也不影響離線 Standalone 或重新安裝 React 相依套件。

正式網站：https://via-active-etf-consensus.tonyhuang0122.chatgpt.site

