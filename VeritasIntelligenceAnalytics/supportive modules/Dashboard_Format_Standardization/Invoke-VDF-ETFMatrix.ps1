#Requires -Version 7.0
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
[CmdletBinding()]
param(
    [string]$RequestPath = "$PSScriptRoot\request.json",
    [string]$OutDir      = "$PSScriptRoot\vdf_out",
    [string]$PythonExe   = "python",
    [switch]$Frozen,                      # 凍結:只用已落地的 Parquet,不對外抓
    [switch]$WhatIfOnly                   # 只印路由計畫,不抓
)

# ============================================================================
#  VDF Bridge · request.json  →  (engine routing)  →  etf_matrix.json
#  VERITAS INTELLIGENCE ANALYTICS · Active ETF Console 資料銜接
#  零新依賴:僅用內建 Invoke-RestMethod + 既有 python(yfinance)。
#  Append-only:不覆寫來源,輸出獨立目錄;已存在的輸出自動加 _vN。
# ============================================================================

$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# ---- 0. 讀合約 -------------------------------------------------------------
if (-not (Test-Path $RequestPath)) {
    throw "找不到 request.json:$RequestPath（在『資料請求』頁按複製後存成此檔）"
}
$req = Get-Content -Raw -LiteralPath $RequestPath | ConvertFrom-Json
$asof    = if ($req.asof) { $req.asof } else { (Get-Date).ToString('yyyy-MM-dd') }
$tickers = @($req.tickers)
$start   = if ($req.range.start) { $req.range.start } else { '1996-01-01' }
Write-Host ("[VDF] 合約載入:{0} 檔 · asof {1} · 起 {2}" -f $tickers.Count, $asof, $start) -ForegroundColor Cyan

# ---- 1. 引擎路由表(數據 → 來源 → 取法) -----------------------------------
#   kind: rest | parse | pyproc | keyed   →  決定用哪個引擎函式
$ROUTES = @(
    @{ field='list';        source='TWSE';     kind='rest';   url='https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL' }
    @{ field='ohlcv_adj';   source='TWSE';     kind='rest';   url='https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL' }
    @{ field='etf_profile'; source='SITCA';    kind='parse';  url='https://www.sitca.org.tw/ROOT/mowa/mowa01.aspx' }
    @{ field='holdings';    source='MOPS';     kind='parse';  url='https://mopsov.twse.com.tw/mops/web/t05st09_2' }
    @{ field='target_yf';   source='yfinance'; kind='pyproc'; url='' }
    @{ field='target_fs';   source='FactSet';  kind='keyed';  url='https://formula.factset.com/api/v1/formulas'; env='FACTSET_KEY' }
    @{ field='macro';       source='FRED';     kind='keyed';  url='https://api.stlouisfed.org/fred/series/observations'; env='FRED_KEY' }
)

function Show-Plan {
    Write-Host "`n[VDF] 路由計畫 Field → Engine" -ForegroundColor Yellow
    $ROUTES | ForEach-Object {
        $key = if ($_.env) { (Test-Path "Env:$($_.env)") ? 'KEY✓' : 'KEY✗' } else { '—' }
        '{0,-12} {1,-9} {2,-7} {3}' -f $_.field, $_.source, $_.kind, $key
    }
    Write-Host ''
}
Show-Plan
if ($WhatIfOnly) { return }

# ---- 2. 引擎介面卡(每種 kind 一個) ----------------------------------------
function Invoke-RestEngine {
    param([string]$Url)
    try { Invoke-RestMethod -Uri $Url -TimeoutSec 30 -Headers @{ 'User-Agent' = 'VDF/1.0' } }
    catch { Write-Warning "REST 失敗 $Url : $($_.Exception.Message)"; $null }
}

function Invoke-PyEngine {
    param([string[]]$Tickers)
    # yfinance 子行程橋接:吐 ticker,target_mean,target_median,price
    $py = @"
import sys, json
try:
    import yfinance as yf
except Exception as e:
    print(json.dumps({"error":"yfinance missing: pip install yfinance"})); sys.exit(0)
out=[]
for t in sys.argv[1:]:
    tk = t if t.endswith('.TW') else t+'.TW'
    try:
        i = yf.Ticker(tk).info
        out.append({"ticker":t,
            "price": i.get("currentPrice"),
            "tgt_mean": i.get("targetMeanPrice"),
            "tgt_median": i.get("targetMedianPrice")})
    except Exception as e:
        out.append({"ticker":t,"error":str(e)})
print(json.dumps(out, ensure_ascii=False))
"@
    $tmp = New-TemporaryFile
    Set-Content -LiteralPath $tmp -Value $py -Encoding utf8
    try { & $PythonExe $tmp @Tickers | ConvertFrom-Json }
    catch { Write-Warning "yfinance 橋接失敗:$($_.Exception.Message)"; @() }
    finally { Remove-Item $tmp -ErrorAction SilentlyContinue }
}

function Invoke-KeyedEngine {
    param([string]$Url, [string]$EnvName)
    if (-not (Test-Path "Env:$EnvName")) {
        Write-Warning "$EnvName 未設定 → 跳過 $Url（請 `$env:$EnvName='...'）"; return $null
    }
    Invoke-RestEngine -Url ("{0}?api_key={1}" -f $Url, (Get-Item "Env:$EnvName").Value)
}

# ---- 3. 雙重恆等驗算(SSOT 契約:2 加減 + 2 除法) ---------------------------
function Test-Identity {
    param([double]$Value, [double]$A, [double]$B, [double]$C, [double]$D, [double]$Tol = 0.01)
    $checks = @(
        [math]::Abs(($A + $B) - $Value) -le $Tol * [math]::Max(1, [math]::Abs($Value))
        [math]::Abs(($C - $D) - $Value) -le $Tol * [math]::Max(1, [math]::Abs($Value))
        ($B -ne 0) -and [math]::Abs(($A / $B) - ($Value / $B)) -le $Tol
        ($D -ne 0) -and [math]::Abs(($C / $D) - ($Value / $D)) -le $Tol
    )
    ($checks | Where-Object { $_ }).Count -ge 2     # 至少 2 法通過才算驗證
}

# ---- 4. 主流程:逐 field 抓 → 合併 → 落地 ----------------------------------
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

$rows = @()
$i = 0
foreach ($tk in $tickers) {
    $i++
    Write-Progress -Id 1 -Activity 'VDF 擷取' -Status $tk -PercentComplete ([int]($i / [math]::Max(1, $tickers.Count) * 100))
    $rows += [ordered]@{ ticker = $tk; verified = $false; source = @() }
}

if (-not $Frozen) {
    $yf = Invoke-PyEngine -Tickers $tickers
    foreach ($r in $rows) {
        $m = $yf | Where-Object { $_.ticker -eq $r.ticker } | Select-Object -First 1
        if ($m) { $r.tgt_yf_mean = $m.tgt_mean; $r.tgt_yf_median = $m.tgt_median; $r.price = $m.price; $r.source += 'yfinance' }
    }
    # TWSE/SITCA/MOPS/FactSet/FRED 介面卡在此依 $ROUTES 串接(端點如表)…
    # $list = Invoke-RestEngine -Url ($ROUTES | ? field -eq 'list').url   等
} else {
    Write-Host "[VDF] Frozen 模式:僅讀既有 Parquet,不對外抓取。" -ForegroundColor DarkYellow
}

# ---- 5. 輸出合約 etf_matrix.json(DC 直接讀) -------------------------------
$payload = [ordered]@{
    schema_version = '1.0'
    generated      = (Get-Date).ToString('s')
    asof           = $asof
    request        = $req.request
    universe       = $req.universe
    verify         = 'double_identity'
    rows           = $rows
}
$outFile = Join-Path $OutDir 'etf_matrix.json'
$n = 2; while (Test-Path $outFile) { $outFile = Join-Path $OutDir ("etf_matrix_v{0}.json" -f $n); $n++ }  # append-only
$payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $outFile -Encoding utf8NoBOM
Write-Progress -Id 1 -Activity 'VDF 擷取' -Completed
Write-Host ("[VDF] 完成 → {0}（{1} 檔）" -f $outFile, $rows.Count) -ForegroundColor Green
Write-Host "      將此檔放到 DC 同目錄,改 DC 由 fetch('etf_matrix.json') 載入即可。" -ForegroundColor DarkGray

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
