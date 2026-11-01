# VRN-2 v0152 + VRN2_RoundAll_v0108 + VRN2_HandleAll_v0100 容器實測紀錄(2026-10-30)

操作員 2026-10-30「GENERATE A PS CODE TO HANDLE ALL」(貼回的是桌機 17:06 跑 RoundAll v0107 只重做報告:收尾 OPEN · VRN-2 1 = ⑪ 年度數據 FAIL 證據 · 驗證器讀法 · 原文相符)→ v0152(見發行清單 `fixes` · `not_fixed_here`)。

## 1. 自測

| 檔 | 結果 |
|---|---|
| VRN2_IndependentVerifier_v0114(VIA 樹內 · 含 v0105 · v0110 ~ v0113) | [PASS] v0114: annual FAIL aligned by column in the second reading — Daiwa aspeed PBR 26E 'n.a.' = source → NILVAL · number equal → PRESENT · a value m / [PASS] v0113: BADITEM read a second way — item on the page (whole · wrapped · words in order) keeps PRESENT / ALIGNED; fabricated / renamed item stays |
| VRN2_RoundAll_v0108 | [PASS] VRN2_RoundAll v0108 --selftest · 44 項 · 不過 0 |
| ActivateVRN-2_v0152(建置夾) | [PASS] v0152: runtime's newest IndependentVerifier = v0114 (annual FAIL aligned by column in the second reading · structural copy, its own --shard) · v0113 kept |
| ActivateVRN-2_v0152(套件夾複本 · 不靠 ../new) | [PASS] v0152: runtime's newest IndependentVerifier = v0114 (annual FAIL aligned by column in the second reading · structural copy, its own --shard) · v0113 kept |

## 2. IndependentVerifier v0114 回歸 + 變造(14 份真實 PDF · 4905 筆)

```
0) 原樣 4378 筆 · core {'ALIGNED': 4378} · v0114 {'ALIGNED': 4378} · 判決不同 0
A) 冊值改成 n.a. 60 筆 · core {'FAIL': 49, 'NILVAL': 5, 'PRESENT': 6} · v0114 {'FAIL': 49, 'NILVAL': 5, 'PRESENT': 6} · v0114 誤放行 0
B) 冊值改成別的數字 60 筆 · core {'FAIL': 60} · v0114 {'FAIL': 60} · v0114 誤放行 0
C) 字元框讀法把值讀壞 60 筆(桌機的樣子)· core {'FAIL': 46, 'PRESENT': 14} · v0114 {'FAIL': 35, 'PRESENT': 25} · core FAIL 46 → v0114 依欄位對齊救回 11(其餘對不齊 → 照樣 FAIL)
```

整支跑(平行子行程)v0113 vs v0114:`{"fin_rows 相同": true, "fin_counts": {"ALIGNED": 4378, "TRANSALIGNED": 75, "SUBALIGNED": 452}, "basic 相同(排序後)": true, "summary 相同(排序後)": true, "筆數": 4905}`

## 3. PowerShell 雜湊鏈與剖析(pwsh 7.4.6)

```
[PASS] 套件 zip = RoundAll 釘的 = 發行清單 · ba3bbfd5d0ce
[PASS] RoundAll 檔 = Handle-All 一行 / 可讀版 / PS7 一行 / 解開版的 $H = 發行清單 · 58576a79c441
[PASS] HandleAll md:第一段 = 一行檔 · 第二段 = 可讀版 · 一行 SHA-256 標在 md 與發行清單 · d4efc02c12b2
[PASS] RoundAll md:PS7 一行 = 檔 · 兩行 -EncodedCommand 解開 = 解開版 · 都在 8191 字元內
[PASS] Handle-All / PS7 一行沒有 exit(視窗不關)· 沒有 # 註解 · 8573 字元
[PASS] PowerShell 剖析(pwsh 7.4.6)0 錯:handleall_line.txt 1231 詞 · handleall_src.ps1 1243 詞 · oneline_roundall_ps7.txt 378 詞 · boot_roundall.ps1 501 詞
[PASS] Handle-All 一行版 = 可讀版(去掉換行 / 分號後詞序列相同)
```

## 4. 桌機情境:貼 Handle-All(只有啟動器 v0151 的收據 + 上一輪輸出 · 跟桌機 17:06 一樣)

| 項目 | 結果 |
|---|---|
| auto → 模式 | [計] ④ 自動選模式 verify · 上一輪收據 VRN2_Closeout_v0151.json · 上一輪輸出冊 有(要整輪:先貼 $env:VRN2_MODE = 'full') |
| ⑤ 取 RoundAll | [GREEN] ⑤ VRN2_RoundAll_v0108.py SHA-256 58576a79c441 相符(GitHub claude/optimistic-goodall-yhalc5)→ <v152>/t152d/home/Downloads/VRN2_RoundAll_v0108.py |
| ① 套件 | [GREEN] ① 套件 · 套件就位 <v152>/t152d/home/Downloads/VRN2_Closeout_v0152(SHA-256 ba3bbfd5d0ce · 11 檔逐檔相符) · 來源 GitHub claude/optimistic-goodall-yhalc5 |
| ⑪b | [GREEN] ⑪b 重跑獨立驗證 · VRN2_IndependentVerifier_v0114 · 錯值 0 · 基本資料 14 份 · 欄位檢查 {'PASS': 193, 'OCR': 2} · 一標題四重點 14 份 · 欄位檢查 {'PASS': 65, 'OCR': 5} · 年度數據 4905 筆 · {'ALIGNED': 4378, 'TRANSALIGNED': 75, 'SUBALIGNED': 452} · 報告 VRN2_IndependentVerify_20261030_093238.json · 32 秒 |
| 收尾收據(沿用前版) | [RED] ⑥ 收尾收據 · ActivateVRN-2 v0151 · rc 1 · 195.58 秒 · 1 輪 · RoundAll 補修 3 步(rc 不改 · 原收據 VRN2_Closeout_v0151.before_roundall.json) · 沿用前版收據 VRN2_Closeout_v0151.json(這輪沒跑啟動器 v0152) |
| v0151 收據 ⑪ 改後 | [('⑪ 獨立驗證(背景 · 只讀)', 'GREEN', "RoundAll 修正後 · VRN2_IndependentVerifier_v0114 · 錯值 0 · 基本資料 14 份 · 欄位檢查 {'PASS': 193, 'OCR': 2} · 一標題四重點 14 份 · 欄位檢查 {'P")] |
| v0151 收據 roundall.fixed | ['⑪', '⑬ ', '⑬b'] |
| 收尾頁 | BLOCKED · VRN-2 側沒有待修 · 5 項等 VCGC 決定 / 安裝 · {"VCGC": 5, "人工": 2} |
| 貼回包帶收據 | ['vrn2/VRN2_CloseoutUI_latest.html', 'vrn2/VRN2_CloseoutUI_latest.json', 'vrn2/VRN2_Closeout_v0151.json', 'vrn2/VRN2_Closeout_v0151.before_roundall.json'] |
| report 模式 | [計] Handle-All 結束 · RoundAll 結束碼 1 · 1 秒(視窗不會關) |
| 錯模式 | [RED] VRN2_MODE = xyz 不認得(auto / full / verify / report) |
| 不是 git 倉 | [RED] ① <v152>/t152d/tmp 不是 git 倉(先設 $env:VRN2_ROOT = '<VIA 根>') |
| RoundAll 被竄改 | [RED] ⑤ VRN2_RoundAll_v0108.py SHA-256 不對(e4fc05b8be96bd6daa1688fc6803adb9f16bb46267ce68bdcde89c6f0b73eac2)· 不執行 · 存檔:沒有(不執行) |

```
[GREEN] ① 工具 · git 倉 <v152>/t152d/VIA · Python 3.13.16(/tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)
[GREEN] ③ Downloads 的 VRN-2 套件夾都讀得到
[計] ④ 自動選模式 verify · 上一輪收據 VRN2_Closeout_v0151.json · 上一輪輸出冊 有(要整輪:先貼 $env:VRN2_MODE = 'full')
[計] ④ 模式 verify:只重跑 ⑪ 獨立驗證(套件 v0152 的 IndependentVerifier v0114 · 用上一輪的輸出冊)→ 除錯報告 → 收尾頁 → 貼回包(約 10 分鐘)
[GREEN] ⑤ VRN2_RoundAll_v0108.py SHA-256 58576a79c441 相符(GitHub claude/optimistic-goodall-yhalc5)→ <v152>/t152d/home/Downloads/VRN2_RoundAll_v0108.py
[GREEN] ① 套件 · 套件就位 <v152>/t152d/home/Downloads/VRN2_Closeout_v0152(SHA-256 ba3bbfd5d0ce · 11 檔逐檔相符) · 來源 GitHub claude/optimistic-goodall-yhalc5
[計] ⑪b VRN2_IndependentVerifier_v0114.py 重跑(/tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)· 輸出冊 <v152>/t152d/VIA/VIA_Reports/vrn2/output · 原檔 <v152>/t152d/VIA/VIA_Repo
[GREEN] ⑪b 重跑獨立驗證 · VRN2_IndependentVerifier_v0114 · 錯值 0 · 基本資料 14 份 · 欄位檢查 {'PASS': 193, 'OCR': 2} · 一標題四重點 14 份 · 欄位檢查 {'PASS': 65, 'OCR': 5} · 年度數據 4905 筆 · {'ALIGNED': 4378, 'TRANSALIGNED': 75, 'SUBALIGNED': 452} · 報告 VRN2_In
[GREEN] ⑥ ⑪ 驗證器版本 · VRN2_IndependentVerifier_v0114 · VRN2_IndependentVerify_20261030_093238.json
[YELLOW] ⑧ 收尾頁(HTML U/I) · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 5 項等 VCGC 決定 / 安裝 · VRN-2 0 · VCGC 5 · 人工 2 · 資料源 0 → <v152>/t152d/VIA/VIA_Reports/vrn2/VRN2_CloseoutUI_latest.html
總表 · 綠 11 · 黃 11 · 紅 2 · 灰 8 · 33 秒
===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 5 項等 VCGC 決定 / 安裝
  [VCGC] 5 項
  [人工] 2 項
  下一步:VRN-2 側已結案 · 剩下是 VCGC 的決定 / 安裝(上面 [VCGC] 那幾項 · 例:MOPS 經 VIA 網路工具被 DENY)→ 交 VCGC,VRN-2 不繞道
[計] Handle-All 結束 · RoundAll 結束碼 1 · 34 秒(視窗不會關)
```

## 5. 全新沙盒:貼 Handle-All(auto → full)→ 再貼(auto → verify)→ report

| 項目 | 結果 |
|---|---|
| auto → 模式(沒有收據) | [計] ④ 自動選模式 full · 上一輪收據 沒有 · 上一輪輸出冊 沒有(要整輪:先貼 $env:VRN2_MODE = 'full') |
| ③ 自測 | 14 支 · 綠 14 · 紅 / 黃 0 |
| ④ 啟動器 v0152 |   [RED] ④ 跑啟動器 ActivateVRN-2_v0152.py · rc 1 · 176 秒 |
| ⑪(啟動器內 · 背景) |   [計] ⑪ 獨立驗證 · 年度數據 4905 筆 · {'ALIGNED': 4378, 'TRANSALIGNED': 75, 'SUBALIGNED': 452} |
| ⑥ ⑪ 驗證器版本 | [GREEN] ⑥ ⑪ 驗證器版本 · VRN2_IndependentVerifier_v0114 · VRN2_IndependentVerify_20261030_093232.json |
| 總表 | 總表 · 綠 33 · 黃 14 · 紅 3 · 灰 10 · 198 秒 |
| 再貼(auto → 模式) | [計] ④ 自動選模式 verify · 上一輪收據 VRN2_Closeout_v0152.json · 上一輪輸出冊 有(要整輪:先貼 $env:VRN2_MODE = 'full') |
| 再貼 ⑪b | [GREEN] ⑪b 重跑獨立驗證 · VRN2_IndependentVerifier_v0114 · 錯值 0 · 基本資料 14 份 · 欄位檢查 {'PASS': 193, 'OCR': 2} · 一標題四重點 14 份 · 欄位檢查 {'PASS': 65, 'OCR': 5} · 年度數據 4905 筆 · {'ALIGNED': 4378, 'TRANSALIGNED': 75, ' |
| report | 總表 · 綠 7 · 黃 12 · 紅 2 · 灰 11 · 0 秒 |
| 收尾頁(最後) | BLOCKED · VRN-2 側沒有待修 · 7 項等 VCGC 決定 / 安裝 · {"VCGC": 7, "人工": 2} |
| v0152 收據 roundall.fixed | ['⑪', '⑬c'] |
| 貼回包帶收據 | ['vrn2/VRN2_Closeout_v0152.json', 'vrn2/VRN2_Closeout_v0152.before_roundall.json', 'vrn2/VRN2_CloseoutUI_latest.html', 'vrn2/VRN2_CloseoutUI_latest.json'] |
| 容器才有的 VCGC 項 | ③ 環境檢查缺 7(accelerator / curl_cffi / cv2 / duckdb / lz4 / pyvips / watchdog)· ⑥e 擷取 Python 沒有合 VDF 界線的 —— 容器沒裝,桌機有 |

```
[GREEN] ① 工具 · git 倉 <v152>/t152/VIA · Python 3.13.16(/tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)
[GREEN] ③ Downloads 的 VRN-2 套件夾都讀得到
[計] ④ 自動選模式 full · 上一輪收據 沒有 · 上一輪輸出冊 沒有(要整輪:先貼 $env:VRN2_MODE = 'full')
[計] ④ 模式 full:整輪(取套件 v0152 → 診斷 → 全部自測 → 跑啟動器 v0152 → 自動修 → 除錯報告 → 收尾頁 → 貼回包 · 桌機約 66 分鐘)
[GREEN] ⑤ VRN2_RoundAll_v0108.py SHA-256 58576a79c441 相符(GitHub claude/optimistic-goodall-yhalc5)→ <v152>/t152/home/Downloads/VRN2_RoundAll_v0108.py
[GREEN] ① 套件 · 套件就位 <v152>/t152/home/Downloads/VRN2_Closeout_v0152(SHA-256 ba3bbfd5d0ce · 11 檔逐檔相符) · 來源 GitHub claude/optimistic-goodall-yhalc5
[YELLOW] ② 擷取 Python(⑥e / ⑥f) · 沒有裝齊 yfinance / lxml / pandas / pyarrow / duckdb 的 Python(看過 via_tw_fetch 缺 yfinance,lxml,pandas,pyarrow,duckdb ; venv_vrn2 缺 yfinance,duckdb)
[YELLOW] ② 擷取 Python · VDF 版本界線(⑥e) · 沒有合 pandas>=2.2,<3 pyarrow>=17,<27 duckdb>=1.1,<3 yfinance>=0.2.54,<2 lxml>=5,<7 tzdata>=2024.1 的 Python:envs/via_tw_fetch(VDF 預設)(3.13.16):pandas>=2.2,<3 pyarrow>=17,<27 duckdb>=1.1,<3 yfinan
[GREEN] ③ 自測 · runtime 解壓 · 188 檔 逐檔相符
[GREEN] ③ 自測 · VRN_SystemManager_v0255.py · [PASS] v0255: idempotence gate per-file parallel waves (GREEN · NONDETERMINISTIC · lanes 1) with timing in the receipt; phase timers bound into the native flow; · 10 秒
[GREEN] ③ 自測 · ActivateVRN-2_v0152.py · PASS 10 段 · 1 秒
[計] ④ /tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python -X utf8 <v152>/t152/home/Downloads/VRN2_Closeout_v0152/ActivateVRN-2_v0152.py --source <v152>/t152/samples --no-ope
[RED] ④ 跑啟動器 ActivateVRN-2_v0152.py · rc 1 · 176 秒 · NEXT: [RED] VRN-2 v0152 · rc 1 · 跑了 1 輪 · <v152>/t152/VIA/VIA_Reports/vrn2/VRN2_Closeout_v0152.json
[計] ⑤ 自動修計畫:舊資料庫 1 份待決定 · 模式 yes · Workbench 重渲染(最新收據)
[GREEN] ⑤ 修 · 舊資料庫 1 份待決定 · 模式 yes · 資料整合 v0101 · APPLIED · 整合 1 份 → <v152>/t152/OneDrive/VRN2_out/VRN2/integrated · 原檔副本在 <v152>/t152/ · 原檔已複製到 <v152>/t152/tmp/VRN2_Integrate_20261030_093309\originals(整合成功才複製);原位置的舊資料未刪未搬,請自行處理。
[GREEN] ⑤ 修 · Workbench 重渲染(最新收據) · VRN2_Workbench v0102 · <v152>/t152/VIA/VIA_Reports/vrn2/VRN2_Workbench_latest.html
[GREEN] ⑥ ⑪ 驗證器版本 · VRN2_IndependentVerifier_v0114 · VRN2_IndependentVerify_20261030_093232.json
[YELLOW] ⑧ 收尾頁(HTML U/I) · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 9 項等 VCGC 決定 / 安裝 · VRN-2 0 · VCGC 9 · 人工 2 · 資料源 0 → <v152>/t152/VIA/VIA_Reports/vrn2/VRN2_CloseoutUI_latest.html
總表 · 綠 33 · 黃 14 · 紅 3 · 灰 10 · 198 秒
===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 9 項等 VCGC 決定 / 安裝
  [VCGC] 9 項
  [人工] 2 項
  下一步:VRN-2 側已結案 · 剩下是 VCGC 的決定 / 安裝(上面 [VCGC] 那幾項 · 例:MOPS 經 VIA 網路工具被 DENY)→ 交 VCGC,VRN-2 不繞道
[計] Handle-All 結束 · RoundAll 結束碼 1 · 199 秒(視窗不會關)
```

## 6. ③ 舊套件夾讀不到

| 項目 | 結果 |
|---|---|
| 偵測(uid 0 拿掉 CAP_DAC_OVERRIDE / CAP_DAC_READ_SEARCH · 模擬一般身分) | 讀不到 zip 的夾 + 列不出的夾 → 列出 2 個;讀得到的夾 / 名字不符的夾 → 不列 |
| 以系統管理員身分要跑的指令(只在 Windows · 答 y 才跑) | icacls '<夾>' /reset /T /C /Q(單引號路徑跳脫 · -EncodedCommand 往返一致 · 剖析 0 錯)· UAC 本身只在桌機 |

回合結束碼:`f_auto_full rc 0 · d_auto rc 0 · d_report rc 0 · d_bogus rc 0 · d_nogit rc 0 · d_tamper rc 0 · done-d · f_auto_verify rc 0 · f_report rc 0 · done-drive`

## 7. 沒做到 / 沒驗到(照實)

- Windows desktop run of Handle-All v0100 / RoundAll v0108 / package v0152: not yet (next paste-back); the Daiwa aspeed PDF is only on the desktop — v0114 is proven by its selftest case built from the desktop's FIN evidence lines and by the container regression (4905 rows unchanged · mutations still FAIL)
- Windows-only parts of Handle-All (Get-CimInstance process check, UAC Start-Process -Verb RunAs, icacls) are checked by parsing / encoding round-trip and by the capability-dropped detection test only
- MOPS DENY (VCGC) · MQ-1560 OCR 4 points / annual gaps 3 (human) · Apple not a TW stock / no daily data before the report date (data source): not changed
- the container's VCGC items (missing accelerator packages, fetch Python outside VDF bounds) are container-only; the desktop has them
