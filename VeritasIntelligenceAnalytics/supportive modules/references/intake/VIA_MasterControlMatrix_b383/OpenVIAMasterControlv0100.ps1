#requires -Version 7.0
param(
    [string] $Path = $PSScriptRoot,
    [string] $Pattern = 'VIA_MasterControl_Matrix_*.html'
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function def_WriteLine([string] $Msg, [string] $Color = 'Gray') {
    Write-Host $Msg -ForegroundColor $Color
}

function def_ResolveReport([string] $BasePath, [string] $Glob) {
    if ($BasePath -and (Test-Path -LiteralPath $BasePath -PathType Leaf) -and $BasePath.ToLower().EndsWith('.html')) {
        return (Resolve-Path -LiteralPath $BasePath).Path
    }
    $dir = if ($BasePath -and (Test-Path -LiteralPath $BasePath -PathType Container)) { $BasePath } else { (Get-Location).Path }
    $hits = [System.Collections.Generic.List[object]]::new()
    foreach ($f in [System.IO.Directory]::EnumerateFiles($dir, $Glob)) { $hits.Add([System.IO.FileInfo]::new($f)) }
    if ($hits.Count -eq 0) { return $null }
    $latest = $hits.ToArray() | Sort-Object -Property LastWriteTimeUtc -Descending | Select-Object -First 1
    return $latest.FullName
}

try {
    def_WriteLine 'VIA Central Governance Console - 總控面板啟動器 (non-blocking)' 'Cyan'
    $report = def_ResolveReport -BasePath $Path -Glob $Pattern
    if (-not $report) {
        def_WriteLine ("找不到報告 (pattern: {0})。請以 -Path 指定 HTML 或其所在資料夾。" -f $Pattern) 'Yellow'
    }
    else {
        $size = [System.IO.FileInfo]::new($report).Length
        def_WriteLine ("報告: {0}" -f $report) 'Gray'
        def_WriteLine ("大小: {0:N0} bytes" -f $size) 'Gray'
        Start-Process -FilePath $report | Out-Null
        def_WriteLine '已於預設瀏覽器開啟 (非阻塞)。' 'Green'
    }
}
catch {
    def_WriteLine ("啟動器例外: " + $_.Exception.Message) 'Red'
}
finally {
    def_WriteLine 'PowerShell session remains open.' 'DarkGray'
}
