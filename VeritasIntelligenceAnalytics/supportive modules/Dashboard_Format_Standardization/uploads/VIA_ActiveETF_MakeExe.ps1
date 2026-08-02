#Requires -Version 7.0
# =============================================================================
# VIA_ActiveETF — Route B：編譯成 VIA_ActiveETF.exe（內嵌 AIO + 狼盾圖示 + 無黑窗）
# 做的事：找最新封裝 AIO → base64 內嵌進 C# WinExe → 取 .ico → csc 編譯(/win32icon)
#         → EXE 雙擊：解出 ps1 到 %TEMP% → 隱藏起 pwsh server → 等 health → 開 Edge --app
# 跑法：pwsh -ExecutionPolicy Bypass -File "本檔路徑"
# 注意：未簽章 EXE 可能被 SmartScreen/Defender 警告（見文末說明）。
# =============================================================================
[CmdletBinding(PositionalBinding=$false)]
param(
    [string]$PackageRoot = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\_packages",
    [string]$DeployDir   = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\_deploy\VIA_ActiveETF",
    [int]$Port = 8787,
    [string]$IpAddr = "127.0.0.1",
    [switch]$NoTest
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$AioLeaf = "Run_VIA_ActiveETF_Sealed_AIO_B.ps1"

function L {
    param([string]$Level,[string]$Message)
    $ts = Get-Date -Format "HH:mm:ss.fff"
    $color = switch ($Level) { "OK"{"Green"} "WARN"{"Yellow"} "FAIL"{"Red"} "INFO"{"Cyan"} "RUN"{"White"} default{"Gray"} }
    Write-Host "[$ts] [$Level] $Message" -ForegroundColor $color
}

function Get-LatestAio {
    if (-not (Test-Path -LiteralPath $PackageRoot)) { return $null }
    $hit = @(Get-ChildItem -LiteralPath $PackageRoot -Recurse -Filter $AioLeaf -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending)
    if ($hit.Count -gt 0) { return $hit[0].FullName }
    return $null
}

function Resolve-Ico {
    param([string]$OutDir)
    $existing = Join-Path $DeployDir "VIA.ico"
    if (Test-Path -LiteralPath $existing) {
        $dst = Join-Path $OutDir "VIA.ico"; Copy-Item -LiteralPath $existing -Destination $dst -Force
        L "OK" "使用既有 VIA.ico"; return $dst
    }
    foreach ($png in @("icon-512.png","VIA_logo.png","icon-192.png")) {
        $src = Join-Path $DeployDir $png
        if (Test-Path -LiteralPath $src) {
            try {
                Add-Type -AssemblyName System.Drawing -ErrorAction Stop
                $img = [System.Drawing.Image]::FromFile($src)
                $bmp = New-Object System.Drawing.Bitmap($img, 256, 256)
                $icon = [System.Drawing.Icon]::FromHandle($bmp.GetHicon())
                $dst = Join-Path $OutDir "VIA.ico"
                $fs = [System.IO.File]::Create($dst); $icon.Save($fs); $fs.Close()
                $img.Dispose(); $bmp.Dispose()
                L "OK" ("由 " + $png + " 產生 VIA.ico"); return $dst
            } catch { L "WARN" ("PNG 轉 ico 失敗: " + $_.Exception.Message) }
        }
    }
    L "WARN" "找不到圖示，EXE 將用預設圖示。"; return $null
}

function Resolve-Csc {
    foreach ($p in @(
        (Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"),
        (Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe")
    )) { if (Test-Path -LiteralPath $p) { return $p } }
    return $null
}

# =============================================================================
function Main {
    Write-Host ""
    Write-Host "============ VIA Active ETF — Route B：EXE ============" -ForegroundColor Cyan

    $aio = Get-LatestAio
    if (-not $aio) { throw "找不到封裝 AIO ($AioLeaf)。請先跑 VIA_ActiveETF_SealedAIO_Build.ps1。" }
    L "OK" ("使用最新 AIO: " + $aio)

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $runDir = Join-Path $PackageRoot ("VIA_ActiveETF_EXE_" + $stamp)
    if (-not (Test-Path -LiteralPath $runDir)) { New-Item -ItemType Directory -Path $runDir -Force | Out-Null }

    $ico = Resolve-Ico -OutDir $runDir

    L "RUN" "讀取 AIO 並 base64 內嵌..."
    $aioBytes = [IO.File]::ReadAllBytes($aio)
    $aioB64 = [Convert]::ToBase64String($aioBytes)
    $url = "http://" + $IpAddr + ":" + [string]$Port + "/"
    $health = "http://" + $IpAddr + ":" + [string]$Port + "/health.json"

    # ---- C# WinExe 原始碼（單引號 heredoc + token 取代）----
    $csTpl = @'
using System;
using System.IO;
using System.Net;
using System.Diagnostics;
using System.Threading;
using System.Windows.Forms;

namespace VIA {
  static class Program {
    [STAThread]
    static void Main() {
      try {
        string b64 = "@@PS1B64@@";
        string url = "@@URL@@";
        string health = "@@HEALTH@@";

        string tempDir = Path.Combine(Path.GetTempPath(), "VIA_ActiveETF_Run");
        Directory.CreateDirectory(tempDir);
        string ps1 = Path.Combine(tempDir, "Run_VIA_ActiveETF_Sealed_AIO_B.ps1");
        File.WriteAllBytes(ps1, Convert.FromBase64String(b64));

        if (!IsUp(health)) {
          string pwsh = FindPwsh();
          ProcessStartInfo psi = new ProcessStartInfo(pwsh,
            "-NoLogo -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File \"" + ps1 + "\"");
          psi.UseShellExecute = false;
          psi.CreateNoWindow = true;
          try { Process.Start(psi); }
          catch (Exception) {
            MessageBox.Show("找不到或無法啟動 PowerShell 7。請先安裝 PowerShell 7。", "Veritas Active ETF");
            return;
          }
          for (int i = 0; i < 60; i++) { Thread.Sleep(500); if (IsUp(health)) break; }
        }

        if (IsUp(health)) { OpenApp(url); }
        else { MessageBox.Show("啟動逾時，請再雙擊一次。", "Veritas Active ETF"); }
      }
      catch (Exception ex) {
        MessageBox.Show("啟動失敗：" + ex.Message, "Veritas Active ETF");
      }
    }

    static bool IsUp(string url) {
      try {
        HttpWebRequest req = (HttpWebRequest)WebRequest.Create(url);
        req.Timeout = 1500;
        req.Proxy = null;
        using (HttpWebResponse r = (HttpWebResponse)req.GetResponse()) {
          return (int)r.StatusCode == 200;
        }
      } catch { return false; }
    }

    static string FindPwsh() {
      string pf = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
      string p = Path.Combine(pf, "PowerShell\\7\\pwsh.exe");
      if (File.Exists(p)) return p;
      return "pwsh.exe";
    }

    static void OpenApp(string url) {
      string pfx86 = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86);
      string pf = Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles);
      string[] edges = new string[] {
        Path.Combine(pfx86, "Microsoft\\Edge\\Application\\msedge.exe"),
        Path.Combine(pf, "Microsoft\\Edge\\Application\\msedge.exe")
      };
      foreach (string e in edges) {
        if (File.Exists(e)) {
          Process.Start(e, "--app=" + url + " --window-size=1500,950");
          return;
        }
      }
      ProcessStartInfo psi = new ProcessStartInfo(url);
      psi.UseShellExecute = true;
      Process.Start(psi);
    }
  }
}
'@
    $cs = $csTpl.Replace('@@PS1B64@@', $aioB64).Replace('@@URL@@', $url).Replace('@@HEALTH@@', $health)
    $csPath = Join-Path $runDir "VIA_ActiveETF_Launcher.cs"
    [IO.File]::WriteAllText($csPath, $cs, [System.Text.UTF8Encoding]::new($false))
    L "OK" ("C# 原始碼已寫: " + $csPath)

    $exe = Join-Path $runDir "VIA_ActiveETF.exe"
    $csc = Resolve-Csc

    $built = $false
    if ($csc) {
        L "RUN" "用 csc 編譯（含 /win32icon 圖示）..."
        $cscArgs = @("/nologo","/target:winexe","/out:$exe")
        if ($ico) { $cscArgs += "/win32icon:$ico" }
        $cscArgs += @("/r:System.dll","/r:System.Windows.Forms.dll",$csPath)
        $p = Start-Process -FilePath $csc -ArgumentList $cscArgs -NoNewWindow -PassThru -Wait
        if ($p.ExitCode -eq 0 -and (Test-Path -LiteralPath $exe)) { $built = $true; L "OK" "csc 編譯成功(含圖示)" }
        else { L "WARN" ("csc 失敗 (ExitCode=" + $p.ExitCode + ")，改用 Add-Type 後備（無圖示）") }
    }
    else { L "WARN" "找不到 csc.exe，改用 Add-Type 後備（無圖示）" }

    if (-not $built) {
        try {
            Add-Type -OutputAssembly $exe -OutputType WindowsApplication `
                -ReferencedAssemblies @("System.Windows.Forms") `
                -TypeDefinition $cs -Language CSharp -ErrorAction Stop
            if (Test-Path -LiteralPath $exe) { $built = $true; L "OK" "Add-Type 編譯成功（無內嵌圖示，捷徑/工作列圖示仍可另設）" }
        } catch { L "FAIL" ("Add-Type 也失敗: " + $_.Exception.Message) }
    }

    if (-not $built) { throw "EXE 編譯失敗" }

    $sz = (Get-Item -LiteralPath $exe).Length
    Write-Host ""
    Write-Host "==================== DONE ====================" -ForegroundColor Cyan
    Write-Host ("EXE: " + $exe) -ForegroundColor Green
    Write-Host ("大小: " + [math]::Round($sz/1MB,2) + " MB")
    Write-Host ""
    Write-Host "雙擊 EXE → 背景起 server → Edge --app 視窗開啟（無 Edge 退回預設瀏覽器）" -ForegroundColor Cyan
    Write-Host "密碼: tonyissohot" -ForegroundColor Yellow

    if (-not $NoTest) {
        Write-Host ""
        L "RUN" "測試啟動 EXE..."
        Start-Process -FilePath $exe
        $ok = $false
        for ($i = 0; $i -lt 60; $i++) {
            Start-Sleep -Milliseconds 500
            Write-Progress -Id 1 -Activity "測試 EXE" -Status ("等待 server... " + [int]($i*0.5) + "s") -PercentComplete (($i*3) % 100)
            try { $r = Invoke-WebRequest -Uri $health -UseBasicParsing -NoProxy -TimeoutSec 2; if ($r.StatusCode -eq 200) { $ok = $true; break } } catch {}
        }
        Write-Progress -Id 1 -Activity "done" -Completed
        if ($ok) { L "OK" "EXE 可正常啟動 server，視窗應已開啟登入頁。" }
        else { L "WARN" "測試逾時，請手動雙擊 EXE 確認（首次可能被 SmartScreen 攔，見下方說明）。" }
    }

    Write-Host ""
    Write-Host "── SmartScreen / Defender 說明 ──" -ForegroundColor DarkCyan
    Write-Host "未簽章 EXE 首次執行可能跳『Windows 已保護你的電腦』："
    Write-Host "  點『更多資訊』→『仍要執行』即可。這是正常現象（你自製、未買憑證）。"
    Write-Host "若要免警告，需購買 code-signing 憑證對 EXE 簽章。給別人用時務必先提醒這一步。"
}

try { Main }
catch {
    L "FAIL" $_.Exception.Message
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}
finally {
    Write-Progress -Id 1 -Activity "done" -Completed
    Write-Host ""
    Write-Host "完成。" -ForegroundColor Cyan
}
