#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG088_SsotAdditiveBridge v0101 — v0100 薄尾(v0100 一字不動):收容夾「冊外多出的檔」不把 Python 自動產生的 __pycache__/*.pyc 算進去。

實錄(2026-11-13 容器全量實跑 VRN_SystemManager v0265 test:VRN_ENG088 FAIL rc 1):19 檢只紅 ⑦
  (30 件 · 不符 0 · 夾內多出/少掉 5)。逐檔攤開:多出的 5 件全是
  __pycache__/{VRN_Evidence_Core,audit_ssot,test_vrn_evidence,ticker_regexes}.cpython-313.pyc · baseline/__pycache__/SUP_MDL749_…pyc
  = 任何行程 import 收容夾內的 .py 時 Python 自己寫的位元組碼快取(.gitignore 已忽略、不入倉、隨機器與 Python 版本而變)。
  manifest 30 件逐件 sha256 / bytes 全對、一件不少 → 收容包本身沒被碰。v0100 把快取當「冊外的檔」= 誤判紅。
本版只換 ⑦ 的判定:比對「夾內檔 vs 冊上檔」時排除 __pycache__ 夾與 .pyc 檔(數量照列,不藏);
  其餘(manifest schema · 逐件 sha256/bytes · EOL_ONLY 自成一態 L93 · 冊外有任何別的檔 = 紅)一字照 v0100。
  前版 19 檢照跑照印;紅的只有 ⑦ 而且 ⑦′ 過 → 判過;還有別的紅 → 照實紅。不刪快取、不寫收容夾。
VRN-2 自己的引擎;零網路 · 零寫庫 · 不用 TA-Lib · 不寫同意閘。用法同 v0100:status | tests | drift | candidates | --selftest
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
# [VIA:NET-BRIDGE] 留名:本版不出網

import contextlib
import hashlib
import importlib.util
import io
import json
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0101"
TAG = "VRN_ENG088_SsotAdditiveBridge " + VERSION
HERE = Path(__file__).resolve().parent
_STEM = "VRN_ENG088_SsotAdditiveBridge"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def is_bytecode_cache(rel: str) -> bool:
    """Python 自己寫的位元組碼快取:路徑經過 __pycache__ 或副檔名 .pyc/.pyo。"""
    parts = rel.split("/")
    return "__pycache__" in parts or rel.endswith((".pyc", ".pyo"))


def containment_check(P: dict | None = None) -> dict:
    """⑦′:同 v0100 ⑦,只差冊外檔排除位元組碼快取(數量照列)。回 {ok, note, extra, missing, caches, bad, eol}。"""
    P = P or PRIOR.package()
    res = {"ok": False, "note": "manifest 缺", "extra": [], "missing": [], "caches": 0, "bad": [], "eol": []}
    if P["state"] != "OK" or not P["manifest"]:
        res["note"] = "%s · manifest 缺" % P["state"]
        return res
    try:
        m = json.loads(Path(P["manifest"]).read_text(encoding="utf-8"))
        d = Path(P["dir"])
        for f in m.get("files", []):
            p = d / f["name"]
            if not p.is_file():
                res["bad"].append(f["name"])
                continue
            b = p.read_bytes()
            if hashlib.sha256(b).hexdigest() == f["sha256"] and len(b) == f["bytes"]:
                continue
            if f.get("sha256_lf") and hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest() == f["sha256_lf"]:
                res["eol"].append(f["name"])
            else:
                res["bad"].append(f["name"])
        all_disk = [x.relative_to(d).as_posix() for x in d.rglob("*") if x.is_file() and x.name != Path(P["manifest"]).name]
        caches = [r for r in all_disk if is_bytecode_cache(r)]
        on_disk = sorted(r for r in all_disk if not is_bytecode_cache(r))
        listed = sorted(f["name"] for f in m.get("files", []))
        res["extra"] = sorted(set(on_disk) - set(listed))
        res["missing"] = sorted(set(listed) - set(on_disk))
        res["caches"] = len(caches)
        res["ok"] = m.get("schema") == "VIA.IntakeManifest.v1" and not res["bad"] and on_disk == listed
        res["note"] = ("%d 件 · 不符 %d · 冊外多出 %d · 少掉 %d · Python 位元組碼快取 %d(不計,照列)"
                       % (len(listed), len(res["bad"]), len(res["extra"]), len(res["missing"]), len(caches))
                       + (" · EOL_ONLY %d(L93)" % len(res["eol"]) if res["eol"] else ""))
    except Exception as exc:  # noqa: BLE001 — 讀不動照實記
        res["note"] = "manifest 讀不動 %s" % type(exc).__name__
    return res


def _fixture(td: Path, extra: dict) -> dict:
    d = td / "pkg"
    d.mkdir(parents=True)
    (d / "a.py").write_text("X = 1\n", encoding="utf-8")
    b = (d / "a.py").read_bytes()
    man = d / "_INTAKE_MANIFEST_fixture.json"
    man.write_text(json.dumps({"schema": "VIA.IntakeManifest.v1",
                               "files": [{"name": "a.py", "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}]}), encoding="utf-8")
    for rel, txt in extra.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(txt, encoding="utf-8")
    return {"state": "OK", "dir": str(d), "manifest": str(man)}


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)) if note else ""), flush=True)

    print("=== %s · 薄尾自測(⑦ 冊外檔不計 Python 位元組碼快取;前版 19 檢照跑照印)===" % TAG, flush=True)
    with tempfile.TemporaryDirectory() as td:
        a = containment_check(_fixture(Path(td) / "1", {"__pycache__/a.cpython-313.pyc": "x", "sub/__pycache__/b.cpython-313.pyc": "y"}))
        chk("① 夾內只多 __pycache__/*.pyc → 不算冊外的檔 · 快取數照列", a["ok"] and a["caches"] == 2, a["note"])
        b = containment_check(_fixture(Path(td) / "2", {"stray.py": "Y = 2\n"}))
        chk("② 夾內多一支真的檔(stray.py)→ 照 v0100 判紅、點名", not b["ok"] and b["extra"] == ["stray.py"], b["note"])
        c = containment_check(_fixture(Path(td) / "3", {"x.pyc.txt": "z"}))
        chk("③ 名字像快取但不是(x.pyc.txt)→ 不排除", not c["ok"] and c["extra"] == ["x.pyc.txt"], c["note"])
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = PRIOR.selftest()
    out = buf.getvalue()
    print("  ── 前版 v0100 19 檢 ──", flush=True)
    print(out, end="")
    fails = [ln.strip() for ln in out.splitlines() if "[FAIL]" in ln]
    only7 = bool(fails) and all(ln.startswith("[FAIL] ⑦") for ln in fails)
    live = containment_check()
    chk("④ 實夾 ⑦′:manifest 逐件對得上 · 冊外沒有別的檔(快取不計)", live["ok"], live["note"])
    chk("⑤ 前版 19 檢:全過,或只紅 ⑦(= 快取誤判,④ 已重驗)", rc == 0 or only7, "rc %s · 紅 %d 項" % (rc, len(fails)))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 不刪快取 · 不寫收容夾 · 不出網 · 不用 TA-Lib", ("un" + "link(") not in src and ("rm" + "tree(") not in src
        and not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib)", src, re.M))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", TAG, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main() -> int:
    if "--selftest" in sys.argv[1:] or sys.argv[1:2] == ["selftest"]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
