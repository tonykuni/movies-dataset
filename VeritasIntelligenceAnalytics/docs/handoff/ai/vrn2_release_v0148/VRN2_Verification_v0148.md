# VRN-2 v0148 + VRN2_RoundAll_v0101 容器實測紀錄(2026-10-29)

桌機 2026-10-29 14:40 第一次跑 VRN2_RoundAll_v0100 的貼回(52 份 · 2069 秒 · 紅 4 黃 10)→ 能在容器重現 / 驗證的修成 v0148(見發行清單 `fixes` · `not_fixed_here`)。

## 0. 桌機問題在容器重現 / 驗證

| 項目 | 結果 |
|---|---|
| UIAction v0109 · 殼有 VIA_ROOT(重現桌機 ③ 紅) | [FAIL] ④ vrn2://integrate?dismiss=1 → DISMISSED · ui_actions.log 有紀錄 · 沒有 root 時說下一輪重渲染 / [FAIL] VRN2_UIAction v0109 --selftest · 6 項 · 不過 1 |
| UIAction v0110 · 同條件 | [PASS] VRN2_UIAction v0110 --selftest · 7 項 · 不過 0 |
| 共識引擎原本 vs v0101(上櫃 .TWO) | [PASS] ⑨ 引擎原本:鉅亨 TWS:5274 → 5274.TW(桌機 404 的根因)· patch 後 → 5274.TWO · 2330 照舊 .TW |
| 同日快取用錯尾碼 → 重抓 | [PASS] ⑪ 同日續跑:checkpoint 裡 5274 是用 .TW 抓的 → 不沿用(重抓)· 2330 用對的 .TW → 照常沿用 |
| 歷史對齊 v0101 vs v0102(同一份資料) | 0101:對上 11 · 沒對上 0 · 無歷史 0(共 11 份)· 覆蓋 76 格 · 刪除區 12 列 · 檢驗 218(不過 74) → 0102:對上 11 · 沒對上 0 · 無歷史 0(共 11 份)· 覆蓋 64 格 · 刪除區 12 列 · 檢驗 192(不過 5 · 口徑不明 6) |
| 端到端:退役環境略過 | [計] 擷取 Python 不用退役 / 備份的環境:via_core.retired-20260914_111946 |
| 端到端:殼有 VIA_ROOT 時處理器自測 | [GREEN] ③ 自測 · VRN2_UIAction_v0110.py · [PASS] VRN2_UIAction v0110 --selftest · 7 項 · 不過 0 · 1 秒 |

## 1. 自測

| 檔 | 結果 |
|---|---|
| VRN2_RoundAll_v0101 | [PASS] VRN2_RoundAll v0101 --selftest · 16 項 · 不過 0 |
| VRN2_UIAction_v0110(殼有 VIA_ROOT) | [PASS] VRN2_UIAction v0110 --selftest · 7 項 · 不過 0 |
| VRN2_ConsensusJoin_v0101 | [PASS] VRN2_ConsensusJoin v0101 --selftest · 11 項 · 不過 0 |
| VRN2_HistoryAlign_v0102 | [PASS] VRN2_HistoryAlign v0102 --selftest · 11 項 · 不過 0 |
| ActivateVRN-2_v0148(建置夾) | [PASS] v0148: UIAction v0110 (hermetic selftest · patch_ui kept) · ConsensusJoin v0101 (TPEx .TWO from the market book) · HistoryAlign v0102 (strict item mapping) |
| ActivateVRN-2_v0148(真套件 zip 解到隔離夾 · VRN2_OUTPUT_DIR / VIA_ROOT 已設) | [PASS] v0148: UIAction v0110 (hermetic selftest · patch_ui kept) · ConsensusJoin v0101 (TPEx .TWO from the market book) · HistoryAlign v0102 (strict item mapping) |

## 2. PowerShell 雜湊鏈(pwsh 7.4.6)

```
Run-VRN2-v0148.ps1 parse errors: 0
boot148.ps1 parse errors: 0
Run-VRN1-VRN2-v0109.ps1 parse errors: 0
boot_pair109.ps1 parse errors: 0
round.ps1 parse errors: 0
vrn2 one-click v0148: code sha = boot H → True (f49cc54d071d)
one-liner decodes to boot → True
package zip sha = \c43a2355cf151239a394dc78af8c1433bee41d9a63d8526a08f600e2d016fa31 → True
operator v0109: code sha = boot H → True (69ce1469c1f3)
operator H2 = vrn2 one-click v0148 code sha → True
operator banner says v0109 → True
localround H_OP = operator v0109 code sha → True
localround H_CS = chainship md v0101 code sha → True
chainship md WANT = tool v0101 sha → True
boot_roundall.ps1 parse errors: 0
roundall one-liner decodes to boot_roundall → True
roundall py sha (LF-normalised) = boot $H → True (ee9500d3a352)
roundall pinned package sha = zip sha → True
roundall CRLF checkout (git autocrlf) still verifies → True
```

## 3. 端到端:RoundAll v0101 在仿桌機沙盒(殼有 VIA_ROOT · envs 有退役環境 · 套件從假 GitHub 分支取 · 共用 MarketFetch 在、沒 yfinance · 輸出夾在 OneDrive · 舊 Google Sheet CSV + 家用記帳 CSV · 19 份真實樣本)

RoundAll 全流程 NEXT: [RED] VRN2_RoundAll · 紅 3 · 黃 11(綠 30 · 黃 11 · 紅 3 · 灰 10)· ③ 自測 12 支 · 綠 12 · 紅的步驟:④ 跑啟動器 ActivateVRN-2_v0148.py / ⑥ 收尾收據 / ⑥ 步驟 ③ 環境檢查與補裝 · Combined 14 列 · 整合 APPLIED(套用 1 · 略過 家用記帳.csv)

```
[GREEN] ⓪ VIA 根 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/VIA
[GREEN] ① 套件 · 套件就位 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/Downloads/VRN2_Closeout_v0148(SHA-256 c43a2355cf15 · 10 檔逐檔相符) · 來源 GitHub claude/optimistic-goodall-yhalc5
[GREEN] ② VRN-2 Python · /tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python(--python · 3.13.16)
[GREEN] ② VRN-2 套件 · 必裝 全在 · 選裝缺 duckdb, rapidocr_onnxruntime
[YELLOW] ② 擷取 Python(⑥e / ⑥f) · 沒有裝齊 yfinance / lxml / pandas / pyarrow / duckdb 的 Python(看過 venv_vrn2 缺 yfinance,duckdb)
[GREEN] ② 共用市場擷取工具 · VRN2_MarketFetch_v0112.py · VDF 引擎 VDF_TW_AllInOne_v039.py
[GREEN] ② 啟動器鎖 · 沒有其他啟動器在跑
[GREEN] ② 輸出檔案夾(長線 Parquet 庫) · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/OneDrive/VRN2_out · 可寫
[GREEN] ② 來源夾 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/samples · PDF 19 份
[GREEN] ② 磁碟 · VIA 根 · 可用 5.9 GB
[GREEN] ② 磁碟 · TEMP · 可用 5.9 GB
[GREEN] ② CPU · 忙碌 26%
[GREEN] ② git · /usr/bin/git
[GREEN] ③ 自測 · runtime 解壓 · 181 檔 逐檔相符
[GREEN] ③ 自測 · VRN2_Workbench_v0102.py · [PASS] VRN2_Workbench v0102 --selftest · 13 項 · 不過 0 · 0 秒
[GREEN] ③ 自測 · VRN2_HistoryAlign_v0100.py · [PASS] VRN2_HistoryAlign v0100 --selftest · 14 項 · 不過 0 · 1 秒
[GREEN] ③ 自測 · VRN2_HistoryAlign_v0102.py · [PASS] VRN2_HistoryAlign v0102 --selftest · 11 項 · 不過 0 · 0 秒
[GREEN] ③ 自測 · VRN2_DataIntegrate_v0100.py · [PASS] VRN2_DataIntegrate v0100 --selftest · 15 項 · 不過 0 · 0 秒
[GREEN] ③ 自測 · VRN2_DataIntegrate_v0101.py · [PASS] VRN2_DataIntegrate v0101 --selftest · 7 項 · 不過 0 · 1 秒
[GREEN] ③ 自測 · VRN2_UIAction_v0110.py · [PASS] VRN2_UIAction v0110 --selftest · 7 項 · 不過 0 · 1 秒
[GREEN] ③ 自測 · VRN2_SSOTSync_v0101.py · [PASS] VRN2_SSOTSync v0101 --selftest · 6 項 · 不過 0 · 0 秒
[GREEN] ③ 自測 · VRN2_OutputStore_v0101.py · [PASS] VRN2_OutputStore v0101 --selftest · 引擎 pyarrow · 8 項 · 不過 0 · 1 秒
[GREEN] ③ 自測 · VRN2_ConsensusJoin_v0101.py · [PASS] VRN2_ConsensusJoin v0101 --selftest · 11 項 · 不過 0 · 2 秒
[GREEN] ③ 自測 · VRN_SystemManager_v0255.py · [PASS] v0255: idempotence gate per-file parallel waves (GREEN · NONDETERMINISTIC · lanes 1) with timing in the receipt; phase timers bound into the native flow; · 10 秒
[GREEN] ③ 自測 · ActivateVRN-2_v0148.py · PASS 6 段 · 1 秒
[RED] ④ 跑啟動器 ActivateVRN-2_v0148.py · rc 1 · 166 秒 · NEXT: [RED] VRN-2 v0148 · rc 1 · 跑了 1 輪 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/VIA/VIA_Reports/vrn2/VRN2_Closeout_v0148.json
[GREEN] ⑤ 修 · 舊資料庫 1 份待決定 · 模式 yes · 資料整合 v0101 · APPLIED · 整合 1 份 → /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/OneDrive/VRN2_out/VRN2/integrated · 原檔副本在 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scra
[GREEN] ⑤ 修 · Workbench 重渲染(最新收據) · VRN2_Workbench v0102 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/VIA/VIA_Reports/vrn2/VRN2_Workbench_latest.html
[RED] ⑥ 收尾收據 · ActivateVRN-2 v0148 · rc 1 · 164.5 秒 · 1 輪 · RoundAll 補修 1 步(rc 不改 · 原收據 VRN2_Closeout_v0148.before_roundall.json)
[RED] ⑥ 步驟 ③ 環境檢查與補裝 · [計] 環境檢查(envcheck · /tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)· 掃 加速器 / 網路工具 2 檔 + VRN-2 尾版 1 · 仍缺 7 · 耗時 3 秒
[GRAY] ⑥ 步驟 ⑥c U/I 操作協定 · 非 Windows · 不註冊 vrn2://(設定檔已寫 · 處理器 VRN2_UIAction_v0110.py) · launcher v0148 · 耗時 0 秒(平行)
[GRAY] ⑥ 步驟 ⑨ 上船 GitHub · Closeout validation only; no Git commit or push · 耗時 0 秒
[GRAY] ⑥ 步驟 ⑩ 整併封存 · Versioned runtime retained; no files moved or deleted · 耗時 0 秒
[GRAY] ⑥ 步驟 ⑫a VRN-1 倉同步(借工具前 · 只 fast-forward) · VIA_VRN2_NO_VRN1_SYNC=1 · 這次不同步 VRN-1 的倉 · 耗時 0 秒
[GRAY] ⑥ 步驟 ⑫ PIVOT 資料庫(借用 VRN-1) · VIA_VRN2_NO_BORROW=1 · 這次不借 · 耗時 0 秒
[YELLOW] ⑥ 步驟 ⑥e 市場擷取(TWSE / TPEX / Yahoo · 借共用 Market · VRN2_MarketFetch_v0112.py · Python 本行程 · 擷取 YELLOW:擷取環境缺套件(/tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)· yfinance / lxml / pandas / pyarro
[YELLOW] ⑥ 步驟 ⑥f 共識合併(FactSet / YFinance → Combined 冊) · 共識 GREEN:共識 13 / 13 代號 · FactSet 中位數 13 · YFinance 中位數 13 · gate PASS_WITH_WARNINGS · rc 0 · Combined YELLOW:Combined 14 列 · 調整後目標價 0 · FactSet 中位數 14 · YFinance 中位數 14 · EPS 格 42 · 年 2026 ~ 2028
[GRAY] ⑥ 步驟 ⑬b 歷史對齊(歷史覆蓋預估 · 加減乘除檢驗 · 刪除區) · 沒有市場資料 VRN2_Market_latest.json(⑥e 沒跑或沒抓到)· 不覆蓋
[YELLOW] ⑥ 步驟 ⑬ 輸出位置 · 增量庫(DuckDB) · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/OneDrive/VRN2_out(OneDrive 同步夾(本機寫入 · 由同步軟體上雲))· 鏡像 20 · 引擎 pyarrow · 新檔 14 / 已知 0 · 追加 BasicInfo 14 / FinancialData 4905 / Summary 14 / 
[YELLOW] ⑥ 四點原文核對 · REVIEW_OCR · {"PASS": 52, "OCR_PENDING": 4} · 不過 4 點:MQ-1560 20260520.pdf 第 1 點 OCR_PENDING(image page; OCR excerpt needs image verification) | MQ-1560 20260520.pdf 第 2 點 OCR_PENDING(image page; OCR excerpt needs image verification) | MQ-15
[YELLOW] ⑥ 輸出缺項 · {"book": "四點原文核對", "reason": "REVIEW_OCR · {'PASS': 52, 'OCR_PENDING': 4}"}
[YELLOW] ⑥ 完成判定 · ① 結果計算驗證 · 黃 1(提醒 · 不擋完成)· 綠 7
[YELLOW] ⑥ 完成判定 · ⑦ 基本資料雙讀 · 黃 1(提醒 · 不擋完成)· 綠 12
[YELLOW] ⑥ 完成判定 · 輸出值驗證(第二讀取器逐值回查 · 年度數據對欄) · 基本資料 欄 126 · 剔除 3 | 年度數據 輸出 4041(對欄 3726 · 未定位 88 · 空值記號 227)· 剔除 212(一格多值 183 · 非數據列 25 · 科目 / 文字混進數值欄 2 · 數值 x 430 不在 FY 1) → output/VRN2_Rejected_latest(帶理由) · v0234 子欄拆分 452 筆(對位驗證 · 剔除剩 77)· 電話第三讀取器補 3 份 · v02
[GRAY] ⑥ 階段耗時 · 總 115.0 秒 · 最慢 驗收 + 摘要 45 · 輸出冊 31 · 擷取迴圈 p1loop 30
[YELLOW] ⑥ Combined 冊 · 14 列 · 欄序正確 · 空格 {"TARGET_PRICE(ADJ)": 14, "FACTSET_TARGET_PRICE_MEDIAN": 0, "YFINANCE_TARGET_PRICE_MEDIAN": 0, "2026_DILUTED_EPS_FACTSET": 0}
[GREEN] ⑥ Workbench U/I · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/VIA/VIA_Reports/vrn2/VRN2_Workbench_latest.html · 雙語表頭 / 靠上 / 千分位 / 自動縮放 / 輸出夾格 / 第一區 都在
[GREEN] ⑥ ⑥f Yahoo 代號 · 對應表 0 筆 · 上櫃 .TWO 0()· Yahoo 404:無
[GRAY] ⑥ 歷史對齊 · 沒有市場資料 VRN2_Market_latest.json(⑥e 沒跑或沒抓到)· 不覆蓋
[YELLOW] ⑥ 長線 Parquet 庫 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/OneDrive/VRN2_out · pyarrow · 累計 {"BasicInfo": 14, "FinancialData": 4905, "Summary": 14, "Rejected": 812, "Combined": 14, "FinancialAligned": 0, "Delet
[GREEN] ⑥ 舊資料庫整合 · APPLIED · 整合 1 份 → /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/OneDrive/VRN2_out/VRN2/integrated · 原檔副本在 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scra
[GRAY] ⑥ SSOT-ID 請求 · 待核號 472 · 提案 9 · 自撞 0(等 VCGC 核發)
[GRAY] ⑥ 獨立驗證摘要 · VRN2_IndependentVerify_20261029_081640.json.digest.txt · [驗證摘要] VRN2_IndependentVerifier_v0110 · 平行 3 路 / 基本資料 14 份 {'PASS': 193, 'OCR': 2} / 一標題四重點 14 份 {'PASS': 65, 'OCR': 5}
[GREEN] ⑦ 貼回包 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/Downloads/VRN2_PasteBack_20261029_081713.zip(0.3 MB)
總表 · 綠 30 · 黃 11 · 紅 3 · 灰 10 · 185 秒
NEXT: [RED] VRN2_RoundAll · 紅 3 · 黃 11 · 貼回包 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/Downloads/VRN2_PasteBack_20261029_081713.zip
```

## 4. 只修回合(`--skip-package --skip-selftest --skip-run`,先放一份合成的市場資料)

只修回合 NEXT: [RED] VRN2_RoundAll · 紅 2 · 黃 12(綠 20 · 黃 12 · 紅 2):⑤ 計畫 市場資料比歷史對齊新 / 歷史對齊沒跑 → 重跑 ⑬b · Combined 比市場 / 共識舊(或不在)→ 重組 · ⑬ 增量庫補寫(本輪有修正) · Workbench 重渲染(最新收據) · 歷史對齊 對上 11 · 沒對上 0 · 無歷史 0(共 11 份)· 覆蓋 64 格 · 刪除區 12 列 · 檢驗 192(不過 5 · 口徑不明 6) · 長線庫 {"BasicInfo": 14, "FinancialData": 4905, "Summary": 14, "Rejected": 812, "Combined": 28, "FinancialAligned": 4905, "Deleted": 12}(Combined 值變了的列另存一版,舊版留著)

```
[GREEN] ⓪ VIA 根 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/VIA
[GRAY] ① 套件 · 略過取套件 · 用 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/Downloads/VRN2_Closeout_v0148
[GREEN] ② VRN-2 Python · /tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python(--python · 3.13.16)
[GREEN] ② VRN-2 套件 · 必裝 全在 · 選裝缺 duckdb, rapidocr_onnxruntime
[YELLOW] ② 擷取 Python(⑥e / ⑥f) · 沒有裝齊 yfinance / lxml / pandas / pyarrow / duckdb 的 Python(看過 venv_vrn2 缺 yfinance,duckdb)
[GREEN] ② 共用市場擷取工具 · VRN2_MarketFetch_v0112.py · VDF 引擎 VDF_TW_AllInOne_v039.py
[GREEN] ② 啟動器鎖 · 沒有其他啟動器在跑
[GREEN] ② 輸出檔案夾(長線 Parquet 庫) · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/OneDrive/VRN2_out · 可寫
[GREEN] ② 來源夾 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/samples · PDF 19 份
[GREEN] ② 磁碟 · VIA 根 · 可用 5.8 GB
[GREEN] ② 磁碟 · TEMP · 可用 5.8 GB
[GREEN] ② CPU · 忙碌 0%
[GREEN] ② git · /usr/bin/git
[GREEN] ⑤ 修 · 市場資料比歷史對齊新 / 歷史對齊沒跑 · 歷史對齊 v0102 · 對上 11 · 沒對上 0 · 無歷史 0(共 11 份)· 覆蓋 64 格 · 刪除區 12 列 · 檢驗 192(不過 5 · 口徑不明 6)
[GREEN] ⑤ 修 · Combined 比市場 / 共識舊(或不在)→ 重組 · 共識合併 v0101 · join · Combined 14 列 · 調整後目標價 11 · FactSet 中位數 14 · YFinance 中位數 14 · EPS 格 42 · 年 2026 ~ 2028
[YELLOW] ⑤ 修 · ⑬ 增量庫補寫(本輪有修正) · pyarrow · 追加 {"BasicInfo": 0, "FinancialData": 0, "Summary": 0, "Rejected": 0, "Combined": 14, "FinancialAligned": 4905, "Deleted": 12} · 補缺 {"BasicInfo": 0, "FinancialData": 0, "Summary": 0, "Rejected": 0, "Combined": 14, "Fina
[GREEN] ⑤ 修 · Workbench 重渲染(最新收據) · VRN2_Workbench v0102 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/VIA/VIA_Reports/vrn2/VRN2_Workbench_latest.html
[RED] ⑥ 收尾收據 · ActivateVRN-2 v0148 · rc 1 · 164.5 秒 · 1 輪 · RoundAll 補修 2 步(rc 不改 · 原收據 VRN2_Closeout_v0148.before_roundall.json)
[RED] ⑥ 步驟 ③ 環境檢查與補裝 · [計] 環境檢查(envcheck · /tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)· 掃 加速器 / 網路工具 2 檔 + VRN-2 尾版 1 · 仍缺 7 · 耗時 3 秒
[GRAY] ⑥ 步驟 ⑥c U/I 操作協定 · 非 Windows · 不註冊 vrn2://(設定檔已寫 · 處理器 VRN2_UIAction_v0110.py) · launcher v0148 · 耗時 0 秒(平行)
[GRAY] ⑥ 步驟 ⑨ 上船 GitHub · Closeout validation only; no Git commit or push · 耗時 0 秒
[GRAY] ⑥ 步驟 ⑩ 整併封存 · Versioned runtime retained; no files moved or deleted · 耗時 0 秒
[GRAY] ⑥ 步驟 ⑫a VRN-1 倉同步(借工具前 · 只 fast-forward) · VIA_VRN2_NO_VRN1_SYNC=1 · 這次不同步 VRN-1 的倉 · 耗時 0 秒
[GRAY] ⑥ 步驟 ⑫ PIVOT 資料庫(借用 VRN-1) · VIA_VRN2_NO_BORROW=1 · 這次不借 · 耗時 0 秒
[YELLOW] ⑥ 步驟 ⑥e 市場擷取(TWSE / TPEX / Yahoo · 借共用 Market · VRN2_MarketFetch_v0112.py · Python 本行程 · 擷取 YELLOW:擷取環境缺套件(/tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)· yfinance / lxml / pandas / pyarro
[YELLOW] ⑥ 步驟 ⑥f 共識合併(FactSet / YFinance → Combined 冊) · 共識 GREEN:共識 13 / 13 代號 · FactSet 中位數 13 · YFinance 中位數 13 · gate PASS_WITH_WARNINGS · rc 0 · Combined YELLOW:Combined 14 列 · 調整後目標價 0 · FactSet 中位數 14 · YFinance 中位數 14 · EPS 格 42 · 年 2026 ~ 2028
[YELLOW] ⑥ 步驟 ⑬ 輸出位置 · 增量庫(DuckDB) · RoundAll 修正後 · pyarrow · 追加 {"BasicInfo": 0, "FinancialData": 0, "Summary": 0, "Rejected": 0, "Combined": 14, "FinancialAligned": 4905, "Deleted": 12} · 補缺 {"BasicInfo": 0, "FinancialData": 0, "Summary": 0, "Rejected": 0
[YELLOW] ⑥ 四點原文核對 · REVIEW_OCR · {"PASS": 52, "OCR_PENDING": 4} · 不過 4 點:MQ-1560 20260520.pdf 第 1 點 OCR_PENDING(image page; OCR excerpt needs image verification) | MQ-1560 20260520.pdf 第 2 點 OCR_PENDING(image page; OCR excerpt needs image verification) | MQ-15
[YELLOW] ⑥ 輸出缺項 · {"book": "四點原文核對", "reason": "REVIEW_OCR · {'PASS': 52, 'OCR_PENDING': 4}"}
[YELLOW] ⑥ 完成判定 · ① 結果計算驗證 · 黃 1(提醒 · 不擋完成)· 綠 7
[YELLOW] ⑥ 完成判定 · ⑦ 基本資料雙讀 · 黃 1(提醒 · 不擋完成)· 綠 12
[YELLOW] ⑥ 完成判定 · 輸出值驗證(第二讀取器逐值回查 · 年度數據對欄) · 基本資料 欄 126 · 剔除 3 | 年度數據 輸出 4041(對欄 3726 · 未定位 88 · 空值記號 227)· 剔除 212(一格多值 183 · 非數據列 25 · 科目 / 文字混進數值欄 2 · 數值 x 430 不在 FY 1) → output/VRN2_Rejected_latest(帶理由) · v0234 子欄拆分 452 筆(對位驗證 · 剔除剩 77)· 電話第三讀取器補 3 份 · v02
[GRAY] ⑥ 階段耗時 · 總 115.0 秒 · 最慢 驗收 + 摘要 45 · 輸出冊 31 · 擷取迴圈 p1loop 30
[YELLOW] ⑥ Combined 冊 · 14 列 · 欄序正確 · 空格 {"TARGET_PRICE(ADJ)": 3, "FACTSET_TARGET_PRICE_MEDIAN": 0, "YFINANCE_TARGET_PRICE_MEDIAN": 0, "2026_DILUTED_EPS_FACTSET": 0}
[GREEN] ⑥ Workbench U/I · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/VIA/VIA_Reports/vrn2/VRN2_Workbench_latest.html · 雙語表頭 / 靠上 / 千分位 / 自動縮放 / 輸出夾格 / 第一區 都在
[GREEN] ⑥ ⑥f Yahoo 代號 · 對應表 0 筆 · 上櫃 .TWO 0()· Yahoo 404:無
[GREEN] ⑥ 市場資料 · 2026-10-29T12:00:00 · {"OK": 14}
[GREEN] ⑥ 歷史對齊 · 對上 11 · 沒對上 0 · 無歷史 0(共 11 份)· 覆蓋 64 格 · 刪除區 12 列 · 檢驗 192(不過 5 · 口徑不明 6)
[YELLOW] ⑥ 長線 Parquet 庫 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/OneDrive/VRN2_out · pyarrow · 累計 {"BasicInfo": 14, "FinancialData": 4905, "Summary": 14, "Rejected": 812, "Combined": 28, "FinancialAligned": 4905, "De
[GREEN] ⑥ 舊資料庫整合 · APPLIED · 整合 1 份 → /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/OneDrive/VRN2_out/VRN2/integrated · 原檔副本在 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scra
[GRAY] ⑥ SSOT-ID 請求 · 待核號 472 · 提案 9 · 自撞 0(等 VCGC 核發)
[GRAY] ⑥ 獨立驗證摘要 · VRN2_IndependentVerify_20261029_081640.json.digest.txt · [驗證摘要] VRN2_IndependentVerifier_v0110 · 平行 3 路 / 基本資料 14 份 {'PASS': 193, 'OCR': 2} / 一標題四重點 14 份 {'PASS': 65, 'OCR': 5}
[GREEN] ⑦ 貼回包 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/Downloads/VRN2_PasteBack_20261029_081745.zip(0.5 MB)
總表 · 綠 20 · 黃 12 · 紅 2 · 灰 9 · 5 秒
NEXT: [RED] VRN2_RoundAll · 紅 2 · 黃 12 · 貼回包 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148/Downloads/VRN2_PasteBack_20261029_081745.zip
```

| 項目 | 值 |
|---|---|
| 長線庫(修後)| {"lamp": "YELLOW", "store_engine": "pyarrow", "appended": {"BasicInfo": 0, "FinancialData": 0, "Summary": 0, "Rejected": 0, "Combined": 14, "FinancialAligned": 4905, "Deleted": 12}, "backfilled": {"BasicInfo": 0, "FinancialData": 0, "Summary": 0, "Rejected": 0, "Combined": 14, "FinancialAligned": 4905, "Deleted": 12}, "totals": {"BasicInfo": 14, "FinancialData": 4905, "Summary": 14, "Rejected": 812, "Combined": 28, "FinancialAligned": 4905, "Deleted": 12}} |
| 歷史對齊(修後)| {"lamp": "GREEN", "why": "對上 11 · 沒對上 0 · 無歷史 0(共 11 份)· 覆蓋 64 格 · 刪除區 12 列 · 檢驗 192(不過 5 · 口徑不明 6)", "totals": {"files": 11, "files_matched": 11, "files_unmatched": 0, "files_no_history": 0, "overrides": 64, "deleted": 12, "checks": 192, "checks_fail": 5, "checks_unclear": 6, "std_excluded_rule": "v0102 排除:其他 / 部門 / 事業 / … of … / 應付 / 負債 / 少數 / 遞延 / 現金 / 調整後 / 核心 / 權益法 / return on / debt"}} |
| 舊資料庫整合 | {"state": "APPLIED", "applied": 1, "skipped": [["家用記帳.csv", "not_vrn2_like · 沒有身分欄(FILENAME / TICKER)"]]} |
| Combined 第一列 | {"FILENAME": "CLST-6669 20251001(20261006-052156).pdf", "TARGET_PRICE": "4200.00", "TARGET_PRICE(ADJ)": "4116.00", "FACTSET_TARGET_PRICE_MEDIAN": "120.00", "YFINANCE_TARGET_PRICE_MEDIAN": "118.00", "2026_DILUTED_EPS_FACTSET": "5.00", "2026_PER_FACTSET": "20.00", "UPSIDE_PCT(ADJ)": "4016.0"} |
| 收尾收據的 roundall 欄 | {"version": "VRN2_RoundAll v0101", "at": "2026-10-29T08:17:45", "fixed": {"⑬b": {"lamp": "GREEN", "detail": "歷史對齊 v0102 · 對上 11 · 沒對上 0 · 無歷史 0(共 11 份)· 覆蓋 64 格 · 刪除區 12 列 · 檢驗 192(不過 5 · 口徑不明 6)"}, "⑬ ": {"lamp": "YELLOW", "detail": "pyarrow · 追加 {\"BasicInfo\": 0, \"FinancialData\": 0, \"Summary\": 0, \"Rejected\": 0, \"Combined\": 14, \"FinancialAligned\": 4905, \"Deleted\": 12} · 補缺 {\"BasicInfo\": 0, \"FinancialData\": 0, \"Summary\": 0, \"Rejected\": 0, \"Combined\": 14, \"FinancialAligned |
| 貼回包 | {"name": "VRN2_PasteBack_20261029_081745.zip", "members": 29, "has": ["transcript.txt", "vrn2/VRN2_Closeout_v0148.before_roundall.json", "vrn2/VRN2_RoundAll_latest.json", "vrn2/output/VRN2_FinancialAligned_latest.csv", "vrn2/output/VRN2_Deleted_latest.csv"]} |

## 5. 一鍵 v0148 使用者情境(pwsh · 假 GitHub 分支 → 跑 → 再貼 → 竄改)

| 項目 | 值 |
|---|---|
| rc | first rc 1 · again rc 1 · tamper rc 1 · done |
| first | [GREEN] ③ 套件 v0148 就位(SHA-256 c43a2355cf15 · 套件內 10 檔逐檔核對相符 · 來源 GitHub claude/optimistic-goodall-yhalc5)→ /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148oc/Download |
| again | [GREEN] ③ 本機已是 v0148 套件(SHA-256 c43a2355cf15 · 套件夾 11 檔與已驗證的 zip 逐檔相符)· /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148oc/Downloads/VRN2_Closeout_v0148 |
| tamper | [GREEN] ③ 舊套件夾已改名備份 → /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v148/t148oc/Downloads/VRN2_Closeout_v0148_20261029_081534.bak |
| closeout | [RED] ⑧b 收尾收據 v0148 · rc 1 · 跑了 1 輪(idempotence GREEN)· 四點原文核對 REVIEW_OCR {'PASS': 52, 'OCR_PENDING': 4} · 輸出缺項 1 |
| roundall_hint | [GRAY] 更完整的除錯 / 自動修 / 貼回包:python VRN2_RoundAll_v0101.py --skip-run(見 vrn2_release_v0148/VRN2_RoundAll_v0101.md) |

## 6. 沒做到 / 沒驗到(照實)

- Windows desktop run of v0148 / RoundAll v0101: not yet (next paste-back)
- 3014TT POINT_3 FAIL (the reason for closeout rc 1 on the desktop): the container only has a synthetic copy of the PDF — needs the paste-back zip
- MS-3661 / MS-6669 / MS-8358 / MS-8210 CURRENT_PRICE / UPSIDE FAIL on the desktop: the same MS-3661 PDF passes when extracted fresh in the container (3190 / 4388 / 38); the desktop reused cached extraction 52/52 — needs the paste-back zip
- ⑥e VDF_TW_AllInOne_v039 fatal errors on the desktop: VDF's own engine (bootstraps via_tw_fetch with pip); reason only in market/vdf/last_error.txt of the paste-back zip; VRN-2 does not modify VDF files
- ⑥f live cnyes / Yahoo: no network here; the .TWO fix is proven on the engine's own ticker function and offline fixtures, not on live Yahoo
- Windows-only paths (os.startfile, winreg vrn2:// lookup, ctypes PID check) are exercised by code review and the posix equivalents only
