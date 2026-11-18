# 短指令改走 Python · 第一批交接(2026-11-18)

操作員令:「一些舊的短指令背後指令全部要改為 PY 指令,且依照規定也要安裝加速器 × 3~5 步驟同步進行安全進行機制」「列短指令清單分批改成 PY」。道數已統一 3~6。

## 這一批交了什麼

| 檔 | 編號 | 做什麼 |
|---|---|---|
| `supportive modules/registry/VIA_ShortCommand_PyRoute_SSOT_v0100.json` | VIA-VCGC-SSOT404 | 212 支短指令全列(應掃 212 · 已掃 212 · 略過 0) |
| `supportive modules/registry/CGC_MDL134_ParallelLanes_v0103.py` | VIA-VCGC-MDL1662 | `cmd list / check / plan / run`;先降壓 → 3~6 道 → 監工 |
| `Register-VIA-Commands-v0279.ps1` | VIA-CORE-MDL868 | 第一批 4 支改成只轉呼叫 Python |

第一批 4 支:`via-vrnrun`(→ VRN 啟動器)· `via-vdffetch`(→ VDF 啟動器)· `via-six`(→ CGC_MDL127)· `via-panorama-all`(→ `cmd run`,兩步同時跑)。
VRN / VDF 的兩支直接呼叫各自系統的啟動器,不經 VCGC。

## 驗過什麼、沒驗什麼

- 容器:自測 35/35;`cmd run via-six` 綠;`cmd run via-panorama-all` 兩步同時起跑、兩步都紅(紅在既有問題,見下)。
- **沒驗**:`Register-VIA-Commands-v0279.ps1` 沒在 PowerShell 跑過(容器沒有 PowerShell),只做了括號引號配對與編碼檢查。
- 主機一行(分支到桌機之後):`via-reload; via-lanes cmd check; via-six --no-open`
- 退回:把 v0279 改名或移走,尾版回到 v0278;舊的 .ps1 都沒刪。

## 這一批看到、沒動的問題

1. `cmd check` 紅 7 支:`via-talib` · `via-taone` · `via-revphase` · `via-vrnuni` · `via-twrev` · `via-ves` 指向的引擎在本樹找不到;`via-managers` 釘的 `VDF_SystemManager_v0105` 沒帶加速器橋。
2. `via-panorama-all` 的加速器控制面自測紅:收容夾 `functional modules/VAP/intake` 有 9 支 .py 沒帶橋(收容夾是凍結來源,不能改;要在控制面登豁免或由操作員裁)。舊的 .ps1 把這個結果丟掉,所以以前看不到。
3. 全景已修冊回歸 2 筆:F535-ACCEL · F536-PINVER。
4. `VDF_MDL022_SafeParallelLaunch_v0103` 總結行印的版本是 v0102。

## 還沒改的 23 支

- 第二批 13:`via-panorama-run` · `via-envgov-auto` · `via-complete` · `via-groups-ui` · `via-op` · `via-op-pick` · `via-op-run` · `via-vrnaudit` · `via-realtest` · `via-review` · `via-psrepair` · `via-bg` · `via-envpy`。
  細看後的修正(下一版路由冊要改):`via-bg`(列 Windows 行程)· `via-envpy`(回傳環境的 python 路徑給 PS 用)· `via-psrepair`(第一輪用 PowerShell 自己的語法樹)比較像 PS 本職;`via-realtest` · `via-review` 是多步,該歸第三批。
- 第三批 5:`via-pipeline` · `via-allgreen` · `via-allinone` · `via-all` · `via-oneshot`(多步編排,要先把步拆成冊)。
- 第四批 5:`via-superhtml` · `via-repo-optimize` · `via-ppp` · `via-unstick` · `via-intake`(先看還用不用)。

下一批開工前:先拿到第一批在主機 PowerShell 的結果,再疊下一版 Register。
