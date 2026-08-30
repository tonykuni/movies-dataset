# VOFIE v1.4 免費 CPU 工具、函式庫與降級路徑

VOFIE 不在執行時自動安裝工具。所有外部工具採 `DETECT_ONLY_NO_AUTO_INSTALL`，JavaScript 路由到 `via-ui`，PowerShell 路由到 `via-ps`，不得污染 base。

```powershell
python .\Veritas_OmniFormat_Intelligence_Engine.py tool-audit --language all --probe-installed --report .\Veritas_VOFIE_POLYGLOT_TOOL_AUDIT.json
```

未安裝工具會標記 `NOT_INSTALLED`；只要已登記唯讀 fallback，Activation 不會因選用工具缺少而失敗。格式化、重構、build、網路或服務型工具只建立執行計畫，不自動呼叫。

## JavaScript 免費 CPU Top 20

| Rank | Tool | 主要定位 | 缺少時 fallback |
|---:|---|---|---|
| 1 | Node.js | 語法、runtime smoke | Python JS 結構掃描 |
| 2 | TypeScript | 型別與語法 | Component symbol extractor |
| 3 | ESLint | 靜態分析 | Node check + 本地規則 |
| 4 | Biome | lint／format | 保留格式並報告 |
| 5 | Prettier | 格式檢查 | 保留原格式 |
| 6 | Jest | 單元測試／mock | Node assert fixture |
| 7 | Vitest | 單元／元件測試 | Node assert fixture |
| 8 | Mocha | 單元測試 | Node assert fixture |
| 9 | c8 | Coverage | 測試結果計數 |
| 10 | Semgrep CE | 安全／靜態掃描 | 本地 security rules |
| 11 | dependency-cruiser | 相依圖／架構規則 | Regex import graph |
| 12 | Madge | 相依圖／循環 | Regex import graph |
| 13 | Knip | 未使用檔案／export／dependency | Registry reference scan |
| 14 | esbuild | build／transpile | 不 build，保留來源 |
| 15 | SWC | transpile／minify | 不 build，保留來源 |
| 16 | Babel CLI | transpile | 不 build，保留來源 |
| 17 | jscodeshift | codemod | Candidate-only rewrite |
| 18 | ts-morph | TypeScript AST／refactor | Candidate-only rewrite |
| 19 | Stylelint | CSS 靜態分析 | CSS brace／token scan |
| 20 | html-validate | HTML／accessibility | Python HTML parser |

## PowerShell 免費 CPU Top 20

| Rank | Tool | 主要定位 | 缺少時 fallback |
|---:|---|---|---|
| 1 | PowerShell 7 | runtime／語法 | Python PS 結構掃描 |
| 2 | System.Management.Automation AST | 正式 AST | Python PS 結構掃描 |
| 3 | PSScriptAnalyzer | 靜態分析／format | AST + 本地安全規則 |
| 4 | Pester | 單元／mock／coverage | Python contract bridge |
| 5 | PSRule | Policy／schema | JSON contract rules |
| 6 | PSResourceGet | 模組 inventory／package | Detect only |
| 7 | PowerShellGet | 模組 inventory／package | Detect only |
| 8 | PlatyPS | Markdown help | Help extractor |
| 9 | InvokeBuild | Build／task runner | Python stage runner |
| 10 | psake | Build／task runner | Python stage runner |
| 11 | PSDepend | 相依 inventory | Manifest scan |
| 12 | ThreadJob | CPU bounded parallel | Serial bounded execution |
| 13 | PoshRSJob | Runspace parallel | Serial bounded execution |
| 14 | ImportExcel | Spreadsheet I/O | Python CSV／XLSX adapter |
| 15 | powershell-yaml | YAML I/O | Python／text adapter |
| 16 | PSToml | TOML I/O | `tomllib` |
| 17 | PsIni | INI I/O | `configparser` |
| 18 | PSWriteHTML | HTML report | Self-contained HTML |
| 19 | Pode | Local web／API | Offline HTML，不啟 server |
| 20 | PSFramework | Logging／configuration | JSONL audit chain |

## 需求式調用

先建立計畫，不執行外部工具：

```powershell
python .\Veritas_OmniFormat_Intelligence_Engine.py tool-plan .\module.js `
  --functions syntax_parse,static_analysis,dependency_graph `
  --report .\JavaScriptToolPlan.json
```

明確加入 `--execute-safe` 時，只允許唯讀 `syntax_parse` quick check；輸入前後 hash 必須一致：

```powershell
python .\Veritas_OmniFormat_Intelligence_Engine.py tool-plan .\launcher.ps1 `
  --functions syntax_parse,unit_test,build_automation `
  --execute-safe `
  --report .\PowerShellToolPlan.json
```

其他功能維持 `PLAN_ONLY`，待使用者明確指定工具與 sandbox 後才可執行；不允許 `--fix`、`--write` 或直接改寫來源。

## 既有核心函式庫

| Library | 用途 | 缺少時 |
|---|---|---|
| Python 3.11+ standard library | Reader、IR、HTML、CSV、Failure Recovery | 必需 |
| `python-docx` | 高品質 Word | stdlib OOXML DOCX |
| `pypdf` | PDF 文字抽取 | 僅 PDF input HOLD |
| `tkinter` | Windows 視窗 | simple CLI／PS7 launcher |
| `tkinterdnd2` | 拖放 | 原生多檔選取 |
| Node + artifact adapter | 完整 PPTX／XLSX | simple 五檔模式 |
| VIA VSIS 1.2 | NLP 四動作 | deterministic local NLP |

## SSOT

- `config/tool_registry.json`：工具入口與 enable／disable。
- `config/polyglot_tool_catalog.json`：40 工具、license、CPU 成本、路由、fallback。
- `adapters/vofie_polyglot_tool_probe.mjs`：dependency-free JavaScript bridge。
- `adapters/Veritas.VOFIE.ToolBridge.psm1`：PowerShell AST／module inventory bridge。
- `tests/Invoke-VOFIE.PowerShell.Tests.ps1`：Pester 可用時的正式 PS 測試。
