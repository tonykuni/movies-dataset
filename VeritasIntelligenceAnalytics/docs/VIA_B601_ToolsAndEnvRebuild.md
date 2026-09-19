# 批601 — 工具清點 · BASE 與其他環境重建計畫

操作員令:「清點所有工具,依照 ENVMANAGER 重建修正 BASE 及其他環境,安裝所有工具」。

---

## 一、清點(走既有正典,不另寫盤點器)

`via-envgov tools` → **130 件**

```
來源   VIA_ToolRoster_SSOT_v0100.json ∪ Celeritas _LIB_MAP(88)∪ AegisNexus 相依(3)
狀態   ENV_ABSENT 69 · UNROUTED 59
風險   HIGH 2 · MEDIUM 9 · LOW 101 · SPECIAL 16
```

**UNROUTED 59** 是「無家族的加速器通用件」——**不排進白名單境 `via_core`**,
分發走 `via-accel-import`(MDL142)。那不是漏掉,是刻意不塞。

## 二、八個境 + BASE

| 境 | Python | 裝幾件 |
|---|---|---|
| `via_core` | 3.12 | 12 |
| `via_vrn_312` | 3.12 | 12 |
| `via_paddle_311` | 3.12 | 13 |
| `via_vap_312` | 3.12 | 10 |
| `via_vdf_312` | 3.12 | 10 |
| `via_mix_ds_np2_M` | 3.12 | 6 |
| `via_mix_http_M` | 3.12 | 3 |
| `via_iso_ml_cuda_H` | 3.11 | 3 |

`_M` / `_H` 一律**同名獨立境不借 alt**(批500/508 隔離律)。

## 三、BASE:判 **RED**

```
BASE  py3.11.15 · 件 98 · 衝突 37
  閉包 54 · 閉包外 17 · manifest 缺 23 · 封鎖家族件 14 · OS 管理不動 72
  拉出 nlp              → via_nlp(待建)          引擎影響 22
  拉出 browser          → via_iso_scrape_H(待建)  引擎影響 26
  拉出 table_extraction → via_camelot_311(待建)   引擎影響 3
  改道 → via_iso_quarantine:conan, fasteners, patch-ng
  段冊 21:並行 13 · 序 8 · **破壞候裁 4** · 波 11
  LKGC:不合格(衝突 37 條)
```

下一步(**你的手,我不代跑**):

```powershell
via-envgov apply --approve                    # 只做 GREEN 非破壞段:建境/裝件/驗證
# 目標境都綠了之後才談:
via-envgov apply --approve --approve-remove   # 破壞段
# 出事先還原:
via-envgov rollback
```

## 四、「一貼即用」的三個坑 —— 逐行讀出來的

引擎自己把產出標成「`.ps1`(一貼即用)」。逐行看過,**三個地方會安靜地做錯事**:

| # | 坑 | 貼下去會怎樣 |
|---|---|---|
| ① | 冊裡 `pip` 欄寫的是**敘述句** —— `via_vdf_312` 的 `"VIA QuantGuard intake"`(那是樹內收容件,`imp=quant_engine`) | 生成器照字面拆成三個套件名。**`intake` 在 PyPI 上真的有同名套件** → 裝到不相干的東西,整行還會失敗 → **vdf 境一件都沒裝** |
| ② | `paddlepaddle>=3.0` **沒引號** | PowerShell 的 `>` 是**重導向** → 「裝 paddlepaddle,順便把 stdout 寫進一個叫 `=3.0` 的檔」 → **套件照裝、版本釘悄悄不見** |
| ③ | 境根寫死 `/root/envs` | 那是**產它的那台**的路徑;貼到 Windows 等於把別人的路徑帶過去 |

三個都有同一個特徵:**不會當場報錯,會安靜地做錯事**。
而且 ②③ 只在「**在 Linux 產、在 Windows 貼**」時才踩得到 —— 跟 L71 同一族。

**修法(`CGC_MDL135 v0109`)**

- ① 冊上加 `install: false` + `source_kind: "in_tree"`(**只增不減**,條目保留);
  生成器照**旗標**跳過,**不靠看名字像不像**
- ② 版本釘一律引號:`'paddlepaddle>=3.0'`
- ③ 境根抽成 `$EnvRoot` 變數 + 分隔符正規化

**第㊸檢正反兩向都釘**:樹內件不得出現在 `uv pip install`,
而正常件(`duckdb`)**必須還在** —— 只擋樹內件,別把正常件也擋掉。

### 四之一、第一版的 ㊸ 自己就是一把太寬的尺

寫完之後回頭讀自己那一檢,③ 那一條我寫的是 `"$EnvRoot" in ps43`。
**標頭那一行就把它餵飽了** —— 只要 `$EnvRoot` 這五個字出現過一次就綠,
底下每一行到底有沒有真的用它,這把尺根本量不到。

把尺改成「**除了兩行該帶原生境根的以外,沒有任何一行還帶著**」,
並且**四種段各造一筆合成計畫走過去**,當場量出兩個還沒修到的洞:

| 段 | 原本印出來的 | 誰會踩到 |
|---|---|---|
| `VERIFY_TOOLS` | `uv pip check --python "/root/envs/…"` | **可執行行**,貼到 Windows 直接指到不存在的路徑 |
| `REBUILD_ENV` | `# Remove-Item -Recurse -Force "/root/envs/…"` | 註解令,但那是要人**解註解去跑**的三行 |

兩個都補走 `_ps_root`。本容器的 8 個境全缺,計畫裡**只有 `ENSURE_ENV`/`INSTALL_TOOLS` 兩種段**,
所以這兩個洞在真跑裡**印不出來** —— 是合成計畫把它逼出來的。
你那台境是在的,`plan` 會產 `VERIFY_TOOLS`;沒補的話就正好踩到。

留兩行**該**帶原生境根,而且 ㊸ **釘死必須是兩行**:
標頭那句出處(計畫在哪台算的,拿掉就沒人知道要改什麼)、和 `$EnvRoot` 那行賦值(要你改的那一行)。

順手還修了一個:`VERSION = "0108"` 寫死,檔名已經是 `_v0109` 卻印 v0108 ——
**操作員會以為自己跑的是舊版**。改成從檔名讀。

自測 **43/43**(尺改嚴之後重測,不是沿用舊數字)。

## 五、誠實界定(這一段最重要)

上面 BASE 的 `py3.11.15 · 98 件 · 衝突 37`,量的是**本容器**,**不是你的工作站**。

- 計畫的**結構**(拉出哪三族、段序、隔離律、破壞候裁要另外批准)是對的、可用的
- 計畫的**數字**(幾件、幾條衝突、哪些缺)得在**你那台**重量一次

```powershell
via-envgov tools        # 清點(唯讀)
via-envgov plan         # BASE + 各境重建計畫(唯讀)
```

**安裝是你的手**(不代裝套件):`via-envgov apply --approve`。
產出的 `TOOLS_PLAN_latest.ps1` 貼之前,**先把第 4 行的 `$EnvRoot` 改成你這台的境根**
(Windows 通常是 `"$env:USERPROFILE\envs"`)。
