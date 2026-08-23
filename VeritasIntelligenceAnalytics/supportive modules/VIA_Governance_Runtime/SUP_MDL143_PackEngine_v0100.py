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
# =====================================================================================
# VIA Pack Engine v0100 — 子系統獨立打包器(產品號 + 單機綁定)
# [1] 產品號獨一無二:AutoCoder 註冊中心給序號(PKG-00N,冪等)+ 內容 manifest SHA8
#     => PRODUCT_ID = PKG-00N-<SUBSYS>-<YYYYMMDD>-<SHA8>(序號唯一 × 內容定址雙保險)
# [2] 單機綁定(NODE_LOCKED_1_HOST):Install 以 MachineGuid+電腦名雜湊成主機指紋寫入
#     HOST_BINDING_LOCK;Launch 每次重算比對,不符=fail-closed 拒跑(誠實訊息,不靜默)
# [3] 驗證閘 fail-closed:py 檔全數 py_compile 過閘才成包;逐檔 SHA256 入 manifest
# 治理:唯讀取材、正本不動;產出 run-local VIA_Reports/packages/(發佈時取 zip)
# 用法:py via_pack_engine_v0100.py <cge|mega|bridge|audit|flow|if|vmt|tools> [--no-zip]
# =====================================================================================
import os, sys, json, glob, gzip, shutil, hashlib, subprocess, datetime as dt

VERSION = "v0100"
ROOT = os.environ.get("VIA_HOME") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUTOCODER = os.path.join(ROOT, "supportive modules", "registry", "CGC_MDL043_AutocoderEngine_v0100.py")

# ---------------------------------------------------------------- 打包規格(可增減)
SPECS = {
    "cge":    {"name": "CentralGovernance", "seal": "治",
               "files": ["supportive modules/VIA_Central_Governance/CGC_MDL001_CentralGovernanceEngine_v0401.py",
                          "supportive modules/VIA_Central_Governance/confirmations_proposed_20260805.jsonl"],
               "globs": ["supportive modules/VIA_Central_Governance/tw_source_snapshots/*"],
               "entry": "CGC_MDL001_CentralGovernanceEngine_v0401.py", "entry_args": "--workdir \"%WORKDIR%\""},
    "mega":   {"name": "MegaAuditor", "seal": "核",
               "files": ["supportive modules/VIA_Governance_Runtime/SUP_MDL142_MegaEngine_v0106.py"],
               "globs": [], "entry": "SUP_MDL142_MegaEngine_v0106.py", "entry_args": "--no-open"},
    "bridge": {"name": "CommandBridge", "seal": "橋",
               "files": ["supportive modules/VIA_Governance_Runtime/SUP_MDL140_BridgeEngine_v0100.py"],
               "globs": [], "entry": "SUP_MDL140_BridgeEngine_v0100.py", "entry_args": "--no-open"},
    "audit":  {"name": "AuditToolkit", "seal": "稽",
               "files": ["supportive modules/VIA_Governance_Runtime/SUP_MDL142_MegaEngine_v0106.py",
                          "supportive modules/VIA_Governance_Runtime/SUP_MDL140_BridgeEngine_v0100.py"],
               "globs": [], "entry": "SUP_MDL140_BridgeEngine_v0100.py", "entry_args": "--no-open"},
    "flow":   {"name": "FlowSystem", "seal": "湧",
               "files": [], "globs": ["supportive modules/VIA_FlowSystem/*"],
               "entry": "FLOW_MDL003_FlowSystemOneShot.py", "entry_args": ""},
    "if":     {"name": "IndustryForecast", "seal": "預",
               "files": [], "globs": ["supportive modules/VIA_IF_Engine/*"],
               "entry": "SUP_MDL144_IfEngine.py", "entry_args": "--selftest"},
    "vmt":    {"name": "MailTracker", "seal": "郵",
               "files": ["supportive modules/VMT_SuperBOM/VIA_ENG021_MasterEngine_v0102.py",
                          "supportive modules/VMT_SuperBOM/via_master_params.json",
                          "supportive modules/VMT_SuperBOM/convergence_params.json",
                          "supportive modules/VMT_SuperBOM/survey_pack_psu.json"],
               "globs": ["supportive modules/VMT_SuperBOM/vmt_*.py",
                          "supportive modules/VMT_SuperBOM/VIA_ENG020_SuperBOMContentParser_v0100.py"],
               "entry": "VIA_ENG021_MasterEngine_v0102.py", "entry_args": "--no-open"},
    "tools":  {"name": "SupportTools", "seal": "工",
               "files": ["supportive modules/VIA_EnvManager.py",
                          "supportive modules/registry/CGC_MDL043_AutocoderEngine_v0100.py",
                          "supportive modules/ssot/via_synonym_engine_v0100.py",
                          "supportive modules/ssot/VIA_Synonym_Seed_v0100.json"],
               "globs": [], "entry": "VIA_EnvManager.py", "entry_args": "scan"},
}

def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def bar(pct, msg):
    n = int(pct / 5)
    sys.stdout.write("\r[%-20s] %3d%%  %-46s" % ("#" * n, pct, msg[:46])); sys.stdout.flush()

# ---------------------------------------------------------------- 產品號
def issue_product_seq(component):
    try:
        subprocess.run([sys.executable, AUTOCODER, "--register", "打包產品", "PKG", "3"],
                       capture_output=True, text=True, timeout=30)
    except Exception:
        pass
    r = subprocess.run([sys.executable, AUTOCODER, "打包產品", component],
                       capture_output=True, text=True, timeout=30)
    out = (r.stdout + r.stderr)
    for tok in out.replace("\n", " ").split():
        if tok.startswith("PKG-"):
            return tok.strip("():,")
    return "PKG-X%s" % dt.datetime.now().strftime("%H%M%S")

# ---------------------------------------------------------------- PS 樣板(單機綁定)
INSTALL_PS = r'''#requires -Version 7.0
# Install-@NAME@.ps1 — @PRODUCT_ID@ 單機綁定安裝(NODE_LOCKED_1_HOST)
# 綁定=MachineGuid+電腦名+產品號 之 SHA256 指紋;只存雜湊不存原值;重綁他機=fail-closed 拒絕
$ErrorActionPreference = "Continue"
$Here = $PSScriptRoot
$Lock = Join-Path $Here "HOST_BINDING_LOCK.json"
$guid = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Cryptography" -Name MachineGuid -ErrorAction SilentlyContinue).MachineGuid
if (-not $guid) { $guid = "NOGUID" }
$raw = "{0}|{1}|@PRODUCT_ID@" -f $guid, $env:COMPUTERNAME
$fp = [BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($raw))).Replace("-", "").ToLower()
if (Test-Path -LiteralPath $Lock) {
    $old = Get-Content -LiteralPath $Lock -Raw | ConvertFrom-Json
    if ($old.fingerprint -eq $fp) { Write-Host "[OK] 本機已綁定(@PRODUCT_ID@ @ $($old.computer))— 冪等通過" -ForegroundColor Green; return }
    Write-Host "[FAIL-CLOSED] 本產品已綁定其他主機($($old.computer) @ $($old.bound_at))— 拒絕重綁。如需移轉請聯繫發行方作廢舊綁定。" -ForegroundColor Red
    return
}
$obj = [ordered]@{ product_id = "@PRODUCT_ID@"; policy = "NODE_LOCKED_1_HOST"; computer = $env:COMPUTERNAME
                   bound_at = (Get-Date).ToString("s"); fingerprint = $fp }
$obj | ConvertTo-Json | Set-Content -LiteralPath $Lock -Encoding utf8
Write-Host "[OK] 綁定完成:@PRODUCT_ID@ -> $($env:COMPUTERNAME)(指紋 $($fp.Substring(0,12))…)" -ForegroundColor Green
Write-Host "[次步] .\Launch-@NAME@.ps1 啟動(每次啟動自動驗證本機指紋)"
'''

LAUNCH_PS = r'''#requires -Version 7.0
# Launch-@NAME@.ps1 — @PRODUCT_ID@ 啟動器(先驗單機綁定,不符 fail-closed 拒跑)
param([string]$WorkDir = ($env:VMT_ROOT ?? "C:\VIA\VeritasMailTracker"))
$ErrorActionPreference = "Continue"
$Here = $PSScriptRoot
$Lock = Join-Path $Here "HOST_BINDING_LOCK.json"
if (-not (Test-Path -LiteralPath $Lock)) { Write-Host "[FAIL-CLOSED] 尚未綁定 — 先執行 .\Install-@NAME@.ps1" -ForegroundColor Red; return }
$b = Get-Content -LiteralPath $Lock -Raw | ConvertFrom-Json
$guid = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Cryptography" -Name MachineGuid -ErrorAction SilentlyContinue).MachineGuid
if (-not $guid) { $guid = "NOGUID" }
$raw = "{0}|{1}|@PRODUCT_ID@" -f $guid, $env:COMPUTERNAME
$fp = [BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($raw))).Replace("-", "").ToLower()
if ($fp -ne $b.fingerprint) {
    Write-Host "[FAIL-CLOSED] 主機指紋不符 — @PRODUCT_ID@ 綁定於 $($b.computer),本機拒跑(NODE_LOCKED_1_HOST)" -ForegroundColor Red; return
}
Write-Host "[OK] 綁定驗證通過($($b.computer))— 啟動 @ENTRY@" -ForegroundColor Green
$args_ = "@ENTRY_ARGS@".Replace("%WORKDIR%", $WorkDir)
Push-Location (Join-Path $Here "payload")
try { if ($args_.Trim()) { & py "@ENTRY@" $args_.Split(" ") } else { & py "@ENTRY@" } }
finally { Pop-Location }
'''

# ---------------------------------------------------------------- 主流程
def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not argv or argv[0] not in SPECS:
        print("用法: py via_pack_engine_%s.py <%s> [--no-zip]" % (VERSION, "|".join(SPECS)))
        return 1
    key = argv[0]; spec = SPECS[key]
    print("=" * 62); print("  VIA Pack Engine %s  |  獨立打包 · 產品號 · 單機綁定" % VERSION); print("=" * 62)
    files = list(spec["files"])
    for g in spec["globs"]:
        files += [os.path.relpath(p, ROOT).replace("\\", "/") for p in sorted(glob.glob(os.path.join(ROOT, g))) if os.path.isfile(p)]
    files = [f for f in files if os.path.exists(os.path.join(ROOT, f))]
    if not files:
        print("[FAIL-CLOSED] 規格內無可打包檔"); return 1
    bar(10, "取材 %d 檔" % len(files))
    # 驗證閘:py 全數 py_compile(fail-closed)
    import py_compile, warnings
    for f in files:
        if f.endswith(".py"):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    py_compile.compile(os.path.join(ROOT, f), doraise=True)
            except Exception as e:
                print("\n[FAIL-CLOSED] py_compile 未過:%s(%s)— 中止不成包" % (f, str(e)[:80])); return 1
    bar(30, "驗證閘 py_compile 全過")
    # 內容定址雜湊 + 產品號
    content = "".join(sorted("%s:%s" % (f, sha256(os.path.join(ROOT, f))) for f in files))
    sha8 = hashlib.sha256(content.encode()).hexdigest()[:8]
    seq = issue_product_seq("VIA_Pack_%s" % spec["name"])
    product_id = "%s-%s-%s-%s" % (seq, key.upper(), dt.datetime.now().strftime("%Y%m%d"), sha8)
    bar(45, "產品號 " + product_id)
    # 組包
    out_dir = os.path.join(ROOT, "VIA_Reports", "packages", product_id)
    pay = os.path.join(out_dir, "payload")
    if os.path.exists(out_dir): shutil.rmtree(out_dir)
    os.makedirs(pay)
    arts = []
    for f in files:
        dst = os.path.join(pay, os.path.basename(f))
        shutil.copy2(os.path.join(ROOT, f), dst)
        arts.append({"path": "payload/" + os.path.basename(f), "bytes": os.path.getsize(dst), "sha256": sha256(dst)})
    bar(65, "payload %d 檔落位" % len(arts))
    for tmpl, fname in ((INSTALL_PS, "Install-%s.ps1" % spec["name"]), (LAUNCH_PS, "Launch-%s.ps1" % spec["name"])):
        txt = (tmpl.replace("@NAME@", spec["name"]).replace("@PRODUCT_ID@", product_id)
                   .replace("@ENTRY@", spec["entry"]).replace("@ENTRY_ARGS@", spec["entry_args"]))
        p = os.path.join(out_dir, fname)
        open(p, "w", encoding="utf-8", newline="\r\n").write(txt)
        arts.append({"path": fname, "bytes": os.path.getsize(p), "sha256": sha256(p)})
    manifest = {"schema_id": "VIA_Package_Manifest", "engine": "via_pack_engine_" + VERSION,
                "product_id": product_id, "subsystem": key, "name": spec["name"], "seal": spec["seal"],
                "created": dt.datetime.now().isoformat(), "binding_policy": "NODE_LOCKED_1_HOST",
                "binding_note": "Install 綁定主機指紋(MachineGuid+電腦名+產品號之 SHA256,只存雜湊);Launch 每次驗證,不符 fail-closed 拒跑",
                "content_sha8": sha8, "gates": {"py_compile": "ALL PASS", "sha256": "per-artifact"},
                "artifacts": arts}
    json.dump(manifest, open(os.path.join(out_dir, "PACKAGE_VALIDATION_Manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    bar(80, "manifest + 綁定雙入口完成")
    zip_path = ""
    if "--no-zip" not in sys.argv:
        zip_path = shutil.make_archive(out_dir, "zip", os.path.join(ROOT, "VIA_Reports", "packages"), product_id)
    bar(100, "成包")
    print()
    print("[產品號] %s(印章 %s)" % (product_id, spec["seal"]))
    print("[內容] payload %d 檔 · manifest SHA256 逐檔 · content_sha8=%s" % (len(files), sha8))
    print("[綁定] NODE_LOCKED_1_HOST:對方主機跑 Install-%s.ps1 綁定 → Launch-%s.ps1 啟動" % (spec["name"], spec["name"]))
    print("[產出] %s" % out_dir)
    if zip_path: print("[ZIP ] %s" % zip_path)
    return 0

if __name__ == "__main__":
    sys.exit(main())
