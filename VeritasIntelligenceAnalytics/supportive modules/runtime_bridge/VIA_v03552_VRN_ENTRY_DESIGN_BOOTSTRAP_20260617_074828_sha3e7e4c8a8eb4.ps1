#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

$Root = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
$Ts = Get-Date -Format "yyyyMMdd_HHmmss"
$Run = Join-Path $Root "_via_vrn_entry_design_runs\RUN_${Ts}_v03552_VRN_ENTRY_DESIGN_BOOTSTRAP"
$ReportDir = Join-Path $Run "report"
$RuntimeDir = Join-Path $Run "runtime"
$RegDir = Join-Path $Run "registry"
$CmdDir = Join-Path $Run "commands"
$WrapperDir = Join-Path $Run "wrappers"
$SealDir = Join-Path $Run "seal"

$ExpectedVrnEntry = Join-Path $Root "functional modules\VRN\Invoke-VRN.ps1"
$MinFreeLightGB = 12
$MinFreeFullGB = 25
$OpenHtml = $true

foreach($d in @($Run,$ReportDir,$RuntimeDir,$RegDir,$CmdDir,$WrapperDir,$SealDir)){
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}

function Show-Step {
    param([int]$Pct,[string]$Text)
    if($Pct -lt 0){$Pct=0}
    if($Pct -gt 100){$Pct=100}
    Write-Progress -Activity "VIA v035.5.2 VRN Entry Design Bootstrap" -Status $Text -PercentComplete $Pct
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
        $used=0L; $free=0L
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
            Message=($(if($n -eq 0){"No parser errors."}else{(@($errors | Select-Object -First 5 | ForEach-Object Message) -join " | ")}))
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

function Get-SearchRoots {
    $roots=@()
    $roots += Join-Path $Root "functional modules\VRN"
    $roots += Join-Path $Root "dict\VRN"
    $roots += Join-Path $Root "tools"
    $roots += $Root

    $od = Join-Path $env:USERPROFILE "OneDrive\VeritasIntelligenceAnalytics"
    $roots += Join-Path $od "module\VRN"
    $roots += Join-Path $od "module"
    $roots += $od

    return @($roots | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Container) } | Select-Object -Unique)
}

function Get-CandidateScore {
    param([System.IO.FileInfo]$File,[object]$Syntax)
    $score=0
    $n=$File.Name
    $p=$File.FullName

    if($n -ieq "Invoke-VRN.ps1"){$score += 100}
    if($n -match "Invoke"){$score += 20}
    if($n -match "VRN"){$score += 30}
    if($n -match "ReportNova|VeritasReportNova"){$score += 25}
    if($p -match "\\module\\VRN\\|\\functional modules\\VRN\\"){$score += 45}
    if($p -match "\\dict\\VRN\\"){$score += 10}
    if($p -match "\\tools\\"){$score += 5}
    if($p -match "\\runs\\RUN_|\\sandbox\\|\\backup|\\archive|\\report\\|\\runtime\\|\\registry\\"){$score -= 25}
    if($Syntax.Status -eq "OK"){$score += 30}
    if($File.Length -gt 0){$score += 5}
    if($File.Length -gt 2MB){$score -= 25}
    return $score
}

function Discover-VrnCandidates {
    $roots=Get-SearchRoots
    $raw=@()

    foreach($r in $roots){
        try {
            $items=@(
                Get-ChildItem -LiteralPath $r -Recurse -File -Filter "*.ps1" -ErrorAction SilentlyContinue |
                Where-Object {
                    $_.FullName -notmatch "\\\.venv\\|\\node_modules\\|\\__pycache__\\|\\_envs\\|\\AppData\\" -and
                    $_.FullName -notmatch "\\report\\|\\runtime\\|\\registry\\" -and
                    (
                        $_.Name -match "VRN|ReportNova|Invoke" -or
                        $_.FullName -match "\\VRN\\|ReportNova|VeritasReportNova"
                    )
                } |
                Sort-Object LastWriteTime -Descending |
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
        $score=Get-CandidateScore -File $f -Syntax $syntax
        $class="REVIEW"
        if($score -ge 100){$class="STRONG_CANDIDATE"}
        elseif($score -ge 55){$class="CANDIDATE"}
        elseif($score -lt 20){$class="LOW_RELEVANCE"}

        $rows += [pscustomobject]@{
            CandidateRank=0
            CandidateClass=$class
            Score=$score
            ParserStatus=$syntax.Status
            ParserErrors=$syntax.ErrorCount
            Bytes=[int64]$f.Length
            Modified=$f.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            Name=$f.Name
            Path=$f.FullName
            Message=$syntax.Message
        }
    }

    $sorted=@($rows | Sort-Object @{Expression='Score';Descending=$true}, @{Expression='Modified';Descending=$true})
    $rank=0
    foreach($s in $sorted){
        $rank++
        $s.CandidateRank=$rank
    }

    return @($sorted | Select-Object -First 50)
}

function New-VrnWrapperDraft {
    param([AllowNull()][object]$Best)
    $wrapper=Join-Path $WrapperDir "Invoke-VRN-EntryCandidateWrapper-DRAFT-v03552.ps1"
    $candidate=""
    if($null -ne $Best){$candidate=[string]$Best.Path}

    $lines=@()
    $lines += "#Requires -Version 7.0"
    $lines += "Set-StrictMode -Version Latest"
    $lines += '$ErrorActionPreference = "Continue"'
    $lines += ""
    $lines += "# VIA v035.5.2 VRN Entry Candidate Wrapper DRAFT"
    $lines += "# PLAN ONLY. Does not overwrite expected Invoke-VRN.ps1."
    $lines += "`$SelectedCandidate = `"$candidate`""
    $lines += "`$ExpectedEntry = `"$ExpectedVrnEntry`""
    $lines += ""
    $lines += "Write-Host `"VIA v035.5.2 VRN Entry Candidate Wrapper DRAFT`" -ForegroundColor Cyan"
    $lines += "if(-not `$SelectedCandidate){ Write-Host `"[WARN] No candidate selected.`" -ForegroundColor Yellow; return }"
    $lines += "if(-not(Test-Path -LiteralPath `$SelectedCandidate -PathType Leaf)){ Write-Host `"[WARN] Candidate missing: `$SelectedCandidate`" -ForegroundColor Yellow; return }"
    $lines += "`$tokens=`$null; `$errors=`$null"
    $lines += "[System.Management.Automation.Language.Parser]::ParseFile(`$SelectedCandidate,[ref]`$tokens,[ref]`$errors)|Out-Null"
    $lines += "if(@(`$errors).Count -eq 0){ Write-Host `"[OK] Candidate parser OK.`" -ForegroundColor Green } else { Write-Host `"[FAIL] Candidate parser errors: `$(@(`$errors).Count)`" -ForegroundColor Red; return }"
    $lines += "`$item=Get-Item -LiteralPath `$SelectedCandidate -Force"
    $lines += "`$hash=(Get-FileHash -LiteralPath `$SelectedCandidate -Algorithm SHA256).Hash"
    $lines += "Write-Host `"[OK] Candidate bytes: `$(`$item.Length)`" -ForegroundColor Green"
    $lines += "Write-Host `"[OK] SHA256: `$hash`" -ForegroundColor Green"
    $lines += "Write-Host `"[HOLD] Expected entry not created: `$ExpectedEntry`" -ForegroundColor Yellow"
    $lines += "Write-Host `"[HOLD] Production activation not executed.`" -ForegroundColor Yellow"

    Write-Utf8 -Path $wrapper -Text ($lines -join "`r`n")
    return $wrapper
}

function Build-CommandFiles {
    param([AllowNull()][object]$Best,[string]$WrapperDraft)
    $safe=Join-Path $CmdDir "VIA_v03552_Run_VRN_WrapperDraft_SafeSandbox.ps1"
    $promote=Join-Path $CmdDir "VIA_v03552_VRN_Entry_Promotion_HOLD.ps1"
    $prod=Join-Path $CmdDir "VIA_v03552_Production_Commands_HOLD.ps1"

    $candidate=""
    if($null -ne $Best){$candidate=[string]$Best.Path}

    Write-Utf8 -Path $safe -Text @"
# VIA v035.5.2 Safe Sandbox Command
# Runs wrapper draft only. No production.
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$WrapperDraft"
"@

    Write-Utf8 -Path $promote -Text @"
# VIA v035.5.2 VRN Entry Promotion HOLD
# PLAN ONLY. No source write here.

# Expected final path:
# $ExpectedVrnEntry

# Selected candidate:
# $candidate

# Manual sequence if approved later:
# 1. Backup expected target location.
# 2. Create minimal Invoke-VRN.ps1 wrapper pointing to selected candidate.
# 3. Parser test.
# 4. Safe wrapper execution.
# 5. Only then consider production activation.
"@

    Write-Utf8 -Path $prod -Text @"
# VIA v035.5.2 Production Commands HOLD
# Do not run until:
# 1. C free >= 25GB
# 2. VRN entry explicitly approved
# 3. v035.5.2 design reviewed
# 4. manual production confirmation set

# pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$Root\functional modules\VDF\Invoke-VDF.ps1"
# pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$Root\supportive modules\Invoke-VeritasNexusCore.ps1"
# pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$Root\Invoke-VIA.ps1"
# pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$ExpectedVrnEntry"
"@

    return @(
        [pscustomobject]@{Type="SafeSandboxWrapperDraft";Status="GENERATED";Message="Run wrapper draft only.";Path=$safe},
        [pscustomobject]@{Type="VRNEntryPromotionHold";Status="PLAN_ONLY";Message="Promotion plan generated, not applied.";Path=$promote},
        [pscustomobject]@{Type="ProductionHold";Status="GENERATED_HOLD";Message="Production commands commented HOLD.";Path=$prod}
    )
}

function Build-Top10Libs {
    return @(
        [pscustomobject]@{Lane="LaneA";Function="Evidence Load";Language="PowerShell";Top10LocalFreeLibs="Microsoft.PowerShell.Management; Microsoft.PowerShell.Utility; Pester; PSScriptAnalyzer; ImportExcel; PSWriteHTML; ThreadJob; PSFramework; BurntToast; PlatyPS"},
        [pscustomobject]@{Lane="LaneA";Function="Evidence Load";Language="Python";Top10LocalFreeLibs="pathlib; json; pandas; polars; duckdb; pyarrow; rich; tqdm; pydantic; typer"},
        [pscustomobject]@{Lane="LaneA";Function="Evidence Load";Language="HTML_JS";Top10LocalFreeLibs="Vanilla JS; Tabulator; Chart.js; Grid.js; Fuse.js; Day.js; Mermaid; Prism.js; Shoelace; FileSaver.js"},

        [pscustomobject]@{Lane="LaneB";Function="VRN Candidate Discovery";Language="PowerShell";Top10LocalFreeLibs="Get-ChildItem; Test-Path; Select-String; PSScriptAnalyzer; Pester; ImportExcel; PSWriteHTML; ThreadJob; PSFramework; PowerShell-Yaml"},
        [pscustomobject]@{Lane="LaneB";Function="VRN Candidate Discovery";Language="Python";Top10LocalFreeLibs="pathlib; re; ast; json; pandas; rich; tqdm; rapidfuzz; networkx; typer"},
        [pscustomobject]@{Lane="LaneB";Function="VRN Candidate Discovery";Language="HTML_JS";Top10LocalFreeLibs="Vanilla JS; Fuse.js; Tabulator; Grid.js; Chart.js; Mermaid; Prism.js; Day.js; Shoelace; FileSaver.js"},

        [pscustomobject]@{Lane="LaneC";Function="Parser / Metadata / Rank";Language="PowerShell";Top10LocalFreeLibs="PSScriptAnalyzer; Pester; Get-FileHash; Microsoft.PowerShell.Management; Microsoft.PowerShell.Utility; ImportExcel; PSWriteHTML; ThreadJob; PSFramework; PlatyPS"},
        [pscustomobject]@{Lane="LaneC";Function="Parser / Metadata / Rank";Language="Python";Top10LocalFreeLibs="ast; libcst; parso; pathlib; hashlib; pandas; rich; tqdm; pydantic; rapidfuzz"},
        [pscustomobject]@{Lane="LaneC";Function="Parser / Metadata / Rank";Language="HTML_JS";Top10LocalFreeLibs="Vanilla JS; Tabulator; Chart.js; Grid.js; Fuse.js; Prism.js; Mermaid; Day.js; Tippy.js; FileSaver.js"},

        [pscustomobject]@{Lane="LaneD";Function="Wrapper Draft Generation";Language="PowerShell";Top10LocalFreeLibs="Microsoft.PowerShell.Management; Microsoft.PowerShell.Utility; PSScriptAnalyzer; Pester; ImportExcel; PSWriteHTML; PSFramework; ThreadJob; PlatyPS; BurntToast"},
        [pscustomobject]@{Lane="LaneD";Function="Wrapper Draft Generation";Language="Python";Top10LocalFreeLibs="pathlib; jinja2; pydantic; typer; rich; pytest; subprocess; pandas; json; hashlib"},
        [pscustomobject]@{Lane="LaneD";Function="Wrapper Draft Generation";Language="HTML_JS";Top10LocalFreeLibs="Vanilla JS; CodeMirror; Prism.js; Tabulator; Grid.js; Chart.js; Mermaid; Shoelace; Fuse.js; FileSaver.js"},

        [pscustomobject]@{Lane="LaneE";Function="Disk / Production HOLD";Language="PowerShell";Top10LocalFreeLibs="Storage; Microsoft.PowerShell.Management; Microsoft.PowerShell.Utility; PSReadLine; ThreadJob; ImportExcel; PSWriteHTML; PSFramework; BurntToast; Pester"},
        [pscustomobject]@{Lane="LaneE";Function="Disk / Production HOLD";Language="Python";Top10LocalFreeLibs="os; pathlib; shutil; psutil; pandas; polars; duckdb; pyarrow; rich; tqdm"},
        [pscustomobject]@{Lane="LaneE";Function="Disk / Production HOLD";Language="HTML_JS";Top10LocalFreeLibs="Vanilla JS; Chart.js; Tabulator; Grid.js; Day.js; Fuse.js; Tippy.js; Shoelace; Mermaid; FileSaver.js"},

        [pscustomobject]@{Lane="LaneF";Function="HTML Matrix / Consolidation";Language="PowerShell";Top10LocalFreeLibs="ImportExcel; PSWriteHTML; Pester; PSScriptAnalyzer; PSFramework; ThreadJob; Microsoft.PowerShell.Archive; Storage; BurntToast; PlatyPS"},
        [pscustomobject]@{Lane="LaneF";Function="HTML Matrix / Consolidation";Language="Python";Top10LocalFreeLibs="pandas; polars; duckdb; pyarrow; pathlib; json; rich; tqdm; networkx; plotly"},
        [pscustomobject]@{Lane="LaneF";Function="HTML Matrix / Consolidation";Language="HTML_JS";Top10LocalFreeLibs="Vanilla JS; Tabulator; Chart.js; Grid.js; Mermaid; Shoelace; Fuse.js; Day.js; Prism.js; FileSaver.js"}
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
            if($c -match "Path|Message|Top10"){$cls="cellBox path"}
            if($c -match "Value|Score|Bytes|Rank|FreeGB|FreePercent"){$cls="cellBox num"}
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
        [array]$CommandRows,
        [array]$Top10Rows,
        [string]$HtmlPath
    )

    $driveCols=@("Drive","Root","Used","Free","FreeGB","FreePercent","Risk")
    $laneCols=@("Lane","Round","Project","Gate","Status","Risk","FixClass","IssueType","Value","Message","Path")
    $candCols=@("CandidateRank","CandidateClass","Score","ParserStatus","ParserErrors","Bytes","Modified","Name","Path","Message")
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
<title>VIA VRN Entry Design Bootstrap v035.5.2</title>
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
table{width:100%;min-width:1450px;border-collapse:separate;border-spacing:0;table-layout:fixed}
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
    <h1>Veritas Intelligence Analytics · VRN Entry Design Bootstrap</h1>
    <p>v035.5.2 · file-mode bootstrap · candidate discovery · wrapper draft · no source write</p>
  </div>
</header>

<section class="kpis">
<div class="kpi"><em>Status</em><b>$(Enc $Runtime.status)</b></div>
<div class="kpi"><em>Risk</em><b>$(Enc $Runtime.risk)</b></div>
<div class="kpi"><em>OK</em><b>$(Enc $Runtime.ok_count)</b></div>
<div class="kpi"><em>WARN/HOLD</em><b>$(Enc $Runtime.warn_count)</b></div>
<div class="kpi"><em>FAIL</em><b>$(Enc $Runtime.fail_count)</b></div>
<div class="kpi"><em>Candidates</em><b>$(Enc $Runtime.candidate_count)</b></div>
<div class="kpi"><em>C Free</em><b>$(Enc $Runtime.c_free)</b></div>
<div class="kpi"><em>Decision</em><b>$(Enc $Runtime.next_decision)</b></div>
</section>

<section class="panel"><h2>Drive Matrix</h2><div class="shell"><table><thead><tr>$(THead $driveCols)</tr></thead><tbody>$(TRows $DriveRows $driveCols)</tbody></table></div></section>
<section class="panel"><h2>Six-Lane Matrix</h2><div class="shell"><table><thead><tr>$(THead $laneCols)</tr></thead><tbody>$(TRows $LaneRows $laneCols)</tbody></table></div></section>
<section class="panel"><h2>VRN Candidate Ranking Matrix</h2><div class="shell"><table><thead><tr>$(THead $candCols)</tr></thead><tbody>$(TRows $CandidateRows $candCols)</tbody></table></div></section>
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
    Write-Host "def VIA · VRN ENTRY DESIGN BOOTSTRAP · v035.5.2" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan

    try { Set-PSReadLineOption -HistorySaveStyle SaveNothing -ErrorAction SilentlyContinue } catch {}

    $rows=@()

    Show-Step 8 "Lane A · Load v035.4 evidence"
    $v0354Runtime = Find-LatestFile -Base (Join-Path $Root "_via_final_sandbox_consolidation_runs") -Filter "VIA_FinalSandboxConsolidationSeal_Runtime_v0354.json"
    $rows += New-Row "LaneA" "Round1" "Evidence" "v035.4 Runtime" ($(if($v0354Runtime){"OK"}else{"WARN"})) ($(if($v0354Runtime){"LOW"}else{"MEDIUM"})) "NONE" "EvidenceLoad" ($(if($v0354Runtime){"FOUND"}else{"MISSING"})) "Loaded latest v035.4 final sandbox seal if available." $v0354Runtime

    Show-Step 20 "Lane B · Discover VRN candidates"
    $candidates=@(Discover-VrnCandidates)
    $best=$null
    if(@($candidates).Count -gt 0){$best=$candidates[0]}

    $rows += New-Row "LaneB" "Round1" "VRN" "Candidate Discovery" ($(if(@($candidates).Count -gt 0){"OK"}else{"WARN"})) ($(if(@($candidates).Count -gt 0){"LOW"}else{"MEDIUM"})) "SEQUENTIAL_REQUIRED" "CandidateDiscovery" ([string]@($candidates).Count) "Candidate discovery completed. No source modified." $Root

    Show-Step 38 "Lane C · Score and validate candidate"
    if($null -ne $best){
        $rows += New-Row "LaneC" "Round1" "VRN" "Best Candidate Selected" "OK" "LOW" "SEQUENTIAL_REQUIRED" "CandidateSelected" "$($best.CandidateClass) / Score $($best.Score)" "Best candidate selected for wrapper draft review only." $best.Path
        $rows += New-Row "LaneC" "Round2" "VRN" "Best Candidate Parser" ($(if($best.ParserStatus -eq "OK"){"OK"}else{"WARN"})) ($(if($best.ParserStatus -eq "OK"){"LOW"}else{"MEDIUM"})) "SEQUENTIAL_REQUIRED" "CandidateParser" ([string]$best.ParserErrors) $best.Message $best.Path
    } else {
        $rows += New-Row "LaneC" "Round1" "VRN" "Best Candidate Selected" "WARN" "MEDIUM" "SEQUENTIAL_REQUIRED" "NoCandidate" "0" "No candidate selected." $ExpectedVrnEntry
    }

    Show-Step 52 "Lane D · Generate wrapper draft"
    $wrapperDraft=New-VrnWrapperDraft -Best $best
    $wrapperSyntax=Test-PsSyntax -Path $wrapperDraft
    $rows += New-Row "LaneD" "Round1" "VRN" "Wrapper Draft Generated" $wrapperSyntax.Status ($(if($wrapperSyntax.Status -eq "OK"){"LOW"}elseif($wrapperSyntax.Status -eq "WARN"){"MEDIUM"}else{"HIGH"})) "PARALLEL_SAFE" "WrapperDraft" ([string]$wrapperSyntax.ErrorCount) $wrapperSyntax.Message $wrapperDraft
    $rows += New-Row "LaneD" "Round2" "VRN" "Expected Entry Write Gate" "HOLD" "MEDIUM" "SEQUENTIAL_REQUIRED" "NoSourceWrite" "HOLD" "Expected Invoke-VRN.ps1 is not created in v035.5.2." $ExpectedVrnEntry
    $rows += New-Row "LaneD" "Round3" "VRN" "Promotion Gate" "HOLD" "MEDIUM" "SEQUENTIAL_REQUIRED" "ManualApprovalRequired" "NOT_SET" "Promotion requires manual review and explicit approval later." $Run

    Show-Step 66 "Lane E · Disk and production HOLD"
    $drive=Get-DriveRows
    $c=@($drive | Where-Object Drive -eq "C" | Select-Object -First 1)[0]
    $rows += New-Row "LaneE" "Round1" "Disk" "Light Sandbox Gate" ($(if([double]$c.FreeGB -ge $MinFreeLightGB){"OK"}else{"FAIL"})) ($(if([double]$c.FreeGB -ge $MinFreeLightGB){"LOW"}else{"HIGH"})) "NONE" "DiskLightGate" "$($c.Free) / $($c.FreePercent)%" "Light sandbox gate requires >= $MinFreeLightGB GB." "C:\"
    $rows += New-Row "LaneE" "Round2" "Disk" "Full Production Gate" ($(if([double]$c.FreeGB -ge $MinFreeFullGB){"OK"}else{"HOLD"})) ($(if([double]$c.FreeGB -ge $MinFreeFullGB){"LOW"}else{"MEDIUM"})) "SEQUENTIAL_REQUIRED" "ProductionDiskHold" "$($c.Free) / $($c.FreePercent)%" "Full production waits until >= $MinFreeFullGB GB." "C:\"
    $rows += New-Row "LaneE" "Round3" "Production" "Confirmation Gate" "HOLD" "MEDIUM" "SEQUENTIAL_REQUIRED" "ConfirmationNotSet" "NOT_SET" "No production confirmation is set. Full production not executed." $Run

    Show-Step 78 "Lane F · Commands and Top10 libs"
    $commands=@(Build-CommandFiles -Best $best -WrapperDraft $wrapperDraft)
    $top10=@(Build-Top10Libs)
    $rows += New-Row "LaneF" "Round1" "Consolidation" "Top10 Local Free Libs" "OK" "LOW" "NONE" "LibMatrix" ([string]@($top10).Count) "Top10 libs matrix generated." (Join-Path $RegDir "VIA_VRNEntryDesignBootstrap_Top10LocalFreeLibs_v03552.csv")
    $rows += New-Row "LaneF" "Round2" "Consolidation" "Command Files" "OK" "LOW" "NONE" "CommandFiles" ([string]@($commands).Count) "Safe sandbox / promotion HOLD / production HOLD commands generated." $CmdDir
    $rows += New-Row "LaneF" "Round3" "Consolidation" "Next Step" "OK" "LOW" "NONE" "Next" "V0356_READY" "Next safe step is review selected candidate, then optionally create guarded VRN entry after approval." $Run

    Show-Step 88 "Classify final result"
    $ok=@($rows | Where-Object Status -eq "OK").Count
    $fail=@($rows | Where-Object Status -eq "FAIL").Count
    $warn=@($rows | Where-Object { $_.Status -eq "WARN" -or $_.Status -eq "HOLD" }).Count
    $seq=@($rows | Where-Object FixClass -eq "SEQUENTIAL_REQUIRED").Count
    $parallel=@($rows | Where-Object FixClass -eq "PARALLEL_SAFE").Count

    $status="VIA_VRN_ENTRY_DESIGN_BOOTSTRAP_READY"
    $risk="LOW"
    $decision="V0356_REVIEW_SELECTED_VRN_CANDIDATE_OR_DISK_RECLAIM"
    if($fail -gt 0){
        $status="VIA_VRN_ENTRY_DESIGN_BOOTSTRAP_BLOCKED_BY_FAIL"
        $risk="HIGH"
        $decision="FIX_FAIL_FIRST"
    } elseif($warn -gt 0 -or $seq -gt 0 -or [double]$c.FreeGB -lt $MinFreeFullGB) {
        $status="VIA_VRN_ENTRY_DESIGN_BOOTSTRAP_READY_WITH_PRODUCTION_HOLD"
        $risk="MEDIUM"
    }

    Show-Step 94 "Write CSV / JSON / HTML"
    $runtimeJson=Join-Path $RuntimeDir "VIA_VRNEntryDesignBootstrap_Runtime_v03552.json"
    $sealJson=Join-Path $SealDir "VIA_VRNEntryDesignBootstrap_Seal_v03552.json"
    $laneCsv=Join-Path $RegDir "VIA_VRNEntryDesignBootstrap_LaneMatrix_v03552.csv"
    $candidateCsv=Join-Path $RegDir "VIA_VRNEntryDesignBootstrap_CandidateMatrix_v03552.csv"
    $driveCsv=Join-Path $RegDir "VIA_VRNEntryDesignBootstrap_DriveMatrix_v03552.csv"
    $commandCsv=Join-Path $RegDir "VIA_VRNEntryDesignBootstrap_CommandMatrix_v03552.csv"
    $top10Csv=Join-Path $RegDir "VIA_VRNEntryDesignBootstrap_Top10LocalFreeLibs_v03552.csv"
    $htmlPath=Join-Path $ReportDir "VIA_VRNEntryDesignBootstrap_Report_v03552.html"

    $runtime=[pscustomobject]@{
        generated_at=[string](Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        status=[string]$status
        risk=[string]$risk
        ok_count=[int]$ok
        warn_count=[int]$warn
        fail_count=[int]$fail
        parallel_safe_count=[int]$parallel
        sequential_required_count=[int]$seq
        candidate_count=[int]@($candidates).Count
        best_candidate_path=($(if($null -ne $best){[string]$best.Path}else{""}))
        best_candidate_score=($(if($null -ne $best){[int]$best.Score}else{0}))
        wrapper_draft=[string]$wrapperDraft
        expected_vrn_entry=[string]$ExpectedVrnEntry
        c_free=[string]$c.Free
        c_free_gb=[double]$c.FreeGB
        c_free_percent=[double]$c.FreePercent
        next_decision=[string]$decision
        mode="VRN_ENTRY_DESIGN_BOOTSTRAP"
        source_modified=$false
        expected_entry_created=$false
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
        drive_csv=[string]$driveCsv
        command_csv=[string]$commandCsv
        top10_libs_csv=[string]$top10Csv
        command_dir=[string]$CmdDir
        wrapper_dir=[string]$WrapperDir
        html=[string]$htmlPath
    }

    @($runtime) | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $runtimeJson -Encoding UTF8
    @($runtime) | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $sealJson -Encoding UTF8
    @($rows) | Export-Csv -LiteralPath $laneCsv -NoTypeInformation -Encoding UTF8BOM
    @($candidates) | Export-Csv -LiteralPath $candidateCsv -NoTypeInformation -Encoding UTF8BOM
    @($drive) | Export-Csv -LiteralPath $driveCsv -NoTypeInformation -Encoding UTF8BOM
    @($commands) | Export-Csv -LiteralPath $commandCsv -NoTypeInformation -Encoding UTF8BOM
    @($top10) | Export-Csv -LiteralPath $top10Csv -NoTypeInformation -Encoding UTF8BOM

    Write-Report -Runtime $runtime -DriveRows $drive -LaneRows $rows -CandidateRows $candidates -CommandRows $commands -Top10Rows $top10 -HtmlPath $htmlPath

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

    Write-Progress -Activity "VIA v035.5.2 VRN Entry Design Bootstrap" -Completed

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "def VIA VRN ENTRY DESIGN BOOTSTRAP COMPLETE · v035.5.2" -ForegroundColor Green
    Write-Host "================================================================================" -ForegroundColor Green
    Write-Host "Status                   : $status"
    Write-Host "Risk                     : $risk"
    Write-Host "OK                       : $ok"
    Write-Host "WARN/HOLD                : $warn"
    Write-Host "FAIL                     : $fail"
    Write-Host "Parallel Safe            : $parallel"
    Write-Host "Sequential Required      : $seq"
    Write-Host "Candidate Count          : $(@($candidates).Count)"
    Write-Host "Best Candidate           : $(if($null -ne $best){$best.Path}else{'NONE'})"
    Write-Host "Best Candidate Score     : $(if($null -ne $best){$best.Score}else{0})"
    Write-Host "Wrapper Draft            : $wrapperDraft"
    Write-Host "Expected VRN Entry       : $ExpectedVrnEntry"
    Write-Host "C Free                   : $($c.Free) / $($c.FreePercent)%"
    Write-Host "Next Decision            : $decision"
    Write-Host "Source Modified          : False"
    Write-Host "Expected Entry Created   : False"
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
    Write-Host "Candidate CSV            : $candidateCsv"
    Write-Host "Command CSV              : $commandCsv"
    Write-Host "Top10 Libs CSV           : $top10Csv"
    Write-Host "Wrapper Dir              : $WrapperDir"
    Write-Host "Command Dir              : $CmdDir"
    Write-Host "HTML                     : $htmlPath"
    Write-Host ""
    Write-Host "PowerShell remains open. VRN entry design bootstrap complete." -ForegroundColor Green
}
catch {
    Write-Progress -Activity "VIA v035.5.2 VRN Entry Design Bootstrap" -Completed
    Write-Host ""
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell remains open. No exit." -ForegroundColor Yellow
}
