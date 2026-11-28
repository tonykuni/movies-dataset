#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VIA_PanoramaFusion_SuperEngine v0303 — 薄尾(v0300–v0302 一字不動):第二輪治理三修(PR #782 Codex 2×P1 + 1×P2)

① (P1 資料邊界)deep_patches 不再把函式原始碼(含註解、docstring、字面值)送給 OmniRoute 後面的模型:
     一律回 BLOCKED,完全不呼叫 route_review。能離開本機的只有程式碼結構與 schema;要深修得先有驗證過的本機推論後端(另案)。
② (P1)短指令綁定(via-fuse · via-panorama · via-super …)與 fusion 產的 VIA_CommandBindings 指向本檔(有全部防護的尾版),
     不再指向 v0300 本體;v0300 的 ENGINE_FILE 改成本檔名(也讓 fusion 照舊把引擎自己排除在修補對象外)。
③ (P2)產生的加速器 / 網路橋 import 改成先從腳本所在夾往上找 VIA_Runtime_Bridge_v0300.py 並放進 sys.path,
     巢狀夾裡的腳本直接執行(沒有外加 PYTHONPATH)也載得到;不再只靠測試工具替它插路徑。
其餘照 v0302 → v0301 → v0300(含 v0302 的四修:只寫 VCGC · 環境只稽核 · 不覆寫原檔 · 橋設定退路 _v0300 · 子行程跑尾版)。
自測零網路 · 暫存夾 · 不碰 TA-Lib · 不設同意閘。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(VDF 全導入令;惰性載入=import 時零網路、零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:  # noqa: BLE001
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT;網路只認 AegisNexus);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "v0303"
STEM = "VIA_PanoramaFusion_SuperEngine"
TAG = f"{STEM} {VERSION}"
HERE = Path(__file__).resolve().parent


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{STEM}_prior_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)                 # v0302
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V300 = PRIOR.V300


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


BRIDGE_MOD = V300.BRIDGE_FILE[:-3]
DATA_BOUNDARY = ("DATA_BOUNDARY_SOURCE_NOT_SENT:能離開本機的只有程式碼結構與 schema;"
                 "函式原始碼不送 OmniRoute / 外部模型(要深修需先有驗證過的本機推論後端)")
_ORIG = {k: getattr(V300, k) for k in ("deep_patches", "inject_bridges", "ENGINE_FILE", "__file__")}


def deep_patches(cfg: dict, files: dict, cards: list) -> dict:
    return {"status": "BLOCKED", "reason": DATA_BOUNDARY, "changed": []}


def _finder(nl: str) -> str:
    return nl.join([
        "import sys as _via_sys, pathlib as _via_pathlib",
        "_via_dir = _via_pathlib.Path(__file__).resolve().parent",
        f"while not (_via_dir / {V300.BRIDGE_FILE!r}).is_file() and _via_dir.parent != _via_dir:",
        "    _via_dir = _via_dir.parent",
        "if str(_via_dir) not in _via_sys.path:",
        "    _via_sys.path.insert(0, str(_via_dir))",
    ]) + nl


def inject_bridges(raw: bytes, network: bool) -> bytes:
    out = _ORIG["inject_bridges"](raw, network)
    if out == raw:
        return raw
    text, encoding = V300.source_text(out)
    if "_via_dir" in V300.source_text(raw)[0]:
        raise ValueError("BRIDGE_NAME_COLLISION")
    nl = "\r\n" if "\r\n" in text else "\n"
    first = f"from {BRIDGE_MOD} import accel_env as _via_accel_env"
    if first not in text:
        return out
    return text.replace(first, _finder(nl) + first, 1).encode(encoding)


def install() -> None:
    V300.deep_patches = deep_patches
    V300.inject_bridges = inject_bridges
    V300.ENGINE_FILE = Path(__file__).name                     # 綁定指向有防護的尾版
    V300.__file__ = str(Path(__file__).resolve())              # 子行程跑本檔


def uninstall() -> None:
    for k, v in _ORIG.items():
        setattr(V300, k, v)


install()


def selftest() -> int:
    ok = []

    def chk(label, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + label + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 5 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存夾 · 零網路)", flush=True)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("T1 加速器真的載到 · 第 3 行標記 · 網路工具橋", VIA_ACCEL is not None and src.splitlines()[2] == "# [VIA:ACCEL-BRIDGE:v0111]"
        and VIA_NET_TOOL_PATH is not None)
    sent = []
    keep = V300.route_review
    V300.route_review = lambda *a, **k: (sent.append(a), {"status": "PASS", "outputs": []})[1]
    try:
        body = 'def f(x):\n    """研報內文 · 不可外送"""\n    return x + undefined_name\n'
        res = V300.deep_patches({}, {"m.py": body.encode()}, [{"path": "m.py", "issues": [{"line": 3, "level": "RED"}]}])
        res0 = _ORIG["deep_patches"]({"fusion": {"mcp_modules": []}}, {"m.py": body.encode()}, [{"path": "m.py", "issues": [{"line": 3, "level": "RED"}]}])
    except Exception as exc:  # noqa: BLE001 — 前版路徑只用來證明它真的會送,型別不限
        res0 = {"status": type(exc).__name__}
    finally:
        V300.route_review = keep
    chk("T2 (P1 資料邊界)deep_patches 回 BLOCKED 且完全不呼叫 route_review;同一份輸入前版真的會送出函式原始碼",
        res["status"] == "BLOCKED" and len(sent) == 1 and "研報內文" in str(sent[0]), (res, len(sent), res0))
    b = V300.command_bindings()
    chk("T3 (P1)短指令綁定與 ENGINE_FILE 指向本檔(有防護的尾版),不再指 v0300",
        b["engine"] == Path(__file__).name and V300.ENGINE_FILE == Path(__file__).name
        and _ORIG["ENGINE_FILE"].endswith("_v0300.py"), b.get("engine"))
    with tempfile.TemporaryDirectory(prefix="pf303_") as td:
        root = Path(td)
        (root / V300.BRIDGE_FILE).write_text("def accel_env():\n    return {}\ndef network_env():\n    return {}\n", encoding="utf-8")
        nested = root / "supportive modules" / "registry"
        nested.mkdir(parents=True)
        raw = b'"""doc"""\nfrom __future__ import annotations\nprint("ran")\n'
        (nested / "new.py").write_bytes(inject_bridges(raw, True))
        (nested / "old.py").write_bytes(_ORIG["inject_bridges"](raw, True))
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        run = lambda p: subprocess.run([sys.executable, "-I", str(p)], cwd=tempfile.gettempdir(), capture_output=True, text=True, env=env, timeout=60)  # noqa: E731
        new, old = run(nested / "new.py"), run(nested / "old.py")
        again = inject_bridges((nested / "new.py").read_bytes(), True) == (nested / "new.py").read_bytes()
    chk("T4 (P2)巢狀夾腳本直接執行(-I · 沒 PYTHONPATH)載得到橋;前版同一檔 ModuleNotFoundError;再注一次不重複",
        new.returncode == 0 and "ran" in new.stdout and old.returncode != 0 and "ModuleNotFoundError" in old.stderr and again,
        (new.returncode, new.stderr[-200:], old.returncode, again))
    chk("T5 子行程跑本檔(v0300 的 __file__ 指到 v0303)", Path(V300.__file__).resolve() == Path(__file__).resolve())
    uninstall()
    try:
        rc = PRIOR.selftest()
    finally:
        install()
    chk("T6 前版 v0302 自測照過(含 v0301 · v0300 原有 107 項)", rc == 0, rc)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


if __name__ == "__main__":
    raise SystemExit(main())
