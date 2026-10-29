# VRN-2 v0151 + VRN2_RoundAll_v0104 容器實測紀錄(2026-10-29 · 收尾輪)

操作員 2026-10-29「解決剩餘系統問題 HTML U/I CLOSE OUT」(貼回的是桌機 19:00 跑 VRN2_RoundAll_v0102 的主控台 · v0150 已處理的不重做)→ v0151(見發行清單 `fixes` · `not_fixed_here`)。

## 0. 桌機剩下的問題在容器重現 / 驗證

| 項目 | 結果 |
|---|---|
| ⑪ BADITEM · 沙盒 4,378 筆原樣(v0105 核心 vs v0113) | 0) 原樣 4378 筆 · core {'ALIGNED': 4378} · v0113 {'ALIGNED': 4378} · 判決不同 0 |
| ⑪ BADITEM · 變造科目名 60 筆 | A) 變造科目名 60 筆 · core {'BADITEM': 60} · v0113 {'BADITEM': 60} · v0113 註記「第二種讀法也沒有」60 |
| ⑪ BADITEM · 模擬桌機字元框把科目列讀壞 60 筆 | B) 字元框讀法把科目列讀壞 60 筆(桌機的樣子)· core {'BADITEM': 59, 'PRESENT': 1} · v0113 {'PRESENT': 60} · core BADITEM 59 → v0113 回到 PRESENT / ALIGNED 59 |
| ⑪ 整支跑(平行子行程)v0112 vs v0113 | 整支跑(平行子行程 · 沙盒 14 份 · 年度 4905 筆)VRN2_IndependentVerifier_v0112 {'ALIGNED': 4378, 'TRANSALIGNED': 75, 'SUBALIGNED': 452} · VRN2_IndependentVerifier_v0113 {'ALIGNED': 4378, 'TRANSALIGNED': 75, 'SUBALIGNED': 452} / 年度數據逐筆判決相同: True / basic 逐檔逐欄判決相同(只差平行完成順序): True / summary 逐檔逐欄判決相同(只差平行完成順序): True |
| 收尾頁 · 用桌機 19:00 那輪 39 列結果試算 | rows 39 state BLOCKED VRN-2 側沒有待修 · 3 項等 VCGC 決定 / 安裝 {'VCGC': 3, '人工': 8, '資料源': 4} |
| 收尾頁 · chromium(桌面 1366 / 深色 / 手機 390 · 篩選 · 搜尋) | desk scrollWidth 1366 VCGC rows 3 VCGC+MS-8358 0 errors [] / dark scrollWidth 1366 VCGC rows 3 VCGC+MS-8358 0 errors [] / phone scrollWidth 390 VCGC rows 3 VCGC+MS-8358 0 errors [] |
| 收尾頁 · 端到端產生的那一頁(chromium) | (沒有) |
| 端到端:pwsh 一行指令取 RoundAll v0104 | [VRN-2] PowerShell 7.4.6 · 從 GitHub 讀 VRN2_RoundAll_v0104.py(核對 SHA-256 後執行) · [GREEN] VRN2_RoundAll_v0104.py SHA-256 8333c1719127 相符 |
| 端到端:⑧ 收尾頁 | (沒有) |

## 1. 自測

| 檔 | 結果 |
|---|---|
| VRN2_RoundAll_v0104 | [PASS] VRN2_RoundAll v0104 --selftest · 29 項 · 不過 0 |
| VRN2_IndependentVerifier_v0113(VIA 樹內 · 含 v0105 30/30 · v0110 ~ v0112) | [PASS] v0113: BADITEM read a second way — item on the page (whole · wrapped · words in order) keeps PRESENT / ALIGNED; fabricated / renamed item stays BADITEM with the closest source line; FAIL keeps FAIL with the item's |
| ActivateVRN-2_v0151(建置夾) | [PASS] v0151: runtime's newest IndependentVerifier = v0113 (BADITEM read a second way before 'item not on this page' · structural copy, its own --shard) · v0112 kept |
| ActivateVRN-2_v0151(套件夾複本 · 不靠 ../new) | [PASS] v0151: runtime's newest IndependentVerifier = v0113 (BADITEM read a second way before 'item not on this page' · structural copy, its own --shard) · v0112 kept |

## 2. PowerShell 雜湊鏈(pwsh 7.4.6)

```
Run-VRN2-v0151.ps1 parse errors: 0
boot151.ps1 parse errors: 0
Run-VRN1-VRN2-v0112.ps1 parse errors: 0
boot_pair112.ps1 parse errors: 0
round.ps1 parse errors: 0
vrn2 one-click v0151: code sha = boot H → True (cce2693f42fc)
one-liner decodes to boot → True
package zip sha = \680d47e7009f78d75f80a1ab8469842aa80ce7e7fa0055e0f9ad2ee271165ceb → True
operator v0112: code sha = boot H → True (17f825cd410f)
operator H2 = vrn2 one-click v0151 code sha → True
operator banner says v0112 → True
localround v0101 H_OP = operator v0112 code sha → True
localround H_CS = chainship md v0101 code sha → True
chainship md WANT = tool v0101 sha → True
boot_roundall.ps1 parse errors: 0
roundall md has pwsh + powershell one-liners → True
roundall one-liner (pwsh) decodes to boot_roundall → True
roundall one-liner (powershell) decodes to boot_roundall → True
oneline_roundall_pwsh.txt = md pwsh line → True
roundall py sha (LF-normalised) = boot $H → True (8333c1719127)
roundall pinned package sha = zip sha → True
roundall CRLF checkout (git autocrlf) still verifies → True
```

## 3. 端到端:一個指令(pwsh -EncodedCommand)在仿桌機沙盒取 RoundAll v0104 跑全流程(殼有 VIA_ROOT · envs 有退役環境 + 沒裝套件的 via_tw_fetch · 套件從假 GitHub 分支取 · 19 份真實樣本)

端到端(pwsh 一行指令取 RoundAll v0104 跑全流程)推送時還在跑 · 跑完後下一個 commit 補進本紀錄

```
[GREEN] VRN2_RoundAll_v0104.py SHA-256 8333c1719127 相符 → /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v151/t151/home/Downloads/VRN2_RoundAll_v0104.py · 用 /tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/s
[GREEN] ⓪ VIA 根 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v151/t151/VIA
[GREEN] ① 套件 · 套件就位 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v151/t151/home/Downloads/VRN2_Closeout_v0151(SHA-256 680d47e7009f · 11 檔逐檔相符) · 來源 GitHub claude/optimistic-goodall-yhalc5
[GREEN] ② VRN-2 Python · /tmp/claude-0/-home-user-movies-dataset/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/venv_vrn2/bin/python(--python · 3.13.16)
[GREEN] ② VRN-2 套件 · 必裝 全在 · 選裝缺 duckdb, rapidocr_onnxruntime
[YELLOW] ② 擷取 Python(⑥e / ⑥f) · 沒有裝齊 yfinance / lxml / pandas / pyarrow / duckdb 的 Python(看過 via_tw_fetch 缺 yfinance,lxml,pandas,pyarrow,duckdb ; venv_vrn2 缺 yfinance,duckdb)
[YELLOW] ② 擷取 Python · VDF 版本界線(⑥e) · 沒有合 pandas>=2.2,<3 pyarrow>=17,<27 duckdb>=1.1,<3 yfinance>=0.2.54,<2 lxml>=5,<7 tzdata>=2024.1 的 Python:envs/via_tw_fetch(VDF 預設)(3.13.16):pandas>=2.2,<3 pyarrow>=17,<27 duckdb>=1.1,<3 yfinance>=0.2.54,<2 lxml>=5,<7 tzdat
[GREEN] ② 共用市場擷取工具 · VRN2_MarketFetch_v0112.py · VDF 引擎 VDF_TW_AllInOne_v039.py
[GREEN] ② 啟動器鎖 · 沒有其他啟動器在跑
[GREEN] ② 輸出檔案夾(長線 Parquet 庫) · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v151/t151/OneDrive/VRN2_out · 可寫
[GREEN] ② 來源夾 · /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v151/t151/samples · PDF 19 份
[GREEN] ② 磁碟 · VIA 根 · 可用 4.4 GB
[GREEN] ② 磁碟 · TEMP · 可用 4.4 GB
[GREEN] ② CPU · 忙碌 26%
[GREEN] ② git · /usr/bin/git
[GREEN] ③ 自測 · runtime 解壓 · 187 檔 逐檔相符
[GREEN] ③ 自測 · VRN2_Workbench_v0102.py · [PASS] VRN2_Workbench v0102 --selftest · 13 項 · 不過 0 · 0 秒
[GREEN] ③ 自測 · VRN2_HistoryAlign_v0100.py · [PASS] VRN2_HistoryAlign v0100 --selftest · 14 項 · 不過 0 · 1 秒
[GREEN] ③ 自測 · VRN2_HistoryAlign_v0102.py · [PASS] VRN2_HistoryAlign v0102 --selftest · 11 項 · 不過 0 · 1 秒
[GREEN] ③ 自測 · VRN2_DataIntegrate_v0100.py · [PASS] VRN2_DataIntegrate v0100 --selftest · 15 項 · 不過 0 · 1 秒
[GREEN] ③ 自測 · VRN2_DataIntegrate_v0101.py · [PASS] VRN2_DataIntegrate v0101 --selftest · 7 項 · 不過 0 · 1 秒
[GREEN] ③ 自測 · VRN2_UIAction_v0110.py · [PASS] VRN2_UIAction v0110 --selftest · 7 項 · 不過 0 · 1 秒
[GREEN] ③ 自測 · VRN2_SSOTSync_v0101.py · [PASS] VRN2_SSOTSync v0101 --selftest · 6 項 · 不過 0 · 0 秒
[GREEN] ③ 自測 · VRN2_OutputStore_v0101.py · [PASS] VRN2_OutputStore v0101 --selftest · 引擎 pyarrow · 8 項 · 不過 0 · 1 秒
[GREEN] ③ 自測 · VRN2_ConsensusJoin_v0102.py · [PASS] VRN2_ConsensusJoin v0102 --selftest · 6 項 · 不過 0 · 1 秒
[GREEN] ③ 自測 · VRN_SystemManager_v0255.py · [PASS] v0255: idempotence gate per-file parallel waves (GREEN · NONDETERMINISTIC · lanes 1) with timing in the receipt; phase timers bound into the native flow; · 11 秒
[GREEN] ③ 自測 · VRN2_VerbatimVerifier_v0105.py · [PASS] VRN2_VerbatimVerifier v0105 --selftest · 5 項 · 不過 0 · 0 秒
[GREEN] ③ 自測 · VRN2_MarketFetchRun_v0100.py · [PASS] VRN2_MarketFetchRun v0100 --selftest · 9 項 · 不過 0 · 2 秒
[GREEN] ③ 自測 · ActivateVRN-2_v0151.py · PASS 9 段 · 1 秒
```

## 4. 只修回合(`--skip-package --skip-selftest --skip-run`,先放一份合成的市場資料)

只修回合推送時還沒跑 · 跑完後補

```
```

| 項目 | 值 |
|---|---|
| 收尾頁(修後)| {"state": null, "state_label": null, "state_text": null, "vrn2_closed": null, "per_owner": null, "counts": null, "items": []} |
| 長線庫(修後)| {"lamp": null, "store_engine": null, "totals": null} |
| 收尾收據的 roundall 欄 | null |
| 貼回包 | {"name": null, "members": 0, "has": []} |

## 5. 一鍵 v0151 使用者情境(pwsh · 假 GitHub 分支 → 跑 → 再貼 → 竄改)

| 項目 | 值 |
|---|---|
| rc | first rc 1 · again rc 1 |
| first | [GREEN] ③ 套件 v0151 就位(SHA-256 680d47e7009f · 套件內 11 檔逐檔核對相符 · 來源 GitHub claude/optimistic-goodall-yhalc5)→ /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v151/t151oc/Download |
| again | [GREEN] ③ 本機已是 v0151 套件(SHA-256 680d47e7009f · 套件夾 12 檔與已驗證的 zip 逐檔相符)· /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v151/t151oc/Downloads/VRN2_Closeout_v0151 |
| tamper | [GREEN] ③ 舊套件夾已改名備份 → /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v151/t151oc/Downloads/VRN2_Closeout_v0151_20261029_145720.bak |
| closeout | [RED] ⑧b 收尾收據 v0151 · rc 1 · 跑了 1 輪(idempotence GREEN)· 四點原文核對 REVIEW_OCR {'PASS': 52, 'OCR_PENDING': 4} · 輸出缺項 1 |
| roundall_hint | [GRAY] 更完整的除錯 / 自動修 / 貼回包:python VRN2_RoundAll_v0104.py --skip-run(見 vrn2_release_v0151/VRN2_RoundAll_v0104.md) |

## 6. 沒做到 / 沒驗到(照實)

- Windows desktop run of v0151 / RoundAll v0104: not yet (next paste-back)
- BADITEM 19 on the desktop: the real MS-3665 / MS-8358 / MS-8210 / Daiwa aspeed PDFs are only on the desktop (the container's same-named files are synthetic samples); v0113 is proven on the 14 real sandbox PDFs by garbling the item's row in the character-box cache only (59 / 59 back to PRESENT) and by fabricated items (60 / 60 stay BADITEM)
- close-out owner rules are proven on the desktop 19:00 console rows and on the sandbox run; a step name the rules do not know is counted as VRN-2 (never as closed)
- MOPS DENY: VIA locked network tool compliance; not changed (VCGC decision)
- OCR_PENDING 4 (MQ-1560 image page) / annual gaps 3: human check, not automatable without the source
- Windows-only paths (os.startfile opening the close-out page, winreg vrn2:// lookup) are exercised by code review and the posix equivalents only
