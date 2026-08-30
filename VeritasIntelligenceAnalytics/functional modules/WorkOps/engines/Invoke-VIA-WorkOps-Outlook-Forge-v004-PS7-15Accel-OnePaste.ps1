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
& {
<#
.SYNOPSIS
    VERITAS INTELLIGENCE ANALYTICS
    VIA WorkOps Intelligence Workbench
    Outlook 全資料夾唯讀郵件智慧化整合器 v004 · PS7+ · 15 Accelerators · Forge Static Integration

.DESCRIPTION
    - 僅支援 PowerShell 7 以上；可整段貼入或另存 .ps1 執行。
    - 不使用頂層 param()，避免互動式貼上造成 ParserError。
    - 只讀目前使用者 Classic Outlook Profile 可見的 Store 與資料夾。
    - 不改已讀、不改分類、不改旗標、不移動、不刪除、不寄送、不儲存附件。
    - 兩階段：先建立資料夾清單，再逐一掃描，因此有精確動態進度。
    - 每個資料夾完成即 append 輸出並寫 checkpoint；非致命錯誤不中止。
    - 同一時間只允許一個執行個體，避免 console paste double-execute。
#>

# ====================================================================================
# def 使用者參數區：只需修改此區
# ====================================================================================

# 留白代表：開始時間＝昨天 00:00；結束時間＝現在。
# 可改成例如：'2026-07-01 00:00:00'、'2026-07-14 23:59:59'
$START_TIME_TEXT = if (-not [string]::IsNullOrWhiteSpace($env:VIA_START_TIME)) { $env:VIA_START_TIME } else { '' }
$END_TIME_TEXT   = if (-not [string]::IsNullOrWhiteSpace($env:VIA_END_TIME))   { $env:VIA_END_TIME }   else { '' }

$OUTPUT_ROOT = Join-Path $env:USERPROFILE 'Downloads\VIA_WorkOps_Mail_ReadOnly_Exports'

$INCLUDE_SUBFOLDERS       = $true
$INCLUDE_SEARCH_FOLDERS   = $false
$INCLUDE_PUBLIC_FOLDERS   = $false
$INCLUDE_MEETING_ITEMS    = $true

# 為本機關鍵字與分類分析，讀取有限長度純文字片段；不寫回 Outlook。
$INCLUDE_BODY_SNIPPET     = $true
$BODY_SNIPPET_LENGTH      = 2400
$INCLUDE_ATTACHMENT_NAMES = $true

# 優先使用 Outlook Restrict 依時間過濾；失敗才逐項後備掃描。
$USE_RESTRICT             = $true

# 0＝不限制。安全試跑可設 500 或 1000。
$MAX_ITEMS_PER_FOLDER     = 0

# 中斷後再次執行相同時間範圍時，自動續跑未完成 RunDir。
$RESUME_INCOMPLETE        = $true

# 每掃描多少個項目更新一次心跳與第二層進度。
$HEARTBEAT_EVERY_ITEMS    = 100

# A05：略過預設項目型別不是郵件的 Calendar / Contacts / Tasks 等資料夾。
$SKIP_NON_MAIL_DEFAULT_FOLDERS = $true

# A14：固定完成若干資料夾後回收 COM 參照，降低長時間掃描記憶體累積。
$GC_EVERY_FOLDERS         = 20

$OPEN_REPORT              = $true

# VIA Forge 靜態整合：只讀取原始碼、JSON、README、docs/runtime/ui；不 import、不啟動 server、不執行未知命令。
$FORGE_ROOT_HINT = 'C:\Users\tonyk\Downloads\VIA_Forge (3)\VIA_Forge'
$AUTO_FIND_FORGE_ROOT = $true
$FORGE_MAX_FILE_BYTES = 4MB

# 自動關鍵字、專案候選、利害關係人、未回覆、Process Mining 與 Controlling Sheet。
$AUTO_KEYWORD_DISCOVERY = $true
$KEYWORD_TOP_N = 300
$MAIL_KEYWORDS_PER_ITEM = 12
$RESPONSE_SLA_HOURS = 72
$PROJECT_CLUSTER_MIN_MAILS = 2
$OPEN_PROJECT_REVIEW_CSV = $false

# ====================================================================================
# def 固定安全政策與時間解析
# ====================================================================================

if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw '此最新版僅支援 PowerShell 7 以上。請使用 pwsh 執行。'
}

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$SCRIPT_VERSION = 'v004'
$POLICY = 'PS7+ / read-only source / user-scope / no install / no registry / no mail mutation / no target import / Forge static-only integration / checkpoint-resume / 15-accelerator / run-local output'
$MAIL_ITEM_CLASS = 43
$MEETING_ITEM_CLASSES = @(53, 54, 55, 56, 57)
$SEARCH_FOLDER_PATTERNS = @('Search Folders', '搜尋資料夾', '検索フォルダー')
$PUBLIC_STORE_PATTERNS = @('Public Folders', '公用資料夾', '公共資料夾')
$INTERNET_MESSAGE_ID_PROPS = @(
    'http://schemas.microsoft.com/mapi/proptag/0x1035001F',
    'http://schemas.microsoft.com/mapi/proptag/0x1035001E'
)

function def_ResolveDateTime {
    [CmdletBinding()]
    param(
        [AllowEmptyString()][string]$Text,
        [Parameter(Mandatory)][datetime]$DefaultValue,
        [Parameter(Mandatory)][string]$Name
    )

    if ([string]::IsNullOrWhiteSpace($Text)) { return $DefaultValue }

    $value = [datetime]::MinValue
    if ([datetime]::TryParse(
        $Text,
        [Globalization.CultureInfo]::CurrentCulture,
        [Globalization.DateTimeStyles]::AllowWhiteSpaces,
        [ref]$value
    )) {
        return $value
    }

    if ([datetime]::TryParse(
        $Text,
        [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::AllowWhiteSpaces,
        [ref]$value
    )) {
        return $value
    }

    throw "$Name 格式無法解析：$Text。建議使用 yyyy-MM-dd HH:mm:ss。"
}

$StartTime = def_ResolveDateTime -Text $START_TIME_TEXT -DefaultValue ((Get-Date).Date.AddDays(-1)) -Name 'START_TIME_TEXT'
$EndTime   = def_ResolveDateTime -Text $END_TIME_TEXT   -DefaultValue (Get-Date) -Name 'END_TIME_TEXT'

if ($StartTime -gt $EndTime) {
    throw 'StartTime 不可晚於 EndTime。'
}

if ($BODY_SNIPPET_LENGTH -lt 100 -or $BODY_SNIPPET_LENGTH -gt 5000) {
    throw 'BODY_SNIPPET_LENGTH 必須介於 100 與 5000。'
}

if ($MAX_ITEMS_PER_FOLDER -lt 0) {
    throw 'MAX_ITEMS_PER_FOLDER 不可小於 0。'
}

if ($HEARTBEAT_EVERY_ITEMS -lt 1) {
    $HEARTBEAT_EVERY_ITEMS = 100
}

$Config = [pscustomobject][ordered]@{
    StartTime              = $StartTime
    EndTime                = $EndTime
    OutputRoot             = $OUTPUT_ROOT
    IncludeSubfolders      = $INCLUDE_SUBFOLDERS
    IncludeSearchFolders   = $INCLUDE_SEARCH_FOLDERS
    IncludePublicFolders   = $INCLUDE_PUBLIC_FOLDERS
    IncludeMeetingItems    = $INCLUDE_MEETING_ITEMS
    IncludeBodySnippet     = $INCLUDE_BODY_SNIPPET
    BodySnippetLength      = $BODY_SNIPPET_LENGTH
    IncludeAttachmentNames = $INCLUDE_ATTACHMENT_NAMES
    UseRestrict            = $USE_RESTRICT
    MaxItemsPerFolder      = $MAX_ITEMS_PER_FOLDER
    ResumeIncomplete       = $RESUME_INCOMPLETE
    HeartbeatEveryItems    = $HEARTBEAT_EVERY_ITEMS
    SkipNonMailDefaultFolders = $SKIP_NON_MAIL_DEFAULT_FOLDERS
    GcEveryFolders         = $GC_EVERY_FOLDERS
    OpenReport             = $OPEN_REPORT
    ForgeRootHint          = $FORGE_ROOT_HINT
    AutoFindForgeRoot      = $AUTO_FIND_FORGE_ROOT
    ForgeMaxFileBytes      = $FORGE_MAX_FILE_BYTES
    AutoKeywordDiscovery  = $AUTO_KEYWORD_DISCOVERY
    KeywordTopN           = $KEYWORD_TOP_N
    MailKeywordsPerItem   = $MAIL_KEYWORDS_PER_ITEM
    ResponseSlaHours      = $RESPONSE_SLA_HOURS
    ProjectClusterMinMails = $PROJECT_CLUSTER_MIN_MAILS
    OpenProjectReviewCsv  = $OPEN_PROJECT_REVIEW_CSV
}

$State = [pscustomobject][ordered]@{
    StartedAt                 = Get-Date
    Stage                     = 'INITIALIZE'
    FolderPlan                = [System.Collections.Generic.List[object]]::new()
    ErrorRows                 = [System.Collections.Generic.List[object]]::new()
    SeenItemKeys              = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    CompletedFolderKeys       = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    StoreCount                = 0
    PlannedFolderCount        = 0
    CompletedFolderCount      = 0
    SkippedFolderCount        = 0
    RestrictedFolderCount     = 0
    FallbackFolderCount       = 0
    ScannedItemReferenceCount = 0L
    MatchedMailCount          = 0L
    ErrorCount                = 0
    CurrentStore              = ''
    CurrentFolder             = ''
    CurrentFolderIndex        = 0
    CurrentFolderItemIndex    = 0
    CurrentFolderItemTotal    = 0
    LastHeartbeatAt           = Get-Date
    RunDir                    = ''
    MailCsv                   = ''
    FolderCsv                 = ''
    ErrorCsv                  = ''
    ManifestJson              = ''
    CheckpointJson            = ''
    HeartbeatJson             = ''
    ReportHtml                = ''
    AcceleratorCsv            = ''
    ForgeRoot                = ''
    PythonExe                = ''
    HelperPy                 = ''
    ForgeInventoryCsv        = ''
    ForgeCapabilityCsv       = ''
    ForgeKeywordSeedCsv      = ''
    ForgeRiskCsv             = ''
    ForgeActivationCsv       = ''
    KeywordDictionaryCsv     = ''
    EnrichedMailCsv          = ''
    ClusterCandidateCsv      = ''
    ProjectCandidateCsv      = ''
    StakeholderCsv           = ''
    PendingResponseCsv       = ''
    ProcessMiningCsv         = ''
    ControllingCsv           = ''
    ActionRegisterCsv        = ''
    QualityCheckCsv          = ''
    LockPath                  = ''
    LockStream                = $null
    OutlookStartedByTool      = $false
}

# ====================================================================================
# def 十五個安全加速器
# ====================================================================================

$ACCELERATORS = @(
    [pscustomobject][ordered]@{ CODE='A01'; NAME='PS7+ One-Paste Wrapper';               ENABLED=$true;  PURPOSE='PowerShell 7+ 單貼執行，避免互動式 param 解析失敗' }
    [pscustomobject][ordered]@{ CODE='A02'; NAME='Single-Instance Hash Lock';       ENABLED=$true;  PURPOSE='防止重複貼上或雙擊造成同時掃描' }
    [pscustomobject][ordered]@{ CODE='A03'; NAME='Time-Window Restrict';            ENABLED=$Config.UseRestrict; PURPOSE='由 Outlook 先依指定時間縮小集合' }
    [pscustomobject][ordered]@{ CODE='A04'; NAME='Two-Phase Folder Inventory';      ENABLED=$true;  PURPOSE='先盤點再掃描，提供準確總進度' }
    [pscustomobject][ordered]@{ CODE='A05'; NAME='Non-Mail Folder Short-Circuit';   ENABLED=$Config.SkipNonMailDefaultFolders; PURPOSE='略過 Calendar、Contacts、Tasks 等非郵件資料夾' }
    [pscustomobject][ordered]@{ CODE='A06'; NAME='Search/Public Folder Gate';       ENABLED=$true;  PURPOSE='預設略過搜尋與公用資料夾，降低重複與權限噪音' }
    [pscustomobject][ordered]@{ CODE='A07'; NAME='Run-Local Append Output';         ENABLED=$true;  PURPOSE='每個資料夾完成即追加 CSV，不等待全程結束' }
    [pscustomobject][ordered]@{ CODE='A08'; NAME='Checkpoint Resume';               ENABLED=$Config.ResumeIncomplete; PURPOSE='相同時間範圍中斷後從未完成資料夾續跑' }
    [pscustomobject][ordered]@{ CODE='A09'; NAME='Heartbeat JSON';                  ENABLED=$true;  PURPOSE='持續記錄階段、資料夾、郵件與錯誤數' }
    [pscustomobject][ordered]@{ CODE='A10'; NAME='In-Memory Item Dedup';             ENABLED=$true;  PURPOSE='多個 Restrict 條件命中同一郵件時只輸出一次' }
    [pscustomobject][ordered]@{ CODE='A11'; NAME='Folder-Level Buffered CSV';       ENABLED=$true;  PURPOSE='每個資料夾批次落盤，降低逐列磁碟 I/O' }
    [pscustomobject][ordered]@{ CODE='A12'; NAME='Bounded Body Access';                ENABLED=$true; PURPOSE='只讀有限長度內文片段，供本機關鍵字與分類分析' }
    [pscustomobject][ordered]@{ CODE='A13'; NAME='Attachment Metadata Only';        ENABLED=$true;  PURPOSE='只讀附件名稱與數量，不儲存附件' }
    [pscustomobject][ordered]@{ CODE='A14'; NAME='COM Release and GC Cadence';      ENABLED=$true;  PURPOSE='逐物件釋放並定期回收，降低長程記憶體累積' }
    [pscustomobject][ordered]@{ CODE='A15'; NAME='Error Isolation and Fallback';    ENABLED=$true;  PURPOSE='單封／單資料夾錯誤不中止；Restrict 失敗才後備逐項掃描' }
)

# ====================================================================================
# def 通用函式
# ====================================================================================

function def_ToSafeString {
    [CmdletBinding()]
    param([AllowNull()]$Value)

    if ($null -eq $Value) { return '' }
    try { return [string]$Value } catch { return '' }
}

function def_NormalizeSingleLine {
    [CmdletBinding()]
    param(
        [AllowNull()][string]$Text,
        [int]$MaxLength = 0
    )

    if ([string]::IsNullOrWhiteSpace($Text)) { return '' }
    $clean = [regex]::Replace($Text, '[\r\n\t]+', ' ')
    $clean = [regex]::Replace($clean, '\s{2,}', ' ').Trim()
    if ($MaxLength -gt 0 -and $clean.Length -gt $MaxLength) {
        return $clean.Substring(0, $MaxLength)
    }
    return $clean
}

function def_ReleaseComObject {
    [CmdletBinding()]
    param([AllowNull()]$ComObject)

    if ($null -eq $ComObject) { return }
    try {
        if ([Runtime.InteropServices.Marshal]::IsComObject($ComObject)) {
            [void][Runtime.InteropServices.Marshal]::ReleaseComObject($ComObject)
        }
    }
    catch {}
}

function def_GetSha256Text {
    [CmdletBinding()]
    param([AllowEmptyString()][string]$Text)

    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
        return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

function def_WriteTextAtomic {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path,
        [AllowEmptyString()][string]$Content
    )

    $tempPath = "$Path.tmp.$PID"
    [IO.File]::WriteAllText($tempPath, $Content, [Text.UTF8Encoding]::new($true))
    Move-Item -LiteralPath $tempPath -Destination $Path -Force
}

function def_WriteJsonAtomic {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)]$Data,
        [int]$Depth = 8
    )

    def_WriteTextAtomic -Path $Path -Content ($Data | ConvertTo-Json -Depth $Depth)
}

function def_AppendCsvUtf8 {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Rows,
        [Parameter(Mandatory)][string]$Path
    )

    $array = @($Rows)
    if ($array.Count -eq 0) { return }

    if ((Test-Path -LiteralPath $Path) -and ((Get-Item -LiteralPath $Path).Length -gt 0)) {
        if ($PSVersionTable.PSVersion.Major -ge 6) {
            $array | Export-Csv -LiteralPath $Path -NoTypeInformation -Append -Encoding utf8BOM
        }
        else {
            $array | Export-Csv -LiteralPath $Path -NoTypeInformation -Append -Encoding UTF8
        }
    }
    else {
        if ($PSVersionTable.PSVersion.Major -ge 6) {
            $array | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding utf8BOM
        }
        else {
            $array | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
        }
    }
}

function def_AddError {
    [CmdletBinding()]
    param(
        [string]$Stage,
        [string]$StoreName,
        [string]$FolderPath,
        [string]$Message
    )

    $row = [pscustomobject][ordered]@{
        TIME        = (Get-Date).ToString('yyyy/MM/dd HH:mm:ss')
        STAGE       = $Stage
        STORE_NAME  = $StoreName
        FOLDER_PATH = $FolderPath
        ERROR       = def_NormalizeSingleLine -Text $Message -MaxLength 4000
    }

    $State.ErrorRows.Add($row)
    $State.ErrorCount++
}

function def_FlushErrors {
    [CmdletBinding()]
    param()

    if ($State.ErrorRows.Count -gt 0) {
        def_AppendCsvUtf8 -Rows @($State.ErrorRows) -Path $State.ErrorCsv
        $State.ErrorRows.Clear()
    }
}

function def_GetDateValue {
    [CmdletBinding()]
    param([AllowNull()]$Value)

    try {
        if ($null -eq $Value) { return $null }
        $dateValue = [datetime]$Value
        if ($dateValue.Year -lt 1900) { return $null }
        return $dateValue
    }
    catch {
        return $null
    }
}

function def_GetElapsedText {
    [CmdletBinding()]
    param()

    $elapsed = (Get-Date) - $State.StartedAt
    return '{0:00}:{1:00}:{2:00}' -f [int]$elapsed.TotalHours, $elapsed.Minutes, $elapsed.Seconds
}

function def_ShowProgress {
    [CmdletBinding()]
    param(
        [ValidateRange(0, 100)][int]$Percent,
        [string]$Stage,
        [string]$Status
    )

    $State.Stage = $Stage
    $text = '{0} | {1} | Folders {2}/{3} | Items {4:n0} | Mail {5:n0} | Errors {6} | Elapsed {7}' -f `
        $Stage,
        $Status,
        $State.CompletedFolderCount,
        $State.PlannedFolderCount,
        $State.ScannedItemReferenceCount,
        $State.MatchedMailCount,
        $State.ErrorCount,
        (def_GetElapsedText)

    Write-Progress -Id 1 -Activity 'VIA WorkOps · Outlook 唯讀掃描' -Status $text -PercentComplete $Percent

    if ($State.CurrentFolderItemTotal -gt 0) {
        $itemPercent = [Math]::Min(100, [Math]::Max(0, [int](100 * $State.CurrentFolderItemIndex / $State.CurrentFolderItemTotal)))
        Write-Progress -Id 2 -ParentId 1 -Activity '目前資料夾' `
            -Status ("{0} | {1:n0}/{2:n0}" -f $State.CurrentFolder, $State.CurrentFolderItemIndex, $State.CurrentFolderItemTotal) `
            -PercentComplete $itemPercent
    }
}

function def_WriteHeartbeat {
    [CmdletBinding()]
    param([string]$Message)

    $State.LastHeartbeatAt = Get-Date
    $heartbeat = [pscustomobject][ordered]@{
        SYSTEM                     = 'VERITAS INTELLIGENCE ANALYTICS'
        PRODUCT                    = 'VIA WorkOps Intelligence Workbench'
        VERSION                    = $SCRIPT_VERSION
        POLICY                     = $POLICY
        PROCESS_ID                 = $PID
        STAGE                      = $State.Stage
        MESSAGE                    = $Message
        CURRENT_STORE              = $State.CurrentStore
        CURRENT_FOLDER             = $State.CurrentFolder
        CURRENT_FOLDER_INDEX       = $State.CurrentFolderIndex
        PLANNED_FOLDER_COUNT       = $State.PlannedFolderCount
        COMPLETED_FOLDER_COUNT     = $State.CompletedFolderCount
        CURRENT_FOLDER_ITEM_INDEX  = $State.CurrentFolderItemIndex
        CURRENT_FOLDER_ITEM_TOTAL  = $State.CurrentFolderItemTotal
        SCANNED_ITEM_REFERENCE_COUNT = $State.ScannedItemReferenceCount
        MATCHED_MAIL_COUNT         = $State.MatchedMailCount
        ERROR_COUNT                = $State.ErrorCount
        ELAPSED                    = def_GetElapsedText
        UPDATED_AT                 = (Get-Date).ToString('yyyy/MM/dd HH:mm:ss')
    }

    def_WriteJsonAtomic -Path $State.HeartbeatJson -Data $heartbeat -Depth 5
}

function def_WriteCheckpoint {
    [CmdletBinding()]
    param(
        [bool]$Completed = $false,
        [string]$Message = ''
    )

    $checkpoint = [pscustomobject][ordered]@{
        VERSION                    = $SCRIPT_VERSION
        COMPLETED                  = $Completed
        MESSAGE                    = $Message
        START_TIME                 = $Config.StartTime.ToString('yyyy/MM/dd HH:mm:ss')
        END_TIME                   = $Config.EndTime.ToString('yyyy/MM/dd HH:mm:ss')
        PLANNED_FOLDER_COUNT       = $State.PlannedFolderCount
        COMPLETED_FOLDER_COUNT     = $State.CompletedFolderCount
        SKIPPED_FOLDER_COUNT       = $State.SkippedFolderCount
        RESTRICTED_FOLDER_COUNT    = $State.RestrictedFolderCount
        FALLBACK_FOLDER_COUNT      = $State.FallbackFolderCount
        SCANNED_ITEM_REFERENCE_COUNT = $State.ScannedItemReferenceCount
        MATCHED_MAIL_COUNT         = $State.MatchedMailCount
        ERROR_COUNT                = $State.ErrorCount
        COMPLETED_FOLDER_KEYS      = @($State.CompletedFolderKeys)
        UPDATED_AT                 = (Get-Date).ToString('yyyy/MM/dd HH:mm:ss')
    }

    def_WriteJsonAtomic -Path $State.CheckpointJson -Data $checkpoint -Depth 7
}

# ====================================================================================
# def 防止重複執行與 RunDir
# ====================================================================================

function def_AcquireSingleInstanceLock {
    [CmdletBinding()]
    param()

    $lockRoot = Join-Path $env:LOCALAPPDATA 'VIA\WorkOps\locks'
    [void][IO.Directory]::CreateDirectory($lockRoot)
    $State.LockPath = Join-Path $lockRoot 'VIA_Outlook_TimeRange_ReadOnly_v003.lock'

    try {
        $State.LockStream = [IO.File]::Open(
            $State.LockPath,
            [IO.FileMode]::CreateNew,
            [IO.FileAccess]::ReadWrite,
            [IO.FileShare]::None
        )
    }
    catch [IO.IOException] {
        $existingText = ''
        try { $existingText = Get-Content -LiteralPath $State.LockPath -Raw -ErrorAction SilentlyContinue } catch {}

        $existingPid = 0
        if ($existingText -match '"PROCESS_ID"\s*:\s*(\d+)') {
            $existingPid = [int]$Matches[1]
        }

        $isActive = $false
        if ($existingPid -gt 0) {
            $isActive = $null -ne (Get-Process -Id $existingPid -ErrorAction SilentlyContinue)
        }

        if ($isActive) {
            throw "已有 VIA Outlook 唯讀掃描正在執行，PID=$existingPid。為避免重複掃描，本次安全停止。"
        }

        $stale = "$($State.LockPath).stale.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        try { Move-Item -LiteralPath $State.LockPath -Destination $stale -Force } catch {}
        $State.LockStream = [IO.File]::Open(
            $State.LockPath,
            [IO.FileMode]::CreateNew,
            [IO.FileAccess]::ReadWrite,
            [IO.FileShare]::None
        )
    }

    $lockData = [pscustomobject][ordered]@{
        PROCESS_ID = $PID
        STARTED_AT = (Get-Date).ToString('yyyy/MM/dd HH:mm:ss')
        START_TIME = $Config.StartTime.ToString('yyyy/MM/dd HH:mm:ss')
        END_TIME   = $Config.EndTime.ToString('yyyy/MM/dd HH:mm:ss')
    } | ConvertTo-Json -Depth 3

    $bytes = [Text.Encoding]::UTF8.GetBytes($lockData)
    $State.LockStream.Write($bytes, 0, $bytes.Length)
    $State.LockStream.Flush()
}

function def_ReleaseSingleInstanceLock {
    [CmdletBinding()]
    param()

    try {
        if ($null -ne $State.LockStream) {
            $State.LockStream.Dispose()
            $State.LockStream = $null
        }
    }
    catch {}

    try {
        if (-not [string]::IsNullOrWhiteSpace($State.LockPath) -and (Test-Path -LiteralPath $State.LockPath)) {
            Remove-Item -LiteralPath $State.LockPath -Force -ErrorAction SilentlyContinue
        }
    }
    catch {}
}

function def_InitializeRunDirectory {
    [CmdletBinding()]
    param()

    [void][IO.Directory]::CreateDirectory($Config.OutputRoot)

    $configBasis = @(
        $Config.StartTime.ToString('o')
        $Config.EndTime.ToString('o')
        $Config.IncludeSubfolders
        $Config.IncludeSearchFolders
        $Config.IncludePublicFolders
        $Config.IncludeMeetingItems
        $Config.IncludeBodySnippet
        $Config.BodySnippetLength
        $Config.IncludeAttachmentNames
        $Config.MaxItemsPerFolder
        $Config.SkipNonMailDefaultFolders
        $Config.GcEveryFolders
    ) -join '|'

    $runKey = (def_GetSha256Text -Text $configBasis).Substring(0, 12).ToUpperInvariant()
    $baseName = 'RUN_{0}_{1}_VIA_OUTLOOK_RO_{2}_{3}' -f `
        $Config.StartTime.ToString('yyyyMMdd_HHmmss'),
        $Config.EndTime.ToString('yyyyMMdd_HHmmss'),
        $SCRIPT_VERSION,
        $runKey

    $candidate = Join-Path $Config.OutputRoot $baseName
    $checkpointCandidate = Join-Path $candidate '05_checkpoint.json'

    $canResume = $false
    if ($Config.ResumeIncomplete -and (Test-Path -LiteralPath $checkpointCandidate)) {
        try {
            $oldCheckpoint = Get-Content -LiteralPath $checkpointCandidate -Raw | ConvertFrom-Json
            $canResume = -not [bool]$oldCheckpoint.COMPLETED
        }
        catch {
            $canResume = $false
        }
    }

    if ($canResume) {
        $State.RunDir = $candidate
    }
    elseif (Test-Path -LiteralPath $candidate) {
        $State.RunDir = "$candidate`_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    }
    else {
        $State.RunDir = $candidate
    }

    [void][IO.Directory]::CreateDirectory($State.RunDir)

    $State.MailCsv       = Join-Path $State.RunDir '01_mail_index.csv'
    $State.FolderCsv     = Join-Path $State.RunDir '02_folder_scan_audit.csv'
    $State.ErrorCsv      = Join-Path $State.RunDir '03_scan_errors.csv'
    $State.ManifestJson  = Join-Path $State.RunDir '04_run_manifest.json'
    $State.CheckpointJson = Join-Path $State.RunDir '05_checkpoint.json'
    $State.HeartbeatJson = Join-Path $State.RunDir '06_heartbeat.json'
    $State.ReportHtml    = Join-Path $State.RunDir 'VIA_Outlook_TimeRange_ReadOnly_Report.html'
    $State.AcceleratorCsv = Join-Path $State.RunDir '07_accelerator_matrix.csv'
    $State.ForgeInventoryCsv    = Join-Path $State.RunDir '08_forge_inventory.csv'
    $State.ForgeCapabilityCsv   = Join-Path $State.RunDir '09_forge_capability_command_matrix.csv'
    $State.ForgeKeywordSeedCsv  = Join-Path $State.RunDir '10_forge_keyword_seeds.csv'
    $State.ForgeRiskCsv         = Join-Path $State.RunDir '11_forge_risk_findings.csv'
    $State.ForgeActivationCsv   = Join-Path $State.RunDir '12_forge_activation_matrix.csv'
    $State.KeywordDictionaryCsv = Join-Path $State.RunDir '20_keyword_dictionary.csv'
    $State.EnrichedMailCsv      = Join-Path $State.RunDir '21_mail_enriched.csv'
    $State.ClusterCandidateCsv  = Join-Path $State.RunDir '22_mail_cluster_candidates.csv'
    $State.ProjectCandidateCsv  = Join-Path $State.RunDir '23_project_candidate_matrix_EDIT_CONFIRM.csv'
    $State.StakeholderCsv       = Join-Path $State.RunDir '24_stakeholder_matrix.csv'
    $State.PendingResponseCsv   = Join-Path $State.RunDir '25_FIRST_PRIORITY_pending_response.csv'
    $State.ProcessMiningCsv     = Join-Path $State.RunDir '26_process_mining_event_log.csv'
    $State.ControllingCsv       = Join-Path $State.RunDir '27_project_controlling_sheet.csv'
    $State.ActionRegisterCsv    = Join-Path $State.RunDir '28_action_register_EDIT_CONTROL.csv'
    $State.QualityCheckCsv      = Join-Path $State.RunDir '29_quality_check_matrix.csv'
    $State.HelperPy             = Join-Path $State.RunDir '_via_workops_local_helper.py'

    if ($canResume) {
        try {
            $checkpoint = Get-Content -LiteralPath $State.CheckpointJson -Raw | ConvertFrom-Json
            foreach ($key in @($checkpoint.COMPLETED_FOLDER_KEYS)) {
                if (-not [string]::IsNullOrWhiteSpace([string]$key)) {
                    [void]$State.CompletedFolderKeys.Add([string]$key)
                }
            }
            $State.CompletedFolderCount = [int]$checkpoint.COMPLETED_FOLDER_COUNT
            $State.SkippedFolderCount = [int]$checkpoint.SKIPPED_FOLDER_COUNT
            $State.RestrictedFolderCount = [int]$checkpoint.RESTRICTED_FOLDER_COUNT
            $State.FallbackFolderCount = [int]$checkpoint.FALLBACK_FOLDER_COUNT
            $State.ScannedItemReferenceCount = [int64]$checkpoint.SCANNED_ITEM_REFERENCE_COUNT
            $State.MatchedMailCount = [int64]$checkpoint.MATCHED_MAIL_COUNT
            $State.ErrorCount = [int]$checkpoint.ERROR_COUNT
        }
        catch {
            def_AddError -Stage 'LOAD_CHECKPOINT' -StoreName '' -FolderPath '' -Message $_.Exception.Message
        }
    }
}

# ====================================================================================
# def Outlook 連線、資料夾盤點
# ====================================================================================

function def_ConnectClassicOutlook {
    [CmdletBinding()]
    param()

    $hadOutlookProcess = @((Get-Process -Name OUTLOOK -ErrorAction SilentlyContinue)).Count -gt 0
    $outlook = $null
    $namespace = $null

    try {
        $outlook = New-Object -ComObject Outlook.Application
        $namespace = $outlook.GetNamespace('MAPI')
    }
    catch {
        def_ReleaseComObject -ComObject $namespace
        def_ReleaseComObject -ComObject $outlook
        throw '無法連線 Classic Outlook。New Outlook 不支援 Outlook COM；請先開啟 Classic Outlook 並登入。'
    }

    $State.OutlookStartedByTool = -not $hadOutlookProcess

    return [pscustomobject]@{
        OUTLOOK   = $outlook
        NAMESPACE = $namespace
    }
}

function def_IsSearchFolderPath {
    [CmdletBinding()]
    param([string]$FolderPath)

    foreach ($pattern in $SEARCH_FOLDER_PATTERNS) {
        if ($FolderPath -like "*$pattern*") { return $true }
    }
    return $false
}

function def_IsPublicStore {
    [CmdletBinding()]
    param([string]$StoreName)

    foreach ($pattern in $PUBLIC_STORE_PATTERNS) {
        if ($StoreName -like "*$pattern*") { return $true }
    }
    return $false
}

function def_AddFolderPlanRecursive {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Folder,
        [string]$StoreName,
        [string]$StoreId,
        [int]$Depth = 0
    )

    $folderName = ''
    $folderPath = ''
    $entryId = ''
    $defaultItemType = ''

    try { $folderName = def_ToSafeString -Value $Folder.Name } catch {}
    try { $folderPath = def_ToSafeString -Value $Folder.FolderPath } catch {}
    try { $entryId = def_ToSafeString -Value $Folder.EntryID } catch {}
    try { $defaultItemType = def_ToSafeString -Value $Folder.DefaultItemType } catch {}

    $skipReason = ''
    if (-not $Config.IncludeSearchFolders -and (def_IsSearchFolderPath -FolderPath $folderPath)) {
        $skipReason = 'SEARCH_FOLDER'
    }

    if ([string]::IsNullOrWhiteSpace($skipReason) -and $Config.SkipNonMailDefaultFolders) {
        # Outlook OlItemType: 0 = MailItem。空值保守保留，不做誤略過。
        if (-not [string]::IsNullOrWhiteSpace($defaultItemType) -and $defaultItemType -ne '0') {
            $skipReason = 'NON_MAIL_DEFAULT_FOLDER'
        }
    }

    $folderKey = def_GetSha256Text -Text "$StoreId|$entryId|$folderPath"

    $State.FolderPlan.Add([pscustomobject][ordered]@{
        FOLDER_KEY       = $folderKey
        STORE_NAME       = $StoreName
        STORE_ID         = $StoreId
        ENTRY_ID         = $entryId
        FOLDER_NAME      = $folderName
        FOLDER_PATH      = $folderPath
        DEPTH            = $Depth
        DEFAULT_ITEM_TYPE = $defaultItemType
        SKIP_REASON      = $skipReason
    })

    if (-not $Config.IncludeSubfolders) { return }
    # 搜尋資料夾本身可能形成虛擬樹，直接短路；非郵件資料夾仍繼續盤點其子資料夾，避免漏掉自訂郵件子資料夾。
    if ($skipReason -eq 'SEARCH_FOLDER') { return }

    $subfolders = $null
    try {
        $subfolders = $Folder.Folders
        $count = [int]$subfolders.Count

        for ($index = 1; $index -le $count; $index++) {
            $subfolder = $null
            try {
                $subfolder = $subfolders.Item($index)
                def_AddFolderPlanRecursive -Folder $subfolder -StoreName $StoreName -StoreId $StoreId -Depth ($Depth + 1)
            }
            catch {
                def_AddError -Stage 'INVENTORY_SUBFOLDER' -StoreName $StoreName -FolderPath $folderPath -Message $_.Exception.Message
            }
            finally {
                def_ReleaseComObject -ComObject $subfolder
            }
        }
    }
    catch {
        def_AddError -Stage 'INVENTORY_READ_SUBFOLDERS' -StoreName $StoreName -FolderPath $folderPath -Message $_.Exception.Message
    }
    finally {
        def_ReleaseComObject -ComObject $subfolders
    }
}

function def_BuildFolderPlan {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Namespace)

    $stores = $null

    try {
        $stores = $Namespace.Stores
        $State.StoreCount = [int]$stores.Count

        for ($storeIndex = 1; $storeIndex -le $State.StoreCount; $storeIndex++) {
            $store = $null
            $root = $null

            $inventoryPercent = 5 + [int](15 * $storeIndex / [Math]::Max(1, $State.StoreCount))
            def_ShowProgress -Percent $inventoryPercent -Stage 'INVENTORY' -Status ("Store {0}/{1}" -f $storeIndex, $State.StoreCount)
            def_WriteHeartbeat -Message ("Inventory Store {0}/{1}" -f $storeIndex, $State.StoreCount)

            try {
                $store = $stores.Item($storeIndex)
                $storeName = def_ToSafeString -Value $store.DisplayName
                $storeId = def_ToSafeString -Value $store.StoreID

                if (-not $Config.IncludePublicFolders -and (def_IsPublicStore -StoreName $storeName)) {
                    $row = [pscustomobject][ordered]@{
                        SCAN_ORDER   = 0
                        STORE_NAME   = $storeName
                        FOLDER_PATH  = ''
                        DEPTH        = 0
                        METHOD       = 'SKIPPED_PUBLIC_STORE'
                        ITEM_COUNT   = 0
                        MATCHED      = 0
                        DURATION_MS  = 0
                        STATUS       = 'SKIPPED'
                        COMPLETED_AT = (Get-Date).ToString('yyyy/MM/dd HH:mm:ss')
                    }
                    def_AppendCsvUtf8 -Rows @($row) -Path $State.FolderCsv
                    $State.SkippedFolderCount++
                    continue
                }

                $root = $store.GetRootFolder()
                def_AddFolderPlanRecursive -Folder $root -StoreName $storeName -StoreId $storeId -Depth 0
            }
            catch {
                $storeNameForError = ''
                try { $storeNameForError = def_ToSafeString -Value $store.DisplayName } catch {}
                def_AddError -Stage 'INVENTORY_STORE' -StoreName $storeNameForError -FolderPath '' -Message $_.Exception.Message
            }
            finally {
                def_ReleaseComObject -ComObject $root
                def_ReleaseComObject -ComObject $store
                def_FlushErrors
            }
        }
    }
    finally {
        def_ReleaseComObject -ComObject $stores
    }

    $State.PlannedFolderCount = $State.FolderPlan.Count
}

# ====================================================================================
# def 郵件讀取
# ====================================================================================

function def_GetMailTiming {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Item)

    $isSent = $false
    try { $isSent = [bool]$Item.Sent } catch {}

    $receivedTime = $null
    $sentTime = $null
    $creationTime = $null
    $modifiedTime = $null

    try { $receivedTime = def_GetDateValue -Value $Item.ReceivedTime } catch {}
    try { $sentTime = def_GetDateValue -Value $Item.SentOn } catch {}
    try { $creationTime = def_GetDateValue -Value $Item.CreationTime } catch {}
    try { $modifiedTime = def_GetDateValue -Value $Item.LastModificationTime } catch {}

    $eventTime = $null
    $direction = 'UNKNOWN'

    if ($isSent -and $null -ne $sentTime) {
        $eventTime = $sentTime
        $direction = 'OUTBOUND'
    }
    elseif ($null -ne $receivedTime) {
        $eventTime = $receivedTime
        $direction = 'INBOUND'
    }
    elseif ($null -ne $sentTime) {
        $eventTime = $sentTime
        $direction = 'OUTBOUND'
    }
    elseif ($null -ne $creationTime) {
        $eventTime = $creationTime
        $direction = 'DRAFT_OR_LOCAL'
    }

    return [pscustomobject]@{
        EVENT_TIME    = $eventTime
        DIRECTION     = $direction
        RECEIVED_TIME = $receivedTime
        SENT_TIME     = $sentTime
        CREATION_TIME = $creationTime
        MODIFIED_TIME = $modifiedTime
    }
}

function def_IsSupportedItem {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Item)

    try {
        $itemClass = [int]$Item.Class
        if ($itemClass -eq $MAIL_ITEM_CLASS) { return $true }
        if ($Config.IncludeMeetingItems -and ($MEETING_ITEM_CLASSES -contains $itemClass)) { return $true }
    }
    catch {}
    return $false
}

function def_GetItemTypeName {
    [CmdletBinding()]
    param([int]$ItemClass)

    if ($ItemClass -eq $MAIL_ITEM_CLASS) { return 'MAIL' }

    switch ($ItemClass) {
        53 { return 'MEETING_REQUEST' }
        54 { return 'MEETING_CANCELLATION' }
        55 { return 'MEETING_RESPONSE_DECLINED' }
        56 { return 'MEETING_RESPONSE_ACCEPTED' }
        57 { return 'MEETING_RESPONSE_TENTATIVE' }
        default { return "CLASS_$ItemClass" }
    }
}

function def_GetInternetMessageId {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Item)

    $accessor = $null
    try {
        $accessor = $Item.PropertyAccessor
        foreach ($propertyName in $INTERNET_MESSAGE_ID_PROPS) {
            try {
                $value = def_ToSafeString -Value $accessor.GetProperty($propertyName)
                if (-not [string]::IsNullOrWhiteSpace($value)) { return $value.Trim() }
            }
            catch {}
        }
    }
    catch {}
    finally {
        def_ReleaseComObject -ComObject $accessor
    }

    return ''
}

function def_GetAttachmentInfo {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Item)

    $attachments = $null
    $names = [System.Collections.Generic.List[string]]::new()
    $count = 0

    try {
        $attachments = $Item.Attachments
        $count = [int]$attachments.Count

        if ($Config.IncludeAttachmentNames -and $count -gt 0) {
            for ($index = 1; $index -le $count; $index++) {
                $attachment = $null
                try {
                    $attachment = $attachments.Item($index)
                    $name = def_NormalizeSingleLine -Text (def_ToSafeString -Value $attachment.FileName) -MaxLength 260
                    if (-not [string]::IsNullOrWhiteSpace($name)) { $names.Add($name) }
                }
                catch {}
                finally {
                    def_ReleaseComObject -ComObject $attachment
                }
            }
        }
    }
    catch {}
    finally {
        def_ReleaseComObject -ComObject $attachments
    }

    return [pscustomobject]@{
        COUNT = $count
        NAMES = ($names -join ' | ')
    }
}

function def_GetItemKey {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Item,
        [string]$StoreId,
        [string]$FolderPath
    )

    $entryId = ''
    try { $entryId = def_ToSafeString -Value $Item.EntryID } catch {}

    if (-not [string]::IsNullOrWhiteSpace($entryId)) {
        return "$StoreId|$entryId"
    }

    $subject = ''
    $size = ''
    $creation = ''
    try { $subject = def_ToSafeString -Value $Item.Subject } catch {}
    try { $size = def_ToSafeString -Value $Item.Size } catch {}
    try { $creation = ([datetime]$Item.CreationTime).ToString('o') } catch {}

    return def_GetSha256Text -Text "$StoreId|$FolderPath|$subject|$size|$creation"
}

function def_ProcessItem {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Item,
        [Parameter(Mandatory)]$FolderMeta,
        [Parameter(Mandatory)]$FolderRows
    )

    $State.ScannedItemReferenceCount++
    $State.CurrentFolderItemIndex++

    if (($State.CurrentFolderItemIndex % $Config.HeartbeatEveryItems) -eq 0) {
        def_WriteHeartbeat -Message 'Scanning folder items'
        $folderBase = if ($State.PlannedFolderCount -gt 0) {
            20 + [int](55 * $State.CurrentFolderIndex / $State.PlannedFolderCount)
        }
        else { 20 }
        def_ShowProgress -Percent ([Math]::Min(75, $folderBase)) -Stage 'SCAN' -Status $FolderMeta.FOLDER_PATH
    }

    if (-not (def_IsSupportedItem -Item $Item)) { return }

    $timing = def_GetMailTiming -Item $Item
    if ($null -eq $timing.EVENT_TIME) { return }
    if ($timing.EVENT_TIME -lt $Config.StartTime -or $timing.EVENT_TIME -gt $Config.EndTime) { return }

    $itemKey = def_GetItemKey -Item $Item -StoreId $FolderMeta.STORE_ID -FolderPath $FolderMeta.FOLDER_PATH
    if (-not $State.SeenItemKeys.Add($itemKey)) { return }

    $subject = ''
    $senderName = ''
    $senderAddress = ''
    $toText = ''
    $ccText = ''
    $categories = ''
    $messageClass = ''
    $entryId = ''
    $conversationId = ''
    $conversationTopic = ''
    $unread = $null
    $flagStatus = ''
    $importance = ''
    $sizeBytes = 0L
    $bodySnippet = ''

    try { $subject = def_NormalizeSingleLine -Text (def_ToSafeString -Value $Item.Subject) -MaxLength 1000 } catch {}
    try { $senderName = def_NormalizeSingleLine -Text (def_ToSafeString -Value $Item.SenderName) -MaxLength 500 } catch {}
    try { $senderAddress = def_NormalizeSingleLine -Text (def_ToSafeString -Value $Item.SenderEmailAddress) -MaxLength 500 } catch {}
    try { $toText = def_NormalizeSingleLine -Text (def_ToSafeString -Value $Item.To) -MaxLength 4000 } catch {}
    try { $ccText = def_NormalizeSingleLine -Text (def_ToSafeString -Value $Item.CC) -MaxLength 4000 } catch {}
    try { $categories = def_NormalizeSingleLine -Text (def_ToSafeString -Value $Item.Categories) -MaxLength 1000 } catch {}
    try { $messageClass = def_ToSafeString -Value $Item.MessageClass } catch {}
    try { $entryId = def_ToSafeString -Value $Item.EntryID } catch {}
    try { $conversationId = def_ToSafeString -Value $Item.ConversationID } catch {}
    try { $conversationTopic = def_NormalizeSingleLine -Text (def_ToSafeString -Value $Item.ConversationTopic) -MaxLength 1000 } catch {}
    try { $unread = [bool]$Item.UnRead } catch {}
    try { $flagStatus = def_ToSafeString -Value $Item.FlagStatus } catch {}
    try { $importance = def_ToSafeString -Value $Item.Importance } catch {}
    try { $sizeBytes = [int64]$Item.Size } catch {}

    if ($Config.IncludeBodySnippet) {
        try {
            $bodySnippet = def_NormalizeSingleLine -Text (def_ToSafeString -Value $Item.Body) -MaxLength $Config.BodySnippetLength
        }
        catch {}
    }

    $attachmentInfo = def_GetAttachmentInfo -Item $Item
    $internetMessageId = def_GetInternetMessageId -Item $Item
    $readStatus = if ($null -eq $unread) { 'UNKNOWN' } elseif ($unread) { 'UNREAD' } else { 'READ' }

    $mailKeyBasis = if (-not [string]::IsNullOrWhiteSpace($internetMessageId)) {
        "IMID|$internetMessageId"
    }
    else {
        "$senderAddress|$($timing.EVENT_TIME.ToString('o'))|$subject|$sizeBytes|$conversationId"
    }

    $itemClassValue = 0
    try { $itemClassValue = [int]$Item.Class } catch {}

    $FolderRows.Add([pscustomobject][ordered]@{
        TIME                   = $timing.EVENT_TIME.ToString('yyyy/MM/dd HH:mm:ss')
        DIRECTION              = $timing.DIRECTION
        ITEM_TYPE              = def_GetItemTypeName -ItemClass $itemClassValue
        TITLE                  = $subject
        FROM                   = $senderName
        FROM_ADDRESS           = $senderAddress
        TO                     = $toText
        CC                     = $ccText
        READ_STATUS            = $readStatus
        IMPORTANCE             = $importance
        FLAG_STATUS            = $flagStatus
        CATEGORIES             = $categories
        ATTACHMENT_COUNT       = $attachmentInfo.COUNT
        ATTACHMENT_NAMES       = $attachmentInfo.NAMES
        BODY_SNIPPET           = $bodySnippet
        STORE_NAME             = $FolderMeta.STORE_NAME
        FOLDER_NAME            = $FolderMeta.FOLDER_NAME
        FOLDER_PATH            = $FolderMeta.FOLDER_PATH
        MESSAGE_CLASS          = $messageClass
        CONVERSATION_TOPIC     = $conversationTopic
        CONVERSATION_ID        = $conversationId
        INTERNET_MESSAGE_ID    = $internetMessageId
        MAIL_FINGERPRINT       = def_GetSha256Text -Text $mailKeyBasis
        ENTRY_ID               = $entryId
        STORE_ID               = $FolderMeta.STORE_ID
        SIZE_BYTES             = $sizeBytes
        RECEIVED_TIME          = if ($null -ne $timing.RECEIVED_TIME) { $timing.RECEIVED_TIME.ToString('yyyy/MM/dd HH:mm:ss') } else { '' }
        SENT_TIME              = if ($null -ne $timing.SENT_TIME) { $timing.SENT_TIME.ToString('yyyy/MM/dd HH:mm:ss') } else { '' }
        CREATION_TIME          = if ($null -ne $timing.CREATION_TIME) { $timing.CREATION_TIME.ToString('yyyy/MM/dd HH:mm:ss') } else { '' }
        LAST_MODIFICATION_TIME = if ($null -ne $timing.MODIFIED_TIME) { $timing.MODIFIED_TIME.ToString('yyyy/MM/dd HH:mm:ss') } else { '' }
        SOURCE_READ_ONLY       = $true
    })
}

function def_GetRestrictDateText {
    [CmdletBinding()]
    param([datetime]$Value)

    return $Value.ToString('g', [Globalization.CultureInfo]::CurrentCulture)
}

function def_ScanFolderByRestrict {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Folder,
        [Parameter(Mandatory)]$FolderMeta
    )

    $items = $null
    $folderRows = [System.Collections.Generic.List[object]]::new()
    $restrictSucceeded = $false
    $itemCount = 0

    try {
        $items = $Folder.Items
        $itemCount = [int]$items.Count

        if ($itemCount -le 0) {
            return [pscustomobject]@{
                SUCCESS = $true
                METHOD = 'EMPTY'
                ITEM_COUNT = 0
                MATCHED = 0
                ROWS = @()
            }
        }

        $startText = def_GetRestrictDateText -Value $Config.StartTime
        $endText = def_GetRestrictDateText -Value $Config.EndTime

        $filters = @(
            "[ReceivedTime] >= '$startText' AND [ReceivedTime] <= '$endText'",
            "[SentOn] >= '$startText' AND [SentOn] <= '$endText'",
            "[CreationTime] >= '$startText' AND [CreationTime] <= '$endText'"
        )

        foreach ($filter in $filters) {
            $filteredItems = $null

            try {
                $filteredItems = $items.Restrict($filter)
                $restrictSucceeded = $true
                $filteredCount = [int]$filteredItems.Count
                $limit = if ($Config.MaxItemsPerFolder -gt 0) {
                    [Math]::Min($filteredCount, $Config.MaxItemsPerFolder)
                }
                else {
                    $filteredCount
                }

                $State.CurrentFolderItemTotal += $limit

                for ($index = 1; $index -le $limit; $index++) {
                    $item = $null
                    try {
                        $item = $filteredItems.Item($index)
                        def_ProcessItem -Item $item -FolderMeta $FolderMeta -FolderRows $folderRows
                    }
                    catch {
                        def_AddError -Stage 'PROCESS_RESTRICTED_ITEM' `
                            -StoreName $FolderMeta.STORE_NAME `
                            -FolderPath $FolderMeta.FOLDER_PATH `
                            -Message $_.Exception.Message
                    }
                    finally {
                        def_ReleaseComObject -ComObject $item
                    }
                }
            }
            catch {
                def_AddError -Stage 'RESTRICT_FILTER' `
                    -StoreName $FolderMeta.STORE_NAME `
                    -FolderPath $FolderMeta.FOLDER_PATH `
                    -Message ("Filter: {0}; Error: {1}" -f $filter, $_.Exception.Message)
            }
            finally {
                def_ReleaseComObject -ComObject $filteredItems
            }
        }

        if (-not $restrictSucceeded) {
            return [pscustomobject]@{
                SUCCESS = $false
                METHOD = 'RESTRICT_FAILED'
                ITEM_COUNT = $itemCount
                MATCHED = $folderRows.Count
                ROWS = @($folderRows)
            }
        }

        return [pscustomobject]@{
            SUCCESS = $true
            METHOD = 'RESTRICT'
            ITEM_COUNT = $itemCount
            MATCHED = $folderRows.Count
            ROWS = @($folderRows)
        }
    }
    finally {
        def_ReleaseComObject -ComObject $items
    }
}

function def_ScanFolderByIteration {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Folder,
        [Parameter(Mandatory)]$FolderMeta
    )

    $items = $null
    $folderRows = [System.Collections.Generic.List[object]]::new()
    $itemCount = 0

    try {
        $items = $Folder.Items
        $itemCount = [int]$items.Count

        $limit = if ($Config.MaxItemsPerFolder -gt 0) {
            [Math]::Min($itemCount, $Config.MaxItemsPerFolder)
        }
        else {
            $itemCount
        }

        $State.CurrentFolderItemTotal = $limit

        for ($index = 1; $index -le $limit; $index++) {
            $item = $null
            try {
                $item = $items.Item($index)
                def_ProcessItem -Item $item -FolderMeta $FolderMeta -FolderRows $folderRows
            }
            catch {
                def_AddError -Stage 'PROCESS_ITERATED_ITEM' `
                    -StoreName $FolderMeta.STORE_NAME `
                    -FolderPath $FolderMeta.FOLDER_PATH `
                    -Message $_.Exception.Message
            }
            finally {
                def_ReleaseComObject -ComObject $item
            }
        }

        return [pscustomobject]@{
            SUCCESS = $true
            METHOD = 'FULL_ITERATION'
            ITEM_COUNT = $itemCount
            MATCHED = $folderRows.Count
            ROWS = @($folderRows)
        }
    }
    finally {
        def_ReleaseComObject -ComObject $items
    }
}

function def_ScanFolderPlan {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Namespace)

    $scanOrder = 0

    foreach ($folderMeta in @($State.FolderPlan)) {
        $scanOrder++
        $State.CurrentFolderIndex = $scanOrder
        $State.CurrentStore = $folderMeta.STORE_NAME
        $State.CurrentFolder = $folderMeta.FOLDER_PATH
        $State.CurrentFolderItemIndex = 0
        $State.CurrentFolderItemTotal = 0

        if ($State.CompletedFolderKeys.Contains($folderMeta.FOLDER_KEY)) {
            continue
        }

        $percent = 20 + [int](55 * $scanOrder / [Math]::Max(1, $State.PlannedFolderCount))
        def_ShowProgress -Percent ([Math]::Min(75, $percent)) -Stage 'SCAN' -Status $folderMeta.FOLDER_PATH
        def_WriteHeartbeat -Message ("Folder {0}/{1}" -f $scanOrder, $State.PlannedFolderCount)

        if (-not [string]::IsNullOrWhiteSpace($folderMeta.SKIP_REASON)) {
            $skipRow = [pscustomobject][ordered]@{
                SCAN_ORDER   = $scanOrder
                STORE_NAME   = $folderMeta.STORE_NAME
                FOLDER_PATH  = $folderMeta.FOLDER_PATH
                DEPTH        = $folderMeta.DEPTH
                METHOD       = "SKIPPED_$($folderMeta.SKIP_REASON)"
                ITEM_COUNT   = 0
                MATCHED      = 0
                DURATION_MS  = 0
                STATUS       = 'SKIPPED'
                COMPLETED_AT = (Get-Date).ToString('yyyy/MM/dd HH:mm:ss')
            }

            def_AppendCsvUtf8 -Rows @($skipRow) -Path $State.FolderCsv
            $State.SkippedFolderCount++
            $State.CompletedFolderCount++
            [void]$State.CompletedFolderKeys.Add($folderMeta.FOLDER_KEY)
            def_WriteCheckpoint -Completed $false -Message 'Folder skipped safely'
            continue
        }

        $folder = $null
        $timer = [Diagnostics.Stopwatch]::StartNew()
        $result = $null
        $status = 'OK'

        try {
            $folder = $Namespace.GetFolderFromID($folderMeta.ENTRY_ID, $folderMeta.STORE_ID)

            if ($Config.UseRestrict) {
                $result = def_ScanFolderByRestrict -Folder $folder -FolderMeta $folderMeta

                if ($result.SUCCESS) {
                    if ($result.METHOD -eq 'RESTRICT') {
                        $State.RestrictedFolderCount++
                    }
                }
                else {
                    $State.FallbackFolderCount++
                    # Restrict 完全失敗才使用逐項後備。先前 Restrict 的列透過 SeenItemKeys 避免重複。
                    $result = def_ScanFolderByIteration -Folder $folder -FolderMeta $folderMeta
                }
            }
            else {
                $State.FallbackFolderCount++
                $result = def_ScanFolderByIteration -Folder $folder -FolderMeta $folderMeta
            }

            if ($null -ne $result -and @($result.ROWS).Count -gt 0) {
                def_AppendCsvUtf8 -Rows @($result.ROWS) -Path $State.MailCsv
                $State.MatchedMailCount += @($result.ROWS).Count
            }
        }
        catch {
            $status = 'ERROR_CONTINUED'
            def_AddError -Stage 'SCAN_FOLDER' `
                -StoreName $folderMeta.STORE_NAME `
                -FolderPath $folderMeta.FOLDER_PATH `
                -Message $_.Exception.Message

            if ($null -eq $result) {
                $result = [pscustomobject]@{
                    METHOD = 'ERROR'
                    ITEM_COUNT = 0
                    MATCHED = 0
                    ROWS = @()
                }
            }
        }
        finally {
            $timer.Stop()
            def_ReleaseComObject -ComObject $folder

            $auditRow = [pscustomobject][ordered]@{
                SCAN_ORDER   = $scanOrder
                STORE_NAME   = $folderMeta.STORE_NAME
                FOLDER_PATH  = $folderMeta.FOLDER_PATH
                DEPTH        = $folderMeta.DEPTH
                METHOD       = if ($null -ne $result) { $result.METHOD } else { 'ERROR' }
                ITEM_COUNT   = if ($null -ne $result) { $result.ITEM_COUNT } else { 0 }
                MATCHED      = if ($null -ne $result) { $result.MATCHED } else { 0 }
                DURATION_MS  = $timer.ElapsedMilliseconds
                STATUS       = $status
                COMPLETED_AT = (Get-Date).ToString('yyyy/MM/dd HH:mm:ss')
            }

            def_AppendCsvUtf8 -Rows @($auditRow) -Path $State.FolderCsv
            def_FlushErrors

            $State.CompletedFolderCount++
            [void]$State.CompletedFolderKeys.Add($folderMeta.FOLDER_KEY)

            def_WriteCheckpoint -Completed $false -Message ("Completed folder {0}/{1}" -f $scanOrder, $State.PlannedFolderCount)
            def_WriteHeartbeat -Message ("Completed folder {0}/{1}" -f $scanOrder, $State.PlannedFolderCount)

            if ($Config.GcEveryFolders -gt 0 -and ($State.CompletedFolderCount % $Config.GcEveryFolders) -eq 0) {
                [GC]::Collect()
                [GC]::WaitForPendingFinalizers()
            }
        }
    }
}

# ====================================================================================
# def VIA Forge 靜態整合與本機郵件智慧分析
# ====================================================================================

function def_ResolveForgeRoot {
    [CmdletBinding()]
    param()

    $candidates = [System.Collections.Generic.List[string]]::new()
    if (-not [string]::IsNullOrWhiteSpace($Config.ForgeRootHint)) { $candidates.Add($Config.ForgeRootHint) }

    if ($Config.AutoFindForgeRoot) {
        $downloads = Join-Path $env:USERPROFILE 'Downloads'
        try {
            Get-ChildItem -LiteralPath $downloads -Directory -Filter 'VIA_Forge*' -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending |
                ForEach-Object {
                    $direct = Join-Path $_.FullName 'VIA_Forge'
                    if (Test-Path -LiteralPath $direct -PathType Container) { $candidates.Add($direct) }
                    elseif (Test-Path -LiteralPath (Join-Path $_.FullName 'via_forge.py') -PathType Leaf) { $candidates.Add($_.FullName) }
                }
        } catch {}
    }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Container) { return (Resolve-Path -LiteralPath $candidate).Path }
    }
    return ''
}

function def_ResolvePythonExe {
    [CmdletBinding()]
    param([string]$ForgeRoot)

    $candidates = [System.Collections.Generic.List[string]]::new()
    if (-not [string]::IsNullOrWhiteSpace($ForgeRoot)) {
        $candidates.Add((Join-Path $ForgeRoot '.venv\Scripts\python.exe'))
        $candidates.Add((Join-Path $ForgeRoot '.venv\Scripts\python3.exe'))
    }
    $candidates.Add('C:\Python313\python.exe')
    foreach ($path in $candidates) { if (Test-Path -LiteralPath $path -PathType Leaf) { return $path } }
    foreach ($name in @('python','python3','py')) {
        try { $cmd = Get-Command $name -ErrorAction Stop | Select-Object -First 1; if ($null -ne $cmd) { return $cmd.Source } } catch {}
    }
    return ''
}

function def_WriteLocalPythonHelper {
    [CmdletBinding()]
    param()

    $helperBase64 = 'ZnJvbSBfX2Z1dHVyZV9fIGltcG9ydCBhbm5vdGF0aW9ucwppbXBvcnQgYXJncGFyc2UsIGFzdCwgY3N2LCBoYXNobGliLCBtYXRoLCByZQpmcm9tIGNvbGxlY3Rpb25zIGltcG9ydCBDb3VudGVyLCBkZWZhdWx0ZGljdApmcm9tIGRhdGV0aW1lIGltcG9ydCBkYXRldGltZQpmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgKClJPTEVfTUFQID0gewogICAgInZpYV9zZXJ2ZXIucHkiOiAoIkxPQ0FMX1VJX1NFUlZFUiIsICJSZWdpc3RlciBsb2NhbCBVSSBjYXBhYmlsaXR5IG9ubHk7IGRvIG5vdCBhdXRvLXN0YXJ0LiIpLAogICAgInZpYV9zaWduYWwucHkiOiAoIldPUktfU0lHTkFMIiwgIlN1cHBseSB1cmdlbmN5LCByaXNrIGFuZCByZXNwb25zZSBzaWduYWwgdm9jYWJ1bGFyeS4iKSwKICAgICJ2aWFfc2luay5weSI6ICgiUlVOX0xPQ0FMX1NJTksiLCAiU3VwcGx5IHJ1bi1sb2NhbCBvdXRwdXQgYW5kIHNpbmsgdm9jYWJ1bGFyeS4iKSwKICAgICJ2aWFfc3RhdHVzLnB5IjogKCJTVEFUVVNfTU9ERUwiLCAiU3VwcGx5IHN0YXR1cyB0YXhvbm9teS4iKSwKICAgICJ2aWFfYWNjZWwucHkiOiAoIkFDQ0VMRVJBVE9SX1JFR0lTVFJZIiwgIkNyb3NzLWNoZWNrIGFjY2VsZXJhdG9yIHZvY2FidWxhcnkuIiksCiAgICAidmlhX2NoZWNrbWF0cml4LnB5IjogKCJRVUFMSVRZX0dBVEUiLCAiU3VwcGx5IHF1YWxpdHktY2hlY2sgY29uY2VwdHMuIiksCiAgICAidmlhX2Nvbm5lY3QucHkiOiAoIkNPTk5FQ1RJVklUWV9JTlZFTlRPUlkiLCAiSW52ZW50b3J5IGNvbm5lY3RvciBkZWNsYXJhdGlvbnMgb25seS4iKSwKICAgICJ2aWFfZGF0YWZvcmdlLnB5IjogKCJEQVRBX05PUk1BTElaQVRJT04iLCAiU3VwcGx5IG5vcm1hbGl6YXRpb24gdm9jYWJ1bGFyeS4iKSwKICAgICJ2aWFfZm9yZ2UucHkiOiAoIk9SQ0hFU1RSQVRPUiIsICJTdXBwbHkgb3JjaGVzdHJhdGlvbiB2b2NhYnVsYXJ5IHdpdGhvdXQgaW1wb3J0aW5nIHRhcmdldC4iKSwKICAgICJ2aWFfaW5zaWdodC5weSI6ICgiSU5TSUdIVF9FTkdJTkUiLCAiU3VwcGx5IGluc2lnaHQgYW5kIGtleXdvcmQgdm9jYWJ1bGFyeS4iKSwKICAgICJ2aWFfbWFpbGZvcmdlLnB5IjogKCJNQUlMX0lOVEVMTElHRU5DRSIsICJTdXBwbHkgbWFpbCBleHRyYWN0aW9uIGFuZCBjbGFzc2lmaWNhdGlvbiB2b2NhYnVsYXJ5LiIpLAogICAgInZpYV9tYWlsaHViLnB5IjogKCJNQUlMX0hVQiIsICJTdXBwbHkgbWFpbGJveCBhbmQgdGhyZWFkLWdyb3VwaW5nIHZvY2FidWxhcnkuIiksCiAgICAidmlhX21hbmFnZXIucHkiOiAoIk1BTkFHRU1FTlRfQ09OVFJPTCIsICJTdXBwbHkgZ292ZXJuYW5jZSBhbmQgbWFuYWdlciB2b2NhYnVsYXJ5LiIpLAogICAgInZpYV9vcHMucHkiOiAoIk9QRVJBVElPTlMiLCAiU3VwcGx5IGRhaWx5IG9wZXJhdGlvbnMgYW5kIHdvcmstY29udHJvbCB2b2NhYnVsYXJ5LiIpLAogICAgInZpYV9wYW5vcmFtYS5weSI6ICgiUEFOT1JBTUFfU1RBVElDX0FVRElUIiwgIlN1cHBseSBzdGF0aWMgaW52ZW50b3J5IGFuZCByaXNrIGNvbmNlcHRzLiIpLAogICAgInZpYV9wZW5kaW5nLnB5IjogKCJQRU5ESU5HX1JFU1BPTlNFIiwgIlN1cHBseSBwZW5kaW5nLXJlc3BvbnNlIGFuZCBmb2xsb3ctdXAgdm9jYWJ1bGFyeS4iKSwKICAgICJ2aWFfcG1pbmUucHkiOiAoIlBST0NFU1NfTUlOSU5HIiwgIlN1cHBseSBwcm9jZXNzLW1pbmluZyBldmVudCBzY2hlbWEgdm9jYWJ1bGFyeS4iKSwKICAgICJ2aWFfcHJvamVjdC5weSI6ICgiUFJPSkVDVF9DT05UUk9MIiwgIlN1cHBseSBwcm9qZWN0IGFuZCBjb250cm9sbGluZy1zaGVldCB2b2NhYnVsYXJ5LiIpLAogICAgInZpYV9yZWJ1aWxkLnB5IjogKCJSRUJVSUxEX01VVEFUSU9OX1JJU0siLCAiQmxvY2tlZCBmcm9tIGF1dG9tYXRpYyBleGVjdXRpb247IHN0YXRpYyBhdWRpdCBvbmx5LiIpLAogICAgImFjdGl2YXRlLnBzMSI6ICgiQUNUSVZBVElPTl9FTlRSWSIsICJCbG9ja2VkIGZyb20gYXV0b21hdGljIGV4ZWN1dGlvbiBpbiByZWFkLW9ubHkgd29ya2Zsb3cuIiksCiAgICAiU3RhcnQtVklBLnBzMSI6ICgiQUNUSVZBVElPTl9FTlRSWSIsICJCbG9ja2VkIGZyb20gYXV0b21hdGljIGV4ZWN1dGlvbiBpbiByZWFkLW9ubHkgd29ya2Zsb3cuIiksCiAgICAiVklBX0ZvcmdlX0xhdW5jaGVyLnBzMSI6ICgiQUNUSVZBVElPTl9FTlRSWSIsICJCbG9ja2VkIGZyb20gYXV0b21hdGljIGV4ZWN1dGlvbiBpbiByZWFkLW9ubHkgd29ya2Zsb3cuIiksCiAgICAiSW52b2tlLVZJQS1TdXBwb3J0aXZlQ29yZS1Qcm9tcHRJbmplY3Rpb24ucHMxIjogKCJQUk9NUFRfSU5KRUNUSU9OX0VOVFJZIiwgIlN0YXRpYyBhdWRpdCBvbmx5OyBubyBkb3Qtc291cmNlLiIpLAogICAgImdvdmVybmFuY2UuYmF0IjogKCJHT1ZFUk5BTkNFX0VOVFJZIiwgIlN0YXRpYyBhdWRpdCBvbmx5LiIpLAogICAgImFjdGl2YXRlLmJhdCI6ICgiQUNUSVZBVElPTl9FTlRSWSIsICJTdGF0aWMgYXVkaXQgb25seS4iKSwKICAgICJWSUFfVmlzdWFsTG9ja19UZW1wbGF0ZS5odG1sIjogKCJWSVNVQUxfTE9DSyIsICJTdXBwbHkgVUkgdm9jYWJ1bGFyeSBvbmx5LiIpLAogICAgInZpc3VhbF9sb2NrLmNzcyI6ICgiVklTVUFMX0xPQ0siLCAiU3VwcGx5IFVJIHZvY2FidWxhcnkgb25seS4iKSwKICAgICJWSUFfQ2hlY2tNYXRyaXguaHRtbCI6ICgiUVVBTElUWV9VSSIsICJTdXBwbHkgcmVwb3J0IHZvY2FidWxhcnkgb25seS4iKSwKICAgICJSRUFETUUubWQiOiAoIkRPQ1VNRU5UQVRJT04iLCAiU3VwcGx5IGRvY3VtZW50ZWQgdm9jYWJ1bGFyeSBhbmQgZGVjbGFyZWQgY29tbWFuZHMuIiksCiAgICAidmlhX2ZvcmdlX2NvbmZpZy5qc29uIjogKCJDT05GSUdfU1NPVCIsICJSZWFkIGNvbmZpZ3VyYXRpb24ga2V5cyBvbmx5LiIpLAogICAgInZpYV9mb3JnZV9yZWdpc3RyeS5qc29uIjogKCJSRUdJU1RSWV9TU09UIiwgIlJlYWQgcmVnaXN0cnkga2V5cyBvbmx5LiIpLAp9CgpSSVNLX1dPUkRTID0gewogICAgImRlbGV0ZSI6ICJERUxFVEUiLCAicmVtb3ZlLWl0ZW0iOiAiREVMRVRFIiwgInVubGluayI6ICJERUxFVEUiLCAicm10cmVlIjogIkRFTEVURSIsCiAgICAibW92ZS1pdGVtIjogIk1PVkUiLCAicmVuYW1lLWl0ZW0iOiAiUkVOQU1FIiwgInJlZ2lzdHJ5IjogIlJFR0lTVFJZIiwgInJlZy5leGUiOiAiUkVHSVNUUlkiLAogICAgInN1YnByb2Nlc3MiOiAiUFJPQ0VTUyIsICJwb3BlbiI6ICJQUk9DRVNTIiwgInN0YXJ0LXByb2Nlc3MiOiAiUFJPQ0VTUyIsICJvcy5zeXN0ZW0iOiAiUFJPQ0VTUyIsCiAgICAicmVxdWVzdHMiOiAiTkVUV09SSyIsICJ1cmxsaWIiOiAiTkVUV09SSyIsICJzb2NrZXQiOiAiTkVUV09SSyIsICJodHRweCI6ICJORVRXT1JLIiwKICAgICJzYXZlYXNmaWxlIjogIkFUVEFDSE1FTlRfV1JJVEUiLCAiZGlzcGF0Y2giOiAiQ09NX09SX0FVVE9NQVRJT04iLAogICAgImltcG9ydC1tb2R1bGUiOiAiTU9EVUxFX0xPQUQiLCAiaW52b2tlLWV4cHJlc3Npb24iOiAiRFlOQU1JQ19FWEVDIiwKICAgICJleGVjKCI6ICJEWU5BTUlDX0VYRUMiLCAiZXZhbCgiOiAiRFlOQU1JQ19FWEVDIiwgInJlYnVpbGQiOiAiTVVUQVRJT04iCn0KU0FGRV9FWFRTID0geycucHknLCcucHMxJywnLmJhdCcsJy5jbWQnLCcuanNvbicsJy5tZCcsJy50eHQnLCcuaHRtbCcsJy5jc3MnLCcuanMnLCcuanN4JywnLnRzJywnLnRzeCcsJy55YW1sJywnLnltbCcsJy50b21sJywnLmluaScsJy5jZmcnfQpUT0tFTl9SRSA9IHJlLmNvbXBpbGUociJbQS1aYS16XVtBLVphLXowLTlfLlwtL117Mix9fFtcdTRlMDAtXHU5ZmZmXXsyLDEwfSIpCkNMSV9PUFRfUkUgPSByZS5jb21waWxlKHIiKD88IVx3KS0tW2EtekEtWjAtOV1bYS16QS1aMC05Xy1dKiIpCgpTVE9QV09SRFMgPSBzZXQoInRoZSBhbmQgZm9yIHdpdGggZnJvbSB0aGlzIHRoYXQgYXJlIHdhcyB3ZXJlIGhhdmUgaGFzIGhhZCB3aWxsIHdvdWxkIHNob3VsZCBjb3VsZCBjYW4gbWF5IG1pZ2h0IGludG8gb250byBhYm91dCBhYm92ZSBiZWxvdyBhZnRlciBiZWZvcmUgYmV0d2VlbiB0aHJvdWdoIGR1cmluZyB3aXRob3V0IHdpdGhpbiB5b3VyIHlvdSBvdXIgdGhlaXIgdGhleSB0aGVtIGhpcyBoZXIgaXRzIG5vdCB5ZXMgbm8gcmUgZncgZndkIHJlcGx5IGZvcndhcmQgc3ViamVjdCBvcmlnaW5hbCBtZXNzYWdlIHNlbnQgZGF0ZSB0aW1lIGRlYXIgaGVsbG8gaGkgdGhhbmtzIHRoYW5rIHBsZWFzZSByZWdhcmRzIGJlc3QgYXR0YWNoZWQgYXR0YWNobWVudCBlbWFpbCBtYWlsIHZpYSB3b3Jrb3BzIHZpYWZvcmdlIGRlZiB0cnVlIGZhbHNlIG5vbmUgbnVsbCBnZXQgc2V0IHVzZSB1c2luZyB1c2VkIGZ1bmN0aW9uIGNsYXNzIHJldHVybiBpbXBvcnQgc2VsZiBhcmdzIGt3YXJncyBkYXRhIGZpbGUgcGF0aCBvdXRwdXQgaW5wdXQgcmVzdWx0IHN0YXR1cyB2YWx1ZSBuYW1lIHR5cGUgaXRlbSBpdGVtcyBsaXN0IGRpY3Qgc3RyaW5nIGludCBmbG9hdCBib29sIG9wZW4gY2xvc2Ugc3RhcnQgZW5kIHJ1biBtYWluIGh0bWwgY3NzIGpzb24gY3N2IHB5IHBzMSBiYXQgY21kIGNvbSBvdXRsb29rIG1lZXRpbmcgcHJvamVjdCB0YXNrIGFjdGlvbiBmb2xsb3cgdXAgZm9sbG93dXAgaW5mb3JtYXRpb24gaW5mbyB1cGRhdGUgdXBkYXRlZCBpc3N1ZSBpc3N1ZXMgdGVhbSB0ZWFtcyBjYyB0byBmcm9tIGluIG9uIGF0IG9mIGEgYW4gb3IgaXMgYmUgYXMgYnkgaXQgd2UgaSBoZSBzaGUgZG8gZGlkIGRvbmUgbmVlZCBuZWVkcyBuZWVkZWQgcmVxdWVzdCByZXF1ZXN0ZWQgcHJvdmlkZSBwcm92aWRlZCByZXZpZXcgcmV2aWV3ZWQgY29uZmlybSBjb25maXJtZWQiLnNwbGl0KCkpCkNOX1NUT1AgPSB7J+aCqOWlvScsJ+isneisnScsJ+iri+WVjycsJ+m6u+eFqScsJ+S7peS4iicsJ+WmguS4iycsJ+mZhOS7ticsJ+mDteS7ticsJ+S/oeS7ticsJ+WbnuimhicsJ+i9ieWvhCcsJ+S4u+aXqCcsJ+WQhOS9jScsJ+aIkeWAkScsJ+S9oOWAkScsJ+S7luWAkScsJ+mAmeWAiycsJ+mCo+WAiycsJ+ebruWJjScsJ+ebuOmXnCcsJ+mAsuihjCcsJ+aPkOS+mycsJ+eiuuiqjScsJ+abtOaWsCcsJ+izh+aWmScsJ+WFp+WuuScsJ+W3peS9nCcsJ+WVj+mhjCcsJ+iZleeQhicsJ+aUtuWIsCcsJ+aZgumWkycsJ+S7iuWkqScsJ+aYjuWkqScsJ+aYqOWkqSd9CkNBVEVHT1JZX1JVTEVTID0gWwogKCdSU0snLCfpoqjpmqrvvI/lu7boqqQnLFsnZGVsYXknLCdkZWxheWVkJywnb3ZlcmR1ZScsJ2xhdGUnLCdyaXNrJywnYmxvY2tlZCcsJ2Jsb2NrZXInLCdlc2NhbGF0JywnbWlzc2luZycsJ+mAvuacnycsJ+W7tumBsicsJ+miqOmaqicsJ+mYu+WhnicsJ+WNoeS9jycsJ+WNh+e0micsJ+acquaPkOS+mycsJ+e8uuWwkSddKSwKICgnREVDJywn5rG6562W77yP5qC45YeGJyxbJ2FwcHJvdmUnLCdhcHByb3ZhbCcsJ2RlY2lzaW9uJywnZGVjaWRlJywnc2lnbiBvZmYnLCdjb25maXJtJywn5qC45YeGJywn5rG6562WJywn5ZCM5oSPJywn56K66KqNJywn57C95qC4J10pLAogKCdBQ1QnLCfooYzli5XvvI/kuqTku5gnLFsnYWN0aW9uJywnZGVsaXZlcicsJ3N1Ym1pdCcsJ3Byb3ZpZGUnLCdwcmVwYXJlJywnY29tcGxldGUnLCdmb2xsb3cgdXAnLCflvoXovqYnLCfkuqTku5gnLCfmj5DkvpsnLCfmupblgpknLCflrozmiJAnLCfln7fooYwnLCfov73ouaQnXSksCiAoJ1dBSScsJ+etieW+heWbnuimhicsWyd3YWl0aW5nJywnYXdhaXQnLCdyZW1pbmQnLCdmb2xsb3ctdXAnLCdubyByZXNwb25zZScsJ3BlbmRpbmcgcmVwbHknLCfnrYnlvoUnLCflgqzopoYnLCfmnKrlm57opoYnLCflvoXlm57opoYnLCflsJrmnKrlm57opoYnXSksCiAoJ0VWRCcsJ+itieaTmu+8j+mZhOS7ticsWydhdHRhY2htZW50JywnYXR0YWNoZWQnLCdldmlkZW5jZScsJ3JlcG9ydCcsJ2RhdGEnLCdkb2N1bWVudCcsJ+mZhOS7ticsJ+itieaTmicsJ+WgseWRiicsJ+aVuOaTmicsJ+aWh+S7tiddKSwKICgnTVRHJywn5pyD6K2w77yP6KiO6KuWJyxbJ21lZXRpbmcnLCdtaW51dGVzJywnYWdlbmRhJywnZGlzY3Vzc2lvbicsJ2NhbGwnLCfmnIPorbAnLCfntIDpjIQnLCforbDnqIsnLCfoqI7oq5YnXSksCiAoJ1RSTicsJ+i9ieWgtO+8j+i9ieenuycsWydpbmRpYScsJ3RyYW5zZmVyJywndHJhbnNpdGlvbicsJ21pZ3JhdGlvbicsJ21hc3MgcHJvZHVjdGlvbicsJ+WNsOW6picsJ+i9ieWgtCcsJ+i9ieenuycsJ+mHj+eUoiddKSwKICgnUUxUJywn5ZOB6LOq77yP6amX6K2JJyxbJ3F1YWxpdHknLCd2YWxpZGF0aW9uJywndmVyaWZ5Jywnc2FtcGxlJywncHBhcCcsJ2ZhaScsJ3Rlc3QnLCflk4Hos6onLCfpqZforYknLCfmqKPlk4EnLCfmuKzoqaYnXSksCiAoJ0NIRycsJ+iuiuabtOeuoeeQhicsWydjaGFuZ2UnLCdyZXZpc2lvbicsJ3ZlcnNpb24nLCdlY24nLCdlY3InLCforormm7QnLCfniYjmnKwnLCfmlLnniYgnXSksCiAoJ1BMTicsJ+ioiOeVq++8j+aOkueoiycsWydwbGFuJywnc2NoZWR1bGUnLCdtaWxlc3RvbmUnLCd0aW1lbGluZScsJ+ioiOeVqycsJ+aOkueoiycsJ+mHjOeoi+eikScsJ+aZgueoiyddKSwKXQoKZGVmIHByb2dyZXNzKHBjdDppbnQsIG1zZzpzdHIpOgogICAgcHJpbnQoZiJQUk9HUkVTU3x7cGN0fXx7bXNnfSIsIGZsdXNoPVRydWUpCgpkZWYgc2hhMjU2X2ZpbGUocGF0aDpQYXRoKS0+c3RyOgogICAgaD1oYXNobGliLnNoYTI1NigpCiAgICB3aXRoIHBhdGgub3BlbigncmInKSBhcyBmOgogICAgICAgIGZvciBjaHVuayBpbiBpdGVyKGxhbWJkYTpmLnJlYWQoMTAyNCoxMDI0KSwgYicnKToKICAgICAgICAgICAgaC51cGRhdGUoY2h1bmspCiAgICByZXR1cm4gaC5oZXhkaWdlc3QoKQoKZGVmIHNhZmVfdGV4dChwYXRoOlBhdGgsIG1heF9ieXRlczppbnQpLT5zdHI6CiAgICByYXc9cGF0aC5yZWFkX2J5dGVzKClbOm1heF9ieXRlc10KICAgIGZvciBlbmMgaW4gKCd1dGYtOC1zaWcnLCd1dGYtOCcsJ2NwOTUwJywnY3AxMjUyJywnbGF0aW4tMScpOgogICAgICAgIHRyeTogcmV0dXJuIHJhdy5kZWNvZGUoZW5jKQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb246IHBhc3MKICAgIHJldHVybiByYXcuZGVjb2RlKCd1dGYtOCcsJ3JlcGxhY2UnKQoKZGVmIGRvdHRlZF9uYW1lKG5vZGUpOgogICAgaWYgaXNpbnN0YW5jZShub2RlLCBhc3QuTmFtZSk6IHJldHVybiBub2RlLmlkCiAgICBpZiBpc2luc3RhbmNlKG5vZGUsIGFzdC5BdHRyaWJ1dGUpOgogICAgICAgIGxlZnQ9ZG90dGVkX25hbWUobm9kZS52YWx1ZSkKICAgICAgICByZXR1cm4gZiJ7bGVmdH0ue25vZGUuYXR0cn0iIGlmIGxlZnQgZWxzZSBub2RlLmF0dHIKICAgIHJldHVybiAnJwoKZGVmIGNvbnN0YW50X3RleHQobm9kZSk6CiAgICBpZiBpc2luc3RhbmNlKG5vZGUsIGFzdC5Db25zdGFudCkgYW5kIGlzaW5zdGFuY2Uobm9kZS52YWx1ZSwoc3RyLGludCxmbG9hdCxib29sKSk6CiAgICAgICAgcmV0dXJuIHN0cihub2RlLnZhbHVlKQogICAgcmV0dXJuICcnCgpkZWYgcGFyc2VfcHl0aG9uKHRleHQ6c3RyKToKICAgIGZ1bmNzPVtdOyBjbGFzc2VzPVtdOyBpbXBvcnRzPVtdOyBjbGk9W107IHN0cmluZ3M9W107IHRvcF9jYWxscz1bXTsgc3RhdHVzPSdPSycKICAgIHRyeToKICAgICAgICB0cmVlPWFzdC5wYXJzZSh0ZXh0KQogICAgICAgIGZvciBub2RlIGluIGFzdC53YWxrKHRyZWUpOgogICAgICAgICAgICBpZiBpc2luc3RhbmNlKG5vZGUsKGFzdC5GdW5jdGlvbkRlZixhc3QuQXN5bmNGdW5jdGlvbkRlZikpOiBmdW5jcy5hcHBlbmQobm9kZS5uYW1lKQogICAgICAgICAgICBlbGlmIGlzaW5zdGFuY2Uobm9kZSxhc3QuQ2xhc3NEZWYpOiBjbGFzc2VzLmFwcGVuZChub2RlLm5hbWUpCiAgICAgICAgICAgIGVsaWYgaXNpbnN0YW5jZShub2RlLGFzdC5JbXBvcnQpOiBpbXBvcnRzLmV4dGVuZChhLm5hbWUgZm9yIGEgaW4gbm9kZS5uYW1lcykKICAgICAgICAgICAgZWxpZiBpc2luc3RhbmNlKG5vZGUsYXN0LkltcG9ydEZyb20pOiBpbXBvcnRzLmFwcGVuZChub2RlLm1vZHVsZSBvciAnJykKICAgICAgICAgICAgZWxpZiBpc2luc3RhbmNlKG5vZGUsYXN0LkNvbnN0YW50KSBhbmQgaXNpbnN0YW5jZShub2RlLnZhbHVlLHN0cik6IHN0cmluZ3MuYXBwZW5kKG5vZGUudmFsdWUpCiAgICAgICAgICAgIGVsaWYgaXNpbnN0YW5jZShub2RlLGFzdC5DYWxsKToKICAgICAgICAgICAgICAgIG5hbWU9ZG90dGVkX25hbWUobm9kZS5mdW5jKQogICAgICAgICAgICAgICAgaWYgbmFtZS5lbmRzd2l0aCgnYWRkX2FyZ3VtZW50Jyk6CiAgICAgICAgICAgICAgICAgICAgZm9yIGFyZyBpbiBub2RlLmFyZ3M6CiAgICAgICAgICAgICAgICAgICAgICAgIHZhbD1jb25zdGFudF90ZXh0KGFyZykKICAgICAgICAgICAgICAgICAgICAgICAgaWYgdmFsLnN0YXJ0c3dpdGgoJy0nKTogY2xpLmFwcGVuZCh2YWwpCiAgICAgICAgICAgICAgICAgICAgZm9yIGt3IGluIG5vZGUua2V5d29yZHM6CiAgICAgICAgICAgICAgICAgICAgICAgIGlmIGt3LmFyZz09J2Nob2ljZXMnIGFuZCBpc2luc3RhbmNlKGt3LnZhbHVlLChhc3QuTGlzdCxhc3QuVHVwbGUpKToKICAgICAgICAgICAgICAgICAgICAgICAgICAgIGNsaS5leHRlbmQoJ2Nob2ljZTonK2NvbnN0YW50X3RleHQoeCkgZm9yIHggaW4ga3cudmFsdWUuZWx0cyBpZiBjb25zdGFudF90ZXh0KHgpKQogICAgICAgIGZvciBub2RlIGluIHRyZWUuYm9keToKICAgICAgICAgICAgaWYgaXNpbnN0YW5jZShub2RlLGFzdC5FeHByKSBhbmQgaXNpbnN0YW5jZShub2RlLnZhbHVlLGFzdC5DYWxsKTogdG9wX2NhbGxzLmFwcGVuZChkb3R0ZWRfbmFtZShub2RlLnZhbHVlLmZ1bmMpKQogICAgICAgICAgICBpZiBpc2luc3RhbmNlKG5vZGUsKGFzdC5Bc3NpZ24sYXN0LkFubkFzc2lnbikpIGFuZCBpc2luc3RhbmNlKGdldGF0dHIobm9kZSwndmFsdWUnLE5vbmUpLGFzdC5DYWxsKTogdG9wX2NhbGxzLmFwcGVuZChkb3R0ZWRfbmFtZShub2RlLnZhbHVlLmZ1bmMpKQogICAgZXhjZXB0IEV4Y2VwdGlvbiBhcyBleGM6CiAgICAgICAgc3RhdHVzPSdQQVJTRV9FUlJPUjonK3N0cihleGMpCiAgICByZXR1cm4gZnVuY3MsY2xhc3NlcyxpbXBvcnRzLHNvcnRlZChzZXQoY2xpKSksc3RyaW5ncyx0b3BfY2FsbHMsc3RhdHVzCgpkZWYgd3JpdGVfY3N2KHBhdGg6UGF0aCwgcm93cywgZmllbGRzKToKICAgIHBhdGgucGFyZW50Lm1rZGlyKHBhcmVudHM9VHJ1ZSxleGlzdF9vaz1UcnVlKQogICAgd2l0aCBwYXRoLm9wZW4oJ3cnLGVuY29kaW5nPSd1dGYtOC1zaWcnLG5ld2xpbmU9JycpIGFzIGY6CiAgICAgICAgdz1jc3YuRGljdFdyaXRlcihmLGZpZWxkbmFtZXM9ZmllbGRzLGV4dHJhc2FjdGlvbj0naWdub3JlJyk7IHcud3JpdGVoZWFkZXIoKTsgdy53cml0ZXJvd3Mocm93cykKCmRlZiByZWFkX2NzdihwYXRoKToKICAgIHdpdGggUGF0aChwYXRoKS5vcGVuKCdyJyxlbmNvZGluZz0ndXRmLTgtc2lnJyxuZXdsaW5lPScnKSBhcyBmOiByZXR1cm4gbGlzdChjc3YuRGljdFJlYWRlcihmKSkKCmRlZiBwcm9iZShhcmdzKToKICAgIHJvb3Q9UGF0aChhcmdzLnJvb3QpOyBvdXQ9UGF0aChhcmdzLm91dCk7IG1heF9ieXRlcz1pbnQoYXJncy5tYXhfYnl0ZXMpCiAgICBpbnZlbnRvcnk9W107IGNhcGFiaWxpdGllcz1bXTsgcmlza3M9W107IHNlZWRzPUNvdW50ZXIoKTsgYWN0aXZhdGlvbj1bXTsgZmlsZXM9W10KICAgIGZvciBwIGluIHJvb3Qucmdsb2IoJyonKToKICAgICAgICB0cnk6IHJlbD1wLnJlbGF0aXZlX3RvKHJvb3QpCiAgICAgICAgZXhjZXB0IEV4Y2VwdGlvbjogY29udGludWUKICAgICAgICBwYXJ0cz17eC5sb3dlcigpIGZvciB4IGluIHJlbC5wYXJ0c30KICAgICAgICBpZiAnLnZlbnYnIGluIHBhcnRzIGFuZCBwLm5hbWUubG93ZXIoKSE9J3B5dmVudi5jZmcnOiBjb250aW51ZQogICAgICAgIGlmIHBhcnRzICYgeycuZ2l0JywnX19weWNhY2hlX18nLCdub2RlX21vZHVsZXMnLCcucHl0ZXN0X2NhY2hlJywnLm15cHlfY2FjaGUnLCcucnVmZl9jYWNoZSd9OiBjb250aW51ZQogICAgICAgIGlmIHAuaXNfZmlsZSgpIGFuZCAocC5zdWZmaXgubG93ZXIoKSBpbiBTQUZFX0VYVFMgb3IgcC5uYW1lIGluIFJPTEVfTUFQKTogZmlsZXMuYXBwZW5kKHApCiAgICBmaWxlcz1zb3J0ZWQoZmlsZXMsa2V5PWxhbWJkYSBwOihwLm5hbWUgbm90IGluIFJPTEVfTUFQLHN0cihwKS5sb3dlcigpKSkKICAgIHRvdGFsPW1heCgxLGxlbihmaWxlcykpCiAgICBmb3IgaSxwIGluIGVudW1lcmF0ZShmaWxlcywxKToKICAgICAgICBpZiBpPT0xIG9yIGklMTA9PTA6IHByb2dyZXNzKG1pbig5NSw1K2ludCg4NSppL3RvdGFsKSksZiJGb3JnZSBzdGF0aWMgc2NhbiB7aX0ve3RvdGFsfToge3AubmFtZX0iKQogICAgICAgIHJlbD1zdHIocC5yZWxhdGl2ZV90byhyb290KSk7IHNpemU9cC5zdGF0KCkuc3Rfc2l6ZQogICAgICAgIHJvbGUsdXNlPVJPTEVfTUFQLmdldChwLm5hbWUsKCJTVVBQT1JUSU5HX1NPVVJDRSIsIlN0YXRpYyB2b2NhYnVsYXJ5IGFuZCBkZXBlbmRlbmN5IGludmVudG9yeS4iKSkKICAgICAgICB0ZXh0PScnOyByZWFkX3N0YXR1cz0nT0snOyBmdW5jcz1bXTsgY2xhc3Nlcz1bXTsgaW1wb3J0cz1bXTsgY2xpPVtdOyBzdHJpbmdzPVtdOyB0b3BfY2FsbHM9W107IHBhcnNlX3N0YXR1cz0nTk9UX0FQUExJQ0FCTEUnCiAgICAgICAgaWYgc2l6ZT5tYXhfYnl0ZXM6IHJlYWRfc3RhdHVzPSdTS0lQUEVEX1NJWkVfR0FURScKICAgICAgICBlbHNlOgogICAgICAgICAgICB0cnk6IHRleHQ9c2FmZV90ZXh0KHAsbWF4X2J5dGVzKQogICAgICAgICAgICBleGNlcHQgRXhjZXB0aW9uIGFzIGV4YzogcmVhZF9zdGF0dXM9J1JFQURfRVJST1I6JytzdHIoZXhjKQogICAgICAgIGlmIHRleHQgYW5kIHAuc3VmZml4Lmxvd2VyKCk9PScucHknOiBmdW5jcyxjbGFzc2VzLGltcG9ydHMsY2xpLHN0cmluZ3MsdG9wX2NhbGxzLHBhcnNlX3N0YXR1cz1wYXJzZV9weXRob24odGV4dCkKICAgICAgICBlbGlmIHRleHQ6IGNsaT1zb3J0ZWQoc2V0KENMSV9PUFRfUkUuZmluZGFsbCh0ZXh0KSkpOyBzdHJpbmdzPVt0ZXh0XQogICAgICAgIHJpc2tfaGl0cz1bXTsgbG93PXRleHQubG93ZXIoKQogICAgICAgIGZvciB3b3JkLGtpbmQgaW4gUklTS19XT1JEUy5pdGVtcygpOgogICAgICAgICAgICBjb3VudD1sb3cuY291bnQod29yZCkKICAgICAgICAgICAgaWYgY291bnQ6CiAgICAgICAgICAgICAgICByaXNrX2hpdHMuYXBwZW5kKGYie2tpbmR9Ontjb3VudH0iKTsgcmlza3MuYXBwZW5kKHsiRklMRSI6cmVsLCJSSVNLX1RZUEUiOmtpbmQsIlRPS0VOIjp3b3JkLCJDT1VOVCI6Y291bnQsIkFDVElPTiI6IlNUQVRJQ19SRVZJRVdfT05MWSJ9KQogICAgICAgIGludmVudG9yeS5hcHBlbmQoeyJGSUxFIjpyZWwsIk5BTUUiOnAubmFtZSwiUk9MRSI6cm9sZSwiU0laRV9CWVRFUyI6c2l6ZSwiU0hBMjU2IjpzaGEyNTZfZmlsZShwKSwiUkVBRF9TVEFUVVMiOnJlYWRfc3RhdHVzLCJQQVJTRV9TVEFUVVMiOnBhcnNlX3N0YXR1cywiRlVOQ1RJT05fQ09VTlQiOmxlbihmdW5jcyksIkNMQVNTX0NPVU5UIjpsZW4oY2xhc3NlcyksIklNUE9SVF9DT1VOVCI6bGVuKGltcG9ydHMpLCJDTElfT1BUSU9OX0NPVU5UIjpsZW4oY2xpKSwiUklTS19ISVRTIjoiIHwgIi5qb2luKHJpc2tfaGl0cyl9KQogICAgICAgIGNhcGFiaWxpdGllcy5hcHBlbmQoeyJGSUxFIjpyZWwsIlJPTEUiOnJvbGUsIklOVEVHUkFUSU9OX1VTRSI6dXNlLCJGVU5DVElPTlMiOiIgfCAiLmpvaW4oc29ydGVkKHNldChmdW5jcykpWzoxMjBdKSwiQ0xBU1NFUyI6IiB8ICIuam9pbihzb3J0ZWQoc2V0KGNsYXNzZXMpKVs6ODBdKSwiSU1QT1JUUyI6IiB8ICIuam9pbihzb3J0ZWQoc2V0KHggZm9yIHggaW4gaW1wb3J0cyBpZiB4KSlbOjEyMF0pLCJERUNMQVJFRF9DTElfT1BUSU9OUyI6IiB8ICIuam9pbihjbGlbOjEyMF0pLCJUT1BfTEVWRUxfQ0FMTFMiOiIgfCAiLmpvaW4oc29ydGVkKHNldCh4IGZvciB4IGluIHRvcF9jYWxscyBpZiB4KSlbOjgwXSksIlRBUkdFVF9JTVBPUlRFRCI6Ik5PIiwiVEFSR0VUX0VYRUNVVEVEIjoiTk8iLCJBVVRPX0VYRUNVVEVfQUxMT1dFRCI6Ik5PIiwiR0FURSI6IlNUQVRJQ19PTkxZIn0pCiAgICAgICAgYWN0aXZhdGlvbi5hcHBlbmQoeyJDT01QT05FTlQiOnAubmFtZSwiUk9MRSI6cm9sZSwiRk9VTkQiOiJZRVMiLCJVU0VEX0JZX1YwMDQiOnVzZSwiRVhFQ1VUSU9OX01PREUiOiJTVEFUSUNfU0NIRU1BX0tFWVdPUkRfU09VUkNFIiwiQVVUT19FWEVDVVRFRCI6Ik5PIiwiUkVBU09OIjoiVW5rbm93biB0YXJnZXQgc2VtYW50aWNzIGFyZSBub3QgZXhlY3V0ZWQgaW5zaWRlIHRoZSB1c2VyLXNjb3BlIHJlYWQtb25seSB3b3JrZmxvdy4ifSkKICAgICAgICBibG9iPScgJy5qb2luKFtwLnN0ZW0scm9sZSx1c2UsJyAnLmpvaW4oZnVuY3MpLCcgJy5qb2luKGNsYXNzZXMpLCcgJy5qb2luKGNsaSksJyAnLmpvaW4oc3RyaW5nc1s6NDAwXSldKQogICAgICAgIGZvciB0b2sgaW4gVE9LRU5fUkUuZmluZGFsbChibG9iKToKICAgICAgICAgICAgdD10b2suc3RyaXAoJy5fLS8nKS5sb3dlcigpCiAgICAgICAgICAgIGlmIDM8PWxlbih0KTw9NDAgYW5kIG5vdCB0LmlzZGlnaXQoKTogc2VlZHNbdF0rPTMgaWYgcC5uYW1lIGluIFJPTEVfTUFQIGVsc2UgMQogICAgZm9yIG5hbWUsKHJvbGUsdXNlKSBpbiBST0xFX01BUC5pdGVtcygpOgogICAgICAgIGlmIG5vdCBhbnkoeFsnTkFNRSddPT1uYW1lIGZvciB4IGluIGludmVudG9yeSk6IGFjdGl2YXRpb24uYXBwZW5kKHsiQ09NUE9ORU5UIjpuYW1lLCJST0xFIjpyb2xlLCJGT1VORCI6Ik5PIiwiVVNFRF9CWV9WMDA0Ijp1c2UsIkVYRUNVVElPTl9NT0RFIjoiTk9UX0ZPVU5EIiwiQVVUT19FWEVDVVRFRCI6Ik5PIiwiUkVBU09OIjoiRXhwZWN0ZWQgY29tcG9uZW50IHdhcyBub3QgZm91bmQgYXQgdGhlIHJlc29sdmVkIEZvcmdlIHJvb3QuIn0pCiAgICBzZWVkX3Jvd3M9W3siS0VZV09SRCI6aywiRk9SR0VfV0VJR0hUIjp2LCJTT1VSQ0UiOiJWSUFfRk9SR0VfU1RBVElDIiwiRU5BQkxFRCI6IllFUyJ9IGZvciBrLHYgaW4gc2VlZHMubW9zdF9jb21tb24oMTAwMCldCiAgICB3cml0ZV9jc3Yob3V0LycwOF9mb3JnZV9pbnZlbnRvcnkuY3N2JyxpbnZlbnRvcnksWyJGSUxFIiwiTkFNRSIsIlJPTEUiLCJTSVpFX0JZVEVTIiwiU0hBMjU2IiwiUkVBRF9TVEFUVVMiLCJQQVJTRV9TVEFUVVMiLCJGVU5DVElPTl9DT1VOVCIsIkNMQVNTX0NPVU5UIiwiSU1QT1JUX0NPVU5UIiwiQ0xJX09QVElPTl9DT1VOVCIsIlJJU0tfSElUUyJdKQogICAgd3JpdGVfY3N2KG91dC8nMDlfZm9yZ2VfY2FwYWJpbGl0eV9jb21tYW5kX21hdHJpeC5jc3YnLGNhcGFiaWxpdGllcyxbIkZJTEUiLCJST0xFIiwiSU5URUdSQVRJT05fVVNFIiwiRlVOQ1RJT05TIiwiQ0xBU1NFUyIsIklNUE9SVFMiLCJERUNMQVJFRF9DTElfT1BUSU9OUyIsIlRPUF9MRVZFTF9DQUxMUyIsIlRBUkdFVF9JTVBPUlRFRCIsIlRBUkdFVF9FWEVDVVRFRCIsIkFVVE9fRVhFQ1VURV9BTExPV0VEIiwiR0FURSJdKQogICAgd3JpdGVfY3N2KG91dC8nMTBfZm9yZ2Vfa2V5d29yZF9zZWVkcy5jc3YnLHNlZWRfcm93cyxbIktFWVdPUkQiLCJGT1JHRV9XRUlHSFQiLCJTT1VSQ0UiLCJFTkFCTEVEIl0pCiAgICB3cml0ZV9jc3Yob3V0LycxMV9mb3JnZV9yaXNrX2ZpbmRpbmdzLmNzdicscmlza3MsWyJGSUxFIiwiUklTS19UWVBFIiwiVE9LRU4iLCJDT1VOVCIsIkFDVElPTiJdKQogICAgd3JpdGVfY3N2KG91dC8nMTJfZm9yZ2VfYWN0aXZhdGlvbl9tYXRyaXguY3N2JyxhY3RpdmF0aW9uLFsiQ09NUE9ORU5UIiwiUk9MRSIsIkZPVU5EIiwiVVNFRF9CWV9WMDA0IiwiRVhFQ1VUSU9OX01PREUiLCJBVVRPX0VYRUNVVEVEIiwiUkVBU09OIl0pCiAgICBwcm9ncmVzcygxMDAsZiJGb3JnZSBzdGF0aWMgaW50ZWdyYXRpb24gY29tcGxldGU6IHtsZW4oaW52ZW50b3J5KX0gZmlsZXMiKQoKZGVmIG5vcm1hbGl6ZV9zdWJqZWN0KHMpOgogICAgcz0ocyBvciAnJykuc3RyaXAoKTsgbGFzdD1Ob25lCiAgICB3aGlsZSBzIT1sYXN0OgogICAgICAgIGxhc3Q9czsgcz1yZS5zdWIocideXHMqKChyZXxmd3xmd2R8YXd8c3YpXHMqWzrvvJpdfOWbnuimhlxzKls677yaXXzovYnlr4RccypbOu+8ml0pXHMqJywnJyxzLGZsYWdzPXJlLkkpCiAgICBzPXJlLnN1YihyJ1xbW15cXV17MCwzMH1cXScsJyAnLHMpOyBzPXJlLnN1YihyJ1xiMjBcZHsyfVstLy5dXGR7MSwyfVstLy5dXGR7MSwyfVxiJywnICcscyk7IHJldHVybiByZS5zdWIocidccysnLCcgJyxzKS5zdHJpcCgpCgpkZWYgdG9rZW5zKHRleHQpOgogICAgb3V0PVtdCiAgICBmb3IgcmF3IGluIFRPS0VOX1JFLmZpbmRhbGwodGV4dCBvciAnJyk6CiAgICAgICAgdD1yYXcuc3RyaXAoJy5fLS8nKS5sb3dlcigpCiAgICAgICAgaWYgbGVuKHQpPDIgb3IgbGVuKHQpPjUwIG9yIHQuaXNkaWdpdCgpOiBjb250aW51ZQogICAgICAgIGlmIHJlLmZ1bGxtYXRjaChyJ1thLXowLTlfLlwtL10rJyx0KToKICAgICAgICAgICAgaWYgbGVuKHQpPj0zIGFuZCB0IG5vdCBpbiBTVE9QV09SRFM6IG91dC5hcHBlbmQodCkKICAgICAgICBlbGlmIHQgbm90IGluIENOX1NUT1AgYW5kIDI8PWxlbih0KTw9MTA6IG91dC5hcHBlbmQodCkKICAgIHJldHVybiBvdXQKCmRlZiBjbGFzc2lmeSh0ZXh0KToKICAgIGxvdz0odGV4dCBvciAnJykubG93ZXIoKTsgaGl0cz1bXQogICAgZm9yIGNvZGUsbGFiZWwsd29yZHMgaW4gQ0FURUdPUllfUlVMRVM6CiAgICAgICAgY291bnQ9c3VtKGxvdy5jb3VudCh3Lmxvd2VyKCkpIGZvciB3IGluIHdvcmRzKQogICAgICAgIGlmIGNvdW50OiBoaXRzLmFwcGVuZCgoY291bnQsY29kZSxsYWJlbCkpCiAgICBpZiBub3QgaGl0czogcmV0dXJuICdJTkYnLCfos4foqIrvvI/lj4PogIMnLCcnCiAgICBoaXRzLnNvcnQocmV2ZXJzZT1UcnVlKTsgcmV0dXJuIGhpdHNbMF1bMV0saGl0c1swXVsyXSwnIHwgJy5qb2luKGYne2N9OntufScgZm9yIG4sYyxsIGluIGhpdHMpCgpkZWYgcGFyc2VfdGltZShzKToKICAgIGZvciBmbXQgaW4gKCclWS8lbS8lZCAlSDolTTolUycsJyVZLSVtLSVkICVIOiVNOiVTJywnJVktJW0tJWRUJUg6JU06JVMnKToKICAgICAgICB0cnk6cmV0dXJuIGRhdGV0aW1lLnN0cnB0aW1lKHMsZm10KQogICAgICAgIGV4Y2VwdDpwYXNzCiAgICByZXR1cm4gZGF0ZXRpbWUubWluCgpkZWYgYXV0b19jb2RlKG5hbWUpOgogICAgd29yZHM9cmUuZmluZGFsbChyJ1tBLVphLXowLTldK3xbXHU0ZTAwLVx1OWZmZl0rJyxuYW1lIG9yICcnKTsgbGV0dGVycz0nJy5qb2luKHdbMF0gZm9yIHcgaW4gd29yZHMgaWYgdyBhbmQgcmUubWF0Y2gocidbQS1aYS16XScsd1swXSkpLnVwcGVyKClbOjNdCiAgICByZXR1cm4gKGxldHRlcnMraGFzaGxpYi5zaGExKChuYW1lIG9yICdPVEhFUicpLmVuY29kZSgpKS5oZXhkaWdlc3QoKS51cHBlcigpKVs6M10KCmRlZiBzcGxpdF9wZW9wbGUodGV4dCk6CiAgICByZXR1cm4gW3Auc3RyaXAoKSBmb3IgcCBpbiByZS5zcGxpdChyJ1xzKls7LHxdXHMqJyx0ZXh0IG9yICcnKSBpZiBwLnN0cmlwKCldCgpkZWYgZmllbGRzKHJvd3MpOgogICAgc2Vlbj1bXQogICAgZm9yIHIgaW4gcm93czoKICAgICAgICBmb3IgayBpbiByOgogICAgICAgICAgICBpZiBrIG5vdCBpbiBzZWVuOiBzZWVuLmFwcGVuZChrKQogICAgcmV0dXJuIHNlZW4gb3IgWydFTVBUWSddCgpkZWYgYW5hbHl6ZShhcmdzKToKICAgIG91dD1QYXRoKGFyZ3Mub3V0KTsgcm93cz1yZWFkX2NzdihhcmdzLm1haWxfY3N2KSBpZiBQYXRoKGFyZ3MubWFpbF9jc3YpLmV4aXN0cygpIGVsc2UgW10KICAgIHNlZWRfd2VpZ2h0cz17fQogICAgaWYgYXJncy5zZWVkX2NzdiBhbmQgUGF0aChhcmdzLnNlZWRfY3N2KS5leGlzdHMoKToKICAgICAgICBmb3IgciBpbiByZWFkX2NzdihhcmdzLnNlZWRfY3N2KToKICAgICAgICAgICAgdHJ5OiBzZWVkX3dlaWdodHNbclsnS0VZV09SRCddLmxvd2VyKCldPWZsb2F0KHIuZ2V0KCdGT1JHRV9XRUlHSFQnKSBvciAwKQogICAgICAgICAgICBleGNlcHQ6IHBhc3MKICAgIG49bWF4KDEsbGVuKHJvd3MpKTsgZG9jZnJlcT1Db3VudGVyKCk7IHRvdGFsZnJlcT1Db3VudGVyKCk7IHJvd190b2tlbnM9W10KICAgIHByb2dyZXNzKDUsZiJLZXl3b3JkIGRpc2NvdmVyeSBmcm9tIHtsZW4ocm93cyl9IG1haWwgcm93cyIpCiAgICBmb3IgaSxyIGluIGVudW1lcmF0ZShyb3dzLDEpOgogICAgICAgIHN1Ymo9bm9ybWFsaXplX3N1YmplY3Qoci5nZXQoJ1RJVExFJywnJykpOyB0ZXh0PScgJy5qb2luKFtzdWJqLHIuZ2V0KCdCT0RZX1NOSVBQRVQnLCcnKSxyLmdldCgnQVRUQUNITUVOVF9OQU1FUycsJycpLHIuZ2V0KCdDT05WRVJTQVRJT05fVE9QSUMnLCcnKV0pCiAgICAgICAgdHM9dG9rZW5zKHRleHQpOyByb3dfdG9rZW5zLmFwcGVuZCh0cyk7IHRvdGFsZnJlcS51cGRhdGUodHMpOyBkb2NmcmVxLnVwZGF0ZShzZXQodHMpKQogICAgICAgIGlmIGklNTAwPT0wOiBwcm9ncmVzcyhtaW4oMzAsNStpbnQoMjUqaS9uKSksZiJUb2tlbml6ZWQge2l9L3tsZW4ocm93cyl9IikKICAgIHNjb3Jlcz17dDpkZiooMSttYXRoLmxvZzFwKHRvdGFsZnJlcVt0XSkpKigxK21hdGgubG9nKChuKzEpLyhkZisxKSkpK21pbihzZWVkX3dlaWdodHMuZ2V0KHQsMCksMjUpKjAuNCBmb3IgdCxkZiBpbiBkb2NmcmVxLml0ZW1zKCl9CiAgICByYW5rZWQ9c29ydGVkKHNjb3Jlcy5pdGVtcygpLGtleT1sYW1iZGEgeDooLXhbMV0sLWRvY2ZyZXFbeFswXV0seFswXSkpWzppbnQoYXJncy50b3BfbildOyByYW5rX21hcD17azppIGZvciBpLChrLHYpIGluIGVudW1lcmF0ZShyYW5rZWQsMSl9CiAgICBrZXl3b3JkX3Jvd3M9W3siUkFOSyI6aSwiS0VZV09SRCI6aywiU0NPUkUiOnJvdW5kKHYsNCksIkRPQ1VNRU5UX0ZSRVFVRU5DWSI6ZG9jZnJlcVtrXSwiVE9UQUxfRlJFUVVFTkNZIjp0b3RhbGZyZXFba10sIkZPUkdFX1dFSUdIVCI6c2VlZF93ZWlnaHRzLmdldChrLDApLCJTT1VSQ0UiOiJNQUlMK0ZPUkdFX1NUQVRJQyJ9IGZvciBpLChrLHYpIGluIGVudW1lcmF0ZShyYW5rZWQsMSldCiAgICBlbnJpY2hlZD1bXTsgY2x1c3RlcnM9ZGVmYXVsdGRpY3QobGlzdCk7IHRocmVhZHM9ZGVmYXVsdGRpY3QobGlzdCk7IG5vdz1kYXRldGltZS5ub3coKQogICAgZm9yIHIsdHMgaW4gemlwKHJvd3Mscm93X3Rva2Vucyk6CiAgICAgICAgbm9ybT1ub3JtYWxpemVfc3ViamVjdChyLmdldCgnVElUTEUnLCcnKSk7IHVuaXF1ZT1zb3J0ZWQoc2V0KHRzKSxrZXk9bGFtYmRhIHQ6KHJhbmtfbWFwLmdldCh0LDk5OTk5OSksLXNjb3Jlcy5nZXQodCwwKSx0KSk7IHRvcD1bdCBmb3IgdCBpbiB1bmlxdWUgaWYgdCBpbiBzY29yZXNdWzppbnQoYXJncy5wZXJfbWFpbCldCiAgICAgICAgY29kZSxsYWJlbCxhbGxoaXRzPWNsYXNzaWZ5KCcgJy5qb2luKFtub3JtLHIuZ2V0KCdCT0RZX1NOSVBQRVQnLCcnKSxyLmdldCgnQVRUQUNITUVOVF9OQU1FUycsJycpXSkpCiAgICAgICAgY29udj0oci5nZXQoJ0NPTlZFUlNBVElPTl9JRCcpIG9yICcnKS5zdHJpcCgpOyBzaWduYXR1cmU9cmUuc3ViKHInW15hLXowLTlcdTRlMDAtXHU5ZmZmXSsnLCcgJyxub3JtLmxvd2VyKCkpOyBzaWduYXR1cmU9JyAnLmpvaW4oc2lnbmF0dXJlLnNwbGl0KClbOjE0XSkgb3IgJyAnLmpvaW4odG9wWzo2XSkgb3Igci5nZXQoJ01BSUxfRklOR0VSUFJJTlQnLCcnKVs6MTZdCiAgICAgICAgY2x1c3Rlcj0nVENMLScraGFzaGxpYi5zaGExKHNpZ25hdHVyZS5lbmNvZGUoKSkuaGV4ZGlnZXN0KClbOjEyXS51cHBlcigpOyBjYXNlPSdDT05WLScraGFzaGxpYi5zaGExKGNvbnYuZW5jb2RlKCkpLmhleGRpZ2VzdCgpWzoxMl0udXBwZXIoKSBpZiBjb252IGVsc2UgY2x1c3RlcgogICAgICAgIHB0PXBhcnNlX3RpbWUoci5nZXQoJ1RJTUUnLCcnKSk7IGFnZT1tYXgoMCwobm93LXB0KS50b3RhbF9zZWNvbmRzKCkvMzYwMCkgaWYgcHQhPWRhdGV0aW1lLm1pbiBlbHNlIDA7IGRpcmVjdGlvbj1yLmdldCgnRElSRUNUSU9OJywnJykKICAgICAgICBpZiBkaXJlY3Rpb249PSdPVVRCT1VORCcgYW5kIGFnZT49ZmxvYXQoYXJncy5zbGEpOiBzdGF0dXM9J1dBSVRJTkdfRVhURVJOQUxfUkVQTFknCiAgICAgICAgZWxpZiBkaXJlY3Rpb249PSdJTkJPVU5EJyBhbmQgKHIuZ2V0KCdSRUFEX1NUQVRVUycpPT0nVU5SRUFEJyBvciBjb2RlIGluIHsnUlNLJywnREVDJywnQUNUJywnV0FJJ30pOiBzdGF0dXM9J0lOVEVSTkFMX0FDVElPTl9SRVFVSVJFRCcKICAgICAgICBlbGlmIGNvZGUgaW4geydSU0snLCdERUMnLCdBQ1QnLCdXQUknfTogc3RhdHVzPSdUT19SRVZJRVcnCiAgICAgICAgZWxzZTogc3RhdHVzPSdSRUZFUkVOQ0UnCiAgICAgICAgZXI9ZGljdChyKTsgZXIudXBkYXRlKHsiTk9STUFMSVpFRF9USVRMRSI6bm9ybSwiQVVUT19LRVlXT1JEUyI6IiB8ICIuam9pbih0b3ApLCJQUklNQVJZX0NBVEVHT1JZX0NPREUiOmNvZGUsIlBSSU1BUllfQ0FURUdPUlkiOmxhYmVsLCJDQVRFR09SWV9ISVRTIjphbGxoaXRzLCJUSVRMRV9DTFVTVEVSX0lEIjpjbHVzdGVyLCJDQVNFX0lEIjpjYXNlLCJQUk9DRVNTX1NUQVRVUyI6c3RhdHVzLCJBR0VfSE9VUlMiOnJvdW5kKGFnZSwxKSwiQVVUT19BTkFMWVNJU19PTkxZIjoiVFJVRSIsIlVTRVJfQ09ORklSTUVEIjoiTk8ifSkKICAgICAgICBlbnJpY2hlZC5hcHBlbmQoZXIpOyBjbHVzdGVyc1tjbHVzdGVyXS5hcHBlbmQoZXIpOyB0aHJlYWRzW2Nhc2VdLmFwcGVuZChlcikKICAgIHByb2dyZXNzKDQ1LCJCdWlsZGluZyBwcm9qZWN0IGNhbmRpZGF0ZXMiKQogICAgY2x1c3Rlcl9yb3dzPVtdOyBwcm9qZWN0X3Jvd3M9W10KICAgIGZvciBjaWQsZ3JvdXAgaW4gc29ydGVkKGNsdXN0ZXJzLml0ZW1zKCksa2V5PWxhbWJkYSBrdjooLWxlbihrdlsxXSksa3ZbMF0pKToKICAgICAgICBjYXRzPUNvdW50ZXIoeFsnUFJJTUFSWV9DQVRFR09SWV9DT0RFJ10gZm9yIHggaW4gZ3JvdXApOyBrd3M9Q291bnRlcigpOyB0aXRsZXM9Q291bnRlcih4WydOT1JNQUxJWkVEX1RJVExFJ10gZm9yIHggaW4gZ3JvdXAgaWYgeFsnTk9STUFMSVpFRF9USVRMRSddKQogICAgICAgIGZvciB4IGluIGdyb3VwOiBrd3MudXBkYXRlKGsuc3RyaXAoKSBmb3IgayBpbiB4WydBVVRPX0tFWVdPUkRTJ10uc3BsaXQoJ3wnKSBpZiBrLnN0cmlwKCkpCiAgICAgICAgcmVwPXRpdGxlcy5tb3N0X2NvbW1vbigxKVswXVswXSBpZiB0aXRsZXMgZWxzZSAnKE5vIHN1YmplY3QpJzsgdGltZXM9c29ydGVkKHBhcnNlX3RpbWUoeFsnVElNRSddKSBmb3IgeCBpbiBncm91cCkKICAgICAgICBjbHVzdGVyX3Jvd3MuYXBwZW5kKHsiQ0xVU1RFUl9JRCI6Y2lkLCJNQUlMX0NPVU5UIjpsZW4oZ3JvdXApLCJSRVBSRVNFTlRBVElWRV9USVRMRSI6cmVwLCJFQVJMSUVTVF9USU1FIjp0aW1lc1swXS5zdHJmdGltZSgnJVkvJW0vJWQgJUg6JU06JVMnKSBpZiB0aW1lcyBlbHNlICcnLCJMQVRFU1RfVElNRSI6dGltZXNbLTFdLnN0cmZ0aW1lKCclWS8lbS8lZCAlSDolTTolUycpIGlmIHRpbWVzIGVsc2UgJycsIlRPUF9DQVRFR09SSUVTIjoiIHwgIi5qb2luKGYne2t9Ont2fScgZm9yIGssdiBpbiBjYXRzLm1vc3RfY29tbW9uKDUpKSwiVE9QX0tFWVdPUkRTIjoiIHwgIi5qb2luKGsgZm9yIGssdiBpbiBrd3MubW9zdF9jb21tb24oMTIpKSwiUkVWSUVXX1BSSU9SSVRZIjoiSElHSCIgaWYgbGVuKGdyb3VwKT49NSBlbHNlICdOT1JNQUwnfSkKICAgICAgICBpZiBsZW4oZ3JvdXApPj1pbnQoYXJncy5jbHVzdGVyX21pbik6IHByb2plY3Rfcm93cy5hcHBlbmQoeyJBVVRPX1BST0pFQ1RfQ09ERSI6YXV0b19jb2RlKHJlcCksIlBST0pFQ1RfTkFNRV9DQU5ESURBVEUiOnJlcFs6MTIwXSwiQ0xVU1RFUl9JRCI6Y2lkLCJNQUlMX0NPVU5UIjpsZW4oZ3JvdXApLCJQUklNQVJZX0NBVEVHT1JZX0NPREUiOmNhdHMubW9zdF9jb21tb24oMSlbMF1bMF0gaWYgY2F0cyBlbHNlICdJTkYnLCJUT1BfS0VZV09SRFMiOiIgfCAiLmpvaW4oayBmb3Igayx2IGluIGt3cy5tb3N0X2NvbW1vbigxNSkpLCJVU0VSX0NPTkZJUk0iOiIiLCJVU0VSX1BST0pFQ1RfTkFNRSI6IiIsIlVTRVJfUFJPSkVDVF9DT0RFIjoiIiwiU1RBVFVTIjoiQ0FORElEQVRFX1JFVklFV19SRVFVSVJFRCJ9KQogICAgcHJvZ3Jlc3MoNjAsIkJ1aWxkaW5nIHN0YWtlaG9sZGVyIGFuZCBwZW5kaW5nLXJlc3BvbnNlIG1hdHJpY2VzIikKICAgIHN0YWtlaG9sZGVycz1kZWZhdWx0ZGljdChsYW1iZGE6eydpbic6MCwnb3V0JzowLCdjYyc6MCwnbGFzdF9pbic6ZGF0ZXRpbWUubWluLCdsYXN0X291dCc6ZGF0ZXRpbWUubWluLCdwcm9qZWN0cyc6c2V0KCksJ25hbWVzJzpDb3VudGVyKCl9KQogICAgZm9yIHIgaW4gZW5yaWNoZWQ6CiAgICAgICAgdD1wYXJzZV90aW1lKHJbJ1RJTUUnXSk7IHByb2o9clsnVElUTEVfQ0xVU1RFUl9JRCddOyBmYT0oci5nZXQoJ0ZST01fQUREUkVTUycpIG9yIHIuZ2V0KCdGUk9NJykgb3IgJycpLnN0cmlwKCkKICAgICAgICBpZiBmYToKICAgICAgICAgICAgeD1zdGFrZWhvbGRlcnNbZmFdOyB4WyduYW1lcyddW3IuZ2V0KCdGUk9NJywnJyldKz0xOyB4Wydwcm9qZWN0cyddLmFkZChwcm9qKQogICAgICAgICAgICBpZiByLmdldCgnRElSRUNUSU9OJyk9PSdJTkJPVU5EJzogeFsnaW4nXSs9MTsgeFsnbGFzdF9pbiddPW1heCh4WydsYXN0X2luJ10sdCkKICAgICAgICAgICAgZWxzZTogeFsnb3V0J10rPTE7IHhbJ2xhc3Rfb3V0J109bWF4KHhbJ2xhc3Rfb3V0J10sdCkKICAgICAgICBmb3IgcCBpbiBzcGxpdF9wZW9wbGUoci5nZXQoJ1RPJywnJykpOiB4PXN0YWtlaG9sZGVyc1twXTsgeFsnb3V0J10rPTE7IHhbJ2xhc3Rfb3V0J109bWF4KHhbJ2xhc3Rfb3V0J10sdCk7IHhbJ3Byb2plY3RzJ10uYWRkKHByb2opCiAgICAgICAgZm9yIHAgaW4gc3BsaXRfcGVvcGxlKHIuZ2V0KCdDQycsJycpKTogeD1zdGFrZWhvbGRlcnNbcF07IHhbJ2NjJ10rPTE7IHhbJ3Byb2plY3RzJ10uYWRkKHByb2opCiAgICBzdGFrZWhvbGRlcl9yb3dzPVtdCiAgICBmb3IgYWRkcix4IGluIHN0YWtlaG9sZGVycy5pdGVtcygpOgogICAgICAgIG5hbWU9eFsnbmFtZXMnXS5tb3N0X2NvbW1vbigxKVswXVswXSBpZiB4WyduYW1lcyddIGVsc2UgYWRkcgogICAgICAgIHN0YWtlaG9sZGVyX3Jvd3MuYXBwZW5kKHsiU1RBS0VIT0xERVIiOm5hbWUsIkNPTlRBQ1QiOmFkZHIsIklOQk9VTkRfQ09VTlQiOnhbJ2luJ10sIk9VVEJPVU5EX09SX1RPX0NPVU5UIjp4WydvdXQnXSwiQ0NfQ09VTlQiOnhbJ2NjJ10sIkxBU1RfSU5CT1VORCI6eFsnbGFzdF9pbiddLnN0cmZ0aW1lKCclWS8lbS8lZCAlSDolTTolUycpIGlmIHhbJ2xhc3RfaW4nXSE9ZGF0ZXRpbWUubWluIGVsc2UgJycsIkxBU1RfT1VUQk9VTkQiOnhbJ2xhc3Rfb3V0J10uc3RyZnRpbWUoJyVZLyVtLyVkICVIOiVNOiVTJykgaWYgeFsnbGFzdF9vdXQnXSE9ZGF0ZXRpbWUubWluIGVsc2UgJycsIlBST0pFQ1RfQ0xVU1RFUl9DT1VOVCI6bGVuKHhbJ3Byb2plY3RzJ10pLCJDT05UQUNUX1RJRVIiOiJVTkNPTkZJUk1FRCIsIlBIT05FIjoiIiwiVEVBTVNfT1JfSU0iOiIiLCJJTkRJQV9DT05GSVJNRUQiOiIiLCJDT05UQUNUX0NPTVBMRVRFTkVTUyI6Ik1JU1NJTkdfUEhPTkVfQU5EX0lNIn0pCiAgICBwZW5kaW5nPVtdOyBldmVudHM9W107IGNvbnRyb2xsaW5nPVtdOyBhY3Rpb25zPVtdCiAgICBmb3IgY2FzZSxncm91cCBpbiB0aHJlYWRzLml0ZW1zKCk6CiAgICAgICAgZ3JvdXA9c29ydGVkKGdyb3VwLGtleT1sYW1iZGEgeDpwYXJzZV90aW1lKHhbJ1RJTUUnXSkpOyBsYXN0PWdyb3VwWy0xXTsgYWdlPWZsb2F0KGxhc3RbJ0FHRV9IT1VSUyddKTsgc3RhdGU9J0NMT1NFRF9PUl9JTkZPJzsgcHJpb3JpdHk9J1AzJzsgbmV4dF9hY3Rpb249J1JldmlldyB3aGVuIG5lZWRlZCcKICAgICAgICBpZiBsYXN0WydESVJFQ1RJT04nXT09J09VVEJPVU5EJyBhbmQgYWdlPj1mbG9hdChhcmdzLnNsYSk6IHN0YXRlPSdXQUlUSU5HX0VYVEVSTkFMX1JFUExZJzsgcHJpb3JpdHk9J1AxJzsgbmV4dF9hY3Rpb249J0ZvbGxvdyB1cCBhbmQgY29uZmlybSBvbmUgcHJpbWFyeSBwbHVzIHR3byBiYWNrdXAgY29udGFjdHMnCiAgICAgICAgZWxpZiBsYXN0WydESVJFQ1RJT04nXT09J0lOQk9VTkQnIGFuZCBsYXN0WydQUk9DRVNTX1NUQVRVUyddIGluIHsnSU5URVJOQUxfQUNUSU9OX1JFUVVJUkVEJywnVE9fUkVWSUVXJ306IHN0YXRlPSdJTlRFUk5BTF9SRVNQT05TRV9SRVFVSVJFRCc7IHByaW9yaXR5PSdQMScgaWYgbGFzdFsnUFJJTUFSWV9DQVRFR09SWV9DT0RFJ109PSdSU0snIGVsc2UgJ1AyJzsgbmV4dF9hY3Rpb249J0Fzc2lnbiBvd25lciBhbmQgcmVwbHkgb3IgcmVjb3JkIGRlY2lzaW9uJwogICAgICAgIGlmIHN0YXRlIT0nQ0xPU0VEX09SX0lORk8nOiBwZW5kaW5nLmFwcGVuZCh7IlBSSU9SSVRZIjpwcmlvcml0eSwiQ0FTRV9JRCI6Y2FzZSwiTEFTVF9USU1FIjpsYXN0WydUSU1FJ10sIkxBU1RfRElSRUNUSU9OIjpsYXN0WydESVJFQ1RJT04nXSwiVElUTEUiOmxhc3RbJ1RJVExFJ10sIkZST00iOmxhc3RbJ0ZST00nXSwiRlJPTV9BRERSRVNTIjpsYXN0WydGUk9NX0FERFJFU1MnXSwiVE8iOmxhc3RbJ1RPJ10sIkNDIjpsYXN0WydDQyddLCJQRU5ESU5HX1NUQVRVUyI6c3RhdGUsIkFHRV9IT1VSUyI6YWdlLCJDQVRFR09SWSI6bGFzdFsnUFJJTUFSWV9DQVRFR09SWSddLCJORVhUX0FDVElPTiI6bmV4dF9hY3Rpb24sIlBSSU1BUllfQ09OVEFDVF9DT05GSVJNRUQiOiJOTyIsIkJBQ0tVUF9DT05UQUNUX0NPVU5UIjowLCJDT05UQUNUX1JFU0lMSUVOQ0VfR0FQIjoiWUVTIn0pCiAgICAgICAgZm9yIHNlcSxyIGluIGVudW1lcmF0ZShncm91cCwxKToKICAgICAgICAgICAgYWN0aXZpdHk9J01haWwgUmVjZWl2ZWQnIGlmIHJbJ0RJUkVDVElPTiddPT0nSU5CT1VORCcgZWxzZSAnTWFpbCBTZW50JwogICAgICAgICAgICBhY3Rpdml0eT17J1JTSyc6J0lzc3VlIG9yIEVzY2FsYXRpb24nLCdERUMnOidEZWNpc2lvbiBvciBBcHByb3ZhbCcsJ0FDVCc6J0FjdGlvbiBvciBEZWxpdmVyeScsJ01URyc6J01lZXRpbmcgQ29tbXVuaWNhdGlvbid9LmdldChyWydQUklNQVJZX0NBVEVHT1JZX0NPREUnXSxhY3Rpdml0eSkKICAgICAgICAgICAgc3RhZ2U9eydSU0snOidFeGNlcHRpb24nLCdERUMnOidEZWNpc2lvbicsJ0FDVCc6J0V4ZWN1dGlvbicsJ1dBSSc6J1dhaXRpbmcnLCdNVEcnOidNZWV0aW5nJywnUExOJzonUGxhbm5pbmcnfS5nZXQoclsnUFJJTUFSWV9DQVRFR09SWV9DT0RFJ10sJ0NvbW11bmljYXRpb24nKQogICAgICAgICAgICBldmVudHMuYXBwZW5kKHsiQ0FTRV9JRCI6Y2FzZSwiRVZFTlRfSUQiOnJbJ01BSUxfRklOR0VSUFJJTlQnXSwiRVZFTlRfU0VRVUVOQ0UiOnNlcSwiVElNRSI6clsnVElNRSddLCJBQ1RJVklUWSI6YWN0aXZpdHksIlBST0NFU1NfU1RBR0UiOnN0YWdlLCJESVJFQ1RJT04iOnJbJ0RJUkVDVElPTiddLCJBQ1RPUiI6clsnRlJPTSddLCJBQ1RPUl9BRERSRVNTIjpyWydGUk9NX0FERFJFU1MnXSwiVElUTEUiOnJbJ1RJVExFJ10sIkNBVEVHT1JZX0NPREUiOnJbJ1BSSU1BUllfQ0FURUdPUllfQ09ERSddLCJQUk9DRVNTX1NUQVRVUyI6clsnUFJPQ0VTU19TVEFUVVMnXSwiU09VUkNFX0ZPTERFUiI6clsnRk9MREVSX1BBVEgnXX0pCiAgICAgICAgICAgIGNvbnRyb2xsaW5nLmFwcGVuZCh7IkNBU0VfSUQiOmNhc2UsIlRJTUUiOnJbJ1RJTUUnXSwiVElUTEUiOnJbJ1RJVExFJ10sIkZST00iOnJbJ0ZST00nXSwiVE8iOnJbJ1RPJ10sIkNDIjpyWydDQyddLCJSRUFEX1NUQVRVUyI6clsnUkVBRF9TVEFUVVMnXSwiUFJPQ0VTU19TVEFUVVMiOnJbJ1BST0NFU1NfU1RBVFVTJ10sIkNBVEVHT1JZX0NPREUiOnJbJ1BSSU1BUllfQ0FURUdPUllfQ09ERSddLCJDQVRFR09SWSI6clsnUFJJTUFSWV9DQVRFR09SWSddLCJLRVlXT1JEUyI6clsnQVVUT19LRVlXT1JEUyddLCJBR0VfSE9VUlMiOnJbJ0FHRV9IT1VSUyddLCJDT05UUk9MX1BSSU9SSVRZIjoiUDEiIGlmIHJbJ1BSSU1BUllfQ0FURUdPUllfQ09ERSddPT0nUlNLJyBlbHNlICgnUDInIGlmIHJbJ1BST0NFU1NfU1RBVFVTJ10hPSdSRUZFUkVOQ0UnIGVsc2UgJ1AzJyksIk5FWFRfQUNUSU9OIjoiUmV2aWV3IGFuZCBhc3NpZ24iIGlmIHJbJ1BST0NFU1NfU1RBVFVTJ10hPSdSRUZFUkVOQ0UnIGVsc2UgJ1JlZmVyZW5jZSBvbmx5JywiT1dORVIiOiIiLCJEVUVfREFURSI6IiIsIlVTRVJfU1RBVFVTIjoiIiwiTUFJTF9GSU5HRVJQUklOVCI6clsnTUFJTF9GSU5HRVJQUklOVCddfSkKICAgICAgICAgICAgaWYgclsnUFJJTUFSWV9DQVRFR09SWV9DT0RFJ10gaW4geydSU0snLCdERUMnLCdBQ1QnLCdXQUknLCdUUk4nLCdRTFQnLCdDSEcnLCdQTE4nfTogYWN0aW9ucy5hcHBlbmQoeyJBQ1RJT05fSUQiOiJBQ1QtIityWydNQUlMX0ZJTkdFUlBSSU5UJ11bOjEyXS51cHBlcigpLCJDQVNFX0lEIjpjYXNlLCJTT1VSQ0VfVElNRSI6clsnVElNRSddLCJUSVRMRSI6clsnVElUTEUnXSwiQUNUSU9OX1RZUEUiOnJbJ1BSSU1BUllfQ0FURUdPUlknXSwiREVTQ1JJUFRJT05fQ0FORElEQVRFIjpyLmdldCgnQk9EWV9TTklQUEVUJywnJylbOjgwMF0sIk9XTkVSX0NBTkRJREFURSI6clsnRlJPTSddIGlmIHJbJ0RJUkVDVElPTiddPT0nSU5CT1VORCcgZWxzZSAnJywiT1dORVJfQ09ORklSTUVEIjoiIiwiRFVFX0RBVEVfQ0FORElEQVRFIjoiIiwiU1RBVFVTIjoiQ0FORElEQVRFX1JFVklFV19SRVFVSVJFRCIsIkVWSURFTkNFX0ZJTkdFUlBSSU5UIjpyWydNQUlMX0ZJTkdFUlBSSU5UJ119KQogICAgcHJvZ3Jlc3MoODUsIldyaXRpbmcga2V5d29yZCwgcHJvamVjdCwgcHJvY2Vzcy1taW5pbmcgYW5kIGNvbnRyb2xsaW5nIG91dHB1dHMiKQogICAgb3V0cHV0cz1bKCcyMF9rZXl3b3JkX2RpY3Rpb25hcnkuY3N2JyxrZXl3b3JkX3Jvd3MpLCgnMjFfbWFpbF9lbnJpY2hlZC5jc3YnLGVucmljaGVkKSwoJzIyX21haWxfY2x1c3Rlcl9jYW5kaWRhdGVzLmNzdicsY2x1c3Rlcl9yb3dzKSwoJzIzX3Byb2plY3RfY2FuZGlkYXRlX21hdHJpeF9FRElUX0NPTkZJUk0uY3N2Jyxwcm9qZWN0X3Jvd3MpLCgnMjRfc3Rha2Vob2xkZXJfbWF0cml4LmNzdicsc3Rha2Vob2xkZXJfcm93cyksKCcyNV9GSVJTVF9QUklPUklUWV9wZW5kaW5nX3Jlc3BvbnNlLmNzdicsc29ydGVkKHBlbmRpbmcsa2V5PWxhbWJkYSByOihyWydQUklPUklUWSddLC1mbG9hdChyWydBR0VfSE9VUlMnXSkpKSksKCcyNl9wcm9jZXNzX21pbmluZ19ldmVudF9sb2cuY3N2JyxldmVudHMpLCgnMjdfcHJvamVjdF9jb250cm9sbGluZ19zaGVldC5jc3YnLGNvbnRyb2xsaW5nKSwoJzI4X2FjdGlvbl9yZWdpc3Rlcl9FRElUX0NPTlRST0wuY3N2JyxhY3Rpb25zKV0KICAgIGZvciBuYW1lLGRhdGEgaW4gb3V0cHV0czogd3JpdGVfY3N2KG91dC9uYW1lLGRhdGEsZmllbGRzKGRhdGEpKQogICAgcWM9W3siQ0hFQ0siOiJNQUlMX1JPV1NfUFJFU0VOVCIsIlJFU1VMVCI6IlBBU1MiIGlmIHJvd3MgZWxzZSAiV0FSTiIsIlZBTFVFIjpsZW4ocm93cyl9LHsiQ0hFQ0siOiJVTkNMQVNTSUZJRURfTUFJTFMiLCJSRVNVTFQiOiJQQVNTIiBpZiBhbGwoclsnUFJJTUFSWV9DQVRFR09SWV9DT0RFJ10gZm9yIHIgaW4gZW5yaWNoZWQpIGVsc2UgIkZBSUwiLCJWQUxVRSI6c3VtKDEgZm9yIHIgaW4gZW5yaWNoZWQgaWYgbm90IHJbJ1BSSU1BUllfQ0FURUdPUllfQ09ERSddKX0seyJDSEVDSyI6IlBST0pFQ1RfQ0FORElEQVRFUyIsIlJFU1VMVCI6IlBBU1MiIGlmIHByb2plY3Rfcm93cyBlbHNlICJXQVJOIiwiVkFMVUUiOmxlbihwcm9qZWN0X3Jvd3MpfSx7IkNIRUNLIjoiUEVORElOR19GSVJTVF9QUklPUklUWSIsIlJFU1VMVCI6IlJFVklFVyIgaWYgcGVuZGluZyBlbHNlICJQQVNTIiwiVkFMVUUiOmxlbihwZW5kaW5nKX0seyJDSEVDSyI6IkNPTlRBQ1RfUkVTSUxJRU5DRV9DT05GSVJNRUQiLCJSRVNVTFQiOiJSRVZJRVciLCJWQUxVRSI6IlVzZXIgY29uZmlybWF0aW9uIHJlcXVpcmVkOiAxIHByaW1hcnkgKyAyIGJhY2t1cHMifSx7IkNIRUNLIjoiU09VUkNFX01VVEFUSU9OIiwiUkVTVUxUIjoiUEFTUyIsIlZBTFVFIjoiRkFMU0UifSx7IkNIRUNLIjoiVEFSR0VUX0ZPUkdFX0lNUE9SVF9FWEVDVVRJT04iLCJSRVNVTFQiOiJQQVNTIiwiVkFMVUUiOiJGQUxTRSJ9XQogICAgd3JpdGVfY3N2KG91dC8nMjlfcXVhbGl0eV9jaGVja19tYXRyaXguY3N2JyxxYyxbIkNIRUNLIiwiUkVTVUxUIiwiVkFMVUUiXSkKICAgIHByb2dyZXNzKDEwMCxmIk1haWwgaW50ZWxsaWdlbmNlIGNvbXBsZXRlOiBrZXl3b3Jkcz17bGVuKGtleXdvcmRfcm93cyl9LCBwcm9qZWN0cz17bGVuKHByb2plY3Rfcm93cyl9LCBwZW5kaW5nPXtsZW4ocGVuZGluZyl9IikKCmRlZiBtYWluKCk6CiAgICBhcD1hcmdwYXJzZS5Bcmd1bWVudFBhcnNlcigpOyBhcC5hZGRfYXJndW1lbnQoJy0tbW9kZScsY2hvaWNlcz1bJ3Byb2JlJywnYW5hbHl6ZSddLHJlcXVpcmVkPVRydWUpOyBhcC5hZGRfYXJndW1lbnQoJy0tcm9vdCcpOyBhcC5hZGRfYXJndW1lbnQoJy0tb3V0JyxyZXF1aXJlZD1UcnVlKTsgYXAuYWRkX2FyZ3VtZW50KCctLW1heC1ieXRlcycsZGVmYXVsdD0nNDE5NDMwNCcpOyBhcC5hZGRfYXJndW1lbnQoJy0tbWFpbC1jc3YnKTsgYXAuYWRkX2FyZ3VtZW50KCctLXNlZWQtY3N2Jyk7IGFwLmFkZF9hcmd1bWVudCgnLS10b3AtbicsZGVmYXVsdD0nMzAwJyk7IGFwLmFkZF9hcmd1bWVudCgnLS1wZXItbWFpbCcsZGVmYXVsdD0nMTInKTsgYXAuYWRkX2FyZ3VtZW50KCctLXNsYScsZGVmYXVsdD0nNzInKTsgYXAuYWRkX2FyZ3VtZW50KCctLWNsdXN0ZXItbWluJyxkZWZhdWx0PScyJykKICAgIGFyZ3M9YXAucGFyc2VfYXJncygpOyBwcm9iZShhcmdzKSBpZiBhcmdzLm1vZGU9PSdwcm9iZScgZWxzZSBhbmFseXplKGFyZ3MpCmlmIF9fbmFtZV9fPT0nX19tYWluX18nOiBtYWluKCkK'
    $bytes = [Convert]::FromBase64String($helperBase64)
    [IO.File]::WriteAllBytes($State.HelperPy, $bytes)
}

function def_InvokeLocalHelper {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string[]]$Arguments,
        [int]$ProgressBase,
        [int]$ProgressSpan,
        [string]$Stage
    )

    if ([string]::IsNullOrWhiteSpace($State.PythonExe)) { throw '找不到可用 Python。' }
    $oldDontWrite = $env:PYTHONDONTWRITEBYTECODE
    $oldUtf8 = $env:PYTHONUTF8
    $env:PYTHONDONTWRITEBYTECODE = '1'
    $env:PYTHONUTF8 = '1'
    try {
        & $State.PythonExe -B -u $State.HelperPy @Arguments 2>&1 | ForEach-Object {
            $line = [string]$_
            if ($line -match '^PROGRESS\|(\d+)\|(.*)$') {
                $helperPct = [int]$Matches[1]
                $message = $Matches[2]
                $mapped = $ProgressBase + [int]($ProgressSpan * $helperPct / 100)
                def_ShowProgress -Percent ([Math]::Min(99, $mapped)) -Stage $Stage -Status $message
                def_WriteHeartbeat -Message $message
            } elseif (-not [string]::IsNullOrWhiteSpace($line)) {
                Write-Host "def $Stage : $line" -ForegroundColor DarkGray
            }
        }
        if ($LASTEXITCODE -ne 0) { throw "Python helper failed with exit code $LASTEXITCODE" }
    } finally {
        $env:PYTHONDONTWRITEBYTECODE = $oldDontWrite
        $env:PYTHONUTF8 = $oldUtf8
    }
}

function def_RunForgeStaticIntegration {
    [CmdletBinding()]
    param()

    $State.ForgeRoot = def_ResolveForgeRoot
    $State.PythonExe = def_ResolvePythonExe -ForgeRoot $State.ForgeRoot
    def_WriteLocalPythonHelper

    if ([string]::IsNullOrWhiteSpace($State.ForgeRoot)) {
        $missing = [pscustomobject][ordered]@{ COMPONENT='VIA_Forge'; ROLE='PANORAMA_STATIC_AUDIT'; FOUND='NO'; USED_BY_V004='Forge root not found'; EXECUTION_MODE='SKIPPED'; AUTO_EXECUTED='NO'; REASON='Check FORGE_ROOT_HINT or Downloads VIA_Forge folders.' }
        def_AppendCsvUtf8 -Rows @($missing) -Path $State.ForgeActivationCsv
        return
    }
    if ([string]::IsNullOrWhiteSpace($State.PythonExe)) {
        def_AddError -Stage 'FORGE_STATIC' -StoreName '' -FolderPath $State.ForgeRoot -Message 'Python executable not found; Forge AST integration skipped.'
        return
    }
    def_InvokeLocalHelper -Arguments @('--mode','probe','--root',$State.ForgeRoot,'--out',$State.RunDir,'--max-bytes',[string]$Config.ForgeMaxFileBytes) -ProgressBase 1 -ProgressSpan 9 -Stage 'FORGE_PANORAMA'
}

function def_RunMailIntelligence {
    [CmdletBinding()]
    param()

    if (-not $Config.AutoKeywordDiscovery -or -not (Test-Path -LiteralPath $State.MailCsv)) { return }
    if ([string]::IsNullOrWhiteSpace($State.PythonExe)) { $State.PythonExe = def_ResolvePythonExe -ForgeRoot $State.ForgeRoot }
    if ([string]::IsNullOrWhiteSpace($State.PythonExe)) {
        def_AddError -Stage 'MAIL_INTELLIGENCE' -StoreName '' -FolderPath '' -Message 'Python unavailable; keyword and project analysis skipped.'
        return
    }
    if (-not (Test-Path -LiteralPath $State.HelperPy)) { def_WriteLocalPythonHelper }
    def_InvokeLocalHelper -Arguments @('--mode','analyze','--out',$State.RunDir,'--mail-csv',$State.MailCsv,'--seed-csv',$State.ForgeKeywordSeedCsv,'--top-n',[string]$Config.KeywordTopN,'--per-mail',[string]$Config.MailKeywordsPerItem,'--sla',[string]$Config.ResponseSlaHours,'--cluster-min',[string]$Config.ProjectClusterMinMails) -ProgressBase 76 -ProgressSpan 20 -Stage 'WORKOPS_INTELLIGENCE'
}

# ====================================================================================
# def 輸出與 HTML
# ====================================================================================

function def_WriteAcceleratorMatrix {
    [CmdletBinding()]
    param()

    $rows = foreach ($item in $ACCELERATORS) {
        [pscustomobject][ordered]@{
            CODE    = $item.CODE
            NAME    = $item.NAME
            ENABLED = [bool]$item.ENABLED
            PURPOSE = $item.PURPOSE
        }
    }

    if ($PSVersionTable.PSVersion.Major -ge 6) {
        $rows | Export-Csv -LiteralPath $State.AcceleratorCsv -NoTypeInformation -Encoding utf8BOM
    }
    else {
        $rows | Export-Csv -LiteralPath $State.AcceleratorCsv -NoTypeInformation -Encoding UTF8
    }
}

function def_EnsureOutputHeaders {
    [CmdletBinding()]
    param()

    if (-not (Test-Path -LiteralPath $State.MailCsv)) {
        $header = 'TIME,DIRECTION,ITEM_TYPE,TITLE,FROM,FROM_ADDRESS,TO,CC,READ_STATUS,IMPORTANCE,FLAG_STATUS,CATEGORIES,ATTACHMENT_COUNT,ATTACHMENT_NAMES,BODY_SNIPPET,STORE_NAME,FOLDER_NAME,FOLDER_PATH,MESSAGE_CLASS,CONVERSATION_TOPIC,CONVERSATION_ID,INTERNET_MESSAGE_ID,MAIL_FINGERPRINT,ENTRY_ID,STORE_ID,SIZE_BYTES,RECEIVED_TIME,SENT_TIME,CREATION_TIME,LAST_MODIFICATION_TIME,SOURCE_READ_ONLY'
        def_WriteTextAtomic -Path $State.MailCsv -Content ($header + [Environment]::NewLine)
    }

    if (-not (Test-Path -LiteralPath $State.FolderCsv)) {
        $header = 'SCAN_ORDER,STORE_NAME,FOLDER_PATH,DEPTH,METHOD,ITEM_COUNT,MATCHED,DURATION_MS,STATUS,COMPLETED_AT'
        def_WriteTextAtomic -Path $State.FolderCsv -Content ($header + [Environment]::NewLine)
    }

    if (-not (Test-Path -LiteralPath $State.ErrorCsv)) {
        $header = 'TIME,STAGE,STORE_NAME,FOLDER_PATH,ERROR'
        def_WriteTextAtomic -Path $State.ErrorCsv -Content ($header + [Environment]::NewLine)
    }
}

function def_WriteHtmlReport {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Summary)

    $folderRows = @()
    $mailRows = @()
    $acceleratorRows = @()
    $forgeActivationRows = @()
    $keywordRows = @()
    $projectRows = @()
    $pendingRows = @()
    $qualityRows = @()

    try {
        $folderRows = @(Import-Csv -LiteralPath $State.FolderCsv | Where-Object { [int]$_.MATCHED -gt 0 } | Sort-Object { [int]$_.MATCHED } -Descending | Select-Object -First 30)
    }
    catch {}

    try {
        $mailRows = @(Import-Csv -LiteralPath $State.MailCsv | Sort-Object TIME -Descending | Select-Object -First 300)
    }
    catch {}

    try {
        $acceleratorRows = @(Import-Csv -LiteralPath $State.AcceleratorCsv)
    }
    catch {}

    try { $forgeActivationRows = @(Import-Csv -LiteralPath $State.ForgeActivationCsv | Sort-Object FOUND, ROLE | Select-Object -First 80) } catch {}
    try { $keywordRows = @(Import-Csv -LiteralPath $State.KeywordDictionaryCsv | Select-Object -First 50) } catch {}
    try { $projectRows = @(Import-Csv -LiteralPath $State.ProjectCandidateCsv | Sort-Object { [int]$_.MAIL_COUNT } -Descending | Select-Object -First 40) } catch {}
    try { $pendingRows = @(Import-Csv -LiteralPath $State.PendingResponseCsv | Sort-Object PRIORITY, { [double]$_.AGE_HOURS } -Descending | Select-Object -First 80) } catch {}
    try { $qualityRows = @(Import-Csv -LiteralPath $State.QualityCheckCsv) } catch {}

    $summaryHtml = @"
<table>
<tr><th>項目</th><th>結果</th></tr>
<tr><td>Policy</td><td>$([Net.WebUtility]::HtmlEncode($Summary.POLICY))</td></tr>
<tr><td>指定時間</td><td>$([Net.WebUtility]::HtmlEncode($Summary.START_TIME)) ～ $([Net.WebUtility]::HtmlEncode($Summary.END_TIME))</td></tr>
<tr><td>Store 數</td><td>$($Summary.STORE_COUNT)</td></tr>
<tr><td>規劃資料夾數</td><td>$($Summary.PLANNED_FOLDER_COUNT)</td></tr>
<tr><td>完成資料夾數</td><td>$($Summary.COMPLETED_FOLDER_COUNT)</td></tr>
<tr><td>符合郵件數</td><td>$($Summary.MATCHED_MAIL_COUNT)</td></tr>
<tr><td>錯誤數</td><td>$($Summary.ERROR_COUNT)</td></tr>
<tr><td>執行時間</td><td>$([Net.WebUtility]::HtmlEncode($Summary.ELAPSED))</td></tr>
<tr><td>內文摘要</td><td>$($Summary.INCLUDE_BODY_SNIPPET)</td></tr>
<tr><td>安全加速器</td><td>$($Summary.ACCELERATOR_ENABLED_COUNT) / 15 enabled</td></tr>
<tr><td>VIA Forge Root</td><td>$([Net.WebUtility]::HtmlEncode($Summary.FORGE_ROOT))</td></tr>
<tr><td>自動關鍵字</td><td>$($Config.AutoKeywordDiscovery)</td></tr>
</table>
"@

    $folderHtml = if ($folderRows.Count -gt 0) {
        $folderRows |
            Select-Object STORE_NAME, FOLDER_PATH, METHOD, ITEM_COUNT, MATCHED, DURATION_MS, STATUS |
            ConvertTo-Html -Fragment
    }
    else {
        '<p>指定時間內沒有符合郵件的資料夾。</p>'
    }

    $acceleratorHtml = if ($acceleratorRows.Count -gt 0) {
        $acceleratorRows | Select-Object CODE, NAME, ENABLED, PURPOSE | ConvertTo-Html -Fragment
    }
    else { '<p>無加速器資料。</p>' }

    $mailHtml = if ($mailRows.Count -gt 0) {
        $mailRows |
            Select-Object TIME, DIRECTION, TITLE, FROM, TO, CC, READ_STATUS, ATTACHMENT_COUNT, STORE_NAME, FOLDER_PATH |
            ConvertTo-Html -Fragment
    }
    else {
        '<p>指定時間內未找到郵件。</p>'
    }

    $forgeHtml = if ($forgeActivationRows.Count -gt 0) {
        $forgeActivationRows | Select-Object COMPONENT, ROLE, FOUND, USED_BY_V004, EXECUTION_MODE, AUTO_EXECUTED | ConvertTo-Html -Fragment
    } else { '<p>未取得 VIA Forge 靜態整合矩陣。</p>' }

    $keywordHtml = if ($keywordRows.Count -gt 0) {
        $keywordRows | Select-Object RANK, KEYWORD, SCORE, DOCUMENT_FREQUENCY, TOTAL_FREQUENCY, FORGE_WEIGHT | ConvertTo-Html -Fragment
    } else { '<p>沒有關鍵字結果。</p>' }

    $projectHtml = if ($projectRows.Count -gt 0) {
        $projectRows | Select-Object AUTO_PROJECT_CODE, PROJECT_NAME_CANDIDATE, MAIL_COUNT, PRIMARY_CATEGORY_CODE, TOP_KEYWORDS, STATUS | ConvertTo-Html -Fragment
    } else { '<p>沒有達到門檻的專案候選。</p>' }

    $pendingHtml = if ($pendingRows.Count -gt 0) {
        $pendingRows | Select-Object PRIORITY, LAST_TIME, TITLE, FROM, TO, PENDING_STATUS, AGE_HOURS, CATEGORY, NEXT_ACTION, CONTACT_RESILIENCE_GAP | ConvertTo-Html -Fragment
    } else { '<p>沒有第一優先未回覆／待處理案件。</p>' }

    $qualityHtml = if ($qualityRows.Count -gt 0) {
        $qualityRows | Select-Object CHECK, RESULT, VALUE | ConvertTo-Html -Fragment
    } else { '<p>沒有品質檢查結果。</p>' }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA WorkOps Intelligence Report v004</title>
<style>
body{font-family:Segoe UI,Microsoft JhengHei,sans-serif;margin:28px;color:#202124;background:#f7f8fa}
main{max-width:1500px;margin:auto;background:white;padding:28px;border:1px solid #dfe1e5;border-radius:12px}
h1{margin:0 0 4px;font-size:26px}h2{margin-top:30px;font-size:19px}
.brand{color:#5f6368;margin-bottom:22px}.policy{padding:12px;background:#f1f3f4;border-left:4px solid #5f6368}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:10px}
th,td{border:1px solid #dadce0;padding:7px;text-align:left;vertical-align:top}
th{background:#f1f3f4;position:sticky;top:0}
.small{font-size:12px;color:#5f6368}
</style>
</head>
<body><main>
<h1>VIA WorkOps 郵件、專案與流程智慧報告</h1>
<div class="brand">VERITAS INTELLIGENCE ANALYTICS · VIA WorkOps Intelligence Workbench</div>
<div class="policy">本工具只讀目前使用者 Outlook Profile 與 VIA Forge 文字型原始碼；不修改郵件、不 import 或執行 Forge 目標、不下載附件、不安裝模組、不提權。</div>
<h2>執行摘要</h2>
$summaryHtml
<h2>十五個安全加速器</h2>
$acceleratorHtml
<h2>VIA Forge 元件整合矩陣</h2>
$forgeHtml
<h2>自動發現關鍵字 Top 50</h2>
$keywordHtml
<h2>專案候選群組</h2>
$projectHtml
<h2>第一優先：未回覆與窗口韌性缺口</h2>
$pendingHtml
<h2>品質檢查</h2>
$qualityHtml
<h2>符合郵件最多的資料夾</h2>
$folderHtml
<h2>最近 300 封符合郵件</h2>
$mailHtml
<p class="small">完整資料位於同一 RunDir 的 CSV；HTML 僅呈現最近 300 封。</p>
</main></body></html>
"@

    def_WriteTextAtomic -Path $State.ReportHtml -Content $html
}

function def_WriteFinalManifest {
    [CmdletBinding()]
    param([bool]$Completed)

    $summary = [pscustomobject][ordered]@{
        SYSTEM_NAME                 = 'VERITAS INTELLIGENCE ANALYTICS'
        PRODUCT_NAME                = 'VIA WorkOps Intelligence Workbench'
        SCRIPT_VERSION              = $SCRIPT_VERSION
        POLICY                      = $POLICY
        COMPLETED                   = $Completed
        RUN_DIR                     = $State.RunDir
        START_TIME                  = $Config.StartTime.ToString('yyyy/MM/dd HH:mm:ss')
        END_TIME                    = $Config.EndTime.ToString('yyyy/MM/dd HH:mm:ss')
        STORE_COUNT                 = $State.StoreCount
        PLANNED_FOLDER_COUNT        = $State.PlannedFolderCount
        COMPLETED_FOLDER_COUNT      = $State.CompletedFolderCount
        SKIPPED_FOLDER_COUNT        = $State.SkippedFolderCount
        RESTRICTED_FOLDER_COUNT     = $State.RestrictedFolderCount
        FALLBACK_FOLDER_COUNT       = $State.FallbackFolderCount
        SCANNED_ITEM_REFERENCE_COUNT = $State.ScannedItemReferenceCount
        MATCHED_MAIL_COUNT          = $State.MatchedMailCount
        ERROR_COUNT                 = $State.ErrorCount
        INCLUDE_SUBFOLDERS          = $Config.IncludeSubfolders
        INCLUDE_SEARCH_FOLDERS      = $Config.IncludeSearchFolders
        INCLUDE_PUBLIC_FOLDERS      = $Config.IncludePublicFolders
        INCLUDE_MEETING_ITEMS       = $Config.IncludeMeetingItems
        INCLUDE_BODY_SNIPPET        = $Config.IncludeBodySnippet
        INCLUDE_ATTACHMENT_NAMES    = $Config.IncludeAttachmentNames
        USE_RESTRICT                = $Config.UseRestrict
        MAX_ITEMS_PER_FOLDER        = $Config.MaxItemsPerFolder
        RESUME_INCOMPLETE           = $Config.ResumeIncomplete
        SKIP_NON_MAIL_DEFAULT_FOLDERS = $Config.SkipNonMailDefaultFolders
        GC_EVERY_FOLDERS             = $Config.GcEveryFolders
        ACCELERATOR_TOTAL_COUNT      = $ACCELERATORS.Count
        ACCELERATOR_ENABLED_COUNT    = @($ACCELERATORS | Where-Object { $_.ENABLED }).Count
        OUTLOOK_INSTANCE_STARTED_BY_TOOL = $State.OutlookStartedByTool
        ELAPSED                     = def_GetElapsedText
        MAIL_CSV                    = $State.MailCsv
        FOLDER_AUDIT_CSV            = $State.FolderCsv
        ERROR_CSV                   = $State.ErrorCsv
        CHECKPOINT_JSON             = $State.CheckpointJson
        HEARTBEAT_JSON              = $State.HeartbeatJson
        HTML_REPORT                 = $State.ReportHtml
        ACCELERATOR_CSV              = $State.AcceleratorCsv
        FORGE_ROOT                   = $State.ForgeRoot
        PYTHON_EXE                   = $State.PythonExe
        FORGE_INVENTORY_CSV          = $State.ForgeInventoryCsv
        FORGE_CAPABILITY_CSV         = $State.ForgeCapabilityCsv
        FORGE_KEYWORD_SEEDS_CSV      = $State.ForgeKeywordSeedCsv
        FORGE_RISK_CSV               = $State.ForgeRiskCsv
        FORGE_ACTIVATION_CSV         = $State.ForgeActivationCsv
        KEYWORD_DICTIONARY_CSV       = $State.KeywordDictionaryCsv
        ENRICHED_MAIL_CSV            = $State.EnrichedMailCsv
        CLUSTER_CANDIDATE_CSV        = $State.ClusterCandidateCsv
        PROJECT_CANDIDATE_CSV        = $State.ProjectCandidateCsv
        STAKEHOLDER_CSV              = $State.StakeholderCsv
        PENDING_RESPONSE_CSV         = $State.PendingResponseCsv
        PROCESS_MINING_CSV           = $State.ProcessMiningCsv
        CONTROLLING_CSV              = $State.ControllingCsv
        ACTION_REGISTER_CSV          = $State.ActionRegisterCsv
        QUALITY_CHECK_CSV            = $State.QualityCheckCsv
        COMPLETED_AT                = (Get-Date).ToString('yyyy/MM/dd HH:mm:ss')
    }

    def_WriteJsonAtomic -Path $State.ManifestJson -Data $summary -Depth 6
    return $summary
}

# ====================================================================================
# def 主流程
# ====================================================================================

function def_Main {
    [CmdletBinding()]
    param()

    $connection = $null
    $outlook = $null
    $namespace = $null
    $completed = $false

    def_AcquireSingleInstanceLock
    def_InitializeRunDirectory
    def_EnsureOutputHeaders
    def_WriteAcceleratorMatrix

    Write-Host ''
    Write-Host ('=' * 104) -ForegroundColor DarkGray
    Write-Host 'def VERITAS INTELLIGENCE ANALYTICS' -ForegroundColor Cyan
    Write-Host 'def VIA WorkOps · Outlook + VIA Forge 智慧工作整合 · v004 · PS7+ · 15 ACCELERATORS' -ForegroundColor Cyan
    Write-Host ('=' * 104) -ForegroundColor DarkGray
    Write-Host "def StartTime : $($Config.StartTime.ToString('yyyy/MM/dd HH:mm:ss'))"
    Write-Host "def EndTime   : $($Config.EndTime.ToString('yyyy/MM/dd HH:mm:ss'))"
    Write-Host "def Policy    : $POLICY" -ForegroundColor Yellow
    Write-Host "def RunDir    : $($State.RunDir)"
    Write-Host "def Accelerators: $(@($ACCELERATORS | Where-Object { $_.ENABLED }).Count)/15 enabled" -ForegroundColor Green
    Write-Host ''

    try {
        def_ShowProgress -Percent 1 -Stage 'FORGE_PANORAMA' -Status 'Resolving VIA Forge static capabilities'
        def_RunForgeStaticIntegration
        def_FlushErrors
        Write-Host "def Forge Root   : $($State.ForgeRoot)"
        Write-Host "def Python       : $($State.PythonExe)"
        Write-Host 'def Forge Gate   : static only / no import / no target execution' -ForegroundColor Yellow
        Write-Host ''

        def_ShowProgress -Percent 11 -Stage 'CONNECT' -Status 'Connecting Classic Outlook'
        def_WriteHeartbeat -Message 'Connecting Classic Outlook'

        $connection = def_ConnectClassicOutlook
        $outlook = $connection.OUTLOOK
        $namespace = $connection.NAMESPACE

        def_ShowProgress -Percent 12 -Stage 'INVENTORY' -Status 'Building folder plan'
        def_BuildFolderPlan -Namespace $namespace
        def_FlushErrors

        Write-Host "def Stores planned : $($State.StoreCount)"
        Write-Host "def Folders planned: $($State.PlannedFolderCount)"
        Write-Host ''

        def_WriteCheckpoint -Completed $false -Message 'Folder inventory completed'

        def_ShowProgress -Percent 20 -Stage 'SCAN' -Status 'Starting folder scan'
        def_ScanFolderPlan -Namespace $namespace

        def_ShowProgress -Percent 76 -Stage 'WORKOPS_INTELLIGENCE' -Status 'Discovering keywords, clusters, projects and pending responses'
        def_RunMailIntelligence
        def_FlushErrors

        def_ShowProgress -Percent 97 -Stage 'FINALIZE' -Status 'Writing manifest and report'
        def_EnsureOutputHeaders

        $completed = $true
        def_WriteCheckpoint -Completed $true -Message 'Scan completed'
        $summary = def_WriteFinalManifest -Completed $true

        def_ShowProgress -Percent 98 -Stage 'REPORT' -Status 'Building HTML report'
        def_WriteHtmlReport -Summary $summary

        def_ShowProgress -Percent 100 -Stage 'COMPLETE' -Status 'Completed'
        def_WriteHeartbeat -Message 'Completed'

        Write-Progress -Id 2 -ParentId 1 -Activity '目前資料夾' -Completed
        Write-Progress -Id 1 -Activity 'VIA WorkOps · Outlook 唯讀掃描' -Completed

        Write-Host ''
        Write-Host 'def SCAN COMPLETE' -ForegroundColor Green
        Write-Host "def Stores       : $($State.StoreCount)"
        Write-Host "def Folders      : $($State.CompletedFolderCount)/$($State.PlannedFolderCount)"
        Write-Host "def Item Refs    : $($State.ScannedItemReferenceCount)"
        Write-Host "def Mail Rows    : $($State.MatchedMailCount)"
        Write-Host "def Errors       : $($State.ErrorCount)"
        Write-Host "def Elapsed      : $(def_GetElapsedText)"
        Write-Host "def Mail CSV     : $($State.MailCsv)"
        Write-Host "def Folder Audit : $($State.FolderCsv)"
        Write-Host "def Report       : $($State.ReportHtml)"
        Write-Host "def Accelerators : $($State.AcceleratorCsv)"
        Write-Host "def Forge Matrix : $($State.ForgeCapabilityCsv)"
        Write-Host "def Keywords     : $($State.KeywordDictionaryCsv)"
        Write-Host "def Project Review: $($State.ProjectCandidateCsv)"
        Write-Host "def Pending P1   : $($State.PendingResponseCsv)"
        Write-Host "def Process Mining: $($State.ProcessMiningCsv)"
        Write-Host "def Controlling  : $($State.ControllingCsv)"
        Write-Host ''

        if ($Config.OpenReport -and (Test-Path -LiteralPath $State.ReportHtml)) {
            Start-Process -FilePath $State.ReportHtml
        }
    }
    catch {
        def_AddError -Stage 'FATAL_SAFE_CATCH' -StoreName $State.CurrentStore -FolderPath $State.CurrentFolder -Message $_.Exception.Message
        def_FlushErrors

        if (-not [string]::IsNullOrWhiteSpace($State.CheckpointJson)) {
            try { def_WriteCheckpoint -Completed $false -Message ('Interrupted safely: ' + $_.Exception.Message) } catch {}
        }

        if (-not [string]::IsNullOrWhiteSpace($State.ManifestJson)) {
            try { [void](def_WriteFinalManifest -Completed $false) } catch {}
        }

        Write-Progress -Id 2 -ParentId 1 -Activity '目前資料夾' -Completed
        Write-Progress -Id 1 -Activity 'VIA WorkOps · Outlook 唯讀掃描' -Completed

        Write-Host ''
        Write-Host 'def FATAL SAFE CATCH' -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
        Write-Host 'def 已完成資料夾已寫入 checkpoint；重新執行相同時間範圍可續跑。' -ForegroundColor Yellow
        Write-Host 'def No Outlook item was modified.' -ForegroundColor Yellow
        throw
    }
    finally {
        def_ReleaseComObject -ComObject $namespace
        def_ReleaseComObject -ComObject $outlook

        [GC]::Collect()
        [GC]::WaitForPendingFinalizers()

        def_ReleaseSingleInstanceLock
    }
}

try {
    def_Main
}
catch {
    # 外層只保留錯誤碼與畫面，不重複執行主流程。
}
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
