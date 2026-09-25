[CmdletBinding()]
param(
    [switch]$StrictToolAvailability,
    [switch]$WaitForKey
)

$ErrorActionPreference = "Stop"
$EngineRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $EngineRoot ".venv\Scripts\python.exe"
$Python = if (Test-Path -LiteralPath $VenvPython) { $VenvPython } else { "python" }
$NodeTest = Join-Path $EngineRoot "tests\node.test.mjs"
$Fixture = Join-Path $EngineRoot "tests\fixtures\broken.md"
$LinkTargetFixture = Join-Path $EngineRoot "tests\fixtures\missing.md"
$TemporaryRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("MarkdownEditingEngine-Test-" + [guid]::NewGuid())

function defAssert-ExitCode {
    param([Parameter(Mandatory)][string]$Name, [Parameter(Mandatory)][int]$Code)
    if ($Code -ne 0) { throw "$Name failed with exit code $Code." }
}

function defMain {
    New-Item -ItemType Directory -Path $TemporaryRoot -Force | Out-Null
    try {
        & $Python -m unittest discover -s (Join-Path $EngineRoot "tests") -p "test_*.py" -v
        defAssert-ExitCode -Name "Python unit tests" -Code $LASTEXITCODE
        if (Get-Command node -ErrorAction SilentlyContinue) {
            & node --test $NodeTest
            defAssert-ExitCode -Name "Node tests" -Code $LASTEXITCODE
        } elseif ($StrictToolAvailability) { throw "Node is unavailable." }
        $CSpell = Join-Path $EngineRoot "node_modules\.bin\cspell.cmd"
        if (Test-Path -LiteralPath $CSpell) {
            & $CSpell lint --config (Join-Path $EngineRoot "config\cspell.json") --no-progress --no-summary (Join-Path $EngineRoot "tests\fixtures\simple.md")
            defAssert-ExitCode -Name "CSpell offline validation" -Code $LASTEXITCODE
        } elseif ($StrictToolAvailability) { throw "CSpell is unavailable." }

        $First = Join-Path $TemporaryRoot "first.md"
        Copy-Item -LiteralPath $Fixture -Destination $First
        Copy-Item -LiteralPath $LinkTargetFixture -Destination (Join-Path $TemporaryRoot "missing.md")
        & $Python (Join-Path $EngineRoot "engine\markdown_engine.py") fix --input $First --formatter prettier --strict
        defAssert-ExitCode -Name "First integration pass" -Code $LASTEXITCODE
        $FirstHash = (Get-FileHash -LiteralPath $First -Algorithm SHA256).Hash
        & $Python (Join-Path $EngineRoot "engine\markdown_engine.py") fix --input $First --formatter prettier --strict
        defAssert-ExitCode -Name "Second integration pass" -Code $LASTEXITCODE
        $SecondHash = (Get-FileHash -LiteralPath $First -Algorithm SHA256).Hash
        if ($FirstHash -ne $SecondHash) { throw "Idempotency check failed." }

        $StressRoot = Join-Path $TemporaryRoot "stress"
        New-Item -ItemType Directory -Path $StressRoot -Force | Out-Null
        1..12 | ForEach-Object {
            Copy-Item -LiteralPath (Join-Path $EngineRoot "tests\fixtures\simple.md") -Destination (Join-Path $StressRoot "sample-$_.md")
        }
        $StressReport = Join-Path $TemporaryRoot "stress-report.json"
        & $Python (Join-Path $EngineRoot "engine\markdown_engine.py") analyze-structure --input $StressRoot --strict --workers 4 --report $StressReport
        defAssert-ExitCode -Name "Parallel stress pass" -Code $LASTEXITCODE
        $StressPayload = Get-Content -LiteralPath $StressReport -Raw | ConvertFrom-Json
        if ($StressPayload.effective_workers -ne 4 -or $StressPayload.summary.files -ne 12 -or $StressPayload.summary.failed -ne 0) {
            throw "Parallel stress report did not record four workers and twelve passing files."
        }
    }
    finally {
        Remove-Item -LiteralPath $TemporaryRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

defMain
[Environment]::ExitCode = 0
if ($WaitForKey) {
    Read-Host "全部測試完成，按 Enter 關閉"
}
