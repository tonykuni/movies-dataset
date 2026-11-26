#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_TestExport_v0101 — 薄尾(v0100 一字不動):--root 先轉成絕對路徑再交棒

PR #747 Codex(P2):`--root testroot` 這類相對路徑時,v0100 的 verify 每支載入探測都把 cwd 設成 testroot/VDF,
參數卻還是 testroot/VDF/example.py → Python 去找 testroot/VDF/testroot/VDF/example.py → 誤報缺檔;
工具探測也是先 cd 進 supportive modules 再傳相對的同一路徑。
本版:main 收到的 --root 一律先 Path(...).resolve() 成絕對路徑,export / verify / 收據全用它;
直接呼叫 verify(root, man) 的也包一層同樣處理。清單照 v0100 取同夾 VIA_AllSystems_TestExport_Manifest_v*.json 尾版。
PR #747 Codex 二輪(P2):v0100 的回傳碼只看 tools_ok,引擎載入失敗(收據 verify.fails)照樣 rc 0。本版在驗證有跑時讀收據判:
  · 沒有失敗 → 0;只有「缺第三方套件」(ModuleNotFoundError 且模組名不是 VIA 自己的)→ 2(黃:缺依賴不是綠);
  · 缺 VIA 自己的模組(VDF_ / VRN_ / CGC_ … 或帶 _vNNNN)或其他錯誤 → 1(紅:匯出的測試樹不能用)。
零網路 · 零 TA-Lib · 不 import 他系統 · 不設同意閘。用法同 v0100:--repo <倉> --root <夾> [--ref …] [--dry] [--no-verify] · --selftest
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
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve()
FAMILY = "VIA_TestExport"
TAG = "VIA_TestExport v0101"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def abs_root_args(a: list) -> list:
    """把 --root <夾> / --root=<夾> 換成絕對路徑;其餘參數原樣。"""
    out, i = [], 0
    while i < len(a):
        x = a[i]
        if x == "--root" and i + 1 < len(a):
            out += [x, str(Path(a[i + 1]).expanduser().resolve())]
            i += 2
            continue
        if x.startswith("--root="):
            out.append("--root=" + str(Path(x.split("=", 1)[1]).expanduser().resolve()))
        else:
            out.append(x)
        i += 1
    return out


VIA_MOD = re.compile(r"^(VDF|VRN2?|CGC|VCGC|VAP|VQG|VTK|SUP|VIA|via)_|_v\d{4}$")
_MISSING = re.compile(r"ModuleNotFoundError: No module named '([^']+)'")


def classify(fails: list) -> tuple:
    """→ (rc, 說明)。0 沒失敗;2 只缺第三方套件;1 其他(含缺 VIA 自己的模組)。"""
    if not fails:
        return 0, "引擎載入全過"
    pkgs, hard = set(), []
    for f in fails:
        m = _MISSING.search(str(f.get("why") or ""))
        top = m.group(1).split(".")[0] if m else None
        if top and not VIA_MOD.search(top):
            pkgs.add(top)
        else:
            hard.append(f.get("tail"))
    if hard:
        return 1, "引擎載入不過 %d 支(非缺套件):%s" % (len(hard), hard[:5])
    return 2, "只缺第三方套件 %s(%d 支;黃)" % (sorted(pkgs), len(fails))


_PREV_VERIFY = PRIOR.verify


def verify(root, man: dict, lanes: int = 6, log=print) -> dict:
    return _PREV_VERIFY(Path(root).expanduser().resolve(), man, lanes, log)


PRIOR.verify = verify


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    b = abs_root_args(a)
    rc = PRIOR.main(b)
    if rc != 0 or "--dry" in b or "--no-verify" in b or "--root" not in b:
        return rc
    rec = Path(b[b.index("--root") + 1]) / PRIOR.RECEIPT
    try:
        fails = (json.loads(rec.read_text(encoding="utf-8")).get("verify") or {}).get("fails") or []
    except (OSError, ValueError) as exc:
        print(f"[RED] 讀不到收據的驗證結果:{exc}", flush=True)
        return 1
    rc2, why = classify(fails)
    print(f"[{'OK' if rc2 == 0 else ('YELLOW' if rc2 == 2 else 'RED')}] {why}", flush=True)
    return rc2


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 7 項 · 前版 {PRIOR_PATH.name} 在子行程)", flush=True)
    chk("T1 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    got = abs_root_args(["--repo", ".", "--root", "testroot", "--dry"])
    got2 = abs_root_args(["--root=sub/dir"])
    chk("T2 --root 相對 → 絕對(兩種寫法);其他參數原樣",
        Path(got[3]).is_absolute() and got[3].endswith("testroot") and got[:3] == ["--repo", ".", "--root"] and got[4] == "--dry"
        and Path(got2[0].split("=", 1)[1]).is_absolute(), (got, got2))
    keep = os.getcwd()
    with tempfile.TemporaryDirectory(prefix="texp101_") as td:
        try:
            os.chdir(td)
            (Path(td) / "rel" / "VDF").mkdir(parents=True)
            (Path(td) / "rel" / "supportive modules").mkdir(parents=True)
            (Path(td) / "rel" / "VDF" / "example.py").write_text("X = 1\n", encoding="utf-8")
            man = {"tails": ["VDF/example.py"], "expect": {}, "support_probe": []}
            old = _PREV_VERIFY(Path("rel"), man, 1, lambda *_: None)
            new = verify(Path("rel"), man, 1, lambda *_: None)
        finally:
            os.chdir(keep)
    ok_old = (old.get("systems") or {}).get("VDF", {})
    ok_new = (new.get("systems") or {}).get("VDF", {})
    chk("T3 重現:v0100 相對 root 的載入探測誤報失敗;本版同一夾 → 載入成功",
        str(ok_old).count("fail") >= 1 and ok_new and (ok_new.get("ok") == 1 or ok_new.get("fail") == 0), (old.get("systems"), new.get("systems")))
    tp = "ModuleNotFoundError: No module named "
    c0, c2, c1, c1b = (classify([]), classify([{"tail": "VDF/a.py", "why": tp + "'duckdb'"}]),
                       classify([{"tail": "VDF/b.py", "why": tp + "'VDF_MDL020_DataPlane_v0104'"}]),
                       classify([{"tail": "VRN/c.py", "why": "SyntaxError: bad"}]))
    chk("T6 引擎載入判法:沒失敗 0 · 只缺第三方套件 2(黃)· 缺 VIA 自己的模組 1 · 其他錯誤 1",
        (c0[0], c2[0], c1[0], c1b[0]) == (0, 2, 1, 1), (c0, c2, c1, c1b))
    with tempfile.TemporaryDirectory(prefix="texp101m_") as tm:
        keep_main = PRIOR.main
        outs = {}
        for name, fl in (("ok", []), ("pkg", [{"tail": "VDF/a.py", "why": tp + "'duckdb'"}]),
                         ("hard", [{"tail": "VDF/b.py", "why": tp + "'VDF_X_v0101'"}])):
            def fake(argv, fl=fl):
                r = Path(argv[argv.index("--root") + 1])
                r.mkdir(parents=True, exist_ok=True)
                (r / PRIOR.RECEIPT).write_text(json.dumps({"verify": {"tools_ok": True, "fails": fl}}), encoding="utf-8")
                return 0
            PRIOR.main = fake
            try:
                outs[name] = main(["--repo", ".", "--root", str(Path(tm) / name)])
            finally:
                PRIOR.main = keep_main
        dry = None
        PRIOR.main = lambda argv: 0
        try:
            dry = main(["--repo", ".", "--root", str(Path(tm) / "d"), "--dry"])
        finally:
            PRIOR.main = keep_main
    chk("T7 重現 Codex:工具都過、一支 VDF 引擎缺 VIA 模組 → v0100 rc 0,本版 rc 1;只缺套件 rc 2;全過 0;--dry 不讀收據",
        outs == {"ok": 0, "pkg": 2, "hard": 1} and dry == 0, (outs, dry))
    cp = subprocess.run([sys.executable, "-B", str(PRIOR_PATH), "--selftest"], capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=1800)
    chk(f"T4 前版 {PRIOR_PATH.name} 自測照過(子行程)", cp.returncode == 0, cp.stdout[-300:])
    src = HERE.read_text(encoding="utf-8")
    chk("T5 第 3 行加速器標記 · glob 取前版 · 零 TA-Lib · 不 import 他系統 · 不設同意閘",
        src.splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]" and "HERE.parent.glob(FAMILY" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M) and not re.search(r"^\s*(import|from)\s+(VDF|VRN|VQG|VAP)", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M))
    n = sum(ok)
    print(f"[計] {TAG} 自測 {n}/{len(ok)} {'PASS' if n == len(ok) else 'FAIL'}", flush=True)
    return 0 if n == len(ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
