#requires -Version 7.0
# ======================================================================================
# def VIA · Batch Mailer (自己帳號 · 官方管道 · 節流防誤判) v001
# def 用途：把資料夾內每個檔案，透過「你自己的 Outlook 桌機(COM)或 Gmail(SMTP)」逐封寄出。
# def 設計原則：
# def   1. 走官方寄信管道（COM / SMTP），不做 UI 模擬點擊/複製貼上——那才會觸發盜帳號偵測。
# def   2. 預設 dry-run；要真的寄出必須加 -Send。
# def   3. 隨機節流(20–45 秒抖動) + 每次上限，避免爆量像 spam/被鎖帳號。
# def   4. Gmail 密碼一律讀環境變數 $env:VIA_GMAIL_APP_PW，絕不寫死在檔案。
# def   5. append-only 台帳(csv)，每封記錄，可稽核。
# def 規則：no Read-Host、param 首行、UTF8 No-BOM、def_ 命名。
# ======================================================================================

param(
    [Parameter(Mandatory = $true)][string]$SourceFolder,
    [string]$Filter = "*.md",
    [ValidateSet("Outlook", "Gmail")][string]$Provider = "Outlook",
    [Parameter(Mandatory = $true)][string]$To,
    [string]$Cc = "",
    [string]$SubjectPrefix = "[VIA] ",
    [ValidateSet("Inline", "Attach", "Both")][string]$BodyMode = "Both",
    [string]$GmailUser = "",
    [int]$MinDelaySec = 20,
    [int]$MaxDelaySec = 45,
    [int]$MaxPerRun = 50,
    [switch]$Send
)

$ErrorActionPreference = "Stop"

function def_WriteUtf8NoBom {
    param([string]$Path, [string]$Text)
    $enc = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $enc)
}

function def_ReadBodyFromFile {
    param([string]$Path, [string]$Extension)
    if ($Extension -in @(".md", ".txt", ".csv", ".json", ".html", ".htm", ".log")) {
        return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
    }
    return "（此檔為二進位/非文字格式，內容以附件寄出）"
}

function def_SendViaOutlook {
    param([string]$To, [string]$Cc, [string]$Subject, [string]$Body, [string]$AttachPath, [bool]$DoAttach, [bool]$DoInline)
    $ol = New-Object -ComObject Outlook.Application
    try {
        $mail = $ol.CreateItem(0)          # olMailItem
        $mail.To = $To
        if ($Cc) { $mail.CC = $Cc }
        $mail.Subject = $Subject
        if ($DoInline) { $mail.Body = $Body } else { $mail.Body = "（內容見附件）" }
        if ($DoAttach -and $AttachPath) { [void]$mail.Attachments.Add($AttachPath) }
        $mail.Send()
    }
    finally {
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($ol) | Out-Null
    }
}

function def_SendViaGmail {
    param([string]$From, [string]$To, [string]$Cc, [string]$Subject, [string]$Body, [string]$AttachPath, [bool]$DoAttach, [bool]$DoInline)
    $pw = $env:VIA_GMAIL_APP_PW
    if ([string]::IsNullOrWhiteSpace($pw)) {
        throw "缺少 Gmail 應用程式密碼：請先設定環境變數 VIA_GMAIL_APP_PW（Google 帳號→安全性→應用程式密碼）。"
    }
    if ([string]::IsNullOrWhiteSpace($From)) { throw "Gmail 模式需提供 -GmailUser you@gmail.com" }

    $smtp = New-Object System.Net.Mail.SmtpClient("smtp.gmail.com", 587)
    $smtp.EnableSsl = $true
    $smtp.Credentials = New-Object System.Net.NetworkCredential($From, $pw)

    $msg = New-Object System.Net.Mail.MailMessage
    try {
        $msg.From = $From
        $msg.To.Add($To)
        if ($Cc) { $msg.CC.Add($Cc) }
        $msg.Subject = $Subject
        $isHtml = ($AttachPath.ToLowerInvariant().EndsWith(".html") -or $AttachPath.ToLowerInvariant().EndsWith(".htm"))
        $msg.IsBodyHtml = ($DoInline -and $isHtml)
        $msg.Body = if ($DoInline) { $Body } else { "（內容見附件）" }
        if ($DoAttach -and $AttachPath) {
            $msg.Attachments.Add((New-Object System.Net.Mail.Attachment($AttachPath)))
        }
        $smtp.Send($msg)
    }
    finally {
        $msg.Dispose()
        $smtp.Dispose()
    }
}

function def_Main {
    if (-not (Test-Path -LiteralPath $SourceFolder)) { throw "找不到來源資料夾：$SourceFolder" }

    $files = @(Get-ChildItem -LiteralPath $SourceFolder -File -Filter $Filter | Sort-Object Name)
    if ($files.Count -eq 0) { Write-Host "def 無符合檔案（$Filter）。" -ForegroundColor Yellow; return }

    if ($files.Count -gt $MaxPerRun) {
        Write-Host ("def 本次 {0} 檔超過上限 {1}，只處理前 {1} 檔（其餘下次跑）。" -f $files.Count, $MaxPerRun) -ForegroundColor Yellow
        $files = $files[0..($MaxPerRun - 1)]
    }

    $doInline = ($BodyMode -in @("Inline", "Both"))
    $doAttach = ($BodyMode -in @("Attach", "Both"))

    $ledger = @()
    $mode = if ($Send) { "SEND" } else { "DRY-RUN（未加 -Send，不會真的寄出）" }

    Write-Host ""
    Write-Host "====================================================================" -ForegroundColor DarkCyan
    Write-Host "def VIA Batch Mailer · $Provider · $mode" -ForegroundColor Cyan
    Write-Host "def 收件：$To  副本：$Cc  檔數：$($files.Count)  節流：$MinDelaySec–$MaxDelaySec 秒" -ForegroundColor White
    Write-Host "====================================================================" -ForegroundColor DarkCyan

    $i = 0
    foreach ($f in $files) {
        $i++
        $subject = "$SubjectPrefix$($f.BaseName)"
        $body = if ($doInline) { def_ReadBodyFromFile -Path $f.FullName -Extension $f.Extension.ToLowerInvariant() } else { "" }
        $status = "DRYRUN"; $err = ""

        Write-Host ("[{0}/{1}] {2}  →  {3}" -f $i, $files.Count, $f.Name, $subject) -ForegroundColor Gray

        if ($Send) {
            try {
                if ($Provider -eq "Outlook") {
                    def_SendViaOutlook -To $To -Cc $Cc -Subject $subject -Body $body -AttachPath $f.FullName -DoAttach $doAttach -DoInline $doInline
                }
                else {
                    def_SendViaGmail -From $GmailUser -To $To -Cc $Cc -Subject $subject -Body $body -AttachPath $f.FullName -DoAttach $doAttach -DoInline $doInline
                }
                $status = "SENT"
            }
            catch {
                $status = "FAIL"; $err = $_.Exception.Message
                Write-Host ("    def FAIL: {0}" -f $err) -ForegroundColor Red
            }

            if ($i -lt $files.Count) {
                $wait = Get-Random -Minimum $MinDelaySec -Maximum ($MaxDelaySec + 1)
                Write-Host ("    def 節流等待 {0} 秒…" -f $wait) -ForegroundColor DarkGray
                Start-Sleep -Seconds $wait
            }
        }

        $ledger += [pscustomobject]@{
            ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            file = $f.Name; subject = $subject; provider = $Provider
            to = $To; status = $status; error = $err
        }
    }

    $ledgerPath = Join-Path $SourceFolder ("_via_mail_ledger_{0}.csv" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
    $ledger | Export-Csv -LiteralPath $ledgerPath -NoTypeInformation -Encoding UTF8BOM

    Write-Host ""
    Write-Host ("def 完成。SENT={0}  FAIL={1}  DRYRUN={2}" -f `
        (@($ledger | Where-Object status -eq 'SENT').Count), `
        (@($ledger | Where-Object status -eq 'FAIL').Count), `
        (@($ledger | Where-Object status -eq 'DRYRUN').Count)) -ForegroundColor Green
    Write-Host "def 台帳：$ledgerPath" -ForegroundColor Green
    if (-not $Send) { Write-Host "def 這是預覽。確認無誤後，加 -Send 重跑才會真的寄出。" -ForegroundColor Cyan }
}

try { def_Main }
catch {
    Write-Host ""
    Write-Host "def OUTER SAFE CATCH" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}
