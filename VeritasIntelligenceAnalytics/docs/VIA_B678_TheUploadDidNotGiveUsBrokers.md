# 批678 · 上傳沒有給我們券商,它照出了我們自己的兩個問題

操作員令:「以現有得 SSOT REGEX 同意字及中央控管的其他褲為主 只增不減除衝突」。

## 一 · 先量既有的(LL329 拿到規格先去量既有實作)

沒有先寫任何新冊。先把既有的六本攤開逐條標來源:

| 冊 | 位置 | 別名條數 |
|---|---|---|
| 正典(READ_ONLY) | `supportive modules/ssot/VIA_Financial_Institution_SSOT_v0100.json` | 券商 28 家 · 評等 6 鍵 · 研究欄位 1 |
| 疊加層(操作員裁決層) | `supportive modules/ssot/VIA_FinancialInstitution_Overlay_v0100.json` | 拒絕 20 · 券商別名 14 鍵 · 新增機構 5 · 評等別名 4 鍵 · 檔名鍵 16 |
| 中央規則正本 | `supportive modules/registry/VRN_FieldRules_SSOT_v0100.json` | 評等 canon_map 4 鍵 + local_scale 14 · 券商 extra_table 36 |
| 券商冊 | `functional modules/VRN/registry/VRN_BROKER_LIST_v01.json` | 19 家 |
| 知識冊 | `functional modules/VRN/knowledge/VRN_{Broker,Rating}_Dict_v0100.json` | 券商 29 + 32 · 評等 4 級 + 6 組 |

正規化後合計 **底冊別名 1,000 條**(broker 269 · rating 158 · target_price 17 個正規化鍵)。

上傳的兩份 `SYNONYM_LIBRARY*.json` **位元完全相同**(md5 `4a946821…`),
而且和 zip 裡的那一份也相同 —— 是同一份檔上傳了三次,不是三份料(L30 一個出處)。

## 二 · 443 條逐條判(誠實五態,不是「合併成功」四個字)

```
SAME 347 · ADD 80 · WIDEN 1 · CONFLICT 5 · DENIED 10
```

| scope | ADD | CONFLICT | WIDEN | DENIED | SAME |
|---|---:|---:|---:|---:|---:|
| broker | **0** | 4 | 0 | 10 | 185 |
| rating | 31 | 1 | 1 | 0 | 146 |
| target_price | 12 | 0 | 0 | 0 | 16 |
| valuation_method | 20 | — | — | — | — |
| rating_label | 7 | — | — | — | — |
| financial_concept | 7 | — | — | — | — |
| scenario | 3 | — | — | — | — |

**券商 ADD = 0。** 199 條券商別名裡,既有的冊本來就有 185 條,其餘 14 條全是衝突或拒絕。
上傳沒有給我們任何一家新券商 —— 它做的事是**照出我們自己的兩個問題**。

## 三 · 第一個問題:四本冊對同一家用了兩種正典鍵拼法(L30)

| 別名 | 既有判 | 正典鍵 | 同一家? |
|---|---|---|---|
| `megabank` | `MEGABANK`(broker_list) | `MEGA` 兆豐證券 | 是 |
| `daiwa capital` | `DAIWA SECURITIES`(broker_list) | `DAIWA` 大和資本 | 是 |
| `jp` | `J.P. MORGAN` / `JPMORGAN`(broker_list) | `JPM` 摩根大通 | 是 |
| `ibf securities` | `IBF`(規則冊 extra_table) | `WATERLAND` 國票證券 | 是 |

**裁定:一律解到正典鍵。**
正典是唯讀正本,它的鍵就是唯一的正本命名空間;其他拼法**降為別名(不刪)**。
正典自己早就有 `key_migration_map`(`BOA`/`ML`→`BOFA` · `MCQ`/`MQ`→`MACQUARIE`)——
這四條就是同一件事的第五到第八條,寫進疊加層 v0101 的 `key_alias_add`。
裁定者 `AI(批665 操作員授權同義裁定)`,理由逐條留在 `rulings`(LL90 留痕義務不轉移)。

第五個衝突是**粗細尺**,不是判得相反:

* 正典六鍵切**強弱**(`STRONG_BUY`/`BUY`…),把 `ADD` 摺進 `BUY`
* 規則冊四鍵切**加碼強度**(`BUY`/`HOLD`/`SELL`/`ADD`),把 `STRONG_*` 摺進 `BUY`/`SELL`

所以「避免」既有在 `strong_sell` 組、上傳判 `SELL`,兩邊都對,只是尺不同。
聯集冊記**最細的那一個**,兩條粗尺各由 `fine_of()` / `coarse_of()` 當場投影。
**LL327:兩條基準不同的車道,永遠不准混成一個數字。**

## 四 · 第二個問題:拒絕清單只擋得住走疊加層那條路

十條 DENIED 照出來的。分兩種,**不可以混成一個數字**:

* `OVERRIDDEN` **2 條** —— 在正典裡(`中信證券→CTBC` · `摩通→JPM`)。拒絕清單先行=已經擋住了,行為沒錯。
  列出來是因為疊加層自己的裁定文寫「Grok 正典的 JPM 別名本來就沒有摩通,兩邊一致」——**量下去正典有**。
  行為對、冊上的話錯,所以要留痕。
* `LEAK` **31 條** —— 在 `broker_list` / 規則冊 `extra_table` / 兩本知識冊裡,
  `GF` · `廣發` · `海通` · `中金` · `CICC` · `中信建投` · `國泰君安` 全都還在。

只增不減=**一條都不刪**。本批做的是:在聯集冊上把它們標成 `inclusion: DENIED`,
並且 `status` 逐條指名是哪一本冊的哪一條(L92 哨兵抓到就要給得出下一步)。

### 順手照出來的兩條冊內瑕疵(不是上傳帶進來的)

* `FALSE_ALIAS` —— `knowledge.broker_dict` 把 `Guotai Junan` / `國泰君安` / `國泰君安證券`
  掛成 **國泰(Cathay)** 的別名。國泰君安是另一家機構(而且在拒絕清單上)。
  掛在這裡 = 國泰君安的研報會被記成國泰證券的。
* `ABBR_COLLISION` —— 同一本冊裡 **大華** 和 **高盛** 共用縮寫鍵 `GS`。
  疊加層 `broker_add` 早就給了大華正典鍵 `DH`,但這本冊還是 `GS`。同一個名字兩扇門(L101)。

兩條都**只指名不刪**;修法是解析一律走 `resolve()` 的「拒絕→正典→疊加→聯集」那一道。

## 五 · 最重要的那一條:沒過閘的活支 10/10

尺很窄,窄得可以講清楚:**讀券商冊的活尾版**(檔案裡出現
`VRN_BROKER_LIST_v01` / `extra_table` / `VRN_Broker_Dict` / `broker_alias` / `def broker_of(` / `BROKER_ABBR` 任一),
**有沒有出現**拒絕閘的字樣(`FinancialInstitution_Overlay` / `resolve_broker` / `deny_reason` / `CGC_MDL176`)。

```
[沒過閘] SUP_MDL015_VISVRNBrokerAliasFullList_v0100.py
[沒過閘] SUP_MDL749_VRNFieldRuleHub_v0110.py          ← 中央規則正本樞紐
[沒過閘] VIS_VRN_BrokerAlias_Compatibility_v0222.py
[沒過閘] VIS_VRN_BrokerAlias_Extension_v0224.py
[沒過閘] VIS_VRN_PDFTextLayerFallbackPlan_v0222.py
[沒過閘] VIS_VRN_Q1_AliasRoutePatch_v0100.py
[沒過閘] VRN_ENG062_SummarizerV1_v0102.py
[沒過閘] VRN_ENG086_FirstPageLogicBridge_v0108.py      ← 首頁邏輯橋
[沒過閘] vrn_finlex_v0106.py
[沒過閘] vrn_report_digest_v0116.py
```

**十支,十支都沒過。** 拒絕清單立了、操作員的裁定留了,
可是真正在讀研報券商名的那幾支,從來沒有走過那扇門。
(`VRN_ENG073` 尾版**有**走疊加層,但它不讀這幾本券商冊,所以不在這個分母裡。
 尺只講它量過的事 —— LL324。)

這一條不是這一批能順手修完的:`SUP_MDL749` 是中央規則正本,
改它的解析道要單獨一批、單獨一套自測。本批做的是**把它照出來並且釘住**:
`CGC_MDL176 status` 每跑一次就會重報一次,格子上有站,漏了就紅。

## 六 · 只增不減怎麼證

`contains()` 逐條比對:底冊 1,000 條 `(scope, alias, canonical)`,
每一條都要在聯集冊裡出現。少一條 → `status` rc=1、格子紅。

負控(LL89 會過的檢等於沒有檢):自測當場從聯集冊拿掉一條,
要求 `contains()` **一定**抓得到。抓不到就 FAIL。

疊加層 v0100 → v0101 同樣證:舊版每一個鍵、`rating_alias_add` 每一條別名都要還在;
少一個鍵就 fail-closed 不寫。原件走深拷貝,**v0100 一個位元不動**(尾版律 + Hydra 守衛:
目標版號已存在即拒寫)。

## 七 · 新收的短碼不進內文道

上傳新給的 13 個短碼(`SB` `OP` `OW` `N` `MP` `EW` `UP` `UW` `SS` `CD` `B` `H` `S`)
一律收進 `namespace: field_code`(研報表格裡的評等欄位代碼),`resolve()` 的內文道看不到。

這不是我發明的謹慎,是操作員批413 對 `JP` 立過的同一條:
**「兩三字母 token 只在檔名命名空間認得;內文別名絕不收(在內文會亂咬)」**。

**既有的短碼(`TP` `PT` `FV` `目標` …)一個都不動** —— 這條只約束新收的,不然就是減。

## 八 · 產出

| 檔 | 是什麼 |
|---|---|
| `supportive modules/registry/CGC_MDL176_SynonymUnion_v0100.py` | 聯集閘(廿九檢;`status` / `plan` / `--apply` / `resolve` / `--selftest`) |
| `supportive modules/registry/VIA_SSOT_SynonymUnion_v0100.json` | 聯集冊:7 個 scope · 524 個正規化鍵,逐條帶 `source` / `inclusion` / `namespace` |
| `supportive modules/ssot/VIA_FinancialInstitution_Overlay_v0101.json` | 疊加層下一版(純增:評等別名 +18 · `key_alias_add` 6 條) |
| `supportive modules/references/intake/VIA_SSOT_SynonymUnion_b678/` | 收容件正本零觸碰 + `MANIFEST.sha256` |
| `supportive modules/registry/CGC_MDL064_SelftestGrid_v0431.py` | 兩盞新站(工具健康 + 冊的現況) |

## 九 · 沒做的,以及為什麼(L87 豁免必附理由)

* **沒有加短令 `via-synunion`。** L70:未經操作員逐次許可不得修改任何 `.ps1`。
  批678 的令裡沒有 PS,所以我不自己開 Register v0241。
  要的話一句話,或直接貼第十節那一段。
* **沒有改 `SUP_MDL749` / `ENG086` 的解析道。** 見第五節:那是單獨一批的事,
  本批只負責把它照出來並釘在格子上。
* **沒有刪任何一條被拒的鍵。** 只增不減,只標 `DENIED`。

## 十 · 短令:還沒有,而且刻意還沒有

本批**沒有**登記 `via-synunion`。兩個理由,都不是懶:

1. **L70** —— 未經操作員逐次許可不得修改任何 `.ps1`。批678 的令裡沒有 PS,所以我不自己開 Register v0241。
2. **L89 幽靈令** —— 冊上沒有的名字就不准寫成一貼即用的樣子。
   我第一版的 docs 真的犯了這一條:把 `via-syn`+`union` 寫進 ```powershell 區塊,
   全格子當場照紅(CGC_MDL157「every via-* call inside a paste-ready block resolves to a real command」,
   calls=487 · ghost 1)。**尺做對了** —— 你照著貼只會得到一次 not recognized。
   所以這裡改成:名字先不給你貼,等你點頭我再一次把 Register 新版號、根目錄梭、`bin\` 梭三面一起補齊。

在那之前,現在就跑得動的是這兩行(直呼引擎,不經短令):

```powershell
python "supportive modules\registry\CGC_MDL176_SynonymUnion_v0100.py" status
python "supportive modules\registry\CGC_MDL176_SynonymUnion_v0100.py" resolve broker 廣發
```
