#Requires -Version 5.1
<# =====================================================================
 VIA_WinIO_InputPicker_v0100.ps1 — Windows 原生 I/O 輸入器(批465 立)
 ---------------------------------------------------------------------
 操作員令:「輸入介面不再有特定系統內指定位置,改為一律 WINDOWS I/O
 或拖曳式輸入,搜尋檔案夾中的 WORD PDF IMAGE 檔案」。

 先查再造(量到的,不是猜的):
   · 全倉 grep `FolderBrowserDialog|OpenFileDialog|System.Windows.Forms`
     → **零命中**。真正的 Windows 原生選檔器不存在,所以造。
   · MDL139 InputConsole v0102 **已經有**選夾/選檔/拖曳區(webkitdirectory
     + type=file + dragover/drop)→ Zero-Hydra:那一套不重造。但瀏覽器
     **拿不到真實路徑**(webkitRelativePath 只有相對名),所以它只能把副本
     上傳進 incoming——「特定系統內指定位置」拔不掉的根就在這裡。
     本件補的正是那一格:原生對話框交出**真實路徑**,引擎就地讀,零複製。

 三條輸入道(都只交出真實路徑,下游一視同仁):
   ① 原生對話框   -Pick File|Folder  → OpenFileDialog(可多選)/ FolderBrowserDialog
   ② 拖曳         把檔或夾拖到 via-vrnin.cmd 上(Windows 把路徑當 %* 傳進來)
   ③ 參數/管線    -Path a,b,c  或  dir *.pdf | via-vrnin -FromPipe

 零彈窗律(與治理律相容):對話框**只在操作員自己要求時**開。
   -Pick 沒給 → 一律不開對話框;非互動環境(排程/CI/VIA_NO_DIALOG=1)
   即使給了 -Pick 也不開,改為誠實回「非互動=不彈窗」並要求 -Path。

 PS7 的坑(不處理就是他一按就爆):Windows PowerShell 5.1 主執行緒是 STA,
 **PowerShell 7 預設是 MTA**,對話框在 MTA 執行緒 ShowDialog 會直接拋
 「current thread must be set to single thread apartment」。故本件一律把
 對話框丟進一個 STA runspace 跑(Invoke-VIASTA),兩種殼都通。

 紀律:零 force、零刪除、原件零複製(就地讀)、誠實三態、不卡斷。
 用法:
   .\VIA_WinIO_InputPicker_v0100.ps1 -Pick File            選檔(多選)→ 跑鏈
   .\VIA_WinIO_InputPicker_v0100.ps1 -Pick Folder          選夾 → 跑鏈
   .\VIA_WinIO_InputPicker_v0100.ps1 -Path "D:\a.pdf","E:\報告夾"
   .\VIA_WinIO_InputPicker_v0100.ps1 -Path X -ListOnly     只列不跑
   .\VIA_WinIO_InputPicker_v0100.ps1 -Selftest             自測(零彈窗)
===================================================================== #>
param(
    [string[]]$Path = @(),
    [ValidateSet("", "File", "Folder")][string]$Pick = "",
    [switch]$ListOnly,
    [switch]$NoIncoming,
    [switch]$Open,
    [int]$TimeoutSec = 900,
    [switch]$FromPipe,
    [switch]$Selftest
)
$ErrorActionPreference = "Continue"
Set-StrictMode -Off

# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

$HERE = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
$VIA = Split-Path $HERE -Parent
$SPEC = Join-Path $VIA "supportive modules\registry\VIA_InputConsole_Spec_v0100.json"
$VRNDIR = Join-Path $VIA "functional modules\VRN"

function Say([string]$state, [string]$msg) { Write-Host ("  [" + $state + "] " + $msg) }

# ── ① 受理副檔名:讀冊,不寫死 ─────────────────────────────────────
function Get-VIAIntakeExt {
    <# 回 @{ pdf=@(...); word=@(...); image=@(...); all=@(...); why="" } #>
    $fb = @{
        pdf   = @(".pdf")
        word  = @(".docx", ".doc")
        image = @(".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp", ".gif")
    }
    $why = "冊不在 → 內建退路"
    if (Test-Path -LiteralPath $SPEC) {
        try {
            $j = Get-Content -LiteralPath $SPEC -Raw -Encoding UTF8 | ConvertFrom-Json
            $it = $j.families.vrn.input.intake
            if ($it) {
                $fb = @{
                    pdf   = @($it.pdf)
                    word  = @($it.word)
                    image = @($it.image)
                }
                $why = "冊 VIA_InputConsole_Spec_v0100.json.input.intake"
            } else {
                $why = "冊無 intake 鍵 → 內建退路"
            }
        } catch {
            $why = "冊讀取失敗 " + $_.Exception.GetType().Name + " → 內建退路"
        }
    }
    $all = @($fb.pdf + $fb.word + $fb.image | ForEach-Object { $_.ToString().ToLower() } | Sort-Object -Unique)
    return @{ pdf = $fb.pdf; word = $fb.word; image = $fb.image; all = $all; why = $why }
}

# ── ② STA 保險:PS7 預設 MTA,對話框不放進 STA runspace 會當場拋例外 ──
function Invoke-VIASTA([scriptblock]$Body) {
    if ([System.Threading.Thread]::CurrentThread.GetApartmentState() -eq "STA") {
        return (& $Body)
    }
    $rs = [runspacefactory]::CreateRunspace()
    $rs.ApartmentState = "STA"
    $rs.ThreadOptions = "ReuseThread"
    $rs.Open()
    $ps = [powershell]::Create()
    $ps.Runspace = $rs
    [void]$ps.AddScript($Body.ToString())
    try { $out = $ps.Invoke() } catch { $out = @() }
    $ps.Dispose(); $rs.Close(); $rs.Dispose()
    return $out
}

function Test-VIAInteractive {
    <# 零彈窗律:非互動一律不開對話框,而且要說得出為什麼。 #>
    if ($env:VIA_NO_DIALOG -eq "1") { return @($false, "VIA_NO_DIALOG=1") }
    if ($env:CI -or $env:GITHUB_ACTIONS) { return @($false, "CI 環境") }
    if (-not [Environment]::UserInteractive) { return @($false, "UserInteractive=False") }
    if (-not ($PSVersionTable.Platform -eq $null -or $PSVersionTable.Platform -eq "Win32NT")) {
        return @($false, "非 Windows(" + $PSVersionTable.Platform + ")=無 Windows I/O")
    }
    return @($true, "")
}

# ── ③ 原生對話框(交出真實路徑)─────────────────────────────────────
function Show-VIAFileDialog([string[]]$Ext) {
    $filt = "報告件 (WORD/PDF/IMAGE)|" + (($Ext | ForEach-Object { "*" + $_ }) -join ";") + "|全部 (*.*)|*.*"
    $body = [scriptblock]::Create(@"
Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
`$d = New-Object System.Windows.Forms.OpenFileDialog
`$d.Title = 'VIA · 選取研究報告(WORD / PDF / IMAGE;可多選)'
`$d.Multiselect = `$true
`$d.Filter = '$filt'
if (`$d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { `$d.FileNames }
"@)
    return @(Invoke-VIASTA $body)
}

function Show-VIAFolderDialog {
    $body = [scriptblock]::Create(@"
Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
`$d = New-Object System.Windows.Forms.FolderBrowserDialog
`$d.Description = 'VIA · 選取報告資料夾(夾內 WORD / PDF / IMAGE 全收)'
`$d.ShowNewFolderButton = `$false
if (`$d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { `$d.SelectedPath }
"@)
    return @(Invoke-VIASTA $body)
}

# ── ④ 路徑解析:檔/夾都收,系統任何位置;不存在的**講出來**不吞 ──────
function Resolve-VIAInput([string[]]$Raw, [hashtable]$Ext) {
    $files = @(); $notes = @()
    foreach ($r in $Raw) {
        $t = ($r -as [string])
        if (-not $t) { continue }
        $t = $t.Trim().Trim('"')
        if (-not $t) { continue }
        if (Test-Path -LiteralPath $t -PathType Container) {
            $got = @(Get-ChildItem -LiteralPath $t -File -Recurse:$false -ErrorAction SilentlyContinue |
                     Where-Object { $Ext.all -contains $_.Extension.ToLower() })
            $notes += ("夾 " + $t + " → " + $got.Count + " 件")
            $files += @($got | ForEach-Object { $_.FullName })
        } elseif (Test-Path -LiteralPath $t -PathType Leaf) {
            $e = [System.IO.Path]::GetExtension($t).ToLower()
            if ($Ext.all -contains $e) {
                $notes += ("檔 " + (Split-Path $t -Leaf))
                $files += (Resolve-Path -LiteralPath $t).Path
            } else {
                $notes += ("略過 " + (Split-Path $t -Leaf) + "(非報告件 " + ($(if ($e) { $e } else { "無副檔名" })) + ")")
            }
        } else {
            $notes += ("路徑不存在 " + $t)
        }
    }
    return @{ files = @($files | Sort-Object -Unique); notes = $notes }
}

# ── ⑤ 交給 VRN 尾版引擎(尾版律 glob;不卡斷;動態進度)─────────────
function Invoke-VIAVrnIntake([string[]]$Files, [switch]$NoInc, [switch]$OpenAfter, [int]$Timeout) {
    $eng = @(Get-ChildItem -LiteralPath $VRNDIR -Filter "VRN_ENG072_FirstPageText_v*.py" -File -ErrorAction SilentlyContinue |
             Sort-Object Name)
    if ($eng.Count -lt 1) { Say "FAIL" ("尾版引擎缺:" + $VRNDIR + "\VRN_ENG072_FirstPageText_v*.py"); return 2 }
    $tail = $eng[-1].FullName
    $py = "python"
    foreach ($cand in @("python", "python3", "py")) {
        $c = Get-Command $cand -ErrorAction SilentlyContinue
        if ($c) { $py = $c.Source; break }
    }
    $argv = @($tail, "run")
    foreach ($f in $Files) { $argv += @("--in", $f) }
    if ($NoInc) { $argv += "--no-incoming" }
    if ($OpenAfter) { $argv += "--open" }
    Say "RUN" ("引擎 " + (Split-Path $tail -Leaf) + " · 收件 " + $Files.Count + " 份 · 逾時 " + $Timeout + "s")

    $o = [System.IO.Path]::GetTempFileName(); $e = [System.IO.Path]::GetTempFileName()
    # Start-Process 不會自己替含空白的引數補引號(實測:靜靜 rc=2)
    $q = @($argv | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } })
    $p = Start-Process -FilePath $py -ArgumentList $q -NoNewWindow -PassThru `
                       -RedirectStandardOutput $o -RedirectStandardError $e
    $sw = [Diagnostics.Stopwatch]::StartNew(); $seen = 0; $killed = $false
    while (-not $p.HasExited) {
        Start-Sleep -Milliseconds 400
        $el = [int]$sw.Elapsed.TotalSeconds
        $pct = [Math]::Min(99, [int](100 * $el / [Math]::Max(1, $Timeout)))
        $lines = @(Get-Content -LiteralPath $o -ErrorAction SilentlyContinue)
        if ($lines.Count -gt $seen) {
            foreach ($ln in $lines[$seen..($lines.Count - 1)]) { if ($ln) { Write-Host ("    " + $ln) } }
            $seen = $lines.Count
        }
        Write-Progress -Id 1 -Activity "VIA · VRN 首頁擷取" `
                       -Status ("已 " + $el + "s · 輸出 " + $seen + " 行") -PercentComplete $pct
        if ($el -ge $Timeout) { try { $p.Kill() } catch { }; $killed = $true; break }
    }
    Write-Progress -Id 1 -Activity "VIA · VRN 首頁擷取" -Completed
    $rest = @(Get-Content -LiteralPath $o -ErrorAction SilentlyContinue)
    if ($rest.Count -gt $seen) { foreach ($ln in $rest[$seen..($rest.Count - 1)]) { if ($ln) { Write-Host ("    " + $ln) } } }
    $err = (Get-Content -LiteralPath $e -Raw -ErrorAction SilentlyContinue)
    Remove-Item -LiteralPath $o, $e -ErrorAction SilentlyContinue
    if ($killed) { Say "FAIL" ("逾 " + $Timeout + "s 未回=已停(不卡斷);現場保留"); return 3 }
    if ($p.ExitCode -ne 0 -and $err) { Say "WARN" ("引擎 stderr:" + ($err.Trim() -split "`n")[-1]) }
    return $p.ExitCode
}

# ── ⑥ 自測(零彈窗;對話框那一段在非 Windows 上測不到,誠實講明)──────
function Invoke-VIAPickerSelftest {
    $fails = @(); $done = 0
    function ck([string]$name, [bool]$cond, [string]$note) {
        $script:done++
        Write-Host ("  [" + $(if ($cond) { "OK" } else { "FAIL" }) + "] " + $name + " " + $note)
        if (-not $cond) { $script:fails += $name }
    }
    $script:done = 0; $script:fails = @()
    $src = Get-Content -LiteralPath $PSCommandPath -Raw
    # 「缺席檢」不能拿整支檔比對:檢自己那一行就寫著要找的那個字
    # (例如 `-notmatch "Stop-Process"` 這句本身就含 Stop-Process),
    # 於是永遠為假=自我指涉假紅。缺席一律只看**自測段以外**的本體。
    $cut = $src.IndexOf("function Invoke-VIAPickerSelftest")
    $body = if ($cut -gt 0) { $src.Substring(0, $cut) } else { $src }

    $ext = Get-VIAIntakeExt
    ck "① 受理副檔名讀冊不寫死(WORD/PDF/IMAGE 三類)" `
       (($ext.all -contains ".pdf") -and ($ext.all -contains ".docx") -and ($ext.all -contains ".png") -and ($ext.all.Count -ge 10)) `
       ("(" + $ext.why + " · " + $ext.all.Count + " 種:" + (($ext.all | Select-Object -First 6) -join ",") + "…)")

    ck "② STA 保險在檔——PS7 預設 MTA,對話框不丟進 STA runspace 會拋 'single thread apartment' 當場爆" `
       (($src -match 'ApartmentState\s*=\s*"STA"') -and ($src -match "Invoke-VIASTA")) `
       ("(本殼 " + [System.Threading.Thread]::CurrentThread.GetApartmentState() + " · PS " + $PSVersionTable.PSVersion + ")")

    $iact = Test-VIAInteractive
    $env:VIA_NO_DIALOG = "1"
    $iact2 = Test-VIAInteractive
    $env:VIA_NO_DIALOG = ""
    ck "③ 零彈窗律:VIA_NO_DIALOG=1 / CI / 非互動 / 非 Windows 一律不開對話框" `
       ((-not $iact2[0]) -and ($iact2[1] -eq "VIA_NO_DIALOG=1")) `
       ("(本境互動=" + $iact[0] + $(if ($iact[1]) { "(" + $iact[1] + ")" } else { "" }) + " · 旗標壓制=生效)")

    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("via_pick_" + [guid]::NewGuid().ToString("N"))
    $sub = Join-Path $tmp "任意位置"
    New-Item -ItemType Directory -Path $sub -Force | Out-Null
    Set-Content -LiteralPath (Join-Path $sub "a.pdf") -Value "x" -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $sub "b.docx") -Value "x" -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $sub "c.png") -Value "x" -Encoding UTF8
    Set-Content -LiteralPath (Join-Path $sub "d.txt") -Value "x" -Encoding UTF8
    $r1 = Resolve-VIAInput @($sub) $ext
    ck "④ 夾輸入:夾內 WORD/PDF/IMAGE 全收,非報告件不收(這裡是 .txt)" `
       ($r1.files.Count -eq 3) ("(收 " + $r1.files.Count + " 件 · 應 3)")

    $r2 = Resolve-VIAInput @((Join-Path $sub "a.pdf"), (Join-Path $sub "d.txt"), (Join-Path $tmp "不存在.pdf")) $ext
    ck "⑤ 檔輸入:真實路徑收下;非報告件與不存在路徑**講出來**不默默吞掉" `
       ($r2.files.Count -eq 1 -and (($r2.notes -join "|") -match "非報告件") -and (($r2.notes -join "|") -match "路徑不存在")) `
       ("(收 1 · 註記 " + $r2.notes.Count + " 條)")

    $r3 = Resolve-VIAInput @("  `"$sub`"  ") $ext
    ck "⑥ 拖曳律:Windows 拖檔進來會帶引號與空白(`"C:\有 空白\a.pdf`"),要剝乾淨才 Test-Path 得到" `
       ($r3.files.Count -eq 3) ("(帶引號空白仍收 " + $r3.files.Count + " 件)")

    $eng = @(Get-ChildItem -LiteralPath $VRNDIR -Filter "VRN_ENG072_FirstPageText_v*.py" -File -ErrorAction SilentlyContinue | Sort-Object Name)
    $tailName = ""
    if ($eng.Count -ge 1) { $tailName = $eng[-1].Name }
    ck "⑦ 尾版律:綁 ENG072 尾版(glob 取尾,不寫死版號)且該版**收得下影像**" `
       (($eng.Count -ge 1) -and ((Get-Content -LiteralPath $eng[-1].FullName -Raw) -match "intake_in_dir")) `
       ("(" + $eng.Count + " 版 · 尾版 " + $tailName + ")")

    ck "⑧ Zero-Hydra:不自建 OCR/抽取,一律委派 ENG072 尾版;也不重造 MDL139 的拖曳區(瀏覽器那套拿不到真實路徑,本件補的正是那一格)" `
       (($body -notmatch "tesseract") -and ($src -match "Invoke-VIAVrnIntake") -and ($src -match "webkitRelativePath")) `
       "(零 OCR 實作 · 委派在檔 · 因由在檔)"

    ck "⑨ 不卡斷:逾時只殺**自己生的**那個子行程,並回 rc=3 誠實說停;兩級進度條" `
       (($body -match '\$p\.Kill\(\)') -and ($body -match "Write-Progress") -and ($body -notmatch "Stop-Process")) `
       "(零 Stop-Process)"

    # 檢法用 Contains 不用 -match:這句本身滿是引號與反斜線,寫成正則會把
    # 檔案的語法弄壞(v0100 初稿就是在這裡 ParserError,整支載不進來)。
    $quoteGuard = $src.Contains("ForEach-Object { if (`$_ -match '\s')")
    ck "⑪ 零卡斷續章:腳本一提 `$input`,PowerShell 在 -File 模式會先把 stdin 讀到 EOF 才開跑;stdin 是沒人關的管線時=永遠不回(v0100 初稿實測掛住)。管線輸入改成只有明講 -FromPipe 才讀" `
       (($body -notmatch '\$input') -and ($body -match "FromPipe")) `
       "(本體零 dollar-input · -FromPipe 在檔)"

    ck "⑩ Start-Process 引數含空白要自己補引號(實測慣例:不補會靜靜 rc=2,看起來像引擎壞了)" `
       ($quoteGuard -and $src.Contains("-ArgumentList `$q")) "(補引號在檔)"

    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue

    $winOnly = -not ($PSVersionTable.Platform -eq $null -or $PSVersionTable.Platform -eq "Win32NT")
    if ($winOnly) {
        Write-Host "  [註] 本境非 Windows:對話框**實際彈出**那一段測不到(System.Windows.Forms 載不了)。"
        Write-Host "       ①–⑩ 測的是路徑解析、零彈窗律、STA 保險在檔、委派與不卡斷;"
        Write-Host "       對話框本體要在工作站按一次才算驗過——不拿「檔裡有」當「跑得動」。"
    }
    Write-Host ("  [計] 十一檢(" + $script:done + " 檢) OK " + ($script:done - $script:fails.Count) + " · FAIL " + $script:fails.Count)
    if ($script:fails.Count) { return 1 }
    return 0
}

# ═══════════════════ 主流程 ═══════════════════
if ($Selftest) {
    Write-Host ""
    Write-Host "=== Windows 原生 I/O 輸入器(VIA_WinIO_InputPicker v0100)· 十一檢自測(零彈窗)==="
    exit (Invoke-VIAPickerSelftest)
}

Write-Host ""
Write-Host "=== VIA · Windows I/O 輸入(批465:零指定位置)==="
$ext = Get-VIAIntakeExt
Say "OK" ("受理 " + $ext.all.Count + " 種副檔名 · " + $ext.why)

$raw = @()
# 管線輸入:**只有明講 -FromPipe 才讀**。
# v0100 初稿寫 `if ($input) {...}`,實測當場卡死:腳本一旦提到 $input,
# PowerShell 在 -File 模式會**先把 stdin 讀到 EOF 才開始跑**——stdin 是
# 沒人要關的管線時,它不是慢,是永遠不會回(自測那一次就這樣掛住)。
# 「零卡斷」不能靠使用者記得加 </dev/null。
if ($FromPipe) {
    $piped = [Console]::In.ReadToEnd()
    if ($piped) { $raw += @($piped -split "`r?`n" | Where-Object { $_.Trim() }) }
}
$raw += @($Path)

if ($Pick) {
    $ia = Test-VIAInteractive
    if (-not $ia[0]) {
        Say "WARN" ("非互動(" + $ia[1] + ")=不彈窗(零彈窗律);請改用 -Path")
    } else {
        if ($Pick -eq "Folder") { $got = Show-VIAFolderDialog } else { $got = Show-VIAFileDialog $ext.all }
        if ($got.Count) {
            Say "OK" ("原生對話框選了 " + $got.Count + " 筆(真實路徑)")
            $raw += @($got)
        } else {
            Say "WARN" "對話框取消或沒選=零件(誠實)"
        }
    }
}

if (-not $raw.Count) {
    Say "FAIL" "沒有輸入。三條道擇一:-Pick File / -Pick Folder / -Path <檔或夾>,或把檔拖到 via-vrnin.cmd 上"
    exit 2
}

$res = Resolve-VIAInput $raw $ext
foreach ($n in $res.notes) { Say "OK" $n }
if (-not $res.files.Count) {
    Say "FAIL" "解析後零報告件(誠實;不假跑)"
    exit 2
}
Say "OK" ("就地讀 " + $res.files.Count + " 件(零複製;不進 incoming、不進任何指定位置)")

if ($ListOnly) {
    foreach ($f in $res.files) { Write-Host ("    " + $f) }
    Say "OK" "-ListOnly=只列不跑"
    exit 0
}

$rc = Invoke-VIAVrnIntake $res.files -NoInc:$NoIncoming -OpenAfter:$Open -Timeout $TimeoutSec
Write-Host ""
if ($rc -eq 0) { Say "OK" "總判 GREEN · 首頁擷取完成" }
elseif ($rc -eq 2) { Say "WARN" "總判 AMBER · 引擎回無報告件(看上面逐行因由)" }
else { Say "FAIL" ("總判 RED · rc=" + $rc) }
exit $rc
