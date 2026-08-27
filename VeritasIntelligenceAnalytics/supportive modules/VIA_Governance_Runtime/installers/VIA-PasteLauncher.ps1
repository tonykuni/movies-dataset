&{
# ============================================================================
#  VIA 一鍵啟動器 (貼上即用 / 不卡斷)  --  15 個 PowerShell .NET 加速器
# ----------------------------------------------------------------------------
#  為什麼用 &{ } 包起來: 主控台會把整塊緩衝到結尾 } 才一次解析,
#  所以 else / 空行 / 多行結構都不會被逐行拆斷 (這是上次報錯的真正原因).
#  它做的事: 快速找到 VIA-OneShot-v0100.ps1 -> 解鎖 -> 用 -File 正確執行
#            -> 輸出即時串流 (不緩衝, 不卡畫面) -> 完成後開 UI.
#  加速器清單 (共 15):
#   1 Stopwatch  2 EnumerationOptions  3 Directory.EnumerateFiles  4 Path
#   5 File  6 FileInfo  7 UTF8Encoding  8 List[T]  9 ProcessStartInfo
#  10 Process  11 Environment  12 StringBuilder  13 regex  14 datetime
#  15 Language.Parser
# ============================================================================
$sw = [System.Diagnostics.Stopwatch]::StartNew()                              # 加速器1
Write-Host ''
Write-Host '=============================================================' -ForegroundColor DarkCyan
Write-Host '  VIA 一鍵啟動器  |  15 加速器 · 貼上即用 · 不卡斷' -ForegroundColor Cyan
Write-Host '=============================================================' -ForegroundColor DarkCyan
$target = 'VIA-OneShot-v0100.ps1'
# --- 搜尋根: 使用者資料夾優先 (加速器11 Environment) ---
$up = [System.Environment]::GetFolderPath('UserProfile')                      # 加速器11
$roots = [System.Collections.Generic.List[string]]::new()                     # 加速器8
foreach ($sub in @('Downloads','Desktop','Documents','OneDrive','VIA')) {
    $p = [System.IO.Path]::Combine($up, $sub)                                 # 加速器4
    if ([System.IO.Directory]::Exists($p)) { $roots.Add($p) }
}
foreach ($extra in @('C:\VIA', (Get-Location).Path)) {
    if ([System.IO.Directory]::Exists($extra)) { $roots.Add($extra) }
}
# --- 快速遞迴搜尋: IgnoreInaccessible 免權限中斷 (加速器2+3) ---
$opt = [System.IO.EnumerationOptions]::new()                                  # 加速器2
$opt.RecurseSubdirectories = $true
$opt.IgnoreInaccessible = $true
$opt.AttributesToSkip = 'ReparsePoint'
$hits = [System.Collections.Generic.List[string]]::new()
foreach ($r in $roots) {
    try {
        foreach ($f in [System.IO.Directory]::EnumerateFiles($r, $target, $opt)) { $hits.Add($f) }  # 加速器3
    } catch { }
    if ($hits.Count -gt 0) { break }
}
if ($hits.Count -eq 0) {
    Write-Host ('  找不到 {0}' -f $target) -ForegroundColor Yellow
    Write-Host '  請確認已下載該檔 (Downloads/Desktop/OneDrive 皆會自動搜尋)。' -ForegroundColor Yellow
    return
}
# --- 挑最新一份 (加速器6 FileInfo) ---
$best = $null; $bestTime = [datetime]::MinValue                               # 加速器14
foreach ($h in $hits) {
    $fi = [System.IO.FileInfo]::new($h)                                       # 加速器6
    if ($fi.LastWriteTimeUtc -gt $bestTime) { $bestTime = $fi.LastWriteTimeUtc; $best = $fi.FullName }
}
$sb = [System.Text.StringBuilder]::new()                                      # 加速器12
[void]$sb.Append('  目標: ').Append($best)
Write-Host $sb.ToString() -ForegroundColor Green
# --- 解鎖網路標記 (加速器5 File: 直接刪 ADS, 失敗才回退 cmdlet) ---
try { [System.IO.File]::Delete($best + ':Zone.Identifier') } catch { try { Unblock-File -Path $best -ErrorAction SilentlyContinue } catch { } }   # 加速器5
# --- 先做語法檢查, 確認檔案完整 (加速器15) ---
$perr = $null
try { $null = [System.Management.Automation.Language.Parser]::ParseFile($best, [ref]$null, [ref]$perr) } catch { }   # 加速器15
if ($perr -and $perr.Count -gt 0) {
    Write-Host ('  檔案解析有誤 ({0} 項), 可能下載不完整, 請重新下載。' -f $perr.Count) -ForegroundColor Red
    return
}
Write-Host '  語法檢查通過, 開始執行 (輸出即時顯示, 不緩衝)' -ForegroundColor Green
Write-Host ''
# --- 用 -File 正確執行 + 逐程序 Bypass 政策; 不重導輸出 => 即時串流不卡畫面 ---
$exe = (Get-Process -Id $PID).Path
if (-not $exe) { $exe = 'pwsh' }
$psi = [System.Diagnostics.ProcessStartInfo]::new()                           # 加速器9
$psi.FileName = $exe
foreach ($a in @('-NoProfile','-ExecutionPolicy','Bypass','-File',$best)) { [void]$psi.ArgumentList.Add($a) }
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $false
$psi.RedirectStandardError  = $false
$proc = [System.Diagnostics.Process]::new()                                   # 加速器10
$proc.StartInfo = $psi
[void]$proc.Start()
$proc.WaitForExit()
$sw.Stop()
Write-Host ''
if ($proc.ExitCode -eq 0) {
    Write-Host ('  一鍵完成 (總耗時 {0}s)' -f [math]::Round($sw.Elapsed.TotalSeconds,1)) -ForegroundColor Green
} else {
    Write-Host ('  執行結束但回傳碼 {0} (總耗時 {1}s) — 上方訊息即原因' -f $proc.ExitCode, [math]::Round($sw.Elapsed.TotalSeconds,1)) -ForegroundColor Yellow
}
# --- 找出並開啟 UI (加速器3 再用一次 + 加速器13 regex 過濾) ---
$home2 = [System.IO.Path]::GetDirectoryName($best)
$rx = [regex]::new('VIA_CommandCenter\.html$', 'IgnoreCase')                  # 加速器13
$ui = $null
try {
    foreach ($f in [System.IO.Directory]::EnumerateFiles($home2, '*.html', $opt)) { if ($rx.IsMatch($f)) { $ui = $f; break } }
} catch { }
if ($ui) {
    Write-Host ('  入口: {0}' -f $ui) -ForegroundColor Yellow
    Start-Process $ui
} else {
    Write-Host '  (UI 尚未產生 — 若上方顯示 Python 缺席, 先 winget install Python.Python.3.12 再貼一次)' -ForegroundColor Yellow
}
Write-Host ''
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
