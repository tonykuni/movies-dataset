#requires -Version 7.0
<# =====================================================================
 VRN Batch AllInOne v0101 — v0100 全功能保留 + OCR 重擷取車道(只增不減)
 ---------------------------------------------------------------------
 預設(無 -OCR):完整委派 v0100 No-OCR 車道(正本零觸碰,行為不變)。
 -OCR:重擷取車道(torch/paddleocr 修復後啟用)——
   O1  MDL005 文字擷取(雙引擎共識:fitz 主 + OCR 副,T01-T20 修復)
   O2  MDL004 表格擷取(pdfplumber 主 + OCR 副,F01-F20 修復)
   O3  DOCX 解析鏈(docx2txt → python-docx 梯次,末梯規格存證不空手)
 誠實口徑:每段 OK/FAIL/TIMEOUT 各自判定,不卡斷;引擎 exit code 為準。
 存證:VIA_Reports\vrn_ocr_runs\ocr_matrix_<ts>.html + ocr_all_<ts>.json
 用法:via-batch            → No-OCR 車道(= v0100)
       via-batch -OCR       → OCR 重擷取車道(60 PDF + 4 DOCX 全上)
       via-batch -OCR -Probe → 只印解析結果(python/引擎/路徑)不執行
===================================================================== #>
param(
    [switch]$OCR,
    [switch]$Probe,
    [switch]$NoOpen,
    [int]$Throttle = 3,
    [int]$TimeoutSec = 240,
    [int]$StageTimeoutSec = 5400,
    [int]$Workers = 0,
    [switch]$Fresh
)
Set-StrictMode -Off
$ErrorActionPreference = "Continue"
$vrn = $PSScriptRoot
$via = $vrn | Split-Path -Parent | Split-Path -Parent

# ── 無 -OCR:完整委派 v0100(正本行為不變)────────────────────────────
if (-not $OCR) {
    $v0100 = Join-Path $vrn "Invoke-VRN-Batch-AllInOne-v0100.ps1"
    & pwsh -NoProfile -File $v0100 -Throttle $Throttle -TimeoutSec $TimeoutSec @(if ($Fresh) { "-Fresh" })
    exit $LASTEXITCODE
}

# ── OCR 車道 ──────────────────────────────────────────────────────────
$inbox   = Join-Path $vrn "input\incoming"
$stageRt = Join-Path $vrn "staging\ocr_out"
$t005    = Join-Path $stageRt "mdl005_temp"
$t004    = Join-Path $stageRt "mdl004_temp"
$tdocx   = Join-Path $stageRt "docx_txt"
$ts      = Get-Date -Format "yyyyMMdd_HHmmss"
$repDir  = Join-Path $via "VIA_Reports\vrn_ocr_runs"
foreach ($d in @($stageRt,$t005,$t004,$tdocx,$repDir)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }

# python 動態解析(嚴禁寫死):via_core env → py → python → python3
$py = @("$env:USERPROFILE\envs\via_core_312\Scripts\python.exe","py","python","python3") |
      Where-Object { ($_ -notmatch '\\') -and (Get-Command $_ -ErrorAction SilentlyContinue) -or (($_ -match '\\') -and (Test-Path $_)) } |
      Select-Object -First 1
$eng005 = Join-Path $vrn "VRN_MDL005_OCRFetchingPDFText.py"
$eng004 = Join-Path $vrn "VRN_MDL004_OCR_FetchingPDFTable.py"

$pdfs = @(Get-ChildItem -LiteralPath $inbox -Filter *.pdf  -File -ErrorAction SilentlyContinue)
$docx = @(Get-ChildItem -LiteralPath $inbox -Filter *.doc* -File -ErrorAction SilentlyContinue)

Write-Host "=== VRN OCR 批次 v0101 · 進件 $($pdfs.Count) PDF + $($docx.Count) DOC/DOCX · python=$py ===" -ForegroundColor Cyan
Write-Host "  [入] $inbox" -ForegroundColor DarkGray
Write-Host "  [出] $stageRt" -ForegroundColor DarkGray
if ($Probe) {
    Write-Host "  [probe] MDL005=$(Test-Path $eng005) MDL004=$(Test-Path $eng004) 逾時=$StageTimeoutSec s/段 workers=$Workers"
    exit 0
}

$stages = [System.Collections.Generic.List[object]]::new()
function Invoke-Stage([string]$Name,[string]$Zh,[scriptblock]$Body) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    Write-Host "  ── $Name · $Zh ──" -ForegroundColor Yellow
    $st = "OK"; $note = ""
    try { $note = & $Body; if ($LASTEXITCODE -is [int] -and $LASTEXITCODE -ne 0 -and $script:stageExit -ne 0) { $st = "FAIL" } }
    catch { $st = "FAIL"; $note = $_.Exception.Message }
    if ($script:stageTimedOut) { $st = "TIMEOUT"; $script:stageTimedOut = $false }
    elseif ($script:stageExit -ne 0) { $st = "FAIL" }
    $sec = [math]::Round($sw.Elapsed.TotalSeconds,1)
    $color = if ($st -eq "OK") { "Green" } elseif ($st -eq "TIMEOUT") { "Yellow" } else { "Red" }
    Write-Host "  [$st] $Name · ${sec}s $note" -ForegroundColor $color
    $stages.Add([pscustomobject]@{ id=$Name; zh=$Zh; verdict=$st; sec=$sec; note="$note" })
}

# 引擎子程序:硬逾時 kill,exit code 誠實回傳
function Run-Engine([string]$EngPath,[string[]]$EngArgs,[string]$LogPath) {
    $script:stageExit = 0; $script:stageTimedOut = $false
    $spArgs = @{ FilePath=$py; ArgumentList=(@("`"$EngPath`"") + $EngArgs)
                 RedirectStandardOutput=$LogPath; RedirectStandardError="$LogPath.err"; PassThru=$true }
    if ($IsWindows) { $spArgs.WindowStyle = "Hidden" }   # 非 Windows pwsh 不支援此參數(容器煙測實抓)
    $proc = Start-Process @spArgs
    if (-not $proc.WaitForExit($StageTimeoutSec * 1000)) {
        try { $proc.Kill($true) } catch {}
        $script:stageTimedOut = $true; $script:stageExit = 1
        return "硬逾時 ${StageTimeoutSec}s → kill(誠實 TIMEOUT;log=$LogPath)"
    }
    $script:stageExit = $proc.ExitCode
    $okLine = Select-String -Path $LogPath -Pattern '"ok"\s*:\s*(true|false)' -ErrorAction SilentlyContinue | Select-Object -Last 1
    return "exit=$($proc.ExitCode) $(if($okLine){$okLine.Matches[0].Value}) · log=$(Split-Path $LogPath -Leaf)"
}

$script:stageExit = 0; $script:stageTimedOut = $false

# O1 · MDL005 文字
Invoke-Stage "O1 MDL005" "文字擷取(雙引擎共識+T01-T20)" {
    Run-Engine $eng005 @("--pdf-temp","`"$inbox`"","--mdl005-temp","`"$t005`"","--workers","$Workers") (Join-Path $repDir "mdl005_$ts.log")
}
# O2 · MDL004 表格
Invoke-Stage "O2 MDL004" "表格擷取(雙引擎投票+F01-F20)" {
    Run-Engine $eng004 @("--pdf-temp","`"$inbox`"","--mdl004-temp","`"$t004`"","--workers","$Workers") (Join-Path $repDir "mdl004_$ts.log")
}
# O3 · DOCX 解析鏈(docx2txt → python-docx;末梯規格存證)
Invoke-Stage "O3 DOCX" "解析鏈 $($docx.Count) 件(docx2txt→python-docx 梯次)" {
    $script:stageExit = 0; $script:stageTimedOut = $false
    $pycode = @'
import sys, os, json, hashlib
inbox, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
rows = []
for n in sorted(os.listdir(inbox)):
    if not n.lower().endswith((".docx", ".doc")): continue
    src = os.path.join(inbox, n); txt = None; eng = ""
    try:
        import docx2txt; txt = docx2txt.process(src); eng = "docx2txt"
    except Exception:
        try:
            import docx
            txt = "\n".join(p.text for p in docx.Document(src).paragraphs); eng = "python-docx"
        except Exception as e:
            eng = "spec-only:%s" % type(e).__name__
    if txt is not None:
        out = os.path.join(outdir, os.path.splitext(n)[0] + ".txt")
        open(out, "w", encoding="utf-8").write(txt)
        rows.append({"file": n, "engine": eng, "chars": len(txt), "ok": True})
    else:
        h = hashlib.sha256(open(src, "rb").read()).hexdigest()[:12]
        rows.append({"file": n, "engine": eng, "sha12": h,
                     "size": os.path.getsize(src), "ok": False,
                     "note": "規格存證(候引擎補件;via-envmgr plan-install docx2txt)"})
    print("[%s] %s %s" % ("OK " if rows[-1]["ok"] else "SPEC", n, eng))
ok = sum(1 for r in rows if r["ok"])
json.dump({"ok": ok == len(rows) and len(rows) > 0, "total": len(rows), "extracted": ok, "rows": rows},
          open(os.path.join(outdir, "docx_parse_result.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(json.dumps({"ok": ok == len(rows), "total": len(rows), "extracted": ok}, ensure_ascii=False))
sys.exit(0 if ok == len(rows) else 1)
'@
    $tmp = Join-Path $repDir "docx_parse_$ts.py"
    [IO.File]::WriteAllText($tmp, $pycode, [Text.UTF8Encoding]::new($false))
    $log = Join-Path $repDir "docx_$ts.log"
    Run-Engine $tmp @("`"$inbox`"","`"$tdocx`"") $log
}

# ── 總結矩陣(誠實口徑)+ 存證 ────────────────────────────────────────
$okN   = @($stages | Where-Object verdict -eq "OK").Count
$failN = @($stages | Where-Object verdict -eq "FAIL").Count
$toN   = @($stages | Where-Object verdict -eq "TIMEOUT").Count
$tot   = [math]::Round(($stages | Measure-Object sec -Sum).Sum,1)
Write-Host "`n=== OCR 批次總結 · OK $okN · FAIL $failN · TIMEOUT $toN · ${tot}s(誠實口徑,不卡斷)===" -ForegroundColor Cyan
$evi = Join-Path $repDir "ocr_all_$ts.json"
@{ ts=$ts; inbox="$inbox"; pdf=$pdfs.Count; docx=$docx.Count; python="$py"; stages=$stages } |
    ConvertTo-Json -Depth 5 | Out-File $evi -Encoding utf8

$rowsHtml = ($stages | ForEach-Object {
    $cls = @{OK="g";TIMEOUT="o";FAIL="r"}[$_.verdict]
    "<tr><td class='mono'>$($_.id)</td><td>$($_.zh)</td><td><span class='tag $cls'>$($_.verdict)</span></td><td class='r mono'>$($_.sec)s</td><td class='small'>$([System.Web.HttpUtility]::HtmlEncode($_.note))</td></tr>"
}) -join ""
Add-Type -AssemblyName System.Web -ErrorAction SilentlyContinue
$html = @"
<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VRN OCR Batch Matrix $ts</title><style>
*{box-sizing:border-box;margin:0;padding:0}body{background:#f2f1ec;color:#33403f;font-family:"Microsoft JhengHei","Segoe UI",sans-serif;font-size:clamp(9.5px,1.05vw,11px);padding:16px 20px;max-width:980px;margin:0 auto;line-height:1.5}
.mast{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;border-bottom:1px solid #dcdad3;padding-bottom:10px;margin-bottom:12px}
h1{font-family:'Cormorant Garamond',Georgia,serif;font-size:19px;font-weight:500;letter-spacing:.055em;color:#1b1a17}
.zh{font-size:11px;color:#6b6860;margin-top:2px}.num{font-family:Consolas,monospace;font-size:9.5px;letter-spacing:.16em;color:#6b6860;text-transform:uppercase}
.st{font-family:Consolas,monospace;font-size:11px;color:#3d7a52;text-align:right}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #dbd9d3;border-radius:8px}
th,td{text-align:left;border-bottom:1px solid #ebe9e3;padding:5px 9px;vertical-align:top}
th{color:#6b6860;font-weight:700;font-size:9px;text-transform:uppercase;font-family:Consolas,monospace;letter-spacing:.05em}
.r{text-align:right}.mono{font-family:Consolas,monospace;font-size:.95em}.small{font-size:.92em;color:#6b6860}
.tag{display:inline-block;padding:1px 8px;border-radius:9px;font-family:Consolas,monospace;font-size:8.5px;font-weight:700}
.tag.g{background:#e6efec;color:#2c4f4a}.tag.o{background:#f2ecdd;color:#6f5c31}.tag.r{background:#f3e7e6;color:#9e2b25}
.foot{font-family:Consolas,monospace;font-size:9px;letter-spacing:.1em;color:#6b6860;text-transform:uppercase;text-align:center;padding:9px 0 3px}
</style></head><body>
<div class="mast"><div><div class="num">VRN-OCR-BATCH · $ts</div><h1>VRN OCR BATCH · SUMMARY MATRIX</h1>
<div class="zh">重擷取車道 O1-O3 · 進件 $($pdfs.Count) PDF + $($docx.Count) DOC/DOCX · 誠實口徑不卡斷</div></div>
<div class="st">OK $okN · FAIL $failN · TIMEOUT $toN<br>${tot}s</div></div>
<table><tr><th>段</th><th>內容</th><th>判定</th><th class="r">耗時</th><th>備註</th></tr>$rowsHtml</table>
<div class="foot">VERITAS REPORT NOVA · OCR BATCH v0101 · 存證 ocr_all_$ts.json</div></body></html>
"@
$rep = Join-Path $repDir "ocr_matrix_$ts.html"
[IO.File]::WriteAllText($rep, $html, [Text.UTF8Encoding]::new($false))
Write-Host "  報告:$rep" -ForegroundColor Cyan
Write-Host "  存證:$evi" -ForegroundColor Cyan
if (-not $NoOpen) { Start-Process $rep }
exit $(if ($failN -eq 0 -and $toN -eq 0) { 0 } else { 1 })
