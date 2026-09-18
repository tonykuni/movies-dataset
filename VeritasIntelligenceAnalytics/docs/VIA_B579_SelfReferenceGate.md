# 批579 · 自我指涉閘 —— 把 LL133 從一條教訓變成一道守得住的閘

## 一、為什麼要立這道閘

批578 被自我指涉咬了三次,其中一次**差點變成假進步**:
制度稽核器判「誰在讀這本冊」時只排除 `__file__`,我一開 `v0101`,
舊的 `v0100` 立刻變成每一本冊的第二讀者 ——「單一讀者 3 本」當場變 **0**。

> 那是我自己的版本號造出來的假改善,比假綠更難發現,因為它看起來像進步。

與其記在冊上等下次再踩,不如讓它**下次自己亮燈**。

## 二、`via-govaudit selfref`

掃全樹**尾版**,找出「在回答**誰引用 / 誰是 owner / 誰是讀者**」的判定器,
檢查它有沒有把**自己的家族**排掉:

```
在回答「誰引用」的判定器 18 支 · SAFE 3 · WEAK_SELF 0 · NO_EXCLUDE 15 · 基線外 0
```

| 狀態 | 意思 |
|---|---|
| `SAFE` | 排掉**整個家族**(泛用寫法或自家族字面) |
| `WEAK_SELF` | 只排掉 `__file__` 這一支 —— 一開新版號,舊版就變成引用者(批578 實例) |
| `NO_EXCLUDE` | 完全沒排自己 |

### 為什麼 NO_EXCLUDE 15 支**不判紅**

`NO_EXCLUDE` 本身不等於一定壞 —— 要它的說明文字或設定表**剛好提到它在數的那個名字**,
才會自己算自己。15 盞清不掉的紅燈只會教人忽略紅燈(LL129)。

所以走**棘輪**:

- 基線內的 15 支 = **既有債**,逐支改(列在 `SELFREF_BASELINE`)
- **基線外再冒出一支 = 紅燈** —— 新寫的判定器一律要排掉自己的家族

第⑱檢另外釘住一件事:**偵測器自己必須是 SAFE**,否則它就是在示範反例。

## 三、做這道閘的過程,又踩了兩次同類的坑

**① 分母沒套尾版律。** 第一版量出 **130 支** —— 其中一百多支是同一支引擎的歷史版號
(`CGC_MDL069_SystemManager` 一家就有 v0105~v0112)。套上尾版律:**18 支**。
這是本週第三次:MDL160 的頁(106→72)、MDL164 的讀者、現在是判定器。
**L68 不是寫給別人看的。**

**② 狀態判錯。** 第一版 `WEAK_SELF` 的尺只看「檔案裡有沒有 `__file__` 這個字」,
結果把 `CGC_MDL157`(拿 `__file__` **解版號**)和 `CGC_MDL158`(自測裡拿 `__file__` **當樣本**)
都誤判成 WEAK_SELF。收窄成「**在掃描迴圈裡**用 `__file__` 把自己 `continue` 掉」之後歸零。

> **判錯的狀態和判錯的紅燈一樣傷。**

## 四、回歸

```
CGC_MDL164 v0102 18/18 · 制度稽核站 十六檢→十八檢
```

**本批零 PowerShell 改動 · 零套件安裝**(L70)。

```powershell
via-govaudit selfref     # 18 支判定器 · SAFE/WEAK_SELF/NO_EXCLUDE · 棘輪守線
via-govaudit books       # 多冊並存逐組對照
via-govaudit             # 14 庫 3 機制
```

## 五、待辦(基線內的 15 支既有債)

`VIA_SYSTEM_MANAGER` · `CGC_MDL069_SystemManager` · `CGC_MDL075_CentralGov` ·
`CGC_MDL092_ConsolidationAudit` · `CGC_MDL106_GovConsole` · `CGC_MDL115_SSOTRegexDict` ·
`CGC_MDL124_BridgeSweeper` · `CGC_MDL135_EnvGovernance` · `CGC_MDL148_EngineBus` ·
`CGC_MDL153_WorkflowComposer` · `CGC_MDL156_VIAAcceleratorControl` · `CGC_MDL157_VIAUniqueEntryControl` ·
`CGC_MDL158_VIAPanoramaAuditRepair` · `via_bridge_sweeper` · `via_central_gov`

逐支改是後續的事;**棘輪先把線守住**,不會再變多。

再往下看一層(這一層是**線索,不是判定**):15 支裡有 3 支
(`CGC_MDL153_WorkflowComposer` · `CGC_MDL158_VIAPanoramaAuditRepair` · `via_bridge_sweeper`)
的原始碼裡有**自己的家族名字面 + 豁免機制**(例如 `via_bridge_sweeper` 的 `EXEMPT_SELF` 名單裡
就寫了自己)—— 它們**很可能早就是安全的**,只是用名單而不是家族比對,偵測器認不出來。
先別急著改它們;逐支看的時候從這 3 支開始確認,省下的力氣拿去修真正的 12 支。
**不把「偵測器認不出來」當成「它壞了」** —— 那又是一種判錯。
