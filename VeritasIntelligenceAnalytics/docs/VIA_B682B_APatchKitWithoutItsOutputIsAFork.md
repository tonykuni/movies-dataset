# 批682B · 補丁包進了樹、產物沒進樹 —— 那就是一條看不見的分岔

> **撞號**:本線與 `claude/awesome-bardeen-h0wm5v` 在同一小時各取了 批682;它先併入 main(PR #56),本批改稱 **682B**。
> 已推出去的 ad846ecf 主旨仍寫「批682」,不改歷史(L08 零 force push;同 批679b)。批號跟版號一樣是跨分支的共用資源(LL334),先併進 main 的贏。
> 批684(同一條線,08:55)也把位元相同的 v0128 收進它的分支;兩線併入時 git 自動合併,不撞。

操作員令:「接手VIA」(接手 session_01RLMQGZLcigd5Bt5aN6J4Ck;該會期批680 五檔 staged 未 commit,已由批681 登成 Z57)。
本批沒有新令;它是接手驗收的實錄照出來的:工作站 `git status` 有兩支未追蹤的 `CGC_MDL148_EngineBus_v0128.py`,
我給了 L25 側枝區塊,操作員跑了 = 留。批號:680 留給前一會期(Z57),681 已被 `claude/awesome-bardeen-h0wm5v` 佔用(LL334 掃過 30 條活分支);682 撞號見上。

## 一 · 先量(LL329)

| 量到 | 結果 |
|---|---|
| v0128 在哪 | 只在工作站。全倉 30 條遠端分支沒有一條有它;main 的尾版是 v0127,v0127 裡沒有 `NEED_INPUT` 這個字 |
| 它從哪來 | Grok 線 B600 補丁包 `_patches/Apply-B600-vrn_unified.ps1` + `CGC_MDL148_EngineBus_v0127_to_v0128.diff`(補丁包**在樹上**);操作員 2026-09-18 22:24 套的(`VIA_InputConsole_Spec_v0100.json.bak_b600_20260918_222403` 是它留的備份) |
| 之前怎麼處理 | 批604–606 三批都寫「`?? CGC_MDL148_EngineBus_v0128.py`、`_patches\`、`*.bak_b600_*` 一根不碰」;VIA_DataUpdate_B559 記「main 與本分支都沒有」。**都知道,但沒登進掉球清單** |
| 後果 | 尾版律 `newest()` 只看本機有什麼檔:工作站每一次 `via-bus` / 矩陣跑的是 v0128(自訂缺參句 → ABSENT),倉裡任何人跑的是 v0127(同一句 → 假 RED)。三天,零紅燈 |
| 側枝長什麼樣 | `local/parallel-b600-bus-v0128` = 側線 `claude/busy-bell-97sa4f` 225702bc + da89abbc(兩檔純增);與 main 的 merge-base 是 9d5cfc61(PR #54)。**不能 merge 這條分支**,會把側線 11 個 commit 一起拖進來(那是 PR #53 的事);只能 cherry-pick 那一個 commit |

## 二 · 做了什麼

| 件 | 檔(版號) | 驗 | 證據 |
|---|---|---|---|
| 落地操作員的並行線(L25「只由一隻手併」) | `supportive modules/registry/CGC_MDL148_EngineBus_v0128.py`(`_patches/` 副本見六) | cherry-pick da89abbc → ee9c4a53,作者與訊息原樣 | `git log` |
| 產物 = 正本 + 補丁 | 同上 | `patch v0127 < _patches/*.diff` 得到的檔與操作員的 v0128 **位元相同**;兩份副本 md5 `213a641272d2a0f8685e855fd6cf60ce` 相同;`ast.parse` OK | 本批容器 |
| 引擎自測 | v0128 `--selftest` | 四十八檢(49 檢)**OK 49 · FAIL 0** | 含新增 ㊾:自訂 `[ERROR]/[NEED_INPUT] --in` → ABSENT;真 traceback 仍不誤放 |
| 格子站 | 「引擎調度匯流排十九檢」`newest()` → v0128 | **OK**(57.5s) | REFAIL_20260921_083739 |
| 元件冊 | `VIA_Component_Inventory_SSOT_v0100.json` | 第一次(對 c8310908):`registry-sync --apply` 活 5908 · 新 0 · 變更 40 · 退役 1;併入 main 後以 VCGC v0118 重跑:活 5991 · 新 0 · 變更 40 · 退役 0 | 第一次退役的那一筆 = `VIA-ENV-0001`,與批681 在它的容器退役的是同一筆(見 Z79) |
| 台帳 | `VIA_AutoCode_Registry_v0100.json` +1(1274 → 1275)· 照原檔格式寫回(indent 2、非 ASCII 不跳脫、無尾換行;LL 批679b) | — | — |
| 掉球清單 | `VIA_DroppedBalls_B507.md` +4:~~Z78~~ 已結 · Z79 · Z80 · Z81 | main 已到 Z73、awesome-bardeen 分支到 Z77,本批從 Z78 起;併時取聯集(L25) | — |

v0128 對 v0127 的實質差異只有三段:`NEED_INPUT_RX`(五種自訂缺參句)、`classify_stop()` 命中即回 `("ABSENT", "**缺參數**(不是壞掉)…")`、自測 ㊾。
Register / Deck / Manager 不用動:同一支引擎、同一個名字,短令 `via-bus` 與矩陣都走 `newest()`。

## 三 · 接手驗收(容器;不是操作員的機器)

| 步 | 結果 |
|---|---|
| 對齊遠端(L25) | main = PR #55 併入(批678–679d,c8310908),CI run #288 綠;舊線 `claude/via-envmanager-governance-7cls8h` 對 main 零未併 commit |
| VCGC status | 律 99 · lessons 305 · 格子 285 站 · Register 165 · 家族 268/268 · 台帳 1274 |
| VCGC --selftest(接手時) | 二十三檢 OK 22 · FAIL 1(⑬ ACTIVE 5909/5908) → 根因 Z79;本批 `--apply` 後 **OK 23 · FAIL 0** |
| 全格子 v0432 第一輪 | OK 254 · FAIL 24 · SKIP 7 · TIMEOUT 0(GRID_20260921_071808;新容器補齊套件、無料) |
| 補料後 `--refail` | 24 站轉綠 17 · 仍紅 7,逐站歸類:pwsh 不在 1 · 缺料 5(TWSE openapi 三車道在容器回非 JSON → 無 `tw_listings_industry`/ETF 冊;sidecar 庫 0 份;綠燈率自指)· 尺 1(⑬,Z79) |
| 推之前的全格子(LL117) | OK 273 · FAIL 6 · SKIP 6 · TIMEOUT 0 · 381s;仍紅 6 站全是容器(PowerShell 語法與參數名閘十一檢( / 產業混合分類冊六檢(批155) / 治理台 UI Matrix 八檢(批201) / 首頁全能引擎三十九檢(批448) / 治理主控台六檢(批258) / 市場分析引擎自測(批259 合流)):pwsh 不在 · TWSE openapi 三車道回非 JSON → 無產業表/ETF 冊 · sidecar 庫 0 份 · 綠燈率自指;⑬ 已綠(GRID_20260921_083959) |

### 順帶照出的四件

1. **⑬ 是尺,不是樹**(Z79):`live_components()` 把執行期產物 `TOOLS_PLAN_latest.json` 裡的虛境 `(未路由:加速器通用件)` 算成活元件;工作站有這份檔、容器沒有。批681 與本批各自在容器 `--apply` 都把 VIA-ENV-0001 退役,一併入 main,工作站的 ⑬ 就會變「缺 1」,工作站再 `--apply` 它又復活。根治要開 MDL149 v0119(v0118 已被批681 佔),把 runtime 列排除在等式之外。
2. **㉔ 在沒有價表的環境必紅**(Z80):ENG090 `roster()` 的 ABSENT 早退分支沒帶「不代設」,它自己的檢就把它判紅。補料後轉綠只是因為不再走那條分支。
3. **開機更新器的自補在新容器是壞的**(Z81):jieba 在 Debian setuptools 68 建輪失敗,pip 把整份 requirements 放棄,結果 15 條 OmniFetch 車道全因 `No module named duckdb/pandas` 假敗。`--use-pep517` 裝得過;補裝後重跑,收尾 YELLOW(vrn YELLOW · vap YELLOW),10 車道真抓到料。
4. **我自己違了一次 L50**:補裝套件時把 TA-Lib 裝進容器,六域現況矩陣當場照紅「talib 竟然裝著」。判得對,已移除,站轉綠。尺比我先想起律。

## 四 · 三條活線(併入前先看這張表;LL334)

| 線 | 狀態 | 佔用的號 |
|---|---|---|
| `claude/awesome-bardeen-h0wm5v` | 批681/682 已併 main(PR #56);批683/684 在分支上(PS/PY 橋;收 PR #57 的 v0128 與 VDF 審視文) | 批681–684 · VCGC v0118 · Grid v0433 · LL336 |
| `claude/busy-bell-97sa4f`(PR #53) | 領先 11 · 落後 6 · dirty(撞 `VIA_VRN_LogicArchitecture_SSOT_v0100.json`、`VIA_UI_MasterControl_v0100.html`) | Register v0241 · Manager v0147 · Deck v0158 · Grid v0431 |
| `claude/brave-goldberg-ri5k42`(本線;PR #58) | main(批681/682)+ 本批 | 批682B · EngineBus v0128(與批684 位元相同) |
| 前一會期 | 批680 五檔 staged 未 commit(Z57) | 批680 |

建議併入順序(操作員裁):awesome-bardeen 的 683/684 → main;本線 PR #58 再對 main 取一次聯集(台帳/元件冊/掉球);PR #57、#53 依批684 的量測可關(內容 ⊂ main/awesome-bardeen);Z57 看前一會期推不推。

## 五 · 教訓(未編號:律冊停在 LL305,LL306 之後只在批文與 commit 訊息裡,見 Z59;LL336 已被批683/684 用掉)

> **補丁包進了樹、產物沒進樹,就是一條看不見的分岔。**
> 尾版律只看本機有什麼檔:工作站三天裡每一次矩陣都跑在倉裡不存在的版本上,而且不會有任何一盞燈紅。
> 收到補丁包的那一批就要把產物一起落地;做不到,至少把「本機有、倉沒有」登進掉球清單,不能只寫在批文裡說「一根不碰」。

## 六 · 收

| 檔 | 是什麼 |
|---|---|
| `supportive modules/registry/CGC_MDL148_EngineBus_v0128.py` | 落地(操作員的 commit,cherry-pick) |
| `_patches/CGC_MDL148_EngineBus_v0128.py` | **不收**:與 registry 正位那一份位元相同(md5 213a6412,L23 有證據),第二顆頭不留;批684 同一判斷。ee9c4a53 裡有它,本批合併 commit 移除 |
| `supportive modules/registry/VIA_Component_Inventory_SSOT_v0100.json` | registry-sync:變更 40 · 退役 1 |
| `supportive modules/registry/VIA_AutoCode_Registry_v0100.json` | 台帳 +1 |
| `docs/VIA_DroppedBalls_B507.md` | ~~Z78~~ · Z79 · Z80 · Z81 |
| `docs/VIA_B682B_APatchKitWithoutItsOutputIsAFork.md` | 本文 |
