# VPNS Self-Build｜配套參考:各流程 Top-10 本機免費 Libs · 三輪修正設計 · 未來兩回合12步

> 全部**本機可跑、免費、不外傳**。誠實標註:PowerShell 的第三方生態較小,部分格以**內建/.NET**補足;不虛構套件名。
> 語言別:**PS**=PowerShell 7 模組/.NET · **PY**=Python 套件 · **JS**=Node/瀏覽器

---

## 流程 ↔ 十大功能(對應 PS7 的 lane / 階段)

| # | 功能 | 對應 lane/階段 |
|---|---|---|
| 1 | 檔案掃描 / 雜湊 | L1/L2 Inventory |
| 2 | Markdown 解析 | L3 Parse_ReadMe |
| 3 | PowerShell AST / 靜態解析 | L4 AST_Invoke |
| 4 | JSON schema / SSOT 驗證 | 合併 → SSOT |
| 5 | 並行編排 | lane 執行 |
| 6 | 進度 / 矩陣 / HTML UI 報告 | L6→Report |
| 7 | 測試 / debug harness | test-debug |
| 8 | 靜態分析 / lint | L5 ParseGate |
| 9 | diff / patch(精準錨點) | 修正迴圈 |
| 10 | 行程監督 | orchestrator |

---

### 1 · 檔案掃描 / 雜湊
- **PS**：`Get-ChildItem -Recurse`(內建)、`Get-FileHash`(內建 SHA256)、`System.IO.Directory.EnumerateFiles`(.NET,大量檔更快)、`System.IO.FileSystemWatcher`(監看)、`Microsoft.PowerShell.Management`、`PSEverything`(接 Everything 引擎)、`robocopy`(鏡像/清單)、`fd`(外部 exe)、`System.Security.Cryptography`(自訂雜湊)、`Compress-Archive`(打包清單)。
- **PY**：`os.walk`/`pathlib`(內建)、`hashlib`(內建)、`scandir`、`watchdog`、`send2trash`(quarantine 不硬刪)、`xxhash`(快雜湊)、`blake3`、`python-magic`(型別)、`filetype`、`rich`(掃描進度)。
- **JS**：`fs`(內建)、`fast-glob`、`globby`、`chokidar`(監看)、`hasha`、`xxhash-wasm`、`blake3-wasm`、`readdirp`、`node:crypto`(內建)、`graceful-fs`。

### 2 · Markdown 解析(Read_Me)
- **PS**：`ConvertFrom-Markdown`(內建,→ AST/HTML)、`Markdig`(.NET 引用)、`PSMarkdown`、正則自解 `^#{1,6}`、`Microsoft.PowerShell.Utility`、`Show-Markdown`(內建預覽)、`platyPS`(help/md 互轉)、`YamlDotNet`(front-matter)、`Markdown.Xaml`、自建 section splitter。
- **PY**：`markdown-it-py`(推薦,CommonMark+AST)、`mistune`、`markdown`、`marko`、`commonmark`、`python-frontmatter`、`mdformat`(正規化)、`pymdown-extensions`、`myst-parser`、`beautifulsoup4`(解 render 後 HTML)。
- **JS**：`markdown-it`、`remark`/`unified`、`marked`、`micromark`、`mdast-util-from-markdown`、`gray-matter`(front-matter)、`commonmark`、`turndown`(HTML→md)、`markdownlint`、`vfile`。

### 3 · PowerShell AST / 靜態解析(兩支 Invoke)
- **PS**：`System.Management.Automation.Language.Parser::ParseFile`(**首選,官方 AST**)、`Ast.FindAll`(遍歷)、`Get-Command -Syntax`、`Tokenize`、`PSScriptAnalyzer`(規則+AST)、`platyPS`、`Get-Help`、`[scriptblock].Ast`、`Language.Tokenizer`、`Trace-Command`。
- **PY**(若要跨語言統一 AST)：`ast`(內建,Python 檔)、`tree-sitter` + `tree-sitter-powershell`(**多語言 AST 首選**)、`libcst`、`asttokens`、`astroid`、`parso`、`RedBaron`、`pycparser`、`sqlglot`(SQL)、`lark`(自訂文法)。
- **JS**：`tree-sitter`(+ powershell/py/js grammar)、`@babel/parser`、`acorn`、`espree`、`esprima`、`typescript`(compiler API)、`@typescript-eslint/parser`、`meriyah`、`cherow`、`shift-parser`。

### 4 · JSON schema / SSOT 驗證
- **PS**：`Test-Json -Schema`(**內建,Draft support**)、`ConvertTo/From-Json -Depth`(內建)、`NJsonSchema`(.NET)、`Newtonsoft.Json.Schema`、`PSToml`、`powershell-yaml`、`Assert`(斷言)、`Pester`(結構測試)、`ConvertFrom-Json -AsHashtable`、自訂 invariant 檢查。
- **PY**：`jsonschema`(**首選**)、`pydantic`(model 驗證)、`fastjsonschema`(快)、`cerberus`、`marshmallow`、`voluptuous`、`orjson`(快解析)、`jsonpatch`、`deepdiff`(SSOT drift 比對)、`genson`(從資料推 schema)。
- **JS**：`ajv`(**首選,最快**)、`zod`、`joi`、`yup`、`superstruct`、`json-schema-to-typescript`、`fast-json-stringify`、`jsonpatch`、`deep-diff`、`quicktype`。

### 5 · 並行編排(lane 同步)
- **PS**：`ForEach-Object -Parallel`(**內建 PS7**)、`Start-ThreadJob`(ThreadJob 模組,內建)、`Runspace`/`RunspacePool`(.NET,細控)、`PSJobs`(`Start-Job`)、`PoshRSJob`、`Wait-Job -Timeout`(逾時)、`ThreadJob` + `-ThrottleLimit`、`System.Threading.Tasks`(.NET Task)、`Split-Pipeline`(SplitPipeline 模組)、`Register-ObjectEvent`(非同步)。**LL-17**:快速唯讀 lane 預設順序,`-Parallel` opt-in + timeout + 空回退。
- **PY**：`concurrent.futures`(內建,Thread/Process)、`multiprocessing`(內建)、`joblib`、`asyncio`(內建)、`ray`(本機亦可)、`dask`、`loky`、`threading`(內建)、`pebble`(逾時控制)、`mpire`。
- **JS**：`worker_threads`(內建)、`piscina`(worker pool)、`p-limit`(並發上限)、`p-queue`、`async`、`Promise.all`(內建)、`bree`(排程)、`node:cluster`(內建)、`workerpool`、`tinypool`。

### 6 · 進度 / 矩陣 / HTML UI 報告
- **PS**：`Write-Progress`(內建)、`ConvertTo-Html`(內建)、`PSWriteHTML`(**強,矩陣/表格/圖**)、`PSHTML`、`Format-Table`、`Out-GridView`(互動格)、字串範本 + `-replace`(本 harness 用)、`ImportExcel`(Excel 報告)、`PSWritePDF`、`Show-Markdown`。
- **PY**：`rich`(**終端矩陣/進度首選**)、`tqdm`(進度)、`jinja2`(HTML 範本)、`pandas.to_html`、`tabulate`、`great-tables`、`plotly`(離線 HTML)、`matplotlib`、`datapane`(本機報告)、`textual`(TUI 矩陣)。
- **JS**：`cli-progress`、`ora`(spinner)、`chalk`+`cli-table3`、`blessed`/`blessed-contrib`(TUI 矩陣)、`ejs`/`handlebars`(HTML 範本)、`d3`(離線圖)、`chart.js`、`ink`(React CLI)、`console-table-printer`、`ascii-table3`。

### 7 · 測試 / debug harness
- **PS**：`Pester`(**首選,BDD 測試**)、`PSScriptAnalyzer`、`Set-PSBreakpoint`(除錯)、`Write-Debug`/`Trace-Command`、`AssertionExtensions`、`InModuleScope`(白箱)、`Mock`(Pester)、`Measure-Command`(效能)、`Start-Transcript`(記錄)、`PSKoans`。
- **PY**：`pytest`(**首選**)、`unittest`(內建)、`hypothesis`(property-based)、`pytest-cov`、`pdb`(內建除錯)、`ipdb`、`pytest-benchmark`、`freezegun`(時間)、`responses`(mock)、`tox`(矩陣測試)。
- **JS**：`vitest`(**首選**)、`jest`、`node:test`(內建)、`mocha`+`chai`、`ava`、`playwright`(UI 測試)、`sinon`(mock)、`c8`(coverage)、`supertest`、`fast-check`(property)。

### 8 · 靜態分析 / lint(Parse=0 gate)
- **PS**：`PSScriptAnalyzer`(**首選,含 AST 規則+自訂**)、`Parser::ParseFile`(Parse=0)、`Invoke-Formatter`、`Test-ModuleManifest`、`Get-Command -Syntax`、`Injection Hunter`(安全規則)、`ScriptAnalyzer custom rules`、`PSSA -Fix`、`Debug-Runspace`、`platyPS` 校驗。
- **PY**：`ruff`(**首選,超快**)、`pylint`、`flake8`、`mypy`(型別)、`bandit`(安全)、`pyflakes`、`vulture`(死碼)、`black`(格式)、`isort`、`pycodestyle`。
- **JS**：`eslint`(**首選**)、`typescript`(tsc --noEmit)、`biome`(快)、`oxlint`、`prettier`、`jshint`、`standard`、`dependency-cruiser`(相依)、`madge`(循環相依)、`knip`(死碼)。

### 9 · diff / patch(精準錨點編輯)
- **PS**：`Compare-Object`(內建)、`git diff/apply`(外部)、`DiffPlex`(.NET,行/字元 diff)、`Select-String -Context`(錨點定位)、`[regex]` 錨點取代、`Set-Content`(原子寫)、`PSDiff`、`Update-TypeData`(結構)、`New-TemporaryFile`(暫存)、`Rename-Item`(atomic)。
- **PY**：`difflib`(內建)、`unidiff`、`patch`/`python-patch`、`redbaron`(語法感知改)、`libcst`(**AST 級精準改**)、`bowler`(codemod)、`rope`(重構)、`GitPython`、`diff-match-patch`、`parso`。
- **JS**：`diff`(jsdiff)、`diff-match-patch`、`jscodeshift`(**codemod,AST 錨點**)、`recast`、`magic-string`、`ts-morph`、`unidiff`、`fast-diff`、`node-diff3`、`patch-package`。

### 10 · 行程監督(orchestrator)
- **PS**：`Start-Process`/`Wait-Process`(內建)、`Register-ObjectEvent`、`Job` 生命週期(`Get/Receive/Remove-Job`)、`System.Diagnostics.Process`(.NET,細控+逾時)、`ThreadJob` 監看、`Timeout`(逾時包裝)、`Try/Catch/Finally`(內建)、`trap`、`$PSDefaultParameterValues`、`Register-EngineEvent`(退出鉤子)。
- **PY**：`subprocess`(內建)、`psutil`(行程/資源)、`supervisor`、`multiprocessing`、`signal`(內建)、`atexit`(內建)、`tenacity`(重試)、`watchfiles`、`apscheduler`、`sh`。
- **JS**：`child_process`(內建)、`execa`、`pm2`(監督/重啟)、`nodemon`、`p-retry`、`node:process`(內建)、`signal-exit`、`foreground-child`、`concurrently`、`zx`(scripting)。

---

## 三輪全景修正設計(全面 → 順序 → 收尾;保證收斂、避免修壞)

**輸入**:每輪 `Invoke-PanoramicScan` 產出 issue 清單(帶錨點 path/kind)。
**分類(關鍵)**:建 issue 相依圖 → topological sort:
- **可同時修(independent)**:彼此不共享錨點/檔案、修 A 不動 B → 一批平行修(全面性修正)。
- **需順序修(sequential)**:有相依鏈(改 SSOT schema 才能改讀取端)→ 依 topo 序逐一(順序性修正)。
- **收尾修正**:格式/lint/註解/命名 一致化(不改邏輯)。

**每輪流程**：
1. 快照 backup(只增不減,不動原檔)→ 2. 全面批修(independent)→ 3. 順序批修(sequential)→ 4. 收尾修 →
5. **回歸閘**:Parse=0 全綠 + count invariants(檔數/引擎數不倒退)+ 目標指標不劣化 →
6. 若回歸失敗 → **rollback 到本輪快照**(避免修壞)→ 記錄該修為「需人工」→
7. 重跑 `Invoke-PanoramicScan`;issues=0 即**收斂停止**。

**≤3 輪硬上限**:超過 3 輪仍未收斂 → 停,輸出剩餘 issue 清單交人工(避免無限/過度修正把系統改壞)。
**本 harness 立場**:只**定位 + 分類 + 生 stub + 記錄錨點**,**不自動改你的原始碼**;實際修復交 `Invoke-VIA-PolyglotCheckTestRepair` + 人工核准閘。

---

## 未來兩大回合 × 12 步驟(harness 已備妥資訊/測試)

**回合 1(建立真值)**
1. R1-01 匯入 Read_Me 真實引擎清單校準 declared(取代通用 token 抽取)
2. R1-02 建 engine ↔ 檔案 對應表(精準錨點)
3. R1-03 缺件 stub → 真實實作(交 PolyglotCheckTestRepair)
4. R1-04 Parse=0 全綠(PS + `py_compile` + `tsc`)
5. R1-05 SSOT schema 驗證(`Test-Json`/`jsonschema`)
6. R1-06 lane 相依圖 topo 排序落地

**回合 2(壓測與啟用)**
7. R2-07 並行壓測 + `-LaneTimeoutSec` 校準(LL-17 空回退驗證)
8. R2-08 回歸閘 count invariants(檔/引擎/測試數不倒退)
9. R2-09 promote gate 演練(`-PromoteToken PROMOTE_VPNS_v3`,只增不減不覆蓋)
10. R2-10 matrix 報告 UI 細節(lane×step 熱度、剩餘步數精度)
11. R2-11 user-test 腳本(關鍵路徑人測)
12. R2-12 activate 系統 + 監看(`Start-Process`/`psutil`)→ 反覆 test-debug 至 perfect

> 每步完成後回跑三輪全景掃描;缺件實作與任何 promote **一律經人工核准閘**(殘留最高風險點)。
