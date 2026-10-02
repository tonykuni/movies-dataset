# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by VeritasCeleritas.PS7.Template.ps1; the template's contract covers it)
#Requires -Version 7.0
# =============================================================================
#  VeritasCeleritas.PS7.UI.ps1  v0100 — 標準 PS 模板的主控台呈現件(YFinance 啟動器版型)
#  操作員 2026-10-02(VCGC-REQ124):「PS U/I 的呈現方式將 YFINANCE 啟動器 PS 模板拿來,U/I 優化效果很好」
#  「檢視短指令 PS 指令中有無單獨啟動 YFINANCE 的指令 他 PS U/I 呈現很美 可採用加入標準 PS 模板」。
#  查證:短令冊(Register 鏈)沒有單獨啟動 YFinance 的指令;那個版面是 VDF_MDL002_YFinanceFetchingEngine
#  (intake VIA_VDF_Engines_b716)在 PowerShell 視窗裡用 Python Rich 印的:
#    藍框標題 Panel → 一條青色分節線 → 每節一張圓角表(洋紅表頭 · 青 / 綠 / 黃三欄色 · 數字靠右 · 燈置中)
#    → 青框「整體狀態」Panel.fit → 灰色尾線。
#  這裡用純 PowerShell 7 重做同一個版型(不靠 Python / Rich / 任何外掛模組);只 Write-Host,只動本行程,不改系統檔。
#  計數 · 判決 · JSON 一律交給既有 Write-CeleritasMatrixSummary(同一把尺,不另寫一份)。
#  環境:VIA_PS_UI_ASCII=1 改用 + - | 框與 [OK] 字樣燈(舊主控台 / 記錄檔);VIA_PS_UI_WIDTH=N 固定總寬。
#  函式:Write-CeleritasRule · Write-CeleritasPanel · Write-CeleritasTable · Write-CeleritasRichMatrix · Test-CeleritasUI
#  例:
#    Write-CeleritasRichMatrix -Title 'VDF 單引擎' -Header @('引擎 : VDF_ENG229', '模式 : status') -Rows @(
#        @{ id = '①'; title = '啟動前閘'; state = 'GREEN'; sec = 0.4; note = '加速器 · 網路橋都在' },
#        @{ id = '②'; title = '經 VCGC 啟動'; state = 'rc=1'; sec = 3.2; note = '看引擎日誌' })
# =============================================================================

$script:CeleritasUI = [ordered]@{ Version = 'v0100'; Source = 'VDF_MDL002_YFinanceFetchingEngine (Rich 版型)' }

# 欄位讀取 · 燈分類 · 計數判決都用模板本體的函式(同一把尺);單獨點源本檔時先接本體(= 接模板,L102)。
if (-not (Get-Command Write-CeleritasMatrixSummary -ErrorAction SilentlyContinue)) {
    $celeritasUIBody = Join-Path $PSScriptRoot 'VeritasCeleritas.PS7.ps1'
    if (Test-Path -LiteralPath $celeritasUIBody) { . $celeritasUIBody }
    Remove-Variable -Name celeritasUIBody -ErrorAction Ignore
}

$script:CeleritasUIWideBmp = [System.Collections.Generic.HashSet[int]]::new()
foreach ($celeritasUIRange in @(
        @(0x231A, 0x231B), @(0x23E9, 0x23EC), @(0x23F0, 0x23F0), @(0x23F3, 0x23F3), @(0x25FD, 0x25FE), @(0x2614, 0x2615),
        @(0x2648, 0x2653), @(0x267F, 0x267F), @(0x2693, 0x2693), @(0x26A1, 0x26A1), @(0x26AA, 0x26AB), @(0x26BD, 0x26BE),
        @(0x26C4, 0x26C5), @(0x26CE, 0x26CE), @(0x26D4, 0x26D4), @(0x26EA, 0x26EA), @(0x26F2, 0x26F3), @(0x26F5, 0x26F5),
        @(0x26FA, 0x26FA), @(0x26FD, 0x26FD), @(0x2705, 0x2705), @(0x270A, 0x270B), @(0x2728, 0x2728), @(0x274C, 0x274C),
        @(0x274E, 0x274E), @(0x2753, 0x2755), @(0x2757, 0x2757), @(0x2795, 0x2797), @(0x27B0, 0x27B0), @(0x27BF, 0x27BF),
        @(0x2B1B, 0x2B1C), @(0x2B50, 0x2B50), @(0x2B55, 0x2B55))) {
    for ($celeritasUICode = $celeritasUIRange[0]; $celeritasUICode -le $celeritasUIRange[1]; $celeritasUICode++) {
        [void]$script:CeleritasUIWideBmp.Add($celeritasUICode)
    }
}
Remove-Variable -Name celeritasUIRange, celeritasUICode -ErrorAction Ignore

function Get-CeleritasUIWidth {
    <# 終端機顯示寬度:CJK / 全形 / 東亞寬 emoji = 2;補充平面(emoji)= 2;變體選擇字 · ZWJ · 組合符號 = 0;其餘 1。 #>
    param([AllowNull()][string]$Text)
    $s = "" + $Text
    $w = 0
    $i = 0
    while ($i -lt $s.Length) {
        $ch = $s[$i]
        if ([char]::IsHighSurrogate($ch) -and $i + 1 -lt $s.Length -and [char]::IsLowSurrogate($s[$i + 1])) {
            $w += 2
            $i += 2
            continue
        }
        $c = [int]$ch
        $i++
        if ($c -lt 0x20 -or $c -eq 0x200B -or $c -eq 0x200D -or ($c -ge 0xFE00 -and $c -le 0xFE0F) -or ($c -ge 0x0300 -and $c -le 0x036F)) { continue }
        $wide = ($c -ge 0x1100 -and $c -le 0x115F) -or ($c -ge 0x2E80 -and $c -le 0xA4CF) -or ($c -ge 0xAC00 -and $c -le 0xD7A3) -or
                ($c -ge 0xF900 -and $c -le 0xFAFF) -or ($c -ge 0xFE30 -and $c -le 0xFE4F) -or ($c -ge 0xFF00 -and $c -le 0xFF60) -or
                ($c -ge 0xFFE0 -and $c -le 0xFFE6) -or $script:CeleritasUIWideBmp.Contains($c)
        $w += $(if ($wide) { 2 } else { 1 })
    }
    return $w
}

function Format-CeleritasUICell {
    <# 依顯示寬度裁切(按字素,不拆 emoji)並補空白;Justify = left / right / center。 #>
    param([AllowNull()][string]$Text, [int]$Width, [ValidateSet('left', 'right', 'center')][string]$Justify = 'left')
    $Width = [Math]::Max(1, $Width)
    $t = ("" + $Text) -replace "[\r\n\t]+", ' '
    if ((Get-CeleritasUIWidth $t) -gt $Width) {
        $sb = [System.Text.StringBuilder]::new()
        $acc = 0
        $e = [System.Globalization.StringInfo]::GetTextElementEnumerator($t)
        while ($e.MoveNext()) {
            $el = [string]$e.GetTextElement()
            $ew = Get-CeleritasUIWidth $el
            if ($acc + $ew + 1 -gt $Width) { break }
            [void]$sb.Append($el)
            $acc += $ew
        }
        $t = $sb.ToString() + '…'
    }
    $pad = [Math]::Max(0, $Width - (Get-CeleritasUIWidth $t))
    if ($Justify -eq 'right') { return (' ' * $pad) + $t }
    if ($Justify -eq 'center') {
        $left = [int][Math]::Floor($pad / 2)
        return (' ' * $left) + $t + (' ' * ($pad - $left))
    }
    return $t + (' ' * $pad)
}

function Get-CeleritasUIBudget {
    <# 總寬:VIA_PS_UI_WIDTH 優先;否則視窗寬(讀不到 / 太窄 = 100);上限 140。 #>
    $w = 0
    if ($env:VIA_PS_UI_WIDTH -as [int]) { $w = [int]$env:VIA_PS_UI_WIDTH }
    else {
        try { $w = [int]$Host.UI.RawUI.WindowSize.Width - 1 } catch { $w = 0 }
    }
    if ($w -lt 60) { $w = 100 }
    return [Math]::Min($w, 140)
}

function Get-CeleritasUIBox {
    if ($env:VIA_PS_UI_ASCII -eq '1') {
        return @{ tl = '+'; tr = '+'; bl = '+'; br = '+'; h = '-'; v = '|'; tj = '+'; bj = '+'; lj = '+'; rj = '+'; x = '+'; rule = '-' }
    }
    return @{ tl = '╭'; tr = '╮'; bl = '╰'; br = '╯'; h = '─'; v = '│'; tj = '┬'; bj = '┴'; lj = '├'; rj = '┤'; x = '┼'; rule = '─' }
}

function Get-CeleritasUILamp {
    <# 燈:分類用模板本體 Get-CeleritasStateClass(同 Write-CeleritasMatrixSummary)。 #>
    param([AllowNull()][string]$State)
    $cls = Get-CeleritasStateClass $State
    $ascii = $env:VIA_PS_UI_ASCII -eq '1'
    $map = @{
        OK   = @{ Lamp = $(if ($ascii) { '[OK]' } else { '✅' }); Color = 'Green' }
        SKIP = @{ Lamp = $(if ($ascii) { '[--]' } else { '⚪' }); Color = 'DarkYellow' }
        WARN = @{ Lamp = $(if ($ascii) { '[!!]' } else { '🟡' }); Color = 'Yellow' }
        FAIL = @{ Lamp = $(if ($ascii) { '[XX]' } else { '❌' }); Color = 'Red' }
    }
    $m = $map[$cls]
    return [pscustomobject]@{ Class = $cls; Lamp = $m.Lamp; Color = $m.Color }
}

function Write-CeleritasUISegments {
    <# 一行多段顏色;顏色空 = 終端機預設色。 #>
    param([object[]]$Segments)
    foreach ($seg in $Segments) {
        $color = "" + $seg[1]
        if ($color) { Write-Host $seg[0] -ForegroundColor $color -NoNewline }
        else { Write-Host $seg[0] -NoNewline }
    }
    Write-Host ""
}

function Write-CeleritasRule {
    <# Rich console.rule:一條滿寬分節線,標題置中。 #>
    param([string]$Title = '', [string]$Color = 'Cyan', [int]$Width = 0, [switch]$PassThru)
    $W = $(if ($Width -gt 0) { $Width } else { Get-CeleritasUIBudget })
    $b = Get-CeleritasUIBox
    $line = $b.rule * $W
    if ($Title) {
        $t = ' ' + (Format-CeleritasUICell $Title ([Math]::Min((Get-CeleritasUIWidth $Title), $W - 6))).TrimEnd() + ' '
        $tw = Get-CeleritasUIWidth $t
        $left = [int][Math]::Floor(($W - $tw) / 2)
        $line = ($b.rule * $left) + $t + ($b.rule * [Math]::Max(0, $W - $tw - $left))
    }
    if ($PassThru) { return $line }
    Write-Host $line -ForegroundColor $Color
}

function Write-CeleritasPanel {
    <# Rich Panel:圓角框,標題嵌在上框置中;-Fit = 框寬貼內容(Panel.fit)。
       -Lines 每個元素是字串,或 @{ Text = '…'; Color = 'Green' }。 #>
    param(
        [string]$Title = '',
        [AllowEmptyCollection()][object[]]$Lines = @(),
        [string]$Border = 'Blue',
        [string]$TitleColor = '',
        [switch]$Fit,
        [int]$Width = 0,
        [switch]$PassThru
    )
    $b = Get-CeleritasUIBox
    $items = @(foreach ($l in $Lines) {
            if ($l -is [System.Collections.IDictionary] -or ($null -ne $l -and $l -isnot [string] -and $l.PSObject.Properties['Text'])) {
                [pscustomobject]@{ Text = "" + (Get-CeleritasRowField $l @('Text', 'text')); Color = "" + (Get-CeleritasRowField $l @('Color', 'color')) }
            }
            else { [pscustomobject]@{ Text = "" + $l; Color = '' } }
        })
    $budget = [int]$(if ($Width -gt 0) { $Width } else { Get-CeleritasUIBudget })
    $longest = [int]((@($items | ForEach-Object { Get-CeleritasUIWidth $_.Text }) + @(0) | Measure-Object -Maximum).Maximum)
    $natural = [int][Math]::Max((Get-CeleritasUIWidth $Title) + 6, $longest + 4)
    $outer = [int]$(if ($Fit) { [Math]::Min($natural, $budget) } else { $budget })
    $inner = $outer - 2
    $top = $b.h * $inner
    if ($Title) {
        $t = ' ' + (Format-CeleritasUICell $Title ([Math]::Min((Get-CeleritasUIWidth $Title), $inner - 4))).TrimEnd() + ' '
        $tw = Get-CeleritasUIWidth $t
        $left = [int][Math]::Floor(($inner - $tw) / 2)
        $topL = $b.h * $left
        $topR = $b.h * [Math]::Max(0, $inner - $tw - $left)
    }
    $rows = @(foreach ($it in $items) { [pscustomobject]@{ Cell = (Format-CeleritasUICell $it.Text ($inner - 2)); Color = $it.Color } })
    if ($PassThru) {
        $out = [System.Collections.Generic.List[string]]::new()
        $out.Add($(if ($Title) { $b.tl + $topL + $t + $topR + $b.tr } else { $b.tl + $top + $b.tr }))
        foreach ($r in $rows) { $out.Add($b.v + ' ' + $r.Cell + ' ' + $b.v) }
        $out.Add($b.bl + $top + $b.br)
        return , $out.ToArray()
    }
    if ($Title) {
        $tc = $(if ($TitleColor) { $TitleColor } else { $Border })
        Write-CeleritasUISegments @(@(($b.tl + $topL), $Border), @($t, $tc), @(($topR + $b.tr), $Border))
    }
    else { Write-Host ($b.tl + $top + $b.tr) -ForegroundColor $Border }
    foreach ($r in $rows) {
        Write-CeleritasUISegments @(@(($b.v + ' '), $Border), @($r.Cell, $r.Color), @((' ' + $b.v), $Border))
    }
    Write-Host ($b.bl + $top + $b.br) -ForegroundColor $Border
}

function Write-CeleritasTable {
    <# Rich Table(box.ROUNDED):表名置中在上 · 洋紅表頭 · 表頭下一條分隔 · 欄色預設 青 / 綠 / 黃。
       -Columns 每欄是字串(欄名),或 @{ Name; Key; Width; Color; Justify = left|right|center; Lamp = $true }。
       Lamp 欄:值當狀態讀,印「燈 + 狀態」並依燈上色(同 Write-CeleritasMatrixSummary 的分類)。
       -Rows 每列是陣列(依欄序),或 hashtable / 物件(依欄 Key,預設 = Name)。 #>
    param(
        [string]$Title = '',
        [Parameter(Mandatory)][object[]]$Columns,
        [AllowEmptyCollection()][object[]]$Rows = @(),
        [string]$HeaderColor = 'Magenta',
        [string]$Border = 'DarkGray',
        [string]$TitleColor = 'White',
        [int]$MaxWidth = 0,
        [switch]$PassThru
    )
    $b = Get-CeleritasUIBox
    $palette = @('Cyan', 'Green', 'Yellow', 'Yellow', 'Yellow', 'Yellow', 'Yellow', 'Yellow')
    $cols = @(for ($k = 0; $k -lt $Columns.Count; $k++) {
            $c = $Columns[$k]
            if ($c -is [string]) { $c = @{ Name = $c } }
            $name = "" + (Get-CeleritasRowField $c @('Name', 'name'))
            $key = Get-CeleritasRowField $c @('Key', 'key')
            $jus = "" + (Get-CeleritasRowField $c @('Justify', 'justify'))
            $col = "" + (Get-CeleritasRowField $c @('Color', 'color'))
            [pscustomobject]@{
                Name    = $name
                Key     = $(if ($key) { "" + $key } else { $name })
                Fixed   = [int](0 + (Get-CeleritasRowField $c @('Width', 'width')))
                Color   = $(if ($col) { $col } else { $palette[[Math]::Min($k, $palette.Count - 1)] })
                Justify = $(if ($jus -in @('left', 'right', 'center')) { $jus } else { 'left' })
                Lamp    = [bool](Get-CeleritasRowField $c @('Lamp', 'lamp'))
                Width   = 0
            }
        })
    $n = $cols.Count
    $cells = @(foreach ($r in $Rows) {
            $vals = for ($k = 0; $k -lt $n; $k++) {
                $v = $(if ($r -is [System.Array]) { $(if ($k -lt $r.Count) { $r[$k] } else { '' }) } else { Get-CeleritasRowField $r @($cols[$k].Key) })
                if ($v -is [System.Collections.IEnumerable] -and $v -isnot [string]) { $v = (@($v) -join ' | ') }
                $text = "" + $v
                $color = $cols[$k].Color
                if ($cols[$k].Lamp) {
                    $lamp = Get-CeleritasUILamp $text
                    $text = $(if ($text) { $lamp.Lamp + ' ' + $text } else { $lamp.Lamp })
                    $color = $lamp.Color
                }
                [pscustomobject]@{ Text = $text; Color = $color }
            }
            , @($vals)
        })
    if ($cells.Count -eq 0) {
        $cells = @(, @(for ($k = 0; $k -lt $n; $k++) { [pscustomobject]@{ Text = $(if ($k -eq 0) { '(無資料)' } else { '' }); Color = 'DarkGray' } }))
    }
    foreach ($k in 0..($n - 1)) {
        $nat = Get-CeleritasUIWidth $cols[$k].Name
        foreach ($row in $cells) { $nat = [Math]::Max($nat, (Get-CeleritasUIWidth $row[$k].Text)) }
        $cols[$k].Width = $(if ($cols[$k].Fixed -gt 0) { $cols[$k].Fixed } else { [Math]::Max(1, $nat) })
    }
    $budget = [int]$(if ($MaxWidth -gt 0) { $MaxWidth } else { Get-CeleritasUIBudget })
    $total = { [int](1 + (($cols | Measure-Object -Property Width -Sum).Sum) + 3 * $n) }
    $guard = 0
    while ((& $total) -gt $budget -and $guard -lt 2000) {
        $wide = $cols | Where-Object { $_.Width -gt 4 } | Sort-Object Width -Descending | Select-Object -First 1
        if (-not $wide) { break }
        $wide.Width--
        $guard++
    }
    $outer = & $total
    $topLine = $b.tl + (($cols | ForEach-Object { $b.h * ($_.Width + 2) }) -join $b.tj) + $b.tr
    $sepLine = $b.lj + (($cols | ForEach-Object { $b.h * ($_.Width + 2) }) -join $b.x) + $b.rj
    $botLine = $b.bl + (($cols | ForEach-Object { $b.h * ($_.Width + 2) }) -join $b.bj) + $b.br
    $titleLine = $(if ($Title) { Format-CeleritasUICell $Title $outer 'center' } else { '' })
    $headCells = @(for ($k = 0; $k -lt $n; $k++) { Format-CeleritasUICell $cols[$k].Name $cols[$k].Width $(if ($cols[$k].Lamp) { 'center' } else { $cols[$k].Justify }) })
    $bodyCells = @(foreach ($row in $cells) {
            , @(for ($k = 0; $k -lt $n; $k++) {
                    $j = $(if ($cols[$k].Lamp) { 'center' } else { $cols[$k].Justify })
                    [pscustomobject]@{ Cell = (Format-CeleritasUICell $row[$k].Text $cols[$k].Width $j); Color = $row[$k].Color }
                })
        })
    if ($PassThru) {
        $out = [System.Collections.Generic.List[string]]::new()
        if ($Title) { $out.Add($titleLine.TrimEnd()) }
        $out.Add($topLine)
        $out.Add($b.v + ' ' + ($headCells -join (' ' + $b.v + ' ')) + ' ' + $b.v)
        $out.Add($sepLine)
        foreach ($row in $bodyCells) { $out.Add($b.v + ' ' + (@($row | ForEach-Object { $_.Cell }) -join (' ' + $b.v + ' ')) + ' ' + $b.v) }
        $out.Add($botLine)
        return , $out.ToArray()
    }
    if ($Title) { Write-Host $titleLine.TrimEnd() -ForegroundColor $TitleColor }
    Write-Host $topLine -ForegroundColor $Border
    $segs = [System.Collections.Generic.List[object]]::new()
    $segs.Add(@(($b.v + ' '), $Border))
    for ($k = 0; $k -lt $n; $k++) {
        $segs.Add(@($headCells[$k], $HeaderColor))
        $segs.Add(@($(if ($k -lt $n - 1) { ' ' + $b.v + ' ' } else { ' ' + $b.v }), $Border))
    }
    Write-CeleritasUISegments $segs.ToArray()
    Write-Host $sepLine -ForegroundColor $Border
    foreach ($row in $bodyCells) {
        $segs = [System.Collections.Generic.List[object]]::new()
        $segs.Add(@(($b.v + ' '), $Border))
        for ($k = 0; $k -lt $n; $k++) {
            $segs.Add(@($row[$k].Cell, $row[$k].Color))
            $segs.Add(@($(if ($k -lt $n - 1) { ' ' + $b.v + ' ' } else { ' ' + $b.v }), $Border))
        }
        Write-CeleritasUISegments $segs.ToArray()
    }
    Write-Host $botLine -ForegroundColor $Border
}

function Write-CeleritasRichMatrix {
    <# YFinance 啟動器版型的 MATRIX SUMMARY:
         [標題 Panel(-Header)] → 分節線 → [-Sections 各表] → 📈 步驟矩陣 → ⚡ 加速器 → 🎯 整體狀態 Panel.fit → 尾線。
       -Rows 同 Write-CeleritasMatrixSummary(id/步 · title/名 · state/結果 · sec/秒 · note/註);計數 · 判決 · -JsonPath 交給它。
       -Sections 每個是 @{ Title; Columns; Rows }(同 Write-CeleritasTable)。-PassThru 回傳同一份摘要物件。 #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][AllowEmptyCollection()][object[]]$Rows,
        [string]$Title = 'MATRIX SUMMARY',
        [string]$Icon = '🏛️',
        [AllowEmptyCollection()][object[]]$Header = @(),
        [AllowEmptyCollection()][object[]]$Sections = @(),
        [string]$Footer = 'VERITAS Intelligence System',
        [string]$JsonPath,
        [switch]$PassThru
    )
    if (-not (Get-Command Write-CeleritasMatrixSummary -ErrorAction SilentlyContinue)) {
        Write-Host '  [Celeritas UI] 模板本體 VeritasCeleritas.PS7.ps1 沒點源(Write-CeleritasMatrixSummary 不在);改經模板接入再叫' -ForegroundColor Yellow
        return
    }
    $sum = Write-CeleritasMatrixSummary -Rows $Rows -Title $Title -JsonPath $JsonPath -Quiet -PassThru
    $ico = $(if ($env:VIA_PS_UI_ASCII -eq '1' -or -not $Icon) { '' } else { $Icon + ' ' })
    $pick = { param($a, $u) if ($env:VIA_PS_UI_ASCII -eq '1') { $a } else { $u } }
    Write-Host ""
    if (@($Header).Count) { Write-CeleritasPanel -Title ($ico + $Title) -Lines $Header -Border 'Blue' }
    Write-CeleritasRule -Title ($ico + $Title + ' · 執行彙總矩陣') -Color 'Cyan'
    foreach ($sec in $Sections) {
        $sc = Get-CeleritasRowField $sec @('Columns', 'columns')
        if (-not $sc) { continue }
        Write-CeleritasTable -Title ("" + (Get-CeleritasRowField $sec @('Title', 'title'))) -Columns $sc -Rows @(Get-CeleritasRowField $sec @('Rows', 'rows'))
    }
    $stepRows = @(foreach ($i in $sum.Rows) {
            [pscustomobject]@{
                'ID'   = $i.Id
                '步驟' = $i.Title
                '狀態' = $i.State
                '秒'   = $(if ($i.Sec -as [double]) { '{0:N1}' -f [double]$i.Sec } else { '—' })
                '說明' = $i.Note
            }
        })
    Write-CeleritasTable -Title ((& $pick '' '📈 ') + '步驟矩陣') -Columns @(
        @{ Name = 'ID'; Color = 'Cyan' }, @{ Name = '步驟'; Color = 'Cyan' }, @{ Name = '狀態'; Lamp = $true },
        @{ Name = '秒'; Color = 'Green'; Justify = 'right' }, @{ Name = '說明'; Color = 'Yellow' }) -Rows $stepRows
    $acc = $sum.Accel
    Write-CeleritasTable -Title ((& $pick '' '⚡ ') + '加速器(Celeritas · 只動本行程 · 關閉即還原)') -Columns @(
        @{ Name = '功能'; Color = 'Cyan' }, @{ Name = '狀態'; Lamp = $true }, @{ Name = '參數'; Color = 'Yellow' }) -Rows @(
        @('Celeritas 本體', $(if ($acc.Applied) { 'OK' } else { 'SKIP' }), ('版本 ' + $acc.Version)),
        @('執行緒', 'INFO', ('workers=' + $acc.Workers)),
        @('本行程耗時', 'INFO', ('' + $acc.ElapsedMs + ' ms')))
    $verdictLine = switch ($sum.Verdict) {
        'GREEN' { @{ Text = ('  ' + (& $pick '[OK]' '✅') + ' 系統運行正常'); Color = 'Green' } }
        'AMBER' { @{ Text = ('  ' + (& $pick '[!!]' '🟡') + ' 部分功能受限(看上表黃燈列)'); Color = 'Yellow' } }
        'RED' { @{ Text = ('  ' + (& $pick '[XX]' '❌') + ' 有紅燈(先看上表紅燈列)'); Color = 'Red' } }
        default { @{ Text = ('  ' + (& $pick '[--]' '⚪') + ' 沒有步驟'); Color = 'DarkGray' } }
    }
    Write-CeleritasPanel -Fit -Border 'Cyan' -Title ((& $pick '' '🎯 ') + '整體狀態') -Lines @(
        ('  總步數   : ' + $sum.Total),
        ('  OK / SKIP / WARN / FAIL : {0} / {1} / {2} / {3}' -f $sum.OK, $sum.SKIP, $sum.WARN, $sum.FAIL),
        ('  總秒數   : ' + $sum.Seconds + ' 秒'),
        '',
        $verdictLine)
    Write-CeleritasRule -Title ($Title + ' · Celeritas ' + $acc.Version + ' · ' + (Get-Date -Format 'yyyy-MM-dd') + ' · ' + $Footer) -Color 'DarkGray'
    if ($PassThru) { return $sum }
}

function Test-CeleritasUI {
    <# 自測:框線每一行顯示寬度相同(含中文 / emoji / 裁切)· ASCII 模式 · 燈分類同模板本體 · 判決交給 MatrixSummary。 #>
    [CmdletBinding()]
    param([switch]$Quiet)
    $ok = [System.Collections.Generic.List[bool]]::new()
    $chk = {
        param($name, $cond, $note = '')
        $ok.Add([bool]$cond)
        if (-not $Quiet) { Write-Host ('  [' + $(if ($cond) { 'OK' } else { 'FAIL' }) + '] ' + $name + $(if ($note) { ' · ' + $note } else { '' })) -ForegroundColor $(if ($cond) { 'Green' } else { 'Red' }) }
    }
    $same = { param($lines) $ws = @($lines | ForEach-Object { Get-CeleritasUIWidth $_ } | Sort-Object -Unique); ($ws.Count -eq 1) }
    & $chk '① 寬度:中文 2 · emoji 2(含變體選擇字)· ASCII 1' ((Get-CeleritasUIWidth '中a') -eq 3 -and (Get-CeleritasUIWidth '✅') -eq 2 -and (Get-CeleritasUIWidth '🏛️') -eq 2 -and (Get-CeleritasUIWidth '🟡') -eq 2)
    & $chk '② 裁切不拆 emoji、補到指定寬' ((Get-CeleritasUIWidth (Format-CeleritasUICell '🏛️ 這是一段很長很長的說明文字' 9)) -eq 9 -and (Get-CeleritasUIWidth (Format-CeleritasUICell 'ab' 6 'right')) -eq 6)
    $t = Write-CeleritasTable -Title '📈 測試表' -MaxWidth 70 -PassThru -Columns @('項目', @{ Name = '狀態'; Lamp = $true }, @{ Name = '數值'; Justify = 'right' }, '說明') -Rows @(
        @('pandas/numpy', 'GREEN', '1,234', '資料表處理 + 衍生計算'),
        @('yfinance', 'RED', '0', '這一欄很長很長很長很長很長很長很長很長很長很長很長很長,要被裁切'),
        @('rich', 'SKIP', '—', '⚪ 可缺'))
    & $chk '③ 圓角表:框線每一行等寬 · 不超過上限' ((& $same @($t | Select-Object -Skip 1)) -and (Get-CeleritasUIWidth $t[1]) -le 70) ('寬 ' + (Get-CeleritasUIWidth $t[1]))
    $p = Write-CeleritasPanel -Fit -Title '🎯 整體狀態' -Lines @('  總步數 : 3', @{ Text = '  ✅ 系統運行正常'; Color = 'Green' }) -PassThru
    & $chk '④ Panel.fit:每一行等寬 · 標題嵌在上框' ((& $same $p) -and $p[0] -like '*整體狀態*')
    $keep = $env:VIA_PS_UI_ASCII
    try {
        $env:VIA_PS_UI_ASCII = '1'
        $a = Write-CeleritasTable -Columns @('A', @{ Name = 'S'; Lamp = $true }) -Rows @(, @('x', 'GREEN')) -PassThru
        & $chk '⑤ ASCII 模式:+ - | 框 · [OK] 字樣燈 · 等寬' ((& $same $a) -and ($a -join "`n") -match '\[OK\]' -and ($a -join '') -notmatch '[╭│]')
    }
    finally { $env:VIA_PS_UI_ASCII = $keep }
    & $chk '⑥ 燈分類就是模板本體 Get-CeleritasStateClass(GREEN=OK · rc=1=FAIL · SKIP=SKIP · 其他=WARN)' ((Get-CeleritasUILamp 'GREEN').Class -eq 'OK' -and (Get-CeleritasUILamp 'rc=1').Class -eq 'FAIL' -and (Get-CeleritasUILamp 'SKIP').Class -eq 'SKIP' -and (Get-CeleritasUILamp 'YELLOW').Class -eq 'WARN')
    if (Get-Command Write-CeleritasMatrixSummary -ErrorAction SilentlyContinue) {
        $s = Write-CeleritasRichMatrix -Title 'UI 自測' -Rows @(@{ id = '①'; title = '甲'; state = 'GREEN'; sec = 1.5 }, @{ id = '②'; title = '乙'; state = 'YELLOW'; sec = 0.5; note = '黃' }) -PassThru 6>$null
        & $chk '⑦ RichMatrix 的計數 · 判決就是 Write-CeleritasMatrixSummary 的(同一把尺)' ($s.Verdict -eq 'AMBER' -and $s.Total -eq 2 -and $s.WARN -eq 1 -and $s.Seconds -eq 2)
    }
    else { & $chk '⑦ RichMatrix(模板本體沒點源 → 跳過,不冒充)' $true 'SKIP' }
    $pass = -not ($ok -contains $false)
    if (-not $Quiet) { Write-Host ('[Celeritas UI ' + $script:CeleritasUI.Version + '] 自測 ' + @($ok | Where-Object { $_ }).Count + '/' + $ok.Count) -ForegroundColor $(if ($pass) { 'Green' } else { 'Red' }) }
    return [pscustomobject]@{ Pass = $pass; Passed = @($ok | Where-Object { $_ }).Count; Total = $ok.Count }
}
