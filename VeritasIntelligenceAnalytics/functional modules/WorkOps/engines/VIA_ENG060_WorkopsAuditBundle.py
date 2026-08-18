# -*- coding: utf-8 -*-
r"""Veritas WorkOps 稽核包引擎 v0100(ENG-036)— 六機制研究第六項「audit bundle」落地

一鍵彙整全系統證據 → 帶 sha256 manifest 的稽核 zip,IT 送審/主管審查直接交件:
  自測報告 · 部署報告 · 結案快照(最新)· 準確度報告 · 路由統計/趨勢 · 備份清單
  · 決策 KPI · 節奏參數 · registry 帳本尾 50 筆 · 現場紅線掃描(即時跑;隔離區不列可執行)
  · 環境指紋(python 版本/引擎清單)
缺件誠實列 absent(絕不編造);全程唯讀,產物落 out/audit_bundle/。
動詞:build(預設)。via-workops auditpack。
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import hashlib, io, json, os, re, sys, zipfile
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
WORKOPS = HERE.parent
OUT = WORKOPS / "out"
VIAROOT = WORKOPS.parent.parent
BUNDLE_DIR = OUT / "audit_bundle"


def sha16(b):
    return hashlib.sha256(b).hexdigest()[:16]


def redline_scan():
    """現場紅線掃描:WorkOps 樹 ps1/py — 去 <#…#> 區塊與行內註解後,Send 呼叫零容忍。"""
    hits = []
    n = 0
    rx = re.compile("\\." + "Send" + "\\s*\\(")   # 動態組樣式,免自身字面誤中
    for ext in ("*.ps1", "*.py"):
        for f in WORKOPS.rglob(ext):
            if ".venv" in str(f) or "__pycache__" in str(f) or "quarantine" in str(f):
                continue
            n += 1
            try:
                t = re.sub(r"<#.*?#>", "", f.read_text(encoding="utf-8", errors="replace"), flags=re.S)
            except Exception:
                continue
            for i, ln in enumerate(t.splitlines(), 1):
                code = ln.split("#", 1)[0]          # 去行內/整行註解(ps1 與 py 同記號)
                if rx.search(code):
                    hits.append({"file": str(f.relative_to(WORKOPS)), "line": i})
    return {"scanned": n, "hits": hits, "gate": "PASS" if not hits else "FAIL"}


def newest(pattern, root):
    c = sorted(root.glob(pattern))
    return c[-1] if c else None


def build():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)
    zpath = BUNDLE_DIR / ("VIA_Audit_Bundle_%s.zip" % ts)

    closure_dir = VIAROOT / "VIA_Reports" / "closure"
    sources = [
        ("selftest_report.json", OUT / "selftest_report.json", "全鏈自測(ENG-032)"),
        ("bootstrap_report.json", OUT / "bootstrap_report.json", "一鍵部署報告"),
        ("accuracy_report.json", OUT / "accuracy_report.json", "Gold Set 實測(ENG-030)"),
        ("wop_route_stats.json", OUT / "wop_route_stats.json", "路由分佈"),
        ("wop_route_history.jsonl", OUT / "wop_route_history.jsonl", "L8 趨勢歷史"),
        ("decision_log.csv", OUT / "decision_log.csv", "決策 KPI(ENG-027)"),
        ("watchtower_params.json", HERE / "watchtower_params.json", "節奏參數"),
        ("closure_snapshot.json", newest("VIA_Trinity_Closure_Snapshot_*.json", closure_dir) if closure_dir.exists() else None, "三系統結案快照(最新)"),
        ("backup_newest.zip.name", newest("*.zip", OUT / "backups") if (OUT / "backups").exists() else None, "最新側車備份(僅記名+sha,不重複打包)"),
    ]
    manifest = {"ts": datetime.now().isoformat(timespec="seconds"), "tool": "workops_audit_bundle v0100",
                "policy": "唯讀彙整;缺件誠實 absent;紅線=現場即時掃描", "files": [], "absent": []}
    zf = zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED)
    for name, p, role in sources:
        if p is None or not Path(p).exists():
            manifest["absent"].append({"name": name, "role": role})
            print("  [absent] %-26s %s" % (name, role))
            continue
        b = Path(p).read_bytes()
        if name == "backup_newest.zip.name":
            entry = {"note": "備份不重複入包(避免包中包)", "backup_file": Path(p).name,
                     "sha256_16": sha16(b), "size": len(b)}
            zf.writestr("backup_pointer.json", json.dumps(entry, ensure_ascii=False, indent=1))
            manifest["files"].append({"name": "backup_pointer.json", "role": role, "sha256_16": sha16(json.dumps(entry, ensure_ascii=False, indent=1).encode())})
        else:
            zf.writestr(name, b)
            manifest["files"].append({"name": name, "role": role, "sha256_16": sha16(b), "size": len(b)})
        print("  [in]     %-26s %s" % (name, role))

    rl = redline_scan()
    zf.writestr("redline_scan.json", json.dumps(rl, ensure_ascii=False, indent=1))
    manifest["files"].append({"name": "redline_scan.json", "role": "現場紅線掃描(.Send 零容忍)",
                              "gate": rl["gate"], "scanned": rl["scanned"]})
    print("  [scan]   redline_scan.json          %d 檔掃描 · %s" % (rl["scanned"], rl["gate"]))

    reg_p = VIAROOT / "supportive modules" / "registry" / "VIA_AutoCode_Registry_v0100.json"
    if reg_p.exists():
        try:
            reg = json.loads(reg_p.read_text(encoding="utf-8"))
            tail = {"components_total": len(reg.get("components", {})), "ledger_tail_50": reg.get("ledger", [])[-50:]}
            b = json.dumps(tail, ensure_ascii=False, indent=1).encode()
            zf.writestr("registry_ledger_tail.json", b)
            manifest["files"].append({"name": "registry_ledger_tail.json", "role": "編號帳本尾 50 筆", "sha256_16": sha16(b)})
            print("  [in]     registry_ledger_tail.json  帳本 %d 筆取尾 50" % len(reg.get("ledger", [])))
        except Exception as e:
            manifest["absent"].append({"name": "registry_ledger_tail.json", "role": "帳本讀取失敗:%s" % e})

    env = {"python": sys.version.split()[0], "platform": sys.platform,
           "engines_present": sorted(p.name for p in HERE.glob("workops_*.py"))}
    b = json.dumps(env, ensure_ascii=False, indent=1).encode()
    zf.writestr("environment.json", b)
    manifest["files"].append({"name": "environment.json", "role": "環境指紋", "sha256_16": sha16(b)})

    mb = json.dumps(manifest, ensure_ascii=False, indent=1).encode()
    zf.writestr("MANIFEST.json", mb)
    zf.close()
    zsha = sha16(zpath.read_bytes())
    gate = "PASS" if rl["gate"] == "PASS" else "FAIL"
    print("[稽核包] %d 件證據 + %d 件缺席(誠實列示)→ %s" % (len(manifest["files"]), len(manifest["absent"]), zpath.name))
    print("[雜湊] zip sha256 前16 = %s" % zsha)
    print(json.dumps({"gate": gate, "bundle": str(zpath), "sha256_16": zsha,
                      "files": len(manifest["files"]), "absent": len(manifest["absent"])}, ensure_ascii=False))
    print("[交件] IT 送審附件:本 zip + docs/IT_Approval_Letter_VeritasWorkOps_v0100.md;主管審查:zip 內 MANIFEST.json 為目錄")
    return 0 if gate == "PASS" else 1


if __name__ == "__main__":
    sys.exit(build())
