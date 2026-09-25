#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_InjectAccelNetBridges_v0104 — 只增不減錨點注入器
對 VDF 樹內 .py 補 ACCEL-BRIDGE / NET-BRIDGE。已有錨點不改。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ACCEL_MARK = "[VIA:ACCEL-BRIDGE:"
NET_MARK = "[VIA:NET-BRIDGE:"

ACCEL_BLOCK = """# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
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
"""

NET_BLOCK = """# ===== [VIA:NET-BRIDGE:v0101] 統包網路工具橋(VDF 全導入;VIA_NetSupport 後備;graceful) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_sup = _nb_p / "supportive modules"
        _nb_dir = _nb_sup / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py")) + sorted(
                _nb_dir.glob("SUP_MDL740_NetUnified_v*.py")
            )
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
                break
        _nb_ns = _nb_sup / "VIA_NetSupport.py"
        if _nb_ns.exists():
            VIA_NET_TOOL_PATH = str(_nb_ns)
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    \"\"\"統包網路工具惰性載入(法遵閘 VIA_NET_CONSENT);缺席回 None(誠實)\"\"\"
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
"""

SKIP_DIR_PARTS = {
    "SCOPE_COPY",
    "BACKUP",
    "_rebuilds_superseded",
    "_from_vap_iso_cleanup",
    "__pycache__",
    ".git",
    "ASSETS",
    "ICON_BASE_MANAGED",
    "package_samples",
}


def _is_skipped(path: Path) -> bool:
    return any(part in SKIP_DIR_PARTS for part in path.parts)


def _insert_after_header(src: str, block: str) -> str:
    lines = src.splitlines(keepends=True)
    i = 0
    if i < len(lines) and lines[i].startswith("#!"):
        i += 1
    if i < len(lines) and re.match(r"^#.*coding[:=]", lines[i]):
        i += 1
    # from __future__ must stay first statement; keep any leading futures
    while i < len(lines) and lines[i].lstrip().startswith("from __future__"):
        i += 1
        while i < len(lines) and lines[i].startswith((" ", "\t")):
            i += 1
    # module docstring
    if i < len(lines) and lines[i].lstrip().startswith(('"""', "'''")):
        quote = '"""' if '"""' in lines[i] else "'''"
        if lines[i].count(quote) >= 2 and len(lines[i].strip()) > 3:
            i += 1
        else:
            i += 1
            while i < len(lines) and quote not in lines[i]:
                i += 1
            if i < len(lines):
                i += 1
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    piece = block if block.endswith("\n") else block + "\n"
    if i > 0 and not lines[i - 1].endswith("\n"):
        piece = "\n" + piece
    return "".join(lines[:i]) + piece + "".join(lines[i:])


def plan_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    need_accel = ACCEL_MARK not in text
    need_net = NET_MARK not in text
    return {
        "path": str(path),
        "need_accel": need_accel,
        "need_net": need_net,
        "ok": (not need_accel) and (not need_net),
    }


def apply_file(path: Path, backup_dir: Path) -> dict:
    raw = path.read_text(encoding="utf-8", errors="replace")
    need_accel = ACCEL_MARK not in raw
    need_net = NET_MARK not in raw
    if not need_accel and not need_net:
        return {"path": str(path), "changed": False, "need_accel": False, "need_net": False}
    new = raw
    if need_accel:
        new = _insert_after_header(new, ACCEL_BLOCK)
    if need_net:
        new = _insert_after_header(new, NET_BLOCK)
    rel = path.name
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_dir / f"{rel}.{stamp}.bak")
    path.write_text(new, encoding="utf-8", newline="\n")
    return {"path": str(path), "changed": True, "need_accel": need_accel, "need_net": need_net}


def collect(vdf_root: Path) -> list[Path]:
    out = []
    for p in sorted(vdf_root.rglob("*.py")):
        if _is_skipped(p):
            continue
        if p.name.startswith("VDF_InjectAccelNetBridges"):
            continue
        out.append(p)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vdf-root", required=True)
    ap.add_argument("--mode", choices=("preview", "apply"), default="preview")
    ap.add_argument("--backup-dir", default="")
    ap.add_argument("--report", default="")
    args = ap.parse_args(argv)
    root = Path(args.vdf_root).resolve()
    files = collect(root)
    rows = [plan_file(p) for p in files]
    changed = []
    if args.mode == "apply":
        bdir = Path(args.backup_dir) if args.backup_dir else root / "tools" / "RUN_ACCELNET_v0104"
        for p, row in zip(files, rows):
            if row["ok"]:
                continue
            changed.append(apply_file(p, bdir))
    report = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "vdf_root": str(root),
        "mode": args.mode,
        "total": len(rows),
        "already_ok": sum(1 for r in rows if r["ok"]),
        "need_accel": sum(1 for r in rows if r["need_accel"]),
        "need_net": sum(1 for r in rows if r["need_net"]),
        "applied": len(changed),
        "rows": rows,
        "changed": changed,
    }
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
