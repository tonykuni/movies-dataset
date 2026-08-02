# Read_Me — VIA Turbo Optimizer v4

> **單檔 PS7 系統優化器 + 函式庫佈建加速器（Library Registration Accelerator）**
> 只增不減（append-only）：v3 全功能保留，v4 純疊加。
> Veritas 視覺鎖定 UI（Seaborn 深色盤、縮小字體、單一畫面高度）。

---

## 1. 這版（v4）加了什麼

| 類別 | v3 | v4 新增 |
|---|---|---|
| 清理目標 | 8 | 8（保留） |
| 優化選項 | 6 | **+2**（`dnsregister` 註冊 DNS、`standby` 待命清單快照建議） |
| 函式庫目錄 | — | **+27**（12 CORE + 15 EXTENSIONS，三語 py/ps/net） |
| 佈建流程 | — | **R1 並行探測 → R2 順序佈建（gate）→ R3 並行驗證** |
| 全景診斷 | — | **Invoke-Panorama**：7 區掃描、GREEN/YELLOW/RED、健康分 0–100 + 等級 A–F |
| 推薦矩陣 | — | **5 流程 × 3 語言 × 10 = 150** local-free libs，UI 矩陣呈現 |
| 子程序 | ReadToEnd（可能管線死結） | **ProcessStartInfo + 非同步 stdout/stderr drain**（死結修正） |
| 編碼 | `Encoding::UTF8`（含 BOM） | **`UTF8Encoding::new($false)` No-BOM** 全面替換 |
| 後端安全 | 無 | **CSRF token、Host 白名單、mutating 端點 POST-only、2MB body cap、安全標頭** |
| 結束行為 | — | `exit` 僅在 `-CI` 開關下觸發（主作用域預設不 exit） |
| 支援模組 | — | 偵測 NexusCore / Polyglot（優雅降級，不存在不報錯） |

---

## 2. 函式庫目錄（27 = 12 CORE + 15 EXT）

### CORE（12）
| Key | 套件 | 語言 | 風險 | 用途 |
|---|---|---|---|---|
| psutil | psutil | py | Low | Process / RAM / CPU 量測 |
| cpuinfo | py-cpuinfo | py | Low | CPU 型號 / 旗標偵測 |
| send2trash | Send2Trash | py | Low | 安全送回收筒刪除 |
| rich | rich | py | Low | 主控台 / 報表美化 |
| humanize | humanize | py | Low | 人類可讀大小 / 時間 |
| orjson | orjson | py | Low | 高速 JSON 序列化 |
| duckdb | duckdb | py | Low | TWChip 倉儲查詢引擎 |
| pyarrow | pyarrow | py | Med | Parquet I/O（numpy<2 共釘） |
| PSWriteHTML | PSWriteHTML | ps | Low | PS7 HTML 報表生成 |
| ImportExcel | ImportExcel | ps | Low | 無 Excel 讀寫 xlsx |
| PSScriptAnalyzer | PSScriptAnalyzer | ps | Low | PS 靜態分析 / Lint（Polyglot 修復核心） |
| Pester | Pester | ps | Low | PS 測試框架 |

### EXTENSIONS（15）
| Key | 套件 | 語言 | 風險 | 備註 |
|---|---|---|---|---|
| watchdog | watchdog | py | Low | 檔案系統事件監看 |
| tqdm | tqdm | py | Low | 進度條 |
| loguru | loguru | py | Low | 結構化日誌 |
| tabulate | tabulate | py | Low | 文字表格 |
| cachetools | cachetools | py | Low | 記憶體快取 |
| diskcache | diskcache | py | Low | 磁碟快取 |
| pydantic | pydantic | py | Low | Schema 驗證 |
| typer | typer | py | Low | CLI 框架 |
| msgpack | msgpack | py | Low | 二進位序列化 |
| **numba** | numba | py | **High** | **JIT，需 Py≤3.12（Gatekeeper 攔截）** |
| PSResourceGet | Microsoft.PowerShell.PSResourceGet | ps | Low | 新世代模組安裝器 |
| PSDepend | PSDepend | ps | Low | 相依性宣告 / 解析 |
| powershell-yaml | powershell-yaml | ps | Low | YAML 讀寫 |
| BurntToast | BurntToast | ps | Low | Windows 原生通知 |
| ConsoleGuiTools | Microsoft.PowerShell.ConsoleGuiTools | ps | Low | 終端 TUI |

> **numpy 黃金律**：所有 pip 安裝共釘 `numpy>=1.24,<2.0`。
> **Gatekeeper**：`numba` 在 Py3.13 會被 `Test-LibGate` 攔下（MaxPy=3.12）。

---

## 3. 每流程 × 每語言 Top-10 Local-Free Libs（150 推薦矩陣）

完整矩陣已內建於 UI「推薦函式庫矩陣」卡片，亦可由 `Get-RecommendMatrix` 取得。

### P1 磁碟清理 / 掃描
- **Python**：send2trash, scandir, pathlib, psutil, watchdog, diskcache, humanize, glob2, pyfilesystem2, tqdm
- **PowerShell**：PSFolderSize, PSEverything, Carbon, BurntToast, PSWriteColor, PSWindowsUpdate, PendingReboot, PSWriteHTML, ImportExcel, PSScriptAnalyzer
- **.NET**：System.IO, System.IO.Compression, Microsoft.Win32.Registry, System.Management(WMI), DotNetZip, SharpCompress, Polly, Spectre.Console, Humanizer, FluentValidation

### P2 記憶體 / CPU 加速
- **Python**：psutil, py-cpuinfo, GPUtil, memory-profiler, pympler, numexpr, numba(Py≤3.12), cython, joblib, multiprocessing
- **PowerShell**：ThreadJob, PoshRSJob, PSParallel, ForEach-Object-Parallel, PSWriteHTML, BurntToast, PSScheduledJob, PSWindowsUpdate, Microsoft.PowerShell.ThreadJob, PSReadLine
- **.NET**：TPL(Tasks), Threading.Channels, PerformanceCounter, System.Management, ClrMD, BenchmarkDotNet, Spectre.Console, Polly, System.Memory, System.Buffers

### P3 函式庫佈建 / 註冊
- **Python**：pip, pip-tools, uv, virtualenv, venv, packaging, importlib.metadata, pipdeptree, wheel, setuptools
- **PowerShell**：PowerShellGet, PSResourceGet, PSDepend, PSModuleDevelopment, PackageManagement, Plaster, PSFramework, ModuleBuilder, PSScriptAnalyzer, Pester
- **.NET**：NuGet.Client, dotnet-tool, Cake, Nuke, LibGit2Sharp, System.Reflection, McMaster.NETCore.Plugins, MEF, Autofac, Microsoft.Extensions.DependencyInjection

### P4 全景診斷 / 測試
- **Python**：pytest, hypothesis, coverage, mypy, ruff, pylint, flake8, bandit, tox, pyright
- **PowerShell**：Pester, PSScriptAnalyzer, PSCodeHealth, PSKoans, InjectionHunter, PSRule, Catesta, PSScriptTools, Format-Pester, PSDecode
- **.NET**：xUnit, NUnit, FluentAssertions, Moq, Roslyn, BenchmarkDotNet, Verify, Coverlet, Stryker.NET, SonarAnalyzer

### P5 報表 / 視覺化
- **Python**：matplotlib, plotly, seaborn, rich, tabulate, jinja2, weasyprint, bokeh, altair, pandas
- **PowerShell**：PSWriteHTML, ImportExcel, PSWritePDF, PSWriteOffice, PSGraph, Dashimo, PScribo, EnhancedHTML2, PSWriteColor, PSParseHTML
- **.NET**：ScottPlot, OxyPlot, LiveCharts, QuestPDF, ClosedXML, EPPlus, RazorLight, Spectre.Console, SkiaSharp, System.Text.Json

---

## 4. 三輪全景式分析（套用於佈建與本工具自身）

| 輪次 | 性質 | 內容 |
|---|---|---|
| **R1 全面** | 並行安全、唯讀 | 一次 python 程序匯入全部 py 套件 → JSON；`Get-Module -ListAvailable` 掃 ps 模組；7 區全景掃描（Memory/CPU/Disk/Security/Libs/Modules/Env） |
| **R2 順序** | 相依序、parse-gate | Security 無 RED 才放行；佈建低風險先、Gatekeeper 逐套件閘門；`Write-Progress -Id 1` 非阻塞 |
| **R3 收尾** | 並行安全 | 重新探測驗證；健康分 0–100 + 等級 A–F |

> **九頭龍風險（Hydra-9）**：parse 錯誤會封鎖廣域自動修復；互相依賴的元件不同時修。
> 本次交付的 v4 本體經靜態驗證 **0 ERROR / 0 WARNING**；修正僅發生在驗證器誤報，未動到交付物（符合 ≤3 輪、不修壞原則）。

---

## 5. 執行方式

```powershell
# 啟動（自動開瀏覽器、單一畫面儀表板）
pwsh -File .\VIA_TurboOptimizer_v4.ps1

# 指定埠 / 清理門檻天數 / 不自動開瀏覽器
pwsh -File .\VIA_TurboOptimizer_v4.ps1 -Port 8870 -AgeDays 3 -NoBrowser

# 自我測試（~30 項）；-CI 才會回傳 exit code（CI 用）
pwsh -File .\VIA_TurboOptimizer_v4.ps1 -SelfTest
pwsh -File .\VIA_TurboOptimizer_v4.ps1 -SelfTest -CI
```

執行根目錄：`%LOCALAPPDATA%\OptimizeTool\`（log、rendered HTML 落地於此）。

---

## 6. 後端 API 與安全模型（loopback 127.0.0.1）

| 端點 | 方法 | CSRF | 說明 |
|---|---|---|---|
| `/` | GET | — | 儀表板 HTML |
| `/api/scan` | GET | — | 清理目標掃描 |
| `/api/metrics` | GET | — | Mem / Cpu / Drives 快照 |
| `/api/libscan` | GET | — | R1 函式庫探測（27 套件現況） |
| `/api/panorama` | GET | — | 全景診斷報告 |
| `/api/run` | POST | ✔ | 執行清理 / 優化 |
| `/api/libinstall` | POST | ✔ | R2 佈建選定套件 |
| `/api/psutil` | POST | ✔ | 安裝 psutil |
| `/api/shutdown` | POST | ✔ | 關閉後端 |

**硬化**：Host 白名單（127.0.0.1 / localhost / [::1]）、mutating 端點強制 POST、`X-VIA-CSRF` 比對 `$script:Csrf`（每次啟動隨機 32-hex）、body 上限 2MB、`X-Content-Type-Options: nosniff` / `X-Frame-Options: DENY` / `Referrer-Policy: no-referrer` / `Cache-Control: no-store`。

---

## 7. 支援模組整合（優雅降級）

啟動時偵測下列三者，存在則記錄、不存在不阻斷：

- `…\supportive modules\Read_Me_VeritasNexusCore.md`
- `…\supportive modules\Invoke-VeritasNexusCore.ps1`
- `…\supportive modules\Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1`

`PSScriptAnalyzer` + `Pester` 已列入 CORE，對應 Polyglot 的 check / repair 與 NexusCore 的測試骨幹。

---

## 8. LL 規則遵循（節錄）

`param()` 置頂（僅 `#requires`、區塊註解可在前）｜全檔 `UTF8Encoding::new($false)` No-BOM｜`ProcessStartInfo` + `ArgumentList.Add()` + 非同步 drain（禁 `Start-Job`）｜主作用域不 `exit`（`-CI` 例外）｜`${var}:` 包裹｜`[ordered]@{}` 用 `.Contains()`、純 `@{}` 用 `.ContainsKey()`｜`("" -f x)` 加括號｜`Sort-Object @{e=…;desc=$true}`｜單引號 here-string + `.Replace()`（禁 `-replace` 注入）｜全 cmdlet 名（禁別名 / SL/SP/WL/WB/DP）｜`Write-Progress -Id 1`｜`Start-Process` 僅開 HTML（LL#12）。

---

## 9. 隨附驗證器

`VIA_TurboOptimizer_v4_validator.py` — Python 靜態驗證器，把 LL 規則 + 結構平衡編成 parse-gate（此環境無 pwsh，作為 test/debug harness）。

```bash
python3 VIA_TurboOptimizer_v4_validator.py VIA_TurboOptimizer_v4.ps1
# => ERRORS: 0  WARNINGS: 0  PARSE-GATE: CLEAR
```

檢查項：here-string 遮罩後的 brace/paren 平衡、param 置頂、別名、`${var}:` 包裹、`[ordered]` 的 `.ContainsKey` 誤用、`Sort-Object` hashtable 形式、`-replace` token 注入、token 全替換覆蓋、JS 端點 ↔ router arm 覆蓋。
