# 批667 · 「VDF 是獨立引擎」—— 量出來的,不是宣稱的

## 你的令

> VDF 是獨立引擎,幫我確認一下完整測試;邏輯·因子·參數·引擎串連一下,
> 給我一個 PS 指令啟動他們,自 2023-07-01 開始的資料,邊測邊修直到成功,
> 跳出 HTML MATRIX SUMMARY BY RICH。
> + 要加入我指令的加速器及網路工具。

---

## 一、第一個問題的答案:**是,獨立。**

```
45 個 ENG 家族 · 真依賴兄弟家族 0
```

不是我說的,是掃出來的 —— 逐支讀 VDF 引擎尾版,找有沒有指回 `functional modules/VRN`
或 `functional modules/VAP`。

**第一次掃出 1 支。逐行看,那一支是誤判:**

```
VDF_ENG088_ConsensusFusionBridge
  INTAKE_GLOB = "functional modules/VRN/references/intake/**/VIA_CNYES_…_v*.py"
```

它讀的是一份**歸檔在 VRN 收容夾底下**的外來件 —— 那是**路徑**,不是**依賴**。
某份第三方檔案被收在哪個家族的 intake 夾,跟誰依賴誰是兩件事。

尺改成分兩類之後才是對的:

| 類 | 算不算不獨立 |
|---|---|
| 收容件路徑(`references/intake/…`) | **不算** |
| 真依賴(指到兄弟家族的引擎) | 算 |

→ 結果:**真依賴 0**,另有 1 處是收容件路徑,具名列出來讓你自己看。

---

## 二、四件全部在架上,一件都不用新造

```
參數  VDF_ENG053_ParamEngineMap      輸入參數 × 引擎整合映射
邏輯  VDF_ENG073_DataArchitecture    資料架構對映/盤點/最佳化計畫
因子  VDF_ENG061_FeatureStore + VDF_ENG062_GroupFeatureLayer
引擎  functional modules/VDF/engine  45 個 ENG 家族
```

所以新的是**串連器**不是引擎(LL306:先問翻了哪個架子)。
`CGC_MDL170` **只調度尾版**,判準留在各自那一支裡 —— 抄第二份判準就是九頭龍。

---

## 三、第 0 站是你點名的兩件

| | |
|---|---|
| **加速器** | `VIA_SuperAccel_Module`(accel_map / fetch / celeritas / 快取) |
| **網路工具** | `SUP_MDL740_NetUnified_v0113` → 後端 `VeritasAegisNexus` 正典(批402 律:網路只認 AegisNexus,740 留作橋) |

兩件都 graceful(缺席零影響),**但在不在一定印出來** —— 靜默掛不上等於沒掛。

### 同意閘

```
VIA_NET_CONSENT=未開  →  網路那一站 GATED,不是 RED
```

**自測⑦ 從原始碼層咬死這件事**:整份程式碼不准出現對那兩個 env 的寫入動作,
寫入點必須是 0。閘是你的手,不是我的。

---

## 四、容器這一跑

```
0a 加速器掛載      GREEN   可用道 accel_map·fetch·celeritas·activate
0b 網路工具掛載    GATED   SUP_MDL740_NetUnified_v0113 · 後端 AegisNexus 正典 · 閘一未開
0c VDF 獨立性      GREEN   45 家族 · 真依賴 0
1  參數           GREEN   0.7s   十一檢 OK 11
2  邏輯           GREEN   0.4s   九檢 OK 9
3a 因子·特徵庫     GREEN   4.8s   九檢 OK 9
3b 因子·族群特徵層  GREEN   1.1s   八檢 OK 8
4a 引擎·資料涵蓋閘  GREEN   0.2s   23 檢 OK 23(內含誠實 NODATA:冊 1980 · 價表 892 · TWSE 整所缺席)
4b 引擎·增量擷取閘  GREEN   0.8s   十六檢 OK 16
4c 引擎·VDF 稽核閘  GREEN   5.1s   十一檢 OK 11
→ GATED(唯一沒綠的是等你開閘那一站)
```

**七站全綠,13 秒。**

---

## 五、「邊測邊修直到成功」怎麼落地

不是我在迴圈裡硬跑,是三件:

1. **每一站失敗都給得出下一步**(L92)—— 表格最右邊第二欄就是修法句
2. **`--resume` 只重跑沒過的站** —— 讀上一回存證,已綠的跳過
3. **存證 append-only** —— `VDFCHAIN_LEDGER.tsv` 記得住第幾回合、起始日是哪天

自測⑰ 咬死「只跳過綠的」:把第一站假裝成綠,第二站必須還是真跑。

---

## 六、一個指令

`run` 不只是跑 —— 它**跑完就落 rich HTML MATRIX 並跳出來**。
要你跑完再多打一句 `html`,那就不是「一個指令」了。

```
via-vdfchain run
```

預設起始日 **2023-07-01**(`--since YYYY-MM-DD` 可覆寫;格式驗得住,`2024-13-01` 會被擋)。

---

## 七、又抓到一次自我指涉

自測⑱ 第一版寫 `"GRID_" not in src` —— **檢查器自己那一行也含有那個字面**,
於是永遠數得到。跟批664 的 `"duckdb"` 是同一條河的第三個渡口。

修法一樣:needle 動態組,而且只看引擎本體不看自測 ——
**自測碼提到一個字是在描述它,不是在用它。**
