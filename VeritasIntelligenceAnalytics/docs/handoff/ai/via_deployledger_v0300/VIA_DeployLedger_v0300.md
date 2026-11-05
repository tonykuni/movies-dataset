# VIA DeployLedger v0300(商業部署開發包 · 只測 · 未啟用)

操作員 2026-11-04 上傳 `VIA_DeployLedger_v0300_Developer_Upgrade.zip`(112 KB · 原包含桌機路徑與桌機狀態紀錄 → **不進倉** · 只寫結論與筆數)。依它自己的 README:**管理端開發包,含原始碼,不是客戶可交付的產品**;Windows 原生編譯、DPAPI、PowerShell 執行、真實 VCGC 接合都還沒實測。

| 項目 | 結果(容器 · 離線)|
|---|---|
| `tests/test_deployledger.py` | 48 項 · 過 47 · 錯 1:`environment_probe` 在本容器系統 Python 偵測到重複套件(cryptography ×3 · pyjwt ×2 · packaging ×2 · six ×2)→ 照設計 fail-closed(是環境事實,不是程式錯)|
| `legacy/VIA_HybridEdgeCloud_AllInOne_v0200.py selftest --rounds 3` | 相容核心 2.2.1 · 3 輪 ok |
| 網路 | 程式不匯入網路模組;用 subprocess(編譯 / 執行子程式)|

**沒有啟用、沒有拆進現役樹**:原包(含 `.ps1` / `.cmd` 與桌機路徑)不進倉;授權私鑰、Ed25519 簽發、Nuitka 編譯是商業出貨流程,要操作員決定何時做、在哪台 Windows 做。
