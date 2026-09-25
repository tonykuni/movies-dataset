#requires -Version 7.0
# ============================================================================
# VIA_ActiveETF_MakeLauncher.ps1 — 瘦啟動器 EXE（不內嵌資料 / 不開連接埠 / 防誤判）
#   產出 VIA_ActiveETF.exe：執行時只用 Edge --app 開「同資料夾的 VIA_ActiveETF_Console.html」
#   找不到 Edge → 用預設瀏覽器開該 HTML。行為單純，最不易被 Defender/SmartScreen 啟發式攔。
#   ※ EXE 旁需保留 VIA_ActiveETF_Console.html（自帶資料的單檔 UI）。
#   用 .NET Framework csc.exe 編譯（PS7 的 Add-Type 不支援 -OutputType）。
#   用法： & "…\VIA_ActiveETF_MakeLauncher.ps1"   （-Root 來源夾；-Out 輸出 exe；-Icon 圖示.ico）
# ============================================================================
param(
    [string]$Root = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\modules\vetf",
    [string]$Out  = "",
    [string]$Icon = ""
)
$ErrorActionPreference = "Stop"
function Write-Status { param([string]$Level,[string]$Message)
    $c = switch ($Level.ToUpper()) { "OK"{"Green"} "WARN"{"Yellow"} "FAIL"{"Red"} default{"Gray"} }
    Write-Host ("[{0}] {1}" -f $Level.ToUpper(), $Message) -ForegroundColor $c }

if (-not (Test-Path $Root)) { Write-Status FAIL "Root not found: $Root"; return }
$console = Get-ChildItem -LiteralPath $Root -Recurse -Depth 4 -File -Filter "VIA_ActiveETF_Console.html" -ErrorAction SilentlyContinue |
           Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $console) { Write-Status FAIL "找不到 VIA_ActiveETF_Console.html。"; return }
$srcDir = $console.Directory.FullName
Write-Status OK ("console = {0}" -f $console.FullName)
if (-not $Out) { $Out = Join-Path $srcDir "VIA_ActiveETF.exe" }

# 瘦啟動器：執行檔旁找 Console.html（找不到再往子層找一層），用 Edge --app 開；無 Edge 用 ShellExecute
$cs = @'
using System;using System.IO;using System.Diagnostics;
static class Program{
 static string Find(string dir){
  string f = Path.Combine(dir, "VIA_ActiveETF_Console.html");
  if (File.Exists(f)) return f;
  try { foreach (string d in Directory.GetDirectories(dir)) { string g = Path.Combine(d, "VIA_ActiveETF_Console.html"); if (File.Exists(g)) return g; } } catch {}
  return null;
 }
 [STAThread] static void Main(){
  try{
   string baseDir = AppDomain.CurrentDomain.BaseDirectory;
   string html = Find(baseDir);
   if (html == null) { return; }
   string url = "file:///" + Path.GetFullPath(html).Replace("\\", "/");
   string[] edges = { Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86)+"\\Microsoft\\Edge\\Application\\msedge.exe",
                      Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles)+"\\Microsoft\\Edge\\Application\\msedge.exe" };
   foreach (string e in edges){ if (File.Exists(e)){ Process.Start(e, "--app=" + url + " --window-size=1500,950"); return; } }
   Process.Start(new ProcessStartInfo(url){ UseShellExecute = true });
  }catch(Exception ex){ Console.Error.WriteLine(ex.Message); }
 }
}
'@
$csFile = Join-Path $env:TEMP "VIA_ActiveETF_launcher.cs"
[IO.File]::WriteAllText($csFile, $cs, [System.Text.UTF8Encoding]::new($false))

function Find-Csc {
    @("$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe","$env:WINDIR\Microsoft.NET\Framework\v4.0.30319\csc.exe") |
        Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (Test-Path $Out) { Remove-Item $Out -Force }
$csc = Find-Csc
if (-not $csc) { Write-Status FAIL "找不到 .NET Framework csc.exe。"; return }
Write-Status INFO ("compiling launcher via csc: {0}" -f $csc)
$cscArgs = @("/nologo","/target:winexe","/optimize+","/out:$Out","/reference:System.dll")
if ($Icon -and (Test-Path $Icon)) { $cscArgs += "/win32icon:$Icon" }
$cscArgs += $csFile
& $csc @cscArgs 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0 -and (Test-Path $Out)) {
    Write-Status OK ("DONE → {0}  ({1:N0} KB) 瘦啟動器" -f $Out, ((Get-Item $Out).Length/1KB))
    Write-Status INFO "EXE 旁請保留 VIA_ActiveETF_Console.html；雙擊 EXE 即以 Edge app 視窗開啟。"
    Write-Status INFO "若仍被誤判：把整夾移出 OneDrive（如 C:\\VIA\\vetf），或在 Defender 排除該資料夾。"
} else { Write-Status FAIL "編譯失敗。可改直接雙擊 VIA_ActiveETF_Console.html。" }

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
