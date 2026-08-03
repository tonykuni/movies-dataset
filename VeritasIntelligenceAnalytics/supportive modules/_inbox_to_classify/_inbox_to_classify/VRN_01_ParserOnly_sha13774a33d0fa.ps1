$Target = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VRN\Invoke-VRN.ps1"
if(-not $Target -or -not(Test-Path -LiteralPath $Target -PathType Leaf)){ Write-Host "[WARN] Missing target: $Target" -ForegroundColor Yellow; return }
$tokens=$null; $errors=$null
[System.Management.Automation.Language.Parser]::ParseFile($Target,[ref]$tokens,[ref]$errors)|Out-Null
if(@($errors).Count -eq 0){ Write-Host "[OK] ParserOnly passed." -ForegroundColor Green } else { Write-Host "[FAIL] Parser errors: $(@($errors).Count)" -ForegroundColor Red; @($errors | Select-Object -First 10) | ForEach-Object { Write-Host $_.Message -ForegroundColor Red } }