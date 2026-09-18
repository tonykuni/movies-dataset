# 批597 — 全樹導入加速器/網路工具 · VDF 三庫整併 · 2023-07-01 起增量缺口實測

操作員令三件:
1. 全部 PY 檔案導入加速器 `VeritasCeleritas.py` 與網路工具 `VeritasAegisNexus.py`
2. 整合好 VDF 的參數庫 · 因子庫 · 邏輯庫
3. 實測擷取 2023-07-01 起到最新的增量,到目前的資料庫

---

## 一、全樹導入(做完,而且鏈是實證的)

| 系 | 橋 | 導入前 | 導入後 |
|---|---|---|---|
| VDF | ACCEL | 184/189 | **189/189 100%** |
| VRN | ACCEL | 280/312 | **312/312 100%** |
| VAP | ACCEL | 247/247 | 247/247 100% |
| supportive | ACCEL | 1689/1715 | **1715/1715 100%** |
| VDF | NET(真擷取檔) | 28/28 | **28/28 100%** |

注入 **63 檔**(VDF 5 · VRN 32 · supportive 26)。

**跑之前先驗 L77。** BridgeSweeper 是會寫檔的腳本,所以先拿它**自己的** `_excluded()`
去問風險集合:`_superseded` 缺橋 **0 支**、`_sha` 缺橋 2 支但**兩支都被它排除**。
跑完再用 `git status` 逐檔複驗:63 檔全是 `.py`,**零 L77 違規**,63 支全數編譯通過。

**鏈是實測的不是文字**:

```
CANONICAL = SUP_MDL737_SuperAccelModule_v0104.py
celeritas() →  module .../supportive modules/VeritasCeleritas.py
via_net_unified_v0101 → SUP_MDL740_NetUnified_v0113 → VeritasAegisNexus
```

**更正一個我自己量錯的尺**:`--subsystems` 報「VDF/net 181/189(95.8%)」是錯的——
它沒帶 `--net-callers`,把 **161 支非擷取檔**也算進分母。批402 立的正確尺是
「只有真的會擷取的檔才該掛網路橋」,照那把尺量是 **28 掛 / 0 缺 / 100%**。

---

## 二、VDF 三庫整併

### 先更正一個量級

PEIS 的 `debt` 報 `_num` **24 檔**、`_connect_ro` **25 檔**、`_diag` **23 檔**——
那是**含版本史**的檔數。只看**活樹尾版**(VDF 一共 **65 支**):

| 能力 | 尾版重複 | 歸屬 |
|---|---|---|
| `_num` | **5** | 邏輯庫 |
| `_newest` | **4** | 邏輯庫 |
| `_write_json` | **4** | 邏輯庫 |
| `_arg` | **3** | 參數庫 |

### 分群之後,`_num` 那五支**不是同一件事**

| 支 | 差在哪 | 與正典 `num` 的差異(28 組語料) |
|---|---|---|
| ENG055 | 哨兵 `(None,'','--')` | **0** |
| ENG057 | 純轉換 | **0** |
| ENG056 | 哨兵含 **`'nan'`** | **2**(`'nan'` / `nan` → 原 None,正典 nan) |
| ENG063 | 只收 **`f > 0`** | **8**(`'0'` / `'-inf'` / `'nan'` … 原 None,正典放行) |
| ENG075 | 同上 + strip | **8** |

照「名字一樣就併」去做,會靜悄悄改掉三支引擎的行為,而且**位元組比對驗不出來**
——輸出格式沒變,變的是**哪些輸入被擋掉**。

所以差異**寫成參數**:`num(drop=…, positive=…)`。逐群綁定後 **5 群 × 28 組 = 140 組全同**。

### 正典升版

- **`SUP_MDL751_VIATailPick_v0102`**(十二檢 → **十四檢**)
  - `**` 樣式以前**靜默回 None**:`root/"**/x.py"` 的 `.parent` 是 `root/"**"`,
    那個目錄當然不存在 → `hits=[]` → None。呼叫端看到的是「沒找到」,
    而不是「這支不支援」——跟批596 的假綠同一個病。量過:活樹 **32 個呼叫端目前沒有人傳 `**`**,
    所以這是補洞不是修災情。
  - `bind(attr=, missing=)`:ENG073 那一群要的是**檔名字串 + 缺件回空字串**,
    `stringify=True` 給的是**整條路徑**,兩者不一樣。
- **`SUP_MDL753_VIACommonUtils_v0101`**(十四檢 → **十六檢**)
  - `num(drop=, positive=)`、`argval(default=, dashdash=)`
  - `default` 走**位置參數**(VDF 活樹是 `_arg(a, "--db", str(DB_TW))` 這樣用的)
  - `default` 每次回**新的一份**(L76/LL147:批593 就是栽在這裡,位元組比不出來)
- **`VIA_LibCanon.py`**(新;七檢)— 穩定名字的轉接口,跟 `VIA_SuperAccel_Module`
  同一個角色:底下用**尾版律**接三本正典,引擎裡**不出現版號**;缺席**大聲拋**不 graceful。

### 遷移結果

**12 支尾版引擎 · 15 支函式 → 正典綁定**,`[VIA:LIB-BRIDGE:v0100]` 橋 12 條。
遷法是**模組層綁定**不是再包一層 `def`(LL143:再包一層的話能力庫裡那一族還在,家族數不會掉)。

12 支引擎自測:**全部 FAIL 0**(10/6/9/9/10/13/12/8/8/8/11/9)。

**不遷的一支,具名**:`VDF_ENG056.ProgressBar._write_json(self, force)` 是**類別方法**
而且帶 2 秒節流(`now - self.last_json < 2.0` 就 return),寫的是自己的 `snapshot()`。
**名字一樣,做的事不一樣。**

### 三本庫的現況(誠實)

| 庫 | 冊 | 狀態 |
|---|---|---|
| 參數庫 | `VIA_Central_Params_SSOT_v0100.json` | 名實相符;本批把 `argval` 路由記進新冊 |
| **邏輯庫** | `VIA_Lib_Registry_v0100.json` | **名實不符** — 頂層鍵 `['ledger','schema']`,內容是 **pip 安裝台帳**(`packages` / `pre_conflicts` / `support_smoke`) |
| 因子庫 | `VIA_Feature_Catalog_v0100.json` | 名實相符;**本批沒有動因子** |

新立 **`VIA_Logic_Registry_v0100.json`** 記真正的邏輯正典路由(15 條 + 證據 + 不遷的那一支)。
舊的「邏輯庫」**一個位元組沒動**——只增不減;**它該改名成什麼(安裝台帳?環境台帳?)是操作員裁定**(LL90),
本批只記不改。因子庫的 5 個候選(`policy_factors` 9 處、`feature_audit` 6 處…)同樣**只列不寫**。

---

## 三、2023-07-01 起的增量:量到了,但**擷取閘沒開**

先補 `via-datahome catalog`(ENG089 原本回 ABSENT 就是缺這一頁),然後:

**表級(ENG089 `plan --since 2023-07-01`)**:38 表 · **18 表有缺**。

**逐日尺(ENG064 `--gap-mode plan`,對 `tw_daily_prices`)**:

```
缺 170,655 個 (日期×票) 鍵 · 既有 578,625
涉及 829 個交易日候選 × 892 檔
逐年:2023 → 130 天 · 2024 → 262 · 2025 → 261 · 2026 → 176
```

**本容器的庫從 2024-01-02 才開始**,所以 **2023-07-01 → 2023-12-29 整段是空的**。
另外 `tw_chip_inst` / `tw_chip_margin` **連表都不存在**——批596 那個空表守衛走的就是這條路。
`consensus_daily` / `consensus_latest` / `tw_monthly_revenue` / `monthly_revenue_analysis` **四張表 0 列**。

**擷取閘實證**(實跑 `--gap-mode fetch`,**沒有碰網路**):

```json
{"state": "GATED", "why": "擷取授權旗標未開", "missing_keys": 892}
```

`VIA_NET_CONSENT` 與 `VIA_SCRAPE_CONSENT` **兩個都沒設,也不由我設**。
這一步是操作員的手。

### 要真的補,請在工作站貼這一段

```powershell
$env:VIA_NET_CONSENT    = "YES"
$env:VIA_SCRAPE_CONSENT = "YES"

# 逐日缺口先看一眼(零寫入)
via-py vdf "functional modules\VDF\engine\VDF_ENG064_HistoryBackfill_v0111.py" `
  --gap-mode plan --start 2023-07-01 --end (Get-Date -Format yyyy-MM-dd)

# 真補(checkpoint 有,中斷可續;--batch-size 可調)
via-py vdf "functional modules\VDF\engine\VDF_ENG064_HistoryBackfill_v0111.py" `
  --gap-mode fetch --start 2023-07-01 --end (Get-Date -Format yyyy-MM-dd) --batch-size 20

# 籌碼兩張表整個不存在,要另外跑
via-chip
via-daytrade

# 補完回頭量一次
via-py vdf "functional modules\VDF\engine\VDF_ENG089_IncrementalFetchGate_v0100.py" plan --since 2023-07-01
```

> 工作站的資料家在 `C:\Users\tonyk\Github\movies-dataset\data`,**跟本容器不是同一個庫**。
> 上面那些數字是**本容器**量出來的;工作站要跑一次才知道它自己缺多少。
> **本機綠不等於倉裡綠,倉裡的數字也不等於本機的數字。**

---

## 四、立法

- **L79 正典轉接口律** — 引擎接正典一律經穩定名字的轉接件,由轉接件用尾版律解析本體,
  引擎裡不出現版號;轉出**綁定**不是新 `def`;缺席**大聲拋**;差異**寫成參數**。
- **LL153** — 整併之前先問「這個數字是哪一把尺量的」。同一批債,含版本史是 24 檔,
  只看活樹尾版是 5 支;網路橋覆蓋率我一開始也量錯(95.8% vs 100%)。
  **三次都是尺的問題,不是樹的問題。**

---

## 五、我自己踩的一個坑(閘抓到的,不是我)

全樹注入之後跑全格,`CGC_MDL150` 第①檢報紅:

```
[FAIL] ① 家族正位在位(尾版夾 glob)且五成員 md5 對冊(原名零觸碰律的量尺)
       supportive modules/VIA_Central_Governance/VIA_CentralGovernanceFamily_b514
```

我把加速器橋注進了那一夾的**四支**。那是**原名零觸碰律的凍結家族**,
靠 `MANIFEST_b514.json` 這本 md5 冊管著——注進去 md5 就對不上了。

**四支已還原,MDL150 回到 12/12。**

刺的是:**跑之前我特地驗過 L77** —— 拿 BridgeSweeper 自己的 `_excluded()` 去問
`_superseded` 和 `_sha`,兩邊都乾淨。但我驗的是「**清單裡的項目有沒有被遵守**」,
沒驗「**清單本身有沒有漏**」。b514 那一夾的名字不在任何排除清單裡。

所以判準從**名單**改成**證據**——`CGC_MDL124_BridgeSweeper_v0104`:

> 夾裡有一本**點名自己 `.py`** 的雜湊冊(`*MANIFEST*.json`)→ 那一夾是凍結件,不得注入。

修尺的時候我又差點犯**反向**錯誤:第一版往**祖先夾**一路找雜湊冊,結果
`supportive modules/` 底下一個 `*_sha*.json` 就把**整個 supportive modules 判成凍結**
= 把整棵樹關掉。**尺太寬跟太窄一樣壞。** 收窄成只看本夾、而且冊裡要真的點名這一夾的 `.py`。

第⑩檢**正反兩向都釘**:b514 要判凍結、`supportive modules/` 與 `VDF/engine` 不准被判凍結。

→ **L77 延伸** · **LL154**。

---

## 六、第二個坑:我為了量資料而產的檔,把一盞燈弄紅了

全格還剩一盞紅:`輸入主控台十三檢`(CGC_MDL139)。
單獨跑是 **18/18 綠**,在格子裡卻紅。逐項二分,兇手是格子注的
`PYTHONPATH=<supportive modules/bootstrap>`——但我**沒有動過 bootstrap**。

再往下挖,真兇是**我自己產的一個檔**:為了讓 `VDF_ENG089` 跑得起來
(它原本回 ABSENT 就是缺這一頁),我用 `VIA_DATA_HOME=<容器 output_hub>` 跑了
`via-datahome catalog`,寫出 `VIA_Reports/datahome/DATAHOME_CATALOG_latest.json`。
那本目錄把**容器自己的 output_hub** 記成資料家,MDL139 的
「主庫路徑律 ⑫」與「副本錯了要叫 ⑬」照那個記錄去量,就對不起來了。

實測:把那一夾移走,**同樣的 `PYTHONPATH` 下 18/18 全綠**。

處置:**不留**。那本目錄記的是容器路徑,不是工作站的資料家;
留著它等於讓一盞燈紅著、而且紅的理由是假的。它沒有進 git(gitignored),
數字我已經抄進本文與台帳。ENG089 在本容器回 **ABSENT** 才是它**誠實的狀態**。

> **量東西的動作本身會改變被量的系統。** 這一批我犯了兩次同一族的錯:
> 一次是注入橋改到凍結家族(第五節),一次是為了量資料而產的檔改了閘的判讀。
> 兩次都不是「改壞了」,是**我留下的痕跡被下一把尺讀到了**。
