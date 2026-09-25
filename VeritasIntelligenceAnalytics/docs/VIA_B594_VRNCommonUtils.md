# 批594 — VRN 前幾大債:遷了 13 支,**擋下 17 處**

操作員令:`VRN 前十大債 繼續整併`

---

## 一、量:170 尾版 / 68 處定義 / **18 個行為群**

| 函式 | 處 | 群 | 差在哪 |
|---|---|---|---|
| `_cel_submit` | 17 | 4 | 有沒有**第二層退路**(`_LazyPool` 之後再試 `_CEL.submit`) |
| `_si` | 17 | 4 | 有一群用 **bare `except:`** |
| `_hash8` | 14 | 2 | 有一處**根本沒有 xxhash 分支** |
| `_jwrite` | 14 | 3 | mkdir / default / 吞不吞例外 |
| `_argval` | 3 | 2 | 回 `Path` vs 回 str,其中一版**有狀態** |
| `_num` | 2 | 2 | 一版是類別的 `@staticmethod` |

---

## 二、本批最重要的事:**17 處在出貨前被擋下**

遷移腳本先把 8 支判成 `BLOCKED`(說注入點之前沒有 `_CEL`)。我去看檔案,發現兩件事:

```python
_CEL: Any = None;  _CEL_OK: bool = False     # 227 行:import 時是 None / False
def _boot():
    global _CEL, _CEL_OK                      # 240 行:開機函式**事後**才填真值
```

1. `_CEL: Any = None` 是 **`AnnAssign`** 不是 `Assign`,我的偵測器認不到 ——
   **`BLOCKED` 的是尺,不是檔。**
2. **更重要的:就算偵測器認到了,遷過去也是錯的。**
   原版 `_cel_submit` 是**呼叫時**才讀 `_CEL_OK`;做成模組層綁定,會在 **import 當下**
   把 `False` 凍住,開機之後**永遠走不到 Celeritas 的池子** ——
   **而且不會報錯,只是變慢**,是最難發現的那一種。

這跟批593 的可變預設值是**同一族**:**早綁了一個本來要晚讀的東西。**

> **L76 擴充**:不只是可變的「預設值」。凡是**本來要在呼叫時才讀**的東西,
> 都不得做成模組層綁定。判準是:**這個綁定式裡的每一個名字,
> 是不是在 import 當下就有最終值?** 有任何一個是事後才填的
> (`global` 賦值 / boot 函式 / 延遲初始化),就不得做成綁定。

17 處具名不遷,並用合成語料把陷阱**演進自測**(檢②之二)。

**批593 是出貨後才炸;批594 是出貨前擋下。** 這是這一批真正的收穫。

---

## 三、其他不能吃掉的差異

| | |
|---|---|
| `_si` 有一群是 **bare `except:`** | 連 `KeyboardInterrupt` / `SystemExit` 都吞 —— import 一個會 `sys.exit()` 的模組時會被當成「沒有這個模組」。**那是潛在缺陷不是風格**。正典給 `catch_all=` 等價遷移,**不代改**(LL90)。 |
| `generic_layout_engine.hash8` **沒有 xxhash 分支** | 併成預設值,等於在裝了 xxhash 的機器上**悄悄改掉它產生的所有 id**。加 `prefer_xxhash=False` 保住。 |
| 有狀態的那版 `_argval` | 讀寫模組層的 `_FLAG_OK_BARE` / `_BARE_FLAG_SEEN`,搬出來就不是同一件事。 |
| `close(self)` / `export_csv(self, out_dir)` | 是**類別方法**,各有各的欄位與表頭,本來就不是同一件事。 |

---

## 四、`_jwrite` 直接接上一批的正典

`_jwrite` 14 處三群,底下**直接走批592 的 `SUP_MDL752`**,不另造一支 JSON 寫法。
零損失:三群**逐群比位元組全同**。

這是整併該有的樣子 —— **新的正典不重新發明上一個正典解過的問題。**

---

## 五、我自己踩了兩條核心律 —— 寫檔的腳本沒有排除清單

commit 前 `git status` 才看到,遷移腳本掃 `functional modules/VRN` 整棵子樹,改到:

| | |
|---|---|
| `references/intake/GenericLayoutEngine_.../generic_layout_engine.py` | **收容正本,零觸碰** |
| `_superseded/20260804/` 五支 | **退役件不是活樹** |

全部 `git checkout` 還原,收容夾 diff 為空。

**這不是尺量錯,是我根本沒給尺邊界。** 前四批(590–593)遷 registry 時剛好沒有 intake 子夾,
一路沒事 —— **那叫運氣,不叫紀律**。→ **L77 掃描根一律帶排除清單律**

我補了一道 `via-govaudit intake` 閘(逐夾比 sha):

```
58 夾   GREEN 23 · RED 0 · UNKEPT 10 · NODATA 25
```

`RED` 只給「檔案在、sha 對不上」—— 那才叫正本被改;
原件沒留(多半是上傳的 `.zip` 解開後沒留)= `UNKEPT`;沒有可比的 sha = `NODATA`。
**兩者都不算綠。**

> **但要講清楚:這道閘擋不下我剛才那一筆。**
> 那個收容夾**沒有 manifest**,落在 `NODATA 25` 裡。
> 閘的價值是把那 25 夾**具名列出來、不算綠**;真正擋下我的是排除清單。
> **不能把「我補了閘」講成「以後不會再發生」。**

做那道閘時又踩了一次 **L71**:`source_path` 是操作員工作站的 Windows 絕對路徑,
Linux 上取 `.name` 拿到整串 → 14 夾全判假紅;正規化分隔符後 `RED 14→0`。

---

## 六、結果

```
遷 **7 支活樹尾版**(_si / _hash8 / _jwrite / _argval / _num)   逐支冒煙 BAD/EXC 0
(原本 13 支,扣掉還原的 6 支:收容正本 1 · 退役件 5)
具名不遷 19 處(_cel_submit 17 · 有狀態 _argval 1 · staticmethod _num 1)
sha 凍結快照 8 支                                        不得改
全格 246 站   OK 244 · FAIL 0 · SKIP 2
```

## 七、登錄(L70:沒有動任何 `.ps1`)

- `SUP_MDL753_VIACommonUtils_v0100.py` —— VRN 共用小工具正典,十四檢
- 13 支 VRN 尾版就地改吃正典綁定
- `CGC_MDL164_GovernanceCompletenessAudit_v0106.py` —— +`intake` 收容正本零觸碰閘;二十一→二十二檢
- `CGC_MDL064_SelftestGrid_v0361.py` —— +VRN 共用小工具正典站;制度健全度站 二十一→二十二檢
- `VIA_Policy_Laws_SSOT_v0100.json` —— **L76 擴充** · **L77** · **LL148** · **LL149**(律 74→75 · 課 147→149)
- `VIA_AutoCode_Registry_v0100.json` —— 台帳 1163→1167
