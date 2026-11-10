#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_ConstitutionCheck v0100 — 憲法第十一 / 十二章四件事(VCGC · 只讀檢查 + 合格才發 IFC 號)。

操作員 2026-11-10:「不可違反獨立性 · 編號憲法性 · AI 跟我有權利改 · 必用 TOKEN 節省工具 · 簡化不要太雜」。
只做四件:
  ① 獨立性(CONST-031 / 033 / 043 / 044):VCGC · VDF · VRN-2 尾版引用他系統模組名,不在契約 allowlist 的 = 衝突(照實列,不代修)。
  ② 編號憲法性(CONST-034 / 037 / 038 / L125):契約六欄齊 + 錯誤碼標準 + 測試五類齊 + 號不撞 → 才發 IFC-### 永久號(只增 · 發後不改 · 不重用)。
  ③ 註冊三要素(L126):每條契約都有 編號 · 版本號 · 時間。
  ④ 不可用 TA-Lib(L50):三系統尾版靜態 / 動態載入 0。
用法:check(只讀)· issue(合格的 DRAFT 發號 → 寫新版號契約冊)· --selftest
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更)=====
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
import json
import re
import sys
import tempfile
import warnings
from datetime import datetime, timezone
from pathlib import Path

ENGINE = "VIA_ConstitutionCheck_v0100"
HERE = Path(__file__).resolve().parent
VIA = HERE.parents[2]
REG = "supportive modules/registry/"
FIELDS = ("INPUT", "OUTPUT", "PARAMETERS", "ERROR_CODE", "TIMEOUT", "SECURITY")
TESTS = ("normal", "boundary", "error", "stress", "security")
SYSTEMS = {"VCGC": ("supportive modules/registry", r"^CGC_"), "VDF": ("functional modules/VDF", r"^VDF_"), "VRN-2": ("functional modules/VRN", r"^VRN2?_")}
TALIB = {"talib", "ta_lib"}


def _tail(folder: Path, pattern: str):
    c = sorted(folder.glob(pattern))
    return c[-1] if c else None


def _tails(root: Path) -> dict:
    """每系統的尾版 .py(同夾同家族取最大 _vNNNN)。"""
    out = {}
    for sysname, (sub, _) in SYSTEMS.items():
        fam = {}
        for p in (root / sub).rglob("*.py"):
            m = re.match(r"^(.+?)_v(\d{4})$", p.stem)
            key = (p.parent, m.group(1) if m else p.stem)
            v = int(m.group(2)) if m else 0
            if key not in fam or v > fam[key][0]:
                fam[key] = (v, p)
        out[sysname] = [p for _, p in fam.values()]
    return out


def _refs(path: Path):
    """一支檔裡提到的模組名(import + 字串常數 *.py / glob)與 TA-Lib 載入。"""
    warnings.simplefilter("ignore", SyntaxWarning)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set(), ""
    names, tal = set(), ""
    for nd in ast.walk(tree):
        if isinstance(nd, (ast.Import, ast.ImportFrom)):
            for a in ([nd.module] if isinstance(nd, ast.ImportFrom) and nd.module else [x.name for x in nd.names]):
                top = (a or "").split(".")[0]
                names.add(top)
                tal = tal or ("static:L%d" % nd.lineno if top.lower() in TALIB else "")
        elif isinstance(nd, ast.Call):
            fn = nd.func.attr if isinstance(nd.func, ast.Attribute) else (nd.func.id if isinstance(nd.func, ast.Name) else "")
            if "import" in fn.lower() and nd.args and isinstance(nd.args[0], ast.Constant) and str(nd.args[0].value).split(".")[0].lower() in TALIB:
                tal = tal or "dynamic:L%d" % nd.lineno
        elif isinstance(nd, ast.Constant) and isinstance(nd.value, str) and len(nd.value) < 160:
            m = re.search(r"([A-Za-z0-9_\-]+?)(?:_v[\d\*]{1,4})?\*?\.py$", nd.value)
            if m:
                names.add(m.group(1))
    return names, tal


def check(root: Path = VIA) -> dict:
    const = json.loads(_tail(root / REG, "VIA_Constitution_SSOT_v*.json").read_text(encoding="utf-8"))
    book_path = _tail(root / REG, "VIA_SystemInterface_Contract_SSOT_v*.json")
    book = json.loads(book_path.read_text(encoding="utf-8"))
    errs = set(const.get("error_codes", {}))
    allow = [n for c in book["contracts"] for n in c.get("allowlist", {}).get("names", [])]
    # ① 獨立性
    indep, talib = {}, []
    for sysname, files in _tails(root).items():
        for p in files:
            names, tal = _refs(p)
            if tal:
                talib.append("%s:%s(%s)" % (sysname, p.name, tal))
            for other, (_, rx) in SYSTEMS.items():
                if other == sysname:
                    continue
                for n in names:
                    if re.match(rx, n) and not any(n.startswith(a) for a in allow):
                        indep.setdefault("%s→%s" % (sysname, other), []).append("%s:%s" % (p.name, n))
    # ②③ 契約
    used = {c["ifc_id"] for c in book["contracts"] if c.get("ifc_id")} | {t.get("ifc_id") for t in book.get("tombstones", [])}
    rows = []
    for c in book["contracts"]:
        miss = [f for f in FIELDS if not c.get(f)]
        bad_err = [k for k in (c.get("ERROR_CODE") or {}) if k not in errs]
        miss_t = [t for t in TESTS if not any(str(x).startswith(t + ":") for x in c.get("tests", []))]
        reg = [k for k, v in (("number", c.get("ifc_id") or c.get("cand")), ("version", c.get("version")), ("time", c.get("registered_at"))) if not v]
        ok = not (miss or bad_err or miss_t or reg)
        rows.append({"cand": c.get("cand"), "ifc_id": c.get("ifc_id", ""), "state": c.get("state"), "title": c.get("title"), "ok": ok,
                     "missing_fields": miss, "bad_error_codes": bad_err, "missing_tests": miss_t, "missing_registration": reg})
    ids = [c["ifc_id"] for c in book["contracts"] if c.get("ifc_id")]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    lamp = "RED" if (talib or dup) else ("YELLOW" if (indep or not all(r["ok"] for r in rows) or any(not r["ifc_id"] for r in rows)) else "GREEN")
    return {"engine": ENGINE, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "lamp": lamp, "book": book_path.name,
            "independence": {k: {"count": len(v), "sample": v[:5]} for k, v in sorted(indep.items())},
            "contracts": rows, "duplicate_ids": dup, "used_ids": sorted(i for i in used if i), "talib": talib}


def issue(root: Path = VIA) -> dict:
    """合格且仍是 DRAFT 的契約 → 發 IFC-###(接續最大號 · 不重用墓碑號)→ ACTIVE;寫新版號冊(舊版不就地改 · L04)。"""
    res = check(root)
    if res["duplicate_ids"] or res["talib"]:
        return {"issued": [], "why": "有撞號或 TA-Lib → 不發號(L125)", "check": res}
    src = _tail(root / REG, "VIA_SystemInterface_Contract_SSOT_v*.json")
    book = json.loads(src.read_text(encoding="utf-8"))
    taken = [int(i[4:]) for i in res["used_ids"] if re.match(r"^IFC-\d{3}$", i)]
    nxt, now, issued = (max(taken) + 1 if taken else 1), datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), []
    okmap = {r["cand"]: r["ok"] for r in res["contracts"]}
    for c in book["contracts"]:
        if c.get("state") == "DRAFT" and not c.get("ifc_id") and okmap.get(c.get("cand")):
            c.update(ifc_id="IFC-%03d" % nxt, state="ACTIVE", updated_at=now)
            c.setdefault("history", []).append({"at": now, "state": "ACTIVE", "why": "%s:六欄 · 錯誤碼 · 測試五類 · 註冊三要素齊 · 無撞號 → 發號(L125)" % ENGINE})
            issued.append((c["cand"], c["ifc_id"]))
            nxt += 1
    if not issued:
        return {"issued": [], "why": "沒有合格的 DRAFT", "check": res}
    v = int(re.search(r"_v(\d{4})", src.name).group(1)) + 1
    dst = src.with_name("VIA_SystemInterface_Contract_SSOT_v%04d.json" % v)
    book.update(version="v%04d" % v, ts=now, prior=src.name)
    dst.write_text(json.dumps(book, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"issued": issued, "book": dst.name}


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · %s" % note) if note else ""))
    print("[%s selftest]" % ENGINE)
    with tempfile.TemporaryDirectory() as td:
        r = Path(td)
        (r / REG).mkdir(parents=True)
        (r / "functional modules/VDF").mkdir(parents=True)
        (r / "functional modules/VRN").mkdir(parents=True)
        (r / REG / "VIA_Constitution_SSOT_v0100.json").write_text(json.dumps({"error_codes": {"ERR-001": "", "ERR-004": ""}}), encoding="utf-8")
        good = {"cand": "C1", "ifc_id": "", "version": "v1.0", "state": "DRAFT", "registered_at": "t", "title": "收據", "allowlist": {"names": ["VDF_SystemManager"]},
                "tests": ["normal:x", "boundary:x", "error:x", "stress:x", "security:x"], "ERROR_CODE": {"ERR-001": "x"}}
        good.update({f: "x" for f in FIELDS if f != "ERROR_CODE"})
        bad = dict(good, cand="C2", TIMEOUT="", tests=["normal:x"])
        (r / REG / "VIA_SystemInterface_Contract_SSOT_v0100.json").write_text(json.dumps({"contracts": [good, bad], "tombstones": [{"ifc_id": "IFC-001"}]}), encoding="utf-8")
        (r / REG / "CGC_MDL001_Watch_v0100.py").write_text('import os\nX = "VDF_SystemManager_v0100.py"\nY = "VDF_MDL009_Private_v0102.py"\n', encoding="utf-8")
        (r / "functional modules/VRN/VRN_ENG001_A_v0100.py").write_text('def f():\n    import talib\n', encoding="utf-8")
        c = check(r)
        chk("① 獨立性:契約 allowlist 內(VDF_SystemManager)放行 · 他系統私有模組(VDF_MDL009)= 衝突", c["independence"].get("VCGC→VDF", {}).get("count") == 1
            and "VDF_MDL009_Private" in c["independence"]["VCGC→VDF"]["sample"][0], c["independence"])
        chk("④ TA-Lib:函式內 import talib 抓到 → 燈 RED", c["talib"] and c["lamp"] == "RED", c["talib"])
        chk("② 欄位 / 測試缺的契約不合格 · 齊的合格", [x["ok"] for x in c["contracts"]] == [True, False], [x["missing_fields"] + x["missing_tests"] for x in c["contracts"]])
        n = issue(r)
        chk("②' 有 TA-Lib 時一律不發號(L125)", not n["issued"], n.get("why"))
        (r / "functional modules/VRN/VRN_ENG001_A_v0100.py").write_text('def f():\n    return 1\n', encoding="utf-8")
        n = issue(r)
        chk("②'' 無衝突 → 只發合格的那條 · 跳過墓碑號(IFC-001 已終止 → 發 IFC-002)· 寫新版號冊 v0101,舊冊不動",
            n["issued"] == [("C1", "IFC-002")] and (r / REG / "VIA_SystemInterface_Contract_SSOT_v0101.json").is_file()
            and "IFC-002" not in (r / REG / "VIA_SystemInterface_Contract_SSOT_v0100.json").read_text(), n)
        b = json.loads((r / REG / "VIA_SystemInterface_Contract_SSOT_v0101.json").read_text(encoding="utf-8"))
        chk("③ 註冊三要素:發號後 編號 · 版本 · 時間 都在 · 狀態唯一 ACTIVE", all(b["contracts"][0].get(k) for k in ("ifc_id", "version", "updated_at")) and b["contracts"][0]["state"] == "ACTIVE")
        chk("②''' 再跑不重發(已發的號不變)", not issue(r)["issued"])
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", ENGINE, n, len(ok)))
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if a[:1] == ["issue"]:
        print(json.dumps(issue(), ensure_ascii=False, indent=1)[:3000])
        return 0
    res = check()
    print("[%s] %s · 契約冊 %s" % (res["lamp"], ENGINE, res["book"]))
    print("  ① 獨立性(未走契約的跨系統內部引用):" + (" · ".join("%s %d" % (k, v["count"]) for k, v in res["independence"].items()) or "0"))
    for r in res["contracts"]:
        print("  ② %s %-12s %-8s %s%s" % ("OK " if r["ok"] else "缺 ", r["ifc_id"] or r["cand"], r["state"], r["title"],
                                          "" if r["ok"] else " · " + " ".join(r["missing_fields"] + r["missing_tests"] + r["bad_error_codes"] + r["missing_registration"])))
    print("  ③ 撞號 %d · ④ TA-Lib %d%s" % (len(res["duplicate_ids"]), len(res["talib"]), (" · " + "; ".join(res["talib"][:3])) if res["talib"] else ""))
    return 0 if res["lamp"] != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())
