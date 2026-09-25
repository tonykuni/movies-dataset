# VIA 短指令矩陣 · 貼在已進入專案的 PS>（PowerShell 7）
# 右側小板 · 上方鎖定 · 中文說明 · 不擋左邊 PS · 不刪 · 禁網
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Lamp([string]$c, [string]$layer, [string]$msg) {
    $col = switch ($c) { 'GREEN' { 'Green' } 'RED' { 'Red' } 'GREY' { 'DarkGray' } default { 'Yellow' } }
    Write-Host ('{0,-7} {1,-12} {2}' -f $c, $layer, $msg) -ForegroundColor $col
}

function global:via-enter {
    $roots = @(
        'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics',
        'C:\Users\tonyk\Github\movies-dataset\VeritasIntelligenceAnalytics',
        'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics',
        'C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics',
        'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics'
    )
    $root = $roots | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $root) { Lamp 'RED' 'ENTER' '找不到母系統'; return $false }
    Set-Location -LiteralPath $root
    $env:PYTHONNOUSERSITE = '1'
    $env:VIA_LKGC = '2026-09-06'
    $env:VIA_START_YEAR = '2023'
    $env:VIA_NET = '0'
    $env:VIA_ROOT = $root
    $vdfHome = @(
        "$env:USERPROFILE\miniconda3\envs\via_vdf",
        "$env:USERPROFILE\anaconda3\envs\via_vdf",
        "$env:USERPROFILE\Miniconda3\envs\via_vdf",
        'C:\Users\tonyk\miniconda3\envs\via_vdf',
        'C:\Users\tonyk\anaconda3\envs\via_vdf'
    ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if ($vdfHome) {
        $env:CONDA_PREFIX = $vdfHome
        $env:CONDA_DEFAULT_ENV = 'via_vdf'
        $env:PATH = "$vdfHome;$vdfHome\Scripts;$vdfHome\Library\bin;" + $env:PATH
        Lamp 'GREEN' 'ENV' "via_vdf  $vdfHome"
    }
    else { Lamp 'YELLOW' 'ENV' 'via_vdf 未見 · 不 conda create' }
    Lamp 'GREEN' 'ENTER' $root
    return $true
}

function global:via-path {
    if (-not (via-enter)) { return }
    $venv = Join-Path (Get-Location) '.venv-via_vdf\Scripts'
    if (Test-Path -LiteralPath (Join-Path $venv 'python.exe')) {
        $env:PATH = "$venv;" + $env:PATH
        $env:VIA_VDF_PY = Join-Path $venv 'python.exe'
        Lamp 'GREEN' 'PATH' "venv prepend $venv"
    }
    else { Lamp 'YELLOW' 'PATH' '.venv-via_vdf 未見 · 不新建 conda' }
    Lamp 'GREEN' 'PATH' 'via_iso_* 不進 PATH · ISO99'
}

function global:via-env {
    via-path
    $py = Join-Path (Get-Location) 'public\via\VIA_EnvManager.py'
    if ((Test-Path -LiteralPath $py) -and $env:VIA_VDF_PY) {
        & $env:VIA_VDF_PY $py 2>&1 | ForEach-Object { Lamp 'GREY' 'ENV' "$_" }
    }
    else { Lamp 'YELLOW' 'ENV' 'EnvManager 計畫 · numpy → via_iso_numpy · 不刪' }
    Lamp 'GREEN' 'ENV' '中央入口 · 衝突隔離後才裝庫'
}

function global:via-entry {
    via-env
    Lamp 'GREEN' 'ENTRY' '唯一入口完成 · GitHub 用 via-gh'
}

function global:via-gh {
    if (-not (via-enter)) { return }
    $root = Get-Location
    if (-not (Test-Path -LiteralPath (Join-Path $root '.git'))) { Lamp 'RED' 'GH' '不是 git 倉'; return }
    git status -sb
    $prefer = @('src', 'public/via', 'public', 'scripts', 'locks', 'package.json', 'package-lock.json', 'AGENTS.md', 'VIA-ALL.cmd')
    [string[]]$add = @($prefer | Where-Object { Test-Path -LiteralPath (Join-Path $root $_) })
    if ($env:VIA_GH_HTML -eq '1' -and (Test-Path -LiteralPath (Join-Path $root 'logs\via_aetf_board.html'))) {
        $add += 'logs/via_aetf_board.html'
    }
    if ($add -isnot [System.Array]) { $add = @($add) }
    Lamp 'GREEN' 'ADD' $(if ($add.Count) { $add -join ' ' } else { '無標準路徑（母倉可無 src）' })
    if ($env:VIA_GH_YES -ne '1') {
        Lamp 'YELLOW' 'GH' '預覽 · 設 VIA_GH_YES=1 才 add/commit/push · 禁止強制推送'
        return
    }
    if (-not $add.Count) { Lamp 'YELLOW' 'GH' '此倉無標準路徑 · 不 add'; return }
    foreach ($p in $add) { git add -- $p }
    git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) { Lamp 'YELLOW' 'GH' '無暫存'; return }
    $msg = $env:VIA_GH_MSG
    if (-not $msg) { $msg = 'VIA central entry · EnvManager PATH isolate-not-delete' }
    git commit -m $msg
    git push -u origin HEAD
    Lamp 'GREEN' 'GH' 'push 完成 · 禁止強制推送'
}

function global:via-hand {
    Lamp 'YELLOW' 'HAND' '2026-09-08 foreach git add -- $p · VIA-ALL.cmd 未暫存 · iso 不進 PATH · LIVE 關'
}

function global:via-aea {
    Lamp 'GREEN' 'AEA' 'BOARD 29 · 00981A 2880億 +3.52% · 流0無Δ單位 · COPY_ONLY · LIVE 關'
}

function global:via-rev {
    Lamp 'GREEN' 'U' 'VIA_U＝VDF_ENG075 月營收 · 2023-01→ · MOPS sii/otc 月檔 · CACHE · LIVE 關 · 季報另表'
}

function global:via-handle {
    $hit = @(
        (Join-Path (Get-Location) 'public\via\VIA-Handle-All.ps1'),
        (Join-Path (Get-Location) 'scripts\VIA-Handle-All.ps1')
    ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if ($hit) { & $hit } else { Lamp 'YELLOW' 'HANDLE' '未見 VIA-Handle-All.ps1 · 仍可用 via-entry / via-rev / via-gh' }
}

function New-ViaDir([string]$p) {
    if ($p -and -not (Test-Path -LiteralPath $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null }
}

function Find-ViaPython {
    $hits = [System.Collections.Generic.List[string]]::new()
    foreach ($root in @(
            "$env:USERPROFILE\miniconda3\envs",
            "$env:USERPROFILE\Miniconda3\envs",
            "$env:USERPROFILE\anaconda3\envs",
            "$env:USERPROFILE\Anaconda3\envs",
            'C:\Users\tonyk\miniconda3\envs',
            'C:\Users\tonyk\Miniconda3\envs',
            'C:\Users\tonyk\anaconda3\envs',
            'C:\ProgramData\miniconda3\envs',
            'C:\ProgramData\anaconda3\envs'
        )) {
        if (-not (Test-Path -LiteralPath $root)) { continue }
        Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            $py = Join-Path $_.FullName 'python.exe'
            if (Test-Path -LiteralPath $py) { $hits.Add($py) }
        }
    }
    foreach ($one in @(
            "$env:CONDA_PREFIX\python.exe",
            "$env:USERPROFILE\miniconda3\python.exe",
            (Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source)
        )) {
        if ($one -and (Test-Path -LiteralPath $one) -and -not $hits.Contains($one)) { $hits.Add($one) }
    }
    return @($hits)
}

function global:via-probe {
    $SrcRoot = 'C:\新增資料夾\新增資料夾'
    $Parts = @(
        @{ Id = 'PX'; Folder = 'VIA_db_part1_prices' }
        @{ Id = 'CHIP'; Folder = 'VIA_db_part2_chips' }
        @{ Id = 'REST'; Folder = 'VIA_db_part3_rest' }
    )
    $extOf = { param($files, $pat) @($files | Where-Object { $_.Extension -match $pat }).Count }
    Write-Host ('{0,-6} {1,-6} {2,-8} {3,-8} {4,-6} {5,-6} {6,-6} {7}' -f '燈', '庫', '檔數', 'parquet', 'csv', 'db', 'xlsx', '樣本／偵測年') -ForegroundColor Cyan
    $out = @()
    foreach ($p in $Parts) {
        $src = Join-Path $SrcRoot $p.Folder
        if (-not (Test-Path -LiteralPath $src)) {
            Lamp 'RED' $p.Id "缺 $src"
            continue
        }
        $files = @(Get-ChildItem -LiteralPath $src -Recurse -File -ErrorAction SilentlyContinue)
        $pq = @($files | Where-Object { $_.Extension -match '^\.(parquet|pq)$' })
        $csv = @($files | Where-Object { $_.Extension -match '^\.(csv|tsv|txt)$' })
        $db = @($files | Where-Object { $_.Extension -match '^\.(duckdb|db|sqlite|sqlite3)$' })
        $xls = @($files | Where-Object { $_.Extension -match '^\.(xlsx|xls)$' })
        $years = [System.Collections.Generic.HashSet[string]]::new()
        foreach ($f in $files) {
            [regex]::Matches($f.FullName, '20(2[3-9]|3[0-9])') | ForEach-Object { [void]$years.Add($_.Value) }
            if ($f.DirectoryName -match 'year=(\d{4})') { [void]$years.Add($Matches[1]) }
        }
        $sample = ($files | Select-Object -First 3 | ForEach-Object { $_.Name }) -join ' · '
        $lamp = if ($files.Count -eq 0) { 'YELLOW' } elseif ($pq.Count -gt 0 -or $csv.Count -gt 0 -or $db.Count -gt 0) { 'GREEN' } else { 'YELLOW' }
        $ystr = if ($years.Count) { ($years | Sort-Object) -join ',' } else { '路徑無年' }
        Lamp $lamp $p.Id ("檔{0} pq{1} csv{2} db{3} xls{4} 年[{5}] {6}" -f $files.Count, $pq.Count, $csv.Count, $db.Count, $xls.Count, $ystr, $sample)
        $out += [pscustomobject]@{ Id = $p.Id; Path = $src; Files = $files.Count; Parquet = $pq.Count; Csv = $csv.Count; Db = $db.Count; Xls = $xls.Count; Years = $ystr }
    }
    $pys = Find-ViaPython
    if ($pys.Count) { Lamp 'GREEN' 'PY' ($pys -join ' | ') } else { Lamp 'YELLOW' 'PY' '無 python.exe · 只能檔案複製' }
    return $out
}

function global:via-ingest {
    via-enter | Out-Null
    $StartYear = 2023
    $EndYear = [int](Get-Date).Year
    $SrcRoot = 'C:\新增資料夾\新增資料夾'
    $GitLake = 'C:\Users\tonyk\Github\movies-dataset\data\vdf'
    $GitAlt = 'C:\Users\tonyk\movies-dataset\data\vdf'
    $Mother = 'C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics\data\vdf'
    $LakeRoot = @($GitLake, $GitAlt, $Mother) | Where-Object {
        $probe = Split-Path (Split-Path $_ -Parent) -Parent
        Test-Path -LiteralPath $probe
    } | Select-Object -First 1
    if (-not $LakeRoot) { $LakeRoot = $GitLake }
    New-ViaDir $LakeRoot
    Lamp 'GREEN' 'POLICY' "COPY_ONLY · 不刪原件 · $StartYear → $EndYear · 網 $($env:VIA_NET)"
    Lamp 'GREEN' 'PROBE' '先盤三庫檔種（無 year= 也能切）'
    [void](via-probe)

    $py = $null
    foreach ($c in (Find-ViaPython)) {
        $chk = & $c -c "import duckdb; print('DUCK')" 2>$null
        if ($LASTEXITCODE -eq 0 -and "$chk" -match 'DUCK') { $py = $c; break }
    }
    if ($py) { Lamp 'GREEN' 'DUCK' $py } else { Lamp 'YELLOW' 'DUCK' '無 duckdb · 有 parquet/csv 仍會整檔複製到 year=_raw' }

    $helper = Join-Path $env:TEMP 'via_ingest_split.py'
    @'
import glob, os, sys
src, dest_root, y0s, y1s = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
y0, y1 = int(y0s), int(y1s)
import duckdb
con = duckdb.connect()
files = sorted(glob.glob(os.path.join(src, "**", "*.parquet"), recursive=True))
if not files:
    sys.stderr.write("NO_FILES\n"); sys.exit(2)
DATE_CAND = ("date", "obs_date", "trade_date", "as_of", "datetime", "dt", "tradedate", "asof")
ok = 0
for i, f in enumerate(files):
    fu = f.replace("\\", "/")
    base = os.path.basename(f)
    try:
        cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{fu}')").fetchall()]
    except Exception as e:
        print(f"FAIL {base} DESCRIBE {e}"); continue
    lower = {c.lower(): c for c in cols}
    dcol = next((lower[n] for n in DATE_CAND if n in lower), None)
    if not dcol:
        print(f"NODATE {base} cols={cols[:10]}")
        continue
    for y in range(y1, y0 - 1, -1):
        dest = os.path.join(dest_root, f"year={y}", f"part-{i:03d}.parquet")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        dest_u = dest.replace("\\", "/")
        where = f'YEAR(TRY_CAST("{dcol}" AS DATE)) = {y}'
        try:
            n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{fu}') WHERE {where}").fetchone()[0]
            if not n:
                print(f"EMPTY {base} {y}")
                continue
            con.execute(
                f"COPY (SELECT * FROM read_parquet('{fu}') WHERE {where}) TO '{dest_u}' "
                f"(FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 65536, OVERWRITE_OR_IGNORE)"
            )
            sz = os.path.getsize(dest) if os.path.isfile(dest) else 0
            print(f"OK {base} {y} rows={n} bytes={sz}")
            ok += 1
        except Exception as e:
            print(f"FAIL {base} {y} {e}")
if ok == 0:
    sys.exit(3)
'@ | Set-Content -LiteralPath $helper -Encoding utf8

    $Parts = @(
        @{ Id = 'PX'; Lake = 'px'; Folder = 'VIA_db_part1_prices' }
        @{ Id = 'CHIP'; Lake = 'chip'; Folder = 'VIA_db_part2_chips' }
        @{ Id = 'REST'; Lake = 'rest'; Folder = 'VIA_db_part3_rest' }
    )
    $Years = @(); for ($y = $EndYear; $y -ge $StartYear; $y--) { $Years += $y }
    $copyN = 0; $skipN = 0; $rawN = 0
    foreach ($p in $Parts) {
        $src = Join-Path $SrcRoot $p.Folder
        $srcOk = Test-Path -LiteralPath $src
        $lakeBase = Join-Path $LakeRoot $p.Lake
        New-ViaDir $lakeBase
        if (-not $srcOk) { Lamp 'RED' $p.Id "缺 $($p.Folder)"; continue }
        $didDuck = $false
        if ($py) {
            $out = & $py $helper $src $lakeBase "$StartYear" "$EndYear" 2>&1
            $out | ForEach-Object {
                $line = "$_"
                $c = if ($line -match '^OK') { 'GREEN' } elseif ($line -match '^EMPTY') { 'GREY' } else { 'YELLOW' }
                Lamp $c "$($p.Id)-DUCK" $line
            }
            if ($LASTEXITCODE -eq 0) { $didDuck = $true }
        }
        foreach ($year in $Years) {
            $lakeDir = Join-Path $lakeBase "year=$year"
            New-ViaDir $lakeDir
            $have = @(Get-ChildItem -LiteralPath $lakeDir -Filter 'part-*.parquet' -File -ErrorAction SilentlyContinue)
            if ($have.Count -gt 0) {
                $skipN++; Lamp 'GREEN' "$($p.Id)-$year" "年檔 $($have.Count) · $(if ($didDuck) {'DuckDB'} else {'已在湖'})"
                if (Test-Path -LiteralPath $Mother) {
                    $relDir = Join-Path $Mother (Join-Path $p.Lake "year=$year")
                    New-ViaDir $relDir
                    Copy-Item -Path (Join-Path $lakeDir 'part-*.parquet') -Destination $relDir -Force -ErrorAction SilentlyContinue
                }
                continue
            }
            $n = 0
            $hive = @(Get-ChildItem -LiteralPath $src -Recurse -Directory -Filter "year=$year" -ErrorAction SilentlyContinue)
            foreach ($d in $hive) {
                foreach ($f in @(Get-ChildItem -LiteralPath $d.FullName -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match '^\.(parquet|pq|csv)$' })) {
                    Copy-Item -LiteralPath $f.FullName -Destination (Join-Path $lakeDir $f.Name) -Force
                    $n++
                }
            }
            if ($n -eq 0) {
                $files = @(Get-ChildItem -LiteralPath $src -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match '^\.(parquet|pq|csv)$' -and ($_.Name -match "$year" -or $_.DirectoryName -match "$year") })
                $i = 0
                foreach ($f in $files) {
                    $destName = if ($f.Extension -match 'parquet') { 'part-{0:000}.parquet' -f $i } else { 'part-{0:000}{1}' -f $i, $f.Extension }
                    Copy-Item -LiteralPath $f.FullName -Destination (Join-Path $lakeDir $destName) -Force
                    $n++; $i++
                }
            }
            if ($n -gt 0) { $copyN++; Lamp 'GREEN' "$($p.Id)-$year" "COPY $n · 不刪原件" }
            else { Lamp 'YELLOW' "$($p.Id)-$year" '該年切不出 · 看 PROBE' }
        }
        if (-not $didDuck) {
            $raw = @(Get-ChildItem -LiteralPath $src -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match '^\.(parquet|pq|csv|duckdb|db)$' })
            if ($raw.Count -gt 0) {
                $rawDir = Join-Path $lakeBase 'year=_raw'
                New-ViaDir $rawDir
                $i = 0
                foreach ($f in $raw) {
                    Copy-Item -LiteralPath $f.FullName -Destination (Join-Path $rawDir ('src-{0:000}{1}' -f $i, $f.Extension)) -Force
                    $i++
                }
                $rawN += $raw.Count
                Lamp 'YELLOW' "$($p.Id)-raw" "原件 $i 個 COPY 到 year=_raw · 不刪源 · 待 DuckDB 切年"
            }
        }
    }
    Lamp 'GREEN' 'AK' 'akshare_call SKIP'
    Lamp 'GREEN' 'SUM' "COPY年 $copyN · 已有年 $skipN · raw $rawN · 原件未動"
}

function Get-VIAZh {
    @{
        'via-enter'          = '進入母目錄並釘 via_vdf，禁網'
        'via-path'           = '釘 PATH：venv 優先，iso 不進'
        'via-env'            = 'EnvManager 衝突快檢，不刪'
        'via-entry'          = '中央唯一入口：隔離→裝庫→PATH'
        'via-gh'             = 'GitHub 預覽；foreach add；VIA_GH_YES=1 才 push'
        'via-aea'            = '主動 ETF 29 檔看板，LIVE 關'
        'via-rev'            = '台股月營收 U＝ENG075，LIVE 關'
        'via-hand'           = '隔日接手全景（2026-09-08）'
        'via-handle'         = '一貼：PATH＋log＋AEA＋U＋Git'
        'via-ingest'         = '2023→今年 COPY 三庫，原件不刪'
        'via-matrix'         = '重開右側短指令板'
        'via-status'         = '系統狀態盤點'
        'via-health'         = '健康檢查'
        'via-help'           = '短指令說明'
        'via-rootcheck'      = '根目錄／路徑探針'
        'via-fred'           = 'FRED 宏觀（LIVE 另閘）'
        'via-vdfarch'        = 'VDF 湖架構'
        'via-ssot'           = 'SSOT 對齊，別名退下'
        'via-accel'          = 'PS20 加速器'
        'via-accel-check'    = '加速器對帳'
        'via-ui'             = 'UI 總管'
        'via-pipeline'       = '流程管線'
        'via-system'         = '系統總覽'
        'via-selftest'       = '自測'
        'selftest'           = '自測（別名）'
        'via-intake'         = '研報進件'
        'via-intake-roster'  = '進件名冊'
        'via-manager'        = '管理器'
        'via-register'       = '註冊短指令'
        'via-all'            = '全開（重，不自動跑）'
        'via-fixall'         = '全修（重，不自動跑）'
        'via-datahome'       = '資料盤根'
        'via-complete'       = '完工序'
        'via-loop'           = '測試迴圈'
        'via-six'            = '六程'
        'via-charter'        = '憲章／契約'
        'via-api'            = 'API 閘'
        'via-master'         = '主控'
        'via-netbench'       = '網路基準（預設禁網）'
        'via-mobile'         = '行動版'
        'via-superhtml'      = 'HTML 報告'
        'via-bridge-sweep'   = '橋接掃描'
        'via-repo-optimize'  = '倉優化'
        'via-rotation'       = '輪替'
        'via-vapstack'       = 'VAP 堆疊'
        'via-reload'         = '重載短指令'
        'via-plotlaw'        = '繪圖規則'
        'via-tpn'            = 'TPN'
        'via-psrepair'       = 'PS 修復'
        'via-prompt'         = '提示／規範'
        'via-analysis'       = '分析'
        'via-md'             = 'Markdown'
        'via-tower-reset'    = '塔重置'
        'regen-all'          = '全重生（重，不自動跑）'
        'via'                = 'VIA 入口'
    }
}

function Get-VIAShortCommands {
    $zh = Get-VIAZh
    $pin = @('via-enter', 'via-ingest', 'via-matrix')
    $known = @($zh.Keys) + @(Get-Command -Name 'via-*', 'regen-all', 'selftest' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name)
    $rows = @()
    foreach ($n in ($known | Select-Object -Unique | Sort-Object)) {
        $cmd = Get-Command -Name $n -ErrorAction SilentlyContinue | Select-Object -First 1
        $ok = [bool]$cmd
        $kind = switch ("$($cmd.CommandType)") {
            'Function' { '函式' }
            'Alias' { '別名' }
            'Cmdlet' { '指令' }
            'ExternalScript' { '腳本' }
            default { if ($ok) { '已載' } else { '未載' } }
        }
        $note = $zh[$n]
        if (-not $note) { $note = $(if ($ok) { '已註冊短指令' } else { '本視窗未載入' }) }
        $lamp = if (-not $ok) { '灰' } elseif ($pin -contains $n) { '綠' } else { '綠' }
        if (-not $ok) { $lamp = '灰' }
        $rows += [pscustomobject]@{ Lamp = $lamp; Name = $n; Kind = $kind; Note = $note }
    }
    return $rows
}

function global:via-matrix {
    $rows = @(Get-VIAShortCommands)
    $parent = [runspace]::DefaultRunspace
    if (-not (Get-EventSubscriber -SourceIdentifier 'VIA.UI' -ErrorAction SilentlyContinue)) {
        Register-EngineEvent -SourceIdentifier 'VIA.UI' -Action {
            $n = $Event.SourceArgs[0]
            if ($n -and (Get-Command -Name $n -ErrorAction SilentlyContinue)) {
                Write-Host ("GREEN   RUN          {0}" -f $n) -ForegroundColor Green
                & $n
            }
            else {
                Write-Host ("YELLOW  MISS         {0}" -f $n) -ForegroundColor Yellow
            }
        } | Out-Null
    }
    $rs = [runspacefactory]::CreateRunspace()
    $rs.ApartmentState = 'STA'
    $rs.ThreadOptions = 'ReuseThread'
    $rs.Open()
    $rs.SessionStateProxy.SetVariable('ViaRows', $rows)
    $rs.SessionStateProxy.SetVariable('ParentRS', $parent)
    $ps = [powershell]::Create()
    $ps.Runspace = $rs
    [void]$ps.AddScript({
            Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase
            $xaml = @'
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Title="VIA 短指令 · 右側板"
        Background="#0E1116" Foreground="#D7DDE8"
        FontFamily="Segoe UI" FontSize="12"
        Width="448" MinWidth="400" MaxWidth="520"
        ResizeMode="CanResizeWithGrip" Topmost="True" ShowInTaskbar="True">
  <DockPanel>
    <Border DockPanel.Dock="Top" Background="#12161C" BorderBrush="#242A36" BorderThickness="0,0,0,1" Padding="10,8">
      <StackPanel>
        <TextBlock Text="短指令鎖定 · 右側板 · 左邊 PS 不擋" FontSize="11" Foreground="#8B93A7" Margin="0,0,0,8"/>
        <WrapPanel x:Name="CmdBar" Orientation="Horizontal"/>
      </StackPanel>
    </Border>
    <TextBlock x:Name="Hint" DockPanel.Dock="Bottom" Margin="10,6" FontSize="11" Foreground="#8B93A7"
               Text="點上方執行（事件回左邊 PS）· 欄位為中文說明"/>
    <DataGrid x:Name="Grid" AutoGenerateColumns="False" IsReadOnly="True"
              HeadersVisibility="Column" GridLinesVisibility="Horizontal"
              RowHeaderWidth="0" BorderThickness="0" Background="#0E1116"
              Foreground="#D7DDE8" RowBackground="#0E1116" AlternatingRowBackground="#12161C"
              HorizontalGridLinesBrush="#242A36" CanUserResizeColumns="True"
              CanUserSortColumns="True" SelectionMode="Single" RowHeight="24"
              FontSize="12">
      <DataGrid.ColumnHeaderStyle>
        <Style TargetType="DataGridColumnHeader">
          <Setter Property="Background" Value="#161B22"/>
          <Setter Property="Foreground" Value="#8B93A7"/>
          <Setter Property="BorderBrush" Value="#242A36"/>
          <Setter Property="FontSize" Value="11"/>
          <Setter Property="Padding" Value="8,4"/>
          <Setter Property="Height" Value="28"/>
        </Style>
      </DataGrid.ColumnHeaderStyle>
      <DataGrid.Columns>
        <DataGridTextColumn Header="燈" Binding="{Binding Lamp}" Width="36"/>
        <DataGridTextColumn Header="指令" Binding="{Binding Name}" Width="128"/>
        <DataGridTextColumn Header="類型" Binding="{Binding Kind}" Width="48"/>
        <DataGridTextColumn Header="說明" Binding="{Binding Note}" Width="*"/>
      </DataGrid.Columns>
    </DataGrid>
  </DockPanel>
</Window>
'@
            $win = [Windows.Markup.XamlReader]::Parse($xaml)
            $bar = $win.FindName('CmdBar')
            $grid = $win.FindName('Grid')
            $hint = $win.FindName('Hint')
            $grid.ItemsSource = $ViaRows
            $wa = [System.Windows.SystemParameters]::WorkArea
            $win.Height = [math]::Max(420, [math]::Floor($wa.Height * 0.72))
            $win.Left = $wa.Right - $win.Width - 10
            $win.Top = $wa.Top + 32
            $pinned = @(
                @{ n = 'via-enter'; z = '進專案' },
                @{ n = 'via-entry'; z = '唯一入口' },
                @{ n = 'via-env'; z = '環境' },
                @{ n = 'via-path'; z = 'PATH' },
                @{ n = 'via-ingest'; z = 'COPY三庫' },
                @{ n = 'via-gh'; z = 'GitHub' },
                @{ n = 'via-aea'; z = 'ETF29' },
                @{ n = 'via-rev'; z = '月營收U' },
                @{ n = 'via-handle'; z = '全做' },
                @{ n = 'via-hand'; z = '交接' },
                @{ n = 'via-status'; z = '狀態' },
                @{ n = 'via-help'; z = '說明' }
            )
            $br = [Windows.Media.BrushConverter]::new()
            foreach ($p in $pinned) {
                $b = New-Object System.Windows.Controls.Button
                $b.Content = $p.n
                $b.ToolTip = $p.z
                $b.Margin = '0,0,6,6'
                $b.Padding = '8,3'
                $b.MinWidth = 72
                $b.Background = $br.ConvertFrom('#1C2330')
                $b.Foreground = $br.ConvertFrom('#D7DDE8')
                $b.BorderBrush = $br.ConvertFrom('#3D4A5C')
                $b.FontFamily = 'Cascadia Mono, Consolas'
                $b.FontSize = 11
                $b.Tag = $p.n
                $b.Add_Click({
                        $name = $this.Tag
                        $hint.Text = "已送出 $name · 看左邊 PS"
                        try { $ParentRS.Events.GenerateEvent('VIA.UI', $null, @($name), $null) | Out-Null } catch {}
                        try { [Windows.Clipboard]::SetText([string]$name) } catch {}
                    })
                [void]$bar.Children.Add($b)
            }
            $grid.Add_MouseDoubleClick({
                    $item = $grid.SelectedItem
                    if ($item -and $item.Name) {
                        $hint.Text = "已複製 $($item.Name) · $($item.Note)"
                        try { [Windows.Clipboard]::SetText([string]$item.Name) } catch {}
                    }
                })
            [void]$win.ShowDialog()
        })
    [void]$ps.BeginInvoke()
    Lamp 'GREEN' 'UI' '右側板 448px · 上方鎖定 · 中文說明 · 左邊 PS 可打字'
}

Lamp 'GREEN' 'LOAD' 'via-enter / via-entry / via-env / via-path / via-gh / via-ingest / via-matrix 已註冊本視窗'
via-enter | Out-Null
try { via-matrix } catch { Lamp 'YELLOW' 'UI' "WPF 未開 · $($_.Exception.Message) · 仍可用 via-enter / via-ingest" }
