# 批716 — 四支裡有三支樹上早就有,缺的是第四支

> 操作員 2026-09-23 兩道令:
> ①「用裡面優化整合引擎的功能將這些整合**看能否改善問題**」
> ②「**先測試除錯 加上加速器及網路工具看能否啟動**」
>
> 上傳:`VDF_MDL002_YFinanceFetchingEngine` · `VDF_MDL003_SentimentMacroEngine` ·
> `VDF_MDL004_TWFullMarketEngine` · `VDF_MDL006_FinancialModel`

---

## 一、先量再判 —— 四支裡有三支,樹上早就有

批713 才立的 **LL404「開一把新尺之前,先問樹上有沒有人量過同一件事」**,
這一批第一件事就是拿它量。

**證據一:函數集合比對**

| 上傳 | 樹上定義數 | 上傳定義數 | **上傳獨有** | 樹獨有 |
|---|---|---|---|---|
| MDL002 YFinance | 46 | 42 | **0** | 4 |
| MDL003 Sentiment | 35 | 28 | **0** | 7 |
| MDL006 FinancialModel | 35 | 34 | **0** | 1 |
| **MDL004 TWFullMarket** | **樹上沒有現役** | 30 | — | — |

**證據二(更硬):樹上的檔名就是用這三支的 sha256 命名的**

```
上傳 sha e5dbb168…  →  樹上 VDF_MDL002_YFinanceFetchingEngine_shae5dbb168.py
上傳 sha cb9c413e…  →  樹上 VDF_MDL003_SentimentMacroEngine_shacb9c413e.py
上傳 sha 3da0113e…  →  樹上 VDF_MDL006_FinancialModel_sha3da0113e.py
上傳 sha b5748ea4…  →  **樹上沒有同名**
```

那三支的收容本**早就躺在樹上**,檔名就是用它們自己的 sha 前八碼取的;
樹上那幾份只多了加速橋(所以整檔 sha 不同、檔名照舊)。

> **結論:MDL002 / MDL003 / MDL006 零新增,不整合。**
> 整合它們只會把樹上更完整的版本換成更舊的 —— 那不是改善,是退版。

---

## 二、缺的是第四支,而它正好是缺的那一半

`VDF_MDL004_TWFullMarketEngine` **樹上完全沒有現役** ——
批180 退役,只剩 `VIA_RetiredEngines/batch180_wave1/` 和一份 SCOPE_COPY 快照。

而它身上有:

```
TWSEFullMarketFetcher   openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL   一次全上市 ~1000 檔
TPEXFullMarketFetcher   tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes  全上櫃 ~900 檔
```

對照批644 那個一直沒解掉的洞:**`tw_listings` 893 檔全是 `.TWO`,`.TW` 零筆**。

> **缺的那一半,和這一支負責抓的那一半,是同一半。**

活樹裡打 `openapi.twse` 的只有 VRN 第一頁引擎 —— **VDF 家族一支都沒有**。
上市資料抓不進來,不是因為誰寫錯了,是因為**負責抓它的那支引擎被退役之後沒人補上**。

---

## 三、第二道令:加上加速器與網路工具,它起得來嗎

起得來。但先修了三件,才敢讓它進格子。

### ① 直連改走 AegisNexus(L20)

上游原件的 `_http_get` 直接呼叫第三方 HTTP 庫。本樹的網路**只有一個出口**。
AegisNexus 身上早就有 `fetch_json` / `fetch_twse_list` / `ResilientHTTPClient`
(UA 輪換 + 代理 + retry + throttle)—— 所以**只接線,不重寫**(LL404)。

保留 `_http_get` 的簽章(只增不減:上游呼叫端一個字不用改),
內部改成委派,回一個最小的 response-like 物件讓 `r.json()` 照舊跑得動。
**接不上就誠實 `None`,不偷偷落回直連** —— 有第二個出口,L20 就是空的。

> 載入方式也踩過一次:用 `spec_from_file_location` 載 AegisNexus 會炸
> `AttributeError`,因為它內部有幾段要拿得到**自己的模組名**。
> 改成 `sys.path` + 具名 `import` 就過了。

### ② 拆掉會把格子卡死的彈窗

上游原件結尾停在一行等人敲鍵盤的 `input()`。在格子裡那就是**整跑卡死到逾時**。

> 寫這一檢的時候**又踩了 LL384**:檢的字句裡含著它自己禁的那串字,
> 所以它掃自己的原始碼時永遠是紅的。**本週第四次。** 拆寫。

### ③ 「閘沒開」不是「壞了」

原件在閘關著時一路跑到 Step 1,兩所都拿不到料,然後 `abort` 回 **rc1 RED**。

```
[INFO] Step 1/5: Daily quote from TWSE + TPEX OpenAPI
[INFO] 網路未取得(GATED)… ← 同意閘未開,這不是壞掉
[ERR]  No quote data, abort.
rc=1
```

**把「閘沒開」講成「壞了」。** 判錯的紅燈和假綠一樣傷 ——
看的人會跑去修一支根本沒有壞的引擎。

補 `main_governed()`:閘沒開回 **rc4 GATED**,並把一次貼上的那兩行印出來。
格子那一站用 `gated_ok`(rc 0 或 4 都算過)。

```
[GATED] 同意閘未開 —— 這**不是壞掉**。本引擎要觸網(TWSE / TPEX OpenAPI + yfinance)。
[律] **AI 永不代設同意閘。** 要開請操作員自己貼:
     $env:VIA_NET_CONSENT='YES'
rc=4
```

自測 **7 檢 OK 7 · FAIL 0**。實跑:引擎點得起來、跑到 Step 1、兩所都回 GATED、誠實停。

---

## 三之二、第三道令:「VDF 要加入網路工具」—— 格子先我一步講出來了

全格子第一跑,我那兩站綠,**另外兩站紅**:

```
自動總跑器六檢 ② S1 雙橋稽核 GREEN(網路缺 0) … 外呼 5
加速器控制面三十七檢 … 批115 VDF 全導入令(正向尺):每一支 VDF 活件尾版都掛了統包網路工具橋 → FAIL
```

兩盞紅講的是同一件事:**我把 AegisNexus 直接掛進 MDL004 當網路出口,門走錯了。**

本樹 VDF 的網路出口是**統包工具**(`SUP_MDL740_NetUnified`,經 `via_net_unified_v*` 轉接)。
它身上才有雙閘(`VIA_NET_CONSENT` / `VIA_SCRAPE_TOKEN`)、才有 AegisNexus 後端 + stdlib 退路。
繞過它直接接 AegisNexus,**等於在 VDF 開了第二個網路出口** —— 批115 全導入令的正向尺當場紅。

> 方向是對的(L20「網路只認 AegisNexus」),**但那是後端,不是門。**
> 門是統包。改掛 `[VIA:NET-BRIDGE:v0100]`,閘況也改成問統包的 `gate_state()`。
> 兩站重跑:**轉綠 2**。

這一盞紅是操作員第三道令「VDF 要加入網路工具」的**機器版本** ——
操作員講的和格子講的是同一句,只是格子先講出來了。

---

## 三之三、第四道令:「全部加速新的加速器」—— 撞上 L50 第一條

加速器的解析序在 `SUP_MDL737.CEL_CANDIDATES`。量了才知道不能照直做:

| 候選 | talib 路徑 | 說明 |
|---|---|---|
| `accelerator/VeritasCeleritas.py` | **0** | L50 合規本 —— 批618 操作員裁定**排第一** |
| `VeritasCeleritas_v1140.py`(新) | **8** | 新版,talib 路徑**比舊本還多** |
| `VeritasCeleritas.py`(批345 正本) | 1 | |
| `50_Protection_Acceleration/…` | 1 | |

**L50 是第一條**(批618:「TA-Lib 禁用,QuantGuard 是唯一正主」),而且那一條明訂
解析序要把**零 talib 合規本排第一** —— 因為工作站的 `find_spec('talib')` 找得到,
排錯順序執行期會真的把 talib 載進來(容器這邊 `find_spec` 是 False,所以這件事
**只在操作員的機器上會發生**,容器量不到)。

所以新版**不能排第一**。`v0106` 的處置:

```
1  accelerator/VeritasCeleritas.py   ← L50 合規本,永遠第一
2  VeritasCeleritas_v1140.py         ← 批716 新版,**第二**
3  VeritasCeleritas.py               ← 批345 正本(不動)
4  50_Protection_Acceleration/…
```

新版因此**接手了兩本舊的全部呼叫**,而 L50 一步都沒退。
實測載到的仍是第 1 本(合規本在位),這是**對的**。

> **要讓新版真的排第一,它得先有一條零 talib 路徑。**
> 那是操作員的裁定(要推翻自己批618 那一條),不是我的。

---

## 四、這一批的律

**LL415 「上傳了四支」不等於「缺四支」。**
先拿 sha 和函數集合去對樹,再決定整合哪一支。
這一次四支裡有三支樹上早就有,而且樹上那幾份**更完整** ——
照單全收等於用舊版覆蓋新版,那不是改善,是退版。

**LL417 「接上那個工具」和「走那道門」是兩件事。**
L20 說網路只認 AegisNexus —— 那是**後端**。VDF 的**門**是統包工具,
雙閘掛在門上。直接接後端等於繞過閘,而且在同一棵樹上開了第二個出口。
**看到一個工具名字,先問它是門還是後端。**

**LL416 退役一支引擎,要留下「誰來接它的班」。**
MDL004 在批180 退役之後,**沒有任何一支接手抓上市資料** ——
於是 `tw_listings` 整整 893 檔全是上櫃,而這件事一路被當成「資料源的問題」查了好幾批。
退役單上該有一欄:**它原本負責的那件事,現在誰做**。

---

## 五、還卡在操作員手上

| 件 | 卡點 |
|---|---|
| 真的去抓 TWSE 全上市 | **同意閘**。引擎已就緒、起得來、停在閘上 |
| MDL002/003/006 要不要用上傳版覆蓋樹上版 | 我的判讀是**不要**(退版);要覆蓋請下令 |

要補上市那一半,請貼這兩行:

```powershell
$env:VIA_NET_CONSENT='YES'
python3 "functional modules/VDF/VDF_MDL004_TWFullMarketEngine_v0100.py"
```

---

*四支裡有三支樹上早就有 —— 先量再判,省下的不只是工,是一次退版。*
