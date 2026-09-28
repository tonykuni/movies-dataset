#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL233_ToolActivate v0100 — 兩件工具的版本固定與啟用閘(只有 VCGC 能啟用)

操作員 2026-09-28:「透過VCGC才能啟用」「全部接新的透過VCGC註冊導入」「VDF引擎加入網路工具版本固定」。
在這之前,加速器與網路工具是「尾版律取最新檔」:任何人往夾裡放一支版號更大的檔,下一個行程就掛上它
——沒經過 VCGC,也沒過任何檢查。本支把「哪一版在用」改成**鎖冊說了算**:

  pinned(family)   鎖冊 VIA_ToolVersion_Lock_v*(尾版)指定的那一支。啟動層(bootstrap/sitecustomize ④)、
                   網路載入器 SUP_MDL740、加速器載入器 SUP_MDL737、加速器控管 CGC_MDL156 都問這一個函式
                   (L05 一把尺);鎖冊讀不到或指的檔不在 → 回 None,各載入器才退回原本的尾版律。
  status           兩件工具:鎖指哪支 · 位元是否等於鎖上的 sha · 夾裡有沒有已登錄但未啟用的新版。
  activate <family> <file> [--apply]
                   先驗:檔在該在的夾 · 名稱帶四位版號 · AST 剖析過 · 零 TA-Lib(L50)· 帶加速器橋 ·
                   不在匯入層開子行程/裝套件/載二進位 · 公開名稱不少於現役那一支 · 必備 API 在 · 冊上已登錄。
                   全過才出計畫;加 --apply 才寫:鎖(舊版記進 previous)· 冊的 engine 列 · 兩本名冊 v0101。
                   不刪任何檔(L10 刪除是操作員的手;舊版引用歸零後另印 git rm)。
只收 VCGC 呼叫(VIA_FROM_VCGC=YES)。零網路 · 不安裝 · 不執行被啟用的檔(只做 AST)。

用法(經 VCGC):
  via-vcgc tools
  via-vcgc tools activate network VeritasAegisNexus_v1651.py            乾跑:只驗、只印計畫
  via-vcgc tools activate network VeritasAegisNexus_v1651.py --apply    寫鎖與冊
  python CGC_MDL233_ToolActivate_v0100.py --selftest
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

import ast
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPO = VIA.parent
SUPP = VIA / "supportive modules"
ENGINE = Path(__file__).stem

#: family → (stem, folder, required public names, roster fields)
FAMILIES = {
    "accelerator": ("VeritasCeleritas", SUPP, ("get_available_libs", "get_missing_libs", "_LIB_MAP"),
                    (("VIA_Accelerator_Roster_SSOT", "control_plane", "fetch_mount"),)),
    "network": ("VeritasAegisNexus", SUPP / "network",
                ("fetch_json", "fetch_text", "ComplianceReactor", "compliance_status_report", "net_status_report"),
                (("VIA_Accelerator_Roster_SSOT", "control_plane", "network_mount"),)),
}
VERSIONED = re.compile(r"_v(\d{4})\.py$")
TALIB = re.compile(r"(?im)^\s*(?:import\s+talib\b|from\s+talib\s+import\b)|_si\(\s*['\"]talib['\"]\s*\)")
IMPORT_TIME_FORBIDDEN = ("subprocess", "ctypes", "os.system", "pip install")


def _vnum(path: Path) -> int:
    match = re.search(r"_v(\d+)$", path.stem)
    return int(match.group(1)) if match else -1


def _newest(folder: Path, pattern: str) -> Path | None:
    hits = [p for p in folder.glob(pattern) if re.search(r"_v\d+$", p.stem)]
    return max(hits, key=_vnum) if hits else None


def lock_path(root: Path | None = None) -> Path | None:
    return _newest((root or HERE), "VIA_ToolVersion_Lock_v*.json")


def _json(path: Path | None) -> dict:
    if not path or not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _sha(path: Path) -> tuple:
    raw = path.read_bytes()
    return hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(), len(raw)


def pinned(family: str, root: Path | None = None) -> Path | None:
    """The file the lock book names for this family, if it is there. The one ruler every loader asks."""
    ent = _json(lock_path(root)).get(family) or {}
    rel = str(ent.get("path") or "")
    if not rel:
        return None
    p = REPO / rel
    return p if p.is_file() else None


def _public(tree: ast.Module) -> set:
    names = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, ast.Assign):
            names.update(t.id for t in n.targets if isinstance(t, ast.Name))
    return names


def _import_time_calls(tree: ast.Module) -> list:
    """Top-level statements (not inside a def/class) that start a process, install, or load a binary."""
    bad = []
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for sub in ast.walk(n):
            if isinstance(sub, ast.Call):
                text = ast.unparse(sub.func)
                if any(k in text for k in ("subprocess", "ctypes", "os.system", "Popen")):
                    bad.append(f"L{sub.lineno} {text}")
            elif isinstance(sub, ast.Constant) and isinstance(sub.value, str) and "pip install" in sub.value.lower():
                bad.append(f"L{sub.lineno} pip install 字串")
    return bad


def _is_forwarding_tail(tree: ast.Module) -> bool:
    return any(isinstance(n, ast.FunctionDef) and n.name == "__getattr__" for n in tree.body)


def _has_engine_version(tree: ast.Module) -> bool:
    return any(isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "ENGINE_VERSION" for t in n.targets)
               for n in tree.body)


def _body_of(path: Path) -> Path:
    """A thin versioned tail runs on a body; APIs are compared on the body.
    with_name('X.py') names it directly; otherwise a forwarding tail runs on the newest lower-version
    same-stem file that is a concrete body (top-level ENGINE_VERSION) — the rule v1652 uses itself."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"with_name\(\s*['\"]([A-Za-z]+\.py)['\"]", text)
    if m and path.with_name(m.group(1)).is_file():
        return path.with_name(m.group(1))
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return path
    if not _is_forwarding_tail(tree):
        return path
    stem = path.stem.rsplit("_v", 1)[0]
    for cand in sorted(path.parent.glob(stem + "_v*.py"), key=_vnum, reverse=True):
        if not 0 <= _vnum(cand) < _vnum(path):
            continue
        try:
            if _has_engine_version(ast.parse(cand.read_text(encoding="utf-8", errors="replace"))):
                return cand
        except SyntaxError:
            BODY_UNREADABLE.append(cand.name)
    return path


BODY_UNREADABLE: list = []


def _api(path: Path) -> set:
    """Public names reachable on this file: its own, plus its body's when it forwards."""
    names = _public(ast.parse(path.read_text(encoding="utf-8", errors="replace")))
    body = _body_of(path)
    if body != path:
        names |= _public(ast.parse(body.read_text(encoding="utf-8", errors="replace")))
    return names


def param_tables(path: Path) -> dict:
    """Literal parameter tables (SSOT / regex / synonym style): module- and class-level literals, and the
    pattern string of every X = re.compile("...")."""
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    out = {}
    scopes = [("", tree.body)] + [(c.name + ".", c.body) for c in tree.body if isinstance(c, ast.ClassDef)]
    for prefix, body in scopes:
        for n in body:
            if not isinstance(n, (ast.Assign, ast.AnnAssign)) or getattr(n, "value", None) is None:
                continue
            targets = [t for t in (n.targets if isinstance(n, ast.Assign) else [n.target]) if isinstance(t, ast.Name)]
            v = n.value
            if isinstance(v, ast.Call) and getattr(v.func, "attr", "") == "compile" and v.args \
                    and isinstance(v.args[0], ast.Constant):
                out.update({prefix + t.id + "#regex": v.args[0].value for t in targets})
                continue
            try:
                val = ast.literal_eval(v)
            except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
                val = None                                  # not a literal table: not a parameter here
            if isinstance(val, (dict, list, tuple, set, frozenset, str)):
                out.update({prefix + t.id: val for t in targets})
    return out


def param_diff(old, new, path: str = "") -> tuple:
    """(lost, conflict): every old key / element must still be there; same key with another value = conflict."""
    lost, conflict = [], []
    if isinstance(old, dict):
        if not isinstance(new, dict):
            return [], [path]
        for k, v in old.items():
            if k not in new:
                lost.append(f"{path}[{k!r}]")
            else:
                sub_lost, sub_conf = param_diff(v, new[k], f"{path}[{k!r}]")
                lost += sub_lost
                conflict += sub_conf
    elif isinstance(old, (list, tuple, set, frozenset)):
        if not isinstance(new, (list, tuple, set, frozenset)):
            return [], [path]
        pool = list(new)
        lost += [f"{path}<{str(e)[:40]}>" for e in old if e not in pool]
    elif old != new:
        conflict.append(path)
    return lost, conflict


def params_superset(old_path: Path, new_path: Path) -> dict:
    old, new = param_tables(old_path), param_tables(new_path)
    lost = [k for k in old if k not in new]
    conflict = []
    for k in old:
        if k in new:
            sub_lost, sub_conf = param_diff(old[k], new[k], k)
            lost += sub_lost
            conflict += sub_conf
    return {"old": len(old), "new": len(new), "lost": lost, "conflict": conflict}


def checks(family: str, file_name: str, register: dict | None = None, root: Path | None = None) -> list:
    stem, folder, required, _rost = FAMILIES[family]
    cand = folder / file_name
    out = []

    def chk(name, ok, detail=""):
        out.append({"check": name, "ok": bool(ok), "detail": str(detail)})

    chk("檔在該在的夾", cand.is_file(), str(cand.relative_to(VIA)) if cand.is_file() else f"不在 {folder.name}/")
    chk("名稱帶四位版號(尾版律 · 可登錄)", cand.name.startswith(stem + "_v") and VERSIONED.search(cand.name), cand.name)
    if not cand.is_file():
        return out
    text = cand.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text)
        chk("AST 剖析過", True)
    except SyntaxError as exc:
        chk("AST 剖析過", False, f"L{exc.lineno} {exc.msg}")
        return out
    chk("零 TA-Lib(L50 第一條)", TALIB.search(text) is None)
    chk("帶加速器橋 [VIA:ACCEL-BRIDGE]", "[VIA:ACCEL-BRIDGE" in text)
    bad = _import_time_calls(tree)
    chk("匯入層不開子行程 · 不裝套件 · 不載二進位", not bad, "; ".join(bad[:4]))
    names = _api(cand)
    miss_req = [n for n in required if n not in names]
    chk("必備 API 在(載入器與控管會叫的名字)", not miss_req, ", ".join(miss_req) or ", ".join(required))
    current = pinned(family, root)
    if current and current.resolve() != cand.resolve():
        base = _body_of(current)
        try:
            old = {n for n in _public(ast.parse(base.read_text(encoding="utf-8", errors="replace"))) if not n.startswith("_")}
            lost = sorted(n for n in old if n not in names)
            chk(f"公開名稱不少於現役({base.name})", not lost, ", ".join(lost[:12]) or f"{len(old)} 個全在")
        except SyntaxError:
            chk(f"公開名稱不少於現役({base.name})", False, "現役本體剖析不過")
        try:
            ps = params_superset(base, _body_of(cand))
            chk("參數只增不減、不衝突(SSOT / regex / 同義字表;操作員 2026-09-28)",
                not ps["lost"] and not ps["conflict"],
                f"舊 {ps['old']} 張 → 新 {ps['new']} 張 · 少 {len(ps['lost'])} · 衝突 {len(ps['conflict'])} "
                + "; ".join((ps["lost"] + ps["conflict"])[:6]))
        except SyntaxError:
            chk("參數只增不減、不衝突(SSOT / regex / 同義字表;操作員 2026-09-28)", False, "剖析不過")
    reg = register if register is not None else _json(HERE / "VIA_EngineVersion_Register_v0100.json")
    row = next((r for r in reg.get("rows") or [] if r.get("file") == cand.name), None)
    chk("冊上已登錄(VCGC 工具號)", row is not None, row.get("code") if row else "未登錄")
    return out


def status(root: Path | None = None) -> dict:
    lock = _json(lock_path(root))
    rows = []
    for fam, (stem, folder, _req, _r) in FAMILIES.items():
        ent = lock.get(fam) or {}
        p = pinned(fam, root)
        sha_ok = None
        if p:
            a, b, _n = _sha(p)
            sha_ok = ent.get("sha256") in (a, b)
        newer = sorted(q.name for q in folder.glob(stem + "_v*.py")
                       if VERSIONED.search(q.name) and p and _vnum(q) > _vnum(p))
        rows.append({"family": fam, "pinned": p.name if p else "ABSENT", "version": ent.get("version"),
                     "sha_ok": sha_ok, "waiting": newer})
    return {"via": "vcgc", "door": ENGINE, "lock": lock_path(root).name if lock_path(root) else "ABSENT", "tools": rows,
            "next": "none" if all(r["sha_ok"] for r in rows) else "do not unlock; name the drift"}


def plan(family: str, file_name: str) -> dict:
    stem, folder, _req, rosters = FAMILIES[family]
    cand = folder / file_name
    res = checks(family, file_name)
    ok = all(c["ok"] for c in res)
    out = {"via": "vcgc", "door": ENGINE, "family": family, "file": file_name, "checks": res, "ok": ok}
    if not ok:
        out["next"] = "do not activate; name the failed checks"
        return out
    a, _b, n = _sha(cand)
    out["writes"] = {
        "lock": {"version": "v" + VERSIONED.search(file_name).group(1),
                 "path": str(cand.relative_to(REPO)).replace("\\", "/"), "sha256": a, "bytes": n},
        "register_engine_row": file_name,
        "rosters": [f"{r[0]}_v*.json {r[1]}.{r[2]}" for r in rosters] + (["VIA_ToolRoster_SSOT_v*.json accelerator_control.network_tools"]),
    }
    out["next"] = "run again with --apply (VCGC) to write"
    return out


def apply(family: str, file_name: str, why: str) -> dict:
    p = plan(family, file_name)
    if not p["ok"]:
        return p
    stem, folder, _req, rosters = FAMILIES[family]
    w = p["writes"]
    lp = lock_path()
    lock = _json(lp)
    prev = lock.get(family) or {}
    same = prev.get("path") == w["lock"]["path"]          # re-activation of the same file (new bytes): keep the real previous
    previous = (prev.get("previous") if same else
                {"version": prev.get("version"), "path": prev.get("path"), "sha256": prev.get("sha256")})
    lock[family] = dict(w["lock"], why=why, activated_by="VCGC " + ENGINE, previous=previous)
    lp.write_text(json.dumps(lock, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="")
    reg_p = HERE / "VIA_EngineVersion_Register_v0100.json"
    reg_text = reg_p.read_text(encoding="utf-8")
    reg = json.loads(reg_text)
    old_eng = next((r for r in reg["rows"] if r.get("family") == family and r.get("role") == "engine"), None)
    if old_eng and old_eng["file"] != file_name:
        old_rel = old_eng["path"]
        new_rel = str((folder / file_name).relative_to(VIA)).replace("\\", "/")
        reg_text = reg_text.replace(f'"file": "{old_eng["file"]}",\n      "path": "{old_rel}",',
                                    f'"file": "{file_name}",\n      "path": "{new_rel}",', 1)
        json.loads(reg_text)
        reg_p.write_text(reg_text, encoding="utf-8", newline="")
    prev_name = Path(str(prev.get("path") or "")).name
    touched = []
    for glob in ("VIA_Accelerator_Roster_SSOT_v*.json", "VIA_ToolRoster_SSOT_v*.json"):
        rp = _newest(HERE, glob)
        if rp and prev_name:
            t = rp.read_text(encoding="utf-8")
            if prev_name in t:
                t = t.replace(prev_name, file_name)
                json.loads(t)
                rp.write_text(t, encoding="utf-8", newline="")
                touched.append(rp.name)
    p["applied"] = {"lock": lp.name, "register": reg_p.name, "rosters": touched, "previous": prev.get("version")}
    p["next"] = "none"
    return p


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    if args and args[0] == "activate":
        if len(args) < 3 or args[1] not in FAMILIES:
            print(json.dumps({"state": "USAGE", "use": "activate <accelerator|network> <file> [--apply]"}, ensure_ascii=False))
            return 2
        fam, name = args[1], args[2]
        why = next((a.split("=", 1)[1] for a in args if a.startswith("--why=")), "VCGC activation")
        card = apply(fam, name, why) if "--apply" in args else plan(fam, name)
        print(json.dumps(card, ensure_ascii=False, indent=1))
        return 0 if card.get("ok") else 2
    card = status()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["next"] == "none" else 2


def selftest() -> int:
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    keep = os.environ.pop("VIA_FROM_VCGC", None)
    chk("① 沒從 VCGC 進就拒(status / activate 都一樣)",
        main([]) == 2 and main(["activate", "network", "x.py", "--apply"]) == 2)
    if keep is not None:
        os.environ["VIA_FROM_VCGC"] = keep
    st = status()
    chk("② 兩件工具都有鎖、鎖指的檔在、位元等於鎖上 sha", st["next"] == "none",
        " · ".join(f"{r['family']}={r['pinned']} sha_ok={r['sha_ok']} 待啟用={r['waiting']}" for r in st["tools"]))
    for fam in FAMILIES:
        p = pinned(fam)
        chk(f"③ pinned({fam}) 是帶版號的檔", bool(p) and VERSIONED.search(p.name), p.name if p else "None")
    bad = checks("network", "VeritasAegisNexus.py", register={"rows": []})
    chk("④ 負控:無版號檔 · 未登錄 → 不得啟用", not all(c["ok"] for c in bad),
        "; ".join(c["check"] for c in bad if not c["ok"]))
    miss = checks("network", "VeritasAegisNexus_v9999.py")
    chk("⑤ 負控:檔不在 → 不得啟用", not all(c["ok"] for c in miss))
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        o, n1, n2 = Path(td) / "o.py", Path(td) / "n1.py", Path(td) / "n2.py"
        o.write_text("T = {'a': 1, 'b': [1, 2]}\nR = re.compile('x+')\n", encoding="utf-8")
        n1.write_text("T = {'a': 1, 'b': [1, 2, 3], 'c': 9}\nR = re.compile('x+')\nNEW = (1,)\n", encoding="utf-8")
        n2.write_text("T = {'a': 2, 'b': [2]}\n", encoding="utf-8")
        good, bad = params_superset(o, n1), params_superset(o, n2)
    chk("⑦ 參數只增不減:多了照過;少了鍵/元素、同鍵異值、regex 不見 → 指名擋下",
        not good["lost"] and not good["conflict"] and bad["conflict"] == ["T['a']"] and len(bad["lost"]) == 2,
        f"lost={bad['lost']} conflict={bad['conflict']}")
    tree = ast.parse("import subprocess\nsubprocess.run(['pip','install','x'])\ndef f():\n    subprocess.run([])\n")
    chk("⑥ 匯入層開子行程會被指出(函式裡的不算匯入層)", len(_import_time_calls(tree)) == 1, str(_import_time_calls(tree)))
    ok = all(results)
    print(f"  {ENGINE} selftest {sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
