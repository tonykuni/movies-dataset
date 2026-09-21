# 批671 · 先敲門再問話 —— 一把尺在同一天同時造出假紅與假綠

操作員令:「將 VRN 實測完畢」。
做法:CGC_MDL172_VRNChainRunner —— **鏈表不寫死**,直接讀批665 已覆核的六層冊
(`VIA_VRN_LogicArchitecture_SSOT_v0100.json`,44 節點),冊就是鏈。
跑法照資料流的形狀:**層間依序、層內並行**。

第一回量出來是這樣:

| 態 | 數 |
|---|---|
| GREEN | 37 |
| RED | 4 |
| GATED | 1 |
| NODATA | 4 |

然後我逐支去看那四盞紅。**四盞裡沒有一盞是真紅。**

---

## 一 · LL317:先敲門再問話

`VRN_ENG057_ScanOcrRescue` / `VRN_ENG056_PdfForensics` / `VRN_ENG052_DocxEngine`
這三支**根本沒有「自測」這扇門**。我遞過去的 `--selftest` 被它們當成
檔名樣式吃進去,然後它們很誠實地回「收件夾無匹配」,rc=1。
於是我的尺說:紅燈。

更傷的是反方向。`VRN_ENG050_ContentStore` 一樣沒有門,`--selftest`
被吃掉之後它跑了**自己的預設動作**(列出 upsert 計畫),rc=0。
於是我的尺說:綠燈。

同一把尺,同一天,兩個方向同時錯。
判錯的紅燈和假綠一樣傷——紅的那邊會有人去修一支沒有壞的引擎,
綠的那邊會有人以為量過了。

**修法:量之前先問「這支到底有沒有這扇門」。**
走 AST(LL311:寫 regex 去讀 code 永遠會在跳脫上斷),
找一個**字面值剛好等於 `--selftest`** 的 Constant——
`add_argument("--selftest")`、`"--selftest" in sys.argv`、
`argv[1] == "--selftest"`、`{"--selftest": ...}` 四種寫法一次收齊。
沒有門就**不敲**:記 NODATA,並說出「它沒有門」。
沒敲過的牆,回音不是綠也不是紅,是你自己的聲音。

量到的結果:44 個節點裡 **12 支沒有自測門**。
這不是缺陷清單,是**誠實分母**(L57):VRN 這條鏈現在只有 32/44 量得到。

| 沒有自測門的 12 支 |
|---|
| SUP_MDL030_VISVRNTickerFilenameSSOT · SUP_MDL015_VISVRNBrokerAliasFullList |
| VRN_ENG017_MDL004OCRFetchingPDFTable · VRN_ENG018_MDL005OCRFetchingPDFText |
| VRN_ENG023_MDL011DailyFetcher · VRN_ENG049_ContentReconcile |
| VRN_ENG050_ContentStore · VRN_ENG052_DocxEngine · VRN_ENG055_OfficeMerge |
| VRN_ENG056_PdfForensics · VRN_ENG057_ScanOcrRescue · VRN_ENG062_SummarizerV1 |

下一步(L92 哨兵抓到就要給得出下一步):逐支補 `--selftest` 門,
或在冊上標免測**並附理由**(L87 豁免必附理由)。**不准**用「它一直都這樣」當理由。

---

## 二 · LL318:冊記的是當時的尾版,不是永遠的尾版

第四盞紅是 `VRN_ENG059_GapMultirescue`:
輸出印「[計] 4/4 檢通過」,rc 卻是 **-6**(`terminate called without an active exception`,C++ abort)。

單跑三次,rc 全 0。**只有在鏈裡才會紅。**
4 路併發咬 12 跑,壞 2 次:一次 `pyarrow.lib.ArrowInvalid: Could not open Parquet input source '<Buffer>'`,一次 abort。

根因(LL319,見下)修掉,做成 `v0101`。**再量,還是紅。**

因為冊上那一行釘著 `..._v0100.py`。鏈照著冊去敲,
敲到的是**我剛剛修好那支的前一版**。

尾版律(最新 `_vNNNN` 為準)在這裡不是偏好,是「**你到底量到誰**」的問題。
修法:照冊找檔,但用 glob 解析到同名家族的尾版;
冊落後時**不偷偷換掉**——把「冊 v0100 · 樹 v0101」印在那一格的註記上。
冊與樹的落差要看得見,不是補掉。

---

## 三 · LL319:自測不准跟別人共用暫存

`VRN_ENG059` v0100 的自測把兩個 parquet 落在
`VIA_Reports/rescue_runs/selftest_tmp/t5.parquet` —— 固定、共用、跨行程同一個檔。

單跑當然綠:一次只有一個人在寫。
可是鏈是**層內並行**的。兩個行程同時寫同一個檔,pyarrow 讀到寫到一半的檔就會炸,
而且它是在**四檢全部印完 PASS 之後**、關門的時候才死。
輸出說通過,rc 說死了——這種壞法最難查。

第一版修法:改用 `tempfile.TemporaryDirectory()`。併發 20 跑,還是壞 1 次。
**沒修乾淨。** 再想一次:那四檢裡**沒有一檢是在問 pyarrow 寫不寫得出檔**——
繞那一圈只是把 pyarrow 的關門順序也一起賭進來。

第二版修法:自測**整個不碰 parquet**。併發 32 跑,非零 0。

> 自測要測的是**這支的邏輯**,不是別人的關門順序。

---

## 四 · LL320:拿同一組字面量跟自己比,是一個永遠為真的檢

順手翻 ENG059 的第四檢,原文是:

```python
("終局四態冊", {"RESOLVED", "PURE_TEXT", "SCAN_RESCUE_CANDIDATE", "UNRESOLVED"} ==
              {"RESOLVED", "PURE_TEXT", "SCAN_RESCUE_CANDIDATE", "UNRESOLVED"})
```

左邊等於右邊,一個字不差。**它永遠是 PASS。**
四檢裡有一檢從來沒測過任何東西,而它一直在報「4/4 檢通過」。

修法:立一個出處 `FINAL_STATES`(L30),
自測用 AST 讀自己這份原始碼,把**實際會被吐出去**的終局字串收齊,跟 `FINAL_STATES` 對。
多一個少一個都會敗。

負向驗證(批670 的教訓:負向測試要先證明它咬得住):
注入第五態 `FIFTH_STATE` → `rc=1`、`3/4 檢通過`、該檢 FAIL。**咬得住。**

---

## 五 · 修完之後的誠實態

| 態 | 數 | 說明 |
|---|---|---|
| GREEN | 33 | 有門、敲過、rc0 |
| NODATA | 12 | **沒有自測門**——量不到,不是壞掉 |
| GATED | 1 | 網路工具掛載:同意閘未開。**AI 永不代設** |
| RED | 0 | |
| ABSENT | 0 | |

→ `rc=4 GATED`。

引擎會跑跟資料是對的是兩件事,所以同一頁的第二段是資料:
研報 81 × 欄 7 的逐列舉證(ticker / report_date / broker / rating / target_price /
upside_calc / analyst_names),其中 `upside_calc` 只有 2 綠、51 NODATA、28 YELLOW——
**一個全綠如果庫裡 0 列,那個綠沒有意義。**

---

## 六 · 四條新律

- **LL317** 拿一個動詞去問每一支之前,先問「它有沒有這扇門」。沒敲過的牆,回音是你自己的聲音。
- **LL318** 冊記的是**當時的**尾版。修好新版之後照冊去敲,敲到的是前一版;落差要印出來,不是補掉。
- **LL319** 自測不准跟別人共用暫存。固定路徑在層內並行時會被兩個行程同時寫,而且會在「全部 PASS」之後才死。
- **LL320** `{A,B,C,D} == {A,B,C,D}` 是一個永遠為真的檢。檢要有東西可以咬,咬不住的檢是在替你數數,不是在替你把關。
