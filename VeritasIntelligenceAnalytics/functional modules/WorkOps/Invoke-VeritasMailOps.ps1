#requires -Version 5.1
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
<#
==========================================================================================
 Veritas MailOps · One-Script Compliance Edition
 Version : v001
 Mode    : LOCAL-ONLY / READ-ONLY SCAN / DRAFTS-FOR-REVIEW / NEVER-AUTO-SEND / NEVER-AUTO-WRITE
==========================================================================================

 一支 PowerShell 打通整條合規流程,滑鼠 / 單鍵即可跑:

   [1] 掃描   Scan       只讀你自己的 Outlook -> 匯出 mails.csv / pending.csv / stakeholders.csv
   [2] 對帳   Reconcile  控管表(control_sheet.csv) × 郵件佐證 -> 產生 proposals.csv(建議,不改控管表)
   [3] 追蹤信 Draft      依 recipients.csv + 範本 -> 建 Outlook 草稿(選擇題),你檢視後親自寄
   [4] 補追殺 FollowUp   同上,改用「再次追蹤」範本
   [5] 範本   Templates  建立 / 開啟 templates\ 範本庫(TPL_*.html)
   [6] 全部   All        掃描 -> 對帳 -> 建草稿,一次跑完
   [0] 離開

 核心原則(不因改寫 / 最佳化而改變):
   郵件只「佐證」 · 控管表「治理」 · 你核准才生效。

 明確不做:
   - 不自動寄信 / 不自動回信 —— 一律只建立「草稿」,由你本人按傳送(絕不呼叫 .Send())。
   - 讀信只讀:不搬移、不刪除、不修改、不標記已讀、不改任何既有郵件。
   - 不自動寫回控管表 —— 只輸出 proposals.csv 供你逐列核准後自行套用。
   - 不用 Graph / OAuth / API / 網路;不建排程;不改登錄檔;不要系統管理員。
   - 不壓制 / 不繞過 Outlook 或公司資安提示。COM 被政策封鎖即停止,不嘗試繞過。
   - 不夾帶自己 BCC 追蹤碼;不監看同事信箱。全程你自己的權限、你自己的信箱。

 執行:
   powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File ".\Invoke-VeritasMailOps.ps1"
   (直接雙擊 START_Veritas_MailOps.cmd 亦可)
#>

# ==========================================================================================
# 01. PARAMETERS
# ==========================================================================================
[CmdletBinding()]
param(
    [ValidateSet("Menu", "Scan", "Reconcile", "Draft", "FollowUp", "Templates", "All")]
    [string]$Action = "Menu",

    [string]$Root = $PSScriptRoot,
    [string]$TemplateDir = "",
    [string]$RecipientsCsv = "",
    [string]$ControlSheet = "",
    [string]$OutDir = "",

    [ValidateSet("Display", "Save")]
    [string]$OpenMode = "Display",
    [string]$Category = "VIA_Tracking",
    [string]$MyName = "Tony Huang",
    [string]$DefaultTemplate = "status_request",

    [int]$Days = 14
)

$Script:APP_VERSION = "v001"
if ([string]::IsNullOrWhiteSpace($Root)) { $Root = (Get-Location).Path }
if ([string]::IsNullOrWhiteSpace($TemplateDir))   { $TemplateDir   = Join-Path $Root "templates" }
if ([string]::IsNullOrWhiteSpace($RecipientsCsv)) { $RecipientsCsv = Join-Path $Root "recipients.csv" }
if ([string]::IsNullOrWhiteSpace($ControlSheet))  { $ControlSheet  = Join-Path $Root "control_sheet.csv" }
if ([string]::IsNullOrWhiteSpace($OutDir))        { $OutDir        = Join-Path $Root "out" }

# ==========================================================================================
# 02. STA RELAUNCH (Outlook COM prefers single-threaded apartment)
# ==========================================================================================
function VO_RelaunchInStaIfNeeded {
    param([string]$ForAction)
    if ([Threading.Thread]::CurrentThread.GetApartmentState() -eq "STA") { return $false }
    $PwshPath = (Get-Process -Id $PID).Path
    $ArgList = @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-STA",
        "-File", ('"{0}"' -f $PSCommandPath),
        "-Action", $ForAction,
        "-Root", ('"{0}"' -f $Root),
        "-OpenMode", $OpenMode,
        "-Category", ('"{0}"' -f $Category),
        "-MyName", ('"{0}"' -f $MyName),
        "-DefaultTemplate", $DefaultTemplate,
        "-Days", $Days
    )
    Start-Process -FilePath $PwshPath -ArgumentList $ArgList | Out-Null
    return $true
}

# ==========================================================================================
# 03. SAFE HELPERS
# ==========================================================================================
function VO_WriteUtf8 {
    param([string]$Path, [string]$Text)
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { $null = New-Item -ItemType Directory -Path $dir -Force }
    [IO.File]::WriteAllText($Path, $Text, (New-Object Text.UTF8Encoding($false)))
}

function VO_ExportCsv {
    param($Rows, [string]$Path)
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path -LiteralPath $dir)) { $null = New-Item -ItemType Directory -Path $dir -Force }
    if ($null -eq $Rows -or @($Rows).Count -eq 0) {
        # still write a header-less marker so the pipeline is explicit
        VO_WriteUtf8 -Path $Path -Text ""
        return 0
    }
    @($Rows) | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
    return @($Rows).Count
}

function VO_ReleaseComObject {
    param($ComObject)
    if ($null -eq $ComObject) { return }
    try {
        if ([Runtime.InteropServices.Marshal]::IsComObject($ComObject)) {
            $null = [Runtime.InteropServices.Marshal]::FinalReleaseComObject($ComObject)
        }
    } catch { }
}

function VO_ParseDate {
    param($Value)
    if ($null -eq $Value) { return $null }
    if ($Value -is [datetime]) { return $Value }
    $s = ([string]$Value).Trim()
    if ([string]::IsNullOrWhiteSpace($s)) { return $null }
    $dt = [datetime]::MinValue
    if ([datetime]::TryParse($s, [ref]$dt)) { return $dt }
    foreach ($fmt in @("yyyy/MM/dd", "yyyy-MM-dd", "yyyy/M/d", "yyyyMMdd", "MM/dd/yyyy")) {
        if ([datetime]::TryParseExact($s, $fmt, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::None, [ref]$dt)) { return $dt }
    }
    return $null
}

function VO_FirstAddr {
    param([string]$s)
    if ([string]::IsNullOrWhiteSpace($s)) { return "" }
    return ($s -split "[;,]")[0].Trim()
}

function VO_Get {
    param($Row, [string[]]$Names)
    foreach ($n in $Names) {
        if ($Row.PSObject.Properties.Name -contains $n) {
            $v = [string]$Row.$n
            if (-not [string]::IsNullOrWhiteSpace($v)) { return $v.Trim() }
        }
    }
    return ""
}

# ==========================================================================================
# 04. TEMPLATE LIBRARY (scaffold + render) — subject on first line: <!-- SUBJECT: ... -->
# ==========================================================================================
function VO_BuildQuestionRows {
    # v0116(操作員「郵件加入必問問題」令):必回題庫 JSON 化 — engines\mail_questions.json
    # 為唯一題庫正本;加題/改選項只改 JSON,重建範本即生效。JSON 缺席=誠實回退內建五題。
    param([switch]$WithNotes)
    $qp = Join-Path $PSScriptRoot "engines\mail_questions.json"
    $rows = ""
    try {
        $qb = Get-Content -LiteralPath $qp -Raw -Encoding UTF8 | ConvertFrom-Json
        $i = 0
        foreach ($q in $qb.questions) {
            $i++
            $opts = ($q.options | ForEach-Object { "○ " + $_ }) -join "　"
            $rows += "      {0}. {1}： {2}<br/>`n" -f $i, $q.text, $opts
            if ($WithNotes -and $q.note) {
                $rows += "      <span style=""color:#64748b;font-size:11.5px;"">└ {0}</span><br/>`n" -f $q.note
            }
        }
    } catch { $rows = "" }
    if (-not $rows) {
        $rows = @'
      1. 目前狀態： ○ 進行中　○ 已完成　○ 卡關<br/>
      2. 完成百分比： ○ 25%　○ 50%　○ 75%　○ 100%<br/>
      3. 預計完成 ETA： ○ 今日　○ 明日　○ 本週　○ 其他：__________<br/>
      4. 是否有阻礙 / 風險： ○ 無　○ 有：__________<br/>
      5. 是否需要我協助： ○ 否　○ 是：__________<br/>
'@
    }
    return $rows
}

function VO_GetDefaultTemplates {
    $QRows = VO_BuildQuestionRows
    $Answer = @"
      <table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin:14px 0;width:100%;max-width:560px;">
        <tr><td style="background:#1e293b;color:#fff;font:700 13px 'Segoe UI',sans-serif;padding:8px 14px;border-radius:6px 6px 0 0;">請圈選或保留適用項後直接回覆(選項為主,幾乎免打字)</td></tr>
        <tr><td style="border:1px solid #e2e8f0;border-top:none;padding:12px 16px;font:400 13px 'Segoe UI',sans-serif;color:#1e293b;line-height:2.1;">
$QRows
        </td></tr>
      </table>
"@
    $Wrap = {
        param($Subject, $Lead, $Extra)
        @"
<!-- SUBJECT: $Subject -->
<div style="font:400 13px/1.6 'Segoe UI','Microsoft JhengHei',sans-serif;color:#1e293b;">
  <p>Hi {{ProjectName}} 窗口,</p>
  <p>$Lead</p>
$Extra
$Answer
  <p style="color:#64748b;font-size:12px;">為利明日整理進度,若能今天回覆最好。若已於電話 / 會議中說明,也請簡短補一句於上方,以便留存紀錄。謝謝!</p>
  <p>Best regards,<br/>{{MyName}}</p>
  <p style="color:#94a3b8;font-size:11px;font-family:Consolas,monospace;">追蹤案號 {{ProjectCode}} · {{Date}}</p>
</div>
"@
    }
    # v0113:豐富版必回選擇題(操作員令:範本內文寫得太過簡單)— 背景區塊+三種回覆方式+
    # 每題補充說明+期限句;placeholders 由列欄位注入,缺席欄位由 Render 清空
    $RichApproval = @'
<!-- SUBJECT: [待回·選擇題] {{ProjectCode}} {{ProjectName}} - 請點投票鈕或圈選,一分鐘可回 -->
<div style="font:400 13px/1.7 'Segoe UI','Microsoft JhengHei',sans-serif;color:#1e293b;max-width:660px;">
  <p>Hi {{ProjectName}} 窗口,您好:</p>
  <p>關於 <b>{{ProjectName}}</b>(案號 <span style="font-family:Consolas,monospace;">{{ProjectCode}}</span>)的目前進度,
     我這邊正在彙整各案排程與資源配置,需要您更新一下狀態。這封信設計成<b>選擇題</b>,回覆幾乎不用打字。</p>
  <table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin:10px 0;width:100%;">
    <tr><td style="background:#f1f5f9;border-left:4px solid #64748b;padding:8px 12px;font-size:12px;color:#475569;line-height:1.8;">
      原信主旨:{{OrigSubject}}<br/>追蹤識別:{{CaseID}} · 已等候 {{WaitingDays}} 天 · 原寄出 {{SentOn}}
    </td></tr>
  </table>
  <table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin:12px 0;width:100%;">
    <tr><td style="background:#1e293b;color:#fff;font:700 13px 'Segoe UI',sans-serif;padding:8px 14px;border-radius:6px 6px 0 0;">三種回覆方式,擇一即可(最快 10 秒)</td></tr>
    <tr><td style="border:1px solid #e2e8f0;border-top:none;padding:12px 16px;font-size:13px;line-height:2.0;">
      ① <b>最快 — 投票按鈕</b>:本信上方 Outlook「投票」列(進行中 / 已完成 / 卡關 / 需要協助),點一顆即回,零打字。<br/>
      ② <b>回覆本信</b>:在下表把適用的 ○ 圈起、或刪去不適用的選項後送出。<br/>
      ③ <b>一句話</b>:例「進行中,70%,週五完成」— 我來歸檔。
    </td></tr>
  </table>
  <table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin:12px 0;width:100%;">
    <tr><td style="background:#334155;color:#fff;font:700 13px 'Segoe UI',sans-serif;padding:8px 14px;border-radius:6px 6px 0 0;">__QHEADER__</td></tr>
    <tr><td style="border:1px solid #e2e8f0;border-top:none;padding:12px 16px;font-size:13px;line-height:2.2;">
__QROWS__
    </td></tr>
  </table>
  <p>若能於 <b>明日中午前</b> 回覆,即可趕上本週彙整;若您已在會議或電話中說明,回「已口頭說明」即可留檔。謝謝!</p>
  <p>Best regards,<br/>{{MyName}}</p>
  <p style="color:#94a3b8;font-size:11px;font-family:Consolas,monospace;">追蹤 {{ProjectCode}} {{CaseID}} · {{Date}} · 本信為 VIA WorkOps 產生之草稿,經本人確認後親自寄出</p>
</div>
'@
    # v0116:豐富版必回題區塊由題庫 JSON 組裝(__QHEADER__/__QROWS__ 佔位替換)
    $qhdr = "必回五題(圈選即可)"
    try {
        $qb2 = Get-Content -LiteralPath (Join-Path $PSScriptRoot "engines\mail_questions.json") -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($qb2.header) { $qhdr = [string]$qb2.header }
    } catch { }
    $RichApproval = $RichApproval.Replace("__QHEADER__", $qhdr).Replace("__QROWS__", (VO_BuildQuestionRows -WithNotes))
    # v0115 三段追蹤 T3:緊急升級範本(前兩段未獲回覆;建議 CC 主管由人自加 — 系統絕不代加代寄)
    $UrgentEscalation = @"
<!-- SUBJECT: [緊急·第三次通知] {{ProjectCode}} {{ProjectName}} - 今日內需要您的回覆 -->
<div style="font:400 13px/1.7 'Segoe UI','Microsoft JhengHei',sans-serif;color:#1e293b;max-width:660px;">
  <p>Hi {{ProjectName}} 窗口,您好:</p>
  <table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin:10px 0;width:100%;">
    <tr><td style="background:#fef2f2;border-left:4px solid #dc2626;padding:10px 14px;font-size:12.5px;color:#7f1d1d;line-height:1.8;">
      <b>此為第三次通知。</b>關於「{{OrigSubject}}」(追蹤識別 {{CaseID}}),自 {{SentOn}} 寄出至今已 {{WaitingDays}} 天未獲回覆,
      前兩次追蹤信亦未見回音。此案已影響後續排程,若今日內仍無回覆,我將需要向上反映以尋求協助排除。
    </td></tr>
  </table>
  <p>仍然只需要幾秒:點本信上方的<b>投票按鈕</b>(進行中 / 已完成 / 卡關 / 需要協助),或直接回一句話即可。
     若您已於電話/會議中說明,回「已口頭說明」即可留檔結案。</p>
$Answer
  <p style="color:#7f1d1d;"><b>請於今日下班前回覆。</b>若有任何困難,直接回「需要協助」,我來安排。謝謝!</p>
  <p>Best regards,<br/>{{MyName}}</p>
  <p style="color:#94a3b8;font-size:11px;font-family:Consolas,monospace;">追蹤 {{ProjectCode}} {{CaseID}} · {{Date}} · T3 升級通知 · 本信為草稿,經本人確認後親自寄出;如需 CC 主管由本人寄出時自行加入</p>
</div>
"@
    return @{
        "status_request"   = (& $Wrap "[追蹤] {{ProjectCode}} {{ProjectName}} - 進度確認" "想跟你確認 <b>{{ProjectName}}</b>({{ProjectCode}})目前的進度。" "")
        "eta_confirm"      = (& $Wrap "[追蹤] {{ProjectCode}} {{ProjectName}} - 交期確認" "想跟你再次確認 <b>{{ProjectName}}</b>({{ProjectCode}})的<b>預計完成 / 交期</b>是否仍如原訂。" "  <p style='color:#c0392b;'>如需調整交期,請於下方第 3 點圈選或填新日期並簡述原因。</p>")
        "blocker_check"    = (& $Wrap "[追蹤] {{ProjectCode}} {{ProjectName}} - 風險 / 阻礙盤點" "想確認 <b>{{ProjectName}}</b>({{ProjectCode}})目前是否有卡關或潛在風險,以便及早協助。" "")
        "approval_request" = (& $Wrap "[待核] {{ProjectCode}} {{ProjectName}} - 請確認 / 核准" "以下 <b>{{ProjectName}}</b>({{ProjectCode}})事項需要你確認或核准,煩請於下方圈選回覆。" "")
        "approval_request_v2" = $RichApproval
        "urgent_escalation" = $UrgentEscalation
        "followup"         = (& $Wrap "[再次追蹤] {{ProjectCode}} {{ProjectName}} - 尚未收到回覆" "先前關於 <b>{{ProjectName}}</b>({{ProjectCode}})的進度確認尚未收到你的回覆,再麻煩你抽空圈選一下,謝謝!" "")
        "followup_firm"    = (& $Wrap "[急件·再追] {{ProjectCode}} {{ProjectName}} - 需盡快回覆" "<b>{{ProjectName}}</b>({{ProjectCode}})的進度已影響後續排程,今天內需要你的回覆。麻煩直接圈選下列項目即可:" "  <p style='color:#c0392b;'>若有困難請於第 5 點勾『是』並說明,我來協助排除。</p>")
    }
}

function VO_ScaffoldTemplates {
    if (-not (Test-Path -LiteralPath $TemplateDir)) { $null = New-Item -ItemType Directory -Path $TemplateDir -Force }
    $Templates = VO_GetDefaultTemplates
    foreach ($Key in $Templates.Keys) {
        $File = Join-Path $TemplateDir ("TPL_{0}.html" -f $Key)
        if (-not (Test-Path -LiteralPath $File)) { VO_WriteUtf8 -Path $File -Text $Templates[$Key] }
    }
    if (-not (Test-Path -LiteralPath $RecipientsCsv)) {
        $SampleCsv = @'
ProjectCode,ProjectName,To,Cc,Template
PRJ-001,日本合資案,someone@example.com,,status_request
PRJ-002,德商合約談判,another@example.com,manager@example.com,eta_confirm
PRJ-003,Q3 產線稽核,third@example.com,,blocker_check
'@
        VO_WriteUtf8 -Path $RecipientsCsv -Text $SampleCsv
    }
    if (-not (Test-Path -LiteralPath $ControlSheet)) {
        $SampleControl = @'
ProjectCode,ProjectName,Owner,Status,Progress,DueDate,LastUpdated
PRJ-001,日本合資案,Tony,進行中,50%,2026/08/20,2026/08/01
PRJ-002,德商合約談判,Tony,等待回覆,75%,2026/08/12,2026/07/28
PRJ-003,Q3 產線稽核,Tony,已完成,100%,2026/07/31,2026/07/30
'@
        VO_WriteUtf8 -Path $ControlSheet -Text $SampleControl
    }
}

function VO_LoadTemplate {
    param([string]$Key)
    $File = Join-Path $TemplateDir ("TPL_{0}.html" -f $Key)
    if (Test-Path -LiteralPath $File) { return (Get-Content -LiteralPath $File -Raw -Encoding UTF8) }
    $Defaults = VO_GetDefaultTemplates          # v0113:檔案缺席退內建預設(檔案優先,可自行覆寫)
    if ($Defaults.ContainsKey($Key)) { return [string]$Defaults[$Key] }
    return $null
}

function VO_RenderTemplate {
    param([string]$Raw, [hashtable]$Values)
    $Subject = ""
    $Body = $Raw
    $FirstLine = ($Raw -split "`r?`n", 2)[0]
    $Match = [regex]::Match($FirstLine, "<!--\s*SUBJECT:\s*(.*?)\s*-->")
    if ($Match.Success) {
        $Subject = $Match.Groups[1].Value
        $Body = ($Raw -split "`r?`n", 2)[1]
    }
    foreach ($Key in $Values.Keys) {
        $Token = "{{" + $Key + "}}"
        $Subject = $Subject.Replace($Token, [string]$Values[$Key])
        $Body = $Body.Replace($Token, [string]$Values[$Key])
    }
    $Subject = [regex]::Replace($Subject, "\{\{[A-Za-z]+\}\}", "")   # v0113:缺席欄位清空不留 token
    $Body    = [regex]::Replace($Body, "\{\{[A-Za-z]+\}\}", "")
    return [pscustomobject]@{ Subject = $Subject; HtmlBody = $Body }
}

# ==========================================================================================
# 05. OUTLOOK CONNECTION (attach to your running Classic Outlook; never bypass)
# ==========================================================================================
function VO_GetOutlook {
    try { return [Runtime.InteropServices.Marshal]::GetActiveObject("Outlook.Application") } catch { }
    try { return (New-Object -ComObject Outlook.Application) } catch { return $null }
}

# ==========================================================================================
# 06. SCAN — READ-ONLY. Reads your own Inbox + Sent, exports CSVs. Modifies nothing.
# ==========================================================================================
function VO_Scan {
    Write-Host ">> [掃描] 只讀你自己的 Outlook(不改任何郵件)..." -ForegroundColor Cyan
    $Outlook = VO_GetOutlook
    if ($null -eq $Outlook) {
        Write-Host "   無法連上 Classic Outlook COM。請先開啟 Outlook。政策封鎖則停止,不繞過。" -ForegroundColor Red
        return $false
    }
    $ns = $null; $inbox = $null; $sent = $null
    try {
        $ns = $Outlook.GetNamespace("MAPI")
        $inbox = $ns.GetDefaultFolder(6)   # olFolderInbox
        $sent  = $ns.GetDefaultFolder(5)   # olFolderSentMail
        $cutoff = (Get-Date).AddDays(-1 * [math]::Abs($Days))
        $filter = "[ReceivedTime] >= '" + $cutoff.ToString("MM/dd/yyyy hh:mm tt") + "'"

        $mails = New-Object System.Collections.ArrayList
        $stake = @{}
        $inboxConv = @{}   # ConversationID -> latest inbound datetime

        $inItems = $inbox.Items
        try { $inItems = $inItems.Restrict($filter) } catch { }
        foreach ($it in $inItems) {
            try {
                if ($it.Class -ne 43) { continue }  # 43 = olMail
                $conv = ""; try { $conv = [string]$it.ConversationID } catch { }
                $rt = $null; try { $rt = $it.ReceivedTime } catch { }
                $from = ""; try { $from = [string]$it.SenderEmailAddress } catch { }
                $row = [pscustomobject]@{
                    MailID         = $conv
                    Subject        = [string]$it.Subject
                    Direction      = "INBOUND"
                    EventDate      = if ($rt) { $rt.ToString("yyyy/MM/dd HH:mm") } else { "" }
                    SenderEmail    = $from
                    ConversationID = $conv
                    Unread         = [bool]$it.UnRead    # READ ONLY — value is observed, never assigned
                    Categories     = [string]$it.Categories
                    VotingResponse = $(try { [string]$it.VotingResponse } catch { "" })   # READ ONLY(M3 回覆解析投票層)
                }
                $null = $mails.Add($row)
                if ($from) {
                    if (-not $stake.ContainsKey($from)) { $stake[$from] = [pscustomobject]@{ Email=$from; Domain=(($from -split "@")[-1]); FromCount=0; ToOrCcCount=0; LastDate="" } }
                    $stake[$from].FromCount++
                    if ($rt) { $stake[$from].LastDate = $rt.ToString("yyyy/MM/dd") }
                }
                if ($conv -and $rt) {
                    if (-not $inboxConv.ContainsKey($conv) -or $rt -gt $inboxConv[$conv]) { $inboxConv[$conv] = $rt }
                }
            } catch { }
            finally { VO_ReleaseComObject -ComObject $it }
        }

        # Sent items in window -> pending (you are waiting on THEIR reply)
        $pending = New-Object System.Collections.ArrayList
        $sfilter = "[SentOn] >= '" + $cutoff.ToString("MM/dd/yyyy hh:mm tt") + "'"
        $seenConv = @{}
        $sentItems = $sent.Items
        try { $sentItems = $sentItems.Restrict($sfilter) } catch { }
        foreach ($it in $sentItems) {
            try {
                if ($it.Class -ne 43) { continue }
                $conv = ""; try { $conv = [string]$it.ConversationID } catch { }
                $so = $null; try { $so = $it.SentOn } catch { }
                $to = ""; try { $to = [string]$it.To } catch { }
                if ($conv -and $seenConv.ContainsKey($conv)) { continue }
                if ($conv) { $seenConv[$conv] = $true }
                $replied = $false
                if ($conv -and $inboxConv.ContainsKey($conv) -and $so) { if ($inboxConv[$conv] -gt $so) { $replied = $true } }
                if (-not $replied) {
                    $null = $pending.Add([pscustomobject]@{
                        CASE_ID        = $conv
                        Subject        = [string]$it.Subject
                        LAST_DIRECTION = "OUTBOUND"
                        TO             = VO_FirstAddr $to
                        SentOn         = if ($so) { $so.ToString("yyyy/MM/dd HH:mm") } else { "" }
                        WaitingDays    = if ($so) { [int]((Get-Date) - $so).TotalDays } else { 0 }
                    })
                }
            } catch { }
            finally { VO_ReleaseComObject -ComObject $it }
        }

        $nMail = VO_ExportCsv -Rows $mails -Path (Join-Path $OutDir "mails.csv")
        $nPend = VO_ExportCsv -Rows $pending -Path (Join-Path $OutDir "pending.csv")
        $nStk  = VO_ExportCsv -Rows ($stake.Values) -Path (Join-Path $OutDir "stakeholders.csv")
        Write-Host ("   匯出:mails={0}  pending(待回覆)={1}  stakeholders={2}" -f $nMail, $nPend, $nStk) -ForegroundColor Green
        Write-Host ("   位置:{0}" -f $OutDir) -ForegroundColor DarkGray
        return $true
    }
    catch {
        Write-Host ("   掃描發生錯誤:{0}" -f $_.Exception.Message) -ForegroundColor Red
        return $false
    }
    finally {
        VO_ReleaseComObject -ComObject $sent
        VO_ReleaseComObject -ComObject $inbox
        VO_ReleaseComObject -ComObject $ns
        VO_ReleaseComObject -ComObject $Outlook
    }
}

# ==========================================================================================
# 07. RECONCILE — control sheet GOVERNS, email INFORMS, you APPROVE.
#     Pure logic (unit-testable). Writes proposals.csv only; NEVER edits control_sheet.csv.
# ==========================================================================================
function VO_BuildEvidence {
    param($Mails, $Pending)
    # returns hashtable keyed lowercased helper is done at match time; here just normalize rows
    $ev = [pscustomobject]@{ Mails = @($Mails); Pending = @($Pending) }
    return $ev
}

function VO_MatchEvidence {
    param([string]$Code, [string]$Name, $Evidence)
    $code = ($Code + "").Trim()
    $name = ($Name + "").Trim()
    $count = 0; $lastDate = $null; $lastDir = ""; $waiting = $null
    foreach ($m in $Evidence.Mails) {
        $subj = [string]$m.Subject
        $hit = $false
        if ($code -and $subj -like "*$code*") { $hit = $true }
        elseif ($name -and $subj -like "*$name*") { $hit = $true }
        if ($hit) {
            $count++
            $d = VO_ParseDate ($m.EventDate)
            if ($d -and (($null -eq $lastDate) -or ($d -gt $lastDate))) { $lastDate = $d; $lastDir = [string]$m.Direction }
        }
    }
    foreach ($p in $Evidence.Pending) {
        $subj = [string]$p.Subject
        $hit = $false
        if ($code -and $subj -like "*$code*") { $hit = $true }
        elseif ($name -and $subj -like "*$name*") { $hit = $true }
        if ($hit) {
            $wd = 0; try { $wd = [int]$p.WaitingDays } catch { }
            if (($null -eq $waiting) -or ($wd -gt $waiting)) { $waiting = $wd }
            $d = VO_ParseDate ($p.SentOn)
            if ($d -and (($null -eq $lastDate) -or ($d -gt $lastDate))) { $lastDate = $d; $lastDir = "OUTBOUND" }
        }
    }
    return [pscustomobject]@{
        Count    = $count + ($(if ($null -ne $waiting) { 1 } else { 0 }))
        LastDate = $lastDate
        LastDir  = $lastDir
        Waiting  = $waiting
        HasEvidence = ($count -gt 0 -or $null -ne $waiting)
    }
}

function VO_ReconcileRow {
    param($ControlRow, $Evidence)
    $code = VO_Get $ControlRow @("ProjectCode","專案代號","案號","代號","Code")
    $name = VO_Get $ControlRow @("ProjectName","專案名稱","案名","Name")
    $owner = VO_Get $ControlRow @("Owner","負責人","窗口")
    $status = VO_Get $ControlRow @("Status","狀態","進度狀態")
    $updatedRaw = VO_Get $ControlRow @("LastUpdated","最後更新","更新日","更新日期")
    $updated = VO_ParseDate $updatedRaw

    $m = VO_MatchEvidence -Code $code -Name $name -Evidence $Evidence

    $doneWords = @("已完成","完成","結案","closed","done","complete")
    $isDone = $false
    foreach ($w in $doneWords) { if ($status -and $status.ToLower().Contains($w.ToLower())) { $isDone = $true } }

    $confidence = "Verified"; $field = ""; $proposed = ""; $evidence = ""
    if ([string]::IsNullOrWhiteSpace($code) -or [string]::IsNullOrWhiteSpace($status)) {
        $confidence = "Incomplete"; $evidence = "控管表缺少代號或狀態欄位"
    }
    elseif (-not $m.HasEvidence) {
        $confidence = "Unmatched"; $evidence = "此期間郵件中查無此案佐證(代號/案名未出現)"
    }
    else {
        $emailNewer = ($m.LastDate -ne $null -and $updated -ne $null -and $m.LastDate -gt $updated)
        $emailNewerNoBase = ($m.LastDate -ne $null -and $updated -eq $null)
        $isNewer = ($emailNewer -or $emailNewerNoBase)
        $isWaiting = ($null -ne $m.Waiting -and $m.Waiting -ge 3)
        if ($isDone -and $isNewer) {
            $confidence = "Conflicted"
            $field = "Status"
            $proposed = "請人工判讀(標記已完成,但仍有較新郵件往來)"
            $evidence = ("控管表狀態=已完成,但郵件最後活動 {0} {1} 晚於更新日 {2}" -f (VO_FmtDate $m.LastDate), $m.LastDir, $updatedRaw)
        }
        elseif ($isWaiting -and $m.LastDir -eq "OUTBOUND" -and -not $isDone) {
            $confidence = "Pending Review"
            $field = "Status"
            $proposed = "建議追蹤(已寄出待回覆 " + $m.Waiting + " 天)"
            $evidence = ("最後一次為你寄出,已等待 {0} 天未見回覆;可用 [3]/[4] 建追蹤草稿" -f $m.Waiting)
        }
        elseif ($isNewer) {
            $confidence = "Stale"
            $field = "LastUpdated"
            $proposed = (VO_FmtDate $m.LastDate)
            $evidence = ("郵件最後活動 {0}({1})晚於控管表更新日 {2};建議更新最後更新日" -f (VO_FmtDate $m.LastDate), $m.LastDir, $updatedRaw)
        }
        else {
            $confidence = "Verified"
            $evidence = ("郵件佐證與控管表一致(最後活動 {0})" -f (VO_FmtDate $m.LastDate))
        }
    }

    return [pscustomobject]@{
        ProjectCode   = $code
        ProjectName   = $name
        Owner         = $owner
        Confidence    = $confidence
        BaselineStatus= $status
        BaselineUpdated = $updatedRaw
        ObservedLast  = (VO_FmtDate $m.LastDate)
        ObservedDir   = $m.LastDir
        ObservedMsgs  = $m.Count
        ProposeField  = $field
        ProposeValue  = $proposed
        Evidence      = $evidence
        Decision      = ""   # 你填:採納 / 不採納
    }
}

function VO_FmtDate {
    param($d)
    if ($null -eq $d) { return "" }
    if ($d -is [datetime]) { return $d.ToString("yyyy/MM/dd") }
    return [string]$d
}

function VO_Reconcile {
    Write-Host ">> [對帳] 控管表 × 郵件佐證 -> 產生建議(不改控管表)..." -ForegroundColor Cyan
    if (-not (Test-Path -LiteralPath $ControlSheet)) {
        Write-Host ("   找不到控管表:{0}(可先跑 [5] 範本產生範例)" -f $ControlSheet) -ForegroundColor Yellow
        return $false
    }
    $control = @(Import-Csv -LiteralPath $ControlSheet -Encoding UTF8)
    if ($control.Count -eq 0) { Write-Host "   控管表沒有資料列。" -ForegroundColor Yellow; return $false }

    $mailsPath = Join-Path $OutDir "mails.csv"
    $pendPath  = Join-Path $OutDir "pending.csv"
    $mails = @(); $pending = @()
    if ((Test-Path -LiteralPath $mailsPath) -and (Get-Item -LiteralPath $mailsPath).Length -gt 0) { $mails = @(Import-Csv -LiteralPath $mailsPath -Encoding UTF8) }
    if ((Test-Path -LiteralPath $pendPath)  -and (Get-Item -LiteralPath $pendPath).Length  -gt 0) { $pending = @(Import-Csv -LiteralPath $pendPath -Encoding UTF8) }
    if ($mails.Count -eq 0 -and $pending.Count -eq 0) {
        Write-Host "   尚無郵件佐證(out\mails.csv / pending.csv)。請先跑 [1] 掃描;仍會輸出以控管表為準的結果。" -ForegroundColor DarkYellow
    }

    $ev = VO_BuildEvidence -Mails $mails -Pending $pending
    $rows = New-Object System.Collections.ArrayList
    foreach ($c in $control) { $null = $rows.Add((VO_ReconcileRow -ControlRow $c -Evidence $ev)) }

    $recPath = Join-Path $OutDir "reconcile.csv"
    $null = VO_ExportCsv -Rows $rows -Path $recPath

    # proposals = only rows that suggest a change (Stale/Conflicted/Pending Review)
    $props = @($rows | Where-Object { $_.ProposeField -ne "" })
    $propPath = Join-Path $OutDir "proposals.csv"
    $null = VO_ExportCsv -Rows $props -Path $propPath

    $byConf = $rows | Group-Object Confidence | ForEach-Object { "{0}={1}" -f $_.Name, $_.Count }
    Write-Host ("   對帳完成 {0} 案 · {1}" -f $rows.Count, ($byConf -join "  ")) -ForegroundColor Green
    Write-Host ("   全部結果 : {0}" -f $recPath) -ForegroundColor DarkGray
    Write-Host ("   待核建議 : {0}(共 {1} 筆;你在 Decision 欄填『採納/不採納』後自行套回控管表)" -f $propPath, $props.Count) -ForegroundColor Yellow
    Write-Host "   注意:本步驟不會修改你的 control_sheet.csv。" -ForegroundColor DarkGray
    return $true
}

# ==========================================================================================
# 08. DRAFT — build Outlook drafts from recipients.csv. .Display()/.Save() only. NEVER .Send().
# ==========================================================================================
function VO_Draft {
    param([ValidateSet("Initial","FollowUp")][string]$DraftMode = "Initial")
    Write-Host (">> [追蹤信] 模式={0}  只建立草稿,你檢視後親自寄(不自動寄)。" -f $DraftMode) -ForegroundColor Cyan

    if (-not (Test-Path -LiteralPath $RecipientsCsv) -or -not (Test-Path -LiteralPath $TemplateDir)) {
        VO_ScaffoldTemplates
        Write-Host "   已建立 templates\ 與 recipients.csv 範例。請編輯 recipients.csv 後再執行。" -ForegroundColor Yellow
        return $false
    }
    $Rows = @(Import-Csv -LiteralPath $RecipientsCsv -Encoding UTF8)
    if ($Rows.Count -eq 0) { Write-Host "   recipients.csv 沒有資料列。" -ForegroundColor Yellow; return $false }

    $Outlook = VO_GetOutlook
    if ($null -eq $Outlook) {
        Write-Host "   無法連上 Classic Outlook COM。請先開啟 Outlook。政策封鎖則停止,不繞過。" -ForegroundColor Red
        return $false
    }

    $Today = (Get-Date).ToString("yyyy/MM/dd")
    $Created = 0; $Failed = 0
    foreach ($Row in $Rows) {
        $Mail = $null
        try {
            $EffectiveDefault = if ($DraftMode -eq "FollowUp") { "followup" } else { $DefaultTemplate }
            $TemplateKey = if ([string]::IsNullOrWhiteSpace($Row.Template)) { $EffectiveDefault } else { $Row.Template.Trim() }
            $Raw = VO_LoadTemplate -Key $TemplateKey
            if ($null -eq $Raw) { Write-Host ("   [略過] 找不到範本 TPL_{0}.html" -f $TemplateKey) -ForegroundColor DarkYellow; $Failed++; continue }

            $Values = @{}
            foreach ($Prop in $Row.PSObject.Properties) { $Values[$Prop.Name] = [string]$Prop.Value }
            $Values["MyName"] = $MyName
            $Values["Date"] = $Today
            $Rendered = VO_RenderTemplate -Raw $Raw -Values $Values

            $Mail = $Outlook.CreateItem(0)   # 0 = olMailItem
            $Mail.Subject = $Rendered.Subject
            if (-not [string]::IsNullOrWhiteSpace($Row.To)) { $Mail.To = [string]$Row.To }
            if (($Row.PSObject.Properties.Name -contains "Cc") -and -not [string]::IsNullOrWhiteSpace($Row.Cc)) { $Mail.CC = [string]$Row.Cc }
            $Mail.HTMLBody = $Rendered.HtmlBody
            try { $Mail.Categories = $Category } catch { }
            # v0112 追加:必回選擇題範本附 Outlook 原生投票按鈕(收件人點按即回,零打字)。
            # 回覆 HTML 表單在收件端不作用(Outlook 剝除表單),投票鈕是唯一原生勾選 UI。
            # 仍只建草稿(.Display/.Save),絕不 .Send;投票由收件人於原生介面操作。
            if ($TemplateKey -like "approval_request*") {   # v0113:v2 豐富版同附投票鈕
                try { $Mail.VotingOptions = "進行中;已完成;卡關;需要協助" } catch { }
            }

            if ($OpenMode -eq "Display") { $Mail.Display($false) } else { $Mail.Save() }
            $Created++
            Write-Host ("   [草稿] {0} -> {1}  ({2})" -f $Row.ProjectCode, $Row.To, $TemplateKey) -ForegroundColor Green
        }
        catch { $Failed++; Write-Host ("   [失敗] {0}: {1}" -f $Row.ProjectCode, $_.Exception.Message) -ForegroundColor Red }
        finally { if ($Mail) { VO_ReleaseComObject -ComObject $Mail; $Mail = $null } }
    }

    if ($OpenMode -eq "Save" -and $Created -gt 0) {
        try {
            $Namespace = $Outlook.GetNamespace("MAPI")
            $Drafts = $Namespace.GetDefaultFolder(16)   # olFolderDrafts
            $Drafts.Display()
            VO_ReleaseComObject -ComObject $Drafts
            VO_ReleaseComObject -ComObject $Namespace
        } catch { }
    }
    VO_ReleaseComObject -ComObject $Outlook
    Write-Host ("   完成:草稿 {0} 封,失敗 {1} 封。請在 Outlook 檢視後親自按傳送。" -f $Created, $Failed) -ForegroundColor White
    return $true
}

function VO_Templates {
    VO_ScaffoldTemplates
    Write-Host (">> [範本] 範本庫:{0}" -f $TemplateDir) -ForegroundColor Green
    Write-Host ("   收件人清單:{0}" -f $RecipientsCsv)
    Write-Host ("   控管表範例:{0}" -f $ControlSheet)
    try { if (Test-Path -LiteralPath $TemplateDir) { Start-Process -FilePath $TemplateDir | Out-Null } } catch { }
    return $true
}

# ==========================================================================================
# 09. MENU (numeric single-key; minimal typing)
# ==========================================================================================
function VO_Banner {
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host (" Veritas MailOps · One-Script Compliance Edition {0}" -f $Script:APP_VERSION) -ForegroundColor Cyan
    Write-Host " 郵件只佐證 · 控管表治理 · 你核准才生效 · 不自動寄 · 不自動寫回" -ForegroundColor DarkGray
    Write-Host "==========================================================" -ForegroundColor Cyan
}

function VO_Menu {
    while ($true) {
        Write-Host ""
        VO_Banner
        Write-Host " [1] 掃描   只讀你的 Outlook -> out\*.csv" -ForegroundColor White
        Write-Host " [2] 對帳   控管表 × 郵件 -> out\proposals.csv(建議)" -ForegroundColor White
        Write-Host " [3] 追蹤信 建草稿(選擇題),你親自寄" -ForegroundColor White
        Write-Host " [4] 補追殺 建『再次追蹤』草稿" -ForegroundColor White
        Write-Host " [5] 範本   建立 / 開啟 templates 與範例 CSV" -ForegroundColor White
        Write-Host " [6] 全部   掃描 -> 對帳 -> 建草稿" -ForegroundColor White
        Write-Host " [0] 離開" -ForegroundColor DarkGray
        $c = Read-Host " 請選擇"
        switch ($c) {
            "1" { VO_RunAction "Scan" }
            "2" { VO_RunAction "Reconcile" }
            "3" { VO_RunAction "Draft" }
            "4" { VO_RunAction "FollowUp" }
            "5" { VO_RunAction "Templates" }
            "6" { VO_RunAction "All" }
            "0" { return }
            default { Write-Host " 請輸入 0-6。" -ForegroundColor Yellow }
        }
    }
}

# ==========================================================================================
# 10. ACTION DISPATCH (+ STA relaunch for COM actions)
# ==========================================================================================
function VO_RunAction {
    param([string]$Act)
    $needsCom = @("Scan","Draft","FollowUp","All") -contains $Act
    if ($needsCom -and (VO_RelaunchInStaIfNeeded -ForAction $Act)) {
        Write-Host " (已在 STA 子行程開啟以連接 Outlook COM)" -ForegroundColor DarkGray
        return
    }
    switch ($Act) {
        "Scan"      { $null = VO_Scan }
        "Reconcile" { $null = VO_Reconcile }
        "Draft"     { $null = VO_Draft -DraftMode "Initial" }
        "FollowUp"  { $null = VO_Draft -DraftMode "FollowUp" }
        "Templates" { $null = VO_Templates }
        "All" {
            if (VO_Scan) { $null = VO_Reconcile }
            $null = VO_Draft -DraftMode "Initial"
        }
    }
}

# ==========================================================================================
# 11. ENTRY  (skipped when the script is dot-sourced, e.g. for unit testing)
# ==========================================================================================
if ($MyInvocation.InvocationName -ne '.') {
    try {
        if ($Action -eq "Menu") { VO_Menu }
        else { VO_RunAction $Action }
    }
    catch {
        Write-Host (">> 發生未預期錯誤:{0}" -f $_.Exception.Message) -ForegroundColor Red
    }
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
