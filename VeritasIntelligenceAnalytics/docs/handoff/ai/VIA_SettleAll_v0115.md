# VIA_SettleAll v0115(2026-11-06 · VQG→VAP 匯出 / 串接 · 衝突偵測)

v0114 一字不動。操作員令:「VQG 擷取自資料庫檔案夾整理全部 · 統一輸出資料到其他應用如 VAP · 確認各系統完全獨立交互支援 · VCGC 協助大家偵測顯示衝突 · 協助導入環境與工具無衝突」。

## 新增步驟

| 步 | 做什麼 | 燈 |
|---|---|---|
| ⑧b VQG→VAP 匯出 | ⑧ closeout 綠 / 黃且 VDF 家在 → VQG v0106 `export-vap --max-tickers 3 --indicator-points 20`(VDF 庫夾整理全部 · 一票一表 SERIES / INDICATOR_RESULT · 連線證據指紋 · VAP config);子行程不帶 `VQG_VDF_ROOT`(`--root` 已明給;v0105 自測 ⑩ 會被它誤判) | = `VIA_Reports/vqg/VQG_ExportVAP_latest.json` 的燈;沒 VDF 庫 ⚪ |
| ⑰ VQG→VAP 串接 | 拿 ⑧b 的 config 跑 VAP 尾版 `--once-refresh`(python -I · loopback · 不開瀏覽器) | 表數 = 來源數且 0 錯且全 vqgVerified 🟢 · 有表有錯 🟡 · 其他 🔴 · 沒匯出 ⚪ |
| ⑯ 衝突偵測 | 只讀 AST / 檔名 / SHA · 不執行 · 不改檔 · 只攤開不代修:跨系統 import(共用 SUP_/VIA_* 不算)· 同名不同內容(含同家族同版號撞號)· 撞埠(兩系統以上寫死同一 127.0.0.1 埠)· 工具鎖(`VIA_ToolVersion_Lock` 指到的檔不在 / 有更新尾版沒啟用)· 鏡像夾(SCOPE_COPY)→ `VIA_Reports/settle/VIA_Conflicts_latest.json / .md` | 🔴 同家族同版號 .py / .ps1 兩邊都在活夾 · 🟡 其他任一有 · 🟢 都沒有 |
| ⑫ 矩陣 | 加「VQG→VAP 匯出 ⑧b」「VQG→VAP 串接 ⑰」「衝突偵測 ⑯」三列;⑩ 報告加兩段;貼回包多 `VQG_ExportVAP_latest.json` · `VIA_Conflicts_latest.*` | — |

其他:`PINNED` 加 VQG v0106(SHA e3fb9d7d…)· `_env()` 支援值 None = 子行程不帶該變數 · 自測 45 項(+㉝ 衝突偵測迷你樹 · +㉞ 串接判燈 / JSON 尾段 / env 拿掉)。

## 容器實測(2026-11-06 · VDF 形狀夾具 · `--only scan,vqg,vap,link,conflicts,matrix,report`)

⑮ VAP v0302 PASS 16 項 · ⑧ VQG closeout YELLOW(曆推的)· ⑧b 匯出 YELLOW(4 來源 · 4 表閘過)· ⑰ 串接 🟢(4 / 4 · 0 錯 · 全 vqgVerified)· ⑯ 🟡(跨系統 import 14 · 撞號 3 活夾 0 · 撞埠 2:8765 = VCGC / VDF / VQG / VRN-2 + VAP U/I 寫死;8080 = VAP / VCGC · 工具鎖舊 1 = NLP v0108 沒啟用 · 鏡像夾 1 = `functional modules/VAP/ASSETS/SCOPE_COPY/` 5075 檔)· 整輪 YELLOW rc 2。

## 桌機(PowerShell 7.6.9)

見 `VRN2_Handover_latest.md` §29 一行(SHA 核過才跑)。真 VDF 庫在時 ⑧b 會匯到 `VIA_Reports\vqg\vap_export\`,VAP 啟動:`python <VAP 尾版> --config "<VIA 根>\VIA_Reports\vqg\vap_export\VAP_AllInOne_v0300.config.json"`。
