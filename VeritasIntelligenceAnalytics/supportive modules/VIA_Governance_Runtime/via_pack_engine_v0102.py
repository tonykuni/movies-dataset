# =====================================================================================
# VIA Pack Engine v0102 — 子系統獨立打包器(產品號 + 單機綁定 + 每包自帶 U/I)
# (v0101 版本前送:Launch 參數改 PS 原生陣列 — 根除 Split(" ") 對引號/含空白路徑的
#   碎裂 bug(cge --workdir 受害);entry_args 規格改列表形,%WORKDIR% 以 $WorkDir 變數注入)
# (v0100 版本前送:[4] 每包生成 Porcelain 封面 UI index.html — 產品/綁定/manifest 矩陣/
#   啟動指引/報告出口;Launch 綁定驗證通過後設 VIA_HOME=包根 並於引擎跑完自動開 UI)
# [1] 產品號獨一無二:AutoCoder 註冊中心給序號(PKG-00N,冪等)+ 內容 manifest SHA8
#     => PRODUCT_ID = PKG-00N-<SUBSYS>-<YYYYMMDD>-<SHA8>(序號唯一 × 內容定址雙保險)
# [2] 單機綁定(NODE_LOCKED_1_HOST):Install 以 MachineGuid+電腦名雜湊成主機指紋寫入
#     HOST_BINDING_LOCK;Launch 每次重算比對,不符=fail-closed 拒跑(誠實訊息,不靜默)
# [3] 驗證閘 fail-closed:py 檔全數 py_compile 過閘才成包;逐檔 SHA256 入 manifest
# 治理:唯讀取材、正本不動;產出 run-local VIA_Reports/packages/(發佈時取 zip)
# 用法:py via_pack_engine_v0100.py <cge|mega|bridge|audit|flow|if|vmt|tools> [--no-zip]
# =====================================================================================
import os, sys, json, glob, gzip, shutil, hashlib, subprocess, datetime as dt

VERSION = "v0102"
ROOT = os.environ.get("VIA_HOME") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUTOCODER = os.path.join(ROOT, "supportive modules", "registry", "via_autocoder_engine_v0100.py")

# ---------------------------------------------------------------- 打包規格(可增減)
SPECS = {
    "cge":    {"name": "CentralGovernance", "seal": "治",
               "files": ["supportive modules/VIA_Central_Governance/VIA_CentralGovernanceEngine_v0401.py",
                          "supportive modules/VIA_Central_Governance/confirmations_proposed_20260805.jsonl"],
               "globs": ["supportive modules/VIA_Central_Governance/tw_source_snapshots/*"],
               "entry": "VIA_CentralGovernanceEngine_v0401.py", "entry_args": ["--workdir", "$WorkDir"],
               "reports": [("%WORKDIR%/VIA_CentralGovernance.html", "中央治理 TAB 儀表板(workdir 內)")]},
    "mega":   {"name": "MegaAuditor", "seal": "核",
               "files": ["supportive modules/VIA_Governance_Runtime/via_mega_engine_v0106.py"],
               "globs": [], "entry": "via_mega_engine_v0106.py", "entry_args": ["--no-open"],
               "reports": [("VIA_Reports/VIA_MegaMatrix.html", "Mega 三輪全景 Matrix")]},
    "bridge": {"name": "CommandBridge", "seal": "橋",
               "files": ["supportive modules/VIA_Governance_Runtime/via_bridge_engine_v0100.py"],
               "globs": [], "entry": "via_bridge_engine_v0100.py", "entry_args": ["--no-open"],
               "reports": [("VIA_Reports/VIA_CommandBridge.html", "Command Bridge 狀態矩陣")]},
    "audit":  {"name": "AuditToolkit", "seal": "稽",
               "files": ["supportive modules/VIA_Governance_Runtime/via_mega_engine_v0106.py",
                          "supportive modules/VIA_Governance_Runtime/via_bridge_engine_v0100.py"],
               "globs": [], "entry": "via_bridge_engine_v0100.py", "entry_args": ["--no-open"],
               "reports": [("VIA_Reports/VIA_CommandBridge.html", "Command Bridge 狀態矩陣"), ("VIA_Reports/VIA_MegaMatrix.html", "Mega 三輪全景 Matrix")]},
    "flow":   {"name": "FlowSystem", "seal": "湧",
               "files": [], "globs": ["supportive modules/VIA_FlowSystem/*"],
               "entry": "VIA_FlowSystem_OneShot.py", "entry_args": [],
               "reports": [("payload/VIA_FlowSystem_UI.html", "FlowSystem 五鏡頭 UI"), ("payload/VIA_FIS_Validation_v3_Matrix.html", "FIS 驗證 Matrix(隨包)")]},
    "if":     {"name": "IndustryForecast", "seal": "預",
               "files": [], "globs": ["supportive modules/VIA_IF_Engine/*"],
               "entry": "via_if_engine.py", "entry_args": ["--selftest"],
               "reports": [("if_out", "IF append-only 輸出(RYG/coverage,跑正式掃描後)")]},
    "vmt":    {"name": "MailTracker", "seal": "郵",
               "files": ["supportive modules/VMT_SuperBOM/via_master_engine_v0102.py",
                          "supportive modules/VMT_SuperBOM/via_master_params.json",
                          "supportive modules/VMT_SuperBOM/convergence_params.json",
                          "supportive modules/VMT_SuperBOM/survey_pack_psu.json"],
               "globs": ["supportive modules/VMT_SuperBOM/vmt_*.py",
                          "supportive modules/VMT_SuperBOM/VIA_SuperBOM_ContentParser_v0100.py"],
               "entry": "via_master_engine_v0102.py", "entry_args": ["--no-open"],
               "reports": [("%WORKDIR%/reports/MasterRun.html", "VMT MasterRun 總覽(VMT_ROOT 內)")]},
    "tools":  {"name": "SupportTools", "seal": "工",
               "files": ["supportive modules/VIA_EnvManager.py",
                          "supportive modules/registry/via_autocoder_engine_v0100.py",
                          "supportive modules/ssot/via_synonym_engine_v0100.py",
                          "supportive modules/ssot/VIA_Synonym_Seed_v0100.json"],
               "globs": [], "entry": "VIA_EnvManager.py", "entry_args": ["scan"],
               "reports": [("payload/_via_envmanager_output/VIA_EnvManager_Report.html", "EnvManager 健康報告")]},
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
$env:VIA_HOME = $Here
$entryArgs = @(@PSARGS@)
Push-Location (Join-Path $Here "payload")
try { if ($entryArgs.Count) { & py "@ENTRY@" @entryArgs } else { & py "@ENTRY@" } }
finally { Pop-Location }
$ui = Join-Path $Here "index.html"
if (Test-Path -LiteralPath $ui) { Start-Process $ui | Out-Null; Write-Host "[U/I] 封面 UI 已開啟(報告出口見頁內)" -ForegroundColor Green }
'''


# ---------------------------------------------------------------- [4] 封面 U/I(Porcelain)
def build_index_html(spec, product_id, sha8, arts, out_dir):
    def esc(x): return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    rows = "".join("<tr><td class='mono'>%s</td><td class='mono'>%d</td><td class='mono'>%s</td></tr>"
                   % (esc(a["path"]), a["bytes"], a["sha256"][:12]) for a in arts)
    reps = spec.get("reports", [])
    rep_rows = "".join("<tr><td><a href='%s' target='_blank' class='mono'>%s</a></td><td>%s</td></tr>"
                       % (esc(p), esc(p), esc(d) + "(首跑 Launch 後生成)") for p, d in reps) or                "<tr><td colspan='2'>本包為 CLI 工具組,輸出見終端機與 payload 目錄</td></tr>"
    page = ("<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'><title>" + esc(product_id) + "</title>"
      "<link href='https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Noto+Serif+TC:wght@500;600&display=swap' rel='stylesheet'><style>"
      ":root{--ink:#1b1a17;--mut:#6b6860;--mut2:#9aa5a1;--hair:#dcdad3;--seal:#9e2b25;--teal:#3d8f8f;"
      "--serif:'Cormorant Garamond',Georgia,serif;--cjk:'Noto Serif TC','Noto Serif CJK TC','Songti TC','PMingLiU',serif;"
      "--mono:'SFMono-Regular',Consolas,'Liberation Mono',monospace}"
      "*{box-sizing:border-box;margin:0;padding:0}body{background:#f0efeb;color:var(--ink);"
      "font-family:'Microsoft JhengHei','Segoe UI',system-ui,sans-serif;padding:26px;max-width:960px;margin:0 auto}"
      ".chip{display:inline-block;padding:2px 7px;background:var(--ink);color:#fbfaf7;font:700 9px var(--mono);letter-spacing:.14em;margin-bottom:8px}"
      "header{display:flex;align-items:center;border-bottom:3px solid var(--seal);padding-bottom:14px}"
      ".seal{width:44px;height:44px;background:var(--seal);color:#fbfaf7;display:flex;align-items:center;justify-content:center;font-family:var(--cjk);font-size:24px;border-radius:5px;margin-right:14px}"
      "h1{font:500 20px/1.2 var(--serif);letter-spacing:.055em}.wmcjk{font:600 9.5px var(--cjk);letter-spacing:.22em;color:var(--teal);margin-top:2px}"
      ".sub{font:10.5px var(--mono);color:var(--mut);margin-top:4px}"
      ".strip{height:4px;background:linear-gradient(90deg,#24457f 0 16.6%,#3c6660 0 33.3%,#4a6b45 0 50%,#8a7340 0 66.6%,#5e5540 0 83.3%,#3f4f78 0 100%);margin:13px 0 18px;border-radius:2px}"
      "h2{font:700 11px var(--mono);letter-spacing:2px;color:var(--mut);margin:20px 0 9px;text-transform:uppercase}"
      ".note{background:#fdfbf6;border-left:4px solid var(--teal);padding:10px 14px;font-size:12px;border-radius:3px;margin:8px 0}"
      ".warn{background:#fdfbf6;border-left:4px solid var(--seal);padding:10px 14px;font-size:12px;border-radius:3px;margin:8px 0}"
      "table{width:100%;border-collapse:collapse;background:#fbfaf7;border:1px solid var(--hair);table-layout:fixed}"
      "th{font:700 10px var(--mono);text-align:left;padding:8px 10px;border-bottom:1px solid var(--hair);color:var(--mut)}"
      "td{font-size:11.5px;padding:7px 10px;border-bottom:1px solid var(--hair);word-wrap:break-word;overflow-wrap:anywhere}"
      "tr:last-child td{border-bottom:none}.mono{font-family:var(--mono);font-size:10.5px}"
      ".cmd{display:inline-block;font:700 12px var(--mono);background:var(--ink);color:#fbfaf7;border-radius:4px;padding:6px 14px;margin:3px 6px 3px 0}"
      "a{color:#24457f}footer{margin-top:24px;font:10px var(--mono);color:var(--mut2)}</style></head><body>"
      "<span class='chip'>" + esc(product_id) + "</span>"
      "<header><div class='seal'>" + esc(spec["seal"]) + "</div><div>"
      "<h1>VIA " + esc(spec["name"].upper()) + " — 獨立子系統包</h1>"
      "<div class='wmcjk'>維里塔斯 · 單機綁定 · 內容定址</div>"
      "<div class='sub'>content_sha8 " + esc(sha8) + " · NODE_LOCKED_1_HOST · Porcelain(DesignLock v0101)</div></div></header>"
      "<div class='strip'></div>"
      "<h2>啟動</h2>"
      "<div><span class='cmd'>1. .\\Install-" + esc(spec["name"]) + ".ps1</span> 綁定本機(僅首次)"
      "<br><span class='cmd'>2. .\\Launch-" + esc(spec["name"]) + ".ps1</span> 驗證指紋 → 執行引擎 → 自動回開本頁</div>"
      "<div class='warn'>本包綁定單一主機:Install 以 MachineGuid+電腦名+產品號之 SHA256 指紋落鎖(只存雜湊);"
      "他機 Launch 一律 fail-closed 拒跑。移轉需發行方重新出包。</div>"
      "<h2>報告出口</h2><table><tr><th style='width:52%'>出口</th><th>說明</th></tr>" + rep_rows + "</table>"
      "<h2>內容 Manifest(逐檔 SHA256)</h2><table><tr><th style='width:46%'>artifact</th>"
      "<th style='width:90px'>bytes</th><th>sha12</th></tr>" + rows + "</table>"
      "<div class='note'>完整雜湊見 PACKAGE_VALIDATION_Manifest.json;py_compile 閘全過方成包(fail-closed)。</div>"
      "<footer>via_pack_engine " + VERSION + " | 產品號=AutoCoder 序號 × 內容 SHA8(冪等) | 印章 " + esc(spec["seal"]) + "</footer></body></html>")
    open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8").write(page)

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
        psargs = ", ".join(a if a.startswith("$") else '"%s"' % a for a in spec["entry_args"])
        txt = (tmpl.replace("@NAME@", spec["name"]).replace("@PRODUCT_ID@", product_id)
                   .replace("@ENTRY@", spec["entry"]).replace("@PSARGS@", psargs))
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
    build_index_html(spec, product_id, sha8, arts, out_dir)
    bar(80, "manifest + 綁定雙入口 + 封面 U/I 完成")
    zip_path = ""
    if "--no-zip" not in sys.argv:
        zip_path = shutil.make_archive(out_dir, "zip", os.path.join(ROOT, "VIA_Reports", "packages"), product_id)
    bar(100, "成包")
    print()
    print("[產品號] %s(印章 %s)" % (product_id, spec["seal"]))
    print("[內容] payload %d 檔 · manifest SHA256 逐檔 · content_sha8=%s" % (len(files), sha8))
    print("[綁定] NODE_LOCKED_1_HOST:對方主機跑 Install-%s.ps1 綁定 → Launch-%s.ps1 啟動" % (spec["name"], spec["name"]))
    print("[U/I ] index.html 封面(Launch 跑完自動開)")
    print("[產出] %s" % out_dir)
    if zip_path: print("[ZIP ] %s" % zip_path)
    return 0

if __name__ == "__main__":
    sys.exit(main())
