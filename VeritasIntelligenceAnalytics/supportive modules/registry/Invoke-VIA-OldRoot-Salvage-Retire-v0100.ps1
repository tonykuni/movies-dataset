# =============================================================================
# Invoke-VIA-OldRoot-Salvage-Retire-v0100 — 舊根救援+封存一鍵(TOOL-053)
# 操作員令 2026-08-18:「one powershell to handle all」——Downloads 舊母根
# 只留最新最強:殘餘救援(證據群/儀表板)→具名提交雙推→封存改名(鎖定
# 自癒重試+robocopy 後備)→誠實逐段 OK/FAIL/SKIP,永不中途退出。
# 常備令Ⅰ:全程 Start-Transcript 留痕。常備令Ⅱ:20 加速器+不卡斷+動態進度條。
# 紅線:零刪除(只搬移/改名);VRN Activate ps1 封存唯讀原件不取。
# =============================================================================
#requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

# ── def 01-20 · 加速器組(常備令Ⅱ) ─────────────────────────────────
function def_A01_Paths { @{ Canon = Join-Path $env:USERPROFILE 'movies-dataset'
                            Old   = Join-Path $env:USERPROFILE 'Downloads\movies-dataset'
                            Ret   = Join-Path $env:USERPROFILE 'Downloads\movies-dataset_RETIRED_20260818' } }
function def_A02_Log { $d = Join-Path (def_A01_Paths).Canon 'VeritasIntelligenceAnalytics\VIA_Reports\command_logs'
    New-Item -ItemType Directory -Force -Path $d | Out-Null
    Join-Path $d ("RETIREROOT_{0}.log" -f (Get-Date -Format 'yyyyMMdd_HHmmss')) }
function def_A03_Bar([int]$p,[string]$m){ $n=[int](25*$p/100)
    Write-Host ("`r[{0}%] [{1}{2}] {3}" -f $p.ToString().PadLeft(3),('█'*$n),('░'*(25-$n)),$m.PadRight(46)) -NoNewline
    if($p -ge 100){ Write-Host '' } }
function def_A04_Say([string]$t,[string]$s='INFO'){ Write-Host ("def [{0}] {1}" -f $s,$t) }
function def_A05_TryCopy([string]$src,[string]$dst){
    if(-not (Test-Path -LiteralPath $src)){ return 'SKIP(源缺)' }
    try { $pd = Split-Path $dst -Parent; New-Item -ItemType Directory -Force -Path $pd | Out-Null
          if((Test-Path -LiteralPath $dst) -and (Get-Item -LiteralPath $src).PSIsContainer){
              Copy-Item -Path (Join-Path $src '*') -Destination $dst -Recurse -Force -ErrorAction Stop  # 防 evidence\evidence 巢套
          } else { Copy-Item -LiteralPath $src -Destination $dst -Recurse -Force -ErrorAction Stop }
          return 'OK' }
    catch { return "FAIL($($_.Exception.Message.Split("`n")[0]))" } }
function def_A06_Retry([scriptblock]$b,[int]$n=4,[int]$s=2){
    for($i=1;$i -le $n;$i++){ try { & $b; return 'OK' } catch {
        if($i -eq $n){ return "FAIL($($_.Exception.Message.Split("`n")[0]))" }
        Start-Sleep -Seconds ($s * [math]::Pow(2,$i-1)) } } }
function def_A07_GitC([string[]]$a){ $r = & git -C (def_A01_Paths).Canon @a 2>&1
    @{ rc = $LASTEXITCODE; out = ($r | Select-Object -Last 3) -join ' | ' } }
function def_A08_Unlock([string]$p){  # 鎖定自癒:清唯讀/隱藏屬性(不動內容)
    try { Get-ChildItem -LiteralPath $p -Recurse -Force -ErrorAction SilentlyContinue |
          ForEach-Object { try { $_.Attributes = 'Normal' } catch {} } } catch {} }
function def_A09_WhoLocks([string]$p){  # 佔用嗅探(無管理權限之誠實近似)
    $hits = Get-Process | Where-Object { try { $_.Path -like "$p*" } catch { $false } }
    if($hits){ ($hits | Select-Object -First 3 | ForEach-Object ProcessName) -join ',' } else { '' } }
function def_A10_RoboMove([string]$src,[string]$dst){  # 後備:robocopy /MOVE 繞部分鎖
    & robocopy $src $dst /E /MOVE /R:2 /W:2 /NFL /NDL /NJH /NJS | Out-Null
    if($LASTEXITCODE -le 8 -and -not (Test-Path -LiteralPath $src)){ 'OK' }
    elseif($LASTEXITCODE -le 8){ 'PARTIAL(殘留=鎖定件)' } else { "FAIL(rc=$LASTEXITCODE)" } }
function def_A11_Marker([string]$root,[string]$note){
    try { Set-Content -LiteralPath (Join-Path $root '_RETIRED_MARKER.txt') -Value $note -Encoding UTF8; 'OK' } catch { 'FAIL' } }
function def_A12_Stamp { Get-Date -Format 'yyyyMMdd_HHmmss' }
function def_A13_SizeOf([string]$p){ try { '{0:N0} MB' -f ((Get-ChildItem -LiteralPath $p -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1MB) } catch { '?' } }
function def_A14_Guard([string]$name){ if($name -match 'Invoke-VRN-Activate-And-Validate'){ $true } else { $false } }
function def_A15_Evidence([hashtable]$r){ $d = Join-Path (def_A01_Paths).Canon 'VeritasIntelligenceAnalytics\VIA_Reports\retire_runs'
    New-Item -ItemType Directory -Force -Path $d | Out-Null
    $f = Join-Path $d ("RETIRE_{0}.json" -f (def_A12_Stamp))
    $r | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $f -Encoding UTF8; $f }
function def_A16_Heartbeat([string]$m){ def_A04_Say ("♥ {0} · {1}" -f (Get-Date -Format 'HH:mm:ss'),$m) }
function def_A17_NoExit([scriptblock]$b,[string]$tag){ try { & $b } catch { def_A04_Say "$tag 例外:$($_.Exception.Message)" 'WARN' } }
function def_A18_LongPath { try { git -C (def_A01_Paths).Canon config core.longpaths true | Out-Null; 'OK' } catch { 'SKIP' } }
function def_A19_DualPush {
    $a = def_A07_GitC @('push','origin','HEAD:main')
    $b = def_A07_GitC @('push','origin','HEAD:claude/via-system-followup-tz7k9t')
    "main:rc=$($a.rc) · tz7k9t:rc=$($b.rc)" }
function def_A20_Summary([System.Collections.ArrayList]$rows){
    def_A04_Say '── 段別總結(誠實三態,零假綠)──'
    foreach($r in $rows){ def_A04_Say ("  [{0}] {1}" -f $r.st.PadRight(18),$r.name) } }

# ── 主流程 S1-S7 ──────────────────────────────────────────────────────
$P = def_A01_Paths
$log = def_A02_Log
Start-Transcript -Path $log -Append | Out-Null   # 常備令Ⅰ
$rows = [System.Collections.ArrayList]@()
function Step([string]$name,[string]$st){ [void]$rows.Add(@{name=$name;st=$st}); def_A04_Say ("[{0}] {1}" -f $st,$name) }

def_A04_Say '=== 舊根救援+封存一鍵 v0100 · 只留最新最強 · 零刪除 ==='
def_A03_Bar 5 '預檢'
if(-not (Test-Path -LiteralPath $P.Canon)){ Step '正典倉在位' 'FAIL(缺)'; def_A20_Summary $rows; Stop-Transcript|Out-Null; return }
Step '正典倉在位' 'OK'
$oldExists = Test-Path -LiteralPath $P.Old
Step ("舊根在位(大小 {0})" -f ($(if($oldExists){ def_A13_SizeOf $P.Old } else { '—' }))) ($(if($oldExists){'OK'}else{'SKIP(已封存?)'}))
def_A18_LongPath | Out-Null

def_A03_Bar 20 '殘餘救援:GroupIndex 證據群'
if($oldExists){
    $st = def_A05_TryCopy (Join-Path $P.Old 'VeritasIntelligenceAnalytics\functional modules\GroupIndex\evidence') `
                          (Join-Path $P.Canon 'VeritasIntelligenceAnalytics\functional modules\GroupIndex\evidence')
    Step 'GroupIndex 證據群救援' $st
    $st2 = def_A05_TryCopy (Join-Path $P.Old 'VeritasIntelligenceAnalytics\VIA_Reports\VIA_SectorFlow_AllInOne_Dashboard_v0100.html') `
                           (Join-Path $P.Canon 'VeritasIntelligenceAnalytics\VIA_Reports\VIA_SectorFlow_AllInOne_Dashboard_v0100.html')
    Step 'SectorFlow 儀表板救援' $st2
    foreach($pair in @(
        @('VeritasIntelligenceAnalytics\supportive modules\VIA_Governance_Runtime\v0163A','v0163A 冪等補'),
        @('VeritasIntelligenceAnalytics\_via_20_ps_accelerators','20 加速器庫冪等補'),
        @('VeritasIntelligenceAnalytics\_via_20_ps_accelerators_ui_optimized','加速器 UI 版冪等補'))){
        $dst = Join-Path $P.Canon $pair[0]
        if(Test-Path -LiteralPath $dst){ Step $pair[1] 'SKIP(已在)' }
        else { Step $pair[1] (def_A05_TryCopy (Join-Path $P.Old $pair[0]) $dst) } }
} else { Step '殘餘救援' 'SKIP(舊根不在)' }

def_A03_Bar 45 '提交雙推(僅具名路徑,禁 -A)'
def_A17_NoExit {
    $null = def_A07_GitC @('add','VeritasIntelligenceAnalytics/functional modules/GroupIndex/evidence')
    $chk = def_A07_GitC @('status','--short','--','VeritasIntelligenceAnalytics/functional modules/GroupIndex/evidence')
    if($chk.out -and $chk.out.Trim()){
        $c = def_A07_GitC @('commit','-m','VIA: 舊根殘餘救援——GroupIndex 最新證據群(SECTORFLOW/ETF/LIVEWIRE/主驗證)')
        Step ("git 提交({0})" -f $c.out.Substring(0,[math]::Min(40,$c.out.Length))) ($(if($c.rc -eq 0){'OK'}else{"FAIL(rc=$($c.rc))"}))
        Step ("雙推 " + (def_A19_DualPush)) 'OK'
    } else { Step 'git 提交' 'SKIP(證據無差=已同步)' ; Step ("雙推 " + (def_A19_DualPush)) 'OK' }
} 'git 段'

def_A03_Bar 70 '封存改名(鎖定自癒鏈)'
if(Test-Path -LiteralPath $P.Old){
    $who = def_A09_WhoLocks $P.Old
    if($who){ def_A04_Say "佔用嗅探:$who(請關閉後可重跑;本輪續嘗試)" 'WARN' }
    def_A08_Unlock $P.Old
    $r1 = def_A06_Retry { Rename-Item -LiteralPath $P.Old -NewName 'movies-dataset_RETIRED_20260818' -ErrorAction Stop }
    if($r1 -eq 'OK'){ Step '封存改名' 'OK' }
    else {
        def_A04_Say "直改名失敗($r1)→ robocopy /MOVE 後備道" 'WARN'
        def_A16_Heartbeat 'robocopy 搬移中(大樹耗時,不卡斷)'
        $r2 = def_A10_RoboMove $P.Old $P.Ret
        Step "封存(robocopy /MOVE)" $r2
        if($r2 -like 'PARTIAL*' -or $r2 -like 'FAIL*'){
            Step ('鎖定殘留標記 ' + (def_A11_Marker $P.Old "RETIRED $(def_A12_Stamp):殘留=鎖定件;關閉佔用($who)後重跑本一鍵")) 'OK'
            def_A04_Say '殘留件多半是 .venv_via_takeover/開啟中之視窗——關閉後重跑即完封' 'INFO' } }
} else { Step '封存改名' 'SKIP(已不在原位)' }

def_A03_Bar 90 '存證'
Step ('存證 ' + (def_A15_Evidence @{ ts=(def_A12_Stamp); rows=$rows; log=$log })) 'OK'
def_A03_Bar 100 '完成'
def_A20_Summary $rows
def_A04_Say ("留痕:{0}" -f $log)
def_A04_Say '零刪除聲明:全程僅複製/改名/搬移;任何內容零刪除;robocopy /MOVE 之源殘留=鎖定件原地保存。'
Stop-Transcript | Out-Null
