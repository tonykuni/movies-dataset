# VRN-2 雲端靜態稽核 · 2026-10-28 · 第 1 段(收尾授權 48h · 雲端容器側)

> 來源:Claude Code 雲端 Linux 容器(倉 `tonykuni/movies-dataset` · 分支 `claude/vrn2-closeout-authorization-y4ixl7` = origin/main 918461d4)。
> 本容器**不是** Tony 的 Windows 桌機:沒有 Downloads、PowerShell、`C:\測試樣本報告`、ActivateVRN-2 v0158、收尾包。
> 因此授權書 §3 工作 1~11 的執行(`--loop N --closeout`)**本段沒有跑、沒有冒充跑過**;本段只做倉上可做的只讀稽核。只增不減:本檔為新增,未動任何既有版本檔。

## 1. 進場步驟(CLAUDE.md)

| 步 | 結果 |
|---|---|
| token | 6/6 啟用 · 全景 v0117 · NLP v0106 · rc0 |
| functions | 卡 v0102 · rc0 |
| handoff check | rc2 · 交接閘 RED(倉級既有:落後 191 提交 · 快照 610h · 註冊冊待同步 new 796 / changed 138 / stale 54;SDD X-REG / X-NUM 紅)· 與 VRN-2 本批無直接相依 |

## 2. 倉上(origin/main)VRN-2 家族實況 vs 授權書 §1 現役表

| 元件 | 授權書現役 | 倉上實況 | 判定 |
|---|---|---|---|
| 啟動器 ActivateVRN-2 | v0158(Downloads) | 從未以 .py 提交;只有 `docs/handoff/ai/vrn2_release_v0122~v0136/*.zip` | 灰(不在倉,無法從倉啟動) |
| VRN-2 SystemManager | v0254(鏈 …→v0249→v0253→v0254) | 有 v0244 · v0245 · v0249 · v0254;**缺 v0242 · v0246 · v0247 · v0248 · v0253**(git 全分支歷史從未提交) | **紅:鏈在乾淨 clone 載不起來** |
| 擷取引擎 ENG397 | v0129 鎖 `33ff9eae8c11` | v0129 在位;sha256(CRLF 正規化)= `33ff9eae8c11` ✓(LF 原樣 = `4692ccad5301`) | 綠 |
| 摘要器 ENG062 | v0114 | 倉上最高 **v0113**;v0114 未提交 | 黃(現役版不在倉) |
| MarketFetch | v0112 | v0112 在位(前版 v0100~v0107 · v0110 · v0111;v0108/v0109 另一線不在) | 綠 |
| VDF 引擎包 | `_vdf_fetch\VDF_TW_AllInOne_v039.py`(v036 保留) | 倉上只有 AllInOne_v039;`VDF_TW_DataFetchEngine_v036.py` 不在(v0112 以 glob 取 AllInOne 優先,不致硬失敗) | 黃(v036 未保留在倉) |
| 發布引擎 VRN2_Publish | v0101 | v0100 · v0101 在位 | 綠 |
| U/I 處理器 VRN2_UIAction | v0107(轉交 v0106 → v0105) | v0100 · v0101 · v0105 · v0107;**v0106 不在** | 黃(轉交目標缺一層) |
| SSOT VRN2_SSOT | 最高版 · funnel.ocr_ladder 325p,400p | v0101 已是 `325p,400p`(v0254 `ensure_ssot_funnel` 不會再出版) | 綠 |
| 帳本 / 輸出冊 / 收尾包 | registry\VRN2_*Ledger · VIA_Reports\vrn2\{output,loop} | 倉上皆無(未入倉,屬桌機本地) | 灰 |

## 3. 實測證據(只讀 · 本容器)

```
cd "functional modules/VRN"
python3 VRN_SystemManager_v0254.py --selftest   → FileNotFoundError: 前版 VRN_SystemManager_v0253.py 不在 · v0254 不接  (rc1)
python3 VRN_SystemManager_v0249.py --selftest   → FileNotFoundError: 前版 VRN_SystemManager_v0248.py 不在 · v0249 不接
v0244 PRIOR_NAME = VRN_SystemManager_v0242.py → 不在
git log --all -- '*VRN_SystemManager_v025[0-3]*' → 空(v0250~v0253 從未進任何分支)
最近兩筆上船 commit(v0152 · v0155 收尾)各只含 4~5 檔:當輪新落地的尾版 + SSOT;前版鏈未隨船。
```

## 4. 判定與對 §3 工作的影響

- **工作 11(上船)真紅前置**:⑨ 自動上船只帶「當輪新落地的檔」,薄尾釘名的前版(v0242 / v0246 / v0247 / v0248 / v0253 · ENG062 v0114 · UIAction v0106 · VDF v036)留在桌機未入倉。
  乾淨 clone 的 v0254 無法載入 → 任何從倉啟動的 VRN-2(含雲端 Claude、另一台機器、CI)都是紅。
  建議(不執行、等 Tony 確認):下一輪 ⑨ 把 **鏈上所有在位前版**納入同一筆上船(只增 · 不覆寫 · 同名不同內容出 v+1 不覆寫),再用 `chain VRN_SystemManager` 確認 PINVER 風險歸零。
- **「6 KB 殘樁 v0152 / v0153」**:倉上 `VRN_SystemManager_v0152.py`(5,906 B)/ `v0153.py`(6,125 B)說明寫的是 2026-10-14 VRN provenance / metrics-resolve 薄尾(glob 取前版),與授權書描述一致;本段**未** git checkout、未搬動,交 ②r 處理。
- **ENG397 鎖雜湊口徑**:鎖值是 CRLF 正規化後的 sha256;倉為 LF。若桌機 MarketFetch v0106+ 的「CRLF 正規化」同樣套在 ENG397 比對上即一致,否則 LF 環境會誤報「鎖冊過期」。
- 工作 1~10、12 **未動**:需桌機(Downloads v0158 · pwsh · 測試樣本 52 份 · 網路 MOPS/VDF)。本容器沒有 pwsh,不冒充跑過(functions 卡[門] go 條)。

## 5. 停止條件對照(§7)

- 「版本輩分冊來源不明 > 0」:倉上無法產生輩分冊(啟動器不在)→ 未判定。
- 「需要刪除 / 覆寫既有版本」:無。「需改 VRN-1 / VDF / VCGC / v1652」:無。MOPS DENY:未觸及。
- 本段停在:**執行環境不符**(§0「執行指令必須自己找檔(Downloads 最新版)」→ [RED] Downloads 沒有 v0158)。

## 6. 決定(2026-10-28 · 操作員令「依我最大利益決定」· 雲端代決 · 可推翻)

1. **前版鏈隨船 = 是。** 已搜遍 origin 全部 272 個分支(含 `vrn2-auto` edc215ad):v0242 / v0246 / v0247 / v0248 / v0253 · ENG062 v0114 · UIAction v0106 · VDF v036 **沒有任何一個分支有**,只在桌機。
   桌機下一輪 ⑨ 必須把鏈上所有在位前版一起上船(只增 · 同名不同內容出 v+1 · 不覆寫),否則工作 11 不能算過。雲端做不到,不冒充。
2. **VCGC 座位冊不帶上船。** `handoff check` 自動把 `VIA_VCGC_SubsystemSeat_v0100.json` 的 VRN 座位改成 v0254、VDF 改成 v0162;那是 VCGC 的冊,已還原到提交版、未入本分支。要改經 VCGC `registry-sync --apply`。
3. **本分支不開 PR、不推 main。** 審核冊只放 `claude/vrn2-closeout-authorization-y4ixl7`;要進 main 由桌機 ⑨ 或 Tony 決定。
4. **不疊版。** 不在雲端出 v0255 / ENG397 v0130 / ENG062 v0115:缺前版與樣本,出了也驗不了(§7「連續兩版同家族仍無法轉綠」防線)。

NEXT(桌機):貼授權書 §6 指令跑 `--loop 3 --closeout`;貼包出來後把本冊 §2 表與 §6 第 1 條一起貼給桌面端 Claude,Day 2 工作 11 先補鏈再上船。
