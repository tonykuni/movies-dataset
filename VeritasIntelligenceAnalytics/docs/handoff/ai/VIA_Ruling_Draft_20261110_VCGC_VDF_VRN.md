# 裁定書草案 · 2026-11-10 · VCGC / VDF / VRN-2 獨立收尾(待操作員批)

操作員今日令:「今日收尾目標獨立收尾 VCGC VDF VRN 其他先免 · 回顧憲法規定政策規定」·「不可有 TA-LIB」·
「善用 VCGC 所有節省 TOKEN 工具 · 全景式地毯式搜尋 → 移除 → 修正 → 測試無誤」·「刪除相關功能不一定是全部刪除」。

## 一、憲法與政策(回顧 · 原文在 VIA_Policy_Laws_SSOT_v0116)
- **L50 第一條**:TA-Lib 禁用,QuantGuard 唯一正主;三層落地(執行期解析不到 · 不安裝 · 不 import)。「提到」不是「使用」;歷史檔不因提到而刪(MDL205 / MDL243 do_not)。
- **L120 / L123**:VCGC · VDF · VRN-2 · VRN-1 對等獨立、互不干涉;各自入口(VCGC = CGC_MDL149 · VDF = VDF_SystemManager 尾版 · VRN-2 = ActivateVRN-2 → VRN-2 SystemManager);VRN-1 外倉只讀。
- **L122**:衝突由 **AI 與操作員一起裁定(裁定書)**,由該系統自己的 manager 修自己的冊;VCGC 重檢後自動發號。
- **L125**:衝突解掉、VCGC 偵測無誤才發號;發出的號才有憲法性。現況:VCGC · VDF · VRN-2 三系統憲法燈 **RED = 衝突冊 OPEN 項點到本系統**。
- **L70**:`.ps1` 與套件是操作員的手(未經逐次許可不改、不裝)。**L04**:改動 = 新版號檔。

## 二、今日 TA-Lib 地毯式結果(VCGC 自家工具 + SystemCard G7)
| 工具 | 結果 |
|---|---|
| CGC_MDL190 TALibLock | GREEN · import 0 |
| CGC_MDL205 TalibBan | GREEN · 尾版 688 · import 0 · 提到 115(不算)· 未安裝 · 替代 VDF_ENG086_QuantGuardOneBridge 在 |
| CGC_MDL243 TalibCommandScan | 鎖成功 · 歷史保留 |
| CGC_MDL206 TalibPolicy | **YELLOW:missing code** —— 元件冊 `feature\|policy/L50`(VIA-FNT-0182)2026-09-28 被 registry-sync 標 RETIRED(來源冊 VIA_Policy_TalibBan_v0100 已有 v0101 尾版)。**點名漂移,不解鎖、不改號**(裁定 R5) |
| VIA_SystemCard v0101 G7(新:靜態 + 動態載入;v0100 已併 main 不就地改)| 兩倉尾版 3 支:**VAP 2**(AllInOne v0302 `def_import_optional("talib")` · v025 runtime L430)· **VRN-1 外倉 1**(engine/…FactorLibrary L686)。**VCGC / VDF / VRN-2 本倉 0** |

→ 今日範圍(VCGC · VDF · VRN-2)TA-Lib 使用 = 0。VAP 依今日令「其他先免」只登 CONFLICT-00013;VRN-1 只讀回報。

## 三、待裁項(點到 VCGC / VDF / VRN-2 的 OPEN 衝突 + L50 漂移)
| # | 衝突 | 系統 | 建議裁定 | 影響 | 復原 |
|---|---|---|---|---|---|
| R1 | CONFLICT-00002 VeritasAegisNexus 多份(W1 已轉接 50_Protection 副本;餘 2 份內容不同、有 exec 引用 20 / 37 處)| VCGC · VDF(網路橋)| 正本 = `network/VeritasAegisNexus_v1652`(鎖冊 sha 相符);其餘 2 份**先 diff 判功能差**,差異併成 v1653 新版號,原檔改轉接殼(不刪)| 呼叫點不動;exec 仍可用 | 轉接殼還原為原檔(git revert) |
| R2 | CONFLICT-00004 114 重名 .py(治理核心 5 件已轉接;餘 SSOT_Unified · Runtime_Bridge 內容不同 + 109 多為 VDF_MDL003 類)| VCGC · VDF | 治理核心 2 件先 diff 判正本(W2);其餘**不搬**(L04 · 仍被薄尾引用者不搬),只在 SSOT 標 `superseded_by` | 零行為變更 | 冊列標記可撤 |
| R3 | CONFLICT-00005 277 `_sha` 分身檔 | VCGC · VDF | AST 確認無 import 且不在 PRIOR 鏈 → 標 retire(不刪檔,移入 `_superseded/` 清單冊);有呼叫者 → 重指正名尾版 | 匯入面縮小 | 清單冊撤銷 |
| R4 | CONFLICT-00012 VRN-2 啟動器版本分岔(倉 release zip v0132 · 本機 v0178 · 管理器倉 v0262 / 本機 v0260)| VRN-2 | **以操作員本機測過的那一版為正**:請上傳本機 ActivateVRN-2 最新(v0178+)與 vrn2_work 清單;上之前掃 local ∪ origin/main 取號 | 只增版號 | 不覆蓋舊版 |
| R5 | MDL206 L50 code 漂移(VIA-FNT-0182 RETIRED)| VCGC | registry-sync 把 `feature\|policy/L50` 來源改指 `VIA_Policy_TalibBan_v0101`,**沿用 VIA-FNT-0182 原號**(不改身分 · 不重號)→ ACTIVE | MDL206 轉 GREEN | 改回 RETIRED |
| R6 | CONFLICT-00006 15 組同號異名(VCGC 8)| VCGC | 伴隨模組(同家族 _LayoutX 類)記命名冊;真撞號由操作員逐組裁定改號 | 編號唯一鍵恢復 | 命名冊撤銷 |
| — | CONFLICT-00007 275 遠端分支 · CONFLICT-00013 VAP TA-Lib | 全域 / VAP | 今日不動(「其他先免」);分支整理 = 操作員決定 | — | — |

批准後:各系統自己的 manager 修自己的冊(L122 ④)→ VCGC 重跑憲法矩陣 + CGC_MDL237 audit(遺失 0 · 改身分 0 · 重號 0)→ 衝突清空的系統才發號(L125)。
