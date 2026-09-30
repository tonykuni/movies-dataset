# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# =====================================================================================
# Invoke-VIA-PSTemplateJoin-v0100.ps1 — 既有債 .ps1 批次接模板章(L103 ③ · 剖析器驗證 · 不包裹接法)
#   操作員 2026-09-28:「加速器導入所有 py 檔 ps 檔 · 覆蓋率要達 100%」+「授權進行一切 · 邊測邊完善 · 成功即鎖」。
#   以 PowerShell 自己的剖析器(System.Management.Automation.Language.Parser)定位,不靠正規式猜:
#     · 章插在 param() / using 之後(param 必須是第一個敘述,插在前面會壞);沒有 param 就插在第一個敘述前(開頭的說明註解與 #Requires 保持在上)
#     · 章不加 #Requires 7:PS 5.1 照跑不擋,章內只有 PS7 才點源模板
#     · 只有「自己點源到模板」的那一支才 Start / Restore($VIACelTplOwn):被已加速的呼叫端叫到時不重複加速、不提早還原呼叫端
#     · exit 前補還原:只補「直接敘述」的 exit(父節點是敘述區塊);管線鏈裡的 exit 不動,交給結尾與 PowerShell.Exiting
#     · 函式庫(只有函式定義 / 指派 / Set-Alias 之類;或 Register-* / *_Module.ps1)只蓋章不執行:它被點源進呼叫端,由呼叫端的模板接管
#   不碰:intake / references 正本 · 封存/備份副本(BACKUP · _superseded · SCOPE_COPY · ARCHIVE)· 雜湊被登錄的(manifest / 冊裡有它的 sha256·md5,改了就對不上)· 旁有 .freeze.lock.json ·
#         非 UTF-8 / UTF-16 · 原檔就剖析不過 · 具名 begin/process/end 區塊 · param 與模板同名(RestoreOnly/Report/Body)
#   驗證(每支):接後再剖析 0 錯 · param 區塊原文不變 · using 不變 · 函式名單不變 · exit 數不變 · 章在;任何一項不過 = 不寫。
#   寫檔保留 BOM 與換行;章全是 ASCII(無 BOM 的檔在 PS 5.1 也不會被多位元組吃掉換行)。
# 用法(站在 VeritasIntelligenceAnalytics):
#   .\Invoke-VIA-PSTemplateJoin-v0100.ps1                 # 乾跑:只出計畫與矩陣(預設)
#   .\Invoke-VIA-PSTemplateJoin-v0100.ps1 -Apply          # 照計畫寫(只寫驗證全過的);寫前備份到 VIA_Reports\psjoin\restore\<時間>
#   .\Invoke-VIA-PSTemplateJoin-v0100.ps1 -SelfTest       # 沙盒實跑:param/switch 保留 · exit 碼保留 · 函式庫不執行 · PS5 路徑不動
# 結束碼:0 = 完成 · 1 = 自測失敗 · 3 = 流程閘沒過(PSGATE-1)
# =====================================================================================
[CmdletBinding()]
param(
    [switch]$Apply,
    [switch]$SelfTest,
    [switch]$NoFlowGate,
    [string[]]$Files
)
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

$ErrorActionPreference = "Stop"
$VIA = $PSScriptRoot
$Repo = Split-Path $VIA -Parent
$script:TplPath = Join-Path $VIA "supportive modules\ps7\VeritasCeleritas.PS7.ps1"
$script:HasCel = $false
try {
    if (Test-Path -LiteralPath $script:TplPath) { . $script:TplPath; $script:HasCel = $true }
} catch { $script:HasCel = $false }
Set-StrictMode -Off
$ErrorActionPreference = "Stop"

$script:Marker = "CELERITAS-TEMPLATE-" + "JOIN"
$script:Conflict = @("RestoreOnly", "Report", "Body")
$script:LibCmds = @("Set-Alias", "New-Alias", "Export-ModuleMember", "Set-StrictMode", "Add-Type", "Import-Module", "Update-TypeData", "Update-FormatData")

function Get-JoinHead {
    param([string]$Mode, [string]$NL)
    if ($Mode -eq "lib") {
        $t = @(
            ("# " + $script:Marker + " v1 (library: dot-sourced by its caller, the caller's template covers it; batch R16-9)"),
            "# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session ====="
        )
        return ($t -join $NL) + $NL
    }
    $t = @(
        ("# " + $script:Marker + " v1 (no-wrap join, L103-3; batch R16-9; PS 5.1 runs unchanged, only PS7 loads the template)"),
        "# ===== [VIA:PS-TEMPLATE:v0101] Celeritas PS7 template: this process only, restore on exit, skip when absent, param() untouched =====",
        '$VIACelTplOwn = $false',
        'if ($PSVersionTable.PSVersion.Major -ge 7) {',
        '    try {',
        '        $VIACelTplFile = $null',
        '        $VIACelTplProbe = $PSScriptRoot',
        '        while ($VIACelTplProbe) {',
        '            $VIACelTplTry = Join-Path $VIACelTplProbe ''supportive modules\ps7\VeritasCeleritas.PS7.ps1''',
        '            if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry; break }',
        '            $VIACelTplUp = Split-Path $VIACelTplProbe -Parent',
        '            if ((-not $VIACelTplUp) -or ($VIACelTplUp -eq $VIACelTplProbe)) { break }',
        '            $VIACelTplProbe = $VIACelTplUp',
        '        }',
        '        if ($VIACelTplFile -and (-not (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore))) {',
        '            $VIACelTplKeep = @{}',
        '            foreach ($VIACelTplName in ''RestoreOnly'', ''Report'', ''Body'') {',
        '                $VIACelTplVar = Get-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore',
        '                if ($VIACelTplVar) { $VIACelTplKeep[$VIACelTplName] = $VIACelTplVar.Value }',
        '            }',
        '            try { $null = . $VIACelTplFile -RestoreOnly }',
        '            finally {',
        '                Set-StrictMode -Off',
        '                foreach ($VIACelTplName in ''RestoreOnly'', ''Report'', ''Body'') {',
        '                    Remove-Variable -Name $VIACelTplName -Scope 0 -Force -ErrorAction Ignore',
        '                    if ($VIACelTplKeep.ContainsKey($VIACelTplName)) { Set-Variable -Name $VIACelTplName -Value $VIACelTplKeep[$VIACelTplName] -Scope 0 }',
        '                }',
        '            }',
        '            if (Get-Command Start-CeleritasPS7 -ErrorAction Ignore) {',
        '                if (-not (Get-EventSubscriber -Force -ErrorAction Ignore | Where-Object { $_.SourceIdentifier -eq ''PowerShell.Exiting'' })) {',
        '                    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action { try { Restore-CeleritasPS7 } catch { } }',
        '                }',
        '                [void](Start-CeleritasPS7)',
        '                $VIACelTplOwn = $true',
        '            }',
        '        }',
        '    } catch { }',
        '}',
        "# ===== [VIA:PS-TEMPLATE:END] ====="
    )
    return ($t -join $NL) + $NL
}

$script:RestoreInline = 'if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }; '
$script:RestoreLine = 'if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit'

function Test-LibScript {
    param($Ast, [string]$Name)
    if ($Name -match '^Register-VIA-Commands' -or $Name -match '(_Module|\.Module|Profile|\.Template)\.ps1$') { return $true }
    if ($Ast.ParamBlock) { return $false }
    $stmts = @($Ast.EndBlock.Statements)
    if ($stmts.Count -eq 0) { return $false }
    $fn = 0
    foreach ($s in $stmts) {
        if ($s -is [System.Management.Automation.Language.FunctionDefinitionAst]) { $fn++; continue }
        if ($s -is [System.Management.Automation.Language.AssignmentStatementAst]) { continue }
        if ($s -is [System.Management.Automation.Language.TypeDefinitionAst]) { continue }
        if ($s -is [System.Management.Automation.Language.PipelineAst] -and $s.PipelineElements.Count -eq 1 -and
            $s.PipelineElements[0] -is [System.Management.Automation.Language.CommandAst]) {
            $cn = $s.PipelineElements[0].GetCommandName()
            if ($cn -and ($script:LibCmds -contains $cn)) { continue }
        }
        return $false
    }
    return ($fn -gt 0)
}

function Get-Shape {
    param($Ast)
    $fns = @($Ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true) | ForEach-Object { $_.Name }) | Sort-Object
    $exits = @($Ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.ExitStatementAst] }, $true)).Count
    return [ordered]@{
        param = $(if ($Ast.ParamBlock) { $Ast.ParamBlock.Extent.Text } else { "" })
        using = (@($Ast.UsingStatements | ForEach-Object { $_.Extent.Text }) -join "|")
        fns   = ($fns -join ",")
        exits = $exits
    }
}

function Join-OneScript {
    # 回 [ordered]@{ path; action(join/skip); mode; why; exits; text; bom }
    param([string]$Full, [string]$Rel, [hashtable]$Pinned)
    $r = [ordered]@{ path = $Rel; action = "skip"; mode = ""; why = ""; exits = 0; text = $null; bom = $false }
    if ($Rel -match '(^|/)(intake|references)/') { $r.why = "intake/references 正本(一個位元不動)"; return $r }
    if ($Rel -match '(?i)(^|/)(BACKUP|_superseded|SCOPE_COPY)/|ARCHIVE') { $r.why = "封存 / 備份副本(保持原樣)"; return $r }
    if ($Pinned.ContainsKey($Rel)) { $r.why = "雜湊被登錄:" + $Pinned[$Rel]; return $r }
    if (Test-Path -LiteralPath ($Full + ".freeze.lock.json")) { $r.why = "凍結鎖在旁"; return $r }
    $bytes = [IO.File]::ReadAllBytes($Full)
    if ($bytes.Length -ge 2 -and (($bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) -or ($bytes[0] -eq 0xFE -and $bytes[1] -eq 0xFF))) { $r.why = "UTF-16"; return $r }
    $bom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
    $r.bom = $bom
    try {
        $enc = [Text.UTF8Encoding]::new($false, $true)
        $text = if ($bom) { $enc.GetString($bytes, 3, $bytes.Length - 3) } else { $enc.GetString($bytes) }
    } catch { $r.why = "不是 UTF-8"; return $r }
    if ($text.Contains($script:Marker)) { $r.why = "已接"; return $r }
    $nl = if ($text.Contains("`r`n")) { "`r`n" } else { "`n" }
    $tok = $null; $err = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseInput($text, [ref]$tok, [ref]$err)
    if ($err.Count -gt 0) { $r.why = "原檔剖析不過(" + $err[0].Message + ")"; return $r }
    if ($ast.BeginBlock -or $ast.ProcessBlock -or $ast.DynamicParamBlock -or ($ast.EndBlock -and -not $ast.EndBlock.Unnamed)) { $r.why = "具名 begin/process/end 區塊"; return $r }
    if ($ast.ParamBlock) {
        $names = @($ast.ParamBlock.Parameters | ForEach-Object { $_.Name.VariablePath.UserPath })
        $clash = @($names | Where-Object { $script:Conflict -contains $_ })
        if ($clash.Count -gt 0) { $r.why = "param 與模板同名:" + ($clash -join ","); return $r }
    }
    $leaf = Split-Path $Full -Leaf
    $mode = if (Test-LibScript $ast $leaf) { "lib" } else { "run" }
    # 說明裡教人點源自己(. .\X.ps1)= 設計成被點源進使用者視窗 → 當函式庫,只蓋章不動呼叫端
    if ($mode -eq "run" -and $text -match ('(?m)(^|[\s;{(])\.\s+[^\r\n]*' + [regex]::Escape($leaf))) { $mode = "lib" }
    $r.mode = $mode
    $head = Get-JoinHead $mode $nl
    # 插入點
    if ($ast.ParamBlock -or @($ast.UsingStatements).Count -gt 0) {
        $end = 0
        if ($ast.ParamBlock) { $end = $ast.ParamBlock.Extent.EndOffset }
        foreach ($u in @($ast.UsingStatements)) { if ($u.Extent.EndOffset -gt $end) { $end = $u.Extent.EndOffset } }
        $at = $end
        $ins = $nl + $head
    } else {
        $first = @($tok | Where-Object { $_.Kind -notin @('Comment', 'NewLine', 'LineContinuation', 'EndOfInput') } | Select-Object -First 1)
        if ($first.Count -eq 0) { $r.why = "空檔(沒有敘述)"; return $r }
        $at = $first[0].Extent.StartOffset
        $ins = $head
    }
    $edits = [System.Collections.Generic.List[object]]::new()
    $edits.Add(@($at, $ins))
    if ($mode -eq "run") {
        $exits = @($ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.ExitStatementAst] }, $true) | Where-Object {
            $_.Parent -is [System.Management.Automation.Language.StatementBlockAst] -or $_.Parent -is [System.Management.Automation.Language.NamedBlockAst] })
        foreach ($x in $exits) {
            if ($x.Extent.StartOffset -lt $at) { continue }
            $edits.Add(@($x.Extent.StartOffset, $script:RestoreInline))
        }
        $r.exits = $exits.Count
    }
    $new = $text
    foreach ($e in @($edits | Sort-Object { $_[0] } -Descending)) { $new = $new.Insert([int]$e[0], [string]$e[1]) }
    if ($mode -eq "run") {
        if (-not $new.EndsWith("`n")) { $new += $nl }
        $new += $script:RestoreLine + $nl
    }
    # 驗證
    $tok2 = $null; $err2 = $null
    $ast2 = [System.Management.Automation.Language.Parser]::ParseInput($new, [ref]$tok2, [ref]$err2)
    if ($err2.Count -gt 0) { $r.why = "接後剖析不過(" + $err2[0].Message + ")→ 不寫"; return $r }
    $a = Get-Shape $ast; $b = Get-Shape $ast2
    foreach ($k in @("param", "using", "fns", "exits")) {
        if ("" + $a[$k] -ne "" + $b[$k]) { $r.why = "接後形狀變了(" + $k + ")→ 不寫"; return $r }
    }
    if (-not $new.Contains($script:Marker)) { $r.why = "章沒寫進去 → 不寫"; return $r }
    # 章要是真的程式,不是一整行註解(逗號比 + 先結合的教訓):run 模式頂層要多出「Own 指派 + if」兩句與結尾還原一句
    $n1 = @($ast.EndBlock.Statements).Count; $n2 = @($ast2.EndBlock.Statements).Count
    $want = if ($mode -eq "run") { $n1 + 3 + @($ast.EndBlock.Statements | Where-Object { $_ -is [System.Management.Automation.Language.ExitStatementAst] }).Count } else { $n1 }
    $own = @($ast2.EndBlock.Statements | Where-Object { $_ -is [System.Management.Automation.Language.AssignmentStatementAst] -and $_.Left.Extent.Text -eq '$VIACelTplOwn' }).Count
    if ($n2 -ne $want -or (($mode -eq "run") -and $own -ne 1)) { $r.why = "章的敘述數不對(" + $n1 + "→" + $n2 + ",應 " + $want + ")→ 不寫"; return $r }
    $r.action = "join"
    $r.text = $new
    return $r
}

function Get-PinnedMap {
    # 冊 / manifest 裡登錄了這支檔的 sha256(全長或 12/16 碼前綴)或 md5 → 不碰
    param([string[]]$Rels)
    $map = @{}
    $pat = @{}
    foreach ($rel in $Rels) {
        $full = Join-Path $VIA $rel
        if (-not (Test-Path -LiteralPath $full)) { continue }
        $h = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant()
        $m = (Get-FileHash -LiteralPath $full -Algorithm MD5).Hash.ToLowerInvariant()
        foreach ($p in @($h, $h.Substring(0, 16), $h.Substring(0, 12), $m)) { if (-not $pat.ContainsKey($p)) { $pat[$p] = [System.Collections.Generic.List[string]]::new() }; $pat[$p].Add($rel) }
    }
    if ($pat.Count -eq 0) { return $map }
    $pf = Join-Path ([IO.Path]::GetTempPath()) ("via_psjoin_pat_" + $PID + ".txt")
    [IO.File]::WriteAllLines($pf, [string[]]@($pat.Keys))
    try {
        $hits = @(git -C $VIA grep -l -i -F -f $pf -- . 2>$null | Where-Object { $_ })
        $rx = [regex]::new('[0-9a-fA-F]{12,64}')
        foreach ($hf in $hits) {
            $t = [IO.File]::ReadAllText((Join-Path $VIA $hf))
            foreach ($mt in $rx.Matches($t)) {
                $tl = $mt.Value.ToLowerInvariant()
                foreach ($L in @(64, 32, 16, 12)) {
                    if ($tl.Length -ge $L -and $pat.ContainsKey($tl.Substring(0, $L))) {
                        foreach ($rel in $pat[$tl.Substring(0, $L)]) { if (-not $map.ContainsKey($rel)) { $map[$rel] = $hf } }
                    }
                }
            }
        }
    } finally { Remove-Item -LiteralPath $pf -ErrorAction Ignore }
    return $map
}

function Write-JoinMatrix {
    param($Rows, [string]$Title)
    Write-Host ""
    Write-Host ("  ━━ " + $Title + " ━━") -ForegroundColor Cyan
    $g = $Rows | Group-Object { if ($_.action -eq "join") { "接(" + $_.mode + ")" } else { "略過:" + (($_.why -split '[(::]')[0]) } } | Sort-Object Count -Descending
    foreach ($x in $g) { Write-Host ("  {0,-44} {1,5}" -f $x.Name, $x.Count) -ForegroundColor $(if ($x.Name -like "接*") { "Green" } else { "DarkYellow" }) }
}

# ---------------------------------------------------------------- 自測(沙盒實跑)
function Invoke-JoinSelfTest {
    $ok = 0; $bad = 0
    function chk([string]$name, [bool]$cond, [string]$note = "") {
        if ($cond) { $script:stOK++ ; Write-Host ("  [OK] " + $name + $(if ($note) { " · " + $note })) -ForegroundColor Green }
        else { $script:stBad++; Write-Host ("  [FAIL] " + $name + $(if ($note) { " · " + $note })) -ForegroundColor Red }
    }
    $script:stOK = 0; $script:stBad = 0
    $box = Join-Path ([IO.Path]::GetTempPath()) ("via_psjoin_st_" + $PID)
    $ps7 = Join-Path $box "supportive modules\ps7"
    New-Item -ItemType Directory -Force -Path $ps7 | Out-Null
    try {
        Copy-Item -LiteralPath $script:TplPath -Destination (Join-Path $ps7 "VeritasCeleritas.PS7.ps1")
        $cases = [ordered]@{
            "run_param.ps1" = "<# help #>`n[CmdletBinding()]`nparam([switch]`$Loud, [int]`$N = 3)`n`$ErrorActionPreference = 'Stop'`nif (`$N -eq 9) { exit 9 }`nWrite-Output ('loud=' + [bool]`$Loud + ' n=' + `$N + ' own=' + `$VIACelTplOwn + ' pri=' + (Get-Process -Id `$PID).PriorityClass)`nexit 4`n"
            "run_plain.ps1" = "#Requires -Version 5.1`n# top comment`nWrite-Output 'plain'`n"
            "lib_funcs.ps1" = "function Get-A { 'a' }`nSet-Alias ga Get-A`n"
            "chain_exit.ps1" = "Write-Output 'x' || exit 5`nif (`$true) { `$v = `$(if (`$false) { exit 7 }; 1) }`nexit 6`n"
            "named.ps1"     = "param(`$a)`nbegin { 1 }`nprocess { 2 }`n"
            "clash.ps1"     = "param([switch]`$Report)`n`$Report`n"
            "broken.ps1"    = "if ( {`n"
        }
        foreach ($k in $cases.Keys) { [IO.File]::WriteAllText((Join-Path $box $k), $cases[$k], [Text.UTF8Encoding]::new($false)) }
        $res = @{}
        foreach ($k in $cases.Keys) {
            $res[$k] = Join-OneScript (Join-Path $box $k) $k @{}
            if ($res[$k].action -eq "join") { [IO.File]::WriteAllText((Join-Path $box $k), $res[$k].text, [Text.UTF8Encoding]::new($false)) }
        }
        chk "① run 腳本接上且 param 原文不動" ($res["run_param.ps1"].action -eq "join" -and $res["run_param.ps1"].mode -eq "run")
        $out = @(& pwsh -NoProfile -File (Join-Path $box "run_param.ps1") -Loud -N 5 2>&1 | ForEach-Object { "" + $_ })
        $rc = $LASTEXITCODE
        chk "② 實跑:switch / int 參數原樣綁定 · exit 碼保留 · 自己點源才 own" (($out -join " ") -match 'loud=True n=5 own=True' -and $rc -eq 4) (($out -join " ") + " rc=" + $rc)
        $null = & pwsh -NoProfile -File (Join-Path $box "run_param.ps1") -N 9 2>&1
        chk "③ 早退 exit 9 前補還原,碼仍是 9" ($LASTEXITCODE -eq 9) ("rc=" + $LASTEXITCODE)
        $pri = (Get-Process -Id $PID).PriorityClass
        $out2 = @(& pwsh -NoProfile -File (Join-Path $box "run_plain.ps1") 2>&1 | ForEach-Object { "" + $_ })
        $t2 = [IO.File]::ReadAllText((Join-Path $box "run_plain.ps1"))
        chk "④ 沒 param:章在開頭註解與 #Requires 之後,照跑" (($out2 -join "") -eq "plain" -and $t2.IndexOf("#Requires -Version 5.1") -lt $t2.IndexOf($script:Marker)) ($out2 -join "|")
        $t3 = [IO.File]::ReadAllText((Join-Path $box "lib_funcs.ps1"))
        chk "⑤ 函式庫只蓋章,沒有可執行的章" ($res["lib_funcs.ps1"].mode -eq "lib" -and $t3 -notmatch 'Start-CeleritasPS7')
        $libCmd = ". '" + (Join-Path $box "lib_funcs.ps1") + "'; Get-A"
        $out5 = @(& pwsh -NoProfile -Command $libCmd 2>&1 | ForEach-Object { "" + $_ })
        chk "⑥ 函式庫點源後函式照用" (($out5 -join "") -eq "a") ($out5 -join "|")
        $null = & pwsh -NoProfile -File (Join-Path $box "chain_exit.ps1") 2>&1
        chk "⑦ 管線鏈裡的 exit 不動,直接敘述的 exit 補還原(碼 6 照舊)" ($res["chain_exit.ps1"].action -eq "join" -and $LASTEXITCODE -eq 6) ("rc=" + $LASTEXITCODE + " exits=" + $res["chain_exit.ps1"].exits)
        chk "⑧ 具名區塊 / param 同名 / 原檔壞 → 略過不寫" ($res["named.ps1"].action -eq "skip" -and $res["clash.ps1"].action -eq "skip" -and $res["broken.ps1"].action -eq "skip") (($res["named.ps1"].why, $res["clash.ps1"].why, $res["broken.ps1"].why) -join " | ")
        $again = Join-OneScript (Join-Path $box "run_param.ps1") "run_param.ps1" @{}
        chk "⑨ 冪等:已接的再跑一次 = 已接略過" ($again.action -eq "skip" -and $again.why -eq "已接")
        $pin = Join-OneScript (Join-Path $box "run_plain.ps1") "x/intake/y.ps1" @{}
        chk "⑩ intake 路徑一律不碰" ($pin.action -eq "skip")
        $nest = ". '" + (Join-Path $ps7 "VeritasCeleritas.PS7.ps1") + "'; & '" + (Join-Path $box "run_param.ps1") + "' -N 5; 'after=' + (Get-Process -Id `$PID).PriorityClass"
        $out6 = @(& pwsh -NoProfile -Command $nest 2>&1 | ForEach-Object { "" + $_ })
        chk "⑫ 巢狀:呼叫端已加速 → 子腳本不重複 Start、不提早還原呼叫端" ((($out6 -join " ") -match 'own=False') -and (($out6 -join " ") -match 'after=AboveNormal')) ($out6 -join " | ")
        chk "⑪ 自測不改本行程優先權" ((Get-Process -Id $PID).PriorityClass -eq $pri)
    } finally {
        Remove-Item -LiteralPath $box -Recurse -Force -ErrorAction Ignore
    }
    Write-Host ("  [計] PSTemplateJoin 自測 OK " + $script:stOK + " · FAIL " + $script:stBad) -ForegroundColor $(if ($script:stBad -eq 0) { "Green" } else { "Red" })
    return $script:stBad
}

try {
    if ($SelfTest) {
        $bad = Invoke-JoinSelfTest
        if ($bad -gt 0) { exit 1 }
        exit 0
    }
    # 流程閘(PSGATE-1):先從 VCGC 讀流程
    if (-not $NoFlowGate) {
        if (-not (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue)) {
            $pyMod = Join-Path $VIA "supportive modules\VIA_PS_PyProgress_Module.ps1"
            if (Test-Path -LiteralPath $pyMod) { . $pyMod }
        }
        $env:VIA_FROM_VCGC = "YES"
        $console = Get-ChildItem -LiteralPath (Join-Path $VIA "supportive modules\registry") -Filter "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py" -File | Sort-Object Name | Select-Object -Last 1
        $st = if (Get-Command Invoke-VIAPython -ErrorAction SilentlyContinue) { @(Invoke-VIAPython -Family 'vrn' $console.FullName 'status' 2>&1 | ForEach-Object { "" + $_ }) } else { @() }
        $flow = @($st | Where-Object { $_ -match '\[流程\]\s*政策過' } | Select-Object -First 1)
        if ($flow.Count -eq 0) { Write-Host "  [流程閘] 沒讀到「[流程] 政策過」→ 依 PSGATE-1 停" -ForegroundColor Red; exit 3 }
        Write-Host ("  [流程閘] 過:" + $flow[0].Trim()) -ForegroundColor Green
    }
    # 候選:閘的基線既有債(沒給 -Files 時)
    if (-not $Files) {
        $base = Get-Content -LiteralPath (Join-Path $VIA "supportive modules\registry\VIA_CeleritasPolicy_Baseline_v0100.json") -Raw -Encoding utf8 | ConvertFrom-Json
        $Files = @($base.ps1_debt.files)
    }
    $cand = @($Files | Where-Object { Test-Path -LiteralPath (Join-Path $VIA $_) })
    Write-Host ("  [候選] " + $cand.Count + " 支(閘基線既有債)· 查雜湊登錄中…") -ForegroundColor Cyan
    $pinned = Get-PinnedMap $cand
    Write-Host ("  [雜湊] 被冊 / manifest 登錄 " + $pinned.Count + " 支 → 不碰") -ForegroundColor DarkYellow
    $rows = [System.Collections.Generic.List[object]]::new()
    foreach ($rel in $cand) { $rows.Add((Join-OneScript (Join-Path $VIA $rel) $rel $pinned)) }
    $out = Join-Path $VIA "VIA_Reports\psjoin"
    New-Item -ItemType Directory -Force -Path $out | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $written = 0
    if ($Apply) {
        $bak = Join-Path $out ("restore\" + $stamp)
        foreach ($r in $rows) {
            if ($r.action -ne "join") { continue }
            $full = Join-Path $VIA $r.path
            $dst = Join-Path $bak $r.path
            New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
            Copy-Item -LiteralPath $full -Destination $dst
            $enc = [Text.UTF8Encoding]::new([bool]$r.bom)
            [IO.File]::WriteAllText($full, $r.text, $enc)
            $written++
        }
    }
    $slim = @($rows | ForEach-Object { [ordered]@{ path = $_.path; action = $_.action; mode = $_.mode; why = $_.why; exits = $_.exits } })
    $sum = [ordered]@{ schema = "VIA.PSJoin.v1"; ts = (Get-Date -Format "yyyy-MM-dd HH:mm:ss"); apply = [bool]$Apply; candidates = $cand.Count
                       join = @($rows | Where-Object { $_.action -eq "join" }).Count; written = $written; pinned = $pinned; rows = $slim }
    [IO.File]::WriteAllText((Join-Path $out "PSJOIN_latest.json"), ($sum | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))
    Write-JoinMatrix $rows ("既有債 .ps1 模板章 · " + $(if ($Apply) { "已寫 " + $written } else { "乾跑(加 -Apply 才寫)" }))
    Write-Host ("  [結果] " + (Join-Path $out "PSJOIN_latest.json")) -ForegroundColor DarkCyan
    if ($Apply) { Write-Host ("  [備份] " + (Join-Path $out ("restore\" + $stamp)) + "(救回:把這夾的檔案複製回原位)") -ForegroundColor DarkCyan }
} finally {
    if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) { try { Restore-CeleritasPS7 } catch { } }
}
exit 0
