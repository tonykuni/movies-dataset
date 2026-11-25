#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN2_NonStockSummarizer v0102 — 薄尾(v0100 · v0101 一字不動):v0310 原檔釘 SHA 認得「原檔 + 只多加速器橋」

PR #722 併 main 時:main 的 3dba5db74(「2 支 VRN 補加速器橋」)替 nonstock_v0310/engine/VIA_NON_STOCK_SUMMARIZER_ENGINE_v0310.py
  補了 [VIA:ACCEL-BRIDGE:v0100] 區塊 → 檔的 SHA 從 86903811… 變成 2b3688c5…;v0100 自測 ①「v0310 原檔 SHA 釘住」因此紅,
  v0101 自測 ①(v0100 的 18 檢)與 ⑥(沙盒裡跑本版自測)跟著紅。拿掉那一段加速器橋(含前面一個換行)後 SHA 正好回到 86903811…
  → 原檔內容沒被改,只多了加速器橋。
本版:只在「現檔 SHA ≠ 釘的值,但拿掉恰好一段加速器橋之後 = 釘的值」時,把這一輪的比對值換成現檔 SHA(只在記憶體,不寫檔);
  其他任何改動照樣紅。⑥ 的沙盒多帶本檔,子行程跑本版自測。分類 / 讀檔 / 核心 v0400 全照 v0101。
零網路 · 不用 TA-Lib · 不 import VCGC · 加速器橋在。用法同 v0101。
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
import contextlib
import hashlib
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VRN2_NonStockSummarizer"
ENGINE = "VRN2_NonStockSummarizer v0102"
BRIDGE_RX = re.compile(rb"\r?\n# ===== \[VIA:ACCEL-BRIDGE:v0100\].*?# ===== \[VIA:ACCEL-BRIDGE:END\] =====\r?\n", re.S)


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0102", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0100 = PRIOR.PRIOR
PIN = V0100.NS_ENGINE_SHA


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def bridge_only(path: Path, pin: str = PIN) -> dict:
    """現檔是不是「釘住的原檔 + 恰好一段加速器橋」。回 {state, sha, stripped}。"""
    b = path.read_bytes()
    sha = hashlib.sha256(b).hexdigest()
    if sha == pin:
        return {"state": "ORIGINAL", "sha": sha, "stripped": sha}
    hits = BRIDGE_RX.findall(b)
    stripped = hashlib.sha256(BRIDGE_RX.sub(b"", b, count=1)).hexdigest() if len(hits) == 1 else None
    return {"state": "ORIGINAL_PLUS_ACCEL_BRIDGE" if stripped == pin else "CHANGED", "sha": sha, "stripped": stripped}


def _accept_bridge() -> dict:
    st = bridge_only(V0100.NS_ENGINE) if V0100.NS_ENGINE.is_file() else {"state": "MISSING"}
    if st["state"] == "ORIGINAL_PLUS_ACCEL_BRIDGE":
        V0100.NS_ENGINE_SHA = st["sha"]                    # 只在這一輪記憶體裡換比對值;不寫檔
    return st


BRIDGE_STATE = _accept_bridge()


def proof_without_standin() -> dict:
    """同 v0101(沙盒 = 非個股車道真正要的檔,沒有暫代核心),多帶本檔,子行程跑本版 --selftest 與 doctor。"""
    lane = V0100.LANE_FILE
    m = re.search(r'^CLASSIFIER_SRC\s*=\s*"([^"]+)"', lane.read_text(encoding="utf-8"), re.M) if lane.is_file() else None
    files = [PRIOR.PRIOR_PATH, PRIOR_PATH, Path(__file__), PRIOR.readers_path(), lane] + ([HERE / m.group(1)] if m and (HERE / m.group(1)).is_file() else [])
    files += [p for p in (HERE / n for n in PRIOR.REUSE_CANON) if p.is_file()]
    with tempfile.TemporaryDirectory(prefix="vrn2_ns102_proof_") as td:
        via = Path(td) / "VeritasIntelligenceAnalytics"
        vrn = via / "functional modules" / "VRN"
        vrn.mkdir(parents=True)
        sup = HERE.parents[1] / "supportive modules"
        if sup.is_dir():
            (via / "supportive modules").symlink_to(sup, target_is_directory=True)
        for f in files:
            shutil.copy2(f, vrn / f.name)
        for d in (V0100.NS_DIR, PRIOR.CORE_DIR):
            shutil.copytree(d, vrn / d.name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "output"))
        env = dict(os.environ, **{PRIOR.SANDBOX_ENV: "1", "PYTHONDONTWRITEBYTECODE": "1"})
        me = vrn / Path(__file__).name
        r1 = subprocess.run([sys.executable, "-B", str(me), "--selftest"], capture_output=True, text=True, env=env, timeout=900, cwd=td)
        r2 = subprocess.run([sys.executable, "-B", str(me), "doctor"], capture_output=True, text=True, env=env, timeout=300, cwd=td)
        present = (vrn / PRIOR.STANDIN_NAME).exists()
    return {"rc_selftest": r1.returncode, "rc_doctor": r2.returncode, "standin_in_sandbox": present,
            "files": sorted(f.name for f in files), "tail": (r1.stdout + r1.stderr)[-600:], "doctor_tail": (r2.stdout + r2.stderr)[-300:]}


PRIOR.proof_without_standin = proof_without_standin        # v0101 自測 ⑥ 叫它模組裡的這支


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print("  [%s] %s%s" % ("OK" if cond else "FAIL", name, (" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("=== %s 自測(v0100 / v0101 / v0310 / v0400 不改;零網路)===" % ENGINE, flush=True)
    chk("⓪ v0310 原檔 = 釘住的原檔,或原檔 + 恰好一段加速器橋(%s)" % BRIDGE_STATE.get("state"),
        BRIDGE_STATE.get("state") in ("ORIGINAL", "ORIGINAL_PLUS_ACCEL_BRIDGE"), BRIDGE_STATE)
    with tempfile.TemporaryDirectory(prefix="vrn2_ns102_") as td:
        base = b"print('x')\nX = 1\n"
        pin = hashlib.sha256(base).hexdigest()
        bridge = (b"\n# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel\ntry:\n    import VIA_SuperAccel_Module as VIA_ACCEL\nexcept Exception:\n"
                  b"    VIA_ACCEL = None\n# ===== [VIA:ACCEL-BRIDGE:END] =====\n")
        p = Path(td) / "e.py"
        p.write_bytes(b"print('x')\n" + bridge + b"X = 1\n")
        s1 = bridge_only(p, pin)["state"]
        p.write_bytes(b"print('x')\n" + bridge + b"X = 2\n")
        s2 = bridge_only(p, pin)["state"]
        p.write_bytes(b"print('x')\n" + bridge + bridge + b"X = 1\n")
        s3 = bridge_only(p, pin)["state"]
        p.write_bytes(base)
        s4 = bridge_only(p, pin)["state"]
    chk("① 只多一段加速器橋 → 認得;多橋之外還改了內容 / 兩段橋 → 照樣紅;原樣 → ORIGINAL",
        (s1, s2, s3, s4) == ("ORIGINAL_PLUS_ACCEL_BRIDGE", "CHANGED", "CHANGED", "ORIGINAL"), (s1, s2, s3, s4))
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc1 = PRIOR.selftest()
    out1 = buf.getvalue()
    fails = [ln.strip() for ln in out1.splitlines() if ln.strip().startswith("[FAIL]")]
    chk("② v0101 自測整個照過(v0100 的 18 檢 · 核心 v0400 · 沙盒證明 ⑥ 帶本版)", rc1 == 0, fails[:3] or out1[-300:])
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("③ 零網路 · 不用 TA-Lib · 不 import VCGC · 加速器橋在 · 不寫檔(比對值只換記憶體)",
        not re.search(r"^\s*(?:import|from)\s+(talib|requests|urllib|socket|http|CGC_)", body, re.M) and "[VIA:ACCEL-BRIDGE:v0100]" in src
        and ".write_bytes(" not in body and ".write_text(" not in body)
    pub = [n for n in dir(PRIOR) if not n.startswith("_") and callable(getattr(PRIOR, n, None))]
    chk("④ 尾版保有前版公開名稱(TAILAPI)", all(getattr(sys.modules[__name__], n, None) is not None for n in pub), "%d 支" % len(pub))
    n = sum(ok)
    print("[%s] %s selftest · %d/%d" % ("PASS" if n == len(ok) else "FAIL", ENGINE, n, len(ok)), flush=True)
    return 0 if n == len(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if not a or a[:1] in (["selftest"], ["--selftest"]) or "--selftest" in a:
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    sys.exit(main())
