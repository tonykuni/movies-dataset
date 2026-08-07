#requires -Version 7.0
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
$def_PARAM_RUN_PREFIX = "VIA_SUPPORTIVE_FUNCTIONAL_REGISTRY"
$def_PARAM_TIMEZONE = "Asia/Taipei"
$def_PARAM_ACTION_MODE = "COPY_TO_CANONICAL_AND_REGISTER"  # REGISTER_ONLY | COPY_TO_CANONICAL_AND_REGISTER
$def_PARAM_OPEN_HTML_UI = $true
$def_PARAM_KEEP_POWERSHELL_OPEN = $true
$def_PARAM_ENABLE_BACKUP_BEFORE_COPY = $true
$def_PARAM_SCAN_DIRECT_ONLY_FOR_ROOT_RELOCATION = $false
$def_PARAM_MAX_CONTENT_READ_BYTES = 262144
$def_PARAM_JSON_DEPTH = 18
$def_PARAM_HTML_TABLE_LIMIT = 2000

$def_PARAM_CANONICAL_SUPPORTIVE_DIR = Join-Path $def_PARAM_BASE_DIR "supportive modules"
$def_PARAM_CANONICAL_FUNCTIONAL_DIR = Join-Path $def_PARAM_BASE_DIR "functional modules"
$def_PARAM_CANONICAL_REGISTRY_DIR = Join-Path $def_PARAM_BASE_DIR "_via_registry"
$def_PARAM_CANONICAL_OUTPUT_DIR = Join-Path $def_PARAM_CANONICAL_REGISTRY_DIR "supportive_functional_registry"
$def_PARAM_CANONICAL_BACKUP_DIR = Join-Path $def_PARAM_CANONICAL_REGISTRY_DIR "_source_backups"

$def_PARAM_SCAN_EXTENSIONS = @(".py", ".ps1", ".psm1", ".json", ".html", ".htm", ".md", ".txt", ".csv")
$def_PARAM_EXCLUDE_DIR_KEYWORDS = @("\.git", "__pycache__", "node_modules", "\.venv", "\venv", "\_envs", "\_backup", "\_bak", "\_via_registry")
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
  $normalized = $FullPath.Replace('/', '\')
  foreach ($kw in $def_PARAM_EXCLUDE_DIR_KEYWORDS) {
    if ($normalized -match $kw) { return $true }
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
  if ($FileName -match $Rule.Pattern) { $score += 5 }
  if ($SearchText -match $Rule.Pattern) { $score += 2 }
  if ($FileName -eq $Rule.Manager) { $score += 10 }
  return $score
}

function def_ClassifyFile {
  param([Parameter(Mandatory=$true)][System.IO.FileInfo]$FileObj)

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
    $role = $bestParameter.Role
    $folder = $bestParameter.Folder
    $manager = "VIA_SSOT_Unified.py / VIA_RegistryCore_v1.py"
    $responsibility = $bestParameter.Responsibility
    $confidence = $bestParameterScore
  }

  if ($bestSupportiveScore -ge $bestFunctionalScore -and $bestSupportiveScore -ge 4) {
    $domain = "SUPPORTIVE"
    $role = $bestSupportive.Role
    $folder = $bestSupportive.Folder
    $manager = $bestSupportive.Manager
    $responsibility = $bestSupportive.Responsibility
    $confidence = $bestSupportiveScore
  } elseif ($bestFunctionalScore -gt $bestSupportiveScore -and $bestFunctionalScore -ge 4) {
    $domain = "FUNCTIONAL"
    $role = $bestFunctional.Role
    $folder = $bestFunctional.Folder
    $manager = $bestFunctional.Manager
    $responsibility = $bestFunctional.Responsibility
    $confidence = $bestFunctionalScore
  }

  if ($domain -eq "UNKNOWN" -and $ext -eq ".html") {
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
  elseif ($relative -notmatch "\\") { $currentBucket = "BASE_ROOT" }

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
  if ($fileName -match "(?i)(delete|remove|format|shutdown|stop-process|kill|credential|secret|token|key)") { $risk = "HIGH" }

  [pscustomobject]@{
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
    $present = @($Rows | Where-Object { $_.FileName -eq $rule.Manager -or $_.ManagerFile -eq $rule.Manager }).Count -gt 0
    $ownedCount = @($Rows | Where-Object { $_.Domain -eq "SUPPORTIVE" -and $_.ManagerFile -eq $rule.Manager }).Count
    $matrix += [pscustomobject]@{
      Domain="SUPPORTIVE"
      Role=$rule.Role
      Folder=$rule.Folder
      ManagerFile=$rule.Manager
      Responsibility=$rule.Responsibility
      Present=$present
      OwnedFiles=$ownedCount
      Status= if ($present) { "GREEN_PRESENT" } else { "RED_MANAGER_MISSING" }
      RYG= if ($present) { "GREEN" } else { "RED" }
    }
  }
  foreach ($rule in $def_PARAM_FUNCTIONAL_RULES) {
    $present = @($Rows | Where-Object { $_.FileName -eq $rule.Manager -or $_.ManagerFile -eq $rule.Manager -or ($_.Domain -eq "FUNCTIONAL" -and $_.Role -eq $rule.Role) }).Count -gt 0
    $ownedCount = @($Rows | Where-Object { $_.Domain -eq "FUNCTIONAL" -and $_.Role -eq $rule.Role }).Count
    $matrix += [pscustomObject]@{
      Domain="FUNCTIONAL"
      Role=$rule.Role
      Folder=$rule.Folder
      ManagerFile=$rule.Manager
      Responsibility=$rule.Responsibility
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
  }
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
    $cls = def_RowClass -RYG $row.RYG
    [void]$out.Append("<tr class='$cls'>")
    foreach ($col in $Columns) {
      $v = $row.$col
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
    @{k="Core Missing"; v=$Summary.CoreMissingCount; s="核心缺口"}
  )
  $kpiHtml = ($kpiCards | ForEach-Object { "<div class='kpi'><div class='k'>$(def_HtmlEncode $_.k)</div><div class='v'>$(def_HtmlEncode $_.v)</div><div class='s'>$(def_HtmlEncode $_.s)</div></div>" }) -join "`n"

  $fileTable = def_BuildHtmlTable -Title "def File Ownership Matrix" -Rows $Rows -Columns @("RYG","Domain","Role","FileName","ManagerFile","CurrentBucket","Status","Action","Risk","RelativePath","TargetPath","Confidence","Sha256") -Note "支援性 / 功能性 / 參數 / 未判定的總矩陣"
  $managerTable = def_BuildHtmlTable -Title "def Manager Responsibility Matrix" -Rows $ManagerRows -Columns @("RYG","Domain","Role","ManagerFile","Folder","OwnedFiles","Present","Status","Responsibility") -Note "哪個檔案管理支援性模組與功能性模組"
  $placementTable = def_BuildHtmlTable -Title "def Placement Action Matrix" -Rows $PlacementRows -Columns @("Ok","Action","FileName","Message","TargetPath") -Note "歸位動作；來源保留，不刪除"
  $paramTable = def_BuildHtmlTable -Title "def Parameter Integration Matrix" -Rows $ParameterRows -Columns @("RYG","FileName","Role","ManagerFile","Status","ParameterIntegrated","IsJson","JsonValid","JsonError","RelativePath","TargetPath") -Note "參數是否整合、JSON 是否可解析、歸入 SSOT/Registry"
  $unknownRows = @($Rows | Where-Object { $_.Domain -eq "UNKNOWN" -or $_.RYG -ne "GREEN" })
  $unknownTable = def_BuildHtmlTable -Title "def Review / Inbox Matrix" -Rows $unknownRows -Columns @("RYG","Domain","Role","FileName","Status","Risk","Action","RelativePath","TargetPath","JsonError") -Note "仍需人工確認或修正的項目"

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
.kpis{display:grid;grid-template-columns:repeat(8,minmax(110px,1fr));gap:10px;margin:14px 0}@media(max-width:1200px){.kpis{grid-template-columns:repeat(4,1fr)}}@media(max-width:720px){.hero{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,1fr)}}
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

  $managerTable
  $paramTable
  $fileTable
  $placementTable
  $unknownTable

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
  $ssotPath = Join-Path $def_PARAM_CANONICAL_OUTPUT_DIR "VIA_ModuleGovernance_SSOT_LATEST.json"
  $htmlPath = Join-Path $runDir "VIA_ModuleGovernance_UI.html"
  $latestHtmlPath = Join-Path $def_PARAM_CANONICAL_OUTPUT_DIR "VIA_ModuleGovernance_UI_LATEST.html"

  Write-Host ""
  Write-Host "================================================================================" -ForegroundColor DarkCyan
  Write-Host "def VIA · SUPPORTIVE / FUNCTIONAL MODULE REGISTRY · AIO v0100" -ForegroundColor Cyan
  Write-Host "================================================================================" -ForegroundColor DarkCyan
  Write-Host "Base : $def_PARAM_BASE_DIR" -ForegroundColor Gray
  Write-Host "Run  : $runId" -ForegroundColor Gray

  if (-not (Test-Path -LiteralPath $def_PARAM_BASE_DIR)) {
    throw "Base directory not found: $def_PARAM_BASE_DIR"
  }

  foreach ($dir in @($def_PARAM_CANONICAL_SUPPORTIVE_DIR, $def_PARAM_CANONICAL_FUNCTIONAL_DIR, $def_PARAM_CANONICAL_REGISTRY_DIR, $runDir, $def_PARAM_CANONICAL_BACKUP_DIR)) {
    def_EnsureDirectory -PathValue $dir
  }

  foreach ($rule in $def_PARAM_SUPPORTIVE_RULES) { def_EnsureDirectory -PathValue (Join-Path $def_PARAM_CANONICAL_SUPPORTIVE_DIR $rule.Folder) }
  foreach ($rule in $def_PARAM_FUNCTIONAL_RULES) { def_EnsureDirectory -PathValue (Join-Path $def_PARAM_CANONICAL_FUNCTIONAL_DIR $rule.Folder) }
  def_EnsureDirectory -PathValue (Join-Path $def_PARAM_CANONICAL_SUPPORTIVE_DIR "parameters")
  def_EnsureDirectory -PathValue (Join-Path $def_PARAM_CANONICAL_SUPPORTIVE_DIR "_inbox_to_classify")

  Write-Host "[1/5] 掃描檔案與 AST/JSON/關鍵字分類..." -ForegroundColor Yellow
  $files = Get-ChildItem -LiteralPath $def_PARAM_BASE_DIR -File -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $def_PARAM_SCAN_EXTENSIONS -contains $_.Extension.ToLowerInvariant() } |
    Where-Object { -not (def_TestExcludedPath -FullPath $_.FullName) }

  $rows = @()
  $i = 0
  foreach ($file in $files) {
    $i++
    if (($i % 50) -eq 0) { Write-Progress -Activity "VIA module scan" -Status $file.Name -PercentComplete ([Math]::Min(95, ($i / [Math]::Max(1,$files.Count))*100)) }
    $rows += def_ClassifyFile -FileObj $file
  }
  Write-Progress -Activity "VIA module scan" -Completed

  Write-Host "[2/5] 產生 Manager Responsibility Matrix..." -ForegroundColor Yellow
  $managerRows = @(def_BuildManagerPresenceMatrix -Rows $rows)

  Write-Host "[3/5] 安全歸位：copy to canonical + registry append-only..." -ForegroundColor Yellow
  $placementRows = @()
  foreach ($row in $rows) {
    $placementRows += def_CopyToCanonicalSafe -Row $row
  }

  Write-Host "[4/5] 輸出 SSOT / Registry JSON..." -ForegroundColor Yellow
  $supportiveRows = @($rows | Where-Object { $_.Domain -eq "SUPPORTIVE" })
  $functionalRows = @($rows | Where-Object { $_.Domain -eq "FUNCTIONAL" })
  $parameterRows = @($rows | Where-Object { $_.Domain -eq "PARAMETER" })
  $summary = def_BuildSummary -Rows $rows -PlacementRows $placementRows -ManagerRows $managerRows

  $ssot = [pscustomobject]@{
    Summary=$summary
    ManagerResponsibilityMatrix=$managerRows
    ModuleOwnershipRegistry=$rows
    SupportiveRegistry=$supportiveRows
    FunctionalRegistry=$functionalRows
    ParameterIntegrationRegistry=$parameterRows
    PlacementActionMatrix=$placementRows
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
  def_WriteJson -PathValue $ssotPath -Payload $ssot

  Write-Host "[5/5] 產生並開啟 HTML U/I..." -ForegroundColor Yellow
  $html = def_RenderHtmlUi -Summary $summary -Rows $rows -ManagerRows $managerRows -PlacementRows $placementRows -ParameterRows $parameterRows -RunId $runId -OutputJsonPath $ssotPath
  def_WriteTextUtf8 -PathValue $htmlPath -TextValue $html
  Copy-Item -LiteralPath $htmlPath -Destination $latestHtmlPath -Force

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

  return [pscustomobject]@{
    ok=($summary.FinalHealth -ne "RED")
    gate=$summary.FinalGate
    health=$summary.FinalHealth
    html_path=$htmlPath
    latest_html_path=$latestHtmlPath
    ssot_path=$ssotPath
    summary=$summary
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
  Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
  Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
} finally {
  if ($def_PARAM_KEEP_POWERSHELL_OPEN) {
    Write-Host ""
    Write-Host "PowerShell remains open. Press Enter to return to prompt." -ForegroundColor Cyan
    Read-Host | Out-Null
  }
}
