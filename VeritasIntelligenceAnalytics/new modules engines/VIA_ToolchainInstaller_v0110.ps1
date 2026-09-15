#requires -Version 7.0
param(
    [string]$Source      = 'C:\Users\tonyk\Downloads',
    [string]$Destination = 'C:\VeritasIntelligenceAnalytics\CGE',
    [switch]$Install,
    [switch]$Copy,
    [switch]$DeleteDuplicates,
    [switch]$NoBrowser
)

# ============================================================
# VIA Toolchain Installer v0110
#
# 把散在 Downloads 的 VIA_* 工具收進固定的工具樹，並且順手擋掉兩件事：
#
#   1. **舊版不准進場。** 同一支工具有 v0100 與 v0110 時只安裝高版，
#      舊版直接進 _superseded\ —— VIA_VersionGuard_v0100 就是造成
#      母系統檔案被誤搬的那一版，它不該留在工具目錄裡。
#   2. **(1) 副本以內容雜湊判定。** 內容相同就是重複，只留一份；
#      內容不同代表是兩個東西，兩份都留並標記，不自動選。
#      -DeleteDuplicates 會把「雜湊完全相同」的副本送進資源回收筒
#      （不是永久刪除，撈得回來）；內容不同的一律不刪。
#   3. **能力盤點。** 掃過安裝好的工具，回報自動編號、SSOT、Regex、
#      同義字、參數整合、下行派工這幾項能力各由誰提供、有沒有缺。
#
# 另外會比對已知工具名冊，列出**你手上缺哪幾支**。
#
# 安裝後的結構：
#   <Destination>\tools\        所有引擎
#   <Destination>\configs\      設定與台帳
#   <Destination>\out\ logs\ plans\
#   <Destination>\_superseded\  被取代的舊版（保留不刪）
#   <Destination>\Invoke-VIA.ps1  指令索引
#
# 預設 dry-run。-Install 才會真的動；-Copy 改為複製而非搬移。
# ============================================================

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Script:Stamp = (Get-Date).ToString('yyyyMMdd_HHmmss')

# ------------------------------------------------------------
# 已知工具名冊：檔名前綴 -> 域 / 用途 / 目前應有的版本
# ------------------------------------------------------------
$Roster = @(
    [pscustomobject]@{ stem='VIA_Central_Governance_Console';      latest='v0600'; domain='治理'; role='PowerShell 全景治理主控台（URN 台帳、Gate）'; runtime='pwsh' }
    [pscustomobject]@{ stem='VIA_CentralGovernanceConsole';        latest='';      domain='治理'; role='純 Python 中央總管 VIA-SYS-MGR-001'; runtime='python' }
    [pscustomobject]@{ stem='VIA_DownwardController';              latest='';      domain='編排'; role='自動下行控制層，把各能力依拓撲派工'; runtime='python' }
    [pscustomobject]@{ stem='VIA_FilePriorityRouter';              latest='';      domain='檔案'; role='L0 掃描 + L1 格式路由 + 優先序引擎'; runtime='python' }
    [pscustomobject]@{ stem='VIA_EnvManager_UnifiedGovernance';    latest='v0110'; domain='環境'; role='venv 治理（PEP508 標記、LKGC、uv 仲裁）'; runtime='pwsh' }
    [pscustomobject]@{ stem='VIA_EnvDeepProbe';                    latest='';      domain='環境'; role='環境深層探測，20 道故障'; runtime='python' }
    [pscustomobject]@{ stem='VIA_Round1_CodeRepair';               latest='v0100'; domain='修復'; role='ruff/PSSA/AST 一輪修復，指紋回滾'; runtime='pwsh' }
    [pscustomobject]@{ stem='VIA_Polyglot_Repair_Injector';        latest='v0100'; domain='修復'; role='Celeritas/NetSupport/Codex 橋注入'; runtime='pwsh' }
    [pscustomobject]@{ stem='VIA_Profile_Doctor';                  latest='v0100'; domain='終端'; role='$PROFILE 修復與啟動耗時分解'; runtime='pwsh' }
    [pscustomobject]@{ stem='VIA_SupportiveModules_Classifier';    latest='v0100'; domain='分析'; role='控管 vs 引擎判定'; runtime='pwsh' }
    [pscustomobject]@{ stem='VIA_AuthorityAudit';                  latest='';      domain='分析'; role='JSON 參數整合去重 + 控制層識別'; runtime='python' }
    [pscustomobject]@{ stem='VIA_EngineHardening';                 latest='';      domain='分析'; role='三引擎硬化稽核，60 種故障'; runtime='python' }
    [pscustomobject]@{ stem='VIA_VRN_FinancialRowAuditor';         latest='';      domain='VRN';  role='財務列原子性與假綠燈稽核'; runtime='python' }
    [pscustomobject]@{ stem='VIA_TestAccelerator';                 latest='';      domain='測試'; role='判定/回歸/閃爍/人工驗收'; runtime='python' }
    [pscustomobject]@{ stem='VIA_VersionGuard';                    latest='v0110'; domain='維運'; role='同族多版本收斂（v0110 修掉誤搬）'; runtime='pwsh' }
    [pscustomobject]@{ stem='VIA_Recover';                         latest='v0110'; domain='維運'; role='隔離區定位與還原（v0110 修掉路徑壓平）'; runtime='pwsh' }
    [pscustomobject]@{ stem='VIA_SameNameConsolidator';            latest='v0110'; domain='維運'; role='同名檔整併，SHRANK 偵測'; runtime='pwsh' }
    [pscustomobject]@{ stem='VIA_Launch_NonBlocking';              latest='v0100'; domain='維運'; role='非阻塞啟動器與動態進度條'; runtime='pwsh' }
    [pscustomobject]@{ stem='VIA_ToolchainInstaller';              latest='v0100'; domain='維運'; role='本安裝器'; runtime='pwsh' }
)

function Get-Stem {
    param([string]$Name)
    $base = [regex]::Replace($Name, '\.(ps1|psm1|py|pyw|md)$', '', 'IgnoreCase')
    $base = [regex]::Replace($base, '\s*\(\d+\)\s*$', '')
    $base = [regex]::Replace($base, '\s*-\s*複製$', '')
    $base = [regex]::Replace($base, '[_-]v\d{2,4}[A-Za-z]?$', '', 'IgnoreCase')
    return $base.Trim()
}

function Get-VersionRank {
    param([string]$Name)
    $m = [regex]::Match($Name, '[_-]v(\d{2,4})([A-Za-z]?)(?=$|[_.\s(])', 'IgnoreCase')
    if (-not $m.Success) { return 0 }
    $suffix = 0
    if ($m.Groups[2].Value) { $suffix = [int][char]($m.Groups[2].Value.ToUpperInvariant()[0]) - 64 }
    return ([int]$m.Groups[1].Value * 100) + $suffix
}

function Get-Hash16 {
    param([string]$Path)
    try {
        $sha = [System.Security.Cryptography.SHA256]::Create()
        $stream = [System.IO.File]::OpenRead($Path)
        try { $bytes = $sha.ComputeHash($stream) } finally { $stream.Dispose(); $sha.Dispose() }
        return ([System.BitConverter]::ToString($bytes).Replace('-', '').Substring(0, 16).ToLowerInvariant())
    } catch { return 'HASH_FAIL' }
}

function Test-Parses {
    param([string]$Path)
    $ext = [System.IO.Path]::GetExtension($Path).ToLowerInvariant()
    if ($ext -eq '.ps1' -or $ext -eq '.psm1') {
        $tokens = $null; $errs = $null
        try {
            $null = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errs)
            return ($null -eq $errs -or $errs.Count -eq 0)
        } catch { return $false }
    }
    if ($ext -eq '.py') {
        $py = Get-Command 'python' -ErrorAction SilentlyContinue
        if ($null -eq $py) { $py = Get-Command 'python3' -ErrorAction SilentlyContinue }
        if ($null -eq $py) { return $true }
        $psi = [System.Diagnostics.ProcessStartInfo]::new()
        $psi.FileName = $py.Source
        $psi.Arguments = ('-m py_compile "' + $Path + '"')
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $false
        $psi.RedirectStandardError = $false
        $psi.CreateNoWindow = $true
        try {
            $proc = [System.Diagnostics.Process]::Start($psi)
            if (-not $proc.WaitForExit(20000)) { $proc.Kill($true); return $false }
            return ($proc.ExitCode -eq 0)
        } catch { return $false }
    }
    return $true
}

Write-Host ''
Write-Host '  VIA TOOLCHAIN INSTALLER v0110' -ForegroundColor Cyan
Write-Host ('  來源 ' + $Source) -ForegroundColor DarkGray
Write-Host ('  目標 ' + $Destination) -ForegroundColor DarkGray
Write-Host ''

if (-not (Test-Path -LiteralPath $Source)) {
    Write-Host ('  來源不存在：' + $Source) -ForegroundColor Red
    return
}

# ------------------------------------------------------------
# 1. 掃描來源
# ------------------------------------------------------------
$candidates = @(Get-ChildItem -LiteralPath $Source -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '(?i)^VIA[_-]' -and $_.Extension -match '(?i)^\.(ps1|psm1|py|md)$' })

if ($candidates.Count -eq 0) {
    Write-Host '  來源沒有任何 VIA_* 工具檔' -ForegroundColor Yellow
    return
}

$families = @{}
foreach ($file in $candidates) {
    $stem = Get-Stem -Name $file.Name
    $key = ($stem + '|' + $file.Extension).ToLowerInvariant()
    if (-not $families.ContainsKey($key)) { $families[$key] = [System.Collections.Generic.List[object]]::new() }
    $families[$key].Add([pscustomobject]@{
        name = $file.Name; path = $file.FullName; stem = $stem
        ext = $file.Extension.ToLowerInvariant()
        rank = (Get-VersionRank -Name $file.Name)
        dupmark = $(if ($file.Name -match '\(\d+\)|複製|(?i)[ _-]copy\.') { 1 } else { 0 })
        mtime = $file.LastWriteTime; size = $file.Length
        hash = (Get-Hash16 -Path $file.FullName)
    })
}

# ------------------------------------------------------------
# 2. 選版 + 去重
# ------------------------------------------------------------
$plan = [System.Collections.Generic.List[object]]::new()
foreach ($key in ($families.Keys | Sort-Object)) {
    $members = @($families[$key] | Sort-Object -Property @{ e='rank'; desc=$true }, @{ e='dupmark'; desc=$false }, @{ e='mtime'; desc=$true })
    $keep = $members[0]
    $keepOk = Test-Parses -Path $keep.path
    foreach ($member in $members) {
        $verdict = 'SUPERSEDED'
        $note = ''
        if ($member.path -eq $keep.path) {
            $verdict = 'INSTALL'
            $note = $(if ($keepOk) { '語法通過' } else { '語法未通過，仍安裝但請先查' })
        } elseif ($member.hash -eq $keep.hash) {
            $verdict = 'DUPLICATE'
            $note = '與安裝版內容完全相同'
        } elseif (-not $keepOk) {
            $verdict = 'KEPT_FALLBACK'
            $note = '高版無法解析，此版保留為後援'
        } else {
            $note = '較舊版本'
        }
        $plan.Add([pscustomobject]@{
            stem = $member.stem; name = $member.name; verdict = $verdict
            rank = $member.rank; hash = $member.hash
            mtime = $member.mtime.ToString('yyyy-MM-dd HH:mm'); size = $member.size
            note = $note; path = $member.path
        })
    }
}

# ------------------------------------------------------------
# 3. 對照名冊：缺哪幾支、手上是不是舊版
# ------------------------------------------------------------
$haveStems = @{}
foreach ($row in ($plan | Where-Object { $_.verdict -eq 'INSTALL' })) { $haveStems[$row.stem.ToLowerInvariant()] = $row }
$rosterRows = [System.Collections.Generic.List[object]]::new()
foreach ($entry in $Roster) {
    $key = $entry.stem.ToLowerInvariant()
    $state = 'MISSING'
    $found = ''
    $stale = ''
    if ($haveStems.ContainsKey($key)) {
        $row = $haveStems[$key]
        $found = $row.name
        $state = 'PRESENT'
        if ($entry.latest) {
            $want = Get-VersionRank -Name ('x_' + $entry.latest)
            if ($row.rank -lt $want) { $state = 'OUTDATED'; $stale = '應為 ' + $entry.latest }
        }
    }
    $rosterRows.Add([pscustomobject]@{
        domain = $entry.domain; stem = $entry.stem; state = $state
        have = $found; want = $entry.latest; note = ($stale + ' ' + $entry.role).Trim()
        runtime = $entry.runtime
    })
}

# 名冊說有更新版的，一律不進 tools\ —— 舊版工具就是上次誤搬母系統檔案的原因。
foreach ($row in $rosterRows) {
    if ($row.state -ne 'OUTDATED') { continue }
    foreach ($item in $plan) {
        if ($item.verdict -eq 'INSTALL' -and $item.name -eq $row.have) {
            $item.verdict = 'OUTDATED_PARK'
            $item.note = '名冊要求 ' + $row.want + '，此版不進工具目錄'
        }
    }
}

foreach ($group in ($plan | Group-Object -Property verdict)) {
    $color = 'DarkGray'
    if ($group.Name -eq 'INSTALL') { $color = 'Green' }
    if ($group.Name -eq 'SUPERSEDED') { $color = 'Yellow' }
    if ($group.Name -eq 'DUPLICATE') { $color = 'DarkYellow' }
    if ($group.Name -eq 'KEPT_FALLBACK') { $color = 'Red' }
    if ($group.Name -eq 'OUTDATED_PARK') { $color = 'Red' }
    Write-Host ('  [' + $group.Name + '] ' + $group.Count + ' 個') -ForegroundColor $color
    foreach ($row in $group.Group) {
        Write-Host ('     ' + $row.name.PadRight(52) + $row.note) -ForegroundColor DarkGray
    }
    Write-Host ''
}

$missing = @($rosterRows | Where-Object { $_.state -eq 'MISSING' })
$outdated = @($rosterRows | Where-Object { $_.state -eq 'OUTDATED' })
if ($outdated.Count -gt 0) {
    Write-Host ('  手上是舊版的 ' + $outdated.Count + ' 支：') -ForegroundColor Red
    foreach ($row in $outdated) { Write-Host ('     ' + $row.have + '  ->  ' + $row.note) -ForegroundColor Red }
    Write-Host ''
}
if ($missing.Count -gt 0) {
    Write-Host ('  名冊上但你手上沒有的 ' + $missing.Count + ' 支：') -ForegroundColor Yellow
    foreach ($row in $missing) {
        Write-Host ('     [' + $row.domain + '] ' + $row.stem.PadRight(38) + $row.note) -ForegroundColor Yellow
    }
    Write-Host ''
}

# ------------------------------------------------------------
# 3b. 能力盤點：這批工具到底具備哪些引擎能力
# ------------------------------------------------------------
$Capabilities = @(
    [pscustomobject]@{ id='C1'; name='自動編號引擎'; patterns=@('URNAuthority','VIA-%s-%s-%04d','issued_this_run','via_console_registry','urn_registry'); note='永久 URN 配發、只增不減、冪等' }
    [pscustomobject]@{ id='C2'; name='SSOT 台帳'; patterns=@('append-only','RegistryEntry','registry_version','VIA.URNRegistry'); note='實體登記與狀態機' }
    [pscustomobject]@{ id='C3'; name='Regex SSOT'; patterns=@('build_regex','regex_auto','regex_curated','selftest'); note='每 canonical 交替式 + 自我測試' }
    [pscustomobject]@{ id='C4'; name='同義字自適應'; patterns=@('SynonymSSOT','ask_queue','QUARANTINE','difflib.SequenceMatcher'); note='AUTO/ASK/QUARANTINE 三段分級' }
    [pscustomobject]@{ id='C5'; name='參數整合去重'; patterns=@('ParameterSSOT','via_parameters_ssot','CONFLICT'); note='跨檔案參數一致性裁決' }
    [pscustomobject]@{ id='C6'; name='自動向下派工'; patterns=@('topological_levels','DownwardController','CapabilityRegistry'); note='依相依拓撲下行' }
    [pscustomobject]@{ id='C7'; name='介面契約比對'; patterns=@('ContractGovernor','CONTRACT_MATCHES_SOURCE'); note='宣告 vs 原始碼' }
    [pscustomobject]@{ id='C8'; name='台股代號鎖'; patterns=@('TW_TICKER_LOCK','tw_stock_registry','LOCK_SELF_HEALED'); note='三式代號鎖定與竄改自癒' }
    [pscustomobject]@{ id='C9'; name='時間語彙正規化'; patterns=@('normalize_temporal','NS_TEMPORAL','民國'); note='民國/季/半年/FY 正規化' }
    [pscustomobject]@{ id='C10'; name='確認回饋迴路'; patterns=@('CGE-CONFIRM','confirmations.jsonl','VIA-UAT'); note='人工裁決回寫，M/P 升 V' }
)
$capRows = [System.Collections.Generic.List[object]]::new()
$installTargets = @($plan | Where-Object { $_.verdict -eq 'INSTALL' })
foreach ($cap in $Capabilities) {
    $providers = [System.Collections.Generic.List[string]]::new()
    $hits = 0
    foreach ($row in $installTargets) {
        $text = ''
        try { $text = [System.IO.File]::ReadAllText($row.path) } catch { continue }
        $matched = 0
        foreach ($pattern in $cap.patterns) {
            if ($text.Contains($pattern)) { $matched++ }
        }
        if ($matched -gt 0) {
            $providers.Add($row.name + '(' + $matched + '/' + $cap.patterns.Count + ')')
            $hits += $matched
        }
    }
    $state = 'ABSENT'
    if ($providers.Count -gt 0) {
        $best = 0
        foreach ($row in $installTargets) {
            $text = ''
            try { $text = [System.IO.File]::ReadAllText($row.path) } catch { continue }
            $matched = 0
            foreach ($pattern in $cap.patterns) { if ($text.Contains($pattern)) { $matched++ } }
            if ($matched -gt $best) { $best = $matched }
        }
        $state = $(if ($best -ge [math]::Ceiling($cap.patterns.Count / 2)) { 'PRESENT' } else { 'PARTIAL' })
    }
    $capRows.Add([pscustomobject]@{
        id = $cap.id; name = $cap.name; state = $state
        providers = (($providers | Select-Object -First 3) -join '、')
        note = $cap.note
    })
}
Write-Host '  能力盤點' -ForegroundColor Cyan
foreach ($row in $capRows) {
    $color = 'DarkYellow'
    if ($row.state -eq 'PRESENT') { $color = 'Green' }
    if ($row.state -eq 'ABSENT') { $color = 'Red' }
    Write-Host ('    ' + $row.id.PadRight(4) + $row.name.PadRight(16) + $row.state.PadRight(9) +
                $(if ($row.providers) { $row.providers } else { $row.note })) -ForegroundColor $color
}
Write-Host ''

# ------------------------------------------------------------
# 4. 安裝
# ------------------------------------------------------------
$installed = 0
$parked = 0
$recycled = 0
if ($Install) {
    foreach ($sub in @('tools', 'configs', 'out', 'logs', 'plans', '_superseded')) {
        $dir = Join-Path $Destination $sub
        if (-not (Test-Path -LiteralPath $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
    }
    $toolsDir = Join-Path $Destination 'tools'
    $parkDir = Join-Path $Destination '_superseded'
    foreach ($row in $plan) {
        $target = $(if ($row.verdict -eq 'INSTALL') { Join-Path $toolsDir $row.name } else { Join-Path $parkDir $row.name })
        if (Test-Path -LiteralPath $target) {
            $existing = Get-Hash16 -Path $target
            if ($existing -eq $row.hash) {
                Write-Host ('    [已存在且相同] ' + $row.name) -ForegroundColor DarkGray
                continue
            }
            $target = Join-Path (Split-Path $target -Parent) (
                [System.IO.Path]::GetFileNameWithoutExtension($row.name) + '_' + $Script:Stamp +
                [System.IO.Path]::GetExtension($row.name))
        }
        if ($row.verdict -eq 'DUPLICATE' -and $DeleteDuplicates) {
            # 只有雜湊完全相同的副本才會走到這裡；送資源回收筒而非永久刪除
            try {
                Add-Type -AssemblyName Microsoft.VisualBasic -ErrorAction Stop
                [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile(
                    $row.path,
                    [Microsoft.VisualBasic.FileIO.UIOption]::OnlyErrorDialogs,
                    [Microsoft.VisualBasic.FileIO.RecycleOption]::SendToRecycleBin)
                $recycled++
                Write-Host ('    [回收筒] ' + $row.name) -ForegroundColor DarkYellow
            } catch {
                Move-Item -LiteralPath $row.path -Destination $target -Force
                $parked++
                Write-Host ('    [收存（無法送回收筒）] ' + $row.name) -ForegroundColor DarkYellow
            }
            continue
        }
        if ($Copy) { Copy-Item -LiteralPath $row.path -Destination $target -Force }
        else { Move-Item -LiteralPath $row.path -Destination $target -Force }
        if ($row.verdict -eq 'INSTALL') { $installed++; Write-Host ('    [安裝] ' + $row.name) -ForegroundColor Green }
        else { $parked++; Write-Host ('    [收存] ' + $row.name) -ForegroundColor DarkYellow }
    }

    # 指令索引
    $index = [System.Collections.Generic.List[string]]::new()
    $index.Add('#requires -Version 7.0')
    $index.Add('param([string]$Tool = "")')
    $index.Add('# VIA 工具索引 —— 產生於 ' + $Script:Stamp)
    $index.Add('$ToolsDir = "' + (Join-Path $Destination 'tools').Replace('"', '`"') + '"')
    $index.Add('$Catalog = @(')
    foreach ($entry in $Roster) {
        $row = $null
        if ($haveStems.ContainsKey($entry.stem.ToLowerInvariant())) { $row = $haveStems[$entry.stem.ToLowerInvariant()] }
        $file = $(if ($row) { $row.name } else { '' })
        $index.Add('  [pscustomobject]@{ Domain = ''' + $entry.domain + '''; Tool = ''' + $entry.stem +
                   '''; File = ''' + $file + '''; Runtime = ''' + $entry.runtime +
                   '''; Role = ''' + $entry.role.Replace("'", "''") + ''' }')
    }
    $index.Add(')')
    $index.Add('if (-not $Tool) {')
    # Format-Table -AutoSize 在沒有主控台寬度的環境（重導向、CI）會輸出空白，
    # 所以自己排版，不依賴主機的格式化器。
    $index.Add('    Write-Host ""')
    $index.Add('    Write-Host ("  {0,-6} {1,-38} {2,-9} {3}" -f "域","工具","執行期","狀態") -ForegroundColor DarkGray')
    $index.Add('    foreach ($row in ($Catalog | Sort-Object Domain, Tool)) {')
    $index.Add('        $state = if ($row.File) { "已安裝" } else { "未安裝" }')
    $index.Add('        $color = if ($row.File) { "Green" } else { "DarkYellow" }')
    $index.Add('        Write-Host ("  {0,-6} {1,-38} {2,-9} {3}" -f $row.Domain, $row.Tool, $row.Runtime, $state) -ForegroundColor $color')
    $index.Add('        Write-Host ("         " + $row.Role) -ForegroundColor DarkGray')
    $index.Add('    }')
    $index.Add('    Write-Host ""')
    $index.Add('    Write-Host "  用法： .\Invoke-VIA.ps1 <工具名片段> [該工具的參數]" -ForegroundColor Cyan')
    $index.Add('    return')
    $index.Add('}')
    $index.Add('$hit = @($Catalog | Where-Object { $_.Tool -like ("*" + $Tool + "*") -and $_.File })')
    $index.Add('if ($hit.Count -eq 0) { Write-Host "找不到，或該工具尚未安裝" -ForegroundColor Yellow; return }')
    $index.Add('$path = Join-Path $ToolsDir $hit[0].File')
    $index.Add('if ($hit[0].Runtime -eq "python") { & python $path @args } else { & pwsh -NoProfile -ExecutionPolicy Bypass -File $path @args }')
    [System.IO.File]::WriteAllText((Join-Path $Destination 'Invoke-VIA.ps1'),
        (($index -join "`n") + "`n"), [System.Text.UTF8Encoding]::new($false))
} else {
    Write-Host '  這是 DRY-RUN。確認上面清單後加 -Install 才會建立工具樹並搬移。' -ForegroundColor Yellow
    Write-Host '  想保留 Downloads 的原檔就再加 -Copy。' -ForegroundColor Yellow
}

# ------------------------------------------------------------
# 5. 報告
# ------------------------------------------------------------
$reportDir = Join-Path $Destination 'out'
if (-not (Test-Path -LiteralPath $reportDir)) { New-Item -Path $reportDir -ItemType Directory -Force | Out-Null }
$jsonPath = Join-Path $reportDir ('toolchain_install_' + $Script:Stamp + '.json')
[System.IO.File]::WriteAllText($jsonPath, (([ordered]@{
    tool = 'VIA_ToolchainInstaller'; version = 'v0110'; stamp = $Script:Stamp
    source = $Source; destination = $Destination
    installed = $installed; parked = $parked; recycled = $recycled
    committed = $Install.IsPresent; delete_duplicates = $DeleteDuplicates.IsPresent
    plan = @($plan); roster = @($rosterRows); capabilities = @($capRows)
} | ConvertTo-Json -Depth 6)), [System.Text.UTF8Encoding]::new($false))

Write-Host '  ============================================================' -ForegroundColor DarkGray
Write-Host ('   來源 ' + $candidates.Count + ' 檔｜可安裝 ' +
            @($plan | Where-Object { $_.verdict -eq 'INSTALL' }).Count +
            '｜舊版 ' + @($plan | Where-Object { $_.verdict -eq 'SUPERSEDED' }).Count +
            '｜重複 ' + @($plan | Where-Object { $_.verdict -eq 'DUPLICATE' }).Count +
            '｜名冊缺 ' + $missing.Count)
if ($Install) { Write-Host ('   已安裝 ' + $installed + '，收存 ' + $parked + '，送回收筒 ' + $recycled) -ForegroundColor Green }
if (-not $DeleteDuplicates -and @($plan | Where-Object { $_.verdict -eq 'DUPLICATE' }).Count -gt 0) {
    Write-Host '   內容相同的副本預設只收存不刪；要刪請加 -DeleteDuplicates（送資源回收筒）' -ForegroundColor Yellow
}
Write-Host ('   報告：' + $jsonPath) -ForegroundColor DarkCyan
Write-Host '  ============================================================' -ForegroundColor DarkGray
