# VIA-Commands-Override-v0102.ps1(薄尾:骨架 / 加速器用的助手不蓋 — Test-VIAPageTarget · Test-VIABookFresh · Invoke-VIACeleritasScoped · Get-VIAPinnedDir · ConvertTo-VIACleanArgs;v0101 不動)· 操作員令 2026-10-08:「過去的快捷指令等全部覆蓋刪除取代避免錯誤」
# 作法(L108 只增不減 · L117 指令 PY 化 · L119 入口各自):Register-VIA-Commands 原檔不動;本檔在 $PROFILE 最後一行 dot-source,
# 把所有已載入的 via-* / Set-VIA* / Test-VIA* 等舊短令「覆蓋」成 DEPRECATED 殘樁(印去處,不執行),只留下面 4 個現行指令。
$script:VIA_Launcher = Join-Path $env:USERPROFILE 'Downloads\Invoke-VIA-Launch-v0111.ps1'
$latest = Get-ChildItem -LiteralPath (Join-Path $env:USERPROFILE 'Downloads') -Filter 'Invoke-VIA-Launch-v0*.ps1' -ErrorAction SilentlyContinue | Where-Object { $_.Name -notmatch '\(\d+\)' } | Sort-Object Name | Select-Object -Last 1
if ($latest) { $script:VIA_Launcher = $latest.FullName }

function Invoke-VIASub { param([string]$Sub, [string]$Verb, [string[]]$VerbArgs)
  $a = @('-ExecutionPolicy', 'Bypass', '-File', $script:VIA_Launcher, '-Sub', $Sub, '-Verb', $Verb); if ($VerbArgs -and $VerbArgs.Count) { $a += '-VerbArgs'; $a += $VerbArgs }
  & pwsh @a }
function via-vdf { param([string]$Verb = 'ui', [string[]]$VerbArgs = @()) Invoke-VIASub -Sub VDF -Verb $Verb -VerbArgs $VerbArgs }
function via-vrn { param([string]$Verb = 'ui', [string[]]$VerbArgs = @()) Invoke-VIASub -Sub VRN -Verb $Verb -VerbArgs $VerbArgs }
function via-vcgc { param([string]$Verb = 'ui', [string[]]$VerbArgs = @()) Invoke-VIASub -Sub VCGC -Verb $Verb -VerbArgs $VerbArgs }
function via-view { & pwsh -ExecutionPolicy Bypass -File $script:VIA_Launcher -Sub VIA }   # 母系統監控視圖(不是入口)
function via-help { Write-Host "VIA 現行指令(L119):`n  via-vdf [動詞] [參數]   VDF 自己的入口(預設 ui 開頁)`n  via-vrn [動詞] [參數]   VRN 自己的入口`n  via-vcgc [動詞]         VCGC 治理矩陣`n  via-view                三系統監控視圖`n其餘舊短令已覆蓋為 DEPRECATED 殘樁;原檔在 Register-VIA-Commands 未刪。" -ForegroundColor Cyan }

$keep = @('via-vdf', 'via-vrn', 'via-vcgc', 'via-view', 'via-help', 'Invoke-VIASub', 'Test-VIAPageTarget', 'Test-VIABookFresh', 'Invoke-VIACeleritasScoped', 'Get-VIAPinnedDir', 'ConvertTo-VIACleanArgs')   # 後五個是骨架 / 加速器助手,不是短令
$old = Get-Command -CommandType Function | Where-Object { ($_.Name -match '^(via-|via$|Set-VIA|Test-VIA|regen-all|selftest$)') -and ($keep -notcontains $_.Name) }
$n = 0
foreach ($c in $old) {
  $name = $c.Name
  $body = [scriptblock]::Create("Write-Host ('[DEPRECATED] ' + '$name' + ' 已覆蓋(2026-10-08 操作員令)。改用 via-vdf / via-vrn / via-vcgc / via-view;原定義在 Register-VIA-Commands 未刪。') -ForegroundColor Yellow; return 2")
  Set-Item -Path ("Function:\global:" + $name) -Value $body -Force
  $n++
}
Write-Host ("  [VIA] 短令覆蓋:留 4 個現行(via-vdf / via-vrn / via-vcgc / via-view)· " + $n + " 個舊短令改為 DEPRECATED 殘樁 · via-help 看清單 · 啟動器 " + (Split-Path $script:VIA_Launcher -Leaf)) -ForegroundColor DarkCyan
