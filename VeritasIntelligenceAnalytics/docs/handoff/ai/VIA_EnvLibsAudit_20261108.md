# 近期安裝是不是走 VIA 自己管理的環境與 libs?(操作員 2026-11-08 問 · 用 VIA 自己的工具查)

**答案:不是。** 近期安裝完全沒有經過 VIA 的環境治理,也沒有進任何 `via_` 隔離境。
以下每一條都是容器實測,不是推定。

## ⓿ 一句話

本容器**一個 `via_` 境都不存在**;近期那批安裝是 **`uv`** 裝進容器主境的 MCP 相依,
**VIA 冊裡零紀錄**;而且 libs 分成三層,其中 `duckdb` 這個冊上屬 `engine_core` 的件
跑到了使用者層 —— **這就是本輪 ENG115 炸掉的真正源頭**。

## ① 跑的是哪個 Python:不是 VIA 的境

```
執行檔   /usr/bin/python3
前綴     /usr
在 venv? False          ← 不在任何虛擬境
site     /usr/local/lib/python3.13/dist-packages
版本     3.13.16
```

冊 `VIA_EnvGovernance_Baseline_v0102` 宣告的隔離境 —— `via_paddle_311` ·
`via_camelot_311` · `via_vdf_312` · `via_vrn_312` · `via_iso_ml_cuda_H` ·
`via_iso_scrape_H` · `via_mix_ds_np2_M` · `via_iso_gis_H` —— **本容器一個都沒有**
(倉內與 `/opt` `/usr/local` `~` 都掃過,只有同名的程式夾,沒有 venv)。

`base.python_expected = 3.13` vs 實況 `3.13.16` → 大版對得上,這一項沒問題。

## ② 近期安裝是誰裝的:`uv`,不是 VIA

`dist-info/INSTALLER` 逐支讀出來都寫 **`uv`**:

| 套件 | INSTALLER | metadata 時戳 | 目錄 mtime |
|---|---|---|---|
| `mcp` · `mcp_types` | uv | 2026-10-03 05:41 | 2026-11-07 09:12 |
| `httpx2` · `starlette` · `uvicorn` · `anyio` · `sse_starlette` · `python_multipart` · `click` | uv | 2026-10-03 05:41 | 2026-11-07 09:31 |
| `seaborn` | — | — | 2026-11-06 13:53 |

這批是 **MCP 伺服器的相依**,由 harness / plugin 層裝進主境,
**不經 `via-envgov`、不經同意閘、冊上零紀錄**(`grep` 整個 registry 找
`httpx2` / `sse_starlette` / `python_multipart` → 零命中)。

容器根 mtime `2026-11-08 10:42`(今天重啟過);`dist-packages` 最後寫入 `2026-11-06 13:53`。
→ **11-08 重啟之後安裝面沒有新動作**,本輪我也沒裝任何東西
(pip 被沙盒拒絕 `[Code from External]`;VIA 的 envgov 第 ㊿ 檢明文
「授權但同意閘未開 = `BLOCKED_CONSENT` 零動作(**不代設**)」)。

## ③ libs 分三層 —— 這正是治理要防的分裂

| 層 | 套件數 | 代表件 |
|---|---|---|
| `/usr/local/lib/python3.13/dist-packages` | **82** | pandas · polars · pyarrow · numpy · matplotlib · reportlab(uv 裝的主層) |
| `/root/.local/lib/python3.13/site-packages` | **13** | **duckdb-2.0.0** · jinja2 · requests · urllib3 · certifi · conan …(**使用者層**) |
| `/usr/lib/python3/dist-packages` | **25** | yaml(系統層) |

### ④ 找到一條真的因果鏈,不是理論風險

冊 `base.engine_core` 明列:
`numpy · pandas · pyarrow · duckdb · polars · plotly · matplotlib · scipy · requests · httpx · jsonschema · openpyxl · xlsxwriter · rich`

也就是 **`duckdb` 冊上屬 base 共用基座**。但實況它在
`/root/.local/lib/python3.13/site-packages/duckdb/__init__.py` —— **使用者層**。
而那一層的版本是 **duckdb 2.0.0**,正是移除了 `DuckDBPyRelation.fetchone()` 的版本。

→ **本輪 `VRN_ENG115_HeaderFrameTemp` 自測炸 `AttributeError` 的源頭就是這個。**
治理面的「件跑錯層」直接變成程式面的紅燈。這條值得記進冊,不只是環境雜訊。

同理 `requests` / `jinja2` 也在使用者層,`requests` 同樣是 `engine_core`。

## ⑤ 冊上封鎖家族 vs 實況

`base.never_in_base_families` 列 12 個 **RED 立拔** 的家族:
`ocr · deep_learning · browser · table_extraction · ml_boost · gis · web_api · webui ·
nlp · process_mining · compilers · stealth_proxy`。

本容器因為**沒有任何 `via_` 境**,這些家族的件:
* 缺席 —— `fitz`(pymupdf,屬 docs/ocr 面)· `curl_cffi`(屬 web_api)· `yfinance` 全 ABSENT
* 或者沒地方放 —— 要裝也只能裝進 base,而那會違反 `never_in_base_families`

所以 **A 那三支套件不能「就裝在主境」解決**:照冊,`pymupdf` 要進 `via_vrn_312`、
`curl-cffi` 要進 `via_vdf_312`。在這個沒有 `via_` 境的雲端容器裡,
正確做法本來就是「不要在這裡裝」。

## ⑥ 用了哪些 VIA 自己的工具查(照 L65 次序)

| 工具 | 查到什麼 |
|---|---|
| `via-vcgc token` | 省 Token 卡 6/6 已啟用;禁令行逐字寫著「**裝套件 · 代設同意閘**」 |
| `CGC_MDL158 read`(全景) | 讀冊與引擎骨架,整檔沒讀進對話 |
| `VIA_EnvGovernance_Baseline_v0102` | base 政策 / engine_core / low_risk_allow / never_in_base_families / 各家族 target_env |
| `CGC_MDL135_EnvGovernance v0118 --selftest` | 52/52 + 本版 5/5;第 ㊿ 檢證實「同意閘未開 = 零動作,不代設」 |
| `CGC_MDL186_EnvGovernance_8Hub v0101` | 八面檢查跑過;位階三條(L103 / L50 / L102)· 環境計畫七步 · 「中高風險與 paddle 進自己的 `via_` 境」· **衝突現況 NODATA**(沒有活的環境快照可比) |
| `CGC_MDL240_EnvGovernance` | **ABSENT** —— 找不到尾版 |

## ⑦ 判決與下一手

| 面 | 燈 | 說明 |
|---|---|---|
| 近期安裝走 VIA 治理? | **紅** | 走 `uv` 進主境,冊上零紀錄 |
| `via_` 隔離境存在? | **紅** | 一個都沒有 |
| libs 單層? | **黃** | 分三層;`duckdb` / `requests` / `jinja2` 這些 `engine_core` 件在使用者層 |
| base Python 版本對冊? | **綠** | 冊 3.13 · 實況 3.13.16 |
| 本輪有沒有繞過閘裝東西? | **綠** | 零安裝,兩道閘都擋著,照實記 |

**要你決定的三件:**

1. **雲端容器要不要建 `via_` 境?** 照冊該建(`via_vdf_312` / `via_vrn_312` 等),
   但建境與裝件都要同意閘 + 網路,我不代設。不建的話,ENV_PKG 那 18 案在雲端永遠紅 ——
   這是政策結果,不是缺陷。
2. **`duckdb` 要不要從使用者層移回 base 層?** 它在冊上是 `engine_core`。
   現在那層是 2.0.0,已經造成一次真紅(ENG115)。我已出 v0102 相容墊片擋住,
   但根因是「件在錯的層」。移動要動環境,交你裁。
3. **MCP 那批 uv 裝的件要不要補登 VIA 冊?** 它們是 harness 的相依不是 VIA 的件,
   可以選擇「登記為外部層、不納治理」或「明文豁免」。現在是兩邊都沒寫,屬於治理盲區。

---

本文只讀:沒有裝任何套件、沒有改任何環境、沒有設任何同意閘。
五系統對等獨立(L120 / L123):環境與 libs 的正本歸 VCGC,本文只攤開實況與冊的落差。
