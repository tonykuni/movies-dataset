#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA Header Sync v1.0 — S 部分
=============================
讓 VIA_DualHwBind_Console.html 與 VIA_Snapshot_Console.html
共用同一個 header partial。改 _header_partial.html 一處就同步兩處。

機制:
  1. tools/_header_partial.html 是 source of truth
  2. 兩個 console HTML 用以下標記包住自己的 header:
       <!-- BEGIN VIA_HEADER -->
         (任何內容)
       <!-- END VIA_HEADER -->
  3. 執行此工具會把標記之間的內容替換成 partial 的內容
  4. 若 console 還沒加標記，工具會自動找到 <header class="hdr">...</header>
     並把它用標記包起來

CLI:
  python via_header_sync.py sync              # 同步兩個 console
  python via_header_sync.py sync --dry-run    # 只看差異
  python via_header_sync.py check             # 檢查兩個 console 的 header 是否一致
  python via_header_sync.py extract           # 從 console 反向產生 partial (首次)
"""

import os, sys, re, argparse, hashlib
from pathlib import Path
from typing import Optional, Tuple, List

BEGIN_MARK = "<!-- BEGIN VIA_HEADER -->"
END_MARK   = "<!-- END VIA_HEADER -->"

# 預設管理的 console 清單；可由 CLI 加更多
DEFAULT_CONSOLES = [
    "VIA_DualHwBind_Console.html",
    "VIA_Snapshot_Console.html",
]


def sha8(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:8]


def find_console_dir(start: Path = None) -> Path:
    """從當前位置往上找 tools/ 或同層 HTML"""
    p = Path(start or Path.cwd()).resolve()
    for _ in range(5):
        # 直接含 HTML
        for h in DEFAULT_CONSOLES:
            if (p / h).exists():
                return p
        # 或包含 tools/
        if (p / "tools").exists() and any((p / "tools").glob("*.html")):
            return p / "tools"
        if p.parent == p: break
        p = p.parent
    return Path.cwd()


def extract_header_block(content: str) -> Optional[Tuple[int, int, str]]:
    """
    回傳 (start_idx, end_idx, inner_html)
    優先找 BEGIN/END 標記；找不到再找 <header class="hdr">...</header>
    """
    # 1) 標記版
    bi = content.find(BEGIN_MARK)
    if bi != -1:
        ei = content.find(END_MARK, bi)
        if ei != -1:
            inner_start = bi + len(BEGIN_MARK)
            return (bi, ei + len(END_MARK), content[inner_start:ei])

    # 2) <header class="hdr">...</header>
    m = re.search(r'<header\s+class="hdr">.*?</header>', content,
                  flags=re.DOTALL | re.IGNORECASE)
    if m:
        return (m.start(), m.end(), m.group(0))

    return None


def wrap_with_marks(html: str) -> str:
    """確保 html 被 BEGIN/END 標記包住"""
    return f"{BEGIN_MARK}\n{html.strip()}\n{END_MARK}"


def sync_console(console_path: Path, partial_html: str,
                 dry_run: bool = False) -> dict:
    """把 partial_html 注入 console_path"""
    if not console_path.exists():
        return {"path": str(console_path), "ok": False, "error": "file not found"}

    original = console_path.read_text(encoding="utf-8")
    found = extract_header_block(original)
    if not found:
        return {"path": str(console_path), "ok": False,
                "error": "no <header class='hdr'> or BEGIN/END marks found"}

    start, end, current_inner = found
    current_hash = sha8(current_inner.strip())
    new_block = wrap_with_marks(partial_html)
    new_hash = sha8(partial_html.strip())

    if current_hash == new_hash:
        return {"path": str(console_path), "ok": True,
                "action": "unchanged", "hash": current_hash}

    new_content = original[:start] + new_block + original[end:]

    if dry_run:
        return {"path": str(console_path), "ok": True,
                "action": "would-update", "dry_run": True,
                "old_hash": current_hash, "new_hash": new_hash,
                "size_diff": len(new_content) - len(original)}

    # 備份
    backup = console_path.with_suffix(console_path.suffix + ".bak")
    backup.write_text(original, encoding="utf-8")
    console_path.write_text(new_content, encoding="utf-8")
    return {"path": str(console_path), "ok": True,
            "action": "updated", "backup": str(backup),
            "old_hash": current_hash, "new_hash": new_hash}


def cmd_sync(args):
    base = Path(args.dir or find_console_dir()).resolve()
    partial_path = base / "_header_partial.html"

    print(f"\n  Working dir : {base}")
    print(f"  Partial     : {partial_path.name}")

    if not partial_path.exists():
        print(f"\n  ✗ 找不到 {partial_path}")
        print(f"     先執行: python via_header_sync.py extract")
        sys.exit(1)

    partial_html = partial_path.read_text(encoding="utf-8")
    print(f"  Partial hash: {sha8(partial_html)}")

    # 找所有要同步的 console
    targets = []
    for name in (args.targets.split(",") if args.targets else DEFAULT_CONSOLES):
        p = base / name.strip()
        if p.exists():
            targets.append(p)
        else:
            print(f"  ⊘ skip (missing): {name}")

    if not targets:
        print(f"\n  ✗ 沒有可同步的 console"); sys.exit(1)

    print(f"\n  Targets: {len(targets)}")
    for p in targets: print(f"    - {p.name}")
    print()

    results = []
    for p in targets:
        r = sync_console(p, partial_html, dry_run=args.dry_run)
        results.append(r)
        if not r.get("ok"):
            print(f"  ✗ {p.name}: {r.get('error')}")
        elif r.get("action") == "unchanged":
            print(f"  ⊘ {p.name}  unchanged (hash={r['hash']})")
        elif r.get("action") == "would-update":
            print(f"  ~ {p.name}  WOULD UPDATE  "
                  f"{r['old_hash']} → {r['new_hash']}  Δ={r['size_diff']:+d}B")
        elif r.get("action") == "updated":
            print(f"  ✓ {p.name}  UPDATED  "
                  f"{r['old_hash']} → {r['new_hash']}  backup: {Path(r['backup']).name}")

    if args.dry_run:
        print(f"\n  ⚠ DRY-RUN. 加 --execute 真的寫入")
    else:
        print(f"\n  ✓ Done. 備份檔: *.html.bak")


def cmd_check(args):
    base = Path(args.dir or find_console_dir()).resolve()
    print(f"\n  Dir: {base}\n")
    hashes = {}
    targets = args.targets.split(",") if args.targets else DEFAULT_CONSOLES
    for name in targets:
        p = base / name.strip()
        if not p.exists():
            print(f"  ⊘ missing: {name}"); continue
        content = p.read_text(encoding="utf-8")
        found = extract_header_block(content)
        if not found:
            print(f"  ✗ {name}: no header found"); continue
        _, _, inner = found
        h = sha8(inner.strip())
        hashes[name] = h
        print(f"  • {name}  header_hash={h}")

    partial_path = base / "_header_partial.html"
    if partial_path.exists():
        ph = sha8(partial_path.read_text(encoding="utf-8").strip())
        print(f"\n  • _header_partial.html  hash={ph}")
        diffs = [n for n, h in hashes.items() if h != ph]
        if diffs:
            print(f"\n  ⚠ Out-of-sync with partial: {diffs}")
            print(f"     Fix: python via_header_sync.py sync --execute")
        else:
            print(f"\n  ✓ All consoles match partial")
    else:
        unique = set(hashes.values())
        if len(unique) == 1:
            print(f"\n  ✓ All {len(hashes)} consoles share same header")
        else:
            print(f"\n  ⚠ {len(unique)} distinct headers (no partial yet)")
            print(f"     Run: python via_header_sync.py extract")


def cmd_extract(args):
    """從現有 console 抽出 header → 寫成 _header_partial.html"""
    base = Path(args.dir or find_console_dir()).resolve()
    src_name = args.source or DEFAULT_CONSOLES[0]
    src = base / src_name
    if not src.exists():
        print(f"  ✗ 找不到 {src}"); sys.exit(1)

    content = src.read_text(encoding="utf-8")
    found = extract_header_block(content)
    if not found:
        print(f"  ✗ {src.name} 沒有 <header class='hdr'>"); sys.exit(1)

    _, _, inner = found
    partial_path = base / "_header_partial.html"

    if partial_path.exists() and not args.force:
        print(f"  ⚠ {partial_path.name} 已存在；用 --force 覆寫"); sys.exit(1)

    partial_path.write_text(inner.strip() + "\n", encoding="utf-8")
    print(f"  ✓ Extracted from {src.name}")
    print(f"  ✓ Wrote {partial_path.name}  ({len(inner)} bytes, hash={sha8(inner.strip())})")
    print(f"\n  下一步: python via_header_sync.py sync --execute")


def main():
    ap = argparse.ArgumentParser(prog="via_header_sync",
        description="VIA Header Sync — 共用 header partial 同步")
    sub = ap.add_subparsers(dest="cmd")

    s = sub.add_parser("sync", help="把 partial 同步到所有 console")
    s.add_argument("--dir", help="工作目錄 (預設: 自動偵測)")
    s.add_argument("--targets", help="逗號分隔的 console 檔名")
    s.add_argument("--dry-run", action="store_true", default=True)
    s.add_argument("--execute", dest="dry_run", action="store_false",
                   help="實際寫入 (預設 dry-run)")

    c = sub.add_parser("check", help="檢查 header 是否一致")
    c.add_argument("--dir", help="工作目錄")
    c.add_argument("--targets", help="逗號分隔")

    e = sub.add_parser("extract", help="從 console 抽出 partial (首次)")
    e.add_argument("--dir", help="工作目錄")
    e.add_argument("--source", help="來源 console 檔名 (預設第一個)")
    e.add_argument("--force", action="store_true", help="覆寫已存在的 partial")

    args = ap.parse_args()
    if args.cmd == "sync":     cmd_sync(args)
    elif args.cmd == "check":  cmd_check(args)
    elif args.cmd == "extract":cmd_extract(args)
    else: ap.print_help()


if __name__ == "__main__":
    main()
