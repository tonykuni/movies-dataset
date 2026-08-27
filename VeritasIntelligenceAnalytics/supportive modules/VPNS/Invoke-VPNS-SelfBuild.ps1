#requires -Version 7.0
<#
  Invoke-VPNS-SelfBuild.ps1  ·  VIA / VeritasNexusCore — 自我探索一鍵建置
  ------------------------------------------------------------------------
  在【你本機】執行:自己掃 base + supportive、用 AST 解析治理三檔、生 SSOT_VPNS.json、
  偵測缺件引擎並生 parse-clean stub(需 -PromoteToken 才 promote)、六個獨立唯讀 lane
  回報 現在/未來/剩餘步驟、single-writer 合併、≤3 輪全景修正、跳出 matrix HTML 報告。

  安全設計(依可行性研究):預設順序(LL-17)、並行 opt-in 且 timeout+空回退、
  single-writer SSOT(atomic temp+rename)、append-only(只增不減,quarantine 不硬刪)、
  Parse=0 gate、精準錨點、缺件僅 stub 不自動 promote(避免九頭龍/修壞)。

  用法:
    貼上整段直接跑(paste-and-run),或  pwsh -File .\Invoke-VPNS-SelfBuild.ps1
    首次:  .\Invoke-VPNS-SelfBuild.ps1 -OpenReport
    並行:  .\Invoke-VPNS-SelfBuild.ps1 -Parallel -OpenReport
    promote 缺件 stub 進 live:  .\Invoke-VPNS-SelfBuild.ps1 -PromoteToken PROMOTE_VPNS_v3
#>
[CmdletBinding()]
param(
  [string]$Root          = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics',
  [switch]$Parallel,                 # opt-in;預設順序(快速唯讀 lane 更穩,LL-17)
  [int]   $Rounds        = 3,        # ≤3 輪全景修正(避免修壞)
  [int]   $LaneTimeoutSec = 120,
  [string]$PromoteToken,             # = 'PROMOTE_VPNS_v3' 才把 stub promote 進 live
  [switch]$OpenReport,
  [switch]$ScanAllProjects           # 掃整個 functional modules(VAP/VRN/VDF/VPNS 四專案),預設僅 VPNS
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
$PROMOTE_OK = 'PROMOTE_VPNS_v3'

# ---------- 0. 路徑解析 + 工具在磁碟驗證 (LL-21) ----------
$FuncRoot   = Join-Path $Root 'functional modules'
$VpnsBase   = Join-Path $FuncRoot 'VPNS'
# 掃描範圍可變(-ScanAllProjects 覆蓋 VAP/VRN/VDF/VPNS 四專案);輸出位置永遠釘在 VPNS base(規格:SSOT 存 base)
$Base       = if ($ScanAllProjects) { $FuncRoot } else { $VpnsBase }
$Supportive = Join-Path $Root 'supportive modules'
$Govern = @(
  (Join-Path $Supportive 'Read_Me_VeritasNexusCore.md'),
  (Join-Path $Supportive 'Invoke-VeritasNexusCore.ps1'),
  (Join-Path $Supportive 'Invoke-VIA-PolyglotCheckTestRepair-v0101.ps1')
)
$Work    = Join-Path $VpnsBase '_vpns_selfbuild'
$LaneDir = Join-Path $Work 'lanes'
$StageDir= Join-Path $VpnsBase '_generated\staging'
$BackupDir = Join-Path $Work ('backup_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
$SsotPath = Join-Path $VpnsBase 'SSOT_VPNS.json'
$ReportPath = Join-Path $VpnsBase 'VPNS_Matrix_Report.html'

foreach ($d in @($Work,$LaneDir,$StageDir,$BackupDir)) {
  if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

$PasteMode = [string]::IsNullOrEmpty($PSCommandPath)   # LL-21: 貼上執行 vs -File
Write-Host ("[VPNS] Root={0}" -f $Root)
Write-Host ("[VPNS] mode={0} · parallel={1} · rounds={2}" -f ($(if($PasteMode){'paste-and-run'}else{'-File'})), [bool]$Parallel, $Rounds)

# ---------- helpers ----------
function Write-Utf8NoBom {
  param([string]$Path,[string]$Text)
  [System.IO.File]::WriteAllText($Path, $Text, [System.Text.UTF8Encoding]::new($false))
}
function Write-JsonAtomic {
  param([string]$Path,[object]$Obj)          # single-writer atomic: temp + rename
  $json = $Obj | ConvertTo-Json -Depth 12
  $tmp  = "$Path.tmp"
  Write-Utf8NoBom -Path $tmp -Text $json
  Move-Item -Path $tmp -Destination $Path -Force
}
$script:ShaCachePath = Join-Path $Work 'sha_cache.json'
$script:ShaCache = @{}
if (Test-Path $script:ShaCachePath) {
  try { $script:ShaCache = Get-Content $script:ShaCachePath -Raw -Encoding UTF8 | ConvertFrom-Json -AsHashtable } catch { $script:ShaCache=@{} }
}
function Get-Sha12 {   # A1 加速:path+size+mtime 快取,重掃免重算
  param([string]$Path)
  if (-not (Test-Path $Path -PathType Leaf)) { return '-' }
  if (-not (Test-Path variable:script:ShaCache)) { $script:ShaCache=@{} }
  $fi = Get-Item -LiteralPath $Path
  $key = "$Path|$($fi.Length)|$($fi.LastWriteTimeUtc.Ticks)"
  if ($script:ShaCache.ContainsKey($key)) { return $script:ShaCache[$key] }
  $h = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.Substring(0,12)
  $script:ShaCache[$key] = $h
  return $h
}
function Test-ParseClean {
  param([string]$Path)                        # Parse=0 gate for .ps1
  $errs = $null; $toks = $null
  try {
    [System.Management.Automation.Language.Parser]::ParseFile($Path,[ref]$toks,[ref]$errs) | Out-Null
    return @{ ok = ($errs.Count -eq 0); errors = $errs.Count }
  } catch { return @{ ok = $false; errors = -1 } }
}
function Get-Ps1Facts {
  param([string]$Path)                        # AST → functions/params/referenced commands
  $errs=$null;$toks=$null
  $ast = [System.Management.Automation.Language.Parser]::ParseFile($Path,[ref]$toks,[ref]$errs)
  $fns = $ast.FindAll({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst]},$true) |
         ForEach-Object { $_.Name }
  $cmds = $ast.FindAll({param($n) $n -is [System.Management.Automation.Language.CommandAst]},$true) |
          ForEach-Object { $_.GetCommandName() } | Where-Object { $_ } | Sort-Object -Unique
  # 引擎樣式:Invoke-* / *-Engine / Engine 名稱 token
  $engines = $cmds | Where-Object { $_ -match '(?i)(Invoke-|-Engine$|Engine)' } | Sort-Object -Unique
  @{ functions=@($fns); commands=@($cmds); engines=@($engines); parse=(Test-ParseClean $Path) }
}
function Get-MdSections {
  param([string]$Path)                        # markdown → ## sections + engine-like tokens
  if (-not (Test-Path $Path -PathType Leaf)) { return @{ sections=@(); engines=@() } }
  $lines = Get-Content -Path $Path -Encoding UTF8
  $secs = $lines | Where-Object { $_ -match '^#{1,3}\s+' } | ForEach-Object { ($_ -replace '^#{1,3}\s+','').Trim() }
  $eng  = ($lines -join "`n" | Select-String -Pattern '(?i)([A-Za-z][\w]*Engine|Invoke-[A-Za-z][\w-]+|VPNS[\w-]+|VRN[\w-]+|VDF[\w-]+)' -AllMatches).Matches |
          ForEach-Object { $_.Value } | Sort-Object -Unique
  @{ sections=@($secs); engines=@($eng) }
}
function New-StepTracker {
  param([string[]]$Steps)
  [pscustomobject]@{ Steps=$Steps; Index=0; Total=$Steps.Count;
    Current={param($t) if($t.Index -lt $t.Total){$t.Steps[$t.Index]}else{'done'}};
  }
}

# ---------- 六個獨立唯讀 lane(各自只寫自己的 lane 檔 → 可安全並行) ----------
# 每個 lane: Name, Steps[], Scriptblock(ctx) → 回傳 result 物件(含 current/next/remaining)
$LaneDefs = @(
  @{ Name='L1_Inventory_Base';  Steps=@('enumerate','hash','write')
     Do = { param($ctx)
       $items = @()
       if (Test-Path $ctx.Base) {
         Get-ChildItem -Path $ctx.Base -Recurse -File -ErrorAction SilentlyContinue |
           Where-Object { $_.FullName -notmatch '_vpns_selfbuild|_generated|\.git|node_modules|__pycache__|VIA_RUNS|backup_' } |
           ForEach-Object { $items += @{ path=$_.FullName; ext=$_.Extension; kb=[math]::Round($_.Length/1kb,1);
             sha12=$(if($_.Length -le 50MB){Get-Sha12 $_.FullName}else{'SKIP>50MB'}) } }
       }
       @{ lane='L1_Inventory_Base'; count=$items.Count; items=$items }
     } },
  @{ Name='L2_Inventory_Support'; Steps=@('enumerate','hash','write')
     Do = { param($ctx)
       $items=@()
       if (Test-Path $ctx.Supportive) {
         Get-ChildItem -Path $ctx.Supportive -Recurse -File -ErrorAction SilentlyContinue |
           Where-Object { $_.FullName -notmatch '\.git|node_modules|__pycache__|VIA_RUNS|backup_' } |
           ForEach-Object { $items += @{ path=$_.FullName; ext=$_.Extension; kb=[math]::Round($_.Length/1kb,1);
             sha12=$(if($_.Length -le 50MB){Get-Sha12 $_.FullName}else{'SKIP>50MB'}) } }
       }
       @{ lane='L2_Inventory_Support'; count=$items.Count; items=$items }
     } },
  @{ Name='L3_Parse_ReadMe'; Steps=@('read','sections','engines')
     Do = { param($ctx)
       $md = Get-MdSections $ctx.Govern[0]
       @{ lane='L3_Parse_ReadMe'; exists=(Test-Path $ctx.Govern[0]); sections=$md.sections; engines=$md.engines }
     } },
  @{ Name='L4_AST_Invoke'; Steps=@('ast-core','ast-polyglot','collect')
     Do = { param($ctx)
       $out=@{}
       foreach ($p in @($ctx.Govern[1],$ctx.Govern[2])) {
         $k = Split-Path $p -Leaf
         if (Test-Path $p -PathType Leaf) { $out[$k] = (Get-Ps1Facts $p) }
         else { $out[$k] = @{ missing=$true } }
       }
       @{ lane='L4_AST_Invoke'; parsed=$out }
     } },
  @{ Name='L5_ParseGate_All'; Steps=@('scan-ps1','parse=0','issues')
     Do = { param($ctx)
       $issues=@(); $ok=0; $bad=0
       Get-ChildItem -Path $ctx.Base,$ctx.Supportive -Recurse -Filter *.ps1 -ErrorAction SilentlyContinue |
         Where-Object { $_.FullName -notmatch '_vpns_selfbuild' } |
         ForEach-Object {
           $r = Test-ParseClean $_.FullName
           if ($r.ok) { $ok++ } else { $bad++; $issues += @{ path=$_.FullName; parse_errors=$r.errors; type='parse'; dep=$false } }
         }
       @{ lane='L5_ParseGate_All'; parse_ok=$ok; parse_bad=$bad; issues=$issues }
     } },
  @{ Name='L6_LangProbe'; Steps=@('py','node','libs')
     Do = { param($ctx)
       $py = (Get-Command python -ErrorAction SilentlyContinue) ?? (Get-Command python3 -ErrorAction SilentlyContinue)
       $node = Get-Command node -ErrorAction SilentlyContinue
       $pyc=@(); if ($py) {   # A4 加速:單一 python 行程批次編譯(免每檔 spawn)
         $pyFiles = Get-ChildItem -Path $ctx.Base,$ctx.Supportive -Recurse -Filter *.py -ErrorAction SilentlyContinue |
                    Where-Object { $_.FullName -notmatch '__pycache__' } | Select-Object -ExpandProperty FullName
         if ($pyFiles) {
           $lst = [System.IO.Path]::GetTempFileName()
           $pyFiles | Set-Content -Path $lst -Encoding utf8
           $code = "import py_compile,sys`nfor p in open(sys.argv[1],encoding='utf-8'):`n p=p.strip()`n if not p: continue`n try: py_compile.compile(p,doraise=True); print('OK|'+p)`n except Exception: print('BAD|'+p)"
           $out = & $py.Source -c $code $lst 2>$null
           foreach ($ln in @($out)) {
             if ($ln -match '^(OK|BAD)\|(.+)$') { $pyc += @{ path=$Matches[2]; ok=($Matches[1] -eq 'OK') } }
           }
           Remove-Item $lst -ErrorAction SilentlyContinue
         }
       }
       $pySrc = if ($py) { $py.Source } else { '-' }
       $nodeSrc = if ($node) { $node.Source } else { '-' }
       @{ lane='L6_LangProbe'; python=$pySrc; node=$nodeSrc; py_compiled=$pyc }
     } }
)

# ---------- lane 執行(順序預設 / 並行 opt-in + timeout + 空回退 LL-17) ----------
$ctx = @{ Base=$Base; Supportive=$Supportive; Govern=$Govern }
$LaneResults = [System.Collections.Generic.List[object]]::new()

function Invoke-LaneSequential {
  param($defs,$ctx,$laneDir)
  foreach ($d in $defs) {
    $tr = New-StepTracker $d.Steps
    Write-Host ("  [lane] {0} · steps={1} · running..." -f $d.Name, $d.Steps.Count)
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $res = & $d.Do $ctx
    $sw.Stop()
    $res.elapsed_ms = [int]$sw.ElapsedMilliseconds
    if ($sw.ElapsedMilliseconds -lt 500 -and $res.ContainsKey('count') -and $res.count -eq 0) {
      Write-Warning ("  [LL-17?] lane {0} sub-0.5s + empty — 疑似 wait-loop/路徑錯,檢查 Root 參數" -f $d.Name)
      $res.ll17_suspect = $true
    }
    $res.steps_total = $d.Steps.Count
    $res.current = $d.Steps[[math]::Min(1,$d.Steps.Count-1)]
    $res.next    = $d.Steps[[math]::Min(2,$d.Steps.Count-1)]
    $res.remaining = 0
    $res.status = 'done'
    Write-JsonAtomic -Path (Join-Path $laneDir ($d.Name + '.json')) -Obj $res
    $LaneResults.Add($res)
  }
}

if ($Parallel -and (Get-Command Start-ThreadJob -ErrorAction SilentlyContinue)) {
  Write-Host "[VPNS] parallel lanes (opt-in) with timeout + sequential fallback"
  # ThreadJob runspace 看不到主 session 的 functions → 以 InitializationScript 注入 helpers
  # ${function:Name} 已含原 param 區塊,直接包 function 名即可(勿再包 param → 雙重宣告)
  $helperSrc = @(
    "function Get-Sha12 { $(${function:Get-Sha12}) }",
    "function Test-ParseClean { $(${function:Test-ParseClean}) }",
    "function Get-Ps1Facts { $(${function:Get-Ps1Facts}) }",
    "function Get-MdSections { $(${function:Get-MdSections}) }"
  ) -join "`n"
  $init = [scriptblock]::Create($helperSrc)
  $jobs = @()
  foreach ($d in $LaneDefs) {
    $jobs += Start-ThreadJob -Name $d.Name -InitializationScript $init -ArgumentList $d,$ctx,$LaneDir -ScriptBlock {
      param($d,$ctx,$laneDir)
      $res = & $d.Do $ctx
      $res.status='done'; $res.steps_total=$d.Steps.Count; $res.remaining=0
      $p = Join-Path $laneDir ($d.Name + '.json')
      ($res | ConvertTo-Json -Depth 12) | Set-Content -Path $p -Encoding utf8
      $res
    }
  }
  $done = Wait-Job -Job $jobs -Timeout $LaneTimeoutSec
  foreach ($j in $jobs) {
    $r = if ($j.State -eq 'Completed') { Receive-Job $j } else { $null }
    if ($null -eq $r -or @($r).Count -eq 0) {                 # LL-17 空回退:該 lane 改順序重跑
      Write-Warning ("  lane {0} empty/timeout → sequential fallback" -f $j.Name)
      $def = $LaneDefs | Where-Object { $_.Name -eq $j.Name }
      $r = & $def.Do $ctx; $r.status='done(fallback)'; $r.steps_total=$def.Steps.Count; $r.remaining=0
      Write-JsonAtomic -Path (Join-Path $LaneDir ($j.Name + '.json')) -Obj $r
    }
    $LaneResults.Add($r)
  }
  $jobs | Remove-Job -Force -ErrorAction SilentlyContinue
} else {
  Invoke-LaneSequential -defs $LaneDefs -ctx $ctx -laneDir $LaneDir
}

# ---------- single-writer 合併 → SSOT_VPNS.json (append-only) ----------
function Get-LaneByName { param($name) $LaneResults | Where-Object { $_.lane -eq $name } | Select-Object -First 1 }
function Get-LaneVal {   # StrictMode-safe lane accessor (lane may be $null on parallel timeout)
  param($lane,[string]$key,$default)
  if ($null -ne $lane -and $lane.ContainsKey($key)) { return $lane[$key] }
  return $default
}

$L1=Get-LaneByName 'L1_Inventory_Base'; $L2=Get-LaneByName 'L2_Inventory_Support'
$L3=Get-LaneByName 'L3_Parse_ReadMe';   $L4=Get-LaneByName 'L4_AST_Invoke'
$L5=Get-LaneByName 'L5_ParseGate_All';  $L6=Get-LaneByName 'L6_LangProbe'

# 缺件引擎:治理檔宣告的 engines − 磁碟實際存在的 *.ps1/*.py 檔名
$declaredEngines = @()
$declaredEngines += (Get-LaneVal $L3 'engines' @())
$l4p = Get-LaneVal $L4 'parsed' @{}
if ($l4p.Count) { foreach ($k in $l4p.Keys) { if ($l4p[$k].ContainsKey('engines')) { $declaredEngines += $l4p[$k].engines } } }
$declaredEngines = $declaredEngines | Where-Object { $_ } | Sort-Object -Unique

$onDisk = @()
foreach ($L in @($L1,$L2)) { if ($null -ne $L -and $L.ContainsKey('items')) { $onDisk += ($L.items | ForEach-Object { [IO.Path]::GetFileNameWithoutExtension($_.path) }) } }
$onDisk = $onDisk | Sort-Object -Unique

$missing = @($declaredEngines | Where-Object { $tok=$_; -not ($onDisk | Where-Object { $_ -match [regex]::Escape($tok) }) })

# 讀既有 SSOT(只增不減:保留舊 provenance,新增本次)
$prev = $null
if (Test-Path $SsotPath) { try { $prev = Get-Content $SsotPath -Raw -Encoding UTF8 | ConvertFrom-Json } catch {} }

$ssot = [ordered]@{
  meta = @{
    system='VPNS / VeritasNexusCore'; generated=(Get-Date -Format s);
    root=$Root; base=$Base; supportive=$Supportive; append_only=$true; parallel=[bool]$Parallel
  }
  governance = @($Govern | ForEach-Object { @{ path=$_; sha12=(Get-Sha12 $_); exists=(Test-Path $_) } })
  readme = @{ sections=(Get-LaneVal $L3 'sections' @()); engines=(Get-LaneVal $L3 'engines' @()) }
  invoke_ast = (Get-LaneVal $L4 'parsed' @{})
  inventory = @{ base_count=(Get-LaneVal $L1 'count' 0); support_count=(Get-LaneVal $L2 'count' 0) }
  engines = @{ declared=$declaredEngines; on_disk_hint=$onDisk; missing=$missing }
  parse_gate = @{ ok=(Get-LaneVal $L5 'parse_ok' 0); bad=(Get-LaneVal $L5 'parse_bad' 0); issues=(Get-LaneVal $L5 'issues' @()) }
  lang = @{ python=(Get-LaneVal $L6 'python' '-'); node=(Get-LaneVal $L6 'node' '-') }
  provenance_prev = if ($prev) { $prev.meta } else { $null }
}
Write-JsonAtomic -Path $SsotPath -Obj $ssot
Write-Host ("[VPNS] SSOT → {0}  (declared engines={1}, missing={2})" -f $SsotPath, $declaredEngines.Count, $missing.Count)

# ---------- 缺件引擎:生 parse-clean stub(需 -PromoteToken 才 promote 進 live) ----------
$stubTemplate = @'
#requires -Version 7.0
# AUTO-STUB (VPNS self-build) — NeedsImpl. 不含實作,只保證 Parse=0 與可被載入。
function {NAME} {
  [CmdletBinding()] param([hashtable]$Context)
  Write-Verbose "[stub] {NAME} invoked — NeedsImpl"
  return [pscustomobject]@{ engine='{NAME}'; status='NeedsImpl'; ok=$false }
}
# dot-source 即可見;勿用 Export-ModuleMember(.ps1 非 module,執行會拋錯)
'@
$stubMade=@()
foreach ($m in $missing) {
  $safe = ($m -replace '[^A-Za-z0-9_\-]','_')
  $stubPath = Join-Path $StageDir ("$safe.stub.ps1")
  Write-Utf8NoBom -Path $stubPath -Text ($stubTemplate -replace '\{NAME\}',$safe)
  $pc = Test-ParseClean $stubPath
  $stubMade += @{ engine=$m; stub=$stubPath; parse_ok=$pc.ok }
}
if ($stubMade.Count) { Write-Host ("[VPNS] generated {0} parse-clean stubs → {1}" -f $stubMade.Count,$StageDir) }

# promote gate(只增不減:promote = 複製進 live 的 engines 夾,不覆蓋既有)
$promoted=@()
if ($PromoteToken) {
  if ($PromoteToken -eq $PROMOTE_OK) {
    $live = Join-Path $VpnsBase 'engines'; if (-not (Test-Path $live)) { New-Item -ItemType Directory -Path $live -Force | Out-Null }
    foreach ($s in $stubMade) {
      $dest = Join-Path $live (Split-Path $s.stub -Leaf)
      if (Test-Path $dest) { Write-Warning ("  skip(exists,只增不減): {0}" -f $dest) }
      else { Copy-Item $s.stub $dest; $promoted += $dest }
    }
    Write-Host ("[VPNS] promoted {0} stubs to live engines/" -f $promoted.Count)
  } else { Write-Warning "PromoteToken 不符,拒絕 promote(需 PROMOTE_VPNS_v3)" }
}

# ---------- ≤3 輪全景修正迴圈(全面 → 順序 → 收尾;回歸閘 + rollback) ----------
function Invoke-PanoramicScan {
  param($base,$supportive)
  $issues=@()
  Get-ChildItem -Path $base,$supportive -Recurse -Filter *.ps1 -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '_vpns_selfbuild' } |
    ForEach-Object {
      $r = Test-ParseClean $_.FullName
      if (-not $r.ok) { $issues += @{ path=$_.FullName; kind='parse'; errors=$r.errors; independent=$true } }
    }
  # 依賴分類:parse 錯彼此獨立(independent=可同時修);後續實作型依賴 → sequential(此處先標)
  ,$issues
}
$roundLog=@()
for ($round=1; $round -le $Rounds; $round++) {
  $issues = Invoke-PanoramicScan -base $Base -supportive $Supportive
  $indep = @($issues | Where-Object { $_.independent })
  $seq   = @($issues | Where-Object { -not $_.independent })
  # 快照(rollback 用)——只增不減:每輪存 backup,不動原檔
  $snap = Join-Path $BackupDir ("round$round"); New-Item -ItemType Directory -Path $snap -Force | Out-Null
  $issues | ForEach-Object { if (Test-Path $_.path) { Copy-Item $_.path (Join-Path $snap (Split-Path $_.path -Leaf)) -ErrorAction SilentlyContinue } }
  # 本 harness 不自動改碼(避免修壞);只『定位 + 分類 + 記錄錨點』,交人工/PolyglotCheckTestRepair 修
  $roundLog += @{ round=$round; total=$issues.Count; independent=$indep.Count; sequential=$seq.Count;
                  anchors=@($issues | ForEach-Object { @{ path=$_.path; kind=$_.kind } }) }
  Write-Host ("  [round {0}] issues={1} (independent={2}, sequential={3})" -f $round,$issues.Count,$indep.Count,$seq.Count)
  if ($issues.Count -eq 0) { Write-Host "  [round] converged (0 issues) — stop"; break }
}

# 輪間回歸閘:issues 數不得回升(修壞偵測)
for ($i=1; $i -lt $roundLog.Count; $i++) {
  if ($roundLog[$i].total -gt $roundLog[$i-1].total) {
    $roundLog[$i].regression = $true
    Write-Warning ("  [regression] round {0} issues({1}) > round {2}({3}) — 疑似修壞,檢查該輪快照" -f ($i+1),$roundLog[$i].total,$i,$roundLog[$i-1].total)
  } else { $roundLog[$i].regression = $false }
}

# ---------- 未來兩大回合 × 12 步驟 準備清單 ----------
$next12 = @(
 'R1-01 匯入 Read_Me 真實引擎清單校準 declared','R1-02 建 engine↔檔案 對應表(錨點)',
 'R1-03 缺件 stub → 真實實作(PolyglotCheckTestRepair)','R1-04 Parse=0 全綠',
 'R1-05 SSOT schema 驗證(jsonschema)','R1-06 lane 依賴圖 topo 排序',
 'R2-07 並行壓測 + timeout 校準','R2-08 回歸閘(count invariants)',
 'R2-09 promote gate 演練(token)','R2-10 matrix 報告 UI 細節',
 'R2-11 user-test 腳本','R2-12 activate + 監看'
)

# ---------- matrix HTML 報告(Visual Lock)+ 自動跳出 ----------
$laneRows = ($LaneResults | ForEach-Object {
  $st = if ($_.PSObject.Properties.Name -contains 'status') { $_.status } else { 'done' }
  "<tr><td class='l mono'>$($_.lane)</td><td class='l'>$st</td><td class='l'>$($_.steps_total)</td><td class='l'>0</td></tr>"
}) -join ''
$missRows = if ($missing.Count) { ($missing | ForEach-Object { "<tr><td class='l mono'>$_</td><td class='l'>stub 生成(待 promote)</td></tr>" }) -join '' } else { "<tr><td class='l' colspan='2'>— 無缺件</td></tr>" }
$roundRows = ($roundLog | ForEach-Object { "<tr><td class='l'>$($_.round)</td><td class='l'>$($_.total)</td><td class='l'>$($_.independent)</td><td class='l'>$($_.sequential)</td></tr>" }) -join ''
$next12Rows = ($next12 | ForEach-Object { "<li>$_</li>" }) -join ''

$html = @'
<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VPNS · Self-Build Matrix Report</title>
<style>
:root{--bg:#f5f4f0;--sf:#fff;--ink:#1e1d1a;--sub:#6b6860;--bd:#dbd9d3;--up:#c96b5a;--dn:#5a9e6f;--bl:#4c78a8;--seal:#b5291a;--amber:#c4943a}
*{box-sizing:border-box}body{background:var(--bg);color:var(--ink);font-family:"DM Sans","Noto Sans TC",system-ui,sans-serif;margin:0;padding:22px;font-size:13px}
h1{font-family:"Syne","DM Sans";font-weight:800;font-size:22px;margin:0 0 2px}
.seal{display:inline-flex;width:30px;height:30px;align-items:center;justify-content:center;border-radius:7px;background:var(--seal);color:#fff;font-weight:900;margin-right:8px;vertical-align:middle}
.sub{color:var(--sub);font-size:12px;margin-bottom:12px}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:10px 0}
.kpi{background:var(--sf);border:1px solid var(--bd);border-radius:6px;padding:10px}
.kpi .v{font-family:"DM Mono",monospace;font-size:20px;font-weight:600}.kpi .l{font-size:9.5px;color:var(--sub);text-transform:uppercase}
.card{background:var(--sf);border:1px solid var(--bd);border-radius:8px;padding:12px;margin:12px 0}
h2{font-size:14px;margin:0 0 6px}
table{width:100%;border-collapse:collapse;font-size:11.5px}th,td{padding:5px 8px;border-bottom:1px solid #eceae2;text-align:left}
th{font-size:9.5px;color:var(--sub);text-transform:uppercase}.mono{font-family:"DM Mono",monospace}.l{text-align:left}
ol{columns:2;font-size:11.5px;color:var(--sub)}
.foot{color:#9c9890;font-size:11px;margin-top:14px;border-top:1px solid var(--bd);padding-top:10px}
</style></head><body>
<h1><span class="seal">理</span>VPNS · Self-Build Matrix Report</h1>
<div class="sub">自我探索建置 · 只增不減 · Parse=0 gate · 缺件僅 stub 待 promote · ≤3 輪全景修正 · __GEN__</div>
<div class="grid">
 <div class="kpi"><div class="v">__BASEN__</div><div class="l">base 檔案</div></div>
 <div class="kpi"><div class="v">__SUPN__</div><div class="l">supportive 檔案</div></div>
 <div class="kpi"><div class="v">__PARSEOK__/__PARSEALL__</div><div class="l">Parse=0 通過</div></div>
 <div class="kpi"><div class="v">__MISSN__</div><div class="l">缺件引擎(stub)</div></div>
</div>
<div class="card"><h2>六 Lane 矩陣(現在/未來/剩餘)</h2>
 <table><thead><tr><th>Lane</th><th>狀態</th><th>步驟數</th><th>剩餘</th></tr></thead><tbody>__LANEROWS__</tbody></table></div>
<div class="card"><h2>缺件引擎(生 stub,需 -PromoteToken 才進 live)</h2>
 <table><thead><tr><th>引擎</th><th>處置</th></tr></thead><tbody>__MISSROWS__</tbody></table></div>
<div class="card"><h2>≤3 輪全景修正(定位錨點,不自動改碼避免修壞)</h2>
 <table><thead><tr><th>輪</th><th>issues</th><th>可同時修(獨立)</th><th>需順序修</th></tr></thead><tbody>__ROUNDROWS__</tbody></table></div>
<div class="card"><h2>未來兩大回合 × 12 步驟(已備妥)</h2><ol>__NEXT12__</ol></div>
<div class="foot">SSOT → SSOT_VPNS.json · 缺件 stub → _generated\staging · backup → _vpns_selfbuild\backup · append-only · 非破壞。<br>本 harness 只定位/分類/生 stub,不自動改動你的原始碼(避免九頭龍/修壞);實際修復交 Invoke-VIA-PolyglotCheckTestRepair + 人工核准。</div>
</body></html>
'@
$html = $html.
  Replace('__GEN__',(Get-Date -Format 'yyyy-MM-dd HH:mm')).
  Replace('__BASEN__',[string](Get-LaneVal $L1 'count' 0)).
  Replace('__SUPN__',[string](Get-LaneVal $L2 'count' 0)).
  Replace('__PARSEOK__',[string](Get-LaneVal $L5 'parse_ok' 0)).
  Replace('__PARSEALL__',[string]((Get-LaneVal $L5 'parse_ok' 0)+(Get-LaneVal $L5 'parse_bad' 0))).
  Replace('__MISSN__',[string]$missing.Count).
  Replace('__LANEROWS__',$laneRows).
  Replace('__MISSROWS__',$missRows).
  Replace('__ROUNDROWS__',$roundRows).
  Replace('__NEXT12__',$next12Rows)
Write-Utf8NoBom -Path $ReportPath -Text $html
Write-Host ("[VPNS] report → {0}" -f $ReportPath)
if ($OpenReport -and $env:OS -match 'Windows') { Start-Process $ReportPath }

# A1 快取落盤(下次重掃直接命中)
try { $script:ShaCache | ConvertTo-Json -Depth 3 -Compress | Set-Content -Path $script:ShaCachePath -Encoding utf8 } catch {}
Write-Host "[VPNS] done · SSOT + stubs(staging) + report 完成 · promote 需 -PromoteToken PROMOTE_VPNS_v3"

# ===== S0 SUMMARY(印在最尾;把 BEGIN~END 整段貼回對話即可解鎖回合1)=====
Write-Host "===== S0 SUMMARY BEGIN ====="
Write-Host ("mode      : {0} · parallel={1} · scanAll={2}" -f ($(if($PasteMode){'paste'}else{'-File'})), [bool]$Parallel, [bool]$ScanAllProjects)
Write-Host ("inventory : base={0} support={1}" -f (Get-LaneVal $L1 'count' 0), (Get-LaneVal $L2 'count' 0))
Write-Host ("parse     : ok={0} bad={1}" -f (Get-LaneVal $L5 'parse_ok' 0), (Get-LaneVal $L5 'parse_bad' 0))
foreach ($i in @((Get-LaneVal $L5 'issues' @()))) { if ($i) { Write-Host ("  parse-bad: {0}" -f $i.path) } }
foreach ($g in @($ssot.governance)) { Write-Host ("  gov: {0} exists={1} sha12={2}" -f (Split-Path $g.path -Leaf), $g.exists, $g.sha12) }
Write-Host ("readmeSecs: {0}" -f @($ssot.readme.sections).Count)
Write-Host ("engines   : declared={0} missing={1} stubs={2} promoted={3}" -f @($declaredEngines).Count, @($missing).Count, @($stubMade).Count, @($promoted).Count)
Write-Host ("declared  : {0}" -f ((@($declaredEngines) | Select-Object -First 40) -join ', '))
Write-Host ("missing   : {0}" -f ((@($missing) | Select-Object -First 40) -join ', '))
$rl = @($roundLog | ForEach-Object { "r{0}:{1}" -f $_.round, $_.total }) -join ' '
Write-Host ("rounds    : {0}" -f $rl)
Write-Host "===== S0 SUMMARY END ====="

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
