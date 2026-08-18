#requires -Version 7.0
param(
    [Parameter(Mandatory)][string]$Mode,
    [Parameter(Mandatory)][string]$Output,
    [string]$Current = ""
)

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
