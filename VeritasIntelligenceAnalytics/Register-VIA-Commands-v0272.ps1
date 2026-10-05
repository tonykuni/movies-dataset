# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R30)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0272.ps1 — 2026-10-05:所有短令整合成一個入口 via(VCGC-REQ169)
#   操作員令「integrate all short command into one」= L70 這一次的許可:只加這一件;v0271 以前一字不動。
#   L113 裁定:被點源的函式庫豁免骨架,仍帶兩章(L106)。
#   舊短令(via-xxx · via_xxx · 中文別名)全部照留照用;via 只是多一個總門:
#     via                      = 原行為(v0243 起的 VIA.ps1 總入口,一字不改地轉呼)
#     via <名> [參數…]          = 轉派到 via-<名>;via_<名> / via-<名> / 中文別名(例:via 總檢)都認
#     via <唯一前綴> [參數…]    = 前綴只對到一支就直接跑(先印 → 實際指令);對到多支只列不跑(rc 2)
#     via list [關鍵字]         = 全部短令一覽:名 · 別名 · 說明(取自定義處上方註解)· 來源檔;關鍵字比對名 / 別名 / 說明
#     via which <名>            = 只解析不執行:印出會跑哪一支 · 定義檔
#     via help                  = 照舊轉 via-help(CGC_MDL102 新舊指令整合冊)
#   找不到 = 印最接近的幾支(子字串 / 前綴),rc 2;不猜著跑。
#   不安裝、不寫冊、不觸網;轉派的那支自己的行為(含加速器 / 同意閘)完全不變。
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0271.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path

# 原本的 via(無參數 = VIA.ps1 總入口)先存起來;重複點源時不把自己存成「原本的」
if ((Test-Path function:\via) -and -not (Get-Variable -Name VIAUnifiedPrevVia -Scope Global -ErrorAction Ignore)) {
    $global:VIAUnifiedPrevVia = ${function:global:via}
}

function global:Get-VIAUnifiedRoster {
    # 全部短令:via-* 函式 / 腳本 / 執行檔 + 指向它們的別名;說明取自各 Register 檔定義處上方第一行註解(後檔蓋前檔 = 同尾版律)
    $desc = @{}
    $dir = if ($global:VIARegisterPath) { Split-Path -Parent $global:VIARegisterPath } else { $PSScriptRoot }
    foreach ($f in @(Get-ChildItem -Path $dir -Filter "Register-VIA-Commands-v*.ps1" -ErrorAction Ignore | Sort-Object Name)) {
        $lines = @(Get-Content -LiteralPath $f.FullName -Encoding UTF8 -ErrorAction Ignore)
        for ($i = 0; $i -lt $lines.Count; $i++) {
            if ($lines[$i] -match '^function\s+(global:)?(via-[A-Za-z0-9_-]+)') {
                $name = $Matches[2]; $j = $i - 1; $first = $null
                while ($j -ge 0 -and $lines[$j] -match '^\s*#') { $first = $lines[$j]; $j-- }
                if ($first) { $desc[$name] = (($first -replace '^\s*#+\s*', '') -replace '\s+', ' ').Trim() }
                elseif (-not $desc.ContainsKey($name)) {
                    # 上方沒註解:退取本檔第一行提到這個名的註解(檔頭「+via-xxx(…)」那種)
                    $hdr = $lines | Where-Object { $_ -match '^\s*#' -and $_ -match [regex]::Escape($name) } | Select-Object -First 1
                    if ($hdr) { $desc[$name] = (($hdr -replace '^\s*#+\s*', '') -replace '\s+', ' ').Trim() }
                }
            }
        }
    }
    $alias = @{}
    foreach ($a in @(Get-Alias -ErrorAction Ignore | Where-Object { $_.Definition -like 'via-*' })) {
        if (-not $alias.ContainsKey($a.Definition)) { $alias[$a.Definition] = @() }
        $alias[$a.Definition] += $a.Name
    }
    $seen = @{}
    foreach ($c in @(Get-Command -Name 'via-*' -CommandType Function, ExternalScript, Application -ErrorAction Ignore)) {
        $n = [IO.Path]::GetFileNameWithoutExtension($c.Name)
        if ($c.CommandType -eq 'Function') { $n = $c.Name }
        if ($seen.ContainsKey($n)) { continue }
        $seen[$n] = $true
        $src = if ($c.CommandType -eq 'Function' -and $c.ScriptBlock.File) { Split-Path -Leaf $c.ScriptBlock.File } elseif ($c.Source) { $c.Source } else { '' }
        [pscustomobject]@{
            Name    = $n
            Aliases = (@($alias[$c.Name]) | Where-Object { $_ } | Sort-Object) -join ' · '
            Desc    = if ($desc.ContainsKey($n)) { $desc[$n] } else { '' }
            Kind    = "$($c.CommandType)"
            Source  = $src
        }
    }
}

function global:Resolve-VIAUnified {
    # 名 → 實際指令。回 @{ Status = 'exact'|'alias'|'prefix'|'ambiguous'|'none'; Command; Candidates }
    param([string]$Name)
    $raw = "$Name".Trim()
    if (-not $raw) { return [pscustomobject]@{ Status = 'none'; Command = $null; Candidates = @() } }
    # ① 原字串就是別名(中文別名 · via_precheck 這類)且指向 via-*
    $al = Get-Alias -Name $raw -ErrorAction Ignore
    if ($al -and $al.Definition -like 'via-*') {
        return [pscustomobject]@{ Status = 'alias'; Command = $al.Definition; Candidates = @($al.Definition) }
    }
    # ② 正規化:去 via- / via_ 前綴,底線當連字號
    $core = ($raw -replace '^(?i)via[-_]', '') -replace '_', '-'
    $full = "via-$core"
    # 用萬用字元查:精確名查不到時不觸發 CommandNotFound 守門員(它會印一大段「漏登錄」說明)
    $hit = Get-Command -Name "$full*" -CommandType Function, Alias, ExternalScript, Application -ErrorAction Ignore |
        Where-Object { $_.Name -eq $full -or [IO.Path]::GetFileNameWithoutExtension($_.Name) -eq $full } | Select-Object -First 1
    if ($hit) {
        $cmd = if ($hit.CommandType -eq 'Alias') { $hit.Definition } else { $hit.Name }
        return [pscustomobject]@{ Status = 'exact'; Command = $cmd; Candidates = @($cmd) }
    }
    # ③ 唯一前綴
    $names = @(Get-VIAUnifiedRoster | ForEach-Object { $_.Name })
    $pre = @($names | Where-Object { $_ -like "$full*" } | Sort-Object -Unique)
    if ($pre.Count -eq 1) { return [pscustomobject]@{ Status = 'prefix'; Command = $pre[0]; Candidates = $pre } }
    if ($pre.Count -gt 1) { return [pscustomobject]@{ Status = 'ambiguous'; Command = $null; Candidates = $pre } }
    # ④ 都沒有:子字串建議(不跑)
    $sub = @($names | Where-Object { $_ -like "*$core*" } | Sort-Object -Unique | Select-Object -First 12)
    return [pscustomobject]@{ Status = 'none'; Command = $null; Candidates = $sub }
}

function global:via {
    if ($args.Count -eq 0) {
        if ($global:VIAUnifiedPrevVia) { & $global:VIAUnifiedPrevVia; return }
        Write-Host "  [via] 用法:via <短令> [參數…] · via list [關鍵字] · via which <短令> · via help" -ForegroundColor Cyan
        return
    }
    $head = "$($args[0])"
    $rest = @(if ($args.Count -gt 1) { $args[1..($args.Count - 1)] })
    switch -Regex ($head) {
        '^(list|ls|\?)$' {
            $kw = ($rest -join ' ').Trim()
            $rows = @(Get-VIAUnifiedRoster | Sort-Object Name)
            if ($kw) { $rows = @($rows | Where-Object { $_.Name -like "*$kw*" -or $_.Aliases -like "*$kw*" -or $_.Desc -like "*$kw*" }) }
            foreach ($r in $rows) {
                $d = if ($r.Desc.Length -gt 90) { $r.Desc.Substring(0, 90) + '…' } else { $r.Desc }
                $a = if ($r.Aliases) { " (" + $r.Aliases + ")" } else { '' }
                Write-Host ("  {0,-26}{1}" -f $r.Name, $a) -ForegroundColor Green
                if ($d) { Write-Host ("      " + $d) -ForegroundColor Gray }
            }
            Write-Host ("  [via list] " + $rows.Count + " 支" + $(if ($kw) { " · 關鍵字 「" + $kw + "」" } else { "" }) + " · 用法:via <名> [參數…]") -ForegroundColor Cyan
            $global:LASTEXITCODE = 0
            return
        }
        '^which$' {
            $r = Resolve-VIAUnified ($rest -join ' ')
            if ($r.Command) {
                $c = Get-Command -Name $r.Command -ErrorAction Ignore | Select-Object -First 1
                $file = if ($c -and $c.CommandType -eq 'Function' -and $c.ScriptBlock.File) { $c.ScriptBlock.File } elseif ($c) { $c.Source } else { '' }
                Write-Host ("  [via which] " + $r.Status + " → " + $r.Command + $(if ($file) { " · " + $file } else { "" })) -ForegroundColor Green
                $global:LASTEXITCODE = 0
            } else {
                Write-Host ("  [via which] " + $r.Status + " · 候選:" + (($r.Candidates) -join ' · ')) -ForegroundColor Yellow
                $global:LASTEXITCODE = 2
            }
            return
        }
    }
    $r = Resolve-VIAUnified $head
    if (-not $r.Command) {
        if ($r.Status -eq 'ambiguous') {
            Write-Host ("  [via] 「" + $head + "」對到多支,不猜:" + (($r.Candidates) -join ' · ')) -ForegroundColor Yellow
        } else {
            Write-Host ("  [via] 找不到「" + $head + "」" + $(if ($r.Candidates) { ";接近的:" + (($r.Candidates) -join ' · ') } else { ";via list 看全部" })) -ForegroundColor Yellow
        }
        $global:LASTEXITCODE = 2
        return
    }
    if ($r.Status -eq 'prefix') { Write-Host ("  [via] → " + $r.Command) -ForegroundColor DarkCyan }
    & $r.Command @rest
}
Set-Alias -Name 總門 -Value via -Scope Global -Force
