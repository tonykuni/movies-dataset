# VIA_PS_PyProgress_Selftest_v0101.ps1 — 中央 py 啟動器七檢 + 前後快慢實測(批542;批694 +⑦ 真百分比協定)
# v0100→v0101(批694):+⑦ 引擎印 [進度] n/N → 啟動器算出真百分比並放進 $global:VIA_PYPROG_LAST(n/d/pct);沒報進度時 pct=-1(脈動,不假裝)。
# =====================================================================
# 為什麼要有這一支
#   所有 py 指令都走 Invoke-VIAPython(中央唯一入口)。它快一點,全系統就快一點;
#   它把 stdout 吞掉一行,全系統就少一行。批542 動了它的輪詢節奏,所以必須有一組
#   **會抓到吞行/吞 rc** 的檢查釘住行為——不是只看它跑得快。
# 用法:  via-pyprog            七檢
#        via-pyprog -Bench     七檢 + 首發/後續耗時(拿數字說話,不是感覺變快)
# 律:零網路 · 不寫任何正本 · 只起 python -c 的小跑
param([switch]$Bench)
$ErrorActionPreference = "Continue"
$VIA = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $VIA "supportive modules"))) { $VIA = Split-Path -Parent $MyInvocation.MyCommand.Path; $VIA = Split-Path -Parent $VIA }
if (-not (Get-Command Get-VIAEnvPython -ErrorAction SilentlyContinue)) { function global:Get-VIAEnvPython([string]$f) { if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { "python" } } }
if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
    . (Join-Path $VIA "supportive modules\VIA_PS_Accel_Module.ps1")
    . (Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1")
}
$PY = Get-VIAEnvPython "core"
$script:fails = 0
function chk($n, $c, $note = "") {
    if ($c) { Write-Host "  [OK] $n $note" -ForegroundColor Green }
    else { Write-Host "  [FAIL] $n $note" -ForegroundColor Red; $script:fails++ }
}
Write-Host "=== 中央 py 啟動器(Invoke-VIAPython)· 七檢(零網路;只起 python -c 小跑)===" -ForegroundColor Cyan

$o = Invoke-VIAPython -Python $PY "-c" "print('A');print('B');print('C');print('D');print('E')"
chk "① 短跑 stdout **一行不少**地回到 pipeline(自適應輪詢最怕的就是提早收工吞掉尾巴)" (($o -join ',') -eq 'A,B,C,D,E') "(得 $($o.Count) 行:$($o -join ','))"
chk "② rc 0 照實回" ($global:LASTEXITCODE -eq 0) "(rc=$global:LASTEXITCODE)"

$o2 = Invoke-VIAPython -Python $PY "-c" "import time,sys`nfor i in range(6):`n    print('line%d'%i);sys.stdout.flush();time.sleep(0.15)"
chk "③ 長跑(~0.9s)邊跑邊轉播,結束時仍收齊 6 行(橫幅那條路也要收得乾淨)" ($o2.Count -eq 6) "(得 $($o2.Count) 行)"

Invoke-VIAPython -Python $PY "-c" "import sys;sys.exit(3)" | Out-Null
chk "④ 非零 rc 不吞(rc 被吞=下游把失敗當成功)" ($global:LASTEXITCODE -eq 3) "(rc=$global:LASTEXITCODE)"

$o4 = Invoke-VIAPython -Python $PY "-c" "import sys;print('OUT');print('ERR',file=sys.stderr)"
chk "⑤ stderr 走灰字、**不混進** stdout pipeline(混進去上游 ConvertFrom-Json 就炸)" (($o4 -join ',') -eq 'OUT') "(stdout 得:$($o4 -join ','))"

Invoke-VIAPython -Python $PY -TimeoutSec 1 "-c" "import time;time.sleep(30)" | Out-Null
chk "⑥ 逾時停得住 · rc 124 · 不卡斷(只殺自己生的樹)" ($global:LASTEXITCODE -eq 124) "(rc=$global:LASTEXITCODE)"

if ($Bench) {
    Write-Host "=== 耗時實測(python 側 -c pass 約 20ms;其餘都是包裝成本)===" -ForegroundColor Cyan
    $env:VIA_ACCEL_LIT = ""
    $sw = [Diagnostics.Stopwatch]::StartNew(); Invoke-VIAPython -Python $PY "-c" "pass" | Out-Null; $first = $sw.ElapsedMilliseconds
    $sw.Restart(); for ($i = 0; $i -lt 5; $i++) { Invoke-VIAPython -Python $PY "-c" "pass" | Out-Null }; $rest = [int]($sw.ElapsedMilliseconds / 5)
    Write-Host ("  首發(含點燈 25 格)= {0}ms   後續每道 = {1}ms" -f $first, $rest)
    Write-Host ("  批542 之前:首發 1137ms · 後續 279ms(同一棵樹、同一條快取路徑量的)") -ForegroundColor DarkGray
}
$o7 = Invoke-VIAPython -Python $PY "-c" "import sys,time`nfor i in range(1,5):`n    print('[進度] %d/4 步驟'%i);sys.stdout.flush();time.sleep(0.15)"
chk "⑦ 真百分比協定:引擎印 [進度] n/N → 啟動器算出 4/4=100%(沒報進度才脈動,pct=-1)" ($o7.Count -eq 4 -and $global:VIA_PYPROG_LAST.d -eq 4 -and $global:VIA_PYPROG_LAST.n -eq 4 -and $global:VIA_PYPROG_LAST.pct -eq 100) ("(n/d=" + $global:VIA_PYPROG_LAST.n + "/" + $global:VIA_PYPROG_LAST.d + " · pct=" + $global:VIA_PYPROG_LAST.pct + ")")
$o7b = Invoke-VIAPython -Python $PY "-c" "print('no progress here')"
chk "⑦b 沒報進度=脈動,不假裝(pct=-1)" ($global:VIA_PYPROG_LAST.pct -eq -1) ("(pct=" + $global:VIA_PYPROG_LAST.pct + ")")

Write-Host ("  [計] 七檢(8 項)OK {0} · FAIL {1}" -f (8 - $script:fails), $script:fails) -ForegroundColor $(if ($script:fails) { "Red" } else { "Green" })
exit $(if ($script:fails) { 1 } else { 0 })
