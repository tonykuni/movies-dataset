# -*- coding: utf-8 -*-
r"""WorkOps 備份/驗證/還原到暫存 v0100(ENG-031)— v0200 RC 驗收 L06 安全車道補強落地

操作員令(2026/08/09 整合補強):RC 驗收 Lane 06 = backup → SHA verify →
restore-to-staging(STAGED_REVIEW_REQUIRED,canonical_mutation=false)。
本引擎把該安全車道落到 run-local 線,保護 side-car 帳本正本(編號/命名/互鏈/
學習記憶/決策/回覆事實流)與參數 JSON。

動詞:
  backup           → out/backups/WorkOps_Backup_<ts>.zip + 同名 .sha256 + 內嵌 manifest
  verify <zip>     → 重算 SHA-256 對 .sha256 檔;逐檔對內嵌 manifest — PASS/FAIL
  restore <zip>    → 只解壓到 out/restore_staging/<ts>/ — 絕不覆寫正本
                     (gate=STAGED_REVIEW_REQUIRED · canonical_mutation=false;
                      過目後由人自行取用 — 與 RC 同一安全語義)
治理:token/秘密不入備份(本線本無);只增不減(備份不輪刪,操作員自管);誠實逐檔回報。
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
import argparse, hashlib, io, json, sys, zipfile
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE  = Path(__file__).resolve().parent            # engines/
WOPS  = HERE.parent
OUT   = WOPS / "out"
BK    = OUT / "backups"
STAGE = OUT / "restore_staging"

# 正本清單(存在才收;out/ 側車 + engines/ 參數)
CANON = [
    OUT / "workops_id_ledger.json", OUT / "workops_naming.json", OUT / "thr_case_map.json",
    OUT / "wop_registry.json", OUT / "wop_confirmations.jsonl",
    OUT / "reply_events.jsonl", OUT / "reply_status.json",
    OUT / "decision_log.db", OUT / "decision_log.csv",
    OUT / "gold_set.csv", OUT / "gold_set_template.csv", OUT / "accuracy_report.json",
    HERE / "identifier_params.json", HERE / "watchtower_params.json",
    HERE / "reply_parser_params.json", HERE / "product_code_map.json",
    HERE / "org_lexicon.json", HERE / "holidays_tw.txt",
    HERE / "bulk_senders.txt", HERE / "domain_dict.txt",
]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_backup():
    files = [p for p in CANON if p.exists()]
    if not files:
        print("[FAIL] 無正本可備(out/ 尚空)— 先跑 via-workops all")
        return 1
    BK.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    zp = BK / ("WorkOps_Backup_%s.zip" % ts)
    manifest = {"ts": ts, "files": []}
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            arc = str(p.relative_to(WOPS)).replace("\\", "/")
            z.write(p, arc)
            manifest["files"].append({"path": arc, "sha256": sha256(p), "bytes": p.stat().st_size})
        z.writestr("BACKUP_MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=1))
    digest = sha256(zp)
    (zp.with_suffix(".zip.sha256")).write_text(digest + "  " + zp.name + "\n", encoding="utf-8")
    print(json.dumps({"gate": "PASS", "backup": str(zp), "files": len(files), "sha256": digest},
                     ensure_ascii=False))
    print("[備份] %d 檔 → %s(sha256 前16 %s)" % (len(files), zp.name, digest[:16]))
    return 0


def cmd_verify(zippath):
    zp = Path(zippath) if zippath else None
    if zp is None or not zp.exists():
        cands = sorted(BK.glob("WorkOps_Backup_*.zip"))
        if not cands:
            print("[FAIL] 無備份可驗:%s" % (zippath or BK))
            return 1
        zp = cands[-1]
    sfile = zp.with_suffix(".zip.sha256")
    digest = sha256(zp)
    if sfile.exists():
        want = sfile.read_text(encoding="utf-8").split()[0].strip()
        if want != digest:
            print(json.dumps({"gate": "FAIL", "reason": "zip sha mismatch", "want": want, "got": digest}))
            return 1
    n_bad = 0
    with zipfile.ZipFile(zp) as z:
        man = json.loads(z.read("BACKUP_MANIFEST.json").decode("utf-8"))
        for f in man["files"]:
            h = hashlib.sha256(z.read(f["path"])).hexdigest()
            if h != f["sha256"]:
                n_bad += 1
                print("   [壞] %s" % f["path"])
    if n_bad:
        print(json.dumps({"gate": "FAIL", "bad_files": n_bad}))
        return 1
    print(json.dumps({"gate": "PASS", "sha256": digest, "files": len(man["files"])}, ensure_ascii=False))
    print("[驗證] %s:zip 雜湊+逐檔 manifest 全對(%d 檔)" % (zp.name, len(man["files"])))
    return 0


def cmd_restore(zippath):
    zp = Path(zippath) if zippath else None
    if zp is None or not zp.exists():
        cands = sorted(BK.glob("WorkOps_Backup_*.zip"))
        if not cands:
            print("[FAIL] 無備份可還原")
            return 1
        zp = cands[-1]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = STAGE / ts
    dst.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zp) as z:
        for info in z.infolist():                      # zip-slip 防護
            name = info.filename.replace("\\", "/")
            if name.startswith("/") or ".." in name.split("/"):
                continue
            z.extract(info, dst)
    print(json.dumps({"gate": "STAGED_REVIEW_REQUIRED", "canonical_mutation": False,
                      "staging": str(dst)}, ensure_ascii=False))
    print("[還原] 只到暫存 %s — 正本零觸碰;過目後由你自行取用(RC L06 同語義)" % dst)
    return 0


def main():
    ap = argparse.ArgumentParser(description="側車正本備份/驗證/還原到暫存(絕不覆寫正本)")
    ap.add_argument("command", nargs="?", default="backup", choices=["backup", "verify", "restore"])
    ap.add_argument("arg1", nargs="?", default="")
    a = ap.parse_args()
    if a.command == "backup":
        return cmd_backup()
    if a.command == "verify":
        return cmd_verify(a.arg1)
    return cmd_restore(a.arg1)


if __name__ == "__main__":
    sys.exit(main())
