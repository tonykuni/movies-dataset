
    try {
        $selfText = $MyInvocation.MyCommand.Definition

        if ([string]::IsNullOrWhiteSpace($selfText) -or $selfText.Length -lt 100) {
            return
        }

        def_WriteUtf8Additive -Path $def_PARAM_MANAGER_PATH -Content $selfText
    }
    catch {
        # non-blocking
    }

