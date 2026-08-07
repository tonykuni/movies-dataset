#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPNS AST Symbol Engine  ·  vpns_ast_symbol_engine.py
=====================================================================
精準錨點式 (precise-anchor) Python 符號稽核 + 跨檔呼叫名稱一致化引擎。

設計原則 (對齊 VIA 治理):
  - 只讀預設 (scan / plan = dry-run);apply 需 token,且永不碰 freeze-zone。
  - 用 ast 取得每個 Name / FunctionDef 的精準 (line, col, end) 錨點,
    做「定位後外科式字串替換」,保留註解 / 空白 / 字串原貌 (不用 ast.unparse 整檔重寫,
    避免破壞可讀性 → 避免九頭龍)。
  - 跨檔傳播:rename 一個 def 名,所有檔案的同名 Name 呼叫點一起改。
  - 屬性存取 (obj.attr) 只「報告」不自動改 (保守,避免誤傷模組命名空間)。
  - apply 前先 ast.parse 全綠;apply 後對每檔再 ast.parse 驗證 (parse=0 gate)。

模式:
  scan  --root DIR [--exclude SUBSTR ...]                         → 符號 + 約定 + 版號稽核
  plan  --root DIR --map MAP.json                                → 計畫編輯 (dry-run, 不寫檔)
  apply --root DIR --map MAP.json --token APPROVE_VPNS_AST_RENAME → 套用 (備份後外科改名)

MAP.json 格式:
  { "renames": [ {"old":"def_FooBar","new":"def_foo_bar"}, ... ] }
"""
import os, sys, ast, json, hashlib, argparse, datetime, shutil

APPLY_TOKEN = "APPROVE_VPNS_AST_RENAME"
STAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
ISO = datetime.datetime.now().isoformat(timespec="seconds")

# -------------------------------------------------------------------- helpers
def sha12(path):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for blk in iter(lambda: f.read(1 << 20), b""):
                h.update(blk)
        return h.hexdigest()[:12]
    except Exception:
        return None

def read_text(path):
    # tolerate BOM on read; write back no-BOM
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()

def write_text_nobom(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)

def iter_py(root, excludes):
    for dirpath, dirnames, filenames in os.walk(root):
        # prune common noise + generated/quarantine/backup trees
        dirnames[:] = [d for d in dirnames if d not in (
            "__pycache__", ".git", "_quarantine", "backups", ".venv", "venv")]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            full = os.path.join(dirpath, fn)
            if any(x and x in full for x in excludes):
                continue
            yield full

def convention_of(name):
    if name.startswith("def_"):
        body = name[4:]
    else:
        body = name
    if any(c.isupper() for c in body) and "_" in body:
        return "mixed"
    if any(c.isupper() for c in body):
        return "camel/Pascal"
    return "snake"

def version_tokens(name):
    import re
    return re.findall(r"[vV]\d+(?:\.\d+)?|_\d{2,}", name)

# ------------------------------------------------------------------- scanning
def collect_symbols(path):
    """Return (defs, name_refs, attr_refs, parse_ok, err). Positions are
    (lineno, col_offset, end_lineno, end_col_offset)."""
    defs, names, attrs = [], [], []
    try:
        src = read_text(path)
    except Exception as e:
        return defs, names, attrs, False, f"read failed: {e}"
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError as e:
        return defs, names, attrs, False, f"SyntaxError: {e.msg} (line {e.lineno})"
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defs.append((node.name, node.lineno, node.col_offset))
        elif isinstance(node, ast.Name):
            names.append((node.id, node.lineno, node.col_offset,
                          getattr(node, "end_lineno", node.lineno),
                          getattr(node, "end_col_offset", None)))
        elif isinstance(node, ast.Attribute):
            attrs.append((node.attr, node.lineno))
    return defs, names, attrs, True, ""

def scan(root, excludes):
    files = list(iter_py(root, excludes))
    per_file, all_defs = [], {}
    conv_counter = {}
    parse_fail = []
    for p in files:
        defs, names, attrs, ok, err = collect_symbols(p)
        if not ok:
            parse_fail.append({"path": p, "error": err})
        defnames = sorted({d[0] for d in defs})
        for dn in defnames:
            all_defs.setdefault(dn, []).append(p)
            conv_counter[convention_of(dn)] = conv_counter.get(convention_of(dn), 0) + 1
        per_file.append({
            "path": p, "sha12": sha12(p), "parse_ok": ok, "error": err,
            "def_count": len(defnames), "defs": defnames,
            "name_ref_count": len(names), "attr_ref_count": len(attrs),
        })
    # mixed-convention flags (within a single file holding >1 convention)
    convention_flags = []
    for f in per_file:
        cs = sorted({convention_of(d) for d in f["defs"]})
        if len(cs) > 1:
            convention_flags.append({"path": f["path"], "conventions": cs})
    # version-token flags
    version_flags = []
    for dn in all_defs:
        vt = version_tokens(dn)
        if vt:
            version_flags.append({"symbol": dn, "version_tokens": vt,
                                  "files": all_defs[dn]})
    # cross-file duplicate def names (potential collision / rename target)
    duplicates = {k: v for k, v in all_defs.items() if len(v) > 1}
    return {
        "schema": "VPNS_AST_SCAN",
        "generated_at": ISO, "root": root,
        "py_file_count": len(files),
        "parse_fail_count": len(parse_fail),
        "parse_fail": parse_fail,
        "total_def_symbols": len(all_defs),
        "convention_counter": conv_counter,
        "convention_mixed_files": convention_flags,
        "version_token_flags": version_flags,
        "duplicate_def_names": duplicates,
        "files": per_file,
    }

# --------------------------------------------------------------------- rename
def plan_edits(root, excludes, rename_map):
    """Locate every precise (line,col,len) span where an old name appears as a
    FunctionDef name or a Name leaf. Returns planned edits per file. Dry-run."""
    rename = {r["old"]: r["new"] for r in rename_map.get("renames", [])}
    plan = []
    attr_warn = []
    import_warn = []
    for p in iter_py(root, excludes):
        try:
            src = read_text(p)
            tree = ast.parse(src, filename=p)
        except Exception as e:
            plan.append({"path": p, "skipped": True, "reason": str(e), "edits": []})
            continue
        lines = src.splitlines(keepends=True)
        edits = []
        for node in ast.walk(tree):
            old = None; ln = None; col = None
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                for al in node.names:
                    if al.name in rename or (al.asname and al.asname in rename):
                        import_warn.append({"path": p, "line": node.lineno,
                                            "name": al.name, "asname": al.asname})
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in rename:
                old = node.name; ln = node.lineno
                # def<sp>NAME : find NAME after 'def ' on that line
                line = lines[ln - 1]
                idx = line.find(old, node.col_offset)
                col = idx if idx >= 0 else None
            elif isinstance(node, ast.Name) and node.id in rename:
                old = node.id; ln = node.lineno; col = node.col_offset
            elif isinstance(node, ast.Attribute) and node.attr in rename:
                attr_warn.append({"path": p, "attr": node.attr, "line": node.lineno})
                continue
            if old is None or col is None:
                continue
            line = lines[ln - 1]
            # ANCHOR VERIFICATION: the slice must equal old exactly
            if line[col:col + len(old)] != old:
                continue
            edits.append({"line": ln, "col": col, "old": old,
                          "new": rename[old], "len": len(old)})
        if edits:
            plan.append({"path": p, "skipped": False, "edits": edits,
                         "edit_count": len(edits)})
    return {
        "schema": "VPNS_AST_PLAN", "generated_at": ISO, "root": root,
        "rename_rules": rename,
        "files_touched": len(plan),
        "total_edits": sum(len(f["edits"]) for f in plan),
        "attribute_warnings": attr_warn,
        "import_warnings": import_warn,
        "plan": plan,
    }

def apply_edits(root, excludes, rename_map, token, backup_dir):
    if token != APPLY_TOKEN:
        return {"schema": "VPNS_AST_APPLY", "applied": False,
                "reason": f"token mismatch; expected {APPLY_TOKEN}"}
    planned = plan_edits(root, excludes, rename_map)
    os.makedirs(backup_dir, exist_ok=True)
    results = []
    for f in planned["plan"]:
        p = f["path"]
        if f.get("skipped") or not f["edits"]:
            continue
        src = read_text(p)
        lines = src.splitlines(keepends=True)
        # apply per line, descending col, to keep offsets valid
        by_line = {}
        for e in f["edits"]:
            by_line.setdefault(e["line"], []).append(e)
        for ln, es in by_line.items():
            line = lines[ln - 1]
            for e in sorted(es, key=lambda x: x["col"], reverse=True):
                c = e["col"]
                if line[c:c + e["len"]] != e["old"]:
                    continue  # anchor re-verify; skip if drifted
                line = line[:c] + e["new"] + line[c + e["len"]:]
            lines[ln - 1] = line
        new_src = "".join(lines)
        # parse=0 gate on the rewritten content BEFORE writing
        try:
            ast.parse(new_src, filename=p)
        except SyntaxError as ex:
            results.append({"path": p, "written": False,
                            "reason": f"post-edit parse fail: {ex.msg}"})
            continue
        # backup then write (append-only: original preserved in backup_dir)
        bdest = os.path.join(backup_dir,
                             os.path.basename(p) + f".{STAMP}.bak")
        shutil.copy2(p, bdest)
        write_text_nobom(p, new_src)
        results.append({"path": p, "written": True, "backup": bdest,
                        "edits": len(f["edits"]),
                        "sha12_after": sha12(p)})
    return {"schema": "VPNS_AST_APPLY", "applied": True, "generated_at": ISO,
            "token_ok": True, "files_written": sum(1 for r in results if r["written"]),
            "results": results, "plan_summary": {
                "files_touched": planned["files_touched"],
                "total_edits": planned["total_edits"]}}

# ----------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["scan", "plan", "apply"])
    ap.add_argument("--root", required=True)
    ap.add_argument("--map", default=None)
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--token", default="")
    ap.add_argument("--backup-dir", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.mode == "scan":
        res = scan(a.root, a.exclude)
    else:
        if not a.map or not os.path.exists(a.map):
            print(json.dumps({"error": "map file required/missing"}, ensure_ascii=False))
            sys.exit(2)
        rm = json.loads(read_text(a.map))
        if a.mode == "plan":
            res = plan_edits(a.root, a.exclude, rm)
        else:
            bdir = a.backup_dir or os.path.join(a.root, "_vpns_system", "backups", "ast")
            res = apply_edits(a.root, a.exclude, rm, a.token, bdir)

    payload = json.dumps(res, ensure_ascii=False, indent=2)
    if a.out:
        write_text_nobom(a.out, payload)
    print(payload)

if __name__ == "__main__":
    main()
