#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA Inventory & Snapshot Manager v1.0
======================================
清點 + 保存 + 版本管理。所有 snapshot 功能的底層。

子命令:
  scan       即時清點 (不存檔)
  snapshot   拍快照
  list       列出快照
  diff a b   比對兩版
  verify id  驗證完整性
  rollback id 回滾 (dry-run 預設)
  bump kind  升版號 (patch/minor/major)
  changelog  最近兩版 CHANGELOG
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


import os, sys, json, hashlib, hmac, shutil, argparse, datetime, tarfile, fnmatch, re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

SNAP_DIR_NAME = "snapshots"
EXCLUDE = [
    "snapshots/*", "logs/*", "**/__pycache__/*", "**/*.pyc",
    "**/.git/*", "**/.venv/*", "**/node_modules/*",
    "**/*.tmp", "**/Thumbs.db", "**/.DS_Store", "**/*.bak",
]
EXCLUDE_AUTH = ["auth/registry/*", "auth/master.key"]


def now_iso() -> str:
    try:
        d = datetime.datetime.now(datetime.UTC).replace(microsecond=0, tzinfo=None)
    except AttributeError:
        d = datetime.datetime.utcnow().replace(microsecond=0)
    return d.isoformat() + "Z"

def now_compact() -> str:
    try:
        d = datetime.datetime.now(datetime.UTC)
    except AttributeError:
        d = datetime.datetime.utcnow()
    return d.strftime("%Y%m%d-%H%M%S")

def sha256_file(p: Path, chunk=65536) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(chunk), b""):
            h.update(b)
    return h.hexdigest()

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def fmt_bytes(n: int) -> str:
    for u in ["B","KB","MB","GB"]:
        if n < 1024: return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}TB"

def banner(s: str):
    print("\n" + "=" * 66 + f"\n  {s}\n" + "=" * 66)

def is_excluded(rel: str, pats: List[str]) -> bool:
    for p in pats:
        if fnmatch.fnmatch(rel, p): return True
        if fnmatch.fnmatch(rel, p.replace("**/","")): return True
    return False


class Scanner:
    def __init__(self, base: Path, include_auth: bool = False):
        self.base = Path(base).resolve()
        self.excludes = list(EXCLUDE)
        if not include_auth: self.excludes.extend(EXCLUDE_AUTH)
        self.include_auth = include_auth

    def scan_physical(self) -> Dict[str, Any]:
        files = []
        total = 0
        excluded = 0
        for root, dirs, fns in os.walk(self.base):
            dirs[:] = [d for d in dirs if not is_excluded(
                str(Path(root, d).relative_to(self.base)).replace("\\","/"),
                self.excludes)]
            for fn in fns:
                full = Path(root) / fn
                rel = str(full.relative_to(self.base)).replace("\\","/")
                if is_excluded(rel, self.excludes):
                    excluded += 1; continue
                try:
                    sz = full.stat().st_size
                    files.append({"path": rel, "size": sz, "sha256": sha256_file(full),
                                   "mtime": datetime.datetime.utcfromtimestamp(
                                       full.stat().st_mtime).replace(microsecond=0).isoformat()+"Z"})
                    total += sz
                except Exception as e:
                    print(f"  ⚠ skip {rel}: {e}")
        files.sort(key=lambda x: x["path"])
        merkle = hashlib.sha256()
        for f in files:
            merkle.update(f["sha256"].encode("ascii"))
            merkle.update(b"\n")
        return {"file_count": len(files), "total_bytes": total,
                "total_bytes_human": fmt_bytes(total), "excluded_count": excluded,
                "merkle_root": merkle.hexdigest(), "file_index": files}

    def scan_logical(self) -> Dict[str, Any]:
        subs_dir = self.base / "module"   # NEW: 對齊 v2 結構
        if not subs_dir.exists():
            subs_dir = self.base / "subsystems"   # 舊版相容
        subsystems = []
        if subs_dir.exists():
            for sd in sorted(subs_dir.iterdir()):
                if not sd.is_dir(): continue
                if sd.name in ("docs", "schemas", "supportive_module"): continue
                cmd_dir = sd / "cmd"
                cmds = [f.stem for f in sorted(cmd_dir.glob("*.py"))
                        if cmd_dir.exists() and f.stem != "__init__"]
                subsystems.append({"code": sd.name,
                                    "has_manifest": (sd / "manifest.json").exists() or (sd / "manifest.yaml").exists(),
                                    "command_count": len(cmds), "commands": cmds})

        cmds_json = self.base / "config" / "commands.json"
        reg_cmds = []
        mask = None
        if cmds_json.exists():
            try:
                d = json.loads(cmds_json.read_text(encoding="utf-8"))
                reg_cmds = d.get("commands", [])
                mask = d.get("feature_mask_hex")
            except Exception as e:
                print(f"  ⚠ commands.json: {e}")

        return {"subsystem_count": len(subsystems), "subsystems": subsystems,
                "command_count_physical": sum(s["command_count"] for s in subsystems),
                "command_count_registered": len(reg_cmds),
                "feature_mask_hex": mask, "registered_commands": reg_cmds}

    def scan_config(self) -> Dict[str, Any]:
        r = {"via_config": None, "product_manifest": None, "version_file": None}
        for k, p in [("via_config", self.base/"config"/"via.config.json"),
                     ("product_manifest", self.base/"product_manifest.json")]:
            if p.exists():
                try: r[k] = json.loads(p.read_text(encoding="utf-8"))
                except: pass
        vp = self.base / "VERSION"
        if vp.exists(): r["version_file"] = vp.read_text(encoding="utf-8").strip()
        return r

    def scan_runtime(self) -> Dict[str, Any]:
        r = {"license_count": 0, "binding_count": 0, "active_count": 0,
              "license_summary": []}
        for p in [self.base/"auth"/"registry"/"licenses.json",
                  self.base/"auth"/"registry"/"dual_hwbind.json"]:
            if p.exists():
                try:
                    d = json.loads(p.read_text(encoding="utf-8"))
                    if p.name == "licenses.json":
                        r["license_count"] = len(d)
                        r["active_count"] = sum(1 for l in d if l.get("status")=="Active")
                    elif p.name == "dual_hwbind.json":
                        r["binding_count"] = len(d)
                except: pass
        return r

    def scan_all(self) -> Dict[str, Any]:
        print(f"  [L1] file system...")
        L1 = self.scan_physical()
        print(f"       ✓ {L1['file_count']} files, {L1['total_bytes_human']}")
        print(f"  [L2] subsystems/commands...")
        L2 = self.scan_logical()
        print(f"       ✓ {L2['subsystem_count']} subs, {L2['command_count_registered']} cmds")
        print(f"  [L3] config...")
        L3 = self.scan_config()
        v = (L3["via_config"] or {}).get("version") or L3["version_file"] or "?"
        print(f"       ✓ version={v}")
        print(f"  [L4] runtime/auth...")
        L4 = self.scan_runtime()
        return {"scanned_at": now_iso(), "base": str(self.base),
                "include_auth": self.include_auth,
                "L1_physical": L1, "L2_logical": L2,
                "L3_config": L3, "L4_runtime": L4}


class SnapManager:
    def __init__(self, base: Path):
        self.base = Path(base).resolve()
        self.root = self.base / SNAP_DIR_NAME
        self.root.mkdir(exist_ok=True, parents=True)
        self.secret = os.getenv("VIA_LICENSE_SECRET", "CHANGE_ME").encode("utf-8")

    def _sign(self, content: str) -> str:
        return hmac.new(self.secret, content.encode("utf-8"), hashlib.sha256).hexdigest()

    def _read_version(self) -> str:
        for p in [self.base/"VERSION", self.base/"config"/"via.config.json"]:
            if p.exists():
                if p.name == "VERSION": return p.read_text(encoding="utf-8").strip()
                try: return json.loads(p.read_text(encoding="utf-8")).get("version", "0.0.0")
                except: pass
        return "0.0.0"

    def _write_version(self, ver: str):
        (self.base / "VERSION").write_text(ver + "\n", encoding="utf-8")
        cfg = self.base / "config" / "via.config.json"
        if cfg.exists():
            try:
                d = json.loads(cfg.read_text(encoding="utf-8"))
                d["version"] = ver
                cfg.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            except: pass

    def _snap_id(self, ver: str) -> str:
        return f"v{ver}_{now_compact()}_{sha256_text(now_iso())[:8]}"

    def create(self, version: str = None, archive: bool = False,
               include_auth: bool = False, note: str = "") -> Dict[str, Any]:
        ver = version or self._read_version()
        sid = self._snap_id(ver)
        out = self.root / sid

        banner(f"CREATING SNAPSHOT — {sid}")
        print(f"  Version: {ver}  Note: {note or '(none)'}  Archive: {archive}")
        sc = Scanner(self.base, include_auth=include_auth)
        inv = sc.scan_all()

        inv["snapshot_id"] = sid; inv["version"] = ver; inv["note"] = note
        inv["previous_snapshot_id"] = self._latest()

        manifest = {"snapshot_id": sid, "version": ver, "created_at": now_iso(),
                    "merkle_root": inv["L1_physical"]["merkle_root"],
                    "files": [{"path": f["path"], "sha256": f["sha256"], "size": f["size"]}
                              for f in inv["L1_physical"]["file_index"]]}

        out.mkdir(parents=True, exist_ok=False)
        inv_text = json.dumps(inv, ensure_ascii=False, indent=2)
        man_text = json.dumps(manifest, ensure_ascii=False, indent=2)
        (out/"INVENTORY.json").write_text(inv_text, encoding="utf-8")
        (out/"MANIFEST.json").write_text(man_text, encoding="utf-8")

        prev = inv["previous_snapshot_id"]
        if prev:
            try:
                pinv = self._load(prev)
                (out/"CHANGELOG.md").write_text(self._gen_changelog(pinv, inv),
                                                  encoding="utf-8")
            except Exception as e: print(f"  ⚠ changelog: {e}")
        else:
            (out/"CHANGELOG.md").write_text(
                f"# Initial Snapshot\n\nsnapshot_id: {sid}\nversion: {ver}\n",
                encoding="utf-8")

        if archive:
            print("  封存 files.tar.gz ...")
            with tarfile.open(out/"files.tar.gz", "w:gz") as tf:
                for f in inv["L1_physical"]["file_index"]:
                    tf.add(self.base/f["path"], arcname=f["path"])
            print(f"      ✓ {fmt_bytes((out/'files.tar.gz').stat().st_size)}")

        sig = self._sign(inv_text + man_text)
        (out/"SIGNATURE").write_text(
            f"snapshot_id: {sid}\nalgorithm: HMAC-SHA256\nsignature: {sig}\n",
            encoding="utf-8")
        (self.root/"LATEST.txt").write_text(sid + "\n", encoding="utf-8")

        banner(f"✓ SNAPSHOT SAVED")
        print(f"  Path  : snapshots/{sid}")
        print(f"  Files : {inv['L1_physical']['file_count']}")
        print(f"  Merkle: {inv['L1_physical']['merkle_root'][:32]}...")
        return inv

    def list(self) -> List[Dict[str, Any]]:
        items = []
        for d in sorted(self.root.iterdir()):
            if not d.is_dir(): continue
            ip = d/"INVENTORY.json"
            if not ip.exists(): continue
            try:
                inv = json.loads(ip.read_text(encoding="utf-8"))
                items.append({"snapshot_id": inv.get("snapshot_id", d.name),
                               "version": inv.get("version"),
                               "scanned_at": inv.get("scanned_at"),
                               "file_count": inv["L1_physical"]["file_count"],
                               "total_bytes": inv["L1_physical"]["total_bytes"],
                               "merkle_root": inv["L1_physical"]["merkle_root"][:16],
                               "note": inv.get("note"),
                               "has_archive": (d/"files.tar.gz").exists()})
            except Exception as e: print(f"  ⚠ {d.name}: {e}")
        return items

    def _latest(self) -> Optional[str]:
        p = self.root/"LATEST.txt"
        if p.exists():
            sid = p.read_text(encoding="utf-8").strip()
            if (self.root/sid).exists(): return sid
        items = sorted([d.name for d in self.root.iterdir() if d.is_dir()])
        return items[-1] if items else None

    def _load(self, sid: str) -> Dict[str, Any]:
        return json.loads((self.root/sid/"INVENTORY.json").read_text(encoding="utf-8"))

    def diff(self, a: str, b: str) -> Dict[str, Any]:
        A = self._load(a); B = self._load(b)
        fa = {f["path"]: f for f in A["L1_physical"]["file_index"]}
        fb = {f["path"]: f for f in B["L1_physical"]["file_index"]}
        return {"snapshot_a": a, "snapshot_b": b,
                "version_a": A.get("version"), "version_b": B.get("version"),
                "files": {"added": sorted(set(fb)-set(fa)),
                          "removed": sorted(set(fa)-set(fb)),
                          "modified": sorted([p for p in set(fa)&set(fb)
                                              if fa[p]["sha256"] != fb[p]["sha256"]]),
                          "unchanged_count": len(set(fa)&set(fb))},
                "subsystems": {
                    "added": sorted({s["code"] for s in B["L2_logical"]["subsystems"]} -
                                     {s["code"] for s in A["L2_logical"]["subsystems"]}),
                    "removed": sorted({s["code"] for s in A["L2_logical"]["subsystems"]} -
                                       {s["code"] for s in B["L2_logical"]["subsystems"]})}}

    def _gen_changelog(self, A: Dict, B: Dict) -> str:
        d = self.diff(A["snapshot_id"], B["snapshot_id"])
        lines = [f"# Changelog", "",
                 f"**From** `{d['snapshot_a']}` ({d['version_a']})",
                 f"**To**   `{d['snapshot_b']}` ({d['version_b']})", "",
                 f"## Files",
                 f"- Added    : {len(d['files']['added'])}",
                 f"- Removed  : {len(d['files']['removed'])}",
                 f"- Modified : {len(d['files']['modified'])}",
                 f"- Unchanged: {d['files']['unchanged_count']}", ""]
        if d["subsystems"]["added"] or d["subsystems"]["removed"]:
            lines.append("## Subsystems")
            for s in d["subsystems"]["added"]:   lines.append(f"- ➕ `{s}`")
            for s in d["subsystems"]["removed"]: lines.append(f"- ➖ `{s}`")
        return "\n".join(lines) + "\n"

    def verify(self, sid: str) -> Dict[str, Any]:
        out = self.root/sid
        if not out.exists(): return {"ok": False, "error": "snapshot missing"}
        inv_text = (out/"INVENTORY.json").read_text(encoding="utf-8")
        man_text = (out/"MANIFEST.json").read_text(encoding="utf-8")
        # SIGNATURE
        actual = ""
        for line in (out/"SIGNATURE").read_text(encoding="utf-8").splitlines():
            if line.startswith("signature:"): actual = line.split(":",1)[1].strip()
        expected = self._sign(inv_text + man_text)
        sig_ok = hmac.compare_digest(expected, actual)
        # Files vs current
        manifest = json.loads(man_text)
        ok = 0; mismatch = []; missing = []
        for f in manifest["files"]:
            p = self.base/f["path"]
            if not p.exists(): missing.append(f["path"]); continue
            if sha256_file(p) == f["sha256"]: ok += 1
            else: mismatch.append(f["path"])
        # Merkle
        merkle = hashlib.sha256()
        for f in sorted(manifest["files"], key=lambda x: x["path"]):
            merkle.update(f["sha256"].encode("ascii")); merkle.update(b"\n")
        merkle_ok = merkle.hexdigest() == manifest["merkle_root"]

        checks = [
            {"name": "HMAC signature", "ok": sig_ok,
             "detail": "match" if sig_ok else "MISMATCH"},
            {"name": "File hashes",
             "ok": len(mismatch)==0 and len(missing)==0,
             "detail": f"matched={ok} mismatched={len(mismatch)} missing={len(missing)}"},
            {"name": "Merkle root", "ok": merkle_ok,
             "detail": "match" if merkle_ok else "MISMATCH"}]
        return {"snapshot_id": sid, "checks": checks,
                "ok": all(c["ok"] for c in checks),
                "mismatched_sample": mismatch[:5], "missing_sample": missing[:5]}

    def rollback(self, sid: str, dry_run: bool = True) -> Dict[str, Any]:
        arc = self.root/sid/"files.tar.gz"
        if not arc.exists():
            return {"ok": False, "error": "snapshot has no files.tar.gz"}
        v = self.verify(sid)
        if not v["ok"]:
            return {"ok": False, "error": "integrity check failed", "verify": v}
        if dry_run:
            with tarfile.open(arc, "r:gz") as tf:
                return {"ok": True, "dry_run": True, "file_count": len(tf.getnames())}
        self.create(note=f"safety before rollback to {sid}")
        with tarfile.open(arc, "r:gz") as tf:
            tf.extractall(self.base)
        return {"ok": True, "rolled_back_to": sid}

    def bump(self, kind: str) -> Tuple[str, str]:
        v = self._read_version()
        m = re.match(r"^(\d+)\.(\d+)\.(\d+)", v)
        if not m: raise ValueError(f"bad VERSION: {v}")
        mj, mi, pt = map(int, m.groups())
        if kind == "patch": pt += 1
        elif kind == "minor": mi += 1; pt = 0
        elif kind == "major": mj += 1; mi = 0; pt = 0
        else: raise ValueError("kind must be patch/minor/major")
        new = f"{mj}.{mi}.{pt}"
        self._write_version(new)
        return v, new


# ============================================================
# CLI
# ============================================================
def main():
    ap = argparse.ArgumentParser(prog="via_inventory")
    ap.add_argument("--base", default=str(Path.cwd()))
    sub = ap.add_subparsers(dest="cmd")

    s = sub.add_parser("scan"); s.add_argument("--include-auth", action="store_true")
    s.add_argument("--output")

    s = sub.add_parser("snapshot"); s.add_argument("--version"); s.add_argument("--archive", action="store_true")
    s.add_argument("--include-auth", action="store_true"); s.add_argument("--note", default="")

    sub.add_parser("list")
    s = sub.add_parser("diff"); s.add_argument("snap_a"); s.add_argument("snap_b")
    s = sub.add_parser("verify"); s.add_argument("snap_id")
    s = sub.add_parser("rollback"); s.add_argument("snap_id"); s.add_argument("--execute", action="store_true")
    sub.add_parser("changelog")
    s = sub.add_parser("bump"); s.add_argument("kind", choices=["patch","minor","major"])

    args = ap.parse_args()
    if not args.cmd: ap.print_help(); return

    if args.cmd == "scan":
        sc = Scanner(args.base, include_auth=args.include_auth)
        banner("INSTANT SCAN")
        inv = sc.scan_all()
        if args.output:
            Path(args.output).write_text(json.dumps(inv, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
        else:
            print(f"\n  Files: {inv['L1_physical']['file_count']} "
                  f"({inv['L1_physical']['total_bytes_human']})")
            print(f"  Subs : {inv['L2_logical']['subsystem_count']}")
            print(f"  Cmds : {inv['L2_logical']['command_count_registered']}")
            print(f"  Merkle: {inv['L1_physical']['merkle_root'][:32]}...")

    elif args.cmd == "snapshot":
        SnapManager(args.base).create(version=args.version, archive=args.archive,
                                       include_auth=args.include_auth, note=args.note)

    elif args.cmd == "list":
        items = SnapManager(args.base).list()
        if not items: print("  (none)"); return
        banner(f"SNAPSHOTS ({len(items)})")
        for x in items:
            print(f"  {x['snapshot_id']}  v{x['version']}  files={x['file_count']}  "
                  f"size={fmt_bytes(x['total_bytes'])}  "
                  f"{'[ARCHIVED]' if x['has_archive'] else ''}")
            if x.get("note"): print(f"    └─ {x['note']}")

    elif args.cmd == "diff":
        d = SnapManager(args.base).diff(args.snap_a, args.snap_b)
        banner(f"DIFF {args.snap_a} → {args.snap_b}")
        print(f"  v{d['version_a']} → v{d['version_b']}")
        print(f"  + {len(d['files']['added'])}  - {len(d['files']['removed'])}  "
              f"~ {len(d['files']['modified'])}  = {d['files']['unchanged_count']}")
        if d["subsystems"]["added"]:   print(f"  Subs +: {d['subsystems']['added']}")
        if d["subsystems"]["removed"]: print(f"  Subs -: {d['subsystems']['removed']}")

    elif args.cmd == "verify":
        r = SnapManager(args.base).verify(args.snap_id)
        banner(f"VERIFY {args.snap_id}")
        for c in r["checks"]:
            print(f"  {'✓' if c['ok'] else '✗'} {c['name']:<24} {c['detail']}")
        if r.get("mismatched_sample"):
            print(f"\n  Mismatched sample:")
            for p in r["mismatched_sample"]: print(f"    - {p}")
        print(f"\n  Overall: {'✓ OK' if r['ok'] else '✗ VIOLATION'}")
        sys.exit(0 if r["ok"] else 1)

    elif args.cmd == "rollback":
        r = SnapManager(args.base).rollback(args.snap_id, dry_run=not args.execute)
        if not r["ok"]: print(f"  ✗ {r['error']}"); sys.exit(1)
        if r.get("dry_run"): print(f"  DRY-RUN: would restore {r['file_count']} files")
        else: print(f"  ✓ rolled back to {r['rolled_back_to']}")

    elif args.cmd == "bump":
        old, new = SnapManager(args.base).bump(args.kind)
        print(f"  {old} → {new}")

    elif args.cmd == "changelog":
        mgr = SnapManager(args.base)
        items = mgr.list()
        if len(items) < 2: print("  need >= 2 snapshots"); return
        A = mgr._load(items[-2]["snapshot_id"])
        B = mgr._load(items[-1]["snapshot_id"])
        print(mgr._gen_changelog(A, B))


if __name__ == "__main__":
    main()
