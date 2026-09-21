# 批687B · 第一次真跑 --verify:665 列裡 627 列 INSUFFICIENT、21 列 FAIL,先把尺修對再談對錯

操作員拉了 批685/686 後跑 `VRN_ENG074 v0113 --verify`(HEAD 對了:VCGC v0119 · 台帳 1286 · 中央冊 6006/6006 缺 0):

```
[驗算] 30 件 × 7 條恆等式 → 665 列 · INSUFFICIENT 627 · FAIL 21 · PASS 17
[驗算] 缺運算元點名:gross_profit ×173, net_margin ×133, cogs ×128, op_margin ×128, net_income ×84, gross_margin ×81, opex ×79, shares ×69
[官方核對] 官方表 tw_financial 不在=誠實略(補料=VDF_ENG082 run;同意閘你設)
```

## 一 · 這三行怎麼讀(LL329)

| 數字 | 讀法 |
|---|---|
| 30 件 | 105 份入庫報告裡只有 30 份有 `vrn_report_financial` 列;48 份非個股本來就沒財報頁(N/A),**剩下 27 份個股沒有財報列**=財報頁擷取未覆蓋,不是驗算的錯(Z89) |
| PASS 17 · FAIL 21 | 七條恆等式裡**只有毛利率那條**三個正典都登錄了(gross_profit/revenue/gross_margin),所以 38 次真算全是 GM_DIV;21 次 FAIL 的第一嫌疑是**同期間同正典多列**(「毛利率」與「營業毛利率」、不同頁的兩張表),v0113 用第一列,對錯全看誰先出現——尺的問題,先修尺 |
| INSUFFICIENT 627 | 混了兩種事:`cogs/opex/op_margin/net_margin/shares` 是**未登錄正典**(登錄=你的手,Z82);`gross_profit ×173 / net_income ×84 / gross_margin ×81` 是**報告未載**(這份表沒那一列,登錄救不了)。v0113 混成一串,看不出哪些是你能決定的 |
| tw_financial 不在 | VDF_ENG082 還沒跑(或跑了沒過同意閘);貼回時前面被切掉的 `^` 那段可能就是它的輸出——要那一段(Z83) |

## 二 · 做了什麼

| 件 | 檔 | 驗 |
|---|---|---|
| 財報頁 | `VRN_ENG074_FinancialPages_v0114.py`:① `_identity_best()` 同期間同正典多列逐組合試(≤3×3×3)、**同頁優先**、取差最小,note 寫明用了哪幾列(頁·原文)與候選數;② 缺運算元分「未登錄正典 / 報告未載」兩類點名;③ FAIL 列與 DIVERGE 列直接印(各 ≤10);④ 分母印出(有財報列 N/入庫 M) | **三十三檢 33/33**(㉜ 8888 雙列「毛利率 45 錯 / 營業毛利率 40 對」→ PASS 且 note 具名;㉝ 兩類點名 + ✗ 列 + 3/4 分母) |
| 格子 | `CGC_MDL064_SelftestGrid_v0437.py` 一站改名;站數 287 | 全格子見四 |
| 冊 | 規則冊零改(容差、恆等式、未登錄清單都在 批685 那一段) | — |

## 三 · 你的手

1. 拉線後再跑一次 `--verify`:FAIL 列會直接印出來(哪份、哪期、期望/實際、用了哪幾列),貼回那段就知道 21 列是抽錯列、單位混、還是報告自己算錯。
2. 登錄(Z82):冊上 `unregistered_canonicals` 就是清單;你說「登錄 cogs、opex」我就寫進 `VRN_Financial_Synonyms_SSOT`(只增不減),恆等式立刻多四條能跑。
3. 官方料(Z83):`$env:VIA_NET_CONSENT='YES'` 後跑 VDF_ENG082,貼回它的輸出(上次被切掉的那段)。
4. 財報列覆蓋(Z89):`VRN_ENG074 v0114 run`(對 `C:\測試樣本報告` 全跑)後再 `--verify`,分母應從 30/105 往上。

## 四 · 本批實測(容器)

```
ENG074 v0114 --selftest          三十三檢 OK 33 · FAIL 0(㉜ 雙列取差最小具名 · ㉝ 缺分兩類 + ✗ 列 + 分母)
registry-sync --apply            活 6007 · 新 1 · 變更 57;契約 19/19 OK
全格子 v0437(LL117)             OK 255 · FAIL 20 · SKIP 6 · TIMEOUT 0(266s;GRID_20260921_104209)· 終判 FAIL 集對 批686 逐站相同:新紅 0 · 消失 0(平行段 2 站鎖撞序跑轉綠)
```
