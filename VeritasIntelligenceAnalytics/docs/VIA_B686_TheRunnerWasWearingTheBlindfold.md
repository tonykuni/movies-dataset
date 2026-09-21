# 批686 · 眼罩是跑器自己戴的:紅燈要講出為什麼紅

操作員 09-21 第二次貼回 `via-vrnrun`(HEAD 仍是 `0b6f7dfb`=批684,**批685 還沒拉**)。V2 六層鏈 GREEN 28 · RED 3 · NODATA 15;三盞紅跟上一次一樣:SUP_MDL746、CGC_MDL141、VRN_ENG068 ⑨。

## 一 · 量到的(LL329)

| 看到什麼 | 其實是什麼 |
|---|---|
| SUP_MDL746 那格印 `[OK] ⑨ 紀律宣告 … OK 8 · FAIL 1(rc=1)` | 跑器 v0101 的「量到什麼」取**最後兩行**;多檢自測的最後一行幾乎永遠是最後一檢的 OK,紅的那一檢被蓋住 |
| CGC_MDL141 那格印 `[OK] ⑭ 報告夾律…` | 同上。**⑭ 是過的**。批685 我照這行把根因猜成 ⑭,猜錯了(已在 B685 與 Z84 更正) |
| 容器裡兩支各 9/9、14/14 全綠 | 紅只在工作站發生,而工作站的紅**沒有一行說得出是哪一檢**——這就是為什麼貼回兩次還是定不了根因 |
| V4 `[第二顆頭]` 另一本 `functional modules\VRN\output\vrn_reports.duckdb` 也有 vrn_report_basic | 舊路徑遺留(09-20);矩陣已具名點出;封不封存=你的手(Z87) |
| vcgc `VRN 系統管理 engine RED · handover STALE · 連結 RED 1` | engine 燈照抄鏈跑器(RED 3);交接 STALE=一頁交接仍 批554(Z58);連結 RED 1 隨鏈 |

## 二 · 做了什麼

| 件 | 檔 | 驗 |
|---|---|---|
| 鏈跑器 | `CGC_MDL172_VRNChainRunner_v0102.py`:① `_note_of()` rc≠0 先印 `[FAIL]` 行(最多兩行)再接 `[計]` 行;② `ModuleNotFoundError` → **ABSENT 具名套件**(Z60 結;缺件≠壞掉 L16;修法指 `via-rungate --approve-install`=你的手);③ 檢數改成數的(LL332) | **廿四檢 24/24**(㉓ 假引擎 rc=1 三檢:量到什麼=`[FAIL] ② …/[計] …`,最後一行的 `[OK] ③` 不在;㉔ 假引擎 import 缺件 → ABSENT 具名) |
| 格子 | `CGC_MDL064_SelftestGrid_v0436.py`:「VRN 六層鏈廿二檢」→「廿四檢」;站數 287 不變 | 全格子見四 |
| 文 | B685 第四節兩列更正;掉球 Z84 改寫、~~Z60~~ 結、+Z87 | — |

不動的:SUP_MDL746 / MDL141 本身(容器全綠,沒有證據說它們壞;要修得先看到 FAIL 行)。

## 三 · 工作站下一步(你的手)

拉 批685+686 之後再跑一次 `via-vrnrun`,SUP_MDL746 / MDL141 兩格會直接印出 `[FAIL] ①…` 那一行——貼回那兩行就能定根因,不必再猜。

## 四 · 本批實測(容器)

```
CGC_MDL172 v0102 --selftest      廿四檢 OK 24 · FAIL 0(㉓ 量到什麼=[FAIL] 行優先 · ㉔ 缺件 → ABSENT 具名)
CGC_MDL172 v0102 run --fast      GREEN 31 · RED 1 · GATED 1 · NODATA 13 · ABSENT 0(ENG064/ENG068 兩格直接印 [FAIL] ⑦ / [FAIL] ②,不再是最後一行的 OK)
registry-sync --apply            活 6006 · 新 2 · 變更 41
契約 test_master_control_contract 19/19 OK
全格子 v0436(LL117)             OK 255 · FAIL 20 · SKIP 6 · TIMEOUT 0(256s;GRID_20260921_102019)· 終判 FAIL 集對 批685 逐站相同:新紅 0 · 消失 0
                                 (平行段 1 站 DuckDB 鎖撞「鉅亨 FactSet 共識九檢」,序跑轉綠=尺的問題不是引擎,批610 已記)
```
