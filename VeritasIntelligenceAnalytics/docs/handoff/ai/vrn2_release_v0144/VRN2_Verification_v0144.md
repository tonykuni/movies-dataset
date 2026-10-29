# VRN-2 v0144 容器實測紀錄(2026-10-29)

起因:操作員 2026-10-29 政策 —— 三系統獨立、SSOT / Regex / 同義字 / 政策由基層提出(ID 空白)→ VCGC 核號 → 子系統自動補填;VRN-2 快速收尾用 HTML U/I:輸出位置 Windows I/O(拖曳 / 對話框)或連接雲端 · 輸出 Parquet 增量擷取 · 增量擷取用 DuckDB 管理 · 全景式檢視。

## 1. 本輪改了什麼

| 元件 | 版本 | 內容 |
|---|---|---|
| 啟動器 | ActivateVRN-2 v0144(v0136 底座 · v0143 的閘 / 上限 / ⑫b 補放照舊)| ⑤b SSOT-ID 核號同步(⑤ 之後)· ⑬ 輸出位置 / 增量庫(收尾收據之後 · 沒選輸出夾 = 灰 · `VRN2_OUTPUT_DIR` 預設)· 註冊處理器 v0108 · Workbench v0101 · 收據 v0144 多 `ssot_sync` / `output_store` |
| VRN2_SSOTSync | v0100(runtime v0144 新成員)| `request`(登記冊尾版 → 請求冊 `contract/VRN2_NUMBER_REQUEST_latest.json`:ssot_id 空白 · proposed_no · vcgc_kind · 同義字 / 正則 / 來源 sha · 自撞)· `apply`(讀 `VCGC_NUMBER_GRANT_latest.json` 四處只讀合併 → 核發補填出新版登記冊 · 衝突待人判 · `contract/VRN2_NUMBER_STATE_latest.json`)· `sync` |
| VRN2_OutputStore | v0100(runtime v0144 新成員)| 鏡像四本冊 + Workbench + 收據到 `<輸出夾>/VRN2/latest`;DuckDB 增量庫 `vrn2_store.duckdb`(catalog 以 SHA-256 為鍵 · book_* 帶 run_id / file_sha · 只追加新檔)· Parquet 分區 `parquet/<冊>/run=<id>.parquet` + `catalog.parquet`(DuckDB COPY)· 沒 duckdb → pyarrow 備援(黃)· 設定冊 `VRN2_Output_Config.json` · 收據 `VRN2_OutputStore_latest.json` |
| VRN2_UIAction | v0108(v0104 留著;v0105 / v0107 是桌機線 publish 處理器的號)| `vrn2://pick?kind=outdir`(FolderBrowserDialog · 可新建)· `vrn2://outdir?reset=1` · `--set-outdir` · 舊版 U/I「輸出位置(window I/O)」區塊 · OneDrive / Google Drive / Dropbox 同步夾 = 雲端提示 |
| VRN2_Workbench | v0101(v0100 留著 · 字型資產包 v0100 不動)| 匯出分頁:輸出位置面板(選擇 / 取消 · 拖曳區 → 開對話框 · 庫收據表:引擎 / 新檔 / 已知 / 追加 / 累計 / parquet)· 交接分頁:SSOT-ID 協作表(核發 / 衝突 / 待核號)|
| 協定 | `docs/handoff/ai/VIA_SSOT_ID_Protocol_v0100.md` | 三系統共讀的契約:角色 · 請求冊 / 核發冊 JSON 格式 · 衝突規則 · VRN-2 落地位置;VCGC / VDF 側只寫契約,不代寫實作 |
| 一鍵 | VRN-2 一鍵 v0144 · 操作員一鍵 v0105 · 本地實測一輪 v0100 改指 | ⑤b 核對處理器 v0108 · ⑧b 收據 v0144 · 摘要多 ⑬ / ⑤b 兩行 |

## 2. 自測與雜湊鏈

| 項 | 結果 |
|---|---|
| `ActivateVRN-2_v0144 --selftest` | [PASS] v0144: ⑤b SSOT-ID sync (no register → GRAY · pending → GREEN + request) · ⑬ output store (unset → GRAY · VRN2_OUTPUT_DIR seeds config · incremental append · idempotent re-run) |
| `VRN2_SSOTSync_v0100 --selftest` | [計] VRN2_SSOTSync v0100 --selftest · OK 9 · FAIL 0 |
| `VRN2_OutputStore_v0100 --selftest` | [計] VRN2_OutputStore v0100 --selftest · OK 9 · FAIL 0 |
| `VRN2_UIAction_v0108 --selftest` | [計] VRN2_UIAction v0108 自測 14/14 · PASS |
| `VRN2_Workbench_v0101 --selftest` | [計] VRN2_Workbench v0101 --selftest · OK 18 · FAIL 0 |
| pwsh 雜湊鏈 | Run-VRN2-v0144.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | boot144.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | Run-VRN1-VRN2-v0105.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | boot_pair105.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | cs101.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | round.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | vrn2 one-click v0144: code sha = boot H → True (9adeab66d446) |
| pwsh 雜湊鏈 | one-liner decodes to boot → True |
| pwsh 雜湊鏈 | package zip sha = \41c49c5ed19a4f361a7ebaa4c961473f93762ae3de6928be64a673407a4fc284 → True |
| pwsh 雜湊鏈 | operator v0105: code sha = boot H → True (c1dfe6d2f676) |
| pwsh 雜湊鏈 | operator H2 = vrn2 one-click v0144 code sha → True |
| pwsh 雜湊鏈 | operator banner says v0105 → True |
| pwsh 雜湊鏈 | localround H_OP = operator v0105 code sha → True |
| pwsh 雜湊鏈 | localround H_CS = chainship md v0101 code sha → True |
| pwsh 雜湊鏈 | chainship md WANT = tool v0101 sha → True |

## 3. 沙盒全流程(套件 v0144 · 19 份真檔 · `VRN2_OUTPUT_DIR` 指向 OneDrive 式夾 · 容器 venv 沒 duckdb)

| 項 | 結果 |
|---|---|
| 收尾 rc | 1(③ 環境檢查 RED in the Linux sandbox only (accelerator deps not in venv; --no-install); same as v0142 / v0143)|
| 非綠步驟 | [('③ 環境檢查與補裝', 'RED'), ('⑥c U/I 操作協定', 'GRAY'), ('⑨ 上船 GitHub', 'GRAY'), ('⑩ 整併封存', 'GRAY'), ('⑫a VRN-1 倉同步(借工具前 · 只 fast-forward)', 'GRAY'), ('⑫ PIVOT 資料庫(借用 VRN-1)', 'GRAY'), ('⑬ 輸出位置 · 增量庫(DuckDB)', 'YELLOW')] |
| 單機閘 / 上限 / ⑫b | 結束後鎖檔已移除 True · {'VRN2_UI_REFRESH_WAIT': 600, 'VRN2_SILENT_MAX': 3600, 'VRN2_MANIFEST_WAIT': 900, 'VIA_VRN2_VERIFY_WAIT': 3600} · ui_block {'lamp': 'GREEN', 'how': '子行程', 'detail': '[鎖驗證] accelerator=EXACT · network=EXACT · 耗時 1 秒'} |
| 輪數 / 冪等 | [(1, 0, 'idempotence GREEN')] · GREEN |
| ⑧ 完成判定 | 完成 · 紅 0 黃 3 · VRN-2 SystemManager v0243 |
| ⑦ 個股四項 | 14 份 · 全綠 14 |
| 四點原文核對 | {'PASS': 52, 'OCR_PENDING': 4} · 缺項 [{'book': '四點原文核對', 'reason': "REVIEW_OCR · {'PASS': 52, 'OCR_PENDING': 4}"}] |
| ⑪ 獨立驗證 | 基本資料 {'PASS': 193, 'OCR': 2} · 四點 {'PASS': 65, 'OCR': 5} · 年度 4905 筆 {'ALIGNED': 4378, 'TRANSALIGNED': 75, 'SUBALIGNED': 452} |
| 註冊核對 | [計] 註冊核對 · ⑤ 元件登記 GREEN · ⑥c U/I 操作協定 GRAY · ② 定位 VRN-2 程式夾 GREEN · 處理器 VRN2_UIAction_v0108.py · 全部登記成功 |
| **⑤b SSOT-ID** | GREEN · 核發 0 · 衝突 0 · 待核號 371(SSOT 類 82 · 程式類 289)· 自撞 0 · 登記冊 VRN2_Component_Register_v0101.json · 核發冊 尚無(VCGC 還沒核發) · 請求冊 functional modules/VRN2/contract/VRN2_NUMBER_REQUEST_latest.json · counts {'ssot_like': 82, 'program': 289, 'self_conflicts': 0} · STATE 已寫 True |
| **⑬ 輸出位置 · 增量庫** | YELLOW · OneDrive 同步夾(本機寫入 · 由同步軟體上雲) · 引擎 pyarrow · 鏡像 17 · 新檔 14 / 已知 0 · 追加 {'BasicInfo': 14, 'FinancialData': 4905, 'Summary': 14, 'Rejected': 815} · 累計 {'BasicInfo': 14, 'FinancialData': 4905, 'Summary': 14, 'Rejected': 815} · parquet 5 · 沒有 duckdb 套件 → pyarrow 備援(功能同 · 沒有 SQL 查詢;桌機裝 duckdb 即走正式路徑) |
| Workbench v0101 | GREEN · 舊版 U/I 連結 True |

擷取 / 驗收 / 驗證的數字與 v0142 / v0143 同一組(無退步)。

## 4. DuckDB 正式路徑(venv_duck · 同一批輸出冊 · OutputStore CLI)

| 項 | 結果 |
|---|---|
| 環境 | venv_duck · python 3.13 · duckdb 1.5.6 (no pyarrow) |
| 第一次 sync | [計] VRN2_OutputStore v0100 · GREEN · 輸出夾 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v144/duck/out(本機夾(要上雲就選 OneDrive / Google Drive / Dropbox 的同步夾))· 鏡像 13 檔 · 增量庫 duckdb(/tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v144/duck/out/VRN2/vrn2_store.duckdb)· 本輪新檔 14 · 已知檔 0 · 追加列 BasicInfo 14 / FinancialData 4905 / Summary 14 / Rejected 815 · 累 |
| 第二次 sync(同檔再跑)| [計] VRN2_OutputStore v0100 · GREEN · 輸出夾 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v144/duck/out(本機夾(要上雲就選 OneDrive / Google Drive / Dropbox 的同步夾))· 鏡像 13 檔 · 增量庫 duckdb(/tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v144/duck/out/VRN2/vrn2_store.duckdb)· 本輪新檔 0 · 已知檔 14 · 追加列 BasicInfo 0 / FinancialData 0 / Summary 0 / Rejected 0 · 累計 Basic |
| SQL | `tables ['book_basicinfo', 'book_financialdata', 'book_rejected', 'book_summary', 'catalog']` |
| SQL | `catalog [(14, '20261029_000001', '20261029_000002', 28)]` |
| SQL | `BasicInfo [('20261029_000001', 14, 14)]` |
| SQL | `FinancialData [('20261029_000001', 4905, 11)]` |
| SQL | `Summary [('20261029_000001', 14, 14)]` |
| SQL | `Rejected [('20261029_000001', 815, 8)]` |
| SQL | `parquet scan [(4905,)]` |
| SQL | `join sample [('CLST-6669 20251001(20261006-052156).pdf', 1078), ('Daiwa-1319 20231011(20261006-122413).pdf', 813), ('凱基投顧_2637 慧洋-KY_賴偉中_20260915.pdf', 781)]` |
| OutputStore 自測(venv_duck)| [計] VRN2_OutputStore v0100 --selftest · OK 9 · FAIL 0 |

## 5. 一鍵 v0144 情境(pwsh · 假 GitHub 分支)

| 項 | 結果 |
|---|---|
| rc | first rc 1 · again rc 1 · tamper rc 1 · done(rc 1 = 沙盒 ③ 環境檢查 RED,與 §3 同)|
| 第一次(Downloads 沒套件 → 從分支取)| [GREEN] ③ 套件 v0144 就位(SHA-256 41c49c5ed19a · 套件內 10 檔逐檔核對相符 · 來源 GitHub claude/optimistic-goodall-yhalc5)→ /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v144/t144oc/Download |
| 再貼一次 | [GREEN] ③ 本機已是 v0144 套件(SHA-256 41c49c5ed19a · 套件夾 11 檔與已驗證的 zip 逐檔相符)· /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v144/t144oc/Downloads/VRN2_Closeout_v0144 |
| 竄改啟動器後再貼 | [YELLOW] ③ 本機套件夾有 1 個檔與已驗證的 zip 不同或不在(ActivateVRN-2_v0144.py)→ 不用它,從本機這份 zip 重新解壓 → [GREEN] ③ 舊套件夾已改名備份 → /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v144/t144oc/Downloads |
| ⑧b / Workbench | [RED] ⑧b 收尾收據 v0144 · rc 1 · 跑了 1 輪(idempotence GREEN)· 四點原文核對 REVIEW_OCR {'PASS': 52, 'OCR_PENDING': 4} · 輸出缺項 1 ·  |
| ⑬ / ⑤b 摘要行 | [YELLOW] ⑬ 輸出位置 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v144/t144oc/OneDrive/VRN2_out · 增量庫 pyarrow · 新檔 14 / 已知 0 · 追加 BasicInfo 14 / FinancialData 4905 / Summary 14 / Rejected 815 · parquet 5 · 沒有 duckdb 套件 → pyarrow 備援(功能同 · · [GREEN] ⑤b SSOT-ID 核號同步 · 核發 0 · 衝突 0 · 待核號 371(SSOT 類 82 · 程式類 289)· 自撞 0 · 登記冊 VRN2_Component_Register_v0101.json · 核發冊 尚無(VCGC 還沒核發) |

## 6. 沒有宣稱的

- Windows desktop run of v0144: not yet (next paste-back); the desktop has not run v0143 either
- VCGC side of the SSOT-ID protocol (reading VRN2_NUMBER_REQUEST_latest.json, writing VCGC_NUMBER_GRANT_latest.json): contract only (VIA_SSOT_ID_Protocol_v0100.md); not implemented by this line (VCGC is another system)
- A real Windows FolderBrowserDialog for vrn2://pick?kind=outdir: not exercised in the container (handler selftest uses the VRN2_PICK_OUTDIR hook); the dialog code path is the same as vrn2://pick for input (v0133 · desktop-proven)
- Browser drag-and-drop cannot read the dropped folder's real path (browser sandbox); the drop zone opens the dialog instead
- DuckDB path inside the launcher: the launcher sandbox venv has no duckdb (pyarrow fallback · YELLOW); the DuckDB engine was proven with the OutputStore CLI in venv_duck on the same output books
- Items carried from v0143: PasteBack zip 013350 transcript, v0248 / v0253 location on the desktop, verifier wall time on 52 files, 四點 FAIL 1 / 缺項 3 份年度數據
