#requires -Version 7.0
param([string]$AppRoot=(Split-Path -Parent $PSScriptRoot))
Set-Location $AppRoot
$py=Get-Command python -ErrorAction Stop
& $py.Source "engines\workops_backup_restore.py" backup
