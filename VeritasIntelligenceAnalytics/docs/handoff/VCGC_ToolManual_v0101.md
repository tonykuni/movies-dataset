# VCGC 開發支援工具說明書(白話版)v0101

> 2026-11-22 依操作員令「整理好工具,用中文白話文詳細說明工具用途」編寫。
> 所有工具都由 **VCGC 管理器 `CGC_SystemManager`** 統一指揮(`toolbox` 動詞)。
> v0101(2026-11-22 09:29):加「全景連線 `connect`」一節;其餘照 v0100。
> 這本說明書本身也是管理器讀的:`python CGC_SystemManager_v0118.py toolbox help <代號>` 會印出下面對應那一節。

---

## 一張表看懂:十個工具在做什麼

| 代號 | 白話名稱 | 一句話用途 | 什麼時候用 |
|---|---|---|---|
| `token` | 省 Token 工具 | 讓 AI 只讀「重點卡片」,不用整檔讀 | AI 每次要看程式之前 |
| `guard` | 全景守衛 | 一次把程式從頭到尾體檢一遍,能安全修的就修 | 改完一批程式、要上傳之前 |
| `fuse` | 模組整合去重(拳腳) | 把散在很多檔的函式整合成一個單檔工具庫,順便找重複程式 | 想整理重複功能、要打包工具時 |
| `install` | 安裝閘 | 裝套件的唯一大門 | 缺工具、缺套件時 |
| `handoff` | 交接閘 | 檢查交接資料齊不齊、證據有沒有失效 | 每次接手工作、收尾前 |
| `numbering` | 編號系統 | 幫每個檔、每個函式發號,並查有沒有掉號或重號 | 新檔落地後 |
| `sdd` | SDD 驗證 | 檢查需求、工作流、編號三本冊彼此對不對得起來 | 改了需求冊或工作流冊之後 |
| `applyrun` | 一鍵套用啟動器 | 把上面很多步驟排成幾條道,一次跑完 | 主機每天實跑 |
| `manager` | VCGC 管理器本身 | 總指揮;另外負責 AI 用戶端路由(omniroute) | 隨時 |
| `accel` | 加速器 VeritasCeleritas | 讓掃描、平行處理變快;每個工具自己會載 | 不用手動叫 |

**它們怎麼串在一起**

```
改程式 ─→ guard 體檢(只看改過的檔)─→ 有紅就修 ─→ guard 再掃(沒變就 304)
   │                                         │
   └─→ fuse 找重複 / 整合工具庫              └─→ numbering 發號 → sdd 驗證 → handoff 交接閘
                                                                              │
缺套件 ─→ install(安裝閘)                       applyrun 每天一次全跑 ←──────┘
AI 讀程式 ─→ token(只讀卡片)
上面全部 ─→ manager toolbox check(核十個工具有沒有漏)
```

**燈號怎麼看(四色,全部工具一致)**

- 綠:做完、有證據、沒問題。
- 黃:還沒做完,或有要注意的地方(例如複雜度太高、少了說明),不會壞但要排時間處理。
- 紅:有錯、會壞、或被擋下;要先處理。紅燈會慢慢閃。
- 灰:沒跑、沒裝、或不適用(例如沒有 YAML 檔,YAML 檢查就灰)。**灰不是綠**,只是沒有證據。

---

## 省 Token 工具 `token`

**用途**:AI 要看程式時,不必把上千行的檔整個讀進對話。它先產生「骨架卡」(這檔有哪些函式、在第幾行、第一句說明),AI 要改哪一個函式再只拿那一段。
等於先看目錄再翻那一頁,通常可省 80%~95% 的讀取量。

**怎麼叫**(在倉根):
- 骨架卡:`python "VeritasIntelligenceAnalytics\supportive modules\registry\CGC_MDL158_VIAPanoramaAuditRepair_v0121.py" read <檔或資料夾>`
- 只拿一個函式:`… slice <檔> <函式名>`
- 跑測日誌只留判決行:`… digest <日誌檔>`
- 沒變就不重讀:任何 `read` 後面加 `--if-etag <上次卡片上的 etag>`,沒變只回一行「304」。

**注意**:v0121 起,同一個檔換參數(例如 `--depth 3`)會得到不同的 etag,不會再誤回「沒變」。
**界線**:只讀,不改檔、不執行被讀的程式。

---

## 全景守衛 `guard`

**用途**:對「任何專案」做一次完整體檢,再做一輪「保證不改變程式行為」的安全修復。
可以想成:醫生先全身檢查(掃描),再只做不會出事的小手術(修復),手術做在「複製出來的副本」上,原本的檔一個字都不動,你看過再決定要不要用。

**它檢查什麼**
1. 自己的 Python 結構檢查(語法、例外被吞、過深的巢狀、重複程式碼、少說明……)。
2. 15 個在地免費工具(沒裝就灰燈,不會自己上網下載):

| 工具 | 白話用途 |
|---|---|
| ruff | 一般程式錯誤與風格(例如用了沒定義的變數 → 紅);另看格式有沒有跑掉 |
| mypy | 型別對不對(把字串當數字用之類) |
| pyright | 第二套型別檢查(要 Node.js) |
| bandit | 資安風險(例如 `shell=True`、寫死密碼) |
| detect-secrets | 找不小心寫進程式的密碼、金鑰(只報種類和行號,不顯示內容) |
| vulture | 找沒人用的程式(死碼) |
| radon | 函式太複雜(複雜度分級,最多黃) |
| lizard | 函式太長、參數太多(也看 JS 等其他語言) |
| pylint(重複碼) | 跨檔案「複製貼上」的程式 |
| interrogate | 有說明文字(docstring)的函式佔幾成 |
| codespell | 拼字錯誤 |
| deptry | 用了沒宣告的套件、宣告了沒用的套件 |
| pip check | 這台電腦裝的套件彼此有沒有版本衝突 |
| yamllint | YAML 設定檔語法 |
| PSScriptAnalyzer | PowerShell 檔的錯誤;另外一定檢查「`param()` 必須是第一句」 |

3. 內建:JSON 檔語法;VIA 專屬規範(加速器橋、網路橋、禁用 TA-Lib、程式不准自己打開同意閘、PS 加速橋)。

**怎麼叫**
- 由管理器(建議):`python …\CGC_SystemManager_v0118.py toolbox run`(只掃 `origin/main~8` 之後改過的檔,順便跑模組整合檢查)
- 直接叫:`python …\VIA_PanoramaGuard_v0103.py scan --root <專案資料夾> --changed-since origin/main`
- 安全修復:把 `scan` 換成 `repair`;加 `--tool-fix` 會多用 ruff 的「安全修正」(也是只改副本)
- 看有哪些工具:`… tools`

**會產生什麼**(都放在電腦的暫存資料夾 `VIA_PanoramaGuard`,不在專案裡)
- `pastepack.txt`:給 AI 的貼回包,最多 300 行,只列黃紅,最後一行是 `NEXT:` 下一步。
- `tools.html`:四色燈工具頁(燈在第一欄)。
- `results.sarif`:業界通用格式,VS Code 等工具都看得懂。
- `report.json` / `tools.json`:完整明細;`overlay` 資料夾:修好的副本。

**看到 FAIL_STOP 怎麼辦**:卡片上的 `blocked` 會列原因(v0103 起)。常見的:
- `scan_baseline_regression`:同一個範圍再掃,紅燈比上次多 → 有東西變糟了。
- `BASELINE_RESET_REQUIRED`:規則設定改了,要重新建立基準。
- `source_drift`:掃描途中檔案被改了(例如 OneDrive 同步),等同步完再跑。

**界線**:不執行被掃的程式、不連網、不改原檔;安裝工具只經安裝閘。

---

## 模組整合去重(拳腳)`fuse`

**用途**:把一個資料夾裡很多 Python 檔的「公開函式」整合成**一個單檔工具庫**(FNC-LIB),
之後用一個名字就能叫到任何函式,不用記它在哪個檔;同時找出「一模一樣」或「只差換行」的重複程式,算出可以省多少空間。
可以想成:把散在各抽屜的工具收進同一個工具箱,並標出哪幾把其實是同一把。

**怎麼叫**(由管理器叫,會自動帶上鎖定的加速器):
- 檢查套件:`python …\CGC_SystemManager_v0118.py fuse doctor`
- 先預覽(不產生任何檔):`… fuse plan <來源資料夾>`
- 真的建置:`… fuse build <來源資料夾> --expect-plan <預覽給的指紋>`(預覽後來源又變了就拒絕)
- 自我測試:`… fuse selftest`
- 發布 / 還原:`… fuse publish <產物> <目的地.py>`、`… fuse rollback <目的地.py> <備份檔>`

**會產生什麼**(在暫存資料夾 `VIA_ModuFuse`):`fnc_lib.py`(單檔工具庫)、`panorama.manifest.json`(稽核)、`DISPATCH_PROMPT_MINIFIED.md`(給 AI 的精簡指令表)、`snapshots`(原檔逐位元組快照)。

**注意**
- 同名函式不只一個時,要寫成 `模組::函式` 指定版本,不會亂猜。
- 有 `--strict`:缺型別、缺說明、用 print、可變預設值就停。
- 原檔是操作員上傳的 v0101,一字未改;它沒有 VIA 加速器橋標記,全景守衛會提醒(黃),要補請出薄尾新版。

---

## 安裝閘 `install`

**用途**:VIA 規定「裝套件只能走這一道門」。它會先檢查現有套件衝突、再裝、裝完驗證能不能載入,並登記到套件冊。
**怎麼叫**:`python …\CGC_SystemManager_v0118.py toolbox install`(先列出全景守衛與模組整合還缺什麼);加 `--apply` 才真的裝。
**注意**:要連網時需要兩道同意閘;同意閘只能由操作員端的啟動器在「那一次安裝的行程」裡打開,裝完還原,不寫進任何檔。AI 不替你開。

---

## 交接閘 `handoff`

**用途**:每次接手前檢查「交接資料齊不齊」:哪些需求做完、哪些測試證據已經失效(因為程式改了)、哪些改過的程式沒有測試。
**怎麼叫**:`via-vcgc handoff check`
**看燈**:交接閘綠只代表「交接資料完整」,不代表驗收通過;驗收要看 `closeout_lamp`。
**v0111 起**:VCGC 只算自己的列;VDF / VRN / VQG 的問題放在「他系統 · 只讀」區,由它們自己的管理器處理,互不拖累。

---

## 編號系統 `numbering`

**用途**:幫新檔、新函式、新需求發正式號碼,並稽核「只增不減」:有沒有號碼不見(遺失)、有沒有被改身分、有沒有重號。
**怎麼叫**:`via-vcgc run CGC_MDL237_NumberingSystem audit`(稽核);發號由批次流程用 `--apply --scope <檔…>` 只登本批。
**看燈**:遺失 0 · 改身分 0 · 重號 0 才算過。

---

## SDD 驗證 `sdd`

**用途**:檢查需求冊、工作流冊、編號冊三本彼此對得起來(需求有歸屬、工作流引用的需求存在、步驟都有號)。
**怎麼叫**:`via-vcgc sdd check`;要鎖定工作流用 `sdd lock`(交接閘紅的時候會拒絕)。

---

## 一鍵套用啟動器 `applyrun`

**用途**:把每天要做的事分成幾條「道」一次跑完,例如 G 道(Graphify、AI 路由、備份檢查)、K 道(三系統收尾驗證)、A 道(啟用 VDF / VRN 產出)。
**怎麼叫**:主機用 `Invoke-VIA-ApplyAll` 那支 PS;它會自己找倉、快轉、跑、把貼回包放進剪貼簿。

---

## VCGC 管理器本身 `manager`

**用途**:VCGC 的總指揮。本版新增 `toolbox`,一個入口管全部開發支援工具,並核對「有沒有漏」。

**`toolbox check` 對每個工具核七件事**
1. 尾版在(檔案存在)
2. 有編號
3. 有登錄(元件冊)
4. 有交接測試案
5. 有盤點站(全功能串測會跑到)
6. 管理器有路由(叫得到)
7. 工具類另核:引擎版本冊有登記、鎖冊指到尾版

全齊 = 綠;缺任何一件 = 黃,並列出缺哪幾件;檔案不見 = 紅。

**其他動詞**:`toolbox help [代號]`(印本說明書)· `toolbox install [--apply]` · `toolbox run [--since <參照>]` · `guard …` · `fuse …` · `omniroute`(把 VCGC 的 MCP 伺服器設定給五家 AI 用戶端)。
**報告**:`VIA_Reports\vcgc\toolbox\TOOLBOX_latest.txt / .html / .json`。

---

## 加速器 `accel`

**用途**:VeritasCeleritas 是 VIA 的平行處理加速器;全景守衛、模組整合在掃很多檔時會自動用它分工。
**注意**:只認「鎖冊指定、雜湊對得上」的那一版(目前 v1141);對不上就退回標準庫,或在要求加速器的模式下直接擋下,不會偷用來路不明的版本。

---

## 全景連線 `connect`

**用途**:一次看清「各類文件能不能、經哪條路讀到」:VCGC 的 MCP 接到哪些 AI、外部工具裝了沒、備份讀不讀得回來。只看不改。

**一張矩陣四段**
- A 通道:PC 檔案(VCGC MCP 握手)· GitHub · Claude Code · Claude Desktop · Gemini CLI · Copilot(VS Code)· ChatGPT · Manus · Perplexity · Grok。
  本機的看設定檔有沒有 `vcgc` 這一項;網頁 / 雲端的(ChatGPT · Manus · Perplexity · Grok)吃不到本機,要開公開 HTTPS 端點,和資料邊界衝突,**一律灰「待裁」,不開端點**。
- B 工具:Graphify · OmniRoute · Ponytail · Agency-mem(agentmemory / claude-mem;11-06 裁定收尾期不引入,只列不接)。
- C 備份 / 讀取:每日備份尾版的 `check`(逐檔 sha 對冊)和最新備份幾小時前。
- D 文件類型:倉裡程式、冊、文件、辦公檔、資料庫、圖各幾個;用什麼讀;MCP 能不能讀;能不能離開本機。

**怎麼叫**
- 看:`python …\CGC_SystemManager_v0118.py connect`
- 補設定:`… connect config`(只列會改哪幾個檔)→ `… connect config --apply`(只補「已存在」的 Claude Desktop / Gemini CLI / VS Code 設定檔,先留 .bak,只加 vcgc 一項,不動別的伺服器、不建新檔)
- 報告:`VIA_Reports\vcgc\connect\CONNECT_latest.txt / .html / .json`

**現在知道的缺口**:VCGC MCP 的 17 個工具全是治理類,沒有「讀一份文件」的工具,所以 AI 經 MCP 讀不到文件內容(本機省 Token `read` 可以)。要不要加「只回結構、不回內容」的讀檔工具,待裁。
