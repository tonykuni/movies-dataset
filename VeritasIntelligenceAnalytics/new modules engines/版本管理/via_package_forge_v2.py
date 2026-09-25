#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA Package Forge v2.0 — Integrated Build System
================================================
整合 G (package_forge) + 結構生成 + 雙硬綁授權 stub + 快照工具註冊。

一次完成:
  1. 建 VeritasIntelligenceAnalytics/ 樹 (含 module/, supportive_module/, 各專案)
  2. 註冊子系統 + 自動編號 (bitIndex 不重用)
  3. 生 commands.json + 各指令 handler stub
  4. 安裝 core/ (router / license_guard / audit / command_registry)
  5. 拷貝雙硬綁面板 + 快照儀表板 HTML
  6. 註冊快照指令 + 預設保留策略 + hooks
  7. 寫 README + product_manifest.json + structure.json + via.ps1 / via.cmd

CLI:
  python via_package_forge_v2.py wizard
  python via_package_forge_v2.py forge --base "C:\\" --projects VRN,VDF,VAP --version 1.0.0
  python via_package_forge_v2.py forge --spec spec.json
  python via_package_forge_v2.py catalog

如果 outputs/ 同層放有以下檔案，會被自動拷入產品包:
  VIA_DualHwBind_Console.html         → tools/
  VIA_Snapshot_Console.html           → tools/
  via_inventory.py                    → tools/
  via_snapshot_integration.py         → tools/
"""

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


import os, sys, json, shutil, argparse, datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# ============================================================
# 1) 規格常數 (與 via_structure_forge 對齊)
# ============================================================
ROOT_FOLDER_NAME = "VeritasIntelligenceAnalytics"
MODULE_LAYER     = "module"
SUPPORTIVE_LAYER = "supportive_module"

# Header (locked) — 與 VHBC 一致
HEADER = {
    "line1": "VeritasIntelligenceAnalytics",
    "line2": "Dual Hard-Bind License Console (VHBC)",
    "line3_template": ("v{version} · 雙硬綁定授權治理面板 · maxDevices={max_devices} · "
                       "HKDF-SHA256 device key derivation · ● online · {ts} · ● {alerts} alert"),
}

# 完整子系統 + 指令 catalog (合併 G 章節 + structure_forge)
CATALOG: Dict[str, Dict[str, Any]] = {
    "VAP": {
        "name": "Veritas Analytics Portal",
        "productId": 1001,
        "bitIndex": 0,
        "description": "資料分析入口與儀表板生成",
        "sub_projects": ["dashboards", "pipelines", "exports", "ui_components"],
        "commands": [
            ("VAP.CORE.INIT.001",      "vap-init",       "初始化 VAP 工作區"),
            ("VAP.IO.SCAN.001",        "vap-scan",       "掃描資料來源"),
            ("VAP.RUN.PIPELINE.001",   "vap-run",        "執行分析管線"),
            ("VAP.UI.DASHBOARD.001",   "vap-dashboard",  "生成儀表板 HTML"),
            ("VAP.EXPORT.REPORT.001",  "vap-export",     "輸出分析報告"),
        ]
    },
    "VRN": {
        "name": "Veritas Reporting Node",
        "productId": 1002,
        "bitIndex": 1,
        "description": "報表合成與 PDF 輸出引擎 (12 模組管線)",
        "sub_projects": ["M01_UnifiedPDFConverter", "M02_ContentParser",
                          "M03_LayoutEngine", "S01_RatingList", "S02_HealthScore"],
        "commands": [
            ("VRN.CORE.INIT.001",      "vrn-init",       "初始化 VRN 環境"),
            ("VRN.IO.FETCH.001",       "vrn-fetch",      "資料抓取"),
            ("VRN.RUN.PIPELINE.001",   "vrn-run",        "12 模組管線 (M01-M08+S01-S04)"),
            ("VRN.BUILD.PDF.001",      "vrn-pdf",        "高品質 PDF 合成"),
            ("VRN.CHECK.HEALTH.001",   "vrn-health",     "健康評分 A-F"),
        ]
    },
    "VDF": {
        "name": "Veritas Data Fusion",
        "alias": "VDS",
        "productId": 1003,
        "bitIndex": 2,
        "description": "資料融合框架 (V12BloomFilter, winloop, parquet)",
        "sub_projects": ["ingest", "fusion", "quality", "schema_registry"],
        "commands": [
            ("VDF.CORE.INIT.001",      "vdf-init",       "初始化 VDF 工作區"),
            ("VDF.IO.INGEST.001",      "vdf-ingest",     "資料攝入"),
            ("VDF.RUN.FUSE.001",       "vdf-fuse",       "執行融合"),
            ("VDF.CHECK.QUALITY.001",  "vdf-quality",    "資料品質檢測"),
        ]
    },
    "VPN": {
        "name": "Veritas Panorama Nexus",
        "productId": 1004,
        "bitIndex": 3,
        "description": "全景監控 + 命令治理",
        "sub_projects": ["system_monitor", "command_governance",
                          "panorama_core", "risk_engine"],
        "commands": [
            ("VPN.CORE.INIT.001",      "vpn-init",       "初始化 VPN"),
            ("VPN.SCAN.PANORAMA.001",  "vpn-scan",       "全景掃描"),
            ("VPN.GOV.AUTHORIZE.001",  "vpn-auth",       "命令授權檢查"),
            ("VPN.MONITOR.START.001",  "vpn-monitor",    "啟動監控服務"),
            ("VPN.BUILD.SYSTEM.001",   "vpn-build",      "建構系統 (Builder)"),
        ]
    },
    "VGF": {
        "name": "Veritas Glyph Forge",
        "productId": 1005,
        "bitIndex": 4,
        "description": "圖像處理 (rembg/MODNet/Real-ESRGAN)",
        "sub_projects": ["vgf_core", "via_image", "vgf_ml"],
        "commands": [
            ("VGF.CORE.INIT.001",      "vgf-init",       "初始化 VGF"),
            ("VGF.IMG.REMBG.001",      "vgf-rembg",      "背景移除"),
            ("VGF.IMG.UPSCALE.001",    "vgf-upscale",    "影像放大 (Real-ESRGAN)"),
            ("VGF.IMG.MATTE.001",      "vgf-matte",      "MODNet 摳圖"),
        ]
    },
    "VEGN": {
        "name": "Veritas Environment Governance Nexus",
        "productId": 1006,
        "bitIndex": 5,
        "description": "Step 1 v3.0 環境健康掃描 → 5D 分類 → 政策計劃 → AI Prompt (唯讀)",
        "sub_projects": ["step1_health_scan", "step2_5d_classify",
                          "step3_policy_plan", "step4_prompt_export"],
        "commands": [
            ("VEGN.CORE.INIT.001",     "vegn-init",      "初始化 VEGN"),
            ("VEGN.SCAN.HEALTH.001",   "vegn-scan",      "環境健康掃描"),
            ("VEGN.CLASS.5D.001",      "vegn-class",     "5D 分類"),
            ("VEGN.PLAN.POLICY.001",   "vegn-plan",      "政策計劃生成"),
            ("VEGN.OUT.PROMPT.001",    "vegn-prompt",    "輸出 AI Prompt"),
        ]
    },
}

# Core 指令 (永遠生)
VIA_CORE_COMMANDS = [
    ("VIA.SYS.HEALTH.001",     "via-health",     "系統健康檢查"),
    ("VIA.SYS.VERSION.001",    "via-version",    "顯示版本資訊"),
    ("VIA.AUTH.STATUS.001",    "via-auth",       "顯示授權狀態"),
    ("VIA.AUTH.ACTIVATE.001",  "via-activate",   "啟用授權 (雙硬綁)"),
    ("VIA.AUTH.VALIDATE.001",  "via-validate",   "校驗授權"),
    ("VIA.SYS.SELFTEST.001",   "via-selftest",   "自動化測試"),
    ("VIA.SYS.CONSOLE.001",    "via-console",    "開啟雙硬綁面板"),
    ("VIA.SYS.LIST.001",       "via-list",       "列出所有指令"),
]

# 快照指令 (與 via_snapshot_integration.py 對齊)
SNAPSHOT_COMMANDS = [
    ("VIA.SNAP.CREATE.001",   "via-snapshot",     "手動拍系統快照"),
    ("VIA.SNAP.LIST.001",     "via-snap-list",    "列出所有快照"),
    ("VIA.SNAP.DIFF.001",     "via-snap-diff",    "比對兩版"),
    ("VIA.SNAP.VERIFY.001",   "via-verify",       "驗證快照完整性"),
    ("VIA.SNAP.ROLLBACK.001", "via-rollback",     "回滾到指定快照"),
    ("VIA.SNAP.BUMP.001",     "via-bump",         "升版號"),
    ("VIA.SNAP.AUTO.001",     "via-snap-auto",    "自動快照"),
    ("VIA.SNAP.RETAIN.001",   "via-snap-retain",  "套用保留策略"),
    ("VIA.SNAP.SYNC.001",     "via-snap-sync",    "推到遠端"),
    ("VIA.SNAP.PULL.001",     "via-snap-pull",    "從遠端拉回"),
    ("VIA.SNAP.STATUS.001",   "via-snap-status",  "快照狀態"),
    ("VIA.SNAP.HOOK.001",     "via-snap-hook",    "設定觸發點"),
    ("VIA.SNAP.CONSOLE.001",  "via-snap-console", "開啟快照儀表板"),
]

# Supportive 模組預設子資料夾
SUPPORTIVE_SUBFOLDERS = ["shared_lib", "common_config", "utils",
                          "templates", "ll_handbook"]


# ============================================================
# 2) Header partial (S 部分：共用)
# ============================================================
HEADER_PARTIAL_HTML = '''<!--
  ============================================================
  VIA HEADER PARTIAL (S — shared, locked)
  Source of truth: tools/_header_partial.html
  改這檔會同步反映到所有 VIA console HTML。
  ============================================================
-->
<header class="hdr">
  <div class="hdr-l1" data-via-header="line1">VeritasIntelligenceAnalytics</div>
  <div class="hdr-l2" data-via-header="line2">__TITLE__</div>
  <div class="hdr-l3" data-via-header="line3">
    v__VERSION__
    <span class="dot">·</span><span data-via-header="subtitle">__SUBTITLE__</span>
    <span class="dot">·</span>maxDevices=__MAX_DEVICES__
    <span class="dot">·</span>HKDF-SHA256 device key derivation
    <span class="dot">·</span><span class="ok">● online</span>
    <span class="dot">·</span><span id="hdr-ts" class="mono-sm"></span>
    <span class="dot">·</span><span class="pin">● <span id="hdr-alert-count">0</span> alert</span>
  </div>
</header>

<script>
/* Universal header timer + alert count sync — shared by all VIA consoles */
(function(){
  function z(n){return String(n).padStart(2,'0');}
  function updHdrTs(){
    var el=document.getElementById('hdr-ts'); if(!el) return;
    var d=new Date();
    el.textContent=d.getUTCFullYear()+'-'+z(d.getUTCMonth()+1)+'-'+z(d.getUTCDate())+
      'T'+z(d.getUTCHours())+':'+z(d.getUTCMinutes())+':'+z(d.getUTCSeconds())+'Z';
  }
  updHdrTs(); setInterval(updHdrTs, 1000);
  window.viaHeaderSetAlerts = function(n){
    var el=document.getElementById('hdr-alert-count');
    if(el) el.textContent = n;
  };
})();
</script>
'''

def render_header_partial(title: str, subtitle: str, version: str,
                           max_devices: int) -> str:
    """安全替換佔位符 (JS 大括號不會被誤解析)"""
    return (HEADER_PARTIAL_HTML
            .replace("__TITLE__", title)
            .replace("__SUBTITLE__", subtitle)
            .replace("__VERSION__", str(version))
            .replace("__MAX_DEVICES__", str(max_devices)))


# ============================================================
# 3) 工具
# ============================================================
def today_ymd() -> str:
    return datetime.date.today().strftime("%Y-%m-%d")

def now_iso_z() -> str:
    try:
        d = datetime.datetime.now(datetime.UTC).replace(microsecond=0, tzinfo=None)
    except AttributeError:
        d = datetime.datetime.utcnow().replace(microsecond=0)
    return d.isoformat() + "Z"

def feature_mask_hex(codes: List[str]) -> str:
    mask = 0
    for c in codes:
        if c in CATALOG:
            mask |= (1 << CATALOG[c]["bitIndex"])
    return f"{mask:08X}"

def banner(s: str):
    print("\n" + "=" * 66)
    print(f"  {s}")
    print("=" * 66)

def resolve_projects(arg: str) -> List[str]:
    if not arg or arg.strip().lower() == "all":
        return list(CATALOG.keys())
    out = []
    for tok in arg.split(","):
        t = tok.strip().upper()
        if t in CATALOG:
            out.append(t)
        else:
            # alias 反查
            for k, v in CATALOG.items():
                if v.get("alias") == t:
                    print(f"  ℹ alias {t} → {k}"); out.append(k); break
            else:
                print(f"  ⚠ 未知子系統: {t}; 略過")
    return list(dict.fromkeys(out))


# ============================================================
# 4) 內嵌模板 (從 G 章節帶來，路徑改成新規格)
# ============================================================
TPL_README = """\
# {product_name}

**Version**: {version}
**Generated**: {generated_at}
**Feature Mask**: `{feature_mask}`
**Subsystems**: {subs_inline}

---

## 結構

```
{root}/
├── via.ps1 / via.cmd        ← 主路由
├── core/                    ← 系統內核 (router / license_guard / audit)
├── auth/                    ← 雙硬綁授權
├── config/                  ← via.config.json / commands.json / snapshot_*.json
├── tools/                   ← 管理工具 + HTML 面板
├── docs/                    ← 自動生成的文件
├── logs/                    ← 日誌與審計
├── snapshots/               ← 快照歷史
└── {module}/                ← 子系統實作層
    ├── {supportive}/        ← 跨子系統共用
{subs_tree}
```

## 快速啟動

```cmd
via via-health             :: 系統健康檢查
via via-activate           :: 雙硬綁定啟用 (此 PC)
via via-list               :: 列出所有指令
via via-console            :: 開啟雙硬綁面板
via via-snapshot           :: 拍快照
via via-snap-console       :: 開啟快照儀表板
```

## 已包含的子系統

{subs_table}

詳見 `docs/COMMANDS.md`。
"""

TPL_VIA_CMD = """\
@echo off
:: VIA Main Launcher (Windows)
setlocal
set VIA_HOME=%~dp0
if "%1"=="" goto :menu
pwsh -NoLogo -ExecutionPolicy Bypass -File "%VIA_HOME%via.ps1" %*
goto :eof

:menu
echo.
echo  ============================================================
echo   {product_name}  v{version}
echo  ============================================================
echo   1. via-health        System health check
echo   2. via-auth          License status
echo   3. via-activate      Activate (dual hard-bind)
echo   4. via-console       Open VHBC console
echo   5. via-snap-console  Open snapshot console
echo   6. via-selftest      Run automated test loop
echo   7. via-list          List all commands
echo   q. quit
echo  ============================================================
set /p choice="Choose: "
if "%choice%"=="1" pwsh -File "%VIA_HOME%via.ps1" via-health
if "%choice%"=="2" pwsh -File "%VIA_HOME%via.ps1" via-auth
if "%choice%"=="3" pwsh -File "%VIA_HOME%via.ps1" via-activate
if "%choice%"=="4" start "" "%VIA_HOME%tools\\VIA_DualHwBind_Console.html"
if "%choice%"=="5" start "" "%VIA_HOME%tools\\VIA_Snapshot_Console.html"
if "%choice%"=="6" pwsh -File "%VIA_HOME%via.ps1" via-selftest
if "%choice%"=="7" pwsh -File "%VIA_HOME%via.ps1" via-list
if /i "%choice%"=="q" goto :eof
goto :menu
"""

TPL_VIA_PS1 = '''\
<#
.SYNOPSIS
    VIA Main Router (PowerShell 7)
#>
param([string]$Command = "", [Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)

$script:VIA_HOME      = $PSScriptRoot
$script:CONFIG_PATH   = Join-Path $script:VIA_HOME "config\\via.config.json"
$script:COMMANDS_PATH = Join-Path $script:VIA_HOME "config\\commands.json"
$script:LOG_PATH      = Join-Path $script:VIA_HOME "logs\\runtime\\via.log"

function Write-Log {{
    param([string]$Level = "INFO", [string]$Message)
    $dir = Split-Path $script:LOG_PATH -Parent
    if (-not (Test-Path $dir)) {{ New-Item -ItemType Directory -Path $dir -Force | Out-Null }}
    $line = ("{{0}} [{{1}}] {{2}}" -f (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"), $Level, $Message)
    Add-Content -Path $script:LOG_PATH -Value $line -Encoding UTF8
}}

function Show-Banner {{
    Write-Host ""
    Write-Host "  ============================================================" -ForegroundColor DarkGray
    Write-Host "   {product_name}" -ForegroundColor Cyan -NoNewline
    Write-Host "  v{version}" -ForegroundColor DarkGray
    Write-Host "  ============================================================" -ForegroundColor DarkGray
}}

if (-not $Command) {{
    Show-Banner
    Write-Host "  Usage: via <alias or CMD-ID> [args]"
    Write-Host "  Try:   via via-list"
    return
}}

if (-not (Test-Path $script:COMMANDS_PATH)) {{ Write-Error "commands.json missing"; return }}
$registry = Get-Content $script:COMMANDS_PATH -Raw | ConvertFrom-Json
$cmd = $registry.commands | Where-Object {{ $_.alias -eq $Command -or $_.id -eq $Command }} | Select-Object -First 1
if (-not $cmd) {{
    Write-Host "  ✗ Unknown command: $Command" -ForegroundColor Red
    Write-Host "    Try: via via-list" -ForegroundColor DarkGray
    Write-Log "ERROR" "unknown command: $Command"; return
}}

$scriptPath = Join-Path $script:VIA_HOME $cmd.script
if (-not (Test-Path $scriptPath)) {{
    Write-Host "  ✗ Handler missing: $($cmd.script)" -ForegroundColor Red
    Write-Log "ERROR" "handler missing: $($cmd.script)"; return
}}

Write-Log "INFO" "exec $($cmd.id) ($($cmd.alias))"
& py -3.11 $scriptPath @Args
$exit = $LASTEXITCODE

# Fire post-* hooks based on command id
switch -Wildcard ($cmd.id) {{
    "VIA.AUTH.ACTIVATE.*" {{ Invoke-SnapshotHook -Trigger "post-activate" -Note "after $($cmd.alias)" }}
    "VIA.SYS.SELFTEST.*"  {{ if ($exit -eq 0) {{ Invoke-SnapshotHook -Trigger "post-selftest" -Note "selftest passed" }} }}
}}

Write-Log "INFO" "done $($cmd.id) exit=$exit"
exit $exit

function Invoke-SnapshotHook {{
    param([string]$Trigger, [string]$Note = "")
    $hookCfg = Join-Path $script:VIA_HOME "config\\snapshot_hooks.json"
    if (-not (Test-Path $hookCfg)) {{ return }}
    try {{
        $cfg = Get-Content $hookCfg -Raw | ConvertFrom-Json
        if ($cfg.enabled -contains $Trigger) {{
            $intPy = Join-Path $script:VIA_HOME "tools\\via_snapshot_integration.py"
            if (Test-Path $intPy) {{
                Write-Log "INFO" "snapshot hook fired: $Trigger"
                & py -3.11 $intPy auto --trigger $Trigger --note $Note 2>&1 |
                    ForEach-Object {{ Write-Log "HOOK" $_ }} | Out-Null
            }}
        }}
    }} catch {{
        Write-Log "WARN" "snapshot hook error: $_"
    }}
}}
'''

TPL_CORE_REGISTRY = '''\
"""core/command_registry.py — auto-generated"""
SUBSYSTEM_BIT = {subsys_bit}
SUBSYSTEM_NAME = {subsys_name}
'''

TPL_CORE_AUDIT = '''\
"""core/audit.py — unified audit log"""
import json, datetime
from pathlib import Path
LOG = Path(__file__).resolve().parent.parent / "logs" / "audit.log"
LOG.parent.mkdir(parents=True, exist_ok=True)
def log(action: str, detail):
    try: ts = datetime.datetime.now(datetime.UTC).replace(microsecond=0, tzinfo=None).isoformat() + "Z"
    except AttributeError: ts = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": ts, "action": action, "detail": detail}, ensure_ascii=False) + "\\n")
'''

TPL_CORE_LICENSE_GUARD = '''\
"""
core/license_guard.py — 內嵌授權守門
檢查當前 PC 的 dual_hwbind 記錄是否：
  1. 存在 (license activated)
  2. status == "Active"
  3. featureMaskHex 包含當前指令的 subsystem bit
"""
import sys, json, os
from pathlib import Path

VIA_HOME = Path(__file__).resolve().parent.parent
DB = VIA_HOME / "auth" / "registry" / "dual_hwbind.json"

# 從 command_registry 取 bit map
try:
    from core.command_registry import SUBSYSTEM_BIT
except ImportError:
    SUBSYSTEM_BIT = {}


def _mask_includes(mask_hex: str, bit_index: int) -> bool:
    try:
        return (int(mask_hex, 16) >> bit_index) & 1 == 1
    except (ValueError, TypeError):
        return False


def require(subsys_code: str) -> bool:
    """
    在每個子系統 handler 開頭呼叫:
        from core.license_guard import require
        require("VRN")
    通過則繼續；不通過 sys.exit() 直接結束。
    """
    if not DB.exists():
        print(f"✗ License not activated. Run: via via-activate"); sys.exit(10)

    try:
        items = json.loads(DB.read_text(encoding="utf-8") or "[]")
    except Exception as e:
        print(f"✗ License DB corrupt: {e}"); sys.exit(11)

    if not items:
        print(f"✗ No active license bindings"); sys.exit(12)

    bit = SUBSYSTEM_BIT.get(subsys_code)
    if bit is None:
        print(f"✗ Unknown subsystem in registry: {subsys_code}"); sys.exit(13)

    # 找任一 Active 且 mask 包含此子系統的 binding
    for rec in items:
        if rec.get("status", "Active") != "Active":
            continue
        mask = rec.get("featureMaskHex", "00000000")
        if _mask_includes(mask, bit):
            return True

    print(f"✗ Subsystem '{subsys_code}' (bit={bit}) is NOT in your license mask.")
    available_masks = [r.get("featureMaskHex", "?") for r in items if r.get("status", "Active") == "Active"]
    if available_masks:
        print(f"  Active masks on this PC: {available_masks}")
    sys.exit(14)
'''

TPL_CMD_HANDLER = '''\
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{cmd_id} — {description}
Subsystem: {subsys} ({subsys_name})
Alias:     {alias}
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[{parents_depth}]))

{license_check}from core.audit import log

def main(argv):
    log("{cmd_id}", {{"argv": argv}})
    print(f"[{cmd_id}] {description}")
    print(f"  alias    : {alias}")
    print(f"  subsystem: {subsys} - {subsys_name}")
    print(f"  args     : {{argv}}")
    # TODO: 實作邏輯
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''

TPL_VIA_HEALTH = '''\
#!/usr/bin/env python3
import sys, json, platform
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.audit import log

def main(argv):
    cfg = json.loads((Path(__file__).resolve().parents[1] / "config" / "via.config.json").read_text(encoding="utf-8"))
    print(f"╔════════════════════════════════════════════════════════╗")
    print(f"║  {cfg['product_name']}")
    print(f"║  Version    : {cfg['version']}")
    print(f"║  Subsystems : {', '.join(cfg['subsystems'])}")
    print(f"║  Mask       : {cfg['feature_mask_hex']}")
    print(f"║  Python     : {platform.python_version()}")
    print(f"║  Platform   : {platform.system()} {platform.release()}")
    print(f"║  Status     : ✓ OK")
    print(f"╚════════════════════════════════════════════════════════╝")
    log("VIA.SYS.HEALTH.001", "ok")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''

TPL_VIA_LIST = '''\
#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def main(argv):
    reg = json.loads((Path(__file__).resolve().parents[1] / "config" / "commands.json").read_text(encoding="utf-8"))
    cur = None
    for c in sorted(reg["commands"], key=lambda x: x["id"]):
        sub = c["id"].split(".")[0]
        if sub != cur:
            cur = sub; print(f"\\n  [{sub}]")
        print(f"    {c['alias']:18s}  {c['id']:28s}  {c['description']}")
    print()
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''

TPL_VIA_SELFTEST = '''\
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA.SYS.SELFTEST.001 — Automated self-test loop
五階段: TEST → DEBUG → OPTIMIZE → CONSOLIDATE → USER-TEST
"""
import sys, json, time, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.audit import log

PASS = 0; FAIL = 0; ERRORS = []

def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        print(f"  ✓ {name}"); PASS += 1
    else:
        print(f"  ✗ {name}  {detail}"); FAIL += 1
        ERRORS.append({"name": name, "detail": detail})

def banner(s):
    print("\\n" + "=" * 60 + f"\\n  {s}\\n" + "=" * 60)


def main(argv):
    banner("VIA SELFTEST — 5-stage automated loop")

    # ============ TEST ============
    banner("[1/5] TEST — basic functionality")

    cfg_path = ROOT / "config" / "via.config.json"
    check("config/via.config.json exists", cfg_path.exists())
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        check("version present", bool(cfg.get("version")))
        check("subsystems list non-empty", bool(cfg.get("subsystems")))
        check("feature_mask_hex 8 chars", len(cfg.get("feature_mask_hex","")) == 8)

    cmds_path = ROOT / "config" / "commands.json"
    check("config/commands.json exists", cmds_path.exists())
    if cmds_path.exists():
        cmds = json.loads(cmds_path.read_text(encoding="utf-8"))
        n = len(cmds.get("commands", []))
        check(f"commands registered (count={n})", n > 0)

    check("core/audit.py exists", (ROOT/"core/audit.py").exists())
    check("core/license_guard.py exists", (ROOT/"core/license_guard.py").exists())
    check("core/command_registry.py exists", (ROOT/"core/command_registry.py").exists())
    check("via.ps1 exists", (ROOT/"via.ps1").exists())
    check("via.cmd exists", (ROOT/"via.cmd").exists())

    # ============ DEBUG ============
    banner("[2/5] DEBUG — handler integrity")

    # 每個註冊指令的 handler 檔都要存在
    missing_handlers = []
    if cmds_path.exists():
        for c in cmds["commands"]:
            p = ROOT / c["script"]
            if not p.exists():
                missing_handlers.append(c["id"])
    check(f"all handler files present ({len(cmds.get('commands',[]))} total)",
          not missing_handlers,
          f"missing: {missing_handlers[:3]}" if missing_handlers else "")

    # core 模組可以正常 import
    try:
        from core.audit import log as _log
        check("core.audit importable", True)
    except Exception as e:
        check("core.audit importable", False, str(e))

    try:
        from core.license_guard import require, _mask_includes
        # 內部測試 _mask_includes 邏輯
        check("mask includes bit 0 of 0x07", _mask_includes("00000007", 0))
        check("mask includes bit 1 of 0x07", _mask_includes("00000007", 1))
        check("mask includes bit 2 of 0x07", _mask_includes("00000007", 2))
        check("mask excludes bit 3 of 0x07", not _mask_includes("00000007", 3))
    except Exception as e:
        check("license_guard logic", False, str(e))

    # ============ OPTIMIZE ============
    banner("[3/5] OPTIMIZE — performance baseline")

    t0 = time.time()
    for _ in range(100):
        json.loads(cmds_path.read_text(encoding="utf-8"))
    elapsed = (time.time() - t0) * 1000
    check(f"100x commands.json load < 1000ms ({elapsed:.0f}ms)", elapsed < 1000)

    t0 = time.time()
    result = subprocess.run([sys.executable, str(ROOT/"bin/via_health.py")],
                             capture_output=True, text=True, timeout=10)
    elapsed = (time.time() - t0) * 1000
    check(f"via_health.py runs < 5000ms ({elapsed:.0f}ms)", elapsed < 5000 and result.returncode == 0)

    # ============ CONSOLIDATE ============
    banner("[4/5] CONSOLIDATE — end-to-end integration")

    # 跑 via-list 看是否能輸出
    r = subprocess.run([sys.executable, str(ROOT/"bin/via_list.py")],
                        capture_output=True, text=True, timeout=10)
    check("via_list.py exits 0", r.returncode == 0)
    check("via_list.py produces output", len(r.stdout) > 100)

    # 跑 inventory scan
    inv_path = ROOT / "tools" / "via_inventory.py"
    if inv_path.exists():
        r = subprocess.run([sys.executable, str(inv_path), "--base", str(ROOT), "scan"],
                            capture_output=True, text=True, timeout=30)
        check("via_inventory.py scan exits 0", r.returncode == 0)
        check("scan output mentions Merkle", "Merkle" in r.stdout)

    # ============ USER-TEST ============
    banner("[5/5] USER-TEST — real workflow simulation")

    # 測 license_guard 對未授權子系統真的會擋
    auth_db = ROOT / "auth" / "registry" / "dual_hwbind.json"
    auth_existed = auth_db.exists()
    auth_backup = None
    if auth_existed:
        auth_backup = auth_db.read_text(encoding="utf-8")

    try:
        # 暫時清空授權
        auth_db.parent.mkdir(parents=True, exist_ok=True)
        auth_db.write_text("[]", encoding="utf-8")

        # 隨機找一個子系統 cmd 來試
        subs_cmds = [c for c in cmds["commands"]
                      if c["subsystem"] not in ("VIA",) and c["id"].endswith(".001")]
        if subs_cmds:
            test_cmd = subs_cmds[0]
            r = subprocess.run([sys.executable, str(ROOT/test_cmd["script"])],
                                capture_output=True, text=True, timeout=10)
            check(f"unauthorized {test_cmd['subsystem']} cmd rejected (exit != 0)",
                  r.returncode != 0)

            # 給足 mask 再試
            full_mask = "FFFFFFFF"
            auth_db.write_text(json.dumps([{
                "productKey": "SELFTEST", "featureMaskHex": full_mask,
                "status": "Active", "fpHash": "selftest", "slotIndex": 1
            }]), encoding="utf-8")
            r = subprocess.run([sys.executable, str(ROOT/test_cmd["script"])],
                                capture_output=True, text=True, timeout=10)
            check(f"authorized {test_cmd['subsystem']} cmd passes (exit 0)",
                  r.returncode == 0, f"stderr: {r.stderr[:200]}")
    finally:
        # 還原原來授權狀態
        if auth_existed and auth_backup is not None:
            auth_db.write_text(auth_backup, encoding="utf-8")
        elif not auth_existed and auth_db.exists():
            auth_db.unlink()

    # ============ Summary ============
    banner("SELFTEST SUMMARY")
    total = PASS + FAIL
    print(f"  Pass : {PASS}/{total}")
    print(f"  Fail : {FAIL}/{total}")
    print(f"  Status: {'✓ ALL PASS' if FAIL == 0 else '✗ ' + str(FAIL) + ' FAILURES'}")
    if ERRORS:
        print(f"\\n  Failures:")
        for e in ERRORS[:10]:
            print(f"    - {e['name']}: {e['detail']}")

    log("VIA.SYS.SELFTEST.001", {"pass": PASS, "fail": FAIL})

    # 寫報告
    report = ROOT / "logs" / "selftest_report.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({
        "pass": PASS, "fail": FAIL, "total": total,
        "errors": ERRORS, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\\n  Report: logs/selftest_report.json")

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
'''


# ============================================================
# 5) ProductSpec & Forge
# ============================================================
class ProductSpec:
    def __init__(self, base: str, subsystems: List[str], version: str,
                 product_name: str, max_devices: int = 2):
        self.base = Path(base).resolve()
        self.subsystems = resolve_projects(",".join(subsystems) if isinstance(subsystems, list) else subsystems)
        if not self.subsystems:
            raise ValueError("沒有有效的子系統")
        self.version = version
        self.product_name = product_name
        self.max_devices = max_devices
        self.feature_mask = feature_mask_hex(self.subsystems)
        self.generated_at = now_iso_z()
        self.root_path = self.base / ROOT_FOLDER_NAME

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base": str(self.base),
            "root_folder": ROOT_FOLDER_NAME,
            "root_path": str(self.root_path),
            "product_name": self.product_name,
            "version": self.version,
            "subsystems": self.subsystems,
            "featureMaskHex": self.feature_mask,
            "max_devices": self.max_devices,
            "generated_at": self.generated_at,
        }


class IntegratedForge:
    """整合版 Forge：一次完成結構 + 指令 + 工具"""

    def __init__(self, spec: ProductSpec, dry_run: bool = False,
                 source_dir: Optional[Path] = None):
        self.spec = spec
        self.dry = dry_run
        self.source_dir = source_dir or Path(__file__).resolve().parent
        self.created = []

    def _write(self, rel: str, content: str):
        full = self.spec.root_path / rel
        rel_full = str(full.relative_to(self.spec.base)).replace("\\", "/")
        self.created.append(rel_full)
        if self.dry:
            print(f"  [DRY] write  {rel_full}  ({len(content)} bytes)"); return
        full.parent.mkdir(parents=True, exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

    def _mkdir(self, rel: str):
        full = self.spec.root_path / rel if rel else self.spec.root_path
        rel_full = str(full.relative_to(self.spec.base)).replace("\\", "/")
        self.created.append(rel_full + "/")
        if self.dry:
            print(f"  [DRY] mkdir  {rel_full}/"); return
        full.mkdir(parents=True, exist_ok=True)

    def _copy(self, src_name: str, rel_dst: str) -> bool:
        src = self.source_dir / src_name
        if not src.exists():
            print(f"  ⊘ skip (source missing): {src_name}")
            return False
        dst = self.spec.root_path / rel_dst
        rel_full = str(dst.relative_to(self.spec.base)).replace("\\", "/")
        self.created.append(rel_full)
        if self.dry:
            print(f"  [DRY] copy   {src_name} → {rel_full}"); return True
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"  ✓ copy   {src_name} → {rel_full}")
        return True

    def forge(self):
        s = self.spec
        banner(f"FORGING — {s.product_name} v{s.version}")
        print(f"  Base       : {s.base}")
        print(f"  Root       : {s.root_path}")
        print(f"  Subsystems : {s.subsystems}")
        print(f"  Mask       : {s.feature_mask}")
        print(f"  Dry run    : {self.dry}")

        # 預檢
        if s.root_path.exists() and any(s.root_path.iterdir()) and not self.dry:
            ans = input(f"\n  ⚠ {s.root_path} 不是空的，繼續會覆寫。確認? [y/N] ").strip().lower()
            if ans != "y": print("  取消。"); return

        # ====== 1. 主結構 (根 + 標準資料夾) ======
        print("\n[1/9] 建立主結構...")
        for d in ["", "core", "auth/registry", "bin", "tools",
                  "logs/runtime", "config", "docs", "snapshots"]:
            self._mkdir(d)

        # ====== 2. module/ + supportive_module/ ======
        print(f"[2/9] 建立 {MODULE_LAYER}/ + {SUPPORTIVE_LAYER}/...")
        self._mkdir(MODULE_LAYER)
        for extra in ["docs", "schemas"]:
            self._mkdir(f"{MODULE_LAYER}/{extra}")
        sup_root = f"{MODULE_LAYER}/{SUPPORTIVE_LAYER}"
        self._mkdir(sup_root)
        for sf in SUPPORTIVE_SUBFOLDERS:
            self._mkdir(f"{sup_root}/{sf}")
        self._write(f"{sup_root}/README.md",
            "# Supportive Module\n\n跨子系統共用元件、工具、模板與 Lessons Learned Handbook。\n")
        self._write(f"{sup_root}/shared_lib/__init__.py", "")
        self._write(f"{sup_root}/utils/__init__.py", "")

        # ====== 3. 各子系統 (module/<CODE>/) ======
        print(f"[3/9] 建立 {len(s.subsystems)} 個子系統...")
        for code in s.subsystems:
            info = CATALOG[code]
            proj_root = f"{MODULE_LAYER}/{code}"
            self._mkdir(proj_root)
            # 標準子資料夾
            for sf in ["cmd", "lib", "tests", "docs"]:
                self._mkdir(f"{proj_root}/{sf}")
            # 子專案
            for sp in info["sub_projects"]:
                self._mkdir(f"{proj_root}/{sp}")
            # __init__
            self._write(f"{proj_root}/__init__.py", "")
            self._write(f"{proj_root}/cmd/__init__.py", "")
            # manifest
            manifest = {
                "code": code, "name": info["name"],
                "alias": info.get("alias"),
                "productId": info["productId"], "bitIndex": info["bitIndex"],
                "description": info["description"],
                "sub_projects": info["sub_projects"],
                "commands": [{"id": c, "alias": a, "description": d}
                              for c, a, d in info["commands"]],
                "created_at": today_ymd(),
            }
            self._write(f"{proj_root}/manifest.json",
                        json.dumps(manifest, ensure_ascii=False, indent=2))
            # README
            alias_note = f"_Alias: {info['alias']}_\n\n" if info.get("alias") else ""
            self._write(f"{proj_root}/README.md",
                f"# {code} — {info['name']}\n\n{alias_note}"
                f"productId: `{info['productId']}` · bitIndex: `{info['bitIndex']}`\n\n"
                f"{info['description']}\n\n## 子專案\n\n" +
                "\n".join(f"- `{sp}/`" for sp in info["sub_projects"]) + "\n\n"
                f"## 指令 ({len(info['commands'])})\n\n" +
                "\n".join(f"- `{a}` — {d}  (`{c}`)" for c, a, d in info["commands"]) + "\n")

        # ====== 4. core/ 模組 ======
        print("[4/9] 寫 core/ (router / license_guard / audit / registry)...")
        self._write("core/__init__.py", "")
        self._write("core/audit.py", TPL_CORE_AUDIT)
        self._write("core/license_guard.py", TPL_CORE_LICENSE_GUARD)
        bit_dict = {c: CATALOG[c]["bitIndex"] for c in s.subsystems}
        name_dict = {c: CATALOG[c]["name"] for c in s.subsystems}
        self._write("core/command_registry.py", TPL_CORE_REGISTRY.format(
            subsys_bit=json.dumps(bit_dict, indent=4),
            subsys_name=json.dumps(name_dict, indent=4, ensure_ascii=False)))

        # ====== 5. 指令 handlers ======
        print("[5/9] 寫指令 handlers (core + 子系統 + 快照)...")
        all_commands: List[Dict[str, Any]] = []

        # 5a. Core
        for cid, al, ds in VIA_CORE_COMMANDS:
            rel = f"bin/{al.replace('-', '_')}.py"
            all_commands.append({"id": cid, "alias": al, "subsystem": "VIA",
                                  "script": rel, "description": ds, "status": "Active"})
            if cid == "VIA.SYS.HEALTH.001": self._write(rel, TPL_VIA_HEALTH)
            elif cid == "VIA.SYS.LIST.001": self._write(rel, TPL_VIA_LIST)
            elif cid == "VIA.SYS.SELFTEST.001": self._write(rel, TPL_VIA_SELFTEST)
            else:
                self._write(rel, TPL_CMD_HANDLER.format(
                    cmd_id=cid, alias=al, description=ds,
                    subsys="VIA", subsys_name="VIA Core",
                    license_check="", parents_depth=1))

        # 5b. 子系統 — 放在 module/<CODE>/cmd/
        for code in s.subsystems:
            info = CATALOG[code]
            for cid, al, ds in info["commands"]:
                rel = f"{MODULE_LAYER}/{code}/cmd/{cid.replace('.', '_')}.py"
                all_commands.append({"id": cid, "alias": al, "subsystem": code,
                                      "script": rel, "description": ds, "status": "Active"})
                self._write(rel, TPL_CMD_HANDLER.format(
                    cmd_id=cid, alias=al, description=ds,
                    subsys=code, subsys_name=info["name"],
                    license_check=f'from core.license_guard import require\nrequire("{code}")\n\n',
                    parents_depth=3))

        # 5c. 快照指令 (直接指到 tools/, 由 via_snapshot_integration 處理)
        for cid, al, ds in SNAPSHOT_COMMANDS:
            # 全部指到 integration; via_inventory 例外的幾個指向 inventory
            if cid in ("VIA.SNAP.CREATE.001", "VIA.SNAP.LIST.001",
                        "VIA.SNAP.DIFF.001", "VIA.SNAP.VERIFY.001",
                        "VIA.SNAP.ROLLBACK.001", "VIA.SNAP.BUMP.001"):
                rel = "tools/via_inventory.py"
            else:
                rel = "tools/via_snapshot_integration.py"
            all_commands.append({"id": cid, "alias": al, "subsystem": "VIA",
                                  "script": rel, "description": ds, "status": "Active"})

        # ====== 6. config/ ======
        print("[6/9] 寫 config/...")
        self._write("config/via.config.json", json.dumps({
            "product_name": s.product_name, "version": s.version,
            "feature_mask_hex": s.feature_mask, "subsystems": s.subsystems,
            "max_devices": s.max_devices, "generated_at": s.generated_at,
            "python": "py -3.11", "log_level": "INFO",
            "audit_enabled": True, "license_required": True,
            "root_folder": ROOT_FOLDER_NAME,
            "module_layer": MODULE_LAYER,
        }, ensure_ascii=False, indent=2))

        self._write("config/commands.json", json.dumps({
            "generated_at": s.generated_at, "version": s.version,
            "feature_mask_hex": s.feature_mask, "commands": all_commands
        }, ensure_ascii=False, indent=2))

        # 快照預設策略 + hooks
        self._write("config/snapshot_retention.json", json.dumps({
            "keep_all_major": True, "keep_all_minor": True,
            "keep_recent_patch": 10, "keep_all_archived": True,
            "min_age_days": 1, "max_total": 100
        }, indent=2))
        self._write("config/snapshot_hooks.json", json.dumps({
            "enabled": ["post-activate", "post-forge"],
            "auto_retention": True
        }, indent=2))

        # ====== 7. tools/ — 拷貝面板與工具 (S: 共用 header partial) ======
        print("[7/9] 拷貝 tools/ (HTML 面板 + Python 工具 + 共用 header)...")
        # 共用 header
        header_html = render_header_partial(
            title="Dual Hard-Bind License Console (VHBC)",
            subtitle="雙硬綁定授權治理面板",
            version=s.version, max_devices=s.max_devices)
        self._write("tools/_header_partial.html", header_html)

        copied_files = []
        for name, dst in [
            ("VIA_DualHwBind_Console.html",   "tools/VIA_DualHwBind_Console.html"),
            ("VIA_Snapshot_Console.html",     "tools/VIA_Snapshot_Console.html"),
            ("via_inventory.py",              "tools/via_inventory.py"),
            ("via_snapshot_integration.py",   "tools/via_snapshot_integration.py"),
        ]:
            if self._copy(name, dst):
                copied_files.append(name)

        if not copied_files:
            print("  ℹ 找不到 HTML/Python 工具來源；產品包仍可運作，但管理面板/快照需另外裝")

        # ====== 8. 主路由 + README + structure.json ======
        print("[8/9] 寫主路由 + README + structure.json...")
        self._write("via.cmd", TPL_VIA_CMD.format(
            product_name=s.product_name, version=s.version))
        self._write("via.ps1", TPL_VIA_PS1.format(
            product_name=s.product_name, version=s.version))
        self._write("VERSION", s.version + "\n")
        self._write("product_manifest.json",
                    json.dumps(s.to_dict(), ensure_ascii=False, indent=2))

        # structure.json (與 via_structure_forge 對齊的格式)
        structure = {
            "root_folder": ROOT_FOLDER_NAME, "base": str(s.base),
            "module_layer": MODULE_LAYER, "supportive_layer": SUPPORTIVE_LAYER,
            "projects": [
                {"code": c, "name": CATALOG[c]["name"],
                 "alias": CATALOG[c].get("alias"),
                 "path": f"{MODULE_LAYER}/{c}",
                 "sub_projects": CATALOG[c]["sub_projects"]}
                for c in s.subsystems
            ],
            "generated_at": s.generated_at,
        }
        self._write("structure.json", json.dumps(structure, ensure_ascii=False, indent=2))

        # README
        subs_table = "\n".join(
            f"- **{c}**{' (alias: '+CATALOG[c]['alias']+')' if CATALOG[c].get('alias') else ''} — "
            f"{CATALOG[c]['name']} (productId={CATALOG[c]['productId']}, bit={CATALOG[c]['bitIndex']})"
            for c in s.subsystems)
        subs_tree = "\n".join(
            f"    ├── {c}/  ({CATALOG[c]['name']})" for c in s.subsystems)
        self._write("README.md", TPL_README.format(
            product_name=s.product_name, version=s.version,
            generated_at=s.generated_at, feature_mask=s.feature_mask,
            subs_inline=", ".join(s.subsystems),
            subs_table=subs_table, root=ROOT_FOLDER_NAME,
            module=MODULE_LAYER, supportive=SUPPORTIVE_LAYER,
            subs_tree=subs_tree))

        # ====== 9. 文件 ======
        print("[9/9] 寫 docs/...")
        self._write("docs/NUMBERING.md", self._gen_numbering_md())
        self._write("docs/COMMANDS.md", self._gen_commands_md(all_commands))

        # .gitignore + 範本
        self._write(".gitignore",
            "logs/\nauth/registry/*.json\nauth/master.key\n__pycache__/\n"
            "*.pyc\nsnapshots/*/files.tar.gz\n")
        self._write("auth/master.key.example",
            "# 設定環境變數 VIA_LICENSE_SECRET 取代此檔\n"
            "# Windows: setx VIA_LICENSE_SECRET \"<long-random>\"\n")

        # ====== 摘要 ======
        banner("✓ FORGE COMPLETE")
        print(f"  Root        : {s.root_path}")
        print(f"  Items       : {len(self.created)}")
        print(f"  Subsystems  : {len(s.subsystems)}")
        print(f"  Commands    : {len(all_commands)}  "
              f"(core={len(VIA_CORE_COMMANDS)} + "
              f"subsystems={sum(len(CATALOG[c]['commands']) for c in s.subsystems)} + "
              f"snapshot={len(SNAPSHOT_COMMANDS)})")
        if not self.dry:
            print(f"\n  下一步:")
            print(f"    cd \"{s.root_path}\"")
            print(f"    via via-health")
            print(f"    via via-list")
            print(f"    via via-activate")
        else:
            print(f"\n  (dry-run; 移除 --dry-run 真的生)")

    def _gen_numbering_md(self) -> str:
        return """\
# VIA Command Numbering — CMD-ID Spec

## Format
`<SUBSYS>.<DOMAIN>.<VERB>.<NNN>`

- SUBSYS — VAP / VRN / VDF / VPN / VGF / VEGN / VIA
- DOMAIN — CORE / IO / RUN / BUILD / CHECK / EXPORT / SNAP / AUTH / SYS / UI / GOV / MONITOR
- VERB — INIT / SCAN / PIPELINE / etc.
- NNN — 001-999 (NEVER reused)

## Rules
1. CMD-IDs are immutable.
2. Serial numbers never reused (deprecated → status "Deprecated", same ID).
3. 1 CMD-ID = 1 handler file.
4. License enforcement: SUBSYS prefix checked against `featureMaskHex`.
"""

    def _gen_commands_md(self, commands: List[Dict[str, Any]]) -> str:
        s = self.spec
        lines = [f"# {s.product_name} — Command Dictionary", "",
                 f"Total: {len(commands)} commands", "",
                 f"Auto-generated. Do not edit by hand.", ""]
        cur_sub = None
        for c in sorted(commands, key=lambda x: x["id"]):
            sub = c["subsystem"]
            if sub != cur_sub:
                cur_sub = sub
                lines += [f"\n## {sub}", "",
                          "| CMD-ID | Alias | Script | Description |", "|---|---|---|---|"]
            lines.append(f"| `{c['id']}` | `{c['alias']}` | `{c['script']}` | {c['description']} |")
        return "\n".join(lines) + "\n"


# ============================================================
# 6) Wizard + CLI
# ============================================================
def wizard():
    banner("VIA Package Forge v2.0 — Wizard")

    default_base = "C:\\" if os.name == "nt" else os.path.expanduser("~")
    base = input(f"\n  BASE 路徑 [{default_base}]: ").strip() or default_base
    print(f"\n  ➜ 將建在: {Path(base) / ROOT_FOLDER_NAME}")

    name = input("  產品名稱 [VIA Custom Pack]: ").strip() or "VIA Custom Pack"
    version = input("  版本 [1.0.0]: ").strip() or "1.0.0"

    print("\n  可用子系統:")
    keys = list(CATALOG.keys())
    for i, k in enumerate(keys, 1):
        c = CATALOG[k]
        alias = f" / {c['alias']}" if c.get("alias") else ""
        print(f"    [{i}] {k}{alias:<8s}  bit={c['bitIndex']}  id={c['productId']}  {c['name']}")
        print(f"          {c['description']}")
        print(f"          {len(c['commands'])} commands, {len(c['sub_projects'])} sub-projects")

    raw = input("\n  勾選 (編號/代碼/逗號分隔, 'all'): ").strip() or "all"
    if raw.lower() == "all":
        selected = keys
    else:
        selected = []
        for tok in raw.split(","):
            tok = tok.strip().upper()
            if tok.isdigit():
                idx = int(tok) - 1
                if 0 <= idx < len(keys): selected.append(keys[idx])
            else:
                selected.extend(resolve_projects(tok))
        selected = list(dict.fromkeys(selected))

    if not selected: print("  沒選任何子系統。"); return

    md = input("  maxDevices [2]: ").strip() or "2"

    spec = ProductSpec(base, selected, version, name, int(md))
    print("\n  ============ 將要建立 ============")
    print(f"    產品       : {spec.product_name}")
    print(f"    版本       : {spec.version}")
    print(f"    根目錄     : {spec.root_path}")
    print(f"    子系統     : {spec.subsystems}")
    print(f"    Mask       : {spec.feature_mask}")
    total_cmds = (len(VIA_CORE_COMMANDS)
                  + sum(len(CATALOG[c]['commands']) for c in spec.subsystems)
                  + len(SNAPSHOT_COMMANDS))
    total_subp = sum(len(CATALOG[c]['sub_projects']) for c in spec.subsystems)
    print(f"    Commands   : {total_cmds}")
    print(f"    Sub-projects: {total_subp}")

    ans = input("\n  確認生成? [Y/n] ").strip().lower()
    if ans and ans != "y": print("  取消。"); return

    IntegratedForge(spec).forge()


def cmd_catalog():
    banner("VIA Package Forge — Catalog")
    print(f"  Root folder      : {ROOT_FOLDER_NAME}/")
    print(f"  Module layer     : {MODULE_LAYER}/")
    print(f"  Supportive layer : {SUPPORTIVE_LAYER}/")
    print(f"  Core commands    : {len(VIA_CORE_COMMANDS)}")
    print(f"  Snapshot commands: {len(SNAPSHOT_COMMANDS)}")
    print()
    for k, c in CATALOG.items():
        alias = f" (alias: {c['alias']})" if c.get('alias') else ""
        print(f"  {k}{alias}  bit={c['bitIndex']}  id={c['productId']}")
        print(f"    {c['name']}")
        print(f"    {c['description']}")
        print(f"    Sub-projects: {c['sub_projects']}")
        print(f"    Commands:")
        for cid, al, ds in c["commands"]:
            print(f"      {cid:28s}  {al:16s}  {ds}")
        print()


def cmd_forge(args):
    if args.spec:
        data = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        spec = ProductSpec(**data)
    else:
        if not args.base or not args.projects:
            print("✗ 需要 --base 與 --projects (或 --spec)"); sys.exit(2)
        spec = ProductSpec(
            base=args.base,
            subsystems=args.projects.split(","),
            version=args.version or "1.0.0",
            product_name=args.product_name or "VIA Custom Pack",
            max_devices=args.max_devices,
        )
    IntegratedForge(spec, dry_run=args.dry_run,
                    source_dir=Path(args.source_dir).resolve() if args.source_dir else None).forge()


def main():
    ap = argparse.ArgumentParser(prog="via_package_forge_v2",
        description="VIA Package Forge v2.0 — 整合版 (結構 + 指令 + 工具)")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("wizard", help="互動式 (推薦)")
    sub.add_parser("catalog", help="列出可用子系統")

    f = sub.add_parser("forge", help="CLI 一鍵")
    f.add_argument("--base")
    f.add_argument("--projects", help="例: VRN,VDF,VAP 或 all")
    f.add_argument("--version", default="1.0.0")
    f.add_argument("--product-name", default="VIA Custom Pack")
    f.add_argument("--max-devices", type=int, default=2)
    f.add_argument("--source-dir", help="HTML/Python 工具來源 (預設: 此腳本所在目錄)")
    f.add_argument("--spec")
    f.add_argument("--dry-run", action="store_true")

    args = ap.parse_args()
    if args.cmd == "wizard":  wizard()
    elif args.cmd == "catalog": cmd_catalog()
    elif args.cmd == "forge":   cmd_forge(args)
    else: ap.print_help()


if __name__ == "__main__":
    main()
