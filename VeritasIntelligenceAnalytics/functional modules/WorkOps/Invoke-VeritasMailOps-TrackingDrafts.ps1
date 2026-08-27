#requires -Version 5.1
<#
==========================================================================================
def Veritas MailOps Workbench · Tracking-Draft Template Engine
def Version : v001
def Mode    : LOCAL-ONLY / DRAFTS-FOR-REVIEW / NEVER-AUTO-SEND
def Policy  : 在你自己權限內、你自己的 Outlook 建立「草稿」，開啟供你檢視後手動寄出。
==========================================================================================

用途:
  幫你把「追蹤信」一鍵批次擬好草稿。每封信都內建「預填答案表」——收件人只要照
  格子填，回覆就不會漏掉狀態 / ETA / 阻礙 等關鍵資訊。你檢視、最少幅度修改後，
  自己按「傳送」。

明確不做(與 SafeLocal 同一條線):
  - 不自動寄信、不自動回信 —— 一律只建立草稿(Draft),由你本人按傳送。
  - 不讀取、不搬移、不刪除、不修改任何既有郵件。
  - 不使用 Microsoft Graph / OAuth / API / 網路;不建立排程工作;不改登錄檔;不要求系統管理員。
  - 不壓制、不繞過 Outlook 安全提示。若公司原則封鎖 Outlook COM,立即停止,不嘗試繞過。

第一次執行:
  若找不到範本資料夾,會自動在腳本旁建立 .\templates\ 與 recipients.csv 範例,
  然後結束。請編輯 recipients.csv(填你要追蹤的專案與收件人),再執行一次。

再次執行:
  讀 recipients.csv + 範本 -> 為每一列建立一封草稿。
  -OpenMode Display : 每封草稿直接開啟撰寫視窗供你檢視(適合少量)。
  -OpenMode Save    : 靜靜存進「草稿匣」並貼上分類標籤(適合大量),最後打開草稿匣。

執行:
  powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File ".\Invoke-VeritasMailOps-TrackingDrafts.ps1"
#>

# ==========================================================================================
# def 01. PARAMETERS
# ==========================================================================================
[CmdletBinding()]
param(
    [string]$TemplateDir = (Join-Path $PSScriptRoot "templates"),
    [string]$RecipientsCsv = (Join-Path $PSScriptRoot "recipients.csv"),
    [ValidateSet("Display", "Save")]
    [string]$OpenMode = "Display",
    [string]$Category = "VIA_Tracking",
    [string]$MyName = "Tony Huang",
    [string]$DefaultTemplate = "status_request",
    [ValidateSet("Initial", "FollowUp")]
    [string]$Mode = "Initial"
)

$Script:APP_VERSION = "v001"

# ==========================================================================================
# def 02. BOOTSTRAP (STA relaunch — Outlook COM prefers single-threaded apartment)
# ==========================================================================================
function def_RelaunchInStaIfNeeded {
    if ([Threading.Thread]::CurrentThread.GetApartmentState() -eq "STA") {
        return $false
    }
    $PwshPath = (Get-Process -Id $PID).Path
    $ArgList = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-STA",
        "-File", ('"{0}"' -f $PSCommandPath),
        "-TemplateDir", ('"{0}"' -f $TemplateDir),
        "-RecipientsCsv", ('"{0}"' -f $RecipientsCsv),
        "-OpenMode", $OpenMode,
        "-Category", ('"{0}"' -f $Category),
        "-MyName", ('"{0}"' -f $MyName),
        "-DefaultTemplate", $DefaultTemplate,
        "-Mode", $Mode
    )
    Start-Process -FilePath $PwshPath -ArgumentList $ArgList | Out-Null
    return $true
}

# ==========================================================================================
# def 03. SAFE HELPERS
# ==========================================================================================
function def_WriteUtf8 {
    param([string]$Path, [string]$Text)
    [IO.File]::WriteAllText($Path, $Text, (New-Object Text.UTF8Encoding($false)))
}

function def_ReleaseComObject {
    param($ComObject)
    if ($null -eq $ComObject) { return }
    try {
        if ([Runtime.InteropServices.Marshal]::IsComObject($ComObject)) {
            $null = [Runtime.InteropServices.Marshal]::FinalReleaseComObject($ComObject)
        }
    }
    catch {
    }
}

function def_HtmlEncode {
    param([string]$Text)
    if ([string]::IsNullOrEmpty($Text)) { return "" }
    return $Text.Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;")
}

# ==========================================================================================
# def 04. DEFAULT TEMPLATES (auto-scaffolded on first run)
# Each template's FIRST line is the subject:  <!-- SUBJECT: ... -->
# Placeholders:  {{ProjectCode}} {{ProjectName}} {{MyName}} {{Date}} + any recipients.csv column
# The "answer form" block is what makes replies complete.
# ==========================================================================================
function def_GetDefaultTemplates {
    # 選擇題式必回內容:對方多半只需「圈選 / 保留適用項」,幾乎免打字。
    $Answer = @'
      <table role="presentation" cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin:14px 0;width:100%;max-width:560px;">
        <tr><td style="background:#1e293b;color:#fff;font:700 13px 'Segoe UI',sans-serif;padding:8px 14px;border-radius:6px 6px 0 0;">請圈選或保留適用項後直接回覆(選項為主,幾乎免打字)</td></tr>
        <tr><td style="border:1px solid #e2e8f0;border-top:none;padding:12px 16px;font:400 13px 'Segoe UI',sans-serif;color:#1e293b;line-height:2.1;">
          1. 目前狀態： ○ 進行中　○ 已完成　○ 卡關<br/>
          2. 完成百分比： ○ 25%　○ 50%　○ 75%　○ 100%<br/>
          3. 預計完成 ETA： ○ 今日　○ 明日　○ 本週　○ 其他：__________<br/>
          4. 是否有阻礙 / 風險： ○ 無　○ 有：__________<br/>
          5. 是否需要我協助： ○ 否　○ 是：__________<br/>
        </td></tr>
      </table>
'@

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

    return @{
        "status_request"   = (& $Wrap "[追蹤] {{ProjectCode}} {{ProjectName}} - 進度確認" "想跟你確認 <b>{{ProjectName}}</b>({{ProjectCode}})目前的進度。" "")
        "eta_confirm"      = (& $Wrap "[追蹤] {{ProjectCode}} {{ProjectName}} - 交期確認" "想跟你再次確認 <b>{{ProjectName}}</b>({{ProjectCode}})的<b>預計完成 / 交期</b>是否仍如原訂。" "  <p style='color:#c0392b;'>如需調整交期,請於下方第 3 點圈選或填新日期並簡述原因。</p>")
        "blocker_check"    = (& $Wrap "[追蹤] {{ProjectCode}} {{ProjectName}} - 風險 / 阻礙盤點" "想確認 <b>{{ProjectName}}</b>({{ProjectCode}})目前是否有卡關或潛在風險,以便及早協助。" "")
        "approval_request" = (& $Wrap "[待核] {{ProjectCode}} {{ProjectName}} - 請確認 / 核准" "以下 <b>{{ProjectName}}</b>({{ProjectCode}})事項需要你確認或核准,煩請於下方圈選回覆。" "")
        "followup"         = (& $Wrap "[再次追蹤] {{ProjectCode}} {{ProjectName}} - 尚未收到回覆" "先前關於 <b>{{ProjectName}}</b>({{ProjectCode}})的進度確認尚未收到你的回覆,再麻煩你抽空圈選一下,謝謝!" "")
        "followup_firm"    = (& $Wrap "[急件·再追] {{ProjectCode}} {{ProjectName}} - 需盡快回覆" "<b>{{ProjectName}}</b>({{ProjectCode}})的進度已影響後續排程,今天內需要你的回覆。麻煩直接圈選下列項目即可:" "  <p style='color:#c0392b;'>若有困難請於第 5 點勾『是』並說明,我來協助排除。</p>")
    }
}

function def_ScaffoldTemplates {
    param([string]$Dir, [string]$CsvPath)

    if (-not (Test-Path -LiteralPath $Dir)) {
        $null = New-Item -ItemType Directory -Path $Dir -Force
    }

    $Templates = def_GetDefaultTemplates
    foreach ($Key in $Templates.Keys) {
        $File = Join-Path $Dir ("TPL_{0}.html" -f $Key)
        if (-not (Test-Path -LiteralPath $File)) {
            def_WriteUtf8 -Path $File -Text $Templates[$Key]
        }
    }

    if (-not (Test-Path -LiteralPath $CsvPath)) {
        $SampleCsv = @'
ProjectCode,ProjectName,To,Cc,Template
PRJ-001,日本合資案,someone@example.com,,status_request
PRJ-002,德商合約談判,another@example.com,manager@example.com,eta_confirm
PRJ-003,Q3 產線稽核,third@example.com,,blocker_check
'@
        def_WriteUtf8 -Path $CsvPath -Text $SampleCsv
    }
}

# ==========================================================================================
# def 05. TEMPLATE RENDERING
# ==========================================================================================
function def_LoadTemplate {
    param([string]$Dir, [string]$Key)
    $File = Join-Path $Dir ("TPL_{0}.html" -f $Key)
    if (-not (Test-Path -LiteralPath $File)) {
        return $null
    }
    return (Get-Content -LiteralPath $File -Raw -Encoding UTF8)
}

function def_RenderTemplate {
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

    return [pscustomobject]@{
        Subject = $Subject
        HtmlBody = $Body
    }
}

# ==========================================================================================
# def 06. OUTLOOK CONNECTION (attach to your running Classic Outlook; do not bypass)
# ==========================================================================================
function def_GetOutlook {
    try {
        return [Runtime.InteropServices.Marshal]::GetActiveObject("Outlook.Application")
    }
    catch {
    }
    try {
        return (New-Object -ComObject Outlook.Application)
    }
    catch {
        return $null
    }
}

# ==========================================================================================
# def 07. MAIN
# ==========================================================================================
function def_Main {
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host " Veritas MailOps · Tracking-Draft Template Engine $Script:APP_VERSION" -ForegroundColor Cyan
    Write-Host " 執行模式:$Mode  ·  只建立草稿供你檢視後手動寄出;不自動寄信。" -ForegroundColor DarkGray
    Write-Host "==========================================================" -ForegroundColor Cyan

    # First-run scaffold
    if (-not (Test-Path -LiteralPath $RecipientsCsv) -or -not (Test-Path -LiteralPath $TemplateDir)) {
        def_ScaffoldTemplates -Dir $TemplateDir -CsvPath $RecipientsCsv
        Write-Host ""
        Write-Host ">> 已建立範本與範例清單:" -ForegroundColor Green
        Write-Host "   範本資料夾 : $TemplateDir"
        Write-Host "   收件人清單 : $RecipientsCsv"
        Write-Host ""
        Write-Host ">> 下一步:編輯 recipients.csv 填入你的專案與收件人,再執行一次本腳本。" -ForegroundColor Yellow
        return
    }

    $Rows = @(Import-Csv -LiteralPath $RecipientsCsv -Encoding UTF8)
    if ($Rows.Count -eq 0) {
        Write-Host ">> recipients.csv 沒有任何資料列。" -ForegroundColor Yellow
        return
    }

    $Outlook = def_GetOutlook
    if ($null -eq $Outlook) {
        Write-Host ">> 無法連上 Classic Outlook COM。請先開啟 Classic Outlook for Windows。" -ForegroundColor Red
        Write-Host "   (若公司政策封鎖 COM,本工具在此停止,不會嘗試繞過。)" -ForegroundColor DarkGray
        return
    }

    $Today = (Get-Date).ToString("yyyy/MM/dd")
    $Created = 0
    $Failed = 0

    foreach ($Row in $Rows) {
        try {
            $EffectiveDefault = if ($Mode -eq "FollowUp") { "followup" } else { $DefaultTemplate }
            $TemplateKey = if ([string]::IsNullOrWhiteSpace($Row.Template)) { $EffectiveDefault } else { $Row.Template.Trim() }
            $Raw = def_LoadTemplate -Dir $TemplateDir -Key $TemplateKey
            if ($null -eq $Raw) {
                Write-Host "   [略過] 找不到範本 TPL_$TemplateKey.html($($Row.ProjectCode))" -ForegroundColor DarkYellow
                $Failed++
                continue
            }

            # Build substitution set: every CSV column + standard tokens
            $Values = @{}
            foreach ($Prop in $Row.PSObject.Properties) {
                $Values[$Prop.Name] = [string]$Prop.Value
            }
            $Values["MyName"] = $MyName
            $Values["Date"] = $Today

            $Rendered = def_RenderTemplate -Raw $Raw -Values $Values

            $Mail = $Outlook.CreateItem(0)   # 0 = olMailItem
            $Mail.Subject = $Rendered.Subject
            if (-not [string]::IsNullOrWhiteSpace($Row.To)) { $Mail.To = [string]$Row.To }
            if (($Row.PSObject.Properties.Name -contains "Cc") -and -not [string]::IsNullOrWhiteSpace($Row.Cc)) {
                $Mail.CC = [string]$Row.Cc
            }
            $Mail.HTMLBody = $Rendered.HtmlBody
            try { $Mail.Categories = $Category } catch {}

            if ($OpenMode -eq "Display") {
                $Mail.Display($false)        # open compose window for your review (does NOT send)
            }
            else {
                $Mail.Save()                 # quietly to Drafts (does NOT send)
            }

            $Created++
            Write-Host "   [草稿] $($Row.ProjectCode) -> $($Row.To)  ($TemplateKey)" -ForegroundColor Green
        }
        catch {
            $Failed++
            Write-Host "   [失敗] $($Row.ProjectCode): $($_.Exception.Message)" -ForegroundColor Red
        }
        finally {
            if ($Mail) { def_ReleaseComObject -ComObject $Mail; $Mail = $null }
        }
    }

    # If Save mode, open the Drafts folder so you can review them all together.
    if ($OpenMode -eq "Save" -and $Created -gt 0) {
        try {
            $Namespace = $Outlook.GetNamespace("MAPI")
            $Drafts = $Namespace.GetDefaultFolder(16)   # 16 = olFolderDrafts
            $Drafts.Display()
            def_ReleaseComObject -ComObject $Drafts
            def_ReleaseComObject -ComObject $Namespace
        }
        catch {
        }
    }

    def_ReleaseComObject -ComObject $Outlook

    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host " 完成:建立草稿 $Created 封,失敗 $Failed 封。" -ForegroundColor White
    Write-Host " 請在 Outlook 檢視 / 微調後,由你本人按「傳送」。" -ForegroundColor Yellow
    Write-Host "==========================================================" -ForegroundColor Cyan
}

# ==========================================================================================
# def 08. ENTRY
# ==========================================================================================
if (def_RelaunchInStaIfNeeded) {
    return
}

try {
    def_Main
}
catch {
    Write-Host ">> 發生未預期錯誤:$($_.Exception.Message)" -ForegroundColor Red
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
