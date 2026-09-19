# 批626 · 加速器:掛滿了一棵樹,一次也沒真的用過

操作員令:

> 跑太慢了 請加入25個加速器 所有py檔都加入"…\supportive modules\VeritasCeleritas.py"
> vdf檔都加入網路模組"…\supportive modules\VeritasAegisNexus.py" 之前已經上載 請加入

本批先照這句話去量,量完的結果跟這句話的前提不一樣,所以先把量到的擺出來。

---

## 一 · 先量:橋早就掛完了

容器實跑,正典掃描器 `CGC_MDL124_BridgeSweeper`(git 在冊律 + 批597 凍結夾 + 批402 真外呼判準):

| 掃描 | 範圍 | 已掛 | 缺 | 覆蓋 |
|---|---|---|---|---|
| ACCEL(→ VeritasCeleritas) | functional modules/VDF | 191 | 0 | 100.0% |
| ACCEL | functional modules/VAP | 247 | 0 | 100.0% |
| ACCEL | functional modules/VRN | 318 | 0 | 100.0% |
| ACCEL | supportive modules + 根層 | 1753 | 0 | 100.0% |
| **ACCEL 全樹** | — | **2693** | **0** | **100.0%** |
| NET 真外呼件(→ VeritasAegisNexus) | functional modules/VDF | 28 | 0 | 100.0% |

`[VIA:ACCEL-BRIDGE]` → `VIA_SuperAccel_Module` → `SUP_MDL737` 尾版 → **`VeritasCeleritas.py`**;
`[VIA:NET-BRIDGE]` → `via_net_unified` 尾版 → `SUP_MDL740` → **`VeritasAegisNexus.py`**。
兩條鏈都在,兩邊都沒有可注入的缺口。**「請加入」這件事,批102 / 批115 / 批345 / 批402 已經做完了。**

NET 那一欄另有 163 件被判「非擷取」——去掉註解與字串之後沒有任何網路原語直呼。
例如 `VDF_MDL303` 裡那五處 `yfinance:` 是**資料表裡的字串鍵**,不是呼叫。
給它們掛網路橋是為了綠而綠(零九頭龍),正典掃描器明文拒絕,本批照拒。

### 那 100.0% 是這一批才對的

v0104 掃出來是 `2692/2694 · 99.9%`,缺的 1 支是
`supportive modules/ssot/VIA_Financial_Institution_SSOT_v0100.py` —— **唯讀正典 SSOT**,
而掃描器**不知道有這條律**,照樣把它列進注入計畫;`--apply` 一下就寫進唯讀正本。
v0105 加 `READONLY_CANON`,排除理由直接寫出來。**數字沒變好,是帳記對了**(新律 L95)。

---

## 二 · 那為什麼還是慢:掛了橋 ≠ 用了橋

| 量到的 | 數字 |
|---|---|
| 尾版 .py(L77 排除後) | 1448 |
| 其中持有 ACCEL 橋 | 1426 |
| **橋之後真的呼叫加速器的** | **76(5.3%)** |
| 只掛不用 | 1350 |

覆蓋率量的是「有沒有掛」,報告上只會出現這個數字;**使用率沒有人在量**(LL210)。

### 而且正典那條路是斷的

`SUP_MDL753_VIACommonUtils`(批594 把全樹 17 處 `_cel_submit` 收斂進來的正典)裡:

```
SUP_MDL753._celeritas()  →  None   AttributeError: 'NoneType' object has no attribute '__dict__'
SUP_MDL737.celeritas()   →  模組   _LazyPool 在位
```

差別一行:**`sys.modules[name] = mod` 要在 `exec_module` 之前**。
Celeritas 裡有 dataclass,3.11+ 建類別時會查 `sys.modules[cls.__module__]`;
沒先登記就查到 None。批323 早在 `SUP_MDL737` 修過,批594 收斂時**抄了形狀,漏了那一行**。

後果不是慢一點,是 `cel_submit` **全數退回 `fn(*args, **kw)`——池子一次也沒被用到**,
而 graceful 把它蓋得一聲不響。活樹上吃這支正典的有 `VRN_ENG073`(鏈上的站)、
`VRN_ENG074 v0110/v0111`、`VRN_MDL001_Converter_v0121`、`ENG017/018/023`、`MDL010`、`VIA_LibCanon`。

**v0102 修法**:`_celeritas()` 改成**交給正典 `SUP_MDL737`**(不自己再寫一份=不製造第二把尺),
候選序照 L50(`accelerator/` 那本零 talib 排第一),退路也補上登記那一行;
缺席時把原因留在 `cel_why()`(L87)。自測 **24 檢 OK 24**。

其中第 ⑤ 檢值得單記:v0101 那一檢最後一段是
`... and cel_submit(f, 3, _cel=None) == 6 or cel_submit(f, 3, _cel=None) == ("pool", 6)`。
它綠,是因為 `_celeritas()` **壞著**——永遠回 None,所以永遠直呼回 6。
**那盞燈是靠那個 bug 才亮的**,修好載入器它立刻紅。已改成:池子在位就必須回 Future。

---

## 三 · 真的讓它快:VRN_ENG072 v0136

工作站實錄 `R1-鏈實跑 已跑 579s`(64 件 · 雙法 56)。579 秒在
`triage_page1` / `extract_page1_zones`(fitz)/ `extract_page1_plumber` 這三支,
一件一件序列跑。這三支的形狀很乾淨:**吃一個 Path、回一個 dict、不改模組狀態**——
所以不必動那段兩百行的迴圈本體(動它才是真的危險),先把三支跑完、把答案記住就好。

### 第一版是錯的,量出來才知道

第一版用執行緒池,還特地去拿 Celeritas 的 `thread_budget`——「那才叫用到加速器」。

```
語料 64 件 × 3 頁 · CPU 4 顆
  序列       9.0s   1.00×
  執行緒 4  11.9s   0.76×   ← 比序列還慢
  行程   4   2.4s   3.68×
```

那三支是**純 Python 的 CPU 工**,不是 I/O 等待。GIL 一次只放一條執行緒進去算,
多開只是多付切換與競爭的錢。`thread_budget` 是給等待工用的預算,
**加速器沒有錯,是我把它放在幫不上忙的地方**(新教訓 LL211)。

### 改行程分片之後

```
端到端(FORCE,邏輯庫不短路;24 件 × 3 頁)
  序列(--jobs 1)       4.9s
  行程預熱(auto)       2.6s     1.90×
  sidecar 逐位元組相同  True     ← jobs=1 vs auto · v0135 vs v0136 兩組都同
```

分片走 `subprocess` 而不是 `ProcessPoolExecutor`:後者要把 worker 函式 pickle 過去,
而本引擎常被別人用 `spec_from_file_location` 以臨時模組名載入(`ENG083` 就是),
那個名字在子行程裡不存在;Windows 的 spawn 又會把主模組重跑一遍。
「同一支檔 + 一個動詞 + 一張清單」兩個作業系統同一條路。

**刻意不碰 OCR 車道**:它有預算時鐘與逐件遞減的剩餘預算,平行化會把「剩餘預算」這個概念弄壞。

退路:`--jobs 1` = 完全不預熱,退回 v0135 的行為。
邏輯庫命中的件不預熱(序列根本不會叫那三支,預熱等於燒白工)。
預熱時拋例外的件**不記**——序列這一趟照樣自己算、照樣在原地壞。

自測 **56 檢 OK 56**。

---

## 四 · 順手修掉的三盞假綠

| 位置 | 病 |
|---|---|
| `ENG072 v0135` ⑰ | `_src72.index("else extract_page1_zones(p)")` —— 整支檔裡沒有這一串,唯一一處就是這一行檢查自己。**永遠綠,而且量的是自己**(LL212)。改讀 `inspect.getsource(run)`。 |
| `MDL124 v0104` 收尾 | `f"十檢 OK {10 - len(fails)}"` 寫死。加了第 11 檢它照樣印 10,**新檢不在帳上**(LL213)。 |
| 批626 自己的第一版 | 三檢借上一段的 `tdp` 夾具,而那個 TemporaryDirectory 早關了 → 列表恆空 → 整段跳過。畫面「52 檢 OK 52」,其中三檢根本沒跑(LL214)。改成自備夾具,造不出來報 NODATA。 |

`SUP_MDL753` 的「十六檢」、`ENG072` 抬頭停在 `v0129`,一併改成現場計 / 由檔名取版號。

---

## 五 · 注入器的破口(這個是真的要修)

`via_accel_injector_v0100` / `via_net_injector_v0100`(根層短令 `via-inject` / `via-netinject`)
的 `SKIP_FRAGS` 少了四段。實測 v0100 vs v0101:

| 路徑 | v0100 | v0101 |
|---|---|---|
| `functional modules/VRN/references/intake/…/x.py` | **會寫!** | 排除 |
| `supportive modules/_superseded/old.py` | **會寫!** | 排除 |
| `supportive modules/RetiredEngines/dead.py` | **會寫!** | 排除 |
| `supportive modules/_backup/bak.py` | **會寫!** | 排除 |
| `x/SCOPE_COPY/c.py` | **會寫!** | 排除 |
| `functional modules/VRN/VRN_ENG072_…_v0136.py`(活檔) | 會寫 | 會寫 |

第一列就是**正本零觸碰**那一條:收容正本帶 sha 冊,`--run` 一跑就破。
v0101 把排除判準接到 `SUP_MDL753` 的 **L77 正典排除清單**(`SCAN_EXCLUDE` / `scan_excluded()` /
`frozen_dirs()`),正典不在就**誠實停**,不拿一張比較短的清單代打。

### 一件要操作員裁定的(LL90)

這兩支和 `CGC_MDL124_BridgeSweeper` 做的是**同一件事**。
MDL124 多了 git 在冊律、批597 凍結夾、批402 真外呼判準、批626 唯讀正典排除;
兩支注入器多了 manifest + `--undo`(MDL124 沒有)。
批626 實掃兩邊都已經沒有可注入的缺口,所以這不是「哪一支比較好」,
是「**要不要留兩支**」——那是你的裁定,本批不代裁,只把破口補起來。

---

## 六 · 這一批沒做到的

- **合成語料**。容器裡沒有真報告(73 份 sidecar 是倉裡帶的產物,PDF 本體不在),
  倍率是拿 fitz 現造的 64 件 × 3 頁量的。你那台 CPU 顆數不同、報告密度不同,倍率會不一樣。
  真數字要你跑一次 `via-vrnaudit` 才有。
- **那 1350 支「只掛不用」**。本批只修了正典那條斷掉的路,沒有逐支去接。
  要接哪些、怎麼接,得先有一份「誰真的需要平行」的清單,那是下一批的事。
