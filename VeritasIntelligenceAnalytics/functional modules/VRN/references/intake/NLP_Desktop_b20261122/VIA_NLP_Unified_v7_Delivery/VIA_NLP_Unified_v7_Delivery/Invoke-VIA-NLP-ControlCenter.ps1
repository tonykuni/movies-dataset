#requires -Version 7.0
[CmdletBinding()]
param(
    [int]$Port = 8765,
    [switch]$OpenBrowser,
    [switch]$Foreground
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-Python {
    foreach ($candidate in @('python', 'python3', 'py')) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($null -ne $command) { return $command.Source }
    }
    throw 'Python 3.9+ was not found.'
}

$python = Resolve-Python
$server = Join-Path $PSScriptRoot 'via_nlp_control_api.py'
if (-not (Test-Path -LiteralPath $server -PathType Leaf)) { throw "Missing API server: $server" }
$url = "http://localhost:$Port/"

if ($Foreground) {
    Write-Host "Starting VIA NLP Control Center at $url" -ForegroundColor Green
    & $python $server --host 0.0.0.0 --port $Port
    exit $LASTEXITCODE
}

$argumentList = @($server, '--host', '0.0.0.0', '--port', $Port.ToString())
$process = Start-Process -FilePath $python -ArgumentList $argumentList -WorkingDirectory $PSScriptRoot -PassThru
Start-Sleep -Milliseconds 800
Write-Host "VIA NLP Control Center started: $url" -ForegroundColor Green
Write-Host "PID=$($process.Id)  Stop with: Stop-Process -Id $($process.Id)" -ForegroundColor DarkGray
if ($OpenBrowser) { Start-Process $url }
