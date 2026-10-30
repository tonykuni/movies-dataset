# VRN-2 v0153 + 管理器 v0257 + VRN2_RoundAll_v0109 + VRN2_HandleAll_v0101 容器實測紀錄(2026-10-30)

桌機 18:34 貼回 Handle-All v0100(RoundAll v0108 verify):收尾 BLOCKED · VRN-2 0,但驗證器 DUPKEY 45(6933 AMAX 第 8 頁並排兩張表 37 · 凱基 2891 第 5 頁沒有列號 8)→ v0153(見發行清單 `fixes` · `not_fixed_here`)。

## 1. 自測

| 檔 | 結果 |
|---|---|
| VRN_SystemManager_v0257(VIA 樹內 · PRIOR v0255 → v0243 …) | [PASS] v0257: one row, one item — side-by-side right-table values renamed to their own row label or moved to Rejected · row-less duplicates rejected · repeated item names on different rows untouched · v0255 gate selftest |
| VRN2_RoundAll_v0109 | [PASS] VRN2_RoundAll v0109 --selftest · 46 項 · 不過 0 |
| ActivateVRN-2_v0153(套件夾複本 · 不靠 ../new) | [PASS] v0153: manager v0257 is the active manager (one row, one item: side-by-side right-table values renamed to their own row label or moved to Rejected · row-less duplicates rejected) · v0255 kept as PRIOR |

## 2. 管理器 v0257 拿桌機 18:34 的年度數據冊重放(沒有擷取快取 → 留最左邊、其他剔除)· 容器 14 份真檔(有擷取快取)

```
== 桌機 18:34(52 份) · 年度數據 11513 → 留 11468 · 改名 0 · 剔除 45 [('6933_AMAX-KY_個股介紹報告.pd', 37), ('凱基投顧_2891 中信金_施志鴻_2026', 8)]
    凱基投顧_2891 中信金_施志 p5 「現金及約當現金」FY25 沒有列號 → 剔除 2 筆
    凱基投顧_2891 中信金_施志 p5 「國內債券」FY25 沒有列號 → 剔除 2 筆
    凱基投顧_2891 中信金_施志 p5 「國外債券」FY25 沒有列號 → 剔除 2 筆
    凱基投顧_2891 中信金_施志 p5 「保單貸款」FY25 沒有列號 → 剔除 2 筆
    6933_AMAX-KY_個股介 p8 P8·F·02·TB 第 4 列「流動資產」→ 改名 0 · 剔除 3
    6933_AMAX-KY_個股介 p8 P8·F·02·TB 第 5 列「不動產、廠房及設備」→ 改名 0 · 剔除 3
    剔除例: 流動資產 2020 3,411,492 · 並排的另一張表:同一列「流動資產」2020 有 2 個不同的值 · 留最左邊的 1,331,956 · 這個值在這一列找不到它自己的科目名 → 不掛在「流動資產」名下
    剔除例: 流動資產 2021 5,212,499 · 並排的另一張表:同一列「流動資產」2021 有 2 個不同的值 · 留最左邊的 2,155,768 · 這個值在這一列找不到它自己的科目名 → 不掛在「流動資產」名下
    剔除例: 流動資產 2022 6,748,900 · 並排的另一張表:同一列「流動資產」2022 有 2 個不同的值 · 留最左邊的 2,112,693 · 這個值在這一列找不到它自己的科目名 → 不掛在「流動資產」名下
== 容器 t152(14 份 · 有擷取快取) · 年度數據 4905 → 留 4905 · 改名 0 · 剔除 0 []
```

## 3. RoundAll v0109 的收尾規則重算桌機 18:34 那份收尾頁(只讀)

```
18:34 原判: BLOCKED {'人工': 5, 'VCGC': 3, '資料源': 2}
v0109 規則 · 同一份結果(DUPKEY 45 還在) → OPEN · VRN-2 還有 1 項要修 · {'VRN-2': 1, 'VCGC': 1, '人工': 2, '資料源': 2} · 列 14 → 10
   [VRN-2] ⑪b 重跑獨立驗證  (+⑥ 步驟 ⑪ 獨立驗證(背景 · 只讀))
   [VCGC] ⑥ 步驟 ⑥e 市場擷取(TWSE / TPEX / Yahoo · 借共用 Market  (+⑥ ⑥e 擷取錯誤(last_error.txt、⑥ ⑥e MOPS 財報被拒(VIA 網路工具 )
   [人工] ⑥ 四點原文核對  (+⑥ 輸出缺項)
   [人工] ⑥ 完成判定 · 輸出冊(基本資料 / 年度數據 / 一標題四重點)
   [資料源] ⑥ Combined 冊
   [資料源] ⑥ 市場資料
v0109 規則 · 整輪重跑後(管理器 v0257 → DUPKEY 0 的預期) → BLOCKED · VRN-2 側沒有待修 · 1 項等 VCGC 決定 / 安裝 · {'人工': 3, 'VCGC': 1, '資料源': 2} · 列 14 → 10
   [人工] ⑪b 重跑獨立驗證  (+⑥ 步驟 ⑪ 獨立驗證(背景 · 只讀))
   [VCGC] ⑥ 步驟 ⑥e 市場擷取(TWSE / TPEX / Yahoo · 借共用 Market  (+⑥ ⑥e 擷取錯誤(last_error.txt、⑥ ⑥e MOPS 財報被拒(VIA 網路工具 )
   [人工] ⑥ 四點原文核對  (+⑥ 輸出缺項)
   [人工] ⑥ 完成判定 · 輸出冊(基本資料 / 年度數據 / 一標題四重點)
   [資料源] ⑥ Combined 冊
   [資料源] ⑥ 市場資料
```

## 4. PowerShell 雜湊鏈與剖析(pwsh 7.4.6)

```
[PASS] 套件 zip = RoundAll 釘的 = 發行清單 · 4beed2bc7a84
[PASS] RoundAll 檔 = Handle-All 一行 / 可讀版 / PS7 一行 / 解開版的 $H = 發行清單 · 716bfe2bd911
[PASS] HandleAll md:第一段 = 一行檔 · 第二段 = 可讀版 · 一行 SHA-256 標在 md 與發行清單 · c4374130f9f6
[PASS] RoundAll md:PS7 一行 = 檔 · 兩行 -EncodedCommand 解開 = 解開版 · 都在 8191 字元內
[PASS] Handle-All / PS7 一行沒有 exit(視窗不關)· 沒有 # 註解 · 8695 字元
[PASS] PowerShell 剖析(pwsh 7.4.6)0 錯:handleall_line.txt 1231 詞 · handleall_src.ps1 1243 詞 · oneline_roundall_ps7.txt 378 詞 · boot_roundall.ps1 501 詞
[PASS] Handle-All 一行版 = 可讀版(去掉換行 / 分號後詞序列相同)
```

## 5. 桌機情境:貼 Handle-All v0101(複製 v0151 沙盒 · 只有 v0151 收據 + 上一輪輸出)→ auto(full)→ auto(verify)→ report → 竄改

| 項目 | 結果 |
|---|---|
| auto → 模式(只有 v0151 收據) | [計] ④ 自動選模式 full · 上一輪收據 VRN2_Closeout_v0151.json · 上一輪輸出冊 有(上一輪輸出冊是啟動器 v0153 以前做的 · 管理器 v0257 要重做輸出冊)(只重驗:先貼 $env:VRN2_MODE = 'verify') |
| ⑤ 取 RoundAll | [GREEN] ⑤ VRN2_RoundAll_v0109.py SHA-256 716bfe2bd911 相符(GitHub claude/optimistic-goodall-yhalc5)→ <v153>/t153d/home/Downloads/VRN2_RoundAll_v0109.py |
| ① 套件 | [GREEN] ① 套件 · 套件就位 <v153>/t153d/home/Downloads/VRN2_Closeout_v0153(SHA-256 4beed2bc7a84 · 11 檔逐檔相符) · 來源 GitHub claude/optimistic-goodall-yhalc5 |
| ③ 自測 | 14 支 · 綠 14 · 紅 / 黃 0 · 管理器 v0257:[GREEN] ③ 自測 · VRN_SystemManager_v0257.py · [PASS] v0257: one row, one item — side-by-side right-table values renamed to |
| ④ 啟動器 v0153 |   [RED] ④ 跑啟動器 ActivateVRN-2_v0153.py · rc 1 · 124 秒 |
| 管理器 |   [計] 成功模組登記 · VRN-2 SystemManager VRN_SystemManager_v0257.py · 擷取引擎 ENG397 VRN_ENG397_P1Segment_v0127.py · 摘要器 ENG062 VRN_ENG062_SummarizerV1_v0117.py · VRN-2 設定冊 VRN2_SSOT_v0103.json · OCR 橋 VRN2_OC |
| v0257 一列一科目(容器 14 份 · 應該沒有撞鍵) | 沒有印(0 列撞鍵 · 輸出冊不重寫) |
| 年度數據冊 v0255 做的 vs v0257 做的 | 4905 列 → 4905 列 · 逐列(檔 · 頁 · 表 · 列 · 段落 · 科目 · 期間 · 子欄 · 值)完全相同 |
| ⑥ ⑪ 驗證器版本 | [GREEN] ⑥ ⑪ 驗證器版本 · VRN2_IndependentVerifier_v0114 · VRN2_IndependentVerify_20261030_111937.json |
| 總表(full) | 總表 · 綠 35 · 黃 12 · 紅 3 · 灰 8 · 145 秒 |
| 再貼(auto → 模式 · 收據 v0153) | [計] ④ 自動選模式 verify · 上一輪收據 VRN2_Closeout_v0153.json · 上一輪輸出冊 有(只重驗:先貼 $env:VRN2_MODE = 'verify') |
| 再貼 ⑪b | [GREEN] ⑪b 重跑獨立驗證 · VRN2_IndependentVerifier_v0114 · 錯值 0 · 基本資料 14 份 · 欄位檢查 {'PASS': 193, 'OCR': 2} · 一標題四重點 14 份 · 欄位檢查 {'PASS': 65, 'OCR': 5} · 年度數據 4905 筆 · {'ALIGNED': 4378, 'TRANSALIGNED': 75, ' |
| report | [計] Handle-All 結束 · RoundAll 結束碼 1 · 1 秒(視窗不會關) |
| 收尾頁(最後) | BLOCKED · VRN-2 側沒有待修 · 5 項等 VCGC 決定 / 安裝 · {"VCGC": 5, "人工": 1} · 列 10(其中合併 1 列) |
| v0153 收據 roundall.fixed | ['⑪'] |
| 貼回包帶收據 | ['vrn2/VRN2_Closeout_v0153.json', 'vrn2/VRN2_Closeout_v0153.before_roundall.json', 'vrn2/VRN2_CloseoutUI_latest.html', 'vrn2/VRN2_CloseoutUI_latest.json'] |
| RoundAll 被竄改 | [RED] ⑤ VRN2_RoundAll_v0109.py SHA-256 不對(91220570b053decb78db734c8e0788cb2cdf3ea163beca4c3f32df6309a14ce9)· 不執行 · 存檔:沒有(不執行) |
| 容器才有的 VCGC 項 | ③ 環境檢查缺 7(accelerator / curl_cffi / cv2 / duckdb / lz4 / pyvips / watchdog)· ⑥e 擷取 Python 沒有合 VDF 界線的 —— 容器沒裝,桌機有 |

```
[GREEN] ① 工具 · git 倉 <v153>/t153d/VIA · Python 3.13.16(/tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)
[GREEN] ③ Downloads 的 VRN-2 套件夾都讀得到
[計] ④ 自動選模式 full · 上一輪收據 VRN2_Closeout_v0151.json · 上一輪輸出冊 有(上一輪輸出冊是啟動器 v0153 以前做的 · 管理器 v0257 要重做輸出冊)(只重驗:先貼 $env:VRN2_MODE = 'verify')
[計] ④ 模式 full:整輪(取套件 v0153 → 診斷 → 全部自測 → 跑啟動器 v0153(管理器 v0257 重做輸出冊)→ 自動修 → 除錯報告 → 收尾頁 → 貼回包 · 桌機約 66 分鐘)
[GREEN] ⑤ VRN2_RoundAll_v0109.py SHA-256 716bfe2bd911 相符(GitHub claude/optimistic-goodall-yhalc5)→ <v153>/t153d/home/Downloads/VRN2_RoundAll_v0109.py
[GREEN] ① 套件 · 套件就位 <v153>/t153d/home/Downloads/VRN2_Closeout_v0153(SHA-256 4beed2bc7a84 · 11 檔逐檔相符) · 來源 GitHub claude/optimistic-goodall-yhalc5
[YELLOW] ② 擷取 Python(⑥e / ⑥f) · 沒有裝齊 yfinance / lxml / pandas / pyarrow / duckdb 的 Python(看過 via_tw_fetch 缺 yfinance,lxml,pandas,pyarrow,duckdb ; venv_vrn2 缺 yfinance,duckdb)
[YELLOW] ② 擷取 Python · VDF 版本界線(⑥e) · 沒有合 pandas>=2.2,<3 pyarrow>=17,<27 duckdb>=1.1,<3 yfinance>=0.2.54,<2 lxml>=5,<7 tzdata>=2024.1 的 Python:envs/via_tw_fetch(VDF 預設)(3.13.16):pandas>=2.2,<3 pyarrow>=17,<27 duckdb>=1.1,<3 yfinan
[GREEN] ③ 自測 · runtime 解壓 · 189 檔 逐檔相符
[GREEN] ③ 自測 · VRN_SystemManager_v0257.py · [PASS] v0257: one row, one item — side-by-side right-table values renamed to their own row label or moved to Rejected · row-less duplicates rejected · repeated  · 10 秒
[GREEN] ③ 自測 · ActivateVRN-2_v0153.py · PASS 11 段 · 1 秒
[計] ④ /tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python -X utf8 <v153>/t153d/home/Downloads/VRN2_Closeout_v0153/ActivateVRN-2_v0153.py --source <v153>/t153d/samples --no-o
[RED] ④ 跑啟動器 ActivateVRN-2_v0153.py · rc 1 · 124 秒 · NEXT: [RED] VRN-2 v0153 · rc 1 · 跑了 1 輪 · <v153>/t153d/VIA/VIA_Reports/vrn2/VRN2_Closeout_v0153.json
[GREEN] ⑤ 自動修 · 沒有要修的(能自動修的都已綠 / 灰)
[GREEN] ⑥ ⑪ 驗證器版本 · VRN2_IndependentVerifier_v0114 · VRN2_IndependentVerify_20261030_111937.json
[YELLOW] ⑧ 收尾頁(HTML U/I) · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 7 項等 VCGC 決定 / 安裝 · VRN-2 0 · VCGC 7 · 人工 1 · 資料源 0 → <v153>/t153d/VIA/VIA_Reports/vrn2/VRN2_CloseoutUI_latest.html
總表 · 綠 35 · 黃 12 · 紅 3 · 灰 8 · 145 秒
===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 7 項等 VCGC 決定 / 安裝
  [VCGC] 7 項
  [人工] 1 項
  下一步:VRN-2 側已結案 · 剩下是 VCGC 的決定 / 安裝(上面 [VCGC] 那幾項 · 例:MOPS 經 VIA 網路工具被 DENY)→ 交 VCGC,VRN-2 不繞道
[計] Handle-All 結束 · RoundAll 結束碼 1 · 146 秒(視窗不會關)
```

```
[GREEN] ① 工具 · git 倉 <v153>/t153d/VIA · Python 3.13.16(/tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)
[GREEN] ③ Downloads 的 VRN-2 套件夾都讀得到
[計] ④ 自動選模式 verify · 上一輪收據 VRN2_Closeout_v0153.json · 上一輪輸出冊 有(只重驗:先貼 $env:VRN2_MODE = 'verify')
[計] ④ 模式 verify:只重跑 ⑪ 獨立驗證(套件 v0153 的 IndependentVerifier v0114 · 用上一輪的輸出冊)→ 除錯報告 → 收尾頁 → 貼回包(約 10 分鐘)
[GREEN] ⑤ VRN2_RoundAll_v0109.py SHA-256 716bfe2bd911 相符(GitHub claude/optimistic-goodall-yhalc5)→ <v153>/t153d/home/Downloads/VRN2_RoundAll_v0109.py
[GREEN] ① 套件 · 本機已是 VRN2_Closeout_v0153(SHA-256 4beed2bc7a84 · 11 檔逐檔相符)· <v153>/t153d/home/Downloads/VRN2_Closeout_v0153
[計] ⑪b VRN2_IndependentVerifier_v0114.py 重跑(/tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python)· 輸出冊 <v153>/t153d/VIA/VIA_Reports/vrn2/output · 原檔 <v153>/t153d/VIA/VIA_Repo
[GREEN] ⑪b 重跑獨立驗證 · VRN2_IndependentVerifier_v0114 · 錯值 0 · 基本資料 14 份 · 欄位檢查 {'PASS': 193, 'OCR': 2} · 一標題四重點 14 份 · 欄位檢查 {'PASS': 65, 'OCR': 5} · 年度數據 4905 筆 · {'ALIGNED': 4378, 'TRANSALIGNED': 75, 'SUBALIGNED': 452} · 報告 VRN2_In
[GREEN] ⑥ ⑪ 驗證器版本 · VRN2_IndependentVerifier_v0114 · VRN2_IndependentVerify_20261030_112009.json
[YELLOW] ⑧ 收尾頁(HTML U/I) · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 5 項等 VCGC 決定 / 安裝 · VRN-2 0 · VCGC 5 · 人工 1 · 資料源 0 → <v153>/t153d/VIA/VIA_Reports/vrn2/VRN2_CloseoutUI_latest.html
總表 · 綠 11 · 黃 10 · 紅 2 · 灰 8 · 25 秒
===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 5 項等 VCGC 決定 / 安裝
  [VCGC] 5 項
  [人工] 1 項
  下一步:VRN-2 側已結案 · 剩下是 VCGC 的決定 / 安裝(上面 [VCGC] 那幾項 · 例:MOPS 經 VIA 網路工具被 DENY)→ 交 VCGC,VRN-2 不繞道
[計] Handle-All 結束 · RoundAll 結束碼 1 · 25 秒(視窗不會關)
```

回合結束碼:`d_auto_full rc 0 · d_auto_verify rc 0 · d_report rc 0 · d_tamper rc 0 · done-drive`

## 6. 沒做到 / 沒驗到(照實)

- Windows desktop run of package v0153 / manager v0257 / RoundAll v0109 / Handle-All v0101: not yet (next paste-back); the 6933 AMAX and 凱基 2891 PDFs are only on the desktop — v0257 is proven by its selftest (side-by-side rows built like page 8 · fused label+value cell · row-less pairs) and by replaying the desktop's own annual book (exactly the 45 DUPKEY rows rejected); whether the desktop's extracted row also holds the right table's labels (rename instead of reject) shows only in the next run
- the close-out merge rules (one row per root cause) are proven on the desktop 18:34 rows; a new step name is not merged
- MOPS DENY (VCGC) · MQ-1560 OCR / EST 1 / annual gaps 3 (human) · Apple not a TW stock / 3706 · 6669 no adjusted close in the week before the report date (VDF daily windows PARTIAL · data source): not changed
- VDF_v0102_Redownload_4.zip (VDF's own system): read only — not installed, not changed, not committed (four systems independent)
- the container's VCGC items (missing accelerator packages, fetch Python outside VDF bounds) are container-only; the desktop has them
