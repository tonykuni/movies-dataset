# CELERITAS-TEMPLATE-JOIN v1 (library: dot-sourced by its caller, the caller's template covers it; R17)
# ===== [VIA:PS-TEMPLATE:v0101-lib] no code here on purpose: running Start here would change the caller's session =====
# Register-VIA-Commands-v0261.ps1 — R17(操作員 2026-09-28):兩個新 VDF 引擎的短令,經 VCGC、每步包 Invoke-VIACeleritasScoped。
#   via-cnnfg  [status|run [--start YYYY-MM-DD] [--csv 檔] [--dry]|--selftest]   CNN 恐懼與貪婪全歷史回補(VDF_ENG229;別名 恐懼貪婪)
#   via-fwdval [status|run [--days N] [--dry]|--selftest]                       指數 Forward PER / EPS 唯一正主(VDF_ENG230;別名 預估本益比)
#   via-lists  [status|lists|run [--only us,jp] [--dry]|--selftest]          美·日·台 個股總清單 + 每日主動式台股 ETF 總清單(VDF_ENG231;別名 總清單)
#   run 要觸網:先在**你的**視窗開 $env:VIA_NET_CONSENT='YES' 與 $env:VIA_SCRAPE_CONSENT='YES'(AI 永不代設;閘沒開 = DENY、零外呼、零寫入)。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0260.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path

function global:Invoke-VIAVdfEngineVerb {
    param([string]$Pattern, [string]$Tag, [object[]]$Rest)
    $env:VIA_FROM_VCGC = "YES"
    $eng = Get-VIANewest "$VIA\functional modules\VDF\engine" $Pattern
    if (-not $eng) { Write-Host ("  [" + $Tag + "] ABSENT:functional modules\VDF\engine\" + $Pattern + " 不在這棵樹(先 git pull)") -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $a = @(ConvertTo-VIACleanArgs $Rest)
    if ($a.Count -eq 0) { $a = @("status") }
    $py = Get-VIAEnvPython "vdf"
    if (Get-Command Invoke-VIACeleritasScoped -ErrorAction SilentlyContinue) {
        Invoke-VIACeleritasScoped { Invoke-VIAPython -Python $py $eng @a }
    } else {
        Invoke-VIAPython -Python $py $eng @a
    }
}
function global:via-cnnfg { Invoke-VIAVdfEngineVerb "VDF_ENG229_CNNFearGreedHistory_v*.py" "via-cnnfg" $args }
function global:via-fwdval { Invoke-VIAVdfEngineVerb "VDF_ENG230_ForwardValuation_v*.py" "via-fwdval" $args }
function global:via-lists { Invoke-VIAVdfEngineVerb "VDF_ENG231_GlobalListings_v*.py" "via-lists" $args }
Set-Alias -Name 恐懼貪婪 -Value via-cnnfg -Scope Global -Force
Set-Alias -Name 預估本益比 -Value via-fwdval -Scope Global -Force
Set-Alias -Name 總清單 -Value via-lists -Scope Global -Force
