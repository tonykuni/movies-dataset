#requires -Version 7.0
# ============================================================================
# VIA_ActiveETF_Pack.ps1  —  一支 PowerShell：INTEGRATE + COPY + PACK→EXE (+PWA)
# ----------------------------------------------------------------------------
#  INTEGRATE : 盤點 vetf 5 檔；檢查輔助工具是否需掛入；可選 -Sync 先用 PY 重建最新 Console
#  COPY      : 組裝 dist\（Console + PWA 資產：manifest / sw / icons）
#  PACK→EXE  : 用 .NET 把 Console.html 內嵌、編譯成單一 VIA_ActiveETF.exe
#              （執行時寫入 %TEMP% 並以 Edge --app 視窗開啟，無則退回預設瀏覽器）
#  PWA       : 同時輸出可「安裝」的 PWA 資產（http 提供時 service worker 生效）
#  LL：param 頂部 / 全名函式 / py 啟動器 / .Replace(LL#34) / [IO.File] / 無 Start-Job
# ============================================================================
param(
    [string]$Root = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\modules\vetf",
    [string]$ModulesDir = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\modules\supportive modules",
    [string]$Dist = "",
    [switch]$Sync,
    [switch]$SyncBundle,
    [switch]$NoExe
)

$script:Core = @("VIA_ActiveETF_System.py","console_merged_template.html","VIA_ActiveETF.ps1","VIA_ActiveETF_Console.html","VIA_ActiveETF_PackList.json")
$script:Used = @("VeritasAegisNexus.py","VeritasCeleritas.py","VIA_EnvManager.py","VIA_SSOT_Unified.py")

function Write-Status { param([string]$Level,[string]$Message)
    Write-Host ("[{0}][{1}] {2}" -f (Get-Date -Format "HH:mm:ss"), $Level.ToUpper(), $Message) }
function Find-Python {
    foreach ($v in @("3.12","3.11","3.13")) { try { & py "-$v" -c "import sys" 2>$null; if ($LASTEXITCODE -eq 0) { return @("py","-$v") } } catch {} }
    try { & python -c "import sys" 2>$null; if ($LASTEXITCODE -eq 0) { return @("python") } } catch {}
    return $null
}

# ---------- INTEGRATE ----------
if (-not (Test-Path $Root)) { Write-Status FAIL "找不到 vetf 資料夾：$Root"; exit 1 }
Write-Status INFO ("Root = {0}" -f $Root)
$missing = @($script:Core | Where-Object { -not (Test-Path (Join-Path $Root $_)) })
if ($missing.Count) { foreach ($m in $missing) { Write-Status WARN "缺核心檔：$m" } }

Write-Status INFO "—— 輔助工具掛入評估 ——"
Write-Status OK  "UI EXE / Console.html 為自帶資料的單檔（內嵌 perf/hold/logo）→ 執行期【不需】掛入任何輔助工具。"
$haveUsed = @($script:Used | Where-Object { (Test-Path (Join-Path $ModulesDir $_)) -or (Test-Path (Join-Path $Root $_)) })
Write-Status INFO ("若要 EXE 內可【重新 sync 抓資料】，才需 Python + 4 支：{0}（現有 {1}/4）" -f ($script:Used -join ", "), $haveUsed.Count)

if (-not $Dist) { $Dist = Join-Path $Root "dist" }
if (-not (Test-Path $Dist)) { New-Item -ItemType Directory -Path $Dist -Force | Out-Null }
Write-Status OK ("Dist = {0}" -f $Dist)

# ---------- 可選：先 SYNC 重建最新 Console ----------
$consoleSrc = Join-Path $Root "VIA_ActiveETF_Console.html"
if ($Sync) {
    $py = Find-Python; $tpl = Join-Path $Root "console_merged_template.html"; $sys = Join-Path $Root "VIA_ActiveETF_System.py"
    if ($py -and (Test-Path $tpl) -and (Test-Path $sys)) {
        Write-Status INFO "SYNC：用 PY 重建最新 Console..."
        $logo = Join-Path $Root "VIA_logo.png"; $a = @($sys,"sync","--templates",$Root,"--out",$Root)
        if (Test-Path $logo) { $a += @("--logo",$logo) }
        & $py[0] ($py[1..($py.Count-1)] + $a); if ($LASTEXITCODE -eq 0) { Write-Status OK "Console 已重建。" } else { Write-Status WARN "sync 非零，沿用現有 Console。" }
    } else { Write-Status WARN "缺 Python/模板，略過 sync。" }
}
if (-not (Test-Path $consoleSrc)) { Write-Status FAIL "找不到 Console.html"; exit 1 }

# ---------- COPY：Console + PWA 資產 ----------
Copy-Item -LiteralPath $consoleSrc -Destination (Join-Path $Dist "VIA_ActiveETF_Console.html") -Force

# manifest
$manifest = @'
{ "name":"VIA Active ETF Console","short_name":"VIA ETF","start_url":"VIA_ActiveETF_Console.html","scope":"./",
  "display":"standalone","background_color":"#f5f4f0","theme_color":"#4c78a8",
  "icons":[{"src":"icon-192.png","sizes":"192x192","type":"image/png","purpose":"any maskable"},
           {"src":"icon-512.png","sizes":"512x512","type":"image/png","purpose":"any maskable"}] }
'@
[IO.File]::WriteAllText((Join-Path $Dist "VIA_ActiveETF.webmanifest"), $manifest, [System.Text.UTF8Encoding]::new($false))
# service worker
$sw = @'
const CACHE="via-active-etf-v1";
const ASSETS=["VIA_ActiveETF_Console.html","icon-192.png","icon-512.png","VIA_ActiveETF.webmanifest"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting()));});
self.addEventListener("activate",e=>{e.waitUntil(self.clients.claim());});
self.addEventListener("fetch",e=>{e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request).catch(()=>r)));});
'@
[IO.File]::WriteAllText((Join-Path $Dist "sw.js"), $sw, [System.Text.UTF8Encoding]::new($false))
Write-Status OK "PWA 資產輸出：VIA_ActiveETF.webmanifest, sw.js"

# icons：先複製現有，無則由 VIA_logo.png 以 GDI+ 產生
function New-Icon { param([string]$LogoPath,[int]$Size,[string]$OutPath)
    Add-Type -AssemblyName System.Drawing -ErrorAction Stop
    $img = [System.Drawing.Image]::FromFile($LogoPath)
    $bmp = New-Object System.Drawing.Bitmap($Size,$Size)
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.Clear([System.Drawing.Color]::FromArgb(255,28,30,36))
    $m = [int]($Size*0.80); $r = [Math]::Min($m/$img.Width, $m/$img.Height); $w=[int]($img.Width*$r); $h=[int]($img.Height*$r)
    $g.DrawImage($img, [int](($Size-$w)/2), [int](($Size-$h)/2), $w, $h)
    $bmp.Save($OutPath, [System.Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose(); $img.Dispose()
}
foreach ($sz in 192,512) {
    $name = "icon-$sz.png"; $dest = Join-Path $Dist $name
    if (Test-Path (Join-Path $Root $name)) { Copy-Item (Join-Path $Root $name) $dest -Force }
    elseif (Test-Path (Join-Path $Root "VIA_logo.png")) { try { New-Icon -LogoPath (Join-Path $Root "VIA_logo.png") -Size $sz -OutPath $dest; Write-Status OK "icon 產生：$name" } catch { Write-Status WARN "icon 產生失敗（$name）：$($_.Exception.Message)" } }
    else { Write-Status WARN "缺 $name 與 VIA_logo.png，PWA 圖示略過。" }
}
# 可選：sync bundle（讓 dist 也能重抓資料）
if ($SyncBundle) {
    foreach ($f in @("VIA_ActiveETF_System.py","console_merged_template.html","VIA_ActiveETF.ps1","VIA_logo.png")) { if (Test-Path (Join-Path $Root $f)) { Copy-Item (Join-Path $Root $f) (Join-Path $Dist $f) -Force } }
    foreach ($u in $script:Used) { $s = if (Test-Path (Join-Path $ModulesDir $u)) { Join-Path $ModulesDir $u } elseif (Test-Path (Join-Path $Root $u)) { Join-Path $Root $u } else { $null }; if ($s) { Copy-Item $s (Join-Path $Dist $u) -Force } }
    Write-Status OK "SyncBundle：System.py + 模板 + ps1 + 4 支輔助工具已併入 dist。"
}

# ---------- PACK → EXE（.NET 編譯，內嵌 Console）----------
if ($NoExe) { Write-Status OK "NoExe：完成打包（dist 內含 Console + PWA）。"; exit 0 }
Write-Status INFO "PACK：內嵌 Console → 編譯 EXE..."
$bytes = [IO.File]::ReadAllBytes($consoleSrc)
$b64 = [Convert]::ToBase64String($bytes)
# 切塊避免單一字串字面量過長
$chunkLen = 6000; $sb = New-Object System.Text.StringBuilder
for ($i=0; $i -lt $b64.Length; $i += $chunkLen) {
    $len = [Math]::Min($chunkLen, $b64.Length - $i)
    [void]$sb.Append('"').Append($b64.Substring($i,$len)).Append('",')
}
$chunks = $sb.ToString()
$cs = @'
using System;using System.IO;using System.Diagnostics;
static class Program{
 static string[] P = new string[]{ ##CHUNKS## };
 [STAThread] static void Main(){
  try{
   string b64 = string.Concat(P);
   byte[] data = Convert.FromBase64String(b64);
   string tmp = Path.Combine(Path.GetTempPath(), "VIA_ActiveETF_Console.html");
   File.WriteAllBytes(tmp, data);
   string url = "file:///" + tmp.Replace("\\", "/");
   string[] edges = {
     Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86) + "\\Microsoft\\Edge\\Application\\msedge.exe",
     Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles) + "\\Microsoft\\Edge\\Application\\msedge.exe" };
   foreach (var ex in edges) { if (File.Exists(ex)) { Process.Start(ex, "--app=" + url + " --window-size=1500,950"); return; } }
   Process.Start(new ProcessStartInfo(tmp){ UseShellExecute = true });
  } catch (Exception e) { Console.Error.WriteLine(e.Message); }
 }
}
'@
$cs = $cs.Replace('##CHUNKS##', $chunks)
$exe = Join-Path $Dist "VIA_ActiveETF.exe"
try {
    Add-Type -OutputAssembly $exe -OutputType WindowsApplication -TypeDefinition $cs -Language CSharp -ErrorAction Stop
    Write-Status OK ("EXE 完成：{0}（{1:N0} KB，自帶 UI，雙擊即開）" -f $exe, ((Get-Item $exe).Length/1KB))
} catch {
    Write-Status WARN ("Add-Type 編譯失敗：{0}" -f $_.Exception.Message)
    Write-Status INFO "退路：dist 內 Console.html 可直接雙擊；或用 VIA_ActiveETF.ps1 啟動。"
}
Write-Status OK "DONE：dist 內含 VIA_ActiveETF.exe + Console + PWA(manifest/sw/icons)。"
Write-Status INFO "PWA 安裝：以 http 提供 dist（如 'py -m http.server'）後用 Edge/Chrome 開 Console → 網址列『安裝』。"
exit 0
