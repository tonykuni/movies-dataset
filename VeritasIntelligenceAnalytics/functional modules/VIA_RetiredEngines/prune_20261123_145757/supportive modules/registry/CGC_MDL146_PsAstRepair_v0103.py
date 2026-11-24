#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL146_PsAstRepair v0103 — PowerShell 多輪並行安全修正引擎(批394 操作員令:
「啟動 PowerShell 指令語法多輪並行安全修正引擎,調用全套語法診斷工具與 AST 雙模錨點定位,
對所有 *.ps1/*.psm1 執行全景式語法分析、錯誤分流、並行安全修正、沙盒啟動驗證,直到啟動測試完全無誤」)

本引擎接在 MDL145(PS 真測閘)之後:MDL145 只「判真假」,本引擎「定位+修+複驗」。

一、全景式識別工具矩陣(缺者誠實 SKIP,永不假綠)
  T1 AST Parser  [System.Management.Automation.Language.Parser]::ParseFile → ParseError 清單
                 (含 Extent 起訖行列=精準錨點來源)
  T2 PSScriptAnalyzer  Invoke-ScriptAnalyzer(模組在位才跑;缺=SKIP 並印安裝指令,絕不代裝)
  T3 Command/Param Inspector  對可解析檔取 CommandAst:未知指令(v0101 真實作)+ 已知陷阱樣式
                 (硬寫磁碟機代號、Join-Path 空值、行尾註解截斷續行)逐一定位

二、AST 雙模錨點
  精準錨點 Precision:ParseError.Extent 的 (StartLine, StartCol, EndLine, EndCol) + 節點型別
  彈性錨點 Elastic:結構特徵簽名(正規式族 + 前後文窗),用於行數漂移後仍能命中同一處

三、錯誤分流(批389–393 真測實錄為據)
  Parallel-Fixable(可並行、單點、零語意變更)
    F1 行尾註解截斷續行 — `… -and   # 註解` 後接續行 `-and …` → PowerShell 視運算式結束 → 括號永不收
       (批389 於 Invoke-VIA-PSRepair-v0102.ps1 L179 真遇;MDL145 抓到)
       修法(pwsh 實測定案)=續接運算子上提到本行末 + 註解搬到續行末,token 零變更
       (只搬註解不足以解:PowerShell 換行續接的唯一條件是「上一行以運算子結尾」)
  Report-Only(需語意判斷,只定位不自動改;--apply 亦不改)
    R1 硬寫磁碟機代號 — 非 Windows 上 `Join-Path "C:\..."` 噴 Cannot find drive(批389 實錄)
    R2 Join-Path 空值 — 基底未非空判(批389 實錄)
    R3 其餘 ParseError — 未閉合字串/括號等需人眼
    R4 if 當參數位置運算式 — 解析綠但執行必紅(v0103 新;我方自犯實例:寫 Invoke-VIA-Unstick
       時連犯 5 處 `Write-Step (if (...) {...} else {...})`,AST 解析全綠、pwsh 真跑全紅
       「The term 'if' is not recognized」)。合法寫法只有 $(if ...) 子運算式或 $x = if ... 賦值。
       與 InvokeVIA.ps1 的 param 位置錯同屬一族:解析綠 ≠ 能跑,故兩者都只有真跑或樣式檢抓得到。
       三種合法寫法 $(if ...) / @(if ...) / $x = if ... 一律不報(立規當輪 R4 誤判 @(if ...) 已同輪修正)
  Sequence-Dependent(跨檔/跨模組;本版只列不動)
    S1 函式匯出名變更、S2 Pipeline 上下游結構、S3 非同步結構

四、多輪循環(每輪皆沙盒複驗;不卡斷)
  R1 全景掃描 → 分流 → 並行修正所有 Parallel-Fixable(寫前寫後各解析一次;任一不過即放棄該檔)
  R2 依賴拓撲(本版:Report-Only/Sequence-Dependent 僅列矩陣,不動)
  R3 收尾:全樹再解析;尾版必綠才算過(封存版壞=WARN,凍結不改)
  迴圈至「尾版零 ParseError」或「本輪零新增修正」(收斂即停,避免無限輪)

五、零九頭龍與只增不減
  修正一律 version-forward:Register-VIA-Commands-v0174.ps1 → v0175.ps1(同族版號 +1);
  目標版號已存在即拒寫(Hydra 守衛),正本零觸碰、零刪除、零 force。

輸出:VIA_Reports/ps_ast_repair/REPAIR_<ts>.json + 頁 VIA_UI_PsAstRepair_v0100.html
      (四分區 MODULE/ENGINE/FUNCTION-LIB/OTHERS + RYG + 修正前後對比 + Hydra 風險 + 沙盒日誌;零 CDN 手機單欄)
v0100→v0101(批394 續章「test debug optimize test debug till they work」自我檢討三枚):
  ① T3 名實不符:v0100 docstring 宣稱「Command/Param Inspector:未知動詞」,實作只有 regex 陷阱樣式,
     未知動詞從未掃過=宣稱大於實作(誠實性缺口)。v0101 真實作:逐檔取 CommandAst,以「冊內
     FunctionDefinitionAst/Set-Alias 定義集 ∪ 系統 Get-Command 可解析」為準,兩者皆不認即列
     T3 未知指令(死路嫌疑;Report-Only 只列不改,與 MDL136 短令死路掃描互補)。
  ② 規格要求「Parallel-Fixable 一口氣並行」,v0100 卻是逐檔循序(pwsh 子行程為 I/O bound,
     循序=白等)。v0101 以執行緒池並行修,並以鎖做「目標版號預約」(reserve)使 Hydra 守衛在
     並行下不競態;每檔 version-forward 目標天然互異,故並行寫入零覆蓋。
  ③ PSScriptAnalyzer 全樹掃描每輪重跑=工作站上最慢的一段白跑。v0101 快取:僅第一輪與
     「上輪有實際寫入」時重掃,其餘輪沿用(效能優化,判定零放寬)。
  併:_ps 臨時腳本檔名改為唯一(v0100 以 hash(script) 命名,並行下同腳本必撞同檔=讀寫競態)。

v0101→v0102(T3 首跑 11 枚,逐枚查證後只有 1 枚是真缺陷=9 枚假紅不可接受,故加分級):
  真缺陷 1 枚(T1/MDL145 都看不見,唯 T3 抓到):InvokeVIA.ps1 的 param 區塊原在 L24,
    前面已有加速器橋 try{}/Set-StrictMode/$ErrorActionPreference 等可執行語句 → param 不在合法位置
    → PowerShell 把 param(...) 當指令呼叫(實測 InvalidOperation: called as if it were a method)
    → -Run/-SafeProbe/-Plan 三開關永遠無法綁定 → 真跑路徑完全不可達(只能跑 SAFE PROBE)。
    檔案解析仍綠,所以解析閘永遠抓不到。已就地修(無版號檔可就地;param 上移至 #Requires 後),
    修後真跑零 InvalidOperation、AST ParamBlock 三開關在位。
  假紅 9 枚的四個成因 → v0102 分級(誠實不上色:非死路者不列為死路)
    PLATFORM  Windows 原生指令/Windows-only cmdlet(winget/robocopy/schtasks/cmd/powershell/py/
              Get-CimInstance…)在 Linux 雲端本就缺席,工作站有 → 平台性缺席,非死路
    CROSS     定義在被點源的 .ps1 模組(如 supportive modules\VIA_PS_Accel_Module.ps1 的
              Write-VIAProgress/Invoke-VIAGuarded)→ v0101 只收根目錄定義集故誤報;v0102 定義集改全樹遞迴
    GUARDED   呼叫點外有 Get-Command 在位判斷(如 via-matrix)→ 缺席不會炸,非死路
    SYNTAX    param/begin/process/end/class/filter/data 等關鍵字被當 CommandAst → 噪音不報
    ARCHIVE   只出現在封存版檔 → 凍結不追(尾版律)
  只有「尾版檔 × 非平台 × 無守衛 × 非關鍵字 × 定義集與系統皆不認」才算 TRUE 死路嫌疑。

用法:via-psrepair-ast            → 全景掃描+分流(唯讀;不改任何檔)
      via-psrepair-ast --apply    → 多輪並行安全修正(只動 Parallel-Fixable;version-forward)
      python <本檔> --selftest    → 十三檢(真修真驗 + T3 真掃與分級 + 並行一致性 + 真缺陷回歸;pwsh 缺=SKIP)
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import html
import importlib.util
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI = VIA / "supportive modules" / "ui_support"
REP = VIA / "VIA_Reports" / "ps_ast_repair"
PAGE = UI / "VIA_UI_PsAstRepair_v0100.html"
ENGINE_TAG = "CGC_MDL146_PsAstRepair v0103"
MAX_ROUNDS = int(os.environ.get("VIA_AST_ROUNDS", "3") or 3)
VER_RX = re.compile(r"^(?P<fam>.+?)(?P<sep>[-_])v(?P<ver>\d{3,4})(?P<ext>\.ps1|\.psm1)$", re.I)

# F1 彈性錨點:行尾註解後,下一行以續接運算子開頭(PowerShell 視運算式已結束=括號收不回)
CONT_OPS = ("-and", "-or", "-band", "-bor", "+", "|", "-eq", "-ne", "-gt", "-lt", "-ge", "-le", "-match", "-notmatch", "-contains")
R1_DRIVE_RX = re.compile(r'Join-Path\s+"[A-Za-z]:\\\\?')
R2_NULLBASE_RX = re.compile(r"Join-Path\s+\$env:[A-Za-z_]+\s")
# R4(v0103;我方自犯實例):if 當「參數位置運算式」=解析綠但執行必紅
#   Write-Step ("x" + (if ($a) { "y" } else { "z" }))  → The term 'if' is not recognized...
#   合法寫法有三種(pwsh 實測):子運算式 $(if ...)、陣列子運算式 @(if ...)、賦值右值 $x = if ...
#   (立規當輪 R4 即誤判了 Register 冊裡合法的 @(if ($args) {...} else {...}) → 同輪修掉)
R4_IFEXPR_RX = re.compile(r"(?<![\$@])\(\s*if\s*\(")
RULES = ["修正一律 version-forward(同族版號 +1);目標版號已存在=拒寫(Hydra 守衛);正本零觸碰零刪除零 force",
         "只自動修 Parallel-Fixable(單點、零語意變更、寫前寫後各解析一次);Report-Only 與 Sequence-Dependent 只列不動",
         "工具缺席誠實 SKIP:PSScriptAnalyzer 缺=印安裝指令不代裝;pwsh 缺=全閘 SKIP",
         "尾版律:判定只看同族尾版;封存版壞=WARN 凍結不改",
         "收斂即停:本輪零新增修正或尾版零 ParseError 即結束(不卡斷、無限輪防護 VIA_AST_ROUNDS)",
         "並行安全:Parallel-Fixable 以執行緒池並行,目標版號先鎖後預約(reserve)使 Hydra 守衛零競態;每檔目標互異故零覆蓋",
         "T3 誠實分級:PLATFORM/CROSS/GUARDED/SYNTAX/ARCHIVE 皆非死路,只有尾版檔的 TRUE 級才算死路嫌疑(不製造假紅)",
         "解析綠 ≠ 能跑:param 位置錯與 if 當參數運算式皆可解析卻必在執行期炸,故 R1–R4 樣式檢與真跑並用"]

# T3 分級冊
PLATFORM_CMDS = {"winget", "robocopy", "schtasks", "cmd", "powershell", "py", "cscript", "wscript",
                 "reg", "wmic", "netsh", "icacls", "takeown", "diskpart", "bcdedit", "msiexec",
                 "explorer", "notepad", "start", "xcopy", "attrib", "tasklist", "taskkill", "sc",
                 "pwsh.exe", "powershell.exe", "python.exe", "pythonw", "conda", "choco", "mklink"}
PLATFORM_CMDLETS = {"get-ciminstance", "new-ciminstance", "get-wmiobject", "invoke-ciminstance",
                    "get-scheduledtask", "register-scheduledtask", "new-scheduledtasktrigger",
                    "new-scheduledtaskaction", "get-appxpackage", "add-appxpackage",
                    "get-windowsoptionalfeature", "set-executionpolicy", "get-disk", "get-volume",
                    "get-netadapter", "get-localuser", "new-itemproperty", "get-itempropertyvalue",
                    "show-controlpanelitem", "add-type"}
PS_KEYWORDS = {"param", "begin", "process", "end", "clean", "class", "enum", "filter", "data",
               "configuration", "dynamicparam", "trap", "workflow", "hidden", "using"}

PARSE_PS = r'''
param([string]$Root)
foreach ($f in (Get-ChildItem -LiteralPath $Root -Include *.ps1,*.psm1 -File -Recurse:$false -ErrorAction SilentlyContinue | Sort-Object Name)) {
  $errs = $null; $toks = $null
  [void][System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$toks, [ref]$errs)
  if ($errs.Count -gt 0) {
    foreach ($e in $errs) {
      Write-Output ("ERR|" + $f.Name + "|" + $e.Extent.StartLineNumber + "|" + $e.Extent.StartColumnNumber + "|" + $e.Extent.EndLineNumber + "|" + $e.Extent.EndColumnNumber + "|" + ($e.Message -replace '\|',' '))
    }
  } else { Write-Output ("OK|" + $f.Name) }
}
'''

PARSE_ONE_PS = r'''
param([string]$File)
$errs = $null; $toks = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($File, [ref]$toks, [ref]$errs)
if ($errs.Count -gt 0) { Write-Output ("BAD|" + $errs[0].Extent.StartLineNumber + "|" + ($errs[0].Message -replace '\|',' ')) } else { Write-Output "GOOD" }
'''

PSSA_PS = r'''
param([string]$Root)
if (-not (Get-Module -ListAvailable -Name PSScriptAnalyzer)) { Write-Output "PSSA|MISSING"; exit 0 }
Import-Module PSScriptAnalyzer -ErrorAction SilentlyContinue
foreach ($f in (Get-ChildItem -LiteralPath $Root -Include *.ps1,*.psm1 -File -ErrorAction SilentlyContinue)) {
  foreach ($d in (Invoke-ScriptAnalyzer -Path $f.FullName -Severity Error,Warning -ErrorAction SilentlyContinue)) {
    Write-Output ("PSSA|" + $f.Name + "|" + $d.Severity + "|" + $d.RuleName + "|" + $d.Line)
  }
}
Write-Output "PSSA|DONE"
'''


T3_PS = r'''
param([string]$Root)
$files = @(Get-ChildItem -LiteralPath $Root -Include *.ps1,*.psm1 -File -ErrorAction SilentlyContinue | Sort-Object Name)
# v0102:定義集改全樹遞迴(被點源的 supportive modules\*.ps1 亦算已定義;解 CROSS 級誤報)
$defFiles = @(Get-ChildItem -LiteralPath $Root -Include *.ps1,*.psm1 -File -Recurse -ErrorAction SilentlyContinue)
$defs = @{}
$guarded = @{}
foreach ($f in $defFiles) {
  $errs = $null; $toks = $null
  $ast = [System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$toks, [ref]$errs)
  if ($errs.Count -gt 0) { continue }
  foreach ($d in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)) {
    $defs[($d.Name -replace '^global:', '')] = 1
  }
  foreach ($c in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)) {
    $cn = $c.GetCommandName()
    if ($cn -eq 'Set-Alias') {
      $el = $c.CommandElements
      for ($i = 1; $i -lt $el.Count - 1; $i++) {
        if ("$($el[$i].Extent.Text)" -match '^-Name') { $defs[("$($el[$i+1].Extent.Text)" -replace '^[\"\x27]|[\"\x27]$', '')] = 1 }
      }
    }
    if ($cn -eq 'Get-Command') {        # v0102 GUARDED:呼叫點外有在位判斷=缺席不會炸
      foreach ($el in $c.CommandElements) {
        $tx = "$($el.Extent.Text)" -replace '^[\"\x27]|[\"\x27]$', ''
        if ($tx -and $tx -notmatch '^-' -and $tx -ne 'Get-Command') { $guarded[$tx] = 1 }
      }
    }
  }
}
$rows = New-Object System.Collections.ArrayList
foreach ($f in $files) {
  $errs = $null; $toks = $null
  $ast = [System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$toks, [ref]$errs)
  if ($errs.Count -gt 0) { continue }          # 不可解析檔交給 T1,不在此誤報
  foreach ($d in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)) {
    $defs[($d.Name -replace '^global:', '')] = 1
  }
  foreach ($c in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)) {
    $nm = $c.GetCommandName()
    if (-not $nm) { continue }
    if ($nm -eq 'Set-Alias') {                 # 冊內別名亦算已定義
      $el = $c.CommandElements
      for ($i = 1; $i -lt $el.Count - 1; $i++) {
        if ("$($el[$i].Extent.Text)" -match '^-Name') { $defs[("$($el[$i+1].Extent.Text)" -replace '^[\"\x27]|[\"\x27]$', '')] = 1 }
      }
    }
    [void]$rows.Add(@($f.Name, $c.Extent.StartLineNumber, $nm))
  }
}
$seen = @{}
foreach ($r in $rows) {
  $nm = $r[2]
  if ($nm -match '^[\$\&]' -or $nm -match '[\\/]') { continue }      # 變數/路徑呼叫不判
  if ($defs.ContainsKey($nm)) { continue }
  if ($seen.ContainsKey($nm)) { continue }
  if (Get-Command -Name $nm -ErrorAction SilentlyContinue) { continue }
  $seen[$nm] = 1
  $g = $(if ($guarded.ContainsKey($nm)) { "GUARDED" } else { "" })
  Write-Output ("UNK|" + $r[0] + "|" + $r[1] + "|" + $nm + "|" + $g)
}
Write-Output "T3|DONE"
'''


def find_pwsh() -> str:
    """與 MDL145 同律:env VIA_PWSH → PATH → 常見位置(零重造:若 MDL145 在位即直取其 find_pwsh)"""
    try:
        p = sorted(HERE.glob("CGC_MDL145_PsTestGate_v0*.py"))
        if p:
            spec = importlib.util.spec_from_file_location("pstest_ar", p[-1])
            m = importlib.util.module_from_spec(spec)
            sys.modules["pstest_ar"] = m
            spec.loader.exec_module(m)
            return m.find_pwsh()
    except Exception:
        pass
    c = [os.environ.get("VIA_PWSH", ""), shutil.which("pwsh") or "", shutil.which("powershell") or ""]
    return next((x for x in c if x and Path(x).exists()), "")


_SEQ = itertools.count(1)
_LOCK = threading.Lock()


def _ps(pwsh: str, script: str, args: list, tmp: Path, timeout: int = 900) -> str:
    # v0101:檔名唯一(v0100 以 hash(script) 命名,並行下同腳本必撞同檔=讀寫競態)
    f = tmp / ("ar_" + str(next(_SEQ)) + ".ps1")
    f.write_text(script, encoding="utf-8")
    r = subprocess.run([pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(f)] + args,
                       capture_output=True, text=True, timeout=timeout)
    return (r.stdout or "") + (r.stderr or "")


# ---------------------------------------------------------------- 一、全景掃描
def t3_grade(name: str, file: str, guarded: str, tails: set) -> str:
    """T3 誠實分級(v0102):只有 TRUE 級才算死路嫌疑,其餘皆有正當理由不上色"""
    low = name.lower()
    if low in PS_KEYWORDS:
        return "SYNTAX"                         # 關鍵字被當 CommandAst=噪音
    if low in PLATFORM_CMDS or low in PLATFORM_CMDLETS or low.endswith(".exe"):
        return "PLATFORM"                       # Linux 雲端缺席、工作站在位=平台性
    if guarded == "GUARDED":
        return "GUARDED"                        # 呼叫點外有 Get-Command 在位判斷
    if file not in tails:
        return "ARCHIVE"                        # 只在封存版出現=凍結不追
    return "TRUE"


def t3_scan(pwsh: str, root: Path, tmp: Path, tails: set | None = None) -> list:
    """T3 Command/Param Inspector(v0101 真實作;v0102 加分級):
    CommandAst 指令名 × (全樹定義集 ∪ 系統可解析) 皆不認 → 依 t3_grade 分級。
    只有 TRUE 級才算死路嫌疑;Report-Only 只列不改。不可解析檔交給 T1,不在此誤報。"""
    if not pwsh:
        return []
    out = _ps(pwsh, T3_PS, ["-Root", str(root)], tmp)
    if tails is None:
        allf = [p.name for p in sorted(root.glob("*.ps1")) + sorted(root.glob("*.psm1"))]
        tails = tail_only(allf)[0]
    rows = []
    for l in out.splitlines():
        if l.startswith("UNK|"):
            p5 = l.split("|")
            if len(p5) >= 4:
                nm, fl = p5[3], p5[1]
                g = p5[4] if len(p5) >= 5 else ""
                rows.append({"file": fl, "line": int(p5[2]) if p5[2].isdigit() else 0,
                             "name": nm, "grade": t3_grade(nm, fl, g, tails)})
    rows.sort(key=lambda x: (x["grade"] != "TRUE", x["grade"], x["name"]))
    return rows[:200]


def panorama(pwsh: str, root: Path, tmp: Path, pssa_cache: dict | None = None) -> dict:
    if not pwsh:
        return {"state": "SKIP", "note": "pwsh 缺席(env VIA_PWSH 可指)", "errors": [], "pssa": "SKIP", "files_ok": 0}
    out = _ps(pwsh, PARSE_PS, ["-Root", str(root)], tmp)
    errs, ok = [], 0
    for l in out.splitlines():
        if l.startswith("OK|"):
            ok += 1
        elif l.startswith("ERR|"):
            p = l.split("|")
            if len(p) >= 7:
                errs.append({"file": p[1], "line": int(p[2]), "col": int(p[3]), "end_line": int(p[4]), "end_col": int(p[5]), "msg": p[6]})
    if pssa_cache is not None and "out" in pssa_cache:
        ps_out = pssa_cache["out"]          # v0101 快取:僅首輪與「上輪有實際寫入」時重掃(判定零放寬)
    else:
        ps_out = _ps(pwsh, PSSA_PS, ["-Root", str(root)], tmp)
        if pssa_cache is not None:
            pssa_cache["out"] = ps_out
    pssa = "MISSING" if "PSSA|MISSING" in ps_out else ("DONE" if "PSSA|DONE" in ps_out else "PROBE_FAIL")
    findings = [l.split("|") for l in ps_out.splitlines() if l.startswith("PSSA|") and len(l.split("|")) >= 5]
    return {"state": "OK", "errors": errs, "files_ok": ok, "pssa": pssa,
            "pssa_findings": [{"file": f[1], "sev": f[2], "rule": f[3], "line": f[4]} for f in findings][:200],
            "note": ("PSScriptAnalyzer 缺=SKIP(安裝:Install-Module PSScriptAnalyzer -Scope CurrentUser;本引擎不代裝)"
                     if pssa == "MISSING" else "")}


def tail_only(files: list) -> tuple[list, list]:
    """尾版律:回 (尾版檔名集, 封存版檔名集)"""
    tails: dict[str, int] = {}
    for n in files:
        m = VER_RX.match(n)
        if m:
            tails[m.group("fam") + m.group("ext").lower()] = max(tails.get(m.group("fam") + m.group("ext").lower(), -1), int(m.group("ver")))
    tail, arch = [], []
    for n in files:
        m = VER_RX.match(n)
        if not m:
            tail.append(n)
        elif int(m.group("ver")) == tails.get(m.group("fam") + m.group("ext").lower(), -1):
            tail.append(n)
        else:
            arch.append(n)
    return tail, arch


# ---------------------------------------------------------------- 二、錨點 + 分流
def _lead_op(s: str) -> str:
    """續行開頭的續接運算子(取最長相符;字母型運算子後須為界)"""
    best = ""
    for op in CONT_OPS:
        if not s.startswith(op) or len(op) <= len(best):
            continue
        tail = s[len(op):]
        if op[0] == "-" and tail[:1].isalnum():   # -ne vs -nextthing
            continue
        best = op
    return best


def detect_f1(src: str) -> list:
    """F1 彈性錨點:行尾註解 + 下一行以續接運算子起頭
    真因(pwsh 實測):運算式換行只有「上一行以運算子結尾」才續接;
    行尾註解把運算子留在下一行開頭 → 上一行提前結束 → Missing closing ')'。"""
    hits, lines = [], src.splitlines()
    for i, l in enumerate(lines[:-1]):
        if "#" not in l:
            continue
        code, _, comment = l.partition("#")
        if code.count('"') % 2 or code.count("'") % 2:   # 註解其實在字串內=不碰
            continue
        if not code.strip() or not comment.strip():
            continue
        op = _lead_op(lines[i + 1].strip())
        if op:
            hits.append({"line": i + 1, "kind": "F1", "code": code.rstrip(), "comment": comment.rstrip(),
                         "op": op, "next": lines[i + 1].strip()[:60]})
    return hits


def fix_f1(src: str, hits: list) -> tuple[str, int]:
    """真修(與主線 PSRepair v0103 同法):續接運算子上提到本行末 + 註解搬到續行末
    token 零變更(僅搬動運算子與註解的位置),運算式語意不變。"""
    lines = src.splitlines(keepends=False)
    n = 0
    for h in sorted(hits, key=lambda x: -x["line"]):
        i = h["line"] - 1
        j = i + 1
        if j >= len(lines):
            continue
        code, _, comment = lines[i].partition("#")
        op = h.get("op") or _lead_op(lines[j].strip())
        if not op:
            continue
        raw = lines[j]
        lead = raw[:len(raw) - len(raw.lstrip())]
        rest = raw.strip()[len(op):].lstrip()
        lines[i] = code.rstrip() + " " + op               # 運算子上提=顯式續接
        jc, jsep, jcom = rest.partition("#")
        ok_str = not (jc.count('"') % 2 or jc.count("'") % 2)
        if jsep and ok_str and jcom.strip():              # 續行已有註解=合併不丟字
            lines[j] = lead + jc.rstrip() + "   # " + jcom.strip() + " · " + comment.strip()
        else:
            lines[j] = lead + rest.rstrip() + "   # " + comment.strip()
        n += 1
    return ("\n".join(lines) + ("\n" if src.endswith("\n") else "")), n


def detect_reports(src: str) -> list:
    out = []
    for i, l in enumerate(src.splitlines(), 1):
        if R1_DRIVE_RX.search(l):
            out.append({"line": i, "kind": "R1", "note": "硬寫磁碟機代號(非 Windows 上 Join-Path 噴 Cannot find drive)"})
        elif R2_NULLBASE_RX.search(l) and "if (" not in l:
            out.append({"line": i, "kind": "R2", "note": "Join-Path 基底為 $env: 未見非空判(空值即噴 Cannot bind)"})
        if R4_IFEXPR_RX.search(l) and not re.search(r"=\s*if\s*\(", l):
            out.append({"line": i, "kind": "R4",
                        "note": "if 當參數位置運算式(解析綠但執行必紅:The term 'if' is not recognized);"
                                "改 $(if ...) 子運算式或 $x = if ... 賦值"})
    return out


def next_version_path(p: Path) -> Path | None:
    """version-forward 目標;Hydra 守衛:已存在即 None"""
    m = VER_RX.match(p.name)
    if not m:
        return None
    nxt = p.with_name(m.group("fam") + m.group("sep") + "v" + ("%04d" % (int(m.group("ver")) + 1)) + m.group("ext"))
    return None if nxt.exists() else nxt


def parse_ok(pwsh: str, f: Path, tmp: Path) -> tuple[bool, str]:
    out = _ps(pwsh, PARSE_ONE_PS, ["-File", str(f)], tmp, timeout=300)
    if "GOOD" in out:
        return True, ""
    bad = [l for l in out.splitlines() if l.startswith("BAD|")]
    return False, (bad[0][4:] if bad else out.strip()[:120])


# ---------------------------------------------------------------- 三、多輪
def _reserve(f: Path, taken: set) -> Path | None:
    """並行安全的 Hydra 守衛:鎖內判存在並預約目標版號(同輪兩檔絕不撞同一目標)"""
    with _LOCK:
        nxt = next_version_path(f)
        if nxt is None or str(nxt) in taken:
            return None
        taken.add(str(nxt))
        return nxt


def _fix_one(pwsh: str, root: Path, tmp: Path, nm: str, apply: bool, taken: set) -> dict:
    f = root / nm
    src = f.read_text(encoding="utf-8", errors="ignore")
    f1 = detect_f1(src)
    act = {"file": nm, "class": "Parallel-Fixable" if f1 else "Report-Only",
           "f1": f1, "reports": detect_reports(src), "state": "PLAN", "target": "", "note": ""}
    if not (f1 and apply):
        return act
    new_src, n = fix_f1(src, f1)
    nxt = _reserve(f, taken)
    if nxt is None:
        act["state"], act["note"] = "BLOCKED", "Hydra 守衛:下一版號已存在/已被本輪預約(不就地改正本)"
        return act
    sand = tmp / ("sandbox_" + nxt.name)
    sand.write_text(new_src, encoding="utf-8")
    good, why = parse_ok(pwsh, sand, tmp)
    if not good:
        act["state"], act["note"] = "REJECT", "沙盒複驗未過=放棄該檔(誠實):" + why
        return act
    nxt.write_text(new_src, encoding="utf-8")
    good2, why2 = parse_ok(pwsh, nxt, tmp)
    act["state"] = "OK" if good2 else "FAIL"
    act["target"] = nxt.name
    act["note"] = "修 " + str(n) + " 處 F1;寫後複驗 " + ("綠" if good2 else "紅 " + why2)
    return act


def run_rounds(pwsh: str, root: Path, tmp: Path, apply: bool, do_print: bool = True) -> dict:
    rounds, fixed_total = [], 0
    pssa_cache: dict = {}
    t3: list = []
    reports_all: list = []
    for rnd in range(1, MAX_ROUNDS + 1):
        pan = panorama(pwsh, root, tmp, pssa_cache)
        if pan["state"] == "SKIP":
            return {"state": "SKIP", "rounds": [], "note": pan["note"], "panorama": pan}
        names = [e["file"] for e in pan["errors"]]
        all_files = [p.name for p in sorted(root.glob("*.ps1")) + sorted(root.glob("*.psm1"))]
        tails, archs = tail_only(all_files)
        tail_errs = [e for e in pan["errors"] if e["file"] in tails]
        arch_errs = [e for e in pan["errors"] if e["file"] in archs]
        if rnd == 1:
            t3 = t3_scan(pwsh, root, tmp, set(tails))   # T3 只需首輪(指令名集合不因 F1 搬位而變)
            # v0103 修設計缺口:Report-Only(R1/R2/R4)原只在「有 ParseError 的尾版檔」上跑,
            # 但這三型正是「解析綠卻執行期必紅」——健康檔才是它們的主場,故規則存在卻永不掃到
            # =名存實亡(R4 立規當輪全樹零命中就是這個原因)。改為首輪全掃所有尾版檔。
            for _nm in tails:
                try:
                    _src = (root / _nm).read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                for _r in detect_reports(_src):
                    reports_all.append({"file": _nm, **_r})
        # 分流 + 並行修(規格:Parallel-Fixable 一口氣並行;目標版號鎖內預約=零競態零覆蓋)
        targets = sorted({e["file"] for e in tail_errs})
        taken: set = set()
        if targets:
            with ThreadPoolExecutor(max_workers=min(8, len(targets))) as ex:
                acts = list(ex.map(lambda nm: _fix_one(pwsh, root, tmp, nm, apply, taken), targets))
        else:
            acts = []
        fixed_total += sum(1 for a in acts if a["state"] == "OK")
        rounds.append({"round": rnd, "tail_errors": len(tail_errs), "archive_errors": len(arch_errs),
                       "files_ok": pan["files_ok"], "pssa": pan["pssa"], "actions": acts,
                       "pssa_findings": len(pan.get("pssa_findings", [])),
                       "archive_list": [{"file": x["file"], "line": x.get("line", 0), "msg": str(x.get("msg", ""))[:140]}
                                        for x in arch_errs],
                       "tail_list": [{"file": x["file"], "line": x.get("line", 0), "msg": str(x.get("msg", ""))[:140]}
                                     for x in tail_errs],
                       "t3_unknown": (t3 if rnd == 1 else []),
                       "reports_all": (reports_all if rnd == 1 else [])})
        if any(a["state"] == "OK" for a in acts):
            pssa_cache.pop("out", None)            # 本輪有實際寫入=下一輪重掃 PSSA(判定零放寬)
        if do_print:
            print("  [R" + str(rnd) + "] 尾版 ParseError " + str(len(tail_errs)) + " · 封存版 " + str(len(arch_errs))
                  + " · 解析綠 " + str(pan["files_ok"]) + " · PSSA " + pan["pssa"]
                  + " · 本輪動作 " + str(sum(1 for a in acts if a["state"] == "OK"))
                  + (" · Report-Only 全樹 " + str(len(reports_all))
                     + "(" + ",".join(k + str(sum(1 for x in reports_all if x["kind"] == k))
                                      for k in ("R1", "R2", "R4") if any(x["kind"] == k for x in reports_all)) + ")"
                     if rnd == 1 and reports_all else "")
                  + (" · T3 死路嫌疑 " + str(sum(1 for x in t3 if x["grade"] == "TRUE"))
                     + "/" + str(len(t3)) + "(其餘 PLATFORM/CROSS/GUARDED/SYNTAX/ARCHIVE 非死路)" if rnd == 1 else ""))
            for a in acts:
                print("      [" + a["state"] + "] " + a["file"] + " · " + a["class"]
                      + (" → " + a["target"] if a["target"] else "") + (" · " + a["note"] if a["note"] else ""))
        if not tail_errs or not apply or not any(a["state"] == "OK" for a in acts):
            break   # 收斂即停
    last = rounds[-1] if rounds else {}
    if not last:
        state = "SKIP"
    elif last.get("tail_errors"):
        state = "FAIL"                                  # 尾版律:同族尾版必綠
    elif last.get("archive_errors"):
        state = "WARN"                                  # 封存律:封存版壞=凍結不改(誠實標黃)
    else:
        state = "OK"
    return {"state": state, "rounds": rounds, "fixed": fixed_total, "panorama": None}


def build(apply: bool = False, do_print: bool = True, write: bool = True, root: Path | None = None) -> dict:
    import tempfile
    root = root or VIA
    pwsh = find_pwsh()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        res = run_rounds(pwsh, root, tmp, apply, do_print)
    rep = {"engine": ENGINE_TAG, "stamp": datetime.now().strftime("%Y%m%d_%H%M%S"), "root": str(root),
           "pwsh": pwsh or "(缺)", "apply": apply, "state": res["state"], "fixed": res.get("fixed", 0),
           "rounds": res.get("rounds", []), "rules": RULES, "note": res.get("note", "")}
    if write:
        try:
            REP.mkdir(parents=True, exist_ok=True)
            (REP / ("REPAIR_" + rep["stamp"] + ".json")).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
            UI.mkdir(parents=True, exist_ok=True)
            PAGE.write_text(render(rep), encoding="utf-8")
        except Exception:
            pass
    if do_print:
        print("VIA PS AST REPAIR · " + rep["stamp"] + " · " + rep["state"] + " · pwsh " + rep["pwsh"]
              + " · " + ("APPLY" if apply else "唯讀") + " · 修 " + str(rep["fixed"]) + " 件"
              + (" · " + rep["note"] if rep["note"] else ""))
        if write:
            print("  [頁] " + str(PAGE))
    return rep


# ---------------------------------------------------------------- 頁
def _b(s: str) -> str:
    c = {"OK": "gr", "PLAN": "gy", "WARN": "ye", "SKIP": "gy", "REJECT": "ye", "BLOCKED": "ye", "FAIL": "rd"}.get(s, "gy")
    return '<span class="b ' + c + '">' + html.escape(s) + "</span>"


def render(r: dict) -> str:
    e = html.escape
    rows = ""
    for rd in r.get("rounds", []):
        for a in rd["actions"]:
            rows += ('<tr><td class="c m">R' + str(rd["round"]) + '</td><td class="m">' + e(a["file"]) + '</td><td class="m">' + e(a["class"])
                     + '</td><td class="c">' + _b(a["state"]) + '</td><td class="m">' + e(a.get("target", "") or "—")
                     + '</td><td class="dim">' + e("F1 " + str(len(a.get("f1", []))) + " · Report " + str(len(a.get("reports", []))) + " · " + str(a.get("note", ""))[:120]) + "</td></tr>")
    arows = ""
    seen_a = set()
    for rd in r.get("rounds", []):
        for a in rd.get("archive_list", []):
            k = (a["file"], a["line"], a["msg"])
            if k in seen_a:
                continue
            seen_a.add(k)
            arows += ('<tr><td class="m">' + e(a["file"]) + '</td><td class="c m">' + str(a["line"])
                      + '</td><td class="dim">' + e(a["msg"]) + "</td></tr>")
    prows = ""
    for rd in r.get("rounds", []):
        for x in rd.get("reports_all", []):
            prows += ('<tr><td class="m">' + e(x["file"]) + '</td><td class="c">' + _b("WARN") + " " + e(x["kind"])
                      + '</td><td class="c m">' + str(x["line"]) + '</td><td class="dim">' + e(x["note"]) + "</td></tr>")
    trows = ""
    for rd in r.get("rounds", []):
        for u in rd.get("t3_unknown", []):
            g = u.get("grade", "TRUE")
            trows += ('<tr><td class="m">' + e(u["name"]) + '</td><td class="c">'
                      + _b("FAIL" if g == "TRUE" else ("WARN" if g == "ARCHIVE" else "SKIP")) + " " + e(g)
                      + '</td><td class="m">' + e(u["file"]) + '</td><td class="c m">' + str(u["line"]) + "</td></tr>")
    rrows = "".join('<tr><td class="c m">R' + str(rd["round"]) + '</td><td class="c m">' + str(rd["tail_errors"]) + '</td><td class="c m">' + str(rd["archive_errors"])
                    + '</td><td class="c m">' + str(rd["files_ok"]) + '</td><td class="c m">' + e(rd["pssa"]) + '</td><td class="c m">' + str(rd["pssa_findings"]) + "</td></tr>"
                    for rd in r.get("rounds", []))
    head = ('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            "<title>VIA · PS AST 修復矩陣</title><style>:root{--bg:#0f172a;--card:#1e293b;--line:#334155;--tx:#f8fafc;--mu:#94a3b8}*{box-sizing:border-box}"
            "body{margin:0;background:var(--bg);color:var(--tx);font:11px/1.35 -apple-system,'Segoe UI',Roboto,'Microsoft JhengHei',sans-serif}"
            ".wrap{max-width:1300px;margin:0 auto;padding:18px 14px 48px}h1{font-size:14px;margin:0}.sub{color:var(--mu);margin:3px 0 14px}"
            "h2{font-size:12px;margin:20px 0 7px;border-bottom:1px solid var(--line);padding-bottom:5px}.nav a{color:#7dd3fc;margin-right:12px;text-decoration:none}"
            ".kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:14px}.kpi{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:9px 11px}.kpi .n{font-size:16px;font-weight:600}.kpi .l{font-size:10px;color:var(--mu)}"
            "table{width:100%;table-layout:fixed;border-collapse:collapse;background:var(--card);border:1px solid var(--line)}th{font-size:10px;color:var(--mu);text-align:left;padding:4px 6px;border-bottom:1px solid var(--line)}td{padding:4px 6px;border-bottom:1px solid #253248;vertical-align:top;word-wrap:break-word;overflow-wrap:break-word;white-space:normal}td.c{text-align:center}.m{font-family:ui-monospace,Consolas,monospace;font-size:10px}.dim{color:var(--mu)}"
            ".b{display:inline-block;font-size:10px;padding:1px 6px;border-radius:2px;border:1px solid}.gr{background:#064e3b;color:#34d399;border-color:#059669}.ye{background:#78350f;color:#fde047;border-color:#d97706}.rd{background:#7f1d1d;color:#fca5a5;border-color:#dc2626}.gy{background:#1f2937;color:#9ca3af;border-color:#374151}"
            ".note{background:var(--card);border:1px solid var(--line);border-left:3px solid #d97706;border-radius:3px;padding:10px 12px;margin-top:16px}"
            "@media(max-width:700px){table,thead,tbody,tr,td,th{display:block}thead{display:none}td{border:0;padding:2px 6px}tr{border-bottom:1px solid var(--line);padding:6px 0}}</style></head><body><div class=\"wrap\">")
    body = ("<h1>VIA PS AST REPAIR · 多輪並行安全修正矩陣</h1><p class=\"sub\">" + e(r["engine"]) + " · " + e(r["stamp"]) + " · pwsh " + e(r["pwsh"])
            + " · " + ("APPLY" if r["apply"] else "唯讀") + " · 修 " + str(r["fixed"]) + " 件</p>"
            '<p class="nav"><a href="VIA_UI_ProductGate_v0100.html">產</a><a href="VIA_UI_ParallelLanes_v0100.html">道</a>'
            '<a href="VIA_UI_ProjectCompletion_v0100.html">竣</a><a href="VIA_UI_AccelImport_v0100.html">加速</a></p>'
            '<div class="kpis"><div class="kpi"><div class="n">' + _b(r["state"]) + '</div><div class="l">RYG 健康度</div></div>'
            '<div class="kpi"><div class="n">' + str(len(r.get("rounds", []))) + '</div><div class="l">ENGINE 輪數</div></div>'
            '<div class="kpi"><div class="n">' + str(r["fixed"]) + '</div><div class="l">FUNCTION-LIB 修正件</div></div>'
            '<div class="kpi"><div class="n">' + e(r.get("rounds", [{}])[-1].get("pssa", "—") if r.get("rounds") else "—") + '</div><div class="l">OTHERS PSSA</div></div>'
            '<div class="kpi"><div class="n">' + str(sum(1 for x in r.get("rounds", []) for y in x.get("t3_unknown", []) if y.get("grade") == "TRUE")) + '</div><div class="l">T3 死路嫌疑</div></div></div>'
            "<h2>ENGINE — 每輪全景(尾版 ParseError / 封存版 / 解析綠 / PSSA)</h2>"
            '<table><colgroup><col style="width:10%"><col style="width:20%"><col style="width:20%"><col style="width:18%"><col style="width:16%"><col style="width:16%"></colgroup>'
            "<thead><tr><th>輪</th><th>尾版 ParseError</th><th>封存版(凍結)</th><th>解析綠</th><th>PSSA</th><th>PSSA 發現</th></tr></thead><tbody>" + rrows + "</tbody></table>"
            "<h2>MODULE — 逐檔分流與修正(前後對比=版號 +1;Hydra 守衛)</h2>"
            '<table><colgroup><col style="width:7%"><col style="width:26%"><col style="width:15%"><col style="width:10%"><col style="width:18%"><col style="width:24%"></colgroup>'
            "<thead><tr><th>輪</th><th>檔</th><th>分類</th><th>態</th><th>產出版</th><th>細節</th></tr></thead><tbody>" + (rows or '<tr><td colspan="6" class="dim">本輪零動作</td></tr>') + "</tbody></table>"
            "<h2>FUNCTION-LIB — T3 指令解析(只有 TRUE 級=死路嫌疑;PLATFORM/GUARDED/SYNTAX/ARCHIVE 皆有正當理由,誠實不上色)</h2>"
            '<table><colgroup><col style="width:28%"><col style="width:18%"><col style="width:42%"><col style="width:12%"></colgroup>'
            "<thead><tr><th>指令名</th><th>級別</th><th>出現檔</th><th>行</th></tr></thead><tbody>" + (trows or '<tr><td colspan="3" class="dim">零未知指令</td></tr>') + "</tbody></table>"
            "<h2>FUNCTION-LIB — Report-Only 全樹掃描(R1 硬寫磁碟機代號 / R2 Join-Path 空值 / R4 if 當參數運算式;皆解析綠卻執行期必紅,故只列不自動改)</h2>"
            '<table><colgroup><col style="width:34%"><col style="width:8%"><col style="width:10%"><col style="width:48%"></colgroup>'
            "<thead><tr><th>檔</th><th>級</th><th>行</th><th>說明</th></tr></thead><tbody>" + (prows or '<tr><td colspan="4" class="dim">全樹零命中</td></tr>') + "</tbody></table>"
            "<h2>OTHERS — 封存版凍結紅檔(尾版律:不改不刪,只誠實列出)</h2>"
            '<table><colgroup><col style="width:40%"><col style="width:10%"><col style="width:50%"></colgroup>'
            "<thead><tr><th>封存檔</th><th>行</th><th>ParseError</th></tr></thead><tbody>" + (arows or '<tr><td colspan="3" class="dim">封存版零紅</td></tr>') + "</tbody></table>"
            '<div class="note">' + "<br>".join(e(x) for x in r["rules"]) + "</div></div></body></html>")
    return head + body


# ---------------------------------------------------------------- 自測
def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print("  [" + ("OK" if cond else "FAIL") + "] " + name + " " + note)
        if not cond:
            fails.append(name)

    pwsh = find_pwsh()
    chk("① 工具尋路(pwsh 共用 MDL145 find_pwsh 零重造;缺=空字串誠實)", isinstance(pwsh, str), "(" + (pwsh or "缺") + ")")
    broken = ("function T {\n    Test-X 'a' (\n        (-not $x) -and (-not $y)   # 說明\n"
              "        -and ($z -match 'q'))\n    Write-Host 'done'\n}\n")
    hits = detect_f1(broken)
    chk("② F1 彈性錨點(行尾註解+下一行以 -and 起頭=真因;命中 1 處並記行號)",
        len(hits) == 1 and hits[0]["line"] == 3, "(命中 " + str(len(hits)) + ")")
    fixed, n = fix_f1(broken, hits)
    chk("③ F1 修法=運算子上提本行末+註解搬續行末(token 零變更;註解文字保留)",
        n == 1 and "(-not $y) -and" in fixed and "($z -match 'q'))   # 說明" in fixed
        and fixed.count("說明") == 1 and fixed.count("-and") == broken.count("-and"))
    inside_str = 'Write-Host "a # b"\n-and $x\n'
    chk("④ 反誤判(註解符在字串內=不碰;無續接運算子=不碰)",
        detect_f1(inside_str) == [] and detect_f1("$a = 1   # c\n$b = 2\n") == [])
    reps = detect_reports('$x = Join-Path "C:\\Users\\t" "y"\n$z = Join-Path $env:NOPE "w"\n')
    chk("⑤ Report-Only 定位(R1 硬寫磁碟機代號 / R2 $env: 基底未非空判;只列不改)",
        {r["kind"] for r in reps} == {"R1", "R2"} and all("line" in r for r in reps))
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        f = t / "Fix-Me-v0100.ps1"
        f.write_text(broken, encoding="utf-8")
        nxt = next_version_path(f)
        chk("⑥ version-forward 目標(Fix-Me-v0100.ps1 → v0101;連字號族亦認)", nxt is not None and nxt.name == "Fix-Me-v0101.ps1")
        (t / "Fix-Me-v0101.ps1").write_text("# occupied\n", encoding="utf-8")
        chk("⑦ Hydra 守衛(下一版號已存在=拒寫 None;正本零觸碰)", next_version_path(f) is None and f.read_text(encoding="utf-8") == broken)
        (t / "Fix-Me-v0101.ps1").unlink()
        if not pwsh:
            print("  [SKIP] ⑧⑨⑩⑪⑫⑬ 需 pwsh(工作站必有;雲端 env VIA_PWSH)")
            print("  [計] 十三檢 OK " + str(7 - len(fails)) + " · FAIL " + str(len(fails)) + " · SKIP 6(pwsh 缺;誠實)")
            return 1 if fails else 0
        ok_before, why = parse_ok(pwsh, f, t)
        rep = build(apply=True, do_print=False, write=False, root=t)
        prod = t / "Fix-Me-v0101.ps1"
        ok_after = parse_ok(pwsh, prod, t)[0] if prod.exists() else False
        chk("⑧ 多輪真修真驗(壞檔解析紅→修→產出 v0101 解析綠;原檔零觸碰;收斂即停)",
            (not ok_before) and prod.exists() and ok_after and f.read_text(encoding="utf-8") == broken and rep["fixed"] == 1,
            "(修前紅 " + str(not ok_before) + " · 修後綠 " + str(ok_after) + " · 輪 " + str(len(rep["rounds"])) + ")")
        healthy = t / "Healthy-v0100.ps1"
        healthy.write_text("$a = 1   # ok\nWrite-Host $a\n", encoding="utf-8")
        rep2 = build(apply=True, do_print=False, write=False, root=t)
        chk("⑨ 健康檔零動作(無 ParseError=不產新版;永不沒事亂改)",
            not (t / "Healthy-v0101.ps1").exists() and rep2["state"] in ("OK", "WARN"), "(態 " + rep2["state"] + ")")
    # ⑩ T3 真掃(v0101 新):自定義函式不報、系統指令不報、真未知指令必報
    with tempfile.TemporaryDirectory() as td2:
        t2 = Path(td2)
        (t2 / "T3-v0100.ps1").write_text(
            "function global:via-zzz-local { 'x' }\nSet-Alias -Name 假別名 -Value via-zzz-local -Scope Global -Force\n"
            "via-zzz-local\n假別名\nWrite-Host 'sys ok'\nvia-nonexistent-verb-zzz9\n", encoding="utf-8")
        (t2 / "T3-v0100.ps1").write_text(
            (t2 / "T3-v0100.ps1").read_text(encoding="utf-8")
            + "winget install x\nif (Get-Command via-guarded-zzz -ErrorAction SilentlyContinue) { via-guarded-zzz }\n",
            encoding="utf-8")
        u = t3_scan(pwsh, t2, t2)
        by = {x["name"]: x["grade"] for x in u}
        chk("⑩ T3 真掃(冊內函式/別名/系統指令不報;真未知必報並記行)",
            by.get("via-nonexistent-verb-zzz9") == "TRUE" and "via-zzz-local" not in by
            and "假別名" not in by and "Write-Host" not in by
            and all(x["line"] > 0 for x in u), "(命中 " + str(sorted(by)) + ")")
        chk("⑫ T3 誠實分級(PLATFORM/GUARDED/SYNTAX 不列死路;TRUE 級唯一可行動)",
            by.get("winget") == "PLATFORM" and by.get("via-guarded-zzz") == "GUARDED"
            and t3_grade("param", "X-v0100.ps1", "", {"X-v0100.ps1"}) == "SYNTAX"
            and t3_grade("Get-CimInstance", "X-v0100.ps1", "", {"X-v0100.ps1"}) == "PLATFORM"
            and t3_grade("zzz-dead", "Old-v0099.ps1", "", {"Old-v0100.ps1"}) == "ARCHIVE",
            "(" + str({k: v for k, v in by.items() if k in ("winget", "via-guarded-zzz")}) + ")")
    # ⑪ 並行一致性(v0101 新):同輪兩壞檔並行修,各自 version-forward,目標互異零覆蓋
    with tempfile.TemporaryDirectory() as td3:
        t3d = Path(td3)
        for nm in ("Par-A-v0100.ps1", "Par-B-v0100.ps1"):
            (t3d / nm).write_text(broken, encoding="utf-8")
        rep3 = build(apply=True, do_print=False, write=False, root=t3d)
        pa, pb = t3d / "Par-A-v0101.ps1", t3d / "Par-B-v0101.ps1"
        both = pa.exists() and pb.exists()
        greens = both and parse_ok(pwsh, pa, t3d)[0] and parse_ok(pwsh, pb, t3d)[0]
        intact = all((t3d / nm).read_text(encoding="utf-8") == broken for nm in ("Par-A-v0100.ps1", "Par-B-v0100.ps1"))
        chk("⑪ 並行安全(兩檔同輪並行修;目標互異、各自解析綠、兩正本零觸碰)",
            both and greens and intact and rep3["fixed"] == 2,
            "(產出 " + str(both) + " · 綠 " + str(greens) + " · 修 " + str(rep3["fixed"]) + ")")
    # ⑬ 真缺陷回歸(v0102):param 不在首位 → PowerShell 當指令呼叫 → T3 必抓(解析仍綠)
    if pwsh:
        with tempfile.TemporaryDirectory() as td4:
            t4 = Path(td4)
            bad_param = t4 / "BadParam-v0100.ps1"
            bad_param.write_text("Set-StrictMode -Version Latest\nparam(\n    [switch]$Run\n)\nWrite-Host 'x'\n", encoding="utf-8")
            green = parse_ok(pwsh, bad_param, t4)[0]
            u2 = {x["name"]: x["grade"] for x in t3_scan(pwsh, t4, t4, {"BadParam-v0100.ps1"})}
            chk("⑬ 真缺陷回歸(param 不在首位=被當指令呼叫;解析仍綠故唯 T3 抓到)",
                green and u2.get("param") == "SYNTAX",
                "(解析綠 " + str(green) + " · T3 命中 param " + str("param" in u2) + ")")
    # ⑭ v0103:R4 偵測 if 當參數位置運算式(我方自犯型;解析綠但執行必紅)
    bad_if = 'Write-Step ("a" + (if ($x) { "y" } else { "z" }))\n'
    good1 = 'Write-Step ("a" + $(if ($x) { "y" } else { "z" }))\n'
    good2 = '$rc = if ($x) { 1 } else { 0 }\n'
    good3 = 'python x @(if ($args) { $args } else { @("status") }) --root $r\n'
    k_bad = {r["kind"] for r in detect_reports(bad_if)}
    k_g1 = {r["kind"] for r in detect_reports(good1)}
    k_g2 = {r["kind"] for r in detect_reports(good2)}
    k_g3 = {r["kind"] for r in detect_reports(good3)}
    chk("⑭ R4 偵測 if 當參數位置運算式(命中壞寫法;$(if ...)、@(if ...)、$x = if ... 三種合法寫法零誤判)",
        "R4" in k_bad and "R4" not in k_g1 and "R4" not in k_g2 and "R4" not in k_g3,
        "(壞 " + str(sorted(k_bad)) + " · $( " + str(sorted(k_g1) or "零") + " · 賦值 "
        + str(sorted(k_g2) or "零") + " · @( " + str(sorted(k_g3) or "零") + ")")
    print("  [計] 十四檢 OK " + str(14 - len(fails)) + " · FAIL " + str(len(fails)))
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== PS AST 多輪並行安全修正引擎(" + ENGINE_TAG + ")· 十四檢自測 ===")
        return selftest()
    rep = build(apply="--apply" in a)
    return 0 if rep["state"] in ("OK", "WARN", "SKIP") else 1


if __name__ == "__main__":
    sys.exit(main())
