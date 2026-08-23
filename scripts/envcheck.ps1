<#
.SYNOPSIS
  envcheck.ps1 — 監測環境衝突快篩(local free libs Top 8 · uv 加速)Windows 版
.DESCRIPTION
  鏡像:清華 → 阿里 → 官方 PyPI 兜底(自動探測,失聯即切換)。
  與 scripts/envcheck.sh 同功能;相容 Windows PowerShell 5.1 / PowerShell 7。
.PARAMETER Mode
  fast(預設)| full | tree | why | resolve | info | lock | setup | doctor
.PARAMETER Target
  why/info/lock 的目標套件或檔案;resolve 可給多個規格
.EXAMPLE
  .\scripts\envcheck.ps1                      # 秒級快篩
  .\scripts\envcheck.ps1 why numpy            # 反查誰依賴 numpy
  .\scripts\envcheck.ps1 resolve "torch" "numpy==1.26.4"   # 裝前衝突預測
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('fast', 'full', 'tree', 'why', 'resolve', 'info', 'lock', 'setup', 'doctor')]
    [string]$Mode = 'fast',

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$Target
)

$ErrorActionPreference = 'Continue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$TsinghuaUrl = 'https://pypi.tuna.tsinghua.edu.cn/simple'
$AliyunUrl   = 'https://mirrors.aliyun.com/pypi/simple/'
$OfficialUrl = 'https://pypi.org/simple'
$script:FailCount = 0

function Test-IndexUrl([string]$Url) {
    try {
        $probe = Invoke-WebRequest -Uri ($Url.TrimEnd('/') + '/pip/') -Method Head `
            -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        return ($probe.StatusCode -ge 200 -and $probe.StatusCode -lt 400)
    } catch { return $false }
}

function Set-IndexEnv {
    $choice = $env:ENVCHECK_INDEX
    if (-not $choice -or $choice -eq 'auto') {
        if (Test-IndexUrl $TsinghuaUrl)   { $choice = 'tsinghua' }
        elseif (Test-IndexUrl $AliyunUrl) { $choice = 'aliyun' }
        else                              { $choice = 'official' }
    }
    $env:UV_NO_CONFIG = '1'   # 索引全由本腳本指定,不受 cwd 設定檔影響
    switch ($choice) {
        'tsinghua' {
            $env:UV_INDEX = "$TsinghuaUrl $AliyunUrl"
            $env:UV_DEFAULT_INDEX = $OfficialUrl
            $env:PIP_INDEX_URL = $TsinghuaUrl
            $env:PIP_EXTRA_INDEX_URL = "$AliyunUrl $OfficialUrl"
        }
        'aliyun' {
            $env:UV_INDEX = $AliyunUrl
            $env:UV_DEFAULT_INDEX = $OfficialUrl
            $env:PIP_INDEX_URL = $AliyunUrl
            $env:PIP_EXTRA_INDEX_URL = $OfficialUrl
        }
        default {
            Remove-Item Env:UV_INDEX -ErrorAction SilentlyContinue
            $env:UV_DEFAULT_INDEX = $OfficialUrl
            $env:PIP_INDEX_URL = $OfficialUrl
            Remove-Item Env:PIP_EXTRA_INDEX_URL -ErrorAction SilentlyContinue
        }
    }
    $script:IndexChosen = $choice
    Write-Host "◆ 索引:$choice(官方 PyPI 兜底)" -ForegroundColor Cyan
}

function Find-TargetPython {
    if ($env:ENVCHECK_PY) { return $env:ENVCHECK_PY }
    foreach ($cand in @('.venv\Scripts\python.exe', '.venv\bin\python')) {
        if (Test-Path $cand) { return (Resolve-Path $cand).Path }
    }
    $sys = Get-Command python -ErrorAction SilentlyContinue
    if ($sys) { return $sys.Source }
    return $null
}

function Test-UvPresent {
    if (Get-Command uv -ErrorAction SilentlyContinue) { return $true }
    Write-Host "✘ 未找到 uv(Top 1 工具兼加速器)。安裝:" -ForegroundColor Red
    Write-Host "    pip install uv -i $TsinghuaUrl"
    Write-Host "    或 powershell -c `"irm https://astral.sh/uv/install.ps1 | iex`""
    return $false
}

function Invoke-Step([string]$Name, [scriptblock]$Body) {
    Write-Host "▶ $Name"
    & $Body
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✔ $Name" -ForegroundColor Green
    } else {
        Write-Host "  ✘ $Name(exit=$LASTEXITCODE)" -ForegroundColor Yellow
        $script:FailCount++
    }
}

function Invoke-FastChecks {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Invoke-Step 'uv pip check(已裝套件相容性)' { uv pip check --python $script:Py }
        Invoke-Step 'pipdeptree --warn fail(依賴樹衝突)' { uvx pipdeptree --python $script:Py --warn fail | Out-Null }
    } else {
        Invoke-Step 'pip check(未裝 uv 的退路)' { & $script:Py -m pip check }
    }
}

function Invoke-FullChecks {
    Invoke-FastChecks
    if ((Test-Path 'pyproject.toml') -or (Test-Path 'requirements.txt')) {
        Invoke-Step 'deptry(依賴宣告 vs 實際 import)' { uvx deptry . }
    }
    if (Test-Path 'requirements.txt') {
        if ($env:ENVCHECK_NO_MUTATE -eq '1') {
            Write-Host '  (ENVCHECK_NO_MUTATE=1,略過 pip-check-reqs)'
        } else {
            Invoke-Step 'pip-check-reqs(需求清單漂移)' {
                uv pip install -q --python $script:Py pip-check-reqs
                if ($LASTEXITCODE -eq 0) {
                    $vbin = Split-Path $script:Py
                    & (Join-Path $vbin 'pip-missing-reqs.exe') --requirements-file=requirements.txt .
                    if ($LASTEXITCODE -eq 0) {
                        & (Join-Path $vbin 'pip-extra-reqs.exe') --requirements-file=requirements.txt .
                    }
                }
            }
        }
        Invoke-Step 'uv --dry-run(整組需求解析預演)' {
            uv pip install --dry-run -q -r requirements.txt --python $script:Py
        }
    }
}

function Invoke-Doctor {
    $uvVer = ''
    if (Get-Command uv -ErrorAction SilentlyContinue) { $uvVer = (uv --version) } else { $uvVer = '未安裝' }
    Write-Host "◆ uv:$uvVer"
    Write-Host "◆ python:$(& $script:Py --version 2>&1)($script:Py)"
    foreach ($row in @(@('清華', $TsinghuaUrl), @('阿里', $AliyunUrl), @('官方', $OfficialUrl))) {
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        if (Test-IndexUrl $row[1]) {
            Write-Host "◆ 鏡像 $($row[0]):可用($($sw.ElapsedMilliseconds)ms)"
        } else {
            Write-Host "◆ 鏡像 $($row[0]):失聯"
        }
    }
    Write-Host "◆ 本次選用:$script:IndexChosen"
    if (Get-Command uv -ErrorAction SilentlyContinue) { Write-Host "◆ uv cache:$(uv cache dir)" }
}

Set-IndexEnv
$script:Py = Find-TargetPython
if (-not $script:Py) { Write-Host '✘ 找不到 python 直譯器' -ForegroundColor Red; exit 2 }

switch ($Mode) {
    'fast'    { if (-not (Test-UvPresent)) { } ; Invoke-FastChecks }
    'full'    { if (-not (Test-UvPresent)) { exit 2 }; Invoke-FullChecks }
    'tree'    { if (-not (Test-UvPresent)) { exit 2 }; uvx pipdeptree --python $script:Py; exit $LASTEXITCODE }
    'why'     { if (-not (Test-UvPresent)) { exit 2 }
                if (-not $Target) { Write-Host '用法:envcheck.ps1 why <pkg>'; exit 2 }
                uvx pipdeptree --python $script:Py -r -p $Target[0]; exit $LASTEXITCODE }
    'resolve' { if (-not (Test-UvPresent)) { exit 2 }
                if (-not $Target) { Write-Host '用法:envcheck.ps1 resolve <spec…>'; exit 2 }
                uvx pipgrip --tree @Target; exit $LASTEXITCODE }
    'info'    { if (-not (Test-UvPresent)) { exit 2 }
                if (-not $Target) { Write-Host '用法:envcheck.ps1 info <pkg>'; exit 2 }
                uvx johnnydep $Target[0] --fields name version_latest requires; exit $LASTEXITCODE }
    'lock'    { if (-not (Test-UvPresent)) { exit 2 }
                $reqFile = 'requirements.txt'; if ($Target) { $reqFile = $Target[0] }
                uvx --from pip-tools pip-compile --dry-run $reqFile; exit $LASTEXITCODE }
    'setup'   { if (-not (Test-UvPresent)) { exit 2 }
                if (-not (Test-Path '.venv')) { Invoke-Step 'uv venv .venv' { uv venv .venv } }
                $script:Py = Find-TargetPython
                if (Test-Path 'requirements.txt') {
                    Invoke-Step 'uv pip install -r requirements.txt' {
                        uv pip install -q -r requirements.txt --python $script:Py
                    }
                } }
    'doctor'  { Invoke-Doctor; exit 0 }
}

Write-Host '───────────────────────────────'
if ($script:FailCount -eq 0) {
    Write-Host "✅ 環境衝突檢測全數通過(python=$script:Py,索引=$script:IndexChosen)" -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️  發現 $script:FailCount 項問題(python=$script:Py)——詳見上方 ✘ 步驟輸出" -ForegroundColor Yellow
    exit 1
}
