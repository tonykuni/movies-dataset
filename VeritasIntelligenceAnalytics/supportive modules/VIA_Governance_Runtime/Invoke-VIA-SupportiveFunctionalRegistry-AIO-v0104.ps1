#requires -Version 7.0
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
<#
.SYNOPSIS
  VIA Supportive / Functional Module Registry + Safe Placement + HTML UI
.DESCRIPTION
  Scans C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics, classifies supportive / functional / parameter assets,
  creates append-only SSOT registries, safely copies not-yet-placed files to canonical folders, and opens an HTML UI report.
  No delete. No source overwrite. Existing source files are preserved.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# =============================================================================
# def PARAMETERS
# =============================================================================
$def_PARAM_BASE_DIR = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
$def_PARAM_RUN_PREFIX = "VIA_SUPPORTIVE_FUNCTIONAL_REGISTRY_v0104_NOFATAL_TURBO"
$def_PARAM_TIMEZONE = "Asia/Taipei"
$def_PARAM_ACTION_MODE = "COPY_TO_CANONICAL_AND_REGISTER"  # REGISTER_ONLY | COPY_TO_CANONICAL_AND_REGISTER
$def_PARAM_OPEN_HTML_UI = $true
$def_PARAM_KEEP_POWERSHELL_OPEN = $true
$def_PARAM_ENABLE_BACKUP_BEFORE_COPY = $true
$def_PARAM_SCAN_DIRECT_ONLY_FOR_ROOT_RELOCATION = $false
$def_PARAM_MAX_CONTENT_READ_BYTES = 262144
$def_PARAM_JSON_DEPTH = 18
$def_PARAM_HTML_TABLE_LIMIT = 2000
$def_PARAM_ENABLE_15_PS_ACCELERATORS = $true
$def_PARAM_ENABLE_DYNAMIC_PROGRESS = $true
$def_PARAM_ENABLE_NO_STALL_ERROR_LEDGER = $true
$def_PARAM_PROGRESS_EVERY_N_FILES = 25
$def_PARAM_HASH_BYTES_BUFFER_SIZE = 1048576
$def_PARAM_ENABLE_FAST_EXTENSION_HASHSET = $true
$def_PARAM_ENABLE_HISTORY_RECORD_REUSE = $true
$def_PARAM_HISTORY_MAX_FILES = 5000
$def_PARAM_HISTORY_MAX_READ_BYTES = 131072
$def_PARAM_HISTORY_PROGRESS_EVERY_N_FILES = 50
$def_PARAM_HISTORY_SCAN_PATTERNS = @(
  "*Registry*.json", "*SSOT*.json", "*Matrix*.json", "*Gate*.json", "*Report*.json",
  "*Index*.json", "*Health*.json", "*Summary*.json", "*Seal*.json", "*Ledger*.json",
  "*Registry*.html", "*SSOT*.html", "*Matrix*.html", "*Gate*.html", "*Report*.html", "*Index*.html",
  "*.log", "*.md", "*.txt"
)


$def_PARAM_CANONICAL_SUPPORTIVE_DIR = Join-Path $def_PARAM_BASE_DIR "supportive modules"
$def_PARAM_CANONICAL_FUNCTIONAL_DIR = Join-Path $def_PARAM_BASE_DIR "functional modules"
$def_PARAM_CANONICAL_REGISTRY_DIR = Join-Path $def_PARAM_BASE_DIR "_via_registry"
$def_PARAM_CANONICAL_OUTPUT_DIR = Join-Path $def_PARAM_CANONICAL_REGISTRY_DIR "supportive_functional_registry"
$def_PARAM_CANONICAL_BACKUP_DIR = Join-Path $def_PARAM_CANONICAL_REGISTRY_DIR "_source_backups"

$def_PARAM_SCAN_EXTENSIONS = @(".py", ".ps1", ".psm1", ".json", ".html", ".htm", ".md", ".txt", ".csv")
$def_PARAM_EXCLUDE_DIR_NAMES = @(
  ".git",
  "__pycache__",
  "node_modules",
  ".venv",
  "venv",
  "_envs",
  "_backup",
  "_bak",
  "_via_registry"
)
$def_PARAM_EXPECTED_CORE_SUPPORTIVE = @(
  "VIA_EnvManager.py",
  "VIA_RegistryCore_v1.py",
  "VIA_SSOT_Unified.py",
  "VeritasAegisNexus.py",
  "VeritasCeleritas.py",
  "VIA_Runtime_Bridge_All_in_One.py",
  "VIA_Panorama_AST_RuntimeInjector.py"
)

$def_PARAM_SUPPORTIVE_RULES = @(
  @{ Role="ENV_MANAGER";      Folder="environment";    Manager="VIA_EnvManager.py";                 Pattern="(?i)(envmanager|envrouter|envdispatch|environment|venv|pip|uv|alias|route|rebuild)"; Responsibility="環境、套件、路由、安裝決策、衝突治理" },
  @{ Role="REGISTRY_CORE";    Folder="registry";       Manager="VIA_RegistryCore_v1.py";            Pattern="(?i)(registrycore|registry|manifest|module.?record|iaic|5d|asset.?id|append.?only)"; Responsibility="模組註冊、資產身份、版本、風險、依賴、入口治理" },
  @{ Role="SSOT_UNIFIED";     Folder="ssot";           Manager="VIA_SSOT_Unified.py";               Pattern="(?i)(ssot|unified|canonical|synonym|alias|regex|rule|schema|parameter|config|settings)"; Responsibility="單一真實來源、代碼/文字正規化、參數與規則語料" },
  @{ Role="NETWORK_AEGIS";    Folder="network";        Manager="VeritasAegisNexus.py";              Pattern="(?i)(aegis|nexus|fetch|http|request|cloudflare|anti.?bot|twse|tpex|mops|yfinance|finmind|akshare|scrape|crawler|proxy|cache)"; Responsibility="網路擷取、反阻擋、故障轉移、台股資料源、快取" },
  @{ Role="ACCELERATOR";      Folder="accelerator";    Manager="VeritasCeleritas.py";               Pattern="(?i)(celeritas|accel|accelerator|parallel|thread|process|xmap|xbatch|xfetch|cache|compress|duckdb|polars|orjson|memory|gc)"; Responsibility="加速器、批次、平行、記憶體、壓縮、JSON/DataFrame 高速化" },
  @{ Role="RUNTIME_BRIDGE";   Folder="runtime_bridge"; Manager="VIA_Runtime_Bridge_All_in_One.py";   Pattern="(?i)(runtime.?bridge|bridge|bootstrap|ctx|context|mount|load.?core)"; Responsibility="核心模組掛載、共享 ctx、統一執行入口" },
  @{ Role="AST_AUDIT";        Folder="audit_tools";    Manager="VIA_Panorama_AST_RuntimeInjector.py";Pattern="(?i)(ast|injector|audit|panorama|matrix|gate|validator|validation|selftest|syntax|compile|patchplan|repair|health|hydra)"; Responsibility="AST 掃描、語法驗證、治理矩陣、修復計畫、健康檢查" },
  @{ Role="UI_SUPPORT";       Folder="ui_support";     Manager="VPN_v35_Dashboard.html";            Pattern="(?i)(dashboard|console|html|ui|u_i|pwa|manifest|sw\.js|css|layout|theme|visual|chart|matrix)"; Responsibility="HTML U/I、儀表板、報表、視覺矩陣、前端支援" }
)

$def_PARAM_FUNCTIONAL_RULES = @(
  @{ Role="VDF";       Folder="VDF";       Manager="Invoke-VDF.ps1";              Pattern="(?i)(\bVDF\b|DataForge|TWSE|TPEX|MOPS|Fetch|Ticker|base.?info|financial.?data|fundamental)"; Responsibility="台股交易所/櫃買/MOPS/基礎與財報資料擷取" },
  @{ Role="VRN";       Folder="VRN";       Manager="Invoke-VRN.ps1";              Pattern="(?i)(\bVRN\b|ReportNova|PDF|OCR|table|pdfplumber|camelot|tabula|pymupdf|layout|document|report)"; Responsibility="PDF 報告文字/表格/OCR/版面解析" },
  @{ Role="VAP";       Folder="VAP";       Manager="Invoke-VAP.ps1";              Pattern="(?i)(\bVAP\b|Panorama|Analysis|macro|industry|equity|insight|scenario|geopolitical)"; Responsibility="宏觀/產業/個股/情境分析與觀測" },
  @{ Role="VETF";      Folder="VETF";      Manager="VIA_ActiveETF_System.py";     Pattern="(?i)(Active.?ETF|\bETF\b|VETF|etf_universe|fund|benchmark|tracking)"; Responsibility="主動式 ETF / ETF 宇宙 / 基準與追蹤分析" },
  @{ Role="VIAS";      Folder="VIAS";      Manager="Invoke-VIAS.ps1";             Pattern="(?i)(\bVIAS\b|asset.?system|asset.?class|commodity|shipping|fx|rate|bond|index)"; Responsibility="資產類別、商品、航運、匯率、利率、指數資料系統" },
  @{ Role="VPNS";      Folder="VPNS";      Manager="Invoke-VPNS.ps1";             Pattern="(?i)(\bVPNS\b|PanoramaNexus|Nexus|Command.?Center|Smart.?Asset|VPN_)"; Responsibility="Panorama Nexus / 多模組指揮中心" },
  @{ Role="TRADING";   Folder="Trading";   Manager="VIA_IntraDay_Trading.py";     Pattern="(?i)(intraday|day.?trade|trading|strategy|signal|alpha|beta|factor|backtest|ta.?lib|technical|risk|sharpe|sortino|drawdown)"; Responsibility="當沖/量化交易/因子/風險/回測策略" },
  @{ Role="RESEARCH";  Folder="Research";  Manager="VIA_ResearchEngine.py";       Pattern="(?i)(research|lesson|knowledge|KM|methodology|evidence|adversarial|logic|prompt|engine)"; Responsibility="研究方法論、知識庫、證據、演化與反證流程" }
)

$def_PARAM_PARAMETER_RULES = @(
  @{ Role="PARAMETERS"; Folder="parameters"; Pattern="(?i)(parameter|params|config|setting|settings|schema|sample|full|registry|ssot|manifest|route|alias|rule|dictionary|dict)"; Responsibility="JSON/CSV/MD 參數、Schema、樣本、註冊與路由設定" }
)


# =============================================================================
# def 15 PS ACCELERATORS
# =============================================================================
$def_PARAM_PS_ACCELERATORS = @(
  @{ Id="A01"; Name="LiteralPath everywhere"; Status="ON"; Purpose="避免 wildcard path 展開造成慢速與誤判" },
  @{ Id="A02"; Name="Path-segment exclusion"; Status="ON"; Purpose="用資料夾段落排除 _envs / _via_registry，不用危險 regex" },
  @{ Id="A03"; Name="Extension HashSet"; Status="ON"; Purpose="副檔名 O(1) 快速判斷" },
  @{ Id="A04"; Name="Read head cap"; Status="ON"; Purpose="只讀每檔前段內容，避免大檔卡住" },
  @{ Id="A05"; Name="Per-file try/catch"; Status="ON"; Purpose="單檔失敗不炸主流程" },
  @{ Id="A06"; Name="Safe rule getter"; Status="ON"; Purpose="Hashtable / PSCustomObject 混用也不會缺屬性中斷" },
  @{ Id="A07"; Name="Safe regex match"; Status="ON"; Purpose="任何規則 regex 錯誤進 ledger，不中斷" },
  @{ Id="A08"; Name="JSON parse only JSON"; Status="ON"; Purpose="只對 .json 做 ConvertFrom-Json" },
  @{ Id="A09"; Name="Hash safe wrapper"; Status="ON"; Purpose="Get-FileHash 失敗收斂為 WARN" },
  @{ Id="A10"; Name="Dynamic Write-Progress"; Status="ON"; Purpose="Scan / Classify / Placement / HTML 分段進度" },
  @{ Id="A11"; Name="StringBuilder HTML"; Status="ON"; Purpose="大型表格輸出不做大量字串相加" },
  @{ Id="A12"; Name="Append-only output"; Status="ON"; Purpose="每次 run 獨立資料夾，latest 只做指標檔" },
  @{ Id="A13"; Name="No destructive placement"; Status="ON"; Purpose="只 copy，不 delete、不移走來源" },
  @{ Id="A14"; Name="Duplicate hash guard"; Status="ON"; Purpose="同 hash 已存在則不重複 copy" },
  @{ Id="A15"; Name="No-stall error ledger"; Status="ON"; Purpose="錯誤寫入 JSON/HTML，流程繼續完成" }
)
$def_PARAM_HISTORY_ACCELERATORS = @(
  @{ Id="H01"; Name="Historical registry discovery"; Status="ON"; Purpose="先讀取過去 registry / SSOT / gate / index / report，不重做已完成判斷" },
  @{ Id="H02"; Name="Pattern-limited history scan"; Status="ON"; Purpose="只掃描高價值歷史檔名，避免整顆專案重跑卡住" },
  @{ Id="H03"; Name="History read head cap"; Status="ON"; Purpose="歷史檔只讀前 128KB，保留速度" },
  @{ Id="H04"; Name="Evidence tag extraction"; Status="ON"; Purpose="抽取 NexusCore / EnvManager / Registry / SSOT / HardGate 等證據標籤" },
  @{ Id="H05"; Name="Reusable flow mapping"; Status="ON"; Purpose="把過去流程映射成可重用的現況讀取策略" },
  @{ Id="H06"; Name="No duplicate history paths"; Status="ON"; Purpose="HashSet 去重歷史檔路徑" },
  @{ Id="H07"; Name="Latest-first ordering"; Status="ON"; Purpose="優先使用最新 run / latest / summary" },
  @{ Id="H08"; Name="Safe JSON history probe"; Status="ON"; Purpose="JSON 歷史檔解析錯誤不 fatal，改列入 ledger" },
  @{ Id="H09"; Name="HTML/Log text evidence"; Status="ON"; Purpose="可從 HTML 報表與 log 讀取歷史狀態" },
  @{ Id="H10"; Name="Legacy NexusCore bridge hints"; Status="ON"; Purpose="辨識 supportive modules 既有 NexusCore 分層" },
  @{ Id="H11"; Name="No canonical mutation from history"; Status="ON"; Purpose="歷史吸收只讀不寫 canonical，避免誤改舊成果" },
  @{ Id="H12"; Name="History confidence score"; Status="ON"; Purpose="依 evidence tag 數量與 latest 檔名計分" },
  @{ Id="H13"; Name="Run ledger preservation"; Status="ON"; Purpose="每次 run 獨立保留歷史吸收矩陣" },
  @{ Id="H14"; Name="Current-state assisted classification"; Status="ON"; Purpose="用歷史 evidence 輔助判斷支援/功能/參數整合現況" },
  @{ Id="H15"; Name="No-stall history errors"; Status="ON"; Purpose="歷史檔讀取失敗只進 Error Ledger，主流程繼續" }
)
$def_PARAM_PS_ACCELERATORS = @($def_PARAM_PS_ACCELERATORS + $def_PARAM_HISTORY_ACCELERATORS)

$def_PARAM_TURBO_NOFATAL_ACCELERATORS = @(
  @{ Id="T01"; Name="Object ArrayList rows"; Status="ON"; Purpose="分類/歸位矩陣使用 ArrayList，避免 += 大量複製拖慢" },
  @{ Id="T02"; Name="Type-neutral history queue"; Status="ON"; Purpose="歷史候選檔不使用強型別 FileInfo List，避免 Argument types do not match" },
  @{ Id="T03"; Name="Stage guard wrapper"; Status="ON"; Purpose="每一階段 try/catch，階段錯誤進 ledger 並繼續" },
  @{ Id="T04"; Name="History direct file enumeration"; Status="ON"; Purpose="Get-ChildItem 回傳物件逐一正規化，避免混型集合炸裂" },
  @{ Id="T05"; Name="Safe file object normalization"; Status="ON"; Purpose="任何檔案物件轉成標準 Path/Name/Extension/Length/LastWriteTime" },
  @{ Id="T06"; Name="Progress throttle"; Status="ON"; Purpose="進度條節流，避免 Write-Progress 本身成為瓶頸" },
  @{ Id="T07"; Name="Root-local pattern guard"; Status="ON"; Purpose="每個 root/pattern 獨立錯誤收斂" },
  @{ Id="T08"; Name="Fallback emergency HTML"; Status="ON"; Purpose="即使後段出錯也產出可開啟 HTML 診斷報告" },
  @{ Id="T09"; Name="JSON output guard"; Status="ON"; Purpose="每個 JSON 輸出獨立保護，壞資料不阻斷其他輸出" },
  @{ Id="T10"; Name="String-safe HTML row getter"; Status="ON"; Purpose="HTML 表格欄位缺失時輸出空字串，不再 strict fatal" },
  @{ Id="T11"; Name="Directory creation idempotent"; Status="ON"; Purpose="所有輸出資料夾可重複建立且不覆蓋來源" },
  @{ Id="T12"; Name="Latest pointer safe copy"; Status="ON"; Purpose="latest HTML 複製失敗不影響 run 產物" },
  @{ Id="T13"; Name="Hash optional fast path"; Status="ON"; Purpose="Hash 失敗或大檔問題直接降級 WARN" },
  @{ Id="T14"; Name="Run-local finalizer"; Status="ON"; Purpose="finally 階段補寫錯誤 ledger 與 emergency note" },
  @{ Id="T15"; Name="PowerShell no-close policy"; Status="ON"; Purpose="錯誤後仍保持 PowerShell 開啟並列出輸出路徑" }
)
$def_PARAM_PS_ACCELERATORS = @($def_PARAM_PS_ACCELERATORS + $def_PARAM_TURBO_NOFATAL_ACCELERATORS)

$script:def_ERROR_LEDGER = New-Object System.Collections.Generic.List[object]
$script:def_PROGRESS_STARTED_AT = Get-Date

# =============================================================================
# def LOW LEVEL HELPERS
# =============================================================================
function def_GetNowTaipeiString {
  try {
    $tz = [System.TimeZoneInfo]::FindSystemTimeZoneById("Taipei Standard Time")
    return [System.TimeZoneInfo]::ConvertTime([DateTime]::UtcNow, $tz).ToString("yyyy-MM-dd HH:mm:ss")
  } catch {
    return (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  }
}

function def_GetRunId {
  return "RUN_{0}_{1}" -f (Get-Date -Format "yyyyMMdd_HHmmss"), $def_PARAM_RUN_PREFIX
}

function def_EnsureDirectory {
  param([Parameter(Mandatory=$true)][string]$PathValue)
  if (-not (Test-Path -LiteralPath $PathValue)) {
    New-Item -ItemType Directory -Path $PathValue -Force | Out-Null
  }
}

function def_WriteJson {
  param(
    [Parameter(Mandatory=$true)][string]$PathValue,
    [Parameter(Mandatory=$true)]$Payload
  )
  def_EnsureDirectory -PathValue ([System.IO.Path]::GetDirectoryName($PathValue))
  $json = $Payload | ConvertTo-Json -Depth $def_PARAM_JSON_DEPTH
  [System.IO.File]::WriteAllText($PathValue, $json, [System.Text.UTF8Encoding]::new($false))
}

function def_WriteTextUtf8 {
  param(
    [Parameter(Mandatory=$true)][string]$PathValue,
    [Parameter(Mandatory=$true)][string]$TextValue
  )
  def_EnsureDirectory -PathValue ([System.IO.Path]::GetDirectoryName($PathValue))
  [System.IO.File]::WriteAllText($PathValue, $TextValue, [System.Text.UTF8Encoding]::new($false))
}

function def_GetRelativePathSafe {
  param(
    [Parameter(Mandatory=$true)][string]$BasePath,
    [Parameter(Mandatory=$true)][string]$FullPath
  )
  try {
    return [System.IO.Path]::GetRelativePath($BasePath, $FullPath)
  } catch {
    return $FullPath
  }
}

function def_TestExcludedPath {
  param([Parameter(Mandatory=$true)][string]$FullPath)

  # v0102 hotfix:
  # Do not use raw regex patterns for folder names like "_envs".
  # PowerShell/.NET regex treats \_ as an invalid escape sequence.
  # Use path-segment exact matching instead, so _envs / _backup / _via_registry
  # are safely excluded without regex parsing.
  $normalized = $FullPath.Replace('/', '\')
  $segments = @($normalized -split '\\+') | Where-Object { $_ -ne "" }

  foreach ($segment in $segments) {
    foreach ($excludeName in $def_PARAM_EXCLUDE_DIR_NAMES) {
      if ($segment.Equals($excludeName, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $true
      }
    }
  }
  return $false
}

function def_GetFileHashSafe {
  param([Parameter(Mandatory=$true)][string]$PathValue)
  try {
    return (Get-FileHash -LiteralPath $PathValue -Algorithm SHA256).Hash
  } catch {
    return "HASH_FAILED: $($_.Exception.Message)"
  }
}

function def_ReadFileHeadSafe {
  param([Parameter(Mandatory=$true)][string]$PathValue)
  try {
    $bytes = [System.IO.File]::ReadAllBytes($PathValue)
    $count = [Math]::Min($bytes.Length, $def_PARAM_MAX_CONTENT_READ_BYTES)
    return [System.Text.Encoding]::UTF8.GetString($bytes, 0, $count)
  } catch {
    return ""
  }
}

function def_TestJsonValid {
  param([Parameter(Mandatory=$true)][string]$PathValue)
  try {
    if ([System.IO.Path]::GetExtension($PathValue).ToLowerInvariant() -ne ".json") {
      return @{ IsJson=$false; Valid=$null; Error="" }
    }
    $raw = Get-Content -LiteralPath $PathValue -Raw -Encoding UTF8
    $null = $raw | ConvertFrom-Json -Depth $def_PARAM_JSON_DEPTH
    return @{ IsJson=$true; Valid=$true; Error="" }
  } catch {
    return @{ IsJson=$true; Valid=$false; Error=$_.Exception.Message }
  }
}

function def_GetRyG {
  param([Parameter(Mandatory=$true)][string]$StatusValue)
  switch -Regex ($StatusValue) {
    "(?i)PASS|OK|REGISTERED|PLACED|COPY|INTEGRATED" { return "GREEN" }
    "(?i)WARN|UNKNOWN|INBOX|REVIEW|DUP" { return "YELLOW" }
    "(?i)FAIL|ERROR|MISSING|BROKEN" { return "RED" }
    default { return "YELLOW" }
  }
}


function def_AddErrorLedger {
  param(
    [string]$Phase="UNKNOWN",
    [string]$FileName="",
    [string]$PathValue="",
    [string]$Message="",
    [string]$Detail=""
  )
  try {
    $script:def_ERROR_LEDGER.Add([pscustomobject]@{
      TimeTaipei = def_GetNowTaipeiString
      Phase = $Phase
      FileName = $FileName
      Path = $PathValue
      Message = $Message
      Detail = $Detail
    }) | Out-Null
  } catch { }
}

function def_GetRuleValue {
  param(
    [Parameter(Mandatory=$true)]$Rule,
    [Parameter(Mandatory=$true)][string]$Name,
    $DefaultValue = ""
  )
  try {
    if ($null -eq $Rule) { return $DefaultValue }
    if ($Rule -is [System.Collections.IDictionary]) {
      if ($Rule.Contains($Name)) { return $Rule[$Name] }
      return $DefaultValue
    }
    $prop = $Rule.PSObject.Properties[$Name]
    if ($null -ne $prop) { return $prop.Value }
    return $DefaultValue
  } catch {
    def_AddErrorLedger -Phase "RULE_GETTER" -Message $_.Exception.Message -Detail $Name
    return $DefaultValue
  }
}

function def_TestRegexMatchSafe {
  param(
    [AllowNull()][string]$TextValue,
    [AllowNull()][string]$PatternValue,
    [string]$Phase="REGEX_MATCH"
  )
  try {
    if ([string]::IsNullOrWhiteSpace($PatternValue)) { return $false }
    if ($null -eq $TextValue) { $TextValue = "" }
    return [regex]::IsMatch($TextValue, $PatternValue)
  } catch {
    def_AddErrorLedger -Phase $Phase -Message $_.Exception.Message -Detail $PatternValue
    return $false
  }
}

function def_ShowProgressSafe {
  param(
    [Parameter(Mandatory=$true)][string]$Activity,
    [string]$Status="",
    [int]$Current=0,
    [int]$Total=1,
    [int]$PhaseBase=0,
    [int]$PhaseSpan=100
  )
  if (-not $def_PARAM_ENABLE_DYNAMIC_PROGRESS) { return }
  try {
    $safeTotal = [Math]::Max(1, $Total)
    $innerPct = [Math]::Min(100, [Math]::Max(0, ($Current / $safeTotal) * 100))
    $overall = [Math]::Min(100, [Math]::Max(0, $PhaseBase + ($innerPct * $PhaseSpan / 100)))
    $elapsed = [int]((Get-Date) - $script:def_PROGRESS_STARTED_AT).TotalSeconds
    Write-Progress -Activity $Activity -Status ("{0} · {1}/{2} · {3}s" -f $Status, $Current, $Total, $elapsed) -PercentComplete $overall
  } catch { }
}

function def_NewFailureRow {
  param(
    [Parameter(Mandatory=$true)][System.IO.FileInfo]$FileObj,
    [Parameter(Mandatory=$true)][string]$Message
  )
  $relative = def_GetRelativePathSafe -BasePath $def_PARAM_BASE_DIR -FullPath $FileObj.FullName
  def_AddErrorLedger -Phase "CLASSIFY_FILE" -FileName $FileObj.Name -PathValue $FileObj.FullName -Message $Message
  return [pscustomobject]@{
    FileName = $FileObj.Name
    Extension = $FileObj.Extension.ToLowerInvariant()
    RelativePath = $relative
    FullPath = $FileObj.FullName
    CurrentBucket = "ERROR"
    Domain = "UNKNOWN"
    Role = "UNASSIGNED"
    ManagerFile = "MANUAL_REVIEW"
    Responsibility = "單檔分類失敗，已收斂進 Error Ledger，主流程不中斷"
    Confidence = 0
    TargetDir = Join-Path $def_PARAM_CANONICAL_SUPPORTIVE_DIR "_inbox_to_classify"
    TargetPath = Join-Path (Join-Path $def_PARAM_CANONICAL_SUPPORTIVE_DIR "_inbox_to_classify") $FileObj.Name
    Status = "YELLOW_CLASSIFY_ERROR_REVIEW"
    RYG = "YELLOW"
    Action = "COPY_TO_INBOX_AND_REGISTER"
    NeedsPlacement = $true
    Risk = "MEDIUM"
    Sha256 = "HASH_SKIPPED_DUE_CLASSIFY_ERROR"
    SizeBytes = $FileObj.Length
    LastWriteTime = $FileObj.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
    IsJson = ($FileObj.Extension.ToLowerInvariant() -eq ".json")
    JsonValid = $null
    JsonError = $Message
    ParameterIntegrated = $false
  }
}

function def_FindFirstExistingDir {
  param([Parameter(Mandatory=$true)][string[]]$Candidates)
  foreach ($candidate in $Candidates) {
    if (Test-Path -LiteralPath $candidate) { return $candidate }
  }
  return $null
}

# =============================================================================
# def CLASSIFICATION
# =============================================================================
function def_MatchRuleScore {
  param(
    [Parameter(Mandatory=$true)]$Rule,
    [Parameter(Mandatory=$true)][string]$SearchText,
    [Parameter(Mandatory=$true)][string]$FileName
  )
  $score = 0
  $pattern = [string](def_GetRuleValue -Rule $Rule -Name "Pattern" -DefaultValue "")
  $manager = [string](def_GetRuleValue -Rule $Rule -Name "Manager" -DefaultValue "")
  if (def_TestRegexMatchSafe -TextValue $FileName -PatternValue $pattern -Phase "RULE_MATCH_FILENAME") { $score += 5 }
  if (def_TestRegexMatchSafe -TextValue $SearchText -PatternValue $pattern -Phase "RULE_MATCH_CONTENT") { $score += 2 }
  if (-not [string]::IsNullOrWhiteSpace($manager) -and $FileName.Equals($manager, [System.StringComparison]::OrdinalIgnoreCase)) { $score += 10 }
  return $score
}

function def_ClassifyFile {
  param([Parameter(Mandatory=$true)][System.IO.FileInfo]$FileObj)

  try {
    $fileName = $FileObj.Name
    $ext = $FileObj.Extension.ToLowerInvariant()
    $head = def_ReadFileHeadSafe -PathValue $FileObj.FullName
    $searchText = ($fileName + "`n" + $FileObj.FullName + "`n" + $head)
    $relative = def_GetRelativePathSafe -BasePath $def_PARAM_BASE_DIR -FullPath $FileObj.FullName

    $bestSupportive = $null; $bestSupportiveScore = 0
    foreach ($rule in $def_PARAM_SUPPORTIVE_RULES) {
      $score = def_MatchRuleScore -Rule $rule -SearchText $searchText -FileName $fileName
      if ($score -gt $bestSupportiveScore) { $bestSupportiveScore = $score; $bestSupportive = $rule }
    }

    $bestFunctional = $null; $bestFunctionalScore = 0
    foreach ($rule in $def_PARAM_FUNCTIONAL_RULES) {
      $score = def_MatchRuleScore -Rule $rule -SearchText $searchText -FileName $fileName
      if ($score -gt $bestFunctionalScore) { $bestFunctionalScore = $score; $bestFunctional = $rule }
    }

    $bestParameter = $null; $bestParameterScore = 0
    foreach ($rule in $def_PARAM_PARAMETER_RULES) {
      $score = def_MatchRuleScore -Rule $rule -SearchText $searchText -FileName $fileName
      if ($score -gt $bestParameterScore) { $bestParameterScore = $score; $bestParameter = $rule }
    }

    $domain = "UNKNOWN"
    $role = "UNASSIGNED"
    $folder = "_inbox_to_classify"
    $manager = "MANUAL_REVIEW"
    $responsibility = "低信心，需人工確認後再進 SSOT"
    $confidence = 0

    if ($bestParameterScore -ge 6 -and $ext -in @(".json", ".csv", ".md", ".txt")) {
      $domain = "PARAMETER"
      $role = [string](def_GetRuleValue -Rule $bestParameter -Name "Role" -DefaultValue "PARAMETERS")
      $folder = [string](def_GetRuleValue -Rule $bestParameter -Name "Folder" -DefaultValue "parameters")
      $manager = "VIA_SSOT_Unified.py / VIA_RegistryCore_v1.py"
      $responsibility = [string](def_GetRuleValue -Rule $bestParameter -Name "Responsibility" -DefaultValue "參數、Schema、樣本、註冊與路由設定")
      $confidence = $bestParameterScore
    }

    if ($bestSupportiveScore -ge $bestFunctionalScore -and $bestSupportiveScore -ge 4) {
      $domain = "SUPPORTIVE"
      $role = [string](def_GetRuleValue -Rule $bestSupportive -Name "Role" -DefaultValue "SUPPORTIVE_UNKNOWN")
      $folder = [string](def_GetRuleValue -Rule $bestSupportive -Name "Folder" -DefaultValue "_inbox_to_classify")
      $manager = [string](def_GetRuleValue -Rule $bestSupportive -Name "Manager" -DefaultValue "MANUAL_REVIEW")
      $responsibility = [string](def_GetRuleValue -Rule $bestSupportive -Name "Responsibility" -DefaultValue "支援性模組")
      $confidence = $bestSupportiveScore
    } elseif ($bestFunctionalScore -gt $bestSupportiveScore -and $bestFunctionalScore -ge 4) {
      $domain = "FUNCTIONAL"
      $role = [string](def_GetRuleValue -Rule $bestFunctional -Name "Role" -DefaultValue "FUNCTIONAL_UNKNOWN")
      $folder = [string](def_GetRuleValue -Rule $bestFunctional -Name "Folder" -DefaultValue "_inbox_to_classify")
      $manager = [string](def_GetRuleValue -Rule $bestFunctional -Name "Manager" -DefaultValue "MANUAL_REVIEW")
      $responsibility = [string](def_GetRuleValue -Rule $bestFunctional -Name "Responsibility" -DefaultValue "功能性模組")
      $confidence = $bestFunctionalScore
    }

    if ($domain -eq "UNKNOWN" -and $ext -in @(".html", ".htm")) {
      $domain = "SUPPORTIVE"; $role = "UI_SUPPORT"; $folder = "ui_support"; $manager = "VPN_v35_Dashboard.html"; $responsibility = "HTML U/I、儀表板、報表、視覺矩陣"; $confidence = 3
    }

    $baseTarget = switch ($domain) {
      "SUPPORTIVE" { $def_PARAM_CANONICAL_SUPPORTIVE_DIR }
      "FUNCTIONAL" { $def_PARAM_CANONICAL_FUNCTIONAL_DIR }
      "PARAMETER" { Join-Path $def_PARAM_CANONICAL_SUPPORTIVE_DIR "parameters" }
      default { Join-Path $def_PARAM_CANONICAL_SUPPORTIVE_DIR "_inbox_to_classify" }
    }

    $targetDir = if ($domain -eq "PARAMETER") { $baseTarget } else { Join-Path $baseTarget $folder }
    $targetPath = Join-Path $targetDir $fileName
    $jsonStatus = def_TestJsonValid -PathValue $FileObj.FullName
    $hashValue = def_GetFileHashSafe -PathValue $FileObj.FullName

    $currentBucket = "OTHER"
    if ($FileObj.FullName.StartsWith($def_PARAM_CANONICAL_SUPPORTIVE_DIR, [System.StringComparison]::OrdinalIgnoreCase)) { $currentBucket = "CANONICAL_SUPPORTIVE" }
    elseif ($FileObj.FullName.StartsWith($def_PARAM_CANONICAL_FUNCTIONAL_DIR, [System.StringComparison]::OrdinalIgnoreCase)) { $currentBucket = "CANONICAL_FUNCTIONAL" }
    elseif ($FileObj.FullName.StartsWith($def_PARAM_CANONICAL_REGISTRY_DIR, [System.StringComparison]::OrdinalIgnoreCase)) { $currentBucket = "REGISTRY_OUTPUT" }
    elseif ($relative -notmatch "[\\/]") { $currentBucket = "BASE_ROOT" }

    $status = "REGISTERED"
    $action = "REGISTER_ONLY"
    $needsPlacement = $false

    if ($domain -eq "UNKNOWN") {
      $status = "YELLOW_INBOX_REVIEW"
      $needsPlacement = $true
      $action = "COPY_TO_INBOX_AND_REGISTER"
    } elseif ($currentBucket -eq "REGISTRY_OUTPUT") {
      $status = "SKIP_REGISTRY_OUTPUT"
      $action = "SKIP"
    } elseif (-not $FileObj.FullName.StartsWith($targetDir, [System.StringComparison]::OrdinalIgnoreCase)) {
      $status = "NEEDS_CANONICAL_COPY"
      $needsPlacement = $true
      $action = $def_PARAM_ACTION_MODE
    } else {
      $status = "REGISTERED_IN_PLACE"
      $action = "REGISTER_ONLY"
    }

    if ($jsonStatus.IsJson -and $jsonStatus.Valid -eq $false) {
      $status = "RED_JSON_PARSE_ERROR"
    }

    $risk = "LOW"
    if ($domain -eq "UNKNOWN" -or $status -match "REVIEW|PARSE") { $risk = "MEDIUM" }
    if (def_TestRegexMatchSafe -TextValue $fileName -PatternValue "(?i)(delete|remove|format|shutdown|stop-process|kill|credential|secret|token|key)" -Phase "RISK_FILENAME") { $risk = "HIGH" }

    return [pscustomobject]@{
      FileName = $fileName
      Extension = $ext
      RelativePath = $relative
      FullPath = $FileObj.FullName
      CurrentBucket = $currentBucket
      Domain = $domain
      Role = $role
      ManagerFile = $manager
      Responsibility = $responsibility
      Confidence = $confidence
      TargetDir = $targetDir
      TargetPath = $targetPath
      Status = $status
      RYG = def_GetRyG -StatusValue $status
      Action = $action
      NeedsPlacement = $needsPlacement
      Risk = $risk
      Sha256 = $hashValue
      SizeBytes = $FileObj.Length
      LastWriteTime = $FileObj.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
      IsJson = $jsonStatus.IsJson
      JsonValid = $jsonStatus.Valid
      JsonError = $jsonStatus.Error
      ParameterIntegrated = ($domain -eq "PARAMETER" -and ($jsonStatus.Valid -eq $true -or -not $jsonStatus.IsJson))
    }
  } catch {
    return def_NewFailureRow -FileObj $FileObj -Message $_.Exception.Message
  }
}

# =============================================================================
# def PLACEMENT / REGISTRATION
# =============================================================================
function def_CopyToCanonicalSafe {
  param([Parameter(Mandatory=$true)]$Row)

  if ($Row.Action -eq "SKIP") {
    return [pscustomobject]@{ FileName=$Row.FileName; Ok=$true; Action="SKIP"; Message="Registry output skipped"; TargetPath=$Row.TargetPath }
  }

  if (-not $Row.NeedsPlacement -or $def_PARAM_ACTION_MODE -eq "REGISTER_ONLY") {
    return [pscustomobject]@{ FileName=$Row.FileName; Ok=$true; Action="REGISTER_ONLY"; Message="Already registered or register-only mode"; TargetPath=$Row.TargetPath }
  }

  try {
    def_EnsureDirectory -PathValue $Row.TargetDir

    $source = $Row.FullPath
    $target = $Row.TargetPath

    if ((Test-Path -LiteralPath $target) -and ((def_GetFileHashSafe -PathValue $target) -eq $Row.Sha256)) {
      return [pscustomobject]@{ FileName=$Row.FileName; Ok=$true; Action="ALREADY_COPIED"; Message="Same hash already exists at canonical target"; TargetPath=$target }
    }

    if ((Test-Path -LiteralPath $target) -and ((def_GetFileHashSafe -PathValue $target) -ne $Row.Sha256)) {
      $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
      $target = Join-Path $Row.TargetDir ("{0}.{1}.dup{2}{3}" -f [System.IO.Path]::GetFileNameWithoutExtension($Row.FileName), $stamp, "", [System.IO.Path]::GetExtension($Row.FileName))
    }

    if ($def_PARAM_ENABLE_BACKUP_BEFORE_COPY) {
      $backupRelative = ($Row.RelativePath -replace "[:\\/]+", "__")
      $backupTarget = Join-Path $def_PARAM_CANONICAL_BACKUP_DIR ("{0}__{1}" -f (Get-Date -Format "yyyyMMdd_HHmmss"), $backupRelative)
      def_EnsureDirectory -PathValue ([System.IO.Path]::GetDirectoryName($backupTarget))
      Copy-Item -LiteralPath $source -Destination $backupTarget -Force
    }

    Copy-Item -LiteralPath $source -Destination $target -Force
    return [pscustomobject]@{ FileName=$Row.FileName; Ok=$true; Action="COPIED_TO_CANONICAL"; Message="Source preserved; canonical copy created"; TargetPath=$target }
  } catch {
    return [pscustomobject]@{ FileName=$Row.FileName; Ok=$false; Action="COPY_FAILED"; Message=$_.Exception.Message; TargetPath=$Row.TargetPath }
  }
}

function def_BuildManagerPresenceMatrix {
  param([Parameter(Mandatory=$true)]$Rows)

  $matrix = @()
  foreach ($rule in $def_PARAM_SUPPORTIVE_RULES) {
    $role = [string](def_GetRuleValue -Rule $rule -Name "Role" -DefaultValue "SUPPORTIVE_UNKNOWN")
    $folder = [string](def_GetRuleValue -Rule $rule -Name "Folder" -DefaultValue "_inbox_to_classify")
    $manager = [string](def_GetRuleValue -Rule $rule -Name "Manager" -DefaultValue "MANUAL_REVIEW")
    $responsibility = [string](def_GetRuleValue -Rule $rule -Name "Responsibility" -DefaultValue "支援性模組")
    $present = @($Rows | Where-Object { $_.FileName -eq $manager -or $_.ManagerFile -eq $manager }).Count -gt 0
    $ownedCount = @($Rows | Where-Object { $_.Domain -eq "SUPPORTIVE" -and $_.ManagerFile -eq $manager }).Count
    $matrix += [pscustomobject]@{
      Domain="SUPPORTIVE"
      Role=$role
      Folder=$folder
      ManagerFile=$manager
      Responsibility=$responsibility
      Present=$present
      OwnedFiles=$ownedCount
      Status= if ($present) { "GREEN_PRESENT" } else { "RED_MANAGER_MISSING" }
      RYG= if ($present) { "GREEN" } else { "RED" }
    }
  }
  foreach ($rule in $def_PARAM_FUNCTIONAL_RULES) {
    $role = [string](def_GetRuleValue -Rule $rule -Name "Role" -DefaultValue "FUNCTIONAL_UNKNOWN")
    $folder = [string](def_GetRuleValue -Rule $rule -Name "Folder" -DefaultValue "_inbox_to_classify")
    $manager = [string](def_GetRuleValue -Rule $rule -Name "Manager" -DefaultValue "MANUAL_REVIEW")
    $responsibility = [string](def_GetRuleValue -Rule $rule -Name "Responsibility" -DefaultValue "功能性模組")
    $present = @($Rows | Where-Object { $_.FileName -eq $manager -or $_.ManagerFile -eq $manager -or ($_.Domain -eq "FUNCTIONAL" -and $_.Role -eq $role) }).Count -gt 0
    $ownedCount = @($Rows | Where-Object { $_.Domain -eq "FUNCTIONAL" -and $_.Role -eq $role }).Count
    $matrix += [pscustomobject]@{
      Domain="FUNCTIONAL"
      Role=$role
      Folder=$folder
      ManagerFile=$manager
      Responsibility=$responsibility
      Present=$present
      OwnedFiles=$ownedCount
      Status= if ($present) { "GREEN_PRESENT_OR_CONTENT_FOUND" } else { "YELLOW_NO_EXPLICIT_MANAGER" }
      RYG= if ($present) { "GREEN" } else { "YELLOW" }
    }
  }
  return $matrix
}

function def_BuildSummary {
  param(
    [Parameter(Mandatory=$true)]$Rows,
    [Parameter(Mandatory=$true)]$PlacementRows,
    [Parameter(Mandatory=$true)]$ManagerRows
  )
  $jsonRows = @($Rows | Where-Object { $_.IsJson -eq $true })
  $jsonInvalid = @($jsonRows | Where-Object { $_.JsonValid -eq $false })
  $coreMissing = @()
  foreach ($core in $def_PARAM_EXPECTED_CORE_SUPPORTIVE) {
    if (@($Rows | Where-Object { $_.FileName -eq $core }).Count -eq 0) { $coreMissing += $core }
  }
  $unknownRows = @($Rows | Where-Object { $_.Domain -eq "UNKNOWN" })
  $redRows = @($Rows | Where-Object { $_.RYG -eq "RED" })
  $placementFailed = @($PlacementRows | Where-Object { $_.Ok -ne $true })

  $finalHealth = "GREEN"
  $finalGate = "VIA_MODULE_REGISTRY_READY"
  if ($coreMissing.Count -gt 0 -or $jsonInvalid.Count -gt 0 -or $placementFailed.Count -gt 0) {
    $finalHealth = "RED"; $finalGate = "BLOCKED_BY_CORE_OR_JSON_OR_PLACEMENT_ERRORS"
  } elseif ($unknownRows.Count -gt 0 -or $redRows.Count -gt 0) {
    $finalHealth = "YELLOW"; $finalGate = "READY_WITH_REVIEW_ITEMS"
  }

  [pscustomobject]@{
    GeneratedAtTaipei = def_GetNowTaipeiString
    BaseDir = $def_PARAM_BASE_DIR
    ActionMode = $def_PARAM_ACTION_MODE
    TotalFiles = @($Rows).Count
    SupportiveFiles = @($Rows | Where-Object { $_.Domain -eq "SUPPORTIVE" }).Count
    FunctionalFiles = @($Rows | Where-Object { $_.Domain -eq "FUNCTIONAL" }).Count
    ParameterFiles = @($Rows | Where-Object { $_.Domain -eq "PARAMETER" }).Count
    UnknownFiles = $unknownRows.Count
    JsonFiles = $jsonRows.Count
    JsonInvalid = $jsonInvalid.Count
    PlacementAttempts = @($PlacementRows | Where-Object { $_.Action -match "COPY" }).Count
    PlacementFailed = $placementFailed.Count
    CoreExpected = $def_PARAM_EXPECTED_CORE_SUPPORTIVE.Count
    CoreMissingCount = $coreMissing.Count
    CoreMissing = $coreMissing
    ManagerRows = @($ManagerRows).Count
    FinalHealth = $finalHealth
    FinalGate = $finalGate
    ErrorLedgerCount = @($script:def_ERROR_LEDGER).Count
  }
}


# =============================================================================
# def HISTORY RECORD REUSE / CURRENT STATE ASSIST
# =============================================================================
function def_GetHistoryScanRoots {
  $roots = New-Object System.Collections.Generic.List[string]
  foreach ($candidate in @(
    $def_PARAM_CANONICAL_OUTPUT_DIR,
    (Join-Path $def_PARAM_BASE_DIR "supportive modules"),
    (Join-Path $def_PARAM_BASE_DIR "functional modules"),
    (Join-Path $def_PARAM_BASE_DIR "_viam_runs"),
    (Join-Path $def_PARAM_BASE_DIR "_deploy"),
    (Join-Path $def_PARAM_BASE_DIR "_packages"),
    (Join-Path $def_PARAM_BASE_DIR "dict"),
    (Join-Path $def_PARAM_BASE_DIR "registry")
  )) {
    try {
      if (-not [string]::IsNullOrWhiteSpace($candidate) -and (Test-Path -LiteralPath $candidate)) {
        [void]$roots.Add($candidate)
      }
    } catch {
      def_AddErrorLedger -Phase "HISTORY_ROOT" -PathValue $candidate -Message $_.Exception.Message
    }
  }
  return @($roots)
}

function def_ReadHistoryHeadSafe {
  param([Parameter(Mandatory=$true)][string]$PathValue)
  try {
    $bytes = [System.IO.File]::ReadAllBytes($PathValue)
    $count = [Math]::Min($bytes.Length, $def_PARAM_HISTORY_MAX_READ_BYTES)
    return [System.Text.Encoding]::UTF8.GetString($bytes, 0, $count)
  } catch {
    def_AddErrorLedger -Phase "HISTORY_READ_HEAD" -PathValue $PathValue -Message $_.Exception.Message
    return ""
  }
}

function def_GetHistoryEvidenceTags {
  param([Parameter(Mandatory=$true)][string]$SearchText)
  $tags = New-Object System.Collections.Generic.List[string]
  $rules = @(
    @{Tag="NEXUSCORE"; Pattern="(?i)(VeritasNexusCore|NexusCore|Invoke-VeritasNexusCore|Unified Supportive Tooling)"},
    @{Tag="SUPPORTIVE_INDEX"; Pattern="(?i)(VIS_Supportive_Module_Index|supportive module index|10_Core_Runtime|20_Registry_SSOT|30_HardGate_Governance|40_Environment_Health|50_Protection_Acceleration)"},
    @{Tag="REGISTRY_CORE"; Pattern="(?i)(VIA_RegistryCore_v1|RegistryCore|VIA_REGISTRY_CORE|ModuleRecord|append-only|append only)"},
    @{Tag="SSOT_UNIFIED"; Pattern="(?i)(VIA_SSOT_Unified|SSOT|canonical|single source|synonym|alias|regex corpus)"},
    @{Tag="ENV_MANAGER"; Pattern="(?i)(VIA_EnvManager|EnvManager|venv|pip check|environment health|install decision|conflict report)"},
    @{Tag="RUNTIME_BRIDGE"; Pattern="(?i)(VIA_Runtime_Bridge|RuntimeBridge|Runtime Bridge|shared ctx|bootstrap runtime|load core modules)"},
    @{Tag="AEGIS_NEXUS"; Pattern="(?i)(VeritasAegisNexus|Aegis|fetch_json|anti.?bot|TWSE|TPEX|MOPS|yfinance|FinMind|akshare)"},
    @{Tag="CELERITAS"; Pattern="(?i)(VeritasCeleritas|Celeritas|accelerator|xmap|xfetch|xbatch|thread|memory guard|no-stall|nohang)"},
    @{Tag="HARDGATE"; Pattern="(?i)(HardGate|Gate|Seal|Final Activation|no DB write|no SSOT mutation|no canonical mutation|no delete|no_move|no_rollback)"},
    @{Tag="VRN"; Pattern="(?i)(\bVRN\b|VeritasReportNova|PDF|OCR|table extraction|pdfplumber|camelot|pymupdf)"},
    @{Tag="VDF"; Pattern="(?i)(\bVDF\b|VeritasDataForge|TWSE|TPEX|MOPS|base.?info|financial.?data)"},
    @{Tag="VPNS"; Pattern="(?i)(\bVPNS\b|VeritasPanoramaNexus|PanoramaNexus|Smart Asset Command Center)"},
    @{Tag="HTML_UI"; Pattern="(?i)(HTML UI|Dashboard|Matrix|RYG|Health Indicators|panoramic|console)"},
    @{Tag="PARAMETERS"; Pattern="(?i)(parameter|config|schema|manifest|route table|alias map|registry sample|registry full)"},
    @{Tag="NO_STALL"; Pattern="(?i)(no.?stall|nohang|watchdog|timeout|PowerShell remains open|dynamic progress|Write-Progress)"}
  )
  foreach ($rule in $rules) {
    if (def_TestRegexMatchSafe -TextValue $SearchText -PatternValue $rule.Pattern -Phase "HISTORY_EVIDENCE_TAG") {
      [void]$tags.Add($rule.Tag)
    }
  }
  return @($tags | Select-Object -Unique)
}

function def_GetHistoryReusePlan {
  param([Parameter(Mandatory=$true)][string[]]$EvidenceTags)
  if ($EvidenceTags -contains "SUPPORTIVE_INDEX" -or $EvidenceTags -contains "NEXUSCORE") {
    return "reuse_supportive_layering: 10_Core_Runtime / 20_Registry_SSOT / 30_HardGate / 40_Environment / 50_Protection_Acceleration"
  }
  if ($EvidenceTags -contains "REGISTRY_CORE" -or $EvidenceTags -contains "SSOT_UNIFIED") {
    return "reuse_registry_ssot: absorb latest registry rows and SSOT aliases before new classification"
  }
  if ($EvidenceTags -contains "ENV_MANAGER") {
    return "reuse_env_health: read environment aliases, route table, conflict report, install decisions"
  }
  if ($EvidenceTags -contains "HARDGATE") {
    return "reuse_governance_policy: keep no_delete / no_canonical_mutation / append_only gates"
  }
  if ($EvidenceTags -contains "HTML_UI") {
    return "reuse_html_matrix_layout: keep RYG health, matrix tables, latest pointer"
  }
  if ($EvidenceTags -contains "VRN" -or $EvidenceTags -contains "VDF" -or $EvidenceTags -contains "VPNS") {
    return "reuse_functional_registry: use prior subsystem registry and run gates as status evidence"
  }
  return "review_only: evidence low; register as history reference"
}

function def_ScoreHistoryEvidence {
  param(
    [Parameter(Mandatory=$true)][string[]]$EvidenceTags,
    [Parameter(Mandatory=$true)][string]$FileName
  )
  $score = ($EvidenceTags.Count * 10)
  if ($FileName -match "(?i)(LATEST|Summary|SSOT|Registry|Index|Gate|Seal)") { $score += 12 }
  if ($FileName -match "(?i)(Error|Fail|Fatal)") { $score += 4 }
  return $score
}

function def_GetHistoryStatus {
  param([Parameter(Mandatory=$true)][int]$ScoreValue)
  if ($ScoreValue -ge 45) { return "GREEN_REUSABLE_HISTORY" }
  if ($ScoreValue -ge 20) { return "YELLOW_USE_AS_CONTEXT" }
  return "GRAY_REFERENCE_ONLY"
}

function def_NormalizeHistoryFileObject {
  param([Parameter(Mandatory=$true)]$FileObject)
  try {
    $full = [string]$FileObject.FullName
    if ([string]::IsNullOrWhiteSpace($full)) { $full = [string]$FileObject }
    if ([string]::IsNullOrWhiteSpace($full)) { return $null }
    $item = Get-Item -LiteralPath $full -ErrorAction Stop
    if (-not $item.PSIsContainer) { return $item }
    return $null
  } catch {
    def_AddErrorLedger -Phase "HISTORY_NORMALIZE_FILE" -PathValue ([string]$FileObject) -Message $_.Exception.Message
    return $null
  }
}

function def_GetHistorySourceKindSafe {
  param([string]$ExtensionValue)
  $ext = ""
  try { $ext = ([string]$ExtensionValue).ToLowerInvariant() } catch { $ext = "" }
  if ($ext -eq ".json") { return "JSON_REGISTRY_OR_SSOT" }
  if ($ext -eq ".html" -or $ext -eq ".htm") { return "HTML_REPORT_OR_UI" }
  if ($ext -eq ".log") { return "LOG_LEDGER" }
  if ($ext -eq ".md") { return "README_OR_NOTE" }
  return "TEXT_EVIDENCE"
}

function def_ScanHistoryRecords {
  param([Parameter(Mandatory=$true)][string]$RunDir)

  # v0104 no-fatal turbo rewrite:
  # - Do NOT use Generic.List[System.IO.FileInfo], because mixed provider outputs can trigger
  #   "Argument types do not match" during .Add().
  # - Use ArrayList[object], normalize each candidate with Get-Item, and catch every root/pattern/file.
  # - This stage is evidence-only; it must never block current-state scan.
  $historyRows = [System.Collections.ArrayList]::new()
  if (-not $def_PARAM_ENABLE_HISTORY_RECORD_REUSE) { return @() }

  $seen = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
  $candidateFiles = [System.Collections.ArrayList]::new()

  try { $roots = @(def_GetHistoryScanRoots) } catch {
    def_AddErrorLedger -Phase "HISTORY_ROOTS_FATAL_CAUGHT" -PathValue $def_PARAM_BASE_DIR -Message $_.Exception.Message
    $roots = @()
  }

  $rootIndex = 0
  foreach ($root in $roots) {
    $rootIndex++
    foreach ($pattern in $def_PARAM_HISTORY_SCAN_PATTERNS) {
      try {
        if ([string]::IsNullOrWhiteSpace([string]$root) -or -not (Test-Path -LiteralPath $root)) { continue }
        $found = @(Get-ChildItem -LiteralPath $root -File -Recurse -Filter $pattern -ErrorAction SilentlyContinue)
        foreach ($raw in $found) {
          try {
            $f = def_NormalizeHistoryFileObject -FileObject $raw
            if ($null -eq $f) { continue }
            if ($seen.Add([string]$f.FullName)) { [void]$candidateFiles.Add($f) }
            if ($candidateFiles.Count -ge $def_PARAM_HISTORY_MAX_FILES) { break }
          } catch {
            def_AddErrorLedger -Phase "HISTORY_DISCOVERY_ITEM" -PathValue ([string]$raw) -Message $_.Exception.Message
          }
        }
      } catch {
        def_AddErrorLedger -Phase "HISTORY_DISCOVERY_PATTERN" -PathValue ([string]$root) -Message ("pattern={0}; {1}" -f $pattern, $_.Exception.Message)
      }
      if ($candidateFiles.Count -ge $def_PARAM_HISTORY_MAX_FILES) { break }
    }
    if ($candidateFiles.Count -ge $def_PARAM_HISTORY_MAX_FILES) { break }
  }

  try {
    $ordered = @($candidateFiles.ToArray() | Sort-Object LastWriteTime -Descending | Select-Object -First $def_PARAM_HISTORY_MAX_FILES)
  } catch {
    def_AddErrorLedger -Phase "HISTORY_ORDER" -PathValue $RunDir -Message $_.Exception.Message
    $ordered = @($candidateFiles.ToArray())
  }

  $idx = 0
  $total = [Math]::Max(1, @($ordered).Count)
  foreach ($fileRaw in $ordered) {
    $idx++
    try {
      $file = def_NormalizeHistoryFileObject -FileObject $fileRaw
      if ($null -eq $file) { continue }
      if (($idx % $def_PARAM_HISTORY_PROGRESS_EVERY_N_FILES) -eq 0 -or $idx -eq 1 -or $idx -eq $total) {
        def_ShowProgressSafe -Activity "VIA history reuse scan" -Status $file.Name -Current $idx -Total $total -PhaseBase 0 -PhaseSpan 12
      }

      $head = def_ReadHistoryHeadSafe -PathValue $file.FullName
      $searchText = ([string]$file.Name + "`n" + [string]$file.FullName + "`n" + [string]$head)
      try { $tags = @(def_GetHistoryEvidenceTags -SearchText $searchText) } catch {
        def_AddErrorLedger -Phase "HISTORY_TAGS" -FileName $file.Name -PathValue $file.FullName -Message $_.Exception.Message
        $tags = @()
      }
      try { $score = [int](def_ScoreHistoryEvidence -EvidenceTags ([string[]]$tags) -FileName $file.Name) } catch { $score = 0 }
      try { $status = def_GetHistoryStatus -ScoreValue $score } catch { $status = "GRAY_HISTORY_REFERENCE" }
      try { $reusePlan = def_GetHistoryReusePlan -EvidenceTags ([string[]]$tags) } catch { $reusePlan = "review_only: history reuse plan fallback" }
      $sourceKind = def_GetHistorySourceKindSafe -ExtensionValue $file.Extension

      if ($tags.Count -gt 0 -or ([string]$file.Name -match "(?i)(Registry|SSOT|Matrix|Gate|Report|Index|Health|Summary|Seal|Ledger)")) {
        [void]$historyRows.Add([pscustomobject]@{
          RYG = if ($score -ge 45) { "GREEN" } elseif ($score -ge 20) { "YELLOW" } else { "GRAY" }
          Status = $status
          Score = $score
          FileName = [string]$file.Name
          SourceKind = [string]$sourceKind
          EvidenceTags = ([string]::Join(",", [string[]]$tags))
          ReusableFlow = [string]$reusePlan
          RelativePath = [string](def_GetRelativePathSafe -BasePath $def_PARAM_BASE_DIR -FullPath $file.FullName)
          FullPath = [string]$file.FullName
          SizeBytes = [int64]$file.Length
          LastWriteTime = $file.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        })
      }
    } catch {
      $safeName = ""
      $safePath = ""
      try { $safeName = [string]$fileRaw.Name } catch { $safeName = "" }
      try { $safePath = [string]$fileRaw.FullName } catch { $safePath = [string]$fileRaw }
      def_AddErrorLedger -Phase "HISTORY_CLASSIFY_NOFATAL" -FileName $safeName -PathValue $safePath -Message $_.Exception.Message
    }
  }
  Write-Progress -Activity "VIA history reuse scan" -Completed
  return @($historyRows.ToArray())
}

# =============================================================================
# def HTML UI
# =============================================================================
function def_HtmlEncode {
  param($Value)
  if ($null -eq $Value) { return "" }
  return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function def_RowClass {
  param($RYG)
  switch ($RYG) {
    "GREEN" { return "ok" }
    "YELLOW" { return "warn" }
    "RED" { return "fail" }
    default { return "warn" }
  }
}

function def_BuildHtmlRows {
  param(
    [Parameter(Mandatory=$true)]$Rows,
    [Parameter(Mandatory=$true)][string[]]$Columns
  )
  $out = New-Object System.Text.StringBuilder
  $count = 0
  foreach ($row in $Rows) {
    if ($count -ge $def_PARAM_HTML_TABLE_LIMIT) { break }
    try { $rowRyg = $row.RYG } catch { $rowRyg = "YELLOW" }
    $cls = def_RowClass -RYG $rowRyg
    [void]$out.Append("<tr class='$cls'>")
    foreach ($col in $Columns) {
      try { $v = $row.$col } catch { $v = "" }
      if ($v -is [array]) { $v = ($v -join ", ") }
      [void]$out.Append("<td data-col='$(def_HtmlEncode $col)'>$(def_HtmlEncode $v)</td>")
    }
    [void]$out.AppendLine("</tr>")
    $count++
  }
  return $out.ToString()
}

function def_BuildHtmlTable {
  param(
    [Parameter(Mandatory=$true)][string]$Title,
    [Parameter(Mandatory=$true)]$Rows,
    [Parameter(Mandatory=$true)][string[]]$Columns,
    [string]$Note=""
  )
  $thead = ($Columns | ForEach-Object { "<th>$(def_HtmlEncode $_)</th>" }) -join ""
  $tbody = def_BuildHtmlRows -Rows $Rows -Columns $Columns
  return @"
<section class="card">
  <div class="cardHead"><h2>$Title</h2><span>$Note</span></div>
  <div class="tableWrap"><table><thead><tr>$thead</tr></thead><tbody>$tbody</tbody></table></div>
</section>
"@
}

function def_RenderHtmlUi {
  param(
    [Parameter(Mandatory=$true)]$Summary,
    [Parameter(Mandatory=$true)]$Rows,
    [Parameter(Mandatory=$true)]$ManagerRows,
    [Parameter(Mandatory=$true)]$PlacementRows,
    [Parameter(Mandatory=$true)]$ParameterRows,
    [Parameter(Mandatory=$true)]$ErrorRows,
    [Parameter(Mandatory=$true)]$AcceleratorRows,
    [Parameter(Mandatory=$true)]$HistoryRows,
    [Parameter(Mandatory=$true)][string]$RunId,
    [Parameter(Mandatory=$true)][string]$OutputJsonPath
  )

  $healthClass = switch ($Summary.FinalHealth) { "GREEN" { "healthGreen" } "YELLOW" { "healthYellow" } "RED" { "healthRed" } default { "healthYellow" } }
  $kpiCards = @(
    @{k="Total"; v=$Summary.TotalFiles; s="掃描檔案"},
    @{k="Supportive"; v=$Summary.SupportiveFiles; s="支援性模組"},
    @{k="Functional"; v=$Summary.FunctionalFiles; s="功能性模組"},
    @{k="Parameters"; v=$Summary.ParameterFiles; s="參數/Schema"},
    @{k="Unknown"; v=$Summary.UnknownFiles; s="待歸位"},
    @{k="JSON Bad"; v=$Summary.JsonInvalid; s="JSON 錯誤"},
    @{k="Copied"; v=$Summary.PlacementAttempts; s="已複製歸位"},
    @{k="Core Missing"; v=$Summary.CoreMissingCount; s="核心缺口"},
    @{k="Errors"; v=$Summary.ErrorLedgerCount; s="錯誤收斂"},
    @{k="History"; v=$Summary.HistoryEvidenceCount; s="歷史證據"},
    @{k="Reusable"; v=$Summary.HistoryReusableCount; s="可重用流程"}
  )
  $kpiHtml = ($kpiCards | ForEach-Object { "<div class='kpi'><div class='k'>$(def_HtmlEncode $_.k)</div><div class='v'>$(def_HtmlEncode $_.v)</div><div class='s'>$(def_HtmlEncode $_.s)</div></div>" }) -join "`n"

  $fileTable = def_BuildHtmlTable -Title "def File Ownership Matrix" -Rows $Rows -Columns @("RYG","Domain","Role","FileName","ManagerFile","CurrentBucket","Status","Action","Risk","RelativePath","TargetPath","Confidence","Sha256") -Note "支援性 / 功能性 / 參數 / 未判定的總矩陣"
  $managerTable = def_BuildHtmlTable -Title "def Manager Responsibility Matrix" -Rows $ManagerRows -Columns @("RYG","Domain","Role","ManagerFile","Folder","OwnedFiles","Present","Status","Responsibility") -Note "哪個檔案管理支援性模組與功能性模組"
  $placementTable = def_BuildHtmlTable -Title "def Placement Action Matrix" -Rows $PlacementRows -Columns @("Ok","Action","FileName","Message","TargetPath") -Note "歸位動作；來源保留，不刪除"
  $paramTable = def_BuildHtmlTable -Title "def Parameter Integration Matrix" -Rows $ParameterRows -Columns @("RYG","FileName","Role","ManagerFile","Status","ParameterIntegrated","IsJson","JsonValid","JsonError","RelativePath","TargetPath") -Note "參數是否整合、JSON 是否可解析、歸入 SSOT/Registry"
  $unknownRows = @($Rows | Where-Object { $_.Domain -eq "UNKNOWN" -or $_.RYG -ne "GREEN" })
  $unknownTable = def_BuildHtmlTable -Title "def Review / Inbox Matrix" -Rows $unknownRows -Columns @("RYG","Domain","Role","FileName","Status","Risk","Action","RelativePath","TargetPath","JsonError") -Note "仍需人工確認或修正的項目"
  $acceleratorTable = def_BuildHtmlTable -Title "def PowerShell Accelerator Matrix" -Rows $AcceleratorRows -Columns @("Id","Name","Status","Purpose") -Note "15 顆主流程加速器 + 15 顆歷史吸收加速器；不卡斷、動態進度、錯誤收斂與安全歸位"
  $historyTable = def_BuildHtmlTable -Title "def Historical Record Reuse Matrix" -Rows $HistoryRows -Columns @("RYG","Status","Score","FileName","SourceKind","EvidenceTags","ReusableFlow","RelativePath","LastWriteTime") -Note "過去整理紀錄、NexusCore / Registry / SSOT / EnvManager / HardGate / HTML UI 可重用流程"
  $errorTable = def_BuildHtmlTable -Title "def No-Stall Error Ledger" -Rows $ErrorRows -Columns @("TimeTaipei","Phase","FileName","Path","Message","Detail") -Note "單檔失敗不終止；錯誤集中到此矩陣"

  $summaryJson = ($Summary | ConvertTo-Json -Depth 8)
  $coreMissingHtml = if ($Summary.CoreMissing.Count -gt 0) { ($Summary.CoreMissing | ForEach-Object { "<code>$(def_HtmlEncode $_)</code>" }) -join " " } else { "<span class='passText'>全部核心檔已找到</span>" }

  $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>VIA Module Registry UI · $RunId</title>
<style>
:root{
  --bg:#F9F9F6; --surface:#FFFFFF; --ink:#1F2933; --muted:#6B7C78; --line:#DFE7E3;
  --celadon:#DFECEA; --sky:#AFCFCC; --seal:#9F1D1D; --ok:#166534; --warn:#B7791F; --fail:#B91C1C;
  --blue:#2563EB; --teal:#0F766E; --amber:#D97706; --shadow:0 18px 48px rgba(31,41,51,.08);
  --mono:Consolas,'DM Mono','Cascadia Mono',monospace; --sans:'Microsoft JhengHei','Noto Sans TC',Arial,sans-serif;
}
*{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at 12% 6%,rgba(175,207,204,.45),transparent 26%),radial-gradient(circle at 92% 16%,rgba(223,236,234,.75),transparent 28%),var(--bg);color:var(--ink);font-family:var(--sans);font-size:13px;line-height:1.55}
body:before{content:"";position:fixed;inset:-20%;background:linear-gradient(112deg,transparent 0 38%,rgba(159,29,29,.035) 38.2% 38.8%,transparent 39% 100%);pointer-events:none;transform:rotate(-7deg)}
.wrap{max-width:1680px;margin:auto;padding:20px;position:relative}.hero{display:grid;grid-template-columns:1fr auto;gap:16px;align-items:center;background:rgba(255,255,255,.82);backdrop-filter:blur(18px);border:1px solid var(--line);border-radius:24px;padding:22px 24px;box-shadow:var(--shadow)}
.brand{display:flex;gap:16px;align-items:center}.seal{width:58px;height:58px;border-radius:16px;background:var(--seal);color:white;display:grid;place-items:center;font-size:34px;font-weight:900;font-family:serif;box-shadow:0 12px 26px rgba(159,29,29,.22)}
h1{margin:0;font-size:26px;letter-spacing:.02em}.sub{color:var(--muted);font-family:var(--mono);font-size:12px;margin-top:4px}.gate{padding:12px 16px;border-radius:18px;border:1px solid var(--line);min-width:280px;text-align:right}.gate .label{font-size:11px;color:var(--muted);font-family:var(--mono)}.gate .value{font-size:18px;font-weight:800}.healthGreen{background:rgba(22,101,52,.08);color:var(--ok)}.healthYellow{background:rgba(183,121,31,.10);color:var(--warn)}.healthRed{background:rgba(185,28,28,.10);color:var(--fail)}
.toolbar{display:flex;gap:8px;align-items:center;margin:14px 0;flex-wrap:wrap}.toolbar input{flex:1;min-width:260px;border:1px solid var(--line);border-radius:14px;padding:10px 12px;background:white;color:var(--ink)}.btn{border:1px solid var(--line);background:white;border-radius:14px;padding:9px 12px;cursor:pointer;color:var(--ink)}.btn:hover{border-color:var(--sky)}
.kpis{display:grid;grid-template-columns:repeat(9,minmax(110px,1fr));gap:10px;margin:14px 0}@media(max-width:1200px){.kpis{grid-template-columns:repeat(4,1fr)}}@media(max-width:720px){.hero{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,1fr)}}
.kpi{background:rgba(255,255,255,.88);border:1px solid var(--line);border-radius:18px;padding:12px;box-shadow:0 8px 22px rgba(31,41,51,.05)}.k{font-size:11px;color:var(--muted);font-family:var(--mono)}.v{font-size:24px;font-weight:900;margin:4px 0}.s{font-size:11px;color:var(--muted)}
.card{background:rgba(255,255,255,.90);border:1px solid var(--line);border-radius:22px;margin:14px 0;box-shadow:var(--shadow);overflow:hidden}.cardHead{display:flex;justify-content:space-between;gap:12px;align-items:flex-end;padding:16px 18px;border-bottom:1px solid var(--line);background:linear-gradient(90deg,rgba(223,236,234,.62),rgba(255,255,255,.4))}.cardHead h2{margin:0;font-size:17px}.cardHead span{color:var(--muted);font-size:12px}.tableWrap{max-height:620px;overflow:auto}table{width:100%;border-collapse:collapse}th,td{border-bottom:1px solid var(--line);padding:7px 8px;text-align:left;vertical-align:top}th{position:sticky;top:0;background:#F4F8F7;z-index:2;font-size:11px;color:#3b5552}td{font-size:12px}td[data-col='Sha256'],td[data-col='TargetPath'],td[data-col='RelativePath'],td[data-col='FullPath']{font-family:var(--mono);font-size:10.5px;word-break:break-all}.ok td:first-child{color:var(--ok);font-weight:800}.warn td:first-child{color:var(--warn);font-weight:800}.fail td:first-child{color:var(--fail);font-weight:800}.ok{background:rgba(22,101,52,.015)}.warn{background:rgba(183,121,31,.03)}.fail{background:rgba(185,28,28,.035)}
.summary{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 0}.box{background:rgba(255,255,255,.78);border:1px solid var(--line);border-radius:18px;padding:14px}.box h3{margin:0 0 8px 0}.box code{background:var(--celadon);padding:2px 6px;border-radius:8px;margin:2px;display:inline-block}.passText{color:var(--ok);font-weight:800}.footer{color:var(--muted);font-size:11px;margin:20px 4px;font-family:var(--mono)}
.hidden{display:none!important}
</style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <div class="brand"><div class="seal">理</div><div><h1>Veritas Intelligence Analytics · Module Governance UI</h1><div class="sub">$RunId · Generated $($Summary.GeneratedAtTaipei) · $($Summary.BaseDir)</div></div></div>
    <div class="gate $healthClass"><div class="label">def Gate</div><div class="value">$($Summary.FinalGate)</div><div class="label">Health: $($Summary.FinalHealth)</div></div>
  </div>

  <div class="toolbar">
    <input id="q" placeholder="搜尋檔名 / role / manager / path / status..." oninput="filterRows()" />
    <button class="btn" onclick="setFilter('')">全部</button>
    <button class="btn" onclick="setFilter('SUPPORTIVE')">支援性</button>
    <button class="btn" onclick="setFilter('FUNCTIONAL')">功能性</button>
    <button class="btn" onclick="setFilter('PARAMETER')">參數</button>
    <button class="btn" onclick="setFilter('YELLOW')">YELLOW</button>
    <button class="btn" onclick="setFilter('RED')">RED</button>
  </div>

  <div class="kpis">$kpiHtml</div>

  <div class="summary">
    <div class="box"><h3>def Quantity Validation</h3><pre id="summaryJson"></pre></div>
    <div class="box"><h3>def Core Supportive Check</h3><p>$coreMissingHtml</p><p>核心以 Registry + SSOT + Runtime Bridge 管，不硬搬破壞 import；未歸位檔採 canonical copy，來源保留。</p><p><code>$OutputJsonPath</code></p></div>
  </div>

  $historyTable
  $acceleratorTable
  $managerTable
  $paramTable
  $fileTable
  $placementTable
  $unknownTable
  $errorTable

  <div class="footer">No delete · No destructive overwrite · Source preserved · Canonical copy + append-only registry · HTML UI generated locally</div>
</div>
<script>
const SUMMARY = $summaryJson;
document.getElementById('summaryJson').textContent = JSON.stringify(SUMMARY, null, 2);
let activeFilter = '';
function setFilter(v){ activeFilter = v; filterRows(); }
function filterRows(){
  const q = (document.getElementById('q').value || '').toLowerCase();
  document.querySelectorAll('tbody tr').forEach(tr => {
    const t = tr.innerText.toLowerCase();
    const okQ = !q || t.includes(q);
    const okF = !activeFilter || t.includes(activeFilter.toLowerCase());
    tr.classList.toggle('hidden', !(okQ && okF));
  });
}
</script>
</body>
</html>
"@
  return $html
}

# =============================================================================
# def MAIN FLOW
# =============================================================================
function def_InvokeMain {
  $runId = def_GetRunId
  $runDir = Join-Path $def_PARAM_CANONICAL_OUTPUT_DIR $runId
  $jsonPath = Join-Path $runDir "VIA_ModuleOwnershipRegistry.json"
  $supportiveJsonPath = Join-Path $runDir "VIA_SupportiveRegistry.json"
  $functionalJsonPath = Join-Path $runDir "VIA_FunctionalRegistry.json"
  $parameterJsonPath = Join-Path $runDir "VIA_ParameterIntegrationRegistry.json"
  $managerJsonPath = Join-Path $runDir "VIA_ManagerResponsibilityMatrix.json"
  $placementJsonPath = Join-Path $runDir "VIA_PlacementActionMatrix.json"
  $summaryJsonPath = Join-Path $runDir "VIA_ModuleGovernanceSummary.json"
  $errorLedgerJsonPath = Join-Path $runDir "VIA_NoStall_ErrorLedger.json"
  $acceleratorJsonPath = Join-Path $runDir "VIA_45_PS_AcceleratorMatrix.json"
  $historyJsonPath = Join-Path $runDir "VIA_HistoricalRecordReuseMatrix.json"
  $ssotPath = Join-Path $def_PARAM_CANONICAL_OUTPUT_DIR "VIA_ModuleGovernance_SSOT_LATEST.json"
  $htmlPath = Join-Path $runDir "VIA_ModuleGovernance_UI.html"
  $latestHtmlPath = Join-Path $def_PARAM_CANONICAL_OUTPUT_DIR "VIA_ModuleGovernance_UI_LATEST.html"

  Write-Host ""
  Write-Host "================================================================================" -ForegroundColor DarkCyan
  Write-Host "def VIA · SUPPORTIVE / FUNCTIONAL MODULE REGISTRY · HISTORY-AWARE NOFATAL TURBO AIO v0104" -ForegroundColor Cyan
  Write-Host "================================================================================" -ForegroundColor DarkCyan
  Write-Host "Base : $def_PARAM_BASE_DIR" -ForegroundColor Gray
  Write-Host "Run  : $runId" -ForegroundColor Gray

  if (-not (Test-Path -LiteralPath $def_PARAM_BASE_DIR)) {
    throw "Base directory not found: $def_PARAM_BASE_DIR"
  }

  foreach ($dir in @($def_PARAM_CANONICAL_SUPPORTIVE_DIR, $def_PARAM_CANONICAL_FUNCTIONAL_DIR, $def_PARAM_CANONICAL_REGISTRY_DIR, $runDir, $def_PARAM_CANONICAL_BACKUP_DIR)) {
    def_EnsureDirectory -PathValue $dir
  }

  foreach ($rule in $def_PARAM_SUPPORTIVE_RULES) { def_EnsureDirectory -PathValue (Join-Path $def_PARAM_CANONICAL_SUPPORTIVE_DIR ([string](def_GetRuleValue -Rule $rule -Name "Folder" -DefaultValue "_inbox_to_classify"))) }
  foreach ($rule in $def_PARAM_FUNCTIONAL_RULES) { def_EnsureDirectory -PathValue (Join-Path $def_PARAM_CANONICAL_FUNCTIONAL_DIR ([string](def_GetRuleValue -Rule $rule -Name "Folder" -DefaultValue "_inbox_to_classify"))) }
  def_EnsureDirectory -PathValue (Join-Path $def_PARAM_CANONICAL_SUPPORTIVE_DIR "parameters")
  def_EnsureDirectory -PathValue (Join-Path $def_PARAM_CANONICAL_SUPPORTIVE_DIR "_inbox_to_classify")

  Write-Host "[0/6] 回看過去整理紀錄：Registry / SSOT / Gate / HTML / Logs..." -ForegroundColor Yellow
  Write-Host "      History reuse accelerators: 30 ON · read-only · no canonical mutation · type-safe no-fatal" -ForegroundColor DarkGray
  try {
    $historyRows = @(def_ScanHistoryRecords -RunDir $runDir)
  } catch {
    def_AddErrorLedger -Phase "HISTORY_STAGE_FATAL_CAUGHT_CONTINUE" -PathValue $runDir -Message $_.Exception.Message
    $historyRows = @([pscustomobject]@{
      RYG="YELLOW"; Status="HISTORY_STAGE_SKIPPED_NOFATAL"; Score=0; FileName="history_stage"; SourceKind="FALLBACK";
      EvidenceTags=""; ReusableFlow="history scan failed but current scan continues"; RelativePath=""; FullPath=$runDir; SizeBytes=0; LastWriteTime=(Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    })
  }

  Write-Host "[1/6] 掃描檔案與 AST/JSON/關鍵字分類..." -ForegroundColor Yellow
  Write-Host "      45 PS Accelerators: ON · No-fatal stage guard: ON · Turbo ArrayList: ON · Dynamic progress: ON" -ForegroundColor DarkGray

  $extensionSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
  foreach ($extItem in $def_PARAM_SCAN_EXTENSIONS) { [void]$extensionSet.Add($extItem) }

  $files = @()
  try {
    $rawFiles = @(Get-ChildItem -LiteralPath $def_PARAM_BASE_DIR -File -Recurse -ErrorAction SilentlyContinue)
    $scanIndex = 0
    foreach ($f in $rawFiles) {
      $scanIndex++
      if (($scanIndex % $def_PARAM_PROGRESS_EVERY_N_FILES) -eq 0) { def_ShowProgressSafe -Activity "VIA discovery" -Status $f.Name -Current $scanIndex -Total $rawFiles.Count -PhaseBase 0 -PhaseSpan 18 }
      try {
        if ($extensionSet.Contains($f.Extension.ToLowerInvariant()) -and -not (def_TestExcludedPath -FullPath $f.FullName)) { $files += $f }
      } catch {
        def_AddErrorLedger -Phase "DISCOVERY_FILTER" -FileName $f.Name -PathValue $f.FullName -Message $_.Exception.Message
      }
    }
  } catch {
    def_AddErrorLedger -Phase "DISCOVERY" -Message $_.Exception.Message -PathValue $def_PARAM_BASE_DIR
  }

  $rows = @()
  $i = 0
  foreach ($file in $files) {
    $i++
    if (($i % $def_PARAM_PROGRESS_EVERY_N_FILES) -eq 0 -or $i -eq 1 -or $i -eq $files.Count) { def_ShowProgressSafe -Activity "VIA classify" -Status $file.Name -Current $i -Total $files.Count -PhaseBase 18 -PhaseSpan 36 }
    try {
      $rows += def_ClassifyFile -FileObj $file
    } catch {
      $rows += def_NewFailureRow -FileObj $file -Message $_.Exception.Message
    }
  }
  Write-Progress -Activity "VIA classify" -Completed

  Write-Host "[2/6] 產生 Manager Responsibility Matrix..." -ForegroundColor Yellow
  $managerRows = @(def_BuildManagerPresenceMatrix -Rows $rows)

  Write-Host "[3/6] 安全歸位：copy to canonical + registry append-only..." -ForegroundColor Yellow
  $placementRows = @()
  $pIndex = 0
  foreach ($row in $rows) {
    $pIndex++
    if (($pIndex % $def_PARAM_PROGRESS_EVERY_N_FILES) -eq 0 -or $pIndex -eq 1 -or $pIndex -eq $rows.Count) { def_ShowProgressSafe -Activity "VIA placement" -Status $row.FileName -Current $pIndex -Total $rows.Count -PhaseBase 58 -PhaseSpan 24 }
    try {
      $placementRows += def_CopyToCanonicalSafe -Row $row
    } catch {
      def_AddErrorLedger -Phase "PLACEMENT" -FileName $row.FileName -PathValue $row.FullPath -Message $_.Exception.Message
      $placementRows += [pscustomobject]@{ FileName=$row.FileName; Ok=$false; Action="COPY_FAILED_CAUGHT"; Message=$_.Exception.Message; TargetPath=$row.TargetPath }
    }
  }
  Write-Progress -Activity "VIA placement" -Completed

  Write-Host "[4/6] 輸出 SSOT / Registry JSON..." -ForegroundColor Yellow
  def_ShowProgressSafe -Activity "VIA registry output" -Status "Build JSON / SSOT" -Current 1 -Total 2 -PhaseBase 82 -PhaseSpan 10
  $supportiveRows = @($rows | Where-Object { $_.Domain -eq "SUPPORTIVE" })
  $functionalRows = @($rows | Where-Object { $_.Domain -eq "FUNCTIONAL" })
  $parameterRows = @($rows | Where-Object { $_.Domain -eq "PARAMETER" })
  $summary = def_BuildSummary -Rows $rows -PlacementRows $placementRows -ManagerRows $managerRows
  $historyReusableCount = @($historyRows | Where-Object { $_.Status -eq "GREEN_REUSABLE_HISTORY" }).Count
  $summary | Add-Member -NotePropertyName HistoryEvidenceCount -NotePropertyValue @($historyRows).Count -Force
  $summary | Add-Member -NotePropertyName HistoryReusableCount -NotePropertyValue $historyReusableCount -Force
  $summary | Add-Member -NotePropertyName HistoricalRecordReuseEnabled -NotePropertyValue $def_PARAM_ENABLE_HISTORY_RECORD_REUSE -Force

  $ssot = [pscustomobject]@{
    Summary=$summary
    ManagerResponsibilityMatrix=$managerRows
    ModuleOwnershipRegistry=$rows
    SupportiveRegistry=$supportiveRows
    FunctionalRegistry=$functionalRows
    ParameterIntegrationRegistry=$parameterRows
    PlacementActionMatrix=$placementRows
    HistoricalRecordReuseMatrix=$historyRows
    ErrorLedger=@($script:def_ERROR_LEDGER)
    PSAcceleratorMatrix=$def_PARAM_PS_ACCELERATORS
    Policy=[pscustomobject]@{
      NoDelete=$true
      NoSourceOverwrite=$true
      ActionMode=$def_PARAM_ACTION_MODE
      CanonicalSupportiveDir=$def_PARAM_CANONICAL_SUPPORTIVE_DIR
      CanonicalFunctionalDir=$def_PARAM_CANONICAL_FUNCTIONAL_DIR
      RegistryDir=$def_PARAM_CANONICAL_OUTPUT_DIR
    }
  }

  def_WriteJson -PathValue $jsonPath -Payload $rows
  def_WriteJson -PathValue $supportiveJsonPath -Payload $supportiveRows
  def_WriteJson -PathValue $functionalJsonPath -Payload $functionalRows
  def_WriteJson -PathValue $parameterJsonPath -Payload $parameterRows
  def_WriteJson -PathValue $managerJsonPath -Payload $managerRows
  def_WriteJson -PathValue $placementJsonPath -Payload $placementRows
  def_WriteJson -PathValue $summaryJsonPath -Payload $summary
  def_WriteJson -PathValue $errorLedgerJsonPath -Payload @($script:def_ERROR_LEDGER)
  def_WriteJson -PathValue $acceleratorJsonPath -Payload $def_PARAM_PS_ACCELERATORS
  def_WriteJson -PathValue $historyJsonPath -Payload $historyRows
  def_WriteJson -PathValue $ssotPath -Payload $ssot

  Write-Host "[5/6] 產生並開啟 HTML U/I..." -ForegroundColor Yellow
  def_ShowProgressSafe -Activity "VIA HTML UI" -Status "Render HTML" -Current 1 -Total 2 -PhaseBase 92 -PhaseSpan 8
  $html = def_RenderHtmlUi -Summary $summary -Rows $rows -ManagerRows $managerRows -PlacementRows $placementRows -ParameterRows $parameterRows -ErrorRows @($script:def_ERROR_LEDGER) -AcceleratorRows $def_PARAM_PS_ACCELERATORS -HistoryRows $historyRows -RunId $runId -OutputJsonPath $ssotPath
  def_WriteTextUtf8 -PathValue $htmlPath -TextValue $html
  Copy-Item -LiteralPath $htmlPath -Destination $latestHtmlPath -Force
  def_ShowProgressSafe -Activity "VIA HTML UI" -Status "Completed" -Current 2 -Total 2 -PhaseBase 92 -PhaseSpan 8
  Write-Progress -Activity "VIA HTML UI" -Completed

  if ($def_PARAM_OPEN_HTML_UI) {
    Start-Process -FilePath $htmlPath | Out-Null
  }

  Write-Host ""
  Write-Host "================================================================================" -ForegroundColor DarkCyan
  Write-Host "def RESULT" -ForegroundColor Cyan
  Write-Host "================================================================================" -ForegroundColor DarkCyan
  Write-Host "Gate        : $($summary.FinalGate)" -ForegroundColor $(if($summary.FinalHealth -eq 'GREEN'){'Green'}elseif($summary.FinalHealth -eq 'YELLOW'){'Yellow'}else{'Red'})
  Write-Host "Health      : $($summary.FinalHealth)" -ForegroundColor $(if($summary.FinalHealth -eq 'GREEN'){'Green'}elseif($summary.FinalHealth -eq 'YELLOW'){'Yellow'}else{'Red'})
  Write-Host "Total       : $($summary.TotalFiles)" -ForegroundColor Gray
  Write-Host "Supportive  : $($summary.SupportiveFiles)" -ForegroundColor Gray
  Write-Host "Functional  : $($summary.FunctionalFiles)" -ForegroundColor Gray
  Write-Host "Parameters  : $($summary.ParameterFiles)" -ForegroundColor Gray
  Write-Host "Unknown     : $($summary.UnknownFiles)" -ForegroundColor Gray
  Write-Host "HTML        : $htmlPath" -ForegroundColor Green
  Write-Host "Latest HTML : $latestHtmlPath" -ForegroundColor Green
  Write-Host "SSOT        : $ssotPath" -ForegroundColor Green
  Write-Host "Errors      : $errorLedgerJsonPath" -ForegroundColor Green
  Write-Host "Accelerator : $acceleratorJsonPath" -ForegroundColor Green
  Write-Host "History     : $historyJsonPath" -ForegroundColor Green

  return [pscustomobject]@{
    ok=($summary.FinalHealth -ne "RED")
    gate=$summary.FinalGate
    health=$summary.FinalHealth
    html_path=$htmlPath
    latest_html_path=$latestHtmlPath
    ssot_path=$ssotPath
    error_ledger_path=$errorLedgerJsonPath
    accelerator_matrix_path=$acceleratorJsonPath
    history_reuse_matrix_path=$historyJsonPath
    summary=$summary
  }
}


function def_WriteEmergencyHtmlOnFatal {
  param([Parameter(Mandatory=$true)]$ErrorRecord)
  try {
    $fallbackRoot = Join-Path $def_PARAM_CANONICAL_OUTPUT_DIR "_fatal_fallback"
    def_EnsureDirectory -PathValue $fallbackRoot
    $fallbackHtml = Join-Path $fallbackRoot "VIA_ModuleGovernance_UI_FATAL_FALLBACK.html"
    $fallbackJson = Join-Path $fallbackRoot "VIA_NoStall_FatalFallback.json"
    $payload = [pscustomobject]@{
      generated_at = def_GetNowTaipeiString
      base = $def_PARAM_BASE_DIR
      message = [string]$ErrorRecord.Exception.Message
      stack = [string]$ErrorRecord.ScriptStackTrace
      policy = "NO_DELETE_NO_SOURCE_OVERWRITE_FATAL_FALLBACK_ONLY"
    }
    def_WriteJson -PathValue $fallbackJson -Payload $payload
    $msg = def_HtmlEncode $payload.message
    $stk = def_HtmlEncode $payload.stack
    $html = "<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VIA Fatal Fallback</title><style>body{font-family:'Noto Sans TC',Arial,sans-serif;background:#F9F9F6;color:#1F2933;padding:28px}.card{background:#fff;border:1px solid #DFECEA;border-radius:16px;padding:18px;margin:12px 0}pre{white-space:pre-wrap;background:#f3f4f6;padding:12px;border-radius:12px}.warn{color:#B7791F}.fail{color:#B91C1C}</style></head><body><div class='card'><h1>def VIA · No-Stall Fatal Fallback</h1><p class='warn'>主流程發生未預期錯誤，但 fallback HTML 已產出；來源檔未刪除、未覆蓋。</p></div><div class='card'><h2>def Fatal Message</h2><pre>$msg</pre></div><div class='card'><h2>def Stack</h2><pre>$stk</pre></div><div class='card'><h2>def Next</h2><p>請改跑 v0104；若仍出錯，查看 $fallbackJson。</p></div></body></html>"
    def_WriteTextUtf8 -PathValue $fallbackHtml -TextValue $html
    Copy-Item -LiteralPath $fallbackHtml -Destination (Join-Path $def_PARAM_CANONICAL_OUTPUT_DIR "VIA_ModuleGovernance_UI_LATEST.html") -Force -ErrorAction SilentlyContinue
    if ($def_PARAM_OPEN_HTML_UI) { Start-Process -FilePath $fallbackHtml | Out-Null }
    Write-Host "Fallback HTML: $fallbackHtml" -ForegroundColor Yellow
    Write-Host "Fallback JSON: $fallbackJson" -ForegroundColor Yellow
  } catch {
    Write-Host "[WARN] Emergency HTML failed: $($_.Exception.Message)" -ForegroundColor Yellow
  }
}

# =============================================================================
# def ENTRYPOINT
# =============================================================================
try {
  $def_RESULT = def_InvokeMain
  $def_RESULT | ConvertTo-Json -Depth 8
} catch {
  Write-Host ""
  Write-Host "[FATAL CAUGHT · NO-STALL FALLBACK] $($_.Exception.Message)" -ForegroundColor Red
  Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
  def_WriteEmergencyHtmlOnFatal -ErrorRecord $_
} finally {
  if ($def_PARAM_KEEP_POWERSHELL_OPEN) {
    Write-Host ""
    Write-Host "PowerShell remains open. Press Enter to return to prompt." -ForegroundColor Cyan
    Read-Host | Out-Null
  }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
