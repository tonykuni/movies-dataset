#requires -Version 7.0
param(
    [Parameter(Mandatory)][string]$Mode,
    [Parameter(Mandatory)][string]$Output,
    [string]$Current = ""
)
# CELERITAS-TEMPLATE-JOIN v1 (no-wrap join, L103-3; batch R16-9; PS 5.1 runs unchanged, only PS7 loads the template)
# ===== [VIA:PS-TEMPLATE:v0101] Celeritas PS7 template: this process only, restore on exit, skip when absent, param() untouched =====
$VIACelTplOwn = $false
if ($PSVersionTable.PSVersion.Major -ge 7) {
    try {
        $VIACelTplFile = $null
        $VIACelTplProbe = $PSScriptRoot
        while ($VIACelTplProbe) {
            $VIACelTplTry = Join-Path $VIACelTplProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
            if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry; break }
            $VIACelTplUp = Split-Path $VIACelTplProbe -Parent
            if ((-not $VIACelTplUp) -or ($VIACelTplUp -eq $VIACelTplProbe)) { break }
            $VIACelTplProbe = $VIACelTplUp
        }
        if ($VIACelTplFile -and (-not (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore))) {
            $VIACelTplKeep = @{}
            foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                $VIACelTplVar = Get-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore
                if ($VIACelTplVar) { $VIACelTplKeep[$VIACelTplName] = $VIACelTplVar.Value }
            }
            try { $null = . $VIACelTplFile -RestoreOnly }
            finally {
                Set-StrictMode -Off
                foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                    Remove-Variable -Name $VIACelTplName -Scope 0 -Force -ErrorAction Ignore
                    if ($VIACelTplKeep.ContainsKey($VIACelTplName)) { Set-Variable -Name $VIACelTplName -Value $VIACelTplKeep[$VIACelTplName] -Scope 0 }
                }
            }
            if (Get-Command Start-CeleritasPS7 -ErrorAction Ignore) {
                if (-not (Get-EventSubscriber -Force -ErrorAction Ignore | Where-Object { $_.SourceIdentifier -eq 'PowerShell.Exiting' })) {
                    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action { try { Restore-CeleritasPS7 } catch { } }
                }
                [void](Start-CeleritasPS7)
                $VIACelTplOwn = $true
            }
        }
    } catch { }
}
# ===== [VIA:PS-TEMPLATE:END] =====

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

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms

$result = @()
$dialog = $null

try {
    switch ($Mode) {
        "Folder" {
            $dialog = [System.Windows.Forms.FolderBrowserDialog]::new()
            $dialog.Description = "VIA Unified Workbench — Select folder"
            $dialog.UseDescriptionForTitle = $true

            if (
                -not [string]::IsNullOrWhiteSpace($Current) -and
                (Test-Path -LiteralPath $Current -PathType Container)
            ) {
                $dialog.SelectedPath = $Current
            }

            if (
                $dialog.ShowDialog() -eq
                [System.Windows.Forms.DialogResult]::OK
            ) {
                $result = @($dialog.SelectedPath)
            }
        }

        "File" {
            $dialog = [System.Windows.Forms.OpenFileDialog]::new()
            $dialog.Multiselect = $false
            $dialog.Filter = "Executable or file|*.exe;*.ps1;*.json;*.jsonl;*.py|All files (*.*)|*.*"

            if (
                -not [string]::IsNullOrWhiteSpace($Current) -and
                (Test-Path -LiteralPath $Current -PathType Leaf)
            ) {
                $dialog.InitialDirectory = Split-Path -Parent $Current
                $dialog.FileName = Split-Path -Leaf $Current
            }

            if (
                $dialog.ShowDialog() -eq
                [System.Windows.Forms.DialogResult]::OK
            ) {
                $result = @($dialog.FileName)
            }
        }

        "Reports" {
            $dialog = [System.Windows.Forms.OpenFileDialog]::new()
            $dialog.Multiselect = $true
            $dialog.Filter = "Research reports|*.pdf;*.docx;*.doc;*.xlsx;*.xls;*.pptx;*.ppt;*.html;*.htm;*.txt;*.md;*.json;*.csv;*.rtf|All files (*.*)|*.*"

            if (
                -not [string]::IsNullOrWhiteSpace($Current) -and
                (Test-Path -LiteralPath $Current -PathType Container)
            ) {
                $dialog.InitialDirectory = $Current
            }

            if (
                $dialog.ShowDialog() -eq
                [System.Windows.Forms.DialogResult]::OK
            ) {
                $result = @($dialog.FileNames)
            }
        }

        "DataFiles" {
            $dialog = [System.Windows.Forms.OpenFileDialog]::new()
            $dialog.Multiselect = $true
            $dialog.Filter = "VDF data|*.csv;*.xlsx;*.xls;*.json;*.jsonl;*.parquet;*.duckdb;*.db;*.sqlite;*.txt;*.yaml;*.yml|All files (*.*)|*.*"

            if (
                -not [string]::IsNullOrWhiteSpace($Current) -and
                (Test-Path -LiteralPath $Current -PathType Container)
            ) {
                $dialog.InitialDirectory = $Current
            }

            if (
                $dialog.ShowDialog() -eq
                [System.Windows.Forms.DialogResult]::OK
            ) {
                $result = @($dialog.FileNames)
            }
        }

        default {
            throw "Unsupported dialog mode: $Mode"
        }
    }
}
finally {
    if ($null -ne $dialog) {
        $dialog.Dispose()
    }
}

$result |
    ConvertTo-Json -Depth 10 |
    Set-Content -LiteralPath $Output -Encoding UTF8

if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
