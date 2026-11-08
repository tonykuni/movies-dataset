# 各 AI 近三日對話紀錄稽核 + 技能引擎規格落差 — 2026-11-08

操作員令:「授權給你一切完成指令。PR #610。啟動 MCP:檢查各 AI 近三日的對話紀錄。」
+ 貼回 CLAUDE SKILLS AUTONOMOUS INTEGRATION ENGINE 規格 + 一個 Gemini 分享連結。

---

## 〇 先說三件我做不到 / 不該做的,不含糊

| 事 | 實況 |
|---|---|
| **desktop-commander MCP 不是桌機** | 它報 `platform: linux` · `containerName: vm` · `node /opt/node22/bin/node` · `python3 3.13.16` —— 這些全是**本容器**的值。它跑在雲端容器裡,看得到的是容器的檔案系統,不是你的 Windows 桌機。`allowedDirectories: []`、`defaultShell: /bin/sh`。所以「用 MCP 去讀桌機上各 AI 的對話紀錄」這條路在這個 session 走不通。 |
| **Gemini 分享頁讀不到** | 用無頭 Chromium 實試兩個網址(含 `?social_preview=true`),HTTP 200、HTML 873 KB,但 `innerText` 長度 **0**,og 只給 `og:description=Created with Gemini`。內容沒有端給未登入的客戶端。若裡面有指令,請把文字貼過來。 |
| **那個 `cshk_…` 連結** | 是 Claude Code 的**工作階段**連結(裡面那段 id 就是這個 session),不是 MCP 端點。MCP 要的是指令(stdio)或 HTTP 端點。 |

能量到的我全量到了,下面每一格都有來源。

---

## 一 近三日對話 / 工作紀錄(量測,不是回憶)

視窗 **2026-11-06 → HEAD**(取自 git,不用機器當下時間,所以可重現)。

| 指標 | 數 | 來源 |
|---|---|---|
| 提交 | **133** | `git log --since` |
| 改檔次 | **1618** | 同上 `--name-only` |
| 車道分佈 | docs 1333 · VCGC 239 · VRN-2 26 · VAP 11 · VQG 4 · VDF 3 · 其他 2 | `VIA_ThreeDayLock scan` |
| 合併的 PR | **#603 → #610 共 8 個**,全部 merged | GitHub |

### 誰留下的紀錄(commit 作者 / Co-Authored-By)

| 身分 | 提交數 | 說明 |
|---|---|---|
| `Claude`(AI 直接提交) | 90 | 雲端 session |
| `Tony Huang` / `tonykuni`(你) | 45 | 含 8 個 merge commit |
| Co-Authored-By **Claude Fable 5.1** | 73 | 本 session 早段 |
| Co-Authored-By **Claude Opus 5** | 39 | 本 session 後段(換模型) |

> 兩個 Co-Authored-By 加起來 112 > 90,因為有些提交是你推的但帶 AI 共同作者。

### 另一個 AI(Codex)的紀錄在哪裡

Codex 的「對話紀錄」不在 git,在 **PR review**。近三日八個 PR 的標題自己記著它:
`#607 修 Codex 三項` · `#608 修 Codex P1(交接閘崩潰)` · `#609 修 Codex 兩項` · `#606 修 Codex 三項 P2` ·
`#605 修 Codex 四項`。也就是 **近三日 Codex 至少提了 13 項,全部已修並記在 PR 標題與提交訊息裡**。

### 本 session 自己的對話紀錄(容器實況)

`/root/.claude/projects/-home-user/a5893bdc-….jsonl` —— **239.1 MiB · 56180 列**
(assistant 16391 · attachment 14581 · user 9013)。只有這一個檔,其他 AI 的紀錄不在這台機器上。

### 三日鎖現況(實測成功才鎖)

| | |
|---|---|
| 鎖住(rc 0 + 標記見到 + 有 log_sha256) | **220 案**(上輪 218,**新綠 2**) |
| 回歸 REGRESSED | **0** |
| 消失 GONE | **0** |
| 未鎖 | 23 案:`ENV_PKG 18 · DESKTOP 2 · NO_PWSH 2 · NET_GATE 1` |

未鎖那 23 案沒有一件是邏輯壞掉 —— 18 件是套件不在位(就是 libs 盤那條 R2),2 件要桌機,2 件要 pwsh,1 件要同意閘。

---

## 二 PR #610:已經合併了

| | |
|---|---|
| 狀態 | **merged** 2026-11-08T13:32:10Z by `tonykuni` |
| head | `7c1e7e8bf`(我最後推的那一個) |
| 內容 | 20 提交 · 156 檔 · +100683 / −24392 |

照版本律,已合併的 PR 不能再承載新工作。我把分支從最新 main 重開(同名 `claude/optimistic-goodall-yhalc5`,`origin/main` = `25ec39eff`),本輪的工作是新一條,會開新 PR。

---

## 三 技能引擎:你貼的規格,**今天早上就已經實作掉大半了**

你貼的 `CLAUDE SKILLS AUTONOMOUS INTEGRATION ENGINE` 規格,對應的是 **PR #608 `VIA_SkillExport v0100`**
(merged 2026-11-08T01:00:32Z,自測 56/56)。逐條對帳:

| 規格要求 | v0100 現況 |
|---|---|
| Tier 1 語意索引常駐 | ✅ `registry` —— 10 技能 · 1194 字元 |
| Tier 2 SOP 按需載入(四段) | ✅ `sop <slash>` —— 全部 SOP 5099 字元,**倍數 4.27×**(常駐只付 Tier1) |
| Tier 3 資源掛載 | ✅ `export` / `export-all` 產出 `scripts/` `references/` `assets/` |
| `SKILL.md` = YAML frontmatter + 四段 SOP | ✅ `skill_md()` |
| 零依賴防禦式腳本 | ✅ `check` 跑 PY AST 規則 + PS 唯讀驗證(沒 pwsh 誠實回 UNAVAILABLE) |
| 省 Token 可量測 | ✅ `tokens` —— 本倉 6 檔真測 **省 94.1%** |
| 手動斜線叫用 | ✅ |
| **語意自動偵測** | ❌ **缺** |
| **`[ACTIVE SKILLS: /a, /b]` 緊湊抬頭** | ❌ **缺** |
| **多技能串接 `/a + /b`** | ❌ **缺** |

**所以本輪只補那三件,不重做已經過的七件。** → `VIA_SkillExport_v0101`(add-only 薄尾,自測 **46/46 PASS**,其中含前版 56/56 全過)

```
$ python3 VIA_SkillExport_v0101.py detect "幫我看這份 PDF 財報的複雜表格,再做成時序 ETL 大表"
[ACTIVE SKILLS: /doc-extract, /data-pipe]
  /doc-extract  hybrid-layout-extraction        命中 3 —— pdf(trigger) · 財報(trigger) · 複雜表格(trigger)
  /data-pipe    high-throughput-data-pipeline   命中 3 —— 大表(trigger) · 時序(trigger) · etl(trigger)

$ python3 VIA_SkillExport_v0101.py chain "/doc-extract + /data-pipe"
[ACTIVE SKILLS: /doc-extract, /data-pipe]
  [鏈] /doc-extract + /data-pipe
  1. /doc-extract  hybrid-layout-extraction        B 資料 · 量化
  2. /data-pipe    high-throughput-data-pipeline   B 資料 · 量化
  [加速器] 19
```

### 偵測是確定性的,不是語意猜測

比對字典就是登錄表自己的 **Tier1 欄位**(`slash` / `name` / `trigger` / `category` / `desc`)——
`trigger` 欄本來就是設計時寫好的觸發語。命中哪一條就把那一條印出來當證據,分數不是黑箱。
**只讀 Tier1,不碰 `sop` 內文** —— 偵測要是去讀 SOP,就等於常駐載入 Tier2,省 Token 的前提自己毀掉(自測第 ㉓ ㉔ 條守這件)。

### 兩條刻意的「不」

- **沒命中就不硬掛**:`detect "今天天氣真好"` → `[ACTIVE SKILLS: none]` + rc 3。掛錯技能比不掛貴。
- **鏈裡有假技能 → 整條不跑**(rc 2):半條鏈比沒有鏈危險 —— 前半段改了檔、後半段才發現技能不存在,就留下改一半的樹。

### 你貼的規格裡,那 10 個技能的清單被截掉了

規格寫「the 10 registered Skills below」,但下面的清單沒跟過來。冊上現有的 10 個是這些,**請你核對是不是同一批**:

| slash | 技能 | 類 | 觸發語 | 加速器 |
|---|---|---|---|---|
| `/ast-diag` | ast-driven-diagnosis | A 開發自動化 | 結構分析 / 修 bug / 跨 PS·PY 注入 | 01/03/06/13 |
| `/token-state` | token-optimized-state | A | 多 Agent 交接 / 大 repo / 資料 schema | 02/12 |
| `/self-heal` | self-healing-automation | A | 寫腳本 / CLI / 批次 / 部署 | 05/16/17/18/20 |
| `/local-env` | local-first-virtualization | A | 環境 / 依賴 / 本機套件 | 21–25 |
| `/doc-extract` | hybrid-layout-extraction | B 資料·量化 | PDF / 財報 / 複雜表格 | 19 |
| `/data-pipe` | high-throughput-data-pipeline | B | 大表 / 時序 / ETL | 19 |
| `/quant-roll` | dynamic-rolling-analytics | B | 指標 / 模型 / 估值 / 門檻 | 11 |
| `/entity-norm` | entity-ticker-normalization | B | 代碼清洗 / 跨平台對映 | 08 |
| `/canvas-zen` | minimalist-canvas-design | C 視覺·治理 | 圖表 / U/I / 報告 | 09 |
| `/ssot-gov` | ssot-filename-governance | C | 重構 / 參數登錄 / 跨子系統同步 | 08/26–30 |

全部 **READY 10/10**,每一個都對上 Celeritas 加速器。如果你要的 10 個跟這批不一樣,把清單貼過來,我按 add-only 出 v0102 換登錄表。

---

## 四 自測裡值得記的一件事

第 ④ 條紅過一次:我原本把 `trigger` 欄**連空白一起切**,結果「多 Agent 交接」被切成「多」(一字,被長度閘丟掉)+ 子詞,**整句設計好的觸發語消失了**。改成兩層切 —— `_PHRASE` 只切 `/ ·` 這些片語分隔符(保留整句),`_TOKEN` 再切空白(補子詞)—— 整句與子詞並存。第 ㉖ ㉗ ㉘ 條是這件的回歸測。
