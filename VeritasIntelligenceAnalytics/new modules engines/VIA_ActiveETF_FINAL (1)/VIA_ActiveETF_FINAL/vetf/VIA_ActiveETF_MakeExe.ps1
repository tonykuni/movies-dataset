#requires -Version 7.0
# ============================================================================
# VIA_ActiveETF_MakeExe.ps1 — 整合封裝為「單一 EXE」(HTML PWA U/I)
#   自尋 VIA_ActiveETF_Console.html(含巢狀 vetf\vetf)→ 內嵌(+manifest/sw/icons)
#   編譯成 1 個 VIA_ActiveETF.exe：內建 localhost 微伺服器(SW/manifest 生效→可裝 PWA)，
#   以 Edge --app 開 app 視窗；視窗關閉即結束。無法起伺服器時自動退回 file:// app 視窗。
#   用法： & "…\VIA_ActiveETF_MakeExe.ps1"      （-Root 可指定來源；-Out 指定輸出 exe）
#   LL：param 頂部 / 全名函式 / [IO.File] / .Replace / 無 Start-Job
# ============================================================================
param(
    [string]$Root = "C:\Users\tonyk\OneDrive\Desktop\VeritasIntelligenceAnalytics\modules\vetf",
    [string]$Out  = ""
)
$ErrorActionPreference = "Stop"
function Write-Status { param([string]$Level,[string]$Message)
    $c = switch ($Level.ToUpper()) { "OK"{"Green"} "WARN"{"Yellow"} "FAIL"{"Red"} default{"Gray"} }
    Write-Host ("[{0}] {1}" -f $Level.ToUpper(), $Message) -ForegroundColor $c }

if (-not (Test-Path $Root)) { Write-Status FAIL "Root not found: $Root"; return }
# 自尋 Console.html（含巢狀）
$console = Get-ChildItem -LiteralPath $Root -Recurse -Depth 4 -File -Filter "VIA_ActiveETF_Console.html" -ErrorAction SilentlyContinue |
           Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $console) { Write-Status FAIL "找不到 VIA_ActiveETF_Console.html（請先放進 vetf）。"; return }
$srcDir = $console.Directory.FullName
Write-Status OK ("source = {0}" -f $srcDir)
if (-not $Out) { $Out = Join-Path $srcDir "VIA_ActiveETF.exe" }

# 收集可內嵌資產
$assets = [ordered]@{}
$assets["VIA_ActiveETF_Console.html"] = $console.FullName
foreach ($n in @("VIA_ActiveETF.webmanifest","sw.js","icon-192.png","icon-512.png")) {
    $p = Join-Path $srcDir $n; if (Test-Path $p) { $assets[$n] = $p }
}
Write-Status OK ("embedding {0} files: {1}" -f $assets.Count, ($assets.Keys -join ", "))

# 產生 base64 切塊
function Get-ChunkArray { param([string]$Path)
    $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($Path))
    $sb = [System.Text.StringBuilder]::new(); $len = 6000
    for ($i=0; $i -lt $b64.Length; $i += $len) { $n=[Math]::Min($len,$b64.Length-$i); [void]$sb.Append('"').Append($b64.Substring($i,$n)).Append('",') }
    return $sb.ToString()
}
$initSb = [System.Text.StringBuilder]::new()
foreach ($k in $assets.Keys) {
    [void]$initSb.AppendLine(('  FILES["{0}"] = string.Concat(new string[]{{ {1} }});' -f $k, (Get-ChunkArray $assets[$k])))
}
$initBody = $initSb.ToString()
$consoleChunks = Get-ChunkArray $assets["VIA_ActiveETF_Console.html"]

# ---- 完整版 C#（localhost 伺服器 → PWA）----
$csFull = @'
using System;using System.IO;using System.Net;using System.Text;using System.Diagnostics;using System.Collections.Generic;using System.Threading;
static class Program{
 static Dictionary<string,string> FILES = new Dictionary<string,string>();
 static void INIT(){
##INIT##
 }
 [STAThread] static void Main(){
  INIT();
  string profile = Path.Combine(Path.GetTempPath(), "via_edge_profile");
  string[] edges = { Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86)+"\\Microsoft\\Edge\\Application\\msedge.exe",
                     Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles)+"\\Microsoft\\Edge\\Application\\msedge.exe" };
  string edge = null; foreach (var e in edges) { if (File.Exists(e)) { edge = e; break; } }
  HttpListener listener = null; int port = 0; var rnd = new Random();
  for (int i=0;i<12 && listener==null;i++){ port=8810+rnd.Next(380); try{ var l=new HttpListener(); l.Prefixes.Add("http://localhost:"+port+"/"); l.Start(); listener=l; }catch{ listener=null; } }
  string url;
  if (listener!=null){ url="http://localhost:"+port+"/VIA_ActiveETF_Console.html"; var t=new Thread(()=>Serve(listener)); t.IsBackground=true; t.Start(); }
  else { string tmp=Path.Combine(Path.GetTempPath(),"VIA_ActiveETF_Console.html"); File.WriteAllBytes(tmp,Convert.FromBase64String(FILES["VIA_ActiveETF_Console.html"])); url="file:///"+tmp.Replace("\\","/"); }
  try{
   if (edge!=null){ var p=Process.Start(edge, "--app="+url+" --user-data-dir=\""+profile+"\" --window-size=1500,950 --no-first-run --no-default-browser-check"); p.WaitForExit(); }
   else { Process.Start(new ProcessStartInfo(url){ UseShellExecute=true }); Thread.Sleep(4000); }
  }catch{}
  if (listener!=null){ try{ listener.Stop(); }catch{} }
 }
 static void Serve(HttpListener l){
  var mime = new Dictionary<string,string>(){ {".html","text/html; charset=utf-8"},{".js","text/javascript"},{".png","image/png"},{".webmanifest","application/manifest+json"},{".json","application/json"} };
  while (l.IsListening){
   HttpListenerContext c; try{ c=l.GetContext(); }catch{ break; }
   string path = Uri.UnescapeDataString(c.Request.Url.AbsolutePath).TrimStart('/'); if (path.Length==0) path="VIA_ActiveETF_Console.html";
   try{
    if (FILES.ContainsKey(path)){ byte[] b=Convert.FromBase64String(FILES[path]); string ext=Path.GetExtension(path).ToLower(); c.Response.ContentType = mime.ContainsKey(ext)?mime[ext]:"application/octet-stream"; c.Response.ContentLength64=b.Length; c.Response.OutputStream.Write(b,0,b.Length); }
    else { c.Response.StatusCode=404; }
   }catch{}
   try{ c.Response.OutputStream.Close(); }catch{}
  }
 }
}
'@
$csFull = $csFull.Replace('##INIT##', $initBody)

# ---- 簡版 C#（file:// app 視窗，保證可編譯）----
$csSimple = @'
using System;using System.IO;using System.Diagnostics;
static class Program{
 static string[] P = new string[]{ ##CHUNKS## };
 [STAThread] static void Main(){
  try{
   byte[] d = Convert.FromBase64String(string.Concat(P));
   string tmp = Path.Combine(Path.GetTempPath(), "VIA_ActiveETF_Console.html"); File.WriteAllBytes(tmp, d);
   string url = "file:///" + tmp.Replace("\\","/");
   string[] edges = { Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86)+"\\Microsoft\\Edge\\Application\\msedge.exe",
                      Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles)+"\\Microsoft\\Edge\\Application\\msedge.exe" };
   foreach (var e in edges){ if (File.Exists(e)){ Process.Start(e, "--app="+url+" --window-size=1500,950"); return; } }
   Process.Start(new ProcessStartInfo(tmp){ UseShellExecute=true });
  }catch(Exception ex){ Console.Error.WriteLine(ex.Message); }
 }
}
'@
$csSimple = $csSimple.Replace('##CHUNKS##', $consoleChunks)

if (Test-Path $Out) { Remove-Item $Out -Force }
$built = $false
try {
    Write-Status INFO "compiling PWA exe (localhost server)…"
    Add-Type -OutputAssembly $Out -OutputType WindowsApplication -TypeDefinition $csFull -ReferencedAssemblies @("System.Net.HttpListener","System.Net.Primitives","System.Threading.Thread") -ErrorAction Stop
    $built = $true; Write-Status OK "PWA exe compiled."
} catch {
    Write-Status WARN ("PWA 編譯失敗，退回 app 視窗版：{0}" -f $_.Exception.Message)
    try { Add-Type -OutputAssembly $Out -OutputType WindowsApplication -TypeDefinition $csSimple -ErrorAction Stop; $built=$true; Write-Status OK "app-window exe compiled." }
    catch { Write-Status FAIL ("EXE 編譯失敗：{0}" -f $_.Exception.Message) }
}
if ($built -and (Test-Path $Out)) {
    Write-Status OK ("DONE → {0}  ({1:N0} KB)  雙擊即開" -f $Out, ((Get-Item $Out).Length/1KB))
    Write-Status INFO "PWA：開啟後若用 localhost，Edge 網址列會出現『安裝』；關閉視窗 exe 即結束。"
} else { Write-Status WARN "未產生 EXE；可改用 dist\Console.html 或 VIA_ActiveETF.ps1 啟動。" }
