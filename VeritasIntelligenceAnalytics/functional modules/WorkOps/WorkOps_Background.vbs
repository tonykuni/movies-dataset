' VIA WorkOps 背景啟動器:雙擊即以隱藏視窗跑 via-workops silent(掃描+報表+桌面通知,不開瀏覽器)
' 設為每日開機自動:Win+R → shell:startup → 放本檔捷徑
Dim sh, fso, here, cmd
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
here = fso.GetParentFolderName(WScript.ScriptFullName)
cmd = "cmd.exe /c """ & fso.BuildPath(fso.GetParentFolderName(fso.GetParentFolderName(here)), "bin\via-workops.cmd") & """ silent"
sh.Run cmd, 0, False
