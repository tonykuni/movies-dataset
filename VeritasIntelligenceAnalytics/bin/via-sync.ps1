#requires -Version 7.0
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Push-Location $repo
git fetch origin 2>&1 | Out-Host
git merge origin/claude/via-system-followup-tz7k9t 2>&1 | Out-Host
git push origin main 2>&1 | Out-Host
git log --oneline -3 | Out-Host
Pop-Location
