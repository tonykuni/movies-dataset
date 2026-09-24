# VCGC 支援工具擷取（2026-09-24）

來源：`tonykuni/movies-dataset`，main commit `eebaab0a06ecc18c69249a56dbc11c617c6dc84f`。
範圍是中央治理入口及其直接使用的現役 Python 支援家族，共 22 支；同一家族只取數字版號最高者。各檔路徑、原始 Git blob SHA-1 和大小見同目錄的 `VCGC_support_tools_manifest_20260924.json`。

| 類別 | 家族 |
|---|---|
| 中央入口與兩個埠 | `CGC_MDL149`, `CGC_MDL178`（工具盤點、棘輪、撞號）, `CGC_MDL179`（端點對帳） |
| 治理與驗證 | `CGC_MDL064/095/115/123/137/141/144/148/158/164/169/176/177/185` |
| 共用支援 | `SUP_MDL737/749/750/751/752` |

`CGC_MDL149.tool_inventory()` 委派 `CGC_MDL178.inventory()/ratchet()/version_race()/shuttles()`，`sync_hub()` 委派 `CGC_MDL179.collect()`；本擷取只複製正本，不另實作盤點或同步判準。`CGC_MDL179` 對雲端同步夾做唯讀對帳，API 端點目前標記 GATED，不具備雲端憑證交換。這是供審查的來源快照，不包含元件 SSOT、資料庫、金鑰或完整執行環境，因此不應直接當可執行套件部署。

在完整本機倉庫執行（預設只列檔，不寫入）：

```powershell
$VIA = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset'; & py -3 (Join-Path $VIA 'scripts\extract_vcgc_support.py') --root $VIA --json
```

確認後可加 `--zip C:\Users\tonyk\Downloads\VCGC_support_tools.zip` 建立來源快照。ZIP 含逐檔 SHA-256 清單；缺任一家族、遇到越界符號連結或輸出檔已存在時會拒絕，寫入中途異常不保留半成品。這項功能沒有登入、連網、安裝套件或修改同意閘。
