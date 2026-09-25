# 2026-09-25f · 正則與同義字只走一條路

操作員令：任何 SSOT REGEX、同義字的自動交互檢查，都要設在單一路徑。沒過，VRN 很多定義又會大亂。

這條路已經在，不另開第二套比對。

```
via-vcgc ssot
  → via-vcgc ssot plan            零寫，只列出來
  → via-vcgc ssot plan -Apply     只把可自動的那幾步交給正主寫，做完再量
  → via-vcgc ssot verify         驗收。紅 = rc1
```

正主在 `CGC_MDL149` v0130 的 `SSOT_PORT`，一格一家，本台不編一條正則、不併一個同義字：

| 格 | 正主 |
| --- | --- |
| hub | `SUP_MDL749_VRNFieldRuleHub`，VRN 欄位規則 |
| bridge | `VRN_ENG088_SsotAdditiveBridge` |
| union | `CGC_MDL176_SynonymUnion`，同義聯集。會丟東西的變更它自己拒寫 |
| regexdict | `CGC_MDL115_SSOTRegexDict` |
| matrix | `CGC_MDL169_VIAStateMatrix` |
| purge | `CGC_MDL177_ChinaBrokerPurge` |
| booksync | `CGC_MDL185_SsotBookSync`：拒絕清單、網域冊、同名副本、四本台股代號 regex 冊 |

自動已經在這三處，不再加一個排程：`via-vcgc status` 每次帶輕檢；可自動的才進 `-Apply`；黃的進待裁定，紅的進 `verify` 且 rc1。

沒過這扇門，VRN 的欄位定義、代號正則、同義字都不當成已定。別處再比一次，就是第二條路，定義會分叉。

這台沒跑 `via-vcgc ssot`，門是 ABSENT。預覽裡引用過的代號正則只是某一次快照，不是這扇門。
