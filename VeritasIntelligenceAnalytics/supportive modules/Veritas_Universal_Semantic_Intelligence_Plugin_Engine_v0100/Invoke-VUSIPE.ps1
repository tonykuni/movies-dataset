[CmdletBinding()]
param(
    [ValidateSet('SelfTest','Capabilities','Invoke','Jsonl','Http')]
    [string]$Mode = 'SelfTest',
    [string]$RequestFile = '',
    [string]$RuntimeDir = '.\vusipe_runtime',
    [string]$PythonExe = 'python',
    [string]$HostAddress = '127.0.0.1',
    [int]$Port = 8765
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Engine = Join-Path $Root 'VUSIPE.py'
$Adapter = Join-Path $Root 'adapter.py'

function Invoke-VUSIPEPython {
    param([string[]]$Arguments)
    & $PythonExe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "VUSIPE exited with code $LASTEXITCODE" }
}

switch ($Mode) {
    'SelfTest' { Invoke-VUSIPEPython @($Engine, '--runtime-dir', $RuntimeDir, 'self-test') }
    'Capabilities' { Invoke-VUSIPEPython @($Engine, '--runtime-dir', $RuntimeDir, 'capabilities') }
    'Invoke' {
        if (-not (Test-Path -LiteralPath $RequestFile -PathType Leaf)) { throw 'RequestFile is required.' }
        Invoke-VUSIPEPython @($Engine, '--runtime-dir', $RuntimeDir, 'invoke', '--request-file', $RequestFile)
    }
    'Jsonl' { Invoke-VUSIPEPython @($Adapter, 'jsonl', '--runtime-dir', $RuntimeDir) }
    'Http' { Invoke-VUSIPEPython @($Adapter, 'http', '--runtime-dir', $RuntimeDir, '--host', $HostAddress, '--port', "$Port") }
}
