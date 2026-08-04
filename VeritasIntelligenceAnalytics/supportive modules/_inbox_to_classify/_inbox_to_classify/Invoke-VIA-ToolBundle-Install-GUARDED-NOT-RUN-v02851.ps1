#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

param(
    [switch]$ExecuteInstall,
    [string]$ApprovalToken = ""
)

$RequiredToken = "APPROVE_VIA_TOOL_BUNDLE_INSTALL"
if (-not $ExecuteInstall -or $ApprovalToken -ne $RequiredToken) {
    Write-Host "[REVIEW ONLY] Tool install not executed." -ForegroundColor Yellow
    Write-Host "To execute later, run with: -ExecuteInstall -ApprovalToken $RequiredToken"
    Write-Host "PowerShell remains open. No exit." -ForegroundColor Green
    return
}

Write-Host "Install path intentionally disabled in v028.5.1 generated installer. Create a separate approved install gate first." -ForegroundColor Yellow
return
