#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

$Root = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
$Ts = Get-Date -Format "yyyyMMdd_HHmmss"

$Run        = Join-Path $Root "_via_guarded_root_entry_promotion_runs\RUN_${Ts}_v0357_GUARDED_ROOT_ENTRY_PROMOTION_GATE"
$ReportDir  = Join-Path $Run "report"
$RuntimeDir = Join-Path $Run "runtime"
$RegDir     = Join-Path $Run "registry"
$CmdDir     = Join-Path $Run "commands"
$SealDir    = Join-Path $Run "seal"
$StdoutDir  = Join-Path $Run "stdout"
$DraftDir   = Join-Path $Run "drafts"

$OpenHtml = $true
$MinFreeLightGB = 12
$MinFreeFullGB = 25

$ExpectedVdfEntry   = Join-Path $Root "functional modules\VDF\Invoke-VDF.ps1"
$ExpectedNexusEntry = Join-Path $Root "supportive modules\Invoke-VeritasNexusCore.ps1"
$ExpectedViaEntry   = Join-Path $Root "Invoke-VIA.ps1"
$ExpectedVrnEntry   = Join-Path $Root "functional modules\VRN\Invoke-VRN.ps1"

foreach($d in @($Run,$ReportDir,$RuntimeDir,$RegDir,$CmdDir,$SealDir,$StdoutDir,$DraftDir)){
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}

function Show-Step {
    param([int]$Pct,[string]$Text)
    if($Pct -lt 0){$Pct=0}
    if($Pct -gt 100){$Pct=100}
    Write-Progress -Activity "VIA v035.7 Guarded Root Entry Promotion Gate" -Status $Text -PercentComplete $Pct
    $bar=("█"* [int]($Pct/5)).PadRight(20,"░")
    Write-Host ("[{0,3}%] [{1}] {2}" -f $Pct,$bar,$Text) -ForegroundColor Cyan
}

function Enc {
    param([AllowNull()][object]$Value)
    if($null -eq $Value){return ""}
    return [System.Net.WebUtility]::HtmlEncode([string]$Value)
}

function Write-Utf8 {
    param([string]$Path,[string]$Text)
    $parent = Split-Path -Parent $Path
    if(-not(Test-Path -LiteralPath $parent)){ New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    [System.IO.File]::WriteAllText($Path,$Text,[System.Text.UTF8Encoding]::new($false))
}

function FmtBytes {
    param([AllowNull()][object]$Bytes)
    if($null -eq $Bytes){return "0 B"}
    $x=0.0
    if(-not [double]::TryParse(([string]$Bytes),[ref]$x)){return [string]$Bytes}
    if($x -ge 1GB){return "{0:N2} GB" -f ($x/1GB)}
    if($x -ge 1MB){return "{0:N2} MB" -f ($x/1MB)}
    if($x -ge 1KB){return "{0:N2} KB" -f ($x/1KB)}
    return "{0:N0} B" -f $x
}

function Find-Browser {
    $pf86=[Environment]::GetEnvironmentVariable("ProgramFiles(x86)")
    $items=@(
        "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
        "$pf86\Microsoft\Edge\Application\msedge.exe",
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
        "$pf86\Google\Chrome\Application\chrome.exe"
    )
    foreach($p in $items){
        if($p -and (Test-Path -LiteralPath $p -PathType Leaf)){return $p}
    }
    return ""
}

function Get-DriveRows {
    $rows=@()
    Get-PSDrive -PSProvider FileSystem | ForEach-Object {
        $used=0L
        $free=0L
        try { $used=[int64]$_.Used; $free=[int64]$_.Free } catch {}
        $total=$used+$free
        $pct=0.0
        if($total -gt 0){$pct=[math]::Round(($free/$total)*100,2)}
        $risk="LOW"
        if($pct -lt 5){$risk="HIGH"} elseif($pct -lt 12){$risk="MEDIUM"}

        $rows += [pscustomobject]@{
            Drive=$_.Name
            Root=$_.Root
            Used=(FmtBytes $used)
            Free=(FmtBytes $free)
            FreeGB=[math]::Round($free/1GB,2)
            FreePercent=$pct
            Risk=$risk
        }
    }
    return @($rows)
}

function Find-LatestFile {
    param([string]$Base,[string]$Filter)
    if(-not(Test-Path -LiteralPath $Base -PathType Container)){return ""}
    $f=@(
        Get-ChildItem -LiteralPath $Base -Recurse -File -Filter $Filter -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    )
    if(@($f).Count -eq 0){return ""}
    return [string]$f[0].FullName
}

function Load-JsonSafe {
    param([string]$Path)
    if(-not($Path) -or -not(Test-Path -LiteralPath $Path -PathType Leaf)){return $null}
    try { return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json } catch { return $null }
}

function Test-PsSyntax {
    param([string]$Path)
    if(-not(Test-Path -LiteralPath $Path -PathType Leaf)){
        return [pscustomobject]@{Status="WARN"; ErrorCount=0; Message="Missing file."}
    }

    try {
        $tokens=$null
        $errors=$null
        [System.Management.Automation.Language.Parser]::ParseFile($Path,[ref]$tokens,[ref]$errors) | Out-Null
        $n=@($errors).Count
        return [pscustomobject]@{
            Status=($(if($n -eq 0){"OK"}else{"FAIL"}))
            ErrorCount=$n
            Message=($(if($n -eq 0){"No parser errors."}else{(@($errors | Select-Object -First 8 | ForEach-Object Message) -join " | ")}))
        }
    } catch {
        return [pscustomobject]@{Status="FAIL"; ErrorCount=-1; Message=$_.Exception.Message}
    }
}

function New-Row {
    param(
        [string]$Lane,[string]$Round,[string]$Project,[string]$Gate,
        [string]$Status,[string]$Risk,[string]$FixClass,[string]$IssueType,
        [string]$Value,[string]$Message,[string]$Path
    )
    return [pscustomobject]@{
        Lane=$Lane
        Round=$Round
        Project=$Project
        Gate=$Gate
        Status=$Status
        Risk=$Risk
        FixClass=$FixClass
        IssueType=$IssueType
        Value=$Value
        Message=$Message
        Path=$Path
    }
}

function Is-GeneratedPath {
    param([string]$Path)
    if($Path -match "\\_via_"){return $true}
    if($Path -match "\\runs\\RUN_"){return $true}
    if($Path -match "\\sandbox\\"){return $true}
    if($Path -match "\\commands\\"){return $true}
    if($Path -match "\\wrappers\\"){return $true}
    if($Path -match "\\report\\"){return $true}
    if($Path -match "\\runtime\\"){return $true}
    if($Path -match "\\registry\\"){return $true}
    if($Path -match "\\backup|\\archive"){return $true}
    return $false
}

function Score-File {
    param([System.IO.FileInfo]$File,[object]$Syntax,[string]$Kind)

    $score=0
    $n=$File.Name
    $p=$File.FullName

    if(Is-GeneratedPath $p){$score -= 300}
    if($Syntax.Status -eq "OK"){$score += 40}
    if($File.Length -gt 0){$score += 10}
    if($File.Length -gt 2MB){$score -= 30}

    if($Kind -eq "VRN"){
        if($n -ieq "Invoke-VRN.ps1"){$score += 180}
        if($n -match "^Invoke-VRN"){$score += 90}
        if($n -match "VRN"){$score += 40}
        if($n -match "ReportNova|VeritasReportNova"){$score += 35}
        if($p -match "\\functional modules\\VRN\\"){$score += 100}
        if($p -match "\\module\\VRN\\"){$score += 100}
        if($p -match "\\supportive modules\\|\\supportive_module\\"){$score += 30}
    }

    if($Kind -eq "VIA"){
        if($n -ieq "Invoke-VIA.ps1"){$score += 180}
        if($n -match "^Invoke-VIA"){$score += 90}
        if($n -match "VIA|Veritas"){$score += 35}
        if($p -match "\\supportive modules\\|\\supportive_module\\"){$score += 35}
        if($p -match "\\_oneclick\\"){$score -= 20}
    }

    return $score
}

function Discover-Candidates {
    param([string]$Kind)

    $roots=@()
    if($Kind -eq "VRN"){
        $roots += Join-Path $Root "functional modules\VRN"
        $roots += Join-Path $Root "supportive modules"
        $roots += Join-Path $Root "dict\VRN"
        $od = Join-Path $env:USERPROFILE "OneDrive\VeritasIntelligenceAnalytics"
        $roots += Join-Path $od "module\VRN"
        $roots += Join-Path $od "module"
        $roots += Join-Path $od "supportive_module"
        $roots += Join-Path $od "supportive modules"
    } else {
        $roots += $Root
        $roots += Join-Path $Root "supportive modules"
        $roots += Join-Path $Root "_oneclick"
        $od = Join-Path $env:USERPROFILE "OneDrive\VeritasIntelligenceAnalytics"
        $roots += $od
        $roots += Join-Path $od "module"
    }

    $roots=@($roots | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Container) } | Select-Object -Unique)

    $raw=@()
    foreach($r in $roots){
        try {
            $items=@(
                Get-ChildItem -LiteralPath $r -Recurse -File -Filter "*.ps1" -ErrorAction SilentlyContinue |
                Where-Object {
                    $_.FullName -notmatch "\\\.venv\\|\\node_modules\\|\\__pycache__\\|\\_envs\\|\\AppData\\" -and
                    $_.FullName -notmatch "\\report\\|\\runtime\\|\\registry\\|\\commands\\|\\wrappers\\" -and
                    (
                        ($Kind -eq "VRN" -and ($_.Name -match "VRN|ReportNova|Invoke" -or $_.FullName -match "\\VRN\\|ReportNova|VeritasReportNova")) -or
                        ($Kind -eq "VIA" -and ($_.Name -match "VIA|Veritas|Invoke" -or $_.FullName -match "\\VIA\\|Veritas"))
                    )
                } |
                Sort-Object -Property LastWriteTime -Descending |
                Select-Object -First 500
            )
            $raw += $items
        } catch {}
    }

    $seen=@{}
    foreach($f in $raw){
        if($f -and -not $seen.ContainsKey($f.FullName)){
            $seen[$f.FullName]=$f
        }
    }

    $rows=@()
    foreach($f in $seen.Values){
        $syntax=Test-PsSyntax -Path $f.FullName
        $score=Score-File -File $f -Syntax $syntax -Kind $Kind
        $generated=Is-GeneratedPath $f.FullName

        $class="REVIEW"
        if($generated){$class="GENERATED_EXCLUDED"}
        elseif($score -ge 180){$class="REAL_STRONG_CANDIDATE"}
        elseif($score -ge 100){$class="REAL_CANDIDATE"}
        elseif($score -ge 50){$class="WEAK_REAL_CANDIDATE"}
        else{$class="LOW_RELEVANCE"}

        $rows += [pscustomobject]@{
            Kind=$Kind
            CandidateRank=0
            CandidateClass=$class
            Score=$score
            GeneratedPath=$generated
            ParserStatus=$syntax.Status
            ParserErrors=$syntax.ErrorCount
            Bytes=[int64]$f.Length
            Modified=$f.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            Name=$f.Name
            Path=$f.FullName
            Message=$syntax.Message
        }
    }

    $sorted=@($rows | Sort-Object -Property @{Expression='GeneratedPath';Descending=$false}, @{Expression='Score';Descending=$true}, @{Expression='Modified';Descending=$true})
    $rank=0
    foreach($s in $sorted){
        $rank++
        $s.CandidateRank=$rank
    }

    return @($sorted | Select-Object -First 80)
}

function New-GuardedRootWrapperText {
    param([string]$Project,[string]$Candidate,[string]$Expected)

    return @"
#Requires -Version 7.0
Set-StrictMode -Version Latest
`$ErrorActionPreference = "Continue"

# =============================================================================
# VIA v035.7 Guarded Root Entry
# Project   : $Project
# Candidate : $Candidate
# =============================================================================
# Default behavior is SAFE PROBE only.
# Full run requires explicit -Run.
# =============================================================================

param(
    [switch]`$Run,
    [switch]`$SafeProbe,
    [switch]`$Plan
)

`$SelectedCandidate = "$Candidate"
`$ExpectedEntry = "$Expected"

function Write-GuardedLine {
    param([string]`$Level,[string]`$Message)
    `$c="Gray"
    if(`$Level -eq "OK"){`$c="Green"}
    elseif(`$Level -eq "WARN"){`$c="Yellow"}
    elseif(`$Level -eq "FAIL"){`$c="Red"}
    elseif(`$Level -eq "RUN"){`$c="Cyan"}
    Write-Host "[`$(Get-Date -Format 'HH:mm:ss.fff')] [`$Level] `$Message" -ForegroundColor `$c
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "VIA v035.7 · $Project Guarded Root Entry" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

if(-not(Test-Path -LiteralPath `$SelectedCandidate -PathType Leaf)){
    Write-GuardedLine "FAIL" "Selected candidate missing: `$SelectedCandidate"
    return
}

try {
    `$tokens=`$null
    `$errors=`$null
    [System.Management.Automation.Language.Parser]::ParseFile(`$SelectedCandidate,[ref]`$tokens,[ref]`$errors)|Out-Null

    if(@(`$errors).Count -eq 0){
        Write-GuardedLine "OK" "Candidate parser OK."
    } else {
        Write-GuardedLine "FAIL" "Candidate parser errors: `$(@(`$errors).Count)"
        @(`$errors | Select-Object -First 10) | ForEach-Object { Write-GuardedLine "FAIL" `$_.Message }
        return
    }

    `$item=Get-Item -LiteralPath `$SelectedCandidate -Force
    `$hash=(Get-FileHash -LiteralPath `$SelectedCandidate -Algorithm SHA256).Hash
    Write-GuardedLine "OK" "Candidate bytes: `$(`$item.Length)"
    Write-GuardedLine "OK" "Candidate SHA256: `$hash"
} catch {
    Write-GuardedLine "FAIL" `$_.Exception.Message
    return
}

if(`$Plan -or -not `$Run){
    Write-GuardedLine "OK" "SAFE_PROBE_COMPLETE"
    Write-GuardedLine "WARN" "Default mode does not execute candidate. Use -Run only after production approval."
    Write-GuardedLine "WARN" "Expected entry: `$ExpectedEntry"
    return
}

Write-GuardedLine "RUN" "Explicit -Run detected. Invoking selected candidate."
& pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File `$SelectedCandidate @args
"@
}

function Promote-IfMissing {
    param([string]$Project,[string]$Expected,[string]$Candidate)

    $created=$false
    $status="OK"
    $risk="LOW"
    $message="Expected entry already exists. No overwrite."
    $draft=Join-Path $DraftDir "$Project-GuardedRootEntry-DRAFT-v0357.ps1"

    $text=New-GuardedRootWrapperText -Project $Project -Candidate $Candidate -Expected $Expected
    Write-Utf8 -Path $draft -Text $text

    $candidateSyntax=Test-PsSyntax -Path $Candidate
    $draftSyntax=Test-PsSyntax -Path $draft

    if($candidateSyntax.Status -ne "OK" -or $draftSyntax.Status -ne "OK"){
        return [pscustomobject]@{
            Project=$Project; Status="FAIL"; Risk="HIGH"; Created=$false; Message="Candidate or draft parser failed."; Expected=$Expected; Candidate=$Candidate; Draft=$draft
        }
    }

    if(Test-Path -LiteralPath $Expected -PathType Leaf){
        return [pscustomobject]@{
            Project=$Project; Status=$status; Risk=$risk; Created=$false; Message=$message; Expected=$Expected; Candidate=$Candidate; Draft=$draft
        }
    }

    try {
        $parent=Split-Path -Parent $Expected
        if(-not(Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Force -Path $parent | Out-Null}
        Write-Utf8 -Path $Expected -Text $text
        $created=$true
        $status="OK"
        $risk="LOW"
        $message="Guarded root entry created because it was missing. Default mode is safe probe only."
    } catch {
        $status="FAIL"
        $risk="HIGH"
        $message=$_.Exception.Message
    }

    return [pscustomobject]@{
        Project=$Project
        Status=$status
        Risk=$risk
        Created=$created
        Message=$message
        Expected=$Expected
        Candidate=$Candidate
        Draft=$draft
    }
}

function New-ThreeStreamCommands {
    param([string]$Project,[string]$Target)

    $dir=Join-Path $CmdDir $Project
    New-Item -ItemType Directory -Force -Path $dir | Out-Null

    $parser=Join-Path $dir "$Project`_01_ParserOnly.ps1"
    $hash=Join-Path $dir "$Project`_02_MetadataHash.ps1"
    $surface=Join-Path $dir "$Project`_03_SurfaceScan.ps1"

    Write-Utf8 -Path $parser -Text @"
`$Target = "$Target"
if(-not `$Target -or -not(Test-Path -LiteralPath `$Target -PathType Leaf)){ Write-Host "[WARN] Missing target: `$Target" -ForegroundColor Yellow; return }
`$tokens=`$null; `$errors=`$null
[System.Management.Automation.Language.Parser]::ParseFile(`$Target,[ref]`$tokens,[ref]`$errors)|Out-Null
if(@(`$errors).Count -eq 0){ Write-Host "[OK] ParserOnly passed." -ForegroundColor Green } else { Write-Host "[FAIL] Parser errors: `$(@(`$errors).Count)" -ForegroundColor Red; @(`$errors | Select-Object -First 10) | ForEach-Object { Write-Host `$_.Message -ForegroundColor Red } }
"@

    Write-Utf8 -Path $hash -Text @"
`$Target = "$Target"
if(-not `$Target -or -not(Test-Path -LiteralPath `$Target -PathType Leaf)){ Write-Host "[WARN] Missing target: `$Target" -ForegroundColor Yellow; return }
`$item=Get-Item -LiteralPath `$Target -Force
`$sha=(Get-FileHash -LiteralPath `$Target -Algorithm SHA256).Hash
Write-Host "[OK] MetadataHash passed." -ForegroundColor Green
Write-Host "Path  : `$Target"
Write-Host "Bytes : `$(`$item.Length)"
Write-Host "SHA256: `$sha"
"@

    Write-Utf8 -Path $surface -Text @"
`$Target = "$Target"
if(-not `$Target -or -not(Test-Path -LiteralPath `$Target -PathType Leaf)){ Write-Host "[WARN] Missing target: `$Target" -ForegroundColor Yellow; return }
`$text=Get-Content -LiteralPath `$Target -Raw -Encoding UTF8
`$functionCount=([regex]::Matches(`$text,'(?im)^\s*function\s+')).Count
`$paramCount=([regex]::Matches(`$text,'(?im)^\s*param\s*\(')).Count
`$review=([regex]::Matches(`$text,'(?i)\bStop-Process\b|\bRemove-Item\b|\bSet-Content\b|\bStart-Process\b|\bexit\b')).Count
Write-Host "[OK] SurfaceScan completed." -ForegroundColor Green
Write-Host "Functions   : `$functionCount"
Write-Host "ParamBlocks : `$paramCount"
Write-Host "ReviewTokens: `$review"
"@

    return @(
        [pscustomobject]@{Project=$Project;StreamNo=1;Stream="ParserOnly";CommandPath=$parser;Target=$Target},
        [pscustomobject]@{Project=$Project;StreamNo=2;Stream="MetadataHash";CommandPath=$hash;Target=$Target},
        [pscustomobject]@{Project=$Project;StreamNo=3;Stream="SurfaceScan";CommandPath=$surface;Target=$Target}
    )
}

function Invoke-SafeCommand {
    param([object]$Command)

    $stdout=Join-Path $StdoutDir "$($Command.Project)_$($Command.StreamNo)_stdout.txt"
    $stderr=Join-Path $StdoutDir "$($Command.Project)_$($Command.StreamNo)_stderr.txt"
    $exit=-999
    $duration=0.0
    $status="WARN"
    $risk="MEDIUM"
    $message="Not executed."

    try {
        $sw=[System.Diagnostics.Stopwatch]::StartNew()
        $p=Start-Process -FilePath "pwsh" -ArgumentList @("-NoLogo","-NoProfile","-ExecutionPolicy","Bypass","-File",$Command.CommandPath) -NoNewWindow -PassThru -Wait -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        $sw.Stop()
        $exit=$p.ExitCode
        $duration=[math]::Round($sw.Elapsed.TotalSeconds,2)

        $out=""
        $err=""
        if(Test-Path -LiteralPath $stdout){$out=Get-Content -LiteralPath $stdout -Raw -Encoding UTF8}
        if(Test-Path -LiteralPath $stderr){$err=Get-Content -LiteralPath $stderr -Raw -Encoding UTF8}
        $all="$out`n$err"

        if($all -match "\[FAIL\]"){
            $status="FAIL"; $risk="HIGH"; $message="Safe stream reported FAIL."
        } elseif($all -match "\[WARN\]"){
            $status="WARN"; $risk="MEDIUM"; $message="Safe stream reported WARN."
        } elseif($exit -eq 0) {
            $status="OK"; $risk="LOW"; $message="Safe stream passed."
        } else {
            $status="WARN"; $risk="MEDIUM"; $message="Safe stream returned non-zero exit."
        }
    } catch {
        $status="FAIL"; $risk="HIGH"; $message=$_.Exception.Message
    }

    return [pscustomobject]@{
        Project=$Command.Project
        StreamNo=$Command.StreamNo
        Stream=$Command.Stream
        Status=$status
        Risk=$risk
        ExitCode=$exit
        DurationSec=$duration
        Message=$message
        Target=$Command.Target
        CommandPath=$Command.CommandPath
        StdoutPath=$stdout
        StderrPath=$stderr
    }
}

function Build-Top10Libs {
    return @(
        [pscustomobject]@{Lane="LaneA";Function="VDF Guarded Entry Validation";Language="PowerShell";Top10LocalFreeLibs="Pester; PSScriptAnalyzer; Microsoft.PowerShell.Management; Microsoft.PowerShell.Utility; ThreadJob; ImportExcel; PSWriteHTML; PSFramework; BurntToast; Pode"},
        [pscustomobject]@{Lane="LaneA";Function="VDF Guarded Entry Validation";Language="Python";Top10LocalFreeLibs="pytest; unittest; pathlib; subprocess; psutil; rich; tqdm; pandas; pydantic; structlog"},
        [pscustomobject]@{Lane="LaneA";Function="VDF Guarded Entry Validation";Language="HTML_JS";Top10LocalFreeLibs="Vanilla JS; Web Components; Chart.js; Tabulator; Grid.js; htmx; Alpine.js; Prism.js; Fuse.js; FileSaver.js"},

        [pscustomobject]@{Lane="LaneB";Function="NexusCore Guarded Entry Validation";Language="PowerShell";Top10LocalFreeLibs="Pester; PSScriptAnalyzer; ThreadJob; PSFramework; ImportExcel; PSWriteHTML; Pode; Polaris; SecretManagement; BurntToast"},
        [pscustomobject]@{Lane="LaneB";Function="NexusCore Guarded Entry Validation";Language="Python";Top10LocalFreeLibs="pytest; typer; pydantic; subprocess; psutil; rich; pandas; polars; duckdb; pyarrow"},
        [pscustomobject]@{Lane="LaneB";Function="NexusCore Guarded Entry Validation";Language="HTML_JS";Top10LocalFreeLibs="Vanilla JS; Web Components; Tabulator; Chart.js; Mermaid; xterm.js; Prism.js; DOMPurify; Marked; Tippy.js"},

        [pscustomobject]@{Lane="LaneC";Function="VIA Guarded Root Entry";Language="PowerShell";Top10LocalFreeLibs="Microsoft.PowerShell.Management; Microsoft.PowerShell.Utility; PSScriptAnalyzer; Pester; ImportExcel; PSWriteHTML; PSFramework; ThreadJob; platyPS; PowerShell-Yaml"},
        [pscustomobject]@{Lane="LaneC";Function="VIA Guarded Root Entry";Language="Python";Top10LocalFreeLibs="pathlib; re; json; ast; libcst; parso; pandas; rich; tqdm; networkx"},
        [pscustomobject]@{Lane="LaneC";Function="VIA Guarded Root Entry";Language="HTML_JS";Top10LocalFreeLibs="Vanilla JS; Tabulator; Grid.js; Chart.js; Fuse.js; Day.js; Mermaid; Prism.js; Shoelace; FileSaver.js"},

        [pscustomobject]@{Lane="LaneD";Function="VRN Guarded Root Entry";Language="PowerShell";Top10LocalFreeLibs="Get-ChildItem; Test-Path; Select-String; PSScriptAnalyzer; Pester; ImportExcel; PSWriteHTML; ThreadJob; PSFramework; PowerShell-Yaml"},
        [pscustomobject]@{Lane="LaneD";Function="VRN Guarded Root Entry";Language="Python";Top10LocalFreeLibs="pathlib; re; ast; json; pandas; rich; tqdm; rapidfuzz; networkx; typer"},
        [pscustomobject]@{Lane="LaneD";Function="VRN Guarded Root Entry";Language="HTML_JS";Top10LocalFreeLibs="Vanilla JS; Fuse.js; Tabulator; Grid.js; Chart.js; Mermaid; Prism.js; Day.js; Shoelace; FileSaver.js"},

        [pscustomobject]@{Lane="LaneE";Function="Disk / Production HOLD";Language="PowerShell";Top10LocalFreeLibs="Storage; Microsoft.PowerShell.Management; Microsoft.PowerShell.Utility; PSReadLine; ThreadJob; ImportExcel; PSWriteHTML; PSFramework; BurntToast; Pester"},
        [pscustomobject]@{Lane="LaneE";Function="Disk / Production HOLD";Language="Python";Top10LocalFreeLibs="os; pathlib; shutil; psutil; pandas; polars; duckdb; pyarrow; rich; tqdm"},
        [pscustomobject]@{Lane="LaneE";Function="Disk / Production HOLD";Language="HTML_JS";Top10LocalFreeLibs="Vanilla JS; Chart.js; Tabulator; Grid.js; Day.js; Fuse.js; Tippy.js; Shoelace; Mermaid; FileSaver.js"},

        [pscustomobject]@{Lane="LaneF";Function="HTML Matrix / Consolidation";Language="PowerShell";Top10LocalFreeLibs="ImportExcel; PSWriteHTML; Pester; PSScriptAnalyzer; PSFramework; ThreadJob; Microsoft.PowerShell.Archive; Storage; BurntToast; PlatyPS"},
        [pscustomobject]@{Lane="LaneF";Function="HTML Matrix / Consolidation";Language="Python";Top10LocalFreeLibs="pandas; polars; duckdb; pyarrow; pathlib; json; rich; tqdm; networkx; plotly"},
        [pscustomobject]@{Lane="LaneF";Function="HTML Matrix / Consolidation";Language="HTML_JS";Top10LocalFreeLibs="Vanilla JS; Tabulator; Chart.js; Grid.js; Mermaid; Shoelace; Fuse.js; Day.js; Prism.js; FileSaver.js"}
    )
}

function Build-CommandFiles {
    $prod=Join-Path $CmdDir "VIA_v0357_Production_Commands_HOLD.ps1"
    $rerun=Join-Path $CmdDir "VIA_v0357_Rerun_4Project_3Stream_Sandbox.ps1"

    Write-Utf8 -Path $prod -Text @"
# VIA v035.7 Production Commands HOLD
# Do not run until:
# 1. C free >= 25GB
# 2. Guarded entries reviewed
# 3. Manual production confirmation set

# Safe default probes:
# pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$ExpectedVrnEntry"
# pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$ExpectedViaEntry"

# Explicit production run remains HOLD:
# pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$ExpectedVrnEntry" -Run
# pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$ExpectedViaEntry" -Run
"@

    Write-Utf8 -Path $rerun -Text @"
# VIA v035.7 Rerun 4 Project × 3 Stream Sandbox
Get-ChildItem -LiteralPath "$CmdDir" -Recurse -File -Filter "*.ps1" |
  Where-Object { `$_.Name -match "_0[123]_" } |
  Sort-Object FullName |
  ForEach-Object {
    Write-Host "[RUN] `$(`$_.FullName)" -ForegroundColor Cyan
    pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File `$_.FullName
  }
"@

    return @(
        [pscustomobject]@{Type="ProductionHold";Status="GENERATED_HOLD";Message="Production commands commented HOLD.";Path=$prod},
        [pscustomobject]@{Type="RerunSandbox";Status="GENERATED";Message="4 project x 3 stream sandbox rerun command generated.";Path=$rerun}
    )
}

function THead {
    param([string[]]$Cols)
    return (($Cols | ForEach-Object { "<th>$(Enc $_)</th>" }) -join "")
}

function TRows {
    param([array]$Rows,[string[]]$Cols)
    $out=@()
    foreach($r in @($Rows)){
        $cells=@()
        foreach($c in $Cols){
            $v=""
            if($r.PSObject.Properties[$c]){$v=[string]$r.$c}
            $cls="cellBox"
            if($c -match "Path|Message|Top10|Target|Command|Expected|Candidate|Draft"){$cls="cellBox path"}
            if($c -match "Value|Score|Bytes|Rank|FreeGB|FreePercent|ExitCode|Duration"){$cls="cellBox num"}
            $cells += "<td><span class='$cls'>$(Enc $v)</span></td>"
        }
        $out += "<tr>$($cells -join '')</tr>"
    }
    return ($out -join "`n")
}

function Write-Report {
    param(
        [object]$Runtime,
        [array]$DriveRows,
        [array]$LaneRows,
        [array]$CandidateRows,
        [array]$PromotionRows,
        [array]$StreamRows,
        [array]$ExecRows,
        [array]$CommandRows,
        [array]$Top10Rows,
        [string]$HtmlPath
    )

    $driveCols=@("Drive","Root","Used","Free","FreeGB","FreePercent","Risk")
    $laneCols=@("Lane","Round","Project","Gate","Status","Risk","FixClass","IssueType","Value","Message","Path")
    $candCols=@("Kind","CandidateRank","CandidateClass","Score","GeneratedPath","ParserStatus","ParserErrors","Bytes","Modified","Name","Path","Message")
    $promoteCols=@("Project","Status","Risk","Created","Message","Expected","Candidate","Draft")
    $streamCols=@("Project","StreamNo","Stream","CommandPath","Target")
    $execCols=@("Project","StreamNo","Stream","Status","Risk","ExitCode","DurationSec","Message","Target","CommandPath","StdoutPath","StderrPath")
    $cmdCols=@("Type","Status","Message","Path")
    $libCols=@("Lane","Function","Language","Top10LocalFreeLibs")

    $focus=@($LaneRows | Where-Object { $_.Status -ne "OK" })
    $seq=@($LaneRows | Where-Object FixClass -eq "SEQUENTIAL_REQUIRED")
    $parallel=@($LaneRows | Where-Object FixClass -eq "PARALLEL_SAFE")

    $html=@"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA Guarded Root Entry Promotion Gate v035.7</title>
<style>
:root{--ink:#16211D;--muted:#66726B;--line:rgba(42,64,55,.14);--dan:#B64236;--sky:#EAF2EC}
*{box-sizing:border-box}
body{margin:0;background:linear-gradient(135deg,#F9F9F6,#EFF5F0);color:var(--ink);font-family:"Noto Sans TC","Microsoft JhengHei",Arial,sans-serif;font-size:11px}
.page{padding:12px;display:grid;gap:10px}
.top,.panel,.kpi{border:1px solid var(--line);border-radius:16px;background:rgba(255,255,250,.92);box-shadow:0 8px 24px rgba(28,45,39,.08)}
.top{padding:12px;display:grid;grid-template-columns:42px 1fr;gap:10px;align-items:center}
.seal{width:38px;height:38px;border-radius:12px;background:var(--dan);color:white;font-weight:900;font-size:22px;display:flex;align-items:center;justify-content:center}
h1{font-size:15px;margin:0}p{margin:3px 0 0;color:var(--muted)}
.kpis{display:grid;grid-template-columns:repeat(8,minmax(105px,1fr));gap:8px}
.kpi{padding:8px 10px}.kpi em{display:block;color:var(--muted);font-style:normal;font-size:9px}.kpi b{font-size:12px}
.panel{overflow:hidden}.panel h2{font-size:11px;margin:0;padding:8px 10px;background:var(--sky);border-bottom:1px solid var(--line)}
.shell{overflow:auto;max-height:56vh}
table{width:100%;min-width:1550px;border-collapse:separate;border-spacing:0;table-layout:fixed}
th{position:sticky;top:0;background:#EEF5F0;padding:5px;text-align:left;border-bottom:1px solid var(--line);z-index:2}
td{height:54px;max-height:54px;padding:5px;border-bottom:1px solid rgba(47,70,61,.08);vertical-align:top;overflow:hidden}
tr:hover td{height:145px;max-height:145px}
.cellBox{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3;overflow:hidden;word-break:break-word;line-height:1.25;white-space:pre-wrap}
tr:hover .cellBox{-webkit-line-clamp:10}
.path{font-family:Consolas,"Cascadia Mono",monospace}.num{text-align:right}
.footer{color:var(--muted);font-size:9px;display:grid;gap:4px}
</style>
</head>
<body>
<div class="page">
<header class="top">
  <div class="seal">理</div>
  <div>
    <h1>Veritas Intelligence Analytics · Guarded Root Entry Promotion Gate</h1>
    <p>v035.7 · guarded entry creation only if missing · default safe probe · production hold</p>
  </div>
</header>

<section class="kpis">
<div class="kpi"><em>Status</em><b>$(Enc $Runtime.status)</b></div>
<div class="kpi"><em>Risk</em><b>$(Enc $Runtime.risk)</b></div>
<div class="kpi"><em>OK</em><b>$(Enc $Runtime.ok_count)</b></div>
<div class="kpi"><em>WARN/HOLD</em><b>$(Enc $Runtime.warn_count)</b></div>
<div class="kpi"><em>FAIL</em><b>$(Enc $Runtime.fail_count)</b></div>
<div class="kpi"><em>Created Entries</em><b>$(Enc $Runtime.created_entry_count)</b></div>
<div class="kpi"><em>C Free</em><b>$(Enc $Runtime.c_free)</b></div>
<div class="kpi"><em>Decision</em><b>$(Enc $Runtime.next_decision)</b></div>
</section>

<section class="panel"><h2>Drive Matrix</h2><div class="shell"><table><thead><tr>$(THead $driveCols)</tr></thead><tbody>$(TRows $DriveRows $driveCols)</tbody></table></div></section>
<section class="panel"><h2>Six-Lane Matrix</h2><div class="shell"><table><thead><tr>$(THead $laneCols)</tr></thead><tbody>$(TRows $LaneRows $laneCols)</tbody></table></div></section>
<section class="panel"><h2>Candidate Ranking</h2><div class="shell"><table><thead><tr>$(THead $candCols)</tr></thead><tbody>$(TRows $CandidateRows $candCols)</tbody></table></div></section>
<section class="panel"><h2>Guarded Entry Promotion Results</h2><div class="shell"><table><thead><tr>$(THead $promoteCols)</tr></thead><tbody>$(TRows $PromotionRows $promoteCols)</tbody></table></div></section>
<section class="panel"><h2>4 Projects × 3 Safe Streams</h2><div class="shell"><table><thead><tr>$(THead $streamCols)</tr></thead><tbody>$(TRows $StreamRows $streamCols)</tbody></table></div></section>
<section class="panel"><h2>Safe Stream Execution Results</h2><div class="shell"><table><thead><tr>$(THead $execCols)</tr></thead><tbody>$(TRows $ExecRows $execCols)</tbody></table></div></section>
<section class="panel"><h2>Focus Matrix · Non-OK</h2><div class="shell"><table><thead><tr>$(THead $laneCols)</tr></thead><tbody>$(TRows $focus $laneCols)</tbody></table></div></section>
<section class="panel"><h2>Sequential Required Matrix</h2><div class="shell"><table><thead><tr>$(THead $laneCols)</tr></thead><tbody>$(TRows $seq $laneCols)</tbody></table></div></section>
<section class="panel"><h2>Parallel Safe Matrix</h2><div class="shell"><table><thead><tr>$(THead $laneCols)</tr></thead><tbody>$(TRows $parallel $laneCols)</tbody></table></div></section>
<section class="panel"><h2>Generated Command Files</h2><div class="shell"><table><thead><tr>$(THead $cmdCols)</tr></thead><tbody>$(TRows $CommandRows $cmdCols)</tbody></table></div></section>
<section class="panel"><h2>Top 10 Local Free Libs</h2><div class="shell"><table><thead><tr>$(THead $libCols)</tr></thead><tbody>$(TRows $Top10Rows $libCols)</tbody></table></div></section>

<footer class="footer">
<span>判天地之美，析萬物之理。 Veritas Intelligence Analytics │ AI-Augmented Investment Intelligence</span>
<span>Runtime: $(Enc $Runtime.runtime_json)</span>
</footer>
</div>
</body>
</html>
"@

    Write-Utf8 -Path $HtmlPath -Text $html
}

try {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA · GUARDED ROOT ENTRY PROMOTION GATE · v035.7" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan

    try { Set-PSReadLineOption -HistorySaveStyle SaveNothing -ErrorAction SilentlyContinue } catch {}

    $laneRows=@()

    Show-Step 8 "Round 1 · Disk gate"
    $drive=Get-DriveRows
    $c=@($drive | Where-Object Drive -eq "C" | Select-Object -First 1)[0]

    $laneRows += New-Row "LaneE" "Round1" "Disk" "Light Sandbox Gate" ($(if([double]$c.FreeGB -ge $MinFreeLightGB){"OK"}else{"FAIL"})) ($(if([double]$c.FreeGB -ge $MinFreeLightGB){"LOW"}else{"HIGH"})) "NONE" "DiskLightGate" "$($c.Free) / $($c.FreePercent)%" "Light sandbox requires >= $MinFreeLightGB GB." "C:\"

    Show-Step 18 "Round 1 · Discover real candidates"
    $vrnCandidates=@(Discover-Candidates -Kind "VRN")
    $viaCandidates=@(Discover-Candidates -Kind "VIA")

    $bestVrn=@($vrnCandidates | Where-Object { $_.GeneratedPath -eq $false -and $_.ParserStatus -eq "OK" -and $_.Score -ge 50 } | Select-Object -First 1)
    $bestVia=@($viaCandidates | Where-Object { $_.GeneratedPath -eq $false -and $_.ParserStatus -eq "OK" -and $_.Score -ge 50 } | Select-Object -First 1)

    $allCandidates=@($vrnCandidates + $viaCandidates)

    $laneRows += New-Row "LaneD" "Round1" "VRN" "Real Candidate Discovery" ($(if($bestVrn){"OK"}else{"WARN"})) ($(if($bestVrn){"LOW"}else{"MEDIUM"})) "SEQUENTIAL_REQUIRED" "RealCandidateDiscovery" ([string]@($vrnCandidates).Count) "VRN candidates discovered; generated artifacts excluded." $Root
    $laneRows += New-Row "LaneC" "Round1" "VIA" "Real Candidate Discovery" ($(if($bestVia){"OK"}else{"WARN"})) ($(if($bestVia){"LOW"}else{"MEDIUM"})) "SEQUENTIAL_REQUIRED" "RealCandidateDiscovery" ([string]@($viaCandidates).Count) "VIA candidates discovered; generated artifacts excluded." $Root

    Show-Step 30 "Round 1 · Select candidates"
    if($bestVrn){
        $laneRows += New-Row "LaneD" "Round2" "VRN" "Best Candidate" "OK" "LOW" "SEQUENTIAL_REQUIRED" "BestCandidate" "$($bestVrn.CandidateClass) / Score $($bestVrn.Score)" "Selected VRN candidate." $bestVrn.Path
    }
    if($bestVia){
        $laneRows += New-Row "LaneC" "Round2" "VIA" "Best Candidate" "OK" "LOW" "SEQUENTIAL_REQUIRED" "BestCandidate" "$($bestVia.CandidateClass) / Score $($bestVia.Score)" "Selected VIA candidate." $bestVia.Path
    }

    Show-Step 42 "Round 2 · Guarded root entry promotion if missing"
    $promotionRows=@()

    if($bestVrn){
        $promotionRows += Promote-IfMissing -Project "VRN" -Expected $ExpectedVrnEntry -Candidate ([string]$bestVrn.Path)
    } else {
        $promotionRows += [pscustomobject]@{Project="VRN";Status="WARN";Risk="MEDIUM";Created=$false;Message="No valid VRN candidate.";Expected=$ExpectedVrnEntry;Candidate="";Draft=""}
    }

    if($bestVia){
        $promotionRows += Promote-IfMissing -Project "VIA" -Expected $ExpectedViaEntry -Candidate ([string]$bestVia.Path)
    } else {
        $promotionRows += [pscustomobject]@{Project="VIA";Status="WARN";Risk="MEDIUM";Created=$false;Message="No valid VIA candidate.";Expected=$ExpectedViaEntry;Candidate="";Draft=""}
    }

    foreach($p in $promotionRows){
        $laneRows += New-Row ($(if($p.Project -eq "VRN"){"LaneD"}else{"LaneC"})) "Round2" $p.Project "Guarded Entry Promotion" $p.Status $p.Risk ($(if($p.Created){"SEQUENTIAL_DONE"}else{"NONE"})) "GuardedEntry" ($(if($p.Created){"CREATED"}else{"NO_OVERWRITE"})) $p.Message $p.Expected
    }

    Show-Step 56 "Round 2 · Generate 4 Project × 3 Stream commands"
    $projectTargets=@(
        [pscustomobject]@{Project="VDF";Target=$ExpectedVdfEntry},
        [pscustomobject]@{Project="NexusCore";Target=$ExpectedNexusEntry},
        [pscustomobject]@{Project="VIA";Target=$ExpectedViaEntry},
        [pscustomobject]@{Project="VRN";Target=$ExpectedVrnEntry}
    )

    $streamRows=@()
    foreach($pt in $projectTargets){
        $streamRows += @(New-ThreeStreamCommands -Project $pt.Project -Target $pt.Target)
    }

    $laneRows += New-Row "LaneA" "Round2" "VDF" "3 Safe Streams Generated" "OK" "LOW" "PARALLEL_SAFE" "ThreeStream" "3" "ParserOnly / MetadataHash / SurfaceScan generated." "$CmdDir\VDF"
    $laneRows += New-Row "LaneB" "Round2" "NexusCore" "3 Safe Streams Generated" "OK" "LOW" "PARALLEL_SAFE" "ThreeStream" "3" "ParserOnly / MetadataHash / SurfaceScan generated." "$CmdDir\NexusCore"
    $laneRows += New-Row "LaneC" "Round2" "VIA" "3 Safe Streams Generated" "OK" "LOW" "PARALLEL_SAFE" "ThreeStream" "3" "ParserOnly / MetadataHash / SurfaceScan generated." "$CmdDir\VIA"
    $laneRows += New-Row "LaneD" "Round2" "VRN" "3 Safe Streams Generated" "OK" "LOW" "PARALLEL_SAFE" "ThreeStream" "3" "ParserOnly / MetadataHash / SurfaceScan generated." "$CmdDir\VRN"

    Show-Step 68 "Round 2 · Execute safe streams"
    $execRows=@()
    $i=0
    foreach($cmd in @($streamRows)){
        $i++
        Show-Step (68 + [int](($i/[math]::Max(1,@($streamRows).Count))*12)) "Safe stream $i / $(@($streamRows).Count)"
        $execRows += Invoke-SafeCommand -Command $cmd
    }

    $execFail=@($execRows | Where-Object Status -eq "FAIL").Count
    $execWarn=@($execRows | Where-Object Status -eq "WARN").Count
    $execOk=@($execRows | Where-Object Status -eq "OK").Count

    $laneRows += New-Row "LaneF" "Round2" "Sandbox" "4 Project × 3 Stream Execution" ($(if($execFail -eq 0){"OK"}else{"FAIL"})) ($(if($execFail -eq 0){"LOW"}else{"HIGH"})) "PARALLEL_SAFE" "StreamExecution" "OK=$execOk WARN=$execWarn FAIL=$execFail" "All safe streams executed. Warnings are review items." $StdoutDir

    Show-Step 84 "Round 3 · Final hold gates"
    $laneRows += New-Row "LaneE" "Round3" "Disk" "Full Production Gate" ($(if([double]$c.FreeGB -ge $MinFreeFullGB){"OK"}else{"HOLD"})) ($(if([double]$c.FreeGB -ge $MinFreeFullGB){"LOW"}else{"MEDIUM"})) "SEQUENTIAL_REQUIRED" "ProductionDiskHold" "$($c.Free) / $($c.FreePercent)%" "Full production waits until >= $MinFreeFullGB GB." "C:\"
    $laneRows += New-Row "LaneE" "Round3" "Production" "Confirmation Gate" "HOLD" "MEDIUM" "SEQUENTIAL_REQUIRED" "ConfirmationNotSet" "NOT_SET" "No production confirmation is set. Full production not executed." $Run

    $cmdFiles=@(Build-CommandFiles)
    $top10=@(Build-Top10Libs)

    $laneRows += New-Row "LaneF" "Round3" "Consolidation" "Top10 Local Free Libs" "OK" "LOW" "NONE" "LibMatrix" ([string]@($top10).Count) "Top10 libs matrix generated." (Join-Path $RegDir "VIA_GuardedRootEntry_Top10LocalFreeLibs_v0357.csv")
    $laneRows += New-Row "LaneF" "Round3" "Consolidation" "Next Step" "OK" "LOW" "NONE" "Next" "V0358_READY" "Next safe step is final user-test safe probe. Full production remains HOLD until disk gate passes." $Run

    Show-Step 90 "Round 3 · Final classification"
    $ok=@($laneRows | Where-Object Status -eq "OK").Count + $execOk
    $fail=@($laneRows | Where-Object Status -eq "FAIL").Count + $execFail
    $warn=@($laneRows | Where-Object { $_.Status -eq "WARN" -or $_.Status -eq "HOLD" }).Count + $execWarn
    $seq=@($laneRows | Where-Object FixClass -eq "SEQUENTIAL_REQUIRED").Count
    $parallel=@($laneRows | Where-Object FixClass -eq "PARALLEL_SAFE").Count
    $createdCount=@($promotionRows | Where-Object Created -eq $true).Count

    $status="VIA_GUARDED_ROOT_ENTRY_PROMOTION_READY"
    $risk="LOW"
    $decision="V0358_FINAL_USER_TEST_SAFE_PROBE_READY_FULL_PRODUCTION_HOLD"

    if($fail -gt 0){
        $status="VIA_GUARDED_ROOT_ENTRY_PROMOTION_BLOCKED_BY_FAIL"
        $risk="HIGH"
        $decision="FIX_FAIL_FIRST"
    } elseif($warn -gt 0 -or $seq -gt 0 -or [double]$c.FreeGB -lt $MinFreeFullGB) {
        $status="VIA_GUARDED_ROOT_ENTRY_PROMOTION_READY_WITH_PRODUCTION_HOLD"
        $risk="MEDIUM"
    }

    Show-Step 94 "Write CSV / JSON / HTML"
    $runtimeJson=Join-Path $RuntimeDir "VIA_GuardedRootEntryPromotion_Runtime_v0357.json"
    $sealJson=Join-Path $SealDir "VIA_GuardedRootEntryPromotion_Seal_v0357.json"
    $laneCsv=Join-Path $RegDir "VIA_GuardedRootEntryPromotion_LaneMatrix_v0357.csv"
    $candidateCsv=Join-Path $RegDir "VIA_GuardedRootEntryPromotion_CandidateMatrix_v0357.csv"
    $promotionCsv=Join-Path $RegDir "VIA_GuardedRootEntryPromotion_PromotionMatrix_v0357.csv"
    $streamCsv=Join-Path $RegDir "VIA_GuardedRootEntryPromotion_StreamMatrix_v0357.csv"
    $execCsv=Join-Path $RegDir "VIA_GuardedRootEntryPromotion_ExecutionMatrix_v0357.csv"
    $driveCsv=Join-Path $RegDir "VIA_GuardedRootEntryPromotion_DriveMatrix_v0357.csv"
    $commandCsv=Join-Path $RegDir "VIA_GuardedRootEntryPromotion_CommandMatrix_v0357.csv"
    $top10Csv=Join-Path $RegDir "VIA_GuardedRootEntryPromotion_Top10LocalFreeLibs_v0357.csv"
    $htmlPath=Join-Path $ReportDir "VIA_GuardedRootEntryPromotion_Report_v0357.html"

    $runtime=[pscustomobject]@{
        generated_at=[string](Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        status=[string]$status
        risk=[string]$risk
        ok_count=[int]$ok
        warn_count=[int]$warn
        fail_count=[int]$fail
        parallel_safe_count=[int]$parallel
        sequential_required_count=[int]$seq
        created_entry_count=[int]$createdCount
        best_vrn_candidate=($(if($bestVrn){[string]$bestVrn.Path}else{""}))
        best_via_candidate=($(if($bestVia){[string]$bestVia.Path}else{""}))
        stream_count=[int]@($streamRows).Count
        executed_stream_count=[int]@($execRows).Count
        c_free=[string]$c.Free
        c_free_gb=[double]$c.FreeGB
        c_free_percent=[double]$c.FreePercent
        next_decision=[string]$decision
        mode="GUARDED_ROOT_ENTRY_PROMOTION_GATE"
        source_modified=($createdCount -gt 0)
        expected_entry_created=($createdCount -gt 0)
        full_production_executed=$false
        deletion_used=$false
        patch_applied=$false
        active_pointer_changed=$false
        canonical_changed=$false
        python_activation_used=$false
        vscode_opened=$false
        stop_process_used=$false
        runtime_json=[string]$runtimeJson
        seal_json=[string]$sealJson
        lane_csv=[string]$laneCsv
        candidate_csv=[string]$candidateCsv
        promotion_csv=[string]$promotionCsv
        stream_csv=[string]$streamCsv
        execution_csv=[string]$execCsv
        drive_csv=[string]$driveCsv
        command_csv=[string]$commandCsv
        top10_libs_csv=[string]$top10Csv
        command_dir=[string]$CmdDir
        draft_dir=[string]$DraftDir
        html=[string]$htmlPath
    }

    @($runtime) | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $runtimeJson -Encoding UTF8
    @($runtime) | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $sealJson -Encoding UTF8
    @($laneRows) | Export-Csv -LiteralPath $laneCsv -NoTypeInformation -Encoding UTF8BOM
    @($allCandidates) | Export-Csv -LiteralPath $candidateCsv -NoTypeInformation -Encoding UTF8BOM
    @($promotionRows) | Export-Csv -LiteralPath $promotionCsv -NoTypeInformation -Encoding UTF8BOM
    @($streamRows) | Export-Csv -LiteralPath $streamCsv -NoTypeInformation -Encoding UTF8BOM
    @($execRows) | Export-Csv -LiteralPath $execCsv -NoTypeInformation -Encoding UTF8BOM
    @($drive) | Export-Csv -LiteralPath $driveCsv -NoTypeInformation -Encoding UTF8BOM
    @($cmdFiles) | Export-Csv -LiteralPath $commandCsv -NoTypeInformation -Encoding UTF8BOM
    @($top10) | Export-Csv -LiteralPath $top10Csv -NoTypeInformation -Encoding UTF8BOM

    Write-Report -Runtime $runtime -DriveRows $drive -LaneRows $laneRows -CandidateRows $allCandidates -PromotionRows $promotionRows -StreamRows $streamRows -ExecRows $execRows -CommandRows $cmdFiles -Top10Rows $top10 -HtmlPath $htmlPath

    $opened=$false
    $browser=""
    if($OpenHtml){
        Show-Step 98 "Open HTML"
        $browser=Find-Browser
        if($browser){
            Start-Process -FilePath $browser -ArgumentList @("--new-window","`"$htmlPath`"")
            $opened=$true
        }
    }

    Write-Progress -Activity "VIA v035.7 Guarded Root Entry Promotion Gate" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "def VIA GUARDED ROOT ENTRY PROMOTION GATE COMPLETE · v035.7" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "Status                   : $status"
    Write-Host "Risk                     : $risk"
    Write-Host "OK                       : $ok"
    Write-Host "WARN/HOLD                : $warn"
    Write-Host "FAIL                     : $fail"
    Write-Host "Parallel Safe            : $parallel"
    Write-Host "Sequential Required      : $seq"
    Write-Host "Created Entry Count      : $createdCount"
    Write-Host "Best VRN Candidate       : $(if($bestVrn){$bestVrn.Path}else{'NONE'})"
    Write-Host "Best VIA Candidate       : $(if($bestVia){$bestVia.Path}else{'NONE'})"
    Write-Host "Stream Count             : $(@($streamRows).Count)"
    Write-Host "Executed Stream Count    : $(@($execRows).Count)"
    Write-Host "C Free                   : $($c.Free) / $($c.FreePercent)%"
    Write-Host "Next Decision            : $decision"
    Write-Host "Source Modified          : $($createdCount -gt 0)"
    Write-Host "Expected Entry Created   : $($createdCount -gt 0)"
    Write-Host "Full Production Executed : False"
    Write-Host "Deletion Used            : False"
    Write-Host "Patch Applied            : False"
    Write-Host "Active Pointer Changed   : False"
    Write-Host "Canonical Changed        : False"
    Write-Host "Python Activation Used   : False"
    Write-Host "VS Code Opened           : False"
    Write-Host "Stop-Process Used        : False"
    Write-Host "HTML Opened              : $opened"
    Write-Host "Browser                  : $browser"
    Write-Host "Runtime JSON             : $runtimeJson"
    Write-Host "Seal JSON                : $sealJson"
    Write-Host "Lane CSV                 : $laneCsv"
    Write-Host "Promotion CSV            : $promotionCsv"
    Write-Host "Execution CSV            : $execCsv"
    Write-Host "Command CSV              : $commandCsv"
    Write-Host "Top10 Libs CSV           : $top10Csv"
    Write-Host "Command Dir              : $CmdDir"
    Write-Host "Draft Dir                : $DraftDir"
    Write-Host "HTML                     : $htmlPath"
    Write-Host ""
    Write-Host "PowerShell remains open. v035.7 complete." -ForegroundColor Green
}
catch {
    Write-Progress -Activity "VIA v035.7 Guarded Root Entry Promotion Gate" -Completed
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell remains open. No exit." -ForegroundColor Yellow
}
