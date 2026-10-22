# VRN-2 v0141 容器實測紀錄(2026-10-22 · 操作員令「自動完成 VRN-2 所有問題 自己測試自完成」)

輸入:操作員上傳的 `VRN2_Closeout_v0104.zip`(啟動器 v0140 · 管理器 v0242 · 驗證器 v0109 · runtime v0140 155 個成員)與 `VRN2_VDF_Closeout_v0103.zip`(v0139 前版 · VDF v0115/v0116 本輪不碰),
以及 v0140 在 `C:\測試樣本報告` 的 U/I 貼回:**RED 冪等**(神達 3706 真實內容差異 1 份)· 四點原文核對 **FAIL 8**(GFHK Apple update POINT_1~4 · 欣銓 POINT_3~4 · 3014TT · 華南 2606)· OCR_PENDING 4(MQ-1560)· 輸出冊缺項 6 · 獨立驗證 ✗ 45(6933 AMAX 37 · 凱基 2891 8)。

## 1. 主體不動(逐位元組)

runtime v0140 的 155 個成員(管理器鏈 v0100 → v0242 · ENG397 v0127 · ENG062 v0114 / v0115 · 驗證器 v0105 ~ v0109 · 處理器 · 工具橋 · 原文核對 v0100 ~ v0103 · 規則目錄)逐位元保留在 runtime v0141;啟動器底座 `ActivateVRN-2_v0136.py`(`cb6bf142a0e3…`)不動。新增 4 檔:`VRN_ENG062_SummarizerV1_v0116.py` · `VRN_SystemManager_v0243.py` · `VRN2_VerbatimVerifier_v0104.py` · `VRN2_IndependentVerifier_v0110.py`;入口 `ActivateVRN-2_v0141.py`。

| 檔 | SHA-256 |
|---|---|
| `VRN2_Closeout_v0141.zip`(套件 · 一鍵 ③ 核對的就是這個)| `11b2de30419f2107e898f27e6fe0278515fc5fd0e9c43c36069394c4d63e51f9` |
| `ActivateVRN-2_v0141.py` | `fe1b03cd72687df7fc8eb1bdb8086efab632d130760e0ebf82b80b78c1ae2e71` |
| `VRN2_Runtime_v0141.zip` | `b41b6dc65ba52c6ed6d497faaa7230230745811437a3b2c0940160ac3b3f1242` |
| 一鍵程式碼(`VRN2_OneClick_v0141.md` 內)| `1dcf40389bbf…` |

## 2. 貼回的問題 → 根因 → 做法

| # | 貼回 | 容器裡追到的 | v0141 做法 | 在哪支 |
|---|---|---|---|---|
| 1 | 冪等 RED:神達 3706 主跑紀錄 ≠ 重跑 | 原檔不在容器(本機 13 份真實多頁檔 · 主跑分路 / 同行程 / 快取命中 三條路徑 ×4 次語意差異 **0**)。v0242 的閘是「主跑紀錄(可能來自擷取快取 / 子行程)vs 同行程重跑一次」,不是像對像,也分不出「紀錄過期」與「引擎非冪等」 | 冪等閘走主跑同一條子行程路徑重跑**兩次**:全同 GREEN;重跑一致、主跑不同 = STALE_RECORD → 清該檔擷取快取 → 啟動器自動再跑一輪;重跑就不同 = NONDETERMINISTIC(RED · 第一個差異路徑)· 收據記錄執行環境 | 管理器 v0243 `_idem_check` · 啟動器 v0141 `repass_wanted` |
| 2 | 四點原文核對 FAIL 8 | 摘要器 v0115 只挑嚴格句(前 3 頁 · ≥24 中文字 / ≥9 英文字 · 主題詞 · 數字比例);短訊 / bullet / 英文 update 湊不滿 4 點 → 空點被原文核對 v0103 算 FAIL | 階梯補齊(放寬句 → 單行 → 整頁文字行 · 去掉開頭 bullet / 控制字元 · 每點仍是精確字串);原文核對 v0104:缺句 = MISSING(rc 2 待核對),比對忽略 bullet / 控制字元 | ENG062 v0116 · 原文核對 v0104 · 驗證器 v0110 |
| 3 | 輸出冊缺項 6 | 同 2 | 同 2 | 同 2 |
| 4 | U/I「複製執行指令」| v0242 把 v0136 的備援指令(升優先權 → PS 加速器 → 實際啟動器 · 不上船版)換成只有 PS7 模板 → 真瀏覽器檢查 3 條不過 | 回到 v0136 契約再加 PS7 模板 + `VRN2_ROOT` + finally Restore | 管理器 v0243 `_ui_panel_html` |
| 5 | 獨立驗證 ✗ 45(6933 · 2891)| 兩份 PDF 不在容器 | 財務核心 v0105 不動;需原檔或 `verify_independent\*.digest.txt` | — |

## 3. 自測

| 項目 | 結果 |
|---|---|
| ENG062 v0116 `--selftest` | PASS(v0115 嚴格挑句不變 · 短訊 / 整頁文字補滿 4 點且每點是原文精確字串 · 沒文字層仍 MISSING · 竄改被拒)|
| 管理器 v0243 `--selftest` | PASS(分類 GREEN / STALE_RECORD / NONDETERMINISTIC 三種 · 備援指令契約 · 數值竄改被抓)|
| 原文核對 v0104 / 驗證器 v0110 `--selftest` | PASS(缺句 MISSING rc 2 · 無證據文字仍 FAIL rc 1 · v0105 財務核心 30/30)|
| 啟動器 v0141 `--selftest` | PASS(結束碼規則 · 私有 runtime 還原與衝突保留 · 只在 STALE_RECORD 再跑)|
| 合成短訊 / 英文 update PDF(PyMuPDF 寫文字層)| v0115:GFHK 0/4 · 欣銓 1/4 → v0116:`TOTAL {'PASS': 5, 'FAIL': 3, 'OCR_PENDING': 0, 'MISSING': 4}`(純數字頁正確 MISSING)|
| 13 份真實個股 PDF 四點核對(v0115 即可)| `TOTAL {'PASS': 48, 'FAIL': 0, 'OCR_PENDING': 0, 'MISSING': 0}` |

## 4. 沙盒端到端(啟動器 v0141 · 19 份真實 PDF · 個股 14)

- ⑦ 14 份(全綠 14)· ⑧ **完成** 紅 0 黃 3(VRN-2 SystemManager v0243)· 冪等閘 **GREEN**(Daiwa-1319 20231011(20 · GS-6415 20260517.pdf · JP-2330 20250718.pdf · 同主跑子行程路徑 ×2)
- 四點原文核對 `{'PASS': 52, 'OCR_PENDING': 4}`(MQ-1560 影像頁 4 點 OCR 待核對)· 一標題四重點 14 份全部 4/4 · 挑句層級 {'strict': 56}
- ⑪ 獨立驗證 VRN2_IndependentVerifier_v0110:錯值 **0** · 基本資料 {'PASS': 193, 'OCR': 2} · 一標題四重點 {'PASS': 65, 'OCR': 5} · 年度數據 4905 筆 {'ALIGNED': 4378, 'TRANSALIGNED': 75, 'SUBALIGNED': 452}
- 收據 rc 1:③ 環境檢查 RED in the Linux sandbox only (VeritasCeleritas accelerator deps not in venv: accelerator · curl_cffi · cv2 · duckdb · lz4 · pyvips · watchdog; --no-install); every VRN-2 gate GREEN; v0140+ returns rc 1 for any RED step;跑了 1 輪
- **冪等自癒情境**(竄改擷取快取裡 1 份的一格數值再跑):第 1 輪 `STALE_RECORD · Daiwa-1319 20231011(20261006-122413).pdf · cache cleare` → 自動第 2 輪 → 最終 **GREEN**(跑了 2 輪)
- U/I 真瀏覽器(Chromium):`ui_test` 35 / 35 · `ui_input` 14 / 14

## 5. 一鍵 v0141(pwsh 7.4.6 · 假 GitHub 分支 · 本機沒有套件)

結束碼:`first rc 1 · again rc 1 · tamper rc 1 · done`(RED 1 只因沙盒的 ③ 環境檢查:加速器 VeritasCeleritas 的 7 個相依套件不在 venv —— accelerator · curl_cffi · cv2 · duckdb · lz4 · pyvips · watchdog;v0140 起任一紅燈步驟 rc 1。VRN-2 自己的閘全綠:⑧ 完成 · 冪等 GREEN · ⑪ 錯值 0 · 四點 52 PASS + 4 OCR;Windows 上 ③ 綠 → 最多 YELLOW 2(OCR 待核對))

第一次(從 GitHub 取套件):
```
[GREEN] ③ 套件 v0141 就位(SHA-256 11b2de30419f · 套件內 10 檔逐檔核對相符 · 來源 GitHub claude/optimistic-goodall-yhalc5)→ /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v141/t141oc/Downloads/VRN2_Closeout_v0141
→ RED ③ 環境檢查與補裝 · [計] 環境檢查(envcheck · /tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)· 掃 加速器 / 網路工具 2 檔 + VRN-2 尾版 9 · 仍缺 7 · 耗時 3 秒
→ GREEN ③b OCR 隔離環境 · 沿用指定的 OCR 環境 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v131/ocrenv/vrn2_ocr/bin/python · official ONNX telemetry opt-out bridge v0101 · 耗時 0 秒(平行)
→ GREEN ⑦ 啟動 VRN-2 · [計] VRN-2 個股四項 · 14 份(全綠 14)· 檔名 綠14黃0紅0灰0 · 首頁 綠14黃0紅0灰0 · 年度財報 綠12黃0紅0灰2 · 評價資訊 綠12黃0紅0灰2 · 本輪新鎖 52 項 · 累計鎖 52 項 · 退步 0 · U/I /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v141/t14
→ GREEN ⑧ 完成判定 · VRN-2 完成 · 輸出驗證 紅 0 黃 3 · 耗時 0 秒
→ GREEN ⑪ 獨立驗證(背景 · 只讀) · 錯值 0 · 基本資料 14 份 · 欄位檢查 {'PASS': 193, 'OCR': 2} · 一標題四重點 14 份 · 欄位檢查 {'PASS': 65, 'OCR': 5} · 年度數據 4905 筆 · {'ALIGNED': 4378, 'TRANSALIGNED': 75, 'SUBALIGNED': 452} · U/I「驗證過的輸出」已寫回 · 報告 VRN2_IndependentV
[RED] ③ 環境檢查與補裝 · [計] 環境檢查(envcheck · /tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)· 掃 加速器 / 網路工具 2 檔 + VRN-2 尾版 9 · 仍缺 7 · 耗時 3 秒
NEXT: VRN-2 完成 · 自測 / 實測全過 · 獨立驗證錯值 0(U/I「驗證過的輸出」每格有驗證徽章) · PIVOT 沒寫(VIA_VRN2_NO_VRN1_SYNC=1 · 這次不同步 VRN-1 的倉 · 耗時 0 秒)
NEXT: [RED] VRN-2 v0141 · rc 1 · 跑了 1 輪 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v141/t141oc/VIA/VIA_Reports/vrn2/VRN2_Closeout_v0141.json
[GREEN] ⑧ 完成判定 · 完成 · 紅 0 · 黃 3 · VRN-2 SystemManager v0243 · 本輪
[RED] ⑧b 收尾收據 v0141 · rc 1 · 跑了 1 輪(idempotence GREEN)· 四點原文核對 REVIEW_OCR {'PASS': 52, 'OCR_PENDING': 4} · 輸出缺項 1
[RED]    紅燈步驟 · ③ 環境檢查與補裝 · [計] 環境檢查(envcheck · /tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)· 掃 加速器 / 網
[GREEN] 冪等閘 · GREEN · Daiwa-1319 20231011(2026 · GS-6415 20260517.pdf · JP-2330 20250718.pdf · same shard subprocess path as the main run (python -W ignore ENG397 --
[GREEN] ⑤b 目前輸入 · 個股報告/訊息 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v141/t141oc/samples(啟動器 --source)· 檔 19(PDF 19 · Word 0 · TXT 0 · 影像 0)· 個股範圍 14 · 範圍外 5(產業 / 其他 · 檔名規則 VRN_SystemManager_v0231.p
[GRAY] ⑤c U/I 不開(VRN2_NO_UI = 1)
NEXT: [RED] VRN-2 有紅燈(⑧ 完成判定不是本輪的綠 或 啟動器 rc 1:紅燈步驟 / 四點原文核對 FAIL / 冪等非冪等)· 看 ⑧b 收尾收據與冪等閘那兩行 · 把貼包(≤300 行 · 結尾 NEXT)貼回 · 交接報告 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v141/t141oc/VIA/docs/handoff/ai/
```
再貼一次(本機已是 v0141 套件 · 套件夾逐檔對已驗證的 zip):
```
[GREEN] ③ 本機已是 v0141 套件(SHA-256 11b2de30419f · 套件夾 11 檔與已驗證的 zip 逐檔相符)· /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v141/t141oc/Downloads/VRN2_Closeout_v0141
→ RED ③ 環境檢查與補裝 · [計] 環境檢查(envcheck · /tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)· 掃 加速器 / 網路工具 2 檔 + VRN-2 尾版 9 · 仍缺 7 · 耗時 3 秒
→ GREEN ③b OCR 隔離環境 · 沿用指定的 OCR 環境 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v131/ocrenv/vrn2_ocr/bin/python · official ONNX telemetry opt-out bridge v0101 · 耗時 0 秒(平行)
→ GREEN ⑦ 啟動 VRN-2 · [計] VRN-2 個股四項 · 14 份(全綠 14)· 檔名 綠14黃0紅0灰0 · 首頁 綠14黃0紅0灰0 · 年度財報 綠12黃0紅0灰2 · 評價資訊 綠12黃0紅0灰2 · 本輪新鎖 0 項 · 累計鎖 52 項 · 退步 0 · U/I /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v141/t141
→ GREEN ⑧ 完成判定 · VRN-2 完成 · 輸出驗證 紅 0 黃 3 · 耗時 0 秒
→ GREEN ⑪ 獨立驗證(背景 · 只讀) · 錯值 0 · 基本資料 14 份 · 欄位檢查 {'PASS': 193, 'OCR': 2} · 一標題四重點 14 份 · 欄位檢查 {'PASS': 65, 'OCR': 5} · 年度數據 4905 筆 · {'ALIGNED': 4378, 'TRANSALIGNED': 75, 'SUBALIGNED': 452} · U/I「驗證過的輸出」已寫回 · 報告 VRN2_IndependentV
[RED] ③ 環境檢查與補裝 · [計] 環境檢查(envcheck · /tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)· 掃 加速器 / 網路工具 2 檔 + VRN-2 尾版 9 · 仍缺 7 · 耗時 3 秒
NEXT: VRN-2 完成 · 自測 / 實測全過 · 獨立驗證錯值 0(U/I「驗證過的輸出」每格有驗證徽章) · PIVOT 沒寫(VIA_VRN2_NO_VRN1_SYNC=1 · 這次不同步 VRN-1 的倉 · 耗時 0 秒)
NEXT: [RED] VRN-2 v0141 · rc 1 · 跑了 1 輪 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v141/t141oc/VIA/VIA_Reports/vrn2/VRN2_Closeout_v0141.json
[GREEN] ⑧ 完成判定 · 完成 · 紅 0 · 黃 3 · VRN-2 SystemManager v0243 · 本輪
[RED] ⑧b 收尾收據 v0141 · rc 1 · 跑了 1 輪(idempotence GREEN)· 四點原文核對 REVIEW_OCR {'PASS': 52, 'OCR_PENDING': 4} · 輸出缺項 1
[RED]    紅燈步驟 · ③ 環境檢查與補裝 · [計] 環境檢查(envcheck · /tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)· 掃 加速器 / 網
[GREEN] 冪等閘 · GREEN · Daiwa-1319 20231011(2026 · GS-6415 20260517.pdf · JP-2330 20250718.pdf · same shard subprocess path as the main run (python -W ignore ENG397 --
[GREEN] ⑤b 目前輸入 · 個股報告/訊息 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v141/t141oc/samples(啟動器 --source)· 檔 19(PDF 19 · Word 0 · TXT 0 · 影像 0)· 個股範圍 14 · 範圍外 5(產業 / 其他 · 檔名規則 VRN_SystemManager_v0231.p
[GRAY] ⑤c U/I 不開(VRN2_NO_UI = 1)
NEXT: [RED] VRN-2 有紅燈(⑧ 完成判定不是本輪的綠 或 啟動器 rc 1:紅燈步驟 / 四點原文核對 FAIL / 冪等非冪等)· 看 ⑧b 收尾收據與冪等閘那兩行 · 把貼包(≤300 行 · 結尾 NEXT)貼回 · 交接報告 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v141/t141oc/VIA/docs/handoff/ai/
```
第三次(Codex #566:套件夾裡的啟動器被改一行 → 快路徑逐檔核對抓到 → 從本機已驗證的 zip 重新解壓 · 舊夾改名備份):
```
[YELLOW] ③ 本機套件夾有 1 個檔與已驗證的 zip 不同或不在(ActivateVRN-2_v0141.py)→ 不用它,從本機這份 zip 重新解壓
[GREEN] ③ 舊套件夾已改名備份 → /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v141/t141oc/Downloads/VRN2_Closeout_v0141_20261022_080341.bak
[GREEN] ③b VRN-2 程式夾 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v141/t141oc/VIA/functional modules/VRN(來源 VIA 根)· 私有 runtime → /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/
→ RED ③ 環境檢查與補裝 · [計] 環境檢查(envcheck · /tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)· 掃 加速器 / 網路工具 2 檔 + VRN-2 尾版 9 · 仍缺 7 · 耗時 3 秒
→ GREEN ③b OCR 隔離環境 · 沿用指定的 OCR 環境 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v131/ocrenv/vrn2_ocr/bin/python · official ONNX telemetry opt-out bridge v0101 · 耗時 0 秒(平行)
→ GREEN ⑦ 啟動 VRN-2 · [計] VRN-2 個股四項 · 14 份(全綠 14)· 檔名 綠14黃0紅0灰0 · 首頁 綠14黃0紅0灰0 · 年度財報 綠12黃0紅0灰2 · 評價資訊 綠12黃0紅0灰2 · 本輪新鎖 0 項 · 累計鎖 52 項 · 退步 0 · U/I /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v141/t141
→ GREEN ⑧ 完成判定 · VRN-2 完成 · 輸出驗證 紅 0 黃 3 · 耗時 0 秒
→ GREEN ⑪ 獨立驗證(背景 · 只讀) · 錯值 0 · 基本資料 14 份 · 欄位檢查 {'PASS': 193, 'OCR': 2} · 一標題四重點 14 份 · 欄位檢查 {'PASS': 65, 'OCR': 5} · 年度數據 4905 筆 · {'ALIGNED': 4378, 'TRANSALIGNED': 75, 'SUBALIGNED': 452} · U/I「驗證過的輸出」已寫回 · 報告 VRN2_IndependentV
[RED] ③ 環境檢查與補裝 · [計] 環境檢查(envcheck · /tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)· 掃 加速器 / 網路工具 2 檔 + VRN-2 尾版 9 · 仍缺 7 · 耗時 3 秒
NEXT: VRN-2 完成 · 自測 / 實測全過 · 獨立驗證錯值 0(U/I「驗證過的輸出」每格有驗證徽章) · PIVOT 沒寫(VIA_VRN2_NO_VRN1_SYNC=1 · 這次不同步 VRN-1 的倉 · 耗時 0 秒)
NEXT: [RED] VRN-2 v0141 · rc 1 · 跑了 1 輪 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v141/t141oc/VIA/VIA_Reports/vrn2/VRN2_Closeout_v0141.json
[GREEN] ⑧ 完成判定 · 完成 · 紅 0 · 黃 3 · VRN-2 SystemManager v0243 · 本輪
[RED] ⑧b 收尾收據 v0141 · rc 1 · 跑了 1 輪(idempotence GREEN)· 四點原文核對 REVIEW_OCR {'PASS': 52, 'OCR_PENDING': 4} · 輸出缺項 1
[GREEN] 冪等閘 · GREEN · Daiwa-1319 20231011(2026 · GS-6415 20260517.pdf · JP-2330 20250718.pdf · same shard subprocess path as the main run (python -W ignore ENG397 --
[YELLOW] ⑤b U/I 有輸入區塊,但 vrn2:// 沒註冊(HKCU)→ 按鈕不會有反應;在 Windows 重跑一次啟動器(⑥c 會註冊並讀回核對)或用 $env:VRN2_SOURCE
[GREEN] ⑤b 目前輸入 · 個股報告/訊息 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v141/t141oc/samples(啟動器 --source)· 檔 19(PDF 19 · Word 0 · TXT 0 · 影像 0)· 個股範圍 14 · 範圍外 5(產業 / 其他 · 檔名規則 VRN_SystemManager_v0231.p
[GRAY] ⑤c U/I 不開(VRN2_NO_UI = 1)
NEXT: [RED] VRN-2 有紅燈(⑧ 完成判定不是本輪的綠 或 啟動器 rc 1:紅燈步驟 / 四點原文核對 FAIL / 冪等非冪等)· 看 ⑧b 收尾收據與冪等閘那兩行 · 把貼包(≤300 行 · 結尾 NEXT)貼回 · 交接報告 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v141/t141oc/VIA/docs/handoff/ai/
```

## 6. 沒做 / 照實說

- Windows full-sample run (C:\測試樣本報告 · 52 stock reports) · the operator's own PDFs for 神達 3706 / GFHK / 欣銓 / 6933 AMAX / 凱基 2891 are not in the container: the ladder and the idempotence classification are proven on real + synthetic files here, not on those five
- 獨立驗證 ✗ 45 (6933 AMAX 37 · 凱基 2891 8): financial core v0105 untouched; needs those PDFs or verify_independent digest to root-cause
- MQ-1560 four points stay OCR_PENDING (image page) by design

日誌:`logs_v0141.zip` · 測試工具:`vrn2_test_tools_v0141.zip`(產生器 · 情境腳本 · 不含 .ps1)。v0136 / v0140 都留著。
