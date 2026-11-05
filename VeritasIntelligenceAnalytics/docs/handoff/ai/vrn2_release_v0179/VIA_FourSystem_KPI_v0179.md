# VIA 四系統收尾 KPI · v0179(2026-11-04)

操作員令:「結果驗證正確性及運作速度在 CPU/DRAM 架構下是否最快化為所有 VIA 系統收尾驗證 KPI」。
四系統對等獨立(VRN-1 · VRN-2 · VDF · VCGC;VRN-1 是另一團隊的倉,不在本倉、只讀 —— 本表不列它的數)。
**規則**:正確性「不符 0」才算達標;待人工照列(REVIEW 不是成功);速度只報實測(不推估);灰燈 = 指標,不改任何系統的結案判定。

## 1. VRN-2 · 桌機實跑(2026-11-04 01:53 · 套件 v0178 整輪 + repair · 8 核桌機)

正確性(只讀這輪已寫的驗證檔 · RoundAll v0135 ⑥ 收尾 KPI 同一支函式重算 = 貼回包內容):

| 項目 | 對上 / 全部 | 待人工 | 不符 |
|---|---|---|---|
| 獨立驗證 · 基本資料 | 708 / 711 | 3(OCR 影像頁 2 · 推算已標示 1)| 0 |
| 獨立驗證 · 一標題四重點 | 255 / 260 | 5(MQ-1560 影像頁)| 0 |
| 獨立驗證 · 年度數據 | 11971 / 11971 | 0 | 0 |
| 四點原文核對(第二讀取器) | 204 / 208 | 4(MQ-1560 OCR_PENDING)| 0 |
| **判定** | **達標(不符 0)** | 待人工 12(全在 MQ-1560 影像頁 + 1 個已標示推算)| — |

速度(CPU / DRAM):

| 指標 | 實測 |
|---|---|
| 收據耗時 | 2286.87 秒(2 輪)|
| 最慢步驟 | ⑦ 啟動 VRN-2 344 秒 · ⑪ 獨立驗證(背景 · 只讀) 289 秒 · ④ 加速器覆蓋 26 秒 |
| 有計時步驟合計 / 沒計時 | 779.0 秒 / ≥ 1507.9 秒(⑥e / ⑥f 擷取與共識 · 第 1 輪 · 這幾步沒印耗時)|
| 管理器(VRN-2 SystemManager v0259)| 326.5 秒 · 最慢「輸出冊」243.2 秒(占 74%)|
| CPU / DRAM(① 步實測)| 8 核 · 執行緒上限 7 · 可用 RAM 6.8 GB · 啟動時 CPU 忙 22.2% · 平行 3 路 |
| ④b 平行段 | 6 段 23.7 秒(依序要 54.3 秒 · 2.29 倍)|
| 加速器 / 網路工具 | ①b VeritasCeleritas_v1141(= 鎖冊 accelerator)· 網路 VeritasAegisNexus_v1652(= 鎖冊 network)· 都是最新 |

**是不是 CPU / DRAM 下最快?照實說:還不是。** 已做到:執行緒上限開到 核數 − 1、④b 平行 2.3 倍、加速器與網路工具是鎖冊最新版。
還沒做到:①「輸出冊」一個階段占管理器 74%(單一階段 · 下一輪優化目標)· ② 這輪跑了 2 輪(第 2 輪是 RoundAll 補修後重跑)·
③ ≥ 1508 秒沒有逐步計時(⑥e / ⑥f 主要是等外部網站)→ 先補計時才能判斷是 CPU 還是網路。

## 2. 各系統自己的檢查 · 本容器同一把尺(4 核 · 依序一支一支跑 · 不互相干擾)

| 系統 | 跑什麼 | 牆鐘秒 | CPU 秒 | 平均用核 / 可用 | 峰值 RSS MB |
|---|---|---|---|---|---|
| VRN-2 | RoundAll v0135 --selftest(111 項 · 多半在等逾時 / 心跳測試) | 10.9 | 0.6 | 0.06 / 4 | 66 |
| VRN-2 底座 | VRN_SystemManager v0261 --selftest(6 項 · 含 v0256 6 項) | 3.8 | 4.0 | 1.06 / 4 | 120 |
| VDF | 經 VCGC run VDF_SystemManager --selftest | 135.3 | 130.1 | 0.96 / 4 | 312 |
| VCGC | test --quick(10 站 · 沒變的 9 站沿用 · 平行 4) | 26.4 | 26.8 | 1.02 / 4 | 240 |
| VIA Agent OS | VIA_AgentOS_v0100 selftest(15 項) | 0.2 | 0.2 | 0.98 / 4 | 26 |

結果:VRN-2 `[PASS] VRN2_RoundAll v0135 --selftest · 111 項 · 不過 0` · 底座 `[計] VRN-2 SystemManager v0261(VRN_SystemManager_v0261.py)自測 6/6 · PASS · 鏈 v0261→v0256→v0254→v0253→v0249→v0248` · VDF rc 0 · VCGC `[VCGC 全功能串測] YELLOW · 站 10(綠 9 · 黃 1 · 紅 0 · 沿用 9)· 盤點 verb 46/46 · seat 6/6 · card 13/13 · case 230/230 · workflow 84/84 · ps 2/2 · 家族尾版 282 支 compil` · Agent OS `tests_run 15 · failures 0 · errors 0`。
**瓶頸照實列**:VDF 自測平均只用 0.96 核(依序執行 · 4 核只用 1 核)· Agent OS bootstrap 乾跑 1500 模組單執行緒 64 秒(v0178 量)· VRN-2 RoundAll 自測單執行緒。
這三處是「可平行但還沒平行」—— 屬各自系統的下一輪,不在本輪範圍內硬改(範圍不擴張)。

## 3. 四系統燈(各自自報 · 互相只讀)

| 系統 | 燈 | 說明 |
|---|---|---|
| VRN-2 | **REVIEW**(VRN-2 側結案)| 桌機收尾 VRN-2 0 · 人工 1(MQ-1560 影像頁 · 操作員 `--confirm`)· 資料源 3(外部來源本來沒有)|
| VDF | 自測 **綠**(rc 0)· 收尾收據 **灰**(沒有自報收據)| SUP_MDL753 v0113 修好 DuckDB 2.x;VDF 自己的收尾收據要桌機 ActivateVDF 真跑才有 |
| VCGC | 串測 **黃**(9 綠 1 黃 0 紅)· SSOT 全景 **黃**(前一刻紅)· 交接閘 **紅** | 交接閘紅 = 結構性(見 §4)· 不是這輪改壞 |
| VIA Agent OS | 自測 15 / 15 · Skill 23 / 23 | v0100 · 只讀 AST · `.via\ssot.json` 不進倉 |

## 4. 照實列的缺口(不寫成成功)

- VCGC 交接閘:{"REQ_CHANGED": 56, "CHECKPOINT_STALE": 1, "EVIDENCE_INVALID": 95, "CHANGED_CODE_WITHOUT_TEST": 204, "ACCEL_BRIDGE_MISSING": 2, "MODULE_UNREGISTERED": 1}。204 支「改了沒有宣告測試」是舊檔(VRN 101 · VDF 82 · VCGC 19 · 規則 2),要 VCGC 線替它們宣告測試案或豁免;
  93 個證據案要重跑(多數是 VDF 桌機 / 資料庫實跑);`manager` 案的標記只在 VRN_SystemManager v0110 印過 → v0231 起的 VRN-2 鏈一直對不上(2026-10-08 的證據就已經是「沒看到標記」)。checkpoint 沒打(閘紅不假裝成功)。
- 加速器覆蓋(AST 靜態):VRN-2 runtime 17 / 18(VerbatimVerifier v0105 · 桌機 ④ 自動注入 v0106)· VRN 共用 94 / 95(VRN_ENG112_FinancialRead_v0100)· VDF / VCGC / Agent OS 100%。已出貨的檔不改位元組 → 以新版號補(下一輪)。
- 網路:各橋都解到鎖冊最新(NetUnified v0119 → Aegis v1652);VDF MDL008 擷取系統在載入時 AST 改道到網路工具。**真缺口**:VRN-2 ⑥e 借用的 VDF AllInOne_v039(子行程 · yfinance / urllib)不經網路工具 —— 是 VDF 的引擎(VRN-2 只讀不改),記給 VDF 線。
- VDF MDL008 FetchSystem v0103 自測缺測資 `tw_fullmarket_snapshot.parquet`(環境資料 · 不是程式錯)。
