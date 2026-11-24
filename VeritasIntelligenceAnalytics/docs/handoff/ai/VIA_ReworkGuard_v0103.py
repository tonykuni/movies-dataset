#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_ReworkGuard v0103 — 薄尾(v0102 以前一字不動;已鎖成功,修改開新版)

  PR #734 誤判:R11(憑證明文進倉)的「*KEY* = 長常數」把 TOKEN_TOOL = "CGC_MDL158_VIAPanoramaAuditRepair_v0121"
  當成金鑰 —— 變數名裡有 TOKEN(省 Token 工具),值是 VIA 的版號檔名本體,不是憑證。
  本版只改這一條判法:值若是「VIA 版號檔名本體」(字母開頭、底線分段、以 _v + 四位數結尾)就不算金鑰。
  其餘照舊:ghp_ / sk- / AKIA / xox 樣式照樣紅;*KEY* = 一般長常數(如 32 位十六進位)照樣紅;值不印。
  其餘全照 v0102 / v0101 / v0100(經 v0100 模組全域換上 d_secret)。
用法同 v0100:python VIA_ReworkGuard_v0103.py check [--fetch-prs] | report | causes | --selftest
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
import ast
import importlib.util
import os
import re
import sys
from pathlib import Path

VERSION = "v0103"
HERE = Path(__file__).resolve()
FAMILY = "VIA_ReworkGuard"
TAG = "VIA_ReworkGuard " + VERSION


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0103", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE                                                            # v0100:run_check 叫它模組裡的 d_secret
_V0100_SECRET, _V0102_TAG = BASE.d_secret, PRIOR.TAG
VERSIONED_STEM = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*_v\d{4}")


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def looks_secret(value: str) -> bool:
    """長常數像不像金鑰:同 v0100(24 字以上、英數 _ -、不是全大寫),但 VIA 版號檔名本體不算。"""
    return (bool(re.fullmatch(r"[A-Za-z0-9_\-]{24,}", value)) and not value.isupper()
            and not VERSIONED_STEM.fullmatch(value))


def d_secret(repo, files) -> list:
    out = []
    for p in files:
        src = BASE.read(repo, p)
        if not src:
            continue
        hit = next((rx.pattern[:12] for rx in BASE.SECRET_RX if rx.search(src)), None)
        if not hit and p.endswith(".py"):
            for n in ast.walk(BASE._parse(src) or ast.Module(body=[], type_ignores=[])):
                if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                    names = [t.id if isinstance(t, ast.Name) else getattr(t, "attr", "") for t in n.targets]
                    if any(BASE.SECRET_NAME.search(x or "") for x in names) and looks_secret(n.value.value):
                        hit = "*KEY* = 長常數"
                        break
        if hit:
            out.append(("RED", "R11", f"`{p}` 含疑似金鑰({hit};值不印)→ 遮罩 <REDACTED:…> 並作廢重發"))
    return out


def _install():
    BASE.d_secret = d_secret
    BASE.TAG = TAG
    for c in BASE.CAUSES:
        c["cmd"] = c["cmd"].replace(PRIOR_PATH.name, HERE.name)


_install()


def run_check(*a, **kw) -> dict:
    r = PRIOR.run_check(*a, **kw)
    r["tool"] = TAG
    return r


def selftest() -> int:
    import contextlib
    import io
    import shutil
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    buf = io.StringIO()
    BASE.d_secret, BASE.TAG = _V0100_SECRET, _V0102_TAG
    for c in BASE.CAUSES:
        c["cmd"] = c["cmd"].replace(HERE.name, PRIOR_PATH.name)
    try:
        with contextlib.redirect_stdout(buf):
            rc0 = PRIOR.selftest()                                           # v0102 自測照 v0102 的判法跑(它再照前版鏈跑)
    finally:
        _install()
    print(f"=== {TAG} · 薄尾自測(R11 版號檔名不算金鑰 · 前版原封不動;暫存夾 · 零網路)===", flush=True)
    chk("⓪ 前版 %s 自測照過(含整條前版鏈)" % PRIOR_PATH.name, rc0 == 0, buf.getvalue()[-300:])
    td = Path(tempfile.mkdtemp(prefix="via_rework103_"))
    try:
        cases = {
            "tool.py": 'TOKEN_TOOL = "CGC_MDL158_VIAPanoramaAuditRepair_v0121"\nTOKEN_STATION = "VIA_TokenSaver_v0100"\n',
            "fred.py": "FRED_API_KEY = 'abcdef0123456789abcdef0123456789'\n",
            "mixed.py": 'API_TOKEN = "Xy7Qp2Lm9Rt4Vb8Nc3Kd6Hs1Wf5Gj0Za"\n',
            "ghp.py": "x = 'ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8'\n",
        }
        for name, body in cases.items():
            (td / name).write_text(body, encoding="utf-8")
        hits = {name: bool(d_secret(str(td), [name])) for name in cases}
        txt = "\n".join(m for _l, _c, m in d_secret(str(td), list(cases)))
    finally:
        shutil.rmtree(td, ignore_errors=True)
    chk("① *TOKEN* = VIA 版號檔名本體(工具名)→ 不算金鑰(PR #734 誤判重現)", hits["tool.py"] is False, hits)
    chk("② *KEY* = 32 位十六進位 · *TOKEN* = 混合英數長常數 → 照樣紅 R11", hits["fred.py"] and hits["mixed.py"], hits)
    chk("③ ghp_ 樣式照樣紅;訊息不印值", hits["ghp.py"] and "abcdef0123456789" not in txt and "Xy7Qp2" not in txt, txt[:200])
    chk("④ run_check 走本版 d_secret(v0100 模組全域已換上)", BASE.d_secret is d_secret and BASE.TAG == TAG)
    pub = [n for n in vars(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n)) and getattr(getattr(PRIOR, n), "__module__", "") == PRIOR.__name__]
    chk("⑤ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), f"{len(pub)} 支")
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    BASE.run_check = run_check
    return BASE.main(a)


if __name__ == "__main__":
    sys.exit(main())
