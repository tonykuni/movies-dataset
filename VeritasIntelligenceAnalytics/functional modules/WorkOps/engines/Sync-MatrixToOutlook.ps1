# =============================================================================
# Sync-MatrixToOutlook.ps1  v1.0
# 通用工作矩陣 -> Outlook 行事曆 同步器
# -----------------------------------------------------------------------------
# 規則:
#   R1 追蹤日期有值且狀態非已完成  -> 建立「期限前追蹤」提醒(當日 09:00,15 分鐘)
#   R2 會前追蹤日有值              -> 建立「會前 3 天追蹤信」提醒(當日 09:00)
#   R3 狀態=卡住                   -> 建立「斷點催辦」提醒(明日 09:00)
#   R4 每日 17:30「下班前 Review」週期性提醒(僅首次建立一次)
# 防重複: 以 Categories=工作矩陣 + Subject 前綴 [矩陣 編號] + 同日期 判斷,已存在則略過
# 備援:   無 Outlook 時輸出 WorkMatrix_Reminders.ics,可匯入任何行事曆(含 OWA)
# 慣例:   單檔貼上即跑 / 無別名 / 無 Read-Host / UTF8 無 BOM / 結尾開啟 HTML 報告
# =============================================================================
param(
    [string]$MatrixPath = (Join-Path -Path (Get-Location).Path -ChildPath 'WorkMatrix.xlsx'),
    [int]$LookAheadDays = 120,
    [switch]$AddDailyReview
)

$script:Rows      = @()
$script:Planned   = @()
$script:Created   = 0
$script:Skipped   = 0
$script:Failed    = 0
$script:Mode      = 'OUTLOOK'
$script:LogLines  = @()

function Write-SyncLog {
    param([string]$Message)
    $stamp = (Get-Date).ToString('HH:mm:ss')
    $line = '[' + $stamp + '] ' + $Message
    $script:LogLines += $line
    Write-Host $line
}

# ---------------------------------------------------------------- 讀取矩陣
function Read-MatrixRows {
    param([string]$FilePath)
    $result = @()
    if (-not (Test-Path -Path $FilePath)) {
        Write-SyncLog ('找不到矩陣檔案: ' + $FilePath)
        return ,$result
    }
    $ext = [System.IO.Path]::GetExtension($FilePath).ToLowerInvariant()
    if ($ext -eq '.csv') {
        $csv = Import-Csv -Path $FilePath -Encoding UTF8
        foreach ($r in $csv) {
            $result += [pscustomobject]@{
                Id = $r.'編號'; Category = $r.'類別'; Name = $r.'事務名稱'
                Holder = $r.'進度在誰手上'; Counterpart = $r.'對口(等誰)'
                Status = $r.'狀態'
                PromiseDate = $r.'承諾日期'; FollowDate = $r.'追蹤日期(自動:承諾-2天)'
                MeetingDate = $r.'會議日期'; PreMeetDate = $r.'會前追蹤日(自動:會議-3天)'
                NextStep = $r.'下一步'
            }
        }
        return ,$result
    }
    # xlsx 路徑: 使用 Excel COM 唯讀開啟
    $excel = $null
    $wb = $null
    try {
        $excel = New-Object -ComObject Excel.Application
        $excel.Visible = $false
        $excel.DisplayAlerts = $false
        $wb = $excel.Workbooks.Open($FilePath, $null, $true)
        $ws = $wb.Worksheets.Item(1)
        $lastRow = $ws.Cells($ws.Rows.Count, 1).End(-4162).Row   # -4162 = xlUp
        for ($r = 2; $r -le $lastRow; $r++) {
            $idVal = [string]$ws.Cells($r, 1).Value2
            if ([string]::IsNullOrWhiteSpace($idVal)) { continue }
            $result += [pscustomobject]@{
                Id          = $idVal.Trim()
                Category    = [string]$ws.Cells($r, 2).Value2
                Name        = [string]$ws.Cells($r, 3).Value2
                Holder      = [string]$ws.Cells($r, 4).Value2
                Counterpart = [string]$ws.Cells($r, 5).Value2
                Status      = [string]$ws.Cells($r, 7).Value2
                PromiseDate = $ws.Cells($r, 8).Text
                FollowDate  = $ws.Cells($r, 9).Text
                MeetingDate = $ws.Cells($r, 10).Text
                PreMeetDate = $ws.Cells($r, 11).Text
                NextStep    = [string]$ws.Cells($r, 12).Value2
            }
        }
    }
    catch {
        Write-SyncLog ('Excel COM 讀取失敗: ' + $_.Exception.Message)
        Write-SyncLog '請改將矩陣另存為 CSV 後以 -MatrixPath 指定。'
    }
    finally {
        if ($null -ne $wb) { $wb.Close($false) | Out-Null }
        if ($null -ne $excel) {
            $excel.Quit()
            [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
        }
    }
    return ,$result
}

function ConvertTo-SafeDate {
    param([string]$Text)
    $parsed = [datetime]::MinValue
    $formats = @('yyyy-MM-dd', 'yyyy/M/d', 'yyyy/MM/dd', 'M/d/yyyy', 'yyyy-M-d')
    foreach ($f in $formats) {
        if ([datetime]::TryParseExact($Text, $f, [System.Globalization.CultureInfo]::InvariantCulture,
            [System.Globalization.DateTimeStyles]::None, [ref]$parsed)) { return $parsed }
    }
    if ([datetime]::TryParse($Text, [ref]$parsed)) { return $parsed }
    return $null
}

# ---------------------------------------------------------------- 產生提醒計畫
function Build-ReminderPlan {
    param([object[]]$MatrixRows, [int]$Horizon)
    $plan = @()
    $today = (Get-Date).Date
    $limit = $today.AddDays($Horizon)
    foreach ($row in $MatrixRows) {
        $tag = '[矩陣 ' + $row.Id + ']'
        $done = ($row.Status -eq '已完成')
        # R1 期限前追蹤
        if (-not $done -and -not [string]::IsNullOrWhiteSpace($row.FollowDate)) {
            $d = ConvertTo-SafeDate -Text $row.FollowDate
            if ($null -ne $d -and $d -ge $today -and $d -le $limit) {
                $plan += [pscustomobject]@{
                    Subject = $tag + ' 期限前追蹤:' + $row.Name
                    Start   = $d.AddHours(9)
                    Body    = '對口:' + $row.Counterpart + ' / 承諾日:' + $row.PromiseDate + ' / 下一步:' + $row.NextStep
                    Rule    = 'R1'
                }
            }
        }
        # R2 會前 3 天追蹤信
        if (-not [string]::IsNullOrWhiteSpace($row.PreMeetDate)) {
            $d = ConvertTo-SafeDate -Text $row.PreMeetDate
            if ($null -ne $d -and $d -ge $today -and $d -le $limit) {
                $plan += [pscustomobject]@{
                    Subject = $tag + ' 會前3天追蹤信:' + $row.Name
                    Start   = $d.AddHours(9)
                    Body    = '寄出議程 + 上次行動項目完成狀況 + 未結案清單。會議日:' + $row.MeetingDate
                    Rule    = 'R2'
                }
            }
        }
        # R3 卡住 -> 明日催辦
        if ($row.Status -eq '卡住') {
            $d = $today.AddDays(1)
            $plan += [pscustomobject]@{
                Subject = $tag + ' 斷點催辦:' + $row.Name
                Start   = $d.AddHours(9)
                Body    = '書面催辦,副本主管。對口:' + $row.Counterpart + '。再 2 天無結果即上報。'
                Rule    = 'R3'
            }
        }
    }
    return ,$plan
}

# ---------------------------------------------------------------- Outlook 寫入
function Sync-ToOutlook {
    param([object[]]$Plan, [switch]$WithDailyReview)
    $outlook = $null
    try { $outlook = New-Object -ComObject Outlook.Application }
    catch {
        Write-SyncLog ('無法連接 Outlook: ' + $_.Exception.Message)
        return $false
    }
    $ns  = $outlook.GetNamespace('MAPI')
    $cal = $ns.GetDefaultFolder(9)   # olFolderCalendar
    # 既有項目索引(防重複): Categories = 工作矩陣
    $existingKeys = New-Object 'System.Collections.Generic.HashSet[string]'
    $items = $cal.Items
    $items.IncludeRecurrences = $false
    $restricted = $items.Restrict("[Categories] = '工作矩陣'")
    foreach ($it in $restricted) {
        $k = $it.Subject + '|' + $it.Start.ToString('yyyyMMdd')
        [void]$existingKeys.Add($k)
    }
    foreach ($p in $Plan) {
        $key = $p.Subject + '|' + $p.Start.ToString('yyyyMMdd')
        if ($existingKeys.Contains($key)) {
            $script:Skipped++
            continue
        }
        try {
            $appt = $outlook.CreateItem(1)   # olAppointmentItem
            $appt.Subject = $p.Subject
            $appt.Start = $p.Start
            $appt.Duration = 15
            $appt.Body = $p.Body
            $appt.Categories = '工作矩陣'
            $appt.BusyStatus = 0             # 顯示為有空,不佔行程
            $appt.ReminderSet = $true
            $appt.ReminderMinutesBeforeStart = 0
            $appt.Save()
            $script:Created++
        }
        catch {
            $script:Failed++
            Write-SyncLog ('建立失敗: ' + $p.Subject + ' / ' + $_.Exception.Message)
        }
    }
    if ($WithDailyReview) {
        $reviewKey = '[矩陣] 下班前 Review'
        $hasReview = $false
        foreach ($it in $restricted) {
            if ($it.Subject -eq $reviewKey) { $hasReview = $true; break }
        }
        if (-not $hasReview) {
            $appt = $outlook.CreateItem(1)
            $appt.Subject = $reviewKey
            $appt.Start = (Get-Date).Date.AddHours(17).AddMinutes(30)
            $appt.Duration = 15
            $appt.Body = '1 今日新斷點入清單了嗎 2 明日到期有哪些 3 今日承諾都留痕了嗎 4 紅色案件今天推進了嗎'
            $appt.Categories = '工作矩陣'
            $appt.ReminderSet = $true
            $appt.ReminderMinutesBeforeStart = 0
            $pattern = $appt.GetRecurrencePattern()
            $pattern.RecurrenceType = 2      # olRecursWeekly
            $pattern.DayOfWeekMask = 62      # 週一至週五
            $appt.Save()
            $script:Created++
            Write-SyncLog '已建立週一至週五 17:30 下班前 Review 週期提醒。'
        }
    }
    return $true
}

# ---------------------------------------------------------------- ICS 備援
function Export-IcsFallback {
    param([object[]]$Plan, [string]$OutFile)
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine('BEGIN:VCALENDAR')
    [void]$sb.AppendLine('VERSION:2.0')
    [void]$sb.AppendLine('PRODID:-//WorkMatrix//Sync//ZH-TW')
    $seq = 0
    foreach ($p in $Plan) {
        $seq++
        $uid = 'workmatrix-' + $seq + '-' + $p.Start.ToString('yyyyMMdd') + '@local'
        [void]$sb.AppendLine('BEGIN:VEVENT')
        [void]$sb.AppendLine('UID:' + $uid)
        [void]$sb.AppendLine('DTSTART:' + $p.Start.ToString('yyyyMMddTHHmmss'))
        [void]$sb.AppendLine('DTEND:' + $p.Start.AddMinutes(15).ToString('yyyyMMddTHHmmss'))
        [void]$sb.AppendLine('SUMMARY:' + $p.Subject)
        [void]$sb.AppendLine('DESCRIPTION:' + ($p.Body -replace ',', '\,'))
        [void]$sb.AppendLine('BEGIN:VALARM')
        [void]$sb.AppendLine('TRIGGER:PT0M')
        [void]$sb.AppendLine('ACTION:DISPLAY')
        [void]$sb.AppendLine('DESCRIPTION:Reminder')
        [void]$sb.AppendLine('END:VALARM')
        [void]$sb.AppendLine('END:VEVENT')
    }
    [void]$sb.AppendLine('END:VCALENDAR')
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($OutFile, $sb.ToString(), $utf8NoBom)
    Write-SyncLog ('已輸出 ICS 備援檔: ' + $OutFile)
}

# ---------------------------------------------------------------- HTML 報告
function Write-HtmlReport {
    param([string]$OutFile, [object[]]$Plan)
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine('<!DOCTYPE html><html><head><meta charset="utf-8"><title>矩陣同步報告</title>')
    [void]$sb.AppendLine('<style>body{font-family:"Microsoft JhengHei",sans-serif;background:#f5f4f0;color:#26313a;margin:32px}')
    [void]$sb.AppendLine('h1{font-size:20px}table{border-collapse:collapse;width:100%;background:#fff}')
    [void]$sb.AppendLine('td,th{border:1px solid #dbd9d3;padding:6px 10px;font-size:13px;text-align:left}')
    [void]$sb.AppendLine('th{background:#2b3a42;color:#fff}.k{display:inline-block;margin-right:24px;font-size:14px}')
    [void]$sb.AppendLine('.n{font-size:26px;font-weight:bold;color:#0e7c86}</style></head><body>')
    [void]$sb.AppendLine('<h1>工作矩陣 → Outlook 同步報告 · ' + (Get-Date).ToString('yyyy-MM-dd HH:mm') + '</h1>')
    [void]$sb.AppendLine('<p><span class="k"><span class="n">' + $script:Created + '</span> 新建</span>')
    [void]$sb.AppendLine('<span class="k"><span class="n">' + $script:Skipped + '</span> 已存在略過</span>')
    [void]$sb.AppendLine('<span class="k"><span class="n">' + $script:Failed + '</span> 失敗</span>')
    [void]$sb.AppendLine('<span class="k">模式:' + $script:Mode + '</span></p>')
    [void]$sb.AppendLine('<table><tr><th>規則</th><th>日期時間</th><th>主旨</th></tr>')
    $sorted = $Plan | Sort-Object -Property @{e = 'Start'; desc = $false }
    foreach ($p in $sorted) {
        [void]$sb.AppendLine('<tr><td>' + $p.Rule + '</td><td>' + $p.Start.ToString('yyyy-MM-dd HH:mm') + '</td><td>' + $p.Subject + '</td></tr>')
    }
    [void]$sb.AppendLine('</table><h1>執行紀錄</h1><pre>' + ($script:LogLines -join [Environment]::NewLine) + '</pre>')
    [void]$sb.AppendLine('</body></html>')
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($OutFile, $sb.ToString(), $utf8NoBom)
}

# ================================================================ 主流程
Write-SyncLog ('讀取矩陣: ' + $MatrixPath)
$script:Rows = Read-MatrixRows -FilePath $MatrixPath
Write-SyncLog ('讀入 ' + $script:Rows.Count + ' 列事務')

$script:Planned = Build-ReminderPlan -MatrixRows $script:Rows -Horizon $LookAheadDays
Write-SyncLog ('產生 ' + $script:Planned.Count + ' 筆提醒計畫(未來 ' + $LookAheadDays + ' 天內)')

$ok = $false
if ($script:Planned.Count -gt 0 -or $AddDailyReview) {
    $ok = Sync-ToOutlook -Plan $script:Planned -WithDailyReview:$AddDailyReview
}
if (-not $ok) {
    $script:Mode = 'ICS-FALLBACK'
    $icsPath = Join-Path -Path (Split-Path -Path $MatrixPath -Parent) -ChildPath 'WorkMatrix_Reminders.ics'
    Export-IcsFallback -Plan $script:Planned -OutFile $icsPath
}

$reportPath = Join-Path -Path (Split-Path -Path $MatrixPath -Parent) -ChildPath 'MatrixSync_Report.html'
Write-HtmlReport -OutFile $reportPath -Plan $script:Planned
Write-SyncLog ('新建 ' + $script:Created + ' / 略過 ' + $script:Skipped + ' / 失敗 ' + $script:Failed)
Start-Process -FilePath $reportPath

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
