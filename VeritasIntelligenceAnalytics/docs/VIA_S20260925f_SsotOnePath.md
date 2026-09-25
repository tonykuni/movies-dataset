# 2026-09-25f · 正則與同義字只走一條路

操作員令：任何 SSOT REGEX、同義字的自動交互檢查，都要設在單一路徑。沒過，VRN 很多定義又會大亂。

單一指的是誰有權判過沒過，不是樹上只能有一個帶 SSOT 的檔名。

## 判決只有這一條

```
via-vcgc ssot
  → via-vcgc ssot plan            零寫，只列出來
  → via-vcgc ssot plan -Apply     只把可自動的那幾步交給正主寫，做完再量
  → via-vcgc ssot verify         驗收。紅 = rc1。沒跑到這一步，就還沒過
```

正主在 `CGC_MDL149` v0130 的 `SSOT_PORT`。這是一張委派表，不是七扇門。本台不編一條正則、不併一個同義字：

| 格 | 正主 | 在判決裡的角色 |
| --- | --- | --- |
| hub | `SUP_MDL749_VRNFieldRuleHub` | VRN 欄位規則。被叫，不自己當整體過沒過 |
| bridge | `VRN_ENG088_SsotAdditiveBridge` | 增補與漂移 |
| union | `CGC_MDL176_SynonymUnion` | 同義聯集。會丟東西的變更它自己拒寫 |
| regexdict | `CGC_MDL115_SSOTRegexDict` | 正則清冊 |
| matrix | `CGC_MDL169_VIAStateMatrix` | 全冊編譯 |
| purge | `CGC_MDL177_ChinaBrokerPurge` | 拒絕名 |
| booksync | `CGC_MDL185_SsotBookSync` | 四本冊互相對：拒絕清單、網域、副本、台股代號 regex |

自動只發生在這條裡：`status` 每次帶輕檢；可自動的才進 `-Apply`；黃的進待裁定；紅的進 `verify` 且 rc1。

## 不是第二條路

| 看起來像另一條 | 實際上 |
| --- | --- |
| `via-ssotadd` | 只打到 bridge 那一格。候選是 PENDING_OPERATOR，不是整體過了 |
| `via-ssot-evolve` | `CGC_MDL065`，寫提案版，正本凍結。它不在 `SSOT_PORT` 裡。提案沒經過 `verify`，不能當成新正則 |
| 預覽裡引用的代號正則 | 某一次快照，不參加判決 |
| 直接打開某一格的檔自己比 | 繞過這扇門。比完也不算過 |

沒跑到 `verify` 且不是紅，VRN 的欄位定義、代號正則、同義字都不當成已定。

這台沒跑 `via-vcgc ssot`，門是 ABSENT。
