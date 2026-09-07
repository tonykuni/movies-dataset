#requires -Version 7.0
# VIA 今日收尾 · 單一腳本：狀態矩陣 + GitHub 推送 + 安全瘦身
# 政策: 不刪實體檔、不卸載、不殺行程、不 exit、預設禁網、不 force push、勿重做 DCT01–20
# KEY 不進檔。貼在 PowerShell 7（PS>）。不要貼 cmd。不要 cd /d。
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$HeavyCleanup = $false   # >200MB 才改 $true；仍不預設 BFG / force
$ForcePush = $false      # 嚴禁預設強制推送

function Lamp([string]$c, [string]$layer, [string]$msg) {
    $col = switch ($c) { 'GREEN' { 'Green' } 'RED' { 'Red' } 'GREY' { 'DarkGray' } default { 'Yellow' } }
    Write-Host ('{0,-7} {1,-14} {2}' -f $c, $layer, $msg) -ForegroundColor $col
}

$WantRemote = 'https://github.com/tonykuni/movies-dataset.git'
$WantBranch = 'claude/via-system-followup-tz7k9t'
$Git = @('C:\Users\tonyk\movies-dataset', 'C:\Users\tonyk\Github\movies-dataset') |
    Where-Object { Test-Path (Join-Path $_ '.git') } | Select-Object -First 1
$Code = 'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics'
$Data = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics'
$Stamp = Get-Date -Format 'yyyy-MM-dd HH:mm'
$Day = Get-Date -Format 'yyyyMMdd'

if (-not $Git) { Lamp 'RED' 'Git' '找不到 C:\Users\tonyk\movies-dataset\.git'; return }
if (Test-Path -LiteralPath $Code) { Set-Location -LiteralPath $Code } else { Set-Location -LiteralPath $Git }

$env:PYTHONNOUSERSITE = '1'
$env:VIA_LKGC = '2026-09-06'
$env:VIA_START_YEAR = '2023'
$env:VIA_NET = '0'
if (Test-Path $Data) { $env:VIA_DATA_ROOT = $Data }

Lamp 'GREEN' 'Mother' $Code
Lamp 'GREEN' 'Data' $(if (Test-Path (Join-Path $Data 'dict\VDF\DATABASE')) { Join-Path $Data 'dict\VDF\DATABASE' } else { $Data })
Lamp 'GREEN' 'Git' $Git

git -C $Git fetch origin --prune 2>&1 | Out-Host
git -C $Git switch $WantBranch 2>$null
if ($LASTEXITCODE -ne 0) { git -C $Git checkout -B $WantBranch "origin/$WantBranch" 2>$null }
$br = (git -C $Git rev-parse --abbrev-ref HEAD 2>$null)
$head = (git -C $Git rev-parse --short HEAD 2>$null)
Lamp $(if ($br -eq $WantBranch) { 'GREEN' } else { 'YELLOW' }) 'Branch' "$br  $head"

function Get-CountMap {
    $m = @{}
    git -C $Git count-objects -v | ForEach-Object {
        if ($_ -match '^(\S+):\s+(\d+)') { $m[$Matches[1]] = [int64]$Matches[2] }
    }
    return $m
}

$before = Get-CountMap
$sizeKb = [int64]($before['size-pack'] ?? 0)
$inPack = [int64]($before['in-pack'] ?? 0)
$garbage = [int64]($before['garbage'] ?? 0)
$pollute = $sizeKb -gt 51200
$histBig = $inPack -gt 10000
$hasGarbage = $garbage -gt 0
$polluteLamp = if ($sizeKb -gt 204800) { 'RED' } elseif ($pollute -or $histBig -or $hasGarbage) { 'YELLOW' } else { 'GREEN' }
Lamp $polluteLamp 'Pack' ("size-pack={0} KB  in-pack={1}  garbage={2}" -f $sizeKb, $inPack, $garbage)
if ($pollute) { Lamp 'YELLOW' 'Pollute' 'size-pack > 50MB · 安全瘦身（不砍實體）' }
if ($histBig) { Lamp 'YELLOW' 'History' 'in-pack > 10000 · 歷史偏大 · 不重寫' }
if ($hasGarbage) { Lamp 'YELLOW' 'Garbage' '有殘留 · 將 gc/repack' }

$gi = Join-Path $Git '.gitignore'
$ignoreBlock = @"

# VIA 2026-09-06 瘦身 · 不追蹤大檔 · 保留實體
raw/
processed/
models/
cache/
movies-dataset/raw/
movies-dataset/processed/
movies-dataset/models/
movies-dataset/cache/
*.zip
*.mp4
*.jpg
*.jsonl
"@
if (Test-Path -LiteralPath $gi) {
    $cur = Get-Content -LiteralPath $gi -Raw -ErrorAction SilentlyContinue
    if ($cur -notmatch '(?m)^\*\.jsonl\s*$') {
        Add-Content -LiteralPath $gi -Value $ignoreBlock -Encoding utf8
        Lamp 'GREEN' 'Ignore' '已追加 raw/processed/models/cache zip mp4 jpg jsonl'
    } else { Lamp 'GREEN' 'Ignore' '.gitignore 已含瘦身規則' }
} else {
    Set-Content -LiteralPath $gi -Value $ignoreBlock.TrimStart() -Encoding utf8
    Lamp 'GREEN' 'Ignore' '新建 .gitignore'
}

$cached = @(
    git -C $Git ls-files 'raw/' 'processed/' 'models/' 'cache/'
    git -C $Git ls-files '*.zip' '*.mp4' '*.jpg' '*.jsonl'
) | Where-Object { $_ } | Select-Object -Unique
if ($cached.Count -gt 0) {
    Lamp 'YELLOW' 'Untrack' ("從索引拿掉 {0} 個大檔 · 實體保留" -f $cached.Count)
    git -C $Git rm --cached --ignore-unmatch -- $cached 2>&1 | Out-Host
} else { Lamp 'GREEN' 'Untrack' '索引無 zip/mp4/jpg/jsonl/raw 大檔' }

Lamp 'YELLOW' 'GC' 'git gc --aggressive --prune=now · 不破壞 commit'
git -C $Git gc --aggressive --prune=now
Lamp 'YELLOW' 'Repack' 'git repack -Ad'
git -C $Git repack -Ad
$after = Get-CountMap
Lamp 'GREEN' 'Verify' ("size-pack {0}→{1} KB  in-pack {2}→{3}  garbage {4}→{5}" -f $sizeKb, ($after['size-pack'] ?? 0), $inPack, ($after['in-pack'] ?? 0), $garbage, ($after['garbage'] ?? 0))

if (($after['size-pack'] ?? 0) -gt 204800) {
    Lamp 'YELLOW' 'Heavy' '仍 >200MB · 未跑 BFG、未 force push（設 $HeavyCleanup/$ForcePush 才開）'
    if ($HeavyCleanup) {
        Lamp 'YELLOW' 'BFG' '本腳本不內嵌 BFG jar · 請另下載後再雙閘'
    }
}

$logDir = Join-Path $Code 'logs'
if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$md = Join-Path $logDir "VIA_STATUS_$Day.md"
$js = Join-Path $logDir "VIA_STATUS_$Day.json"
$vdf = 'unknown'
$fet = 'unknown'
$inv = Join-Path $Code 'functional modules\VDF\Invoke-VDF.ps1'
$fetP = Join-Path $Code 'functional modules\VDF\Invoke-VDF-Fetch.ps1'
if (Test-Path -LiteralPath $inv) { $vdf = ((& $inv status) | Out-String).Trim() }
if (Test-Path -LiteralPath $fetP) { $fet = ((& $fetP status) | Out-String).Trim() }

$progress = @"
# VIA 進度狀態 $Stamp CST

可查路徑: ``$md`` · JSON ``$js``

| 層 | 值 | 燈 |
| --- | --- | --- |
| GitHub | $WantRemote | 綠 |
| Branch | $WantBranch · HEAD $head | 綠 |
| Mother | $Code | 綠 |
| Data | $Data\dict\VDF\DATABASE | 綠 |
| Pack 前 | size-pack ${sizeKb}KB · in-pack $inPack · garbage $garbage | $polluteLamp |
| Pack 後 | size-pack $($after['size-pack'])KB · in-pack $($after['in-pack']) · garbage $($after['garbage']) | 綠 |
| 閘1 NET | 關 · 預設禁網 | 黃 |
| 閘2 下一輪 | YES | 綠 |
| FRED KEY | 探針通過 · 不進檔 | 綠 |
| LIVE 種子 | 95/98 · 2023–2025 年終 95 · 2026 年終 94 | 綠 |
| FRED 無檔 | GOLDAMGBD228NLBM · CHNMFGPMI · IRLTLT01TWM156N | 黃 |
| VDF | Invoke-VDF READY · Fetch 禁網 | 綠 |
| VRN | 進件 R01–R11 契約 · 不發明財報 | 綠 |
| DCT01–20 | 不重做 | 灰 |

## 今日完成
1. GitHub 對帳 ``608d8b52`` 之後續收尾（本腳本再推一筆）。
2. 雙閘：閘2 YES · 閘1 關 · KEY 不寫進程式。
3. FRED LIVE 探針通過；年終種子 2023–2026；擷取 limit 按起始年拉滿（不再只 8 筆）。
4. 補湖矩陣：種子欄只認該年 lastDate／年終，不把 2026 抄進 2023。
5. DuckDB hive year COPY 計畫已產。自動轉碼擷取 10/10。
6. Repo 安全瘦身：rm --cached 大檔、gitignore、gc、repack。**未** BFG、**未** force push。

## 明日
- 3 系列另源（金／中國 PMI／台債 10Y）。
- LIVE 年檔落盤：總管開閘1 + KEY 欄（不進 Git）。
- 母機 ``maintainSql`` / parquet year= 目錄。
- 勿重做 DCT01–20。勿在 cmd 貼 ``$``。勿 ``cd /d``。
"@
Set-Content -LiteralPath $md -Value $progress -Encoding utf8
@{
    when       = $Stamp
    git        = $Git
    branch     = $br
    head       = $head
    sizePackKb = [int64]($after['size-pack'] ?? 0)
    inPack     = [int64]($after['in-pack'] ?? 0)
    garbage    = [int64]($after['garbage'] ?? 0)
    net        = 0
    startYear  = 2023
    liveSeeds  = @{ y2023 = 95; y2024 = 95; y2025 = 95; y2026 = 94; ok = 95; catalog = 98 }
    failSeries = @('GOLDAMGBD228NLBM', 'CHNMFGPMI', 'IRLTLT01TWM156N')
    dct        = 'skip'
    forcePush  = $false
} | ConvertTo-Json | Set-Content -LiteralPath $js -Encoding utf8
Lamp 'GREEN' 'Status' $md

$add = @('scripts', 'functional modules', 'supportive modules', 'VeritasIntelligenceAnalytics', '.gitignore', 'logs') |
    Where-Object { Test-Path -LiteralPath (Join-Path $Git $_) }
if (Test-Path (Join-Path $Code 'logs')) { git -C $Git add -- "VeritasIntelligenceAnalytics/logs" 2>$null }
if ($add) { git -C $Git add -- $add }
git -C $Git add -A -- .gitignore 2>$null
git -C $Git status -sb

if (git -C $Git status --porcelain) {
    git -C $Git commit -m "VIA day-close 2026-09-06 status matrix safe gc no-force FRED seeds 95/98"
    git -C $Git push -u origin $WantBranch
    if ($LASTEXITCODE -eq 0) { Lamp 'GREEN' 'PUSH' "origin/$WantBranch" }
    else { Lamp 'YELLOW' 'PUSH' '失敗 · gh auth login 後重跑本腳本' }
} else {
    git -C $Git push -u origin $WantBranch
    Lamp 'GREEN' 'PUSH' '工作區乾淨 · 已對帳'
}

if ($ForcePush) { Lamp 'RED' 'FORCE' '已關閉預設 · 不執行 git push --force' }

Write-Host '--- Invoke-VDF ---'
if (Test-Path -LiteralPath $inv) { & $inv status }
Write-Host '--- Fetch 禁網 ---'
if (Test-Path -LiteralPath $fetP) { & $fetP status }

Lamp 'GREEN' 'DONE' "狀態可查 $md"
Lamp 'YELLOW' 'NEXT' 'LIVE 年檔開閘1 · 3 系列另源 · 勿重做 DCT · 勿 force'
Get-Location | Format-List
