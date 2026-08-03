# VRN · Safe Stream 01 · ParserOnly
$Target = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\60_PowerShell_Entry_Internal\Invoke-VRN-MQ-NoOCR-Staging-v222.ps1"
if(-not $Target -or -not(Test-Path -LiteralPath $Target -PathType Leaf)){ Write-Host "[WARN] Missing target: $Target" -ForegroundColor Yellow; return }
$tokens=$null; $errors=$null
[System.Management.Automation.Language.Parser]::ParseFile($Target,[ref]$tokens,[ref]$errors)|Out-Null
if(@($errors).Count -eq 0){ Write-Host "[OK] ParserOnly passed." -ForegroundColor Green } else { Write-Host "[FAIL] Parser errors: $(@($errors).Count)" -ForegroundColor Red; @($errors | Select-Object -First 10) | ForEach-Object { Write-Host $_.Message -ForegroundColor Red } }