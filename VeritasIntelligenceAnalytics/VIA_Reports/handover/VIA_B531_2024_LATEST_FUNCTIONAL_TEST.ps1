[CmdletBinding()]
param(
    [string]$FromDate = '2024-01-01',
    [switch]$Pull,
    [switch]$EnableNetwork,
    [switch]$InstallOpenCC,
    [switch]$RebuildOCREnvironment,
    # Legacy compatibility switch only: TA-Lib/TA-One is prohibited and is never executed.
    [switch]$RunTAOne,
    [string]$DaytradeFile = '',
    [switch]$Publish,
    [switch]$OpenReport
)

$ErrorActionPreference = 'Continue'
$VIA = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
$Branch = 'claude/via-envmanager-governance-7cls8h'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$OutDir = Join-Path $VIA "VIA_Reports\handover\B531_2024_latest_$Stamp"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Log = Join-Path $OutDir 'B531_console.log'
$Summary = Join-Path $OutDir 'B531_summary.md'
Start-Transcript -Path $Log -Force | Out-Null

function Invoke-Step {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][scriptblock]$Action
    )
    Write-Host "`n=== $Name ===" -ForegroundColor Cyan
    try {
        & $Action
        $rc = if ($null -eq $LASTEXITCODE) { 0 } else { [int]$LASTEXITCODE }
    } catch {
        Write-Host "[EXCEPTION] $($_.Exception.Message)" -ForegroundColor Red
        $rc = 1
    }
    if ($rc -eq 0) { Write-Host "[PASS] $Name" -ForegroundColor Green }
    else { Write-Host "[RESULT $rc] $Name" -ForegroundColor Yellow }
    return $rc
}

function Invoke-IfCommand {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][scriptblock]$Action
    )
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        Write-Host "[ABSENT] $Name 未在目前 PowerShell 視窗註冊；不假裝執行。" -ForegroundColor Yellow
        return 2
    }
    return (Invoke-Step -Name $Name -Action $Action)
}

function Invoke-VIAPost2024DatabaseCheck {
    param(
        [Parameter(Mandatory=$true)][string]$Database,
        [Parameter(Mandatory=$true)][string]$From,
        [Parameter(Mandatory=$true)][string]$OutputJson
    )
    $py = Get-VIAEnvPython "vdf"
    if (-not $py -or -not (Test-Path -LiteralPath $py)) {
        Write-Host "[ABSENT] VDF Python 環境不存在，無法執行只讀 DuckDB 核驗：$py" -ForegroundColor Yellow
        return 2
    }
    $probe = Join-Path $env:TEMP ("via_b531_post2024_{0}.py" -f $Stamp)
    @'
import json
import sys
import duckdb

db = sys.argv[1]
start = sys.argv[2]
con = duckdb.connect(db, read_only=True)
out = {"database": db, "from": start}
overall = con.execute("""
    select count(*), count(distinct ticker), min(cast(date as date)), max(cast(date as date))
    from tw_daily_prices where ticker <> '_NOOP_' and cast(date as date) >= cast(? as date)
""", [start]).fetchone()
out["overall"] = {"rows": overall[0], "tickers": overall[1], "min_date": str(overall[2]), "max_date": str(overall[3])}
out["years"] = []
for year in (2024, 2025, 2026):
    dates = con.execute("""
        select count(distinct cast(date as date))
        from tw_daily_prices where ticker <> '_NOOP_' and year(cast(date as date)) = ?
    """, [year]).fetchone()[0]
    rows = con.execute("""
        select count(*), count(distinct ticker)
        from tw_daily_prices where ticker <> '_NOOP_' and year(cast(date as date)) = ?
    """, [year]).fetchone()
    full = con.execute("""
        with d as (
            select count(distinct cast(date as date)) n
            from tw_daily_prices where ticker <> '_NOOP_' and year(cast(date as date)) = ?
        ), t as (
            select ticker, count(distinct cast(date as date)) n
            from tw_daily_prices where ticker <> '_NOOP_' and year(cast(date as date)) = ?
            group by ticker
        )
        select sum(case when t.n = d.n then 1 else 0 end), count(*) from t cross join d
    """, [year, year]).fetchone()
    out["years"].append({"year": year, "market_dates": dates, "rows": rows[0], "tickers": rows[1], "full_market_dates": full[0] or 0, "tickers_checked": full[1] or 0})
con.close()
print(json.dumps(out, ensure_ascii=False, indent=2))
'@ | Set-Content -LiteralPath $probe -Encoding UTF8
    try {
        & $py $probe $Database $From | Tee-Object -FilePath $OutputJson
        return [int]$LASTEXITCODE
    } finally {
        Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue
    }
}

try {
    Set-Location -LiteralPath $VIA
    $Register = (Get-ChildItem -LiteralPath $VIA -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName
    if (-not $Register) { throw '找不到 Register-VIA-Commands-v*.ps1' }
    . $Register

    $MarketJson = Join-Path $VIA 'VIA_Reports\vdf\central_lists\MARKET_LISTS_latest.json'
    $LatestDate = 'latest'
    if (Test-Path -LiteralPath $MarketJson) {
        try {
            $Market = Get-Content -LiteralPath $MarketJson -Raw -Encoding UTF8 | ConvertFrom-Json
            $LatestDate = [string]$Market.lists.tw_stock_universe.prices.max
            if ([string]::IsNullOrWhiteSpace($LatestDate)) { $LatestDate = 'latest' }
        } catch { $LatestDate = 'latest' }
    }

    $env:VIA_TEST_FROM = $FromDate
    $env:VIA_TEST_TO = $LatestDate
    $env:VIA_TEST_SCOPE = "$FromDate..$LatestDate"
    $env:VIA_NO_OPEN = '1'
    $env:VIA_SELFTEST = '1'

    Write-Host "VIA 根目錄 : $VIA" -ForegroundColor White
    Write-Host "測試範圍   : $FromDate 至 $LatestDate（依目前資料庫最新日）" -ForegroundColor White
    Write-Host "網路模式   : $(if ($EnableNetwork) { '明示開啟' } else { '關閉；只做離線驗收' })" -ForegroundColor White
    Write-Host "報告目錄   : $OutDir" -ForegroundColor White

    $Db = Join-Path $VIA 'functional modules\VDF\output_hub\mega\vdf_tw_market.duckdb'
    $DbJson = Join-Path $OutDir 'VDF_POST2024_DATABASE_CHECK.json'
    Invoke-Step '2024 至最新 DuckDB 只讀核驗' {
        Invoke-VIAPost2024DatabaseCheck -Database $Db -From $FromDate -OutputJson $DbJson
    } | Out-Null

    Invoke-Step 'Git 工作樹快照' {
        git status --short | Select-Object -First 20
        git branch --show-current
        git log --oneline -1
    } | Out-Null

    if ($Pull) {
        Invoke-Step 'Git stash 與 fast-forward 更新' {
            $dirty = @(git status --short)
            if ($dirty.Count -gt 0) {
                git stash push -u -m "B531 2024-latest 測試前工作站快照"
            } else {
                Write-Host '[INFO] 工作樹乾淨，不建立 stash。'
            }
            git pull --ff-only origin $Branch
            git stash list | Select-Object -First 5
            git log --oneline -1
        } | Out-Null
        . ((Get-ChildItem -LiteralPath $VIA -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1).FullName)
    }

    if ($InstallOpenCC) {
        if (-not $EnableNetwork) {
            Write-Host '[BLOCKED] -InstallOpenCC 必須同時明示 -EnableNetwork；本次不代開網路。' -ForegroundColor Yellow
        } else {
            $Py312 = 'C:\Users\tonyk\envs\via_vrn_312\Scripts\python.exe'
            if (Test-Path -LiteralPath $Py312) {
                Invoke-Step '安裝 OpenCC（明示網路）' { & $Py312 -m pip install opencc-python-reimplemented } | Out-Null
            } else {
                Write-Host "[ABSENT] $Py312" -ForegroundColor Yellow
            }
        }
    }

    if ($RebuildOCREnvironment) {
        if (-not $EnableNetwork) {
            Write-Host '[BLOCKED] -RebuildOCREnvironment 必須同時明示 -EnableNetwork；本次不改動環境。' -ForegroundColor Yellow
        } else {
            Invoke-IfCommand 'via-rebuild' { via-rebuild --env via_paddle_311 } | Out-Null
        }
    }

    if ($EnableNetwork) {
        $env:VIA_NET_CONSENT = 'YES'
        $env:VIA_SCRAPE_CONSENT = 'YES'
        Write-Host '[GATE] 已由操作員明示開啟 VIA_NET_CONSENT / VIA_SCRAPE_CONSENT。' -ForegroundColor Yellow
    } else {
        Remove-Item Env:VIA_NET_CONSENT -ErrorAction SilentlyContinue
        Remove-Item Env:VIA_SCRAPE_CONSENT -ErrorAction SilentlyContinue
    }

    Invoke-IfCommand 'via-vetf' { via-vetf } | Out-Null
    Invoke-IfCommand 'via-fplogic' { via-fplogic status } | Out-Null
    Invoke-IfCommand 'via-fplogic' { via-fplogic bench } | Out-Null
    Invoke-IfCommand 'via-fplogic' { via-fplogic enrich } | Out-Null
    Invoke-IfCommand 'via-vrnlogic' { via-vrnlogic reset-backends } | Out-Null
    Invoke-IfCommand 'via-vrnlogic' { via-vrnlogic sync-db } | Out-Null
    Invoke-IfCommand 'via-ryg' { via-ryg vrn -Timeout 300 -NoOpen } | Out-Null

    if ($DaytradeFile) {
        if (Test-Path -LiteralPath $DaytradeFile) {
            Invoke-IfCommand 'via-daytrade' { via-daytrade --from-file $DaytradeFile --date $LatestDate } | Out-Null
        } else {
            Write-Host "[ABSENT] 當沖輸入檔不存在：$DaytradeFile" -ForegroundColor Yellow
        }
    } else {
        Write-Host '[SKIP] via-daytrade：未提供 -DaytradeFile；避免無輸入時誤觸發抓取。' -ForegroundColor DarkYellow
    }

    if ($RunTAOne) {
        Write-Host '[BLOCKED] Legacy TA-One/TA-Lib path is permanently prohibited; use via-quantguard instead.' -ForegroundColor Red
    } else {
        Write-Host '[SKIP] Legacy TA-One/TA-Lib path：VIA 政策永久禁用；QuantGuard 為唯一活動技術分析路徑。' -ForegroundColor DarkYellow
    }

    Invoke-IfCommand 'via-cgfamily' { via-cgfamily status } | Out-Null
    Invoke-IfCommand 'via-census' { via-census -Tables } | Out-Null
    Invoke-IfCommand 'via-ssot' { via-ssot selftest } | Out-Null
    Invoke-IfCommand 'via-functional-acceptance' { via-functional-acceptance run } | Out-Null
    Invoke-IfCommand 'via-vcgc' {
        if ($Publish) { via-vcgc page -Publish } else { via-vcgc page }
    } | Out-Null

    $Status = Join-Path $VIA 'VIA_Reports\acceptance\VIA_FUNCTIONAL_ACCEPTANCE_latest.json'
    $MarketLatest = Join-Path $VIA 'VIA_Reports\vdf\central_lists\MARKET_LISTS_latest.json'
    $SummaryLines = @(
        '# VIA B531 2024→最新功能性測試',
        '',
        "- 測試範圍：$FromDate 至 $LatestDate",
        "- 執行時間：$(Get-Date -Format s)",
        "- 網路模式：$(if ($EnableNetwork) { '明示開啟' } else { '關閉' })",
        "- VIA functional acceptance：$Status",
        "- VDF market list status：$MarketLatest",
        "- 原始完整 console log：$Log",
        '',
        '## 說明',
        '',
        '此腳本把資料驗收範圍固定為 2024-01-01 至目前資料庫最新日期。資料不足時保留 RED/YELLOW/BLOCKED，不把結構測試通過誤當成資料完整。',
        '',
        '## Git',
        '',
        "- 分支：$Branch",
        '- 若使用 -Pull 且工作樹原先有變更，變更會留在 stash，不自動 stash pop。'
    )
    Set-Content -LiteralPath $Summary -Value $SummaryLines -Encoding UTF8
    Write-Host "`n[REPORT] $Summary" -ForegroundColor Green
    if ($OpenReport -and (Test-Path -LiteralPath $Summary)) { Start-Process -FilePath $Summary }
}
finally {
    Stop-Transcript | Out-Null
}
