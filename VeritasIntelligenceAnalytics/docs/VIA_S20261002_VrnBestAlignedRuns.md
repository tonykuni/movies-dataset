# VRN 近兩週「幾乎全對齊」的三次:狀態 · 邏輯 · 工具組合(2026-10-02 記錄)

操作員令:「在檢查近期兩周對話紀錄有兩三次幾乎值完全隊齊紀錄剛當時的狀態及邏輯及工具組合」「其他對話框也是」。
登錄:VCGC-REQ126(需求冊 v0151)· 交接工作項 `VCGC-REQ126:best-aligned-baseline`(PENDING,工作站驗證)。
查法:唯讀翻本倉各遠端分支的提交與 docs 記錄(含其他對話框的分支);沒有改任何引擎。本機是淺複本,更早的提交從其他遠端分支 ref 讀。

## 排名

| # | 日期 | 語料 | 判對率 | 可判率 | 鏈 | 證據 |
|---|---|---|---|---|---|---|
| 1 | 09-21(09-24 重現) | 工作站 105 份 × 7 欄 = 735 格 | **461/461 = 100%** | 62.7%(扣不適用 67.1%) | GREEN 29–32 · RED 0–3 · NODATA 14 | `cb1939a2` `docs/VIA_B690_HonestLampsForTheVdfFamily.md` §9;`f55a4a38`(B691);`eeaa7889` `VIA_B694_RealPercentAndNoBlackBox.md` §4;`90bc629b` / `224acaa0` `VIA_B729_TheSmallPrintAndTheAdjustedClose.md` §10 |
| 2 | 09-23 | 姊妹倉第二血統 106 份實檔 | PASS 260 · WARN 9 · **FAIL 0**;人工真值 券商 105/105 · 評等 48/48 · 目標價 41/41 · 現價 45/45 | — | — | 姊妹倉 `tonykuni/VIA-VDF-VRN` `41ce6d4`(分支 `claude/festive-ptolemy-ts2yyh`);本倉 `506b8ccb` `docs/VIA_B728_TheWorkInTheWrongPlaceComesHome.md` §1 |
| 3 | 09-21 | 容器 81 份 | 306/306 · FAIL 0 | 扣不適用 57.4%(306/533) | GREEN 33 · RED 0 · GATED 1 · NODATA 12 | `bf727640` `docs/VIA_B677_SeventeenOfSeventeenWereAlreadyThere.md` §3(更早 302/302:`VIA_B630B_RulerMismatch.md`) |

#1 各欄 GREEN:代號 57(NA 48)· 報告日 97 · 券商 90 · 評等 72 · 目標價 38 · **上漲空間 36**(NODATA 67 · YELLOW 2)· 分析師 71。
合計 GREEN 461 · YELLOW 11 · NODATA 215 · NA 48。

## #1 當時的工具組合(以 `cb1939a2` 的樹為準;近似,見限制)

| 家族 | 當時 | 現在(main `8399df4f`) |
|---|---|---|
| VRN_ENG073 | v0136 | v0139(v0138 的薄尾) |
| VRN_ENG072 | v0136 | v0139 |
| VRN_ENG083 VerifiedMatrix | v0119 | v0120(只修沿鏈讀 schema,判準沒動) |
| VRN_ENG086 | v0112 | v0119 |
| VRN_ENG082 | v0110 | v0111 |
| VRN_ENG080 | v0109 | v0111 |
| VRN_ENG049 / 057 / 058 / 085 | v0102 / v0104 / v0105 / v0106 | v0103 / v0105 / — / — |
| SUP_MDL746 PDFPlumberPlusHub | v0100 | v0102 |
| SUP_MDL743 GenericLayoutHub | v0100 | v0109(另拆 Layout* 子檔) |
| SUP_MDL749 | v0112 | v0116 |
| CGC_MDL172 | v0102 | v0108 |
| VRN_SystemManager | v0104 | v0114 |

邏輯冊:VRN_ExtractionLogic_SSOT v0100(至今未變)· VIA_VRN_LogicArchitecture_SSOT v0100。
環境:直譯器 via_vrn_312(B694);09-24 那跑記為 Python 3.13。ADJ 因子分母當時用 Yahoo close。
ENG072 當時逾時 180s 判 NODATA → 那一跑 OCR 線實際沒貢獻(成績全來自原生文字層)。

限制:工作站跑的不是確切提交。B694 記「拉批694 之前的樹」;B729 記 09-24 那棵樹是工作站本機 HEAD `16524649`(分支 `claude/via-envmanager-governance-7cls8h`,只在工作站,遠端沒有)。所以 ENG073 v0136 確定,其餘尾版是近似。
#2 的 `41ce6d4` 本對話框沒有姊妹倉權限,未親驗;那條線也沒回灌正本 ENG073 → ENG083(掉球 Z146 待裁)。

## 退步在哪:461 → 425,差 36 格,全在「上漲空間」

- 算術:461 − 36 = 425;YELLOW 11 + 36 = 47;NODATA 215 不變。
- 時間點:`a338a3d0`(09-25)`docs/VIA_S20260925h_VcgcVdfVrnCloseout.md` 已記「判對率 425/425」與「上漲空間整欄零綠」。
- 兩跑之間的變更:
  - ENG073 v0137(`1cfaf893`,09-24,批729):上漲空間改用最新 ADJ CLOSE,新增前一日 ADJ 三欄。
  - ENG073 v0138(`9e740220`,09-24,批730):因子分母改交易所原始收盤,新增狀態 `ADJ_EVENT_UNADJUSTED`。
  - `ddaaee74` · `bb9428e5`(批732/733):共識上漲空間改 ADJ。
- 尺:ENG083 v0119 `_v_upside`(L365)只在 `upside_adj_state` 以 `ADJ_OK` 開頭且 `upside_adj` 有值、或 `upside_state` ∈ EXACT / ROUNDING_DB 時判綠。
- 兩個假設(都未證實,要工作站庫):
  1. 產出端改了狀態字彙,尺沒跟上(LL292 同病)。
  2. v0138 要交易所收盤,而交易所價表缺日(Z174:上櫃表缺 09-08~09-22,上市表停在 08-12)→ ADJ_OK 歸零。
- 定案方法:工作站庫上看 V3 `[ADJ]` 那一行的 `upside_adj_state` 分布(哪些狀態、各幾列)。

## 其他對話框 · 其他系統

- 鏈本身沒退步:現在 GREEN 46 · NODATA 5,比歷來都好。
- 燈鎖 VIA_LampLock v0103–v0108 在 VRN 只鎖 ENG068 / 082 / 087;ENG083 · ENG073 從沒鎖過 → 矩陣沒有被鎖住的黃金狀態。這份記錄就是補那個基準。
- VDF:找不到「值對齊」等級的證據(最近只有 `cf03e24f` TAIEX 三源互核、`d23bdb26` lanes PART OK 3 · FAIL 10)。

## 下一步(工作站)

1. 同步到 main 後跑 VRN 矩陣,看是否仍是 425。
2. 看 `upside_adj_state` 分布 → 定是假設 1 還是 2;是 1 就出 ENG083 新尾版收新狀態,是 2 就補交易所價表缺日。
3. 回到 ≥ 461 後,把 ENG083 · ENG073 加進燈鎖,這次的數字成為鎖住的基準。
