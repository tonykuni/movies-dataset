# VRN-2 v0145 容器實測紀錄(2026-10-29)

起因:桌機 2026-10-29 08:14 用 v0144 跑本地實測一輪(52 份 · 2422 秒):前後端已連結、⑬ 走 duckdb 正式路徑、⑤b 綠,但 ⑦ 1201 秒裡約 1050 秒管理器沒有輸出;操作員問「IS IT THE FIRST TIME TO LAUNCH SYSTEM OR ACCELERATORS DIDN'T WORK」。

## 0. 桌機貼回判讀(v0144 · 08:14)

| 項 | 結果 |
|---|---|
| 前後端同步 | ⑥c vrn2:// → VRN2_UIAction_v0108 read back equal · ⑤b 前後端已連結 GREEN · ⑫b input block GREEN · 驗證過的輸出 written back (fingerprint 9888cecc1a7f291f) · Workbench v0101 GREEN opened · ⑬ duckdb GREEN 52 files · ⑤b SSOT-ID GREEN pending 371 |
| 紅燈 | ⑧b closeout rc 1 ← 四點原文核對 FAIL 1 (3014TT-20231005 POINT_3 · second reader did not reproduce the complete source excerpt) · 輸出缺項 3 份年度數據 (Daiwa-6278 · 欣銓 3264 · 華南 6143) |
| 時間 | 總 2422 秒 · 啟動器 2401 · ⑦ 1201(無輸出 ~1050 (heartbeat 距上次輸出 1068 秒 before the manager's [計] lines))· ⑪ 691 · ④ 92 |
| 快取 / 加速器 | 擷取沿用 52/52 · 驗收沿用 51/52 · VeritasCeleritas v1141 loaded · PS accelerator bound · accelfix 0 missing · 6-way parallel segment 55 s vs 177 s serial |
| 判讀 | not a first launch; accelerators worked; the silent 1050 s is consistent with the v0243 idempotence gate: 3 兆豐 PDFs × 2 waves in ONE single-lane subprocess per wave, no extraction cache, serial — main extraction itself was all cache hits |

## 1. 本輪改了什麼

| 元件 | 版本 | 內容 |
|---|---|---|
| 管理器 | VRN_SystemManager v0255(薄尾 · 釘名前版 v0243;v0244 ~ v0254 是桌機線的號)| 冪等閘契約不變,每波一份一個單路子行程並行(預設 3 路 · `VRN2_IDEM_LANES`)· R1 跑完才 R2 · 30 秒心跳 · R1 / R2 / 每份秒數進 `IDEMPOTENCE_latest.json.timing` · 階段計時(擷取迴圈 · 驗收 + 摘要 · 輸出冊 · U/I 輸出冊頁 · 調節輪 · 冪等閘)即時印 + `[計] 階段耗時` 一行 + `VRN2_Phase_Timing_latest.json` · completion.manager = v0255 |
| 啟動器 | ActivateVRN-2 v0145 | 改指管理器 v0255 · 收據 `VRN2_Closeout_v0145.json` · runtime v0145 = v0144 的 166 成員 + v0255;v0144 的 ⑤b / ⑬ / 處理器 v0108 / Workbench v0101 與 v0143 的閘 / 上限 / ⑫b 照舊 |
| 一鍵 | VRN-2 一鍵 v0145 · 操作員一鍵 v0106 · 本地實測一輪 v0100 改指 | ⑤ 摘要多印階段耗時 · ⑧b 收據 v0145 · ④ 貼回包改收 v0145 收據 + 階段計時,不再把前版收據與鎖檔算缺 |

## 2. 自測與雜湊鏈

| 項 | 結果 |
|---|---|
| `ActivateVRN-2_v0145 --selftest` | [PASS] v0145: manager v0255 is the active manager (parallel idempotence gate · phase timing) · receipt v0145 |
| `VRN_SystemManager_v0255 --selftest` | [PASS] v0255: idempotence gate per-file parallel waves (GREEN · NONDETERMINISTIC · lanes 1) with timing in the receipt; phase timers bound into the native flow; success register names v0255; v0243 code reached through PRIOR |
| pwsh 雜湊鏈 | Run-VRN2-v0145.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | boot145.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | Run-VRN1-VRN2-v0106.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | boot_pair106.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | cs101.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | round.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | vrn2 one-click v0145: code sha = boot H → True (c834b06e8702) |
| pwsh 雜湊鏈 | one-liner decodes to boot → True |
| pwsh 雜湊鏈 | package zip sha = \8aa7efe6e50b227b5f65f8d2378e46152ce578c3dce0c50b175e1d4dc92211e5 → True |
| pwsh 雜湊鏈 | operator v0106: code sha = boot H → True (b625cfbc6a3d) |
| pwsh 雜湊鏈 | operator H2 = vrn2 one-click v0145 code sha → True |
| pwsh 雜湊鏈 | operator banner says v0106 → True |
| pwsh 雜湊鏈 | localround H_OP = operator v0106 code sha → True |
| pwsh 雜湊鏈 | localround H_CS = chainship md v0101 code sha → True |
| pwsh 雜湊鏈 | chainship md WANT = tool v0101 sha → True |

## 3. 沙盒全流程(套件 v0145 · 19 份真檔)

| 項 | 結果 |
|---|---|
| 收尾 rc | 1(③ 環境檢查 RED in the Linux sandbox only (accelerator deps not in venv; --no-install); same as v0142–v0144)|
| 非綠步驟 | [('③ 環境檢查與補裝', 'RED'), ('⑥c U/I 操作協定', 'GRAY'), ('⑨ 上船 GitHub', 'GRAY'), ('⑩ 整併封存', 'GRAY'), ('⑫a VRN-1 倉同步(借工具前 · 只 fast-forward)', 'GRAY'), ('⑫ PIVOT 資料庫(借用 VRN-1)', 'GRAY'), ('⑬ 輸出位置 · 增量庫(DuckDB)', 'YELLOW')] |
| 輪數 / 冪等 | [(1, 0, 'idempotence GREEN')] · GREEN · 鎖檔已移除 True |
| ⑧ 完成判定 | 完成 · 紅 0 黃 3 · **VRN-2 SystemManager v0255** |
| ⑦ 個股四項 | 14 份 · 全綠 14 · ⑦ 耗時 136 秒 |
| **冪等閘** | [計] 冪等閘 · GREEN · 重跑 3 份 ×2(同主跑的子行程路徑 · 每波 3 路並行),文字／表格／數值／期間／位置一致 · 耗時 8 秒(R1 4 · R2 4) · 詳細差異 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v145/t145 |
| 冪等閘 timing | R1 3.5 秒(3 路 · {'JP-2330 20250718.pdf': 2.0, 'GS-6415 20260517.pdf': 2.5, 'Daiwa-1319 20231011(20261006-122413).pdf': 3.5})· R2 4.0 秒 · 總 7.6 秒 |
| 冪等閘進度行 | [計] 冪等閘 · 開始 · 3 份 ×2(R1 → R2)· 每波 3 路並行 · 單路 · 不吃擷取快取 · Daiwa-1319 20231011(20261006-122413).pdf、GS-6415 20260517.pdf、JP-2330 20250718.pdf |
| 冪等閘進度行 | [計] 冪等閘 · R1 完成 · 耗時 4 秒 · Daiwa-1319 20231011(20261006-122413).pdf 4 · GS-6415 20260517.pdf 2 · JP-2330 20250718.pdf 2 |
| 冪等閘進度行 | [計] 冪等閘 · R2 完成 · 耗時 4 秒 |
| 冪等閘進度行 | [計] 冪等閘 · 開始 · 3 份 ×2(R1 → R2)· 每波 3 路並行 · 單路 · 不吃擷取快取 · Daiwa-1319 20231011(20261006-122413).pdf、GS-6415 20260517.pdf、JP-2330 20250718.pdf |
| 冪等閘進度行 | [計] 冪等閘 · R1 完成 · 耗時 4 秒 · Daiwa-1319 20231011(20261006-122413).pdf 4 · GS-6415 20260517.pdf 2 · JP-2330 20250718.pdf 2 |
| 冪等閘進度行 | [計] 冪等閘 · R2 完成 · 耗時 4 秒 |
| **階段耗時** | [計] 階段耗時(秒)· 擷取迴圈 p1loop 35 · 驗收 + 摘要 61 · 輸出冊 29 · U/I 輸出冊頁 0 · 冪等閘 8 · 調節輪 0 · 其他 1 · 總 133 · 收據 VRN2_Phase_Timing_latest.json |
| 階段行 | [計] 階段 · 擷取迴圈 p1loop · 完成 · 耗時 35 秒 |
| 階段行 | [計] 階段 · 驗收 + 摘要 · 完成 · 耗時 61 秒 |
| 階段行 | [計] 階段 · 輸出冊 · 完成 · 耗時 29 秒 |
| 階段行 | [計] 階段 · U/I 輸出冊頁 · 完成 · 耗時 0 秒 |
| 階段行 | [計] 階段 · 調節輪 · 完成 · 耗時 0 秒 |
| 階段行 | [計] 階段 · 擷取迴圈 p1loop · 完成 · 耗時 35 秒 |
| 階段行 | [計] 階段 · 驗收 + 摘要 · 完成 · 耗時 61 秒 |
| 階段行 | [計] 階段 · 輸出冊 · 完成 · 耗時 29 秒 |
| 階段行 | [計] 階段 · U/I 輸出冊頁 · 完成 · 耗時 0 秒 |
| 階段行 | [計] 階段 · 調節輪 · 完成 · 耗時 0 秒 |
| 四點原文核對 | {'PASS': 52, 'OCR_PENDING': 4} · 缺項 [{'book': '四點原文核對', 'reason': "REVIEW_OCR · {'PASS': 52, 'OCR_PENDING': 4}"}] |
| ⑪ 獨立驗證 | 基本資料 {'PASS': 193, 'OCR': 2} · 四點 {'PASS': 65, 'OCR': 5} · 年度 4905 筆 {'ALIGNED': 4378, 'TRANSALIGNED': 75, 'SUBALIGNED': 452} |
| 註冊核對 | [計] 註冊核對 · ⑤ 元件登記 GREEN · ⑥c U/I 操作協定 GRAY · ② 定位 VRN-2 程式夾 GREEN · 處理器 VRN2_UIAction_v0108.py · 全部登記成功 |
| ⑤b / ⑬ / Workbench | GREEN · YELLOW pyarrow 新檔 14 · Workbench GREEN |

擷取 / 驗收 / 驗證的數字與 v0142 ~ v0144 同一組(無退步);管理器換成 v0255 只改了冪等閘跑法與計時。

## 4. 一鍵 v0145 情境(pwsh · 假 GitHub 分支)

| 項 | 結果 |
|---|---|
| rc | first rc 1 · again rc 1 · tamper rc 1 · done(rc 1 = 沙盒 ③ 環境檢查 RED,與 §3 同)|
| 第一次(Downloads 沒套件 → 從分支取)| [GREEN] ③ 套件 v0145 就位(SHA-256 8aa7efe6e50b · 套件內 10 檔逐檔核對相符 · 來源 GitHub claude/optimistic-goodall-yhalc5)→ /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v145/t145oc/Download |
| 再貼一次 | [GREEN] ③ 本機已是 v0145 套件(SHA-256 8aa7efe6e50b · 套件夾 11 檔與已驗證的 zip 逐檔相符)· /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v145/t145oc/Downloads/VRN2_Closeout_v0145 |
| 竄改啟動器後再貼 | [YELLOW] ③ 本機套件夾有 1 個檔與已驗證的 zip 不同或不在(ActivateVRN-2_v0145.py)→ 不用它,從本機這份 zip 重新解壓 → [GREEN] ③ 舊套件夾已改名備份 → /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v145/t145oc/Downloads/VRN |
| ⑧b | [RED] ⑧b 收尾收據 v0145 · rc 1 · 跑了 1 輪(idempotence GREEN)· 四點原文核對 REVIEW_OCR {'PASS': 52, 'OCR_PENDING': 4} · 輸出缺項 1 |
| ⑤ 階段耗時行 | [GRAY] 階段耗時(秒 · 管理器 VRN-2 SystemManager v0255)· 擷取迴圈 p1loop 36 · 驗收 + 摘要 62 · 輸出冊 29 · U/I 輸出冊頁 0 · 冪等閘 8 · 調節輪 0 · 其他 0 · 總 136 |
| 冪等閘 | [計] 冪等閘 · GREEN · 重跑 3 份 ×2(同主跑的子行程路徑 · 每波 3 路並行),文字／表格／數值／期間／位置一致 · 耗時 8 秒(R1 4 · R2 4) · 詳細差異 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v145/t145 |
| 註冊核對 | [計] 註冊核對 · ⑤ 元件登記 GREEN · ⑥c U/I 操作協定 GRAY · ② 定位 VRN-2 程式夾 GREEN · 處理器 VRN2_UIAction_v0108.py · 全部登記成功 |

## 5. 沒有宣稱的

- Windows desktop run of v0145: not yet (next paste-back); the 1050 s attribution to the idempotence gate is an inference from the console (the R*.log evidence is deleted on GREEN by v0243); v0255 records R1/R2 timing so the next paste-back proves or refutes it
- ⑪ independent verifier 691 s and ④ accelfix double pass 92 s: not changed this round
- 3014TT POINT_3 FAIL and the 3 missing annual-data books: need the paste-back zip (VRN2_PasteBack_20261029_081428.zip) — not in the container samples
- OneDrive-synced repository folder slows file I/O: not measured; the phase timing will show it
- Items carried from v0143 / v0144: PasteBack 013350 transcript, v0248 / v0253 location on the desktop, VCGC side of the SSOT-ID protocol
