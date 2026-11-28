[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = '1'
& python "$PSScriptRoot\VIA_PanoramaFusion_SuperEngine_v0308.py" @args
