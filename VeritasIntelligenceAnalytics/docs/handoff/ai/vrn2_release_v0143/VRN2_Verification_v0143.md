# VRN-2 v0143 容器實測紀錄(2026-10-29)

起因:操作員 2026-10-29 桌機第一次實跑本地實測一輪 v0100(貼回主控台):② ChainShip 紅(ship 後仍缺 v0248 / v0253)· ③ VRN-2 一鍵 rc 1(同一 VIA 根兩個啟動器重疊 → RAM 0.16 GB → ⑦ 1500 秒無輸出被停 · ⑪ 1800 秒超時 · ⑫b 120 秒超時 → ⑤b 紅)· ① logo 黃。

## 1. 本輪改了什麼

| 元件 | 版本 | 內容 |
|---|---|---|
| 啟動器 | ActivateVRN-2 v0143(v0136 底座 · runtime v0142 不動)| 單機閘 `VRN2_Launcher.lock`(活 PID → rc 1 不跑 · 過期接手 · `VRN2_FORCE_PARALLEL=1` 強制)· 子行程上限從環境讀(`VRN2_UI_REFRESH_WAIT` 600 · `VRN2_SILENT_MAX` 3600 · `VRN2_MANIFEST_WAIT` 900 · `VIA_VRN2_VERIFY_WAIT` 3600 · 下限 60)· ⑫b 子行程失敗 / 超時 → 本支補放輸入區塊 · 收據 v0143 多 guard / limits / ui_block |
| ChainShip | v0101(v0100 留著)| `ship` 先 `recover`:缺的環在 VIA 樹 / 私有 runtime / 備份 / Downloads VRN2_* 夾與 zip(含套件 zip 內 runtime zip)找同名唯一內容 → 複製進 VRN 夾再隨船;多份不同內容只列;`recover` 動詞 · `--no-recover` · `--extra` |
| 操作員一鍵 | v0104 | ② 改指 VRN-2 一鍵 v0143 · 橫幅版號修正(v0103 印 v0102)|
| 本地實測一輪 | v0100(改指)| `$H_CS` → ChainShip md v0101 · `$H_OP` → 操作員一鍵 v0104 · ① 印章候選加 `OneDrive\Pictures\seal-logo-square.png` · ④ 收 `VRN2_Closeout_v0143.json` 與鎖檔 |

## 2. 自測與雜湊鏈

| 項 | 結果 |
|---|---|
| ChainShip v0101 `--selftest` | [計] VRN2_ChainShip v0101 --selftest · OK 27 · FAIL 0 |
| 啟動器 v0143 `--selftest` | [PASS] v0143: v0142 checks + single-instance lock (live / stale / forced / foreign), child limits (env · floor · mapping), ⑫b in-process fallback (missing page · patched · already present · handler er |
| pwsh 雜湊鏈 | Run-VRN2-v0143.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | boot143.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | Run-VRN1-VRN2-v0104.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | boot_pair104.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | cs101.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | round.ps1 parse errors: 0 |
| pwsh 雜湊鏈 | vrn2 one-click v0143: code sha = boot H → True (4652f05bc4f7) |
| pwsh 雜湊鏈 | one-liner decodes to boot → True |
| pwsh 雜湊鏈 | package zip sha = \1fd30c4ee23ea06edd2f9dba931d5a1f5953246c2426b274b050968ebd7b205c → True |
| pwsh 雜湊鏈 | operator v0104: code sha = boot H → True (c0c7511e009f) |
| pwsh 雜湊鏈 | operator H2 = vrn2 one-click v0143 code sha → True |
| pwsh 雜湊鏈 | operator banner says v0104 → True |
| pwsh 雜湊鏈 | localround H_OP = operator v0104 code sha → True |
| pwsh 雜湊鏈 | localround H_CS = chainship md v0101 code sha → True |
| pwsh 雜湊鏈 | chainship md WANT = tool v0101 sha → True |
| ChainShip v0101 `recover`(本倉 clone · 容器 Downloads 空)| [計] VRN2_ChainShip v0101 · recover · YELLOW · 缺 5 · 複製 0 · 多份不同 0 · 找不到 5 · 內容不過 0 |

## 3. 沙盒全流程(套件 v0143 · 19 份真檔)

| 項 | 結果 |
|---|---|
| 單機閘 | 接手過期鎖(PID 1569 已不在) · 結束後鎖檔已移除 True |
| 上限 | {'VRN2_UI_REFRESH_WAIT': 600, 'VRN2_SILENT_MAX': 3600, 'VRN2_MANIFEST_WAIT': 900, 'VIA_VRN2_VERIFY_WAIT': 3600} |
| ⑫b | [計] ⑫b U/I 輸入區塊(window I/O) · [鎖驗證] accelerator=EXACT · network=EXACT · 耗時 1 秒 · ui_block {'lamp': 'GREEN', 'how': 'in-process', 'detail': 'v0143 本支補放(處理器子行程 沒跑)· U/I 輸入區塊 換掉同一塊(三類 · 只開個股報告/訊息)'} |
| 收尾 rc | 1(③ 環境檢查 RED in the Linux sandbox only (accelerator deps not in venv; --no-install); same as v0142)|
| 非綠步驟 | [('③ 環境檢查與補裝', 'RED'), ('⑦ 啟動 VRN-2', 'GRAY')] |
| 輪數 / 冪等 | [(1, 0, 'idempotence GREEN')] · GREEN |
| ⑧ 完成判定 | 完成 · 紅 0 黃 3 · VRN-2 SystemManager v0243 |
| ⑦ 個股四項 | 14 份 · 全綠 14 |
| 四點原文核對 | None · 缺項 [{'book': '四點原文核對', 'reason': 'NOT_RUN · RuntimeError: 本輪輸出未齊，不驗舊冊'}] |
| ⑪ 獨立驗證 | 基本資料 {'PASS': 193, 'OCR': 2} · 四點 {'PASS': 65, 'OCR': 5} · 年度 4905 筆 {'ALIGNED': 4378, 'TRANSALIGNED': 75, 'SUBALIGNED': 452} |
| Workbench | GREEN · 舊版 U/I 連結 True |

與 v0142 同一組數字(無退步)。

## 4. 單機閘情境(沙盒)

| 情境 | 結果 |
|---|---|
| 鎖裡的 PID 活著(sleep 行程)再啟動第二個 | second launcher printed [RED] 單機閘 · 另一個 VRN-2 啟動器還在跑(PID …)and exited rc 1 before ① (nothing ran) |
| 鎖裡的 PID 已死 | taken over: [計] 單機閘 · 接手過期鎖(PID … 已不在) |
| 跑完 | 鎖檔 removed |

## 5. 一鍵 v0143 情境(pwsh · 假 GitHub 分支)

| 項 | 結果 |
|---|---|
| rc | first rc 1 · again rc 1 · tamper rc 1 · done(rc 1 = 沙盒 ③ 環境檢查 RED,與 §3 同)|
| 第一次(Downloads 沒套件 → 從分支取)| <Objs Version="1.1.0.1" xmlns="http://schemas.microsoft.com/powershell/2004/04"><Obj S="information" RefId="0"><TN RefId="0"><T>System.Management.Automation.InformationRecord</T><T>System.Object</T></ |
| 再貼一次 | <Objs Version="1.1.0.1" xmlns="http://schemas.microsoft.com/powershell/2004/04"><Obj S="information" RefId="0"><TN RefId="0"><T>System.Management.Automation.InformationRecord</T><T>System.Object</T></ |
| 竄改啟動器後再貼 | ng>[GREEN] ③ 套件 v0143 就位(SHA-256 1fd30c4ee23e · 套件內 10 檔逐檔核對相符 · 來源 本機已驗證的 zip)→ /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/v143/t143oc/Downloads/VRN2_Closeout_v0143</ToS |
| ⑧b / Workbench | 32><U32 N="ManagedThreadId">12</U32></Props></Obj><Obj S="information" RefId="39"><TNRef RefId="0" /><ToString>[GREEN] Parquet 4 / 4</ToString><Props><Obj N="MessageData" RefId="40"><TNRef RefId="1" / · 32><U32 N="ManagedThreadId">12</U32></Props></Obj><Obj S="information" RefId="39"><TNRef RefId="0" /><ToString>[GREEN] Parquet 4 / 4</ToString><Props><Obj N="Me |

## 6. 沒有宣稱的

- Windows desktop run of v0143: not yet (the operator's next paste-back); the 2026-10-29 paste-back was v0142
- Why the second launcher started at 01:35 on the desktop: needs transcript.txt from VRN2_PasteBack_20261029_013350.zip; v0143 only prevents the overlap
- Where v0248 / v0253 live on the desktop: only ChainShip v0101 recover on the desktop can tell ([FIND] / [FIND?] / [FIND-])
- Verifier v0110 wall time on 52 desktop files under normal RAM: no clean measurement yet (both desktop runs were starved)
- 四點原文核對 FAIL 1 · ⑧ 黃 4 · 缺項 3 份年度數據 on the desktop: untouched this round (needs the paste-back zip)
