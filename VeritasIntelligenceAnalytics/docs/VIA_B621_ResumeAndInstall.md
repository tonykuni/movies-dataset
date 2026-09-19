# 批621:擋住的那一件事,正是解開它的那一件事

操作員令(原話):

> 找前一個成功安裝環境工具布局 根據歷史紀錄還原後在把沒安裝的工具經過衝突檢查後無於建立新增計畫
> 依計畫執行安裝 不測是因為之前已測試過

---

## 一 · 先講他卡在哪:L19 把自己鎖死了

`via-envgov apply --approve` 連跑三次,每一次都是:

```
執行:跑 0 OK 0 FAIL 0 SKIP 0 BLOCKED 136
零動作:授權了但一段都沒跑——L19:RunGate 判定 YELLOW(非 GREEN);修綠再裝(整批擋下)
```

而 RunGate 判 YELLOW 的**唯一原因**是:

```
YELLOW  vap   必要庫缺:pandas
```

**要綠得先裝,要裝得先綠。**閘沒有壞,是閘**沒有出口**。
更糟的是輸出把它講成「修綠再裝」,聽起來像他少做了一步 —— 其實那一步在這個狀態下不存在。

## 二 · 開一條界線寫死的窄路,而不是把閘拆掉

`resume` 本來就有 ①②(批602 的逐境 LKGC:前次成功的布局 + 只增不減的還原令),
缺的是 ③ 衝突檢查 和 ④ 執行。v0113 補上:

| 步 | 做什麼 | 怎麼做 |
|---|---|---|
| ① 找 | 前次成功的逐境紀錄 | `LKGC_latest.json` 的 per-env lock |
| ② 還原 | 照那份 lock 補齊 | `uv pip install -r <lock>` —— **只增不減** |
| ③ 新增 | 工具冊有、境裡沒有的件 | 正典 `tools_plan`(不自己重查一遍冊) |
| ③′ 衝突檢查 | 還原集 + 新增集一起解析 | `uv pip install --dry-run` —— **零安裝** |
| ④ 裝 | 只裝衝突檢查 CLEAN 的 | `resume --approve` |

### L19 具名豁免 —— 理由印在臉上

```
── ④ 執行安裝(L19 具名豁免;豁免必附理由 L87)──
   理由:L19 要 RunGate 綠才准裝,而 RunGate 黃的原因就是這些件沒裝
        ——擋住的那一件事正是解開它的那一件事(死結)。
   界線:只跑 `uv pip install`(只增不減)· 還原集來自前次成功的逐境 lock ·
        新增集只裝衝突檢查 CLEAN 的 · 破壞段(境重建/改名/退役)一律不進這支。
   **不複驗**:操作員裁定「之前已測試過」→ 本次只做衝突檢查,不做三輪複驗。
```

**同意閘照樣不代設**:`VIA_NET_CONSENT` 沒開就是 `BLOCKED_CONSENT` 零動作。
指令是他自己打的,我沒有在任何地方代裝。

### 「不複驗」寫在資料裡,不是靠沒提到

每一筆結果都帶:

```json
{"env": "via_vap_312", "state": "OK", "reverified": false,
 "reverify_why": "操作員裁定「之前已測試過」→ 本次只做衝突檢查,不做三輪複驗(L87:豁免附理由)"}
```

如果只印「裝好了」,三天後沒有人分得出這次是**驗過**還是**跳過驗**。

### 四道紅線,沙盒各撞一次

容器裡只有 BASE 而且是紅的,逐境 LKGC 永遠空 —— 實樹證不出這條路(L83)。
所以整條在沙盒裡合成走一次:

```
未授權=零動作 · 無同意=BLOCKED_CONSENT · CONFLICT 的境 SKIP 不裝 ·
無待裝件=SKIP_EMPTY · 指令裡零 sync/uninstall/remove · uv 缺=NOT_RUN 不猜
```

自測 49 → **50 檢**。

---

## 三 · 順帶:批620 我自己造的一個截斷

他的實錄印出 `[🔴 名實不符] 9 境`,底下只列了 6 列,全是 `NAME_LIES`。
v0112 寫的是 `bad_id[:6]`,而 `bad_id` 是**掃描順序** —— 萬一有一列 `ABI_MISMATCH`
排在第 7 位,它在畫面上等於不存在,而那正是唯一一種「裝更多件只會更糟」的狀態。
而且截了就截了,連「還有 3 境沒列」都沒說。

v0113 改成依嚴重度排(`ABI_MISMATCH > HOME_DRIFT > NAME_LIES`),並印出被截掉的逐態計數。

---

## 四 · 他的實錄順便證實了批620 的一半

```
BASE 身分:3.13.7 @ C:\Python313\python.exe · 件 692 · base · base(本解譯器)
[🔴 名實不符] 9 境
  NAME_LIES  camelot_311 / paddle_311 / via_camelot_311 / via_html_312 / via_paddle_311 / via_tools_312
```

BASE 身分那一行照出來了,名實不符也照出來了 —— **9 境的名字全在騙人**。

但**沒有一列是 `ABI_MISMATCH`**。也就是說那些境裡的原生輪子標籤跟 3.13 是對得上的:
名字過期了,ABI 沒有錯位。我在批620 把 `pyarrow no attribute '__version__'`
推論成 ABI 錯位 —— **那個推論到目前為止沒有被證實**;症狀吻合,但尺沒照到。
`via_vap_312` 沒有出現在名實不符清單裡,所以 pyarrow 那一幕要另外查。

---

## 怎麼用

```powershell
$env:VIA_NET_CONSENT = 'YES'      # 同意閘 —— 你的手,我不代設
via-envgov resume                 # 唯讀:①②③ 全出,衝突檢查照跑,什麼都不裝
via-envgov resume --approve       # ④ 依計畫裝(只增不減;只裝 CLEAN)
via-rungate run --family vdf,vrn,vap   # 要驗再跑(本支不複驗)
```

## 登錄

* 法 92 · 課 197(+LL195/LL196/LL197)· 台帳 1221
* 新件:`CGC_MDL135_EnvGovernance_v0113.py` · `CGC_MDL064_SelftestGrid_v0375.py`(站名 49→50 檢)
