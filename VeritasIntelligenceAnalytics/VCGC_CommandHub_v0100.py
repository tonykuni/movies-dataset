# -*- coding: utf-8 -*-
"""VCGC_CommandHub_v0100.py — VIA 4-command governance hub (PY-complete, PS-thin).

四個核心短指令(全邏輯純 Python,PowerShell 僅薄 TUI 外殼):
  boot  → via      晨間:讀前次備份 + 頂部短指令矩陣 + 系統摘要(Rich 調整格式)
  pano  → via-pano 全景檢視 GitHub + 本機 PC File,一輪安全 AST 修復(預設乾跑,--apply 才寫)
  bak   → via-bak  主動備份 + Graphify 拓撲 + OmniRoute 帳本 + agency-mem 交接記憶
  ast   → via-ast  AST 導入加速器:剪貼簿 / --code-file / --code,diff 預覽 + 確認,--rollback 還原

路徑一律由環境變數 VIA_ROOT 決定(預設 = 本檔所在的 VIA 根),不寫死任何本機路徑。
狀態與備份寫在 VIA_Reports/vcgc_hub/(.gitignore 已排除,永不入庫)。
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

import argparse
import ast
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except Exception:
    RICH_AVAILABLE = False

try:
    import libcst as _cst  # type: ignore
    LIBCST_AVAILABLE = True
except Exception:
    _cst = None
    LIBCST_AVAILABLE = False

# ==============================================================================
# [ANCHOR: SSOT_PATHS] 路徑全由 VIA_ROOT 決定,狀態寫在 gitignore 的 VIA_Reports 下
# ==============================================================================
VIA_ROOT = Path(os.environ.get("VIA_ROOT") or Path(__file__).resolve().parent).resolve()
HUB_DIR = VIA_ROOT / "VIA_Reports" / "vcgc_hub"
STATE_DIR = HUB_DIR / "state"
BACKUP_ROOT = HUB_DIR / "backups"
LEDGER_FILE = STATE_DIR / "universal_ledger.jsonl"
AGENCY_MEM_FILE = STATE_DIR / "agency_mem_handoff.json"
GRAPHIFY_FILE = STATE_DIR / "graphify_topology.json"
OMNIROUTE_FILE = STATE_DIR / "omniroute_ledger.json"

console = Console(force_terminal=True) if RICH_AVAILABLE else None

SHORT_COMMANDS_SPEC = [
    ("via", "主控台＋晨間快照", "讀取前次備份與系統狀態,開選擇題或按 Enter 直接貼上指令", "PS UI + Rich"),
    ("via-pano", "全景檢視＋AST修復", "掃描 GitHub 與本機 PC File,一輪安全 AST 修復(--apply 才寫)", "Python AST/CST"),
    ("via-bak", "四合一主動備份", "檔案快照 + Graphify 拓撲 + OmniRoute 帳本 + agency-mem", "SHA-256 棘輪"),
    ("via-ast", "AST 導入加速器", "剪貼簿 / --code-file / --code,diff 預覽 + 確認,可 --rollback", "AST Compile"),
]

# 全景掃描排除目錄(凍結 / 副本 / 退役 / 輸出殘檔不動)
_PANO_EXCLUDE = {
    ".git", ".venv", "venv", "__pycache__", "backups", "VIA_Reports",
    "VIA_RetiredEngines", "SCOPE_COPY", "ASSETS", "intake", "_archive",
    "node_modules", ".vcgc_state", "vcgc_hub",
}


def ensure_dirs() -> None:
    for d in (HUB_DIR, STATE_DIR, BACKUP_ROOT):
        d.mkdir(parents=True, exist_ok=True)


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_cmd(cmd: list[str], cwd: Path = VIA_ROOT) -> tuple[int, str]:
    try:
        res = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=20,
        )
        return res.returncode, (res.stdout or res.stderr or "").strip()
    except Exception as exc:
        return 1, str(exc)


def read_clipboard_text() -> str:
    """讀系統剪貼簿純文字,零外部相依(tkinter → PowerShell Get-Clipboard 後援)。"""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        text = root.clipboard_get()
        root.destroy()
        return text
    except Exception:
        rc, out = run_cmd(["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"])
        if rc == 0:
            return out
        rc2, out2 = run_cmd(["pbpaste"])
        if rc2 == 0:
            return out2
        raise RuntimeError(f"無法讀取系統剪貼簿: {out}")


def _excluded(p: Path) -> bool:
    return any(part in _PANO_EXCLUDE for part in p.parts)


def _pathkey(p: Path) -> str:
    """以完整(resolved)路徑產生穩定鍵,避免同名不同目錄的備份互撞。"""
    return hashlib.sha1(str(p.resolve()).encode("utf-8")).hexdigest()[:12]


def _is_versioned_original(stem: str) -> bool:
    """尾版正本(..._vNNNN):不就地改寫,應另出新版(獨立性 + 鎖定正本保護)。"""
    return bool(re.search(r"_v\d{3,}$", stem))


# ==============================================================================
# [ANCHOR: TOP_COMMAND_MATRIX] 頂部短指令速查矩陣(固定於最上方)
# ==============================================================================
def print_top_command_matrix() -> None:
    if not RICH_AVAILABLE:
        print("=== VIA 短指令速查矩陣 ===")
        for cmd, title, desc, _ in SHORT_COMMANDS_SPEC:
            print(f"  {cmd:<10} | {title} | {desc}")
        return
    t = Table(
        title="[bold #88C0D0]VIA 短指令速查矩陣 (COMMAND QUICK MATRIX)[/]",
        box=box.ROUNDED, header_style="bold #ECEFF4 on #2E3440",
        border_style="#5E81AC", expand=True, padding=(0, 1),
    )
    t.add_column("短指令", style="bold #A3BE8C", width=11, no_wrap=True)
    t.add_column("模組定位", style="bold #EBCB8B", width=18, no_wrap=True)
    t.add_column("功能說明", style="#E5E9F0", overflow="fold")
    t.add_column("核心引擎", style="dim #81A1C1", width=14, no_wrap=True)
    for cmd, title, desc, engine in SHORT_COMMANDS_SPEC:
        t.add_row(cmd, title, desc, engine)
    console.print(t)


# ==============================================================================
# [ANCHOR: RICH_SUMMARY_MATRIX] Rich 調整格式詳細摘要矩陣(無折行破圖)
# ==============================================================================
def print_detailed_summary_matrix(title: str, sections: list[dict],
                                  footer_note: str = "VCGC Hub | Local-First CPU") -> None:
    if not RICH_AVAILABLE:
        print(f"\n=== {title} ===")
        for row in sections:
            print(f"[{row.get('status')}] {row.get('category')} | {row.get('metric')}: {row.get('detail')}")
        return
    t = Table(
        title=f"[bold #88C0D0]{title}[/]", box=box.SIMPLE_HEAVY,
        header_style="bold #ECEFF4 on #2E3440", border_style="#4C566A",
        row_styles=["none", "dim"], expand=True, padding=(0, 1),
    )
    t.add_column("模組域", style="bold #88C0D0", width=12, no_wrap=True)
    t.add_column("核心指標 / 項目", style="bold #D8DEE9", width=22, no_wrap=True)
    t.add_column("燈號", justify="center", width=10, no_wrap=True)
    t.add_column("詳細數據與路徑摘要", style="#E5E9F0", overflow="fold")
    t.add_column("建議動作 / 備註", style="italic #A3BE8C", width=22, overflow="fold")
    for item in sections:
        raw = item.get("status", "INFO")
        if any(k in raw for k in ("OK", "就緒", "綠")):
            badge = f"[bold #A3BE8C]● {raw}[/]"
        elif any(k in raw for k in ("WARN", "待修", "黃")):
            badge = f"[bold #EBCB8B]▲ {raw}[/]"
        else:
            badge = f"[bold #BF616A]■ {raw}[/]"
        t.add_row(str(item.get("category", "-")), str(item.get("metric", "-")), badge,
                  str(item.get("detail", "-")), str(item.get("action", "-")))
    console.print(Panel(
        t, subtitle=f"[dim #81A1C1]{footer_note} | accel={'on' if VIA_ACCEL else 'off'} | {datetime.now():%Y-%m-%d %H:%M:%S}[/]",
        border_style="#5E81AC", padding=(0, 1)))


# ==============================================================================
# [ANCHOR: MORNING_BOOT] 1. boot:頂部矩陣 + 晨間讀前次備份
# ==============================================================================
def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def cmd_boot(show_top_matrix: bool = True) -> int:
    ensure_dirs()
    if show_top_matrix:
        print_top_command_matrix()
    rows: list[dict] = []
    mem = _read_json(AGENCY_MEM_FILE)
    if mem:
        backup_path = mem.get("last_backup_dir", "無")
        rows.append({"category": "AGENCY-MEM", "metric": "前次跨 AI 交接記憶", "status": "就緒",
                     "detail": f"時間: {mem.get('timestamp', '未知')} | 焦點: {mem.get('active_focus', '-')}",
                     "action": "已載入前次上下文"})
        rows.append({"category": "BACKUP", "metric": "前次主動備份快照",
                     "status": "就緒" if backup_path != "無" and Path(backup_path).exists() else "黃燈",
                     "detail": f"目錄: {Path(backup_path).name} | 檔數: {mem.get('backed_up_files', 0)}",
                     "action": "via-bak 可建立新快照"})
    else:
        rows.append({"category": "AGENCY-MEM", "metric": "前次跨 AI 交接記憶", "status": "黃燈",
                     "detail": "尚未偵測到 agency_mem_handoff.json", "action": "請先執行 via-bak 初始化"})
    venv = Path(os.environ.get("VIRTUAL_ENV", "系統全域環境")).name
    rows.append({"category": "VIA-ENV", "metric": "Python 與虛擬環境", "status": "就緒",
                 "detail": f"Py {sys.version.split()[0]} | venv: {venv} | ROOT: {VIA_ROOT.name}",
                 "action": "CPU 本地模式就緒"})
    g = _read_json(GRAPHIFY_FILE)
    o = _read_json(OMNIROUTE_FILE)
    g_count = len(g.get("nodes", []))
    rows.append({"category": "ORCHESTRATE", "metric": "Graphify + OmniRoute",
                 "status": "就緒" if g_count > 0 else "黃燈",
                 "detail": f"拓撲節點: {g_count} | 本地 AST 省 Token 次數: {o.get('cumulative_ast_local_ops', 0)}",
                 "action": "低消耗路由已鎖定"})
    print_detailed_summary_matrix("VIA MORNING SUMMARY — 晨間前次備份與環境狀態矩陣", rows)
    return 0


# ==============================================================================
# [ANCHOR: PANORAMA_AUTOFIX] 2. pano:GitHub + PC File 全景 + 一輪 AST 修復
# ==============================================================================
class _AstOpenEncodingFixer(ast.NodeTransformer):
    """純 ast 後援:僅在 open() 可證明為文字模式時補 encoding='utf-8'(ast.unparse 會丟註解)。
    模式未知(非字面量)/ 二進位 / encoding 可能以位置(第 4 參)或 **kwargs 提供 → 一律跳過。"""
    def __init__(self) -> None:
        self.fixes: list[str] = []

    def visit_Call(self, node: ast.Call) -> ast.AST:
        self.generic_visit(node)
        if not (isinstance(node.func, ast.Name) and node.func.id == "open"):
            return node
        # encoding 可能是第 4 個位置參數(index 3);有 **kwargs 展開 → 未知,不動
        if len(node.args) >= 4 or any(k.arg is None for k in node.keywords):
            return node
        if any(k.arg == "encoding" for k in node.keywords):
            return node
        # 解析 mode:位置 arg[1] 或 mode= kwarg;只接受字面字串,非字面量 → 未知,不動
        mode_val: str | None = None
        if len(node.args) >= 2:
            a1 = node.args[1]
            if isinstance(a1, ast.Constant) and isinstance(a1.value, str):
                mode_val = a1.value
            else:
                return node
        for k in node.keywords:
            if k.arg == "mode":
                if isinstance(k.value, ast.Constant) and isinstance(k.value.value, str):
                    mode_val = k.value.value
                else:
                    return node
        # mode_val is None(預設 'r' 文字)或字面字串;含 'b' = 二進位 → 不動
        if mode_val is not None and "b" in mode_val:
            return node
        node.keywords.append(ast.keyword(arg="encoding", value=ast.Constant(value="utf-8")))
        self.fixes.append(f"L{getattr(node, 'lineno', '?')}")
        return node


def _libcst_fix(src: str) -> tuple[str | None, int]:
    """libcst 路徑:補 open() encoding,保留註解與排版。回 (new_src|None, 修正數)。"""
    if not LIBCST_AVAILABLE:
        return None, 0
    try:
        mod = _cst.parse_module(src)

        class _T(_cst.CSTTransformer):
            def __init__(self) -> None:
                self.n = 0

            def leave_Call(self, orig: "_cst.Call", upd: "_cst.Call"):  # noqa: N802
                func = upd.func
                if not (isinstance(func, _cst.Name) and func.value == "open"):
                    return upd
                args = list(upd.args)
                # **kwargs 展開 → 未知,不動
                if any(getattr(a, "star", "") == "**" for a in args):
                    return upd
                positional = [a for a in args if a.keyword is None and getattr(a, "star", "") == ""]
                kwargs = {a.keyword.value: a for a in args if a.keyword is not None}
                # encoding 已以 kwarg 或第 4 個位置參數提供 → 不動
                if "encoding" in kwargs or len(positional) >= 4:
                    return upd
                # 解析 mode:只接受字面字串;非字面量 → 未知,不動;二進位 → 不動
                mode_node = None
                if len(positional) >= 2:
                    mode_node = positional[1].value
                elif "mode" in kwargs:
                    mode_node = kwargs["mode"].value
                if mode_node is not None:
                    if isinstance(mode_node, _cst.SimpleString):
                        if "b" in mode_node.value:
                            return upd
                    else:
                        return upd
                # mode 缺省(文字)或文字字面量 → 補 encoding,保留註解排版
                self.n += 1
                newarg = _cst.Arg(keyword=_cst.Name("encoding"),
                                  value=_cst.SimpleString('"utf-8"'),
                                  equal=_cst.AssignEqual(whitespace_before=_cst.SimpleWhitespace(""),
                                                         whitespace_after=_cst.SimpleWhitespace("")))
                return upd.with_changes(args=args + [newarg])

        tr = _T()
        new = mod.visit(tr)
        return (new.code, tr.n) if tr.n else (None, 0)
    except Exception:
        return None, 0


def cmd_panorama(apply: bool = False, scope: str | None = None) -> int:
    ensure_dirs()
    rows: list[dict] = []
    # 寫入授權:--apply 必須搭配 --scope <授權子目錄>,否則一律只乾跑,絕不整樹改寫。
    # 且版本化正本(..._vNNNN)永不就地改(另出新版);掃描只在 scope 內,不跨系統。
    scan_root = (VIA_ROOT / scope).resolve() if scope else VIA_ROOT
    if scope and (VIA_ROOT not in scan_root.parents and scan_root != VIA_ROOT):
        rows.append({"category": "SAFETY", "metric": "--scope 越界", "status": "紅燈",
                     "detail": f"scope 必須在 VIA_ROOT 內:{scope}", "action": "拒絕,只乾跑"})
        scan_root, scope = VIA_ROOT, None
    write_ok = bool(apply and scope)
    if apply and not scope:
        rows.append({"category": "SAFETY", "metric": "--apply 遭擋(未給 --scope)", "status": "黃燈",
                     "detail": "整樹改寫會動到他系統/鎖定正本;--apply 需明確 --scope <授權子目錄>",
                     "action": "例:via-pano -Apply -Scope scripts;本次只乾跑"})
    # 1. GitHub 狀態
    if (VIA_ROOT / ".git").exists():
        _, branch = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        _, status_out = run_cmd(["git", "status", "--porcelain"])
        _, remote = run_cmd(["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"])
        changed = [l for l in status_out.splitlines() if l.strip()]
        sync = remote.replace("\t", " ↑/ ") + " ↓" if remote and "fatal" not in remote else "僅本機分支"
        rows.append({"category": "GITHUB", "metric": f"分支 [{branch}]",
                     "status": "綠燈" if not changed else "黃燈",
                     "detail": f"未提交變更: {len(changed)} | 遠端差異: {sync}",
                     "action": "工作區乾淨" if not changed else "可 via-bak 留存"})
    else:
        rows.append({"category": "GITHUB", "metric": "Git 檢測", "status": "黃燈",
                     "detail": f"{VIA_ROOT.name} 未初始化 .git", "action": "略過遠端比對"})
    # 2. PC File 盤點 + 一輪 AST 修復(偵測全景;寫入只在授權 scope 內、跳過版本化正本)
    py_files = [p for p in scan_root.rglob("*.py") if not _excluded(p)]
    ps_files = [p for p in scan_root.rglob("*.ps1") if not _excluded(p)]
    syntax_errors: list[str] = []
    detected: list[str] = []      # 偵測到可修復
    written: list[str] = []       # 實際寫入(授權 + 非版本化)
    skipped_versioned = 0         # 版本化正本:不就地改,另出新版
    engine_used = "libcst(保留註解)" if LIBCST_AVAILABLE else "ast(unparse)"
    for py in py_files:
        try:
            src = py.read_text(encoding="utf-8")
            ast.parse(src, filename=str(py))  # 語法閘
            new_src, n = (None, 0)
            if LIBCST_AVAILABLE:
                new_src, n = _libcst_fix(src)
            if new_src is None:
                tr = _AstOpenEncodingFixer()
                tree = tr.visit(ast.parse(src, filename=str(py)))
                if tr.fixes:
                    ast.fix_missing_locations(tree)
                    new_src, n = ast.unparse(tree) + "\n", len(tr.fixes)
            if new_src and n:
                compile(new_src, filename=str(py), mode="exec")  # Hydra 防護:記憶體編譯過才算
                detected.append(f"{py.name}({n})")
                if write_ok:
                    if _is_versioned_original(py.stem):
                        skipped_versioned += 1
                    else:
                        shutil.copy2(py, STATE_DIR / f"{_pathkey(py)}__{py.name}.pre_ast.bak")
                        py.write_text(new_src, encoding="utf-8")
                        written.append(py.name)
        except SyntaxError as se:
            syntax_errors.append(f"{py.name}:L{se.lineno}")
        except Exception as exc:
            syntax_errors.append(f"{py.name}:{str(exc)[:30]}")
    rows.append({"category": "PC FILE", "metric": "本機腳本資產盤點", "status": "綠燈",
                 "detail": f"Python: {len(py_files)} 支 | PowerShell: {len(ps_files)} 支"
                           f"{' | scope=' + scope if scope else ' | 全景(唯讀偵測)'}",
                 "action": "全數納入全景追蹤"})
    if write_ok:
        act = f"已寫入 {len(written)} 檔 · 跳過版本化正本 {skipped_versioned}(另出新版)"
    else:
        act = "乾跑偵測;--apply + --scope 才寫(版本化正本永不就地改)"
    rows.append({"category": "AST-FIX", "metric": f"一輪修復({engine_used})",
                 "status": "綠燈" if not syntax_errors else "紅燈",
                 "detail": f"語法錯誤: {len(syntax_errors)} | 偵測可修復: {len(detected)} 檔 {', '.join(detected[:3])}",
                 "action": act if not syntax_errors else f"請修: {', '.join(syntax_errors[:3])}"})
    print_detailed_summary_matrix("VIA PANORAMA — GitHub + PC File 全景檢測與一輪修復矩陣", rows)
    return 1 if syntax_errors else 0


# ==============================================================================
# [ANCHOR: ACTIVE_BACKUP] 3. bak:快照 + Graphify + OmniRoute + agency-mem
# ==============================================================================
def cmd_backup(note: str = "Routine Active Checkpoint") -> int:
    ensure_dirs()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    snap = BACKUP_ROOT / ts
    snap.mkdir(parents=True, exist_ok=True)
    exts = {".py", ".ps1", ".json", ".md", ".toml"}
    copied: list[dict] = []
    nodes: list[dict] = []
    for item in VIA_ROOT.rglob("*"):
        if not item.is_file() or _excluded(item) or item.suffix.lower() not in exts:
            continue
        rel = item.relative_to(VIA_ROOT)
        dest = snap / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dest)
        h = compute_sha256(item)
        copied.append({"file": str(rel), "sha256": h[:16]})
        if item.suffix.lower() == ".py":
            try:
                tree = ast.parse(item.read_text(encoding="utf-8"))
                funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                nodes.append({"module": str(rel), "functions": funcs, "sha256_16": h[:16]})
            except Exception:
                pass
    GRAPHIFY_FILE.write_text(json.dumps(
        {"updated_at": ts, "node_count": len(nodes), "nodes": nodes}, ensure_ascii=False, indent=2), encoding="utf-8")
    prev = _read_json(OMNIROUTE_FILE).get("cumulative_ast_local_ops", 0)
    total = prev + len(nodes)
    OMNIROUTE_FILE.write_text(json.dumps(
        {"updated_at": ts, "route": "Local-AST-First -> CPU -> LLM-Minimal", "cumulative_ast_local_ops": total},
        ensure_ascii=False, indent=2), encoding="utf-8")
    AGENCY_MEM_FILE.write_text(json.dumps({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "active_focus": note,
        "last_backup_dir": str(snap), "backed_up_files": len(copied), "graphify_nodes": len(nodes),
        "sha256_manifest": copied[:20]}, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(LEDGER_FILE, "a", encoding="utf-8") as lf:
        lf.write(json.dumps({"ts": ts, "event": "ACTIVE_BACKUP", "count": len(copied)}, ensure_ascii=False) + "\n")
    rows = [
        {"category": "SNAPSHOT", "metric": "實體檔案主動備份", "status": "綠燈",
         "detail": f"備份 {len(copied)} 檔至 {snap.name}", "action": "SHA-256 校驗完成"},
        {"category": "GRAPHIFY", "metric": "AST 模組拓撲", "status": "綠燈",
         "detail": f"收錄 {len(nodes)} 個 Python 模組節點", "action": GRAPHIFY_FILE.name},
        {"category": "OMNIROUTE", "metric": "本地路由省 Token 帳本", "status": "綠燈",
         "detail": f"累計本地 AST 處理次數: {total}", "action": "Zero-Token 優先"},
        {"category": "AGENCY-MEM", "metric": "跨 AI 交接記憶", "status": "綠燈",
         "detail": f"焦點: {note}", "action": "明日 via 自動讀取"},
    ]
    print_detailed_summary_matrix("VIA ACTIVE BACKUP — 四合一主動備份與記憶同步矩陣", rows)
    return 0


# ==============================================================================
# [ANCHOR: AST_ACCELERATOR] 4. ast:導入加速器(diff 預覽 + 確認 + rollback)
# ==============================================================================
def _confirm(prompt: str, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    if not sys.stdin.isatty():
        print("[ABORT] 非互動環境且未加 --yes,為安全不自動覆寫。")
        return False
    try:
        return input(f"{prompt} [y/N] ").strip().lower() in ("y", "yes")
    except EOFError:
        return False


def _show_diff(old: str, new: str, name: str) -> None:
    diff = list(difflib.unified_diff(old.splitlines(), new.splitlines(),
                                     fromfile=f"{name} (現況)", tofile=f"{name} (注入後)", lineterm=""))
    if not diff:
        print("(無差異)")
        return
    if RICH_AVAILABLE:
        from rich.syntax import Syntax
        console.print(Syntax("\n".join(diff), "diff", theme="ansi_dark", word_wrap=True))
    else:
        print("\n".join(diff))


def cmd_ast_inject(target_file: str, symbol_name: str | None, code_snippet: str | None,
                   code_file: str | None, from_clipboard: bool, assume_yes: bool) -> int:
    target = Path(target_file).resolve()
    if not target.exists():
        print(f"[ERROR] 找不到目標檔案: {target}")
        return 1
    if code_file:
        srcp = Path(code_file).resolve()
        if not srcp.exists():
            print(f"[ERROR] 找不到 --code-file: {srcp}")
            return 1
        raw = srcp.read_text(encoding="utf-8")
        label = f"CodeFile({srcp.name})"
    elif from_clipboard:
        raw = read_clipboard_text()
        label = "Clipboard"
    elif code_snippet:
        raw = code_snippet
        label = "Inline(--code)"
    else:
        print("[ERROR] 請提供 --code-file / --clipboard / --code 之一。")
        return 1
    if not raw or not raw.strip():
        print(f"[ERROR] 來源 {label} 內容為空,中止。")
        return 1

    orig_src = target.read_text(encoding="utf-8")
    orig_tree = ast.parse(orig_src, filename=str(target))
    inj = ast.parse(raw)
    import_nodes = [n for n in inj.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    logic_nodes = [n for n in inj.body if not isinstance(n, (ast.Import, ast.ImportFrom))]
    inj_defs = {n.name: n for n in logic_nodes
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    inj_stmts = [n for n in logic_nodes
                 if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    targets = {symbol_name} if symbol_name else set(inj_defs)

    # 原位替換:舊定義若在 targets 且注入有同名新定義 → 就地換(保留定義順序),
    # 不移到檔尾,避免後續 module-level 引用該符號時 NameError。
    new_body: list = []
    replaced: list[str] = []
    for node in orig_tree.body:
        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and node.name in targets and node.name in inj_defs):
            new_body.append(inj_defs[node.name])
            replaced.append(node.name)
            continue
        new_body.append(node)
    # 真正新增的定義(無同名舊定義)+ 注入的其他陳述式 → 插在 __main__ 之前
    added_defs = [n for name, n in inj_defs.items() if name not in replaced]
    tail_nodes = added_defs + inj_stmts
    # imports 插在既有 import 之後
    if import_nodes:
        existing = {ast.dump(n) for n in new_body if isinstance(n, (ast.Import, ast.ImportFrom))}
        idx = 0
        for i, node in enumerate(new_body):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                idx = i + 1
            elif i == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                idx = 1
        for imp in import_nodes:
            if ast.dump(imp) not in existing:
                new_body.insert(idx, imp)
                idx += 1
    insert_idx = len(new_body)
    for i, node in enumerate(new_body):
        if isinstance(node, ast.If) and "__name__" in ast.unparse(node.test) and "__main__" in ast.unparse(node.test):
            insert_idx = i
            break
    for off, n in enumerate(tail_nodes):
        new_body.insert(insert_idx + off, n)
    orig_tree.body = new_body
    ast.fix_missing_locations(orig_tree)
    final_src = ast.unparse(orig_tree) + "\n"
    compile(final_src, filename=str(target), mode="exec")  # Hydra 防護

    syms = ", ".join(sorted(targets)) if targets else f"{len(logic_nodes)} 個頂層陳述式"
    print(f"\n[AST-ACCEL] 目標 {target.name} ← {label} | 符號: {syms} | "
          f"原位覆寫 {len(replaced)} / 新增 {len(added_defs)} def + {len(inj_stmts)} 陳述式")
    _show_diff(orig_src, final_src, target.name)
    if not _confirm("確認注入並覆寫目標檔?", assume_yes):
        print("[CANCELLED] 未寫入,原檔不動。")
        return 0
    ensure_dirs()
    # 備份鍵以完整路徑 hash + 微秒時戳,避免同名不同目錄互撞、同秒覆寫
    bak = STATE_DIR / f"{_pathkey(target)}__{target.name}.{datetime.now():%Y%m%d_%H%M%S_%f}.astbak"
    shutil.copy2(target, bak)
    target.write_text(final_src, encoding="utf-8")
    print_detailed_summary_matrix("VIA AST ACCELERATOR — 無損語法樹注入報告", [{
        "category": "AST-ACCEL", "metric": f"[{target.name}]", "status": "綠燈",
        "detail": f"來源: {label} | 符號: {syms}", "action": f"備份: {bak.name}(可 via-ast --rollback 還原)"}])
    return 0


def cmd_ast_rollback(target_file: str, assume_yes: bool) -> int:
    target = Path(target_file).resolve()
    # 以完整路徑鍵查詢,只還原「這個路徑」的備份(不會抓到同名不同目錄的檔)
    baks = sorted(STATE_DIR.glob(f"{_pathkey(target)}__*.astbak"))
    if not baks:
        print(f"[ERROR] 找不到 {target.name}(此路徑)的 .astbak 備份(位置: {STATE_DIR})")
        return 1
    latest = baks[-1]
    old = target.read_text(encoding="utf-8") if target.exists() else ""
    restore = latest.read_text(encoding="utf-8")
    print(f"\n[ROLLBACK] 以最新備份還原 {target.name} ← {latest.name}")
    _show_diff(old, restore, target.name)
    if not _confirm("確認還原(目前內容將被覆蓋)?", assume_yes):
        print("[CANCELLED] 未還原。")
        return 0
    shutil.copy2(latest, target)
    print(f"[OK] 已還原 {target.name}(來源備份 {latest.name})")
    return 0


# ==============================================================================
# [ANCHOR: CLI] 參數路由(4 短指令)
# ==============================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description="VCGC 4-Command Hub (VIA_ROOT 由環境變數決定)")
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("boot", help="頂部短指令矩陣 + 晨間前次備份摘要")
    pp = sub.add_parser("pano", help="全景檢視 GitHub + PC File,一輪 AST 修復(預設乾跑)")
    pp.add_argument("--apply", action="store_true", help="實際寫入修復(需搭配 --scope;預設只乾跑報告)")
    pp.add_argument("--scope", default=None, help="--apply 時必填:只在此授權子目錄內寫(版本化正本一律跳過、不跨系統)")
    pb = sub.add_parser("bak", help="主動備份 + Graphify + OmniRoute + agency-mem")
    pb.add_argument("--note", default="Routine Active Checkpoint")
    pa = sub.add_parser("ast", help="AST 導入加速器(diff 預覽 + 確認)")
    pa.add_argument("--target", required=True)
    pa.add_argument("--symbol", default=None, help="指定單一符號(省略則自動偵測全部函式/類別)")
    pa.add_argument("--yes", action="store_true", help="跳過互動確認(非互動環境必帶)")
    pa.add_argument("--rollback", action="store_true", help="以最新 .astbak 還原 --target")
    g = pa.add_mutually_exclusive_group(required=False)
    g.add_argument("--code-file", help="注入來源 .py 檔")
    g.add_argument("--clipboard", action="store_true", help="從系統剪貼簿讀取")
    g.add_argument("--code", help="直接傳入程式碼字串")
    args = ap.parse_args()
    if args.command == "boot":
        return cmd_boot()
    if args.command == "pano":
        return cmd_panorama(apply=args.apply, scope=args.scope)
    if args.command == "bak":
        return cmd_backup(note=args.note)
    if args.command == "ast":
        if args.rollback:
            return cmd_ast_rollback(args.target, assume_yes=args.yes)
        return cmd_ast_inject(args.target, args.symbol, args.code, args.code_file, args.clipboard, args.yes)
    return 2


if __name__ == "__main__":
    sys.exit(main())
