# 批688B · 三個洞一次補:pull 被冊擋、抓官方料零列還炸、`--only` 只吃一半

操作員貼回(HEAD 仍 `53736e39`=批686):

```
git pull  → error: Your local changes to … VIA_VRN_LogicArchitecture_SSOT_v0100.json would be overwritten by merge. Aborting
VDF_ENG082 run --only 2330,2454 → 目標 1 檔:2330.TW · yfinance Ticker failed: Yahoo API requires curl_cffi session not requests.Session(兩次)
                                → 零列 → Traceback CatalogException: Table tw_financial does not exist
ENG074 v0114 → No such file(批687 沒拉到,因為 pull 被擋)
via-vrnlogic sync-db → 6 庫 OK(邏輯庫同步 落後 6 → 同步 6,結)
```

## 一 · 量到的(LL329)

| 看到 | 其實是 |
|---|---|
| pull 被 `VIA_VRN_LogicArchitecture_SSOT_v0100.json` 擋 | `via-vrnrun` 第一站 `via-vrnbook build` 每建一次就把 `built_at` 寫成當下時間——**內容一個指標都沒變,檔案永遠是髒的**;這本冊是「刻意入倉」的冊(再生物還原閘 MDL167 不還原它),於是每跑一次 VRN 就把下一次 pull 擋掉。MDL167 docstring 寫的「三次卡死同一個病根」,這是第四次,換了一本冊 |
| `目標 1 檔` | PowerShell 把 `2330,2454` 當陣列拆成兩個參數,`--only` 只吃到第一個 |
| yfinance 兩次 failed → 零列 | 收容件把「requires curl_cffi session」的例外吞成 WARNING 回空列;v0100 只在 TypeError 才退原生,那條路永遠走不到。容器實測:原生 yfinance 對 2330.TW 0.7s 拿到 54×5 的損益表;而**注入 AegisNexus session 那一趟在容器不是拒收,是在 urllib3 Retry 退避睡眠裡爬**(faulthandler 75s 堆疊:`retry.py _sleep_backoff` ← `yfinance … _fetch_fundamentals_payload`;Cookie/crumb RetryError 一再重試),一檔幾分鐘才回空列——料抓得到,是我們自己的 session 注入把它擋掉、還拖慢 |
| Traceback `tw_financial does not exist` | 零列之後 `SELECT COUNT(*)` 對一張沒建過的表——**零列該是誠實 rc2,不是炸** |

## 二 · 做了什麼

| 件 | 檔 | 驗 |
|---|---|---|
| 索引冊建冊器 | `via_vrn_logic_book_v0106.py`:建冊前讀既有冊,**除 built_at 外相同就不重寫**(built_at 沿用上一次真正變動的時間);內容變了才寫並印「冊已變:哪幾個鍵」;`do_build(book_path)` 可進沙盒 | **十七檢 17/17**(⑰ 第二次 build 位元相同;改內容才重寫);真冊第二次 build 印「冊未變」 |
| 三大報表 | `VDF_ENG082_FinStatements_v0101.py`:`_only_list()` 收 `--only` 後連續 token 再拆逗號;`_pull()` 注入 session 那一趟放進**看門狗執行緒**(INJECT_TIMEOUT_S=40s):逾時 / 拒收 / 零列 都改走原生(tag 講明哪一種);原生那一趟**另開子行程**(yfinance 的 YfData 是單例,注入過一次 session 之後同行程「不帶 session」也在爬——容器實測看門狗之後的原生趟一樣不回;子行程=乾淨 yfinance,容器 2330.TW 12 列 2.8s);零列 → 表未建=0、誠實 rc2 講因由 | **十二檢 12/12**(⑨ 兩種 --only 寫法;⑩ 注入零列→原生有料;⑪ 兩趟零列 rc2 無 Traceback;⑫ 注入卡住→看門狗 0.5s 放掉→原生) |
| 格子 | `CGC_MDL064_SelftestGrid_v0438.py` 兩站改名;站數 287 | 全格子見四 |

## 三 · 你的手(順序很重要)

1. 先把被擋的那本冊放回去再拉(它是產物,重建就有):`git checkout -- "supportive modules/registry/VIA_VRN_LogicArchitecture_SSOT_v0100.json"` → `git pull`(以後用 `via-reload`,它會先 stash 再拉)。
2. 拉到 批688B 之後,`via-vrnbook build` 第二次會印「冊未變」,pull 不再被它擋。
3. 官方料:同意閘後 `via-finstat run --only "2330,2454"`(加引號;不加也吃得下了)→ 貼回每檔括號裡的車道 tag 與 `[三大報表計]` 行。
4. 然後 `ENG074 v0114 --verify` 與 `--official`,貼回 `[官方核對]`、`__alignment__`、`✗` 列。

## 四 · 本批實測(容器)

```
via_vrn_logic_book v0106 --selftest   十七檢 OK 17 · FAIL 0;真冊第二次 build 印「冊未變(built_at 沿用)」,git status 乾淨
VDF_ENG082 v0101 --selftest           十二檢 OK 12 · FAIL 0
VDF_ENG082 v0101 run --only 2330 2454 --years 3(容器真跑;同意閘只為量測暫設;沙盒庫)
   [1/2] 2330.TW +10 列 · [2/2] 2454.TW +10 列 · MOPS 探路 OK len 686 · 表 tw_financial 共 20 列(年度 3 + 季 7 各檔)
   2330.TW 2024-12-31 營收 2,894,307,700,000 · EPS 45.25 · 毛利率 56.12(= ENG074 ㉘ 夾具用的那組真值)
   注入 AegisNexus session 那一趟:40s 看門狗逾時 → 原生子行程 2.8s 有料(tag 講明)
registry-sync --apply                 活 6017;契約 19/19 OK
全格子 v0438(LL117)                  OK 255 · FAIL 20 · SKIP 6 · TIMEOUT 0(257s;GRID_20260921_111252)· 終判 FAIL 集對 批687 逐站相同:新紅 0 · 消失 0
```
