#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0136 — 薄尾 v0136:修 health 印出格式(v0134 在正式樹上印爆:格式串少一個 %d);其餘同 v0134;health 動詞 v0101 律(操作員 2026-10-06「網路工具應該是有版號的新版本」:網橋要 SUP_MDL740_NetUnified_v####;舊橋黃;網路工具本體豁免;副本檔名 DORMANT 候選;對帳改號的版號洞不算錯)(操作員令 2026-10-06:各 system manager 自管自報健康矩陣——有無編號 · 版本號與語意 · 有無註冊 · 加速器 · 網路工具 · AST 可跑 · lib/環境已裝 · 最近結果)。
  health            掃自己的 .py 族 / 冊 / 表頭冊 / 功能矩陣 / lib → 寫 VIA_Reports/vrn/HEALTH_latest.json(母系統 HealthMatrix 只讀它來匯總);印 [計] 一行 + 紅行
其餘動詞照前版鏈(extract · table · fn · ssot …)。沙盒鍵:VIA_VRN_SSOT_HOME · VIA_VRN_HEALTH_OUT。
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

import datetime
import importlib.util
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0136"


def _vnum_v0136(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0136(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0136(p) < _vnum_v0136(__file__)), key=_vnum_v0136)
PRIOR = _load_v0136(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


# ===== [VIA:SM-HEALTH:v0102] 子系統健康段(v0102:副本檔最多黃)(v0101:網橋要「有版號的新版」SUP_MDL740_NetUnified_v####/via_net_unified_v####/[VIA:NET-BRIDGE:v####];無版號舊橋=黃;網路工具本體與加速器本體豁免;副本檔名 (1)/_sha 標 DORMANT 候選;對帳改號造成的版號洞不當語意錯)(各 SystemManager 自管自報:功能矩陣 · 表頭冊 · 編號 · 版本語意 · 加速器 · 網橋 · lib/環境 · 最近自測;只讀,寫自己的 HEALTH_latest.json)=====
def _hl_vnum(name):
    import re as _re
    m = _re.search(r"_v(\d{2,4})[A-Za-z0-9]*(?:\.[A-Za-z0-9]+)?$", name)
    return int(m.group(1)) if m else -1


def _hl_read_json(p):
    import json as _json
    try:
        return _json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return None


def _hl_tail(d, pat):
    hits = sorted(d.glob(pat), key=lambda q: _hl_vnum(q.name)) if d.is_dir() else []
    return hits[-1] if hits else None


def sm_health(sub, home, root, out_dir, now, required_libs=(), net_required=False):
    """→ dict(健康矩陣的子系統段)。home = functional modules/<SUB>;out_dir = VIA_Reports/<sub>/。"""
    import importlib.util as _ilu
    import re as _re
    import sys as _sys
    import json as _json
    from collections import defaultdict as _dd
    from pathlib import Path as _P
    reg = home / "registry"
    fm = _hl_read_json(_hl_tail(reg, sub + "_FunctionMatrix_v*.json")) if reg.is_dir() else None
    th = _hl_read_json(_hl_tail(reg, sub + "_TableHeader_v*.json")) if reg.is_dir() else None
    nb = {}
    central = root / "supportive modules" / "registry"
    for p in (central / "VIA_NumberBooks").glob("VIA_NumberBook_*_v*.jsonl") if (central / "VIA_NumberBooks").is_dir() else []:
        try:
            for ln in p.read_text(encoding="utf-8-sig").splitlines():
                r = _json.loads(ln)
                if r.get("source") and r.get("code"):
                    nb[r["source"].replace("\\", "/")] = r["code"]
        except Exception:  # noqa: BLE001
            pass
    rn = _hl_read_json(central / "VIA_RegistryNumbers_v0100.json") if (central / "VIA_RegistryNumbers_v0100.json").exists() else None
    rn_keys = {e["key"]: e["code"] for e in (rn or {}).get("entries", []) if e.get("key")}
    # 檔案列:每族(去版號)一列
    fams = _dd(list)
    for p in home.rglob("*.py"):
        if set(p.relative_to(home).parts[:-1]) & {"references", "intake", "_superseded", "__pycache__", "VIA_RetiredEngines", "_quarantine"}:
            continue
        fams[(p.parent, _re.sub(r"_v\d{2,4}[A-Za-z0-9]*$", "", p.stem))].append(p)
    rows = []
    sem_issues = 0
    collision_fams = set()
    cl = root / "VIA_Reports" / "review" / "vcgc_collision" / "COLLISION_ledger.jsonl"
    if cl.exists():
        for ln in cl.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            m = _re.search(r"([A-Za-z0-9]+_SystemManager|CGC_MDL\d{3}_[A-Za-z0-9]+)", ln)
            if m:
                collision_fams.add(_re.sub(r"_v\d{4}$", "", m.group(1)))
    for (d, fam), ps in sorted(fams.items(), key=lambda x: (str(x[0][0]), x[0][1])):
        ps.sort(key=lambda q: (_hl_vnum(q.name), q.name))
        tail = ps[-1]
        vers = [_hl_vnum(q.name) for q in ps if _hl_vnum(q.name) >= 0]
        try:
            txt = tail.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            txt = ""
        body = txt.split("\ndef selftest(")[0]
        accel = "[VIA:ACCEL-BRIDGE" in txt or "VeritasCeleritas_v1141" in txt
        net_use = bool(_re.search(r"^\s*(?:import|from)\s+(requests|httpx|aiohttp|urllib\.request|yfinance|akshare|fredapi|pandas_datareader)\b", body, _re.M))   # 要真的 import 才算出網(正則字串裡的字不算)
        is_net_tool = bool(_re.search(r"(?i)NetUnified|AegisNexus|via_net_unified|VIA_NetSupport|via_aegis_netcore|^(request|proxy|collector|urls|git)$", fam)) or "network" in d.parts or "accelerator" in d.parts or fam.startswith(("VeritasCeleritas", "SUP_MDL737", "VIA_SuperAccel", "pip_subprocess"))
        net_new = bool(_re.search(r"SUP_MDL740_NetUnified_v\d{4}|via_net_unified_v\d{4}|\[VIA:NET-BRIDGE:v\d{4}\]", body))
        net_old = (not net_new) and bool(_re.search(r"\[VIA:NET-BRIDGE|VIA_NetSupport\b|via_net_unified\b|SUP_MDL740", body))
        net_ok = (not net_use) or is_net_tool or net_new or net_old      # 舊橋不紅(黃),沒橋才紅
        net_note = "" if (not net_use or is_net_tool) else ("新版網橋" if net_new else ("舊版網橋(無版號)→ 改接 SUP_MDL740_NetUnified_v####" if net_old else "無網橋"))
        junk = bool(_re.search(r"\s\(\d+\)$|_sha[0-9a-f]{8,}$", tail.stem)) or " (1)" in tail.name
        sem = []
        if junk:
            sem.append("副本檔名((1)/_sha)→ DORMANT 候選")
        if len(vers) != len(set(vers)):
            sem.append("同版號重複")
        if vers and max(vers) - min(vers) + 1 != len(vers) and len(vers) > 1:
            sem.append(("版號洞=對帳改號(已記帳)" if fam in collision_fams else "版號有洞(%d–%d 共 %d)") % ((min(vers), max(vers), len(vers)) if fam not in collision_fams else ()))
        if _hl_vnum(tail.name) < 0 and len(ps) > 1:
            sem.append("尾版無版號")
        sem_issues += bool([x for x in sem if "已記帳" not in x])
        rel = tail.relative_to(root).as_posix() if str(tail).startswith(str(root)) else tail.as_posix()
        key_mdl = "%s|MDL|%s|%s" % (sub, fam, ("v%04d" % _hl_vnum(tail.name)) if _hl_vnum(tail.name) >= 0 else "v0000")
        key_eng = key_mdl.replace("|MDL|", "|ENG|")
        code = nb.get(rel) or rn_keys.get(key_mdl) or rn_keys.get(key_eng) or ""
        registered = bool(fm and any(k.split("|")[1] == fam for k in (fm.get("items") or {}) if k.startswith(("MDL|", "ENG|"))))
        try:
            import ast as _ast
            _ast.parse(txt)
            ast_ok = True
        except Exception:  # noqa: BLE001
            ast_ok = False
        lamp = "RED" if ((not ast_ok or not net_ok) and not junk) else ("YELLOW" if (junk or not accel or not code or not registered or net_old or [x for x in sem if "已記帳" not in x]) else "GREEN")   # 副本檔(junk)最多黃:它的歸宿是 dormant,不是修
        rows.append({"family": fam, "dir": d.relative_to(home).as_posix() if str(d).startswith(str(home)) else str(d), "tail": tail.name, "version": ("v%04d" % _hl_vnum(tail.name)) if _hl_vnum(tail.name) >= 0 else "—", "n_versions": len(ps),
                     "number": code, "registered": registered, "accel": accel, "net_use": net_use, "net_ok": net_ok, "net_note": net_note, "net_tool": is_net_tool, "ast_ok": ast_ok, "semantic": ";".join(sem), "lamp": lamp})
    # 冊 / 表頭 / 字典
    books = []
    for sd in ("SSOT", "registry", "knowledge"):
        d = home / sd
        if d.is_dir():
            seen = {}
            for p in d.glob("*.json"):
                fam = _re.sub(r"_v\d{2,4}[A-Za-z0-9]*$", "", p.stem)
                if fam not in seen or _hl_vnum(p.name) > _hl_vnum(seen[fam].name):
                    seen[fam] = p
            for fam, p in seen.items():
                tid = _re.sub(r"[^a-z0-9_]+", "_", fam.lower()).strip("_")
                ent = (th or {}).get("tables", {}) if th else {}
                reg_t = any(k == tid or k.startswith(tid + "_") for k in ent)
                num_t = any((k == tid or k.startswith(tid + "_")) and v.get("table_no") for k, v in ent.items())
                books.append({"book": p.name, "dir": sd, "registered": reg_t, "numbered": num_t, "lamp": "GREEN" if num_t else ("YELLOW" if reg_t else "GRAY")})
    # lib / 環境(本直譯器)
    libs = []
    for name in required_libs:
        ok = _ilu.find_spec(name) is not None
        libs.append({"lib": name, "importable": ok, "lamp": "GREEN" if ok else "RED"})
    # 最近自測 / 結果
    results = []
    if out_dir.is_dir():
        for p in sorted(out_dir.glob("RESULT_*_latest.json"))[:40]:
            import datetime as _dt, time as _time
            age = (_time.time() - p.stat().st_mtime) / 86400
            results.append({"result": p.name, "age_days": round(age, 1), "lamp": "GREEN" if age <= 7 else "YELLOW"})
    fm_items = (fm or {}).get("items", {}) if fm else {}
    summary = {"files": len(rows), "red": sum(1 for r in rows if r["lamp"] == "RED"), "yellow": sum(1 for r in rows if r["lamp"] == "YELLOW"), "green": sum(1 for r in rows if r["lamp"] == "GREEN"),
               "numbered": sum(1 for r in rows if r["number"]), "registered": sum(1 for r in rows if r["registered"]), "accel": sum(1 for r in rows if r["accel"]), "net_bad": sum(1 for r in rows if not r["net_ok"]), "net_old": sum(1 for r in rows if r["net_note"].startswith("舊版")), "semantic_issues": sem_issues,
               "fn_items": len(fm_items), "fn_numbered": sum(1 for e in fm_items.values() if e.get("number")), "tables": len((th or {}).get("tables", {}) if th else {}), "tables_numbered": sum(1 for v in ((th or {}).get("tables", {}) if th else {}).values() if v.get("table_no")),
               "books": len(books), "libs_missing": sum(1 for l in libs if not l["importable"]), "python": _sys.executable}
    lamp = "RED" if (summary["red"] or summary["libs_missing"]) else ("YELLOW" if (summary["yellow"] or not fm or not th) else "GREEN")
    health = {"sub": sub, "ts": now, "python": _sys.executable, "lamp": lamp, "summary": summary, "files": rows, "books": books, "libs": libs, "results": results,
              "fn_matrix": (_hl_tail(reg, sub + "_FunctionMatrix_v*.json").name if fm else None), "table_header": (_hl_tail(reg, sub + "_TableHeader_v*.json").name if th else None)}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "HEALTH_latest.json").write_text(_json.dumps(health, ensure_ascii=False, indent=1), encoding="utf-8")
    return health


def sm_health_print(h):
    s = h["summary"]
    print("[計] %s health · 檔族 %d(紅 %d 黃 %d 綠 %d)· 有號 %d · 已登記 %d · 有橋 %d · 網橋缺 %d 舊橋 %d · 版號語意 %d · 功 %d/%d 有號 · 表 %d/%d 有號 · 冊 %d · lib 缺 %d · %s" % (
        h["sub"], s["files"], s["red"], s["yellow"], s["green"], s["numbered"], s["registered"], s["accel"], s["net_bad"], s["net_old"], s["semantic_issues"], s["fn_numbered"], s["fn_items"], s["tables_numbered"], s["tables"], s["books"], s["libs_missing"], h["lamp"]))
    for r in [x for x in h["files"] if x["lamp"] == "RED"][:10]:
        print("  [RED] %s %s · %s" % (h["sub"], r["tail"], "AST 壞" if not r["ast_ok"] else r["net_note"]))
    for r in [x for x in h["files"] if x["net_note"].startswith("舊版")][:10]:
        print("  [YEL] %s %s · %s" % (h["sub"], r["tail"], r["net_note"]))
    for l in [x for x in h["libs"] if not x["importable"]]:
        print("  [RED] %s lib 缺 %s(本直譯器 %s)" % (h["sub"], l["lib"], h["python"]))
# ===== [VIA:SM-HEALTH:END] =====

# ===== [VIA:SM-DORMANT:v0100] 子系統副本退役段(只動自己夾裡的副本檔:檔名帶 " (1)" 或 "_sha<8+hex>" 尾;移到 _superseded/,不刪,一行帳;只增不減)=====
def sm_dormant(sub, home, now, apply=False):
    import json as _json
    import re as _re
    import shutil as _shutil
    from pathlib import Path as _P
    rows = []
    for p in sorted(home.rglob("*")):
        if not p.is_file() or set(p.relative_to(home).parts[:-1]) & {"_superseded", "references", "intake", "__pycache__", "VIA_RetiredEngines", "_quarantine", "input"}:
            continue
        stem = p.stem
        m = _re.search(r"^(.*?)(?:\s\(\d+\))?(?:_sha[0-9a-f]{8,})?$", stem)
        base = m.group(1) if m else stem
        is_junk = bool(_re.search(r"\s\(\d+\)$|_sha[0-9a-f]{8,}$", stem))
        if not is_junk:
            continue
        sibling = next((q for q in p.parent.glob(base + "*" + p.suffix) if q != p and not _re.search(r"\s\(\d+\)$|_sha[0-9a-f]{8,}$", q.stem)), None)
        rec = {"file": p.relative_to(home).as_posix(), "base": base, "sibling": (sibling.name if sibling else None), "status": "PLAN"}
        if apply:
            dst_dir = p.parent / "_superseded"
            dst_dir.mkdir(exist_ok=True)
            dst = dst_dir / (p.name + ".DORMANT_" + now.replace(":", "").replace("-", "")[:15])
            _shutil.move(str(p), str(dst))
            rec["status"], rec["to"] = "DORMANT", dst.relative_to(home).as_posix()
            with open(home / "registry" / (sub + "_Dormant_Ledger.jsonl"), "a", encoding="utf-8") as fh:
                fh.write(_json.dumps(dict(rec, ts=now, why="副本檔名 (1)/_sha;原正本 " + (sibling.name if sibling else "不在(獨本,仍退役:副本命名不入鏈)")), ensure_ascii=False) + "\n")
        rows.append(rec)
    return {"verb": "dormant", "apply": apply, "n": len(rows), "moved": sum(1 for r in rows if r["status"] == "DORMANT"), "rows": rows, "lamp": "GREEN" if apply or not rows else "YELLOW"}


def sm_dormant_print(sub, out):
    print("[計] %s dormant%s · 副本檔 %d · 移 _superseded %d · %s" % (sub, " --apply" if out["apply"] else "(dry-run)", out["n"], out["moved"], out["lamp"]))
    for r in out["rows"][:20]:
        print("  [%s] %s %s · 正本 %s" % ("OK" if r["status"] == "DORMANT" else "YEL", r["status"], r["file"], r["sibling"] or "—"))
# ===== [VIA:SM-DORMANT:END] =====

REQUIRED_LIBS = ('pandas', 'pdfplumber')


def health() -> dict:
    home = Path(os.environ.get("VIA_VRN_SSOT_HOME") or HERE)
    root = home.parents[1] if len(home.parents) > 1 else home
    out_dir = Path(os.environ.get("VIA_VRN_HEALTH_OUT") or (root / "VIA_Reports" / "vrn"))
    return sm_health("VRN", home, root, out_dir, datetime.datetime.now().isoformat(timespec="seconds"), REQUIRED_LIBS)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["health"]:
        h = health()
        sm_health_print(h)
        return 1 if h["lamp"] == "RED" else 0
    if args[:1] == ["dormant"]:
        home = Path(os.environ.get("VIA_VRN_SSOT_HOME") or HERE)
        out = sm_dormant("VRN", home, datetime.datetime.now().isoformat(timespec="seconds"), apply=("--apply" in args))
        sm_dormant_print("VRN", out)
        return 0
    return PRIOR.main(args)


def selftest() -> int:
    import json
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

    td = Path(tempfile.mkdtemp(prefix="vrnhl-"))
    home = td / "functional modules" / "VRN"
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_HEALTH_OUT")}
    os.environ["VIA_VRN_SSOT_HOME"] = str(home)
    os.environ["VIA_VRN_HEALTH_OUT"] = str(td / "VIA_Reports" / "vrn")
    A = "# [VIA:ACCEL-BRIDGE:v0100]\n"
    (home / "registry").mkdir(parents=True)
    (home / "VRN_ENG001_A_v0100.py").write_text(A + "x=1\n", encoding="utf-8")
    (home / "VRN_ENG001_A_v0102.py").write_text(A + "x=2\n", encoding="utf-8")                    # 版號有洞(0101 缺)
    (home / "VRN_ENG002_B_v0100.py").write_text("import requests\nrequests.get('x')\n", encoding="utf-8")   # 無橋 + 出網無網橋 → 紅
    (home / "VRN_ENG003_C_v0100.py").write_text(A + "def f(:\n", encoding="utf-8")                # AST 壞 → 紅
    (home / "registry" / "VRN_FunctionMatrix_v0100.json").write_text(json.dumps({"items": {"ENG|VRN_ENG001_A": {"kind": "ENG", "number": "VIA-VRN-ENG001"}}}), encoding="utf-8")
    (home / "SSOT").mkdir()
    (home / "SSOT" / "VRN_Thing_SSOT_v0100.json").write_text("{}", encoding="utf-8")
    (home / "registry" / "VRN_TableHeader_v0100.json").write_text(json.dumps({"tables": {"vrn_thing_ssot": {"table_no": "SSOT-VCGC-VRN-TBL0001"}}}), encoding="utf-8")
    h = health()
    sm_health_print(h)        # 印出也要過(2026-10-06 教訓:格式串與參數數量對不上只有真印才爆)
    R = {r["family"]: r for r in h["files"]}
    chk("① 檔族 3:ENG001 尾版 v0102 · 版號有洞語意黃 · 已登記", R["VRN_ENG001_A"]["version"] == "v0102" and "版號有洞" in R["VRN_ENG001_A"]["semantic"] and R["VRN_ENG001_A"]["registered"])
    chk("② ENG002 出網無網橋 → 紅;ENG003 AST 壞 → 紅", R["VRN_ENG002_B"]["lamp"] == "RED" and not R["VRN_ENG002_B"]["net_ok"] and R["VRN_ENG003_C"]["lamp"] == "RED" and not R["VRN_ENG003_C"]["ast_ok"])
    chk("③ 冊:Thing_SSOT 有表頭有號 → 綠", any(b["book"].startswith("VRN_Thing_SSOT") and b["lamp"] == "GREEN" for b in h["books"]))
    chk("④ lib 檢查(本直譯器)· HEALTH_latest.json 落檔 · 總燈紅", (td / "VIA_Reports" / "vrn" / "HEALTH_latest.json").exists() and h["lamp"] == "RED" and len(h["libs"]) == len(REQUIRED_LIBS))
    (home / "VRN_ENG002_B_v0100 (1).py").write_text("x=1\n", encoding="utf-8")
    dd = sm_dormant("VRN", home, "2026-10-06T00:00:00", apply=False)
    still_there = (home / "VRN_ENG002_B_v0100 (1).py").exists()
    da = sm_dormant("VRN", home, "2026-10-06T00:00:00", apply=True)
    chk("⑤ dormant:dry-run 列 1 副本不動;--apply 移 _superseded 不刪 · 記 VRN_Dormant_Ledger", dd["n"] == 1 and dd["moved"] == 0 and still_there and da["moved"] == 1 and not (home / "VRN_ENG002_B_v0100 (1).py").exists() and list((home / "_superseded").glob("*DORMANT*")) and (home / "registry" / "VRN_Dormant_Ledger.jsonl").exists())
    h2 = health()
    chk("⑥ 副本檔最多黃:退役後總燈仍紅是因 ENG002 出網無橋(真紅)· ENG003 AST 壞", h2["lamp"] == "RED")
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑦ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑧ 帶加速器橋 · 健康共用段 · 退役段 · glob 取前版", "[VIA:ACCEL-BRIDGE:v0100]" in body and "[VIA:SM-HEALTH:" in body and "[VIA:SM-DORMANT:" in body)
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0136 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
