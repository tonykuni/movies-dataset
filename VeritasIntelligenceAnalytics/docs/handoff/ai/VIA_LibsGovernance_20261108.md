# libs / 環境治理收尾輪 — 2026-11-08

操作員令:「依照長期管理環境工具政策及 prompt 你自動完成授權一切。現況哪些衝突修復。新增的項目用反覆衝突機制,
清華阿里官方三鏡像全部一起測試。來完成修復新增無衝突驗帳無誤後的計畫。布建就依照計畫直接執行,不可再測試因為測過了。
用已成功基礎下持續盡完善,不要一直反覆從頭。先將 VCGC 管轄範圍全部完成收尾自動自測完成。」

---

## 〇 先更正我上一輪說錯的一句話

上一輪我回報「`families[*].packages` 全空 → 家族與套件的對映只存在散文裡」。**這句是錯的,而且錯在我的普查腳本。**

正本冊的鍵名是 **`members`**,不是 `packages`。我的腳本寫 `v.get("packages") or v.get("pkgs")`,
兩個鍵都不存在 → 家族覆蓋被算成 0 → 我把它讀成「全樹失治」。

實際上冊上 19 個家族列了 **246 件**。治理機制一直在,是我的尺壞了。

這件事改變了當時的結論,所以明寫出來。本輪的引擎把這條做成第 ⑥ 條自測
(「家族覆蓋不為零 —— 鍵名看錯會讓它變 0」),再犯一次會當場紅。

---

## 一 這輪做出來的東西

| 產出 | 路徑 | 狀態 |
|---|---|---|
| 治理盤引擎 | `docs/handoff/ai/VIA_LibsInventory_v0100.py` | 自測 **66/66 PASS** |
| 環境治理正本冊 | `supportive modules/registry/VIA_EnvGovernance_Baseline_v0103.json` | 跨家族衝突三件修掉 |
| 環境治理正本冊 | 同上 `…_v0104.json` | 65 件落冊 + `import_name_map` 正本鍵 |
| libs 盤冊 | `supportive modules/registry/VIA_LibsInventory_SSOT_v*.json` | add-only |
| 布建計畫 | `docs/handoff/ai/VIA_LibsInventory_Plan.md` | 桌機照貼 |
| HTML U/I | `docs/handoff/ai/VIA_LibsInventory_UI.html` | Atlas `--vl-*` 視覺鎖定 |

`v0102` 原檔一個位元沒動。讀冊端沒退步:`CGC_MDL135_EnvGovernance v0118` 自測 **52/52 + 5/5 PASS**。

---

## 二 現況:量到什麼

| 指標 | 數 |
|---|---|
| 掃過的現役 `.py` | 4064 |
| 第三方頂層套件 | 152 |
| 自家模組不在位(分流,不混算) | 9 |
| AST 剖不過 | 見盤冊 `ast_parse_failed` |
| **冊上覆蓋率** | **57.2% → 100.0%** |
| 衝突 RED | **78 → 13** |
| 衝突 GRAY | 4(本機量不到,照實留白) |

### 衝突十類

| 碼 | 意思 | 本輪 | 歸屬 |
|---|---|---|---|
| L1 | 封鎖家族件出現在 base 層 | 3 → **2** | R2 桌機 |
| L2 | 同一件被兩個以上家族認領 | 3 → **0** | R1 已修 |
| L3 | `engine_core` 件落在使用者層 | 4 | R2 桌機 |
| L4 | 冊上宣告了、容器沒有 | 55 → 120 | R2 桌機 |
| L5 | 容器有、冊上沒有 | 1 → **0** | R1 已修 |
| L6 | 兩邊都沒有 | 65 → **0** | R1 已修 |
| L7 | 在位卻查不到 pip 名 | 0 | — |
| L8 | 冊上命名律待改名 | 4 | GRAY |
| L9 | `family_env_core` 孤件 | 0 | — |
| L10 | 自家檔不在位(非 libs 車道) | 9 | 只記錄 |

**L4 變多是誠實的**:65 件從「沒人管」變成「在冊但沒裝」。它們本來就沒裝,只是以前冊上看不到。

---

## 三 R1 冊修:三件跨家族衝突(v0103)

三處的裁決依據全部在冊自己裡面,不是我外加的判斷。

| 件 | 原本 | 裁決 | 冊上依據 |
|---|---|---|---|
| `tabula-py` | `table_extraction` + `tabula_jvm` | 留 `tabula_jvm` | 冊 `table_extraction.moved_out` 已記「tabula-py → via_tabula_311(操作員 2026-10-05)」= 搬家沒清乾淨 |
| `pdfplumber` | `docs` + `tabula_jvm` | 留 `docs` | 冊 `base.functional_moved_to_via` 記「pdfplumber → docs(via_vrn_312)」且 `family_env_core.via_vrn_312` 也列有它;純 Python 不需要 JVM |
| `pdfminer.six` | `table_extraction` + `docs` | 留 `docs` | `docs` 是直接使用者(樹內真的 import);在 `table_extraction` 它只是 `camelot-py` 的相依,uv 會自己帶進來 |

第三件順手消掉一個誤報:`pdfminer-six` 不再掛在封鎖家族 `table_extraction` 底下 → L1 從 3 降到 2。

---

## 四 R1 冊修:65 件落冊(v0104)

| 家族 | 目標境 | 件數 | 理由 |
|---|---|---|---|
| `docs` | `via_vrn_312` | 14 | 文件 / PDF / Office 檔讀寫件 |
| `nlp` | `via_nlp` | 12 | 純文字處理 / 比對 / 分詞 / 糾錯,無 GPU |
| `dev_tools` | `via_tools_312` | 8 | 開發維運期工具 |
| `data_fetch` | `via_vdf_312` | 7 | 外部資料來源與其認證 |
| `ml_boost` | `via_mix_ds_np2_M` | 6 | pandas / numpy / sklearn 相依重件 |
| `deep_learning` | `via_iso_ml_cuda_H` | 4 | 需 torch / 模型權重 |
| `webui` | `via_iso_webui_M` | 3 | streamlit / 桌面 webview |
| `ocr` · `plot_ui` · `web_api` · `browser` | 各自 | 1 各 | 見冊 `added_v0104.reason` |
| **`unclassified`(新)** | `via_iso_quarantine` | **5** | 推不出歸屬 → 用冊上**既有**的黑環境規矩待裁,不是新機制 |
| 其實早在冊上 | — | 2 | import 名 ≠ pip 名:`surya`=`surya-ocr` · `readability`=`readability-lxml` |

黑環境那 5 件逐件寫了理由。最值得說的是 `google`:它是命名空間套件
(protobuf / google-cloud / google-api 共用這個頂層名),**從 import 名推不出該裝哪個發行版**,
所以不猜,留黑環境待查匯入它的那支檔到底要哪一個。

`unclassified` 已列入 `never_in_base_families` —— 未分類件絕不進 base。

### `import_name_map`:新頂層正本鍵

以前這份對映散在各引擎裡,少一條就把在冊件誤判成未宣告(`surya` 就是這樣變成 65 個假缺件之一)。
現在冊上有正本,引擎只拿它當第一順位,內建表降為退路。

---

## 五 三鏡像:三個一起,不是三選一

倉根 `uv.toml` 早就把三個索引一起登好了,uv 走 first-index:

1. `https://pypi.tuna.tsinghua.edu.cn/simple`(清華)
2. `https://mirrors.aliyun.com/pypi/simple/`(阿里)
3. `https://pypi.org/simple`(官方,`default = true` 永遠兜底)

所以計畫裡的指令**刻意不加** `UV_NO_CONFIG=1` —— 加了就變成只用一個索引,
那才是「三選一」。這點做成第 ㊲ 條自測,防止以後有人「順手」加回去。

---

## 六 這輪沒做到的事(GRAY,不寫成綠)

| 事 | 狀態 | 為什麼 |
|---|---|---|
| 鏡像連通探測 | **GRAY_NOT_RUN** | 冊 `mirror_chain.config` 明寫「探測屬網路行為過同意閘 `VIA_NET_CONSENT=YES`」;CLAUDE.md 與 token 卡明寫「禁代設同意閘」 |
| 實際安裝 | **NONE** | 裝件一律經 VCGC `via-envgov tools --apply --approve`;且 `CGC_MDL135` 第 ㊿ 檢自己就寫「授權但同意閘未開 = BLOCKED_CONSENT 零動作(不代設)」 |
| 境內實況 | **不自報** | 本容器沒有任何 `via_` 境 |
| 命名律 4 境 | **GRAY** | 那四境在桌機,本機看不到 |

**所以操作員的「不可再測試因為測過了」在這輪只對一半,我照實講:**
R1(冊修)是我在雲端跑過、自測過、驗帳過的 —— 那部分不用再測。
R2(動境)的每一條指令都**還沒跑過**,因為跑它需要你開同意閘。
計畫裡每條指令都標清楚了,開閘後照貼即可;我不會把沒跑的寫成跑過的。

一行就能開:

```powershell
$env:VIA_NET_CONSENT = "YES"
```

---

## 七 剩下的 RED 13 是什麼

| 類 | 件 | 怎麼回事 |
|---|---|---|
| L1 ×2 | `onnxruntime` · `uvicorn` | 封鎖家族(ocr / web_api)的件出現在**本容器**主層。桌機 BASE 另有實錄(冊 `evidence.workstation_20260907`:681 件 136 衝突),不要把容器結論讀成桌機結論 |
| L3 ×4 | `duckdb` · `requests` · `urllib3` · `jinja2` | `engine_core` 共用基座件裝在使用者層,主層沒有 → 版本會蓋過主層而沒人看見。**這就是 `duckdb 2.0.0` 移除 `Relation.fetchone` 弄掉 `VRN_ENG115` 自測的機制** |
| L4 ×7 | `plotly` `scipy` `loguru` `tqdm` `filelock` `httpx` `orjson` | 冊上是共用基座件,容器沒裝 |

每一筆的 `evidence` 欄都寫了量測地點,不會被誤讀。

---

## 八 各境相依閉包(給桌機)

17 境 · 140 件次。`via_vrn_312` 33 · `via_nlp` 24 · `via_vdf_312` 18 · `via_mix_ds_np2_M` 10 · `via_paddle_311` 9 ·
`via_tools_312` 9 · `via_vap_312` 8 · `via_html_312` 5 · `via_iso_ml_cuda_H` 5 · `via_iso_quarantine` 5 ·
`via_iso_webui_M` 4 · `via_iso_scrape_H` 3 · `via_mix_api_v2_M` 3 · `via_camelot_311` 1 · `via_mix_http_M` 1 ·
`via_onnxruntime` 1 · `via_tabula_311` 1。

全量在盤冊 `env_closure`,計畫已逐境展開成可貼的指令。

---

## 九 自測裡刻意放的回歸條

這些不是湊數,每一條都對應我這輪自己犯過、或工具抓到我的錯:

| 條 | 防的是 |
|---|---|
| ⑥ 家族覆蓋不為零 | 把 `members` 讀成 `packages` → 覆蓋變 0 → 誤報全樹失治 |
| ㊼㊽㊾ 自家模組判定 | 把 `via_nlp_engine` / `VRN_SupportBridge` 之類算成第三方缺件(憑空造出 31 個假缺件) |
| ㉑b ABSENT 不重複報 L7 | 同一件同時報 L6 + L7 → 黃燈灌水 65 筆 |
| ㉑e PIP_NAME 值要正規化 | `pdfminer.six` 查不到索引鍵 `pdfminer-six` → 誤報 L5 |
| ㉑f 冊上對映覆蓋引擎內建 | 正本放錯地方 |
| ㊿ L10 不混進 libs 輪次 | 自家檔不在位被當成要裝的套件 |
| ㊽b–e AST 剖不過不得默默吞 | 全景工具報我 `L284 SWALLOW` —— 它說得對:剖不過就讀不到那支檔的 import,盤冊缺一塊卻看起來很完整 |
| ㉜b 指紋對剖不過敏感 | 多一支剖不過 = 盤冊真的變了,不該判「沒變」而不出新版號 |
| ㉝㉞㉟ 盤冊 add-only | 覆寫已發布版號 |
| ㊲ 不教人加 `UV_NO_CONFIG` | 把三鏡像退化成一個 |
| ㊳ 同意閘留給操作員 | 代設閘 |
| ㊺ 正本冊讀過後位元不變 | 讀冊時誤寫 |

---

## 十 登冊 / 閘

| 項 | 值 |
|---|---|
| 需求冊 | `VIA_Requirements_SSOT_v0228.json` · `VCGC-REQ200`(PARTIAL,`blocked` 寫明 R2 卡在同意閘) |
| 工作流冊 | `VIA_Workflow_VCGC_SSOT_v0132.json` · `VCGC-WKF026` `libs_inventory`(7 步 / 9 條驗收) |
| 盤點冊 | `VIA_VCGC_FunctionInventory_SSOT_v0201.json` · 站 `C-libsinventory-v0100` |
| 交接冊 | 案 `C-libsinventory-v0100` + 工作項 `VCGC-REQ200:libs-inventory` |
| 交接閘收據 | `handoff test` → **rc 0 · marker true** |

需求冊 `tally` 這次改成由 `requirements` 逐筆重數(v0227 存的數字已經落後,不是本輪改的)——
差額不等於「只加了一筆」,所以在 `tally_note` 裡寫清楚了。
