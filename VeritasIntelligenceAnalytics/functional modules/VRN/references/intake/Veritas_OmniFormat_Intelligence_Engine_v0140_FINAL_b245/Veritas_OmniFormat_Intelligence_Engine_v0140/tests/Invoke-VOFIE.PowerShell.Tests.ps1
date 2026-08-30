BeforeAll {
    $Root = Split-Path -Parent $PSScriptRoot
    Import-Module (Join-Path $Root "adapters\Veritas.VOFIE.ToolBridge.psm1") -Force
}

Describe "VOFIE PowerShell CPU Tool Bridge" {
    It "parses the launcher without mutating it" {
        $result = Test-VOFIEPowerShellFile -LiteralPath (Join-Path $Root "Invoke-Veritas-VOFIE.ps1")
        $result.gate | Should -Be "PASS"
        $result.source_mutated | Should -BeFalse
    }

    It "reports exactly twenty PowerShell tools" {
        $result = Get-VOFIEPowerShellToolInventory
        $result.gate | Should -Be "PASS"
        $result.total | Should -Be 20
    }

    It "passes the bridge self-test" {
        $result = Invoke-VOFIEPowerShellBridgeSelfTest
        $result.gate | Should -Be "PASS"
    }
}
