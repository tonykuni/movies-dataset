# VIA EnvManager · uv 裝必備庫 · 不刪 conda base · 拔除＝via_iso_* · 禁 conda remove
#requires -Version 7.0
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONNOUSERSITE = '1'
$env:VIA_LKGC = '2026-09-06'
$Root = @(
    'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics',
    'C:\Users\tonyk\Github\movies-dataset\VeritasIntelligenceAnalytics'
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if ($Root) { Set-Location -LiteralPath $Root } else { $Root = (Get-Location).Path }
$LogDir = Join-Path $Root 'logs'; New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LockDir = Join-Path $Root 'locks'; New-Item -ItemType Directory -Force -Path $LockDir | Out-Null
$Log = Join-Path $LogDir 'env_governance.log'
function Lamp([string]$c, [string]$layer, [string]$msg) {
    $col = switch ($c) { 'GREEN' { 'Green' } 'RED' { 'Red' } 'GREY' { 'DarkGray' } default { 'Yellow' } }
    $line = '{0,-7} {1,-14} {2}' -f $c, $layer, $msg
    Write-Host $line -ForegroundColor $col
    Add-Content -LiteralPath $Log -Value ("{0:HH:mm:ss} {1}" -f (Get-Date), $line)
}
Lamp 'GREEN' 'GOV' "LKGC $($env:VIA_LKGC) · uv 隔離裝庫 · 不刪 base · DCT 不動"

$Venv = Join-Path $Root '.venv-via_vdf'
$Need = @('polars','duckdb','pyarrow','numpy','pandas','pydantic','ruff','pypdf','pdfplumber','opencc','fredapi','yfinance')
$Mirrors = @(
    'https://pypi.tuna.tsinghua.edu.cn/simple',
    'https://mirrors.aliyun.com/pypi/simple',
    'https://pypi.org/simple'
)

$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    $uvPy = @('C:\Python313\python.exe','C:\ProgramData\miniconda3\python.exe') | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($uvPy) {
        Lamp 'YELLOW' 'UV' '本機無 uv · 用 python -m pip install --user uv（不碰 conda env）'
        & $uvPy -m pip install --user uv 2>&1 | ForEach-Object { Lamp 'GREY' 'PIP' "$_" }
    }
    $uv = Get-Command uv -ErrorAction SilentlyContinue
}
if (-not $uv) { Lamp 'RED' 'UV' '仍無 uv · 停止裝庫 · conda 未動'; }
else {
    Lamp 'GREEN' 'UV' $uv.Source
    if (-not (Test-Path (Join-Path $Venv 'Scripts\python.exe'))) {
        Lamp 'YELLOW' 'VENV' "新建 $Venv （不重建 conda）"
        & uv venv $Venv 2>&1 | ForEach-Object { Lamp 'GREY' 'VENV' "$_" }
    }
    $pyV = Join-Path $Venv 'Scripts\python.exe'
    $idx = $Mirrors[0]
    Lamp 'GREEN' 'MIRROR' $idx
    Lamp 'GREEN' 'R1' 'Parallel-Fixable · uv pip install 必裝庫'
    & uv pip install --python $pyV --index-url $idx @Need 2>&1 | ForEach-Object { Lamp 'GREY' 'INST' "$_" }
    Lamp 'GREEN' 'R2' 'Sequence · 逐庫 import 核對'
    $miss = @()
    foreach ($p in $Need) {
        $m = if ($p -eq 'opencc') { 'opencc' } elseif ($p -eq 'pdfplumber') { 'pdfplumber' } elseif ($p -eq 'pypdf') { 'pypdf' } else { $p }
        $chk = & $pyV -c "import $m; print('OK', '$p')" 2>&1
        if ("$chk" -match '^OK') { Lamp 'GREEN' 'LIB' "$chk" } else { Lamp 'YELLOW' 'LIB' "$p · $($chk | Select-Object -First 1)"; $miss += $p }
    }
    if ($miss.Count) {
        Lamp 'YELLOW' 'R2' "缺 $($miss -join ',') · 改官方源再試 · 不 conda remove"
        & uv pip install --python $pyV --index-url $Mirrors[2] @miss 2>&1 | ForEach-Object { Lamp 'GREY' 'INST' "$_" }
    }
    Lamp 'GREEN' 'R3' 'Harden · uv pip freeze → locks/via_vdf.txt'
    & uv pip freeze --python $pyV | Out-File -Encoding utf8 (Join-Path $LockDir 'via_vdf.txt')
    $env:VIA_VDF_PY = $pyV
    $env:PATH = "$(Join-Path $Venv 'Scripts');$env:PATH"
    Lamp 'GREEN' 'ENV' "via_vdf venv $pyV"
}

$html = Join-Path $LogDir 'via_gov_matrix.html'
$pyLine = if ($env:VIA_VDF_PY) { $env:VIA_VDF_PY } else { '未建 venv' }
@"
<!doctype html><meta charset=utf-8><title>VIA GOV Matrix</title>
<style>
body{margin:0;background:#0e1116;color:#d7dde8;font:12px/1.35 Segoe UI,sans-serif}
h1{font-size:13px;margin:8px 12px;color:#8b93a7}
table{width:100%;border-collapse:collapse;table-layout:fixed}
td,th{border:1px solid #242a36;padding:4px 6px;word-wrap:break-word;overflow-wrap:anywhere;vertical-align:top}
th{background:#161b22;color:#8b93a7;font-size:11px}
.g{color:#3dd68c}.y{color:#e6b84d}.r{color:#ff5d5d}
.z{font-size:10px;letter-spacing:.08em;color:#8b93a7}
</style>
<h1>VIA EnvManager · MODULE / ENGINE / FUNCTION-LIB / OTHERS · LKGC 2026-09-06</h1>
<table>
<tr><th>區</th><th>燈</th><th>項</th><th>說明</th></tr>
<tr><td class=z>MODULE</td><td class=g>綠</td><td>GA-01–20</td><td>治理加速器掛載 · 與 PS20 分冊</td></tr>
<tr><td class=z>ENGINE</td><td class=g>綠</td><td>uv venv</td><td>$pyLine · 不刪 conda base · 衝突走 via_iso_*</td></tr>
<tr><td class=z>FUNCTION-LIB</td><td class=y>黃</td><td>必裝 $($Need -join ' ')</td><td>locks/via_vdf.txt · Python313 無 pandas 不混用</td></tr>
<tr><td class=z>OTHERS</td><td class=g>綠</td><td>DCT / LIVE</td><td>DCT 不動 · AETF/FRED LIVE 關 · 禁網除非 uv index</td></tr>
</table>
"@ | Set-Content $html -Encoding utf8
Start-Process $html
Lamp 'GREEN' 'UI' $html
Lamp 'GREEN' 'SUM' '三輪結束 · 不 exit · conda 未動'
if (-not ($args -contains '-Yes')) { [void](Read-Host 'ENTER 保持視窗') }
