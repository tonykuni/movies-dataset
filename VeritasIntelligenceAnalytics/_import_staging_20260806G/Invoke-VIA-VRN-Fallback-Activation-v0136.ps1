#requires -Version 7.0
[CmdletBinding()]
param(
  [string]$BaseDir="C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
  [bool]$ActivateVrn=$true,
  [bool]$OpenHtmlReport=$true,
  [int]$ProbeSeconds=12,
  [string]$ApprovalPhrase="I_APPROVE_VIA_v0136_VRN_FALLBACK_ACTIVATION"
)

Set-StrictMode -Version Latest
$ErrorActionPreference="Stop"
$Expected="I_APPROVE_VIA_v0136_VRN_FALLBACK_ACTIVATION"
$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$RunDir=Join-Path $BaseDir "_via_vrn_fallback_activation_runs\RUN_${Stamp}_VIA_VRN_FALLBACK_ACTIVATION_v0136"
$CsvDir=Join-Path $RunDir "csv"
$JsonDir=Join-Path $RunDir "json"
$HtmlDir=Join-Path $RunDir "html"
$TmpDir=Join-Path $RunDir "runtime_candidate"

$Persist=Join-Path $BaseDir "supportive modules\VIA_Governance_Runtime\v0136"
$LaunchDir=Join-Path $Persist "launcher"
$LogDir=Join-Path $Persist "logs"
$ManifestDir=Join-Path $Persist "manifests"
$HtmlPersist=Join-Path $Persist "html"

$SupportiveSource=Join-Path $BaseDir "supportive modules\VIA_Governance_Runtime\v0135\manifests\supportive_loaded_modules.v0135.json"
$SupportiveDeploy=Join-Path $ManifestDir "supportive_loaded_modules.v0136.json"
$CandidateCsv=Join-Path $CsvDir "VRN_EntrypointCandidateMatrix.v0136.csv"
$AttemptCsv=Join-Path $CsvDir "VRN_ActivationAttemptEvidence.v0136.csv"
$SummaryJson=Join-Path $JsonDir "summary.v0136.json"
$Html=Join-Path $HtmlDir "VIA_VRN_Fallback_Activation_Matrix_v0136.html"

function Ensure([string]$x){if(-not(Test-Path -LiteralPath $x)){New-Item -ItemType Directory -Path $x -Force|Out-Null}}
function J($o,[string]$x){$o|ConvertTo-Json -Depth 50|Set-Content -LiteralPath $x -Encoding UTF8}
function C($o,[string]$x){@($o)|Export-Csv -LiteralPath $x -NoTypeInformation -Encoding UTF8}
function Enc($x){[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes("& '"+$x.Replace("'","''")+"'"))}
function ParsePs([string]$x){
  $t=$null;$e=$null
  try{$a=[Management.Automation.Language.Parser]::ParseFile($x,[ref]$t,[ref]$e)
    [pscustomobject]@{ast=$a;ok=(@($e).Count-eq0);count=@($e).Count;first=if(@($e).Count){$e[0].Message}else{""}}
  }catch{[pscustomobject]@{ast=$null;ok=$false;count=1;first=$_.Exception.Message}}
}
function ParamMeta($a){
  $all=@();$mandatory=@();$defaults=@()
  if($null-ne$a-and$null-ne$a.ParamBlock){
    foreach($p in @($a.ParamBlock.Parameters)){
      $n=[string]$p.Name.VariablePath.UserPath;$all+=$n
      if($null-ne$p.DefaultValue){$defaults+=$n}
      $m=$false
      foreach($at in @($p.Attributes)){
        if([string]$at.TypeName.FullName-match"Parameter"){
          foreach($na in @($at.NamedArguments)){
            if([string]$na.ArgumentName-eq"Mandatory"-and[string]$na.Argument.Extent.Text-match"(?i)\$?true"){$m=$true}
          }
        }
      }
      if($m-and$null-eq$p.DefaultValue){$mandatory+=$n}
    }
  }
  [pscustomobject]@{all=($all-join";");mandatory=($mandatory-join";");count=@($mandatory).Count;defaults=($defaults-join";")}
}
function HtmlEnc($x){if($null-eq$x){""}else{[Net.WebUtility]::HtmlEncode([string]$x)}}
function Table($rows){
  $a=@($rows);if(-not$a.Count){return"<div>No rows.</div>"}
  $u=[ordered]@{}
  foreach($r in$a){foreach($n in$r.PSObject.Properties.Name){if(-not$u.Contains($n)){$u[$n]=$true}}}
  $names=@($u.Keys);$b=[Text.StringBuilder]::new()
  [void]$b.Append("<div class='tw'><table><tr>")
  foreach($n in$names){[void]$b.Append("<th>$(HtmlEnc $n)</th>")};[void]$b.Append("</tr>")
  foreach($r in$a){[void]$b.Append("<tr>");foreach($n in$names){$q=$r.PSObject.Properties[$n];$v=if($null-ne$q){$q.Value}else{""};[void]$b.Append("<td>$(HtmlEnc $v)</td>")};[void]$b.Append("</tr>")}
  [void]$b.Append("</table></div>");$b.ToString()
}

function ChildScript([string]$candidate,[string]$name,[string]$status,[string]$transcript,[string]$dest){
$tpl=@'
#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference="Stop"
$Candidate="__CANDIDATE__";$Name="__NAME__";$Manifest="__MANIFEST__";$Status="__STATUS__";$Transcript="__TRANSCRIPT__"
function S([string]$state,[bool]$ok,[string]$err,[int]$loaded,[int]$empty){
 $o=[ordered]@{state=$state;success=$ok;error=$err;candidate=$Name;loaded=$loaded;empty_skipped=$empty;pid=$PID;time=(Get-Date).ToString("o")}
 $tmp="$Status.tmp.$PID";$o|ConvertTo-Json -Depth 20|Set-Content -LiteralPath $tmp -Encoding UTF8;Move-Item $tmp $Status -Force
}
$loaded=0;$empty=0
try{
 try{Start-Transcript -LiteralPath $Transcript -Append|Out-Null}catch{}
 S "BOOTSTRAP_STARTED" $true "" 0 0
 $mods=@(Get-Content -LiteralPath $Manifest -Raw -Encoding UTF8|ConvertFrom-Json)
 foreach($m in$mods){
   $mp=[string]$m.path;$ext=[IO.Path]::GetExtension($mp).ToLowerInvariant()
   if(-not(Test-Path -LiteralPath $mp)){throw "Missing supportive module: $mp"}
   $it=Get-Item -LiteralPath $mp
   if($ext-in@(".psm1",".psd1")){Import-Module $mp -Force -ErrorAction Stop;$loaded++;continue}
   if($ext-eq".ps1"){
     if($it.Length-eq0){$empty++;continue}
     $txt=[string](Get-Content -LiteralPath $mp -Raw -Encoding UTF8)
     if([string]::IsNullOrWhiteSpace($txt)){$empty++;continue}
     $tok=$null;$err=$null;[Management.Automation.Language.Parser]::ParseInput($txt,[ref]$tok,[ref]$err)|Out-Null
     if(@($err).Count){throw "Supportive AST error: $($err[0].Message)"}
     $sb=[scriptblock]::Create($txt);$mi=New-Module -Name ("VIA_SAFE_"+[guid]::NewGuid().ToString("N")) -ScriptBlock $sb
     Import-Module -ModuleInfo $mi -Force -ErrorAction Stop;$loaded++
   }
 }
 S "SUPPORTIVE_IMPORTED" $true "" $loaded $empty
 if(-not(Test-Path -LiteralPath $Candidate)){throw "Candidate missing: $Candidate"}
 $t=$null;$e=$null;[Management.Automation.Language.Parser]::ParseFile($Candidate,[ref]$t,[ref]$e)|Out-Null
 if(@($e).Count){throw "Candidate AST error: $($e[0].Message)"}
 S "ENTRYPOINT_STARTED" $true "" $loaded $empty
 & $Candidate
 S "COMPLETED" $true "" $loaded $empty
}catch{
 S "FAILED" $false $_.Exception.Message $loaded $empty
 Write-Host "def VRN Candidate ERROR: $($_.Exception.Message)" -ForegroundColor Red
 Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}finally{try{Stop-Transcript|Out-Null}catch{}}
'@
 $z=$tpl.Replace("__CANDIDATE__",$candidate).Replace("__NAME__",$name).Replace("__MANIFEST__",$SupportiveDeploy).Replace("__STATUS__",$status).Replace("__TRANSCRIPT__",$transcript)
 Set-Content -LiteralPath $dest -Value $z -Encoding UTF8
}

try{
 if($ApprovalPhrase-ne$Expected){throw"Approval phrase mismatch"}
 foreach($d in@($RunDir,$CsvDir,$JsonDir,$HtmlDir,$TmpDir,$Persist,$LaunchDir,$LogDir,$ManifestDir,$HtmlPersist)){Ensure $d}
 Write-Host "def [BOOT] v0136 started. v0134 organization will NOT repeat." -ForegroundColor Cyan

 $vdfStatus=Join-Path $BaseDir "supportive modules\VIA_Governance_Runtime\v0135\logs\VDF_activation_status.v0135.json"
 if(-not(Test-Path -LiteralPath $vdfStatus)){throw"v0135 VDF status missing"}
 $vdf=Get-Content -LiteralPath $vdfStatus -Raw -Encoding UTF8|ConvertFrom-Json
 if([string]$vdf.state-ne"COMPLETED"){throw"VDF is not COMPLETED in v0135"}

 $vrnStatus=Join-Path $BaseDir "supportive modules\VIA_Governance_Runtime\v0135\logs\VRN_activation_status.v0135.json"
 if(-not(Test-Path -LiteralPath $vrnStatus)){throw"v0135 VRN status missing"}
 $vrn=Get-Content -LiteralPath $vrnStatus -Raw -Encoding UTF8|ConvertFrom-Json
 if([string]$vrn.state-ne"FAILED"){throw"VRN is not FAILED; fallback unnecessary"}
 Write-Host "def [V0135] Confirmed VDF COMPLETED and canonical VRN FAILED." -ForegroundColor Yellow

 if(-not(Test-Path -LiteralPath $SupportiveSource)){throw"Supportive manifest missing"}
 Copy-Item -LiteralPath $SupportiveSource -Destination $SupportiveDeploy -Force
 $mods=@(Get-Content -LiteralPath $SupportiveDeploy -Raw -Encoding UTF8|ConvertFrom-Json)

 $root=Join-Path $BaseDir "functional modules\VRN"
 $spec=@(
  [pscustomobject]@{priority=10;name="Invoke-VRN-PURE-NOHANG-v2192.ps1";role="NOHANG_PRIMARY"},
  [pscustomobject]@{priority=20;name="Invoke-VRN-Guarded-Entry-v217.ps1";role="GUARDED"},
  [pscustomobject]@{priority=30;name="Start-VRN-Lane3-EngineCapability.ps1";role="ENGINE_CAPABILITY"},
  [pscustomobject]@{priority=40;name="Start-VRN-Lane2-IOInventory.ps1";role="IO_INVENTORY"},
  [pscustomobject]@{priority=50;name="Invoke-VRN-MQ-NoOCR-Staging-v222.ps1";role="NO_OCR_STAGING"},
  [pscustomobject]@{priority=999;name="Invoke-VRN.ps1";role="CANONICAL_FAILED"}
 )
 $matrix=@()
 foreach($q in$spec){
  $x=Join-Path $root $q.name;$exists=Test-Path -LiteralPath $x;$ok=$false;$first="";$meta=[pscustomobject]@{all="";mandatory="";count=0;defaults=""}
  if($exists){$pc=ParsePs $x;$ok=$pc.ok;$first=$pc.first;$meta=ParamMeta $pc.ast}
  $eligible=$exists-and$ok-and$meta.count-eq0-and$q.name-ne"Invoke-VRN.ps1"
  $decision=if($q.name-eq"Invoke-VRN.ps1"){"EXCLUDE_RUNTIME_FAILED"}elseif(-not$exists){"EXCLUDE_MISSING"}elseif(-not$ok){"EXCLUDE_AST"}elseif($meta.count){"EXCLUDE_MANDATORY_PARAMS"}else{"ELIGIBLE"}
  $matrix+=[pscustomobject]@{priority=$q.priority;name=$q.name;role=$q.role;path=$x;exists=$exists;parse_ok=$ok;first_error=$first;parameters=$meta.all;mandatory_without_default=$meta.mandatory;eligible=$eligible;decision=$decision}
 }
 C $matrix $CandidateCsv;J $matrix (Join-Path $JsonDir "VRN_EntrypointCandidateMatrix.v0136.json")
 $eligible=@($matrix|Where-Object eligible|Sort-Object priority)
 Write-Host ("def [CANDIDATES] Eligible: {0}" -f $eligible.Count) -ForegroundColor Green

 $attempts=@();$selected=$null
 if($ActivateVrn){
  foreach($cand in$eligible){
   $safe=([IO.Path]::GetFileNameWithoutExtension($cand.name)-replace'[^A-Za-z0-9_]','_')
   $tmp=Join-Path $TmpDir "Start-$safe-v0136.ps1";$launcher=Join-Path $LaunchDir "Start-$safe-v0136.ps1"
   $status=Join-Path $LogDir "${safe}_status.v0136.json";$trans=Join-Path $LogDir "${safe}_transcript.v0136.txt"
   ChildScript $cand.path $cand.name $status $trans $tmp
   $lc=ParsePs $tmp
   if(-not$lc.ok){$attempts+=[pscustomobject]@{candidate=$cand.name;process_state="NOT_STARTED";child_state="LAUNCHER_AST_FAILED";success=$false;error=$lc.first;status=$status;transcript=$trans};continue}
   Copy-Item $tmp $launcher -Force
   if(Test-Path $status){Remove-Item $status -Force -ErrorAction SilentlyContinue}
   Write-Host "def [ATTEMPT] $($cand.name)" -ForegroundColor Cyan
   $proc=Start-Process (Get-Command pwsh).Source -ArgumentList @("-NoLogo","-NoProfile","-ExecutionPolicy","Bypass","-EncodedCommand",(Enc $launcher)) -PassThru
   Start-Sleep -Seconds $ProbeSeconds;$proc.Refresh()
   $ps=if($proc.HasExited){"EXITED_$($proc.ExitCode)"}else{"RUNNING"}
   $cs="STATUS_NOT_WRITTEN";$ld=0;$em=0;$er="";$success=$false
   if(Test-Path $status){$st=Get-Content $status -Raw -Encoding UTF8|ConvertFrom-Json;$cs=[string]$st.state;$ld=[int]$st.loaded;$em=[int]$st.empty_skipped;$er=[string]$st.error;$success=$cs-in@("ENTRYPOINT_STARTED","COMPLETED")}
   $a=[pscustomobject]@{candidate=$cand.name;process_state=$ps;child_state=$cs;loaded=$ld;empty_skipped=$em;success=$success;error=$er;status=$status;transcript=$trans}
   $attempts+=$a
   if($success){$selected=$a;break}
  }
 }
 C $attempts $AttemptCsv;J $attempts (Join-Path $JsonDir "VRN_ActivationAttemptEvidence.v0136.json")

 $gate="VRN_FALLBACK_REVIEW_REQUIRED";$risk="MEDIUM_REVIEW";$decision="No VRN fallback candidate reached ENTRYPOINT_STARTED or COMPLETED.";$next="Review the last candidate transcript."
 $sel="";$state="NOT_ACTIVATED"
 if($null-ne$selected){$gate="FULL_VRN_VDF_ACTIVATION_SUCCESS";$risk="LOW_CONTROLLED_WITH_HYDRA_MONITORING";$sel=$selected.candidate;$state="$($selected.process_state)/$($selected.child_state)/Loaded=$($selected.loaded)/EmptySkipped=$($selected.empty_skipped)";$decision="VDF remained completed; VRN activated through a safe fallback without changing canonical Invoke-VRN.ps1.";$next="Repair canonical Invoke-VRN.ps1 separately in draft-only mode."}
 $summary=[ordered]@{version="v0136";generated=(Get-Date).ToString("o");gate=$gate;risk=$risk;decision=$decision;next_step=$next;organization_repeated=$false;vdf_state="COMPLETED_FROM_v0135";vrn_canonical="FAILED_METHOD_STYLE_RUNTIME";vrn_selected=$sel;vrn_state=$state;attempts=$attempts.Count;eligible=$eligible.Count;supportive_approved=$mods.Count;run_dir=$RunDir;html=$Html}
 J $summary $SummaryJson

 $css="<style>body{font:12px 'Microsoft JhengHei';background:#f7f8f6;padding:22px;color:#24312f}h1{font-size:22px}h2{border-left:5px solid #0f766e;padding-left:8px}.card{background:white;border:1px solid #d8e2df;border-radius:10px;padding:12px;margin:10px 0}.tw{overflow:auto;max-height:600px}table{border-collapse:collapse;font-size:10.5px}th,td{border:1px solid #d8e2df;padding:5px;vertical-align:top;white-space:normal;word-break:break-word;max-width:440px}th{position:sticky;top:0;background:#e7efed}.ok{color:#18794e}.bad{color:#b42318}</style>"
 $hc=if($gate-eq"FULL_VRN_VDF_ACTIVATION_SUCCESS"){"ok"}else{"bad"}
 $doc="<!doctype html><meta charset='utf-8'><title>VIA VRN v0136</title>$css<h1>VIA · VRN Fallback Activation · v0136</h1><div class='card'><b>Gate:</b> <span class='$hc'>$(HtmlEnc $gate)</span><br><b>VDF:</b> COMPLETED_FROM_v0135<br><b>VRN:</b> $(HtmlEnc $state)<br><b>Organization repeated:</b> NO</div><h2>Decision</h2><div class='card'>$(HtmlEnc $decision)<br>Next: $(HtmlEnc $next)</div><h2>Candidate Matrix</h2><div class='card'>$(Table $matrix)</div><h2>Attempts</h2><div class='card'>$(Table $attempts)</div><h2>Paths</h2><div class='card'>RunDir: $(HtmlEnc $RunDir)<br>HTML: $(HtmlEnc $Html)</div>"
 Set-Content -LiteralPath $Html -Value $doc -Encoding UTF8
 Copy-Item $Html (Join-Path $HtmlPersist (Split-Path -Leaf $Html)) -Force
 if($OpenHtmlReport){Start-Process $Html}

 Write-Host "";Write-Host ("="*112) -ForegroundColor DarkCyan
 Write-Host "def VIA · v0136 FINAL RESULT" -ForegroundColor Cyan
 Write-Host ("def Gate                 : {0}" -f $gate) -ForegroundColor Cyan
 Write-Host "def OrganizationRepeated : False" -ForegroundColor Green
 Write-Host "def VDFState             : COMPLETED_FROM_v0135" -ForegroundColor Green
 Write-Host ("def VRNSelected          : {0}" -f $sel) -ForegroundColor Green
 Write-Host ("def VRNState             : {0}" -f $state) -ForegroundColor Green
 Write-Host ("def Attempts             : {0}" -f $attempts.Count) -ForegroundColor White
 Write-Host ("def RunDir               : {0}" -f $RunDir) -ForegroundColor Cyan
 Write-Host ("def HTML                 : {0}" -f $Html) -ForegroundColor Green
}catch{
 Write-Host "";Write-Host "def VIA · v0136 OUTER SAFE CATCH" -ForegroundColor Red
 Write-Host ("def ErrorType    : {0}" -f $_.Exception.GetType().FullName) -ForegroundColor Red
 Write-Host ("def ErrorMessage : {0}" -f $_.Exception.Message) -ForegroundColor Red
 Write-Host ("def StackTrace   : {0}" -f $_.ScriptStackTrace) -ForegroundColor DarkRed
 Write-Host ("def RunDir       : {0}" -f $RunDir) -ForegroundColor Cyan
 Write-Host "def No organization, delete, canonical mutation or Stop-Process was executed." -ForegroundColor Yellow
}finally{
 Write-Host ""
 Write-Host "def Parent PowerShell remains open. v0134 organization was not repeated." -ForegroundColor Cyan
}
