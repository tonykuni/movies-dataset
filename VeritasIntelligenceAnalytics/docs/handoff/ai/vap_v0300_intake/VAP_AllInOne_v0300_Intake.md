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
