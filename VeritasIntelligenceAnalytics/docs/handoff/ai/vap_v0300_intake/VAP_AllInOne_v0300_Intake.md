# 操作員上傳 · VeritasAutoPlot v0300 All-In-One(2026-11-06)· 入倉紀錄

byte-exact 進 zip(`VAP_AllInOne_v0300_upload_20261106.zip` · SHA 在 `SHA256.txt`)。**只到兩檔**:

| 檔 | 大小 | 說明(照 README)|
|---|---|---|
| `VAP_AllInOne_README_v0300.md` | 1,631 B | Python 函式 70 · JS 62 · Workbench 函式 459 · Active 圖形能力 40 + 5 · 啟動 `python VAP_AllInOne_v0300.py --run-self-test` |
| `VAP_AllInOne_UI_v0300.html` | 4,791,158 B | 自包含 Workbench(title 仍寫 v027 · 內容標 v0300 · 內嵌 5 個 JS 引擎)|

**沒上傳**:`VAP_AllInOne_v0300.py`(引擎本體)· `VAP_Function_Inventory_v0300.json`。沒有 .py 就**不能實測啟動**(README 的 `--run-self-test` / `127.0.0.1:8765` 都要它),
所以 ⑫ 系統矩陣 VAP 列仍 ⚪「桌機 VAP_AllInOne 未上傳」。README 自述治理邊界(VDF/VRN → VQG → VAP 單向 · SQLite / DuckDB 唯讀 · loopback)與五系統對等政策一致。

下一步(操作員):上傳 `VAP_AllInOne_v0300.py` + `VAP_Function_Inventory_v0300.json`(或整包 zip)→ 容器隔離 `python -I … --run-self-test` → 入 ⑫ / ⑭(VAP 夾尾版 · 自測燈)。
注意它與上傳的 VIA_SystemIntegrationEngine **都預設綁 127.0.0.1:8765**,桌機不要同時開兩個(改 `--port`)。

## 2026-11-06 第二批:整包到了 → 入倉 `functional modules/VAP/intake/allinone_v0300/`(byte-exact 4 檔 + SHA256.txt;夾內 .gitignore 擋 state / logs / output)

| 實測(容器 · 隔離 · `python -I`)| 結果 |
|---|---|
| `--run-self-test` | **PASS**(16 項:loopback · formalInputAuthority · vdfManifest · vqgManifest · vdfFingerprints · demoRefresh · uiExists …)· 缺選用套件 duckdb / talib(它自己誠實列)|
| `--no-browser --port 8766` 啟動 | `SYNC CONNECT ready · 1 tables · 0 errors` · 7 條 API 全 200:/api/health(READY · readOnly true · VQG_ONLY)· catalog · functions(591 函式清冊)· spec · templates · images · context |
| Chromium 載入 Workbench | 632 個按鈕 · 12 頁(平台總覽 → 系統驗證)· **JS 錯誤 2:`fallback is not a function`**(UI 第 2078 行 `loadStore(key,fallback)` 在 `return fallback()`,但有呼叫端把非函式當 fallback 傳進來;預設 8765 埠也一樣)→ VAP(Manus)自己的 bug,原件不改 |
| 全景卡(MDL158)| 1,345 行 · 標準庫 · **DUPDEF 4**:`def_load_config`(L668 / L1252)· `def_load_vdf_manifest` · `def_load_vqg_manifest` · `def_run_self_test`(後面的蓋前面的;Python 合法)· SWALLOW 1(L140)|
| 副作用 | 引擎把 `state/ logs/ output/` 寫在**自己的夾**(不是 VIA_Reports)→ 入倉夾加 .gitignore;UI `<title>` 仍寫 v027 |

VCGC 登錄:SettleAll v0113 **⑮ VAP** 每輪跑它的自測(容器 🟢)· ⑭ 模組矩陣列 · 編號 / 盤點冊站 `E-vap-allinone` 見本輪提交。
