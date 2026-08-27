#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA Structure Forge v2.0
========================
- BASE 為輸入參數
- 根資料夾固定 VeritasIntelligence
- 下層 module/
  - supportive_module/
  - 各專案 (VRN / VDS / VAP / ...) 各自含子專案資料夾

新 Header 規範 (locked):
  Line 1: VeritasIntelligenceAnalytics
  Line 2: Dual Hard-Bind License Console (VHBC)
  Line 3: v3.0 · 雙硬綁定授權治理面板 · maxDevices=2 · HKDF-SHA256 device key derivation · ● online · <ts> · ● <n> alert

CLI:
  python via_structure_forge.py wizard
  python via_structure_forge.py forge --base "C:\\" --projects VRN,VDF,VAP
  python via_structure_forge.py forge --base "C:\\" --projects all
  python via_structure_forge.py catalog
  python via_structure_forge.py header   # 只輸出 header HTML 片段
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

import os, sys, json, argparse, datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# ============================================================
# 1) 規格 — Header / 根名 / 專案目錄
# ============================================================
ROOT_FOLDER_NAME = "VeritasIntelligenceAnalytics"   # 與前面文件一致
MODULE_LAYER     = "module"
SUPPORTIVE_LAYER = "supportive_module"

# Header (locked)
HEADER = {
    "line1": "VeritasIntelligenceAnalytics",
    "line2": "Dual Hard-Bind License Console (VHBC)",
    "line3_template": ("v3.0 · 雙硬綁定授權治理面板 · maxDevices=2 · "
                       "HKDF-SHA256 device key derivation · ● online · {ts} · ● {alerts} alert"),
}

# 專案目錄 (catalog) — 子專案資料夾用 Forge 規範
PROJECT_CATALOG: Dict[str, Dict[str, Any]] = {
    "VRN": {
        "name": "Veritas Reporting Node",
        "subfolders": ["cmd", "lib", "tests", "docs"],
        "sub_projects": [
            "M01_UnifiedPDFConverter",
            "M02_ContentParser",
            "M03_LayoutEngine",
            "S01_RatingList",
            "S02_HealthScore",
        ],
    },
    "VDF": {
        "name": "Veritas Data Fusion",     # 照前面記錄
        "alias": "VDS",                     # 新名相容
        "subfolders": ["cmd", "lib", "tests", "docs"],
        "sub_projects": [
            "ingest",
            "fusion",
            "quality",
            "schema_registry",
        ],
    },
    "VAP": {
        "name": "Veritas Analytics Portal",
        "subfolders": ["cmd", "lib", "tests", "docs"],
        "sub_projects": [
            "dashboards",
            "pipelines",
            "exports",
            "ui_components",
        ],
    },
    "VPN": {
        "name": "Veritas Panorama Nexus",
        "subfolders": ["cmd", "lib", "tests", "docs"],
        "sub_projects": [
            "system_monitor",
            "command_governance",
            "panorama_core",
            "risk_engine",
        ],
    },
    "VGF": {
        "name": "Veritas Glyph Forge",
        "subfolders": ["cmd", "lib", "tests", "docs"],
        "sub_projects": [
            "vgf_core",
            "via_image",
            "vgf_ml",
        ],
    },
    "VEGN": {
        "name": "Veritas Environment Governance Nexus",
        "subfolders": ["cmd", "lib", "tests", "docs"],
        "sub_projects": [
            "step1_health_scan",
            "step2_5d_classify",
            "step3_policy_plan",
            "step4_prompt_export",
        ],
    },
}

# supportive_module 預設內容
SUPPORTIVE_CONTENT = {
    "subfolders": ["shared_lib", "common_config", "utils", "templates", "ll_handbook"],
    "files": {
        "README.md": "# Supportive Module\n\n跨專案共用元件與工具。",
        "shared_lib/__init__.py": "",
        "utils/__init__.py": "",
    }
}

# module 層的固定附加資料夾
MODULE_EXTRAS = ["docs", "schemas"]


# ============================================================
# 2) 工具函式
# ============================================================
def now_iso_z() -> str:
    # tz-aware UTC (Python 3.12+ 推薦寫法；同時相容 3.10/3.11)
    try:
        d = datetime.datetime.now(datetime.UTC).replace(microsecond=0, tzinfo=None)
    except AttributeError:
        d = datetime.datetime.utcnow().replace(microsecond=0)
    return d.isoformat() + "Z"

def today_ymd() -> str:
    return datetime.date.today().strftime("%Y-%m-%d")

def banner(s: str):
    print("\n" + "=" * 66)
    print(f"  {s}")
    print("=" * 66)

def resolve_projects(arg: str) -> List[str]:
    """'VRN,VDS,VAP' / 'all' / 'VRN,VDF' (VDF→VDS) → 標準清單"""
    if not arg or arg.strip().lower() == "all":
        return list(PROJECT_CATALOG.keys())
    out = []
    for tok in arg.split(","):
        t = tok.strip().upper()
        if t in PROJECT_CATALOG:
            out.append(t)
        else:
            # 找 alias
            for k, v in PROJECT_CATALOG.items():
                if v.get("alias") == t:
                    print(f"  ℹ alias {t} → {k}")
                    out.append(k); break
            else:
                print(f"  ⚠ 未知專案: {t}; 略過")
    return out


# ============================================================
# 3) Structure Forge
# ============================================================
class StructureForge:
    def __init__(self, base: Path, projects: List[str], dry_run: bool = False):
        self.base = Path(base).resolve()
        self.projects = projects
        self.dry = dry_run
        self.created_dirs: List[str] = []
        self.created_files: List[str] = []
        self.root_path = self.base / ROOT_FOLDER_NAME

    def _mkdir(self, rel: str):
        full = self.root_path / rel if rel else self.root_path
        self.created_dirs.append(str(full.relative_to(self.base)).replace("\\","/"))
        if self.dry:
            print(f"  [DRY] mkdir  {self.created_dirs[-1]}/"); return
        full.mkdir(parents=True, exist_ok=True)

    def _write(self, rel: str, content: str):
        full = self.root_path / rel
        rel_full = str(full.relative_to(self.base)).replace("\\","/")
        self.created_files.append(rel_full)
        if self.dry:
            print(f"  [DRY] write  {rel_full}  ({len(content)} bytes)"); return
        full.parent.mkdir(parents=True, exist_ok=True)
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

    def forge(self):
        banner(f"FORGING STRUCTURE — {ROOT_FOLDER_NAME}")
        print(f"  Base     : {self.base}")
        print(f"  Root     : {self.root_path}")
        print(f"  Projects : {self.projects}")
        print(f"  Dry run  : {self.dry}")

        # 1. 根目錄
        print("\n[1/5] 建立根目錄...")
        self._mkdir("")

        # 2. module 層
        print("[2/5] 建立 module/ 層...")
        self._mkdir(MODULE_LAYER)
        for extra in MODULE_EXTRAS:
            self._mkdir(f"{MODULE_LAYER}/{extra}")

        # 3. supportive_module
        print(f"[3/5] 建立 {SUPPORTIVE_LAYER}/...")
        sup_root = f"{MODULE_LAYER}/{SUPPORTIVE_LAYER}"
        self._mkdir(sup_root)
        for sf in SUPPORTIVE_CONTENT["subfolders"]:
            self._mkdir(f"{sup_root}/{sf}")
        for fname, content in SUPPORTIVE_CONTENT["files"].items():
            self._write(f"{sup_root}/{fname}", content)

        # 4. 各專案 + 子專案
        print(f"[4/5] 建立 {len(self.projects)} 個專案資料夾...")
        for code in self.projects:
            info = PROJECT_CATALOG[code]
            proj_root = f"{MODULE_LAYER}/{code}"
            self._mkdir(proj_root)
            # 標準子資料夾
            for sf in info["subfolders"]:
                self._mkdir(f"{proj_root}/{sf}")
            # 各子專案
            for sp in info["sub_projects"]:
                self._mkdir(f"{proj_root}/{sp}")
            # manifest
            manifest = {
                "code": code,
                "name": info["name"],
                "alias": info.get("alias"),
                "subfolders": info["subfolders"],
                "sub_projects": info["sub_projects"],
                "created_at": today_ymd(),
            }
            self._write(f"{proj_root}/manifest.json",
                        json.dumps(manifest, ensure_ascii=False, indent=2))
            # README
            self._write(f"{proj_root}/README.md",
                f"# {code} — {info['name']}\n\n" +
                (f"_Alias: {info['alias']}_\n\n" if info.get('alias') else "") +
                f"## 子專案\n\n" +
                "\n".join(f"- `{sp}/`" for sp in info["sub_projects"]) +
                f"\n\n## 標準子資料夾\n\n" +
                "\n".join(f"- `{sf}/`" for sf in info["subfolders"]) + "\n")

        # 5. 寫頂層 manifest / structure 描述
        print("[5/5] 寫頂層 manifest + structure.json...")
        structure = {
            "root_folder": ROOT_FOLDER_NAME,
            "base": str(self.base),
            "module_layer": MODULE_LAYER,
            "supportive_layer": SUPPORTIVE_LAYER,
            "projects": [
                {
                    "code": p,
                    "name": PROJECT_CATALOG[p]["name"],
                    "alias": PROJECT_CATALOG[p].get("alias"),
                    "path": f"{MODULE_LAYER}/{p}",
                    "sub_projects": PROJECT_CATALOG[p]["sub_projects"],
                }
                for p in self.projects
            ],
            "generated_at": now_iso_z(),
        }
        self._write("structure.json",
                    json.dumps(structure, ensure_ascii=False, indent=2))

        # 頂層 README
        self._write("README.md", self._gen_readme())

        # 摘要
        banner("✓ STRUCTURE FORGED")
        print(f"  Root        : {self.root_path}")
        print(f"  Directories : {len(self.created_dirs)}")
        print(f"  Files       : {len(self.created_files)}")
        print(f"  Projects    : {self.projects}")
        if not self.dry:
            print(f"\n  瀏覽:")
            print(f"    cd {self.root_path}")
            print(f"    cat structure.json")

    def _gen_readme(self) -> str:
        lines = [
            f"# {ROOT_FOLDER_NAME}",
            "",
            f"**Header**: {HEADER['line1']} / {HEADER['line2']}",
            f"**Generated**: {now_iso_z()}",
            f"**Base**: `{self.base}`",
            "",
            "## 結構",
            "",
            "```",
            f"{ROOT_FOLDER_NAME}/",
            f"├── {MODULE_LAYER}/",
            f"│   ├── {SUPPORTIVE_LAYER}/",
        ]
        for sf in SUPPORTIVE_CONTENT["subfolders"]:
            lines.append(f"│   │   ├── {sf}/")
        for i, p in enumerate(self.projects):
            is_last = (i == len(self.projects) - 1)
            connector = "└──" if is_last else "├──"
            lines.append(f"│   {connector} {p}/  ({PROJECT_CATALOG[p]['name']})")
            sub_pipe = "    " if is_last else "│   "
            info = PROJECT_CATALOG[p]
            all_sub = info["subfolders"] + info["sub_projects"]
            for j, sp in enumerate(all_sub):
                is_last_sp = (j == len(all_sub) - 1)
                sc = "└──" if is_last_sp else "├──"
                lines.append(f"│   {sub_pipe}{sc} {sp}/")
        lines.append("└── structure.json")
        lines.append("```")
        lines.append("")
        lines.append("## 專案清單")
        lines.append("")
        for p in self.projects:
            info = PROJECT_CATALOG[p]
            alias_str = f" (alias: {info['alias']})" if info.get("alias") else ""
            lines.append(f"### {p}{alias_str}")
            lines.append(f"_{info['name']}_")
            lines.append("")
            lines.append("子專案:")
            for sp in info["sub_projects"]:
                lines.append(f"- `{sp}/`")
            lines.append("")
        return "\n".join(lines)


# ============================================================
# 4) Header generator (給 HTML / 文件用)
# ============================================================
def render_header_html(alerts: int = 1, ts: Optional[str] = None) -> str:
    """產生對齊 VIA Visual Lock v1 的 header HTML 片段"""
    ts = ts or now_iso_z()
    line3 = HEADER["line3_template"].format(ts=ts, alerts=alerts)
    return f'''<!-- VIA Visual Lock v1 — Header (locked) -->
<header class="hdr">
  <div class="hdr-l1">{HEADER["line1"]}</div>
  <div class="hdr-l2">{HEADER["line2"]}</div>
  <div class="hdr-l3">{line3.replace(" · ", '<span class="dot"> · </span>')}</div>
</header>'''

def render_header_console() -> str:
    """純文字版 (給 CLI / log 用)"""
    return (f"{HEADER['line1']}\n"
            f"{HEADER['line2']}\n"
            f"{HEADER['line3_template'].format(ts=now_iso_z(), alerts=1)}")


# ============================================================
# 5) CLI
# ============================================================
def cmd_catalog():
    banner("PROJECT CATALOG")
    print(f"  Root folder name : {ROOT_FOLDER_NAME}")
    print(f"  Module layer     : {MODULE_LAYER}/")
    print(f"  Supportive layer : {SUPPORTIVE_LAYER}/")
    print()
    for k, v in PROJECT_CATALOG.items():
        alias = f" (alias: {v['alias']})" if v.get("alias") else ""
        print(f"  {k}{alias}")
        print(f"    {v['name']}")
        print(f"    Standard subfolders: {v['subfolders']}")
        print(f"    Sub-projects ({len(v['sub_projects'])}):")
        for sp in v["sub_projects"]:
            print(f"      - {sp}")
        print()


def cmd_header(args):
    if args.format == "html":
        print(render_header_html(alerts=args.alerts))
    else:
        print(render_header_console())


def cmd_forge(args):
    if not args.base:
        print("✗ 需要 --base"); sys.exit(2)
    projects = resolve_projects(args.projects or "all")
    if not projects:
        print("✗ 沒有有效的專案"); sys.exit(2)
    forge = StructureForge(Path(args.base), projects, dry_run=args.dry_run)
    forge.forge()


def wizard():
    banner("VIA Structure Forge — Wizard")

    # BASE
    default_base = "C:\\" if os.name == "nt" else os.path.expanduser("~")
    base = input(f"\n  BASE 路徑 [{default_base}]: ").strip() or default_base

    # 確認根名
    print(f"\n  Root folder 將建在: {Path(base) / ROOT_FOLDER_NAME}")

    # 專案
    print(f"\n  可用專案:")
    keys = list(PROJECT_CATALOG.keys())
    for i, k in enumerate(keys, 1):
        info = PROJECT_CATALOG[k]
        alias = f" / {info['alias']}" if info.get("alias") else ""
        print(f"    [{i}] {k}{alias:<10s}  {info['name']}")
        print(f"          {len(info['sub_projects'])} sub-projects: " +
              ", ".join(info['sub_projects'][:3]) +
              ("..." if len(info['sub_projects']) > 3 else ""))

    raw = input(f"\n  選擇 (編號/代碼/逗號分隔, 'all' 全選) [VRN,VDF,VAP]: ").strip()
    if not raw: raw = "VRN,VDF,VAP"
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
                resolved = resolve_projects(tok)
                selected.extend(resolved)
        selected = list(dict.fromkeys(selected))   # 去重保序

    if not selected:
        print("  沒選任何專案，取消。"); return

    print(f"\n  ============ 將要建立 ============")
    print(f"    根目錄     : {Path(base) / ROOT_FOLDER_NAME}")
    print(f"    Projects   : {selected}")
    total_sub = sum(len(PROJECT_CATALOG[p]['sub_projects']) for p in selected)
    print(f"    Sub-projects: {total_sub}")

    ans = input("\n  確認生成? [Y/n] ").strip().lower()
    if ans and ans != "y":
        print("  取消。"); return

    StructureForge(Path(base), selected).forge()


def main():
    ap = argparse.ArgumentParser(prog="via_structure_forge",
        description="VIA Structure Forge — 依參數建 VeritasIntelligence/ 樹")
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("wizard", help="互動式 (推薦)")
    sub.add_parser("catalog", help="列出可用專案")

    f = sub.add_parser("forge", help="CLI 一鍵生成")
    f.add_argument("--base", required=True, help="BASE 路徑 (例 C:\\)")
    f.add_argument("--projects", default="all",
                   help="逗號分隔 (例 VRN,VDS,VAP) 或 'all'")
    f.add_argument("--dry-run", action="store_true")

    h = sub.add_parser("header", help="輸出 header (HTML 片段或純文字)")
    h.add_argument("--format", choices=["html","text"], default="html")
    h.add_argument("--alerts", type=int, default=1)

    args = ap.parse_args()
    if args.cmd == "wizard":  wizard()
    elif args.cmd == "catalog": cmd_catalog()
    elif args.cmd == "forge":   cmd_forge(args)
    elif args.cmd == "header":  cmd_header(args)
    else: ap.print_help()


if __name__ == "__main__":
    main()
