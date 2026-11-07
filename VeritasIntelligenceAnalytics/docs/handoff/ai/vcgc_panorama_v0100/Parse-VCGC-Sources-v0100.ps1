#Requires -Version 7.0
[CmdletBinding()]
param([Parameter(Mandatory)][string]$Manifest,[Parameter(Mandatory)][string]$OutputFile)
$ErrorActionPreference='Stop'
# Static parser only: no dot-source and no execution of the inspected scripts.
$files = @(Get-Content -LiteralPath $Manifest -Raw -Encoding utf8 | ConvertFrom-Json)
$writer = [System.IO.StreamWriter]::new($OutputFile,$false,[System.Text.UTF8Encoding]::new($false))
try {
    foreach ($file in $files) {
        try {
            $tokens=$null; $parseErrors=$null
            $tree=[System.Management.Automation.Language.Parser]::ParseFile([string]$file,[ref]$tokens,[ref]$parseErrors)
            $functions=@($tree.FindAll({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst]},$true) | ForEach-Object { @{name=$_.Name;line=$_.Extent.StartLineNumber} })
            $calls=@($tree.FindAll({param($node) $node -is [System.Management.Automation.Language.CommandAst]},$true) | ForEach-Object {$_.GetCommandName()} | Where-Object {$_} | Sort-Object -Unique)
            $row=@{path=[string]$file; parser='PowerShell AST'; errors=@($parseErrors | ForEach-Object {@{message=$_.Message;line=$_.Extent.StartLineNumber;id=$_.ErrorId}}); functions=$functions; commands=$calls}
        } catch { $row=@{path=[string]$file;parser='PowerShell AST';errors=@(@{message="$_";line=0;id='READ_OR_PARSE_ERROR'});functions=@();commands=@()} }
        $writer.WriteLine(($row | ConvertTo-Json -Depth 12 -Compress))
        $writer.Flush()
    }
} finally { $writer.Dispose() }
