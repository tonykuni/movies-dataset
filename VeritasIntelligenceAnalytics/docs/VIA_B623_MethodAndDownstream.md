# 批623:方法論存檔 · SSOT 上下貫通 · 兩盞我自己造的假紅燈

操作員令:

> 整理環境若正確則將方法論導入VIA存檔
> VRN若正確則實測驗證: 測試樣本報告路徑為 C:\測試樣本報告  測完後AUDIT會換一批PDF
> SSOT 同義字 REGEX隨時新增更新上下自動檢視  邊做邊修正更新

---

## 一 · 環境確實正確了

你那一跑的證據:

```
via-envgov resume --approve → APPLIED · 跑 42 · 失敗 0
via-rungate run --family 'vdf,vrn,vap'
  vrn  GREEN 8/8   ← VRN 正確
  vap  GREEN 8/8   ← VAP_ENG015 從 ENV_BROKEN 轉 OK(pandas/pyarrow/seaborn 裝進去了)
  vdf  RED         ← 紅在 VDF_ENG088 的**資料面**,不是環境面
```

所以 ①「環境若正確」成立,② 「VRN 若正確」也成立。

### 方法論存檔

`VIA_EnvRestore_Methodology_SSOT_v0100.json` —— 五步 · 五條紅線 · L19 豁免界線。

| 步 | 做什麼 | 為什麼 |
|---|---|---|
| ① 找 | 前一次成功的逐境 LKGC lock | 「成功過」必須是**有紀錄的事實**,不是印象 |
| ② 還原 | `uv pip install -r <lock>` | **只增不減**;`sync` 會移除=破壞,候裁 |
| ③ 新增 | 走正典 `tools_plan` | 還原只回到過去;往前得看冊(零 Hydra) |
| ④ 衝突檢查 | `uv pip install --dry-run` | **只有 CLEAN 才准裝**;uv 不在=NOT_RUN 不猜 |
| ⑤ 裝 | `via-envgov resume --approve` | 指令你自己打;同意閘不代設 |

冊上同時寫明**何時不適用**:直譯器本身換版/壞掉是 `via-rebuild` 的事,不是補件的事。
L19 豁免寫明界線與但書:**這是這一種死結的出口,不是 L19 普遍可以繞過**。

## 二 · SSOT 上下貫通檢

「冊上加一個同義字,不等於下游吃得到。」`SUP_MDL749 v0106` 新增 `downstream`:

```
$ via-vrnrules downstream
=== SSOT 上下貫通檢 · 供應 17 · 活消費者 3 ===
  [計] USED 6 · INTERNAL 11 · ORPHAN 0
  活消費者:VRN_ENG073_v0129 · VRN_ENG074_v0111 · VRN_ENG083_v0100
```

三態:`USED`(外部引擎叫)/ `INTERNAL`(樞紐自己叫)/ `ORPHAN`(都沒有)。
**ORPHAN 0 —— 鏈是通的。**自測 20 → **21 檢**,格子站名同步。

## 三 · 兩盞我自己造的假紅燈(同一支檢,連造兩盞)

| 版 | 報什麼 | 錯在哪 |
|---|---|---|
| 第一版 | 22 供應 / **14 ORPHAN** | 把 `drift`/`harvest`/`status` 這些**你自己要打的 CLI 動詞**算成供應函式 |
| 第二版 | 17 供應 / **11 ORPHAN** | 把 `matchers`/`repair` 這種**樞紐自己內部在用**的零件算成 ORPHAN |
| 第三版 | 17 供應 / **ORPHAN 0** | 三態分開,才是真的 |

前兩版會對著一條**健康的鏈**亮 14 盞、11 盞紅燈。
動詞清單的修法也不是手抄(手抄一定會過期),是從 argparse 的 `choices=` **量出來**。

> 規矩:新造一把尺,先問它**會不會把正常的東西判成壞的**;
> 「找不到呼叫」這種否定式判準最會生假紅。

## 四 · 對著紅燈說綠燈

你那一跑的最後一行:

```
[via-rungate] 判定 RED · 存證 … · 三族皆以家族境 python 真跑綠燈
```

**判定 RED,尾巴說三族都綠。**那句是寫死的,條件只看 `rep["next"]` 空不空,**根本不看裁決**
—— 「沒有可自動修的次步」被說成「一切都好」。`CGC_MDL137 v0108` 改成看裁決本身。

## 五 · 你的 vdf RED 是什麼

```
[FAIL] vdf VDF_ENG088_ConsensusFusionBridge_v0101.py
  ② 誠實四態:0 列與缺來源不是同一件事(L57)… (NODATA · consensus_daily=792 · cons…)
```

那一檢**自己說**該判 NODATA,實際卻走到 FAIL,而且 `consensus_daily=792`
—— 你的庫**有 792 列**,不是空的。容器這邊是 0 列,所以我從來沒看過這條路。
這是下一批的事,**我不會憑一行截斷的訊息猜它**;下次請把那一行完整貼回來。

## 六 · VRN 實測:指令早就有,不另造

`C:\測試樣本報告` 這條路批569 就建好了(`VRN_ENG083_VerifiedMatrix`):

```powershell
via-vrnmatrix run --in "C:\測試樣本報告"
```

換一批 PDF 再跑同一句即可。**我沒有造新件** —— 造一支新的只會是第二顆頭。

## 登錄

* 課 202(+LL201/LL202)· 台帳 1227
* 新件:`VIA_EnvRestore_Methodology_SSOT_v0100.json` · `SUP_MDL749_VRNFieldRuleHub_v0106.py` ·
  `CGC_MDL137_RunGate_v0108.py` · `CGC_MDL064_SelftestGrid_v0378.py`(站名 20→21 檢)
