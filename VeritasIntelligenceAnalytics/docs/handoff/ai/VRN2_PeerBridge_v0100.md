# VRN2_PeerBridge v0100 —— VRN-2 為主,缺的功能向 VRN-1 借來用

操作員 2026-11-08:「VRN-2為主 缺少功能自VRN-1抓來用 等VRN-2功能完美才去整合 全部自動完成」。

## 一、動手前查到的事(不是推定)

| 查什麼 | 實際狀況 |
|---|---|
| VRN-1 有沒有橋 | **有** —— `functional modules/VRN/engine/VRN_ToolBridge_v0100.py`,協定乾淨:工具冊(相對路徑 + sha256)→ `borrow(tool_id)` 依路徑載入並驗 sha256 |
| VRN-1 想借什麼 | 寫死兩項:`BORROWS = ("section.near", "ocr.image")` |
| VRN-1 去哪找 VRN-2 的工具冊 | `VIA_Reports/vrn2/tools/VRN2_ToolManifest_v0100.json` |
| **VRN-2 這側有沒有橋** | **沒有。倉內一支都沒有。** 而且 VRN-1 要找的那本冊在 `VIA_Reports/**` —— 本倉**從不提交**那個夾,所以那本冊是臨時的、倉裡根本不存在 |

結論:**VRN-2 原本借不到任何東西,VRN-1 也借不到 VRN-2 的東西**。這是第一個要補的洞,
本支就是補它。

## 二、能力差異矩陣(由程式算,不手寫)

拿 VRN-1 的 23 個能力逐項去 VRN-2 的 650 個檔裡找。**MATCH 一律附證據檔**;
檔名沒命中就再掃一次說明,掃到算 `REVIEW`(交操作員判),掃不到才算 `GAP`。

**MATCH 14 · REVIEW 0 · GAP 9**

### VRN-2 缺、VRN-1 有的 9 項(都已實測借得到)

| 能力 | VRN-1 引擎 | 它做什麼 | 實借 sha256 |
|---|---|---|---|
| `prove.lock` | `VRN_Lock_v0100.py` | 證明對的就鎖住,後來改壞它的變更要被拒絕 | `c817ed86b8d92dcf…` |
| `truth.matrix` | `VRN_TruthMatrix_v0100.py` | 母系統第一頁真值矩陣(一報告一列) | `e8f38aa47994f71b…` |
| `run.cache` | `VRN_RunCache_v0100.py` | 一輪讀過的放 TEMP,輸入沒變就重用 | `1d5176cfe2d67b4a…` |
| `temp.store` | `VRN_TempStore_v0100.py` | TEMP 分擔記憶體,刪除規則寫明 | `e5d171b4b95083fc…` |
| `focus.only` | `VRN_Focus_v0100.py` | 只處理操作員指名的那些 | `2a3a1654116f7f37…` |
| `ast.id` | `VRN_AstId_v0100.py` | 每個模組 / 類 / 函式都有號、類別與說明 | `7348bc0534731a0d…` |
| `dataframe.headers` | `VRN_DataFrame_v0100.py` | 每份輸出都是 DataFrame 並對表頭核對 | `4040db7df2bd9db7…` |
| `ticker.record` | `VRN_TickerRecord_v0100.py` | 4 位代碼為鍵,一股一筆 15 欄 | `5c24766c0bd0f2f9…` |
| `book.check` | `VRN_BookCheck_v0100.py` | 別場會話收來的冊當測試儀器 | `73089385b6fd5478…` |

**9/9 實際借到**(不是「理論上可以借」):每支都真的 `borrow` 過,驗了 sha256、載入成功、
公開名數得出來(24–49 個)。

### VRN-2 已有的 14 項(附證據檔)

`output.verify`←ENG083 VerifiedMatrix · `pivot.db`←ENG081 ParquetMainDB · `ocr.image`←ENG057 ScanOcrRescue ·
`page.regions`←ENG072 FirstPageText · `title.trim`←ENG062 SummarizerV1 · `ticker.master`←VRN2 MarketFetch ·
`firstpage.engine`←FirstPageEngine v0102 · `report.db`←ENG073 ReportStructuredDB · `autotest.loop`←ENG076 RegressionGate ·
`lexicon.valuation`←ENG063 Lexicon · `evidence.core`←VRN_Evidence_Core · `local.db`←VRN2 VDFBridge ·
`run.matrix`←ENG079 ControlTowerDashboard · `panorama.probe`←VRN_PanoramaProbe

## 三、VRN-2 自己的工具冊:4/4 可借出

VRN-1 指名要借的兩項,一開始判成 `NO_ENTRY` —— 查下去發現**不是它們壞,是我的入口函式名猜錯**:
`ENG049` 與 `ENG057` 都是**薄尾版本**,公開面靠 PEP 562 `__getattr__` 轉接給前版本體,
AST 只看得到 `main`。入口改認 `main`,並在冊上標 `forwards_dynamically: true` ——
**AST 看不到被動態轉接的那些名字,就不假裝列舉**。

| 工具 id | 狀態 | 檔 | 入口 |
|---|---|---|---|
| `section.near` | LENDABLE | `VRN_ENG049_ContentReconcile_v0103.py` | `main`(其餘動態轉接) |
| `ocr.image` | LENDABLE | `VRN_ENG057_ScanOcrRescue_v0105.py` | `main`(其餘動態轉接) |
| `table.omni` | LENDABLE | `VRN_ENG058_TableOmni_v0105.py` | `main` |
| `verified.matrix` | LENDABLE | `VRN_ENG083_VerifiedMatrix_v0120.py` | `main` |

工具冊寫兩份、內容相同:倉內可提交正本 `functional modules/VRN/ssot/VRN2_ToolManifest_v0100.json`,
加上 VRN-1 寫死會去找的 `VIA_Reports/vrn2/tools/…`(那份不提交,每次重生)。
**VRN-1 是另一個系統的倉,我不改它去配合我**,所以由我這側多寫一份。

## 四、「等 VRN-2 功能完美才去整合」—— 這是閘,不是承諾

`integrate` 動詞**會拒絕執行**,只要 readiness 不綠:

```
$ VRN2_PeerBridge_v0100.py integrate
[拒絕整合] 整合就緒燈 YELLOW —— 操作員令「等 VRN-2 功能完美才去整合」。
  擋住的原因:VRN-2 仍有 9 項能力缺口(GAP)
[下一步] 先把 GAP 補完、REVIEW 交操作員裁,readiness 轉綠後再跑 integrate。
rc = 1
```

readiness 轉綠的條件(全部要成立):GAP 0 · REVIEW 0 · 工具冊 4/4 可借出 · 找得到 VRN-1。
現在是 **YELLOW**,只剩 GAP 9 那一條。用程式擋,不靠我記得。

## 五、對 VRN-1 只讀 —— 查證過,不是宣稱

* `borrow` 用 `sys.dont_write_bytecode = True` 包住載入 → **不在 VRN-1 的夾裡留位元碼**。
* 實查:VRN-1 的 `engine/__pycache__` 確實存在,但裡面是 **2026-10-20 的 cpython-312**,
  而本容器是 **Python 3.13.16**;我借的 9 支裡**一支都沒有 .pyc**。
  全倉搜 `*.cpython-313*.pyc` → **0 個**。`git status` → **乾淨**。
* 借到的工具**只在記憶體用,不複製 VRN-1 的檔進本倉** —— 複製就變兩份正本,一定會漂。

## 六、開發中被自己抓到的兩件事

1. **效能缺陷(不是調參)**:差異矩陣原本對每個沒命中的能力都重掃全樹並剖析
   (650 檔 × 9 缺口 × 2 關鍵詞),`all` 又跑三遍矩陣 → **實測直接吃掉 120 秒逾時**。
   改成整輪只建一次索引、說明索引只在真有需要時才建:**6.5 秒**。補兩個迴歸測
   (每檔最多讀一次 · 第二次完全走快取 0 次讀檔)。
2. **自測的期待寫錯**(不是程式錯):我斷言「假樹下找不到 VRN-1」,但 `find_vrn1` 會看
   上一層的鄰居,而夾具剛好把假 VRN-1 放在那裡 —— 它**找到是對的**。改成三段測:
   真的沒鄰居 → None;鄰居在上一層 → 找到;`VIA_VRN1_ROOT` 指定優先。

## 七、怎麼跑

```bash
cd VeritasIntelligenceAnalytics
python3 "functional modules/VRN/VRN2_PeerBridge_v0100.py" peer          # 找 VRN-1(只讀)
python3 "functional modules/VRN/VRN2_PeerBridge_v0100.py" gap           # 能力差異矩陣
python3 "functional modules/VRN/VRN2_PeerBridge_v0100.py" borrow ast.id # 實借一支
python3 "functional modules/VRN/VRN2_PeerBridge_v0100.py" manifest --apply
python3 "functional modules/VRN/VRN2_PeerBridge_v0100.py" fill --apply
python3 "functional modules/VRN/VRN2_PeerBridge_v0100.py" readiness     # 整合就緒燈
python3 "functional modules/VRN/VRN2_PeerBridge_v0100.py" integrate     # 不綠就拒絕
python3 "functional modules/VRN/VRN2_PeerBridge_v0100.py" --selftest    # 33/33
```

VRN-1 不在預設位置時設 `VIA_VRN1_ROOT`。

## 八、照實說清楚:本輪**沒有**做什麼

* **沒有整合。** 操作員說「等 VRN-2 功能完美才去整合」,而 readiness 是 YELLOW,
  所以 `integrate` 被自己的閘擋下。整合要等 GAP 9 補完,而且整合範圍(冊 / 號 / 入口 / U/I
  各自怎麼併)要操作員另下令 —— 我不自己決定那個範圍。
* **沒有把 9 支 VRN-1 引擎複製進 VRN-2。** 借用是執行期載入,不是搬檔。要把某項能力變成
  VRN-2 自己的,得在 VRN-2 側寫自己的實作(另一輪的事),不是把別人的檔搬過來。
* **沒有改 VRN-1 任何東西。**

五系統對等獨立不變(L120 / L123)。
