#requires -Version 7.0
param(
    [switch]$OpenReport,
    [switch]$RunSandboxSelfTest,
    [switch]$SelfTest
)
$ErrorActionPreference = "Continue"
$scriptPath = ""
if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "AIO script not found: $scriptPath"
}
$argsList = @("-ExecutionPolicy", "Bypass", "-File", $scriptPath, "-RegisterLauncher")
if ($OpenReport) { $argsList += "-OpenReport" }
if ($RunSandboxSelfTest) { $argsList += "-RunSandboxSelfTest" }
if ($SelfTest) { $argsList += "-SelfTest" }
& pwsh @argsList