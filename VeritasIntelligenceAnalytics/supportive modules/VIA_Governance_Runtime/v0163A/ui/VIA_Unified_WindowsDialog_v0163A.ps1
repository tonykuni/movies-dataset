#requires -Version 7.0
param(
    [Parameter(Mandatory)][string]$Mode,
    [Parameter(Mandatory)][string]$Output,
    [string]$Current = ""
)
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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
