#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_SystemManager v0132 — 薄尾:功能矩陣自創自管(操作員令 2026-10-06:每個系統建立功能矩陣掌控各功能;MDL/ENG/CLS/FNC/LIB 一旦登錄只增不減,
除非衝突裁定或工具無人維護才可退役,且必有替代版本;AST 從頭注入到尾登錄;相似 = 黃燈提醒非紅燈)。
  fn register [--apply]                 AST 掃 VDF 尾版 .py → 登記 registry/VDF_FunctionMatrix_v0100.json(number 留白;NEW/SAME/UPDATED+history/GONE 不刪)
  fn status                             矩陣計:各類數 · 留白 · 相似提醒 · GONE · AST 失敗
  fn retire <key> --replaced-by <key> --reason <衝突裁定|無人維護>   唯一退役路徑(標 RETIRED,不物理刪;缺替代或理由 = 拒)
  fn number pull                        依鍵 VDF|<key>|<version> 從母系統 VIA_RegistryNumbers_v*.json 讀號填回
其餘動詞照前版鏈(v0131 table · v0130 refill …);在本行程呼叫,不經 VCGC 也能跑。沙盒鍵:VIA_VDF_HOME · VIA_VDF_CENTRAL;VIA_SKIP_PRIOR_SELFTEST=1 沙盒跳過前版鏈自測。
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_SystemManager"
TAG = "v0132"


def _vnum_v0132(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0132(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0132(p) < _vnum_v0132(__file__)), key=_vnum_v0132)
PRIOR = _load_v0132(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


# ===== [VIA:FN-MATRIX:v0100] 功能矩陣共用段(AST 從頭到尾;子系統自創自管;只增不減;相似 = 黃燈提醒;三系統各帶一份,零相依)=====
_FM_EXCL = {"references", "intake", "_superseded", "VIA_RetiredEngines", "_quarantine_pip_vendor", "__pycache__", ".venv", "venv", "node_modules", "_quarantine", "VIA_NumberBooks", "_df"}
_FM_LOCAL = __import__("re").compile(r"^(VIA|via|VRN|vrn|VDF|vdf|CGC|SUP|VAP|GIF|VRM|_sa_|_nb_)")


def _fm_vnum(name):
    import re as _re
    m = _re.search(r"_v(\d{2,4})[A-Za-z0-9]*(?:\.[A-Za-z0-9]+)?$", name)
    return int(m.group(1)) if m else -1


def _fm_ver(name):
    import re as _re
    m = _re.search(r"_(v\d{2,4}[A-Za-z0-9]*)(?:\.[A-Za-z0-9]+)?$", name)
    return m.group(1) if m else "v0000"


def _fm_family(name):
    import re as _re
    from pathlib import Path as _P
    return _re.sub(r"_v\d{2,4}[A-Za-z0-9]*$", "", _re.sub(r"_sha[0-9a-f]{8,}$", "", _P(name).stem))


def _fm_read(p):
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "utf-16", "cp950"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return ""


def _fm_tails(dirs, root):
    best = {}
    for d in dirs:
        if not d.is_dir():
            continue
        for p in d.rglob("*.py"):
            if not p.is_file():
                continue
            try:
                parts = set(p.relative_to(root).parts[:-1])
            except ValueError:
                parts = set(p.parts)
            if parts & _FM_EXCL:
                continue
            k = (p.parent, _fm_family(p.name))
            v = _fm_vnum(p.name)
            if k not in best or v > best[k][0]:
                best[k] = (v, p)
    return sorted((v[1] for v in best.values()), key=lambda q: str(q))


def _fm_body_sha(node):
    import ast as _ast
    import hashlib as _h
    try:
        s = _ast.dump(node, annotate_fields=False, include_attributes=False)
    except Exception:  # noqa: BLE001
        s = repr(node)
    return _h.sha256(s.encode("utf-8", "replace")).hexdigest()[:16]


def _fm_sig(fn):
    import ast as _ast
    a = fn.args
    names = [x.arg for x in a.posonlyargs] + [x.arg for x in a.args]
    if a.vararg:
        names.append("*" + a.vararg.arg)
    names += [x.arg for x in a.kwonlyargs]
    if a.kwarg:
        names.append("**" + a.kwarg.arg)
    return "%s(%s)" % (fn.name, ", ".join(names))


def _fm_scan_file(p, root, sub):
    """一支 .py → items 列表(MDL/ENG 一列 · CLS 每類一列 · FNC 每函式/方法一列 · LIB 每第三方套件一列)。AST 失敗 = 該檔 MDL 列帶 issue,不紅。"""
    import ast as _ast
    import hashlib as _h
    import sys as _sys
    txt = _fm_read(p)
    rel = p.relative_to(root).as_posix() if str(p).startswith(str(root)) else p.as_posix()
    fam, ver = _fm_family(p.name), _fm_ver(p.name)
    kind = "ENG" if ("_ENG" in fam or "Engine" in fam or fam.lower().endswith("engine")) else "MDL"
    base = {"sub": sub, "module": fam, "version": ver, "source": rel}
    items = [dict(base, kind=kind, name=fam, key="%s|%s" % (kind, fam), lines=txt.count("\n") + 1,
                  body_sha=_h.sha256(txt.encode("utf-8", "replace")).hexdigest()[:16], accel=("[VIA:ACCEL-BRIDGE" in txt), issues=[])]
    try:
        tree = _ast.parse(txt)
    except (SyntaxError, ValueError) as exc:
        items[0]["issues"].append("AST 失敗 %s L%s" % (type(exc).__name__, getattr(exc, "lineno", "?")))
        return items
    std = set(getattr(_sys, "stdlib_module_names", ()))
    libs = set()
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Import):
            for al in node.names:
                libs.add(al.name.split(".")[0])
        elif isinstance(node, _ast.ImportFrom) and node.module and node.level == 0:
            libs.add(node.module.split(".")[0])
    for lib in sorted(libs):
        if lib in std or _FM_LOCAL.match(lib):
            continue
        items.append(dict(base, kind="LIB", name=lib, key="LIB|%s" % lib, api="import %s" % lib, body_sha="", issues=[]))
    for node in tree.body:
        if isinstance(node, _ast.ClassDef):
            bases = [getattr(b, "id", getattr(b, "attr", "?")) for b in node.bases]
            items.append(dict(base, kind="CLS", name=node.name, key="CLS|%s|%s" % (fam, node.name), api="class %s(%s)" % (node.name, ", ".join(bases)),
                              line=node.lineno, body_sha=_fm_body_sha(node), methods=sum(1 for n in node.body if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef))), issues=[]))
            for n in node.body:
                if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                    q = "%s.%s" % (node.name, n.name)
                    items.append(dict(base, kind="FNC", name=q, key="FNC|%s|%s" % (fam, q), api=_fm_sig(n), line=n.lineno, body_sha=_fm_body_sha(n),
                                      doc=(_ast.get_docstring(n) or "").split("\n")[0][:80], issues=[]))
        elif isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            items.append(dict(base, kind="FNC", name=node.name, key="FNC|%s|%s" % (fam, node.name), api=_fm_sig(node), line=node.lineno, body_sha=_fm_body_sha(node),
                              doc=(_ast.get_docstring(node) or "").split("\n")[0][:80], issues=[]))
    return items


def _fm_similar(items):
    """相似提醒(黃,不紅):同名 FNC/CLS 散在 ≥2 模組 · 同 body 異名/異模組 · 同 LIB 多模組不算。→ {key: [提醒]}"""
    from collections import defaultdict as _dd
    by_name, by_body = _dd(list), _dd(list)
    for it in items:
        if it["kind"] in ("FNC", "CLS"):
            short = it["name"].split(".")[-1]
            if not short.startswith("_") and short not in ("main", "selftest", "chk", "__getattr__", "run", "check", "load", "build", "emit", "scan"):
                by_name[(it["kind"], short)].append(it["key"])
            if it.get("body_sha"):
                by_body[(it["kind"], it["body_sha"])].append(it["key"])
    rem = _dd(list)
    for (k, nm), keys in by_name.items():
        mods = {x.split("|")[1] for x in keys}
        if len(mods) >= 2:
            for x in keys:
                rem[x].append("同名 %s 散在 %d 模組" % (nm, len(mods)))
    for (k, sha), keys in by_body.items():
        if len(keys) >= 2 and len({x.split("|")[1] for x in keys}) >= 2:
            for x in keys:
                rem[x].append("同 body 另見 %d 處(候選共用 LIB)" % (len(keys) - 1))
    return dict(rem)


def _fm_register(sub, dirs, root, book_dir, now, apply=True):
    """掃尾版 .py → 登記 <sub>_FunctionMatrix_v0100.json(只增:新=NEW · 同=SAME · 改 body=UPDATED+history · 樹上不見=GONE(不刪,gone_since)· 刪除只能 fn retire 帶 replaced_by)。"""
    import json as _json
    from pathlib import Path as _P
    hits = sorted(_P(book_dir).glob(sub + "_FunctionMatrix_v*.json"), key=lambda q: _fm_vnum(q.name))
    if hits:
        book = _json.loads(_fm_read(hits[-1]))
        fp = hits[-1]
    else:
        fp = _P(book_dir) / (sub + "_FunctionMatrix_v0100.json")
        book = {"schema": "VIA.FunctionMatrix.v1", "sub": sub, "version": "v0100", "created_at": now,
                "rule": "子系統自創自管(L114 ①);AST 從頭到尾登錄 MDL/ENG/CLS/FNC/LIB;只增不減:樹上不見 = GONE 不刪;刪除只限 (a) 衝突裁定 (b) 工具無人維護,且必帶 replaced_by;相似 = 黃燈提醒不紅;number 留白待母系統",
                "items": {}}
    items_all = []
    for p in _fm_tails(dirs, root):
        items_all += _fm_scan_file(p, root, sub)
    sim = _fm_similar(items_all)
    bk = book.setdefault("items", {})
    seen = set()
    counts = {"NEW": 0, "SAME": 0, "UPDATED": 0, "GONE": 0, "BACK": 0}
    for it in items_all:
        k = it["key"]
        seen.add(k)
        it["similar"] = sim.get(k, [])
        e = bk.get(k)
        if e is None:
            bk[k] = dict(it, status="ACTIVE", first_seen=now, last_seen=now, number="", history=[])
            counts["NEW"] += 1
        else:
            was_gone = e.get("status") == "GONE"
            if e.get("body_sha") != it.get("body_sha") or e.get("version") != it.get("version"):
                e.setdefault("history", []).append({"version": e.get("version"), "body_sha": e.get("body_sha"), "source": e.get("source"), "until": now})
                counts["UPDATED"] += 1
            else:
                counts["SAME"] += 1
            e.update({x: it[x] for x in it if x not in ("status", "first_seen", "number", "history")})
            e["status"] = "ACTIVE"
            e["last_seen"] = now
            if was_gone:
                counts["BACK"] += 1
                e.pop("gone_since", None)
    for k, e in bk.items():
        if k not in seen and e.get("status") == "ACTIVE":
            e["status"] = "GONE"
            e["gone_since"] = now
            counts["GONE"] += 1
    book["updated_at"] = now
    if apply:
        _P(book_dir).mkdir(parents=True, exist_ok=True)
        fp.write_text(_json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    kinds = {}
    for e in bk.values():
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    return {"book": fp.name, "items": len(bk), "kinds": kinds, "counts": counts, "similar": sum(1 for e in bk.values() if e.get("similar")),
            "gone": sum(1 for e in bk.values() if e.get("status") == "GONE"), "ast_fail": sum(1 for e in bk.values() if any("AST" in x for x in e.get("issues", []))),
            "blank": sum(1 for e in bk.values() if e.get("status") == "ACTIVE" and not e.get("number"))}


def _fm_retire(sub, book_dir, key, replaced_by, reason, now, apply=True):
    """唯一能把列移出 ACTIVE/GONE 的動作:要 replaced_by(替代版本)與 reason(衝突裁定 / 無人維護);不物理刪,標 RETIRED。"""
    import json as _json
    from pathlib import Path as _P
    hits = sorted(_P(book_dir).glob(sub + "_FunctionMatrix_v*.json"), key=lambda q: _fm_vnum(q.name))
    if not hits:
        return {"status": "NO_BOOK"}
    book = _json.loads(_fm_read(hits[-1]))
    e = book.get("items", {}).get(key)
    if not e:
        return {"status": "NO_KEY"}
    if not replaced_by or not reason:
        return {"status": "REFUSED", "why": "退役必帶 replaced_by 與 reason(衝突裁定 / 無人維護)"}
    if replaced_by not in book["items"]:
        return {"status": "REFUSED", "why": "replaced_by 不在矩陣:%s" % replaced_by}
    e.update(status="RETIRED", retired_at=now, replaced_by=replaced_by, retire_reason=reason)
    if apply:
        hits[-1].write_text(_json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"status": "RETIRED", "key": key, "replaced_by": replaced_by}


def _fm_pull(sub, book_dir, numbers_dir, now, apply=True):
    """依鍵 <sub>|<key>|<version> 從母系統 VIA_RegistryNumbers_v*.json 讀號填回(只填留白;填了即鎖)。"""
    import json as _json
    from pathlib import Path as _P
    hits = sorted(_P(book_dir).glob(sub + "_FunctionMatrix_v*.json"), key=lambda q: _fm_vnum(q.name))
    if not hits:
        return {"status": "NO_BOOK", "filled": 0, "already": 0, "pending": 0, "lamp": "GRAY"}
    book = _json.loads(_fm_read(hits[-1]))
    nb = sorted(_P(numbers_dir).glob("VIA_RegistryNumbers_v*.json"), key=lambda q: _fm_vnum(q.name))
    table = {}
    if nb:
        try:
            d = _json.loads(_fm_read(nb[-1]))
            table = {e["key"]: e["code"] for e in d.get("entries", []) if e.get("key") and e.get("code")}
        except (ValueError, KeyError):
            pass
    filled = already = pending = 0
    for k, e in book.get("items", {}).items():
        if e.get("status") != "ACTIVE":
            continue
        if e.get("number"):
            already += 1
            continue
        code = table.get("%s|%s|%s" % (sub, k, e.get("version")))
        if code:
            e["number"] = code
            e["numbered_at"] = now
            filled += 1
        else:
            pending += 1
    if apply and filled:
        hits[-1].write_text(_json.dumps(book, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"status": "OK", "book": hits[-1].name, "number_book": (nb[-1].name if nb else None), "filled": filled, "already": already, "pending": pending,
            "lamp": "GREEN" if (pending == 0 and (filled or already)) else "GRAY"}
# ===== [VIA:FN-MATRIX:END] =====


def _now_v0132() -> str:
    import datetime
    return datetime.datetime.now().isoformat(timespec="seconds")


def _roots_v0132() -> dict:
    home = Path(os.environ.get("VIA_VDF_HOME") or HERE)
    central = Path(os.environ.get("VIA_VDF_CENTRAL") or (HERE.parents[1] / "supportive modules" / "registry"))
    root = home.parents[1] if len(home.parents) > 1 else home
    return {"home": home, "registry": home / "registry", "central": central, "root": root}


def fn_register(apply: bool = False) -> dict:
    r = _roots_v0132()
    res = _fm_register("VDF", [r["home"]], r["root"], r["registry"], _now_v0132(), apply=apply)
    res.update(verb="fn_register", apply=apply, lamp=("YELLOW" if (not apply or res["similar"] or res["ast_fail"]) else "GREEN"))
    return res


def fn_status() -> dict:
    import json
    r = _roots_v0132()
    hits = sorted(r["registry"].glob("VDF_FunctionMatrix_v*.json"), key=lambda q: _fm_vnum(q.name))
    if not hits:
        return {"verb": "fn_status", "book": None, "items": 0, "lamp": "GRAY"}
    b = json.loads(_fm_read(hits[-1]))
    it = b.get("items", {})
    kinds = {}
    for e in it.values():
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    return {"verb": "fn_status", "book": hits[-1].name, "items": len(it), "kinds": kinds, "active": sum(1 for e in it.values() if e["status"] == "ACTIVE"),
            "gone": sum(1 for e in it.values() if e["status"] == "GONE"), "retired": sum(1 for e in it.values() if e["status"] == "RETIRED"),
            "numbered": sum(1 for e in it.values() if e.get("number")), "blank": sum(1 for e in it.values() if e["status"] == "ACTIVE" and not e.get("number")),
            "similar": sum(1 for e in it.values() if e.get("similar")), "lamp": "GREEN" if it else "GRAY"}


def fn_retire(key: str, replaced_by: str, reason: str) -> dict:
    r = _roots_v0132()
    res = _fm_retire("VDF", r["registry"], key, replaced_by, reason, _now_v0132(), apply=True)
    res["verb"] = "fn_retire"
    return res


def fn_number_pull() -> dict:
    r = _roots_v0132()
    res = _fm_pull("VDF", r["registry"], r["central"], _now_v0132(), apply=True)
    res["verb"] = "fn_number_pull"
    return res


def _print_v0132(out: dict) -> None:
    v = out["verb"]
    if v == "fn_register":
        c = out["counts"]
        print("[計] fn register%s 冊 %s · 項 %d %s · NEW %d SAME %d UPDATED %d GONE %d BACK %d · 相似提醒 %d · AST 失敗 %d · 留白 %d · %s"
              % (" --apply" if out["apply"] else "(dry-run)", out["book"], out["items"], out["kinds"], c["NEW"], c["SAME"], c["UPDATED"], c["GONE"], c["BACK"], out["similar"], out["ast_fail"], out["blank"], out["lamp"]))
    elif v == "fn_status":
        print("[計] fn status · 冊 %s · 項 %d %s · ACTIVE %d GONE %d RETIRED %d · 已號 %d 留白 %d · 相似 %d · %s"
              % (out.get("book"), out.get("items", 0), out.get("kinds", {}), out.get("active", 0), out.get("gone", 0), out.get("retired", 0), out.get("numbered", 0), out.get("blank", 0), out.get("similar", 0), out["lamp"]))
    elif v == "fn_retire":
        print("[計] fn retire · %s · %s" % (out["status"], out.get("why") or out.get("key", "")))
    elif v == "fn_number_pull":
        print("[計] fn number pull · 冊 %s · 母發號冊 %s · filled %d already %d pending %d · %s" % (out.get("book"), out.get("number_book") or "未建", out["filled"], out["already"], out["pending"], out["lamp"]))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] != ["fn"]:
        return PRIOR.main(args)

    sub = args[1] if len(args) > 1 else ""
    if sub == "register":
        out = fn_register(apply=("--apply" in args))
    elif sub == "status":
        out = fn_status()
    elif sub == "retire":
        def _opt(flag):
            return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else ""
        out = fn_retire(args[2] if len(args) > 2 else "", _opt("--replaced-by"), _opt("--reason"))
    elif sub == "number" and args[2:3] == ["pull"]:
        out = fn_number_pull()
    else:
        print("[拒跑] fn register [--apply] | fn status | fn retire <key> --replaced-by <key> --reason <衝突裁定|無人維護> | fn number pull")
        return 2
    _print_v0132(out)
    return 0


def selftest() -> int:
    import json
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="vdffm-"))
    home = td / "functional modules" / "VDF"
    central = td / "supportive modules" / "registry"
    saved = {k: os.environ.get(k) for k in ("VIA_VDF_HOME", "VIA_VDF_CENTRAL", "VIA_NO_OPEN", "VIA_NO_NET", "VIA_VRN_UI_DIR")}
    os.environ.update({"VIA_VDF_HOME": str(home), "VIA_VDF_CENTRAL": str(central), "VIA_NO_OPEN": "1", "VIA_NO_NET": "1", "VIA_VRN_UI_DIR": str(td / "ui")})
    home.mkdir(parents=True)
    central.mkdir(parents=True)
    (home / "VDF_ENG001_A_v0100.py").write_text("import requests\nclass K:\n    def go(self, x):\n        return x\n\ndef helper(a, b=1):\n    return a+b\n", encoding="utf-8")
    (home / "VDF_ENG002_B_v0100.py").write_text("def helper(a, b=1):\n    return a+b\n\ndef other():\n    pass\n", encoding="utf-8")
    (home / "VDF_MDL003_Bad_v0100.py").write_text("def broken(:\n", encoding="utf-8")
    d0 = fn_register(apply=False)
    chk("① dry-run 不寫冊 · AST 從頭到尾:ENG 2 MDL 1 CLS 1 FNC 4 LIB 1 · AST 失敗 1 列黃不紅", not (home / "registry" / "VDF_FunctionMatrix_v0100.json").exists() and d0["kinds"].get("ENG") == 2 and d0["kinds"].get("MDL") == 1 and d0["kinds"].get("CLS") == 1 and d0["kinds"].get("FNC") == 4 and d0["kinds"].get("LIB") == 1 and d0["ast_fail"] == 1 and d0["lamp"] == "YELLOW")
    a1 = fn_register(apply=True)
    bk = json.loads((home / "registry" / "VDF_FunctionMatrix_v0100.json").read_text(encoding="utf-8"))
    chk("② --apply 登記 · number 全留白 · 相似提醒:helper 同名+同 body 兩處皆黃", a1["counts"]["NEW"] == d0["items"] and all(e["number"] == "" for e in bk["items"].values())
        and bk["items"]["FNC|VDF_ENG001_A|helper"]["similar"] and bk["items"]["FNC|VDF_ENG002_B|helper"]["similar"])
    (home / "VDF_ENG002_B_v0101.py").write_text("def helper(a, b=2):\n    return a*b\n", encoding="utf-8")
    a2 = fn_register(apply=True)
    bk2 = json.loads((home / "registry" / "VDF_FunctionMatrix_v0100.json").read_text(encoding="utf-8"))
    chk("③ 只增不減:新版 → UPDATED+history · other 樹上不見 → GONE 不刪(gone_since)", a2["counts"]["UPDATED"] >= 1 and bk2["items"]["FNC|VDF_ENG002_B|other"]["status"] == "GONE" and bk2["items"]["FNC|VDF_ENG002_B|other"].get("gone_since")
        and len(bk2["items"]["FNC|VDF_ENG002_B|helper"]["history"]) == 1)
    r0 = fn_retire("FNC|VDF_ENG002_B|other", "", "")
    r1 = fn_retire("FNC|VDF_ENG002_B|other", "FNC|VDF_ENG001_A|helper", "無人維護")
    bk3 = json.loads((home / "registry" / "VDF_FunctionMatrix_v0100.json").read_text(encoding="utf-8"))
    chk("④ 退役律:缺替代/理由 = 拒;帶 replaced_by+reason → RETIRED(不物理刪)", r0["status"] == "REFUSED" and r1["status"] == "RETIRED" and bk3["items"]["FNC|VDF_ENG002_B|other"]["status"] == "RETIRED" and "FNC|VDF_ENG002_B|other" in bk3["items"])
    ver = bk3["items"]["ENG|VDF_ENG001_A"]["version"]
    (central / "VIA_RegistryNumbers_v0100.json").write_text(json.dumps({"entries": [{"key": "VDF|ENG|VDF_ENG001_A|" + ver, "code": "VIA-VDF-ENG001"}]}), encoding="utf-8")
    n1 = fn_number_pull()
    bk4 = json.loads((home / "registry" / "VDF_FunctionMatrix_v0100.json").read_text(encoding="utf-8"))
    chk("⑤ 讀號:依鍵填 1 · 其餘 pending · 號出現在子系統冊", n1["filled"] == 1 and bk4["items"]["ENG|VDF_ENG001_A"]["number"] == "VIA-VDF-ENG001" and n1["pending"] >= 1)
    st = fn_status()
    chk("⑥ status 計:已號 1 · RETIRED 1 · 中央只讀(1 冊)", st["numbered"] == 1 and st["retired"] == 1 and len(list(central.glob("*"))) == 1)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 帶加速器橋 · 功能矩陣共用段 · glob 取前版", "[VIA:ACCEL-BRIDGE:v0100]" in body and "[VIA:FN-MATRIX:v0100]" in body)
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑧ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VDF_SystemManager_v0132 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
