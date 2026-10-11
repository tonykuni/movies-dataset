#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG396_AssetIndex v0100 — 智慧資產化(操作員 2026-10-11:VCGC 省 token 全景分析 · 注入 AST 分類與說明 · 加速器覆蓋 100% · 以最新最成功模組為基準往前找缺少但合規的功能 ·
   模組化 AST 定位 · 分類分群 · 不產生九頭龍 / 不傷引擎 · 註冊完畢後指令精準化 · AI 一讀就知道全貌 · PY 化 + 加速器 + 編號名稱 + 契約)。
  VES(VIA Engine Standardizer v1000 · supportive modules/references/intake)→ 有就呼叫 scan_tree / build_clusters(只讀 · 不複製)· 沒有 → 內建精簡 AST
  只讀分析 · 不改任何既有檔 · 範圍 = VRN 自己的樹(三系統獨立)· 輸出 VIA_Reports/vrn/assets/ + contract/
  [VIA:AST-CLASS] 類別 = 引擎(智慧資產化)· 入口 = VRN_SystemManager assetize 動詞
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import ast
import datetime
import hashlib
import html
import importlib.util
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE_ID, ENGINE_NAME = "VRN_ENG396", "AssetIndex(智慧資產化)"
SKIP = re.compile(r"(?i)__pycache__|_superseded|\.venv|site-packages|node_modules|[\\/]archive[\\/]|[\\/]\.git[\\/]")
_VR = re.compile(r"^(?P<fam>.+?)_v(?P<v>\d{3,5})$")
ACCEL_RX = re.compile(r"\[VIA:ACCEL-BRIDGE|VeritasCeleritas|VC_ACCEL|Invoke-VCPython|VeritasCeleritas\.PS7")


def family(p: Path) -> tuple:
    m = _VR.match(p.stem)
    return (m.group("fam"), int(m.group("v"))) if m else (p.stem, -1)


def files(root: Path) -> list:
    return [p for p in root.rglob("*") if p.suffix.lower() in (".py", ".ps1", ".psm1") and p.is_file() and not SKIP.search(str(p))]


def tails(fs: list) -> dict:
    out = {}
    for p in fs:
        f, v = family(p)
        key = (f, p.suffix.lower())
        if key not in out or v > out[key][1]:
            out[key] = (p, v)
    return out


def _fhash(n) -> str:
    d = ast.dump(n, annotate_fields=False, include_attributes=False)
    return hashlib.sha1(re.sub(r"Constant\('(?:[^'\\]|\\.)*'\)", "C", d).encode()).hexdigest()[:12]


def analyze(p: Path) -> dict:
    """一檔的 AST 分類:一句話用途 · 函式 / 類別 · 動詞 · 替換點(九頭龍)· 加速器 · 是否獨立執行。"""
    try:
        src = p.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"err": type(exc).__name__}
    info = {"bytes": len(src), "accel_static": bool(ACCEL_RX.search(src))}
    if p.suffix.lower() != ".py":
        info.update({"lang": "ps", "doc1": next((l.strip("# ").strip() for l in src.splitlines()[:8] if l.strip().startswith("#") and len(l.strip()) > 4), ""),
                     "funcs": [{"name": m} for m in re.findall(r"(?im)^\s*function\s+([\w-]+)", src)][:80], "verbs": [], "patches": [], "has_main": True})
        return info
    try:
        t = ast.parse(src)
    except SyntaxError as exc:
        info.update({"lang": "py", "err": "SyntaxError L%s" % exc.lineno})
        return info
    doc = (ast.get_docstring(t) or "").strip().splitlines()
    fn, cl, verbs, patches = [], [], [], []
    for n in t.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fn.append({"name": n.name, "args": [a.arg for a in n.args.args], "line": n.lineno, "hash": _fhash(n), "doc1": ((ast.get_docstring(n) or "").splitlines() or [""])[0][:80],
                       "lines": (n.end_lineno or n.lineno) - n.lineno + 1})
        elif isinstance(n, ast.ClassDef):
            cl.append({"name": n.name, "line": n.lineno, "methods": [m.name for m in n.body if isinstance(m, ast.FunctionDef)][:30]})
    for n in ast.walk(t):
        if isinstance(n, ast.Compare) and isinstance(n.left, ast.Subscript):
            for c in ast.walk(n):
                if isinstance(c, ast.List) and len(c.elts) == 1 and isinstance(c.elts[0], ast.Constant) and isinstance(c.elts[0].value, str):
                    verbs.append(c.elts[0].value)
        if isinstance(n, ast.Call):
            nm = n.func.id if isinstance(n.func, ast.Name) else (n.func.attr if isinstance(n.func, ast.Attribute) else "")
            if nm in ("setattr", "_patch", "_patch_v") and n.args:
                a = n.args[1] if nm == "setattr" and len(n.args) > 1 else n.args[0]
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    patches.append(a.value)
    has_main = any(isinstance(n, ast.If) and "__main__" in ast.dump(n.test) for n in t.body)
    info.update({"lang": "py", "doc1": (doc[0] if doc else "")[:160], "funcs": fn, "classes": cl, "verbs": sorted(set(v for v in verbs if re.fullmatch(r"[a-z][a-z0-9_]{1,24}", v))),
                 "patches": patches, "has_main": has_main})
    return info


def category(fam: str, p: Path, root: Path) -> str:
    rel = str(p.relative_to(root)).replace("\\", "/")
    if "SystemManager" in fam:
        return "管理器"
    if re.search(r"(?i)selftest|test_|_test$", fam):
        return "測試"
    if p.suffix.lower() in (".ps1", ".psm1"):
        return "PS 啟動 / 外殼"
    if re.search(r"ENG\d{3}", fam):
        return "引擎" if "/" not in rel else "收容引擎"
    if re.search(r"(?i)toolhub|tool", fam):
        return "工具"
    return "收容模組" if rel.startswith("intake/") else "模組"


def ves_engine(root: Path):
    p = root.resolve()
    while p.parent != p and not (p / "supportive modules").is_dir():
        p = p.parent
    cands = sorted((p / "supportive modules" / "references" / "intake").glob("VIA_VES_EngineStandardizer_b*/via_engine_standardizer.py")) if (p / "supportive modules").is_dir() else []
    if not cands:
        return None, "VES 不在本機 → 內建精簡 AST"
    try:
        spec = importlib.util.spec_from_file_location("via_engine_standardizer_vrn", cands[-1])
        m = importlib.util.module_from_spec(spec)
        sys.modules["via_engine_standardizer_vrn"] = m
        spec.loader.exec_module(m)
        return m, "VES %s(%s)" % (getattr(m, "VERSION", "?"), cands[-1].parent.name)
    except Exception as exc:  # noqa: BLE001
        return None, "VES 載入失敗 %s → 內建精簡 AST" % type(exc).__name__


def builtin_clusters(tl: dict) -> dict:
    by_hash, by_name = defaultdict(list), defaultdict(list)
    for (fam, ext), (p, v) in tl.items():
        for f in (p and tl[(fam, ext)] and ANALYSIS.get(str(p), {}).get("funcs") or []):
            if f.get("hash") and f.get("lines", 0) >= 3:
                by_hash[f["hash"]].append("%s.%s" % (fam, f["name"]))
            if not f["name"].startswith("_") and f["name"] not in ("main", "selftest"):
                by_name[f["name"]].append(fam)
    ident = [v for v in by_hash.values() if len({x.split(".")[0] for x in v}) > 1]
    same = {k: sorted(set(v)) for k, v in by_name.items() if len(set(v)) > 1}
    return {"identical": ident, "same_name_diff_family": same}


ANALYSIS = {}


def missing_functions(fs: list, tl: dict) -> list:
    """以每個家族最新版為基準:舊版有、最新版沒有、其他最新版也沒有 → 往前找到的缺少但合規功能(AST 錨點)。"""
    tail_names = set()
    for (fam, ext), (p, v) in tl.items():
        tail_names |= {f["name"] for f in ANALYSIS.get(str(p), {}).get("funcs") or []}
    fams = defaultdict(list)
    for p in fs:
        if p.suffix.lower() == ".py":
            f, v = family(p)
            if v >= 0:
                fams[f].append((v, p))
    out = []
    for fam, vs in fams.items():
        if len(vs) < 2:
            continue
        vs.sort()
        seen = set()
        for v, p in reversed(vs[:-1]):
            a = ANALYSIS.get(str(p)) or analyze(p)
            ANALYSIS[str(p)] = a
            for f in a.get("funcs") or []:
                n = f["name"]
                if n in tail_names or n in seen or n.startswith("__") or n in ("main", "selftest", "__getattr__"):
                    continue
                seen.add(n)
                ok = f.get("lines", 0) >= 3 and not a.get("err")
                out.append({"family": fam, "func": n, "from": p.name, "anchor": "%s:%d#%s" % (p.name, f["line"], f["hash"]), "elastic": "%s(%s)" % (n, ", ".join(f["args"])),
                            "compliant": ok, "doc1": f.get("doc1", "")})
    return out


def run(root: Path, rep: Path, register: dict = None, use_ves: bool = True) -> dict:
    root, rep = Path(root), Path(rep)
    fs = files(root)
    tl = tails(fs)
    for (fam, ext), (p, v) in tl.items():
        ANALYSIS[str(p)] = analyze(p)
    ves, ves_note = (ves_engine(root) if use_ves else (None, "未啟用 VES"))
    clusters = None
    if ves is not None:
        try:
            r = ves.scan_tree(str(root), 1)
            funcs = r[1] if isinstance(r, tuple) and len(r) > 1 else r
            cl = ves.build_clusters(funcs, 0.85)
            names = ["完全相同(identical)", "同功能不同工具(same_cap_diff_tool)", "近似重複(near_dup)"]
            items = cl.items() if isinstance(cl, dict) else ((names[i] if i < 3 else str(i), v) for i, v in enumerate(cl))
            clusters = {"ves": True, "summary": {k: (len(v) if hasattr(v, "__len__") else v) for k, v in items}}
        except Exception as exc:  # noqa: BLE001
            ves_note += " · 執行失敗 %s → 內建" % type(exc).__name__
    if clusters is None:
        clusters = dict(builtin_clusters(tl), ves=False)
    mgr_src = "\n".join(p.read_text(encoding="utf-8", errors="replace") for (fam, ext), (p, v) in tl.items() if "SystemManager" in fam and ext == ".py")
    heads = Counter()
    for (fam, ext), (p, v) in tl.items():
        pass
    for p in fs:
        if p.suffix.lower() == ".py" and "SystemManager" in p.stem:
            a = ANALYSIS.get(str(p)) or analyze(p)
            ANALYSIS[str(p)] = a
            heads.update(set(a.get("patches") or []))
    reg = register or {}
    rows = []
    for (fam, ext), (p, v) in sorted(tl.items()):
        a = ANALYSIS[str(p)]
        cat = category(fam, p, root)
        runtime = "SystemManager" in fam or (fam in mgr_src and not a.get("has_main"))
        cov = "檔內標記" if a.get("accel_static") else ("經管理器執行" if runtime else "獨立執行 · 未覆蓋")
        hot = [t for t in (a.get("patches") or []) if heads[t] >= 3]
        lamp = "RED" if a.get("err") else ("YELLOW" if cov.startswith("獨立") or hot else "GREEN")
        rows.append({"id": (reg.get(fam) or {}).get("no") or "", "family": fam, "ext": ext, "version": v, "path": str(p.relative_to(root)), "category": cat, "doc1": a.get("doc1", ""),
                     "funcs": len(a.get("funcs") or []), "classes": len(a.get("classes") or []), "verbs": a.get("verbs") or [], "accel": cov, "hot_heads": hot, "lamp": lamp, "err": a.get("err", "")})
    miss = missing_functions(fs, tl)
    cov = Counter(r["accel"] for r in rows)
    covered = cov.get("檔內標記", 0) + cov.get("經管理器執行", 0)
    out_d = rep / "assets"
    out_d.mkdir(parents=True, exist_ok=True)
    mgr = max((r for r in rows if r["family"].endswith("SystemManager") and r["ext"] == ".py"), key=lambda r: r["version"], default=None)
    cmd = {}
    if mgr:
        for p in fs:
            if p.suffix.lower() == ".py" and "SystemManager" in p.stem:
                for vb in (ANALYSIS.get(str(p)) or {}).get("verbs") or []:
                    cmd.setdefault(vb, []).append(p.stem)
    catalog = {"engine": ENGINE_ID, "name": ENGINE_NAME, "ts": datetime.datetime.now().isoformat(timespec="seconds"), "root": str(root), "ves": ves_note, "families": rows,
               "missing_functions": miss, "clusters": clusters, "hydra_heads": dict(heads.most_common()), "command_map": {k: sorted(set(v), key=lambda s: s)[-1:] for k, v in sorted(cmd.items())},
               "coverage": {"tails": len(rows), "covered": covered, "pct": round(100 * covered / max(len(rows), 1), 1), "by": dict(cov)}}
    (out_d / "VRN_ASSET_CATALOG_latest.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (out_d / "VRN_COMMAND_MAP_latest.json").write_text(json.dumps(catalog["command_map"], ensure_ascii=False, indent=1), encoding="utf-8")
    idx = ["# VRN 全貌索引(AI 一讀即懂 · %s · %s)" % (ENGINE_ID, catalog["ts"]),
           "加速器覆蓋 %s%%(%d/%d · 檔內標記 %d · 經管理器執行 %d · 獨立執行未覆蓋 %d)· 九頭龍熱點 %s · 往前找到缺少功能 %d(合規 %d)· %s" % (
               catalog["coverage"]["pct"], covered, len(rows), cov.get("檔內標記", 0), cov.get("經管理器執行", 0), cov.get("獨立執行 · 未覆蓋", 0),
               ", ".join("%s×%d" % kv for kv in heads.most_common() if kv[1] >= 3) or "無", len(miss), sum(1 for m in miss if m["compliant"]), ves_note),
           "動詞 → 管理器版:" + " · ".join("%s→%s" % (k, v[-1].split("_v")[-1]) for k, v in catalog["command_map"].items())[:600], "", "編號 | 家族 | 版 | 類別 | 加速器 | 用途"]
    for r in sorted(rows, key=lambda r: ({"管理器": 0, "引擎": 1, "工具": 2, "收容引擎": 3}.get(r["category"], 4), r["family"]))[:250]:
        idx.append("%s | %s | v%04d | %s | %s | %s" % (r["id"] or "—", r["family"], max(r["version"], 0), r["category"], r["accel"], (r["doc1"] or "")[:70]))
    (out_d / "VRN_ASSET_INDEX_latest.md").write_text("\n".join(idx[:300]) + "\n", encoding="utf-8")
    cdir = rep / "contract"
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "VRN_ASSET_CONTRACT_latest.json").write_text(json.dumps({"contract": "VRN 智慧資產化", "engine": ENGINE_ID, "producer": "VRN_SystemManager assetize", "readonly": True,
                                                                     "outputs": {"catalog": "assets/VRN_ASSET_CATALOG_latest.json", "ai_index": "assets/VRN_ASSET_INDEX_latest.md(≤300 行 · AI 先讀這份)",
                                                                                 "command_map": "assets/VRN_COMMAND_MAP_latest.json"},
                                                                     "rules": ["不改既有檔(只增)", "加速器 100% = 執行入口保證(經管理器)+ 獨立執行檔出新版補橋", "九頭龍熱點不動(整併版處理)",
                                                                               "往前找到的缺少功能 → 任務卡 · 經在地測試才併入"]}, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"tails": len(rows), "coverage": catalog["coverage"], "missing": len(miss), "missing_ok": sum(1 for m in miss if m["compliant"]), "heads": heads, "ves": ves_note,
            "lamps": dict(Counter(r["lamp"] for r in rows)), "cats": dict(Counter(r["category"] for r in rows)), "uncovered": [r["path"] for r in rows if r["accel"].startswith("獨立")][:6],
            "index": str(out_d / "VRN_ASSET_INDEX_latest.md"), "verbs": len(catalog["command_map"])}


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    td = Path(tempfile.mkdtemp(prefix="eng396-"))
    try:
        root = td / "VRN"
        (root / "intake").mkdir(parents=True)
        for v in (99, 100, 101):                                   # 九頭龍頭數 = 有幾個版本替換同一目標
            (root / ("VRN_SystemManager_v%04d.py" % v)).write_text('"""管理器 v%04d"""\n# [VIA:ACCEL-BRIDGE:v0111]\ndef main(args):\n    if args[:1] == ["auto"]:\n        return 1\n    if args[:1] == ["restore"]:\n        return 2\n' % v
                                                                   + "setattr(m, 'l2_one', 1)\nif __name__ == '__main__':\n    main([])\n", encoding="utf-8")
        (root / "VRN_ENG100_Foo_v0100.py").write_text('"""Foo 引擎 舊版"""\ndef keep(x):\n    a = 1\n    return x + a\n\ndef lost_helper(y):\n    """舊版才有的小工具"""\n    z = y * 2\n    return z\n', encoding="utf-8")
        (root / "VRN_ENG100_Foo_v0101.py").write_text('"""Foo 引擎 新版"""\ndef keep(x):\n    a = 1\n    return x + a\n', encoding="utf-8")
        (root / "intake" / "VRN_Tool_v0100.py").write_text('"""獨立小工具"""\ndef keep(x):\n    a = 1\n    return x + a\nif __name__ == "__main__":\n    keep(1)\n', encoding="utf-8")
        (root / "Bad_v0100.py").write_text("def x(:\n", encoding="utf-8")
        o = run(root, td / "rep", register={"VRN_SystemManager": {"no": "VRN-E-0001"}}, use_ves=False)
        cat = json.loads((td / "rep" / "assets" / "VRN_ASSET_CATALOG_latest.json").read_text(encoding="utf-8"))
        fam = {r["family"]: r for r in cat["families"]}
        chk("① 全景 AST 分類:家族最新版 %d 個 · 管理器 / 引擎 / 收容模組 · 用途一句話 · 編號 VRN-E-0001 · 語法錯 → 紅" % o["tails"],
            fam["VRN_SystemManager"]["category"] == "管理器" and fam["VRN_ENG100_Foo"]["version"] == 101 and fam["VRN_SystemManager"]["id"] == "VRN-E-0001" and fam["Bad"]["lamp"] == "RED"
            and "Foo 引擎 新版" in fam["VRN_ENG100_Foo"]["doc1"])
        chk("② 加速器覆蓋三類:管理器檔內標記 · 獨立執行未覆蓋(intake 小工具)· 覆蓋率 %s%%" % o["coverage"]["pct"],
            fam["VRN_SystemManager"]["accel"] == "檔內標記" and fam["VRN_Tool"]["accel"].startswith("獨立") and 0 < o["coverage"]["pct"] < 100)
        mf = [m for m in cat["missing_functions"] if m["func"] == "lost_helper"]
        chk("③ 往前找缺少但合規的功能:Foo v0100 有 lost_helper · v0101 沒有 · 其他最新版也沒有 → 列出 + AST 錨點 %s" % (mf[0]["anchor"] if mf else "—"),
            mf and mf[0]["compliant"] and mf[0]["anchor"].startswith("VRN_ENG100_Foo_v0100.py:") and not any(m["func"] == "keep" for m in cat["missing_functions"]))
        chk("④ 分群(內建):keep 三個家族結構完全相同 → identical 群 · 九頭龍 l2_one 3 頭 → 熱點 · 動詞表 auto / restore",
            any(len(g) >= 2 for g in cat["clusters"]["identical"]) and cat["hydra_heads"].get("l2_one") == 3 and set(cat["command_map"]) >= {"auto", "restore"})
        idx = (td / "rep" / "assets" / "VRN_ASSET_INDEX_latest.md").read_text(encoding="utf-8").splitlines()
        con = json.loads((td / "rep" / "contract" / "VRN_ASSET_CONTRACT_latest.json").read_text(encoding="utf-8"))
        chk("⑤ AI 一讀全貌索引 ≤300 行(%d 行 · 首行總覽 · 一行一家族)· 契約(只讀 · 不改既有檔)" % len(idx), len(idx) <= 300 and "加速器覆蓋" in idx[1] and con["readonly"] is True)
        before = {q: q.stat().st_mtime for q in root.rglob("*.py")}
        run(root, td / "rep", use_ves=False)
        chk("⑥ 只讀:跑兩次 · 既有檔一個都沒改", all(q.stat().st_mtime == t for q, t in before.items()))
    finally:
        shutil.rmtree(td, ignore_errors=True)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 最新有版號加速器橋 [VIA:ACCEL-BRIDGE:v0111]", "[VIA:ACCEL-BRIDGE:v0111]" in me)
    print("[計] %s %s 自測 %d/%d · %s" % (ENGINE_ID, Path(__file__).stem.split("_")[-1], p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:2]:
        raise SystemExit(selftest())
    print(json.dumps(run(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE, HERE / "_assets_out"), ensure_ascii=False, default=str)[:2000])
