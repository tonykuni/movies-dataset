#requires -Version 5.1
<#
.SYNOPSIS
    VIA WorkOps - Outlook 指定時間範圍全資料夾唯讀郵件索引器。

.DESCRIPTION
    - 只使用目前使用者的 Classic Outlook COM Profile。
    - 遞迴讀取目前 Outlook Profile 中的所有 Store 與郵件資料夾。
    - 只讀，不修改已讀狀態、分類、旗標、資料夾、附件或郵件內容。
    - 不需管理員權限、不安裝模組、不修改 Registry、不建立排程、不連接額外 API。
    - 以 run-local 方式輸出 CSV、JSON 與 HTML 報告。

.NOTES
    VERITAS INTELLIGENCE ANALYTICS
    VIA WorkOps Intelligence Workbench
    VIA 日常作業與專案管理智慧工作台
#>

[CmdletBinding()]
param(
    # ============================== def 使用者參數區 ==============================
    [datetime]$StartTime = (Get-Date).Date.AddDays(-1),
    [datetime]$EndTime = (Get-Date),

    [string]$OutputRoot = (Join-Path $env:USERPROFILE 'Downloads\VIA_WorkOps_Mail_ReadOnly_Exports'),

    [bool]$IncludeSubfolders = $true,
    [bool]$IncludeSearchFolders = $false,
    [bool]$IncludePublicFolders = $false,
    [bool]$IncludeMeetingItems = $true,

    # 預設不讀取／輸出內文；需要摘要時才明確開啟。
    [bool]$IncludeBodySnippet = $false,
    [ValidateRange(100, 5000)]
    [int]$BodySnippetLength = 800,

    [bool]$IncludeAttachmentNames = $true,
    [bool]$UseRestrict = $true,

    # 0 = 不設上限；僅用於極大資料夾的安全試跑。
    [ValidateRange(0, 10000000)]
    [int]$MaxItemsPerFolder = 0,

    [bool]$OpenReport = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ============================== def 固定安全政策 ==============================
$SCRIPT_VERSION = 'v001'
$POLICY = 'read-only / user-scope / no install / no registry / no mail mutation / no attachment save / run-local output'
$MAIL_ITEM_CLASS = 43
$MEETING_ITEM_CLASS = 53
$SEARCH_FOLDER_PATTERNS = @('Search Folders', '搜尋資料夾', '検索フォルダー')
$PUBLIC_STORE_PATTERNS = @('Public Folders', '公用資料夾', '公共資料夾')
$INTERNET_MESSAGE_ID_PROPS = @(
    'http://schemas.microsoft.com/mapi/proptag/0x1035001F',
    'http://schemas.microsoft.com/mapi/proptag/0x1035001E'
)

# ============================== def 全域執行狀態 ==============================
$script:MailRows = [System.Collections.Generic.List[object]]::new()
$script:FolderRows = [System.Collections.Generic.List[object]]::new()
$script:ErrorRows = [System.Collections.Generic.List[object]]::new()
$script:SeenItemKeys = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
$script:FolderCounter = 0
$script:ScannedItemCounter = 0
$script:MatchedItemCounter = 0
$script:RestrictedFolderCounter = 0
$script:FallbackFolderCounter = 0

# def 輸出安全字串
function def_ToSafeString {
    [CmdletBinding()]
    param([AllowNull()]$Value)

    if ($null -eq $Value) { return '' }
    try { return [string]$Value } catch { return '' }
}

# def COM 物件釋放；不關閉使用者 Outlook
function def_ReleaseComObject {
    [CmdletBinding()]
    param([AllowNull()]$ComObject)

    if ($null -eq $ComObject) { return }
    try {
        if ([Runtime.InteropServices.Marshal]::IsComObject($ComObject)) {
            [void][Runtime.InteropServices.Marshal]::ReleaseComObject($ComObject)
        }
    }
    catch {
        # 僅釋放參考，失敗不影響掃描結果。
    }
}

# def 記錄錯誤但不中止其他資料夾
function def_AddError {
    [CmdletBinding()]
    param(
        [string]$Stage,
        [string]$StoreName,
        [string]$FolderPath,
        [string]$Message
    )

    $script:ErrorRows.Add([pscustomobject][ordered]@{
        TIME        = (Get-Date).ToString('yyyy/MM/dd HH:mm:ss')
        STAGE       = $Stage
        STORE_NAME  = $StoreName
        FOLDER_PATH = $FolderPath
        ERROR       = $Message
    })
}

# def 計算 SHA256
function def_GetSha256Text {
    [CmdletBinding()]
    param([AllowEmptyString()][string]$Text)

    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
        return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $sha.Dispose()
    }
}

# def 清理單行文字
function def_NormalizeSingleLine {
    [CmdletBinding()]
    param(
        [AllowNull()][string]$Text,
        [int]$MaxLength = 0
    )

    if ([string]::IsNullOrWhiteSpace($Text)) { return '' }
    $clean = [regex]::Replace($Text, '[\r\n\t]+', ' ')
    $clean = [regex]::Replace($clean, '\s{2,}', ' ').Trim()
    if ($MaxLength -gt 0 -and $clean.Length -gt $MaxLength) {
        return $clean.Substring(0, $MaxLength)
    }
    return $clean
}

# def 取得安全 DateTime
function def_GetDateValue {
    [CmdletBinding()]
    param([AllowNull()]$Value)

    try {
        if ($null -eq $Value) { return $null }
        $dateValue = [datetime]$Value
        if ($dateValue.Year -lt 1900) { return $null }
        return $dateValue
    }
    catch {
        return $null
    }
}

# def 判定郵件事件時間與方向
function def_GetMailTiming {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Item)

    $isSent = $false
    try { $isSent = [bool]$Item.Sent } catch { $isSent = $false }

    $receivedTime = $null
    $sentTime = $null
    $creationTime = $null
    $modifiedTime = $null

    try { $receivedTime = def_GetDateValue -Value $Item.ReceivedTime } catch {}
    try { $sentTime = def_GetDateValue -Value $Item.SentOn } catch {}
    try { $creationTime = def_GetDateValue -Value $Item.CreationTime } catch {}
    try { $modifiedTime = def_GetDateValue -Value $Item.LastModificationTime } catch {}

    $eventTime = $null
    $direction = 'UNKNOWN'

    if ($isSent -and $null -ne $sentTime) {
        $eventTime = $sentTime
        $direction = 'OUTBOUND'
    }
    elseif ($null -ne $receivedTime) {
        $eventTime = $receivedTime
        $direction = 'INBOUND'
    }
    elseif ($null -ne $sentTime) {
        $eventTime = $sentTime
        $direction = 'OUTBOUND'
    }
    elseif ($null -ne $creationTime) {
        $eventTime = $creationTime
        $direction = 'DRAFT_OR_LOCAL'
    }

    return [pscustomobject]@{
        EVENT_TIME       = $eventTime
        DIRECTION        = $direction
        RECEIVED_TIME    = $receivedTime
        SENT_TIME        = $sentTime
        CREATION_TIME    = $creationTime
        MODIFIED_TIME    = $modifiedTime
    }
}

# def 取得 Internet Message ID
function def_GetInternetMessageId {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Item)

    $accessor = $null
    try {
        $accessor = $Item.PropertyAccessor
        foreach ($propertyName in $INTERNET_MESSAGE_ID_PROPS) {
            try {
                $value = def_ToSafeString -Value $accessor.GetProperty($propertyName)
                if (-not [string]::IsNullOrWhiteSpace($value)) { return $value.Trim() }
            }
            catch {}
        }
    }
    catch {}
    finally {
        def_ReleaseComObject -ComObject $accessor
    }
    return ''
}

# def 取得附件名稱但不儲存附件
function def_GetAttachmentInfo {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Item)

    $attachmentCollection = $null
    $names = [System.Collections.Generic.List[string]]::new()
    $count = 0

    try {
        $attachmentCollection = $Item.Attachments
        $count = [int]$attachmentCollection.Count
        if ($IncludeAttachmentNames -and $count -gt 0) {
            for ($index = 1; $index -le $count; $index++) {
                $attachment = $null
                try {
                    $attachment = $attachmentCollection.Item($index)
                    $name = def_NormalizeSingleLine -Text (def_ToSafeString -Value $attachment.FileName) -MaxLength 260
                    if (-not [string]::IsNullOrWhiteSpace($name)) { $names.Add($name) }
                }
                catch {}
                finally {
                    def_ReleaseComObject -ComObject $attachment
                }
            }
        }
    }
    catch {}
    finally {
        def_ReleaseComObject -ComObject $attachmentCollection
    }

    return [pscustomobject]@{
        COUNT = $count
        NAMES = ($names -join ' | ')
    }
}

# def 取得郵件類型
function def_GetItemTypeName {
    [CmdletBinding()]
    param([int]$ItemClass)

    switch ($ItemClass) {
        $MAIL_ITEM_CLASS { return 'MAIL' }
        $MEETING_ITEM_CLASS { return 'MEETING_MESSAGE' }
        default { return "CLASS_$ItemClass" }
    }
}

# def 判定項目是否納入
function def_IsSupportedItem {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Item)

    try {
        $itemClass = [int]$Item.Class
        if ($itemClass -eq $MAIL_ITEM_CLASS) { return $true }
        if ($IncludeMeetingItems -and $itemClass -eq $MEETING_ITEM_CLASS) { return $true }
    }
    catch {}
    return $false
}

# def 建立不重複項目鍵
function def_GetItemKey {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Item,
        [string]$StoreId,
        [string]$FolderPath
    )

    $entryId = ''
    try { $entryId = def_ToSafeString -Value $Item.EntryID } catch {}
    if (-not [string]::IsNullOrWhiteSpace($entryId)) {
        return "$StoreId|$entryId"
    }

    $subject = ''
    $size = ''
    $creation = ''
    try { $subject = def_ToSafeString -Value $Item.Subject } catch {}
    try { $size = def_ToSafeString -Value $Item.Size } catch {}
    try { $creation = ([datetime]$Item.CreationTime).ToString('o') } catch {}
    return def_GetSha256Text -Text "$StoreId|$FolderPath|$subject|$size|$creation"
}

# def 將一封郵件轉為索引列
function def_ProcessItem {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Item,
        [string]$StoreName,
        [string]$StoreId,
        [string]$FolderPath,
        [string]$FolderName
    )

    $script:ScannedItemCounter++

    if (-not (def_IsSupportedItem -Item $Item)) { return $false }

    $timing = def_GetMailTiming -Item $Item
    if ($null -eq $timing.EVENT_TIME) { return $false }
    if ($timing.EVENT_TIME -lt $StartTime -or $timing.EVENT_TIME -gt $EndTime) { return $false }

    $itemKey = def_GetItemKey -Item $Item -StoreId $StoreId -FolderPath $FolderPath
    if (-not $script:SeenItemKeys.Add($itemKey)) { return $false }

    $subject = ''
    $senderName = ''
    $senderAddress = ''
    $toText = ''
    $ccText = ''
    $categories = ''
    $messageClass = ''
    $entryId = ''
    $conversationId = ''
    $conversationTopic = ''
    $unread = $null
    $flagStatus = ''
    $importance = ''
    $sizeBytes = 0
    $bodySnippet = ''

    try { $subject = def_NormalizeSingleLine -Text (def_ToSafeString -Value $Item.Subject) -MaxLength 1000 } catch {}
    try { $senderName = def_NormalizeSingleLine -Text (def_ToSafeString -Value $Item.SenderName) -MaxLength 500 } catch {}
    try { $senderAddress = def_NormalizeSingleLine -Text (def_ToSafeString -Value $Item.SenderEmailAddress) -MaxLength 500 } catch {}
    try { $toText = def_NormalizeSingleLine -Text (def_ToSafeString -Value $Item.To) -MaxLength 4000 } catch {}
    try { $ccText = def_NormalizeSingleLine -Text (def_ToSafeString -Value $Item.CC) -MaxLength 4000 } catch {}
    try { $categories = def_NormalizeSingleLine -Text (def_ToSafeString -Value $Item.Categories) -MaxLength 1000 } catch {}
    try { $messageClass = def_ToSafeString -Value $Item.MessageClass } catch {}
    try { $entryId = def_ToSafeString -Value $Item.EntryID } catch {}
    try { $conversationId = def_ToSafeString -Value $Item.ConversationID } catch {}
    try { $conversationTopic = def_NormalizeSingleLine -Text (def_ToSafeString -Value $Item.ConversationTopic) -MaxLength 1000 } catch {}
    try { $unread = [bool]$Item.UnRead } catch { $unread = $null }
    try { $flagStatus = def_ToSafeString -Value $Item.FlagStatus } catch {}
    try { $importance = def_ToSafeString -Value $Item.Importance } catch {}
    try { $sizeBytes = [int64]$Item.Size } catch { $sizeBytes = 0 }

    if ($IncludeBodySnippet) {
        try {
            $bodySnippet = def_NormalizeSingleLine -Text (def_ToSafeString -Value $Item.Body) -MaxLength $BodySnippetLength
        }
        catch {
            $bodySnippet = ''
        }
    }

    $attachmentInfo = def_GetAttachmentInfo -Item $Item
    $internetMessageId = def_GetInternetMessageId -Item $Item
    $readStatus = if ($null -eq $unread) { 'UNKNOWN' } elseif ($unread) { 'UNREAD' } else { 'READ' }
    $mailKeyBasis = if (-not [string]::IsNullOrWhiteSpace($internetMessageId)) {
        "IMID|$internetMessageId"
    }
    else {
        "$senderAddress|$($timing.EVENT_TIME.ToString('o'))|$subject|$sizeBytes|$conversationId"
    }

    $itemClassValue = 0
    try { $itemClassValue = [int]$Item.Class } catch {}

    $script:MailRows.Add([pscustomobject][ordered]@{
        TIME                  = $timing.EVENT_TIME.ToString('yyyy/MM/dd HH:mm:ss')
        DIRECTION             = $timing.DIRECTION
        ITEM_TYPE             = def_GetItemTypeName -ItemClass $itemClassValue
        TITLE                 = $subject
        FROM                  = $senderName
        FROM_ADDRESS          = $senderAddress
        TO                    = $toText
        CC                    = $ccText
        READ_STATUS           = $readStatus
        IMPORTANCE            = $importance
        FLAG_STATUS           = $flagStatus
        CATEGORIES            = $categories
        ATTACHMENT_COUNT      = $attachmentInfo.COUNT
        ATTACHMENT_NAMES      = $attachmentInfo.NAMES
        BODY_SNIPPET          = $bodySnippet
        STORE_NAME            = $StoreName
        FOLDER_NAME           = $FolderName
        FOLDER_PATH           = $FolderPath
        MESSAGE_CLASS         = $messageClass
        CONVERSATION_TOPIC    = $conversationTopic
        CONVERSATION_ID       = $conversationId
        INTERNET_MESSAGE_ID   = $internetMessageId
        MAIL_FINGERPRINT      = def_GetSha256Text -Text $mailKeyBasis
        ENTRY_ID              = $entryId
        STORE_ID              = $StoreId
        SIZE_BYTES            = $sizeBytes
        RECEIVED_TIME         = if ($null -ne $timing.RECEIVED_TIME) { $timing.RECEIVED_TIME.ToString('yyyy/MM/dd HH:mm:ss') } else { '' }
        SENT_TIME             = if ($null -ne $timing.SENT_TIME) { $timing.SENT_TIME.ToString('yyyy/MM/dd HH:mm:ss') } else { '' }
        CREATION_TIME         = if ($null -ne $timing.CREATION_TIME) { $timing.CREATION_TIME.ToString('yyyy/MM/dd HH:mm:ss') } else { '' }
        LAST_MODIFICATION_TIME = if ($null -ne $timing.MODIFIED_TIME) { $timing.MODIFIED_TIME.ToString('yyyy/MM/dd HH:mm:ss') } else { '' }
        SOURCE_READ_ONLY      = $true
    })

    $script:MatchedItemCounter++
    return $true
}

# def 建立 Outlook Restrict 日期字串
function def_GetRestrictDateText {
    [CmdletBinding()]
    param([datetime]$Value)

    # Outlook Jet syntax 依目前 Windows 地區格式解析日期。
    return $Value.ToString('g', [Globalization.CultureInfo]::CurrentCulture)
}

# def 使用 Restrict 掃描單一資料夾
function def_ScanFolderByRestrict {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Folder,
        [string]$StoreName,
        [string]$StoreId,
        [string]$FolderPath,
        [string]$FolderName
    )

    $items = $null
    $processedInFolder = 0
    $restrictSucceeded = $false

    try {
        $items = $Folder.Items
        $itemCount = [int]$items.Count
        if ($itemCount -le 0) {
            return [pscustomobject]@{ SUCCESS = $true; METHOD = 'EMPTY'; ITEM_COUNT = 0; MATCHED = 0 }
        }

        $startText = def_GetRestrictDateText -Value $StartTime
        $endText = def_GetRestrictDateText -Value $EndTime
        $filters = @(
            "[ReceivedTime] >= '$startText' AND [ReceivedTime] <= '$endText'",
            "[SentOn] >= '$startText' AND [SentOn] <= '$endText'",
            "[CreationTime] >= '$startText' AND [CreationTime] <= '$endText'"
        )

        foreach ($filter in $filters) {
            $filteredItems = $null
            try {
                $filteredItems = $items.Restrict($filter)
                $restrictSucceeded = $true
                $filteredCount = [int]$filteredItems.Count
                $limit = if ($MaxItemsPerFolder -gt 0) { [Math]::Min($filteredCount, $MaxItemsPerFolder) } else { $filteredCount }

                for ($index = 1; $index -le $limit; $index++) {
                    $item = $null
                    try {
                        $item = $filteredItems.Item($index)
                        if (def_ProcessItem -Item $item -StoreName $StoreName -StoreId $StoreId -FolderPath $FolderPath -FolderName $FolderName) {
                            $processedInFolder++
                        }
                    }
                    catch {
                        def_AddError -Stage 'PROCESS_RESTRICTED_ITEM' -StoreName $StoreName -FolderPath $FolderPath -Message $_.Exception.Message
                    }
                    finally {
                        def_ReleaseComObject -ComObject $item
                    }
                }
            }
            catch {
                def_AddError -Stage 'RESTRICT_FILTER' -StoreName $StoreName -FolderPath $FolderPath -Message ("Filter: {0}; Error: {1}" -f $filter, $_.Exception.Message)
            }
            finally {
                def_ReleaseComObject -ComObject $filteredItems
            }
        }

        if (-not $restrictSucceeded) {
            return [pscustomobject]@{ SUCCESS = $false; METHOD = 'RESTRICT_FAILED'; ITEM_COUNT = $itemCount; MATCHED = $processedInFolder }
        }

        return [pscustomobject]@{ SUCCESS = $true; METHOD = 'RESTRICT'; ITEM_COUNT = $itemCount; MATCHED = $processedInFolder }
    }
    finally {
        def_ReleaseComObject -ComObject $items
    }
}

# def 完整逐項後備掃描單一資料夾
function def_ScanFolderByIteration {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Folder,
        [string]$StoreName,
        [string]$StoreId,
        [string]$FolderPath,
        [string]$FolderName
    )

    $items = $null
    $processedInFolder = 0
    try {
        $items = $Folder.Items
        $itemCount = [int]$items.Count
        $limit = if ($MaxItemsPerFolder -gt 0) { [Math]::Min($itemCount, $MaxItemsPerFolder) } else { $itemCount }

        for ($index = 1; $index -le $limit; $index++) {
            $item = $null
            try {
                $item = $items.Item($index)
                if (def_ProcessItem -Item $item -StoreName $StoreName -StoreId $StoreId -FolderPath $FolderPath -FolderName $FolderName) {
                    $processedInFolder++
                }
            }
            catch {
                def_AddError -Stage 'PROCESS_ITERATED_ITEM' -StoreName $StoreName -FolderPath $FolderPath -Message $_.Exception.Message
            }
            finally {
                def_ReleaseComObject -ComObject $item
            }
        }

        return [pscustomobject]@{ SUCCESS = $true; METHOD = 'FULL_ITERATION'; ITEM_COUNT = $itemCount; MATCHED = $processedInFolder }
    }
    finally {
        def_ReleaseComObject -ComObject $items
    }
}

# def 判定是否為搜尋資料夾
function def_IsSearchFolderPath {
    [CmdletBinding()]
    param([string]$FolderPath)

    foreach ($pattern in $SEARCH_FOLDER_PATTERNS) {
        if ($FolderPath -like "*$pattern*") { return $true }
    }
    return $false
}

# def 掃描單一資料夾並遞迴子資料夾
function def_ScanFolderRecursive {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Folder,
        [string]$StoreName,
        [string]$StoreId,
        [int]$Depth = 0
    )

    $folderPath = ''
    $folderName = ''
    try { $folderPath = def_ToSafeString -Value $Folder.FolderPath } catch {}
    try { $folderName = def_ToSafeString -Value $Folder.Name } catch {}

    if (-not $IncludeSearchFolders -and (def_IsSearchFolderPath -FolderPath $folderPath)) {
        $script:FolderRows.Add([pscustomobject][ordered]@{
            STORE_NAME  = $StoreName
            FOLDER_PATH = $folderPath
            DEPTH       = $Depth
            METHOD      = 'SKIPPED_SEARCH_FOLDER'
            ITEM_COUNT  = 0
            MATCHED     = 0
            STATUS      = 'SKIPPED'
        })
        return
    }

    $script:FolderCounter++
    Write-Progress -Activity 'VIA Outlook 指定時間唯讀掃描' -Status ("Store: {0} | Folder: {1}" -f $StoreName, $folderPath)

    $result = $null
    try {
        if ($UseRestrict) {
            $result = def_ScanFolderByRestrict -Folder $Folder -StoreName $StoreName -StoreId $StoreId -FolderPath $folderPath -FolderName $folderName
            if ($result.SUCCESS) {
                if ($result.METHOD -eq 'RESTRICT') { $script:RestrictedFolderCounter++ }
            }
            else {
                $script:FallbackFolderCounter++
                $result = def_ScanFolderByIteration -Folder $Folder -StoreName $StoreName -StoreId $StoreId -FolderPath $folderPath -FolderName $folderName
            }
        }
        else {
            $script:FallbackFolderCounter++
            $result = def_ScanFolderByIteration -Folder $Folder -StoreName $StoreName -StoreId $StoreId -FolderPath $folderPath -FolderName $folderName
        }

        $script:FolderRows.Add([pscustomobject][ordered]@{
            STORE_NAME  = $StoreName
            FOLDER_PATH = $folderPath
            DEPTH       = $Depth
            METHOD      = $result.METHOD
            ITEM_COUNT  = $result.ITEM_COUNT
            MATCHED     = $result.MATCHED
            STATUS      = 'OK'
        })
    }
    catch {
        def_AddError -Stage 'SCAN_FOLDER' -StoreName $StoreName -FolderPath $folderPath -Message $_.Exception.Message
        $script:FolderRows.Add([pscustomobject][ordered]@{
            STORE_NAME  = $StoreName
            FOLDER_PATH = $folderPath
            DEPTH       = $Depth
            METHOD      = 'ERROR'
            ITEM_COUNT  = 0
            MATCHED     = 0
            STATUS      = 'ERROR'
        })
    }

    if (-not $IncludeSubfolders) { return }

    $subfolders = $null
    try {
        $subfolders = $Folder.Folders
        $subfolderCount = [int]$subfolders.Count
        for ($index = 1; $index -le $subfolderCount; $index++) {
            $subfolder = $null
            try {
                $subfolder = $subfolders.Item($index)
                def_ScanFolderRecursive -Folder $subfolder -StoreName $StoreName -StoreId $StoreId -Depth ($Depth + 1)
            }
            catch {
                def_AddError -Stage 'ENUMERATE_SUBFOLDER' -StoreName $StoreName -FolderPath $folderPath -Message $_.Exception.Message
            }
            finally {
                def_ReleaseComObject -ComObject $subfolder
            }
        }
    }
    catch {
        def_AddError -Stage 'READ_SUBFOLDERS' -StoreName $StoreName -FolderPath $folderPath -Message $_.Exception.Message
    }
    finally {
        def_ReleaseComObject -ComObject $subfolders
    }
}

# def 判定是否略過 Public Folder Store
function def_IsPublicStore {
    [CmdletBinding()]
    param([string]$StoreName)

    foreach ($pattern in $PUBLIC_STORE_PATTERNS) {
        if ($StoreName -like "*$pattern*") { return $true }
    }
    return $false
}

# def 連線 Classic Outlook
function def_ConnectClassicOutlook {
    [CmdletBinding()]
    param()

    $outlook = $null
    $hadOutlookProcess = @((Get-Process -Name OUTLOOK -ErrorAction SilentlyContinue)).Count -gt 0
    $createdNewInstance = -not $hadOutlookProcess

    try {
        # Outlook.Application 通常會連到既有 Classic Outlook 實例；若未開啟則由 COM 啟動。
        $outlook = New-Object -ComObject Outlook.Application
    }
    catch {
        throw '無法連線 Classic Outlook。New Outlook 不支援 Outlook COM；請先開啟 Classic Outlook 並登入目前使用者可存取的信箱。'
    }

    $namespace = $null
    try {
        $namespace = $outlook.GetNamespace('MAPI')
        return [pscustomobject]@{
            OUTLOOK             = $outlook
            NAMESPACE           = $namespace
            CREATED_NEW_INSTANCE = $createdNewInstance
        }
    }
    catch {
        def_ReleaseComObject -ComObject $namespace
        def_ReleaseComObject -ComObject $outlook
        throw
    }
}

# def UTF-8 CSV 輸出
function def_ExportCsvUtf8 {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$InputObject,
        [Parameter(Mandatory)][string]$Path
    )

    if ($PSVersionTable.PSVersion.Major -ge 6) {
        $InputObject | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding utf8BOM
    }
    else {
        $InputObject | Export-Csv -LiteralPath $Path -NoTypeInformation -Encoding UTF8
    }
}

# def 建立 HTML 報告
function def_WriteHtmlReport {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)]$Summary,
        [Parameter(Mandatory)]$MailRows,
        [Parameter(Mandatory)]$FolderRows
    )

    $topFolders = @($FolderRows | Where-Object { $_.MATCHED -gt 0 } | Sort-Object MATCHED -Descending | Select-Object -First 20)
    $recentMail = @($MailRows | Sort-Object TIME -Descending | Select-Object -First 300)

    $summaryHtml = @"
<table>
<tr><th>項目</th><th>結果</th></tr>
<tr><td>Policy</td><td>$([Net.WebUtility]::HtmlEncode($Summary.POLICY))</td></tr>
<tr><td>指定時間</td><td>$([Net.WebUtility]::HtmlEncode($Summary.START_TIME)) ～ $([Net.WebUtility]::HtmlEncode($Summary.END_TIME))</td></tr>
<tr><td>Store 數</td><td>$($Summary.STORE_COUNT)</td></tr>
<tr><td>資料夾數</td><td>$($Summary.FOLDER_COUNT)</td></tr>
<tr><td>符合郵件數</td><td>$($Summary.MATCHED_MAIL_COUNT)</td></tr>
<tr><td>錯誤數</td><td>$($Summary.ERROR_COUNT)</td></tr>
<tr><td>內文摘要</td><td>$($Summary.INCLUDE_BODY_SNIPPET)</td></tr>
</table>
"@

    $topFolderHtml = if ($topFolders.Count -gt 0) {
        $topFolders | Select-Object STORE_NAME, FOLDER_PATH, METHOD, ITEM_COUNT, MATCHED, STATUS | ConvertTo-Html -Fragment
    }
    else { '<p>指定時間內沒有符合的資料夾。</p>' }

    $mailHtml = if ($recentMail.Count -gt 0) {
        $recentMail | Select-Object TIME, DIRECTION, TITLE, FROM, TO, CC, READ_STATUS, ATTACHMENT_COUNT, STORE_NAME, FOLDER_PATH | ConvertTo-Html -Fragment
    }
    else { '<p>指定時間內未找到郵件。</p>' }

    $html = @"
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA Outlook Time Range Read-Only Report</title>
<style>
body{font-family:Segoe UI,Microsoft JhengHei,sans-serif;margin:28px;color:#202124;background:#f7f8fa}
main{max-width:1500px;margin:auto;background:white;padding:28px;border:1px solid #dfe1e5;border-radius:12px}
h1{margin:0 0 4px;font-size:26px} h2{margin-top:30px;font-size:19px}
.brand{color:#5f6368;margin-bottom:22px}.policy{padding:12px;background:#f1f3f4;border-left:4px solid #5f6368}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:10px}th,td{border:1px solid #dadce0;padding:7px;text-align:left;vertical-align:top}th{background:#f1f3f4;position:sticky;top:0}
.small{font-size:12px;color:#5f6368}
</style>
</head>
<body><main>
<h1>VIA Outlook 指定時間全資料夾唯讀郵件報告</h1>
<div class="brand">VERITAS INTELLIGENCE ANALYTICS · VIA WorkOps Intelligence Workbench</div>
<div class="policy">本工具只讀取目前使用者 Outlook Profile 可見資料；不修改郵件、不下載附件、不安裝模組、不提權。</div>
<h2>執行摘要</h2>
$summaryHtml
<h2>符合郵件最多的資料夾</h2>
$topFolderHtml
<h2>最近 300 封符合郵件</h2>
$mailHtml
<p class="small">完整資料請使用同一 RunDir 內的 CSV。HTML 僅顯示前 300 封郵件。</p>
</main></body></html>
"@

    [IO.File]::WriteAllText($Path, $html, [Text.UTF8Encoding]::new($true))
}

# def 主流程
function def_Main {
    [CmdletBinding()]
    param()

    if ($StartTime -gt $EndTime) {
        throw 'StartTime 不可晚於 EndTime。'
    }

    $runId = 'RUN_{0}_VIA_OUTLOOK_TIMERANGE_READONLY_{1}' -f (Get-Date -Format 'yyyyMMdd_HHmmss'), $SCRIPT_VERSION
    $runDir = Join-Path $OutputRoot $runId
    [void][IO.Directory]::CreateDirectory($runDir)

    $mailCsv = Join-Path $runDir '01_mail_index.csv'
    $folderCsv = Join-Path $runDir '02_folder_scan_audit.csv'
    $errorCsv = Join-Path $runDir '03_scan_errors.csv'
    $manifestJson = Join-Path $runDir '04_run_manifest.json'
    $reportHtml = Join-Path $runDir 'VIA_Outlook_TimeRange_ReadOnly_Report.html'

    Write-Host ''
    Write-Host ('=' * 100) -ForegroundColor DarkGray
    Write-Host 'def VERITAS INTELLIGENCE ANALYTICS' -ForegroundColor Cyan
    Write-Host 'def VIA WorkOps · Outlook 指定時間全資料夾唯讀掃描' -ForegroundColor Cyan
    Write-Host ('=' * 100) -ForegroundColor DarkGray
    Write-Host "def StartTime : $($StartTime.ToString('yyyy/MM/dd HH:mm:ss'))"
    Write-Host "def EndTime   : $($EndTime.ToString('yyyy/MM/dd HH:mm:ss'))"
    Write-Host "def Policy    : $POLICY" -ForegroundColor Yellow
    Write-Host "def RunDir    : $runDir"

    $connection = $null
    $outlook = $null
    $namespace = $null
    $stores = $null
    $storeCount = 0

    try {
        $connection = def_ConnectClassicOutlook
        $outlook = $connection.OUTLOOK
        $namespace = $connection.NAMESPACE
        $stores = $namespace.Stores
        $storeCount = [int]$stores.Count

        for ($storeIndex = 1; $storeIndex -le $storeCount; $storeIndex++) {
            $store = $null
            $rootFolder = $null
            try {
                $store = $stores.Item($storeIndex)
                $storeName = def_ToSafeString -Value $store.DisplayName
                $storeId = def_ToSafeString -Value $store.StoreID

                if (-not $IncludePublicFolders -and (def_IsPublicStore -StoreName $storeName)) {
                    $script:FolderRows.Add([pscustomobject][ordered]@{
                        STORE_NAME  = $storeName
                        FOLDER_PATH = ''
                        DEPTH       = 0
                        METHOD      = 'SKIPPED_PUBLIC_STORE'
                        ITEM_COUNT  = 0
                        MATCHED     = 0
                        STATUS      = 'SKIPPED'
                    })
                    continue
                }

                $rootFolder = $store.GetRootFolder()
                def_ScanFolderRecursive -Folder $rootFolder -StoreName $storeName -StoreId $storeId -Depth 0
            }
            catch {
                $storeNameForError = ''
                try { $storeNameForError = def_ToSafeString -Value $store.DisplayName } catch {}
                def_AddError -Stage 'SCAN_STORE' -StoreName $storeNameForError -FolderPath '' -Message $_.Exception.Message
            }
            finally {
                def_ReleaseComObject -ComObject $rootFolder
                def_ReleaseComObject -ComObject $store
            }
        }
    }
    finally {
        Write-Progress -Activity 'VIA Outlook 指定時間唯讀掃描' -Completed
        def_ReleaseComObject -ComObject $stores
        def_ReleaseComObject -ComObject $namespace
        def_ReleaseComObject -ComObject $outlook
        [GC]::Collect()
        [GC]::WaitForPendingFinalizers()
    }

    $sortedMailRows = @($script:MailRows | Sort-Object @{ Expression = { [datetime]::ParseExact($_.TIME, 'yyyy/MM/dd HH:mm:ss', $null) }; Descending = $false }, STORE_NAME, FOLDER_PATH)
    $sortedFolderRows = @($script:FolderRows | Sort-Object STORE_NAME, FOLDER_PATH)
    $sortedErrorRows = @($script:ErrorRows | Sort-Object TIME, STORE_NAME, FOLDER_PATH)

    if ($sortedMailRows.Count -gt 0) {
        def_ExportCsvUtf8 -InputObject $sortedMailRows -Path $mailCsv
    }
    else {
        [IO.File]::WriteAllText($mailCsv, 'TIME,DIRECTION,ITEM_TYPE,TITLE,FROM,FROM_ADDRESS,TO,CC,READ_STATUS,IMPORTANCE,FLAG_STATUS,CATEGORIES,ATTACHMENT_COUNT,ATTACHMENT_NAMES,BODY_SNIPPET,STORE_NAME,FOLDER_NAME,FOLDER_PATH,MESSAGE_CLASS,CONVERSATION_TOPIC,CONVERSATION_ID,INTERNET_MESSAGE_ID,MAIL_FINGERPRINT,ENTRY_ID,STORE_ID,SIZE_BYTES,RECEIVED_TIME,SENT_TIME,CREATION_TIME,LAST_MODIFICATION_TIME,SOURCE_READ_ONLY' + [Environment]::NewLine, [Text.UTF8Encoding]::new($true))
    }

    if ($sortedFolderRows.Count -gt 0) { def_ExportCsvUtf8 -InputObject $sortedFolderRows -Path $folderCsv }
    if ($sortedErrorRows.Count -gt 0) {
        def_ExportCsvUtf8 -InputObject $sortedErrorRows -Path $errorCsv
    }
    else {
        [IO.File]::WriteAllText($errorCsv, 'TIME,STAGE,STORE_NAME,FOLDER_PATH,ERROR' + [Environment]::NewLine, [Text.UTF8Encoding]::new($true))
    }

    $summary = [pscustomobject][ordered]@{
        SYSTEM_NAME              = 'VERITAS INTELLIGENCE ANALYTICS'
        PRODUCT_NAME             = 'VIA WorkOps Intelligence Workbench'
        SCRIPT_VERSION           = $SCRIPT_VERSION
        POLICY                   = $POLICY
        RUN_ID                   = $runId
        RUN_DIR                  = $runDir
        START_TIME               = $StartTime.ToString('yyyy/MM/dd HH:mm:ss')
        END_TIME                 = $EndTime.ToString('yyyy/MM/dd HH:mm:ss')
        STORE_COUNT              = $storeCount
        FOLDER_COUNT             = $script:FolderCounter
        RESTRICTED_FOLDER_COUNT  = $script:RestrictedFolderCounter
        FALLBACK_FOLDER_COUNT    = $script:FallbackFolderCounter
        SCANNED_ITEM_REFERENCE_COUNT = $script:ScannedItemCounter
        MATCHED_MAIL_COUNT       = $sortedMailRows.Count
        ERROR_COUNT              = $sortedErrorRows.Count
        INCLUDE_SUBFOLDERS       = $IncludeSubfolders
        INCLUDE_SEARCH_FOLDERS   = $IncludeSearchFolders
        INCLUDE_PUBLIC_FOLDERS   = $IncludePublicFolders
        INCLUDE_MEETING_ITEMS    = $IncludeMeetingItems
        INCLUDE_BODY_SNIPPET     = $IncludeBodySnippet
        INCLUDE_ATTACHMENT_NAMES = $IncludeAttachmentNames
        USE_RESTRICT             = $UseRestrict
        MAX_ITEMS_PER_FOLDER     = $MaxItemsPerFolder
        OUTLOOK_INSTANCE_STARTED_BY_SCRIPT = if ($null -ne $connection) { $connection.CREATED_NEW_INSTANCE } else { $false }
        MAIL_CSV                 = $mailCsv
        FOLDER_AUDIT_CSV         = $folderCsv
        ERROR_CSV                = $errorCsv
        HTML_REPORT              = $reportHtml
        COMPLETED_AT             = (Get-Date).ToString('yyyy/MM/dd HH:mm:ss')
    }

    [IO.File]::WriteAllText($manifestJson, ($summary | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($true))
    def_WriteHtmlReport -Path $reportHtml -Summary $summary -MailRows $sortedMailRows -FolderRows $sortedFolderRows

    Write-Host ''
    Write-Host 'def SCAN COMPLETE' -ForegroundColor Green
    Write-Host "def Stores    : $storeCount"
    Write-Host "def Folders   : $($script:FolderCounter)"
    Write-Host "def Mail Rows : $($sortedMailRows.Count)"
    Write-Host "def Errors    : $($sortedErrorRows.Count)"
    Write-Host "def Mail CSV  : $mailCsv"
    Write-Host "def Report    : $reportHtml"
    Write-Host ''

    if ($OpenReport -and (Test-Path -LiteralPath $reportHtml)) {
        Start-Process -FilePath $reportHtml
    }
}

try {
    def_Main
}
catch {
    Write-Host ''
    Write-Host 'def FATAL SAFE CATCH' -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host 'def No Outlook item was modified.' -ForegroundColor Yellow
    throw
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
